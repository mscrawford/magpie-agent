# Module Verification Protocol

<!-- check-gams-vars: allow f22_bii,f35_fire_loss,pm_carbon_density -->

**Purpose**: Ensure 100% accuracy in module documentation through systematic verification.

---

## Full Verification (New Modules)

**Use when**: Creating documentation from scratch or uncertain about existing docs.

**Time**: 1-2 hours per module

### Step 1: Read All Source Files (30 min)

```bash
# Identify module realization
ls modules/XX_modulename/

# Read all GAMS files in order
modules/XX_modulename/realization_name/
  ├── declarations.gms   ← Start here (sets, parameters, variables, equations)
  ├── input.gms          ← Configuration & input file loading
  ├── sets.gms           ← Module-specific sets (if exists)
  ├── preloop.gms        ← Pre-optimization calculations
  ├── presolve.gms       ← Time-step calculations before solve
  ├── equations.gms      ← Equation implementations
  ├── postsolve.gms      ← Post-solve calculations (if exists)
  ├── scaling.gms        ← Equation scaling (if exists)
  └── not_used.txt       ← Files not used in current realization
```

**Read in this order**: declarations → input → preloop → presolve → equations

### Step 2: Trace Parameter Flow (20 min)

For each key parameter:

1. **Where is it loaded?** (input.gms)
2. **What input file?** (look for `$include` or `table` statements)
3. **How is it processed?** (preloop.gms, presolve.gms)
4. **Where is it used?** (equations.gms)

### Step 3: Verify Every Equation (30-60 min)

```bash
# Count equations
grep "^[ ]*qXX_" modules/XX_*/*/declarations.gms | wc -l
```

For **EVERY equation**:

1. ✅ **Name**: Matches declaration (qXX_equation_name)
2. ✅ **Dimensions**: Check set indices (t, j, kli, etc.)
3. ✅ **Formula**: Verify RHS matches source exactly
4. ✅ **Units**: Check parameter units in declarations
5. ✅ **Purpose**: Understand what it calculates

**Copy formulas directly from source code** - don't paraphrase!

### Step 4: Check Interface Variables (15 min)

For variables/parameters provided to other modules:

```bash
# Find variable declaration
grep "vm_varname" modules/XX_*/*/declarations.gms

# Verify it exists
grep "^vm_varname" modules/*/*/declarations.gms
```

For variables/parameters received from other modules:

```bash
# Check Phase 2 dependency matrix
cat core_docs/Module_Dependencies.md | grep "vm_varname"
```

### Step 4b: Verify Variable Name Accuracy (5 min)

Check that all GAMS variable names in the documentation are correct:

```bash
# Run automated checker for a specific module
python3 scripts/check_gams_variables.py --module XX
```

**Common error patterns** (see `core_docs/Bug_Taxonomy.md`):

1. **Prefix confusion**: `vm_` vs `v{N}_`, `pm_` vs `s{N}_`, `fm_` vs `p{N}_`
2. **Suffix truncation**: Dropping `_ac`, `_iso`, `_reg` from compound names
3. **Hallucinated names**: Advisory text invents plausible but non-existent variables
4. **Conceptual pseudo-code**: Using "intuitive" names instead of actual GAMS identifiers

**Rule**: Every backtick-quoted variable name MUST exist in `declarations.gms` or `input.gms`.
If using a conceptual name, annotate: "(conceptual, not actual GAMS variable)".

### Step 5: Document Limitations (10 min)

Explicitly state what the module does **NOT** do:

- Static vs. dynamic
- Simplified processes
- Uniform factors
- Missing feedbacks
- Geographic aggregation

### Step 6: Final Quality Check (5 min)

Use the checklist from `AGENT.md`:

- [ ] Cited file:line for every claim
- [ ] Used exact variable names
- [ ] Verified all equation formulas
- [ ] Checked interface variables
- [ ] Stated limitations
- [ ] No vague language
- [ ] Labeled examples as illustrative

---

## Spot Verification (Recovered Modules)

**Use when**: Verifying existing documentation quickly.

**Time**: 5-30 minutes per module

### Quick Check (5 min)

```bash
# 1. Count equations
grep "^[ ]*qXX_" modules/XX_*/*/declarations.gms | wc -l

# 2. Compare to documentation
# (Check "Equations" section in module doc)

# 3. Spot-check 2-3 equation names
grep "^[ ]*qXX_" modules/XX_*/*/declarations.gms | head -3

# 4. Verify those equations exist in doc
# (Search for equation names in documentation)
```

If counts match and sample equations are correct → **High confidence**

### Medium Check (15 min)

Quick check +

```bash
# 5. Read 1-2 equation formulas in equations.gms
# 6. Compare to documentation
# 7. Check 1 interface variable
grep "vm_varname" modules/XX_*/*/declarations.gms
# 8. Verify provider module exists in Phase 2 matrix
```

If formulas match → **Very high confidence**

### Deep Spot Check (30 min)

Medium check +

```bash
# 9. Read input.gms
# 10. Verify input files mentioned in doc
# 11. Check presolve.gms for parameter calculations
# 12. Verify 5-6 equations
# 13. Check limitation statements
```

If all match → **Full verification not needed immediately**

---

## Red Flags - Reject Module Doc

**Immediate rejection criteria**:

1. **Phantom equations**: Equation in doc doesn't exist in source
2. **Wrong formula**: Formula doesn't match source code
3. **Missing equations**: Equation count mismatch > 10%
4. **Wrong dimensions**: Set indices don't match
5. **Fake interface variables**: Claims variables that don't exist

**Action**: Document errors, reject module, start fresh verification.

**See**: `archive/MODULE_59_ERRORS_FOUND.md` for example

---

## Citation Standards

### File References

✅ **Correct** (always full-path `modules/NN_name/realization/file.gms:N`):
- `modules/22_biodiversity/bv_btc_mar21/equations.gms:45` (single line)
- `modules/22_biodiversity/bv_btc_mar21/equations.gms:45-52` (range)
- `modules/14_yields/managementcalib_aug19/presolve.gms:123-145`

❌ **Wrong**:
- "equations file" (too vague)
- "line 45" (which file?)
- `equations.gms:45` (bare basename — ambiguous in cross-module docs; Check 25 forbids) <!-- check-bare-cite -->

### Equation References

✅ **Correct**:
```markdown
The biodiversity intactness index is calculated in equation `q22_bii`:

```gams
q22_bii(j) .. vm_bii(j) =e= sum(land, pm_land_start(j,land) * f22_bii(land)) / sum(land, pm_land_start(j,land));
```

(Source: `modules/22_biodiversity/bv_btc_mar21/equations.gms:12-14`)
```

❌ **Wrong**:
```markdown
The BII is calculated by averaging land-type BII values.
```
(Missing: equation name, formula, citation)

### Parameter References

✅ **Correct**:
```markdown
`f22_bii(land)` - BII factor by land type (unitless, 0-1)
Source: `input/f22_bii.csv`, loaded in `modules/22_land_conservation/area_based_apr22/input.gms:34`
```

❌ **Wrong**:
```markdown
BII factors are loaded from input files.
```
(Missing: parameter name, file name, line number)

---

## Common Pitfalls

### 1. Confusing Ecological Facts with Model Implementation

❌ **Wrong**: "Forests sequester atmospheric carbon through photosynthesis"
✅ **Right**: "Carbon stocks are tracked via `pm_carbon_density(t,j,"forestry",c_pools)` with growth derived from `im_growing_stock(t,j,ac,land_timber)` (formerly *pm_timber_yield* before PR #869 rename on 2026-04-20)"

### 2. Assuming Features Exist

❌ **Wrong**: "MAgPIE models fire dynamics in natural vegetation"
✅ **Right**: "Fire impacts are NOT dynamically modeled; carbon loss from fire is parameterized via `f35_fire_loss(t,j)` (modules/35_natveg/pot_forest_may24/input.gms:45)"

### 3. Vague Interface Variable Claims

❌ **Wrong**: "The module receives land area from Module 10"
✅ **Right**: "Receives `vm_land(j,land)` from Module 10 (land), declared in `modules/10_land/*/declarations.gms:67`"

### 4. Invented Numerical Examples

❌ **Wrong**: "In Sub-Saharan Africa, BII drops from 0.8 to 0.4"
✅ **Right**: "To illustrate: if initial BII = 0.8 and cropland expands replacing natural vegetation (BII factor 0.3), BII decreases (example values for illustration only)"

### 5. Skipping Limitations

❌ **Wrong**: [No mention of simplifications]
✅ **Right**: "Limitations: (1) BII factors are uniform globally, (2) does NOT model species-specific dynamics, (3) land-use history beyond current state is not tracked"

---

## Verification Log Template

**Use this when verifying a module**:

```markdown
# Module XX Verification Log

**Date**: YYYY-MM-DD
**Verification Type**: Full / Spot / Deep Spot

## Source Files Read
- [ ] declarations.gms
- [ ] input.gms
- [ ] preloop.gms
- [ ] presolve.gms
- [ ] equations.gms

## Equation Count
- Source: XX equations (grep count)
- Documentation: YY equations
- Match: YES / NO

## Equations Verified
1. qXX_equation1 - ✅ Formula matches
2. qXX_equation2 - ✅ Formula matches
3. qXX_equation3 - ❌ Dimension mismatch (ERROR)
...

## Interface Variables Checked
- vm_varname1 - ✅ Exists in Module YY
- pm_param1 - ✅ Declared in Module ZZ
...

## Issues Found
- Issue 1 description
- Issue 2 description

## Decision
- [ ] APPROVED - Fully verified
- [ ] APPROVED - Spot-verified (needs full verification later)
- [ ] REJECTED - Errors found (documented in archive/)

## Notes
Any additional observations...
```

---

## After Verification

(R6 2026-05-25: CURRENT_STATE.json was retired as SSOT — use the live audit trail instead.)

1. ✅ Update `modules/module_XX.md` header (Realization, Verified Against footer)
2. ✅ Append the verification result to `audit/validation_rounds.json` if it happened as part of a semantic-flywheel round (otherwise it can be noted in the per-module notes file)
3. ✅ Update `modules/module_XX_notes.md` with any lessons learned
4. ✅ If errors found: append to `audit/global/agent_lessons.md` (system-wide) or `modules/module_XX_notes.md` (module-specific); commit with `fix(...)` prefix
5. ✅ If verification was part of a sync: update `project/sync_log.json` entry

---

**Remember**: Verification is not optional. Every module must be verified before being marked as complete.
