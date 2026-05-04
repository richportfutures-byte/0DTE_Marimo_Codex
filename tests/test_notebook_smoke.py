"""Smoke tests for the marimo notebook entrypoint."""

from importlib import util
import os
from pathlib import Path
import subprocess
import sys
import tomllib

import marimo


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = ROOT / "notebooks/spx_inventory_app.py"


def _script_metadata() -> dict[str, object]:
    lines = NOTEBOOK_PATH.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "# /// script"

    metadata_lines: list[str] = []
    for line in lines[1:]:
        if line == "# ///":
            break
        assert line.startswith("#")
        metadata_lines.append(line[1:].lstrip())
    else:
        raise AssertionError("top-level script metadata block is not closed")

    return tomllib.loads("\n".join(metadata_lines))


def _load_notebook_module():
    spec = util.spec_from_file_location("spx_inventory_app_smoke", NOTEBOOK_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_notebook_import_exposes_marimo_app_with_cells() -> None:
    module = _load_notebook_module()

    assert isinstance(module.app, marimo.App)
    assert len(list(module.app._cell_manager.valid_cells())) > 0


def test_notebook_script_metadata_forces_marimo_dark_theme() -> None:
    metadata = _script_metadata()
    marimo_config = metadata.get("tool", {}).get("marimo", {})

    assert isinstance(marimo_config, dict)
    assert marimo_config.get("display") == {"theme": "dark"}


def test_notebook_script_exits_under_timeout() -> None:
    env = os.environ.copy()
    src_path = str(ROOT / "src")
    env["PYTHONPATH"] = (
        src_path
        if not env.get("PYTHONPATH")
        else os.pathsep.join((src_path, env["PYTHONPATH"]))
    )
    result = subprocess.run(
        [sys.executable, str(NOTEBOOK_PATH)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_run_button_exposes_value_frontend() -> None:
    """Fail loudly if marimo removes _value_frontend; click-dedup will silently regress."""
    import marimo as mo

    button = mo.ui.run_button(label="test")
    assert hasattr(button, "_value_frontend"), (
        "marimo run_button no longer exposes _value_frontend; "
        "click-dedup in spx_inventory_app.py will silently regress to double-fire behavior"
    )


def test_app_exposes_cell_manager() -> None:
    """Fail loudly if marimo removes _cell_manager; notebook smoke test will break."""
    module = _load_notebook_module()
    assert hasattr(module.app, "_cell_manager"), (
        "marimo App no longer exposes _cell_manager; "
        "test_notebook_import_exposes_marimo_app_with_cells will need updating"
    )


def test_notebook_source_includes_market_data_readiness_section() -> None:
    source = NOTEBOOK_PATH.read_text(encoding="utf-8")

    assert "evaluate_market_data_facade" in source
    assert "default_fail_closed" in source
    assert "healthy_preview" in source
    assert "stale_underlying" in source
    assert "partial_chain" in source
    assert "locked_liquidity" in source
    assert "missing_atm_straddle" in source
    assert "Sanitized fixture" in source
    assert "No market data loaded" in source
    assert "Market Data Readiness" in source
    assert "not live" in source
    assert "not broker data" in source
    assert "Manual confirmation required" in source


def test_notebook_source_includes_read_only_option_chain_fixture_panel() -> None:
    source = NOTEBOOK_PATH.read_text(encoding="utf-8")

    assert "FixtureOptionChainProvider" in source
    assert "load_marimo_option_chain_provider" in source
    assert "Option Chain Fixture View" in source
    assert "Option Chain Live Schwab View" in source
    assert "Option Chain Failed Live Request" in source
    assert "Refresh Option Chain" in source
    assert "FIXTURE_OPTION_CHAIN_MODE_LABEL" in source
    assert "LIVE_OPTION_CHAIN_MODE_LABEL" in source
    assert "capture-live-option-chain-selection" in source
    assert "static_fixture" in source
    assert "Freshness status" in source
    assert "Data context" in source
    assert "Warning level" in source
    assert "Context reason codes" in source
    assert "display only" in source
    assert "These flags do not authorize trades or change playbook rules" in source
    assert "app-owned sanitized" in source
    assert "fixture" in source
    assert "Not live market data" in source
    assert "Token file path is read from environment" in source
    assert "Last successful result retained" in source
    assert "no automatic refresh" in source
    assert "orders" in source
    assert "trading" in source
    assert "authorization changes" in source


def test_notebook_source_includes_local_only_paper_intent_ledger() -> None:
    source = NOTEBOOK_PATH.read_text(encoding="utf-8")

    assert "PaperTradeLedger" in source
    assert "Record Paper Intent" in source
    assert "Paper Intent Ledger" in source
    assert "Local paper-only recordkeeping" in source
    assert "No broker submission" in source
    assert "no execution" in source
    assert "no playbook authorization changes" in source


def test_notebook_source_keeps_darkmode_titles_and_sidebar_usable() -> None:
    source = NOTEBOOK_PATH.read_text(encoding="utf-8")

    assert "background:#0b1220;color:#e2e8f0" in source
    assert "text-transform:uppercase;color:#cbd5e1" in source
    assert ".app-sidebar{display:block!important" in source
    assert '.app-sidebar[data-expanded="false"]{width:320px!important}' in source
    assert ".app-sidebar + div{display:none!important}" not in source


def test_notebook_source_exposes_operator_sidebar_collapse_and_reopen() -> None:
    source = NOTEBOOK_PATH.read_text(encoding="utf-8")

    assert "left_panel_open_state, set_left_panel_open = mo.state(True)" in source
    assert "left_panel_collapse_button = mo.ui.button" in source
    assert "left_panel_reopen_button = mo.ui.button" in source
    assert 'label="Collapse left panel"' in source
    assert 'label="Show left panel"' in source
    assert "set_left_panel_open(False)" in source
    assert "set_left_panel_open(True)" in source
    assert "_left_panel = (" in source
    assert "if left_panel_open_state()" in source
    assert "\n    _left_panel\n" in source
