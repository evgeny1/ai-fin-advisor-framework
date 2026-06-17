#!/usr/bin/env python3
"""
validate_manifests.py — Schema validator for framework MODULE MANIFEST headers.

Enforces the canonical header schema shared by every M01-M19 module file and
FW_Types.md. Per the framework's own module-file-hygiene rule, no Changes/
Updated/Resolves comment lines belong in these files - git log is the
changelog. This script checks that rule plus the full manifest field schema.

Usage:
    python tools/validate_manifests.py            validate every target file
    python tools/validate_manifests.py M02 M11    validate only files whose
                                                   filename starts with one
                                                   of the given prefixes

Exit code 0 = every file conforms. Exit code 1 = at least one violation.

Also wired into the pytest suite: python/tests/test_framework/test_manifest_schema.py
imports validate_file() directly and asserts a clean report per file.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

FRAMEWORK_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_FIELDS = [
    "ID",
    "Version",
    "Sub-project",
    "Reason to change",
    "Inputs consumed",
    "Outputs produced",
    "Calibration deps",
    "Types consumed",
]
OPTIONAL_TRAILING_FIELDS = ["Cross-module"]
ALL_ALLOWED_FIELDS = REQUIRED_FIELDS + OPTIONAL_TRAILING_FIELDS

ALLOWED_SUBPROJECT_TOKENS = {
    "DATA_INTELLIGENCE",
    "ANALYSIS_ENGINE",
    "PORTFOLIO_ADVISOR",
    "FRAMEWORK_CORE",
    "ORCHESTRATION",
    "THESIS_MONITORING",
}

TITLE_RE = re.compile(r"^# (M\d{2}|FW_Types) — .+$")
VERSION_LINE_RE = re.compile(r"^<!-- Version: (.+?) \| Updated: see git log -->$")
MANIFEST_OPEN = "<!-- MODULE MANIFEST"
MANIFEST_CLOSE = "-->"
FIELD_LINE_RE = re.compile(r"^  (\S[^:]*?):\s?(.*)$")


@dataclass
class FileReport:
    path: Path
    violations: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.violations


def find_target_files() -> list:
    files = sorted(FRAMEWORK_ROOT.glob("M[0-1][0-9]_*.md"))
    fw_types = FRAMEWORK_ROOT / "FW_Types.md"
    if fw_types.exists():
        files.append(fw_types)
    return files


def parse_manifest_block(lines, start_idx):
    """Parse fields out of a MODULE MANIFEST block.

    start_idx points at the '<!-- MODULE MANIFEST' line. Returns
    (fields_dict, field_order, end_idx, errors).
    """
    fields = {}
    order = []
    errors = []
    i = start_idx + 1
    current_label = None
    while i < len(lines):
        line = lines[i]
        if line.strip() == MANIFEST_CLOSE:
            return fields, order, i, errors
        m = FIELD_LINE_RE.match(line)
        if m:
            label, value = m.group(1), m.group(2)
            if label not in ALL_ALLOWED_FIELDS:
                errors.append(f"unrecognized manifest field '{label}:' — not part of the schema")
            if label in fields:
                errors.append(f"duplicate manifest field '{label}:'")
            fields[label] = value.strip()
            order.append(label)
            current_label = label
        else:
            if current_label is None:
                errors.append(f"unparseable manifest line: {line!r}")
            else:
                fields[current_label] += " " + line.strip()
        i += 1
    errors.append("MODULE MANIFEST block never closed with '-->'")
    return fields, order, i, errors


def validate_file(path: Path) -> FileReport:
    report = FileReport(path=path)
    lines = path.read_text(encoding="utf-8").splitlines()

    if not lines or not TITLE_RE.match(lines[0]):
        report.violations.append(
            "line 1 must match '# M{NN} — Title' or '# FW_Types — Title'"
        )
        return report

    version_title = None
    if len(lines) < 2 or not VERSION_LINE_RE.match(lines[1]):
        report.violations.append(
            "line 2 must be exactly '<!-- Version: X.Y | Updated: see git log -->' "
            "— found a stray 'Adopted:' date, an explicit 'Updated: <date>', "
            "or a leftover changelog comment instead"
        )
    else:
        version_title = VERSION_LINE_RE.match(lines[1]).group(1)

    manifest_idx = None
    for i in range(2, len(lines)):
        stripped = lines[i].strip()
        if stripped == "":
            continue
        if stripped == MANIFEST_OPEN.strip():
            manifest_idx = i
            break
        report.violations.append(
            f"line {i + 1}: stray content between the version line and MODULE "
            f"MANIFEST (fold into the Cross-module field or remove — git log is "
            f"the changelog): {lines[i]!r}"
        )
    if manifest_idx is None:
        report.violations.append("no '<!-- MODULE MANIFEST' block found")
        return report

    fields, order, _end_idx, errors = parse_manifest_block(lines, manifest_idx)
    report.violations.extend(errors)

    required_seen = [f for f in order if f in REQUIRED_FIELDS]
    if required_seen != REQUIRED_FIELDS:
        report.violations.append(
            f"required fields missing or out of order — found {required_seen}, "
            f"expected {REQUIRED_FIELDS}"
        )
    if order and order[-1] not in REQUIRED_FIELDS and order[-1] not in OPTIONAL_TRAILING_FIELDS:
        report.violations.append(f"unexpected trailing field '{order[-1]}'")

    expected_id = path.stem
    if "ID" in fields and fields["ID"] != expected_id:
        report.violations.append(
            f"ID field is '{fields['ID']}', expected '{expected_id}' (filename stem)"
        )
    if version_title is not None and "Version" in fields and fields["Version"] != version_title:
        report.violations.append(
            f"Version mismatch: title line says '{version_title}', "
            f"manifest says '{fields['Version']}'"
        )
    if "Types consumed" in fields:
        tc = fields["Types consumed"]
        if not (tc.lower().startswith("none") or tc.startswith("@see FW_Types.md")):
            report.violations.append(
                f"Types consumed should start with '@see FW_Types.md —' or 'none', "
                f"got: {tc[:60]!r}"
            )
    if "Sub-project" in fields:
        tokens = re.findall(r"[A-Z][A-Z_]+", fields["Sub-project"])
        unknown = [t for t in tokens if t not in ALLOWED_SUBPROJECT_TOKENS]
        if unknown:
            report.violations.append(
                f"Sub-project contains unrecognized token(s): {unknown}"
            )

    return report


def main(argv) -> int:
    targets = find_target_files()
    if argv:
        targets = [t for t in targets if any(t.name.startswith(a) for a in argv)]

    reports = [validate_file(p) for p in targets]
    failed = [r for r in reports if not r.ok]

    for r in reports:
        status = "PASS" if r.ok else "FAIL"
        print(f"[{status}] {r.path.name}")
        for v in r.violations:
            print(f"    - {v}")

    print(f"\n{len(reports) - len(failed)}/{len(reports)} files conform to schema.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
