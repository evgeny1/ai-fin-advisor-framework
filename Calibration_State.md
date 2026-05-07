# Calibration State

Persistent framework configuration — load at every session start alongside Session Log.

Version: 1.12  Last updated: May 6, 2026 (architecture session: file split implemented — §7 and §8 moved to Session_Log.md; Calibration_Log.md created for §3 archive; M16_ReturnTableCalibration.md authored; §3 trimmed to last 10 entries; roles inflation_linked_sovereign and real_estate_equity_income added to §11.1 and §4.1 as LOW-confidence placeholders pending June 30 empirical audit.)  Next scheduled review: June 30, 2026 (Q2 2026 quarter-end)

**File split as of v1.12:**
- Session observations (§7) and session state (§8) now live in **Session_Log.md** (fetched concurrently at session start).
- Prior calibration history before last-10 entries lives in **Calibration_Log.md**.
- This file (Calibration_State.md) is the LIVE CONFIG — kept lean for reliable write-back.

---

## Load Verification Requirement

At session start, after both files are fetched, the advisor must state in the briefing:

"Calibration State loaded, last update: May 6, 2026 | Session Log loaded"

Absence of either confirmation line indicates the respective file was not loaded and the session is invalid for threshold-sensitive decisions.

After loading: run M15.ValidateClassifications() — all instruments in the allocation file must have §11 entries before session proceeds to analysis.

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
Session observation (May 6 full session): HY ~284 bps (carry forward). FRED fetch attempted — metadata only; no live values. No threshold fires. T1_flag: stale.

### 1.2 IG Composite - FRED: BAMLC0A0CM

| Parameter | Current Value | Type | Notes |
| --- | --- | --- | --- |
| IG_TRANSMISSION_DELTA | +60 bps | Calibration-dated | Provisional initial - full audit pending June 30, 2026 |
| Velocity overlay | +40 bps over prior 60 days | Fixed structural | Not calibration-dated |
| Sustain period | 10 trading days | Fixed structural | Not calibration-dated |

Session observation (April 19): IG ~83 bps. Baseline reference.
Session observation (April 21-29): IG ~80-83 bps. Carry forward. IG_TransmissionReached NOT fired (threshold ~143 bps; gap ~60-63 bps). Stale.
Session observation (April 30 full session): IG ~80 bps (carry). NOT fired. T1_flag: stale.
Session observation (May 6 full session): IG ~80 bps (carry). NOT fired. T1_flag: stale.

### 1.3 CCC Tail - FRED: BAMLH0A3HYC

| Parameter | Current Value | Type | Notes |
| --- | --- | --- | --- |
| Ratio divergence | CCC widens 3x composite over 30d | Fixed structural | Not calibration-dated |
| Absolute divergence floor | CCC +200 bps while composite +<50 bps over 30d | Calibration-dated | Provisional - audit pending June 30, 2026 |

First divergence computation (April 19): CCC Apr 16 = 921 bps vs Mar 16 = 973 bps = -52 bps tightening. Neither threshold fired.
Session observations (April 21-30): CCC ~921 bps (carry forward; FRED stale). CCC_TailFirstWidening NOT fired. T1_flag: stale.
Session observation (May 6 full session): CCC ~921 bps (carry). NOT fired. T1_flag: stale.

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
- May 1 (ad-hoc bridge): Day 3 = May 1 $116.10. Clock active. Fujairah oil hub fire; IRGC declared Hormuz zones under Iranian military control. Escalation confirmed T1.
- May 4 (ad-hoc bridge): Day 4 = May 4 $114.06-$115.01. Clock active. US-Iran direct naval exchange confirmed. UAE attacked.
- May 6 full session: BRENT C-TRIGGER CLOCK BROKEN. Day 5 = May 5 close ~$109.87 (CNBC T1 — international benchmark Brent futures fell ~4% to close at $109.87). Below $110 nominal threshold. Clock resets to Day 0. 4 consecutive days achieved (Apr 29-May 4); 10 required; not met. New 10-day clock requires fresh initiation above $110. May 6: Brent declining further on US-Iran deal reports (~$102 intraday; WTI down 12%+). SGOL WTI floor: WTI ~$89-93, comfortably above $55 floor. SGOL invalidation NOT triggered.

### 2.2 Currency

| Threshold | Current Value | Audit Status |
| --- | --- | --- |
| DXY sustained above - SGOL invalidation | 105 nominal | Pending June 30 |

DXY ~98.42-98.46 (StreetStats T2, May 4-5). Well below 105. No SGOL invalidation risk.

### 2.3 Macro

| Threshold | Current Value | Audit Status |
| --- | --- | --- |
| CPI trigger - Scenario B | 4% YoY, 3+ consecutive prints | Pending June 30 |
| CPI invalidation - Scenario B | below 3% YoY, 2+ consecutive prints | Pending June 30 |
| GDP trigger - Scenario F | above 3% annualized, 2+ consecutive quarters | Pending June 30 |
| GDP invalidation - Scenario F | below 2% on BEA advance estimate | Pending June 30 |
| Unemployment trigger - Scenario D | +0.5% over any 3-month window | Pending June 30 |

April 30 full session: Q1 2026 GDP advance estimate = +2.0% annualized (BEA T1). Above 1.5% threshold - B check_gdp drops to 1. D watch NOT triggered. Core PCE 3.2% YoY (BEA T1). FOMC: hold at 3.5-3.75%. Language upgraded: inflation is elevated. 4 dissents (3 hawkish, 1 dovish/Miran). C-hawk regime confirmed. Next CPI May 10-12 (second print - watch for >=3.5% -> C check_cpi to 2).

May 6 full session: No new macro data releases. CPI print expected May 10-12. US-Iran deal framework reported (Axios/CBS/NPR T1) but not confirmed. Trump paused "Project Freedom"; Iran reviewing latest US proposal. Deal unconfirmed as of session close. Sahm Rule 0.20 (stable). No new unemployment or GDP data.

Prior context: CPI March 3.3% YoY (1 of 3 for B trigger). Q4 2025 GDP 0.5%. Consumer sentiment 49.8 (record low). 10Y breakeven ~2.43%. Sahm Rule 0.20. Mag7 Q1 earnings all beat; zero guidance withdrawals. Azure +40%, AWS +28%, META +33%, GOOGL beat, AMZN EPS $2.78 vs $1.64 est. MSFT +18% YoY.

### 2.4 Instrument Evaluation

| Threshold | Current Value | Audit Status |
| --- | --- | --- |
| Foreign concentration disqualification | 40% single-country/single-region | Pending June 30 |
| AUM disqualification | $100M minimum | Pending June 30 |

---

## Section 3 - Calibration Log (last 10 entries; prior entries in Calibration_Log.md)

2026-04-23 - Framework update (v1.3): M13 adoption, section 4 added, GitHub migration.

2026-04-23 - M13 first application (v1.4). IRA B/C multipliers 1.5x->1.3x. Roth B/C multipliers 2.0x->1.3x. Initial M13 targets computed (superseded by April 30 rerun).

2026-04-27 - Framework update (v1.5): M14 adoption, section 9 added.

2026-04-28 - PAVE reclassification + M08 update (v1.6). PAVE status: watch (not FLAGGED). PAVE cost basis $54.09/share (~$1,286 embedded gain on 590 shares). Section 10 added.

2026-04-28 - Framework update (v1.7): M15 adoption, section 11 added, secular_technology_growth role added. Initial instrument classifications: VTI, XAR, MLPX, SGOL, SGOV, PAVE.

2026-04-29 - Session write-back. XAR ThematicETF_ClassificationAudit COMPLETED (confirmed: 90% geopolitical_premium / 10% broad_market). Calibration proposals documented as pending. M14 divergence HIGH. UnderweightReviewTrigger fired for Relative accounts (MLPX -8.5pp IRA, -16.87pp Roth). Probabilities unchanged A=8/B=45/C=38.

2026-04-30 - Calibration proposals adopted (v1.8). secular_technology_growth B: [-10%,-3%]->[-6%,-1%]. secular_technology_growth C: [-2%,+4%]->[+2%,+8%]. inflation_hedge_precious_metals C: [+7%,+14%]->[-2%,+6%]. XAR HoldJustification: break-even peace prob <5.6%; opportunity cost vs MLPX -2.33%/year. M13 structural gap: Primary IRA max achievable EV ~2.65% vs required 3.2%.

2026-04-30 - Full M05 session: M13 rerun, AIPO+MAGS adopted, VTI eliminated (v1.9). Session type: full M05. Allocation sheet fetched (Google Drive MCP). Calibration State fetched (GitHub MCP). MOVE index first logged. Credit carry-forward. FOMC hold 3.5-3.75%. Q1 GDP +2.0%. Brent C-trigger clock Day 2. Scenario probabilities: A=7/B=42/C=42/D=3/E=3/F=3.

2026-05-06 - Full M05 session (v1.10). C-trigger clock broken Day 5 (May 5 close ~$109.87, CNBC T1). Scenario probabilities updated: A=15%(+8pp), B=36%(-6pp), C=36%(-6pp), D=3%(unch), E=3%(unch), F=7%(+4pp). AIPO §11 updated: AUM $457M. PAVE watch status confirmed. MLPX EntryExtensionGuard blocking. M14 composite divergence: MODERATE.

2026-05-06 - Returns table empirical overhaul initiated (v1.11). Full methodology framework documented. Historical scenario-to-analogue mapping established. ADOPTED: real_asset_contracted_revenue B [3,7]→[6,14] and C [3,6]→[8,16]. Empirical basis: AMZI total return 2022 +31.4% nominal. MLPX §11 EV updated: +3.64%→+5.51%. Fourteen additional revision proposals logged in §6 item 23.

2026-05-06 - Architecture session (v1.12). File split implemented: §7 and §8 moved to Session_Log.md; §3 entries 1-4 archived to Calibration_Log.md. M16_ReturnTableCalibration.md authored (governs §4.1 revision methodology). M12, M05, 00_INDEX updated for two-file session protocol. New roles added to §11.1 and §4.1: inflation_linked_sovereign and real_estate_equity_income (LOW confidence, [TBD] values, pending June 30 empirical audit). No portfolio analysis this session.

---

## Section 4 - Growth Objectives: Return Table and Multipliers

All values CALIBRATION_DATED. Last calibrated: May 6, 2026 (v1.11 — real_asset_contracted_revenue B/C). Full empirical audit: June 30, 2026.

CALIBRATION PROPOSALS ADOPTED April 30, 2026:
- secular_technology_growth Scenario C: [-2%,+4%]->[+2%,+8%]
- secular_technology_growth Scenario B: [-10%,-3%]->[-6%,-1%]
- inflation_hedge_precious_metals Scenario C: [+7%,+14%]->[-2%,+6%]
Post-adoption check: review if May 10-12 CPI surprises (>=4.0% or <=2.5%).

CALIBRATION PROPOSALS ADOPTED May 6, 2026 (v1.11):
- real_asset_contracted_revenue Scenario B: [3,7]→[6,14]. Empirical basis: AMZI 2022 +31.4% nominal total return in confirmed B/C environment; four consecutive years 2021-2024 of 20%+ nominal gains. Conservative [6%] anchored to ~+19% real in 2022.
- real_asset_contracted_revenue Scenario C: [3,6]→[8,16]. Same empirical basis; C (acute inflationary shock) is the strongest environment for contracted energy revenue. Prior [3%] conservative was understated by >2x.
- NOTE: real_asset_contracted_revenue D and E remain at prior values [2,6] and [2,5] pending June 30 audit. Proposed revisions D→[-10,-2] and E→[-8,0] are logged in §6 item 23.

### 4.1 Expected Real Annualized Return Table

Conservative end used for ALL computations. Upside end disclosed in briefing only.
All scenario return computations use M15.blendedScenarioReturn() — this table is consumed via that function, never directly.
All §4.1 revisions must follow M16.CalibrationMethodology() 4-layer procedure before adoption.
Historical scenario analogues: A=1991/2003/2016 normalization; B=1973-1982/2022 stagflation; C=1974/1979-80/2022 H1 shock; D=2008-09/2020 COVID; E=2008 acute systemic/1998 LTCM; F=1995-2000/2017-2019/2023-2024 growth.
Institutional unconditional anchors (real, 10yr, neutral distribution): broad_market ~1-4% (JPM 4.2%, Vanguard 1-3%, RA 0.6%, GMO -6%); gold ~3% (JPM 5.5% nom); infrastructure ~4-5% (JPM 6.5-7.1% nom); commodities ~1.6-2.1% (JPM 4.1-4.6% nom); short_duration ~1.5-2%. Conditional scenario returns are not required to match unconditional estimates — the unconditional is the scenario-probability-weighted average under a neutral distribution (approx A=35/B=15/C=15/D=10/E=5/F=20), not the current crisis distribution.

| Role | Scenario A | Scenario B | Scenario C | Scenario D | Scenario E | Scenario F |
| --- | --- | --- | --- | --- | --- | --- |
| geopolitical_premium | [-2, 3] | [2, 6] | [4, 10] | [-4, 0] | [1, 5] | [1, 4] |
| inflation_hedge_precious_metals | [0, 4] | [6, 12] | [-2, 6] | [-2, 4] | [10, 20] | [-3, 1] |
| inflation_hedge_commodity_linked | [2, 6] | [6, 12] | [7, 13] | [-8, -2] | [2, 6] | [2, 5] |
| real_asset_contracted_revenue | [3, 7] | [6, 14] | [8, 16] | [2, 6] | [2, 5] | [3, 7] |
| policy_driven_thematic_equity | [4, 8] | [-3, 1] | [-1, 3] | [-5, -1] | [-6, -2] | [4, 8] |
| rate_sensitive_income_short_duration | [0, 2] | [1, 3] | [1, 3] | [0, 3] | [-2, 2] | [1, 3] |
| rate_sensitive_income_long_duration | [3, 7] | [-4, -1] | [-5, -2] | [5, 10] | [-10, -3] | [-4, -1] |
| broad_market_equity_domestic | [5, 12] | [-8, -2] | [-4, -1] | [-12, -4] | [-8, -3] | [7, 14] |
| broad_market_equity_international | [4, 9] | [-5, -1] | [-6, -2] | [-8, -3] | [-10, -4] | [3, 8] |
| secular_technology_growth | [6, 16] | [-6, -1] | [+2, +8] | [-14, -5] | [-10, -4] | [4, 11] |
| inflation_linked_sovereign | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] |
| real_estate_equity_income | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] |

secular_technology_growth: added v1.7 Apr 28. B and C values revised v1.8 Apr 30. Provisional - empirical audit June 30, 2026.
inflation_hedge_precious_metals Scenario C: revised v1.8 Apr 30 (C-hawk regime empirical data).
real_asset_contracted_revenue B and C: revised v1.11 May 6 (AMZI 2021-2024 empirical data). D and E pending June 30.
inflation_linked_sovereign: added v1.12 May 6. LOW confidence. [TBD] values pending June 30 empirical audit (M16.CalibrationMethodology() required). Proxy: CPI-adjusted T-bill returns for pre-TIPS periods.
real_estate_equity_income: added v1.12 May 6. LOW confidence. [TBD] values pending June 30 empirical audit (M16.CalibrationMethodology() required). Historical basis available: 1973-1982 REIT/property real return ~+4.5%/yr (Morningstar/CAIA); JP Morgan LTCMA 2026: U.S. core real estate 8.2% nominal (~5.7% real).
⚠ 14 additional revision proposals pending June 30 formal adoption — see §6 item 23.

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

Weighted target (A=15%/B=36%/C=36%/D=3%/E=3%/F=7%) = 1.454x. Required ~3.2%. STRUCTURAL GAP: max achievable EV ~2.65% under prior table — gap narrowing with v1.11 MLPX EV revision to +5.51%. Revised feasibility check required at next M05 session with updated blendedScenarioReturn() outputs.

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

Weighted multiplier (A=15/B=36/C=36/D=3/E=3/F=7) = 1.599x. Required ~2.8%.

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
| 2026-06-30 | Q2 first full audit | All calibration-dated thresholds; section 4 return table and multipliers; M14/M10/M15 thresholds; restore multipliers if commodity-linked added; AIPO ThematicETF_ClassificationAudit (REQUIRED - provisional); AIPO/PAVE ETN overlap check; MOVE index integration assessment; MAGS vs AGIX reassessment if Anthropic IPO announced; secular_technology_growth empirical validation; formal adoption of §6 item 23 pending proposals; populate §4.1 values for inflation_linked_sovereign and real_estate_equity_income (full M16.CalibrationMethodology() 4-layer procedure required) |
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
8. Empirical audit section 4.1 return table — all roles including secular_technology_growth. Incorporate FOMC/GDP/CPI data post-April 30. Validate secular_tech B/C and precious_metals C revisions. Formally adopt or reject §6 item 23 pending proposals with documented M16.CalibrationMethodology() 4-layer procedure (historical analogue citations, institutional cross-reference, confidence-level assignment). Populate [TBD] values for inflation_linked_sovereign and real_estate_equity_income using Layer 2 analogues + Layer 1 anchors; run Layer 4 consistency check before adoption.
9. Empirical audit 4.2/4.3 multipliers. Assess if commodity-linked added; if so restore B/C and floors (IRA 1.5x, Roth 2.0x). Reassess structural IRA gap with updated blendedScenarioReturn() outputs (v1.11 MLPX revision changes achievable EV materially).
10. Audit 4.4 floor/concentration parameters.
11. First audit section 9 M14 thresholds (divergence, underweight, entry extension).
12. First audit section 10 M08 ETF classification thresholds.
13. XAR: re-verify at Q2 (standard staleness check; composition drift).
14. First audit section 11 classification weights — all instruments including AIPO and MAGS. Flag weight drift >5pp.
15. AIPO ThematicETF_ClassificationAudit() — REQUIRED (provisional classification). Confirm real_asset_contracted_revenue (0.55) weight. Check ETN concentration vs PAVE.
16. MAGS vs AGIX: reassess if Anthropic IPO announced or completed. AGIX holds ~2.98% Anthropic direct. Evaluate upgrade at Q3 or earlier on IPO announcement.
17. Review section 11 role registry for new structural drivers warranting new roles.
18. MOVE index: assess formal integration into M11/M14 as supplementary credit/volatility signal.
19. Add Fed response function sub-variable to Scenario C scoring (design proposal Apr 29).
20. Record all results in section 3 calibration log.
21. AIPO Financial Services weight (3.60% as of Apr 30): assess materiality for classification. Flag if above 5% by Q2 audit.
22. MLPX target allocation: reassess if client formally requests reduction from 40% due to volatility profile — document any revision here. Note: MLPX drawdown tolerance analysis (May 6) identified Relative IRA as breaching 20% tolerance at 34% MLPX weight assuming 67% historical max drawdown. Formal target revision pending client decision.
23. RETURNS TABLE PENDING REVISION PROPOSALS (logged May 6, 2026 — formal adoption requires June 30 audit with M16.CalibrationMethodology() 4-layer procedure: historical analogue evidence, institutional unconditional anchor, structural adjustment documentation, and confidence-level assignment before adoption).
  - geopolitical_premium A: [−2,3]→[−6,0]. Basis: defense de-rating on peace; historical Gulf War 1991 post-resolution; ITA/defense ETFs fell 10-20% on relief rallies.
  - inflation_hedge_precious_metals A: [0,4]→[−2,2]. Basis: gold headwind from rising real yields and dollar strength in normalization; post-1991 and post-2003 gold underperformed.
  - inflation_hedge_precious_metals D: [−2,4]→[−5,3]. Basis: forced selling in acute demand destruction; 2008 gold briefly −30% before recovery; 2020 −12% before surge.
  - inflation_hedge_commodity_linked A: [2,6]→[0,4]. Basis: energy premium deflates in normalization; commodity-linked assets lose war premium.
  - inflation_hedge_commodity_linked D: [−8,−2]→[−15,−5]. Basis: 2008 WTI −78% from peak; energy stocks −40%+; 2020 WTI briefly negative.
  - inflation_hedge_commodity_linked E: [2,6]→[−5,2]. Basis: systemic stress produces commodity selloff with everything else; current [2,6] implies positive real return in E which is not empirically supported.
  - real_asset_contracted_revenue D: [2,6]→[−10,−2]. Basis: 2020 AMZI full-year −42% total return; demand destruction collapses throughput volumes; current [2,6] positive is badly wrong vs empirical.
  - real_asset_contracted_revenue E: [2,5]→[−8,0]. Basis: 2008 MLP sector −50%+; systemic forced selling; institutional credit seizure.
  - broad_market_equity_domestic A: [5,12]→[8,15]. Basis: post-1991 Gulf War S&P +34% nominal yr1; post-2003 +29% yr1; empirically stronger than current conservative [5%].
  - broad_market_equity_domestic C: [−4,−1]→[−8,−2]. Basis: 2022 H1 acute C: S&P ~−15% real; current [−4,−1] too optimistic for defined C environment.
  - broad_market_equity_domestic D: [−12,−4]→[−20,−8]. Basis: 2008 S&P real ~−38%; 2009 ~−11%; annual D event far worse than current conservative [−12%].
  - secular_technology_growth B: [−6,−1]→[−12,−3]. Basis: 2022 QQQ nominal −33% (~−41% real); April 30 upward revision to [−6,−1] was driven by revenue not stock returns; multiple compression dominates in stagflation. Flag: reassess at June 30 with additional quarters of B-environment AI stock data.
  - secular_technology_growth D: [−14,−5]→[−20,−8]. Basis: 2008 NASDAQ −40%; 2020 QQQ −28%; current conservative [−14%] too mild for demand destruction.
  - secular_technology_growth E: [−10,−4]→[−18,−6]. Basis: systemic stress is worst for leverage/duration-sensitive tech; 1987 NASDAQ −35% in weeks; 2008 systemic catastrophic for growth stocks.
  - rate_sensitive_income_short A: [0,2]→[1,4]. Basis: Fed rate cuts in A add price appreciation to short duration on top of yield; current [0,2] understates total return.
  - rate_sensitive_income_short D: [0,3]→[2,6]. Basis: aggressive Fed cuts in D boost short duration total return substantially; SGOV-equivalent benefits from price appreciation.
  - ADDITIONALLY at June 30: Assign confidence levels HIGH/MEDIUM/LOW to every cell in §4.1.
  - ADDITIONALLY at June 30: Run neutral-distribution consistency check (A=35/B=15/C=15/D=10/E=5/F=20) on revised table vs institutional unconditional estimates. Document results.
  - ADDITIONALLY at June 30: Determine whether secular_technology_growth continues as separate role or folds into broad_market with structural premium. Requires 4+ quarters of C-environment AI stock return data.
  - ADDITIONALLY at June 30: Add historical analogue period citations to each row in §4.1 as a permanent reference column.
  - ADDITIONALLY at June 30: Define living update triggers between quarterly audits (proposed triggers documented in May 6 session; formally adopt here — now governed by M16 §5).
24. Implement living update protocol: now formally governed by M16_ReturnTableCalibration §5. Confirm June 30 as first formal application of M16 §5 LivingUpdateTriggers. Validate that triggers defined in M16 §5 match proposals from May 6 session; adjust if needed.
25. Session_Log.md compaction: retain last 10 §7 credit rows; collapse §8 to last 3 full entries + summary table. Move prior entries to Archive_2026Q2.md.

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
| inflation_linked_sovereign | N/A | Guard does not apply (sovereign duration risk captured by scenario framework) |
| real_estate_equity_income | 15% | Provisional — same tier as real_asset_contracted_revenue |
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
| 2026-05-06 | PAVE | Status confirmation | No new legislation since Apr 28. IIJA core programs intact. NEVI cuts already reflected. userMemory FLAGGED label confirmed stale. | watch (unchanged) |
| 2026-06-30 | AIPO | ThematicETF_ClassificationAudit | PENDING - provisional Apr 30. Full audit required Q2. Check ETN/Eaton concentration vs PAVE. Financial Services weight (3.60% Apr 30) — assess if above 5% by audit. | PROVISIONAL: see section 11 |

---

## Section 11 - Instrument Classification Registry (M15)

All values CALIBRATION_DATED. First audit: June 30, 2026.
VTI, XAR, MLPX, SGOL, SGOV, PAVE added Apr 28 (v1.7). AIPO, MAGS added Apr 30 (v1.9). AIPO §11 data updated May 6 (v1.10). MLPX EV updated May 6 (v1.11). New roles inflation_linked_sovereign and real_estate_equity_income added May 6 (v1.12) — pending instrument assignments.

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
| inflation_linked_sovereign | CPI_accrual, real_yield_compression, sovereign_credit_quality | v1.12 May 6 | PENDING — instrument candidates: VTIP (Vanguard Short-Term TIPS ETF). Tax placement: retirement preferred (inflation adjustments taxed as ordinary income in taxable). Empirical audit required before return table values can be populated. Historical proxy: CPI-adjusted T-bill returns in stagflation periods (pre-TIPS data). |
| real_estate_equity_income | property_income, rental_growth, cap_rate, real_asset_inflation_linkage | v1.12 May 6 | PENDING — instrument candidates: VNQ (Vanguard Real Estate ETF). Tax placement: retirement preferred (REIT distributions mostly ordinary income — tax-inefficient in taxable). Empirical basis available: 1973-1982 REIT/property real return ~+4.5%/yr (Morningstar/CAIA); JPM LTCMA 2026: U.S. core real estate 8.2% nominal (~5.7% real). Return table [TBD] pending June 30 M16.CalibrationMethodology() audit. |

### 11.2 secular_technology_growth - Return Estimates

Provisional. Added Apr 28. B and C revised Apr 30 (v1.8). Full empirical audit June 30, 2026.
⚠ Vanguard VCMM (Mar 2026): 2.3%-4.3% nominal (0%-2% real) for U.S. growth equities over 10yr — unconditional pessimistic anchor. Research Affiliates: 3.1% nominal U.S. large cap. GMO: -6% real U.S. large cap 7yr. Secular_tech B value revised Apr 30 upward to [-6,-1] based on AI revenue resilience — reassess at June 30 with additional B-environment quarters; proposed revision to [-12,-3] pending (§6 item 23).

| Scenario | Conservative | Upside | Rationale |
| --- | --- | --- | --- |
| A | 6% | 16% | Fed cuts; AI capex expands; multiple expansion |
| B | -6% | -1% | REVISED Apr 30. Multiple compression under elevated rates, partially offset by AI earnings growth (AMZN $2.78 vs $1.64 est; MSFT beat; Azure +40%). Less severe than 2022 zero-AI-revenue analog. PENDING REVISION to [-12,-3] at June 30 — 2022 QQQ real ~-41%; Apr 30 revision may be premature. |
| C | +2% | +8% | REVISED Apr 30. Q1 2026 empirical: Azure +40%, AWS +28%, META +33%, GOOGL beat during active Scenario C. AI enterprise contracts multi-year; weak conflict transmission to AI capex cycle. LOW CONFIDENCE — single data point; empirical audit June 30. |
| D | -14% | -5% | Capex collapse in demand destruction; severe multiple contraction. PENDING REVISION to [-20,-8] at June 30. |
| E | -10% | -4% | Growth multiples collapse in systemic stress. PENDING REVISION to [-18,-6] at June 30. |
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
- EV (A=15/B=36/C=36/D=3/E=3/F=7): +1.29% (revised from +1.58% at A=7 probs — A=15% adds weight to -1.3% conservative A return, reducing blended EV).
- Target: 12% structural across applicable accounts (Primary IRA, Primary Roth, Taxable Acc4).
- Client preference: exit excess XAR at ~$265 spike. Currently overweight in all accounts. Reduction in progress — staged sell in Taxable Acc4 unconfirmed.
- HoldJustification: break-even peace probability <5.6%; opportunity cost vs MLPX -2.33%/year (computed at A=7 probs; directionally valid at A=15 — gap widens further with MLPX EV now +5.51%).
- ⚠ Deal trajectory (A rising): geopolitical_premium A return proposed revision to [-6,0] pending June 30. If adopted, XAR EV would decline further. Reduction to 12% target becomes more urgent as A rises.

#### MLPX
- Components: real_asset_contracted_revenue (0.65) + inflation_hedge_commodity_linked (0.35)
- Last reviewed: 2026-05-06 (v1.11 EV update)
- EV (A=15/B=36/C=36/D=3/E=3/F=7): +5.51% (#1 ranked instrument; revised from +3.64% — real_asset_contracted_revenue B [3,7]→[6,14] and C [3,6]→[8,16] adopted v1.11. D/E unchanged pending June 30 audit.)
- EV computation:
  A(15%): 0.65×3 + 0.35×2 = 2.65% × 0.15 = +0.40%
  B(36%): 0.65×6 + 0.35×6 = 6.00% × 0.36 = +2.16%
  C(36%): 0.65×8 + 0.35×7 = 7.65% × 0.36 = +2.75%
  D(3%):  0.65×2 + 0.35×(-8) = -1.50% × 0.03 = -0.05%
  E(3%):  0.65×2 + 0.35×2 = 2.00% × 0.03 = +0.06%
  F(7%):  0.65×3 + 0.35×2 = 2.65% × 0.07 = +0.19%
  Total: +5.51%
- NOTE: D and E blended returns use current (unadopted) table values. If June 30 proposals adopted (D real_asset→[-10,-2], E real_asset→[-8,0]), blended D/E would worsen: D=-6.30%, E=-5.90%. Revised EV under full June 30 adoption: approximately +4.85% (lower but still #1 ranked).
- Target allocation: 40% across retirement accounts (Primary IRA, Primary Roth, Relative IRA, Relative Roth).
- EntryExtensionGuard: BLOCKING at $73.91 (preliminary — precise 90d trailing avg not computed; real_asset_contracted_revenue threshold 15%, commodity_linked threshold 20%, WAR PREMIUM GUARD independent). Do not ADD until guard clears with dedicated source 90d trailing close.
- Underweight: Primary IRA -9.71pp, Primary Roth -10.16pp. Accept underweight pending guard clearance.
- Drawdown tolerance: client expressed cannot-hold concern re 2014-2020 style 67% price decline (3x wealth reduction). EV case intact and now stronger (+5.51%). However: Relative IRA at 34% MLPX × 67% max drawdown = 22.8% portfolio loss EXCEEDS 20% tolerance with floor_nominal_loss=TRUE. Client decision pending on target revision for Relative IRA (proposed: ~20-22%). Primary Taxable (37%) and Relative Roth (39%) are tight but within stated tolerances. See §6 item 22.

#### SGOL
- Components: inflation_hedge_precious_metals (1.00)
- Last reviewed: 2026-04-28
- CALIBRATION ANOMALY RESOLVED Apr 30 (v1.8): section 4.1 Scenario C return revised [+7%,+14%]->[-2%,+6%]. C-hawk regime empirical basis: gold down ~18% from Jan ATH during active Scenario C; Fed holding rates elevated; real yields at +1.89%; gold underperforms vs short-duration income.
- EV (A=15/B=36/C=36/D=3/E=3/F=7): +1.47% (revised from +1.83% at A=7 probs).
- ⚠ Pending June 30 proposals: A [0,4]→[-2,2] and D [-2,4]→[-5,3]. If adopted, SGOL EV would decline further. SGOL ranking currently #2 at +1.47%.
- JPM LTCMA 2026: gold 5.5% nominal = ~3.0% real unconditional. Current SGOL EV of +1.47% reflects crisis-skewed scenario distribution (B/C dominant suppresses gold in C). Directionally consistent.

#### SGOV
- Components: rate_sensitive_income_short_duration (1.00)
- Last reviewed: 2026-04-28
- EV: +0.73%. Preservation account (Taxable Acc3) = 100% SGOV. Taxable Acc4 SGOV target increased to 29% in M13 rerun (XAR reduction proceeds flow here).
- ⚠ Pending June 30 proposals: A [0,2]→[1,4] and D [0,3]→[2,6]. If adopted, SGOV EV improves modestly.

#### PAVE
- Components: broad_market_equity_domestic (0.82) + policy_driven_thematic_equity (0.18)
- ThematicETF_ClassificationAudit conducted Apr 28. Status: watch (not FLAGGED).
- Last reviewed: 2026-05-06 (status reconfirmed — no new legislation; IIJA core programs intact)
- Cost basis: $54.09/share (~$1,286 embedded gain on 590 shares). Target: ~11% in Taxable Acc4. Currently 13.04% (slight overweight).
- Monitor IIJA reauthorization September 30, 2026.
- OVERLAP: Eaton Corp (ETN) in both PAVE (~3.4% NAV) and AIPO (~8.1% NAV as of Dec 2025; ~8.04% as of Apr 30 2026). Monitor combined concentration at Q2 audit.
- EV (A=15/B=36/C=36/D=3/E=3/F=7): approximately -3.18%. Negative EV — legacy position with embedded gain; do not add.

#### AIPO
- Components: real_asset_contracted_revenue (0.55) + secular_technology_growth (0.20) + broad_market_equity_domestic (0.15) + inflation_hedge_commodity_linked (0.10)
- Basis: Defiance AI & Power Infrastructure ETF. Tracks MarketVector U.S. Listed AI and Power Infrastructure Index. Dominant driver: power and grid infrastructure for AI data centers, not AI companies directly.
- UPDATED May 6, 2026 (v1.10):
  - AUM: ~$457M (as of Apr 30, 2026). Prior entry ($249.5M) was stale Dec 2025 Schwab snapshot — corrected.
  - Sector weights (Apr 30, 2026): Industrials 57.09%, Technology 16.46%, Utilities 14.42%, Energy 6.91%, Financial Services 3.60%, Real Estate 1.04%, Communications 0.48%.
  - Top 10 holdings (Apr 30, 2026): PWR 8.47%, GEV 8.42%, ETN 8.04%, VRT 7.88%, BE 4.95%, CCO 4.33%, AVGO 4.03%, NVDA 3.54%, CEG 3.51%, MTZ 2.33%.
  - Technology weight change: -2.04pp vs Dec 2025 snapshot — within 5pp classification drift threshold; no reclassification.
  - Financial Services 3.60%: new category not present in prior snapshot. Below 5% materiality threshold for classification impact; log for June 30 formal ThematicETF_ClassificationAudit().
- Source: Session bridge May 4, 2026 (audit complete); sector weights and top-10 as of Apr 30, 2026.
- Methodology: sector_weight_analysis + judgment. ThematicETF_ClassificationAudit() REQUIRED at Q2 June 30 — PROVISIONAL classification.
- Last reviewed: 2026-05-06
- Price at adoption: $31.28. Current price (May 6): $32.75. EntryExtensionGuard: ~+11.6% above approx 90d avg per May 4 bridge — below 15% threshold for real_asset_contracted_revenue — PASSES. Recompute with live trailing avg before executing any ADD.
- AUM: ~$457M. Expense ratio: 0.69%. Inception: 07/24/2025 (thin track record — flag at Q2).
- EV (A=15/B=36/C=36/D=3/E=3/F=7): ~+2.94% (v1.11 — real_asset_contracted_revenue B/C revision improves AIPO EV via 0.55 weight component). AIPO now #2 ranked instrument at +2.94%, ahead of SGOL (+1.47%) and XAR (+1.29%).
- EV recompute v1.11 (real_asset_contracted_revenue B/C adopted):
  A(15%): 0.55×3+0.20×6+0.15×5+0.10×2 = 3.80% × 0.15 = +0.57%
  B(36%): 0.55×6+0.20×(-6)+0.15×(-8)+0.10×6 = 3.30-1.20-1.20+0.60 = 1.50% × 0.36 = +0.54%
  C(36%): 0.55×8+0.20×2+0.15×(-4)+0.10×7 = 4.40+0.40-0.60+0.70 = 4.90% × 0.36 = +1.76%
  D(3%):  0.55×2+0.20×(-14)+0.15×(-12)+0.10×(-8) = 1.10-2.80-1.80-0.80 = -4.30% × 0.03 = -0.13%
  E(3%):  0.55×2+0.20×(-10)+0.15×(-8)+0.10×2 = 1.10-2.00-1.20+0.20 = -1.90% × 0.03 = -0.06%
  F(7%):  0.55×3+0.20×4+0.15×7+0.10×2 = 1.65+0.80+1.05+0.20 = 3.70% × 0.07 = +0.26%
  Total: +2.94%
- TAX PLACEMENT: ALL ACCOUNTS including taxable (standard ETF structure — no swap, no phantom gains).
- PAVE overlap: ETN in both AIPO (~8.04% Apr 30) and PAVE (~3.4% NAV). Audit at Q2 June 30.

#### MAGS
- Components: secular_technology_growth (0.85) + broad_market_equity_domestic (0.15)
- Basis: Roundhill Magnificent Seven ETF. Equal-weight AAPL/MSFT/GOOGL/AMZN/META/NVDA/TSLA via total return swap structure (T-bills as collateral + equity swaps). Top holdings (03/31/2026): T-bills 41.86%, AMZN 6.13%, NVDA 6.04%, META 5.81%, MSFT 5.70%, GOOGL swap 5.29%, AAPL 5.26%. 15% broad_market weight reflects TSLA and AAPL hardware/consumer component.
- Source: Schwab report card 04/30/2026; holdings as of 03/31/2026
- Methodology: holdings_analysis + judgment
- Last reviewed: 2026-04-30
- Price at adoption: $66.24. EntryExtensionGuard: fund down 12.2% over 3 months; current price well below 90d trailing avg (~$75) — PASSES easily.
- AUM: $3.5B. Expense ratio: 0.29% (lowest of all AI-sector candidates). Inception: 04/10/2023.
- EV (A=15/B=36/C=36/D=3/E=3/F=7): approximately -1.38% (revised from -2.34% at A=7 probs — A=15% adds weight to +4.1% conservative A return, slightly improving blended EV; still negative). NEGATIVE EV — documented client judgment override. Rationale accepted: AI/Mag7 earnings momentum thesis; optionality on future scenario shift toward A/F; cheapest and most liquid pure secular-tech instrument.
- TAX PLACEMENT: RETIREMENT ACCOUNTS ONLY (IRA and Roth accounts). Swap structure generates phantom taxable gains in losing years. Do NOT hold in Taxable Acc4 or any taxable account.
- COUNTERPARTY RISK: does not directly hold Mag7 shares — uses total return swaps. Counterparty default risk exists. Does not vote underlying shares.
- No Anthropic or SpaceX exposure. Pure public-market Mag7 bet.
- MAGS vs AGIX upgrade evaluation: AGIX (AUM $171.5M, expense 0.99%) holds Anthropic ~2.98% direct. Anthropic targeting IPO Oct 2026 at ~$60B valuation. If IPO announced/imminent, evaluate MAGS->AGIX upgrade. Assess at Q3 2026 audit or earlier on announcement.
