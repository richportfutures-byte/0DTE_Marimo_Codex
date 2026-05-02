#!/usr/bin/env python3
"""Manual-gated live Schwab option-chain selection harness."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from spx_inventory_playbook.adapters.live_schwab_option_chain_provider import (  # noqa: E402
    MANUAL_LIVE_CONFIRM_PHRASE,
    ManualLiveSchwabOptionChainConfig,
    format_live_harness_summary,
    run_manual_live_schwab_option_chain_selection,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run one manually confirmed live Schwab option-chain selection request "
            "and print sanitized summary diagnostics only."
        )
    )
    parser.add_argument("--confirm-live", default="")
    parser.add_argument("--access-token-file", type=Path)
    parser.add_argument("--access-token-stdin", action="store_true")
    parser.add_argument("--symbol", default="$SPX")
    parser.add_argument("--strike-count", type=int, default=2)
    parser.add_argument("--timeout-seconds", type=float, default=10.0)
    return parser


def run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    stdin = sys.stdin if args.access_token_stdin else None
    result = run_manual_live_schwab_option_chain_selection(
        config=ManualLiveSchwabOptionChainConfig(
            confirm_live=args.confirm_live,
            symbol=args.symbol,
            strike_count=args.strike_count,
            timeout_seconds=args.timeout_seconds,
        ),
        access_token_file=args.access_token_file,
        access_token_stdin=stdin,
    )
    sys.stdout.write(format_live_harness_summary(result))
    if result.status == "available":
        return 0
    if result.reason_code == "manual_live_confirmation_required":
        sys.stdout.write(f"confirm_phrase: {MANUAL_LIVE_CONFIRM_PHRASE}\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(run())
