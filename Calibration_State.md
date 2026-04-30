# Calibration State
Persistent framework configuration — load at every session start alongside session handoff.

Version: 1.7  Last updated: April 28, 2026 (M15 InstrumentClassification adopted; §11 added — extensible role registry + instrument classification table; secular_technology_growth role added; current holdings classified; GitHub write workflow codified in M12)  Next scheduled review: June 30, 2026 (Q2 2026 quarter-end)

_______________

## Load Verification Requirement
At session start, the advisor must state in the briefing:

"Calibration State loaded, last update: April 28, 2026"

Absence of this line indicates the calibration file was not loaded and the session is invalid for threshold-sensitive decisions.

After loading: run M15.ValidateClassifications() — all instruments in the allocation file must have §11 entries before session proceeds to analysis.

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

Session observation (April 28, 2026 session): HY composite ~285-287 bps (FRED last updated April 21 — stale 7 days; Trading Economics proxy). Unchanged. No threshold fires. HY_StressBeginning threshold ~435 bps (285+150); gap ~148 bps. T1_flag: stale.

Session observation (April 29, 2026 session): HY composite ~284 bps (Trading Economics; FRED last updated April 28). Marginal tightening from prior sessions. No threshold fires. HY_StressBeginning threshold ~434-435 bps; gap ~151 bps. T1_flag: stale (FRED last April 28 — 1 day lag, lowest staleness since series began). No velocity check executable — insufficient §7 history depth.

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

Session observation (April 28, 2026 session): IG composite ~83 bps (carry from April 23; FRED stale ~12 days). IG_TransmissionReached NOT fired (threshold ~143 bps; gap ~60 bps). T1_flag: stale.

Session observation (April 29, 2026 session): IG composite ~80 bps (cross-referenced: T2 source article confirms IG OAS ~80 bps as of early April 2026 near 25-year tights; FRED data last April 28). IG_TransmissionReached NOT fired (threshold ~143 bps; gap ~63 bps). T1_flag: composite_only (primary FRED series not independently confirmed at this tick).

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

Session observation (April 28, 2026 session): CCC OAS ~921 bps (carry forward; FRED stale ~12 days). CCC_TailFirstWidening NOT fired. T1_flag: stale. Priority: fetch fresh FRED data at next session.

Session observation (April 29, 2026 session): CCC OAS ~921 bps (carry forward; FRED last updated April 24 per search result metadata). CCC_TailFirstWidening NOT fired. No divergence relative to HY (both stable/tightening). T1_flag: stale. No change.

_______________

## Section 2 — Other Calibration-Dated Thresholds (Pending Initial Audit)
The following thresholds exist in the main framework and are calibration-dated. Initial formal audit has not been completed for these — they carry forward at their current framework values. Full hit-rate / miss-rate audit scheduled for June 30, 2026 quarter-end review.

### 2.1 Energy / Commodities

| Threshold | Current Value | Source | Audit Status |
| :-: | :-: | :-: | :-: |
| WTI floor — SGOL invalidation (Scenario A, D) | $55 nominal OR 30% below 90d trailing WTI settlement average | Existing framework, calibration-dated | Pending June 30 |
| Brent trigger — Scenario C | $110 nominal OR 40% above 90d trailing Brent settlement average | Existing framework, calibration-dated | Pending June 30 |
| Brent invalidation — Scenario C | $80 nominal OR 20% below 90d trailing Brent settlement average | Existing framework, calibration-dated | Pending June 30 |

Session observation (April 19, 2026 session): Brent Friday close $90.38, Sunday futures ~$95.25-$95.71. WTI Friday close $83.85, Sunday futures $89.94. All well within Scenario C un-triggered zone; none approach the nominal $110 Brent trigger or the $80 invalidation threshold. SGOL WTI floor ($55) comfortably clear.

Session observation (April 21, 2026 session): Brent ~$94-96 (high volatility — Friday -11.5% on Iran Strait opening announcement, Monday +5-6% on US ship seizure and Strait re-blocking). WTI ~$87-88. All still below $110 C trigger. No floor or invalidation thresholds approached.

Session observation (April 22, 2026 session): Brent ~$99.81 (approaching $100; +1.4% today). WTI ~$89.33. C trigger ($110 nominal) NOT fired. No floor or invalidation thresholds approached. SGOL WTI floor ($55) comfortably clear. Trailing 90d average unavailable this session — nominal thresholds apply.

Session observation (April 23, 2026 session): Brent ~$103.50 (+3% today; IRGC gunboat attacks on commercial vessels confirmed). WTI ~$94.00. C trigger ($110 nominal) NOT fired — gap $6.50/bbl. $110 clock not started. SGOL WTI floor ($55) comfortably clear. Trailing 90d average unavailable — nominal thresholds apply. NOTE: Brent within 6.2% of $110 — elevated monitoring warranted.

Session observation (April 28, 2026 session): Brent peaked at $108.11 on April 27; easing to ~$106 intraday April 28 on Iran diplomatic proposal news. WTI ~$95-96. C trigger ($110 nominal) NOT fired — gap ~$2-4/bbl. $110 clock NOT started. SGOL WTI floor ($55) comfortably clear. WARNING: gap narrowed to ~$2-4/bbl — close monitoring required every session. EIA STEO (T1, April 2026): expects Brent to peak ~$115/b in Q2 2026 before easing.

Session observation (April 29, 2026 session): Brent ~$106 (day range $98.43-$107.65 for WTI; Brent proximate). WTI ~$103-107 (handoff data, 3rd straight session gaining). C trigger ($110 nominal) NOT fired — gap ~$2-4/bbl. $110 clock NOT started. EIA STEO Q2 2026 peak ~$115 projection remains T1 reference. SGOL WTI floor ($55) comfortably clear. ⚠ CRITICAL: gap to $110 remains at minimum level recorded — monitor daily. Scenario C check_brent will upgrade to 3 if clock starts (10 trading days sustained ≥$110).

### 2.2 Currency

| Threshold | Current Value | Source | Audit Status |
| :-: | :-: | :-: | :-: |
| DXY sustained above — SGOL invalidation | 105 nominal | Existing framework, not currently flagged as calibration-dated | Pending June 30 — classify formally |

Session observation (April 19, 2026): DXY 98.23 Friday close, Sunday futures modestly higher. Well below 105 invalidation threshold.

Session observation (April 21, 2026): DXY ~97.9 — flat to marginally lower. Well below 105 threshold.

Session observation (April 22, 2026): DXY ~98.30 — flat. Well below 105 invalidation threshold. SGOL invalidation condition 2 NOT approached.

Session observation (April 23, 2026): DXY ~98.73. Well below 105 SGOL invalidation threshold. Stable.

Session observation (April 28, 2026): DXY ~98.5 (range 98.5-99.3 intraday; slight firming on Iran safe-haven demand and FOMC hold expectations). Well below 105 invalidation threshold.

Session observation (April 29, 2026): DXY ~98.5. Unchanged from April 28. Well below 105 threshold. No SGOL invalidation risk from currency channel.

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

Session observation (April 28, 2026): No new macro data. CPI March 3.3% still most recent print. Q1 2026 GDP advance estimate due ~April 30 — BINARY for B/D scoring. FOMC April 28-29 meeting active; decision tomorrow. 10Y breakeven ~2.43% (4.32% nominal minus 1.89% TIPS real yield April 24). Consumer sentiment record low 49.8 (U. Michigan April).

Session observation (April 29, 2026): No new macro data. CPI March 3.3% still most recent print. Q1 2026 GDP advance estimate due April 30 — BINARY for B/D. FOMC decision April 30 — 94% hold probability. 10Y breakeven ~2.43% unchanged. Sahm Rule 0.20 (well below 0.5% trigger). Initial claims ~214K (healthy labor market). Mag7 earnings all in: MSFT +18% YoY, Azure +40% (supply-constrained), GOOGL beat, META +33% (capex raised $125-145B), AMZN AWS +28% (fastest 15 quarters), EPS $2.78 vs $1.64 est. Zero guidance withdrawals. T1-confirmed (public quarterly filings). Earnings signal documented in calibration proposals — see §3.

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
* No threshold changes. First CCC divergence computation: 2026-04-16 (921 bps) vs 2026-03-16 (973 bps) = -52 bps tightening. Neither divergence threshold fired. Session observations logged for HY/IG/CCC.

2026-04-21 — Framework update (v1.2)
* §6 Session State Log added. M03 DeriveScenarioProbabilities() function added. M04/M05/M12 updated accordingly.

2026-04-21 — First full portfolio audit session
* Scenario probabilities: A=7%, B=44%, C=36%, D=3%, E=7%, F=3% (initial derivation; no prior anchor). Primary driver: Strait of Hormuz Crisis / US-Iran War (Day 52). PAVE legislative mandate verification flagged. §7 and §8 initialized.

2026-04-22 — Scheduled bi-weekly portfolio review session
* Scenario probabilities: A=8%, B=45%, C=38%, D=3%, E=3%, F=3%. PAVE/IIJA T1-verified (GAO, DOT/FHWA, T4America): >$2.3B rescissions confirmed; IIJA expires Sept 30, 2026; no reauthorization bill. PAVE FLAGGED. Pre-M13 target allocations produced.

2026-04-23 — Framework update (v1.3): M13 adoption, §4 addition, GitHub migration
* M13_GrowthObjectives.md adopted (v1.0). §4 (return table + multipliers) added. GitHub migration: Calibration_State.md now in GitHub. M03/M05/M12/00_INDEX updated.

2026-04-23 — M13 first application; §4.2/§4.3 multiplier revisions (v1.4)
* §4.2 IRA B/C target multipliers revised: 1.5x to 1.3x. IRA floor revised: 1.5x to 1.3x. Rationale: commodity_linked unavailable at war-elevated prices; restore to 1.5x when added post-conflict.
* §4.3 Roth IRA B/C target multipliers revised: 2.0x to 1.3x. Roth floor revised: 2.0x to 1.3x. Same rationale. Restore to 2.0x when commodity-linked added.
* Final M13 scenario-weighted target allocations:
  - Primary IRA (3080-6469): VTI 10%, XAR 22%, MLPX 26%, SGOL 42%
  - Primary Roth (3534-9838): VTI 10%, XAR 22%, MLPX 27%, SGOL 41%
  - Taxable Acc3 (3459-4443): SGOV 100%
  - Taxable Acc4 (6668-9768): PAVE 3%, XAR 32%, MLPX 39%, SGOV 26% [SUPERSEDED — see April 28 entry]
  - Relative IRA (...469): VTI 6%, MLPX 35%, SGOL 39%, SGOV 20%
  - Relative Roth (...466): VTI 22%, MLPX 38%, SGOL 40%
* Scenario probabilities unchanged from April 22: A=8%, B=45%, C=38%, D=3%, E=3%, F=3%.

2026-04-27 — Framework update (v1.5): M14 adoption; §9 Market Regime Thresholds added
* M14_MarketRegime.md adopted (v1.0). WAR PREMIUM ENTRY GUARD superseded by M14.EntryExtensionGuard. §9 added (provisional initial values). 00_INDEX, M02, M04, M08 updated to reference M14.

2026-04-28 — PAVE reclassification + M08 framework update (v1.6)
* PAVE status corrected: FLAGGED to watch.
  The April 22 FLAGGED classification was applied at ETF label level without constituent-level mandate exposure analysis — structural gap in M08. Holdings audit conducted April 28 covering top ~32% of PAVE NAV: Howmet Aerospace (~3.3%), Trane Technologies (~3.4%), Eaton Corporation (~3.4%), CSX Corporation (~3.3%), Parker-Hannifin (~3.5%) have negligible to low IIJA exposure. Core programs those holdings depend on — highways, bridges, rail formula programs — were NOT among the $2.3B rescinded. T1 source (Transportation for America, GAO, FHWA): rescissions primarily hit NEVI (EV charging, ~$879M) and climate/equity programs. Highway, bridge, water SRF, and BEAD broadband formula programs survived intact. Correct M08 status per MandateImpairmentPropagation(): watch, not FLAGGED. ETF NAV directly at risk from actual rescissions: estimated <15% (Quanta Services EV segment + minor). Below §10.2 materiality threshold of 20%.
* PAVE M13 target (Taxable Acc4): revised from 3% back to 11% (hold at current allocation). The 3% floor-enforcement target derived from FLAGGED status is removed. Revised posture: hold at ~11%; monitor September 30, 2026 IIJA expiration and reauthorization progress. Trigger to reassess: reauthorization fails AND formula highway programs materially cut in successor bill — then rerun MandateImpairmentPropagation() and reclassify.
* PAVE cost basis confirmed: $31,913.10 / 590 shares = $54.09/share. ~$1,286 embedded gain. 454-share reduction open decision REMOVED — not justified under watch status.
* Updated Taxable Acc4 targets: PAVE 11%, XAR 32%, MLPX 39%, SGOV 18%.
* M08 framework update: ThematicETF_ClassificationAudit() and MandateImpairmentPropagation() procedures added. Policy_driven_thematic_equity classifyRole() note updated to gate thematic ETFs through the audit before confirming classification. §10 added to Calibration State with provisional initial thresholds.
* Action item: apply ThematicETF_ClassificationAudit() to XAR at next session to confirm geopolitical_premium classification holds at constituent level.
* Scenario probabilities unchanged: A=8%, B=45%, C=38%, D=3%, E=3%, F=3%. FOMC April 29 and Q1 GDP April 30 both pending — all open decisions deferred.

2026-04-28 — Framework update (v1.7): M15 adoption; §11 addition; secular_technology_growth role
* M15_InstrumentClassification.md adopted (v1.0). Resolves: hardcoded role ENUM in M08; binary classifyRole() producing inaccurate scenario returns for composite instruments (e.g., VTI with material tech concentration having different B and C sensitivities than generic broad_market_equity_domestic).
* Architecture: roles now in §11.ROLE_REGISTRY (extensible without module file edits); instrument decompositions in §11.INSTRUMENT_CLASSIFICATION_TABLE; M15.blendedScenarioReturn() replaces all direct §4.1[role] lookups; M15.ValidateClassifications() hard-stops session if any allocation instrument is unclassified.
* New role added: secular_technology_growth. Binding driver: AI capex cycle, mega-cap tech multiple expansion. Scenario profile: more negative than broad_market_equity_domestic in B (multiple compression under rate constraint); less negative in C (conflict transmission to AI capex is weak — same observation that triggered this amendment). Return table row added §11.2. Provisional — empirical audit June 30, 2026.
* Initial instrument classification (current holdings): VTI (78% broad/22% secular_tech), XAR (90% geopolitical/10% broad — pending ThematicETF_ClassificationAudit confirmation), MLPX (65% real_asset_contracted/35% commodity_linked), SGOL (100% precious_metals), SGOV (100% short_duration), PAVE (82% broad/18% policy_thematic — per April 28 constituent audit).
* GitHub write workflow codified in M12 §CANONICAL_GITHUB_WRITE_WORKFLOW. Two patterns: PATTERN_A (framework amendments: create_branch → push_files → create_pull_request; no SHA required) and PATTERN_B (session write-back: create_or_update_file to master with SHA). Root cause of prior failures documented.

2026-04-29 — Session write-back: full audit, XAR ThematicETF_ClassificationAudit completed, calibration proposals documented
* Scenario probabilities: A=8%, B=45%, C=38%, D=3%, E=3%, F=3% — UNCHANGED from April 28. All scoring inputs unchanged (FOMC + Q1 GDP both pending April 30). 25pp cap not triggered. derivation_method: scored.
* Primary driver: Strait of Hormuz Crisis / US-Iran War (Day 60). Diplomatic track stalled. No ceasefire. Trump rejected Iran proposal. Brent gap to $110 C-trigger ~$2-4/bbl — closest recorded this series.
* XAR ThematicETF_ClassificationAudit() COMPLETED: geopolitical_premium classification CONFIRMED at constituent level. Top holdings (Heico, TransDigm, L3Harris, Northrop, RTX, General Dynamics, Huntington Ingalls, Curtiss-Wright) are defense procurement dependent. NAV coverage ~65% (exceeds 60% minimum). Mandate-dependent NAV ~75-80% (exceeds 30% threshold). XAR §11 entry confirmed: 90% geopolitical_premium / 10% broad_market_equity_domestic. §10.3 updated.
* M14 composite divergence signal: HIGH. commodity_fear_divergence HIGH (energy 90d >+35%, VIX flat/declining). equity_scenario_divergence MODERATE (broad equity 30d est. +3-5% while directive reductive). UnderweightReviewTrigger fired: MLPX underweight in Relative IRA (-8.76pp) and Relative Roth (-17.04pp) with 30d appreciation ~10%. EntryExtensionGuard passed (MLPX ~13% above 90d avg; threshold 20%). WAR PREMIUM ENTRY GUARD: both guards pass for MLPX at current price.
* M15 blended scenario returns computed for all holdings. EV ranking: SGOL +5.51% > MLPX +3.80% > XAR +1.47% > SGOV +0.80% > PAVE -4.48% > VTI -5.17%.
* Per-account EV at current vs target weights:
  - Primary IRA: current 2.23% → target 3.11% (required 3.2%; gap closes to 0.09pp at target)
  - Primary Roth: current 2.25% → target 3.09% (required 2.8%; FEASIBLE at target)
  - Taxable Acc3: 0.80% preservation — meets objective
  - Taxable Acc4: current 1.46% → target 1.60%
  - Relative IRA: current 2.95% → target 3.33% (floor objective met)
  - Relative Roth: current 1.85% → target 2.51% (required 2.8%; gap persists 0.29pp)
* All rebalancing trades remain deferred pending FOMC (April 30) + Q1 GDP (April 30).
* CALIBRATION PROPOSALS — for formal adoption at May 5-6 session (T1 evidence logged):
  1. secular_technology_growth Scenario C return: revise [−2%, +4%] → [+2%, +8%]. Evidence: Q1 2026 quarterly filings (T1) — MSFT Azure +40% (supply-constrained not demand-constrained), AMZN AWS +28% (fastest 15 quarters), META +33% revenue, GOOGL beat $2.9B vs consensus — all accelerating DURING active Scenario C. AI enterprise contracts multi-year; not correlated to Hormuz supply shock. 2022 Ukraine analog understates AI capex cycle independence.
  2. secular_technology_growth Scenario B return: revise [−10%, −3%] → [−6%, −1%]. Evidence: Q1 2026 EPS growth rate (AMZN $2.78 vs $1.64 est.; MSFT $4.27 vs $4.07 est.) materially higher than 2022 tech which had zero AI revenue during multiple compression. Earnings growth partially offsets multiple compression under rate constraint — less severe than 2022 pure multiple compression playbook.
  3. inflation_hedge_precious_metals Scenario C return: revise [+7%, +14%] → [−2%, +6%]. Evidence: Gold spot $4,554 — down 18% from $5,595 January ATH during active Scenario C. Mechanism: high oil → sticky inflation → Fed holds hawkish → real yields 1.89% elevated → gold (non-yielding) underperforms. Framework Scenario C was calibrated for C-dove (Fed eventually accommodates); current regime is C-hawk (Fed holding rates persistently). Conservative floor reflects C-hawk empirical data. Upside retains C-dove optionality if Fed eventually pivots.
  4. Framework design proposal (for Q2 June 30 audit): add Fed response function sub-variable to Scenario C scoring. Current framework does not distinguish C-hawk vs C-dove; gold and real yield asset returns are materially different across these sub-states. Not a calibration-dated threshold — proposed as module architecture enhancement.
* CRITICAL IMPLICATION of Proposal 3: If adopted, SGOL EV revises from +5.51% to +2.09%. SGOL rank drops from #1 to #3 (below MLPX). This would materially change M13.idealAllocation() output for all accounts — SGOL targets would decrease, MLPX/XAR targets would increase. Full reallocation recomputation required at May 5-6 session IF calibration proposals are adopted.
* AI ETF evaluation: CHAT (100% secular_tech) EV = -5.38% current / -2.06% revised. AIPO (~50% secular_tech / 30% real_asset / 20% broad) EV = -1.77% current / -1.17% revised. Neither positive EV under current scenario weights. AIPO preferred over CHAT (power infrastructure component provides B-scenario partial hedge). Decision deferred. If calibration proposals adopted AND SGOL targets reduced, freed allocation weight could partially fund AIPO position. AIPO requires §11 entry before any allocation. Tax placement: taxable accounts only.
* Taxable Acc4 sheet target discrepancy noted: sheet shows PAVE 12% / XAR 30% / MLPX 38% / SGOV 20% vs calibration state PAVE 11% / XAR 32% / MLPX 39% / SGOV 18%. Calibration state is authoritative. Sheet update required next session.
* Wash sale: VTI window clears April 30. VTI purchase (~$32K, ~91 shares) timing and account to be determined at May 5-6 session after FOMC + GDP clarity.

_______________

## Section 4 — Growth Objectives: Return Table and Multipliers
All values in this section are CALIBRATION_DATED.
Review at every quarter-end audit alongside §1 and §2 thresholds.
@see M13_GrowthObjectives

Last calibrated: April 23, 2026 (v1.3 initial instantiation; v1.4 B/C multipliers and floors revised)
Full empirical audit scheduled: June 30, 2026

⚠ PENDING CALIBRATION PROPOSALS (April 29, 2026 — not yet adopted; decision at May 5-6 session):
* secular_technology_growth Scenario C: proposed revision [−2%, +4%] → [+2%, +8%]
* secular_technology_growth Scenario B: proposed revision [−10%, −3%] → [−6%, −1%]
* inflation_hedge_precious_metals Scenario C: proposed revision [+7%, +14%] → [−2%, +6%]
These values in §4.1 remain at current figures until formally adopted. Do NOT use proposed values for computation until adopted.

### 4.1 Expected Real Annualized Return Table
Conservative end used for ALL computations. Upside end disclosed in briefing only.
Format per cell: [conservative%, upside%]
All scenario return computations use M15.blendedScenarioReturn() — this table is consumed via that function, never directly.

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
| secular_technology_growth | [6, 16] | [-10, -3] | [-2, 4] | [-14, -5] | [-10, -4] | [4, 11] |

secular_technology_growth added April 28, 2026 (v1.7). Provisional — empirical audit June 30, 2026.
Analogues: 2010-2021 tech multiple expansion (A/F upside); 2022 compression under rate tightening (B downside); 2022 Ukraine invasion equity impact vs tech (C — less negative than broad market); 2022 demand-driven drawdown (D); 2023-2024 AI re-expansion (A/F upside).
Note: these values are also reflected in the §4.1 table as the secular_technology_growth row.

### 4.2 IRA Target Multipliers (planning horizon: 10 years)
Floor: 1.3x REVISED April 23, 2026 (was 1.5x) — restore to 1.5x when commodity-linked added post-war.

| Scenario | Multiplier | Implied Real Return | Basis |
| :-: | :-: | :-: | :-- |
| A | 2.0 | ~7.2% annualized | Historical soft landing 1990s |
| B | 1.3 | ~2.7% annualized | REVISED April 23, 2026 from 1.5x. Restore when commodity-linked added post-conflict. |
| C | 1.3 | ~2.7% annualized | REVISED April 23, 2026 from 1.5x. Same rationale as B. |
| D | 1.3 | ~2.7% annualized | Preservation primary; demand collapse |
| E | 1.2 | ~1.8% annualized | Capital preservation; maximum stress |
| F | 2.0 | ~7.2% annualized | Strong nominal growth; similar to A on 10yr horizon |

Current regime weighted target (A=8%, B=45%, C=38%, D=3%, E=3%, F=3%) = 1.374x. Required real return ~3.2% annualized. Portfolio achieves ~3.05% — gap 0.18pp accepted.

### 4.3 Roth IRA Target Multipliers (planning horizon: 15 years)
Floor: 1.3x REVISED April 23, 2026 (was 2.0x) — restore to 2.0x when commodity-linked added post-war.

| Scenario | Roth 15yr Multiplier | Notes |
| :-: | :-: | :-- |
| A | 3.1 | Full tax-free compounding; extended 15yr runway |
| B | 1.3 | REVISED April 23, 2026 from 2.0x. Restore when commodity-linked added. |
| C | 1.3 | REVISED April 23, 2026 from 2.0x. Same rationale. |
| D | 1.6 | Preservation + modest bond appreciation |
| E | 1.4 | Capital preservation; rupture scenario |
| F | 3.1 | Same as A; full overheat compounding advantage |

Current regime weighted multiplier = 1.510x. Required real return ~2.8% annualized. Primary Roth achieves ~2.97% — FEASIBLE. Relative Roth achieves ~2.2% — 0.57pp gap accepted this regime.

### 4.4 Structural Floor and Concentration Parameters

| Parameter | Current Value | Type |
| :-: | :-: | :-: |
| Base floor (fraction of current allocation) | 0.25 | Calibration-dated |
| Minimum floor (% of account total value) | 2% | Calibration-dated |
| Concentration cap (max single position) | 40% | Calibration-dated |
| Floor nominal loss probability threshold | 15% | Calibration-dated |

_______________

## Section 5 — Review Cadence

| Date | Type | Scope |
| :-: | :-: | :-: |
| 2026-06-30 | Scheduled Q2 (first full audit) | Compute 180d medians HY/IG/CCC; verify triggers 75th-90th percentile; hit-rate audit §2; classify unflagged thresholds; audit §4 return table and multipliers; restore §4.2/§4.3 B/C and floors if commodity-linked added; first audit §9 M14 thresholds; first audit §10 M08 ETF thresholds; first audit §11 role registry + instrument classification weights; first empirical audit secular_technology_growth return estimates |
| 2026-09-30 | Scheduled Q3 | Full audit all calibration-dated thresholds |
| 2026-12-31 | Scheduled Q4 | Full audit |
| 2027-03-31 | Scheduled Q1 2027 | Full audit |

_______________

## Section 6 — First-Audit Checklist (for June 30, 2026 session)

1. Compute trailing 180-day median for FRED BAMLH0A0HYM2, BAMLC0A0CM, BAMLH0A3HYC.
2. Compute 10th/25th/75th/90th percentiles of trailing distribution for each series.
3. Verify HY\_STRESS\_DELTA (+150) places trigger in 75th-90th percentile band. Adjust if needed.
4. Verify HY\_RECESSION\_DELTA (+300) places trigger in 75th-90th percentile band. Adjust if needed.
5. Verify IG\_TRANSMISSION\_DELTA (+60) places trigger in 75th-90th percentile band. Adjust if needed.
6. Hit-rate audit each absolute threshold in Section 2 against trailing 5-year data.
7. Formally classify currently-unflagged thresholds in Sections 2.2, 2.3, 2.4.
8. First empirical audit of §4.1 return table — all roles including secular_technology_growth.
   Additional item (added April 29, 2026): evaluate calibration proposals for secular_tech B/C and precious_metals C using Q1 2026 actual data as empirical anchors. Decision on adoption should incorporate FOMC and GDP outcomes from April 30.
9. First empirical audit of §4.2 and §4.3 multipliers. Assess whether commodity-linked has been added; if so restore B/C multipliers and floors (IRA: 1.5x; Roth: 2.0x).
10. Audit §4.4 floor and concentration parameters.
11. First audit of §9 M14 thresholds: assess whether divergence and entry extension thresholds produced actionable signals or noise since adoption.
12. First audit of §10 M08 ETF classification thresholds: review ThematicETF_ClassificationAudit() and MandateImpairmentPropagation() parameter outcomes since April 28. Adjust thresholds if systematic misclassifications observed.
13. XAR ThematicETF_ClassificationAudit() COMPLETED April 29 — no further audit required at Q2 for XAR unless fund composition changes materially.
14. First audit of §11 instrument classification weights: re-verify component weights for all holdings using fresh fund composition data. Flag any instrument where weight drift > 5pp since last review.
15. Empirical audit of secular_technology_growth return estimates (§11.2 + §4.1 row): validate against 2022 tech compression and 2023-2024 re-expansion data. Incorporate Q1 2026 actual data from Mag7 quarterly filings. Adjust conservative/upside ranges if distribution evidence warrants.
16. Review §11.ROLE_REGISTRY: assess whether any new structural return drivers have emerged warranting a new role. Specifically: assess whether AI capex cycle warrants a sub-role split (infrastructure AI vs software AI).
17. Assess AIPO (Defiance AI & Power Infrastructure ETF) for §11 classification if portfolio decision made. Proposed classification: ~50% secular_technology_growth / 30% real_asset_contracted_revenue / 20% broad_market_equity_domestic — requires empirical verification against fund holdings.
18. Add Fed response function sub-variable to Scenario C scoring (design proposal, April 29 session).
19. Record all results in Section 3 Calibration Log.

_______________

## Section 7 — Session Observations Log (Credit Readings)

| Date | HY OAS (bps) | IG OAS (bps) | CCC OAS (bps) | Source | T1 Flag |
| :-: | :-: | :-: | :-: | :-: | :-: |
| 2026-04-19 | 285 | 83 | 921 | Trading Economics / FRED | composite_only |
| 2026-04-21 | 285 | 83 | 921 | Trading Economics / FRED (stale — last updated Apr 15-16) | stale |
| 2026-04-22 | 287 | 83 | 921 | Trading Economics / FRED (HY last updated Apr 20; IG/CCC Apr 16-17) | stale |
| 2026-04-23 | 287 | 83 | 921 | Trading Economics / FRED (HY Apr 20; IG/CCC Apr 16-17 — stale 3-7 days) | stale |
| 2026-04-28 | 285 | 83 | 921 | Trading Economics / FRED (HY Apr 21; IG/CCC Apr 16-17 — stale 7-12 days) | stale |
| 2026-04-29 | 284 | 80 | 921 | Trading Economics proxy; FRED HY Apr 28 (1 day lag); IG cross-referenced T2 source article confirming ~80 bps near 25yr tights; CCC carry forward | stale (IG: composite_only) |

_______________

## Section 8 — Session State Log

date: 2026-04-21
scenario_probabilities: { A: 7%, B: 44%, C: 36%, D: 3%, E: 7%, F: 3% }
primary_driver: Strait of Hormuz Crisis / US-Iran War (Day 52)
derivation_method: scored
open_triggers:
  - Ceasefire expiry April 22
  - Warsh Senate confirmation hearing April 21
  - Q1 2026 GDP advance estimate due ~April 30
  - Next CPI print ~May 10-12
open_decisions:
  - PAVE legislative mandate verification required
next_session_flags:
  - MOVE index not fetched
  - Ceasefire expiry outcome — reassess C probability
  - Warsh confirmation outcome — assess E probability
  - Verify PAVE/IIJA spending mandate status via T1 source

---

date: 2026-04-22
scenario_probabilities: { A: 8%, B: 45%, C: 38%, D: 3%, E: 3%, F: 3% }
primary_driver: Strait of Hormuz Crisis / US-Iran War (Day 53)
derivation_method: scored
open_triggers:
  - Brent $110 C-trigger — clock not started; currently ~$100
  - Q1 2026 GDP advance estimate ~April 30
  - FOMC April 28-29 — expected hold
  - PAVE/IIJA FLAGGED — T1-verified
open_decisions:
  - ALL SUPERSEDED by April 23 M13 targets
next_session_flags:
  - SUPERSEDED — see April 23 entry

---

date: 2026-04-23
scenario_probabilities: { A: 8%, B: 45%, C: 38%, D: 3%, E: 3%, F: 3% }
primary_driver: Strait of Hormuz Crisis / US-Iran War (Day 55+)
derivation_method: scored
open_triggers:
  - Brent $110 C-trigger — clock NOT started; ~$103.50; gap $6.50/bbl
  - FOMC April 28-29 — reassess A/B scores on release
  - Q1 2026 GDP advance estimate ~April 30 — if negative: B check_gdp to 3; D watch begins
  - Next CPI print ~May 10-12
  - Warsh confirmation stalled
open_decisions:
  - Primary IRA: sell VTI -49, XAR -30; buy MLPX +8, SGOL +541. Targets: VTI 10%, XAR 22%, MLPX 26%, SGOL 42%
  - Primary Roth: sell VTI -8, XAR -4; buy MLPX +3, SGOL +88. Targets: VTI 10%, XAR 22%, MLPX 27%, SGOL 41%
  - Taxable Acc4: PAVE reduction SUPERSEDED by April 28 entry. XAR +20, MLPX +76, SGOV +149 pending
  - Relative IRA: sell VTI -20, SGOL -152, SGOV -21; buy MLPX +222. Targets: VTI 6%, MLPX 35%, SGOL 39%, SGOV 20%
  - Relative Roth: sell VTI -2, SGOL -19; buy MLPX +23. Targets: VTI 22%, MLPX 38%, SGOL 40%
  - Taxable Acc3: SGOV 100% — no action
next_session_flags:
  - PAVE cost basis verification required
  - MOVE index still not fetched
  - Q1 2026 GDP ~April 30 — reassess B/D scoring
  - FOMC April 29 — reassess A/B scores
  - Brent $103.50 — gap to $110 is $6.50; monitor closely

---

date: 2026-04-28
scenario_probabilities: { A: 8%, B: 45%, C: 38%, D: 3%, E: 3%, F: 3% }
primary_driver: Strait of Hormuz Crisis / US-Iran War (Day 59) — Iran submitted new proposal via Pakistani mediators; Trump cancelled envoy trip; diplomatic stalemate with open channel
derivation_method: scored
manual_override_reason: null
open_triggers:
  - FOMC April 29 — reassess A/B scoring on release; 94% probability hold
  - Q1 2026 GDP ~April 30 — BINARY for B/D; negative means B check_gdp to 3; D watch begins
  - Brent $110 C-trigger — clock NOT started; peaked $108.11 April 27; ~$106 now; gap ~$2-4/bbl
  - Next CPI print ~May 10-12
  - IIJA expiration September 30, 2026 — monitor reauthorization
  - Warsh confirmation expected soon after DOJ probe dropped
open_decisions:
  - Primary IRA: sell VTI -49, XAR -30; buy MLPX +8, SGOL +541. Deferred pending FOMC + GDP
  - Primary Roth: sell VTI -8, XAR -4; buy MLPX +3, SGOL +88. Same deferral
  - Taxable Acc4: buy XAR +20, MLPX +76, SGOV +149. PAVE hold at ~11% (watch status). Same deferral
  - Relative IRA: sell VTI -20, SGOL -152, SGOV -21; buy MLPX +222. Same deferral
  - Relative Roth: sell VTI -2, SGOL -19; buy MLPX +23. Same deferral
  - Taxable Acc3: SGOV 100% — no action
next_session_flags:
  - FOMC April 29: reassess A/B scoring
  - Q1 2026 GDP ~April 30: BINARY — negative triggers B check_gdp to 3; D watch begins
  - Brent: gap to $110 now ~$2-4/bbl — monitor daily
  - PAVE: watch status; hold at ~11%; monitor IIJA reauthorization
  - XAR: apply ThematicETF_ClassificationAudit() next session
  - Proceed with all open decisions after FOMC + GDP clarity
  - FRED credit spreads stale (HY Apr 21; IG/CCC Apr 16-17) — fetch fresh next session
  - M15 PR open — review and merge before next full session init

---

date: 2026-04-29
scenario_probabilities: { A: 8%, B: 45%, C: 38%, D: 3%, E: 3%, F: 3% }
primary_driver: Strait of Hormuz Crisis / US-Iran War (Day 60) — no ceasefire; diplomatic track stalled; Trump rejected Iranian proposal; IEA largest supply shock on record
derivation_method: scored
manual_override_reason: null
open_triggers:
  - FOMC April 30 — REASSESS A/B scoring on release (language determines: 'patient' = B maintained; 'concerned' = C confirmation; cut odds for 2026 direction material)
  - Q1 2026 GDP April 30 — BINARY: negative → B check_gdp to 3; D watch begins. Positive >1.5% → B check_gdp drops to 1; significant probability shift
  - Brent $110 C-trigger — clock NOT started; gap ~$2-4/bbl; EIA STEO Q2 2026 peak ~$115 projection; monitor daily without exception
  - CPI May 10-12 — second print. If >=3.5% YoY: C check_cpi upgrades to 2; C probability rises
  - IIJA reauthorization September 30, 2026
  - Warsh confirmation expected
open_decisions:
  - Primary IRA: sell VTI -49, XAR -30; buy MLPX +8, SGOL +541. Deferred pending FOMC + GDP. NOTE: if calibration proposals adopted at May 5-6, rerun idealAllocation() before executing — targets may change materially
  - Primary Roth: sell VTI -8, XAR -4; buy MLPX +3, SGOL +88. Same deferral + same note
  - Taxable Acc4: buy XAR +20, MLPX +76, SGOV +149. PAVE hold ~11%. Same deferral
  - Relative IRA: sell VTI -20, SGOL -152, SGOV -21; buy MLPX +222. Same deferral
  - Relative Roth: sell VTI -2, SGOL -19; buy MLPX +23. Same deferral
  - Taxable Acc3: SGOV 100% — no action
  - VTI purchase ~$32K (~91sh): wash sale clears April 30; timing and account to be resolved at May 5-6
  - Calibration proposals (3): formal adoption decision at May 5-6 session. If adopted: rerun M13.idealAllocation() before executing ANY rebalancing trades — SGOL targets will change
  - Taxable Acc4 sheet targets: update to match calibration state (PAVE 11%, XAR 32%, MLPX 39%, SGOV 18%)
  - AIPO §11 classification: pending portfolio decision
next_session_flags:
  - FOMC language AND Q1 GDP: both due April 30 — CRITICAL inputs for May 5-6 session
  - If calibration proposals adopted: M13.idealAllocation() must be rerun for all accounts BEFORE executing deferred trades
  - If Q1 GDP negative: B check_gdp upgrades to 3; B probability rises ~5pp; reassess allocation targets
  - If Q1 GDP >1.5%: B check_gdp drops to 1; B probability falls ~5pp; reassess allocation targets
  - Brent daily monitoring — $110 clock could start any session
  - M14 composite divergence remains HIGH — underweight review active for MLPX in Relative accounts
  - MOVE index: still not fetched — low priority but log absence

---

_______________

## Section 9 — Market Regime Thresholds (M14)
All values CALIBRATION_DATED. First audit: June 30, 2026.
@see M14_MarketRegime

Last calibrated: April 27, 2026 (v1.5 initial instantiation)

### 9.1 Divergence Signal Thresholds

| Parameter | Current Value | Type |
| :-: | :-: | :-: |
| commodity\_fear\_divergence HIGH | energy\_90d >= +15% AND VIX\_change\_90d\_pts <= 0 | Calibration-dated |
| commodity\_fear\_divergence MODERATE | energy\_90d >= +10% AND VIX\_change\_90d\_pts <= +5 pts | Calibration-dated |
| equity\_scenario\_divergence HIGH | broad\_equity\_30d >= +5% while directive reductive | Calibration-dated |
| equity\_scenario\_divergence MODERATE | broad\_equity\_30d >= +2% while directive reductive | Calibration-dated |

### 9.2 Underweight Review Trigger

| Parameter | Current Value | Type |
| :-: | :-: | :-: |
| underweight\_gap\_trigger | 5 pp | Calibration-dated |
| appreciation\_trigger\_30d | 5% | Calibration-dated |

### 9.3 Entry Extension Guard Thresholds

| Role | Threshold | Notes |
| :-: | :-: | :-: |
| broad\_market\_equity | 15% | Provisional |
| thematic\_sector\_equity | 20% | policy\_driven\_thematic\_equity, geopolitical\_premium |
| commodity\_linked | 20% | WAR PREMIUM ENTRY GUARD also applies independently |
| inflation\_hedge\_precious\_metals | 20% | Provisional |
| real\_asset\_contracted\_revenue | 15% | Provisional |
| secular\_technology\_growth | 20% | Added April 28, 2026 (v1.7) — same threshold as thematic sector |
| rate\_sensitive\_income\_short | N/A | Guard does not apply |
| rate\_sensitive\_income\_long | N/A | Duration risk captured by scenario framework |

_______________

## Section 10 — M08 Thematic ETF Classification Parameters
All values CALIBRATION_DATED. First audit: June 30, 2026.
@see M08_FunctionalRoles.ThematicETF_ClassificationAudit()
@see M08_FunctionalRoles.MandateImpairmentPropagation()

Added: April 28, 2026 (v1.6). Rationale: PAVE reclassification session revealed that applying policy_driven_thematic_equity and FLAGGED status at ETF label level without constituent-level analysis produces materially incorrect conclusions. The $2.3B IIJA rescissions targeted NEVI and climate programs, not the highway/bridge/rail formula programs that PAVE's dominant holdings depend on.

### 10.1 Classification Audit Parameters

| Parameter | Current Value | Notes |
| :-: | :-: | :-- |
| minimum\_nav\_coverage | 60% | Minimum % of ETF NAV requiring constituent-level analysis before policy\_driven\_thematic\_equity is confirmed. If holdings unavailable for this coverage, classify as UNCONFIRMED\_THEMATIC until resolved. |
| mandate\_exposure\_materiality\_threshold | 30% | Minimum % of ETF NAV with confirmed primary mandate dependence required to confirm classification. Below this threshold, classify by dominant actual constituent return driver instead. |

### 10.2 Mandate Impairment Propagation Parameters

| Parameter | Current Value | Notes |
| :-: | :-: | :-- |
| program\_rescission\_materiality | 20% | Minimum % of ETF NAV directly at risk from specifically-identified rescinded programs to escalate status to FLAGGED. Below this, watch status. Direct risk = constituent earns >5% of total revenue from the specific rescinded program. |
| constituent\_revenue\_materiality | 5% | Minimum share of a constituent holding's total revenue from the rescinded program to count as exposed. |

### 10.3 Application Log

| Date | ETF | Audit Type | Finding | Outcome |
| :-: | :-: | :-: | :-: | :-: |
| 2026-04-28 | PAVE | MandateImpairmentPropagation | NEVI rescission (~$879M) maps to Quanta Services EV segment. Highways/bridges/rail formula programs intact. ETF NAV at risk: ~10-15%. Below 20% materiality threshold. | watch (not FLAGGED) |
| 2026-04-28 | PAVE | ThematicETF_ClassificationAudit | Retrospective: top 32% NAV covered. Mandate-dependent NAV ~15-18%. Below 30% threshold. Dominant actual driver: industrial/capital goods broadly. | Revised to watch; monitor |
| 2026-04-29 | XAR | ThematicETF_ClassificationAudit | Top 8 holdings analyzed: Heico, TransDigm, L3Harris, Northrop, RTX, General Dynamics, Huntington Ingalls, Curtiss-Wright (~65% NAV coverage estimated; exceeds 60% minimum). All holdings defense procurement dependent (DoD + allied government contracts). Mandate-dependent NAV: ~75-80% (exceeds 30% threshold). geopolitical_premium binding driver (elevated_conflict, defense_procurement, geopolitical_tension) confirmed at constituent level. 10% broad_market residual retained for commercial aerospace/diversified industrial. | CONFIRMED: XAR = 90% geopolitical_premium / 10% broad_market_equity_domestic. Status: thesis_intact. Monitor for fund composition drift at Q2 audit. |

_______________

## Section 11 — Instrument Classification Registry (M15)
All values CALIBRATION_DATED. First audit: June 30, 2026.
@see M15_InstrumentClassification

Added: April 28, 2026 (v1.7).

Design: roles are defined here, not in module files. Instruments are classified here with fractional component weights. To add a role: add to §11.1 and §4.1. To add an instrument: add to §11.3. No module file edits required for either operation.

### 11.1 Role Registry

All registered roles must have a corresponding §4.1 return table row. Adding a role without a §4.1 row causes HARD_STOP at session start (M15.ValidateClassifications).

| Role | Binding Driver | Added | Status |
| :-- | :-- | :-: | :-: |
| geopolitical_premium | elevated_conflict, defense_procurement, geopolitical_tension | v1.0 (original) | Active |
| inflation_hedge_precious_metals | real_yield_compression, monetary_base_expansion, dollar_reserve_status_erosion | v1.0 (original) | Active |
| inflation_hedge_commodity_linked | broad_commodity_prices, energy, materials | v1.0 (original) | Active |
| real_asset_contracted_revenue | physical_throughput, contracted_fees, real_infrastructure | v1.0 (original) | Active |
| policy_driven_thematic_equity | legislated_government_spending, regulatory_mandates, domestic_policy_cycle | v1.0 (original) | Active |
| rate_sensitive_income_short_duration | short_term_interest_rates, duration <= 1y | v1.0 (original) | Active |
| rate_sensitive_income_long_duration | long_term_interest_rates, duration > 1y | v1.0 (original) | Active |
| broad_market_equity_domestic | domestic_aggregate_economic_growth | v1.0 (original) | Active |
| broad_market_equity_international | ex_US_aggregate_economic_growth | v1.0 (original) | Active |
| secular_technology_growth | AI_capex_cycle, mega-cap_tech_multiple_expansion, software_adoption, semiconductor_demand | v1.7 (April 28, 2026) | Active — provisional, empirical audit June 30, 2026 |

### 11.2 secular_technology_growth — Return Estimates
Provisional. Added April 28, 2026. Full empirical audit: June 30, 2026.
Analogues used: 2010-2021 tech multiple expansion (A/F); 2022 compression under rate tightening (B); 2022 Ukraine invasion equity impact vs tech (C — less negative than broad market); 2022 demand-driven drawdown (D); 2023-2024 AI re-expansion (A/F upside).
Note: these values are also reflected in the §4.1 table as the secular_technology_growth row.
⚠ CALIBRATION PROPOSALS PENDING (April 29, 2026): B revision [−10%,−3%]→[−6%,−1%]; C revision [−2%,+4%]→[+2%,+8%]. Current values remain until formally adopted at May 5-6 session.

| Scenario | Conservative | Upside | Key rationale |
| :-: | :-: | :-: | :-- |
| A (Soft Landing) | 6% | 16% | Fed cuts compress discount rate on long-duration growth; AI capex cycle expands |
| B (Stagflation) | -10% | -3% | High multiples compress harder under rate constraint than broad equity |
| C (Inflationary Shock) | -2% | 4% | Conflict transmission to AI capex cycle is weak; less negative than broad_market_equity_domestic |
| D (Deflationary Recession) | -14% | -5% | Capex cycles compress in demand collapse; multiple contraction severe |
| E (Structural Rupture) | -10% | -4% | Growth multiples collapse in systemic stress; reserve stress impairs long-duration assets |
| F (Growth Overheat) | 4% | 11% | Strong nominal demand supports AI capex; rising rates partially compress multiples |

### 11.3 Instrument Classification Table

All instruments appearing in the allocation file must have an entry here. New instruments without entries trigger HARD_STOP at session start (M15.ValidateClassifications). Weights must sum to 1.0 per instrument. Review staleness threshold: 90 calendar days.

**Initial population: April 28, 2026 — current holdings**

#### VTI
- Components: broad_market_equity_domestic (0.78) + secular_technology_growth (0.22)
- Basis: CRSP US Total Market, ~3,600 holdings. Technology sector ~30% of fund; ~22% estimated as AI/mega-cap tech multiple driver (Microsoft, Apple, Nvidia, Alphabet, Amazon, Meta — these six names represent disproportionate return attribution via AI capex cycle narrative). Residual tech and all other sectors mapped to broad_market_equity_domestic.
- Source: Vanguard fund page sector weights; top holdings analysis
- Methodology: sector_weight_analysis + judgment
- Last reviewed: 2026-04-28
- Notes: secular_technology_growth weight re-verify at Q2 audit. The 22% weight reflects estimated AI/mega-cap tech multiple attribution, not raw technology sector weight. The critical implication: VTI is less negative than generic broad_market_equity_domestic in Scenario C; more negative in Scenario B.

#### XAR
- Components: geopolitical_premium (0.90) + broad_market_equity_domestic (0.10)
- Basis: SPDR S&P Aerospace & Defense ETF. Dominant return driver is defense procurement tied to geopolitical tension. ThematicETF_ClassificationAudit COMPLETED April 29, 2026. Top holdings (Heico, TransDigm, L3Harris, Northrop, RTX, General Dynamics, Huntington Ingalls, Curtiss-Wright) confirmed defense procurement dependent. ~65% NAV coverage; mandate-dependent NAV ~75-80%. 10% broad_market reflects commercial aerospace and diversified industrial revenue in lower holdings.
- Source: SPDR fund page; April 29 constituent audit (top ~65% NAV)
- Methodology: ThematicETF_ClassificationAudit() — CONFIRMED
- Last reviewed: 2026-04-29
- Notes: Classification confirmed. No further audit required until fund composition changes materially (>5pp weight drift in top holdings, or rebalance toward non-defense sectors). Re-verify at Q2 audit as standard staleness check.

#### MLPX
- Components: real_asset_contracted_revenue (0.65) + inflation_hedge_commodity_linked (0.35)
- Basis: Global X MLP & Energy Infrastructure ETF. Primary return driver is contracted fee revenue (throughput, capacity, gathering contracts — pipeline and midstream structure). Secondary driver is commodity price linkage through volume sensitivity to energy prices, gathering and processing margins.
- Source: Global X fund page; MLP business model analysis; midstream industry structure
- Methodology: holdings_analysis + judgment
- Last reviewed: 2026-04-28
- Notes: The 65/35 split reflects typical midstream fee-to-commodity exposure. Re-verify at Q2 audit against current fund composition.

#### SGOL
- Components: inflation_hedge_precious_metals (1.00)
- Basis: Aberdeen Standard Physical Gold ETF — physical gold grantor trust. Single-driver. Pure.
- Source: Aberdeen Standard fund page
- Methodology: direct
- Last reviewed: 2026-04-28
- Notes: ⚠ CALIBRATION ANOMALY (April 29, 2026): SGOL producing negative real returns during active Scenario C (down 18% from ATH) due to elevated real yields (10Y TIPS +1.89%). Framework §4.1 Scenario C return [+7%, +14%] may overstate gold's C-scenario performance in C-hawk regime (Fed holding rates). Calibration proposal pending for May 5-6 session. Do not use §4.1 Scenario C = 7% as confirmed return estimate — treat as potentially stale pending formal revision.

#### SGOV
- Components: rate_sensitive_income_short_duration (1.00)
- Basis: iShares 0-3 Month Treasury Bill ETF — 0-3 month Treasury bills. Single-driver. Pure.
- Source: iShares fund page
- Methodology: direct
- Last reviewed: 2026-04-28

#### PAVE
- Components: broad_market_equity_domestic (0.82) + policy_driven_thematic_equity (0.18)
- Basis: Global X U.S. Infrastructure Development ETF. ThematicETF_ClassificationAudit conducted April 28, 2026 (top ~32% NAV): Howmet (~3.3%), Trane (~3.4%), Eaton (~3.4%), CSX (~3.3%), Parker-Hannifin (~3.5%) — returns not primarily mandate-dependent. Mandate-dependent NAV: ~15-18%. policy_driven_thematic_equity weight (0.18) reflects infrastructure-mandate exposure across audited and extrapolated unaudited holdings. Dominant actual driver: industrial/capital goods broadly.
- Source: Global X fund page; April 28 constituent analysis; Transportation for America, GAO, FHWA
- Methodology: ThematicETF_ClassificationAudit() + MandateImpairmentPropagation()
- Last reviewed: 2026-04-28
- Notes: Status: watch (not FLAGGED). Monitor IIJA reauthorization (September 30, 2026 expiration). Re-run audit if: reauthorization fails AND formula highway programs cut in successor bill.
