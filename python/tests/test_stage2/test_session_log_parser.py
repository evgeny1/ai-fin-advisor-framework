"""
tests/test_stage2/test_session_log_parser.py

Unit tests for advisor/config/session_log.py using inline fixture text.

ENG-52 (2026-07-06): rewritten for the YAML-based §8 format. Internal
helpers this used to import directly (_parse_probs, _extract_list) no
longer exist -- the parser now delegates to PyYAML rather than field-by-
field regex. Tests exercise the same behavior through the public
_parse_scenario_states()/parse_session_log() surface, plus new coverage
for entry_id/status (the fields ENG-52 added to fix the same-day-entry
disambiguation gap).
"""
import pytest
from advisor.config.session_log import (
    _parse_credit_readings,
    _probs_from_doc,
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
entry_id: 2026-05-25T10:00
date: 2026-05-25
session_type: full M05
status: superseded
scenario_probabilities: {A: 7, B: 36, C: 41, D: 5, E: 4, F: 7}
primary_driver: 'US-Iran War Day 86. BZ=F ~$107.60.'
open_triggers:
- 'Brent C-trigger clock: Day 0.'
- 'CPI mid-June: BINARY EVENT.'
open_decisions:
- 'PAVE: exit review deferred.'
- 'MAGS: override in force.'
next_session_flags:
- 'LOAD: confirm Iran deal status'
- 'FIRST: BZ=F current close'

---
entry_id: 2026-06-10T11:52
date: 2026-06-10
session_type: full M05
status: current
scenario_probabilities: {A: 5, B: 41, C: 38, D: 5, E: 4, F: 7}
primary_driver: 'May CPI 4.2% YoY T1 BLS. B trigger fires.'
calibration_changes_this_session:
- 'Calibration_State.md v1.33'
- '§2.3: CPI B trigger status updated to FIRED'
open_triggers:
- 'FOMC June 17-18: rate decision pending.'
- 'MOVE 77.03: approaching ELEVATED threshold.'
open_decisions:
- 'MAGS: HOLD-only override. EV -0.94%.'
- 'URA ADD: IRA 3%, Roth 3%.'
next_session_flags:
- 'LOAD: Calibration State loaded, last update June 10'
- 'FIRST: Iran deal status'
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


# ── _probs_from_doc ────────────────────────────────────────────────────────────

class TestProbsFromDoc:
    def test_valid(self):
        doc = {"scenario_probabilities": {"A": 7, "B": 36, "C": 41, "D": 5, "E": 4, "F": 7}}
        p = _probs_from_doc(doc)
        assert p is not None
        assert p.A == 7.0
        assert p.B == 36.0
        assert p.F == 7.0

    def test_sum_100(self):
        doc = {"scenario_probabilities": {"A": 5, "B": 41, "C": 38, "D": 5, "E": 4, "F": 7}}
        p = _probs_from_doc(doc)
        assert p is not None
        assert abs(p.A + p.B + p.C + p.D + p.E + p.F - 100.0) < 0.01

    def test_missing_returns_none(self):
        assert _probs_from_doc({}) is None

    def test_not_a_dict_returns_none(self):
        assert _probs_from_doc({"scenario_probabilities": "not a mapping"}) is None

    def test_incomplete_mapping_returns_none(self):
        # Missing F -> KeyError inside, must fail soft to None, not raise.
        doc = {"scenario_probabilities": {"A": 7, "B": 36, "C": 41, "D": 5, "E": 4}}
        assert _probs_from_doc(doc) is None


# ── _parse_scenario_states ─────────────────────────────────────────────────────

class TestParseScenarioStates:
    def setup_method(self):
        self.entries = _parse_scenario_states(FIXTURE)

    def test_count(self):
        assert len(self.entries) == 2

    def test_first_date(self):
        assert self.entries[0].date == "2026-05-25"

    def test_second_date(self):
        assert self.entries[1].date == "2026-06-10"

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
        # The COMPACTED comment block has no 'date:' key at all — must be
        # excluded by construction (it's outside the YAML region entirely,
        # not filtered out post-hoc), never mis-parsed into a bogus entry.
        assert all("COMPACTED" not in e.date for e in self.entries)

    # ENG-52: entry_id / status coverage — the fields added to disambiguate
    # same-day entries without reading the full primary_driver prose.
    def test_entry_id_present(self):
        assert self.entries[0].entry_id == "2026-05-25T10:00"
        assert self.entries[1].entry_id == "2026-06-10T11:52"

    def test_status_values(self):
        assert self.entries[0].status == "superseded"
        assert self.entries[1].status == "current"


# ── parse_session_log (round-trip) ─────────────────────────────────────────────

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


# ── Malformed input handling (ENG-52: fail soft, don't crash session start) ────

class TestMalformedInput:
    def test_no_section_8_heading(self):
        assert _parse_scenario_states("# Session Log\n\nNo section 8 here.") == []

    def test_section_8_with_no_entries_yet(self):
        text = "## Section 8 - Session State Log\n\n// COMPACTED: nothing yet\n"
        assert _parse_scenario_states(text) == []

    def test_broken_yaml_fails_soft(self):
        text = (
            "## Section 8\n\n---\n"
            "date: 2026-07-06\n"
            "scenario_probabilities: { A: 1, B: this is not: valid: yaml [\n"
        )
        # Must not raise -- degrades to an empty list, same as "no entries".
        assert _parse_scenario_states(text) == []

    def test_one_malformed_entry_does_not_poison_others(self):
        """The regression this design specifically guards against: parsing
        must be per-entry independent. A malformed block must only drop
        itself, never take down every entry parsed after it."""
        text = (
            "## Section 8\n\n---\n"
            "date: 2026-07-05\n"
            "scenario_probabilities: { A: 1, B: broken: [ unclosed\n"
            "---\n"
            "entry_id: 2026-07-06T10:00\n"
            "date: 2026-07-06\n"
            "status: current\n"
            "scenario_probabilities: {A: 20, B: 20, C: 20, D: 20, E: 10, F: 10}\n"
            "primary_driver: well-formed entry after a broken one\n"
        )
        entries = _parse_scenario_states(text)
        assert len(entries) == 1
        assert entries[0].date == "2026-07-06"
