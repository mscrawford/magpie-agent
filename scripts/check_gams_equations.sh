#!/bin/bash
# check_gams_equations.sh — Verify equation name references in AI docs against GAMS code
#
# Checks that q{N}_* equation names in module docs exist in the GAMS codebase.
# Maintains an allowlist for intentionally hypothetical/conceptual equations.
#
# Usage: ./scripts/check_gams_equations.sh [magpie_root]
# Exit: 0 = all verified, 1 = mismatches found

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AGENT_DIR="$(dirname "$SCRIPT_DIR")"
MAGPIE_ROOT="${1:-$(dirname "$AGENT_DIR")}"

if [ ! -d "$MAGPIE_ROOT/modules" ]; then
    echo "ERROR: MAgPIE modules not found at $MAGPIE_ROOT/modules"
    exit 1
fi

# Hypothetical/conceptual equations explicitly annotated in docs
ALLOWLIST=(
    "q10_deforestation"
    "q10_urban_source"
)

# Build index of all equation names in GAMS code
GAMS_EQUATIONS=$(rg -oN '\bq\d+_[a-zA-Z_]+[a-zA-Z]\b' --no-filename "$MAGPIE_ROOT/modules/" 2>/dev/null | sort -u)
GAMS_COUNT=$(echo "$GAMS_EQUATIONS" | wc -l | tr -d ' ')

# Extract equation references from AI docs
DOC_REFS=$(rg -oN '\bq\d+_[a-zA-Z_]+[a-zA-Z]\b' "$AGENT_DIR/modules/" 2>/dev/null || true)

TOTAL=0
VERIFIED=0
MISMATCHES=0
MISMATCH_DETAILS=""

while IFS= read -r line; do
    [ -z "$line" ] && continue
    eq_name=$(echo "$line" | sed 's/.*://')
    doc_file=$(echo "$line" | sed 's/:.*//')

    TOTAL=$((TOTAL + 1))

    # Check allowlist
    is_allowed=false
    for allowed in "${ALLOWLIST[@]}"; do
        if [ "$eq_name" = "$allowed" ]; then
            is_allowed=true
            break
        fi
    done

    if $is_allowed; then
        VERIFIED=$((VERIFIED + 1))
        continue
    fi

    # Check against GAMS index
    if echo "$GAMS_EQUATIONS" | grep -qx "$eq_name"; then
        VERIFIED=$((VERIFIED + 1))
    else
        MISMATCHES=$((MISMATCHES + 1))
        MISMATCH_DETAILS="${MISMATCH_DETAILS}  ❌ ${eq_name} (in ${doc_file})\n"
    fi
done <<< "$DOC_REFS"

# Deduplicate count (same equation referenced multiple times)
UNIQUE_TOTAL=$(echo "$DOC_REFS" | sed 's/.*://' | sort -u | wc -l | tr -d ' ')
UNIQUE_VERIFIED=$((UNIQUE_TOTAL - MISMATCHES))

if [ "$MISMATCHES" -gt 0 ]; then
    echo "Equation check: ${MISMATCHES} mismatches found"
    echo -e "$MISMATCH_DETAILS"
    exit 1
else
    echo "Equation names verified: Accuracy: 100% (${UNIQUE_VERIFIED}/${UNIQUE_TOTAL} unique equations)"
    exit 0
fi
