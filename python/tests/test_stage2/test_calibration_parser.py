"""
tests/test_stage2/test_calibration_parser.py

Unit tests for advisor/config/calibration.py using inline fixture text.
No file I/O — all fixtures are self-contained strings.
"""
import pytest
from advisor.config.calibration import (
    _parse_cell,
    _parse_version_date,
    _parse_thresholds,
    _parse_return_table,
    _parse_multipliers,
    _parse_floor_params,
    _parse_instruments,
    parse_calibration_state,
)
from advisor.types import ReturnRange

# ── Minimal fixture text ───────────────────────────────────────────────────────

FIXTURE = """\
# Calibration State

# Version: 9.99  Last updated: January 1, 2099 (test fixture)

## Section 1 - Credit Signal Thresholds (relative, 1.5a)

### 1.1 HY Composite - FRED: BAMLH0A0HYM2

| Parameter | Current Value | Type | Notes |
| --- | --- | --- | --- |
| HY_STRESS_DELTA | +150 bps | Calibration-dated | provisional |
| HY_RECESSION_DELTA | +300 bps | Calibration-dated | provisional |
| Velocity overlay | +100 bps over prior 60 days | Fixed structural | |
| Sustain period | 10 trading days | Fixed structural | |

### 1.2 IG Composite - FRED: BAMLC0A0CM

| Parameter | Current Value | Type | Notes |
| --- | --- | --- | --- |
| IG_TRANSMISSION_DELTA | +60 bps | Calibration-dated | provisional |
| Velocity overlay | +40 bps over prior 60 days | Fixed structural | |
| Sustain period | 10 trading days | Fixed structural | |

### 1.3 CCC Tail - FRED: BAMLH0A3HYC

| Parameter | Current Value | Type | Notes |
| --- | --- | --- | --- |
| Ratio divergence | CCC widens 3x composite over 30d | Fixed structural | |
| Absolute divergence floor | CCC +200 bps while composite +<50 bps over 30d | Calibration-dated | |

---

## Section 2 - Energy / Macro Thresholds
placeholder

## Section 4 - Return Table

### 4.1 Expected Real Annualized Return Table

| Role | Scenario A | Scenario B | Scenario C | Scenario D | Scenario E | Scenario F |
| --- | --- | --- | --- | --- | --- | --- |
| systematic_trend_following | [-12, -3]★ | [+15, +30]★ | [+18, +35]★ | [-5, +15]★ | [-8, +8]★ | [-5, +3]★ |
| consumer_defensive_equity | [0, +4]★ | [+2, +6]★ | [+2, +6]★ | [-5, 0]★ | [-8, -2]⚑ | [-3, +2]★ |

### 4.2 IRA Target Multipliers (10-year horizon)

| Scenario | Multiplier | Implied Real Return |
| --- | --- | --- |
| A | 2.0 | ~7.2% |
| B | 1.3 | ~2.7% |
| C | 1.3 | ~2.7% |
| D | 1.3 | ~2.7% |
| E | 1.2 | ~1.8% |
| F | 2.0 | ~7.2% |

### 4.3 Roth IRA Target Multipliers (15-year horizon)

| Scenario | Multiplier |
| --- | --- |
| A | 3.1 |
| B | 1.3 |
| C | 1.3 |
| D | 1.6 |
| E | 1.4 |
| F | 3.1 |

### 4.4 Structural Floor and Concentration Parameters

| Parameter | Value | Type |
| --- | --- | --- |
| Base floor | 0.25 | Calibration-dated |
| Minimum floor | 2% of account | Calibration-dated |
| Concentration cap | 40% | Calibration-dated |
| Floor nominal loss probability threshold | 15% | Calibration-dated |

## Section 5 - Review Cadence
placeholder

## Section 11 - Instrument Registry

### 11.1 Role Registry

| Role | Binding Driver | Added | Status |
| --- | --- | --- | --- |
| systematic_trend_following | multi_asset_price_trends | v1.13 | Active |
| consumer_defensive_equity | consumer_pricing_power | v1.13 | Active |

### 11.2 Notes
placeholder

### 11.3 Active Instrument Registry

#### DBMF
- Components: systematic_trend_following (1.00)
- TAX PLACEMENT: ALL ACCOUNTS.

#### MAGS
- Components: secular_technology_growth (0.85) + broad_market_equity_domestic (0.15)
- TAX PLACEMENT: RETIREMENT ACCOUNTS ONLY. Swap structure.

### 11.4 Candidate Instruments

#### VNQ
- Components: real_estate_equity_income (1.00)
- TAX PLACEMENT: ALL ACCOUNTS.

## Section 12 - M17 Systemic Cascade Warning Thresholds

### 12.1 Agriculture / Fertilizer Chain

| Parameter | Alert Threshold | Notes |
| --- | --- | --- |
| farm_filings_alert | +50% YoY farm chapter 12 bankruptcies | current: below |
| natgas_alert | $6.00/mmBtu sustained 30 days | current: below |
| fertilizer_alert | +50% above 12-month average | monitor |

### 12.2 CRE / Regional Bank Chain

| Parameter | Alert Threshold | Notes |
| --- | --- | --- |
| KRE_alert | KRE −15% vs SPX over 90 days | current: not fired |
| SOFR_DFF_alert | SOFR–DFF spread +10 bp sustained 5 days | current: normal |

### 12.3 Private Credit / Margin Chain (two-mode — v1.20)

| Mode | Parameter | Threshold | Score | Current Status |
| --- | --- | --- | --- | --- |
| WATCH | margin_at_nominal_record | FINRA margin debt at all-time nominal high | 0 | WATCH |
| FIRES | margin_MoM_decline | ≤ −5% MoM after record high | +1 | NOT fired |
| FIRES | gate_count_alert | 3+ named fund gate/suspension events in 90 days | +1 | NOT fired |

### 12.4 Manufacturing / Corporate Stress Chain

| Parameter | Alert Threshold | Confidence | Notes |
| --- | --- | --- | --- |
| bankruptcy_quarterly_WATCH | ≥220/quarter | HIGH ★ | above 2010 level |
| bankruptcy_quarterly_FIRES | ≥300/quarter | HIGH ★ | cascade signal |

### 12.5 Sovereign Stress / Scenario E Watch

| Parameter | Alert Threshold | Notes |
| --- | --- | --- |
| E_term_premium_warning | THREEFYTP10 ≥ 100 bp | Warning threshold |
| E_term_premium_alert | THREEFYTP10 ≥ 150 bp | Alert threshold |
| E_30Y_warning | 30Y Treasury yield ≥ 5.50% | below warning |

### 12.6 Municipal Chain
qualitative only

"""


# ── _parse_cell ────────────────────────────────────────────────────────────────

class TestParseCell:
    def test_simple_range(self):
        r = _parse_cell("[-2, +4]")
        assert r is not None
        assert r.conservative == -2.0
        assert r.upside == 4.0
        assert r.confidence == "MEDIUM"

    def test_high_confidence(self):
        r = _parse_cell("[+15, +30]★")
        assert r.conservative == 15.0
        assert r.upside == 30.0
        assert r.confidence == "HIGH"

    def test_pending_medium(self):
        r = _parse_cell("[-6, 0]⚑")
        assert r.confidence == "PENDING_MEDIUM"

    def test_pending_low(self):
        r = _parse_cell("[3, 8]⚠")
        assert r.confidence == "PENDING_LOW"

    def test_no_match_returns_none(self):
        assert _parse_cell("N/A") is None
        assert _parse_cell("") is None

    def test_positive_both(self):
        r = _parse_cell("[+10, +20]★")
        assert r.conservative == 10.0
        assert r.upside == 20.0


# ── _parse_version_date ────────────────────────────────────────────────────────

class TestParseVersionDate:
    def test_normal(self):
        v, d = _parse_version_date(FIXTURE)
        assert v == "9.99"
        assert "January 1, 2099" in d

    def test_missing_returns_unknown(self):
        v, d = _parse_version_date("no version here")
        assert v == "unknown"
        assert d == "unknown"


# ── _parse_thresholds ─────────────────────────────────────────────────────────

class TestParseThresholds:
    def setup_method(self):
        self.t = _parse_thresholds(FIXTURE)

    def test_hy_stress(self):
        assert self.t.hy_stress_delta == 150

    def test_hy_recession(self):
        assert self.t.hy_recession_delta == 300

    def test_hy_velocity(self):
        assert self.t.hy_velocity_delta == 100

    def test_hy_sustain(self):
        assert self.t.hy_sustain_days == 10

    def test_ig_transmission(self):
        assert self.t.ig_transmission_delta == 60

    def test_ig_velocity(self):
        assert self.t.ig_velocity_delta == 40

    def test_ig_sustain(self):
        assert self.t.ig_sustain_days == 10

    def test_ccc_ratio(self):
        assert self.t.ccc_ratio_multiplier == 3.0

    def test_ccc_floor(self):
        assert self.t.ccc_absolute_floor_bps == 200

    def test_ccc_ceiling(self):
        assert self.t.ccc_composite_ceiling_bps == 50


# ── _parse_return_table ───────────────────────────────────────────────────────

class TestParseReturnTable:
    def setup_method(self):
        self.rt = _parse_return_table(FIXTURE)

    def test_stf_present(self):
        assert "systematic_trend_following" in self.rt

    def test_stf_b_value(self):
        r = self.rt["systematic_trend_following"]["B"]
        assert r.conservative == 15.0
        assert r.upside == 30.0
        assert r.confidence == "HIGH"

    def test_stf_a_negative(self):
        r = self.rt["systematic_trend_following"]["A"]
        assert r.conservative == -12.0

    def test_consumer_defensive_e_pending(self):
        r = self.rt["consumer_defensive_equity"]["E"]
        assert r.confidence == "PENDING_MEDIUM"

    def test_all_six_scenarios(self):
        for s in ("A", "B", "C", "D", "E", "F"):
            assert s in self.rt["systematic_trend_following"]


# ── _parse_multipliers ────────────────────────────────────────────────────────

class TestParseMultipliers:
    def setup_method(self):
        self.m = _parse_multipliers(FIXTURE)

    def test_ira_a(self):
        assert self.m.ira["A"] == 2.0

    def test_ira_e(self):
        assert self.m.ira["E"] == 1.2

    def test_roth_a(self):
        assert self.m.roth["A"] == 3.1

    def test_roth_d(self):
        assert self.m.roth["D"] == 1.6

    def test_all_scenarios_present(self):
        for s in ("A", "B", "C", "D", "E", "F"):
            assert s in self.m.ira
            assert s in self.m.roth


# ── _parse_floor_params ───────────────────────────────────────────────────────

class TestParseFloorParams:
    def setup_method(self):
        self.fp = _parse_floor_params(FIXTURE)

    def test_base_floor(self):
        assert self.fp.base_floor == pytest.approx(0.25)

    def test_min_floor(self):
        assert self.fp.min_floor_pct == pytest.approx(0.02)

    def test_concentration_cap(self):
        assert self.fp.concentration_cap == pytest.approx(0.40)

    def test_loss_prob_threshold(self):
        assert self.fp.floor_loss_prob_threshold == pytest.approx(0.15)


# ── _parse_instruments ────────────────────────────────────────────────────────

class TestParseInstruments:
    def setup_method(self):
        self.instruments = _parse_instruments(FIXTURE)

    def test_dbmf_present(self):
        assert "DBMF" in self.instruments

    def test_mags_present(self):
        assert "MAGS" in self.instruments

    def test_vnq_is_candidate(self):
        assert "VNQ" in self.instruments
        assert self.instruments["VNQ"].is_candidate is True

    def test_dbmf_not_candidate(self):
        assert self.instruments["DBMF"].is_candidate is False

    def test_mags_tax_retirement(self):
        assert self.instruments["MAGS"].tax_placement == "RETIREMENT_ONLY"

    def test_dbmf_tax_all(self):
        assert self.instruments["DBMF"].tax_placement == "ALL"

    def test_mags_components(self):
        mags = self.instruments["MAGS"]
        roles = [c.role_id for c in mags.components]
        assert "secular_technology_growth" in roles
        assert "broad_market_equity_domestic" in roles

    def test_mags_stg_weight(self):
        mags = self.instruments["MAGS"]
        stg = next(c for c in mags.components if c.role_id == "secular_technology_growth")
        assert stg.weight == pytest.approx(0.85)

    def test_dbmf_single_component(self):
        dbmf = self.instruments["DBMF"]
        assert len(dbmf.components) == 1
        assert dbmf.components[0].role_id == "systematic_trend_following"
        assert dbmf.components[0].weight == pytest.approx(1.00)


# ── parse_calibration_state (round-trip) ─────────────────────────────────────

class TestParseCalibrationState:
    def setup_method(self):
        self.state = parse_calibration_state(FIXTURE)

    def test_version(self):
        assert self.state.version == "9.99"

    def test_thresholds_wired(self):
        assert self.state.thresholds.hy_stress_delta == 150

    def test_return_table_wired(self):
        assert "systematic_trend_following" in self.state.return_table

    def test_multipliers_wired(self):
        assert self.state.multipliers.ira["A"] == 2.0

    def test_floor_wired(self):
        assert self.state.floor_params.base_floor == pytest.approx(0.25)

    def test_instruments_wired(self):
        assert "MAGS" in self.state.instruments

    def test_cascade_wired(self):
        assert self.state.cascade.bankruptcy_watch_quarterly == 220
