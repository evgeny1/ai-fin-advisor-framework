# M11 — Credit Signal Protocol & Calibration Discipline
<!-- Version: 1.5 | Updated: see git log -->

<!-- MODULE MANIFEST
  ID:              M11_CreditAndCalibration
  Version:         1.5
  Sub-project:     ANALYSIS_ENGINE (CreditSignal) | FRAMEWORK_CORE (CalibrationDiscipline)
  Reason to change: credit signal methodology or spread thresholds change (CreditSignal);
                    OR calibration review process or schedule changes (CalibrationDiscipline).
  Inputs consumed:  DataReading<HY_OAS>, DataReading<CCC_OAS>, DataReading<IG_OAS>,
                    DataReading<BBB_OAS>, DataReading<MOVE>
  Outputs produced: CreditSignal
  Calibration deps: CALIBRATION_STATE §1
  Types consumed:   @see FW_Types.md — DataReading, CreditSignal, FetchSpec, BriefingSectionSpec
  Cross-module:     @see M02_IntelGathering (FetchRegistry), @see M04_BriefingFormat (BriefingRegistry),
                    @see M10_ScenariosDEF (Scenario D trigger). DATA_REGISTRY_ENTRIES superseded by
                    M18_MarketDataFetch. CALIBRATION_STATE must load every session.
-->

```
MODULE CreditSignal {

  // DATA_REGISTRY_ENTRIES and FetchList moved to M18_MarketDataFetch (v1.2). @see M18.

  GUARD DataSourceIntegrity {
    REQUIRE: all_credit_spread_values verified_against [
      dedicated_FRED_series_pages,
      ICE_Data_Indices_direct_feed
    ]
    NEVER:   accept_from [aggregator_sidebars, embedded_ticker_widgets, summary_tables]
    NOTE:    "From April 2026 onward: FRED display limited to 3 years of observations.
              Longer history requires ICE Data direct source.
              Trailing 180-day median computation remains feasible from 3-year FRED window."
  }

  // ─── BRIEFING REGISTRY ENTRY ──────────────────────────────────────────────────────────
  // Claude assembles this entry into the briefing in position_after order
  // (no executed BriefingRegistry — see ENG-17).
  // CASCADE_EARLY_WARNING (M17) is registered with position_after: "CREDIT_SIGNALS" — this id.

  BRIEFING_REGISTRY_ENTRY {
    REGISTER BriefingSectionSpec {
      id:             "CREDIT_SIGNALS"
      title:          "CREDIT STRESS"
      position_after: "FIXED_INCOME_AND_RATES"   // M04's registered section id
      module_id:      M11
      render_fn:      "M11.BriefingBlock"
    }
  }

  // ─── BRIEFING BLOCK (render function — applied by Claude, no executed registry) ───────

  BriefingBlock {
    HY_OAS_composite:    ___ bps  [Δ vs 30d / 90d]
    CCC_OAS:             ___ bps  [Δ vs 30d / 90d]
    IG_OAS:              ___ bps  [Δ vs 30d / 90d]
    MOVE_index:          ___      [Δ vs 30d]
    trailing_180d_median_HY: ___ bps
    trailing_180d_median_IG: ___ bps
    Signal: [one sentence — credit endorsing or dissenting from equity]
    data_quality_flag: T1_confirmed | composite_only | stale
  }

  // ─── SIGNAL CONVERGENCE TEST (run each session) ───────────────────────────────────────
  // Confirmed during ENG-2 review (2026-06-17): faithfully implemented as
  // analysis/credit.py's _convergence_text(), called by compute_credit_signal(),
  // which IS wired into advisor_run_computation() — this runs live every session.
  // The four cases below (corroborating / hidden stress / primary warning / severe)
  // are the exact branches credit.py evaluates. @see python/advisor/analysis/credit.py

  // ─── ASYMMETRIC WEIGHTING RULE (post-2008 signal quality) ────────────────────────────

  GUARD AsymmetricWeighting {
    RULE: absence_of_widening IS NOT positive_evidence_of_market_health
    RULE: only_presence_of_widening IS actionable
    // Widening confirms stress. Calm does NOT confirm absence of stress.
  }

  // ─── SCENARIO ROUTING ─────────────────────────────────────────────────────────────────

  RULE ScenarioRouting(credit_signal) {
    IF HY_widening AND energy_shock_persistent  → supports: ScenarioC deepening toward D
    IF HY_widening AND energy_calm              → supports: ScenarioD directly
    IF IG_widening
       AND sovereign_CDS_widening
       AND DXY_falling                          → supports: ScenarioE probability increase
    IF all_credit_calm                          → downweights: ScenarioD probability
  }

  // ─── THRESHOLDS ───────────────────────────────────────────────────────────────────────
  // Confirmed during ENG-2 review (2026-06-17): the four thresholds below — and their
  // exact delta/velocity/sustain conditions — are implemented line-for-line in
  // analysis/credit.py's compute_credit_signal(), which IS wired into
  // advisor_run_computation() and runs live every session. Delta values still come
  // from CALIBRATION_STATE §1 (read by the parser, never hardcoded in Python).
  // Velocity overlays (HY: 100bps/60d; IG: 40bps/60d) are fixed structural constants,
  // not calibration-dated, also matched exactly in Python.
  //
  //   HY_StressBeginning:     HY_OAS > median+§1.1 delta, velocity confirmed, 10d sustain
  //                            → CreditSignal.hy_stress_beginning
  //   HY_RecessionPricing:    HY_OAS > median+§1.1 delta, 10d sustain
  //                            → CreditSignal.hy_recession_pricing; fires ScenarioD floor = 25%
  //   IG_TransmissionReached: IG_OAS > median+§1.2 delta, velocity confirmed, 10d sustain
  //                            → CreditSignal.ig_transmission_reached
  //   CCC_TailFirstWidening:  CCC widens 3x HY composite (30d) OR CCC+200bps while
  //                            composite+<50bps (30d) → CreditSignal.ccc_tail_first_widening
  //
  // @see python/advisor/analysis/credit.py — compute_credit_signal()

  // ─── UPDATED SCENARIO D TRIGGER ───────────────────────────────────────────────────────
  // Supersedes original Part 6 Scenario D trigger. @see M10_ScenariosDEF.ScenarioD
  // The credit_stress component (IG transmission OR HY recession OR CCC tail-widening,
  // each independently sufficient) is implemented identically in
  // orchestrator/scoring_questions.py's D_check_credit auto-scoring and in M03's
  // raw_D check membership (capped at 3). The unemployment + Fed-cutting-aggressively
  // conditions remain AI-scored (no automated unemployment/Fed-pace data feed yet).
  //
  // D_floor_25pct: HY_RecessionPricing firing triggers the 25% D floor automatically in
  //   analysis/scenario_math.py's apply_floors() — wired, runs every session.
  // GraduatedResponseRule still applies once D crosses 30%/40% — @see M08.ExecutionGuards.
  // NOTE: all spread conditions require T1 confirmation from dedicated FRED series pages.

}

// ─────────────────────────────────────────────────────────────────────────────

MODULE CalibrationDiscipline {

  ENUM ThresholdType {
    permanent:          // structural rules; do not drift
    calibration_dated:  // nominal or relative values requiring periodic review ⚑
  }

  SCHEDULE {
    quarter_end: [March_31, June_30, September_30, December_31]
    action: audit_all_calibration_dated_thresholds in_first_session_after_quarter_end
  }

  TRIGGER InterimRecalibration {
    IF ANY [
      (a) trailing_baseline shifts > 20% from_last_calibration
      (b) threshold_fires_twice WITHOUT prescribed_regime_materializing
      (c) threshold_fails_to_fire WHILE prescribed_regime_materializes
      (d) primary_driver_recalibration_declared
    ] {
      conduct_review BEFORE producing_trade_recommendations
    }
  }

  PROCEDURE ReviewRelativeThreshold(series, current_delta) {
    1: fetch trailing_180d_daily_data from T1_source
    2: compute median
    3: compute percentiles [10th, 25th, 75th, 90th] of trailing_distribution
    4: verify threshold_delta places_trigger BETWEEN 75th_and_90th_percentile
    5: IF threshold ABOVE 90th_percentile → loosen (lower delta)
       IF threshold BELOW 75th_percentile → tighten (raise delta)
    6: document [trailing_median, threshold_level, percentile_position, last_calibration_date]
  }

  PROCEDURE ReviewAbsoluteThreshold(series, threshold_value) {
    1: fetch trailing_5y_data for underlying_series
    2: identify all_historical_episodes where prescribed_regime_materialized
    3: check: was_threshold_crossed BEFORE | DURING | AFTER regime_materialization?
    4: IF consistently_crossed AFTER → threshold_is_lagging → lower_it
       IF consistently_crossed WITHOUT regime → false_positives → raise_it
    5: document [episode_count, hit_rate, miss_rate, adjustment_made]
  }

  CONSTRAINT ProspectiveOnly {
    recalibration_applies: prospectively_only
    takes_effect: start_of_next_session_following_calibration_update
    NEVER:        apply_retroactively
  }

  PROCEDURE SessionLoad {
    1: load CALIBRATION_STATE
    2: state_in_briefing: "Calibration State loaded, last update: [date]"
    3: apply current_threshold_values_from calibration_file
       NEVER: use_remembered_values
    4: IF scheduled_review_date_has_passed WITHOUT completion {
       FLAG: immediately
       conduct_review BEFORE producing_trade_recommendations
    }
  }

  STRUCT CalibrationLogEntry {
    name:                  String
    current_value:         Any
    last_calibration_date: Date
    trailing_baseline:     Float?
    percentile_position:   Float?
    rationale:             String
  }
  // Full log preserved in CALIBRATION_STATE §3

}
```
