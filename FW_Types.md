# FW_Types — Framework Shared Type Definitions
<!-- Version: 1.3 | Updated: see git log -->

<!-- MODULE MANIFEST
  ID:              FW_Types
  Version:         1.3
  Sub-project:     FRAMEWORK_CORE
  Reason to change: a new shared contract is needed (rare).
                    NEVER add business logic here — types only.
  Inputs consumed:  none — this file defines contracts; it does not consume them
  Outputs produced: shared type contracts consumed by all sub-projects
                    (DataReading → DATA_INTELLIGENCE; Signal types → ANALYSIS_ENGINE;
                    AllocationTarget/AdvisoryAction → PORTFOLIO_ADVISOR; ORCHESTRATION wires all)
  Calibration deps: none
  Types consumed:   none — this file IS the type contract source for all other modules
-->

```
TYPES FrameworkCore {

  // ─── SUB-PROJECT REGISTRY ──────────────────────────────────────────────

  ENUM SubProject {
    DATA_INTELLIGENCE,   // M01, M02, M12, M18
    ANALYSIS_ENGINE,     // M03, M11, M14, M15, M16, M17 §1–4
    PORTFOLIO_ADVISOR,   // M06, M07, M08, M09, M10, M13, M17 §5
    FRAMEWORK_CORE,      // FW_Types.md, CALIBRATION_STATE, SESSION_LOG, 00_INDEX
    ORCHESTRATION        // M05, M04
  }


  // ─── DATA LAYER TYPES ───────────────────────────────────────────────
  // Produced by DATA_INTELLIGENCE. Consumed by ANALYSIS_ENGINE only.
  // PORTFOLIO_ADVISOR never reads DataReading directly.

  ENUM DataSource {
    FRED_SPREADSHEET_TAB,          // FRED series embedded in allocation spreadsheet
    ALLOCATION_SPREADSHEET_FINRA,  // FINRA margin debt tab
    ALLOCATION_SPREADSHEET_OTHER,  // Other indexes tab (VIX, MOVE, KRE, etc.) — crosscheck gate
    GOOGLEFINANCE,                 // live prices via GOOGLEFINANCE function (~20-min delay)
    FMP_ECONOMICS_TREASURY_RATES,  // FMP economics.treasury-rates endpoint
    FMP_CHART,                     // FMP:chart historical-price-eod-light endpoint (added v1.1)
                                   //   confirmed working: ^VIX, SPY at current plan tier
                                   //   used by: VIX_30D_AVG, VIX_90D_AVG, BROAD_EQUITY_TRAILING
    FMP_COMMODITY,                 // FMP:commodity endpoint (added v1.1; confirmed v1.2)
                                   //   confirmed working free tier June 4, 2026:
                                   //   BZUSD (Brent), GCUSD (Gold), SIUSD (Silver)
                                   //   used by: BRENT_CRUDE, GOLD_SPOT, SILVER
    FMP_INDEXES,                   // FMP:indexes endpoint (added v1.2)
                                   //   confirmed working free tier June 4, 2026:
                                   //   ^VIX ($15.40), ^GSPC ($7,584.82)
                                   //   ACCESS DENIED: ^MOVE, ^SPX, DX-Y.NYB, all forex indexes
                                   //   used by: VIX, SP500, BROAD_EQUITY_TRAILING
    FMP_MARKET_PERFORMANCE,        // FMP marketPerformance — REJECTED for sector PE (see M17 §6)
    YFINANCE_MCP,                  // market_data MCP server — yfinance (added v1.2)
                                   //   tools: market_get_quotes, market_get_ytd,
                                   //          market_get_history, market_get_macro
                                   //   instrument list: instruments.json (written by advisory
                                   //     session WriteBack per M12 PATTERN_B)
                                   //   confirmed working June 4, 2026: all portfolio instruments
                                   //   + DX-Y.NYB (DXY), ^MOVE (MOVE), ^GSPC, ^VIX, KRE, KBE
                                   //   used by: HOLDINGS_PRICES, MOVE, DXY, KRE, KBE,
                                   //            NASDAQ_COMP, DOW, RUSSELL2000,
                                   //            HISTORICAL_INSTRUMENT_PRICES
    WEBSEARCH_T1,                  // web search returning T1 source
                                   //   ⚠ PROHIBITED for price/return/index level data
                                   //   (M18 v1.2 HARD_GATE NoWebSearchForPriceData)
                                   //   Permitted only for: CPI/BLS official press releases,
                                   //   USDA farm reports, FOMC statements, geopolitical text,
                                   //   FRED statistical series pages (breakevens, term premium)
    WEBSEARCH_T2,                  // web search with uncertain provenance — flag explicitly
                                   //   PROHIBITED for any numerical framework input
    MANUAL_CLIENT_INPUT,           // client-confirmed value (e.g. Schwab screenshot — T1)
    USDA_OR_AFBF,                  // agricultural data — USDA quarterly or AFBF
    FRED_OR_WEBSEARCH              // FRED preferred; web search fallback only for official
                                   //   statistical series (not price/return data)
  }

  STRUCT FetchSpec {
    id:                  String       // unique data point identifier (e.g. "HY_OAS", "THREEFYTP10")
    source:              DataSource
    description:         String?
    update_frequency:    DAILY | WEEKLY | MONTHLY | QUARTERLY | ON_DEMAND
                         // ON_DEMAND: fetch only when explicitly required for a specific task
                         //   (e.g. HISTORICAL_INSTRUMENT_PRICES — not a standard session fetch)
    acceptable_lag_days: Integer      // days before staleness_flag fires
    // ticker_or_series is NOT stored here — lives in CALIBRATION_STATE or module constants
    // This keeps FetchSpec free of hardcoded series names that may change
  }

  STRUCT DataReading {
    spec_id:    String       // references FetchSpec.id
    value:      Any          // Float | YieldCurveReading | String (qualitative flags)
    source_tier: SourceTier
    timestamp:  DateTime     // time of fetch
    stale:      Boolean      // true if (now − timestamp.days) > FetchSpec.acceptable_lag_days
    raw_source: String?      // URL or source name for M01 audit trail
  }

  STRUCT YieldCurveReading {
    // Full Treasury curve from FMP economics.treasury-rates
    month1: Float; month2: Float; month3: Float; month6: Float
    year1:  Float; year2:  Float; year3:  Float; year5:  Float
    year7:  Float; year10: Float; year20: Float; year30: Float
    date:   Date
  }


  // ─── ANALYSIS LAYER SIGNAL TYPES ───────────────────────────────────────
  // Produced by ANALYSIS_ENGINE modules. Consumed by PORTFOLIO_ADVISOR.
  // These are the cross-sub-project contracts.
  // PORTFOLIO_ADVISOR sees only these types, never raw DataReading.

  STRUCT CreditSignal {
    // Output of M11_CreditAndCalibration
    HY_OAS:                   Float     // bps
    IG_OAS:                   Float     // bps
    CCC_OAS:                  Float     // bps
    trailing_180d_median_HY:  Float     // bps
    trailing_180d_median_IG:  Float     // bps
    HY_stress_beginning:      Boolean   // M11.HY_StressBeginning fired
    HY_recession_pricing:     Boolean   // M11.HY_RecessionPricing fired
    IG_transmission_reached:  Boolean   // M11.IG_TransmissionReached fired
    CCC_tail_widening:        Boolean   // M11.CCC_TailFirstWidening flagged
    D_floor_override:         Boolean   // true when HY_recession_pricing fires
    MOVE_index:               Float     // from M11.FetchList
    convergence_verdict:      CREDIT_ENDORSING | CREDIT_DISSENTING | CREDIT_NEUTRAL
    data_quality:             T1_CONFIRMED | COMPOSITE_ONLY | STALE
  }

  STRUCT RegimeSignal {
    // Output of M14_MarketRegime
    commodity_fear_divergence:    HIGH | MODERATE | LOW
    equity_scenario_divergence:   HIGH | MODERATE | LOW
    composite:                    HIGH | MODERATE | LOW
    entry_guards:                 Map<RoleID, GuardStatus>
    underweight_review_triggered: Boolean
  }

  STRUCT CascadeSignal {
    // Output of M17.sectorStressScore() + M17.assessCascadeLevel()
    level:               MONITORING | ALERT | PRE_POSITION
    active_chain_ids:    List<ChainID>
    active_chain_count:  Integer       // chains at or above D_alert threshold
    formal_score:        Integer       // 0–3 (M03 binding variable scale)
    D_precursor_binding: Integer       // 0–3 — fed into DeriveScenarioProbabilities()
  }

  STRUCT YieldCurveSignal {
    // Output of M17.computeYieldCurveSignal()
    spread_10Y_2Y:     Float
    spread_10Y_3M:     Float
    curve_state:       INVERTED | PARTIAL_INVERSION | NORMAL_OR_STEEP
    D_timing_signal:   RECESSION_ONSET_PATTERN | CURVE_INVERTED | MONITORING
    D_timing_estimate: String          // human-readable, e.g. "0–12 months"
    term_premium:      Float           // THREEFYTP10
    E_watch_flag:      E_PATHWAY_WATCH | FISCAL_STRESS_BUILDING | CLEAR
    yield_30Y:         Float
    e_pathway_type:    SYSTEMIC_LIQUIDITY | RESERVE_EROSION
    // e_pathway_type (added v1.1) — derived by M17.computeYieldCurveSignal().
    // Consumed by M10.ScenarioE directives to route two position responses correctly:
    //   SYSTEMIC_LIQUIDITY: classic credit crisis (2008/LTCM analog) — dollar strengthens,
    //     Treasuries rally. Rate_sensitive_income_long_duration = Hold or Add.
    //   RESERVE_EROSION: dollar reserve status challenged — dollar weakens,
    //     Treasuries under pressure. Rate_sensitive_income_long_duration = Reduce or Exit.
    // Derivation logic: @see M17.computeYieldCurveSignal.DeterminePathwayType
    // NEVER feeds into M03.DeriveScenarioProbabilities() — directive layer only.
  }

  STRUCT ScenarioProbabilities {
    // Output of M03.DeriveScenarioProbabilities()
    // Inputs: CreditSignal + RegimeSignal + CascadeSignal + direct macro bindings
    A: Float; B: Float; C: Float; D: Float; E: Float; F: Float
    INVARIANT: A + B + C + D + E + F == 100.0
  }

  STRUCT BlendedReturn {
    // Output of M15.blendedScenarioReturn(instrument, scenario)
    role_id:    RoleID
    scenario:   Scenario
    conservative: Float
    upside:     Float
  }


  // ─── PORTFOLIO LAYER TYPES ────────────────────────────────────────────
  // Produced by PORTFOLIO_ADVISOR modules. Consumed by ORCHESTRATION.
  // These types never contain tickers or raw DataReading.

  STRUCT AllocationTarget {
    // Output of M13.idealAllocation()
    role_id:    RoleID
    target_pct: Float
    account_id: AccountID
    scenario:   Scenario?    // null = scenario-weighted EV target; set = per-scenario floor
    ev:         Float?       // scenario-weighted EV if scenario is null
    rationale:  String
  }

  STRUCT AdvisoryAction {
    // Output of M17.PrePositioningLadder (§5) and advisory functions
    // INVARIANT: role_id is always a RoleID — NEVER a ticker symbol.
    // Tickers are resolved from CALIBRATION_STATE §11 at execution time.
    role_id:                      RoleID
    direction:                    ActionDirection
    target_fn:                    String?  // reference to computation, e.g. "M13.idealAllocation(account, D)"
    rationale:                    String
    requires_client_confirmation: true    // ALWAYS true — no advisory action auto-executes
    tax_constraint:               TaxConstraint?
    guard_check:                  String?  // e.g. "EntryExtensionGuard required before ADD"
    execution_note:               String?  // resolution guidance: "@see CALIBRATION_STATE §11"
  }

  ENUM ActionDirection {
    ADD,                // increase toward target
    HOLD,               // maintain; no action required
    TRIM,               // reduce; do NOT add
    EXIT_INITIATED,     // begin exit; timing per execution_note
    CONFIRM,            // verify allocation is at target; review if not
    REVIEW_EXECUTION_WINDOW  // assess timing; action type determined at review
  }

  STRUCT TaxConstraint {
    // Human-readable; resolved via M06.TaxPlacement(role_id, account) at execution
    note: String
    // Examples:
    //  "Instruments in this role may carry swap structures adverse in taxable accounts."
    //  "REIT distributions are predominantly ordinary income — retirement accounts preferred."
  }


  // ─── REGISTRY TYPES ────────────────────────────────────────────────
  // Extension points for the framework. New modules add entries; orchestration
  // iterates registries without knowing their contents. M05 never changes when
  // a new module is added — the module registers itself.

  STRUCT FetchRegistry {
    // Accumulates FetchSpec from all modules. Replaces M02 hardcoded FETCH_LIST.
    // Phase 2 complete: M18 is the single DATA_REGISTRY_ENTRIES source.
    entries: List<FetchSpec>
    FUNCTION register(spec: FetchSpec) → void  // idempotent on duplicate id
    FUNCTION fetchAll() → List<DataReading>     // parallel fetch of all entries
  }

  STRUCT BriefingSectionSpec {
    id:             String    // unique identifier
    title:          String    // displayed in briefing
    position_after: String    // id of section this follows (null = first)
    module_id:      ModuleID
    render_fn:      String    // reference to module function that produces BriefingSection
  }

  STRUCT BriefingRegistry {
    // Accumulates BriefingSectionSpec from all modules. Replaces M04 hardcoded sections.
    // Phase 2 complete: all modules register their own BRIEFING_REGISTRY_ENTRY.
    sections: List<BriefingSectionSpec>
    FUNCTION register(spec: BriefingSectionSpec) → void
    FUNCTION assemble(readings: List<DataReading>) → OrderedList<BriefingSection>
  }

  STRUCT BriefingSection {
    spec_id:            String
    title:              String
    content:            String
    data_quality_flags: List<String>
  }


  // ─── IDENTIFIER ENUMS ────────────────────────────────────────────────
  // IMPORTANT: RoleID and AccountID are SHADOWS of CALIBRATION_STATE §11.
  // §11 is AUTHORITATIVE. When M15.AddRole() adds a role, update BOTH §11 AND RoleID atomically.
  // These enums provide type contracts for module interfaces; §11 governs the live configuration.

  ENUM RoleID {
    // All roles from CALIBRATION_STATE §11.1 (as of v1.19)
    geopolitical_premium,
    inflation_hedge_precious_metals,
    inflation_hedge_commodity_linked,
    real_asset_contracted_revenue,
    policy_driven_thematic_equity,
    rate_sensitive_income_short_duration,
    rate_sensitive_income_long_duration,
    broad_market_equity_domestic,
    broad_market_equity_international,
    secular_technology_growth,
    inflation_linked_sovereign,
    real_estate_equity_income,
    systematic_trend_following,
    consumer_defensive_equity,
    healthcare_defensive_equity,
    floating_rate_credit_income,
    emerging_market_equity
    // EXTENSIBLE — add here AND in §11.1 atomically when M15.AddRole() is called
  }

  ENUM AccountID {
    PRIMARY_IRA, PRIMARY_ROTH, PRIMARY_TAXABLE,
    TAXABLE_PRESERVATION, RELATIVE_IRA, RELATIVE_ROTH
  }

  ENUM Scenario { A, B, C, D, E, F }

  ENUM ModuleID {
    M01, M02, M03, M04, M05, M06, M07, M08,
    M09, M10, M11, M12, M13, M14, M15, M16, M17, M18
    // M18 added v1.1 — centralized data fetch registry
  }

  ENUM SourceTier { T1, T2, T3 }

  ENUM ChainID {
    // M17 cascade chain identifiers
    CHAIN_1,   // Agriculture → Regional Bank
    CHAIN_2,   // CRE Maturity Wall → Regional Bank
    CHAIN_3,   // Private Credit → Margin Cascade
    CHAIN_4,   // Manufacturing Supply Chain
    CHAIN_5,   // Sovereign Fiscal → E Pathway
    CHAIN_6    // Municipal Fiscal
  }

  ENUM GuardStatus {
    // M14 entry extension guard states per role
    CLEARED,          // price below extension threshold — ADD eligible
    ACTIVE,           // price above threshold — ADD blocked
    NOT_APPLICABLE    // role exempt from entry extension guard per §9.3
  }

}
```
