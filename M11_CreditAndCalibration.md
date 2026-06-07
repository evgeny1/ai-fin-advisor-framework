# M11 — Credit Signal Protocol & Calibration Discipline
<!-- Version: 1.2 | Adopted: May 25, 2026 -->
<!-- Changes from v1.1: DATA_REGISTRY_ENTRIES moved to M18_MarketDataFetch (v1.20 M18 integration). -->
<!--   M11 DATA_REGISTRY_ENTRIES block renamed _LEGACY. M18 is the single FetchSpec registry. -->
<!-- Extends: M02_IntelGathering (FetchRegistry), M04_BriefingFormat (BriefingRegistry), M10_ScenariosDEF (D trigger) -->
<!-- Companion: @see CALIBRATION_STATE (must load every session); @see FW_Types.md (types) -->

<!-- MODULE MANIFEST
  ID:              M11_CreditAndCalibration
  Version:         1.2
  Sub-project:     ANALYSIS_ENGINE (CreditSignal) | FRAMEWORK_CORE (CalibrationDiscipline)
  Phase-3 note:    Planned split: M11_CreditData (DATA_INTELLIGENCE) + M11_CreditAnalysis (ANALYSIS_ENGINE)
  Reason to change (CreditSignal):          credit signal methodology or spread thresholds change
  Reason to change (CalibrationDiscipline): calibration review process or schedule changes
  Inputs consumed:  DataReading<HY_OAS>, DataReading<CCC_OAS>, DataReading<IG_OAS>,
                    DataReading<BBB_OAS>, DataReading<MOVE>
  Outputs produced: CreditSignal
  Calibration deps: CALIBRATION_STATE §1
  Types consumed:   @see FW_Types.md — DataReading, CreditSignal, FetchSpec, BriefingSectionSpec
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
  // Phase 2 complete: BriefingRegistry.assemble() in M04 iterates this entry.
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

  // ─── BRIEFING BLOCK (render function — called by BriefingRegistry.assemble()) ─────────

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

  RULE SignalConvergenceTest() {
    IF all_indicators(HY, CCC, IG) tighten_or_hold {
      RETURN credit_endorses_current_equity_regime
      weight: corroborating
    }
    IF HY_composite_calm AND CCC_widening_materially {
      RETURN early_stage_stress_hidden_by_aggregation
    }
    IF HY_composite > stress_beginning_threshold
       AND velocity_confirmed
       AND equities_flat_or_up {
      RETURN institutional_credit_dissenting_from_retail_equity_bid
      weight: primary_warning
    }
    IF IG > transmission_threshold AND velocity_confirmed {
      RETURN transmission_reached_investment_grade
      weight: severe
    }
  }

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
  // Delta values loaded from @see CALIBRATION_STATE §1 at session start.
  // Velocity overlays are FIXED STRUCTURAL RULES — not calibration-dated.

  THRESHOLD HY_StressBeginning {
    condition:  HY_OAS > (trailing_180d_median + [HY_STRESS_DELTA])
                AND widened >= 100bps OVER prior_60_days  // velocity — fixed structural
    sustain:    >= 10 trading_days
    action:     revisit B/C/D probabilities
    [HY_STRESS_DELTA]: @see CALIBRATION_STATE §1.1
  }

  THRESHOLD HY_RecessionPricing {
    condition:  HY_OAS > (trailing_180d_median + [HY_RECESSION_DELTA])
    sustain:    >= 10 trading_days
    action:     ScenarioD.probability_floor = 25%
    [HY_RECESSION_DELTA]: @see CALIBRATION_STATE §1.1
  }

  THRESHOLD IG_TransmissionReached {
    condition:  IG_OAS > (trailing_180d_median + [IG_TRANSMISSION_DELTA])
                AND widened >= 40bps OVER prior_60_days  // velocity — fixed structural
    sustain:    >= 10 trading_days
    action:     recession/credit_event_pricing has_reached_investment_grade
    [IG_TRANSMISSION_DELTA]: @see CALIBRATION_STATE §1.2
  }

  THRESHOLD CCC_TailFirstWidening {
    condition_ratio:    CCC widens 3x HY_composite OVER any_30_day_window
    condition_absolute: CCC + >= 200bps WHILE composite + < 50bps OVER 30_days
    action:   flag_for_monitoring
              add_explicit_note to_next_3_sessions
    [absolute_divergence_floor]: @see CALIBRATION_STATE §1.3
  }

  CONSTRAINT VelocityOverlayRationale {
    // HY: 100bps / 60 days — FIXED — not calibration-dated
    // IG:  40bps / 60 days — FIXED — not calibration-dated
  }

  // ─── UPDATED SCENARIO D TRIGGER ───────────────────────────────────────────────────────
  // Supersedes original Part 6 Scenario D trigger. @see M10_ScenariosDEF.ScenarioD

  ScenarioDTrigger {
    REQUIRE [
      unemployment_rising >= 0.5% OVER any_3_month_window  // BLS
      AND Fed_cutting_aggressively(
            >= 75bps_cumulative_within_60d
            OR any_emergency_inter_meeting_cut
          )
      AND credit_stress AT_LEAST_ONE_OF [
        (a) IG_OAS transmission_reached threshold_fired
        (b) HY_OAS recession_pricing threshold_fired
        (c) CCC_OAS + >= 100bps OVER 30d WHILE composite_calm
            SUSTAINED through_next_session
      ]
    ]
    NOTE: "All spread conditions require T1 confirmation from dedicated FRED series pages."
    GraduatedResponseRule: still_applies
    D_floor_25pct: partial_rotation triggered_automatically
                   UNLESS T1_counter_evidence_documented_in_briefing
  }

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
