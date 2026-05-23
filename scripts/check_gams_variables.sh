#!/bin/bash
# check_gams_variables.sh - thin wrapper around check_gams_variables.py
#
# Historical bash implementation was ~47s wall-clock due to a per-variable
# `grep` loop. Replaced 2026-05-23 by check_gams_variables.py (~0.2s) which
# also tightened a buggy wildcard filter in the bash version that was silently
# skipping any var whose name appeared as the prefix of a longer name with
# `_` suffix (e.g., `vm_cost` skipped because doc had `vm_cost_iso`).
#
# Same CLI: --summary-only, --module N. Same exit codes (0 clean, 1 mismatch).

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/check_gams_variables.py" "$@"
