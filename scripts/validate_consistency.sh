#!/bin/bash

# validate_consistency.sh
# Validates documentation consistency across the magpie-agent ecosystem

# Robustness: deliberately NOT `set -e`.
#
# This validator's job is to probe for ABSENT things — greps that don't match,
# counters that start at zero. Under `set -e` those normal non-zero returns
# abort the whole run. From this file's creation (2025-10-26) until 2026-05-31
# the combination of `set -e` and `((VAR++))`-from-0 silently killed the script
# at the very first check, yet commit messages and project/sync_log.json kept
# recording "NN/NN clean" results that no completed run ever produced.
#
# The fix has two parts:
#   1. Use pipefail but NOT -e/-u, so benign empty greps and zero counters
#      don't abort the run.
#   2. An EXIT trap + completion sentinel (VALIDATOR_COMPLETED). If the script
#      exits for ANY reason before reaching its verdict block, the trap fires
#      LOUDLY and exits 99 (ABORTED) — a state distinct from 0 (PASS) and
#      1 (FAIL). A silent partial run can no longer be mistaken for a pass.
set -o pipefail

VALIDATOR_COMPLETED=0
on_exit() {
    local rc=$?
    if [ "$VALIDATOR_COMPLETED" -ne 1 ]; then
        {
            echo ""
            echo "================================================================"
            echo "FATAL: validate_consistency.sh ABORTED before completion (rc=$rc)."
            echo "This run did NOT reach its verdict block. Results are INVALID and"
            echo "MUST NOT be recorded as a pass. Treat the guard as broken until"
            echo "the abort cause is fixed (re-run with 'bash -x' to locate it)."
            echo "================================================================"
        } >&2
        exit 99
    fi
    # Completed normally: preserve the verdict block's own exit code.
    exit "$rc"
}
trap on_exit EXIT

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

# Get script directory FIRST (so REPORT_DIR can be anchored to agent root,
# not the caller's CWD — historical bug: invoking from parent magpie/ root
# spawned validation_report_*.txt in the upstream MAgPIE repo. Fixed R6 0f-1.)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_DIR="$(dirname "$SCRIPT_DIR")"

# Report file (anchored to AGENT_DIR, independent of caller's CWD)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_DIR="${AGENT_DIR}/.cache/validation_reports"
mkdir -p "$REPORT_DIR"
REPORT_FILE="${REPORT_DIR}/validation_report_${TIMESTAMP}.txt"

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
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
    log_color "${GREEN}✓${NC} $1" "✓ $1"
}

check_warning() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    WARNINGS=$((WARNINGS + 1))
    log_color "${YELLOW}⚠️  $1${NC}" "⚠️  $1"
}

check_error() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    ERRORS=$((ERRORS + 1))
    log_color "${RED}❌ $1${NC}" "❌ $1"
}

# Section labels auto-number from SECTION_NUM; SECTION_TOTAL is the SINGLE place
# the denominator lives (R7: replaced the 28 hardcoded "/28" literals, which had
# no self-check and drifted). The legacy first arg ("N/M") is now ignored.
# R53 (2026-06-28): +2 advisory checks (29 set-member drift, 30 intra-doc default
# contradiction) appended -> 30. Appended, never middle-renumbered (stable IDs).
# 2026-06-29: +1 advisory check (31 role-attribution: declared-in/provider claims vs
# declarations.gms) appended -> 31.
# 2026-07-15: +2 advisory checks (32 attribution-TABLES phantom, 33 attribution-PROSE
# phantom: the CONSUMER/provides-to half of MANDATE 18, deterministic ~0-FNR) -> 33.
SECTION_NUM=0
SECTION_TOTAL=34
print_section() {
    SECTION_NUM=$((SECTION_NUM + 1))
    echo ""
    log_color "${BLUE}[$SECTION_NUM/$SECTION_TOTAL] $2${NC}" "[$SECTION_NUM/$SECTION_TOTAL] $2"
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
print_section "1/28" "Checking dependency counts..."

# R5 2026-05-24: Fixed vacuous-pass bug — `echo "" | wc -l` returns 1, so
# empty grep results were being reported as "1 consistent count" with no
# value. Now an empty grep result correctly maps to count=0 via -z check.
#
# Note: the docs increasingly express dependency counts via dependency tables
# rather than "N dependents" prose, so empty grep is now common. This check
# is best-effort; canonical source is core_docs/Module_Dependencies.md.

# Helper: count unique non-empty lines (treats empty string as 0)
count_lines() {
    if [ -z "$1" ]; then
        echo 0
    else
        printf '%s\n' "$1" | wc -l | tr -d ' '
    fi
}

# Check Module 10
MODULE_10_REFS=$(grep -r "Module 10.*dependents\|10.*dependents" \
    modules/module_10.md \
    modules/module_10_notes.md \
    core_docs/Module_Dependencies.md \
    cross_module/modification_safety_guide.md \
    2>/dev/null | grep -oE "[0-9]+ dependent" | grep -oE "[0-9]+" | sort -u)

COUNT_10=$(count_lines "$MODULE_10_REFS")
if [ "$COUNT_10" -eq 1 ]; then
    check_pass "Module 10: $(echo $MODULE_10_REFS) dependents (consistent across 4 files)"
elif [ "$COUNT_10" -eq 0 ]; then
    check_pass "Module 10: No explicit dependency-count prose found (acceptable — see Module_Dependencies.md tables)"
else
    check_warning "Module 10: Inconsistent counts found: $(echo $MODULE_10_REFS | tr '\n' ' ')"
    log "    → Check: modules/module_10.md, modules/module_10_notes.md, Module_Dependencies.md, modification_safety_guide.md"
fi

# Check Module 11
MODULE_11_REFS=$(grep -r "Module 11.*dependents\|11.*dependents" \
    modules/module_11.md \
    core_docs/Module_Dependencies.md \
    2>/dev/null | grep -oE "[0-9]+ dependent" | grep -oE "[0-9]+" | sort -u)

COUNT_11=$(count_lines "$MODULE_11_REFS")
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

COUNT_17=$(count_lines "$MODULE_17_REFS")
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
print_section "2/28" "Checking equation parameters..."

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
print_section "3/28" "Checking cross-references..."

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
        VALID_REFS=$((VALID_REFS + 1))
    else
        BROKEN_REFS=$((BROKEN_REFS + 1))
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
        VALID_PHASE_REFS=$((VALID_PHASE_REFS + 1))
    else
        BROKEN_PHASE_REFS=$((BROKEN_PHASE_REFS + 1))
        check_error "Broken reference: $ref referenced but doesn't exist in core_docs/"
    fi
done

# Check GAMS reference documents (in reference/ directory)
GAMS_REFS=$(grep -r "GAMS_[A-Z][A-Za-z_]*\.md" AGENT.md modules/*.md 2>/dev/null | \
    grep -oE "GAMS_[A-Za-z_]+\.md" | sort -u)

BROKEN_GAMS_REFS=0
VALID_GAMS_REFS=0

for ref in $GAMS_REFS; do
    if [ -f "reference/$ref" ]; then
        VALID_GAMS_REFS=$((VALID_GAMS_REFS + 1))
    else
        BROKEN_GAMS_REFS=$((BROKEN_GAMS_REFS + 1))
        check_error "Broken reference: $ref referenced but doesn't exist in reference/"
    fi
done

if [ $BROKEN_PHASE_REFS -eq 0 ] && [ $BROKEN_GAMS_REFS -eq 0 ]; then
    TOTAL_PHASE_REFS=$((VALID_PHASE_REFS + VALID_GAMS_REFS))
    check_pass "All $TOTAL_PHASE_REFS GAMS document references valid"
fi

# ===============================
# Check 4: Duplicate Equations
# ===============================
print_section "4/28" "Checking duplicate equations... [RETIRED]"
# RETIRED 2026-06-07 (pipeline-audit R7/R10 finding C5-1): this check only ever
# called check_pass -- no check_warning/check_error path existed -- so it was
# structurally incapable of failing and caught nothing in its lifetime. Kept as
# a numbered tombstone so section auto-numbering and all by-number "Check N"
# references stay stable. Proper removal (stable check IDs) is the deferred fix;
# see audit/BACKLOG.md "Validator check IDs".
log "    (retired: zero-catch by construction; see BACKLOG 'Validator check IDs')"

# =================================
# Check 5: Entry Point Consistency
# =================================
print_section "5/28" "Checking entry point consistency..."

# README should point to the live audit-state files (was CURRENT_STATE.json
# pre-R6; that file was retired and relocated to project/archive/ by R25).
if grep -q "audit/validation_rounds.json" README.md 2>/dev/null; then
    check_pass "README.md points to audit/validation_rounds.json (live state)"
else
    check_warning "README.md doesn't reference audit/validation_rounds.json (live state file)"
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
print_section "6/28" "Checking file counts..."

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
FEEDBACK_COUNT=$(ls -1 audit/integrated/*.md 2>/dev/null | wc -l | tr -d ' ')
check_pass "Feedback integrated: $FEEDBACK_COUNT files"

# Count GAMS reference docs
GAMS_COUNT=$(ls -1 reference/GAMS_*.md 2>/dev/null | wc -l | tr -d ' ')
if [ "$GAMS_COUNT" -eq 6 ]; then
    check_pass "GAMS reference: $GAMS_COUNT files (matches expected 6)"
else
    check_warning "GAMS reference: $GAMS_COUNT files (expected 6)"
fi

# ==========================================
# Check 7: Convention Linter (stale formats)
# ==========================================
print_section "7/28" "Checking naming conventions..."

# Scan for stale "command: X" format in active files (excluding trigger descriptions and archives)
STALE_CMD_COUNT=0
while IFS= read -r file; do
    # Skip archived/historical files, top-level audit/plan artifacts, and this script's own source
    case "$file" in
        ./audit/integrated/*|./audit/archive/*|./reference/archive/*) continue ;;
        ./audit/pipeline_audit_round*.md|./audit/r*_execution_plan.md|./audit/next_session_plan.md|./audit/flywheel_rubric.md|./audit/README.md) continue ;;
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
done < <(find . -name "*.md" -not -path "./.git/*" -not -path "./audit/integrated/*" -not -path "./audit/archive/*" -not -path "./reference/archive/*" 2>/dev/null)

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
# Exclude files that legitimately reference CLAUDE.md as a deployment target
CLAUDE_REFS=$(grep -rl "CLAUDE\.md" --include="*.md" --include="*.sh" . 2>/dev/null \
    | grep -v ".git" \
    | grep -v "audit/integrated/" \
    | grep -v "audit/archive/" \
    | grep -v "audit/pipeline_audit_round" \
    | grep -v "audit/validation_round" \
    | grep -v "audit/r.*_execution_plan" \
    | grep -v "audit/next_session_plan" \
    | grep -v "audit/flywheel_rubric" \
    | grep -v "audit/README.md" \
    | grep -v "reference/archive/" \
    | grep -v "audit/global/agent_lessons.md" \
    | grep -v "scripts/validate_consistency.sh" \
    | grep -v "agent/commands/validate.md" \
    | grep -v "./AGENT.md" \
    | grep -v "core_docs/Bug_Taxonomy.md" \
    | grep -v "agent/commands/bootstrap.md" \
    | grep -v "agent/helpers/session_startup.md" \
    | grep -v "agent/helpers/maintenance_protocol.md" \
    | grep -v "agent/commands/update.md" \
    | grep -v "agent/commands/pipeline-audit.md" \
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
print_section "8/28" "Checking markdown link targets..."

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
print_section "9/28" "Checking helper trigger keyword sync..."

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
print_section "10/28" "Checking AGENT.md deployment..."

DEPLOY_OK=0
DEPLOY_FAIL=0

if [ -f "../AGENT.md" ]; then
    if diff -q AGENT.md ../AGENT.md > /dev/null 2>&1; then
        DEPLOY_OK=$((DEPLOY_OK + 1))
    else
        check_error "AGENT.md differs from ../AGENT.md — run: cp AGENT.md ../AGENT.md"
        DEPLOY_FAIL=$((DEPLOY_FAIL + 1))
    fi
else
    check_warning "../AGENT.md not found (deploy with: cp AGENT.md ../AGENT.md)"
    DEPLOY_FAIL=$((DEPLOY_FAIL + 1))
fi

if [ -f "../CLAUDE.md" ]; then
    if diff -q AGENT.md ../CLAUDE.md > /dev/null 2>&1; then
        DEPLOY_OK=$((DEPLOY_OK + 1))
    else
        check_error "CLAUDE.md differs from AGENT.md — run: cp AGENT.md ../CLAUDE.md (CRITICAL: Claude loads this!)"
        DEPLOY_FAIL=$((DEPLOY_FAIL + 1))
    fi
else
    check_warning "../CLAUDE.md not found (deploy with: cp AGENT.md ../CLAUDE.md)"
    DEPLOY_FAIL=$((DEPLOY_FAIL + 1))
fi

if [ "$DEPLOY_FAIL" -eq 0 ]; then
    check_pass "All deployment copies in sync (AGENT.md + CLAUDE.md)"
fi

# =============================================
# Check 11: Anti-Hardcoding Guard
# =============================================
print_section "11/28" "Checking for hardcoded values in mechanism files..."

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
print_section "12/28" "Checking for stale path prefixes..."

# Files inside magpie-agent/ should not use magpie-agent/ as a path prefix
# (since the working directory IS magpie-agent/, this creates double-nesting)
PREFIX_ISSUES=0
# Exclude: README.md/AGENT.md (may mention it in prose), Tool_Usage_Patterns (teaching examples),
# archive dirs, audit/integrated (historical records), audit/round*_answers/ and audit/round*_audits/
# (immutable captured agent outputs — not authoritative docs), session_startup.md (handles both dirs)
PREFIX_HITS=$(grep -rn 'magpie-agent/' --include="*.md" . 2>/dev/null | \
    grep -v ".git" | \
    grep -v "archive/" | \
    grep -v "README.md\|AGENT.md\|Tool_Usage_Patterns\|session_startup.md" | \
    grep -v "github\|http\|repo\|git@\|clone\|remote" | \
    grep -v "audit/integrated/" | \
    grep -vE 'audit/round[0-9]+_(answers|audits)/' | \
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
print_section "13/28" "Checking for unclosed code blocks..."

UNCLOSED=0
for f in $(find . -name "*.md" -not -path "./.git/*" -not -path "./reference/archive/*" -not -path "./audit/archive/*"); do
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
print_section "14/28" "Checking GAMS variable names in docs..."

GAMS_CHECK_SCRIPT="$AGENT_DIR/scripts/check_gams_variables.py"
if [ -f "$GAMS_CHECK_SCRIPT" ]; then
    if GAMS_OUTPUT=$(python3 "$GAMS_CHECK_SCRIPT" --summary-only 2>&1); then GAMS_EXIT=0; else GAMS_EXIT=$?; fi
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
    # I4: surface typo'd allowlist markers (loose-match passes, strict-match fails).
    # These warnings appear independently of the main check above.
    # `|| true` guards against `set -e` aborting on grep no-match.
    TYPO_COUNT=$(echo "$GAMS_OUTPUT" | grep -oE "Found [0-9]+ likely typo" | grep -oE "[0-9]+" || true)
    if [ -n "$TYPO_COUNT" ] && [ "$TYPO_COUNT" -gt 0 ]; then
        check_warning "Allowlist marker typos: $TYPO_COUNT marker(s) silently failing (see check_gams_variables.py output)"
    fi
else
    check_warning "GAMS variable checker not found or not executable: $GAMS_CHECK_SCRIPT"
fi

# Check 15: GAMS Equation Name Verification
# ==========================================
print_section "15/28" "Checking GAMS equation names in docs..."

# Python implementation (the check_gams_equations.sh twin was removed in R7).
EQ_CHECK_PY="$AGENT_DIR/scripts/check_gams_equations.py"
if [ -f "$EQ_CHECK_PY" ]; then
    if EQ_OUTPUT=$(python3 "$EQ_CHECK_PY" --summary-only 2>&1); then EQ_EXIT=0; else EQ_EXIT=$?; fi
else
    EQ_OUTPUT=""
    EQ_EXIT=127
fi
if [ "$EQ_EXIT" = "127" ]; then
    check_warning "GAMS equation checker not found ($EQ_CHECK_PY)"
elif [ "$EQ_EXIT" -eq 0 ]; then
    EQ_ACCURACY=$(echo "$EQ_OUTPUT" | grep "Accuracy:" | head -1)
    check_pass "GAMS equation names verified: $EQ_ACCURACY"
else
    EQ_MISMATCH_COUNT=$(echo "$EQ_OUTPUT" | grep -oE "[0-9]+ mismatches" | grep -oE "[0-9]+" || true)
    check_error "GAMS equation name mismatches: ${EQ_MISMATCH_COUNT:-?} equations in docs not found in code"
    echo "$EQ_OUTPUT" | grep "^  " | while read -r line; do
        log "    $line"
    done
fi

# Check 16: GAMS Realization Name Verification
# =============================================
print_section "16/28" "Checking GAMS realization names in docs..."

# Python implementation (the check_gams_realizations.sh twin was removed in R7).
# (Note: this is Check 16's "GAMS realization names in docs" check — separate
# from Check 19's check_module_realizations.py which validates header/footer
# alignment against config/default.cfg.)
REAL_CHECK_PY="$AGENT_DIR/scripts/check_gams_realizations.py"
if [ -f "$REAL_CHECK_PY" ]; then
    if REAL_OUTPUT=$(python3 "$REAL_CHECK_PY" --summary-only 2>&1); then REAL_EXIT=0; else REAL_EXIT=$?; fi
else
    REAL_OUTPUT=""
    REAL_EXIT=127
fi
if [ "$REAL_EXIT" = "127" ]; then
    check_warning "GAMS realization checker not found ($REAL_CHECK_PY)"
elif [ "$REAL_EXIT" -eq 0 ]; then
    REAL_ACCURACY=$(echo "$REAL_OUTPUT" | grep "Accuracy:" | head -1)
    check_pass "GAMS realization names verified: $REAL_ACCURACY"
else
    REAL_MISMATCH_COUNT=$(echo "$REAL_OUTPUT" | grep -oE "[0-9]+ mismatches" | grep -oE "[0-9]+" || true)
    check_error "GAMS realization name mismatches: ${REAL_MISMATCH_COUNT:-?} names in docs not found as directories"
    echo "$REAL_OUTPUT" | grep "^  " | while read -r line; do
        log "    $line"
    done
fi

# Check 17: File:Line Citation Verification
# ==========================================
print_section "17/28" "Checking file:line citations in docs..."

CIT_CHECK_SCRIPT="$AGENT_DIR/scripts/check_gams_citations.sh"
if [ -x "$CIT_CHECK_SCRIPT" ]; then
    if CIT_OUTPUT=$("$CIT_CHECK_SCRIPT" 2>&1); then CIT_EXIT=0; else CIT_EXIT=$?; fi
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

# Check 18: Default Realization Cross-Reference
# ==============================================
print_section "18/28" "Checking default realization labels against config/default.cfg..."

DEFAULT_CHECK_SCRIPT="$AGENT_DIR/scripts/check_default_realizations.py"
if [ -f "$DEFAULT_CHECK_SCRIPT" ]; then
    if DEFAULT_OUTPUT=$(python3 "$DEFAULT_CHECK_SCRIPT" 2>&1); then DEFAULT_EXIT=0; else DEFAULT_EXIT=$?; fi
    if [ $DEFAULT_EXIT -eq 0 ]; then
        DEFAULT_SUMMARY=$(echo "$DEFAULT_OUTPUT" | head -1)
        check_pass "Default realizations: $DEFAULT_SUMMARY"
    else
        DEFAULT_ISSUE_COUNT=$(echo "$DEFAULT_OUTPUT" | grep -oE "[0-9]+ default realization mismatch" | grep -oE "[0-9]+")
        check_error "Default realization mismatches: $DEFAULT_ISSUE_COUNT (doc labels disagree with config/default.cfg)"
        echo "$DEFAULT_OUTPUT" | grep "^    " | head -10 | while read -r line; do
            log "    $line"
        done
    fi
else
    check_warning "Default realization checker not found: $DEFAULT_CHECK_SCRIPT"
fi

# Check 19: Realization-Validity (header + footer cross-reference)
# =================================================================
print_section "19/28" "Checking module-doc realization validity (header + Verified Against footer)..."

REAL_CHECK_SCRIPT="$AGENT_DIR/scripts/check_module_realizations.py"
if [ -f "$REAL_CHECK_SCRIPT" ]; then
    if REAL_OUTPUT=$(python3 "$REAL_CHECK_SCRIPT" 2>&1); then REAL_EXIT=0; else REAL_EXIT=$?; fi
    REAL_SUMMARY=$(echo "$REAL_OUTPUT" | tail -1)
    if [ $REAL_EXIT -eq 0 ]; then
        check_pass "Realization validity: $REAL_SUMMARY"
    elif [ $REAL_EXIT -eq 2 ]; then
        check_warning "Realization validity: $REAL_SUMMARY"
        echo "$REAL_OUTPUT" | grep -E "^(⚠|❌)" | head -10 | while read -r line; do
            log "    $line"
        done
    else
        check_error "Realization validity: $REAL_SUMMARY"
        echo "$REAL_OUTPUT" | grep -E "^❌" | head -20 | while read -r line; do
            log "    $line"
        done
    fi
else
    check_warning "Realization validity checker not found: $REAL_CHECK_SCRIPT"
fi

# Check 20: Parameter default values (Pattern 13)
# ===============================================
print_section "20/28" "Checking parameter default values against source (Pattern 13)..."

PARAM_DEFAULT_SCRIPT="$AGENT_DIR/scripts/check_param_defaults.py"
if [ -f "$PARAM_DEFAULT_SCRIPT" ]; then
    if PARAM_OUTPUT=$(python3 "$PARAM_DEFAULT_SCRIPT" 2>&1); then PARAM_EXIT=0; else PARAM_EXIT=$?; fi
    PARAM_SUMMARY=$(echo "$PARAM_OUTPUT" | head -1)
    # Script always exits 0 (advisory); detect mismatches via output text.
    if echo "$PARAM_OUTPUT" | head -1 | grep -q "0 mismatches"; then
        check_pass "Param defaults: $PARAM_SUMMARY"
    elif [ $PARAM_EXIT -eq 0 ]; then
        check_warning "Param defaults: $PARAM_SUMMARY"
        echo "$PARAM_OUTPUT" | grep "^    " | head -10 | while read -r line; do
            log "    $line"
        done
    else
        check_error "Param defaults checker failed (exit $PARAM_EXIT)"
        echo "$PARAM_OUTPUT" | head -5 | while read -r line; do
            log "    $line"
        done
    fi
else
    check_warning "Param defaults checker not found: $PARAM_DEFAULT_SCRIPT"
fi

# ===============================================
# Check 21: Cross-cutting doc identifier existence (R3 Cluster 2 mechanization)
# Catches fabricated [vmps]\d*_<name> tokens in cross_module/ and core_docs/.
# Complements Check 14 (which scans modules/module_*.md).
# ===============================================
print_section "21/28" "Checking identifier existence in cross-cutting docs..."

DOC_VAR_EXIST_SCRIPT="$AGENT_DIR/scripts/check_doc_var_existence.py"
if [ -f "$DOC_VAR_EXIST_SCRIPT" ]; then
    if DOC_VAR_OUTPUT=$(python3 "$DOC_VAR_EXIST_SCRIPT" 2>&1); then DOC_VAR_EXIT=0; else DOC_VAR_EXIT=$?; fi
    if echo "$DOC_VAR_OUTPUT" | grep -q "All identifier references verified"; then
        ACCURACY=$(echo "$DOC_VAR_OUTPUT" | grep -oE "Accuracy: [0-9]+% \([0-9]+/[0-9]+ verified\)" | head -1)
        check_pass "Cross-cutting doc identifiers: $ACCURACY"
    elif [ $DOC_VAR_EXIT -eq 0 ]; then
        MISMATCH_COUNT=$(echo "$DOC_VAR_OUTPUT" | grep -oE "Found [0-9]+ identifier" | head -1)
        check_warning "Cross-cutting doc identifiers: $MISMATCH_COUNT not in GAMS code"
        echo "$DOC_VAR_OUTPUT" | grep "^  " | head -10 | while read -r line; do
            log "    $line"
        done
    else
        check_error "Cross-cutting identifier checker failed (exit $DOC_VAR_EXIT)"
        echo "$DOC_VAR_OUTPUT" | head -5 | while read -r line; do
            log "    $line"
        done
    fi
else
    check_warning "Cross-cutting identifier checker not found: $DOC_VAR_EXIST_SCRIPT"
fi

# ===============================================
# Check 22: Consumer-count attribution (I1 / R4 Cluster 3+4+5 mechanization)
# For every `var | N (modules)?` row in consumer-tables across module docs,
# Module_Dependencies, and modification_safety_guide, recompute the actual
# consumer count from .gms sources and flag mismatches. Advisory mode.
# ===============================================
print_section "22/28" "Checking consumer-count attribution against GAMS source..."

CONSUMER_CHECK_SCRIPT="$AGENT_DIR/scripts/check_consumer_attribution.py"
if [ -f "$CONSUMER_CHECK_SCRIPT" ]; then
    if CONSUMER_OUTPUT=$(python3 "$CONSUMER_CHECK_SCRIPT" 2>&1); then CONSUMER_EXIT=0; else CONSUMER_EXIT=$?; fi
    if echo "$CONSUMER_OUTPUT" | grep -q "All consumer-count claims match"; then
        SCANNED=$(echo "$CONSUMER_OUTPUT" | grep "claims scanned:" | grep -oE "[0-9]+" | head -1)
        check_pass "Consumer-count attribution: ${SCANNED:-?} claims verified"
    elif [ $CONSUMER_EXIT -eq 0 ]; then
        MISMATCH_COUNT=$(echo "$CONSUMER_OUTPUT" | grep -oE "Found [0-9]+ consumer-count" | grep -oE "[0-9]+" | head -1)
        check_warning "Consumer-count attribution: ${MISMATCH_COUNT:-?} mismatch(es)"
        echo "$CONSUMER_OUTPUT" | grep "^  " | head -10 | while read -r line; do
            log "    $line"
        done
    else
        check_error "Consumer-count attribution checker failed (exit $CONSUMER_EXIT)"
        echo "$CONSUMER_OUTPUT" | head -5 | while read -r line; do
            log "    $line"
        done
    fi
else
    check_warning "Consumer-count attribution checker not found: $CONSUMER_CHECK_SCRIPT"
fi

# ===============================================
# Check 23: Multi-section dimension consistency (I2 / R4 Lens 1 mechanization)
# When a backticked variable is mentioned with parenthesized dimensions in
# multiple sections of one module doc, verify all mentions use consistent
# dimensions (set-alias normalized). Catches rename stragglers like the M14
# pcm_tau h→j drift. Advisory mode (variants are usually legitimate context).
# ===============================================
print_section "23/28" "Checking multi-section dimension consistency... [RETIRED]"
# RETIRED 2026-06-07 (pipeline-audit R7/R10 finding C5-3): advisory-only (never
# gated); check_multi_section_consistency.py emitted a perpetual false-positive
# floor (signature "variants" are legitimate context variation) with zero
# lifetime real catches. Script + its 3 allowlist entries deleted. Tombstone
# keeps numbering stable; proper removal (stable check IDs) is deferred --
# see audit/BACKLOG.md "Validator check IDs".
log "    (retired: zero-catch advisory; see BACKLOG 'Validator check IDs')"

# ===============================================
# Check 24: Historical-rename references (I5)
# Greps for old identifier names (from audit/renames.json) in non-exempt
# docs. Skips italicized historical refs (`*old*`) and allowlist marker lines
# (which must name old names by design). Catches "doc references a name that
# was renamed in MAgPIE before the doc was last edited" — the M14 pcm_tau
# straggler class.
# ===============================================
print_section "24/28" "Checking historical-rename references..."

RENAMES_CHECK_SCRIPT="$AGENT_DIR/scripts/check_renames.py"
if [ -f "$RENAMES_CHECK_SCRIPT" ]; then
    if RENAMES_OUTPUT=$(python3 "$RENAMES_CHECK_SCRIPT" --summary-only 2>&1); then RENAMES_EXIT=0; else RENAMES_EXIT=$?; fi
    if echo "$RENAMES_OUTPUT" | grep -q "No references to historically-renamed"; then
        TRACKED=$(echo "$RENAMES_OUTPUT" | grep "Renames tracked:" | grep -oE "[0-9]+" || true)
        check_pass "Historical-rename references: 0 hits across ${TRACKED:-?} tracked renames"
    elif [ $RENAMES_EXIT -eq 0 ]; then
        HIT_COUNT=$(echo "$RENAMES_OUTPUT" | grep -oE "Found [0-9]+ reference" | grep -oE "[0-9]+" | head -1 || true)
        check_warning "Historical-rename references: ${HIT_COUNT:-?} stale reference(s) to renamed identifiers"
        echo "$RENAMES_OUTPUT" | grep "^  " | head -8 | while read -r line; do
            log "    $line"
        done
    else
        check_error "Historical-rename checker failed (exit $RENAMES_EXIT)"
        echo "$RENAMES_OUTPUT" | head -5 | while read -r line; do
            log "    $line"
        done
    fi
else
    check_warning "Historical-rename checker not found: $RENAMES_CHECK_SCRIPT"
fi

# ===============================================
# Check 25: Bare-basename .gms citations in non-module docs
# Enforces full-path citation form (modules/NN_name/REAL/file.gms:N) in
# cross_module/, core_docs/, reference/, agent/helpers/, AGENT.md, README.md.
# Migration was applied 2026-05-24 via scripts/migrate_bare_cites.py.
# Pedagogical examples can opt out via per-doc or per-line allow markers.
# ===============================================
print_section "25/28" "Checking for bare-basename .gms citations in non-module docs..."

BARE_CITES_SCRIPT="$AGENT_DIR/scripts/check_no_bare_cites.py"
if [ -f "$BARE_CITES_SCRIPT" ]; then
    if BARE_OUTPUT=$(python3 "$BARE_CITES_SCRIPT" --summary-only 2>&1); then BARE_EXIT=0; else BARE_EXIT=$?; fi
    if [ $BARE_EXIT -eq 0 ]; then
        check_pass "No bare-basename .gms citations in non-module docs"
    else
        BARE_COUNT=$(echo "$BARE_OUTPUT" | grep -oE "Bare cites found: [0-9]+" | grep -oE "[0-9]+" || true)
        check_error "${BARE_COUNT:-?} bare-basename .gms citation(s) in non-module docs"
        echo "$BARE_OUTPUT" | grep "^  " | head -8 | while read -r line; do
            log "    $line"
        done
    fi
else
    check_warning "Bare-cite checker not found: $BARE_CITES_SCRIPT"
fi

# Check 26: doc unit claims vs canonical declarations.gms units (advisory)
print_section "26/28" "Checking doc unit claims vs declarations.gms canonical units... [RETIRED]"
# RETIRED 2026-06-07 (pipeline-audit R7/R10 finding C5-4): advisory-only (never
# gated); check_units.py emitted a perpetual false-positive floor (legitimate
# unit abbreviations, e.g. USD vs USD17MER) with zero lifetime real catches.
# Script deleted (it owned no allowlist entries). Tombstone keeps numbering
# stable; proper removal (stable check IDs) is deferred -- see
# audit/BACKLOG.md "Validator check IDs".
log "    (retired: zero-catch advisory; see BACKLOG 'Validator check IDs')"

# Check 27: hedged-as-fact claims on interface-identifier lines (advisory)
print_section "" "Checking hedged-as-fact claims on interface-identifier lines (advisory)..."

HEDGED_SCRIPT="$AGENT_DIR/scripts/check_hedged_claims.py"
if [ -f "$HEDGED_SCRIPT" ]; then
    HEDGED_OUTPUT=$(python3 "$HEDGED_SCRIPT" 2>&1)
    HEDGED_COUNT=$(echo "$HEDGED_OUTPUT" | grep -oE "ADVISORY: [0-9]+ hedged" | grep -oE "[0-9]+" | head -1)
    [ -z "$HEDGED_COUNT" ] && HEDGED_COUNT=0
    if [ "$HEDGED_COUNT" = "0" ]; then
        check_pass "No hedged-as-fact claims on interface-identifier lines"
    else
        # Advisory: a hedge near an identifier is sometimes legitimate honest marking.
        check_warning "$HEDGED_COUNT hedged-as-fact claim(s) on interface-identifier lines (advisory; run scripts/check_hedged_claims.py)"
    fi
else
    check_warning "Hedged-claims checker not found: $HEDGED_SCRIPT"
fi

# Check 28: doc .scale-value claims vs scaling.gms canonical (advisory)
print_section "" "Checking doc .scale-value claims vs scaling.gms canonical (advisory)..."

SCALING_SCRIPT="$AGENT_DIR/scripts/check_scaling.py"
if [ -f "$SCALING_SCRIPT" ]; then
    SCALING_OUTPUT=$(python3 "$SCALING_SCRIPT" --summary 2>&1)
    SCALING_COUNT=$(echo "$SCALING_OUTPUT" | grep -oE "[0-9]+ mismatch" | grep -oE "[0-9]+" | head -1)
    [ -z "$SCALING_COUNT" ] && SCALING_COUNT=0
    if [ "$SCALING_COUNT" = "0" ]; then
        check_pass "Doc .scale-value claims match canonical scaling.gms"
    else
        # Advisory: catches the 10eN-vs-1eN (10x) doc error class. Reviewer triages
        # (realization-specific .scale values can legitimately differ).
        check_warning "$SCALING_COUNT doc scaling-value claim(s) differ from canonical (advisory; run scripts/check_scaling.py)"
    fi
else
    check_warning "Scaling checker not found: $SCALING_SCRIPT"
fi

# ===============================================
# Check 29: Set-member enumeration drift (R53 Phase 1, advisory)
# For each tracked CLOSED set (land family + carbon pools) parse the canonical
# membership from GAMS source, then flag module docs that enumerate the set
# `setname` (m1, m2, ...) with invented members. Positive control (in the
# script's --self-test): the R52 module_52 plant_pri/plant_sec bug.
# ===============================================
print_section "" "Checking set-member enumerations against canonical GAMS sets (R53)..."

SET_MEMBERS_SCRIPT="$AGENT_DIR/scripts/check_set_members.py"
if [ -f "$SET_MEMBERS_SCRIPT" ]; then
    if SETMEM_OUTPUT=$(python3 "$SET_MEMBERS_SCRIPT" 2>&1); then SETMEM_EXIT=0; else SETMEM_EXIT=$?; fi
    SETMEM_SUMMARY=$(echo "$SETMEM_OUTPUT" | head -1 | sed 's/^[[:space:]]*//')
    if echo "$SETMEM_OUTPUT" | head -1 | grep -q "0 mismatches"; then
        check_pass "$SETMEM_SUMMARY"
    elif [ $SETMEM_EXIT -eq 0 ]; then
        check_warning "$SETMEM_SUMMARY"
        echo "$SETMEM_OUTPUT" | grep "^    " | head -10 | while read -r line; do
            log "    $line"
        done
    else
        check_error "Set-member checker failed (exit $SETMEM_EXIT)"
        echo "$SETMEM_OUTPUT" | head -5 | while read -r line; do
            log "    $line"
        done
    fi
else
    check_warning "Set-member checker not found: $SET_MEMBERS_SCRIPT"
fi

# ===============================================
# Check 30: Intra-doc default contradiction (R53 Phase 1, advisory)
# Flags a scalar whose default is stated with two DIFFERENT primary values in one
# doc (doc-vs-doc, never doc-vs-unit-converted-source -> sidesteps the known
# Pattern-13 s59 unit FP). Positive control (in the script's --self-test): the R52
# module_59 s59_nitrogen_uptake 0.0002-vs-0.2 bug.
# ===============================================
print_section "" "Checking intra-doc default-value contradictions (R53)..."

INTRA_DOC_SCRIPT="$AGENT_DIR/scripts/check_intra_doc_contradiction.py"
if [ -f "$INTRA_DOC_SCRIPT" ]; then
    if INTRA_OUTPUT=$(python3 "$INTRA_DOC_SCRIPT" 2>&1); then INTRA_EXIT=0; else INTRA_EXIT=$?; fi
    INTRA_SUMMARY=$(echo "$INTRA_OUTPUT" | head -1 | sed 's/^[[:space:]]*//')
    if echo "$INTRA_OUTPUT" | head -1 | grep -q "contradictions: 0"; then
        check_pass "$INTRA_SUMMARY"
    elif [ $INTRA_EXIT -eq 0 ]; then
        check_warning "$INTRA_SUMMARY"
        echo "$INTRA_OUTPUT" | grep "^    " | head -10 | while read -r line; do
            log "    $line"
        done
    else
        check_error "Intra-doc contradiction checker failed (exit $INTRA_EXIT)"
        echo "$INTRA_OUTPUT" | head -5 | while read -r line; do
            log "    $line"
        done
    fi
else
    check_warning "Intra-doc contradiction checker not found: $INTRA_DOC_SCRIPT"
fi

# ===============================================
# Check 31: Role attribution / declarer verification (2026-06-29, advisory)
# Verifies explicit "declared in / provided by Module X" claims (and "Module X provides
# `var`") against declarations.gms (build_producer_map). Mechanizes the FP-safe DECLARED
# half of MANDATE 18. Positive control (in the script's --self-test): a planted
# "vm_carbon_stock declared in Module 52" (actual M56) + an "M10 provides pm_max_forest_est"
# phantom; FP-traps incl. legit slice-populator and the module_17.md:772 prose mis-bind.
# ===============================================
print_section "" "Checking doc role-attribution (declared-in / provider claims vs declarations.gms)..."

ROLE_ATTR_SCRIPT="$AGENT_DIR/scripts/check_role_attribution.py"
if [ -f "$ROLE_ATTR_SCRIPT" ]; then
    if ROLEATTR_OUTPUT=$(python3 "$ROLE_ATTR_SCRIPT" 2>&1); then ROLEATTR_EXIT=0; else ROLEATTR_EXIT=$?; fi
    ROLEATTR_SUMMARY=$(echo "$ROLEATTR_OUTPUT" | head -1 | sed 's/^[[:space:]]*//')
    if echo "$ROLEATTR_OUTPUT" | head -1 | grep -q "0 mismatches"; then
        check_pass "$ROLEATTR_SUMMARY"
    elif [ $ROLEATTR_EXIT -eq 0 ]; then
        check_warning "$ROLEATTR_SUMMARY"
        echo "$ROLEATTR_OUTPUT" | grep "^    " | head -10 | while read -r line; do
            log "    $line"
        done
    else
        check_error "Role-attribution checker failed (exit $ROLEATTR_EXIT)"
        echo "$ROLEATTR_OUTPUT" | head -5 | while read -r line; do
            log "    $line"
        done
    fi
else
    check_warning "Role-attribution checker not found: $ROLE_ATTR_SCRIPT"
fi

# Check 32: Attribution TABLES — phantom module<->var in Provides-To/Receives-From
# markdown tables (2026-07-15, advisory). The CONSUMER/provides-to half of MANDATE 18
# that Check 31 (DECLARED half) does not cover. Deterministic ~0-FNR; caught the R54
# module_32 Critical class (M10/M35 for forestry vars whose sole consumer is M58).
# Positive control in --self-test (planted phantom + correct rows). Coverage line is
# ALWAYS printed (a "0 findings" is meaningless without the denominator).
# ===============================================
print_section "" "Checking interface-attribution TABLES vs code (advisory)..."

ATTR_TABLES_SCRIPT="$AGENT_DIR/scripts/check_attribution_tables.py"
if [ -f "$ATTR_TABLES_SCRIPT" ]; then
    if ATTRTAB_OUTPUT=$(python3 "$ATTR_TABLES_SCRIPT" 2>&1); then ATTRTAB_EXIT=0; else ATTRTAB_EXIT=$?; fi
    ATTRTAB_COVERAGE=$(echo "$ATTRTAB_OUTPUT" | grep -m1 "coverage =" | sed 's/^[[:space:]]*//')
    if echo "$ATTRTAB_OUTPUT" | grep -q "could not build consumer map"; then
        check_warning "Attribution tables: skipped (parent modules/ not found)"
    elif echo "$ATTRTAB_OUTPUT" | grep -q "0 findings within covered"; then
        check_pass "${ATTRTAB_COVERAGE:-Attribution tables: 0 phantom findings}"
    elif [ $ATTRTAB_EXIT -eq 0 ]; then
        ATTRTAB_N=$(echo "$ATTRTAB_OUTPUT" | grep -oE "[0-9]+ advisory phantom" | grep -oE "^[0-9]+")
        check_warning "Attribution tables: ${ATTRTAB_N:-some} phantom finding(s) (advisory; run scripts/check_attribution_tables.py)"
        echo "$ATTRTAB_OUTPUT" | grep "attribution-table" | head -10 | while read -r line; do
            log "    $line"
        done
    else
        check_error "Attribution-tables checker failed (exit $ATTRTAB_EXIT)"
        echo "$ATTRTAB_OUTPUT" | head -5 | while read -r line; do log "    $line"; done
    fi
else
    check_warning "Attribution-tables checker not found: $ATTR_TABLES_SCRIPT"
fi

# Check 33: Attribution PROSE — phantom module<->var in single-module prose attributions
# (2026-07-15, advisory). The prose complement to Check 32; closes the gap Check 31 left
# (its regex needs the module number adjacent to the verb, so labeled bullets
# "- **Module 10 (Land):** Provides `fm_croparea`" — a real R54 Critical — slip through).
# Direction-agnostic phantom test; precision-first (one module + one var per ;-clause).
# Positive control in --self-test (17 cases incl. the corpus FP classes). Coverage always
# printed.
# ===============================================
print_section "" "Checking interface-attribution PROSE vs code (advisory)..."

ATTR_PROSE_SCRIPT="$AGENT_DIR/scripts/check_attribution_prose.py"
if [ -f "$ATTR_PROSE_SCRIPT" ]; then
    if ATTRPROSE_OUTPUT=$(python3 "$ATTR_PROSE_SCRIPT" 2>&1); then ATTRPROSE_EXIT=0; else ATTRPROSE_EXIT=$?; fi
    ATTRPROSE_COVERAGE=$(echo "$ATTRPROSE_OUTPUT" | grep -m1 "coverage =" | sed 's/^[[:space:]]*//')
    if echo "$ATTRPROSE_OUTPUT" | grep -q "could not build consumer map"; then
        check_warning "Attribution prose: skipped (parent modules/ not found)"
    elif echo "$ATTRPROSE_OUTPUT" | grep -q "0 findings within covered"; then
        check_pass "${ATTRPROSE_COVERAGE:-Attribution prose: 0 phantom findings}"
    elif [ $ATTRPROSE_EXIT -eq 0 ]; then
        ATTRPROSE_N=$(echo "$ATTRPROSE_OUTPUT" | grep -oE "[0-9]+ advisory phantom" | grep -oE "^[0-9]+")
        check_warning "Attribution prose: ${ATTRPROSE_N:-some} phantom finding(s) (advisory; run scripts/check_attribution_prose.py)"
        echo "$ATTRPROSE_OUTPUT" | grep "attribution-prose" | head -10 | while read -r line; do
            log "    $line"
        done
    else
        check_error "Attribution-prose checker failed (exit $ATTRPROSE_EXIT)"
        echo "$ATTRPROSE_OUTPUT" | head -5 | while read -r line; do log "    $line"; done
    fi
else
    check_warning "Attribution-prose checker not found: $ATTR_PROSE_SCRIPT"
fi

# Check 34: Attribution OMISSIONS — role-resolved completeness (2026-07-16, advisory).
# The OMISSION complement to Checks 32/33 (which flag phantoms only). Builds a
# code-derived {declared/populated/read} role map and flags a real consumer/producer
# absent from an owner's Provides-To table or an explicit "consumers of `V`" list —
# the exact class that hid Module 58 in R54. Deterministic; precision-first (owner +
# completeness gate); coverage line ALWAYS printed. Positive control in --self-test
# (16 cases incl. the M58 hider) + historical replay on pre-R54 module_32.
# ===============================================
print_section "" "Checking interface-attribution OMISSIONS vs code (advisory)..."

ATTR_OMIT_SCRIPT="$AGENT_DIR/scripts/check_attribution_omissions.py"
if [ -f "$ATTR_OMIT_SCRIPT" ]; then
    if ATTROMIT_OUTPUT=$(python3 "$ATTR_OMIT_SCRIPT" 2>&1); then ATTROMIT_EXIT=0; else ATTROMIT_EXIT=$?; fi
    ATTROMIT_COVERAGE=$(echo "$ATTROMIT_OUTPUT" | grep -m1 "coverage =" | sed 's/^[[:space:]]*//')
    ATTROMIT_SUMMARY=$(echo "$ATTROMIT_OUTPUT" | grep -m1 "SUMMARY")
    ATTROMIT_NPH=$(echo "$ATTROMIT_SUMMARY" | grep -oE "phantoms=[0-9]+" | grep -oE "[0-9]+")
    ATTROMIT_NOM=$(echo "$ATTROMIT_SUMMARY" | grep -oE "omissions_high=[0-9]+" | grep -oE "[0-9]+")
    if echo "$ATTROMIT_OUTPUT" | grep -q "GAMS modules not found"; then
        check_warning "Attribution omissions: skipped (parent modules/ not found)"
    elif [ "${ATTROMIT_NPH:-0}" = "0" ] && [ "${ATTROMIT_NOM:-0}" = "0" ]; then
        check_pass "${ATTROMIT_COVERAGE:-Attribution omissions: 0 findings}"
    elif [ $ATTROMIT_EXIT -eq 0 ]; then
        check_warning "Attribution omissions: ${ATTROMIT_NPH:-?} phantom / ${ATTROMIT_NOM:-?} omission (advisory; run scripts/check_attribution_omissions.py)"
        echo "$ATTROMIT_OUTPUT" | grep -E "omits M[0-9]|references the var nowhere" | head -10 | while read -r line; do
            log "    $line"
        done
    else
        check_error "Attribution-omissions checker failed (exit $ATTROMIT_EXIT)"
        echo "$ATTROMIT_OUTPUT" | head -5 | while read -r line; do log "    $line"; done
    fi
else
    check_warning "Attribution-omissions checker not found: $ATTR_OMIT_SCRIPT"
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

# Structural guard (pipeline-audit R8 I2): every section's print_section runs
# unconditionally, so SECTION_NUM must equal SECTION_TOTAL on a complete run. A
# mismatch means a whole section was silently skipped (a continue, a dead if, or
# a dropped block) - the verdict would be a green that verified less than it
# claims. This closes the "completed=1 proves REACHED, not RAN" gap; catch it loudly.
if [ "$SECTION_NUM" -ne "$SECTION_TOTAL" ]; then
    VALIDATOR_COMPLETED=1   # we did reach here; suppress the generic ABORT message
    echo ""
    log_color "${RED}FATAL: section-count mismatch: ran $SECTION_NUM of $SECTION_TOTAL sections.${NC}" "FATAL: ran $SECTION_NUM/$SECTION_TOTAL sections"
    log "A section was silently skipped (or SECTION_TOTAL is stale). The verdict is"
    log "structurally INVALID and MUST NOT be recorded as a pass."
    echo "VALIDATOR_RESULT: completed=1 sections=$SECTION_NUM/$SECTION_TOTAL verdict=ABORTED"
    exit 99
fi

# ============
# Machine-readable verdict.
# Cite the VALIDATOR_RESULT line (or latest_result.json) verbatim in
# project/sync_log.json and PR descriptions. NEVER hand-type "NN/NN clean":
# `completed=1` is the proof the run actually reached this point — the missing
# guarantee that let a dead validator be reported as passing for ~7 months.
# ============
if [ "$ERRORS" -gt 0 ]; then
    VERDICT="FAIL"
else
    VERDICT="PASS"
fi

# Mark completion BEFORE emitting results so the EXIT trap treats this as a
# clean finish rather than an abort.
VALIDATOR_COMPLETED=1

RESULT_LINE="VALIDATOR_RESULT: completed=1 checks=$TOTAL_CHECKS passed=$PASSED_CHECKS warnings=$WARNINGS errors=$ERRORS verdict=$VERDICT"
echo ""
log_color "${BLUE}${RESULT_LINE}${NC}" "$RESULT_LINE"

RESULT_JSON="${REPORT_DIR}/latest_result.json"
cat > "$RESULT_JSON" <<EOF
{
  "completed": true,
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "checks": $TOTAL_CHECKS,
  "passed": $PASSED_CHECKS,
  "warnings": $WARNINGS,
  "errors": $ERRORS,
  "verdict": "$VERDICT"
}
EOF
log_color "${BLUE}Result JSON: $RESULT_JSON${NC}" "Result JSON: $RESULT_JSON"

# Exit code: 0 = PASS, 1 = FAIL (completed with errors). 99 = ABORTED is
# emitted by the EXIT trap when the run never reaches this block.
if [ "$ERRORS" -gt 0 ]; then
    exit 1
else
    exit 0
fi
