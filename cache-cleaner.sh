#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if command -v python3 >/dev/null 2>&1; then
  exec python3 "$SCRIPT_DIR/cache_cleaner.py" "$@"
fi

if command -v python >/dev/null 2>&1; then
  exec python "$SCRIPT_DIR/cache_cleaner.py" "$@"
fi

echo "Python 3 wurde nicht gefunden. Bitte Python installieren und erneut ausführen." >&2
exit 1
