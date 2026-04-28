# Calibration State
Persistent framework configuration — load at every session start alongside session handoff.

Version: 1.5  Last updated: April 27, 2026 (M14 adoption; §9 Market Regime Thresholds added)  Next scheduled review: June 30, 2026 (Q2 2026 quarter-end)

_______________

## Load Verification Requirement
At session start, the advisor must state in the briefing:

"Calibration State loaded, last update: April 27, 2026"

Absence of this line indicates the calibration file was not loaded and the session is invalid for threshold-sensitive decisions.

_______________

## Section 1 — Credit Signal Thresholds (relative, §1.5a)
All HY/CCC/IG thresholds are relative to the trailing 180-day median of the underlying FRED series, computed at session start.

### 1.1 HY Composite — FRED: BAMLH0A0HYM2

| Parameter | Current Value | Type | Notes |
| :-: | :-: | :-: | :-: |
| HY\_STRESS\_DELTA | \+150 bps | Calibration-dated | Provisional initial — full audit pending June 30, 2026 |
| HY\_RECESSION\_DELTA | \+300 bps | Calibration-dated | Provisional initial — full audit pending June 30, 2026 |
| Velocity overlay | \+100 bps over prior 60 days | Fixed structural | Not calibration-dated |
| Sustain period | 10 trading days | Fixed structural | Not calibration-dated |
| D-floor on recession-pricing trigger | 25% | Fixed structural | Not calibration-dated |

Baseline snapshot at instantiation (April 19, 2026): ~285 bps (Trading Economics / FRED point observation — NOT the computed 180-day median). Trailing 180d median to be computed at Q2 2026 audit.

Session observation (April 19, 2026 session): HY composite remains at ~285 bps (Trading Economics). Consistent with baseline snapshot. No velocity check executed this session — full 30-day HY composite history not pulled; fetch planned for next session.

Session observation (April 21, 2026 session): HY composite ~285 bps (Trading Economics; FRED last updated April 15-16 — readings stale by 4-5 days due to weekend + active geopolitical events). Unchanged from April 19 baseline. Velocity check not executable — §7 log needs 60+ trading day history. T1_flag: composite_only | stale. No threshold fires.

Session observation (April 22, 2026 session): HY composite ~287 bps (Trading Economics; FRED last updated April 20). Marginal uptick from April 21 reading. No threshold fires. Velocity check not executable — §7 log needs 60+ trading day history. T1_flag: stale.

Session observation (April 23, 2026 session): HY composite ~287 bps (FRED last updated April 20 — stale 3 days). No change from April 22. No threshold fires. T1_flag: stale.

### 1.2 IG Composite — FRED: BAMLC0A0CM

| Parameter | Current Value | Type | Notes |
| :-: | :-: | :-: | :-: |
| IG\_TRANSMISSION\_DELTA | \+60 bps | Calibration-dated | Provisional initial — full audit pending June 30, 2026 |
| Velocity overlay | \+40 bps over prior 60 days | Fixed structural | Not calibration-dated |
| Sustain period | 10 trading days | Fixed structural | Not calibration-dated |

Baseline at instantiation: Not yet computed. Trailing 180d median to be computed at Q2 2026 audit.

Session observation (April 19, 2026 session): IG composite ~83 bps (Trading Economics). Recorded for baseline reference; no trigger check executed pending 180d median computation.

Session observation (April 21, 2026 session): IG composite ~83 bps (Trading Economics; FRED stale by 4-5 days). Unchanged from April 19 observation. IG_TransmissionReached NOT fired (threshold ~143 bps vs current ~83 bps; gap ~60 bps). T1_flag: composite_only | stale.

Session observation (April 22, 2026 session): IG composite ~83 bps (FRED last updated April 16-17; stale). No change. IG_TransmissionReached NOT fired. T1_flag: stale.

Session observation (April 23, 2026 session): IG composite ~83 bps (FRED last updated April 16-17 — stale 6-7 days). No change. IG_TransmissionReached NOT fired. T1_flag: stale.

### 1.3 CCC Tail — FRED: BAMLH0A3HYC

| Parameter | Current Value | Type | Notes |
| :-: | :-: | :-: | :-: |
| Ratio divergence | CCC widens 3x composite over 30d | Fixed structural | Not calibration-dated |
| Absolute divergence floor | CCC \+200 bps while composite \+\<50 bps over 30d | Calibration-dated | Provisional — audit pending June 30, 2026 |
| Action on trigger | Flag for monitoring; note in next 3 sessions | Fixed structural | Not calibration-dated |

Session observation (April 19, 2026 session) — first concrete divergence computation executed:

| Measurement | Value |
| :-: | :-: |
| CCC OAS on 2026-03-16 (30 trading days prior, approx) | 9.73% = 973 bps |
| CCC OAS on 2026-04-16 (latest FRED observation) | 9.21% = 921 bps |
| CCC 30-day change | −52 bps (tightening) |

Divergence test results:
* Ratio divergence: NOT fired — CCC tightening, not widening
* Absolute divergence: NOT fired — CCC delta negative

Signal: Credit calm across composite and tail. No early-warning divergence. Per §1.5a.2 asymmetric weighting rule, this is absence-of-widening (not actively confirming health), but no dissent signal against risk-on equity regime.

Session observation (April 21, 2026 session): CCC OAS ~921 bps (carried from April 19 FRED observation; no new FRED data published since April 16). CCC_TailFirstWidening NOT fired. T1_flag: stale. No new divergence computation this session — carry forward April 19 result.

Session observation (April 22, 2026 session): CCC OAS ~921 bps (FRED last updated April 17; stale). No new FRED data. CCC_TailFirstWidening NOT fired. T1_flag: stale. Carry forward April 19 divergence result.

Session observation (April 23, 2026 session): CCC OAS ~921 bps (FRED stale; carry forward April 19 result). CCC_TailFirstWidening NOT fired. T1_flag: stale.

_______________

## Section 2 — Other Calibration-Dated Thresholds (Pending Initial Audit)
The following thresholds exist in the main framework and are calibration-dated. Initial formal audit has not been completed for these — they carry forward at their current framework values. Full hit-rate / miss-rate audit scheduled for June 30, 2026 quarter-end review.

### 2.1 Energy / Commodities

| Threshold | Current Value | Source | Audit Status |
| :-: | :-: | :-: | :-: |
| WTI floor — SGOL invalidation (Scenario A, D) | $55 nominal OR 30% below 90d trailing WTI settlement average | Existing framework, ⚑ calibration-dated | Pending June 30 |
| Brent trigger — Scenario C | $110 nominal OR 40% above 90d trailing Brent settlement average | Existing framework, ⚑ calibration-dated | Pending June 30 |
| Brent invalidation — Scenario C | $80 nominal OR 20% below 90d trailing Brent settlement average | Existing framework, ⚑ calibration-dated | Pending June 30 |

Session observation (April 19, 2026 session): Brent Friday close $90.38, Sunday futures ~$95.25–$95.71. WTI Friday close $83.85, Sunday futures $89.94. All well within Scenario C un-triggered zone; none approach the nominal $110 Brent trigger or the $80 invalidation threshold. SGOL WTI floor ($55) comfortably clear.

Session observation (April 21, 2026 session): Brent ~$94–96 (high volatility — Friday -11.5% on Iran Strait opening announcement, Monday +5–6% on US ship seizure and Strait re-blocking). WTI ~$87–88. All still below $110 C trigger. No floor or invalidation thresholds approached.

Session observation (April 22, 2026 session): Brent ~$99.81 (approaching $100; +1.4% today). WTI ~$89.33. C trigger ($110 nominal) NOT fired. No floor or invalidation thresholds approached. SGOL WTI floor ($55) comfortably clear. Trailing 90d average unavailable this session — nominal thresholds apply.

Session observation (April 23, 2026 session): Brent ~$103.50 (+3% today; IRGC gunboat attacks on commercial vessels confirmed). WTI ~$94.00. C trigger ($110 nominal) NOT fired — gap $6.50/bbl. $110 clock not started. SGOL WTI floor ($55) comfortably clear. Trailing 90d average unavailable — nominal thresholds apply. NOTE: Brent within 6.2% of $110 — elevated monitoring warranted.

### 2.2 Currency

| Threshold | Current Value | Source | Audit Status |
| :-: | :-: | :-: | :-: |
| DXY sustained above — SGOL invalidation | 105 nominal | Existing framework, not currently flagged as calibration-dated | Pending June 30 — classify formally |

Session observation (April 19, 2026): DXY 98.23 Friday close, Sunday futures modestly higher. Well below 105 invalidation threshold.

Session observation (April 21, 2026): DXY ~97.9 — flat to marginally lower. Well below 105 threshold.

Session observation (April 22, 2026): DXY ~98.30 — flat. Well below 105 invalidation threshold. SGOL invalidation condition 2 NOT approached.

Session observation (April 23, 2026): DXY ~98.73. Well below 105 SGOL invalidation threshold. Stable.

### 2.3 Macro

| Threshold | Current Value | Source | Audit Status |
| :-: | :-: | :-: | :-: |
| CPI trigger — Scenario B | 4% YoY, 3+ consecutive monthly prints | Existing framework, not currently flagged | Pending June 30 — classify formally |
| CPI invalidation — Scenario B | below 3% YoY, 2+ consecutive monthly prints | Existing framework, not currently flagged | Pending June 30 — classify formally |
| GDP trigger — Scenario F | above 3% annualized, 2+ consecutive quarters | Existing framework, not currently flagged | Pending June 30 — classify formally |
| GDP invalidation — Scenario F | below 2% on BEA advance estimate | Existing framework, not currently flagged | Pending June 30 — classify formally |
| Unemployment trigger — Scenario D | \+0.5% over any 3-month window | Existing framework, not currently flagged | Pending June 30 — classify formally |

Session observation (April 19, 2026): CPI March 3.3% YoY (below 4% trigger, above 3% invalidation — in neither regime). PPI March 4.0% YoY — strongest since Feb 2023 (BLS Tier 1, supports B probability but not itself a CPI trigger).

Session observation (April 21, 2026): No new macro data. CPI March 3.3% remains most recent print (1 of 3 required for B trigger). Q4 2025 GDP revised to 0.5% annualized (down sharply from 4.4% Q3 2025). Q1 2026 GDP advance estimate due end of April.

Session observation (April 22, 2026): No new macro data. CPI March 3.3% YoY remains most recent print (1 of 3 for B trigger; 1 of 2 for C trigger reacceleration check). Q4 2025 GDP 0.5% annualized confirmed. Q1 2026 advance estimate due ~April 30. Next CPI print ~May 10-12.

Session observation (April 23, 2026): No new macro data. CPI March 3.3% most recent (1 of 3 for B trigger; 1 of 2 for C reacceleration). Q4 2025 GDP 0.5% confirmed. Q1 2026 advance estimate due ~April 30 — critical for B/D scoring. FOMC April 28-29 expected hold. 10Y breakeven ~2.38% (4.30% nominal minus 1.92% TIPS real yield) — above Fed target, consistent with B/C dominance.

### 2.4 Instrument Evaluation

| Threshold | Current Value | Source | Audit Status |
| :-: | :-: | :-: | :-: |
| Foreign concentration disqualification | 40% single-country/single-region | Existing framework, not currently flagged | Pending June 30 — classify formally |
| AUM disqualification | $100M minimum | Existing framework, not currently flagged | Pending June 30 — classify formally |

_______________

## Section 3 — Calibration Log

2026-04-19 — Initial instantiation (v1)
* Framework Extension v1 adopted. Credit signal thresholds added with provisional initial delta values: HY\_STRESS\_DELTA = +150 bps; HY\_RECESSION\_DELTA = +300 bps; IG\_TRANSMISSION\_DELTA = +60 bps; CCC absolute divergence floor = +200 bps. HY baseline snapshot ~285 bps. Full audit scheduled June 30, 2026.

2026-04-19 — First session after instantiation (same-day, post-markets)
* No threshold changes. First CCC divergence computation: 2026-04-16 (921 bps) vs 2026-03-16 (973 bps) = −52 bps tightening. Neither divergence threshold fired. Session observations logged for HY/IG/CCC.

2026-04-21 — Framework update (v1.2)
* §6 Session State Log added. M03 DeriveScenarioProbabilities() function added. M04/M05/M12 updated accordingly.

2026-04-21 — First full portfolio audit session
* Scenario probabilities: A=7%, B=44%, C=36%, D=3%, E=7%, F=3% (initial derivation; no prior anchor). Primary driver: Strait of Hormuz Crisis / US-Iran War (Day 52). PAVE legislative mandate verification flagged. §7 and §8 initialized.

2026-04-22 — Scheduled bi-weekly portfolio review session
* Scenario probabilities: A=8%, B=45%, C=38%, D=3%, E=3%, F=3%. PAVE/IIJA T1-verified (GAO, DOT/FHWA, T4America): >$2.3B rescissions confirmed; IIJA expires Sept 30, 2026; no reauthorization bill. PAVE FLAGGED. Pre-M13 target allocations produced (IRA/Roth SGOL 47%, Relative IRA SGOL 48%, Relative Roth SGOL 50%).

2026-04-23 — Framework update (v1.3): M13 adoption, §4 addition, GitHub migration
* M13_GrowthObjectives.md adopted (v1.0). §4 (return table + multipliers) added. §§4–6 renumbered §§5–8. GitHub migration: Calibration_State.md now in GitHub (evgeny1/ai-fin-advisor-framework, master). M03/M05/M12/00_INDEX updated. Account objective profiles added to Allocation sheet Objectives tab.

2026-04-23 — M13 first application; §4.2/§4.3 multiplier revisions (v1.4)
* §4.2 IRA B/C target multipliers revised: 1.5× → 1.3×. IRA floor revised: 1.5× → 1.3×.
  Rationale (M13.RecalibrationSequence Path 3): inflation_hedge_commodity_linked identified as
  the role needed to close the IRA feasibility gap. M07 evaluation confirmed PDBC (IRA, 10yr)
  and BCI (Roth, 15yr) as preferred instruments. Price-adjustment analysis showed near-zero
  forward EV from current war-elevated entry (Brent +55% YoY; ~$35-38/bbl war premium;
  A-scenario collapse estimated −15–20% for commodity-linked). Entry deferred pending post-war
  price reset. Current holdings achieve ~3.05% conservative real return; revised 1.3× B/C
  requires 3.23% — gap 0.18pp accepted within return table estimation precision. Floor also
  revised to 1.3× to prevent floor override. Restore both to 1.5× when commodity-linked added.
* §4.3 Roth IRA B/C target multipliers revised: 2.0× → 1.3×. Roth floor revised: 2.0× → 1.3×.
  Same rationale. Primary Roth achieves ~2.97% vs 2.77% required at 1.3× — FEASIBLE.
  Relative Roth achieves ~2.2% vs 2.77% — residual gap 0.57pp accepted this regime.
  Restore both to 2.0× when commodity-linked added at appropriate entry prices post-conflict.
* Methodological error identified and corrected: §4.1 return table assumes neutral entry prices.
  Must price-adjust before ADD recommendation when instruments are at war-elevated levels.
  WAR PREMIUM ENTRY GUARD added to advisor session memory. Rule: for any instrument up >20%
  from a discrete geopolitical event, apply M06 entry EV math adjusted for embedded premium.
* Final M13 scenario-weighted target allocations:
   * Primary IRA (3080-6469): VTI 10%, XAR 22%, MLPX 26%, SGOL 42%
   * Primary Roth (3534-9838): VTI 10%, XAR 22%, MLPX 27%, SGOL 41%
   * Taxable Acc3 (3459-4443): SGOV 100%
   * Taxable Acc4 (6668-9768): PAVE 3%, XAR 32%, MLPX 39%, SGOV 26%
   * Relative IRA (...469): VTI 6%, MLPX 35%, SGOL 39%, SGOV 20%
   * Relative Roth (...466): VTI 22%, MLPX 38%, SGOL 40%
* Key changes vs April 22 pre-M13 targets:
   - XAR IRA/Roth held at 22% (not bumped to 28-32%); C-scenario Add not justified given
     war-elevated entry and current underperformance; B equity multiple compression dominant
   - SGOL IRA: 47% → 42%; Roth: 47% → 41% (C = Hold not Add; XAR moderation freed weight)
   - MLPX IRA: 21% → 26% (Hold at current; prior target was set too low)
   - PAVE Acc4: 11% → 3% (full floor enforcement per FLAGGED status)
   - Relative IRA SGOL: 48% → 39% (40% cap enforcement; prior target violated cap)
   - Relative Roth SGOL: 50% → 40% (40% cap enforcement; prior target violated cap)
   - Relative IRA/Roth MLPX: significantly higher (absorbs SGOL freed weight from cap)
* PAVE execution note: PAVE is top portfolio performer — embedded GAIN likely in Taxable Acc4.
  Verify cost basis and holding period before executing 454-share reduction. If short-term gain,
  assess deferral to long-term qualifying date before executing.
* Relative Roth note: "VTI | $9,259.01 | Apr 15" = portfolio total value on April 15 (reference
  only). No wash sale concern. VTI sale of 2 shares can proceed without restriction.
* XAR context: entered ~1 month into war at elevated prices; currently underperforming.
  Equity multiple compression in B regime (45%) overwhelming procurement thesis. Hold at 22%.
* Gold context: down ~10% from war peak; war premium minimal vs oil (+55% YoY).
  Structural monetary/fiscal thesis is primary driver. SGOL addition valid.
* Preferred commodity-linked instruments: PDBC (IRA) and BCI (Roth) — entry deferred pending
  post-war price reset. Re-evaluate when Brent retreats toward $65–75 post-conflict.
* Scenario probabilities unchanged from April 22: A=8%, B=45%, C=38%, D=3%, E=3%, F=3%.

2026-04-27 — Framework update (v1.5): M14 adoption; §9 Market Regime Thresholds added
* M14_MarketRegime.md adopted (v1.0). Addresses three structural gaps: (1) no market
  desensitization detection — market can absorb an ongoing scenario without it resolving;
  (2) no underweight opportunity-cost review gate when scenario-underweighted positions
  appreciate materially; (3) entry-price extension check previously limited to commodity-linked
  instruments under discrete supply events (WAR PREMIUM ENTRY GUARD) — now generalized to
  all roles via EntryExtensionGuard.
* WAR PREMIUM ENTRY GUARD superseded by M14.EntryExtensionGuard. Both guards apply
  independently when a discrete supply event is also active — position must clear both EV
  checks before ADD executes.
* §9 Market Regime Thresholds added (provisional initial values — full audit June 30, 2026).
* 00_INDEX, M02, M04, M08 updated to reference M14. CALIBRATION_DATED_THRESHOLDS in
  00_INDEX updated to reflect actual current IRA/Roth multipliers (1.3×) from prior session.
* Architectural boundary confirmed: M14 signals route to entry-timing EV calculations only.
  NEVER feed into M03.DeriveScenarioProbabilities — ScoringIntegrity guard applies absolutely.

_______________

## Section 4 — Growth Objectives: Return Table and Multipliers
⚑ All values in this section are CALIBRATION_DATED.
Review at every quarter-end audit alongside §1 and §2 thresholds.
Interim review triggered if: return table produces systematic infeasibility across accounts despite valid allocation changes.
@see M13_GrowthObjectives

Last calibrated: April 23, 2026 (v1.3 initial instantiation; v1.4 §4.2/§4.3 B/C multipliers and floors revised — see §3 log)
Full empirical audit scheduled: June 30, 2026

Revision triggers for §4 specifically:
- New macro regime episode completes with sufficient data → update relevant scenario column
- Academic consensus on historical returns revises materially (e.g., JST database update)
- A role's structural characteristics change materially (e.g., MLPX contract structure shifts from fee-based)
- Systematic infeasibility across accounts despite valid allocations → interim review before next recommendation

### 4.1 Expected Real Annualized Return Table
Conservative end used for ALL computations. Upside end disclosed in briefing only — never used in computation.
Format per cell: [conservative%, upside%]

| Role | Scenario A | Scenario B | Scenario C | Scenario D | Scenario E | Scenario F |
| :-- | :-: | :-: | :-: | :-: | :-: | :-: |
| geopolitical_premium | [-2, 3] | [2, 6] | [4, 10] | [-4, 0] | [1, 5] | [1, 4] |
| inflation_hedge_precious_metals | [0, 4] | [6, 12] | [7, 14] | [-2, 4] | [10, 20] | [-3, 1] |
| inflation_hedge_commodity_linked | [2, 6] | [6, 12] | [7, 13] | [-8, -2] | [2, 6] | [2, 5] |
| real_asset_contracted_revenue | [3, 7] | [3, 7] | [3, 6] | [2, 6] | [2, 5] | [3, 7] |
| policy_driven_thematic_equity | [4, 8] | [-3, 1] | [-1, 3] | [-5, -1] | [-6, -2] | [4, 8] |
| rate_sensitive_income_short_duration | [0, 2] | [1, 3] | [1, 3] | [0, 3] | [-2, 2] | [1, 3] |
| rate_sensitive_income_long_duration | [3, 7] | [-4, -1] | [-5, -2] | [5, 10] | [-10, -3] | [-4, -1] |
| broad_market_equity_domestic | [5, 12] | [-8, -2] | [-4, -1] | [-12, -4] | [-8, -3] | [7, 14] |
| broad_market_equity_international | [4, 9] | [-5, -1] | [-6, -2] | [-8, -3] | [-10, -4] | [3, 8] |

Empirical basis (key anchors — see Calibration Log 2026-04-23 for full sourcing):
- inflation_hedge_precious_metals B: ~9.2% real 1973–82 (conservative); ~19% annualized stagflation 1973–2024 (upside)
- inflation_hedge_precious_metals E: Nixon shock analog; reserve erosion = maximum thesis conviction
- inflation_hedge_precious_metals F: −1.1% real 1980–2000 with positive real rates (World Gold Council)
- broad_market_equity_domestic B: −7.1% nominal / −16.6% real in stagflation (Robeco 146-year study)
- broad_market_equity_domestic D: −36.5% nominal in 2008 peak year; multi-year regime −12% conservative
- broad_market_equity_domestic A/F: ~15–18% real in 1990s soft landing / overheat
- inflation_hedge_commodity_linked B/C: near one-for-one with unexpected inflation (GSCI/NBER)
- inflation_hedge_commodity_linked D: "particularly poorly during severe recessions" (NBER)
- real_asset_contracted_revenue D: 77% cumulative outperformance vs S&P 500, 2008–2011 (Alerian)
- rate_sensitive_income_long_duration D: primary beneficiary confirmed; flight to quality 2008
- policy_driven_thematic_equity: insufficient historical analog data — structurally derived from M09/M10 narratives
- Scenario E: limited data — structurally reasoned; no clean modern analog for full reserve rupture

### 4.2 IRA Target Multipliers (planning horizon: 10 years)
Floor: 1.3× ⚑ REVISED April 23, 2026 (was 1.5×) — restore to 1.5× when commodity-linked added post-war price reset.

| Scenario | Multiplier | Implied Real Return | Basis |
| :-: | :-: | :-: | :-- |
| A — Soft Landing | 2.0 | ~7.2% annualized | Historical soft landing 1990s: ~15–18% real equity returns; balanced portfolio approximately 7–8% real |
| B — Stagflation Lock | 1.3 ⚑ | ~2.7% annualized | REVISED April 23, 2026 from 1.5×. Commodity-linked unavailable at war-elevated prices; restore to 1.5× when added post-conflict. |
| C — Inflationary Shock | 1.3 ⚑ | ~2.7% annualized | REVISED April 23, 2026 from 1.5×. Same rationale as B. |
| D — Deflationary Recession | 1.3 | ~2.7% annualized | Preservation primary; modest growth from long bonds only; demand collapse |
| E — Structural Rupture | 1.2 | ~1.8% annualized | Capital preservation dominates; maximum stress scenario; real asset focus |
| F — Growth Overheat | 2.0 | ~7.2% annualized | Strong nominal growth; cyclicals and financials outperform; similar to A on 10yr horizon |

Current regime probability-weighted target (A=8%, B=45%, C=38%, D=3%, E=3%, F=3%):
= 0.08×2.0 + 0.45×1.3 + 0.38×1.3 + 0.03×1.3 + 0.03×1.2 + 0.03×2.0
= 0.16 + 0.585 + 0.494 + 0.039 + 0.036 + 0.060 = 1.374×
Required real return: (1.374)^(1/10) − 1 ≈ 3.2% annualized
Portfolio achieves ~3.05% — gap 0.18pp accepted within return table estimation precision.

### 4.3 Roth IRA Target Multipliers (planning horizon: 15 years)
Floor: 1.3× ⚑ REVISED April 23, 2026 (was 2.0×) — restore to 2.0× when commodity-linked added post-war price reset.
Derivation: IRA multipliers extended to 15-year horizon at same implied annualized real return,
plus ~0.5–0.75% effective annual advantage from tax-free compounding on a typical equity-heavy portfolio.

| Scenario | IRA Rate | Roth Rate (adj) | Roth 15yr Multiplier | Notes |
| :-: | :-: | :-: | :-: | :-- |
| A | ~7.2% | ~7.9% | 3.1 | Full tax-free compounding; extended 15yr runway |
| B | ~2.7% | ~3.0% | 1.3 ⚑ | REVISED April 23, 2026 from 2.0×. Same rationale as §4.2 B. Restore when commodity-linked added. |
| C | ~2.7% | ~3.0% | 1.3 ⚑ | REVISED April 23, 2026 from 2.0×. Same rationale. |
| D | ~2.7% | ~3.0% | 1.6 | Preservation + modest bond appreciation; tax-free muted benefit |
| E | ~1.8% | ~2.1% | 1.4 | Capital preservation; rupture scenario; limited compounding environment |
| F | ~7.2% | ~7.9% | 3.1 | Same as A; full overheat compounding advantage |

Current regime weighted multiplier (A=8%, B=45%, C=38%, D=3%, E=3%, F=3%):
= 0.08×3.1 + 0.45×1.3 + 0.38×1.3 + 0.03×1.6 + 0.03×1.4 + 0.03×3.1
= 0.248 + 0.585 + 0.494 + 0.048 + 0.042 + 0.093 = 1.510×
Required real return: (1.510)^(1/15) − 1 ≈ 2.8% annualized
Primary Roth achieves ~2.97% — FEASIBLE. Relative Roth achieves ~2.2% — 0.57pp gap accepted this regime.

Status: B/C multipliers and floors revised April 23, 2026 per M13 RecalibrationSequence Path 3. Full review June 30, 2026.

### 4.4 Structural Floor and Concentration Parameters

| Parameter | Current Value | Type | Notes |
| :-: | :-: | :-: | :-- |
| Base floor (fraction of current allocation) | 0.25 | Calibration-dated | 75% reduction = maximum adverse directive applied |
| Minimum floor (% of account total value) | 2% | Calibration-dated | Prevents floor from becoming a rounding artifact |
| Concentration cap (max single position) | 40% | Calibration-dated | Consistent with M06 5–6 position monitoring constraint |
| Floor nominal loss probability threshold | 15% | Calibration-dated | Scenarios at or above this probability checked for floor breach in FLOOR_THEN_RETURN accounts |

All values provisional — full audit pending June 30, 2026.

_______________

## Section 5 — Review Cadence
(Formerly §4 — renumbered April 23, 2026)

| Date | Type | Scope |
| :-: | :-: | :-: |
| 2026-06-30 | Scheduled Q2 (first full audit) | Compute 180d medians for HY/IG/CCC; verify triggers in 75th–90th percentile band; hit-rate audit all §2 thresholds; classify unflagged thresholds; audit §4 return table and multipliers; restore §4.2/§4.3 B/C and floors if commodity-linked has been added; audit §9 M14 thresholds (first review) |
| 2026-09-30 | Scheduled Q3 | Full audit of all calibration-dated thresholds including §4 and §9 |
| 2026-12-31 | Scheduled Q4 | Full audit |
| 2027-03-31 | Scheduled Q1 2027 | Full audit |

Interim recalibration triggered per §1.10 if: trailing baseline shifts >20% from last calibration; threshold fires twice without prescribed regime; threshold fails to fire while regime materializes; primary driver recalibration declared; §4.1 produces systematic infeasibility despite valid allocations; §9 thresholds produce systematic false positives or false negatives.

_______________

## Section 6 — First-Audit Checklist (for June 30, 2026 session)
(Formerly §5 — renumbered April 23, 2026)
At Q2 2026 review, execute the following:

1. Compute trailing 180-day median for FRED series BAMLH0A0HYM2, BAMLC0A0CM, BAMLH0A3HYC. Record in Section 1.
2. Compute 10th/25th/75th/90th percentiles of trailing distribution for each series.
3. Verify HY\_STRESS\_DELTA (+150) places trigger in 75th–90th percentile band of HY distribution. If outside band, adjust and log rationale.
4. Verify HY\_RECESSION\_DELTA (+300) places trigger in 75th–90th percentile band. Adjust if needed.
5. Verify IG\_TRANSMISSION\_DELTA (+60) places trigger in 75th–90th percentile band of IG distribution. Adjust if needed.
6. Hit-rate audit each absolute threshold in Section 2 against trailing 5-year data. Adjust if lagging or false-positive-prone.
7. Formally classify currently-unflagged thresholds in Sections 2.2, 2.3, 2.4 as calibration-dated. Update main framework document to add ⚑ markers.
8. First empirical audit of §4.1 return table: verify conservative bounds against any new regime episode data; check structural coherence across roles and scenarios.
9. First empirical audit of §4.2 and §4.3 multipliers: assess whether commodity-linked has been added at appropriate entry prices; if so, restore B/C multipliers and floors (IRA: 1.5×; Roth: 2.0×) or calibrate to new empirical basis. If not added, document continued deferral rationale.
10. Audit §4.4 floor and concentration parameters against actual account sizes and position counts.
11. First audit of §9 M14 thresholds: review entry_extension thresholds against actual position history this session; assess whether divergence thresholds produced actionable signals or noise; adjust if systematic false positives or missed signals documented.
12. Record all results in Section 3 Calibration Log with date-stamped entry.
13. Confirm next review date (September 30, 2026).

_______________

## Section 7 — Session Observations Log (Credit Readings)
(Formerly §5b — renumbered April 23, 2026)
Appended at every session end by M12_FileProtocol.WriteBack.
Enables velocity checks once 60+ trading days of entries accumulate.
Note: Until 60+ entries exist, velocity overlays (HY: 100bps/60d; IG: 40bps/60d) cannot be computed from this log — log the gap rather than skipping the entry.

| Date | HY OAS (bps) | IG OAS (bps) | CCC OAS (bps) | Source | T1 Flag |
| :-: | :-: | :-: | :-: | :-: | :-: |
| 2026-04-19 | 285 | 83 | 921 | Trading Economics / FRED | composite_only |
| 2026-04-21 | 285 | 83 | 921 | Trading Economics / FRED (stale — last updated Apr 15-16) | stale |
| 2026-04-22 | 287 | 83 | 921 | Trading Economics / FRED (HY last updated Apr 20; IG/CCC Apr 16-17) | stale |
| 2026-04-23 | 287 | 83 | 921 | Trading Economics / FRED (HY Apr 20; IG/CCC Apr 16-17 — stale 3–7 days) | stale |

_______________

## Section 8 — Session State Log
(Formerly §6 — renumbered April 23, 2026)
Appended at every session end by M12_FileProtocol.WriteBack.
Consumed at every session start by M05_SessionInit.INPUT_3 (§8 load).
Provides prior scenario probability anchor for 25pp cap enforcement in
M03_ScenarioFramework.DeriveScenarioProbabilities().

Format per entry:
  date: [YYYY-MM-DD]
  scenario_probabilities: { A: %, B: %, C: %, D: %, E: %, F: % }  // must sum to 100%
  primary_driver: [name]
  derivation_method: scored | manual_override
  manual_override_reason: [T1 evidence and rationale] | null
  open_triggers: [list]
  open_decisions: [list]
  next_session_flags: [list]

---

date: 2026-04-21
scenario_probabilities: { A: 7%, B: 44%, C: 36%, D: 3%, E: 7%, F: 3% }
primary_driver: Strait of Hormuz Crisis / US-Iran War (Day 52)
derivation_method: scored
manual_override_reason: null
open_triggers:
  - Ceasefire expiry April 22 — watching for Brent spike toward $110 C trigger
  - Warsh Senate confirmation hearing April 21 — outcome affects E probability
  - Q1 2026 GDP advance estimate due ~April 30
  - Next CPI print ~May 10-12
  - Brent $80 invalidation watch
open_decisions:
  - PAVE legislative mandate verification required before B trigger reduction execution
  - XAR Acc4 — defer to next scheduled rebalancing
next_session_flags:
  - MOVE index not fetched — retrieve at next session start
  - Ceasefire expiry outcome (April 22) — reassess C probability
  - Warsh confirmation hearing outcome — assess E probability direction
  - Verify PAVE/IIJA spending mandate status via T1 source
  - Gold 90-day check: +1.3% — NOT triggered
  - Credit spread staleness — fetch fresh at next session start

---

date: 2026-04-22
scenario_probabilities: { A: 8%, B: 45%, C: 38%, D: 3%, E: 3%, F: 3% }
primary_driver: Strait of Hormuz Crisis / US-Iran War (Day 53) — ceasefire extended; Strait remains blocked; Iran declined talks; VP Vance Islamabad trip canceled
derivation_method: scored
manual_override_reason: null
open_triggers:
  - Brent $110 C-trigger — clock not started; currently ~$100
  - Q1 2026 GDP advance estimate ~April 30
  - Next CPI print ~May 10-12
  - FOMC April 28-29 — expected hold
  - Warsh confirmation BLOCKED by Sen. Tillis; DOJ/Powell investigation prerequisite
  - PAVE/IIJA FLAGGED — T1-verified; rescissions >$2.3B; IIJA expires Sept 30, 2026
open_decisions:
  - ALL SUPERSEDED by April 23 M13 targets — see April 23 §8 entry
next_session_flags:
  - SUPERSEDED — see April 23 entry

---

date: 2026-04-23
scenario_probabilities: { A: 8%, B: 45%, C: 38%, D: 3%, E: 3%, F: 3% }
primary_driver: Strait of Hormuz Crisis / US-Iran War (Day 55+) — ceasefire holds; Strait blocked; IRGC fired on 3 commercial vessels; US intercepted Iranian tankers; Iran refuses talks
derivation_method: scored
manual_override_reason: null
open_triggers:
  - Brent $110 C-trigger — clock NOT started; currently ~$103.50; gap $6.50/bbl; elevated monitoring
  - FOMC April 28-29 — expected hold; reassess A/B scores on release
  - Q1 2026 GDP advance estimate ~April 30 — if negative: B check_gdp → 3; D watch begins
  - Next CPI print ~May 10-12 — 2nd print needed for C trigger reacceleration; 3rd above 4% for B
  - Warsh confirmation stalled (Tillis hold); DOJ/Powell timeline indeterminate
  - PAVE/IIJA FLAGGED — reduction authorized and pending execution
open_decisions:
  - Primary IRA: sell VTI -49 shares, XAR -30 shares; buy MLPX +8 shares, SGOL +541 shares. Targets: VTI 10%, XAR 22%, MLPX 26%, SGOL 42%
  - Primary Roth: sell VTI -8 shares, XAR -4 shares; buy MLPX +3 shares, SGOL +88 shares. Targets: VTI 10%, XAR 22%, MLPX 27%, SGOL 41%
  - Taxable Acc4: sell PAVE -454 shares; buy XAR +20, MLPX +76, SGOV +149 shares. Targets: PAVE 3%, XAR 32%, MLPX 39%, SGOV 26%. ⚠ VERIFY PAVE COST BASIS AND HOLDING PERIOD BEFORE EXECUTING — embedded gain; assess short vs long-term capital gains tax timing
  - Relative IRA: sell VTI -20, SGOL -152, SGOV -21 shares; buy MLPX +222 shares. Targets: VTI 6%, MLPX 35%, SGOL 39%, SGOV 20%. NOTE: major reversal from Apr 22 — SGOL sells (cap enforcement); MLPX buys
  - Relative Roth: sell VTI -2, SGOL -19 shares; buy MLPX +23 shares. Targets: VTI 22%, MLPX 38%, SGOL 40%. NOTE: major reversal from Apr 22. "$9,259.01 Apr 15" = portfolio total value on April 15 — reference only; no wash sale concern
  - Taxable Acc3: SGOV 100% — no action
next_session_flags:
  - MOVE index still not fetched — priority at next session start
  - Q1 2026 GDP advance estimate ~April 30 — reassess B/D scoring immediately on release
  - FOMC April 29 decision — reassess A/B/D scores immediately on release
  - Brent $103.50 — gap to $110 C-trigger is $6.50; begin close monitoring if Brent approaches $107
  - FRED credit staleness: HY Apr 20, IG/CCC Apr 16-17 — fetch fresh at next session start
  - §4.2 IRA B/C revised to 1.3× and floor to 1.3×; §4.3 Roth same — restore both when commodity-linked added post-war at appropriate entry prices
  - Relative Roth: 0.57pp feasibility gap accepted this regime; reassess when Brent resets post-war
  - Preferred commodity-linked: PDBC (IRA), BCI (Roth) — entry deferred; re-evaluate when Brent toward $65–75
  - PAVE cost basis and holding period verification required before Taxable Acc4 execution
  - XAR: entered ~1 month into war; currently underperforming; hold at 22%; do not add
  - Gold 90-day check: Jan 20 ($4,737) to Apr 23 (~$4,738) = +0.02% — NOT triggered

---

_______________

## Section 9 — Market Regime Thresholds (M14)
⚑ All values in this section are CALIBRATION_DATED.
Review quarterly alongside §1 and §2 thresholds.
First audit scheduled: June 30, 2026 (provisional initial values — no prior data to calibrate against at adoption).
@see M14_MarketRegime

Last calibrated: April 27, 2026 (v1.5 initial instantiation — provisional values)

### 9.1 Divergence Signal Thresholds

| Parameter | Current Value | Type | Notes |
| :-: | :-: | :-: | :-: |
| commodity\_fear\_divergence HIGH | energy\_90d >= +15% AND VIX\_change\_90d\_pts <= 0 | Calibration-dated | Provisional — first audit June 30, 2026 |
| commodity\_fear\_divergence MODERATE | energy\_90d >= +10% AND VIX\_change\_90d\_pts <= +5 pts | Calibration-dated | Provisional |
| equity\_scenario\_divergence HIGH | broad\_equity\_30d >= +5% while directive reductive | Calibration-dated | Provisional |
| equity\_scenario\_divergence MODERATE | broad\_equity\_30d >= +2% while directive reductive | Calibration-dated | Provisional |

### 9.2 Underweight Review Trigger

| Parameter | Current Value | Type | Notes |
| :-: | :-: | :-: | :-: |
| underweight\_gap\_trigger | 5 pp | Calibration-dated | Provisional |
| appreciation\_trigger\_30d | 5% | Calibration-dated | Provisional |

### 9.3 Entry Extension Guard Thresholds (appreciation above 90d trailing avg)

| Role | Threshold | Type | Notes |
| :-: | :-: | :-: | :-: |
| broad\_market\_equity | 15% | Calibration-dated | Provisional |
| thematic\_sector\_equity | 20% | Calibration-dated | policy\_driven\_thematic\_equity, geopolitical\_premium |
| commodity\_linked | 20% | Calibration-dated | WAR PREMIUM ENTRY GUARD also applies independently when discrete event active |
| inflation\_hedge\_precious\_metals | 20% | Calibration-dated | Provisional |
| real\_asset\_contracted\_revenue | 15% | Calibration-dated | Provisional |
| rate\_sensitive\_income\_short | N/A | — | Guard does not apply — price-stable instrument |
| rate\_sensitive\_income\_long | N/A | — | Duration risk captured by scenario framework |

Review schedule: quarterly alongside §1 and §2. Assess whether thresholds produce actionable signals vs noise based on session history since adoption.
