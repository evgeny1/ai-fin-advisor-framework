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

---

## Section 7 - Session Observations Log (Credit Readings)

| Date | HY OAS (bps) | IG OAS (bps) | CCC OAS (bps) | Source | T1 Flag |
| --- | --- | --- | --- | --- | --- |
| 2026-05-07 (full) | 277 (carry) | 80 (carry) | 921 (carry) | Carry. FRED still metadata only. | stale |
| 2026-05-11 (full) | **281** | **79** | **920** | **FRED T1 — DATA GAP RESOLVED.** BAMLH0A0HYM2, BAMLC0A0CM, BAMLH0A3HYC: May 8 close. MOVE: 70.74 T1 (NYSE Global Indexes). | **T1 — gap resolved** |
| 2026-05-13 (full) | **282** | **77** | **937** | **FRED T1 — embedded allocation spreadsheet tab.** May 12 close. MOVE: 70.74 carry. | **T1 — spreadsheet tab** |
| 2026-05-22 (full) | **278** | **75** | **939** | **FRED T1 — embedded allocation spreadsheet tab.** May 21 close. MOVE: 79.72 GOOGLEFINANCE. VIX: 16.52. S&P 500: 7,494.81. | **T1 — spreadsheet tab** |
| 2026-05-25 (research/dev + full M05) | 278 (carry) | 75 (carry) | 939 (carry) | FRED T1 via allocation spreadsheet tab — May 21 close (most recent; May 25 is Sunday/Memorial Day). Also confirmed: BAMLC0A4CBBB (BBB OAS) 94 bps; SOFR 3.51%; DFF 3.62%; SOFR–DFF spread −11bp (normal). MOVE: 78.43 (GOOGLEFINANCE live). VIX: 16.70. S&P 7,473.47 (May 22 close). S&P Futures overnight: 7,268.25 (−2.7%). FINRA margin debt: $1.304T (Apr 2026 record). THREEFYTP10: 0.8117% (May 15 — 14-yr high). Yield curve (FMP May 22): 10Y–2Y +43bp; 10Y–3M +88bp; 30Y 5.07%. BZ=F overnight ~$107.60 (Yahoo Finance pre-market T2, Memorial Day). | **T1 — spreadsheet tab + FMP** |
| 2026-05-25 (second M05 — v1.20 framework evaluation) | 278 (carry) | 75 (carry) | 939 (carry) | Carry — Memorial Day; no new FRED data. BZ=F intraday (Memorial Day session): ~$93-96 (down ~6% from $100.21 May 22 close) on US-Iran deal optimism. S&P futures: +0.95% (reversed from prior −2.7% overnight). DXY ~98.92. Gold $4,523, Silver $76.15 (May 22). Kevin Warsh sworn in as 17th Fed Chairman May 22. | T1 carry; BZ=F T2 (Investing.com/Trading Economics CFD); equities T2 |
| 2026-05-29 (Q2 audit — full M05) | **278** | **73** | **935** | **FRED T1 — embedded allocation spreadsheet tab.** May 28 close. MOVE: 70.22 (GOOGLEFINANCE live). VIX: 15.32. S&P: 7,580. DFF: 3.62%. BBB OAS: 93bps. BB OAS: 161bps. KRE: $69.61. BZ=F: ~$91-92 (CNBC/Trading Economics T1, May 29 intraday — down ~19% in May on Iran deal optimism). NatGas (DHHNGSP): $3.10 (May 26). | **T1 — spreadsheet tab** |

---

## Section 8 - Session State Log

// COMPACTED: 2026-04-30 | A=7%/B=42%/C=42%/D=3%/E=3%/F=3% | Hormuz Day 61; SUPERSEDED by May 13 full session

---

date: 2026-05-25 (full M05 session — v1.19)
scenario_probabilities: { A: 7%, B: 36%, C: 41%, D: 5%, E: 4%, F: 7% }
  // UPDATED from May 22 carry (A=7/B=36/C=44/D=3/E=3/F=7)
  // DeriveScenarioProbabilities() run with D_precursor_binding=2 (M17 §12 CascadeLevel ALERT)
  // D: 3%→5% (+2pp), E: 3%→4% (+1pp), C: 44%→41% (−3pp). Client approved.
  // derivation_method: scored (D_precursor overlay via M17 §12; M11 formal triggers not fired)
primary_driver: US-Iran War / Hormuz closure Day ~86. Brent C-trigger clock Day 0 (T2 confirmed — max ~5-6 consecutive closes ≥$110 May 13-19; clock reset ~May 20 on deal optimism + Hormuz satellite data showing 3 supertankers crossing). BZ=F overnight (Memorial Day) ~$107.60. Iran Strait Authority (permanent toll rejected by Trump) + uranium retained inside Iran. Rubio soft A-signal (T1 unconfirmed). D/E precursor stack: CascadeLevel ALERT.
session_type: full M05 (v1.19 — §12 pushed to Calibration_State; probabilities updated)

open_triggers:
- Brent C-trigger clock: Day 0. BZ=F ~$107.60 overnight. Watch for close ≥$110 to restart.
- Iran Strait Authority: structural C escalation (permanent toll rejected by Trump). No resolution timeline.
- CPI mid-June (May data): BINARY EVENT — if ≥4.0% → B formal trigger fires (3rd print). Run DeriveScenarioProbabilities() immediately on release.
- MOVE: 78.43 — approaching 80; no formal threshold yet (June 30 assessment).
- E_term_premium_warning: THREEFYTP10 0.8117% (14-yr high, rising) vs 100bp warning — not yet fired.
- CHAIN_1 watch: farm filings +46% vs +50% threshold.
- CHAIN_4: T1 formal confirmation pending.
- IIJA reauthorization: September 30, 2026.
- Q2 audit: June 30, 2026.

open_decisions:
1. PAVE: CascadeLevel MONITORING — exit review deferred. EV −4.03%. IIJA Sep 30 approaching.
2. MAGS: at target. Override in force. EV −2.17%.
3. secular_technology_growth B calibration: PENDING June 30.
4. URA evaluation: PENDING June 30.
5. XOM post-Hormuz ramp-up lag: ~2mo not encoded. Monitor.
6. Goldman Brent $90 Q4: T1 not confirmed. Carry.
7. CHAIN_4 manufacturing: T1 formal confirmation pending.

---

date: 2026-05-25 (second M05 session — v1.20 framework evaluation)
scenario_probabilities: { A: 7%, B: 36%, C: 41%, D: 5%, E: 4%, F: 7% }
  // UNCHANGED. Trump deal announcement evaluated but A NOT updated per M01 source integrity.
  // No signed deal; no permanent Hormuz reopening; T2 cluster only.
primary_driver: US-Iran War / Hormuz ceasefire negotiations Day ~86. BZ=F ~$93-96 Memorial Day. Kevin Warsh sworn in as Fed Chair May 22.
session_type: second M05 session same day (framework evaluation + v1.20 bug fixes)

framework_changes_this_session:
  - FW-BUG-01 FIXED: M17 v1.3 — CHAIN_3 two-mode scoring
  - M18_MarketDataFetch.md v1.0 ADDED
  - Calibration_State v1.20: CHAIN_3 two-mode table; CascadeLevel corrected to MONITORING

corrected_cascade_state:
  sectorStressScore: 0 (formal)
  CascadeLevel: MONITORING
  D_precursor_binding: 0 (formal)
  CHAIN_3_WATCH: TRUE — $1.304T record loaded

open_triggers:
  - Brent C-trigger clock: Day 0; BZ=F ~$93-96. Well below $110.
  - US-Iran deal: no signed agreement. A=7% unchanged.
  - CPI mid-June: BINARY EVENT — print 3/3 threshold for B formal trigger.
  - THREEFYTP10: 0.8117% rising toward 100bp E_term_premium_warning.
  - CHAIN_1: farm filings +46% vs 50%; NATURAL_GAS mandatory next session.
  - CHAIN_4: T1 corporate bankruptcy count pending.
  - MOVE: 78.43 — formal threshold pending Q2.
  - IIJA reauthorization: September 30, 2026.
  - Q2 audit: June 30, 2026.

open_decisions:
  1. PAVE: exit review deferred. EV −4.03%. Low urgency.
  2. MAGS: at target. Override in force. EV −2.17%.
  3. secular_technology_growth B: PENDING June 30.
  4. URA evaluation: PENDING June 30.
  5. US-Iran deal A-probability update: PENDING T1-confirmed signed deal.

---

date: 2026-05-29 (Q2 audit session — full M05 + §6 items 1-5, 8, 11-12, 18, 25, 27 + §7 flags)
scenario_probabilities: { A: 7%, B: 36%, C: 41%, D: 5%, E: 4%, F: 7% }
  // UNCHANGED. Iran MOU agreed at negotiator level (Axios May 28 T1: US-Iran negotiators reached
  // 60-day MOU text) but Trump approval NOT given and Iran NOT signed as of May 29.
  // M01 NEVER rule: no probability move on unsigned agreement / T2 cluster.
  // A-trigger: ELEVATED WATCH — closest pre-signing state observed. Update immediately on T1 signing.
primary_driver: US-Iran War Day ~90. BZ=F ~$91-92 (down ~19% in May — deal optimism). Hormuz mines in place; no systematic reopening confirmed. Kevin Warsh Fed Chair. DFF 3.62%.
session_type: full M05 + Q2 audit (§6 items 1-5, 8, 11-12, 18, 25, 27)

calibration_changes_this_session:
  - Calibration_State v1.22:
  - §4.1 consumer_defensive_equity C: [0,+4]⚑ → [+2,+6]★ ADOPTED HIGH confidence
      (Layer 2: 1974 +4-6% real, 1979-80 +3-5% real, 2022 XLP +6% real; 3 analogues; L4 pass)
  - §4.1 systematic_trend_following D: [-5,+15]⚑ → [-5,+15]★ status upgrade only (values confirmed)
  - §4.1 consumer_defensive_equity A: [0,+4]⚑ → [0,+4]★ status upgrade only (values confirmed)
  - §9: MOVE thresholds formally encoded (NORMAL<80, ELEVATED 80-100, STRESS 100-130, CRISIS 130-160, SYSTEMIC>160)
  - §11: URA added (new instrument — nuclear_energy_thematic)
      ComponentVector: RAC(0.50)+IHC(0.30)+STG(0.20). EV: +4.17%. Rank #3.
      Targets: Primary IRA 3%, Primary Roth 3% (funded: MAGS −2pp each, AIPO −1pp each)
      MAGS targets: IRA 5%→3%, Roth 6%→4%
      AIPO targets: IRA 8%→7%, Roth 8%→7%
  - §6 item 25: Session_Log compacted. Archive_2026Q2.md created (§7 rows Apr 19 – May 6 archived).
  - §7 new credit reading added (May 28 close, T1).

credit_readings (May 28 close, T1):
  HY: 278bps | IG: 73bps | CCC: 935bps | MOVE: 70.22 | VIX: 15.32
  All thresholds CLEAR. Credit stress declining on Iran deal optimism.

open_triggers:
  - US-Iran deal: MOU text agreed at negotiator level; Trump NOT signed; Iran NOT signed.
    A=7% unchanged. IMMEDIATE update required on T1 signed deal → run DeriveScenarioProbabilities().
    Expected A move: +8 to +15pp on signing; C/B recalibrate; BZ=F likely $75-85.
  - CPI mid-June (May data): BINARY EVENT — print 3/3 for B formal trigger (≥4.0%).
  - Brent C-trigger clock: INACTIVE. BZ=F ~$91-92 (well below $110 restart threshold).
    If deal signed → BZ=F likely falls further; C-trigger structurally inactive for foreseeable future.
  - THREEFYTP10: 0.8117% (May 15) vs 100bp E_term_premium_warning — below by ~19bp; rising.
  - CHAIN_1: farm filings +46% (below 50%); NatGas $3.10 (below $6 threshold). NORMAL.
  - CHAIN_3_WATCH: $1.304T FINRA margin debt record. Requires ≥−5% MoM to FIRE. WATCH only.
  - CHAIN_4: T1 AACER/PACER bankruptcy count pending. Score=0 until T1 confirmed.
  - MOVE: 70.22 (NORMAL, <80 new threshold). Retreating from 79.72 peak. Not elevated.
  - IIJA reauthorization: September 30, 2026 (PAVE watch).
  - secular_technology_growth B: PENDING June 30 (two competing proposals: [-2,+4] vs [-12,-3]).
  - XOM post-Hormuz ramp-up lag (~2mo): not encoded. Monitor if deal signed.

open_decisions:
  1. PAVE: exit review deferred. EV −4.03%. CascadeLevel MONITORING. IIJA Sep 30 approaching.
     Re-engage if CascadeLevel reaches ALERT or if IIJA reauthorization at risk.
  2. MAGS: targets reduced to IRA 3%, Roth 4% (this session). Override maintained.
     EV −2.17%. Continue monitoring.
  3. secular_technology_growth B calibration: PENDING June 30 adjudication (both proposals on table).
  4. §6 item 23 pending proposals (14 items): PENDING June 30 formal adoption.
  5. CHAIN_4 manufacturing: T1 formal confirmation pending (AACER/PACER).
  6. AIPO track record flag: inception Jul 2025 — thin. Re-verify at June 30.
  7. AIPO/PAVE ETN (Eaton) overlap: ~8% AIPO + ~3.4% PAVE — confirm materiality at June 30.
  8. NVDA/AVGO/AMD overlap AIPO vs MAGS: monitor at June 30.

next_session_flags:
  - LOAD: "Calibration State loaded, last update: May 29, 2026 | Session Log loaded"
  - FIRST: confirm US-Iran deal status (signed or not) — gates A probability discussion
  - FIRST: BZ=F current close — confirm C-trigger clock status
  - CPI mid-June binary event: run DeriveScenarioProbabilities() immediately on 8:30am ET release
  - June 30 Q2 audit: all remaining §5/§6 items (items 6-7, 9-10, 13-17, 19-24, 26, 29-39)
  - secular_technology_growth B adjudication at June 30: [-2,+4] vs [-12,-3]
