# Calibration State

Persistent framework configuration — load at every session start alongside Session Log.

Version: 1.19  Last updated: May 25, 2026 (Full M05 session — §12 M17 thresholds pushed; probabilities updated A=7/B=36/C=41/D=5/E=4/F=7; D/E uplift reflects M17 CascadeLevel ALERT; C-trigger clock Day 0 confirmed; EVs updated throughout; portfolio ~$775k)  Next scheduled review: June 30, 2026 (Q2 2026 quarter-end)

**File split as of v1.12:**
- Session observations (§7) and session state (§8) now live in **Session_Log.md** (fetched concurrently at session start).
- Prior calibration history before last-10 entries lives in **Calibration_Log.md**.
- This file (Calibration_State.md) is the LIVE CONFIG — kept lean for reliable write-back.

---

## Load Verification Requirement

At session start, after both files are fetched, the advisor must state in the briefing:

"Calibration State loaded, last update: May 25, 2026 | Session Log loaded"

Absence of either confirmation line indicates the respective file was not loaded and the session is invalid for threshold-sensitive decisions.

After loading: run M15.ValidateClassifications() — all instruments in the allocation file must have §11 entries before session proceeds to analysis.

---

## Section 1 - Credit Signal Thresholds (relative, 1.5a)

All HY/CCC/IG thresholds are relative to the trailing 180-day median of the underlying FRED series, computed at session start.

**Approved source URLs (confirmed May 11, 2026):**
- HY: https://fred.stlouisfed.org/data/BAMLH0A0HYM2
- IG: https://fred.stlouisfed.org/data/BAMLC0A0CM
- CCC: https://fred.stlouisfed.org/data/BAMLH0A3HYC
- MOVE: https://www.investing.com/indices/ice-bofaml-move | https://finance.yahoo.com/quote/%5EMOVE/

**FRED data availability (v1.17):** FRED series now embedded directly in allocation spreadsheet (new tab added May 13, 2026). Three series confirmed as CCC (BAMLH0A3HYC), HY (BAMLH0A0HYM2), IG (BAMLC0A0CM) by cross-referencing known session values. T1 data available at each session fetch via GOOGLEFINANCE-linked spreadsheet. MOVE index tab also present — reference separately.

Note: FRED /data/ endpoint may return HTML wrapper in some fetch contexts. If web_fetch returns HTML rather than raw data, use allocation spreadsheet tab as T1 source (confirmed May 13). Screenshots from client are acceptable T1 backup.

### 1.1 HY Composite - FRED: BAMLH0A0HYM2

| Parameter | Current Value | Type | Notes |
| --- | --- | --- | --- |
| HY_STRESS_DELTA | +150 bps | Calibration-dated | Provisional initial - full audit pending June 30, 2026 |
| HY_RECESSION_DELTA | +300 bps | Calibration-dated | Provisional initial - full audit pending June 30, 2026 |
| Velocity overlay | +100 bps over prior 60 days | Fixed structural | Not calibration-dated |
| Sustain period | 10 trading days | Fixed structural | Not calibration-dated |
| D-floor on recession-pricing trigger | 25% | Fixed structural | Not calibration-dated |

Baseline snapshot at instantiation (April 19, 2026): ~285 bps. Trailing 180d median to be computed at Q2 2026 audit.

Session observation (May 22 full session): HY **278 bps** (FRED T1 — BAMLH0A0HYM2, May 21 close, via embedded spreadsheet tab). −4 bps from May 12. HY_StressBeginning ~435 bps; gap 157 bps. Tightening continues. NO THRESHOLD FIRES.
Session observation (May 25 full session): HY **278 bps** (carry — FRED T1, May 21 close; May 25 = Memorial Day, no new data). Gap 157 bps. NO THRESHOLD FIRES.

### 1.2 IG Composite - FRED: BAMLC0A0CM

| Parameter | Current Value | Type | Notes |
| --- | --- | --- | --- |
| IG_TRANSMISSION_DELTA | +60 bps | Calibration-dated | Provisional initial - full audit pending June 30, 2026 |
| Velocity overlay | +40 bps over prior 60 days | Fixed structural | Not calibration-dated |
| Sustain period | 10 trading days | Fixed structural | Not calibration-dated |

Session observation (May 22 full session): IG **75 bps** (FRED T1 — BAMLC0A0CM, May 21 close, via embedded spreadsheet tab). −2 bps from May 12. IG_TransmissionReached threshold ~143 bps; gap 68 bps. NOT FIRED. Continued tightening.
Session observation (May 25 full session): IG **75 bps** (carry). Gap 68 bps. NOT FIRED.

### 1.3 CCC Tail - FRED: BAMLH0A3HYC

| Parameter | Current Value | Type | Notes |
| --- | --- | --- | --- |
| Ratio divergence | CCC widens 3x composite over 30d | Fixed structural | Not calibration-dated |
| Absolute divergence floor | CCC +200 bps while composite +<50 bps over 30d | Calibration-dated | Provisional - audit pending June 30, 2026 |

Session observation (May 22 full session): CCC **939 bps** (FRED T1 — BAMLH0A3HYC, May 21 close, via embedded spreadsheet tab). +2 bps from May 12. 30d divergence: CCC +2 bps vs HY −4 bps (HY tightening; ratio check moot when HY tightening). Absolute divergence floor: NOT fired (+200 bps required). CCC_TailFirstWidening NOT triggered.
Session observation (May 25 full session): CCC **939 bps** (carry). NOT triggered. ⚠ Quiet re-widening noted: +2 bps while HY tightening — watch for divergence acceleration.

---

## Section 2 - Other Calibration-Dated Thresholds

### 2.1 Energy / Commodities

| Threshold | Current Value | Source | Audit Status |
| --- | --- | --- | --- |
| WTI floor - SGOL invalidation | $55 nominal OR 30% below 90d trailing WTI avg | Calibration-dated | Pending June 30 |
| Brent trigger - Scenario C | $110 nominal OR 40% above 90d trailing Brent avg | Calibration-dated | Pending June 30 |
| Brent invalidation - Scenario C | $80 nominal OR 20% below 90d trailing Brent avg | Calibration-dated | Pending June 30 |

**Canonical Brent price source (established v1.17): BZ=F (ICE front-month futures, Yahoo Finance). Fortune T2 daily spot references rejected as clock reference after source discrepancy confirmed May 13 (Fortune $110+ vs BZ=F $105.71 for May 12 close). All future C-trigger clock determinations use BZ=F closing price.**

Session observations:
- April 19–May 12: [See prior entries in §3 calibration log]
- May 22 full session: BZ=F pre-market ~$109.11 (T2, Yahoo Finance, 6:10am EDT, declining −1.95%). C-TRIGGER CLOCK STATUS UNRESOLVED at session close. Brent 52-week high = $126.41 confirmed (Investing.com); achieved between May 13 and May 22. BZ=F daily closes May 14-21 not confirmed from approved source.
- May 25 full session: **C-TRIGGER CLOCK: DAY 0 — RESOLVED (T2).** Reconstruction of BZ=F trajectory using Trading Economics CFD differential and Yahoo Finance pre-market: max consecutive days at or above $110 ≈ 5–6 (approx. May 13–19); price dropped below $110 around May 20 when CFD fell 5.66% to ~$105. 10-day requirement NOT met. BZ=F Sunday night pre-market (Memorial Day): **~$107.60** (Yahoo Finance T2, 1:32am EDT). Day 0 confirmed. ⚠ BZ=F daily closes May 14–19 remain T2-estimated; not confirmed from approved source; flag for T1 confirmation if clock restarts near $110.
- SGOL WTI floor ($55): WTI ~$97–101 est. comfortably clear. DXY ~99 carry, below 105. No SGOL invalidation risk.

### 2.2 Currency

| Threshold | Current Value | Audit Status |
| --- | --- | --- |
| DXY sustained above - SGOL invalidation | 105 nominal | Pending June 30 |

DXY ~99 (carry). Below 105. No SGOL invalidation risk.

### 2.3 Macro

| Threshold | Current Value | Audit Status |
| --- | --- | --- |
| CPI trigger - Scenario B | 4% YoY, 3+ consecutive prints | Pending June 30 |
| CPI invalidation - Scenario B | below 3% YoY, 2+ consecutive prints | Pending June 30 |
| GDP trigger - Scenario F | above 3% annualized, 2+ consecutive quarters | Pending June 30 |
| GDP invalidation - Scenario F | below 2% on BEA advance estimate | Pending June 30 |
| Unemployment trigger - Scenario D | +0.5% over any 3-month window | Pending June 30 |

May 25 full session: No new CPI or GDP since May 13. **CPI B trigger status: print 2 of 3 (March 3.3%, April 3.8%). May CPI print mid-June is the binary event: if ≥4.0% → B formal trigger fires.** FOMC holding 3.50–3.75%. Q1 GDP +2.0% (positive). Sahm Rule 0.20. Term premium (THREEFYTP10): 0.8117% (May 15 — 14-yr high, rising). 30Y yield: 5.07% (approaching M17 §12.5 warning level). Yield curve 10Y–2Y +43bp; 10Y–3M +88bp — post-inversion re-steepening = D_timing_signal RECESSION_ONSET_PATTERN.

---

## Section 3 - Calibration Log (last 10 entries; prior entries in Calibration_Log.md)

2026-05-25 - Full M05 session (v1.19). **§12 M17 thresholds pushed** (first formal action this session). Scenario probabilities updated: A=7%(unch), B=36%(unch), C=41%(−3pp), D=5%(+2pp), E=4%(+1pp), F=7%(unch) — D/E uplift reflects M17 CascadeLevel ALERT (formal sectorStressScore=2: CHAIN_3 margin debt $1.304T all-time record + gate events; CHAIN_4 corporate bankruptcies 14-yr high qualitative; D_timing_signal=RECESSION_ONSET_PATTERN post-inversion yield curve re-steepening; THREEFYTP10=0.8117% 14-yr high). Credit T1 carry (May 21): HY=278, IG=75, CCC=939 — all thresholds clear; CCC quiet re-widening (+2 bps) vs HY tightening noted. BZ=F C-trigger clock: **Day 0 confirmed** — max ~5–6 consecutive days ≥$110 (approx. May 13–19); reset ~May 20; 10-day requirement NOT met (T2 reconstruction; BZ=F May 14–19 T1 pending). BZ=F Sunday night ~$107.60 (T2). MOVE=78.43, VIX=16.70, S&P=7,473.47 (May 22 close). Memorial Day — US markets closed; S&P futures overnight −2.7% (7,268.25) — watch Tuesday open. M14 composite: HIGH (unchanged). EVs updated throughout §11 at new probability vector. Portfolio ~$775k; all accounts within ±2pp of v1.18 targets; no rebalancing required.

2026-05-22 - Full M05 session (v1.18). Gold reallocation CONFIRMED EXECUTED — Relative IRA and Relative Roth allocation sheet targets match v1.17 recommendations exactly. Targets updated: Relative IRA SGOL 26%→20%, SIVR 3%→6%, DBMF 12%→15%; Relative Roth SGOL 22%→16%, SIVR new 4%, DBMF 18%→20%. Relative IRA EV: +3.53%→+3.89% (+0.36pp); Relative Roth EV: +4.45%→+4.73% (+0.28pp). FRED T1 credit (May 21 close via embedded spreadsheet tab): HY=278 bps (−4 from May 12), IG=75 bps (−2), CCC=939 bps (+2) — all thresholds clear. MOVE=79.72 (GOOGLEFINANCE, rising +9.0 pts from 70.74 on May 11 — approaching 80; no formal threshold yet; flag for Q2 formal integration). VIX=16.52, S&P=7,494.81. BZ=F pre-market ~$109.11 (T2, Yahoo Finance) — C-trigger clock STATUS UNRESOLVED (Brent 52-wk high $126.41 achieved between May 13 and May 22; BZ=F daily closes May 14-21 not confirmed; clock may have started and reset; requires verification at next session). Geopolitical: Iran + Oman "Persian Gulf Strait Authority" (permanent Hormuz toll system; Trump rejected — new structural C escalation); Iran uranium directive hardened (counter-deal T1 via Reuters); Rubio "encouraging signs" (soft A-signal, T1 unconfirmed); SPR ~10M barrel release (largest on record, T2). Probabilities: carry forward A=7/B=36/C=44/D=3/E=3/F=7 — no new binary events warranting re-derive. Main session: rebalancing strategy analysis — sell-winners/buy-losers thesis; conclusion: EV-optimal targets should update with scenario probabilities, not mechanically revert price drift; 1-2pp current drifts below all action thresholds. Secondary: AI capex sustainability; private credit AI; prisoner's dilemma analysis; hyperscaler knowledge asymmetry. No allocation changes.

2026-05-13 - Full M05 session (v1.17). CPI April 2026 = 3.8% YoY (BLS T1) — C check_cpi 1→2; C raw 5→6. Scenario probabilities updated: A=7%(−5pp), B=36%(−1pp), C=44%(+6pp), D=3%(unch), E=3%(unch), F=7%(unch). MLPX EntryExtensionGuard CLEARED: 90d avg $72.31 (Feb 5 close $66.54, client-confirmed T2); threshold $86.77; current $74.40 (+2.9% above avg — well below 20%). WAR PREMIUM ENTRY GUARD also CLEARED (same threshold). BZ=F established as canonical Brent session reference (Fortune spot rejected after $3-4 discrepancy confirmed). FRED credit data via embedded spreadsheet tab (T1, May 12 close): HY=282, IG=77, CCC=937 — no thresholds fired. Gold reallocation recommended for relative accounts (Rel IRA: SGOL 26%→20%, SIVR 3%→6%, DBMF 12%→15%; Rel Roth: SGOL 22%→16%, SIVR new 4%, DBMF 18%→20%) — EV improvement +0.36pp/+0.28pp respectively — pending client execution. Portfolio total ~$775k.

2026-05-11 - Full M05 session (v1.16). Scenario probabilities updated: A=12%(-3pp), B=37%(+1pp), C=38%(+2pp), D=3%(unch), E=3%(unch), F=7%(unch). check_energy reverted to 0 (Brent $107.67 rising; May 8 day-5 check FAILED — streak reversed up; Saudi Aramco CEO T1 conference call May 11: normalization into 2027 even if Hormuz opened today). FRED DATA GAP RESOLVED — first T1 credit readings in multiple sessions: HY=281 bps, IG=79 bps, CCC=920 bps (all May 8 close via FRED screenshots). MOVE=70.74 T1 confirmed (NYSE Global Indexes). Approved FRED+MOVE source URLs logged in §1. All v1.13 trades confirmed executed per allocation sheet (all 6 accounts at targets ±1pp). Portfolio total ~$769k (+$7k vs May 7 on price appreciation). No allocation changes this session. CPI May 12 binary event pending — run DeriveScenarioProbabilities() immediately on 8:30am ET release.

2026-05-07 - AIPO reclassification + guard clearance (v1.14). Session type: ad-hoc analysis (no allocation fetch — full M05 session required for share count targets). AIPO ThematicETF_ClassificationAudit() COMPLETE. Holdings confirmed from T1 sources: Industrials 50%, IT 30%, Utilities 20%. Top holdings: Quanta Services 8.6%, GE Vernova 8.2%, Eaton 7.9%, Vertiv 7.9%, NVDA 4.2%, AVGO 3.9%, AMD 2.1%. Revised components: RAC 0.55→0.45; STG 0.20→0.30; BMD 0.15→0.00 (ELIMINATED — no qualifying undifferentiated domestic equity; all holdings have specific AI/power binding drivers); new PDT 0.20; IHC 0.10→0.05. CORRECTION: prior session analysis (May 7 ad-hoc) erroneously stated "B improves" — WRONG. Actual revised AIPO EV = +2.42% (↓ from +2.95%), rank drops to #5 (below SIVR +2.86%). EV reduction driven by PDT B conservative = -3% and more STG weight at B = -6%. A-regime improves: +4.05% (↑ from +3.80%) due to STG A = +6% and PDT A = +4%. SIVR entry guard CLEARED: confirmed price anchors (March 14 = $76.31, March 26 = ~$63.64, April 2 = $69.11, April 24 = $72.28, May 6 = $73.79); 90d avg ~$78-82; threshold ~$94-98; current $73.79 below threshold. v1.13 estimated avg ($55-65) was incorrect — all confirmed data points above $63. COPX entry guard CLEARED: confirmed anchors (Feb 6 = $81.31, April 28 = $78.69, May 6 = $78.21); 90d avg ~$85-90; threshold ~$102-106; current $78.21 below threshold. v1.13 estimated avg ($55-65) was significantly incorrect — Feb 6 anchor $81.31 alone exceeds entire estimated range. Execution notes updated: SIVR and COPX now immediate. AI application layer instrument screen conducted: no M07-compliant pure-play instrument available (track record and/or AUM constraints). NVDA overlap noted: AIPO holds NVDA 4.2%, AVGO 3.9%, AMD 2.1% — partial overlap with MAGS. Monitor at Q2.

2026-05-07 - Full M05 session (v1.15). Scenario probabilities updated: A=15%(-3pp), B=36%(+1pp), C=36%(+2pp), D=3%(unch), E=3%(unch), F=7%(unch). check_energy=1 this session (Brent declining 4 consecutive days vs ≥5 threshold). CPI May 12 binary event upcoming — highest priority. M14 composite HIGH unchanged. M16 analysis: secular_technology_growth Scenario B full 4-layer run completed; MEDIUM confidence; upward pending proposal logged (§6 item 35). Primary Taxable deployment complete: DBMF 854sh, XLP 196sh, COPX 212sh executed; $51,950 cash fully deployed (Open Decision #4 CLOSED). v1.13 targets confirmed live in allocation file; remaining trades executing through May 8. Portfolio total ~$762,097.

2026-05-06 - Comprehensive instrument expansion (v1.13). Probability update: A=18%(+3pp), B=35%(-1pp), C=34%(-2pp), D=3%, E=3%, F=7%. Full M14 ComputeDivergenceSignal: composite HIGH (equity_scenario_divergence HIGH at S&P 30d +10.3%). XAR confirmed sold to 12% target across all accounts — Open Decision #2 CLOSED. Five new roles added to §11.1: systematic_trend_following, consumer_defensive_equity, healthcare_defensive_equity, floating_rate_credit_income, emerging_market_equity. §4.1 return table fully calibrated for all roles using M16.CalibrationMethodology() 4-layer procedure. ADOPTED (HIGH confidence): systematic_trend_following A/B/C values; consumer_defensive_equity B value. Nine new instruments classified in §11.3: DBMF, SIVR, COPX, VTIP, XLP, VNQ, VEA, XLV, FLOT. Primary IRA structural gap RESOLVED: achievable EV +3.62% with DBMF adoption (required: 3.2%). MLPX EntryExtensionGuard preliminary analysis: guard may be clearing (estimated 90d avg ~$66; current $73.63 ~12% above avg vs 15% threshold). Verification from approved price source required before ADD executes. New target allocations issued for all 6 accounts. Relative IRA MLPX drawdown breach RESOLVED by reducing target to 24% (24% × 67% = 16.1% < 20% floor). MOVE index: ~76.8 (TradingView T2). Brent close: $101.27. S&P 500 record high: +1.46%.

2026-05-06 - Architecture session (v1.12). File split implemented: §7 and §8 moved to Session_Log.md; §3 entries 1-4 archived to Calibration_Log.md. M16_ReturnTableCalibration.md authored (governs §4.1 revision methodology). M12, M05, 00_INDEX updated for two-file session protocol. New roles added to §11.1 and §4.1: inflation_linked_sovereign and real_estate_equity_income (LOW confidence, [TBD] values, pending June 30 empirical audit). No portfolio analysis this session.

2026-05-06 - Returns table empirical overhaul initiated (v1.11). Full methodology framework documented. Historical scenario-to-analogue mapping established. ADOPTED: real_asset_contracted_revenue B [3,7]→[6,14] and C [3,6]→[8,16]. Empirical basis: AMZI total return 2022 +31.4% nominal. MLPX §11 EV updated: +3.64%→+5.51%. Fourteen additional revision proposals logged in §6 item 23.

2026-05-06 - Full M05 session (v1.10). C-trigger clock broken Day 5 (May 5 close ~$109.87, CNBC T1). Scenario probabilities updated: A=15%(+8pp), B=36%(-6pp), C=36%(-6pp), D=3%(unch), E=3%(unch), F=7%(+4pp). AIPO §11 updated: AUM $457M. PAVE watch status confirmed. MLPX EntryExtensionGuard blocking. M14 composite divergence: MODERATE.

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

Weighted target (A=7/B=36/C=41/D=5/E=4/F=7) = 0.07×2.0+0.36×1.3+0.41×1.3+0.05×1.3+0.04×1.2+0.07×2.0 = 1.394x. Required ~3.38%. Achievable EV Primary IRA = +4.03% (updated v1.19) — exceeds required by +0.65pp. ✅ Gap remains closed.

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

Weighted multiplier (A=7/B=36/C=41/D=5/E=4/F=7) = 0.07×3.1+0.36×1.3+0.41×1.3+0.05×1.6+0.04×1.4+0.07×3.1 = 1.571x. Required ~3.05%. Achievable Primary Roth = +4.08% (updated v1.19). Exceeds by +1.03pp. ✅

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
| 2026-06-30 | Q2 first full audit | All calibration-dated thresholds; section 4 return table and multipliers; M14/M10/M15 thresholds; restore multipliers if commodity-linked added post-war; AIPO ThematicETF_ClassificationAudit — COMPLETE v1.14 (§11 revised; EV +2.16% at v1.19 probs; confirm at Q2 for weight drift); AIPO/PAVE ETN overlap check; MOVE index integration assessment — MOVE at 78.43 as of May 25 (elevated; formal threshold pending); MAGS vs AGIX reassessment if Anthropic IPO announced; secular_technology_growth empirical validation; formal adoption of §6 item 23 pending proposals; populate all PENDING §4.1 values (M16.CalibrationMethodology() 4-layer required for all MEDIUM/LOW confidence cells); resolve real_estate_equity_income leverage-adjusted calibration; COPX M07 regional ruling formal confirmation; URA full M07+M15 evaluation; SIVR+COPX entry guard 90d trailing price computation — CLEARED v1.14; DBMF D/E/F formal adoption; Brent C-trigger clock threshold review; PAVE IIJA reauthorization assessment (Sep 30 deadline approaching); M17 §12 first formal audit and threshold calibration |
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
18. MOVE index: assess formal integration into M11/M14 as supplementary credit/volatility signal. MOVE at 78.43 as of May 25 (elevated but below 80 threshold watch). Approved source URLs confirmed May 11 (§1). Allocation spreadsheet MOVE tab confirmed. If MOVE sustained above 100 before Q2, accelerate formal integration. Q2 audit: establish formal MOVE threshold and integrate into M14/M11 signal framework.
19. Add Fed response function sub-variable to Scenario C scoring (design proposal Apr 29).
20. Record all results in section 3 calibration log.
21. AIPO Financial Services weight (3.60% as of Apr 30): assess materiality for classification. Flag if above 5% by Q2 audit.
22. MLPX target allocation: Relative IRA formally reduced to 24% (drawdown breach resolved v1.13). Primary accounts per new consolidated targets. Relative Roth at 32%. Document final decisions in §11 MLPX entry.
23. RETURNS TABLE PENDING REVISION PROPOSALS (logged May 6, 2026 — formal adoption requires June 30 audit): [14 proposals listed in prior v1.12 §6 item 23 — all carry forward unchanged].
24. Implement living update protocol: now formally governed by M16_ReturnTableCalibration §5. Confirm June 30 as first formal application of M16 §5 LivingUpdateTriggers.
25. Session_Log.md compaction: retain last 10 §7 credit rows; collapse §8 to last 3 full entries + summary table. Move prior entries to Archive_2026Q2.md.
26. COPX M07 regional concentration ruling: confirm "region = political/economic bloc" ruling from v1.13 as formal framework policy. Apply consistently to all future M07 screens.
27. URA (Global X Uranium ETF): full M07 screen + M15 classification. Proposed role composition: real_asset_contracted_revenue (0.50) + inflation_hedge_commodity_linked (0.30) + secular_technology_growth (0.20). Verify Canada concentration passes 40% threshold (URNM failed at 60.5%; URA expected to pass). Add to §11 if passes.
28. SIVR entry guard computation — COMPLETE v1.14 (May 7, 2026). CLEARED. 90d avg ~$78-82; threshold ~$94-98; current $73.79 < threshold.
29. COPX entry guard computation — COMPLETE v1.14 (May 7, 2026). CLEARED. 90d avg ~$85-90; threshold ~$102-106; current $78.21 < threshold.
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
36. GOOGLEFINANCE ticker setup (v1.17): New allocation spreadsheet tab added for market data "Other Indexes". Confirmed working: VIX (INDEXCBOE:VIX), S&P 500 (INDEXSP:.INX), MOVE (INDEXNYSEGIS:MOVE). FRED series: use existing spreadsheet "FRED Series" tab. BZ=F is canonical Brent reference for C-trigger clock per v1.17.
37. AI capex / secular_technology_growth context note (v1.18, May 22, 2026): Session intelligence — hyperscaler AI capex $660-830B committed for 2026 (nearly doubling 2025). Capex intensity 45-57% of revenue (vs 10-15% in 2020). Revenue growth 15-16% vs capex growth 60-80%; FCF projected to decline 90% across Big Four. Private credit ($800B+ in AI infrastructure financing) opacity flagged as tail risk not visible in HY/IG spread series. AI utility pricing emerging (62% usage-based by 2027). Prisoner's dilemma / war-of-attrition structure confirmed: no coordination mechanism among 5+ hyperscalers; 18-36 month infrastructure commitment periods prevent exit. Fiber optic 1999 analogy: technology correct, equity returns poor due to timing, cost of capital, and competitive dynamics. Portfolio implication: AIPO (infrastructure layer, contracted revenue) positive EV in B/C; MAGS (hyperscaler equity) negative EV in B/C — distinction maintained. No §4.1 changes warranted from session analysis.
38. M17 §12 thresholds (v1.19): First application May 25, 2026. sectorStressScore()=2 (formal). CascadeLevel=ALERT. PAVE exit window review triggered per M17 §5 (CascadeLevel ALERT + PAVE FLAGGED). D_precursor_binding=2 (formal) / 3 (qualitative). Formal Q2 audit: calibrate all §12 thresholds; confirm CHAIN_4 count; assess CHAIN_1 USDA quarterly; formal integration of yield curve D_timing_signal into M03 scoring function.

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

May 25 full session M14 computation: commodity_fear_divergence = HIGH (energy_90d ~+55%; VIX_change_90d ~−1 to −4 pts ≤0). equity_scenario_divergence = HIGH (S&P 30d ~+5.3%; B/C directive reductive). Composite = HIGH (unchanged). UnderweightReviewTrigger: NOT fired (max drift = Relative Roth MLPX +1.71pp; all accounts below 5pp threshold).

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
| 2026-05-07 | AIPO | ThematicETF_ClassificationAudit | COMPLETE v1.14. Holdings confirmed: Industrials 50%, IT 30%, Utilities 20%. Top holdings: Quanta Services 8.6%, GE Vernova 8.2%, Eaton 7.9%, Vertiv 7.9%, NVDA 4.2%, AVGO 3.9%, AMD 2.1%. Revised components: RAC(0.45), STG(0.30), PDT(0.20), IHC(0.05). BMD ELIMINATED. NVDA/AVGO/AMD overlap with MAGS flagged. | REVISED: see §11 AIPO entry. EV: +2.16% at v1.19 probs (↓ from +2.42%). Ranked #5. Confirm at Q2 for weight drift. |

---

## Section 11 - Instrument Classification Registry (M15)

All values CALIBRATION_DATED. First audit: June 30, 2026.
VTI, XAR, MLPX, SGOL, SGOV, PAVE added Apr 28 (v1.7). AIPO, MAGS added Apr 30 (v1.9). AIPO §11 data updated May 6 (v1.10). MLPX EV updated May 6 (v1.11). New roles inflation_linked_sovereign and real_estate_equity_income added May 6 (v1.12). Five new roles added May 6 (v1.13): systematic_trend_following, consumer_defensive_equity, healthcare_defensive_equity, floating_rate_credit_income, emerging_market_equity. New instruments added May 6 (v1.13): DBMF, SIVR, COPX, VTIP, XLP, VNQ, VEA, XLV, FLOT. AIPO reclassified May 7 (v1.14): ThematicETF_ClassificationAudit() COMPLETE. MLPX entry guards CLEARED May 13 (v1.17). Gold reallocation targets confirmed executed May 22 (v1.18). EVs updated at new probability vector May 25 (v1.19): A=7/B=36/C=41/D=5/E=4/F=7.

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
- EV (A=7/B=36/C=41/D=5/E=4/F=7): **+1.46%** (updated v1.19; prior at C=44: +1.65%).
  - A: (0.90×(-2)+0.10×5)×0.07 = -1.30×0.07 = -0.091%
  - B: (0.90×2+0.10×(-8))×0.36 = 1.00×0.36 = +0.360%
  - C: (0.90×4+0.10×(-4))×0.41 = 3.20×0.41 = +1.312%
  - D: (0.90×(-4)+0.10×(-12))×0.05 = -4.80×0.05 = -0.240%
  - E: (0.90×1+0.10×(-8))×0.04 = 0.10×0.04 = +0.004%
  - F: (0.90×1+0.10×7)×0.07 = 1.60×0.07 = +0.112%
  - Total: +1.457% ≈ +1.46%. Ranked #6.
- Target: 12% structural across applicable accounts (Primary IRA, Primary Roth, Taxable Acc4). CONFIRMED AT TARGET.
- Client preference: exit excess XAR at ~$265 on a conflict-resumption spike. EXECUTED — reduction to 12% confirmed via allocation sheet May 6.
- HoldJustification: break-even peace probability <5.6%; opportunity cost vs MLPX -4.21%/year (at v1.19 probs).
- ⚠ Deal trajectory (A rising): geopolitical_premium A return proposed revision to [-6,0] pending June 30. If adopted, XAR EV would decline further.

#### MLPX
- Components: real_asset_contracted_revenue (0.65) + inflation_hedge_commodity_linked (0.35)
- Last reviewed: 2026-05-13 (v1.17 — entry guards CLEARED)
- EV (A=7/B=36/C=41/D=5/E=4/F=7): **+5.67%** (updated v1.19; prior at C=44: +5.91%). Ranked #2.
  - A: (0.65×3+0.35×2)×0.07 = 2.65×0.07 = +0.186%
  - B: (0.65×6+0.35×6)×0.36 = 6.00×0.36 = +2.160%
  - C: (0.65×8+0.35×7)×0.41 = 7.65×0.41 = +3.137%
  - D: (0.65×2+0.35×(-8))×0.05 = -1.50×0.05 = -0.075%
  - E: (0.65×2+0.35×2)×0.04 = 2.00×0.04 = +0.080%
  - F: (0.65×3+0.35×2)×0.07 = 2.65×0.07 = +0.186%
  - Total: +5.674% ≈ +5.67%.
- Target allocation (v1.13 consolidated targets):
  - Primary IRA: 30%
  - Primary Roth: 28%
  - Primary Taxable: 30%
  - Relative IRA: 24% (REDUCED from 35% — drawdown tolerance breach resolved: 24% × 67% = 16.1% < 20% floor)
  - Relative Roth: 32%
- EntryExtensionGuard: **CLEARED (v1.17, May 13, 2026).** 90d trailing average: **$72.31**. Guard threshold (20% above avg): **$86.77**. Current price (May 22): **$77.33** (+6.9% above avg — well below 20% threshold). ADD eligible in all accounts.
- WAR PREMIUM ENTRY GUARD: **CLEARED (v1.17, May 13, 2026).** Same threshold: $86.77. Current $77.33 < $86.77. ADD eligible.
- Drawdown tolerance: Relative IRA target reduced to 24% per drawdown analysis (see §6 item 22).

#### SGOL
- Components: inflation_hedge_precious_metals (1.00)
- Last reviewed: 2026-04-28
- CALIBRATION ANOMALY RESOLVED Apr 30 (v1.8): §4.1 Scenario C revised [+7%,+14%]->[-2%,+6%]. C-hawk regime empirical basis.
- EV (A=7/B=36/C=41/D=5/E=4/F=7): **+1.43%** (updated v1.19; prior at C=44: +1.31%; E weight increase improved SGOL as E conservative = +10%). Ranked #7.
  - A: 0%×0.07 = 0%
  - B: 6%×0.36 = +2.160%
  - C: (-2%)×0.41 = -0.820%
  - D: (-2%)×0.05 = -0.100%
  - E: 10%×0.04 = +0.400%
  - F: (-3%)×0.07 = -0.210%
  - Total: +1.430%.
- Target allocation (v1.18 CONFIRMED):
  - Primary IRA: 16%
  - Primary Roth: 14%
  - Relative IRA: 20% (CONFIRMED EXECUTED v1.18 — reduced from 26%)
  - Relative Roth: 16% (CONFIRMED EXECUTED v1.18 — reduced from 22%)
  - Note: SIVR added as complement; SGOL + SIVR combined restores precious metals exposure
- ⚠ Pending June 30 proposals: A [0,4]→[-2,2] and D [-2,4]→[-5,3].

#### SGOV
- Components: rate_sensitive_income_short_duration (1.00)
- Last reviewed: 2026-04-28
- EV (A=7/B=36/C=41/D=5/E=4/F=7): **+0.76%** (updated v1.19; prior: +0.81%). Ranked #9.
  - A: 0%×0.07=0; B: 1%×0.36=+0.360; C: 1%×0.41=+0.410; D: 0%×0.05=0; E: (-2%)×0.04=-0.080; F: 1%×0.07=+0.070
  - Total: +0.760%.
- Target allocation (v1.13):
  - Primary Taxable: 15%
  - Taxable Preservation: 100%
  - Relative IRA: 14%
- ⚠ Pending June 30 proposals: A [0,2]→[1,4] and D [0,3]→[2,6].

#### PAVE
- Components: broad_market_equity_domestic (0.82) + policy_driven_thematic_equity (0.18)
- ThematicETF_ClassificationAudit conducted Apr 28. Status: watch (not FLAGGED).
- Last reviewed: 2026-05-06 (status reconfirmed — no new legislation; IIJA core programs intact)
- Cost basis: $54.09/share. Current: $54.94/share (May 22). Embedded gain: ~$427 on 502 shares (essentially breakeven). Target: ~11% in Taxable Acc4. Currently 10.39%.
- **M17 CascadeLevel ALERT (v1.19): exit window review ACTIVATED per M17 §5.** PAVE FLAGGED + CascadeLevel ALERT creates converging exit argument. Review during this session.
- EV (A=7/B=36/C=41/D=5/E=4/F=7): approximately **−4.03%** (updated v1.19; worse at higher D/E; prior: −3.84%).
  - A: (0.82×5+0.18×4)×0.07 = 4.82×0.07 = +0.337%
  - B: (0.82×(-8)+0.18×(-3))×0.36 = -7.10×0.36 = -2.556%
  - C: (0.82×(-4)+0.18×(-1))×0.41 = -3.46×0.41 = -1.419%
  - D: (0.82×(-12)+0.18×(-5))×0.05 = -10.74×0.05 = -0.537%
  - E: (0.82×(-8)+0.18×(-6))×0.04 = -7.64×0.04 = -0.306%
  - F: (0.82×7+0.18×4)×0.07 = 6.46×0.07 = +0.452%
  - Total: -4.029% ≈ −4.03%.
- Monitor IIJA reauthorization September 30, 2026.

#### AIPO
- Components: real_asset_contracted_revenue (0.45) + secular_technology_growth (0.30) + policy_driven_thematic_equity (0.20) + inflation_hedge_commodity_linked (0.05)
- CLASSIFICATION REVISED v1.14 (May 7, 2026): ThematicETF_ClassificationAudit() COMPLETE. Prior v1.13 classification included broad_market_equity_domestic (0.15) — ELIMINATED.
- Basis: Defiance AI & Power Infrastructure ETF. Tracks MarketVector US Listed AI & Power Infrastructure Index. Holdings must derive ≥50% revenue from AI hardware, data centers, or power infrastructure. 78 holdings. Confirmed sector breakdown: Industrials 50% (Quanta Services 8.6%, Eaton 7.9%), IT 30% (GE Vernova 8.2%, Vertiv 7.9%, NVDA 4.2%, AVGO 3.9%, AMD 2.1%), Utilities 20%. US-domiciled 90.1%, foreign 9.5%.
- AUM: ~$457M. Expense ratio: 0.69%. Inception: 07/24/2025 (thin track record — flag at Q2).
- ⚠ NVDA overlap: AIPO holds NVDA 4.2%, AVGO 3.9%, AMD 2.1%. MAGS holds NVDA (Magnificent 7). Partial overlap in AI chip layer. Manageable at current target weights — track for Q2 concentration review.
- ⚠ PAVE overlap: ETN (Eaton) in both AIPO (~8%) and PAVE (~3.4%). Audit at Q2 June 30.
- Last reviewed: 2026-05-07 (v1.14 — ThematicETF_ClassificationAudit() COMPLETE)
- EV (A=7/B=36/C=41/D=5/E=4/F=7): **+2.16%** (updated v1.19; prior at C=44: +2.42%). Ranked #5.
  - A:  0.45×3 + 0.30×6 + 0.20×4 + 0.05×2 = 4.05% × 0.07 = +0.284%
  - B:  0.45×6 + 0.30×(-6) + 0.20×(-3) + 0.05×6 = 0.60% × 0.36 = +0.216%
  - C:  0.45×8 + 0.30×2 + 0.20×(-1) + 0.05×7 = 4.35% × 0.41 = +1.784%
  - D:  0.45×2 + 0.30×(-14) + 0.20×(-5) + 0.05×(-8) = -4.70% × 0.05 = -0.235%
  - E:  0.45×2 + 0.30×(-10) + 0.20×(-6) + 0.05×2 = -3.20% × 0.04 = -0.128%
  - F:  0.45×3 + 0.30×4 + 0.20×4 + 0.05×2 = 3.45% × 0.07 = +0.242%
  - Total: +2.163% ≈ +2.16%
- TAX PLACEMENT: ALL ACCOUNTS including taxable.
- Target allocation (v1.13, unchanged): 8% Primary IRA; 8% Primary Roth; 8% Primary Taxable; 6% Relative IRA; 10% Relative Roth.

#### MAGS
- Components: secular_technology_growth (0.85) + broad_market_equity_domestic (0.15)
- Last reviewed: 2026-04-30
- EV (A=7/B=36/C=41/D=5/E=4/F=7): approximately **−2.17%** (updated v1.19; prior at C=44: −1.77%; deteriorating as D/E increase and C decreases). Ranked #11.
  - A:  (0.85×6+0.15×5)×0.07 = 5.85×0.07 = +0.410%
  - B:  (0.85×(-6)+0.15×(-8))×0.36 = -6.30×0.36 = -2.268%
  - C:  (0.85×2+0.15×(-4))×0.41 = 1.10×0.41 = +0.451%
  - D:  (0.85×(-14)+0.15×(-12))×0.05 = -13.70×0.05 = -0.685%
  - E:  (0.85×(-10)+0.15×(-8))×0.04 = -9.70×0.04 = -0.388%
  - F:  (0.85×4+0.15×7)×0.07 = 4.45×0.07 = +0.312%
  - Total: −2.168% ≈ −2.17%
- ⚠ EV deterioration: from −1.77% (C=44, D=3) to −2.17% (C=41, D=5). D scenario deeply negative (−13.70% blended) — increasing D weight amplifies drag. Override remains in force but EV trendline is worsening.
- Target allocation (v1.13): 5% Primary IRA; 6% Primary Roth; 3% Relative IRA; 8% Relative Roth.
- TAX PLACEMENT: RETIREMENT ACCOUNTS ONLY. Swap structure generates phantom taxable gains in losing years.
- MAGS vs AGIX upgrade evaluation: monitor Anthropic IPO news. Assess at Q3 2026 or earlier on announcement.

#### DBMF
- Components: systematic_trend_following (1.00)
- Basis: iMGP DBi Managed Futures Strategy ETF. Actively managed. Replicates top CTA hedge fund portfolios using T-bill collateral + equity/commodity/bond/currency swap agreements. Strategy: systematic trend-following across all major asset classes.
- K-1: NONE — 1940 Act registered fund (ETF structure). No K-1 issued.
- AUM: $3.51B. Expense ratio: 0.85%. Inception: 2019-05-08. 1-year total return: +27.3%.
- Last reviewed: 2026-05-06 (v1.13, initial classification)
- EV (A=7/B=36/C=41/D=5/E=4/F=7, D/E/F PENDING): **+11.02%** (updated v1.19; prior at C=44: +11.74%). Ranked #1.
  - A: -12% × 0.07 = -0.840%
  - B: +15% × 0.36 = +5.400% ★ADOPTED
  - C: +18% × 0.41 = +7.380% ★ADOPTED
  - D: -5% × 0.05 = -0.250% ⚑PENDING
  - E: -8% × 0.04 = -0.320% ⚑PENDING
  - F: -5% × 0.07 = -0.350% ⚑PENDING
  - Total: +11.020%
- TAX PLACEMENT: ALL ACCOUNTS. No K-1. No swap phantom gain issue.
- ENTRY EXTENSION GUARD: N/A — systematic_trend_following role is explicitly exempt (§9.3).
- KEY RISK: Trend-reversal events (Scenario A normalization) produce material losses (-12% conservative). A=7% weight creates -0.84% EV drag — priced into EV computation. DBMF and MLPX are partially inversely correlated in A (MLPX appreciates as energy normalizes; DBMF loses as commodity trends reverse) — portfolio diversification benefit.
- Target allocation (v1.18 CONFIRMED):
  - Primary IRA: 15%
  - Primary Roth: 17%
  - Primary Taxable: 10%
  - Relative IRA: 15% (CONFIRMED EXECUTED v1.18 — increased from 12%)
  - Relative Roth: 20% (CONFIRMED EXECUTED v1.18 — increased from 18%)

#### SIVR
- Components: inflation_hedge_precious_metals (0.55) + inflation_hedge_commodity_linked (0.45)
- Basis: Aberdeen Standard Physical Silver Shares ETF. Tracks spot silver price via physical silver bullion. Lower cost alternative to SLV (0.30% ER vs 0.50%)
- AUM: ~$5.5B. Expense ratio: 0.30%. Custodian: ICBC Standard Bank (UK).
- Last reviewed: 2026-05-07 (v1.14 — entry guard cleared)
- EV (A=7/B=36/C=41/D=5/E=4/F=7): **+2.92%** (updated v1.19; prior at C=44: +3.02%). Ranked #3.
  - A:  (0.55×0 + 0.45×2) = 0.90% × 0.07 = +0.063%
  - B:  (0.55×6 + 0.45×6) = 5.70% × 0.36 = +2.052%
  - C:  (0.55×(-2) + 0.45×7) = 2.05% × 0.41 = +0.841%
  - D:  (0.55×(-2) + 0.45×(-8)) = -4.70% × 0.05 = -0.235%
  - E:  (0.55×10 + 0.45×2) = 6.40% × 0.04 = +0.256%
  - F:  (0.55×(-3) + 0.45×2) = -0.75% × 0.07 = -0.053%
  - Total: +2.924% ≈ +2.92%.
- TAX PLACEMENT: Retirement accounts preferred. Physical silver ETF is classified as a collectible; capital gains taxed at 28% max rate in taxable accounts.
- ENTRY EXTENSION GUARD: CLEARED (v1.14, May 7, 2026). 90d trailing average ~$78-82; guard threshold ~$94-98; current ~$71.82 — well below threshold.
- Target allocation (v1.18 CONFIRMED):
  - Primary IRA: 4%
  - Primary Roth: 5%
  - Relative IRA: 6% (CONFIRMED EXECUTED v1.18 — increased from 3%)
  - Relative Roth: 4% (CONFIRMED EXECUTED v1.18 — new position; was 0%)

#### COPX
- Components: inflation_hedge_commodity_linked (0.75) + broad_market_equity_international (0.25)
- Basis: Global X Copper Miners ETF. Tracks Solactive Global Copper Miners Total Return Index. 41 holdings across global copper mining companies.
- AUM: $6.86B. Expense ratio: 0.65%. Inception: 2010-04-19.
- Country breakdown (Jan 31, 2026): Canada 36.68%, China 9.62%, US 9.59%, Japan 7.92%, Australia 7.86%, Poland 5.93%, Sweden 5.35%, UK 5.12%, Switzerland 4.82%, Others 7.13%.
- M07 STATUS: PASS — Canada 36.68% below 40% single-country threshold. Regional ruling per v1.13: Canada + US are separate political/economic regimes. RULING: PASS. ⚠ Amber flag for June 30 formal confirmation.
- Last reviewed: 2026-05-07 (v1.14 — entry guard cleared)
- EV (A=7/B=36/C=41/D=5/E=4/F=7): **+2.60%** (updated v1.19; prior at C=44: +2.88%). Ranked #4.
  - A:  (0.75×2 + 0.25×4) = 2.50% × 0.07 = +0.175%
  - B:  (0.75×6 + 0.25×(-5)) = 3.25% × 0.36 = +1.170%
  - C:  (0.75×7 + 0.25×(-6)) = 3.75% × 0.41 = +1.538%
  - D:  (0.75×(-8) + 0.25×(-8)) = -8.00% × 0.05 = -0.400%
  - E:  (0.75×2 + 0.25×(-10)) = -1.00% × 0.04 = -0.040%
  - F:  (0.75×2 + 0.25×3) = 2.25% × 0.07 = +0.158%
  - Total floor: +2.601% ≈ +2.60%. Mining-leverage adjusted estimate: ~+3.2-4.0%.
- TAX PLACEMENT: ALL ACCOUNTS.
- ENTRY EXTENSION GUARD: CLEARED (v1.14, May 7, 2026). 90d avg ~$85-90; threshold ~$102-106; current $83.35 — below threshold.
- Target allocation (v1.13): 2% Primary IRA; 7% Primary Taxable.

#### VTIP
- Components: inflation_linked_sovereign (1.00)
- Basis: Vanguard Short-Term Inflation-Protected Securities ETF. AUM: $66.6B. Expense ratio: 0.03%. Beta: 0.22.
- Last reviewed: 2026-05-06 (v1.13, initial classification)
- EV (A=7/B=36/C=41/D=5/E=4/F=7, ⚑ PENDING): **+0.52%** (updated v1.19; prior: +0.56%).
  - A: -2×0.07=-0.14; B: 1×0.36=+0.36; C: 1×0.41=+0.41; D: 0×0.05=0; E: -1×0.04=-0.04; F: -1×0.07=-0.07
  - Total: +0.520%.
- TAX PLACEMENT: RETIREMENT ACCOUNTS ONLY. Inflation accrual on TIPS taxed as ordinary income annually.
- ENTRY EXTENSION GUARD: N/A.
- Target allocation (v1.13): 8% Primary IRA; 10% Primary Roth; 12% Relative IRA; 10% Relative Roth.

#### XLP
- Components: consumer_defensive_equity (1.00)
- Basis: State Street Consumer Staples Select Sector SPDR ETF. AUM: $14.5B. Expense ratio: 0.08%. 100% US domestic.
- Last reviewed: 2026-05-06 (v1.13, initial classification)
- EV (A=7/B=36/C=41/D=5/E=4/F=7, ⚑ partial): **+0.14%** (updated v1.19; prior: +0.12%). Ranked #10.
  - A: 0×0.07=0; B: 2×0.36=+0.72; C: 0×0.41=0; D: -5×0.05=-0.25; E: -8×0.04=-0.32; F: -3×0.07=-0.21
  - Total: +0.140%.
- TAX PLACEMENT: ALL ACCOUNTS.
- ENTRY EXTENSION GUARD: N/A.
- Target allocation (v1.13): 7% Primary Taxable.

#### VNQ
- Components: real_estate_equity_income (0.60) + rate_sensitive_income_long_duration (0.22) + secular_technology_growth (0.12) + broad_market_equity_domestic (0.06)
- Last reviewed: 2026-05-06 (v1.13, initial classification)
- EV at current probs (real_estate_equity_income [TBD] — LOW confidence): -4.52% to +1.27% depending on §4.1 calibration outcome.
- STRUCTURAL NOTE: VNQ is ADVERSARIAL to current B/C dominant distribution. Modern REIT leverage (40-60% LTV) causes cap rate expansion to overwhelm rental income growth in elevated-rate environments.
- TAX PLACEMENT: RETIREMENT ACCOUNTS ONLY (REIT distributions predominantly ordinary income).
- ADOPTION TRIGGER: A > 25% on T1-confirmed US-Iran deal.
- CURRENT PORTFOLIO ALLOCATION: NONE.

#### VEA
- Components: broad_market_equity_international (1.00)
- Last reviewed: 2026-05-06 (v1.13, initial classification)
- EV at current probs: approximately **−3.40%** (B/C dominant; international equity faces energy-importer FX drag).
- ADOPTION TRIGGER: A > 25% on T1-confirmed deal.
- CURRENT PORTFOLIO ALLOCATION: NONE.

#### XLV
- Components: healthcare_defensive_equity (1.00)
- Last reviewed: 2026-05-06 (v1.13, initial classification — provisional)
- Provisional EV (§4.1 ALL PENDING): approximately −0.44% at current probs.
- TAX PLACEMENT: ALL ACCOUNTS.
- CURRENT PORTFOLIO ALLOCATION: NONE.

#### FLOT
- Components: floating_rate_credit_income (1.00)
- Last reviewed: 2026-05-06 (v1.13, initial classification — full M07 screen pending)
- Provisional EV (§4.1 ALL PENDING): approximately +0.2-0.5% above SGOV in B.
- KEY RISK: D/E scenario credit spread blowout vs SGOV pure Treasury safety.
- TAX PLACEMENT: ALL ACCOUNTS.
- CURRENT PORTFOLIO ALLOCATION: NONE.

---

## Consolidated Target Allocations (v1.18, May 22, 2026 — confirmed executed; EVs updated v1.19)

| Instrument | Primary IRA | Primary Roth | Primary Taxable | Taxable Pres. | Relative IRA | Relative Roth |
| --- | --- | --- | --- | --- | --- | --- |
| MLPX | 30% | 28% | 30% | — | 24% | 32% |
| DBMF | 15% | 17% | 10% | — | 15% | 20% |
| SGOL | 16% | 14% | — | — | 20% | 16% |
| VTIP | 8% | 10% | — | — | 12% | 10% |
| AIPO | 8% | 8% | 8% | — | 6% | 10% |
| XAR | 12% | 12% | 12% | — | — | — |
| SGOV | — | — | 15% | 100% | 14% | — |
| SIVR | 4% | 5% | — | — | 6% | 4% |
| COPX | 2% | — | 7% | — | — | — |
| MAGS | 5% | 6% | — | — | 3% | 8% |
| XLP | — | — | 7% | — | — | — |
| PAVE | — | — | 11% | — | — | — |
| **Total** | **100%** | **100%** | **100%** | **100%** | **100%** | **100%** |

Portfolio EV by account (v1.18 targets, A=7/B=36/C=41/D=5/E=4/F=7 — updated v1.19):
- Primary IRA: +4.03% (required ~3.38% — GAP CLOSED ✅ +0.65pp above)
- Primary Roth: +4.08% (required ~3.05% ✅ +1.03pp above)
- Primary Taxable: +3.04% (RETURN_THEN_TARGET 5yr ✅)
- Taxable Preservation: Capital preservation — SGOV 100% ✅
- Relative IRA: **+3.89%** (FLOOR_THEN_RETURN ✅ — v1.18 targets confirmed)
- Relative Roth: **+4.73%** (required ~3.03% ✅ — v1.18 targets confirmed)

## Section 12 - M17 Systemic Cascade Warning Thresholds

All values CALIBRATION_DATED. Added v1.19 May 25, 2026. First formal audit: June 30, 2026.
Module: M17_SystemicCascadeWarning.md (v1.1, merged PR #15 May 25, 2026)
Purpose: Early warning system for D/E scenario cascade chains. sectorStressScore() outputs feed as D_precursor_binding into DeriveScenarioProbabilities().
Source: Session_Log May 25 research/dev session; PR #14 and PR #15 design documentation.

### 12.1 Agriculture/Fertilizer Chain (CHAIN_1)

| Parameter | Alert Threshold | Notes |
| --- | --- | --- |
| farm_filings_alert | +50% YoY chapter 12 filings | USDA quarterly data. Hormuz → Iranian urea → food CPI structural floor. |
| natgas_alert | $6.00/mmBtu sustained 30 days | Natural gas price Hormuz/Iran pricing link. |
| fertilizer_alert | +50% above 12-month average | CRU/Bloomberg commodity data. |

Current status (May 25, 2026): Farm filings +46% YoY — **BORDERLINE** (threshold +50% not formally met). CHAIN_1: NOT FIRED formally.

### 12.2 CRE/Regional Bank Chain (CHAIN_2)

| Parameter | Alert Threshold | Notes |
| --- | --- | --- |
| KRE_alert | −15% vs SPX over 90 days | Regional bank stress signal. CRE maturity wall $930B in 2026. |
| SOFR_DFF_alert | +10 bp SOFR–DFF spread sustained 5 days | Funding stress / liquidity squeeze indicator. |

Current status (May 25, 2026): KRE $69.37 (not meaningfully underperforming vs SPX over 90d); SOFR–DFF −11 bp (benign). **CHAIN_2: NOT FIRED.**

### 12.3 Private Credit / Margin Chain (CHAIN_3)

| Parameter | Alert Threshold | Notes |
| --- | --- | --- |
| margin_MoM_alert | −5% MoM after record high | FINRA monthly margin debt data. |
| gate_count_alert | 3+ gate/suspension events in 90 days | Private credit fund gates, PIK toggle abuse, redemption halts. |

Current status (May 25, 2026): FINRA margin debt $1.304T (April 2026 — all-time record). Gate events observed: BlackRock CLO OC breach, Blue Owl gate. **CHAIN_3: FIRES** — record margin debt + gate events constitute threshold breach.

### 12.4 Manufacturing/Corporate Chain (CHAIN_4)

| Parameter | Alert Threshold | Notes |
| --- | --- | --- |
| bankruptcy_quarterly_alert | 800+ large-company filings per quarter | 14-year high observed qualitatively; T1 source pending. |

Current status (May 25, 2026): Corporate bankruptcies qualitatively at 14-year high (T1 count source pending). **CHAIN_4: FIRES qualitatively** — awaiting T1 source for formal score.

### 12.5 Sovereign Stress / Scenario E Chain

| Parameter | Alert Threshold | Warning Level | Notes |
| --- | --- | --- | --- |
| E_term_premium_alert | 150 bp | Formal E escalation trigger | THREEFYTP10 series |
| E_term_premium_warning | 100 bp | Watch flag | THREEFYTP10 series |
| E_30Y_warning | 5.50% | Watch flag | 30Y Treasury yield |

Current status (May 25, 2026): THREEFYTP10 = 0.8117% (May 15 — 14-year high, rising). E_term_premium_warning (100 bp): **NOT YET FIRED** (gap 18.83 bp — watch; trajectory rising). 30Y = 5.07% — below 5.50% warning. **E_watch_flag: FISCAL_STRESS_BUILDING.**

### 12.6 Municipal Chain

Qualitative only. No formal threshold at this time. Assess at June 30, 2026 audit.

### 12.7 Yield Curve Signal

| Parameter | Value | Notes |
| --- | --- | --- |
| resteepening_min_inversion | 3 months | Minimum inversion duration before re-steepening counts as D signal |
| inversion_threshold | −50 bp | 10Y–2Y must have reached −50 bp or more negative prior to re-steepening |
| steep_threshold | +100 bp | Re-steepening target that confirms recession-onset pattern |

Current status (May 25, 2026): 10Y–2Y = +43 bp (re-steepened; curve NORMAL_OR_STEEP). Prior inversion confirmed (exceeded −50 bp in 2024-2025). Re-steepening post-inversion: **D_timing_signal: RECESSION_ONSET_PATTERN** (historically 5/6 occurrence rate for recession onset following this pattern).

### 12.8 Cascade Level Computation

sectorStressScore() = count of formally fired chains (CHAIN_1 through CHAIN_4):

| Score | CascadeLevel | D_precursor_binding |
| --- | --- | --- |
| 0 | CLEAR | 0 |
| 1 | WATCH | 1 |
| 2 | ALERT | 2 |
| 3 | WARNING | 3 |
| 4 | CRITICAL | 3 (capped — M11 formal trigger required for further D escalation) |

**Current (May 25, 2026): sectorStressScore = 2** (CHAIN_3 formally + CHAIN_4 qualitatively) → **CascadeLevel: ALERT** → **D_precursor_binding = 2.**

Applied to DeriveScenarioProbabilities() May 25 full M05 session: D 3%→5% (+2pp), E 3%→4% (+1pp), C 44%→41% (−3pp). Client approved. Active probabilities: A=7/B=36/C=41/D=5/E=4/F=7.

⚠ CHAIN_4 T1 confirmation pending — if CHAIN_4 is formally confirmed via T1 source, sectorStressScore remains 2 (both CHAIN_3 and CHAIN_4 formally confirmed). Score and CascadeLevel unchanged. Confirm at Q2 or next session with T1 corporate bankruptcy data.
