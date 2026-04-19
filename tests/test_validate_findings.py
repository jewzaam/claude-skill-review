"""Tests for scripts/validate-findings.py."""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "validate-findings.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )


class TestValidateFindings:
    def test_valid_agent_output_exits_zero(self):
        result = _run([str(FIXTURES / "agent-output.valid.json")])
        assert result.returncode == 0, result.stderr

    def test_invalid_agent_output_exits_nonzero(self):
        result = _run([str(FIXTURES / "agent-output.invalid-no-locations.json")])
        assert result.returncode != 0
        assert "locations" in (result.stderr + result.stdout).lower()

    def test_explicit_schema_flag(self):
        result = _run(
            ["--schema", "consolidated", str(FIXTURES / "consolidated.valid.json")]
        )
        assert result.returncode == 0, result.stderr

    def test_unknown_schema_name_exits_nonzero(self):
        result = _run(
            ["--schema", "nonsense", str(FIXTURES / "agent-output.valid.json")]
        )
        assert result.returncode != 0

    def test_missing_file_exits_nonzero(self):
        result = _run([str(FIXTURES / "does-not-exist.json")])
        assert result.returncode != 0
