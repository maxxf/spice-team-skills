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

# The credential can arrive two ways: injected by HQ secrets, or as a local key file.
# Ask creds.py rather than testing for the file here, so the wrapper can never disagree
# with what the Python actually accepts.
if ! "${SPICE_PY:-python3}" -c "import sys;sys.path.insert(0,'$HERE/references');import creds;sys.exit(0 if creds.available() else 1)" 2>/dev/null; then
  echo "❌ No Google service-account credential."
  echo "   Either run it through HQ secrets:"
  echo "     hq secrets exec --company spice --only SHARED/GOOGLE_SHEETS_WRITER --only SHARED/NOTION_SPICY -- ./run_local.sh $CLIENT"
  echo "   or put the key file at: $KEY"
  echo "   Setup is in RUNBOOK.md."
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
