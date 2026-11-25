# Portfolio State — 2026-11-25

**Calibration State:** 1.71
**Scenario probabilities:** A=13% / B=32% / C=26% / D=3% / E=6% / F=19%
**Primary driver:** AI-equity unwind (S&P 500 -3.70% to 6,910 on Nov 20, technical correction after 7 down days; Nasdaq -5.28%, negative YTD; Nvidia leadership scandal after Huang resignation) colliding with a Fed set to hike again (held 3.75-4.00% Oct 28 on 10-2 with Cook/Hammack for a hike; Oct minutes: majority sees more hikes needed; Dec 8-9 hike >90% priced). Oil shock fading: Brent 89.87 vs 117.64 early Oct (IEA: Gulf exports recovering, Q4 surplus) though Hormuz traffic still ~65% below pre-conflict with continuing attacks. Data: Oct CPI +0.4% m/m (Sept +0.6%), core +0.3% 3rd month, Oct YoY unpublished (2025 shutdown base); Q3 GDP 3.4% real / 5.6% nominal; Oct payrolls +165k, UR 4.1%, U-6 7.9%. Scoring (59/66 specs valid): A 5.9->12.9, B 29.4->32.3, C 23.5->25.9, D 5.9->3.0, E 5.9->6.5, F 29.4->19.4. B dominant but 30-39% band = half-size, high-urgency-only execution. No directive changes. NOTE: write-back executed Nov 25 for the Nov 20 session (server cache had been lost; restored by re-running computation and re-applying the identical Nov 20 answers, which reproduced the identical vector); all research, prices and account values are Nov 20.

## Open Triggers
- Q3 GDP second estimate Nov 25 (advance 3.4% real, 5.6% nominal); Nov jobs Dec 4 (Oct +165k, UR 4.1%, U-6 7.9%); FOMC Dec 8-9 (25bp hike >90% priced, 50bp ~9%); Nov CPI Dec 10 (Oct +0.4% m/m, core +0.3%; Oct YoY unpublished)
- Iran/Hormuz T1-active: talks via Qatar/Vance continue with no breakthrough; Iran drone attack on US radar in Bahrain Nov 18; vessel traffic ~65% below pre-conflict but oil flows recovering under US escort; Iran exports near zero under US blockade. XAR_CONFLICT_GATE 0
- Brent BZ=F 89.87 vs C trigger $142.37 (MAX($110, 90d avg 101.69 x 1.4)), 36.9% below -> C_check_brent 1. Dated Brent below nearby futures since ~Nov 9, so both bases now score 1
- Credit widening but no trigger (Nov 20): HY 352 (trigger ~425), IG 94 (trigger ~138), CCC 1,361. 30d CCC +34bp vs HY +19bp (1.8x) - no ratio divergence; D_check_credit auto 0 confirmed by hand. Nov 25 re-run showed further widening: HY 372, IG 98, CCC 1,405
- Rates: 10Y 5.04, 30Y 5.40 (back below 5.50 M17 E warning), term premium 0.986 (back below 1.00); E-watch CLEAR (was FISCAL_STRESS_BUILDING); e_pathway RESERVE_EROSION; 10Y-2Y +28bp, 10Y-3M +70bp
- Gold 3,539 (one-year low Nov 16 on yields/dollar/hike odds); CB buying Q3 321t (most since Q4 2024), PBoC streak through Oct, Poland at 700t target may pause. SGOL gate 1. DXY 103.84 (+1.9% over 8 wks); USD reserve share 56.7% Q2
- AI capex intact: Q3 hyperscaler capex $201.9B (+108% YoY); Amazon ~$220B 2026, Alphabet $195-205B held, 2027 up; FCF negative except Microsoft. AIPO gate 1. China NBS PMI Oct 49.3 (COPX gate 2)
- Trend signals Nov 20 (shadow, never a directive): AIPO WEAKENING (-6.20pp short / -12.37pp medium vs PAVE/QQQM/URA); XAR INCONCLUSIVE (-1.15/-8.10 vs ITA/PPA); SGOL INCONCLUSIVE (own down/down, no macro agreement); MLPX labeled INCONCLUSIVE but HY_OAS gate missing (effectively DATA_UNAVAILABLE, ENG-60). Store: 4 entries added, 12 forward outcomes filled, committed
- Q3 audit v1.71 PARTIAL items still open (Calibration_State 6 items 49/50/51)

## Open Decisions
- Primary Roth 9838: AIPO 18.3% (Nov 20 prices) vs 0% sheet target, but framework rates AIPO HOLD at +3.29% EV; at sheet targets the account returns 0.28% vs 4.36% required (4.08pp shortfall, was 4.48pp) - keep or change the 0% target
- VYMI (EV -5.34%, REDUCE) and SCHD (EV -0.13%, REDUCE_TO_MIN; below SGOV +0.81%) carry reduce directives with DualRoleConflict (dominant roles clear: intl broad equity 68%, domestic broad equity 49%); M06 HoldJustification with EV math required before any hold. B at 32.3% caps any rotation at 50% and high-urgency only
- SGOL (EV +1.14%) and VTIP (EV +0.06%) carry ADD directives; before any SGOL add run M14.EntryExtensionGuard and the war-premium entry guard (Hormuz still active). Primary IRA scenario-weighted SGOL 16.9% vs current 5.8%
- Primary IRA 6469 feasibility shortfall 3.53pp (0.74% vs 4.28% required; was 3.91pp). Taxable 9768 feasible at 0.87% (drawdown-adjusted 3.46); VTI REDUCE_TO_MIN (EV +0.35%)
- Relative IRA/Roth: floors intact (expected 1.29% / 0.90% at sheet targets; ~1.20% at current Relative IRA weights); Relative sheet last edited Aug 14 - share counts may be stale; PassiveMandateAbsent warnings on MLPX (Relative IRA 20.2%, Relative Roth 33.9%) and VTIP (Relative Roth 17.4%)
- Brent basis decision (futures vs Dated) is currently moot - both score 1 this session - but still unresolved for when they diverge again

_Generated via MCP (Pattern B — Claude app)._