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
| 2026-06-01 (objective type resolution — ad-hoc) | **274** | **74** | **941** | **FRED T1 — embedded allocation spreadsheet tab.** May 31 close: HY BAMLH0A0HYM2 2.74%, IG BAMLC0A0CM 0.74%, CCC BAMLH0A3HYC 9.41%. MOVE: 73.33 (GOOGLEFINANCE). VIX: 16.05. S&P: 7,599.96. KRE: $68.31. SOFR: 3.63%. DFF: 3.62%. NatGas: $3.10 (May 26 — latest available). | **T1 — spreadsheet tab** |

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
  1. PAVE: HOLD with explicit exit triggers (v1.23). EV −4.03%. CascadeLevel MONITORING.
     EXIT on: (1) CPI ≥4.0% mid-June; (2) no IIJA action by Aug 15, 2026; (3) IIJA at reduced
     levels; (4) CascadeLevel ALERT. HOLD if: A-prob ≥20% on T1 deal; clean IIJA extension.
     Constituent analysis: Bucket A insulated (~35-45%), Bucket B partial (~30-40%),
     Bucket C at-risk highway contractors (~20-25%). See §11 PAVE for full trigger text.
  2. MAGS: HOLD-only override CONFIRMED (v1.23). Targets IRA 3%, Roth 4%. No ADD. EV −2.17%.
     Revisit if secular_technology_growth B adjudication at June 30 materially changes B value.
  3. secular_technology_growth B calibration: PENDING June 30 adjudication (both proposals on table).
  4. §6 item 23 pending proposals (14 items): PENDING June 30 formal adoption.
  5. CHAIN_4 manufacturing: T1 formal confirmation pending (AACER/PACER).
  6. AIPO track record flag: inception Jul 2025 — thin. Re-verify at June 30.
  7. AIPO EV ALERT: reclassification v1.23 moves EV from +2.16% to +0.02%. Run M13.FeasibilityCheck()
     at next full session. Review targets at June 30 given EV now near-zero vs URA +4.17%.
  8. NVDA/AVGO/AMD overlap AIPO vs MAGS: confirmed immaterial (~0.6-0.9% portfolio). No action.
  9. XOM post-Hormuz ramp-up lag (~2mo): not encoded. Monitor if deal signed.

next_session_flags:
  - LOAD: "Calibration State loaded, last update: May 30, 2026 | Session Log loaded"
  - LOAD via Desktop Commander / local git bash — NOT GitHub MCP. File: Calibration_State.md
  - FIRST: confirm US-Iran deal status (signed or not) — gates A probability discussion
  - FIRST: BZ=F current close — confirm C-trigger clock status
  - FIRST: run M13.FeasibilityCheck() with updated AIPO EV (+0.02%) — Primary IRA/Roth feasibility
  - CPI mid-June binary event: run DeriveScenarioProbabilities() immediately on 8:30am ET release
    → if ≥4.0%: B formal trigger fires → EXIT PAVE (Trigger 1)
  - PAVE watch: August 15, 2026 — exit if no congressional IIJA action of any kind by that date
  - June 30 Q2 audit: all remaining §5/§6 items (6-7, 9-10, 13-17, 19-24, 26, 29-39)
  - secular_technology_growth B adjudication at June 30: [-2,+4] vs [-12,-3]
  - M07 screens COMPLETE: FLOT PASS; VWO PASS (⚠ Taiwan/China 56.7% geopolitical concentration flag)
  - §6 items COMPLETE this session: 8, 13, 14, 15, 21, 32, 33

---

date: 2026-06-01 (objective type resolution — ad-hoc)
scenario_probabilities: { A: 7%, B: 36%, C: 41%, D: 5%, E: 4%, F: 7% }
  // UNCHANGED. No new macro binary events.
  // derivation_method: carry from 2026-05-29
primary_driver: US-Iran War Day ~93. BZ=F ~$91-92 (carry). No signed deal. DFF 3.62%. May CPI print pending mid-June.
session_type: ad-hoc — objective type review (no full M05 sequence; no allocation fetch; no market data fetch)

resolutions_this_session:
  ISSUE_1 — Relative Roth IRA objective type:
    FINDING: No mismatch. Allocation sheet is correct.
    Allocation sheet: Roth IRA (...466) | relative | 15 | TARGET_THEN_RETURN | FALSE | 0.4 | 0.3
    M13 code: TARGET_THEN_RETURN — "Used for: IRA (primary), Roth IRA (primary + relative)"
    RATIONALE: 15-year Roth horizon + no RMDs applies regardless of owner age. The 75yo age
    constraint changes the IRA objective (shorter distribution horizon → FLOOR_THEN_RETURN) but
    NOT the Roth (no RMDs, indefinite compounding horizon, TARGET_THEN_RETURN correct).
    drawdown_tolerance: 0.3 is correctly more conservative than primary Roth (0.35). Encoded correctly.
    RESOLUTION: No change to Allocation sheet. No change to Calibration_State.
    NOTE FOR FUTURE SESSIONS: Do NOT re-flag Relative Roth as FLOOR_THEN_RETURN.
    M13 classification is authoritative. This confusion arose from memory/notes — not from the files.

  ISSUE_2 — Relative IRA floor specification:
    FINDING: Floor is correctly defined. No field is misplaced.
    Allocation sheet: IRA (...469) | relative | 10 | FLOOR_THEN_RETURN | TRUE | 0.4 | 0.2
    floor_nominal_loss: TRUE — correct; M13 struct defines this as Bool where true = constraint active.
    The floor level itself is implicit in M13.FeasibilityCheck() FLOOR_THEN_RETURN branch:
      "IF scenario_return_s < 0 → floor_breach = true" — floor = zero nominal loss.
    Probability threshold for which scenarios to test: §4.4 floor_nominal_loss_probability_threshold = 15%.
    drawdown_tolerance: 0.2 is a separate position-sizing constraint (used in MLPX 24% × 67% = 16.1%
    < 20% calculation). It is NOT the floor — it operates in a different function.
    RESOLUTION: No change to Allocation sheet. No change to Calibration_State.
    NOTE FOR FUTURE SESSIONS: floor_nominal_loss (Bool=TRUE) + M13 §4.4 threshold (15%) +
    zero-return floor in FeasibilityCheck() are three separate components that together define the
    complete FLOOR_THEN_RETURN constraint. drawdown_tolerance (0.2) is the position-sizing guard —
    a distinct parameter. Neither is a misplaced value.

credit_readings (May 31 close, T1 — via embedded allocation spreadsheet):
  HY: 274bps | IG: 74bps | CCC: 941bps | MOVE: 73.33 | VIX: 16.05 | S&P: 7,599.96
  KRE: $68.31. SOFR: 3.63%. DFF: 3.62%.
  HY 274bps: −4bps from May 28. IG 74bps: +1bp. CCC 941bps: +6bps. All thresholds CLEAR.
  CCC quietly widening (+6bps in 3 days) while HY tightening — divergence watch. No threshold fires.
  MOVE 73.33: NORMAL zone (<80). Retreating from May 22 peak.

open_triggers: (carry from 2026-05-29 — no changes)
  - US-Iran deal: MOU text agreed at negotiator level; Trump NOT signed. A=7% unchanged.
  - CPI mid-June (May data): BINARY EVENT — B formal trigger on ≥4.0% (3rd print).
  - Brent C-trigger clock: INACTIVE. BZ=F ~$91-92 (carry).
  - THREEFYTP10: 0.8117% vs 100bp warning — below by ~19bp.
  - CHAIN_3_WATCH: $1.304T FINRA margin debt record. No FIRE condition met.
  - CHAIN_4: T1 AACER/PACER bankruptcy count pending.
  - IIJA reauthorization: September 30, 2026 (PAVE watch).
  - Q2 audit: June 30, 2026.
  - CCC divergence watch: +6bps in 3 days while HY tightening. Not at threshold — monitor.

open_decisions: (carry from 2026-05-29 — no changes)
  1. PAVE: HOLD with explicit exit triggers (v1.23). EV −4.03%. CascadeLevel MONITORING.
  2. MAGS: HOLD-only override CONFIRMED. EV −2.17%. No ADD.
  3. secular_technology_growth B calibration: PENDING June 30.
  4. §6 item 23 pending proposals (14 items): PENDING June 30.
  5. CHAIN_4 manufacturing: T1 formal confirmation pending.
  6. AIPO track record flag: inception Jul 2025. Re-verify at June 30.
  7. AIPO EV ALERT: EV +0.02%. Run M13.FeasibilityCheck() at next full session.
  8. XOM post-Hormuz ramp-up lag (~2mo): not encoded. Monitor if deal signed.

next_session_flags:
  - LOAD: "Calibration State loaded, last update: May 30, 2026 | Session Log loaded"
  - FIRST: confirm US-Iran deal status (signed or not) — gates A probability discussion
  - FIRST: BZ=F current close — confirm C-trigger clock status
  - FIRST: run M13.FeasibilityCheck() with updated AIPO EV (+0.02%) — Primary IRA/Roth feasibility
  - CPI mid-June binary event: run DeriveScenarioProbabilities() immediately on 8:30am ET release
    → if ≥4.0%: B formal trigger fires → EXIT PAVE (Trigger 1)
  - PAVE watch: August 15, 2026 — exit if no congressional IIJA action of any kind by that date
  - June 30 Q2 audit: all remaining §5/§6 items (6-7, 9-10, 13-17, 19-24, 26, 29-39)
  - Relative Roth / Relative IRA objective type: RESOLVED 2026-06-01. DO NOT re-flag.
    See §8 entry 2026-06-01 resolutions_this_session for full findings.
  - CCC divergence: +6bps in 3 days while HY tightening — watch for acceleration at next session.
