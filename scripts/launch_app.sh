#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

HOST="${SPX_WORKSTATION_HOST:-127.0.0.1}"
PORT="${SPX_WORKSTATION_PORT:-27182}"

if command -v lsof >/dev/null 2>&1; then
  if lsof -ti "tcp:${PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "Port ${PORT} is already in use. Set SPX_WORKSTATION_PORT to another local port or stop the existing server." >&2
    exit 2
  fi
fi

echo "Launching fixture-default local workstation at http://${HOST}:${PORT}"
echo "Default launch does not read token files or call live APIs."
exec uv run marimo run notebooks/spx_inventory_app.py --host "$HOST" --port "$PORT"
