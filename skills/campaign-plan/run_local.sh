#!/usr/bin/env bash
# Run a campaign-plan refresh LOCALLY (open network) — the workaround for the Cowork sandbox
# being unable to reach Google's OAuth endpoint. Runs fine from any teammate's own Mac.
# Usage: ./run_local.sh <client-slug> [--as-of YYYY-MM-DD] [other refresh.py flags]
set -euo pipefail
CLIENT="${1:-}"
if [ -z "$CLIENT" ]; then echo "usage: ./run_local.sh <client-slug> [--as-of YYYY-MM-DD]"; exit 1; fi
shift
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KEY="${SPICE_SHEETS_KEY:-$HOME/.config/spice/google-sheets-writer.json}"
PY="${SPICE_PY:-python3}"

if [ ! -f "$KEY" ]; then
  echo "❌ Google service-account key not found at: $KEY"
  echo "   Get it from Maxx/Santi, save it there (or set SPICE_SHEETS_KEY=/path/to/key.json)."
  exit 1
fi
if ! "$PY" -c "import googleapiclient, google.oauth2.service_account" 2>/dev/null; then
  echo "❌ '$PY' is missing Google API deps. Install them:"
  echo "     $PY -m pip install --user google-api-python-client google-auth openpyxl"
  echo "   (or set SPICE_PY to a venv python that has them)"
  exit 1
fi
if [[ " $* " == *" --dry-run "* ]]; then
  echo "→ Refreshing '$CLIENT' locally — DRY RUN, nothing will be written."
else
  echo "→ Refreshing '$CLIENT' locally — this writes the live Google Sheet."
fi
"$PY" "$HERE/references/refresh.py" --client "$CLIENT" "$@"
