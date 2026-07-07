# Instrument Classification Registry (M15)
<!-- ENG-51, 2026-07-06: extracted verbatim from Calibration_State.md §11. -->
<!-- Storage-location change only -- no semantics change. classifyInstrument(), -->
<!-- ValidateClassifications(), and blendedScenarioReturn() logic is untouched; -->
<!-- this file holds exactly what §11 held before, same heading numbering (§11.1-§11.4) -->
<!-- so every cross-reference to "§11.x" elsewhere in the framework still resolves. -->
<!-- Fetched via M12_DriveProtocol.fetchInstrumentClassification() -- see that module. -->

## Section 11 - Instrument Classification Registry (M15)

All values CALIBRATION_DATED. First audit: June 30, 2026.
VTI, XAR, MLPX, SGOL, SGOV, PAVE added Apr 28 (v1.7). AIPO, MAGS added Apr 30 (v1.9). AIPO §11 data updated May 6 (v1.10). MLPX EV updated May 6 (v1.11). New roles inflation_linked_sovereign and real_estate_equity_income added May 6 (v1.12). Five new roles added May 6 (v1.13): systematic_trend_following, consumer_defensive_equity, healthcare_defensive_equity, floating_rate_credit_income, emerging_market_equity. New instruments added May 6 (v1.13): DBMF, SIVR, COPX, VTIP, XLP, VNQ, VEA, XLV, FLOT. AIPO reclassified May 7 (v1.14): ThematicETF_ClassificationAudit() COMPLETE. MLPX entry guards CLEARED May 13 (v1.17). Gold reallocation targets confirmed executed May 22 (v1.18). EVs updated at new probability vector May 25 (v1.19): A=7/B=36/C=41/D=5/E=4/F=7. SIVR EV arithmetic corrected May 26 (v1.21): B blended 5.70%→6.00%, total EV +2.92%→+3.03%. AIPO fully re-audited June 2 (v1.30): RAC(0.55)+STG(0.16)+IHC(0.11)+PDT(0.04)+UNCLASSIFIED(0.07 bitcoin miners); EV +3.28%. ENG-50/ENG-55 trend/rotation comparator documentation added per-instrument 2026-07-07 (MLPX, DBMF, XAR, AIPO, COPX, SGOL, SIVR, MAGS) — shadow-mode signal, never feeds M03 or this section's EV; see FRAMEWORK_BACKLOG_ARCHIVE.md ENG-55 and analysis/trend_signal.py.

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
| defensive_equity_buffered_domestic | SPY_realized_volatility, options_buffer_cap_structure, outcome_period_path_dependency | v1.62 July 6 | PROPOSED — NOT YET Active. LOW confidence all six §4.1 cells (M16 4-layer drafted, no full historical analogue for this instrument — see §3 log 2026-07-06 / §6 item 45 [P1]). Instrument candidate: BALT. Formal adoption requires the September 30, 2026 full audit at the earliest. No current allocation. |

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
- ENG-50/ENG-55 trend/rotation comparator (2026-07-07, shadow-mode only — never feeds M03 or this section's EV): Mode 1 return-spread vs 0.5×ITA+0.5×PPA (defense/aerospace equity peers). Orthogonal to the geopolitical_premium sign-flip review noted above — this reads whether XAR is out/underperforming the sector, not whether the sector's assumed EV sign is correct. See FRAMEWORK_BACKLOG_ARCHIVE.md ENG-55 and analysis/trend_signal.py.

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
- GAP-16 sub-condition drivers PROPOSED 2026-07-03 (v1.59, §6 item 44) — NOT YET WIRED (documentation only): Brent (BZ=F) trend + HY OAS trend/level (both already-tracked M18/M11 series, no new fetch). Energy prices rising/stable + calm HY credit = tailwind; falling energy + widening HY credit = headwind.
- ENG-50/ENG-55 trend/rotation comparator (2026-07-07, shadow-mode only — never feeds M03 or the EV mechanism above, despite reusing the same Brent/HY OAS data): Mode 1 return-spread vs Brent (BZ=F), gated by an independently-computed HY OAS confirmation (tightening confirms, widening downgrades to INCONCLUSIVE) — same underlying data as the GAP-16 line above but a fully separate decision path, per the coupling-risk discipline in FRAMEWORK_BACKLOG_ARCHIVE.md's ENG-55 writeup. See analysis/trend_signal.py.

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
- ENG-50/ENG-55 trend/rotation comparator (2026-07-07, shadow-mode only — never feeds M03 or the GAP-16 EV mechanism above): Mode 2 own-trend confirmed by an independently-computed REAL_YIELD_10Y_TREND + DXY agreement gate — reuses the same two data series as GAP-16 above but reimplements the agreement check separately rather than reusing GAP-16's own favorable/unfavorable verdict, per the coupling-risk discipline in FRAMEWORK_BACKLOG_ARCHIVE.md's ENG-55 writeup. See analysis/trend_signal.py.

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
- ENG-50/ENG-55 trend/rotation comparator (2026-07-07, shadow-mode only — never feeds M03 or this section's EV): Mode 1 return-spread vs a weighted composite of 0.671×PAVE + 0.195×QQQM + 0.134×URA. Reuses AIPO's own ComponentVector weights (RAC 0.55/STG 0.16/IHC 0.11, renormalized over their 0.82 sum) as the composite blend weights; PDT (0.04) and UNCLASSIFIED (0.07, bitcoin miners) excluded per the client-confirmed 10%-materiality rule, same threshold that kept COPX's 25% BMEI slice in. See FRAMEWORK_BACKLOG_ARCHIVE.md ENG-55 and analysis/trend_signal.py.
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
- ENG-50/ENG-55 trend/rotation comparator (2026-07-07, shadow-mode only — never feeds M03 or this section's EV): Mode 1 return-spread vs QQQM alone. MAGS's own thesis is concentrated mega-cap tech, so comparing it to the framework's own established, more-diversified STG proxy directly reads whether the concentration is currently outperforming or underperforming the broader AI-capex trade. See FRAMEWORK_BACKLOG_ARCHIVE.md ENG-55 and analysis/trend_signal.py.

#### DBMF
- Components: systematic_trend_following (1.00)
- passive_mandate_eligible: false
- Basis: iMGP DBi Managed Futures Strategy ETF. Actively managed. Replicates top CTA hedge fund portfolios using T-bill collateral + equity/commodity/bond/currency swap agreements. Strategy: systematic trend-following across all major asset classes.
- K-1: NONE — 1940 Act registered fund (ETF structure). No K-1 issued.
- AUM: $3.51B. Expense ratio: 0.85%. Inception: 2019-05-08. 1-year total return: +27.3%.
- Last reviewed: 2026-05-06 (v1.13, initial classification)
- EV: computed fresh each session via M15.blendedScenarioReturn() (ENG-7) -- not stored here; see live computation each session.
- TAX PLACEMENT: ALL ACCOUNTS. No K-1. No swap phantom gain issue.
- GAP-16 sub-condition drivers PROPOSED 2026-07-03 (v1.59, §6 item 44) — NOT YET WIRED to any live EV adjustment (documentation only; range_position.py has no per-role branch for this yet): DXY_TREND direction + cross-asset trend breadth (Brent/Gold/DXY/S&P — reuses the same 4-market check already computed for the §13 TSC evaluation, no new fetch). Strong clean DXY trend + high breadth (3-4 of 4 trending) = tailwind (tracks toward DBMF's upside); flat DXY + low breadth (0-1 trending) = headwind (tracks toward conservative end).
- ENG-50/ENG-55 trend/rotation comparator (2026-07-07, shadow-mode only — never feeds M03): Mode 2 own-trend confirmed by DXY direction + the same 4-market breadth concept as the GAP-16 line above, reimplemented independently rather than sharing GAP-16's own decision logic, per the coupling-risk discipline in FRAMEWORK_BACKLOG_ARCHIVE.md's ENG-55 writeup. See analysis/trend_signal.py.
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
- ENG-50/ENG-55 trend/rotation comparator (2026-07-07, shadow-mode only — never feeds M03 or the GAP-16 EV mechanism above): Mode 2 own-trend confirmed by the same REAL_YIELD_10Y_TREND + DXY agreement gate as SGOL (v1 simplification, client-confirmed — SIVR's IHC slice arguably behaves more like COPX's industrial-commodity comparator, but treating it identically to SGOL is the simpler v1 default). See FRAMEWORK_BACKLOG_ARCHIVE.md ENG-55 and analysis/trend_signal.py.
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
- M07 STATUS: PASS — Canada 36.68% below 40% single-country threshold. Regional ruling per v1.13: Canada + US are separate political/economic regimes. RULING: PASS. Confirmed as formal framework policy 2026-07-03 (v1.58, §6 item 26 closed) — amber flag cleared.
- Last reviewed: 2026-05-07 (v1.14 — entry guard cleared)
- EV (A=7/B=36/C=41/D=5/E=4/F=7): **+2.60%** (updated v1.19; prior at C=44: +2.88%). Ranked #4.
  - A:  (0.75×2 + 0.25×4) = 2.50% × 0.07 = +0.175%
  - B:  (0.75×6 + 0.25×(-5)) = 3.25% × 0.36 = +1.170%
  - C:  (0.75×7 + 0.25×(-6)) = 3.75% × 0.41 = +1.538%
  - D:  (0.75×(-8) + 0.25×(-8)) = -8.00% × 0.05 = -0.400%
  - E:  (0.75×2 + 0.25×(-10)) = -1.00% × 0.04 = -0.040%
  - F:  (0.75×2 + 0.25×3) = 2.25% × 0.07 = +0.158%
  - Total floor: +2.601% ≈ +2.60%. Mining-leverage adjusted estimate: ~+3.2-4.0%.
- GAP-16 sub-condition drivers PROPOSED 2026-07-03 (v1.59, §6 item 44) — NOT YET WIRED (documentation only): DXY_TREND + Brent trend as an imperfect commodity-complex proxy. Flagged: COPX is industrial-metals/copper-mining, not energy, so Brent stands in directionally (both correlate with global growth/reflation and dollar weakness) rather than precisely — a copper-specific series or China PMI would be more accurate but needs new M18 fetcher work (China PMI isn't currently a DataReading, only used ad-hoc via web_search this session).
- ENG-50/ENG-55 trend/rotation comparator (2026-07-07, shadow-mode only — never feeds M03 or this section's EV): Mode 1 return-spread vs a weighted composite of 0.75×HG=F (copper futures, direct — more precise than the imperfect Brent proxy GAP-16 flags above) + 0.25×VEA (BMEI slice, clears the 10%-materiality threshold comfortably so it's kept rather than excluded). See FRAMEWORK_BACKLOG_ARCHIVE.md ENG-55 and analysis/trend_signal.py.
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

#### BALT
- Components: defensive_equity_buffered_domestic (1.00)
- passive_mandate_eligible: false
- Basis: Innovator Defined Wealth Shield ETF. Actively managed, quarterly-laddered FLEX options referencing SPY. Targets ~20% downside buffer and ~2.4-2.6% upside cap per quarterly outcome period (caps reset each quarter based on prevailing options pricing at reset). Marketed by issuer as a bond alternative, not a growth allocation fund.
- AUM: $2.46B. Expense ratio: 0.69%. Inception: 2021-06-30 (~5.0yr track record).
- M07 STATUS (2026-07-06): PASS, no flags — AUM $2.46B, track record 5.0yr, 0% foreign concentration (100% domestic), fee-based revenue type.
- Backtest evidence (2026-07-06, via portfolio_backtest_mcp + market_data_mcp, since-inception through 2026-07-02): CAGR 5.94%, volatility 3.29%, max drawdown -4.9%, Sharpe 1.80 (vs. matched-window 60/40 VTI/BND Sharpe 0.65). No negative calendar year 2022-2026 (2022 full year +2.46% vs SPY -18.62%). Stress tests: 2022 Fed Tightening Cycle (Mar-Dec) +2.51% vs SPY -6.66% (max DD -1.98% vs SPY -22.09%); 2026 Hormuz Closure (Mar-Jun) +1.24% vs SPY +8.36% (cap constrained participation in the V-shaped recovery rally).
- PROPOSED NEW ROLE: defensive_equity_buffered_domestic — see §11.1 and §6 item 45 [P1] for full M16 4-layer detail. LOW confidence all cells; cannot be formally adopted before the September 30, 2026 full audit.
- ADOPTION TRIGGER: client decision to pursue formal role adoption at the September 2026 audit; no trigger has fired yet — this is a logged proposal, not a pending action.
- CURRENT PORTFOLIO ALLOCATION: NONE.
- Last reviewed: 2026-07-06 (ad-hoc session — M07 screen + M16 draft 4-layer calibration; role NOT yet in formal Active status pending September audit adoption decision)

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
