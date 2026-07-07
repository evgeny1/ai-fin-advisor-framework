# Framework Backlog Archive

Full descriptions and resolutions for CLOSED engineering items (ENG-N),
moved here from FRAMEWORK_BACKLOG.md to keep that file lean -- same split
philosophy as Calibration_State.md / Calibration_Log.md. FRAMEWORK_BACKLOG.md's
Index table still lists every item (open and closed) for a complete status
overview; this file holds the full body for closed ones only, in ID order.

Maintenance: when an open item in FRAMEWORK_BACKLOG.md is closed, move its
full section here (in correct ID order) and leave a short stub in place of
it there. Do not edit closed items here except to fix factual errors --
this is a historical record, not a living document.

---

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

---

### ENG-2 — Module necessity review (M01–M19)
<!-- ITEM
  Status:    CLOSED
  Severity:  HIGH
  Category:  architecture
  Opened:    2026-06-17
  Closed:    2026-06-20
  Area:      M01_SourceIntegrity.md – M19_ThesisSustainingConditions.md (all 19), FW_Types.md
  Related:   ENG-3, ENG-12, ENG-13, ENG-14, ENG-15, ENG-16, ENG-17, ENG-18, ENG-19, ENG-20, ENG-21,
             ENG-22, ENG-23, ENG-24, ENG-25
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

**Closed (2026-06-20):** all three follow-on decisions this item's own
"Why this stays IN_PROGRESS" note conditioned closure on are now resolved:
(1) ENG-16 (mcp_server.py wiring) — CLOSED 2026-06-17; (2) ENG-23
(M05_SessionInit.md retirement) — CLOSED 2026-06-17; (3) the hygiene/
functional-gap findings spun out as ENG-17 through ENG-21 — all five
CLOSED as of today (ENG-19, ENG-20, ENG-17, ENG-21, ENG-18 all closed
2026-06-20; ENG-25, opened slightly out of the original 17–21 numbering
but part of the same M12 finding batch, also CLOSED 2026-06-20). ENG-18
in particular surfaced a real functional bug, not just hygiene — see its
own entry for detail — but it's resolved either way.

Five items opened during the same investigation remain genuinely open
but were never part of this item's own stated closure condition, and are
independently tracked rather than holding this one open further: ENG-12
(testing — live-file test assertions), ENG-13 (functional-gap — M19
trailing-window tracking), ENG-14 (documentation — GAP-11 label), ENG-15
(process — no CI), ENG-22 (testing — test suite reorg). None of these
concern "is this module still necessary," the question this item was
actually opened to answer; that question has been answered for all 19
files plus FW_Types.md, with evidence, twice over (the original pass and
the M07/M08/M13/M15/M12/M18 follow-on shrink passes above).

---

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

---

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

---

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

---

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

---

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

---

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

---

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

---

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

---

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

---

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

---

### ENG-17 — BriefingRegistry described as built ("Phase 2 complete") but doesn't exist in Python anywhere
<!-- ITEM
  Status:    CLOSED
  Severity:  LOW
  Category:  documentation
  Opened:    2026-06-17
  Closed:    2026-06-20
  Area:      M02_IntelGathering.md, M04_BriefingFormat.md,
             M11_CreditAndCalibration.md, M14_MarketRegime.md, M17_SystemicCascadeWarning.md,
             M19_ThesisSustainingConditions.md, FW_Types.md, 00_INDEX.md
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

**Resolution (2026-06-20):** Implemented as suggested, plus one expansion of
scope found during the fix. Corrected the false "Phase 2 complete:
BriefingRegistry.assemble()..." annotation in all six files that actually
contained it — `M04_BriefingFormat.md` (4 occurrences: registry-entries
header, render-functions header, template header, template body call),
`M11_CreditAndCalibration.md` (2), `M14_MarketRegime.md` (3, including a
SESSION_HOOKS step-line), `M17_SystemicCascadeWarning.md` (1),
`M19_ThesisSustainingConditions.md` (1), and `FW_Types.md`'s own
`BriefingRegistry` struct comment (1) — each replaced with a note that
Claude applies the `position_after` ordering manually each session, no
registry class executes. (`M02_IntelGathering.md` was correctly left
untouched — its own "Phase 2 complete" comment is about `FetchRegistry`/M18,
which really is wired; that file was in this item's Area only for
contrast, not because it carried the false claim — confirmed six files
had it, not seven, matching this item's own description.)

**Scope expansion found while fixing:** a repo-wide grep for the same
pattern (not just the Area-listed files) turned up three more instances in
`00_INDEX.md` that the original 2026-06-17 investigation missed — the
`SUB_PROJECTS` comment block, the `market_data` cross-reference chain, and
the `BriefingRegistry_is_extension_point` architecture rule. All three
corrected the same way. `00_INDEX.md` added to this item's Area
retroactively since it was actually in scope; bumped to v1.26 (its own
"Last updated" convention, not a MODULE MANIFEST — see ENG-23 precedent).
Worth flagging for future hygiene passes: grep the *pattern*, not just the
file list a prior session already identified — Area fields can themselves
be incomplete.

`tools/validate_manifests.py`: 19/19 pass. Full suite (`not integration`):
651 passed, 60 deselected — 0 regressions, as expected for a docs-only
change. Module versions bumped: M04 2.1→2.2, M11 1.4→1.5, M14 1.6→1.7,
M17 1.5→1.6, M19 1.2→1.3, FW_Types 1.5→1.6, 00_INDEX v1.25→v1.26.

---

### ENG-18 — M17 CascadeChainRegistry embeds live dated figures in module file; CHAIN_5/6 not scored
<!-- ITEM
  Status:    CLOSED
  Severity:  LOW
  Category:  hygiene
  Opened:    2026-06-17
  Closed:    2026-06-20
  Area:      M17_SystemicCascadeWarning.md, Calibration_State.md, Calibration_Log.md,
             python/advisor/config/calibration.py, python/advisor/analysis/cascade.py,
             python/tests/test_mcp/test_run_computation.py
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

**Resolution (2026-06-20):** Implemented finding 1's suggested fix, but the
investigation surfaced something more severe than this item's original
"hygiene/staleness" framing — not just unversioned live data sitting in
the wrong file, but a silently broken read path:

`calibration.py`'s `_parse_cascade()` locates §12.1–12.4 by searching for
the literal string `"## Section 12"` in `Calibration_State.md`. That
header did not exist in the live file at all — only `### 12.5` through
`### 12.8` existed, orphaned with no parent `## Section 12` heading above
them (sandwiched inside what was labeled "Consolidated Target
Allocations"), and `### 12.1`–`### 12.4` did not exist as written
subsections anywhere. With the anchor absent, `_parse_cascade()`'s search
came up empty every session, and **every cascade threshold silently fell
back to the hardcoded Python defaults baked into `_parse_cascade()`
itself, never reading this file** — `farm_filings_alert: "+50%"`,
`natgas_alert: "$6.00"`, `KRE_alert: "15%"`, `bankruptcy_quarterly_WATCH:
"220/quarter"`, etc. Confirmed this wasn't a parser bug:
`tests/test_stage2/test_calibration_parser.py`'s synthetic fixture has
always had the well-formed `## Section 12` / `### 12.1`–`### 12.4`
structure and the parser extracts values from it correctly — the live
file just never had matching structure built, despite
`M17_SystemicCascadeWarning.md`'s CHAIN_1–CHAIN_4 all explicitly
cross-referencing `@see CALIBRATION_STATE §12.1`–`§12.4`.

Confirmed via direct test (parsing the real file before vs. after the fix)
that today's computed cascade output is unchanged — §12.1–12.4 had
apparently never been formally calibrated to begin with (§6's audit
checklist already lists "M17 §12 first formal audit and threshold
calibration" as outstanding June 30 work), so the Python defaults and
what little §12.5–12.8 content did exist happened to agree. The real risk
was forward-looking: any future edit to these thresholds — including
whatever the June 30 audit produces — would have had **zero effect** on
the actual computation, since the parser could never reach them.

**Fix:** added the missing `## Section 12` header and `### 12.1`–`### 12.4`
subsections to `Calibration_State.md`, populated with the exact values
`_parse_cascade()` already defaulted to (so behavior is unchanged, but now
visible and live-editable instead of an invisible Python fallback), each
marked `⚠ PENDING formal calibration (Q2 audit)` for consistency with §6's
existing audit-checklist item. Moved `ACTIVE_STATUS` prose for CHAIN_1–4
out of `M17_SystemicCascadeWarning.md`'s `CascadeChainRegistry` into the
corresponding new §12.x subsections (M17 bumped v1.6→v1.7); each CHAIN
block now carries a one-line pointer instead. CHAIN_5 (already lived at
§12.5, not moved) and CHAIN_6 (confirmed intentionally qualitative-only,
per finding 2 above and its own `.md` text) needed no changes. A one-line
orphaned text fragment with no identifiable parent sentence
(`"...er) by ~74%. Would never have fired under any observed historical
scenario."`) sat immediately above where `### 12.5` began — removed
rather than guessed at; its likely origin (a CHAIN_4 800/quarter-threshold
backtest note) is already captured factually in `Calibration_Log.md`'s
existing 2026-06-01 (v1.24) archived entry.

Adding the new §3 entry pushed `Calibration_State.md`'s §3 log to 11
entries against its stated "last 10" limit (ENG-5) — compacted the oldest
(2026-06-02, v1.30, an unrelated AIPO classification audit entry) to
`Calibration_Log.md` to restore the invariant, in the same pass.
`Calibration_State.md` bumped v1.40→v1.41.

**Self-correction during this item:** an earlier pass at this fix placed a
multi-paragraph `<!-- RESOLVED ... -->` HTML comment directly inside
`Calibration_State.md` explaining the bug and fix — flagged by the
framework owner as the wrong location (this file is live config, not a
changelog) and removed; the explanation lives here and in a proper dated
§3 entry instead, matching how every other module-hygiene fix in this
backlog is documented. That same earlier pass also left a duplicate of
the 2026-06-02 AIPO entry in `Calibration_Log.md` without actually
removing it from §3 — apparently an incomplete, premature attempt at the
compaction this entry's addition would eventually require — reverted, then
the compaction was performed correctly (move, not copy) at the right
point in the sequence above. A citation in the new §3 entry's first draft
also incorrectly claimed the CHAIN_4 800/quarter note was "captured in
this section's 2026-06-01 entry below" — that entry doesn't exist in live
§3 (it was archived to `Calibration_Log.md` at v1.39's compaction, before
v1.30); corrected to cite `Calibration_Log.md` directly.

**Project_Instructions_MCP.md:** assessed for needed updates — none found.
It already describes `Calibration_State.md` §12 as the live source for
cascade thresholds (file-map table, Step 3 description) and M17 as owning
"cascade chain registry" structurally; both statements were already
correct as *intent*, they just weren't true in *practice* until this fix.
No wording in that file assumed `ACTIVE_STATUS` lived in `M17.md` or
referenced the missing header, so nothing there needed correcting.

**Test coverage added:** `tests/test_mcp/test_run_computation.py` —
`test_calibration_state_has_section_12_header`, a structural regression
guard (not a value assertion, since §12.1–12.4's actual values are
expected to change at calibration) confirming `"## Section 12"` is present
in the live file Claude actually loads each session. Considered adding
this to `test_calibration_parser.py` instead but that file's own docstring
states "No file I/O — all fixtures are self-contained strings"; the
live-file-testing pattern already exists in `test_run_computation.py` /
`test_pattern_b_pipeline.py` (`skip_if_missing`), so the guard was added
there to match established precedent rather than violating a different
file's stated design.

`tools/validate_manifests.py`: 19/19 pass. Full suite (`not integration`):
663 passed, 60 deselected (+1 from this item, 0 regressions). Confirmed via
a direct parse of the live file (both before reverting the bad earlier
attempt and after the final version) that all 13 `CascadeBlock` fields
read correctly and match expected values.

---

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

---

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

---

### ENG-21 — M12's documented GitHub read-fallback vs file_protocol.py's actual Drive fallback
<!-- ITEM
  Status:    CLOSED
  Severity:  LOW
  Category:  hygiene
  Opened:    2026-06-17
  Closed:    2026-06-20
  Area:      M12_DriveProtocol.md, python/advisor/data/file_protocol.py,
             python/advisor/data/fetchers/allocation_sheet.py
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

**Resolution (2026-06-20):** Investigated as suggested rather than guessing.
Confirmed `_read_from_drive()` had zero test coverage anywhere in the
suite, and traced its credential dependency: it reuses
`allocation_sheet._get_drive_service()`, which requires a service-account
or OAuth credential file under `~/.advisor/`. Confirmed with the framework
owner that this Python-native Google Drive client is not configured and
not currently needed — the Allocation spreadsheet is read by Claude
directly via the Google Drive MCP connector, not through this code path;
the Python-native client (this fallback, plus `allocation_sheet.py`'s
unwired `fetch_fred_series`/`fetch_finra_margin` FRED-via-sheet fetchers)
is a possible future feature.

Decided against outright removal — the suggested-next-step's "simplest
fix" framing assumed dead code with no future value, but the owner wants
to keep the option open. Instead: documented the actual state precisely
rather than reconciling two systems that were never in real conflict.
`M12_DriveProtocol.md`'s SOURCE_MAP comment block now explicitly scopes
the Desktop-Commander→GitHub hierarchy to Claude's own direct-tool read
path, and adds a paragraph distinguishing it from the Python server's
separate, currently-dormant local→Drive fallback (naming the missing
credential requirement and pointing at the Allocation-sheet/MCP-connector
split). Added a matching docstring note to `_read_from_drive()` in
`file_protocol.py` and a one-line note on the unwired FRED/FINRA
fetchers in `allocation_sheet.py`'s SOURCE_MAP entry — both flagged
"no action needed," not reopened as new items. M12 bumped Amendment 7→8.

**Test coverage added:** new
`tests/test_stage1/test_file_protocol_read_fallback.py` (4 tests) —
confirms `read_framework_file()` never touches Drive when the local file
is present, that it does attempt Drive when local is missing, that a
Drive failure produces a clean `HardStopException` naming both causes
(not an unhandled exception), and directly verifies
`_get_drive_service()` raises `EnvironmentError("Google credentials not
found")` with no credential files configured — empirically confirming the
"dormant by design" claim above rather than asserting it from code
inspection alone.

`tools/validate_manifests.py`: 19/19 pass. Full suite (`not integration`):
662 passed, 60 deselected (+4 from this item, 0 regressions).

---

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

---

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

---

### ENG-25 — instruments.json write not wired — Project_Instructions_MCP.md claimed MCP server writes it
<!-- ITEM
  Status:    CLOSED
  Severity:  LOW
  Category:  architecture
  Opened:    2026-06-18
  Closed:    2026-06-20
  Area:      python/advisor/mcp_server.py, python/advisor/data/fetchers/yfinance_fetcher.py,
             M12_DriveProtocol.md (STEP 4b), Project_Instructions_MCP.md
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

**Resolution (2026-06-20):** Implemented as suggested, wired at
`_tool_run_computation()` rather than `write_back()` — the source data
(§11.3 active tickers) is freshest right when `Calibration_State.md` is
parsed at session Step 3, and wiring it there means the write happens
even on sessions where write-back is skipped or fails later. Added
`write_instruments_json(tickers)` to `yfinance_fetcher.py` (co-located
with `load_instruments()`, which already owns `_MCP_DIR`/`_INSTRUMENTS_FILE`
path resolution — avoids duplicating that logic in `file_protocol.py`,
which writes to a different directory entirely and has no reason to know
about this path). Called from `_tool_run_computation()` right after
`alloc_tickers` is computed (the exact same §11.3-active, not-§11.4-candidate
list `validate_classifications()` already uses), wrapped in try/except —
a write failure is flagged (`result["flags"]`), not a `HARD_STOP`, since
`load_instruments()`'s existing fallback means a session can proceed
without a fresh write.

Format matches what M12 STEP 4b already specified for the manual version:
`{"instruments": [...], "last_updated": "[date]", "session": "[date] advisory"}`.
`instruments.json` continues to live outside the framework git repo
(sibling `market_data_mcp/` folder) and is never committed — this was
always a local-filesystem write, never a git operation, so the existing
NEVER rule is unaffected.

Updated `Project_Instructions_MCP.md` (removed the manual-write line under
Step 9; added a one-line note to Step 3 instead, since that's where it now
actually happens) and `M12_DriveProtocol.md` STEP 4b (marked AUTOMATED,
clarified it no longer executes as part of the WriteBack procedure at all
— it runs earlier, at session Step 3 — kept at this numbering only for
continuity with existing cross-references). M12 bumped Amendment 6→7.

**Test coverage added:** `tests/test_stage1/test_dispatcher_and_instruments.py`
— new `TestWriteInstrumentsJson` class (5 tests: correct shape, creates
missing parent directory, overwrites stale content, round-trips with
`load_instruments()`, and documents the empty-list/fallback interaction
between the two functions). `tests/test_mcp/test_run_computation.py` — 2
new tests confirming `_tool_run_computation()` calls
`write_instruments_json()` with exactly the §11.3 active set (not §11.4
candidates), and that a write failure is flagged rather than propagated
as a `HARD_STOP`.

**Side-effect risk found and fixed while adding coverage:** the existing
`no_network` fixtures in `test_run_computation.py` and
`test_pattern_b_pipeline.py` mock `FetchRegistry.fetch_all()` but, before
this fix, would have let every `_tool_run_computation()` call in both
files write straight through to the **real** `instruments.json` on disk —
it lives outside both the framework git repo and `test_pattern_b_pipeline`'s
`tmp_path` sandbox (keyed off `ADVISOR_MCP_DIR`, not `ADVISOR_FRAMEWORK_PATH`),
so nothing was isolating it. Added a `write_instruments_json` no-op patch to
both fixtures. Confirmed via the real file's mtime (unchanged, predates this
session) that no test run actually touched it before or after this fix.

`tools/validate_manifests.py`: 19/19 pass. Full suite (`not integration`):
658 passed, 60 deselected (+7 from this item's new tests, 0 regressions).

---

### ENG-13 — M19 trailing-window conditions have no tracking infrastructure
<!-- ITEM
  Status:    CLOSED
  Severity:  MEDIUM
  Category:  functional-gap
  Opened:    2026-06-17 (originally noted in Calibration_State.md v1.38 log entry)
  Closed:    2026-06-20
  Area:      python/advisor/analysis/thesis.py, trend.py (new), range_position.py (new),
             python/advisor/data/fetchers/yfinance_fetcher.py, fred_fetcher.py,
             python/advisor/data/m18_registry.py, python/advisor/mcp_server.py
  Related:   GAP-16, ENG-26 (split out of this item on closing it)
-->

**Description:** §13 conditions containing "sustained" / "consecutive" /
"rolling" / "trend" / "reversal" (6-12 week windows) were explicitly
skipped with a `quality_flag` rather than evaluated — there was no
historical-trend-tracking infrastructure. Documented behavior, not a
silent gap, but the underlying capability didn't exist.

**Suggested next step (original):** design a small rolling-window store
that `thesis.py` can query for "has X trended directionally over the
last N weeks."


**Resolution (2026-06-20):** Closed the price-series half of this item —
the half that didn't actually need persisted history. Key insight:
yfinance and FRED both serve arbitrary historical lookback windows in a
single request (already proven by the pre-existing VIX_30D_AVG/
VIX_90D_AVG/BROAD_EQUITY_TRAILING fetchers), so DBMF/SGOL/SIVR/MLPX/URA/
COPX's trend conditions don't need cross-session persistence — one fetch
per session covering the full window is sufficient.

New `analysis/trend.py`: pure functions on a `List[float]` of weekly
closes — `directional_trend()` (DBMF's own stated definition: net move
>= threshold% in one direction "without full reversal," operationalized
as never crossing back through the window's starting value),
`all_weeks_meet()` (every week satisfies a comparator — for "sustained <
threshold for N weeks" conditions), `decline_from_high_pct()` (for
"decline from most recent high" conditions), `mean_reversion_mode()`
(negation of `directional_trend` over the same window/threshold — an
earlier draft used a separate short trailing sub-window with the SAME
threshold as the full window, which is a real bug: a steady multi-week
trend routinely moves less than the materiality threshold within any
short sub-window of itself, so it would have been systematically
misclassified as "mean-reversion." Caught by the DBMF test suite before
shipping — see `test_two_trending_markets_satisfies_sustaining` in
`test_thesis.py`.)

9 new `*_TREND`/`NASDAQ_30D_RETURN` FetchSpecs registered in
`m18_registry.py` (DXY_TREND, BRENT_TREND, GOLD_TREND, SP500_TREND,
COPPER_TREND, URANIUM_TREND, COPX_PRICE_TREND, THREEFYTP10_TREND,
NASDAQ_30D_RETURN) — mirrors the existing VIX/broad-equity pattern in
`yfinance_fetcher.py` (`fetch_weekly_trend()`, `fetch_nasdaq_trailing()`)
and a new `_fetch_history()`/`_fetch_trend_series()` pair in
`fred_fetcher.py` for THREEFYTP10 (FRED's observations endpoint already
supports a date range — no new capability needed, just a multi-row
variant of the existing single-value fetch). All degrade gracefully
(quality_flag, no exception) on empty/illiquid series — same contract as
the rest of these files (e.g. URANIUM_SPOT's existing UX=F caveat).
`tests/test_stage1/test_fetchers.py::test_expected_spec_count` bumped
34→43 per its own "update when adding series" instruction.

`thesis.py`'s `_eval_trend()` dispatches each recognized §13 phrasing
(DBMF's 2-of-4 directional count and mean-reversion failure; SGOL/SIVR's
DXY-trend sustaining/failure and THREEFYTP10-sustained failure; SIVR's
COPX-decline failure; MLPX's BZUSD-sustained-low failure; URA/COPX's
stable-or-upward sustaining and sustained-decline failure) against the
new readings. Found and fixed while wiring this: `_evaluate_one_condition`
previously gated `_eval_trend` behind the same `_needs_trailing_window()`
keyword check used for flagging — but at least one real §13 condition
("DXY appreciation > 8% over 8 weeks") doesn't contain any of the five
skip keywords, so it was silently falling through to "no evaluator
recognizes condition" via a completely different path than the one this
item was meant to fix. `_eval_trend` is now attempted unconditionally
(cheap string matching); the keyword check is now used only to choose
which generic flag message to show when nothing recognizes a condition.

Also fixed in the same pass, found via the MAGS test: "Nasdaq 30d return
<= -10%" had no skip keyword AND no regex pattern in
`_eval_simple_numeric` — it was falling through to the generic
unrecognized-condition flag for an entirely separate reason (missing
data source, not missing trend logic). Added `NASDAQ_30D_RETURN` (point-
in-time, same pattern as `BROAD_EQUITY_TRAILING`) and a regex pattern for
it.

**Split out, not solved here — ENG-26:** MAGS's failure signal
"equity_scenario_divergence shifts to MODERATE for >= 2 consecutive
sessions" is a condition over a COMPUTED SIGNAL across sessions, not a
raw price series — no amount of yfinance/FRED history-fetching solves
"what was M14's divergence level last session," because nothing
persists it. `_eval_trend()` flags this specific case distinctly (cites
"ENG-26" in the quality_flag text) rather than lumping it in with the
now-solved price-trend conditions.

**Enabled directly by this fix — GAP-16:** the new trend infrastructure
(specifically `THREEFYTP10_TREND` and `DXY_TREND`) is reused as-is by
`analysis/range_position.py`, closing GAP-16's within-scenario IHP
sub-condition advisory in the same session. See GAP-16 in
`Calibration_State.md` §6 for that half.

**Bug found and fixed in `mcp_server.py` while adding test coverage:**
`_tool_apply_scoring()`'s M19 block was gated `if cal_for_tsc is not None
and readings_list:` — an empty readings list (e.g. every fetcher failed
this session) is falsy in Python, so the ENTIRE M19 block — including
`tsc_evaluations` and the new GAP-16 block — silently never ran, despite
both being specifically designed to degrade to UNKNOWN/"inconclusive"
with quality_flags on missing data, not crash. Caught via the existing
`no_network` test fixture (`FetchRegistry.fetch_all` mocked to return
`[]`) when adding `test_apply_scoring_has_range_position_advisories_key`
— no pre-existing test had ever asserted on `tsc_evaluations`'s presence,
so this had been silently true since M19 shipped (v1.37) without being
caught. Fixed: gate is now `if cal_for_tsc is not None:` only.

New tests: `tests/test_stage3/test_trend.py` (22, pure-function unit
tests on `analysis/trend.py`), `tests/test_stage3/test_thesis.py` (16 —
no dedicated test file existed for `thesis.py` before this at all; only
ever exercised via the live-data smoke test mentioned in the v1.37 log
entry, never via committed pytest), plus fetcher tests in
`test_stage1/test_yfinance_unit.py` (9) and `test_stage1/test_fred_fetcher.py`
(5), plus MCP-level shape tests in `test_mcp/test_run_computation.py` (2).
`tools/validate_manifests.py`: 19/19 pass (no module `.md` files needed
changes — the trailing-window limitation was never documented in
`M19_ThesisSustainingConditions.md` itself, only in `thesis.py`'s
docstring and this backlog). Full suite (`not integration`): 645 passed,
18 deselected, 0 regressions.

---

### ENG-27 — yfinance concurrent fetches return cross-contaminated *_TREND data
<!-- ITEM
  Status:    CLOSED
  Severity:  CRITICAL
  Category:  data-integrity
  Opened:    2026-06-20
  Closed:    2026-06-20
  Area:      python/advisor/data/fetchers/yfinance_fetcher.py
  Related:   ENG-13, GAP-16 (both consumers of the corrupted data)
-->

**Found:** during the first live session exercising ENG-13's trend infrastructure
and GAP-16's range-position advisory in anger, `DXY_TREND` and `BRENT_TREND`
came back from `advisor_run_computation()` with the EXACT same 8-value closes
array, and `COPPER_TREND`/`GOLD_TREND`/`URANIUM_TREND`/`SP500_TREND`/
`COPX_PRICE_TREND` all shared a SECOND identical array — values in the
$98–101 range, i.e. roughly that session's DXY spot price, not gold ($4,172),
copper ($6.34), uranium futures, the S&P (7,500), or COPX ($85.48). Only
`THREEFYTP10_TREND` (FRED-sourced, different client) was correct. Downstream
effect: GAP-16's `range_position_advisories` for SGOL/SIVR both came back
`"signal": "inconclusive"` / `"note": "no trend data available this session"`,
and the M19 DBMF mean-reversion failure condition fired (or didn't) on garbage
data — ENG-13/GAP-16 were both functionally dead on arrival for this reason
alone, despite both modules' own logic being correct (verified by re-reading
`trend.py`, `thesis.py`, `range_position.py` line by line — each correctly
reads the `*_TREND` `DataReading`s it's given; the bug is purely in what gets
written into those readings before they're handed over).

**Root cause:** `FetchRegistry.fetch_all()` (`data/fetch_registry.py`) runs
every registered `FetchSpec` concurrently via `ThreadPoolExecutor(max_workers=8)`.
Seven distinct specs all dispatch to `yfinance_fetcher.py` functions that call
`yf.download()`/`yf.Ticker()` with different symbols, all in the same batch.
yfinance's underlying session/cache machinery is not safe under concurrent
calls from multiple threads — a known class of issue with the library, not a
bug in this codebase's symbol mapping (`_SYMBOL_MAP`/`_TREND_SPECS` were
independently verified correct: each call site passes the right symbol).
Under load, results from one thread's `yf.download()` call were observed
leaking into another thread's return value.

**Fix:** added a module-level `_YF_LOCK = threading.Lock()` in
`yfinance_fetcher.py` and wrapped every yfinance network call site (
`fetch_holdings_prices`, `fetch_vix_history`, `fetch_broad_equity_trailing`,
`fetch_nasdaq_trailing`, `fetch_weekly_trend`, `fetch_yield_curve_partial`,
`fetch_instrument_history`, `_fetch_single`) in `with _YF_LOCK:`. This
serializes all yfinance calls relative to each other while leaving
`fred_fetcher.py`'s FRED-sourced fetches (different client, unaffected)
running concurrently in the same `ThreadPoolExecutor` batch — i.e. the fix is
scoped to the actually-unsafe library, not a wholesale removal of
`FetchRegistry`'s concurrency. Did not touch `fetch_registry.py` itself.

**Verification:** full suite (`not integration`): 645 passed, 0 regressions
(existing yfinance unit tests mock `yf.download` directly, so the lock wrapping
is transparent to them — no test changes needed). `tools/validate_manifests.py`:
19/19 (no module `.md` changes — pure Python fix, no spec-level behavior
change). Live re-verification of the actual cross-contamination fix (i.e.
confirming `DXY_TREND`/`BRENT_TREND`/etc. return genuinely distinct, correct
data under concurrent load) deferred to the next live session that calls
`advisor_run_computation()` — not practical to reproduce the race
deterministically in a unit test without mocking away the exact concurrency
this fix targets.

### ENG-28 — floor_account_weights_json double-JSON-encoding crashes floor checks
<!-- ITEM
  Status:    CLOSED
  Severity:  HIGH
  Category:  data-integrity
  Opened:    2026-06-20
  Closed:    2026-06-20
  Area:      python/advisor/mcp_server.py
  Related:   —
-->

**Found:** `CurrentHoldingsFloorCheck [3b]` and `PassiveMandateAbsentWarning`
both failed with `string indices must be integers, not 'str'` inside
`advisor_run_computation()`; the auto-triggered Step 6b re-check inside
`advisor_apply_scoring()` failed identically with no new arguments passed,
confirming the bug was server-side, not a one-off caused by how the calling
session formatted that one call.

**Root cause:** `_tool_run_computation()`'s `floor_account_weights_json`
parameter was typed `Optional[str]`, and the line
`floor_accounts = json.loads(floor_account_weights_json)` assumed exactly one
layer of JSON-string encoding. Some MCP calling layers re-stringify a
string-typed parameter that already looks like JSON — i.e. the value this
function received was itself the JSON encoding of a JSON string, not the
array. One `json.loads()` call only undoes the outer layer, yielding a
plain Python `str` (the inner, still-encoded array text) rather than a list.
`floor_accounts` then silently held a string with no exception raised (`
json.loads` succeeded — it just didn't produce a list). `check_all_floor_accounts()`
/ `passive_mandate_absent_warnings()` then did `for acct in floor_accounts:
acct["account_id"]`, which iterates a string character-by-character and
indexes each character with a string key — exactly the observed
`TypeError`.

**Fix:** added `_parse_floor_accounts()` in `mcp_server.py`: loops
`json.loads()` while the result is still a `str` (capped at 3 attempts, then
raises a clear `ValueError` rather than looping forever), validates the final
result is a list of `{account_id, weights}` dicts, and raises a clear error
on any other shape — so a genuinely malformed value now surfaces as a
flagged parse error (existing `except` handling in the call site), not a
silent wrong-type cache write. Also widened the parameter type from
`Optional[str]` to `Optional[Any]` (both in `_tool_run_computation()` and the
`@srv.tool()` wrapper) so a calling layer that DOES deliver a native list
isn't rejected by pydantic's string-only schema either — the function now
accepts whichever shape arrives and normalizes it, rather than assuming one
specific encoding convention.

**Verification:** full suite (`not integration`): 645 passed, 0 regressions
(no existing test called `_tool_run_computation` with a JSON-string
`floor_account_weights_json` directly, so nothing else depended on the old
single-`json.loads()` behavior). `tools/validate_manifests.py`: 19/19. Live
re-verification (passing a real floor-account payload and confirming Step
3b/6b run cleanly end-to-end) deferred to the next live session with
FLOOR_THEN_RETURN accounts populated.

### ENG-29 — thesis.py XAR Call-2 routing misses an alternate §13 phrasing
<!-- ITEM
  Status:    CLOSED
  Severity:  LOW
  Category:  hygiene
  Opened:    2026-06-20
  Closed:    2026-06-20
  Area:      python/advisor/analysis/thesis.py
  Related:   —
-->

**Found:** XAR's M19 evaluation correctly resolved to `FAILED` (the
`"de-escalation event"` phrasing matched and routed to
`M19_XAR_CONFLICT_GATE`, which fired as answered), but a SECOND §13 condition
— text: "Iran MOU signed AND Hormuz traffic confirmed reopened (T1
verified)" — fell through to the generic "no evaluator recognizes condition"
flag on the same evaluation. Same underlying judgment, different wording,
only one phrasing was recognized.

**Fix:** broadened the `_eval_call2()` match from
`if "de-escalation event" in cond:` to
`if "de-escalation event" in cond or "Hormuz traffic confirmed reopened" in cond:`
— both phrasings now route to the same `M19_XAR_CONFLICT_GATE` Call-2 answer.
No calibration text changes; per `thesis.py`'s own docstring, the module's
job is to own the mapping from recognized phrasings to live data, so the fix
belongs in code, not in rewriting §13's human-authored condition text to match
the code.

**Verification:** full suite (`not integration`): 645 passed, 0 regressions.
`tools/validate_manifests.py`: 19/19. **Audit note for a future session:** this
was found by inspection of one ticker's live output, not a systematic check
— §13's full condition-string set has not been cross-checked against every
recognized pattern in `thesis.py`. Worth a dedicated audit pass (read every
ticker's §13 entry, confirm each condition string matches some `_eval_*`
branch) rather than relying on phrasing mismatches surfacing one live session
at a time.

---

### ENG-32 — range_position.py conflated "flat" with "unavailable" trend data
<!-- ITEM
  Status:    CLOSED
  Severity:  LOW
  Category:  hygiene
  Opened:    2026-06-20
  Closed:    2026-06-20
  Area:      python/advisor/analysis/range_position.py
  Related:   ENG-27 (surfaced while live-verifying that fix), GAP-16
-->

**Found:** while live-verifying ENG-27's trend-data fix (after the MCP server
restart confirmed `DXY_TREND`/`BRENT_TREND`/etc. now return correct,
distinct data), GAP-16's SGOL/SIVR `range_position_advisories` STILL showed
`"signal": "inconclusive"` / `"note": "...no trend data available this
session."` — but `quality_flags` was empty, which only happens when the
underlying `*_TREND` reads succeeded. The data was present (DXY +2.6%/8wk,
THREEFYTP10 +0.6%/8wk that session) — it simply didn't clear the 5%
materiality threshold in `directional_trend()` in either direction.

**Root cause:** `_ihp_sub_conditions()` only appended to `drivers`/`signals`
on `d == "up"` or `d == "down"`; when `directional_trend()` correctly
returned `None` for a flat/non-directional move (data present, no edge
case, working as designed), neither branch fired and nothing was recorded.
The caller's fallback, `driver_text = "..." if drivers else "no trend data
available this session"`, then fired on an EMPTY `drivers` list regardless
of *why* it was empty — genuinely missing data and present-but-flat data
produced the identical, misleading message.

**Fix:** added an `else` branch under each of the two `if tp10/dxy is not
None:` blocks that appends an explicit "flat over the window... no lean"
driver note when data is available but non-directional. `drivers` is now
non-empty whenever data was fetched at all, so the "no trend data
available" fallback text is reserved for the case it actually describes.
`signal` classification logic (`overall = "inconclusive"` when `signals` is
empty) is unchanged — this was a message-text bug, not a misclassification
of the underlying advisory signal itself.

**Verification:** full suite (`not integration`): 645 passed, 0 regressions
both before and after this change (no existing test asserted on the exact
note text for the flat-data case, so nothing needed updating — a gap worth
closing: no dedicated `test_range_position.py` exists yet covering the
flat-vs-unavailable distinction). `tools/validate_manifests.py`: 19/19. **Live-verified** after a second
same-session restart: SGOL/SIVR `range_position_advisories` now read
"real yield (THREEFYTP10) flat over the window (move below 5% materiality
threshold) — no lean; DXY flat over the window (move below 5% materiality
threshold) — no lean" instead of the previous "no trend data available
this session" — `quality_flags` empty in both cases, confirming the data
was present all along and only the message was wrong.


---

### ENG-36 — dominant_directive() crashed on MAGS/MLPX/COPX (DirectiveCode.upper())
<!-- ITEM
  Status:    CLOSED
  Severity:  MEDIUM
  Category:  bug
  Opened:    2026-06-20
  Closed:    2026-06-20
  Area:      python/advisor/analysis/instruments.py
  Related:   discovered while running advisor_evaluate_allocation in-process
             to test ENG-33 and produce the floor-breach remediation numbers
-->

**Found:** `dominant_directive()` returned `"⚠ {ticker}: dominantDirective
failed — 'DirectiveCode' object has no attribute 'upper'"` for MAGS, MLPX,
and COPX, but not for DBMF, SGOL, SGOV, SIVR, VTIP, or AIPO held in the same
accounts.

**Root cause:** `DIRECTIVES: Dict[Tuple[str,str], DirectiveCode]`
(`portfolio/directives.py`) maps every (role, scenario) pair to a
`DirectiveCode` enum member — a plain `Enum`, not a `str` subclass.
`dominant_directive()`'s lookup `directives_table.get((role, scenario),
"HOLD")` returns either that enum (found) or the literal string `"HOLD"`
(the fallback default) — a mixed-type return depending on whether the
lookup hits. `_directive_direction(directive: str)` and `_most_conservative()`
both called `.upper()` directly on whatever they received, which only
works for the string fallback. Single-component tickers (DBMF, SGOL, ...)
and tickers whose material components happen to share an identical
directive (SIVR: both components ADD in scenario B) short-circuit before
ever reaching `.upper()`, so they never hit the bug. MAGS, MLPX, and COPX
all have two material (≥15% weight) components with genuinely *different*
directives in scenario B — exactly the case `dominant_directive()` exists
to resolve — so they hit `direction_sets = {_directive_direction(d) for d
in directives}`, calling `.upper()` on real `DirectiveCode` enum members
and crashing every time. The function worked in every trivial case and
crashed in precisely the substantive one.

**Fix:** both `_directive_direction()` and `_most_conservative()`'s inner
`_rank()` now normalize via `d.value if hasattr(d, "value") else d` before
calling `.upper()`, handling either a `DirectiveCode` enum or the plain-str
fallback.

**Verification:** full suite (`not integration`): 645 passed, 0 regressions.
`tools/validate_manifests.py`: 19/19. Live-verified with real
`Calibration_State.md` data (no network fetch needed — loaded via
`parse_calibration_state()` directly): `dominant_directive()` now resolves
cleanly for MAGS, MLPX, and COPX across all six scenarios with zero
errors, where it previously crashed on at least scenario B for all three.


---

### ENG-38 — advisor_write_back's `git push` could hang on an interactive credential prompt
<!-- ITEM
  Status:    CLOSED
  Severity:  HIGH
  Category:  infrastructure
  Opened:    2026-06-20
  Closed:    2026-06-20
  Area:      python/advisor/data/file_protocol.py (_git_commit)
  Related:   ENG-33 (split off from -- same ~4min symptom, separate cause)
-->

**Found:** `advisor_write_back` hung at the MCP client's ~4-minute call
ceiling. Unlike `advisor_evaluate_allocation` (ENG-33, a pure in-memory
computation), `write_back` does real file I/O and a git commit -- a much
more plausible place for a genuine block. Critically, when the operation
was eventually re-run in-process, it completed in well under a second,
*and* `git log` showed the ORIGINAL (timed-out) call had actually
completed and committed server-side all along -- the timeout was purely
client-side; the operation was simply slow to return, not stuck or
crashed.

**Root cause:** `_git_commit()`'s `git push origin master` call had no
timeout and no guard against git's interactive credential-prompt
behavior. If the MCP server's process doesn't have the same cached git
credentials an interactive shell session has (plausible -- Claude Desktop
spawns the MCP server as a child process, which may not inherit the same
credential-helper state as a fresh interactive terminal), `git push` can
block waiting for a credential prompt that has no TTY to display on and
will never be answered, until some far-future OS/network-level timeout
eventually fires.

**Fix:** `_git_commit()` now sets `GIT_TERMINAL_PROMPT=0` in the
subprocess environment for every git call (makes git fail fast instead of
prompting when no credential is cached, rather than hanging), adds an
explicit `timeout=` to each `subprocess.run()` call (60s for add/commit/
rev-parse, 30s specifically for push), and treats a failed or timed-out
push as **non-fatal**: the local commit has already succeeded by that
point (the part that matters for `Session_Log.md`/`Portfolio_State.md`
integrity), so the function logs a clear warning and still returns the
commit sha rather than losing that information by raising. Also added a
defensive `_with_timeout()` wrapper in `mcp_server.py` (see ENG-33) as a
second, independent line of defense around both `advisor_write_back` and
`advisor_evaluate_allocation`.

**Verification:** full suite (`not integration`): 645 passed, 0
regressions. `tools/validate_manifests.py`: 19/19. Isolated test against a
disposable temp git repo with no remote configured at all: `_git_commit()`
returned the local commit sha in 0.28s (logging the expected push-failure
warning) instead of hanging -- confirms the non-fatal-failure path works.
Did not (and safely could not) reproduce the original credential-prompt
hang itself in a test, since that requires the specific environment
mismatch between the MCP server's spawned process and an interactive
shell; `GIT_TERMINAL_PROMPT=0` is a standard, well-documented git
mechanism for exactly this class of problem, so the fix is sound by
inspection even without reproducing the original failure mode directly.


---

### ENG-39
<!-- ITEM
  Status:    CLOSED
  Severity:  MEDIUM
  Category:  bug
  Opened:    2026-06-21
  Closed:    2026-06-21
  Area:      python/advisor/analysis/range_position.py,
             python/advisor/data/fetchers/fred_fetcher.py,
             python/advisor/data/m18_registry.py
  Related:   GAP-16 (the IHP range-position advisory ENG-39 corrects),
             ENG-13 (introduced THREEFYTP10_TREND), ENG-32 (prior GAP-16
             text bug in the same module, different bug)
-->

**Found:** GAP-16's IHP (inflation_hedge_precious_metals) range-position
advisory (`analysis/range_position.py`) names one of its two sub-condition
drivers "real yield (THREEFYTP10)" and uses `THREEFYTP10_TREND`'s closes to
evaluate it. THREEFYTP10 is the Adrian-Crump-Moench 10Y *term premium* --
the compensation bond investors demand for duration risk -- not a real
yield. Identified 2026-06-21: term premium and real yield are not the same
variable and can move in different directions (e.g. term premium can rise
on pure auction-supply/duration-demand dynamics with no change in the
Fed's actual policy path), so the advisory's "rising real yield = headwind
for gold/silver" logic was being driven by the wrong number whenever the
two series diverge -- the textbook real-yield mechanism (real rates raise
the opportunity cost of holding a zero-yield asset like gold) was never
actually being measured.

**Fix:** Added a new FetchSpec, `REAL_YIELD_10Y_TREND` (`m18_registry.py`),
computed as DGS10 (10Y nominal Treasury yield) minus T10YIE (10Y breakeven
inflation) -- the standard Fisher-equation real yield -- both daily FRED
series. `fred_fetcher.py` gained `_fetch_history_with_dates()` (date-aware
fetch, needed to align two series before subtracting -- the existing
`_fetch_history()` returns bare values with no date to align on),
`_resample_weekly()` (collapses the daily diff series to one value per ISO
calendar week, matching the implicit weekly resampling the YFINANCE
`*_TREND` specs get from `yf.download(..., interval="1wk")`, so
`directional_trend()`'s materiality threshold means the same thing
regardless of data source), and `_fetch_real_yield_trend()` (the dispatcher
target, 8-week window to match `DXY_TREND`'s window since
`range_position.py` pairs the two as IHP's sub-condition drivers).
`range_position.py`'s `_ihp_sub_conditions()` now reads
`REAL_YIELD_10Y_TREND` instead of `THREEFYTP10_TREND`, with driver-text
labels corrected to "real yield (10Y, DGS10−T10YIE)". `THREEFYTP10_TREND`
remains registered unchanged -- M19's existing SGOL/SIVR "real yield
sustained > 2.0% for >= 4 weeks" §13 failure-signal text
(`analysis/thesis.py`) still names THREEFYTP10 explicitly and still
consumes it; that condition has the *same* underlying mislabeling bug, but
relabeling it is a `Calibration_State.md` §13 text change (calibration
content, not pure code) and was left out of scope for this engineering
session -- noted in both the FetchSpec docstrings and the
`Calibration_State.md` v1.44 log entry as a flagged follow-on.

`Calibration_State.md` updated to v1.44: §3 log entry added; §11 SGOL and
SIVR entries' GAP-16 driver descriptions corrected from "real yield
(THREEFYTP10)" to "real yield (REAL_YIELD_10Y_TREND = DGS10−T10YIE)".

**Verification:** full suite (`not integration`): 649 passed (was 645;
+4 new: 3 `TestRealYieldTrend` mocked-fetch unit tests in
`test_fred_fetcher.py` covering the computed-diff happy path, one-series-
missing, and non-overlapping-dates cases, +1 live-integration test gated
on `FRED_API_KEY` asserting the real yield lands near the commonly-cited
~1.5-2.5% range rather than THREEFYTP10's ~0.5-1.0% term-premium range --
confirms this is actually a different number, not THREEFYTP10 relabeled),
0 regressions. `test_fetchers.py::test_expected_spec_count` updated 43->44
for the new spec. `tests/test_stage3/test_range_position.py` updated
(mock reading key `THREEFYTP10_TREND` -> `REAL_YIELD_10Y_TREND` across all
4 affected tests) -- all 7 range_position tests still pass unchanged in
behavior (the tests assert on signal/driver-count outcomes, not the
specific spec_id, so this was a pure rename). `tools/validate_manifests.py`:
19/19.



### ENG-40
<!-- ITEM
  Status:    CLOSED
  Severity:  HIGH
  Category:  bug
  Opened:    2026-06-24
  Closed:    2026-06-24
  Area:      python/advisor/data/fetch_registry.py,
             python/advisor/data/fetchers/yfinance_fetcher.py
  Related:   ENG-27 (introduced _YF_LOCK for the 2026-06-20 yfinance
             thread-safety bug; this item adds a bound to that same lock)
-->

**Found:** `advisor_run_computation()` hung for 25+ minutes mid-session
(2026-06-24), unresponsive to the point Claude Desktop's MCP client gave
up waiting and reported the tool as dead. Diagnosis (Desktop Commander
process/network inspection on the live hung process, not a guess):
`fetch_registry.py`'s `fetch_all()` runs every M18 spec in a
`ThreadPoolExecutor` and waits on `as_completed(futures)` with no timeout
at all -- a single fetcher that never returns blocks the entire batch
forever. The hung worker thread was holding ~30 simultaneous TCP sockets in
CLOSE_WAIT against Yahoo Finance IPs (reverse-DNS confirmed one as
`*.ycpi.vip.deb.yahoo.com`), consistent with `yfinance` retrying an
illiquid/rate-limited symbol (`UX=F`, already flagged `⚠ unconfirmed/
illiquid` in `_SYMBOL_MAP`/`_TREND_SPECS`) without an overall bound. A
second, structural compounding factor: `yfinance_fetcher.py` serializes
*every* yfinance call behind one process-wide `_YF_LOCK` (ENG-27's
thread-safety fix), acquired via plain `with _YF_LOCK:` -- unbounded
`acquire()`. Even after `fetch_all()` itself returns, a thread stuck inside
one yfinance call holds that lock forever, so *every other* yfinance-sourced
spec would also block forever on lock acquisition for the remaining life of
the MCP server process -- a single bad symbol effectively bricks all market
data until the process is restarted.

**Fix:** `fetch_registry.py`'s `fetch_all()` now bounds each future to
`_FETCH_TIMEOUT_SECONDS` (25s) via `future.result(timeout=...)`, catching
`concurrent.futures.TimeoutError` and emitting a `FETCH_TIMEOUT`-flagged
reading for that spec instead of blocking -- consistent with the existing
"failures become flagged readings, never exceptions" contract, extended to
"and never block forever either." The `ThreadPoolExecutor` is shut down
with `wait=False` so a genuinely stuck worker thread doesn't also block
`fetch_all()`'s own return on the way out (`with ThreadPoolExecutor(...)`'s
implicit `shutdown(wait=True)` would have defeated the per-future timeout
entirely). `yfinance_fetcher.py` gained `_yf_lock_guard()`, a context
manager wrapping bounded `_YF_LOCK.acquire(timeout=20.0)`; a spec that can't
get the lock in time raises `TimeoutError` immediately rather than queuing
behind a stuck call indefinitely. All eight `with _YF_LOCK:` call sites
(`fetch_holdings_prices`, `fetch_vix_history`, `fetch_broad_equity_trailing`,
`fetch_nasdaq_trailing`, `fetch_weekly_trend`, `fetch_yield_curve_partial`,
`fetch_instrument_history`, `_fetch_single`) now use `_yf_lock_guard()`;
behavior is unchanged on the success path (same mutual exclusion), bounded
only on the failure path. `fred_fetcher.py` was checked and already passes
an explicit `timeout=10` on every `requests.get()` call -- no change needed
there; this was a yfinance-specific gap.

**Verification:** full suite (`not integration`): 744 passed, 0 regressions
(+5 new: `TestFetchAllTimeout` in `test_fetch_registry.py` -- a hung fetcher
produces a `FETCH_TIMEOUT` reading within the patched-down test bound and
does not block a concurrently-registered healthy spec; `TestYfLockGuard` in
`test_yfinance_unit.py` -- acquires immediately when free, raises
`TimeoutError` when held elsewhere beyond the timeout, releases the lock
even when the guarded body raises). One pre-existing, unrelated failure
confirmed independent of this fix via `git stash` A/B comparison against
the pre-ENG-40 working tree: `test_stage5/test_session.py::
test_pipeline_probabilities_all_at_or_above_floor` (a live-data integration
test) fails identically with or without this change (`Scenario C=2.8103%
below 3% floor`) -- reproduces deterministically off current
`Calibration_State.md`/`Session_Log.md` state plus today's live market
data plus `StubAIClient`'s canned scoring answers; flagged as a separate
follow-on (M03 floor-enforcement or test-strictness gap), not touched here.
`tools/validate_manifests.py`: 19/19 (unaffected, no manifest changes).

**Addendum (same session, 2026-06-24):** retrying the live MCP call after
the fix above still hung the full ~4 minutes. Root cause: a *second*,
separate unguarded yfinance call -- `mcp_server.py`'s `_tool_run_computation()`
Step 4b ("holdings 30d returns" for `RoleRepricingDivergence`) calls
`yfinance.download()` directly, bypassing `fetch_registry.py` and
`yfinance_fetcher.py`'s `_yf_lock_guard()` entirely; it was never covered
by either of this item's fixes. Separately, `advisor_run_computation`'s
tool registration was the one tool of the three *not* wrapped in this
file's own `_with_timeout()` defense (`advisor_evaluate_allocation` and
`advisor_write_back` already are, per ENG-33). Fixed both: extracted the
Step 4b call into `_fetch_holdings_30d_raw()`, called through a bounded
20s future (mirroring `_with_timeout()`'s pattern but Dict-returning, not
JSON-string-returning); wrapped `advisor_run_computation`'s registration in
`_with_timeout(..., 180.0)`, matching the other two tools. Verified: full
suite (`not integration`) 730 passed / 0 failures / 42 skipped / 19
deselected (live-data integration tests), `tools/validate_manifests.py`
19/19. `test_yfinance_unit.py` was separately lost to the same Google
Drive Cloud Files lock that blocked staging it earlier in this session --
recreated from the current `yfinance_fetcher.py` source (same test names/
coverage, not a byte-identical restore) once the lock cleared on a Claude
Desktop restart.



### ENG-45 — credit.py §1.3 CCC divergence OR-combines ratio + absolute modes (ratio false-positives)
**CLOSED** 2026-06-30 (LOW, bug). Full description and resolution below.
<!-- ITEM
  Status:    CLOSED
  Severity:  LOW
  Category:  bug
  Opened:    2026-06-30
  Closed:    2026-06-30
  Area:      python/advisor/analysis/credit.py (ccc_widening logic),
             python/advisor/config/calibration.py, python/advisor/types.py,
             Calibration_State.md §1.3
  Related:   Calibration_State.md §6 Batch A; M11
-->

**Found:** `credit.py` computed the CCC tail-first-widening monitoring flag
as `ccc_widening = ratio_met or absolute_met`. In a compressed regime the
ratio mode false-positives: measured 2026-06-30, CCC +29 bps/30d vs HY +8
bps/30d — ratio 3.62x trips the >=3x condition on a noise-level move, while
the absolute floor correctly does not fire (+29 << +200). Because the modes
were OR-combined, the flag fired spuriously whenever HY was near-flat
(denominator ~0), desensitizing the advisory flag over time.

**Fix:** added a new calibration-dated threshold, `ccc_ratio_min_bps` (value:
75 bps — the low end of the ~75-100 bps range suggested at audit time, chosen
so the existing genuine-divergence reading used in tests, +100 bps, still
fires). `ThresholdBlock` (`types.py`) gained the field, defaulted so none of
the five existing constructor call sites (test fixtures + the live parser)
needed updating. `calibration.py`'s `_parse_thresholds()` parses it from a
new Calibration_State.md §1.3 row ("Minimum absolute CCC move (ratio gate)"),
falling back to 75 if the row is absent. `credit.py`'s `ratio_met` now
additionally requires `ccc_vel_30d >= t.ccc_ratio_min_bps` — the ratio
condition and the absolute-move floor must both be satisfied for ratio mode
to fire; absolute mode (CCC >= +200 while composite +< 50) is untouched, as
specified (values 3x/+200/<50 unchanged, only the combination logic changed).

**Tests added** (`test_stage3/test_credit.py`): the exact 2026-06-30
compressed-regime reading (CCC+29/HY+8 -> does not fire); two genuine
divergences (CCC+150/HY+20 -> fires via ratio; CCC+250/HY+30 -> fires via
absolute). One pre-existing test (`test_ccc_tail_first_widening_ratio_mode`,
previously CCC+70/HY+20) was updated to the CCC+150/HY+20 fixture — 70 bps
sits below the new 75 bps gate, so it would have flipped from firing to not
firing under the fix; it was itself a smaller instance of the exact bug
being fixed here, not a case worth preserving as-is. `test_calibration_parser.py`
gained a parse test for the new field and its FIXTURE gained the matching row.

**Verification:** full suite `python3 -m pytest -q`: 773 passed / 46 skipped
(baseline, pre-fix) -> 776 passed / 46 skipped (post-fix, +3 new tests),
0 regressions. `tools/validate_manifests.py`: not run — no M0X module file
touched (Calibration_State.md is Layer 2, not a manifest-schema module).
Calibration_State.md §1.3 updated: new row added, "Ratio divergence" row's
note changed from "Enforcement pending" to "Enforcement done."


### ENG-44 — calculator_mcp not wired to the project + is a stub
**CLOSED** 2026-07-02 (MEDIUM, infrastructure). Full description and resolution below.
<!-- ITEM
  Status:    CLOSED
  Severity:  MEDIUM
  Category:  infrastructure
  Opened:    2026-06-30
  Closed:    2026-07-02
  Area:      G:\My Drive\dev\calculator_mcp.py; Claude Desktop MCP config
             (C:\Users\Evgeny\AppData\Roaming\Claude\claude_desktop_config.json);
             Project_Instructions_MCP.md
  Related:   README design principles 1 & 6 (single source of truth /
             all arithmetic auditable); framework NEVER-hand-compute-EV rule
-->

**Found:** `calculator_mcp.py` existed but was unregistered in Claude
Desktop and was a stub (`add`/`subtract`/`multiply`/`divide`/
`calculate_compound_interest` only) — no sanctioned, auditable path for
ad-hoc session/audit math (medians, percentiles, scenario-weighted EV).

**Fix:** `calculator_mcp.py` gained `median`, `percentile(values, p)`
(linear interpolation, numpy/Excel-PERCENTILE.INC convention),
`percentile_rank(values, value)` (inverse of `percentile()`), `mean`,
`stdev(values, sample=True)`, `pct_to_bps`/`bps_to_pct`, and
`scenario_weighted_ev(prob_vector, per_scenario_returns)` — the last one
matches Calibration_State.md's whole-number-percentage convention (not
fractions), validates prob/return key sets match, and warns (doesn't
raise) if probabilities don't sum to 100. A scope-boundary comment block
in the file itself (and now in `Project_Instructions_MCP.md`) documents
that this server is for ad-hoc/audit math only — not a second
implementation of `scenario_math.py`/`allocation.py`'s pipeline math.

Registered `calculator_mcp` in Claude Desktop's MCP config: `C:\Python\
python.exe` running `G:\My Drive\dev\calculator_mcp.py` directly (no
`cmd.exe` wrapper — same space-in-path handling as `financial-advisor`'s
entry). Requires a Claude Desktop restart to take effect — not yet
restarted/verified live as of this commit; verify the tool actually
appears in a fresh session before relying on it.

**Verified (direct-call smoke test, no MCP transport, mirrors
`market_data_mcp/test_server.py`'s approach):** all 8 new functions
against hand-calculated expected values, including `scenario_weighted_ev`'s
key-mismatch `ValueError` and non-100-sum `WARNING` paths. 15/15 checks
passed under both `C:\Python\python.exe` and confirmed the file has no
external dependency beyond `mcp` (no yfinance/pandas/requests needed).
`calculator_mcp.py` has no git repository of its own — noted, not fixed
this session (separate decision: whether it gets its own repo, joins an
existing one, or stays a loose file is a call for the client, not
something to assume).

**Acceptance met:** the calculator is wired and connectable; the tools an
audit needs (median/percentile/percentile_rank/scenario_weighted_ev) exist
with tested, documented contracts.


### ENG-42 — No MCP tool exposes FRED (or any) series-history fetch
**CLOSED** 2026-07-02 (MEDIUM, infrastructure). Full description and resolution below.
<!-- ITEM
  Status:    CLOSED
  Severity:  MEDIUM
  Category:  infrastructure
  Opened:    2026-06-30
  Closed:    2026-07-02
  Area:      python/advisor/data/fetchers/fred_fetcher.py; market_data_mcp/server.py
             (separate repo); Project_Instructions_MCP.md
  Related:   ENG-43; M18; M11; Calibration_State.md §6 Batch A
-->

**Found:** Historical FRED series data (trailing medians, percentiles,
velocity — everything a calibration audit needs) was reachable only
through underscore-private helpers in `fred_fetcher.py`. The Q2 2026 credit
audit had to hand-roll a scratch script against `_fetch_history_with_dates`
directly. Two MCP servers were wired (financial-advisor, market_data_mcp);
neither exposed series-history fetch.

**Fix — two parts, deliberately kept separate (2026-06-30 decision:
standalone port, not a cross-repo import):**

1. **fred_fetcher.py** (this repo): promoted `_fetch_history_with_dates` →
   `fetch_history_with_dates` (public), same behavior, contract now
   documented (oldest-first `(date, value)` tuples, `[]` if no key, raises
   on HTTP failure). Internal caller (`_fetch_real_yield_trend`) updated to
   match. New tests: `TestFetchHistoryWithDates` in `test_fred_fetcher.py`
   (5 cases: ordering, missing-value-marker skip, no-key, no-observations,
   HTTP-error propagation).

2. **market_data_mcp** (separate repo, `G:\My Drive\dev\market_data_mcp\`):
   added `fred_get_history(series_id, days|weeks, as_of?)` — a small,
   standalone port of the FRED REST fetch pattern, NOT an import from this
   repo (market_data_mcp had zero dependency on this repo before and stays
   that way by design; the two implementations may drift, an accepted cost
   of decoupling). Reads `FRED_API_KEY` from market_data_mcp's OWN `.env`
   (not this repo's) via `python-dotenv`; degrades gracefully with a clear
   error when absent. Returns FRED's native units, NOT bps-converted
   (documented explicitly, since `fred_fetcher.py`'s OAS series ARE
   bps-converted and this intentionally is not — a naming/unit trap worth
   flagging for future callers). `.gitignore` for that repo was also
   missing `.env` entirely — fixed before any secret could land there.
   New tests: `test_fred_history()` in `test_server.py` (days/weeks
   equivalence, `as_of` window, missing-days-and-weeks validation,
   graceful no-key degradation); `fred_get_history` added to the
   signature guard's tool list.

Documented both in `Project_Instructions_MCP.md`: `calculator_mcp`'s
scope boundary (shared with ENG-44) and, as a gap larger than this ticket
but adjacent to it, a full first-time write-up of `market_data_mcp`'s tool
surface (previously entirely undocumented there, including its 4
pre-existing tools) — README §9/§12's "update
Project_Instructions_MCP.md" rule is textually scoped to the
financial-advisor server's `mcp_server.py`, so `fred_get_history` alone
wouldn't have triggered it, but the ticket's own suggested-step text asked
for it regardless and it was a low-risk, high-value documentation gap to
close alongside this work.

**Verified:** `test_fred_fetcher.py` (18 passed, not counting 2 live
integration tests), `market_data_mcp/test_server.py` under BOTH
`C:\Python\python.exe` and the actual production interpreter Claude
Desktop uses (`D:\ai_financial_server\.venv\Scripts\python.exe`) — 91
passed / 0 failed each time, including `fred_get_history`'s graceful
degradation (no `.env` created yet in market_data_mcp — a live key would
need to be added there to exercise the happy path for real).

**Note — a Google Drive sync reliability issue surfaced during this work,
unrelated to the fix itself but worth recording:** mid-session, an already
-applied edit to `fred_fetcher.py` was found silently reverted to its
pre-edit (HEAD) content on disk, and separately a scratch commit-message
file vanished entirely, both self-resolving/re-appearing shortly after
(consistent with the already-documented "Google Drive locks a filename for
2-3 minutes after rapid successive edits" pattern, but a more severe
manifestation — actual content reversion, not just a lock timeout). Both
edits were re-verified and re-applied before committing; no data was lost,
but this is a real risk for any Desktop-Commander-driven edit in this
Drive-synced folder during a rapid-edit sequence — verify-after-write,
don't just trust the write confirmation, especially right after `git
stash`-style operations that touch the same file rapidly in succession.

**Acceptance met:** a calibration session can pull N days of any FRED
series via a tool call (`fred_get_history` in market_data_mcp), no scratch
script, covered by round-trip tests in both repos.


### ENG-43 — Credit-spread history truncated to 3y by FRED
**CLOSED** 2026-07-02 (MEDIUM, data-integrity). Full description and resolution below.
<!-- ITEM
  Status:    CLOSED
  Severity:  MEDIUM
  Category:  data-integrity
  Opened:    2026-06-30
  Closed:    2026-07-02
  Area:      python/advisor/data/credit_history_store.py (new);
             python/advisor/mcp_server.py (Step 3 wiring); CreditHistoryStore.json (new, repo root)
  Related:   ENG-42 (fetch_history_with_dates, which this consumes); Calibration_State.md Sec1 Batch A
-->

**Found:** FRED restricts the ICE BofA OAS series (BAMLH0A0HYM2 HY,
BAMLC0A0CM IG, BAMLH0A3HYC CCC) to a rolling 3-year window as of ~April
2026. Sec1 stress/recession deltas (sized for a full-cycle distribution)
and the Sec2 5-year hit-rate audit could no longer be verified or run
against FRED alone.

**Path (a) ruled out, confirmed empirically 2026-07-02:** FRED's ALFRED
archival layer does not carry these series at all. Querying with
ALFRED's own vintage mechanism (`realtime_start`/`vintage_dates` params)
returns FRED's own error: "the series does not exist in ALFRED but may
exist in FRED." The series' own metadata says "for more data, go to the
source" (ICE directly), not at FRED's own archival layer -- confirming
this is a licensing/redistribution constraint on current data, not a
revision-history gap ALFRED was ever built to solve.

**Path (c) chosen and implemented (client decision 2026-07-02):** a new
module, `credit_history_store.py`, accumulates the daily OAS readings FRED
does currently provide into `CreditHistoryStore.json` (repo root, git-
tracked) every session, so the window self-heals over roughly the next ~2
years even though FRED's own window never expands. Design:
- One JSON file, keyed by spec_id (HY_OAS/IG_OAS/CCC_OAS) -> {date: bps},
  plus a `last_updated` stamp. Values converted from FRED's native percent
  to this repo's bps convention on write.
- `update_credit_history_store()` re-fetches each series' full currently-
  visible FRED window (~1200 days) and merges any new/changed observations
  in -- not just "append today" -- so a run after a gap of missed sessions
  still catches up, and a date already captured is never lost even after
  it ages out of FRED's own live window.
- Gated to run at most once per calendar day (checked against
  `last_updated`) -- FRED is daily-resolution regardless, so more frequent
  runs would add API load and git-commit noise for zero additional
  coverage.
- Self-commits to git (add + commit, no push -- push happens via whatever
  later write-back naturally pushes) whenever new data actually merged in.
  `GIT_TERMINAL_PROMPT=0` + a 30s subprocess timeout, deliberately simple
  and low-risk for a background nice-to-have (contrast ENG-33/ENG-38, both
  real git-push hangs elsewhere in this codebase -- this avoids that whole
  class of failure by never pushing).
- Wired into `advisor_run_computation()` (Step 3), immediately after
  CreditSignal computation, fire-and-forget: any failure (network, parse,
  git) is caught internally and surfaced as an advisory flag, never a
  HARD_STOP -- same posture as `instruments.json`'s write at the same step.

**Seeded 2026-07-02:** `CreditHistoryStore.json` backfilled from FRED's
currently-visible window -- HY/IG/CCC, 2023-07-03 through 2026-07-01 (785
daily observations per series, matching the window FRED itself confirms).
This is the one-time historical baseline; `update_credit_history_store()`
extends it forward every session from here.

**Verified:** 13/13 new tests (`test_stage1/test_credit_history_store.py`)
-- store load/malformed-JSON/missing-key handling, once-per-day gating,
percent-to-bps merge conversion, aged-out-date preservation, zero-new-data
no-commit path, git-failure-caught-not-raised, fetch-exception-caught-not-
raised. Full suite: 777 passed (plus the 2 known ENG-46 date-boundary
failures, pre-existing and unrelated), 0 new regressions.

**What this does NOT close:** Sec1's full-cycle-distribution acceptance
criterion is a multi-year timeline, not something this ticket resolves on
its own -- even after ~2 years of accumulation the store will cover
~5 years total (3y FRED baseline + ~2y accumulated), which is enough for
the Sec2 hit-rate audit's stated need but does NOT itself guarantee
inclusion of a genuine stress/recession event (2008, 2020) the way the
original Sec1 deltas were sized against. The interim posture from the
2026-06-30 audit (retain HY/IG/CCC deltas unchanged, do not force them
down to what the truncated 3y window alone would imply) stands until a
future audit has enough accumulated history to actually re-verify them --
this ticket's job was building the mechanism that makes that future audit
possible at all, not performing it early on insufficient data.

**Acceptance met (the engineering deliverable, not the multi-year data
outcome):** a self-healing local history mechanism exists, is seeded, is
wired into every session, is tested, and requires no manual intervention
to keep accumulating going forward.


### ENG-46 — test_compaction.py hardcodes a specific quarter, breaks every real quarter boundary
**CLOSED** 2026-07-03 (LOW, testing). Full description and resolution below.
<!-- ITEM
  Status:    CLOSED
  Severity:  LOW
  Category:  testing
  Opened:    2026-07-01/02
  Closed:    2026-07-03
  Area:      python/tests/test_stage1/test_compaction.py
  Related:   ENG-41
-->

**Found:** `test_sec7_overflow_archives_oldest` and `test_sec8_overflow_archives_oldest`
both hardcoded `assert archive_fn == "Archive_2026Q2.md"` against the REAL
`datetime.date.today()` -- passed for as long as the suite happened to run
within Q2 2026, then failed the moment real wall-clock time crossed into Q3
(confirmed: this happened mid-session, between two full-suite runs on the
same day).

**Fix:** froze "today" in both tests via a small `_freeze_today(monkeypatch,
year, month, day)` helper -- a `datetime.date` subclass overriding
`today()`, monkeypatched onto the `datetime` module's own `date` attribute
(file_protocol.py does `import datetime`, not `from datetime import date`,
so patching the module attribute globally is the correct target; monkeypatch
reverts it automatically per-test). No `freezegun` dependency added --
confirmed not already a project dependency, and a two-test fix didn't
justify adding one. Chose option (a) from the original write-up (freeze
"today") over option (b) (compute the expected filename dynamically via
`_quarter_label()`) since (a) actually exercises the archive-naming logic
against a known input rather than just re-deriving the same computation the
code under test performs -- weaker "b" would pass even if `_quarter_label()`
itself had a bug.

**Verified:** `test_stage1/test_compaction.py` -- 24/24 passed (was 22/24).
Full suite: 801 passed / 46 skipped, 0 failures (previously 792 passed / 46
skipped / 2 known failures -- these two).

**Acceptance met:** both tests now pass regardless of which real calendar
quarter the suite happens to run in.


### ENG-47 — session.py Step4 signal-summary line crashes when spread_10y_2y is None
**CLOSED** 2026-07-03 (MEDIUM, bug). Full description and resolution below.
<!-- ITEM
  Status:    CLOSED
  Severity:  MEDIUM
  Category:  bug
  Opened:    2026-07-02
  Closed:    2026-07-03
  Area:      python/advisor/orchestrator/session.py
             (_step4_compute_signals line ~359, _render_briefing_context line ~514)
  Related:   ENG-40, ENG-41
-->

**Found:** a live FRED DGS10 read-timeout left `YieldCurveSignal.spread_10y_2y`
as `None`, and `_step4_compute_signals()`'s progress-summary f-string --
`f"10Y-2Y={yc.spread_10y_2y:.0f}bps ..."` -- crashed with `TypeError:
unsupported format string passed to NoneType.__format__` instead of degrading
gracefully. **A second, identical occurrence was found in the same file**
while fixing the first: `_render_briefing_context()`'s "YIELD CURVE" line
(the text that feeds AI Call 3) had the exact same unguarded pattern for
BOTH `spread_10y_2y` AND `spread_10y_3m` (confirmed via `FW_Types.md`/
`types.py`: both fields are `Optional[float]`, not just the one originally
found) -- the original write-up only caught the first instance because that's
the one the live-integration test happened to hit first.

**Fix:** added a small module-level helper, `_fmt_bps(value) -> str`,
returning `"n/a"` for `None` and `f"{value:.0f}bps"` otherwise. Applied at
all three call sites (Step 4's `yc_summary`, and both spreads in
`_render_briefing_context`'s YIELD CURVE line). This is a progress/log
line and part of AI Call 3's input context, not a computation result --
degrading to "n/a" is safe; no downstream signal math reads these strings.

**Verified:** new `test_stage5/test_yield_curve_none_formatting.py` (7
tests) -- `_fmt_bps()` unit tests (None/positive/negative/zero) plus
`_render_briefing_context()` exercised with both spreads None, one None,
and both present (regression guard: output must stay unchanged, "Nbps" not
"n/a", when data IS available). Full suite: 801 passed / 46 skipped, 0
failures -- and notably, zero live-network-related failures this run either
(the original crash needed a transient FRED timeout to surface at all, so a
clean run doesn't re-trigger it by itself; the new tests exercise the None
path deterministically instead of waiting for one).

**Acceptance met:** `_step4_compute_signals()` and
`_render_briefing_context()` never raise when either yield-curve spread is
`None` -- both degrade to an "n/a" placeholder.


### ENG-52 — V4: structured parseable entry format for Session_Log.md / Calibration_State.md / FRAMEWORK_BACKLOG.md
**CLOSED** 2026-07-06 (MEDIUM, hygiene). Full description and resolution below.
<!-- ITEM
  Status:    CLOSED
  Severity:  MEDIUM
  Category:  hygiene
  Opened:    2026-07-06
  Closed:    2026-07-06
  Area:      Session_Log.md §8; Calibration_State.md §3; config/session_log.py;
             config/calibration.py; rendering.py; types.py
  Related:   ENG-1 (prior §8 parser-compatibility fix — same failure class,
             this is prevention not repair), ENG-50, ENG-51, ENG-53, ENG-56
             (deferred remainder: pre-v1.46 §3 entries)
-->

**Found:** client observed that extracting a specific prior §8 entry's
`scenario_probabilities` required visually distinguishing between two
same-day 2026-07-03 entries in prose — no structural markup separated
machine-relevant fields (date, scenario_probabilities, session_type) from
the free-text driver narrative, and nothing disambiguated two entries
sharing an identical `date:` line. `Calibration_State.md` §3 had the same
underlying gap (confirmed live: two 2026-07-03 entries both tagged
`v1.51`, sharing both date AND version).

**Design decisions (client-confirmed 2026-07-06):** real YAML front-matter
(not a hand-rolled fenced key:value block), parsed via PyYAML (new
dependency — `PyYAML>=6.0` added to `requirements.txt`; already present
transitively in the venv, so no install was needed). Entry disambiguation
via a real wall-clock `entry_id` timestamp (`YYYY-MM-DDTHH:MM`), not a
sequence number or date+letter suffix. Both §8 and §3 in scope this
session; `FRAMEWORK_BACKLOG.md`'s existing `<!-- ITEM -->` convention left
untouched (already satisfies the same goal for this file).

**§8 (Session_Log.md) — full YAML entries:**
`config/session_log.py`'s `_parse_scenario_states()` rewritten from
field-by-field regex to `yaml.safe_load()` per `---`-delimited chunk
(deliberately NOT `yaml.safe_load_all()` across the whole region as one
stream — a single malformed or un-migrated entry must only drop itself,
not silently take down every entry parsed after it; this was caught and
fixed during implementation, not part of the original design). New
`entry_id`/`status` (`current`|`superseded`) fields added to
`SessionStateEntry`. `rendering.build_session_log_entry()` rewritten to
build a Python dict and `yaml.safe_dump()` it rather than hand-formatting
strings — a `_FlowDict` marker + isolated `_SessionLogDumper` subclass
keeps `scenario_probabilities` rendered as one compact flow-style line
while everything else uses block style. New
`rendering.mark_prior_entries_superseded()` flips a prior same-day
`status: current` entry to `superseded` as a targeted text patch (not a
full re-parse/re-dump, to avoid reformatting entries not being touched);
wired into both `mcp_server._tool_write_back()` (Pattern B) and
`orchestrator/session.py` (Pattern A) immediately before each appends its
new entry. Probabilities are now plain numbers (no `%` suffix — YAML
numerics round-trip exactly; the string convention was dropped).

The 3 live §8 entries were migrated to the new format using each entry's
**real git commit timestamp** for `entry_id` (`989b407a` /
2026-07-03T21:26 for the two same-commit recovered entries, `a194436b` /
2026-07-03T23:36 for the third) — not a fabricated time. The two earlier
same-day entries are marked `status: superseded`.

**§3 (Calibration_State.md) — front-matter header, narrative untouched:**
Different treatment from §8 by design: §3's free-text rationale (M16
4-layer analogues, dense technical prose) was never going to round-trip
cleanly as a YAML scalar, and nothing parses §3 programmatically today
(confirmed before starting), so there was no active bug to fix there —
only a hygiene opportunity. Adopted a small Jekyll-style YAML front-matter
block (`entry_id`/`date`/`version`/`category`, delimited by `---` — a
convention §3 didn't use before, so no collision risk) prepended before
each entry's **completely unchanged** existing text. New
`config/calibration.py:parse_calibration_log()` + `types.CalibrationLogEntry`
parse this format; deliberately NOT wired into `parse_calibration_state()`
(§3 was never part of that dataclass and still isn't — this parser is
hygiene/tooling, not a live computation path).

Migrated the 17 §3 entries from v1.46 through v1.62 (the entire live
section using the consistent "DATE (vX.XX) - Title." convention) —
`entry_id` for each is the real git commit timestamp that introduced it
(collected via `git log --format="%H|%ad|%s" -- Calibration_State.md`),
confirming along the way that `version` alone isn't actually a unique
key (two 2026-07-03 entries both tagged `v1.51` — DBMF and RSP — share
one commit/timestamp too, which is accurate: they were logged together).
Entries older than v1.46 (~line 836 onward) use at least one other,
inconsistent title-line convention (some with no version tag at all) —
deliberately NOT retrofitted this session; real transcription risk
outweighed the benefit given nothing depends on parsing them today.
Tracked as ENG-56, its own low-priority follow-up.

**Verified:** full suite run before any change (baseline): 799 passed / 46
skipped / 2 failed (both pre-existing and unrelated — `test_pipeline_probabilities_all_at_or_above_floor`,
already tracked as ENG-41, and an environment-dependent credentials test).
After migration: 3 test files had seed fixtures written in the old prose
format (`test_stage2/test_session_log_parser.py`, `test_rendering.py`,
`test_mcp/test_write_back_format.py`, `test_mcp/test_pattern_b_pipeline.py`,
`test_stage5/test_session.py`) — all rewritten to the new YAML format, plus
new coverage for `entry_id`/`status` round-tripping,
`mark_prior_entries_superseded()` (flip/ignore-other-dates/no-op/idempotent),
and per-entry parse independence (a malformed entry must only drop itself,
proven with a two-entry fixture: one broken, one well-formed after it).
Final full suite: **807 passed / 46 skipped / 2 failed** — the same two
pre-existing, unrelated failures as the baseline; zero new regressions.

**Acceptance met:** two same-day §8/§3 entries are now unambiguous via
`entry_id` (and `status` for §8) without reading narrative prose. ENG-51
and ENG-53 can now build on this format rather than migrating twice, per
the original sequencing request.


### ENG-51 — V4: split instrument classification (§11) into its own persistence entity
**CLOSED** 2026-07-06 (MEDIUM, architecture). Full description and resolution below.
<!-- ITEM
  Status:    CLOSED
  Severity:  MEDIUM
  Category:  architecture
  Opened:    2026-07-06
  Closed:    2026-07-06
  Area:      Calibration_State.md §11 -> Instrument_Classification.md (new file);
             config/calibration.py; data/file_protocol.py; mcp_server.py;
             orchestrator/session.py; __main__.py; M12_DriveProtocol.md;
             M15_InstrumentClassification.md; 00_INDEX.md; Project_Instructions_MCP.md
  Related:   ENG-50 (consumer of the resulting per-instrument state),
             ENG-52 (landed first per the original sequencing request, so this
             file was created in the improved format from day one)
-->

**Found:** motivated by ENG-50 — the planned trend/rotation layer needs to
read/write per-instrument state without every read/write touching credit
thresholds, the return table, or anything else living in
Calibration_State.md. §11 (role registry + instrument classification
table, ~539 lines) was one section inside one 2,697-line file.

**Design:** extracted §11 verbatim (lines 1881-2419, boundary-detected via
the heading strings themselves rather than hardcoded line numbers) into
`Instrument_Classification.md`, keeping the exact same `§11.1-§11.4`
heading numbering so every existing "§11.x" cross-reference in the
framework still resolves. `Calibration_State.md` §11 was replaced with a
short pointer stub (not renumbered — §12/§13 keep their existing numbers).

Turned out to require zero changes to `_parse_role_registry()` /
`_parse_instruments()` in `config/calibration.py`: both already located
their content via string markers (`### 11.1`/`"## Section 11"`) rather
than a hardcoded document structure, so calling them on the new file's
text just works. Only `parse_calibration_state()`'s signature changed —
gained an optional `instrument_classification_text` parameter (defaults
to `None`, falling back to parsing roles/instruments from `text` itself
for backward compatibility with any fixture that still embeds §11 in one
blob). All 4 production call sites (`mcp_server.py`, `orchestrator/session.py`,
`__main__.py` x2) were updated to fetch and pass the new file explicitly
via a new `read_instrument_classification()` in `file_protocol.py`.
`CalibrationState.roles`/`.instruments` are unchanged in shape —
`classifyInstrument()`, `ValidateClassifications()`, and
`blendedScenarioReturn()` needed no changes, per the original ask.

**Framework spec files updated to match** (M12_DriveProtocol.md Amendment
8→9, M15_InstrumentClassification.md v1.2→1.3, 00_INDEX.md, and the repo
copy of Project_Instructions_MCP.md — all "§11 lives in Calibration_State.md"
references corrected to point at the new file). **Note for the client:**
these are Project Knowledge attachments in this Claude Project, not
live-synced from git — the repo copies are now correct, but re-uploading
them to Project Knowledge is a separate manual step if this Project's
attachments are meant to stay current. While doing this pass, found that
whatever backs `project_knowledge_search` is already stale relative to
the repo in more ways than this change touches (e.g. M12's on-disk
version is Amendment 8/9 with `read_calibration_state()`-based pseudo-code;
project_knowledge_search returned an older `fetchCalibrationState()`/
`readFrameworkFile()` version; M15 was v1.0 there vs v1.2 on disk) — worth
a dedicated look separate from this item.

**Verified:** 4 test fixtures using an isolated tmp framework directory
were identified via `ADVISOR_FRAMEWORK_PATH` usage; only
`test_mcp/test_pattern_b_pipeline.py`'s `pipeline_dir` fixture actually
exercises the full read path (the others either don't call
`parse_calibration_state()` at all or don't override the framework path),
and was updated to also seed a copy of the real `Instrument_Classification.md`
alongside `Calibration_State.md`. Full suite: 807 passed / 46 skipped / 2
failed — same two pre-existing, unrelated failures as every run this
session — zero new regressions.

**Acceptance met:** §11 lives in its own file; role-registry logic is
byte-for-byte unchanged; every existing "§11.x" reference in the framework
still resolves.
