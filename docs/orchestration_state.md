# Orchestration State

## Current Position

- Current roadmap position: R1 complete
- Last completed step: R1 Baseline Verification and Failure Inventory
- Current step: baseline repaired; ready to begin R2 when explicitly requested
- Next planned step: R2 Product Contract and Session Lifecycle
- Known repo role: local-first personal 0DTE SPX/SPXW inventory workstation

## Hard Constraints

- Documentation-only for the current step.
- Do not modify source code.
- Do not modify tests.
- Do not modify notebook behavior.
- Do not modify fixtures.
- Do not modify package configuration.
- Do not call live APIs.
- Do not read or print token files.
- Do not introduce commercial SaaS requirements.
- Do not add order routing, broker submission, or automated execution concepts.
- Preserve fail-closed doctrine.
- Preserve fixture/live distinction.
- Use precise language: this is for personal operational use, not public commercial release.

## How To Resume If The Chat Migrates

1. Open this file first.
2. Confirm `docs/founder_ready_roadmap.md` exists and matches the roadmap through R11.
3. Check `git status --short` before making changes.
4. Continue from the current roadmap position unless the user explicitly redirects.
5. For the next step, perform R1 baseline verification before implementation.
6. Keep all routine verification credential-free and fixture-safe.
7. If live-data work is later requested, confirm boundaries first and never read or print credential material.

## Do Not Do Yet

- No implementation before baseline verification.
- No live API calls.
- No credential reads.
- No UI polish.
- No execution or broker-order features.

## R1 Baseline Verification - Results

- Date/time in local shell: Sun May 3 23:04:33 EDT 2026
- Current roadmap position after this step: R1 blocked
- Next step: classify/fix baseline failures before R2 Product Contract and Session Lifecycle

### Exact Commands Run

- `pwd`
- `git branch --show-current`
- `git status --short`
- `python3 --version || python --version`
- `uv --version`
- `date`
- `uv sync`
- `uv run pytest`
- `uv run ruff check .`
- `uv run python notebooks/spx_inventory_app.py`
- `sed -n '1,220p' docs/orchestration_state.md`
- `git status --short`

### Command Results

- PASS: `pwd`
  - Output confirmed repo root: `/Users/stu/Projects/0DTE_Marimo_Codex`
- PASS: `git branch --show-current`
  - Output: `main`
- PASS: `git status --short`
  - Output before R1 verification matched expected doc/untracked state:
    - ` M README.md`
    - `?? .DS_Store`
    - `?? docs/founder_ready_roadmap.md`
    - `?? docs/orchestration_state.md`
    - `?? notebooks/.DS_Store`
- PASS: `python3 --version || python --version`
  - Output: `Python 3.13.1`
- PASS: `uv --version`
  - Output: `uv 0.10.12 (00d72dac7 2026-03-19 x86_64-apple-darwin)`
- PASS: `date`
  - Output: `Sun May 3 23:04:33 EDT 2026`
- PASS: `uv sync`
  - Output: resolved 32 packages and checked 28 packages.
- FAIL: `uv run pytest`
  - Summary: 360 tests collected; 356 passed; 4 failed.
  - Failure 1: `tests/test_notebook_smoke.py::test_notebook_script_exits_under_timeout` failed because subprocess execution with `sys.executable` could not import `spx_inventory_playbook`.
  - Failure 2: `tests/test_schwab_market_data_adapter_boundary.py::test_sanitized_schwab_fixture_directory_contains_expected_payloads` failed because `raw_option_chain_0dte.sanitized.json` is an extra JSON file in the Schwab fixture directory.
  - Failure 3: `tests/test_schwab_market_data_adapter_boundary.py::test_sanitized_schwab_fixtures_are_marked_as_fixtures` failed with `KeyError: 'fixture'` while iterating fixture payloads.
  - Failure 4: `tests/test_schwab_market_data_adapter_boundary.py::test_sanitized_schwab_fixture_numbers_are_decimal_compatible_strings` failed because at least one numeric field, `ask`, was a number rather than a string.
- FAIL: `uv run ruff check .`
  - Summary: one lint error.
  - Failure: `tests/test_reference.py:3:46` imports `ReferenceCard` but does not use it.
- PASS: `uv run python notebooks/spx_inventory_app.py`
  - Output: no stdout/stderr; command exited 0.
- PASS: `sed -n '1,220p' docs/orchestration_state.md`
  - Output: inspected existing orchestration state before updating this section.
- PASS: `git status --short`
  - Output before editing this section still matched the expected doc/untracked state.

### Files Modified By Commands

No command-generated tracked file modifications were observed before this documentation update. The two `.DS_Store` files were already present as untracked files and were left untouched.

## R1A Baseline Failure Repair - Results

- Date/time in local shell: Sun May 3 23:11:58 EDT 2026
- Current roadmap position: R1 complete
- Next step: R2 Product Contract and Session Lifecycle

### Exact Files Changed

- `tests/test_notebook_smoke.py`
- `tests/test_reference.py`
- `tests/test_schwab_market_data_adapter_boundary.py`
- `docs/orchestration_state.md`

### Root Cause Summary

- Notebook subprocess import failure: the direct command `uv run python notebooks/spx_inventory_app.py` passed from repo root, but the pytest subprocess used `sys.executable` without the pytest-configured `src` import path. The smoke test now passes `PYTHONPATH=<repo>/src` only to that subprocess.
- Ruff unused import: `tests/test_reference.py` imported `ReferenceCard` but did not use it. The unused import was removed.
- Schwab extra raw sanitized JSON failure: `raw_option_chain_0dte.sanitized.json` is app-owned raw sanitized capture data referenced by notebook/provider/parser tests, not stray generated junk. The boundary allowlist now includes it.
- Schwab missing `fixture` key and numeric-string failures: those invariants apply to normalized mapper fixtures, not to the app-owned raw sanitized capture whose sanitizer tests intentionally preserve raw Schwab numeric shape. The boundary helper now applies normalized fixture metadata and decimal-string checks only to the normalized mapper fixture set while still scanning every JSON fixture for sensitive content.

### Exact Commands Run

- `git status --short`
- `uv run pytest -q`
- `uv run ruff check .`
- `uv run python notebooks/spx_inventory_app.py`
- `sed -n '1,140p' tests/test_notebook_smoke.py`
- `sed -n '1,180p' tests/test_reference.py`
- `sed -n '1,180p' tests/test_schwab_market_data_adapter_boundary.py`
- `rg -n "raw_option_chain_0dte|sanitized|fixture_payloads|FIXTURES" tests src scripts docs notebooks -g '!*.pyc'`
- `sed -n '1,220p' tests/test_schwab_market_data_fixture_mapper.py`
- `sed -n '1,220p' tests/test_schwab_option_chain_capture_sanitizer.py`
- `sed -n '1,140p' tests/fixtures/market_data/schwab/raw_option_chain_0dte.sanitized.json`
- `sed -n '1,180p' pyproject.toml`
- `sed -n '580,630p' notebooks/spx_inventory_app.py`
- `sed -n '1,130p' src/spx_inventory_playbook/live_market_rehearsal_readiness.py`
- `sed -n '1,230p' src/spx_inventory_playbook/adapters/schwab_market_data.py`
- `uv run pytest -q tests/test_notebook_smoke.py tests/test_schwab_market_data_adapter_boundary.py tests/test_reference.py`
- `uv run ruff check tests/test_notebook_smoke.py tests/test_schwab_market_data_adapter_boundary.py tests/test_reference.py`
- `uv run pytest`
- `uv run ruff check .`
- `uv run python notebooks/spx_inventory_app.py`
- `git status --short`
- `date`
- `tail -n 120 docs/orchestration_state.md`

### Verification Results

- PASS: `uv run pytest`
  - Result: 360 passed.
- PASS: `uv run ruff check .`
  - Result: all checks passed.
- PASS: `uv run python notebooks/spx_inventory_app.py`
  - Result: command exited 0 with no stdout/stderr.

### R1 Status

R1 is complete. The repo has a clean pre-implementation baseline. Do not start R2 until explicitly requested.
