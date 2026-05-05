# Founder-Ready Completion Roadmap

This roadmap defines the path from the current Marimo-based SPX/SPXW 0DTE inventory reference and decision-support shell to a founder-ready personal workstation.

The target is local-first personal operational use. It is not commercial SaaS, not an order execution platform, and not a broker submission system. The workstation must remain restart-safe, live-data-aware, audit-preserving, fail-closed, and clear about fixture versus live data.

## R0 Baseline, Roadmap, and Orchestration State

### Goal

Establish durable documentation that future LLM orchestration can use to resume the work safely and consistently.

### Deliverables

- A founder-ready completion roadmap.
- A persistent orchestration-state document.
- README links to the roadmap and orchestration-state documents.

### Non-goals

- No source-code changes.
- No test changes.
- No notebook behavior changes.
- No package, fixture, or market-data changes.
- No live API calls or credential reads.

### Acceptance criteria

- `docs/founder_ready_roadmap.md` exists and contains roadmap sections R0 through R11.
- `docs/orchestration_state.md` exists and records current position as R0.
- `README.md` links to both documents.
- Git diff shows documentation-only changes.

### Dependencies

- Existing repository docs and README.
- Existing app role and constraints described by the repository and current task.

### Resume note for future LLM orchestration

Resume from R0 only to verify that the roadmap and orchestration-state docs exist, are linked from README, and preserve the personal local-first, fail-closed, no-execution doctrine. Then proceed to R1.

## R1 Baseline Verification and Failure Inventory

### Goal

Create a factual baseline of the current app behavior, test coverage, known gaps, and failure modes before implementation begins.

### Deliverables

- A baseline verification note covering app sections, docs, tests, fixtures, and market-data boundaries.
- A failure inventory that distinguishes confirmed failures, missing coverage, ambiguous behavior, and future design questions.
- A restart-safe checklist for reproducing the baseline locally.

### Non-goals

- No feature implementation.
- No UI polish.
- No live API calls.
- No credential reads.
- No edits to notebook behavior unless a later roadmap step explicitly authorizes them.

### Acceptance criteria

- Baseline commands and results are recorded with dates.
- Any failures are documented without being silently fixed.
- Fixture/live distinctions are explicitly preserved.
- No implementation work starts before baseline findings are reviewed.

### Dependencies

- R0 documentation.
- Existing test suite, README, docs, notebooks, and fixtures.

### Resume note for future LLM orchestration

Start by reading `docs/orchestration_state.md`, then inspect repository status. Run only baseline-safe local commands, avoid credentials and live APIs, and record findings before making code changes.

## R2 Product Contract and Session Lifecycle

### Goal

Define the workstation contract and daily session lifecycle so the app has a clear operational shape for personal use.

### Deliverables

- Product contract describing supported use cases, operator responsibilities, and hard boundaries.
- Session lifecycle specification from pre-market preparation through end-of-day export.
- Explicit failure, stale-data, manual-confirmation, and no-trade states.

### Non-goals

- No commercial onboarding, billing, tenancy, or multi-user requirements.
- No automated execution, broker-order routing, or trade submission workflows.
- No replacement of operator judgment.

### Acceptance criteria

- The product contract states that the app is a local-first personal SPX/SPXW 0DTE inventory workstation.
- Session lifecycle states are restart-safe and audit-preserving.
- Fail-closed behavior is the default for missing, stale, partial, or unverifiable data.
- The app boundary remains decision support, not execution.

### Dependencies

- R1 baseline verification and failure inventory.
- Existing README live-data-safe boundaries.

### Resume note for future LLM orchestration

Use R2 to settle language and operating semantics before touching storage, ledgers, or UI flows. Treat unclear execution-adjacent concepts as out of scope.

## R3 Durable Local State

### Goal

Design and implement restart-safe local persistence for personal workstation state without introducing hosted services.

### Deliverables

- Local state model for current session, operator inputs, selected market-data mode, positions, and audit metadata.
- Recovery behavior for app restarts and partial writes.
- Migration or versioning strategy suitable for local files.
- Documentation for where state lives and how to back it up.

### Non-goals

- No cloud database.
- No SaaS account model.
- No hidden credential storage.
- No broker integration.

### Acceptance criteria

- State survives app restarts.
- Corrupt, missing, or incompatible state fails closed with clear recovery guidance.
- State files do not contain access tokens or secrets.
- Persistence preserves fixture/live mode distinctions.

### Dependencies

- R1 baseline verification.
- R2 product contract and session lifecycle.

### Resume note for future LLM orchestration

Design local state before implementation. Keep storage explicit, inspectable, and recoverable. Do not read token files while exploring the repo.

## R4 Inventory Ledger

### Goal

Create an audit-preserving inventory ledger for positions, lifecycle events, adjustments, thesis changes, and closures.

### Deliverables

- Append-oriented ledger model for inventory events.
- Position reconstruction rules from ledger history.
- Manual correction workflow that preserves prior records.
- Ledger export schema for review and tax-adjacent recordkeeping support.

### Non-goals

- No broker statement ingestion unless explicitly added in a later personal-use step.
- No tax advice.
- No execution confirmation or order placement.
- No destructive history edits.

### Acceptance criteria

- Position state can be reconstructed from ledger events.
- Adjustments and closures preserve prior event history.
- Manual corrections are recorded as new auditable events.
- Ledger behavior remains deterministic under restart.

### Dependencies

- R3 durable local state.
- Existing position and paper-trade logic.

### Resume note for future LLM orchestration

Treat the ledger as the source of operational memory. Preserve audit history even when correcting mistakes.

## R5 Market Data Provider Unification

### Goal

Unify fixture and approved live market-data provider flows behind explicit contracts, health states, and fail-closed behavior.

### Deliverables

- Provider contract for quotes, option chains, timestamps, provenance, and freshness.
- Mode selection semantics for fixture versus live data.
- Provider health and degradation states.
- Documentation for approved live-data boundaries.

### Non-goals

- No calls to live APIs during documentation or design-only work.
- No unsupported data providers.
- No fabricated Greeks, IV, strikes, marks, fills, or P/L.
- No credential display or token inspection.

### Acceptance criteria

- Fixture and live data remain visibly distinct.
- Missing, stale, partial, or unverifiable data fails closed or requires manual confirmation.
- Provider responses carry provenance and freshness metadata.
- Tests cover provider contract behavior without requiring live API calls.

### Dependencies

- R1 baseline verification.
- Existing market-data facade, adapters, fixtures, and tests.
- R2 product contract.

### Resume note for future LLM orchestration

Inspect provider contracts and tests before editing. Never call live APIs or read credentials unless a later explicit user request permits a safe live rehearsal.

## R6 Rule Engine as Main Authorization Layer

### Goal

Promote deterministic rules into the main authorization layer for workstation decisions and actions.

### Deliverables

- Rule contract defining allowed, blocked, warning, no-trade, and manual-confirmation states.
- Mapping from data health, inventory state, operator intent, and playbook constraints into authorization outcomes.
- Audit records for rule decisions.
- Tests proving fail-closed defaults.

### Non-goals

- No machine-learning authorization.
- No discretionary bypass without audit.
- No automated execution.
- No hidden rule exceptions.

### Acceptance criteria

- Risk-relevant actions are gated by deterministic rules.
- Unknown or invalid inputs resolve to blocked, no-trade, or manual-confirmation states.
- Rule decisions are explainable and reproducible.
- Rule outcomes do not imply trade execution.
- Fixture data is simulation-only; stale, unavailable, parse-error, missing, or ambiguous market-data states block or severely restrict live authorization.
- Operator-facing authorization views read from the typed rule-engine decision rather than ad hoc notebook logic.

### Dependencies

- R2 product contract.
- R3 durable local state.
- R4 inventory ledger.
- R5 market-data provider unification.
- Existing validators, rules, playbook, and calculators.

### Resume note for future LLM orchestration

Keep the rule engine conservative. If a state cannot be proven valid, the authorization layer must fail closed.

## R7 Operator Input Workflow

### Goal

Make operator inputs deliberate, validated, and auditable across session setup, trade planning, position management, and review.

### Deliverables

- Input workflow specification for required fields, optional notes, confirmations, and validation messages.
- Manual confirmation patterns for degraded or stale data.
- Clear distinction between observed data, operator-entered data, calculated values, and rule decisions.
- Audit records for meaningful operator actions.

### Non-goals

- No UI polish for its own sake.
- No natural-language auto-trading.
- No broker-order ticket generation.
- No public-user onboarding flow.

### Acceptance criteria

- Operator-entered values are validated before use.
- Confirmations are explicit where data quality or risk state requires them.
- App text preserves decision-support boundaries.
- Inputs that affect inventory or rule outcomes are audit-preserving.
- The notebook's default authorization workflow consumes structured operator inputs; missing, ambiguous, or invalid inputs fail closed before rule evaluation proceeds.
- Fixture presets remain labeled simulation/demo inputs and cannot become live authorization.

### Dependencies

- R2 product contract.
- R3 durable local state.
- R4 inventory ledger.
- R6 rule authorization.

### Resume note for future LLM orchestration

Design inputs around operational clarity, not decoration. Preserve the distinction between what the operator says, what the data provider says, and what the rule engine authorizes.

## R8 Daily Export Bundle

### Status

Complete. R8 adds a deterministic local JSON/markdown export bundle command under the repo-owned `.state/exports/daily/{trading_date}/{session_id}/` path. The export preserves session metadata, lifecycle events, inventory snapshots, paper intents, market-data provenance, authorization audit evidence, operator notes, and structured operator-input placeholders without live API calls, credential reads, broker submission, order routing, or automated execution.

### Goal

Produce a daily local export bundle that preserves session state, inventory events, data provenance, rule decisions, and operator notes.

### Deliverables

- Export bundle format and directory convention.
- Daily session summary.
- Ledger export.
- Rule-decision log.
- Market-data provenance and freshness summary.
- Operator notes and prompts used during the session.

### Non-goals

- No cloud publishing requirement.
- No public reporting workflow.
- No tax filing automation.
- No broker submission artifacts.

### Acceptance criteria

- Exports are local, inspectable, and restart-safe.
- Exported data distinguishes fixtures, live data, manual inputs, calculated values, and rule decisions.
- Missing or invalid session data produces a clear failed export state rather than partial silent success.
- Export can be regenerated deterministically where source state is unchanged.

### Dependencies

- R3 durable local state.
- R4 inventory ledger.
- R5 market-data provider unification.
- R6 rule authorization.
- R7 operator input workflow.

### Resume note for future LLM orchestration

Treat the export bundle as the workstation's daily evidence package. Do not add hosted sharing or SaaS reporting concepts.

## R9 App-Level Smoke and Regression Tests

### Status

Complete. R9 adds fixture-only app-level regression coverage for notebook import/script smoke, deterministic session lifecycle and restart-safe state recovery, live-data gating, daily export bundle generation, rule-engine authorization integration, operator-input audit serialization, and secret redaction.

### Goal

Add app-level confidence that critical personal-workstation workflows remain intact across restarts and refactors.

### Deliverables

- Smoke tests for notebook import or script execution as appropriate.
- Regression tests for session lifecycle, local state recovery, ledger reconstruction, provider gating, rule authorization, and export bundle generation.
- Fixture-only test paths for market-data-dependent behavior.
- Documentation for test scope and known manual checks.

### Non-goals

- No live API dependency in routine tests.
- No brittle visual snapshot suite unless justified by workflow risk.
- No test changes before baseline verification.

### Acceptance criteria

- Routine tests run without credentials or live network calls.
- Critical workflows have regression coverage.
- Fail-closed cases are tested.
- Tests do not blur fixture/live boundaries.

### Dependencies

- R1 baseline verification.
- R3 through R8 implementation outcomes.

### Resume note for future LLM orchestration

Use tests to protect operational behavior, not to encode incidental UI layout. Keep routine test runs fixture-only and credential-free.

## R10 Launch Ergonomics and Runbooks

### Status

Complete. R10 adds repo-owned launch, verification, and fixture/default export wrappers plus an operator runbook for local startup, verification, daily export, live-data safety, degraded data handling, restart/recovery, troubleshooting, and the no-push boundary.

### Goal

Make the workstation easy and safe to start, operate, recover, and shut down during a trading day.

### Deliverables

- Personal launch checklist.
- Local runbook for normal startup, degraded data, stale data, restart recovery, export, and end-of-day shutdown.
- Clear troubleshooting guidance.
- Optional command wrappers if justified by baseline findings and implementation state.

### Non-goals

- No commercial deployment guide.
- No hosted infrastructure.
- No support playbook for other users.
- No broker execution setup.

### Acceptance criteria

- A founder/operator can start the app from a clean local checkout using documented commands.
- Runbooks describe what to do when data, state, or validation fails.
- Recovery steps preserve audit records.
- Launch instructions do not require live credentials for fixture-mode use.

### Dependencies

- R2 product contract.
- R3 durable local state.
- R5 market-data provider unification.
- R8 daily export bundle.
- R9 app-level tests.

### Resume note for future LLM orchestration

Keep runbooks practical and local. They should help one operator complete the trading-day routine safely, not launch a public product.

## R11 Final Founder-Ready Acceptance

### Status

Complete. R11 adds the final founder-ready acceptance artifact and deterministic acceptance tests over the repo's local-first personal operating envelope, fixture/default behavior, explicit live opt-in, no-silent-fallback doctrine, restart-safe durable local state, inventory and event/audit evidence, rule authorization, operator-input audit evidence, local daily export bundle, launch/verify/export wrappers, app-level smoke/regression coverage, no broker/order/execution boundaries, and default non-live credential-safe verification.

### Goal

Verify the app is ready for disciplined personal operational use as a local-first SPX/SPXW 0DTE inventory workstation.

### Deliverables

- Final acceptance checklist.
- Evidence of passing routine tests.
- Manual workflow review notes.
- Known limitations and explicit out-of-scope list.
- Updated orchestration state marking roadmap completion.

### Non-goals

- No public commercial release.
- No order routing, broker submission, or automated execution.
- No claim that the app removes trading risk.
- No hidden live-data or credential assumptions.

### Acceptance criteria

- The workstation can run locally in fixture mode without credentials.
- Live-data-aware behavior is gated, provenance-bearing, and fail-closed.
- Inventory state is restart-safe and audit-preserving.
- Daily export bundle captures operational evidence.
- Rule authorization blocks unsafe, stale, partial, or unknown states.
- README and runbooks accurately describe personal-use boundaries.

### Dependencies

- Completion and verification of R1 through R10.

### Resume note for future LLM orchestration

At R11, verify evidence instead of adding scope. Founder-ready means personally operable, restart-safe, audited, and bounded; it does not mean SaaS-ready or execution-enabled.

## R12 - Controlled Marimo Live Runtime Wiring

### Status

Complete. R12 documents and tightens the controlled runtime bridge that connects
the already-approved Schwab live option-chain provider boundary to the Marimo
notebook under explicit operator opt-in.

This is not broker integration and not execution. It does not add order routing,
account access, positions import, fill import, or P/L import.

### Goal

Make the roadmap and current code reality explicit, then preserve the smallest
safe live-runtime path for display-only SPX option-chain cells in the notebook.

### Deliverables

- Controlled Marimo runtime wiring from the option-chain source controls to the
  approved live Schwab option-chain provider boundary.
- Documentation that distinguishes fixture/default operation, controlled live
  runtime wiring, and the separate manual live rehearsal command.
- Deterministic tests for fixture default behavior, live gate failures, mocked
  live success, stale/unavailable/parse-error classification, secret-safe
  summaries, and roadmap/runbook accuracy.

### Non-goals

- No broker integration.
- No order execution, order routing, broker submission, account actions,
  positions import, fill import, or P/L import.
- No automatic refresh loops.
- No production-grade live-data claim.
- No live APIs, token-file reads, or credential requirements in default launch
  or default verification.
- R12 does not make default launch or default verification live.

### Acceptance criteria

- Fixture mode remains the default.
- Live option-chain data requires explicit live source selection, the exact
  manual confirmation phrase, a configured local token source initialized
  outside the notebook, and a manual refresh.
- The notebook uses only the repo-native `SPX_OPTION_CHAIN_LIVE_TOKEN_FILE`
  token-file source.
- Live data carries source, timestamp, freshness status, and fixture/live
  classification.
- Live failure remains live failure and never silently falls back to fixture
  data.
- Last successful retained context is limited to explicitly fresh/aging live
  option-chain results.
- Deterministic tests pass without credentials or network access.
- Separate manual live rehearsal remains available through
  `scripts/capture_live_schwab_option_chain_selection.py`.

### Dependencies

- R5 market-data provider unification.
- R9 app-level regression coverage.
- R10 launch ergonomics and runbooks.
- R11 final founder-ready acceptance boundaries.

### Resume note for future LLM orchestration

Treat R12 as controlled live runtime wiring only. Keep default commands
fixture-safe and credential-free. A real Schwab request belongs only in an
explicit operator-run live rehearsal or manually refreshed notebook session with
the required local token source and confirmation phrase.

## R13 - Single-Active-App Schwab Token Manager

### Status

Next active roadmap step. R13 is not implemented by this documentation update.
R12 remains complete and verified at commit
`5e63a7ea5f95fe6cdaca0917627920083e02d004`.

### Correct Interpretation

R13 means `0DTE_Marimo_Codex` becomes self-sufficient for Schwab token refresh
when it is the active 0DTE live app. R13 does not mean `ntb-marimo-console` is
deleted, retired, permanently disabled, or barred from future reference use.

The ownership doctrine is:

- One Schwab registered developer app / key-secret-callback configuration.
- Multiple local repos may use that Schwab app configuration serially.
- Only one Schwab-authenticated live process should be active at a time.
- Do not run `0DTE_Marimo_Codex` live and `ntb-marimo-console` live
  simultaneously.
- `ntb-marimo-console` remains allowed as a donor/reference repo.
- `ntb-marimo-console` remains allowed as a separate live harness only when
  `0DTE_Marimo_Codex` is shut down.
- `0DTE_Marimo_Codex` is the primary implementation target for the 0DTE
  workstation.

### Goal

Add an 0DTE-native Schwab token manager so the notebook live option-chain path
can refresh an expired token before a manually gated live REST request, while
preserving fixture defaults and fail-closed behavior.

### Deliverables

- 0DTE-native Schwab token manager.
- Token refresh before the live option-chain REST request when refresh is
  needed.
- Atomic token-file rewrite.
- Preservation of the existing refresh token when Schwab omits a replacement
  refresh token.
- Live refresh failures surfaced as live failures.
- Deterministic mocked tests only.

### Non-goals

- No automatic refresh loop.
- No streaming sidecar.
- No order routing.
- No account access.
- No fills.
- No positions import.
- No P/L import.
- No broker/execution integration.
- No official Schwab REST rate-limit claims.
- No live API calls in routine tests or default verification.

### Acceptance criteria

- Fixture mode remains the default and remains credential-free.
- Live mode still requires explicit source selection, exact confirmation phrase,
  configured local credential source, and manual refresh.
- Token refresh occurs only inside the explicit live path when needed.
- Token-file writes are atomic and do not print, export, or log token contents.
- If refresh fails, the live request fails closed and does not fall back to
  fixture data.
- If Schwab omits a new refresh token, the prior refresh token is preserved.
- Tests use mocked HTTP/token responses only and do not require real credentials
  or network access.
- Secret-bearing values are not printed, displayed, committed, exported, or
  logged, including access tokens, refresh tokens, app secrets, Authorization
  headers, bearer tokens, callback URLs with codes, account IDs, customer IDs,
  correl IDs, streamer URLs, raw Schwab payload bodies, Schwab user preference
  raw responses, or token-file contents.

### Dependencies

- R12 controlled Marimo live runtime wiring.
- Existing manually gated Schwab option-chain provider boundary.
- Existing fixture-safe launch, verification, and test doctrine.

### Resume note for future LLM orchestration

R13 implementation must stay inside `0DTE_Marimo_Codex`. Use
`ntb-marimo-console` only as a donor/reference for Schwab OAuth, token, or
harness behavior. Do not implement R14 architecture audit findings, R15 hybrid
market-data implementation, or R16 market-data panel integration in R13.

## R14 - Hybrid Continuous Market Data Architecture Audit

### Status

Future step after R13.

### Corrected Live-Data Objective

The final live-data architecture should be hybrid. The app should continuously
update SPX/SPXW price, selected option quotes, option-chain context, and Greeks
to the maximum extent permitted by Schwab's documented REST and Streamer
capabilities while preserving fail-closed behavior, single-active-app
ownership, conservative REST usage, and explicit source/freshness labeling.

REST is the source for option-chain discovery, full chain snapshots,
expiration/strike universe, ATM straddle context, chain-level liquidity, and
Greeks when the REST chain endpoint provides them. Schwab Streamer/WebSocket is
the source for continuous underlying price and selected option quote updates
where Schwab supports the requested symbols and fields.

Do not claim the full option chain is streaming unless Schwab documentation
proves it. Do not claim Greeks are streaming unless Schwab documentation proves
the fields.

### Scope

- Determine exactly which data comes from REST.
- Determine exactly which data comes from Streamer.
- Confirm symbol/field support for SPX/SPXW, selected option contracts,
  underlying/index proxies, Greeks, and quote fields based on available Schwab
  documentation and local donor harness behavior.
- Define the source/freshness model for underlying price, selected option
  quotes, option-chain snapshot, Greeks, ATM straddle context, and liquidity.
- Define a conservative REST refresh policy for chain/Greeks snapshots without
  aggressive undocumented polling.
- Define a streamer quote-cache model for continuous selected quotes.
- Define fail-closed authorization behavior when any required source is stale,
  unavailable, or parse-invalid.
- Identify open Schwab support/documentation questions before implementation.

### Non-goals

- No token-manager implementation.
- No REST auto-refresh implementation.
- No streamer sidecar implementation.
- No official Schwab REST rate-limit claims unless verified from official
  Schwab documentation in a future prompt.
- No broker/order/execution/account behavior.
- No fills, positions import, or P/L import.

### Open Schwab Documentation Questions

- Official REST limits for chains, quotes, and pricehistory.
- Numeric Streamer symbol limit.
- Whether `$SPX`/SPXW index options stream through `LEVELONE_OPTIONS`,
  `OPTIONS_BOOK`, both, or neither.
- Whether Greeks are available via streaming fields or only REST chain
  snapshots.

## R15 - Hybrid REST Chain/Greeks Refresh + Streamer Quote Cache Implementation

### Status

Future step after R14.

### Scope

- Implement a single-active Schwab streamer sidecar/cache.
- Implement a conservative REST chain/Greeks refresh layer for full chain
  discovery, chain snapshots, expiration/strike universe, ATM straddle context,
  chain-level liquidity, and Greeks when REST provides them.
- Stream supported underlying price and selected option quote fields where
  Schwab supports the symbols and fields.
- Marimo reads snapshots from cache/state.
- No long-running WebSocket loop inside ordinary notebook cells.
- Label source and freshness for every displayed field.
- Fail closed when required REST or Streamer data is stale, unavailable, or
  parse-invalid.
- Preserve no fixture fallback after live failure.

### Non-goals

- No claim that full-chain streaming or streaming Greeks exist unless Schwab
  documentation proves it.
- No aggressive undocumented REST polling.
- No multiple simultaneous Schwab streamer owners.
- No order routing, account actions, fills, positions import, P/L import, or
  broker/execution integration.

## R16 - Continuous Market Data Panel Integration

### Status

Future step after R15.

### Scope

- Integrate continuous market-data state into the Marimo app.
- Show source, last update time, age, and freshness classification for
  underlying price, selected option quotes, option-chain snapshot, Greeks, ATM
  straddle context, and liquidity.
- Use freshness to gate live-dependent authorization.
- Preserve fixture-safe default behavior.
- Preserve manual/live opt-in controls where appropriate.

### Non-goals

- No order routing, account actions, fills, positions import, P/L import, or
  broker/execution integration.
- No default live launch or default live verification.
- No fixture fallback after live failure.
