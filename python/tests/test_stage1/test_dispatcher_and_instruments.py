"""
Regression tests for two Stage 1 bugs found during shadow session 2026-06-10.

Bug 1 — Dispatcher overwrite:
    _build_registry() iterated over 7 spec_ids and called register_fetcher()
    with DataSource.YFINANCE each time. The registry uses DataSource as the dict key,
    so each iteration overwrote the previous. Only fetch_holdings_prices survived,
    meaning every YFINANCE spec produced N readings (one per instrument) instead of
    1 targeted reading — 138 readings total, all cross-polluted
    (e.g. MOVE:MLPX, KRE:SGOV, etc.).

Bug 2 — instruments.json wrong path:
    _SERVER_DIR used 5 .parent calls + "dev/market_data_mcp", landing at
    AI Financial Advisor Framework/dev/market_data_mcp (does not exist).
    The file lives at My Drive/dev/market_data_mcp (sibling of the framework dir).
    Fix: 6 .parent calls + "market_data_mcp".
    Side-effect of wrong path: load_instruments() fell back to _FALLBACK_INSTRUMENTS,
    which included PAVE (an exited position).
"""
from __future__ import annotations

import importlib
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from advisor.data.fetchers.yfinance_fetcher import yfinance_dispatcher
from advisor.types import DataReading, DataSource, FetchSpec, UpdateFrequency


# ── Helpers ───────────────────────────────────────────────────────────────────

def _spec(spec_id: str, source: DataSource = DataSource.YFINANCE) -> FetchSpec:
    return FetchSpec(
        id=spec_id, source=source,
        description="test", update_frequency=UpdateFrequency.DAILY,
        acceptable_lag_days=1,
    )


def _reading(spec_id: str) -> DataReading:
    return DataReading(
        spec_id=spec_id, value={"price": 1.0},
        source=DataSource.YFINANCE, fetched_at=datetime.utcnow(),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Bug 1 — Dispatcher routing
# ═══════════════════════════════════════════════════════════════════════════════

class TestDispatcherRouting:
    """
    Each spec.id must reach exactly the right underlying function.
    Before the fix, ALL YFINANCE specs reached fetch_holdings_prices.
    """

    def test_holdings_prices_routes_to_fetch_holdings_prices(self):
        spec = _spec("HOLDINGS_PRICES")
        with patch("advisor.data.fetchers.yfinance_fetcher.fetch_holdings_prices") as mock_fn:
            mock_fn.return_value = [_reading("HOLDINGS_PRICES:MLPX")]
            result = yfinance_dispatcher(spec)
        mock_fn.assert_called_once_with(spec)

    def test_vix_30d_routes_to_fetch_vix_history(self):
        spec = _spec("VIX_30D_AVG")
        with patch("advisor.data.fetchers.yfinance_fetcher.fetch_vix_history") as mock_fn:
            mock_fn.return_value = [_reading("VIX_30D_AVG")]
            result = yfinance_dispatcher(spec)
        mock_fn.assert_called_once_with(spec)

    def test_vix_90d_routes_to_fetch_vix_history(self):
        spec = _spec("VIX_90D_AVG")
        with patch("advisor.data.fetchers.yfinance_fetcher.fetch_vix_history") as mock_fn:
            mock_fn.return_value = [_reading("VIX_90D_AVG")]
            result = yfinance_dispatcher(spec)
        mock_fn.assert_called_once_with(spec)

    def test_broad_equity_routes_to_fetch_broad_equity_trailing(self):
        spec = _spec("BROAD_EQUITY_TRAILING")
        with patch("advisor.data.fetchers.yfinance_fetcher.fetch_broad_equity_trailing") as mock_fn:
            mock_fn.return_value = [_reading("BROAD_EQUITY_TRAILING")]
            result = yfinance_dispatcher(spec)
        mock_fn.assert_called_once_with(spec)

    def test_yield_curve_routes_to_fetch_yield_curve_partial(self):
        spec = _spec("YIELD_CURVE")
        with patch("advisor.data.fetchers.yfinance_fetcher.fetch_yield_curve_partial") as mock_fn:
            mock_fn.return_value = [_reading("YIELD_CURVE")]
            result = yfinance_dispatcher(spec)
        mock_fn.assert_called_once_with(spec)

    @pytest.mark.parametrize("spec_id", [
        "DXY", "MOVE", "VIX", "KRE", "KBE", "SP500",
        "BRENT_CRUDE", "WTI", "GOLD_SPOT", "SILVER",
        "NASDAQ_COMP", "DOW", "RUSSELL2000",
    ])
    def test_macro_and_commodity_specs_route_to_fetch_single(self, spec_id: str):
        """
        Every single-quote spec must route to _fetch_single, NOT fetch_holdings_prices.
        Before the fix, all of these reached fetch_holdings_prices and produced
        N instrument readings apiece (the cross-polluted fanout).
        """
        spec = _spec(spec_id)
        with patch("advisor.data.fetchers.yfinance_fetcher._fetch_single") as mock_single, \
             patch("advisor.data.fetchers.yfinance_fetcher.fetch_holdings_prices") as mock_holdings:
            mock_single.return_value = [_reading(spec_id)]
            result = yfinance_dispatcher(spec)

        mock_single.assert_called_once_with(spec)
        mock_holdings.assert_not_called()  # ← this would have failed before the fix

    def test_on_demand_spec_raises_value_error(self):
        """HISTORICAL_INSTRUMENT_PRICES is ON_DEMAND; dispatcher must reject it."""
        spec = _spec("HISTORICAL_INSTRUMENT_PRICES")
        with pytest.raises(ValueError, match="ON_DEMAND"):
            yfinance_dispatcher(spec)

    def test_unknown_spec_id_raises_value_error(self):
        """Unmapped spec.id must fail loudly so it is caught at development time."""
        spec = _spec("DOES_NOT_EXIST")
        with patch("advisor.data.fetchers.yfinance_fetcher._fetch_single") as mock_single:
            mock_single.side_effect = ValueError("No yfinance symbol for spec.id='DOES_NOT_EXIST'")
            with pytest.raises(ValueError, match="DOES_NOT_EXIST"):
                yfinance_dispatcher(spec)


class TestNoFanout:
    """
    Regression: a non-holdings YFINANCE spec must produce exactly 1 reading,
    not one per instrument in the portfolio.
    """

    def test_move_spec_produces_one_reading(self):
        spec = _spec("MOVE")
        with patch("advisor.data.fetchers.yfinance_fetcher._fetch_single") as mock_single, \
             patch("advisor.data.fetchers.yfinance_fetcher.fetch_holdings_prices") as mock_holdings:
            mock_single.return_value = [_reading("MOVE")]
            result = yfinance_dispatcher(spec)

        assert len(result) == 1, (
            f"Expected 1 reading for MOVE, got {len(result)}. "
            "Fanout: fetch_holdings_prices was called instead of _fetch_single."
        )
        assert result[0].spec_id == "MOVE"
        mock_holdings.assert_not_called()

    def test_brent_crude_produces_one_reading(self):
        spec = _spec("BRENT_CRUDE")
        with patch("advisor.data.fetchers.yfinance_fetcher._fetch_single") as mock_single:
            mock_single.return_value = [_reading("BRENT_CRUDE")]
            result = yfinance_dispatcher(spec)

        assert len(result) == 1
        assert result[0].spec_id == "BRENT_CRUDE"


class TestBuildRegistryDispatcherWiring:
    """
    Verify _build_registry() results in exactly one YFINANCE fetcher entry
    and that it is the dispatcher (not fetch_holdings_prices or a stale lambda).
    """

    def test_exactly_one_yfinance_fetcher_registered(self):
        """
        Before the fix: 8 register_fetcher calls all used DataSource.YFINANCE,
        each overwriting the previous. This test would have passed anyway (dict
        has one key), but it validates the single-registration intent.
        """
        from advisor.__main__ import _build_registry
        registry = _build_registry()
        assert DataSource.YFINANCE in registry._fetchers

    def test_registered_yfinance_fetcher_is_dispatcher(self):
        """The registered function must be yfinance_dispatcher, not fetch_holdings_prices."""
        from advisor.__main__ import _build_registry
        import advisor.data.fetchers.yfinance_fetcher as m
        registry = _build_registry()
        registered = registry._fetchers[DataSource.YFINANCE]
        assert registered is m.yfinance_dispatcher, (
            f"Expected yfinance_dispatcher, got {registered.__name__}. "
            "The overwrite bug would have left fetch_holdings_prices here."
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Bug 2 — instruments.json path
# ═══════════════════════════════════════════════════════════════════════════════

class TestInstrumentsJsonPath:
    """
    _MCP_DIR must resolve to dev/market_data_mcp (sibling of the framework folder),
    NOT to AI Financial Advisor Framework/dev/market_data_mcp (non-existent).
    """

    def test_mcp_dir_name_is_market_data_mcp(self):
        from advisor.data.fetchers.yfinance_fetcher import _MCP_DIR
        assert _MCP_DIR.name == "market_data_mcp", (
            f"Expected directory name 'market_data_mcp', got '{_MCP_DIR.name}'"
        )

    def test_mcp_dir_is_not_nested_inside_framework_repo(self):
        """
        Before the fix: 5 parents landed at AI Financial Advisor Framework/,
        then appended dev/market_data_mcp → nested inside the repo.
        After fix: 6 parents lands at dev/, then appends market_data_mcp → sibling.
        """
        from advisor.data.fetchers.yfinance_fetcher import _MCP_DIR
        framework_dir_name = "AI Financial Advisor Framework"
        ancestor_names = [p.name for p in _MCP_DIR.parents]
        assert framework_dir_name not in ancestor_names, (
            f"_MCP_DIR is nested inside '{framework_dir_name}' — 5-parent bug still present.\n"
            f"_MCP_DIR resolves to: {_MCP_DIR}\n"
            f"Ancestors: {ancestor_names}"
        )

    def test_mcp_dir_parent_matches_framework_dir_parent(self):
        """
        dev/market_data_mcp and AI Financial Advisor Framework/ must share the same parent (dev/).
        This confirms they are siblings.
        """
        from advisor.data.fetchers.yfinance_fetcher import _MCP_DIR
        import advisor  # package root
        framework_dir = Path(advisor.__file__).parent.parent.parent  # python/advisor → python/ → framework/
        # _MCP_DIR.parent == dev/;  framework_dir.parent == dev/
        assert _MCP_DIR.parent == framework_dir.parent, (
            f"_MCP_DIR.parent ({_MCP_DIR.parent}) != framework_dir.parent ({framework_dir.parent}). "
            f"They should share the same dev/ parent."
        )

    def test_instruments_file_path_ends_correctly(self):
        from advisor.data.fetchers.yfinance_fetcher import _INSTRUMENTS_FILE
        assert _INSTRUMENTS_FILE.name == "instruments.json"
        assert _INSTRUMENTS_FILE.parent.name == "market_data_mcp"

    def test_env_var_overrides_mcp_dir(self, tmp_path, monkeypatch):
        """ADVISOR_MCP_DIR must override the auto-computed path."""
        import advisor.data.fetchers.yfinance_fetcher as m
        monkeypatch.setenv("ADVISOR_MCP_DIR", str(tmp_path))
        importlib.reload(m)
        try:
            assert m._MCP_DIR == tmp_path, (
                f"Expected {tmp_path}, got {m._MCP_DIR}. "
                "ADVISOR_MCP_DIR env var is not overriding the computed path."
            )
        finally:
            monkeypatch.delenv("ADVISOR_MCP_DIR", raising=False)
            importlib.reload(m)  # restore to computed path


class TestLoadInstruments:
    """
    load_instruments() must return the live list from instruments.json
    and fall back gracefully (without PAVE) when the file is missing or corrupt.
    """

    def test_returns_contents_of_valid_json(self, tmp_path):
        expected = ["MLPX", "SGOV", "DBMF", "AIPO", "XAR"]
        instruments_file = tmp_path / "instruments.json"
        instruments_file.write_text(json.dumps({
            "instruments":  expected,
            "last_updated": "2026-06-10",
            "session":      "2026-06-10 advisory",
        }))
        import advisor.data.fetchers.yfinance_fetcher as m
        original = m._INSTRUMENTS_FILE
        m._INSTRUMENTS_FILE = instruments_file
        try:
            result = m.load_instruments()
            assert result == expected
        finally:
            m._INSTRUMENTS_FILE = original

    def test_fallback_when_file_missing(self, tmp_path):
        import advisor.data.fetchers.yfinance_fetcher as m
        original = m._INSTRUMENTS_FILE
        m._INSTRUMENTS_FILE = tmp_path / "nonexistent.json"
        try:
            result = m.load_instruments()
            assert len(result) > 0, "Fallback list must not be empty"
            assert "PAVE" not in result, (
                "PAVE is an exited position and must not appear in the fallback list. "
                "The stale fallback was a symptom of the wrong path resolving to no file."
            )
        finally:
            m._INSTRUMENTS_FILE = original

    def test_fallback_when_json_empty_instruments_list(self, tmp_path):
        """An instruments.json with an empty list should also trigger the fallback."""
        instruments_file = tmp_path / "instruments.json"
        instruments_file.write_text(json.dumps({"instruments": []}))
        import advisor.data.fetchers.yfinance_fetcher as m
        original = m._INSTRUMENTS_FILE
        m._INSTRUMENTS_FILE = instruments_file
        try:
            result = m.load_instruments()
            assert len(result) > 0, "Empty instruments list should trigger fallback"
        finally:
            m._INSTRUMENTS_FILE = original

    def test_fallback_when_json_malformed(self, tmp_path):
        """Corrupt JSON must not crash load_instruments — fallback silently."""
        instruments_file = tmp_path / "instruments.json"
        instruments_file.write_text("{ this is not valid json }")
        import advisor.data.fetchers.yfinance_fetcher as m
        original = m._INSTRUMENTS_FILE
        m._INSTRUMENTS_FILE = instruments_file
        try:
            result = m.load_instruments()
            assert len(result) > 0
        finally:
            m._INSTRUMENTS_FILE = original


class TestWriteInstrumentsJson:
    """
    write_instruments_json() (ENG-25) — the write half of the read/fallback
    pair above. Source of truth is the §11.3 active-instrument list Claude
    derives from THIS session's Calibration_State.md parse; this just
    confirms the function writes it correctly and round-trips with
    load_instruments().
    """

    def test_writes_expected_shape(self, tmp_path):
        import advisor.data.fetchers.yfinance_fetcher as m
        instruments_file = tmp_path / "instruments.json"
        original = m._INSTRUMENTS_FILE
        m._INSTRUMENTS_FILE = instruments_file
        try:
            tickers = ["MLPX", "SGOV", "AIPO"]
            returned_path = m.write_instruments_json(tickers)
            assert returned_path == instruments_file
            data = json.loads(instruments_file.read_text())
            assert data["instruments"] == tickers
            assert "last_updated" in data
            assert "session" in data
            assert data["session"].endswith("advisory")
        finally:
            m._INSTRUMENTS_FILE = original

    def test_creates_parent_directory_if_missing(self, tmp_path):
        import advisor.data.fetchers.yfinance_fetcher as m
        nested = tmp_path / "market_data_mcp_does_not_exist_yet"
        instruments_file = nested / "instruments.json"
        original_file = m._INSTRUMENTS_FILE
        original_dir = m._MCP_DIR
        m._INSTRUMENTS_FILE = instruments_file
        m._MCP_DIR = nested
        try:
            assert not nested.exists()
            m.write_instruments_json(["XAR"])
            assert instruments_file.exists()
        finally:
            m._INSTRUMENTS_FILE = original_file
            m._MCP_DIR = original_dir

    def test_overwrites_existing_content(self, tmp_path):
        import advisor.data.fetchers.yfinance_fetcher as m
        instruments_file = tmp_path / "instruments.json"
        instruments_file.write_text(json.dumps({
            "instruments": ["STALE_TICKER", "PAVE"],
            "last_updated": "2026-01-01",
            "session": "2026-01-01 advisory",
        }))
        original = m._INSTRUMENTS_FILE
        m._INSTRUMENTS_FILE = instruments_file
        try:
            m.write_instruments_json(["MLPX", "SGOV"])
            data = json.loads(instruments_file.read_text())
            assert data["instruments"] == ["MLPX", "SGOV"]
            assert "PAVE" not in data["instruments"]
        finally:
            m._INSTRUMENTS_FILE = original

    def test_round_trips_with_load_instruments(self, tmp_path):
        """write then load should return exactly what was written, not the fallback."""
        import advisor.data.fetchers.yfinance_fetcher as m
        instruments_file = tmp_path / "instruments.json"
        original = m._INSTRUMENTS_FILE
        m._INSTRUMENTS_FILE = instruments_file
        try:
            written = ["MLPX", "SGOV", "DBMF", "AIPO", "XAR", "SGOL", "SIVR", "VTIP", "XLP"]
            m.write_instruments_json(written)
            loaded = m.load_instruments()
            assert loaded == written
        finally:
            m._INSTRUMENTS_FILE = original

    def test_empty_list_does_not_silently_fall_back_on_next_load(self, tmp_path):
        """
        Writing an empty list is a legitimate (if unusual) caller decision —
        but load_instruments() treats an empty 'instruments' key as a signal
        to fall back (see TestLoadInstruments.test_fallback_when_json_empty_instruments_list
        above). Documenting that interaction here so a future change to either
        function doesn't silently break the contract between them.
        """
        import advisor.data.fetchers.yfinance_fetcher as m
        instruments_file = tmp_path / "instruments.json"
        original = m._INSTRUMENTS_FILE
        m._INSTRUMENTS_FILE = instruments_file
        try:
            m.write_instruments_json([])
            loaded = m.load_instruments()
            assert loaded == m._FALLBACK_INSTRUMENTS
        finally:
            m._INSTRUMENTS_FILE = original
