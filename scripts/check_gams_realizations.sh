#!/usr/bin/env bash
# check_gams_realizations.sh — Verify realization name references in AI docs against GAMS directories
#
# Checks that realization names (word_monthYY patterns) in module docs match actual
# realization directories in the GAMS codebase.
# Maintains an allowlist for intentionally historical/comparative references.
#
# Usage: ./scripts/check_gams_realizations.sh [magpie_root]
# Exit: 0 = all verified, 1 = mismatches found

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AGENT_DIR="$(dirname "$SCRIPT_DIR")"
MAGPIE_ROOT="${1:-$(dirname "$AGENT_DIR")}"

if [ ! -d "$MAGPIE_ROOT/modules" ]; then
    echo "ERROR: MAgPIE modules not found at $MAGPIE_ROOT/modules"
    exit 1
fi

# Build index of all actual realization directory names
REAL_DIRS=$(find "$MAGPIE_ROOT/modules" -mindepth 2 -maxdepth 2 -type d \
    ! -name input ! -name '.git' \
    -exec basename {} \; | sort -u)

# Realization names that legitimately refer to old/removed realizations
# (e.g., in comparison text, historical notes, or warnings)
ALLOWLIST="anthropometrics_jan18 substitution_dec18 price_jan20 fbask_jan16"

# Extract realization-pattern names from AI docs
# Pattern: word(s)_monthYY (e.g., endo_apr13, sticky_feb18, pot_forest_may24)
DOC_REFS=$(rg -oN '\b[a-z][a-z_]+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\d{2}\b' \
    "$AGENT_DIR/modules/" 2>/dev/null || true)

# Deduplicate to unique (file:realization) pairs
UNIQUE_REFS=$(echo "$DOC_REFS" | sort -u)

TOTAL=0
VERIFIED=0
MISMATCHES=0
MISMATCH_DETAILS=""

while IFS= read -r line; do
    [ -z "$line" ] && continue
    real_name=$(echo "$line" | sed 's/.*://')
    doc_file=$(echo "$line" | sed 's/:.*//')

    TOTAL=$((TOTAL + 1))

    # Check allowlist
    is_allowed=false
    for allowed in $ALLOWLIST; do
        if [ "$real_name" = "$allowed" ]; then
            is_allowed=true
            break
        fi
    done

    if $is_allowed; then
        VERIFIED=$((VERIFIED + 1))
        continue
    fi

    # Check against actual directories
    if echo "$REAL_DIRS" | grep -qx "$real_name"; then
        VERIFIED=$((VERIFIED + 1))
    else
        MISMATCHES=$((MISMATCHES + 1))
        MISMATCH_DETAILS="${MISMATCH_DETAILS}  ❌ ${real_name} (in ${doc_file})\n"
    fi
done <<< "$UNIQUE_REFS"

if [ "$MISMATCHES" -gt 0 ]; then
    echo "Realization check: ${MISMATCHES} mismatches found"
    echo -e "$MISMATCH_DETAILS"
    exit 1
else
    echo "Realization names verified: Accuracy: 100% (${VERIFIED}/${TOTAL} references)"
    exit 0
fi
