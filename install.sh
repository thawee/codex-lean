#!/usr/bin/env bash
# Installs portable settings only. Never copies authentication or session state.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$ROOT/scripts/install.py" "$ROOT/codex" "${CODEX_HOME:-$HOME/.codex}"
