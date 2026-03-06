#!/bin/bash
# check_gams_variables.sh
# Validates GAMS variable names in AI documentation against actual GAMS code
#
# Catches: wrong prefixes (vm_ vs v{N}_), invented names, suffix truncation
# Skips: wildcard patterns (vm_cost_*), placeholder patterns (<type>), pseudo-code
#
# Usage: ./check_gams_variables.sh [--summary-only] [--module N]
# Exit: 0 if clean, 1 if mismatches found, 0 if GAMS code not available

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_DIR="$(dirname "$SCRIPT_DIR")"
MAGPIE_DIR="$(dirname "$AGENT_DIR")"

# Check that GAMS code exists
if [ ! -d "$MAGPIE_DIR/modules" ] || [ ! -f "$MAGPIE_DIR/main.gms" ]; then
    echo "⚠️  GAMS codebase not found at $MAGPIE_DIR — skipping variable verification"
    exit 0
fi

SUMMARY_ONLY=false
TARGET_MODULE=""
while [ $# -gt 0 ]; do
    case $1 in
        --summary-only) SUMMARY_ONLY=true; shift ;;
        --module) TARGET_MODULE="$2"; shift 2 ;;
        *) shift ;;
    esac
done

# Step 1: Build GAMS variable index from codebase
GAMS_VARS=$(mktemp)

# Interface variables and parameters
grep -rohE '\b(vm_|pm_|fm_|im_|pcm_|ic_|ov_|oq_)[a-zA-Z0-9_]+[a-zA-Z0-9]' \
    "$MAGPIE_DIR/modules/" "$MAGPIE_DIR/core/" "$MAGPIE_DIR/main.gms" \
    "$MAGPIE_DIR/config/default.cfg" \
    2>/dev/null | sort -u > "$GAMS_VARS"

# Local vars/params (v{N}_, p{N}_, f{N}_, i{N}_, s{N}_)
grep -rohE '\b[vpfis][0-9]+_[a-zA-Z0-9_]+[a-zA-Z0-9]' \
    "$MAGPIE_DIR/modules/" 2>/dev/null | sort -u >> "$GAMS_VARS"

# Core scalars (s_*)
grep -rohE '\bs_[a-zA-Z0-9_]+[a-zA-Z0-9]' \
    "$MAGPIE_DIR/modules/" "$MAGPIE_DIR/core/" 2>/dev/null | sort -u >> "$GAMS_VARS"

sort -u -o "$GAMS_VARS" "$GAMS_VARS"
TOTAL_GAMS=$(wc -l < "$GAMS_VARS" | tr -d ' ')

# Step 2: Extract and validate variable references from AI docs
MISMATCHES=$(mktemp)
TOTAL_DOC_VARS=0
TOTAL_MISMATCHES=0
MODULES_CHECKED=0

for doc in "$AGENT_DIR"/modules/module_*.md; do
    [ -f "$doc" ] || continue
    basename=$(basename "$doc")
    mod_num=$(echo "$basename" | grep -oE '[0-9]+')

    if [ -n "$TARGET_MODULE" ] && [ "$mod_num" != "$TARGET_MODULE" ]; then
        continue
    fi

    # Extract backtick-quoted GAMS variables
    # Matches patterns like `vm_something`, `vm_something(dims)`, `vm_something.l`
    DOC_VARS=$(mktemp)
    grep -oE '`(vm_|pm_|fm_|im_|pcm_|ic_|ov_|oq_|v[0-9]+_|p[0-9]+_|f[0-9]+_|i[0-9]+_|s[0-9]+_|s_)[a-zA-Z0-9_]+[a-zA-Z0-9]' \
        "$doc" 2>/dev/null | sed 's/`//' | sort -u > "$DOC_VARS"

    # Known conceptual pseudo-code variables (annotated in docs, not actual GAMS)
    ALLOWLIST="vm_prod_calibrated vm_prod_initial"

    # Filter out:
    # - Wildcard patterns (ending with _* in surrounding text)
    # - Placeholder patterns containing <type>, _X_, etc.
    # - Allowlisted conceptual variables
    FILTERED_VARS=$(mktemp)
    while IFS= read -r var; do
        # Skip if variable name contains placeholder markers
        if echo "$var" | grep -qE '_X_|_type_'; then
            continue
        fi
        # Skip if this exact var appears in a wildcard context (var_* pattern)
        if grep -qE "\`${var}\*\`|\`${var}_\*\`|${var}_\\\*|${var}\*" "$doc" 2>/dev/null; then
            continue
        fi
        # Skip allowlisted conceptual variables
        skip=false
        for allowed in $ALLOWLIST; do
            if [ "$var" = "$allowed" ]; then skip=true; break; fi
        done
        if $skip; then continue; fi
        echo "$var" >> "$FILTERED_VARS"
    done < "$DOC_VARS"

    count=$(wc -l < "$FILTERED_VARS" | tr -d ' ')
    TOTAL_DOC_VARS=$((TOTAL_DOC_VARS + count))
    MODULES_CHECKED=$((MODULES_CHECKED + 1))

    # Check each doc var against GAMS index
    while IFS= read -r var; do
        if ! grep -qxF "$var" "$GAMS_VARS" 2>/dev/null; then
            echo "$basename:$var" >> "$MISMATCHES"
            TOTAL_MISMATCHES=$((TOTAL_MISMATCHES + 1))
        fi
    done < "$FILTERED_VARS"

    rm -f "$DOC_VARS" "$FILTERED_VARS"
done

# Step 3: Report
echo "GAMS Variable Name Verification"
echo "================================"
echo "GAMS codebase variables: $TOTAL_GAMS"
echo "AI doc variable references: $TOTAL_DOC_VARS (across $MODULES_CHECKED modules)"
echo ""

if [ "$TOTAL_MISMATCHES" -eq 0 ]; then
    echo "✅ All variable references verified against GAMS code"
else
    echo "❌ Found $TOTAL_MISMATCHES variable(s) in docs not found in GAMS code:"
    echo ""
    if [ "$SUMMARY_ONLY" = false ]; then
        sort "$MISMATCHES" | while IFS=: read -r file var; do
            echo "  $file: $var"
        done
    else
        sort "$MISMATCHES" | cut -d: -f1 | uniq -c | sort -rn | while read -r count file; do
            echo "  $file: $count mismatches"
        done
    fi
fi

echo ""
if [ "$TOTAL_DOC_VARS" -gt 0 ]; then
    ACCURACY=$(( (TOTAL_DOC_VARS - TOTAL_MISMATCHES) * 100 / TOTAL_DOC_VARS ))
    echo "Accuracy: ${ACCURACY}% ($((TOTAL_DOC_VARS - TOTAL_MISMATCHES))/$TOTAL_DOC_VARS verified)"
fi

# Common error patterns (educational output)
if [ "$TOTAL_MISMATCHES" -gt 0 ]; then
    echo ""
    echo "Common error patterns:"
    echo "  - Wrong prefix: vm_ vs v{N}_, pm_ vs p{N}_, fm_ vs f{N}_, pm_ vs s{N}_"
    echo "  - Suffix truncation: missing _ac, _iso, _reg suffixes"
    echo "  - Invented names: plausible but non-existent variables (especially in advisory text)"
    echo "  - Conceptual pseudo-code: annotate with '(conceptual, not actual GAMS)'"
fi

# Cleanup
rm -f "$GAMS_VARS" "$MISMATCHES"

if [ "$TOTAL_MISMATCHES" -gt 0 ]; then
    exit 1
else
    exit 0
fi
