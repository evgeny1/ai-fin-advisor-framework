"""
tests/test_stage2/test_integration.py

Integration tests: load actual Calibration_State.md and Session_Log.md from disk
and assert known-good values verified against the live framework files.

These tests require the local framework repo to be present at the path
defined in FRAMEWORK_DIR. They are skipped automatically if the path is missing
(e.g., in CI without the repo mounted).
"""
import os
import pytest

BASE = os.path.expanduser(
    "~/Library/CloudStorage/"
    "GoogleDrive-evgeny.shatalov@gmail.com/My Drive/"
    "dev/AI Financial Advisor Framework"
)
CAL_PATH = os.path.join(BASE, "Calibration_State.md")
LOG_PATH = os.path.join(BASE, "Session_Log.md")

SKIP_REASON = "Framework files not present — skipping integration tests"
skip_if_missing = pytest.mark.skipif(
    not os.path.exists(CAL_PATH) or not os.path.exists(LOG_PATH),
    reason=SKIP_REASON,
)

from advisor.config import parse_calibration_state, parse_session_log


@pytest.fixture(scope="module")
def cal_state():
    with open(CAL_PATH, encoding="utf-8") as f:
        return parse_calibration_state(f.read())


@pytest.fixture(scope="module")
def session_log():
    with open(LOG_PATH, encoding="utf-8") as f:
        return parse_session_log(f.read())


# ── Calibration_State.md integration ──────────────────────────────────────────

@skip_if_missing
class TestCalibrationStateIntegration:

    def test_version_not_unknown(self, cal_state):
        assert cal_state.version != "unknown"
        assert cal_state.last_updated != "unknown"

    # §1 — credit thresholds
    def test_hy_stress_delta(self, cal_state):
        assert cal_state.thresholds.hy_stress_delta == 150

    def test_hy_recession_delta(self, cal_state):
        assert cal_state.thresholds.hy_recession_delta == 300

    def test_hy_velocity(self, cal_state):
        assert cal_state.thresholds.hy_velocity_delta == 100

    def test_hy_sustain(self, cal_state):
        assert cal_state.thresholds.hy_sustain_days == 10

    def test_ig_transmission(self, cal_state):
        assert cal_state.thresholds.ig_transmission_delta == 60

    def test_ccc_ratio(self, cal_state):
        assert cal_state.thresholds.ccc_ratio_multiplier == pytest.approx(3.0)

    def test_ccc_floor(self, cal_state):
        assert cal_state.thresholds.ccc_absolute_floor_bps == 200

    # §4.1 — return table
    def test_stf_b_conservative(self, cal_state):
        r = cal_state.return_table["systematic_trend_following"]["B"]
        assert r.conservative == pytest.approx(15.0)

    def test_stf_b_confidence(self, cal_state):
        r = cal_state.return_table["systematic_trend_following"]["B"]
        assert r.confidence == "HIGH"

    def test_stf_b_upside(self, cal_state):
        r = cal_state.return_table["systematic_trend_following"]["B"]
        assert r.upside == pytest.approx(30.0)

    def test_all_roles_have_all_scenarios(self, cal_state):
        for role, scenarios in cal_state.return_table.items():
            for s in ("A", "B", "C", "D", "E", "F"):
                assert s in scenarios, f"Missing scenario {s} for role {role}"

    # §4.2 / §4.3 — multipliers
    def test_ira_a(self, cal_state):
        assert cal_state.multipliers.ira["A"] == pytest.approx(2.0)

    def test_ira_e(self, cal_state):
        assert cal_state.multipliers.ira["E"] == pytest.approx(1.2)

    def test_roth_a(self, cal_state):
        assert cal_state.multipliers.roth["A"] == pytest.approx(3.1)

    def test_roth_d(self, cal_state):
        assert cal_state.multipliers.roth["D"] == pytest.approx(1.6)

    # §4.4 — floor params
    def test_base_floor(self, cal_state):
        assert cal_state.floor_params.base_floor == pytest.approx(0.25)

    def test_concentration_cap(self, cal_state):
        assert cal_state.floor_params.concentration_cap == pytest.approx(0.40)

    # §9 — regime
    def test_move_elevated(self, cal_state):
        assert cal_state.regime.move_elevated == pytest.approx(80.0)

    def test_underweight_gap(self, cal_state):
        assert cal_state.regime.underweight_gap_trigger_pp == pytest.approx(5.0)

    # §11 — instruments
    def test_mags_present(self, cal_state):
        assert "MAGS" in cal_state.instruments

    def test_mags_tax(self, cal_state):
        assert cal_state.instruments["MAGS"].tax_placement == "RETIREMENT_ONLY"

    def test_mags_stg_component(self, cal_state):
        roles = [c.role_id for c in cal_state.instruments["MAGS"].components]
        assert "secular_technology_growth" in roles

    def test_dbmf_tax_all(self, cal_state):
        assert cal_state.instruments["DBMF"].tax_placement == "ALL"

    def test_dbmf_stf_weight(self, cal_state):
        dbmf = cal_state.instruments["DBMF"]
        stf = next(c for c in dbmf.components if c.role_id == "systematic_trend_following")
        assert stf.weight == pytest.approx(1.00)

    def test_active_instruments_not_candidate(self, cal_state):
        for ticker in ("DBMF", "MAGS", "MLPX", "XLP", "SGOV", "AIPO"):
            if ticker in cal_state.instruments:
                assert cal_state.instruments[ticker].is_candidate is False, ticker

    # §12 — cascade
    def test_bankruptcy_watch(self, cal_state):
        assert cal_state.cascade.bankruptcy_watch_quarterly == 220

    def test_bankruptcy_fires(self, cal_state):
        assert cal_state.cascade.bankruptcy_fires_quarterly == 300

    def test_e_term_premium_warning(self, cal_state):
        assert cal_state.cascade.e_term_premium_warning_bps == pytest.approx(100.0)

    def test_e_term_premium_alert(self, cal_state):
        assert cal_state.cascade.e_term_premium_alert_bps == pytest.approx(150.0)

    def test_e_30y_warning(self, cal_state):
        assert cal_state.cascade.e_30y_warning_pct == pytest.approx(5.50)

    def test_natgas_price(self, cal_state):
        assert cal_state.cascade.natgas_alert_price == pytest.approx(6.00)


# ── Session_Log.md integration ────────────────────────────────────────────────

@skip_if_missing
class TestSessionLogIntegration:

    def test_credit_readings_count(self, session_log):
        # File has ≥10 entries as of June 10, 2026
        assert len(session_log.credit_readings) >= 10

    def test_scenario_states_count(self, session_log):
        # File has 10 full entries (May 25 through June 14 — two June 14 entries
        # recovered 2026-06-17 from a malformed write-back format; see git log)
        assert len(session_log.scenario_states) == 10

    def test_latest_probs_sum_100(self, session_log):
        p = session_log.latest_probs
        assert p is not None
        total = p.A + p.B + p.C + p.D + p.E + p.F
        assert abs(total - 100.0) < 0.01

    def test_latest_probs_values(self, session_log):
        # June 14 second session (US-Iran MOU announced): A=14.3/B=42.9/C=14.3/D=7.1/E=14.3/F=7.1
        p = session_log.latest_probs
        assert p.A == pytest.approx(14.3)
        assert p.B == pytest.approx(42.9)
        assert p.C == pytest.approx(14.3)
        assert p.D == pytest.approx(7.1)
        assert p.E == pytest.approx(14.3)
        assert p.F == pytest.approx(7.1)

    def test_all_states_sum_100(self, session_log):
        for entry in session_log.scenario_states:
            p = entry.probabilities
            total = p.A + p.B + p.C + p.D + p.E + p.F
            assert abs(total - 100.0) < 0.01, f"Sum != 100 for {entry.date}"

    def test_chronological_order(self, session_log):
        # Compare YYYY-MM-DD prefix only; same-day entries (e.g., two June 2 sessions)
        # are ordered by file position, not alphabetically by session-type annotation.
        dates = [e.date[:10] for e in session_log.scenario_states]
        assert dates == sorted(dates), "Entries not in chronological order"

    def test_latest_has_open_triggers(self, session_log):
        triggers = session_log.latest_open_triggers
        assert len(triggers) >= 3

    def test_latest_has_open_decisions(self, session_log):
        decisions = session_log.latest_open_decisions
        assert len(decisions) >= 5

    def test_latest_has_flags(self, session_log):
        assert len(session_log.latest_next_flags) >= 5

    def test_prior_probs_not_same_as_latest(self, session_log):
        # June 14 first and second entries differ (C: 25.1→14.3 on MOU announcement)
        prior   = session_log.prior_probs
        latest  = session_log.latest_probs
        assert prior is not None
        assert prior.A != latest.A or prior.B != latest.B
