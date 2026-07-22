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

**Last updated:** 2026-07-22, live advisory session (ENG-69 OPENED -- NASDAQ_30D_RETURN
data reading returned -25.23% with current:55.8, matching SIVR's price rather than any
real Nasdaq level; direct market_data_mcp verification shows Nasdaq Composite's actual
30d return is -1.26%. Same cross-contamination signature as ENG-68 [closed one day
prior], different FetchSpec. Caused a false-positive MAGS section-13 FAILED read this
session, which was NOT acted on. Not fixed this session (advisory session, no code
changes) -- flagged for next coding session; see full entry in Part 1.)
Prior:
**Last updated:** 2026-07-21, coding session (ENG-68 CLOSED — root cause
confirmed by reading the installed yfinance source directly: `download()`
resets a global `shared._DFS = {}` per call and waits on a COUNT check
(`len(shared._DFS) < len(tickers)`), not a key check, so a straggler
worker thread from one concurrent `yf.download()` call can satisfy a
different call's wait with the wrong ticker's data — matches external
yfinance issue #2557. DBMF was fetched via two overlapping paths in the
same `fetch_all()` batch (its own dedicated call, plus the
TREND_SIGNAL_HISTORY batch it's already part of). Fix: removed the
redundant `DBMF_3M_RETURN` FetchSpec entirely; `thesis.py` now derives
DBMF's 3-month return from TREND_SIGNAL_HISTORY:DBMF's already-fetched
closes instead of a second racing fetch. Full suite: 947 passed / 46
skipped / 0 failed. Commit `516352e` (fix), see Part 1/Archive for the
closing commit. Root cause was NOT reproduced locally via direct testing
(5x full fetch_all() runs, 2-way concurrent repro, 5x isolated calls all
came back clean) — confirmed via yfinance's source instead, consistent
with a rare, timing-dependent race rather than a deterministic bug).
Prior:
2026-07-21, live advisory session (ENG-68 OPENED — client
challenged the DBMF_3M_RETURN figure cited in the session briefing (-4.19%);
direct market_data_mcp verification showed it was actually MAGS's price
series/return mislabeled as DBMF's, and DBMF's real 3-month return is
+2.53%. Same failure signature as ENG-27 (concurrent yfinance fetch
cross-contamination, closed 2026-06-20) but manifesting in the ENG-30
DBMF §13 evaluator's new data reading, not the *_TREND specs. Not fixed
this session (advisory session, no code changes) -- flagged for the next
coding session; see full entry in Part 1. Same session: confirmed ENG-67's
fix IS live and working (C_check_brent's auto_score correctly returned
None/deferred to Claude this session) -- a Claude briefing error stated it
was "still open," which was incorrect; ENG-67 remains CLOSED, no code
action needed there).
Prior:
2026-07-14, live M05 session (ENG-67 OPENED — client-side
audit found `C_check_brent`'s auto-scorer forces score=0 whenever Brent
sits >15% below the $110 nominal trigger, with no way to distinguish "no
supply event" from "verified event, price hasn't caught up" -- exposed
live tonight when a T1-confirmed Hormuz naval blockade still scored 0
because Brent ($85.30) hadn't moved far enough. Not fixed this session
(advisory session, no code changes) -- flagged for the next coding
session; suggested fix is a one-line deletion, see full entry in Part 1).
Prior:
2026-07-13, live M05 session (ENG-65 CLOSED — direct
follow-on from ENG-63: `directional_trend()`'s "no reversal through the
window's start" rule was found to be a faithful implementation of
`Calibration_State.md` §13's own DBMF-specific text ("directional = net
move >= 8% in one direction without full reversal"), but had been
silently reused as the GENERAL trend definition for every other caller —
SGOL/SIVR's own price, GAP-16's real-yield/DXY gate, URA/COPX's §13
conditions — none of which have any documented text requiring it.
Evgeny's framing (DBMF is a strategy classification whose OWN price
should get the same plain trend treatment as any instrument; only its
macro-breadth condition, checking OTHER markets as a strategy-backdrop
proxy, should keep the stricter reading) resolved this cleanly:
`directional_trend()` gained an explicit `require_no_reversal` opt-in,
default False (plain time-series momentum — sign of net change, gated by
materiality, no path dependence), applied only at DBMF's own two §13
call sites (`thesis.py`) and its breadth-check mirror in `trend_signal.py`.
Live impact: SGOL and SIVR now correctly resolve to a real, confirmed
WEAKENING signal matching their actual observed decline, instead of the
misleading INCONCLUSIVE both reported before. 12 tests added/updated
across `test_stage3/test_trend.py` and `test_stage3/test_trend_signal.py`;
full suite 900 passed / 46 skipped / 0 failed, confirmed live. Same
session, post-restart: ENG-66 OPENED — client-requested audit of every
held instrument's §13 automated thesis coverage, run directly against
tsc_evaluations rather than assumed. First draft of this item wrongly
restated DBMF/AIPO/XAR's gaps as new finds — corrected in the same
session once a full backlog search surfaced ENG-30/31/34 already
documenting those exact three since 2026-06-20; ENG-66 now scoped to
what's actually new (COPX's consecutive-PMI-months gap, no prior
entry) plus reconfirming ENG-26/30/31/34 are all still open. Also
caught and logged a related Objectives-file misread (concentration_cap
vs drawdown_tolerance column confusion) found during the same pass.
Prior:
2026-07-13, live M05 session (ENG-63 CLOSED — root-caused
and fixed, mid-session, DBMF/SGOL/SIVR's Mode 2 confirmation gate conflating
a missing input with a computed no-agreement result: both `_agreement_gate`
and `_dbmf_macro_confirms` returned a bare `None` whether their raw series
were genuinely unfetchable or fetched fine but `directional_trend()` simply
found no resolved direction (a real-yield series with a materially strong
net move nulled by one early wobble below its own starting value; DBMF's
own price genuinely below the materiality floor). Both now correctly report
INCONCLUSIVE, not DATA_UNAVAILABLE, when the gate ran on real data — same
distinction ENG-60 already drew one layer up. 12 tests added/updated across
`test_stage3/test_trend_signal.py`; full suite 896 passed / 46 skipped / 0
failed. ENG-64 OPENED same session — Evgeny requested a polling mechanism to
replace the two remaining hard MCP-tool timeouts (`advisor_run_computation`,
`advisor_evaluate_trend_signal`); logged as its own architecture item since
it needs a server-side job-queue redesign, not a live patch. Prior:
2026-07-12, coding session (ENG-61 CLOSED — root-caused and
fixed RoleRepricingDivergence's "always skipped" flag, which Evgeny caught by
noticing SGOL/SIVR's real 30-day declines weren't being surfaced despite
`advisor_run_computation()`'s market data coverage having recovered from a
same-session VPN-related outage to 62/70 specs valid, including
`holdings_30d_returns`. Root cause: `compute_divergence_signal()`
(analysis/regime.py) only checked `BROAD_EQUITY_TRAILING.value` for keys
`change_30d`/`pct_30d`/`pct_change_30d` — none of which either
`fetch_broad_equity_trailing()` implementation (fmp_fetcher.py,
yfinance_fetcher.py) has ever actually produced; both use `return_30d_pct`,
a percentage number needing /100 to become the fraction this function's
threshold comparisons expect (confirmed via `types.py`'s own field comment).
The mismatch meant `broad_equity_30d` was always None in production,
regardless of whether holdings 30d data was available, so
`role_repricing_divergence()` (mcp_server.py) never even got called. Fixed by
recognizing `return_30d_pct` explicitly with the /100 conversion; other three
candidate keys kept for compatibility. `role_repricing_divergence()` itself
had zero test coverage before this session — added
`tests/test_stage3/test_regime.py::TestBroadEquityTrailingKeyExtraction` and
`::TestRoleRepricingDivergence` (10 new tests total). One test locks in the
exact 2026-07-12 SGOL figures (broad +2.56%, SGOL −8.87%) that motivated the
fix — confirms the corrected extraction does NOT, by itself, produce a
warning for that specific case: 11.43pp underperformance is genuinely below
SGOL's calibrated 15pp §9.5 threshold (SIVR's −22.55% would have crossed it
at 25.11pp, but SIVR isn't currently held in any of the six accounts). The
fix corrects a real bug; it doesn't retroactively make this session's SGOL
move cross the bar. Full suite: 889 passed, 46 skipped (one pre-existing,
unrelated failure — missing `googleapiclient` package for Pattern A's dormant
`allocation_sheet.py` Drive fallback, not touched by this change).
`codebase-memory-mcp` was fully unresponsive this session (both `manage_adr`
and `list_projects` timed out) — freshness check and investigation done via
Desktop Commander + grep instead, per README §14's own sanctioned fallback
for a codebase this size.

ENG-62 CLOSED same session — `Project_Instructions_MCP.md` and
`M03_ScenarioFramework.md`/`M12_DriveProtocol.md`/`M13_GrowthObjectives.md`/
`M14_MarketRegime.md` synced to the 2026-07-12 Allocation-file split (one
multi-tab "Allocation" file → three single-tab files: "Allocation",
"Allocation - Relative's Schwab Accounts", "Allocation - Objectives"). The
split itself happened in an earlier advisory session this same day, motivated
by discovering Google Drive's `read_file_content` reliably surfaces only ONE
tab per file — a hard per-call limitation, not the length/token-budget issue
first assumed, and which tab it returns from a multi-tab file depends on
which was last active in the Sheets UI, not a fixed index. `M12_DriveProtocol.md`'s
`fetchAllocation()` was rewritten as three calls to a new
`fetchAllocationFile(exact_title)` helper rather than one. Not yet
independently verified this session: whether the "Other Indexes"/FINRA/FRED
Series tabs M18_MarketDataFetch.md references (§ALLOCATION_SPREADSHEET_OTHER,
§ALLOCATION_SPREADSHEET_FINRA) still live inside the "Allocation" file
post-split, in their own file(s), or have been dropped — M18 was
deliberately left untouched rather than guessed at; worth a direct check
next session before touching that module.

Prior: 2026-07-08, coding session (ENG-60 CLOSED — resolved per the
session hand-off's own recommendation: added a 4th `TrendSignalCode` value,
`DATA_UNAVAILABLE`, distinct from `INCONCLUSIVE` [client-confirmed direction
(a) over additive-field option (b)]. Touched: `evaluate_return_spread()`'s and
`evaluate_own_trend_confirmed()`'s insufficient-history/missing-confirmation
branches; `evaluate_all_trend_signals()`'s own-price-missing and both
RETURN_SPREAD/HYBRID comparator-missing branches. Also fixed a related latent
bug found while touching MLPX's HY_OAS gate: `hy_confirms is None` (gate
itself unavailable) previously fell through with no downgrade at all, and
separately `code != INCONCLUSIVE` could wrongly clobber an already-
DATA_UNAVAILABLE code down to INCONCLUSIVE on `hy_confirms is False` — both
fixed by gating explicitly on the code being a real STRENGTHENING/WEAKENING
call before applying the confirmation veto. Backfilled today's 3 affected
TrendSignalStore.json entries (DBMF/SGOL/SIVR: INCONCLUSIVE → DATA_UNAVAILABLE;
AIPO/COPX/MAGS/MLPX/XAR unaffected — real computed reads) per Evgeny's
explicit confirmation. Project_Instructions_MCP.md synced (tool bullet, Step
7 TREND_ROTATION_SIGNAL guidance, NEVER-rules) per its own mandatory-sync
rule. tools/backtest_trend_signal.py's print_report() now reports
inconclusive/data_unavailable as separate columns — the actual intended
consumer of this distinction per the hand-off's own framing. Discovered and
fixed one unrelated pre-existing test bug in the same file: a 63-point
fixture one short of the 64 evaluate_return_spread's medium window needs,
silently landing in the insufficient-history branch instead of the
"windows disagree" branch it claimed to test — invisible before this fix
because both branches used to return the same value. 10 new tests
(trend_signal.py wiring/gating, trend_signal_store.py's DATA_UNAVAILABLE
forward-outcome fill). Full suite: 880 passed / 46 skipped / 0 failed —
ENG-41's known live-data-dependent flake [see its own entry] not observed
this run.)
Prior: 2026-07-08, advisory session (ENG-59 CLOSED — evaluate-trend-signal
CLI's own weekly-series fetch showed a one-off transient gap for DXY_TREND/
REAL_YIELD_10Y_TREND; root cause not reproducible on direct re-test [3x
clean], so added a single bounded retry as hardening rather than claim a
fix for an unconfirmed bug. ENG-60 OPENED — Evgeny flagged that
TrendSignalCode.INCONCLUSIVE conflates "inputs missing" with "inputs
complete, no resolved direction" [observed same session: DBMF/SGOL/SIVR
missing-input vs. XAR/AIPO/MAGS clean-data-mixed-signal, currently
indistinguishable except by checking whether quality_flags is empty] —
real design gap, touches the MCP tool's documented rs_signal contract, so
logged with a session hand-off rather than rushed alongside a live
advisory session. 2 new tests; full suite 873 passed / 46 skipped / 1
failed [ENG-41, pre-existing unrelated], zero new regressions.)
Prior: 2026-07-08, coding session (ENG-33 fallback built for the
trend signal: new `python -m advisor evaluate-trend-signal --json-file` CLI
command mirroring evaluate-allocation's — same one-tested-implementation-
two-entry-points pattern; `_tool_evaluate_trend_signal()` gained optional
cal/probs/log/readings overrides; the CLI reconstructs everything except
scenario_probs (framework files parsed fresh, five weekly-trend series
fetched fresh) and updates TrendSignalStore.json exactly like the MCP tool
so the ENG-50 shadow trial keeps accumulating data when the transport
hangs. Building its tests caught and fixed a REAL latent bug: a
DirectiveCode enum in dominant_directive_conflict_aware was not JSON
serializable and silently killed the entire TrendSignalStore update —
normalized to str at the source in mcp_server.py + default=str backstop in
trend_signal_store._save(). Project_Instructions_MCP.md updated (tool
bullet + Step 6c fallback notes). 5 new tests; full suite 871 passed / 46
skipped / 1 failed (ENG-41, same pre-existing unrelated failure), zero new
regressions.)
Prior: 2026-07-08, coding session (ENG-58 CLOSED — root-caused
and fixed the ~240s advisor_run_computation() hangs reported this session:
_fetch_single() in yfinance_fetcher.py — the URANIUM_SPOT/UX=F single-quote
path — was the one yfinance call site with no exception handling and no
independent timeout. UX=F is now confirmed genuinely delisted (live evidence
via mcp-server-financial-advisor.log); yf.Ticker(...).fast_info hanging on
it for ~4min compounded into an aggregate delay because the abandoned
thread kept holding the single global _YF_LOCK (ENG-27), stalling every
other yfinance-sourced spec in the same fetch_all() batch behind it —
landing right on Claude Desktop's own ~4min client-side call ceiling.
Fixed by bounding the actual blocking call to 12s via a worker-thread +
future.result(timeout=...), same pattern as mcp_server.py's _with_timeout(),
so _YF_LOCK can never be held past that bound regardless of whether the
delisted symbol's fetch itself ever completes. Also fixed the secondary
`TypeError: unsupported operand type(s) for -: float and NoneType` this
produced downstream (previous_close is None for a delisted symbol; now
raises a caught, flagged ValueError instead). 3 new tests
(TestFetchSingle: delisted-symbol degrade, hung-ticker timeout bound,
hung-ticker releases the lock promptly). Full suite: 866 passed / 46
skipped / 1 failed (ENG-41, same pre-existing unrelated failure as
baseline), zero new regressions. Separately confirmed via the same log
that advisor_evaluate_trend_signal()'s hangs this session are NOT this bug
— zero log entries for those calls at all, matching ENG-33's already-
documented client-side transport symptom exactly (request never reaches
the server); see ENG-33's update below. Full writeup in this entry below.)
Prior: 2026-07-07, coding session (ENG-57 CLOSED — persistence +
MCP wiring for the ENG-55 trend/rotation signal: new 6th MCP tool
`advisor_evaluate_trend_signal()`, `TrendSignalStore.json` persistence with
retroactive ~21-trading-day forward-outcome fill (CreditHistoryStore-style,
local commit only), one new batched `TREND_SIGNAL_HISTORY` FetchSpec (16
symbols, one yf.download() call rather than 16 separate registry entries —
ENG-35's MCP-ceiling concern stayed the deciding factor), and full
Project_Instructions_MCP.md wiring (new Step 6c, automatic every session per
client confirmation; new informational-only TREND_ROTATION_SIGNAL briefing
section; NEVER-rules addition). 43 new tests, zero regressions (854 passed /
46 skipped / 1 pre-existing unrelated failure, same as ENG-53's baseline).
Full writeup in FRAMEWORK_BACKLOG_ARCHIVE.md.)
Prior: 2026-07-07, design session (ENG-55 CLOSED — relative-strength
formula + peer-basket definition resolved: per-instrument comparator/mode table
(Mode 1 return-spread for XAR/MAGS/AIPO/COPX vs equity or commodity peers, Mode 2
own-trend-macro-confirmed for DBMF/SGOL/SIVR, hybrid for MLPX), a reusable 10%
materiality-exclusion rule, a blended ~1mo+~1qtr agreement-gated lookback window,
and a soft-flag-only (non-numeric) margin-debt fragility caveat for v1 shadow
mode — client-confirmed on all three open judgment calls. Noise-floor and
margin-debt tier thresholds explicitly deferred pending historical-analog work;
data-fetchability of new comparator tickers (PAVE/URA/HG=F/ITA/PPA) deferred to
ENG-50's persistence/MCP-wiring step. Full writeup in FRAMEWORK_BACKLOG_ARCHIVE.md.)
Prior: 2026-07-06, coding session (ENG-53 CLOSED — Session_Log.md
§7/§8 retention switched from entry-count (last-10/last-3, ENG-5) to pure
calendar age (90 days, client-confirmed), with no count-based fallback;
archived items now route to the archive file matching their OWN quarter,
not today's quarter, so a single write-back can touch more than one
Archive_[Year]Q[N].md file if archived items span a quarter or year
boundary; write_back()'s return signature changed to support multiple
archive files per call. §3 explicitly not brought under this rule -- stays
count-based/manual. Full suite: 809 passed / 46 skipped / 2 failed, same
baseline failures, zero new regressions. Full writeup in
FRAMEWORK_BACKLOG_ARCHIVE.md.)
Prior: 2026-07-06, coding session (ENG-51 CLOSED — §11 extracted
verbatim out of Calibration_State.md into its own file, Instrument_Classification.md;
required zero changes to the existing role/instrument parser functions since
they already located content via string markers rather than assuming a
single-file structure; parse_calibration_state() gained an optional second
parameter; all 4 production call sites updated; M12/M15/00_INDEX/
Project_Instructions_MCP.md framework spec files updated to match, and a
stale-Amendment-number drift was fixed in passing. Also surfaced that
whatever backs project_knowledge_search is stale relative to the actual
repo state in ways beyond this change -- flagged for a separate look. Full
suite: 807 passed / 46 skipped / 2 failed, same baseline failures, zero new
regressions. Full writeup in FRAMEWORK_BACKLOG_ARCHIVE.md.)
Prior: 2026-07-06, coding session (ENG-52 CLOSED — Session_Log.md
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
| ENG-48 | CLOSED 2026-07-14 | HIGH | bug | advisor_write_back's 90s safety-timeout races its own actual completion time — reports TIMEOUT while succeeding server-side |
| ENG-49 | MITIGATED 2026-07-14 (root fix — full step instrumentation — not built) | HIGH | bug | advisor_write_back TIMEOUT with a genuinely incomplete server-side operation — files+archive rendered and written, but git add/commit never ran, distinct from ENG-48's "actually succeeded" pattern |
| ENG-50 | OPEN | HIGH | architecture | V4: Trend/Rotation Signal Layer — deterministic price/relative-strength module, additive to scenario engine, shadow-mode trial before any authority decision |
| ENG-51 | CLOSED | MEDIUM | architecture | V4: split instrument classification (§11) out of Calibration_State.md into its own persistence entity |
| ENG-52 | CLOSED | MEDIUM | hygiene | V4: structured parseable entry format (front-matter block) for Session_Log.md, Calibration_State.md, FRAMEWORK_BACKLOG.md |
| ENG-53 | CLOSED | MEDIUM | architecture | V4: calendar-age archival mechanism for Session_Log.md (and candidate extension to other growing files) |
| ENG-54 | OPEN | MEDIUM | infrastructure | V4: FINRA margin debt series has no M18 DATA_REGISTRY_ENTRY or fetch path |
| ENG-55 | CLOSED | HIGH | functional-gap | V4: relative-strength formula + peer-basket definition for trend layer — needs its own dedicated session, real judgment calls involved |
| ENG-56 | OPEN | LOW | hygiene | Retrofit ENG-52 front-matter onto pre-v1.46 §3 entries (inconsistent legacy title-line conventions) |
| ENG-57 | CLOSED | HIGH | functional-gap | V4: persistence + MCP wiring for the ENG-55 trend/rotation signal — new 6th MCP tool, TrendSignalStore.json, batched daily-history fetch |
| ENG-58 | CLOSED | HIGH | bug | _fetch_single()'s unguarded URANIUM_SPOT/UX=F fetch could hold the global _YF_LOCK for ~4min, stalling every other yfinance spec in the same fetch_all() batch behind it |
| ENG-59 | CLOSED | LOW | hardening | evaluate-trend-signal CLI's own weekly-series fetch showed a one-off transient gap; added single bounded retry (root cause not reproducible on direct re-test) |
| ENG-60 | CLOSED | MEDIUM | architecture | TrendSignalCode gained a 4th value, DATA_UNAVAILABLE, distinct from INCONCLUSIVE -- direction (a) from the hand-off, client-confirmed; backfilled today's 3 affected store entries; also fixed a related MLPX HY_OAS gating bug found in the same code |
| ENG-61 | CLOSED | HIGH | bug | RoleRepricingDivergence always skipped -- BROAD_EQUITY_TRAILING key mismatch (regime.py checked change_30d/pct_30d/pct_change_30d; both fetchers actually produce return_30d_pct) meant broad_equity_30d was always None in production |
| ENG-62 | CLOSED | LOW | hygiene | Project_Instructions_MCP.md + M03/M12/M13/M14 synced to the 2026-07-12 Allocation-file split (one multi-tab file -> three single-tab files) |
| ENG-63 | CLOSED | MEDIUM | bug | DBMF/SGOL/SIVR's Mode 2 confirmation gate (_agreement_gate, _dbmf_macro_confirms) conflated a missing input with a computed no-agreement result -- both collapsed to DATA_UNAVAILABLE even when the underlying data fetched cleanly |
| ENG-64 | OPEN | MEDIUM | architecture | advisor_run_computation / advisor_evaluate_trend_signal have a hard client-side timeout with no polling/job-status mechanism -- both confirmed ENG-33-style transport hangs, not slow computation |
| ENG-65 | CLOSED | HIGH | bug | directional_trend()'s unconditional "no reversal" veto (built to match DBMF's own §13 text) silently suppressed real, material trends for every other caller -- SGOL/SIVR's own price, GAP-16's real-yield/DXY gate, URA/COPX conditions; now an explicit require_no_reversal opt-in, kept only for DBMF's own documented strategy-backdrop condition |
| ENG-66 | CLOSED 2026-07-14 (COPX leg only) | MEDIUM | functional-gap | COPX's "China demand collapse >=2 consecutive months" §13 condition has no evaluator (same consecutive-period problem as ENG-26/31) -- the one genuinely new gap from a full coverage audit that otherwise reconfirmed ENG-26/30/31/34 are still open; also documents an Objectives-file column misread (concentration_cap vs drawdown_tolerance) found in the same pass, still UNRESOLVED, no ENG number yet |
| ENG-67 | OPEN | MEDIUM | bug | C_check_brent auto-scorer forces score=0 whenever Brent is >15% below the $110 nominal trigger, regardless of whether a T1-verified supply event (e.g. tonight's Hormuz blockade) is active -- can silently understate C; existing above-trigger branch already defers to Claude, below-trigger branch should too |
| ENG-68 | CLOSED 2026-07-21 | HIGH | data-integrity | DBMF_3M_RETURN data reading returned MAGS's price series -- yfinance concurrent-fetch race; fixed by removing the redundant FetchSpec and deriving DBMF's 3M return from TREND_SIGNAL_HISTORY:DBMF instead |
| ENG-69 | OPEN | HIGH | data-integrity | NASDAQ_30D_RETURN data reading (-25.23%, current 55.8) cross-contaminated with SIVR's series -- same ENG-27/ENG-68 failure signature, different FetchSpec; caused a false-positive MAGS section-13 FAILED read this session |
| ENG-70 | OPEN | HIGH | data-integrity | holdings_30d_returns systematically overstated SGOL (-8.92%/-13.86% vs verified -2.46%) and SIVR (-21.89%/-22.26% vs verified -9.9%) in BOTH consecutive runs this session -- consistent wrongness, not a random flip, suggests a lookback-window/indexing bug distinct from ENG-27/68/69's race condition; caused a false-positive SIVR Sec9.5 role-repricing warning (real underperformance -10.4pp, below its 15pp threshold) |
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
| ENG-26 | CLOSED 2026-07-14 | LOW | functional-gap | MAGS's "consecutive sessions" §13 condition needs cross-session SIGNAL history — different problem from ENG-13's price-series trends |
| ENG-27 | CLOSED | CRITICAL | data-integrity | yfinance concurrent fetches under ThreadPoolExecutor returned cross-contaminated *_TREND data |
| ENG-28 | CLOSED | HIGH | data-integrity | floor_account_weights_json double-JSON-encoding crashed CurrentHoldingsFloorCheck/PassiveMandateAbsentWarning |
| ENG-29 | CLOSED | LOW | hygiene | thesis.py XAR Call-2 routing missed an alternate §13 phrasing for the same de-escalation judgment |
| ENG-30 | CLOSED 2026-07-14 | MEDIUM | functional-gap | DBMF's "3M return < -3% while B+C>=55%" §13 failure condition has no FetchSpec/evaluator |
| ENG-31 | CLOSED 2026-07-14 | LOW | functional-gap | AIPO's hyperscaler capex guidance §13 sustaining condition has no data source |
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

### ENG-70 -- holdings_30d_returns systematically wrong for SGOL/SIVR (both runs, not a random flip)
<!-- ITEM
Status:    OPEN
Severity:  HIGH
Category:  data-integrity
Opened:    2026-07-22
Area:      python/advisor -- holdings_30d_returns computation path (Sec9.5 RoleRepricingDivergence input); distinct from TREND_SIGNAL_HISTORY, which was independently verified correct for the same tickers/window
Related:   ENG-69 (same session, different mechanism -- ENG-69 was a one-off cross-ticker race flip; this is a consistent bias reproduced across two separate advisor_run_computation() calls)
-->

**Description:** Live M05 session, 2026-07-22, second half. Two separate advisor_run_computation() calls in the same session both reported SGOL and SIVR 30-day returns far more negative than reality: SGOL -8.92% then -13.86% (verified actual, via market_data_mcp period=1m: -2.46%); SIVR -21.89% then -22.26% (verified actual: -9.9%). Unlike AIPO/MAGS/NASDAQ_30D_RETURN in the same session (ENG-69), which flipped sign or value randomly call-to-call -- consistent with the known ENG-27 concurrent-yfinance-fetch race -- SGOL/SIVR were wrong in the SAME direction (overstated decline) both times, with different-but-similarly-wrong magnitudes. This pattern does not match a random race flip; it looks more like a lookback-window or array-indexing bug specific to how holdings_30d_returns resolves these two tickers (e.g. reading a stale/longer-window closing price as the '30 days ago' anchor). Cross-checked against TREND_SIGNAL_HISTORY:SGOL and TREND_SIGNAL_HISTORY:SIVR (both fetched in the same run) -- the raw daily closes in those arrays are internally consistent with the verified market_data_mcp figures, meaning the raw price data was fetched correctly; the bug is specifically in whatever holdings_30d_returns does with it (a separate calculation path, not a raw-fetch contamination).

**Live impact this session:** the corrupted SIVR figure fed Sec9.5 RoleRepricingDivergence and produced a role-repricing warning (SIVR breaching its 15pp inflation_hedge_precious_metals threshold) in BOTH runs. On verified data, SIVR's real underperformance vs broad market is only ~10.4pp -- below the 15pp threshold. This warning is a false positive and was not acted on. AIPO's warning (run 1 only; run 2 missed it via ENG-69's unrelated sign-flip) held up under verified data (-13.4pp, above its 10pp threshold) -- that one is real.

**Suggested fix direction:** isolate holdings_30d_returns's calculation (likely in the same module that produces Sec9.5 inputs) and compare its lookback-day/index logic against TREND_SIGNAL_HISTORY's, which is known-correct for the same tickers over the same window. Given two independently wrong-but-consistent readings for the SAME two tickers (not a random pair each time), suspect a ticker-specific data-shape issue (e.g. SGOL/SIVR fetched via a different code path than XAR/MLPX/DBMF/COPX, which were all correct both runs) rather than a generic off-by-N bug.

Not fixed this session (advisory session, no code changes) -- flagged for the next coding session. Recommend triaging together with ENG-69 since both surfaced in the same session, but keep them as separate items given the distinct failure signature.


### ENG-69 -- NASDAQ_30D_RETURN data reading cross-contaminated with SIVR's series
<!-- ITEM
Status:    OPEN
Severity:  HIGH
Category:  data-integrity
Opened:    2026-07-22
Area:      python/advisor -- likely yfinance_fetcher.py / fetch_registry.py, NASDAQ_30D_RETURN FetchSpec
Related:   ENG-68 (same failure signature, closed one day prior, for DBMF_3M_RETURN), ENG-27 (original yfinance concurrent-fetch cross-contamination root cause)
-->

**Description:** Live M05 session, 2026-07-22. advisor_run_computation()'s market_data.NASDAQ_30D_RETURN reading returned {return_30d_pct: -25.23, current: 55.8}. Direct verification via market_data_mcp:market_get_history (symbol ^IXIC, period 1m) shows the Nasdaq Composite's actual 30-day return is -1.26% (26,166.60 -> 25,837.21, 2026-06-22 to 2026-07-21) -- nowhere near -25.23%. The current: 55.8 figure does not match any plausible Nasdaq index/ETF level; it is suspiciously close to SIVR's actual price this session (~$55.80-56.98 per market_data.PRICE:SIVR / holdings_30d_returns.SIVR: -21.89%), suggesting the same class of cross-ticker contamination as ENG-68 (concurrent yf.download() race per yfinance issue #2557) -- but on a different data reading than the one ENG-68's fix (removing the redundant DBMF_3M_RETURN FetchSpec) addressed. ENG-68's fix was a point patch for one manifestation, not the underlying race-condition risk shared across all FetchSpecs that share a concurrent batch.

**Live impact this session:** the corrupted reading fed tsc_evaluations and caused MAGS's section-13 'Nasdaq 30d return <= -10% (sustained tech correction)' condition to report status: FAILED. This is a false positive -- the real Nasdaq 30d return (-1.26%) is far from the -10% threshold. Treated as unresolved/not-failed in this session's briefing and write-back, same handling pattern used for ENG-68's DBMF figure when it was caught live.

**Suggested fix direction:** identify which FetchSpec produces NASDAQ_30D_RETURN and whether it shares a concurrent yf.download() batch with a SIVR-touching spec; apply the same fix pattern as ENG-68 (derive from an already-fetched, non-racing series, or isolate the fetch). Given ENG-27's root cause is shared yfinance global state under concurrent fetches, this can in principle contaminate any FetchSpec overlapping another in the same batch -- a systemic audit of all concurrent FetchSpecs may be warranted rather than patching one symbol at a time as each is caught live.

Not fixed this session (advisory session, no code changes) -- flagged for the next coding session.


### ENG-48 — advisor_write_back's 90s safety-timeout races its own actual completion time
**CLOSED** 2026-07-14 (HIGH, bug). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.

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

**Recurrence (2026-07-08):** same exact pattern, fourth-ish occurrence —
`advisor_write_back()` hit the ~4min ceiling; `git log` showed no new
commit; `git status`/`git diff` confirmed `Session_Log.md` and
`Portfolio_State.md` were both rendered completely and correctly (§8 entry
well-formed, scenario_probabilities summed to 100%, no truncation).
Recovered the same way: `git add` both files + `git commit -F` + `git push`
by hand. Still no instrumentation added — the suggested next step above
remains the actual fix; this is just another data point that it's a
recurring, not one-off, failure mode.

**MITIGATION (2026-07-14, coding session):** the full step-by-step
instrumentation suggested above was NOT built — this item stays OPEN for
that reason. What did change, as part of closing ENG-48 (same code paths):
`file_protocol._git_commit()` now backgrounds `git push` in a daemon thread
instead of running it synchronously inside the 90s critical path, and
`mcp_server._write_back_with_verification()` now checks `git rev-parse
HEAD` before/after a TIMEOUT to distinguish a raced-but-real success from a
genuinely stuck operation (see ENG-48's resolution in
FRAMEWORK_BACKLOG_ARCHIVE.md for both in full). Net effect on this item
specifically: the synchronous window between file-write and git-commit —
the actual failure boundary this item describes — no longer has push's
up-to-30s allowance sitting inside it competing for the same 90s budget,
so the operation as a whole should have more comfortable margin and this
failure mode should occur less often. It has NOT been made structurally
impossible, and there is still no per-step visibility into exactly where a
future occurrence stalls — a real TIMEOUT after the 2026-07-14 fix now
reliably means "verified no new commit landed, something is actually
stuck," which is a strictly better diagnostic starting point than before,
but "which step" still requires the same manual `git status`/`git diff`
forensic pass this item was opened to eliminate.

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

**Progress note (2026-07-07):** ENG-55 closed (formula/comparator design
resolved). Spot-checked comparator-ticker fetchability via
market_data_mcp this session: PAVE and URA are both already live holdings
(PAVE 11% Taxable, URA 3% IRA/Roth) and already flow through the existing
`HOLDINGS_PRICES` FetchSpec -- no new work needed for either. HG=F
already has a dedicated M18 FetchSpec (added for §13 M19's COPX/URA
thesis monitoring) -- but registered at WEEKLY granularity there; the new
RS formula's Mode 1 spread wants daily closes for its 21td/63td windows,
so either a second daily-granularity fetch or a weekly-close-adapted
formula variant will be needed. ITA and PPA (XAR's comparator peers) have
no registry entry anywhere yet, but market_data_mcp confirms clean daily
history for both (62 trading days, no gaps) -- trivial to add later via
the same YFINANCE pattern already used for BZ=F/HG=F. Nothing here is
wired yet; this is confirmation the persistence/MCP-wiring step has no
data-availability surprises waiting, not the wiring itself.

**Progress note (2026-07-07): persistence + MCP wiring done, see ENG-57
(CLOSED).** `advisor_evaluate_trend_signal()` is now a live 6th MCP tool,
`TrendSignalStore.json` accumulates readings + forward-outcome fills, and
it's wired into the session sequence as automatic Step 6c (client-
confirmed) with a new informational-only TREND_ROTATION_SIGNAL briefing
section. What's still outstanding for THIS item (ENG-50) specifically:
the ~8-week shadow-mode trial itself hasn't started accumulating real
data yet (starts from the next FULL_DESKTOP session), ENG-54 (margin-debt
source) is still OPEN so `margin_debt_fragility_flag` stays null every
session until that lands, and the conflict-resolution-authority question
(does trend ever override EV) stays explicitly undecided until the trial
produces outcome data to decide it from.

**Progress note (2026-07-07, later same day): e2e wiring test + historical
backtest capability added.** Two follow-ups after a direct question about
whether ENG-50/ENG-55 were "fully implemented": (1) `_tool_evaluate_trend_signal()`
itself had only been unit-tested in pieces, never as the actual composed
MCP tool — added 3 tests to `test_pattern_b_pipeline.py` exercising it
end-to-end (sequential-dependency checks + a full no-network run); all
pass. (2) Built `tools/backtest_trend_signal.py` — a historical backtest,
explicitly a complement to the live trial, NOT a substitute (see its own
docstring for the full reasoning: look-ahead-bias risk on today's
placeholder thresholds, no reconstruction of historical
`dominant_directive_conflict_aware`, small non-overlapping-window sample
sizes). Reuses `evaluate_all_trend_signals()` directly against sliced
historical data rather than reimplementing the formula, so it tests the
same code path production uses. First real run (~18mo lookback, one bug
fixed first — the script forgot to load `.env`, so an initial run showed
false FRED-unavailable results for SGOL/SIVR before that was caught):
MLPX 5 calls/60% hit rate, XAR 4/25%, COPX 8/75%, MAGS 5/60%, DBMF/SGOL/SIVR
0 calls (100% INCONCLUSIVE across all 15 windows each — a genuine finding,
not a bug, once the FRED fix confirmed it), AIPO only 3 windows (inception
2025-07-24, genuinely short trading history, not a data problem). Overall
22 calls / 59% hit rate across the whole backtest — small-sample, not
treated as validating or invalidating the formula. Worth watching whether
DBMF/SGOL/SIVR's Mode 2 conditions are simply strict-but-correct or too
strict to ever fire usefully, once more live trial data accumulates.

### ENG-51 — V4: split instrument classification (§11) into its own persistence entity
**CLOSED** 2026-07-06 (MEDIUM, architecture). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.

### ENG-52 — V4: structured parseable entry format for Session_Log.md / Calibration_State.md / FRAMEWORK_BACKLOG.md
**CLOSED** 2026-07-06 (MEDIUM, hygiene). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.

### ENG-53 — V4: calendar-age archival mechanism for Session_Log.md
**CLOSED** 2026-07-06 (MEDIUM, architecture). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.

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
**CLOSED** 2026-07-07 (HIGH, functional-gap). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.

### ENG-57 — V4: persistence + MCP wiring for the ENG-55 trend/rotation signal
**CLOSED** 2026-07-07 (HIGH, functional-gap). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.

### ENG-58 — _fetch_single()'s unguarded URANIUM_SPOT fetch could hold _YF_LOCK for ~4min
<!-- ITEM
Status:    CLOSED
Severity:  HIGH
Category:  bug
Opened:    2026-07-08
Closed:    2026-07-08
Area:      python/advisor/data/fetchers/yfinance_fetcher.py (_fetch_single)
Related:   ENG-27 (introduced _YF_LOCK), ENG-40 (introduced _FETCH_TIMEOUT_SECONDS
           and _YF_LOCK_TIMEOUT_SECONDS, same UX=F symbol), ENG-33 (different
           mechanism — see that entry's update below)
-->

**Description:** An advisory session reported `advisor_run_computation()` hanging
the full ~4-minute MCP client ceiling, twice, before a server restart, then
again once after. Diagnosed live via `mcp-server-financial-advisor.log`
(Claude Desktop's own MCP transport log) rather than guessed at: the request
DID reach the server both times, and the server DID eventually return a
valid, complete result — `notifications/cancelled` from the client arrives
at almost exactly 240.0s, with the server's actual `result` logged only
~5-10ms later. The client gave up right as a good answer was arriving, not
because the server was stuck or crashed.

Immediately after each delayed result, the log shows:
```
ERROR yfinance: $UX=F: possibly delisted; no price data found (period=5d)
ERROR yfinance: $UX=F: possibly delisted; no price data found (period=5d)
WARNING advisor.data.fetch_registry: Fetch failed [URANIUM_SPOT]: unsupported operand type(s) for -: 'float' and 'NoneType'
ERROR yfinance: 1 Failed download: ['UX=F']: YFInvalidPeriodError(...)
```

`URANIUM_SPOT` (`_SYMBOL_MAP["URANIUM_SPOT"] = "UX=F"`, already flagged
`# ← unconfirmed/illiquid` in this file and `m18_registry.py` — this session
is the first live confirmation it's genuinely broken, not just theoretically
risky) routes through `_fetch_single()`, the *one* yfinance call site in
this module with no try/except and no independent timeout — unlike its two
siblings `fetch_weekly_trend()` and `fetch_trend_signal_histories()`, both
of which already degrade gracefully. `yf.Ticker("UX=F").fast_info` hanging/
retrying internally against a delisted symbol could run for minutes,
uncaught.

**Why one bad symbol produced an *aggregate* ~240s delay, not just its own
timeout:** `fetch_registry.py.fetch_all()` already bounds each spec's future
to `_FETCH_TIMEOUT_SECONDS=25s` (added by ENG-40) and abandons it
(`ex.shutdown(wait=False)`) rather than waiting further. But the abandoned
worker thread keeps running in the background — and keeps holding
`_YF_LOCK`, the single global lock ENG-27 added to prevent cross-symbol
data corruption under concurrent yfinance calls. Every *other*
yfinance-sourced spec still pending in the same `fetch_all()` batch then
also has to wait up to `_YF_LOCK_TIMEOUT_SECONDS=20s` just to acquire that
still-held lock before it can even start its own fetch. With ~15-20 other
YFINANCE specs typically in the batch, that's how one bad symbol's own 25s
timeout compounds into an aggregate delay landing right on Claude Desktop's
~4-minute client-side call ceiling. ENG-27 and ENG-40 are each individually
correct; the gap was in the *interaction* between a global lock and a
timeout mechanism that can only abandon *waiting*, not force the underlying
thread to actually stop and release what it holds.

**Fix:** bound the actual blocking call inside `_fetch_single()` itself,
using the same worker-thread + `future.result(timeout=...)` pattern already
established in `mcp_server.py`'s `_with_timeout()` — `_SINGLE_FETCH_TIMEOUT_SECONDS
= 12.0`. This guarantees `_fetch_single()` exits (and releases `_YF_LOCK`)
within its own 12s bound regardless of whether the abandoned inner thread
ever actually finishes — the same accepted caveat `_with_timeout()` already
documents, just applied one layer deeper so the *lock specifically* can
never be held past our own bound, rather than for however long Yahoo
Finance's retry/backoff behavior against a delisted symbol takes. Also
fixed the secondary bug this same failure mode was tripping: `fast_info.previous_close`
is `None` for a delisted symbol, and the day-change computation
`(last_price - previous_close) / previous_close` raised an uncaught
`TypeError` on that `None` — now explicitly checked and raised as a caught,
flagged `ValueError` instead.

**Verification:** 3 new tests added to `TestFetchSingle` in
`test_yfinance_unit.py` — delisted-symbol (`previous_close=None`) degrades
to a flagged reading rather than an uncaught `TypeError`; a hung
`fast_info` property is bounded to the patched-down timeout rather than
blocking the caller; and, directly targeting the actual regression, a
second unrelated `_yf_lock_guard()` acquisition immediately after a timed-
out hung fetch completes near-instantly rather than waiting out
`_YF_LOCK_TIMEOUT_SECONDS` — proving the lock is released promptly instead
of staying held by the abandoned thread. Full suite: 866 passed / 46
skipped / 1 failed (`ENG-41`, same pre-existing unrelated failure as
baseline — confirmed via `git stash` equivalent reasoning, not new), zero
new regressions.

**Not fixed as part of this item (deliberately deferred):** whether
`URANIUM_SPOT` should implement the proxy-substitution fallback its own
`m18_registry.py` description already promises ("M19 falls back to the URA
ETF price... flagged as a proxy substitution") — that fallback isn't
actually wired anywhere today; `URANIUM_SPOT` just fails and flags. Given
`URA`'s own price already flows through `HOLDINGS_PRICES` regardless, this
is a real but separate follow-up, not blocking — flagging here rather than
scope-creeping this fix.

**Suggested next step:** decide whether `URANIUM_SPOT` (the single-quote
spot price) is worth keeping at all given `URANIUM_TREND` (same `UX=F`,
weekly closes, already degrades gracefully via `fetch_weekly_trend`) covers
the same underlying data need for M19's actual sustaining/failure
conditions. If keeping it, wire the documented URA-proxy substitution
explicitly rather than leaving it as a bare `FETCH_FAILED`.

### ENG-59 — evaluate-trend-signal CLI: bounded retry for a transient weekly-series gap
<!-- ITEM
Status:    CLOSED
Severity:  LOW
Category:  hardening
Opened:    2026-07-08
Closed:    2026-07-08
Area:      python/advisor/__main__.py (cmd_evaluate_trend_signal)
Related:   ENG-33 (this CLI exists as its fallback), ENG-58 (same session,
           different mechanism -- see that entry's own note on this)
-->

**Description:** A live re-run of the advisory session showed
`advisor_evaluate_trend_signal`'s own `evaluate-trend-signal` CLI fallback
completing successfully overall, but three tickers' comparator inputs
(DBMF, SGOL, SIVR) came back INCONCLUSIVE with quality flags citing
`DXY_TREND`/`REAL_YIELD_10Y_TREND` unavailable -- series that
`advisor_run_computation()`'s own `fetch_all()` had fetched successfully
moments earlier in the same session.

**Investigated, root cause NOT confirmed:** initial hypothesis was a
fetcher-registration collision in `__main__.py`'s `_build_registry()`
(`fred.fetch_yield_curve_fred` and `sheet.fetch_fred_series` are both
registered for `DataSource.FRED_SPREADSHEET_TAB` when Google credentials
exist, with the second silently overwriting the first in the registry's
plain dict). Directly tested this by calling `_build_registry()` and
`fetch_one()` for both specs in isolation -- three repeated, clean
attempts, zero flags, correct values matching what `advisor_run_computation`
had returned. The registry wiring is correct; this was not a reproducible
collision. Most likely explanation given the evidence: a one-off transient
network hiccup on the CLI's own independent re-fetch (it fetches its own
fresh copy of these five weekly series rather than reusing
`advisor_run_computation`'s cached readings) -- not a deterministic bug.

**Fix:** rather than leave the CLI (which exists specifically to be the
*reliable* path when the MCP tool itself is flaky) vulnerable to the same
class of one-off blip, added a single bounded retry per spec: if
`fetch_one(spec_id)` returns a flagged reading, retry once and use the
retry's result only if it comes back clean; otherwise keep the original
(flagged) reading and let the tool degrade gracefully as designed. This is
deliberately NOT unbounded/blind retrying (that's the exact anti-pattern
ENG-58 just fixed elsewhere) -- one extra attempt, only for specs that
failed once, nothing more.

**Verification:** 2 new tests in `test_evaluate_trend_signal_cli.py` --
a spec flagged on attempt 1 but clean on retry ends up clean in the
tool's input; a spec flagged on *both* attempts still completes
(`status: "OK"`) with the tool's normal per-instrument degrade, not a
crash or hang. Full suite: see ENG-60's entry below for combined test
count (both items landed in the same commit).

**Honesty note:** this closes the *symptom* with reasonable, low-risk
insurance. It does not close the question of *why* the transient gap
happened in the first place, since it could not be reproduced. If this
recurs, capture the exact error via `ADVISOR_LOG_LEVEL=DEBUG` on a repeat
occurrence before assuming the retry alone is sufficient long-term.

### ENG-60 — TrendSignalCode.INCONCLUSIVE conflated two different situations
<!-- ITEM
Status:    CLOSED
Severity:  MEDIUM
Category:  architecture
Opened:    2026-07-08
Closed:    2026-07-08
Area:      python/advisor/types.py (TrendSignalCode),
           python/advisor/analysis/trend_signal.py (evaluate_return_spread,
           evaluate_own_trend_confirmed, evaluate_all_trend_signals),
           python/advisor/mcp_server.py (_tool_evaluate_trend_signal's
           docstring), python/advisor/__main__.py (cmd_evaluate_trend_signal
           docstring/comments), tools/backtest_trend_signal.py (print_report),
           Project_Instructions_MCP.md (tool bullet, Step 7
           TREND_ROTATION_SIGNAL guidance, NEVER-rules), TrendSignalStore.json
           (backfilled 2026-07-08 entries)
Related:   ENG-50/ENG-55 (the trend signal layer this belongs to)
-->

**Description:** Raised directly by Evgeny during a live session: is it
ambiguous that `rs_signal` collapses two genuinely different situations
into the same `INCONCLUSIVE` value?

1. **Inputs missing** -- a comparator series, macro confirmation gate, or
   own-price history was unavailable this session, so the tool has no
   basis to compute a direction at all. (Observed 2026-07-08: DBMF, SGOL,
   SIVR -- each with an explicit quality_flag naming the missing input.)
2. **Inputs complete, no resolved direction** -- the computation ran in
   full, but either the short/medium-window spreads point in opposite
   directions, or one of them falls below the 2.0pp `NOISE_FLOOR_PCT`
   threshold. This is itself an informative result (e.g., "no sustained
   divergence detected"), not a data problem. (Observed 2026-07-08: XAR,
   AIPO, MAGS -- all with empty quality_flags and real numeric spread
   values.)

Both used to produce the identical `rs_signal: "INCONCLUSIVE"`, with the
only distinguishing signal being whether `quality_flags` happened to be
empty -- an implicit, easy-to-miss distinction rather than an explicit one.

**Why this mattered specifically for this module:** the ~8-week shadow-mode
trial's entire purpose is to let real accumulated data determine whether
the trend signal has predictive value and whether it should ever gain
conflict-resolution authority over the EV engine (deliberately deferred,
per ENG-50/Project_Instructions_MCP.md's own NEVER-rule). The trial's
eventual hit-rate analysis (see the ENG-55 backtest note elsewhere in this
file: "MLPX 5 calls/60% hit rate ... DBMF/SGOL/SIVR 0 calls (100%
INCONCLUSIVE across all 15 windows each)") needed to distinguish "the
signal never had enough information to fire" from "the signal looked and
genuinely found nothing" -- these have very different implications for
whether the *signal design* is sound versus whether the *data pipeline*
needs more work. Conflating them risked either conclusion being drawn on
the wrong evidence.

**Decision (client-confirmed, coding session 2026-07-08):** direction (a)
from the original hand-off -- a fourth `TrendSignalCode` value,
`DATA_UNAVAILABLE`, distinct from `INCONCLUSIVE`, over option (b)'s
additive `data_complete: bool` field. Backfill today's one day of
`TrendSignalStore.json` history to match, rather than forward-only.

**Fix:**
- `types.py`: added `TrendSignalCode.DATA_UNAVAILABLE`.
- `trend_signal.py`: every branch that previously returned `INCONCLUSIVE`
  for a *missing input* (rather than a computed non-result) now returns
  `DATA_UNAVAILABLE` instead -- `evaluate_return_spread()`'s insufficient-
  window-history branch; `evaluate_own_trend_confirmed()`'s insufficient-
  own-price-history branch and its `macro_confirms is None` branch (own
  trend agreement is irrelevant here -- the confirmation gate itself never
  resolved, so no verdict is possible either way);
  `evaluate_all_trend_signals()`'s no-own-price-history branch and both
  RETURN_SPREAD/HYBRID comparator-missing branches. Genuine computed
  non-results (opposite-sign windows, sub-noise-floor spreads, a real
  `macro_confirms is False`) still correctly return `INCONCLUSIVE`
  unchanged.
- **Related bug found and fixed in the same code:** MLPX's (HYBRID mode)
  HY_OAS confirmation gate previously only special-cased `hy_confirms is
  False`. This meant `hy_confirms is None` (the gate itself unavailable --
  fewer than 2 valid HY_OAS readings) fell through with *no* downgrade at
  all, letting an unconfirmed STRENGTHENING/WEAKENING call from the Brent
  spread pass straight through as if it had been vetted. Separately, the
  old `code != INCONCLUSIVE` guard would have wrongly downgraded an
  already-`DATA_UNAVAILABLE` code (from insufficient windows) to
  `INCONCLUSIVE` on `hy_confirms is False`, implying a real computation
  had run when it hadn't. Both fixed by gating explicitly on `code` being
  a real `STRENGTHENING`/`WEAKENING` call before applying either
  confirmation-gate outcome (`None` → `DATA_UNAVAILABLE`, `False` →
  `INCONCLUSIVE`); an already-INCONCLUSIVE or DATA_UNAVAILABLE code from
  the Brent spread itself is left untouched, since there's no directional
  call to vet.
- `mcp_server.py`, `__main__.py`: docstrings/comments updated to document
  the 4th value and its meaning.
- `tools/backtest_trend_signal.py`'s `print_report()`: now reports
  `inconclusive` and `data_unavailable` as separate columns per ticker
  (previously one combined "inconclusive" bucket) -- this is the actual
  consumer this distinction exists for; the ENG-55 backtest note's "100%
  INCONCLUSIVE" read for DBMF/SGOL/SIVR was exactly the ambiguity this
  closes.
- `Project_Instructions_MCP.md` synced per its own mandatory-sync rule:
  the `advisor_evaluate_trend_signal` tool bullet, Step 7's
  TREND_ROTATION_SIGNAL briefing guidance (present DATA_UNAVAILABLE and
  INCONCLUSIVE reads as separate lines, not lumped together), and a new
  NEVER-rule against collapsing the two back together in a briefing.
- `TrendSignalStore.json`: backfilled the 3 affected 2026-07-08 entries
  (DBMF, SGOL, SIVR: `INCONCLUSIVE` → `DATA_UNAVAILABLE`). AIPO, COPX,
  MAGS, MLPX, XAR unaffected -- confirmed real computed reads, not missing
  input.
- **Unrelated pre-existing test bug discovered and fixed in the same
  commit:** `test_inconclusive_when_short_and_medium_windows_disagree_in_sign`
  built a 63-point fixture (`_linear(150,90,43) + _linear(90,100,21)[1:]`),
  one point short of the 64
  `evaluate_return_spread()`'s medium window (`MEDIUM_WINDOW_DAYS=63`)
  actually needs (`len >= window_days+1`). It was silently landing in the
  insufficient-history branch instead of the "windows computed and
  disagree" branch its name and comment describe -- invisible before this
  fix because both branches used to return the same `INCONCLUSIVE` value.
  Fixed to a 64-point fixture (44+20) so it now exercises what it claims
  to test; the ENG-60 fix is precisely what surfaced this, since the two
  branches now diverge.

**Verification:** 10 new tests across `test_stage3/test_trend_signal.py`
(missing-input vs. computed-non-result wiring for both modes, the MLPX
HY_OAS gating fix, the corrected 64-point fixture) and
`test_stage1/test_trend_signal_store.py` (DATA_UNAVAILABLE's
forward-outcome fill behaves identically to INCONCLUSIVE's -- no code
change needed there, confirmed by a dedicated regression test). Full
suite: 880 passed / 46 skipped / 0 failed. ENG-41's known live-data-
dependent flake (see its own entry) was not observed this run.

**Honesty note:** conflict-resolution authority (whether the trend signal
ever overrides EV) remains deliberately deferred to the 8-week trial
checkpoint, per ENG-50's own design -- this closes only the labeling
ambiguity flagged in the hand-off, not anything about what the signal is
allowed to do.

### ENG-63 — DBMF/SGOL/SIVR's Mode 2 confirmation gate conflated missing input with a computed no-agreement result
<!-- ITEM
Status:    CLOSED
Severity:  MEDIUM
Category:  bug
Opened:    2026-07-13
Closed:    2026-07-13
Area:      python/advisor/analysis/trend_signal.py (_agreement_gate,
           _dbmf_macro_confirms, evaluate_own_trend_confirmed,
           evaluate_all_trend_signals)
Related:   ENG-60 (the DATA_UNAVAILABLE-vs-INCONCLUSIVE split this
           carries one layer deeper), ENG-50/ENG-55
-->

**Description:** Live session finding, caught directly by Evgeny pushing
back on an initial hand-wave explanation: during the 2026-07-13 M05
session, `advisor_evaluate_trend_signal`'s CLI fallback reported DBMF,
SGOL, and SIVR as `DATA_UNAVAILABLE` ("real-yield/DXY agreement gate
unavailable this session" / "own_short or DXY_TREND unavailable").
Manually re-fetching `DXY_TREND` and `REAL_YIELD_10Y_TREND` independently,
three separate times, always returned clean, populated, zero-quality-flag
data. The bug was not in the fetch layer at all -- it was two layers
downstream, in how the Mode 2 (`OWN_TREND_CONFIRMED`) confirmation-gate
helpers collapsed "the raw input was missing" and "the raw input was
present but `directional_trend()` legitimately computed no resolved
direction" into the identical `None` return value.

Two distinct mechanisms were found by live-tracing this session's actual
data, not by inspection alone:

1. **SGOL/SIVR** (`_agreement_gate`): the session's `REAL_YIELD_10Y_TREND`
   series `[2.16, 2.07, 2.19, 2.17, 2.21, 2.18, 2.26, 2.32]` has a
   materially strong net move (+7.4%, well past the 2.0pp
   `NOISE_FLOOR_PCT`), but `directional_trend()` also requires that no
   later close ever drop back below the window's *first* value, or it
   calls the whole move a "reversal" and returns `None`. Week 2 (2.07)
   dipped fractionally below week 1 (2.16) before the series climbed hard
   and stayed up -- a real, sustained, materially-strengthening trend
   nulled by one small wobble right at the start.
2. **DBMF** (`_dbmf_macro_confirms`): a different, more mundane cause --
   its own trailing 21-day price only moved +0.57% (30.62 -> 30.80),
   genuinely below the 2.0pp materiality floor. Not missing data; DBMF
   just hadn't moved enough to call a direction.

Both produced the same "unavailable this session" flag text and the same
`DATA_UNAVAILABLE` code, even though both were real, valid computations
on complete data -- exactly the ENG-60 DATA_UNAVAILABLE-vs-INCONCLUSIVE
distinction, just one layer deeper than where ENG-60 originally drew it.

**Fix:**
- `_agreement_gate()`: now returns `(confirms, data_available)` instead of
  a bare `Optional[bool]`. `data_available=False` only when either raw
  series itself is missing/empty; `True` whenever both raw series were
  present, regardless of whether `directional_trend()` resolved a
  direction for either.
- `_dbmf_macro_confirms()`: now takes an explicit
  `own_short_data_available: bool` from the caller (which holds DBMF's
  raw own-price history and already knows whether it was long enough for
  a short-window read) and returns `(confirms, flags, data_available)`.
  `data_available=False` only for a missing `DXY_TREND` series or
  insufficient own-price history; `True` for every other `None` case (own
  short-window indeterminate on sufficient data, or DXY's own direction
  indeterminate on present data).
- `evaluate_own_trend_confirmed()`: new `confirm_data_available: bool =
  False` parameter (default preserves old behavior for any caller that
  doesn't pass it). When `macro_confirms is None`: `confirm_data_available
  =True` now returns `INCONCLUSIVE` ("macro confirmation gate computed no
  clear agreement this session"); `False` still returns `DATA_UNAVAILABLE`
  ("macro confirmation input unavailable this session") exactly as
  before.
- `evaluate_all_trend_signals()`'s `OWN_TREND_CONFIRMED` branch: both the
  DBMF and SGOL/SIVR call sites updated to compute and thread
  `confirm_data_available` through to `evaluate_own_trend_confirmed()`,
  with matching flag text for each case.

**Verification:** 3 existing tests updated for the new tuple/parameter
signatures (no change to what they actually assert); 9 new tests added --
unit-level coverage for both gates' missing-vs-indeterminate split, plus
two end-to-end `evaluate_all_trend_signals()` regression tests
reproducing this session's exact SGOL scenario (real, present,
reversal-nulled real-yield data -> `INCONCLUSIVE`) and its contrast case
(genuinely absent real-yield data -> `DATA_UNAVAILABLE`, unchanged). Full
suite: 896 passed / 46 skipped / 0 failed -- confirmed via direct re-run,
zero regressions.

**Honesty note:** whether `directional_trend()`'s "no reversal through the
window's starting value" rule is itself too strict (a small early wobble
nulling an otherwise-clear multi-week trend) is a separate, open design
question, not addressed here -- this fix only ensures that whatever
`directional_trend()` decides gets labeled correctly (`INCONCLUSIVE` vs
`DATA_UNAVAILABLE`), not that the underlying rule is the right one. Worth
a dedicated look once the 8-week shadow trial has enough real outcome
data to judge it against -- same posture as `NOISE_FLOOR_PCT` itself
(flagged as a placeholder since ENG-55).

### ENG-64 — advisor_run_computation / advisor_evaluate_trend_signal: hard timeout with no polling/job-status mechanism
<!-- ITEM
Status:    OPEN
Severity:  MEDIUM
Category:  architecture
Opened:    2026-07-13
Area:      python/advisor/mcp_server.py (_tool_run_computation,
           _tool_evaluate_trend_signal, their _with_timeout() wrapper)
Related:   ENG-33 (the underlying client-transport hang these tools
           guard against), ENG-40 (the per-spec timeout inside
           fetch_all() these MCP-level timeouts sit on top of)
-->

**Description:** Raised by Evgeny during the 2026-07-13 M05 session,
after both `advisor_run_computation()` (180s ceiling) and
`advisor_evaluate_trend_signal()` (60s ceiling) hit their hard timeout in
the same session -- both later confirmed via the CLI fallback to be
ENG-33-style client-transport hangs, not slow computation (both CLI
calls returned in well under 15s on identical data). The concern: a
single hardcoded timeout-then-fail call gives Claude no way to
distinguish "still working, just slow" from "genuinely stuck," and no way
to check in incrementally on a longer-running call rather than either
waiting blind or failing outright. This will only get more visible as
live data volume grows (a slower external fetch is a *when*, not an
*if*).

Client-side, the CLI fallback used via Desktop Commander's
`start_process`/`read_process_output` already behaves like real polling
(no fixed ceiling -- can be re-polled indefinitely for as long as the
subprocess is genuinely still running); the gap is specific to the two
in-process MCP tool calls themselves, which are single synchronous
requests with no exposed intermediate state to poll.

**Suggested next step:** have `advisor_run_computation()` and
`advisor_evaluate_trend_signal()` kick off their work as a background job
(thread or subprocess) and return immediately with
`{"status": "IN_PROGRESS", "job_id": ...}`; add a new MCP tool (e.g.
`advisor_check_job(job_id)`) that Claude can poll for completion,
mirroring the pattern Desktop Commander's own `start_process` +
`read_process_output` already uses. Needs its own dedicated coding
session -- touches both tools' registration in `mcp_server.py` and
introduces genuinely new job-lifecycle state (in-memory job registry,
cleanup/expiry policy for abandoned jobs), not a small patch.

### ENG-65 — directional_trend()'s unconditional "no reversal" veto suppressed real, material trends across every module that uses it
<!-- ITEM
Status:    CLOSED
Severity:  HIGH
Category:  bug
Opened:    2026-07-13
Closed:    2026-07-13
Area:      python/advisor/analysis/trend.py (directional_trend,
           mean_reversion_mode), python/advisor/analysis/thesis.py
           (DBMF's two §13 call sites), python/advisor/analysis/
           trend_signal.py (_dbmf_macro_confirms's breadth check)
Related:   ENG-63 (found while investigating this), ENG-13 (original
           trend.py build), ENG-55 (trend/rotation layer design)
-->

**Description:** Direct follow-on from ENG-63, raised by Evgeny after
noticing gold (SGOL) and silver (SIVR) were still reporting INCONCLUSIVE
despite visibly, materially declining. Live-tracing SGOL/SIVR's actual own
daily closes showed both were genuinely down -13.89%/-21.06% over the
63-day window and -3.53%/-8.50% over 21 days — well past any reasonable
materiality floor — but `directional_trend()`'s "no later close may cross
back through the window's own starting value" rule was nulling the read,
because both series ticked up briefly a few days after the window opened
before their sustained decline resumed.

Checked how widely this rule is actually used before touching anything:
`analysis/thesis.py` (M09/M10 §13 sustaining conditions, live, not
shadow-mode) and `analysis/range_position.py` (GAP-16's real-yield/DXY
gate, feeding `range_position_advisories` on every real session) both
depend on the same primitive, not just the ENG-55 trend/rotation layer.

Checked whether the "no reversal" rule was itself a mistake or
intentional: it is NOT a bug in the sense of an oversight.
`Calibration_State.md` 13 documents DBMF's own sustaining condition
word-for-word: *"directional = net move >= 8% in one direction without
full reversal"* — `directional_trend()` was built to implement that exact
sentence (see the original ENG-13 test comment: *"DBMF's own text
requires 'without full reversal'"*), then reused as the GENERAL
"is this trending" definition across every other caller, none of which
have any documented text requiring that behavior. Grepped
`Calibration_State.md` for every occurrence of "reversal" to confirm: the
phrase appears exactly once, in DBMF's own 13 block. Every other
condition (SGOL/SIVR's DXY-appreciation check, URA's uranium trend, COPX's
copper trend, GAP-16's real-yield/DXY gate, every instrument's own-price
trend in the ENG-55 layer) inherited the veto as an unintended side effect
of sharing the function, not because their own documented text asked for
it.

**Decision (client-directed, live session):** this is two genuinely
separate layers that had been conflated — a data-driven, instrument-
agnostic trend calculation (should be one standard method, used
identically everywhere) versus a strategy-specific consumption rule
(DBMF's own documented macro-breadth condition, which legitimately wants
the stricter "no reversal" reading since DBMF is a `systematic_trend_
following` strategy fund, and a choppy/reversing macro backdrop genuinely
undermines its own thesis — see `Calibration_State.md` 13's
`systematic_trend_following` note). Client's framing, confirmed correct
against the code: DBMF's OWN price should get the same plain trend
treatment as any other instrument; only the breadth condition that checks
OTHER markets as a strategy-backdrop proxy should keep the stricter
reading.

**Fix:**
- `directional_trend()`: new `require_no_reversal: bool = False`
  parameter. Default is now plain time-series momentum — sign of
  `net_change_pct` over the window, gated by the materiality threshold,
  full stop (the same baseline "sign of trailing return" measure used in
  time-series-momentum trend-following research/practice). The path taken
  to get there no longer matters — only the net outcome. `require_no_
  reversal=True` restores the exact old behavior byte-for-byte, as an
  explicit, documented opt-in.
- `mean_reversion_mode()`: threads the same parameter through (it's a
  logical negation of `directional_trend()`).
- `thesis.py`'s two DBMF 13 call sites (the "trending directionally"
  sustaining condition and the "mean-reversion mode" failure condition):
  updated to pass `require_no_reversal=True` — DBMF's own documented text
  is preserved exactly, byte-for-byte.
- `trend_signal.py`'s `_dbmf_macro_confirms`: its breadth check (`dxy_dir`
  and the Brent/Gold/S&P breadth loop) also passes `require_no_
  reversal=True` internally — its own docstring already describes this as
  "exact reuse of the breadth concept GAP-16/13 already defined for
  DBMF," so it keeps the same documented semantics for consistency. DBMF's
  OWN price trend (`own_short`/`own_medium`, computed by the caller) does
  NOT get this flag — it's a plain instrument read, same as any other
  ticker.
- Every other caller (SGOL/SIVR's own price and DXY-appreciation checks,
  URA's uranium check, COPX's copper checks, MLPX's Brent-floor check,
  GAP-16's real-yield/DXY gate, every Mode-1/Mode-2 instrument-level trend
  read in the ENG-55 layer) needed NO code change — they automatically get
  the corrected, standard behavior via the new default.

**Live impact:** SGOL and SIVR now correctly resolve to a real, confirmed
WEAKENING signal on 2026-07-13's actual data (own_short=down,
own_medium=down, both agree, real-yield/DXY confirmation gate agrees) —
matching gold and silver's actual observed decline, instead of the
misleading INCONCLUSIVE both were reporting before. DBMF correctly stays
INCONCLUSIVE — its own trailing 21-day move is a genuine +0.57%, below the
materiality floor on its own merits, unrelated to the reversal rule.

**Verification:** checked every existing test in
`test_stage3/test_thesis.py` and `test_stage3/test_range_position.py`
before changing anything — none rely on reversal-veto-specific fixtures
(all monotonic or clearly-flat series), confirming this was safe to
change without touching those two modules' own tests. 7 new/updated tests
in `test_stage3/test_trend.py` (the default vs. opt-in behavior,
`mean_reversion_mode`'s threading), 5 new/updated in
`test_stage3/test_trend_signal.py` (the corrected `_agreement_gate`
outcome, an end-to-end SGOL regression using SGOL's real declining
closes, `_dbmf_macro_confirms`'s breadth check keeping the veto
internally, DBMF's own price NOT keeping it). Full suite: 900 passed / 46
skipped / 0 failed. Confirmed live against tonight's actual data via the
CLI fallback.

**Honesty note:** plain time-series momentum (sign of net change, no path
dependence) is the simplest, most standard baseline — not the most
sophisticated. A regression-slope-based measure (fitting a trend line
across the whole window, weighting every point rather than just the two
endpoints) would be more robust to single-day noise at either endpoint
and is a legitimate, common alternative; it wasn't adopted here because it
changes what "materiality" means (a projected slope-based move rather than
the literally observed net change) and is exactly the kind of judgment
call ENG-55 already carved out for its own dedicated session. Worth
revisiting once the 8-week shadow trial has real outcome data — same
posture already established for `NOISE_FLOOR_PCT`.

### ENG-66 — COPX's consecutive-months condition has no evaluator; audit reconfirms ENG-26/30/31/34
**CLOSED** 2026-07-14, COPX consecutive-months leg only (MEDIUM, functional-gap). A side finding from this item's audit (Allocation - Objectives sheet's floor_nominal_loss/concentration_cap column misread) is UNRESOLVED and not tracked under any ENG number — worth a fresh item. Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.

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
**CLOSED** 2026-07-14 (LOW, functional-gap). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.

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

### ENG-67 — C_check_brent auto-scorer can't distinguish "no supply event" from "verified event, price hasn't caught up"
**CLOSED** 2026-07-14 (MEDIUM, bug). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.


### ENG-68 — DBMF_3M_RETURN data reading returned MAGS's price series, not DBMF's
**CLOSED** 2026-07-21 (HIGH, data-integrity). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.

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
**CLOSED** 2026-07-14 (MEDIUM, functional-gap). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.


### ENG-31 — AIPO's hyperscaler capex §13 sustaining condition has no data source
**CLOSED** 2026-07-14 (LOW, functional-gap). Full description and resolution: see `FRAMEWORK_BACKLOG_ARCHIVE.md`.


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

**Fourth tool now showing the identical symptom (2026-07-08):**
`advisor_evaluate_trend_signal()` (the new ENG-57 tool) hung the full
~4-minute client ceiling twice in one advisory session, immediately after
`advisor_run_computation()` and `advisor_apply_scoring()` had both just
logged normally on the same connection. Checked `mcp-server-financial-advisor.log`
directly (the access this entry's 2026-06-24 breakthrough established):
zero `tools/call` entries appear for either hung attempt at all -- the gap
between the preceding `advisor_apply_scoring` response and the next logged
`tools/call` is ~37 minutes, comfortably enough to contain two silent
~4-minute client-side hangs plus normal conversation time in between. This
is the exact same "request never arrives" signature this entry already
established for `evaluate_allocation` -- not a new hypothesis, a fourth
confirmed occurrence of the same one. (Contrast ENG-58, opened the same
session: that one's `advisor_run_computation` hangs DID show up in the log,
with a clear server-side yfinance root cause -- a genuinely different
mechanism that happened to produce a superficially similar symptom.)

**CLI fallback built (2026-07-08, same session):** `python -m advisor
evaluate-trend-signal --json-file <path>` now exists, mirroring
`evaluate-allocation`'s. See `Project_Instructions_MCP.md`'s tool bullet
and Step 6c for usage; `python/tests/test_mcp/test_evaluate_trend_signal_cli.py`
for coverage. Building it surfaced a real, separate latent bug along the
way: `dominant_directive_conflict_aware` could carry a raw `DirectiveCode`
enum, which isn't JSON-serializable and was silently killing the entire
`TrendSignalStore.json` update on every session, live MCP path included --
not just the CLI path this item was ostensibly about. Fixed at the source
(normalized to `.value`/str in `_tool_evaluate_trend_signal`) plus a
`default=str` backstop in `trend_signal_store._save()`.

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
| GAP-17 | OPEN — approach decided v1.66 (flip-within-role, not split) | geopolitical_premium — XAR sign-question. Numbers not yet derived; LOW confidence, gated to March 31, 2027 audit at the earliest | Calibration_State.md §3/§6 item 46 |

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
