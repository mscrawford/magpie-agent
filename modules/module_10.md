## Module 10: Land Allocation & Transitions ✅ COMPLETE

**Status**: Fully documented
**Location**: `modules/10_land/landmatrix_dec18/`
**Method**: Land transition matrix tracking all sources and targets of land-use change
**Authors**: Jan Philipp Dietrich, Florian Humpenoeder, Kristine Karstens

### 1. Purpose & Overview

**Core Function**: Module 10 is the **central land allocation hub** of MAgPIE, coordinating all land-related activities across the model. It maintains **total land area conservation**, tracks **net land transitions** between 7 land pools, and calculates **gross land-use change** metrics.

**Complexity**: CENTRAL HUB ⭐⭐⭐
**Dependencies**: 17 total connections (2 inputs, 15 outputs) - **HIGHEST centrality in MAgPIE**
**Impact**: Changes to this module affect **15 other modules** - testing must be comprehensive

**From Module Header** (`module.gms:10-14`):
```gams
*' @description The land module coordinates and analyzes all land related activities
*' by summing up all land types and calculating the gross changes in land use
*' between two time steps of optimization given the recursive dynamic structure of
*' MAgPIE model. The land module tracks land use transitions by directly counting
*' sources and targets of conversions.
```

**Realization**: `landmatrix_dec18` (only realization)
- Tracks land transitions via transition matrix approach
- Accounts for **net transitions only** (limitation)
- Enforces land conservation constraint

---

### 2. Mechanisms & Equations

Module 10 implements **7 equations** that enforce land accounting and track transitions:

#### **Equation 1: Land Area Conservation** (`equations.gms:13-15`)

```gams
q10_land_area(j2) ..
  sum(land, vm_land(j2,land)) =e=
  sum(land, pcm_land(j2,land));
```

**Purpose**: Ensures total land area in each cell remains constant over time
**Translation**: New land allocation = Previous land allocation
**Conservation Law**: ∑(land types) = constant for each cell j

**Implication**: Land cannot be created or destroyed, only converted between types

---

#### **Equation 2: Transition Matrix - Destinations** (`equations.gms:19-21`)

```gams
q10_transition_to(j2,land_to) ..
  sum(land_from, vm_lu_transitions(j2,land_from,land_to)) =e=
  vm_land(j2,land_to);
```

**Purpose**: Sum of all transitions INTO a land type = current area of that land type
**Translation**: (Forest→Crop + Past→Crop + ...) = Current Cropland
**Matrix**: Tracks **where land comes from** for each destination

---

#### **Equation 3: Transition Matrix - Sources** (`equations.gms:23-25`)

```gams
q10_transition_from(j2,land_from) ..
  sum(land_to, vm_lu_transitions(j2,land_from,land_to)) =e=
  pcm_land(j2,land_from);
```

**Purpose**: Sum of all transitions FROM a land type = previous area of that land type
**Translation**: (Crop→Forest + Crop→Past + ...) = Previous Cropland
**Matrix**: Tracks **where land goes to** from each source

---

#### **Equation 4: Land Expansion** (`equations.gms:30-33`)

```gams
q10_landexpansion(j2,land_to) ..
    vm_landexpansion(j2,land_to) =e=
    sum(land_from$(not sameas(land_from,land_to)),
    vm_lu_transitions(j2,land_from,land_to));
```

**Purpose**: Calculate land expansion (area gained from other land types)
**Translation**: Cropland expansion = (Forest→Crop + Past→Crop + Other→Crop + ...)
**Excludes**: Crop→Crop transitions (not expansion, just persistence)

---

#### **Equation 5: Land Reduction** (`equations.gms:35-38`)

```gams
q10_landreduction(j2,land_from) ..
    vm_landreduction(j2,land_from) =e=
    sum(land_to$(not sameas(land_from,land_to)),
    vm_lu_transitions(j2,land_from,land_to));
```

**Purpose**: Calculate land reduction (area lost to other land types)
**Translation**: Cropland reduction = (Crop→Forest + Crop→Past + Crop→Other + ...)
**Excludes**: Crop→Crop transitions (not reduction, just persistence)

---

#### **Equation 6: Land Transition Costs** (`equations.gms:42-44`)

```gams
q10_cost(j2) ..
    vm_cost_land_transition(j2) =e=
    sum(land, vm_landexpansion(j2,land) + vm_landreduction(j2,land)) * 1;
```

**Purpose**: Impose small costs (1 USD/ha) on gross land-use change
**Rationale**: Avoids unrealistic cycling patterns in transition matrix (e.g., Forest→Crop→Forest in same timestep)
**Translation**: Cost = Total land change × 1 USD/ha
**Design**: Tiny penalty ensures smooth transitions without distorting optimization

---

#### **Equation 7: Gross Land Difference** (`equations.gms:50-54`)

```gams
q10_landdiff ..
    vm_landdiff =e= sum((j2,land), vm_landexpansion(j2,land)
                                 + vm_landreduction(j2,land))
                                 + vm_landdiff_natveg
                                 + vm_landdiff_forestry;
```

**Purpose**: Calculate **global gross land-use change** across all cells and land types
**Components**:
1. `sum(vm_landexpansion + vm_landreduction)` - Net transitions between land types
2. `vm_landdiff_natveg` - Within-natveg changes (e.g., Primary→Secondary, age-class shifts) from Module 35
3. `vm_landdiff_forestry` - Within-forestry changes (e.g., rotation harvests, age-class shifts) from Module 32

**Translation**: Total change = Between-type transitions + Within-natveg transitions + Within-forestry transitions

**Why This Matters**: Captures both **net** land-use change (crop expansion) AND **gross** change (forest disturbance that doesn't change land type)

---

### 3. Parameters & Data

#### **Land Types** (`land` set - defined in `core/sets.gms:250-251`)

MAgPIE distinguishes **7 land pools**:

| Land Type | Code | Description | Management |
|-----------|------|-------------|------------|
| **Cropland** | `crop` | Cultivated land for food/feed/fiber | Managed |
| **Pasture** | `past` | Grazed grassland for livestock | Managed |
| **Forestry** | `forestry` | Timber plantations | Managed |
| **Primary Forest** | `primforest` | Intact, undisturbed forests | Protected |
| **Secondary Forest** | `secdforest` | Regrown/degraded forests (>20 tC/ha) | Semi-natural |
| **Urban** | `urban` | Built-up areas, settlements | Exogenous |
| **Other** | `other` | Grassland, savanna, shrubland, desert (<20 tC/ha) | Natural |

**Subsets** (defined in `core/sets.gms:253-263`):
- `land_ag` = {crop, past} - Agricultural land
- `land_forest` = {forestry, primforest, secdforest} - Forested areas
- `land_natveg` = {primforest, secdforest, other} - Natural vegetation
- `land_timber` = {forestry, primforest, secdforest, other} - Can provide timber

---

#### **Variables Declared** (`declarations.gms:14-24`)

**6 variables** that form the land allocation core:

1. **`vm_land(j,land)`** - Current land area by type (mio. ha)
   - **Most shared variable in MAgPIE** (used by 11 modules!)
   - Optimization variable (solver determines allocation)

2. **`vm_landexpansion(j,land)`** - Area gained from other types (mio. ha)
   - Example: Cropland expansion from forest clearing

3. **`vm_landreduction(j,land)`** - Area lost to other types (mio. ha)
   - Example: Cropland abandoned to secondary forest

4. **`vm_lu_transitions(j,land_from,land_to)`** - Full transition matrix (mio. ha)
   - Tracks every possible land conversion (7×7 = 49 transitions per cell)
   - Example: `vm_lu_transitions(j,"primforest","crop")` = deforestation to cropland

5. **`vm_cost_land_transition(j)`** - Small costs for transitions (mio. USD17MER/yr)
   - Prevents unrealistic cycling

6. **`vm_landdiff`** - Global gross land-use change (mio. ha)
   - Aggregates all transitions globally

---

#### **Parameters** (`declarations.gms:8-12`)

1. **`pm_land_start(j,land)`** - Initial land area (1995) (mio. ha)
   - Used to initialize model in `start.gms:8`
   - From `f10_land("y1995",j,land)`

2. **`pm_land_hist(t_ini10,j,land)`** - Historical land area (1995-2015) (mio. ha)
   - Years: 1995, 2000, 2005, 2010, 2015 (set `t_ini10`)
   - Used for calibration and validation
   - From `f10_land(t_ini10,j,land)`

3. **`pcm_land(j,land)`** - Previous timestep land (mio. ha)
   - Updated in `postsolve.gms:9` after each optimization
   - Critical for recursive dynamics: current becomes previous

---

### 4. Data Sources

#### **File 1: Historical Land Area** (`input.gms:8-11`)

```gams
table f10_land(t_ini10,j,land) Different land type areas (mio. ha)
$include "./modules/10_land/input/avl_land_t.cs3"
```

**Source**: Land-Use Harmonization 2 (LUH2) dataset
**Resolution**: 0.5° gridded, aggregated to 200 MAgPIE cells
**Years**: 1995, 2000, 2005, 2010, 2015
**Correction**: Negative values (from rounding) set to zero (`input.gms:16`)

**Data Processing**:
- LUH2 categories mapped to MAgPIE land types:
  - `c3ann + c4ann` → crop
  - `pastr + range` → past
  - `primf` → primforest
  - `secdf` → secdforest
  - `urban` → urban
  - Remainder → other

---

#### **File 2: LUH2 Side Layers** (`input.gms:19-23`)

```gams
table fm_luh2_side_layers(j,luh2_side_layers10) luh2 side layers (grid cell share)
$include "./modules/10_land/input/luh2_side_layers.cs3"
```

**Side Layers** (`sets.gms:12-13`):
- `manpast` - Managed pasture fraction
- `rangeland` - Rangeland fraction
- `primveg` - Primary vegetation fraction
- `secdveg` - Secondary vegetation fraction
- `forested` - Potential forest biome
- `nonforested` - Non-forest biome

**Purpose**: Classify land suitability and potential natural vegetation

---

#### **File 3: ISO-Level Land Area** (`input.gms:25-29`)

```gams
table fm_land_iso(t_ini10,iso,land) Land area at ISO level (mio. ha)
$include "./modules/10_land/input/avl_land_t_iso.cs3"
```

**Resolution**: 249 ISO countries
**Purpose**: Country-level reporting and disaggregation
**Use**: Validation, national-level outputs, scenario development

---

### 5. Dependencies

**From Phase 2 Analysis** (`detailed_module_analysis.txt:35-65`):

**Centrality Score**: 17 (Provides to: 15, Depends on: 2)
**Rank**: 2nd most depended-upon module (after 09_drivers)

#### **DEPENDS ON (2 modules)**:

1. **Module 32 (Forestry)**:
   - Variable: `vm_landdiff_forestry`
   - What: Gross changes within forestry land (rotation harvests, age-class shifts)
   - Why: Needed for total gross land-use change calculation

2. **Module 35 (Natural Vegetation)**:
   - Variable: `vm_landdiff_natveg`
   - What: Gross changes within natveg (Primary→Secondary, forest degradation)
   - Why: Needed for total gross land-use change calculation

**Circular Dependency**: Yes! Modules 10↔32↔35 form a tight feedback loop
**Implication**: Changes must be tested together

---

#### **PROVIDES TO (15 modules)** - **MOST in MAgPIE**:

| Module | Variables Provided | Purpose |
|--------|-------------------|---------|
| **59_som** | vm_land, pm_land_start, vm_landexpansion, vm_lu_transitions (4) | Soil carbon tracking |
| **29_cropland** | vm_land, pm_land_hist, vm_lu_transitions (3) | Cropland management |
| **35_natveg** | vm_land, vm_landexpansion, vm_lu_transitions (3) | Natural vegetation dynamics |
| **58_peatland** | vm_land, vm_landreduction, vm_landexpansion (3) | Peatland area changes |
| **32_forestry** | vm_land, pm_land_start (2) | Plantation area |
| **39_landconversion** | vm_landreduction, vm_landexpansion (2) | Land conversion costs |
| **11_costs** | vm_cost_land_transition (1) | Cost aggregation |
| **14_yields** | vm_land (1) | Yield calculations |
| **22_land_conservation** | vm_land (1) | Protected area constraints |
| **30_croparea** | vm_land (1) | Crop allocation |
| **31_past** | vm_land (1) | Pasture management |
| **34_urban** | vm_land (1) | Urban expansion |
| **50_nr_soil_budget** | vm_land (1) | Nitrogen budget |
| **71_disagg_lvst** | vm_land (1) | Livestock disaggregation |
| **80_optimization** | vm_land (1) | Objective function |

**Critical Consumers of `vm_land`** (11 modules total):
- 11_costs, 14_yields, 22_land_conservation, 29_cropland, 30_croparea
- 31_past, 32_forestry, 34_urban, 35_natveg, 39_landconversion, 50_nr_soil_budget
- 58_peatland, 59_som, 71_disagg_lvst, 80_optimization

**Why vm_land is So Critical**: It's the fundamental spatial allocation that determines:
- How much land available for production
- Carbon stocks per land type
- GHG emissions from land-use change
- Conservation constraints
- Cost calculations

---

### 6. Code Truth: What Module 10 DOES

✅ **1. Enforces Total Land Conservation** (`equations.gms:13-15`)
- Each cell's total land area stays constant
- No land creation or destruction
- Verified every timestep via `q10_land_area` constraint

✅ **2. Tracks Net Land-Use Transitions** (`equations.gms:19-25`)
- Full 7×7 transition matrix per cell (49 transitions)
- Knows source and target of every conversion
- Example: Forest→Crop, Crop→Past, Past→Forest, etc.

✅ **3. Calculates Expansion and Reduction** (`equations.gms:30-38`)
- Expansion = land gained from other types
- Reduction = land lost to other types
- Used by modules 35, 39, 58, 59 for impacts

✅ **4. Applies Transition Restrictions** (`presolve.gms:10-23`)
- **No plantation forestry on primary forest** (`vm_lu_transitions.fx(j,"primforest","forestry") = 0`)
- **No conversions within natveg** (Primary↔Other, Secondary↔Other blocked)
- **Primary forest can only decrease** (no land can become primary)
- **Primary→Primary allowed** (persistence OK)

✅ **5. Imposes Small Transition Costs** (`equations.gms:42-44`)
- 1 USD per hectare of gross change
- Prevents unrealistic rapid cycling
- Ensures smooth, realistic transitions

✅ **6. Aggregates Gross Land-Use Change** (`equations.gms:50-54`)
- Combines net transitions (between types)
- Adds within-natveg changes (Module 35)
- Adds within-forestry changes (Module 32)
- Produces global `vm_landdiff` metric

✅ **7. Initializes from LUH2 Historical Data** (`input.gms:8-16`, `start.gms:8-12`)
- Starts from 1995 observed land area
- Uses LUH2 0.5° data aggregated to 200 cells
- Historical period (1995-2015) used for calibration

✅ **8. Updates Land State Recursively** (`postsolve.gms:9`)
- After optimization: `pcm_land(j,land) = vm_land.l(j,land)`
- Current allocation becomes next timestep's starting point
- Enables path-dependent dynamics

---

### 7. Code Truth: What Module 10 does NOT

❌ **1. Does NOT Track Gross Transitions**
- Limitation stated in `realization.gms:11`: "only accounts for **net** land use transitions"
- Example: If 10 ha Forest→Crop AND 10 ha Crop→Forest, transition matrix shows ZERO net change
- Missing: Simultaneous opposing transitions within same timestep

❌ **2. Does NOT Determine Land Allocation Itself**
- Module 10 is **accounting only** - it tracks and enforces conservation
- Allocation decisions come from:
  - Module 30 (croparea) - crop distribution
  - Module 31 (past) - pasture extent
  - Module 32 (forestry) - plantation establishment
  - Module 35 (natveg) - forest protection/degradation
  - Module 34 (urban) - exogenous expansion

❌ **3. Does NOT Include Land Conversion Costs** (beyond 1 USD/ha token)
- Realistic conversion costs are in **Module 39 (landconversion)**
- Module 10's 1 USD/ha is just stabilization, not economic cost
- Clearing costs, establishment costs → Module 39

❌ **4. Does NOT Model Spatial Clustering**
- Land types within a cell can change independently
- No spatial autocorrelation (forests don't "cluster")
- No edge effects or fragmentation
- Each cell optimizes separately

❌ **5. Does NOT Distinguish Transition Pathways**
- Example: Primary Forest → Other vs Primary Forest → Crop looks the same to Module 10
- Detailed impacts (carbon, biodiversity) handled in Modules 35, 52, 56

❌ **6. Does NOT Restrict Urban Land**
- Urban is exogenous from Module 34
- Module 10 accounts for it but doesn't constrain it
- Total land conservation still enforced (urban expansion must come from somewhere)

❌ **7. Does NOT Model Sub-Grid Heterogeneity**
- Each cell (200 total) treated as homogeneous
- Reality: 67,420 original 0.5° cells aggregated to 200
- Within-cell variation lost in aggregation

❌ **8. Does NOT Prevent Ecologically Unrealistic Transitions**
- Example: Desert (other) → Cropland mathematically allowed if other modules don't restrict
- Realistic constraints come from:
  - Module 14 (yields) - low yields in marginal areas
  - Module 42 (water) - irrigation limits
  - Module 39 (landconversion) - high conversion costs
  - Module 22 (conservation) - protected areas

---

### 8. Common Modifications

#### 8.1 Change Historical Land Initialization

**Purpose**: Start from different base year or custom land distribution

**How**: Modify `start.gms:8`
```gams
* Default: 1995 start
pm_land_start(j,land) = f10_land("y1995",j,land);

* Alternative: 2000 start
pm_land_start(j,land) = f10_land("y2000",j,land);

* Custom: User-provided distribution
pm_land_start(j,land) = f_custom_land(j,land);
```

**Effect**:
- Changes path-dependent dynamics (different starting point)
- Affects calibration (historical period shorter if starting from 2000)
- Impacts carbon accounting (different baseline stocks)

**File**: `modules/10_land/landmatrix_dec18/start.gms:8`

---

#### 8.2 Adjust Land Transition Costs

**Purpose**: Increase/decrease penalty for rapid land-use change

**How**: Modify `equations.gms:44`
```gams
* Default: 1 USD/ha
vm_cost_land_transition(j2) =e=
  sum(land, vm_landexpansion(j2,land) + vm_landreduction(j2,land)) * 1;

* Higher penalty (10 USD/ha) - smoother transitions
vm_cost_land_transition(j2) =e=
  sum(land, vm_landexpansion(j2,land) + vm_landreduction(j2,land)) * 10;

* Zero cost - allow unrestricted transitions (may cause cycling)
vm_cost_land_transition(j2) =e= 0;
```

**Effect**:
- Higher cost → slower, smoother land-use change
- Zero cost → may get cycling artifacts (Forest→Crop→Forest)
- Trade-off: realism vs computational stability

**File**: `modules/10_land/landmatrix_dec18/equations.gms:44`

---

#### 8.3 Modify Transition Restrictions

**Purpose**: Allow/restrict specific land conversions

**How**: Edit `presolve.gms:10-23`

**Example 1: Allow plantation forestry on primary forest** (NOT RECOMMENDED)
```gams
* Default: No plantations on primary forest
vm_lu_transitions.fx(j,"primforest","forestry") = 0;

* Alternative: Allow limited conversion (0.01% per year)
vm_lu_transitions.up(j,"primforest","forestry") =
  pcm_land(j,"primforest") * 0.0001 * m_timestep_length;
```

**Example 2: Restrict cropland abandonment**
```gams
* Prevent crop → other conversions (force maintained agriculture)
vm_lu_transitions.up(j,"crop","other") = 0;
```

**Example 3: Allow controlled natveg conversions**
```gams
* Default: No primary → other conversions
vm_lu_transitions.fx(j,"primforest","other") = 0;

* Alternative: Allow degradation at 0.5% per year
vm_lu_transitions.up(j,"primforest","other") =
  pcm_land(j,"primforest") * 0.005 * m_timestep_length;
```

**Effect**:
- Alters feasible transition pathways
- Can make model infeasible if too restrictive
- Affects carbon emissions, biodiversity, production

**File**: `modules/10_land/landmatrix_dec18/presolve.gms:10-23`

---

#### 8.4 Track Additional Transition Metrics

**Purpose**: Add custom land-use change indicators

**How**: Add equations to `equations.gms`

**Example: Track total deforestation**
```gams
* In declarations.gms:
positive variable vm_deforestation(j) Total forest loss (mio. ha);
equation q10_deforestation(j) Deforestation tracking;

* In equations.gms:
q10_deforestation(j2) ..
  vm_deforestation(j2) =e=
  vm_lu_transitions(j2,"primforest","crop") +
  vm_lu_transitions(j2,"primforest","past") +
  vm_lu_transitions(j2,"secdforest","crop") +
  vm_lu_transitions(j2,"secdforest","past");
```

**Effect**:
- Enables direct tracking of specific conversions
- Useful for reporting, constraints, policy scenarios
- Can feed into other modules (e.g., biodiversity impacts)

---

#### 8.5 Impose Exogenous Land Trajectories

**Purpose**: Force specific land allocation (e.g., policy scenarios)

**How**: Fix `vm_land` in `presolve.gms`

**Example: Fixed afforestation target**
```gams
* In presolve.gms:
vm_land.fx(j,"forestry") = f_afforestation_target(t,j);
```

**Effect**:
- Overrides optimization for specific land types
- Useful for policy counterfactuals ("what if 100 Mha afforestation?")
- Can make model infeasible if inconsistent with conservation

---

#### 8.6 Disaggregate Urban Expansion Impacts

**Purpose**: Track which land types are converted to urban

**How**: Add urban-specific transition tracking

**Example**:
```gams
* Track urban expansion sources
positive variable vm_urban_expansion_source(j,land);
equation q10_urban_source(j);

q10_urban_source(j2) ..
  sum(land$(not sameas(land,"urban")),
    vm_lu_transitions(j2,land,"urban")) =e=
  sum(land, vm_urban_expansion_source(j2,land));
```

**Effect**:
- Identifies whether urban expansion takes cropland, forest, or other land
- Critical for land scarcity analysis
- Informs land-saving vs land-using urbanization

---

### 9. Testing & Validation

#### 9.1 Land Conservation Check

**Test**: Does total land area remain constant?

**How**:
```r
library(magpie4)
land <- land(gdx, level="cell")
total_land <- dimSums(land, dim=3.1)  # Sum over land types

# Check if total land constant across time
land_change <- total_land["y2050",,] - total_land["y1995",,]
max_violation <- max(abs(land_change))
stopifnot(max_violation < 0.001)  # Less than 1,000 ha (rounding error)
```

**Expected**: `max_violation` ≈ 0 (machine precision)

**If fails**: Check `q10_land_area` constraint, exogenous urban expansion consistency

**File**: `equations.gms:13-15` (constraint definition)

---

#### 9.2 Transition Matrix Consistency

**Test**: Do transition matrix rows/columns sum correctly?

**How**:
```r
transitions <- readGDX(gdx, "ov_lu_transitions", select=list(type="level"))

# For each cell and timestep:
# Sum of outflows from land_from should equal previous area
# Sum of inflows to land_to should equal current area
for(j in cells) {
  for(t in timesteps[-1]) {  # Skip first timestep
    land_prev <- land[[t-1]][j,,]
    land_curr <- land[[t]][j,,]
    trans_from <- rowSums(transitions[[t]][j,,,])
    trans_to <- colSums(transitions[[t]][j,,,])

    stopifnot(all.equal(trans_from, land_prev))
    stopifnot(all.equal(trans_to, land_curr))
  }
}
```

**Expected**: Perfect equality (zero difference)

**If fails**: Bug in `q10_transition_from` or `q10_transition_to` constraints

**Files**: `equations.gms:19-25`

---

#### 9.3 Expansion/Reduction Calculation

**Test**: Is expansion correctly calculated from off-diagonal transitions?

**How**:
```gams
* In GAMS after solve:
parameter test_expansion(j,land);
test_expansion(j,land_to) = sum(land_from$(not sameas(land_from,land_to)),
                                vm_lu_transitions.l(j,land_from,land_to));
display test_expansion, vm_landexpansion.l;

* Difference should be zero
parameter diff_expansion(j,land);
diff_expansion(j,land) = test_expansion(j,land) - vm_landexpansion.l(j,land);
display diff_expansion;
```

**Expected**: `diff_expansion` = 0 for all j, land

**If fails**: Check `q10_landexpansion` definition (`equations.gms:30-33`)

---

#### 9.4 Gross Land-Use Change Validation

**Test**: Does `vm_landdiff` correctly aggregate all changes?

**How**:
```r
landdiff_total <- readGDX(gdx, "ov_landdiff", select=list(type="level"))
expansion <- readGDX(gdx, "ov_landexpansion", select=list(type="level"))
reduction <- readGDX(gdx, "ov_landreduction", select=list(type="level"))
natveg_diff <- readGDX(gdx, "vm_landdiff_natveg", select=list(type="level"))
forestry_diff <- readGDX(gdx, "vm_landdiff_forestry", select=list(type="level"))

# Manual calculation
manual_landdiff <- dimSums(expansion + reduction, dim=c(1,3.1)) +
                   dimSums(natveg_diff, dim=1) +
                   dimSums(forestry_diff, dim=1)

# Compare with model output
difference <- landdiff_total - manual_landdiff
stopifnot(max(abs(difference)) < 0.01)
```

**Expected**: Difference < 0.01 Mha globally

**If fails**: Check `q10_landdiff` equation (`equations.gms:50-54`)

---

#### 9.5 Transition Restriction Enforcement

**Test**: Are forbidden transitions actually prevented?

**How**:
```r
transitions <- readGDX(gdx, "ov_lu_transitions", select=list(type="level"))

# Check primary forest → forestry transitions (should be zero)
prim_to_forestry <- transitions[,,"primforest","forestry"]
stopifnot(max(prim_to_forestry) == 0)

# Check primary forest → other transitions (should be zero)
prim_to_other <- transitions[,,"primforest","other"]
stopifnot(max(prim_to_other) == 0)

# Check secondary → other transitions (should be zero)
secd_to_other <- transitions[,,"secdforest","other"]
stopifnot(max(secd_to_other) == 0)
```

**Expected**: All forbidden transitions exactly zero

**If fails**: Check `presolve.gms:10-23` restrictions

---

#### 9.6 Historical Period Validation (1995-2015)

**Test**: Does model match observed historical land-use change?

**How**:
```r
# Load historical data
land_hist <- readGDX(gdx, "pm_land_hist")
land_sim <- land(gdx, level="cell")

# Compare for calibration period
hist_years <- c("y1995", "y2000", "y2005", "y2010", "y2015")
for(yr in hist_years) {
  diff <- land_sim[yr,,] - land_hist[yr,,]
  rmse <- sqrt(mean(diff^2))
  print(paste("Year", yr, "RMSE:", rmse, "Mha"))
}
```

**Expected**: Low RMSE during calibration period (< 5 Mha per cell)

**If fails**: Check calibration in Modules 29, 30, 31, 35 (they control allocation)

**Note**: Module 10 doesn't calibrate - it accounts. Calibration is in allocation modules.

---

### 10. Summary

**Module 10 (Land)** is the **central coordination hub** for all land-related activities in MAgPIE, with **17 connections** (highest centrality). It **tracks** land allocation but **does not determine** it.

**Core Functions**:
1. **Enforce land conservation** (total area constant per cell)
2. **Track net transitions** via 7×7 transition matrix (49 transitions/cell)
3. **Calculate expansion/reduction** for use by other modules
4. **Apply transition restrictions** (protect primary forest, prevent natveg conversions)
5. **Aggregate gross land-use change** (net transitions + within-type changes)
6. **Initialize from LUH2 data** (1995-2015 historical)

**Key Features**:
- Only 318 lines of code, but **15 modules depend on it**
- 7 equations enforce accounting and conservation
- 6 variables (most critical: `vm_land` used by 11 modules)
- 2 parameters (initialization and history)
- Recursive dynamics: current → previous via `postsolve.gms`

**Limitations** (from `realization.gms:11`):
- **Accounts for net transitions only** (not gross)
- No spatial clustering or edge effects
- No sub-grid heterogeneity
- No ecologically-driven restrictions (those come from other modules)
- Transition costs are token only (1 USD/ha for stability)

**Dependencies**:
- **Receives from**: Modules 32 (forestry), 35 (natveg) - for gross change components
- **Provides to**: 15 modules (11, 14, 22, 29, 30, 31, 32, 34, 35, 39, 50, 58, 59, 71, 80)
- **Circular**: Yes - tight coupling with Modules 32, 35 (test together!)
- **Impact**: Changes to Module 10 affect **15 modules** - most critical module for testing

**Typical Modifications**:
- Adjust transition costs (stabilization vs speed)
- Modify transition restrictions (allow/block specific conversions)
- Track custom metrics (deforestation, afforestation)
- Impose exogenous trajectories (policy scenarios)

**Testing Focus**:
- Land conservation (total area constant)
- Transition matrix consistency (rows/columns sum correctly)
- Expansion/reduction calculations
- Gross land-use change aggregation
- Transition restrictions enforced
- Historical validation (1995-2015)

**Why Module 10 Matters**:
- **Foundation** for all land-use dynamics in MAgPIE
- **vm_land** determines production capacity, carbon stocks, emissions, costs
- **Highest connectivity** → changes propagate widely
- **Path-dependent** → allocation history affects future options

---

### 11. Participates In

This section shows Module 10's role in system-level mechanisms. For complete details, see the linked documentation.

#### Conservation Laws

**Land Balance Conservation** ⭐ PRIMARY ENFORCER
- **Role**: Enforces strict land area conservation via `q10_land_area` constraint
- **Formula**: ∑(land types) = constant for each cell
- **Details**: `cross_module/land_balance_conservation.md`

**Carbon Balance**
- **Role**: Tracks carbon stock changes through land-use transitions
- **Contribution**: Provides `vm_land` and `vm_lu_transitions` for carbon accounting
- **Details**: `cross_module/carbon_balance_conservation.md`

#### Dependency Chains

**As Central Hub** (Rank #2 by centrality):
- **Provides interface to**: 15 modules via `vm_land`, `vm_landexpansion`, `vm_landreduction`, `vm_lu_transitions`
- **Consumes from**: 2 modules (32_forestry, 35_natveg for gross change components)
- **Complete dependency map**: `core_docs/Phase2_Module_Dependencies.md`

**Key downstream dependents**:
- Module 11 (Costs): Land conversion costs
- Module 14 (Yields): Cropland area for production
- Module 42 (Water): Land area for water demand
- Module 52 (Carbon): Land area for carbon stocks
- Module 59 (SOM): Land transitions for soil carbon dynamics

#### Circular Dependencies

**Land-Vegetation Cycles**:
- **Cycle 1**: Module 10 ←→ Module 35 (Natural Vegetation)
  - Module 10 provides land allocation → Module 35 calculates gross changes → Module 10 aggregates
- **Cycle 2**: Module 10 ←→ Module 22 (Land Conservation)
  - Module 10 allocates land → Module 22 enforces protection → Module 10 respects bounds

**Complex multi-module cycles**:
- **Forest-Land-Carbon Cycle**: 56_ghg_policy → 32_forestry → 10_land → 52_carbon → 56_ghg_policy
  - Carbon pricing affects afforestation → changes land allocation → updates carbon stocks → affects pricing
- **Details**: `cross_module/circular_dependency_resolution.md`

#### Modification Safety

**Risk Level**: ⚠️ **CRITICAL** (Highest centrality module)
- **Impact**: Changes affect 15 downstream modules
- **Testing required**: Comprehensive validation of all dependents
- **Safety protocols**: `cross_module/modification_safety_guide.md#module-10`

**Before modifying Module 10**:
1. Review dependency list (15 modules depend on vm_land)
2. Check conservation law implications (land balance is strict equality)
3. Test with circular dependency modules (32, 35) together
4. Verify no cascading failures in water (42), carbon (52), or costs (11)

---

**Last Verified**: 2025-10-13
**Verified Against**: `../modules/10_*/landmatrix_dec18/*.gms`
**Verification Method**: Equations cross-referenced with source code
**Changes Since Last Verification**: None (stable)
