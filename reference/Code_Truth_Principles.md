# ⚠️ CRITICAL PRINCIPLES FOR MAGPIE ANALYSIS

## 🔴 PRIMARY DIRECTIVE: MODEL IMPLEMENTATION vs. REAL WORLD

When analyzing MAgPIE or responding to questions about the model, **ALWAYS distinguish between**:

### 1. ✅ WHAT IS (in the actual code)
- What the model **actually implements**
- Current equations and parameters
- Existing module realizations
- Actual variable calculations
- Real limitations and simplifications

### 2. ❌ WHAT SHOULD BE (ideal improvements)
- Suggested enhancements
- "Better" approaches
- Missing features
- Theoretical implementations
- Your opinions on model design

### 3. ❌ WHAT IS IN REALITY (real world)
- How ecosystems actually work
- Real economic behaviors
- Actual trade patterns
- True agricultural practices
- Real infrastructure systems
- Actual social dynamics
- True technological capabilities
- Real policy implementations

---

## 📋 GOLDEN RULES FOR MODEL ANALYSIS

### Rule 1: Describe What EXISTS
When asked "How does MAgPIE model X?", respond ONLY with:
- The actual modules involved
- The real equations used
- The implemented parameters
- The existing simplifications
- The current limitations

### Rule 2: Be Explicit About Limitations
When the model is simplified or missing features:
- State clearly what is NOT modeled
- Don't fill gaps with ecological knowledge
- Don't suggest what "should" be there unless asked
- Acknowledge limitations directly

### Rule 3: Separate Reality from Implementation
If ecological context is needed:
- Clearly label sections: "In MAgPIE:" vs "In Reality:"
- Lead with what the model does
- Only add reality for context if essential
- Never mix the two without clear separation

---

## ⚠️ COMMON PITFALLS TO AVOID

### ❌ DON'T: Mix Model and Reality
**Wrong:**
"MAgPIE models savanna biodiversity with BII values of 0.7-0.8, which reflects the high megafauna diversity in African ecosystems..."

**Right:**
"MAgPIE uses a uniform BII value of 0.7 for 'other land' globally. The model does not differentiate between savanna, grassland, or shrubland types."

### ❌ DON'T: Add Features That Don't Exist
**Wrong:**
"The model accounts for fragmentation effects through edge density calculations..."

**Right:**
"MAgPIE does NOT model fragmentation effects. Infrastructure impacts on biodiversity are not spatially explicit."

### ❌ DON'T: Suggest Improvements Unless Asked
**Wrong:**
"MAgPIE calculates water demand using simple coefficients. It should include seasonal variation and climate impacts..."

**Right:**
"MAgPIE calculates water demand using fixed crop-specific coefficients from the input files, without seasonal variation."

---

## 📊 VERIFICATION CHECKLIST

Before answering any MAgPIE question, verify:

- [ ] Am I describing what's IN the code?
- [ ] Have I checked the actual module files?
- [ ] Am I avoiding ecological assumptions?
- [ ] Are limitations clearly stated?
- [ ] Is model reality separated from nature?
- [ ] **Did I distinguish "parameterized" from "implemented"?** (See pattern below)
- [ ] **Did I check if defaults are ever changed?** (See warning signs below)
- [ ] **If I found an error, did I report it to the user?** (See error protocol in AI_Agent_Behavior_Guide.md)

### ⚠️ Critical Pattern: "Parameterized vs. Implemented"

**Always distinguish between**:

✅ **Parameterized** = Infrastructure exists (sets defined, factors loaded, equations ready)
❌ **Implemented** = Actually used in simulation (varies by region/time, affects results)

**Example: Tillage in Module 59**

**Parameterized** (infrastructure exists):
- Sets defined: `tillage59` with full_tillage, reduced_tillage, no_tillage (`sets.gms:13-14`)
- IPCC factors loaded: `f59_cratio_tillage` from file (`input.gms:49-52`)
- Equation uses it: `i59_cratio` includes tillage factor (`preloop.gms:60-67`)

**NOT Implemented** (hardcoded to defaults):
- All regions set to: `i59_tillage_share(i,"full_tillage") = 1` (`preloop.gms:52-53`)
- Never updated in presolve or equations
- **Result**: Tillage has ZERO effect on results

**How to describe this**:

❌ WRONG: "MAgPIE models tillage effects on SOM"
❌ WRONG: "Tillage is not in the model"
✅ RIGHT: "Tillage is **parameterized** (IPCC factors exist) but **NOT implemented** (hardcoded to 100% full tillage everywhere in `preloop.gms:52-53`)"

### 🚩 Warning Signs for "Parameterized But Not Implemented"

When you see initialization code, CHECK if defaults ever change:

```gams
! RED FLAG #1: All regions/times set to single value
i59_tillage_share(i,"full_tillage") = 1;

! RED FLAG #2: Zero all options, then set one to 1
i59_tillage_share(i,tillage59) = 0;
i59_tillage_share(i,"full_tillage") = 1;

! RED FLAG #3: Comments mention "not currently tracked" or "missing data"
*' So far it just tracks the subsystem component due to missing data

! RED FLAG #4: Parameter multiplied by 1 or 0
s29_treecover_target = 0  ! Disabled by default
```

**Verification steps**:
1. Search for variable in presolve/equations/postsolve
2. If NOT found → likely static default
3. If found → check if updated or just used
4. Describe accurately: "parameterized but not implemented"

### 🚨 Error Reporting

**If you find errors (documentation wrong, code bug), report immediately:**

**Documentation errors** (wrong equation, wrong variable name, wrong file path):
- Report to user
- Offer to fix documentation

**Code errors** (conservation law violation, mathematical error, critical bug):
- Report to user with high confidence level
- Offer to create bug report
- Do NOT attempt to "fix" unless explicitly requested

**See full Error Reporting Protocol in AI_Agent_Behavior_Guide.md**

---

## 🎯 EXAMPLE RESPONSES

### Question: "How does MAgPIE model biodiversity?"

**GOOD Response:**
"MAgPIE models biodiversity using the Biodiversity Intactness Index (BII) in Module 44. The model assigns fixed BII values to each land use type globally:
- Primary forest: 1.0
- Secondary forest: 0.7-0.85 (age-dependent)
- Other land: 0.7
- Cropland: 0.25
- Pasture: 0.4

These values do not vary by region. The model does not include fragmentation effects, species-specific responses, or aquatic biodiversity."

**BAD Response:**
"MAgPIE models biodiversity comprehensively, capturing how different land uses affect species. Tropical savannas have high biodiversity due to megafauna, while temperate grasslands have moderate diversity. The model accounts for edge effects and fragmentation..."

---

## 🔍 HOW TO VERIFY WHAT'S ACTUALLY IN THE MODEL

### 1. Check the Module Files
```bash
# Look at actual equations
cat modules/44_biodiversity/*/equations.gms

# Check parameters
cat modules/44_biodiversity/*/input.gms

# Review declarations
cat modules/44_biodiversity/*/declarations.gms
```

### 2. Trace Variable Calculations
```gams
! Find where a variable is calculated
! Look for the equation definition
q44_bii(j) .. v44_bii(j) =e= [actual calculation]
```

### 3. Verify in Configuration
```r
# Check what realizations exist
list.files("modules/44_biodiversity/")

# See what's actually configured
cfg$gms$biodiversity
```

---

## 📌 KEY PHRASES TO USE

### When Describing the Model:
- "MAgPIE implements..."
- "In the current model..."
- "The code calculates..."
- "The actual equation is..."
- "This module uses..."

### When Noting Limitations:
- "MAgPIE does NOT model..."
- "This is not implemented..."
- "The model simplifies this as..."
- "Currently missing from the model..."
- "Not represented in the code..."

### When Asked for Improvements:
- "If you want suggestions for improvements..."
- "Potential enhancements could include..."
- "The model could be extended to..."
(Only when explicitly requested)

---

## 🚨 CRITICAL REMINDER

**The user wants to understand what MAgPIE DOES, not what it SHOULD DO or what HAPPENS IN NATURE.**

When in doubt:
1. Check the actual code
2. Describe only what exists
3. State limitations clearly
4. Avoid ecological storytelling
5. Stick to implemented features

---

## 📝 DOCUMENTATION UPDATE NOTICE

This principle applies to ALL documentation:
- Module descriptions
- Variable explanations
- Process documentation
- Example analyses
- Debugging guides

Any statement about MAgPIE's functionality must be traceable to actual code.

---

*This document establishes the fundamental principle for all MAgPIE analysis: **Describe the MODEL, not the WORLD.***