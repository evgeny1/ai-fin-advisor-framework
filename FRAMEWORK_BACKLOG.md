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

**Last updated:** 2026-06-20

## Index

| ID | Status | Severity | Category | Title |
|---|---|---|---|---|
| ENG-1 | CLOSED | CRITICAL | data-integrity | §8 write-back format incompatible with parser |
| ENG-2 | IN_PROGRESS | HIGH | architecture | Module necessity review (M01–M19) |
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
| ENG-13 | OPEN | MEDIUM | functional-gap | M19 trailing-window conditions have no tracking infrastructure |
| ENG-14 | OPEN | LOW | documentation | GAP-11 label has no description anywhere |
| ENG-15 | OPEN | LOW | process | No CI — test suite is run manually |
| ENG-16 | CLOSED | HIGH | architecture | M07/M08/M09/M10/M13/M15 portfolio-math Python implemented but never called by mcp_server.py |
| ENG-17 | OPEN | LOW | documentation | BriefingRegistry described as built ("Phase 2 complete") but doesn't exist in Python anywhere |
| ENG-18 | OPEN | LOW | hygiene | M17 CascadeChainRegistry embeds live dated figures in module file; CHAIN_5/6 not scored |
| ENG-19 | CLOSED | MEDIUM | functional-gap | 8 of 17 RoleID roles have no M09/M10 scenario-directive coverage anywhere |
| ENG-20 | CLOSED | MEDIUM | functional-gap | M14 energy_180d extended-conflict caveat not implemented in regime.py |
| ENG-21 | OPEN | LOW | hygiene | M12's documented GitHub read-fallback vs file_protocol.py's actual Drive fallback |
| ENG-22 | OPEN | LOW | testing | Test suite needs reorganizing into unit/e2e/integration — currently flat test_stageN folders |
| ENG-23 | CLOSED | MEDIUM | architecture | M05_SessionInit.md retired outright (ENG-2 follow-on decision #2) |
| ENG-24 | CLOSED | MEDIUM | architecture | M13.RecalibrationSequence() has no Python implementation — still 100% manual |
| ENG-25 | OPEN | LOW | architecture | instruments.json write not wired — Project_Instructions_MCP.md claimed MCP server writes it; it doesn't |

---

## Part 1 — Engineering Items

### ENG-1 — §8 write-back format incompatible with parser
<!-- ITEM
  Status:    CLOSED
  Severity:  CRITICAL
  Category:  data-integrity
  Opened:    2026-06-14 (root cause introduced) / discovered 2026-06-17
  Closed:    2026-06-17
  Area:      python/advisor/mcp_server.py, python/advisor/orchestrator/session.py,
             python/advisor/data/file_protocol.py, Session_Log.md
  Related:   ENG-10, ENG-11, ENG-12
-->

**Description:** `advisor_write_back()` generated §8 entries using a format
(`### §8 Entry — DATE` header, `**Probabilities:** A=N / B=N`, no `---`
separator) that does not match `config/session_log.py`'s parser, which
requires a `date:` line, a literal `scenario_probabilities: { A: N%, ... }`
line, and `---`-separated blocks. The identical bug existed independently
in `orchestrator/session.py._append_session_log_entry()` (Pattern A), which
also interpolated a `List[str]` directly into an f-string for
`next_session_flags`, producing a Python repr instead of a parseable list.

**Impact:** Two real §8 entries (2026-06-14) were silently invisible to
`SessionLogState.latest_probs` / `prior_probs`. The system was loading a
stale (June 10) probability vector with no error, missing the entire
US-Iran MOU-driven scenario shift. No exception was raised anywhere —
this was discovered only by manually running the parser against the live
file and inspecting the result by hand.

**Resolution:** Both malformed entries recovered into canonical schema
(commit `2ea8afe`); both write-back code paths fixed to emit the literal
canonical format, using `:g` number formatting so fractional probabilities
(e.g. 12.5%) round-trip exactly instead of rounding to integers that no
longer sum to 100 (commit `d7bb376`). `advisor_write_back()` gained a
required `session_type` parameter (no default). `Project_Instructions_MCP.md`
Step 9 updated to match the new signature.

**Standing lesson (see README.md → Testing):** any function that serializes
data into a format later re-parsed by this codebase must have a round-trip
test. This is now codified as a rule, not just a one-off fix.

### ENG-2 — Module necessity review (M01–M19)
<!-- ITEM
  Status:    IN_PROGRESS
  Severity:  HIGH
  Category:  architecture
  Opened:    2026-06-17
  Area:      M01_SourceIntegrity.md – M19_ThesisSustainingConditions.md (all 19), FW_Types.md
  Related:   ENG-3, ENG-16, ENG-17, ENG-18, ENG-19, ENG-20, ENG-21
-->

**Description:** The M01–M19 pseudo-code module files predate the Python/MCP
implementation. Per the framework owner (2026-06-17): "this is a python mcp
server, essentially, the pseudo-code modules are the artifacts of the old
version, at least some of them... I will be planning work to review the
necessity of having this many modules now that the mcp part of the
framework is implemented." This is the framework owner's own planned
review, recorded here as a flagged open question.

**Suggested approach (original framing, see Update below for what was
actually found):** for each module, classify as (a) AI-judgment-only —
keep as the authoritative source, Python has no equivalent; (b)
spec-for-Python — Python is the executable truth, the .md file is
documentation of intent and could likely shrink substantially; (c) fully
superseded — logic, thresholds, and registries have moved entirely into
`python/advisor/` and CALIBRATION_STATE, and the .md file may be
retireable or mergeable into 00_INDEX.md.

**Update (2026-06-17) — deep-verification pass completed:** Read all 19
module files in full plus FW_Types.md and cross-checked each against the
actual Python source AND against what `mcp_server.py` actually imports
and calls (not just whether a Python equivalent exists anywhere in the
repo — those are different questions; see ENG-16). Findings:

- **Wired into the live session today, and shrunk/retired this pass:**
  M02 (deleted legacy `PriceDataIntegrity` block), M03 (shrunk six
  `SCORE ScenarioA-F` blocks — confirmed verbatim-duplicated in
  `scoring_questions.py`), M05 (reduced to a step-cross-reference stub —
  superseded by `Project_Instructions_MCP.md`; also fixed a stale
  GitHub-push write-back instruction), M11 (shrunk
  `SignalConvergenceTest`/`THRESHOLD`/`ScenarioDTrigger` blocks — confirmed
  in `credit.py`), M12 (corrected three factual errors — see commit
  `26b861b`), M14 (deleted legacy fetch-list blocks; shrunk
  `ComputeDivergenceSignal`'s deterministic math — confirmed in
  `regime.py` — while keeping the `energy_180d` extended-conflict caveat
  in full, since that part is NOT implemented in Python; see ENG-20).
  FW_Types.md: added missing M19 to the `ModuleID` enum.
- **Confirmed AI-judgment-only, no Python equivalent, left untouched:**
  M01, M06, M16.
- **Confirmed mixed but NOT wired into `mcp_server.py` despite having a
  faithful, tested Python implementation — left fully untouched, see
  ENG-16 for the real issue here:** M07, M08, M09, M10, M13, M15.
- **M04 is AI-judgment-only, not Python-owned, despite README previously
  implying otherwise** — no `BriefingRegistry` class exists anywhere in
  the codebase; see ENG-17. Left untouched this pass (correcting the
  misleading framing is tracked separately, not urgent).
- **M17, M18, M19 reviewed, left untouched** — M18 is already the
  strongest "fully superseded, minimal" example in the framework; M19 is
  flagged as the best-designed module in the framework (clean AI-boundary
  routing, no spec/Python duplication, no legacy cruft) — worth using as
  the template for what M02/M07/M08/M09/M10/M11/M13/M17 should converge
  toward, NOT a retirement candidate. M17 has two open findings of its
  own (ENG-18).

All 7 edited files re-validated against `tools/validate_manifests.py`
(20/20 pass) and committed/pushed (`26b861b`), net change -361 lines.

**Why this item stays IN_PROGRESS rather than CLOSED:** the original ask
— "review the necessity of having this many modules" — has now actually
happened, with evidence, for all 19 files. Of the three follow-on
decisions flagged in the original pass: (1) the `mcp_server.py` wiring
for the unwired portfolio-math modules — see ENG-16, CLOSED; (2) whether
`M05_SessionInit.md` should be deleted outright — see ENG-23, CLOSED,
deleted 2026-06-17; (3) the smaller hygiene/functional-gap findings spun
out as ENG-17 through ENG-21 — still open.

**Update (2026-06-18) — M07/M08/M13/M15 shrink pass, second half of the
M07/M08/M09/M10/M13/M15 question left open above:** now that ENG-16 wired
their Python, re-read all four files against the actual wired functions
and shrunk every FUNCTION/GUARD/RULE block confirmed to have a faithful,
called Python equivalent to a short pointer (formula/spec retained,
literal pseudo-code removed) — M07 (`AutoDisqualify` →
`advisor_check_instrument_candidate()`), M08 (`DualRoleConflict` →
`dual_role_conflict()`), M13 (`ComputeTargetMultiplier`,
`RequiredRealReturn`, `ComputeFloor`, `idealAllocation`,
`minimumConvictionWeight` — fully retired, folded into `ComputeFloor`,
`FeasibilityCheck`, `PassiveMandateAbsentWarning`,
`CurrentHoldingsFloorCheck`), M15 (`ValidateClassifications`,
`classifyInstrument`, `blendedScenarioReturn`, `dominantDirective`).
Net: M13 541→~290 lines, M15 263→176 lines, M07/M08 shrunk by their one
superseded section each. Two real NEVER-rule violations were found and
fixed in the same pass, not just staleness: M13's `RecalibrationSequence`
had two direct `§4.1[M08.classifyRole(a)][s]` lookups (should route
through `M15.blendedScenarioReturn()`/`classifyInstrument()` per the
NEVER rules) and `RecommendationFlow` step 3 still said
`M08.classifyRole(asset)` instead of `M15.classifyInstrument(asset)` —
M15.md had already claimed this exact correction was made, but it
hadn't actually been applied in M13. All four fixed.
`M13.RecalibrationSequence()` itself was left fully untouched — confirmed
via grep it has no Python implementation anywhere, unlike every other
M13 function — opened as its own item, ENG-24, rather than folded into
this one. M09/M10 were read in full and confirmed NOT shrinkable: their
Python mirror (`directives.py`) captures only the bare DirectiveCode,
not the `rationale`/`urgency`/conditional nuance (e.g. Scenario A's
DXY-trajectory check before adding international equity) that these
files carry — that's the legitimate "why" half of the why/how split per
design principle 3, not redundant documentation. `validate_manifests.py`:
19/19 pass. Full pytest suite: 491 passed, 46 skipped (44 are
`test_stage2/test_integration.py`'s pre-existing live-file-presence
skips — see ENG-12; 2 are pre-existing FMP 403 plan-tier skips), 2
failed (live yfinance network/DNS resolution failure on the machine
this pass ran on — unrelated to any code change here).

**Update (2026-06-18) — M12 and M18 shrink passes:**
M12_DriveProtocol.md: confirmed not a deletion candidate (fetchAllocation(),
PATTERN_A FrameworkAmendment, CompactSessionLog are still 100% manual). Shrunk
the Python-wired functions to pointers: readFrameworkFile, fetchCalibrationState,
fetchSessionLog → advisor_run_computation(); constructPortfolioState →
_render_portfolio_state(); PATTERN_B → advisor_write_back(). Also corrected
SOURCE_MAP local path (was Mac-hardcoded; now notes ADVISOR_FRAMEWORK_PATH env
var). 375→278 lines. Bug found: instruments.json NOT written by Python write_back()
despite Project_Instructions_MCP.md claiming otherwise — opened ENG-25.
M18_MarketDataFetch.md: 1,034 lines. DATA_REGISTRY_ENTRIES (~620 lines of
REGISTER FetchSpec blocks) confirmed superseded by python/advisor/data/m18_registry.py
(377-line Python translation). Shrunk entire DATA_REGISTRY_ENTRIES section to a
pointer + brief series list. Kept all other content (HARD_GATE NoWebSearchForPriceData,
FMP_PLAN_TIER_MAP, AllocationPriceCrossCheck, PriceDataIntegrity, ALLOCATION_
SPREADSHEET_TABS, YFINANCE_MCP_SERVER_REFERENCE, NEVER list). Also fixed:
instruments.json LIFECYCLE note (pointed to ENG-25 gap); cleared the "pending M18
registration" doc-note for COPPER_SPOT/URANIUM_SPOT/CHINA_PMI_MANUFACTURING
(added to m18_registry.py during M19 work; M18.md pointer now covers them). Noted
that M18.md FMP sources reflect FMP MCP connector context (higher-tier account)
while Python m18_registry.py uses standalone key (lower tier, many endpoints 403).
1,034→546 lines. validate_manifests: 19/19 pass.

### ENG-16 — M07/M08/M09/M10/M13/M15 portfolio-math Python implemented but never called by mcp_server.py
<!-- ITEM
  Status:    CLOSED
  Severity:  HIGH
  Category:  architecture
  Opened:    2026-06-17
  Closed:    2026-06-17
  Area:      python/advisor/mcp_server.py, analysis/instruments.py, portfolio/allocation.py,
             portfolio/directives.py, portfolio/evaluation.py, tests/e2e/test_evaluate_allocation.py
  Related:   ENG-2, ENG-3, ENG-22
-->

**Description:** Confirmed by reading every import in `mcp_server.py`
directly: `M07.auto_disqualify()`, `M08.dual_role_conflict()`, the entire
M09/M10 RESPONSES table (`portfolio/directives.py` — 54 entries, complete
and tested), `M13.idealAllocation()`/`FeasibilityCheck()`/
`ComputeTargetMultiplier()`/`RecalibrationSequence()`
(`portfolio/allocation.py`), and M15's `classifyInstrument()`/
`blendedScenarioReturn()`/`dominantDirective()`
(`analysis/instruments.py`) were all implemented faithfully and had test
coverage — but none of them were imported or called anywhere in
`mcp_server.py`. (M15's `validate_classifications` and M07/M08's other
functions referenced elsewhere were the only exceptions actually wired.)

**Why it mattered:** roughly a third of the framework's logic. Every live
session, Claude was re-deriving all of this by hand from the `.md` spec —
directive lookups, allocation math, feasibility checks — because no MCP
tool surfaced the Python version. Directly contradicted design principle
#1 ("minimize AI to interpretation-only tasks; all arithmetic, threshold
comparisons... belong in Python").

**Resolution (2026-06-17):** Added two new MCP tools to `mcp_server.py`:

- `advisor_evaluate_allocation(account_profile, current_weights, tickers?,
  proposed_allocations?)` — wires `scenario_weighted_allocation()` (full
  per-scenario breakdown, probability-weighted target, blended
  conservative return, floor, naive directive), `dominant_directive()`
  (conflict-aware, multi-role — supersedes the naive directive for
  presentation), `dual_role_conflict()` (M08), `classify_instrument()`
  (M15 ComponentVector), and `feasibility_check()` (M13, when
  `proposed_allocations` is given). Requires `advisor_run_computation()`
  and `advisor_apply_scoring()` to have run this session (uses their
  cached `cal`/`scenario_probs` — never recomputes probabilities). No
  Python parser exists for the allocation sheet's "Objectives" tab, so
  `account_profile` is a dict Claude constructs after reading it
  directly — same pattern as the existing `floor_account_weights_json`
  parameter on `advisor_run_computation`.
- `advisor_check_instrument_candidate(ticker, aum_millions?,
  track_record_years?, foreign_concentration_pct?, instrument_type,
  revenue_type, has_contract_backstop, hold_horizon_years)` — wires M07's
  `auto_disqualify()`. No session precondition; pure on supplied metrics.

Per-ticker failures are isolated (one unclassified ticker doesn't take
down the whole call) and every external call is wrapped with a flag on
failure, matching the error-handling convention already used in
`_tool_run_computation`.

Added `tests/e2e/test_evaluate_allocation.py` (13 tests, all passing) —
genuinely end-to-end: exercises the MCP tool wrapper composing five
underlying functions for one ticker the way a real session would, not
just the underlying functions in isolation (those already had coverage
in `tests/test_stage4/` — what was missing was the composition layer,
which is exactly what shipped unwired). Covers: precondition errors (no
`advisor_run_computation`/`advisor_apply_scoring` having run), invalid
`objective_type`, full per-scenario breakdown shape, dominant-scenario
selection, composite-instrument component weights, `DualRoleConflict`
detection on a composite with genuinely conflicting ADD/REDUCE directives
in its dominant scenario, per-ticker failure isolation,
`FeasibilityCheck` skip/run paths, and the M07 candidate check's
disqualify/pass/no-precondition paths. Full existing suite
(536 passed, 4 skipped) re-run clean after the change.

**Follow-up, not done here:** `Project_Instructions_MCP.md`'s "How to
make a recommendation" and "How to execute a position action" sections
still describe the manual hand-derivation procedure — they should be
updated to call the new tool instead, the next time that file is
touched. M13's `RecalibrationSequence()` also remains unwired (out of
scope for this pass — narrower than the allocation/feasibility/
directive/classification math this closed).

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

### ENG-17 — BriefingRegistry described as built ("Phase 2 complete") but doesn't exist in Python anywhere
<!-- ITEM
  Status:    OPEN
  Severity:  LOW
  Category:  documentation
  Opened:    2026-06-17
  Area:      M02_IntelGathering.md, M04_BriefingFormat.md,
             M11_CreditAndCalibration.md, M14_MarketRegime.md, M17_SystemicCascadeWarning.md,
             M19_ThesisSustainingConditions.md, FW_Types.md
  Related:   ENG-2
-->

**Description:** Confirmed no `BriefingRegistry` class exists anywhere in
`python/advisor/` — not in `mcp_server.py`, not in `orchestrator/session.py`,
not in `types.py`. `FW_Types.md`'s own `BriefingRegistry`/
`BriefingSectionSpec` structs were never translated into `types.py` at
all — they remain pseudo-code only. Despite this, six module files
contain a "Phase 2 complete: BriefingRegistry.assemble()..." annotation
describing a working registry-based briefing-assembly system. (A seventh,
`M05_SessionInit.md`, was originally also listed here — checked during
ENG-23's retirement pass and confirmed it did NOT actually contain this
annotation by the time it was deleted, so the count is six, not seven;
removed from this item's Area.) (Contrast
with `FetchRegistry`, which really was built as real Python and really is
wired — so the asymmetry is real, not just consistently-stale wording
everywhere.) Briefing rendering is, and remains, 100% Claude's job,
following each module's `BriefingBlock`/`render_fn` spec directly in
prose — which is fine and already correct in practice (Claude follows
`Project_Instructions_MCP.md`, not this claim) — the only problem is the
documentation actively misleads about what exists in code.

**Why it matters:** low urgency today since nothing currently relies on
the false claim, but it risks sending a future coding session looking
for nonexistent code, or being used to justify treating M04 as more
Python-owned than it is.

**Suggested next step:** in each of the seven files, replace "Phase 2
complete: BriefingRegistry.assemble()..." with an accurate one-line
note that this section ordering is a Claude-applied convention, not
executed code. Cosmetic, low-risk, batchable in one pass.

### ENG-18 — M17 CascadeChainRegistry embeds live dated figures in module file; CHAIN_5/6 not scored
<!-- ITEM
  Status:    OPEN
  Severity:  LOW
  Category:  hygiene
  Opened:    2026-06-17
  Area:      M17_SystemicCascadeWarning.md, Calibration_State.md, python/advisor/analysis/cascade.py
  Related:   ENG-2, ENG-9
-->

**Description:** Two related findings from reading `M17_SystemicCascadeWarning.md`
against `analysis/cascade.py`:

1. `CascadeChainRegistry`'s `ACTIVE_STATUS` fields embed live, dated
   figures directly in the module file (e.g. specific debt totals, YoY
   filing percentages, margin-debt levels, dated 2026 figures) — this is
   the same "why/how vs what-now" violation ENG-9 already flags for §13,
   just in the opposite direction: live data sitting in a module `.md`
   instead of `Calibration_State.md`, with no versioning mechanism, so it
   will go stale silently.
2. `sector_stress_score()` in `cascade.py` only scores CHAIN_1 through
   CHAIN_4. CHAIN_5 (Sovereign Fiscal → E Pathway) is partially covered
   by `compute_yield_curve_signal()`'s separate term-premium/E-watch
   logic (same module, different function — not a gap), but CHAIN_6
   (Municipal Fiscal) has no scoring logic anywhere and is explicitly
   qualitative-only per its own `.md` text — confirmed intentional, not
   a bug, but worth noting alongside finding 1 since both concern the
   same registry.

**Suggested next step:** move the dated `ACTIVE_STATUS` figures out of
M17.md into a new `Calibration_State.md` §-numbered section (parallel to
how §13 holds M19's per-ticker data), leaving M17.md with only the
structural chain definitions. Larger edit than a simple shrink since it
requires touching Calibration_State.md's section numbering — not done
as part of the ENG-2 pass.

### ENG-19 — 8 of 17 RoleID roles have no M09/M10 scenario-directive coverage anywhere
<!-- ITEM
  Status:    CLOSED
  Severity:  MEDIUM
  Category:  functional-gap
  Opened:    2026-06-17
  Closed:    2026-06-20
  Area:      M09_ScenariosABC.md, M10_ScenariosDEF.md, python/advisor/portfolio/directives.py,
             python/advisor/types.py, python/tests/test_stage4/test_directives.py
  Related:   ENG-2, ENG-13, ENG-16
-->

**Description:** `FW_Types.md`'s `RoleID` enum lists 17 roles (per
`CALIBRATION_STATE` §11.1), but the M09/M10 RESPONSES table — and its
Python mirror, `directives.py` — only define directives for 9 of them.
`directives.py`'s own docstring admits this: "Newer §11 roles not in
M09/M10 return HOLD with a quality_flag." The 8 uncovered roles:
`secular_technology_growth`, `inflation_linked_sovereign`,
`real_estate_equity_income`, `systematic_trend_following`,
`consumer_defensive_equity`, `healthcare_defensive_equity`,
`floating_rate_credit_income`, `emerging_market_equity`.

**Pre-check (2026-06-20):** confirmed `Calibration_State.md` §11 does
NOT fill the gap some other way as the original item speculated it
might — §4.1 carries full per-scenario *return* values for all 8 roles
(several ★ ADOPTED HIGH confidence, several ⚑ MEDIUM pending June 30,
`real_estate_equity_income` entirely ⚠ LOW), but §11.1 has no
ADD/HOLD/REDUCE/EXIT directive table for any of them — the coverage gap
was real, not a documentation gap.

**Resolution (2026-06-20):** Added all 48 missing (role, scenario)
entries — methodology: each cell derived from that role's §4.1
conservative-end return value plus its §11.1 `Binding Driver` and
account/tax context, using the same directive vocabulary and severity
conventions already established by the original 9-role table (e.g. a
conservative return beyond approximately -8 to -10% is treated as the
existing `EXIT` threshold, per `broad_market_equity_international`'s own
D/E directives; a role's two best-return scenarios get `ADD`, not every
positive-return scenario, mirroring how `inflation_hedge_precious_metals`
and `inflation_hedge_commodity_linked` are only `ADD` in B, not C, despite
positive C returns). Full per-cell rationale is written inline in
M09/M10's RESPONSES blocks under a `NEWER §11 ROLES` subsection per
scenario — not just in this backlog entry.

Three cross-cutting judgment calls worth flagging explicitly:

1. **`real_estate_equity_income`** — every cell is `Evaluate` (explicit
   EV calc required before acting), not a directional directive. Its
   entire §4.1 row is LOW confidence — the framework's own calibration
   notes describe an unresolved 1970s-NAREIT-vs-2022-VNQ conflict that is
   *specific to Scenario B*, not a general data-quality footnote.
   Encoding a directional ADD/REDUCE off that row would be asserting
   conviction the framework itself doesn't have. This role is not
   currently held in any account, so the practical impact today is nil.
2. **`emerging_market_equity`** — `EXIT` in 4 of 6 scenarios (B, C, D, E).
   This looks aggressive but is a direct read of §4.1: every one of those
   four conservative values (-12%, -15%, -25%, -22%) exceeds the
   framework's own existing EXIT threshold as established by
   `broad_market_equity_international`'s D/E directives (-8%, -10%). EM
   is explicitly the most volatile role in the entire return table by a
   wide margin. Not currently held in any account — VWO is listed as an
   "instrument candidate" only.
3. **`inflation_linked_sovereign`** joined the Scenario E
   pathway-conditional set (alongside the two `rate_sensitive_income`
   roles) — its §11.1 binding driver explicitly lists
   `sovereign_credit_quality`, which is directly pathway-sensitive.
   `resolve_e_pathway_directive()` now branches on it: its instrument
   candidate is VTIP (short-term TIPS, ~2.5yr duration per §11.1), so it
   is resolved like `rate_sensitive_income_short_duration`
   (SYSTEMIC_LIQUIDITY → Hold; RESERVE_EROSION → Evaluate counterparty
   risk), not like the long-duration role.

`directives.py`: `DIRECTIVES` grew from 54 to 102 entries (17 roles × 6
scenarios); `_M09_M10_ROLES` and `_E_PATHWAY_ROLES` updated;
`directive_count()` regression anchor updated to 102.
`tests/test_stage4/test_directives.py`: rewritten for 17-role coverage —
the "unregistered role" fallback tests now use a synthetic
`placeholder_uncovered_role` name since all 17 real roles are covered
(the fallback path itself is unchanged and still tested); added spot-check
parametrized tests for the 8 newer roles plus a pathway test for
`inflation_linked_sovereign`. Full suite: 575 passed (`not integration`,
excluding the live-file `test_stage2` per ENG-12), 18 deselected.
`tools/validate_manifests.py`: 19/19 pass. M09/M10 bumped to v1.2.

**Not done in this pass:** the actual SEQUENCE/DE_ESCALATION blocks for
these 8 roles (rotation ordering, unwind priority) were not added — only
RESPONSES (the directive itself). The original ask and this fix are both
scoped to directive *coverage*; rotation-sequence integration for the
newer roles would be a reasonable follow-on if any of them moves from
"instrument candidate" to an actual held position with meaningful weight.


### ENG-20 — M14 energy_180d extended-conflict caveat not implemented in regime.py
<!-- ITEM
  Status:    CLOSED
  Severity:  MEDIUM
  Category:  functional-gap
  Opened:    2026-06-17
  Closed:    2026-06-20
  Area:      M14_MarketRegime.md, python/advisor/analysis/regime.py, python/advisor/types.py,
             python/tests/test_stage3/test_regime.py
  Related:   ENG-2
-->

**Description:** `M14_MarketRegime.md`'s `ComputeDivergenceSignal` has an
"EXTENDED CONFLICT CAVEAT" (added 2026-06-07): when an active discrete
supply event has persisted > 90 calendar days, both endpoints of the
`energy_90d` window fall inside the conflict period, so the signal can
understate a sustained war premium — the spec says to also compute
`energy_180d` and use the higher reading. Confirmed during the ENG-2 pass
that `analysis/regime.py`'s `compute_divergence_signal()` had no
conflict-duration awareness and never computed an `energy_180d` fallback
— it unconditionally used the 90d window.

**Resolution (2026-06-20):** `compute_divergence_signal()` now accepts an
optional `conflict_duration_days` parameter, mirroring the exact same
caller-responsibility convention already established by
`entry_extension_guard()`'s parameter of the same name (the caller — in
practice, Claude, from a T1-confirmed conflict onset date — supplies it
each session; the function does not infer conflict duration on its own).
When `conflict_duration_days > 90`: `energy_180d_change` is computed via
the same `compute_pct_change()` helper already used for the 90d figure
(just with `window=180`), and the **higher** of the two readings drives
`commodity_fear_divergence` classification, per the spec's "use the higher
reading" instruction. Both readings are always returned on
`DivergenceSignal` (new `energy_180d_change` field, default `None`) so the
briefing can surface the spec's exact flag format: `"⚠ Conflict > 90d:
energy_90d may understate war premium — 180d: [value%]"`. When the
parameter is omitted (`None`, the default), behavior is byte-for-byte
unchanged from before this fix — 90d-only, zero regression risk for every
session that doesn't pass it.

Insufficient-history case handled gracefully: if `conflict_duration_days >
90` but fewer than 181 daily Brent points are available, a flag is
emitted ("insufficient BRENT_CRUDE history to compute") and classification
falls back to the 90d-only value rather than raising.

`M14_MarketRegime.md`'s caveat text updated in place to point at the
implementation instead of describing it as a manual gap. M14 bumped to
v1.6. New `tests/test_stage3/test_regime.py` (9 tests — this file didn't
exist before; `regime.py` had no test coverage at all) covers: default
(no-parameter) behavior unchanged, conflict ≤ 90d does not trigger the
180d fallback, conflict > 90d with sufficient history computes 180d and
the higher reading wins classification (and the reverse — 90d already
higher, 180d does not override), insufficient-history graceful fallback,
and basic return-type/empty-input sanity. Full suite (`not integration`,
excluding `test_stage2` per ENG-12): 575 passed, 18 deselected.
`tools/validate_manifests.py`: 19/19 pass.

**Not done in this pass (pre-existing gap, not introduced or worsened
here):** nothing in `mcp_server.py` currently passes
`conflict_duration_days` into the automatic per-session call to
`compute_divergence_signal()` — exactly mirroring the fact that nothing
calls `entry_extension_guard()` from `mcp_server.py` either today. Both
functions share the same caller-responsibility design; wiring an
automatic conflict-duration source (e.g. a tracked onset date in
Calibration_State.md) into `advisor_run_computation()` would be a
reasonable follow-on, but is a different, larger question (where does
conflict duration come from at all, for either guard) than what this item
asked for. Separately: as of this writing the active geopolitical
context is a US-Iran ceasefire framework moving toward de-escalation, not
an extended live conflict, so this caveat does not appear to be
operationally live right now — worth a fresh check if a Scenario C
supply-shock event becomes active again.


**Environment note (2026-06-20):** this machine's registered Python
installations (`miniforge3` 3.12, `Program Files\Python311`) had neither
`pytest` nor the project's other dependencies installed — the
`C:\Python\python.exe` 3.12.10 interpreter referenced in earlier sessions
no longer exists on this machine. Installed `pytest`, `pytest-mock`,
`python-dotenv`, `mcp`, `pandas`, `yfinance` into `miniforge3`'s base
environment to restore a working test run. No venv created (consistent
with prior sessions); flagging in case this surprises a future session
expecting the old interpreter path.


### ENG-21 — M12's documented GitHub read-fallback vs file_protocol.py's actual Drive fallback
<!-- ITEM
  Status:    OPEN
  Severity:  LOW
  Category:  hygiene
  Opened:    2026-06-17
  Area:      M12_DriveProtocol.md, python/advisor/data/file_protocol.py
  Related:   ENG-2
-->

**Description:** `M12_DriveProtocol.md` documents the read-fallback path
for framework `.md` files as: 1st Desktop Commander (local git path),
2nd GitHub MCP — explicitly stating Google Drive is "NOT used for .md
reads." This describes Claude's own direct-tool-call read path (used in
READONLY_MOBILE or when Claude itself is reading these files, e.g. in a
coding session). Separately, `file_protocol.py`'s internal
`_read_from_drive()` fallback — exercised only when the
`financial-advisor` MCP server's own Python process can't find the file
locally — uses the Google Drive API, not GitHub. These may not actually
be in conflict in practice: the Python server fallback is a rarely-
triggered internal resilience path (the server already requires local
filesystem access to run at all, so the local file being absent is an
edge case — e.g. misconfigured `ADVISOR_FRAMEWORK_PATH` or accidental
deletion), serving a different purpose than the READONLY_MOBILE path
M12.md describes. Flagged as low-priority and not fixed this pass — the
nuance needs more investigation (has this Python fallback path ever
actually fired in practice?) before deciding whether M12.md's absolute
"NOT used: Google Drive" rule needs qualifying or whether
`file_protocol.py`'s fallback should be changed to match it.

**Suggested next step:** before editing either side, check whether
`_read_from_drive()` has ever actually been exercised (log output,
existing tests). If it's genuinely dead code in practice, simplest fix
is removing it rather than reconciling two systems for an edge case
that doesn't occur.


### ENG-3 — Pattern A / Pattern B duplication & convergence decision
<!-- ITEM
  Status:    CLOSED
  Severity:  HIGH
  Category:  architecture
  Opened:    2026-06-17
  Closed:    2026-06-18
  Area:      python/advisor/orchestrator/session.py, python/advisor/mcp_server.py,
             python/advisor/rendering.py
  Related:   ENG-1, ENG-2, ENG-4, ENG-11
-->

**Description:** Two independent implementations of the session pipeline
exist: Pattern B (`mcp_server.py` — Claude orchestrates via 3 MCP tools;
active, production path) and Pattern A (`orchestrator/session.py` —
Python orchestrates, calling Claude at 3 bounded AI boundaries via the
real Anthropic API; Stage 5 target, not currently the active path). They
do not share an implementation of session write-back, briefing rendering,
or pipeline sequencing — each reimplements it independently.

**Why it matters:** ENG-1 is direct proof this duplication is already
costing correctness: the identical §8-format bug existed independently in
both files. Any future fix to one path has to be remembered and reapplied
to the other, with no mechanism forcing that to happen. This will keep
recurring until either (a) Pattern A is archived/explicitly deprioritized,
or (b) the shared logic (entry rendering, briefing rendering, write-back)
is factored into one place both patterns call.

**Suggested next step:** decide, as part of or alongside ENG-2, whether
Stage 5 / Pattern A is still a live goal. If yes: extract the duplicated
logic (§8 entry rendering at minimum — see `_fmt_scenario_probs` /
`_bullet_list` / `_numbered_list` in `mcp_server.py`, which Pattern A
should import rather than reimplement) into a shared module. If no:
mark Pattern A explicitly archived/frozen in this backlog and in
README.md, so future sessions don't keep half-maintaining it.

**Resolution (2026-06-18):** Framework owner decided option (b) — both
Pattern A and Pattern B are staying; neither is archived. Extracted the
duplicated logic into a new shared module, `python/advisor/rendering.py`:
`format_scenario_probs()`, `format_bullet_list()`, `format_numbered_list()`,
`build_session_log_entry()` (the §8 entry construction — the exact thing
that had ENG-1's bug independently in both files), and
`render_portfolio_state()` (parameterized by `generator_label` so each
pattern's Portfolio_State.md output stays correctly attributed).
`mcp_server.py._tool_write_back()` and
`orchestrator/session.py._step8_write_back()` both call these shared
functions now; the old `_render_portfolio_state()` and
`_append_session_log_entry()` instance methods in `session.py` were
removed entirely rather than kept as thin wrappers — there is now exactly
one implementation, not two that happen to agree.
New `tests/test_rendering.py` (17 tests) tests the shared module directly,
including `test_render_portfolio_state_both_patterns_use_same_structure` —
the direct proof of this item's resolution. `README.md` updated in 5
places to describe the dedup instead of flagging it as an open question.
Full suite: 535 passed, 46 skipped. See ENG-4 for the related fix this
unblocked.


### ENG-4 — Stage 5 (Pattern A) incomplete plumbing
<!-- ITEM
  Status:    CLOSED
  Severity:  MEDIUM
  Category:  architecture
  Opened:    2026-06-17
  Closed:    2026-06-18
  Area:      python/advisor/orchestrator/context.py, session.py, ai_client.py
  Related:   ENG-3
-->

**Description:** `SessionContext` has no structured field carrying
open_triggers / open_decisions through the pipeline. As a result,
`_append_session_log_entry()` writes literal `[review session briefing]`
placeholder text into those §8 fields rather than real content. This was
left as an explicit placeholder (not fabricated) during the ENG-1 fix.

**Why it matters:** if Pattern A is ever run for a real session (vs. the
StubAIClient dry-run tests), its §8 entries will have permanently useless
open_triggers/open_decisions fields, defeating the purpose of carrying
them forward.

**Suggested next step:** add `open_triggers: List[str]` and
`open_decisions: List[str]` fields to `SessionContext`, populate them
from wherever the pipeline currently surfaces this information (briefing
generation step, most likely), and wire them into
`_append_session_log_entry()`. Blocked on / informed by the ENG-3 decision
— don't invest in this if Pattern A is going to be archived.

**Resolution (2026-06-18):** Unblocked by ENG-3 (Pattern A is staying).
Added `open_triggers: List[str]` and `open_decisions: List[str]` fields
to `SessionContext`. Rather than populate them from a separate
extraction step, extended `AIClient.generate_briefing()`'s existing
prompt (AI Call 3) to also append a structured `###OPEN_ITEMS###`
trailer after the NET_ASSESSMENT section — `generate_briefing()` now
returns `(briefing, open_triggers, open_decisions)`, parsed by a new
`_split_open_items()` helper in `ai_client.py`. No added AI-call cost:
the model already has full session context in that one call.
`StubAIClient` returns clearly-labeled `[STUB] ...` placeholders rather
than silently empty lists, consistent with its existing pattern for the
other two AI calls. If the live model ever fails to return a parseable
trailer, the result is an honest empty list plus a flag in
`ctx.write_back_flags` — never a fabricated placeholder.
`_step8_write_back()` now passes `ctx.open_triggers`/`ctx.open_decisions`
into the shared `rendering.build_session_log_entry()` (see ENG-3) instead
of the old hardcoded `[review session briefing]` strings. 4 new parser
tests + an updated `test_stub_generate_briefing` in
`tests/test_stage5/test_session.py`.

### ENG-5 — Compaction cadence mismatch (Calibration_State §3, Session_Log §8)
<!-- ITEM
  Status:    CLOSED
  Severity:  HIGH
  Category:  hygiene
  Opened:    2026-06-17
  Closed:    2026-06-19
  Area:      Calibration_State.md §3, Session_Log.md §8, M12_DriveProtocol.md
  Related:   ENG-6, ENG-7, GAP-7
-->

**Description:** Both files' compaction is gated to quarterly Q-end audits
(`M12.CompactSessionLog`, run at June 30 / Sep 30 / Dec 31 / Mar 31), but
the framework versions multiple times per week. By audit time, §3 had
accumulated ~24 verbose narrative entries against a stated "last 10"
intent, and §8 had well more than the "last 3 full entries" the compaction
rule specifies. Calibration_Log.md (the §3 overflow archive) hadn't been
touched since May 7 as of this writing.

**Why it matters:** Calibration_State.md is the largest file in the
framework (1,695 lines / 146 KB as of 2026-06-17), loaded as Project
Knowledge every advisory session. §3 + §11 + §6 alone account for over
half of it. The quarterly cadence guarantees this keeps recurring every
quarter rather than being addressed.

**Suggested next step:** decouple compaction from calendar gating —
trigger it whenever §3 exceeds 10 entries or §8 exceeds 3, evaluated at
every write-back, not just at Q-end. Ideally implemented in
`advisor_write_back()` itself (Python), since it already touches these
files. M12's `CompactSessionLog` procedure should gain its own explicit
STEP 1-4 sequence for §3 (it currently only handles §3 as an
afterthought — "Calibration_State.md (if §3 trimmed)" — with no
dedicated retain-count logic the way §7/§8 have).

**Resolution (2026-06-19):** Both halves fixed.

§7/§8 (Session_Log.md): fully automated. Added `_compact_session_log()` to
`file_protocol.py`, called automatically from `write_back()` on every call — no
longer something Claude executes by hand at all. Checks §7 > 10 rows / §8 > 3
entries; archives overflow into the current quarter's Archive_[Year]Q[N].md
(creating it if absent, appending and merging into existing sections if not) in
the SAME git commit as the write-back. 24 new tests in
`tests/test_stage1/test_compaction.py` cover no-overflow, §7-only, §8-only, both
together, archive creation vs. append, and the same-quarter repeated-compaction
merge case (a real bug found and fixed during this implementation — the second
same-quarter compaction was creating a duplicate "## Archived §8" section instead
of merging into the first one).

§3 (Calibration_State.md): one-time catch-up performed manually (26 entries →
10; 17 archived to Calibration_Log.md, v1.12-v1.28) plus the trigger condition
fixed going forward — M12_DriveProtocol.md's `CompactSessionLog` rewritten as
`CompactCalibrationLog` (Amendment 6), checked per-session rather than quarterly.
Stays manual by design — `write_back()` never touches Calibration_State.md (see
the NEVER rule above) — but the stale quarterly gate that let this recur is gone.

Also closed in the same pass: ENG-6, ENG-7, ENG-8, ENG-9 (all downstream of this
item's §3 bloat). See each item below for specifics.


### ENG-6 — §6 First-Audit Checklist accumulates stale content
<!-- ITEM
  Status:    CLOSED
  Severity:  MEDIUM
  Category:  hygiene
  Opened:    2026-06-17
  Closed:    2026-06-19
  Area:      Calibration_State.md §6
  Related:   ENG-5
-->

**Description:** §6 is meant to be one-time prep for the June 30 audit,
but items resolved elsewhere are never pruned from it. Example: item 35
is a ~15-line walkthrough of the secular_technology_growth B revision
debate, which §3 shows was already ADOPTED at v1.27 — the checklist is
duplicating a decision that's been final for weeks.

**Suggested next step:** any §6 item marked ADOPTED/COMPLETE per a §3 log
entry should be reduced to a one-line pointer ("see §3 v1.27") or deleted
outright in the same version bump that resolves it — not left for
"cleanup later," which in practice means cleanup never.

**Resolution (2026-06-19):** Confirmed via the live §4.1 table (which already
showed secular_technology_growth Scenario B = [-2,+4]★) plus Calibration_Log.md's
v1.27 entry ("STG B [-6,-1]→[-2,+4] ADOPTED HIGH confidence... 3 clean analogues
(1973-82, Q1 2026, + 2022 acute-phase partial)") that item 35's ~15-line MEDIUM-
confidence debate was fully superseded weeks before this fix — the table had
already moved on, only the checklist hadn't. Reduced to a 6-line pointer citing
§3 v1.27; full adoption rationale remains intact in Calibration_Log.md, not lost,
just not duplicated in two places.


### ENG-7 — §11 stores computed EV math redundantly
<!-- ITEM
  Status:    CLOSED
  Severity:  MEDIUM
  Category:  hygiene
  Opened:    2026-06-17
  Closed:    2026-06-19
  Area:      Calibration_State.md §11.3, python/advisor/analysis/instruments.py
  Related:   ENG-5
-->

**Description:** Each §11.3 instrument entry stores full per-scenario EV
arithmetic as static text (e.g. `A: (0.50×3+0.50×2)×0.188 = +0.470%`).
This is recomputed fresh every session by
`M15.blendedScenarioReturn()` / `analysis/instruments.py` from
ComponentVector + §4.1 + current probabilities — it is output, not
configuration. Storing it means it goes stale the moment probabilities
shift, requiring manual "stale — do not use" annotations (several exist
in the live file today).

**Suggested next step:** keep ComponentVector + target allocations +
qualitative rationale in §11.3; drop the per-scenario arithmetic
walkthrough. If an EV-at-decision-time audit trail is wanted, it belongs
in the (already compacted, per ENG-5) §3 log, not duplicated per
instrument on every revision.

**Resolution (2026-06-19):** Removed all 11 per-scenario EV arithmetic
walkthroughs (XAR, MLPX, SGOL, SGOV, PAVE, AIPO, MAGS, DBMF, SIVR, VTIP, XLP) —
replaced each with a one-line pointer to M15.blendedScenarioReturn(). Kept
ComponentVector, target allocations, guard status, and qualitative sensitivity
notes (e.g. MLPX's IHC-E-recalibration-risk note) untouched — those sit AFTER
the removed block boundary and have lasting value independent of any specific
stale number. §11.3 shrunk by ~3,450 characters across the 11 entries.

### ENG-8 — Orphaned exited-instrument entries not pruned
<!-- ITEM
  Status:    CLOSED
  Severity:  LOW
  Category:  hygiene
  Opened:    2026-06-17
  Closed:    2026-06-19
  Area:      Calibration_State.md §11.3
  Related:   ENG-5, ENG-7
-->

**Description:** PAVE still has a full §11.3 entry even though §3 logs it
as exited and dropped twice (v1.33, reconfirmed v1.37). Nobody deleted
the classification entry when the position was closed.

**Suggested next step:** add a NEVER rule — an exited instrument loses
its §11.3 entry in the same session/version bump that logs the exit, not
on a future cleanup pass. PAVE is the concrete example to fix first.

**Resolution (2026-06-19):** Confirmed via §3 (PAVE exit: 502sh Acc4 @~$56.095,
v1.33, reconfirmed exited at v1.37/v1.38) that the position has been fully closed
for weeks. Deleted PAVE's entire §11.3 entry (ComponentVector, target allocations,
the pre-exit hold/exit-trigger constituent analysis — all of it; none of it has
forward decision use for a closed position). Checked 15 other PAVE mentions
outside §3 across the document: all are either dated historical snapshots
(e.g. the v1.22 Consolidated Target Allocations table, correctly labeled with
its as-of date, predating the exit), permanent audit-log tables (§10), or
illustrative protocol text — none were live/current references needing
cleanup. (Found, but left for a future pass as a separate smaller instance of
this same pattern: a few §6 checklist items still reference PAVE-specific
follow-ups like an IIJA reauthorization assessment that are now moot.)
Added `PROCEDURE RemoveInstrument()` to `M15_InstrumentClassification.md`
(v1.1→1.2) with the requested NEVER rule, right after the existing
`RemoveRole()` procedure it's modeled on.


### ENG-9 — §13 preamble mixes methodology with live data
<!-- ITEM
  Status:    CLOSED
  Severity:  LOW
  Category:  hygiene
  Opened:    2026-06-17
  Closed:    2026-06-19
  Area:      Calibration_State.md §13, M19_ThesisSustainingConditions.md
  Related:   ENG-2
-->

**Description:** §13's status-taxonomy and briefing-suppression-behavior
explanation is methodology ("why/how"), not a calibration-dated value
("what now"). It belongs in M19_ThesisSustainingConditions.md.

**Suggested next step:** move the explanatory preamble into M19.md;
leave only the per-ticker data blocks in §13. Low priority — §13's
per-entry structure is otherwise appropriately lean (unlike §3/§6/§11).

**Resolution (2026-06-19):** Found, while implementing, that M19.md already
duplicated most of this preamble in distributed form: the ENUM ThesisStatus
comments cover the status taxonomy, the BRIEFING BLOCK comment covers the
suppression behavior, and a NEVER rule already said "see preamble" for the
scope exclusions — meaning M19 already structurally expected §13 to carry that
one piece. Only the Scope paragraph (which roles are excluded and why) was
genuinely new content; added it to M19.md as its own section, right after the
ENUM. Everything else in §13's old preamble was simply deleted rather than
duplicated again, since M19 already said the same thing. §13 now carries a
6-line pointer instead of the original ~25-line preamble.


### ENG-10 — No test coverage for advisor_run_computation / advisor_apply_scoring
<!-- ITEM
  Status:    CLOSED
  Severity:  HIGH
  Category:  testing
  Opened:    2026-06-17
  Closed:    2026-06-18
  Area:      python/advisor/mcp_server.py
  Related:   ENG-1, ENG-11
-->

**Description:** Verified by grep — no test anywhere calls
`_tool_run_computation` or `_tool_apply_scoring`. Only `_tool_write_back`
has tests (added closing ENG-1). These are the two most complex tools in
the active Pattern-B path: `_tool_run_computation` fetches all M18 market
data and computes credit/regime/cascade/yield-curve signals;
`_tool_apply_scoring` runs the M03 probability arithmetic, normalization,
floor application, and 25pp session cap.

**Why it matters:** this is exactly the coverage gap that let ENG-1 ship.
The underlying analysis functions (`analysis/*.py`) do have unit tests
(test_stage3), but nothing tests that `mcp_server.py`'s tool wrappers
correctly call them, cache results between calls, or produce the JSON
shape the session protocol depends on.

**Suggested next step:** add `tests/test_mcp/test_run_computation.py` and
`test_apply_scoring.py` — at minimum, call each tool function with
realistic inputs against an isolated temp framework dir (same
`ADVISOR_FRAMEWORK_PATH` pattern used in `test_write_back_format.py`) and
assert the returned JSON has the documented shape and that `_cache` is
populated correctly for the next tool in the sequence to consume.

**Resolution (2026-06-18):** Implemented as suggested. `tests/test_mcp/test_run_computation.py`
added with 23 tests covering both `_tool_run_computation()` (OK status, prior_probs
shape/sum, scoring_questions structure, signals key, calibration_version,
floor_breach_alerts, market_data_summary, and _cache population for
cal/log/scoring_questions/readings) and `_tool_apply_scoring()` (precondition
error, OK status, probs sum-to-100, all 6 scenarios present, 3% floor respected,
scenario_probs cached, raw_scores shape, write_back prereqs confirmed). All
network fetchers mocked via `FetchRegistry.fetch_all` monkeypatch — tests run
against the real Calibration_State.md/Session_Log.md content for config parsing
fidelity, skipped automatically if those files are absent (same pattern as
ENG-12's `skip_if_missing`). 0 failures.


### ENG-11 — No Pattern-B end-to-end pipeline test
<!-- ITEM
  Status:    CLOSED
  Severity:  HIGH
  Category:  testing
  Opened:    2026-06-17
  Closed:    2026-06-18
  Area:      python/advisor/mcp_server.py
  Related:   ENG-3, ENG-10
-->

**Description:** Pattern A has `test_stage5/test_session.py`'s pipeline
tests, exercising `SessionPipeline.run()` end-to-end with a stubbed AI
client. Pattern B — the actually active path — has no equivalent: no
test calls `_tool_run_computation` → `_tool_apply_scoring` →
`_tool_write_back` in sequence the way a real Claude session does.

**Suggested next step:** add an end-to-end test that runs the three tool
functions in sequence against an isolated temp framework dir, feeding
deterministic stubbed "answers" for the scoring step (analogous to
StubAIClient), and asserts the final Session_Log.md is fully parseable
and internally consistent (sum-to-100, dates monotonic, etc.). This is
the single highest-value test currently missing in the repo.

**Resolution (2026-06-18):** Implemented as suggested.
`tests/test_mcp/test_pattern_b_pipeline.py` added with 10 tests: 2 sequential-
dependency checks (write_back fails cleanly without prior run_computation or
apply_scoring) and 8 full-pipeline tests running
`_tool_run_computation()` -> `_tool_apply_scoring()` -> `_tool_write_back(dry_run=True)`
in sequence against an isolated tmp dir seeded with real Calibration_State.md
content and a minimal Session_Log.md. Confirms: no errors anywhere in the
sequence, the new §8 entry is distinct and parseable (not merged into the
seed block), new entry probabilities sum to 100% and respect the 3% floor,
the seed entry is preserved unchanged, entry dates are chronologically
monotonic, and open_triggers/open_decisions/next_session_flags round-trip
correctly through the write → re-parse cycle. Network fetchers mocked the
same way as ENG-10. 0 failures.


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


### ENG-13 — M19 trailing-window conditions have no tracking infrastructure
<!-- ITEM
  Status:    OPEN
  Severity:  MEDIUM
  Category:  functional-gap
  Opened:    2026-06-17 (originally noted in Calibration_State.md v1.38 log entry)
  Area:      python/advisor/analysis/thesis.py
  Related:   —
-->

**Description:** §13 conditions containing "sustained" / "consecutive" /
"rolling" / "trend" / "reversal" (6-12 week windows) are explicitly
skipped with a `quality_flag` rather than evaluated — there is no
historical-trend-tracking infrastructure yet. This is intentional,
documented behavior (not a silent gap), but the underlying capability
doesn't exist.

**Suggested next step:** design a small rolling-window store (could be as
simple as a CSV/JSON history file per tracked series, updated each
session) that `thesis.py` can query for "has X trended directionally over
the last N weeks" — needed before any §13 condition using that language
can move from UNKNOWN to a real ACTIVE/DEGRADED/FAILED evaluation.


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


### ENG-23 — M05_SessionInit.md retired outright (ENG-2 follow-on decision #2)
<!-- ITEM
  Status:    CLOSED
  Severity:  MEDIUM
  Category:  architecture
  Opened:    2026-06-17
  Closed:    2026-06-17
  Area:      M05_SessionInit.md (deleted), 00_INDEX.md, Project_Instructions_MCP.md,
             FW_Types.md, M03/M04/M12/M13/M14/M15_*.md, README.md
  Related:   ENG-2
-->

**Description:** Per the framework owner's explicit direction (2026-06-17:
"the modules and pseudo-code must go... all the unneeded ones should get
deleted entirely"), resolved the open question ENG-2 deliberately left
unmade: `M05_SessionInit.md` had already been reduced to a pure
step-cross-reference stub (no executable content of its own — see its
v1.6 history), with the real sequence fully owned by
`Project_Instructions_MCP.md`. A stub with zero unique content is the
clearest possible deletion candidate in the whole module set.

**What was found and fixed in the process (not just the deletion):**
`00_INDEX.md`'s own `SESSION_START_SEQUENCE` block — a second, independent
copy of the session sequence, never updated when M05 was first shrunk —
was not just redundant but actively wrong: it ended in step 10,
`M12_FileProtocol.WriteBack` / `push_files([...])`, a literal instruction
to write back via GitHub. This directly contradicts 00_INDEX.md's own
`NEVER` list three sections down (`write_to_GitHub_without_confirming...`)
and M12's CoreRules. It was never executed in practice — Claude follows
`Project_Instructions_MCP.md`, not 00_INDEX.md, for session mechanics —
but it sat there as a live landmine for anyone (human or a future Claude
coding session) who read 00_INDEX.md as the sequence source. Replaced
with a pointer, same pattern as M05's own prior shrink.

**Resolution:** Deleted `M05_SessionInit.md`. Updated every cross-reference
found via repo-wide grep: `00_INDEX.md` (MODULES list, ORCHESTRATION
sub-project, FILE_MAP, the `SESSION_START_SEQUENCE` block above, header
changelog comment → v1.25), `Project_Instructions_MCP.md` (file map table,
"Session start sequence" heading no longer names a file that doesn't
exist, M01–M19 project-knowledge list corrected — it had said M01–M18,
missing M19 entirely, a pre-existing typo fixed opportunistically while
in the area), `FW_Types.md` (`ModuleID` enum, `SubProject.ORCHESTRATION`
comment, a `REGISTRY TYPES` comment — version bumped 1.4→1.5), and one
cross-reference each in `M03_ScenarioFramework.md`, `M04_BriefingFormat.md`,
`M12_DriveProtocol.md`, `M13_GrowthObjectives.md` (three spots),
`M14_MarketRegime.md`, `M15_InstrumentClassification.md` — all retargeted
to `Project_Instructions_MCP.md`'s step numbering, which is unchanged
from M05's original numbering by design (1, 1b, 3b, 6b, etc. all match).
`README.md`'s module map and "which file do I edit" tables updated to
reflect the retirement. Historical session-type labels ("full M05
session") in `Session_Log.md`/`Calibration_State.md` log prose were left
untouched — "M05" survives only as that vocabulary, decoupled from any
file, exactly as the M05 stub's own retained `STEP_CROSS_REFERENCE` table
anticipated.

`tools/validate_manifests.py` re-run clean (19/19 — auto-discovers files
via glob, no hardcoded count to fix). Full pytest suite re-run clean:
535 passed, 4 skipped (one fewer than the prior 536 — `test_manifest_schema.py`
parametrizes over the same glob, one fewer file to assert PASS on; not a
regression).


### ENG-25 — instruments.json write not wired — Project_Instructions_MCP.md claimed MCP server writes it
<!-- ITEM
  Status:    OPEN
  Severity:  LOW
  Category:  architecture
  Opened:    2026-06-18
  Area:      python/advisor/mcp_server.py, python/advisor/data/file_protocol.py,
             M12_DriveProtocol.md (WriteBack STEP 4b), Project_Instructions_MCP.md
  Related:   ENG-2
-->

**Description:** Discovered during ENG-2 M12 assessment (2026-06-18). A
comment in Project_Instructions_MCP.md's Step 9 block read:
"instruments.json - written by MCP server automatically" (lowercase dash,
no em-dash). Confirmed via grep across all of `python/advisor/` that this
is false: no production code calls `.write_text()` on `_INSTRUMENTS_FILE`
— only test fixtures do. `advisor_run_computation()` (`_tool_run_computation`)
and `advisor_write_back()` (`_tool_write_back`) / `file_protocol.write_back()`
contain zero calls that create or update instruments.json.

`yfinance_fetcher.py` READS instruments.json at fetch time (via
`load_instruments()`) and falls back to a hardcoded list if the file is
missing/unreadable. So the fallback works, but the "automatically written"
claim was just wrong.

**Resolution so far:** Project_Instructions_MCP.md corrected to say
"written manually via Desktop Commander:write_file during WriteBack Step 4b
(@see M12_DriveProtocol.md WriteBack STEP 4b)". M12_DriveProtocol.md's
STEP 4b already correctly described the manual write; added a ⚠ note
confirming the automation gap and referencing this item.

**Suggested next step (LOW priority — fallback works):** Wire the
instruments.json write into `file_protocol.write_back()` or
`_tool_run_computation()` (after Calibration_State.md is loaded): extract
active tickers from `cal.instruments`, serialize to JSON, write to
`_MCP_DIR / "instruments.json"`. Then remove the manual step from
WriteBack and update Project_Instructions_MCP.md and M12 accordingly.


### ENG-24 — M13.RecalibrationSequence() has no Python implementation — still 100% manual
<!-- ITEM
  Status:    CLOSED
  Severity:  MEDIUM
  Category:  architecture
  Opened:    2026-06-18
  Closed:    2026-06-18
  Area:      M13_GrowthObjectives.md, python/advisor/mcp_server.py
  Related:   ENG-2, ENG-16
-->

**Description:** Confirmed by grep across `python/advisor/` — `RecalibrationSequence`
appears only as a string in three places (`types.py`, `mcp_server.py`,
`orchestrator/session.py`), all saying it's "required before allocation
recommendations proceed." No function anywhere actually implements it.
This is the one M13 function that survived the 2026-06-18 shrink pass
untouched, because there is nothing to point to — every other FUNCTION in
M13 (ComputeTargetMultiplier, RequiredRealReturn, ComputeFloor,
idealAllocation, FeasibilityCheck, PassiveMandateAbsentWarning,
CurrentHoldingsFloorCheck) is wired via `advisor_evaluate_allocation()` or
`advisor_run_computation()`; this one is still 100% Claude's manual job,
fires whenever `FeasibilityCheck` / `feasibility_check()` returns
`feasible: false`.

**Why it matters:** anchor-position identification, residual-gap
computation, and the reallocate-then-evaluate-new-instrument decision tree
are exactly the kind of deterministic, multi-step arithmetic the framework's
design principle #1 says belongs in Python, not re-derived by Claude each
time a feasibility check fails.

**Suggested next step:** port `RecalibrationSequence()` into
`portfolio/allocation.py` alongside the other M13 functions, wire it into
`advisor_evaluate_allocation()` (fire automatically when `feasibility.feasible
== false`), add e2e test coverage analogous to `tests/e2e/test_evaluate_allocation.py`,
then shrink M13's RECALIBRATION SEQUENCE section to match the rest of the file.


**Resolution (2026-06-18):** Implemented exactly as suggested above.
`recalibration_sequence()` added to `python/advisor/portfolio/allocation.py` alongside
the other M13 functions. `RecalibrationResult` dataclass added to `types.py`.
Wired into `_tool_evaluate_allocation()` in `mcp_server.py`: when
`proposed_allocations` is passed and `feasibility.feasible == False`, the tool
automatically calls `recalibration_sequence()` and adds a `recalibration` block to
the JSON output. `high_conviction_tickers` is an optional parameter; if not supplied
by Claude (having run M06.SimplicityTest), Python defaults to tickers with
`proposed_weight > compute_floor()` as a computable proxy. 15 new pytest cases
across `tests/test_stage4/test_allocation.py` (unit) and
`tests/e2e/test_evaluate_allocation.py` (e2e MCP wiring). Full pytest suite: 508
passed, 46 skipped, 0 failed. M13_GrowthObjectives.md RECALIBRATION SEQUENCE block
shrunk to pointer (v1.2→1.3). validate_manifests: 19/19 pass.

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
