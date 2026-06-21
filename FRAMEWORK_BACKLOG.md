# Framework Backlog — Engineering Gaps, TODOs & Open Items

<!--
  Purpose: single canonical tracker for ENGINEERING/ARCHITECTURE backlog items —
  code, test coverage, module structure, documentation. This is NOT a duplicate
  of the financial calibration backlog.

  SCOPE BOUNDARY (read this before adding anything):
    - Engineering items (code, tests, architecture, docs)              → THIS FILE, prefix ENG-N
    - Calibration/methodology items (return table revisions, GAP-N
      labels already in use throughout Calibration_State.md)          → Calibration_State.md §6
                                                                          is authoritative; this file
                                                                          only INDEXES them (see Part 2)
    - Portfolio/advisory open items (allocation discrepancies, pending
      trades, client decisions)                                       → Session_Log.md §8
                                                                          open_decisions/open_triggers
                                                                          is authoritative; NOT tracked
                                                                          here at all

  This file is NOT loaded as Project Knowledge during advisory sessions and is
  NOT part of 00_INDEX.md's FILE_MAP. It exists for coding/engineering sessions.
  See README.md for the engineering onboarding doc this file is paired with.

  Schema: each item uses an ITEM manifest block (same convention as the
  MODULE MANIFEST header used in M01-M19.md), so the format is already
  familiar within this repo. Fields: Status, Severity, Category, Opened,
  Closed (if applicable), Area, Related.

  Status values:   OPEN | IN_PROGRESS | BLOCKED | DEFERRED | CLOSED
  Severity values: CRITICAL | HIGH | MEDIUM | LOW
  Maintenance: update this file in the same commit as the work that opens,
  progresses, or closes an item. Do not let it drift into its own stale
  backlog — that would be ironic given ENG-5/ENG-6 below.
-->

**Last updated:** 2026-06-20 (ENG-27/28/29/32 closed — yfinance thread-safety bug, floor_account_weights_json double-encoding crash, thesis.py XAR phrasing gap, range_position.py flat-vs-unavailable note bug; ENG-30/31 opened — DBMF 3M-return condition, AIPO capex dependency; all found/fixed live the same session)

Closed items: full descriptions and resolutions live in `FRAMEWORK_BACKLOG_ARCHIVE.md`, indexed by the same ENG-N numbers. The Index table below still lists every item (open and closed) for a complete status overview; only OPEN items get full bodies in Part 1 below it -- closed items get a one-line stub pointing to the archive.

## Index

| ID | Status | Severity | Category | Title |
|---|---|---|---|---|
| ENG-1 | CLOSED | CRITICAL | data-integrity | §8 write-back format incompatible with parser |
| ENG-2 | CLOSED | HIGH | architecture | Module necessity review (M01–M19) |
| ENG-3 | CLOSED | HIGH | architecture | Pattern A / Pattern B duplication & convergence decision |
| ENG-4 | CLOSED | MEDIUM | architecture | Stage 5 (Pattern A) incomplete plumbing |
| ENG-5 | CLOSED | HIGH | hygiene | Compaction cadence mismatch (Calibration_State §3, Session_Log §8) |
| ENG-6 | CLOSED | MEDIUM | hygiene | §6 First-Audit Checklist accumulates stale content |
| ENG-7 | CLOSED | MEDIUM | hygiene | §11 stores computed EV math redundantly |
| ENG-8 | CLOSED | LOW | hygiene | Orphaned exited-instrument entries not pruned |
| ENG-9 | CLOSED | LOW | hygiene | §13 preamble mixes methodology with live data |
| ENG-10 | CLOSED | HIGH | testing | No test coverage for advisor_run_computation / advisor_apply_scoring |
| ENG-11 | CLOSED | HIGH | testing | No Pattern-B end-to-end pipeline test |
| ENG-12 | OPEN | MEDIUM | testing | Tests assert against live, not snapshotted, framework files |
| ENG-13 | CLOSED | MEDIUM | functional-gap | M19 trailing-window conditions have no tracking infrastructure |
| ENG-14 | OPEN | LOW | documentation | GAP-11 label has no description anywhere |
| ENG-15 | OPEN | LOW | process | No CI — test suite is run manually |
| ENG-16 | CLOSED | HIGH | architecture | M07/M08/M09/M10/M13/M15 portfolio-math Python implemented but never called by mcp_server.py |
| ENG-17 | CLOSED | LOW | documentation | BriefingRegistry described as built ("Phase 2 complete") but doesn't exist in Python anywhere |
| ENG-18 | CLOSED | LOW | hygiene | M17 CascadeChainRegistry embeds live dated figures in module file; CHAIN_5/6 not scored |
| ENG-19 | CLOSED | MEDIUM | functional-gap | 8 of 17 RoleID roles have no M09/M10 scenario-directive coverage anywhere |
| ENG-20 | CLOSED | MEDIUM | functional-gap | M14 energy_180d extended-conflict caveat not implemented in regime.py |
| ENG-21 | CLOSED | LOW | hygiene | M12's documented GitHub read-fallback vs file_protocol.py's actual Drive fallback |
| ENG-22 | OPEN | LOW | testing | Test suite needs reorganizing into unit/e2e/integration — currently flat test_stageN folders |
| ENG-23 | CLOSED | MEDIUM | architecture | M05_SessionInit.md retired outright (ENG-2 follow-on decision #2) |
| ENG-24 | CLOSED | MEDIUM | architecture | M13.RecalibrationSequence() has no Python implementation — still 100% manual |
| ENG-25 | CLOSED | LOW | architecture | instruments.json write not wired — Project_Instructions_MCP.md claimed MCP server writes it; it doesn't |
| ENG-26 | OPEN | LOW | functional-gap | MAGS's "consecutive sessions" §13 condition needs cross-session SIGNAL history — different problem from ENG-13's price-series trends |
| ENG-27 | CLOSED | CRITICAL | data-integrity | yfinance concurrent fetches under ThreadPoolExecutor returned cross-contaminated *_TREND data |
| ENG-28 | CLOSED | HIGH | data-integrity | floor_account_weights_json double-JSON-encoding crashed CurrentHoldingsFloorCheck/PassiveMandateAbsentWarning |
| ENG-29 | CLOSED | LOW | hygiene | thesis.py XAR Call-2 routing missed an alternate §13 phrasing for the same de-escalation judgment |
| ENG-30 | OPEN | MEDIUM | functional-gap | DBMF's "3M return < -3% while B+C>=55%" §13 failure condition has no FetchSpec/evaluator |
| ENG-31 | OPEN | LOW | functional-gap | AIPO's hyperscaler capex guidance §13 sustaining condition has no data source |
| ENG-32 | CLOSED | LOW | hygiene | range_position.py conflated "trend data flat" with "trend data unavailable" in GAP-16 advisory note text |
| ENG-33 | OPEN | HIGH | infrastructure | advisor_evaluate_allocation MCP tool call hangs ~4min in live use; underlying Python verified fast/correct, suspect MCP transport layer |

---

## Part 1 — Engineering Items

### ENG-12 — Tests assert against live, not snapshotted, framework files
<!-- ITEM
  Status:    OPEN
  Severity:  MEDIUM
  Category:  testing
  Opened:    2026-06-17
  Area:      python/tests/test_stage2/test_integration.py
  Related:   ENG-1
-->

**Description:** `test_integration.py` reads the live, production
Calibration_State.md / Session_Log.md and asserts hardcoded values
("File has 8 full entries", "June 10 session: A=5/B=41..."). Fixing
ENG-1 legitimately changed the live file's state and broke two of these
tests — not because the parser regressed, but because the tests were
pinned to a moment in time.

**Suggested next step:** split this file's concerns. Keep a small set of
"does the live file still structurally parse without throwing" smoke
tests against the real files (skippable when absent, as today). Move
value-specific assertions (sum-to-100, specific date ordering, specific
known-good values) onto static fixture files committed under
`tests/fixtures/`, so they test parser logic rather than a snapshot of
production data that's expected to keep changing.

### ENG-26 — MAGS "consecutive sessions" condition needs cross-session SIGNAL history
<!-- ITEM
  Status:    OPEN
  Severity:  LOW
  Category:  functional-gap
  Opened:    2026-06-20 (split out of ENG-13 on closing it)
  Area:      python/advisor/analysis/thesis.py
  Related:   ENG-13 (closed — see FRAMEWORK_BACKLOG_ARCHIVE.md)
-->

**Description:** ENG-13 closed the price-series half of §13's trailing-window
gap (DBMF/SGOL/SIVR/MLPX/URA/COPX — all evaluable in one yfinance/FRED call
per session, no persistence needed). One condition remains genuinely
unsolved: MAGS's failure signal "equity_scenario_divergence shifts to
MODERATE for >= 2 consecutive sessions." That's a condition over a
COMPUTED SIGNAL's value across sessions, not a raw price series — yfinance/
FRED can't serve "what was M14's divergence level last session," because
nothing persists it. `analysis/thesis.py`'s `_eval_trend()` explicitly
flags this case (`"ENG-26"` in the quality_flag text) rather than lumping
it in with the now-solved price-trend conditions.

**Suggested next step:** a small per-session signal-history file (mirrors
the existing local-only `instruments.json` write pattern — JSON, outside
the git repo, never committed) recording M14's `equity_scenario_divergence`
level each session would let `thesis.py` check "was it MODERATE last
session too." Low priority — MAGS already carries a HOLD-only override for
unrelated EV reasons, so this one failure signal not firing doesn't change
current execution; it just means a real exit trigger is currently inert.

### ENG-14 — GAP-11 label has no description anywhere
<!-- ITEM
  Status:    OPEN
  Severity:  LOW
  Category:  documentation
  Opened:    2026-06-17
  Area:      Session_Log.md
  Related:   GAP-11
-->

**Description:** "GAP-11 (M07 EV floor)" appears twice in Session_Log.md
with no further elaboration anywhere in the framework. Even the existing
GAP-N tracking has at least one item that's a label without content.

**Suggested next step:** next session that touches M07 or EV-floor logic,
recover or reconstruct what this was meant to refer to and either close
it or write an actual description.

### ENG-15 — No CI — test suite is run manually
<!-- ITEM
  Status:    OPEN
  Severity:  LOW
  Category:  process
  Opened:    2026-06-17
  Area:      (repo-wide)
  Related:   —
-->

**Description:** No `.github/workflows` or other CI config exists. The
523-test suite (as of ENG-1's fix) is run locally, on demand, relying on
developer discipline to run it before pushing.

**Suggested next step:** for a single-maintainer personal project this may
be an acceptable conscious tradeoff rather than an oversight — recorded
here so it's a known, chosen state rather than an invisible gap. If the
codebase grows, a simple local pre-push git hook running `pytest -q`
would close most of the risk without needing real CI infrastructure.

### ENG-22 — Test suite needs reorganizing into unit/e2e/integration
<!-- ITEM
  Status:    OPEN
  Severity:  LOW
  Category:  testing
  Opened:    2026-06-17
  Area:      python/tests/
  Related:   ENG-16
-->

**Description:** The test suite is currently organized as flat
`test_stage1` through `test_stage5` folders (named for the Python
migration stage that introduced them) plus `test_mcp` and
`test_framework`. Per the framework owner: this should eventually become
a structure organized by test *kind* — unit, e2e, integration — rather
than by historical migration stage. `tests/e2e/` was created when
closing ENG-16 as the first instance of the new convention (genuinely
end-to-end: exercises an MCP tool composing multiple underlying functions
together, not a single function in isolation) — the existing
`test_stage1`–`test_stage5`/`test_mcp` folders were deliberately NOT
moved as part of that fix; this is a separate, larger task.

**Suggested next step:** decide the target taxonomy (likely: `unit/`
for single-function tests close to today's `test_stage1`-`test_stage4`
content, `e2e/` for MCP-tool-level composition tests like the new
allocation test and `test_mcp/test_write_back_format.py`, `integration/`
for anything touching the live framework files like
`test_stage2/test_integration.py` — see ENG-12, which is closely related).
Migrate incrementally rather than in one large rename — each move risks
breaking relative imports/fixtures (e.g. `test_stage3/conftest.py` and
`test_stage4/conftest.py` are both consumed by name-scoped pytest
fixture discovery, not explicit imports) and should get its own
verification pass (`pytest -q` clean) before moving on to the next
folder.

---

## Closed Items (archived)

### ENG-1 — §8 write-back format incompatible with parser
**CLOSED** 2026-06-17 (CRITICAL, data-integrity). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.


### ENG-2 — Module necessity review (M01–M19)
**CLOSED** 2026-06-20 (HIGH, architecture). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.


### ENG-3 — Pattern A / Pattern B duplication & convergence decision
**CLOSED** 2026-06-18 (HIGH, architecture). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.


### ENG-4 — Stage 5 (Pattern A) incomplete plumbing
**CLOSED** 2026-06-18 (MEDIUM, architecture). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.


### ENG-5 — Compaction cadence mismatch (Calibration_State §3, Session_Log §8)
**CLOSED** 2026-06-19 (HIGH, hygiene). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.


### ENG-6 — §6 First-Audit Checklist accumulates stale content
**CLOSED** 2026-06-19 (MEDIUM, hygiene). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.


### ENG-7 — §11 stores computed EV math redundantly
**CLOSED** 2026-06-19 (MEDIUM, hygiene). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.


### ENG-8 — Orphaned exited-instrument entries not pruned
**CLOSED** 2026-06-19 (LOW, hygiene). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.


### ENG-9 — §13 preamble mixes methodology with live data
**CLOSED** 2026-06-19 (LOW, hygiene). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.


### ENG-10 — No test coverage for advisor_run_computation / advisor_apply_scoring
**CLOSED** 2026-06-18 (HIGH, testing). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.


### ENG-11 — No Pattern-B end-to-end pipeline test
**CLOSED** 2026-06-18 (HIGH, testing). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.


### ENG-13 — M19 trailing-window conditions have no tracking infrastructure
**CLOSED** 2026-06-20 (MEDIUM, functional-gap). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.


### ENG-16 — M07/M08/M09/M10/M13/M15 portfolio-math Python implemented but never called by mcp_server.py
**CLOSED** 2026-06-17 (HIGH, architecture). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.


### ENG-17 — BriefingRegistry described as built ("Phase 2 complete") but doesn't exist in Python anywhere
**CLOSED** 2026-06-20 (LOW, documentation). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.


### ENG-18 — M17 CascadeChainRegistry embeds live dated figures in module file; CHAIN_5/6 not scored
**CLOSED** 2026-06-20 (LOW, hygiene). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.


### ENG-19 — 8 of 17 RoleID roles have no M09/M10 scenario-directive coverage anywhere
**CLOSED** 2026-06-20 (MEDIUM, functional-gap). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.


### ENG-20 — M14 energy_180d extended-conflict caveat not implemented in regime.py
**CLOSED** 2026-06-20 (MEDIUM, functional-gap). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.


### ENG-21 — M12's documented GitHub read-fallback vs file_protocol.py's actual Drive fallback
**CLOSED** 2026-06-20 (LOW, hygiene). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.


### ENG-23 — M05_SessionInit.md retired outright (ENG-2 follow-on decision #2)
**CLOSED** 2026-06-17 (MEDIUM, architecture). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.


### ENG-24 — M13.RecalibrationSequence() has no Python implementation — still 100% manual
**CLOSED** 2026-06-18 (MEDIUM, architecture). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.


### ENG-25 — instruments.json write not wired — Project_Instructions_MCP.md claimed MCP server writes it
**CLOSED** 2026-06-20 (LOW, architecture). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.


### ENG-27 — yfinance concurrent fetches return cross-contaminated *_TREND data
**CLOSED** 2026-06-20 (CRITICAL, data-integrity). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.


### ENG-28 — floor_account_weights_json double-JSON-encoding crashes floor checks
**CLOSED** 2026-06-20 (HIGH, data-integrity). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.


### ENG-29 — thesis.py XAR Call-2 routing misses an alternate §13 phrasing
**CLOSED** 2026-06-20 (LOW, hygiene). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.


### ENG-32 — range_position.py conflated "flat" with "unavailable" trend data
**CLOSED** 2026-06-20 (LOW, hygiene). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.


### ENG-30 — DBMF's own-performance §13 failure condition has no FetchSpec/evaluator
<!-- ITEM
  Status:    OPEN
  Severity:  MEDIUM
  Category:  functional-gap
  Opened:    2026-06-20
  Area:      python/advisor/analysis/thesis.py, data/fetchers/, data/m18_registry.py
  Related:   ENG-13 (closed — solved the *_TREND price-series half; this is a different, ticker-own-performance condition)
-->

**Description:** DBMF's §13 failure_signals includes "DBMF_3M_return < -3% while B+C >= 55% (instrument underperforming own scenario)". This isn't a generic market-index trend (which ENG-13 already solved for BRENT/GOLD/DXY/SP500/COPPER/URANIUM/COPX) — it needs DBMF's *own* 3-month return, which has no FetchSpec anywhere (holdings_30d_returns in mcp_server.py only covers a ~35-trading-day window, not 3 months) and no regex pattern in `_eval_simple_numeric`. Surfaced 2026-06-20 as a "no evaluator recognizes condition" quality_flag, separate from that session's ENG-27 data-corruption bug (which affected DBMF's mean-reversion sustaining/failure check, not this one).

**Suggested next step:** add a `DBMF_3M_RETURN` FetchSpec (same pattern as `fetch_nasdaq_trailing`/`fetch_broad_equity_trailing` — one `yf.download` call, ~64 trading days, `(last/first - 1) * 100`), then a regex in `_eval_simple_numeric` matching `DBMF_3M_return\s*(>=|<=|>|<)\s*(-?\d+(?:\.\d+)?)%` combined with the existing `B+C` combined-probability check (`_BC_PROB_RE`) via an AND. Confirm with Evgeny whether -3%/55% are the intended live thresholds or illustrative placeholders before wiring.


### ENG-31 — AIPO's hyperscaler capex §13 sustaining condition has no data source
<!-- ITEM
  Status:    OPEN
  Severity:  LOW
  Category:  functional-gap
  Opened:    2026-06-20
  Area:      python/advisor/analysis/thesis.py, orchestrator/scoring_questions.py
  Related:   —
-->

**Description:** AIPO's §13 sustaining condition "AI infrastructure capital expenditure cycle intact (hyperscaler capex guidance positive)" and failure condition "Hyperscaler capex guidance revised down >=2 consecutive quarters" have no Call-2 judgment question wired (unlike SGOL/SIVR/URA/XAR/COPX, which each route through a `M19_{TICKER}_*` scoring question) and no quantitative data source either. Surfaced 2026-06-20 as `missing_dependencies` on an otherwise-ACTIVE evaluation — not a crash, just permanently unevaluable as-is.

**Suggested next step:** decide whether this should be a new Call-2 judgment question (qualitative, Claude answers from hyperscaler earnings-call research each session — cheapest fix, same pattern as `M19_URA_NUCLEAR_POLICY`) or a quantitative consecutive-quarters tracker (harder — needs cross-session persistence like ENG-26, since "2 consecutive quarters" of guidance can't be derived from one session's data alone). Given AIPO's UNCLASSIFIED-weight EV flag is already a standing item, low priority relative to that.


### ENG-33 — advisor_evaluate_allocation hangs ~4min in live MCP use
<!-- ITEM
  Status:    OPEN
  Severity:  HIGH
  Category:  infrastructure
  Opened:    2026-06-20
  Area:      python/advisor/mcp_server.py (_tool_evaluate_allocation), MCP transport
  Related:   ENG-16 (introduced this tool), ENG-28 (similar-looking symptom, different
             root cause — that one WAS in the Python code and is fixed)
-->

**Description:** `advisor_evaluate_allocation` timed out at the ~4-minute MCP
call ceiling four times this session (twice before the ENG-27/28/29 fixes,
twice after, across two separate server restarts) with no partial output and
no server-side error surfaced to the caller. `advisor_run_computation` and
`advisor_apply_scoring` both worked normally throughout, including on the
same restarted process immediately before/after the hung calls — so this
isn't "the server is generally wedged."

**Investigated and ruled out:** read every function in the call path end to
end — `_tool_evaluate_allocation` → `classify_instrument`,
`scenario_weighted_allocation` → `ideal_allocation` (loops over 6 scenarios
and a small ranked ticker list), `dominant_directive`, `dual_role_conflict`,
`get_directive` (plain dict lookups). Nothing unbounded, no recursion, no
network I/O, no locks. `tests/e2e/test_evaluate_allocation.py` exercises
this exact function in-process with realistic fixtures and passes in
under a second as part of the regular 645-test suite run (same session,
same machine). That combination — correct and fast in-process, hangs at
the MCP layer specifically for this tool — points at the MCP
transport/serialization layer (FastMCP's handling of the `Dict[str, Any]`
`account_profile` / `Dict[str, float]` `current_weights` params, or a
stdio buffering issue specific to this tool's call shape) rather than
application code. Not confirmed; no access to server-side stderr/logs from
the calling side to pin it further.

**Suggested next step:** capture the MCP server process's stderr during a
live hang (Claude Desktop's MCP logs, or run the server manually in a
visible terminal and trigger the same call shape via an MCP CLI client to
get a stack trace at the point it stalls). Until root-caused, the existing
fallback holds: don't retry more than once live; fall back to the manually
documented EV figures in `Calibration_State.md` §11 for the session and
flag that a live recompute wasn't available.


---

## Part 2 — Calibration & Methodology Gaps (GAP-N index)

These use the GAP-N label already established in Calibration_State.md /
Session_Log.md prose. **This section is an index only — Calibration_State.md
§6 and Session_Log.md §8 remain the authoritative source.** Update there
first; update this index to match, not the other way around.

| ID | Status | Title | Authoritative source |
|---|---|---|---|
| GAP-3 | OPEN | Regime maturity / crowding-risk signal (DBMF AUM inflows) — deferred; would require M13.idealAllocation() sizing-logic changes | Calibration_State.md v1.38 log entry (M19 hand-off) |
| GAP-6 | CLOSED v1.27 | §11.2 secular_technology_growth B table corrected to [-2,+4]★ ADOPTED | Calibration_State.md §3 |
| GAP-7 | OPEN | §8 compaction annotation | Session_Log.md (June 14 entries); see ENG-5 — same root cause, engineering side |
| GAP-8 | CLOSED v1.32 | §2.1 C-trigger clock T1-confirmed (max 3 consecutive closes ≥$110) | Calibration_State.md §3 |
| GAP-11 | OPEN | M07 EV floor — see ENG-14, no description recovered yet | Session_Log.md |
| GAP-15 | CLOSED v1.32 | B_WATCH_LEVEL_3 graduated protocol added to §2.3 | Calibration_State.md §3 |
| GAP-16 | CLOSED v1.42 | Within-scenario sub-condition advisory (range-position) for wide-range roles — IHP (real yield/DXY) implemented; STF/RAC/IHC sub-conditions not yet identified, separate follow-on | Calibration_State.md §6 |

---

## How to add an item

1. Pick the next free `ENG-N` (engineering) — do not reuse `GAP-N`, that
   namespace belongs to the calibration backlog and is assigned in
   Calibration_State.md, not here.
2. Copy the `<!-- ITEM ... -->` manifest block format from any entry above.
3. Add a row to the Index table at the top.
4. If it touches a tool signature, the session sequence, or anything
   Project_Instructions_MCP.md describes, cross-check that file per the
   rule in README.md → "Keeping Project_Instructions_MCP.md in sync."
