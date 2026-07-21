# Portfolio State — 2026-07-21

**Calibration State:** 1.66
**Scenario probabilities:** A=13% / B=39% / C=39% / D=3% / E=3% / F=3%
**Primary driver:** Iran/Hormuz conflict sharply re-escalated (10th consecutive night of US strikes vs 4th last session, 3 US KIA, tanker hit in Strait of Hormuz July 20, gas ~$4/gal) against a Fed holding rates with no forward guidance (Warsh: inflation "too high", FOMC split hike-vs-hold) -- pushed C 23.5%->39%, held B at 39% (both above 30% co-elevation threshold, documented as independent signal families). E collapsed 11.75%->3% on IMF COFER Q1 2026 data showing dollar reserve share rose (57.13% vs 56.42%), no de-dollarization event this quarter. Correction same session: DBMF Sec13 FAILED flag retracted (data bug, ENG-68); ENG-67 status corrected to CLOSED (was mischaracterized as open).

## Open Triggers
- Iran war: 10th consecutive night of US strikes as of July 20, 2026; naval blockade active since July 14; 3 US service members killed, ~100 injured since July 7; tanker struck in Strait of Hormuz July 20 (UKMTO); no de-escalation signal -- watch for Brent breaching the $110 nominal C-trigger (currently $91.09, 17.2% below).
- June CPI (3.5% headline/2.6% core, released July 14) predates the current oil-price re-acceleration (Brent ~$72 early June to $91 now) -- July print (BLS, Aug 12) is the key test of whether C's score reverses upward further.
- Next FOMC July 28-29 -- no cut expected; watch guidance language given committee reportedly split hike-vs-hold.
- GDPNow next update July 27 (currently 1.7% for Q2, up from 1.3% on July 8).
- CORRECTION: the DBMF Sec13 'FAILED' flag reported earlier this session was a false positive. The underlying DBMF_3M_RETURN reading was corrupted (it was actually MAGS's price series, not DBMF's -- confirmed via direct market_data_mcp check after client challenge). DBMF's real 3-month return is +2.53%, not -4.19%; on the correct figure the Sec13 condition does not fire. Logged as ENG-68 (data-integrity, HIGH). DBMF's ADD directive (blended_conservative_return_pct 10.77%) stands on its EV math, unaffected by this correction.
- SIVR/COPX role-repricing divergence (Sec9.5): SIVR -24.63% 30d, COPX -17.71% 30d, both vs broad market +0.13% -- underperforming inflation-hedge role thesis by >15pp threshold.
- SGOL: GAP-16 range-position read 'unfavorable' in Scenario B (rising real yields) -- blended_conservative_return_pct now negative (-0.06%) despite an ADD directive from position-sizing; flag before executing.
- XAR: GAP-17 sign-flip approach decided (v1.66) but replacement Scenario C/E numbers not yet derived; still HOLD everywhere; still gated to March 31, 2027 audit at earliest.
- CORRECTION: ENG-67 (C_check_brent auto-scorer) is CLOSED (fixed 2026-07-14) and confirmed working correctly this session -- auto_score correctly returned None/deferred to Claude. An earlier note this session incorrectly called it 'still open' with a 'fix still needed'; that was wrong, retracted.
- AIPO: 14% of component weight remains unclassified, excluded from EV -- verify at next Sec11 audit.

## Open Decisions
- Relative IRA (...469) rebalance (SGOL 4.85%->9%, VTIP 12.25%->12%, DBMF 15.71%->17%, funded from SGOV 26.17%->20%) reconfirmed feasible tonight at 3.88% portfolio return, floor clear -- still awaiting Evgeny's staged-vs-lump-sum execution call.
- Relative Roth (...466) corrected target (AIPO 10/MLPX 34/VTIP 45/DBMF 11) reconfirmed feasible at 3.56%, floor clear -- still awaiting manual entry into the allocation sheet's Target column.
- DBMF/MLPX/SGOL(SGOV) 40/40/20 simplification -- FeasibilityCheck re-run fresh tonight for Primary IRA (6.43% vs 3.49% required, 1.41x), Primary Roth (6.43% vs 3.18% required, 1.6x), and Acc4 taxable (6.62%, drawdown-adjusted 26.50) -- all feasible; still awaiting Evgeny's go/no-go; confirmed unsafe for both Relative FLOOR_THEN_RETURN accounts.
- XAR thesis: flip-within-role sign revision on Scenario C/E (not a new RoleID split, per v1.66) -- numbers not yet derived, LOW confidence, gated to March 31, 2027 audit at earliest. Directive remains HOLD everywhere; do not execute TRIM/EXIT.

_Generated via MCP (Pattern B — Claude app)._