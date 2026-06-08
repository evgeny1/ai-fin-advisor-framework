# M16 — Return Table Calibration
<!-- Version: 1.0 | Updated: see git log -->

<!-- MODULE MANIFEST
  ID:              M16_ReturnTableCalibration
  Version:         1.0
  Sub-project:     ANALYSIS_ENGINE
  Reason to change: §4.1 revision methodology, confidence level definitions, or 4-layer procedure changes.
                    Governs revision only — M13 and M15 consumption rules are not overridden by M16.
  Inputs consumed:  CALIBRATION_STATE §4.1 (table being revised)
                    historical return data (from M18 HISTORICAL_INSTRUMENT_PRICES on demand)
                    neutral scenario distribution A=35/B=15/C=15/D=10/E=5/F=20 (Layer 4 — always, never current operating)
  Outputs produced: revised §4.1 entries at HIGH/MEDIUM/LOW confidence; CalibrationLogEntry
  Calibration deps: CALIBRATION_STATE §4.1 (the table being revised)
                    CALIBRATION_STATE §3 via Calibration_Log.md (revision history)
  Types consumed:   @see FW_Types.md — CalibrationLogEntry, ConfidenceLevel
-->

```
MODULE ReturnTableCalibration {

  // ─── §1 PURPOSE AND SCOPE ─────────────────────────────────────────────────────

  SCOPE {
    GOVERNS:   maintenance, revision, and audit of CALIBRATION_STATE §4.1
               Expected Real Annualized Return Table
    TABLE_LIVES_IN: CALIBRATION_STATE.md §4.1
                    (CALIBRATION_DATED — fetched every session; values never hardcoded)
    THIS_MODULE_OWNS: rules for HOW the table is revised; not the values themselves
    CONSUMED_BY: [
      M13_GrowthObjectives.idealAllocation()               // growth objective computations
      M15_InstrumentClassification.blendedScenarioReturn() // per-instrument scenario return
    ]
    NEVER: M16 overrides M13 or M15 on consumption rules
  }

  // ─── §2 CALIBRATION METHODOLOGY — 4-LAYER FRAMEWORK ──────────────────────────

  FUNCTION CalibrationMethodology(role, scenario) {
    // All 4 layers are required before any §4.1 revision is adopted.
    // Returns: (revised_range, confidence_level, layer_citations)

    // ── Layer 1: Structural / Unconditional Anchor ─────────────────────────────
    LAYER_1 UnconditionalAnchor {
      SOURCE_TIER: T1 required (annual institutional publications only)
      SOURCES: [
        "JPM Long-Term Capital Market Assumptions (LTCMA) — annual Q4",
        "Vanguard Capital Markets Model (VCMM) — annual or semi-annual",
        "Research Affiliates Expected Returns — annual",
        "GMO / Morningstar Asset Class Return Survey"
      ]
      // T2 cross-references may supplement but CANNOT serve as primary anchor.

      FOR_EACH role:
        ESTABLISH: long-run unconditional expected real return
        NOTE: unconditional = scenario-weighted under NEUTRAL_DISTRIBUTION
              NEUTRAL_DISTRIBUTION { A=35, B=15, C=15, D=10, E=5, F=20 }
              // NOT the current operating (crisis-skewed) distribution

      UPDATE_CADENCE: annually at Q4 audit OR upon new institutional publication
    }

    // ── Layer 2: Historical Scenario Analogue Mapping ──────────────────────────
    LAYER_2 HistoricalAnalogue {
      SCENARIO_TO_PERIOD_MAP {
        A: ["1991 Gulf War normalization", "2003 Iraq War drawdown", "2016 commodity rebound"]
        B: ["1973-1982 stagflation", "2022 rate-shock stagflation"]
        C: ["1974 oil shock", "1979-1980 second oil crisis", "2022 H1 acute inflation"]
        D: ["2008-09 Global Financial Crisis", "2020 COVID shock"]
        E: ["2008 acute systemic (Sep-Nov)", "1998 LTCM crisis", "1987 crash"]
        F: ["1995-2000 tech boom", "2017-2019 goldilocks", "2023-2024 soft landing"]
      }

      FOR_EACH (role, scenario):
        IDENTIFY: instrument or index that proxies this role during the analogue period
        COMPUTE:  annualized real return during that analogue period
        CITE:     data source for each historical return
          // Acceptable: Morningstar Direct, CAIA materials, Shiller CAPE dataset,
          //   Alerian MLP Index history, FRED, Bloomberg Historical (T1 or T2)

      IF no clean analogue exists (e.g., TIPS pre-2000, AI ETFs pre-2018):
        PROXY: CPI-adjusted return of nearest available comparable series
        FLAG:  ⚠ proxy used — auto-escalate to LOW confidence
    }

    // ── Layer 3: Structural Adjustments ───────────────────────────────────────
    LAYER_3 StructuralAdjustments {
      FOR_EACH material_difference BETWEEN current_instance AND historical_analogue:
        DOCUMENT: the specific structural difference and its directional impact
          // Examples of valid structural adjustments:
          //   Modern MLPX is more deleveraged than 2014 MLP sector → D/E risk lower
          //   AI revenue changes secular_technology_growth C return vs 2022
          //   TIPS real yield starting point differs from 1970s T-bill proxy
        EVIDENCE:    T1 or T2 citation required for each structural claim
        FALSIFIABLE: each claim must specify what observable data would invalidate it
        NOTE: structural adjustments justify deviation from Layer 2 analogue;
              they do NOT substitute for Layer 2 evidence
    }

    // ── Layer 4: Consistency Check ────────────────────────────────────────────
    LAYER_4 ConsistencyCheck {
      APPLY NEUTRAL_DISTRIBUTION { A=35, B=15, C=15, D=10, E=5, F=20 }
      COMPUTE: scenario-probability-weighted average of revised [conservative]
               values across all 6 scenarios for this role
      COMPARE: to Layer 1 unconditional institutional estimate for this role

      IF abs(computed_weighted_avg - institutional_unconditional) <= 3.0 pp:
        STATUS: PASS — proceed to adoption per §4 RevisionAdoption rules

      IF abs(computed_weighted_avg - institutional_unconditional) > 3.0 pp:
        STATUS: DOCUMENT_AND_FLAG
        DOCUMENT: explanation (one or more applicable):
          (a) Current starting valuation deviates materially from historical average
          (b) Role newly created (< 4 quarters live data) — LOW confidence expected
          (c) Structural adjustment dominates — cite Layer 3 evidence explicitly
          (d) Role has no full historical analogue — proxy used; gap is expected
        FLAG: in CALIBRATION_STATE §6 audit checklist for review at next Q-end audit

      MUST_RUN: after EVERY revision to any §4.1 cell, including intra-session adoptions
    }

    REQUIRE: all 4 layers completed before any revision is adopted
    RETURN: (revised_range, confidence_level, layer_citations)
  }

  // ─── §3 CONFIDENCE LEVEL DEFINITIONS ──────────────────────────────────────────

  ENUM ConfidenceLevel {
    HIGH {
      "3+ distinct historical analogues for this (role, scenario) pair"
      "institutional agreement within 2pp across sources"
      "structural adjustment absent OR minor (< 1pp directional impact)"
    }
    MEDIUM {
      "1-2 historical analogues"
      "some institutional agreement (sources within 5pp)"
      "structural adjustment present but bounded (< 3pp directional impact)"
    }
    LOW {
      "fewer than 1 clean analogue (proxy required or no historical data)"
      "institutional disagreement (sources diverge > 5pp)"
      "structural adjustment dominates return estimate"
      "role newly created (< 4 quarters of live performance data)"
    }
  }

  RULE ConfidenceLevelApplication {
    ASSIGN: confidence level to EVERY §4.1 cell at each Q-end full audit

    IF confidence == LOW:
      USE:     conservative end of range in ALL EV computations (never midpoint)
      SUPPRESS: upside end — omit from scenario-weighted allocation math
                (may appear in briefing as informational context only)
      TRIGGER: mandatory immediate review IF scenario probability for this cell's
               scenario exceeds 40% before the next scheduled Q audit

    IF confidence IN [MEDIUM, HIGH]:
      USE: conservative end (standard framework rule — unchanged)
  }

  // ─── §4 REVISION ADOPTION RULES ───────────────────────────────────────────────

  RULE RevisionAdoption {

    REQUIRE for ANY revision:
      - Layer 2: historical analogue evidence (period + cited return data)
      - Layer 1: institutional cross-reference (unconditional anchor)
      - Layer 3: structural adjustment documentation
                 (required IF proposed return deviates > 2pp from Layer 2 historical midpoint)

    CASE confidence == HIGH:
      PERMIT:  intra-session adoption
      REQUIRE: explicit client confirmation before writing to §4.1
      REQUIRE: Layer 4 consistency check passes OR gap documented with explanation

    CASE confidence == MEDIUM:
      LOG:   as pending in CALIBRATION_STATE §6 item 23 (include all Layer citations)
      ADOPT: at next quarterly audit only
      NEVER: intra-session adoption

    CASE confidence == LOW:
      DEFER:   to Q-end audit
      REQUIRE: 2+ quarters of live performance data since proposal date before adoption
      NEVER:   intra-session adoption
  }

  // ─── §5 LIVING UPDATE TRIGGERS (between quarterly audits) ─────────────────────

  RULE LivingUpdateTriggers {
    // These trigger PARTIAL audits of affected cells only — not a full table audit.
    // Document trigger event and affected cells in §6 audit checklist each time fired.

    TRIGGER scenario_B_or_C_dominant {
      CONDITION: scenario_probability(B) > 50% OR scenario_probability(C) > 50%
      ACTION: re-run Layer 4 consistency check for dominant scenario's rows (all roles)
              FLAG any cell where weighted avg diverges > 2pp from Layer 2 historical analogue
      SCOPE: dominant scenario column only
    }

    TRIGGER cpi_print_extreme {
      CONDITION: new CPI print >= 4.0% YoY OR new CPI print <= 2.5% YoY
      ACTION:    mandatory review of Scenario B and C rows for ALL roles
      SCOPE:     B and C columns only
    }

    TRIGGER institutional_ltcma_revision {
      CONDITION: JPM LTCMA or Vanguard VCMM annual publication released
      ACTION:
        re-anchor Layer 1 unconditional reference points for ALL roles
        FLAG any cell where Layer 1 unconditional shifts > 1.5pp vs prior anchor
      SCOPE: all roles; unconditional column only
    }

    TRIGGER ai_earnings_sustained {
      CONDITION: 2+ consecutive quarters with AI/cloud revenue growth > 25%
                 AND active scenario includes C component (C probability > 20%)
      ACTION:    secular_technology_growth Scenario C cell mandatory re-anchor
                 MAY revise upward IF Layer 2 + Layer 3 evidence independently supports
      SCOPE:     secular_technology_growth Scenario C cell only
    }

    TRIGGER mlp_leverage_rise {
      CONDITION: MLP sector average debt-to-EBITDA > 4.5x (sustained 2+ quarters)
      ACTION:    real_asset_contracted_revenue Scenario D and E risk premium review
                 Expected direction: D and E return estimates move more negative
      SCOPE:     real_asset_contracted_revenue D and E cells
    }

    TRIGGER scenario_A_rising {
      CONDITION: scenario_probability(A) exceeds 30%
      ACTION:    geopolitical_premium Scenario A cell mandatory review
                 // War resolution historically produces defense de-rating
      SCOPE:     geopolitical_premium Scenario A cell
    }
  }

  // ─── §6 SCHEDULED AUDIT CADENCE ───────────────────────────────────────────────

  SCHEDULE AuditCadence {

    FULL_AUDIT {
      DATES: [June 30, September 30, December 31, March 31]
      SCOPE: [
        "ALL cells in §4.1 — re-assess confidence level for every cell",
        "Run Layer 4 consistency check for all roles",
        "Incorporate new quarterly institutional publications (Layer 1 update)",
        "Formally adopt or reject all pending proposals from §6 item 23",
        "Document adopted proposals with full Layer 2-3 citations",
        "Assign confidence levels (HIGH/MEDIUM/LOW) to all cells since last audit",
        "Add historical analogue period citations to each §4.1 row as permanent column",
        "Update §3 Calibration Log entry in CALIBRATION_STATE"
      ]
    }

    PARTIAL_AUDIT {
      TRIGGER: per §5 LivingUpdateTriggers
      SCOPE:   affected cells only (not a full table audit)
      DOCUMENT: in §6 audit checklist: which trigger fired, which cells reviewed, outcome
    }

    POST_AUDIT_ALWAYS {
      // Execute after EVERY full or partial audit that changes any §4.1 value:
      STEP 1: update §3 Calibration Log in CALIBRATION_STATE (version bump)
      STEP 2: re-run M15.blendedScenarioReturn() for all active instruments
      STEP 3: re-run M13.FeasibilityCheck() for all accounts using revised EVs
      STEP 4: update §11 instrument EV figures in CALIBRATION_STATE
    }
  }

  // ─── §7 PRECEDENCE ─────────────────────────────────────────────────────────────

  PRECEDENCE {
    M16 governs:  HOW §4.1 is revised
                  (methodology, evidence standards, confidence levels, adoption rules)
    M13 governs:  HOW §4.1 is consumed for growth objectives — NOT overridden by M16
    M15 governs:  HOW §4.1 is consumed per instrument via blendedScenarioReturn() — NOT overridden by M16
    CONFLICTS:    M16 revision methodology rules take precedence over ad-hoc session judgment
    POSITION:     M16 is at precedence level 2.5 (above M13, below M12)
                  @see 00_INDEX PRECEDENCE rules
  }

  GUARD NeverReviseWithoutMethodology {
    NEVER: revise any §4.1 cell without completing all 4 layers of CalibrationMethodology()
    NEVER: adopt a MEDIUM or LOW confidence revision intra-session — log and defer
    NEVER: run Layer 4 using the current operating scenario distribution —
           ALWAYS use NEUTRAL_DISTRIBUTION { A=35, B=15, C=15, D=10, E=5, F=20 }
    NEVER: omit Layer 3 structural adjustment documentation to accelerate adoption
    NEVER: adopt a HIGH confidence revision intra-session without explicit client confirmation
  }

}
```
