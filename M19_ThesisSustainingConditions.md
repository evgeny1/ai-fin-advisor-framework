# M19 — Thesis Sustaining Conditions
<!-- Version: 1.2 | Updated: see git log -->

<!-- MODULE MANIFEST
  ID:              M19_ThesisSustainingConditions
  Version:         1.2
  Sub-project:     THESIS_MONITORING
  Reason to change: thesis-sustaining condition evaluation methodology, status taxonomy, or
                    AI-boundary routing changes. New tickers: add a CALIBRATION_STATE §13
                    entry only — this module file does not change.
  Inputs consumed:  List<DataReading> (M18 FetchRegistry output); ScenarioProbabilities (M03);
                    RegimeSignal (M14, for §13 entries that reference it); Call 1 qualitative
                    outputs (M02.QualitativeGatherList); Call 2 scored answers (M03
                    ScoringQuestion pipeline, M19-tagged subset)
  Outputs produced: ThesisStatus per held instrument (ACTIVE | DEGRADED | FAILED | UNKNOWN);
                    BriefingSection (THESIS_CONDITION_STATUS)
  Calibration deps: CALIBRATION_STATE §13 (sustaining_conditions, degraded_signals,
                    failure_signals, data_dependencies — per ticker)
  Types consumed:   @see FW_Types.md — DataReading, ScenarioProbabilities, RegimeSignal, ThesisStatus
  Cross-module:     @see M02_IntelGathering (QualitativeGatherList consumer), @see M03_ScenarioFramework
                    (ScoringQuestion consumer), @see M06_ClientAndAdvisory (HoldJustification consumer),
                    @see M14_MarketRegime (RegimeSignal, MAGS-class entries), @see M04_BriefingFormat.
                    CALIBRATION_STATE §13 holds per-ticker conditions.
-->

```
MODULE ThesisSustainingConditions {

  // ─── PURPOSE ────────────────────────────────────────────────────────────────
  // Answers a narrower question than M15/M16 EV math: "is the reason we bought this
  // still true?" Conditions live entirely in CALIBRATION_STATE §13 — this module
  // contains no per-ticker logic, only the generic evaluation procedure below.
  //
  // M19 NEVER feeds M03.DeriveScenarioProbabilities(). It is a downstream advisory
  // signal consumed by M06.HoldJustification and surfaced in the briefing — it does
  // not gate, override, or adjust any other module's computation.

  ENUM ThesisStatus {
    ACTIVE,    // all sustaining_conditions hold; nothing else fired
    DEGRADED,  // a degraded_signals condition fired (tailwind fading, not broken)
    FAILED,    // a failure_signals condition fired (original thesis broken)
    UNKNOWN    // a required data_dependency was unavailable this session
  }

  // ─── SCOPE ────────────────────────────────────────────────────────────────────────────
  // (ENG-9, moved here from CALIBRATION_STATE §13’s preamble — this is methodology,
  // not a calibration-dated value, so it belongs here rather than duplicated per ticker.)
  //
  // Applies to active-conviction / thematic positions only. Defensive and floor-sleeve
  // holdings (consumer_defensive_equity, rate_sensitive_income_short, cash-equivalents)
  // have no commodity/duration/war-premium degradation mechanism to monitor — same
  // "N/A, guard does not apply" precedent already used for those roles in §9.3. No §13
  // entry for those roles, and (per the NEVER rule above) that absence is this scope
  // decision, not a data gap — it must never resolve to UNKNOWN.

  // ─── AI BOUNDARY ROUTING ──────────────────────────────────────────────────
  // §13 conditions split into two evaluation paths. Both are declared here so the
  // routing is auditable in one place — §13 itself stays free of implementation detail.

  NUMERIC_CONDITIONS {
    // Evaluated in pure Python against DataReading / ScenarioProbabilities / RegimeSignal.
    // No AI call. Covers the majority of §13: DBMF, MLPX, MAGS, COPX (once COPPER_SPOT +
    // CHINA_PMI_MANUFACTURING are registered in M18), URA's price leg, SGOL/SIVR's rate/DXY
    // legs, AIPO, INFL.
  }

  JUDGMENT_CONDITIONS {
    // Evaluated via Call 2 ScoringQuestion entries tagged consumer: "M19" — appended to the
    // SAME M03 scoring call, not a new AI boundary. @see M03.ScoringQuestion pipeline.
    // M19 itself only thresholds the returned boolean/count; it never interprets free text.
    REGISTRY [
      { ticker: "SGOL", topic: "M02.cb_gold_reserve_accumulation", call2_question_id: "M19_SGOL_CB_NARRATIVE" },
      { ticker: "SIVR", topic: "M02.cb_gold_reserve_accumulation", call2_question_id: "M19_SIVR_CB_NARRATIVE" },
      { ticker: "URA",  topic: "M02.nuclear_policy_trajectory",    call2_question_id: "M19_URA_NUCLEAR_POLICY" },
      { ticker: "XAR",  topic: "M02.active_conflict_status",       call2_question_id: "M19_XAR_CONFLICT_GATE" }
      // XAR reuses an existing Call 1 topic — no new QualitativeGatherList item needed.
    ]
  }

  // ─── EVALUATION PROCEDURE ─────────────────────────────────────────────────

  FUNCTION evaluateThesisConditions(held_tickers, readings, scenario_probs, regime_signal,
                                     call2_answers) -> Map<Ticker, ThesisStatus> {

    results = {}

    FOR each ticker IN held_tickers {
      entry = CALIBRATION_STATE.§13[ticker]
      IF entry IS ABSENT {
        CONTINUE  // no §13 entry = out of scope (defensive/floor sleeve, or not yet reviewed)
                  // @see §13 preamble "Scope" — does NOT trigger UNKNOWN; absence is a scope
                  // decision, not a data gap
      }

      // STEP 1: resolve every data_dependency. Missing/flagged reading → UNKNOWN, full stop.
      resolved = resolve_dependencies(entry.data_dependencies, readings, scenario_probs,
                                       regime_signal, call2_answers)
      IF resolved.any_missing {
        results[ticker] = UNKNOWN
        FLAG: "[ticker] TSC evaluation incomplete — missing: [resolved.missing_keys].
               Reported UNKNOWN, not defaulted to ACTIVE."
        CONTINUE
      }

      // STEP 2: failure_signals take priority — a fired failure overrides a held sustaining condition.
      IF any(entry.failure_signals, condition_fires, resolved) {
        results[ticker] = FAILED
        CONTINUE
      }

      // STEP 3: degraded_signals (optional field).
      IF entry.degraded_signals EXISTS AND any(entry.degraded_signals, condition_fires, resolved) {
        results[ticker] = DEGRADED
        CONTINUE
      }

      // STEP 4: sustaining_conditions must ALL hold for ACTIVE.
      IF all(entry.sustaining_conditions, condition_holds, resolved) {
        results[ticker] = ACTIVE
      } ELSE {
        // A sustaining condition broke but no failure_signals/degraded_signals condition
        // explicitly fired — this is a §13 authoring gap, not a silent pass.
        results[ticker] = DEGRADED
        FLAG: "[ticker] a sustaining_condition failed to hold but no matching degraded_signals
               or failure_signals condition exists in §13. Treated as DEGRADED (conservative).
               Flag for §13 review — add an explicit signal for this case."
      }
    }

    RETURN results
  }

  NEVER {
    feed_ThesisStatus_into_M03_DeriveScenarioProbabilities,
    default_to_ACTIVE_on_missing_data__report_UNKNOWN,
    add_a_fourth_AI_interpretation_boundary__route_judgment_conditions_through_M02_M03_only,
    evaluate_a_judgment_condition_by_having_M19_itself_read_free_text__use_Call_2_ScoringQuestion,
    hardcode_per_ticker_conditions_here__CALIBRATION_STATE_section_13_is_authoritative,
    treat_absence_of_a_section_13_entry_as_UNKNOWN__absence_is_a_scope_decision_see_preamble
  }

  // ─── BRIEFING REGISTRY ENTRY (Phase 2 pattern) ───────────────────────────────
  // BriefingRegistry.assemble() in M04 iterates this entry. M04 does not change.

  BRIEFING_REGISTRY_ENTRY
  REGISTER BriefingSectionSpec {
    id:             "THESIS_CONDITION_STATUS"
    title:          "THESIS CONDITION STATUS"
    position_after: "CURRENT_HOLDINGS"     // M04's section id
    module_id:      M19
    render_fn:      "M19.BriefingBlock"
  }

  // ─── BRIEFING BLOCK ───────────────────────────────────────────────────────
  // SUPPRESS rule: omit rows where status == ACTIVE, UNLESS every held/tracked ticker
  // is ACTIVE this session — then render a single all-clear line instead of a table.
  // Non-ACTIVE rows always include the supporting M02 qualitative narrative (Call 1
  // topic text), never just the status label alone.

  BriefingBlock {
    all_clear:     Boolean   // true IFF every evaluated ticker == ACTIVE
    rows:          List<{ ticker, status, fired_condition_text, supporting_narrative? }>
                   // supporting_narrative populated only for DEGRADED | FAILED | UNKNOWN
  }

}
```
