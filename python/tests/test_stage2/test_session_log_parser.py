"""
tests/test_stage2/test_session_log_parser.py

Unit tests for advisor/config/session_log.py using inline fixture text.
"""
import pytest
from advisor.config.session_log import (
    _parse_credit_readings,
    _parse_probs,
    _extract_list,
    _parse_scenario_states,
    parse_session_log,
)
from advisor.types import ScenarioProbabilities

# ── Fixture ────────────────────────────────────────────────────────────────────

FIXTURE = """\
# Session Log

## Section 7 - Session Observations Log (Credit Readings)

| Date | HY OAS (bps) | IG OAS (bps) | CCC OAS (bps) | Source | T1 Flag |
| --- | --- | --- | --- | --- | --- |
| 2026-05-07 (full) | 277 (carry) | 80 (carry) | 921 (carry) | Carry. FRED still metadata only. | stale |
| 2026-05-11 (full) | **281** | **79** | **920** | FRED T1 — data gap resolved. | **T1** |

---

## Section 8 - Session State Log

// COMPACTED: 2026-04-30 | A=7%/B=42%/C=42%/D=3%/E=3%/F=3% | Superseded

---

date: 2026-05-25 (full M05 session — v1.19)
scenario_probabilities: { A: 7%, B: 36%, C: 41%, D: 5%, E: 4%, F: 7% }
  // UPDATED from prior carry
primary_driver: US-Iran War Day 86. BZ=F ~$107.60.
session_type: full M05

open_triggers:
- Brent C-trigger clock: Day 0.
- CPI mid-June: BINARY EVENT.

open_decisions:
1. PAVE: exit review deferred.
2. MAGS: override in force.

next_session_flags:
- LOAD: confirm Iran deal status
- FIRST: BZ=F current close

---

date: 2026-06-10 (full M05 — B formal trigger; v1.33)
scenario_probabilities: { A: 5%, B: 41%, C: 38%, D: 5%, E: 4%, F: 7% }
  // B formal trigger FIRES: May CPI 4.2% YoY
primary_driver: May CPI 4.2% YoY T1 BLS. B trigger fires.
session_type: full M05

calibration_changes_this_session:
- Calibration_State.md v1.33:
- §2.3: CPI B trigger status updated to FIRED

open_triggers:
- FOMC June 17-18: rate decision pending.
- MOVE 77.03: approaching ELEVATED threshold.

open_decisions:
1. MAGS: HOLD-only override. EV -0.94%.
2. URA ADD: IRA 3%, Roth 3%.

next_session_flags:
- LOAD: Calibration State loaded, last update June 10
- FIRST: Iran deal status

---
"""

# ── Credit readings ────────────────────────────────────────────────────────────

class TestCreditReadings:
    def setup_method(self):
        self.readings = _parse_credit_readings(FIXTURE)

    def test_count(self):
        assert len(self.readings) == 2

    def test_first_date(self):
        assert "2026-05-07" in self.readings[0].date

    def test_second_hy(self):
        assert self.readings[1].hy_oas == 281

    def test_stale_flag(self):
        assert "stale" in self.readings[0].t1_flag

    def test_t1_flag(self):
        assert "T1" in self.readings[1].t1_flag


# ── _parse_probs ───────────────────────────────────────────────────────────────

class TestParseProbs:
    def test_valid(self):
        block = "scenario_probabilities: { A: 7%, B: 36%, C: 41%, D: 5%, E: 4%, F: 7% }"
        p = _parse_probs(block)
        assert p is not None
        assert p.A == 7.0
        assert p.B == 36.0
        assert p.F == 7.0

    def test_sum_100(self):
        block = "scenario_probabilities: { A: 5%, B: 41%, C: 38%, D: 5%, E: 4%, F: 7% }"
        p = _parse_probs(block)
        assert p is not None
        assert abs(p.A + p.B + p.C + p.D + p.E + p.F - 100.0) < 0.01

    def test_missing_returns_none(self):
        assert _parse_probs("no probabilities here") is None


# ── _extract_list ──────────────────────────────────────────────────────────────

class TestExtractList:
    BLOCK = """\
date: 2026-05-25
scenario_probabilities: { A: 7%, B: 36%, C: 41%, D: 5%, E: 4%, F: 7% }
primary_driver: test driver
session_type: full M05

open_triggers:
- Trigger one text
- Trigger two text

open_decisions:
1. Decision alpha
2. Decision beta

next_session_flags:
- Flag one
- Flag two
- Flag three
"""

    def test_triggers_count(self):
        items = _extract_list(self.BLOCK, "open_triggers")
        assert len(items) == 2

    def test_triggers_content(self):
        items = _extract_list(self.BLOCK, "open_triggers")
        assert "Trigger one text" in items[0]

    def test_decisions_count(self):
        items = _extract_list(self.BLOCK, "open_decisions")
        assert len(items) == 2

    def test_decisions_content(self):
        items = _extract_list(self.BLOCK, "open_decisions")
        assert "Decision alpha" in items[0]

    def test_flags_count(self):
        items = _extract_list(self.BLOCK, "next_session_flags")
        assert len(items) == 3

    def test_missing_key(self):
        assert _extract_list(self.BLOCK, "nonexistent_key") == []


# ── _parse_scenario_states ────────────────────────────────────────────────────

class TestParseScenarioStates:
    def setup_method(self):
        self.entries = _parse_scenario_states(FIXTURE)

    def test_count(self):
        assert len(self.entries) == 2

    def test_first_date(self):
        assert self.entries[0].date.startswith("2026-05-25")

    def test_second_date(self):
        assert self.entries[1].date.startswith("2026-06-10")

    def test_first_probs(self):
        p = self.entries[0].probabilities
        assert p.A == 7.0 and p.B == 36.0 and p.C == 41.0

    def test_second_probs(self):
        p = self.entries[1].probabilities
        assert p.A == 5.0 and p.B == 41.0 and p.C == 38.0

    def test_calibration_changes(self):
        changes = self.entries[1].calibration_changes
        assert len(changes) >= 1
        assert any("v1.33" in c for c in changes)

    def test_compacted_line_skipped(self):
        # The COMPACTED comment block has no date: YYYY-MM-DD — must be skipped
        assert all("COMPACTED" not in e.date for e in self.entries)


# ── parse_session_log (round-trip) ────────────────────────────────────────────

class TestParseSessionLog:
    def setup_method(self):
        self.log = parse_session_log(FIXTURE)

    def test_credit_readings_count(self):
        assert len(self.log.credit_readings) == 2

    def test_scenario_states_count(self):
        assert len(self.log.scenario_states) == 2

    def test_latest_probs(self):
        p = self.log.latest_probs
        assert p is not None
        assert p.B == 41.0

    def test_prior_probs(self):
        p = self.log.prior_probs
        assert p is not None
        assert p.B == 36.0

    def test_latest_open_triggers(self):
        triggers = self.log.latest_open_triggers
        assert len(triggers) >= 1
        assert any("FOMC" in t for t in triggers)

    def test_latest_open_decisions(self):
        decisions = self.log.latest_open_decisions
        assert len(decisions) >= 1
        assert any("MAGS" in d for d in decisions)

    def test_latest_next_flags(self):
        flags = self.log.latest_next_flags
        assert len(flags) >= 1
