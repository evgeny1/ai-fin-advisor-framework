"""
analysis/_utils.py — shared helpers for Stage 3 analysis modules.

Convention on units:
  - Percentage changes are stored as fractions (0.12 = +12%).
  - cal.regime percentage fields are in 0–100 scale (15.0 = 15%);
    divide by 100 when comparing to fractions.
  - Spread / OAS values are in basis points (int or float).
  - MOVE / VIX: raw index points.
"""
from __future__ import annotations

import statistics
from typing import Any, Dict, List, Optional, Tuple

from ..types import DataReading


# ── DataReading value extractors ──────────────────────────────────────────────

def get_scalar(
    reading: Optional[DataReading],
    flags: List[str],
    label: str,
) -> Optional[float]:
    """Return numeric current value from DataReading, or None with a flag."""
    if reading is None or not reading.is_valid:
        flags.append(f"{label}: reading unavailable or invalid")
        return None
    v = reading.value
    if isinstance(v, dict):
        for key in ("current", "value", "close", "oas", "price"):
            if key in v and v[key] is not None:
                try:
                    return float(v[key])
                except (TypeError, ValueError):
                    pass
        flags.append(f"{label}: dict value has no recognizable scalar key — keys: {list(v.keys())}")
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        flags.append(f"{label}: cannot convert value to float (type={type(v).__name__})")
        return None


def get_history(reading: Optional[DataReading]) -> List[float]:
    """
    Return ordered history list (oldest-first) from DataReading.
    Returns empty list when reading is None, invalid, or has no history.
    DataReading.value may be:
      - dict with key "history" → List[float | None]
      - dict with key "history_bps", "prices", "closes" → same
      - scalar → no history (return [])
    """
    if reading is None or not reading.is_valid:
        return []
    v = reading.value
    if not isinstance(v, dict):
        return []
    for key in ("history", "history_bps", "prices", "closes", "values"):
        if key in v and isinstance(v[key], list):
            return [float(x) for x in v[key] if x is not None]
    return []


def get_dict_value(
    reading: Optional[DataReading],
    key: str,
    flags: List[str],
    label: str,
) -> Optional[float]:
    """Extract a named key from a dict-valued DataReading."""
    if reading is None or not reading.is_valid:
        flags.append(f"{label}.{key}: reading unavailable")
        return None
    v = reading.value
    if not isinstance(v, dict):
        flags.append(f"{label}.{key}: reading is scalar, not dict")
        return None
    raw = v.get(key)
    if raw is None:
        flags.append(f"{label}.{key}: key not present in reading")
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        flags.append(f"{label}.{key}: cannot convert to float")
        return None


# ── Statistical helpers ────────────────────────────────────────────────────────

def compute_median(
    history: List[float],
    window: int,
    label: str,
    flags: List[str],
) -> Optional[float]:
    """
    Compute trailing median over the most recent `window` datapoints.
    If fewer than window points exist but ≥10, compute from available and flag.
    If <10, return None and flag.
    """
    if len(history) >= window:
        return statistics.median(history[-window:])
    if len(history) >= 10:
        flags.append(
            f"{label}: only {len(history)} datapoints (need {window}) — "
            f"median computed from available history (may be less stable)"
        )
        return statistics.median(history)
    flags.append(
        f"{label}: {len(history)} datapoints insufficient for median — threshold checks skipped"
    )
    return None


def compute_change(
    history: List[float],
    window: int,
    label: str,
    flags: List[str],
) -> Optional[float]:
    """
    Return history[-1] − history[-(window+1)]: absolute change over `window` periods.
    Returns None with flag when history too short.
    """
    if len(history) >= window + 1:
        return history[-1] - history[-(window + 1)]
    flags.append(f"{label}: insufficient history for {window}-period change ({len(history)} points)")
    return None


def compute_pct_change(
    history: List[float],
    window: int,
    label: str,
    flags: List[str],
) -> Optional[float]:
    """
    Return (history[-1] - history[-(window+1)]) / |history[-(window+1)]| as fraction.
    Returns None when history too short or base is zero.
    """
    if len(history) < window + 1:
        flags.append(f"{label}: insufficient history for {window}-period pct change ({len(history)} points)")
        return None
    base = history[-(window + 1)]
    if base == 0.0:
        flags.append(f"{label}: base value is 0 — percentage change undefined")
        return None
    return (history[-1] - base) / abs(base)
