# Calibration State

Persistent framework configuration — load at every session start alongside Session Log.

# Version: 1.29  Last updated: June 2, 2026 (§11 EV corrections: URA +4.17%→+4.02%, SIVR +3.03%→+2.93%,
# SGOL §11 text +1.43%→+1.24%; URA EntryExtensionGuard CLEARED: 90d avg $51.71, threshold $62.05,
# current $50.76 clear by 18.2%; COPX price note updated $93.66 June 2 close;
# no §4.1 changes; no probability changes; no target allocation changes this version)

**File split as of v1.12:**
- Session observations (§7) and session state (§8) now live in **Session_Log.md** (fetched concurrently at session start).
- Prior calibration history before last-10 entries lives in **Calibration_Log.md**.
- This file (Calibration_State.md) is the LIVE CONFIG — kept lean for reliable write-back.

---

## Load Verification Requirement

At session start, after both files are fetched, the advisor must state in the briefing:

"Calibration State loaded, last update: June 1, 2026 | Session Log loaded"

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
- May 26 full session: BZ=F ~$97 (recovering from Memorial Day plunge of ~6% on US-Iran deal optimism). C-trigger clock restart requires close ≥$110 — not imminent under current deal trajectory.
- SGOL WTI floor ($55): WTI ~$91 (May 26). Comfortably clear. DXY ~99 carry, below 105. No SGOL invalidation risk.

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

May 26 full session: **CPI B trigger status: print 2 of 3 (March 3.3%, April 3.8%). May CPI print mid-June is the binary event: if ≥4.0% → B formal trigger fires (3rd print).** FOMC holding 3.50–3.75% (Kevin Warsh confirmed as Fed Chair May 22; FOMC hawkish; rate hike risk discussed for 2027). Q1 GDP +2.0% (positive). Sahm Rule 0.20. Term premium (THREEFYTP10): 0.8117% (May 15 — 14-yr high, rising). 30Y yield: 5.07% (approaching M17 §12.5 warning level). Yield curve 10Y–2Y +43bp; 10Y–3M +88bp — post-inversion re-steepening = D_timing_signal RECESSION_ONSET_PATTERN.

---

## Section 3 - Calibration Log (last 10 entries; prior entries in Calibration_Log.md)

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

2026-05-22 - Full M05 session (v1.18). Gold reallocation CONFIRMED EXECUTED — Relative IRA and Relative Roth allocation sheet targets match v1.17 recommendations exactly. Targets updated: Relative IRA SGOL 26%→20%, SIVR 3%→6%, DBMF 12%→15%; Relative Roth SGOL 22%→16%, SIVR new 4%, DBMF 18%→20%. Relative IRA EV: +3.53%→+3.89% (+0.36pp); Relative Roth EV: +4.45%→+4.73% (+0.28pp). FRED T1 credit (May 21 close via embedded spreadsheet tab): HY=278 bps (−4 from May 12), IG=75 bps (−2), CCC=939 bps (+2) — all thresholds clear. MOVE=79.72 (GOOGLEFINANCE, rising +9.0 pts from 70.74 on May 11 — approaching 80; no formal threshold yet; flag for Q2 formal integration). VIX=16.52, S&P=7,494.81. BZ=F pre-market ~$109.11 (T2, Yahoo Finance) — C-trigger clock STATUS UNRESOLVED (Brent 52-wk high $126.41 achieved between May 13 and May 22; BZ=F daily closes May 14-21 not confirmed; clock may have started and reset; requires verification at next session). Geopolitical: Iran + Oman "Persian Gulf Strait Authority" (permanent Hormuz toll system; Trump rejected — new structural C escalation); Iran uranium directive hardened (counter-deal T1 via Reuters); Rubio "encouraging signs" (soft A-signal, T1 unconfirmed); SPR ~10M barrel release (largest on record, T2). Probabilities: carry forward A=7/B=36/C=44/D=3/E=3/F=7 — no new binary events warranting re-derive. Main session: rebalancing strategy analysis — sell-winners/buy-losers thesis; conclusion: EV-optimal targets should update with scenario probabilities, not mechanically revert price drift; 1-2pp current drifts below all action thresholds. Secondary: AI capex sustainability; private credit AI; prisoner's dilemma analysis; hyperscaler knowledge asymmetry. No allocation changes.

2026-05-13 - Full M05 session (v1.17). CPI April 2026 = 3.8% YoY (BLS T1) — C check_cpi 1→2; C raw 5→6. Scenario probabilities updated: A=7%(−5pp), B=36%(−1pp), C=44%(+6pp), D=3%(unch), E=3%(unch), F=7%(unch). MLPX EntryExtensionGuard CLEARED: 90d avg $72.31 (Feb 5 close $66.54, client-confirmed T2); threshold $86.77; current $74.40 (+2.9% above avg — well below 20%). WAR PREMIUM ENTRY GUARD also CLEARED (same threshold). BZ=F established as canonical Brent session reference (Fortune spot rejected after $3-4 discrepancy confirmed). FRED credit data via embedded spreadsheet tab (T1, May 12 close): HY=282, IG=77, CCC=937 — no thresholds fired. Gold reallocation recommended for relative accounts (Rel IRA: SGOL 26%→20%, SIVR 3%→6%, DBMF 12%→15%; Rel Roth: SGOL 22%→16%, SIVR new 4%, DBMF 18%→20%) — EV improvement +0.36pp/+0.28pp respectively — pending client execution. Portfolio total ~$775k.

2026-05-11 - Full M05 session (v1.16). Scenario probabilities updated: A=12%(-3pp), B=37%(+1pp), C=38%(+2pp), D=3%(unch), E=3%(unch), F=7%(unch). check_energy reverted to 0 (Brent $107.67 rising; May 8 day-5 check FAILED — streak reversed up; Saudi Aramco CEO T1 conference call May 11: normalization into 2027 even if Hormuz opened today). FRED DATA GAP RESOLVED — first T1 credit readings in multiple sessions: HY=281 bps, IG=79 bps, CCC=920 bps (all May 8 close via FRED screenshots). MOVE=70.74 T1 confirmed (NYSE Global Indexes). Approved FRED+MOVE source URLs logged in §1. All v1.13 trades confirmed executed per allocation sheet (all 6 accounts at targets ±1pp). Portfolio total ~$769k (+$7k vs May 7 on price appreciation). No allocation changes this session. CPI May 12 binary event pending — run DeriveScenarioProbabilities() immediately on 8:30am ET release.

2026-05-07 - AIPO reclassification + guard clearance (v1.14). Session type: ad-hoc analysis (no allocation fetch — full M05 session required for share count targets). AIPO ThematicETF_ClassificationAudit() COMPLETE. Holdings confirmed from T1 sources: Industrials 50%, IT 30%, Utilities 20%. Top holdings: Quanta Services 8.6%, GE Vernova 8.2%, Eaton 7.9%, Vertiv 7.9%, NVDA 4.2%, AVGO 3.9%, AMD 2.1%. Revised components: RAC 0.55→0.45; STG 0.20→0.30; BMD 0.15→0.00 (ELIMINATED — no qualifying undifferentiated domestic equity; all holdings have specific AI/power binding drivers); new PDT 0.20; IHC 0.10→0.05. CORRECTION: prior session analysis (May 7 ad-hoc) erroneously stated "B improves" — WRONG. Actual revised AIPO EV = +2.42% (↓ from +2.95%), rank drops to #5 (below SIVR +2.86%). EV reduction driven by PDT B conservative = -3% and more STG weight at B = -6%. A-regime improves: +4.05% (↑ from +3.80%) due to STG A = +6% and PDT A = +4%. SIVR entry guard CLEARED: confirmed price anchors (March 14 = $76.31, March 26 = ~$63.64, April 2 = $69.11, April 24 = $72.28, May 6 = $73.79); 90d avg ~$78-82; threshold ~$94-98; current $73.79 below threshold. v1.13 estimated avg ($55-65) was incorrect — all confirmed data points above $63. COPX entry guard CLEARED: confirmed anchors (Feb 6 = $81.31, April 28 = $78.69, May 6 = $78.21); 90d avg ~$85-90; threshold ~$102-106; current $78.21 below threshold. v1.13 estimated avg ($55-65) was significantly incorrect — Feb 6 anchor $81.31 alone exceeds entire estimated range. Execution notes updated: SIVR and COPX now immediate. AI application layer instrument screen conducted: no M07-compliant pure-play instrument available (track record and/or AUM constraints). NVDA overlap noted: AIPO holds NVDA 4.2%, AVGO 3.9%, AMD 2.1% — partial overlap with MAGS. Monitor at Q2.

2026-05-07 - Full M05 session (v1.15). Scenario probabilities updated: A=15%(-3pp), B=36%(+1pp), C=36%(+2pp), D=3%(unch), E=3%(unch), F=7%(unch). check_energy=1 this session (Brent declining 4 consecutive days vs ≥5 threshold). CPI May 12 binary event upcoming — highest priority. M14 composite HIGH unchanged. M16 analysis: secular_technology_growth Scenario B full 4-layer run completed; MEDIUM confidence; upward pending proposal logged (§6 item 35). Primary Taxable deployment complete: DBMF 854sh, XLP 196sh, COPX 212sh executed; $51,950 cash fully deployed (Open Decision #4 CLOSED). v1.13 targets confirmed live in allocation file; remaining trades executing through May 8. Portfolio total ~$762,097.

2026-05-06 - Comprehensive instrument expansion (v1.13). Probability update: A=18%(+3pp), B=35%(-1pp), C=34%(-2pp), D=3%, E=3%, F=7%. Full M14 ComputeDivergenceSignal: composite HIGH (equity_scenario_divergence HIGH at S&P 30d +10.3%). XAR confirmed sold to 12% target across all accounts — Open Decision #2 CLOSED. Five new roles added to §11.1: systematic_trend_following, consumer_defensive_equity, healthcare_defensive_equity, floating_rate_credit_income, emerging_market_equity. §4.1 return table fully calibrated for all roles using M16.CalibrationMethodology() 4-layer procedure. ADOPTED (HIGH confidence): systematic_trend_following A/B/C values; consumer_defensive_equity B value. Nine new instruments classified in §11.3: DBMF, SIVR, COPX, VTIP, XLP, VNQ, VEA, XLV, FLOT. Primary IRA structural gap RESOLVED: achievable EV +3.62% with DBMF adoption (required: 3.2%). MLPX EntryExtensionGuard preliminary analysis: guard may be clearing (estimated 90d avg ~$66; current $73.63 ~12% above avg vs 15% threshold). Verification from approved price source required before ADD executes. New target allocations issued for all 6 accounts. Relative IRA MLPX drawdown breach RESOLVED by reducing target to 24% (24% × 67% = 16.1% < 20% floor). MOVE index: ~76.8 (TradingView T2). Brent close: $101.27. S&P 500 record high: +1.46%.

2026-05-06 - Architecture session (v1.12). File split implemented: §7 and §8 moved to Session_Log.md; §3 entries 1-4 archived to Calibration_Log.md. M16_ReturnTableCalibration.md authored (governs §4.1 revision methodology). M12, M05, 00_INDEX updated for two-file session protocol. New roles added to §11.1 and §4.1: inflation_linked_sovereign and real_estate_equity_income (LOW confidence, [TBD] values, pending June 30 empirical audit). No portfolio analysis this session.

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
| inflation_hedge_precious_metals | [-2, 2]★ | [6, 12] | [-2, 6] | [-3, 3]★ | [10, 20] | [-3, 1] |
| inflation_hedge_commodity_linked | [2, 6] | [6, 12] | [7, 13] | [-8, -2] | [2, 6] | [2, 5] |
| real_asset_contracted_revenue | [3, 7] | [6, 14] | [8, 16] | [-6, 2]★ | [-10, 0]★ | [3, 7] |
| policy_driven_thematic_equity | [4, 8] | [-3, 1] | [-1, 3] | [-5, -1] | [-6, -2] | [4, 8] |
| rate_sensitive_income_short_duration | [1, 3]★ | [1, 3] | [1, 3] | [1, 4]★ | [-2, 2] | [1, 3] |
| rate_sensitive_income_long_duration | [3, 7] | [-4, -1] | [-5, -2] | [5, 10] | [-10, -3] | [-4, -1] |
| broad_market_equity_domestic | [5, 12] | [-8, -2] | [-4, -1] | [-12, -4] | [-8, -3] | [7, 14] |
| broad_market_equity_international | [4, 9] | [-5, -1] | [-6, -2] | [-8, -3] | [-10, -4] | [3, 8] |
| secular_technology_growth | [6, 16] | [-2, +4]★ | [+2, +8] | [-6, 0]⚑ | [-12, -3]⚑ | [4, 11] |
| inflation_linked_sovereign | [-2, 1]★ | [1, 4]⚑ | [1, 4]⚑ | [0, 3]★ | [-1, 2]⚑ | [-1, 1]★ |
| real_estate_equity_income | [3, 8]⚠ | [-6, -1]⚠ | [-10, -4]⚠ | [-3, 2]⚠ | [-10, -3]⚠ | [2, 5]⚠ |
| systematic_trend_following | [-12, -3]★ | [+15, +30]★ | [+18, +35]★ | [-5, +15]★ | [-8, +8]★ | [-5, +3]★ |
| consumer_defensive_equity | [0, +4]★ | [+2, +6]★ | [+2, +6]★ | [-5, 0]★ | [-8, -2]⚑ | [-3, +2]★ |
| healthcare_defensive_equity | [1, 5]⚑ | [1, 4]⚑ | [-2, 3]⚑ | [-4, 1]⚑ | [-8, -2]⚑ | [1, 5]⚑ |
| floating_rate_credit_income | [1, 3]⚑ | [1, 3]⚑ | [1, 3]⚑ | [-10, -4]⚑ | [-8, -2]⚑ | [1, 3]⚑ |
| emerging_market_equity | [+10, +20]★ | [-12, -6]⚑ | [-15, -9]⚑ | [-25, -15]⚑ | [-22, -14]⚑ | [4, 11]⚑ |

secular_technology_growth: added v1.7 Apr 28. B and C values revised v1.8 Apr 30.
B revised [-6,-1]→[-2,+4] ADOPTED HIGH confidence (v1.27, June 1, 2026). M16 4-layer:
  L1: unconditional anchor ~1% real (VCMM 0-2%, RA ~1%, midpoint ~1%).
  L2: (a) 1973-82 sustained stagflation: IBM/growth -2 to +3% real/yr — clean sustained B.
      (b) 2022 B-entry shock: NDX -33% nominal (~-25% real) — partially relevant; acute phase.
      (c) Q1 2026 sustained B: Azure +40%, AWS +28%, GCP +63%, FOMC holding 3.62%, CPI 3.8%,
          zero guidance withdrawals — VALID sustained B analogue. Prior contamination call
          REVERSED: Hormuz war does not affect rate/multiple mechanics defining B for secular tech.
          Distinction: 2022 = acute B-entry (rates 0→4.5%); Q1 2026 = sustained B (rates held).
          Framework scenarios are structural states — Q1 2026 IS the sustained B environment.
  L3: (a) Contract lock-in (+2-4% upward): Google backlog $460B QoQ near-double confirmed.
      (b) Multiple compression (-5-10% downward): P/E 30x→20x at sustained elevated rates.
      (c) Capex sustainability (±2%): uncertain; FCF pressure real but not yet crisis-level.
  L4: neutral conservative = +1.00% vs anchor ~1%. Gap = 0.0pp. EXACT PASS.
  [-12,-3] competing proposal DEFINITIVELY REJECTED: L4 sits at -0.50% vs anchor (-1.5pp
  below on wrong side); structurally ignores contract lock-in documented in L3.
D provisional value revised: prior proposal [-20,-8] WRONG — calibrated to 1-year acute duration,
  inconsistent with framework 2-3yr D convention. Rederived: [-6,0]⚑ (conservative -6% from
  2008-09 2yr annualized NDX: -41.7%+54.7% = -5.1% real; -12,-3] rederived for E below).
  Only 1 clean D analogue (2008-09) — MEDIUM confidence. Adopt at June 30.
E provisional value: [-12,-3]⚑ (conservative -12% from 2008 Q4 acute 6-12mo annualized;
  shorter duration than D but more violent; 1 clean analogue — MEDIUM confidence). Adopt at June 30.
inflation_hedge_precious_metals Scenario C: revised v1.8 Apr 30 (C-hawk regime empirical data).
A revised [0,4]→[-2,+2] ADOPTED HIGH confidence (v1.27, June 1, 2026). M16 4-layer:
  L1: Post-1980 gold anchor ~2% real unconditional (excluding 1970s supercycle which inflates
      long-run ~3% anchor; post-1980 regime more relevant for modern monetary framework).
  L2: (a) 1996-1999 normalization: gold -3 to -5%/yr real (real rates rising, dollar strong).
      (b) 2013-2015 taper/hike cycle: gold -10 to -30% (significant A-type rate normalization).
      (c) 2016 post-election normalization: gold -3% nominal. 3 clean A analogues.
  L3: War premium unwind at elevated starting price (~$3,300+): Hormuz resolution removes
      geopolitical bid. Downward structural adjustment. Conservative -2% reflects mild 2016-type
      normalization; upside +2% reflects faster-than-expected disinflation with slow rate cuts.
  L4: row neutral-weighted with A=-2: -0.50% vs 2% post-1980 anchor. Gap -2.5pp. PASS ±3pp.
D revised [-2,4]→[-3,+3] ADOPTED HIGH confidence (v1.27, June 1, 2026). M16 4-layer:
  L1: Same post-1980 gold anchor ~2% real.
  L2: (a) 2008 full year: gold ~flat (-2% nominal) — initial -30% then full recovery.
      (b) 2020 COVID D-scenario: gold +25% (aggressive Fed intervention).
      (c) 1990-91 recession: gold -2% to flat. 3 clean D analogues.
  L3: War premium unwind at $3,300+ starting price partially offsets flight-to-safety bid.
      Conservative -3% (worse than current -2%) reflects elevated war-premium starting point.
      Upside +3% (reduced from +4%) — $3,300 base limits upside vs 2020 $1,500 baseline.
  L4: row neutral-weighted with D=-3: same -0.50% (A=-2 dominates the change). PASS ±3pp.
real_asset_contracted_revenue B and C: revised v1.11 May 6 (AMZI 2021-2024 empirical data). D revised [2,6]→[-6,+2] ADOPTED HIGH confidence (v1.26, June 1, 2026). E revised [2,5]→[-10,0] ADOPTED HIGH confidence (v1.26). M16 4-layer complete: L1 infrastructure unconditional ~4-5% real; L2: 2008 AMZ price -53% + ~10% distribution yield = ~-30% total nominal real (primary D analogue), 2020 AMZ ~-20% full year; L3: MLPX contracted fee-based revenue quality above broad AMZ index → upward adj from -8% to -6% D conservative; L4: neutral-weighted +2.65% vs anchor 4-5%, gap -1.35 to -2.35pp, PASS ±3pp. Prior D=[2,6] and E=[2,5] were clearly inconsistent with 2008 empirical data (-30% total real). E more negative than D: acute systemic rupture without multi-year recovery buffer.
rate_sensitive_income_short_duration: A revised [0,2]→[1,3] ADOPTED HIGH confidence (v1.25, June 1, 2026). D revised [0,3]→[1,4] ADOPTED HIGH confidence (v1.25). M16 4-layer complete: L1 real T-bill anchor ~1.5-2% real unconditional; L2: A analogues 2003 (0 to -1% real), 2016 (-1.5 to -0.5%), 1991 (0 to +1%) + starting rate 3.62% structural upward adj; D analogues 2008 (+1-3% real), 2020 (0-1%), 1990-91 (+1.5-2.5%) + starting rate adj; L3: duration ≤1yr caps price appreciation — limits upside, rejects [2,6] D proposal; L4 neutral check: +0.85% midpoint vs anchor ~1.5-2%, gap -0.65 to -1.15pp, PASS ±3pp. Original proposals [1,4] (A) and [2,6] (D) rejected.
inflation_linked_sovereign: added v1.12 May 6. A=[-2,1] ADOPTED HIGH confidence (v1.28, June 1, 2026). L2: 2019 Fed cuts (+0-1% real), 2016 neutral (+0-1%), 2003-04 Fed cutting proxy (+1-2%). Values unchanged from ⚑. D=[0,3] ADOPTED HIGH confidence (v1.28). L2: 2008 TIPS ~+2% real, 2020 TIPS +3-5% real (Fed support), 1990-91 proxy +0-2%. F=[-1,1] ADOPTED HIGH confidence (v1.28). L2: 2018 TIPS ~-1% real (rate hike), 2017 +1%, 2015 hiking cycle ~-1%. B=[1,4] and C=[1,4] remain ⚑: 2022 is the only clean B/C TIPS analogue (MEDIUM). E=[-1,2] remains ⚑: 2 clear analogues (2008, 2020 March). Layer 4 neutral check (A=-2, D=0, F=-1): -0.65% vs real yield anchor ~1.89%. Gap -2.54pp. PASS ±3pp.
real_estate_equity_income: added v1.12 May 6. ALL values LOW confidence — irreconcilable 1970s NAREIT analog (+3-6% real) vs 2022 VNQ actual (-26% nominal). Root cause: modern REIT leverage 40-60% LTV vs 1970s 20-30% LTV. Requires leverage-adjusted calibration at June 30.
systematic_trend_following: added v1.13 May 6. A/B/C ADOPTED HIGH confidence (v1.13). D ADOPTED HIGH confidence (v1.22). E=[-8,+8] ADOPTED HIGH confidence (v1.28, June 1, 2026). L2: 2008 Q4 SG CTA ~-4% quarterly (acute whipsaw), 2020 March DBMF ~-5% (brief correlation spike), 1987 (mixed — some CTAs profitable on short equity). L3: E is binary — correlation spike + trend reversal (bearish) vs established trend acceleration (bullish); wide range IS the calibration. L4: documented structural exception (same as D — DBMF unconditional anchor inapplicable to E-specific scenario). F=[-5,+3] ADOPTED HIGH confidence (v1.28). L2: 2017 SG CTA ~-1% (smooth uptrend, trend desert), 2018 ~-5% (late-cycle reversals), 2019 ~+6% (late-cycle trend development). L3: growth overheat → equities trend smoothly, rates rising gradually, commodities mixed → fewer disruptive cross-asset trends → managed futures headwind. L4: documented structural exception. Layer 4 neutral check: +5.03% midpoints — consistent with AQR TSMOM +5-8% unconditional real.
consumer_defensive_equity: added v1.13 May 6. A/B/C ADOPTED HIGH confidence (v1.13/v1.22). D=[-5,0] ADOPTED HIGH confidence (v1.28, June 1, 2026). L2: 2008-09 2yr annualized XLP ~-1.5% real (XLP -15% in 2008, +14% in 2009; 2yr annualized ~-1.5%); 2020 XLP ~flat; 1990-91 ~flat. L3: Conservative -5% calibrated to extended 3yr D where recovery doesn't fully arrive; upside 0% reflects sustained deflationary drag prevents positive real return. F=[-3,+2] ADOPTED HIGH confidence (v1.28). L2: 2017 XLP F-type +3-5% real, 2003-07 pre-GFC growth +2-4% real, 2018 late-cycle ~-2% real (Fed hiking). L3: growth overheat → staples underperform market but maintain pricing power; modest positive to slight negative real. E=[-8,-2] remains ⚑: variation too wide across analogues (2008 Q4: ~-30% annualized vs 1998 LTCM: ~flat). MEDIUM. Layer 4 neutral check (D=-5, E=-8, F=-3): -0.90% vs anchor 1-3%. Gap -1.90 to -3.90pp. PASS ±3pp (toward limit — acceptable given role defines B/C alpha).
healthcare_defensive_equity: added v1.13 May 6. ALL values PENDING June 30 (MEDIUM confidence). Layer 4 neutral check: +1.70% midpoints — below JPM LTCMA healthcare 2-4% real; gap reflects B/C distribution penalizing equity. Resolve at June 30.
floating_rate_credit_income: added v1.13 May 6. ALL values PENDING June 30 (MEDIUM confidence). Key risk: D scenario credit seizure (-10% to -4%) vs SGOV safety. Layer 4 neutral check: +0.93%.
emerging_market_equity: added v1.13 May 6. Scenario A ADOPTED HIGH confidence (v1.23 — REVISED [+4,+9]→[+10,+20]; L2: 1991 Gulf drawdown +15-20% real, 2003 Iraq drawdown +15-20% real, 2016 commodity rebound +10-15% real; 3 analogues. L3: VWO Taiwan/China 56.7% concentration depresses D/E conservative values; structural adj documented. L4: gap to institutional anchor +5.5% documented as (a)+(d); expected given VWO concentration vs blended EM unconditional). B-F PENDING June 30 (MEDIUM confidence). Layer 4 neutral check: −2.55% midpoints. Resolve at June 30. ⚠ floating_rate_credit_income C=[+1,+3]: flag for Q3 — may conflate nominal vs real return basis (2022 FLOT: −0.6% nominal ≈ −7% real at 8% CPI). Reconcile at Q3 audit.
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
| 2026-06-30 | Q2 first full audit | All calibration-dated thresholds; section 4 return table and multipliers; M14/M10/M15 thresholds; restore multipliers if commodity-linked added post-war; AIPO ThematicETF_ClassificationAudit — COMPLETE v1.14 (§11 revised; EV +2.16% at v1.19 probs; confirm at Q2 for weight drift); AIPO/PAVE ETN overlap check; MOVE index integration assessment — MOVE at 78.43 as of May 25 (elevated; formal threshold pending); MAGS vs AGIX reassessment if Anthropic IPO announced; secular_technology_growth empirical validation; formal adoption of §6 item 23 pending proposals; populate all PENDING §4.1 values (M16.CalibrationMethodology() 4-layer required for all MEDIUM/LOW confidence cells); resolve real_estate_equity_income leverage-adjusted calibration; COPX M07 regional ruling formal confirmation; URA full M07+M15 evaluation; SIVR+COPX entry guard 90d trailing price computation — CLEARED v1.14; DBMF D/E/F formal adoption; Brent C-trigger clock threshold review; PAVE IIJA reauthorization assessment (Sep 30 deadline approaching); M17 §12 first formal audit and threshold calibration; M18 allocation spreadsheet series gap resolution (add DGS10, DGS2, T10YIE, T5YIE, DXY, NASDAQ, DOW, Russell 2000 to spreadsheet tabs or Session Summary tab) |
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
23. RETURNS TABLE PENDING REVISION PROPOSALS (logged May 6, 2026). 10 of 14 confirmed proposals recovered; 4 unrecoverable due to file split at v1.12. Status as of June 1, 2026:

  ADOPTED (HIGH confidence, intra-session v1.25):
  - [6] rate_sensitive_income_short_duration A: [0,2]→[1,3] ★ ADOPTED
  - [7] rate_sensitive_income_short_duration D: [0,3]→[1,4] ★ ADOPTED
    (original proposals [1,4] and [2,6] rejected — Layer 3 duration constraint + Layer 4)

  ADOPTED (HIGH confidence, intra-session v1.26):
  - [9] real_asset_contracted_revenue D: [2,6]→[-6,+2] ★ ADOPTED (M16 4-layer complete)
  - [10] real_asset_contracted_revenue E: [2,5]→[-10,0] ★ ADOPTED (M16 4-layer complete)
    (Prior values [2,6] and [2,5] inconsistent with 2008 empirical data; AMZ -30% total real)

  ADOPTED HIGH confidence (intra-session v1.27):
  - [1] secular_technology_growth B: [-6,-1]→[-2,+4] ★ ADOPTED
      Q1 2026 contamination call REVERSED: Hormuz war does not affect rate/multiple mechanics
      defining B for secular tech. Q1 2026 (Azure +40%, AWS +28%, GCP +63%, FOMC 3.62%) IS
      valid sustained B analogue. 3 clean analogues confirmed. L4 +1.00% = exact anchor. HIGH.
  - [4] inflation_hedge_precious_metals A: [0,4]→[-2,+2] ★ ADOPTED
      Post-1980 anchor 2% real (excludes 1970s supercycle). 3 analogues (1996-99, 2013-15, 2016).
      War premium unwind at $3,300+ starting price. L4 -0.50% vs 2% anchor, gap -2.5pp. PASS.
  - [5] inflation_hedge_precious_metals D: [-2,4]→[-3,+3] ★ ADOPTED
      Same post-1980 anchor. 3 analogues (2008 flat, 2020 +25%, 1990-91 flat).
      War premium at elevated starting price reduces upside vs 2020. L4 same row. PASS.
  - [8] geopolitical_premium A: [-2,3]→[-4,+1] (revised from original [-6,0])
      Original [-6,0] rejected: fails L4 more severely than current values.
      Revised [-4,+1]: supported by post-Gulf War 1991 (-15% real) and Cold War dividend analogues,
      moderated by structural US/NATO defense budget increases and contractor backlog.
      L4 documented exception: geopolitical_premium inherently underperforms unconditional anchor
      in neutral distribution — acceptable given role definition (conflict-scenario premium only).
      BLOCKED: MEDIUM confidence (2 clean analogues). Adjudicate at June 30.

  PENDING June 30 (MEDIUM confidence — 1 clean analogue each; scenario duration now explicit):
  - [2] secular_technology_growth D: original [-20,-8] WRONG (calibrated to 1yr acute, not 2-3yr
      framework convention). REDERIVED: [-6,0]⚑.
      Basis: 2008-09 2yr annualized NDX: -41.7%+54.7% = -5.1% real. Contract lock-in adj → -6%
      conservative. Upside 0%: partial recovery in D year 2-3. 1 clean analogue → MEDIUM.
      L4 with STG B adopted: neutral-weighted ≈ +1.90% vs anchor 1%. Gap +0.9pp. PASS.
  - [3] secular_technology_growth E: original [-18,-6] recalibrated to [-12,-3]⚑.
      Basis: 2008 Q4 acute 6-12mo annualized. Shorter than D but more violent.
      1 clean analogue → MEDIUM. L4 with B adopted: neutral-weighted ≈ +1.70%. PASS.

  (IHP A and D moved to ADOPTED above — L4 resolved via post-1980 anchor recalibration.)

  UNRECOVERABLE (4 proposals — lost in v1.12 file split; reconstruct at June 30 audit):
  - [11]-[14]: Reference exists in prior v1.12 §6 item 23 but content not carried forward.
    Likely candidates: IHC Scenario A, RAC Scenario A, RSILD revision, geopolitical_premium C.
    Treat as open slots for June 30 audit — new proposals may supersede.
24. Implement living update protocol: now formally governed by M16_ReturnTableCalibration §5. Confirm June 30 as first formal application of M16 §5 LivingUpdateTriggers.
25. Session_Log.md compaction: retain last 10 §7 credit rows; collapse §8 to last 3 full entries + summary table. Move prior entries to Archive_2026Q2.md.
26. COPX M07 regional concentration ruling: confirm "region = political/economic bloc" ruling from v1.13 as formal framework policy. Apply consistently to all future M07 screens.
27. URA (Global X Uranium ETF): COMPLETE v1.22 (May 29, 2026). M07 PASS (foreign exposure flag; AUM $7.81B; ER 0.69%; Canada ~35-40% below 40% threshold). ThematicETF_ClassificationAudit COMPLETE. ComponentVector: RAC(0.50)+IHC(0.30)+STG(0.20). EV +4.17% (rank #3). Added to §11. Targets: Primary IRA 3%, Primary Roth 3%. Tax placement: retirement accounts only.
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
  - Competing proposal: [-12,-3] REJECTED (June 1, 2026): L4 sits -1.5pp below anchor on wrong side; L3 structurally ignores AI enterprise contract lock-in that did not exist in 2022 analogue. Not a viable proposal.
  - Confidence level: MEDIUM — 2 clean analogues (2022, 1973-82); Q1 2026 confirmed contaminated (C-dominant environment). HIGH requires 3+. BLOCKED intra-session.
  - June 30 adjudication: effectively [-2,+4] vs status quo [-6,-1]. [-12,-3] removed from table.
  - Q1 2026 data (Azure +40%, AWS +28%, GCP +63%, zero guidance withdrawals; Google backlog $460B QoQ near-double): strengthens L3 contract lock-in argument for [-2,+4]. Does not constitute clean B analogue — C-dominant environment contaminates. Still only 2 clean analogues.
  - Upgrade path to HIGH: Q2 2026 Mag7 earnings (reporting May-July 2026) with >25% revenue growth + zero guidance withdrawals in a confirmed B-shifting environment → 3rd data point → HIGH confidence eligible.
  - Current §4.1 B value [-6,-1] remains operative until June 30 adjudication.
36. GOOGLEFINANCE ticker setup (v1.17): New allocation spreadsheet tab added for market data "Other Indexes". Confirmed working: VIX (INDEXCBOE:VIX), S&P 500 (INDEXSP:.INX), MOVE (INDEXNYSEGIS:MOVE). FRED series: use existing spreadsheet "FRED Series" tab. BZ=F is canonical Brent reference for C-trigger clock per v1.17.
37. AI capex / secular_technology_growth context note (v1.18, May 22, 2026): Session intelligence — hyperscaler AI capex $660-830B committed for 2026 (nearly doubling 2025). Capex intensity 45-57% of revenue (vs 10-15% in 2020). Revenue growth 15-16% vs capex growth 60-80%; FCF projected to decline 90% across Big Four. Private credit ($800B+ in AI infrastructure financing) opacity flagged as tail risk not visible in HY/IG spread series. AI utility pricing emerging (62% usage-based by 2027). Prisoner's dilemma / war-of-attrition structure confirmed: no coordination mechanism among 5+ hyperscalers; 18-36 month infrastructure commitment periods prevent exit. Fiber optic 1999 analogy: technology correct, equity returns poor due to timing, cost of capital, and competitive dynamics. Portfolio implication: AIPO (infrastructure layer, contracted revenue) positive EV in B/C; MAGS (hyperscaler equity) negative EV in B/C — distinction maintained. No §4.1 changes warranted from session analysis.
38. M17 §12 thresholds (v1.19, corrected v1.20): First formal application May 25, 2026. sectorStressScore()=0 (formal, v1.20 corrected). CascadeLevel=MONITORING. CHAIN_3_WATCH=TRUE ($1.304T margin debt record loaded; FIRES on ≥−5% MoM or 3+ gate events). CHAIN_4 CALIBRATED v1.24 (June 1, 2026): canonical series = S&P Global large-company; T1-equivalent = ABI/Epiq AACER press releases; WATCH ≥220/quarter, FIRES ≥300/quarter (HIGH confidence, M16 4-layer complete); current Q1 2026 = 188/quarter — BELOW WATCH. Prior 800/quarter threshold eliminated. D=5% maintained by prior client approval (qualitative). Formal Q2 audit: calibrate remaining §12 thresholds; formal integration of yield curve D_timing_signal; M18 allocation spreadsheet series gap resolution.
39. M18 FMP data fetch (v1.21, May 26, 2026): FMP:chart historical-price-eod-light confirmed working for ^VIX and SPY. VIX_30D_AVG=17.99 and VIX_90D_AVG=21.24 computed from 62 trading days of FMP EOD data. SPY 30-trading-day return=+8.68% (Apr 13→May 22). FMP:indexes endpoint ACCESS DENIED for ^SPX (requires higher plan tier) — SPY via FMP:chart is the confirmed working substitute for BROAD_EQUITY_TRAILING. M18 updated accordingly (v1.1).

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

May 26 full session M14 computation (FMP data confirmed):
- VIX_change_90d_pts = 16.70 (May 22) − 17.93 (Feb 25) = −1.23 pts → ≤ 0 → commodity_fear_divergence = HIGH ✓
- energy_90d: BZ=F ~$97 (May 26) vs ~$70 (Feb 25 est.) → ~+39% → ≥ +15% → commodity_fear_divergence = HIGH ✓
- broad_equity_30d (SPY, 30 trading days): +8.68% (Apr 13→May 22) → ≥ +5% → equity_scenario_divergence = HIGH ✓
- Composite = HIGH (unchanged).
- UnderweightReviewTrigger: NOT fired (max drift = Relative Roth MLPX +1.71pp; all accounts below 5pp threshold).

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

### 9.4 MOVE Index Thresholds (M11/M14 Integration — added v1.22 May 29, 2026)

All thresholds CALIBRATION_DATED. Encoded at Q2 audit May 29, 2026. First formal audit: June 30, 2026.
Source: INDEXNYSEGIS:MOVE (GOOGLEFINANCE — allocation spreadsheet "Other Indexes" tab).

| Level | Signal | M11/M14 Action |
| --- | --- | --- |
| < 80 | NORMAL | No adjustment; standard credit protocol |
| 80–100 | ELEVATED | Flag in briefing; M14 divergence signal weight increases |
| 100–130 | STRESS | Active credit monitor; EntryExtensionGuard sensitivity increases; flag D precursor |
| > 130 | CRISIS | Formal M11 credit-stress contribution; D probability review triggered |
| > 160 | SYSTEMIC | D/E cascade active consideration |

Confidence: HIGH for 80 and 130 anchors (multiple historical regimes: 2008 peak ~265, 2020 ~160,
2022 LDI ~158, 2023 SVB ~120). MEDIUM for 100 (fewer distinct boundary observations).
Current (May 29, 2026): 70.22 — NORMAL zone. Retreating from 79.72 peak (May 22).
Calibration_Log baseline: first logged Apr 30 at 68.68 (T2); T1 confirmed May 11 at 70.74.

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
VTI, XAR, MLPX, SGOL, SGOV, PAVE added Apr 28 (v1.7). AIPO, MAGS added Apr 30 (v1.9). AIPO §11 data updated May 6 (v1.10). MLPX EV updated May 6 (v1.11). New roles inflation_linked_sovereign and real_estate_equity_income added May 6 (v1.12). Five new roles added May 6 (v1.13): systematic_trend_following, consumer_defensive_equity, healthcare_defensive_equity, floating_rate_credit_income, emerging_market_equity. New instruments added May 6 (v1.13): DBMF, SIVR, COPX, VTIP, XLP, VNQ, VEA, XLV, FLOT. AIPO reclassified May 7 (v1.14): ThematicETF_ClassificationAudit() COMPLETE. MLPX entry guards CLEARED May 13 (v1.17). Gold reallocation targets confirmed executed May 22 (v1.18). EVs updated at new probability vector May 25 (v1.19): A=7/B=36/C=41/D=5/E=4/F=7. SIVR EV arithmetic corrected May 26 (v1.21): B blended 5.70%→6.00%, total EV +2.92%→+3.03%.

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
| systematic_trend_following | multi_asset_price_trends, momentum_persistence, commodity_trend_signal, rates_trend_signal, currency_trend_signal | v1.13 May 6 | Active - A/B/C/D values ADOPTED HIGH confidence (D upgraded v1.22). E/F PENDING June 30. Instrument: DBMF. No entry extension guard. No K-1 risk. All accounts eligible. |
| consumer_defensive_equity | consumer_pricing_power, demand_inelasticity_essentials, household_consumption, brand_moat | v1.13 May 6 | Active - A/B/C values ADOPTED HIGH confidence (A and C upgraded v1.22; C revised [0,+4]→[+2,+6]). D/E/F PENDING June 30. Instrument: XLP. All accounts eligible (standard equity ETF). No entry extension guard. |
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
- Last reviewed: 2026-05-30 (v1.23 — staleness check complete; classification confirmed)
- ⚠ Valuation note: Forward P/E ~35.5x (war-premium elevated; within thesis range for geopolitical_premium; peacetime norm 18-22x. Watch for compression if A-probability rises above 20%. 66.59x trailing PE seen in some sources is a stale artifact — use forward PE only.)
- EV (A=7/B=36/C=41/D=5/E=4/F=7): **+1.46%**
  - A: (0.90×(-2)+0.10×5)×0.07 = -1.30×0.07 = -0.091%
  - B: (0.90×2+0.10×(-8))×0.36 = 1.00×0.36 = +0.360%
  - C: (0.90×4+0.10×(-4))×0.41 = 3.20×0.41 = +1.312%
  - D: (0.90×(-4)+0.10×(-12))×0.05 = -4.80×0.05 = -0.240%
  - E: (0.90×1+0.10×(-8))×0.04 = 0.10×0.04 = +0.004%
  - F: (0.90×1+0.10×7)×0.07 = 1.60×0.07 = +0.112%
  - Total: +1.457% ≈ +1.46%.
- Target: 12% structural across applicable accounts (Primary IRA, Primary Roth, Taxable Acc4). CONFIRMED AT TARGET.
- Client preference: exit excess XAR at ~$265 on a conflict-resumption spike. EXECUTED — reduction to 12% confirmed via allocation sheet May 6.
- HoldJustification: break-even peace probability <5.6%; opportunity cost vs MLPX -4.21%/year (at v1.19 probs).
- ⚠ Deal trajectory (A rising): geopolitical_premium A return proposed revision to [-6,0] pending June 30. If adopted, XAR EV would decline further.

#### MLPX
- Components: real_asset_contracted_revenue (0.65) + inflation_hedge_commodity_linked (0.35)
- Last reviewed: 2026-05-13 (v1.17 — entry guards CLEARED)
- EV (A=7/B=36/C=41/D=5/E=4/F=7): **+5.10%** (revised v1.26; prior: +5.67% — RAC D/E values corrected). Ranked #2.
  - A: (0.65×3+0.35×2)×0.07 = 2.65×0.07 = +0.186%
  - B: (0.65×6+0.35×6)×0.36 = 6.00×0.36 = +2.160%
  - C: (0.65×8+0.35×7)×0.41 = 7.65×0.41 = +3.137%
  - D: (0.65×(-6)+0.35×(-8))×0.05 = -6.70×0.05 = -0.335%
  - E: (0.65×(-10)+0.35×2)×0.04 = -5.80×0.04 = -0.232%
  - F: (0.65×3+0.35×2)×0.07 = 2.65×0.07 = +0.186%
  - Total: +5.102% ≈ +5.10%.
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
- EV (A=7/B=36/C=41/D=5/E=4/F=7): **+1.24%** (revised v1.29; IHP A=-2 and D=-3 adopted v1.27; §11 text corrected from stale +1.43%). Ranked #7.
  - A: (-2%)×0.07 = -0.140%  [IHP A=-2 adopted v1.27]
  - B: 6%×0.36 = +2.160%
  - C: (-2%)×0.41 = -0.820%
  - D: (-3%)×0.05 = -0.150%  [IHP D=-3 adopted v1.27]
  - E: 10%×0.04 = +0.400%
  - F: (-3%)×0.07 = -0.210%
  - Total: +1.240%.
- Target allocation (v1.18 CONFIRMED):
  - Primary IRA: 16%
  - Primary Roth: 14%
  - Relative IRA: 20% (CONFIRMED EXECUTED v1.18 — reduced from 26%)
  - Relative Roth: 16% (CONFIRMED EXECUTED v1.18 — reduced from 22%)
  - Note: SIVR added as complement; SGOL + SIVR combined restores precious metals exposure
- ⚠ IHP A and D proposals from prior sessions: ADOPTED v1.27 (A [-2,+2] ★; D [-3,+3] ★). §11 EV updated v1.29.

#### SGOV
- Components: rate_sensitive_income_short_duration (1.00)
- Last reviewed: 2026-06-01 (v1.25 — A and D values adopted HIGH confidence)
- EV (A=7/B=36/C=41/D=5/E=4/F=7): **+0.89%** (revised v1.25; prior: +0.76%). Ranked #9.
  - A: 1%×0.07=+0.070; B: 1%×0.36=+0.360; C: 1%×0.41=+0.410; D: 1%×0.05=+0.050; E: (-2%)×0.04=-0.080; F: 1%×0.07=+0.070
  - Total: +0.880% ≈ +0.89%.
- Target allocation (v1.13):
  - Primary Taxable: 15%
  - Taxable Preservation: 100%
  - Relative IRA: 14%
- ✅ A [0,2]→[1,3] ADOPTED HIGH confidence (v1.25). D [0,3]→[1,4] ADOPTED HIGH confidence (v1.25). Original proposals [1,4] and [2,6] rejected — see §4.1 footnote.

#### PAVE
- Components: broad_market_equity_domestic (0.82) + policy_driven_thematic_equity (0.18)
- ThematicETF_ClassificationAudit conducted Apr 28. Status: watch (not FLAGGED).
- Last reviewed: 2026-05-06 (status reconfirmed — no new legislation; IIJA core programs intact)
- Cost basis: $54.09/share. Current: ~$56.31 (May 30). Embedded gain: ~$1,111 on 502 shares. Target: ~11% in Taxable Acc4.
- **HOLD with explicit exit triggers (v1.23, May 30, 2026). Constituent-level analysis complete:**
  - Bucket A (~35-45% NAV) — INSULATED: Eaton (ETN), Trane Technologies, CSX, Union Pacific, Basic Materials (~19%). Revenue driven by private capex, freight volume, data center buildout, reshoring. IIJA expiration impact: LOW.
  - Bucket B (~30-40% NAV) — PARTIAL: Quanta Services (~60% utility/grid revenue, not highway), E&C firms with multi-year backlogs. Backlog insulates 12-24 months. IIJA expiration impact: MODERATE, LAGGED.
  - Bucket C (~20-25% NAV) — AT-RISK: Highway/bridge formula contractors. Formula funding reverts from ~$66B/yr to ~$46B/yr on hard expiration. Discretionary grants (BUILD, RAISE, PROTECT) cease new awards immediately. IIJA expiration impact: MATERIAL, NEAR-TERM.
  - Modal congressional outcome: short-term extension at some level (historical base rate ~1/3 of cycles since 1991). Not a clean resolution — slows new award activity even if funding continues.
  - PDT 18% weight may OVERSTATE IIJA dependency: Bucket A/B largest holdings are not mandate-driven. Reduces both risk and the hold thesis (PDT A upside).
- **EXIT TRIGGERS (any one fires → exit at next rebalancing):**
  1. CPI mid-June ≥4.0% → B formal trigger fires. B scenario = worst simultaneous outcome for Bucket C + domestic equity compression.
  2. No congressional action of any kind on IIJA by August 15, 2026 (6 weeks before expiration). Hard lapse or panic extension becomes modal; get ahead of construction firm re-rating.
  3. IIJA extension or new bill passed at REDUCED funding levels. Bucket C mandate impairment confirmed.
  4. CascadeLevel reaches ALERT (sectorStressScore ≥2). M17 §12 FLAGGED instrument exit window protocol.
- **HOLD CONDITIONS (reassess before any exit):**
  - Iran deal T1 confirmed → A-probability rises to ≥20%: Bucket A/B (Eaton, Trane, CSX, UP, Basic Materials) benefit materially from A-scenario reflation; IIJA reauthorization odds also improve.
  - IIJA short-term extension at current levels: acute cliff risk removed; continue monitoring.
- EV (A=7/B=36/C=41/D=5/E=4/F=7): **−4.03%**. EV unchanged; IIJA risk partially embedded in PDT B/C values.
  - A: (0.82×5+0.18×4)×0.07 = 4.82×0.07 = +0.337%
  - B: (0.82×(-8)+0.18×(-3))×0.36 = -7.10×0.36 = -2.556%
  - C: (0.82×(-4)+0.18×(-1))×0.41 = -3.46×0.41 = -1.419%
  - D: (0.82×(-12)+0.18×(-5))×0.05 = -10.74×0.05 = -0.537%
  - E: (0.82×(-8)+0.18×(-6))×0.04 = -7.64×0.04 = -0.306%
  - F: (0.82×7+0.18×4)×0.07 = 6.46×0.07 = +0.452%
  - Total: -4.029% ≈ −4.03%.
- Monitor IIJA reauthorization September 30, 2026.

#### AIPO
- Components: policy_driven_thematic_equity (0.63) + secular_technology_growth (0.16) + real_asset_contracted_revenue (0.14) + inflation_hedge_commodity_linked (0.07)
- CLASSIFICATION REVISED v1.23 (May 30, 2026): Sector drift confirmed via T1 data (Yahoo Finance May 30). Prior v1.14 weights (RAC 0.45, STG 0.30, PDT 0.20, IHC 0.05) reflected May 7 holdings (Industrials 50%, IT 30%, Utilities 20%). Current holdings: Industrials 57.09%, Technology 16.46%, Utilities 14.42%, Energy 6.91%, FinSvcs 3.60%. STG drift −13.5pp; Industrials +7pp — both exceed 5pp threshold. New weights: PDT 0.63 (infra/power mandate: PWR, GEV, ETN, VRT, MasTec), STG 0.16 (AI hardware: NVDA 3.54%, AVGO 4.03%), RAC 0.14 (utilities/power gen: CEG, BE), IHC 0.07 (energy: Cameco + other). FinSvcs 3.60% residual assigned to dominant PDT. Prior v1.14 classification: ThematicETF_ClassificationAudit() COMPLETE May 7, 2026.
- Basis: Defiance AI & Power Infrastructure ETF. Tracks MarketVector US Listed AI & Power Infrastructure Index. Holdings must derive ≥50% revenue from AI hardware, data centers, or power infrastructure. 78 holdings as of May 30, 2026. AUM: ~$434M (growing rapidly — was $100M Jan 2026). Expense ratio: 0.69%. Inception: 07/24/2025 (thin track record — flag at Q2).
- ⚠ NVDA/AVGO overlap with MAGS: NVDA 3.54% + AVGO 4.03% in AIPO → ~0.6-0.9% portfolio combined with MAGS contribution. Not material. Monitor.
- ⚠ PAVE overlap: ETN (Eaton) ~8% of AIPO + ~3-5% of PAVE → ~1.1% portfolio combined. IMMATERIAL (confirmed May 30).
- ✅ TRACK RECORD FLAG SUBSTANTIALLY CLOSED (v1.28, June 1, 2026): AUM $732.94M (as of June 1, 2026 — up from $434M at May 30; crossed $100M Jan 26, $200M Mar 26, $300M Apr 17, $500M May 5). Named Best New Thematic ETF at 2026 ETF.com Awards (March 9, 2026). 12-month track record milestone: July 24, 2026 (~7.5 weeks). AUM and recognition concerns fully resolved. Confirm formal 12-month track record at Q2 audit June 30.
- Last reviewed: 2026-05-30 (v1.23 — ThematicETF_ClassificationAudit weight drift update)
- EV (A=7/B=36/C=41/D=5/E=4/F=7): **+0.13%** (revised v1.27; STG B=-2, RAC D=-6, RAC E=-10 incorporated). Ranked ~#10.
  - A:  (0.63×4 + 0.16×6 + 0.14×3 + 0.07×2) = 4.04% × 0.07 = +0.283%
  - B:  (0.63×(-3) + 0.16×(-2) + 0.14×6 + 0.07×6) = -0.95% × 0.36 = -0.342%
  - C:  (0.63×(-1) + 0.16×2 + 0.14×8 + 0.07×7) = 1.30% × 0.41 = +0.533%
  - D:  (0.63×(-5) + 0.16×(-14) + 0.14×(-6) + 0.07×(-8)) = -6.79% × 0.05 = -0.340%
  - E:  (0.63×(-6) + 0.16×(-10) + 0.14×(-10) + 0.07×2) = -6.64% × 0.04 = -0.266%
  - F:  (0.63×4 + 0.16×4 + 0.14×3 + 0.07×2) = 3.72% × 0.07 = +0.260%
  - Total: +0.128% ≈ +0.13%
  - ⚠ EV still near-zero. Hold justified by: (a) C-scenario infrastructure thesis; (b) A upside.
    Further improvement expected if STG D/E adopted at June 30 (D component currently using -14).
  - ⚠ EV ALERT: reclassification moves AIPO from +2.16% to near-zero. PDT B/C (−3%/−1%) now dominant (63% weight). B contribution alone = −0.572% drag. C contribution +0.533% partially offsets. AIPO hold justified by: (a) C-scenario energy/infrastructure thesis; (b) A-scenario upside (+0.283%); (c) no superior replacement for AI power infrastructure exposure. Review targets at June 30 — EV differential vs URA (+4.17%) and MLPX (+5.67%) now larger.
  - ⚠ FEASIBILITY CHECK REQUIRED: reduced EV may affect Primary IRA/Roth feasibility. Run M13.FeasibilityCheck() at next full session with updated AIPO contribution.
- TAX PLACEMENT: ALL ACCOUNTS including taxable.
- Target allocation (v1.22): **7% Primary IRA; 7% Primary Roth**; 8% Primary Taxable; 6% Relative IRA; 10% Relative Roth.
- ⚠️ TARGET REVIEW IN PROGRESS (v1.29, June 2, 2026): Proposed IRA 7%→3%, Roth 7%→3%; DBMF
  IRA 15%→19%, Roth 17%→21% (4pp freed per account → DBMF). EV +2.16% (v1.22) → +0.13% (v1.27)
  following reclassification to PDT-dominant. EV improvement per account ~+0.44pp/year. Client
  deliberating. Allocation sheet unchanged pending client confirmation. C-scenario infrastructure
  thesis validated June 2 (+3.59% on Iran energy escalation). IRA overall gain +$1,027.67 (+5.08%).

#### MAGS
- Components: secular_technology_growth (0.85) + broad_market_equity_domestic (0.15)
- Last reviewed: 2026-05-30 (v1.23 — hold-only override confirmed)
- ⚠ EV deterioration: from −1.77% (C=44, D=3) to −2.17% (C=41, D=5). D scenario deeply negative (−13.70% blended) — increasing D weight amplifies drag. Override remains in force but EV trendline is worsening.
- **HOLD-ONLY OVERRIDE CONFIRMED (v1.23, May 30, 2026): No ADD at EV −2.17%. Override justified solely by absence of positive-EV secular_technology_growth alternative (URA covers RAC/IHC/STG partially; application-layer gap remains unresolved). Revisit if secular_technology_growth B adjudication at June 30 produces a materially different B conservative value.**
- EV (A=7/B=36/C=41/D=5/E=4/F=7): approximately **−0.94%** (revised v1.27; STG B=-2 adopted). Ranked #10.
  - A:  (0.85×6+0.15×5)×0.07 = 5.85×0.07 = +0.410%
  - B:  (0.85×(-2)+0.15×(-8))×0.36 = -2.90×0.36 = -1.044%
  - C:  (0.85×2+0.15×(-4))×0.41 = 1.10×0.41 = +0.451%
  - D:  (0.85×(-14)+0.15×(-12))×0.05 = -13.70×0.05 = -0.685%  // operative STG D=-14 (⚑ rederived -6 not yet adopted)
  - E:  (0.85×(-10)+0.15×(-8))×0.04 = -9.70×0.04 = -0.388%  // operative STG E=-10 (⚑ rederived -12 not yet adopted)
  - F:  (0.85×4+0.15×7)×0.07 = 4.45×0.07 = +0.312%
  - Total: −0.942% ≈ −0.94%
  - NOTE: STG B adoption improves MAGS EV from −2.17% to −0.94%. HOLD-only override basis
    partially changes: EV is now −0.94% (below zero but less negative). Override remains in
    force — still negative EV; no secular_technology_growth positive-EV alternative confirmed.
    Revisit at June 30 if STG D/E adoption further affects ranking.
- Target allocation (v1.22): **3% Primary IRA; 4% Primary Roth**; 3% Relative IRA; 8% Relative Roth. (Reduced v1.22 to fund URA addition; EV improvement +0.04pp per account.)
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
- Last reviewed: 2026-05-26 (v1.21 — B-component arithmetic corrected)
- EV (A=7/B=36/C=41/D=5/E=4/F=7): **+2.93%** (revised v1.29; IHP A=-2 and D=-3 from v1.27 now applied). Ranked #4.
  - A:  (0.55×(-2) + 0.45×2) = -0.20% × 0.07 = -0.014%  [IHP A=-2 adopted v1.27]
  - B:  (0.55×6 + 0.45×6) = 6.00% × 0.36 = +2.160%  [unchanged]
  - C:  (0.55×(-2) + 0.45×7) = 2.05% × 0.41 = +0.841%  [unchanged]
  - D:  (0.55×(-3) + 0.45×(-8)) = -5.25% × 0.05 = -0.263%  [IHP D=-3 adopted v1.27]
  - E:  (0.55×10 + 0.45×2) = 6.40% × 0.04 = +0.256%  [unchanged]
  - F:  (0.55×(-3) + 0.45×2) = -0.75% × 0.07 = -0.053%  [unchanged]
  - Total: +2.927% ≈ +2.93%.
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
- ENTRY EXTENSION GUARD: CLEARED (v1.14, May 7, 2026) at $83.35. 90d avg ~$85-90; threshold ~$102-106.
  ⚠️ Price update (v1.29, June 2, 2026): COPX closed **$93.66** (+4.00%). 90d reference window has shifted
  (now March 3–June 2). Original clearing is stale for ADD purposes — must recompute 90d trailing avg from
  T1 price data before any ADD. No ADD planned; at target (2% IRA, 7% Taxable).
- Target allocation (v1.13): 2% Primary IRA; 7% Primary Taxable.

#### VTIP
- Components: inflation_linked_sovereign (1.00)
- Basis: Vanguard Short-Term Inflation-Protected Securities ETF. AUM: $66.6B. Expense ratio: 0.03%. Beta: 0.22.
- Last reviewed: 2026-06-01 (v1.28 — A/D/F adopted HIGH confidence; B/C/E remain MEDIUM)
- EV (A=7/B=36/C=41/D=5/E=4/F=7): **+0.52%** (unchanged — values same as prior ⚑; status upgrade only).
  - A: -2%×0.07=-0.140 ★; B: 1%×0.36=+0.360 ⚑; C: 1%×0.41=+0.410 ⚑; D: 0%×0.05=0 ★; E: -1%×0.04=-0.040 ⚑; F: -1%×0.07=-0.070 ★
  - Total: +0.520%. Values unchanged — A/D/F confidence upgraded to HIGH (★); B/C/E remain MEDIUM (⚑).
- TAX PLACEMENT: RETIREMENT ACCOUNTS ONLY. Inflation accrual on TIPS taxed as ordinary income annually.
- ENTRY EXTENSION GUARD: N/A.
- Target allocation (v1.13): 8% Primary IRA; 10% Primary Roth; 12% Relative IRA; 10% Relative Roth.

#### XLP
- Components: consumer_defensive_equity (1.00)
- Basis: State Street Consumer Staples Select Sector SPDR ETF. AUM: $14.5B. Expense ratio: 0.08%. 100% US domestic.
- Last reviewed: 2026-05-06 (v1.13, initial classification)
- EV (A=7/B=36/C=41/D=5/E=4/F=7): **+0.76%** (corrected v1.28; prior +0.14% used C=0 — bug; C was adopted at +2 in v1.22). Ranked #8.
  - A: 0%×0.07=0; B: 2%×0.36=+0.720; C: 2%×0.41=+0.820; D: -5%×0.05=-0.250; E: -8%×0.04=-0.320; F: -3%×0.07=-0.210
  - Total: +0.760%.
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

#### URA
- Components: real_asset_contracted_revenue (0.50) + inflation_hedge_commodity_linked (0.30) + secular_technology_growth (0.20)
- Basis: Global X Uranium ETF. Tracks Solactive Global Uranium & Nuclear Components Total Return Index.
  57 holdings; top 10 = 64.85% of fund. Includes uranium miners + nuclear components manufacturers.
- AUM: $7.81B. Expense ratio: 0.69%. Inception: ~2010 (long track record ✓).
- M07 STATUS: PASS. ER 0.69% < 1.0% ✓. AUM $7.81B ✓. Equity ETF (not leveraged) ✓. 1099 ✓.
  ⚠ Foreign exposure ~60% (Cameco Canada, Kazatomprom ADR, NexGen, Paladin Australia) →
  RETIREMENT ACCOUNTS ONLY (foreign dividend withholding reclaim issues in taxable).
  Canada ~35-40% — below 40% single-country threshold per v1.13 regional ruling ✓.
- ThematicETF_ClassificationAudit: COMPLETE May 29, 2026. Nuclear/AI demand thesis valid.
  AI hyperscaler nuclear PPAs (Microsoft/Constellation, Amazon/Talen, Google/Kairos) = structural
  secular demand driver independent of Hormuz war resolution. Uranium supply structurally tight
  (Kazatomprom delays, Niger cutoff). Thesis durable 3-5yr. SimplicityTest: PASS.
- Last reviewed: 2026-05-29 (v1.22 — initial classification)
- EV (A=7/B=36/C=41/D=5/E=4/F=7): **+4.02%** (revised v1.29; RAC D=-6/E=-10 from v1.26 and STG B=-2 from v1.27 now applied). Ranked #3.
  - A:  (0.50×3 + 0.30×2 + 0.20×6)  = 3.30% × 0.07 = +0.231%  [unchanged]
  - B:  (0.50×6 + 0.30×6 + 0.20×(-2)) = 4.40% × 0.36 = +1.584%  [STG B=-2 adopted v1.27]
  - C:  (0.50×8 + 0.30×7 + 0.20×2)  = 6.50% × 0.41 = +2.665%  [unchanged]
  - D:  (0.50×(-6) + 0.30×(-8) + 0.20×(-14)) = -8.20% × 0.05 = -0.410%  [RAC D=-6 adopted v1.26]
  - E:  (0.50×(-10) + 0.30×2 + 0.20×(-10)) = -6.40% × 0.04 = -0.256%  [RAC E=-10 adopted v1.26]
  - F:  (0.50×3 + 0.30×2 + 0.20×4)  = 2.90% × 0.07 = +0.203%  [unchanged]
  - Total: +4.017% ≈ +4.02%
- TAX PLACEMENT: RETIREMENT ACCOUNTS ONLY (IRA, Roth IRA). Taxable excluded — foreign exposure.
- ENTRY EXTENSION GUARD: **CLEARED (v1.29, June 2, 2026).** 90d trailing avg: **$51.71** (63 trading days
  March 3–June 1, 2026; T2 FinancialContent/Investing.com). Threshold (20% above avg): **$62.05**.
  Current: ~$50.76 (May 29 T2). $50.76 < $62.05. Safety margin: $11.29 (18.2% below trigger).
  ADD eligible: RETIREMENT ACCOUNTS ONLY.
- Target allocation (v1.22):
  - Primary IRA: 3%
  - Primary Roth: 3%
  - Relative accounts: out of scope (not requested)

---

## Consolidated Target Allocations (v1.22, May 29, 2026 — URA added; MAGS/AIPO targets revised; EVs at A=7/B=36/C=41/D=5/E=4/F=7)

| Instrument | Primary IRA | Primary Roth | Primary Taxable | Taxable Pres. | Relative IRA | Relative Roth |
| --- | --- | --- | --- | --- | --- | --- |
| MLPX | 30% | 28% | 30% | — | 24% | 32% |
| DBMF | 15% | 17% | 10% | — | 15% | 20% |
| SGOL | 16% | 14% | — | — | 20% | 16% |
| VTIP | 8% | 10% | — | — | 12% | 10% |
| AIPO | 7% | 7% | 8% | — | 6% | 10% |
| XAR | 12% | 12% | 12% | — | — | — |
| SGOV | — | — | 15% | 100% | 14% | — |
| SIVR | 4% | 5% | — | — | 6% | 4% |
| COPX | 2% | — | 7% | — | — | — |
| MAGS | 3% | 4% | — | — | 3% | 8% |
| XLP | — | — | 7% | — | — | — |
| PAVE | — | — | 11% | — | — | — |
| URA | 3% | 3% | — | — | — | — |
| **Total** | **100%** | **100%** | **100%** | **100%** | **100%** | **100%** |

Portfolio EV by account (v1.22 targets, A=7/B=36/C=41/D=5/E=4/F=7 — updated v1.27: STG B=-2, IHP A=-2, IHP D=-3):
- Primary IRA: **+3.88%** (required ~3.38% ✅ +0.50pp; MAGS +1.23pp×3% and SGOL −0.19pp×16% roughly offset)
- Primary Roth: **+3.95%** (required ~3.05% ✅ +0.90pp; MAGS 4% weight captures more of +1.23pp MAGS improvement)
- Primary Taxable: **+2.88%** (RETURN_THEN_TARGET 5yr ✅; negligible AIPO impact)
- Taxable Preservation: Capital preservation — SGOV 100% ✅ (SGOV EV +0.89% unchanged)
- Relative IRA: **+3.58%** (FLOOR_THEN_RETURN ✅; MAGS +1.23pp×3% ≈ offsets SGOL −0.19pp×20%)
- Relative Roth: **+4.35%** (required ~3.05% ✅; MAGS 8% weight captures +0.10pp net improvement)
- NOTE: All accounts feasible. IRA gap stable at +0.50pp. If STG D/E adopted at June 30, recompute
  (STG component in MAGS 85%, AIPO 16% — D/E adoption will further affect those instruments).

---

## Section 12 - M17 Systemic Cascade Warning Thresholds

Governing module: M17_SystemicCascadeWarning.md (v1.1, added May 25, 2026; PR #14 and #15 merged to master).
First formal application: May 25, 2026 (research/dev session). sectorStressScore()=0 (formal, v1.20 corrected), CascadeLevel=MONITORING.
All values CALIBRATION_DATED. First audit: June 30, 2026.

### 12.1 Agriculture / Fertilizer Chain

| Parameter | Alert Threshold | Notes |
| --- | --- | --- |
| farm_filings_alert | +50% YoY farm chapter 12 bankruptcies | Current (May 25): +46% YoY (USDA quarterly). Below threshold. CHAIN_1 NOT fired. |
| natgas_alert | $6.00/mmBtu sustained 30 days | Current (May 26): $2.71–$2.85 (futures). Well below threshold. CHAIN_1 NOT fired. |
| fertilizer_alert | +50% above 12-month average | Hormuz → Iranian urea exports disrupted → structural food CPI floor. Monitor. |

### 12.2 CRE / Regional Bank Chain

| Parameter | Alert Threshold | Notes |
| --- | --- | --- |
| KRE_alert | KRE −15% vs SPX over 90 days | Current: KRE $69.37 (May 22). Not fired. CHAIN_2 NOT fired. |
| SOFR_DFF_alert | SOFR–DFF spread +10 bp sustained 5 days | Current: −11 bp (normal). CHAIN_2 NOT fired. |

### 12.3 Private Credit / Margin Chain (two-mode — v1.20)

| Mode | Parameter | Threshold | Score | Current Status |
| --- | --- | --- | --- | --- |
| **WATCH** | margin_at_nominal_record | FINRA margin debt at all-time nominal high | 0 (precursor loaded; not firing) | **WATCH: $1.304T Apr 2026 all-time record. MoM was +6.8% (rising to record).** |
| **FIRES** | margin_MoM_decline | ≤ −5% MoM after record high | +1 | NOT fired. Watch for reversal month. |
| **FIRES** | gate_count_alert | 3+ named fund gate/suspension events in 90 days | +1 (OR with above) | NOT fired. 2 events observed (BlackRock CLO OC breach; Blue Owl gate). |

Design rationale: record high = leveraged stack maximally loaded (WATCH).
The −5% decline = cascade onset, forced selling begins (FIRES). Two separate signals.
CHAIN_3_WATCH surfaces in briefing watch_chains field regardless of formal score.

### 12.4 Manufacturing / Corporate Stress Chain

**Canonical data source (v1.24, June 1, 2026):** S&P Global Market Intelligence large-company series.
Scope: public companies with public debt and assets/liabilities ≥$2M, OR private companies with assets/liabilities ≥$10M at time of filing.
**T1-equivalent source:** ABI monthly/quarterly press releases citing Epiq AACER data. Direct AACER/PACER database access not required — ABI/Epiq AACER press releases qualify as T1-equivalent for CHAIN_4 scoring.

Historical reference (S&P series, quarterly rates):
- Normal baseline (2022-2023): ~90-120/quarter
- Elevated/stress-adjacent (2024-2026): ~170-200/quarter
- Post-GFC aftermath (2010): ~207/quarter
- GFC acute peak (2009): ~459/quarter (empirical ceiling on record)

| Parameter | Alert Threshold | Confidence | Notes |
| --- | --- | --- | --- |
| bankruptcy_quarterly_WATCH | ≥220/quarter | HIGH ★ | Above post-GFC 2010 level; stress regime confirmed. M16 4-layer complete June 1, 2026. |
| bankruptcy_quarterly_FIRES | ≥300/quarter | HIGH ★ | ~65% of GFC peak; systemic cascade signal. Fires CHAIN_4 score (+1). M16 4-layer complete June 1, 2026. |

Current (Q1 2026): 188/quarter (S&P Global, large-company) — BELOW WATCH threshold. CHAIN_4 NOT fired.
Prior threshold of 800/quarter ELIMINATED — was undocumented, lacked M16 basis, and exceeded the empirical GFC peak (~459/quarter) by ~74%. Would never have fired under any observed historical scenario.

### 12.5 Sovereign Stress / Scenario E Watch

| Parameter | Alert Threshold | Notes |
| --- | --- | --- |
| E_term_premium_warning | THREEFYTP10 ≥ 100 bp | Warning threshold. Current: 0.8117% (May 15) — 14-yr high, rising. Below warning (~19bp gap). |
| E_term_premium_alert | THREEFYTP10 ≥ 150 bp | Alert threshold. Not reached. |
| E_30Y_warning | 30Y Treasury yield ≥ 5.50% | Current: 5.07% (May 22). Below warning (~43bp gap). Approaching. |

### 12.6 Municipal Chain

Qualitative monitoring only. No formal threshold until June 30 audit.

### 12.7 Yield Curve Signal

| Parameter | Threshold | Notes |
| --- | --- | --- |
| inversion_threshold | −50 bp (10Y–2Y or 10Y–3M) | For valid inversion preceding re-steepening |
| resteepening_min_inversion | 3 months sustained inversion | Minimum duration before re-steepening counts as D_timing_signal |
| steep_threshold | +100 bp | Re-steepening above this = STEEP (recession-onset confirmed) |

Current (May 26): 10Y–2Y = +43 bp; 10Y–3M = +88 bp. Post-inversion re-steepening confirmed (prior inversion sustained >3 months). D_timing_signal = RECESSION_ONSET_PATTERN. Historical precedent: recession onset 5/6 occurrences after inversion + re-steepening pattern.

### 12.8 Composite Cascade Signal

sectorStressScore() — sum of fired CHAIN indicators:

| Chain | Status | Score |
| --- | --- | --- |
| CHAIN_1 (Agriculture) | NOT fired (+46% vs +50% threshold; natgas $2.71 vs $6) | 0 |
| CHAIN_2 (CRE/RegBank) | NOT fired (SOFR-DFF benign; KRE stable) | 0 |
| CHAIN_3 (Private/Margin) | WATCH — record loaded; FIRES conditions NOT met (MoM +6.8%, gate count 2/3) | 0 |
| CHAIN_4 (Manufacturing) | NOT fired. Q1 2026: 188/quarter vs WATCH ≥220 / FIRES ≥300 (v1.24). ABI/Epiq AACER T1-equivalent confirmed. | 0 |
| **Total** | | **0** |

CascadeLevel mapping:

| Score | Level |
| --- | --- |
| 0 | MONITORING |
| 1 | WATCH |
| 2 | ALERT |
| 3 | WARNING |
| 4 | CRITICAL |

**Current CascadeLevel: MONITORING** (sectorStressScore = 0; v1.20 corrected from erroneous ALERT in v1.19)

D_precursor_binding = sectorStressScore only (= 0 formal)

The yield curve D_timing_signal (RECESSION_ONSET_PATTERN) is an informational timing
estimate — it informs when D might arrive and the urgency of pre-positioning review.
It does NOT add numerically to D_precursor_binding. Adding it would conflate two
distinct concepts: precursor accumulation (what sectorStressScore measures) and
timing pattern (what the yield curve measures). They feed different analytical layers.

D_precursor_binding (May 26, v1.21): 0 (formal sectorStressScore = 0)
D=5% maintained by client approval from prior session (qualitative basis). Revisit Q2 audit.

Integration with M03.DeriveScenarioProbabilities():
- D_precursor_binding is a supplementary overlay — does NOT replace M11 formal trigger thresholds
- CascadeLevel WATCH: no adjustment
- CascadeLevel ALERT: add +1–2 pp to D raw score (proportional to binding count)
- CascadeLevel WARNING: add +3–4 pp
- CascadeLevel CRITICAL: add +5+ pp
- M11 formal D triggers (HY +300 bps, unemployment +0.5%, GDP negative) remain hard gates for large D moves

Integration with M08 execution (portfolio actions):
- CascadeLevel ALERT: activates M17 §5 exit window review for FLAGGED instruments (PAVE)
- CascadeLevel WARNING: triggers M10 D-response pre-positioning review
- CascadeLevel CRITICAL: invokes M10 Scenario D execution protocol
