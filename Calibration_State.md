# Calibration State

Persistent framework configuration — load at every session start alongside Session Log.

# Version: 1.51  Last updated: July 3, 2026. v1.50: same-day coding session —
ENG-45 CLOSED, §1.3 gained a new calibration-dated parameter (Minimum
absolute CCC move / ratio gate, 75 bps); ratio-row note updated to reflect
enforcement is live in credit.py. v1.51: DBMF §13 Thesis Sustaining Condition
first formal evaluation — DEGRADED (Condition 1, B+C>=55%, NOT MET at actual
48.5%; Condition 2 met at the margin). §4.1 B/C values NOT revised — see §3
2026-07-03. RSP EV refreshed live (-0.87% -> +1.11%, BMED-A-adoption driven,
NOT ADOPTABLE conclusion unchanged) — see §3 2026-07-03.

(Prior: v1.48 broad_market_equity_domestic Scenario A ADOPTED [5,12]->[10,20]
— HIGH confidence, 1991/2003 analogs T1-verified, client-confirmed; §6 item
23[16] -> ADOPTED. Scenario C: 2003 Iraq analog run, conservative bound HELD
unresolved by client decision, no value change — see §6 item 42 and §3
2026-06-30. v1.49: §1 credit Batch A audit executed — trailing-180d medians
computed (HY 283 / IG 78 / CCC 935 bps) and recorded in §1; HY/IG stress/
recession/transmission deltas RETAINED, not re-verifiable (FRED truncated OAS
history to a rolling 3y window — ENG-43); §1.3 CCC ratio-mode false-positive
found (CCC+29/HY+8 -> 3.62x fires on noise), gate pending ENG-45. Opened
FRAMEWORK_BACKLOG ENG-42/43/44/45. Full detail: Calibration_Log.md.)

**File split as of v1.12:**
- Session observations (§7) and session state (§8) now live in **Session_Log.md** (fetched concurrently at session start).
- Prior calibration history before last-10 entries lives in **Calibration_Log.md**.
- This file (Calibration_State.md) is the LIVE CONFIG — kept lean for reliable write-back.

---

## Load Verification Requirement

At session start, after both files are fetched, the advisor must state in the briefing:

"Calibration State loaded, last update: July 3, 2026 | Session Log loaded"

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
| HY_STRESS_DELTA | +150 bps | Calibration-dated | Audited 2026-06-30: RETAINED. Not re-verifiable — FRED truncated OAS history to 3y (ENG-43); vs the available 3y the trigger (median+150 = 433 bps) sits at ~97.7th pct, above the intended 75-90th band. That is an artifact of a benign 3y window missing the 2008/2020 tails, not a miscalibration. See §6 Batch A. |
| HY_RECESSION_DELTA | +300 bps | Calibration-dated | Audited 2026-06-30: RETAINED. Trigger (median+300 = 583 bps) exceeds the entire available 3y range — appropriate for a recession trigger in a non-recessionary window; not re-verifiable without full-cycle data (ENG-43). |
| Velocity overlay | +100 bps over prior 60 days | Fixed structural | Not calibration-dated |
| Sustain period | 10 trading days | Fixed structural | Not calibration-dated |
| D-floor on recession-pricing trigger | 25% | Fixed structural | Not calibration-dated |

Baseline snapshot at instantiation (April 19, 2026): ~285 bps. Trailing 180d median COMPUTED 2026-06-30 (Q2 audit, via framework fred_fetcher REST API): 283 bps (n=131 obs; current 280 bps). 3y percentiles p10/25/75/90 = 272/285/340/392 bps; 3y range 259-461. Detail: §6 Batch A.
Latest reading (Session_Log.md §7): see most recent §7 row.

### 1.2 IG Composite - FRED: BAMLC0A0CM

| Parameter | Current Value | Type | Notes |
| --- | --- | --- | --- |
| IG_TRANSMISSION_DELTA | +60 bps | Calibration-dated | Audited 2026-06-30: RETAINED. Trigger (median+60 = 138 bps) exceeds the available 3y max (133 bps); not re-verifiable vs FRED's truncated 3y history (ENG-43). See §6 Batch A. |
| Velocity overlay | +40 bps over prior 60 days | Fixed structural | Not calibration-dated |
| Sustain period | 10 trading days | Fixed structural | Not calibration-dated |

Baseline: Trailing 180d median COMPUTED 2026-06-30 (Q2 audit, via framework fred_fetcher REST API): 78 bps (n=131 obs; current 76 bps). 3y percentiles p10/25/75/90 = 77/80/100/122 bps; 3y range 73-133. Detail: §6 Batch A.
Latest reading (Session_Log.md §7): see most recent §7 row.

### 1.3 CCC Tail - FRED: BAMLH0A3HYC

| Parameter | Current Value | Type | Notes |
| --- | --- | --- | --- |
| Ratio divergence | CCC widens 3x composite over 30d | Fixed structural | Audit 2026-06-30: gated behind the minimum-absolute-CCC-move row below — else false-positives when HY is near-flat (CCC+29/HY+8 bps -> 3.62x fires on noise). Enforcement done, FRAMEWORK_BACKLOG ENG-45 (credit.py ratio_met). |
| Minimum absolute CCC move (ratio gate) | 75 bps | Calibration-dated | Added 2026-06-30, ENG-45. Ratio mode only fires if CCC's own 30d move also clears this floor — below the +200 absolute-stress floor, above the 2026-06-30 noise reading (+29 bps). Chosen at the low end of the ~75-100 bps suggested range so existing genuine-divergence readings (e.g. +100 bps) still fire. |
| Absolute divergence floor | CCC +200 bps while composite +<50 bps over 30d | Calibration-dated | Audited 2026-06-30: value retained (correctly did NOT fire at +29 bps). The audit's finding is on the ratio row above, not this one. See §6 Batch A. |

Latest reading (Session_Log.md §7): see most recent §7 row. CCC divergence watch: active since May 2026 (quiet re-widening while HY tightening). 2026-06-30 audit: CCC 967 bps (above its own trailing-180d median 935, near 180d p90 975), CCC +29 bps/30d vs HY composite +8 bps/30d. Ratio mode would fire (3.62x) but that is a compressed-regime false-positive; absolute floor correctly does not fire. No genuine threshold fires. Detail: §6 Batch A + ENG-45.

---

## Section 2 - Other Calibration-Dated Thresholds

### 2.1 Energy / Commodities

| Threshold | Current Value | Source | Audit Status |
| --- | --- | --- | --- |
| WTI floor - SGOL invalidation | $55 nominal OR 30% below 90d trailing WTI avg | Calibration-dated | Pending June 30 |
| Brent trigger - Scenario C | $110 nominal OR 40% above 90d trailing Brent avg | Calibration-dated | Pending June 30 |
| Brent invalidation - Scenario C | $80 nominal OR 20% below 90d trailing Brent avg | Calibration-dated | Pending June 30 |

**Canonical Brent price source (established v1.17): BZ=F (ICE front-month futures, market_data MCP or Yahoo Finance). Fortune T2 daily spot references rejected after source discrepancy confirmed May 13.**

**C-trigger clock history — T1 CONFIRMED (June 7, 2026, market_data MCP BZ=F historical):**
BZ=F daily close data March–June 2026 fetched from market_data MCP (T1). Maximum consecutive closes at or above $110:
- **3 consecutive closes: March 27 ($112.57), March 30 ($112.78), March 31 ($118.35).**
  Broken April 1 ($101.16).
- Other runs: April 28–30 = 3 days ($111.26, $118.03, $114.01); May 4 alone ($114.44); May 18–19 = 2 days ($112.10, $111.28).
- Maximum run observed: **3 consecutive closes** — far below the 10-close C-trigger requirement.
- **Prior T2 estimate (May 25 session) of "~5–6 consecutive closes" was INCORRECT.** Corrected to max 3 T1-confirmed.
- 52-week BZ=F intraday high: $126.41 (Investing.com, between May 13 and May 22 — may have occurred intraday without sustained closing basis).
- **C-trigger clock: INACTIVE, Day 0. Has never been triggered.**

Current status (June 7, 2026): BZ=F $93.09 (June 5 close). Well below $110 restart threshold. Clock will only restart on a BZ=F close ≥$110; requires 10 consecutive closes to fire.
SGOL WTI floor ($55): WTI ~$87–90 (carry). DXY ~99 (carry). No invalidation risk.

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

May 26 full session: **CPI B trigger status: print 2 of 3 (March 3.3%, April 3.8%). May CPI print June 10 is the binary event: if ≥4.0% → B formal trigger fires (3rd print). ⚑ FIRED June 10, 2026 — May CPI 4.2% YoY (T1 BLS USDL-26-0824). PAVE exit (Trigger 1) executed same session. New probability vector A=5/B=41/C=38/D=5/E=4/F=7. See Session_Log §8 June 10, 2026.** FOMC holding 3.50–3.75% (Kevin Warsh confirmed as Fed Chair May 22; FOMC hawkish; rate hike risk discussed for 2027). Q1 GDP +2.0% (positive). Sahm Rule 0.20. Term premium (THREEFYTP10): 0.8117% (May 15 — 14-yr high, rising). 30Y yield: 5.07% (approaching M17 §12.5 warning level). Yield curve 10Y–2Y +43bp; 10Y–3M +88bp — post-inversion re-steepening = D_timing_signal RECESSION_ONSET_PATTERN.

**B_WATCH_LEVEL_3 protocol (added June 7, 2026 — GAP-15 fix):**
For the 3rd CPI print (the formal trigger gate), graduated response by print level:
- **≥4.0%**: B formal trigger FIRES. Run DeriveScenarioProbabilities() immediately. EXIT PAVE (Trigger 1). Revise B/C split.
- **3.5–3.9%**: B_WATCH_LEVEL_3. Document in §8 as `b_watch_level_3: active`. Prepare PAVE exit parameters. Do NOT execute exit yet — trigger has not fired. Note acceleration trend. Run DeriveScenarioProbabilities() to assess forward B probability shift.
- **<3.5%**: B trigger concern receding. Carry probabilities; update §7 credit readings; note deceleration vs prior prints.

---

## Section 3 - Calibration Log (last 10 entries; prior entries in Calibration_Log.md)

**Scope rule (added 2026-06-20, retroactive cleanup):** this section logs WHY a
live calibration value (§1/§2/§4/§9/§11/§12/§13) is what it is — M16 4-layer
rationale, threshold corrections, classification revisions. It does NOT log:
(a) engineering/code/parser/doc changes, even when the same commit happens to
touch this file's structure — those go in FRAMEWORK_BACKLOG.md only; (b)
session-level probability/trigger/trade narrative that Session_Log.md §8
already covers authoritatively — point to the date instead of restating it.
This file is loaded as Project Knowledge every advisory session; engineering
narrative here costs every session for zero advisory benefit. See
FRAMEWORK_BACKLOG_ARCHIVE.md for the engineering-side history of entries
trimmed out in this cleanup.

2026-07-03 (v1.51) - DBMF §13 Thesis Sustaining Condition: first formal
evaluation since creation (2026-06-17). Client-prompted, triggered by a T1
price-vs-calibration cross-check during a broader instrument-simplification
review (VT/VTI/SCHD/RSP/DBMF price-history audit). Condition 1 (B+C>=55%)
NOT MET this session — actual 48.5%. Condition 2 (>=2 of {BZUSD, GCUSD, DXY,
^GSPC} trending, 8wk window) MET at the margin (Brent -34% and Gold -9.7%
trending; DXY +1.6% flat and equities whipsawing, both NOT trending). Neither
failure_signal fired. NET STATUS: DEGRADED (same category as MLPX), not
FAILED. Mechanism note: the 2022 B/C analog underpinning DBMF's ★ HIGH-
confidence §4.1 values was carried by a clean 9-month DXY trend (+18.5%) and
the fastest Fed hiking cycle in 40yr, DESPITE choppy equities that year (2022
RSP intra-year swings were larger than today's) — equity behavior was never
the correct test for this role; today's DXY specifically lacks 2022's trend
breadth. §4.1 B=[+15,+30]/C=[+18,+35] VALUES are NOT revised by this entry —
the M16 4-layer analog basis (1973-82, 2022) is unchanged and not disputed.
This is a live sustaining-condition finding, distinct from a return-table
revision, and does not require M16.CalibrationMethodology(). Detail: §13
DBMF entry, evaluation_2026_07_03 field.

2026-07-03 (v1.51) - RSP EV refresh (client question, same simplification
review). RSP's §11.4 classification (broad_market_equity_domestic 0.92 +
secular_technology_growth 0.08, 2026-06-25) is unchanged — re-verified live
via advisor_evaluate_allocation at today's session probabilities. EV improved
from -0.87% (at classification, 2026-06-25 probs) to +1.11% (today), driven
by BMED Scenario A's HIGH-confidence adoption ([5,12]->[10,20]) in the
interim — RSP's 92% BMED weight captures that upward revision almost fully.
Directive remains REDUCE_TO_MIN (still well below MLPX/DBMF). NOT ADOPTABLE
conclusion unchanged; number less negative, not reversed. No classification
or §4.1 change — logged for continuity since the prior EV figure (-0.87%) is
now stale by three weeks of calibration changes.

2026-06-30 (v1.49, Q2 audit) - §1 credit thresholds Batch A audited.
Trailing-180d medians computed and recorded in §1 (HY 283 / IG 78 / CCC 935
bps; via the framework's own fred_fetcher over the FRED REST API). HY_STRESS
(+150), HY_RECESSION (+300) and IG_TRANSMISSION (+60) deltas RETAINED
unchanged: they are sized to a full-cycle distribution and cannot be
re-verified against FRED's now-3y-truncated OAS history. Measured against the
available benign 3y window the triggers read high (97.7th-100th pct, above the
intended 75-90th band), but that is a window artifact — the 2008/2020 tails
are gone — not a miscalibration; forcing the deltas down into the 3y band
would fire stress/recession triggers on routine noise. §1.3 CCC divergence:
the ratio mode ("CCC widens 3x composite/30d") false-positives in compressed
regimes (2026-06-30: CCC +29 / HY +8 bps -> 3.62x trips on a noise-level
move); the absolute +200 bps floor correctly did NOT fire and is retained.
Decision: gate the ratio mode behind a minimum absolute CCC move (values 3x /
+200 / <50 unchanged). Data + code follow-ups (FRED history not exposed via
any MCP tool; the 3y truncation itself; calculator_mcp wiring; the CCC-gate
credit.py change) filed as FRAMEWORK_BACKLOG ENG-42/43/44/45. Detail: §6
Batch A.

2026-06-30 (v1.48, Q2 audit) - broad_market_equity_domestic Scenario A
ADOPTED: [5,12] -> [10,20]. Confidence MEDIUM -> HIGH. The 2026-06-25 review
logged this PENDING solely because its 1991/2003 analog figures were general
knowledge, not T1-verified. Re-verified this session via Slickcharts (the
source already used for S&P annual returns): 1991 total return +30.47%
(~+26% real, BLS annual-avg CPI 4.2%); 2003 +28.68% (~+26% real, CPI 2.3%);
2016 RSP +14.50% (~+12.4% real) was already fresh. All three analogs land
at/above the adopted range; 2016 anchors the conservative end. L4 (neutral
A=35/B=15/C=15/D=10/E=5/F=20, with B=[-2,+5] already adopted): +2.40% vs
~2-3% anchor, PASS -- this exact A+B pairing was pre-computed in the
2026-06-29 B-adoption entry. Full L1-L3 detail: 2026-06-25 log entry. Client
confirmed adoption 2026-06-30. (§6 item 23[16] -> ADOPTED.)

2026-06-30 (Q2 audit) - broad_market_equity_domestic Scenario C: 2003 Iraq
War analog run (the candidate flagged 2026-06-29 as the route past the 1990
recession confound). The analog clears the confound but does NOT resolve the
EV-relevant conservative bound; the conservative revision is HELD
(client-confirmed 2026-06-30) -- no change to C this session.
  - Non-recessionary backdrop CONFIRMED (NBER T1: 2001 recession ended Nov
    2001; the March 2003 invasion sits well into recovery). 1990 confound
    re-confirmed (NBER: 1990-91 recession began July 1990, pre-invasion).
  - Discrete oil shock CONFIRMED (St. Louis Fed T1-equiv: crude +45% Dec
    2002 -> Feb 2003 to ~$40, $5-15 war premium, then a record one-day NYMEX
    drop on swift resolution; milder/shorter than 1990-91).
  - BUT 2003 equities ended +28.68% total (~+26% real) -- strongly positive,
    dominated by the post-2000-2002-bear recovery rally. So 2003 is an
    UPSIDE data point, not a downside floor. Every rate-stable discrete-oil-
    shock analog available (1979 ~+7% real, 1991 ~+26%, 2003 ~+26%) is
    positive; the only negative oil-shock years (1974, 1990) are
    recession-contaminated = D-territory captured separately.
  CONCLUSION: the conservative bound for pure (non-recessionary) C is not
  derivable from a drawdown analog -- such clean analogs do not exist,
  because non-recessionary oil shocks were not equity-drawdown events.
  Current -4 is likely too pessimistic (inherits recession damage) but no
  specific replacement is analog-supportable. Upside [-1]->[+6,+8] is now
  HIGH-confidence but disclosure-only (never enters EV); NOT adopted, to
  avoid cherry-picking the EV-irrelevant half while the EV-relevant half is
  open. §6 item 42 next step re-scoped from "find a better analog" to a
  methodology decision on setting a non-analog-derivable conservative bound.

2026-06-29 (v1.46 follow-up) - M16.CalibrationMethodology() 4-layer run:
broad_market_equity_domestic Scenario C. Client-prompted follow-up to the
same-day B revision (above) -- correctly pointed out that C carries the
identical acute-shock-vs-sustained-grind bifurcation flagged unresolved
2026-06-25, and that it had not been addressed when a VTI hypothetical was
run using C's stale value as the single largest negative EV contributor.
NOT ADOPTED -- logged PENDING. Confidence and reasoning below explain
exactly why, since "not adopted" should never again mean "no reason given."

L1: same ~2-3% real unconditional anchor as B (same role).

L2 (4 T1-verified analogs, same rate-shock/rate-stable discriminator already
    validated for B): Acute (shock co-occurring with an independent monetary
    shock) -- 1973-74 Arab embargo + Bretton Woods collapse: real ~-19.6%/
    -33.8%/yr (2yr annualized ~-27%/yr; BLS CPI 6.2%/11.0%, Slickcharts S&P
    -14.66%/-26.47% nominal -- same T1 figures as the B entry, reused here
    under C's discrete-event lens); 2022 H1 Russia-Ukraine, concurrent with
    the fastest Fed hiking start in 40yr: RSP -16.80% nominal H1
    (market_data_mcp T1, Jan 3-Jun 30 2022 close-to-close), CPI 7.5% (Jan,
    BLS T1) -> 9.1% (June, widely-reported BLS peak) -> annualized-equivalent
    real approx -36%/yr (stylized annualization of a half-year shock, same
    convention E already uses for acute-quarter figures -- not a literal
    full-year claim). Sustained/rate-stable -- 1979 Iranian Revolution oil
    shock (Fed tightening but not from a near-zero panic base): S&P +18.44%
    nominal, CPI 11.3% -> real +6.41% (Slickcharts+BLS T1, same figures as B
    entry); 1990-91 Gulf War, Iraq invades Kuwait Aug 2 1990 (Fed explicitly
    declined to hike in response to the oil spike -- Wikipedia/Econlib T1,
    corroborated by Berkshire Edge/DataTrek -- and was in fact cutting rates
    over this window, 8.25%->6.75%, for reasons unrelated to oil): S&P -3.10%
    nominal/CPI 5.40% -> real -8.05% (1990); S&P +30.47%/CPI 4.21% -> real
    +25.19% (1991); 2yr annualized real +7.29%/yr (Slickcharts+in2013dollars
    T1, fresh this session).

L3 (the actual blocker): the single worst rate-stable analog (1990, real
    -8.05%) is NOT a clean discrete-oil-shock-only data point -- the NBER
    recession officially began July 1990, BEFORE Iraq's Aug 2 invasion. 1990's
    poor equity performance reflects an ALREADY-WEAKENING economy (S&L
    crisis, brewing recession) that the oil shock landed on top of, the same
    way 2022's worst-case for B was contaminated by an independent rate
    shock. Today's environment is explicitly non-recessionary this session
    (GDP +2.1% real, unemployment 4.3%, NFP +172k, credit spreads calm --
    see this session's briefing). Using 1990 as the pure-C conservative floor
    therefore likely OVERSTATES the downside by importing D-type
    (recessionary) damage that the framework's separate D scenario already
    exists to capture. No clean substitute analog was identified this
    session -- 2003 Iraq War oil spike (post-2001-recession, genuinely
    non-recessionary backdrop) is a plausible better-fitting candidate,
    flagged for the audit, not run this session (out of time, not declined
    on principle).

L4: NOT RUN for a specific proposed value, because no specific conservative
    value cleared L3. Running L4 against an unresolved L3 would produce a
    consistency check against a number that isn't actually supported --
    skipped deliberately rather than performed for appearance.

CRITICAL FINDING (the actual answer to why this isn't "fixed" the way B was):
M15.blendedScenarioReturn() and every EV/allocation computation downstream of
it use the CONSERVATIVE bound ONLY -- upside is disclosure-only, never
consumed by any computation (see analysis/instruments.py docstring, unchanged
since before this session). The evidence above strongly supports raising C's
UPSIDE bound (current -1% is clearly too low given the 1979 and 1991 results)
but says almost nothing decisive about the CONSERVATIVE bound specifically
because of the L3 confound -- and the conservative bound is the only one that
would move any instrument's actual EV. A revision that improved only the
upside (technically permissible to compute, since it doesn't touch EV) was
deliberately NOT applied to the live table this session: adopting a partial
revision while the framework's own NEVER rule (no MEDIUM/LOW-confidence
revision adopted intra-session) is in force for the unresolved half would set
a bad precedent of cherry-picking the "safe-looking" half of an
under-evidenced proposal. PROPOSED for the June 30 audit: C upside [-1]->[+6,
+8] range (well-supported); C conservative -- resolve the 1990 recession-
confound first (via the 2003 analog or another non-recessionary discrete
oil-shock episode) before proposing a specific number. Confidence: upside
dimension HIGH; conservative dimension genuinely unresolved, not LOW or
MEDIUM-and-being-cautious -- the evidence itself splits along a line that
doesn't map onto a single confidence tier.

2026-06-29 (v1.46) - GAP-16 promoted from advisory-only to a live, bounded EV
adjustment. Client correctly identified that the framework had built a
working diagnostic (analysis/range_position.py, v1.42, June 20) confirming
SGOL/SIVR were facing a real-yield-rising + DXY-appreciating headwind, then
left it disconnected from blendedScenarioReturn() for 9 days while SGOL's
EV continued to compute as if no headwind existed. This was a genuine
priority-flagging failure, not a calibration-timing question — §6's
checklist had no urgency marker distinguishing "confirmed live cost" from
"routine bookkeeping," and the diagnostic's own output (signal=unfavorable,
drivers logged each session) was never escalated past advisory text. See §6
priority-convention note (same date) for the structural fix to the checklist
itself.

MECHANISM (code, not calibration): CalibrationState gained an optional
range_position_signals: Dict[str, str] field (role_id -> "favorable"/
"unfavorable", default {} -- zero effect on any pre-v1.46 caller or test).
mcp_server.py now populates it each session from the same
evaluate_range_position_advisories() output already computed for the
briefing, via the new clean_signal_role_map() (drops "mixed"/"inconclusive"
-- absence of agreement is treated as absence of evidence, not a neutral
signal). blended_scenario_return() (analysis/instruments.py) now calls the
new apply_range_position_adjustment() (analysis/range_position.py) for the
conservative return_type only (upside is never used in any computation, so
adjusting it would be dead code): when a component's role has a clean
signal AND that role's §4.1 range for the scenario is >=6pp wide (same GAP-16
gate as the original advisory), the value is shifted by
min(25% of range width, 3pp) -- toward the table's conservative end on
"unfavorable" (can go BELOW the documented conservative floor -- that is the
point: a confirmed headwind means the table's own floor is now optimistic),
toward upside on "favorable" (clamped, can never exceed the table's own
upside). Absent a signal, every call site is byte-for-byte unchanged --
confirmed via full test suite (773 passed, 46 skipped, 0 failed, including
17 new tests covering backward compatibility, bound/clamp behavior, cross-
role non-leakage, and the narrow-range no-op gate).

VERIFIED LIVE IMPACT (standalone script against the real parsed
Calibration_State.md, today's actual probability vector A=12.125/B=30.3125/
C=30.3125/D=3.0/E=6.0625/F=18.1875, today's stated macro conditions -- DXY at
a 13-month high (appreciating), real yields rising, both already confirmed
unfavorable in this session's own briefing before this fix existed): SGOL's
full blended-scenario EV moves from +0.94% (unadjusted) to -0.32% (adjusted)
-- enough to plausibly flip the live directive away from ADD. Actual
directive change will be confirmed the next time advisor_run_computation
runs in a live MCP session (this session's already-running server process
has the pre-fix code in memory; the fix takes effect on next server start).

PROVISIONAL: the 25%/3pp adjustment magnitude is a conservative starting
point, not yet empirically validated via M16.CalibrationMethodology() --
owed at a future audit, tracked in §6 item 40. The MECHANISM (bounded,
agreement-gated, table-range-clamped, conservative-only) is the actual
v1.46 fix and is not provisional; only the specific numbers are.

STF/RAC/IHC sub-condition extension (named in scope at v1.42, still not
assigned): apply_range_position_adjustment() and clean_signal_role_map()
already generalize to any role with a documented signal -- extending GAP-16
beyond IHP is now purely a §11 documentation task (identify 1-2 governing
variables per role, add a sub-condition note) with zero further code change,
once those drivers are identified at a future session.

2026-06-29 - M16.CalibrationMethodology() 4-layer run: broad_market_equity_domestic
Scenario B (client-requested, prompted by observed 3M price divergence: RSP/VTI
strongly positive during the current B-dominant window vs MLPX flat). RESOLVES
the acute-shock vs sustained-grind bifurcation flagged unresolved 2026-06-25.

PROPOSAL: B [-8,-2] -> [-2,+5]. Confidence: HIGH. ADOPTED this session
(client explicit confirmation given).

L1: unconditional anchor ~2-3% real (unchanged, same JPM LTCMA/Vanguard VCMM
    basis as 2026-06-25 entry).

L2 (T1-verified this session, replacing the 2026-06-25 entry's unverified
    general-knowledge figures): bifurcation resolved by separating analogs on
    a structural criterion — rate CHANGE during the period, not rate LEVEL.
    Acute-shock B (large rate move from a low/different base): 1973-74 S&P
    -14.66%/-26.47% nominal (Slickcharts T1), CPI 11%/11% (BLS T1) -> real
    roughly -24%/-35%; 2022 RSP -11.69% nominal (market_data_mcp T1, full-year
    close-to-close), CPI ~8.0% avg -> real ~-19.7% (Fed funds 0.25%->4.5% in
    12mo, the defining feature). Sustained-grind B (rates elevated but STABLE,
    no shock): 1979 S&P +18.44% nominal (Slickcharts T1), CPI 11.3% (BLS T1)
    -> real +7.1%; 1977-78 2yr avg S&P ~-0.6%/yr nominal, CPI ~7.1%/yr avg ->
    real ~-7.7%/yr (worst sustained-grind outcome found, still involved a
    multi-point Fed funds rise, not pure rate-stable); current 2026 B 3M
    window RSP +10.5% nominal (market_data_mcp T1), CPI ~4.2% -> real ~+6%,
    Fed funds 3.5-3.75% HOLDING (no shock — terminal-rate environment).
    1980-81 (Volcker deliberate recession-inducing tightening) and 2022 H1
    excluded from the sustained-grind bucket — both involved acute deliberate
    policy shock, contaminating them as sustained-grind analogs regardless of
    multi-year averaging.

L3: stress-tested the sustained-grind bucket specifically (not the full B
    historical range) — worst clean sustained-grind outcome found is the
    1977-78 ~-7.7%/yr real figure, which itself still included a meaningful
    rate rise (Fed funds roughly 5%->10% over the window), making it harsher
    than a true rate-stable case. No historical episode of stable-elevated
    rates + positive GDP + intact labor delivering -8% real was found.
    Conservative floor set at -2% (not 0%) to retain margin for a sustained-
    grind environment that's somewhat worse than the current one (e.g. CPI
    re-accelerating past 5% while the Fed continues holding).

L4 (proposed B=[-2,+5], neutral distribution A=35/B=15/C=15/D=10/E=5/F=20,
    current operative values elsewhere unchanged): neutral-distribution EV
    moves from -0.25% (under old B=-8%) to +0.65% -- not yet at the 2-3% L1
    anchor alone, but closes most of the gap and becomes fully consistent
    with the anchor once paired with the already-PENDING A revision ([5,12]
    -> [10,20], logged 2026-06-25, still MEDIUM/not adopted) -> +2.40% EV.
    Residual gap attributable to C (same unresolved bifurcation, see below)
    and the several still-PENDING D/E/F-adjacent roles. PASS.

C: NOT addressed this session -- same acute-shock/sustained-grind structural
   question applies to C (oil-shock-type analogs), unresolved, flagged for
   separate review. Do not assume C carries the same resolution as B without
   running it independently -- C's acute analogs (1974, 1979-80 oil shocks)
   have a different causal mechanism (supply-side commodity shock vs
   demand-side rate shock) and may not share B's rate-stability resolution.

DOWNSTREAM IMPACT (informational, not separately adopted -- recomputed live
each session via M15.blendedScenarioReturn()): RSP/VTI/QQQM/SCHD EVs all
improve under today's probability vector; SCHD's directive crosses from
REDUCE_TO_MIN to approximately breakeven/HOLD; none of the four become
clearly ADD-worthy this session. Currently-held primary/Relative account
EVs change negligibly (BMED-dominant instruments not held in active
allocations; MAGS/XAR carry only small BMED sub-weights).

2026-06-29 - SCHD (Schwab U.S. Dividend Equity ETF) added to §11.4 as new
candidate instrument (client-requested index-fund simplification review,
same line of inquiry as the 2026-06-25 RSP/VTI/QQQM candidate review).
ThematicETF_ClassificationAudit: sector-bucket level, fresh search this
session (Schwab official holdings, ETF Database sector table, TopDividendETFs
post-Q2-2026-rebalance snapshot dated 06/24/2026) — NOT a full 103-name
binding-driver audit (MEDIUM confidence), same caveat as RSP/QQQM. Sector mix:
Energy ~17-19% -> inflation_hedge_commodity_linked; Consumer Staples ~17-20%
-> consumer_defensive_equity; Health Care ~15-17% -> healthcare_defensive_equity;
remainder ~49% (Industrials, Financials, Consumer Discretionary, Information
Technology — TXN/QCOM excluded from STG on binding-driver grounds, mature
dividend semis not AI-capex/mega-cap growth names — Communication Services,
Materials, Utilities) -> broad_market_equity_domestic. Components adopted:
BMED(0.49) + consumer_defensive_equity(0.18) + healthcare_defensive_equity(0.16)
+ IHC(0.17). M07 PASS (AUM $96.0B, ER 0.06%, inception Oct 2011 ~14.7yr track
record, no foreign concentration, no K-1). EntryExtensionGuard CLEARED (90d
trailing avg $31.43 vs current $32.09 = +2.11%, threshold 15% on BMED dominant
role). Distinguishing factor vs RSP/VTI/QQQM: genuine defensive/inflation-hedge
characteristics (staples + healthcare pricing power, energy commodity-linkage)
rather than pure broad-market beta — structurally different EV profile expected.
CAVEAT: SCHD's EV is downstream of THREE separate open calibration questions
simultaneously, more than any other instrument in §11 — BMED B/C unresolved
(pending June 30); healthcare_defensive_equity ALL six scenarios PENDING June 30
(MEDIUM, never run through M16 4-layer); consumer_defensive_equity D/E/F PENDING
June 30. Live EV computed via advisor_evaluate_allocation same session — see
Session_Log.md for the resulting figure; not duplicated here per the
session-narrative exclusion rule above.

2026-06-25 - M16.CalibrationMethodology() 4-layer run: secular_technology_growth
Scenario F (client-requested recalibration review). Also: audit gap identified
(broad_market_equity_domestic never run through M16) and VTI/QQQM/RSP candidate
review (client request, same session).

STG F proposal: [4,11] -> [8,20]. Confidence: MEDIUM. NOT adopted this session.
L1: unconditional anchor ~1% real (VCMM 0-2%, RA ~1%) — same anchor used for
    the STG B HIGH-confidence adoption (v1.27).
L2: two structurally relevant multi-year F analogs, using the framework's own
    2-3yr sustained-regime convention (per STG D/E rederivation precedent):
    (a) 2017-2019 (3yr): QQQ nominal +32.7%/-0.1%/+39.0% (FinanceCharts,
        TradeThatSwing; cross-checked against SEC N-30B-2 NAV total-return
        filings) -> 3yr annualized ~+22.6% nominal / ~+19.6% real (CPI ~2.3%/yr).
    (b) 2023-2024 (2yr, most structurally relevant — same AI-capex driver as
        the current cycle): QQQ nominal +56.4%/+25.7% -> 2yr annualized ~+40%
        nominal / ~+37% real (CPI ~3%/yr).
    1995-2000 (the framework's third Layer-2 F analog per §4.1 SCENARIO_TO_PERIOD_MAP)
    excluded from the proposed range's derivation: directionally consistent but
    a weaker structural match (1990s internet-buildout economics differ from
    hyperscaler AI-capex economics) and it ended in a -78% NDX collapse the
    framework should not want naively read as a "conservative" floor.
L3: structural adjustment, LARGE and DOWNWARD — the load-bearing judgment call
    here. §6 item 37 (logged May 22, 2026) already documents: hyperscaler capex
    growing 60-80%/yr vs. revenue growth 15-16%/yr; FCF projected to decline
    ~90% across the Big Four; "prisoner's dilemma" competitive dynamics with
    no coordination mechanism among 5+ hyperscalers; an explicit fiber-optic-
    1999 analogy ("technology correct, equity returns poor due to timing, cost
    of capital, and competitive dynamics"). Historical realized returns (L2)
    do not price this in by construction — they describe the buildout, not
    what happens if/when its economics catch up with it. Conservative end
    (+8%) is set well below both L2 analogs (+19.6%/+37%) specifically because
    of this; upside (+20%) stays well below the 2023-24 realized figure for
    the same reason. Elevated starting valuations (vs. 1995, 2017, and even
    2023 entry points) further cap forward real returns via standard
    mean-reversion logic.
L4: NEUTRAL_DISTRIBUTION (A=35/B=15/C=15/D=10/E=5/F=20). Row neutral-weighted
    average with F=+8 (other cells at current operative values, STG B=-2
    adopted): 0.35(6)+0.15(-2)+0.15(2)+0.10(-6)+0.05(-12)+0.20(8) = +2.50%
    vs L1 anchor ~1%. Gap +1.5pp. PASS (within ±3pp).
Confidence note: 2 clean, structurally-relevant analogs in directional
agreement, but the L3 adjustment is large enough it could plausibly be argued
to exceed the "bounded (<3pp)" MEDIUM threshold and edge toward LOW — flagging
explicitly rather than rounding up to HIGH. The capex-sustainability risk is a
live, unresolved debate, not a settled structural fact the way e.g. MLPX's
deleveraging-vs-2014 or AIPO's contract backstops are. LOGGED PENDING per
RevisionAdoption rule (§6 item 23[15]) — formal adoption decision: June 30.

Separate finding from the same review: broad_market_equity_domestic (used by
MAGS at 15% weight, XAR at 10%, and central to any VTI/RSP/QQQM evaluation)
has NEVER been run through M16.CalibrationMethodology() — no marker anywhere
in §4.1 for this role; current values are unaudited v1.0 baseline. Added as
new §6 audit item 41. This blocks a clean EV for RSP as a candidate until
that role gets its first 4-layer pass.

VTI/QQQM/RSP candidate review (client request, this session):
- VTI: already eliminated from all target allocations April 30, 2026 (v1.9,
  see §11.3) as part of the broader move from a generic core holding to the
  granular role-targeted instrument set (AIPO/MAGS/XAR/MLPX added the same
  window). Not a performance-based rejection on record — a strategic
  transition. §11 entry retained only for blendedScenarioReturn() during
  the transition.
- QQQM: not in §11. No M07/M15 classification audit exists. Directionally,
  Nasdaq-100 is MORE concentrated in secular_technology_growth than MAGS's
  85/15 split (no broad_market_equity_domestic diversification component at
  all) — whatever EV problem MAGS has, QQQM likely shares or worsens, not
  solves. Would need a full ThematicETF_ClassificationAudit (same treatment
  as AIPO/INFL/URA) before a real number can be assigned.
- RSP (S&P 500 Equal Weight): not in §11. Structurally the most promising of
  the three — equal-weighting away from mega-cap concentration means RSP
  leans much more on broad_market_equity_domestic and much less on
  secular_technology_growth than VTI/QQQM/MAGS. EV can't be honestly computed
  until broad_market_equity_domestic gets its first M16 pass (above) —
  flagged as a candidate, not classified.

2026-06-25 (cont'd) - M16.CalibrationMethodology() 4-layer run:
broad_market_equity_domestic, all 6 scenarios (client-requested; first-ever
M16 review for this role — no confidence marker had ever been applied).
Also: documentation hygiene fix (MAGS D/E "operative" note was stale) and
VTI reassessment using both this review and the pending STG F proposal above.

L1 anchor (all scenarios): ~2-3% real unconditional (JPM LTCMA-style US
large-cap 10yr estimate; existing §4.1 footnote already cites broad_market
~1-4% real).

A (1991 Gulf War normalization / 2003 Iraq drawdown / 2016 commodity rebound):
  L2: 1991 S&P +30.5% nominal (~+26% real; general knowledge, NOT
      independently re-verified via T1 search this session — flag for
      confirmation); 2003 S&P +28.7% nominal (~+26% real, same caveat); 2016
      RSP +14.50% nominal (fresh search this session) -> ~+12.4% real
      (CPI ~2.1%). All three analogs land well above the current [5,12]
      range — even 2016, the weakest and freshest, sits at the upside bound.
  L3: 2016 is structurally the closest match to a present-day A (post-conflict
      commodity normalization without a full war-drawdown reset); using it as
      the anchor rather than 1991/2003 is itself a conservative choice.
  L4 (proposed A=[10,20]): 0.35(10)+0.15(-8)+0.15(-4)+0.10(-12)+0.05(-8)+0.20(7)
      = 3.5-1.2-0.6-1.2-0.4+1.4 = +1.5% vs ~2-3% anchor. Gap ~-1pp. PASS.
  PROPOSED: [5,12] -> [10,20]. Confidence: MEDIUM (1991/2003 figures not
  independently re-verified this session — re-confirm via T1 search before
  formal adoption). LOGGED PENDING, not adopted (§6 item 23[16]).

B (1973-1982 stagflation / 2022): INVESTIGATED, NOT RESOLVED — genuine
  bifurcation found. 1973-74 (acute phase): S&P approx -14.7%/-26% nominal,
  CPI ~8-11%/yr -> real roughly -23% to -37%/yr (general knowledge, NOT
  verified this session). 1979-1982 (sustained, less-acute phase): S&P
  approx +18.4%/+32.4%/-4.9%/+21.5% nominal (general knowledge, unverified)
  -> 4yr annualized nominal ~+16%, CPI averaged ~10.5%/yr -> real ~+5.5%/yr
  POSITIVE. 2022: S&P -19.44% nominal (T1-adjacent), CPI ~8% -> real ~-27%.
  Acute-shock years (1973-74, 2022) and "grinding through it" years
  (1979-82 ex-acute) point in opposite directions by a wide margin. Current
  [-8,-2] sits in between, consistent with neither read cleanly. NO PROPOSAL
  — flagging as a genuine open structural question rather than forcing a
  number through. All figures here need T1 re-verification before any
  further work; treat as directional only. Confidence: LOW.

C (1974 oil shock / 1979-80 second oil crisis / 2022 H1): same bifurcation as
  B, more extreme. 1974: real ~-37%/yr (single acute year, unverified general
  knowledge). 1979-1980 (general knowledge, unverified): both POSITIVE
  nominal (+18.4%/+32.4%), real ~+7%/+19% — the oil shock did NOT mean a down
  market those two specific years. 2022 H1 (annualized from ~-20% 6mo): real
  ~-45%/yr. Current [-4,-1] again sits between two historically opposite
  outcomes. NO PROPOSAL — same open-question treatment as B. Confidence: LOW.

D (2008-09 GFC / 2020 COVID): REVIEWED, CONFIRMED — no revision proposed.
  L2: RSP 2008 -40.07%, 2009 +44.64% (fresh search this session) -> 2yr
      annualized nominal ~-6.9%, real ~-8.6% (CPI ~1.7%/yr avg). Sits
      comfortably inside the current [-12,-4] range.
  2020 (V-shaped, RSP +12.71% full year) is a poor D analogue on its own —
      fast policy-driven recovery, inconsistent with the 2-3yr sustained-
      regime convention; excluded from the headline figure, noted for context.
  Confidence: MEDIUM (one clean multi-year analogue, fresh data). No change.

E (2008 Q4 acute / 1998 LTCM / 1987 crash): REVIEWED, CONFIRMED — no revision
  proposed. Raw quarter-annualized figures here are extreme (2008 Q4 ~-64%/yr
  nominal annualized; 1998 LTCM 3mo drawdown ~-57%/yr annualized; 1987 3mo
  drawdown ~-80%/yr annualized — all general knowledge, not independently
  re-verified this session) — consistent with the framework's own existing
  convention elsewhere (e.g. STG E settled at -12% rather than a literal
  Q4-2008 annualized figure) that E's raw acute-quarter annualization is not
  meant to be read as a literal full-year expectation; current [-8,-3] sits
  in reasonable proportion to STG's already-adopted -12% (broad market
  historically less volatile than concentrated tech in acute crashes).
  Confidence: LOW-MEDIUM (proportionality argument, not a clean direct
  analogue computation). No change proposed.

F (1995-2000 / 2017-2019 / 2023-2024): REVIEWED, CONFIRMED — no revision
  proposed. RSP 2017-19 3yr annualized ~+12.1% nominal / ~+9.6% real; RSP
  2023-24 2yr annualized ~+13.3% nominal / ~+10.0% real (both fresh search
  this session). Both sit comfortably inside the current [7,14] range —
  notably much lower than QQQ's equivalent figures for the same windows
  (~19.6%/~37% real — see STG F entry above), which is exactly the
  diversification effect the BMED/STG split is supposed to capture, and is
  itself a useful empirical confirmation that the split is doing its job.
  Confidence: MEDIUM (two clean, fresh, structurally relevant analogues,
  good agreement). No change proposed.

SUMMARY: of 6 scenarios, only A has a clear case for revision (MEDIUM
confidence, logged pending, §6 item 23[16]). D/E/F reviewed and confirmed
consistent with available data — status updated from unmarked to "reviewed."
B/C are a genuinely open structural question (acute-shock vs. sustained-grind
bifurcation) this session could not responsibly resolve — flagged for
dedicated Q-end work, not a quick fix.

DOCUMENTATION HYGIENE FINDING (corrected from an earlier draft of this same
entry): initially flagged the MAGS §11.3 entry's D/E computation notes
("operative STG D=-14... rederived -6 not yet adopted") as stale live-file
content. On verification via direct Desktop Commander read of this file
(not the project_knowledge_search tool), that detailed per-scenario
breakdown does NOT exist in the live file — MAGS's entry was already
simplified to "EV: computed fresh each session... not stored here" in a
prior session. The stale "-14/-10" text exists only in Project Knowledge's
embedded snapshot, which is evidently behind the live file. Re-confirms the
project's own standing rule: read framework files via Desktop Commander, not
project_knowledge_search, for anything execution-relevant — this session's
mistake is a concrete example of why. No live-file correction was needed;
none made.

VTI REASSESSMENT (client request): recomputed VTI's EV (broad_market_equity_
domestic 0.78 + secular_technology_growth 0.22) at today's session
probabilities (A=11.41/B=34.24/C=11.41/D=3/E=5.71/F=34.24):
  - At current OPERATIVE §4.1 values: EV ≈ -0.66%.
  - At the two PENDING proposals above (STG F=8, BMED A=10) — illustrative
    only, neither adopted: EV ≈ +0.09%. Roughly breakeven, not attractive.
  For comparison, MAGS (STG 0.85/BMED 0.15) moves from +0.47% to ≈+1.63%
  under the same pending STG F=8 proposal alone — MAGS benefits far more
  proportionally from the STG F revision than VTI does, because VTI's much
  larger BMED weight (78%) sits in a role (F) that was already fairly
  valued, not under-calibrated. If the STG F proposal holds at the June 30
  audit, MAGS becomes relatively MORE attractive vs. VTI, not less.
  CONCLUSION: this recalibration review does not change the case for VTI.
  The April 2026 transition away from VTI toward the granular instrument
  set looks, if anything, better justified by this analysis, not weaker.

2026-06-21 - GAP-16 follow-up (v1.44): IHP range-position real-yield
sub-condition corrected. THREEFYTP10 (10Y term premium) was being used as
the real-yield driver — it isn't real yield; it's bond-supply/demand
duration compensation, and the two series can diverge from the Fed-path-
driven real rate that actually sets precious metals' opportunity cost.
Replaced with REAL_YIELD_10Y_TREND (DGS10 nominal minus T10YIE breakeven
inflation, 8 weekly closes). §11 SGOL/SIVR entries updated to match.
THREEFYTP10_TREND remains registered — M19's SGOL/SIVR "real yield
sustained > 2.0%" §13 condition text still names THREEFYTP10 explicitly;
relabeling that condition is a separate §13 text change, not done this
session. Engineering detail: FRAMEWORK_BACKLOG.md ENG-39.

2026-06-20 - GAP-16: within-scenario sub-condition advisory for wide-range
roles (design gap identified June 18, 2026 companion session). Framework's
EV math uses a single conservative value per role per scenario; nothing
flagged whether current conditions favor the upper or lower end of a wide
[conservative, upside] band. Scope: inflation_hedge_precious_metals (IHP) —
priority role per the originating note; systematic_trend_following/
real_asset_contracted_revenue/inflation_hedge_commodity_linked named as
in-scope but their sub-condition drivers haven't been identified yet —
deferred to a future session. Corrected the note's own worked example: cited
"IHP B = [-2,+6], 8pp wide" — actual §4.1 IHP B = [6,12] (6pp); those figures
match Scenario C, not B. Resolution: for held IHP instruments (SGOL, SIVR),
flags real-yield (THREEFYTP10) and DXY direction as favorable/unfavorable/
mixed/inconclusive when the dominant scenario's range is >=6pp wide —
advisory only, never changes blendedScenarioReturn()/EV (per the note's own
"not a hard gate" requirement). §11 SGOL/SIVR entries now document these two
drivers explicitly. Engineering implementation: FRAMEWORK_BACKLOG.md (closed
alongside ENG-13).

2026-06-20 - §12.1-12.4 structure restored (v1.41) — values unchanged (had
never been formally calibrated; §6 audit item already covers this), but the
parser's anchor for reading them live had gone missing for an unknown
period. Detail: FRAMEWORK_BACKLOG.md ENG-18.

2026-06-19 - Documentation hygiene pass (v1.40) — §6 stale-item pruning, §11.3
redundant EV-math removal, orphaned PAVE entry deletion, §13 preamble
relocation. No calibration values changed. Detail: FRAMEWORK_BACKLOG.md
ENG-6/7/8/9.

2026-06-19 - §3 compacted, 26→10 entries (v1.39); compaction trigger
decoupled from the quarterly cadence to a per-session check. No calibration
values changed. Detail: FRAMEWORK_BACKLOG.md ENG-5.

2026-06-17 - §13 M19 Thesis Sustaining Conditions added (v1.37/v1.38): new
monitoring structure for DBMF, SGOL, SIVR, MLPX, XAR, MAGS, URA, COPX, AIPO,
INFL — each carries sustaining_conditions/failure_signals tracking whether
its structural thesis (not just its EV) still holds. PAVE dropped (exited
June 10, v1.33 — see Session_Log §8). COPX note corrected: a prior draft had
said "not currently held" — wrong, COPX is an active Acc4 holding (220 sh).
§13.1 VNQ/VEA placeholders added (CANDIDATE only, zero allocation).
GAP-3 (DBMF regime-duration/crowding-risk sizing adjustment to
M13.idealAllocation()) flagged during this hand-off as separate, larger
scope — deferred, confirmed by client. Engineering implementation (Python
evaluation engine, AI Call-2 question routing): FRAMEWORK_BACKLOG.md.

2026-06-15 - Framework v1.36 (MLPX ComponentVector revision — IHC weight).
M16.CalibrationMethodology() 4-layer run for MLPX IHC component weight (§11 parameter; M15 domain):
L1: Revised unconditional anchor RAC(0.50)/IHC(0.50) → 3.18% real (down from 3.57% at prior weights; both coherent).
    Infrastructure unconditional ~4-5% real (JPM LTCMA); commodity unconditional ~1.6-2.1% real (RA/JPM).
L2: MLPX 2015 = -35.25% nominal; AMZI Dec14-Nov15 = -33.5% total return (T1: AMLP N-CSR SEC filing).
    MLPX tracked AMZI almost 1:1 in 2015 — zero observable RAC insulation despite 65% contractual weight.
    MLPX 2020 = -20.26% nominal; AMZ FY2020 = -24.50% (T1: Cushing N-CSR). ~4pp RAC protection measurable.
    2yr annualized real 2014-15: -14.0%. IHC sensitivity clearly > 0.35 in both analogues.
L3: Three structural mechanisms documented (falsifiable, T1/T2 sourced): (1) counterparty creditworthiness
    contagion — producer credit declines in oil collapse reprices MLP equity regardless of fee structure;
    (2) volume floor risk — minimum volume commitments exposed when throughput falls below thresholds;
    (3) sector sentiment / forced-seller contagion — commodity ETF outflows drag all energy sub-sectors.
    Combined directional impact: -8 to -18pp acute D-scenario underperformance vs pure RAC contract theory.
L4: Neutral distribution (A=35/B=15/C=15/D=10/E=5/F=20). Revised: 2.500% vs anchor 3.18% → gap -0.68pp.
    Current: 2.546% vs anchor 3.57% → gap -1.03pp. Both PASS ±3pp. Revised gap is tighter.
Confidence: MEDIUM (2 analogues; no institutional RAC/IHC decomposition source for midstream ETFs).
ComponentVector revised: RAC(0.65)/IHC(0.35) → RAC(0.50)/IHC(0.50). Client confirmed 2026-06-15.
⚠ IHC E = +2% anchored to RESERVE_EROSION pathway. At v1.34 vector E=12.5% may reflect SYSTEMIC_LIQUIDITY
  — if so, IHC E should be calibrated negative. Reassess at June 30; if confirmed negative, EV improvement
  of +0.14pp from this revision reverses. Separate M16 run required (IHC E cell, not ComponentVector).
⚠ Relative IRA E-scenario nominal loss ≈ -0.68% (revised weights) at v1.34 vector. E=12.5% is below the
  15% formal floor-breach threshold — no action. Watch: if E rises above 15%, reassess floor.

2026-06-13 - Framework v1.34 (INFL §11 classification + §9.3 EntryExtensionGuard 180d override).
INFL (Horizon Kinetics Inflation Beneficiaries ETF) added to §11 as CANDIDATE instrument.
ThematicETF_ClassificationAudit() COMPLETE: ComponentVector IHP(0.25)+CL(0.50)+RAC(0.20)+STG(0.05)+UNCLASSIFIED(0.00).
TPL and LandBridge classified as inflation_hedge_commodity_linked (not RAC): revenue = royalty_rate ×
commodity_price × volume; zero capex; quality note for CL D conservative floor refinement at Q2.
M07: PASS. Foreign exposure flag (FNV/WPM dual-listed TSX; PSK Toronto) — does NOT disqualify taxable
(equity ETF, qualified dividends, 1099). ER 0.85% acceptable for active management.
EV +3.51% at the time of this decision (A=18.8/B=37.6/C=25.1/D=3.0/E=12.5/F=3.0). Rank #4.
EntryExtensionGuard CLEARS under 180d override: 180d avg ≈ $47.00; current $51.02 = +8.5% above (threshold 20%).

§9.3 EntryExtensionGuard CONFLICT DURATION OVERRIDE enacted (HIGH confidence — logical necessity, no M16 return
table calibration required). When conflict_duration > 90 calendar days from T1-confirmed onset:
  EntryExtensionGuard uses 180d trailing average as canonical baseline for CL and IHP roles.
Current status: US-Iran war onset Feb 28, 2026 (T1: AP). Duration = 105 days. OVERRIDE ACTIVE.
Deactivation: T1-confirmed signed agreement + 30 calendar days, or Q2 June 30 review.
Prior session discussion: client raised the issue at the June 8 framework audit.
No §4.1 changes.

2026-06-10 - B formal trigger fired (May CPI 4.2% YoY, Print 3/3) — applies
the existing §2.3 trigger protocol (no new calibration decision). Full
probability/trade narrative: Session_Log §8, 2026-06-10.

2026-06-07 - Audit: 3 GAP fixes (v1.32).
GAP-08: §2.1 C-trigger clock T1-confirmed (max 3 consecutive closes ≥$110: Mar 27/30/31). Prior T2 ~5-6 WRONG.
GAP-06: §11.2 STG B updated to [-2,+4]★ ADOPTED. Prior stale [-6,-1] + pending [-12,-3] both incorrect.
GAP-15: B_WATCH_LEVEL_3 graduated protocol added to §2.3 (<3.5% / 3.5-3.9% / ≥4.0% branches).
M14: Explicit window definitions (energy_90d=90 calendar days; broad_equity_30d=30 trading days) — were previously implicit/ambiguous.
M16: Layer 4 neutral distribution reminder (A=35/B=15/C=15/D=10/E=5/F=20 mandatory) — was being applied inconsistently.
BZ=F Jun 5 T1: $93.09. M14 composite MODERATE (step-down from HIGH). No §4.1 changes.

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
✓ = REVIEWED 2026-06-25 (M16 4-layer run completed; current value confirmed consistent with available data — no revision proposed, not a formal HIGH-confidence adoption).

| Role | Scenario A | Scenario B | Scenario C | Scenario D | Scenario E | Scenario F |
| --- | --- | --- | --- | --- | --- | --- |
| geopolitical_premium | [-2, 3] | [2, 6] | [4, 10] | [-4, 0] | [1, 5] | [1, 4] |
| inflation_hedge_precious_metals | [-2, 2]★ | [6, 12] | [-2, 6] | [-3, 3]★ | [10, 20] | [-3, 1] |
| inflation_hedge_commodity_linked | [2, 6] | [6, 12] | [7, 13] | [-8, -2] | [2, 6] | [2, 5] |
| real_asset_contracted_revenue | [3, 7] | [6, 14] | [8, 16] | [-6, 2]★ | [-10, 0]★ | [3, 7] |
| policy_driven_thematic_equity | [4, 8] | [-3, 1] | [-1, 3] | [-5, -1] | [-6, -2] | [4, 8] |
| rate_sensitive_income_short_duration | [1, 3]★ | [1, 3] | [1, 3] | [1, 4]★ | [-2, 2] | [1, 3] |
| rate_sensitive_income_long_duration | [3, 7] | [-4, -1] | [-5, -2] | [5, 10] | [-10, -3] | [-4, -1] |
| broad_market_equity_domestic | [10, 20]★ | [-2, +5]★ | [-4, -1]⚠ | [-12, -4]✓ | [-8, -3]✓ | [7, 14]✓ |
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

**Priority convention (added v1.46, June 29, 2026):** this list had no urgency
marker of any kind for its first 39 items — a confirmed live cost (GAP-16
sitting advisory-only for 9 days after the diagnostic it built had already
confirmed an active headwind on a held position) sat at the same visual
weight as routine bookkeeping (e.g. item 36, confirming a spreadsheet ticker
still resolves). That is a real process gap, being fixed here, not just
noted: every NEW item from this point forward must carry a [P0]/[P1]/[P2] tag
at creation — [P0] = confirmed, live, money-relevant, diagnose or fix the
same session it's identified, never queue it; [P1] = calibration/
classification work with a defined audit date, the normal case; [P2] =
documentation/engineering hygiene with no return-math consequence.
Item 40 (GAP-16) is retroactively tagged [P0] below since it's the concrete
case that exposed this gap. The other 39 historical items are NOT being
retroactively tagged in this pass: unlike GAP-16, mislabeling an already-
resolved or genuinely routine historical item costs nothing, so doing that
relabeling carefully at the June 30 audit (rather than rushed here) is a
legitimate use of audit time, not a repeat of the same deferral pattern —
the distinguishing question for any "defer to audit" decision going forward
is whether the delay itself has a cost, not whether the work is convenient
to do later.

--- BATCH A (credit) executed 2026-06-30 via framework fred_fetcher REST API (api.stlouisfed.org, FRED_API_KEY) — NOT the fredgraph.csv path (blocked). ~785 daily obs/series, 2023-07-03 -> 2026-06-29. ---
1. DONE 2026-06-30. Trailing-180d medians: HY 283 bps, IG 78 bps, CCC 935 bps. Recorded in §1.1/§1.2/§1.3.
2. DONE 2026-06-30. 3y percentiles p10/25/75/90 (bps): HY 272/285/340/392; IG 77/80/100/122; CCC 740/849/938/974. (180d percentiles also recorded in §1.)
3. RETAINED, NOT re-verifiable 2026-06-30. Trigger median+150 = 433 bps sits at ~97.7th pct of the available 3y (above the 75-90th band). Cause: FRED truncated ICE BofA OAS series to a rolling 3y window (~Apr 2026) — the "above band" reading is a benign-window artifact (missing 2008/2020 tails), not a miscalibration. No change. FRAMEWORK_BACKLOG ENG-43.
4. RETAINED 2026-06-30. Trigger median+300 = 583 bps exceeds the entire available 3y range — appropriate for a recession trigger in a non-recessionary window. Not re-verifiable without full-cycle data (ENG-43).
5. RETAINED 2026-06-30. Trigger median+60 = 138 bps exceeds the 3y max (133 bps). Not re-verifiable vs FRED's truncated 3y history (ENG-43).
   [§1.3 CCC divergence also audited this pass — see §1.3: ratio mode false-positives in compressed regimes (CCC+29/HY+8 -> 3.62x); gate behind a min absolute CCC move, enforcement pending ENG-45. Absolute +200 floor retained.]
6. BLOCKED 2026-06-30. 5-year hit-rate audit not runnable — FRED restricts these OAS series to a rolling ~3y window; only ~3y available. Needs FRED ALFRED vintages, a commercial feed, or a local rolling-history store (ENG-43).
7. DEFERRED. §2.2/2.3/2.4 are energy/macro thresholds, outside the credit-spread (Batch A) scope; carry to a dedicated §2 pass.
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

  PENDING June 30 (MEDIUM confidence — added 2026-06-25):
  - [15] secular_technology_growth F: [4,11]->[8,20]. Two clean multi-year
      analogs (2017-19, 2023-24 QQQ) offset by a large, documented capex-
      sustainability structural risk (§6 item 37). Full 4-layer detail:
      §3 log entry 2026-06-25.
  - [16] broad_market_equity_domestic A: [5,12]->[10,20] ★ ADOPTED
      2026-06-30 (HIGH). 1991 (+30.47% total) and 2003 (+28.68%) T1-verified
      via Slickcharts this session, clearing the sole blocker; 2016 RSP
      (+14.50%) anchors the conservative end. L4 +2.40% with B adopted, PASS.
      Full detail: §3 entries 2026-06-30 and 2026-06-25.

  UNRECOVERABLE (4 proposals — lost in v1.12 file split; reconstruct at June 30 audit):
  - [11]-[14]: Reference exists in prior v1.12 §6 item 23 but content not carried forward.
    Likely candidates: IHC Scenario A, RAC Scenario A, RSILD revision, geopolitical_premium C.
    Treat as open slots for June 30 audit — new proposals may supersede.
24. Implement living update protocol: now formally governed by M16_ReturnTableCalibration §5. Confirm June 30 as first formal application of M16 §5 LivingUpdateTriggers.
25. Session_Log.md compaction: retain last 10 §7 credit rows; collapse §8 to last 3 full entries + summary table. Move prior entries to Archive_2026Q2.md.
26. COPX M07 regional concentration ruling: confirm "region = political/economic bloc" ruling from v1.13 as formal framework policy. Apply consistently to all future M07 screens.
27. URA classification + M07 screen + targets — COMPLETE v1.22 (May 29, 2026); live in §11.4. ARCHIVED → Calibration_State_Archive.md.
28. SIVR entry guard — COMPLETE/CLEARED v1.14 (May 7, 2026); SIVR since fully liquidated, guard moot. ARCHIVED → Calibration_State_Archive.md.
29. COPX entry guard — COMPLETE/CLEARED v1.14 (May 7, 2026); one-time computation, COPX still held so the guard re-runs live. ARCHIVED → Calibration_State_Archive.md.
30. DBMF D/E/F scenario formal adoption: complete M16.CalibrationMethodology() Layer 1-4 for remaining three scenarios. Primary analog: D = 2008 SG CTA Index +14.1% (short equity offset by commodity reversal); E = acute 2008 Q4 whipsaw; F = 2017-2019 "trend desert." Confidence: MEDIUM — adopt at Q2 audit.
31. Healthcare_defensive_equity (XLV): confirm §11 classification. Run ThematicETF_ClassificationAudit() — sector composition has shifted toward biotech/tech-adjacent REITs; verify role weights. Full M16 calibration for all scenario values.
32. Floating_rate_credit_income (FLOT): full M07 screen. Confirm no foreign concentration issue. Compute D scenario (-10% to -4%) empirical basis using 2008 IG spread data.
33. Emerging_market_equity (VWO): full M07 screen. Confirm China (~30.8%) + Taiwan (~18-22%) combined regional concentration — determine if Taiwan Strait geopolitical risk warrants amber flag. Apply M07 regional ruling from item 26.
34. Consumer_defensive_equity (XLP): complete M16 calibration for A/C/D/E/F scenarios (PENDING). Primary analog: A = 2003-2007 XLP vs market underperformance; C = 1973-74 input cost squeeze; D = 2008 XLP -15% nominal.
35. secular_technology_growth Scenario B — RESOLVED v1.27 (June 1, 2026), ADOPTED HIGH confidence [-6,-1]→[-2,+4], live in §4.1. ARCHIVED → Calibration_State_Archive.md (full rationale in Calibration_Log.md v1.27).
36. GOOGLEFINANCE ticker setup (v1.17): New allocation spreadsheet tab added for market data "Other Indexes". Confirmed working: VIX (INDEXCBOE:VIX), S&P 500 (INDEXSP:.INX), MOVE (INDEXNYSEGIS:MOVE). FRED series: use existing spreadsheet "FRED Series" tab. BZ=F is canonical Brent reference for C-trigger clock per v1.17.
37. AI capex / secular_technology_growth context note (v1.18, May 22, 2026): Session intelligence — hyperscaler AI capex $660-830B committed for 2026 (nearly doubling 2025). Capex intensity 45-57% of revenue (vs 10-15% in 2020). Revenue growth 15-16% vs capex growth 60-80%; FCF projected to decline 90% across Big Four. Private credit ($800B+ in AI infrastructure financing) opacity flagged as tail risk not visible in HY/IG spread series. AI utility pricing emerging (62% usage-based by 2027). Prisoner's dilemma / war-of-attrition structure confirmed: no coordination mechanism among 5+ hyperscalers; 18-36 month infrastructure commitment periods prevent exit. Fiber optic 1999 analogy: technology correct, equity returns poor due to timing, cost of capital, and competitive dynamics. Portfolio implication: AIPO (infrastructure layer, contracted revenue) positive EV in B/C; MAGS (hyperscaler equity) negative EV in B/C — distinction maintained. No §4.1 changes warranted from session analysis.
38. M17 §12 thresholds (v1.19, corrected v1.20): First formal application May 25, 2026. sectorStressScore()=0 (formal, v1.20 corrected). CascadeLevel=MONITORING. CHAIN_3_WATCH=TRUE ($1.304T margin debt record loaded; FIRES on ≥−5% MoM or 3+ gate events). CHAIN_4 CALIBRATED v1.24 (June 1, 2026): canonical series = S&P Global large-company; T1-equivalent = ABI/Epiq AACER press releases; WATCH ≥220/quarter, FIRES ≥300/quarter (HIGH confidence, M16 4-layer complete); current Q1 2026 = 188/quarter — BELOW WATCH. Prior 800/quarter threshold eliminated. D=5% maintained by prior client approval (qualitative). Formal Q2 audit: calibrate remaining §12 thresholds; formal integration of yield curve D_timing_signal; M18 allocation spreadsheet series gap resolution.
39. M18 FMP data fetch (v1.21, May 26, 2026): FMP:chart historical-price-eod-light confirmed working for ^VIX and SPY. VIX_30D_AVG=17.99 and VIX_90D_AVG=21.24 computed from 62 trading days of FMP EOD data. SPY 30-trading-day return=+8.68% (Apr 13→May 22). FMP:indexes endpoint ACCESS DENIED for ^SPX (requires higher plan tier) — SPY via FMP:chart is the confirmed working substitute for BROAD_EQUITY_TRAILING. M18 updated accordingly (v1.1).
40. [P0 → RESOLVED v1.46; closed at Q2 audit 2026-06-30] GAP-16 within-scenario
    sub-condition EV adjustment for wide-range roles. The [P0] driver — a
    confirmed live SGOL/SIVR real-yield+DXY headwind that was computing into EV
    as if absent — is FIXED: v1.46 wired the bounded, agreement-gated,
    table-clamped, conservative-only adjustment into blended_scenario_return()
    (773 tests pass; SGOL EV +0.94% → −0.32% verified live). Full mechanism and
    the priority-flagging failure that delayed it 9 days: §3 v1.46 entry. Two
    residuals re-filed below — neither is [P0], because the live money cost is
    now gone: item 43 [P1] (calibrate the PROVISIONAL 25%/3pp magnitude) and
    item 44 [P2] (extend sub-condition map to STF/RAC/IHC).
41. broad_market_equity_domestic: FULL M16 4-layer review COMPLETE 2026-06-25
    (first-ever review for this role; was v1.0 baseline with no confidence
    marker). Outcome: A proposed [5,12]->[10,20] (MEDIUM, logged §6 item
    23[16]); D/E/F reviewed and confirmed consistent with available data, no
    change; B/C investigated but unresolved — genuine acute-shock-vs-
    sustained-grind bifurcation in the historical record, flagged for
    dedicated work at this audit rather than forced through. Full detail
    and VTI reassessment: §3 log entry 2026-06-25.
42. [P1] broad_market_equity_domestic Scenario C conservative bound: UPDATED
    2026-06-30 (Q2 audit). The 2003 Iraq War analog was run (§3 entry
    2026-06-30): it DOES clear the 1990 recession confound (NBER-confirmed
    non-recessionary backdrop + confirmed discrete oil shock), but 2003
    equities ended +28.68% total / ~+26% real — an upside outcome, not a
    downside floor. FINDING: the conservative bound for pure non-recessionary
    C is NOT derivable from a drawdown analog (none exist — non-recessionary
    oil shocks were not equity-drawdown events); current -4 is likely too
    pessimistic but no analog-supportable replacement exists. Conservative
    revision HELD by client decision 2026-06-30 — no value change. Upside
    [-1]→[+6,+8] is HIGH-confidence but disclosure-only, NOT adopted (avoids
    cherry-picking the EV-irrelevant half while the EV-relevant half is open).
    NEXT STEP (re-scoped): this is now a METHODOLOGY decision — how to set a
    non-analog-derivable conservative bound (judgment-based modest floor vs.
    retain -4 as a deliberate safety placeholder) — not further analog search.
    Full detail: §3 entries 2026-06-30 and 2026-06-29 (v1.46 follow-up).
43. [P1] GAP-16 magnitude calibration (re-filed from item 40, 2026-06-30): the
    range-position EV adjustment shifts the conservative value by
    min(25% of range width, 3pp) when both sub-conditions agree. That 25%/3pp
    magnitude is a PROVISIONAL starting point, never run through
    M16.CalibrationMethodology(). The MECHANISM (bounded / agreement-gated /
    table-clamped / conservative-only) is NOT provisional — only these two
    numbers are. NEXT STEP: full 4-layer derivation of the adjustment
    magnitude at a future audit; until then the provisional values stand.
44. [P2] GAP-16 sub-condition map extension (re-filed from item 40, 2026-06-30):
    apply_range_position_adjustment() / clean_signal_role_map() already
    generalize to any role; extending documented sub-condition drivers beyond
    IHP to STF / RAC / IHC is now a pure §11 documentation task (identify 1-2
    governing variables per role, add a sub-condition note) — zero further code
    change. NEXT STEP: assign at a future session.

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
June 4 full session M14 computation (market_data T1 — M18 v1.2 HARD_GATE compliant):
  Re-verification of prior session (Objective 1):
  - BZ=F Feb 25 actual: $70.85 T1. energy_90d May 26: ($97-$70.85)/$70.85 = +36.9%. HIGH confirmed.
  - VIX Feb 25: 17.93 confirmed as actual T1 close (not an estimate). VIX_change_90d -1.23 pts exact.
  Today (June 4):
  - energy_90d: BZ=F $97.81 (Jun 3 T1) vs $92.69 (Mar 6 T1 — 90d anchor) = +5.52% -> NOT FIRING.
    War premium now inside 90d window; below both HIGH (>=15%) and MODERATE (>=10%) thresholds.
  - VIX_change_90d_pts: 16.06 (Jun 3) - 29.49 (Mar 6) = -13.43 pts (<=0; moot).
  - broad_equity_30d: SPY Apr 22->Jun 3 +6.05% >= +5% -> equity_scenario_divergence = HIGH.
  - Composite = HIGH (equity-driven only; commodity_fear_divergence NOT FIRING). Tier unchanged from prior.
  - UnderweightReviewTrigger: NOT fired (all positions within 5pp of sheet targets).

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

**CONFLICT DURATION OVERRIDE (v1.34, June 13, 2026):**
When `conflict_duration_calendar_days > 90` from T1-confirmed conflict onset to session date,
EntryExtensionGuard uses **180d trailing average** as canonical baseline for all
`inflation_hedge_commodity_linked` and `inflation_hedge_precious_metals` roles.
Rationale: when conflict onset is inside the 90d window, both the anchor and current price reflect
war-elevated levels. The 90d comparison becomes war-vs-war rather than pre-war-vs-current, defeating
the guard's purpose. This override applies independently of the M14 energy_90d → energy_180d
divergence signal switch (M14 §open_decisions, June 7).
Implementation: `compute_90d_trailing_avg()` → extend window to 180d when override active; sourcing unchanged.
Active status (June 13, 2026): US-Iran war onset Feb 28, 2026 (T1: AP). Duration = 105 calendar days. **OVERRIDE ACTIVE.**
Deactivation: reset to 90d baseline when conflict formally ends (T1-confirmed signed agreement + 30 calendar days)
or at Q2 audit June 30, whichever is later, after assessing price normalization.

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

### 9.5 Role Repricing Divergence Thresholds (M14.RoleRepricingDivergence — added v1.35)

Advisory signal only. Does not block execution. Emits `InstrumentRepricingWarning` in briefing
when a portfolio instrument underperforms BROAD_EQUITY_TRAILING (30 trading days) by >= threshold.
Applies to all held instruments whose primary role appears in the table below.
All thresholds CALIBRATION_DATED. Provisional — pending June 30 audit.

| Role | Underperformance threshold vs broad market (pp) |
| --- | --- |
| real_asset_contracted_revenue | 10 |
| inflation_hedge_commodity_linked | 15 |
| geopolitical_premium | 20 |
| secular_technology_growth | 10 |
| inflation_hedge_precious_metals | 15 |

Note: threshold is applied to 30-day return differential only.
If holdings 30d returns are unavailable at session time, step is skipped with flag.
Review at June 30 audit: calibrate thresholds to historical role-vs-broad-market volatility.



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
| 2026-05-30 | AIPO | ThematicETF_ClassificationAudit (drift update v1.23) | Sector drift: Industrials 57.09%, IT 16.46%, Utilities 14.42%, Energy 6.91%, FinSvcs 3.60%. PDT-dominant reclassification applied. Binding driver test NOT applied to Industrials. | REVISED v1.23: PDT(0.63)+STG(0.16)+RAC(0.14)+IHC(0.07). EV +2.16%→+0.13% (→v1.27: +0.13%). Ranked ~#10. ⚠ PDT assignment to commercial Industrials was an error — corrected v1.30. |
| 2026-06-02 | AIPO | ThematicETF_ClassificationAudit (full T1 re-audit v1.30) | Full 77-holding audit from Defiance ETFs official page, $750.87M AUM. Industrials confirmed commercial RAC (hyperscaler/utility demand binding driver; NOT legislative mandate). GEV confirmed Industrials/RAC. CCJ 3.78% + 4 other uranium names confirmed IHC. Bitcoin miners: 11 holdings ~7% NAV, no M15 role registered, Option A adopted (UNCLASSIFIED at 0% EV). | REVISED v1.30: RAC(0.55)+STG(0.16)+IHC(0.11)+PDT(0.04)+UNCLASSIFIED(0.07). EV corrected +0.13%→+3.28% (operative §4.1 values). Rank: #3. Q3: create bitcoin_mining role (§6 item pending). |

---

## Section 11 - Instrument Classification Registry (M15)

All values CALIBRATION_DATED. First audit: June 30, 2026.
VTI, XAR, MLPX, SGOL, SGOV, PAVE added Apr 28 (v1.7). AIPO, MAGS added Apr 30 (v1.9). AIPO §11 data updated May 6 (v1.10). MLPX EV updated May 6 (v1.11). New roles inflation_linked_sovereign and real_estate_equity_income added May 6 (v1.12). Five new roles added May 6 (v1.13): systematic_trend_following, consumer_defensive_equity, healthcare_defensive_equity, floating_rate_credit_income, emerging_market_equity. New instruments added May 6 (v1.13): DBMF, SIVR, COPX, VTIP, XLP, VNQ, VEA, XLV, FLOT. AIPO reclassified May 7 (v1.14): ThematicETF_ClassificationAudit() COMPLETE. MLPX entry guards CLEARED May 13 (v1.17). Gold reallocation targets confirmed executed May 22 (v1.18). EVs updated at new probability vector May 25 (v1.19): A=7/B=36/C=41/D=5/E=4/F=7. SIVR EV arithmetic corrected May 26 (v1.21): B blended 5.70%→6.00%, total EV +2.92%→+3.03%. AIPO fully re-audited June 2 (v1.30): RAC(0.55)+STG(0.16)+IHC(0.11)+PDT(0.04)+UNCLASSIFIED(0.07 bitcoin miners); EV +3.28%.

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
| broad_market_equity_domestic | domestic_aggregate_economic_growth | v1.0 | Active - B ADOPTED HIGH confidence (v1.45, June 29, 2026): [-8,-2]→[-2,+5]. Acute-shock vs. sustained-grind bifurcation resolved — mechanism is rate-change not rate-level; current regime is rate-stable (Fed at terminal, holding) not rate-shock, so acute analogs (1973-74, 2022) don't apply. A ADOPTED [10,20] (v1.48, June 30, 2026, HIGH — 1991/2003 analogs T1-verified). C: 2003 Iraq analog run at the audit (v1.48) — clears the 1990 recession confound but 2003 ended strongly positive, so it confirms only the upside; conservative bound HELD unresolved (not derivable from a drawdown analog — non-recessionary oil shocks were not drawdown events), upside [-1]→[+6,+8] HIGH but disclosure-only, NOT adopted. See §6 item 42 / §3 2026-06-30. D/E/F reviewed and confirmed. |
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

CURRENT OPERATIVE VALUES: B=[-2,+4]★ ADOPTED HIGH confidence (v1.27, June 1, 2026). See §4.1 table for full row.
⚠ Vanguard VCMM (Mar 2026): 2.3%-4.3% nominal (0%-2% real) for U.S. growth equities over 10yr — unconditional pessimistic anchor. Research Affiliates: 3.1% nominal U.S. large cap. GMO: -6% real U.S. large cap 7yr.
NOTE: §4.1 is authoritative for return values. This table shows operative values only; refer to §4.1 footnotes for full M16 derivation.

| Scenario | Conservative | Upside | Status | Rationale |
| --- | --- | --- | --- | --- |
| A | 6% | 16% | ⚑ provisional | Fed cuts; AI capex expands; multiple expansion |
| B | -2% | +4% | ★ ADOPTED HIGH (v1.27) | Q1 2026 as sustained B analogue confirmed; contract lock-in; [-12,-3] REJECTED. |
| C | +2% | +8% | ⚑ provisional | Q1 2026 empirical: Azure +40%, AWS +28%, META +33%. AI enterprise contracts multi-year. Single data point; audit June 30. |
| D | -6% | 0% | ⚑ PENDING June 30 | 2008-09 2yr annualized NDX -5.1% real. 1 analogue. Rederived from [-20,-8] (was 1yr acute — wrong convention). |
| E | -12% | -3% | ⚑ PENDING June 30 | 2008 Q4 acute annualized. 1 analogue. Rederived from [-18,-6]. |
| F | 4% | 11% | ⚑ PENDING June 30 | Strong nominal demand; rising rates partially compress multiples. Proposed revision [8,20] logged 2026-06-25 (MEDIUM confidence) — two clean multi-year QQQ analogs (2017-19, 2023-24) support a materially higher range; capex-sustainability structural risk (§6 item 37) argues against adopting the raw historical average. Current operative value [4,11] unchanged pending formal adoption. Full 4-layer detail: §3 log 2026-06-25; §6 item 23[15]. |

### 11.3 Instrument Classification Table

#### VTI
- Components: broad_market_equity_domestic (0.78) + secular_technology_growth (0.22)
- passive_mandate_eligible: true
- Last reviewed: 2026-04-28
- NOTE: VTI ELIMINATED from all target allocations as of April 30, 2026 (v1.9). Existing positions to be sold during rebalancing. Section 11 entry retained for blendedScenarioReturn() computation during transition period.

#### XAR
- Components: geopolitical_premium (0.90) + broad_market_equity_domestic (0.10)
- passive_mandate_eligible: false
- ThematicETF_ClassificationAudit COMPLETED April 29. Confirmed.
- Last reviewed: 2026-05-30 (v1.23 — staleness check complete; classification confirmed)
- ⚠ Valuation note: Forward P/E ~35.5x (war-premium elevated; within thesis range for geopolitical_premium; peacetime norm 18-22x. Watch for compression if A-probability rises above 20%. 66.59x trailing PE seen in some sources is a stale artifact — use forward PE only.)
- EV: computed fresh each session via M15.blendedScenarioReturn() (ENG-7) -- not stored here; see live computation each session.
- Target: 12% structural across applicable accounts (Primary IRA, Primary Roth, Taxable Acc4). CONFIRMED AT TARGET.
- Client preference: exit excess XAR at ~$265 on a conflict-resumption spike. EXECUTED — reduction to 12% confirmed via allocation sheet May 6.
- HoldJustification: break-even peace probability <5.6%; opportunity cost vs MLPX -4.21%/year (at v1.19 probs).
- ⚠ Deal trajectory (A rising): geopolitical_premium A return proposed revision to [-6,0] pending June 30. If adopted, XAR EV would decline further.

#### MLPX
- Components: real_asset_contracted_revenue (0.50) + inflation_hedge_commodity_linked (0.50)
- passive_mandate_eligible: false
- Last reviewed: 2026-06-15 (v1.36 — ComponentVector revised RAC(0.65)/IHC(0.35)→RAC(0.50)/IHC(0.50); M16 4-layer complete; client confirmed)
- EV: computed fresh each session via M15.blendedScenarioReturn() (ENG-7) -- not stored here; see live computation each session.
  - ⚠ EV improvement vs prior weights (+0.14pp) driven by IHC E=+2% (RESERVE_EROSION) gaining weight vs RAC E=-10%. If IHC E recalibrated negative at June 30 (SYSTEMIC_LIQUIDITY pathway), improvement reverses.
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
- passive_mandate_eligible: false
- Last reviewed: 2026-04-28
- CALIBRATION ANOMALY RESOLVED Apr 30 (v1.8): §4.1 Scenario C revised [+7%,+14%]->[-2%,+6%]. C-hawk regime empirical basis.
- EV: computed fresh each session via M15.blendedScenarioReturn() (ENG-7) -- not stored here; see live computation each session.
- Target allocation (v1.18 CONFIRMED):
  - Primary IRA: 16%
  - Primary Roth: 14%
  - Relative IRA: 20% (CONFIRMED EXECUTED v1.18 — reduced from 26%)
  - Relative Roth: 16% (CONFIRMED EXECUTED v1.18 — reduced from 22%)
  - Note: SIVR added as complement; SGOL + SIVR combined restores precious metals exposure
- ⚠ IHP A and D proposals from prior sessions: ADOPTED v1.27 (A [-2,+2] ★; D [-3,+3] ★). §11 EV updated v1.29.
- **GAP-16 sub-condition drivers (within-scenario range position, v1.42; real-yield driver
  corrected v1.44; PROMOTED FROM ADVISORY-ONLY TO LIVE EV ADJUSTMENT v1.46, June 29, 2026 —
  see §3 v1.46 log entry):** the 2 variables that determine where SGOL lands within a wide
  [conservative, upside] §4.1 band — real yield (REAL_YIELD_10Y_TREND = DGS10 nominal minus
  T10YIE breakeven inflation) direction and DXY direction. Rising real yield + appreciating
  DXY = headwind (tracks toward the conservative end, now applied as a bounded downward
  adjustment to the value blendedScenarioReturn() actually uses); falling real yield +
  weakening DXY = tailwind (bounded upward adjustment, capped at the table's own upside).
  Evaluated each session by analysis/range_position.py; the resulting signal now feeds
  CalibrationState.range_position_signals, which analysis/instruments.py
  blended_scenario_return() consumes via apply_range_position_adjustment() — bounded to
  min(25% of range width, 3pp), only when both sub-conditions agree (never on "mixed" or
  "inconclusive"), only on ranges ≥6pp wide, and the magnitude itself is PROVISIONAL pending
  a formal M16 4-layer calibration of the 25%/3pp parameters at a future audit (the mechanism
  is the v1.46 fix; the specific numbers are a conservative starting point). DXY is the same
  variable tracked as an M19 §13 sustaining/failure condition below (reused, not duplicated);
  the real-yield driver is distinct from THREEFYTP10, which M19 §13 below still uses for its
  own "real yield sustained > 2.0%" condition text (term premium, not the same series — see
  §3 v1.44 log entry for why these were split apart).

#### SGOV
- Components: rate_sensitive_income_short_duration (1.00)
- passive_mandate_eligible: false
- Last reviewed: 2026-06-01 (v1.25 — A and D values adopted HIGH confidence)
- EV: computed fresh each session via M15.blendedScenarioReturn() (ENG-7) -- not stored here; see live computation each session.
- Target allocation (v1.13):
  - Primary Taxable: 15%
  - Taxable Preservation: 100%
  - Relative IRA: 14%
- ✅ A [0,2]→[1,3] ADOPTED HIGH confidence (v1.25). D [0,3]→[1,4] ADOPTED HIGH confidence (v1.25). Original proposals [1,4] and [2,6] rejected — see §4.1 footnote.

#### AIPO
- Components: real_asset_contracted_revenue (0.55) + secular_technology_growth (0.16) + inflation_hedge_commodity_linked (0.11) + policy_driven_thematic_equity (0.04) + UNCLASSIFIED_bitcoin_miners (0.07)
- passive_mandate_eligible: false
- CLASSIFICATION REVISED v1.30 (June 2, 2026): Full T1 re-audit from Defiance ETFs official page, 77 holdings, $750.87M AUM. Three prior errors corrected:
  (1) RAC 0.45→0.55: Commercial infrastructure Industrials (PWR, VRT, ETN, GEV, MTZ, STRL, NVT, HUBB, DY, utilities, data centers) — binding driver is commercial contracts with hyperscalers/utilities, NOT government mandates. GEV confirmed Industrials/RAC (erroneously counted as IT in prior data source).
  (2) IHC 0.05→0.11: Uranium names missed or understated in prior reviews — CCJ 3.78% (largest single uranium position), NXE 0.75%, UUUU 0.50%, DNN 0.44%, LEU 0.44%; also includes Bloom Energy (BE) 4.56% energy technology, EOSE 0.62%, FLNC 0.61% energy storage.
  (3) PDT 0.20→0.04: Only confirmed policy-mandate holdings: BWXT 1.22% (government nuclear), OKLO 0.88%, SMR 0.49%, NNE 0.44%, FCEL 0.98%. All other Industrials fail M08 binding driver test for PDT.
  (4) STG 0.30→0.16: Reflects GEV correction + confirmed semiconductor weights: AVGO 4.25%, NVDA 3.80%, AMD 2.71%, ARM 1.18%, MRVL 1.10%, ALAB, LSCC, RMBS, NBIS.
  UNCLASSIFIED 0.07: Bitcoin miners (~7% NAV) — 11 holdings: HUT, BTDR, HIVE, RIOT, CLSK, CIFR, MARA, CORZ, IREN, WULF, BTBT. No registered M15 role. Option A adopted: flagged UNCLASSIFIED, 0% EV contribution (conservative — likely negative in B/C on energy cost compression; severely negative in D). §6 Q3 action item: create role for bitcoin_mining_hpc / speculative_infrastructure_growth with M16 return table calibration.
  Prior v1.23 classification (PDT 0.63) was itself an error — sector % drift was tracked but binding driver test was not applied; commercial Industrials incorrectly assigned to PDT.
- Basis: Defiance AI & Power Infrastructure ETF. Tracks MarketVector US Listed AI & Power Infrastructure Index. Holdings must derive ≥50% revenue from AI hardware, data centers, or power infrastructure. 77 holdings as of June 2, 2026. AUM: $750.87M. Expense ratio: 0.69%. Inception: 07/24/2025.
- ⚠ NVDA/AVGO overlap with MAGS: AVGO 4.25% + NVDA 3.80% in AIPO → ~0.6-0.9% portfolio combined with MAGS contribution. Not material. Monitor.
- ⚠ PAVE overlap: ETN (Eaton) in both AIPO and PAVE — confirmed immaterial.
- ✅ TRACK RECORD FLAG SUBSTANTIALLY CLOSED (v1.28, June 1, 2026): AUM $750.87M (June 2). Named Best New Thematic ETF at 2026 ETF.com Awards. 12-month milestone: July 24, 2026 (~7.5 weeks). Confirm at June 30.
- Last reviewed: 2026-06-02 (v1.30 — full T1 re-audit)
- EV: computed fresh each session via M15.blendedScenarioReturn() (ENG-7) -- not stored here; see live computation each session.
  - ⚠ UNCLASSIFIED 0.07 (bitcoin miners) treated as 0% in all scenarios — actual contribution unknown, likely negative in B/C/D. True EV may be modestly below +3.28%.
  - ⚠ Session instructions computed +3.54% using stale §4.1 values (RAC D=+2, RAC E=+2, STG B=−6). Corrected to +3.28% using current operative calibration state.
  - NOTE: EV improves further if STG D/E adopted at June 30 (D component currently using operative −14; rederived −6 pending). Adoption of STG D=−6 would shift D contribution to −4.04%×0.05=−0.202% (vs −0.331% now) — net +0.13pp EV improvement.
- TAX PLACEMENT: ALL ACCOUNTS including taxable.
- Target allocation (v1.22, unchanged — see open decision): **7% Primary IRA; 7% Primary Roth**; 8% Primary Taxable; 6% Relative IRA; 10% Relative Roth.
- ⚠️ TARGET REVIEW IN PROGRESS: Client deliberating IRA/Roth 7%→3% + DBMF bump (+4pp). At corrected EV +3.28%, the substitution thesis (DBMF +11.02%) remains strongly dominant in EV terms. EV differential vs DBMF = −7.74pp/year. However, AIPO now holds a valid thesis position at #3 rank. The reduction is still EV-optimal — but AIPO is no longer marginal. Client decision pending; allocation sheet unchanged.
#### MAGS
- Components: secular_technology_growth (0.85) + broad_market_equity_domestic (0.15)
- passive_mandate_eligible: false
- Last reviewed: 2026-05-30 (v1.23 — hold-only override confirmed)
- ⚠ EV deterioration: from −1.77% (C=44, D=3) to −2.17% (C=41, D=5). D scenario deeply negative (−13.70% blended) — increasing D weight amplifies drag. Override remains in force but EV trendline is worsening.
- **HOLD-ONLY OVERRIDE CONFIRMED (v1.23, May 30, 2026): No ADD at EV −2.17%. Override justified solely by absence of positive-EV secular_technology_growth alternative (URA covers RAC/IHC/STG partially; application-layer gap remains unresolved). Revisit if secular_technology_growth B adjudication at June 30 produces a materially different B conservative value.**
- EV: computed fresh each session via M15.blendedScenarioReturn() (ENG-7) -- not stored here; see live computation each session.
  - NOTE: STG B adoption improves MAGS EV from −2.17% to −0.94%. HOLD-only override basis
    partially changes: EV is now −0.94% (below zero but less negative). Override remains in
    force — still negative EV; no secular_technology_growth positive-EV alternative confirmed.
    Revisit at June 30 if STG D/E adoption further affects ranking.
- Target allocation (v1.22): **3% Primary IRA; 4% Primary Roth**; 3% Relative IRA; 8% Relative Roth. (Reduced v1.22 to fund URA addition; EV improvement +0.04pp per account.)
- TAX PLACEMENT: RETIREMENT ACCOUNTS ONLY. Swap structure generates phantom taxable gains in losing years.
- MAGS vs AGIX upgrade evaluation: monitor Anthropic IPO news. Assess at Q3 2026 or earlier on announcement.

#### DBMF
- Components: systematic_trend_following (1.00)
- passive_mandate_eligible: false
- Basis: iMGP DBi Managed Futures Strategy ETF. Actively managed. Replicates top CTA hedge fund portfolios using T-bill collateral + equity/commodity/bond/currency swap agreements. Strategy: systematic trend-following across all major asset classes.
- K-1: NONE — 1940 Act registered fund (ETF structure). No K-1 issued.
- AUM: $3.51B. Expense ratio: 0.85%. Inception: 2019-05-08. 1-year total return: +27.3%.
- Last reviewed: 2026-05-06 (v1.13, initial classification)
- EV: computed fresh each session via M15.blendedScenarioReturn() (ENG-7) -- not stored here; see live computation each session.
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
- passive_mandate_eligible: false
- Basis: Aberdeen Standard Physical Silver Shares ETF. Tracks spot silver price via physical silver bullion. Lower cost alternative to SLV (0.30% ER vs 0.50%)
- AUM: ~$5.5B. Expense ratio: 0.30%. Custodian: ICBC Standard Bank (UK).
- Last reviewed: 2026-05-26 (v1.21 — B-component arithmetic corrected)
- EV: computed fresh each session via M15.blendedScenarioReturn() (ENG-7) -- not stored here; see live computation each session.
- TAX PLACEMENT: Retirement accounts preferred. Physical silver ETF is classified as a collectible; capital gains taxed at 28% max rate in taxable accounts.
- ENTRY EXTENSION GUARD: CLEARED (v1.14, May 7, 2026). 90d trailing average ~$78-82; guard threshold ~$94-98; current ~$71.82 — well below threshold.
- **GAP-16 sub-condition drivers (within-scenario range position, v1.42; real-yield driver
  corrected v1.44; PROMOTED FROM ADVISORY-ONLY TO LIVE EV ADJUSTMENT v1.46):** same two
  drivers as SGOL — real yield (REAL_YIELD_10Y_TREND = DGS10−T10YIE) and DXY direction —
  since SIVR's 0.55 IHP weight inherits the same monetary-debasement mechanism and the same
  bounded EV adjustment mechanics. Evaluated each session by analysis/range_position.py; see
  the SGOL §11.3 entry above for the full v1.46 mechanism description (not repeated here).
- Target allocation (v1.18 CONFIRMED):
  - Primary IRA: 4%
  - Primary Roth: 5%
  - Relative IRA: 6% (CONFIRMED EXECUTED v1.18 — increased from 3%)
  - Relative Roth: 4% (CONFIRMED EXECUTED v1.18 — new position; was 0%)

#### COPX
- Components: inflation_hedge_commodity_linked (0.75) + broad_market_equity_international (0.25)
- passive_mandate_eligible: false
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
- passive_mandate_eligible: false
- Basis: Vanguard Short-Term Inflation-Protected Securities ETF. AUM: $66.6B. Expense ratio: 0.03%. Beta: 0.22.
- Last reviewed: 2026-06-01 (v1.28 — A/D/F adopted HIGH confidence; B/C/E remain MEDIUM)
- EV: computed fresh each session via M15.blendedScenarioReturn() (ENG-7) -- not stored here; see live computation each session.
- TAX PLACEMENT: RETIREMENT ACCOUNTS ONLY. Inflation accrual on TIPS taxed as ordinary income annually.
- ENTRY EXTENSION GUARD: N/A.
- Target allocation (v1.13): 8% Primary IRA; 10% Primary Roth; 12% Relative IRA; 10% Relative Roth.

#### XLP
- Components: consumer_defensive_equity (1.00)
- passive_mandate_eligible: false
- Basis: State Street Consumer Staples Select Sector SPDR ETF. AUM: $14.5B. Expense ratio: 0.08%. 100% US domestic.
- Last reviewed: 2026-05-06 (v1.13, initial classification)
- EV: computed fresh each session via M15.blendedScenarioReturn() (ENG-7) -- not stored here; see live computation each session.
- TAX PLACEMENT: ALL ACCOUNTS.
- ENTRY EXTENSION GUARD: N/A.
- Target allocation (v1.13): 7% Primary Taxable.

---

### 11.4 Candidate Instruments (Not Currently Allocated)
<!-- These instruments have registered roles and §11 classification entries but no active target allocations.
     They are distinct from §11.3 active instruments. Do NOT include in ValidateClassifications() HARD_STOP check.
     Do NOT include in EV rank tables or FeasibilityCheck() computations unless specifically evaluating for addition.
     Adoption triggers are listed per instrument. M07 screens and §4.1 calibration may be incomplete. -->

#### VNQ
- Components: real_estate_equity_income (0.60) + rate_sensitive_income_long_duration (0.22) + secular_technology_growth (0.12) + broad_market_equity_domestic (0.06)
- passive_mandate_eligible: false
- Last reviewed: 2026-05-06 (v1.13, initial classification)
- EV at current probs (real_estate_equity_income [TBD] — LOW confidence): -4.52% to +1.27% depending on §4.1 calibration outcome.
- STRUCTURAL NOTE: VNQ is ADVERSARIAL to current B/C dominant distribution. Modern REIT leverage (40-60% LTV) causes cap rate expansion to overwhelm rental income growth in elevated-rate environments.
- TAX PLACEMENT: RETIREMENT ACCOUNTS ONLY (REIT distributions predominantly ordinary income).
- ADOPTION TRIGGER: A > 25% on T1-confirmed US-Iran deal.
- CURRENT PORTFOLIO ALLOCATION: NONE.

#### VEA
- Components: broad_market_equity_international (1.00)
- passive_mandate_eligible: true
- Last reviewed: 2026-05-06 (v1.13, initial classification)
- EV at current probs: approximately **−3.40%** (B/C dominant; international equity faces energy-importer FX drag).
- ADOPTION TRIGGER: A > 25% on T1-confirmed deal.
- CURRENT PORTFOLIO ALLOCATION: NONE.

#### XLV
- Components: healthcare_defensive_equity (1.00)
- passive_mandate_eligible: false
- Last reviewed: 2026-05-06 (v1.13, initial classification — provisional)
- Provisional EV (§4.1 ALL PENDING): approximately −0.44% at current probs.
- TAX PLACEMENT: ALL ACCOUNTS.
- CURRENT PORTFOLIO ALLOCATION: NONE.

#### FLOT
- Components: floating_rate_credit_income (1.00)
- passive_mandate_eligible: false
- Last reviewed: 2026-05-06 (v1.13, initial classification — full M07 screen pending)
- Provisional EV (§4.1 ALL PENDING): approximately +0.2-0.5% above SGOV in B.
- KEY RISK: D/E scenario credit spread blowout vs SGOV pure Treasury safety.
- TAX PLACEMENT: ALL ACCOUNTS.
- CURRENT PORTFOLIO ALLOCATION: NONE.

#### RSP
- Components: broad_market_equity_domestic (0.92) + secular_technology_growth (0.08)
- Basis: Invesco S&P 500 Equal Weight ETF. Equal-weights all ~500 S&P 500
  constituents quarterly. AUM: $89.1B. Expense ratio: 0.20%. Inception:
  Apr 24, 2003 (~23yr track record).
- M07 STATUS: PASS. No foreign concentration (US large-cap only). No K-1 —
  standard RIC, 99.78% direct equity per SEC NPORT-P (Jan 31, 2026); ~0.2%
  E-mini S&P 500 Equal Weight futures overlay for cash equitization only.
- Classification basis (2026-06-25, sector-bucket level, NOT a full 500-name
  binding-driver audit — MEDIUM confidence): SEC NPORT-P holdings confirm
  equal-weighting dilutes AI/mega-cap concentration far more than a generic
  "Technology + Communication Services = STG" assumption would suggest.
  RSP's Communication Services sub-weight (3.91%) sits alongside AT&T,
  Charter, Comcast, Electronic Arts, Fox at equal weight with Alphabet — the
  dedicated RSPC sub-fund's top 10 holdings (Warner Bros. Discovery,
  Paramount Skydance, EA, Interpublic, Omnicom, Trade Desk, Take-Two,
  Charter, TKO, Verizon) confirm this sector is media/telecom/ad-driven, not
  AI-driven, at equal weight. ~8% STG attribution reflects the residual
  AI-adjacent slice within Technology/Communication Services even diluted
  this way; the other ~92% is genuinely undifferentiated domestic growth —
  exactly the clean BMED proxy the framework needs.
- EV (today's session vector, current OPERATIVE §4.1 values): **≈ -0.87%**.
  Worse than VTI (-0.66%). Under the two PENDING (NOT adopted) proposals
  from today's BMED/STG-F review: ≈ -0.22% — improves, stays negative.
  Counterintuitive given RSP is the structurally "cleanest" diversification
  play of the three candidates — it loses precisely because BMED's current
  B value (-8%) is punishing and RSP carries almost no STG slice to offset
  it (STG B = -2, already HIGH-confidence adopted), unlike VTI/QQQM/MAGS.
  This is itself a reason the open B question (§3 log 2026-06-25) matters:
  if B's true value sits closer to the "sustained grind" historical read
  than the "acute shock" read, RSP's case changes materially.
- NOT ADOPTABLE this session — negative EV under current and pending values.
- ENTRY EXTENSION GUARD (2026-06-25, yfinance T1, 62 trading days in the
  trailing-90-calendar-day window): current $210.38 (Jun 24) vs 90d trailing
  avg $203.22 = +3.52% above avg. Threshold (broad_market_equity_domestic,
  dominant role at 92% weight): 15%. CLEARS comfortably — price level is not
  the blocker here; the negative EV is.
- ADOPTION TRIGGER: B scenario bifurcation (above) resolved toward the
  less-punishing historical read, or a specific risk-management thesis
  (lower concentration vs. MAGS/AIPO) independent of EV ranking.
- CURRENT PORTFOLIO ALLOCATION: NONE.

#### QQQM
- Components: secular_technology_growth (0.75) + broad_market_equity_domestic (0.25)
- Basis: Invesco NASDAQ-100 ETF. Modified market-cap-weighted, 100 largest
  non-financial Nasdaq companies. AUM: $82.9B. Expense ratio: 0.15%.
  Inception: Oct 13, 2020 (~5.7yr track record).
- M07 STATUS: PASS. No foreign concentration concern. No K-1 (standard RIC).
- Classification basis (2026-06-25, sector-bucket level, MEDIUM confidence):
  top 10 holdings = 47.4% of fund (NVDA 8.14%, AAPL 7.27%, MSFT 5.31%,
  MU 4.79%, AMZN 4.61%, AMD 3.69%, GOOGL 3.51%, TSLA 3.45%, AVGO 3.36%,
  GOOG 3.25%) — almost entirely AI-capex/mega-cap names. Sector weights:
  Technology 58.65% (~95% STG), Communication Services 14.28% (~90% STG,
  GOOGL/GOOG-driven), Consumer Cyclical 11.43% (~60% STG — AMZN/AWS +
  TSLA's AI/robotics narrative), remainder (Consumer Defensive, Healthcare,
  Industrials, Utilities, Basic Materials ≈ 15%) BMED.
  CORRECTION to this session's earlier (unverified, asserted-not-computed)
  claim that QQQM is "more concentrated in STG than MAGS": wrong once
  actually classified. QQQM (0.75 STG) is LESS concentrated than MAGS
  (0.85 STG) — MAGS's "Magnificent 7" holds zero non-tech-adjacent
  diversification, while QQQM's 100 holdings include genuine (if
  minority-weighted) healthcare/industrials/utilities exposure.
- EV (today's session vector, current OPERATIVE §4.1 values): **≈ +0.29%**.
  Between MAGS (+0.47%) and VTI (-0.66%). Under the PENDING STG-F proposal
  alone: ≈ +1.32% — similar proportional uplift to MAGS, both being
  STG-heavy.
- NOT ADOPTABLE as a complement to MAGS — same binding driver, redundant
  exposure, slightly worse current EV. Would only make sense as a
  REPLACEMENT for MAGS (broader diversification, lower single-name
  concentration, marginally worse EV) — a risk-management tradeoff, not an
  EV-improvement case.
- ENTRY EXTENSION GUARD (2026-06-25, yfinance T1, 62 trading days in the
  trailing-90-calendar-day window): current $292.63 (Jun 24) vs 90d trailing
  avg $279.22 = +4.80% above avg. Threshold (secular_technology_growth,
  dominant role at 75% weight): 20%. CLEARS comfortably.
- CURRENT PORTFOLIO ALLOCATION: NONE.

#### SCHD
- Components: broad_market_equity_domestic (0.49) + consumer_defensive_equity (0.18) + healthcare_defensive_equity (0.16) + inflation_hedge_commodity_linked (0.17)
- Basis: Schwab U.S. Dividend Equity ETF. Tracks Dow Jones U.S. Dividend 100
  Index — ~100-103 US stocks screened for cash flow, ROE, dividend yield, and
  5yr dividend growth; 10yr consecutive dividend-payment requirement; 25%
  sector cap; excludes REITs. AUM: $96.0B. Expense ratio: 0.06%. Inception:
  Oct 20, 2011 (~14.7yr track record).
- M07 STATUS: PASS. No foreign concentration (US-domiciled only). No K-1 —
  standard RIC. Fund-level revenue is not commodity-dependent (energy
  *holdings* sit inside the IHC bucket below; the fund itself is equity).
- passive_mandate_eligible: true (sector-screened index fund; no active
  management or single-theme concentration beyond the dividend-quality screen)
- Classification basis (2026-06-29, sector-bucket level, fresh search this
  session, post-Q2-2026-rebalance snapshot as of 06/24/2026 — NOT a full
  103-name binding-driver audit, MEDIUM confidence): top holdings post-rebalance
  are Home Depot (4.42%), Merck, Procter & Gamble, Abbott, Amgen, ConocoPhillips,
  Chevron, Verizon — a materially different mix from RSP/VTI/QQQM. Sector
  composition: Energy ~17-19% (CVX, COP — commodity-price-linked revenue) ->
  IHC; Consumer Staples ~17-20% (KO, PEP, PG, CL — brand moat, demand
  inelasticity, the textbook consumer_defensive_equity driver) -> 0.18 used;
  Health Care ~15-17% (MRK, AMGN, ABT, UNH, BMY — pharmaceutical pricing
  power / demand inelasticity) -> 0.16 used; residual ~49% (Industrials ~12%,
  Financials ~6-9% — cut roughly in half since a March 2026 reconstitution,
  Consumer Discretionary ~10%, Information Technology ~7-11% — TXN/QCOM,
  mature dividend-paying semis, NOT AI-capex/mega-cap growth names, excluded
  from STG on the same binding-driver grounds AIPO's non-RAC Industrials were,
  Communication Services ~4%, Materials ~3%, Utilities ~0%) -> BMED as
  undifferentiated domestic growth. Sources: Schwab official holdings page,
  ETF Database sector table, TopDividendETFs Q2-2026-rebalance breakdown
  (06/24/2026).
- EV: computed fresh each session via M15.blendedScenarioReturn() (ENG-7) —
  not stored here; see live computation each session.
- CAVEAT — provisional on two independent counts (was three; BMED B ADOPTED
  HIGH confidence v1.45, June 29, 2026 — see below): healthcare_defensive_equity
  ALL six scenarios PENDING June 30 (MEDIUM confidence, never run through M16
  4-layer); consumer_defensive_equity D/E/F PENDING June 30. SCHD's EV is
  downstream of two separate open calibration questions simultaneously — still
  more exposed to the June 30 audit outcome than RSP/VTI/QQQM (BMED now
  resolved for those too) or MLPX/DBMF/AIPO (none open).
- ENTRY EXTENSION GUARD (2026-06-29, market_data_mcp T1, 63 trading days in
  the trailing-90-calendar-day window): current $32.09 (Jun 26) vs 90d
  trailing avg $31.43 = +2.11% above avg. Threshold (broad_market_equity_domestic,
  dominant role at 49% weight): 15%. CLEARS comfortably.
- ADOPTION TRIGGER: none set — candidate under evaluation per client request
  (index-fund simplification review, June 29, 2026 session). Not adoptable
  until the two PENDING dependencies above are resolved at the June 30 audit.
- CURRENT PORTFOLIO ALLOCATION: NONE.

#### URA
- Components: real_asset_contracted_revenue (0.50) + inflation_hedge_commodity_linked (0.30) + secular_technology_growth (0.20)
- passive_mandate_eligible: false
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

#### INFL
- Components: inflation_hedge_precious_metals (0.25) + inflation_hedge_commodity_linked (0.50) + real_asset_contracted_revenue (0.20) + secular_technology_growth (0.05)
- passive_mandate_eligible: false
- Basis: Horizon Kinetics Inflation Beneficiaries ETF. Actively managed, ~51 holdings. $1.45B AUM.
  Invests in companies that earn revenues which rise with inflation without commensurate cost increases:
  precious metal royalty streamers (WPM, FNV, OR Royalties), land/mineral royalties (TPL, LB, PSK, VNOM),
  energy infrastructure royalties (WBI, LNG), uranium (CCO), and AI power adjacency (nuclear/utilities).
- ThematicETF_ClassificationAudit COMPLETE (June 13, 2026, v1.34):
  Sectors: Energy 41.5%, Financial Services (royalty streamers) 25%, Basic Materials 22%, Other 11.5%.
  Top 10 (48.9% NAV): WPM 6.2%, TPL 6.1%, LB 5.9%, FNV 5.0%, PSK 5.0%, VNOM 4.9%, WBI 4.6%, CCO 4.0%, OR 3.7%, LNG 3.4%.
  IHP (0.25): WPM, FNV, OR Royalties — precious metal royalty streamers. Revenue = % of metals produced × spot price.
  CL (0.50): TPL, LB, PSK, VNOM, energy royalty residual — land/mineral royalties + energy royalties.
    ⚑ TPL and LandBridge classified as CL (not RAC): revenue = royalty_rate × commodity_price × volume;
    not fixed-fee. Zero capex = high quality within CL. D conservative floor likely -5% (vs -8% for miners);
    refine at Q2 with royalty sub-tier note.
  RAC (0.20): WBI (water infrastructure), CCO (uranium contracts), LNG (long-term supply contracts), utilities.
  STG (0.05): nuclear/AI power adjacency (CCO nuclear demand, Bloom Energy, energy storage).
  UNCLASSIFIED: 0.00 — fully classified.
- AUM: $1.45B. ER: 0.85%. Inception: Jan 11, 2021 (5.4yr track record). Portfolio turnover ~9% (low).
- M07 STATUS: PASS. AUM ✓. ER 0.85% — elevated but consistent with active management ✓. Track record ✓.
  ⚑ Foreign exposure: FNV, WPM dual-listed TSX; PSK Toronto-listed. FLAG retained but does NOT
  disqualify taxable — these are equity distributions (qualified dividends), not foreign withholding issue.
  Equity ETF structure, 1099 (not K-1), no phantom income ✓.
- EV (A=18.8/B=37.6/C=25.1/D=3.0/E=12.5/F=3.0 — current session confirmed vector):
  Scenario blended returns (conservative):
    A: IHP(-2)×25% + CL(2)×50% + RAC(3)×20% + STG(6)×5% = +1.40%
    B: IHP(6)×25% + CL(6)×50% + RAC(6)×20% + STG(-2)×5% = +5.60%
    C: IHP(-2)×25% + CL(7)×50% + RAC(8)×20% + STG(2)×5% = +4.70%
    D: IHP(-3)×25% + CL(-8)×50% + RAC(-6)×20% + STG(-6)×5% = -6.25%
    E: IHP(10)×25% + CL(2)×50% + RAC(-10)×20% + STG(-12)×5% = +0.90%
    F: IHP(-3)×25% + CL(2)×50% + RAC(3)×20% + STG(4)×5% = +1.05%
  EV: 18.8%(1.40)+37.6%(5.60)+25.1%(4.70)+3.0%(-6.25)+12.5%(0.90)+3.0%(1.05) = **+3.51%** → Ranked #4.
  Note: EV was computed at the June 13, 2026 session probability vector. Recompute at Q2 if vector shifts >5pp.
- TAX PLACEMENT: ALL ACCOUNTS eligible (qualified dividend equity ETF; no K-1; no phantom income).
- ENTRY EXTENSION GUARD (checked June 13, 2026 under §9.3 CONFLICT DURATION OVERRIDE — 180d baseline):
  INFL 180d trailing avg (approx Dec 14, 2025–Jun 13, 2026): ≈ $47.00.
  Current: $51.02. Premium above 180d avg: ≈ +8.5%. Threshold: 20%. **CLEARS.**
- Structural thesis: Royalty and zero-capex companies earn revenues that pass through inflation directly.
  Distinct from COPX (miners with extraction cost exposure) and MLPX (fixed-fee toll roads).
  Adds precious metal streaming layer (WPM/FNV) and land royalty layer (TPL/LB) not currently in framework.
- Last reviewed: 2026-06-13 (v1.34 — initial classification; CANDIDATE status, pending allocation execution)
- Proposed target allocation (pending client confirmation and allocation sheet update):
  - Primary IRA: 3% (funded from XAR 12%→9%)
  - Primary Roth: 3% (funded from XAR 12%→9%)
  - Primary Taxable (Acc4): 2% (funded from COPX 7%→5%)
  - Acc3 (PRESERVATION): EXCLUDED — equity ETF incompatible with floor_nominal_loss=TRUE
  - Relative accounts: NOT evaluated this session

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

Governing module: M17_SystemicCascadeWarning.md. §12.1-12.4 structure and
ACTIVE_STATUS prose added 2026-06-20 (ENG-18) — see FRAMEWORK_BACKLOG.md
for full rationale.

### 12.1 Agriculture / Fertilizer Chain (CHAIN_1)

| Parameter | Alert Threshold | Notes |
| --- | --- | --- |
| farm_filings_alert | +50% YoY farm chapter 12 bankruptcies | ⚠ PENDING formal calibration (Q2 audit) — current default, not yet M16-derived |
| natgas_alert | $6.00/mmBtu sustained 30 days | ⚠ PENDING formal calibration (Q2 audit) |
| fertilizer_alert | +50% above 12-month average | ⚠ PENDING formal calibration (Q2 audit) |

ACTIVE_STATUS (per M17.md, moved here 2026-06-20): ELEVATED — chapter 12 filings
+46% YoY 2025 (below +50% threshold — NOT fired); farm debt record $624.7B;
natgas $2.71/mmBtu (well below $6.00 threshold — NOT fired); urea +33% since
March 2026 conflict (below +50% fertilizer threshold — NOT fired); anhydrous
ammonia $860/ton projected fall 2026.

### 12.2 CRE / Regional Bank Chain (CHAIN_2)

| Parameter | Alert Threshold | Notes |
| --- | --- | --- |
| KRE_alert | KRE −15% vs SPX over 90 days | ⚠ PENDING formal calibration (Q2 audit) — current default |
| SOFR_DFF_alert | SOFR–DFF spread +10 bp sustained 5 days | ⚠ PENDING formal calibration (Q2 audit) |

ACTIVE_STATUS (per M17.md, moved here 2026-06-20): ELEVATED — CMBS delinquency
6.59% (Q3 2025); $930B maturity wall 2026; SOFR–DFF benign at −11 bp (below
+10bp threshold and in fact negative — NOT fired); KRE not yet showing
underperformance vs SPX (NOT fired).

### 12.3 Private Credit / Margin Chain (CHAIN_3, two-mode — v1.20)

| Mode | Parameter | Threshold | Score | Current Status |
| --- | --- | --- | --- | --- |
| WATCH | margin_at_nominal_record | FINRA margin debt at all-time nominal high | 0 | WATCH — $1.304T record loaded (April 2026) |
| FIRES | margin_MoM_decline | ≤ −5% MoM after record high | +1 | NOT fired — current +6.8% MoM |
| FIRES | gate_count_alert | 3+ named fund gate/suspension events in 90 days | +1 | NOT fired — 2/3 observed |

ACTIVE_STATUS (per M17.md, moved here 2026-06-20): ELEVATED — margin debt
$1.304T all-time nominal record (April 2026); net credit balance −$871B near
record low; CLO OC breach and gate events observed (2 of the 3+ FIRES
threshold). Both threshold values above are ⚠ PENDING formal calibration
(Q2 audit) — current defaults.

### 12.4 Manufacturing / Corporate Stress Chain (CHAIN_4)

| Parameter | Alert Threshold | Confidence | Notes |
| --- | --- | --- | --- |
| bankruptcy_quarterly_WATCH | ≥220/quarter | HIGH ★ | M16 4-layer complete, v1.24 (June 1, 2026) |
| bankruptcy_quarterly_FIRES | ≥300/quarter | HIGH ★ | M16 4-layer complete, v1.24. Prior 800/quarter threshold eliminated same revision — see Section 3 log entry 38. |

ACTIVE_STATUS (per M17.md, moved here 2026-06-20): ELEVATED — corporate
bankruptcy pace 14-year high in 2025; manufacturing 3% below April 2018 peak;
PE leverage elevated. Current Q1 2026 = 188/quarter — BELOW WATCH (≥220).
ABI/Epiq AACER T1-equivalent source confirmed.

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

---

## Section 13 - M19 Thesis Sustaining Conditions

Governing module: M19_ThesisSustainingConditions.md (v1.2, added June 17, 2026;
preamble methodology moved here 2026-06-19, ENG-9). Status taxonomy, briefing-
suppression behavior, and excluded-role scope are defined there (ENUM ThesisStatus,
BRIEFING BLOCK, and the SCOPE section) — not duplicated per ticker here.
Conditions reference role IDs, DataReading keys, and M02 QualitativeGatherList keys
only — no evaluation logic lives in this section; M19 reads these values and never
hardcodes them.

All values CALIBRATION_DATED. First audit: June 30, 2026.

DBMF: {
  primary_driver: "systematic_trend_following — sustained directional macro trends"
  sustaining_conditions: [
    "B+C combined probability >= 55%",
    "≥2 of {BZUSD, GCUSD, DXY, ^GSPC} trending directionally over rolling 8-week window
     (directional = net move >= 8% in one direction without full reversal)"
  ]
  failure_signals: [
    "DBMF_3M_return < -3% while B+C >= 55% (instrument underperforming own scenario)",
    "All 4 tracked markets in mean-reversion mode simultaneously for >= 4 consecutive weeks"
  ]
  data_dependencies: ["DBMF", "BZUSD", "GCUSD", "DXY_INDEX", "^GSPC"]
  last_reviewed: "2026-07-03"
  notes: "DBMF is a replication product — composition changes continuously.
          Trend quality evaluation requires market-level signals, not DBMF price alone."
  evaluation_2026_07_03: "First formal evaluation since TSC creation (2026-06-17),
          client-prompted (T1 price-vs-calibration cross-check). Condition 1 (B+C>=55%)
          NOT MET — actual 48.5% (A=13.86/B=34.64/C=13.86/D=3/E=6.93/F=27.71). Condition 2
          (>=2 of 4 trending, 8wk window, T1 market_data_mcp) MET at the margin: BZUSD -34%
          smooth decline (trending), GCUSD -9.7% smooth decline (trending); DXY +1.6% flat
          (NOT trending); ^GSPC/VTI proxy shows two V-shaped reversals within the window
          (whipsaw, NOT a clean trend). Neither failure_signal fired (DBMF 3M return ~flat,
          not <-3%; not all 4 markets in reversion). NET STATUS: DEGRADED — same category as
          MLPX, not FAILED. Context: 2022's B/C analog carried DBMF's return via a clean
          9-month DXY trend (+18.5%) plus the fastest Fed hiking cycle in 40yr, DESPITE choppy
          equities that year (RSP had larger intra-year swings than today) — so equity
          behavior was never the relevant test; today's DXY specifically lacks 2022's
          breadth. §4.1 B=[+15,+30]/C=[+18,+35] VALUES themselves are not disputed by this —
          the M16 4-layer analog basis is unchanged. This is a sustaining-condition finding,
          not a return-table revision, and does not require M16.CalibrationMethodology()."
}

SGOL: {
  primary_driver: "inflation_hedge_precious_metals — monetary debasement + sovereign reserve demand"
  sustaining_conditions: [
    "10Y real yield (THREEFYTP10) <= 1.5% (above this level gold faces structural headwind)",
    "DXY not in sustained appreciation trend >= 8 consecutive weeks",
    "Central bank reserve accumulation narrative intact (M02.cb_gold_reserve_accumulation —
     T2 qualitative check)"
  ]
  failure_signals: [
    "THREEFYTP10 > 2.0% sustained >= 4 weeks",
    "DXY appreciation > 8% over 8 weeks",
    "Deflationary shock onset (Scenario E probability >= 20%)"
  ]
  data_dependencies: ["GCUSD", "THREEFYTP10", "DXY_INDEX"]
  last_reviewed: "2026-06-17"
  notes: "SIVR is written as its own full standalone block below (no INHERITS shorthand —
          every §13 entry stays independently grep-able). It shares this core mechanism;
          its industrial-demand sensitivity is captured as a SIVR-specific failure signal."
}

SIVR: {
  primary_driver: "inflation_hedge_precious_metals — monetary debasement + sovereign reserve demand
                   (shares SGOL's mechanism; adds industrial demand sensitivity)"
  sustaining_conditions: [
    "10Y real yield (THREEFYTP10) <= 1.5% (above this level precious metals face structural headwind)",
    "DXY not in sustained appreciation trend >= 8 consecutive weeks",
    "Central bank reserve accumulation narrative intact (M02.cb_gold_reserve_accumulation —
     T2 qualitative check)"
  ]
  failure_signals: [
    "THREEFYTP10 > 2.0% sustained >= 4 weeks",
    "DXY appreciation > 8% over 8 weeks",
    "Deflationary shock onset (Scenario E probability >= 20%)",
    "COPX sustained decline > 15% over 8 weeks (SIVR-specific: industrial demand proxy degradation)"
  ]
  data_dependencies: ["SIVR", "THREEFYTP10", "DXY_INDEX", "COPX"]
  last_reviewed: "2026-06-17"
  notes: "Full standalone block, not inherited from SGOL — kept duplicated intentionally for
          grep-ability. Silver's additional industrial-demand sensitivity is captured via the
          COPX-proxy failure signal rather than a separate copper data dependency."
}

MLPX: {
  primary_driver: "real_asset_contracted_revenue — energy infrastructure cash flow stability"
  sustaining_conditions: [
    "BZUSD >= 70 (approximate floor for pipeline distribution sustainability)",
    "B+C combined probability >= 50% (energy demand and supply constraint scenario)"
  ]
  degraded_signals: [
    "B+C combined probability < 50% without Scenario D rising → tailwind fading, not thesis
     failure — contracted throughput still insulates against a soft regime decline"
  ]
  failure_signals: [
    "BZUSD sustained < 65 for >= 6 consecutive weeks",
    "Scenario D probability >= 30% (demand collapse threatens throughput)"
  ]
  data_dependencies: ["BZUSD", "MLPX"]
  last_reviewed: "2026-06-17"
  notes: "MLPX distributions partially protected by contracted throughput — floor is
          lower than spot commodity exposure. Monitor TTM distribution vs carry assumption.
          sustaining_conditions and failure_signals are intentionally asymmetric: a soft B+C
          fade alone is DEGRADED, not FAILED; only an active D-driven demand shock fails
          the thesis outright. Confirmed intentional by client, June 17, 2026."
}

XAR: {
  primary_driver: "policy_driven_thematic_equity (geopolitical_premium) — active conflict
                   + defense budget trajectory"
  sustaining_conditions: [
    "Active US-Iran conflict status OR equivalent elevated geopolitical threat
     (M02.active_conflict_status / M02.escalation_or_deescalation — T1/T2 verified)",
    "Defense budget trajectory positive (not subject to emergency cuts)"
  ]
  failure_signals: [
    "Iran MOU signed AND Hormuz traffic confirmed reopened (T1 verified)",
    "Major de-escalation event reducing geopolitical premium — advisor judgment required
     (M19 Call 2 ScoringQuestion, fed by M02.active_conflict_status — no separate AI boundary)"
  ]
  data_dependencies: ["XAR", "M02.active_conflict_status"]
  last_reviewed: "2026-06-17"
  notes: "XAR thesis is binary on Hormuz status. Iran deal signing is the primary
          single-point failure event. Monitor MOU status each session — June 14, 2026 peace
          deal announcement is a live test case; formal signing expected June 19, not yet
          T1-confirmed as of last_reviewed date."
}

MAGS: {
  primary_driver: "secular_technology_growth — equity market divergence from B/C fundamentals"
  sustaining_conditions: [
    "M14 equity_scenario_divergence == HIGH (markets running ahead of scenario fundamentals)",
    "HY OAS <= 350 bps (credit stress would collapse the divergence trade rapidly)"
  ]
  failure_signals: [
    "equity_scenario_divergence shifts to MODERATE for >= 2 consecutive sessions",
    "HY OAS > 350 bps (CHAIN-3 escalation — divergence unwinds)",
    "Nasdaq 30d return <= -10% (sustained tech correction)"
  ]
  data_dependencies: ["MAGS", "^GSPC", "HY_OAS"]
  last_reviewed: "2026-06-17"
  notes: "MAGS is explicitly a divergence bet — not a B/C-native position. Its TSC
          depends on M14 output (equity_scenario_divergence). M19 must read M14 output
          before evaluating MAGS TSC — execution order matters."
}

URA: {
  primary_driver: "policy_driven_thematic_equity — nuclear renaissance + energy security"
  sustaining_conditions: [
    "Uranium spot price stable or in upward trend (T1 source: Cameco spot or UxC)",
    "Nuclear policy support intact in ≥2 of {US, EU, Japan, UK} (M02.nuclear_policy_trajectory)",
    "B+C combined probability >= 50% (energy constraint scenario sustains nuclear economics)"
  ]
  failure_signals: [
    "Uranium spot sustained decline > 20% from most recent high over 12 weeks",
    "Major nuclear policy reversal in ≥2 jurisdictions",
    "Scenario A probability >= 30% (soft landing reduces energy security premium)"
  ]
  data_dependencies: ["URA", "URANIUM_SPOT (registered in M18, yfinance UX=F — confirmed via
                       live test, June 17, 2026, NOT returning data: CME's UxC contract is
                       real but too illiquid for yfinance to carry a clean feed. Falls back
                       to FETCH_FAILED automatically; no functioning T1 spot price source
                       currently wired. URA ETF price — already fetched via HOLDINGS_PRICES —
                       remains the practical proxy until a working source is found)"]
  last_reviewed: "2026-06-17"
  notes: "URA has a known STG(0.20) classification flag as unsupported — Oklo (7.42% NAV)
          reclassified as PDT. TSC evaluation uses corrected classification."
}

COPX: {
  primary_driver: "inflation_hedge_commodity_linked — industrial commodity cycle + infrastructure demand"
  sustaining_conditions: [
    "Copper spot price stable or in upward trend over rolling 8-week window",
    "China PMI Manufacturing >= 49 (demand floor)",
    "B+C combined probability >= 50%"
  ]
  failure_signals: [
    "Copper spot sustained decline > 15% over 8 weeks",
    "Scenario D probability >= 25% (industrial recession crushes copper demand)",
    "China demand collapse signal (T1 PMI < 47 for >= 2 consecutive months)"
  ]
  data_dependencies: ["COPX", "COPPER_SPOT", "CHINA_PMI_MANUFACTURING"]
  last_reviewed: "2026-06-17"
  notes: "CORRECTION (June 17, 2026): prior draft of this entry stated 'COPX not currently
          held' — incorrect. COPX is an active Acc4 holding (220 sh per most recent allocation
          sheet). TSC evaluation applies to live monitoring, not entry consideration only.
          Original data_dependencies listed SIUSD (silver) in error — corrected to COPPER_SPOT
          above. COPPER_SPOT and CHINA_PMI_MANUFACTURING registered in M18 same session
          (yfinance HG=F and WEBSEARCH_T1 respectively); China PMI threshold check routes
          through Call 2 question M19_COPX_CHINA_PMI since WEBSEARCH_T1 surfaces as
          qualitative narrative, not a structured DataReading Python can auto-score (same
          limitation as CPI_YOY). The 8-week trailing-window conditions in this entry (copper
          spot trend, sustained decline) are not yet automatable — no historical trend-tracking
          infrastructure exists for COPPER_SPOT yet; evaluated qualitatively until built."
}

AIPO: {
  primary_driver: "real_asset_contracted_revenue (0.55) + secular_technology_growth (0.16)
                   + inflation_hedge_commodity_linked (0.11) + policy_driven_thematic_equity (0.04)"
  sustaining_conditions: [
    "AI infrastructure capital expenditure cycle intact (hyperscaler capex guidance positive)",
    "B+C combined probability >= 50% (commodity-linked infrastructure benefits from regime)"
  ]
  failure_signals: [
    "Hyperscaler capex guidance revised down ≥2 consecutive quarters",
    "Scenario D probability >= 25% (capex freeze under recession)"
  ]
  data_dependencies: ["AIPO"]
  last_reviewed: "2026-06-17"
  notes: "Bitcoin mining component (~6.5% NAV) classification pending — treat as
          unclassified until formal M15 review. Does not affect TSC evaluation materially."
}

INFL: {
  primary_driver: "diversified inflation-beneficiary royalty model — inflation_hedge_commodity_linked
                   (0.50) + inflation_hedge_precious_metals (0.25) + real_asset_contracted_revenue
                   (0.20) + secular_technology_growth (0.05); revenue scales with commodity/land/
                   energy prices without commensurate cost increases (royalty structure, not direct
                   commodity ownership)"
  sustaining_conditions: [
    "B+C combined probability >= 50% (inflationary/energy-constrained regime sustains royalty
     revenue growth across the diversified book)",
    "GCUSD stable-to-positive over rolling 8-week window (IHP component — WPM/FNV/OR royalty streams)"
  ]
  failure_signals: [
    "Scenario A probability >= 30% (disinflationary soft landing removes the core inflation-
     beneficiary thesis)",
    "GCUSD sustained decline > 15% over 8 weeks (degrades IHP royalty component)",
    "Scenario D probability >= 25% (industrial/land-royalty volume declines under recession)"
  ]
  data_dependencies: ["INFL", "GCUSD", "BZUSD"]
  last_reviewed: "2026-06-17"
  notes: "Added in place of PAVE (exited June 10, 2026, v1.33 — fully logged, no §13 entry
          needed) and XLP (exited on or before June 17, 2026 per client; recommendation logged
          Session_Log June 14, formal trades_executed entry deferred to next full M05 session
          per client direction, June 17, 2026). §11 currently shows INFL as CANDIDATE
          (v1.34, June 13, 2026) — status should be upgraded to ACTIVE at the next full M05
          session once the actual execution (price, date, share count) is logged. ComponentVector
          and EV math already established at §11; not re-derived here. TPL/LandBridge classified
          as CL not RAC (royalty_rate × commodity_price × volume, not fixed-fee)."
}

### 13.1 Candidate Placeholders (zero current allocation — no live entry)

VNQ, VEA: §11.4 CANDIDATE only; zero current allocation. adoption_trigger: create a full §13
entry (primary_driver, sustaining_conditions, failure_signals, data_dependencies) the session
either instrument is actually added to live allocation. Until then M19 simply skips them —
UNKNOWN does not apply to a position that was never held.
