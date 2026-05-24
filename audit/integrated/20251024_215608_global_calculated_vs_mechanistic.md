# Global Feedback: Calculated vs. Mechanistic Modeling (ERROR PATTERN)

**Type**: 5 (Global - Agent Behavior Pattern)
**Created**: 2024-10-24
**Integrated**: 2024-10-24 (COMPLETE)
**Priority**: HIGH
**Affects**: All modules with emissions, flows, or process calculations

**Integration Status**:
- ✅ CLAUDE.md updated (lines 769-917 - expanded Warning Signs section)
- ✅ AI_Agent_Behavior_Guide.md updated (lines 714-803 - new response pattern added)

---

## Error Pattern Identified

**CRITICAL ERROR TYPE**: Conflating "calculated by equations using fixed parameters" with "mechanistic process-based modeling"

**What happened**: When explaining nitrogen emissions (Module 51), I initially said emissions are "calculated" without clearly distinguishing:
- ✅ Equations DO compute emissions dynamically each timestep
- ❌ But using FIXED IPCC emission factors (not mechanistic soil/climate processes)
- ❌ This is NOT process-based modeling of volatilization/nitrification/denitrification

User correctly asked: **"Is this all calculated?"** - catching that "calculated" is ambiguous and potentially misleading.

---

## Why This Error Pattern Matters

**Fundamental model understanding**: Users need to know whether the model:
1. **Mechanistically simulates** a process (soil moisture → volatilization → NH₃)
2. **Applies parameterized rates** (X% of N becomes NH₃, from IPCC data)
3. **Uses fixed inputs** (emissions read directly from files)

**These have VERY different implications for**:
- Model capabilities and limitations
- What can be modified or improved
- What scenarios the model can represent
- Scientific validity and uncertainty
- Policy interpretation

---

## Error Pattern Detection: Red Flags

**Stop and verify if you write ANY of these phrases:**

### High-Risk Phrases (Almost Always Need Verification)
- ❌ "MAgPIE models [process]"
- ❌ "The model simulates [mechanism]"
- ❌ "MAgPIE accounts for [dynamic process]"
- ❌ "[Process] responds to [state variable]"
- ❌ "The model calculates [process]" ← AMBIGUOUS!

### Specific Red Flags by Domain

**Emissions/Environment**:
- "MAgPIE models volatilization/nitrification/denitrification"
- "Emissions respond to soil moisture/temperature/pH"
- "Fire modeling includes ignition and spread"
- "Leaching calculated from precipitation and soil properties"

**Biophysical Processes**:
- "Yields respond to nutrient deficiency"
- "Water availability affects plant growth"
- "Carbon sequestration responds to temperature"
- "Soil erosion modeled from rainfall intensity"

**Economic Processes**:
- "Prices respond to supply shocks"
- "Trade flows respond to comparative advantage"
- "Investment responds to profitability"

---

## Three-Check Verification Protocol

**Before claiming "MAgPIE models/simulates/calculates X", verify ALL THREE:**

### Check 1: Equation Structure
```gams
✅ MECHANISTIC PROCESS:
vm_yield(j,crop) = f_photosynthesis(light, CO2, water, nutrients)
                   × f_stress(temperature, drought)
where f_photosynthesis uses Farquhar model

❌ PARAMETERIZATION:
vm_yield(j,crop) = f_yield_baseline(j,crop) × tau_factor
where f_yield_baseline comes from input file

❌ EMISSION FACTOR APPROACH:
vm_emissions(i) = N_input × fixed_EF × efficiency_adjustment
where fixed_EF = 0.01 (IPCC constant)
```

**Question**: Does the equation compute the process FROM state variables, or APPLY a rate/factor/parameter?

### Check 2: Input Source
```gams
❌ PARAMETERIZATION INDICATORS:
- Variable names: f_* (input files), i_* (initialized parameters)
- File includes: $include "./modules/XX/input/f_data.cs3"
- Comments: "Source: Historical observations", "IPCC default"
- Data labels: "wildfire", "disturbance", "loss_rate"

✅ MECHANISTIC INDICATORS:
- Calculated from: vm_* (optimization variables), pm_* (processed params)
- Comments: "Based on [scientific theory]", "Derived from"
- Mathematical functions: chapman_richards(), logistic(), exponential()
```

**Question**: Does the key parameter come from input DATA or from CALCULATED state?

### Check 3: Dynamic Feedback
```gams
✅ MECHANISTIC (endogenous feedback):
fire_risk(j,t) = f(forest_moisture(j,t), temperature(j,t), wind(j,t))
where forest_moisture depends on vm_land_cover(j,t)
→ Model state affects fire risk, creating feedback loop

❌ PARAMETERIZATION (exogenous rates):
disturbance(j,t) = f_disturbance_rate(j) × vm_land(j,t)
where f_disturbance_rate from historical data (fixed)
→ Model state only scales the rate, doesn't affect it

❌ PARTIAL ENDOGENEITY (common pattern):
emissions(i,t) = N_input(i,t) × fixed_EF × (1-NUE(i,t))
where N_input optimized, NUE scenario-based, EF fixed
→ SOME dynamics (input amount varies) but NOT mechanistic
```

**Question**: Does model state AFFECT the process rate, or just SCALE a fixed rate?

---

## Correct Language Patterns

### ❌ WRONG: Implying Mechanistic Modeling
- "Module 51 models nitrogen volatilization"
- "NH₃ emissions calculated from soil properties"
- "The model simulates N₂O production via nitrification"

### ✅ CORRECT: Precise Description
- "Module 51 **calculates nitrogen emissions using IPCC Tier 1 emission factors**"
- "NH₃ emissions are **X% of applied N (IPCC default), adjusted for nitrogen use efficiency**"
- "N₂O emissions use **fixed emission factors** (1% of N applied), **not mechanistic nitrification modeling**"

### ✅ EVEN BETTER: Full Transparency
- "Module 51 **applies parameterized emission factors** (IPCC guidelines) **adjusted dynamically** based on nitrogen inputs and use efficiency. The emission factors themselves (1-3% for N₂O, 10-30% for NH₃) are **fixed parameters**, not calculated from soil moisture, temperature, or pH. **This is not process-based modeling** of volatilization or nitrification chemistry."

---

## Examples Across MAgPIE Modules

### Example 1: Module 51 (Nitrogen Emissions) ← THIS CASE

**❌ WRONG**:
> "Module 51 models nitrogen emissions including N₂O, NH₃, and NO₃⁻ leaching."

**✅ CORRECT**:
> "Module 51 **calculates nitrogen emissions using IPCC emission factors** (e.g., 1% of N becomes N₂O). These are **parameterized rates**, not mechanistic models of nitrification, volatilization, or leaching processes. Emissions respond to nitrogen inputs and use efficiency, but **do not respond to soil moisture, temperature, pH, or other environmental conditions**."

**Verification**:
- Check 1: `Emissions = N_input × fixed_EF × efficiency_factor` ← PARAMETERIZATION
- Check 2: `i51_ef_n_soil` from input file `f51_ef_n_soil.csv` ← DATA
- Check 3: EF doesn't depend on soil moisture, temp, etc. ← NO FEEDBACK

### Example 2: Module 35 (Natural Vegetation Disturbance)

**❌ WRONG**:
> "Module 35 models fire disturbance in forests."

**✅ CORRECT**:
> "Module 35 **applies historical disturbance rates** labeled 'wildfire' from observational data. It does **NOT simulate fire processes** (ignition, spread, combustion). The disturbance rates are **fixed parameters** that scale with forest area but **do not respond to climate, fuel load, or management**."

**Verification**:
- Check 1: `disturbance = f_rate × area` ← SCALING, not modeling
- Check 2: `f35_forest_lost_share.cs3` contains historical rates ← DATA
- Check 3: Rate doesn't change with drought, temperature, etc. ← NO FEEDBACK

### Example 3: Module 52 (Carbon Stocks) ← CONTRAST: This IS mechanistic

**✅ CORRECT (this is actually mechanistic)**:
> "Module 52 **mechanistically models carbon stock growth** using Chapman-Richards growth curves calibrated to forest age classes. Carbon density **increases with age** following `C(age) = A × (1 - exp(-k×age))^m`, and **responds to forest type and management**. This IS process-based modeling of carbon accumulation."

**Verification**:
- Check 1: `vm_carbon = f_chapman_richards(A,k,m,age)` ← MECHANISTIC FUNCTION
- Check 2: Age classes tracked dynamically ← CALCULATED STATE
- Check 3: Carbon growth responds to stand age (endogenous) ← FEEDBACK

### Example 4: Module 42 (Water Demand) ← PARTIAL DYNAMICS

**✅ CORRECT (hybrid approach)**:
> "Module 42 **calculates water demand from fixed crop water requirements** (from LPJmL) **multiplied by endogenous crop areas**. The water requirement per hectare is **parameterized** (input data), but **total demand is calculated dynamically** as crop areas change. This is **partial endogeneity** - demand scales with land use decisions, but the per-hectare requirement doesn't respond to irrigation efficiency or technology."

**Verification**:
- Check 1: `demand = water_per_ha × area` ← HYBRID
- Check 2: `water_per_ha` from LPJmL files ← DATA
- Check 3: Total demand varies (area optimized) but rate fixed ← PARTIAL

---

## Integration Proposal

### Target 1: CLAUDE.md - Expand "Warning Signs" Section

**Current** (line ~1090):
```markdown
## ⚠️ WARNING SIGNS - Stop and Verify

**If you write any of these phrases, STOP and verify against code:**
- "MAgPIE accounts for..."
- "The model considers..."
[... existing list ...]
```

**Add New Section** (after existing list):
```markdown
### ⚠️ CRITICAL: Calculated vs. Mechanistic Modeling

**Before claiming "MAgPIE models/simulates/calculates X", perform THREE-CHECK VERIFICATION:**

**Check 1 - Equation Structure**: Does it compute FROM first principles or APPLY a rate?
- ✅ Mechanistic: `yield = f(photosynthesis) × f(stress)` where f() uses biophysical theory
- ❌ Parameterized: `yield = baseline × factor` where baseline from input file

**Check 2 - Parameter Source**: Where do key values come from?
- ✅ Mechanistic: Calculated from state variables (vm_*, pm_*)
- ❌ Parameterized: Input files (f_*), IPCC defaults, historical data

**Check 3 - Dynamic Feedback**: Does model state affect the process?
- ✅ Mechanistic: Process rate responds to endogenous variables
- ❌ Parameterized: Fixed rate just scaled by area/activity
- ⚠️ Hybrid: Amount varies dynamically but rate is fixed

**Common Error Pattern**: Saying "calculated" without distinguishing:
1. **Equations calculate amounts** (e.g., total emissions) ← This IS calculated
2. **Using fixed parameters** (e.g., IPCC emission factors) ← This is NOT mechanistic
3. **vs. Mechanistic processes** (e.g., soil chemistry models) ← This is rarely done

**Correct Language**:
- ❌ "Module 51 models nitrogen volatilization"
- ✅ "Module 51 **calculates emissions using IPCC emission factors**, not mechanistic volatilization models"
- ✅ "Emissions are **parameterized** (1% of N → N₂O), **adjusted dynamically** for NUE changes"

**See**: `audit/integrated/20251024_215608_global_calculated_vs_mechanistic.md` for detailed examples
```

### Target 2: AI_Agent_Behavior_Guide.md - Add Response Pattern

**Location**: `core_docs/AI_Agent_Behavior_Guide.md` (new section or append to existing patterns)

**Add**:
```markdown
## Response Pattern: Explaining Calculations and Processes

**When user asks "How does MAgPIE calculate/model X?"**

### Step 1: Determine Model Approach
- Read module equations (equations.gms)
- Check parameter sources (input.gms, input/ folder)
- Classify as: Mechanistic / Parameterized / Hybrid / Data-driven

### Step 2: Use Precise Language

**If MECHANISTIC** (rare in MAgPIE):
"Module X **mechanistically models [process]** using [theory/model name]. The process is **calculated from first principles** based on [state variables]. Example: Chapman-Richards growth curves for carbon."

**If PARAMETERIZED** (most common):
"Module X **calculates [quantity] using [parameter type]** (IPCC factors / historical rates / input data). The [rates/factors] are **fixed parameters**, not mechanistic models of [process]. The calculation **responds to** [what varies dynamically] but **does not respond to** [what doesn't]."

**If HYBRID**:
"Module X **calculates [quantity]** where [aspect A] is **parameterized** (fixed rates) but [aspect B] is **dynamic** (responds to model state). Example: Water demand = fixed_water_per_ha × optimized_crop_area."

### Step 3: State Limitations Explicitly
Always mention what is NOT modeled:
- "This approach does **not** mechanistically model [actual process]"
- "Emission factors **do not respond to** soil moisture, temperature, pH"
- "Rates are **fixed from historical data**, not calculated from climate/management"

### Example Response Structure:

> **How Module 51 calculates nitrogen emissions**:
>
> Module 51 **calculates nitrogen emissions (N₂O, NH₃, NO₃⁻, NOₓ) using IPCC Tier 1 emission factors** (`equations.gms:22-89`).
>
> **What IS calculated dynamically**:
> - Total emission amounts (equations compute these each timestep)
> - Response to nitrogen inputs (from Module 50 optimization)
> - Adjustment for nitrogen use efficiency improvements
>
> **What is PARAMETERIZED** (not mechanistic):
> - Emission factors: 1% of N → N₂O (IPCC default)
> - NH₃ volatilization: 10-30% of N (IPCC ranges)
> - These rates are **fixed parameters**, not calculated from soil conditions
>
> **What is NOT modeled**:
> - ❌ Mechanistic nitrification/denitrification chemistry
> - ❌ Response to soil moisture, temperature, pH
> - ❌ Management effects (application timing, method)
> - ❌ Soil type effects (clay vs. sand)
>
> **Correct description**: "Module 51 applies IPCC emission factors, adjusted for nitrogen use efficiency" (NOT "mechanistically models volatilization")
>
> 🟢 Based on: module_51.md, equations.gms:22-89
```

---

## Testing: How to Verify Fix

**After integration, test with these queries:**

1. "How does MAgPIE model fire in forests?"
   - ✅ Should say: "applies historical disturbance rates, NOT fire simulation"

2. "How does the model calculate N₂O emissions?"
   - ✅ Should distinguish: "calculates using IPCC factors" vs. "NOT mechanistic chemistry"

3. "Does MAgPIE model soil erosion?"
   - ✅ Should verify existence first, then clarify if parameterized or mechanistic

4. "How are crop yields calculated?"
   - ✅ Should explain: tau factors from empirical data, NOT crop growth models

5. "How does carbon sequestration work?"
   - ✅ Should recognize: Chapman-Richards IS mechanistic (growth function)

---

## Success Criteria

**Agent should ALWAYS**:
1. Verify equation structure before claiming "models/calculates/simulates"
2. Distinguish "equations compute amounts" from "mechanistic process model"
3. State parameter sources (IPCC / data / calculated)
4. Explicitly list what is NOT modeled
5. Use precise language: "applies factors" vs. "mechanistically models"

**Agent should NEVER**:
1. Say "MAgPIE models X" without verifying approach
2. Imply IPCC emission factors are mechanistic models
3. Claim process-based modeling without checking equations
4. Use "calculates" ambiguously (clarify: amounts vs. processes)

---

## Priority: HIGH

**Why**: This error affects fundamental understanding of model capabilities and scientific validity. Incorrect claims about mechanistic modeling could:
- Mislead users about model limitations
- Misrepresent scientific rigor
- Lead to inappropriate scenario applications
- Undermine trust when users discover the distinction

**Frequency**: Likely affects dozens of queries across multiple modules (emissions, disturbances, growth, flows)

**Effort**: Moderate to integrate (update CLAUDE.md section, add behavior guide pattern)

**Impact**: High - prevents a systematic category of errors

---

## Related Documentation

- `CLAUDE.md` lines ~1050-1150 (Warning Signs section)
- `core_docs/AI_Agent_Behavior_Guide.md` (response patterns)
- `modules/module_51.md` lines 355-390 (NUE rescaling - good explanation of hybrid approach)
- `modules/module_35.md` (disturbance - example of parameterization)
- `modules/module_52.md` (carbon - example of mechanistic)

---

**Created by**: Claude (AI Agent)
**Triggered by**: User question "Is this all calculated?" exposing ambiguity in emission explanation
**Session**: 2024-10-24
**Error Type**: Imprecise language about model mechanisms (calculated vs. mechanistic)
