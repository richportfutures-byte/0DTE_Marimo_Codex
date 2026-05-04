from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_NAMES = (
    "launch_app.sh",
    "verify.sh",
    "export_daily_bundle.sh",
)


def script_path(name: str) -> Path:
    return ROOT / "scripts" / name


def test_launch_verify_and_export_scripts_exist_and_are_executable() -> None:
    for name in SCRIPT_NAMES:
        path = script_path(name)
        text = path.read_text(encoding="utf-8")

        assert path.is_file()
        assert os.access(path, os.X_OK)
        assert text.startswith("#!/usr/bin/env bash\n")
        assert "set -euo pipefail" in text


def test_verify_script_runs_founder_ready_sequence_without_hiding_output() -> None:
    text = script_path("verify.sh").read_text(encoding="utf-8")

    assert "uv run pytest" in text
    assert "uv run ruff check ." in text
    assert "uv run python notebooks/spx_inventory_app.py" in text
    assert ">/dev/null" not in text
    assert "2>/dev/null" not in text


def test_launch_script_defaults_to_local_fixture_safe_marimo_command() -> None:
    text = script_path("launch_app.sh").read_text(encoding="utf-8")

    assert "127.0.0.1" in text
    assert "27182" in text
    assert 'export PYTHONPATH="${ROOT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}"' in text
    assert "uv run marimo run notebooks/spx_inventory_app.py" in text
    assert '--host "$HOST"' in text
    assert '--port "$PORT"' in text
    assert "lsof" in text
    assert "already in use" in text
    assert "kill" not in text
    assert "SPX_OPTION_CHAIN_LIVE_TOKEN_FILE" not in text
    assert "SCHWAB_TOKEN_PATH" not in text


def test_export_script_uses_fixture_default_daily_export_path() -> None:
    text = script_path("export_daily_bundle.sh").read_text(encoding="utf-8")

    assert "uv run python -m spx_inventory_playbook.daily_export" in text
    assert "--state-root .state" in text
    assert "--fixture-default" in text
    assert "SPX_OPTION_CHAIN_LIVE_TOKEN_FILE" not in text
    assert "SCHWAB_TOKEN_PATH" not in text


def test_runbook_and_handoff_reference_existing_launch_artifacts() -> None:
    runbook = (ROOT / "docs" / "OPERATOR_RUNBOOK.md").read_text(encoding="utf-8")
    handoff = (ROOT / "docs" / "HANDOFF.md").read_text(encoding="utf-8")
    combined = f"{runbook}\n{handoff}"

    for relative_path in (
        "scripts/launch_app.sh",
        "scripts/verify.sh",
        "scripts/export_daily_bundle.sh",
        "docs/OPERATOR_RUNBOOK.md",
        "notebooks/spx_inventory_app.py",
    ):
        assert (ROOT / relative_path).exists()
        assert relative_path in combined

    assert "Do not push unless explicitly instructed" in combined
    assert "does not place trades" in runbook
    assert "does not require live credentials" in combined
    assert "fixture/default" in combined
