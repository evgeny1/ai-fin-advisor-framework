"""
analysis/trend_signal.py — ENG-50/ENG-55: deterministic trend/rotation
signal layer. Additive, shadow-mode only. NEVER feeds
M03.DeriveScenarioProbabilities() — same NEVER rule M14/M17 already
follow (see FRAMEWORK_BACKLOG.md ENG-50).

Two genuinely different comparator types, not one formula shape forced
onto both (ENG-55 finding, client-confirmed 2026-07-07):

  Mode 1 — RETURN_SPREAD: comparator is a tradeable peer/commodity price
  series, so instrument_return minus comparator_return is a real spread
  in percentage-point terms. Used by XAR (ITA/PPA), MAGS (QQQM), AIPO and
  COPX (weighted composite blends of their own comparator baskets).

  Mode 2 — OWN_TREND_CONFIRMED: comparator is a macro driver (DXY, real
  yield, cross-asset trend breadth) that isn't return-comparable to the
  instrument at all — the question is whether the instrument's OWN price
  trend is confirmed by its known macro driver, not a peer spread. Used
  by DBMF (breadth) and SGOL/SIVR (real-yield+DXY agreement).

  MLPX is a hybrid: Mode 1 vs Brent (BZ=F), gated by a Mode-2-style HY OAS
  confirmation (credit tightening confirms; widening downgrades a real
  directional call to INCONCLUSIVE; the confirmation input itself being
  unavailable downgrades to DATA_UNAVAILABLE instead — ENG-60).

Lookback window (client-confirmed 2026-07-07): blended ~21 trading days
(~1mo) + ~63 trading days (~1qtr), both windows' sign must agree or the
read is INCONCLUSIVE — same "require agreement, else neutral" pattern
GAP-16 already uses for SGOL/SIVR's real-yield+DXY gate (see
analysis/range_position.py). Deliberately NOT reusing GAP-16's own
computed favorable/unfavorable verdict for SGOL/SIVR's Mode 2 confirm
here — that would couple this module's decision logic to GAP-16's own
specific gating conditions (range width, EV-band bounds) which are
irrelevant to this module's purpose. Reusing the underlying FETCHED DATA
(REAL_YIELD_10Y_TREND, DXY_TREND readings) is fine and done below; the
agreement-gate LOGIC is reimplemented independently, per the coupling-risk
discipline flagged in FRAMEWORK_BACKLOG_ARCHIVE.md's ENG-55 writeup.

NOISE_FLOOR below is a placeholder, NOT independently calibrated — ENG-55
explicitly deferred this to real M16-style historical-analog work
(portfolio_backtest_mcp is the likely tool once that happens). Chosen
conservatively so the shadow trial produces some signal rather than none;
revisit once the 8-week trial has real outcome data. Same posture for the
HY_OAS session-cadence approximation in MLPX's confirm leg below — flagged
inline, not silently treated as precise.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .trend import directional_trend, net_change_pct
from ..types import ComparatorMode, TrendSignalCode

# ⚑ Placeholder, not independently calibrated — see module docstring.
NOISE_FLOOR_PCT = 2.0

SHORT_WINDOW_DAYS = 21
MEDIUM_WINDOW_DAYS = 63

# Per-instrument comparator/mode table — the ENG-55 design as code.
# Reusable materiality rule (client-confirmed): any single ComponentVector
# weight below 10% is excluded from a composite comparator and the
# remainder renormalized. Already applied below for AIPO (PDT 4% +
# UNCLASSIFIED 7% excluded; RAC/STG/IHC renormalized 0.55/0.16/0.11 -> sum
# 0.82 -> 0.671/0.195/0.134) — see FRAMEWORK_BACKLOG_ARCHIVE.md ENG-55.
TREND_SIGNAL_CONFIG: Dict[str, Dict[str, Any]] = {
    "MLPX": {
        "mode": ComparatorMode.HYBRID,
        "comparator_symbols": ["BZ=F"],
        "comparator_weights": [1.0],
        "comparator_detail": "BZ=F return-spread, HY_OAS confirmation gate",
    },
    "DBMF": {
        "mode": ComparatorMode.OWN_TREND_CONFIRMED,
        "breadth_symbols": ["DXY_TREND", "BRENT_TREND", "GOLD_TREND", "SP500_TREND"],
        "dxy_symbol": "DXY_TREND",
        "comparator_detail": "own-trend confirmed by DXY direction + 4-market breadth (>=3/4 trending)",
    },
    "XAR": {
        "mode": ComparatorMode.RETURN_SPREAD,
        "comparator_symbols": ["ITA", "PPA"],
        "comparator_weights": [0.5, 0.5],
        "comparator_detail": "0.5xITA+0.5xPPA",
    },
    "AIPO": {
        "mode": ComparatorMode.RETURN_SPREAD,
        "comparator_symbols": ["PAVE", "QQQM", "URA"],
        "comparator_weights": [0.671, 0.195, 0.134],
        "comparator_detail": "0.671xPAVE+0.195xQQQM+0.134xURA (renormalized, PDT+UNCLASSIFIED excluded)",
    },
    "COPX": {
        "mode": ComparatorMode.RETURN_SPREAD,
        "comparator_symbols": ["HG=F", "VEA"],
        "comparator_weights": [0.75, 0.25],
        "comparator_detail": "0.75xHG=F+0.25xVEA",
    },
    "SGOL": {
        "mode": ComparatorMode.OWN_TREND_CONFIRMED,
        "confirm_reading_ids": ["REAL_YIELD_10Y_TREND", "DXY_TREND"],
        "comparator_detail": "own-trend confirmed by REAL_YIELD_10Y_TREND + DXY agreement gate",
    },
    "SIVR": {
        "mode": ComparatorMode.OWN_TREND_CONFIRMED,
        "confirm_reading_ids": ["REAL_YIELD_10Y_TREND", "DXY_TREND"],
        "comparator_detail": "own-trend confirmed by REAL_YIELD_10Y_TREND + DXY agreement gate (v1 simplification, same as SGOL)",
    },
    "MAGS": {
        "mode": ComparatorMode.RETURN_SPREAD,
        "comparator_symbols": ["QQQM"],
        "comparator_weights": [1.0],
        "comparator_detail": "QQQM",
    },
}


# ── Shared helpers ──────────────────────────────────────────────────────────

def _window_pct_change(closes: List[float], window_days: int) -> Optional[float]:
    """pct change over the trailing `window_days` (trading days), using
    trend.py's net_change_pct on just that slice. None if insufficient
    history — caller must treat this as INCONCLUSIVE, never as zero."""
    if len(closes) < window_days + 1:
        return None
    return net_change_pct(closes[-(window_days + 1):])


def _weighted_composite_closes(
    histories: Dict[str, List[float]],
    symbols: List[str],
    weights: List[float],
) -> Optional[List[float]]:
    """
    Synthetic weighted-blend comparator return series (AIPO/COPX/XAR
    composite case). Returns None — not a partial blend — if ANY symbol's
    history is missing or empty; a blend silently built from N-1 of N
    weights would misrepresent the intended composite rather than just
    degrade it. Aligns on the shortest common length among the symbols
    (all normally come from ONE batched fetch, so lengths should match).
    """
    series_list: List[List[float]] = []
    for sym in symbols:
        s = histories.get(sym)
        if not s:
            return None
        series_list.append(s)

    min_len = min(len(s) for s in series_list)
    if min_len < 2:
        return None

    aligned = [s[-min_len:] for s in series_list]
    composite: List[float] = []
    for i in range(min_len):
        composite.append(sum(w * aligned[j][i] for j, w in enumerate(weights)))
    return composite


def _agreement_gate(
    series_a: Optional[List[float]], series_b: Optional[List[float]],
    threshold_pct: float = NOISE_FLOOR_PCT,
) -> Tuple[Optional[bool], bool]:
    """
    Returns (confirms, data_available).

    confirms: True iff both series show the SAME directional_trend over
    their own full supplied window; False if they disagree; None if
    either series' own directional_trend is indeterminate.

    data_available: False only when either raw series itself is missing
    or empty (a genuine fetch gap). True whenever both raw series were
    present, even if directional_trend couldn't resolve a direction for
    one or both — that's a computed result on real data, not a missing
    input. Carries ENG-60's DATA_UNAVAILABLE-vs-INCONCLUSIVE distinction
    one layer deeper into this gate (FRAMEWORK_BACKLOG.md ENG-63) — a
    materially-trending real-yield series that merely dipped below its
    own starting value before recovering was previously indistinguishable
    from real-yield data never having been fetched at all.

    Deliberately independent of GAP-16's own range_position_signals
    verdict — see module docstring.
    """
    if not series_a or not series_b:
        return None, False
    dir_a = directional_trend(series_a, threshold_pct)
    dir_b = directional_trend(series_b, threshold_pct)
    if dir_a is None or dir_b is None:
        return None, True
    return dir_a == dir_b, True


# ── Mode 1: return-spread ──────────────────────────────────────────────────

def evaluate_return_spread(
    ticker: str,
    instrument_closes: List[float],
    comparator_closes: List[float],
) -> Tuple[TrendSignalCode, Optional[str], Optional[str], List[str]]:
    """
    Mode 1. Returns (signal, rs_short_display, rs_medium_display, flags).
    rs_short/medium displays are human-readable pp strings for logging —
    the raw floats aren't returned since the caller only needs the
    direction/magnitude gate result, not the numbers themselves.
    """
    flags: List[str] = []
    rs_short = _window_pct_change(instrument_closes, SHORT_WINDOW_DAYS)
    rs_medium = _window_pct_change(instrument_closes, MEDIUM_WINDOW_DAYS)
    cs_short = _window_pct_change(comparator_closes, SHORT_WINDOW_DAYS)
    cs_medium = _window_pct_change(comparator_closes, MEDIUM_WINDOW_DAYS)

    if None in (rs_short, rs_medium, cs_short, cs_medium):
        flags.append(f"{ticker}: insufficient history for Mode 1 return-spread windows")
        # ENG-60: missing input, not a computed non-result -- DATA_UNAVAILABLE.
        return TrendSignalCode.DATA_UNAVAILABLE, None, None, flags

    spread_short = rs_short - cs_short
    spread_medium = rs_medium - cs_medium

    same_sign = (spread_short > 0) == (spread_medium > 0)
    material = abs(spread_short) >= NOISE_FLOOR_PCT and abs(spread_medium) >= NOISE_FLOOR_PCT

    if same_sign and material and spread_short != 0:
        code = TrendSignalCode.STRENGTHENING if spread_short > 0 else TrendSignalCode.WEAKENING
    else:
        code = TrendSignalCode.INCONCLUSIVE

    return code, f"{spread_short:+.2f}pp", f"{spread_medium:+.2f}pp", flags


# ── Mode 2: own-trend, macro-confirmed ─────────────────────────────────────

def evaluate_own_trend_confirmed(
    ticker: str,
    instrument_closes: List[float],
    macro_confirms: Optional[bool],
    confirm_data_available: bool = False,
) -> Tuple[TrendSignalCode, Optional[str], Optional[str], List[str]]:
    """
    Mode 2. `macro_confirms` is computed by the caller per-instrument
    (breadth check for DBMF, agreement gate for SGOL/SIVR) since the
    confirmation mechanism genuinely differs by instrument — this
    function only applies the shared own-trend + confirmation-gate rule
    once the caller has resolved macro_confirms to True/False/None.

    `confirm_data_available` distinguishes WHY macro_confirms is None
    (FRAMEWORK_BACKLOG.md ENG-63, carrying ENG-60's DATA_UNAVAILABLE-vs-
    INCONCLUSIVE split one layer deeper): False means the confirmation
    gate's own raw inputs were missing (a genuine fetch gap) -- the
    default, for backward compatibility with any caller that hasn't been
    updated to pass it. True means the gate ran on real, present data but
    didn't produce an agreeing direction (e.g. one leg's own
    directional_trend was indeterminate) -- a computed result, not a
    missing one.
    """
    flags: List[str] = []
    if len(instrument_closes) < MEDIUM_WINDOW_DAYS + 1:
        flags.append(f"{ticker}: insufficient own-price history for Mode 2 windows")
        # ENG-60: no own-price basis to compute anything -- DATA_UNAVAILABLE.
        return TrendSignalCode.DATA_UNAVAILABLE, None, None, flags

    own_short = directional_trend(instrument_closes[-(SHORT_WINDOW_DAYS + 1):], NOISE_FLOOR_PCT)
    own_medium = directional_trend(instrument_closes[-(MEDIUM_WINDOW_DAYS + 1):], NOISE_FLOOR_PCT)

    if macro_confirms is None:
        if confirm_data_available:
            # ENG-63: the gate ran on real, present data and genuinely found
            # no agreeing direction -- a computed non-result, not a missing one.
            flags.append(f"{ticker}: macro confirmation gate computed no clear agreement this session")
            return TrendSignalCode.INCONCLUSIVE, own_short, own_medium, flags
        # ENG-60: the confirmation gate's own inputs were missing -- own_short/
        # own_medium may well agree here, but STRENGTHENING/WEAKENING would
        # be a claim this function has no basis to make without knowing
        # whether the gate confirms or disconfirms. own_short/own_medium are
        # still returned for informational display.
        flags.append(f"{ticker}: macro confirmation input unavailable this session")
        return TrendSignalCode.DATA_UNAVAILABLE, own_short, own_medium, flags

    if own_short is not None and own_short == own_medium and macro_confirms:
        code = TrendSignalCode.STRENGTHENING if own_short == "up" else TrendSignalCode.WEAKENING
    else:
        code = TrendSignalCode.INCONCLUSIVE

    return code, own_short, own_medium, flags


# ── DBMF's breadth confirmation ────────────────────────────────────────────

def _dbmf_macro_confirms(
    own_short: Optional[str],
    own_short_data_available: bool,
    breadth_readings: Dict[str, Optional[List[float]]],
    dxy_closes: Optional[List[float]],
) -> Tuple[Optional[bool], List[str], bool]:
    """
    DXY direction agrees with DBMF's own_short short-window direction AND
    breadth >= 3 of 4 (Brent/Gold/DXY/S&P each independently trending, any
    direction). Exact reuse of the breadth concept GAP-16 already defined
    for DBMF's own §13 TSC evaluation (see FRAMEWORK_BACKLOG_ARCHIVE.md
    ENG-55) — reimplemented here independently per the coupling-risk note.

    Returns (confirms, flags, data_available). own_short_data_available is
    supplied by the caller (which holds DBMF's raw own-price history and
    already knows whether it was long enough to compute a short-window
    read at all) — that's the only genuine data gap on the own-price side.
    own_short being None despite own_short_data_available=True, or dxy_dir
    resolving to None on a present dxy_closes series, are both computed
    results on real data, not missing inputs — data_available stays True
    in those cases (FRAMEWORK_BACKLOG.md ENG-63).

    dxy_dir and the breadth check both use require_no_reversal=True — this
    breadth check is an explicit reuse of Calibration_State.md 13's own
    DBMF sustaining-condition concept (checking whether OTHER markets are
    trending as a proxy for a supportive trend-following backdrop), not a
    plain instrument trend read, so it keeps that condition's documented
    "without full reversal" semantics (FRAMEWORK_BACKLOG.md ENG-65). This
    is deliberately NOT applied to own_short (DBMF's own price, computed by
    the caller) — DBMF's own price is a plain instrument trend, evaluated
    the same standard way as any other ticker.
    """
    flags: List[str] = []
    if not dxy_closes:
        return None, ["DBMF: DXY_TREND unavailable — breadth check skipped"], False
    if not own_short_data_available:
        return None, ["DBMF: insufficient own-price history — breadth check skipped"], False
    if own_short is None:
        return None, ["DBMF: own short-window trend indeterminate — breadth check skipped"], True

    dxy_dir = directional_trend(dxy_closes, NOISE_FLOOR_PCT, require_no_reversal=True)
    breadth_count = 0
    for sym, closes in breadth_readings.items():
        if closes and directional_trend(closes, NOISE_FLOOR_PCT, require_no_reversal=True) is not None:
            breadth_count += 1

    if dxy_dir is None:
        flags.append("DBMF: DXY_TREND direction indeterminate")
        return None, flags, True

    confirms = (dxy_dir == own_short) and (breadth_count >= 3)
    if breadth_count < 3:
        flags.append(f"DBMF: breadth {breadth_count}/4 — below the 3/4 confirmation threshold")
    return confirms, flags, True


# ── MLPX's HY OAS confirmation (hybrid case) ───────────────────────────────

def _mlpx_hy_oas_confirms(hy_oas_readings: List[Tuple[str, Optional[int]]]) -> Tuple[Optional[bool], List[str]]:
    """
    Tightening (lower now than ~21 trading days ago) confirms; widening
    downgrades a real directional Brent-spread call to INCONCLUSIVE. The
    caller (evaluate_all_trend_signals) downgrades to DATA_UNAVAILABLE
    instead when this function itself returns None (ENG-60) — that
    distinction is applied by the caller, not here.

    hy_oas_readings: chronological (date, hy_oas_bps) pairs from
    Session_Log.md §7 — approximated by comparing the two readings
    closest to a ~21-session/~30-calendar-day gap, NOT a true fixed
    trading-day lookback (§7 is keyed by session, not trading day).
    Flagged explicitly as a v1 simplification, not treated as precise —
    same posture as NOISE_FLOOR_PCT above.
    """
    flags: List[str] = []
    valid = [(d, v) for d, v in hy_oas_readings if v is not None]
    if len(valid) < 2:
        return None, ["MLPX: insufficient HY_OAS session history for confirmation gate"]

    flags.append(
        "MLPX: HY_OAS confirmation approximated from Session_Log.md §7 session "
        "cadence, not a true fixed-trading-day lookback — known v1 simplification"
    )
    now_bps = valid[-1][1]
    prior_bps = valid[0][1]
    return (now_bps < prior_bps), flags


# ── Main entry point ────────────────────────────────────────────────────────

def evaluate_all_trend_signals(
    held_tickers: List[str],
    daily_histories: Dict[str, List[float]],
    weekly_trend_readings: Dict[str, Optional[List[float]]],
    hy_oas_session_history: List[Tuple[str, Optional[int]]],
    dominant_directives: Dict[str, Optional[str]],
    margin_debt_fragility_flag: Optional[str] = None,
    margin_debt_note: Optional[str] = None,
) -> List["TrendSignalReading"]:
    """
    Compute ENG-55's trend/rotation signal for every ticker in
    held_tickers that has a TREND_SIGNAL_CONFIG entry (tickers without one
    are silently skipped, not errored — this module only covers the 8
    instruments ENG-55 scoped, per its own hand-off).

    daily_histories: {symbol: [close, close, ...]} chronological, from
      yfinance_fetcher.fetch_trend_signal_histories() (one batched fetch,
      covers both instruments' own prices and comparator tickers).
    weekly_trend_readings: {spec_id: closes-or-None} for DXY_TREND,
      BRENT_TREND, GOLD_TREND, SP500_TREND, REAL_YIELD_10Y_TREND — all
      already fetched by the existing M18 registry, reused as-is.
    hy_oas_session_history: Session_Log.md §7 (date, hy_oas_bps) pairs,
      chronological — MLPX's confirm leg only.
    dominant_directives: {ticker: dominant_directive_conflict_aware string
      or None} — logged alongside for comparison, per ENG-50's trial
      design; NOT an input to this module's own signal computation.
    """
    from ..types import TrendSignalReading  # local import avoids a cycle at module load

    import datetime
    today = datetime.date.today().isoformat()

    out: List[TrendSignalReading] = []

    for ticker in held_tickers:
        cfg = TREND_SIGNAL_CONFIG.get(ticker)
        if cfg is None:
            continue

        own_closes = daily_histories.get(ticker)
        price_at_signal = own_closes[-1] if own_closes else None
        mode: ComparatorMode = cfg["mode"]
        flags: List[str] = []

        if own_closes is None:
            # ENG-60: no own-price basis at all -- DATA_UNAVAILABLE, not INCONCLUSIVE.
            out.append(TrendSignalReading(
                ticker=ticker, session_date=today,
                rs_signal=TrendSignalCode.DATA_UNAVAILABLE,
                own_short_dir=None, own_medium_dir=None,
                comparator_mode=mode, comparator_detail=cfg["comparator_detail"],
                price_at_signal=None,
                dominant_directive_conflict_aware=dominant_directives.get(ticker),
                margin_debt_fragility_flag=None,
                quality_flags=[f"{ticker}: no own-price daily history this session"],
            ))
            continue

        if mode == ComparatorMode.RETURN_SPREAD:
            comparator_closes = _weighted_composite_closes(
                daily_histories, cfg["comparator_symbols"], cfg["comparator_weights"]
            )
            if comparator_closes is None:
                # ENG-60: missing input, not a computed non-result.
                code, d1, d2 = TrendSignalCode.DATA_UNAVAILABLE, None, None
                flags.append(f"{ticker}: comparator history unavailable this session")
            else:
                code, d1, d2, spread_flags = evaluate_return_spread(ticker, own_closes, comparator_closes)
                flags.extend(spread_flags)

        elif mode == ComparatorMode.HYBRID:
            # MLPX: Mode 1 vs Brent, then gated by HY OAS confirmation.
            comparator_closes = _weighted_composite_closes(
                daily_histories, cfg["comparator_symbols"], cfg["comparator_weights"]
            )
            if comparator_closes is None:
                # ENG-60: missing input, not a computed non-result.
                code, d1, d2 = TrendSignalCode.DATA_UNAVAILABLE, None, None
                flags.append(f"{ticker}: Brent comparator history unavailable this session")
            else:
                code, d1, d2, spread_flags = evaluate_return_spread(ticker, own_closes, comparator_closes)
                flags.extend(spread_flags)
                hy_confirms, hy_flags = _mlpx_hy_oas_confirms(hy_oas_session_history)
                flags.extend(hy_flags)
                # ENG-60: the confirmation gate only vets a REAL directional
                # call from the Brent spread -- if the spread itself already
                # came back INCONCLUSIVE or DATA_UNAVAILABLE, there's no call
                # to vet, and hy_confirms must not override that. Previously
                # this only special-cased hy_confirms is False, which meant
                # hy_confirms is None (gate itself unavailable) silently fell
                # through with no downgrade at all, letting an unconfirmed
                # STRENGTHENING/WEAKENING call pass straight through -- and
                # separately, `code != INCONCLUSIVE` would have wrongly
                # clobbered a DATA_UNAVAILABLE code (insufficient windows)
                # down to INCONCLUSIVE on hy_confirms is False. Both fixed by
                # gating explicitly on code being a real directional call.
                if code in (TrendSignalCode.STRENGTHENING, TrendSignalCode.WEAKENING):
                    if hy_confirms is None:
                        flags.append(
                            "MLPX: HY_OAS confirmation input unavailable — "
                            "downgraded to DATA_UNAVAILABLE per confirmation gate"
                        )
                        code = TrendSignalCode.DATA_UNAVAILABLE
                    elif hy_confirms is False:
                        flags.append("MLPX: HY_OAS widening — downgraded to INCONCLUSIVE per confirmation gate")
                        code = TrendSignalCode.INCONCLUSIVE

        elif mode == ComparatorMode.OWN_TREND_CONFIRMED:
            if ticker == "DBMF":
                own_short_data_available = len(own_closes) >= SHORT_WINDOW_DAYS + 1
                own_short_probe = directional_trend(
                    own_closes[-(SHORT_WINDOW_DAYS + 1):], NOISE_FLOOR_PCT
                ) if own_short_data_available else None
                breadth_readings = {
                    sym: weekly_trend_readings.get(sym)
                    for sym in cfg["breadth_symbols"]
                }
                dxy_closes = weekly_trend_readings.get(cfg["dxy_symbol"])
                confirms, confirm_flags, confirm_data_available = _dbmf_macro_confirms(
                    own_short_probe, own_short_data_available, breadth_readings, dxy_closes
                )
            else:  # SGOL / SIVR
                ids = cfg["confirm_reading_ids"]
                confirms, confirm_data_available = _agreement_gate(
                    weekly_trend_readings.get(ids[0]), weekly_trend_readings.get(ids[1])
                )
                confirm_flags = []
                if confirms is None:
                    if confirm_data_available:
                        confirm_flags.append(f"{ticker}: real-yield/DXY agreement gate computed no clear agreement this session")
                    else:
                        confirm_flags.append(f"{ticker}: real-yield/DXY agreement gate unavailable this session")

            code, d1, d2, own_flags = evaluate_own_trend_confirmed(ticker, own_closes, confirms, confirm_data_available)
            flags.extend(confirm_flags)
            flags.extend(own_flags)

        else:  # pragma: no cover — exhaustive per TREND_SIGNAL_CONFIG's own modes
            code, d1, d2 = TrendSignalCode.INCONCLUSIVE, None, None
            flags.append(f"{ticker}: unrecognized ComparatorMode {mode!r}")

        margin_flag_for_ticker: Optional[str] = None
        if code == TrendSignalCode.STRENGTHENING:
            margin_flag_for_ticker = margin_debt_fragility_flag
            if margin_debt_note:
                flags.append(margin_debt_note)

        out.append(TrendSignalReading(
            ticker=ticker, session_date=today,
            rs_signal=code,
            own_short_dir=d1, own_medium_dir=d2,
            comparator_mode=mode, comparator_detail=cfg["comparator_detail"],
            price_at_signal=round(price_at_signal, 4) if price_at_signal is not None else None,
            dominant_directive_conflict_aware=dominant_directives.get(ticker),
            margin_debt_fragility_flag=margin_flag_for_ticker,
            quality_flags=flags,
        ))

    return out
