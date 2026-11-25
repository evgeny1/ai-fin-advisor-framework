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

### §8 Canonical Schema (ENG-52, 2026-07-06 — supersedes the June 7, 2026 prose schema)

Each entry below is now a **real YAML document** (parsed via PyYAML, not
regex — see `python/advisor/config/session_log.py`), delimited by the same
`---` separator convention as before. This replaced the old loosely-
structured key:value prose after a client-identified gap: two same-day
2026-07-03 entries were indistinguishable without reading the full
`primary_driver` paragraph — no unique id, no way to tell which one was
authoritative. `entry_id` and `status` exist specifically to fix that.

```yaml
entry_id: YYYY-MM-DDTHH:MM        # real wall-clock write-back time (local), not fabricated
date: YYYY-MM-DD
session_type: full M05 session | ad-hoc | audit | READONLY_MOBILE
status: current | superseded     # flips to superseded automatically when a
                                  # later same-day entry is written (see
                                  # rendering.mark_prior_entries_superseded())
scenario_probabilities: { A: X, B: X, C: X, D: X, E: X, F: X }   # plain numbers, no '%' — VERIFY sum == 100
primary_driver: current dominant driver, one paragraph
open_triggers:
  - item
open_decisions:
  - item                          # numbering was cosmetic in the old prose format;
                                   # order is preserved by the YAML sequence either way
next_session_flags:
  - item

# Optional (include when relevant):
calibration_changes_this_session:
  - item with version bump
```

`entry_id` is generated automatically by `rendering.build_session_log_entry()`
at write-back time — sessions never need to supply it by hand. Entries
migrated from the pre-YAML format use the real git commit timestamp that
introduced them, not a fabricated one.

§7's pipe-table format is unchanged — it was already clean and mechanically
parseable; only §8 had a disambiguation problem worth fixing.

---

## Section 7 - Session Observations Log (Credit Readings)

// COMPACTED: 2026-09-24 — 10 row(s) older than 90 calendar days archived to Archive_2026Q2.md (FRAMEWORK_BACKLOG.md ENG-53)

| Date | HY OAS (bps) | IG OAS (bps) | CCC OAS (bps) | Source | T1 Flag |
| --- | --- | --- | --- | --- | --- |


## Section 8 - Session State Log

// COMPACTED: 2026-04-30 | A=7%/B=42%/C=42%/D=3%/E=3%/F=3% | Hormuz Day 61; SUPERSEDED by May 13 full session

// COMPACTED: 2026-06-19 — entries 2026-05-25 through 2026-06-07 (7 entries) archived to Archive_2026Q2.md, restoring the last-3 retention rule (FRAMEWORK_BACKLOG.md ENG-5); retained: 2026-06-10, 2026-06-14 (x2)

// COMPACTED: 2026-06-21 — advisor_write_back was called twice for this single session (the first MCP tool call completed and committed server-side but timed out client-side before returning a response, per ENG-33's investigation; a second in-process call was made to actually complete the write-back, not realizing the first had already succeeded). Each call's retention pass archived its own oldest entry (June-10, then June-14's first of two same-day entries) to Archive_2026Q2.md, and each appended a near-duplicate "2026-06-21 (full M05 session)" entry. The duplicate (first, less complete) June-21 entry has been removed below, retaining only the second. The extra-archived June-14 entry was not restored — it remains safely in Archive_2026Q2.md if needed; flagged to Evgeny rather than manually reconstructed here to avoid transcription risk.

// COMPACTED: 2026-07-03 — 1 oldest entry(ies) archived to Archive_2026Q3.md, restoring the last-3 retention rule (FRAMEWORK_BACKLOG.md ENG-5)

// COMPACTED: 2026-07-03 — 1 oldest entry(ies) archived to Archive_2026Q3.md, restoring the last-3 retention rule (FRAMEWORK_BACKLOG.md ENG-5)

// COMPACTED: 2026-07-03 — 1 oldest entry(ies) archived to Archive_2026Q3.md, restoring the last-3 retention rule (FRAMEWORK_BACKLOG.md ENG-5)

// COMPACTED: 2026-10-12 — 5 entry(ies) older than 90 calendar days archived to Archive_2026Q3.md (FRAMEWORK_BACKLOG.md ENG-53)

// COMPACTED: 2026-11-25 — 8 entry(ies) older than 90 calendar days archived to Archive_2026Q3.md (FRAMEWORK_BACKLOG.md ENG-53)
---
entry_id: 2026-09-24T09:33
date: '2026-09-24'
session_type: full M05 session + Q3 audit (early, v1.71)
status: current
scenario_probabilities: {A: 5.5294, B: 33.1765, C: 27.6471, D: 3.0, E: 3.0, F: 27.6471}
primary_driver: 'Fed HIKED 25bp on Sept 16 (12-0, to 3.75-4.00%; dots: 16 of 18 expect
  another 2026 hike; next FOMC Oct 27-28) -> A_check_fed 0, F_check_fed 2. Aug CPI
  3.4% YoY flat (MoM +0.4% on gasoline, core 2.4% YoY); Q2 real GDP 1.5% but nominal
  strong (F_check_gdp 3, Q2 final sales to private domestic purchasers +4.2%); Aug
  payrolls +162k, unemployment 4.1%; Hormuz chokepoint still T1-active (Iran-Gulf
  talks postponed indefinitely Sept 13, US blockade/escorts), Brent 99.63 (9.4% below
  the 110 C-trigger). Scoring: A 10.4->5.5, B 41.8->33.2, C 31.3->27.6, F 10.4->27.6,
  D/E 3.0. Same session: Q3 audit v1.71 adopted 7 MEDIUM 4.1 cells (BMEI A/B/C, STG
  D/E/F, RAC A); at the new vector VYMI blended EV -5.02% (REDUCE), SCHD -0.07% (REDUCE_TO_MIN),
  Primary IRA feasibility shortfall widened to 3.54pp (portfolio 0.80% vs required
  4.34%).'
open_triggers:
- FOMC hiked to 3.75-4.00% on Sept 16 (12-0); 16 of 18 dots expect another 2026 hike,
  markets price December; next FOMC Oct 27-28
- 'Data calendar: JOLTS Sept 29, BEA 2026 annual update Sept 30, Sept jobs report
  Oct 2, Sept CPI Oct 14 (Aug CPI was 3.4% YoY, core 2.4%)'
- 'Iran/Hormuz chokepoint T1-active: Iran-Gulf talks on the Omani reopening plan postponed
  indefinitely Sept 13, US naval blockade and tanker escorts continue; Brent 99.63,
  9.4% below the 110 C-trigger; C_check_chokepoint stays 2'
- 'Long end: 10Y 4.96%, 30Y 5.29% (M17 E warning 5.50%), term premium 0.96 (warning
  1.00), MOVE 95.45 (+21.5% on the day), e_pathway_type RESERVE_EROSION'
- CCC OAS 1,075bps still sharply diverging from HY 268 / IG 77 - unresolved tail-widening-first
  pattern; FINRA margin debt 1.454T (record 1.502T in June)
- 'Trend signals 2026-09-24 (shadow mode, never a directive): MLPX WEAKENING (-41.16pp
  medium), XAR WEAKENING (-4.79pp), AIPO INCONCLUSIVE (-12.01pp medium), SGOL INCONCLUSIVE'
- 'Q3 audit v1.71 is PARTIAL: threshold audits (2, 9, 10, MOVE, Fed-response sub-variable),
  BMEI D/E, GP E, and L1 anchors for XLV/FLOT/EM/RE still open - Calibration_State
  6 item 49'
- 'Anthropic IPO: Nasdaq venue reported Sept 13, October listing possible, no public
  terms (item 16 re-check only if a position in the space is considered)'
open_decisions:
- 'Client decision needed: M16 amendment for an anchor-substitution path for narrow-sector
  roles; until then geopolitical_premium A [-4,+1] stays blocked at [-2,3] (Calibration_State
  6 item 51; ~0.19pp XAR EV at A ~10%, less at the new A 5.5%)'
- VYMI (EV -5.02%, REDUCE) and SCHD (EV -0.07%, REDUCE_TO_MIN) now carry framework
  REDUCE directives after v1.71; they are ~11.4% and ~22.4% of the total portfolio.
  M06 HoldJustification with EV math is required before any hold recommendation; sheet
  targets are not changed by this session
- Acc4 (6668-9768) sheet targets (AIPO 14 / SCHD 24 / VYMI 12 / XAR 10 / RSP 5 / MLPX
  20 / SGOV 15) differ from the adopted 2026-07-31 design (MLPX25/SCHD35/VYMI15/XAR10/SGOV15,
  AIPO/RSP dropped) - reconcile
- Primary IRA feasibility shortfall widened to 3.54pp (0.80% vs 4.34% required; was
  2.46pp on Aug 15) - most of the drop is the v1.71 adoptions plus F rising to 27.6%;
  separately, unadopted XLV B/C [-9,-2] are live in SCHD/VYMI EV (about -0.84pp on
  SCHD) - adopt or revert once an L1 anchor is sourced (Calibration_State 6 item 50)
- Primary Roth AIPO is 22.88% vs a 0% target (sell-down pending); Primary IRA AIPO
  13.4% and Acc4 AIPO 13.4% still unreviewed against the AI-bubble thesis
- SCHD, VYMI, RSP are held but registered under 11.4 candidates, so they miss ValidateClassifications/holdings
  fetch/trend-signal set (ENG-75); move to 11.3 in a coding session
- 'Relative IRA/Roth: floor check CLEAR at the new vector; SCHD/VYMI rotation there
  not executed and not decided'
next_session_flags:
- 'Data before the next session: JOLTS Sept 29, Sept jobs Oct 2, Sept CPI Oct 14,
  FOMC Oct 27-28'
- Finish the Q3 audit remainder (Calibration_State 6 item 49) and the L1 anchors for
  XLV/FLOT/EM/RE (item 50)
- 'Coding session: ENG-74 (7 stale tests: 2026-06-01 seed aged out of 90-day compaction;
  DBMF hardcoded after exit) and ENG-75 (SCHD/VYMI/RSP registry)'
- advisor_evaluate_trend_signal MCP call hit the 60s timeout again but had completed
  and written TrendSignalStore.json locally (uncommitted) - committed manually as
  8e7f32c; recurring pattern, worth a note against ENG-64
- VTIP range_position_advisory fired this session (B, unfavorable, real yield up)
  - the Aug 15 miss was not investigated; consider closing that flag

---
entry_id: 2026-10-12T19:35
date: '2026-10-12'
session_type: full M05 session
status: current
scenario_probabilities: {A: 5.8824, B: 29.4118, C: 23.5294, D: 5.8824, E: 5.8824,
  F: 29.4118}
primary_driver: 'Hormuz re-escalation into a physical oil squeeze (record tanker-attack
  week ending Oct 5; Hormuz crude ~8.5 mb/d, ~40% below normal; attacks spreading
  to Qatar/Fujairah; Iran reviewing US counteroffer; Trump: no strike before Nov 3,
  blockade stays) while US hiring stalls (Sept payrolls +29k, unemployment 4.2%) and
  the Fed holds a hawkish pause (Oct hike ~17%, Dec ~84%). BEA annual update lifted
  Q2 real GDP to 2.2% (Q1 2.5%); GDPNow Q3 3.7%. Brent futures 105.92 vs Dated spot
  125.44 (EIA Sept spot avg $114). Scoring (rerun, 59/66 specs valid after Yahoo recovered):
  A 5.5->5.9, B 33.2->29.4, C 27.6->23.5, D 3.0->5.9, E 3.0->5.9, F 27.6->29.4. C_check_brent=1
  on BZ=F with the full MAX($110, 90d avg 94.90 x 1.4 = $132.86) rule (20.3% below);
  spot basis would give 2. D understated ~5pp: CCC ratio divergence fires by hand
  (CCC +196bp vs HY +48bp over 30d, 4.1x) but D_check_credit auto-scored 0 because
  180d medians unavailable; corrected D ~11%. Long end crossed both M17 E warnings
  (30Y 5.60 > 5.50; term premium 1.085 > 1.00). No directive changes vs 9/24; hold
  through Oct 14 CPI.'
open_triggers:
- Sept CPI Oct 14 (Aug 3.4% YoY flat, core 2.4%; Cleveland Fed nowcast 3.60% headline
  / 2.39% core - would be first YoY reacceleration)
- FOMC Oct 27-28 (hiked to 3.75-4.00% Sept 16; Oct hike ~17%, Dec ~84% per CME); Q3
  GDP advance + Sept PCE Oct 29 (GDPNow 3.7%); Oct jobs Nov 6; midterms Nov 3
- 'Iran/Hormuz T1-active and escalating: record tanker-attack week (to Oct 5), attacks
  beyond the strait (Qatar, Fujairah), flows ~40% below normal; Iran reviewing US
  counteroffer, answer expected within days; Trump: no strike before Nov 3, blockade
  stays. XAR_CONFLICT_GATE 0'
- 'Brent: futures 105.92 vs C trigger $132.86 (MAX($110, 90d avg 94.90 x 1.4)), 20.3%
  below -> C_check_brent 1; Dated spot 125.44 vs spot trigger $140.28 (10.6% below).
  Spot-futures gap ~$20'
- 'Long end: 10Y 5.22, 30Y 5.60 (M17 E warning 5.50 CROSSED), term premium 1.085 (warning
  1.00 CROSSED), MOVE 98.5, real 10Y 2.87 (2.40 eight weeks ago); e_pathway RESERVE_EROSION,
  e_watch FISCAL_STRESS_BUILDING'
- 'Credit: CCC 1,252bp RATIO DIVERGENCE FIRES by hand (30d CCC +196bp vs HY +48bp
  = 4.1x; absolute +200 floor missed by 4bp); HY 315 (trigger ~425), IG 82 (trigger
  ~138); FINRA margin debt 1.454T Aug (+37% YoY, record 1.502T June)'
- 'Trend signals 2026-10-12 (shadow mode, never a directive): XAR WEAKENING (-2.22pp
  short / -2.67pp medium vs ITA/PPA); AIPO INCONCLUSIVE; SGOL INCONCLUSIVE; MLPX labeled
  INCONCLUSIVE but HY_OAS confirmation gate missing (should be DATA_UNAVAILABLE per
  ENG-60), raw medium spread -29.54pp vs Brent. 9/24 forward outcomes due ~Oct 23'
- Hyperscaler Q3 earnings late Oct (AIPO capex gate; scored 1 on latest available
  guidance); China NBS PMI 50.1 Sept (COPX gate 2); CB gold 39t Aug, PBoC 22nd month
  (SGOL gate 1); DXY 102.58 (+2.9% over 8 weeks)
- 'Q3 audit v1.71 PARTIAL: threshold audits (2, 9, 10, MOVE, Fed-response sub-variable),
  BMEI D/E, GP E, L1 anchors XLV/FLOT/EM/RE still open - Calibration_State 6 items
  49/50'
open_decisions:
- 'Client decision needed: Brent basis for C_check_brent - futures (BZ=F, M18 primary)
  vs Dated spot (EIA/FRED DCOILBRENTEU); the two diverged ~$20 this session and give
  different scores (1 vs 2). Also the tool''s C evidence uses only nominal $110 and
  ignores the 1.40x 90d rule'
- 'Client decision needed: M16 amendment for an anchor-substitution path for narrow-sector
  roles; until then geopolitical_premium A [-4,+1] stays blocked at [-2,3] (Calibration_State
  6 item 51)'
- VYMI (EV -4.55%, REDUCE) and SCHD (EV -0.31%, REDUCE_TO_MIN) carry framework reduce
  directives (both with DualRoleConflict); M06 HoldJustification with EV math required
  before any hold recommendation
- 'Primary Roth: AIPO 23.4% vs 0% sheet target, but framework rates AIPO HOLD at +2.88%
  EV; at sheet targets the account returns 0.10% vs 4.58% required (4.48pp shortfall)
  - reconcile the sell-down with the AI-bubble thesis vs EV'
- Primary IRA feasibility shortfall 3.91pp (0.51% vs 4.42% required; was 3.54pp on
  9/24); unadopted XLV B/C [-9,-2] still live in SCHD/VYMI EV - adopt or revert once
  L1 anchor sourced (Calibration_State 6 item 50)
- 'Taxable 6668-9768: sheet targets now AIPO13/SCHD25/VYMI12/XAR9/VTI10/MLPX20/SGOV11
  (RSP gone, VTI added) - still differ from the adopted 2026-07-31 design; VTI REDUCE_TO_MIN
  (EV +0.29%); account feasible at 0.77%'
- 'Relative IRA/Roth: floors intact (0.96% / 0.63%); PassiveMandateAbsent warnings
  on MLPX (Relative IRA 20.3%, Relative Roth 34.1%) and VTIP (Relative Roth) - far
  from floor; SCHD/VYMI rotation there not decided'
- SCHD, VYMI, RSP held but registered under 11.4 candidates (ENG-75) - no holdings
  30d returns or trend signal for SCHD/VYMI
next_session_flags:
- 'Coding session backlog: (1) advisor_run_computation reports ''180d median history
  unavailable'' for HY/IG/CCC even with Yahoo healthy, while market_data_mcp fred_get_history
  returns 131 obs - check fred_fetcher history path, CreditHistoryStore.json load,
  and Session_Log 7 history; add FRED-direct fallback. (2) When the credit signal
  is incomplete, credit-dependent auto-scores (D_check_credit, A_check_credit, E_check_ig)
  must return null instead of 0/1 - apply_scoring correctly ignores overrides of auto-scored
  items, so a false ''calm'' auto-score cannot be corrected in session'
- 'Coding session backlog: (3) C_check_brent evidence uses nominal $110 only, ignoring
  MAX($110, 90d avg x 1.40); (4) MLPX trend read labeled INCONCLUSIVE with HY_OAS
  confirmation gate missing - ENG-60 says DATA_UNAVAILABLE; (5) CreditHistoryStore.json
  ENG-43 auto-commit did not complete (staged only) - committed manually as 878dea3'
- advisor_evaluate_trend_signal hit the 60s timeout twice today but completed in the
  background both times (ENG-64 pattern); TrendSignalStore committed manually as 97e5e66.
  advisor_run_computation also timed out once at 180s (succeeded on retry)
- Yahoo/yfinance outage this morning ('currentTradingPeriod' error on all symbols,
  both servers) - recovered by afternoon; if it recurs, consider pinning/upgrading
  yfinance
- 'Python path: C:\Users\evgen\miniforge3\python.exe no longer exists; C:\Python\python.exe
  is on PATH (user folder Evgeny) - verify which interpreter the MCP servers use'
- 'Data before next session: Sept CPI Oct 14, FOMC Oct 27-28, Q3 GDP + PCE Oct 29,
  hyperscaler Q3 earnings, Iran reply to US counteroffer; check 9/24 trend forward
  outcomes (~Oct 23)'
- §8 gap before this session was 18 days (25pp cap not applicable) - keep sessions
  within 7 days during the Hormuz escalation

---
entry_id: 2026-11-25T13:18
date: '2026-11-25'
session_type: full M05 session
status: current
scenario_probabilities: {A: 12.9333, B: 32.3333, C: 25.8667, D: 3.0, E: 6.4667, F: 19.4}
primary_driver: 'AI-equity unwind (S&P 500 -3.70% to 6,910 on Nov 20, technical correction
  after 7 down days; Nasdaq -5.28%, negative YTD; Nvidia leadership scandal after
  Huang resignation) colliding with a Fed set to hike again (held 3.75-4.00% Oct 28
  on 10-2 with Cook/Hammack for a hike; Oct minutes: majority sees more hikes needed;
  Dec 8-9 hike >90% priced). Oil shock fading: Brent 89.87 vs 117.64 early Oct (IEA:
  Gulf exports recovering, Q4 surplus) though Hormuz traffic still ~65% below pre-conflict
  with continuing attacks. Data: Oct CPI +0.4% m/m (Sept +0.6%), core +0.3% 3rd month,
  Oct YoY unpublished (2025 shutdown base); Q3 GDP 3.4% real / 5.6% nominal; Oct payrolls
  +165k, UR 4.1%, U-6 7.9%. Scoring (59/66 specs valid): A 5.9->12.9, B 29.4->32.3,
  C 23.5->25.9, D 5.9->3.0, E 5.9->6.5, F 29.4->19.4. B dominant but 30-39% band =
  half-size, high-urgency-only execution. No directive changes. NOTE: write-back executed
  Nov 25 for the Nov 20 session (server cache had been lost; restored by re-running
  computation and re-applying the identical Nov 20 answers, which reproduced the identical
  vector); all research, prices and account values are Nov 20.'
open_triggers:
- Q3 GDP second estimate Nov 25 (advance 3.4% real, 5.6% nominal); Nov jobs Dec 4
  (Oct +165k, UR 4.1%, U-6 7.9%); FOMC Dec 8-9 (25bp hike >90% priced, 50bp ~9%);
  Nov CPI Dec 10 (Oct +0.4% m/m, core +0.3%; Oct YoY unpublished)
- 'Iran/Hormuz T1-active: talks via Qatar/Vance continue with no breakthrough; Iran
  drone attack on US radar in Bahrain Nov 18; vessel traffic ~65% below pre-conflict
  but oil flows recovering under US escort; Iran exports near zero under US blockade.
  XAR_CONFLICT_GATE 0'
- Brent BZ=F 89.87 vs C trigger $142.37 (MAX($110, 90d avg 101.69 x 1.4)), 36.9% below
  -> C_check_brent 1. Dated Brent below nearby futures since ~Nov 9, so both bases
  now score 1
- 'Credit widening but no trigger (Nov 20): HY 352 (trigger ~425), IG 94 (trigger
  ~138), CCC 1,361. 30d CCC +34bp vs HY +19bp (1.8x) - no ratio divergence; D_check_credit
  auto 0 confirmed by hand. Nov 25 re-run showed further widening: HY 372, IG 98,
  CCC 1,405'
- 'Rates: 10Y 5.04, 30Y 5.40 (back below 5.50 M17 E warning), term premium 0.986 (back
  below 1.00); E-watch CLEAR (was FISCAL_STRESS_BUILDING); e_pathway RESERVE_EROSION;
  10Y-2Y +28bp, 10Y-3M +70bp'
- Gold 3,539 (one-year low Nov 16 on yields/dollar/hike odds); CB buying Q3 321t (most
  since Q4 2024), PBoC streak through Oct, Poland at 700t target may pause. SGOL gate
  1. DXY 103.84 (+1.9% over 8 wks); USD reserve share 56.7% Q2
- 'AI capex intact: Q3 hyperscaler capex $201.9B (+108% YoY); Amazon ~$220B 2026,
  Alphabet $195-205B held, 2027 up; FCF negative except Microsoft. AIPO gate 1. China
  NBS PMI Oct 49.3 (COPX gate 2)'
- 'Trend signals Nov 20 (shadow, never a directive): AIPO WEAKENING (-6.20pp short
  / -12.37pp medium vs PAVE/QQQM/URA); XAR INCONCLUSIVE (-1.15/-8.10 vs ITA/PPA);
  SGOL INCONCLUSIVE (own down/down, no macro agreement); MLPX labeled INCONCLUSIVE
  but HY_OAS gate missing (effectively DATA_UNAVAILABLE, ENG-60). Store: 4 entries
  added, 12 forward outcomes filled, committed'
- Q3 audit v1.71 PARTIAL items still open (Calibration_State 6 items 49/50/51)
open_decisions:
- 'Primary Roth 9838: AIPO 18.3% (Nov 20 prices) vs 0% sheet target, but framework
  rates AIPO HOLD at +3.29% EV; at sheet targets the account returns 0.28% vs 4.36%
  required (4.08pp shortfall, was 4.48pp) - keep or change the 0% target'
- 'VYMI (EV -5.34%, REDUCE) and SCHD (EV -0.13%, REDUCE_TO_MIN; below SGOV +0.81%)
  carry reduce directives with DualRoleConflict (dominant roles clear: intl broad
  equity 68%, domestic broad equity 49%); M06 HoldJustification with EV math required
  before any hold. B at 32.3% caps any rotation at 50% and high-urgency only'
- SGOL (EV +1.14%) and VTIP (EV +0.06%) carry ADD directives; before any SGOL add
  run M14.EntryExtensionGuard and the war-premium entry guard (Hormuz still active).
  Primary IRA scenario-weighted SGOL 16.9% vs current 5.8%
- Primary IRA 6469 feasibility shortfall 3.53pp (0.74% vs 4.28% required; was 3.91pp).
  Taxable 9768 feasible at 0.87% (drawdown-adjusted 3.46); VTI REDUCE_TO_MIN (EV +0.35%)
- 'Relative IRA/Roth: floors intact (expected 1.29% / 0.90% at sheet targets; ~1.20%
  at current Relative IRA weights); Relative sheet last edited Aug 14 - share counts
  may be stale; PassiveMandateAbsent warnings on MLPX (Relative IRA 20.2%, Relative
  Roth 33.9%) and VTIP (Relative Roth 17.4%)'
- Brent basis decision (futures vs Dated) is currently moot - both score 1 this session
  - but still unresolved for when they diverge again
next_session_flags:
- Write-back for the Nov 20 session was executed Nov 25 after re-running advisor_run_computation
  (server cache lost) and re-applying the identical Nov 20 answers; vector reproduced
  exactly. Prices/values in this entry are Nov 20; Portfolio_State may carry the Nov
  25 market snapshot from the cache-restoring run - re-fetch everything next session
- Update 'Allocation - Relative's Schwab Accounts' share counts before the next session
  (last edited Aug 14); floor-check weights this session excluded cash (Relative IRA
  2.7%), so they summed to 97.3%
- 'F_check_gdp ambiguity: rubric says nominal GDP (>3% x 2 quarters) but its 2-3%
  ''approaching'' band only fits real GDP. Scored 1 on real (Q2 2.2, Q3 3.4); literal
  nominal reading (Q2 8.5, Q3 5.6) would score 3 and lift F - needs a rubric decision'
- 'Coding backlog (still open): run_computation reports ''180d median history unavailable''
  for HY/IG/CCC; C_check_brent evidence ignores the 1.4x 90d rule; MLPX trend labeled
  INCONCLUSIVE when HY_OAS gate is missing (ENG-60); XAR TSC condition ''defense budget
  trajectory'' has no evaluator; AIPO 14% unclassified'
- ENG-76 (MCP stdin deadlock) fixed and verified Nov 20 - run_computation, apply_scoring,
  evaluate_allocation, evaluate_trend_signal all completed via MCP without hangs or
  fallbacks; Nov 25 run_computation and write-back also completed normally
- 'Conversation-level note: Claude could not run code in the Nov 20 conversation (bank
  connector used earlier in it); account weights were computed by hand'
