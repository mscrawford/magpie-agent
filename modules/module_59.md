## Module 59: Soil Organic Matter (SOM) ✅ COMPLETE

**Status**: Fully documented
**Location**: `modules/59_som/cellpool_jan23/`
**Method**: IPCC 2019 Guidelines with cell-level carbon pools and stock change factors
**Authors**: Kristine Karstens, Benjamin Leon Bodirsky

### Quick Reference

**Purpose**: Calculates soil organic carbon loss from land use change and estimates nitrogen release from SOM turnover

**Core Method**:
- IPCC 2019 stock change factors for cropland carbon equilibrium
- 15% annual convergence toward equilibrium (44% in 5 yrs, 80% in 10 yrs, 96% in 20 yrs)
- Crop-specific, climate-specific, and management-specific factors
- Tracks land-use transitions using carbon densities

**Dependencies**: MEDIUM (8 connections) - **MODERATE modification risk**
- **Provides to**: Module 51 (nitrogen), Module 11 (costs)
- **Receives from**: Modules 10 (land), 17 (production - via vm_area), 29 (crop management)
- **Interfaces with**: Module 52 (carbon - via vm_carbon_stock)

**Key Variables**:
- `v59_som_pool(j,land)` - Actual soil organic matter pool (mio. tC)
- `v59_som_target(j,land)` - Long-term equilibrium target (mio. tC)
- `vm_nr_som(j)` - N release from SOM loss (Mt N/yr)
- `vm_nr_som_fertilizer(j)` - Plant-available N from SOM (Mt N/yr)
- `vm_cost_scm(j)` - Soil carbon management costs (USD17MER/yr)

**Key Switches**:
- `c59_som_scenario` = "cc" (climate change), "nocc" (static), "nocc_hist" (fixed after year)
- `c59_irrigation_scenario` = "on" (irrigation increases C) or "off" (no effect)
- `s59_scm_target` = 0 (share of cropland under soil carbon management, 0-1)
- `s59_cost_scm_recur` = 65 USD17MER/ha (recurring SCM cost)

---

### 1. Core Purpose

**VERIFIED**: Module 59 calculates soil organic carbon dynamics following IPCC 2019 methodology (`modules/59_som/cellpool_jan23/realization.gms:9-16`).

**What Module 59 DOES**:
1. Tracks topsoil carbon pools by land use type in each cell
2. Calculates equilibrium carbon targets based on IPCC stock change factors
3. Moves actual pools 15% toward equilibrium each year
4. Estimates nitrogen release when SOM is lost
5. Calculates costs for optional soil carbon management practices

**What Module 59 does NOT do**:
- ❌ Does NOT model detailed microbial decomposition processes
- ❌ Does NOT track subsoil carbon dynamics (uses fixed reference value)
- ❌ Does NOT model tillage effects separately (default = full tillage)
- ❌ Does NOT model manure application effects separately (default = medium input)
- ❌ Assumes pastures and forests do NOT change SOM relative to natural state (`realization.gms:21-24`)
- ❌ Does NOT track within-timestep dynamics (annual convergence rate applied per timestep)

---

### 2. Realizations

**Active**: `cellpool_jan23` (cell-level pools, IPCC 2019 factors, temporal dynamics)
**Legacy**: `static_jan19` (IPCC 2006 factors, no temporal dynamics)

**VERIFIED Implementation** (`cellpool_jan23`):
- IPCC 2019 Guidelines stock change factors (`realization.gms:9-11`)
- Cell-specific climate classification (4 zones: temperate/tropical × dry/moist)
- Crop-specific factors by climate zone
- Irrigation effects on carbon equilibrium
- Dedicated soil carbon management option (high-input practices)
- 15% annual convergence to new equilibrium (`preloop.gms:45`)

---

### 3. Key Equations

#### 3.1 Cropland SOM Target (Equilibrium)

**Location**: `equations.gms:20-27`

```gams
q59_som_target_cropland(j2) ..
  v59_som_target(j2,"crop") =e=
    (sum((kcr,w), vm_area(j2,kcr,w) * i59_cratio(j2,kcr,w)) +
     sum((kcr,w,ct), vm_area(j2,kcr,w) * i59_scm_target(ct,j2) *
         i59_cratio(j2,kcr,w) * (i59_cratio_scm(j2) - 1))
     + vm_fallow(j2) * i59_cratio_fallow(j2)
     + vm_treecover(j2) * i59_cratio_treecover)
    * sum(ct,f59_topsoilc_density(ct,j2));
```

**VERIFIED**: Calculates equilibrium carbon pool for cropland as the sum of:
1. **Crop areas** × crop-specific carbon ratio × natural topsoil density
2. **SCM areas** × additional carbon from high-input management
3. **Fallow land** × fallow-specific carbon ratio (reduced tillage + low input)
4. **Treecover on cropland** × natural carbon density (ratio = 1.0)

**Key Parameters**:
- `i59_cratio(j,kcr,w)`: Carbon ratio combining land use × tillage × input × irrigation factors
- `i59_cratio_scm(j)`: High-input factor from IPCC (no manure)
- `i59_cratio_fallow(j)`: Maize + reduced tillage + low input
- `i59_cratio_treecover`: Set to 1.0 (natural soil carbon) (`preloop.gms:82`)
- `f59_topsoilc_density(t,j)`: Natural vegetation topsoil C from LPJmL

#### 3.2 Non-Cropland SOM Target

**Location**: `equations.gms:31-34`

```gams
q59_som_target_noncropland(j2,noncropland59) ..
  v59_som_target(j2,noncropland59) =e=
    vm_land(j2,noncropland59) * sum(ct,f59_topsoilc_density(ct,j2));
```

**VERIFIED**: Non-cropland (pasture, forestry, primforest, secdforest, other, urban) assumed to maintain natural carbon density (`sets.gms:10-11`).

**CRITICAL LIMITATION** (`realization.gms:21-24`):
- Pastures, rangelands, and managed forests do NOT change SOM compared to natural state
- Only transitions from other land and primary forest to secondary forest are tracked

#### 3.3 Actual SOM Pool (Dynamic Convergence)

**Location**: `equations.gms:46-52`

```gams
q59_som_pool(j2,land) ..
  v59_som_pool(j2,land) =e=
    sum(ct,i59_lossrate(ct)) * v59_som_target(j2,land)
    + (1 - sum(ct,i59_lossrate(ct))) *
      sum((ct,land_from), p59_carbon_density(ct,j2,land_from) *
        vm_lu_transitions(j2,land_from,land));
```

**VERIFIED**: Current pool = weighted average of:
- `lossrate` × equilibrium target (new equilibrium contribution)
- `(1 - lossrate)` × carbon density from land-use transitions (legacy contribution)

**Lossrate Calculation** (`preloop.gms:45`):
```gams
i59_lossrate(t) = 1 - 0.85^m_yeardiff(t);
```

**VERIFIED Convergence Rates**:
- **1 year**: 15% (1 - 0.85^1 = 0.15)
- **5 years**: 44% (1 - 0.85^5 = 0.44)
- **10 years**: 80% (1 - 0.85^10 = 0.80)
- **20 years**: 96% (1 - 0.85^20 = 0.96)

**Key Innovation** (`equations.gms:54-56`): Uses land-use transition matrix (`vm_lu_transitions`) to correctly account for carbon densities when land converts between uses.

#### 3.4 Soil Carbon Stock (Topsoil + Subsoil)

**Location**: `equations.gms:61-64`

```gams
q59_carbon_soil(j2,land,stockType) ..
  vm_carbon_stock(j2, land,"soilc",stockType) =e=
    v59_som_pool(j2, land) +
    vm_land(j2, land) * sum(ct,i59_subsoilc_density(ct,j2));
```

**VERIFIED**: Total soil carbon = topsoil pool (dynamic) + subsoil reference (static)

**Subsoil Calculation** (`preloop.gms:12`):
```gams
i59_subsoilc_density(t_all,j) = fm_carbon_density(t_all,j,"other","soilc") - f59_topsoilc_density(t_all,j);
```

**CRITICAL**: Subsoil carbon is NOT modeled dynamically, only topsoil changes.

#### 3.5 Nitrogen Release from SOM Loss

**Location**: `equations.gms:69-75`

```gams
q59_nr_som(j2) ..
  vm_nr_som(j2) =e=
    sum(ct,i59_lossrate(ct))/m_timestep_length * 1/15
    * (sum((ct,land_from), p59_carbon_density(ct,j2,land_from) *
           vm_lu_transitions(j2,land_from,"crop"))
       - v59_som_target(j2,"crop"));
```

**VERIFIED**: Nitrogen release = (carbon from transitions - equilibrium) × lossrate / timestep / 15

**Assumption** (`equations.gms:76`): **C:N ratio of soils = 15:1**

**Key Features**:
- Positive when cropland expansion (transitions > target) → N release
- Negative when cropland abandonment (transitions < target) → N sink
- Divided by timestep length to get annual rate
- Only tracks cropland SOM changes

#### 3.6 Plant-Available Nitrogen from SOM

**Location**: `equations.gms:81-84` and `equations.gms:88-91`

```gams
q59_nr_som_fertilizer(j2) ..
  vm_nr_som_fertilizer(j2) =l= vm_nr_som(j2);

q59_nr_som_fertilizer2(j2) ..
  vm_nr_som_fertilizer(j2) =l=
    vm_landexpansion(j2,"crop") * s59_nitrogen_uptake;
```

**VERIFIED**: Plant-available nitrogen limited by:
1. Total SOM nitrogen release
2. Maximum uptake capacity (200 kg N/ha on expanded area) (`equations.gms:93`, `input.gms:9`)

**CRITICAL**: Only a fraction of SOM nitrogen release is plant-available. Rest is lost to leaching or emissions (tracked by Module 51).

#### 3.7 Soil Carbon Management Cost

**Location**: `equations.gms:98-101`

```gams
q59_cost_scm(j2) ..
  vm_cost_scm(j2) =e=
    sum((kcr,w), vm_area(j2,kcr,w)) * sum(ct, i59_scm_target(ct,j2)) *
    s59_cost_scm_recur;
```

**VERIFIED**: Cost = total cropland area × SCM target share × recurring cost per ha

**Default** (`input.gms:15`): `s59_cost_scm_recur = 65 USD17MER/ha`

**Literature Basis** (`input.gms:18-40`):
- Smith et al. 2008: ~25 USD17MER/ha (low estimate)
- Uludere Aragon et al. 2024: 80-105 USD17MER/ha (high estimate)
- **Adopted**: 65 USD17MER/ha (midpoint)
- Includes practices: cover crops, residue management, green manures, improved fallows

---

### 4. Variables and Parameters

#### 4.1 Core Variables

**v59_som_target(j,land)** - Long-term equilibrium SOM pool (mio. tC)
- **Type**: Positive variable
- **Equation**: q59_som_target_cropland, q59_som_target_noncropland
- **Units**: Million tonnes carbon
- **Meaning**: Target carbon pool under current land use and management

**v59_som_pool(j,land)** - Actual SOM pool (mio. tC)
- **Type**: Positive variable
- **Equation**: q59_som_pool
- **Units**: Million tonnes carbon
- **Meaning**: Current soil organic carbon in topsoil, converging toward target

**vm_nr_som(j)** - Nitrogen release from SOM (Mt N/yr)
- **Type**: Free variable (can be positive or negative)
- **Declaration**: `declarations.gms:45`
- **Equation**: q59_nr_som
- **Units**: Million tonnes nitrogen per year
- **Used by**: Module 51 (nitrogen) for N2O emissions (`modules/51_nitrogen/rescaled_jan21/equations.gms`)

**vm_nr_som_fertilizer(j)** - Plant-available N from SOM (Mt N/yr)
- **Type**: Free variable
- **Declaration**: `declarations.gms:46`
- **Equation**: q59_nr_som_fertilizer, q59_nr_som_fertilizer2
- **Units**: Million tonnes nitrogen per year
- **Used by**: Module 50 (soil budget) for nitrogen availability (`modules/50_nr_soil_budget/macceff_aug22/equations.gms`)

**vm_cost_scm(j)** - Soil carbon management cost (USD17MER/yr)
- **Type**: Positive variable
- **Declaration**: `declarations.gms:41`
- **Equation**: q59_cost_scm
- **Units**: Million USD17MER per year
- **Used by**: Module 11 (costs) for total cost aggregation (`modules/11_costs/default/equations.gms`)

#### 4.2 Key Parameters

**f59_topsoilc_density(t,j)** - Natural topsoil C density (tC/ha)
- **Source**: LPJmL model output (`input.gms:77-86`)
- **File**: `modules/59_som/input/lpj_carbon_topsoil.cs2b`
- **Units**: Tonnes carbon per hectare
- **Climate scenarios**:
  - `c59_som_scenario = "cc"`: Climate change impacts (default)
  - `c59_som_scenario = "nocc"`: Fixed at 1995 values
  - `c59_som_scenario = "nocc_hist"`: Fixed after specific year

**i59_cratio(j,kcr,w)** - Carbon ratio for crop types (1)
- **Calculation**: `preloop.gms:60-67`
- **Components**: Land use × tillage × input × irrigation factors
- **Source**: IPCC 2019 tables
- **Dimensions**: Cell × crop × irrigation type
- **Meaning**: SOM as fraction of natural vegetation carbon

**i59_lossrate(t)** - Convergence rate per timestep (1)
- **Formula**: `1 - 0.85^timestep_length` (`preloop.gms:45`)
- **Default (5-year steps)**: 0.44 (44%)
- **Meaning**: Fraction of gap between current and target that closes each timestep

**i59_subsoilc_density(t,j)** - Subsoil C density (tC/ha)
- **Calculation**: Total soil C - topsoil C (`preloop.gms:12`)
- **Units**: Tonnes carbon per hectare
- **Meaning**: Static subsoil carbon reference (not dynamically modeled)

**i59_scm_target(t,j)** - SCM target share (1)
- **Calculation**: `presolve.gms:31-33`
- **Formula**: `scenario_fader(t) × (s59_scm_target × country_weight + s59_scm_target_noselect × (1 - country_weight))`
- **Range**: 0-1 (share of cropland)
- **Policy**: Can target specific countries via `policy_countries59` set

#### 4.3 IPCC Stock Change Factors

**f59_cratio_landuse(i,climate59,kcr)** - Land use factor (1)
- **File**: `input.gms:43-46` → `f59_ch5_F_LU_2019reg.cs3`
- **Source**: IPCC 2019 Chapter 5
- **Dimensions**: Region × climate × crop
- **Examples**: Perennial crops > annual crops

**f59_cratio_tillage(climate59,tillage59)** - Tillage factor (1)
- **File**: `input.gms:49-52` → `f59_ch5_F_MG.csv`
- **Options**: full_tillage, reduced_tillage, no_tillage
- **Default**: full_tillage = 1.0 (`preloop.gms:52-53`)
- **Meaning**: No tillage increases C, full tillage decreases C

**f59_cratio_inputs(climate59,inputs59)** - Input factor (1)
- **File**: `input.gms:55-58` → `f59_ch5_F_I.csv`
- **Options**: low_input, medium_input, high_input_nomanure, high_input_manure
- **Default**: medium_input = 1.0 (`preloop.gms:54-55`)
- **Meaning**: Higher inputs increase residues → higher C

**f59_cratio_irrigation(climate59,w,kcr)** - Irrigation factor (1)
- **File**: `input.gms:65-69` → `f59_ch5_F_IRR.cs3`
- **Switch**: `c59_irrigation_scenario` = "on" or "off" (`input.gms:61-70`)
- **Meaning**: Irrigation increases productivity → higher residues → higher C

#### 4.4 Soil Carbon Management Parameters

**i59_cratio_scm(j)** - SCM carbon ratio (1)
- **Calculation**: `preloop.gms:88-90`
- **Source**: IPCC high_input_nomanure factor
- **Practices** (`input.gms:20-25`): Cover crops, residue management, green manures, improved fallows
- **Meaning**: Additional carbon sequestration from improved practices

**s59_scm_target** - SCM target share (1)
- **Default**: 0 (disabled) (`input.gms:11`)
- **Range**: 0-1
- **Meaning**: Target share of cropland under soil carbon management

**s59_scm_scenario_start** - SCM ramp-up start year
- **Default**: 2025 (`input.gms:13`)

**s59_scm_scenario_target** - SCM target year
- **Default**: 2050 (`input.gms:14`)

**s59_cost_scm_recur** - SCM recurring cost (USD17MER/ha)
- **Default**: 65 (`input.gms:15`)
- **Literature range**: 25-105 USD17MER/ha

---

### 5. Climate Classification

**VERIFIED**: Module 59 uses climate zones to apply IPCC factors (`sets.gms:13-60`).

**Climate Zones** (`sets.gms:22-24`):
- temperate_dry
- temperate_moist
- tropical_dry
- tropical_moist

**Mapping** (`sets.gms:27-60`): Köppen-Geiger climate types → IPCC climate zones
- Example: Af, Am, As, Aw (equatorial) → tropical_moist
- Example: BSh, BWh (hot arid) → tropical_dry
- Example: Cfa, Cfb (temperate humid) → temperate_moist

**Extended Classification** (`sets.gms:19-20`): IPCC 2019 includes boreal zones (not used in default simulation):
- boreal_dry
- boreal_moist

---

### 6. Initialization (Preloop Phase)

**Location**: `preloop.gms`

**Step 1**: Calculate subsoil carbon density (`preloop.gms:12`)
```gams
i59_subsoilc_density(t_all,j) = fm_carbon_density(t_all,j,"other","soilc") - f59_topsoilc_density(t_all,j);
```

**Step 2**: Initialize cropland SOM pool (`preloop.gms:14-17`)
```gams
pc59_som_pool(j,"crop") = sum((climate59,kcr), climate_match × region_factor × topsoil_density × croparea_1995);
```

**Step 3**: Initialize non-cropland SOM pools (`preloop.gms:19-20`)
```gams
pc59_som_pool(j,noncropland59) = f59_topsoilc_density("y1995",j) * pm_land_start(j,noncropland59);
```

**Step 4**: Calculate lossrate (`preloop.gms:45`)
```gams
i59_lossrate(t) = 1 - 0.85^m_yeardiff(t);
```

**Step 5**: Calculate crop-specific carbon ratios (`preloop.gms:60-67`)
```gams
i59_cratio(j,kcr,w) = landuse_factor × tillage_factor × input_factor × irrigation_factor;
```

**Step 6**: Calculate special carbon ratios (`preloop.gms:73-90`)
- Fallow: Maize + reduced tillage + low input
- Treecover: 1.0 (natural carbon)
- SCM: High input without manure

**Step 7**: Create SCM target trajectory (`preloop.gms:94-100`)
- Linear or sigmoidal interpolation from start year to target year

**Step 8**: Calculate country weights for SCM policy (`preloop.gms:104-110`)
- Countries weighted by available cropland area

**Step 9**: Initialize carbon densities (`preloop.gms:112-116`)
```gams
pc59_carbon_density(j,land) = pc59_som_pool(j,land) / land_area;
```

---

### 7. Presolve Phase (Within-Timestep Updates)

**Location**: `presolve.gms`

**CRITICAL**: SOM pools updated after natural regrowth and disturbance accounting (`presolve.gms:8-12`).

**Secondary Forest Pool Update** (`presolve.gms:14-18`):
```gams
pc59_som_pool(j,"secdforest") = pc59_som_pool(j,"secdforest") +
  (primforest_loss) * carbon_density_primforest +
  (other_land_loss) * carbon_density_other;
```

**VERIFIED**: When primary forest → secondary forest or other land → secondary forest, carbon follows the transition.

**Other Land Pool Update** (`presolve.gms:20-22`):
```gams
pc59_som_pool(j,"other") = pc59_som_pool(j,"other") -
  (other_land_loss) * carbon_density_other;
```

**Primary Forest Pool Update** (`presolve.gms:24-26`):
```gams
pc59_som_pool(j,"primforest") = pc59_som_pool(j,"primforest") -
  (primforest_loss) * carbon_density_primforest;
```

**Carbon Density Recalculation** (`presolve.gms:28`):
```gams
p59_carbon_density(t,j,land) = pc59_som_pool(j,land) / land_area;
```

**SCM Target Update** (`presolve.gms:31-33`):
```gams
i59_scm_target(t,j) = i59_scm_scenario_fader(t) ×
  (s59_scm_target × country_weight + s59_scm_target_noselect × (1 - country_weight));
```

---

### 8. Postsolve Phase (After Optimization)

**Location**: `postsolve.gms`

**Step 1**: Store optimized SOM pools (`postsolve.gms:8`)
```gams
pc59_som_pool(j,land) = v59_som_pool.l(j,land);
```

**Step 2**: Store land areas for next timestep (`postsolve.gms:9`)
```gams
pc59_land_before(j,land) = vm_land.l(j,land);
```

**Step 3**: Update carbon densities for next timestep (`postsolve.gms:10`)
```gams
pc59_carbon_density(j,land) = pc59_som_pool(j,land) / land_area;
```

**Step 4**: Write all output variables (`postsolve.gms:13-65`)
- Marginal values (shadow prices)
- Level values (optimal quantities)
- Upper and lower bounds

---

### 9. Module Interfaces

#### 9.1 Provides To (Outputs)

**To Module 51 (Nitrogen)** via `vm_nr_som(j)`:
- Used in: `modules/51_nitrogen/rescaled_jan21/equations.gms`
- Purpose: Calculate N2O emissions from soil organic matter turnover
- Emission factor: `i51_ef_n_soil(i,n_pollutants_direct,"som")`

**To Module 50 (Soil Budget)** via `vm_nr_som_fertilizer(j)`:
- Used in: `modules/50_nr_soil_budget/macceff_aug22/equations.gms`
- Purpose: Nitrogen availability for plant uptake
- Constraint: Limited by SOM loss and plant uptake capacity

**To Module 11 (Costs)** via `vm_cost_scm(j)`:
- Used in: `modules/11_costs/default/equations.gms`
- Purpose: Add soil carbon management costs to total regional costs
- Type: Recurring annual cost

**To Module 52 (Carbon)** via `vm_carbon_stock(j,land,"soilc",stockType)`:
- Defined in: equation `q59_carbon_soil`
- Purpose: Report total soil carbon stocks (topsoil + subsoil)
- Used for: Carbon accounting, emissions calculations

#### 9.2 Receives From (Inputs)

**From Module 10 (Land)** via `vm_land(j,land)`:
- Used in: q59_som_target_noncropland, q59_carbon_soil
- Purpose: Land area by type

**From Module 10 (Land)** via `vm_lu_transitions(j,land_from,land_to)`:
- Used in: q59_som_pool, q59_nr_som
- Purpose: Track carbon densities through land-use transitions

**From Module 10 (Land)** via `vm_landexpansion(j,land)`:
- Used in: q59_nr_som_fertilizer2
- Purpose: Limit nitrogen uptake to expanded cropland area

**From Module 17 (Production)** via `vm_area(j,kcr,w)`:
- Used in: q59_som_target_cropland, q59_cost_scm
- Purpose: Cropland area by crop and irrigation type

**From Module 29 (Cropland Management)** via `vm_fallow(j)` and `vm_treecover(j)`:
- Used in: q59_som_target_cropland
- Purpose: Fallow and treecover areas with distinct carbon ratios

---

### 10. Configuration Options

#### 10.1 Climate Scenarios

**c59_som_scenario** (global setting)
- **"cc"** (default): Climate change impacts on topsoil carbon
  - `f59_topsoilc_density(t,j)` varies over time from LPJmL
- **"nocc"**: No climate change (static at 1995)
  - `f59_topsoilc_density(t,j) = f59_topsoilc_density("y1995",j)` (`input.gms:84`)
- **"nocc_hist"**: No climate change after fixed year
  - `f59_topsoilc_density(t,j) = f59_topsoilc_density(sm_fix_cc,j)` for t > sm_fix_cc (`input.gms:85`)

#### 10.2 Irrigation Effects

**c59_irrigation_scenario** (global setting)
- **"on"** (default): Irrigation increases carbon via higher productivity
  - Uses `f59_cratio_irrigation(climate59,w,kcr)` from IPCC
- **"off"**: No irrigation effect on soil carbon
  - `f59_cratio_irrigation(climate59,w,kcr) = 1` (`input.gms:70`)

#### 10.3 Soil Carbon Management

**s59_scm_target** (scalar, 0-1)
- **Default**: 0 (disabled)
- **Meaning**: Target share of cropland under improved soil carbon management
- **Practices**: Cover crops, residue management, green manures, improved fallows
- **Effect**: Increases carbon equilibrium via `i59_cratio_scm(j)`

**s59_scm_target_noselect** (scalar, 0-1)
- **Default**: 0
- **Meaning**: SCM target for countries NOT in `policy_countries59`
- **Use case**: Differential SCM adoption by region

**s59_scm_scenario_start** (year)
- **Default**: 2025
- **Meaning**: Year to start phasing in SCM

**s59_scm_scenario_target** (year)
- **Default**: 2050
- **Meaning**: Year to reach full SCM target

**s59_fader_functional_form** (1 or 2)
- **1**: Linear interpolation from start to target
- **2**: Sigmoidal interpolation (S-curve)

**s59_cost_scm_recur** (USD17MER/ha)
- **Default**: 65
- **Meaning**: Annual recurring cost of soil carbon management per hectare

#### 10.4 Nitrogen Parameters

**s59_nitrogen_uptake** (tN/ha)
- **Default**: 0.2 (200 kg N/ha) (`input.gms:9`)
- **Meaning**: Maximum plant-available nitrogen from SOM on newly expanded cropland

---

### 11. Typical Modifications

#### 11.1 Enable Soil Carbon Management

**Goal**: Implement improved soil carbon management on 30% of cropland by 2050

**Configuration**:
```r
cfg$gms$s59_scm_target <- 0.3                # 30% of cropland
cfg$gms$s59_scm_scenario_start <- 2025      # Start in 2025
cfg$gms$s59_scm_scenario_target <- 2050     # Reach 30% by 2050
cfg$gms$s59_cost_scm_recur <- 65            # 65 USD/ha annual cost
cfg$gms$s59_fader_functional_form <- 1      # Linear ramp-up
```

**Expected Effect**:
- Gradual increase in cropland carbon equilibrium
- Higher carbon stocks over time
- Reduced SOM loss and nitrogen release
- Additional costs in Module 11

**Module Dependencies**: Check Module 11 (costs) for budget impacts

#### 11.2 Disable Climate Change in SOM

**Goal**: Run counterfactual with static soil carbon conditions

**Configuration**:
```r
cfg$gms$c59_som_scenario <- "nocc"
```

**Expected Effect**:
- `f59_topsoilc_density` fixed at 1995 values
- No climate-driven changes in carbon equilibrium
- Useful for isolating land-use vs. climate effects

#### 11.3 Increase Nitrogen Uptake Limit

**Goal**: Allow more nitrogen from SOM to be plant-available

**Configuration**:
```r
cfg$gms$s59_nitrogen_uptake <- 0.3   # Increase from 0.2 to 0.3 tN/ha
```

**Expected Effect**:
- More SOM nitrogen available to crops on expanded land
- Reduced nitrogen fertilizer demand in Module 50
- Lower N2O emissions from excess N

**Module Dependencies**: Check Module 50 (soil budget) and Module 51 (nitrogen)

#### 11.4 Regional SCM Policy

**Goal**: Implement SCM only in Europe (EU27)

**Configuration**:
```r
# In sets declaration or config script:
policy_countries59 <- c("AUT", "BEL", "BGR", "HRV", "CYP", ...)  # EU27 codes
s59_scm_target <- 0.5           # 50% in EU
s59_scm_target_noselect <- 0.1  # 10% in rest of world
```

**Expected Effect**:
- Higher SCM adoption in selected countries
- Regional cost and carbon differences

#### 11.5 Turn Off Irrigation Effect

**Goal**: Test sensitivity to irrigation carbon boost

**Configuration**:
```r
cfg$gms$c59_irrigation_scenario <- "off"
```

**Expected Effect**:
- `f59_cratio_irrigation` set to 1.0 for all crops
- Lower carbon equilibrium under irrigation
- Reduced soil carbon benefits from irrigation expansion

---

### 12. Debugging & Diagnostics

#### 12.1 Common Issues

**Issue**: SOM pools becoming negative or unrealistic

**Diagnosis**:
1. Check initial pools in `preloop.gms:14-20`
2. Verify `f59_topsoilc_density` is loaded correctly
3. Check land-use transition matrix for errors

**Fix**: Ensure proper initialization and land balance

---

**Issue**: High nitrogen release causing infeasibilities

**Diagnosis**:
1. Check `vm_nr_som` values in output
2. Check cropland expansion rate (rapid expansion → high N release)
3. Verify C:N ratio (fixed at 15:1)

**Fix**: May need to adjust `s59_nitrogen_uptake` or check Module 51 constraints

---

**Issue**: SCM not activating despite positive target

**Diagnosis**:
1. Check `i59_scm_target(t,j)` values
2. Verify `i59_scm_scenario_fader(t)` is ramping up
3. Check country weights (`p59_country_weight`)

**Fix**: Ensure start year < current year and target > 0

---

**Issue**: Unexpected soil carbon trends

**Diagnosis**:
1. Check `c59_som_scenario` setting (cc vs. nocc)
2. Verify IPCC factors loaded correctly
3. Check lossrate calculation (`i59_lossrate`)

**Fix**: Verify climate scenario and timestep length

#### 12.2 Key Outputs to Monitor

**SOM Pools**:
```r
ov59_som_pool(t,j,land,"level")           # Actual pools
ov59_som_target(t,j,land,"level")         # Equilibrium targets
```

**Nitrogen Fluxes**:
```r
ov_nr_som(t,j,"level")                    # Total N release
ov_nr_som_fertilizer(t,j,"level")         # Plant-available N
```

**Carbon Stocks**:
```r
oq59_carbon_soil(t,j,land,stockType,"level")  # Total soil C
```

**Costs**:
```r
ov_cost_scm(t,j,"level")                  # SCM costs
```

#### 12.3 Validation Checks

**Mass Balance**:
```r
# SOM pool change should match land transitions
Delta_SOM = lossrate * (target - previous) + transitions
```

**Nitrogen Balance**:
```r
# N release should be 1/15 of C loss
vm_nr_som ≈ (C_loss / 15) / timestep_length
```

**Cost Consistency**:
```r
# SCM cost should match area and target
vm_cost_scm = sum(vm_area) * i59_scm_target * s59_cost_scm_recur
```

---

### 13. Key Limitations & Assumptions

**VERIFIED Limitations**:

1. **Pastures and Forests** (`realization.gms:21-24`):
   - ❌ Assumed NO SOM change from natural state
   - ❌ Only transitions to/from secondary forest tracked
   - Reality: Grazing and forest management DO affect SOM

2. **Tillage and Inputs** (`preloop.gms:52-55`):
   - ❌ Default = full tillage everywhere
   - ❌ Default = medium input everywhere
   - Reality: Tillage and input practices vary regionally and over time

3. **Subsoil Carbon** (`preloop.gms:12`):
   - ❌ Static reference value, not dynamically modeled
   - ❌ Assumes subsoil unaffected by land use
   - Reality: Subsoil carbon changes over decades

4. **Convergence Rate** (`preloop.gms:45`):
   - ❌ Fixed 15% annual rate for all soils
   - Reality: Convergence rates vary by soil type, climate, management

5. **C:N Ratio** (`equations.gms:76`):
   - ❌ Fixed at 15:1 for all soils
   - Reality: C:N varies by soil type, depth, land use (10:1 to 25:1)

6. **Within-Timestep Dynamics**:
   - ❌ Annual convergence applied per timestep (5 years)
   - ❌ No sub-timestep variation

7. **Nitrogen Uptake** (`equations.gms:91-93`):
   - ❌ Simple limit based on land expansion
   - Reality: Complex plant-microbe interactions

---

### 14. Connection to Other Degradation Modules

**Module 58 (Peatland)**:
- **Independence**: SOM and peatland are separate pools
- **No direct interaction** in current implementation
- **Opportunity**: Could track peatland SOM differently

**Module 35 (NatVeg) & Module 14 (Yields)**:
- **Potential link**: `s14_degradation` switch applies 8% yield penalty
- **Current**: Yield penalty is static, not dynamically linked to SOM loss
- **Opportunity**: Could make yield impact proportional to actual SOM loss from Module 59

**Module 52 (Carbon)**:
- **Interface**: `vm_carbon_stock` reports total soil carbon
- **Emissions**: SOM loss → CO2 emissions calculated by Module 52
- **Balance**: Must maintain carbon conservation

**Module 51 (Nitrogen)**:
- **Interface**: `vm_nr_som` provides N release
- **Emissions**: N mineralization → N2O emissions
- **Balance**: Must maintain nitrogen conservation

---

### 15. Research & Modification Opportunities

**Opportunity 1**: Dynamic Tillage and Input Tracking
- **Current**: Fixed defaults (full tillage, medium input)
- **Enhancement**: Track actual management practices from Module 38 (factor_costs) or Module 50 (soil_budget)
- **Impact**: More accurate carbon stocks, regional differentiation
- **Files to modify**: `preloop.gms:52-55`, add interface to management modules

**Opportunity 2**: Link to Yield Degradation
- **Current**: Module 14 has static 8% penalty (OFF by default)
- **Enhancement**: Make yield impact proportional to SOM loss
  ```gams
  yield_penalty = f(SOM_loss) = beta * (1 - SOM_actual / SOM_natural)
  ```
- **Impact**: More realistic yield-soil feedbacks
- **Files to modify**: `modules/14_yields/*/equations.gms`, add interface to Module 59

**Opportunity 3**: Pasture SOM Dynamics
- **Current**: Pastures assumed = natural carbon
- **Enhancement**: Model pasture degradation (overgrazing, compaction)
- **Impact**: Better degradation accounting in pastoral systems
- **Files to modify**: `equations.gms:31-34`, add pasture-specific factors

**Opportunity 4**: Subsoil Carbon Dynamics
- **Current**: Static subsoil reference
- **Enhancement**: Model deep carbon changes (decades-centuries timescale)
- **Impact**: More complete soil carbon accounting
- **Files to modify**: `equations.gms:61-64`, add subsoil pool tracking

**Opportunity 5**: Variable C:N Ratios
- **Current**: Fixed 15:1
- **Enhancement**: Crop-specific and climate-specific C:N ratios
- **Impact**: More accurate nitrogen release estimates
- **Files to modify**: `equations.gms:69-76`, add C:N parameter table

---

### 16. Testing & Validation

**Test 1**: SOM Mass Balance
```r
# For each timestep, check:
Delta_SOM = v59_som_pool(t) - pc59_som_pool(t-1)
Expected = lossrate * (v59_som_target - pc59_som_pool) + transitions
Tolerance: < 0.1% of pool size
```

**Test 2**: Nitrogen Consistency
```r
# Nitrogen release should match carbon loss
vm_nr_som(t) = (C_loss(t) / timestep_length) / 15
Check: vm_nr_som positive when cropland expands
Check: vm_nr_som_fertilizer <= vm_nr_som
```

**Test 3**: Cost Calculation
```r
# SCM cost should match area and target
Expected_cost = sum(vm_area(j,kcr,w)) * i59_scm_target(t,j) * s59_cost_scm_recur
Check: ov_cost_scm(t,j,"level") = Expected_cost
Tolerance: < 0.1%
```

**Test 4**: Carbon Stock Reporting
```r
# Total soil carbon should match pools + subsoil
Expected_soilc = v59_som_pool(j,land) + vm_land(j,land) * i59_subsoilc_density(j)
Check: vm_carbon_stock(j,land,"soilc",stockType) = Expected_soilc
```

**Test 5**: Climate Scenario Consistency
```r
# When c59_som_scenario = "nocc", density should be constant
Check: f59_topsoilc_density(t,j) = f59_topsoilc_density("y1995",j) for all t
```

**Test 6**: SCM Target Trajectory
```r
# SCM target should ramp from 0 to s59_scm_target
Check: i59_scm_target(s59_scm_scenario_start) ≈ 0
Check: i59_scm_target(s59_scm_scenario_target) = s59_scm_target * country_weight
Check: Monotonic increase between start and target
```

---

### 17. Summary: Module 59 at a Glance

**Purpose**: IPCC 2019-based soil organic matter tracking with dynamic carbon pools

**Method**:
- Stock change factors (crop × climate × management)
- 15% annual convergence to equilibrium
- Land-transition-aware carbon accounting

**Key Innovation**: Uses land-use transition matrix to correctly track carbon through conversions

**Key Limitation**: Pastures and forests assumed static; tillage/inputs at defaults

**Dependencies**: MEDIUM (8 connections) - **MODERATE modification risk**

**Typical Modifications**:
1. Enable soil carbon management (s59_scm_target = 0.3)
2. Link yield degradation to SOM loss (integrate with Module 14)
3. Add pasture SOM dynamics
4. Track actual tillage practices

**Critical Files**:
- `equations.gms` (103 lines) - 8 equations for SOM dynamics
- `preloop.gms` (117 lines) - Initialization and factor calculations
- `presolve.gms` (34 lines) - Natural vegetation transitions
- `input.gms` (118 lines) - IPCC factors and switches

**AI Response Pattern**:
- Cite specific equations and line numbers
- Clarify IPCC methodology (15% convergence, stock change factors)
- Warn about limitations (pastures static, defaults for tillage/input)
- Check Module 51 and Module 50 when modifying nitrogen fluxes
- Check Module 11 when modifying SCM costs

---

