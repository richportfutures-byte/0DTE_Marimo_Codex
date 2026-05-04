# Orchestration State

## Current Position

- Current roadmap position: R2 complete
- Last completed step: R2 Product Contract and Session Lifecycle
- Current step: session lifecycle product contract implemented and verified
- Next planned step: R3 Durable Local State
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

## R2 Product Contract and Session Lifecycle - Results

- Date/time in local shell: Sun May 3 23:21:17 EDT 2026
- Current roadmap position: R2 complete
- Next step: R3 Durable Local State

### Files Changed

- `src/spx_inventory_playbook/session_lifecycle.py`
- `tests/test_session_lifecycle.py`
- `src/spx_inventory_playbook/__init__.py`
- `docs/orchestration_state.md`

### Design Summary

Added a pure deterministic session lifecycle model for the local-first personal 0DTE SPX/SPXW workstation. The model has no wall-clock, file, environment, network, credential, market-data-provider, broker, or Marimo dependencies. It does not place trades, route orders, submit broker instructions, or imply automated execution.

Invalid transitions fail closed by returning the same state, `allowed=False`, and at least one structured reason code. Closing is allowed from every non-closed state. Closed sessions are terminal, including reset attempts. Reset before close returns to `NOT_STARTED`.

### Explicit Lifecycle States

- `NOT_STARTED`
- `READY_CHECK`
- `DATA_LOADED`
- `INVENTORY_LOADED`
- `AUTHORIZED`
- `RESTRICTED`
- `BLOCKED`
- `SESSION_CLOSED`

### Explicit Transition Rules

- `NOT_STARTED` + `START_READY_CHECK` -> `READY_CHECK`
- `READY_CHECK` + `LOAD_DATA` -> `DATA_LOADED`
- `DATA_LOADED` + `LOAD_INVENTORY` -> `INVENTORY_LOADED`
- `INVENTORY_LOADED` + `AUTHORIZE` -> `AUTHORIZED`
- `RESTRICT` -> `RESTRICTED` from active operational states only.
- `BLOCK` -> `BLOCKED` from any non-closed state.
- `CLOSE_SESSION` -> `SESSION_CLOSED` from any non-closed state.
- `RESET_SESSION` -> `NOT_STARTED` from any non-closed state.
- Any action from `SESSION_CLOSED` is blocked with `SESSION_CLOSED_TERMINAL`.
- Other invalid transitions return the same state with a structured reason code.

### Tests Added

- Initial ready-check transition.
- Data load transition.
- Inventory load transition.
- Authorization only after inventory load.
- Direct authorization from `NOT_STARTED`, `READY_CHECK`, and `DATA_LOADED` is blocked.
- Restriction from `INVENTORY_LOADED` is allowed.
- Block from every non-closed state is allowed.
- Close from every non-closed state is allowed.
- Closed session is terminal.
- Invalid transitions preserve current state and include a reason code.
- Reset behavior is explicit before and after close.
- Decisions are deterministic and contain structured reason codes.

### Commands Run

- `git status --short`
- `git log -3 --oneline`
- `uv run pytest`
- `uv run ruff check .`
- `uv run python notebooks/spx_inventory_app.py`
- `sed -n '1,260p' docs/founder_ready_roadmap.md`
- `sed -n '1,260p' docs/orchestration_state.md`
- `cat src/spx_inventory_playbook/__init__.py`
- `sed -n '1,220p' src/spx_inventory_playbook/rules.py`
- `sed -n '1,180p' src/spx_inventory_playbook/validators.py`
- `sed -n '1,200p' tests/test_rules.py`
- `uv run pytest -q tests/test_session_lifecycle.py`
- `uv run ruff check src/spx_inventory_playbook/session_lifecycle.py tests/test_session_lifecycle.py src/spx_inventory_playbook/__init__.py`
- `date`
- `uv run pytest`
- `uv run ruff check .`
- `uv run python notebooks/spx_inventory_app.py`

### Verification Results

- PASS: baseline `uv run pytest`
  - Result before R2 edits: 360 passed.
- PASS: baseline `uv run ruff check .`
  - Result before R2 edits: all checks passed.
- PASS: baseline `uv run python notebooks/spx_inventory_app.py`
  - Result before R2 edits: command exited 0 with no stdout/stderr.
- PASS: targeted `uv run pytest -q tests/test_session_lifecycle.py`
  - Result: 15 passed.
- PASS: targeted `uv run ruff check src/spx_inventory_playbook/session_lifecycle.py tests/test_session_lifecycle.py src/spx_inventory_playbook/__init__.py`
  - Result: all checks passed.

- PASS: post-edit `uv run pytest`
  - Result: 375 passed.
- PASS: post-edit `uv run ruff check .`
  - Result: all checks passed.
- PASS: post-edit `uv run python notebooks/spx_inventory_app.py`
  - Result: command exited 0 with no stdout/stderr.

R2 is complete. The next step is R3 Durable Local State. Do not start R3 until explicitly requested.
