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

**Last updated:** 2026-06-17

## Index

| ID | Status | Severity | Category | Title |
|---|---|---|---|---|
| ENG-1 | CLOSED | CRITICAL | data-integrity | §8 write-back format incompatible with parser |
| ENG-2 | OPEN | HIGH | architecture | Module necessity review (M01–M19) |
| ENG-3 | OPEN | HIGH | architecture | Pattern A / Pattern B duplication & convergence decision |
| ENG-4 | OPEN | MEDIUM | architecture | Stage 5 (Pattern A) incomplete plumbing |
| ENG-5 | OPEN | HIGH | hygiene | Compaction cadence mismatch (Calibration_State §3, Session_Log §8) |
| ENG-6 | OPEN | MEDIUM | hygiene | §6 First-Audit Checklist accumulates stale content |
| ENG-7 | OPEN | MEDIUM | hygiene | §11 stores computed EV math redundantly |
| ENG-8 | OPEN | LOW | hygiene | Orphaned exited-instrument entries not pruned |
| ENG-9 | OPEN | LOW | hygiene | §13 preamble mixes methodology with live data |
| ENG-10 | OPEN | HIGH | testing | No test coverage for advisor_run_computation / advisor_apply_scoring |
| ENG-11 | OPEN | HIGH | testing | No Pattern-B end-to-end pipeline test |
| ENG-12 | OPEN | MEDIUM | testing | Tests assert against live, not snapshotted, framework files |
| ENG-13 | OPEN | MEDIUM | functional-gap | M19 trailing-window conditions have no tracking infrastructure |
| ENG-14 | OPEN | LOW | documentation | GAP-11 label has no description anywhere |
| ENG-15 | OPEN | LOW | process | No CI — test suite is run manually |

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
  Status:    OPEN
  Severity:  HIGH
  Category:  architecture
  Opened:    2026-06-17
  Area:      M01_SourceIntegrity.md – M19_ThesisSustainingConditions.md (all 19)
  Related:   ENG-3
-->

**Description:** The M01–M19 pseudo-code module files predate the Python/MCP
implementation. Per the framework owner (2026-06-17): "this is a python mcp
server, essentially, the pseudo-code modules are the artifacts of the old
version, at least some of them... I will be planning work to review the
necessity of having this many modules now that the mcp part of the
framework is implemented." This is the framework owner's own planned
review, recorded here as a flagged open question — no recommendation is
made in this entry about which modules to retain, merge, or retire, since
that review hasn't happened yet.

**Why it matters:** Every module file still gets loaded as Project
Knowledge in every advisory session (00_INDEX.md FILE_MAP) regardless of
whether its logic is now fully owned by `python/advisor/`. Some modules are
genuinely still doing the job only an LLM can do (M02 qualitative
interpretation, M06 advisory judgment); others may now be near-total
restatements of what `python/advisor/analysis/*.py` already implements and
enforces in code. Until the review happens, nobody can say which bucket a
given module falls into, which makes "should I edit the .md file or the
.py file" a real source of confusion for both advisory and coding sessions.

**Suggested approach (not a decision):** for each module, classify as
(a) AI-judgment-only — keep as the authoritative source, Python has no
equivalent; (b) spec-for-Python — Python is the executable truth, the .md
file is documentation of intent and could likely shrink substantially;
(c) fully superseded — logic, thresholds, and registries have moved
entirely into `python/advisor/` and CALIBRATION_STATE, and the .md file may
be retireable or mergeable into 00_INDEX.md. See README.md → "Pseudo-code
vs Python" for the current best understanding of this split, pending the
actual review.

### ENG-3 — Pattern A / Pattern B duplication & convergence decision
<!-- ITEM
  Status:    OPEN
  Severity:  HIGH
  Category:  architecture
  Opened:    2026-06-17
  Area:      python/advisor/orchestrator/session.py, python/advisor/mcp_server.py
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


### ENG-4 — Stage 5 (Pattern A) incomplete plumbing
<!-- ITEM
  Status:    OPEN
  Severity:  MEDIUM
  Category:  architecture
  Opened:    2026-06-17
  Area:      python/advisor/orchestrator/context.py, session.py
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

### ENG-5 — Compaction cadence mismatch (Calibration_State §3, Session_Log §8)
<!-- ITEM
  Status:    OPEN
  Severity:  HIGH
  Category:  hygiene
  Opened:    2026-06-17
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


### ENG-6 — §6 First-Audit Checklist accumulates stale content
<!-- ITEM
  Status:    OPEN
  Severity:  MEDIUM
  Category:  hygiene
  Opened:    2026-06-17
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


### ENG-7 — §11 stores computed EV math redundantly
<!-- ITEM
  Status:    OPEN
  Severity:  MEDIUM
  Category:  hygiene
  Opened:    2026-06-17
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

### ENG-8 — Orphaned exited-instrument entries not pruned
<!-- ITEM
  Status:    OPEN
  Severity:  LOW
  Category:  hygiene
  Opened:    2026-06-17
  Area:      Calibration_State.md §11.3
  Related:   ENG-5, ENG-7
-->

**Description:** PAVE still has a full §11.3 entry even though §3 logs it
as exited and dropped twice (v1.33, reconfirmed v1.37). Nobody deleted
the classification entry when the position was closed.

**Suggested next step:** add a NEVER rule — an exited instrument loses
its §11.3 entry in the same session/version bump that logs the exit, not
on a future cleanup pass. PAVE is the concrete example to fix first.


### ENG-9 — §13 preamble mixes methodology with live data
<!-- ITEM
  Status:    OPEN
  Severity:  LOW
  Category:  hygiene
  Opened:    2026-06-17
  Area:      Calibration_State.md §13, M19_ThesisSustainingConditions.md
  Related:   ENG-2
-->

**Description:** §13's status-taxonomy and briefing-suppression-behavior
explanation is methodology ("why/how"), not a calibration-dated value
("what now"). It belongs in M19_ThesisSustainingConditions.md.

**Suggested next step:** move the explanatory preamble into M19.md;
leave only the per-ticker data blocks in §13. Low priority — §13's
per-entry structure is otherwise appropriately lean (unlike §3/§6/§11).

### ENG-10 — No test coverage for advisor_run_computation / advisor_apply_scoring
<!-- ITEM
  Status:    OPEN
  Severity:  HIGH
  Category:  testing
  Opened:    2026-06-17
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


### ENG-11 — No Pattern-B end-to-end pipeline test
<!-- ITEM
  Status:    OPEN
  Severity:  HIGH
  Category:  testing
  Opened:    2026-06-17
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
4. If it touches a tool signature, the M05 sequence, or anything
   Project_Instructions_MCP.md describes, cross-check that file per the
   rule in README.md → "Keeping Project_Instructions_MCP.md in sync."
