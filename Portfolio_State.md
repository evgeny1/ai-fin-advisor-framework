# Portfolio State — 2026-07-14

**Calibration State:** 1.66
**Scenario probabilities:** A=12% / B=47% / C=24% / D=3% / E=12% / F=3%
**Primary driver:** Hormuz naval blockade reinstated (T1-confirmed: CENTCOM/NPR/CNN/Axios) vs. cooler June CPI print (headline 3.5% vs 4.2% May; core 2.6% vs 2.9%) -- net scenario shift: C down 31.33%->23.5%, A/E up 7.83%->11.75% each, B flat 47%, D/F flat 3%. Live discovery: C_check_brent auto-scorer (scoring_questions.py) scored 0 despite the T1-verified blockade because Brent's absolute price hasn't closed the gap to the $110 nominal trigger -- logged as ENG-67 (OPEN), likely understates C tonight. FeasibilityCheck also run fresh under tonight's mix for Relative IRA, Relative Roth, and the Primary IRA/Roth/Acc4 40/40/20 simplification -- all reconfirmed feasible.

## Open Triggers
- Hormuz blockade reinstated 2026-07-14 (4pm ET), 4th consecutive night of US strikes on Iran, missile fire reaching Jordan (intercepted) and Kuwait -- no de-escalation signal, if anything more active than last session
- June CPI cooled to 3.5% headline / 2.6% core (BLS) but multiple T1 sources confirm this predates the renewed oil spike -- watch the July print (BLS, Aug 12) for reversal
- GDPNow ~1.3% for Q2 2026, next Atlanta Fed update July 16
- China NBS Manufacturing PMI 50.3 in June, third consecutive expansionary month -- no China-demand-collapse signal for COPX
- Central bank gold accumulation narrative and nuclear policy support (US/EU/Japan/UK, all 4 confirmed intact) both hold up this session
- Fed held 3.50-3.75% June 17 under new Chair Warsh, forward guidance removed entirely, hawkish dot plot (median 2026 now 3.8%) -- next FOMC July 29

## Open Decisions
- Relative IRA (...469) rebalance (SGOL 4.85%->9%, VTIP 12.25%->12%, DBMF 15.71%->17%, funded from SGOV 26.02%->20%) reconfirmed feasible under tonight's mix at 3.11% portfolio return (down from 3.91% under last session's C-heavier mix), floor clear -- still awaiting Evgeny's staged-vs-lump-sum execution call given SGOL/SIVR's recent declines
- Relative Roth (...466) corrected target (AIPO 10/MLPX 34/VTIP 45/DBMF 11) reconfirmed feasible at 2.78% (down from 3.39%), floor clear -- still awaiting manual entry into the allocation sheet's Target column
- DBMF/MLPX/SGOL(SGOV) 40/40/20 simplification -- FeasibilityCheck now run fresh for Primary IRA (5.48% vs 3.36% required, 1.39x), Primary Roth (5.48% vs 3.12% required, 1.59x), and Acc4 taxable (5.29%, drawdown-adjusted 21.16) -- all feasible; still awaiting Evgeny's go/no-go, confirmed unsafe for both Relative FLOOR_THEN_RETURN accounts
- XAR thesis: GAP-17 approach now decided by Evgeny -- flip-within-role sign revision on Scenario C/E, not a new RoleID split (Calibration_State.md v1.66) -- numbers not yet derived, still LOW confidence, still gated to the March 31, 2027 audit at the earliest. Directive remains HOLD everywhere; do not execute TRIM/EXIT

_Generated via MCP (Pattern B — Claude app)._