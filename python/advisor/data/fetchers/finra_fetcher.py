"""
finra_fetcher.py — ENG-54: FINRA monthly margin statistics, fetched directly
from finra.org.

Source characterization (verified live 2026-07-26):
- Official page: https://www.finra.org/rules-guidance/key-topics/margin-accounts/margin-statistics
  (FINRA Rule 4521(d) data; HTML table carries the trailing ~13 months only).
- Full history: the "Download the Data" xlsx on that page —
  https://www.finra.org/sites/default/files/2021-03/margin-statistics.xlsx —
  one sheet ("Customer Margin Balances"), header row + one row per month,
  newest first, Jan 1997 → present. Column 0 = "Year-Month" (YYYY-MM),
  column 1 = "Debit Balances in Customers' Securities Margin Accounts"
  ($ millions). Free-credit columns 2-3 are not consumed here (col 3 is
  NaN pre-Feb-2010 per FINRA's combined-reporting note).
- FINRA states explicitly: no API, no data feeds — the file download IS the
  sanctioned machine-readable path.
- Publication cadence: third week of the month following the reference
  month, so the newest reference month-end is routinely ~50 days old just
  before a release — the spec's acceptable_lag_days accounts for that.

The xlsx (not the HTML table) is fetched because CHAIN_3's WATCH condition
("margin at all-time nominal record", Calibration_State.md §12.3) needs the
full history to determine the record deterministically rather than trusting
a hardcoded description string.
"""
from __future__ import annotations

import datetime
import io
import logging
from typing import Any, Dict, List, Optional, Tuple

from ...types import DataReading, DataSource, FetchSpec

logger = logging.getLogger(__name__)

MARGIN_STATS_XLSX_URL = (
    "https://www.finra.org/sites/default/files/2021-03/margin-statistics.xlsx"
)
_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
_TIMEOUT_S = 30.0
_HISTORY_TAIL_MONTHS = 13  # enough for MoM + YoY audit trail in the reading


def _parse_margin_xlsx(content: bytes) -> List[Tuple[str, float]]:
    """
    Parse the FINRA margin-statistics workbook into chronological
    [(year_month, debit_balance_musd), ...].

    Header row and debit column are located by name ("Year-Month" /
    "Debit Balances"), not by fixed position, so a cosmetic preamble row or
    column reshuffle degrades to a loud parse error rather than silently
    reading the wrong column (same degrade-never-lie posture as ENG-69's
    ticker-identity check).
    """
    import pandas as pd

    df = pd.read_excel(io.BytesIO(content), sheet_name=0, header=None)

    header_row_idx: Optional[int] = None
    for i in range(min(10, len(df))):
        row_strs = [str(c) for c in df.iloc[i].tolist()]
        if any("Year-Month" in s for s in row_strs):
            header_row_idx = i
            break
    if header_row_idx is None:
        raise ValueError("no 'Year-Month' header row found in first 10 rows")

    header = [str(c) for c in df.iloc[header_row_idx].tolist()]
    month_col = next(i for i, h in enumerate(header) if "Year-Month" in h)
    debit_col: Optional[int] = None
    for i, h in enumerate(header):
        if "Debit Balances" in h:
            debit_col = i
            break
    if debit_col is None:
        raise ValueError("no 'Debit Balances' column found in header row")

    rows: List[Tuple[str, float]] = []
    for i in range(header_row_idx + 1, len(df)):
        month = str(df.iloc[i, month_col]).strip()
        raw_val = df.iloc[i, debit_col]
        if len(month) < 6 or "-" not in month:
            continue  # blank/footnote rows
        try:
            val = float(str(raw_val).replace(",", ""))
        except (TypeError, ValueError):
            continue
        if val != val:  # NaN
            continue
        rows.append((month[:7], val))

    if len(rows) < 2:
        raise ValueError(f"only {len(rows)} usable data rows parsed — need >= 2")

    rows.sort(key=lambda t: t[0])  # chronological (file is newest-first)
    return rows


def _derive_margin_metrics(rows: List[Tuple[str, float]]) -> Dict[str, Any]:
    """
    Chronological (month, debit) rows → the CHAIN_3 value dict.

    Key names `current` / `mom_pct` / `at_nominal_record` are the exact
    contract analysis/cascade.py's CHAIN_3 scorer reads (verified against
    its own key lookups, 2026-07-26); everything else is audit context.
    `gate_count_90d` is deliberately ABSENT — that is qualitative
    private-credit redemption-gate data from a different source, never
    derivable from FINRA margin statistics.
    """
    latest_month, current = rows[-1]
    prior = rows[-2][1]
    record_month, record_value = max(rows, key=lambda t: t[1])

    mom_pct = round((current / prior - 1.0) * 100.0, 2) if prior else None

    yoy_pct: Optional[float] = None
    if len(rows) >= 13:
        yr_ago = rows[-13][1]
        if yr_ago:
            yoy_pct = round((current / yr_ago - 1.0) * 100.0, 2)

    return {
        # ── CHAIN_3 contract keys (cascade.py) ──
        "current":            current,          # $ millions
        "mom_pct":            mom_pct,
        "at_nominal_record":  current >= record_value,
        # ── audit context ──
        "latest_month":       latest_month,
        "yoy_pct":            yoy_pct,
        "record_value":       record_value,
        "record_month":       record_month,
        "units":              "USD millions",
        "n_months":           len(rows),
        "history_tail":       rows[-_HISTORY_TAIL_MONTHS:],
    }


def fetch_margin_debt(spec: FetchSpec) -> List[DataReading]:
    """
    FINRA_MARGIN_DEBT fetcher (DataSource.FINRA_WEB). Returns a single
    DataReading whose value dict feeds both M17 CHAIN_3 (cascade.py) and
    the ENG-50 trend layer's margin_debt_fragility_flag
    (analysis/trend_signal.py:derive_margin_fragility_flag).

    Any failure degrades to an invalid reading with FETCH_FAILED — CHAIN_3
    then reports "cannot be scored" and the trend flag derives to None,
    exactly the pre-ENG-54 behavior.
    """
    import requests

    try:
        resp = requests.get(
            MARGIN_STATS_XLSX_URL,
            headers={"User-Agent": _UA},
            timeout=_TIMEOUT_S,
        )
        resp.raise_for_status()
        rows = _parse_margin_xlsx(resp.content)
        value = _derive_margin_metrics(rows)
    except Exception as e:
        logger.warning(f"FINRA margin statistics fetch failed ({spec.id}): {e}")
        return [DataReading(
            spec_id=spec.id,
            value=None,
            source=DataSource.FINRA_WEB,
            fetched_at=datetime.datetime.utcnow(),
            quality_flags=[f"FETCH_FAILED: {e}"],
        )]

    # quality_flags stays reserved for genuine quality problems: the CLI
    # fallback path retries any flagged reading, and is_valid semantics key
    # off flag prefixes — the at-record status is signal, not a quality
    # issue, and already lives in the value dict (at_nominal_record).
    return [DataReading(
        spec_id=spec.id,
        value=value,
        source=DataSource.FINRA_WEB,
        fetched_at=datetime.datetime.utcnow(),
        quality_flags=[],
    )]
