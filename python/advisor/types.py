"""
FW_Types — Python translation of FW_Types.md (Framework Core shared contracts).
All modules consume and produce these types. No business logic here.
Stage 1 includes: DataSource, FetchSpec, DataReading, SessionType.
Stubs for Stage 3+ signal types included for import stability.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


# ── Enums ─────────────────────────────────────────────────────────────────────

class DataSource(Enum):
    FRED_SPREADSHEET_TAB          = "FRED_SPREADSHEET_TAB"
    ALLOCATION_SPREADSHEET_FINRA  = "ALLOCATION_SPREADSHEET_FINRA"
    ALLOCATION_SPREADSHEET_OTHER  = "ALLOCATION_SPREADSHEET_OTHER"
    YFINANCE                      = "YFINANCE"          # Python direct — was YFINANCE_MCP
    FMP_CHART                     = "FMP_CHART"
    FMP_ECONOMICS_TREASURY_RATES  = "FMP_ECONOMICS_TREASURY_RATES"
    FMP_COMMODITY                 = "FMP_COMMODITY"
    FMP_INDEXES                   = "FMP_INDEXES"
    GOOGLEFINANCE                 = "GOOGLEFINANCE"
    WEBSEARCH_T1                  = "WEBSEARCH_T1"
    WEBSEARCH_T2                  = "WEBSEARCH_T2"
    USDA_OR_AFBF                  = "USDA_OR_AFBF"
    FRED_OR_WEBSEARCH             = "FRED_OR_WEBSEARCH"
    MANUAL_CLIENT_INPUT           = "MANUAL_CLIENT_INPUT"


class UpdateFrequency(Enum):
    DAILY     = "DAILY"
    WEEKLY    = "WEEKLY"
    MONTHLY   = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    ON_DEMAND = "ON_DEMAND"   # fetch only when explicitly requested


class SessionType(Enum):
    FULL_DESKTOP    = "FULL_DESKTOP"     # Desktop Commander + git available
    READONLY_MOBILE = "READONLY_MOBILE"  # read + advisory only; no write-back


class SourceTier(Enum):
    T1 = "T1"
    T2 = "T2"
    T3 = "T3"


class Scenario(Enum):
    A = "A"; B = "B"; C = "C"; D = "D"; E = "E"; F = "F"


# ── Data Layer Types (Stage 1) ─────────────────────────────────────────────────

@dataclass
class FetchSpec:
    """Descriptor for one data series. Registered in m18_registry.py only."""
    id:                  str
    source:              DataSource
    description:         str
    update_frequency:    UpdateFrequency
    acceptable_lag_days: int
    consumer:            List[str] = field(default_factory=list)
    calibration_use:     Optional[str] = None


@dataclass
class DataReading:
    """Single fetched value produced by a fetcher and consumed by ANALYSIS_ENGINE."""
    spec_id:       str
    value:         Any              # float | dict | list — type depends on series
    source:        DataSource
    fetched_at:    datetime
    quality_flags: List[str] = field(default_factory=list)
    raw:           Optional[Any] = None   # original API response for debugging

    @property
    def is_valid(self) -> bool:
        return self.value is not None and not any(
            f.startswith(("FETCH_FAILED", "UNAVAILABLE")) for f in self.quality_flags
        )

    def flag(self, msg: str) -> "DataReading":
        self.quality_flags.append(msg)
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {
            "spec_id":       self.spec_id,
            "value":         self.value,
            "source":        self.source.value,
            "fetched_at":    self.fetched_at.isoformat(),
            "quality_flags": self.quality_flags,
        }


# ── Signal Types — stubs; fleshed out in Stage 3 ──────────────────────────────

@dataclass
class ScenarioProbabilities:
    A: float; B: float; C: float; D: float; E: float; F: float

    def __post_init__(self) -> None:
        total = self.A + self.B + self.C + self.D + self.E + self.F
        if abs(total - 100.0) > 0.01:
            raise ValueError(f"Probabilities must sum to 100.0, got {total:.4f}")

    def as_dict(self) -> Dict[str, float]:
        return {s.value: getattr(self, s.value) for s in Scenario}
