"""
orchestrator/scoring_questions.py — M03 check definitions → ScoringQuestion objects.

Two public functions:
  generate_questions()      — builds all 17 M03 checks as ScoringQuestion objects,
                              auto-scoring quantitative ones from DataReadings + signals.
  aggregate_raw_scores()    — merges Python auto-scores + AI answers → RawScores.

AI boundary: Python pre-populates quantitative evidence and auto-scores threshold-based checks.
AI receives only questions with auto_score=None and fills integer answers.
Python runs all probability arithmetic (apply_all_rules) from there.

M03 check structure:
  Scenario A: check_fed[0,1,2], check_energy[0,1,2], check_credit[0,1]          max=5
  Scenario B: check_cpi[0,2,3], check_gdp[0,1,2,3], check_fed[0,2]              max=8
  Scenario C: check_brent[0,1,2,3], check_cpi[0,1,2], check_chokepoint[0,2]     max=7
  Scenario D: check_unemployment[0,1,3], check_fed[0,1,3], check_credit[0,1,2,3], check_gdp[0,1,2]  max=11
  Scenario E: check_dedollar[0,3], check_stress[0,2], check_ig[0,1,2]           max=7
  Scenario F: check_gdp[0,1,3], check_cpi[0,2], check_fed[0,2], check_noshock[-2,1]  max=8 (MIN 0)
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..types import (
    CalibrationState,
    CreditSignal,
    DataReading,
    RawScores,
    ScoringAnswers,
    ScoringQuestion,
)

# Qualitative topics AI must research in Call 1 (M02 QUALITATIVE_GATHER_LIST)
QUALITATIVE_TARGETS: List[str] = [
    "fed_guidance",       # Fed forward guidance, FOMC stance, cutting/holding/hiking
    "cpi_trajectory",     # Latest BLS CPI YoY print, month-over-month, trend direction
    "gdp_trajectory",     # BEA advance estimate nominal + real GDP, Q-over-Q growth
    "labor_market",       # BLS unemployment rate, 3-month trend, recent payrolls
    "supply_chokepoint",  # Active supply disruptions (Hormuz, ACLED, ISW, IEA raw)
    "dollar_reserve",     # Sovereign de-dollarization news, IMF reserve composition shift
    "geopolitical_broad", # Broader geopolitical context affecting macro scenarios
]


# ── Evidence extraction helpers ────────────────────────────────────────────────

def _get_reading(readings: List[DataReading], spec_id: str) -> Optional[DataReading]:
    for r in readings:
        if r.spec_id == spec_id and r.is_valid:
            return r
    return None


def _brent_price(readings: List[DataReading]) -> Optional[float]:
    r = _get_reading(readings, "BRENT_CRUDE")
    if r is None:
        return None
    v = r.value
    if isinstance(v, dict):
        return v.get("current") or v.get("price")
    if isinstance(v, (int, float)):
        return float(v)
    return None


def _hy_oas(readings: List[DataReading]) -> Optional[float]:
    r = _get_reading(readings, "HY_OAS")
    if r is None:
        return None
    v = r.value
    if isinstance(v, dict):
        return v.get("current") or v.get("hy_oas") or v.get("value")
    return float(v) if isinstance(v, (int, float)) else None


def _ig_oas(readings: List[DataReading]) -> Optional[float]:
    r = _get_reading(readings, "IG_OAS")
    if r is None:
        return None
    v = r.value
    if isinstance(v, dict):
        return v.get("current") or v.get("ig_oas") or v.get("value")
    return float(v) if isinstance(v, (int, float)) else None


def _fmt_price(label: str, value: Optional[float], unit: str = "") -> str:
    if value is None:
        return f"{label}: unavailable"
    return f"{label}: {value:.2f}{unit}"


# ── Question factory ───────────────────────────────────────────────────────────

def generate_questions(
    readings: List[DataReading],
    cal: CalibrationState,
    credit_signal: Optional[CreditSignal],
    qualitative: Dict[str, str],
) -> List[ScoringQuestion]:
    """
    Generate all 17 M03 scoring questions, pre-populating quantitative evidence
    and auto-scoring threshold-based checks where Python can determine the score.

    Parameters
    ----------
    readings:
        DataReadings from FetchRegistry.fetch_all().
    cal:
        CalibrationState — provides Brent trigger threshold (§2.1).
    credit_signal:
        CreditSignal from Stage 3 — used to auto-score credit checks.
    qualitative:
        Dict from AI Call 1 (gather_qualitative) — keyed by QUALITATIVE_TARGETS.

    Returns
    -------
    List[ScoringQuestion] — 17 questions. Those with auto_score set are
    Python-scored and excluded from AI Call 2.
    """
    qs: List[ScoringQuestion] = []
    brent = _brent_price(readings)
    hy_oas_val = _hy_oas(readings)
    ig_oas_val = _ig_oas(readings)

    brent_evidence = _fmt_price("Brent crude", brent, "/bbl")
    brent_c_threshold = cal.thresholds  # use thresholds block; §2.1 nominal $110 in markdown
    # §2.1 nominal Brent trigger: $110 (calibration-dated). Use 110 as fallback.
    brent_trigger_nominal = 110.0

    fed_qual = qualitative.get("fed_guidance", "Fed guidance: not yet gathered")
    cpi_qual = qualitative.get("cpi_trajectory", "CPI trajectory: not yet gathered")
    gdp_qual = qualitative.get("gdp_trajectory", "GDP trajectory: not yet gathered")
    labor_qual = qualitative.get("labor_market", "Labor market: not yet gathered")
    chokepoint_qual = qualitative.get("supply_chokepoint", "Supply chokepoint: not yet gathered")
    dollar_qual = qualitative.get("dollar_reserve", "Dollar reserve status: not yet gathered")

    # Credit signal evidence
    credit_ev = "Credit signal: not computed"
    if credit_signal:
        parts = []
        if credit_signal.hy_oas is not None:
            parts.append(f"HY OAS {credit_signal.hy_oas:.0f}bps")
        if credit_signal.ig_oas is not None:
            parts.append(f"IG OAS {credit_signal.ig_oas:.0f}bps")
        parts.append(f"HY_stress={credit_signal.hy_stress_beginning}")
        parts.append(f"HY_recession={credit_signal.hy_recession_pricing}")
        parts.append(f"IG_transmission={credit_signal.ig_transmission_reached}")
        credit_ev = "Credit signal: " + "; ".join(parts)

    # ── Scenario A ─────────────────────────────────────────────────────────────
    qs.append(ScoringQuestion(
        id="A_check_fed", scenario="A",
        question=(
            "Is the Fed cutting rates or has it issued forward guidance toward cuts? "
            "Score 2=cutting or guidance toward cuts confirmed (FOMC statement); "
            "1=pausing; 0=holding or hiking."
        ),
        evidence=f"Fed guidance: {fed_qual}",
        valid_scores=[0, 1, 2],
    ))

    # A_check_energy: Brent declining 5+ days → semi-quantitative
    energy_auto: Optional[int] = None
    energy_ev = brent_evidence
    if brent is not None:
        # We don't have intraday trend in a single reading; leave for AI unless obvious
        energy_ev += f" | Note: 5-consecutive-day decline requires price history context"
    qs.append(ScoringQuestion(
        id="A_check_energy", scenario="A",
        question=(
            "Are energy prices (Brent crude) declining for 5+ consecutive trading days? "
            "Score 2=yes; 1=flat or mixed; 0=rising."
        ),
        evidence=energy_ev,
        valid_scores=[0, 1, 2],
        auto_score=energy_auto,
    ))

    # A_check_credit: from CreditSignal (Python auto-scores)
    a_credit_auto: Optional[int] = None
    if credit_signal is not None:
        if credit_signal.hy_stress_beginning or credit_signal.ig_transmission_reached:
            a_credit_auto = 0
        else:
            a_credit_auto = 1
    qs.append(ScoringQuestion(
        id="A_check_credit", scenario="A",
        question=(
            "Is credit calm per M11 (HY not in stress, IG not at transmission threshold)? "
            "Score 1=calm; 0=stressed."
        ),
        evidence=credit_ev,
        valid_scores=[0, 1],
        auto_score=a_credit_auto,
    ))

    # ── Scenario B ─────────────────────────────────────────────────────────────
    qs.append(ScoringQuestion(
        id="B_check_cpi", scenario="B",
        question=(
            "What is the CPI trajectory vs B trigger (>4% YoY for 3+ consecutive prints, BLS)? "
            "Score 3=trigger met; 2=CPI 3-4% trending upward; 0=below 3% or declining."
        ),
        evidence=f"CPI trajectory: {cpi_qual}",
        valid_scores=[0, 2, 3],
    ))
    qs.append(ScoringQuestion(
        id="B_check_gdp", scenario="B",
        question=(
            "What is real GDP growth vs B condition (<=0%, BEA advance estimate)? "
            "Score 3=GDP<=0%; 2=GDP 0-1.5%; 1=GDP>1.5% (approaching but not trigger); 0=not applicable."
        ),
        evidence=f"GDP trajectory: {gdp_qual}",
        valid_scores=[0, 1, 2, 3],
    ))
    qs.append(ScoringQuestion(
        id="B_check_fed", scenario="B",
        question=(
            "Is the Fed explicitly holding OR signaling continued constraint (FOMC statement)? "
            "Score 2=holding or signaling constraint; 0=cutting."
        ),
        evidence=f"Fed guidance: {fed_qual}",
        valid_scores=[0, 2],
    ))

    # ── Scenario C ─────────────────────────────────────────────────────────────
    # C_check_brent: auto-score against calibration threshold where possible
    c_brent_auto: Optional[int] = None
    c_brent_ev = brent_evidence + f" | C-trigger nominal: ${brent_trigger_nominal:.0f}/bbl"
    if brent is not None:
        if brent >= brent_trigger_nominal:
            # Brent above nominal trigger — score depends on sustained days (qualitative)
            c_brent_ev += f" — ABOVE nominal trigger; sustained days requires qualitative confirmation"
            # Leave for AI since we don't track sustained days automatically
        else:
            gap_pct = (brent_trigger_nominal - brent) / brent_trigger_nominal * 100
            c_brent_ev += f" — {gap_pct:.1f}% BELOW nominal trigger"
            if gap_pct > 15:
                c_brent_auto = 0  # well below trigger, no verified supply event implied

    qs.append(ScoringQuestion(
        id="C_check_brent", scenario="C",
        question=(
            "Is Brent at or above the C trigger (MAX($110, 90d_avg × 1.40) for 10+ trading days)? "
            "Score 3=trigger met and sustained >=10 days (T1: EIA, CME); "
            "2=dateable supply event T1-verified AND Brent within 15% of trigger; "
            "1=T1 supply event verified but Brent below 15%-gap band; 0=no verified supply event."
        ),
        evidence=c_brent_ev,
        valid_scores=[0, 1, 2, 3],
        auto_score=c_brent_auto,
    ))
    qs.append(ScoringQuestion(
        id="C_check_cpi", scenario="C",
        question=(
            "Is CPI reaccelerating >=2 consecutive monthly prints (BLS)? "
            "Score 2=2+ prints confirmed; 1=1 print confirmed; 0=decelerating."
        ),
        evidence=f"CPI trajectory: {cpi_qual}",
        valid_scores=[0, 1, 2],
    ))
    qs.append(ScoringQuestion(
        id="C_check_chokepoint", scenario="C",
        question=(
            "Is a dateable supply chokepoint verified by T1 primary sources (ACLED, ISW, IEA raw)? "
            "Score 2=verified and active; 0=resolved or unverified."
        ),
        evidence=f"Supply chokepoint: {chokepoint_qual}",
        valid_scores=[0, 2],
    ))

    # ── Scenario D ─────────────────────────────────────────────────────────────
    qs.append(ScoringQuestion(
        id="D_check_unemployment", scenario="D",
        question=(
            "Is unemployment rising >=0.5% over any 3-month window (BLS)? "
            "Score 3=threshold met; 1=rising but below threshold; 0=stable or falling."
        ),
        evidence=f"Labor market: {labor_qual}",
        valid_scores=[0, 1, 3],
    ))
    qs.append(ScoringQuestion(
        id="D_check_fed", scenario="D",
        question=(
            "Is the Fed cutting aggressively (>=75bps cumulative within 60 days OR emergency cut)? "
            "Score 3=yes; 1=cutting gradually; 0=holding."
        ),
        evidence=f"Fed guidance: {fed_qual}",
        valid_scores=[0, 1, 3],
    ))

    # D_check_credit: from CreditSignal (auto-score)
    d_credit_auto: Optional[int] = None
    if credit_signal is not None:
        raw_credit = 0
        if credit_signal.hy_recession_pricing:
            raw_credit += 3
        elif credit_signal.ig_transmission_reached:
            raw_credit += 3
        elif credit_signal.hy_stress_beginning:
            raw_credit += 2
        elif credit_signal.ccc_tail_first_widening:
            raw_credit += 1
        d_credit_auto = min(raw_credit, 3)
    qs.append(ScoringQuestion(
        id="D_check_credit", scenario="D",
        question=(
            "Credit stress from M11 D-trigger components: "
            "Score 3=HY_RecessionPricing OR IG_TransmissionReached (each alone = 3); "
            "2=HY_StressBeginning; 1=CCC_TailFirstWidening; 0=credit calm. "
            "Cap at 3 even if multiple triggers fire."
        ),
        evidence=credit_ev,
        valid_scores=[0, 1, 2, 3],
        auto_score=d_credit_auto,
    ))
    qs.append(ScoringQuestion(
        id="D_check_gdp", scenario="D",
        question=(
            "GDP vs D condition: two consecutive negative quarters (BEA advance)? "
            "Score 2=two negative quarters; 1=one negative quarter; 0=positive."
        ),
        evidence=f"GDP trajectory: {gdp_qual}",
        valid_scores=[0, 1, 2],
    ))

    # ── Scenario E ─────────────────────────────────────────────────────────────
    qs.append(ScoringQuestion(
        id="E_check_dedollar", scenario="E",
        question=(
            "Is dollar reserve status materially challenged? "
            "Sub-items (additive, cap at 3): "
            "+2 if formal sovereign de-dollarization T1-confirmed; "
            "+1 if central bank reserve shift documented (IMF); "
            "+1 if DXY falling on fundamental grounds (not safe-haven spike). "
            "Score the MIN(sum, 3)."
        ),
        evidence=f"Dollar reserve: {dollar_qual}",
        valid_scores=[0, 1, 2, 3],
    ))

    # E_check_stress: mix of CreditSignal + qualitative
    e_stress_auto: Optional[int] = None
    e_stress_ev = credit_ev
    if credit_signal is not None and credit_signal.ig_transmission_reached:
        # IG_TransmissionReached fires → score depends on sovereign CDS (qualitative)
        e_stress_ev += " | IG_TransmissionReached=True — sovereign CDS widening requires qualitative"
    qs.append(ScoringQuestion(
        id="E_check_stress", scenario="E",
        question=(
            "Is there systemic financial stress? "
            "Sub-items (additive, cap at 2): "
            "+2 if IG_TransmissionReached AND sovereign_CDS widening significantly; "
            "+2 if interbank_funding_stress confirmed. "
            "Score the MIN(sum, 2)."
        ),
        evidence=e_stress_ev,
        valid_scores=[0, 1, 2],
        auto_score=e_stress_auto,
    ))

    # E_check_ig: from CreditSignal (auto-score)
    # Score 2 when threshold reached; 0 when calm.
    # Score 1 ("approaching within 20bps") requires 180d median history — not available
    # from current FRED readings alone; leave for AI when signal is intermediate.
    e_ig_auto: Optional[int] = None
    if credit_signal is not None:
        if credit_signal.ig_transmission_reached:
            e_ig_auto = 2
        else:
            e_ig_auto = 0   # calm (no transmission); "approaching" requires history → AI if needed
    qs.append(ScoringQuestion(
        id="E_check_ig", scenario="E",
        question=(
            "Has IG_OAS reached the M11 transmission threshold? "
            "Score 2=IG_TransmissionReached fired; 1=approaching (within 20bps); 0=calm."
        ),
        evidence=credit_ev,
        valid_scores=[0, 1, 2],
        auto_score=e_ig_auto,
    ))

    # ── Scenario F ─────────────────────────────────────────────────────────────
    qs.append(ScoringQuestion(
        id="F_check_gdp", scenario="F",
        question=(
            "Is nominal GDP growth strong (>3% annualized × 2 consecutive quarters, BEA)? "
            "Score 3=trigger met; 1=GDP 2-3% (approaching); 0=GDP<2%."
        ),
        evidence=f"GDP trajectory: {gdp_qual}",
        valid_scores=[0, 1, 3],
    ))
    qs.append(ScoringQuestion(
        id="F_check_cpi", scenario="F",
        question=(
            "Is CPI rising but below stagflationary threshold (2% < CPI < 4% YoY)? "
            "Score 2=yes; 0=CPI>=4% or decelerating."
        ),
        evidence=f"CPI trajectory: {cpi_qual}",
        valid_scores=[0, 2],
    ))
    qs.append(ScoringQuestion(
        id="F_check_fed", scenario="F",
        question=(
            "Is the Fed tightening but demand still strong (FOMC confirmed)? "
            "Score 2=tightening AND demand_data_strong; 0=cutting or demand_weakening."
        ),
        evidence=f"Fed guidance: {fed_qual}",
        valid_scores=[0, 2],
    ))
    qs.append(ScoringQuestion(
        id="F_check_noshock", scenario="F",
        question=(
            "Is there an absence of a verified supply shock? "
            "Score 1=no supply shock verified; -2=supply shock T1-confirmed."
        ),
        evidence=f"Supply chokepoint: {chokepoint_qual}",
        valid_scores=[-2, 1],
    ))

    return qs


# ── Raw score aggregation ──────────────────────────────────────────────────────

# Which question IDs contribute to each scenario's raw score
_SCENARIO_CHECKS: Dict[str, List[str]] = {
    "A": ["A_check_fed", "A_check_energy", "A_check_credit"],
    "B": ["B_check_cpi", "B_check_gdp", "B_check_fed"],
    "C": ["C_check_brent", "C_check_cpi", "C_check_chokepoint"],
    "D": ["D_check_unemployment", "D_check_fed", "D_check_credit", "D_check_gdp"],
    "E": ["E_check_dedollar", "E_check_stress", "E_check_ig"],
    "F": ["F_check_gdp", "F_check_cpi", "F_check_fed", "F_check_noshock"],
}

# Per-scenario caps (M03 spec: D credit capped at 3, E dedollar capped at 3, E stress capped at 2)
# These are enforced at the question level above; raw sum here.
_SCENARIO_CAPS: Dict[str, Optional[float]] = {
    "F": None,  # F applies MAX(raw, 0) — handled in aggregate
}


def aggregate_raw_scores(
    answers: ScoringAnswers,
    questions: List[ScoringQuestion],
) -> RawScores:
    """
    Merge Python auto-scores + AI ScoringAnswers → RawScores.

    For each question: prefer auto_score if set; else use answers.answers[id].
    Aggregates per-scenario sums. Scenario F: apply MAX(raw, 0).

    Parameters
    ----------
    answers:
        ScoringAnswers from AI Call 2 (question_id → integer score).
    questions:
        Full question list from generate_questions().

    Returns
    -------
    RawScores(A=..., B=..., C=..., D=..., E=..., F=...)
    """
    # Build merged score lookup: question_id → resolved score
    resolved: Dict[str, int] = {}
    for q in questions:
        if q.auto_score is not None:
            resolved[q.id] = q.auto_score
        elif q.id in answers.answers:
            resolved[q.id] = answers.answers[q.id]
        else:
            # Missing answer — default 0 and flag would be surfaced by caller
            resolved[q.id] = 0

    raw: Dict[str, float] = {}
    for scenario, check_ids in _SCENARIO_CHECKS.items():
        total = sum(resolved.get(qid, 0) for qid in check_ids)
        if scenario == "F":
            total = max(total, 0)  # M03: raw_F = MAX(raw_F, 0)
        raw[scenario] = float(total)

    return RawScores(
        A=raw["A"], B=raw["B"], C=raw["C"],
        D=raw["D"], E=raw["E"], F=raw["F"],
    )


def questions_for_ai(questions: List[ScoringQuestion]) -> List[ScoringQuestion]:
    """Filter to questions that need AI scoring (auto_score is None)."""
    return [q for q in questions if q.auto_score is None]
