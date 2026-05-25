# M04 — Briefing Format
<!-- Version: 2.0 | Adopted: May 25, 2026 -->
<!-- Changes from v1.x: Phase 2 complete — hardcoded section list replaced by BRIEFING_REGISTRY_ENTRIES; -->
<!--   TEMPLATE body now calls BriefingRegistry.assemble(readings); MODULE_MANIFEST added; -->
<!--   render functions added for all M04-owned sections. -->
<!--   M04 is now a thin wiring layer: HEADER hardcoded; sections driven by registry. -->
<!--   Adding a new module's briefing section: register BRIEFING_REGISTRY_ENTRY in the owning -->
<!--   module; M04 does not change. -->
<!-- Cross-references: @see M02_IntelGathering, @see M03_ScenarioFramework -->
<!-- M11 (CREDIT_SIGNALS), M14 (MARKET_REGIME_SIGNAL), M17 (CASCADE_EARLY_WARNING) own their sections. -->

<!-- MODULE MANIFEST
  ID:              M04_BriefingFormat
  Version:         2.0
  Sub-project:     ORCHESTRATION
  Reason to change: session output format changes; OR M04-owned briefing section content changes.
                    Adding a new module's briefing section: register BRIEFING_REGISTRY_ENTRY
                    in the owning module; M04 does not change.
  Inputs consumed:  List<DataReading>            // from FetchRegistry.fetchAll() via M02
                    ScenarioProbabilities        // from M03.DeriveScenarioProbabilities()
  Outputs produced: OrderedList<BriefingSection>
  Calibration deps: none
  Types consumed:   @see FW_Types.md — DataReading, BriefingSection, BriefingSectionSpec, BriefingRegistry
-->

```
MODULE BriefingFormat {

  // ─── HOLDINGS STATUS LABELS ──────────────────────────────────────────────────────────

  ENUM HoldingStatus {
    thesis_intact:  "No new information challenges the structural basis for the position."
    watch:          "One or more emerging conditions warrant monitoring but do not yet invalidate thesis."
    flagged:        "A specific threshold or condition has been breached; requires active review or position action this session."
  }


  // ─── BRIEFING REGISTRY ENTRIES (M04-owned sections) ─────────────────────────────────
  // Phase 2 complete: BriefingRegistry.assemble() iterates all entries from all modules.
  // M11 (CREDIT_SIGNALS), M14 (MARKET_REGIME_SIGNAL), M17 (CASCADE_EARLY_WARNING)
  //   register their own entries independently; M04 references their ids in position_after.

  BRIEFING_REGISTRY_ENTRY {
    REGISTER BriefingSectionSpec {
      id:             "PRIMARY_DRIVER"
      title:          "PRIMARY DRIVER"
      position_after: null          // first section after HEADER
      module_id:      M04
      render_fn:      "M04.render_PRIMARY_DRIVER"
    }
  }

  BRIEFING_REGISTRY_ENTRY {
    REGISTER BriefingSectionSpec {
      id:             "SCENARIO_PROBABILITIES"
      title:          "SCENARIO PROBABILITIES"
      position_after: "PRIMARY_DRIVER"
      module_id:      M04
      render_fn:      "M04.render_SCENARIO_PROBABILITIES"
    }
  }

  BRIEFING_REGISTRY_ENTRY {
    REGISTER BriefingSectionSpec {
      id:             "ENERGY_AND_COMMODITIES"
      title:          "ENERGY & COMMODITIES"
      position_after: "SCENARIO_PROBABILITIES"
      module_id:      M04
      render_fn:      "M04.render_ENERGY_AND_COMMODITIES"
    }
  }

  BRIEFING_REGISTRY_ENTRY {
    REGISTER BriefingSectionSpec {
      id:             "EQUITY_MARKETS"
      title:          "EQUITY MARKETS"
      position_after: "ENERGY_AND_COMMODITIES"
      module_id:      M04
      render_fn:      "M04.render_EQUITY_MARKETS"
    }
  }

  // "MARKET_REGIME_SIGNAL" — position_after: "EQUITY_MARKETS" — owned and registered by M14

  BRIEFING_REGISTRY_ENTRY {
    REGISTER BriefingSectionSpec {
      id:             "FIXED_INCOME_AND_RATES"
      title:          "FIXED INCOME & RATES"
      position_after: "MARKET_REGIME_SIGNAL"    // M14's registered section id
      module_id:      M04
      render_fn:      "M04.render_FIXED_INCOME_AND_RATES"
    }
  }

  // "CREDIT_SIGNALS" — position_after: "FIXED_INCOME_AND_RATES" — owned and registered by M11
  // "CASCADE_EARLY_WARNING" — position_after: "CREDIT_SIGNALS" — owned and registered by M17

  BRIEFING_REGISTRY_ENTRY {
    REGISTER BriefingSectionSpec {
      id:             "CURRENCY"
      title:          "CURRENCY"
      position_after: "CASCADE_EARLY_WARNING"   // M17's registered section id
      module_id:      M04
      render_fn:      "M04.render_CURRENCY"
    }
  }

  BRIEFING_REGISTRY_ENTRY {
    REGISTER BriefingSectionSpec {
      id:             "CURRENT_HOLDINGS"
      title:          "CURRENT HOLDINGS"
      position_after: "CURRENCY"
      module_id:      M04
      render_fn:      "M04.render_CURRENT_HOLDINGS"
    }
  }

  BRIEFING_REGISTRY_ENTRY {
    REGISTER BriefingSectionSpec {
      id:             "GEOPOLITICAL_SIGNAL"
      title:          "GEOPOLITICAL SIGNAL"
      position_after: "CURRENT_HOLDINGS"
      module_id:      M04
      render_fn:      "M04.render_GEOPOLITICAL_SIGNAL"
    }
  }

  BRIEFING_REGISTRY_ENTRY {
    REGISTER BriefingSectionSpec {
      id:             "PENDING_TRIGGERS"
      title:          "PENDING TRIGGERS"
      position_after: "GEOPOLITICAL_SIGNAL"
      module_id:      M04
      render_fn:      "M04.render_PENDING_TRIGGERS"
    }
  }

  BRIEFING_REGISTRY_ENTRY {
    REGISTER BriefingSectionSpec {
      id:             "NET_ASSESSMENT"
      title:          "NET ASSESSMENT"
      position_after: "PENDING_TRIGGERS"
      module_id:      M04
      render_fn:      "M04.render_NET_ASSESSMENT"
    }
  }


  // ─── SECTION RENDER FUNCTIONS (M04-owned) ────────────────────────────────────────────
  // Called by BriefingRegistry.assemble(readings). Each produces one BriefingSection.
  // Content format specs are definitive — follow exactly when producing briefing output.
  // render_MARKET_REGIME_SIGNAL → M14.BriefingBlock
  // render_CREDIT_SIGNALS       → M11.BriefingBlock
  // render_CASCADE_EARLY_WARNING→ M17.BriefingBlock

  FUNCTION render_PRIMARY_DRIVER(readings) → BriefingSection {
    // Output of @see M02_IntelGathering.identifyPrimaryDriver()
    content {
      current_dominant_driver: ___
      challenger_drivers:       ___
      recalibration_trigger_check: Yes | No
    }
    ───────────────────────────────────────────────
  }

  FUNCTION render_SCENARIO_PROBABILITIES(readings) → BriefingSection {
    // Produced by @see M03_ScenarioFramework.DeriveScenarioProbabilities()
    // NEVER present final probabilities without showing the scoring underneath.
    // Must sum to 100%.
    content {
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
        Prior session anchor:   [date and prior probabilities] | "initial derivation"
        Floors applied:         [list] | none
        Caps applied:           [list] | none
        B/C justification:      [required text if B > 30% AND C > 30%] | N/A
      }
      CHANGES {
        FORMAT per_change: '[Scenario]: [prior%] → [final%] ([+/-]pp) — evidence: [T1 source]'
      }
    }
    ───────────────────────────────────────────────
  }

  FUNCTION render_ENERGY_AND_COMMODITIES(readings) → BriefingSection {
    content {
      Brent_Crude:   $___  [+/-%]
      WTI:           $___  [+/-%]
      Natural_Gas:   $___  [+/-%]
      Gold_spot:     $___  [+/-%]
      Silver:        $___  [+/-%]
      Signal: [one sentence]
    }
    ───────────────────────────────────────────────
  }

  FUNCTION render_EQUITY_MARKETS(readings) → BriefingSection {
    content {
      SP500:       ___  [+/-%]
      NASDAQ:      ___  [+/-%]
      Dow:         ___  [+/-%]
      Russell2000: ___  [+/-%]
      VIX:         ___  [+/-%]
      Signal: [one sentence — risk appetite]
    }
    ───────────────────────────────────────────────
  }

  FUNCTION render_FIXED_INCOME_AND_RATES(readings) → BriefingSection {
    content {
      treasury_10Y:   ___% [+/- bps]
      treasury_2Y:    ___% [+/- bps]
      fed_funds_rate: ___% [current]
      MOVE_index:     ___  [+/-%]
      Signal: [one sentence — bond stress / rate trajectory]
    }
    ───────────────────────────────────────────────
  }

  FUNCTION render_CURRENCY(readings) → BriefingSection {
    content {
      DXY: ___  [+/-%]
      Signal: [one sentence — dollar implications for portfolio]
    }
    ───────────────────────────────────────────────
  }

  FUNCTION render_CURRENT_HOLDINGS(readings) → BriefingSection {
    // Live prices. Apply @see M02_IntelGathering.PriceDataIntegrity
    content {
      FORMAT per_holding: [Ticker]: $___  [+/-% today]  [HoldingStatus]
    }
    ───────────────────────────────────────────────
  }

  FUNCTION render_GEOPOLITICAL_SIGNAL(readings) → BriefingSection {
    // 2–4 bullets only
    content {
      FORMAT per_development {
        - [Development]
          Mechanisms: Primary → [effect] / Secondary → [effect]
          Scenario_impact: [A|B|C|D|E|F]
      }
      UNVERIFIED_NARRATIVES {
        FORMAT: '"[Claim]" — source: [Name]. Unverified. Technique: [identify it]'
      }
    }
    ───────────────────────────────────────────────
  }

  FUNCTION render_PENDING_TRIGGERS(readings) → BriefingSection {
    content {
      FORMAT per_trigger: '- [Trigger] — deadline [date/time] — if_fired: [X] — if_not: [Y]'
    }
    ───────────────────────────────────────────────
  }

  FUNCTION render_NET_ASSESSMENT(readings) → BriefingSection {
    // 2–3 sentences MAX
    content {
      // What does evidence say about positioning?
      // What is the single most important issue this session?
    }
    ═══════════════════════════════════════════════
  }


  // ─── TEMPLATE ────────────────────────────────────────────────────────────────────────
  // Phase 2 complete: HEADER hardcoded (always first, always same structure).
  // Section body produced by BriefingRegistry.assemble(readings).

  TEMPLATE IntelligenceBriefing(readings: List<DataReading>) {

    HEADER {
      ═══════════════════════════════════════════════
      PORTFOLIO INTELLIGENCE BRIEFING
      Date: [DATE] | Time: [TIME ET]
      Framework Extension v[N] loaded              // REQUIRED — @see M05_SessionInit
      Calibration State loaded, last update: [date] // REQUIRED — @see M05_SessionInit
      ═══════════════════════════════════════════════
    }

    BriefingRegistry.assemble(readings)
    // Iterates all registered BriefingSectionSpec entries in position_after order.
    // Calls render_fn for each — M04-owned and module-owned sections assembled together.
    //
    // Full section ordering (derived from registered position_after chain):
    //   PRIMARY_DRIVER → SCENARIO_PROBABILITIES → ENERGY_AND_COMMODITIES
    //   → EQUITY_MARKETS → MARKET_REGIME_SIGNAL (M14)
    //   → FIXED_INCOME_AND_RATES → CREDIT_SIGNALS (M11)
    //   → CASCADE_EARLY_WARNING (M17)
    //   → CURRENCY → CURRENT_HOLDINGS → GEOPOLITICAL_SIGNAL
    //   → PENDING_TRIGGERS → NET_ASSESSMENT
  }

}
```
