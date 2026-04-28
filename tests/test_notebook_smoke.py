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
