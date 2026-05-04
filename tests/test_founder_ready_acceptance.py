from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def normalized(relative_path: str) -> str:
    return read_text(relative_path).lower()


def assert_contains_all(text: str, fragments: tuple[str, ...]) -> None:
    missing = [fragment for fragment in fragments if fragment not in text]
    assert missing == []


def test_founder_ready_acceptance_doc_exists_and_names_operating_boundaries() -> None:
    path = ROOT / "docs" / "FOUNDER_READY_ACCEPTANCE.md"
    text = normalized("docs/FOUNDER_READY_ACCEPTANCE.md")

    assert path.is_file()
    assert_contains_all(
        text,
        (
            "local-first personal workstation",
            "fixture default",
            "explicit operator opt-in",
            "no silent fallback from live to fixture",
            "restart-safe durable local state",
            "inventory ledger",
            "event/audit evidence",
            "rule engine as primary authorization layer",
            "operator input audit evidence",
            "daily export bundle",
            "scripts/launch_app.sh",
            "scripts/verify.sh",
            "scripts/export_daily_bundle.sh",
            "app-level smoke/regression coverage",
            "no broker submission",
            "no order routing",
            "no automated execution",
            "default verification does not call live apis",
            "do not read or print token files",
        ),
    )


def test_readme_references_operator_commands_and_acceptance_material() -> None:
    text = read_text("README.md")

    assert_contains_all(
        text,
        (
            "scripts/launch_app.sh",
            "scripts/verify.sh",
            "scripts/export_daily_bundle.sh",
            "docs/OPERATOR_RUNBOOK.md",
            "docs/FOUNDER_READY_ACCEPTANCE.md",
            "docs/HANDOFF.md",
        ),
    )


def test_verify_script_is_default_non_live_and_credential_safe() -> None:
    text = read_text("scripts/verify.sh")

    assert "uv run pytest" in text
    assert "uv run ruff check ." in text
    assert "uv run python notebooks/spx_inventory_app.py" in text
    assert "curl" not in text
    assert "capture_live" not in text
    assert "SPX_OPTION_CHAIN_LIVE_TOKEN_FILE" not in text
    assert "SCHWAB_TOKEN_PATH" not in text
    assert "--access-token-file" not in text
    assert "cat " not in text
    assert "printenv" not in text


def test_launch_script_keeps_fixture_default_behavior_safe() -> None:
    text = read_text("scripts/launch_app.sh")

    assert "127.0.0.1" in text
    assert "fixture-default" in text
    assert "Default launch does not read token files or call live APIs." in text
    assert "uv run marimo run notebooks/spx_inventory_app.py" in text
    assert '--host "$HOST"' in text
    assert '--port "$PORT"' in text
    assert "SPX_OPTION_CHAIN_LIVE_TOKEN_FILE" not in text
    assert "SCHWAB_TOKEN_PATH" not in text
    assert "--access-token-file" not in text
    assert "capture_live" not in text


def test_export_bundle_command_shape_remains_local_and_credential_safe() -> None:
    text = read_text("scripts/export_daily_bundle.sh")

    assert "uv run python -m spx_inventory_playbook.daily_export" in text
    assert "--state-root .state" in text
    assert "--fixture-default" in text
    assert ".state/exports" not in text
    assert "SPX_OPTION_CHAIN_LIVE_TOKEN_FILE" not in text
    assert "SCHWAB_TOKEN_PATH" not in text
    assert "--access-token-file" not in text
    assert "curl" not in text
    assert "capture_live" not in text


def test_docs_preserve_no_broker_order_routing_or_automation_boundaries() -> None:
    combined = "\n".join(
        normalized(path)
        for path in (
            "README.md",
            "docs/HANDOFF.md",
            "docs/OPERATOR_RUNBOOK.md",
            "docs/FOUNDER_READY_ACCEPTANCE.md",
            "docs/founder_ready_roadmap.md",
        )
    )

    assert_contains_all(
        combined,
        (
            "no broker submission",
            "no order routing",
            "no automated execution",
            "must not place trades",
            "route orders",
            "submit broker instructions",
        ),
    )


def test_roadmap_and_orchestration_mark_r12_live_runtime_wiring_complete() -> None:
    roadmap = normalized("docs/founder_ready_roadmap.md")
    orchestration = normalized("docs/orchestration_state.md")

    assert "## r11 final founder-ready acceptance" in roadmap
    assert "## r12 - controlled marimo live runtime wiring" in roadmap
    assert "### status\n\ncomplete." in roadmap
    assert "not broker integration and not execution" in roadmap
    assert "controlled live runtime wiring" in roadmap
    assert "spx_option_chain_live_token_file" in roadmap
    assert "default launch or default verification" in roadmap
    assert "current roadmap position: r12 complete" in orchestration
    assert (
        "last completed step: r12 controlled marimo live runtime wiring"
        in orchestration
    )


def test_live_rehearsal_docs_match_current_controlled_notebook_toggle() -> None:
    text = normalized("docs/LIVE_MARKET_REHEARSAL_READINESS.md")

    assert "marimo now has controlled live runtime wiring" in text
    assert "marimo still uses fixture mode only" not in text
    assert "marimo remains fixture-only" not in text
    assert "spx_option_chain_live_token_file" in text
    assert "schwab_token_path is not used by the notebook runtime path" in text
    assert "capture-live-option-chain-selection" in text
    assert "notebook does not display the token path or token contents" in text
