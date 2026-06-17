# README — AI Financial Advisor Framework (Engineering Onboarding)

**Audience:** coding sessions (Claude Code, or a human developer) working on
`python/advisor/` or the framework `.md` files. Not for advisory sessions —
advisory sessions use `Project_Instructions_MCP.md` and the M01-M19 module
files as Project Knowledge instead.

**Goal:** read this once at the start of a coding session and you should not
need to guess how anything is wired together, where logic lives, what's safe
to change, or what's already a known gap (see `FRAMEWORK_BACKLOG.md` for the
last one).

This file is paired with `FRAMEWORK_BACKLOG.md` (open engineering items) and
is itself **not** loaded as Project Knowledge during advisory sessions and
**not** part of `00_INDEX.md`'s `FILE_MAP`.

---

## 0. What this project actually is

A personal, rules-based financial advisory system for a multi-account ETF
portfolio (6 Schwab accounts: 4 the owner's, 2 a relative's, managed
together but never co-mingled in calculations). Two things are true at once,
and conflating them is the most common source of confusion:

1. **It is a Python MCP server.** `python/advisor/` is real, executable,
   tested code: market data fetchers, signal computation, scenario
   probability arithmetic, instrument classification, portfolio allocation
   math, and session write-back. This is the actual source of truth for
   *how a number gets computed*.
2. **It is also a pseudo-code specification framework** (`M01_*.md` through
   `M19_*.md`, `FW_Types.md`, `00_INDEX.md`) written to be read and executed
   *by an LLM* during advisory sessions — not by a computer. These files
   predate the Python implementation and are, by the framework owner's own
   description, **artifacts of the pre-MCP architecture, at least some of
   them.** A review of which modules still earn their place is explicitly
   planned (`FRAMEWORK_BACKLOG.md` → ENG-2). Do not assume a module `.md`
   file is still the executable source of truth for a given concern —
   check whether `python/advisor/` already owns it (see §2 below for how
   to tell).


---

## 1. The three layers

```
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 1 — Pseudo-code specification (advisory project knowledge) │
│   M01-M19_*.md, FW_Types.md, 00_INDEX.md                         │
│   Read by: Claude, during ADVISORY sessions only.                │
│   Status:  partially superseded by Layer 3. Review pending       │
│            (FRAMEWORK_BACKLOG.md ENG-2). Treat each module's      │
│            "is this still load-bearing" status as unverified     │
│            until that review happens.                            │
├─────────────────────────────────────────────────────────────────┤
│ LAYER 2 — Live data (mutable state, git-tracked)                 │
│   Calibration_State.md, Session_Log.md, Portfolio_State.md,      │
│   Calibration_Log.md, Archive_[Year]Q[N].md                      │
│   Read/written by: both advisory sessions (via MCP tools or      │
│            Desktop Commander) and python/advisor/ directly.       │
├─────────────────────────────────────────────────────────────────┤
│ LAYER 3 — Python implementation (executable, tested)              │
│   python/advisor/  — the real source of truth for HOW a number   │
│            gets computed. This is what a coding session edits.   │
└─────────────────────────────────────────────────────────────────┘
```

**Rule of thumb for "which file do I edit":**

| You're changing... | Edit |
|---|---|
| A threshold value, instrument's classification, calibration-dated number | `Calibration_State.md` (Layer 2) — never hardcode it in Python |
| How a signal/EV/probability is *computed* | The relevant `python/advisor/analysis/` or `portfolio/` file (Layer 3) |
| The *methodology* behind why a calibration value should be revised | `M16_ReturnTableCalibration.md` (Layer 1) — this one is genuinely still authoritative, it's a methodology doc an LLM applies, not something Python executes |
| What an MCP tool does, its signature, or what JSON it returns | `python/advisor/mcp_server.py` (Layer 3) — **then check `Project_Instructions_MCP.md`, see §9 below** |
| The session execution sequence (M05 steps) | `Project_Instructions_MCP.md` is what Claude actually reads; `M05_SessionInit.md` is the pseudo-code original — keep both in sync if you touch either |


---

## 2. Module (.md) ↔ Python file map

If you're unsure whether a module's logic has moved into Python, check this
table. "Python owns it" means the `.md` file is now closer to documentation
of intent than executable specification.

| Module | Python file(s) | Status |
|---|---|---|
| M01 Source Integrity | — (no Python equivalent) | AI-judgment-only |
| M02 Intel Gathering | `data/fetch_registry.py`, `data/m18_registry.py` | Python owns data fetching; qualitative gathering is AI-judgment-only |
| M03 Scenario Framework | `analysis/scenario_math.py` | Python owns the arithmetic; AI owns scoring-question interpretation |
| M04 Briefing Format | `mcp_server.py` (briefing assembly), `orchestrator/session.py` | Mostly Python now |
| M05 Session Init | `Project_Instructions_MCP.md` (Pattern B) / `orchestrator/session.py` (Pattern A) | Sequencing logic now lives outside the .md file |
| M06 Client & Advisory | — | AI-judgment-only (advisory principles, tax placement reasoning) |
| M07 Instrument Eval | `portfolio/evaluation.py` (`auto_disqualify`) | Python owns the mechanical checks |
| M08 Functional Roles | `portfolio/evaluation.py` (`dual_role_conflict`), `portfolio/directives.py` | Python owns conflict detection + directive lookup |
| M09/M10 Scenario Responses | `portfolio/directives.py` (`DIRECTIVES` table) | Python owns the table; AI owns applying it with judgment |
| M11 Credit & Calibration | `analysis/credit.py` | Python owns the signal computation |
| M12 Drive Protocol | `data/file_protocol.py` | Python owns file I/O; this doc governs the *rules*, Python does the *mechanics* |
| M13 Growth Objectives | `portfolio/allocation.py` | Python owns the math |
| M14 Market Regime | `analysis/regime.py` | Python owns divergence/guard computation |
| M15 Instrument Classification | `analysis/instruments.py` | Python owns `blendedScenarioReturn`, `classifyInstrument` |
| M16 Return Table Calibration | — | **AI-judgment-only, genuinely authoritative.** This is a methodology doc; the 4-layer procedure is applied by an LLM, not executed by Python |
| M17 Systemic Cascade Warning | `analysis/cascade.py` | Python owns sector stress / yield curve / cascade-level computation |
| M18 Market Data Fetch | `data/m18_registry.py`, `data/fetchers/` | Fully Python — this module is the registry-as-data pattern at its purest |
| M19 Thesis Sustaining Conditions | `analysis/thesis.py` | Python owns evaluation; §13 conditions are config consumed by it |
| FW_Types | `types.py` | Direct translation; keep both in sync if you add a type |

**Stage 4/Stage 5 naming** you'll see in code comments and test directory
names refers to the migration stages that built this table out — Stage 1
(fetchers) → Stage 2 (parsers) → Stage 3 (analysis) → Stage 4 (portfolio
math) → Stage 5 (orchestration, Pattern A). All are "complete" in the sense
that the code exists and is tested; Stage 5 specifically is not the active
execution path (see §4).


---

## 3. `python/advisor/` directory map

```
advisor/
├── __main__.py            CLI entry point. `python -m advisor <command>`.
│                           Commands: fetch market-data/calibration/session-log,
│                           status, setup google, session [--dry-run], validate,
│                           mcp-server (blocks; stdio transport for Claude Desktop)
├── mcp_server.py           Pattern B: the 3 MCP tools Claude calls directly.
│                           THE ACTIVE PRODUCTION PATH. See §4.
├── exceptions.py           HardStopException et al. — map 1:1 to pseudo-code's
│                           HARD_STOP / GUARD semantics.
├── types.py                FW_Types.md → Python. Every dataclass/enum the
│                           framework passes between layers lives here.
│
├── analysis/                ANALYSIS_ENGINE (Stage 3) — signal computation.
│   ├── credit.py            M11 CreditSignal
│   ├── regime.py             M14 divergence signal + EntryExtensionGuard
│   ├── cascade.py            M17 sector stress / yield curve / cascade level
│   ├── instruments.py        M15 classification + blendedScenarioReturn
│   ├── scenario_math.py       M03 probability arithmetic (normalize, floors,
│                              25pp session cap, B/C simultaneous check)
│   ├── floor_monitor.py       M13 CurrentHoldingsFloorCheck (FLOOR_THEN_RETURN
│                              accounts only — the two Relative accounts)
│   ├── thesis.py              M19 thesis sustaining condition evaluation
│   └── _utils.py              shared helpers
│
├── config/                  Parsers — Layer 2 text ↔ Layer 3 dataclasses.
│   ├── calibration.py        Calibration_State.md → CalibrationState
│   └── session_log.py        Session_Log.md → SessionLogState
│                              (§7 credit readings + §8 scenario states;
│                               see §8 of this README for the format this
│                               parser requires — getting it wrong is how
│                               ENG-1 happened)
│
├── data/                     DATA_INTELLIGENCE (Stage 1) — fetching.
│   ├── fetch_registry.py      FetchRegistry — THE extension point. Adding a
│                              new data series never touches any other file;
│                              register a FetchSpec in m18_registry.py only.
│   ├── m18_registry.py        Python translation of M18_MarketDataFetch.md's
│                              DATA_REGISTRY_ENTRIES.
│   ├── file_protocol.py       M12: read/write Calibration_State.md,
│                              Session_Log.md, Portfolio_State.md. Local
│                              filesystem primary, Google Drive fallback.
│                              `write_back()` lives here — FULL_DESKTOP-only
│                              guard, atomic 2-file git commit.
│   └── fetchers/
│       ├── yfinance_fetcher.py    single dispatcher for all YFINANCE specs
│       ├── fmp_fetcher.py          Financial Modeling Prep REST (currently
│                                  unused — 403 at this plan tier, see code
│                                  comments in __main__.py._build_registry)
│       ├── fred_fetcher.py         FRED REST (yield curve incl. 2Y)
│       └── allocation_sheet.py     Google Sheets reader (Pattern A only —
│                                  Pattern B uses Claude's Drive MCP connector
│                                  instead, see §4)
│
├── portfolio/                PORTFOLIO_ADVISOR (Stage 4) — EV math & rules.
│   ├── allocation.py          M13 ideal allocation, feasibility check
│   ├── directives.py          M09/M10 RESPONSES table as Python data
│   └── evaluation.py          M07 auto-disqualify, M08 dual-role conflict
│
└── orchestrator/             ORCHESTRATION (Stage 5) — Pattern A only.
    ├── session.py              SessionPipeline — M05 sequence as executable
                                 Python. NOT the active path (see §4).
    ├── context.py              SessionContext — full pipeline state
    ├── ai_client.py            AIClient (real Anthropic API calls) +
                                 StubAIClient (deterministic offline double)
    └── scoring_questions.py     M03 check definitions → ScoringQuestion
```

**Tests mirror this almost exactly** — see §8.


---

## 4. Two execution patterns — know which one you're touching

| | Pattern B (active) | Pattern A (Stage 5 target, not active) |
|---|---|---|
| Who orchestrates | Claude, via 3 MCP tool calls during a chat session | Python (`SessionPipeline.run()`) |
| Where AI calls happen | Implicit — the orchestrating Claude *is* the AI, no extra API call | 3 explicit calls to `https://api.anthropic.com/v1/messages` via `AIClient`, gated by `ANTHROPIC_API_KEY` |
| Entry point | `python -m advisor mcp-server` (stdio transport, registered in Claude Desktop config) | `python -m advisor session [--dry-run]` |
| Cost | Zero extra — uses the conversation Claude is already in | Costs a real API call per AI boundary |
| File: write-back | `mcp_server.py._tool_write_back()` | `orchestrator/session.py._append_session_log_entry()` |
| Test coverage | `tests/test_mcp/` (partial — see `FRAMEWORK_BACKLOG.md` ENG-10/11) | `tests/test_stage5/` (full pipeline tests via `StubAIClient`) |
| Known issues | No test of `_tool_run_computation`/`_tool_apply_scoring` (ENG-10) | `SessionContext` has no open_triggers/open_decisions field (ENG-4) |

**These two paths do not share code** for session write-back or briefing
rendering — each reimplements it. This already caused one bug to exist
twice independently (`FRAMEWORK_BACKLOG.md` ENG-1). Whether Pattern A
should keep being maintained, archived, or converged with Pattern B is an
open architectural decision (ENG-3) — **if you're about to add a feature to
one path, check whether the other path needs the same fix, and check
ENG-3 before investing heavily in Pattern A specifically.**

If you only remember one thing from this section: **Pattern B is what
actually runs in production right now.** Pattern A is tested and
functional but dormant. Bug fixes belong in both; new features belong in
Pattern B unless you've checked ENG-3 first.


---

## 5. Design principles (why the code looks the way it does)

These are load-bearing. Code that violates them will look "wrong" to
anyone who reads this framework's conventions, even if it runs correctly.

1. **Minimize AI to interpretation-only.** There are exactly three places
   an LLM's judgment is supposed to enter the pipeline ("AI boundaries"):
   M02 qualitative intel gathering, M03 scoring-question interpretation,
   M04 briefing narrative. Everything else — arithmetic, threshold
   comparisons, file I/O, data fetching — belongs in Python. If you find
   yourself wanting Claude to "decide" a number, that's a sign the logic
   belongs in `analysis/` or `portfolio/` instead, with Claude only
   supplying the qualitative input that feeds it.
2. **Open/closed principle throughout.** Adding a new data series, role,
   or instrument should mean adding a registry entry, never editing
   existing module/file logic. Concretely: new data series → `m18_registry.py`
   only; new instrument → `Calibration_State.md` §11 only; new briefing
   section → register a `BRIEFING_REGISTRY_ENTRY` in the owning module,
   never edit M04 directly.
3. **Python documents what/how; framework `.md` files document why/when.**
   No version tags, no `§section` references, no "Changes:"/"Updated:"
   comment lines in either — git log is the changelog (enforced for
   module `.md` files by `tools/validate_manifests.py`, see §7).
4. **Never hardcode instrument tickers or role names in code or module
   files.** They live in `CALIBRATION_STATE` §11 only.
5. **Forward EV (scenario-weighted expected value) is never conflated with
   realized gains.** If you're writing anything that touches both, keep
   them in visibly separate fields/variables.
6. **All arithmetic is auditable.** Scenario probabilities must sum to
   100; this is checked at multiple layers (`scenario_math.py`, the
   parser, `write_back()`'s guard) — don't remove a check because another
   layer "already" validates it. Redundant validation here is intentional
   defense in depth, not duplication to clean up.


---

## 6. File access & write protocol (M12)

**Reads:**
- Framework `.md` files (M01-M19, `Calibration_State.md`, `Session_Log.md`):
  local filesystem is primary (`file_protocol.framework_path()`, overridable
  via `ADVISOR_FRAMEWORK_PATH` env var — used heavily in tests to isolate
  from the real files, see §8). Google Drive API is the fallback if the
  local file is missing. **Never use `web_fetch` for these** — neither
  `raw.githubusercontent.com` nor `api.github.com` work reliably for this
  repo's egress setup, and Drive web URLs don't either.
- Allocation spreadsheet: Google Drive, searched by title every time
  (`title contains 'ETF Portfolio'`). **Never hardcode a file ID.**
- GitHub: read-only backup path only, via the GitHub MCP connector.

**Writes — this is the part most likely to bite you:**
- `Calibration_State.md`: **never** written by `advisor_write_back()` /
  `write_back()` (look at the call site — `calibration_state=None` is
  passed unconditionally). Calibration value changes go through manual
  edits + a separate git commit. This is intentional, not an oversight —
  don't "fix" it by wiring Calibration_State.md into write_back.
- `Session_Log.md` + `Portfolio_State.md`: written together, atomically, in
  one git commit, by `file_protocol.write_back()`. Guarded by
  `SessionType.FULL_DESKTOP` — raises `WriteBackGuardViolation` otherwise.
- `instruments.json`: written locally by the MCP server automatically.
  **Never push it to git.**
- **GitHub MCP is never used for writes** — only Desktop Commander + git,
  for both `.md` framework files and Python source. This rule predates
  the Python implementation and still applies to it.

**The format trap (read this before touching anything that writes
`Session_Log.md`):** `config/session_log.py`'s parser requires an exact
literal format — `---`-separated blocks, a `date:` line, and
`scenario_probabilities: { A: N%, B: N%, ... }`. This is not enforced by
any type system; it's regex matching against markdown text. Getting this
format wrong produces **no exception** — the entry is just silently
invisible to `latest_probs`/`prior_probs`. This exact failure mode shipped
to production once already (`FRAMEWORK_BACKLOG.md` ENG-1). See §8's
round-trip-testing rule before writing any code that touches this file.


---

## 7. Types, exceptions, and the module manifest schema

**`types.py`** is the direct Python translation of `FW_Types.md` — every
dataclass/enum passed between layers (analysis results, scenario types,
signals, scoring questions) lives here. If you add a new cross-module type,
add it to both files in the same change.

**`exceptions.py`** maps to the pseudo-code's `HARD_STOP`/`GUARD` semantics:

| Exception | Maps to |
|---|---|
| `HardStopException` | `HARD_STOP` — session cannot continue |
| `WriteBackGuardViolation` | a `GUARD` block violation specific to write-back |
| `ClassificationValidationError` | `ValidateClassifications()` HARD_STOP — instrument absent from §11 |
| `PriceDataIntegrityViolation` | M18's `NoWebSearchForPriceData` guard |
| `AllocationPriceCrossCheckFailure` | M18's price cross-check HALT (>5% discrepancy) |

**Module manifest schema:** every `M01-M19.md` file (and `FW_Types.md`) has
a required header:

```markdown
# M15 — Instrument Classification
<!-- Version: 1.0 | Updated: see git log -->

<!-- MODULE MANIFEST
  ID:              M15_InstrumentClassification
  Version:         1.0
  Sub-project:     ANALYSIS_ENGINE
  Reason to change: ...
  Inputs consumed:  ...
  Outputs produced: ...
  Calibration deps: ...
  Types consumed:   @see FW_Types.md — ...
-->
```

This is validated by `tools/validate_manifests.py` (standalone script,
also wired into `tests/test_framework/test_manifest_schema.py`). Run it
after editing any module file:

```bash
python tools/validate_manifests.py            # all files
python tools/validate_manifests.py M02 M11    # just these
```

It enforces: no stray "Changes:"/"Updated: <date>" comments (git log is
the changelog — per design principle 3 above), required fields present
and in order, `Sub-project` token is one of the six recognized values,
`Types consumed` starts with `@see FW_Types.md —` or `none`.

**This validator's pattern (schema + standalone script + pytest wrapper) is
a reasonable model if `FRAMEWORK_BACKLOG.md`'s `ITEM` manifest blocks ever
need automated checking** — not built yet, not currently planned, but
the precedent exists if it becomes worth it.


---

## 8. Testing — how this codebase defines its own test categories

**Run the suite** (working directory matters — `conftest.py` only fixes
`sys.path`, it doesn't change where pytest is invoked from):

```bash
cd python && python3 -m pytest -q          # full suite
python3 -m pytest tests/test_mcp/ -v       # one area, verbose
```

523 tests pass / 4 skip as of 2026-06-17 (the skips are `test_stage2`'s
`skip_if_missing`-guarded tests, which require the live framework files —
see ENG-12 below). No CI exists (`FRAMEWORK_BACKLOG.md` ENG-15) — running
this before every push is on you.

### The four kinds of test in this repo, and what each one is *for*

This codebase doesn't use "integration test" the way that phrase usually
gets used. Don't assume; here's what each directory and marker actually
means:

1. **Unit tests** (`test_stage1`, `test_stage3`, `test_stage4`) — pure
   functions, no file I/O, no network. `analysis/scenario_math.py`'s
   normalization logic, `portfolio/allocation.py`'s feasibility math, the
   yfinance dispatcher's parsing logic given a canned API response. Fast,
   deterministic, the bulk of the suite. **This is what you add for any
   new pure-computation function** (new signal, new role's EV math, a new
   guard's threshold logic).

2. **Parser / isolated-workflow tests** (`test_stage2`) — a single
   module's read or write logic in isolation, fed a known input, checked
   against a known output. `test_calibration_parser.py` and
   `test_session_log_parser.py` are pure parser tests (string in,
   dataclass out, no disk). `test_integration.py` (despite the filename)
   is the live-file-dependent exception — see the caveat below.

3. **Round-trip tests** (`test_mcp/test_write_back_format.py`, the
   analogous test in `test_stage5/test_session.py`) — **write, then
   re-parse, then assert.** This category didn't really exist before
   2026-06-17; it was added specifically because nothing else would have
   caught ENG-1. **Standing rule: any function that serializes data into
   a format this codebase later re-parses (Session_Log.md §8 entries, any
   future equivalent) must have a test that writes through the real
   function and re-parses with the real parser** — not a test that only
   checks the parser against a hand-written fixture, and not a test that
   only checks the writer "doesn't throw." Both of those passed for ENG-1
   right up until the bug shipped. The pattern to copy:
   `monkeypatch.setenv("ADVISOR_FRAMEWORK_PATH", str(tmp_path))`, seed a
   minimal valid file, call the real write function with `dry_run=True`,
   read the result back, parse it with the real parser, assert on the
   parsed structure (not the raw string).

4. **Pipeline / end-to-end tests** (`test_stage5/test_session.py`) — the
   *entire* session sequence run together, with the AI boundary stubbed
   (`StubAIClient`) so it's deterministic and free. This exists for
   Pattern A. **Pattern B (the active path) has no equivalent** —
   `FRAMEWORK_BACKLOG.md` ENG-11 is the single highest-value test
   currently missing from this repo. If you're adding a non-trivial
   feature to the Pattern B pipeline, strongly consider adding this test
   rather than only testing your one new piece in isolation — that's
   exactly the gap that let ENG-1 ship undetected through 497 passing
   tests.

### What `@pytest.mark.integration` means *here*

It is defined in `pytest.ini` as **"requires network access and API
credentials"** — not the general software-engineering sense of "tests
multiple components together." A test that exercises five modules but
needs no network is not marked `integration` in this repo; a single
function test that happens to hit yfinance live is. Don't be misled by
the name when deciding whether something needs this marker.

### Known testing gap: live-file-dependent assertions (ENG-12)

`test_stage2/test_integration.py` asserts hardcoded values read from the
**live, production** `Calibration_State.md`/`Session_Log.md` ("File has 8
full entries", specific probability values for "the latest session").
These tests are skipped automatically when the files aren't present
(`skip_if_missing`), but when they *are* present, they're asserting
against a moving target — fixing ENG-1 legitimately advanced the live
file's state and broke two of them, requiring a same-commit test update.
This is a known, accepted tradeoff for now (see ENG-12 for the proposed
fix — splitting structural smoke-checks from value-specific assertions
onto static fixtures). Until that's done: **if you change Session_Log.md
or Calibration_State.md content, expect to need to update
`test_stage2/test_integration.py`'s hardcoded expectations in the same
commit**, the same way the ENG-1 fix did. This is not a sign you broke
something; check whether the new expected value is actually correct
before just deleting the assertion.

### Practical guidance for new code

- New pure function → unit test, same directory pattern as its peers.
- New thing that reads or writes a framework `.md` file → parser test
  *and* a round-trip test if it writes something later re-parsed.
- New MCP tool, or non-trivial change to an existing one → add it to the
  Pattern B pipeline test once ENG-11 exists; until then, at minimum
  follow the isolated-temp-directory pattern from
  `test_write_back_format.py` rather than testing only against canned
  inputs with no file I/O at all.
- Changing anything in `Project_Instructions_MCP.md`'s described
  sequence → see §9, immediately below.


---

## 9. ⚠ Critical process rule: keeping `Project_Instructions_MCP.md` in sync

`Project_Instructions_MCP.md` is what actually tells the advisor (Claude,
in an advisory session) how to execute the framework — what to call, in
what order, with what arguments, and what's a hard stop versus a flag.
**It is not documentation of the code; it is itself an executable
specification that a different Claude instance, in a different
conversation, will follow literally.**

**Whenever you add or change anything in `python/advisor/` that affects:**
- an MCP tool's name, parameters, required vs. optional arguments, or
  return shape (`mcp_server.py`'s three `@srv.tool()` functions)
- the M05 session sequence — step order, what each step does, what
  triggers a stop
- any `NEVER` / `ALWAYS` rule's enforcement mechanism

**you must review `Project_Instructions_MCP.md` in the same change** and
update it if it now describes something the code no longer does, or omits
a new requirement the code now has.

**This already went wrong once and is the direct reason this rule is
called out this prominently:** the `advisor_write_back()` fix
(`FRAMEWORK_BACKLOG.md` ENG-1) added a required `session_type` parameter.
`Project_Instructions_MCP.md` Step 9 was updated in the same change — but
that update had to be done by hand, deliberately, as a separate edit; the
tool's docstring change did not propagate there automatically, and a
future advisory session reading a stale Step 9 would call the tool
missing a required argument and get an error with no immediately obvious
cause. There is no automated check for this drift. Treat it as a manual
checklist item on every change, not a "the docstring is updated so I'm
done" assumption.


---

## 10. Constraints & invariants most likely to bite a coding session

Pulled from across the framework's `NEVER`/`ALWAYS` rules — the subset
most relevant to writing or changing code, as opposed to running an
advisory session:

- Scenario probabilities (A-F) must always sum to exactly 100. Checked in
  `scenario_math.py`, the parser, and `write_back()`'s guard — keep all
  three checks if you touch any of them (design principle 6).
- `advisor_write_back()` / `write_back()` never writes `Calibration_State.md`
  — that's by design (§6 above), not a bug to fix.
- Never call `scenarioWeightedAllocation()`/`minimumConvictionWeight()`
  equivalents without an account context — these are per-account, not
  global.
- Never use direct §4.1 table lookups for scenario returns — route through
  `blended_scenario_return()` (M15 supersedes direct lookups).
- Never feed M14 regime signals, M17 yield-curve signals, or
  `e_pathway_type` into the M03 probability derivation — these are
  advisory/timing/routing signals only, by explicit design; the
  probability math and the regime/cascade math are deliberately kept
  decoupled.
- `ValidateClassifications()` hard-stops if an allocation instrument is
  absent from Calibration_State.md §11 — don't catch and suppress this
  error, it's a deliberate safety gate.
- Never hardcode a Google Drive file ID — search by title every time.
- `instruments.json` is local-only; never add it to a git commit.
- GitHub MCP is read-only in this framework, full stop — for `.md` files
  and for `python/advisor/` code alike. All writes go through Desktop
  Commander + git.
- MAGS-class tax-inefficiency rules (swap-structure instruments belong in
  retirement accounts only) are a portfolio/tax rule, not a code
  constraint — but if you're writing allocation logic, don't assume
  every instrument is taxable-account-eligible by default; check
  `Calibration_State.md` §11's tax placement notes.


---

## 11. Open architecture questions — check before making structural changes

Full detail in `FRAMEWORK_BACKLOG.md`. The two biggest open questions that
should change how you approach non-trivial work right now:

- **ENG-2 — module necessity review.** The framework owner is planning a
  review of whether all 19 `M*.md` files still need to exist now that
  `python/advisor/` implements most of their logic. If you're about to do
  substantial work on a module `.md` file, consider whether that effort
  is better spent once this review lands, or check with the framework
  owner first.
- **ENG-3 — Pattern A vs Pattern B.** Don't invest heavily in Pattern A
  (`orchestrator/`) features without checking this item — its future is
  an open decision, not a settled roadmap.

Everything else in the backlog is lower-stakes (test gaps, file hygiene,
documentation gaps) and can be picked up opportunistically.

---

## 12. Common tasks — quick cookbook

**Add a new market data series:** add a `FetchSpec` to `m18_registry.py`
only. No other file changes (open/closed principle, §5.2).

**Add a new instrument:** add it to `Calibration_State.md` §11.3 (and §11.1
if it needs a new role). Never add a ticker literal to `python/advisor/`
or any module `.md` file.

**Add a new MCP tool, or change an existing one's signature:** edit
`mcp_server.py` → update its docstring → **update
`Project_Instructions_MCP.md`** (§9 above, non-negotiable) → add/update
tests in `tests/test_mcp/` (round-trip if it writes anything re-parsed
later, §8 above) → run `python3 -m pytest -q` → commit.

**Add a new role / scenario return:** add to `Calibration_State.md` §4.1
and §11.1; consume via `blended_scenario_return()` — never a direct
table lookup (§10 above).

**Change anything in `Session_Log.md`'s or `Calibration_State.md`'s
format:** add/update a round-trip test (§8) before anything else; expect
to update `test_stage2/test_integration.py`'s hardcoded assertions in the
same commit (ENG-12); update `Project_Instructions_MCP.md` if the change
affects what Claude needs to do during a session.

**Edit a module `.md` file:** run
`python tools/validate_manifests.py <module-prefix>` after editing.
Don't add `<!-- Changes -->`/`<!-- Updated -->` comment lines — bump the
Version field in the manifest, put detail in the git commit message.

---

## 13. Glossary

| Term | Meaning |
|---|---|
| T1 / T2 / T3 | Source tiers (M01) — T1 = primary/official, T2 = secondary/reported, T3 = unverified/aggregator. Probability moves require T1. |
| HARD_STOP | Session cannot continue; maps to `HardStopException`. |
| GUARD | A hard constraint block — non-negotiable, no judgment calls. |
| EV | Expected value — scenario-weighted, never to be conflated with realized gains (design principle 5). |
| FLOOR_THEN_RETURN | An account type (the two Relative accounts) where a structural floor allocation takes precedence over return-optimal allocation. |
| ComponentVector | An instrument's decomposition into roles with weights (e.g. RAC 0.50 + IHC 0.50), the input to `blended_scenario_return()`. |
| RAC / IHC / STG / PDT / etc. | Role IDs — see `Calibration_State.md` §11.1 role registry for the current set; never hardcoded outside it. |
| Pattern A / Pattern B | See §4. A = Python orchestrates (Stage 5, dormant). B = Claude orchestrates via MCP (active). |
| §N (section N) | Refers to a numbered section inside `Calibration_State.md` or `Session_Log.md` — these numbers are load-bearing identifiers referenced throughout the codebase and module files, not just document structure. |
| ENG-N / GAP-N | Backlog item prefixes — see `FRAMEWORK_BACKLOG.md`. ENG = engineering, GAP = calibration/methodology. Different namespaces, don't reuse across them. |

---

*If you finish a coding session and learned something this document
should have told you, add it — that's the entire point of this file.*
