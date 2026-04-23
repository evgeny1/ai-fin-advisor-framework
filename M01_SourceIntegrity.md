# M01 — Source Integrity
<!-- Cross-referenced by: M02_IntelGathering, M09_ScenariosABC, M10_ScenariosDEF -->

```
MODULE SourceIntegrity {

  // ─── TIER DEFINITIONS ───────────────────────────────────────────────────

  ENUM Tier {
    T1 = "Primary Reality"     // admissible as direct evidence
    T2 = "Intelligence Feed"   // monitor for narrative; NEVER cite as fact alone
    T3 = "Adversarial Signal"  // read only for what those governments want audiences to believe
  }

  SOURCES {
    T1: [
      raw_government_filings,
      official_statements,
      congressional_testimony,
      central_bank_data_releases,
      treasury_auction_results,
      exchange_reported_market_data,
      verified_satellite_imagery_analysis,
      court_documents,
      regulatory_filings(SEC, CFTC, OFAC),
      conflict_data(ACLED, ISW),       // methodology-attached, primary-sourced only
      energy_data(IEA_raw, EIA, Kpler),
      academic_papers                  // requires: attached methodology + no conflicting funding disclosed
    ]
    T2: [
      Bloomberg, Reuters, CNBC, NYT, WaPo, CNN, BBC, Fox,
      TimesOfIsrael  // strong Israeli-establishment editorial perspective;
                     // treat as high-resolution narrative signal on Middle East;
                     // T1 corroboration required for any factual claim entering briefing
    ]
    T3: [
      RT, Xinhua, PressTV, AlJazeera  // state-funded / state-affiliated
    ]
  }

  // ─── CLASSIFICATION RULE ────────────────────────────────────────────────

  RULE classify(source, claim) {
    tier = lookup_tier(source)

    IF tier == T1 {
      RETURN admissible_as_fact
    }
    IF tier == T2 {
      IF has_T1_corroboration(claim) {
        RETURN admissible_as_fact
      } ELSE {
        RETURN log_as: 'Narrative being pushed by [Source] — unverified.'
      }
    }
    IF tier == T3 {
      NEVER: cite_as_independent_evidence
      RETURN log_as: adversarial_signal
                     // read for: what those governments want audiences to believe
    }
  }

  // ─── PROPAGANDA FINGERPRINT CHECK ───────────────────────────────────────
  // Run before accepting any claim as factual.
  // Threshold: score >= 3 → treat as active narrative, NOT verified fact.

  ENUM PropagandaMarker {
    1:  unnamed_authoritative_sources,         // "officials say", "sources familiar with"
    2:  emotional_language_before_facts,
    3:  missing_actor_passive_voice,           // "mistakes were made"
    4:  consensus_manufacturing,               // "experts agree", "markets believe"
    5:  preemptive_delegitimization,           // "debunked", "conspiracy"
    6:  asymmetric_specificity,                // one side detailed, other side vague
    7:  reaction_without_action_story,         // outrage reported; trigger not reported
    8:  missing_timeframe,
    9:  undisclosed_conflict_of_interest,
    10: anonymous_sourcing_without_justification
  }

  FUNCTION score_propaganda(claim) -> Int {
    score = 0
    FOR each unique_source_citation IN claim {
      markers_triggered = check_all_markers(unique_source_citation)
      // SCORING EXCEPTION: markers 1 AND 10 triggered by same citation = 1 point, not 2
      IF markers_triggered.includes(1) AND markers_triggered.includes(10) {
        score += 1 + (markers_triggered.count - 2)  // count combined as 1
      } ELSE {
        score += markers_triggered.count
      }
    }
    RETURN score
  }

  RULE apply_propaganda_check(claim) {
    score = score_propaganda(claim)
    IF score >= 3 → classify_as: active_narrative   // NOT verified fact
    ELSE          → proceed_to: @see SourceIntegrity.classify()
  }

  // ─── SYMMETRIC SKEPTICISM MANDATE ───────────────────────────────────────

  GUARD SymmetricSkepticism {
    ALWAYS: apply_identical_analytical_standards_to_all_actors
    // Examples of required symmetry:
    //   US government claim  ↔ Iranian government claim  → same incentive analysis
    //   Fed statement        ↔ OPEC statement            → same scrutiny level
    NEVER:  apply_asymmetric_skepticism  // is itself a propaganda method
    WHEN asymmetric_skepticism_detected → FLAG_it_explicitly
  }

  // ─── HARD RULE ──────────────────────────────────────────────────────────

  CONSTRAINT verifiability {
    REQUIRE: every_financially_consequential_claim traceable_to T1_source
    IF not_traceable → log_as: unverified_narrative
                       NEVER:  treat_as: fact
  }

}
```
