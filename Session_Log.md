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
| 2026-04-29 | 284 | 80 | 921 | Trading Economics proxy; FRED HY Apr 28; IG T2 cross-ref (~80 bps near 25yr tights); CCC carry | stale (IG: composite_only) |
| 2026-04-30 (ad-hoc) | - | - | - | No credit fetch - ad-hoc session | n/a |
| 2026-04-30 (full) | 284 (carry) | 80 (carry) | 921 (carry) | Carry from Apr 29. MOVE FIRST LOGGED: 68.68 (Investing.com T2; 52-wk range 55.77-115.02; bond market calm; no fixed income stress) | stale; MOVE T2 |
| 2026-05-06 (full AM) | 284 (carry) | 80 (carry) | 921 (carry) | Carry from Apr 30. FRED fetch attempted — search returned series metadata only; no live values retrieved. govspending.org confirms HY 2.83% (283 bps) as of Apr 30 — consistent with carry. No material divergence expected given equity rally and energy de-escalation, but unconfirmed. MOVE: not fetched — persistent data gap. | stale |
| 2026-05-06 (instrument expansion) | 277 (ycharts T2, May 1) | 80 (carry) | 921 (carry) | ycharts May 1 reading consistent with tightening on deal optimism. HY declining from 284 baseline — directionally confirms equity rally / credit risk-on. MOVE: ~76.8 (TradingView T2, recent) — rising from 68.68 Apr 30 baseline but below 80 (calm threshold). No thresholds fired. | stale (T1_flag: FRED unavailable) |
| 2026-05-07 (full) | 277 (carry) | 80 (carry) | 921 (carry) | Carry from May 6. FRED still returning metadata only — persistent data gap. Directional signal: HY tightening expected given deal optimism + VIX 17.39 (Cboe T1). MOVE: not fetched — persistent data gap. JNK index ~306 bps (24/7 Wall St T2, ~May 5) — note: different series from BAMLH0A0HYM2; not substitutable. No thresholds fired. | stale (T1_flag: FRED unavailable) |
| 2026-05-11 (full) | **281** | **79** | **920** | **FRED T1 — DATA GAP RESOLVED.** BAMLH0A0HYM2 (HY), BAMLC0A0CM (IG), BAMLH0A3HYC (CCC): all May 8 close, confirmed via FRED screenshots provided by client. MOVE: 70.74 T1 (NYSE Global Indexes, 15-min delay, May 11 intraday). Approved source URLs logged in Calibration_State §1. All thresholds: NO FIRE. HY below baseline (285 Apr 19); IG below baseline (83 Apr 19); CCC at baseline (~921); MOVE calm (<80). | **T1 — gap resolved** |
| 2026-05-13 (full) | **282** | **77** | **937** | **FRED T1 — embedded allocation spreadsheet tab** (BAMLH0A0HYM2, BAMLC0A0CM, BAMLH0A3HYC: all May 12 close, direct FRED feed in allocation spreadsheet new tab). MOVE: 70.74 carry from May 11 T1 — new spreadsheet MOVE tab present but value not separately parsed this session; carry forward. All thresholds: NO FIRE. HY +1 bp (282 vs 281); IG −2 bps (77 vs 79 — slight tightening despite hot CPI); CCC +17 bps (937 vs 920 — minor widening; 30d divergence check: CCC +17 vs HY +1; 3× ratio technically fires (17>3×1=3) but absolute floor requires +200 bps not met → NOT triggered). VIX 17.97 pre-market (calm). | **T1 — spreadsheet tab** |

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
session_type: full M05

open_triggers:
- Brent $110 C-trigger clock: Day 2 of 10 active. Monitor every session without exception.
- CPI May 10-12: second print. If >=3.5% YoY -> C check_cpi to 2; C probability rises.
- IIJA reauthorization September 30, 2026 (PAVE watch status trigger)

open_decisions:
- Client reviewing M13 target allocations.
- VTI: wash sale window cleared April 30. VTI purchase CANCELLED.
- AIPO and MAGS: new positions pending client approval.
- Taxable Acc4 XAR: 180-share staged sell at $265 pending verification.
- AIPO §11 classification: provisional — ThematicETF_ClassificationAudit() required Q2.

M13 target allocations (for client allocation file update):
- Primary IRA:   MLPX 40% | SGOL 33% | XAR 12% | AIPO 8% | MAGS 7%
- Primary Roth:  MLPX 40% | SGOL 33% | XAR 12% | AIPO 8% | MAGS 7%
- Taxable Acc3:  SGOV 100%
- Taxable Acc4:  MLPX 40% | SGOV 29% | XAR 12% | AIPO 8% | PAVE 11%
- Relative IRA:  MLPX 35% | SGOL 37% | SGOV 20% | AIPO 5% | MAGS 3%
- Relative Roth: MLPX 40% | SGOL 40% | AIPO 12% | MAGS 8%

next_session_flags: [SUPERSEDED by May 6 sessions]

---

date: 2026-05-06 (full AM session — v1.10/v1.11)
scenario_probabilities: { A: 15%, B: 36%, C: 36%, D: 3%, E: 3%, F: 7% }
primary_driver: Strait of Hormuz Crisis / US-Iran War (Day 68) — deal framework reported (Axios/CBS/NPR) but unconfirmed as of session close; Hormuz still operationally restricted
derivation_method: scored
manual_override_reason: null
session_type: full M05 (Allocation sheet fetched via Google Drive MCP; Calibration State fetched via GitHub MCP; credit carry-forward)

scoring_basis:
- A: check_fed=0 | check_energy=1 (declining 3 days, not >=5) | check_credit=1 (calm) → raw=2
- B: check_cpi=2 (3.3% YoY, 3-4% trending) | check_gdp=1 (GDP +2.0%, >1.5%) | check_fed=2 (holding + constraint language) → raw=5
- C: check_brent=2 (clock broken; active supply event T1; within band) | check_cpi=1 | check_chokepoint=2 (Hormuz active T1) → raw=5
- D: raw=0 → floor 3%
- E: raw=0 → floor 3%
- F: raw=1 → derived 7%

returns_table_actions_this_session:
- ADOPTED v1.11: real_asset_contracted_revenue B [3,7]→[6,14]; C [3,6]→[8,16].
- PENDING June 30: 14 additional revision proposals logged in §6 item 23.
- MLPX §11 EV updated: +3.64%→+5.51%.

open_triggers:
- Brent C-trigger clock: RESET to Day 0. New clock requires 10 consecutive days above $110.
- CPI May 10-12: BINARY EVENT — highest near-term priority.
- US-Iran deal confirmation: IF T1-confirmed → recalibrate (A→25%+, C→<25%).

open_decisions:
- XAR reduction to 12% target: UNCONFIRMED as of this session.
- MLPX ADD: EntryExtensionGuard BLOCKING. Do not ADD until guard clears.
- MLPX Relative IRA drawdown tolerance breach: 34% × 67% = 22.8% > 20% floor.
- Taxable Acc4 cash ~$52K: route to SGOV per M13 targets.
- M13.FeasibilityCheck() rerun required.

M13 target allocations: [per April 30 — unchanged]

next_session_flags: [SUPERSEDED by May 6 instrument expansion session]

---

date: 2026-05-06 (instrument expansion session — v1.13)
scenario_probabilities: { A: 18%, B: 35%, C: 34%, D: 3%, E: 3%, F: 7% }
primary_driver: Strait of Hormuz Crisis Day 68 / US-Iran deal framework — Axios/CBS/NPR T1 reports one-page MOU framework under review; Trump "too soon to sign"; Iran reviewing via Pakistani mediators. Deal UNCONFIRMED as of session close. Brent $101.27 close (NBC T1). S&P 500 record high +1.46%.
derivation_method: scored
manual_override_reason: null
session_type: full M05 + comprehensive instrument expansion

scoring_basis (updated from prior session):
- A: check_fed=0 | check_energy=2 (Brent -12% from peak on deal news — sustained decline above 5%) | check_credit=1 (calm; HY ~277 bps) → raw=3 (+1 vs prior)
- B: check_cpi=2 | check_gdp=1 | check_fed=2 → raw=5 (unchanged)
- C: check_brent=2 (within $93.50-$110 band; active supply event T1; Hormuz still restricted) | check_cpi=1 | check_chokepoint=2 → raw=5 (unchanged, but deal progress noted)
- D: raw=0 → floor 3%
- E: raw=0 → floor 3%
- F: raw=1 → 7% (unchanged)

probability_shifts_vs_prior:
- A: 15% → 18% (+3pp): check_energy upgraded 1→2 on Brent -12% deal-driven decline; deal proximity signal. Hard cap: T1-confirmed deal required for A→25%+.
- B: 36% → 35% (-1pp): minor de-escalation offset; sticky inflation fundamentals unchanged
- C: 36% → 34% (-2pp): energy de-escalation at margin slightly reduces acute inflationary shock probability; Brent below $110; deal direction reduces chokepoint severity
- D: 3% → 3% (0pp): unchanged
- E: 3% → 3% (0pp): unchanged
- F: 7% → 7% (0pp): GDP +2.0% + equity record highs priced in from prior session

M14_divergence:
- commodity_fear_divergence: MODERATE (energy_90d ~+63% >= +10%; VIX_change_90d ~+3.4 pts — above 0, within +5)
- equity_scenario_divergence: HIGH (S&P 30d +10.3% >= +5%; B/C directive for broad_market_equity is reductive)
- composite: HIGH (upgraded from MODERATE)
- UnderweightReviewTrigger: fired for Primary IRA MLPX (-9.82pp) and Primary Roth MLPX (-10.28pp)

framework_updates_this_session:
- 5 new roles added to §11.1: systematic_trend_following, consumer_defensive_equity, healthcare_defensive_equity, floating_rate_credit_income, emerging_market_equity
- §4.1 fully calibrated (M16 4-layer): systematic_trend_following A/B/C ADOPTED HIGH confidence; consumer_defensive_equity B ADOPTED HIGH confidence; all other new role values PENDING June 30
- 9 new instruments classified in §11.3: DBMF, SIVR, COPX, VTIP, XLP, VNQ, VEA, XLV, FLOT
- New EV rankings: DBMF #1 (+8.47%), MLPX #2 (+5.38%), COPX #3 (~+3.5-4.5% adj), AIPO #4 (+2.95%), SIVR #5 (+2.86%)
- M07 regional ruling: "region" = political/economic bloc (not continent); COPX PASSES
- K-1 determination: DBMF issues NO K-1 (1940 Act registered fund, swap structure)
- Primary IRA structural gap RESOLVED: +3.62% achievable (required 3.2%)

open_triggers:
- CPI May 10-12: BINARY — HIGHEST PRIORITY. If >=3.5% → C check_cpi=2 → C rises materially. If <=3.0% → B check_cpi=0 → B falls sharply. Run DeriveScenarioProbabilities() immediately on release.
- US-Iran deal: IF T1-confirmed → A rises to 25%+, C falls below 25%. Triggers: (1) XAR reduction urgency increases; (2) VNQ/VEA adoption conditional unlocked; (3) MLPX war premium guard retired.
- MLPX EntryExtensionGuard: PRELIMINARY CLEARING. Obtain MLPX Feb 5, 2026 historical close from approved source. If confirmed 15% guard clears → ADD eligible in Primary IRA/Roth.
- SIVR EntryExtensionGuard: Likely BLOCKING. Compute 90d trailing silver price before any ADD.
- COPX EntryExtensionGuard: Likely BLOCKING. Compute 90d trailing COPX price before any ADD.
- IIJA reauthorization September 30, 2026 (PAVE watch trigger — unchanged).
- Brent C-trigger clock: Day 0. Initiation requires fresh 10-day sequence above $110. Currently declining on deal news; unlikely near-term unless deal collapses.

open_decisions:
1. CPI May 10-12 [BINARY — TIME-SENSITIVE]: highest priority. Pre-position for immediate DeriveScenarioProbabilities() run.
2. XAR: CONFIRMED AT 12% TARGET across all accounts per allocation sheet. Open Decision #2 CLOSED.
3. MLPX Relative IRA drawdown: RESOLVED by target reduction to 24% (v1.13 targets). Client accepts resolution. Document formally.
4. Taxable Acc4 cash ~$52K ($51,949.87): deploy per new v1.13 targets — SGOV to 15% (~$39.3K after XAR proceeds deployed), DBMF new position, XLP new position, COPX when guard clears.
5. Primary IRA/Roth cash (from XAR proceeds): deploy per v1.13 targets — DBMF and VTIP immediate; MLPX ADD pending guard verification; SIVR pending guard.
6. MLPX 90d trailing price: obtain Feb 5, 2026 MLPX close from Yahoo Finance historical. Compute precise guard threshold.
7. SIVR and COPX 90d trailing prices: compute guard thresholds before execution.
8. MAGS reductions: 7%→5% Primary IRA; 7%→6% Primary Roth (client to confirm override adjustment).

consolidated_target_allocations (v1.13 — AUTHORITATIVE — update allocation file):
- Primary IRA:     MLPX 30% | DBMF 15% | SGOL 16% | XAR 12% | AIPO 8% | VTIP 8% | SIVR 4% | MAGS 5% | COPX 2%
- Primary Roth:    MLPX 28% | DBMF 17% | SGOL 14% | XAR 12% | VTIP 10% | AIPO 8% | SIVR 5% | MAGS 6%
- Primary Taxable: MLPX 30% | SGOV 15% | XAR 12% | AIPO 8% | PAVE 11% | DBMF 10% | COPX 7% | XLP 7%
- Taxable Pres.:   SGOV 100%
- Relative IRA:    SGOL 26% | MLPX 24% | DBMF 12% | VTIP 12% | SGOV 14% | AIPO 6% | SIVR 3% | MAGS 3%
- Relative Roth:   MLPX 32% | DBMF 18% | SGOL 22% | VTIP 10% | AIPO 10% | MAGS 8%

portfolio_ev_by_account (v1.13, A=18/B=35/C=34/D=3/E=3/F=7):
- Primary IRA: +3.62% (required 3.2% — GAP CLOSED)
- Primary Roth: +3.62% (required ~2.8% — exceeds +0.82pp)
- Primary Taxable: +2.99% (RETURN_THEN_TARGET 5yr)
- Taxable Preservation: capital preservation (SGOV 100%)
- Relative IRA: +3.04% (FLOOR_THEN_RETURN; drawdown breach resolved)
- Relative Roth: +3.79% (required ~2.8% — exceeds +0.99pp)

next_session_flags: [SUPERSEDED by May 7 full session]

---

date: 2026-05-07 (full M05 session — v1.15)
scenario_probabilities: { A: 15%, B: 36%, C: 36%, D: 3%, E: 3%, F: 7% }
primary_driver: US-Iran peace deal framework — Axios/WSJ/CBS/NBC (T1) reporting one-page MOU under development; talks potentially beginning next week in Islamabad via Pakistani mediators. Trump: "too soon to sign." Iran: "evaluating US proposal." Major disagreements remain on enrichment limits, inspections, sequencing. Hormuz operationally restricted. Brent ~$97 intraday (CNBC T1, -3%). Deal UNCONFIRMED. VIX 17.39 (Cboe T1).
derivation_method: scored
manual_override_reason: null
session_type: full M05 (Allocation sheet fetched ×2 — second fetch captured post-trade state; Calibration State v1.14 fetched GitHub MCP; Session Log fetched GitHub MCP)

scoring_basis:
- A: check_fed=0 (FOMC hold 3.5-3.75%; 4 hawkish dissents) | check_energy=1 (Brent declining 4 consecutive days May 4-7; threshold ≥5 not met) | check_credit=1 (HY ~277 carry, calm) → raw=2
  NOTE: day 5 threshold (May 8): if Brent remains below ~$101, check_energy upgrades to 2 → A returns to ~18%. Monitor immediately next session.
- B: check_cpi=2 (CPI 3.3% YoY, 3-4% trending; no new print) | check_gdp=1 (GDP +2.0%, >1.5%) | check_fed=2 (holding + constraint language) → raw=5 (unchanged)
- C: check_brent=2 (active supply event T1; Brent $97 within $93.50-$110 band) | check_cpi=1 (1 print confirmed) | check_chokepoint=2 (Hormuz T1-verified active; ACLED/ISW) → raw=5 (unchanged)
- D: raw=0 → floor 3%
- E: raw=0 → floor 3%
- F: check_gdp=1 (GDP 2-3% range) | check_cpi=2 (3.3%, 2-4% rising) | check_fed=0 (holding not tightening with strong demand) | check_noshock=-2 (Hormuz T1-verified) → raw=MAX(1,0)=1

probability_shifts_vs_prior (prior: A=18, B=35, C=34, D=3, E=3, F=7 from May 6 v1.13):
- A: 18% → 15% (-3pp): check_energy=1 this session (4 consecutive days declining, not yet 5-day threshold). No other scoring input changed. Cap: -3pp well within 25pp.
- B: 35% → 36% (+1pp): rounding artifact; structural score raw=5 unchanged.
- C: 34% → 36% (+2pp): rounding artifact; structural score raw=5 unchanged. Hormuz active and scored; Brent within band.
- D: 3% → 3% (0pp)
- E: 3% → 3% (0pp)
- F: 7% → 7% (0pp)
B/C justification (both >30%): Both scenarios fully scored at raw=5. Primary driver (Hormuz + CPI) simultaneously feeds B (rate constraint + CPI persistence) and C (chokepoint severity + supply shock). Equal scoring mechanically correct.

M14_divergence (updated):
- commodity_fear_divergence: MODERATE (energy_90d ~+29-38% ≥ +10%; VIX_change_90d ~+2.4 pts ≤ +5 but >0 → not HIGH)
- equity_scenario_divergence: HIGH (S&P 30d ~+10% ≥ +5%; B/C directive for broad equity reductive)
- composite: HIGH (unchanged from May 6 v1.13)
- UnderweightReviewTrigger: NOT fired at v1.13 target levels (Primary IRA MLPX 29.69% vs 30% target = -0.31pp gap, below 5pp threshold). Relative IRA MLPX OVERWEIGHT +9.4pp (33.92% vs 24% target) — pending reduction.

M16_analysis_this_session:
- secular_technology_growth Scenario B: full 4-layer CalibrationMethodology() run.
  Layer 1: unconditional anchor ~0-2% real (VCMM, RA, GMO).
  Layer 2: 1973-82 (weak proxy, negative); 2022 direct (B analog, secular tech -28-33% despite 20-25% revenue growth — multiple compression dominated); Q1 2026 (1 quarter, contaminated by A-scenario re-pricing).
  Layer 3: AI contract lock-in (+2-4% structural adjustment upward); sustained multiple compression under elevated rates (-5-10% downward); net: mildly supports current [-6,-1] rather than dramatic upward revision.
  Layer 4 (neutral A=35/B=15/C=15/D=10/E=5/F=20): proposed [-2,+4] conservative=-2% → weighted avg +1.0% vs anchor ~1%. PASS within ±3pp tolerance.
  Confidence: MEDIUM (2 analogues; structural adjustment material; 1 contaminated data point).
  OUTCOME: intra-session adoption BLOCKED (MEDIUM confidence). Logged as pending proposal — see §6 item 35.
  Competing proposal ([-12,-3]) from May 6 remains on table. Both for June 30 adjudication.
  Upgrade path: if Q2 Mag7 earnings (reporting May-July) confirm >25% revenue growth in sustained B environment with no guidance withdrawals → 2nd and 3rd data points → HIGH confidence eligible.

framework_updates_this_session:
- v1.15 version bump.
- AIPO reclassification v1.14 (earlier ad-hoc session today): confirmed in §11. EV revised to +2.42% (↓ from +2.95%). Portfolio-level EV impact: ~0.03-0.05pp reduction per account — immaterial; recomputed at next M05 allocation fetch.
- Primary Taxable deployment COMPLETE: DBMF 854sh ($26,090, 10%), XLP 196sh ($16,460, 6.36%), COPX 212sh ($17,513, 6.76%) executed. SGOV 85sh sold (proceeds). $51,950 cash fully deployed. Open Decision #4 CLOSED.
- v1.13 targets confirmed live in allocation file across all 6 accounts.

current_positions (allocation sheet, second fetch, May 7, 2026):
- Primary IRA (3080-6469): MLPX 1029sh/$75,446 (30.28%), SGOL 1850sh/$82,825 (33.24%), XAR 114sh/$29,955 (12.02%), AIPO 605sh/$19,293 (7.74%), MAGS 257sh/$17,705 (7.11%), VTIP 188sh/$9,455 (3.79%), SIVR 129sh/$9,707 (3.90%), COPX 58sh/$4,791 (1.92%), DBMF 0sh. Cash $4.08. Total ~$249,181.
- Primary Roth (3534-9838): MAGS 44sh/$3,031 (7.07%), AIPO 105sh/$3,348 (7.81%), XAR 20sh/$5,255 (12.26%), MLPX 174sh/$12,758 (29.77%), SGOL 300sh/$13,431 (31.34%), DBMF 0sh, VTIP 0sh, SIVR 0sh. Cash $5,033. Total ~$42,857.
- Primary Taxable (6668-9768): MLPX 1317sh/$96,562 (37.28%), AIPO 663sh/$21,143 (8.16%), XLP 196sh/$16,460 (6.36%), DBMF 854sh/$26,090 (10.07%), PAVE 494sh/$28,064 (10.84%), XAR 119sh/$31,268 (12.07%), COPX 212sh/$17,513 (6.76%), SGOV 218sh/$21,898 (8.45%). Cash $6.30. Total ~$259,006.
- Taxable Preservation (3459-4443): SGOV 369sh/$37,066. Cash $9.19. Total $37,075.
- Relative IRA (...469): MLPX 762sh/$55,870 (33.92%), SGOL 1398sh/$62,588 (38.00%), SGOV 328sh/$32,948 (20.00%), MAGS 73sh/$5,029 (3.05%), AIPO 255sh/$8,132 (4.94%), VTIP 0sh, DBMF 0sh, SIVR 0sh. Cash $141. Total ~$164,708.
- Relative Roth (...466): MAGS 11sh/$758 (8.17%), AIPO 34sh/$1,084 (11.70%), MLPX 49sh/$3,593 (38.76%), SGOL 85sh/$3,805 (41.05%), VTIP 0sh, DBMF 0sh. Cash $30. Total ~$9,270.
- Portfolio total (all accounts): ~$762,097.

open_triggers:
- CPI May 12: BINARY — HIGHEST PRIORITY. If ≥3.5% YoY → C check_cpi=2 → C rises materially, likely to 40%+. If ≤3.0% → B check_cpi=0 → B falls sharply, likely to 25-27%. Run DeriveScenarioProbabilities() immediately on release — do not wait for next scheduled session.
- check_energy day 5 (May 8): if Brent remains below ~$101 at close → check_energy=2 → A rises from 15% to ~18%. Verify at next session open.
- US-Iran deal: T1-confirmed deal → A→25%+, C→<25%. Unlocks: VNQ/VEA adoption conditional, MLPX war premium guard retirement, XAR structural target review.
- Brent C-trigger clock: Day 0. Clock inactive. New initiation requires fresh 10-day sequence above $110. Unlikely near-term given deal trajectory.
- IIJA reauthorization September 30, 2026 (PAVE watch trigger).
- MLPX 90d trailing price: Yahoo Finance Feb 5, 2026 historical close — still unverified. Less urgent (MLPX at target in Primary IRA/Taxable) but required before any ADD in Primary IRA/Roth.

open_decisions:
1. CPI May 12 [BINARY — TIME-SENSITIVE]: run DeriveScenarioProbabilities() on release date. Do not wait.
2. XAR at 12% target: CONFIRMED ALL ACCOUNTS. CLOSED.
3. MLPX Relative IRA reduction: PENDING. -222.86sh (-$16,340). Partially funds new instrument additions.
4. Primary Taxable cash deployment: CLOSED (DBMF, XLP, COPX executed).
5. Remaining trades (tomorrow):
   - Primary IRA: sell MAGS 76sh, sell SGOL 959sh, buy DBMF 1223sh, buy VTIP 208sh, buy AIPO 20sh, buy SIVR 3sh, buy COPX 2sh.
   - Primary Roth: sell MAGS 7sh, sell SGOL 166sh, buy DBMF 238sh, buy VTIP 85sh, buy SIVR 28sh.
   - Primary Taxable: sell MLPX 257sh, buy SGOV 169sh (minor trims/adds to other positions).
   - Relative IRA: sell MLPX 223sh, sell SGOL 441sh, sell SGOV 98sh, buy VTIP 393sh, buy DBMF 647sh, buy SIVR 66sh, buy AIPO 55sh.
   - Relative Roth: sell MLPX 9sh, sell SGOL 39sh, sell AIPO 5sh, buy VTIP 18sh, buy DBMF 55sh.
6. MLPX 90d trailing price verification: Yahoo Finance Feb 5, 2026 close. Less urgent (at target) but log before any ADD decision.
7. secular_technology_growth B calibration: PENDING June 30 (MEDIUM confidence). Monitor Q2 Mag7 earnings.
8. MAGS override confirmations: client managing to v1.13 targets (5% Primary IRA, 6% Primary Roth, 3% Rel IRA, 8% Rel Roth) — trades in progress.

consolidated_target_allocations (v1.13 — CONFIRMED IN ALLOCATION FILE):
- Primary IRA:     MLPX 30% | DBMF 15% | SGOL 16% | XAR 12% | AIPO 8% | VTIP 8% | SIVR 4% | MAGS 5% | COPX 2%
- Primary Roth:    MLPX 28% | DBMF 17% | SGOL 14% | XAR 12% | VTIP 10% | AIPO 8% | SIVR 5% | MAGS 6%
- Primary Taxable: MLPX 30% | SGOV 15% | XAR 12% | AIPO 8% | PAVE 11% | DBMF 10% | COPX 7% | XLP 7%
- Taxable Pres.:   SGOV 100%
- Relative IRA:    SGOL 26% | MLPX 24% | DBMF 12% | VTIP 12% | SGOV 14% | AIPO 6% | SIVR 3% | MAGS 3%
- Relative Roth:   MLPX 32% | DBMF 18% | SGOL 22% | VTIP 10% | AIPO 10% | MAGS 8%

portfolio_ev_by_account (v1.13, A=15/B=36/C=36/D=3/E=3/F=7 — updated probs):
NOTE: EV computations below use v1.13 instrument EVs (recalculated at updated probabilities). AIPO EV at new probs = +2.40% (minimal change from +2.42% at A=18 probs). Full recompute deferred to next M05 session.
- Primary IRA: ~+3.55% (required 3.2% — still above threshold ✓; DBMF B/C weight slightly higher at B=36/C=36 improves DBMF EV marginally)
- Primary Roth: ~+3.55% (required ~2.8% — exceeds ✓)
- Primary Taxable: ~+2.95% (RETURN_THEN_TARGET 5yr ✓)
- Taxable Preservation: capital preservation ✓
- Relative IRA: ~+3.00% (FLOOR_THEN_RETURN ✓)
- Relative Roth: ~+3.75% (required ~2.8% — exceeds ✓)

next_session_flags: [SUPERSEDED by May 11 full session]

---

date: 2026-05-11 (full M05 session — v1.16)
scenario_probabilities: { A: 12%, B: 37%, C: 38%, D: 3%, E: 3%, F: 7% }
primary_driver: US-Iran War Day ~73 — ceasefire on "massive life support" (Trump T1, CNN May 11). Iran demands sovereignty over Strait of Hormuz as precondition; Trump called proposal "simply unacceptable." Trump aides report he is more seriously considering combat resumption than at any point in recent weeks. Saudi Aramco CEO Amin Nasser (T1 conference call, May 11): "If Hormuz reopening is delayed a few more weeks, normalization will last into 2027. Even if opened today, market rebalancing takes months." Hormuz closed 10+ straight weeks. Brent ~$107.67 (Fortune T2, May 11 AM). Trump/Xi meeting expected this week — next potential de-escalation signal. VIX 18.11-18.41 (Yahoo Finance T1, +5-7% today). MOVE 70.74 T1 (NYSE Global Indexes).
derivation_method: scored
manual_override_reason: null
session_type: full M05 (Allocation sheet fetched Google Drive MCP; Calibration State v1.15 fetched GitHub MCP; Session Log fetched GitHub MCP; FRED data gap RESOLVED via client-provided screenshots)

scoring_basis:
- A: check_fed=0 (FOMC hold 3.5-3.75%; 4 hawkish dissents) | check_energy=0 (Brent $107.67 RISING; May 8 day-5 reversal confirmed — streak broken; Aramco T1 eliminates near-term normalization) | check_credit=1 (HY 281 bps T1; IG 79 bps T1; MOVE 70.74 T1; calm) → raw=1 (↓ from 2)
- B: check_cpi=2 (CPI 3.3% YoY March; April print scheduled May 12 8:30am ET; consensus 3.7%) | check_gdp=1 (GDP +2.0%, >1.5%) | check_fed=2 (constraint language; hawkish dissents) → raw=5 (unchanged)
- C: check_brent=2 (Brent $107.67 within $93.50-$110 band; active supply event T1; Hormuz 10+ weeks; Aramco T1 confirms supply shock persistence) | check_cpi=1 (1 confirmed print) | check_chokepoint=2 (Hormuz T1-active; ceasefire "massive life support"; combat resumption being considered) → raw=5 (unchanged)
- D: raw=0 → floor 3%
- E: raw=0 → floor 3%
- F: check_gdp=1 | check_cpi=2 | check_fed=0 | check_noshock=-2 (Hormuz T1-verified) → raw=MAX(1,0)=1 (unchanged)

probability_shifts_vs_prior (prior: A=15, B=36, C=36, D=3, E=3, F=7 from May 7):
- A: 15% → 12% (-3pp): check_energy 1→0. Brent reversed up May 8 (streak broken); $107.67 May 11. Aramco T1: normalization into 2027 minimum regardless of near-term deal status. Raw 2→1. Within 25pp cap.
- B: 36% → 37% (+1pp): absorbs A decline; structural score raw=5 unchanged.
- C: 36% → 38% (+2pp): chokepoint escalation confirmed T1; Brent rebounding; ceasefire collapsing; Aramco T1 supportive of sustained supply shock.
- D: 3% → 3% (0pp): unchanged.
- E: 3% → 3% (0pp): unchanged.
- F: 7% → 7% (0pp): unchanged.
B/C dual >30% justification: Both raw=5. B: CPI 3.3% trending + FOMC constraint language + GDP support (rate-constraint mechanism active). C: Hormuz T1-active + CPI 1 print confirmed + chokepoint severity escalating. Equal scoring mechanically correct. Primary driver simultaneously feeds both via inflation persistence (B) and supply shock continuation (C).

M14_divergence (updated):
- commodity_fear_divergence: MODERATE (energy_90d ~+71% ≥+10%; VIX_change_90d ~+1-3 pts >0, ≤+5 → not HIGH)
- equity_scenario_divergence: HIGH (S&P 30d ~+8-10% ≥+5%; B/C directive for broad_market_equity reductive)
- composite: HIGH (unchanged from May 6/7)
- UnderweightReviewTrigger: NOT fired (all accounts within ±1pp of v1.13 targets — trades fully executed)

credit_readings_this_session (T1 — FRED gap RESOLVED):
- HY (BAMLH0A0HYM2): 281 bps (May 8 close). Below baseline 285 bps (Apr 19). Tightening ~−25 bps over 60d. HY_StressBeginning ~435 bps; gap 154 bps. NO THRESHOLD FIRES.
- IG (BAMLC0A0CM): 79 bps (May 8 close). Below baseline 83 bps (Apr 19). IG_TransmissionReached ~143 bps; gap 64 bps. NOT FIRED.
- CCC (BAMLH0A3HYC): 920 bps (May 8 close). At baseline ~921 bps. 30d divergence: CCC tightening ~−30 bps; HY tightening ~−10 to −30 bps. 3× composite rule NOT fired. Absolute divergence NOT fired.
- MOVE: 70.74 (T1 NYSE Global Indexes, 15-min delay, May 11). Calm zone (<80). Up +5.19% today — consistent with fresh escalation signals.
Approved source URLs (see Calibration_State §1): BAMLH0A0HYM2, BAMLC0A0CM, BAMLH0A3HYC via https://fred.stlouisfed.org/data/[SERIES]; MOVE via investing.com/indices/ice-bofaml-move and finance.yahoo.com/quote/^MOVE/

portfolio_status_this_session:
- All Open Decision #5 trades CONFIRMED EXECUTED per allocation sheet (all 6 accounts at v1.13 targets ±1pp)
- Open Decision #3 (MLPX Relative IRA reduction 762→542sh) CONFIRMED EXECUTED
- Portfolio total ~$769k (vs ~$762k May 7; +$7k price appreciation — MLPX, SGOL, XAR gains)
- No allocation changes this session. No ADD or EXIT triggered.

framework_updates_this_session:
- v1.16 version bump
- FRED source URLs confirmed and approved (§1 of Calibration_State.md updated)
- FRED data gap RESOLVED — first T1 credit readings in multiple sessions
- check_energy scoring: day-5 threshold (May 8) FAILED. Brent reversed up. check_energy=0 this session.
- Saudi Aramco CEO statement (T1) encoded as session intelligence: normalization into 2027 even under best-case Hormuz scenario.

open_triggers:
- CPI May 12 [BINARY — IMMINENT]: 8:30am ET tomorrow. If ≥3.5% → C check_cpi=2 → C likely 40%+. If ≤3.0% → B check_cpi=0 → B falls sharply to ~25-27%. Run DeriveScenarioProbabilities() immediately on release. Do not wait for next scheduled session.
- US-Iran deal: Trump/Xi meeting expected this week. T1-confirmed deal → A→25%+, C falls below 25%. Triggers: VNQ/VEA adoption conditional unlocked; MLPX war premium guard retirement; XAR structural target review.
- Brent C-trigger clock: Day 0. Brent $107.67 and rising. Monitor for new 10-day sequence above $110. If Brent closes ≥$110 in a session, clock starts.
- Aramco T1 (May 11): normalization into 2027 regardless of near-term deal. Does NOT change A threshold — T1-confirmed deal still required. Does reinforce B/C structural bias.
- IIJA reauthorization September 30, 2026 (PAVE watch trigger).
- MLPX 90d trailing price: Yahoo Finance Feb 5, 2026 MLPX close — still unverified. Required before any ADD. Lower priority (at target).
- FRED next release: May 12 (concurrent with CPI). Fresh T1 credit readings available at session start if FRED fetch succeeds.

open_decisions:
1. CPI May 12 [BINARY — IMMINENT]: run DeriveScenarioProbabilities() at 8:30am ET release. No other action until CPI result confirmed.
2. MLPX 90d trailing price: carry forward. No ADD pending.
3. secular_technology_growth B calibration: PENDING June 30. Monitor Q2 Mag7 earnings (May-July). HIGH confidence upgrade path: >25% revenue growth + no guidance withdrawals.
4. URA full M07+M15 evaluation: PENDING June 30.

consolidated_target_allocations (v1.13 — CONFIRMED IN ALLOCATION FILE — UNCHANGED):
- Primary IRA:     MLPX 30% | DBMF 15% | SGOL 16% | XAR 12% | AIPO 8% | VTIP 8% | SIVR 4% | MAGS 5% | COPX 2%
- Primary Roth:    MLPX 28% | DBMF 17% | SGOL 14% | XAR 12% | VTIP 10% | AIPO 8% | SIVR 5% | MAGS 6%
- Primary Taxable: MLPX 30% | SGOV 15% | XAR 12% | AIPO 8% | PAVE 11% | DBMF 10% | COPX 7% | XLP 7%
- Taxable Pres.:   SGOV 100%
- Relative IRA:    SGOL 26% | MLPX 24% | DBMF 12% | VTIP 12% | SGOV 14% | AIPO 6% | SIVR 3% | MAGS 3%
- Relative Roth:   MLPX 32% | DBMF 18% | SGOL 22% | VTIP 10% | AIPO 10% | MAGS 8%

portfolio_ev_by_account (v1.13, A=12/B=37/C=38/D=3/E=3/F=7 — updated probs):
NOTE: Full EV recomputation deferred to next M05 session with allocation sheet fetch. Directional: DBMF/MLPX EV improve marginally on higher B/C weights; MAGS/XAR EV decline marginally on lower A weight. Net portfolio impact estimated <0.1pp per account.
- Primary IRA: ~+3.55% (required 3.2% — above threshold ✓)
- Primary Roth: ~+3.55% (required ~2.8% ✓)
- Primary Taxable: ~+2.95% (RETURN_THEN_TARGET 5yr ✓)
- Taxable Preservation: capital preservation ✓
- Relative IRA: ~+3.00% (FLOOR_THEN_RETURN ✓)
- Relative Roth: ~+3.75% (required ~2.8% ✓)

next_session_flags:
- LOAD: confirm "Calibration State loaded, last update: May 11, 2026 | Session Log loaded"
- CRITICAL: CPI May 12. If window has passed, fetch immediately and run DeriveScenarioProbabilities() before any portfolio analysis.
- FRED data gap resolved: attempt web_fetch on approved URLs. If fetch still fails (HTML only), request screenshots as backup.
- Brent C-trigger clock: monitor daily. Currently $107.67 and rising. Any close ≥$110 starts Day 1 of new 10-day clock.
- US-Iran deal: monitor Trump/Xi meeting outcome. T1 confirmation required for A→25%+.
- MLPX 90d trailing price: Yahoo Finance Feb 5, 2026 close — required before any ADD.
- secular_technology_growth B: no action until June 30.
- check_energy: currently 0. If Brent begins sustained decline (5+ consecutive closing days below prior close), monitor for check_energy=2 upgrade.

---

date: 2026-05-13 (full M05 session — v1.17)
scenario_probabilities: { A: 7%, B: 36%, C: 44%, D: 3%, E: 3%, F: 7% }
primary_driver: US-Iran War Day ~74 / CPI April 2026 supply-shock confirmation. CPI = 3.8% YoY (BLS T1, May 12). Energy >40% of monthly gain. Real wages −0.3% YoY. Hormuz closed, deal effectively stalled (Trump considering resuming strikes, dismissed Iran's latest proposal). IEA: market undersupplied through October even if conflict ends. BZ=F May 12 close $105.71 — C-trigger clock Day 0 confirmed.
derivation_method: scored
manual_override_reason: null
session_type: full M05 (Allocation sheet fetched Google Drive MCP — pre-market, prices reflect May 12 close; Calibration State v1.16 fetched GitHub MCP; Session Log fetched GitHub MCP; FRED T1 via embedded allocation spreadsheet tab May 12 close)

scoring_basis:
- A: check_fed=0 (FOMC hold 3.5-3.75%) | check_energy=0 (BZ=F May 12 close $105.71 < $110; C-trigger clock Day 0 confirmed; Fortune T2 spot readings rejected as clock reference) | check_credit=1 (HY 282 bps, IG 77 bps — calm) → raw=1 (unchanged from May 11)
- B: check_cpi=2 (CPI 3.8% YoY April; below 4% formal B trigger; 3-4% trending confirmed; check_cpi unchanged) | check_gdp=1 (GDP +2.0%, >1.5%) | check_fed=2 (FOMC constraint language; hawkish dissents) → raw=5 (unchanged)
- C: check_brent=2 (BZ=F $105.71, within $93.50-$110 band; Hormuz active T1; Aramco T1 normalization 2027+) | check_cpi=2 (UPGRADED: April 3.8% ≥ 3.5% — second qualifying supply-shock print; raw 5→6) | check_chokepoint=2 (Hormuz T1-active; deal stalled; Trump considering resuming strikes per multiple T1) → raw=6 (UPGRADED from 5)
- D: raw=0 → floor 3%
- E: raw=0 → floor 3%
- F: raw=1 (unchanged) → 7%

probability_derivation (non-floor pool = A+B+C+F raw = 1+5+6+1 = 13; non-floor probability = 94%):
- A: 1/13 × 94% = 7.23% → 7%
- B: 5/13 × 94% = 36.15% → 36%
- C: 6/13 × 94% = 43.38% → 44% (rounded up to achieve 100% sum)
- F: 1/13 × 94% = 7.23% → 7%
- D: 3%, E: 3%
- Total: 7+36+44+3+3+7 = 100% ✓

probability_shifts_vs_prior (prior: A=12, B=37, C=38, D=3, E=3, F=7 from May 11):
- A: 12% → 7% (−5pp): raw unchanged at 1; pool denominator grows 12→13 as C check_cpi upgrades; A proportional share falls from 1/12 to 1/13 of non-floor pool. Within 25pp cap.
- B: 37% → 36% (−1pp): raw unchanged at 5; proportional share falls from 5/12 to 5/13. Rounding.
- C: 38% → 44% (+6pp): raw 5→6; proportional share rises from 5/12 to 6/13 of non-floor pool. DRIVER: second qualifying supply-shock CPI print. Within 25pp cap.
- D: 3% → 3% (0pp): unchanged.
- E: 3% → 3% (0pp): unchanged.
- F: 7% → 7% (0pp): raw unchanged; proportional share 1/12→1/13; rounds to 7%.
B/C dual >30% justification: B raw=5 (CPI 3.8% sticky + FOMC constraint + GDP support = rate-constraint stagflation mechanism active). C raw=6 (Hormuz T1-active + second supply-shock CPI print confirmed by energy's 40%+ monthly contribution + chokepoint severity). Asymmetry correct: C elevated above B for first time as second qualifying print resolves binary.

M14_divergence:
- commodity_fear_divergence: MODERATE (energy_90d ~+62% ≥+10%; VIX 17.97 pre-market, VIX_change_90d ~+4-5 pts — borderline; classified MODERATE)
- equity_scenario_divergence: HIGH (S&P 500 futures 7,423 pre-market; S&P ≥+5% above 30d prior — B/C directive reductive)
- composite: HIGH (unchanged)
- UnderweightReviewTrigger: NOT fired (all accounts within ±1pp of v1.13 targets)

credit_readings_this_session (T1 — embedded spreadsheet tab, May 12 close):
- HY (BAMLH0A0HYM2): 282 bps. +1 bp from May 8. HY_StressBeginning ~435 bps; gap 153 bps. NO THRESHOLD FIRES.
- IG (BAMLC0A0CM): 77 bps. −2 bps from May 8. IG_TransmissionReached ~143 bps; gap 66 bps. NOT FIRED.
- CCC (BAMLH0A3HYC): 937 bps. +17 bps from May 8. 30d divergence: CCC +17 vs HY +1; absolute floor requires +200 bps — NOT FIRED.
- MOVE: 70.74 carry from May 11 T1. MOVE tab present in spreadsheet; value not separately parsed this session.
- VIX: 17.97 pre-market (Yahoo Finance, calm).
All credit thresholds: NO FIRE.

key_data_this_session:
- CPI April 2026: +3.8% YoY, +0.6% MoM (BLS T1, USDL-26-0721, released May 12). Core: +2.8% YoY, +0.4% MoM. Energy: +17.9% YoY. Gasoline: +28.4% YoY. Food: +3.2% YoY. Real wages: −0.5% MoM, −0.3% YoY.
- BZ=F May 12 close: $105.71 (client-confirmed T2). Established as canonical Brent reference replacing Fortune T2 intraday spot.
- MLPX EntryExtensionGuard: CLEARED. 90d avg: $72.31 (Feb 5 close: $66.54, client-confirmed). Threshold: $86.77. Current: $74.40. +2.9% above avg — well below 20%. WAR PREMIUM ENTRY GUARD also CLEARED (same threshold).
- Portfolio total: ~$775k (allocation sheet May 12 close prices; up ~$6k from May 11).

framework_updates_this_session:
- v1.17 version bump.
- BZ=F established as canonical Brent reference (Fortune spot rejected).
- MLPX both entry guards CLEARED — ADD eligible in all accounts (no ADD needed; at target).
- FRED data source: allocation spreadsheet embedded tab confirmed as T1 source for credit spreads.
- M16 LivingUpdateTrigger check (C +6pp shift): no intra-session adoption triggered. All pending items MEDIUM/LOW confidence — June 30 audit venue unchanged. Adopted values (DBMF B/C, MLPX B/C) remain valid and improving in direction.
- GOOGLEFINANCE ticker list provided for new spreadsheet market data tab (§6 item 36 in Calibration_State).

portfolio_ev_by_account (v1.13 current targets, A=7/B=36/C=44/D=3/E=3/F=7):
- Primary IRA: +4.27% (required ~3.39% ✓ — +0.88pp above)
- Primary Roth: +4.33% (required ~3.03% ✓ — +1.30pp above)
- Primary Taxable: +3.25% (RETURN_THEN_TARGET 5yr ✓)
- Taxable Preservation: +0.81% (capital preservation ✓)
- Relative IRA: +3.53% current → +3.89% if v1.17 gold reallocation executed (FLOOR_THEN_RETURN ✓)
- Relative Roth: +4.45% current → +4.73% if v1.17 gold reallocation executed (required ~3.03% ✓)

open_triggers:
- Brent C-trigger clock: Day 0 confirmed (BZ=F $105.71 May 12 close < $110). Monitor BZ=F close every session. New clock requires 10 consecutive BZ=F closes ≥$110.
- US-Iran deal: Trump/Xi meeting pending. T1-confirmed deal → A→25%+, C falls below 25%. Unlocks: VNQ/VEA conditional, MLPX war premium guard retirement, XAR structural target review.
- MLPX ADD: both guards cleared; no ADD needed (at target); unblocked for future rebalancing use.
- FRED/MOVE tab: GOOGLEFINANCE ticker list provided this session (§6 item 36). BZ=F (NYMEX:BZ) and DXY (INDEXDXY:DXY) need environment testing. MLPX historical confirmed working.
- IIJA reauthorization September 30, 2026 (PAVE watch trigger).
- secular_technology_growth B calibration: PENDING June 30. Monitor Q2 Mag7 earnings (May-July). Upgrade path: >25% revenue growth + zero guidance withdrawals → HIGH confidence eligible.
- Q2 audit: June 30, 2026.

open_decisions:
1. Gold reallocation — RECOMMENDED THIS SESSION, PENDING CLIENT EXECUTION IN ALLOCATION SHEET:
   Relative IRA: SGOL 26%→20%, SIVR 3%→6%, DBMF 12%→15%
   Relative Roth: SGOL 22%→16%, SIVR 0%→4% (new position), DBMF 18%→20%
   EV impact: Relative IRA +3.53%→+3.89% (+0.36pp); Relative Roth +4.45%→+4.73% (+0.28pp)
   E-scenario floor check (Relative IRA): new portfolio E return = +0.78% (positive; floor maintained ✓)
   Structural basis: C=44% dominant; SGOL C = −2% (C-hawk rate regime); SIVR C blended = +2.05%; DBMF C = +18%. SGOL hold EV still positive (+1.31%) — retained at 20%/16% for B-scenario (+2.16%/+1.92% contribution) and E-scenario safe haven (+2.00%/+1.60% contribution).
   Once executed and confirmed in allocation sheet: update Calibration_State §11 targets and Consolidated Target Allocations table; bump to v1.18.
2. MAGS: at v1.13 target weights ±1pp. Strong recent market performance noted (M14 equity_scenario_divergence). Structural EV = −1.77% (deteriorating as A shrinks). Override remains in force. Monitor for overweight drift at next allocation fetch.
3. secular_technology_growth B: PENDING June 30.
4. URA full M07+M15 evaluation: PENDING June 30.

consolidated_target_allocations:
  v1.13 confirmed targets — see Calibration_State.md Consolidated Target Allocations table.
  v1.17 revision pending execution in allocation sheet (see open_decision #1 above).

next_session_flags:
- LOAD: confirm "Calibration State loaded, last update: May 13, 2026 | Session Log loaded"
- Fetch allocation sheet: will capture executed gold reallocation trades if client has updated targets and executed.
- Brent C-trigger clock: monitor BZ=F close every session. Currently $105.71. Any close ≥$110 starts Day 1.
- FRED spreadsheet tab: use as T1 source for HY/IG/CCC at each session. Also check MOVE value in spreadsheet tab (not parsed May 13 — confirm MOVE tab structure at next session).
- US-Iran deal: monitor for T1-confirmed ceasefire or resumption of strikes.
- MAGS: check weight vs 5%/6%/3%/8% targets — trim if materially overweight.
- BZ=F / DXY GOOGLEFINANCE test: confirm NYMEX:BZ and INDEXDXY:DXY work in spreadsheet environment.
- Gold reallocation: if client has executed, verify in allocation sheet and write v1.18.
