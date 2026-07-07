"""
tests/test_stage1/test_compaction.py — ENG-53 (supersedes ENG-5)

Tests for file_protocol._compact_session_log() and _quarter_label(): the
calendar-age based archival that replaced entry-count based retention.
Any §7 row or §8 entry older than _ARCHIVE_AGE_DAYS (90, client-confirmed
2026-07-06) moves to the archive file for ITS OWN quarter, not today's —
a single write-back spanning archived items from more than one quarter
can touch more than one Archive_[Year]Q[N].md file.
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
SEC8_HEADER = "## Section 8 - Session State Log\n\n"


def _make_log(row_dates, entry_dates):
    """entry_dates: list of YYYY-MM-DD strings. ENG-52 YAML format —
    each entry keeps its own leading '---' per build_session_log_entry()'s
    convention."""
    rows = [f"| {d} | 280 | 80 | 920 | test | t1 |" for d in row_dates]
    sec7 = SEC7_HEADER + TABLE_HDR + "\n".join(rows) + "\n\n"
    entries = "".join(
        f"---\nentry_id: {d}T10:00\ndate: '{d}'\nstatus: current\n"
        f"scenario_probabilities: {{A: 50, B: 50, C: 0, D: 0, E: 0, F: 0}}\n"
        f"primary_driver: test entry {i}\n\n"
        for i, d in enumerate(entry_dates)
    )
    return sec7 + SEC8_HEADER + entries


def _freeze_today(monkeypatch, year, month, day):
    """Monkeypatch datetime.date.today() as seen by file_protocol.py (ENG-46
    pattern). file_protocol.py does `import datetime` (the whole module),
    so patch datetime.date itself, not something inside the module's own
    namespace. monkeypatch reverts automatically after the test."""
    class _FrozenDate(datetime.date):
        @classmethod
        def today(cls):
            return cls(year, month, day)
    monkeypatch.setattr(datetime, "date", _FrozenDate)


@pytest.mark.parametrize("month,expected", [
    (1, "Q1"), (2, "Q1"), (3, "Q1"),
    (4, "Q2"), (5, "Q2"), (6, "Q2"),
    (7, "Q3"), (8, "Q3"), (9, "Q3"),
    (10, "Q4"), (11, "Q4"), (12, "Q4"),
])
def test_quarter_label_all_months(month, expected):
    d = datetime.date(2026, month, 15)
    assert _quarter_label(d) == f"2026{expected}"


# ── No archival needed ──────────────────────────────────────────────────────────

def test_all_recent_returns_unchanged(tmp_path, monkeypatch):
    _freeze_today(monkeypatch, 2026, 7, 6)
    log = _make_log(["2026-07-01", "2026-06-20"], ["2026-07-03", "2026-06-25"])
    compacted, archives = _compact_session_log(log, tmp_path)
    assert compacted == log
    assert archives == {}


def test_exactly_at_90_days_is_kept_not_archived(tmp_path, monkeypatch):
    """Boundary: an entry dated exactly 90 days before today is NOT
    'older than 90 days' -- strictly-less-than cutoff is what archives."""
    _freeze_today(monkeypatch, 2026, 7, 6)
    ninety_days_ago = (datetime.date(2026, 7, 6) - datetime.timedelta(days=90)).isoformat()
    log = _make_log([ninety_days_ago], [ninety_days_ago])
    compacted, archives = _compact_session_log(log, tmp_path)
    assert archives == {}
    assert ninety_days_ago in compacted


def test_91_days_old_is_archived(tmp_path, monkeypatch):
    _freeze_today(monkeypatch, 2026, 7, 6)
    old_date = (datetime.date(2026, 7, 6) - datetime.timedelta(days=91)).isoformat()
    log = _make_log([old_date], [old_date])
    compacted, archives = _compact_session_log(log, tmp_path)
    assert old_date not in compacted
    assert len(archives) == 1


def test_missing_headers_returns_unchanged(tmp_path):
    assert _compact_session_log("no sections here", tmp_path) == ("no sections here", {})


def test_unparseable_date_is_kept_not_archived(tmp_path, monkeypatch):
    """A row/entry whose date can't be parsed must be kept, never
    archived -- failing soft (same philosophy as ENG-52's parser) rather
    than risk silently discarding something with a malformed date."""
    _freeze_today(monkeypatch, 2026, 7, 6)
    log = (
        SEC7_HEADER + TABLE_HDR + "| not-a-date | 280 | 80 | 920 | test | t1 |\n\n"
        + SEC8_HEADER
        + "---\nentry_id: bad\ndate: not-a-date\nstatus: current\n"
        "scenario_probabilities: {A: 50, B: 50, C: 0, D: 0, E: 0, F: 0}\n"
        "primary_driver: malformed date\n"
    )
    compacted, archives = _compact_session_log(log, tmp_path)
    assert archives == {}
    assert "not-a-date" in compacted


# ── §7 rows only ─────────────────────────────────────────────────────────────────

def test_sec7_old_row_archived_to_own_quarter(tmp_path, monkeypatch):
    """Archive destination is the ROW'S OWN quarter (January -> Q1), not
    today's quarter (July -> Q3) -- the key ENG-53 behavior change from
    ENG-5, which always used today's quarter regardless of entry age."""
    _freeze_today(monkeypatch, 2026, 7, 6)
    log = _make_log(["2026-01-15", "2026-07-01"], ["2026-07-03"])
    compacted, archives = _compact_session_log(log, tmp_path)
    assert list(archives.keys()) == ["Archive_2026Q1.md"]
    assert "2026-01-15" not in compacted
    assert "2026-07-01" in compacted
    assert "2026-01-15" in archives["Archive_2026Q1.md"]


def test_sec7_only_leaves_sec8_untouched(tmp_path, monkeypatch):
    _freeze_today(monkeypatch, 2026, 7, 6)
    log = _make_log(["2026-01-15"], ["2026-07-03"])
    compacted, _ = _compact_session_log(log, tmp_path)
    assert compacted.count("entry_id:") == 1


# ── §8 entries only ──────────────────────────────────────────────────────────────

def test_sec8_old_entry_archived_keeps_recent(tmp_path, monkeypatch):
    _freeze_today(monkeypatch, 2026, 7, 6)
    log = _make_log([], ["2026-01-15", "2026-07-03"])
    compacted, archives = _compact_session_log(log, tmp_path)
    assert compacted.count("entry_id:") == 1
    assert "2026-07-03" in compacted
    assert "2026-01-15" in archives["Archive_2026Q1.md"]


def test_sec8_compaction_note_added(tmp_path, monkeypatch):
    _freeze_today(monkeypatch, 2026, 7, 6)
    log = _make_log([], ["2026-01-15", "2026-07-03"])
    compacted, _ = _compact_session_log(log, tmp_path)
    assert "COMPACTED" in compacted
    assert "ENG-53" in compacted


# ── Both §7 and §8, same quarter ──────────────────────────────────────────────────

def test_both_overflow_same_quarter_one_archive_file(tmp_path, monkeypatch):
    _freeze_today(monkeypatch, 2026, 7, 6)
    log = _make_log(["2026-01-10", "2026-07-01"], ["2026-02-20", "2026-07-03"])
    compacted, archives = _compact_session_log(log, tmp_path)
    assert list(archives.keys()) == ["Archive_2026Q1.md"]
    content = archives["Archive_2026Q1.md"]
    assert content.count("## Archived") == 2
    assert "2026-01-10" in content
    assert "2026-02-20" in content


# ── Cross-quarter distribution (the core new ENG-53 behavior) ────────────────────

def test_archived_items_spanning_two_quarters_touch_two_files(tmp_path, monkeypatch):
    _freeze_today(monkeypatch, 2026, 7, 6)
    log = _make_log(
        ["2025-10-05"],                       # -> Archive_2025Q4.md
        ["2026-01-20", "2026-07-03"],          # 01-20 -> Archive_2026Q1.md; 07-03 kept
    )
    compacted, archives = _compact_session_log(log, tmp_path)
    assert sorted(archives.keys()) == ["Archive_2025Q4.md", "Archive_2026Q1.md"]
    assert "2025-10-05" in archives["Archive_2025Q4.md"]
    assert "2026-01-20" in archives["Archive_2026Q1.md"]
    assert compacted.count("entry_id:") == 1


# ── Archive file creation vs append ───────────────────────────────────────────────

def test_creates_new_archive_file_when_absent(tmp_path, monkeypatch):
    _freeze_today(monkeypatch, 2026, 7, 6)
    log = _make_log(["2026-01-15"], [])
    assert not (tmp_path / "Archive_2026Q1.md").exists()
    _, archives = _compact_session_log(log, tmp_path)
    assert "Created:" in archives["Archive_2026Q1.md"]


def test_appends_to_existing_archive_same_quarter(tmp_path, monkeypatch):
    _freeze_today(monkeypatch, 2026, 7, 6)
    log1 = _make_log(["2026-01-10"], [])
    _, archives1 = _compact_session_log(log1, tmp_path)
    (tmp_path / "Archive_2026Q1.md").write_text(archives1["Archive_2026Q1.md"], encoding="utf-8")

    log2 = _make_log(["2026-02-10"], [])
    _, archives2 = _compact_session_log(log2, tmp_path)
    content = archives2["Archive_2026Q1.md"]
    assert "2026-01-10" in content
    assert "2026-02-10" in content


def test_repeated_sec8_archival_merges_not_duplicates(tmp_path, monkeypatch):
    """Regression: a second same-quarter compaction must merge into the
    existing §8 archive section, not create a second one (the original
    ENG-5 bug, still a valid risk under the new age-based trigger)."""
    _freeze_today(monkeypatch, 2026, 7, 6)
    log1 = _make_log([], ["2026-01-10"])
    _, archives1 = _compact_session_log(log1, tmp_path)
    (tmp_path / "Archive_2026Q1.md").write_text(archives1["Archive_2026Q1.md"], encoding="utf-8")

    log2 = _make_log([], ["2026-02-10"])
    _, archives2 = _compact_session_log(log2, tmp_path)
    content = archives2["Archive_2026Q1.md"]
    assert content.count("## Archived") == 1
    assert content.count("entry_id:") == 2
