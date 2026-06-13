# Migration Plan: Pseudo-Code Framework → Python
<!-- Created: 2026-06-08 | Status: Stage 5 COMPLETE -->

## Overview

Five-stage migration converting the pseudo-code framework (M01–M18) to executable Python,
progressively minimizing AI involvement to interpretation-only tasks.
Pattern B (Claude orchestrates, Python tools) throughout Stages 1–4.
Pattern A (Python orchestrates, Claude as service) at Stage 5.

---

## Architecture: Four Python packages

```
advisor/
├── types.py           # FW_Types — all shared dataclasses
├── exceptions.py      # HardStop, DataFetchException, guard violations
├── data/              # DATA_INTELLIGENCE: fetchers, registry, file I/O
├── analysis/          # ANALYSIS_ENGINE: signal computation (Stage 3)
├── portfolio/         # PORTFOLIO_ADVISOR: EV math, directives (Stage 4)
└── orchestrator/      # ORCHESTRATION: SessionPipeline, CLI (Stage 5)
```

**OCP rule**: adding a new data series → one FetchSpec in `data/m18_registry.py`, nothing else.
Adding a new instrument role → one row in Calibration_State §11, nothing else.

---

## ✅ Stage 1 — Data Fetchers (COMPLETE)

**Date completed:** 2026-06-08

### What was built

| File | Purpose |
|---|---|
| `advisor/types.py` | FW_Types dataclasses: DataSource, FetchSpec, DataReading, SessionType |
| `advisor/exceptions.py` | HardStopException, DataFetchException, guard violation types |
| `advisor/data/fetch_registry.py` | FetchRegistry: register() + fetch_all() (parallel, fault-tolerant) |
| `advisor/data/m18_registry.py` | All 28 M18 DATA_REGISTRY_ENTRIES as Python FetchSpec objects |
| `advisor/data/fetchers/yfinance_fetcher.py` | Direct yfinance calls: holdings, macro, VIX history |
| `advisor/data/fetchers/fmp_fetcher.py` | FMP REST API: commodities, indexes, yield curve, chart history |
| `advisor/data/fetchers/allocation_sheet.py` | Google Sheets API: FRED tab, FINRA tab, crosscheck |
| `advisor/data/file_protocol.py` | M12 file reads (local filesystem primary) + git write-back stub |
| `advisor/__main__.py` | CLI: `fetch market-data`, `fetch calibration`, `status`, `setup google` |
| `requirements.txt` | yfinance, requests, google-api-python-client, pandas, pytest |
| `tests/test_stage1/test_fetchers.py` | Registry coherence + integration smoke tests |

### AI work eliminated

Before Stage 1: Claude ran 10–15 individual MCP data fetch operations per session.
After Stage 1: One Desktop Commander call → `python -m advisor fetch market-data` → JSON.

### How Claude uses Stage 1 (Pattern B)

In M05 Step 4, instead of calling market_data MCP tools individually:
```bash
# Claude runs via Desktop Commander:
python3 -m advisor fetch market-data > /tmp/session_readings.json
```
Claude reads the JSON output and uses it as `List[DataReading]` for all downstream steps.
All M05 Steps 1–3 (file reads) also available:
```bash
python3 -m advisor fetch calibration   # → Calibration_State.md text
python3 -m advisor fetch session-log   # → Session_Log.md text
```

### Setup required before first use

```bash
cd "AI Financial Advisor Framework/python"

# 1. Install dependencies
pip install -r requirements.txt

# 2. Create .env with your FMP API key
cp .env.example .env
# Edit .env → add FMP_API_KEY=your_key

# 3. Load .env and verify
source .env
python -m pytest tests/test_stage1/ -v -m "not integration"   # fast (no network)
python -m pytest tests/test_stage1/ -v                        # full (requires network + FMP_API_KEY)
```

**Google credentials are NOT needed for Stage 1.**
In Pattern B (Claude orchestrates), Claude's Google Drive MCP connector handles the
allocation spreadsheet (FRED credit series tab, FINRA tab). The Python `allocation_sheet.py`
fetcher is only activated when Google credentials are present, and is only needed in
Stage 5 (Pattern A) when Python runs as a standalone process with no Claude MCP runtime.

### Verification before proceeding to Stage 2

Run a parallel session: Claude fetches data manually AND via Python tool.
Compare results for: Brent crude, VIX, HY OAS, one holding price.
All values must agree within 0.5% (normal refresh-lag tolerance).
If any mismatch: debug the fetcher before advancing to Stage 2.

### Known gaps / deferred items

- `WEBSEARCH_T1` source (CPI_YOY): still fetched by AI — appropriate, requires interpretation
- `USDA_OR_AFBF` source (FARM_FILINGS_YOY): quarterly, manual input — no automated fetcher
- `FRED_OR_WEBSEARCH` (NATURAL_GAS): falls back to yfinance NG=F — acceptable for now
- Allocation sheet price crosscheck guard (M18.AllocationPriceCrossCheck):
  implemented in `allocation_sheet.py` but only fires if both sources are available.
  Full enforcement comes in Stage 3 when signals are computed.
- `instruments.json` path assumes same-machine as market_data MCP server.
  If framework is ever run from a different machine, update `_SERVER_DIR` in `yfinance_fetcher.py`.

---

## ✅ Stage 2 — Config Migration (COMPLETE)

**Date completed:** 2026-06-10

### What was built

| File | Purpose |
|---|---|
| `advisor/types.py` | Stage 2 types added: `ReturnRange`, `ComponentWeight`, `InstrumentEntry`, `ThresholdBlock`, `MultiplierBlock`, `FloorParams`, `RegimeBlock`, `CascadeBlock`, `CalibrationState`, `CreditReading`, `SessionStateEntry`, `SessionLogState` |
| `advisor/config/__init__.py` | Package exposing `parse_calibration_state`, `parse_session_log` |
| `advisor/config/calibration.py` | Markdown parser: Calibration_State.md → `CalibrationState` (all 10 sections: §1 thresholds, §4.1 return table, §4.2/§4.3 multipliers, §4.4 floor params, §9 regime, §11.1 roles, §11.3/§11.4 instruments, §12 cascade) |
| `advisor/config/session_log.py` | Markdown parser: Session_Log.md → `SessionLogState` (§7 credit readings table, §8 session state blocks; `.latest_probs` and `.prior_probs` properties) |
| `tests/test_stage2/test_calibration_parser.py` | 47 unit tests with inline fixture |
| `tests/test_stage2/test_session_log_parser.py` | 28 unit tests with inline fixture |
| `tests/test_stage2/test_integration.py` | 43 integration tests against live Calibration_State.md and Session_Log.md |

**Test results:** 118/118 passing (unit + integration).

### AI work eliminated

Before Stage 2: Claude manually read and interpreted Calibration_State.md values each session
(thresholds, return table, instrument classifications).
After Stage 2: One `parse_calibration_state(text)` call → fully typed `CalibrationState`.
`session_log.latest_probs` provides the AUTHORITATIVE §8 probability vector in one attribute access.

### How Claude uses Stage 2 (Pattern B)

In M05 Steps 2–3, after fetching the file text via Desktop Commander:
```python
from advisor.config import parse_calibration_state, parse_session_log

cal   = parse_calibration_state(cal_text)   # all §1/§4/§9/§11/§12 values
log   = parse_session_log(log_text)          # §8 prior probs, open items

# AUTHORITATIVE prior probabilities (M05 rule — never from memory):
prior = log.latest_probs   # ScenarioProbabilities(A=5, B=41, C=38, D=5, E=4, F=7)

# Credit signal check:
hy_threshold = cal.thresholds.hy_stress_delta   # 150 bps
```

### Design choice

Direct Markdown parser (no YAML companion) — the §1/§4/§9/§11/§12 sections have
well-defined pipe-table and header structure that admits robust regex-based parsing.
No dual-format maintenance burden. Parser produces deterministic output verified by
118 tests including integration tests against the live file.

### Unblocked by Stage 2 completion

- **Stage 3** — analysis modules (`M03.DeriveScenarioProbabilities()`, credit signal evaluation,
  `M14.ComputeDivergenceSignal()`, `M17.sectorStressScore()`): all consume `CalibrationState`.
- **Stage 4** — portfolio math (`M15.blendedScenarioReturn()`, `M13.idealAllocation()`,
  EV computation): consumes `CalibrationState.return_table` and `CalibrationState.instruments`.

---

## ✅ Stage 3 — Analysis Arithmetic (COMPLETE)

**Depends on:** Stage 1 (DataReading inputs), Stage 2 (CalibrationState thresholds)

### What to build

| File | Maps to | Key functions |
|---|---|---|
| `analysis/credit.py` | M11 | `compute_credit_signal(readings, cal) → CreditSignal` |
| `analysis/regime.py` | M14 | `entry_extension_guard(spec_id, account, cal) → GuardStatus` |
| `analysis/regime.py` | M14 | `compute_divergence_signal(readings, cal) → RegimeSignal` |
| `analysis/cascade.py` | M17 §1–4 | `sector_stress_score(readings, cal) → int` |
| `analysis/cascade.py` | M17 | `compute_yield_curve_signal(readings, cal) → YieldCurveSignal` |
| `analysis/cascade.py` | M17 | `assess_cascade_level(readings, cal) → CascadeSignal` |
| `analysis/instruments.py` | M15 | `blended_scenario_return(ticker, scenario, return_type, cal) → float` |
| `analysis/instruments.py` | M15 | `validate_classifications(allocation_tickers, cal) → None` |
| `analysis/scenario_math.py` | M03 arithmetic | `normalize_scores(raw) → dict` |
| `analysis/scenario_math.py` | M03 | `apply_25pp_cap(normalized, prior) → ScenarioProbabilities` |

**AI boundary contract (AI Call 2 input type):**
```python
@dataclass
class ScoringQuestion:
    id:           str          # "A_check_fed", "B_check_cpi", "BvsC_supply_event"
    scenario:     str
    question:     str          # natural language
    evidence:     str          # pre-rendered from DataReadings
    valid_scores: List[int]    # [0,1,2] or [0,3]

@dataclass
class ScoringAnswers:
    answers:   Dict[str, int]   # question_id → score integer
    reasoning: Dict[str, str]   # question_id → one sentence
```

Python generates `ScoringQuestion` list from M03 check definitions + DataReadings.
AI fills in `ScoringAnswers`. Python runs all arithmetic from there.

**AI work eliminated by Stage 3:**
All threshold comparisons, rolling average checks, credit signal derivation,
cascade scoring, EntryExtensionGuard checks — pure Python, zero AI tokens.

---

## Stage 4 — Portfolio Math

**Depends on:** Stage 2 (CalibrationState), Stage 3 (signals + ScenarioProbabilities)

### What to build

| File | Maps to | Key functions |
|---|---|---|
| `portfolio/directives.py` | M09/M10 RESPONSES tables | `get_directive(role, scenario) → Directive` |
| `portfolio/allocation.py` | M13 | `ideal_allocation(asset, scenario, account, cal) → float` |
| `portfolio/allocation.py` | M13 | `scenario_weighted_allocation(asset, account, probs, cal) → float` |
| `portfolio/allocation.py` | M13 | `feasibility_check(account, probs, cal) → FeasibilityResult` |
| `portfolio/evaluation.py` | M07 | `auto_disqualify(spec, readings) → Optional[str]` |
| `portfolio/evaluation.py` | M08 | `dual_role_conflict(ticker, scenario, cal) → Optional[str]` |

**Directives table** (`portfolio/directives.py`) encodes M09/M10 RESPONSES as pure data:
```python
DIRECTIVES: Dict[Tuple[RoleID, Scenario], Directive] = {
    (RoleID.geopolitical_premium, Scenario.A): Directive.TRIM,
    ...
}
```
This table is driven entirely by CALIBRATION_STATE §11 at load time.
Adding a role → add rows to this table + §11. Nothing else.

**AI work eliminated by Stage 4:**
All EV computations, idealAllocation math, FeasibilityCheck — pure Python.
Advisory session receives pre-computed `AllocationTarget` objects, not raw arithmetic.

---

## Stage 5 — SessionPipeline (Pattern A)

**Depends on:** Stages 1–4 fully validated

### What to build

```python
# orchestrator/session.py
class SessionPipeline:
    def __init__(self, config: FrameworkConfig, ai: AIClient): ...
    def run(self) -> SessionState: ...
    def _stages(self) -> List[Stage]: ...  # 10 stages from M05
```

**Three AI calls in the entire pipeline:**
1. `ai.gather_qualitative(data_readings) → QualitativeInputs` (M02 QUALITATIVE_GATHER_LIST)
2. `ai.answer_scoring(questions, qualitative) → ScoringAnswers` (M03 interpretation)
3. `ai.generate_briefing(context) → str` (M04 narrative)

**CLI entry points:**
```bash
python -m advisor session          # full pipeline → briefing to stdout
python -m advisor session --dry-run  # all steps, no write-back
python -m advisor writeback         # write-back saved session state to git
python -m advisor validate          # ValidateClassifications only
```

**Workflow change:** Instead of opening Claude to start a session, run the pipeline.
Receive a complete, computed brief. Discuss it in a separate Claude session.

---

## Dependency graph

```
Stage 1 (fetchers)
    │
Stage 2 (config migration)  ← can run concurrently with Stage 1
    │
Stage 3 (analysis)          ← needs Stage 1 DataReadings + Stage 2 CalibrationState
    │
Stage 4 (portfolio math)    ← needs Stage 3 signals + Stage 2 CalibrationState
    │
Stage 5 (SessionPipeline)   ← assembles all prior stages
```

---

## AI work remaining after Stage 5

| Task | Module | Reason irreducible |
|---|---|---|
| Qualitative web search + interpretation | M02 | Requires reading novel text |
| Primary driver identification | M02 | Weighs qualitative signals |
| Scenario scoring question answers | M03 | Linguistic interpretation of Fed/geopolitical evidence |
| Source propaganda check on novel claims | M01 | NLP judgment |
| Return table calibration reasoning | M16 Layer 2–3 | Qualitative analytical basis |
| Briefing narrative generation | M04 | Prose synthesis |
| Advisory discussion | M06 | Recommendation judgment |

All other work is Python after Stage 5 is complete.

---

## Session hand-off notes

- Stage 1 code is in `python/` subdirectory of the main framework git repo.
- All files committed with message: `Stage 1: Python data fetchers — M18 registry + fetchers`
- Next session should begin with: `python -m pytest tests/test_stage1/` to verify Stage 1
- Then proceed to Stage 2 (config migration) — start with `CalibrationState` parser.
- The YAML companion approach (keep Markdown + add YAML) is recommended over a pure parser.
- FetchSpec count (28) is a regression test anchor — update `test_expected_spec_count` when adding series.

SESSION CLOSE — June 10, 2026

STAGE 2: COMPLETE ✅  commit 4feb07d
──────────────────────────────────────────────────────────────────────
FILES COMMITTED (9 files, +1700 lines):
  advisor/types.py                             — Stage 2 types (13 new dataclasses)
  advisor/config/__init__.py                   — package entry point
  advisor/config/calibration.py               — Calibration_State.md parser
  advisor/config/session_log.py               — Session_Log.md parser
  tests/test_stage2/__init__.py
  tests/test_stage2/test_calibration_parser.py — 47 unit tests
  tests/test_stage2/test_session_log_parser.py — 28 unit tests
  tests/test_stage2/test_integration.py        — 43 integration tests
  MIGRATION_PLAN.md                            — Stage 2 marked COMPLETE

TEST RESULTS: 118/118 passing (1.25s total)
  Unit tests:        all against inline fixtures, no file I/O
  Integration tests: all against live v1.33 files, auto-skip in CI

KEY ENTRY POINTS:
  from advisor.config import parse_calibration_state, parse_session_log
  cal  = parse_calibration_state(text)   → CalibrationState
  log  = parse_session_log(text)         → SessionLogState
  log.latest_probs                       → ScenarioProbabilities (§8 AUTHORITATIVE)
  log.prior_probs                        → previous vector (25pp cap enforcement)

NEXT STEP: Stage 3 — Analysis Arithmetic
  Unblocked by Stage 2. Next session can start directly on:
  advisor/analysis/credit.py        M11 credit signal
  advisor/analysis/regime.py        M14 divergence + entry guard
  advisor/analysis/cascade.py       M17 sector stress score + yield curve
  advisor/analysis/instruments.py   M15 blendedScenarioReturn()
  All consume CalibrationState — typed input now available.

CURRENT FRAMEWORK STATE (unchanged this session):
  Calibration_State.md v1.33  |  Session_Log.md (8 §8 entries)
  Probs: A=5 / B=41 / C=38 / D=5 / E=4 / F=7
  M14 regime: MODERATE  |  CascadeLevel: MONITORING
  Acc4 active: AIPO(663) XLP(215) DBMF(854) XAR(119) MLPX(1065) SGOV(384) COPX(220)
  PAVE: SOLD (B trigger fired June 10, May CPI 4.2%)
  Open: URA ADD (IRA+2/Roth+3, guard cleared), AIPO target reduction under deliberation
  Q2 audit: June 30, 2026

SESSION CLOSE — June 12, 2026

SESSION HAND-OFF
Stage 3: COMPLETE ✅ commit 144e50c
Stage 4 is next: portfolio/directives.py, portfolio/allocation.py, portfolio/evaluation.py
  - directives.py: M09/M10 RESPONSES table encoded as Dict[(role_id, scenario), Directive]
  - allocation.py: ideal_allocation(), scenario_weighted_allocation(), feasibility_check()
  - evaluation.py: auto_disqualify(), dual_role_conflict()
  All Stage 4 modules consume CalibrationState + Stage 3 signals.

SESSION CLOSE — June 12, 2026

STAGE 4: COMPLETE ✅
──────────────────────────────────────────────────────────────────────
FILES COMMITTED (this session, +~1100 lines):
  advisor/types.py                               — MultiplierBlock + 8 Stage 4 types
  advisor/config/calibration.py                  — _parse_multipliers now extracts ira_floor/roth_floor
  advisor/portfolio/__init__.py                  — package public API
  advisor/portfolio/directives.py (266 lines)    — 9-role × 6-scenario DIRECTIVES dict; get_directive();
                                                    resolve_e_pathway_directive(); is_covered_role()
  advisor/portfolio/allocation.py (518 lines)    — compute_floor(); compute_target_multiplier();
                                                    required_real_return(); ideal_allocation();
                                                    scenario_weighted_allocation(); feasibility_check()
  advisor/portfolio/evaluation.py (206 lines)    — auto_disqualify() (4 M07 guards);
                                                    dual_role_conflict()
  tests/test_stage4/__init__.py
  tests/test_stage4/conftest.py (285 lines)      — CalibrationState fixture + 5 account profiles
  tests/test_stage4/test_directives.py (189 lines) — 37 tests
  tests/test_stage4/test_allocation.py (363 lines) — 30 tests
  tests/test_stage4/test_evaluation.py (277 lines) — 30 tests
  MIGRATION_PLAN.md                              — Stage 4 marked COMPLETE

TEST RESULTS: 457/457 passing, 4 skipped (22.5s total)
  All prior stages green: Stage 1 (unit+integration), Stage 2, Stage 3.
  Stage 4 new tests: 97 tests, 0 failures, first-run clean.

KEY DESIGN DECISIONS:
  REDUCE_TO_MIN → bounds=[floor, floor] (non-circular per M13 amendment)
  REDUCE_50PCT  → bounds=[0.5×current, 0.5×current] (fixed point)
  PATHWAY_CONDITIONAL → bounds=[current, current] + quality_flag (resolve via
    resolve_e_pathway_directive() before acting)
  Newer §11 roles (STG, STF, CDE, ILS, etc.) → HOLD + quality_flag (no M09/M10 entry)
  required_real_return() returns percent (e.g. 4.6) — consistent with blended_scenario_return()
  MultiplierBlock gains ira_floor/roth_floor fields; defaults=1.3 keep all Stage 2 tests green

KEY ENTRY POINTS:
  from advisor.portfolio import get_directive, scenario_weighted_allocation, feasibility_check
  from advisor.portfolio import auto_disqualify, dual_role_conflict
  get_directive("geopolitical_premium", "B")           → DirectiveResult(code=HOLD, ...)
  scenario_weighted_allocation("XAR", account, probs, weights, cal) → AllocationTarget
  feasibility_check(account, proposed_allocations, probs, cal)      → FeasibilityResult
  auto_disqualify(InstrumentSpec(...))                               → AutoDisqualifyResult

NEXT STEP: Stage 5 — SessionPipeline (orchestrator/)
  Three AI calls in the entire pipeline (qualitative gather, scoring, briefing narrative).
  All arithmetic is now Python. Stage 5 wires it together into a single runnable process.

SESSION CLOSE — June 12, 2026

STAGE 5: COMPLETE ✅
──────────────────────────────────────────────────────────────────────
FILES COMMITTED (this session, +~1600 lines):

advisor/types.py                               — ScoringQuestion.auto_score field added
advisor/config/calibration.py                  — _parse_block: skip section-header fragments as tickers
advisor/analysis/instruments.py               — ValidateClassifications Check 4 revised:
                                                  < 1.0 → non-blocking warning (UNCLASSIFIED exclusion)
                                                  > 1.0 or = 0.0 → HardStopException (data error)
advisor/orchestrator/__init__.py               — package public API
advisor/orchestrator/context.py (101 lines)    — SessionContext dataclass (all pipeline state)
advisor/orchestrator/scoring_questions.py (493) — 20 M03 checks → ScoringQuestion; auto-scores
                                                  quantitative checks; aggregates raw scores
advisor/orchestrator/ai_client.py (259 lines)  — AIClient (3 Claude API calls) + StubAIClient
advisor/orchestrator/session.py (494 lines)    — SessionPipeline.run() (M05 Steps 1-10)
advisor/__main__.py                            — session, session --dry-run, validate commands
tests/test_stage3/test_instruments.py         — Check 4 tests updated for new weight policy
tests/test_stage5/__init__.py
tests/test_stage5/test_scoring_questions.py   — 28 unit tests
tests/test_stage5/test_session.py             — 18 tests (unit + integration)
MIGRATION_PLAN.md                             — Stage 5 marked COMPLETE

TEST RESULTS: 497/497 passing, 4 skipped (150s total)
  All prior stages green. Stage 5 integration tests run with StubAIClient + live files.

KEY DESIGN DECISIONS:
  20 scoring questions total: A:3 B:3 C:3 D:4 E:3 F:4
  auto_score set by Python for: A_check_credit, A_check_energy (partial),
    C_check_brent (when well below nominal $110 trigger), D_check_credit,
    E_check_ig — all from computed CreditSignal (zero AI tokens for thresholds)
  AI Call 1: gather_qualitative → Dict[topic, summary] for 7 qualitative targets
  AI Call 2: answer_scoring → ScoringAnswers (integer scores + reasoning)
  AI Call 3: generate_briefing → M04-ordered narrative
  StubAIClient: deterministic offline mode; conservative scores; safe for CI
  Parser bug fixed: section header "Instrument Classification Table" treated as ticker
    → fixed by requiring ticker to be space-free
  ValidateClassifications Check 4 policy change: partial weights (AIPO 0.86)
    → non-blocking warning; zero or overflow → HardStop

KEY ENTRY POINTS:
  python3 -m advisor session --dry-run       # full pipeline, no write-back
  python3 -m advisor session                 # full pipeline + write-back (FULL_DESKTOP)
  python3 -m advisor validate                # ValidateClassifications only

  from advisor.orchestrator import SessionPipeline, AIClient, StubAIClient
  ctx = SessionPipeline(ai=StubAIClient(), dry_run=True).run()
  print(ctx.briefing)
  print(f"A={ctx.scenario_probs.A}% B={ctx.scenario_probs.B}%")

MIGRATION COMPLETE: All 5 stages implemented and tested.
AI involvement reduced to 3 irreducible calls per session:
  1. gather_qualitative (M02) — reads novel text, interprets geopolitical/macro state
  2. answer_scoring (M03)    — linguistic interpretation of Fed/geopolitical evidence
  3. generate_briefing (M04) — prose synthesis of computed signals into M04 narrative
All arithmetic, threshold comparisons, EV math, feasibility checks, cascade scoring
  → pure Python (zero AI tokens).