#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

TRADING_DATE="${1:-$(date +%F)}"
SESSION_ID="${2:-fixture-${TRADING_DATE}}"

uv run python -m spx_inventory_playbook.daily_export \
  --state-root .state \
  --session-id "$SESSION_ID" \
  --trading-date "$TRADING_DATE" \
  --fixture-default
