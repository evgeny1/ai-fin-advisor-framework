"""Exceptions matching the HARD_STOP / guard semantics of the pseudo-code framework."""
from __future__ import annotations


class HardStopException(Exception):
    """Fatal session error — session cannot continue. Maps to HARD_STOP in pseudo-code."""
    def __init__(self, message: str, stage: str = "") -> None:
        super().__init__(message)
        self.stage = stage


class DataFetchException(Exception):
    """Data fetch failed with no available fallback."""
    pass


class PriceDataIntegrityViolation(Exception):
    """Price data sourced from unapproved channel (M18 HARD_GATE NoWebSearchForPriceData)."""
    pass


class AllocationPriceCrossCheckFailure(Exception):
    """
    Price discrepancy > 5% between yfinance and allocation sheet.
    Maps to M18.AllocationPriceCrossCheck HALT condition.
    """
    def __init__(self, symbol: str, yf_price: float, alloc_price: float) -> None:
        pct = abs(yf_price - alloc_price) / alloc_price * 100
        super().__init__(
            f"PRICE_CROSSCHECK_FAILURE: {symbol} "
            f"yfinance=${yf_price:.4f} vs allocation=${alloc_price:.4f} "
            f"(discrepancy: {pct:.1f}%) — HALT. Verify before proceeding."
        )
        self.symbol       = symbol
        self.yf_price     = yf_price
        self.alloc_price  = alloc_price
        self.discrepancy  = pct


class ClassificationValidationError(HardStopException):
    """Raised by ValidateClassifications() — instrument absent from §11."""
    pass


class WriteBackGuardViolation(HardStopException):
    """Attempted write-back in READONLY_MOBILE session or with invalid probabilities."""
    pass
