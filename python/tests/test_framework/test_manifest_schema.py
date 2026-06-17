"""
test_manifest_schema.py — pytest wrapper around tools/validate_manifests.py.

Asserts every M01-M19 module file and FW_Types.md conforms to the canonical
MODULE MANIFEST schema. Fails loudly (with the specific violation list) the
moment a module file's header drifts from the schema — this is the
equivalent of XSD validation for the framework's pseudo-code header format.
"""
import sys
from pathlib import Path

import pytest

_FRAMEWORK_ROOT = Path(__file__).resolve().parents[3]
_TOOLS_DIR = _FRAMEWORK_ROOT / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import validate_manifests as vm  # noqa: E402


def _target_files():
    files = vm.find_target_files()
    assert files, f"no module files found under {vm.FRAMEWORK_ROOT} — check the glob pattern"
    return files


@pytest.mark.parametrize("path", _target_files(), ids=lambda p: p.name)
def test_module_manifest_conforms_to_schema(path):
    report = vm.validate_file(path)
    assert report.ok, (
        f"{path.name} violates the MODULE MANIFEST schema:\n"
        + "\n".join(f"  - {v}" for v in report.violations)
    )
