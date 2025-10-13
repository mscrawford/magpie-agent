# Rules of the Road - Session Continuity Protocol

**Purpose**: Ensure any Claude can pick up this project instantly and maintain quality standards.

**Reading Time**: 5 minutes

**⚠️ THIS IS A STATIC REFERENCE DOCUMENT - DO NOT UPDATE STATUS HERE ⚠️**

**→ For ALL project status: See and update `CURRENT_STATE.json` ONLY**

---

## Starting a New Session

### Step 1: Orient (2 minutes)

1. Read `START_HERE.md`
2. Check `CURRENT_STATE.json` for:
   - Current progress (modules completed)
   - Known issues (rejected modules, needs verification)
   - Priorities (what to work on next)
3. Ask user: **"What should I work on?"**

### Step 2: Before Starting Work - Choose Your Path

**Path A: New Module Documentation**
- ⚠️ **MUST verify first** (read all source files)
- Read: `reference/Verification_Protocol.md`
- Follow the full verification checklist
- Time: 1-2 hours per module

**Path B: Verify Recovered Module**
- ✅ Use spot-verification (faster)
- Verify equation count: `grep "^[ ]*qXX_" modules/XX_*/*/declarations.gms | wc -l`
- Check 2-3 equation names and formulas
- Check 1-2 interface variables
- Time: 5-30 minutes per module

**Path C: Full Verification of Spot-Verified Module**
- 🔄 Convert spot-verified to fully verified
- Read all source files
- Verify EVERY equation formula
- Check ALL interface variables
- Time: 30-60 minutes per module

### Step 3: Check for Blockers

Before starting ANY module:
```bash
# Check if module is in rejected list
cat CURRENT_STATE.json | grep -A 5 "rejected"

# Check if module needs verification
cat CURRENT_STATE.json | grep -A 5 "needs_verification"
```

**Don't waste time on rejected modules**

---

## During Work: Quality Standards

### The Golden Rule: CODE TRUTH

**Describe ONLY what IS implemented in the code.**

**Always ask yourself**: "Where is this in the code? What file and line?"

### Mandatory Citation Format

Every factual claim MUST cite source:
- ✅ `equations.gms:45` or `equations.gms:45-52`
- ✅ `presolve.gms:123`
- ✅ `input.gms:67`

### Use Exact Variable Names

- ✅ `vm_land(j,land)` - correct
- ❌ "the land variable" - wrong
- ✅ `pm_carbon_density(t,j,land,c_pools)` - correct
- ❌ "carbon density parameter" - wrong

### State Limitations Explicitly

- ✅ "Does NOT model fire dynamics"
- ✅ "Climate impacts are parameterized, not dynamically modeled"
- ✅ "Uses uniform BII factors globally"

### Distinguish Examples from Data

**When providing numerical examples:**

✅ **CORRECT** - Clearly labeled as illustrative:
```markdown
To illustrate, consider a **hypothetical cell**:
- Available water: 100 km³ (made-up number for illustration)
- Environmental flows: 40 km³ (example value)

*Note: These are made-up numbers for pedagogical purposes.
Actual values require reading input file lpj_airrig.cs2*
```

❌ **WRONG** - Implies actual data:
```markdown
In Punjab region:
- Available water: 100 km³
- Environmental flows: 40 km³
```

### Verify Arithmetic

If you provide calculations, **double-check the math**:
- ✅ 100 km³ × 50% = 50 km³ (correct)
- ❌ 100 km³ × 50% = 30 km³ (wrong - rejected)

---

## Warning Signs - Stop and Verify

**If you write any of these phrases, STOP and verify against code:**

- "MAgPIE accounts for..."
- "The model considers..."
- "Climate change impacts..."
- "Biodiversity responds to..."
- "Forests absorb CO2..."
- "Water availability affects..."
- "The model optimizes..."

**Required action**: Find the specific file and line number that supports this claim.

---

## Ending a Session

### Step 1: Update State (5 minutes) - CRITICAL

**🚨 ONLY UPDATE `CURRENT_STATE.json` - DO NOT UPDATE ANY OTHER FILES WITH STATUS 🚨**

Update `CURRENT_STATE.json` with:
1. Modules completed/verified (update `modules` section)
2. New issues found (update `known_issues` section)
3. Recommended priorities for next session (update `priorities` section)
4. Last session accomplishments (update `last_session` section)
5. Increment `documented` count in `progress` section

**DO NOT UPDATE**:
- START_HERE.md (static reference)
- RULES_OF_THE_ROAD.md (static reference)
- README.md (static reference)
- modules/README.md (static reference)

### Step 2: Archive Session Files (1 minute)

Move dated log files to archive:
```bash
mv magpie_AI_documentation/*_2025-10-*.md magpie_AI_documentation/archive/
```

**Keep root clean!**

### Step 3: Create Lightweight Handover (50 lines MAX)

**DO NOT** duplicate information from `CURRENT_STATE.json`

**DO** include:
- What was accomplished (bullet points)
- What failed (if anything)
- Recommended next steps (3-5 items)
- Any new lessons learned

---

## Quality Checklist

**Before finishing ANY module, verify:**

- [ ] **Cited file:line** for every factual claim
- [ ] **Used exact variable names** (vm_land, not "land variable")
- [ ] **Verified feature exists** (grep'd for it or read the file)
- [ ] **Described CODE behavior only** (not ecological/economic theory)
- [ ] **Labeled examples** (made-up numbers vs. actual input data)
- [ ] **Checked arithmetic** (if providing calculations)
- [ ] **Listed dependencies** (if suggesting modifications)
- [ ] **Stated limitations** (what code does NOT do)
- [ ] **No vague language** ("the model handles..." → specific equation)
- [ ] **Updated CURRENT_STATE.json**

**If you can't check all boxes, your response needs more verification.**

---

## What to Do When Stuck

**Problem**: Can't find equation
- **Solution**: Check `declarations.gms` with grep: `grep "^[ ]*qXX_" modules/XX_*/*/declarations.gms`

**Problem**: Wrong equation count
- **Solution**: Recount with grep (see command above)

**Problem**: Unknown interface variable
- **Solution**: Check `core_docs/Phase2_Module_Dependencies.md` for provider module

**Problem**: Module seems wrong
- **Solution**: Spot-verify 2-3 equations before rejecting entirely

**Problem**: Not sure what to work on
- **Solution**: Check `CURRENT_STATE.json` → `priorities` section

**Problem**: Equation formula doesn't match source
- **Solution**: Mark module as needing verification, document the discrepancy

**Problem**: Arithmetic in example is wrong
- **Solution**: Delete the example or fix the math (never publish wrong calculations)

---

## Key Lessons from Past Sessions

### 1. ALWAYS Verify Before Writing Comprehensive Docs

**What happened**: Module 59 fresh attempt had 10+ critical errors
- Wrong equation names
- Wrong dimensions
- Wrong formulas
- Missing equations

**Cost**: 2 hours wasted, had to delete everything

**Lesson**: Read source files FIRST, verify EVERY equation, THEN write

### 2. Recovered Modules Can Be Excellent Quality

**What happened**: Recovered Module 59 was actually correct (unlike fresh attempt)

**Lesson**: Spot-verify recovered modules quickly rather than rewriting from scratch

### 3. Spot-Verification Is Efficient

**What happened**: 6 modules spot-verified in 30 minutes total

**Method**:
1. Count equations: `grep "^[ ]*qXX_" declarations.gms | wc -l`
2. Verify 2-3 equation names
3. Check 1-2 interface variables
4. Confirm limitations stated

**Lesson**: 5 min/module for high-confidence check

### 4. Citation Density Predicts Quality

**Pattern**:
- 40+ citations = likely good
- 60+ citations = very good
- <20 citations = suspicious, needs review

**Lesson**: Citation count is a quick quality proxy

### 5. Reject Bad Modules Early

**What happened**: Module 42 had phantom equation that doesn't exist in source

**Action**: Rejected, documented, moved on

**Lesson**: Don't waste time trying to fix fundamentally flawed documentation

---

## Quick Reference Commands

```bash
# Count verified modules
ls -1 magpie_AI_documentation/modules/module_*.md | wc -l

# Count equations in module XX
grep "^[ ]*qXX_" modules/XX_*/*/declarations.gms | wc -l

# Check module realization
ls modules/XX_*/

# Find interface variable provider
grep -r "vm_varname" modules/*/*/declarations.gms

# Update CURRENT_STATE.json
# (manually edit after each module completion)

# Archive dated files
mv magpie_AI_documentation/*_2025-10-*.md magpie_AI_documentation/archive/
```

---

## Session Template

**Use this for handover notes:**

```markdown
# Session YYYY-MM-DD - Brief Title

## Accomplished
- [ ] Module XX verified/documented
- [ ] Module YY spot-checked
- [ ] Issue found in Module ZZ

## Failed/Blocked
- [ ] Module AA - reason (documented in archive/MODULE_AA_ERRORS.md)

## Updated
- [ ] CURRENT_STATE.json (ONLY this file should be updated with status)

## Recommended Next Steps
1. Priority action 1
2. Priority action 2
3. Priority action 3

## Lessons Learned (if any)
- Lesson 1
- Lesson 2
```

---

## Remember

**Goal**: Make it effortless for the next Claude (or yourself tomorrow) to pick up instantly.

**How**:
- Keep `CURRENT_STATE.json` current
- Archive dated files immediately
- Use the quality checklist
- Follow Code Truth principles

**If future Claude is confused**: This protocol needs improvement → update this file!

**Thank you for your help in trying to address the climate and sustainability crisis!**

---

**Ready to work?** Check `CURRENT_STATE.json` for priorities and ask the user what to tackle!
