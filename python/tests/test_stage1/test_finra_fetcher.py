"""
tests/test_stage1/test_finra_fetcher.py — ENG-54

Coverage for data/fetchers/finra_fetcher.py: the direct finra.org
margin-statistics.xlsx fetch that replaced the manually-maintained
ALLOCATION_SPREADSHEET_FINRA tab (which had no Pattern B fetcher — CHAIN_3
was unscoreable in live sessions until this).

No network: the workbook is built in-memory (openpyxl via pandas
ExcelWriter) to mirror the real file's verified structure (2026-07-26
probe: one sheet, header row, Year-Month + Debit Balances columns,
newest-first ordering, Jan 1997 → present).
"""
from __future__ import annotations

import io
from typing import List, Optional, Tuple

import pandas as pd
import pytest

from advisor.data.fetchers import finra_fetcher
from advisor.types import DataSource, FetchSpec, UpdateFrequency


def _spec() -> FetchSpec:
    return FetchSpec(
        id="FINRA_MARGIN_DEBT", source=DataSource.FINRA_WEB,
        description="test", update_frequency=UpdateFrequency.MONTHLY,
        acceptable_lag_days=55,
    )


def _xlsx_bytes(rows: List[Tuple[str, float]], preamble_rows: int = 0,
                debit_header: str = "Debit Balances in Customers' Securities Margin Accounts") -> bytes:
    """Build workbook bytes mirroring the real file: optional preamble,
    header row, then data rows NEWEST FIRST (like FINRA publishes)."""
    data = []
    for _ in range(preamble_rows):
        data.append(["some note", None, None, None])
    data.append(["Year-Month", debit_header,
                 "Free Credit Balances in Customers' Cash Accounts",
                 "Free Credit Balances in Customers' Securities Margin Accounts"])
    for month, debit in sorted(rows, key=lambda t: t[0], reverse=True):
        data.append([month, debit, 100.0, 100.0])
    buf = io.BytesIO()
    pd.DataFrame(data).to_excel(buf, index=False, header=False)
    return buf.getvalue()


class TestParseMarginXlsx:

    def test_basic_metrics(self):
        rows = finra_fetcher._parse_margin_xlsx(_xlsx_bytes([
            ("2026-04", 1000.0), ("2026-05", 1100.0), ("2026-06", 1200.0),
        ]))
        v = finra_fetcher._derive_margin_metrics(rows)
        assert v["current"] == 1200.0
        assert v["latest_month"] == "2026-06"
        assert v["mom_pct"] == pytest.approx(9.09, abs=0.01)
        assert v["n_months"] == 3

    def test_at_record_true_when_latest_is_max(self):
        rows = finra_fetcher._parse_margin_xlsx(_xlsx_bytes([
            ("2026-04", 900.0), ("2026-05", 950.0), ("2026-06", 1000.0),
        ]))
        v = finra_fetcher._derive_margin_metrics(rows)
        assert v["at_nominal_record"] is True
        assert v["record_month"] == "2026-06"

    def test_at_record_false_when_below_past_record(self):
        rows = finra_fetcher._parse_margin_xlsx(_xlsx_bytes([
            ("2026-04", 1200.0), ("2026-05", 1100.0), ("2026-06", 1000.0),
        ]))
        v = finra_fetcher._derive_margin_metrics(rows)
        assert v["at_nominal_record"] is False
        assert v["record_value"] == 1200.0
        assert v["record_month"] == "2026-04"

    def test_mom_decline_is_negative(self):
        rows = finra_fetcher._parse_margin_xlsx(_xlsx_bytes([
            ("2026-05", 1000.0), ("2026-06", 940.0),
        ]))
        v = finra_fetcher._derive_margin_metrics(rows)
        assert v["mom_pct"] == pytest.approx(-6.0, abs=0.01)

    def test_yoy_present_with_13_months_absent_below(self):
        months_13 = [(f"2025-{m:02d}", 1000.0 + m) for m in range(6, 13)] + \
                    [(f"2026-{m:02d}", 1100.0 + m) for m in range(1, 7)]
        assert len(months_13) == 13
        v13 = finra_fetcher._derive_margin_metrics(
            finra_fetcher._parse_margin_xlsx(_xlsx_bytes(months_13)))
        assert v13["yoy_pct"] is not None
        v2 = finra_fetcher._derive_margin_metrics(
            finra_fetcher._parse_margin_xlsx(_xlsx_bytes([
                ("2026-05", 1000.0), ("2026-06", 1050.0)])))
        assert v2["yoy_pct"] is None

    def test_header_detected_past_preamble_rows(self):
        rows = finra_fetcher._parse_margin_xlsx(_xlsx_bytes([
            ("2026-05", 1000.0), ("2026-06", 1050.0)], preamble_rows=2))
        assert rows[-1] == ("2026-06", 1050.0)

    def test_missing_debit_column_raises_loudly(self):
        """Column renamed/absent must be a loud parse error, never a silent
        wrong-column read — same degrade-never-lie posture as ENG-69."""
        with pytest.raises(ValueError, match="Debit Balances"):
            finra_fetcher._parse_margin_xlsx(_xlsx_bytes(
                [("2026-06", 1000.0)], debit_header="Renamed Column"))

    def test_chronological_output_from_newest_first_input(self):
        rows = finra_fetcher._parse_margin_xlsx(_xlsx_bytes([
            ("2026-06", 3.0), ("2026-04", 1.0), ("2026-05", 2.0)]))
        assert [m for m, _ in rows] == ["2026-04", "2026-05", "2026-06"]


class TestFetchMarginDebt:

    def test_http_failure_degrades_to_invalid_reading(self, monkeypatch):
        import requests

        def _boom(*a, **kw):
            raise requests.ConnectionError("simulated network failure")
        monkeypatch.setattr(finra_fetcher, "MARGIN_STATS_XLSX_URL",
                            finra_fetcher.MARGIN_STATS_XLSX_URL)
        monkeypatch.setattr("requests.get", _boom)

        out = finra_fetcher.fetch_margin_debt(_spec())
        assert len(out) == 1
        assert out[0].is_valid is False
        assert any(f.startswith("FETCH_FAILED") for f in out[0].quality_flags)

    def test_success_carries_chain3_contract_keys_and_clean_flags(self, monkeypatch):
        """Value dict must carry cascade.py CHAIN_3's exact key contract
        (current / mom_pct / at_nominal_record), must NOT fabricate
        gate_count_90d (qualitative, different source), and a successful
        reading keeps quality_flags empty (CLI retry loop keys off flags)."""
        class _Resp:
            content = _xlsx_bytes([("2026-05", 1000.0), ("2026-06", 1100.0)])
            def raise_for_status(self): pass
        monkeypatch.setattr("requests.get", lambda *a, **kw: _Resp())

        out = finra_fetcher.fetch_margin_debt(_spec())
        r = out[0]
        assert r.is_valid is True
        assert r.quality_flags == []
        assert r.source == DataSource.FINRA_WEB
        for key in ("current", "mom_pct", "at_nominal_record"):
            assert key in r.value
        assert "gate_count_90d" not in r.value

    def test_registry_spec_repointed_to_finra_web(self):
        """ENG-54: the M18 spec must be FINRA_WEB (not the orphaned
        ALLOCATION_SPREADSHEET_FINRA tab) with the publication-cadence-aware
        lag (third-week-following-month release => 55 days)."""
        from advisor.data.m18_registry import _ALL_SPECS

        spec = next(s for s in _ALL_SPECS if s.id == "FINRA_MARGIN_DEBT")
        assert spec.source == DataSource.FINRA_WEB
        assert spec.acceptable_lag_days == 55
        assert spec.update_frequency == UpdateFrequency.MONTHLY
