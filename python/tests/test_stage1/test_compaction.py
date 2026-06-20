"""
tests/test_stage1/test_compaction.py \u2014 ENG-5

Tests for file_protocol._compact_session_log() and _quarter_label(): the
\u00a77 (last-10-rows) / \u00a78 (last-3-entries) retention enforcement that now
runs automatically on every write_back() call, decoupled from the quarterly
Q-end audit cadence M12_DriveProtocol.md previously gated it to.
"""
from __future__ import annotations

import datetime

import pytest

from advisor.data.file_protocol import _compact_session_log, _quarter_label


SEC7_HEADER = "## Section 7 - Session Observations Log (Credit Readings)\n\n"
TABLE_HDR = (
    "| Date | HY OAS (bps) | IG OAS (bps) | CCC OAS (bps) | Source | T1 Flag |\n"
    "| --- | --- | --- | --- | --- | --- |\n"
)
SEP = "\n\n---\n\n"
SEC8_HEADER = "## Section 8 - Session State Log"


def _make_log(row_dates, entry_dates):
    rows = [f"| {d} | 280 | 80 | 920 | test | t1 |" for d in row_dates]
    sec7 = SEC7_HEADER + TABLE_HDR + "\n".join(rows) + "\n\n"
    entries = [
        f"date: {d} (test)\nscenario_probabilities: {{ A: 50%, B: 50% }}"
        for d in entry_dates
    ]
    sec8 = SEC8_HEADER + SEP + SEP.join(entries)
    return sec7 + sec8


@pytest.mark.parametrize("month,expected", [
    (1, "Q1"), (2, "Q1"), (3, "Q1"),
    (4, "Q2"), (5, "Q2"), (6, "Q2"),
    (7, "Q3"), (8, "Q3"), (9, "Q3"),
    (10, "Q4"), (11, "Q4"), (12, "Q4"),
])
def test_quarter_label_all_months(month, expected):
    d = datetime.date(2026, month, 15)
    assert _quarter_label(d) == f"2026{expected}"


# ── _compact_session_log: no-overflow case ──────────────────────────────────────────

def test_no_overflow_returns_unchanged(tmp_path):
    log = _make_log(
        [f"2026-01-{d:02d}" for d in [1, 5, 10]],
        [f"2026-01-{d:02d}" for d in [1, 5]],
    )
    compacted, archive_fn, archive_content = _compact_session_log(log, tmp_path)
    assert compacted == log
    assert archive_fn is None
    assert archive_content is None


def test_exactly_at_limit_does_not_archive(tmp_path):
    """Exactly 10 rows / 3 entries -- at the limit, not over it."""
    log = _make_log(
        [f"2026-01-{d:02d}" for d in range(1, 11)],
        [f"2026-01-{d:02d}" for d in [1, 5, 10]],
    )
    compacted, archive_fn, archive_content = _compact_session_log(log, tmp_path)
    assert archive_fn is None


# ── §7 overflow only ─────────────────────────────────────────────────────────────────

def test_sec7_overflow_archives_oldest(tmp_path):
    rows = [f"2026-01-{d:02d}" for d in range(1, 14)]  # 13 rows
    log = _make_log(rows, [f"2026-01-{d:02d}" for d in [1, 5]])
    compacted, archive_fn, archive_content = _compact_session_log(log, tmp_path)
    assert archive_fn == "Archive_2026Q2.md"
    assert compacted.count("| 2026-") == 10
    assert archive_content.count("| 2026-") == 3
    # the 3 oldest (01-01, 02, 03) must be the ones archived
    assert "2026-01-01" in archive_content
    assert "2026-01-03" in archive_content
    assert "2026-01-04" not in archive_content


def test_sec7_overflow_keeps_newest_rows(tmp_path):
    rows = [f"2026-01-{d:02d}" for d in range(1, 14)]
    log = _make_log(rows, [f"2026-02-{d:02d}" for d in [1, 5]])
    compacted, _, _ = _compact_session_log(log, tmp_path)
    sec7_section = compacted[:compacted.find("## Section 8")]
    assert "2026-01-13" in sec7_section
    assert "2026-01-04" in sec7_section
    assert "2026-01-01" not in sec7_section


def test_sec7_only_overflow_leaves_sec8_untouched(tmp_path):
    rows = [f"2026-01-{d:02d}" for d in range(1, 14)]
    entries = [f"2026-01-{d:02d}" for d in [1, 5]]
    log = _make_log(rows, entries)
    compacted, _, _ = _compact_session_log(log, tmp_path)
    sec8_idx = compacted.find("## Section 8")
    assert compacted[sec8_idx:].count("date: 2026") == 2


# ── §8 overflow only ─────────────────────────────────────────────────────────────────

def test_sec8_overflow_archives_oldest(tmp_path):
    entries = [f"2026-01-{d:02d}" for d in [1, 5, 10, 15]]
    log = _make_log([f"2026-01-{d:02d}" for d in [1, 5]], entries)
    compacted, archive_fn, archive_content = _compact_session_log(log, tmp_path)
    assert archive_fn == "Archive_2026Q2.md"
    sec8_idx = compacted.find("## Section 8")
    assert compacted[sec8_idx:].count("date: 2026") == 3
    assert archive_content.count("date: 2026") == 1
    assert "2026-01-01" in archive_content


def test_sec8_overflow_keeps_newest_entries(tmp_path):
    entries = [f"2026-01-{d:02d}" for d in [1, 5, 10, 15]]
    log = _make_log([f"2026-01-{d:02d}" for d in [1, 5]], entries)
    compacted, _, _ = _compact_session_log(log, tmp_path)
    assert "2026-01-15" in compacted
    assert "2026-01-10" in compacted


def test_sec8_compaction_note_added(tmp_path):
    entries = [f"2026-01-{d:02d}" for d in [1, 5, 10, 15]]
    log = _make_log([f"2026-01-{d:02d}" for d in [1, 5]], entries)
    compacted, _, _ = _compact_session_log(log, tmp_path)
    assert "COMPACTED" in compacted


# ── both §7 and §8 overflow together ───────────────────────────────────────────────

def test_both_overflow_simultaneously(tmp_path):
    rows = [f"2026-01-{d:02d}" for d in range(1, 14)]
    entries = [f"2026-01-{d:02d}" for d in [1, 5, 10, 15]]
    log = _make_log(rows, entries)
    compacted, archive_fn, archive_content = _compact_session_log(log, tmp_path)
    assert compacted.count("| 2026-") == 10
    sec8_idx = compacted.find("## Section 8")
    assert compacted[sec8_idx:].count("date: 2026") == 3
    assert archive_content.count("## Archived") == 2


# ── archive file creation vs append ───────────────────────────────────────────────────────────

def test_creates_new_archive_file_when_absent(tmp_path):
    rows = [f"2026-01-{d:02d}" for d in range(1, 14)]
    log = _make_log(rows, [f"2026-01-{d:02d}" for d in [1, 5]])
    assert not (tmp_path / "Archive_2026Q2.md").exists()
    _, archive_fn, archive_content = _compact_session_log(log, tmp_path)
    assert "Created:" in archive_content


def test_appends_to_existing_archive_same_quarter(tmp_path):
    rows1 = [f"2026-01-{d:02d}" for d in range(1, 14)]
    log1 = _make_log(rows1, [f"2026-01-{d:02d}" for d in [1, 5]])
    _, fn1, content1 = _compact_session_log(log1, tmp_path)
    (tmp_path / fn1).write_text(content1, encoding="utf-8")

    rows2 = [f"2026-02-{d:02d}" for d in range(1, 14)]
    log2 = _make_log(rows2, [f"2026-02-{d:02d}" for d in [1, 5]])
    _, fn2, content2 = _compact_session_log(log2, tmp_path)
    assert fn2 == fn1
    assert content2.count("| 2026-") == 6  # 3 from round1 + 3 from round2


def test_repeated_sec8_archival_merges_not_duplicates(tmp_path):
    """Regression: second same-quarter compaction must merge into the
    existing §8 archive section, not create a second one (the original
    bug found during ENG-5 implementation testing)."""
    rows1 = [f"2026-01-{d:02d}" for d in range(1, 14)]
    entries1 = [f"2026-01-{d:02d}" for d in [1, 5, 10, 15]]
    log1 = _make_log(rows1, entries1)
    _, fn1, content1 = _compact_session_log(log1, tmp_path)
    (tmp_path / fn1).write_text(content1, encoding="utf-8")

    rows2 = [f"2026-02-{d:02d}" for d in range(1, 3)]
    entries2 = [f"2026-02-{d:02d}" for d in [1, 5, 10, 15]]
    log2 = _make_log(rows2, entries2)
    _, fn2, content2 = _compact_session_log(log2, tmp_path)
    assert content2.count("## Archived") == 2
    assert content2.count("date: 2026") == 2  # 1 from round1 + 1 from round2
