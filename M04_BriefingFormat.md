# M04 — Briefing Format
<!-- Produced at: start of every session, before any portfolio analysis -->
<!-- Cross-references: @see M02_IntelGathering, @see M03_ScenarioFramework, @see M11_CreditAndCalibration.BriefingBlock -->
<!-- Extended by: M14_MarketRegime (MarketRegimeSignal section inserted after EQUITY MARKETS) -->

```
MODULE BriefingFormat {

  // ─── HOLDINGS STATUS LABELS ──────────────────────────────────────────────

  ENUM HoldingStatus {
    thesis_intact:  "No new information challenges the structural basis for the position."
    watch:          "One or more emerging conditions warrant monitoring but do not yet invalidate thesis."
    flagged:        "A specific threshold or condition has been breached; requires active review or position action this session."
  }

  // ─── TEMPLATE ────────────────────────────────────────────────────────────
  // Produce this output at session start before any portfolio analysis.
  // Credit block inserted between FIXED INCOME and CURRENCY per M11_CreditAndCalibration.BriefingBlock
  // Market regime block inserted after EQUITY MARKETS per M14_MarketRegime.BriefingBlock

  TEMPLATE IntelligenceBriefing {

    HEADER {
      ═══════════════════════════════════════════════
      PORTFOLIO INTELLIGENCE BRIEFING
      Date: [DATE] | Time: [TIME ET]
      Framework Extension v[N] loaded              // REQUIRED — @see M05_SessionInit
      Calibration State loaded, last update: [date] // REQUIRED — @see M05_SessionInit
      ═══════════════════════════════════════════════
    }

    SECTION PrimaryDriver {
      // Output of @see M02_IntelGathering.identifyPrimaryDriver()
      current_dominant_driver: ___
      challenger_drivers:       ___
      recalibration_trigger_check: Yes | No
    }

    SECTION ScenarioProbabilities {
      // Produced by @see M03_ScenarioFramework.DeriveScenarioProbabilities()
      // NEVER present final probabilities without showing the scoring underneath.
      // Must sum to 100%.

      FORMAT per_scenario {
        [Label] ([Name]):  [final_%]
          binding_variable: [name]
          scores: [check_name]=[score] | [check_name]=[score] | ...
          raw: [N] / [max]  →  base: [X%]  →  final: [Y%]
          [floor_applied: [note] | cap_applied: [note] | neither]
      }

      DERIVATION_FOOTER {
        Total:                  100%
        Method:                 scored | manual_override
        // IF manual_override: REQUIRE explicit T1 evidence documented here
        Prior session anchor:   [date and prior probabilities] | "initial derivation"
        Floors applied:         [list] | none
        Caps applied:           [list] | none
        B/C justification:      [required text if B > 30% AND C > 30%] | N/A
      }

      CHANGES {
        // Show delta vs prior session anchor for each scenario where delta > 0
        // State explicitly what T1 evidence caused each move
        // IF initial derivation: omit this block and note "initial derivation — no prior anchor"
        FORMAT per_change: '[Scenario]: [prior%] → [final%] ([+/-]pp) — evidence: [T1 source]'
      }
      ───────────────────────────────────────────────
    }

    SECTION EnergyAndCommodities {
      Brent_Crude:   $___  [+/-%]
      WTI:           $___  [+/-%]
      Natural_Gas:   $___  [+/-%]
      Gold_spot:     $___  [+/-%]
      Silver:        $___  [+/-%]
      Signal: [one sentence]
      ───────────────────────────────────────────────
    }

    SECTION EquityMarkets {
      SP500:       ___  [+/-%]
      NASDAQ:      ___  [+/-%]
      Dow:         ___  [+/-%]
      Russell2000: ___  [+/-%]
      VIX:         ___  [+/-%]
      Signal: [one sentence — risk appetite]
      ───────────────────────────────────────────────
    }

    SECTION MarketRegimeSignal {
      // Output of @see M14_MarketRegime.ComputeDivergenceSignal()
      //        and @see M14_MarketRegime.UnderweightReviewTrigger()
      VIX_current vs 30d avg vs 90d avg:   ___ vs ___ vs ___  ([+/-] pts vs 90d avg)
      Broad_equity_30d / 60d / 90d:        [+/-%] / [+/-%] / [+/-%]
      commodity_fear_divergence:           [HIGH | MODERATE | NONE]
      equity_scenario_divergence:          [HIGH | MODERATE | NONE | N/A]
      composite_signal:                    [HIGH | MODERATE | NONE]
      Implication: [one sentence]
      Underweight positions flagged for EV review: [list] | none
      ───────────────────────────────────────────────
    }

    SECTION FixedIncomeAndRates {
      treasury_10Y:   ___% [+/- bps]
      treasury_2Y:    ___% [+/- bps]
      fed_funds_rate: ___% [current]
      MOVE_index:     ___  [+/-%]
      Signal: [one sentence — bond stress / rate trajectory]
      ───────────────────────────────────────────────
    }

    SECTION CreditStress {
      // Inserted here per @see M11_CreditAndCalibration.BriefingBlock
      HY_OAS_composite:    ___ bps  [Δ vs 30d / 90d]
      CCC_OAS:             ___ bps  [Δ vs 30d / 90d]
      IG_OAS:              ___ bps  [Δ vs 30d / 90d]
      MOVE_index:          ___      [Δ vs 30d]
      trailing_180d_median_HY: ___ bps
      trailing_180d_median_IG: ___ bps
      Signal: [one sentence — credit endorsing or dissenting from equity]
      data_quality_flag: T1_confirmed | composite_only | stale
      ───────────────────────────────────────────────
    }

    SECTION Currency {
      DXY: ___  [+/-%]
      Signal: [one sentence — dollar implications for portfolio]
      ───────────────────────────────────────────────
    }

    SECTION CurrentHoldings {
      // Live prices. Apply @see M02_IntelGathering.PriceDataIntegrity
      FORMAT per_holding: [Ticker]: $___  [+/-% today]  [HoldingStatus]
      ───────────────────────────────────────────────
    }

    SECTION GeopoliticalSignal {
      // 2–4 bullets only
      FORMAT per_development {
        - [Development]
          Mechanisms: Primary → [effect] / Secondary → [effect]
          Scenario_impact: [A|B|C|D|E|F]
      }
      UNVERIFIED_NARRATIVES {
        FORMAT: '"[Claim]" — source: [Name]. Unverified. Technique: [identify it]'
      }
      ───────────────────────────────────────────────
    }

    SECTION PendingTriggers {
      FORMAT per_trigger: '- [Trigger] — deadline [date/time] — if_fired: [X] — if_not: [Y]'
      ───────────────────────────────────────────────
    }

    SECTION NetAssessment {
      // 2–3 sentences MAX
      // What does evidence say about positioning?
      // What is the single most important issue this session?
      ═══════════════════════════════════════════════
    }

  }

}
```
