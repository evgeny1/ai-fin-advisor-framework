# M08 — Functional Roles (Dynamic Position Classification)
<!-- Applied at execution time by all Scenario Execution Protocols -->
<!-- Cross-references: @see M09_ScenariosABC, @see M10_ScenariosDEF -->

```
MODULE FunctionalRoles {

  // ─── CORE RULE ───────────────────────────────────────────────────────────
  // Classify holdings at EXECUTION TIME from the current allocation file.
  // Do not carry forward prior classification — re-evaluate each session.

  ENUM Role {
    geopolitical_premium
    inflation_hedge_precious_metals
    inflation_hedge_commodity_linked
    real_asset_contracted_revenue
    policy_driven_thematic_equity
    rate_sensitive_income_short_duration
    rate_sensitive_income_long_duration
    broad_market_equity_domestic
    broad_market_equity_international
  }

  // ─── CLASSIFICATION TESTS ────────────────────────────────────────────────

  FUNCTION classifyRole(holding) -> Role {

    IF holding.primary_value_driver DEPENDS_ON
       [elevated_conflict, defense_procurement, geopolitical_tension]
      → RETURN geopolitical_premium

    IF holding.primary_value_driver DEPENDS_ON
       [real_yield_compression, monetary_base_expansion, dollar_reserve_status_erosion]
       AND holding IS gold_or_silver_instrument
      → RETURN inflation_hedge_precious_metals
        // Structure-type addendum:
        //   physical_bullion | grantor_trust (SGOL, GLD, IAU):
        //     note: custodian_chain_risk; no_roll_yield_exposure; closest_to_pure_thesis
        //   futures_backed:
        //     note: roll_yield_drag_in_contango; counterparty_exposure
        //     → partially compromises hedge thesis in systemic stress

    IF holding.primary_value_driver DEPENDS_ON
       [broad_commodity_prices, energy, materials]
       AND NOT gold_or_silver_instrument
      → RETURN inflation_hedge_commodity_linked
        // Structure-type addendum:
        //   physically_backed_commodity_ETF:
        //     note: custodian_chain_risk; no_roll_yield_exposure; closest_to_pure_thesis
        //   futures_backed_commodity_ETF:
        //     note: roll_yield_drag_in_contango; counterparty_exposure
        //   equity_based_commodity_exposure (stocks, sector_ETFs):
        //     note: earnings_risk + equity_multiple_compression layered on commodity_price
        //     VERIFY: commodity_price remains dominant return driver before classifying here

    IF holding GENERATES_RETURNS_FROM
       [physical_throughput, contracted_fees, real_infrastructure]
       AND NOT [commodity_price, equity_multiples]
      → RETURN real_asset_contracted_revenue

    IF holding.primary_return_driver DEPENDS_ON
       [legislated_government_spending, regulatory_mandates, domestic_policy_cycle]
       AND NOT [aggregate_economic_growth, geopolitical_tension]
      → RETURN policy_driven_thematic_equity
        // Classification note: instruments hold equities of companies that EXECUTE
        // government-directed spending (infrastructure builders, energy transition
        // contractors, defense manufacturing under legislative mandate).
        // VERIFY at classification time: legislative spending mandate still intact.
        // IF mandate materially_cut | repealed | indefinitely_delayed (T1 confirmed)
        //   → downgrade to watch_status and reassess classification

    IF holding.return_profile DETERMINED_BY short_term_interest_rates
       AND holding.maturity_or_duration <= 1y
      → RETURN rate_sensitive_income_short_duration

    IF holding.return_profile DETERMINED_BY long_term_interest_rates
       AND holding.duration > 1y
      → RETURN rate_sensitive_income_long_duration

    IF holding IS passive_or_broad_based
       AND tracking: domestic_aggregate_economic_growth
      → RETURN broad_market_equity_domestic

    IF holding IS passive_or_broad_based
       AND tracking: ex_US_aggregate_economic_growth
      → RETURN broad_market_equity_international

  }

  // ─── DUAL-ROLE CONFLICT RESOLUTION ──────────────────────────────────────

  RULE DualRoleConflict(holding, roleA, roleB) {
    IF holding qualifies_under roleA AND roleB {
      IF prescribed_actions ARE same_direction {
        APPLY: more_conservative_action
      }
      IF prescribed_actions ARE opposite_direction {
        // e.g. one says exit, other says hold/add
        NEVER: default_to_more_conservative_label
        INSTEAD {
          IDENTIFY: which_role_represents_larger_share_of_return_driver
                    // based on most recent position review
          APPLY:    that_role's_instruction
          IF dominant_role_cannot_be_determined_this_session {
            FLAG:   position_for_manual_review
            ACTION: none  // until resolved
          }
        }
      }
    }
  }

  // ─── TAX PLACEMENT AT EXECUTION ──────────────────────────────────────────
  // Apply to every entry and exit across all scenario protocols.

  RULE ExecutionTaxPlacement(direction, position) {
    IF direction == reducing {
      IF position.embedded == loss {
        EXIT: taxable_accounts_first  // tax-loss harvesting applies
      }
      IF position.embedded == gain {
        EXIT: tax_sheltered_accounts_first
        // realizing large embedded gain in taxable = avoidable immediate tax liability
        CONFIRM: which_account_carries_the_gain before_acting
      }
    }
    IF direction == adding {
      ADD: tax_sheltered_accounts_first  // in all scenarios
    }
  }

  // ─── GENERAL EXECUTION GUARDS (all scenario protocols) ───────────────────

  GUARD ExecutionGuards {
    NEVER:  act_on single_unverified_report
    ALWAYS: require T1_evidence_confirmation before_execution
    ALWAYS: document specific_evidence_that_triggered_execution before_acting

    // Graduated Response Rule
    IF scenario.probability IN [30%, 39%] {
      execute: partial_rotation
      execute_only: highest_urgency_actions (marked High | Immediate)
              AT:   50%_of_prescribed_position_change
      NEVER:  execute medium_or_low_urgency_actions
    }
    IF scenario.probability >= 40% {
      execute: full_rotation_sequence as_prescribed
    }
  }

  // ─── DE-ESCALATION RULE (all scenarios except E) ─────────────────────────

  RULE DeEscalation(scenario) {
    threshold = IF scenario == E → 20% ELSE → 25%

    IF scenario.probability < threshold
       AND execution_has_begun {
      INITIATE: unwinding in_reverse_order_of_entry_sequence
      APPLY:    same_tax_placement_logic used_on_entry
      REQUIRE:  T1_evidence_of_directional_reversal before_unwinding
                // single_session_probability_drop is NOT sufficient
    }
  }

}
```
