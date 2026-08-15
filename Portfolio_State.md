# Portfolio State — 2026-08-15

**Calibration State:** 1.70
**Scenario probabilities:** A=10% / B=42% / C=31% / D=3% / E=3% / F=10%
**Primary driver:** Fresh scoring shifted probabilities materially: B 37.6%->41.8%, C 28.2%->31.3%, A 18.8%->10.4%, E 9.4%->3.0%, F 3.0%->10.4%, D unchanged at 3.0%. Drivers: E_check_dedollar scored down (IMF COFER Q1 2026 confirms USD reserve share RISING to 57.13%, no formal de-dollarization event, no clear fundamental DXY decline -- consistent with yesterday's correction, not a new finding). F_check_gdp scored HIGH on T1 current-dollar GDP data not previously scored this granularly: Q1 nominal +5.1-5.6%, Q2 nominal +7.9%, both above the 3% x2-quarter trigger. B stays elevated on Fed's continued hawkish 9-3 hold (July 29) plus GDP settling into 0-1.5%. C stays elevated on the still-unresolved, T1-verified Hormuz chokepoint (60-day toll-free MoU window expiring ~Aug 16-17, talks stalled, Araghchi rejecting resumption) even though Brent sits 19.5% below its $110 trigger. B-vs-C >30% constraint (M03.BvsCRule) applies -- justification: the two theses are concurrently live and non-contradictory (B = grinding Fed-constrained slowdown with decelerating-but-elevated inflation; C = acute unresolved chokepoint risk independent of the broader disinflation trend, with a concrete 48hr catalyst). DBMF: client-confirmed full exit this session; reclassified Instrument_Classification.md \u00a711.3->\u00a711.4 (commit 636e483, pushed). Trend signal via CLI fallback (MCP tool hit 60s TIMEOUT; verified no false commit before falling back, per ENG-33/ENG-49 discipline) correctly evaluated only the 4 actually-held ENG-55 tickers post-reclassification (XAR/MLPX/SGOL/AIPO), all INCONCLUSIVE; AIPO medium-term trend continues worsening (-9.00pp vs -8.41pp prior session). VTIP live-checked via advisor_evaluate_allocation (Primary IRA only): blended EV +0.39%, directive ADD, no dual-role conflict; Primary IRA feasibility shortfall reconfirmed at 2.46pp. NEW FINDING: VTIP's Scenario B range [1,4]% (3pp) clears its own 2.0pp GAP-18 width gate exactly like its Scenario C range does, and B is this session's dominant scenario -- yet VTIP produced no range_position_advisory this session (only SGOL did), despite FRAMEWORK_BACKLOG.md confirming the GAP-16-style mechanism half of ENG-72 CLOSED 2026-08-14 with a full regression suite (1006 passed/46 skipped/0 failed) including VTIP-specific tests. Needs investigation next coding session, separate from ENG-72's still-open \u00a713 M19 gap.

## Open Triggers
- Iran/Hormuz chokepoint remains T1-verified active; 60-day toll-free MoU window (from June 17-19 signing) expires ~Aug 16-17 -- imminent catalyst; C_check_chokepoint stays at 2 until a dateable de-escalation event fires
- August CPI (Sept 11, 2026, 8:30am ET) is the next data point -- July print 3.4% YoY, 3rd consecutive deceleration
- AIPO trend signal WEAKENING, medium-term window now -9.00pp (worsened from -8.41pp last session) -- relevant to client's own stated AIPO exit trigger
- CCC OAS at 1,024bps, still sharply diverging from calm HY(271bps)/IG(79bps) -- unresolved tail-widening-first pattern
- MOVE index 30d/90d rolling averages still uncomputable via market_get_history (series stops 2026-07-17) -- unresolved data-source gap
- Sept 30 audit: broad_market_equity_international A/B/C MEDIUM-confidence §4.1 proposals pending adjudication
- XAR two-quarter procedural gate unchanged through March 2027 -- GAP-17 sign-split still unresolved
- Next FOMC Sept 15-16, 2026 -- July's hold was 9-3 hawkish; real two-sided risk into this meeting
- NEW: VTIP range_position_advisory did not fire this session despite meeting its own 2.0pp width gate under dominant Scenario B's [1,4]% (3pp) range -- investigate next coding session, separate from the §13 M19 gap
- ENG-72 §13 M19 sustaining-condition gap for VTIP still fully open (no item number assigned yet) -- needs its own design pass

## Open Decisions
- Relative IRA/Roth: floor check CLEAR again this session -- SCHD/VYMI rotation tested, improves margin but not required; still undecided whether to execute as an A-snapback buffer
- Taxable Acc4 (6668-9768) target discrepancy still needs reconciliation (aggressive sell-down plan vs. current live sheet targets)
- AIPO exposure in Primary IRA (~13.7%) and Primary Roth (~23.1%) still not reviewed against the AI-bubble thesis applied to Acc4
- SCHD/VYMI dividend-sleeve logic still not evaluated for Primary IRA/Roth or Acc3
- Primary IRA feasibility shortfall reconfirmed at 2.46pp this session (TARGET_THEN_RETURN, portfolio return 1.27% vs required 3.74%) -- root cause still likely SCHD's pending §4.1 calibration cells, not yet investigated
- VTIP: live-checked in Primary IRA only (EV +0.39%/ADD/no conflict) -- full M06 recommendation review across all 4 VTIP-holding accounts (Primary IRA/Roth, Relative IRA/Roth) not completed this session

_Generated via MCP (Pattern B — Claude app)._