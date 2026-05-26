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
| 2026-05-25 (second M05 — v1.20 framework evaluation) | 278 (carry) | 75 (carry) | 939 (carry) | Carry — Memorial Day; no new FRED data. BZ=F intraday (Memorial Day session): ~$93-96 (down ~6% from $100.21 May 22 close) on US-Iran deal optimism. S&P futures: +0.95% (reversed from prior −2.7% overnight). DXY ~98.92. Gold $4,523, Silver $76.15 (May 22). Kevin Warsh sworn in as 17th Fed Chairman May 22. | T1 carry; BZ=F T2 (Investing.com/Trading Economics CFD); equities T2 |  

---

## Section 8 - Session State Log

date: 2026-04-30
scenario_probabilities: { A: 7%, B: 42%, C: 42%, D: 3%, E: 3%, F: 3% }
primary_driver: Strait of Hormuz Crisis / US-Iran War (Day 61)
open_decisions: SUPERSEDED by May 13 full session

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
1. PAVE: CascadeLevel (formerly ALERT, now MONITORING after v1.20 correction) — exit review deferred to next session. EV −4.03%. IIJA Sep 30 expiry approaching.
2. MAGS: at target. Override in force. EV −2.17% (deteriorating).
3. secular_technology_growth B calibration: PENDING June 30.
4. URA evaluation: PENDING June 30.
5. XOM post-Hormuz ramp-up lag: ~2mo not encoded. Monitor.
6. Goldman Brent $90 Q4: T1 not confirmed. Carry.
7. CHAIN_4 manufacturing: T1 formal confirmation pending.
8. S&P Futures gap: +0.95% as of Memorial Day (reversed from prior −2.7%); confirm Tuesday May 26 open.

next_session_flags:
  - LOAD: "Calibration State loaded, last update: May 25, 2026 | Session Log loaded"
  - CPI mid-June binary event: run DeriveScenarioProbabilities() immediately on release at 8:30am ET
  - Brent C-trigger clock: Day 0 but now ~$93-96 (Memorial Day) — deal news; watch for T1-confirmed signed deal before A probability update
  - US-Iran deal: Trump "largely negotiated" (T2); NO signed deal as of May 25; A NOT updated (M01 standard not met — T2 cluster, no T1 signed agreement, no permanent Hormuz reopening verified); next session: confirm deal status
  - PAVE discussion pending
  - Calibration_State §12 cleanup: duplicate §12 block + cascadeLevel table cleanup deferred
  - June 30 Q2 audit: all calibration items per §5 and §6

---

date: 2026-05-25 (second M05 session — v1.20 framework evaluation)
scenario_probabilities: { A: 7%, B: 36%, C: 41%, D: 5%, E: 4%, F: 7% }
  // UNCHANGED from v1.19. Trump deal announcement (BZ=F −6% to ~$93-96; S&P futures +0.95%)
  // evaluated but A NOT updated per M01 source integrity:
  //   - Trump "largely negotiated" = T2 (political actor, self-interest in claiming progress)
  //   - Trump walked back same day: "isn't even fully negotiated yet"
  //   - Iran FM: "consensus on many topics, signing not imminent" (T2)
  //   - No signed deal; no permanent Hormuz reopening; 3 tankers = T1-quality but already
  //     noted in v1.19 session; BZ=F −6% = market speculation, not verified event
  //   - M01 NEVER rule: do not move probabilities on single unverified report or T2 cluster
  //   - A update deferred until: signed agreement OR T1-confirmed systematic Hormuz reopening
primary_driver: US-Iran War / Hormuz ceasefire negotiations Day ~86. BZ=F ~$93-96 Memorial Day (deal optimism). Kevin Warsh sworn in as Fed Chair May 22.
session_type: second M05 session same day (framework evaluation + v1.20 bug fixes)

framework_changes_this_session:
  - FW-BUG-01 FIXED: M17 v1.3 — CHAIN_3 two-mode scoring (WATCH on record, FIRES on −5% decline or 3+ gates)
  - FW-BUG-02 CONFIRMED FIXED: Phase 2 complete in prior commit (M02 v2.0, M04 v2.0, M11/M14/M17 registered)
  - M18_MarketDataFetch.md v1.0 ADDED: centralized DATA_REGISTRY_ENTRIES for all framework series
  - M17 DATA_REGISTRY_ENTRIES → _LEGACY (superseded by M18)
  - Calibration_State v1.20: CHAIN_3 two-mode table in §12.3; D_precursor_binding clarified in §12.8; CascadeLevel corrected to MONITORING
  - All pushed to master in single commit by client

corrected_cascade_state:
  sectorStressScore: 0 (formal) — CHAIN_3 WATCH (not FIRES); CHAIN_4 pending T1
  CascadeLevel: MONITORING (corrected from ALERT in v1.19)
  D_precursor_binding: 0 (formal); yield curve D_timing_signal = informational only
  D=5%: maintained by prior client approval (qualitative basis); NOT mechanically derived
  CHAIN_3_WATCH: TRUE — $1.304T record loaded; cascade onset requires ≥−5% MoM or 3+ gate events

open_triggers:
  - Brent C-trigger clock: Day 0; BZ=F now ~$93-96 (Memorial Day, deal optimism). Well below $110. Clock restart requires close ≥$110.
  - US-Iran deal: no signed agreement as of May 25. A=7% unchanged. Next session: verify deal status before probability update.
  - CPI mid-June: BINARY EVENT — print 3/3 threshold for B formal trigger.
  - THREEFYTP10: 0.8117% rising toward 100bp E_term_premium_warning.
  - CHAIN_1: farm filings +46% vs 50% threshold; NATURAL_GAS data gap — mandatory next session.
  - CHAIN_4: T1 corporate bankruptcy count (AACER/PACER) pending.
  - MOVE: 78.43 — below 80 watch level; formal threshold pending Q2.
  - IIJA reauthorization: September 30, 2026.
  - Calibration_State §12 cleanup: duplicate §12 block + cascade table fix (minor, deferred).
  - Q2 audit: June 30, 2026.

open_decisions:
  1. PAVE: exit review deferred. EV −4.03%. CascadeLevel now MONITORING (not ALERT). IIJA Sep 30 still approaching. Low urgency.
  2. MAGS: at target. Override in force. EV −2.17%.
  3. secular_technology_growth B: PENDING June 30.
  4. URA evaluation: PENDING June 30.
  5. US-Iran deal A-probability update: PENDING T1-confirmed signed deal or systematic Hormuz reopening.
  6. NATURAL_GAS fetch: mandatory next session (CHAIN_1 borderline).
  7. S&P Tuesday May 26 open: confirm gap from futures (+0.95% as of Memorial Day).

next_session_flags:
  - LOAD: "Calibration State loaded, last update: May 25, 2026 | Session Log loaded"
  - FIRST: confirm US-Iran deal status (signed or not) — gates A probability discussion
  - FIRST: confirm S&P May 26 open vs futures gap
  - MANDATORY: fetch NATURAL_GAS (CHAIN_1 borderline)
  - CPI mid-June binary event: run DeriveScenarioProbabilities() immediately on 8:30am ET release
  - Calibration_State §12 duplicate block cleanup (minor; do at next convenient session)
  - June 30 Q2 audit: all §5/§6 items
