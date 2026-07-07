"""
advisor/config/calibration.py

Markdown parser: Calibration_State.md → CalibrationState dataclass.
Called once per session by M12.fetchCalibrationState().
All thresholds are read from the live file; no values are hard-coded here.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional

import yaml

from ..types import (
    CalibrationLogEntry,
    CalibrationState,
    CascadeBlock,
    ComponentWeight,
    FloorParams,
    InstrumentEntry,
    MultiplierBlock,
    RegimeBlock,
    ReturnRange,
    ThesisConditionEntry,
    ThresholdBlock,
)

# ── Regex constants ────────────────────────────────────────────────────────────

# §4.1 cell: [-2, +4]★  |  [10, 20]  |  [-5, +15]★
_CELL_RE = re.compile(
    r"\[([+\-]?\d+(?:\.\d+)?),\s*([+\-]?\d+(?:\.\d+)?)\](★|⚑|⚠)?"
)
_CONFIDENCE_MAP: Dict[Optional[str], str] = {
    "★": "HIGH",
    "⚑": "PENDING_MEDIUM",
    "⚠": "PENDING_LOW",
    None: "MEDIUM",
}

# §11 component line: role_id (weight) + role_id (weight)
_COMP_RE = re.compile(r"([a-zA-Z_][a-zA-Z0-9_%]*)\s*\(([\d.]+)\)")

_SCENARIOS = ("A", "B", "C", "D", "E", "F")


# ── Low-level helpers ──────────────────────────────────────────────────────────


def _between(text: str, start: str, end: str) -> str:
    """Return substring of text between start and end markers (exclusive).
    Returns empty string if start not found; text[i:] if end not found."""
    i = text.find(start)
    if i == -1:
        return ""
    i += len(start)
    j = text.find(end, i)
    return text[i:j] if j != -1 else text[i:]


def _table_rows(section: str) -> List[List[str]]:
    """Parse a Markdown pipe table into rows of stripped cell strings.
    Skips the header row and separator rows (contain '---')."""
    rows: List[List[str]] = []
    for line in section.splitlines():
        s = line.strip()
        if s.startswith("|") and "---" not in s:
            cols = [c.strip() for c in s.strip("|").split("|")]
            if len(cols) >= 2 and any(c for c in cols):
                rows.append(cols)
    return rows[1:]  # drop header row


def _parse_cell(cell: str) -> Optional[ReturnRange]:
    """Parse a §4.1 return table cell like '[-2, +4]★' into ReturnRange."""
    m = _CELL_RE.search(cell)
    if not m:
        return None
    lo = float(m.group(1))
    hi = float(m.group(2))
    conf = _CONFIDENCE_MAP.get(m.group(3), "MEDIUM")
    return ReturnRange(conservative=lo, upside=hi, confidence=conf)


def _s(pattern: str, text: str, default: float = 0.0) -> float:
    """Search for a float-valued pattern; return default if not found."""
    m = re.search(pattern, text)
    return float(m.group(1)) if m else default


# ── Section parsers ────────────────────────────────────────────────────────────


def _parse_version_date(text: str):
    """Extract (version_str, last_updated_str) from file header."""
    m = re.search(r"#\s*Version:\s*(\S+)\s+Last updated:\s*([^\n(]+)", text)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return "unknown", "unknown"


def _parse_thresholds(text: str) -> ThresholdBlock:
    """Parse §1 credit signal thresholds (relative to 180d trailing median)."""
    s1  = _between(text, "## Section 1", "## Section 2")
    s11 = _between(s1, "### 1.1", "### 1.2")
    s12 = _between(s1, "### 1.2", "### 1.3")
    s13 = _between(s1, "### 1.3", "\n---")

    def bps(pat: str, section: str) -> int:
        m = re.search(pat, section)
        return int(m.group(1)) if m else 0

    def days(pat: str, section: str) -> int:
        m = re.search(pat, section)
        return int(m.group(1)) if m else 0

    ccc_ratio_m = re.search(r"(\d+(?:\.\d+)?)x\s*composite", s13)
    ccc_ratio   = float(ccc_ratio_m.group(1)) if ccc_ratio_m else 3.0

    ccc_ratio_min_m = re.search(r"[Mm]inimum absolute CCC move[^|]*\|\s*[^|]*?(\d+)\s*bps", s13)
    ccc_ratio_min   = int(ccc_ratio_min_m.group(1)) if ccc_ratio_min_m else 75

    return ThresholdBlock(
        hy_stress_delta        = bps(r"HY_STRESS_DELTA\s*\|\s*\+?(\d+)", s11),
        hy_recession_delta     = bps(r"HY_RECESSION_DELTA\s*\|\s*\+?(\d+)", s11),
        hy_velocity_delta      = bps(r"Velocity overlay\s*\|\s*\+?(\d+)", s11),
        hy_sustain_days        = days(r"Sustain period\s*\|\s*(\d+)", s11),
        ig_transmission_delta  = bps(r"IG_TRANSMISSION_DELTA\s*\|\s*\+?(\d+)", s12),
        ig_velocity_delta      = bps(r"Velocity overlay\s*\|\s*\+?(\d+)", s12),
        ig_sustain_days        = days(r"Sustain period\s*\|\s*(\d+)", s12),
        ccc_ratio_multiplier   = ccc_ratio,
        ccc_absolute_floor_bps = bps(r"CCC \+(\d+) bps while", s13),
        ccc_composite_ceiling_bps = bps(r"composite \+<(\d+) bps", s13),
        ccc_ratio_min_bps      = ccc_ratio_min,
    )


def _parse_return_table(text: str) -> Dict[str, Dict[str, ReturnRange]]:
    """Parse §4.1 expected real annualized return table.

    Returns dict: role_id → { scenario → ReturnRange }.
    Conservative bound used for ALL EV computations (per §4.1 annotation).
    Rows with fewer than 7 columns (role + 6 scenarios) are skipped.
    """
    s41   = _between(text, "### 4.1", "### 4.2")
    table: Dict[str, Dict[str, ReturnRange]] = {}

    for row in _table_rows(s41):
        if len(row) < 7:
            continue
        role = row[0]
        if not role or role.lower() == "role":
            continue
        scenario_map: Dict[str, ReturnRange] = {}
        for scenario, cell in zip(_SCENARIOS, row[1:7]):
            parsed = _parse_cell(cell)
            if parsed is not None:
                scenario_map[scenario] = parsed
        if scenario_map:
            table[role] = scenario_map

    return table


def _parse_multipliers(text: str) -> MultiplierBlock:
    """Parse §4.2 IRA and §4.3 Roth scenario target multipliers."""
    s42 = _between(text, "### 4.2", "### 4.3")
    s43 = _between(text, "### 4.3", "### 4.4")

    def _mults(section: str) -> Dict[str, float]:
        result: Dict[str, float] = {}
        for row in _table_rows(section):
            if len(row) >= 2 and row[0] in _SCENARIOS:
                try:
                    result[row[0]] = float(row[1])
                except ValueError:
                    pass
        return result

    def _floor(section: str) -> float:
        """Extract floor multiplier from 'Floor: 1.3x' line; default 1.3 if absent."""
        m = re.search(r"Floor:\s*(\d+(?:\.\d+)?)x", section)
        return float(m.group(1)) if m else 1.3

    return MultiplierBlock(
        ira=_mults(s42),
        roth=_mults(s43),
        ira_floor=_floor(s42),
        roth_floor=_floor(s43),
    )


def _parse_floor_params(text: str) -> FloorParams:
    """Parse §4.4 structural floor and concentration parameters."""
    s44 = _between(text, "### 4.4", "## Section 5")
    rows = {r[0]: r[1] for r in _table_rows(s44) if len(r) >= 2}

    def _pct(key: str) -> float:
        """Extract fraction from cell like '40%' or '0.25'."""
        val = rows.get(key, "0")
        m_pct = re.search(r"(\d+(?:\.\d+)?)\s*%", val)
        if m_pct:
            return float(m_pct.group(1)) / 100
        m_flt = re.search(r"(\d+(?:\.\d+)?)", val)
        return float(m_flt.group(1)) if m_flt else 0.0

    return FloorParams(
        base_floor                  = _pct("Base floor"),
        min_floor_pct               = _pct("Minimum floor"),
        concentration_cap           = _pct("Concentration cap"),
        floor_loss_prob_threshold   = _pct("Floor nominal loss probability threshold"),
    )


def _parse_regime(text: str) -> RegimeBlock:
    """Parse §9 market regime thresholds (M14)."""
    s9  = _between(text, "## Section 9", "## Section 10")
    s91 = _between(s9, "### 9.1", "### 9.2")
    s92 = _between(s9, "### 9.2", "### 9.3")
    s93 = _between(s9, "### 9.3", "### 9.4")
    s94 = _between(s9, "### 9.4", "### 9.5")
    s95 = _between(s9, "### 9.5", "\n---")

    # §9.1 — divergence thresholds keyed by first column
    div_rows = {r[0]: r[1] for r in _table_rows(s91) if len(r) >= 2}

    def _energy(key: str) -> float:
        m = re.search(r"energy_90d >= \+?(\d+(?:\.\d+)?)%", div_rows.get(key, ""))
        return float(m.group(1)) if m else 0.0

    def _vix(key: str) -> float:
        m = re.search(r"VIX_change_90d_pts <= \+?(\d+(?:\.\d+)?)", div_rows.get(key, ""))
        return float(m.group(1)) if m else 0.0

    def _equity(key: str) -> float:
        m = re.search(r"broad_equity_30d >= \+?(\d+(?:\.\d+)?)%", div_rows.get(key, ""))
        return float(m.group(1)) if m else 0.0

    cf_high_energy = _energy("commodity_fear_divergence HIGH")
    cf_high_vix    = _vix("commodity_fear_divergence HIGH")
    cf_mod_energy  = _energy("commodity_fear_divergence MODERATE")
    cf_mod_vix     = _vix("commodity_fear_divergence MODERATE")
    eq_high        = _equity("equity_scenario_divergence HIGH")
    eq_mod         = _equity("equity_scenario_divergence MODERATE")

    # §9.2 — underweight review trigger
    uw_rows = {r[0]: r[1] for r in _table_rows(s92) if len(r) >= 2}
    uw_gap  = _s(r"(\d+(?:\.\d+)?)", uw_rows.get("underweight_gap_trigger", "5"), 5.0)
    appr_30 = _s(r"(\d+(?:\.\d+)?)", uw_rows.get("appreciation_trigger_30d", "5"), 5.0)

    # §9.3 — entry extension guard thresholds (role → % or None)
    guards: Dict[str, Optional[float]] = {}
    for row in _table_rows(s93):
        if len(row) >= 2:
            role = row[0]
            val  = row[1].strip()
            if val.upper() == "N/A" or not val:
                guards[role] = None
            else:
                m_pct = re.search(r"(\d+(?:\.\d+)?)\s*%", val)
                guards[role] = float(m_pct.group(1)) if m_pct else None

    # §9.4 — MOVE index boundary levels from the Level | Signal table
    # Row format:  "< 80" | "NORMAL"   "80–100" | "ELEVATED"  etc.
    move_elevated = 80.0
    move_stress   = 100.0
    move_crisis   = 130.0
    move_systemic = 160.0
    for row in _table_rows(s94):
        if len(row) < 2:
            continue
        level_str = row[0]
        signal    = row[1].upper()
        m_num = re.search(r"(\d+)", level_str)
        if not m_num:
            continue
        val = float(m_num.group(1))
        if "ELEVATED" in signal:
            move_elevated = val
        elif "STRESS" in signal:
            move_stress = val
        elif "CRISIS" in signal and "SYSTEMIC" not in signal:
            move_crisis = val
        elif "SYSTEMIC" in signal:
            move_systemic = val

    # §9.5 — role repricing divergence thresholds: role → underperformance_pp
    role_repricing: Dict[str, float] = {}
    for row in _table_rows(s95):
        if len(row) >= 2 and row[0] and row[0].lower() != "role":
            m = re.search(r"(\d+(?:\.\d+)?)", row[1])
            if m:
                role_repricing[row[0].strip()] = float(m.group(1))

    return RegimeBlock(
        commodity_fear_HIGH_energy_pct  = cf_high_energy,
        commodity_fear_HIGH_vix_change  = cf_high_vix,
        commodity_fear_MOD_energy_pct   = cf_mod_energy,
        commodity_fear_MOD_vix_change   = cf_mod_vix,
        equity_div_HIGH_pct             = eq_high,
        equity_div_MOD_pct              = eq_mod,
        underweight_gap_trigger_pp      = uw_gap,
        appreciation_trigger_30d_pct    = appr_30,
        entry_extension_thresholds      = guards,
        move_elevated                   = move_elevated,
        move_stress                     = move_stress,
        move_crisis                     = move_crisis,
        move_systemic                   = move_systemic,
        role_repricing_thresholds       = role_repricing,
    )


def _parse_role_registry(text: str) -> Dict[str, str]:
    """Parse §11.1 role registry. Returns role_id → binding_driver string."""
    s111 = _between(text, "### 11.1", "### 11.2")
    roles: Dict[str, str] = {}
    for row in _table_rows(s111):
        if len(row) >= 2 and row[0] and row[0].lower() != "role":
            roles[row[0]] = row[1]
    return roles


def _parse_instruments(text: str) -> Dict[str, InstrumentEntry]:
    """Parse §11.3 active instruments and §11.4 candidate instruments.

    Each instrument block starts with '#### TICKER' and contains:
      - Components: role_id (weight) + role_id (weight)
      - TAX PLACEMENT: RETIREMENT ACCOUNTS ONLY.  (if retirement-only)
    UNCLASSIFIED_* component entries are excluded from ComponentVector.
    """
    instruments: Dict[str, InstrumentEntry] = {}

    def _parse_block(section: str, is_candidate: bool) -> None:
        parts = re.split(r"(?m)^#### ", section)
        for part in parts:
            if not part.strip():
                continue
            lines  = part.splitlines()
            ticker = lines[0].strip()
            # Skip section header fragments (contain spaces) or empty / comment lines
            if not ticker or ticker.startswith("#") or " " in ticker:
                continue
            block = "\n".join(lines[1:])

            # Components line
            comp_m = re.search(r"^- Components:\s*(.+)$", block, re.MULTILINE)
            components: List[ComponentWeight] = []
            if comp_m:
                for cm in _COMP_RE.finditer(comp_m.group(1)):
                    role_id = cm.group(1)
                    weight  = float(cm.group(2))
                    if not role_id.startswith("UNCLASSIFIED"):
                        components.append(ComponentWeight(role_id=role_id, weight=weight))

            tax = "RETIREMENT_ONLY" if "RETIREMENT ACCOUNTS ONLY" in block else "ALL"
            passive = bool(re.search(r"passive_mandate_eligible:\s*true", block, re.IGNORECASE))
            instruments[ticker] = InstrumentEntry(
                ticker=ticker, components=components,
                tax_placement=tax, is_candidate=is_candidate,
                passive_mandate_eligible=passive,
            )

    s11  = _between(text, "## Section 11", "## Section 12")
    s113 = _between(s11, "### 11.3", "### 11.4")
    # §11.4 runs to end of section 11
    idx114 = s11.find("### 11.4")
    s114   = s11[idx114:] if idx114 != -1 else ""

    _parse_block(s113, is_candidate=False)
    _parse_block(s114, is_candidate=True)
    return instruments


def _parse_cascade(text: str) -> CascadeBlock:
    """Parse §12 systemic cascade warning thresholds."""
    # §12 runs from ## Section 12 to end of file
    idx12 = text.find("## Section 12")
    s12   = text[idx12:] if idx12 != -1 else ""

    s121 = _between(s12, "### 12.1", "### 12.2")
    s122 = _between(s12, "### 12.2", "### 12.3")
    s123 = _between(s12, "### 12.3", "### 12.4")
    s124 = _between(s12, "### 12.4", "### 12.5")
    s125 = _between(s12, "### 12.5", "### 12.6")

    # §12.1 — agriculture / fertilizer chain
    rows121 = {r[0]: r[1] for r in _table_rows(s121) if len(r) >= 2}
    farm_pct  = _s(r"\+?(\d+(?:\.\d+)?)\s*%", rows121.get("farm_filings_alert", "+50%"), 50.0)
    natgas_p  = _s(r"\$(\d+(?:\.\d+)?)", rows121.get("natgas_alert", "$6.00"), 6.0)
    fert_pct  = _s(r"\+?(\d+(?:\.\d+)?)\s*%", rows121.get("fertilizer_alert", "+50%"), 50.0)

    # §12.2 — CRE / regional bank chain
    rows122 = {r[0]: r[1] for r in _table_rows(s122) if len(r) >= 2}
    kre_pct   = _s(r"(\d+(?:\.\d+)?)\s*%", rows122.get("KRE_alert", "15%"), 15.0)
    sofr_bps  = _s(r"\+(\d+(?:\.\d+)?)\s*bp", rows122.get("SOFR_DFF_alert", "+10 bp"), 10.0)
    sofr_days = int(_s(r"(\d+)\s*days", rows122.get("SOFR_DFF_alert", "5 days"), 5.0))

    # §12.3 — private credit / margin chain (Mode | Parameter | Threshold | ...)
    rows123 = {r[1]: r[2] for r in _table_rows(s123) if len(r) >= 3}
    margin_pct  = _s(r"(\d+(?:\.\d+)?)\s*%", rows123.get("margin_MoM_decline", "5%"), 5.0)
    gate_count  = int(_s(r"(\d+)\+", rows123.get("gate_count_alert", "3+"), 3.0))

    # §12.4 — manufacturing / corporate stress chain
    rows124 = {r[0]: r[1] for r in _table_rows(s124) if len(r) >= 2}
    bkr_watch = int(_s(r"≥(\d+)/quarter",
                       rows124.get("bankruptcy_quarterly_WATCH", "≥220/quarter"), 220.0))
    bkr_fires = int(_s(r"≥(\d+)/quarter",
                       rows124.get("bankruptcy_quarterly_FIRES", "≥300/quarter"), 300.0))

    # §12.5 — sovereign stress / Scenario E watch
    rows125 = {r[0]: r[1] for r in _table_rows(s125) if len(r) >= 2}
    e_warn  = _s(r"(\d+(?:\.\d+)?)\s*bp", rows125.get("E_term_premium_warning", "100 bp"), 100.0)
    e_alert = _s(r"(\d+(?:\.\d+)?)\s*bp", rows125.get("E_term_premium_alert",   "150 bp"), 150.0)
    e_30y   = _s(r"(\d+(?:\.\d+)?)\s*%",  rows125.get("E_30Y_warning", "5.50%"), 5.5)

    return CascadeBlock(
        farm_filings_alert_pct      = farm_pct,
        natgas_alert_price          = natgas_p,
        fertilizer_alert_pct        = fert_pct,
        kre_vs_spx_alert_pct        = kre_pct,
        sofr_dff_alert_bps          = sofr_bps,
        sofr_dff_sustain_days       = sofr_days,
        margin_mom_decline_pct      = margin_pct,
        gate_count_alert            = gate_count,
        bankruptcy_watch_quarterly  = bkr_watch,
        bankruptcy_fires_quarterly  = bkr_fires,
        e_term_premium_warning_bps  = e_warn,
        e_term_premium_alert_bps    = e_alert,
        e_30y_warning_pct           = e_30y,
    )


# ── §13 M19 thesis-sustaining conditions ───────────────────────────────────────

_TICKER_BLOCK_START_RE = re.compile(r"(?m)^([A-Z]{2,6}):\s*\{\s*$")
_BLOCK_END_RE = re.compile(r"(?m)^\}\s*$")


def _extract_quoted_field(block: str, field_name: str) -> Optional[str]:
    """Extract a single quoted scalar field, e.g. 'primary_driver: "..."'.
    DOTALL + non-greedy so multi-line continuations inside the quotes are
    captured as one string and collapsed to single spaces."""
    m = re.search(rf'(?m)^\s*{field_name}:\s*"(.*?)"', block, re.DOTALL)
    if not m:
        return None
    return re.sub(r"\s+", " ", m.group(1)).strip()


def _extract_list_field(block: str, field_name: str) -> List[str]:
    """Extract a quoted-string list field, e.g. 'sustaining_conditions: [ "...", "..." ]'.
    Returns [] if the field is absent (e.g. degraded_signals, which most tickers omit)."""
    m = re.search(rf'(?m)^\s*{field_name}:\s*\[(.*?)\]', block, re.DOTALL)
    if not m:
        return []
    return [
        re.sub(r"\s+", " ", item.group(1)).strip()
        for item in re.finditer(r'"(.*?)"', m.group(1), re.DOTALL)
    ]


def _parse_thesis_conditions(text: str) -> Dict[str, "ThesisConditionEntry"]:
    """Parse §13 M19 thesis-sustaining condition entries.

    Each ticker block has the form:
        TICKER: {
          primary_driver: "..."
          sustaining_conditions: [ "...", "..." ]
          degraded_signals: [ "..." ]        # optional — most tickers omit
          failure_signals: [ "...", "..." ]
          data_dependencies: ["...", "..."]
          last_reviewed: "YYYY-MM-DD"
          notes: "..."
        }

    §13.1 candidate placeholders (prose only — "VNQ, VEA: §11.4 CANDIDATE only...")
    never match the ticker-block start pattern below, so they're skipped automatically;
    no explicit section-end boundary is needed before scanning to end of file.
    """
    idx13 = text.find("## Section 13")
    s13 = text[idx13:] if idx13 != -1 else ""

    entries: Dict[str, ThesisConditionEntry] = {}
    for start_m in _TICKER_BLOCK_START_RE.finditer(s13):
        ticker = start_m.group(1)
        end_m = _BLOCK_END_RE.search(s13, start_m.end())
        if end_m is None:
            continue  # malformed block — skip rather than guess at content
        block = s13[start_m.end():end_m.start()]

        entries[ticker] = ThesisConditionEntry(
            ticker=ticker,
            primary_driver=_extract_quoted_field(block, "primary_driver") or "",
            sustaining_conditions=_extract_list_field(block, "sustaining_conditions"),
            degraded_signals=_extract_list_field(block, "degraded_signals"),
            failure_signals=_extract_list_field(block, "failure_signals"),
            data_dependencies=_extract_list_field(block, "data_dependencies"),
            last_reviewed=_extract_quoted_field(block, "last_reviewed") or "",
            notes=_extract_quoted_field(block, "notes") or "",
        )
    return entries


# ── §3 Calibration Log (ENG-52, 2026-07-06) ────────────────────────────────────
# Deliberately NOT part of CalibrationState/parse_calibration_state() above —
# §3 is prose history read directly by Claude each session (M05), never
# consumed by advisor_run_computation(). This parser exists for hygiene/
# tooling (e.g. a future ENG-53 archival pass), not any live computation path.

_LOG_HEADER_RE = re.compile(r"^---\s*\n(.*?\n)---\s*\n", re.MULTILINE | re.DOTALL)


def parse_calibration_log(text: str) -> List[CalibrationLogEntry]:
    """Parse §3 entries that use the ENG-52 structured front-matter format.

    Each entry is a small Jekyll-style YAML front-matter block (entry_id/
    date/version/category, delimited by '---' lines — a convention §3 didn't
    use before, so no collision with anything pre-existing) followed by
    unchanged free-text rationale, running up to the next entry's front
    matter or the end of §3.

    Only entries from v1.46 onward were migrated to this format (see
    CalibrationLogEntry's docstring for why) — older entries use at least
    one other, inconsistent title-line convention and have no front matter,
    so they're silently absent from this parser's output, not mis-parsed.
    This is additive tooling; it does not replace reading §3 directly.
    """
    idx3 = text.find("## Section 3")
    if idx3 == -1:
        return []
    idx4 = text.find("## Section 4")
    s3 = text[idx3:idx4] if idx4 != -1 else text[idx3:]

    matches = list(_LOG_HEADER_RE.finditer(s3))
    entries: List[CalibrationLogEntry] = []

    for i, m in enumerate(matches):
        try:
            header = yaml.safe_load(m.group(1))
        except yaml.YAMLError:
            continue
        if not isinstance(header, dict) or "date" not in header or "version" not in header:
            continue

        narrative_end = matches[i + 1].start() if i + 1 < len(matches) else len(s3)
        narrative = s3[m.end():narrative_end].strip()

        entries.append(CalibrationLogEntry(
            entry_id  = str(header.get("entry_id", "")),
            date      = str(header["date"]),
            version   = str(header["version"]),
            category  = str(header.get("category", "")),
            narrative = narrative,
        ))
    return entries


# ── Top-level entry point ──────────────────────────────────────────────────────


def parse_calibration_state(text: str) -> CalibrationState:
    """Parse the full text of Calibration_State.md into a CalibrationState.

    Args:
        text: Raw markdown content of Calibration_State.md.

    Returns:
        Fully populated CalibrationState dataclass.

    Raises:
        ValueError: If the file cannot be parsed (e.g., truncated or corrupt).
    """
    version, last_updated = _parse_version_date(text)
    return CalibrationState(
        version      = version,
        last_updated = last_updated,
        thresholds   = _parse_thresholds(text),
        return_table = _parse_return_table(text),
        multipliers  = _parse_multipliers(text),
        floor_params = _parse_floor_params(text),
        regime       = _parse_regime(text),
        roles        = _parse_role_registry(text),
        instruments  = _parse_instruments(text),
        cascade      = _parse_cascade(text),
        thesis_conditions = _parse_thesis_conditions(text),
    )
