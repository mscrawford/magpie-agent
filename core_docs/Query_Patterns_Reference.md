# Advanced Query Patterns Reference

**Purpose**: Detailed patterns for handling complex MAgPIE queries accurately.

**When to use**: These patterns help recognize complex query types and respond with precision. Consult this reference when dealing with non-trivial questions that require systematic analysis.

---

## Pattern 1: "Parameterized vs. Implemented" Detection

**Use when**: User asks "Is X modeled?" or "Does MAgPIE account for X?"

**Critical Distinction**: Something can be **parameterized** (infrastructure exists) but **NOT implemented** (hardcoded to defaults).

**Detection Workflow**:

1. ✅ **Check if sets exist** - Are the categories defined?
   ```bash
   grep "tillage59\|inputs59" modules/59_som/*/sets.gms
   ```

2. ✅ **Check if factors loaded** - Are parameters read from files?
   ```bash
   grep "f59_cratio_tillage" modules/59_som/*/input.gms
   ```

3. ✅ **Check if used in equations** - Is it in the calculations?
   ```bash
   grep "i59_cratio" modules/59_som/*/preloop.gms
   ```

4. ⚠️ **CRITICAL: Check if shares are hardcoded**
   ```gams
   i59_tillage_share(i,tillage59) = 0;
   i59_tillage_share(i,"full_tillage") = 1;  ← RED FLAG!
   ```

5. 🔍 **Verify if ever changed**
   ```bash
   grep "i59_tillage_share" modules/59_som/*/{presolve,equations}.gms
   ```
   → If no results = never updated after initialization = NOT modeled

**Response Pattern - If Parameterized But Not Implemented**:

> "Tillage is **parameterized** (IPCC factors loaded, equation structure supports variation) but **NOT actively modeled** (hardcoded to 100% full tillage in `preloop.gms:52-53`).
>
> The infrastructure exists:
> - Sets defined: full_tillage, reduced_tillage, no_tillage
> - IPCC factors: No-tillage could increase SOM by 10-22%
> - Equation ready: Factor included in calculation
>
> However, implementation does NOT use this:
> - All regions set to 100% full tillage
> - Never updated in presolve or equations
> - Result: Tillage has **zero effect** on SOM
>
> To enable, you would need to replace hardcoded defaults with regional data or optimization variables."

**Warning Signs** (RED FLAGS):
```gams
! RED FLAG #1: All regions set to same value
i59_tillage_share(i,"full_tillage") = 1;

! RED FLAG #2: Single option selected from multiple
i59_tillage_share(i,tillage59) = 0;  ! Zero all first
i59_tillage_share(i,"full_tillage") = 1;  ! Then only one

! RED FLAG #3: Comment mentions limitation
*' So far it just tracks the subsystem due to missing data

! RED FLAG #4: Parameter multiplied by 1 or 0 everywhere
s29_treecover_target = 0  ! Disabled by default
```

---

## Pattern 2: Cross-Module Mechanism Tracing

**Use when**: User asks "How does X affect Y?" where X and Y are in different modules

**Tracing Workflow**:

1. **Identify starting module** (where X is calculated/optimized):
   ```bash
   grep -r "vm_treecover" modules/*/*/declarations.gms
   ```

2. **Find interface variable** (what X provides to other modules):
   - Check module_XX.md "Interface Variables" section
   - Look for aggregation equations

3. **Search for downstream usage** (where consumed):
   ```bash
   grep -r "vm_treecover" modules/*/*/equations.gms
   ```

4. **Trace parameter chain** (how X is transformed):
   - Follow through intermediate parameters
   - Check preloop.gms and presolve.gms for transformations

5. **Follow to final effect** (ultimate impact):
   - Trace to final reported variables
   - Check cross_module docs for system-level effects

**Response Pattern**:

> "Tree cover affects SOM through this mechanism chain:
>
> **1. Module 29 (Cropland)** - Tree cover optimization:
> - Variable: `v29_treecover(j,ac)` by age class
> - Equation: `q29_treecover` aggregates to `vm_treecover(j)`
> - Location: `equations.gms:83-84`
>
> **2. Module 59 (SOM)** - SOM equilibrium:
> - Uses: `vm_treecover` in cropland SOM target
> - Formula: `vm_treecover × i59_cratio_treecover × f59_topsoilc_density`
> - Where: `i59_cratio_treecover = 1.0` (100% of natural carbon)
>
> **3. Module 52 (Carbon)** - Stock aggregation:
> - Aggregates SOM into total soil carbon
> - Reports: `vm_carbon_stock(j,"crop","soilc")`
>
> **Net Effect**: Trees restore SOM to 100% of natural levels (vs. typical cropland at 60-80%)."

**Key Insight**: Always trace the FULL chain - don't stop at first module that uses the variable.

---

## Pattern 3: Temporal Mechanism Questions

**Use when**: User asks "What happens after X?" or "How does X change over time?"

**Response Structure**:

**1. Initial State** (before event):
```
Before: Forest with SOM = natural topsoil density
Location: Module 59, q59_som_target_noncropland
Value: vm_land(j,"forest") × f59_topsoilc_density(ct,j)
```

**2. Transition Mechanism** (the event):
```
Transition: Forest → cropland via land-use transition matrix
Tracked by: vm_lu_transitions(j,"forest","crop")
Location: Module 10 (Land), used in Module 59
```

**3. Convergence Dynamics** (movement toward new state):
```
Convergence: 15% annual movement toward equilibrium
Formula: i59_lossrate(t) = 1 - 0.85^timestep_length
Rates:
- 5 years: 44% of gap closed
- 10 years: 80% of gap closed
- 20 years: 96% of gap closed
```

**4. New Equilibrium** (final stable state):
```
After: Cropland with SOM = crop_carbon_ratio × natural_density
Location: q59_som_target_cropland
Typical: 60-80% of natural level
```

**5. Timeframe** (how long until equilibrium):
```
Practical equilibrium: ~20 years (96% convergence)
Mathematical equilibrium: Never fully reached (exponential decay)
```

**Key Insight**: Temporal questions require **initial state → transition → convergence → equilibrium**, not just equation structure.

---

## Pattern 4: "How does MAgPIE calculate/model/simulate [process]?" Handler

**⚠️ CRITICAL: This is the most error-prone query type. Follow this protocol exactly.**

**Step 1: Determine Model Approach**

Apply the three-check verification (from Warning Signs section):
- ✅ **Check 1**: Equation structure (first principles vs. applying rates?)
- ✅ **Check 2**: Parameter source (calculated vs. input data?)
- ✅ **Check 3**: Dynamic feedback (process rate responds to model state?)

**Step 2: Classify the Approach**

- **MECHANISTIC**: Calculated from first principles (rare in MAgPIE)
- **PARAMETERIZED**: Fixed rates/factors from IPCC/data (most common)
- **HYBRID**: Some aspects dynamic, some fixed (common)
- **DATA-DRIVEN**: Directly from input files (no calculation)

**Step 3: Use Precise Language**

**If PARAMETERIZED (most common)**:
> "Module X **calculates [quantity] using [parameter type]** (IPCC factors / historical rates / input data).
>
> **What IS calculated dynamically**:
> - Total amounts (equations compute these each timestep)
> - Response to [optimized variables - e.g., land use, N inputs]
>
> **What is PARAMETERIZED** (fixed parameters):
> - [Parameter 1]: [value/source] (e.g., IPCC EF = 1%)
> - These rates are **fixed**, not calculated from [environmental conditions]
>
> **What is NOT modeled**:
> - ❌ Mechanistic [process] (e.g., soil chemistry, fire ignition)
> - ❌ Response to [conditions] (e.g., temperature, moisture)
>
> **Example**: Module 51 nitrogen emissions:
> - Emissions = N_input × 0.01 (IPCC factor) × NUE_adjustment
> - The 1% is **fixed**, NOT from soil conditions
> - This is **NOT mechanistic nitrification modeling**
>
> 🟡 Based on: module_XX.md"

**Common Mistakes to Avoid**:
- ❌ "MAgPIE models fire disturbance" → ✅ "MAgPIE applies historical disturbance rates"
- ❌ "Emissions calculated from soil properties" → ✅ "Emissions use IPCC factors"
- ❌ "The model simulates volatilization" → ✅ "The model applies volatilization rates (X% of N)"

**See**: `feedback/integrated/20251024_215608_global_calculated_vs_mechanistic.md` for detailed examples

---

## Pattern 5: Debugging Decision Tree

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
│     ├─ Check data integrity (NaN, Inf, negative)
│     └─ Reduce timesteps to isolate problem
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
   │  ├─ Land: sum(vm_land) = available area
   │  ├─ Water: sum(use) ≤ supply
   │  ├─ Carbon: emissions = Δstock + combustion
   │  └─ Food: production + trade ≥ demand
   └─ Compare to historical (2015 should match FAO)
```

---

## Summary

**These patterns cover 80% of complex queries. Use them to provide accurate, detailed responses.**

**When to consult this reference**:
- User asks "Is X modeled?" → Pattern 1
- User asks "How does X affect Y?" → Pattern 2
- User asks "What happens after X?" → Pattern 3
- User asks "How does MAgPIE calculate X?" → Pattern 4
- Model debugging questions → Pattern 5

**Core principle**: Systematic verification beats intuition. Follow the workflows to avoid common pitfalls.
