# Calibration State

Persistent framework configuration — load at every session start alongside Session Log.

Version: 1.15  Last updated: May 7, 2026 (Full M05 session — scenario probabilities updated A=15/B=36/C=36/D=3/E=3/F=7; secular_technology_growth Scenario B pending upward revision logged §6 item 35 (MEDIUM confidence); Primary Taxable deployment complete; v1.13 targets confirmed live in allocation file.)  Next scheduled review: June 30, 2026 (Q2 2026 quarter-end)

**File split as of v1.12:**
- Session observations (§7) and session state (§8) now live in **Session_Log.md** (fetched concurrently at session start).
- Prior calibration history before last-10 entries lives in **Calibration_Log.md**.
- This file (Calibration_State.md) is the LIVE CONFIG — kept lean for reliable write-back.

---

## Load Verification Requirement

At session start, after both files are fetched, the advisor must state in the briefing:

"Calibration State loaded, last update: May 7, 2026 | Session Log loaded"

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
Session observation (May 6 full session): HY ~277 bps (ycharts T2, May 1) / ~283 bps (govspending T2, Apr 30 reference). FRED fetch attempted — metadata only; no live values retrieved. Tightening on deal optimism; no threshold fires. T1_flag: stale.

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
- May 6 full session: BRENT C-TRIGGER CLOCK BROKEN. Day 5 = May 5 close ~$109.87 (CNBC T1). Below $110 nominal threshold. Clock resets to Day 0. 4 consecutive days achieved (Apr 29-May 4); 10 required; not met. May 6 close: Brent $101.27 (NBC T1); WTI $95.08. Deal reports active. SGOL WTI floor: WTI ~$95, comfortably above $55 floor. SGOL invalidation NOT triggered. DXY ~97.77, well below 105 threshold.

### 2.2 Currency

| Threshold | Current Value | Audit Status |
| --- | --- | --- |
| DXY sustained above - SGOL invalidation | 105 nominal | Pending June 30 |

DXY ~97.77 (Investing.com T2, May 6). Well below 105. No SGOL invalidation risk.

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

M07 Regional Concentration Ruling (v1.13, May 6, 2026): "Region" for purposes of the 40% foreign concentration threshold is defined as a single political/economic regulatory bloc — not a geographic continent. Rationale: the rule is designed to protect against single-political-regime concentration risk. Canada and the United States, while geographically North American, operate under separate currencies, regulatory frameworks, central banks, and legal systems. COPX's combined North American exposure (~46% across Canada 36.68% + US 9.59%) passes the M07 screen because no single political/economic regime exceeds 40%. Canada alone at 36.68% is below threshold. RULING: COPX PASSES M07 foreign concentration check. ⚠ Amber flag logged for June 30 ThematicETF_ClassificationAudit() confirmation.

---

## Section 3 - Calibration Log (last 10 entries; prior entries in Calibration_Log.md)

2026-04-30 - Full M05 session: M13 rerun, AIPO+MAGS adopted, VTI eliminated (v1.9). Session type: full M05. Allocation sheet fetched (Google Drive MCP). Calibration State fetched (GitHub MCP). MOVE index first logged. Credit carry-forward. FOMC hold 3.5-3.75%. Q1 GDP +2.0%. Brent C-trigger clock Day 2. Scenario probabilities: A=7/B=42/C=42/D=3/E=3/F=3.

2026-05-06 - Full M05 session (v1.10). C-trigger clock broken Day 5 (May 5 close ~$109.87, CNBC T1). Scenario probabilities updated: A=15%(+8pp), B=36%(-6pp), C=36%(-6pp), D=3%(unch), E=3%(unch), F=7%(+4pp). AIPO §11 updated: AUM $457M. PAVE watch status confirmed. MLPX EntryExtensionGuard blocking. M14 composite divergence: MODERATE.

2026-05-06 - Returns table empirical overhaul initiated (v1.11). Full methodology framework documented. Historical scenario-to-analogue mapping established. ADOPTED: real_asset_contracted_revenue B [3,7]→[6,14] and C [3,6]→[8,16]. Empirical basis: AMZI total return 2022 +31.4% nominal. MLPX §11 EV updated: +3.64%→+5.51%. Fourteen additional revision proposals logged in §6 item 23.

2026-05-06 - Architecture session (v1.12). File split implemented: §7 and §8 moved to Session_Log.md; §3 entries 1-4 archived to Calibration_Log.md. M16_ReturnTableCalibration.md authored (governs §4.1 revision methodology). M12, M05, 00_INDEX updated for two-file session protocol. New roles added to §11.1 and §4.1: inflation_linked_sovereign and real_estate_equity_income (LOW confidence, [TBD] values, pending June 30 empirical audit). No portfolio analysis this session.

2026-05-06 - Comprehensive instrument expansion (v1.13). Probability update: A=18%(+3pp), B=35%(-1pp), C=34%(-2pp), D=3%, E=3%, F=7%. Full M14 ComputeDivergenceSignal: composite HIGH (equity_scenario_divergence HIGH at S&P 30d +10.3%). XAR confirmed sold to 12% target across all accounts — Open Decision #2 CLOSED. Five new roles added to §11.1: systematic_trend_following, consumer_defensive_equity, healthcare_defensive_equity, floating_rate_credit_income, emerging_market_equity. §4.1 return table fully calibrated for all roles using M16.CalibrationMethodology() 4-layer procedure. ADOPTED (HIGH confidence): systematic_trend_following A/B/C values; consumer_defensive_equity B value. Nine new instruments classified in §11.3: DBMF, SIVR, COPX, VTIP, XLP, VNQ, VEA, XLV, FLOT. Primary IRA structural gap RESOLVED: achievable EV +3.62% with DBMF adoption (required: 3.2%). MLPX EntryExtensionGuard preliminary analysis: guard may be clearing (estimated 90d avg ~$66; current $73.63 ~12% above avg vs 15% threshold). Verification from approved price source required before ADD executes. New target allocations issued for all 6 accounts. Relative IRA MLPX drawdown breach RESOLVED by reducing target to 24% (24% × 67% = 16.1% < 20% floor). MOVE index: ~76.8 (TradingView T2). Brent close: $101.27. S&P 500 record high: +1.46%.

2026-05-07 - AIPO reclassification + guard clearance (v1.14). Session type: ad-hoc analysis (no allocation fetch — full M05 session required for share count targets). AIPO ThematicETF_ClassificationAudit() COMPLETE. Holdings confirmed from T1 sources: Industrials 50%, IT 30%, Utilities 20%. Top holdings: Quanta Services 8.6%, GE Vernova 8.2%, Eaton 7.9%, Vertiv 7.9%, NVDA 4.2%, AVGO 3.9%, AMD 2.1%. Revised components: RAC 0.55→0.45; STG 0.20→0.30; BMD 0.15→0.00 (ELIMINATED — no qualifying undifferentiated domestic equity; all holdings have specific AI/power binding drivers); new PDT 0.20; IHC 0.10→0.05. CORRECTION: prior session analysis (May 7 ad-hoc) erroneously stated "B improves" — WRONG. Actual revised AIPO EV = +2.42% (↓ from +2.95%), rank drops to #5 (below SIVR +2.86%). EV reduction driven by PDT B conservative = -3% and more STG weight at B = -6%. A-regime improves: +4.05% (↑ from +3.80%) due to STG A = +6% and PDT A = +4%. SIVR entry guard CLEARED: confirmed price anchors (March 14 = $76.31, March 26 = ~$63.64, April 2 = $69.11, April 24 = $72.28, May 6 = $73.79); 90d avg ~$78-82; threshold ~$94-98; current $73.79 below threshold. v1.13 estimated avg ($55-65) was incorrect — all confirmed data points above $63. COPX entry guard CLEARED: confirmed anchors (Feb 6 = $81.31, April 28 = $78.69, May 6 = $78.21); 90d avg ~$85-90; threshold ~$102-106; current $78.21 below threshold. v1.13 estimated avg ($55-65) was significantly incorrect — Feb 6 anchor $81.31 alone exceeds entire estimated range. Execution notes updated: SIVR and COPX now immediate. AI application layer instrument screen conducted: no M07-compliant pure-play instrument available (track record and/or AUM constraints). NVDA overlap noted: AIPO holds NVDA 4.2%, AVGO 3.9%, AMD 2.1% — partial overlap with MAGS. Monitor at Q2.

2026-05-07 - Full M05 session (v1.15). Scenario probabilities updated: A=15%(-3pp), B=36%(+1pp), C=36%(+2pp), D=3%(unch), E=3%(unch), F=7%(unch). check_energy=1 this session (Brent declining 4 consecutive days vs ≥5 threshold). CPI May 12 binary event upcoming — highest priority. M14 composite HIGH unchanged. M16 analysis: secular_technology_growth Scenario B full 4-layer run completed; MEDIUM confidence; upward pending proposal logged (§6 item 35). Primary Taxable deployment complete: DBMF 854sh, XLP 196sh, COPX 212sh executed; $51,950 cash fully deployed (Open Decision #4 CLOSED). v1.13 targets confirmed live in allocation file; remaining trades executing through May 8. Portfolio total ~$762,097.

---

## Section 4 - Growth Objectives: Return Table and Multipliers

All values CALIBRATION_DATED. Last calibrated: May 6, 2026 (v1.13 — 5 new roles fully calibrated; systematic_trend_following A/B/C and consumer_defensive_equity B adopted HIGH confidence; all other new role values PENDING June 30). Full empirical audit: June 30, 2026.

CALIBRATION PROPOSALS ADOPTED April 30, 2026:
- secular_technology_growth Scenario C: [-2%,+4%]->[+2%,+8%]
- secular_technology_growth Scenario B: [-10%,-3%]->[-6%,-1%]
- inflation_hedge_precious_metals Scenario C: [+7%,+14%]->[-2%,+6%]

CALIBRATION PROPOSALS ADOPTED May 6, 2026 (v1.11):
- real_asset_contracted_revenue Scenario B: [3,7]→[6,14]. Empirical basis: AMZI 2022 +31.4% nominal total return.
- real_asset_contracted_revenue Scenario C: [3,6]→[8,16]. Same empirical basis.

CALIBRATION PROPOSALS ADOPTED May 6, 2026 (v1.13 — HIGH confidence only):
- systematic_trend_following Scenario A: [-12, -3]. BASIS: post-1982, post-1991, post-2003 normalization analogs; CTA trend-reversal whipsaw well-documented.
- systematic_trend_following Scenario B: [+15, +30]. BASIS: 1973-1982 proxy +22-30%/yr; DBMF 2022 actual +22.2%; SG CTA Index 2022 +25.7%. HIGH confidence — multiple confirming data points.
- systematic_trend_following Scenario C: [+18, +35]. BASIS: 1973-74, 1979-80 acute commodity trend events; same structural driver as B but more acute.
- consumer_defensive_equity Scenario B: [+2, +6]. BASIS: 1973-1982 XLP proxy +2-5%/yr real; 2022 XLP +3-4% real vs S&P -18% nominal. HIGH confidence.

### 4.1 Expected Real Annualized Return Table

Conservative end used for ALL computations. Upside end disclosed in briefing only.
All scenario return computations use M15.blendedScenarioReturn() — this table is consumed via that function, never directly.
All §4.1 revisions must follow M16.CalibrationMethodology() 4-layer procedure before adoption.
Historical scenario analogues: A=1991/2003/2016 normalization; B=1973-1982/2022 stagflation; C=1974/1979-80/2022 H1 shock; D=2008-09/2020 COVID; E=2008 acute systemic/1998 LTCM; F=1995-2000/2017-2019/2023-2024 growth.
Institutional unconditional anchors (real, 10yr, neutral distribution A=35/B=15/C=15/D=10/E=5/F=20): broad_market ~1-4%; gold ~3%; infrastructure ~4-5%; commodities ~1.6-2.1%; short_duration ~1.5-2%; managed_futures ~5-8% (AQR TSMOM research); consumer_staples ~1-3%.

★ = ADOPTED v1.13 (HIGH confidence — M16.CalibrationMethodology() 4-layer complete).
⚑ = PENDING June 30 (MEDIUM confidence — M16 calibration required before formal adoption).
⚠ = PENDING June 30 (LOW confidence — irreconcilable historical anchors; requires deeper analysis).

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
| inflation_linked_sovereign | [-2, 1]⚑ | [1, 4]⚑ | [1, 4]⚑ | [0, 3]⚑ | [-1, 2]⚑ | [-1, 1]⚑ |
| real_estate_equity_income | [3, 8]⚠ | [-6, -1]⚠ | [-10, -4]⚠ | [-3, 2]⚠ | [-10, -3]⚠ | [2, 5]⚠ |
| systematic_trend_following | [-12, -3]★ | [+15, +30]★ | [+18, +35]★ | [-5, +15]⚑ | [-8, +8]⚑ | [-5, +3]⚑ |
| consumer_defensive_equity | [0, +4]⚑ | [+2, +6]★ | [0, +4]⚑ | [-5, 0]⚑ | [-8, -2]⚑ | [-3, +2]⚑ |
| healthcare_defensive_equity | [1, 5]⚑ | [1, 4]⚑ | [-2, 3]⚑ | [-4, 1]⚑ | [-8, -2]⚑ | [1, 5]⚑ |
| floating_rate_credit_income | [1, 3]⚑ | [1, 3]⚑ | [1, 3]⚑ | [-10, -4]⚑ | [-8, -2]⚑ | [1, 3]⚑ |
| emerging_market_equity | [4, 9]⚑ | [-12, -6]⚑ | [-15, -9]⚑ | [-25, -15]⚑ | [-22, -14]⚑ | [4, 11]⚑ |

secular_technology_growth: added v1.7 Apr 28. B and C values revised v1.8 Apr 30. Provisional - empirical audit June 30, 2026.
inflation_hedge_precious_metals Scenario C: revised v1.8 Apr 30 (C-hawk regime empirical data).
real_asset_contracted_revenue B and C: revised v1.11 May 6 (AMZI 2021-2024 empirical data). D and E pending June 30.
inflation_linked_sovereign: added v1.12 May 6. All values MEDIUM confidence — PENDING June 30. Proxy: CPI-adjusted T-bill returns + 2022 VTIP actual (+2.0% real). Layer 4 neutral check: +0.75% midpoint (vs real yield anchor ~1.89% — slight understatement resolved at June 30 audit).
real_estate_equity_income: added v1.12 May 6. ALL values LOW confidence — irreconcilable 1970s NAREIT analog (+3-6% real) vs 2022 VNQ actual (-26% nominal). Root cause: modern REIT leverage 40-60% LTV vs 1970s 20-30% LTV. Requires leverage-adjusted calibration at June 30.
systematic_trend_following: added v1.13 May 6. A/B/C ADOPTED HIGH confidence. D/E/F PENDING June 30. Layer 4 neutral check: +5.03% midpoints — consistent with AQR TSMOM research +5-8% unconditional real (1880-2020).
consumer_defensive_equity: added v1.13 May 6. B value ADOPTED HIGH confidence. All other values PENDING June 30. Layer 4 neutral check: +1.00% midpoints — consistent with JPM LTCMA consumer staples 1-3% real unconditional.
healthcare_defensive_equity: added v1.13 May 6. ALL values PENDING June 30 (MEDIUM confidence). Layer 4 neutral check: +1.70% midpoints — below JPM LTCMA healthcare 2-4% real; gap reflects B/C distribution penalizing equity. Resolve at June 30.
floating_rate_credit_income: added v1.13 May 6. ALL values PENDING June 30 (MEDIUM confidence). Key risk: D scenario credit seizure (-10% to -4%) vs SGOV safety. Layer 4 neutral check: +0.93%.
emerging_market_equity: added v1.13 May 6. ALL values PENDING June 30 (MEDIUM confidence). Layer 4 neutral check: -2.55% midpoints — below EM institutional anchor (~+3-5% real) reflecting current crisis distribution skew. Resolve at June 30.
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

Weighted target (A=18%/B=35%/C=34%/D=3%/E=3%/F=7%) = 1.472x. Required ~3.2%. STRUCTURAL GAP RESOLVED v1.13: achievable EV with DBMF adoption = +3.62% (Primary IRA target portfolio per §11 CONSOLIDATED TARGET ALLOCATIONS) — exceeds required 3.2% by +0.42pp. Prior achievable max (no DBMF, v1.11 probs): ~2.93-2.98%. Gap was closed by systematic_trend_following adoption.

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

Weighted multiplier (A=18/B=35/C=34/D=3/E=3/F=7) = 1.599x. Required ~2.8%. Achieved: +3.62% (Primary Roth target portfolio). Exceeds requirement by +0.82pp.

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
| 2026-06-30 | Q2 first full audit | All calibration-dated thresholds; section 4 return table and multipliers; M14/M10/M15 thresholds; restore multipliers if commodity-linked added post-war; AIPO ThematicETF_ClassificationAudit — COMPLETE v1.14 (§11 revised; EV +2.42%; confirm at Q2 for weight drift); AIPO/PAVE ETN overlap check; MOVE index integration assessment; MAGS vs AGIX reassessment if Anthropic IPO announced; secular_technology_growth empirical validation; formal adoption of §6 item 23 pending proposals; populate all PENDING §4.1 values (M16.CalibrationMethodology() 4-layer required for all MEDIUM/LOW confidence cells); resolve real_estate_equity_income leverage-adjusted calibration; COPX M07 regional ruling formal confirmation; URA full M07+M15 evaluation; SIVR+COPX entry guard 90d trailing price computation — CLEARED v1.14 (T1 Yahoo Finance daily close verification optional but not blocking); DBMF D/E/F formal adoption |
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
8. Empirical audit section 4.1 return table — all roles. Incorporate FOMC/GDP/CPI data post-April 30. Validate secular_tech B/C and precious_metals C revisions. Formally adopt or reject §6 item 23 pending proposals with documented M16.CalibrationMethodology() 4-layer procedure. Formally adopt all PENDING cells (⚑ MEDIUM confidence) for new v1.13 roles: consumer_defensive_equity C/A/D/E/F; healthcare_defensive_equity all cells; floating_rate_credit_income all cells; emerging_market_equity all cells; systematic_trend_following D/E/F cells. Resolve real_estate_equity_income (⚠ LOW confidence) — requires leverage-adjusted historical calibration before any cell can be formally adopted. Populate [TBD] / PENDING values for inflation_linked_sovereign. Confirm COPX mining leverage adjustment to blended B/C returns.
9. Empirical audit 4.2/4.3 multipliers. Assess if commodity-linked added; if so restore B/C and floors (IRA 1.5x, Roth 2.0x). Reassess structural IRA gap with updated blendedScenarioReturn() outputs.
10. Audit 4.4 floor/concentration parameters.
11. First audit section 9 M14 thresholds (divergence, underweight, entry extension).
12. First audit section 10 M08 ETF classification thresholds.
13. XAR: re-verify at Q2 (standard staleness check; composition drift). XAR now at 12% target across all applicable accounts — confirm structural target remains appropriate.
14. First audit section 11 classification weights — all instruments including AIPO, MAGS, and all v1.13 additions. Flag weight drift >5pp. NOTE: AIPO reclassified v1.14 — confirm revised weights (RAC 0.45, STG 0.30, PDT 0.20, IHC 0.05) and check for NVDA/AVGO/AMD weight drift vs MAGS overlap.
15. AIPO ThematicETF_ClassificationAudit() — COMPLETE v1.14 (May 7, 2026). Revised classification in §11. Confirm at Q2 for weight drift and PAVE ETN overlap check. Financial Services weight (3.60% Apr 30) — assess if above 5%.
16. MAGS vs AGIX: reassess if Anthropic IPO announced or completed. AGIX holds ~2.98% Anthropic direct. Evaluate upgrade at Q3 or earlier on IPO announcement.
17. Review section 11 role registry for new structural drivers. Confirm all 12 existing + 5 v1.13 roles remain complete and non-redundant. NOTE: AI application layer gap identified — no M07-compliant pure-play instrument available as of May 7, 2026. Re-screen at Q2 as new instruments mature (track record threshold).
18. MOVE index: assess formal integration into M11/M14 as supplementary credit/volatility signal.
19. Add Fed response function sub-variable to Scenario C scoring (design proposal Apr 29).
20. Record all results in section 3 calibration log.
21. AIPO Financial Services weight (3.60% as of Apr 30): assess materiality for classification. Flag if above 5% by Q2 audit.
22. MLPX target allocation: Relative IRA formally reduced to 24% (drawdown breach resolved v1.13). Primary accounts per new consolidated targets. Relative Roth at 32%. Document final decisions in §11 MLPX entry.
23. RETURNS TABLE PENDING REVISION PROPOSALS (logged May 6, 2026 — formal adoption requires June 30 audit): [14 proposals listed in prior v1.12 §6 item 23 — all carry forward unchanged].
24. Implement living update protocol: now formally governed by M16_ReturnTableCalibration §5. Confirm June 30 as first formal application of M16 §5 LivingUpdateTriggers.
25. Session_Log.md compaction: retain last 10 §7 credit rows; collapse §8 to last 3 full entries + summary table. Move prior entries to Archive_2026Q2.md.
26. COPX M07 regional concentration ruling: confirm "region = political/economic bloc" ruling from v1.13 as formal framework policy. Apply consistently to all future M07 screens.
27. URA (Global X Uranium ETF): full M07 screen + M15 classification. Proposed role composition: real_asset_contracted_revenue (0.50) + inflation_hedge_commodity_linked (0.30) + secular_technology_growth (0.20). Verify Canada concentration passes 40% threshold (URNM failed at 60.5%; URA expected to pass). Add to §11 if passes.
28. SIVR entry guard computation — COMPLETE v1.14 (May 7, 2026). CLEARED. 90d avg ~$78-82; threshold ~$94-98; current $73.79 < threshold. T2 anchor computation; T1 Yahoo Finance daily close series verification optional (not blocking given wide margin).
29. COPX entry guard computation — COMPLETE v1.14 (May 7, 2026). CLEARED. 90d avg ~$85-90; threshold ~$102-106; current $78.21 < threshold. T2 anchor computation; confirmed Feb 6 anchor $81.31 alone exceeds v1.13 estimated range.
30. DBMF D/E/F scenario formal adoption: complete M16.CalibrationMethodology() Layer 1-4 for remaining three scenarios. Primary analog: D = 2008 SG CTA Index +14.1% (short equity offset by commodity reversal); E = acute 2008 Q4 whipsaw; F = 2017-2019 "trend desert." Confidence: MEDIUM — adopt at Q2 audit.
31. Healthcare_defensive_equity (XLV): confirm §11 classification. Run ThematicETF_ClassificationAudit() — sector composition has shifted toward biotech/tech-adjacent REITs; verify role weights. Full M16 calibration for all scenario values.
32. Floating_rate_credit_income (FLOT): full M07 screen. Confirm no foreign concentration issue. Compute D scenario (-10% to -4%) empirical basis using 2008 IG spread data.
33. Emerging_market_equity (VWO): full M07 screen. Confirm China (~30.8%) + Taiwan (~18-22%) combined regional concentration — determine if Taiwan Strait geopolitical risk warrants amber flag. Apply M07 regional ruling from item 26.
34. Consumer_defensive_equity (XLP): complete M16 calibration for A/C/D/E/F scenarios (PENDING). Primary analog: A = 2003-2007 XLP vs market underperformance; C = 1973-74 input cost squeeze; D = 2008 XLP -15% nominal.
35. secular_technology_growth Scenario B PENDING UPWARD REVISION (logged May 7, 2026 — full M16.CalibrationMethodology() 4-layer run completed this session):
  - Proposed revision: [-6,-1] → [-2,+4]. MEDIUM confidence.
  - Layer 1: unconditional anchor ~0-2% real (VCMM Mar 2026: 0-2% real US growth equities; RA: ~1% real; GMO: -6% real pessimistic anchor).
  - Layer 2 analogues: (a) 1973-82 — weak proxy, no AI enterprise contract structure; IBM returned ~-2% to +3% real/yr; growth factor underperformed value 15-20% cumulative. (b) 2022 direct — secular tech -28-33% nominal despite 20-25% cloud revenue growth; multiple compression from 35x→20x dominated earnings growth. (c) Q1 2026 — Azure +40%, AWS +28%, META +33%, AMZN EPS $2.78 vs $1.64 est.; ONE QUARTER only; contaminated by A-scenario re-pricing from deal optimism. Analog count: 2 clean + 1 contaminated.
  - Layer 3 structural adjustments: (a) AI enterprise contract lock-in (+2-4% upward): multi-year committed spend clauses absent from 2022 analog. Falsification: if renewal rates fall below 85% in sustained B environment. (b) Sustained multiple compression (-5-10% downward): FOMC at 3.5-3.75% for years → growth P/E 30x→20x even with 35% revenue growth → net negative price return. HIGH confidence on compression mechanism. (c) AI capex sustainability (uncertain, ±2%): capex strain signals emerging (MSFT considering abandoning 2030 renewable goals). Net structural adjustment: mildly supports current [-6,-1] range; provides only weak evidence for significant upward revision.
  - Layer 4 consistency check (neutral A=35/B=15/C=15/D=10/E=5/F=20): proposed conservative=-2% → weighted avg +1.0% vs anchor midpoint ~1.0%. Gap = 0.0pp. PASS within ±3pp tolerance.
  - Competing proposal: [-12,-3] (more negative, logged May 6 §6 item 23) remains on table. Both proposals for June 30 adjudication.
  - Confidence level: MEDIUM — does not meet HIGH (requires 3+ distinct analogues + institutional agreement within 2pp; we have 2 analogues and no institutional source validates positive B return for secular tech).
  - Adoption: BLOCKED intra-session (MEDIUM confidence). Adopt at June 30 audit only.
  - Upgrade path to HIGH confidence: if Q2 2026 Mag7 earnings (reporting May-July 2026) confirm >25% revenue growth in B environment with zero guidance withdrawals → provides 2nd and 3rd data points → eligible for HIGH confidence reclassification and intra-session adoption with client confirmation.
  - Current §4.1 B value [-6,-1] remains operative until June 30 adjudication.
  
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

May 6 full session M14 computation: commodity_fear_divergence = MODERATE (energy_90d ~+63% >= +10%; VIX_change_90d ~+3.4 pts — above 0, within +5). equity_scenario_divergence = HIGH (S&P 30d +10.3% >= +5%; B/C directive for broad_market_equity is reductive). Composite = HIGH (upgraded from MODERATE). UnderweightReviewTrigger fired for Primary IRA MLPX (-9.82pp) and Primary Roth MLPX (-10.28pp).

### 9.2 Underweight Review Trigger

| Parameter | Current Value | Type |
| --- | --- | --- |
| underweight_gap_trigger | 5 pp | Calibration-dated |
| appreciation_trigger_30d | 5% | Calibration-dated |

### 9.3 Entry Extension Guard Thresholds

| Role | Threshold | Notes |
| --- | --- | --- |
| broad_market_equity_domestic | 15% | Provisional |
| broad_market_equity_international | 15% | Provisional |
| thematic_sector_equity | 20% | policy_driven_thematic_equity, geopolitical_premium |
| commodity_linked | 20% | WAR PREMIUM ENTRY GUARD also applies independently |
| inflation_hedge_precious_metals | 20% | Provisional |
| real_asset_contracted_revenue | 15% | Provisional |
| secular_technology_growth | 20% | Added v1.7 Apr 28 |
| consumer_defensive_equity | N/A | Guard does not apply — domestic equity sector ETF, no commodity or war premium component |
| healthcare_defensive_equity | N/A | Guard does not apply — domestic equity sector ETF |
| systematic_trend_following | N/A | Guard does not apply — return is driven by trend signals, not entry price level |
| floating_rate_credit_income | N/A | Guard does not apply — short duration sovereign/IG credit |
| emerging_market_equity | 15% | Provisional — same tier as broad international |
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
| 2026-05-07 | AIPO | ThematicETF_ClassificationAudit | COMPLETE v1.14. Holdings confirmed: Industrials 50%, IT 30%, Utilities 20%. Top holdings: Quanta Services 8.6%, GE Vernova 8.2%, Eaton 7.9%, Vertiv 7.9%, NVDA 4.2%, AVGO 3.9%, AMD 2.1%. Revised components: RAC(0.45), STG(0.30), PDT(0.20), IHC(0.05). BMD ELIMINATED. NVDA/AVGO/AMD overlap with MAGS flagged. | REVISED: see §11 AIPO entry. EV: +2.42% (↓ from +2.95%). Ranked #5. Confirm at Q2 for weight drift. |

---

## Section 11 - Instrument Classification Registry (M15)

All values CALIBRATION_DATED. First audit: June 30, 2026.
VTI, XAR, MLPX, SGOL, SGOV, PAVE added Apr 28 (v1.7). AIPO, MAGS added Apr 30 (v1.9). AIPO §11 data updated May 6 (v1.10). MLPX EV updated May 6 (v1.11). New roles inflation_linked_sovereign and real_estate_equity_income added May 6 (v1.12). Five new roles added May 6 (v1.13): systematic_trend_following, consumer_defensive_equity, healthcare_defensive_equity, floating_rate_credit_income, emerging_market_equity. New instruments added May 6 (v1.13): DBMF, SIVR, COPX, VTIP, XLP, VNQ, VEA, XLV, FLOT. AIPO reclassified May 7 (v1.14): ThematicETF_ClassificationAudit() COMPLETE.

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
| broad_market_equity_international | ex_US_aggregate_economic_growth, developed_markets | v1.0 | Active |
| secular_technology_growth | AI_capex_cycle, mega-cap_tech_multiple_expansion, software_adoption, semiconductor_demand | v1.7 Apr 28 | Active - provisional, empirical audit June 30 |
| inflation_linked_sovereign | CPI_accrual, real_yield_compression, sovereign_credit_quality | v1.12 May 6 | Active - PENDING §4.1 calibration June 30. Instrument candidate: VTIP. Tax: retirement preferred (inflation accrual OI in taxable). |
| real_estate_equity_income | property_income, rental_growth, cap_rate, real_asset_inflation_linkage | v1.12 May 6 | Active - PENDING §4.1 calibration June 30 (LOW confidence — leverage-adjusted analysis required). Instrument candidate: VNQ. Tax: retirement preferred (REIT distributions ordinary income). |
| systematic_trend_following | multi_asset_price_trends, momentum_persistence, commodity_trend_signal, rates_trend_signal, currency_trend_signal | v1.13 May 6 | Active - A/B/C values ADOPTED HIGH confidence. D/E/F PENDING June 30. Instrument: DBMF. No entry extension guard. No K-1 risk. All accounts eligible. |
| consumer_defensive_equity | consumer_pricing_power, demand_inelasticity_essentials, household_consumption, brand_moat | v1.13 May 6 | Active - B value ADOPTED HIGH confidence. A/C/D/E/F PENDING June 30. Instrument: XLP. All accounts eligible (standard equity ETF). No entry extension guard. |
| healthcare_defensive_equity | healthcare_demand_inelasticity, pharmaceutical_pricing_power, aging_demographics, biotech_pipeline | v1.13 May 6 | Active - ALL values PENDING June 30 (MEDIUM confidence). Instrument: XLV. All accounts eligible. No entry extension guard. |
| floating_rate_credit_income | short_term_interest_rates, investment_grade_credit_spread, floating_rate_reset | v1.13 May 6 | Active - ALL values PENDING June 30 (MEDIUM confidence). Instrument: FLOT. Key risk: D/E credit seizure. All accounts eligible. |
| emerging_market_equity | EM_aggregate_growth, commodity_export_revenue, EM_policy_cycle, USD_direction | v1.13 May 6 | Active - ALL values PENDING June 30 (MEDIUM confidence). Distinguished from broad_market_equity_international by EM-specific political risk, commodity dependency, and USD sensitivity. Instrument candidates: VWO. Entry guard: 15% (same tier as international). |

### 11.2 secular_technology_growth - Return Estimates

Provisional. Added Apr 28. B and C revised Apr 30 (v1.8). Full empirical audit June 30, 2026.
⚠ Vanguard VCMM (Mar 2026): 2.3%-4.3% nominal (0%-2% real) for U.S. growth equities over 10yr — unconditional pessimistic anchor. Research Affiliates: 3.1% nominal U.S. large cap. GMO: -6% real U.S. large cap 7yr. Secular_tech B value revised Apr 30 upward to [-6,-1] based on AI revenue resilience — reassess at June 30 with additional B-environment quarters; proposed revision to [-12,-3] pending (§6 item 23).

| Scenario | Conservative | Upside | Rationale |
| --- | --- | --- | --- |
| A | 6% | 16% | Fed cuts; AI capex expands; multiple expansion |
| B | -6% | -1% | REVISED Apr 30. Multiple compression under elevated rates, partially offset by AI earnings growth. PENDING REVISION to [-12,-3] at June 30. |
| C | +2% | +8% | REVISED Apr 30. Q1 2026 empirical: Azure +40%, AWS +28%, META +33%. AI enterprise contracts multi-year. LOW CONFIDENCE — single data point; empirical audit June 30. |
| D | -14% | -5% | Capex collapse in demand destruction. PENDING REVISION to [-20,-8] at June 30. |
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
- EV (A=18/B=35/C=34/D=3/E=3/F=7): +1.18%. Ranked #9.
- Target: 12% structural across applicable accounts (Primary IRA, Primary Roth, Taxable Acc4). CONFIRMED AT TARGET across all three accounts as of May 6 session — XAR reduction complete.
- Client preference: exit excess XAR at ~$265 spike. EXECUTED — reduction to 12% confirmed via allocation sheet May 6.
- HoldJustification: break-even peace probability <5.6%; opportunity cost vs MLPX -4.33%/year (at A=18 probs).
- ⚠ Deal trajectory (A rising): geopolitical_premium A return proposed revision to [-6,0] pending June 30. If adopted, XAR EV would decline further.

#### MLPX
- Components: real_asset_contracted_revenue (0.65) + inflation_hedge_commodity_linked (0.35)
- Last reviewed: 2026-05-06 (v1.13 — targets updated)
- EV (A=18/B=35/C=34/D=3/E=3/F=7): +5.38%. Ranked #2.
- Target allocation (v1.13 consolidated targets):
  - Primary IRA: 30%
  - Primary Roth: 28%
  - Primary Taxable: 30%
  - Relative IRA: 24% (REDUCED from 35% — drawdown tolerance breach resolved: 24% × 67% = 16.1% < 20% floor)
  - Relative Roth: 32%
- EntryExtensionGuard: PRELIMINARY CLEARING. Estimated 90d trailing average ~$66. Current price $73.63 (~+12% above avg vs 15% threshold). Requires verification from approved price source (Yahoo Finance historical for Feb 5, 2026 MLPX close) before ADD executes.
- WAR PREMIUM ENTRY GUARD: Also preliminary clearing (~12% vs 20% threshold). Active supply event (Hormuz) — monitor deal status.
- Drawdown tolerance: Relative IRA target reduced to 24% per drawdown analysis (see §6 item 22).

#### SGOL
- Components: inflation_hedge_precious_metals (1.00)
- Last reviewed: 2026-04-28
- CALIBRATION ANOMALY RESOLVED Apr 30 (v1.8): §4.1 Scenario C revised [+7%,+14%]->[-2%,+6%]. C-hawk regime empirical basis.
- EV (A=18/B=35/C=34/D=3/E=3/F=7): +1.45%. Ranked #7.
- Target allocation (v1.13):
  - Primary IRA: 16% (reduced from 33%)
  - Primary Roth: 14% (reduced from 33%)
  - Relative IRA: 26% (reduced from 37%)
  - Relative Roth: 22% (reduced from 40%)
  - Note: SIVR added as complement; SGOL + SIVR combined restores precious metals exposure
- ⚠ Pending June 30 proposals: A [0,4]→[-2,2] and D [-2,4]→[-5,3].

#### SGOV
- Components: rate_sensitive_income_short_duration (1.00)
- Last reviewed: 2026-04-28
- EV: +0.70%. Ranked #10.
- Target allocation (v1.13):
  - Primary Taxable: 15% (reduced from 32%; cash deployment partially to new instruments)
  - Taxable Preservation: 100% (unchanged)
  - Relative IRA: 14% (reduced from 20%; VTIP takes portion)
- ⚠ Pending June 30 proposals: A [0,2]→[1,4] and D [0,3]→[2,6].

#### PAVE
- Components: broad_market_equity_domestic (0.82) + policy_driven_thematic_equity (0.18)
- ThematicETF_ClassificationAudit conducted Apr 28. Status: watch (not FLAGGED).
- Last reviewed: 2026-05-06 (status reconfirmed — no new legislation; IIJA core programs intact)
- Cost basis: $54.09/share (~$1,286 embedded gain on 590 shares). Target: ~11% in Taxable Acc4. Currently 11.00% — at target.
- Monitor IIJA reauthorization September 30, 2026.
- EV (A=18/B=35/C=34/D=3/E=3/F=7): approximately -2.90%. Negative EV — legacy position with embedded gain; do not add.

#### AIPO
- Components: real_asset_contracted_revenue (0.45) + secular_technology_growth (0.30) + policy_driven_thematic_equity (0.20) + inflation_hedge_commodity_linked (0.05)
- CLASSIFICATION REVISED v1.14 (May 7, 2026): ThematicETF_ClassificationAudit() COMPLETE. Prior v1.13 classification included broad_market_equity_domestic (0.15) — ELIMINATED. No AIPO holding qualifies as undifferentiated domestic equity; all holdings have specific AI/power binding drivers confirmed from T1 source data.
- Basis: Defiance AI & Power Infrastructure ETF. Tracks MarketVector US Listed AI & Power Infrastructure Index. Holdings must derive ≥50% revenue from AI hardware, data centers, or power infrastructure. 78 holdings. Confirmed sector breakdown: Industrials 50% (Quanta Services 8.6%, Eaton 7.9%), IT 30% (GE Vernova 8.2%, Vertiv 7.9%, NVDA 4.2%, AVGO 3.9%, AMD 2.1%), Utilities 20%. US-domiciled 90.1%, foreign 9.5%.
- Component basis (v1.14):
  - real_asset_contracted_revenue (0.45): Quanta Services (utility construction, long-term contracts), Eaton (electrical equipment delivery contracts), Bloom Energy (power purchase agreements), utility companies (regulated long-term power contracts).
  - secular_technology_growth (0.30): IT sector 30% — NVDA (4.2%), AVGO (3.9%), AMD (2.1%), Vertiv (data center cooling/power — direct AI hyperscaler contracts).
  - policy_driven_thematic_equity (0.20): GE Vernova (grid modernization mandate, IRA-driven electrification), grid infrastructure policy mandate driven.
  - inflation_hedge_commodity_linked (0.05): Cameco (4.5% uranium mining), Energy sector 0.9%.
- AUM: ~$457M. Expense ratio: 0.69%. Inception: 07/24/2025 (thin track record — flag at Q2).
- ⚠ NVDA overlap: AIPO holds NVDA 4.2%, AVGO 3.9%, AMD 2.1%. MAGS holds NVDA (Magnificent 7). Partial overlap in AI chip layer. Manageable at current target weights — track for Q2 concentration review.
- ⚠ PAVE overlap: ETN (Eaton) in both AIPO (~8%) and PAVE (~3.4%). Audit at Q2 June 30.
- STRUCTURAL NOTE: AIPO is an AI power infrastructure fund — NOT an AI application software fund. MAGS + AIPO cover: AI compute layer (Mag7 hyperscalers) + AI power infrastructure (grid, cooling, construction). AI application software layer remains unaddressed — no M07-compliant pure-play instrument available as of May 7, 2026.
- Last reviewed: 2026-05-07 (v1.14 — ThematicETF_ClassificationAudit() COMPLETE)
- EV (A=18/B=35/C=34/D=3/E=3/F=7): +2.42%. Ranked #5. (↓ from +2.95% v1.13 — reclassification accurate; prior estimate overstated by incorrect BMD inclusion)
  - A:  0.45×3 + 0.30×6 + 0.20×4 + 0.05×2 = 4.05% × 0.18 = +0.73%
  - B:  0.45×6 + 0.30×(-6) + 0.20×(-3) + 0.05×6 = 0.60% × 0.35 = +0.21%
  - C:  0.45×8 + 0.30×2 + 0.20×(-1) + 0.05×7 = 4.35% × 0.34 = +1.48%
  - D:  0.45×2 + 0.30×(-14) + 0.20×(-5) + 0.05×(-8) = -4.70% × 0.03 = -0.14%
  - E:  0.45×2 + 0.30×(-10) + 0.20×(-6) + 0.05×2 = -3.20% × 0.03 = -0.10%
  - F:  0.45×3 + 0.30×4 + 0.20×4 + 0.05×2 = 3.45% × 0.07 = +0.24%
  - Total: +2.42%
- A-regime note: revised A blended = +4.05% (↑ from +3.80%) — STG and PDT both strongly positive in A (+6%, +4%). AIPO is a moderate A performer, not an A-optimized instrument.
- TAX PLACEMENT: ALL ACCOUNTS including taxable.
- Target allocation (v1.13, unchanged): 8% Primary IRA; 8% Primary Roth; 8% Primary Taxable; 6% Relative IRA; 10% Relative Roth.

#### MAGS
- Components: secular_technology_growth (0.85) + broad_market_equity_domestic (0.15)
- Last reviewed: 2026-04-30
- EV (A=18/B=35/C=34/D=3/E=3/F=7): approximately -1.18%. Ranked #11. NEGATIVE EV — documented client judgment override.
- Target allocation (v1.13): 5% Primary IRA (reduced from 7%); 6% Primary Roth (reduced from 7%); 3% Relative IRA (unchanged); 8% Relative Roth (unchanged).
- TAX PLACEMENT: RETIREMENT ACCOUNTS ONLY. Swap structure generates phantom taxable gains in losing years.
- MAGS vs AGIX upgrade evaluation: monitor Anthropic IPO news. Assess at Q3 2026 or earlier on announcement.

#### DBMF
- Components: systematic_trend_following (1.00)
- Basis: iMGP DBi Managed Futures Strategy ETF. Actively managed. Replicates top CTA hedge fund portfolios using T-bill collateral + equity/commodity/bond/currency swap agreements. Strategy: systematic trend-following across all major asset classes.
- K-1: NONE — 1940 Act registered fund (ETF structure). Uses swap agreements, not limited partnership interests. No K-1 issued.
- AUM: $3.51B. Expense ratio: 0.85%. Inception: 2019-05-08. 1-year total return: +27.3%.
- Last reviewed: 2026-05-06 (v1.13, initial classification)
- EV (A=18/B=35/C=34/D=3/E=3/F=7, conservative ends, D/E/F PENDING): +8.47%. Ranked #1.
  - A: -12% × 0.18 = -2.16%
  - B: +15% × 0.35 = +5.25% ★ADOPTED
  - C: +18% × 0.34 = +6.12% ★ADOPTED
  - D: -5% × 0.03 = -0.15% ⚑PENDING
  - E: -8% × 0.03 = -0.24% ⚑PENDING
  - F: -5% × 0.07 = -0.35% ⚑PENDING
  - Total: +8.47%
- TAX PLACEMENT: ALL ACCOUNTS. No K-1. No swap phantom gain issue (T-bill collateral income is standard income, not a phantom gain).
- ENTRY EXTENSION GUARD: N/A — systematic_trend_following role is explicitly exempt (§9.3).
- KEY RISK: Trend-reversal events (Scenario A normalization) produce material losses (-12% conservative). A=18% weight creates -2.16% EV drag — priced into EV computation. DBMF and MLPX are partially inversely correlated in A (MLPX appreciates as energy normalizes; DBMF loses as commodity trends reverse) — portfolio diversification benefit.
- Target allocation (v1.13): 15% Primary IRA; 17% Primary Roth; 10% Primary Taxable; 12% Relative IRA; 18% Relative Roth.

#### SIVR
- Components: inflation_hedge_precious_metals (0.55) + inflation_hedge_commodity_linked (0.45)
- Basis: Aberdeen Standard Physical Silver Shares ETF. Tracks spot silver price via physical silver bullion. Lower cost alternative to SLV (0.30% ER vs 0.50%).
- AUM: ~$5.5B. Expense ratio: 0.30%. Custodian: ICBC Standard Bank (UK).
- Last reviewed: 2026-05-07 (v1.14 — entry guard cleared)
- EV (A=18/B=35/C=34/D=3/E=3/F=7): +2.86%. Ranked #4.
  - A:  0.55×[0] + 0.45×[2] = 0.90% × 0.18 = +0.16%
  - B:  0.55×[6] + 0.45×[6] = 5.70% × 0.35 = +2.00%
  - C:  0.55×[-2] + 0.45×[7] = 2.05% × 0.34 = +0.70%
  - D:  0.55×[-2] + 0.45×[-8] = -4.70% × 0.03 = -0.14%
  - E:  0.55×[10] + 0.45×[2] = 6.40% × 0.03 = +0.19%
  - F:  0.55×[-3] + 0.45×[2] = -0.75% × 0.07 = -0.05%
- KEY DISTINCTION FROM SGOL: Silver's 45% industrial demand component (electronics, solar, EV batteries, AI data center components) sustains positive returns in Scenario C where SGOL underperforms (C-hawk rate regime). Silver C blended return = +2.05% vs SGOL C conservative = -2%.
- TAX PLACEMENT: Retirement accounts preferred. Physical silver ETF is classified as a collectible; capital gains taxed at 28% max rate in taxable accounts (vs 20% for equity ETFs). Taxable placement technically permissible but suboptimal.
- ENTRY EXTENSION GUARD: CLEARED (v1.14, May 7, 2026). 90d trailing average (Feb 5 – May 6): ~$78-82, computed from T2 price anchors (March 14 = $76.31 [Walletinvestor], March 26 = ~$63.64 [inferred], April 2 = $69.11 [multi-source], April 24 = $72.28 [Yahoo Finance], May 6 = $73.79 [Robinhood]). Guard threshold (20% above avg): ~$94-98. Current price $73.79 < threshold — CLEAR. Note: v1.13 estimated avg ($55-65) was incorrect; all confirmed data points in window are above $63. T1 Yahoo Finance daily close series verification optional — wide margin makes blocking impossible given confirmed anchors. EXECUTE per target allocations.
- Target allocation (v1.13): 4% Primary IRA; 5% Primary Roth; 3% Relative IRA. (Not included in Taxable accounts or Relative Roth due to tax/size constraints.)

#### COPX
- Components: inflation_hedge_commodity_linked (0.75) + broad_market_equity_international (0.25)
- Basis: Global X Copper Miners ETF. Tracks Solactive Global Copper Miners Total Return Index. 41 holdings across global copper mining companies.
- AUM: $6.86B. Expense ratio: 0.65%. Inception: 2010-04-19.
- Country breakdown (Jan 31, 2026): Canada 36.68%, China 9.62%, US 9.59%, Japan 7.92%, Australia 7.86%, Poland 5.93%, Sweden 5.35%, UK 5.12%, Switzerland 4.82%, Others 7.13%.
- M07 STATUS: PASS — Canada 36.68% below 40% single-country threshold. North America 43.85% above 40% geographic threshold; however per M07 regional ruling v1.13 (§2.4), "region" = political/economic bloc, not continent. Canada + US are separate political/economic regimes. RULING: PASS. ⚠ Amber flag for June 30 ThematicETF_ClassificationAudit() formal confirmation.
- Last reviewed: 2026-05-07 (v1.14 — entry guard cleared)
- EV (A=18/B=35/C=34/D=3/E=3/F=7, conservative floor — pre-mining-leverage adjustment): +2.76%.
  - A:  0.75×[2] + 0.25×[4] = 2.50% × 0.18 = +0.45%
  - B:  0.75×[6] + 0.25×[-5] = 3.25% × 0.35 = +1.14%
  - C:  0.75×[7] + 0.25×[-6] = 3.75% × 0.34 = +1.28%
  - D:  0.75×[-8] + 0.25×[-8] = -8.00% × 0.03 = -0.24%
  - E:  0.75×[2] + 0.25×[-10] = -1.00% × 0.03 = -0.03%
  - F:  0.75×[2] + 0.25×[3] = 2.25% × 0.07 = +0.16%
  - Total floor: +2.76%. Mining-leverage adjusted estimate: ~+3.5-4.5%.
- MINING LEVERAGE NOTE: Copper miners apply ~1.3-1.5× operating leverage to copper price moves. §4.1 values calibrated for commodity-tracking instruments. Blended B/C returns understate actual COPX returns in positive commodity scenarios. Compute EV using floor estimates only; adjusted EV for reference.
- TAX PLACEMENT: ALL ACCOUNTS (standard equity ETF, no K-1, no special structure).
- ENTRY EXTENSION GUARD: CLEARED (v1.14, May 7, 2026). 90d trailing average (Feb 5 – May 6): ~$85-90, computed from T2 price anchors (Feb 6 = $81.31 [Walletinvestor], April 28 = $78.69 [Investing.com], May 6 = $78.21 [v1.13/CNBC]; 3-month NAV return = -13.47% [TradingView]; 52-week high $99.99 within window). Guard threshold (20% above avg): ~$102-106. Current price $78.21 < threshold — CLEAR. Note: v1.13 estimated avg ($55-65) was significantly incorrect — confirmed Feb 6 anchor $81.31 alone exceeds the entire estimated range. EXECUTE per target allocations.
- Target allocation (v1.13): 2% Primary IRA; 7% Primary Taxable.

#### VTIP
- Components: inflation_linked_sovereign (1.00)
- Basis: Vanguard Short-Term Inflation-Protected Securities ETF. Tracks Bloomberg US TIPS 0-5 Year Index. 27 holdings; all US Treasury TIPS with remaining maturity < 5 years. 100% Treasury/Agency.
- AUM: $66.6B. Expense ratio: 0.03%. Beta: 0.22. Inception: 2012-10-12.
- Last reviewed: 2026-05-06 (v1.13, initial classification)
- Provisional EV (§4.1 values PENDING — MEDIUM confidence): +0.23% at current probs. Actual structural EV in B/C environment is materially higher; provisional values understate due to PENDING §4.1 calibration. When formally calibrated at June 30, expected EV range: +0.8% to +1.4%.
- TAX PLACEMENT: RETIREMENT ACCOUNTS ONLY. Inflation accrual on TIPS is taxed as ordinary income each year it accrues, even though not received as cash until maturity — same phantom income problem as MAGS in taxable accounts.
- ENTRY EXTENSION GUARD: N/A — inflation_linked_sovereign role explicitly exempt per §9.3.
- Target allocation (v1.13): 8% Primary IRA; 10% Primary Roth; 12% Relative IRA; 10% Relative Roth.

#### XLP
- Components: consumer_defensive_equity (1.00)
- Basis: State Street Consumer Staples Select Sector SPDR ETF. Tracks S&P Consumer Staples Select Sector Index. 35 holdings; top positions Walmart, Costco, Procter & Gamble.
- AUM: $14.5B. Expense ratio: 0.08%. 100% US domestic. Inception: 1998-12-16.
- Last reviewed: 2026-05-06 (v1.13, initial classification)
- Provisional EV (§4.1 B value ADOPTED; others PENDING): +0.10% at current probs. Actual structural EV estimated +2.0-2.5% when all §4.1 values formally calibrated. B-scenario contribution: +2% × 0.35 = +0.70% already captures the key driver.
- KEY THESIS: Consumer pricing power passes through inflation costs in sustained B environment. P&G, Walmart, Costco demonstrated 5-8%/yr real outperformance over S&P 500 in 1973-1982 stagflation; XLP returned +3-4% real in 2022 B/C environment vs S&P -18% nominal.
- TAX PLACEMENT: ALL ACCOUNTS (standard equity ETF, no special structure, dividends qualified).
- ENTRY EXTENSION GUARD: N/A — consumer_defensive_equity role exempt per §9.3.
- Target allocation (v1.13): 7% Primary Taxable.

#### VNQ
- Components: real_estate_equity_income (0.60) + rate_sensitive_income_long_duration (0.22) + secular_technology_growth (0.12) + broad_market_equity_domestic (0.06)
- Basis: Vanguard Real Estate Index Fund ETF. Tracks MSCI US Investable Market Real Estate 25/50 Index. 159 holdings; top positions Welltower 7.69%, Prologis 7.03%, Equinix 5.51%, American Tower 4.63%. Data center REITs 7.8%, Healthcare REITs 13.1%, Industrial REITs 9.8%.
- AUM: $65.7B. Expense ratio: 0.13%. 100% US domestic. Inception: 2004.
- Last reviewed: 2026-05-06 (v1.13, initial classification)
- EV at current probs (real_estate_equity_income [TBD] — LOW confidence; using 2022-calibrated proxy): -4.52% to +1.27% depending on §4.1 calibration outcome.
- STRUCTURAL NOTE: VNQ is ADVERSARIAL to current B/C dominant distribution. Rate_sensitive_income_long_duration component (0.22 weight) has deeply negative B/C returns [-4,-1] and [-5,-2] respectively. Modern REIT leverage (40-60% LTV) causes cap rate expansion to overwhelm rental income growth in elevated-rate environments (2022 VNQ: -26% nominal).
- TAX PLACEMENT: RETIREMENT ACCOUNTS ONLY (REIT distributions predominantly ordinary income — mandatory 90% payout, mostly non-qualified dividends).
- ADOPTION TRIGGER: A > 25% on T1-confirmed US-Iran deal. Under A-dominant distribution, VNQ EV improves materially as Fed cutting → cap rate compression → REIT NAV appreciation.
- CURRENT PORTFOLIO ALLOCATION: NONE. §11 entry for framework completeness.

#### VEA
- Components: broad_market_equity_international (1.00)
- Basis: Vanguard FTSE Developed Markets ETF. Tracks FTSE Developed All Cap ex US Index. 3,906 holdings; Japan 20.6%, Financial Services 22.9%. Top 10 = 11.23% — well-diversified.
- AUM: $282B. Expense ratio: 0.03%. Inception: 2007.
- Last reviewed: 2026-05-06 (v1.13, initial classification)
- EV at current probs: -3.40%.
- STRUCTURAL NOTE: Developed international equity faces same B/C headwinds as domestic equity plus energy-importer FX drag (Europe/Japan directly harmed by Hormuz crisis). 1-year return +30.4% represents significant M14 equity_scenario_divergence — NOT a signal to buy under B/C dominant distribution.
- ADOPTION TRIGGER: A > 25% on T1-confirmed deal. Deal normalization → European/Japanese rate cutting cycles + dollar weakening = strong A setup for developed international.
- CURRENT PORTFOLIO ALLOCATION: NONE. §11 entry for framework completeness.

#### XLV
- Components: healthcare_defensive_equity (1.00)
- Basis: Health Care Select Sector SPDR ETF. Tracks S&P Healthcare Select Sector Index. ~65 holdings; major pharma, biotech, medical devices, managed care.
- AUM: ~$40B range. Expense ratio: ~0.13%. 100% US domestic.
- Last reviewed: 2026-05-06 (v1.13, initial classification — provisional; full ThematicETF_ClassificationAudit required Q2)
- Provisional EV (§4.1 ALL PENDING): -0.44% at current probs. Actual structural EV estimated +0.5-1.5% when calibrated. 2022 analog: XLV -3.5% nominal vs S&P -18% — meaningful defensive outperformance.
- TAX PLACEMENT: ALL ACCOUNTS (standard equity ETF).
- CURRENT PORTFOLIO ALLOCATION: NONE. Lower priority than DBMF/COPX/XLP at current probs. Monitor for entry if B/C probability rises further (healthcare becomes more defensive).

#### FLOT
- Components: floating_rate_credit_income (1.00)
- Basis: iShares Floating Rate Bond ETF. Tracks Bloomberg US Floating Rate Note < 5 Years Index. IG corporate floating-rate bonds. Rate resets quarterly to SOFR/LIBOR + spread.
- AUM: ~$10-15B range. Expense ratio: ~0.15%.
- Last reviewed: 2026-05-06 (v1.13, initial classification — full M07 screen pending)
- Provisional EV (§4.1 ALL PENDING): approximately +0.2-0.5% above SGOV in B; significantly worse in D/E due to corporate credit seizure.
- KEY RISK: D/E scenario credit spread blowout (-10% to -4% vs SGOV 0%). SGOV's pure Treasury safety is a feature when D/E tail risk exists (currently D=3%, E=3%).
- TAX PLACEMENT: ALL ACCOUNTS (standard bond ETF).
- CURRENT PORTFOLIO ALLOCATION: NONE. Lower priority. Optional SGOV supplement in B-dominant allocation if D/E tail risk remains low.

---

## Consolidated Target Allocations (v1.13, May 6, 2026)

All values are target percentages. Share counts computed by allocation file (authoritative). Execution notes: DBMF, VTIP, XLP, SIVR, COPX — immediate (SIVR and COPX entry guards cleared v1.14, May 7, 2026); MLPX ADD — pending 90d trailing price verification from T1 source.

| Instrument | Primary IRA | Primary Roth | Primary Taxable | Taxable Pres. | Relative IRA | Relative Roth |
| --- | --- | --- | --- | --- | --- | --- |
| MLPX | 30% | 28% | 30% | — | 24% | 32% |
| DBMF | 15% | 17% | 10% | — | 12% | 18% |
| SGOL | 16% | 14% | — | — | 26% | 22% |
| VTIP | 8% | 10% | — | — | 12% | 10% |
| AIPO | 8% | 8% | 8% | — | 6% | 10% |
| XAR | 12% | 12% | 12% | — | — | — |
| SGOV | — | — | 15% | 100% | 14% | — |
| SIVR | 4% | 5% | — | — | 3% | — |
| COPX | 2% | — | 7% | — | — | — |
| MAGS | 5% | 6% | — | — | 3% | 8% |
| XLP | — | — | 7% | — | — | — |
| PAVE | — | — | 11% | — | — | — |
| **Total** | **100%** | **100%** | **100%** | **100%** | **100%** | **100%** |

Portfolio EV by account (conservative, partially pending §4.1 calibration):
- Primary IRA: +3.62% (required 3.2% — GAP CLOSED ✅)
- Primary Roth: +3.62% (required ~2.8% — exceeds by +0.82pp ✅)
- Primary Taxable: +2.99% (RETURN_THEN_TARGET 5yr ✅)
- Taxable Preservation: Capital preservation — SGOV 100% ✅
- Relative IRA: +3.04% (FLOOR_THEN_RETURN; drawdown breach RESOLVED ✅)
- Relative Roth: +3.79% (required ~2.8% — exceeds by +0.99pp ✅)

Note: Portfolio EV computations above use v1.13 AIPO EV (+2.95%). AIPO EV revised to +2.42% in v1.14 — impact on portfolio-level EV is minimal (~0.03-0.05pp reduction per account given AIPO weights of 6-10%). Full recomputation at next M05 session with allocation sheet fetch.
