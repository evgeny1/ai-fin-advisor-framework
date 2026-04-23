# Calibration State
Persistent framework configuration — load at every session start alongside session handoff.

Version: 1.3  Last updated: April 23, 2026 (M13 adopted; §4 added; §§4–6 renumbered §§5–8; GitHub migration)  Next scheduled review: June 30, 2026 (Q2 2026 quarter-end)

_______________

## Load Verification Requirement
At session start, the advisor must state in the briefing:

"Calibration State loaded, last update: April 23, 2026"

Absence of this line indicates the calibration file was not loaded and the session is invalid for threshold-sensitive decisions.

_______________

## Section 1 — Credit Signal Thresholds (relative, §1.5a)
All HY/CCC/IG thresholds are relative to the trailing 180-day median of the underlying FRED series, computed at session start.

### 1.1 HY Composite — FRED: BAMLH0A0HYM2

| Parameter | Current Value | Type | Notes |
| :-: | :-: | :-: | :-: |
| HY\_STRESS\_DELTA | \+150 bps | Calibration-dated | Provisional initial — full audit pending June 30, 2026 |
| HY\_RECESSION\_DELTA | \+300 bps | Calibration-dated | Provisional initial — full audit pending June 30, 2026 |
| Velocity overlay | \+100 bps over prior 60 days | Fixed structural | Not calibration-dated |
| Sustain period | 10 trading days | Fixed structural | Not calibration-dated |
| D-floor on recession-pricing trigger | 25% | Fixed structural | Not calibration-dated |

Baseline snapshot at instantiation (April 19, 2026): ~285 bps (Trading Economics / FRED point observation — NOT the computed 180-day median). Trailing 180d median to be computed at Q2 2026 audit.

Session observation (April 19, 2026 session): HY composite remains at ~285 bps (Trading Economics). Consistent with baseline snapshot. No velocity check executed this session — full 30-day HY composite history not pulled; fetch planned for next session.

Session observation (April 21, 2026 session): HY composite ~285 bps (Trading Economics; FRED last updated April 15-16 — readings stale by 4-5 days due to weekend + active geopolitical events). Unchanged from April 19 baseline. Velocity check not executable — §7 log needs 60+ trading day history. T1_flag: composite_only | stale. No threshold fires.

Session observation (April 22, 2026 session): HY composite ~287 bps (Trading Economics; FRED last updated April 20). Marginal uptick from April 21 reading. No threshold fires. Velocity check not executable — §7 log needs 60+ trading day history. T1_flag: stale.

### 1.2 IG Composite — FRED: BAMLC0A0CM

| Parameter | Current Value | Type | Notes |
| :-: | :-: | :-: | :-: |
| IG\_TRANSMISSION\_DELTA | \+60 bps | Calibration-dated | Provisional initial — full audit pending June 30, 2026 |
| Velocity overlay | \+40 bps over prior 60 days | Fixed structural | Not calibration-dated |
| Sustain period | 10 trading days | Fixed structural | Not calibration-dated |

Baseline at instantiation: Not yet computed. Trailing 180d median to be computed at Q2 2026 audit.

Session observation (April 19, 2026 session): IG composite ~83 bps (Trading Economics). Recorded for baseline reference; no trigger check executed pending 180d median computation.

Session observation (April 21, 2026 session): IG composite ~83 bps (Trading Economics; FRED stale by 4-5 days). Unchanged from April 19 observation. IG_TransmissionReached NOT fired (threshold ~143 bps vs current ~83 bps; gap ~60 bps). T1_flag: composite_only | stale.

Session observation (April 22, 2026 session): IG composite ~83 bps (FRED last updated April 16-17; stale). No change. IG_TransmissionReached NOT fired. T1_flag: stale.

### 1.3 CCC Tail — FRED: BAMLH0A3HYC

| Parameter | Current Value | Type | Notes |
| :-: | :-: | :-: | :-: |
| Ratio divergence | CCC widens 3x composite over 30d | Fixed structural | Not calibration-dated |
| Absolute divergence floor | CCC \+200 bps while composite \+\<50 bps over 30d | Calibration-dated | Provisional — audit pending June 30, 2026 |
| Action on trigger | Flag for monitoring; note in next 3 sessions | Fixed structural | Not calibration-dated |

Session observation (April 19, 2026 session) — first concrete divergence computation executed:

| Measurement | Value |
| :-: | :-: |
| CCC OAS on 2026-03-16 (30 trading days prior, approx) | 9.73% = 973 bps |
| CCC OAS on 2026-04-16 (latest FRED observation) | 9.21% = 921 bps |
| CCC 30-day change | −52 bps (tightening) |

Divergence test results:
* Ratio divergence: NOT fired — CCC tightening, not widening
* Absolute divergence: NOT fired — CCC delta negative

Signal: Credit calm across composite and tail. No early-warning divergence. Per §1.5a.2 asymmetric weighting rule, this is absence-of-widening (not actively confirming health), but no dissent signal against risk-on equity regime.

Session observation (April 21, 2026 session): CCC OAS ~921 bps (carried from April 19 FRED observation; no new FRED data published since April 16). CCC_TailFirstWidening NOT fired. T1_flag: stale. No new divergence computation this session — carry forward April 19 result.

Session observation (April 22, 2026 session): CCC OAS ~921 bps (FRED last updated April 17; stale). No new FRED data. CCC_TailFirstWidening NOT fired. T1_flag: stale. Carry forward April 19 divergence result.

_______________

## Section 2 — Other Calibration-Dated Thresholds (Pending Initial Audit)
The following thresholds exist in the main framework and are calibration-dated. Initial formal audit has not been completed for these — they carry forward at their current framework values. Full hit-rate / miss-rate audit scheduled for June 30, 2026 quarter-end review.

### 2.1 Energy / Commodities

| Threshold | Current Value | Source | Audit Status |
| :-: | :-: | :-: | :-: |
| WTI floor — SGOL invalidation (Scenario A, D) | $55 nominal OR 30% below 90d trailing WTI settlement average | Existing framework, ⚑ calibration-dated | Pending June 30 |
| Brent trigger — Scenario C | $110 nominal OR 40% above 90d trailing Brent settlement average | Existing framework, ⚑ calibration-dated | Pending June 30 |
| Brent invalidation — Scenario C | $80 nominal OR 20% below 90d trailing Brent settlement average | Existing framework, ⚑ calibration-dated | Pending June 30 |

Session observation (April 19, 2026 session): Brent Friday close $90.38, Sunday futures ~$95.25–$95.71. WTI Friday close $83.85, Sunday futures $89.94. All well within Scenario C un-triggered zone; none approach the nominal $110 Brent trigger or the $80 invalidation threshold. SGOL WTI floor ($55) comfortably clear.

Session observation (April 21, 2026 session): Brent ~$94–96 (high volatility — Friday -11.5% on Iran Strait opening announcement, Monday +5–6% on US ship seizure and Strait re-blocking). WTI ~$87–88. All still below $110 C trigger. No floor or invalidation thresholds approached.

Session observation (April 22, 2026 session): Brent ~$99.81 (approaching $100; +1.4% today). WTI ~$89.33. C trigger ($110 nominal) NOT fired. No floor or invalidation thresholds approached. SGOL WTI floor ($55) comfortably clear. Trailing 90d average unavailable this session — nominal thresholds apply.

### 2.2 Currency

| Threshold | Current Value | Source | Audit Status |
| :-: | :-: | :-: | :-: |
| DXY sustained above — SGOL invalidation | 105 nominal | Existing framework, not currently flagged as calibration-dated | Pending June 30 — classify formally |

Session observation (April 19, 2026): DXY 98.23 Friday close, Sunday futures modestly higher. Well below 105 invalidation threshold.

Session observation (April 21, 2026): DXY ~97.9 — flat to marginally lower. Well below 105 threshold.

Session observation (April 22, 2026): DXY ~98.30 — flat. Well below 105 invalidation threshold. SGOL invalidation condition 2 NOT approached.

### 2.3 Macro

| Threshold | Current Value | Source | Audit Status |
| :-: | :-: | :-: | :-: |
| CPI trigger — Scenario B | 4% YoY, 3+ consecutive monthly prints | Existing framework, not currently flagged | Pending June 30 — classify formally |
| CPI invalidation — Scenario B | below 3% YoY, 2+ consecutive monthly prints | Existing framework, not currently flagged | Pending June 30 — classify formally |
| GDP trigger — Scenario F | above 3% annualized, 2+ consecutive quarters | Existing framework, not currently flagged | Pending June 30 — classify formally |
| GDP invalidation — Scenario F | below 2% on BEA advance estimate | Existing framework, not currently flagged | Pending June 30 — classify formally |
| Unemployment trigger — Scenario D | \+0.5% over any 3-month window | Existing framework, not currently flagged | Pending June 30 — classify formally |

Session observation (April 19, 2026): CPI March 3.3% YoY (below 4% trigger, above 3% invalidation — in neither regime). PPI March 4.0% YoY — strongest since Feb 2023 (BLS Tier 1, supports B probability but not itself a CPI trigger).

Session observation (April 21, 2026): No new macro data. CPI March 3.3% remains most recent print (1 of 3 required for B trigger). Q4 2025 GDP revised to 0.5% annualized (down sharply from 4.4% Q3 2025). Q1 2026 GDP advance estimate due end of April.

Session observation (April 22, 2026): No new macro data. CPI March 3.3% YoY remains most recent print (1 of 3 for B trigger; 1 of 2 for C trigger reacceleration check). Q4 2025 GDP 0.5% annualized confirmed. Q1 2026 advance estimate due ~April 30. Next CPI print ~May 10-12.

### 2.4 Instrument Evaluation

| Threshold | Current Value | Source | Audit Status |
| :-: | :-: | :-: | :-: |
| Foreign concentration disqualification | 40% single-country/single-region | Existing framework, not currently flagged | Pending June 30 — classify formally |
| AUM disqualification | $100M minimum | Existing framework, not currently flagged | Pending June 30 — classify formally |

_______________

## Section 3 — Calibration Log

2026-04-19 — Initial instantiation (v1)
* Framework Extension v1 adopted (see Framework_Extension_v1_Credit_And_Calibration.md).
* Credit signal thresholds added to framework with provisional initial delta values:
   * HY\_STRESS\_DELTA = +150 bps
   * HY\_RECESSION\_DELTA = +300 bps
   * IG\_TRANSMISSION\_DELTA = +60 bps
   * CCC absolute divergence floor = +200 bps (while composite +<50 bps)
* HY baseline snapshot recorded at ~285 bps (NOT trailing 180d median — point observation only).
* Other framework calibration-dated thresholds carried forward unchanged. Full audit and formal classification scheduled for June 30, 2026.
* No existing thresholds modified in this instantiation.
* Rationale for provisional credit deltas: historical median widening from baseline into "stress-beginning" regime is approximately +150 bps; into "recession-pricing" regime approximately +300 bps. Final calibration pending 180d median computation and percentile-band check at June 30 review.

2026-04-19 — First session after instantiation (same-day, post-markets)
* No threshold changes. All calibration-dated values carried forward.
* First CCC divergence computation executed per §1.5a.4. Method: fetched full FRED series BAMLH0A3HYC, compared 2026-04-16 (latest: 9.21%) against 2026-03-16 (30 trading days prior: 9.73%). Δ = −52 bps (tightening).
   * Ratio divergence: NOT fired
   * Absolute divergence: NOT fired
* Session observations recorded for HY ~285 bps, IG ~83 bps, CCC 921 bps. Logged as reference snapshots, not as baseline revisions.
* Macro / energy / currency observations cross-checked against Section 2 thresholds. No trigger approaches. See handoff document for detail.
* No interim recalibration trigger fired per §1.10 criteria (a)–(d): baseline shift <20% from instantiation, no false positives, no false negatives, no primary driver recalibration declared.
* Note for future sessions: Full 30-day HY composite and IG composite velocity checks require fetching the corresponding FRED txt series (BAMLH0A0HYM2, BAMLC0A0CM) — same method as CCC. Planned for next session to execute the full credit signal protocol end-to-end.

2026-04-21 — Framework update (v1.2)
* No threshold changes. All calibration-dated values carried forward.
* §6 Session State Log section added to this file. Purpose: persist scenario probabilities, primary driver, open triggers, open decisions, and next-session flags at each session end. Enables 25pp session cap enforcement in M03_ScenarioFramework.DeriveScenarioProbabilities().
* M03_ScenarioFramework updated: DeriveScenarioProbabilities() function added — structured scoring procedure for scenario probabilities to eliminate unconstrained fresh-session judgment divergence.
* M04_BriefingFormat updated: ScenarioProbabilities section now requires full scoring output display.
* M05_SessionInit updated: Step 3 now loads §6; Step 10 now writes §6 alongside §5.
* M12_DriveProtocol updated: WriteBack procedure extended to append §6 in same operation as §5.
* Session observations (April 21, 2026): Credit unchanged from April 19 baseline. Energy: Brent ~$94–96 (high volatility around ceasefire events). DXY ~97.9. No thresholds approached.
* MOVE index not fetched April 21 session — carry to next session flags.
* FRED HY/IG velocity checks not yet executable — §5b log needs 60+ trading days of entries.

2026-04-21 — First full portfolio audit session
* No threshold changes. All calibration-dated values carried forward.
* Full session executed: scenario probabilities derived via DeriveScenarioProbabilities() — initial derivation (§6 was empty, no prior anchor; 25pp cap not applied).
* Scenario probabilities: A=7%, B=44%, C=36%, D=3%, E=7%, F=3%. Sum = 100%. B/C simultaneous >30% justification documented in briefing.
* Primary driver: Strait of Hormuz Crisis / US-Iran War (Day 52). No recalibration declared.
* Credit readings (April 21): HY ~285 bps, IG ~83 bps, CCC ~921 bps — all stale (FRED last updated April 15-16). No threshold fires.
* Gold 90-day extraordinary movement check: Jan 20, 2026 ($4,737) to Apr 20, 2026 (~$4,800) = +1.3%. Extraordinary movement rule NOT triggered.
* PAVE legislative mandate verification flagged as prerequisite before B trigger execution.
* §7 Session Observations Log initialized. §8 first entry written.

2026-04-22 — Scheduled bi-weekly portfolio review session
* No threshold changes. All calibration-dated values carried forward.
* Scenario probabilities updated: A=8%, B=45%, C=38%, D=3%, E=3%, F=3% (sum=100%). Derived via DeriveScenarioProbabilities() scoring. Prior anchor: April 21 (A=7%, B=44%, C=36%, D=3%, E=7%, F=3%). All deltas within 25pp cap.
* E probability 7% → 3% (floor). Scoring-driven — E binding variables not currently met. Fed independence strain (Warsh/DOJ/Powell) logged as challenger driver only.
* PAVE/IIJA T1 verification completed this session (GAO, DOT/FHWA Jan 31 2026, Urban Institute, T4America, Crowell & Moring). Finding: >$2.3B in IIJA rescissions confirmed; IIJA expires Sept 30, 2026; no reauthorization bill introduced as of April 2026. PAVE status upgraded from watch to FLAGGED. B-protocol reduction authorized.
* Allocation sheet misread corrected and committed to memory: "Cash to Add" column = external cash needed to deposit without selling existing shares — NOT idle available cash. No accounts hold meaningful idle cash.
* Second opinion sourced: Bridgewater Associates (2026 Fiduciary Investor Symposium, April 2026) validates B+C portfolio positioning — equities Sharpe −0.72 in stagflation, gold Sharpe +1.0+. OECD raised US 2026 CPI forecast to 4.2%.
* New per-account scenario-weighted target allocations produced:
   * Schwab IRA: VTI 10%, XAR 22%, MLPX 21%, SGOL 47%
   * Schwab Roth IRA: VTI 10%, XAR 22%, MLPX 21%, SGOL 47%
   * Taxable Acc3: SGOV 100% (no change)
   * Taxable Acc4: VTI 0%, PAVE 11%, XAR 30%, MLPX 36%, SGOV 23%
   * Relative IRA: VTI 10%, MLPX 23%, SGOL 48%, SGOV 19%
   * Relative Roth: VTI 25%, MLPX 25%, SGOL 50%
* SGOL underweight addressed: portfolio target 24% (up from 16.1% current). All sheltered account SGOL targets raised to 47–48%.
* WriteBack executed via create_file (no update_file tool available in Drive MCP this session). Client must DELETE old Calibration_State.md from Drive root — keep only this new version to prevent M12 HARD_STOP on duplicate detection next session.

2026-04-23 — Framework update (v1.3): M13 adoption, §4 addition, GitHub migration
* No threshold changes to §§1–2. All prior calibration-dated values carried forward.
* M13_GrowthObjectives.md adopted (v1.0). Resolves idealAllocation() gap in M03; replaces minimumConvictionWeight() in M03; adds growth objective feasibility check and recalibration sequence.
* §4 (Growth Objectives: Return Table and Multipliers) added to this file — see below.
* Return table (§4.1) initialized with empirical grounding:
   * Gold/precious metals: ~9.2% real annualized 1973–82 stagflation (Morningstar/CAIA); ~19% in stagflation 1973–2024 (Flexible Plan); confirmed ~4% in low-inflation regimes (World Gold Council).
   * Domestic equity: −7.1% nominal / −16.6% real in stagflation (Robeco/Baltussen 146-year study); ~15–18% real in 1990s soft landing; ~-36% nominal in 2008 deflationary recession peak.
   * Commodities: near one-for-one with unexpected inflation (GSCI/NBER); particularly poor in severe recessions.
   * Real asset/contracted revenue (midstream): outperformed S&P 500 by 77% cumulative 2008–2011; positive in inflation periods due to contract inflation escalators (Alerian/Cohen & Steers).
   * Long duration bonds: primary beneficiary in deflationary recession; directly impaired in stagflation and inflationary shock (Robeco; CAIA).
   * Defense/geopolitical premium: annual returns dependent on defense spending levels (Auer 2013); abnormal returns around discrete geopolitical events.
   * All values provisional — full empirical audit at June 30, 2026 alongside §1–2.
* IRA and Roth IRA target multipliers (§4.2–4.3) initialized. Roth derived from IRA multipliers extended to 15-year horizon + ~0.5–0.75% effective annual tax-free compounding advantage. Both confirmed provisionally by client — full review at June 30, 2026.
* §§4–6 renumbered → §§5–8 to accommodate new §4. Section references in M05 and M12 updated accordingly.
* GitHub migration: Calibration_State.md now lives in GitHub repo (evgeny1/ai-fin-advisor-framework, master branch). M12 updated from Drive-only to hybrid GitHub+Drive protocol. No duplicate-file workaround needed — GitHub create_or_update_file overwrites cleanly. Allocation sheet remains on Google Drive (read-only from framework).
* M03_ScenarioFramework.md updated: scenarioWeightedAllocation() and minimumConvictionWeight() now delegate to M13.
* M05_SessionInit.md updated: §7 and §8 references; Calibration_State fetch now via GitHub.
* 00_INDEX.md updated: M13 added to registry, load order, precedence, cross-references, calibration-dated thresholds.
* Account objective profiles to be added manually to Allocation sheet "Objectives" tab (new tab). See M13 STRUCT AccountObjectiveProfile for required fields.

_______________

## Section 4 — Growth Objectives: Return Table and Multipliers
⚑ All values in this section are CALIBRATION_DATED.
Review at every quarter-end audit alongside §1 and §2 thresholds.
Interim review triggered if: return table produces systematic infeasibility across accounts despite valid allocation changes.
@see M13_GrowthObjectives

Last calibrated: April 23, 2026 (initial instantiation — provisional)
Full empirical audit scheduled: June 30, 2026

Revision triggers for §4 specifically:
- New macro regime episode completes with sufficient data → update relevant scenario column
- Academic consensus on historical returns revises materially (e.g., JST database update)
- A role's structural characteristics change materially (e.g., MLPX contract structure shifts from fee-based)
- Systematic infeasibility across accounts despite valid allocations → interim review before next recommendation

### 4.1 Expected Real Annualized Return Table
Conservative end used for ALL computations. Upside end disclosed in briefing only — never used in computation.
Format per cell: [conservative%, upside%]

| Role | Scenario A | Scenario B | Scenario C | Scenario D | Scenario E | Scenario F |
| :-- | :-: | :-: | :-: | :-: | :-: | :-: |
| geopolitical_premium | [-2, 3] | [2, 6] | [4, 10] | [-4, 0] | [1, 5] | [1, 4] |
| inflation_hedge_precious_metals | [0, 4] | [6, 12] | [7, 14] | [-2, 4] | [10, 20] | [-3, 1] |
| inflation_hedge_commodity_linked | [2, 6] | [6, 12] | [7, 13] | [-8, -2] | [2, 6] | [2, 5] |
| real_asset_contracted_revenue | [3, 7] | [3, 7] | [3, 6] | [2, 6] | [2, 5] | [3, 7] |
| policy_driven_thematic_equity | [4, 8] | [-3, 1] | [-1, 3] | [-5, -1] | [-6, -2] | [4, 8] |
| rate_sensitive_income_short_duration | [0, 2] | [1, 3] | [1, 3] | [0, 3] | [-2, 2] | [1, 3] |
| rate_sensitive_income_long_duration | [3, 7] | [-4, -1] | [-5, -2] | [5, 10] | [-10, -3] | [-4, -1] |
| broad_market_equity_domestic | [5, 12] | [-8, -2] | [-4, -1] | [-12, -4] | [-8, -3] | [7, 14] |
| broad_market_equity_international | [4, 9] | [-5, -1] | [-6, -2] | [-8, -3] | [-10, -4] | [3, 8] |

Empirical basis (key anchors — see Calibration Log 2026-04-23 for full sourcing):
- inflation_hedge_precious_metals B: ~9.2% real 1973–82 (conservative); ~19% annualized stagflation 1973–2024 (upside)
- inflation_hedge_precious_metals E: Nixon shock analog; reserve erosion = maximum thesis conviction
- inflation_hedge_precious_metals F: −1.1% real 1980–2000 with positive real rates (World Gold Council)
- broad_market_equity_domestic B: −7.1% nominal / −16.6% real in stagflation (Robeco 146-year study)
- broad_market_equity_domestic D: −36.5% nominal in 2008 peak year; multi-year regime −12% conservative
- broad_market_equity_domestic A/F: ~15–18% real in 1990s soft landing / overheat
- inflation_hedge_commodity_linked B/C: near one-for-one with unexpected inflation (GSCI/NBER)
- inflation_hedge_commodity_linked D: "particularly poorly during severe recessions" (NBER)
- real_asset_contracted_revenue D: 77% cumulative outperformance vs S&P 500, 2008–2011 (Alerian)
- rate_sensitive_income_long_duration D: primary beneficiary confirmed; flight to quality 2008
- policy_driven_thematic_equity: insufficient historical analog data — structurally derived from M09/M10 narratives
- Scenario E: limited data — structurally reasoned; no clean modern analog for full reserve rupture

### 4.2 IRA Target Multipliers (planning horizon: 10 years)
Floor: 1.5× (enforced regardless of probability vector)

| Scenario | Multiplier | Implied Real Return | Basis |
| :-: | :-: | :-: | :-- |
| A — Soft Landing | 2.0 | ~7.2% annualized | Historical soft landing 1990s: ~15–18% real equity returns; balanced portfolio approximately 7–8% real |
| B — Stagflation Lock | 1.5 | ~4.1% annualized | Real growth constrained; 1973–82 mixed portfolio real returns floor; hedges partially offset equity losses |
| C — Inflationary Shock | 1.5 | ~4.1% annualized | Energy spike limits real return; similar outcome to B over 10yr horizon |
| D — Deflationary Recession | 1.3 | ~2.7% annualized | Preservation primary; modest growth from long bonds only; demand collapse |
| E — Structural Rupture | 1.2 | ~1.8% annualized | Capital preservation dominates; maximum stress scenario; real asset focus |
| F — Growth Overheat | 2.0 | ~7.2% annualized | Strong nominal growth; cyclicals and financials outperform; similar to A on 10yr horizon |

Current regime probability-weighted target (A=8%, B=45%, C=38%, D=3%, E=3%, F=3%):
= 0.08×2.0 + 0.45×1.5 + 0.38×1.5 + 0.03×1.3 + 0.03×1.2 + 0.03×2.0
= 0.16 + 0.675 + 0.57 + 0.039 + 0.036 + 0.06 = 1.54×
Required real return: (1.54)^(1/10) − 1 ≈ 4.4% annualized

### 4.3 Roth IRA Target Multipliers (planning horizon: 15 years)
Floor: 2.0× (enforced regardless of probability vector)
Derivation: IRA multipliers extended to 15-year horizon at same implied annualized real return,
plus ~0.5–0.75% effective annual advantage from tax-free compounding on a typical equity-heavy portfolio.

| Scenario | IRA Rate | Roth Rate (adj) | Roth 15yr Multiplier | Notes |
| :-: | :-: | :-: | :-: | :-- |
| A | ~7.2% | ~7.9% | 3.1 | Full tax-free compounding; extended 15yr runway |
| B | ~4.1% | ~4.6% | 2.0 | Constrained real growth; longer runway partially absorbs shock |
| C | ~4.1% | ~4.6% | 2.0 | Same as B on extended horizon |
| D | ~2.7% | ~3.0% | 1.6 | Preservation + modest bond appreciation; tax-free muted benefit |
| E | ~1.8% | ~2.1% | 1.4 | Capital preservation; rupture scenario; limited compounding environment |
| F | ~7.2% | ~7.9% | 3.1 | Same as A; full overheat compounding advantage |

Status: confirmed provisionally by client April 23, 2026. Full review at June 30, 2026 audit.

### 4.4 Structural Floor and Concentration Parameters

| Parameter | Current Value | Type | Notes |
| :-: | :-: | :-: | :-- |
| Base floor (fraction of current allocation) | 0.25 | Calibration-dated | 75% reduction = maximum adverse directive applied |
| Minimum floor (% of account total value) | 2% | Calibration-dated | Prevents floor from becoming a rounding artifact |
| Concentration cap (max single position) | 40% | Calibration-dated | Consistent with M06 5–6 position monitoring constraint |
| Floor nominal loss probability threshold | 15% | Calibration-dated | Scenarios at or above this probability checked for floor breach in FLOOR_THEN_RETURN accounts |

All values provisional — full audit pending June 30, 2026.

_______________

## Section 5 — Review Cadence
(Formerly §4 — renumbered April 23, 2026)

| Date | Type | Scope |
| :-: | :-: | :-: |
| 2026-06-30 | Scheduled Q2 (first full audit) | Compute 180d medians for HY/IG/CCC; verify HY/IG/CCC deltas place triggers in 75th–90th percentile band; hit-rate audit for all absolute thresholds in Section 2; formally classify currently-unflagged thresholds as calibration-dated; first empirical audit of §4 return table and multipliers |
| 2026-09-30 | Scheduled Q3 | Full audit of all calibration-dated thresholds including §4 |
| 2026-12-31 | Scheduled Q4 | Full audit |
| 2027-03-31 | Scheduled Q1 2027 | Full audit |

Interim recalibration triggered per §1.10 if:

* Trailing baseline shifts >20% from last calibration
* Any threshold fires twice without prescribed regime materializing
* Any threshold fails to fire while prescribed regime materializes
* Primary driver recalibration declared per §1.6
* Return table (§4.1) produces systematic infeasibility across accounts despite valid allocation changes

_______________

## Section 6 — First-Audit Checklist (for June 30, 2026 session)
(Formerly §5 — renumbered April 23, 2026)
At Q2 2026 review, execute the following:

1. Compute trailing 180-day median for FRED series BAMLH0A0HYM2, BAMLC0A0CM, BAMLH0A3HYC. Record in Section 1.
2. Compute 10th/25th/75th/90th percentiles of trailing distribution for each series.
3. Verify HY\_STRESS\_DELTA (+150) places trigger in 75th–90th percentile band of HY distribution. If outside band, adjust and log rationale.
4. Verify HY\_RECESSION\_DELTA (+300) places trigger in 75th–90th percentile band. Adjust if needed.
5. Verify IG\_TRANSMISSION\_DELTA (+60) places trigger in 75th–90th percentile band of IG distribution. Adjust if needed.
6. Hit-rate audit each absolute threshold in Section 2 against trailing 5-year data. Adjust if lagging or false-positive-prone.
7. Formally classify currently-unflagged thresholds in Sections 2.2, 2.3, 2.4 as calibration-dated. Update main framework document to add ⚑ markers.
8. First empirical audit of §4.1 return table: verify conservative bounds against any new regime episode data; check structural coherence across roles and scenarios.
9. First empirical audit of §4.2 and §4.3 multipliers: verify IRA implied returns are achievable given current holdings and scenario probabilities; verify Roth derivation adjustment remains appropriate.
10. Audit §4.4 floor and concentration parameters against actual account sizes and position counts.
11. Record all results in Section 3 Calibration Log with date-stamped entry.
12. Confirm next review date (September 30, 2026).

_______________

## Section 7 — Session Observations Log (Credit Readings)
(Formerly §5b — renumbered April 23, 2026)
Appended at every session end by M12_FileProtocol.WriteBack.
Enables velocity checks once 60+ trading days of entries accumulate.
Note: Until 60+ entries exist, velocity overlays (HY: 100bps/60d; IG: 40bps/60d) cannot be computed from this log — log the gap rather than skipping the entry.

| Date | HY OAS (bps) | IG OAS (bps) | CCC OAS (bps) | Source | T1 Flag |
| :-: | :-: | :-: | :-: | :-: | :-: |
| 2026-04-19 | 285 | 83 | 921 | Trading Economics / FRED | composite_only |
| 2026-04-21 | 285 | 83 | 921 | Trading Economics / FRED (stale — last updated Apr 15-16) | stale |
| 2026-04-22 | 287 | 83 | 921 | Trading Economics / FRED (HY last updated Apr 20; IG/CCC Apr 16-17) | stale |

_______________

## Section 8 — Session State Log
(Formerly §6 — renumbered April 23, 2026)
Appended at every session end by M12_FileProtocol.WriteBack.
Consumed at every session start by M05_SessionInit.INPUT_3 (§8 load).
Provides prior scenario probability anchor for 25pp cap enforcement in
M03_ScenarioFramework.DeriveScenarioProbabilities().

Format per entry:
  date: [YYYY-MM-DD]
  scenario_probabilities: { A: %, B: %, C: %, D: %, E: %, F: % }  // must sum to 100%
  primary_driver: [name]
  derivation_method: scored | manual_override
  manual_override_reason: [T1 evidence and rationale] | null
  open_triggers: [list]
  open_decisions: [list]
  next_session_flags: [list]

---

date: 2026-04-21
scenario_probabilities: { A: 7%, B: 44%, C: 36%, D: 3%, E: 7%, F: 3% }
primary_driver: Strait of Hormuz Crisis / US-Iran War (Day 52)
derivation_method: scored
manual_override_reason: null
open_triggers:
  - Ceasefire expiry April 22 — watching for Brent spike toward $110 C trigger; if Brent crosses $110 and holds 10 trading days with T1 evidence (EIA/CME), C partial rotation activates
  - Warsh Senate Banking Committee confirmation hearing April 21 — outcome affects E probability accumulation and monetary policy succession risk
  - Q1 2026 GDP advance estimate due ~April 30 — if negative: B trigger check_gdp progresses; D trigger watch begins
  - Next CPI print ~May 10-12 — second print needed for C trigger reacceleration; third above 4% needed for B trigger
  - Brent $80 invalidation watch — if sustained Strait resolution drives Brent below $80 for 10 days, SGOL invalidation condition 3 check required (WTI floor $55 still far away)
open_decisions:
  - Do NOT redeploy Acc3 cash into VTI after May 1 — EV calculation negative under B+C dominant environment; deploy into SGOV taxable instead. Client confirmation pending.
  - PAVE legislative mandate (IIJA) status verification required via T1 source before any B trigger reduction execution.
  - XAR Acc4 rebalancing signal directionally consistent with C scenario — defer to next scheduled rebalancing or formal trigger.
next_session_flags:
  - MOVE index not fetched this session — retrieve at next session start (priority)
  - FRED HY/IG velocity checks not yet executable — §7 log needs 60+ trading day entries
  - Ceasefire expiry outcome (April 22) — reassess C probability immediately at next session
  - Warsh confirmation hearing outcome (April 21) — assess E probability direction at next session
  - Verify PAVE/IIJA spending mandate status via T1 source (White House OMB, appropriations legislation, CBO)
  - Gold 90-day extraordinary movement check: Jan 20 ($4,737) to Apr 20 (~$4,800) = +1.3% — NOT triggered; re-check if gold moves >5% between sessions
  - Credit spread staleness: FRED data was 4-5 days stale this session — fetch fresh at next session start
  - Confirm with client: Acc3 cash redeployment decision (SGOV taxable vs. hold as cash)

---

date: 2026-04-22
scenario_probabilities: { A: 8%, B: 45%, C: 38%, D: 3%, E: 3%, F: 3% }
primary_driver: Strait of Hormuz Crisis / US-Iran War (Day 53) — ceasefire extended by Trump; Strait remains blocked; Iran declined talks; VP Vance Islamabad trip canceled
derivation_method: scored
manual_override_reason: null
open_triggers:
  - Brent $110 C-trigger — 10-day sustain clock starts if/when Brent crosses $110; currently ~$100; monitoring EIA/CME
  - Q1 2026 GDP advance estimate ~April 30 — if negative: B check_gdp advances to 3; D watch begins formally
  - Next CPI print ~May 10-12 — 2nd print needed for C trigger reacceleration; 3rd above 4% for B trigger
  - FOMC April 28-29 — expected hold; reassess A/B scores immediately on release
  - Warsh confirmation BLOCKED by Sen. Tillis; DOJ/Powell investigation prerequisite; timeline indeterminate
  - PAVE/IIJA FLAGGED: T1-verified this session (GAO, DOT/FHWA, T4America, Crowell); rescissions >$2.3B confirmed; IIJA expires Sept 30, 2026; no reauthorization bill introduced
open_decisions:
  - Schwab IRA: sell VTI (-48 shares), XAR (-32 shares), MLPX (-154 shares); buy SGOL (+808 shares) — new targets: VTI 10%, XAR 22%, MLPX 21%, SGOL 47% — pending client execution
  - Schwab Roth IRA: sell VTI (-8 shares), XAR (-5 shares), MLPX (-31 shares); buy SGOL (+143 shares) — same new targets — pending client execution
  - Taxable Acc4: sell PAVE (-82 shares); buy SGOV (+73 shares) — new targets: PAVE 11%, SGOV 23% — verify PAVE cost basis for tax-loss harvesting before executing — pending client execution
  - Relative IRA: sell MLPX (-47 shares), SGOV (-36 shares); buy SGOL (+166 shares) — new targets: MLPX 23%, SGOL 48%, SGOV 19% — pending client execution
  - Relative Roth: sell VTI (-1 share); buy MLPX (+7 shares), SGOL (+2 shares) — new targets: VTI 25%, MLPX 25%, SGOL 50% — pending client execution
  - NOTE: April 21 open decision re Acc3 cash redeployment was erroneous — Acc3 has no idle cash; Cash to Add = external deposit required. Decision voided. Acc3 remains 100% SGOV, no action.
next_session_flags:
  - Natural gas price not fetched this session — priority fetch at next session start
  - FRED HY/IG velocity checks still not executable — §7 log needs 60+ trading day entries
  - Q1 2026 GDP advance estimate (~April 30) — reassess B/D scoring immediately upon release
  - FOMC April 29 decision — reassess A/B/D scores immediately on release
  - PAVE downgraded from watch to FLAGGED — B-protocol reduction in Acc4 now authorized per T1 verification this session; execute per open_decisions above
  - Brent ~$100; $110 clock not started; begin close monitoring if Brent approaches $105
  - Credit FRED staleness: HY Apr 20, IG/CCC Apr 16-17 — fetch fresh at next session start
  - New target allocations produced this session — pending client entry into allocation sheet target % columns; confirm execution before next session
  - Gold 90-day extraordinary movement check: Jan 20 ($4,737) to Apr 22 (~$4,785) = +1.0% — NOT triggered

---
