#!/usr/bin/env bash
#
# One-time environment setup for the client-diagnostics pipeline.
#
# The orchestrator launches each diagnostic-* sub-skill via its own
# `<sub-skill>/.venv/bin/python`. A fresh plugin/repo checkout has no venvs,
# so this script creates them and installs the (small, deterministic) deps.
# Run once per machine after installing the spice-team-skills plugin.
#
# Usage:
#   bash scripts/setup_venvs.sh
#
# Idempotent: re-running just upgrades deps in the existing venvs.
# Requires: python3 (3.10+) on PATH.

set -euo pipefail

# Resolve the skills root = the directory that holds client-diagnostics and the
# diagnostic-* sub-skills as siblings. This script lives at
# <skills_root>/client-diagnostics/scripts/setup_venvs.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLIENT_DIAG_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILLS_ROOT="$(cd "$CLIENT_DIAG_DIR/.." && pwd)"

PYTHON_BIN="${PYTHON_BIN:-python3}"

# The orchestrator itself needs pandas + matplotlib; sub-skills need pandas
# (matplotlib included everywhere for safety — campaigns can render charts).
DEPS=(pandas matplotlib)

# client-diagnostics runs run_diagnostic.py; the 5 sub-skills are dispatched.
TARGETS=(
  "client-diagnostics"
  "diagnostic-topline"
  "diagnostic-menu"
  "diagnostic-ops"
  "diagnostic-campaigns"
  "diagnostic-action-plan"
)

echo "Skills root: $SKILLS_ROOT"
echo "Python:      $($PYTHON_BIN --version 2>&1) ($PYTHON_BIN)"
echo

for name in "${TARGETS[@]}"; do
  dir="$SKILLS_ROOT/$name"
  if [ ! -d "$dir" ]; then
    echo "  SKIP  $name (not found at $dir)"
    continue
  fi
  venv="$dir/.venv"
  if [ ! -d "$venv" ]; then
    echo "  CREATE venv: $name"
    "$PYTHON_BIN" -m venv "$venv"
  else
    echo "  EXISTS venv: $name"
  fi
  "$venv/bin/python" -m pip install --quiet --upgrade pip
  "$venv/bin/python" -m pip install --quiet --upgrade "${DEPS[@]}"
done

echo
echo "Done. Run a diagnostic with:"
echo "  \"$SKILLS_ROOT/client-diagnostics/.venv/bin/python\" \\"
echo "    \"$SKILLS_ROOT/client-diagnostics/scripts/run_diagnostic.py\" \\"
echo "    --client <slug> --inputs-dir <path-to-90d-csvs>"
echo
echo "Tip: to point at a different skills layout (e.g. a local dev copy),"
echo "set SPICE_SKILLS_ROOT=/path/to/Skills before running."
