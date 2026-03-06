#!/usr/bin/env bash
# check_gams_citations.sh — Verify file:line citations in AI docs against GAMS code
#
# Checks that file.gms:NN references in module docs point to files that exist
# and have at least NN lines.
#
# Usage: ./scripts/check_gams_citations.sh [magpie_root]
# Exit: 0 = all verified, 1 = issues found

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AGENT_DIR="$(dirname "$SCRIPT_DIR")"
MAGPIE_ROOT="${1:-$(dirname "$AGENT_DIR")}"

if [ ! -d "$MAGPIE_ROOT/modules" ]; then
    echo "ERROR: MAgPIE modules not found at $MAGPIE_ROOT/modules"
    exit 1
fi

python3 "$SCRIPT_DIR/check_gams_citations_impl.py" "$AGENT_DIR" "$MAGPIE_ROOT"
