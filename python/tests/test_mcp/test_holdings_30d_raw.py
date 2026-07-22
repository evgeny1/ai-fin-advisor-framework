"""
tests/test_mcp/test_holdings_30d_raw.py — ENG-70

_fetch_holdings_30d_raw() (mcp_server.py) had ZERO test coverage before
this session's fix. Two bugs were found live, same session, same function:

1. It computed the "30d return" as series.iloc[-1] / series.iloc[0] - 1 --
   the FIRST day of the whole ~35-trading-day fetch window, not ~22
   trading days back like every other 30d-return fetcher in this codebase
   (fetch_nasdaq_trailing, fetch_broad_equity_trailing both use
   n = min(22, len(closes)) and index closes[-n]). Confirmed live via
   market_data_mcp: SGOL's reported -8.92% was an exact match for its full
   2026-06-02->07-21 window return; the ~30-calendar-day figure
   (2026-06-22->07-21) is -2.46%.

2. It bypassed _yf_lock_guard() entirely (on the theory that fetch_all()
   finishing means yfinance is fully quiet by then), unlike every other
   yfinance call site in this codebase.

These tests cover both: the corrected 22-trading-day baseline, and that
the function now actually uses the shared lock.
"""
from __future__ import annotations

from unittest.mock import patch

import pandas as pd
import pytest


def _mock_multi_download(ticker_closes: dict) -> pd.DataFrame:
    """Realistic (Price, Ticker) MultiIndex mock -- same shape real
    yf.download() returns for a multi-ticker batch (group_by='column')."""
    n = len(next(iter(ticker_closes.values())))
    index = pd.date_range("2026-06-02", periods=n, freq="B")
    data = {("Close", t): c for t, c in ticker_closes.items()}
    df = pd.DataFrame(data, index=index)
    df.columns = pd.MultiIndex.from_tuples(df.columns, names=["Price", "Ticker"])
    return df


class TestHoldings30dBaselineWindow:

    def test_uses_22_trading_day_baseline_not_full_window(self):
        """The core ENG-70 regression: a ticker whose price was
        materially HIGHER at the start of the ~34-day fetch window than
        22 trading days ago must report the ~22-day figure, not the
        whole-window figure."""
        from advisor.mcp_server import _fetch_holdings_30d_raw

        # 34 closes total. First 12 days (the "extra" window beyond 22
        # trading days back) trend down from 120 -> 100; the last 22 days
        # are flat-ish at 100 -> 98 (a real ~-2% move). The old "use
        # iloc[0]" bug would report ~-18% (98 vs 120); the fix reports
        # the ~22-day figure instead.
        closes = [120.0, 118.0, 116.0, 114.0, 112.0, 110.0,
                  108.0, 106.0, 104.0, 102.0, 101.0, 100.0] + [100.0] * 21 + [98.0]
        assert len(closes) == 34
        df = _mock_multi_download({"SGOL": closes})

        with patch("yfinance.download", return_value=df):
            result = _fetch_holdings_30d_raw(["SGOL"])

        expected = closes[-1] / closes[-22] - 1  # correct ~22-trading-day return
        assert result["SGOL"] == pytest.approx(expected)
        # The bug's signature: this must NOT match the full-window return.
        wrong = closes[-1] / closes[0] - 1
        assert result["SGOL"] != pytest.approx(wrong)

    def test_matches_verified_sgol_figures_2026_07_22(self):
        """Direct regression test using SGOL's real 2026-06-02->07-21
        closes (verified via market_data_mcp the same session). The old
        bug (iloc[0] baseline) reproduces the exact live-reported -8.92%
        (38.91/42.72-1); the fix (n=22 trading days back, closes[-22]
        =40.16 on 2026-06-18) gives ~-3.11% instead -- much closer to the
        real ~30-calendar-day figure (-2.46%, using 2026-06-22 as
        baseline) than the buggy -8.92%, though not bit-for-bit identical
        to it, since trading-day count and calendar-day count don't land
        on exactly the same date. n=22 matches the convention already
        used by fetch_nasdaq_trailing/fetch_broad_equity_trailing
        elsewhere in this codebase, not a new one invented for this fix."""
        from advisor.mcp_server import _fetch_holdings_30d_raw

        sgol_closes = [
            42.72, 42.30, 42.66, 41.12, 41.21, 40.55, 38.88, 40.06, 40.10,
            41.15, 41.27, 40.32, 40.16, 39.89, 39.15, 37.96, 38.34, 38.77,
            38.24, 38.23, 38.45, 39.24, 39.65, 39.18, 38.85, 39.23, 39.12,
            38.10, 38.61, 38.63, 37.88, 38.22, 38.16, 38.91,
        ]
        assert len(sgol_closes) == 34
        df = _mock_multi_download({"SGOL": sgol_closes})

        with patch("yfinance.download", return_value=df):
            result = _fetch_holdings_30d_raw(["SGOL"])

        # Fixed behavior: closes[-1] / closes[-22] - 1
        assert result["SGOL"] == pytest.approx(38.91 / 40.16 - 1, abs=1e-6)
        assert result["SGOL"] == pytest.approx(-0.0311, abs=0.001)
        # The bug's exact live-reported figure must NOT reproduce anymore.
        buggy = 38.91 / 42.72 - 1
        assert buggy == pytest.approx(-0.0892, abs=0.001)  # confirms fixture realism
        assert result["SGOL"] != pytest.approx(buggy, abs=0.01)

    def test_short_history_uses_all_available_days(self):
        """Fewer than 22 trading days available -- n clamps to len(series),
        same convention as fetch_nasdaq_trailing / fetch_broad_equity_trailing."""
        from advisor.mcp_server import _fetch_holdings_30d_raw
        closes = [10.0, 11.0, 9.0, 9.5]
        df = _mock_multi_download({"XAR": closes})
        with patch("yfinance.download", return_value=df):
            result = _fetch_holdings_30d_raw(["XAR"])
        assert result["XAR"] == pytest.approx(closes[-1] / closes[0] - 1)

    def test_multiple_tickers_each_use_own_22day_baseline(self):
        """SGOL and SIVR real closes, same session -- confirms the fix
        applies per-ticker and reproduces both live-reported bug figures
        when checked against the OLD (iloc[0]) formula."""
        from advisor.mcp_server import _fetch_holdings_30d_raw
        sgol = [
            42.72, 42.30, 42.66, 41.12, 41.21, 40.55, 38.88, 40.06, 40.10,
            41.15, 41.27, 40.32, 40.16, 39.89, 39.15, 37.96, 38.34, 38.77,
            38.24, 38.23, 38.45, 39.24, 39.65, 39.18, 38.85, 39.23, 39.12,
            38.10, 38.61, 38.63, 37.88, 38.22, 38.16, 38.91,
        ]
        sivr = [
            71.44, 69.57, 70.38, 64.68, 64.69, 61.98, 60.61, 63.93, 64.43,
            66.69, 66.60, 63.69, 62.55, 61.93, 58.58, 54.42, 55.01, 56.01,
            55.34, 56.22, 56.32, 57.82, 58.99, 57.27, 55.52, 56.90, 56.71,
            54.83, 55.89, 54.88, 52.92, 53.37, 53.59, 55.80,
        ]
        df = _mock_multi_download({"SGOL": sgol, "SIVR": sivr})
        with patch("yfinance.download", return_value=df):
            result = _fetch_holdings_30d_raw(["SGOL", "SIVR"])

        assert result["SGOL"] == pytest.approx(sgol[-1] / sgol[-22] - 1)
        assert result["SIVR"] == pytest.approx(sivr[-1] / sivr[-22] - 1)
        # Confirm fixture realism: old buggy formula matches both
        # exact live-reported figures from the 2026-07-22 session.
        assert (sgol[-1] / sgol[0] - 1) == pytest.approx(-0.0892, abs=0.001)
        assert (sivr[-1] / sivr[0] - 1) == pytest.approx(-0.2189, abs=0.001)

    def test_empty_history_returns_empty_dict(self):
        from advisor.mcp_server import _fetch_holdings_30d_raw
        with patch("yfinance.download", return_value=pd.DataFrame()):
            result = _fetch_holdings_30d_raw(["SGOL"])
        assert result == {}

    def test_ticker_absent_from_response_is_skipped_not_crashed(self):
        from advisor.mcp_server import _fetch_holdings_30d_raw
        df = _mock_multi_download({"SGOL": [40.0] * 30})
        with patch("yfinance.download", return_value=df):
            result = _fetch_holdings_30d_raw(["SGOL", "NOTREAL"])
        assert "SGOL" in result
        assert "NOTREAL" not in result


class TestHoldings30dUsesSharedLock:
    """ENG-70's second fix: this function used to bypass _yf_lock_guard()
    entirely. Confirm it now actually acquires the shared lock."""

    def test_propagates_timeout_when_lock_held_elsewhere(self, monkeypatch):
        """_yf_lock_guard()'s `timeout` default is bound at function
        definition time, so patching the _YF_LOCK_TIMEOUT_SECONDS module
        constant after the fact has no effect on it -- must swap the
        guard itself for one with a short explicit timeout, or this test
        would genuinely block for the real 20s default."""
        import advisor.data.fetchers.yfinance_fetcher as yff
        from advisor.mcp_server import _fetch_holdings_30d_raw

        original_guard = yff._yf_lock_guard
        monkeypatch.setattr(yff, "_yf_lock_guard", lambda: original_guard(timeout=0.2))

        yff._YF_LOCK.acquire()
        try:
            with pytest.raises(TimeoutError, match="lock busy"):
                _fetch_holdings_30d_raw(["SGOL"])
        finally:
            yff._YF_LOCK.release()

    def test_releases_lock_after_normal_completion(self):
        from advisor.data.fetchers.yfinance_fetcher import _YF_LOCK
        from advisor.mcp_server import _fetch_holdings_30d_raw

        df = _mock_multi_download({"SGOL": [40.0] * 30})
        with patch("yfinance.download", return_value=df):
            _fetch_holdings_30d_raw(["SGOL"])
        assert not _YF_LOCK.locked()
