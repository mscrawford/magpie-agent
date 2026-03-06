# Validate Documentation Consistency

Checks the magpie-agent documentation ecosystem for inconsistencies, duplicates, and potential conflicts across 82+ files.

---

## 🎯 Purpose

With 82+ documentation files (~65,000 lines), information about modules, dependencies, and conservation laws appears in multiple places. This command detects inconsistencies so they can be fixed manually or through compression.

**Key checks:**
- Dependency counts across files (e.g., "Module 10 has 23 dependents")
- Equation parameter counts (e.g., Chapman-Richards has 3 parameters)
- Cross-references to files that don't exist
- Duplicate equation definitions with different formulas
- Entry point consistency (README, AGENT.md, sync_log.json)

---

## 📋 When to Use

Run validation:
- **Before releases** - ensure documentation is consistent
- **After adding/updating files** - verify new content doesn't conflict
- **When suspecting inconsistencies** - diagnose specific issues
- **Monthly maintenance** - proactive consistency check
- **Before compression** - identify what needs consolidating

---

## 🚀 How It Works

### Step 1: Run Validation Script

```bash
./scripts/validate_consistency.sh
```

**The script checks:**

1. **Dependency Count Consistency**
   - Searches for mentions of module dependency counts
   - Flags if different numbers appear in different files
   - Example: "Module 10 has 23 dependents" vs "Module 10 has 22 dependents"

2. **Equation Parameter Consistency**
   - Checks equation descriptions across files
   - Example: Chapman-Richards parameters, water allocation constraints
   - Flags if same equation described differently

3. **Cross-Reference Validity**
   - Extracts all "see module_XX.md" and similar references
   - Verifies target files exist
   - Reports broken links

4. **Duplicate Equation Definitions**
   - Finds equations mentioned in multiple places
   - Checks if formulas match
   - Flags discrepancies

5. **Entry Point Consistency**
   - Checks README.md and AGENT.md
   - Verifies README points to CURRENT_STATE.json and AGENT.md
   - Verifies AGENT.md has command system and sync tracking
   - Checks sync_log.json exists

6. **File Count Audit**
   - Counts files in each category
   - Compares to expected file inventory
   - Flags if counts have changed (new files added?)

---

## 📊 Example Output

```
=== MAgPIE Documentation Consistency Validation ===
Date: [current date]

[1/6] Checking dependency counts...
✓ Module 10: 23 dependents (consistent across 4 files)
✓ Module 11: 17 dependents (consistent)
⚠️  Module 17: Found "21 dependents" in Phase2 but "20 dependents" in modification_safety_guide.md
    → Files: Module_Dependencies.md:87, modification_safety_guide.md:203

[2/6] Checking equation parameters...
✓ Chapman-Richards: 3 parameters (consistent across 3 files)
✓ Land balance: q10_land_area (consistent)
⚠️  Water allocation: "5 sectors" in module_42.md but "4 sectors" in water_balance_conservation.md
    → Files: module_42.md:156, water_balance_conservation.md:89

[3/6] Checking cross-references...
✓ All 47 module references valid
✓ All 12 Phase document references valid
❌ Broken reference: module_65_notes.md referenced in AGENT.md:890 but file doesn't exist

[4/6] Checking duplicate equations...
✓ q70_feed: Consistent definition across 2 files
⚠️  q52_carbon_growth: Different descriptions found
    → module_52.md: "Chapman-Richards with 3 parameters"
    → carbon_balance_conservation.md: "Age-dependent carbon accumulation function"
    → (Descriptions semantically equivalent but phrased differently - low risk)

[5/6] Checking entry point consistency...
✓ README.md points to CURRENT_STATE.json
✓ README.md points to AGENT.md
✓ AGENT.md has command system
✓ AGENT.md references sync tracking
✓ project/sync_log.json exists

[6/6] Checking file counts...
✓ Module docs: 46 files (matches inventory)
✓ Notes files: 3 files (matches inventory)
✓ Cross-module: 6 files (matches inventory)
⚠️  Feedback integrated: 8 files (inventory says 5 - updated recently?)
    → Note: file counts have changed since last validation

=== Summary ===
Total checks: 127
✓ Passed: 119
⚠️  Warnings: 7 (should review)
❌ Errors: 1 (must fix)

Detailed report saved to: validation_report_20251026_143022.txt
```

---

## 🛠️ Workflow

### Step 1: Run Validation

**Command:**
```bash
./scripts/validate_consistency.sh
```

**Output:** Console report + detailed text file

### Step 2: Review Findings

**Errors (❌)** - Must fix:
- Broken cross-references
- Missing files
- Critical inconsistencies (different dependency counts)

**Warnings (⚠️)** - Should review:
- Semantic differences (same meaning, different phrasing)
- File count changes (may be intentional)
- Minor discrepancies

### Step 3: Fix Issues

**For errors:**
1. Fix broken references
2. Update incorrect numbers to match authoritative source
3. Add missing files or remove references

**For warnings:**
1. Decide if it's a real issue or acceptable variation
2. If real issue: update lower-precedence files to match authoritative source
3. If acceptable: document why it's okay (e.g., semantic equivalence)

### Step 4: Re-run Validation

```bash
./scripts/validate_consistency.sh
```

**Goal:** All checks pass or only acceptable warnings remain

### Step 5: Update Ecosystem Map (if needed)

If file counts changed:
```bash
# Update file count records
# Document what was added/removed
```

---

## 📐 Understanding Validation Results

### Dependency Count Inconsistencies

**Example finding:**
```
⚠️  Module 17: Found "21 dependents" in Phase2 but "20 dependents" in modification_safety_guide.md
```

**How to fix:**
1. Check Module_Dependencies.md (authoritative source)
2. Update modification_safety_guide.md to match
3. Update any module_XX_notes.md that mention it

**Precedence:** Module_Dependencies.md > other files

### Equation Description Inconsistencies

**Example finding:**
```
⚠️  Chapman-Richards: module_52.md says "3 parameters" but notes say "4 parameters"
```

**How to fix:**
1. Check actual GAMS code (ultimate truth)
2. Update module_52.md if wrong (should be rare - docs are verified)
3. Update module_52_notes.md to match

**Precedence:** Code > module_XX.md > notes

### Broken Cross-References

**Example finding:**
```
❌ Broken reference: module_65_notes.md referenced in AGENT.md:890 but file doesn't exist
```

**How to fix:**
- If file should exist: Create it
- If reference is wrong: Remove or update the reference

### Semantic Differences (Low Risk)

**Example finding:**
```
⚠️  q52_carbon_growth: Different descriptions found
    → module_52.md: "Chapman-Richards with 3 parameters"
    → carbon_balance_conservation.md: "Age-dependent carbon accumulation function"
    → (Descriptions semantically equivalent but phrased differently - low risk)
```

**Action:** Usually acceptable. Both descriptions are correct, just at different levels of detail.

---

## 🎯 Best Practices

### When to Fix

**Always fix:**
- ❌ Broken references
- ❌ Contradictory numbers (different dependency counts)
- ❌ Incorrect equation formulas

**Consider fixing:**
- ⚠️ Semantic differences (if they might confuse users)
- ⚠️ Outdated information in notes files

**Don't fix:**
- ⚠️ Acceptable variation (overview vs. detailed description)
- ⚠️ Intentional file count changes

### Update Strategy

**Use document precedence hierarchy:**

1. **Code** (ultimate truth) ← Check if unsure
2. **Module docs** (verified) ← Update if code changed
3. **Cross-module** (derived) ← Update if module docs changed
4. **Architecture** (overview) ← Update if major changes
5. **Notes** (experience) ← Update if facts changed

**Bottom-up propagation:** Fix authoritative source first, then propagate to derived sources.

### Automation

**What validation does:**
- ✅ Detect inconsistencies
- ✅ Report findings
- ✅ Suggest fixes

**What validation does NOT do:**
- ❌ Auto-fix issues (too risky)
- ❌ Decide what's "correct" (needs human judgment)
- ❌ Update files automatically

**Validation is detective work, not automatic repair.**

---

## 🔗 Integration with Other Commands

### Before Compression

```bash
# 1. Validate first
./scripts/validate_consistency.sh

# 2. Fix any errors found
# (manual fixes based on report)

# 3. Then compress
# Use /compress-documentation
```

**Why:** Compression consolidates content. Validate ensures you're consolidating *correct* content.

### After Updates

```bash
# 1. Update documentation
# (add module_XX_notes.md, update AGENT.md, etc.)

# 2. Validate
./scripts/validate_consistency.sh

# 3. Fix any new inconsistencies
```

### Monthly Maintenance

```bash
# 1. Validate
./scripts/validate_consistency.sh

# 2. Review warnings (even if no errors)

# 3. Update file count records if needed

# 4. Consider compression if duplicates found
```

---

## 🛡️ What Validation Catches

### Real Issues Caught

**Example 1: Dependency count divergence**
- Module_Dependencies.md updated with new analysis
- modification_safety_guide.md still has old count
- Validation catches mismatch

**Example 2: Notes file contradicts main doc**
- module_52.md updated after code verification
- module_52_notes.md has old information
- Validation flags discrepancy

**Example 3: Broken reference after file rename**
- module_70_notes.md renamed
- AGENT.md still references old name
- Validation catches broken link

### What Validation Misses

**Semantic inconsistencies:**
- "Module 10 is critical" vs "Module 10 is high-risk" (same meaning, different words)
- Validation can't determine semantic equivalence

**Outdated but technically correct:**
- "Module 17 has 21 dependents" was correct 6 months ago, now it's 22
- If old number still exists somewhere, validation may not catch it without timestamp context

**Code vs. docs divergence:**
- Code changed but docs not yet updated
- Validation checks doc-to-doc consistency, not code-to-doc
- (Manual code verification still needed)

---

## 📊 Validation Report Format

**Console output:** Summary of findings (shown above)

**Detailed report file:** `validation_report_YYYYMMDD_HHMMSS.txt`

**Report includes:**
- Timestamp and file counts
- Every check performed
- All inconsistencies found (with file:line numbers)
- Recommendations for fixes
- Precedence hierarchy reminder
- List of authoritative sources

**Keep reports:** Track consistency over time, compare before/after fixes.

---

## 🔍 Troubleshooting

### Issue: "Too many warnings"

**Cause:** Acceptable variation flagged as inconsistencies

**Solution:**
- Review warnings manually
- Add exceptions to validation script for known acceptable cases

### Issue: "False positives"

**Cause:** Different valid descriptions of same concept

**Solution:**
- Use judgment: Is this a real inconsistency or just different phrasing?
- If false positive: Note in report, don't "fix"
- Consider updating validation script to be more nuanced

### Issue: "No inconsistencies found but I know there are some"

**Cause:** Validation script checks limited patterns

**Solution:**
- Validation is not exhaustive - it checks common issues
- Manual review still valuable
- Consider adding new checks to script for specific issues

---

## 💡 Philosophy

**Validation is preventive medicine:**
- Catches problems early before they confuse users
- Maintains quality as documentation grows
- Enables safe parallel editing (multiple contributors)

**Validation is not perfect:**
- Can't catch everything
- Requires human judgment
- Should complement, not replace, manual review

**Best practice:**
- Run validation regularly
- Fix errors immediately
- Review warnings thoughtfully
- Keep ecosystem map updated

---

## 📚 See Also

- `/compress-documentation` - Consolidate redundant documentation
- `AGENT.md` - Document precedence hierarchy and link rules
- `scripts/validate_consistency.sh` - Validation script details

---

**Validation keeps 82+ files working together harmoniously!** ✅
