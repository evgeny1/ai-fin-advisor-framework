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

**Last updated:** 2026-07-06, coding session (ENG-52 CLOSED — Session_Log.md
§8 and Calibration_State.md §3 entries now use real YAML front-matter with
an `entry_id` real-timestamp field and, for §8, a `status: current|superseded`
field, fixing the exact same-day-entry disambiguation gap that motivated the
item; PyYAML added as a dependency; parser rewritten for per-entry-independent
parsing so one malformed entry can't silently drop every entry after it;
3 live §8 entries and the 17 live §3 entries from v1.46–v1.62 migrated using
real git-commit timestamps, not fabricated ones; pre-v1.46 §3 entries
deliberately deferred as ENG-56 — inconsistent legacy title-line conventions
made automated retrofitting a real transcription risk. Full suite: 807
passed / 46 skipped / 2 failed, same two pre-existing unrelated failures as
baseline, zero new regressions. Full writeup in FRAMEWORK_BACKLOG_ARCHIVE.md.)
Prior: 2026-07-06, design session (ENG-50 through ENG-55 OPENED — V4 architecture proposal: additive trend/rotation signal layer to be run in shadow mode against the existing scenario/EV engine before any conflict-resolution authority is assigned; instrument classification split from Calibration_State.md into its own persistence entity; structured parseable entry format for Session_Log.md/Calibration_State.md/FRAMEWORK_BACKLOG.md; calendar-age archival for Session_Log.md; FINRA margin-debt data source; relative-strength formula + peer-basket definition explicitly deferred to its own dedicated session (ENG-55) rather than decided ad hoc. Full session hand-off in dev hand-off note, 2026-07-06. Prior: 2026-07-03, coding session (ENG-46 CLOSED — froze "today" in the two quarter-boundary-hardcoded compaction tests; ENG-47 CLOSED — added _fmt_bps() None-safe formatting, fixed at both call sites including a second occurrence found while fixing the first. Full suite: 801 passed / 46 skipped, 0 failures. Full writeups in FRAMEWORK_BACKLOG_ARCHIVE.md.) Prior: 2026-07-02, coding session (ENG-42 CLOSED — fred_get_history tool + promoted fetch_history_with_dates; ENG-43 CLOSED — ALFRED ruled out empirically, path (c) local self-healing CreditHistoryStore.json implemented, seeded, and wired into advisor_run_computation(); ENG-44 CLOSED — calculator_mcp wired into Claude Desktop's MCP config and documented; ENG-46/47 discovered and logged, not fixed. Full writeups in FRAMEWORK_BACKLOG_ARCHIVE.md.) Prior: 2026-06-30, same-day follow-on coding session (ENG-45 CLOSED — credit.py ccc_widening ratio mode gated behind a new `ccc_ratio_min_bps` calibration threshold (75 bps); full writeup in FRAMEWORK_BACKLOG_ARCHIVE.md). Prior, same day (Q2 audit — opened ENG-42/43/44/45: FRED series-history not exposed via any MCP tool; FRED 3y OAS truncation blocks §1 delta verification + §2 5y hit-rate audit; calculator_mcp not wired and still a stub; credit.py §1.3 CCC divergence ratio-mode OR false-positive found live (CCC+29/HY+8 bps → 3.62x). Full bodies in Part 1.) Prior: 2026-06-25 (ENG-33: live-tested the flattened-parameter fix after a clean Claude Desktop restart and a freshly-rebuilt cache — advisor_evaluate_allocation still hung the full ~4 minutes, and the transport log confirms zero occurrences of the tool name anywhere, not just no tools/call entry. This rules out the $ref/$defs hypothesis as cleanly as the prior two attempts ruled out their own. Three independent hypotheses now falsified across two sessions; root cause confirmed client-side, outside this codebase's reach. Flattened account_profile kept regardless as a genuine cleanup; in-process bypass remains the standing workaround — see full ENG-33 entry below). Prior, same day: ENG-40 opened and closed same session — fetch_all() had no per-spec timeout and the shared yfinance lock had no bound on acquisition, so one stuck/illiquid symbol (UX=F) could hang advisor_run_computation() for 25+ minutes and then permanently block every later yfinance fetch for the rest of the MCP server process's life; fixed with a per-future timeout in fetch_registry.py and a bounded _yf_lock_guard() in yfinance_fetcher.py; full writeup in FRAMEWORK_BACKLOG_ARCHIVE.md. Prior: 2026-06-21 (ENG-39 opened and closed same session — GAP-16's IHP range-position advisory was using THREEFYTP10 (term premium) mislabeled as "real yield"; replaced with a computed REAL_YIELD_10Y_TREND series; full writeup in FRAMEWORK_BACKLOG_ARCHIVE.md). Prior: 2026-06-20/21 (ENG-38 closed — write_back's git-push hang root-caused and fixed via GIT_TERMINAL_PROMPT=0 + timeouts + non-fatal push failure; ENG-27/28/29/32/36 also closed earlier this session — yfinance thread-safety bug, floor_account_weights_json double-encoding crash, thesis.py XAR phrasing gap, GAP-16 flat-vs-unavailable note bug, dominant_directive() DirectiveCode.upper() crash; ENG-30/31/34/35/37 opened — DBMF/AIPO/XAR data-source gaps, run_computation latency, recalibration_sequence anchor heuristic; all found/fixed live across one extended session)

Closed items: full descriptions and resolutions live in `FRAMEWORK_BACKLOG_ARCHIVE.md`, indexed by the same ENG-N numbers. The Index table below still lists every item (open and closed) for a complete status overview; only OPEN items get full bodies in Part 1 below it -- closed items get a one-line stub pointing to the archive.

## Index

| ID | Status | Severity | Category | Title |
|---|---|---|---|---|
| ENG-48 | OPEN | HIGH | bug | advisor_write_back's 90s safety-timeout races its own actual completion time — reports TIMEOUT while succeeding server-side |
| ENG-49 | OPEN | HIGH | bug | advisor_write_back TIMEOUT with a genuinely incomplete server-side operation — files+archive rendered and written, but git add/commit never ran, distinct from ENG-48's "actually succeeded" pattern |
| ENG-50 | OPEN | HIGH | architecture | V4: Trend/Rotation Signal Layer — deterministic price/relative-strength module, additive to scenario engine, shadow-mode trial before any authority decision |
| ENG-51 | OPEN | MEDIUM | architecture | V4: split instrument classification (§11) out of Calibration_State.md into its own persistence entity |
| ENG-52 | CLOSED | MEDIUM | hygiene | V4: structured parseable entry format (front-matter block) for Session_Log.md, Calibration_State.md, FRAMEWORK_BACKLOG.md |
| ENG-53 | OPEN | MEDIUM | architecture | V4: calendar-age archival mechanism for Session_Log.md (and candidate extension to other growing files) |
| ENG-54 | OPEN | MEDIUM | infrastructure | V4: FINRA margin debt series has no M18 DATA_REGISTRY_ENTRY or fetch path |
| ENG-55 | OPEN | HIGH | functional-gap | V4: relative-strength formula + peer-basket definition for trend layer — needs its own dedicated session, real judgment calls involved |
| ENG-56 | OPEN | LOW | hygiene | Retrofit ENG-52 front-matter onto pre-v1.46 §3 entries (inconsistent legacy title-line conventions) |
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
| ENG-42 | CLOSED | MEDIUM | infrastructure | No MCP tool (either server) exposes FRED/series-history fetch — calibration audits hand-roll scratch scripts against fred_fetcher's underscore-private helpers |
| ENG-43 | CLOSED | MEDIUM | data-integrity | FRED truncated ICE BofA OAS series to a rolling 3y window (~Apr 2026) — fixed via a self-healing local history store (path c); see ARCHIVE for the multi-year data-outcome caveat |
| ENG-44 | CLOSED | MEDIUM | infrastructure | calculator_mcp (dev folder) not wired to the project and is a stub — no sanctioned/auditable calc path for ad-hoc audit math (median/percentile/EV) |
| ENG-45 | CLOSED | LOW | bug | credit.py §1.3 CCC divergence OR-combines ratio+absolute modes — ratio mode false-positives in compressed regimes (fired 3.62x on CCC+29/HY+8 bps, 2026-06-30) |
| ENG-46 | CLOSED | LOW | testing | test_compaction.py hardcodes "Archive_2026Q2.md" without freezing datetime.date.today() — breaks every real quarter boundary; tripped mid-session 2026-07-01/02 |
| ENG-47 | CLOSED | MEDIUM | bug | session.py Step4 signal-summary f-string crashes (TypeError on NoneType.__format__) when yield_curve_signal.spread_10y_2y is None — exposed by a live FRED timeout, not just a test flake |

---

## Part 1 — Engineering Items

### ENG-48 — advisor_write_back's 90s safety-timeout races its own actual completion time
<!-- ITEM
Status:    OPEN
Severity:  HIGH
Category:  bug
Opened:    2026-07-03
Area:      python/advisor/mcp_server.py — _tool_write_back()
Related:   ENG-33 (different mechanism — see Description), ENG-38 (git-push timeout,
           likely upstream of this one)
-->

**Description:** During one advisory session, `advisor_write_back()` was called
four times. Two returned `{"status": "TIMEOUT", "error": "_tool_write_back
exceeded its 90s safety timeout without returning..."}` to Claude. Both were
initially treated as failures and retried/abandoned per the tool's own advice
("check git log for a new commit before retrying"). Checking `.git/logs/HEAD`
confirmed no commit had landed either time — consistent with genuine failure.

Much later in the same session, `git status` unexpectedly showed uncommitted
modifications to `Session_Log.md` and `Portfolio_State.md`, plus an untracked
`Archive_2026Q3.md` — despite neither reported TIMEOUT having produced a
commit. Reading both modified files found two COMPLETE, well-formed §8
entries with correct scenario probabilities, primary_driver, open_triggers,
open_decisions, and next_session_flags — matching the content of both
"failed" calls exactly. Nothing was garbled or partial.

Cross-referencing `mcp-server-financial-advisor.log` (Claude Desktop's MCP
transport log — request/response pairs are timestamped even though tool
names/params are redacted) confirms the mechanism precisely:

| Call | Client request sent | Server response logged | Delta |
|---|---|---|---|
| 1st write_back TIMEOUT | 20:13:23.115Z | 20:14:53.136Z | **90.021s** |
| 2nd write_back TIMEOUT | 20:19:16.022Z | 20:20:46.040Z | **90.018s** |

Both deltas land right at the "90s safety timeout" named in the tool's own
error string — not a client-transport hang (contrast ENG-33, where the
transport log showed the tool name occurring ZERO times, meaning the request
never reached the server at all). Here the request DID reach the server, the
server DID complete the full operation (render, write both files, git
add+commit — no push landed either time, worth checking separately whether
that's ENG-38 resurfacing or a distinct third step), and the response WAS
sent — it just arrived at approximately the same instant the tool's own
internal safety-timeout gave up waiting on it, so Claude's tool-call layer
reported failure a beat before (or during) an actual success.

Net effect: a client-visible "TIMEOUT" that is frequently (possibly always,
for this specific tool) actually a success delayed to just past the
watchdog's own deadline. The uncommitted files sat unrecovered for the
remainder of the session until manually found and committed by hand.

**Suggested next step:** the 90s figure is suspiciously tight against
observed real completion time (both instances landed at ~90.02s, not spread
across a wide range) — profile `_tool_write_back()`'s actual wall-clock
breakdown (render time vs. git add vs. git commit vs. git push attempt) to
find what's consistently taking it right up to the wire. Two independent
fixes, either sufficient alone: (a) raise the safety-timeout comfortably
above observed worst-case completion time, or (b) have the safety-timeout
handler check whether the commit actually landed (a fast git call) before
returning TIMEOUT, and return the real success result if so instead of a
false failure. (b) is more robust against the timeout ever being too tight
again. Also worth deciding deliberately: should `git push` be attempted
synchronously inside this call at all, given ENG-38 already made push
failures non-fatal — if push is the slow step, making it fire-and-forget
(commit synchronously, push in a background thread, log push failures
separately) would shorten the critical path without changing write
guarantees for the two files that actually matter to session continuity.

### ENG-49 — advisor_write_back TIMEOUT with genuinely incomplete server-side work
<!-- ITEM
Status:    OPEN
Severity:  HIGH
Category:  bug
Opened:    2026-07-03
Area:      python/advisor/mcp_server.py — _tool_write_back()
Related:   ENG-48 (same symptom, different mechanism — see Description)
-->

**Description:** A third `advisor_write_back()` TIMEOUT this same day did
NOT match the ENG-48 pattern. Per ENG-48's own advice, checked `git log`
before retrying — no new commit, consistent with either genuine failure or
an ENG-48-style race. `git status --short` showed the real state:
`Session_Log.md` and `Portfolio_State.md` modified, plus a NEW untracked
`Archive_2026Q3.md` (an automatic archive-rotation side effect of the
render step, not previously seen in the ENG-48 writeup). `git diff --stat`
and reading the modified files confirmed a single, complete, well-formed §8
entry — not truncated, not duplicated.

So: render + file-write + archive-rotation all completed. But unlike
ENG-48 (where `git add`+`git commit` also completed, just reported late),
here the commit step genuinely never ran — no new commit existed at any
point, checked repeatedly over several minutes. This is a different failure
boundary than ENG-48: that one is "the response raced the deadline after
full completion including commit"; this one is "the operation was killed
or errored out somewhere between file-write and git add, before commit."

Recovered by hand: `git add` the three files + `git commit -F` a message
file (inline `-m` with parentheses/colons in the message got mangled by
PowerShell's argument parsing — not a `advisor_write_back` bug, a Desktop
Commander/PowerShell quoting issue, but worth remembering as its own
gotcha) + `git push`. No data was lost; the fix was purely completing the
git steps the tool itself should have finished.

**Suggested next step:** instrument `_tool_write_back()` to log (or at
least make inspectable) which internal step it reached before returning —
render / file-write / archive-rotation / git-add / git-commit / git-push —
so a future TIMEOUT can be triaged from the log directly instead of
requiring a manual `git status`+`git diff` forensic pass every time. Once
that instrumentation exists, ENG-48's fix (b) (check-before-returning-
TIMEOUT) should specifically verify the commit landed, not just infer
success from the timeout racing a known-good completion window — this
session is proof those are two genuinely different failure modes needing
one shared diagnostic, not one shared assumption.

### ENG-50 — V4: Trend/Rotation Signal Layer (design + shadow-mode trial)
<!-- ITEM
Status:    OPEN
Severity:  HIGH
Category:  architecture
Opened:    2026-07-06
Area:      new module, TBD name (proposal stage)
Related:   ENG-51 (persistence split), ENG-52 (parseability), ENG-55 (formula/basket, separate session)
-->

**Description:** Client-identified gap: the six-scenario/EV engine is
deliberately conservative by design (session-boundary updates only, 25pp
cap, T1-only evidence) — appropriate for feasibility/floor math, but
structurally incapable of catching fast rotations (e.g. XAR's post-Hormuz-
closure bounce, later confirmed as a real classification bug — see M15
XAR sign issue — but the *speed* problem is separate and would recur even
with a correct classification). Client also flagged the July 3→July 6
session-to-session F-probability swing (29.8%→8.8% on materially identical
facts) as evidence the subjective 0-3 scoring layer itself introduces
inconsistency that fine-grained probabilities can't actually support.

**Proposal:** a separate, additive trend/rotation module — NOT feeding
M03.DeriveScenarioProbabilities() (same NEVER rule M14/M17 already
follow) — computing deterministic, non-subjective signals directly off
price/relative-strength data (no Claude scoring judgment calls in the
critical path, learning directly from the F-swing lesson): relative
strength of a holding vs. a defined peer basket over a fixed lookback,
discounted/flagged by margin-debt trend (FINRA, see ENG-54) for rally
fragility. Advisory only during trial — logged, not routed into
execution, same pattern M14's regime signal already uses.

**Trial design (per client + Claude discussion 2026-07-06):** run in
shadow mode — log both the existing `dominant_directive_conflict_aware`
(from advisor_evaluate_allocation, already computed every session) AND
the new trend read, per held instrument, per session, plus a forward-
looking outcome column (did price keep moving the direction trend called).
Review at a fixed **calendar checkpoint (~8 weeks)**, not a session count.
Conflict-resolution authority (does trend override EV, and under what
explicit condition) is decided FROM the trial data, not guessed upfront —
this was an explicit client decision to avoid re-creating today's
ambiguity one layer up.

**Suggested next step:** scope as its own persistence entity + minimal
MCP surface (likely a new fetch for relative-strength calc, reusing
market_data_mcp:market_get_history) once ENG-55 (formula/peer-basket)
is resolved in its own dedicated session. Do not build the formula inline
here.

### ENG-51 — V4: split instrument classification (§11) into its own persistence entity
<!-- ITEM
Status:    OPEN
Severity:  MEDIUM
Category:  architecture
Opened:    2026-07-06
Area:      Calibration_State.md §11 → new file (name TBD, e.g. Instrument_Classification.md)
Related:   ENG-50, ENG-15/M15_InstrumentClassification.md (role registry logic unchanged, only storage location moves)
-->

**Description:** Client-requested split, motivated by ENG-50: the trend
layer needs to read/write per-instrument state (relative-strength rank,
trend flags) without touching credit thresholds, return tables, or other
unrelated §1–§10/§12 content currently sharing Calibration_State.md.
Today §11 (role registry) is one section inside one large file — every
Calibration_State.md read/write for ANY reason currently touches the same
file as instrument classification.

**Suggested next step:** extract §11 verbatim into its own file, update
M15's read path and M12's file-access protocol accordingly, leave the
role-registry *logic* (classifyInstrument(), ValidateClassifications())
untouched — this is a storage-location change only, not a semantics
change. Coordinate with ENG-52 (parseability) so the new file is created
in the improved structured format from day one rather than migrated
twice.

### ENG-52 — V4: structured parseable entry format for Session_Log.md / Calibration_State.md / FRAMEWORK_BACKLOG.md
**CLOSED** 2026-07-06 (MEDIUM, hygiene). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.

### ENG-53 — V4: calendar-age archival mechanism for Session_Log.md
<!-- ITEM
Status:    OPEN
Severity:  MEDIUM
Category:  architecture
Opened:    2026-07-06
Area:      Session_Log.md; candidate extension to Calibration_Log.md, FRAMEWORK_BACKLOG_ARCHIVE.md rotation cadence
Related:   ENG-52 (structured format makes archival mechanical rather than prose-parsing), ENG-5/ENG-7 (prior compaction-cadence work, same file)
-->

**Description:** Session_Log.md is 156 lines / ~20KB after roughly two
months of use, with multiple same-day entries on active days (e.g. two
2026-07-03 entries). Client explicit preference: rotate by **calendar
age**, not entry count or file size, and the live/current file should
remain easy to parse at all times — i.e. archival should keep the live
file small and current, not just prevent it from growing unbounded.

**Suggested next step:** define a fixed calendar-age threshold (e.g.
entries older than N days move to a Session_Log_Archive.md, mirroring the
existing FRAMEWORK_BACKLOG_ARCHIVE.md / Calibration_Log.md pattern already
in use elsewhere in this repo) and implement as part of
`advisor_write_back()`'s render step, gated on ENG-52's structured format
landing first so the rotation logic can key off a real `date:` field
rather than parsing prose.

### ENG-54 — V4: FINRA margin debt series has no M18 DATA_REGISTRY_ENTRY
<!-- ITEM
Status:    OPEN
Severity:  MEDIUM
Category:  infrastructure
Opened:    2026-07-06
Area:      M18_MarketDataFetch.md (new DATA_REGISTRY_ENTRY); new fetcher module
Related:   ENG-50 (consumer of this data)
-->

**Description:** Client wants margin-debt trend as a fragility discount
on the new trend layer's momentum reads (a rally funded heavily by margin
debt is more prone to a violent unwind). No current MCP tool or M18
registry entry fetches FINRA margin statistics. Confirmed with client:
FINRA's data (monthly, ~3–4 week publication lag) is acceptable for this
purpose — it's a regime-level fragility overlay, not a timing signal;
the timing job stays with the price/relative-strength side of ENG-50.

**Suggested next step:** register a new M18 DATA_REGISTRY_ENTRY once
ENG-50's overall shape is settled; identify the specific FINRA published
series/URL and confirm it's fetchable via the existing web_fetch/
web_search tools or needs a dedicated scraper.

### ENG-55 — V4: relative-strength formula + peer-basket definition (dedicated session)
<!-- ITEM
Status:    OPEN
Severity:  HIGH
Category:  functional-gap
Opened:    2026-07-06
Area:      new trend module (ENG-50), formula/config only — no persistence or MCP wiring yet
Related:   ENG-50 (consumer), explicitly scoped OUT of this session by client request
-->

**Description:** The one piece of ENG-50 with genuine judgment calls
baked in: what counts as the peer/comparison basket for a given holding
(e.g. what is MLPX's peer set — other energy-infrastructure/MLP funds?
broader energy sector? a custom basket?), what lookback window defines
"relative strength," and how exactly the margin-debt trend discounts a
momentum read. Client explicitly asked for this to be tackled fresh in
its own session rather than folded into the broader V4 design discussion
this session, precisely because it's the least mechanical, most
judgment-dependent piece of the whole proposal — the same category of
problem (subjective judgment presented as precise output) that this
session's F-probability discrepancy stemmed from. Should be resolved
carefully and explicitly, not inherited from this session's momentum.

**Suggested next step:** dedicated session hand-off already prepared —
open with peer-basket definition per current holding (MLPX, DBMF, XAR,
AIPO, COPX, SGOL/SIVR, MAGS), lookback-window choice, and the margin-debt
discount mechanism, before any code or persistence design.

### ENG-56 — Retrofit ENG-52 front-matter onto pre-v1.46 §3 entries
<!-- ITEM
Status:    OPEN
Severity:  LOW
Category:  hygiene
Opened:    2026-07-06
Area:      Calibration_State.md §3 (entries older than v1.46)
Related:   ENG-52 (this is its explicitly-deferred remainder)
-->

**Description:** ENG-52 migrated §3 entries v1.46 through v1.62 (17
entries, all live in the file today) to the new front-matter format —
every one of them used a single consistent "DATE (vX.XX) - Title." title
line, so extracting entry_id/date/version/category was mechanical, and
each entry's real git-commit timestamp was used for entry_id (not
fabricated). Entries older than v1.46 (roughly line 836 onward in the
current file) were deliberately left untouched: a quick check found at
least two different legacy title-line conventions ("DATE - Framework
vX.XX (Title)." and a bare "DATE - Title." with no version tag at all),
which makes automated splitting meaningfully riskier — the same kind of
transcription risk this file's own §3 scope-rule note and past compaction
entries have flagged before. Nothing programmatically parses §3 today
(parse_calibration_log() in config/calibration.py only recognizes the new
front-matter format and silently skips anything without it), so there is
no active bug from leaving these unmigrated — this is pure hygiene, not
a functional gap.

**Suggested next step:** when a future session has reason to be inside
§3's older history anyway (e.g. a Q-end audit reviewing pre-v1.46
decisions), inventory the actual set of legacy title-line conventions in
use first, then decide per-convention whether a regex extraction is safe
enough to automate or whether it needs a manual pass. Do not rush this —
correctness of the *narrative* content matters far more than having
every historical entry in the new format.

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
**CLOSED** 2026-07-02 (MEDIUM, infrastructure). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.


### ENG-43 — Credit-spread history truncated to 3y by FRED
**CLOSED** 2026-07-02 (MEDIUM, data-integrity). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.


### ENG-44 — calculator_mcp not wired to the project + is a stub
**CLOSED** 2026-07-02 (MEDIUM, infrastructure). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.


### ENG-45 — credit.py §1.3 CCC divergence OR-combines ratio + absolute modes (ratio false-positives)
**CLOSED** 2026-06-30 (LOW, bug). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.


### ENG-46 — test_compaction.py hardcodes a specific quarter, breaks every real quarter boundary
**CLOSED** 2026-07-03 (LOW, testing). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.


### ENG-47 — session.py Step4 signal-summary line crashes when spread_10y_2y is None
**CLOSED** 2026-07-03 (MEDIUM, bug). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.


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
