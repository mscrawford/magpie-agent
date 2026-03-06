#!/bin/bash

# validate_consistency.sh
# Validates documentation consistency across the magpie-agent ecosystem

set -e

# Color codes
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
WARNINGS=0
ERRORS=0

# Report file
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="validation_report_${TIMESTAMP}.txt"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_DIR="$(dirname "$SCRIPT_DIR")"

# Functions
print_header() {
    echo -e "${BLUE}=== MAgPIE Documentation Consistency Validation ===${NC}"
    echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
}

log() {
    echo "$1" | tee -a "$REPORT_FILE"
}

log_color() {
    echo -e "$1"
    echo "$2" >> "$REPORT_FILE"
}

check_pass() {
    ((TOTAL_CHECKS++))
    ((PASSED_CHECKS++))
    log_color "${GREEN}✓${NC} $1" "✓ $1"
}

check_warning() {
    ((TOTAL_CHECKS++))
    ((WARNINGS++))
    log_color "${YELLOW}⚠️  $1${NC}" "⚠️  $1"
}

check_error() {
    ((TOTAL_CHECKS++))
    ((ERRORS++))
    log_color "${RED}❌ $1${NC}" "❌ $1"
}

print_section() {
    echo ""
    log_color "${BLUE}[$1] $2${NC}" "[$1] $2"
}

# Start report
echo "MAgPIE Documentation Consistency Validation" > "$REPORT_FILE"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')" >> "$REPORT_FILE"
echo "Location: $AGENT_DIR" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Print header
print_header

# Change to agent directory
cd "$AGENT_DIR"

# ===========================
# Check 1: Dependency Counts
# ===========================
print_section "1/17" "Checking dependency counts..."

# Check Module 10
MODULE_10_REFS=$(grep -r "Module 10.*dependents\|10.*dependents" \
    modules/module_10.md \
    modules/module_10_notes.md \
    core_docs/Module_Dependencies.md \
    cross_module/modification_safety_guide.md \
    2>/dev/null | grep -oE "[0-9]+ dependent" | grep -oE "[0-9]+" | sort -u)

COUNT_10=$(echo "$MODULE_10_REFS" | wc -l | tr -d ' ')
if [ "$COUNT_10" -eq 1 ]; then
    check_pass "Module 10: $(echo $MODULE_10_REFS) dependents (consistent across 4 files)"
elif [ "$COUNT_10" -eq 0 ]; then
    check_warning "Module 10: No dependency count found in expected files"
else
    check_warning "Module 10: Inconsistent counts found: $(echo $MODULE_10_REFS | tr '\n' ' ')"
    log "    → Check: modules/module_10.md, modules/module_10_notes.md, Module_Dependencies.md, modification_safety_guide.md"
fi

# Check Module 11
MODULE_11_REFS=$(grep -r "Module 11.*dependents\|11.*dependents" \
    modules/module_11.md \
    core_docs/Module_Dependencies.md \
    2>/dev/null | grep -oE "[0-9]+ dependent" | grep -oE "[0-9]+" | sort -u)

COUNT_11=$(echo "$MODULE_11_REFS" | wc -l | tr -d ' ')
if [ "$COUNT_11" -eq 1 ]; then
    check_pass "Module 11: $(echo $MODULE_11_REFS) dependents (consistent)"
elif [ "$COUNT_11" -eq 0 ]; then
    check_pass "Module 11: No explicit count mentioned (acceptable)"
else
    check_warning "Module 11: Inconsistent counts found: $(echo $MODULE_11_REFS | tr '\n' ' ')"
fi

# Check Module 17
MODULE_17_REFS=$(grep -r "Module 17.*dependents\|17.*dependents" \
    modules/module_17.md \
    core_docs/Module_Dependencies.md \
    cross_module/modification_safety_guide.md \
    2>/dev/null | grep -oE "[0-9]+ dependent" | grep -oE "[0-9]+" | sort -u)

COUNT_17=$(echo "$MODULE_17_REFS" | wc -l | tr -d ' ')
if [ "$COUNT_17" -eq 1 ]; then
    check_pass "Module 17: $(echo $MODULE_17_REFS) dependents (consistent)"
elif [ "$COUNT_17" -eq 0 ]; then
    check_pass "Module 17: No explicit count mentioned (acceptable)"
else
    check_warning "Module 17: Inconsistent counts found: $(echo $MODULE_17_REFS | tr '\n' ' ')"
fi

# =====================================
# Check 2: Equation Parameter Counts
# =====================================
print_section "2/17" "Checking equation parameters..."

# Chapman-Richards parameters
CR_PARAMS=$(grep -r "Chapman-Richards\|Chapman Richards" \
    modules/module_52.md \
    modules/module_52_notes.md \
    cross_module/carbon_balance_conservation.md \
    2>/dev/null | grep -i "parameter" | grep -oE "[0-9]+ parameter" | grep -oE "[0-9]+" | sort -u)

COUNT_CR=$(echo "$CR_PARAMS" | wc -l | tr -d ' ')
if [ "$COUNT_CR" -eq 1 ]; then
    check_pass "Chapman-Richards: $(echo $CR_PARAMS) parameters (consistent)"
elif [ "$COUNT_CR" -eq 0 ]; then
    check_pass "Chapman-Richards: No explicit parameter count (acceptable)"
else
    check_warning "Chapman-Richards: Inconsistent parameter counts: $(echo $CR_PARAMS | tr '\n' ' ')"
    log "    → Check: module_52.md, module_52_notes.md, carbon_balance_conservation.md"
fi

# Land balance equation
if grep -q "q10_land" modules/module_10.md && \
   grep -q "q10_land" cross_module/land_balance_conservation.md; then
    check_pass "Land balance: q10_land_area referenced consistently"
else
    check_warning "Land balance: q10_land_area references may be inconsistent"
fi

# Water allocation sectors
WATER_SECTORS_42=$(grep -i "sector" modules/module_42.md 2>/dev/null | grep -oE "[0-9]+ sector" | grep -oE "[0-9]+" | sort -u | head -1)
WATER_SECTORS_BALANCE=$(grep -i "sector" cross_module/water_balance_conservation.md 2>/dev/null | grep -oE "[0-9]+ sector" | grep -oE "[0-9]+" | sort -u | head -1)

if [ -n "$WATER_SECTORS_42" ] && [ -n "$WATER_SECTORS_BALANCE" ]; then
    if [ "$WATER_SECTORS_42" = "$WATER_SECTORS_BALANCE" ]; then
        check_pass "Water sectors: $WATER_SECTORS_42 sectors (consistent)"
    else
        check_warning "Water sectors: module_42.md says $WATER_SECTORS_42, water_balance says $WATER_SECTORS_BALANCE"
    fi
else
    check_pass "Water sectors: No explicit count to validate"
fi

# ============================
# Check 3: Cross-References
# ============================
print_section "3/17" "Checking cross-references..."

# Extract module references (pattern: module_XX.md)
MODULE_REFS=$(grep -r "module_[0-9][0-9]\.md\|module_[0-9][0-9]_notes\.md" \
    AGENT.md \
    core_docs/*.md \
    cross_module/*.md \
    2>/dev/null | grep -oE "module_[0-9][0-9](_notes)?\.md" | sort -u)

BROKEN_REFS=0
VALID_REFS=0

for ref in $MODULE_REFS; do
    if [ -f "modules/$ref" ]; then
        ((VALID_REFS++))
    else
        ((BROKEN_REFS++))
        check_error "Broken reference: $ref referenced but doesn't exist"
        # Find where it's referenced
        REFS_IN=$(grep -l "$ref" AGENT.md core_docs/*.md cross_module/*.md 2>/dev/null | tr '\n' ' ')
        log "    → Referenced in: $REFS_IN"
    fi
done

if [ $BROKEN_REFS -eq 0 ]; then
    check_pass "All $VALID_REFS module references valid"
fi

# Check Phase document references (architecture docs in core_docs/)
PHASE_REFS_CORE=$(grep -r "Phase[123]_[A-Za-z_]+\.md" AGENT.md modules/*.md 2>/dev/null | \
    grep -oE "Phase[123]_[A-Za-z_]+\.md" | sort -u)

BROKEN_PHASE_REFS=0
VALID_PHASE_REFS=0

for ref in $PHASE_REFS_CORE; do
    if [ -f "core_docs/$ref" ]; then
        ((VALID_PHASE_REFS++))
    else
        ((BROKEN_PHASE_REFS++))
        check_error "Broken reference: $ref referenced but doesn't exist in core_docs/"
    fi
done

# Check GAMS reference documents (in reference/ directory)
GAMS_REFS=$(grep -r "GAMS_Phase[0-9]" AGENT.md modules/*.md 2>/dev/null | \
    grep -oE "GAMS_Phase[0-9]_[A-Za-z_]+\.md" | sort -u)

BROKEN_GAMS_REFS=0
VALID_GAMS_REFS=0

for ref in $GAMS_REFS; do
    if [ -f "reference/$ref" ]; then
        ((VALID_GAMS_REFS++))
    else
        ((BROKEN_GAMS_REFS++))
        check_error "Broken reference: $ref referenced but doesn't exist in reference/"
    fi
done

if [ $BROKEN_PHASE_REFS -eq 0 ] && [ $BROKEN_GAMS_REFS -eq 0 ]; then
    TOTAL_PHASE_REFS=$((VALID_PHASE_REFS + VALID_GAMS_REFS))
    check_pass "All $TOTAL_PHASE_REFS Phase/GAMS document references valid"
fi

# ===============================
# Check 4: Duplicate Equations
# ===============================
print_section "4/17" "Checking duplicate equations..."

# Check for common equations mentioned in multiple places
# q70_feed
Q70_LOCATIONS=$(grep -l "q70_feed" modules/module_70.md core_docs/*.md 2>/dev/null | wc -l | tr -d ' ')
if [ "$Q70_LOCATIONS" -gt 0 ]; then
    check_pass "q70_feed: Found in $Q70_LOCATIONS files (cross-references expected)"
fi

# q52_carbon_growth / Chapman-Richards
Q52_LOCATIONS=$(grep -l "q52_carbon\|Chapman-Richards" modules/module_52.md cross_module/carbon_balance_conservation.md 2>/dev/null | wc -l | tr -d ' ')
if [ "$Q52_LOCATIONS" -eq 2 ]; then
    check_pass "Carbon growth equation: Referenced in module_52.md and carbon_balance (expected)"
else
    check_pass "Carbon growth equation: Found in $Q52_LOCATIONS files"
fi

# Check for contradictory equation descriptions (manual review needed)
log ""
log "    NOTE: Duplicate equations with different descriptions require manual review"
log "    Common patterns: module_XX.md (detailed) vs. cross_module/*.md (overview)"

# =================================
# Check 5: Entry Point Consistency
# =================================
print_section "5/17" "Checking entry point consistency..."

# README should point to CURRENT_STATE.json for project work
if grep -q "CURRENT_STATE.json" README.md 2>/dev/null; then
    check_pass "README.md points to CURRENT_STATE.json"
else
    check_warning "README.md doesn't reference CURRENT_STATE.json"
fi

# README should point to AGENT.md for AI setup
if grep -q "AGENT.md" README.md 2>/dev/null; then
    check_pass "README.md points to AGENT.md"
else
    check_warning "README.md doesn't reference AGENT.md"
fi

# AGENT.md should have command system
if grep -q "COMMAND SYSTEM" AGENT.md 2>/dev/null || grep -q "/guide" AGENT.md 2>/dev/null; then
    check_pass "AGENT.md has command system"
else
    check_warning "AGENT.md may not have command system"
fi

# AGENT.md should reference sync tracking
if grep -q "sync_log.json" AGENT.md 2>/dev/null || grep -q "sync" AGENT.md 2>/dev/null; then
    check_pass "AGENT.md references sync tracking"
else
    check_warning "AGENT.md may not reference sync tracking"
fi

# project/sync_log.json should exist
if [ -f "project/sync_log.json" ]; then
    check_pass "project/sync_log.json exists"
else
    check_error "project/sync_log.json missing (run sync command)"
fi

# =======================
# Check 6: File Counts
# =======================
print_section "6/17" "Checking file counts..."

# Count module docs
MODULE_COUNT=$(ls -1 modules/module_*.md 2>/dev/null | grep -v "_notes" | wc -l | tr -d ' ')
if [ "$MODULE_COUNT" -eq 46 ]; then
    check_pass "Module docs: $MODULE_COUNT files (matches expected 46)"
else
    check_warning "Module docs: $MODULE_COUNT files (expected 46)"
fi

# Count notes files
NOTES_COUNT=$(ls -1 modules/module_*_notes.md 2>/dev/null | wc -l | tr -d ' ')
check_pass "Notes files: $NOTES_COUNT files"

# Count cross-module docs
CROSS_COUNT=$(ls -1 cross_module/*.md 2>/dev/null | grep -v "README" | wc -l | tr -d ' ')
if [ "$CROSS_COUNT" -ge 6 ]; then
    check_pass "Cross-module: $CROSS_COUNT files (expected 6+)"
else
    check_warning "Cross-module: $CROSS_COUNT files (expected 6)"
fi

# Count feedback integrated
FEEDBACK_COUNT=$(ls -1 feedback/integrated/*.md 2>/dev/null | wc -l | tr -d ' ')
check_pass "Feedback integrated: $FEEDBACK_COUNT files"

# Count GAMS reference docs
GAMS_COUNT=$(ls -1 reference/GAMS_Phase*.md 2>/dev/null | wc -l | tr -d ' ')
if [ "$GAMS_COUNT" -eq 6 ]; then
    check_pass "GAMS reference: $GAMS_COUNT files (matches expected 6)"
else
    check_warning "GAMS reference: $GAMS_COUNT files (expected 6)"
fi

# ==========================================
# Check 7: Convention Linter (stale formats)
# ==========================================
print_section "7/17" "Checking naming conventions..."

# Scan for stale "command: X" format in active files (excluding trigger descriptions and archives)
STALE_CMD_COUNT=0
while IFS= read -r file; do
    # Skip archived/historical files and this script's own source
    case "$file" in
        ./feedback/integrated/*|./feedback/archive/*|./reference/archive/*) continue ;;
        ./scripts/validate_consistency.sh) continue ;; # self-references are check logic, not stale format
    esac
    # Count "command: X" outside of "When user says" lines and "Unknown command:" patterns
    HITS=$(grep -c "command:" "$file" 2>/dev/null | tr -d ' ')
    SAFE=$(grep -c "When user says\|Unknown command:\|the command:\|COMMAND SYSTEM\|# Command\|e.g., .command:.\|renamed .e.g" "$file" 2>/dev/null | tr -d ' ')
    # In AGENT.md, "run command:" in trigger descriptions is intentional
    if [ "$(basename "$file")" = "AGENT.md" ]; then
        SAFE=$((SAFE + $(grep -c '"run command:' "$file" 2>/dev/null | tr -d ' ')))
    fi
    BAD=$((HITS - SAFE))
    if [ "$BAD" -gt 0 ]; then
        STALE_CMD_COUNT=$((STALE_CMD_COUNT + BAD))
        log "    ⚠️  $file: ~$BAD possible stale 'command:' refs"
    fi
done < <(find . -name "*.md" -not -path "./.git/*" -not -path "./feedback/integrated/*" -not -path "./feedback/archive/*" -not -path "./reference/archive/*" 2>/dev/null)

# Also check shell scripts (excluding this script itself)
while IFS= read -r file; do
    [ "$file" = "./scripts/validate_consistency.sh" ] && continue
    HITS=$(grep -c "command:" "$file" 2>/dev/null | tr -d ' ')
    SAFE=$(grep -c "Unknown command:" "$file" 2>/dev/null | tr -d ' ')
    BAD=$((HITS - SAFE))
    if [ "$BAD" -gt 0 ]; then
        STALE_CMD_COUNT=$((STALE_CMD_COUNT + BAD))
        log "    ⚠️  $file: ~$BAD possible stale 'command:' refs"
    fi
done < <(find . -name "*.sh" -not -path "./.git/*" 2>/dev/null)

if [ "$STALE_CMD_COUNT" -eq 0 ]; then
    check_pass "No stale 'command:' format references found"
else
    check_warning "Found ~$STALE_CMD_COUNT possible stale 'command:' refs (review above)"
fi

# Check for CLAUDE.md references in active files (should be AGENT.md)
CLAUDE_REFS=$(grep -rl "CLAUDE\.md" --include="*.md" --include="*.sh" . 2>/dev/null \
    | grep -v ".git" \
    | grep -v "feedback/integrated/" \
    | grep -v "feedback/archive/" \
    | grep -v "reference/archive/" \
    | grep -v "feedback/global/agent_lessons.md" \
    | grep -v "scripts/validate_consistency.sh" \
    | grep -v "agent/commands/validate.md" \
    || true)

if [ -z "$CLAUDE_REFS" ]; then
    check_pass "No stale CLAUDE.md references (all use AGENT.md)"
else
    CLAUDE_COUNT=$(echo "$CLAUDE_REFS" | wc -l | tr -d ' ')
    check_warning "$CLAUDE_COUNT files still reference CLAUDE.md (should be AGENT.md)"
    for ref in $CLAUDE_REFS; do
        log "    ⚠️  $ref"
    done
fi

# ==============================================
# Check 8: Markdown Link Validator (key files)
# ==============================================
print_section "8/17" "Checking markdown link targets..."

BROKEN_LINKS=0

# Check helpers for broken relative links
for helper in agent/helpers/*.md; do
    [ -f "$helper" ] || continue
    HELPER_DIR=$(dirname "$helper")
    # Extract markdown links: [text](path) — skip URLs and anchors
    while IFS= read -r link_target; do
        # Skip URLs, anchors, and empty
        case "$link_target" in
            http*|mailto*|\#*|"") continue ;;
        esac
        # Strip any anchor from path
        CLEAN_PATH=$(echo "$link_target" | sed 's/#.*//')
        [ -z "$CLEAN_PATH" ] && continue
        # Resolve relative to helper's directory
        RESOLVED="$HELPER_DIR/$CLEAN_PATH"
        if [ ! -e "$RESOLVED" ]; then
            BROKEN_LINKS=$((BROKEN_LINKS + 1))
            log "    ❌ $(basename "$helper"): broken link → $link_target (resolves to $RESOLVED)"
        fi
    done < <(grep -oE '\[([^]]*)\]\(([^)]+)\)' "$helper" 2>/dev/null | sed 's/.*](//' | sed 's/)//')
done

# Check key docs for broken relative links
for doc in AGENT.md README.md core_docs/*.md; do
    [ -f "$doc" ] || continue
    DOC_DIR=$(dirname "$doc")
    while IFS= read -r link_target; do
        case "$link_target" in
            http*|mailto*|\#*|"") continue ;;
        esac
        CLEAN_PATH=$(echo "$link_target" | sed 's/#.*//')
        [ -z "$CLEAN_PATH" ] && continue
        RESOLVED="$DOC_DIR/$CLEAN_PATH"
        if [ ! -e "$RESOLVED" ]; then
            BROKEN_LINKS=$((BROKEN_LINKS + 1))
            log "    ❌ $(basename "$doc"): broken link → $link_target"
        fi
    done < <(grep -oE '\[([^]]*)\]\(([^)]+)\)' "$doc" 2>/dev/null | sed 's/.*](//' | sed 's/)//')
done

if [ "$BROKEN_LINKS" -eq 0 ]; then
    check_pass "All markdown link targets exist"
else
    check_error "$BROKEN_LINKS broken markdown links found (see above)"
fi

# ==============================================
# Check 9: Trigger Keyword Sync
# ==============================================
print_section "9/17" "Checking helper trigger keyword sync..."

TRIGGER_ISSUES=0

# For each keyword-triggered helper, check it appears in AGENT.md routing table
# AND that keywords match between AGENT.md and the helper's Auto-load triggers
for helper in agent/helpers/*.md; do
    [ -f "$helper" ] || continue
    BASENAME=$(basename "$helper")
    # Skip non-keyword helpers
    case "$BASENAME" in
        session_startup.md|README.md) continue ;;
    esac
    # Check if helper is referenced in AGENT.md auto-load table
    if ! grep -q "$BASENAME" AGENT.md 2>/dev/null; then
        TRIGGER_ISSUES=$((TRIGGER_ISSUES + 1))
        log "    ❌ $BASENAME not found in AGENT.md routing table"
        continue
    fi
    # Check if helper has Auto-load triggers line
    if ! grep -q "Auto-load triggers" "$helper" 2>/dev/null; then
        TRIGGER_ISSUES=$((TRIGGER_ISSUES + 1))
        log "    ⚠️  $BASENAME missing Auto-load triggers declaration"
        continue
    fi
    # Compare keyword sets between AGENT.md and helper
    AGENT_KEYWORDS=$(grep "$BASENAME" AGENT.md | grep -oE '"[^"]*"' | sort)
    HELPER_KEYWORDS=$(grep "Auto-load triggers" "$helper" | grep -oE '"[^"]*"' | sort)
    if [ "$AGENT_KEYWORDS" != "$HELPER_KEYWORDS" ]; then
        TRIGGER_ISSUES=$((TRIGGER_ISSUES + 1))
        # Find which keywords differ
        ONLY_AGENT=$(comm -23 <(echo "$AGENT_KEYWORDS") <(echo "$HELPER_KEYWORDS") | tr '\n' ' ')
        ONLY_HELPER=$(comm -13 <(echo "$AGENT_KEYWORDS") <(echo "$HELPER_KEYWORDS") | tr '\n' ' ')
        log "    ⚠️  $BASENAME keyword mismatch:"
        [ -n "$ONLY_AGENT" ] && log "        Only in AGENT.md: $ONLY_AGENT"
        [ -n "$ONLY_HELPER" ] && log "        Only in helper:   $ONLY_HELPER"
    fi
done

if [ "$TRIGGER_ISSUES" -eq 0 ]; then
    check_pass "All helpers registered in AGENT.md with matching trigger keywords"
else
    check_warning "$TRIGGER_ISSUES trigger sync issues found (see above)"
fi

# =============================================
# Check 10: AGENT.md Deployment Freshness
# =============================================
print_section "10/17" "Checking AGENT.md deployment..."

if [ -f "../AGENT.md" ]; then
    if diff -q AGENT.md ../AGENT.md > /dev/null 2>&1; then
        check_pass "AGENT.md deployed copy is in sync"
    else
        check_error "AGENT.md differs from ../AGENT.md — run: cp AGENT.md ../AGENT.md"
    fi
else
    check_warning "../AGENT.md not found (deploy with: cp AGENT.md ../AGENT.md)"
fi

# =============================================
# Check 11: Anti-Hardcoding Guard
# =============================================
print_section "11/17" "Checking for hardcoded values in mechanism files..."

HARDCODED_ISSUES=0

# Check for 40-char hex strings (commit hashes) in mechanism files
for mech in agent/helpers/session_startup.md agent/commands/*.md AGENT.md; do
    [ -f "$mech" ] || continue
    # Find 40-char hex strings that look like commit hashes (not in comments about the check itself)
    HASH_HITS=$(grep -oE '[0-9a-f]{40}' "$mech" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$HASH_HITS" -gt 0 ]; then
        HARDCODED_ISSUES=$((HARDCODED_ISSUES + 1))
        log "    ⚠️  $(basename "$mech"): $HASH_HITS hardcoded commit hash(es)"
    fi
    # Also check for 7-10 char abbreviated hashes that might be hardcoded
    # (only flag if they appear in non-example contexts — this is heuristic)
done

if [ "$HARDCODED_ISSUES" -eq 0 ]; then
    check_pass "No hardcoded commit hashes in mechanism files"
else
    check_warning "$HARDCODED_ISSUES files contain hardcoded commit hashes (may become stale)"
fi

# ================================================
# Check 12: Path prefix check (magpie-agent/)
# ================================================
print_section "12/17" "Checking for stale path prefixes..."

# Files inside magpie-agent/ should not use magpie-agent/ as a path prefix
# (since the working directory IS magpie-agent/, this creates double-nesting)
PREFIX_ISSUES=0
# Exclude: README.md/AGENT.md (may mention it in prose), Tool_Usage_Patterns (teaching examples),
# archive dirs, feedback/integrated (historical records), session_startup.md (handles both dirs)
PREFIX_HITS=$(grep -rn 'magpie-agent/' --include="*.md" . 2>/dev/null | \
    grep -v ".git" | \
    grep -v "archive/" | \
    grep -v "README.md\|AGENT.md\|Tool_Usage_Patterns\|session_startup.md" | \
    grep -v "github\|http\|repo\|git@\|clone\|remote" | \
    grep -v "feedback/integrated/" | \
    grep -v "# From magpie-agent\|in magpie-agent\|is magpie-agent\|or magpie-agent\|the magpie-agent" | \
    grep '`[^`]*magpie-agent/[^`]*`' || true)

if [ -n "$PREFIX_HITS" ]; then
    PREFIX_ISSUES=$(echo "$PREFIX_HITS" | wc -l | tr -d ' ')
    check_error "$PREFIX_ISSUES backtick-quoted paths use stale 'magpie-agent/' prefix"
    echo "$PREFIX_HITS" | head -5 | while IFS= read -r line; do
        log "    → $line"
    done
else
    check_pass "No stale magpie-agent/ path prefixes in backtick-quoted paths"
fi

# ================================================
# Check 13: Unclosed code blocks
# ================================================
print_section "13/17" "Checking for unclosed code blocks..."

UNCLOSED=0
for f in $(find . -name "*.md" -not -path "./.git/*" -not -path "./reference/archive/*" -not -path "./feedback/archive/*"); do
    fences=$(grep -c '```' "$f" 2>/dev/null || true)
    fences=${fences:-0}
    fences=$(echo "$fences" | tr -d '[:space:]')
    if [ $((fences % 2)) -ne 0 ]; then
        UNCLOSED=$((UNCLOSED + 1))
        check_error "Unclosed code block in $f ($fences fence markers)"
    fi
done

if [ "$UNCLOSED" -eq 0 ]; then
    check_pass "All code blocks properly closed"
fi

# Check 14: GAMS Variable Name Verification
# ==========================================
print_section "14/17" "Checking GAMS variable names in docs..."

GAMS_CHECK_SCRIPT="$AGENT_DIR/scripts/check_gams_variables.sh"
if [ -x "$GAMS_CHECK_SCRIPT" ]; then
    GAMS_OUTPUT=$("$GAMS_CHECK_SCRIPT" --summary-only 2>&1)
    GAMS_EXIT=$?
    if [ $GAMS_EXIT -eq 0 ]; then
        ACCURACY=$(echo "$GAMS_OUTPUT" | grep "Accuracy:" | head -1)
        check_pass "GAMS variable names verified: $ACCURACY"
    else
        MISMATCH_COUNT=$(echo "$GAMS_OUTPUT" | grep -oE "Found [0-9]+ variable" | grep -oE "[0-9]+")
        check_error "GAMS variable name mismatches: $MISMATCH_COUNT variables in docs not found in code"
        echo "$GAMS_OUTPUT" | grep "^  " | while read -r line; do
            log "    $line"
        done
    fi
else
    check_warning "GAMS variable checker not found or not executable: $GAMS_CHECK_SCRIPT"
fi

# Check 15: GAMS Equation Name Verification
# ==========================================
print_section "15/17" "Checking GAMS equation names in docs..."

EQ_CHECK_SCRIPT="$AGENT_DIR/scripts/check_gams_equations.sh"
if [ -x "$EQ_CHECK_SCRIPT" ]; then
    EQ_OUTPUT=$("$EQ_CHECK_SCRIPT" 2>&1)
    EQ_EXIT=$?
    if [ $EQ_EXIT -eq 0 ]; then
        EQ_ACCURACY=$(echo "$EQ_OUTPUT" | grep "Accuracy:" | head -1)
        check_pass "GAMS equation names verified: $EQ_ACCURACY"
    else
        EQ_MISMATCH_COUNT=$(echo "$EQ_OUTPUT" | grep -oE "[0-9]+ mismatches" | grep -oE "[0-9]+")
        check_error "GAMS equation name mismatches: $EQ_MISMATCH_COUNT equations in docs not found in code"
        echo "$EQ_OUTPUT" | grep "^  " | while read -r line; do
            log "    $line"
        done
    fi
else
    check_warning "GAMS equation checker not found or not executable: $EQ_CHECK_SCRIPT"
fi

# Check 16: GAMS Realization Name Verification
# =============================================
print_section "16/17" "Checking GAMS realization names in docs..."

REAL_CHECK_SCRIPT="$AGENT_DIR/scripts/check_gams_realizations.sh"
if [ -x "$REAL_CHECK_SCRIPT" ]; then
    REAL_OUTPUT=$("$REAL_CHECK_SCRIPT" 2>&1)
    REAL_EXIT=$?
    if [ $REAL_EXIT -eq 0 ]; then
        REAL_ACCURACY=$(echo "$REAL_OUTPUT" | grep "Accuracy:" | head -1)
        check_pass "GAMS realization names verified: $REAL_ACCURACY"
    else
        REAL_MISMATCH_COUNT=$(echo "$REAL_OUTPUT" | grep -oE "[0-9]+ mismatches" | grep -oE "[0-9]+")
        check_error "GAMS realization name mismatches: $REAL_MISMATCH_COUNT names in docs not found as directories"
        echo "$REAL_OUTPUT" | grep "^  " | while read -r line; do
            log "    $line"
        done
    fi
else
    check_warning "GAMS realization checker not found or not executable: $REAL_CHECK_SCRIPT"
fi

# Check 17: File:Line Citation Verification
# ==========================================
print_section "17/17" "Checking file:line citations in docs..."

CIT_CHECK_SCRIPT="$AGENT_DIR/scripts/check_gams_citations.sh"
if [ -x "$CIT_CHECK_SCRIPT" ]; then
    CIT_OUTPUT=$("$CIT_CHECK_SCRIPT" 2>&1)
    CIT_EXIT=$?
    if [ $CIT_EXIT -eq 0 ]; then
        CIT_ACCURACY=$(echo "$CIT_OUTPUT" | grep "verified:" | head -1)
        check_pass "File:line citations verified: $CIT_ACCURACY"
    else
        CIT_ISSUE_COUNT=$(echo "$CIT_OUTPUT" | grep -oE "[0-9]+ issues" | grep -oE "[0-9]+")
        check_error "File:line citation issues: $CIT_ISSUE_COUNT problems (missing files or out-of-range lines)"
        echo "$CIT_OUTPUT" | grep "^  " | head -10 | while read -r line; do
            log "    $line"
        done
    fi
else
    check_warning "File:line citation checker not found or not executable: $CIT_CHECK_SCRIPT"
fi

# ============
# Summary
# ============
echo ""
log_color "${BLUE}=== Summary ===${NC}" "=== Summary ==="
log "Total checks: $TOTAL_CHECKS"
log_color "${GREEN}✓ Passed: $PASSED_CHECKS${NC}" "✓ Passed: $PASSED_CHECKS"

if [ $WARNINGS -gt 0 ]; then
    log_color "${YELLOW}⚠️  Warnings: $WARNINGS (should review)${NC}" "⚠️  Warnings: $WARNINGS (should review)"
fi

if [ $ERRORS -gt 0 ]; then
    log_color "${RED}❌ Errors: $ERRORS (must fix)${NC}" "❌ Errors: $ERRORS (must fix)"
fi

echo ""
log_color "${BLUE}Detailed report saved to: $REPORT_FILE${NC}" "Detailed report saved to: $REPORT_FILE"

# Recommendations
if [ $ERRORS -gt 0 ] || [ $WARNINGS -gt 0 ]; then
    echo ""
    log "=== Recommendations ==="
    log ""
    log "Document Precedence Hierarchy (for fixing conflicts):"
    log "1. Code truth (actual GAMS files)"
    log "2. Module docs (modules/module_XX.md)"
    log "3. Cross-module (cross_module/*.md)"
    log "4. Architecture (core_docs/*.md)"
    log "5. Notes (modules/module_XX_notes.md)"
    log ""
    log "Fix errors first, then review warnings to determine if action needed."
    log "See AGENT.md and core_docs/Response_Guidelines.md for authoritative sources."
fi

# Exit code
if [ $ERRORS -gt 0 ]; then
    exit 1
else
    exit 0
fi
