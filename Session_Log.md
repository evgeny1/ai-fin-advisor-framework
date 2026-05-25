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
| 2026-04-19 | 285 | 83 | 921 | Trading Economics / FRED | composite_only |
| 2026-04-21 | 285 | 83 | 921 | Trading Economics / FRED (stale Apr 15-16) | stale |
| 2026-04-22 | 287 | 83 | 921 | Trading Economics / FRED (HY Apr 20; IG/CCC Apr 16-17) | stale |
| 2026-04-23 | 287 | 83 | 921 | Trading Economics / FRED (stale 3-7 days) | stale |
| 2026-04-28 | 285 | 83 | 921 | Trading Economics / FRED (stale 7-12 days) | stale |
| 2026-04-29 | 284 | 80 | 921 | Trading Economics proxy; FRED HY Apr 28; IG T2 cross-ref; CCC carry | stale (IG: composite_only) |
| 2026-04-30 (ad-hoc) | - | - | - | No credit fetch - ad-hoc session | n/a |
| 2026-04-30 (full) | 284 (carry) | 80 (carry) | 921 (carry) | Carry from Apr 29. MOVE FIRST LOGGED: 68.68 (Investing.com T2) | stale; MOVE T2 |
| 2026-05-06 (full AM) | 284 (carry) | 80 (carry) | 921 (carry) | Carry from Apr 30. FRED fetch attempted — metadata only. | stale |
| 2026-05-06 (instrument expansion) | 277 (ycharts T2, May 1) | 80 (carry) | 921 (carry) | ycharts May 1; MOVE ~76.8 (TradingView T2). | stale |
| 2026-05-07 (full) | 277 (carry) | 80 (carry) | 921 (carry) | Carry. FRED still metadata only. | stale |
| 2026-05-11 (full) | **281** | **79** | **920** | **FRED T1 — DATA GAP RESOLVED.** BAMLH0A0HYM2, BAMLC0A0CM, BAMLH0A3HYC: May 8 close. MOVE: 70.74 T1 (NYSE Global Indexes). | **T1 — gap resolved** |
| 2026-05-13 (full) | **282** | **77** | **937** | **FRED T1 — embedded allocation spreadsheet tab.** May 12 close. MOVE: 70.74 carry. | **T1 — spreadsheet tab** |
| 2026-05-22 (full) | **278** | **75** | **939** | **FRED T1 — embedded allocation spreadsheet tab.** May 21 close. MOVE: 79.72 GOOGLEFINANCE. VIX: 16.52. S&P 500: 7,494.81. | **T1 — spreadsheet tab** |
| 2026-05-25 (research/dev + full M05) | 278 (carry) | 75 (carry) | 939 (carry) | FRED T1 via allocation spreadsheet tab — May 21 close (most recent; May 25 is Sunday/Memorial Day). Also confirmed: BAMLC0A4CBBB (BBB OAS) 94 bps; SOFR 3.51%; DFF 3.62%; SOFR–DFF spread −11bp (normal). MOVE: 78.43 (GOOGLEFINANCE live). VIX: 16.70. S&P 7,473.47 (May 22 close). S&P Futures overnight: 7,268.25 (−2.7%). FINRA margin debt: $1.304T (Apr 2026 record). THREEFYTP10: 0.8117% (May 15 — 14-yr high). Yield curve (FMP May 22): 10Y–2Y +43bp; 10Y–3M +88bp; 30Y 5.07%. BZ=F overnight ~$107.60 (Yahoo Finance pre-market T2, Memorial Day). | **T1 — spreadsheet tab + FMP** |

---

## Section 8 - Session State Log

date: 2026-04-30
scenario_probabilities: { A: 7%, B: 42%, C: 42%, D: 3%, E: 3%, F: 3% }
primary_driver: Strait of Hormuz Crisis / US-Iran War (Day 61)
open_decisions: SUPERSEDED by May 13 full session

---

date: 2026-05-22 (full M05 session — v1.18)
scenario_probabilities: { A: 7%, B: 36%, C: 44%, D: 3%, E: 3%, F: 7% }
primary_driver: US-Iran War Day ~83 / Hormuz closure ongoing. Iran Strait Authority announced (permanent Hormuz toll). Trump rejected. BZ=F pre-market ~$109.11. Brent 52-wk high $126.41 confirmed.
derivation_method: carry_forward (no new binary events since May 13)
session_type: full M05 (Calibration State v1.17; gold reallocation confirmed executed)

open_triggers:
- [RESOLVED] Brent C-trigger clock: Day 0 confirmed T2 (May 25) — max ~5-6 consecutive closes ≥$110; clock reset ~May 20.
- Iran Strait Authority: structural C escalation. Log for June 30.
- MOVE: 79.72 and rising. Watch; no formal threshold yet.
- CPI mid-June: if ≥4.0% → B trigger fires.
- IIJA: September 30, 2026.
- Q2 audit: June 30, 2026.

open_decisions:
1. Gold reallocation: CLOSED — CONFIRMED EXECUTED.
2. MAGS: at target. Override in force.
3. secular_technology_growth B: PENDING June 30.
4. URA evaluation: PENDING June 30.

consolidated_target_allocations: v1.18 — see Calibration_State.md.

next_session_flags: SUPERSEDED by May 25 full M05 session

---

date: 2026-05-25 (full M05 session — v1.19)
scenario_probabilities: { A: 7%, B: 36%, C: 41%, D: 5%, E: 4%, F: 7% }
  // UPDATED from May 22 carry (A=7/B=36/C=44/D=3/E=3/F=7)
  // DeriveScenarioProbabilities() run with D_precursor_binding=2 (M17 §12 CascadeLevel ALERT)
  // D: 3%→5% (+2pp), E: 3%→4% (+1pp), C: 44%→41% (−3pp). Client approved.
  // derivation_method: scored (D_precursor overlay via M17 §12; M11 formal triggers not fired)
primary_driver: US-Iran War / Hormuz closure Day ~86. Brent C-trigger clock Day 0 (T2 confirmed — max ~5-6 consecutive closes ≥$110 May 13-19; clock reset ~May 20 on deal optimism + Hormuz satellite data showing 3 supertankers crossing). BZ=F overnight (Memorial Day) ~$107.60. Iran Strait Authority (permanent toll rejected by Trump) + uranium retained inside Iran. Rubio soft A-signal (T1 unconfirmed). D/E precursor stack: CascadeLevel ALERT. US markets closed Memorial Day.
session_type: full M05 (v1.19 — §12 pushed to Calibration_State; probabilities updated)

open_triggers:
- Brent C-trigger clock: Day 0. BZ=F ~$107.60 overnight. Watch for close ≥$110 to restart.
- Iran Strait Authority: structural C escalation (permanent toll rejected by Trump). No resolution timeline.
- CPI mid-June (May data): BINARY EVENT — if ≥4.0% → B formal trigger fires (3rd print). Run DeriveScenarioProbabilities() immediately on release.
- MOVE: 78.43 — approaching 80; no formal threshold yet (June 30 assessment).
- E_term_premium_warning: THREEFYTP10 0.8117% (14-yr high, rising) vs 100bp warning — not yet fired; trajectory suggests possible crossing before Q2.
- CHAIN_1 watch: farm filings +46% vs +50% threshold — next USDA quarterly data may fire.
- CHAIN_4: T1 formal confirmation pending (qualitatively fired).
- IIJA reauthorization: September 30, 2026 (PAVE watch).
- Q2 audit: June 30, 2026.

open_decisions:
1. PAVE exit review: CascadeLevel ALERT activates M17 §5 exit window. EV ~−3.84% (negative; worsens with D=5%). Embedded gain ~$427 (502sh × ~$0.85). IIJA expiry Sep 30. Taxable Acc4 currently 10.39% vs 11% target. Pending portfolio discussion.
2. MAGS: at target. Override in force. EV now ~−2.17% (deteriorating — D=5% hits secular_tech hardest at D conservative −14%).
3. secular_technology_growth B calibration: PENDING June 30.
4. URA evaluation: PENDING June 30.
5. XOM post-Hormuz ramp-up lag: ~2mo not encoded in Calibration_State. Monitor.
6. Goldman Brent $90 Q4: T1 not confirmed. Carry.
7. CHAIN_4 manufacturing: T1 formal confirmation pending.
8. S&P Futures overnight −2.7% (7,268 vs 7,473 May 22 close): confirm when US markets open Tuesday May 26.

next_session_flags:
  - LOAD: "Calibration State loaded, last update: May 25, 2026 | Session Log loaded"
  - CPI mid-June binary event: run DeriveScenarioProbabilities() immediately on release at 8:30am ET
  - Brent C-trigger clock: Day 0; watch for BZ=F close ≥$110 to restart
  - PAVE discussion (if not completed this session)
  - CHAIN_1: next USDA farm filing data
  - MOVE watch: formal threshold integration at June 30
  - S&P Futures gap: confirm when US markets open Tuesday May 26
  - June 30 Q2 audit: all calibration items per §5 and §6
  - Architecture Phase 2 when ready: M02 FetchRegistry + M04 BriefingRegistry
