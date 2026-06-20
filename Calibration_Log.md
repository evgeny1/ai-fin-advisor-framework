# Calibration Log — Archive
<!-- Split from Calibration_State.md as of v1.12, May 6, 2026 (framework-v2-architecture-split) -->
<!-- Purpose: append-only permanent archive of calibration history -->
<!-- Entries are moved here from Calibration_State.md §3 at each Q-end audit when §3 exceeds 10 entries -->
<!-- Archived annually into year-specific files (e.g., Archive_2026Q2.md) per M12 compaction rules -->
<!-- Do NOT edit historical entries — append only -->
<!-- SCOPE RULE (added 2026-06-20, alongside Calibration_State.md §3's retroactive cleanup):
     this file inherits §3's scope — calibration/methodology rationale only. Going forward,
     do NOT append pure engineering/code/doc-hygiene entries here, even when a §3 compaction
     would otherwise move them — those live in FRAMEWORK_BACKLOG_ARCHIVE.md only. This rule
     is NOT applied retroactively to entries already archived below (append-only, see above) --
     some predate the engineering/calibration split convention entirely. -->

---

## Section 3 Archive — Calibration History (Entries Archived May 6, 2026)

2026-04-19 - Initial instantiation (v1.0). HY_STRESS_DELTA +150 bps, HY_RECESSION_DELTA +300 bps, IG_TRANSMISSION_DELTA +60 bps, CCC floor +200 bps. HY baseline ~285 bps.

2026-04-21 - Framework update (v1.2). Section 6 Session State Log added. M03 DeriveScenarioProbabilities() added.

2026-04-21 - First full portfolio audit session. Probabilities: A=7%, B=44%, C=36%, D=3%, E=7%, F=3%.

2026-04-22 - Scheduled review. Probabilities: A=8%, B=45%, C=38%, D=3%, E=3%, F=3%. PAVE FLAGGED (subsequently revised to watch Apr 28).

---

## Section 3 Archive — Calibration History (Entries Archived June 19, 2026; v1.12-v1.28)

2026-05-06 - Architecture session (v1.12). File split implemented: §7 and §8 moved to Session_Log.md; §3 entries 1-4 archived to Calibration_Log.md. M16_ReturnTableCalibration.md authored (governs §4.1 revision methodology). M12, M05, 00_INDEX updated for two-file session protocol. New roles added to §11.1 and §4.1: inflation_linked_sovereign and real_estate_equity_income (LOW confidence, [TBD] values, pending June 30 empirical audit). No portfolio analysis this session.

---

2026-05-06 - Comprehensive instrument expansion (v1.13). Probability update: A=18%(+3pp), B=35%(-1pp), C=34%(-2pp), D=3%, E=3%, F=7%. Full M14 ComputeDivergenceSignal: composite HIGH (equity_scenario_divergence HIGH at S&P 30d +10.3%). XAR confirmed sold to 12% target across all accounts — Open Decision #2 CLOSED. Five new roles added to §11.1: systematic_trend_following, consumer_defensive_equity, healthcare_defensive_equity, floating_rate_credit_income, emerging_market_equity. §4.1 return table fully calibrated for all roles using M16.CalibrationMethodology() 4-layer procedure. ADOPTED (HIGH confidence): systematic_trend_following A/B/C values; consumer_defensive_equity B value. Nine new instruments classified in §11.3: DBMF, SIVR, COPX, VTIP, XLP, VNQ, VEA, XLV, FLOT. Primary IRA structural gap RESOLVED: achievable EV +3.62% with DBMF adoption (required: 3.2%). MLPX EntryExtensionGuard preliminary analysis: guard may be clearing (estimated 90d avg ~$66; current $73.63 ~12% above avg vs 15% threshold). Verification from approved price source required before ADD executes. New target allocations issued for all 6 accounts. Relative IRA MLPX drawdown breach RESOLVED by reducing target to 24% (24% × 67% = 16.1% < 20% floor). MOVE index: ~76.8 (TradingView T2). Brent close: $101.27. S&P 500 record high: +1.46%.

2026-05-07 - Full M05 session (v1.15). Scenario probabilities updated: A=15%(-3pp), B=36%(+1pp), C=36%(+2pp), D=3%(unch), E=3%(unch), F=7%(unch). check_energy=1 this session (Brent declining 4 consecutive days vs ≥5 threshold). CPI May 12 binary event upcoming — highest priority. M14 composite HIGH unchanged. M16 analysis: secular_technology_growth Scenario B full 4-layer run completed; MEDIUM confidence; upward pending proposal logged (§6 item 35). Primary Taxable deployment complete: DBMF 854sh, XLP 196sh, COPX 212sh executed; $51,950 cash fully deployed (Open Decision #4 CLOSED). v1.13 targets confirmed live in allocation file; remaining trades executing through May 8. Portfolio total ~$762,097.

2026-05-07 - AIPO reclassification + guard clearance (v1.14). Session type: ad-hoc analysis (no allocation fetch — full M05 session required for share count targets). AIPO ThematicETF_ClassificationAudit() COMPLETE. Holdings confirmed from T1 sources: Industrials 50%, IT 30%, Utilities 20%. Top holdings: Quanta Services 8.6%, GE Vernova 8.2%, Eaton 7.9%, Vertiv 7.9%, NVDA 4.2%, AVGO 3.9%, AMD 2.1%. Revised components: RAC 0.55→0.45; STG 0.20→0.30; BMD 0.15→0.00 (ELIMINATED — no qualifying undifferentiated domestic equity; all holdings have specific AI/power binding drivers); new PDT 0.20; IHC 0.10→0.05. CORRECTION: prior session analysis (May 7 ad-hoc) erroneously stated "B improves" — WRONG. Actual revised AIPO EV = +2.42% (↓ from +2.95%), rank drops to #5 (below SIVR +2.86%). EV reduction driven by PDT B conservative = -3% and more STG weight at B = -6%. A-regime improves: +4.05% (↑ from +3.80%) due to STG A = +6% and PDT A = +4%. SIVR entry guard CLEARED: confirmed price anchors (March 14 = $76.31, March 26 = ~$63.64, April 2 = $69.11, April 24 = $72.28, May 6 = $73.79); 90d avg ~$78-82; threshold ~$94-98; current $73.79 below threshold. v1.13 estimated avg ($55-65) was incorrect — all confirmed data points above $63. COPX entry guard CLEARED: confirmed anchors (Feb 6 = $81.31, April 28 = $78.69, May 6 = $78.21); 90d avg ~$85-90; threshold ~$102-106; current $78.21 below threshold. v1.13 estimated avg ($55-65) was significantly incorrect — Feb 6 anchor $81.31 alone exceeds entire estimated range. Execution notes updated: SIVR and COPX now immediate. AI application layer instrument screen conducted: no M07-compliant pure-play instrument available (track record and/or AUM constraints). NVDA overlap noted: AIPO holds NVDA 4.2%, AVGO 3.9%, AMD 2.1% — partial overlap with MAGS. Monitor at Q2.

2026-05-11 - Full M05 session (v1.16). Scenario probabilities updated: A=12%(-3pp), B=37%(+1pp), C=38%(+2pp), D=3%(unch), E=3%(unch), F=7%(unch). check_energy reverted to 0 (Brent $107.67 rising; May 8 day-5 check FAILED — streak reversed up; Saudi Aramco CEO T1 conference call May 11: normalization into 2027 even if Hormuz opened today). FRED DATA GAP RESOLVED — first T1 credit readings in multiple sessions: HY=281 bps, IG=79 bps, CCC=920 bps (all May 8 close via FRED screenshots). MOVE=70.74 T1 confirmed (NYSE Global Indexes). Approved FRED+MOVE source URLs logged in §1. All v1.13 trades confirmed executed per allocation sheet (all 6 accounts at targets ±1pp). Portfolio total ~$769k (+$7k vs May 7 on price appreciation). No allocation changes this session. CPI May 12 binary event pending — run DeriveScenarioProbabilities() immediately on 8:30am ET release.

2026-05-13 - Full M05 session (v1.17). CPI April 2026 = 3.8% YoY (BLS T1) — C check_cpi 1→2; C raw 5→6. Scenario probabilities updated: A=7%(−5pp), B=36%(−1pp), C=44%(+6pp), D=3%(unch), E=3%(unch), F=7%(unch). MLPX EntryExtensionGuard CLEARED: 90d avg $72.31 (Feb 5 close $66.54, client-confirmed T2); threshold $86.77; current $74.40 (+2.9% above avg — well below 20%). WAR PREMIUM ENTRY GUARD also CLEARED (same threshold). BZ=F established as canonical Brent session reference (Fortune spot rejected after $3-4 discrepancy confirmed). FRED credit data via embedded spreadsheet tab (T1, May 12 close): HY=282, IG=77, CCC=937 — no thresholds fired. Gold reallocation recommended for relative accounts (Rel IRA: SGOL 26%→20%, SIVR 3%→6%, DBMF 12%→15%; Rel Roth: SGOL 22%→16%, SIVR new 4%, DBMF 18%→20%) — EV improvement +0.36pp/+0.28pp respectively — pending client execution. Portfolio total ~$775k.

2026-05-22 - Full M05 session (v1.18). Gold reallocation CONFIRMED EXECUTED — Relative IRA and Relative Roth allocation sheet targets match v1.17 recommendations exactly. Targets updated: Relative IRA SGOL 26%→20%, SIVR 3%→6%, DBMF 12%→15%; Relative Roth SGOL 22%→16%, SIVR new 4%, DBMF 18%→20%. Relative IRA EV: +3.53%→+3.89% (+0.36pp); Relative Roth EV: +4.45%→+4.73% (+0.28pp). FRED T1 credit (May 21 close via embedded spreadsheet tab): HY=278 bps (−4 from May 12), IG=75 bps (−2), CCC=939 bps (+2) — all thresholds clear. MOVE=79.72 (GOOGLEFINANCE, rising +9.0 pts from 70.74 on May 11 — approaching 80; no formal threshold yet; flag for Q2 formal integration). VIX=16.52, S&P=7,494.81. BZ=F pre-market ~$109.11 (T2, Yahoo Finance) — C-trigger clock STATUS UNRESOLVED (Brent 52-wk high $126.41 achieved between May 13 and May 22; BZ=F daily closes May 14-21 not confirmed; clock may have started and reset; requires verification at next session). Geopolitical: Iran + Oman "Persian Gulf Strait Authority" (permanent Hormuz toll system; Trump rejected — new structural C escalation); Iran uranium directive hardened (counter-deal T1 via Reuters); Rubio "encouraging signs" (soft A-signal, T1 unconfirmed); SPR ~10M barrel release (largest on record, T2). Probabilities: carry forward A=7/B=36/C=44/D=3/E=3/F=7 — no new binary events warranting re-derive. Main session: rebalancing strategy analysis — sell-winners/buy-losers thesis; conclusion: EV-optimal targets should update with scenario probabilities, not mechanically revert price drift; 1-2pp current drifts below all action thresholds. Secondary: AI capex sustainability; private credit AI; prisoner's dilemma analysis; hyperscaler knowledge asymmetry. No allocation changes.

2026-05-25 - Full M05 session (v1.19). §12 M17 Systemic Cascade Warning thresholds first
formally applied. sectorStressScore()=2 at time of session (corrected to 0 in v1.20 — see
above). CascadeLevel ALERT at session (corrected to MONITORING in v1.20). D_precursor_binding=2
per v1.19 logic (corrected to 0 in v1.20). Probabilities updated: A=7%(unch), B=36%(unch),
C=44%→41%(−3pp), D=3%→5%(+2pp), E=3%→4%(+1pp), F=7%(unch). Client approved. C-trigger
clock: Day 0 confirmed T2 — max ~5–6 consecutive closes ≥$110 (~May 13–19); reset ~May 20 on
deal optimism + Hormuz satellite data (3 supertankers crossing); 10-day requirement NOT met.
BZ=F overnight (Memorial Day) ~$107.60 (T2). FRED credit (May 21, T1 via spreadsheet tab):
HY=278, IG=75, CCC=939 — all thresholds clear; CCC quiet re-widening (+2 bps) vs HY tightening
noted. MOVE=78.43 (GOOGLEFINANCE). VIX=16.70. S&P=7,473.47 (May 22 close). S&P Futures
overnight −2.7% (7,268 — Asia-led; confirm Tuesday). THREEFYTP10=0.8117% (14-yr high). FINRA
margin debt $1.304T (Apr-26 record). Yield curve D_timing_signal=RECESSION_ONSET_PATTERN
(post-inversion re-steepening). M14 composite: HIGH unchanged. EVs updated throughout §11 at
new probability vector. All accounts at v1.18 targets (max drift: Rel Roth MLPX +1.71pp). No
rebalancing needed. Portfolio total ~$775k.

2026-05-25 - Framework v1.20 (same session day). **FW-BUG-01 CHAIN_3 two-mode scoring fix.**
Prior v1.19 session scored CHAIN_3 as FIRES based on margin debt record + gate events.
Corrected: FIRES requires MARGIN_MOM_DECLINE ≤−5% after record OR gate_count ≥3. Neither
met in Apr 2026 data (MoM was +6.8% rising to record; gate count = 2). CHAIN_3 = WATCH
(record loaded; score 0). Revised formal sectorStressScore = 0. CascadeLevel = MONITORING.
D_precursor_binding clarified = sectorStressScore only (0 formal); yield curve
D_timing_signal = RECESSION_ONSET_PATTERN is informational timing context, not a binding
variable count. D=5% maintained by prior client approval (qualitative grounds); revisit at
Q2 audit with T1 CHAIN_4 count (AACER/PACER). Phase 2 confirmed complete: M02 v2.0,
M04 v2.0, M11/M14/M17 v1.1+ all have DATA_REGISTRY_ENTRIES and BRIEFING_REGISTRY_ENTRY.

2026-05-26 - Framework v1.21 (corrections only). Four surgical fixes applied:
(1) §3 duplicate May-25 v1.19 log entries merged; (2) §11 PAVE stale CascadeLevel ALERT
reference updated to MONITORING; (3) §11 SIVR B-component arithmetic error corrected
(blended B was listed as 5.70% — both components are 6% → correct blended = 6.00%;
EV corrected from +2.92% to +3.03%); (4) §12.8 cascade level mapping table rebuilt
(duplicate Score=0 row removed, Score=2 ALERT row restored). No threshold or probability
changes this version. May 26 session notes: BZ=F ~$97 (recovering from Memorial Day −6%
plunge on US-Iran deal optimism); deal NOT signed as of May 26; A=7% unchanged per M01
NEVER rule (T2 cluster, no T1 signed agreement). VIX_30D_AVG=17.99, VIX_90D_AVG=21.24
(computed from FMP historical EOD data — M18 update confirms FMP:chart as approved source
for these series). M14 composite: HIGH unchanged.

2026-05-29 - Framework v1.22 (Q2 audit session). §4.1 adoptions: consumer_defensive_equity C
revised [0,+4]→[+2,+6] and upgraded ⚑→★ (HIGH confidence; L2: 1974 +4-6% real, 1979-80 +3-5%
real, 2022 XLP +6% real; 3 analogues; L4 pass); consumer_defensive_equity A status ⚑→★ (values
[0,+4] confirmed); systematic_trend_following D status ⚑→★ (values [-5,+15] confirmed; L2: 2008
SG CTA +18.5%, 2020 +2.5%, 1987 positive; L4 gap documented (c)). §9: MOVE thresholds formally
encoded (NORMAL<80, ELEVATED 80-100, STRESS 100-130, CRISIS 130-160, SYSTEMIC>160; HIGH confidence
on 80 and 130 anchors; MEDIUM on 100). §11: URA (Global X Uranium ETF) added — M07 PASS (foreign
exposure flag; AUM $7.81B, ER 0.69%); ComponentVector RAC(0.50)+IHC(0.30)+STG(0.20); EV +4.17%
(rank #3); targets IRA 3%, Roth 3% (funded: MAGS IRA 5%→3%, Roth 6%→4%; AIPO IRA 8%→7%,
Roth 8%→7%). Session_Log §7 compacted; Archive_2026Q2.md created. Scenario probs unchanged
(A=7/B=36/C=41/D=5/E=4/F=7). Iran MOU at negotiator level; Trump NOT signed; A held at 7%.

2026-05-30 - Framework v1.23 (Q2 audit session continuation). §4.1 adoption: emerging_market_equity
A revised [+4,+9]⚑ → [+10,+20]★ HIGH confidence. L2: 3 analogues (1991 Gulf drawdown +15-20%
real, 2003 Iraq drawdown +15-20% real, 2016 commodity rebound +10-15% real). L3: VWO
Taiwan/China 56.7% concentration depresses D/E conservative values vs broad EM benchmark
(structural adj applied — D/E remain PENDING). L4: gap to institutional anchor (+5.5%) documented
as (a)+(d); gap expected given VWO concentration vs blended EM unconditional. Client confirmed.
§11 AIPO classification weights updated for confirmed sector drift (May 30 T1 data: Industrials
57.09%, Technology 16.46%, Utilities 14.42%, Energy 6.91%, FinSvcs 3.60%): PDT 0.20→0.63,
STG 0.30→0.16, RAC+IHC restructured → RAC 0.14 (utilities/power gen), IHC 0.07 (energy/Cameco).
AIPO EV recomputed: +1.54% (↓ from +2.16%; STG weight reduction at B/C primary driver; see §11).
§11 PAVE: explicit exit triggers encoded (4 triggers: B formal fire, Aug 15 no-bill, reduced-level
extension, CascadeLevel ALERT; hold conditions: A≥20% on T1 deal, clean extension). Constituent
bucket analysis complete: Bucket A ~35-45% insulated (Eaton, Trane, CSX, UP, Basic Materials);
Bucket B ~30-40% partial (Quanta, E&C backlog 12-24mo); Bucket C ~20-25% at-risk (highway
formula contractors). §11 XAR: forward PE corrected to ~35.5x (not 66.59x trailing artifact);
classification and target confirmed. §11 MAGS: hold-only override confirmed; no ADD at EV −2.17%.
§6 items 8/13/14/15/21/32/33 marked COMPLETE. Scenario probs: A=7/B=36/C=41/D=5/E=4/F=7 unchanged.

2026-06-01 - Framework v1.24 (CHAIN_4 calibration). §12.4 revised: prior bankruptcy_quarterly_alert
of 800/quarter eliminated — undocumented, no M16 basis, exceeded empirical GFC peak (~459/quarter)
by ~74%, would never fire under any observed historical scenario. Canonical series confirmed:
S&P Global Market Intelligence large-company (public co. with ≥$2M public debt; private co. with
≥$10M assets/liabilities). T1 source amended: ABI/Epiq AACER press releases qualify as
T1-equivalent — same underlying data as direct AACER access, published within days of month-end.
M16 4-layer calibration complete (HIGH confidence):
  L1: GFC peak ~459/quarter empirical ceiling; normal baseline ~100-150/quarter.
  L2: 2009 GFC ~459/quarter (full systemic), 2010 aftermath ~207/quarter (confirmed stress),
      2024-2026 ~170-200/quarter (elevated, not stress regime). 3 clean analogues.
  L3: (a) CHAIN_4 is early-warning signal — thresholds should fire before GDP/HY confirm
      recession; argues lower end of stress range. (b) S&P series includes ≥$2M floor;
      some small-company noise at elevated baseline; argues WATCH not too close to current
      readings. Net: adjustments roughly offset; proposed thresholds held.
  L4: neutral distribution (A=35/B=15/C=15/D=10/E=5/F=20) — 300/quarter consistent with
      D-weight environment; A=35/F=20 growth-dominant → ~90-120/quarter, well clear of WATCH.
      Consistency check PASS.
New thresholds: WATCH ≥220/quarter ★ HIGH; FIRES ≥300/quarter ★ HIGH.
Current Q1 2026: 188/quarter — BELOW WATCH. CHAIN_4 score = 0. CascadeLevel remains MONITORING.
§6 item 38 updated. No probability changes this version.

2026-06-01 - Framework v1.25 (§4.1 return table — items 6-7 of §6 item 23 adopted).
rate_sensitive_income_short_duration A [0,2]→[1,3] and D [0,3]→[1,4] ADOPTED HIGH confidence.
M16 4-layer complete: L1 real T-bill anchor ~1.5-2% real; L2: 3 analogues each scenario
(A: 2003/2016/1991; D: 2008/2020/1990-91) + starting rate 3.62% structural upward adj;
L3: ≤1yr duration caps price appreciation — rejects [2,6] D upside (implausible deflation
depth required); L4: neutral-weighted +0.85% vs anchor, gap -0.65 to -1.15pp, PASS ±3pp.
STG B: [-12,-3] proposal formally rejected — L3 ignores contract lock-in, L4 sits -1.5pp
below anchor on wrong side. June 30 adjudication is [-2,+4] vs status quo [-6,-1].
§6 item 23 enumerated: 10 confirmed proposals written out; 4 unrecoverable from v1.12 split.
SGOV EV updated: +0.76%→+0.89% (A and D conservative values both increase by +1pp).
No probability changes this version.

2026-06-01 - Framework v1.26 (§4.1 items 9-10 of §6 item 23 adopted; M16 work complete on all 10).
real_asset_contracted_revenue D [2,6]→[-6,+2] and E [2,5]→[-10,0] ADOPTED HIGH confidence.
M16 4-layer: L1 infrastructure anchor 4-5% real; L2 primary analogue 2008 AMZ -53% price
+10% distribution = ~-30% total nominal real (worst on record); 2020 AMZ ~-20%;
L3 MLPX contracted revenue quality above broad AMZ → D conservative -8%→-6%;
L4 neutral-weighted +2.65% vs anchor 4-5%, gap -1.35 to -2.35pp, PASS ±3pp.
STG D [-20,-8] and E [-18,-6]: direction correct, empirically supported (NDX -41.7% 2008),
BLOCKED L4 — must adopt jointly with STG B upward revision at June 30.
IHP A [-2,2] and D [-5,3]: direction correct, BLOCKED L4 — full precious metals row
coherence review required at June 30 (C value interaction).
GP A [-4,+1] (revised from [-6,0]): BLOCKED MEDIUM confidence (2 clean analogues);
L4 exception documented (role definition inherently underperforms neutral anchor).
MLPX EV updated: +5.67%→+5.10% (RAC D/E corrections; -0.57pp impact).
No probability changes this version.

2026-06-01 - Framework v1.27 (STG B + IHP A + IHP D adopted HIGH confidence).
STG B [-6,-1]→[-2,+4] ADOPTED HIGH confidence. M16 complete: Q1 2026 contamination call
reversed — Hormuz war does not affect rate/multiple mechanics defining B for secular tech.
Q1 2026 (Azure +40%, AWS +28%, GCP +63%, FOMC 3.62%, CPI 3.8%, zero withdrawals) is valid
sustained B analogue. 3 clean analogues (1973-82, Q1 2026, + 2022 acute-phase partial).
[-12,-3] definitively rejected: L4 -1.5pp below anchor wrong side; ignores L3 lock-in.
L4: neutral +1.00% = exact anchor. Sustained vs acute B distinction now explicit in framework.
STG D rederived: [-20,-8] WRONG (1yr acute, not 2-3yr framework convention). Corrected:
[-6,0]⚑ from 2008-09 2yr annualized NDX (-5.1% real). MEDIUM (1 analogue). Pending June 30.
STG E rederived: [-18,-6] → [-12,-3]⚑. MEDIUM (1 analogue). Pending June 30.
IHP A [0,4]→[-2,+2] ADOPTED HIGH confidence. Anchor recalibrated to post-1980 2% real
(excl. 1970s supercycle). L2: 3 analogues (1996-99, 2013-15, 2016). War premium unwind adj.
IHP D [-2,4]→[-3,+3] ADOPTED HIGH confidence. Same anchor. L2: 3 analogues (2008, 2020, 1990-91).
War premium at $3,300+ limits upside vs 2020 baseline.
EVs updated: SGOL +1.43%→+1.24%; MAGS -2.17%→-0.94%; AIPO +0.02%→+0.13%.
All account EVs updated. All accounts remain feasible.
No probability changes this version.

2026-06-01 - Framework v1.28 (§4.1 multi-role adoption; EV corrections; AIPO flag closed).
STF E=[-8,+8] and F=[-5,+3] ADOPTED HIGH confidence. L2: E: 2008 Q4 SG CTA ~-4% quarterly,
2020 March DBMF ~-5%, 1987 mixed; binary structure (whipsaw vs trend acceleration) is the
calibration — wide range correct. F: 2017 ~-1%, 2018 ~-5%, 2019 ~+6%; growth trend desert.
L4: documented structural exception for both (same as D).
ILS A=[-2,1], D=[0,3], F=[-1,1] ADOPTED HIGH confidence (status upgrade; values unchanged).
L2: A: 2019/2016/2003-04 TIPS (0 to +1% real); D: 2008/2020/1990-91 (+0 to +5% real);
F: 2018/2017/2015 (-1 to +1% real). B/C/E remain MEDIUM (insufficient analogues).
CDQ D=[-5,0] and F=[-3,+2] ADOPTED HIGH confidence. L2: D: 2008-09 2yr -1.5% real,
2020 flat, 1990-91 flat; F: 2017 F-type +3-5%, 2003-07 +2-4%, 2018 ~-2%. E remains MEDIUM.
EV corrections: XLP +0.14%→+0.76% (C=0 bug fixed; C was adopted at +2 in v1.22).
MAGS line items corrected (D/E inputs showed pending values; corrected to operative D=-14, E=-10;
total -0.94% was accidentally correct).
AIPO track record: AUM $732.94M (June 1); ETF.com Best New Thematic ETF; 12-month July 24 2026.
Flag substantially closed. No probability changes this version.

---

## Section 3 Archive — Calibration History (Entries Archived June 19, 2026; v1.29)

2026-06-02 - Framework v1.29 (§11 EV corrections; URA entry guard cleared; COPX price note).
URA EntryExtensionGuard CLEARED: 90d avg $51.71 (63 trading days March 3–June 1, T2 FinancialContent/
Investing.com). Threshold $62.05 (90d avg × 1.20). Current $50.76 < $62.05. Safety margin $11.29
(18.2% below trigger). Estimation sensitivity: ±$2 on 5 unconfirmed March days shifts threshold ±$0.80;
conclusion unchanged. ADD eligible: retirement accounts only (foreign exposure flag).
§11 EV corrections — applying v1.26/v1.27 adoptions not previously propagated to instrument entries:
URA: +4.17%→+4.02% (RAC D=-6 v1.26, RAC E=-10 v1.26, STG B=-2 v1.27 now in §11 computation).
SIVR: +3.03%→+2.93% (IHP A=-2 v1.27, IHP D=-3 v1.27 now in §11 computation).
SGOL: §11 body text corrected to +1.24% (v1.27 §3 log had correct value; §11 text showed stale +1.43%).
COPX: $93.66 June 2 close (+4.00%); entry guard threshold ~$102-106; re-verify before any ADD.
No §4.1 table changes. No probability changes. No target allocation changes this version.
AIPO target reduction (IRA/Roth 7%→3%; DBMF IRA/Roth +4pp): under client deliberation; not adopted.

---

2026-06-02 - Framework v1.30 (AIPO ThematicETF_ClassificationAudit() REVISED). Full holdings re-audited from T1 source (Defiance ETFs official page, 06/02/2026, 77 holdings, $750.87M AUM). Three errors corrected from v1.14/v1.23: (1) PDT reduced 0.20→0.04 — AIPO Industrials (PWR, VRT, ETN, GEV, MTZ, STRL, NVT, HUBB, DY, utilities, data centers) are commercial RAC, not policy-driven; binding driver is hyperscaler/utility demand, NOT legislative mandates. (2) IHC increased 0.05→0.11 — uranium exposure (CCJ 3.78% + NXE 0.75%, UUUU 0.50%, DNN 0.44%, LEU 0.44%) was understated or missed in prior top-holdings review; also includes Bloom Energy (BE) 4.56% energy technology, EOSE 0.62%, FLNC 0.61% energy storage. (3) STG reduced 0.30→0.16 — GEV was erroneously counted in "IT 30%" sector bucket by prior data source; confirmed Industrials/RAC. RAC increased 0.45→0.55. New UNCLASSIFIED exposure: bitcoin miners ~7% NAV (11 holdings: HUT, BTDR, HIVE, RIOT, CLSK, CIFR, MARA, CORZ, IREN, WULF, BTBT); no registered M15 role; treated as 0% EV contribution (conservative — unknown/likely negative in B/C). EV corrected: +0.13%→+3.28% (using all current operative §4.1 values: STG B=−2 ★, RAC D=−6 ★, RAC E=−10 ★, STG D=−14 ⚑ operative). ⚠ Session instructions' +3.54% used stale RAC D=+2, RAC E=+2, STG B=−6 — corrected to +3.28% using live calibration state. Rank: ~#10→#3 (above SIVR +2.93%, below URA +4.02%). v1.29/v1.23 PDT-dominant classification (0.63 PDT) was itself a prior error corrected today — the 57% Industrials weight was misclassified as PDT; binding driver test confirms commercial RAC. Q3 action required: add role for bitcoin_mining / speculative_infrastructure_growth (§6 item TBD). last_reviewed updated to June 2, 2026. No §4.1 changes. No probability changes. No target allocation changes this version.

<!-- Archived 2026-06-20 (§3 compaction, ENG-18 session) — restores §3's "last 10
     entries" invariant after adding the v1.41 Section 12 entry. -->

---

2026-06-04 - Framework v1.31 (M18 v1.2 regime re-verification; M14 re-computation; STG B challenge closed).
BZ=F Feb 25 2026 actual $70.85 T1 (estimate $70 accurate, +$0.85). energy_90d May 26 corrected +36.9%
(vs estimate +38.6%) — HIGH tier CONFIRMED unchanged. VIX Feb 25 = 17.93 confirmed as actual T1 close
(was NOT an estimate). VIX_change_90d_pts -1.23 pts confirmed exact. Prior M14 composite HIGH: FULLY CONFIRMED.
Today (June 4): energy_90d = BZ=F $97.81 (Jun 3 T1) vs $92.69 (Mar 6 T1 — 90d anchor) = +5.52% ->
commodity_fear_divergence NOT FIRING (war premium now inside 90d window; below 10% MODERATE threshold).
VIX_change_90d_pts = 16.06 - 29.49 = -13.43 pts. broad_equity_30d = SPY Apr 22->Jun 3 +6.05% ->
equity_scenario_divergence HIGH. M14 composite = HIGH (equity-driven only). UnderweightReviewTrigger NOT fired.
STG B challenge CLOSED: MAGS +4.79% YTD (Jun 4 live) confirms [-2,+4] * adoption (v1.27). Stale -6% YTD challenge refuted.
Sec 11.2 descriptor update (editorial: "-6% to -1%" -> "[-2,+4] *") deferred to June 30.
PAVE EV confirmed -4.03% at current price $57.61 and current probability vector. No exit triggers fired.
Iran qualitative: MOU unsigned, talks fragile, C not structurally moderated — CARRY A=7/B=36/C=41/D=5/E=4/F=7.
M12 PATTERN_B Step 3b added: instruments.json local write to MCP server directory.
M12 PATTERN_A amendment drafted as artifact. instruments.json written: ["MLPX","DBMF","SGOL","VTIP","AIPO",
"XAR","SGOV","SIVR","COPX","MAGS","XLP","PAVE","URA"]. No Sec 4.1 changes. No probability changes.

<!-- Archived 2026-06-20 (§3 compaction, GAP-16/ENG-13 session) — restores §3's
     "last 10 entries" invariant after adding the v1.42 GAP-16 entry. -->

---
