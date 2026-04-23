# M11 — Credit Signal Protocol & Calibration Discipline
<!-- Source: Framework_Extension_v1_Credit_And_Calibration.md -->
<!-- Version: 1 | Adopted: April 19, 2026 -->
<!-- Extends: M02_IntelGathering (fetch list), M04_BriefingFormat (new section), M10_ScenariosDEF (D trigger) -->
<!-- Companion: @see CALIBRATION_STATE (must load every session) -->

```
MODULE CreditSignal {

  // ─── FETCH LIST ADDITION (extends M02_IntelGathering.FETCH_LIST) ─────────

  FetchList {
    HY_composite:  FRED series BAMLH0A0HYM2   // ICE BofA US High Yield OAS
    CCC_tail:      FRED series BAMLH0A3HYC    // ICE BofA CCC & Lower HY OAS
    IG_composite:  FRED series BAMLC0A0CM     // ICE BofA US Corporate IG OAS
  }

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

  // ─── BRIEFING BLOCK (inserted between Fixed Income and Currency in M04) ──

  BriefingBlock {
    // Insert between FIXED INCOME & RATES and CURRENCY sections
    HY_OAS_composite:    ___ bps  [Δ vs 30d / 90d]
    CCC_OAS:             ___ bps  [Δ vs 30d / 90d]
    IG_OAS:              ___ bps  [Δ vs 30d / 90d]
    MOVE_index:          ___      [Δ vs 30d]
    trailing_180d_median_HY: ___ bps
    trailing_180d_median_IG: ___ bps
    Signal: [one sentence — credit endorsing or dissenting from equity]
    data_quality_flag: T1_confirmed | composite_only | stale
  }

  // ─── SIGNAL CONVERGENCE TEST (run each session) ──────────────────────────

  RULE SignalConvergenceTest() {
    IF all_indicators(HY, CCC, IG) tighten_or_hold {
      RETURN credit_endorses_current_equity_regime
      weight: corroborating
    }
    IF HY_composite_calm AND CCC_widening_materially {
      RETURN early_stage_stress_hidden_by_aggregation
      // See tail-first widening threshold below
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

  // ─── ASYMMETRIC WEIGHTING RULE (post-2008 signal quality) ────────────────

  GUARD AsymmetricWeighting {
    // Public HY spreads may structurally understate credit stress due to:
    // private-credit migration, CLO/insurance structural bid, index quality drift toward BB.
    RULE: absence_of_widening IS NOT positive_evidence_of_market_health
    RULE: only_presence_of_widening IS actionable
    // Widening confirms stress. Calm does NOT confirm absence of stress.
    // This asymmetry is deliberate — preserve in all signal synthesis.
  }

  // ─── SCENARIO ROUTING ────────────────────────────────────────────────────

  RULE ScenarioRouting(credit_signal) {
    IF HY_widening AND energy_shock_persistent  → supports: ScenarioC deepening toward D
    IF HY_widening AND energy_calm              → supports: ScenarioD directly
    IF IG_widening
       AND sovereign_CDS_widening
       AND DXY_falling                          → supports: ScenarioE probability increase
    IF all_credit_calm                          → downweights: ScenarioD probability
                                                  // does NOT downweight B or C
                                                  // (B and C can occur without credit stress — ref. 1970s stagflation)
  }

  // ─── THRESHOLDS ──────────────────────────────────────────────────────────
  // All relative thresholds: computed against trailing 180-day median of underlying FRED series.
  // Delta values loaded from @see CALIBRATION_STATE §1 at session start.
  // Velocity overlays are FIXED STRUCTURAL RULES — not calibration-dated.

  THRESHOLD HY_StressBeginning {
    condition:  HY_OAS > (trailing_180d_median + [HY_STRESS_DELTA])
                AND widened >= 100bps OVER prior_60_days  // velocity — fixed structural
    sustain:    >= 10 trading_days
    action:     revisit B/C/D probabilities
                // credit stress pricing has begun
    [HY_STRESS_DELTA]: @see CALIBRATION_STATE §1.1
  }

  THRESHOLD HY_RecessionPricing {
    condition:  HY_OAS > (trailing_180d_median + [HY_RECESSION_DELTA])
    sustain:    >= 10 trading_days
    action:     ScenarioD.probability_floor = 25%
                // floor overrides narrative-based probability reasoning
                // override ONLY with explicit T1 counter-evidence documented in briefing
    [HY_RECESSION_DELTA]: @see CALIBRATION_STATE §1.1
  }

  THRESHOLD IG_TransmissionReached {
    condition:  IG_OAS > (trailing_180d_median + [IG_TRANSMISSION_DELTA])
                AND widened >= 40bps OVER prior_60_days  // velocity — fixed structural
    sustain:    >= 10 trading_days
    action:     recession/credit_event_pricing has_reached_investment_grade
                // severe signal — assess D and E probabilities
    [IG_TRANSMISSION_DELTA]: @see CALIBRATION_STATE §1.2
  }

  THRESHOLD CCC_TailFirstWidening {
    condition_ratio:    CCC widens 3x HY_composite OVER any_30_day_window
    condition_absolute: CCC + >= 200bps WHILE composite + < 50bps OVER 30_days
    action:   flag_for_monitoring
              add_explicit_note to_next_3_sessions
              // NO automatic scenario update
    [absolute_divergence_floor]: @see CALIBRATION_STATE §1.3  // calibration-dated
  }

  CONSTRAINT VelocityOverlayRationale {
    // Level-alone triggers vulnerable to slow drifts that aren't regime changes.
    // Velocity overlays filter slow drift and catch actual regime transitions.
    // HY: 100bps / 60 days — FIXED — not calibration-dated
    // IG:  40bps / 60 days — FIXED — not calibration-dated
  }

  // ─── UPDATED SCENARIO D TRIGGER ──────────────────────────────────────────
  // Supersedes original Part 6 Scenario D trigger. @see M10_ScenariosDEF.ScenarioD

  ScenarioDTrigger {
    REQUIRE [
      unemployment_rising >= 0.5% OVER any_3_month_window  // BLS
      AND Fed_cutting_aggressively(
            >= 75bps_cumulative_within_60d
            OR any_emergency_inter_meeting_cut
          )  // confirmed: Fed statement
      AND credit_stress AT_LEAST_ONE_OF [
        (a) IG_OAS transmission_reached threshold_fired  // @see IG_TransmissionReached
        (b) HY_OAS recession_pricing threshold_fired     // invokes D_floor = 25%
        (c) CCC_OAS + >= 100bps OVER 30d WHILE composite_calm
            SUSTAINED through_next_session
      ]
    ]
    NOTE: "All spread conditions require T1 confirmation from dedicated FRED series pages."
    GraduatedResponseRule: still_applies  // partial at 30%, full at >= 40%
    D_floor_25pct: partial_rotation triggered_automatically
                   UNLESS T1_counter_evidence_documented_in_briefing
  }

}

// ─────────────────────────────────────────────────────────────────────────────

MODULE CalibrationDiscipline {
  // Source: Framework_Extension_v1 Part E + Part F
  // All thresholds tracked in @see CALIBRATION_STATE

  // ─── THRESHOLD CLASSIFICATION ────────────────────────────────────────────

  ENUM ThresholdType {
    permanent:          // structural rules; do not drift
                        // examples: source tier definitions, velocity overlays, tax placement
    calibration_dated:  // nominal or relative values requiring periodic review ⚑
                        // tracked in CALIBRATION_STATE
  }

  // ─── SCHEDULED REVIEW ────────────────────────────────────────────────────

  SCHEDULE {
    quarter_end: [March_31, June_30, September_30, December_31]
    action: audit_all_calibration_dated_thresholds in_first_session_after_quarter_end
  }

  // ─── TRIGGERED REVIEW ────────────────────────────────────────────────────

  TRIGGER InterimRecalibration {
    IF ANY [
      (a) trailing_baseline shifts > 20% from_last_calibration
      (b) threshold_fires_twice WITHOUT prescribed_regime_materializing
          // false-positive diagnostic
      (c) threshold_fails_to_fire WHILE prescribed_regime_materializes
          // false-negative diagnostic — rarer but more dangerous
      (d) primary_driver_recalibration_declared  // @see M02_IntelGathering.identifyPrimaryDriver
    ] {
      conduct_review BEFORE producing_trade_recommendations
    }
  }

  // ─── REVIEW METHODOLOGY — RELATIVE THRESHOLDS ────────────────────────────

  PROCEDURE ReviewRelativeThreshold(series, current_delta) {
    1: fetch trailing_180d_daily_data from T1_source
    2: compute median  // NOT mean — robust to outliers
    3: compute percentiles [10th, 25th, 75th, 90th] of trailing_distribution
    4: verify threshold_delta places_trigger BETWEEN 75th_and_90th_percentile
    5: IF threshold ABOVE 90th_percentile → loosen (lower delta)
       IF threshold BELOW 75th_percentile → tighten (raise delta)
    6: document [trailing_median, threshold_level, percentile_position, last_calibration_date]
  }

  // ─── REVIEW METHODOLOGY — ABSOLUTE THRESHOLDS ────────────────────────────

  PROCEDURE ReviewAbsoluteThreshold(series, threshold_value) {
    1: fetch trailing_5y_data for underlying_series
    2: identify all_historical_episodes where prescribed_regime_materialized
    3: check: was_threshold_crossed BEFORE | DURING | AFTER regime_materialization?
    4: IF consistently_crossed AFTER regime_already_visible
         → threshold_is_lagging → lower_it
       IF consistently_crossed WITHOUT regime_materializing
         → false_positives → raise_it
    5: document [episode_count, hit_rate, miss_rate, adjustment_made]
  }

  // ─── PROSPECTIVE APPLICATION RULE ────────────────────────────────────────

  CONSTRAINT ProspectiveOnly {
    recalibration_applies: prospectively_only
    takes_effect: start_of_next_session_following_calibration_update
    NEVER:        apply_retroactively
    // Active trigger conditions evaluated before recalibration:
    // evaluated against PREVIOUS threshold until they fire or are dismissed.
    // Prevents gaming recalibration to produce desired outcomes.
  }

  // ─── SESSION LOAD PROTOCOL ────────────────────────────────────────────────

  PROCEDURE SessionLoad {
    1: load CALIBRATION_STATE  // @see M12_DriveProtocol.fetchFile("Calibration_State.md")
    2: state_in_briefing: "Calibration State loaded, last update: [date]"
       // absence = session invalid for threshold-sensitive decisions
    3: apply current_threshold_values_from calibration_file
       NEVER: use_remembered_values
    4: IF scheduled_review_date_has_passed WITHOUT completion {
       FLAG: immediately
       conduct_review BEFORE producing_trade_recommendations
    }
  }

  // ─── CALIBRATION LOG ENTRY FORMAT ────────────────────────────────────────

  STRUCT CalibrationLogEntry {
    name:                  String   // threshold name / description
    current_value:         Any      // absolute value or delta from baseline
    last_calibration_date: Date
    trailing_baseline:     Float?   // if relative threshold
    percentile_position:   Float?   // position of threshold in trailing distribution
    rationale:             String   // rationale for last adjustment
  }
  // Full log preserved in CALIBRATION_STATE §3

}
```
