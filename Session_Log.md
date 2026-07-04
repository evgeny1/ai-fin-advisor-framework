# Session Log
<!-- Split from Calibration_State.md as of v1.12, May 6, 2026 (framework-v2-architecture-split) -->
<!-- Purpose: append-only log of per-session credit readings (§7) and scenario state (§8) -->
<!-- Fetched at session start via M12_FileProtocol.fetchSessionLog() — concurrent with fetchCalibrationState() -->
<!-- Written at session end via M12_FileProtocol.WriteBack (push_files atomic with Calibration_State.md) -->
<!-- §8 is the AUTHORITATIVE SOURCE for prior scenario probabilities and open items -->

## Compaction Rules (execute at each Q-end audit)

- §7: retain last 10 session credit readings; archive prior rows to Archive_[Year]Q[N].md
- §8: retain last 3 full session entries; collapse prior entries to one-line summary:
      format: `date | A%/B%/C%/D%/E%/F% | key_decision`
- Archive file naming: `Archive_[Year]Q[N].md` (e.g., `Archive_2026Q2.md` created June 30, 2026)
- Archive contains: all §7 rows and §8 entries prior to the Q-end compaction cutoff

### §8 Canonical Schema (added June 7, 2026 — required fields for every full-session entry)

```
date: YYYY-MM-DD (session type — e.g., "full M05" or "ad-hoc")
scenario_probabilities: { A: X%, B: X%, C: X%, D: X%, E: X%, F: X% }
  // VERIFY sum == 100%. Include derivation comments.
primary_driver: [current dominant driver one-liner]
session_type: [full M05 | ad-hoc | audit | READONLY_MOBILE]

# Required for full sessions:
credit_readings (date, T1 source):
  HY: Xbps | IG: Xbps | CCC: Xbps | MOVE: X | VIX: X | S&P: X | KRE: $X | BZ=F: $X
cascade_signals:
  sectorStressScore: X. CascadeLevel: [MONITORING|WATCH|ALERT|WARNING|CRITICAL].
  D_timing_signal: [value].
open_triggers: [list with status]
open_decisions: [numbered list]
next_session_flags: [list]

# Optional (include when relevant):
calibration_changes_this_session: [list with version bumps]
work_completed: [list for audit/ad-hoc sessions]
m14_recomputation_results: [M14 session computation if run]
b_watch_level_3: [active | inactive] (include when CPI print 3 is 3.5–3.9%)
```

---

## Section 7 - Session Observations Log (Credit Readings)

// COMPACTED: 2026-06-19 — rows 2026-05-07 through 2026-05-13 (3 rows: 05-07, 05-11, 05-13) archived to Archive_2026Q2.md, restoring the last-10 retention rule (FRAMEWORK_BACKLOG.md ENG-5)

| Date | HY OAS (bps) | IG OAS (bps) | CCC OAS (bps) | Source | T1 Flag |
| --- | --- | --- | --- | --- | --- |
| 2026-05-22 (full) | **278** | **75** | **939** | **FRED T1 — embedded allocation spreadsheet tab.** May 21 close. MOVE: 79.72 GOOGLEFINANCE. VIX: 16.52. S&P 500: 7,494.81. | **T1 — spreadsheet tab** |
| 2026-05-25 (research/dev + full M05) | 278 (carry) | 75 (carry) | 939 (carry) | FRED T1 via allocation spreadsheet tab — May 21 close (most recent; May 25 is Sunday/Memorial Day). Also confirmed: BAMLC0A4CBBB (BBB OAS) 94 bps; SOFR 3.51%; DFF 3.62%; SOFR–DFF spread −11bp (normal). MOVE: 78.43 (GOOGLEFINANCE live). VIX: 16.70. S&P 7,473.47 (May 22 close). S&P Futures overnight: 7,268.25 (−2.7%). FINRA margin debt: $1.304T (Apr 2026 record). THREEFYTP10: 0.8117% (May 15 — 14-yr high). Yield curve (FMP May 22): 10Y–2Y +43bp; 10Y–3M +88bp; 30Y 5.07%. BZ=F overnight ~$107.60 (Yahoo Finance pre-market T2, Memorial Day). | **T1 — spreadsheet tab + FMP** |
| 2026-05-25 (second M05 — v1.20 framework evaluation) | 278 (carry) | 75 (carry) | 939 (carry) | Carry — Memorial Day; no new FRED data. BZ=F intraday (Memorial Day session): ~$93-96 (down ~6% from $100.21 May 22 close) on US-Iran deal optimism. S&P futures: +0.95% (reversed from prior −2.7% overnight). DXY ~98.92. Gold $4,523, Silver $76.15 (May 22). Kevin Warsh sworn in as 17th Fed Chairman May 22. | T1 carry; BZ=F T2 (Investing.com/Trading Economics CFD); equities T2 |
| 2026-05-29 (Q2 audit — full M05) | **278** | **73** | **935** | **FRED T1 — embedded allocation spreadsheet tab.** May 28 close. MOVE: 70.22 (GOOGLEFINANCE live). VIX: 15.32. S&P: 7,580. DFF: 3.62%. BBB OAS: 93bps. BB OAS: 161bps. KRE: $69.61. BZ=F: ~$91-92 (CNBC/Trading Economics T1, May 29 intraday — down ~19% in May on Iran deal optimism). NatGas (DHHNGSP): $3.10 (May 26). | **T1 — spreadsheet tab** |
| 2026-06-01 (objective type resolution — ad-hoc) | **274** | **74** | **941** | **FRED T1 — embedded allocation spreadsheet tab.** May 31 close: HY BAMLH0A0HYM2 2.74%, IG BAMLC0A0CM 0.74%, CCC BAMLH0A3HYC 9.41%. MOVE: 73.33 (GOOGLEFINANCE). VIX: 16.05. S&P: 7,599.96. KRE: $68.31. SOFR: 3.63%. DFF: 3.62%. NatGas: $3.10 (May 26 — latest available). | **T1 — spreadsheet tab** |
| 2026-06-02 (full M05 session — v1.29) | **274** | **74** | **941** | **FRED T1 — embedded allocation spreadsheet tab.** May 31 close (most recent). BZ=F: ~$95.30 (Yahoo Finance T1 close, +3.5% on Iran escalation). DXY: 99.19 (Trading Economics T1). 10Y: 4.51%; 2Y: 4.04%; 30Y: 4.98%; 10Y-2Y: +42bp. S&P open 7,599.96; close 7,609.78 (+0.13%). AIPO: $34.01 (+3.59%); COPX: $93.66 (+4.00%); MLPX: $73.50 (+2.03%). MOVE: 73.33 session-start. All credit thresholds CLEAR. CCC divergence watch active. | **T1 (credit) — spreadsheet tab; T2 (BZ=F, DXY, instruments)** |
| 2026-06-02 (AIPO classification audit — v1.30) | 274 (carry) | 74 (carry) | 941 (carry) | Carry — ad-hoc classification correction session. No new market data fetched. AIPO ThematicETF_ClassificationAudit() re-run from T1 source (Defiance ETFs official page, 77 holdings, $750.87M AUM). | T1 carry |
| 2026-06-04 (full M05 — M18 v1.2 re-verification) | 274 (carry) | 74 (carry) | 941 (carry) | FRED T1 via allocation spreadsheet — May 31 close (most recent). MOVE: 71.16 (GOOGLEFINANCE T1 live). VIX: 15.40 (T1 live). S&P: 7,584.31. DXY: 99.43. 10Y: 4.47%; 2Y: 4.05%; 30Y: 4.97%; 10Y-2Y: +42bp. BZ=F: $97.81 (Jun 3 close T1 market_data). KRE: $69.98. All credit thresholds CLEAR. MOVE NORMAL (71.16 < 80). M14 composite HIGH (equity-driven; commodity NOT FIRING — energy_90d +5.52%). | T1 carry (credit); T1 live (MOVE, VIX, S&P, DXY, rates) |
| 2026-06-07 (audit — framework gap session) | **274** | **74** | **946** | **FRED T1 — embedded allocation spreadsheet tab.** June 4 close: HY BAMLH0A0HYM2 2.74%, IG BAMLC0A0CM 0.74%, CCC BAMLH0A3HYC 9.46%. MOVE: 75.2 (GOOGLEFINANCE). VIX: 21.51 (June 5/7 live). S&P: 7,383.74 (June 5 close — S&P -2.64% on strong May jobs +172k vs +80k expected + semi selloff). KRE: $70.17 (stable). BZ=F: $93.09 (June 5 close, T1 market_data MCP — C-trigger INACTIVE). BBB OAS: 93 bps. SOFR: 3.62%. DFF: 3.62%. NatGas: $3.07 (June 1 latest). THREEFYTP10: 0.7541% (May 29 — latest in spreadsheet). M14 composite MODERATE (energy_90d −5.93% NOT FIRING; broad_equity_30d ~+3.7% MODERATE). CCC +5bps from last reading: divergence watch continues. | **T1 — spreadsheet tab (credit); T1 market_data (BZ=F)** |
| 2026-06-10 (full M05 — B formal trigger session; v1.33) | **274** | **74** | **946** | **FRED T1 — embedded allocation spreadsheet tab.** June 4 close (most recent; no new FRED push): HY BAMLH0A0HYM2 2.74%, IG BAMLC0A0CM 0.74%, CCC BAMLH0A3HYC 9.46% (carry). MOVE: 77.03 (T1 market_data live). VIX: 20.43 (+2.82% on CPI; prev 19.87). S&P: 7,362.65 (−0.32%). KRE: $72.10 (+1.46% — hawkish). BZ=F: $91.45 (Jun 9 T1 market_data). DXY: 99.85. BBB OAS: 93bps (carry). SOFR: 3.62% (carry). KBE: $65.73 (+1.12%). Schwab T1 screenshot: PAVE $56.095 (SOLD 502sh, gain +$984 absorbed by −$2,778 YTD losses), MLPX $74.37 (+1.46%), DBMF $30.85 (+0.23%), SGOV $100.475 (flat), AIPO $29.71 (−3.94%), XLP $85.17 (+1.27%), COPX $78.64 (−1.87%). All credit thresholds CLEAR. MOVE approaching ELEVATED (77.03 < 80). CCC divergence watch: 5th consecutive session quiet widening. | **T1 — spreadsheet tab (credit, June 4 carry); T1 market_data (MOVE, VIX, S&P, KRE, BZ=F live); T1 Schwab screenshot (position prices)** |

---

## Section 8 - Session State Log

// COMPACTED: 2026-04-30 | A=7%/B=42%/C=42%/D=3%/E=3%/F=3% | Hormuz Day 61; SUPERSEDED by May 13 full session

// COMPACTED: 2026-06-19 — entries 2026-05-25 through 2026-06-07 (7 entries) archived to Archive_2026Q2.md, restoring the last-3 retention rule (FRAMEWORK_BACKLOG.md ENG-5); retained: 2026-06-10, 2026-06-14 (x2)

// COMPACTED: 2026-06-21 — advisor_write_back was called twice for this single session (the first MCP tool call completed and committed server-side but timed out client-side before returning a response, per ENG-33's investigation; a second in-process call was made to actually complete the write-back, not realizing the first had already succeeded). Each call's retention pass archived its own oldest entry (June-10, then June-14's first of two same-day entries) to Archive_2026Q2.md, and each appended a near-duplicate "2026-06-21 (full M05 session)" entry. The duplicate (first, less complete) June-21 entry has been removed below, retaining only the second. The extra-archived June-14 entry was not restored — it remains safely in Archive_2026Q2.md if needed; flagged to Evgeny rather than manually reconstructed here to avoid transcription risk.

// COMPACTED: 2026-07-03 — 1 oldest entry(ies) archived to Archive_2026Q3.md, restoring the last-3 retention rule (FRAMEWORK_BACKLOG.md ENG-5)

// COMPACTED: 2026-07-03 — 1 oldest entry(ies) archived to Archive_2026Q3.md, restoring the last-3 retention rule (FRAMEWORK_BACKLOG.md ENG-5)

---

date: 2026-06-25 (full M05 session)
scenario_probabilities: { A: 11.4118%, B: 34.2353%, C: 11.4118%, D: 3%, E: 5.7059%, F: 34.2353% }
primary_driver: Persistent CPI acceleration (May 4.2% YoY, 3rd consecutive accelerating print) + confirmed strong nominal GDP (Q1 third estimate: real 2.1%, nominal ~5.6% annualized -- 2nd consecutive quarter of nominal growth >3%) + hawkish Fed hold (June 17, dropped easing bias, dot-plot median 3.8%) shifted the scenario mix to a B/F tie (34.24%/34.24% each, from prior B 48.5%/F 16.17%). Hormuz/Iran kept scored as conflict-premise-still-active pending fresh T1 confirmation despite mounting de-escalation evidence (Bürgenstock talks concluded with a deconfliction channel; Brent fell to at/below pre-war levels this week).
session_type: full M05 session

open_triggers:
- Hormuz/Iran CONTESTED: IRGC re-declared closure June 20 but Brent has fallen to at/below pre-war levels (multi-month lows, contango) and Bürgenstock talks concluded with a deconfliction channel -- mounting de-escalation evidence. Re-score C_check_chokepoint/M19_XAR_CONFLICT_GATE at Q2 audit with fresh T1 confirmation; do not flip on price action alone.
- Q1 2026 GDP third estimate confirmed 2.1% real (revised up from 1.6% second estimate, released today June 25). Nominal GDP growth ~5.6% annualized, second consecutive quarter >3% nominal -- F_check_gdp trigger now formally met.
- DBMF M19 status FAILED (mean-reversion condition, verified-correct data per ENG-27) -- ENG-30's second condition (DBMF_3M_return < -3% while B+C >= 55%) still has no evaluator; treat as partial signal only.
- Q2 calibration audit June 30 (5 days out): full EV recomputation, XAR sizing review, GAP-16 real-yield methodology, COPX 90d avg recompute, INFL Section 11 classification still pending.
- URA IRA target discrepancy (sheet shows 1% actual vs 3% framework-cleared target) and MAGS sheet 5%/6% vs Calibration_State 3%/4% -- both unresolved, clarify before executing.
- AIPO IRA/Roth reduction (7%->3%, +4pp to DBMF) still under client deliberation, unchanged this session.
- Primary IRA and Primary Roth IRA both join Relative Roth as TARGET_THEN_RETURN accounts running INFEASIBLE this session (shortfalls 2.68pp / 2.79pp / 2.86pp respectively) -- same root cause (B/F-tied scenario mix compresses blended conservative returns account-wide). Add to Q2 audit scope: full required-return/multiplier methodology review, not just Relative Roth.

open_decisions:
1. Relative Roth (...466) objective_type CONFIRMED as TARGET_THEN_RETURN by client 2026-06-25 -- this is correct, not a stale sheet entry. Stop flagging it as a discrepancy needing correction to FLOOR_THEN_RETURN.
2. Relative Roth (...466) reallocated this session per scenario-weighted blended math: AIPO 10.5%->11%, MLPX 33.7%->35%, VTIP 35.4%->30%, DBMF 20.2%->24%. FeasibilityCheck result: INFEASIBLE. Blended conservative return improves 2.12%->2.33% (shortfall narrows from 3.07pp to 2.86pp) but required return for TARGET_THEN_RETURN (15yr horizon, multiplier 2.14x) is 5.19% -- gap not closed. Tested adding a precious-metals candidate role (SGOL) -- made the shortfall worse (2.98pp) given today's B/F-dominant scenario mix (SGOL's per-scenario weight in F is only 0.02). No instrument currently in Section 11 reaches the required 5.19% blended conservative return for this account at today's probabilities. This is a structural gap, not a reallocation-execution problem -- flag for Q2 audit: revisit whether the required-return/multiplier methodology is appropriate for a sub-$10k account, or accept the shortfall as a known limitation.
3. Relative Roth (...466) floor breach this session (Step 3b/6b, scenario F, worst -0.24%, IMMEDIATE priority) -- addressed via the reallocation above; VTIP and DBMF were the floor-proximity drag instruments and both moved in the directionally correct direction (VTIP trimmed toward its lower blended-ideal weight, DBMF added toward its higher one).
4. Ran all four of Evgeny's own accounts through advisor_evaluate_allocation this session (initial pass had only covered Relative Roth). Primary IRA (3080-6469, TARGET_THEN_RETURN/10yr): blended return 2.22% vs required 4.90% (multiplier 1.61x) -- shortfall 2.68pp, INFEASIBLE; directives MAGS/AIPO/XAR/MLPX HOLD, SGOL/DBMF/VTIP/COPX ADD (AIPO and COPX both show dual-role conflicts, dominant role applied). Primary Roth IRA (3534-9838, TARGET_THEN_RETURN/15yr): blended return 2.41% vs required 5.19% (multiplier 2.14x) -- shortfall 2.79pp, INFEASIBLE; directives MAGS/AIPO/XAR/MLPX HOLD, DBMF/VTIP ADD (AIPO dual-role conflict, dominant role applied; account holds no COPX or SGOL). Taxable Acc4 (6668-9768, RETURN_THEN_TARGET/5yr): no required-return hurdle for this objective type; AIPO/XAR/MLPX/SGOV HOLD, DBMF/COPX ADD (COPX dual-role conflict, commodity-linked 75% dominant overrides international-equity 25% sub-component). Taxable Acc3 (3459-4443, PRESERVATION): 99.95% SGOV, HOLD, no findings.
5. Systemic pattern this session: ALL THREE TARGET_THEN_RETURN accounts (Primary IRA, Primary Roth, Relative Roth) are infeasible by a similar margin (2.68pp / 2.79pp / 2.86pp shortfall respectively) under today's B/F-tied scenario mix. The highest blended conservative return available anywhere in the Section 11 registry this session is MLPX at 3.61% -- no single instrument or combination clears any of the three accounts' ~5% real-return hurdles. This is a calibration-level question for the Q2 audit (is the conservative-case return table too conservative under a B/F-tied regime, or is the required-return/multiplier formula miscalibrated for this regime), not an individual-account allocation problem. No REDUCE candidates surfaced in any of the four accounts this session -- AIPO/MAGS/MLPX/XAR are all at-or-near their blended-ideal weight (HOLD) in every account that holds them.
6. AIPO data-quality flag applies across every account holding it (Primary IRA, Primary Roth, Acc4, Relative Roth): component weights sum to only 86% (14% unclassified, excluded from EV computation). Verify classified weights at the next Section 11 audit.

next_session_flags:
- FIRST: re-verify Hormuz/Bürgenstock outcome with fresh T1 sources before re-scoring C_check_chokepoint/M19_XAR_CONFLICT_GATE -- evidence is trending toward de-escalation (Brent at/below pre-war levels, deconfliction channel established).
- Q2 audit due June 30: INFL classification, URA/MAGS sheet-vs-calibration discrepancies, GAP-16 real-yield methodology, and the structural TARGET_THEN_RETURN shortfall now confirmed across THREE accounts (Primary IRA, Primary Roth, Relative Roth) all need deliberate review -- this looks like a methodology question, not isolated account issues.

---

date: 2026-07-03 (full M05 session)
scenario_probabilities: { A: 13.8571%, B: 34.6429%, C: 13.8571%, D: 3%, E: 6.9286%, F: 27.7143% }
primary_driver: Persistent stagflation signal (May CPI 4.2% 3rd accel print, weak June jobs +57k/74k downward revisions) alongside genuine Hormuz de-escalation (JMIC widened route, Brent multi-month lows, ongoing Doha talks) shifted mix from F toward A/C (F 34.2%->27.7%, A/C 11.4%->13.9% each). XAR M19 thesis FAILED on MOU+reopening evidence. Main session work: full advisor_evaluate_allocation feasibility test of a proposed VTI/SCHD/SGOV broad-index simplification across all 6 accounts -- found infeasible (Primary IRA/Roth shortfalls 3.69pp/3.93pp, worse than current 2.68pp/2.79pp) or floor-breaching (Relative IRA breaches floor even at 40% VTI/60% SGOV) in every tested account.
session_type: full M05 session

open_triggers:
- Hormuz chokepoint: accumulated T1 evidence (JMIC widened route, Brent normalization, continued Doha talks) now scores de-escalated (0) -- re-verify at next session, do not revert on a single report
- XAR M19 thesis FAILED (Iran MOU signed + Hormuz reopening confirmed) -- needs TRIM/EXIT execution decision next session, requires client confirmation before acting
- Relative Roth (...466) floor breach on CURRENT holdings (Scenario F, -0.27%, IMMEDIATE) -- mechanical fix (trim VTIP, add DBMF) computed but never written to allocation sheet Target column
- GDPNow Q2 nowcast fell sharply 3.0%->1.2% (June 17->July 1) -- model-based only, official BEA advance estimate due ~July 30, watch not act
- Q2 audit (June 30, now overdue) still has ~15 open calibration items unresolved
- VTI/SCHD/SGOV simplification tested infeasible/floor-breaching across every account this session -- if client still wants simplification, next session should address whether required-return multipliers need revisiting or whether a different instrument set could clear the bar

open_decisions:
1. VT itself was never classified in §11 -- only VTI (US-only). VT would need fresh M15 classification before any evaluation; given VTI's weak result, low priority.
2. SCHD confirmed already classified in §11.4 (added 2026-06-29): BMED(0.49)+consumer_defensive_equity(0.18)+healthcare_defensive_equity(0.16)+inflation_hedge_commodity_linked(0.17). Shows dual-role conflict in Scenario B (dominant BMED role says REDUCE while defensive/IHC components say ADD).
3. Acc3 (3459-4443) correctly identified as PRESERVATION objective type -- should NOT be rotated into equities; stays 100% SGOV. Earlier mobile-session recommendation to rotate it into VT was an error, corrected this session.
4. Relative Roth (...466) objective_type reconfirmed as FLOOR_THEN_RETURN per the live allocation sheet Objectives tab -- a prior in-session claim that 2026-06-25 had confirmed it as TARGET_THEN_RETURN was itself incorrect and has been reversed.
5. Client decision this session: for a VTI/SGOV structure in Relative IRA, tested 75/25 (floor breach -1.25% B) and 40/60 (floor breach -0.20% B) -- neither clears the floor. Relative Roth clears only at 30/70 VTI/SGOV (0.86% blended return).

next_session_flags:
- XAR M19 FAILED -- bring TRIM/EXIT recommendation with full directive breakdown for client confirmation
- Resolve Relative Roth floor breach by writing the computed reallocation to the actual allocation sheet Target column
- Q2 audit (overdue) needs closing -- ~15 items including broad_market_equity_domestic B/C bifurcation, healthcare_defensive_equity full row, real_estate_equity_income leverage recalibration
- If simplification goal persists: revisit required-return multiplier methodology (flagged internally as possibly miscalibrated for a B/F-tied regime) before re-testing any broad-index structure

---

date: 2026-07-03 (full M05 session)
scenario_probabilities: { A: 13.8571%, B: 34.6429%, C: 13.8571%, D: 3%, E: 6.9286%, F: 27.7143% }
primary_driver: Session continuation after MCP server restart (client-initiated) and a repopulated computation cache. Client challenged last session's XAR M19 FAILED call with a direct empirical observation; investigation confirmed geopolitical_premium conflates acute-conflict (de-escalating) and defense-procurement (structurally sticky) drivers -- TRIM/EXIT deferred pending reclassification. Simplification goal redirected from broad-index funds (tested infeasible) to existing high-EV classified instruments (DBMF/MLPX), which meaningfully narrows Primary IRA's feasibility shortfall (2.68pp -> 1.41pp) using only 3 tickers -- also identified the 40% concentration cap as a hard constraint ruling out true 1-2 instrument portfolios.
session_type: full M05 session

open_triggers:
- XAR M19 status under active re-review -- geopolitical_premium role may need splitting into acute-conflict vs defense-procurement sub-components; do not act on current FAILED status
- Relative Roth (...466) floor breach on CURRENT holdings (Scenario F, -0.27%, IMMEDIATE) -- fix computed, not yet written to sheet
- Simplification: DBMF/MLPX/SGOL(SGOV) 40/40/20 structure needs testing across remaining 4 accounts (Primary Roth, Acc4, Relative IRA, Relative Roth) next session
- Q2 audit (June 30, overdue) still has ~15 open items
- Hormuz chokepoint scored de-escalated (0) this session -- re-verify next session

open_decisions:
1. XAR thesis-failure call from last session is under genuine reconsideration, not confirmed -- do not execute TRIM/EXIT until the geopolitical_premium role split/reweight question is resolved.
2. Simplification path pivoted from broad-index (VTI/SCHD, tested infeasible) to existing high-EV classified instruments (DBMF/MLPX) -- Primary IRA test shows meaningful improvement (2.68pp shortfall -> 1.41-1.51pp) though not yet fully feasible.
3. Concentration_cap (40%, all accounts) identified as a hard mathematical constraint ruling out true 1-2 instrument portfolios -- 3-4 instruments is the realistic floor for this client's stated constraints.

next_session_flags:
- XAR M19 flagged FAILED but NOT executed -- client's empirical observation (XAR +6% 30d, sole real green position) held up under investigation: geopolitical_premium role bundles acute-conflict AND defense-procurement drivers: only the former is de-escalating. Needs genuine M15 reclassification review (split the role or reweight) before any TRIM/EXIT, not a mechanical action on the M19 gate alone.
- Concentration_cap=0.4 on every account mathematically rules out a true 1-2 instrument portfolio (2 instruments can't both stay <=40% and sum to 100%) -- client's simplification goal reframed as 3-4 instruments, not 1-2.
- DBMF+MLPX(+SGOL/SGOV) tested as simplification alternative for Primary IRA: 40/40/20 cuts shortfall from 2.68pp (current 8-holding mix) to 1.41-1.51pp, both DBMF and SGOL get live ADD directives -- re-run this same structure test across Primary Roth, Acc4, and both Relative accounts next session.
- Resolve Relative Roth floor breach by writing the computed reallocation to the actual allocation sheet Target column
- Q2 audit (overdue) needs closing -- ~15 items

