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
print_section "1/6" "Checking dependency counts..."

# Check Module 10
MODULE_10_REFS=$(grep -r "Module 10.*dependents\|10.*dependents" \
    modules/module_10.md \
    modules/module_10_notes.md \
    core_docs/Phase2_Module_Dependencies.md \
    cross_module/modification_safety_guide.md \
    2>/dev/null | grep -oE "[0-9]+ dependent" | grep -oE "[0-9]+" | sort -u)

COUNT_10=$(echo "$MODULE_10_REFS" | wc -l | tr -d ' ')
if [ "$COUNT_10" -eq 1 ]; then
    check_pass "Module 10: $(echo $MODULE_10_REFS) dependents (consistent across 4 files)"
elif [ "$COUNT_10" -eq 0 ]; then
    check_warning "Module 10: No dependency count found in expected files"
else
    check_warning "Module 10: Inconsistent counts found: $(echo $MODULE_10_REFS | tr '\n' ' ')"
    log "    → Check: modules/module_10.md, modules/module_10_notes.md, Phase2_Module_Dependencies.md, modification_safety_guide.md"
fi

# Check Module 11
MODULE_11_REFS=$(grep -r "Module 11.*dependents\|11.*dependents" \
    modules/module_11.md \
    core_docs/Phase2_Module_Dependencies.md \
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
    core_docs/Phase2_Module_Dependencies.md \
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
print_section "2/6" "Checking equation parameters..."

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
print_section "3/6" "Checking cross-references..."

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
print_section "4/6" "Checking duplicate equations..."

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
print_section "5/6" "Checking entry point consistency..."

# START_HERE should point to CURRENT_STATE
if grep -q "CURRENT_STATE.json" START_HERE.md 2>/dev/null; then
    check_pass "START_HERE.md points to CURRENT_STATE.json"
else
    check_error "START_HERE.md doesn't reference CURRENT_STATE.json"
fi

# README should point to START_HERE
if grep -q "START_HERE" README.md 2>/dev/null; then
    check_pass "README.md points to START_HERE.md"
else
    check_warning "README.md doesn't reference START_HERE.md"
fi

# RULES_OF_THE_ROAD should point to CURRENT_STATE
if grep -q "CURRENT_STATE" RULES_OF_THE_ROAD.md 2>/dev/null; then
    check_pass "RULES_OF_THE_ROAD.md points to CURRENT_STATE.json"
else
    check_warning "RULES_OF_THE_ROAD.md doesn't reference CURRENT_STATE.json"
fi

# AGENT.md should separate contexts
if grep -q "Context 1.*MAgPIE" AGENT.md && grep -q "Context 2.*Documentation Project" AGENT.md; then
    check_pass "AGENT.md correctly separates contexts"
else
    check_warning "AGENT.md may not clearly separate MAgPIE vs. documentation project contexts"
fi

# =======================
# Check 6: File Counts
# =======================
print_section "6/6" "Checking file counts..."

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
log "    → Update DOCUMENTATION_ECOSYSTEM_MAP.md if this changed"

# Count GAMS reference docs
GAMS_COUNT=$(ls -1 reference/GAMS_Phase*.md 2>/dev/null | wc -l | tr -d ' ')
if [ "$GAMS_COUNT" -eq 6 ]; then
    check_pass "GAMS reference: $GAMS_COUNT files (matches expected 6)"
else
    check_warning "GAMS reference: $GAMS_COUNT files (expected 6)"
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
    log "4. Architecture (core_docs/Phase*.md)"
    log "5. Notes (modules/module_XX_notes.md)"
    log ""
    log "Fix errors first, then review warnings to determine if action needed."
    log "See DOCUMENTATION_ECOSYSTEM_MAP.md for authoritative sources."
fi

# Exit code
if [ $ERRORS -gt 0 ]; then
    exit 1
else
    exit 0
fi
