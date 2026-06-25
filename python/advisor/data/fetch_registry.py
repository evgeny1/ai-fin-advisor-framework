"""
FetchRegistry — extension point for all data series.
OCP: add a new series → register one FetchSpec in m18_registry.py.
fetch_all() picks it up automatically. No other code changes needed.
Maps to FW_Types.FetchRegistry + M18.FetchRegistry.fetchAll().
"""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from datetime import datetime
from typing import Callable, Dict, List, Optional

from ..types import DataReading, DataSource, FetchSpec, UpdateFrequency

logger = logging.getLogger(__name__)

# Per-spec wall-clock bound for fetch_all(). A single hung network call
# (e.g. yfinance/Yahoo Finance retrying without bound — observed 2026-06-24,
# advisor_run_computation hung 25+ minutes on one illiquid-symbol fetch)
# must not block the rest of the session's data fetches indefinitely.
_FETCH_TIMEOUT_SECONDS = 25.0

# Type alias: a fetcher takes a FetchSpec, returns one or more DataReadings.
Fetcher = Callable[[FetchSpec], List[DataReading]]


class FetchRegistry:
    """
    Accumulates FetchSpecs from m18_registry and maps DataSources to fetcher callables.
    fetch_all() executes all non-ON_DEMAND specs in parallel.
    Failures become flagged DataReadings — never propagate as exceptions.
    """

    def __init__(self, max_workers: int = 8) -> None:
        self._specs:    Dict[str, FetchSpec] = {}
        self._fetchers: Dict[DataSource, Fetcher] = {}
        self._max_workers = max_workers

    def register(self, spec: FetchSpec) -> None:
        """Idempotent on duplicate id."""
        if spec.id not in self._specs:
            self._specs[spec.id] = spec

    def register_fetcher(self, source: DataSource, fn: Fetcher) -> None:
        self._fetchers[source] = fn

    # ── Main API ──────────────────────────────────────────────────────────────

    def fetch_all(self) -> List[DataReading]:
        """
        Parallel fetch of all registered specs with update_frequency != ON_DEMAND.
        Always returns a list; never raises.

        Each spec is bounded to _FETCH_TIMEOUT_SECONDS. A spec that exceeds
        the bound produces a FETCH_TIMEOUT-flagged reading rather than
        blocking the rest of the batch — the underlying worker thread may
        still be running in the background (ThreadPoolExecutor cannot cancel
        a running thread), so the executor is shut down with wait=False:
        the slow call is abandoned, not waited on, on the way out.
        """
        eligible = [
            s for s in self._specs.values()
            if s.update_frequency != UpdateFrequency.ON_DEMAND
        ]
        results: List[DataReading] = []

        ex = ThreadPoolExecutor(max_workers=self._max_workers)
        try:
            futures = {ex.submit(self._safe_fetch, spec): spec for spec in eligible}
            for future, spec in futures.items():
                try:
                    results.extend(future.result(timeout=_FETCH_TIMEOUT_SECONDS))
                except FutureTimeoutError:
                    logger.error(
                        f"fetch_all: {spec.id} exceeded {_FETCH_TIMEOUT_SECONDS}s bound "
                        "— abandoning (worker thread may still be running)"
                    )
                    results.append(_failed_reading(
                        spec, f"FETCH_TIMEOUT: exceeded {_FETCH_TIMEOUT_SECONDS}s bound"
                    ))
                except Exception as exc:
                    logger.error(f"Unexpected error in fetch_all for {spec.id}: {exc}")
                    results.append(_failed_reading(spec, str(exc)))
        finally:
            # wait=False: do not block process exit/return on a thread stuck
            # inside a hung network call — see _FETCH_TIMEOUT_SECONDS above.
            ex.shutdown(wait=False)

        valid   = sum(1 for r in results if r.is_valid)
        flagged = len(results) - valid
        logger.info(f"fetch_all: {valid} valid, {flagged} flagged from {len(eligible)} specs")
        return results

    def fetch_one(self, spec_id: str) -> List[DataReading]:
        """Fetch a single spec by id. Use for ON_DEMAND series."""
        spec = self._specs.get(spec_id)
        if spec is None:
            raise KeyError(f"No FetchSpec registered with id '{spec_id}'")
        return self._safe_fetch(spec)

    def readings_dict(self, readings: List[DataReading]) -> Dict[str, DataReading]:
        """Index a reading list by spec_id for convenient downstream lookup."""
        return {r.spec_id: r for r in readings}

    # ── Internals ─────────────────────────────────────────────────────────────

    def _safe_fetch(self, spec: FetchSpec) -> List[DataReading]:
        """Execute fetcher; on any failure return a flagged DataReading."""
        fetcher = self._fetchers.get(spec.source)
        if fetcher is None:
            return [_failed_reading(spec, f"no fetcher for {spec.source.value}")]
        try:
            return fetcher(spec)
        except Exception as exc:
            logger.warning(f"Fetch failed [{spec.id}]: {exc}")
            return [_failed_reading(spec, str(exc))]

    def summary(self) -> str:
        lines = [f"FetchRegistry: {len(self._specs)} specs | {len(self._fetchers)} fetchers"]
        for source, fetcher in self._fetchers.items():
            specs = [s for s in self._specs.values() if s.source == source]
            lines.append(f"  {source.value}: {len(specs)} spec(s) → {fetcher.__name__}")
        unhandled = {s.source for s in self._specs.values()} - set(self._fetchers)
        for src in unhandled:
            count = sum(1 for s in self._specs.values() if s.source == src)
            lines.append(f"  {src.value}: {count} spec(s) → ✗ NO FETCHER")
        return "\n".join(lines)


def _failed_reading(spec: FetchSpec, reason: str) -> DataReading:
    return DataReading(
        spec_id=spec.id, value=None, source=spec.source,
        fetched_at=datetime.utcnow(),
        quality_flags=[f"FETCH_FAILED: {reason}"],
    )
