# Validate Module Documentation

**Usage**: `command: validate-module XX` or `command: validate-module all`

**Purpose**: Comprehensive validation of module documentation quality, structure, links, and freshness.

**What to do**: When the user invokes this command, perform a thorough validation check of the specified module(s).

---

## Validation Process

### Step 1: Parse Command Arguments

Extract the module number from the command:
- `command: validate-module 10` → validate module_10.md
- `command: validate-module all` → validate all 46 modules

### Step 2: Run Validation Checks

For each module, validate the following:

#### **Check 1: File Existence & Readability**
```bash
test -f modules/module_XX.md && test -r modules/module_XX.md
```
- ✅ File exists and is readable
- ❌ File missing or unreadable

#### **Check 2: Required Sections Present**

All modules MUST have these sections (check for markdown headers):
1. `# Module XX` (title)
2. `## Overview` or `## Quick Reference`
3. `## Equations`
4. `## Parameters`
5. `## Interface Variables`
6. `## Participates In` (added in Task 2.2)
7. `## Limitations`
8. `**Last Verified**` (added in Task 2.3)

```bash
for section in "# Module" "## Overview" "## Equations" "## Parameters" "## Interface Variables" "## Participates In" "## Limitations" "Last Verified"; do
  grep -q "$section" modules/module_XX.md || echo "Missing: $section"
done
```

#### **Check 3: Links Validity**

Extract all markdown links and verify targets exist:
```bash
# Extract links: [text](path)
grep -oP '\[.*?\]\(\K[^)]+' modules/module_XX.md
```

Validate each link:
- Internal links (e.g., `#section-name`) → verify section exists
- Relative file links (e.g., `../modules/10_land/`) → verify file/directory exists
- Cross-doc links (e.g., `Module_Dependencies.md`) → verify file exists
- Cross-doc anchors (e.g., `Module_Dependencies.md#module-10`) → verify file exists (anchor validation optional)

Common link patterns to check:
- `Module_Dependencies.md#module-XX`
- `cross_module/*.md`
- `core_docs/*.md`
- `reference/GAMS_Phase*.md`

#### **Check 4: Verification Timestamp Freshness**

Extract the "Last Verified" date and check age:
```bash
grep "Last Verified" modules/module_XX.md
```

Thresholds:
- ✅ **Fresh**: < 3 months old
- ⚠️ **Aging**: 3-6 months old (consider re-verification)
- 🔴 **Stale**: > 6 months old (re-verification recommended)

Calculate age from today's date.

#### **Check 5: Participates In Structure**

The "Participates In" section should have these subsections:
1. `### Conservation Laws` (if applicable)
2. `### Dependency Chains`
3. `### Circular Dependencies` (if applicable)
4. `### Modification Safety`

Verify:
- Section exists
- Has appropriate subsections (at least Dependency Chains)
- Contains links (no bare dependency counts)

#### **Check 6: Cross-Reference Consistency**

Check if this module is mentioned correctly in other files:

**If module is in Module_Dependencies.md:**
- Extract dependent count from Phase2
- Search for module mentions in other files
- Verify no outdated counts elsewhere

**If module is in conservation laws:**
- Check it's mentioned in relevant `cross_module/*_balance_conservation.md`

**If module has high centrality (10, 11, 17, 56):**
- Check it's in `modification_safety_guide.md`

#### **Check 7: No Duplicate Information**

Scan for patterns that indicate duplication:
- Full equation formulas (should only be in module_XX.md)
- Dependency counts (should only be in Phase2 or linked)
- Conservation law equations (should only be in cross_module/*.md)

Warning patterns:
```bash
grep -E "has \d+ dependents" modules/module_XX.md
grep -E "q\d+_\w+ =e=" modules/module_XX.md  # Full equation formulas
```

---

## Step 3: Generate Validation Report

Create a structured report showing results:

```markdown
=== Module XX Validation Report ===
Generated: YYYY-MM-DD HH:MM

**File Status**
✅ File exists and readable: modules/module_XX.md
✅ Size: X KB, Y lines

**Structure Validation**
✅ Required sections: 8/8 present
   ✅ Title (# Module XX)
   ✅ Overview
   ✅ Equations
   ✅ Parameters
   ✅ Interface Variables
   ✅ Participates In
   ✅ Limitations
   ✅ Last Verified timestamp

**Links Validation**
✅ Internal links: 12/12 valid
✅ Cross-doc links: 8/8 valid
   ✅ Module_Dependencies.md
   ✅ cross_module/land_balance_conservation.md
   ✅ modification_safety_guide.md
❌ Broken links: 1 found
   ❌ Module_Dependencies.md#module-XX-deps (file exists, anchor not checked)

**Verification Status**
✅ Last Verified: 2025-10-13 (13 days ago - FRESH)
✅ Verified Against: ../modules/XX_*/realization/*.gms
✅ Changes noted: None (stable)

**Participates In Structure**
✅ Section present
✅ Subsections: 4/4 expected
   ✅ Conservation Laws
   ✅ Dependency Chains
   ✅ Circular Dependencies
   ✅ Modification Safety
✅ Links only (no duplication)

**Cross-Reference Consistency**
✅ Phase2 lists XX dependents
✅ No outdated counts found elsewhere
✅ Conservation law mentions consistent

**Duplication Check**
✅ No full equation formulas (appropriate for module doc)
✅ No dependency counts (uses links)
✅ Follows link-don't-duplicate principle

=== Summary ===
Checks: 25
✅ Passed: 24
⚠️ Warnings: 0
❌ Errors: 1

**Overall**: ⚠️ MINOR ISSUES (1 broken link)

**Recommendations**:
1. Fix broken link to Module_Dependencies.md#module-XX-deps
2. Module is otherwise well-maintained

**Next Steps**:
- Fix identified issues
- Module will be ready for production use
```

---

## Step 4: For `command: validate-module all`

When validating all modules:

1. **Run validation for each of the 46 modules**
2. **Generate summary statistics:**
   - Total modules validated
   - Fully passing (all checks ✅)
   - With warnings (⚠️)
   - With errors (❌)
   - Common issues across modules

3. **Prioritize issues:**
   - Critical: Broken links, missing required sections
   - High: Stale verification (> 6 months), missing Participates In
   - Medium: Aging verification (3-6 months)
   - Low: Minor formatting issues

4. **Generate action items:**
   ```markdown
   === Validation Summary (All 46 Modules) ===

   ✅ Fully Valid: 38 modules
   ⚠️ Warnings: 6 modules
   ❌ Errors: 2 modules

   **Priority Actions**:
   1. Fix broken links in Module 10, Module 52
   2. Re-verify 8 stale modules (> 6 months): 15, 22, 28, ...
   3. Add missing Participates In to 0 modules (all complete)

   **Common Issues**:
   - Broken links: 4 occurrences (modules 10, 35, 52, 70)
   - Stale verification: 8 modules
   - Missing sections: 0 modules

   **Health Score**: 92/100 (Excellent)
   ```

---

## Step 5: Implementation Notes

**Tools to use:**
- `Read` tool to read module content
- `Bash` tool for grep, file checks
- `Glob` tool to find files for link validation
- Regular expressions to parse sections and links

**Performance:**
- Single module: ~30 seconds
- All modules: ~5 minutes (validate in batches, report progress)

**Output format:**
- Use markdown with ✅ ⚠️ ❌ for visual clarity
- Include line numbers when reporting issues
- Provide actionable recommendations

---

## Example Usage

**User**: `command: validate-module 10`

**Agent response:**
"Let me validate Module 10 documentation..."

[Runs validation checks]

[Presents formatted report]

"Module 10 is in excellent shape! All 24 checks passed. Last verified 13 days ago (fresh). The documentation is production-ready."

---

**User**: `command: validate-module all`

**Agent response:**
"Validating all 46 modules... this will take ~5 minutes."

[Progress updates every 10 modules]

[Generates summary report]

"Validation complete! 38/46 modules are fully valid. Found 2 modules with broken links (priority fix) and 8 modules with stale verification (6+ months old). Overall health score: 92/100 (Excellent)."

---

## Validation Logic Reference

### Date Age Calculation

```python
from datetime import datetime

last_verified = "2025-10-13"
today = datetime(2025, 10, 26)
verified_date = datetime.strptime(last_verified, "%Y-%m-%d")
age_days = (today - verified_date).days

if age_days < 90:
    status = "✅ FRESH"
elif age_days < 180:
    status = "⚠️ AGING"
else:
    status = "🔴 STALE"
```

### Link Validation

```bash
# Extract markdown links
grep -oE '\[([^]]+)\]\(([^)]+)\)' module.md

# Check if file exists
for link in $(extracted_links); do
  # Remove anchor if present
  file=$(echo "$link" | cut -d'#' -f1)
  if [ -n "$file" ] && [ ! -f "$file" ]; then
    echo "❌ Broken link: $link"
  fi
done
```

### Section Validation

Required headers (must appear in order):
1. `# Module XX` - Main title
2. `## Overview` OR `## Quick Reference` - Introduction
3. `## Equations` - Documented equations
4. `## Parameters` - Module parameters
5. `## Interface Variables` - What module provides/consumes
6. `## Participates In` - System-level participation
7. `## Limitations` - Known limitations
8. Footer with `**Last Verified**` - Timestamp

---

## Error Handling

**If module number invalid:**
```
❌ Error: Module number must be 09-80 (with gaps)
Valid modules: 09, 10, 11, ..., 80
Use `command: validate-module all` to validate all modules.
```

**If module file missing:**
```
❌ Error: modules/module_XX.md not found
Expected location: /Users/turnip/Documents/Work/Workspace/magpie/magpie-agent/modules/module_XX.md
```

**If validation fails catastrophically:**
```
❌ Validation failed for Module XX due to parsing error.
Manual inspection recommended: modules/module_XX.md
```

---

This command enables comprehensive quality assurance for module documentation, ensuring consistency, freshness, and adherence to documentation standards.
