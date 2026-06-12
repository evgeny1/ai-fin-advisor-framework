"""
tests/test_stage3/test_cascade.py — Unit tests for analysis/cascade.py.

Maps to: M17_SystemicCascadeWarning.md.
Tests: sector_stress_score, compute_yield_curve_signal, assess_cascade_level.
All tests are pure — no file I/O, no network.
"""
from __future__ import annotations

import pytest
from datetime import datetime
from typing import Dict

from advisor.analysis.cascade import (
    assess_cascade_level,
    compute_yield_curve_signal,
    sector_stress_score,
)
from advisor.types import (
    CalibrationState,
    CascadeLevel,
    CreditSignal,
    CurveState,
    DataReading,
    DataSource,
    DTimingSignal,
    EPathwayType,
    EWatchFlag,
)

# ── Helpers ────────────────────────────────────────────────────────────────────

def _r(spec_id: str, value, *, failed: bool = False) -> DataReading:
    flags = ["FETCH_FAILED"] if failed else []
    return DataReading(
        spec_id=spec_id,
        value=value,
        source=DataSource.YFINANCE,
        fetched_at=datetime(2026, 6, 12),
        quality_flags=flags,
    )


def _credit(
    *,
    hy_oas: float = 400.0,
    hy_median: float = 280.0,
    ig_oas: float = 120.0,
    ig_median: float = 90.0,
    hy_stress: bool = False,
    hy_recession: bool = False,
    ig_tx: bool = False,
) -> CreditSignal:
    return CreditSignal(
        hy_oas=hy_oas,
        hy_median_180d=hy_median,
        ig_oas=ig_oas,
        ig_median_180d=ig_median,
        ccc_oas=900.0,
        move=85.0,
        hy_stress_beginning=hy_stress,
        hy_recession_pricing=hy_recession,
        ig_transmission_reached=ig_tx,
        ccc_tail_first_widening=False,
        convergence_text="Calm credit environment.",
        quality_flags=[],
    )


# ── sector_stress_score ────────────────────────────────────────────────────────

class TestSectorStressScore:

    def test_all_data_missing_score_zero(self, cal: CalibrationState):
        score, fires, watch, flags = sector_stress_score({}, cal)
        assert score == 0
        assert not any(fires.values())
        assert "FARM_FILINGS_YOY: unavailable" in " ".join(flags)

    def test_chain1_fires(self, cal: CalibrationState):
        readings = {
            "FARM_FILINGS_YOY":   _r("FARM_FILINGS_YOY", 55.0),   # >= 50
            "NATGAS_HENRY_HUB":   _r("NATGAS_HENRY_HUB", 6.50),   # >= 6.00
        }
        score, fires, _, _ = sector_stress_score(readings, cal)
        assert fires["CHAIN_1"] is True
        assert score >= 1

    def test_chain1_natgas_below_threshold_not_fired(self, cal: CalibrationState):
        readings = {
            "FARM_FILINGS_YOY":   _r("FARM_FILINGS_YOY", 60.0),
            "NATGAS_HENRY_HUB":   _r("NATGAS_HENRY_HUB", 5.50),  # < 6.00
        }
        score, fires, _, _ = sector_stress_score(readings, cal)
        assert fires["CHAIN_1"] is False

    def test_chain1_farm_below_threshold_not_fired(self, cal: CalibrationState):
        readings = {
            "FARM_FILINGS_YOY":   _r("FARM_FILINGS_YOY", 30.0),  # < 50
            "NATGAS_HENRY_HUB":   _r("NATGAS_HENRY_HUB", 7.00),
        }
        score, fires, _, _ = sector_stress_score(readings, cal)
        assert fires["CHAIN_1"] is False

    def test_chain2_fires(self, cal: CalibrationState):
        # KRE underperforms SPX by 20pp; SOFR-DFF = 15bps
        readings = {
            "KRE":                   _r("KRE",   {"change_90d": -0.20}),   # -20%
            "BROAD_EQUITY_TRAILING": _r("BET",   {"change_90d": -0.03}),   # -3%
            "SOFR":                  _r("SOFR",  4.45),
            "DFF":                   _r("DFF",   4.30),   # SOFR-DFF = 15bps >= 10
        }
        score, fires, _, _ = sector_stress_score(readings, cal)
        assert fires["CHAIN_2"] is True

    def test_chain2_sofr_insufficient_not_fired(self, cal: CalibrationState):
        readings = {
            "KRE":                   _r("KRE",   {"change_90d": -0.20}),
            "BROAD_EQUITY_TRAILING": _r("BET",   {"change_90d": -0.03}),
            "SOFR":                  _r("SOFR",  4.33),
            "DFF":                   _r("DFF",   4.30),   # SOFR-DFF = 3bps < 10
        }
        score, fires, _, _ = sector_stress_score(readings, cal)
        assert fires["CHAIN_2"] is False

    def test_chain2_kre_outperforms_not_fired(self, cal: CalibrationState):
        readings = {
            "KRE":                   _r("KRE",   {"change_90d":  0.05}),  # KRE +5%
            "BROAD_EQUITY_TRAILING": _r("BET",   {"change_90d": -0.05}),  # SPX -5% — KRE outperforms
            "SOFR":                  _r("SOFR",  4.45),
            "DFF":                   _r("DFF",   4.30),
        }
        score, fires, _, _ = sector_stress_score(readings, cal)
        assert fires["CHAIN_2"] is False

    def test_chain3_fires_on_mom_decline(self, cal: CalibrationState):
        # MoM = -7% <= -5% threshold
        readings = {
            "FINRA_MARGIN_DEBT": _r("FMD", {"current": 850.0, "mom_pct": -7.0}),
        }
        score, fires, _, _ = sector_stress_score(readings, cal)
        assert fires["CHAIN_3"] is True

    def test_chain3_watch_at_record(self, cal: CalibrationState):
        # at_nominal_record = True, but MoM decline within threshold
        readings = {
            "FINRA_MARGIN_DEBT": _r("FMD", {"current": 900.0, "at_nominal_record": True, "mom_pct": -2.0}),
        }
        score, fires, watch, _ = sector_stress_score(readings, cal)
        assert watch["CHAIN_3"] is True
        assert fires["CHAIN_3"] is False  # MoM not severe enough

    def test_chain3_fires_via_gate_count(self, cal: CalibrationState):
        # gate_count_90d = 3 >= threshold of 3
        readings = {
            "FINRA_MARGIN_DEBT": _r("FMD", {"current": 800.0, "gate_count_90d": 3}),
        }
        score, fires, _, _ = sector_stress_score(readings, cal)
        assert fires["CHAIN_3"] is True

    def test_chain4_always_zero_without_t1_confirmed(self, cal: CalibrationState):
        readings = {
            "CORP_BANKRUPTCY_QUARTERLY": _r("CBQ", 350.0),  # >= fires threshold of 300
        }
        score, fires, _, flags = sector_stress_score(readings, cal, chain_4_t1_confirmed=False)
        assert fires["CHAIN_4"] is False
        assert any("T1 source not confirmed" in f for f in flags)

    def test_chain4_fires_with_t1_confirmed(self, cal: CalibrationState):
        readings = {
            "CORP_BANKRUPTCY_QUARTERLY": _r("CBQ", 350.0),  # >= 300 threshold
        }
        score, fires, _, _ = sector_stress_score(readings, cal, chain_4_t1_confirmed=True)
        assert fires["CHAIN_4"] is True

    def test_chain4_watch_range_with_t1_confirmed(self, cal: CalibrationState):
        # Between watch (220) and fires (300)
        readings = {
            "CORP_BANKRUPTCY_QUARTERLY": _r("CBQ", 250.0),
        }
        score, fires, _, flags = sector_stress_score(readings, cal, chain_4_t1_confirmed=True)
        assert fires["CHAIN_4"] is False
        assert any("WATCH" in f for f in flags)

    def test_score_capped_at_3(self, cal: CalibrationState):
        # Fire CHAIN_1, CHAIN_3 MoM, CHAIN_4 T1, and CHAIN_2 — score would be 4 raw → 3
        readings = {
            "FARM_FILINGS_YOY":          _r("FFY", 60.0),
            "NATGAS_HENRY_HUB":          _r("NHH", 7.00),
            "FINRA_MARGIN_DEBT":         _r("FMD", {"current": 900.0, "mom_pct": -8.0}),
            "CORP_BANKRUPTCY_QUARTERLY": _r("CBQ", 400.0),
            "KRE":                       _r("KRE", {"change_90d": -0.25}),
            "BROAD_EQUITY_TRAILING":     _r("BET", {"change_90d": -0.05}),
            "SOFR":                      _r("SOFR", 4.50),
            "DFF":                       _r("DFF",  4.30),
        }
        score, fires, _, _ = sector_stress_score(readings, cal, chain_4_t1_confirmed=True)
        assert score <= 3


# ── compute_yield_curve_signal ─────────────────────────────────────────────────

class TestYieldCurveSignal:

    def _yc_reading(self, y2: float, y10: float, m3: float, y30: float = 5.0) -> DataReading:
        return _r("YIELD_CURVE", {"year2": y2, "year10": y10, "month3": m3, "year30": y30})

    def test_inverted_both_spreads_negative(self, cal: CalibrationState):
        readings = {"YIELD_CURVE": self._yc_reading(y2=4.8, y10=4.3, m3=5.1)}
        sig = compute_yield_curve_signal(readings, cal)
        assert sig.curve_state == CurveState.INVERTED
        assert sig.spread_10y_2y is not None and sig.spread_10y_2y < 0
        assert sig.spread_10y_3m is not None and sig.spread_10y_3m < 0

    def test_normal_both_spreads_positive(self, cal: CalibrationState):
        readings = {"YIELD_CURVE": self._yc_reading(y2=4.0, y10=4.8, m3=3.9)}
        sig = compute_yield_curve_signal(readings, cal)
        assert sig.curve_state == CurveState.NORMAL_OR_STEEP
        assert sig.d_timing_signal == DTimingSignal.MONITORING

    def test_partial_inversion(self, cal: CalibrationState):
        # 10y-2y negative, 10y-3m positive
        readings = {"YIELD_CURVE": self._yc_reading(y2=4.8, y10=4.5, m3=4.2)}
        sig = compute_yield_curve_signal(readings, cal)
        assert sig.curve_state == CurveState.PARTIAL_INVERSION

    def test_d_timing_curve_inverted(self, cal: CalibrationState):
        readings = {"YIELD_CURVE": self._yc_reading(y2=5.0, y10=4.2, m3=5.2)}
        sig = compute_yield_curve_signal(readings, cal)
        assert sig.d_timing_signal == DTimingSignal.CURVE_INVERTED

    def test_recession_onset_pattern_when_prior_inverted_now_normal(
        self, cal: CalibrationState
    ):
        readings = {"YIELD_CURVE": self._yc_reading(y2=4.0, y10=4.8, m3=3.9)}
        sig = compute_yield_curve_signal(
            readings, cal, prior_curve_was_inverted=True
        )
        assert sig.d_timing_signal == DTimingSignal.RECESSION_ONSET_PATTERN
        assert sig.d_timing_estimate is not None

    def test_no_recession_onset_when_prior_not_inverted(self, cal: CalibrationState):
        readings = {"YIELD_CURVE": self._yc_reading(y2=4.0, y10=4.8, m3=3.9)}
        sig = compute_yield_curve_signal(
            readings, cal, prior_curve_was_inverted=False
        )
        assert sig.d_timing_signal == DTimingSignal.MONITORING

    def test_e_watch_fires_above_alert_threshold(self, cal: CalibrationState):
        # Alert threshold = 150bps / 100 = 1.5% — use 1.6
        readings = {
            "YIELD_CURVE": self._yc_reading(y2=4.0, y10=4.8, m3=3.9),
            "THREEFYTP10": _r("TFP", 1.6),
        }
        sig = compute_yield_curve_signal(readings, cal)
        assert sig.e_watch_flag == EWatchFlag.E_PATHWAY_WATCH

    def test_e_watch_clear_below_threshold(self, cal: CalibrationState):
        readings = {
            "YIELD_CURVE": self._yc_reading(y2=4.0, y10=4.8, m3=3.9),
            "THREEFYTP10": _r("TFP", 0.5),  # < 1.0 (warning) and < 1.5 (alert)
        }
        sig = compute_yield_curve_signal(readings, cal)
        assert sig.e_watch_flag == EWatchFlag.CLEAR

    def test_e_pathway_default_reserve_erosion(self, cal: CalibrationState):
        # No DXY reading → default
        readings = {"YIELD_CURVE": self._yc_reading(y2=4.0, y10=4.8, m3=3.9)}
        sig = compute_yield_curve_signal(readings, cal)
        assert sig.e_pathway_type == EPathwayType.RESERVE_EROSION
        assert any("RESERVE_EROSION" in f for f in sig.quality_flags)

    def test_e_pathway_systemic_liquidity_dxy_strong_positive(
        self, cal: CalibrationState
    ):
        # DXY strengthening >3% without IG+sovereign convergence → SYSTEMIC
        readings = {
            "YIELD_CURVE": self._yc_reading(y2=4.0, y10=4.8, m3=3.9),
            "DXY":         _r("DXY", {"change_30d": 0.05}),  # +5%
        }
        sig = compute_yield_curve_signal(readings, cal)
        assert sig.e_pathway_type == EPathwayType.SYSTEMIC_LIQUIDITY

    def test_e_pathway_reserve_erosion_dxy_weakening(self, cal: CalibrationState):
        readings = {
            "YIELD_CURVE": self._yc_reading(y2=4.0, y10=4.8, m3=3.9),
            "DXY":         _r("DXY", {"change_30d": -0.05}),  # -5%
        }
        sig = compute_yield_curve_signal(readings, cal)
        assert sig.e_pathway_type == EPathwayType.RESERVE_EROSION

    def test_e_pathway_systemic_with_full_conditions(self, cal: CalibrationState):
        # IG transmission + sovereign CDS widening + DXY strengthening → SYSTEMIC
        credit = _credit(ig_tx=True)
        readings = {
            "YIELD_CURVE": self._yc_reading(y2=4.0, y10=4.8, m3=3.9),
            "DXY":         _r("DXY", {"change_30d": 0.02}),  # flat but IG+CDS present
        }
        sig = compute_yield_curve_signal(
            readings, cal, credit, sovereign_cds_widening=True
        )
        assert sig.e_pathway_type == EPathwayType.SYSTEMIC_LIQUIDITY

    def test_missing_yield_curve_returns_none_state(self, cal: CalibrationState):
        sig = compute_yield_curve_signal({}, cal)
        assert sig.curve_state is None
        assert any("YIELD_CURVE" in f for f in sig.quality_flags)


# ── assess_cascade_level ──────────────────────────────────────────────────────

class TestAssessCascadeLevel:

    def test_monitoring_with_no_chains(self, cal: CalibrationState):
        sig = assess_cascade_level({}, cal)
        assert sig.level == CascadeLevel.MONITORING
        assert sig.active_chains_count == 0

    def test_alert_with_two_active_chains(self, cal: CalibrationState):
        # CHAIN_1 + CHAIN_3 MoM
        readings = {
            "FARM_FILINGS_YOY":  _r("FFY", 55.0),
            "NATGAS_HENRY_HUB":  _r("NHH", 7.0),
            "FINRA_MARGIN_DEBT": _r("FMD", {"current": 900.0, "mom_pct": -8.0}),
        }
        sig = assess_cascade_level(readings, cal)
        assert sig.level == CascadeLevel.ALERT
        assert sig.active_chains_count >= 2

    def test_pre_position_with_three_active_chains(self, cal: CalibrationState):
        readings = {
            "FARM_FILINGS_YOY":          _r("FFY", 60.0),
            "NATGAS_HENRY_HUB":          _r("NHH", 7.0),
            "FINRA_MARGIN_DEBT":         _r("FMD", {"current": 900.0, "mom_pct": -8.0}),
            "CORP_BANKRUPTCY_QUARTERLY": _r("CBQ", 400.0),
            "KRE":                       _r("KRE", {"change_90d": -0.25}),
            "BROAD_EQUITY_TRAILING":     _r("BET", {"change_90d": -0.05}),
            "SOFR":                      _r("SOFR", 4.50),
            "DFF":                       _r("DFF",  4.30),
        }
        sig = assess_cascade_level(readings, cal, chain_4_t1_confirmed=True)
        assert sig.level == CascadeLevel.PRE_POSITION

    def test_pre_position_triggered_by_m11_approaching(self, cal: CalibrationState):
        # Credit signal: HY_OAS > median + 150*0.70 = median + 105
        # median = 280, threshold_70pct = 280 + 105 = 385; HY_OAS = 400 → M11_approaching
        credit = _credit(hy_oas=400.0, hy_median=280.0)
        sig = assess_cascade_level({}, cal, credit_signal=credit)
        assert sig.level == CascadeLevel.PRE_POSITION

    def test_monitoring_when_m11_not_approaching(self, cal: CalibrationState):
        # HY_OAS = 350, median = 280, threshold_70pct = 385 → 350 < 385 → not approaching
        credit = _credit(hy_oas=350.0, hy_median=280.0)
        sig = assess_cascade_level({}, cal, credit_signal=credit)
        assert sig.level == CascadeLevel.MONITORING

    def test_yield_curve_embedded_in_signal(self, cal: CalibrationState):
        readings = {
            "YIELD_CURVE": _r("YC", {"year2": 5.0, "year10": 4.2, "month3": 5.3, "year30": 4.8}),
        }
        sig = assess_cascade_level(readings, cal)
        assert sig.yield_curve is not None
        assert sig.yield_curve.curve_state == CurveState.INVERTED

    def test_score_reported_correctly(self, cal: CalibrationState):
        readings = {
            "FARM_FILINGS_YOY": _r("FFY", 55.0),
            "NATGAS_HENRY_HUB": _r("NHH", 7.0),
        }
        sig = assess_cascade_level(readings, cal)
        assert sig.sector_stress_score == 1
        assert sig.chain_fires["CHAIN_1"] is True

    def test_quality_flags_deduplicated(self, cal: CalibrationState):
        sig = assess_cascade_level({}, cal)
        flags = sig.quality_flags
        # No duplicates
        assert len(flags) == len(set(flags))
