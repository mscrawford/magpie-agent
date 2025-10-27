# Land Balance Conservation Law in MAgPIE

**Status**: ✅ Complete
**Created**: 2025-10-22
**Modules Covered**: 10, 29, 30, 31, 32, 34, 35
**Conservation Law Type**: Strict equality constraint (hard)

---

## 1. Overview

The **Land Balance Conservation Law** is the fundamental physical constraint in MAgPIE that ensures **total land area remains constant** in every spatial unit (cell) across all time periods. This law represents the basic physical reality that **land cannot be created or destroyed**, only converted between different uses.

**Source**: Module 10 (Land), equation q10_land_area (`modules/10_land/landmatrix_dec18/equations.gms:13-15`)

**Mathematical Statement**:
```
∀ j ∈ Cells, ∀ t ∈ Time:
  Σ(land_type) Area(j, land_type, t) = Constant(j)
```

**Code Implementation**:
```gams
q10_land_area(j2) ..
  sum(land, vm_land(j2,land)) =e=
  sum(land, pcm_land(j2,land));
```

**Translation**: In every cell j, the sum of all land types in the current timestep equals the sum of all land types in the previous timestep.

---

## 2. The Seven Land Pools

**Verified**: `modules/10_land/landmatrix_dec18/module.gms:149-169`

MAgPIE distinguishes 7 mutually exclusive land types that sum to total cell area:

### 2.1 Managed Agricultural Land

| Land Type | Code | Module | Description |
|-----------|------|--------|-------------|
| **Cropland** | `crop` | 29, 30 | Cultivated land including croparea, fallow, tree cover |
| **Pasture** | `past` | 31 | Grazed grassland for livestock production |

**Total Agricultural Land** = crop + past

---

### 2.2 Managed Forest Land

| Land Type | Code | Module | Description |
|-----------|------|--------|-------------|
| **Forestry** | `forestry` | 32 | Timber plantations + NPI/NDC afforestation + CDR afforestation |

**Forestry Components** (Module 32):
- `plant`: Commercial timber plantations (rotation-based)
- `ndc`: Policy-driven afforestation (NPI/NDC commitments)
- `aff`: Carbon-price incentivized afforestation

---

### 2.3 Natural Vegetation

| Land Type | Code | Module | Description |
|-----------|------|--------|-------------|
| **Primary Forest** | `primforest` | 35 | Intact, undisturbed forests (no age-class tracking) |
| **Secondary Forest** | `secdforest` | 35 | Regenerating/disturbed forests (age-class tracked) |
| **Other Land** | `other` | 35 | Natural grassland, savanna, shrubland, young secondary forest |

**Other Land Components** (Module 35):
- `othernat`: Natural non-forest vegetation
- `youngsecdf`: Young secondary forest with carbon < 20 tC/ha

**Natural Vegetation Total** = primforest + secdforest + other

---

### 2.4 Exogenous Land

| Land Type | Code | Module | Description |
|-----------|------|--------|-------------|
| **Urban** | `urban` | 34 | Built-up areas, settlements (prescribed by SSP scenarios) |

**Special Status**: Urban land is **exogenous** (prescribed by LUH3 data), not optimized.

---

## 3. Core Land Balance Constraint

### 3.1 Mathematical Formulation

**Equation**: q10_land_area (Module 10, `equations.gms:13-15`)

```gams
q10_land_area(j2) ..
  sum(land, vm_land(j2,land)) =e=
  sum(land, pcm_land(j2,land));
```

**Components**:
- **LHS**: `sum(land, vm_land(j2,land))` - Current timestep total land (optimization variable)
- **RHS**: `sum(land, pcm_land(j2,land))` - Previous timestep total land (parameter)
- **Operator**: `=e=` - Strict equality (hard constraint, no tolerance)

**Expanded Form**:
```
vm_land(j,"crop") + vm_land(j,"past") + vm_land(j,"forestry") +
vm_land(j,"primforest") + vm_land(j,"secdforest") + vm_land(j,"other") + vm_land(j,"urban")
=
pcm_land(j,"crop") + pcm_land(j,"past") + pcm_land(j,"forestry") +
pcm_land(j,"primforest") + pcm_land(j,"secdforest") + pcm_land(j,"other") + pcm_land(j,"urban")
```

### 3.2 Recursive Dynamics

**Update Mechanism** (`modules/10_land/landmatrix_dec18/postsolve.gms:9`):
```gams
pcm_land(j,land) = vm_land.l(j,land);
```

**Interpretation**:
- After optimization completes for timestep t
- Current land allocation `vm_land.l` becomes next timestep's starting point `pcm_land`
- Creates path-dependent dynamics (history matters)

**Implication**: Land use decisions are **committed** - previous allocations constrain future options.

---

## 4. Land Transition Matrix

### 4.1 Tracking System

**Module 10** tracks **net land-use transitions** between all 7 land types using a 7×7 transition matrix.

**Variable**: `vm_lu_transitions(j,land_from,land_to)` - Area transitioning from one type to another (mio. ha)

**Matrix Structure** (49 possible transitions per cell):
```
           ↓ TO
FROM →    crop    past   forestry   prim   secd   other   urban
crop       ✓       ✓        ✓        ✗      ✓      ✓       ✓
past       ✓       ✓        ✓        ✗      ✓      ✓       ✓
forestry   ✓       ✓        ✓        ✗      ✓      ✓       ✓
primforest ✓       ✓        ✗        ✓      M35    ✗       ✓
secdforest ✓       ✓        ✓        ✗      ✓      ✗       ✓
other      ✓       ✓        ✓        ✗      M35    ✓       ✓
urban      ✗       ✗        ✗        ✗      ✗      ✗       ✓
```

**Legend**:
- ✓ = Transition allowed via vm_lu_transitions
- ✗ = Transition forbidden by `presolve.gms` restrictions
- M35 = Transition handled internally by Module 35 (not via vm_lu_transitions)

### 4.2 Transition Balance Equations

**Source Conservation** (`modules/10_land/landmatrix_dec18/equations.gms:23-25`):
```gams
q10_transition_from(j2,land_from) ..
  sum(land_to, vm_lu_transitions(j2,land_from,land_to)) =e=
  pcm_land(j2,land_from);
```

**Translation**: Total outflows from land_from = Previous area of land_from

**Destination Conservation** (`modules/10_land/landmatrix_dec18/equations.gms:19-21`):
```gams
q10_transition_to(j2,land_to) ..
  sum(land_from, vm_lu_transitions(j2,land_from,land_to)) =e=
  vm_land(j2,land_to);
```

**Translation**: Total inflows to land_to = Current area of land_to

**Together These Ensure**:
- Every hectare leaving a land type is accounted for
- Every hectare entering a land type has a source
- **No land is created or destroyed in transitions**

### 4.3 Key Transition Restrictions

**Verified**: `modules/10_land/landmatrix_dec18/presolve.gms:10-23`

1. **No Plantation on Primary Forest** (presolve.gms:13):
   ```gams
   vm_lu_transitions.fx(j,"primforest","forestry") = 0;
   ```
   **Rationale**: Protect intact forests from conversion to plantations

2. **No Primary Forest Creation** (presolve.gms:20):
   ```gams
   vm_lu_transitions.fx(j,land_from,"primforest") = 0;
   ```
   **Rationale**: Primary forest is by definition undisturbed (one-way decline)
   **Exception** (presolve.gms:21): `vm_lu_transitions.up(j,"primforest","primforest") = Inf` allows primforest to remain primforest

3. **Limited Within-Natveg Conversions** (presolve.gms:16-17):
   ```gams
   vm_lu_transitions.fx(j,"primforest","other") = 0;
   vm_lu_transitions.fx(j,"secdforest","other") = 0;
   ```
   **Rationale**: Direct transitions between natural vegetation types via vm_lu_transitions are restricted
   **Note**: primforest → secdforest and other → secdforest transitions are handled internally by Module 35 (via harvest and recovery mechanisms), not through Module 10's transition matrix

---

## 5. Module Interactions for Land Balance

### 5.1 Module 10 (Land) - Central Hub

**Role**: Enforces land balance, tracks transitions, provides interface to all land modules

**Key Equations**:
- q10_land_area: Total area conservation
- q10_transition_from: Source accounting
- q10_transition_to: Destination accounting
- q10_landexpansion: Calculate area gained from other types
- q10_landreduction: Calculate area lost to other types

**Provides**:
- `vm_land(j,land)` → To ALL land modules (most shared variable in MAgPIE)
- `vm_lu_transitions(j,land_from,land_to)` → To modules needing transition info
- `vm_landexpansion(j,land)` → To modules 35, 39, 58, 59
- `vm_landreduction(j,land)` → To modules 35, 39, 58, 59

**Centrality**: **17 connections** (2 inputs, 15 outputs) - **Highest in MAgPIE**

---

### 5.2 Module 29 (Cropland) - Aggregates Crop Components

**Role**: Defines total cropland as sum of croparea + fallow + tree cover

**Key Equation** (`modules/29_cropland/detail_apr24/equations.gms:11-12`):
```gams
q29_cropland(j2)..
  vm_land(j2,"crop") =e=
    sum((kcr,w), vm_area(j2,kcr,w)) + vm_fallow(j2) + sum(ac, v29_treecover(j2,ac));
```

**Components**:
- `vm_area(j,kcr,w)`: Harvested crop area (from Module 30)
- `vm_fallow(j)`: Fallow land (optimized)
- `v29_treecover(j,ac)`: Tree cover on cropland (optimized)

**Contribution to Land Balance**:
- Provides `vm_land(j,"crop")` to Module 10
- Must satisfy available cropland constraint
- Subject to SNV (semi-natural vegetation) share requirements

---

### 5.3 Module 30 (Croparea) - Allocates Crops Spatially

**Role**: Determines area for each crop type and water management system

**Key Variable**: `vm_area(j,kcr,w)` - Agricultural production area (mio. ha)
- **j**: Cell
- **kcr**: 19 crop types (15 food crops + 4 bioenergy)
- **w**: Water management (rainfed, irrigated)

**Constraints**:
- Rotational constraints (maximum/minimum shares by crop group)
- Bioenergy tree targets (when policies active)
- Regional cropland growth limits

**Contribution to Land Balance**:
- Provides `vm_area` to Module 29 for cropland aggregation
- Indirectly affects `vm_land(j,"crop")` through Module 29

**Does NOT directly set vm_land** - only allocates within cropland

---

### 5.4 Module 31 (Pasture) - Endogenous Pasture Area

**Role**: Determines pasture area based on livestock feed demand and yield

**Key Equation** (`modules/31_past/endo_jun13/equations.gms:16-18`):
```gams
q31_prod(j2) ..
  vm_prod(j2,"pasture") =l= vm_land(j2,"past") * vm_yld(j2,"pasture","rainfed");
```

**Mechanism**:
- Production capacity constraint: production ≤ area × yield
- Pasture area optimized to meet livestock demand at minimum cost
- **Endogenous** - responds to feed demand from Module 70 (Livestock)

**Contribution to Land Balance**:
- Provides `vm_land(j,"past")` to Module 10
- Competes with cropland and forestry for available land
- Subject to conservation constraints

**Conservation Constraint** (`modules/31_past/endo_jun13/presolve.gms:9`):
```gams
vm_land.lo(j,"past") = sum(consv_type, pm_land_conservation(t,j,"past",consv_type));
```

---

### 5.5 Module 32 (Forestry) - Managed Forest Area

**Role**: Manages three types of forestry land (plantations, NPI/NDC, carbon-price driven)

**Key Equation** (`modules/32_forestry/dynamic_may24/equations.gms:55-56`):
```gams
q32_land(j2) ..
  vm_land(j2,"forestry") =e= sum((type32,ac), v32_land(j2,type32,ac));
```

**Components**:
- `type32 = {"plant", "ndc", "aff"}` - Three forestry types
- `ac` - Age classes (5-year intervals)

**Contribution to Land Balance**:
- Provides `vm_land(j,"forestry")` to Module 10
- Establishment decisions based on forward-looking timber demand
- Subject to maximum forest establishment constraint (from Module 35)

**Land Conservation** (`modules/32_forestry/dynamic_may24/presolve.gms:208-210`):
- Avoids conflict with secdforest restoration targets
- Respects protected area constraints

---

### 5.6 Module 34 (Urban) - Exogenous Urban Expansion

**Role**: Prescribes urban land expansion based on SSP scenarios

**Key Constraint** (`modules/34_urban/exo_nov21/equations.gms:30-31`):
```gams
q34_urban_land(i2) ..
  sum(cell(i2,j2), vm_land(j2,"urban")) =e= sum((ct,cell(i2,j2)), i34_urban_area(ct,j2));
```

**Mechanism**:
- **Regional total** fixed to LUH3 data (hard constraint)
- **Cell-level** has flexibility via strong punishment costs (1e6 USD/ha)
- Urban land **cannot decrease** (one-way expansion)

**Contribution to Land Balance**:
- Provides `vm_land(j,"urban")` to Module 10
- **Exogenous** - not responsive to MAgPIE economics
- Reduces available land for agriculture, forestry, nature

**Special Status**: Only land type with prescribed trajectory (not optimized)

---

### 5.7 Module 35 (Natural Vegetation) - Complex Age-Class Dynamics

**Role**: Manages primary forest, secondary forest (age-classes), and other natural land

**Key Equations**:

**Primary Forest** (no age-classes):
- `vm_land(j,"primforest")` - Single variable, can only decrease

**Secondary Forest** (`modules/35_natveg/pot_forest_may24/equations.gms:11`):
```gams
q35_land_secdforest(j2) ..
  vm_land(j2,"secdforest") =e= sum(ac, v35_secdforest(j2,ac));
```

**Other Land** (`modules/35_natveg/pot_forest_may24/equations.gms:13`):
```gams
q35_land_other(j2) ..
  vm_land(j2,"other") =e= sum((othertype35,ac), vm_land_other(j2,othertype35,ac));
```

**Age-Class System**:
- Secondary forest and other land tracked in 5-year age classes
- Aging: Each timestep, forests progress to next age class
- Recovery: Abandoned land can become youngsecdf (young secondary forest)
- Maturation: youngsecdf graduates to secdforest when carbon > 20 tC/ha

**Contribution to Land Balance**:
- Provides `vm_land(j,"primforest")`, `vm_land(j,"secdforest")`, `vm_land(j,"other")` to Module 10
- Natural land = residual after other land uses allocated
- Subject to conservation constraints (NPI/NDC policies, protected areas)
- Provides maximum forest establishment potential to Module 32

**Critical Threshold** (`modules/35_natveg/pot_forest_may24/presolve.gms:99-107`):
- Carbon density > 20 tC/ha → Land is forest (secdforest)
- Carbon density ≤ 20 tC/ha → Land is other (youngsecdf or othernat)

---

## 6. Conservation Law in Practice

### 6.1 Land Allocation Sequence

**Optimization Flow** (during each timestep solve):

1. **Module 34 (Urban)**: Urban land prescribed exogenously
   - `vm_land(j,"urban")` fixed or strongly constrained
   - Reduces available land pool

2. **Modules 29-32 (Managed Land)**: Optimized based on demand and prices
   - **Module 30**: Crop allocation based on food/bioenergy demand
   - **Module 31**: Pasture area based on livestock feed demand
   - **Module 32**: Forestry area based on timber demand and carbon prices
   - **Module 29**: Aggregates cropland components

3. **Module 35 (Natural Vegetation)**: Residual after managed land allocated
   - Total natural land = Total cell area - (crop + past + forestry + urban)
   - Distributed among primforest, secdforest, other based on:
     - Conservation constraints (minimum forest/other targets)
     - Age-class dynamics (forest aging, maturation)
     - Harvest decisions (timber production from natural forests)
     - Disturbances (fire, shifting agriculture)

4. **Module 10 (Land)**: Verifies land balance constraint
   - Checks that sum of all land types = previous total
   - If violated → model infeasible (no solution)

### 6.2 Land Balance Verification

**Equation Check** (must hold for all cells, all timesteps):
```
vm_land(j,"crop") + vm_land(j,"past") + vm_land(j,"forestry") +
vm_land(j,"primforest") + vm_land(j,"secdforest") + vm_land(j,"other") + vm_land(j,"urban")
= Constant(j)
```

**R Code Example**:
```r
library(magpie4)
land <- land(gdx, level="cell")  # Read all land types by cell
total_land <- dimSums(land, dim=3.1)  # Sum over land types

# Check if total land constant across time
land_1995 <- total_land["y1995",,]
land_2050 <- total_land["y2050",,]
land_change <- land_2050 - land_1995

max_violation <- max(abs(land_change))
print(paste("Maximum land balance violation:", max_violation, "Mha"))

# Should be near-zero (machine precision only)
stopifnot(max_violation < 0.001)  # Less than 1,000 ha
```

**Expected Result**: `max_violation ≈ 0` (< 0.001 Mha = 1,000 ha)

**If Violated**: Model has a bug in land accounting - check Module 10 equations and module interactions

---

## 7. Special Cases and Scenarios

### 7.1 Urban Expansion Scenario

**Situation**: SSP3 scenario with high urban sprawl

**Mechanism**:
1. Module 34 increases `vm_land(j,"urban")` based on LUH3 data
2. Total land constant → Other land types must decrease
3. Model optimizes which land types lose area
4. Typically: Natural land (other, secdforest) converted first (lowest opportunity cost)
5. Cropland/pasture protected by food demand constraints

**Land Balance Maintained**:
```
Δ urban = - (Δ crop + Δ past + Δ forestry + Δ primforest + Δ secdforest + Δ other)
```

**Example** (illustrative):
- Cell has 100 Mha total land
- Urban increases from 1 Mha → 3 Mha (Δ urban = +2 Mha)
- Other land decreases from 40 Mha → 38 Mha (Δ other = -2 Mha)
- All other land types constant
- **Balance preserved**: +2 - 2 = 0 ✓

---

### 7.2 Agricultural Expansion Scenario

**Situation**: High food demand drives cropland expansion

**Mechanism**:
1. Food demand increases → Module 30 needs more `vm_area`
2. Module 29 increases `vm_land(j,"crop")` to accommodate
3. Expansion sources (via `vm_lu_transitions`):
   - Other land → crop (cheapest, if available)
   - Secondary forest → crop (moderate cost)
   - Pasture → crop (if livestock can intensify)
   - Primary forest → crop (expensive, often blocked by conservation)
4. Module 10 tracks transitions via transition matrix

**Land Balance Maintained**:
```
Δ crop = - (Δ past + Δ forestry + Δ primforest + Δ secdforest + Δ other)
(Urban assumed constant in this scenario)
```

**Conservation Constraints May Prevent Full Expansion**:
- If natural land at minimum (NPI/NDC policies) → Agricultural expansion blocked
- Model may become infeasible if food demand + conservation constraints incompatible

---

### 7.3 Afforestation Scenario

**Situation**: High carbon price drives afforestation in Module 32

**Mechanism**:
1. Carbon pricing incentivizes `vm_land(j,"forestry")` expansion (type "aff")
2. Module 32 optimizes afforestation based on CDR credits
3. Afforestation sources (via `vm_lu_transitions`):
   - Other land → forestry (preferred if low carbon density)
   - Pasture → forestry (if livestock can move/intensify)
   - Cropland → forestry (expensive due to food production loss)
4. Maximum forest establishment constraint from Module 35:
   ```
   forestry expansion ≤ pm_max_forest_est(j) - youngsecdf area
   ```

**Land Balance Maintained**:
```
Δ forestry = - (Δ crop + Δ past + Δ primforest + Δ secdforest + Δ other)
```

**Spatial Limit**: Not all cells can support forest (climatic suitability)

---

### 7.4 Conservation Policy Scenario

**Situation**: NPI/NDC policies require minimum forest area

**Mechanism**:
1. Module 35 enforces minimum forest constraint:
   ```
   primforest + secdforest + forestry ≥ p35_min_forest(j)
   ```
2. If current forest < target → Model must expand forest
3. Expansion comes from other land types (crop, past, other)
4. If forest > target → No constraint (can decrease if economically optimal)

**Land Balance Maintained**:
```
If forest must expand:
  Δ forest = - (Δ crop + Δ past + Δ other)
Total land unchanged
```

**Potential Conflicts**:
- High food demand + strict conservation → Infeasible
- Solution: Intensification (higher yields) or imports (trade)

---

### 7.5 Abandonment and Recovery

**Situation**: Agricultural land abandoned (low demand or carbon pricing)

**Mechanism**:
1. Modules 29-31 reduce cropland or pasture area
2. Module 10 tracks transition: `vm_lu_transitions(j,"crop","other")`
3. Module 35 receives abandoned land in `presolve.gms:47-73`
4. Recovery allocation:
   - If potential forest area available → youngsecdf (recovering to forest)
   - Otherwise → othernat (non-forest natural vegetation)
5. Over time: youngsecdf carbon accumulates
6. When carbon > 20 tC/ha → graduates to secdforest

**Land Balance Maintained**:
```
Δ crop (negative) = Δ other (positive)
Within Module 35: other land subdivided into othernat and youngsecdf
```

**Age-Class Dynamics**:
- Abandoned land enters youngest age class (ac0 or ac5)
- Forests age each timestep (ac5→ac10→ac15→...→acx)
- Mature forests (acx) accumulate older cohorts

---

## 8. Violations and Diagnostics

### 8.1 Common Causes of Infeasibility

**1. Urban + Conservation > Total Land**:
```
vm_land(j,"urban") + pm_land_conservation(j,all_types) > Total_Land(j)
```
- **Solution**: Relax conservation targets or use spatial targeting

**2. Food Demand + Conservation Incompatible**:
```
Cropland_Needed > Available_Land(j) - Protected_Land(j) - Urban(j)
```
- **Solution**: Intensification (increase yields) or trade (import food)

**3. Afforestation + Agriculture Compete**:
```
Forestry_Target + Cropland_Target > Total_Land(j) - Urban(j) - Protected_Natural(j)
```
- **Solution**: Adjust carbon price or afforestation limits

**4. Transition Restrictions Bind**:
```
Primary forest cannot be converted (protected)
But food demand requires expansion
And no other land available
```
- **Solution**: Allow conversion from secondary forest or other land

### 8.2 Diagnostic Checks

**Check 1: Total Land Constant**
```r
# Maximum absolute change in total land across all cells and time
max_change <- max(abs(total_land[,"y2050",] - total_land[,"y1995",]))
# Should be < 0.001 Mha (1,000 ha = rounding error only)
```

**Check 2: Transition Matrix Balance**
```r
# For each cell and timestep
# Outflows from land_from = Previous area
# Inflows to land_to = Current area
stopifnot(all.equal(rowSums(transitions), previous_land))
stopifnot(all.equal(colSums(transitions), current_land))
```

**Check 3: Module Sum Consistency**
```r
# Cropland from Module 29 = sum of Module 30 crops + fallow + tree cover
cropland_m29 <- vm_land[,,"crop"]
cropland_components <- sum(vm_area) + vm_fallow + vm_treecover
stopifnot(all.equal(cropland_m29, cropland_components))
```

**Check 4: Age-Class Aggregation**
```r
# Secondary forest from Module 35 = sum of age classes
secdforest_total <- vm_land[,,"secdforest"]
secdforest_ac <- sum(v35_secdforest[,,all_age_classes])
stopifnot(all.equal(secdforest_total, secdforest_ac))
```

**Check 5: Natural Vegetation Residual**
```r
# Natural land = Total - (Managed land + Urban)
natural_land_expected <- total_land - (crop + past + forestry + urban)
natural_land_actual <- primforest + secdforest + other
stopifnot(all.equal(natural_land_expected, natural_land_actual))
```

---

## 9. Implications for Model Modifications

### 9.1 High-Risk Modifications

**⚠️ DANGER: Changing Module 10 equations**
- Land balance is the foundation of MAgPIE
- Breaking this constraint creates physically impossible scenarios
- **Always verify**: Total land remains constant after any change

**⚠️ DANGER: Modifying transition restrictions**
- Adding/removing allowed transitions affects feasibility
- Example: Allowing primary → forestry enables plantation on intact forest
- **Check**: Conservation implications of new transitions

**⚠️ DANGER: Changing age-class dynamics (Module 35)**
- Age-class shifting affects carbon accounting
- Errors can violate land balance if aging not consistent
- **Verify**: Sum of age classes = total land type

### 9.2 Safe Modifications

**✓ SAFE: Adjusting costs**
- Land conversion costs (Module 39)
- Harvest costs (Modules 32, 35)
- Does not affect land balance, only allocation preferences

**✓ SAFE: Changing yields**
- Crop yields (Module 14)
- Pasture yields (Module 14)
- Affects land use efficiency, not total area conservation

**✓ SAFE: Conservation targets**
- Minimum forest (Module 35: p35_min_forest)
- Protected areas (Module 22: pm_land_conservation)
- May affect feasibility but not land balance constraint itself

### 9.3 Testing Protocol After Modifications

**Step 1**: Run standard scenario with modified code

**Step 2**: Extract land data
```r
land <- land(gdx, level="cell")
total_land <- dimSums(land, dim=3.1)
```

**Step 3**: Verify land balance
```r
# Check constancy across time
for(t in getYears(total_land)[-1]) {
  change <- total_land[,t,] - total_land[,getYears(total_land)[1],]
  max_violation <- max(abs(change))
  print(paste(t, ":", max_violation, "Mha"))
  stopifnot(max_violation < 0.001)
}
```

**Step 4**: Check transition matrix consistency
```r
transitions <- readGDX(gdx, "ov_lu_transitions", select=list(type="level"))
land_current <- readGDX(gdx, "ov_land", select=list(type="level"))
land_previous <- readGDX(gdx, "oq_land_area", select=list(type="level"))

# Verify: sum(transitions from X) = previous land X
# Verify: sum(transitions to Y) = current land Y
```

**Step 5**: Visual inspection
```r
# Plot land use change
plot(land[,"y1995":"y2100",])  # Should show smooth transitions
# Sudden jumps or discontinuities indicate problems
```

---

## 10. Summary

### 10.1 Key Principles

1. **Physical Conservation**: Land area is constant (cannot be created or destroyed)
2. **Strict Enforcement**: Hard equality constraint (=e=), no tolerance
3. **Universal Application**: Applies to every cell, every timestep, no exceptions
4. **Transition Tracking**: All land use changes tracked via transition matrix
5. **Module Coordination**: 6 modules provide land types, Module 10 enforces balance

### 10.2 Critical Equations

**Land Balance** (Module 10, equations.gms:13-15):
```
Σ(land types) Current Area = Σ(land types) Previous Area
```

**Transition Balance** (Module 10, equations.gms:19-25):
```
Σ(destinations) Transitions from X = Previous Area X
Σ(sources) Transitions to Y = Current Area Y
```

### 10.3 Module Roles

| Module | Land Type | Role | Optimization |
|--------|-----------|------|--------------|
| 10 | All | Enforces balance | - |
| 29 | Cropland | Aggregates components | Partly |
| 30 | Cropland | Allocates crops | Yes |
| 31 | Pasture | Feed production | Yes |
| 32 | Forestry | Timber + CDR | Yes |
| 34 | Urban | Prescribed expansion | No |
| 35 | Natural veg | Residual + conservation | Partly |

### 10.4 Practical Implications

**For Users**:
- Land balance always satisfied (if model solves)
- Infeasibility indicates conflicting constraints (food + conservation + urban)
- Land use changes are zero-sum (expansion somewhere = contraction elsewhere)

**For Developers**:
- Module 10 equations are **sacred** - modify with extreme caution
- New land types must integrate with transition matrix
- Age-class dynamics must preserve total area
- Always verify land balance after modifications

### 10.5 Verification Checklist

- [ ] Total land constant across all timesteps (< 0.001 Mha tolerance)
- [ ] Transition matrix rows sum to previous land
- [ ] Transition matrix columns sum to current land
- [ ] Module aggregations consistent (e.g., cropland = crops + fallow + trees)
- [ ] Age-class sums equal land type totals
- [ ] No negative land areas
- [ ] Urban land matches prescribed values (regionally)
- [ ] Conservation constraints not violated

---

## References

**Module Documentation**:
- Module 10: `magpie-agent/modules/module_10.md`
- Module 29: `magpie-agent/modules/module_29.md`
- Module 30: `magpie-agent/modules/module_30.md`
- Module 31: `magpie-agent/modules/module_31.md`
- Module 32: `magpie-agent/modules/module_32.md`
- Module 34: `magpie-agent/modules/module_34.md`
- Module 35: `magpie-agent/modules/module_35.md`

**Core Documentation**:
- Phase 1: Core Architecture (`magpie-agent/core_docs/Core_Architecture.md`)
- Phase 2: Module Dependencies (`magpie-agent/core_docs/Module_Dependencies.md`)

**Source Code**:
- Module 10 equations: `modules/10_land/landmatrix_dec18/equations.gms:13-25`
- Module 10 presolve: `modules/10_land/landmatrix_dec18/presolve.gms:10-23`
- Module 10 postsolve: `modules/10_land/landmatrix_dec18/postsolve.gms:9`

---

**Document Status**: ✅ Complete
**Verified Against**: MAgPIE 4.x source code and module documentation
**Created**: 2025-10-22
**Last Updated**: 2025-10-22
