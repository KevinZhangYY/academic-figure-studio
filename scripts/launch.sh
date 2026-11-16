#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
if [ -n "${SEM_PYTHON:-}" ]; then
  PY="$SEM_PYTHON"
elif python3 -c 'import PIL,numpy' >/dev/null 2>&1; then
  PY=python3
elif [ -x "$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3" ]; then
  PY="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
else
  echo 'Install Python dependencies: python3 -m pip install -r requirements.txt' >&2
  exit 1
fi
if [ ! -d "$ROOT/node_modules/@pdf-lib/fontkit" ]; then
  echo 'Run npm ci in the plugin directory before PDF/PPTX export.' >&2
fi
exec "$PY" "$ROOT/scripts/server.py" "$@"
