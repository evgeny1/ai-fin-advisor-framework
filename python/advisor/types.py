"""
FW_Types — Python translation of FW_Types.md (Framework Core shared contracts).
All modules consume and produce these types. No business logic here.
Stage 1 includes: DataSource, FetchSpec, DataReading, SessionType.
Stubs for Stage 3+ signal types included for import stability.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


# ── Enums ─────────────────────────────────────────────────────────────────────

class DataSource(Enum):
    FRED_SPREADSHEET_TAB          = "FRED_SPREADSHEET_TAB"
    ALLOCATION_SPREADSHEET_FINRA  = "ALLOCATION_SPREADSHEET_FINRA"
    ALLOCATION_SPREADSHEET_OTHER  = "ALLOCATION_SPREADSHEET_OTHER"
    YFINANCE                      = "YFINANCE"          # Python direct — was YFINANCE_MCP
    FMP_CHART                     = "FMP_CHART"
    FMP_ECONOMICS_TREASURY_RATES  = "FMP_ECONOMICS_TREASURY_RATES"
    FMP_COMMODITY                 = "FMP_COMMODITY"
    FMP_INDEXES                   = "FMP_INDEXES"
    GOOGLEFINANCE                 = "GOOGLEFINANCE"
    WEBSEARCH_T1                  = "WEBSEARCH_T1"
    WEBSEARCH_T2                  = "WEBSEARCH_T2"
    USDA_OR_AFBF                  = "USDA_OR_AFBF"
    FRED_OR_WEBSEARCH             = "FRED_OR_WEBSEARCH"
    MANUAL_CLIENT_INPUT           = "MANUAL_CLIENT_INPUT"


class UpdateFrequency(Enum):
    DAILY     = "DAILY"
    WEEKLY    = "WEEKLY"
    MONTHLY   = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    ON_DEMAND = "ON_DEMAND"   # fetch only when explicitly requested


class SessionType(Enum):
    FULL_DESKTOP    = "FULL_DESKTOP"     # Desktop Commander + git available
    READONLY_MOBILE = "READONLY_MOBILE"  # read + advisory only; no write-back


class SourceTier(Enum):
    T1 = "T1"
    T2 = "T2"
    T3 = "T3"


class Scenario(Enum):
    A = "A"; B = "B"; C = "C"; D = "D"; E = "E"; F = "F"


# ── Data Layer Types (Stage 1) ─────────────────────────────────────────────────

@dataclass
class FetchSpec:
    """Descriptor for one data series. Registered in m18_registry.py only."""
    id:                  str
    source:              DataSource
    description:         str
    update_frequency:    UpdateFrequency
    acceptable_lag_days: int
    consumer:            List[str] = field(default_factory=list)
    calibration_use:     Optional[str] = None


@dataclass
class DataReading:
    """Single fetched value produced by a fetcher and consumed by ANALYSIS_ENGINE."""
    spec_id:       str
    value:         Any              # float | dict | list — type depends on series
    source:        DataSource
    fetched_at:    datetime
    quality_flags: List[str] = field(default_factory=list)
    raw:           Optional[Any] = None   # original API response for debugging

    @property
    def is_valid(self) -> bool:
        return self.value is not None and not any(
            f.startswith(("FETCH_FAILED", "UNAVAILABLE")) for f in self.quality_flags
        )

    def flag(self, msg: str) -> "DataReading":
        self.quality_flags.append(msg)
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {
            "spec_id":       self.spec_id,
            "value":         self.value,
            "source":        self.source.value,
            "fetched_at":    self.fetched_at.isoformat(),
            "quality_flags": self.quality_flags,
        }


# ── Signal Types — stubs; fleshed out in Stage 3 ──────────────────────────────

@dataclass
class ScenarioProbabilities:
    A: float; B: float; C: float; D: float; E: float; F: float

    def __post_init__(self) -> None:
        total = self.A + self.B + self.C + self.D + self.E + self.F
        if abs(total - 100.0) > 0.01:
            raise ValueError(f"Probabilities must sum to 100.0, got {total:.4f}")

    def as_dict(self) -> Dict[str, float]:
        return {s.value: getattr(self, s.value) for s in Scenario}


# ── Config Layer Types (Stage 2) ───────────────────────────────────────────────
# Parsed from Calibration_State.md and Session_Log.md.
# Consumed by Stage 3 analysis modules and Stage 4 portfolio math.

@dataclass
class ReturnRange:
    """One [conservative, upside] return range for a role × scenario cell (§4.1)."""
    conservative: float   # lower bound — used in ALL EV computations
    upside: float         # upper bound — disclosed in briefing only
    confidence: str       # "HIGH" | "PENDING_MEDIUM" | "PENDING_LOW" | "MEDIUM" | "UNKNOWN"


@dataclass
class ComponentWeight:
    """One role-weight pair in an instrument's ComponentVector (§11)."""
    role_id: str          # must match a role in §11.1 RoleRegistry
    weight: float         # fraction of NAV; UNCLASSIFIED portions excluded


@dataclass
class InstrumentEntry:
    """M15 classification entry for one ticker (§11.3 / §11.4)."""
    ticker: str
    components: List[ComponentWeight]
    tax_placement: str    # "ALL" | "RETIREMENT_ONLY"
    is_candidate: bool = False    # True for §11.4 instruments not yet allocated
    last_reviewed: Optional[str] = None  # ISO date string; M15 Check 5 staleness check


@dataclass
class ThresholdBlock:
    """§1 credit signal thresholds (relative to 180d trailing median)."""
    hy_stress_delta: int           # bps above median — fires HY_STRESS
    hy_recession_delta: int        # bps above median — fires HY_RECESSION
    hy_velocity_delta: int         # bps over prior 60 days (velocity overlay)
    hy_sustain_days: int           # trading days sustained
    ig_transmission_delta: int     # bps above median
    ig_velocity_delta: int         # bps over prior 60 days
    ig_sustain_days: int
    ccc_ratio_multiplier: float    # CCC widens N× composite over 30d
    ccc_absolute_floor_bps: int    # absolute floor for CCC divergence signal
    ccc_composite_ceiling_bps: int # composite must stay below this for CCC to fire


@dataclass
class MultiplierBlock:
    """§4.2 IRA and §4.3 Roth scenario target multipliers."""
    ira: Dict[str, float]   # scenario → multiplier (10-year horizon)
    roth: Dict[str, float]  # scenario → multiplier (15-year horizon)


@dataclass
class FloorParams:
    """§4.4 structural floor and concentration parameters."""
    base_floor: float                 # fraction e.g. 0.25
    min_floor_pct: float              # fraction of account e.g. 0.02
    concentration_cap: float          # single-position cap e.g. 0.40
    floor_loss_prob_threshold: float  # nominal loss prob floor e.g. 0.15


@dataclass
class RegimeBlock:
    """§9 M14 market regime thresholds."""
    commodity_fear_HIGH_energy_pct: float      # energy_90d threshold (%)
    commodity_fear_HIGH_vix_change: float      # VIX_change_90d_pts <= this (pts)
    commodity_fear_MOD_energy_pct: float
    commodity_fear_MOD_vix_change: float
    equity_div_HIGH_pct: float                 # broad_equity_30d threshold (%)
    equity_div_MOD_pct: float
    underweight_gap_trigger_pp: float          # §9.2 gap in percentage points
    appreciation_trigger_30d_pct: float        # §9.2 30d appreciation %
    entry_extension_thresholds: Dict[str, Optional[float]]  # role → % or None
    move_elevated: float    # §9.4: 80
    move_stress: float      # 100
    move_crisis: float      # 130
    move_systemic: float    # 160


@dataclass
class CascadeBlock:
    """§12 M17 systemic cascade warning thresholds."""
    farm_filings_alert_pct: float    # §12.1: % YoY
    natgas_alert_price: float        # $/mmBtu
    fertilizer_alert_pct: float      # % above 12-mo avg
    kre_vs_spx_alert_pct: float      # §12.2: %
    sofr_dff_alert_bps: float        # bps
    sofr_dff_sustain_days: int       # trading days
    margin_mom_decline_pct: float    # §12.3: %
    gate_count_alert: int            # named fund gates in 90 days
    bankruptcy_watch_quarterly: int  # §12.4: filings/quarter
    bankruptcy_fires_quarterly: int  # filings/quarter
    e_term_premium_warning_bps: float  # §12.5
    e_term_premium_alert_bps: float
    e_30y_warning_pct: float


@dataclass
class CalibrationState:
    """Top-level typed container for all Calibration_State.md live config sections."""
    version: str
    last_updated: str                                # e.g. "June 10, 2026"
    thresholds: ThresholdBlock                       # §1
    return_table: Dict[str, Dict[str, ReturnRange]]  # §4.1: role → scenario → range
    multipliers: MultiplierBlock                     # §4.2 / §4.3
    floor_params: FloorParams                        # §4.4
    regime: RegimeBlock                              # §9
    roles: Dict[str, str]                            # §11.1: role_id → binding_driver
    instruments: Dict[str, InstrumentEntry]          # §11.3/§11.4: ticker → entry
    cascade: CascadeBlock                            # §12


# ── Session Log Types (Stage 2) ────────────────────────────────────────────────

@dataclass
class CreditReading:
    """One row from Session_Log.md §7 (credit spread observations)."""
    date: str
    hy_oas: Optional[int]
    ig_oas: Optional[int]
    ccc_oas: Optional[int]
    source: str
    t1_flag: str


@dataclass
class SessionStateEntry:
    """One block from Session_Log.md §8 (AUTHORITATIVE session state)."""
    date: str
    probabilities: ScenarioProbabilities
    primary_driver: str
    open_triggers: List[str]
    open_decisions: List[str]
    next_session_flags: List[str]
    calibration_changes: List[str]


@dataclass
class SessionLogState:
    """Complete parsed Session_Log.md."""
    credit_readings: List[CreditReading]
    scenario_states: List[SessionStateEntry]

    @property
    def latest_probs(self) -> Optional[ScenarioProbabilities]:
        """Most recent probability vector (§8 AUTHORITATIVE source)."""
        return self.scenario_states[-1].probabilities if self.scenario_states else None

    @property
    def prior_probs(self) -> Optional[ScenarioProbabilities]:
        """Second-most-recent vector — for 25pp cap enforcement."""
        return self.scenario_states[-2].probabilities if len(self.scenario_states) >= 2 else None

    @property
    def latest_open_triggers(self) -> List[str]:
        return self.scenario_states[-1].open_triggers if self.scenario_states else []

    @property
    def latest_open_decisions(self) -> List[str]:
        return self.scenario_states[-1].open_decisions if self.scenario_states else []

    @property
    def latest_next_flags(self) -> List[str]:
        return self.scenario_states[-1].next_session_flags if self.scenario_states else []


# ── Stage 3 Signal Types ───────────────────────────────────────────────────────
# Produced by analysis/ modules; consumed by portfolio/ and orchestrator/.


class DivergenceLevel(Enum):
    """M14 market regime divergence strength."""
    NONE           = "NONE"
    MODERATE       = "MODERATE"
    HIGH           = "HIGH"
    NOT_APPLICABLE = "NOT_APPLICABLE"   # equity check skipped (directive not reductive)


class CurveState(Enum):
    """M17 yield curve shape classification."""
    INVERTED         = "INVERTED"           # both 10Y-2Y and 10Y-3M negative
    PARTIAL_INVERSION = "PARTIAL_INVERSION" # one negative, one positive
    NORMAL_OR_STEEP  = "NORMAL_OR_STEEP"    # both positive


class DTimingSignal(Enum):
    """M17 D-scenario timing signal derived from yield curve shape."""
    MONITORING              = "MONITORING"
    CURVE_INVERTED          = "CURVE_INVERTED"
    RECESSION_ONSET_PATTERN = "RECESSION_ONSET_PATTERN"  # post-inversion re-steepening


class CascadeLevel(Enum):
    """M17 §5 pre-positioning rung."""
    MONITORING   = "MONITORING"
    ALERT        = "ALERT"
    PRE_POSITION = "PRE_POSITION"


class EWatchFlag(Enum):
    """M17 Scenario-E long-end elevation signal."""
    CLEAR                  = "CLEAR"
    FISCAL_STRESS_BUILDING = "FISCAL_STRESS_BUILDING"
    E_PATHWAY_WATCH        = "E_PATHWAY_WATCH"


class EPathwayType(Enum):
    """M17 v1.4: routes M10.ScenarioE directive conditional branch. Never feeds M03."""
    SYSTEMIC_LIQUIDITY = "SYSTEMIC_LIQUIDITY"   # 2008/LTCM analog — DXY strengthens
    RESERVE_EROSION    = "RESERVE_EROSION"       # de-dollarization analog — DXY weakens


class GuardResult(Enum):
    """M14 EntryExtensionGuard outcome for one (ticker, account) pair."""
    PASS   = "PASS"    # appreciation below threshold — ADD may proceed
    HALT   = "HALT"    # appreciation at or above threshold — STOP and show adjusted EVs
    EXEMPT = "EXEMPT"  # role has no entry extension threshold (N/A in §9.3)


@dataclass
class CreditSignal:
    """M11 credit spread analysis result. Produced by analysis/credit.py."""
    hy_oas:                  Optional[float]   # current bps; None if fetch failed
    hy_median_180d:          Optional[float]   # trailing 180d median bps; None if history absent
    ig_oas:                  Optional[float]
    ig_median_180d:          Optional[float]
    ccc_oas:                 Optional[float]
    move:                    Optional[float]
    # Threshold flags — False when data is insufficient to confirm True
    hy_stress_beginning:     bool              # M11 HY_StressBeginning threshold
    hy_recession_pricing:    bool              # M11 HY_RecessionPricing (→ D floor 25%)
    ig_transmission_reached: bool              # M11 IG_TransmissionReached
    ccc_tail_first_widening: bool              # M11 CCC_TailFirstWidening (monitoring)
    convergence_text:        str               # one-sentence SignalConvergenceTest summary
    quality_flags:           List[str]         # data gaps, partial evaluations


@dataclass
class DivergenceSignal:
    """M14 market regime divergence signal. Produced by analysis/regime.py."""
    commodity_fear_divergence:  DivergenceLevel
    equity_scenario_divergence: DivergenceLevel
    composite:                  DivergenceLevel
    energy_90d_change:          Optional[float]  # fraction (0.12 = +12% over 90 cal days)
    vix_change_90d_pts:         Optional[float]  # pts (VIX current − VIX 90d rolling avg)
    broad_equity_30d:           Optional[float]  # fraction (30 trading-day SPX/VTI return)
    quality_flags:              List[str]


@dataclass
class GuardStatus:
    """M14 EntryExtensionGuard result for one ticker. Produced by analysis/regime.py."""
    result:          GuardResult
    ticker:          str
    role_id:         Optional[str]
    appreciation:    Optional[float]              # fraction above 90d trailing avg
    threshold:       Optional[float]              # role threshold from §9.3 (as fraction)
    adjusted_returns: Optional[Dict[str, float]]  # scenario → (published_conservative − appreciation)
    flags:           List[str]


@dataclass
class YieldCurveSignal:
    """M17 §3 yield curve protocol result. Produced by analysis/cascade.py."""
    spread_10y_2y:    Optional[float]    # bps; positive = normal, negative = inverted
    spread_10y_3m:    Optional[float]    # bps
    curve_state:      Optional[CurveState]
    d_timing_signal:  DTimingSignal
    d_timing_estimate: Optional[str]     # narrative e.g. "0–12 months from re-steepening onset"
    term_premium:     Optional[float]    # THREEFYTP10 as percent (0.81 = 0.81%)
    e_watch_flag:     EWatchFlag
    yield_30y:        Optional[float]    # percent (5.07 = 5.07%)
    e_pathway_type:   EPathwayType
    quality_flags:    List[str]


@dataclass
class CascadeSignal:
    """M17 systemic cascade early warning result. Produced by analysis/cascade.py."""
    level:               CascadeLevel
    sector_stress_score: int                 # 0–3 (M17 §2 formal sectorStressScore)
    chain_fires:         Dict[str, bool]     # "CHAIN_1".."CHAIN_4" → firing (score +1)
    chain_watch:         Dict[str, bool]     # "CHAIN_3" → WATCH (precursor loaded; score 0)
    active_chains_count: int                 # count of chains at FIRES level
    yield_curve:         "YieldCurveSignal"
    quality_flags:       List[str]


# ── M03 AI Boundary Contract (Stage 3) ────────────────────────────────────────
# Python builds ScoringQuestion list from M03 check definitions + DataReadings.
# AI fills ScoringAnswers. Python runs all arithmetic from there.

@dataclass
class ScoringQuestion:
    """One AI scoring prompt unit for M03.DeriveScenarioProbabilities."""
    id:           str        # e.g. "A_check_fed", "B_check_cpi"
    scenario:     str        # "A".."F"
    question:     str        # natural-language question for AI
    evidence:     str        # pre-rendered from DataReadings
    valid_scores: List[int]  # valid integer answers e.g. [0,1,2] or [0,3]


@dataclass
class ScoringAnswers:
    """AI-filled scores corresponding to a ScoringQuestion list."""
    answers:   Dict[str, int]   # question_id → score integer
    reasoning: Dict[str, str]   # question_id → one-sentence rationale


@dataclass
class RawScores:
    """Unprocessed scenario scores from M03 before normalization."""
    A: float; B: float; C: float; D: float; E: float; F: float

    def as_dict(self) -> Dict[str, float]:
        return {"A": self.A, "B": self.B, "C": self.C,
                "D": self.D, "E": self.E, "F": self.F}

    @property
    def total(self) -> float:
        return self.A + self.B + self.C + self.D + self.E + self.F
