"""Smoke tests for the marimo notebook entrypoint."""

from importlib import util
from pathlib import Path
import subprocess
import sys

import marimo


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = ROOT / "notebooks/spx_inventory_app.py"


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


def test_notebook_script_exits_under_timeout() -> None:
    result = subprocess.run(
        [sys.executable, str(NOTEBOOK_PATH)],
        cwd=ROOT,
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
    assert "Sanitized fixture preview" in source
    assert "No market data loaded" in source
    assert "Market Data Readiness" in source
    assert "not live" in source
    assert "not broker data" in source
    assert "Manual confirmation required" in source
