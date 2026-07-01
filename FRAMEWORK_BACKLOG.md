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

**Last updated:** 2026-06-30, same-day follow-on coding session (ENG-45 CLOSED — credit.py ccc_widening ratio mode gated behind a new `ccc_ratio_min_bps` calibration threshold (75 bps); full writeup in FRAMEWORK_BACKLOG_ARCHIVE.md). Prior, same day (Q2 audit — opened ENG-42/43/44/45: FRED series-history not exposed via any MCP tool; FRED 3y OAS truncation blocks §1 delta verification + §2 5y hit-rate audit; calculator_mcp not wired and still a stub; credit.py §1.3 CCC divergence ratio-mode OR false-positive found live (CCC+29/HY+8 bps → 3.62x). Full bodies in Part 1.) Prior: 2026-06-25 (ENG-33: live-tested the flattened-parameter fix after a clean Claude Desktop restart and a freshly-rebuilt cache — advisor_evaluate_allocation still hung the full ~4 minutes, and the transport log confirms zero occurrences of the tool name anywhere, not just no tools/call entry. This rules out the $ref/$defs hypothesis as cleanly as the prior two attempts ruled out their own. Three independent hypotheses now falsified across two sessions; root cause confirmed client-side, outside this codebase's reach. Flattened account_profile kept regardless as a genuine cleanup; in-process bypass remains the standing workaround — see full ENG-33 entry below). Prior, same day: ENG-40 opened and closed same session — fetch_all() had no per-spec timeout and the shared yfinance lock had no bound on acquisition, so one stuck/illiquid symbol (UX=F) could hang advisor_run_computation() for 25+ minutes and then permanently block every later yfinance fetch for the rest of the MCP server process's life; fixed with a per-future timeout in fetch_registry.py and a bounded _yf_lock_guard() in yfinance_fetcher.py; full writeup in FRAMEWORK_BACKLOG_ARCHIVE.md. Prior: 2026-06-21 (ENG-39 opened and closed same session — GAP-16's IHP range-position advisory was using THREEFYTP10 (term premium) mislabeled as "real yield"; replaced with a computed REAL_YIELD_10Y_TREND series; full writeup in FRAMEWORK_BACKLOG_ARCHIVE.md). Prior: 2026-06-20/21 (ENG-38 closed — write_back's git-push hang root-caused and fixed via GIT_TERMINAL_PROMPT=0 + timeouts + non-fatal push failure; ENG-27/28/29/32/36 also closed earlier this session — yfinance thread-safety bug, floor_account_weights_json double-encoding crash, thesis.py XAR phrasing gap, GAP-16 flat-vs-unavailable note bug, dominant_directive() DirectiveCode.upper() crash; ENG-30/31/34/35/37 opened — DBMF/AIPO/XAR data-source gaps, run_computation latency, recalibration_sequence anchor heuristic; all found/fixed live across one extended session)

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
| ENG-33 | OPEN | MEDIUM | infrastructure | advisor_evaluate_allocation's MCP transport-layer hang -- request confirmed (via mcp-server-financial-advisor.log) to never reach the server at all. Three hypotheses tested and ruled out across two sessions (execution-layer timeout; Dict[str,Any]/pydantic shape; nested-vs-flat schema). Flattened account_profile kept anyway (cleaner, matches other tools) but did not fix it. Root cause remains in Claude Desktop's client, outside this codebase. In-process bypass remains the standing workaround. |
| ENG-34 | OPEN | LOW | functional-gap | XAR's "Defense budget trajectory positive" §13 sustaining condition has no Call-2 question or data source |
| ENG-35 | OPEN | MEDIUM | performance | advisor_run_computation took 244.8s in-process post-ENG-27 (vs sub-4min MCP ceiling) -- likely yfinance lock serialization cost, possibly compounded by session's repeated test-call rate limiting; needs isolated measurement |
| ENG-36 | CLOSED | MEDIUM | bug | dominant_directive() crashed on MAGS/MLPX/COPX -- _directive_direction()/_most_conservative() called .upper() on DirectiveCode enum members, which only worked for the str fallback default |
| ENG-37 | OPEN | MEDIUM | functional-gap | recalibration_sequence()'s "anchor = above-floor proxy" heuristic produces a degenerate no-op when every holding is above its own floor (the normal case) -- gap_closed_by_reallocation reports true without any actual reallocation |
| ENG-38 | CLOSED | HIGH | infrastructure | advisor_write_back's `git push` had no timeout and no guard against an interactive credential prompt, causing it to hang at the MCP client's ~4min ceiling even though the operation completed and committed server-side regardless |
| ENG-39 | CLOSED | MEDIUM | bug | GAP-16's IHP range-position advisory used THREEFYTP10 (10Y term premium) mislabeled as "real yield" -- replaced with a computed REAL_YIELD_10Y_TREND (DGS10-T10YIE) series |
| ENG-40 | CLOSED | HIGH | bug | fetch_all() and the shared yfinance lock had no timeout -- one stuck/illiquid symbol could hang advisor_run_computation() and every later yfinance fetch indefinitely |
| ENG-41 | OPEN | LOW | functional-gap | test_pipeline_probabilities_all_at_or_above_floor fails against live data + StubAIClient (one scenario lands at 2.81%, below the test's asserted 3% floor, after the 25pp session cap compresses the others) -- confirmed pre-existing/independent of ENG-40 via git-stash A/B |
| ENG-42 | OPEN | MEDIUM | infrastructure | No MCP tool (either server) exposes FRED/series-history fetch — calibration audits hand-roll scratch scripts against fred_fetcher's underscore-private helpers |
| ENG-43 | BLOCKED | MEDIUM | data-integrity | FRED truncated ICE BofA OAS series to a rolling 3y window (~Apr 2026) — §1 delta verification and §2 5y hit-rate audit no longer sourceable from FRED |
| ENG-44 | OPEN | MEDIUM | infrastructure | calculator_mcp (dev folder) not wired to the project and is a stub — no sanctioned/auditable calc path for ad-hoc audit math (median/percentile/EV) |
| ENG-45 | CLOSED | LOW | bug | credit.py §1.3 CCC divergence OR-combines ratio+absolute modes — ratio mode false-positives in compressed regimes (fired 3.62x on CCC+29/HY+8 bps, 2026-06-30) |

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
  Severity:  MEDIUM
  Category:  infrastructure
  Opened:    2026-06-20
  Area:      python/advisor/mcp_server.py (_with_timeout, _tool_evaluate_allocation), MCP transport
  Related:   ENG-16 (introduced this tool), ENG-38 (split off -- write_back's
             matching symptom WAS root-caused; this one, evaluate_allocation's,
             was not)
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
same machine). Initially suspected the same root cause as `advisor_write_back`
(ENG-38 — found later in this same session: an unguarded `git push` that can
hang on a credential prompt) — but `evaluate_allocation` does zero git/file/
network I/O of any kind, ruling that out as a shared cause. The two tools'
identical ~4-minute symptom turned out to be coincidental, not the same bug.

**Mitigation applied (not a root-cause fix):** added `_with_timeout()` in
`mcp_server.py` — runs the wrapped tool function in a worker thread with a
hard wall-clock timeout (30s for `evaluate_allocation`, 90s for
`write_back`), well above every observed real runtime (sub-second) for
either. If the timeout ever fires, the caller gets an immediate, clear
`TIMEOUT` status instead of a silent multi-minute hang — and critically,
an explicit instruction to check `git log` before retrying anything with
side effects, directly addressing the duplicate-write risk that prompted
elevating this to CRITICAL earlier in the session. Severity downgraded
back to MEDIUM now that the worst consequence (silent duplicate writes) is
structurally prevented regardless of whether the underlying transport-layer
cause is ever found.

**Live-tested post-mitigation, negative result (2026-06-21):** with the
`_with_timeout()` wrapper live, `evaluate_allocation` still hung the full
~4 minutes with zero response — meaning the wrapper's own 30s timeout
never fired. This proves the hang happens before the wrapped Python
function is ever invoked (the timeout wraps the function call itself;
if it never fires, the function was never entered) — i.e. somewhere in
FastMCP's request handling or the MCP transport, not in this codebase's
execution. Useful negative result: rules out anything inside
`_tool_evaluate_allocation`'s call path with certainty.

**New experiment (2026-06-21, untested as of this writing):** the same
session also showed `advisor_write_back` — which has zero `Dict`-typed
parameters — working instantly through the live MCP transport (tested
via `dry_run=true`). `advisor_apply_scoring`'s `Dict[str, int]` (a
concrete value type) also works fine. `evaluate_allocation`'s
`account_profile: Dict[str, Any]` — an unconstrained-value dict — is
now the most plausible remaining differentiator. Replaced it with a
precise `AccountProfileInput` pydantic model (concrete fields matching
exactly what `_parse_account_profile()` already expects), removing the
bare `Any` entirely. `current_weights`/`proposed_allocations` were left
as `Dict[str, float]` (concrete value type, matching the working
`apply_scoring` precedent) — only the `Any`-valued dict was changed.
Full suite passes (645/0 regressions) and the module compiles cleanly;
not yet verified live — requires an MCP server restart to test.

**Second negative result (2026-06-21, after server restart):** the
`AccountProfileInput` pydantic model change was tested live and
`evaluate_allocation` still hung the full ~4 minutes with zero response,
identical to every prior attempt. This rules out the `Dict[str, Any]`
hypothesis as cleanly as the timeout-wrapper test ruled out anything inside
the function body. `AccountProfileInput` was left in place regardless (a
genuine type-safety improvement on its own merits -- concrete fields beat a
loose dict either way) but it is not the fix.

**Where this leaves things:** two reasonable, falsifiable hypotheses have
now been tested and ruled out in a single session (execution-layer hang;
input-schema hang). Both `_with_timeout()` (mcp_server.py) and the ENG-38
git-push hardening (file_protocol.py) remain in place and are independently
verified to do what they claim -- this account is just for
`evaluate_allocation` specifically. Continuing to guess at the transport
layer from this side, at ~4 minutes of dead time per failed attempt, has a
worse cost/information ratio than just using the established, reliable
workaround.

**Decision: stop experimenting on ENG-33 for now.** Permanent workaround
until someone can capture the MCP server's stderr during a live hang
(requires access this session never had -- Claude Desktop's own MCP logs,
or running the server manually in a visible terminal): use the in-process
bypass demonstrated repeatedly this session (`python -c` or a small script
importing `advisor.mcp_server` directly and calling `_tool_evaluate_allocation`
with cached `cal`/`scenario_probs` populated by hand, or via `parse_calibration_state()`
directly) -- proven fast, correct, and reliable every single time it was
tried, as opposed to four-for-four live MCP failures.

**Breakthrough (2026-06-24): the access this was waiting on existed all
along.** `C:\Users\evgen\AppData\Roaming\Claude\logs\mcp-server-financial-advisor.log`
is Claude Desktop's own MCP transport log -- exactly the "server-side
stderr" the prior decision said wasn't available. Checked it during a
fifth live hang on `advisor_evaluate_allocation` this session. Finding:
**the request never arrives.** The log shows a normal `tools/call` entry
for `advisor_run_computation` at 02:22:39, its response at 02:23:17, a
normal `tools/call` + instant response for `advisor_apply_scoring` at
02:38:10 -- then nothing. No `tools/call` entry for `evaluate_allocation`
at all, ever, for the call that hung the full 4 minutes immediately after.
This is a stronger result than the 2026-06-21 `_with_timeout()` test: it
doesn't just imply the function body was never reached, it shows the
*server process itself never received the request over stdio*. The hang
is in Claude Desktop's MCP client, upstream of this server entirely.

**Revised hypothesis:** of this tool's four parameters, `account_profile`
was the only one typed as a nested object (`AccountProfileInput`, a
pydantic `BaseModel`) rather than a flat scalar or a flat `Dict[str, V]`.
FastMCP renders a `BaseModel` parameter as a `$ref` into a `$defs` block in
the tool's advertised JSON schema -- structurally different from every
other parameter on every other tool here, including `current_weights`'s
`Dict[str, float]` (a flat `additionalProperties` object, no `$ref`). If
Claude Desktop validates or otherwise processes call arguments against the
advertised schema client-side before transmitting, and that handling
doesn't fully resolve `$ref`/`$defs`, a hang client-side before send would
produce exactly this symptom -- and would equally explain why the original
`Dict[str, Any]` shape (also schema-irregular: an unconstrained-value
object) hung too, and why converting it to `AccountProfileInput` made no
observable difference: both versions kept account_profile as the one
non-flat parameter.

**Third negative result (2026-06-25, after Claude Desktop restart, clean
server, flattened params live-tested):** the flattened-parameter fix was
deployed and tested with a freshly-restarted server and a freshly-rebuilt
cache (`advisor_run_computation` + `advisor_apply_scoring` both re-run
and logged normally immediately before). `advisor_evaluate_allocation`
hung the full ~4 minutes again. Checked the transport log directly:
`Select-String -Pattern 'evaluate_allocation'` against the full log
returns zero matches — not even in the `tools/list` advertisement, let
alone a `tools/call` entry. This rules out the $ref/$defs hypothesis as
cleanly as the previous two: removing the nested model and using all flat
scalar parameters made no observable difference. Whatever blocks this
specific call happens before the request leaves Claude Desktop's client
entirely, for reasons unrelated to this tool's JSON schema shape.

**Where this actually leaves things, revised:** three independent,
falsifiable hypotheses have now been tested and ruled out across two
sessions (execution-layer hang; `Dict[str, Any]`/pydantic-model input
shape; nested-vs-flat schema shape). The one new, hard fact established
this session — request never arrives, confirmed via Claude Desktop's own
transport log, not inferred — narrows the search space (it's client-side,
not in this codebase) but doesn't by itself point at a specific remaining
cause. Candidates not yet tested: total parameter count (9, the most of
any tool here) or total schema size/docstring length (this tool's
docstring is the longest of the five); call timing/sequencing relative to
the immediately-preceding tool call on the same server connection; something
specific to Claude Desktop's own client build unrelated to anything a
server-side schema change could fix. None of these are testable by editing
this repo. Decision unchanged from before, reaffirmed with stronger
evidence: keep `_with_timeout()` as the safety net, keep the in-process
bypass as the standing workaround, and stop spending live-test cycles on
schema-shape experiments specifically — the next productive step would
need Anthropic-side visibility into the Desktop client, not another
guess from this side.


### ENG-34 — XAR's "Defense budget trajectory positive" §13 condition has no Call-2 question or data source
<!-- ITEM
  Status:    OPEN
  Severity:  LOW
  Category:  functional-gap
  Opened:    2026-06-20
  Area:      python/advisor/analysis/thesis.py, orchestrator/scoring_questions.py
  Related:   ENG-29 (same ticker, different condition)
-->

**Description:** Found while re-scoring `M19_XAR_CONFLICT_GATE` correctly
(see Session_Log for the geopolitical correction this session) — once XAR's
de-escalation gate is answered 0 (conflict still active, correctly), the
evaluation proceeds past the failure check into XAR's sustaining conditions,
surfacing a previously-hidden gap: "Defense budget trajectory positive (not
subject to emergency cuts)" has no Call-2 question wired and no quantitative
source. Same pattern as ENG-31 (AIPO capex) — masked while XAR was
incorrectly resolving to FAILED, since failed tickers don't reach the
sustaining-conditions loop.

**Suggested next step:** same options as ENG-31 — new Call-2 judgment
question (cheapest) vs. a quantitative defense-budget data source. Low
priority on its own.


### ENG-35 — advisor_run_computation latency: 244.8s measured in-process post-ENG-27
<!-- ITEM
  Status:    OPEN
  Severity:  MEDIUM
  Category:  performance
  Opened:    2026-06-20
  Area:      python/advisor/data/fetchers/yfinance_fetcher.py, data/fetch_registry.py
  Related:   ENG-27 (introduced the lock that may be the cause)
-->

**Description:** Running `_tool_run_computation()` in-process (bypassing
MCP, to test ENG-33/36) timed in at 244.8 seconds — uncomfortably close to
the ~4-minute MCP call ceiling that's been intermittently hit this session
for a different tool (ENG-33). ENG-27's fix serialized all yfinance calls
behind one lock to fix data corruption; that necessarily trades fetch
parallelism for correctness, and ~15-20 yfinance call sites now run
sequentially instead of 8-wide. However, this single measurement also
came after four prior `advisor_run_computation` calls in the same session
(each hitting ~12+ yfinance symbols), and the run's own stderr showed
repeated "HTTP Error 401: Invalid Crumb" — a known Yahoo Finance
rate-limit/session-invalidation symptom — so some or most of the 244.8s
may be retry/backoff delay from session-level rate limiting rather than
the lock itself. Not isolated; don't attribute confidently to ENG-27 yet.

**Suggested next step:** measure `fetch_all()` wall-clock on a cold session
(no recent prior calls) both with and without `_YF_LOCK` to isolate the
two effects. If the lock itself is the dominant cost, consider batching
yfinance calls via `yf.download()`'s native multi-ticker support (one
request for all _SYMBOL_MAP point-quotes, instead of looping under a lock)
rather than removing the lock and reintroducing ENG-27's race.


### ENG-36 — dominant_directive() crashed on MAGS/MLPX/COPX (DirectiveCode.upper())
**CLOSED** 2026-06-20 (MEDIUM, bug). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.


### ENG-37 — recalibration_sequence() anchor heuristic produces a degenerate no-op for small floor breaches
<!-- ITEM
  Status:    OPEN
  Severity:  MEDIUM
  Category:  functional-gap
  Opened:    2026-06-20
  Area:      python/advisor/portfolio/allocation.py (recalibration_sequence)
  Related:   ENG-24 (introduced this function)
-->

**Description:** When `high_conviction_tickers` isn't supplied, the
function defaults anchors to "every ticker with weight > its own floor."
In the normal case — a healthy portfolio where every position is, by
definition, held above its (small, ~2-8%) floor — this proxy captures the
ENTIRE portfolio as "anchors," leaving a near-zero residual_weight with
nothing left to actually reallocate. The function then reports
`gap_closed_by_reallocation: true` with `revised_allocations` identical to
the input — technically not wrong (rounding tolerance is met because
residual_weight ~0), but not an actual remediation either. Found live this
session on a real floor breach (Relative IRA/Roth, scenario F, -0.45%/
-0.13%): the function returned a no-op "fixed" result instead of either
(a) a genuine reallocation suggestion or (b) an honest "no low-conviction
positions available to trim" message.

**Manual analysis this session** (see Session_Log) found the actual
F-scenario drag comes overwhelmingly from DBMF (-0.78pp/-1.02pp contribution)
and SGOL (-0.57pp/-0.45pp), both of which the framework's OWN
`scenario_weighted_allocation()` output ranks as currently UNDER their
ideal weight (i.e. the systematic framework wants MORE of both, not less,
once all six scenarios are probability-weighted) — meaning the mechanically
"correct" fix here may genuinely be to hold as-is, but the function should
say that explicitly rather than silently no-op.

**Suggested next step:** when the above-floor proxy selects the entire
portfolio as anchors (residual_weight below some small threshold, e.g.
1pp), have the function report `gap_closed_by_reallocation: false` with an
explicit message ("no low-conviction positions available to trim; consider
this floor exposure an accepted cost of the optimal allocation, or supply
high_conviction_tickers manually to force a smaller anchor set") instead of
a misleadingly-affirmative true.


### ENG-38 — advisor_write_back's `git push` could hang on an interactive credential prompt
**CLOSED** 2026-06-20 (HIGH, infrastructure). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.


### ENG-39 — GAP-16's IHP range-position advisory mislabeled THREEFYTP10 (term premium) as "real yield"
**CLOSED** 2026-06-21 (MEDIUM, bug). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.


### ENG-40 — fetch_all() and the shared yfinance lock had no timeout bound
**CLOSED** 2026-06-24 (HIGH, bug). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.


### ENG-41 — test_pipeline_probabilities_all_at_or_above_floor fails against live data
<!-- ITEM
  Status:    OPEN
  Severity:  LOW
  Category:  functional-gap
  Opened:    2026-06-24
  Area:      tests/test_stage5/test_session.py, advisor/portfolio/probability.py (M03 derivation/cap)
  Related:   ENG-40 (discovered while verifying ENG-40 didn't regress this test)
-->

**Found:** while verifying ENG-40 against the full suite, this
`@pytest.mark.integration` test failed: `AssertionError: Scenario
C=2.8103% below 3% floor`. Confirmed independent of ENG-40 via `git stash` —
the exact same failure, with the exact same probability vector
(A=31/B=22/C=3/D=3/E=3/F=39 pre-cap, derived 44/3/—/—/—/44-ish post-cap),
reproduces on the pre-ENG-40 working tree against today's live market data
and `Calibration_State.md`/`Session_Log.md` state, using `StubAIClient`'s
fixed canned scoring answers. Mechanism: the 25pp session cap compresses A
and F's derived shift, and the residual math for C lands at 2.8103% —
just under the test's hardcoded `val >= 3.0` floor assertion for every
scenario.

**Open question, not yet investigated:** is this a genuine M03 gap (should
`DeriveScenarioProbabilities()` enforce a hard floor post-cap so no
scenario can mathematically fall below some minimum, the way `compute_floor()`
already does for portfolio weights?), or is the test itself too strict
(should a non-dominant scenario be allowed to print under 3% in a regime
where the cap is actively suppressing a large derived shift elsewhere)?
Needs a deliberate decision, not a quick patch — flagged here rather than
fixed inline since it touches probability-derivation semantics, which is
calibration-adjacent territory (M03), not pure plumbing.


### ENG-42 — No MCP tool exposes FRED (or any) series-history fetch
<!-- ITEM
  Status:    OPEN
  Severity:  MEDIUM
  Priority:  P1
  Category:  infrastructure
  Opened:    2026-06-30
  Area:      python/advisor/mcp_server.py, python/advisor/data/fetchers/fred_fetcher.py, market_data_mcp
  Related:   ENG-43; M18; M11; Calibration_State.md §6 Batch A
-->

**Description:** The financial-advisor MCP tools fetch only the *current*
session snapshot of DataReadings. Historical series — trailing medians,
percentile distributions, N-day change/velocity, everything a calibration
audit needs — are reachable only through underscore-private helpers in
`fred_fetcher.py` (`_fetch_latest`, `_fetch_history`,
`_fetch_history_with_dates`) that no MCP tool and no CLI command surface.
The Q2 2026 credit audit (Calibration_State.md §6 Batch A) had to hand-roll
a scratch script importing those privates directly to get HY/IG/CCC
history. That is not repeatable, not tested, not discoverable, and violates
the "don't hand-roll what the framework should own" posture. Two MCP
servers are wired (financial-advisor and market_data_mcp); neither exposes
series-history fetch. This is the generalized, permanent form of the
one-off problem — the FRED REST client already works fine (it powered the
audit), it just isn't reachable through a tool.

**Suggested next step / scope:**
- Decide ownership. `market_data_mcp` is the more natural home — it already
  owns `market_get_history/quotes/macro/ytd` for symbols, and FRED macro
  series are a data domain, not an advisory computation. Recommended: add
  `fred_get_history(series_id, days | weeks, as_of?)` there, backed by
  `fred_fetcher`'s existing REST client, returning dated observations.
- Promote the internal helper(s) to a documented public function: drop the
  underscore, pin a stable return contract, add a unit test.
- Per README §9, update `Project_Instructions_MCP.md` and README §12
  cookbook once the tool exists.

**Acceptance:** a calibration session pulls N days of any FRED series via a
tool call, no scratch script, covered by a round-trip test.


### ENG-43 — Credit-spread history truncated to 3y by FRED
<!-- ITEM
  Status:    BLOCKED
  Severity:  MEDIUM
  Priority:  P2
  Category:  data-integrity
  Opened:    2026-06-30
  Area:      Calibration_State.md §1 (HY/IG/CCC thresholds) + §2 hit-rate audit; python/advisor/data/fetchers/fred_fetcher.py
  Related:   ENG-42; Calibration_State.md §6 Batch A
  Blocked-on: full-cycle credit history source (see below)
-->

**Description:** As of ~April 2026 FRED restricts the ICE BofA OAS series
(BAMLH0A0HYM2 HY, BAMLC0A0CM IG, BAMLH0A3HYC CCC) to a rolling 3-year
window. Confirmed 2026-06-30: `_fetch_history_with_dates(..., days=1200)`
returns only ~785 obs back to 2023-07-03. Consequences for §1/§2:

1. §1 stress/recession deltas (HY +150/+300, IG +60) are sized for a
   full-cycle, crisis-inclusive distribution. Verified against the
   *available* 3y they land at the 97.7th–100th percentile — above the
   intended 75–90th band — but that is an artifact of a benign, compressed
   3y window missing the 2008/2020 tails, NOT evidence the deltas are
   miscalibrated. They can no longer be verified or recalibrated from FRED.
2. §2 items 6–7 (5-year hit-rate audit) need ≥5y history — impossible from
   current FRED.

**Interim posture (adopted this audit):** retain the current deltas
unchanged. Forcing them down to the 3y-implied band would fire stress /
recession triggers on routine noise. This is a safe hold, not a fix.

**Suggested next step / scope:** source full-cycle credit history from one
of — (a) FRED ALFRED archived vintages (may retain pre-truncation series);
(b) an ICE/Bloomberg commercial feed; (c) a **local rolling-history store**
that accumulates the daily OAS readings going forward so the window
self-heals over ~2 years (cheapest; start now). Then re-run §1 delta
verification and the §2 hit-rate audit. Fetch path is ENG-42.

**Acceptance:** §1 deltas verifiable against a distribution containing ≥1
full credit cycle; §2 hit-rate audit runnable.


### ENG-44 — calculator_mcp not wired to the project + is a stub
<!-- ITEM
  Status:    OPEN
  Severity:  MEDIUM
  Priority:  P1
  Category:  infrastructure
  Opened:    2026-06-30
  Area:      G:\My Drive\dev\calculator_mcp.py; Claude Desktop MCP config; Project_Instructions_MCP.md
  Related:   README §5 design principle 6 ("all arithmetic is auditable"); framework NEVER-hand-compute-EV rule
-->

**Description:** A financial-calculator MCP (`G:\My Drive\dev\
calculator_mcp.py`, FastMCP "Calculator") exists but is (a) not registered
as a connector for this project — absent from the session's available tools
— and (b) currently a stub: only `add`/`subtract`/`multiply`/`divide` and a
single `calculate_compound_interest`. The framework's "all arithmetic is
auditable" principle and the NEVER-hand-compute-EV rule call for a
sanctioned, auditable calculation path; instead ad-hoc audit math (medians,
percentiles, percentile-rank, N-day velocity — exactly the Q2 credit
audit's needs) gets hand-rolled in scratch Python.

**Suggested next step / scope:**
- Wire `calculator_mcp` into Claude Desktop's MCP config (stdio, same
  launcher pattern as `run_mcp_server.py`; heed the space-in-path gotcha,
  README §6 — point directly at the `.py`, no `cmd.exe` wrapper).
- Add the financial/statistical methods the framework reuses: `median`,
  `percentile(values, p)`, `percentile_rank(values, x)`, `mean`/`stdev`,
  basis-point delta helpers, and **scenario_weighted_ev(prob_vector,
  per_scenario_returns)** — the single calculation the framework most wants
  sanctioned. Single-purpose tools, exact-result contracts, matching the
  existing docstring style.
- Define the boundary vs the advisor pipeline: this MCP is for ad-hoc
  session/audit math, NOT a second home for pipeline math that already
  lives in `scenario_math.py`/`allocation.py` — two sources of truth would
  violate design principles 1 & 6. Document the boundary in
  `Project_Instructions_MCP.md`.

**Acceptance:** the calculator is connectable in an advisory/audit session;
the next credit audit computes median/percentile/rank via tool calls, not a
scratch script.


### ENG-45 — credit.py §1.3 CCC divergence OR-combines ratio + absolute modes (ratio false-positives)
**CLOSED** 2026-06-30 (LOW, bug). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.


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
| GAP-16 | CLOSED v1.42; real-yield driver corrected v1.44 (ENG-39) | Within-scenario sub-condition advisory (range-position) for wide-range roles — IHP (real yield/DXY) implemented; STF/RAC/IHC sub-conditions not yet identified, separate follow-on | Calibration_State.md §3 |

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
