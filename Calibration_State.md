# Calibration State

Persistent framework configuration - load at every session start alongside session handoff.

Version: 1.9  Last updated: April 30, 2026 (Full M05 session: M13 rerun with updated section 4.1 v1.8 and new scenario probabilities A=7/B=42/C=42; VTI eliminated from all target allocations; AIPO + MAGS adopted and added to section 11; workflow established; MOVE index first logged; Brent C-trigger clock Day 2 active)  Next scheduled review: June 30, 2026 (Q2 2026 quarter-end)

---

## Load Verification Requirement

At session start, the advisor must state in the briefing:

"Calibration State loaded, last update: April 30, 2026"

Absence of this line indicates the calibration file was not loaded and the session is invalid for threshold-sensitive decisions.

After loading: run M15.ValidateClassifications() - all instruments in the allocation file must have section 11 entries before session proceeds to analysis.

---

## Section 1 - Credit Signal Thresholds (relative, 1.5a)

All HY/CCC/IG thresholds are relative to the trailing 180-day median of the underlying FRED series, computed at session start.

### 1.1 HY Composite - FRED: BAMLH0A0HYM2

| Parameter | Current Value | Type | Notes |
| --- | --- | --- | --- |
| HY_STRESS_DELTA | +150 bps | Calibration-dated | Provisional initial - full audit pending June 30, 2026 |
| HY_RECESSION_DELTA | +300 bps | Calibration-dated | Provisional initial - full audit pending June 30, 2026 |
| Velocity overlay | +100 bps over prior 60 days | Fixed structural | Not calibration-dated |
| Sustain period | 10 trading days | Fixed structural | Not calibration-dated |
| D-floor on recession-pricing trigger | 25% | Fixed structural | Not calibration-dated |

Baseline snapshot at instantiation (April 19, 2026): ~285 bps. Trailing 180d median to be computed at Q2 2026 audit.

Session observation (April 19): HY ~285 bps. No threshold fires.
Session observation (April 21): HY ~285 bps. Stale. No threshold fires.
Session observation (April 22): HY ~287 bps. Stale. No threshold fires.
Session observation (April 23): HY ~287 bps. Stale. No threshold fires.
Session observation (April 28): HY ~285-287 bps. Stale. HY_StressBeginning ~435 bps; gap ~148 bps.
Session observation (April 29): HY ~284 bps. FRED last Apr 28 (1 day lag). No threshold fires.
Session observation (April 30 full session): HY ~284 bps (carry forward). No threshold fires. T1_flag: stale.

### 1.2 IG Composite - FRED: BAMLC0A0CM

| Parameter | Current Value | Type | Notes |
| --- | --- | --- | --- |
| IG_TRANSMISSION_DELTA | +60 bps | Calibration-dated | Provisional initial - full audit pending June 30, 2026 |
| Velocity overlay | +40 bps over prior 60 days | Fixed structural | Not calibration-dated |
| Sustain period | 10 trading days | Fixed structural | Not calibration-dated |

Session observation (April 19): IG ~83 bps. Baseline reference.
Session observation (April 21-29): IG ~80-83 bps. Carry forward. IG_TransmissionReached NOT fired (threshold ~143 bps; gap ~60-63 bps). Stale.
Session observation (April 30 full session): IG ~80 bps (carry). NOT fired. T1_flag: stale.

### 1.3 CCC Tail - FRED: BAMLH0A3HYC

| Parameter | Current Value | Type | Notes |
| --- | --- | --- | --- |
| Ratio divergence | CCC widens 3x composite over 30d | Fixed structural | Not calibration-dated |
| Absolute divergence floor | CCC +200 bps while composite +<50 bps over 30d | Calibration-dated | Provisional - audit pending June 30, 2026 |

First divergence computation (April 19): CCC Apr 16 = 921 bps vs Mar 16 = 973 bps = -52 bps tightening. Neither threshold fired.
Session observations (April 21-30): CCC ~921 bps (carry forward; FRED stale). CCC_TailFirstWidening NOT fired. T1_flag: stale.

---

## Section 2 - Other Calibration-Dated Thresholds

### 2.1 Energy / Commodities

| Threshold | Current Value | Source | Audit Status |
| --- | --- | --- | --- |
| WTI floor - SGOL invalidation | $55 nominal OR 30% below 90d trailing WTI avg | Calibration-dated | Pending June 30 |
| Brent trigger - Scenario C | $110 nominal OR 40% above 90d trailing Brent avg | Calibration-dated | Pending June 30 |
| Brent invalidation - Scenario C | $80 nominal OR 20% below 90d trailing Brent avg | Calibration-dated | Pending June 30 |

Session observations:
- April 19: Brent $90.38. C trigger NOT fired.
- April 21: Brent ~$94-96. C trigger NOT fired.
- April 22: Brent ~$99.81. C trigger NOT fired.
- April 23: Brent ~$103.50. C trigger NOT fired. Gap $6.50/bbl.
- April 28: Brent peaked $108.11 Apr 27; ~$106 Apr 28. C trigger NOT fired. Gap ~$2-4/bbl. EIA STEO Q2 2026 peak ~$115 projection (T1).
- April 29: Brent ~$106. C trigger NOT fired. Gap ~$2-4/bbl.
- April 30: BRENT C-TRIGGER CLOCK ACTIVE. Day 1 = April 29 close $110.44. Day 2 = April 30 intraday $110.73. Clock fires if Brent sustains >=110 through ~May 13, 2026. Monitor every session without exception. SGOL WTI floor ($55) comfortably clear.

### 2.2 Currency

| Threshold | Current Value | Audit Status |
| --- | --- | --- |
| DXY sustained above - SGOL invalidation | 105 nominal | Pending June 30 |

DXY ~98.5-98.6 across all sessions through April 30. Well below 105. No SGOL invalidation risk.

### 2.3 Macro

| Threshold | Current Value | Audit Status |
| --- | --- | --- |
| CPI trigger - Scenario B | 4% YoY, 3+ consecutive prints | Pending June 30 |
| CPI invalidation - Scenario B | below 3% YoY, 2+ consecutive prints | Pending June 30 |
| GDP trigger - Scenario F | above 3% annualized, 2+ consecutive quarters | Pending June 30 |
| GDP invalidation - Scenario F | below 2% on BEA advance estimate | Pending June 30 |
| Unemployment trigger - Scenario D | +0.5% over any 3-month window | Pending June 30 |

April 30 full session: Q1 2026 GDP advance estimate = +2.0% annualized (BEA T1). Above 1.5% threshold - B check_gdp drops to 1. D watch NOT triggered. Core PCE 3.2% YoY (BEA T1). FOMC: hold at 3.5-3.75%. Language upgraded: inflation is elevated. 4 dissents (3 hawkish, 1 dovish/Miran). C-hawk regime confirmed. Next CPI May 10-12 (second print - watch for >=3.5% -> C check_cpi to 2).

Prior context: CPI March 3.3% YoY (1 of 3 for B trigger). Q4 2025 GDP 0.5%. Consumer sentiment 49.8 (record low). 10Y breakeven ~2.43%. Sahm Rule 0.20. Mag7 Q1 earnings all beat; zero guidance withdrawals. Azure +40%, AWS +28%, META +33%, GOOGL beat, AMZN EPS $2.78 vs $1.64 est. MSFT +18% YoY.

### 2.4 Instrument Evaluation

| Threshold | Current Value | Audit Status |
| --- | --- | --- |
| Foreign concentration disqualification | 40% single-country/single-region | Pending June 30 |
| AUM disqualification | $100M minimum | Pending June 30 |

---

## Section 3 - Calibration Log

2026-04-19 - Initial instantiation (v1.0). HY_STRESS_DELTA +150 bps, HY_RECESSION_DELTA +300 bps, IG_TRANSMISSION_DELTA +60 bps, CCC floor +200 bps. HY baseline ~285 bps.

2026-04-21 - Framework update (v1.2). Section 6 Session State Log added. M03 DeriveScenarioProbabilities() added.

2026-04-21 - First full portfolio audit session. Probabilities: A=7%, B=44%, C=36%, D=3%, E=7%, F=3%.

2026-04-22 - Scheduled review. Probabilities: A=8%, B=45%, C=38%, D=3%, E=3%, F=3%. PAVE FLAGGED (subsequently revised to watch Apr 28).

2026-04-23 - Framework update (v1.3): M13 adoption, section 4 added, GitHub migration.

2026-04-23 - M13 first application (v1.4). IRA B/C multipliers 1.5x->1.3x. Roth B/C multipliers 2.0x->1.3x. Initial M13 targets computed (superseded by April 30 rerun).

2026-04-27 - Framework update (v1.5): M14 adoption, section 9 added.

2026-04-28 - PAVE reclassification + M08 update (v1.6). PAVE status: watch (not FLAGGED). PAVE cost basis $54.09/share (~$1,286 embedded gain on 590 shares). Section 10 added.

2026-04-28 - Framework update (v1.7): M15 adoption, section 11 added, secular_technology_growth role added. Initial instrument classifications: VTI, XAR, MLPX, SGOL, SGOV, PAVE.

2026-04-29 - Session write-back. XAR ThematicETF_ClassificationAudit COMPLETED (confirmed: 90% geopolitical_premium / 10% broad_market). Calibration proposals documented as pending. M14 divergence HIGH. UnderweightReviewTrigger fired for Relative accounts (MLPX -8.5pp IRA, -16.87pp Roth). Probabilities unchanged A=8/B=45/C=38.

2026-04-30 - Calibration proposals adopted (v1.8). secular_technology_growth B: [-10%,-3%]->[-6%,-1%]. secular_technology_growth C: [-2%,+4%]->[+2%,+8%]. inflation_hedge_precious_metals C: [+7%,+14%]->[-2%,+6%]. XAR HoldJustification: break-even peace prob <5.6%; opportunity cost vs MLPX -2.33%/year. M13 structural gap: Primary IRA max achievable EV ~2.65% vs required 3.2%.

2026-04-30 - Full M05 session: M13 rerun, AIPO+MAGS adopted, VTI eliminated (v1.9)

- Session type: full M05. Allocation sheet fetched (Google Drive MCP). Calibration State fetched (GitHub MCP). MOVE index first logged. Credit carry-forward.
- FOMC (T1 federalreserve.gov): hold 3.5-3.75%, 11-1 vote. Miran dissented for cut; 3 others against easing bias (hawkish). Language: inflation is elevated. 4 dissents - most since 1992. C-hawk confirmed.
- Q1 2026 GDP: +2.0% (BEA T1). B check_gdp drops to 1. D watch NOT triggered. Core PCE 3.2% YoY.
- Brent C-trigger clock: Day 1 = April 29 close $110.44. Day 2 = April 30 $110.73. ACTIVE - 8 trading days to fire. Monitor every session.
- MOVE index: 68.68 (Investing.com, T2). First logged. 52-week range 55.77-115.02. Bond market calm. No fixed income stress.
- Scenario probabilities UPDATED: A=7% (-1pp), B=42% (-3pp), C=42% (+4pp), D=3%, E=3%, F=3%. GDP +2.0% weakens B stagnation thesis. FOMC hawkish + Brent clock Day 2 strengthen C. B and C co-equal at 42% - first occurrence this series. Justified: moderate growth + persistent inflation + acute supply shock. Max shift 4pp - within 25pp cap. derivation_method: scored.
- VTI ELIMINATED from all target allocations. Rationale: (1) all VTI in retirement accounts - zero tax friction; (2) 78% broad_market_equity_domestic returns -8% in B (42%) - structural drag; (3) AI ETF captures secular_tech function at higher conviction; (4) remaining positions cover all structural roles. VTI $32K wash-sale purchase (cleared April 30) CANCELLED - redirected to AIPO/MAGS.
- AIPO adopted as primary AI sector position. Classification: real_asset_contracted_revenue (0.55) + secular_technology_growth (0.20) + broad_market_equity_domestic (0.15) + inflation_hedge_commodity_linked (0.10). EV: +1.03%. EntryExtensionGuard: ~+9.8% above 90d avg vs 15% threshold - PASSES. Tax placement: all accounts including taxable. Added to section 11.
- MAGS adopted as secondary AI/secular-tech position. Classification: secular_technology_growth (0.85) + broad_market_equity_domestic (0.15). EV: -2.34% (negative EV; documented client judgment override - accepted for AI earnings momentum thesis and optionality on scenario shift toward A/F). EntryExtensionGuard: fund down 12.2% over 3 months; below 90d avg (~$75) - PASSES. RETIREMENT ACCOUNTS ONLY - swap structure generates phantom taxable gains. Added to section 11.
- AIPO/PAVE overlap: Eaton Corp (ETN) in both AIPO (~8.1% NAV) and PAVE (~3.4% NAV). Monitor combined concentration at Q2 audit.
- XAR staged sell: 180 shares limit at $265 in Taxable Acc4. XAR closed $266.59 Apr 30 - order likely executed. Client to verify at broker.
- M13 rerun completed with updated section 4.1 (v1.8) and new probabilities (A=7/B=42/C=42). New target allocations - see section 8 April 30 entry.
- Updated EV ranking (A=7/B=42/C=42): MLPX +3.83% > SGOL +1.83% > XAR +1.58% > AIPO +1.03% > SGOV +0.81% > MAGS -2.34% > PAVE -4.46%.
- Workflow established (permanent): client updates allocation file with target % -> allocation file computes share counts -> client executes trades. Advisor outputs target % only - never pre-computes share counts. Allocation file is authoritative source for share calculations.

---

## Section 4 - Growth Objectives: Return Table and Multipliers

All values CALIBRATION_DATED. Last calibrated: April 30, 2026 (v1.8). Full empirical audit: June 30, 2026.

CALIBRATION PROPOSALS ADOPTED April 30, 2026:
- secular_technology_growth Scenario C: [-2%,+4%]->[+2%,+8%]
- secular_technology_growth Scenario B: [-10%,-3%]->[-6%,-1%]
- inflation_hedge_precious_metals Scenario C: [+7%,+14%]->[-2%,+6%]
Post-adoption check: review if May 10-12 CPI surprises (>=4.0% or <=2.5%).

### 4.1 Expected Real Annualized Return Table

Conservative end used for ALL computations. Upside end disclosed in briefing only.
All scenario return computations use M15.blendedScenarioReturn() - this table is consumed via that function, never directly.

| Role | Scenario A | Scenario B | Scenario C | Scenario D | Scenario E | Scenario F |
| --- | --- | --- | --- | --- | --- | --- |
| geopolitical_premium | [-2, 3] | [2, 6] | [4, 10] | [-4, 0] | [1, 5] | [1, 4] |
| inflation_hedge_precious_metals | [0, 4] | [6, 12] | [-2, 6] | [-2, 4] | [10, 20] | [-3, 1] |
| inflation_hedge_commodity_linked | [2, 6] | [6, 12] | [7, 13] | [-8, -2] | [2, 6] | [2, 5] |
| real_asset_contracted_revenue | [3, 7] | [3, 7] | [3, 6] | [2, 6] | [2, 5] | [3, 7] |
| policy_driven_thematic_equity | [4, 8] | [-3, 1] | [-1, 3] | [-5, -1] | [-6, -2] | [4, 8] |
| rate_sensitive_income_short_duration | [0, 2] | [1, 3] | [1, 3] | [0, 3] | [-2, 2] | [1, 3] |
| rate_sensitive_income_long_duration | [3, 7] | [-4, -1] | [-5, -2] | [5, 10] | [-10, -3] | [-4, -1] |
| broad_market_equity_domestic | [5, 12] | [-8, -2] | [-4, -1] | [-12, -4] | [-8, -3] | [7, 14] |
| broad_market_equity_international | [4, 9] | [-5, -1] | [-6, -2] | [-8, -3] | [-10, -4] | [3, 8] |
| secular_technology_growth | [6, 16] | [-6, -1] | [+2, +8] | [-14, -5] | [-10, -4] | [4, 11] |

secular_technology_growth: added v1.7 Apr 28. B and C values revised v1.8 Apr 30. Provisional - empirical audit June 30, 2026.
inflation_hedge_precious_metals Scenario C: revised v1.8 Apr 30 (C-hawk regime empirical data).

### 4.2 IRA Target Multipliers (10-year horizon)

Floor: 1.3x (revised Apr 23 from 1.5x). Restore to 1.5x when commodity-linked added post-war.

| Scenario | Multiplier | Implied Real Return |
| --- | --- | --- |
| A | 2.0 | ~7.2% |
| B | 1.3 | ~2.7% |
| C | 1.3 | ~2.7% |
| D | 1.3 | ~2.7% |
| E | 1.2 | ~1.8% |
| F | 2.0 | ~7.2% |

Weighted target (A=7%/B=42%/C=42%/D=3%/E=3%/F=3%) = 1.366x. Required ~3.2%. STRUCTURAL GAP: max achievable EV ~2.65% - unfeasible without commodity-linked. Accepted and documented.

### 4.3 Roth IRA Target Multipliers (15-year horizon)

Floor: 1.3x (revised Apr 23 from 2.0x). Restore to 2.0x when commodity-linked added post-war.

| Scenario | Multiplier |
| --- | --- |
| A | 3.1 |
| B | 1.3 |
| C | 1.3 |
| D | 1.6 |
| E | 1.4 |
| F | 3.1 |

Weighted multiplier = 1.496x. Required ~2.8%.

### 4.4 Structural Floor and Concentration Parameters

| Parameter | Value | Type |
| --- | --- | --- |
| Base floor | 0.25 | Calibration-dated |
| Minimum floor | 2% of account | Calibration-dated |
| Concentration cap | 40% | Calibration-dated |
| Floor nominal loss probability threshold | 15% | Calibration-dated |

---

## Section 5 - Review Cadence

| Date | Type | Scope |
| --- | --- | --- |
| 2026-06-30 | Q2 first full audit | All calibration-dated thresholds; section 4 return table and multipliers; M14/M10/M15 thresholds; restore multipliers if commodity-linked added; AIPO ThematicETF_ClassificationAudit (REQUIRED - provisional); AIPO/PAVE ETN overlap check; MOVE index integration assessment; MAGS vs AGIX reassessment if Anthropic IPO announced; secular_technology_growth empirical validation |
| 2026-09-30 | Q3 | Full audit all calibration-dated thresholds |
| 2026-12-31 | Q4 | Full audit |
| 2027-03-31 | Q1 2027 | Full audit |

---

## Section 6 - First-Audit Checklist (June 30, 2026)

1. Compute trailing 180d median for FRED BAMLH0A0HYM2, BAMLC0A0CM, BAMLH0A3HYC.
2. Compute 10th/25th/75th/90th percentiles for each series.
3. Verify HY_STRESS_DELTA (+150) in 75th-90th percentile band. Adjust if needed.
4. Verify HY_RECESSION_DELTA (+300) in 75th-90th percentile band. Adjust if needed.
5. Verify IG_TRANSMISSION_DELTA (+60) in 75th-90th percentile band. Adjust if needed.
6. Hit-rate audit section 2 thresholds against trailing 5-year data.
7. Formally classify unflagged thresholds in sections 2.2, 2.3, 2.4.
8. Empirical audit section 4.1 return table - all roles including secular_technology_growth. Incorporate FOMC/GDP/CPI data post-April 30. Validate secular_tech B/C and precious_metals C revisions.
9. Empirical audit 4.2/4.3 multipliers. Assess if commodity-linked added; if so restore B/C and floors (IRA 1.5x, Roth 2.0x). Reassess structural IRA gap.
10. Audit 4.4 floor/concentration parameters.
11. First audit section 9 M14 thresholds (divergence, underweight, entry extension).
12. First audit section 10 M08 ETF classification thresholds.
13. XAR: re-verify at Q2 (standard staleness check; composition drift).
14. First audit section 11 classification weights - all instruments including AIPO and MAGS. Flag weight drift >5pp.
15. AIPO ThematicETF_ClassificationAudit() - REQUIRED (provisional classification). Confirm real_asset_contracted_revenue (0.55) weight. Check ETN concentration vs PAVE.
16. MAGS vs AGIX: reassess if Anthropic IPO announced or completed. AGIX holds ~2.98% Anthropic direct. Evaluate upgrade at Q3 or earlier on IPO announcement.
17. Review section 11 role registry for new structural drivers warranting new roles.
18. MOVE index: assess formal integration into M11/M14 as supplementary credit/volatility signal.
19. Add Fed response function sub-variable to Scenario C scoring (design proposal Apr 29).
20. Record all results in section 3 calibration log.

---

## Section 7 - Session Observations Log (Credit Readings)

| Date | HY OAS (bps) | IG OAS (bps) | CCC OAS (bps) | Source | T1 Flag |
| --- | --- | --- | --- | --- | --- |
| 2026-04-19 | 285 | 83 | 921 | Trading Economics / FRED | composite_only |
| 2026-04-21 | 285 | 83 | 921 | Trading Economics / FRED (stale Apr 15-16) | stale |
| 2026-04-22 | 287 | 83 | 921 | Trading Economics / FRED (HY Apr 20; IG/CCC Apr 16-17) | stale |
| 2026-04-23 | 287 | 83 | 921 | Trading Economics / FRED (stale 3-7 days) | stale |
| 2026-04-28 | 285 | 83 | 921 | Trading Economics / FRED (stale 7-12 days) | stale |
| 2026-04-29 | 284 | 80 | 921 | Trading Economics proxy; FRED HY Apr 28; IG T2 cross-ref (~80 bps near 25yr tights); CCC carry | stale (IG: composite_only) |
| 2026-04-30 (ad-hoc) | - | - | - | No credit fetch - ad-hoc session | n/a |
| 2026-04-30 (full) | 284 (carry) | 80 (carry) | 921 (carry) | Carry from Apr 29. MOVE FIRST LOGGED: 68.68 (Investing.com T2; 52-wk range 55.77-115.02; bond market calm; no fixed income stress) | stale; MOVE T2 |

---

## Section 8 - Session State Log

date: 2026-04-21
scenario_probabilities: { A: 7%, B: 44%, C: 36%, D: 3%, E: 7%, F: 3% }
primary_driver: Strait of Hormuz Crisis / US-Iran War (Day 52)
derivation_method: scored
open_decisions: SUPERSEDED by April 30 full session

---

date: 2026-04-22
scenario_probabilities: { A: 8%, B: 45%, C: 38%, D: 3%, E: 3%, F: 3% }
primary_driver: Strait of Hormuz Crisis / US-Iran War (Day 53)
derivation_method: scored
open_decisions: SUPERSEDED by April 30 full session

---

date: 2026-04-23
scenario_probabilities: { A: 8%, B: 45%, C: 38%, D: 3%, E: 3%, F: 3% }
primary_driver: Strait of Hormuz Crisis / US-Iran War (Day 55+)
derivation_method: scored
open_decisions: SUPERSEDED by April 30 full session

---

date: 2026-04-28
scenario_probabilities: { A: 8%, B: 45%, C: 38%, D: 3%, E: 3%, F: 3% }
primary_driver: Strait of Hormuz Crisis / US-Iran War (Day 59)
derivation_method: scored
open_decisions: SUPERSEDED by April 30 full session

---

date: 2026-04-29
scenario_probabilities: { A: 8%, B: 45%, C: 38%, D: 3%, E: 3%, F: 3% }
primary_driver: Strait of Hormuz Crisis / US-Iran War (Day 60)
derivation_method: scored
open_decisions: SUPERSEDED by April 30 full session

---

date: 2026-04-30
scenario_probabilities: { A: 7%, B: 42%, C: 42%, D: 3%, E: 3%, F: 3% }
primary_driver: Strait of Hormuz Crisis / US-Iran War (Day 61) - no ceasefire; diplomatic track stalled; Brent C-trigger clock Day 2 active
derivation_method: scored
manual_override_reason: null
session_type: full M05 (Allocation sheet fetched via Google Drive MCP; Calibration State fetched via GitHub MCP; credit carry-forward; MOVE first logged)

open_triggers:
- Brent $110 C-trigger clock: Day 2 of 10 active (Day 1=Apr 29 close $110.44; Day 2=Apr 30 $110.73). Clock fires ~May 13 if sustained. Monitor every session without exception.
- CPI May 10-12: second print. If >=3.5% YoY -> C check_cpi to 2; C probability rises.
- IIJA reauthorization September 30, 2026 (PAVE watch status trigger)
- Warsh confirmation expected - monitor E probability
- XAR 180-share staged sell at $265 in Taxable Acc4: XAR closed $266.59 Apr 30 - order likely executed. Client to verify at broker.

open_decisions:
- Client reviewing M13 target allocations. Will update allocation file with approved targets and execute trades.
- VTI: wash sale window cleared April 30. VTI purchase CANCELLED - capital redirected to AIPO/MAGS.
- AIPO and MAGS: new positions pending client approval and allocation file update.
- Taxable Acc4 XAR: 180-share staged sell at $265 may have executed (verify). Remaining XAR reduction to 12% structural target pending.
- PAVE: hold at ~11% in Taxable Acc4 (watch status).
- AIPO section 11 classification: provisional - ThematicETF_ClassificationAudit() required at Q2 June 30 audit.

M13 target allocations (for client allocation file update):
- Primary IRA:   MLPX 40% | SGOL 33% | XAR 12% | AIPO 8% | MAGS 7% | VTI 0%
- Primary Roth:  MLPX 40% | SGOL 33% | XAR 12% | AIPO 8% | MAGS 7% | VTI 0%
- Taxable Acc3:  SGOV 100% (no change)
- Taxable Acc4:  MLPX 40% | SGOV 29% | XAR 12% | AIPO 8% | PAVE 11% | MAGS 0% (swap tax-inefficient) | VTI 0%
- Relative IRA:  MLPX 35% | SGOL 37% | SGOV 20% | AIPO 5% | MAGS 3% | VTI 0%
- Relative Roth: MLPX 40% | SGOL 40% | AIPO 12% | MAGS 8% | VTI 0%

next_session_flags:
- CONFIRM: Did XAR $265 staged sell execute in Taxable Acc4? Verify at broker. If yes, proceed with remaining Taxable Acc4 rebalancing.
- Brent clock: Day 2 - update daily. Clock fires Day 10 (~May 13). EV ranking shifts materially if C fires (C probability rises further, changes idealAllocation() across all accounts).
- CPI May 10-12: BINARY for C check_cpi. If >=3.5% -> C check_cpi upgrades to 2.
- M14 composite divergence HIGH - MLPX underweight review active for Relative IRA (-8.5pp) and Relative Roth (-16.87pp). EntryExtensionGuard passes for MLPX. Pending allocation file update.
- FRED credit spreads stale - fetch fresh next session.
- B and C co-equal at 42% - first occurrence this series - monitor for further divergence.
- Primary IRA structural gap: achievable EV ~2.65% vs required 3.2% - accepted, documented.
- MOVE index: 68.68 (calm) - update each session going forward.
- GitHub write-back FAILED this session (content size limit). Retry at next session using branch+PR workflow. This manual paste is the authoritative write for v1.9.
- MAGS vs AGIX: monitor Anthropic IPO news (targeting Oct 2026 at ~$60B). AGIX (AUM $171.5M, expense 0.99%) holds ~2.98% Anthropic direct. Evaluate MAGS->AGIX upgrade if IPO imminent. Assess at Q3 audit or earlier on announcement.

---

## Section 9 - Market Regime Thresholds (M14)

All values CALIBRATION_DATED. First audit: June 30, 2026.

### 9.1 Divergence Signal Thresholds

| Parameter | Current Value | Type |
| --- | --- | --- |
| commodity_fear_divergence HIGH | energy_90d >= +15% AND VIX_change_90d_pts <= 0 | Calibration-dated |
| commodity_fear_divergence MODERATE | energy_90d >= +10% AND VIX_change_90d_pts <= +5 pts | Calibration-dated |
| equity_scenario_divergence HIGH | broad_equity_30d >= +5% while directive reductive | Calibration-dated |
| equity_scenario_divergence MODERATE | broad_equity_30d >= +2% while directive reductive | Calibration-dated |

### 9.2 Underweight Review Trigger

| Parameter | Current Value | Type |
| --- | --- | --- |
| underweight_gap_trigger | 5 pp | Calibration-dated |
| appreciation_trigger_30d | 5% | Calibration-dated |

### 9.3 Entry Extension Guard Thresholds

| Role | Threshold | Notes |
| --- | --- | --- |
| broad_market_equity | 15% | Provisional |
| thematic_sector_equity | 20% | policy_driven_thematic_equity, geopolitical_premium |
| commodity_linked | 20% | WAR PREMIUM ENTRY GUARD also applies independently |
| inflation_hedge_precious_metals | 20% | Provisional |
| real_asset_contracted_revenue | 15% | Provisional |
| secular_technology_growth | 20% | Added v1.7 Apr 28 |
| rate_sensitive_income_short | N/A | Guard does not apply |
| rate_sensitive_income_long | N/A | Duration risk captured by scenario framework |

---

## Section 10 - M08 Thematic ETF Classification Parameters

All values CALIBRATION_DATED. First audit: June 30, 2026.

### 10.1 Classification Audit Parameters

| Parameter | Current Value |
| --- | --- |
| minimum_nav_coverage | 60% |
| mandate_exposure_materiality_threshold | 30% |

### 10.2 Mandate Impairment Propagation Parameters

| Parameter | Current Value |
| --- | --- |
| program_rescission_materiality | 20% |
| constituent_revenue_materiality | 5% |

### 10.3 Application Log

| Date | ETF | Audit Type | Finding | Outcome |
| --- | --- | --- | --- | --- |
| 2026-04-28 | PAVE | MandateImpairmentPropagation | NEVI rescission maps to Quanta EV segment. NAV at risk ~10-15%. Below 20% threshold. | watch (not FLAGGED) |
| 2026-04-28 | PAVE | ThematicETF_ClassificationAudit | Mandate-dependent NAV ~15-18%. Below 30% threshold. Dominant driver: industrial/capital goods. | watch; monitor |
| 2026-04-29 | XAR | ThematicETF_ClassificationAudit | ~65% NAV covered. Mandate-dependent ~75-80%. geopolitical_premium confirmed. | CONFIRMED: 90% geopolitical_premium / 10% broad_market |
| 2026-06-30 | AIPO | ThematicETF_ClassificationAudit | PENDING - provisional Apr 30. Full audit required Q2. Check ETN/Eaton concentration vs PAVE. | PROVISIONAL: see section 11 |

---

## Section 11 - Instrument Classification Registry (M15)

All values CALIBRATION_DATED. First audit: June 30, 2026.
VTI, XAR, MLPX, SGOL, SGOV, PAVE added Apr 28 (v1.7). AIPO, MAGS added Apr 30 (v1.9).

### 11.1 Role Registry

| Role | Binding Driver | Added | Status |
| --- | --- | --- | --- |
| geopolitical_premium | elevated_conflict, defense_procurement, geopolitical_tension | v1.0 | Active |
| inflation_hedge_precious_metals | real_yield_compression, monetary_base_expansion, dollar_reserve_status_erosion | v1.0 | Active |
| inflation_hedge_commodity_linked | broad_commodity_prices, energy, materials | v1.0 | Active |
| real_asset_contracted_revenue | physical_throughput, contracted_fees, real_infrastructure | v1.0 | Active |
| policy_driven_thematic_equity | legislated_government_spending, regulatory_mandates, domestic_policy_cycle | v1.0 | Active |
| rate_sensitive_income_short_duration | short_term_interest_rates, duration <= 1y | v1.0 | Active |
| rate_sensitive_income_long_duration | long_term_interest_rates, duration > 1y | v1.0 | Active |
| broad_market_equity_domestic | domestic_aggregate_economic_growth | v1.0 | Active |
| broad_market_equity_international | ex_US_aggregate_economic_growth | v1.0 | Active |
| secular_technology_growth | AI_capex_cycle, mega-cap_tech_multiple_expansion, software_adoption, semiconductor_demand | v1.7 Apr 28 | Active - provisional, empirical audit June 30 |

### 11.2 secular_technology_growth - Return Estimates

Provisional. Added Apr 28. B and C revised Apr 30 (v1.8). Full empirical audit June 30, 2026.

| Scenario | Conservative | Upside | Rationale |
| --- | --- | --- | --- |
| A | 6% | 16% | Fed cuts; AI capex expands; multiple expansion |
| B | -6% | -1% | REVISED Apr 30. Multiple compression under elevated rates, partially offset by AI earnings growth (AMZN $2.78 vs $1.64 est; MSFT beat; Azure +40%). Less severe than 2022 zero-AI-revenue analog. |
| C | +2% | +8% | REVISED Apr 30. Q1 2026 empirical: Azure +40%, AWS +28%, META +33%, GOOGL beat during active Scenario C. AI enterprise contracts multi-year; weak conflict transmission to AI capex cycle. |
| D | -14% | -5% | Capex collapse in demand destruction; severe multiple contraction |
| E | -10% | -4% | Growth multiples collapse in systemic stress |
| F | 4% | 11% | Strong nominal demand supports AI capex; rising rates partially compress multiples |

### 11.3 Instrument Classification Table

#### VTI
- Components: broad_market_equity_domestic (0.78) + secular_technology_growth (0.22)
- Last reviewed: 2026-04-28
- NOTE: VTI ELIMINATED from all target allocations as of April 30, 2026 (v1.9). Existing positions to be sold during rebalancing. Section 11 entry retained for blendedScenarioReturn() computation during transition period.

#### XAR
- Components: geopolitical_premium (0.90) + broad_market_equity_domestic (0.10)
- ThematicETF_ClassificationAudit COMPLETED April 29. Confirmed.
- Last reviewed: 2026-04-29
- EV: +1.58%. Target: 12% structural across applicable accounts (Primary IRA, Primary Roth, Taxable Acc4).
- Client preference: exit excess XAR at ~$265 spike. 180-share staged sell in Taxable Acc4 at $265 limit - may have executed Apr 30 (XAR closed $266.59). Verify at broker.
- HoldJustification: break-even peace probability <5.6%; opportunity cost vs MLPX -2.33%/year.

#### MLPX
- Components: real_asset_contracted_revenue (0.65) + inflation_hedge_commodity_linked (0.35)
- Last reviewed: 2026-04-28
- EV: +3.83% (#1 ranked instrument). Target allocation increased across all accounts in M13 rerun.

#### SGOL
- Components: inflation_hedge_precious_metals (1.00)
- Last reviewed: 2026-04-28
- CALIBRATION ANOMALY RESOLVED Apr 30 (v1.8): section 4.1 Scenario C return revised [+7%,+14%]->[-2%,+6%]. C-hawk regime empirical basis: gold down ~18% from Jan ATH during active Scenario C; Fed holding rates elevated; real yields at +1.89%; gold underperforms vs short-duration income. Revised blended EV: +1.83% (was +5.51%). SGOL targets decreased in M13 rerun.

#### SGOV
- Components: rate_sensitive_income_short_duration (1.00)
- Last reviewed: 2026-04-28
- EV: +0.81%. Preservation account (Taxable Acc3) = 100% SGOV. Taxable Acc4 SGOV target increased to 29% in M13 rerun (XAR reduction proceeds).

#### PAVE
- Components: broad_market_equity_domestic (0.82) + policy_driven_thematic_equity (0.18)
- ThematicETF_ClassificationAudit conducted Apr 28. Status: watch (not FLAGGED).
- Last reviewed: 2026-04-28
- Cost basis: $54.09/share (~$1,286 embedded gain on 590 shares). Target: ~11% in Taxable Acc4.
- Monitor IIJA reauthorization September 30, 2026.
- OVERLAP: Eaton Corp (ETN) in both PAVE (~3.4% NAV) and AIPO (~8.1% NAV). Monitor combined concentration at Q2 audit.

#### AIPO
- Components: real_asset_contracted_revenue (0.55) + secular_technology_growth (0.20) + broad_market_equity_domestic (0.15) + inflation_hedge_commodity_linked (0.10)
- Basis: Defiance AI & Power Infrastructure ETF. Tracks MarketVector U.S. Listed AI and Power Infrastructure Index. Sector weights (12/23/2025): Industrials 56.4%, IT 18.5%, Utilities 15.9%, Energy 7.6%. Top holdings (03/31/2026): GEV 8.9%, ETN 8.1%, PWR 7.7%, VRT 7.7%, Cameco 4.3%, BE 4.2%, AVGO 4.1%, NVDA 4.0%. Dominant driver: power and grid infrastructure for AI data centers, not AI companies directly.
- Source: Schwab report card 04/30/2026; sector weights as of 12/23/2025
- Methodology: sector_weight_analysis + judgment. ThematicETF_ClassificationAudit() REQUIRED at Q2 June 30 - PROVISIONAL classification.
- Last reviewed: 2026-04-30
- Price at adoption: $31.28. EntryExtensionGuard: ~+9.8% above 90d avg vs 15% threshold for real_asset_contracted_revenue - PASSES.
- AUM: $249.5M. Expense ratio: 0.69%. Inception: 07/24/2025 (thin track record - flag at Q2).
- EV (A=7/B=42/C=42): +1.03%. Only AI-sector instrument with positive EV under current regime.
- TAX PLACEMENT: ALL ACCOUNTS including taxable (standard ETF structure - no swap, no phantom gains).
- PAVE overlap: ETN in both AIPO (~8.1%) and PAVE (~3.4%). Audit at Q2 June 30.

#### MAGS
- Components: secular_technology_growth (0.85) + broad_market_equity_domestic (0.15)
- Basis: Roundhill Magnificent Seven ETF. Equal-weight AAPL/MSFT/GOOGL/AMZN/META/NVDA/TSLA via total return swap structure (T-bills as collateral + equity swaps). Top holdings (03/31/2026): T-bills 41.86%, AMZN 6.13%, NVDA 6.04%, META 5.81%, MSFT 5.70%, GOOGL swap 5.29%, AAPL 5.26%. 15% broad_market weight reflects TSLA and AAPL hardware/consumer component.
- Source: Schwab report card 04/30/2026; holdings as of 03/31/2026
- Methodology: holdings_analysis + judgment
- Last reviewed: 2026-04-30
- Price at adoption: $66.24. EntryExtensionGuard: fund down 12.2% over 3 months; current price well below 90d trailing avg (~$75) - PASSES easily.
- AUM: $3.5B. Expense ratio: 0.29% (lowest of all AI-sector candidates). Inception: 04/10/2023.
- EV (A=7/B=42/C=42): -2.34%. NEGATIVE EV - documented client judgment override. Rationale accepted: AI/Mag7 earnings momentum thesis (Q1 2026: MSFT +18%, Azure +40%, META +33%, AMZN AWS +28%); optionality on future scenario probability shift toward A/F; cheapest and most liquid pure secular-tech instrument available.
- TAX PLACEMENT: RETIREMENT ACCOUNTS ONLY (IRA and Roth accounts). Swap structure generates phantom taxable gains in losing years - confirmed by Schwab prospectus tax analysis page (Load Adjusted YTD +37.1% vs market return -12.2% in same period). Do NOT hold in Taxable Acc4 or any taxable account.
- COUNTERPARTY RISK: does not directly hold Mag7 shares - uses total return swaps. Counterparty default risk exists. Does not vote underlying shares.
- No Anthropic or SpaceX exposure. Pure public-market Mag7 bet.
- MAGS vs AGIX upgrade evaluation: AGIX (AUM $171.5M, expense 0.99%) holds Anthropic ~2.98% direct (cap-table position, confirmed in top 10 holdings). Anthropic targeting IPO Oct 2026 at ~$60B valuation. If IPO announced/imminent, evaluate MAGS->AGIX upgrade. Assess at Q3 2026 audit or earlier on announcement. AGIX EntryExtensionGuard would need to be rechecked at time of evaluation (currently near 52-week high $40.01).