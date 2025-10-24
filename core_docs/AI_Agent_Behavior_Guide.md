# AI Agent Behavior Guide for MAgPIE
## Quick Reference for Intelligent Assistance

**Purpose**: This guide provides immediate, actionable patterns for AI agents working with MAgPIE. It's designed to be referenced directly during conversations.

**Last Updated**: October 13, 2025

---

## 🎯 FUNDAMENTAL RULE: CODE TRUTH OVER EVERYTHING

**ALWAYS describe what MAgPIE DOES, not what it SHOULD do or what happens in nature.**

❌ WRONG: "MAgPIE accounts for edge effects in forests" (if it doesn't)
✅ RIGHT: "MAgPIE does NOT currently model edge effects. Carbon density depends only on age class (modules/35_natveg/.../presolve.gms:218-220)"

❌ WRONG: "Forests provide ecosystem services" (ecology)
✅ RIGHT: "Module 35 calculates timber harvest at modules/35_natveg/pot_forest_may24/equations.gms:140-143"

---

## 🚨 ERROR REPORTING PROTOCOL

**If you discover errors during analysis, notify the user immediately.**

### When to Report Errors:

**Documentation Errors** (incorrect info in magpie-agent/):
- Equation formula doesn't match source code
- Variable name is wrong
- File path is incorrect
- Outdated information after code changes

**Code Errors** (critical issues in actual MAgPIE code):
- Conservation law violations (land/water/carbon balance broken)
- Mathematical errors (wrong formula, sign errors)
- Inconsistent units
- Missing critical constraints
- Variable declared but never used/calculated

### Error Reporting Template:

When you find an error, say:

> "⚠️ **I've found a [documentation/code] error that needs attention:**
>
> **Error Type**: [Brief description]
> **Location**: [file:line]
> **Issue**: [What's wrong]
> **Evidence**: [What you checked to confirm]
> **Impact**: [Severity - critical/moderate/minor]
>
> Would you like me to:
> - (a) Create a bug report for this issue
> - (b) Fix the documentation (if documentation error)
> - (c) Both"

### Confidence Levels:

**Report if**:
- ✅ **Very certain** (verified against multiple sources, clear mathematical error)
- ✅ **High confidence** (verified against code, inconsistency confirmed)

**Don't report if**:
- ❌ Uncertain (might be your misunderstanding)
- ❌ Design choice you disagree with (not an error, just different approach)
- ❌ Missing feature (limitation, not bug - describe as "NOT modeled" instead)

### Examples:

**SHOULD REPORT**:
- Documentation says equation uses addition, code shows multiplication
- Variable declared as `vm_X` but documentation calls it `pm_X`
- Conservation law: sum(land) should equal total, but constraint missing

**SHOULD NOT REPORT**:
- "Tillage is parameterized but hardcoded to defaults" (limitation, not error)
- "I think the model should include edge effects" (opinion, not error)
- "Docs don't mention Feature Y" (might just not be documented yet - ask user first)

---

## 🚀 INSTANT QUERY ROUTING (Use This First)

**Available Documentation** (all in `magpie-agent/`):
- **Phase 0 (Foundation)**: `core_docs/` - Architecture, dependencies, data flow
- **Phase 1 (Modules)**: `modules/module_XX.md` - All 46 modules documented
- **Phase 2 (Cross-Module)**: `cross_module/` - Conservation laws, safety, circular deps

```
User Query → Pattern Match → Where to Look

"How does [X] work?" / "What is [X]?"
  └─> MODULE DETAIL: modules/module_XX.md (if module-specific)
  └─> OR: core_docs/Phase1_Core_Architecture.md (if general structure)

"What happens after [X]?" / "How does [X] change over time?"
  └─> TEMPORAL DYNAMICS: Trace initial state → transition → convergence
  └─> Start: modules/module_XX.md (find equations)
  └─> Context: core_docs/Phase1_Core_Architecture.md (execution phases)

"How does [X] affect [Y]?" (across modules)
  └─> CROSS-MODULE: Trace variable chain from X's module to Y's module
  └─> Start: modules/module_XX.md (interface variables)
  └─> Then: core_docs/Phase2_Module_Dependencies.md (dependency paths)
  └─> OR: cross_module/circular_dependency_resolution.md (if feedback loop)

"Is [X] modeled?" / "Does MAgPIE account for [X]?"
  └─> PARAMETERIZED vs IMPLEMENTED: Check module docs for limitations
  └─> modules/module_XX.md (limitations section)

"What depends on [X]?" / "[X] depends on what?"
  └─> DEPENDENCY: core_docs/Phase2_Module_Dependencies.md
  └─> Lists all 173 dependencies, 26 circular cycles

"Where is [X] defined?" / "Which file has [X]?"
  └─> DATA: core_docs/Phase3_Data_Flow.md (if input parameter)
  └─> CODE: modules/module_XX.md (if variable/equation)

"[X] is broken" / "Error [Y]"
  └─> DEBUG: cross_module/circular_dependency_resolution.md (oscillations)
  └─> OR: cross_module/modification_safety_guide.md (infeasibility)

"How to modify [X]?" / "Add [Y] to MAgPIE"
  └─> MODIFICATION:
  └─> 1. modules/module_XX.md (understand current code)
  └─> 2. core_docs/Phase2_Module_Dependencies.md (check dependencies)
  └─> 3. cross_module/modification_safety_guide.md (safety protocols)

"Can I change module [X] without breaking [Y]?"
  └─> SAFETY: cross_module/modification_safety_guide.md
  └─> Covers modules 10, 11, 17, 56 (highest risk)

"Is [conservation law] enforced?"
  └─> CONSERVATION: cross_module/[law]_balance_conservation.md
  └─> land, water, carbon, nitrogen, food balance docs available
```

---

## 📋 RESPONSE CHECKLIST (Run Before Every Answer)

### ✓ Accuracy
- [ ] Did I cite specific file paths? (e.g., `modules/35_natveg/pot_forest_may24/presolve.gms:132`)
- [ ] Did I use actual variable names? (vm_land, pm_carbon_density, not "land variable")
- [ ] Did I check if this actually exists in code? (not assume)
- [ ] Did I avoid ecological/economic/general knowledge? (CODE behavior only)

### ✓ Dependencies (If modification suggested)
- [ ] Did I check Phase2_Module_Dependencies.md for affected modules?
- [ ] Did I list affected modules?
- [ ] Did I warn if high-centrality module (10, 11, 17, 56)?
- [ ] Did I warn if circular dependency involved?

### ✓ Completeness
- [ ] Did I provide line numbers for code references?
- [ ] Did I explain units if relevant?
- [ ] Did I offer next-level detail if answer was high-level?
- [ ] Did I reference conservation laws if modification affects mass/land/water balance?

### ✓ Safety (If code modification)
- [ ] Will this break land balance? (sum(land) = total)
- [ ] Will this break water balance? (use ≤ supply)
- [ ] Will this break food balance? (production + trade ≥ demand)
- [ ] Did I suggest testing scope?
- [ ] Did I recommend scaling if new variable?

---

## 🌲 MODULE-SPECIFIC QUICK PATTERNS

### Pattern: Module Dependency Check
```
BEFORE suggesting any modification to module X:

1. Check core_docs/Phase2_Module_Dependencies.md
2. List upstream (X depends on these):
   - These provide data TO module X
3. List downstream (these depend on X):
   - These consume data FROM module X
   - These need testing if X changes
4. Check centrality:
   - High (>15 connections): WARN - broad impact
   - Medium (5-15): Note dependent modules
   - Low (<5): Relatively isolated
5. Check circular dependencies:
   - If X in a cycle: WARN - test entire cycle together
```

### Pattern: Code Location Response
```
Structure for "Where is X?":

1. Primary location: modules/YY_name/realization/file.gms:line_start-line_end
2. Variable type:
   - vm_ = optimization variable (declared in declarations.gms)
   - pm_ = processed parameter (calculated in presolve.gms)
   - f_ = file input (loaded in input.gms)
   - s_ = scalar switch (set in input.gms)
3. Related locations:
   - Declared: declarations.gms
   - Calculated: presolve.gms or equations.gms
   - Used in: [list other modules from Phase2_Module_Dependencies.md]
4. Offer: "Would you like to see the actual code?"
```

### Pattern: Modification Suggestion
```
Structure for "How to modify X?":

**CURRENT BEHAVIOR** (cite code):
- File: modules/.../file.gms:line
- Code: [show actual snippet]
- Behavior: [describe what happens]

**PROPOSED MODIFICATION**:
- Change: [specific edit]
- Rationale: [why this achieves user's goal]

**DEPENDENCIES AFFECTED** (from Phase 2):
- Modules that depend on X: [list]
- Variables that connect: [list vm_/pm_]

**TESTING REQUIRED**:
- Run with: [suggest config]
- Check: [list outputs to validate]
- Validate: [conservation laws to verify]

**IMPLEMENTATION STEPS**:
1. Edit: [file:line]
2. If new variable: Add to declarations.gms, add scaling
3. Test: Start with 2-3 timesteps only
4. Validate: Check modelstat ≤ 2, check [balance equations]
```

---

## 🔍 ADVANCED PATTERN RECOGNITION

**These patterns emerged from real questions and help distinguish infrastructure from implementation, trace mechanisms across modules, and identify temporal dynamics.**

### Pattern: "Parameterized vs. Implemented" Detection

**Use when**: User asks "Is X modeled?" or "Does MAgPIE account for X?"

**Critical Distinction**: Something can be **parameterized** (infrastructure exists) but **NOT implemented** (hardcoded to defaults).

**Detection Workflow**:

1. ✅ **Check if sets exist**
   ```bash
   grep "tillage59\|inputs59" modules/59_som/*/sets.gms
   ```
   → Example: `tillage59` defined with full_tillage, reduced_tillage, no_tillage

2. ✅ **Check if factors loaded**
   ```bash
   grep "f59_cratio_tillage\|f59_cratio_inputs" modules/59_som/*/input.gms
   ```
   → Example: IPCC 2019 factors loaded from files

3. ✅ **Check if used in equations**
   ```bash
   grep "i59_cratio" modules/59_som/*/preloop.gms
   ```
   → Example: Tillage factor multiplied in carbon ratio calculation

4. ⚠️ **CRITICAL: Check if shares are hardcoded**
   ```gams
   i59_tillage_share(i,tillage59) = 0;
   i59_tillage_share(i,"full_tillage") = 1;  ← RED FLAG!
   ```
   → If set to single value everywhere = NOT actively modeled

5. 🔍 **Verify if ever changed**
   ```bash
   grep "i59_tillage_share" modules/59_som/*/{presolve,equations}.gms
   ```
   → If no results = never updated after initialization

**Response Pattern - If Parameterized But Not Implemented**:

> "Tillage is **parameterized** (IPCC factors loaded from `f59_ch5_F_MG.csv`, equation structure supports variation) but **NOT actively modeled** (hardcoded to 100% full tillage in `preloop.gms:52-53`).
>
> The infrastructure exists to support tillage variation:
> - Sets defined: full_tillage, reduced_tillage, no_tillage (`sets.gms:13-14`)
> - IPCC factors: No-tillage could increase SOM by 10-22% (`f59_ch5_F_MG.csv`)
> - Equation ready: Factor included in `i59_cratio` calculation (`preloop.gms:60-67`)
>
> However, the implementation does NOT use this capability:
> - All regions set to `i59_tillage_share(i,"full_tillage") = 1` (`preloop.gms:52-53`)
> - Never updated in presolve or equations
> - Result: Tillage has **zero effect** on SOM in current implementation
>
> To enable tillage modeling, you would need to replace the hardcoded defaults with either:
> - Regional input data (read from file)
> - Optimization variables (endogenize tillage choice)
> - Scenario switches (policy-driven adoption)"

**Warning Signs** (check these whenever you see initialization code):

```gams
! RED FLAG #1: All regions set to same value
i59_tillage_share(i,"full_tillage") = 1;

! RED FLAG #2: Single option selected from multiple
i59_tillage_share(i,tillage59) = 0;  ! Zero all first
i59_tillage_share(i,"full_tillage") = 1;  ! Then only one to 1

! RED FLAG #3: Comment mentions limitation
*' So far it just tracks the subsystem component due to missing data

! RED FLAG #4: Parameter multiplied by 1 or 0 everywhere
s29_treecover_target = 0  ! Disabled by default
```

**Examples in MAgPIE**:
- ✅ **Tillage**: Parameterized, hardcoded defaults (`modules/59_som/cellpool_jan23/preloop.gms:52-53`)
- ✅ **Input management**: Parameterized, hardcoded defaults (`modules/59_som/cellpool_jan23/preloop.gms:54-55`)
- ✅ **Tree cover on cropland**: Parameterized AND implemented (optimized with targets/costs)

---

### Pattern: Cross-Module Mechanism Tracing

**Use when**: User asks "How does X affect Y?" where X and Y are in different modules

**Example**: "How does tree cover affect soil organic matter?"

**Tracing Workflow**:

1. **Identify starting module** (where X is calculated/optimized):
   ```bash
   grep -r "vm_treecover" modules/*/*/declarations.gms
   ```
   → Result: Module 29 (Cropland) declares and optimizes `v29_treecover(j,ac)`

2. **Find interface variable** (what X provides to other modules):
   - Module 29 provides `vm_treecover(j)` = sum across age classes
   - Check: `equations.gms:83-84` shows aggregation equation

3. **Search for downstream usage** (where interface variable is consumed):
   ```bash
   grep -r "vm_treecover" modules/*/*/equations.gms
   ```
   → Result: Module 59 uses it in `q59_som_target_cropland`

4. **Trace parameter chain** (how X is transformed/used):
   - Module 59: `equations.gms:26` includes `vm_treecover * i59_cratio_treecover`
   - Check: `preloop.gms:82` shows `i59_cratio_treecover = 1` (100% natural carbon)

5. **Follow to final effect** (ultimate impact):
   - Higher SOM equilibrium in Module 59
   - Aggregated into soil carbon stocks by Module 52
   - Reported as `vm_carbon_stock(j,"crop","soilc")`

**Response Pattern**:

> "Tree cover affects SOM through this mechanism chain:
>
> **1. Module 29** (Cropland) - Tree cover optimization:
> - Variable: `v29_treecover(j,ac)` by age class
> - Equation: `q29_treecover` aggregates to `vm_treecover(j)`
> - Location: `modules/29_cropland/detail_apr24/equations.gms:83-84`
>
> **2. Module 59** (SOM) - SOM equilibrium calculation:
> - Uses: `vm_treecover` in cropland SOM target
> - Formula: `vm_treecover × i59_cratio_treecover × f59_topsoilc_density`
> - Where: `i59_cratio_treecover = 1.0` (100% of natural carbon)
> - Location: `modules/59_som/cellpool_jan23/equations.gms:26`, `preloop.gms:82`
>
> **3. Module 52** (Carbon) - Stock aggregation:
> - Aggregates SOM from Module 59 into total soil carbon
> - Reports: `vm_carbon_stock(j,"crop","soilc",stockType)`
>
> **Net Effect**: Trees on cropland restore SOM to **100% of natural levels**, compared to typical cropland at 60-80% of natural (depending on crop and management)."

**Key Insight**: Always trace the FULL chain - don't stop at first module that uses the variable.

---

### Pattern: Temporal Mechanism Questions

**Use when**: User asks "What happens after X?" or "How does X change over time?"

**Different from static questions**:
- ❌ "What is deforestation?" → Static definition
- ✅ "What happens to SOM after deforestation?" → Temporal dynamics

**Response Structure for Temporal Questions**:

**1. Initial State** (before event):
```
Before: Forest with SOM = natural topsoil density
Location: Module 59, q59_som_target_noncropland (equations.gms:31-34)
Value: vm_land(j,"forest") × f59_topsoilc_density(ct,j)
```

**2. Transition Mechanism** (the event):
```
Transition: Forest → cropland via land-use transition matrix
Tracked by: vm_lu_transitions(j,"forest","crop")
Location: Module 10 (Land), used in Module 59 equations
```

**3. Convergence Dynamics** (movement toward new state):
```
Convergence: 15% annual movement toward new equilibrium
Formula: i59_lossrate(t) = 1 - 0.85^timestep_length
Location: modules/59_som/cellpool_jan23/preloop.gms:45

Rates:
- 5 years: 44% of gap closed (56% of difference remains)
- 10 years: 80% of gap closed
- 20 years: 96% of gap closed (essentially at equilibrium)
```

**4. New Equilibrium** (final stable state):
```
After: Cropland with SOM = crop_carbon_ratio × natural_density
Location: Module 59, q59_som_target_cropland (equations.gms:20-27)
Typical: 60-80% of natural level (depends on crop, tillage, inputs)
```

**5. Timeframe** (how long until equilibrium):
```
Practical equilibrium: ~20 years (96% convergence)
Mathematical equilibrium: Never fully reached (exponential decay)
```

**Example Response**:

> "After deforestation (forest → cropland conversion), SOM undergoes gradual convergence to a new, lower equilibrium:
>
> **Initial state**: Forest maintains SOM at natural topsoil C density (~100 tC/ha, illustrative)
>
> **Transition**: Land-use conversion tracked by `vm_lu_transitions(j,"forest","crop")`
>
> **Convergence dynamics** (`preloop.gms:45`):
> - Rate: 15% annual movement toward new equilibrium
> - Formula: `i59_lossrate(t) = 1 - 0.85^timestep_length`
> - Timeline: 44% convergence in 5 years, 80% in 10 years, 96% in 20 years
>
> **New equilibrium**: Cropland SOM = crop-specific ratio × natural density
> - Typical: 60-80% of natural level (depends on crop type, tillage, input management)
> - Calculated in `q59_som_target_cropland` (`equations.gms:20-27`)
>
> **Net carbon loss**: ~20-40% of original SOM over 10-20 years
>
> *Note: Actual values depend on cell-specific natural carbon density and crop management factors.*"

**Key Insight**: Temporal questions require tracing through **initial state → transition → convergence path → final equilibrium**, not just describing the equation structure.

---

### Pattern: Policy Implementation Mechanisms

**Use when**: User asks about policy features, targets, or constraints

**Three Main Patterns in MAgPIE**:

**Pattern A: Target + Penalty (Soft Constraint)**

Example: Tree cover target in Module 29

**Characteristics**:
- Target can be violated if costs too high
- Optimization balances target vs. opportunity cost
- Penalty drives adoption

**Detection**: Look for `*_target`, `*_missing`, `*_penalty` variables

**Example Code**:
```gams
! Target equation
q29_treecover_min(j2)..
  v29_treecover_missing(j2) =g=
    vm_land(j2,"crop") * i29_treecover_target(ct,j2) - sum(ac, v29_treecover(j2,ac));

! Cost equation
q29_cost_cropland(j2)..
  vm_cost_cropland(j2) =e= ... + v29_treecover_missing(j2) * i29_treecover_penalty(ct);
```

**Pattern B: Hard Constraint**

Example: Land balance constraint

**Characteristics**:
- Cannot be violated at any cost
- Model infeasible if constraint can't be satisfied
- Ensures physical/accounting laws

**Detection**: Look for constraint equations (`=e=`, `=l=`, `=g=`) without cost terms

**Example Code**:
```gams
q10_land(j2)..
  sum(land, vm_land(j2,land)) =e= sum(ct, f10_land(j2));
```

**Pattern C: Cost-Based Optimization**

Example: Production decisions with factor costs

**Characteristics**:
- No explicit target
- Level determined by marginal cost = marginal benefit
- Market-driven, endogenous decisions

**Detection**: Look for cost variables in objective, no target constraints

**Example Code**:
```gams
q38_cost_prod_crop(j2,kcr)..
  vm_cost_prod_crop(j2,kcr) =e=
    vm_prod(j2,kcr) * i38_fac_req(kcr) * pm_factor_costs(j2);
```

**When describing policies**: Always specify which pattern is used. Example:

> "Tree cover targets use **Pattern A: Target + Penalty** (`modules/29_cropland/detail_apr24/`):
> - Target: `s29_treecover_target` (default 0, can be set to 0-1)
> - Missing calculation: target × cropland - actual tree cover
> - Penalty: 6150 USD/ha for violation (`input.gms:28`)
> - Result: Target can be missed if costs too high, but penalty incentivizes adoption"

---

### Pattern: Default Value Investigation

**Use when**: You see initialization or default values being set in code

**Verification Workflow**:

**Step 1**: Identify the default setting
```gams
i59_tillage_share(i,"full_tillage") = 1;  ← Setting found
```

**Step 2**: Search for variable in later execution phases
```bash
grep "i59_tillage_share" modules/59_som/cellpool_jan23/{presolve,postsolve,equations}.gms
```

**Step 3**: Check if recalculated or updated
- If found → Check if it's updated or just used
- If not found → Likely static default

**Step 4**: Check configuration files
```bash
grep -r "tillage" config/*.R  # Check if scenario switches exist
```

**Step 5**: Make determination
- **Static default**: Never changed → NOT actively modeled
- **Conditionally varied**: Updated based on switches → Parameterized but optional
- **Actively modeled**: Always updated/optimized → Fully implemented

**Response Pattern if Static Default**:

> "The parameter `i59_tillage_share` is initialized to 100% full tillage in `preloop.gms:52-53` and **never subsequently updated**.
>
> Verification:
> - Searched presolve.gms: Not found
> - Searched equations.gms: Not found
> - Searched postsolve.gms: Not found
> - Searched config files: No scenario switches
>
> **Conclusion**: While infrastructure exists (sets defined, IPCC factors loaded), tillage is **not actively modeled**—it remains at the hardcoded default throughout the simulation.
>
> To enable tillage variation, you would need to modify `preloop.gms` to either:
> - Read regional/temporal tillage data from input files
> - Create optimization variables for endogenous tillage choice
> - Add scenario switches for policy-driven tillage adoption"

---

## 🐛 DEBUGGING DECISION TREE

```
Model fails?
│
├─ modelstat = 4 (INFEASIBLE)
│  ├─ Check which timestep failed
│  ├─ Display binding constraints: .m > 0
│  ├─ Common causes:
│  │  ├─ Land balance: sum(land) ≠ total_available
│  │  ├─ Water shortage: watdem > watavail
│  │  ├─ Food deficit: production < demand
│  │  └─ Incompatible bounds: .lo > .up
│  └─ Fix strategy:
│     ├─ Relax constraint temporarily (find root cause)
│     ├─ Check data integrity (NaN, Inf, negative where positive expected)
│     └─ Reduce timesteps to isolate problem period
│
├─ modelstat = 3 (UNBOUNDED)
│  ├─ Missing cost terms in objective
│  ├─ Missing upper bounds on variables
│  └─ Check: vm_cost_glo has all components
│
├─ modelstat = 13 (ERROR)
│  ├─ GAMS syntax error: Check .lst file
│  ├─ Division by zero: Check denominators
│  └─ Set domain violation: Check set membership
│
└─ modelstat = 1-2 but results unrealistic
   ├─ Check conservation:
   │  ├─ Land: sum over j (vm_land) = available area
   │  ├─ Water: sum(use) ≤ supply
   │  ├─ Carbon: emissions = Δstock + combustion
   │  └─ Food: production + trade ≥ demand
   ├─ Check magnitudes:
   │  ├─ Land: 0-1500 Mha typical per region
   │  ├─ Emissions: 0-2000 Mt C/yr typical per region
   │  └─ Costs: 0-500 billion USD/yr typical per region
   └─ Compare to historical (2015 should match FAO)
```

---

## 📊 DATA FLOW TRACING

### How to trace a parameter through MAgPIE:

```
User asks: "Where does X come from?"

1. Identify prefix:
   f_ → Input file (check core_docs/Phase3_Data_Flow.md or modules/.../input.gms)
   i_ → Interpolated/processed from f_ (check preloop.gms or input.gms)
   p_ → Calculated per timestep (check presolve.gms)
   pm_ → Passed between modules (check Phase2_Module_Dependencies.md for provider)
   vm_ → Optimization variable (check declarations.gms + equations.gms)
   o_ → Output (calculated in postsolve.gms from vm_)

2. Find source module:
   - Phase2_Module_Dependencies.md shows which module provides pm_X
   - modules/module_XX.md show internal calculations

3. Trace backwards:
   vm_X ← calculated by equation q_X ← uses pm_Y ← provided by module Z ← from f_Y

4. Provide complete chain:
   "vm_land comes from the optimization (Module 10).
    It's constrained by pm_land_conservation (Module 22).
    pm_land_conservation is processed from f22_conservation (input file).
    Source: modules/22_land_conservation/.../input.gms:XX"
```

---

## 🎨 RESPONSE STYLE GUIDE

### ✅ DO:

**Be specific**:
- "Module 35 calculates forest area at modules/35_natveg/pot_forest_may24/presolve.gms:82-92"
- NOT: "MAgPIE tracks forests"

**Use actual names**:
- "vm_land(j,'primforest') represents primary forest area in million hectares"
- NOT: "the land variable for forests"

**Cite dependencies**:
- "Module 35 provides vm_land('primforest') to Module 52 (carbon) and Module 56 (ghg_policy). See Phase 2 dependency matrix."
- NOT: "This connects to other modules"

**Warn about impacts**:
- "Module 11 has 27 dependencies (highest centrality). Modifying it requires testing: 10, 17, 21, 29, 32, 34, 35, 38, 39, 41, 42, 50, 52, 56, 58, 59, 70, 73, 80."
- NOT: "Be careful with this module"

**Offer detail levels**:
- "Would you like: (1) Just the file location? (2) The equation details? (3) Full modification workflow?"
- NOT: [dumps everything at once]

### ❌ DON'T:

**Don't describe ecology**:
- ❌ "Forests absorb CO2 through photosynthesis"
- ✅ "Module 52 calculates carbon stock from vm_land × fm_carbon_density"

**Don't assume features**:
- ❌ "MAgPIE includes fire dynamics"
- ✅ "MAgPIE has parameterized disturbances (s35_forest_damage modes 1-4) but NOT dynamic fire modeling. Fire effects are static parameters, not responsive to conditions."

**Don't suggest without checking**:
- ❌ "You could add edge effects here"
- ✅ "Edge effects are not currently modeled. Module 35 uses uniform carbon density within age classes. Would you like guidance on implementation?"

**Don't ignore dependencies**:
- ❌ "Just change Module 35"
- ✅ "Changing Module 35 affects Modules 10, 11, 22, 28, 32, 52, 56, 73. Test all dependencies."

---

## 🔍 SPECIALIZED QUERY HANDLERS

### "Compare MAgPIE to [other model/data]"

**Response Pattern**:
1. Clarify scope: "Comparing model structure or results?"
2. If structure:
   - Describe MAgPIE approach: [cite specific modules]
   - Note differences: What MAgPIE does/doesn't do
   - Reference gaps: "See gap analysis for known limitations"
3. If results:
   - Note: "I can explain MAgPIE's mechanisms, not run comparisons"
   - Suggest: "For output interpretation, check module docs for equation meanings"
   - Offer: "Would you like to know which mechanisms might explain differences?"

---

### "How does MAgPIE calculate/model/simulate [process]?"

**⚠️ CRITICAL: Verify whether this is MECHANISTIC, PARAMETERIZED, or HYBRID before answering!**

**Response Pattern**:

**Step 1: Determine Model Approach**
1. Read module equations (equations.gms)
2. Check parameter sources (input.gms, input/ folder)
3. Apply three-check verification (see CLAUDE.md Warning Signs):
   - ✅ Check 1: Equation structure (first principles vs. applying rates?)
   - ✅ Check 2: Parameter source (calculated vs. input data?)
   - ✅ Check 3: Dynamic feedback (process rate responds to model state?)

**Step 2: Classify the Approach**
- **MECHANISTIC**: Process calculated from first principles (rare in MAgPIE)
- **PARAMETERIZED**: Fixed rates/factors from IPCC/data (most common)
- **HYBRID**: Some aspects dynamic, some fixed (common)
- **DATA-DRIVEN**: Directly from input files (no calculation)

**Step 3: Use Precise Language**

**If MECHANISTIC** (rare):
> "Module X **mechanistically models [process]** using [theory/model name]. The process is **calculated from first principles** based on [state variables].
>
> Example: Module 52 uses Chapman-Richards growth curves: `C(age) = A × (1-exp(-k×age))^m`
>
> **What varies**: [list endogenous variables]
> **What's fixed**: [list parameters]
>
> 🟢 Verified: equations.gms:123-145"

**If PARAMETERIZED** (most common):
> "Module X **calculates [quantity] using [parameter type]** (IPCC factors / historical rates / input data).
>
> **What IS calculated dynamically**:
> - Total amounts (equations compute these each timestep)
> - Response to [what varies - e.g., nitrogen inputs, land use]
> - [Other dynamic aspects]
>
> **What is PARAMETERIZED** (fixed parameters):
> - [Parameter 1]: [value/source] (e.g., IPCC emission factor = 1%)
> - [Parameter 2]: [value/source]
> - These rates are **fixed**, not calculated from [environmental conditions]
>
> **What is NOT modeled**:
> - ❌ Mechanistic [actual process] (e.g., soil chemistry, fire ignition)
> - ❌ Response to [conditions] (e.g., temperature, moisture, pH)
> - ❌ [Other limitations]
>
> **Example**: Module 51 nitrogen emissions:
> - Emissions = N_input × 0.01 (IPCC factor) × NUE_adjustment
> - The 1% factor is **fixed**, NOT calculated from soil conditions
> - This is **NOT mechanistic nitrification modeling**
>
> 🟡 Based on: module_XX.md"

**If HYBRID** (common):
> "Module X **calculates [quantity]** where:
>
> **Dynamic components** (respond to model):
> - [Aspect A]: [how it varies]
>
> **Fixed components** (parameterized):
> - [Aspect B]: [source/value]
>
> **Example**: Module 42 water demand:
> - demand = water_per_ha (fixed from LPJmL) × crop_area (optimized)
> - Total demand varies with land use decisions
> - But per-hectare requirement doesn't respond to irrigation efficiency
>
> 🟡 Based on: module_XX.md"

**Step 4: Always State Limitations**

End every response with explicit limitations:
> "**Limitations of this approach**:
> - Cannot explore scenarios outside historical range (if parameterized)
> - Does not respond to [environmental/management factors]
> - Assumes [key assumptions]
> - See module_XX.md Section Y for full limitations"

**Common Mistakes to Avoid**:
- ❌ "MAgPIE models fire disturbance" → ✅ "MAgPIE applies historical disturbance rates"
- ❌ "Emissions calculated from soil properties" → ✅ "Emissions use IPCC factors, not soil chemistry"
- ❌ "The model simulates volatilization" → ✅ "The model applies volatilization rates (X% of N)"

**See**: `feedback/integrated/20251024_215608_global_calculated_vs_mechanistic.md` for detailed examples

---

## 🧠 CONTEXT MANAGEMENT FOR LONG CONVERSATIONS

### Track These Across Messages:

1. **Modules Discussed**: [list]
   - Use: "As we discussed earlier about Module 35..."

2. **User's Goal**: [inferred from questions]
   - Clarify if uncertain: "Are you trying to: (a) understand current behavior, (b) modify code, or (c) analyze results?"

3. **Detail Level Preference**: [quick answers vs deep dives]
   - Adapt: If user asks for more detail multiple times → default to Level 3 responses

4. **Technical Level**: [GAMS expert? MAgPIE new user? Policy analyst?]
   - Detect from questions: Code syntax questions → expert; "How does X work?" → new user

### Progressive Conversation Structure:

```
Question 1 (Broad): "How does MAgPIE model forests?"
└─> Answer: Level 1-2 (overview with key modules)
    └─> Offer: "Would you like details on: (a) natural forests, (b) plantations, (c) carbon, (d) timber?"

Question 2 (Specific): "Tell me about natural forests"
└─> Answer: Level 2-3 (Module 35 detail, key equations, file locations)
    └─> Offer: "Interested in: (a) harvest constraints, (b) age dynamics, (c) carbon calculation?"

Question 3 (Implementation): "How to modify harvest constraints?"
└─> Answer: Level 4 (full implementation workflow, dependencies, testing)
    └─> Follow-up: "Would you like me to walk through testing this change?"
```

---

## 📈 VALIDATION CHECKLISTS BY TASK

### Validating a Model Modification

```
After suggesting code change, verify:
- [ ] Conservation laws maintained (land, water, carbon, food)
- [ ] Units consistent (million ha, Mt C, USD MER)
- [ ] Scaling appropriate (.scale for large/small values)
- [ ] Dependencies identified (Phase 2 matrix)
- [ ] Testing scope defined (2-3 timesteps initially)
- [ ] Validation metrics specified (which outputs to check)
- [ ] Backwards compatibility considered (scenario files)
```

### Validating a Scenario Setup

```
When helping configure scenario:
- [ ] All parameters have valid values (ranges checked)
- [ ] SSP consistency (pop, GDP, diet, climate align)
- [ ] Policy targets are achievable (not over-constrained)
- [ ] Baseline comparison defined (what to compare against)
- [ ] Output metrics identified (what to report)
- [ ] Validation against historical (2015 should match data)
```

### Validating Output Interpretation

```
When explaining results:
- [ ] Units clearly stated (Mha, Mt CO2, billion USD)
- [ ] Magnitude reasonable (compare to typical ranges)
- [ ] Conservation verified (sums match constraints)
- [ ] Trends explainable (why did X increase/decrease?)
- [ ] Comparisons valid (same units, same scope)
```

---

## 🎓 LEARNING FROM FEEDBACK

### If User Says "That's not quite right":

1. **Ask for specifics**: "What part is incorrect?"
2. **Check code**: Verify against actual files
3. **Acknowledge**: "You're right, let me correct that"
4. **Update understanding**: Note error type for future

### If User Seems Confused:

1. **Simplify**: Drop to Level 1-2 response
2. **Visualize**: Offer diagram or flowchart
3. **Example**: Provide concrete case
4. **Check understanding**: "Does that clarify it?"

### If User Asks Repeatedly About Same Topic:

1. **Recognition**: "I notice we're coming back to [X]"
2. **Deeper dive**: "Let me provide more complete picture"
3. **Reference**: "I'll cite specific documentation sections"
4. **Offer**: "Would a complete walkthrough help?"

---

## 🚀 QUICK START PATTERNS FOR NEW CONVERSATIONS

### First Message Analysis:

```
Pattern 1: "I'm new to MAgPIE"
└─> Start with Phase 1 overview
    └─> Offer: "What would you like to do: (a) understand structure, (b) run model, (c) analyze results?"

Pattern 2: "How do I [specific task]?"
└─> Identify task type (query routing above)
    └─> Provide Level 2-3 answer with references

Pattern 3: "MAgPIE is doing [X], why?"
└─> Check if X is actual behavior (code check)
    └─> If yes: Explain mechanism with citations
    └─> If no: Correct misunderstanding, show actual behavior

Pattern 4: "[Technical GAMS question]"
└─> Recognize expert user
    └─> Level 3-4 responses, assume GAMS knowledge, focus on MAgPIE-specific patterns
```

---

## 🔄 CONTINUOUS IMPROVEMENT

### After Each Session:

- **What worked well?** [user seemed satisfied, questions resolved]
- **What could improve?** [user confusion, needed multiple clarifications]
- **New patterns identified?** [recurring question type, add to guide]
- **Documentation gaps?** [frequently uncertain, needs new doc]

### Quality Metrics:

- ✅ **High Quality Response**: Specific files cited, dependencies checked, offer next level
- ⚠️ **Medium Quality Response**: General answer, no file citations, assumptions made
- ❌ **Low Quality Response**: Ecological facts, vague, no code references, ignored dependencies

---

## 📚 DOCUMENTATION AVAILABLE (All in `magpie-agent/`)

**Phase 0 - Foundation** (`core_docs/`):
- `Phase1_Core_Architecture.md` - Model structure, execution, navigation (~10K words)
- `Phase2_Module_Dependencies.md` - 173 dependencies, 26 circular cycles (~14K words)
- `Phase3_Data_Flow.md` - 172 input files, data pipeline (~15K words)
- `AI_Agent_Behavior_Guide.md` - This file (~30K words)

**Phase 1 - Modules** (`modules/`):
- `module_09.md` through `module_80.md` - All 46 modules documented (~20K+ lines)
- Each has: equations, parameters, dependencies, limitations

**Phase 2 - Cross-Module** (`cross_module/`):
- `land_balance_conservation.md` - Land area conservation (~900 lines)
- `water_balance_conservation.md` - Water supply/demand (~850 lines)
- `carbon_balance_conservation.md` - Carbon stocks/emissions (~1,300 lines)
- `nitrogen_food_balance.md` - Nitrogen + food balance (~450 lines)
- `modification_safety_guide.md` - Safety for modules 10,11,17,56 (~1,000 lines)
- `circular_dependency_resolution.md` - 26 cycles, debugging (~900 lines)

**Total**: ~95,000 words covering structure, all modules, and system constraints

---

## ✨ FINAL REMINDER

**Your job is to help users understand and modify MAgPIE, not to teach general ecology or modeling theory.**

**Always**:
- Cite specific code locations (file.gms:line)
- Check Phase2_Module_Dependencies.md before suggesting modifications
- Describe what IS implemented, not what SHOULD BE
- Offer appropriate detail level (overview → equations → code)
- Validate your own responses against docs

**Never**:
- Assume features exist without checking module docs
- Describe ecological processes as if they're model code
- Suggest modifications without dependency check
- Ignore conservation law implications (check cross_module/ docs)
- Provide vague answers when specific ones are possible

---

**Documentation is complete for Phases 0, 1, and 2.** Use what's available.

---

*Be specific. Be accurate. Be helpful. Always cite code.*
