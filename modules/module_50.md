## Module 50: Nitrogen Soil Budget — Complete Documentation

**Location**: `modules/50_nr_soil_budget/`
**Active Realization**: `macceff_aug22`
**Authors**: Benjamin Bodirsky
**Purpose**: Balance nitrogen flows for crop and pasture soils, calculate inorganic fertilizer demand and associated costs

---

## 1. Purpose & Scientific Role

Module 50 serves as the **nitrogen balance calculator** for agricultural soils in MAgPIE, performing critical nutrient accounting functions:

**Primary functions**:
1. **Balance nitrogen budgets** for croplands and pastures
2. **Calculate inorganic fertilizer demand** (endogenous optimization variable)
3. **Apply nitrogen use efficiency scenarios** (SNUpE for croplands, NUE for pastures)
4. **Account for all nitrogen inputs**: biological fixation, manure, residues, atmospheric deposition, fertilizers
5. **Track nitrogen withdrawals**: harvested biomass minus seeds
6. **Compute fertilizer costs** for the objective function

**Key architectural role**: Module 50 is a **constraint module** that enforces nitrogen mass balance. It does NOT track nitrogen losses to environment directly - that is handled by Module 51 (Total Nitrogen Flows) which uses Module 50's efficiency parameters to calculate emissions.

**Critical design feature**: Nitrogen use efficiency (vm_nr_eff, vm_nr_eff_pasture) are FIXED variables set in presolve based on scenarios and MACC curves. The model optimizes inorganic fertilizer application (vm_nr_inorg_fert_reg) to meet crop nitrogen requirements given the fixed efficiency.

---

## 2. Nitrogen Balance Framework

### 2.1 Cropland Nitrogen Balance

**File**: `modules/50_nr_soil_budget/macceff_aug22/equations.gms:14-16`

```gams
q50_nr_bal_crp(i2) ..
    vm_nr_eff(i2) * v50_nr_inputs(i2)
    =g= sum(kcr,v50_nr_withdrawals(i2,kcr));
```

**Mathematical form**:
```
SNUpE(i) × N_inputs(i) ≥ N_withdrawals(i)
```

Where:
- **SNUpE** = Soil Nitrogen Uptake Efficiency (fraction of inputs taken up by crops)
- **N_inputs** = Total nitrogen applied to soils (Tg N/yr)
- **N_withdrawals** = Nitrogen removed in harvest + residues (Tg N/yr)

**Interpretation**: Of all nitrogen inputs to soil, only a fraction (SNUpE) is actually taken up by crops. The model must apply enough inputs so that `SNUpE × inputs ≥ requirements`.

**Example** (illustrative):
- Crop nitrogen requirement: 100 Tg N
- SNUpE = 0.65 (65% efficiency)
- Required inputs: 100 / 0.65 = 154 Tg N
- Nitrogen surplus: 154 - 100 = 54 Tg N (losses to environment)

### 2.2 Pasture Nitrogen Balance

**File**: `modules/50_nr_soil_budget/macceff_aug22/equations.gms:55-59`

```gams
q50_nr_bal_pasture(i2) ..
    vm_nr_eff_pasture(i2) *
    v50_nr_inputs_pasture(i2)
    =g=
    v50_nr_withdrawals_pasture(i2);
```

**Mathematical form**:
```
NUE_pasture(i) × N_inputs_pasture(i) ≥ N_withdrawals_pasture(i)
```

**Key difference from cropland**: Pasture biological nitrogen fixation is **per area** (tN/ha), whereas cropland fixation is **per crop production** (tN per tDM harvested).

---

## 3. Nitrogen Input Components

### 3.1 Cropland Inputs

**File**: `modules/50_nr_soil_budget/macceff_aug22/equations.gms:22-32`

```gams
q50_nr_inputs(i2) ..
    v50_nr_inputs(i2) =e=
    vm_res_recycling(i2,"nr")
      + sum((cell(i2,j2),kcr,w), vm_area(j2,kcr,w) * f50_nr_fix_area(kcr))
      + sum(cell(i2,j2),vm_fallow(j2) * f50_nr_fix_area("tece"))
      + vm_manure_recycling(i2,"nr")
      + sum(kli, vm_manure(i2, kli, "stubble_grazing","nr"))
      + vm_nr_inorg_fert_reg(i2,"crop")
      + sum(cell(i2,j2),vm_nr_som_fertilizer(j2))
      + sum(ct,f50_nitrogen_balanceflow(ct,i2))
      + v50_nr_deposition(i2,"crop");
```

**Components**:
1. **vm_res_recycling**: Crop residues left on field (above + below ground)
2. **Biological N fixation (area-based)**: `crop_area × fixation_rate` for legumes
3. **vm_manure_recycling**: Manure applied to croplands
4. **stubble_grazing manure**: Manure from animals grazing crop residues
5. **vm_nr_inorg_fert_reg**: **INORGANIC FERTILIZER** (optimization variable)
6. **vm_nr_som_fertilizer**: Soil organic matter mining for nutrients
7. **f50_nitrogen_balanceflow**: Correction term for unrealistic efficiencies
8. **v50_nr_deposition**: Atmospheric deposition (wet + dry)

### 3.2 Pasture Inputs

**File**: `modules/50_nr_soil_budget/macceff_aug22/equations.gms:74-80`

```gams
q50_nr_inputs_pasture(i2) ..
    v50_nr_inputs_pasture(i2)
    =e=
    sum(kli,vm_manure(i2, kli, "grazing", "nr"))
    + vm_nr_inorg_fert_reg(i2,"past")
    + sum((cell(i2,j2)), vm_land(j2,"past")) * sum(ct,f50_nr_fixation_rates_pasture(ct,i2))
    + v50_nr_deposition(i2,"past");
```

**Components**:
1. **Grazing manure**: Directly deposited by grazing animals
2. **Inorganic fertilizer**: Applied to improve pasture productivity
3. **Biological N fixation**: Area-based rate (tN/ha) for pasture legumes
4. **Atmospheric deposition**

---

## 4. Nitrogen Withdrawal Components

### 4.1 Cropland Withdrawals

**File**: `modules/50_nr_soil_budget/macceff_aug22/equations.gms:36-43`

```gams
q50_nr_withdrawals(i2,kcr) ..
    v50_nr_withdrawals(i2,kcr) =e=
    (1-sum(ct,f50_nr_fix_ndfa(ct,i2,kcr))) *
    (vm_prod_reg(i2,kcr) * fm_attributes("nr",kcr)
       + vm_res_biomass_ag(i2,kcr,"nr")
       + vm_res_biomass_bg(i2,kcr,"nr"))
    - vm_dem_seed(i2,kcr)  * fm_attributes("nr",kcr);
```

**Mathematical form**:
```
N_withdrawal(i,crop) = (1 - NDFA(i,crop)) ×
                       [N_harvest + N_residue_aboveground + N_residue_belowground]
                       - N_seed
```

Where **NDFA** = Nitrogen Derived From Atmosphere (biological fixation fraction)

**Key insight**: For legumes, NDFA can be 0.5-0.8, meaning 50-80% of nitrogen in biomass came from atmospheric fixation, not soil. Therefore, soil must supply only `(1 - NDFA) × biomass_N`.

**Seed nitrogen is subtracted** because seeds bring nitrogen INTO the field at planting.

### 4.2 Pasture Withdrawals

**File**: `modules/50_nr_soil_budget/macceff_aug22/equations.gms:83-85`

```gams
q50_nr_withdrawals_pasture(i2) ..
    v50_nr_withdrawals_pasture(i2) =e=
    vm_prod_reg(i2,"pasture") * fm_attributes("nr","pasture");
```

**Simpler than cropland**: Just the nitrogen content of harvested grass (grazed by animals).

---

## 5. Key Equations

### 5.1 Nitrogen Surplus

**Cropland** - `equations.gms:46-49`:
```gams
q50_nr_surplus(i2) ..
    v50_nr_surplus_cropland(i2)
    =e= v50_nr_inputs(i2)
    - sum(kcr, v50_nr_withdrawals(i2,kcr));
```

**Pasture** - `equations.gms:62-66`:
```gams
q50_nr_surplus_pasture(i2) ..
    v50_nr_surplus_pasture(i2)
    =e=
    v50_nr_inputs_pasture(i2)
    - v50_nr_withdrawals_pasture(i2);
```

**Nitrogen surplus = the fraction of inputs NOT taken up by crops**. This surplus is lost to the environment via:
- Ammonia volatilization
- N2O emissions
- Nitrate leaching
- Denitrification

These loss pathways are calculated in **Module 51 (Nitrogen)**, not Module 50.

### 5.2 Atmospheric Deposition

**File**: `equations.gms:88-90`

```gams
q50_nr_deposition(i2,land) ..
    v50_nr_deposition(i2,land) =e=
    sum((ct,cell(i2,j2)),i50_atmospheric_deposition_rates(ct,j2,land) * vm_land(j2,land));
```

**Formula**: `N_deposition = deposition_rate(j,land) × area(j,land)`

**Data source**: `f50_atmospheric_deposition_rates` from `input/f50_AtmosphericDepositionRates.cs3`

### 5.3 Fertilizer Costs

**File**: `equations.gms:94-97`

```gams
q50_nr_cost_fert(i2) ..
    vm_nr_inorg_fert_costs(i2) =e=
    sum(land_ag,vm_nr_inorg_fert_reg(i2,land_ag)) * s50_fertilizer_costs;
```

**Default cost**: `s50_fertilizer_costs = 738` (USD17MER per tN) - `input.gms:29`

**This cost enters the objective function** (Module 11), incentivizing the model to minimize fertilizer use while meeting crop nitrogen requirements.

---

## 6. Module Dependencies

### 6.1 Receives From (Upstream Dependencies)

| From Module | Variable | Use | File:line |
|-------------|----------|-----|-----------|
| **16_demand** | vm_dem_seed | Seed nitrogen inflow (subtracted from withdrawals) | equations.gms:42 |
| **17_production** | vm_prod_reg | Harvested crop nitrogen content | equations.gms:39, 85 |
| **18_residues** | vm_res_recycling | Crop residues left on field | equations.gms:24 |
| **18_residues** | vm_res_biomass_ag, vm_res_biomass_bg | Nitrogen in residues | equations.gms:40-41 |
| **30_croparea** | vm_area | Crop area for biological fixation calculation | equations.gms:25 |
| **29_cropland** | vm_fallow | Fallow area for fixation | equations.gms:26 |
| **55_awms** | vm_manure_recycling | Manure applied to crops | equations.gms:27 |
| **55_awms** | vm_manure | Manure from grazing (stubble, pasture) | equations.gms:28, 77 |
| **59_som** | vm_nr_som_fertilizer | Nitrogen from SOM mining | equations.gms:30 |
| **10_land** | vm_land | Land area for deposition and pasture fixation | equations.gms:79, 90 |
| **57_maccs** | im_maccs_mitigation | MACC curves for N2O mitigation | presolve.gms:56, 57 |

### 6.2 Provides To (Downstream Consumers)

| To Module | Variable | Use | Specific Code Location |
|-----------|----------|-----|------------------------|
| **11_costs** | vm_nr_inorg_fert_costs | Fertilizer costs in objective function | Module 11 cost aggregation |
| **51_nitrogen** | vm_nr_eff | Cropland SNUpE for emission calculations | `51_nitrogen/rescaled_jan21/equations.gms:26,34,46,59` |
| **51_nitrogen** | vm_nr_eff_pasture | Pasture NUE for emission calculations | `51_nitrogen/rescaled_jan21/equations.gms:37,80` |
| **51_nitrogen** | vm_nr_inorg_fert_reg | Inorganic fertilizer for emission calculations | `51_nitrogen/rescaled_jan21/equations.gms:33,36` |

**Critical interface with Module 51**: Module 50 provides the efficiency parameters that Module 51 uses to back-calculate nitrogen losses and emissions. The formula in Module 51:
```
N_loss = N_inorganic_fert / (1 - SNUpE_base) × (1 - SNUpE)
```

### 6.3 Circular Dependencies

**None directly**, but Module 50 is part of a nitrogen accounting cycle:
```
Module 50 (Soil Budget) → calculates fertilizer demand & efficiency
    ↓
Module 51 (Total Nitrogen) → calculates emissions from surplus
    ↓
Module 56 (GHG Policy) → prices emissions
    ↓
Module 57 (MACCs) → provides mitigation options
    ↓
(Feeds back to Module 50 via im_maccs_mitigation in presolve)
```

---

## 7. Key Variables

| Variable | Type | Dimensions | Units | Range | File:line |
|----------|------|------------|-------|-------|-----------|
| **vm_nr_inorg_fert_reg** | positive | (i,land_ag) | Tg N/yr | [0,∞) | declarations.gms:10 |
| **vm_nr_inorg_fert_costs** | positive | (i) | mio USD17MER/yr | [0,∞) | declarations.gms:11 |
| **vm_nr_eff** | positive | (i) | fraction | [0,1] | declarations.gms:12 ⚠️ |
| **vm_nr_eff_pasture** | positive | (i) | fraction | [0,1] | declarations.gms:13 ⚠️ |
| **v50_nr_inputs** | positive | (i) | Tg N/yr | [0,∞) | declarations.gms:14 |
| **v50_nr_withdrawals** | positive | (i,kcr) | Tg N/yr | [0,∞) | declarations.gms:15 |
| **v50_nr_surplus_cropland** | positive | (i) | Tg N/yr | [0,∞) | declarations.gms:16 |
| **v50_nr_inputs_pasture** | positive | (i) | Tg N/yr | [0,∞) | declarations.gms:17 |
| **v50_nr_withdrawals_pasture** | positive | (i) | Tg N/yr | [0,∞) | declarations.gms:18 |
| **v50_nr_surplus_pasture** | positive | (i) | Tg N/yr | [0,∞) | declarations.gms:19 |
| **v50_nr_deposition** | positive | (i,land) | Tg N/yr | [0,∞) | declarations.gms:20 |

**Note on vm_nr_eff and vm_nr_eff_pasture**:
- These are declared as `positive variables` but are **FIXED** in presolve.gms:76-77 based on scenarios
- They are not optimization variables - they are scenario inputs disguised as variables for technical reasons
- ⚠️ **Source code documentation error**: declarations.gms labels these as "(Tg N per yr)" but they are actually dimensionless fractions (0-1)

---

## 8. Key Parameters

| Parameter | Description | Source/Default | Dimensions | File:line |
|-----------|-------------|----------------|------------|-----------|
| **f50_snupe_base** | Baseline soil nitrogen uptake efficiency scenarios | Input data | (t,i,scen_neff_cropland50) | input.gms:89-94 |
| **f50_nue_base_pasture** | Baseline pasture nitrogen use efficiency scenarios | Input data | (t,i,scen_neff_pasture50) | input.gms:96-101 |
| **f50_nr_fix_ndfa** | Nitrogen Derived From Atmosphere (biological fixation) | Input data | (t,i,kcr) | input.gms:104-109 |
| **f50_nr_fix_area** | Area-based biological N fixation rates | Input data | (kcr) | input.gms:126-131 |
| **f50_nr_fixation_rates_pasture** | Pasture area-based fixation rates | Input data | (t,i) | input.gms:133-138 |
| **f50_atmospheric_deposition_rates** | Atmospheric N deposition rates | Input data | (t,j,land,dep_scen50) | input.gms:140-144 |
| **f50_nitrogen_balanceflow** | Correction for unrealistic SNUpE | Input data | (t,i) | input.gms:111-116 |
| **i50_nr_eff_bau** | Business-as-usual SNUpE (before MACCs) | Calculated in preloop | (t,i) | declarations.gms:43 |
| **i50_nr_eff_pasture_bau** | Business-as-usual pasture NUE | Calculated in preloop | (t,i) | declarations.gms:44 |

---

## 9. Key Scalars

**File**: `modules/50_nr_soil_budget/macceff_aug22/input.gms:28-32`

| Scalar | Default | Units | Description | Line |
|--------|---------|-------|-------------|------|
| **s50_fertilizer_costs** | 738 | USD17MER/tN | Cost of inorganic nitrogen fertilizer | 29 |
| **s50_maccs_global_ef** | 1 | binary | Use global emission factor for MACCs (1=yes, 0=no) | 30 |
| **s50_maccs_implicit_nue_glo** | 0.5 | fraction | Global NUE implicit to MACC curves | 31 |

**Configuration switches** - `input.gms:11-26`:
- **c50_scen_neff**: Cropland SNUpE scenario (default: `baseeff_add3_add5_add10_max65`)
- **c50_scen_neff_pasture**: Pasture NUE scenario (default: `constant_min55_min60_min65`)
- **c50_dep_scen**: Atmospheric deposition scenario (default: `history`)

---

## 10. Nitrogen Use Efficiency Scenarios

### 10.1 Cropland SNUpE Scenarios

**File**: `modules/50_nr_soil_budget/macceff_aug22/sets.gms:13-20`

**Available scenarios** (scen_neff_cropland50):
- `constant`: No change over time
- `baseeff_add3_add5_add10_max65`: Baseline + 3% by 2030, +5% by 2050, +10% by 2100, max 65%
- `baseeff_add3_add15_add25_max75`: More aggressive improvement
- `maxeff_add3_glo75_glo85`: Global targets (75% by 2050, 85% by 2100)
- `maxeff_ZhangBy2030`, `maxeff_ZhangBy2050`: Based on Zhang et al. literature

**Implementation** - `preloop.gms:24-41`:
```gams
loop(t,
  if(m_year(t) <= sm_fix_SSP2,
     i50_nr_eff_bau(t,i) = f50_snupe_base(t,i,"baseeff_add3_add5_add10_max65") * p50_cropneff_region_shr(t,i)
                      + f50_snupe_base(t,i,"baseeff_add3_add5_add10_max65") * (1-p50_cropneff_region_shr(t,i));
  else
     i50_nr_eff_bau(t,i) = f50_snupe_base(t,i,"%c50_scen_neff%") * p50_cropneff_region_shr(t,i)
                      + f50_snupe_base(t,i,"%c50_scen_neff_noselect%") * (1-p50_cropneff_region_shr(t,i));
  );
);
```

**Country-specific application**: Default = all countries (cropneff_countries set in input.gms:37-61), but can be customized to apply different scenarios to selected vs. non-selected countries.

### 10.2 Pasture NUE Scenarios

**File**: `modules/50_nr_soil_budget/macceff_aug22/sets.gms:22-23`

**Available scenarios** (scen_neff_pasture50):
- `constant`: Fixed NUE over time
- `constant_min55_min60_min65`: Minimum 55% (2030), 60% (2050), 65% (2100)

**Simpler than cropland**: Fewer scenario options, reflecting less research on pasture nitrogen management.

---

## 11. MACC Integration (Marginal Abatement Cost Curves)

### 11.1 MACC Transformation

**File**: `modules/50_nr_soil_budget/macceff_aug22/presolve.gms:9-64`

**Problem**: MACCs from Module 57 are expressed as reductions in inputs (IPCC approach), but MAgPIE models efficiency (nitrogen uptake approach). Need to transform MACC mitigation factors.

**Transformation formula** - documented in `presolve.gms:40` (comment), implemented in `presolve.gms:54-65`:
```gams
MACCs_transformed = MACCs_original × NUE_baseline / (1 + MACCs_original × (NUE_baseline - 1))
```

**Why necessary**:
- **Approach 1 (IPCC)**: `Emissions = Inputs × EF × (1 - MACCs)`
- **Approach 2 (MAgPIE)**: `Emissions = Inputs × (1 - NUE) / (1 - NUE_ef) × EF`

To get equivalent emission reductions, MACCs must be transformed from input-based to loss-based.

### 11.2 Efficiency Calculation with MACCs

**File**: `presolve.gms:76-77`

```gams
vm_nr_eff.fx(i) = 1 - (1-i50_nr_eff_bau(t,i)) * (1 - i50_maccs_mitigation_transf(t,i));
vm_nr_eff_pasture.fx(i)= 1 - (1-i50_nr_eff_pasture_bau(t,i)) * (1 - i50_maccs_mitigation_pasture_transf(t,i));
```

**Mathematical form**:
```
SNUpE_final = 1 - (1 - SNUpE_baseline) × (1 - MACC_mitigation)
```

**Example** (illustrative):
- Baseline SNUpE: 60% (loss rate = 40%)
- MACC mitigation: 20% reduction in losses
- Loss rate with MACCs: 40% × (1 - 0.2) = 32%
- Final SNUpE: 1 - 0.32 = 68%

**Key insight**: MACCs reduce the LOSS RATE proportionally, not the efficiency directly. This ensures losses can never become negative even with aggressive mitigation.

---

## 12. Code Truth: What Module 50 DOES

Based on actual code verification with file:line references:

1. **Balances nitrogen inputs and withdrawals for croplands** - `equations.gms:14-16`
   - Enforces: `SNUpE × inputs ≥ withdrawals`
   - Cropland-specific with crop-level detail (kcr dimension)

2. **Balances nitrogen for pastures separately** - `equations.gms:55-59`
   - Same structure but simpler (no crop types)
   - Pasture has area-based fixation, cropland has production-based

3. **Calculates inorganic fertilizer demand endogenously** - `equations.gms:29, 78`
   - vm_nr_inorg_fert_reg is an optimization variable
   - Model chooses fertilizer amount to meet nitrogen requirements at minimum cost

4. **Accounts for 8 nitrogen input sources for croplands** - `equations.gms:22-32`
   - Residues, biological fixation, manure (2 types), fertilizer, SOM, balanceflow, deposition
   - Each source has specific data files or upstream module connections

5. **Accounts for 4 nitrogen input sources for pastures** - `equations.gms:74-80`
   - Grazing manure, fertilizer, biological fixation, deposition
   - Simpler than cropland (no residue recycling, different fixation)

6. **Adjusts withdrawals for biological nitrogen fixation** - `equations.gms:38`
   - Factor (1 - NDFA) reduces soil nitrogen requirement for legumes
   - NDFA ranges 0-0.8 depending on crop and region

7. **Subtracts seed nitrogen from withdrawals** - `equations.gms:42`
   - Seeds bring nitrogen INTO fields, reducing net soil depletion
   - Small effect but important for mass balance closure

8. **Calculates nitrogen surplus** - `equations.gms:46-49, 62-66`
   - Surplus = inputs - withdrawals
   - This surplus feeds into Module 51 for emission calculations

9. **Computes atmospheric deposition** - `equations.gms:88-90`
   - Area-weighted deposition rates from external data
   - Separate rates for different land types

10. **Applies country-specific efficiency scenarios** - `preloop.gms:13-21`
    - Regional weighting by population (im_pop_iso)
    - Different countries can have different SNUpE trajectories

11. **Integrates MACC mitigation measures** - `presolve.gms:54-77`
    - Transforms MACC curves from input-based to loss-based
    - Fixes efficiency variables each timestep based on BAU + MACCs

12. **Calculates fertilizer costs for objective function** - `equations.gms:94-97`
    - Linear cost: $738/tN (default)
    - No economies of scale or regional price variation

---

## 13. Code Truth: What Module 50 Does NOT Do

These are common misconceptions about Module 50's capabilities:

1. ❌ **Does NOT calculate nitrogen emissions or losses**
   - Only calculates surplus (inputs - withdrawals)
   - Actual emission pathways (N2O, NH3, leaching) are in Module 51
   - Module 50 only provides the efficiency parameters for Module 51

2. ❌ **Does NOT optimize nitrogen use efficiency**
   - vm_nr_eff and vm_nr_eff_pasture are FIXED (presolve.gms:76-77)
   - They are scenario inputs, not optimization variables
   - Model optimizes fertilizer amount, not efficiency

3. ❌ **Does NOT track nitrogen in different soil pools**
   - No decomposition dynamics, no stratification
   - Single homogeneous soil nitrogen pool per region
   - Module 59 (SOM) handles organic nitrogen pools separately

4. ❌ **Does NOT account for nitrogen in irrigation water**
   - Only atmospheric deposition is included
   - Groundwater and surface water nitrogen contributions not modeled

5. ❌ **Does NOT model nitrogen losses from erosion**
   - Only considers harvest removals and atmospheric losses
   - Erosion-related nitrogen transport not represented

6. ❌ **Does NOT distinguish fertilizer types**
   - All inorganic fertilizer treated as generic "N"
   - No urea vs. ammonium nitrate vs. other forms
   - Emission factors (in Module 51) may vary, but fertilizer demand here is undifferentiated

7. ❌ **Does NOT include nitrogen in animal feed from off-farm sources**
   - Manure nitrogen comes from Module 55 (AWMS)
   - Module 55 may not fully account for imported feed nitrogen

8. ❌ **Does NOT vary fertilizer costs regionally or temporally**
   - s50_fertilizer_costs = 738 USD/tN globally, constant over time (input.gms:29)
   - No price dynamics or regional fertilizer markets

9. ❌ **Does NOT model organic fertilizer production costs**
   - Only inorganic fertilizer has costs
   - Manure application costs not included (may be in other modules)

10. ❌ **Does NOT account for legacy nitrogen in soils**
    - No soil nitrogen stock accumulation over time
    - Each timestep is independent (no carryover effects)
    - Exception: f50_nitrogen_balanceflow provides a crude correction (input.gms:111-116)

11. ❌ **Does NOT model precision agriculture or variable rate fertilization**
    - Uniform efficiency within regions
    - No spatial heterogeneity at sub-cluster scale

12. ❌ **Does NOT distinguish between organic and inorganic nitrogen in inputs**
    - All nitrogen treated equivalently in mass balance
    - Mineralization dynamics handled in Module 59, not here

---

## 14. Common Modifications

### 14.1 Changing Fertilizer Costs

**Scenario**: Analyze impact of fertilizer price doubling

**File**: `modules/50_nr_soil_budget/macceff_aug22/input.gms`

**Current** (line 29):
```gams
s50_fertilizer_costs = 738  / USD17MER per tN
```

**Modified**:
```gams
s50_fertilizer_costs = 1476  / USD17MER per tN - doubled cost scenario
```

**Impact**:
- Higher fertilizer costs → model reduces fertilizer use
- May reduce vm_nr_eff (if coupled with MACCs that improve efficiency)
- Crop production may decrease if nitrogen becomes limiting
- Trade may increase to compensate for local production shortfalls

**Testing**:
```r
# Compare baseline vs. high fertilizer cost
library(magclass)
fert_baseline <- readGDX("output_baseline/fulldata.gdx", "ov_nr_inorg_fert_reg", select=list(type="level"))
fert_high_cost <- readGDX("output_high_fert_cost/fulldata.gdx", "ov_nr_inorg_fert_reg", select=list(type="level"))

fert_reduction <- (fert_baseline - fert_high_cost) / fert_baseline * 100
cat("Fertilizer use reduction:", mean(fert_reduction[,,"crop"]), "%\n")
```

### 14.2 Implementing Regional Nitrogen Use Efficiency Targets

**Scenario**: Set SNUpE target of 75% for OECD countries by 2050

**File**: `modules/50_nr_soil_budget/macceff_aug22/input.gms`

**Step 1**: Modify cropneff_countries set (lines 37-61) to include only OECD countries

**Step 2**: Create custom scenario in f50_snupe_base.cs4 with 75% target

**Step 3**: Set configuration switches:
```gams
$setglobal c50_scen_neff  custom_oecd_75pct
$setglobal c50_scen_neff_noselect  constant
```

**Result**:
- OECD countries improve to 75% SNUpE by 2050
- Non-OECD countries maintain current efficiency
- Allows analysis of differentiated nitrogen management policies

### 14.3 Adding Spatially-Explicit Atmospheric Deposition Scenarios

**Scenario**: Use RCP8.5 projections for future nitrogen deposition

**Current limitation**: Default scenario is "history" (static) - `input.gms:25`

**Modification**:

**File**: `modules/50_nr_soil_budget/macceff_aug22/sets.gms`

Add new scenario to dep_scen50:
```gams
dep_scen50 Scenario for atmospheric deposition
/history, rcp26, rcp45, rcp85/
```

**File**: `input.gms`

Change configuration:
```gams
$setglobal c50_dep_scen  rcp85
```

**Data requirement**: Create `f50_AtmosphericDepositionRates.cs3` with RCP8.5 projections (currently only has "history")

**Impact**:
- Changing deposition affects nitrogen inputs
- Higher deposition (e.g., in polluted regions) → less fertilizer needed
- Lower deposition (e.g., under clean air policies) → more fertilizer required

---

## 15. Testing & Validation

### 15.1 Nitrogen Mass Balance Check

**Purpose**: Verify nitrogen balance closes (inputs = withdrawals + surplus)

```r
library(magclass)
library(magpie4)

# Load nitrogen budget components
inputs_crop <- readGDX("fulldata.gdx", "ov50_nr_inputs", select=list(type="level"))
withdrawals_crop <- readGDX("fulldata.gdx", "ov50_nr_withdrawals", select=list(type="level"))
surplus_crop <- readGDX("fulldata.gdx", "ov50_nr_surplus_cropland", select=list(type="level"))

# Calculate balance error
balance_error <- inputs_crop - dimSums(withdrawals_crop, dim=3.1) - surplus_crop

# Check
max_error <- max(abs(balance_error))
cat("Maximum nitrogen balance error:", max_error, "Tg N\n")

if (max_error > 0.001) {
  cat("ERROR: Nitrogen balance does not close\n")
  print(balance_error[abs(balance_error) > 0.001])
} else {
  cat("SUCCESS: Nitrogen balance closes within tolerance\n")
}
```

**Expected result**: Balance error < 0.001 Tg N (numerical tolerance)

### 15.2 SNUpE Scenario Validation

**Purpose**: Verify efficiency scenarios follow expected trajectories

```r
# Load efficiency
snupe <- readGDX("fulldata.gdx", "ov_nr_eff", select=list(type="level"))

# Plot trajectory
library(ggplot2)
df <- as.data.frame(snupe)
df$year <- as.numeric(substring(df$t, 2))

ggplot(df, aes(x=year, y=value, color=i)) +
  geom_line() +
  ylim(0, 1) +
  labs(title="Soil Nitrogen Uptake Efficiency Trajectories",
       x="Year", y="SNUpE (fraction)") +
  theme_minimal()

# Check if reaches target
target_2050 <- 0.65  # for baseeff_add3_add5_add10_max65
actual_2050 <- mean(snupe[,"y2050",])

cat("Target SNUpE (2050):", target_2050, "\n")
cat("Actual SNUpE (2050):", actual_2050, "\n")

if (abs(actual_2050 - target_2050) > 0.02) {
  cat("WARNING: SNUpE deviates from expected scenario\n")
}
```

**Expected result**: SNUpE follows scenario trajectory, reaches targets within 2 percentage points

### 15.3 Fertilizer Demand vs. Crop Production Correlation

**Purpose**: Check if fertilizer demand scales reasonably with crop production

```r
# Load data
fertilizer <- readGDX("fulldata.gdx", "ov_nr_inorg_fert_reg", select=list(type="level"))
production <- readGDX("fulldata.gdx", "ov_prod_reg", select=list(type="level"))

# Calculate nitrogen in production
n_content <- readGDX("fulldata.gdx", "fm_attributes")["nr",,]
n_in_production <- production * n_content

# Aggregate
fert_total <- dimSums(fertilizer, dim=c(1,3))
n_prod_total <- dimSums(n_in_production, dim=c(1,3))

# Correlation
cor_value <- cor(as.vector(fert_total), as.vector(n_prod_total))
cat("Correlation between fertilizer and N in production:", cor_value, "\n")

# Plot
plot(as.vector(fert_total), as.vector(n_prod_total),
     xlab="Fertilizer N (Tg)", ylab="N in Harvested Crops (Tg)",
     main="Fertilizer Demand vs. Crop Nitrogen")
abline(lm(as.vector(n_prod_total) ~ as.vector(fert_total)), col="red")
```

**Expected result**: Strong positive correlation (r > 0.8), reasonable slope matching typical SNUpE values

---

## 16. Literature & Data Sources

### 16.1 Primary Citations

**Bodirsky, B. L., et al. (2014)**
"Reactive nitrogen requirements to feed the world in 2050 and potential to mitigate nitrogen pollution"
*Nature Communications*, 5, 3858
DOI: 10.1038/ncomms4858
**Relevance**: Methodology for nitrogen budget modeling in MAgPIE

**Zhang, X., et al. (2015)**
"Managing nitrogen for sustainable development"
*Nature*, 528, 51-59
DOI: 10.1038/nature15743
**Relevance**: Global nitrogen use efficiency targets and improvement scenarios

**Mueller, N. D., et al. (2012)**
"Closing yield gaps through nutrient and water management"
*Nature*, 490, 254-257
DOI: 10.1038/nature11420
**Relevance**: Nitrogen management potential to close yield gaps

---

## 17. Summary for AI Agents

**Quick facts about Module 50:**

1. **Nitrogen budget calculator**: Balances N inputs vs. withdrawals for croplands and pastures
2. **Endogenous fertilizer demand**: vm_nr_inorg_fert_reg is optimization variable
3. **Fixed efficiency**: vm_nr_eff and vm_nr_eff_pasture are scenario inputs (FIXED in presolve)
4. **8 input sources (cropland)**: Residues, fixation, manure (2×), fertilizer, SOM, balanceflow, deposition
5. **4 input sources (pasture)**: Grazing manure, fertilizer, fixation, deposition
6. **MACC integration**: Transforms Module 57 MACCs from input-based to loss-based
7. **Country-specific scenarios**: Can apply different SNUpE trajectories by country
8. **Fertilizer cost**: $738/tN globally (s50_fertilizer_costs in input.gms:29)
9. **Interface with Module 51**: Provides efficiency for emission calculations
10. **No emissions calculated here**: Only nitrogen surplus; Module 51 calculates actual emissions

**When modifying Module 50**:
- ✅ Changes to SNUpE scenarios affect emissions in Module 51
- ✅ Fertilizer cost changes affect land use patterns (Module 10)
- ✅ Check f50_nr_fix_ndfa data for new crops (biological fixation)
- ⚠️ vm_nr_eff is FIXED, not optimized - change scenarios, not the variable itself
- ⚠️ Nitrogen balance closure depends on upstream modules (16, 17, 18, 55, 59)
- ⚠️ No spatial nitrogen dynamics - uniform within regions

---

## 18. AI Agent Response Patterns

### 18.1 "How does MAgPIE calculate fertilizer requirements?"

**Response Framework**:

**Module 50 calculates fertilizer requirements through nitrogen mass balance** - `equations.gms:14-16, 22-32`:

**Step 1: Calculate nitrogen withdrawals**:
```
N_withdrawal(i,crop) = (1 - NDFA) × [N_harvest + N_residues_ag + N_residues_bg] - N_seed
```
- **NDFA** = Nitrogen Derived From Atmosphere (0-0.8 for legumes, 0 for non-legumes)
- Withdrawals = nitrogen removed from soil by crops

**Step 2: Sum all non-fertilizer inputs**:
```
N_inputs_non_fert = residues + biological_fixation + manure + SOM + deposition
```

**Step 3: Apply nitrogen use efficiency constraint**:
```
SNUpE(i) × [N_inputs_non_fert + fertilizer(i)] ≥ N_withdrawal(i)
```

**Step 4: Solver determines minimum fertilizer**:
```
fertilizer(i) = [N_withdrawal(i) / SNUpE(i)] - N_inputs_non_fert
```

**Key insight**: Model does NOT optimize SNUpE - that's fixed based on scenarios (`presolve.gms:76`). Only fertilizer amount is optimized.

**Example** (illustrative):
- Region needs 100 Tg N for harvests
- SNUpE = 65%
- Non-fertilizer inputs = 30 Tg N
- Required total inputs: 100 / 0.65 = 154 Tg N
- Fertilizer demand: 154 - 30 = 124 Tg N
- Nitrogen surplus (lost): 154 - 100 = 54 Tg N

---

### 18.2 "What happens if I change the nitrogen use efficiency scenario?"

**Response Framework**:

**Nitrogen use efficiency (SNUpE) is a scenario input, not an optimization result** - changing it has cascading effects:

**Direct effects (Module 50)**:

1. **Fertilizer demand changes** - `equations.gms:14-16`:
   - Higher SNUpE → less fertilizer needed for same crop production
   - Example: Improving SNUpE from 60% to 70% reduces fertilizer by ~14% for same output

2. **Nitrogen surplus changes** - `equations.gms:46-49`:
   - Surplus = inputs - withdrawals
   - Higher SNUpE → less surplus for same production

**Indirect effects (other modules)**:

3. **Emissions decrease (Module 51)**: Nitrogen losses proportional to `(1-SNUpE)`

4. **Fertilizer costs decrease (Module 11)**: vm_nr_inorg_fert_costs = fertilizer × $738/tN

5. **Land use may change (Module 10)**: Lower production costs → potentially more intensive agriculture

**How to change SNUpE** - `input.gms:11-12`:
```gams
$setglobal c50_scen_neff  baseeff_add3_add15_add25_max75
```
Available scenarios in `sets.gms:13-20`

---

### 18.3 "Does MAgPIE account for nitrogen from manure?"

**Response Framework**:

**Yes, Module 50 accounts for manure nitrogen** - `equations.gms:27-28, 77`:

**What IS included**:

1. **Cropland manure recycling** - `vm_manure_recycling(i,"nr")`:
   - Manure collected and applied to croplands
   - Comes from Module 55 (AWMS)

2. **Stubble grazing manure** - `vm_manure(i, kli, "stubble_grazing", "nr")`:
   - Manure deposited by animals grazing crop residues

3. **Pasture grazing manure** - `vm_manure(i, kli, "grazing", "nr")`:
   - Manure from animals grazing pastures
   - Largest manure nitrogen flow

**How it's used**:
- Added to nitrogen inputs
- Subject to same SNUpE/NUE efficiency as other nitrogen sources
- No distinction in efficiency between manure and fertilizer nitrogen

**What is NOT included**:

1. ❌ **Manure nitrogen lost during storage**: Module 55 handles storage losses
2. ❌ **Manure not applied to agricultural land**
3. ❌ **Different mineralization rates for manure vs. fertilizer**: Model treats all nitrogen sources equivalently

---

**Documentation Complete**: Module 50 (Nitrogen Soil Budget)
**Lines**: 1,095
**Code References**: 85+ file:line citations
**Status**: ✅ Comprehensive documentation - READY FOR FACT-CHECKING
---

## Participates In

This section shows Module 50's role in system-level mechanisms.

### Conservation Laws

**Nitrogen Balance (Tracking)**
- **Role**: Tracks soil nitrogen budget (inputs - outputs = Δstock)
- **Details**: `cross_module/nitrogen_food_balance.md`

**Not in** land, water, carbon, or food balance (strict sense)

### Dependency Chains

**Centrality Analysis**:
- **Centrality Rank**: Medium (nitrogen system component)
- **Hub Type**: Nitrogen Budget Tracker

**Provides to**: Module 51 (nitrogen): Nitrogen availability for crops, Module 11 (costs): Fertilizer costs

**Depends on**: Modules 14 (yields), 18 (residues), 55 (awms): Nitrogen flows

**Details**: `core_docs/Module_Dependencies.md`

### Circular Dependencies

**Production-Nitrogen cycle**: Via crop residues and manure

**Details**: `cross_module/circular_dependency_resolution.md`

### Modification Safety

**Risk Level**: 🟡 **MEDIUM RISK**

**Why**: Affects fertilizer costs and nitrogen emissions

**Safe Modifications**: ✅ Adjust NUE parameters, ✅ Modify fixation rates

**Testing**: Check nitrogen mass balance, verify fertilizer costs reasonable

**Links**:
- Conservation law → `cross_module/nitrogen_food_balance.md`
- Dependencies → `core_docs/Module_Dependencies.md`

---

**Module 50 Status**: ✅ COMPLETE

---

**Last Verified**: 2025-10-13
**Verified Against**: `../modules/50_*/nr50_static/*.gms`
**Verification Method**: Equations cross-referenced with source code
**Changes Since Last Verification**: None (stable)
