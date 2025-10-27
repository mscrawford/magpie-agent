# Module 60: Bioenergy (1st2ndgen_priced_feb24)

**Status**: Fully Verified
**Realization**: `1st2ndgen_priced_feb24` (1st and 2nd generation with pricing, February 2024)
**Alternative**: `1stgen_priced_dec18` (1st generation only, older)
**Equations**: 5
**Lines of Code**: ~250
**Authors**: Jan Philipp Dietrich, Jan Steinhauser

---

## Overview

Module 60 (Bioenergy) provides regional and crop-specific bioenergy demand `vm_dem_bioen(i,kall)` to Module 16 (Demand) (`module.gms:10-11`). The module distinguishes between **1st generation** bioenergy (oils, ethanol from food crops) and **2nd generation** bioenergy (dedicated energy crops like bioenergy grasses/trees, plus crop residues) (`equations.gms:9-14`).

**Core Function**: Exogenous bioenergy demand scenarios → Constraint equations → `vm_dem_bioen(i,kall)` provided to demand module → Land allocation for bioenergy production

**Key Mechanism**: Bioenergy demand split into three streams with different substitutability rules:
1. **1st generation**: Fixed minimum trajectories (oils, ethanol) until 2050, then phased out (`equations.gms:23-28`)
2. **2nd generation dedicated**: Bioenergy grasses and trees, fully substitutable based on energy content, constrained globally OR regionally (`equations.gms:30-53`)
3. **2nd generation residues**: Crop residues, fully substitutable based on energy content, constrained regionally (`equations.gms:55-64`)

**Critical Interface**: Provides `vm_dem_bioen(i,kall)` to Module 16 (Demand), which aggregates with food, feed, material, and seed demands (`module.gms:11`). Also provides `vm_bioenergy_utility(i)` (negative costs) to Module 11 (Costs) for bioenergy production incentives beyond minimum demand (`module.gms:15-16`).

---

## Core Equations (5 total)

### 1. Total Bioenergy Demand (`q60_bioenergy`)

**Purpose**: Calculate total regional bioenergy demand in energy units (GJ) from all sources

**Formula** (`equations.gms:16-21`):
```
vm_dem_bioen(i2,kall) * fm_attributes("ge",kall) =g=
    sum(ct, i60_1stgen_bioenergy_dem(ct,i2,kall))
    + v60_2ndgen_bioenergy_dem_dedicated(i2,kall)
    + v60_2ndgen_bioenergy_dem_residues(i2,kall)
```

**Dimensions**:
- `i`: Region
- `kall`: All products (oils, ethanol, betr, begr, residues)

**Left-Hand Side**:
- `vm_dem_bioen(i2,kall)`: Bioenergy demand in mass units (mio. tDM per yr) (`declarations.gms:20`)
- `fm_attributes("ge",kall)`: Gross energy content (GJ per tDM)
- **Product**: Total bioenergy demand in energy units (mio. GJ per yr)

**Right-Hand Side Components**:
1. **1st generation bioenergy**: `i60_1stgen_bioenergy_dem(ct,i2,kall)` (mio. GJ per yr)
   - Fixed trajectories for oils and ethanol from input data (`presolve.gms:15-16, 23-24`)
   - Based on established and planned bioenergy policies (Lotze-Campen et al. 2014) (`equations.gms:23-25`)
2. **2nd generation dedicated**: `v60_2ndgen_bioenergy_dem_dedicated(i2,kall)` (mio. GJ per yr)
   - Variable demand for bioenergy grasses (betr) and trees (begr)
   - Fully substitutable based on energy content (`equations.gms:12-13`)
3. **2nd generation residues**: `v60_2ndgen_bioenergy_dem_residues(i2,kall)` (mio. GJ per yr)
   - Demand for crop residues (kres)
   - Fully substitutable based on energy content (`equations.gms:13-14`)

**Constraint Type**: Inequality (≥) - actual mass-based demand (converted to energy) must meet or exceed sum of energy-based demands from all three sources

**Purpose**: Ensures that the total bioenergy production (in mass terms, converted to energy equivalents via gross energy attributes) satisfies the minimum requirements from 1st generation policies plus 2nd generation demand targets.

**Units**: mio. GJ per yr (all terms)

---

### 2. Global 2nd Generation Dedicated Bioenergy Demand (`q60_bioenergy_glo`)

**Purpose**: Constrain global 2nd generation dedicated bioenergy demand (active when `c60_biodem_level = 0`)

**Formula** (`equations.gms:43-44`):
```
sum((kbe60,i2), v60_2ndgen_bioenergy_dem_dedicated(i2,kbe60)) =g=
    sum((ct,i2), i60_bioenergy_dem(ct,i2)) * (1 - c60_biodem_level)
```

**Mechanism** (`equations.gms:33-41`):
- `c60_biodem_level`: Switch (0 = global demand, 1 = regional demand) (`input.gms:37`)
- **If `c60_biodem_level = 0` (global)**:
  - Right-hand side = `sum(i, i60_bioenergy_dem(ct,i))` (total global demand)
  - Constraint active: Global sum of dedicated 2nd gen bioenergy ≥ global target
  - Regional distribution optimized by model based on comparative advantage
- **If `c60_biodem_level = 1` (regional)**:
  - Right-hand side = 0 (constraint inactive)
  - Regional constraint `q60_bioenergy_reg` becomes active instead

**Dimensions**:
- `kbe60`: 2nd generation bioenergy crops (betr, begr) (`sets.gms:111-112`)
- `i`: Region (summed globally)

**Purpose**: Allows global bioenergy demand target to be met flexibly across regions (model chooses lowest-cost regions for bioenergy production).

**Units**: mio. GJ per yr

---

### 3. Regional 2nd Generation Dedicated Bioenergy Demand (`q60_bioenergy_reg`)

**Purpose**: Constrain regional 2nd generation dedicated bioenergy demand (active when `c60_biodem_level = 1`)

**Formula** (`equations.gms:46-47`):
```
sum(kbe60, v60_2ndgen_bioenergy_dem_dedicated(i2,kbe60)) =g=
    sum(ct, i60_bioenergy_dem(ct,i2)) * c60_biodem_level
```

**Mechanism** (`equations.gms:33-41`):
- **If `c60_biodem_level = 1` (regional)**:
  - Right-hand side = `i60_bioenergy_dem(ct,i2)` (regional demand target)
  - Constraint active: Each region's dedicated 2nd gen bioenergy ≥ regional target
  - Regional demand must be met locally (no spatial substitution)
- **If `c60_biodem_level = 0` (global)**:
  - Right-hand side = 0 (constraint inactive)
  - Global constraint `q60_bioenergy_glo` becomes active instead

**Dimensions**:
- `i`: Region (constraint per region)
- `kbe60`: 2nd generation bioenergy crops (betr, begr)

**Purpose**: Ensures each region meets its bioenergy target locally (e.g., for regionally-specific bioenergy policies).

**Units**: mio. GJ per yr

**Implementation Note** (`equations.gms:49-53`): Both `q60_bioenergy_glo` and `q60_bioenergy_reg` serve the same purpose (ensure 2nd gen dedicated bioenergy demand ≥ target), but only one is active at a time based on `c60_biodem_level` switch.

---

### 4. 2nd Generation Residue Demand (`q60_res_2ndgenBE`)

**Purpose**: Constrain regional demand for crop residues used in 2nd generation bioenergy

**Formula** (`equations.gms:61-64`):
```
sum(kres, v60_2ndgen_bioenergy_dem_residues(i2,kres)) =g=
    sum(ct, i60_res_2ndgenBE_dem(ct,i2))
```

**Dimensions**:
- `i`: Region
- `kres`: Residue types (subset of `kall`)

**Mechanism** (`equations.gms:55-59`):
- `i60_res_2ndgenBE_dem(t,i)`: Exogenous residue demand for 2nd generation bioenergy (mio. GJ per yr)
- Based on estimation that ~33% of available residues for recycling on cropland can be used for 2nd generation bioenergy (`equations.gms:57-58`)
- Varies by SSP scenario (driven by population and GDP) (`equations.gms:58-59`)

**Constraint Type**: Inequality (≥) - sum of residue demands across residue types must meet or exceed scenario-specific target

**Residue Availability Context**: Module 60 does NOT calculate residue availability - it only specifies demand. Residue supply is calculated in Module 18 (Residues) based on crop production and residue-to-product ratios.

**Units**: mio. GJ per yr

---

### 5. Bioenergy Production Incentive (`q60_bioenergy_incentive`)

**Purpose**: Provide financial incentive (negative cost / utility) for bioenergy production beyond exogenous minimum demand

**Formula** (`equations.gms:73-75`):
```
vm_bioenergy_utility(i2) =e=
    sum((ct,k1st60), vm_dem_bioen(i2,k1st60) * fm_attributes("ge",k1st60)
        * (-i60_1stgen_bioenergy_subsidy(ct)))
    + sum((ct,kbe60), vm_dem_bioen(i2,kbe60) * fm_attributes("ge",kbe60)
        * (-i60_2ndgen_bioenergy_subsidy(ct)))
```

**Dimensions**:
- `i`: Region
- `k1st60`: 1st generation bioenergy (oils, ethanol) (`sets.gms:114-115`)
- `kbe60`: 2nd generation dedicated (betr, begr) (`sets.gms:111-112`)

**Components**:
1. **1st generation subsidy**:
   - Production (mio. tDM) × energy content (GJ/tDM) = energy output (mio. GJ)
   - Energy output × subsidy (USD17MER per GJ) = total subsidy payment
   - Negative sign → appears as negative cost (utility) in objective function
2. **2nd generation subsidy**:
   - Same calculation for dedicated bioenergy crops (betr, begr)

**Subsidy Values**:
- `i60_1stgen_bioenergy_subsidy(t)`: 1st generation subsidy (USD17MER per GJ) (`declarations.gms:13`)
  - Can be mass-based (constant over time) or energy-based (time-varying) (`equations.gms:68-69`)
  - Default: 6.5 USD17MER per GJ (mass-based, constant) (`input.gms:38`)
- `i60_2ndgen_bioenergy_subsidy(t)`: 2nd generation subsidy (USD17MER per GJ) (`declarations.gms:14`)
  - Energy-based, can vary over time via price implementation scenarios (`presolve.gms:33-34, 40-41, 47-48`)

**Purpose** (`equations.gms:66-71`):
- Incentivize bioenergy production beyond exogenous minimum demand
- Useful for assessing bioenergy production potentials with low or phased-out exogenous demands
- **Warning**: Can create positive feedback loop with endogenous technological change (Module 13) (`equations.gms:70-71`)

**Interface**: `vm_bioenergy_utility(i)` passed to Module 11 (Costs), added to objective function as negative cost (benefit) (`module.gms:15-16`).

**Units**: mio. USD17MER per yr (negative value = benefit)

---

## Bioenergy Types and Sets

Module 60 distinguishes three categories of bioenergy products:

### 1. First Generation Bioenergy (`k1st60`)

**Definition** (`sets.gms:114-115`):
```
k1st60(kall) = / oils, ethanol /
```

**Characteristics**:
- Produced from food crops (oils from oilseeds, ethanol from cereals/sugar crops)
- Fixed minimum demand trajectories based on established bioenergy policies (`equations.gms:23-25`)
- Demand until 2050, then assumed to transition to 2nd generation (`equations.gms:26-28`)
- Can receive subsidies (default: 6.5 USD17MER per GJ) (`input.gms:38`)

**Scenarios** (`sets.gms:117-118`):
- `const2020`: Constant at 2020 levels
- `const2030`: Constant at 2030 levels
- `phaseout2020`: Phase out from 2020

**Data Source** (`input.gms:82-86`):
```
f60_1stgen_bioenergy_dem(t,i,scen1st60,kall)  // mio. GJ per yr
```

### 2. Second Generation Dedicated Bioenergy (`kbe60`)

**Definition** (`sets.gms:111-112`):
```
kbe60(kall) = / betr, begr /
```
- `betr`: Bioenergy trees (woody perennial crops)
- `begr`: Bioenergy grasses (herbaceous perennial crops like switchgrass, miscanthus)

**Characteristics**:
- Fully substitutable based on gross energy content (`equations.gms:12-13`)
- Not produced from food crops (dedicated energy crops grown on agricultural land)
- Demand can be specified globally OR regionally (`c60_biodem_level` switch) (`equations.gms:33-41`)
- Higher estimated efficiency than 1st generation (`equations.gms:27-28`)
- Can receive subsidies (default: 0, configurable) (`input.gms:40`, `presolve.gms:21`)

**Demand Specification**:
- Global demand: Model optimizes regional distribution (`q60_bioenergy_glo` active)
- Regional demand: Each region must meet local target (`q60_bioenergy_reg` active)

### 3. Second Generation Residues (`kres`)

**Subset**: Crop residues (subset of `kall`, not defined in Module 60 sets, defined elsewhere in model)

**Characteristics**:
- By-products of crop production (straw, stover, husks, etc.)
- Fully substitutable based on energy content (`equations.gms:13-14`)
- Low cost (residues are co-products, not dedicated crops)
- Estimated availability: ~33% of residues recyclable on cropland can be used for 2nd generation bioenergy (`equations.gms:57-58`)
- Demand varies by SSP scenario (population and GDP-driven) (`equations.gms:58-59`)

**Scenarios** (`sets.gms:120-121`):
- SSP1-5, SDP, or "off" (no residue demand)

**Data Source** (`input.gms:72-76`):
```
f60_res_2ndgenBE_dem(t,i,scen2ndres60)  // mio. GJ per yr
```

---

## Bioenergy Demand Scenarios

### 2nd Generation Dedicated Bioenergy Scenarios (`scen2nd60`)

Module 60 includes **90+ scenarios** for 2nd generation dedicated bioenergy demand (`sets.gms:15-103`):

**Scenario Families**:
1. **PIK scenarios** (7 scenarios): PIK_GDP, PIK_H2C, PIK_HBL, PIK_HOS, PIK_LIN, PIK_NPI, PIK_OPT
2. **REMIND-MAgPIE R21M42** (18 scenarios): SSP1/2/5 + SDP × (NDC, NPi, PkBudg900/1100/1300)
3. **REMIND-MAgPIE R2M41** (5 scenarios): SSP2 × (NDC, NPi, Budg600/950/1300)
4. **REMIND-MAgPIE R32M46** (16 scenarios): SSP1/2EU/5 + SDP_MC × (NDC, NPi, PkBudg650/1050)
5. **REMIND-MAgPIE R34BC** (4 scenarios): SSP2-PkBudg650 with biochar variants (BCdef, BCpess, CTS01, BM70)
6. **REMIND-MAgPIE R34M410** (12 scenarios): SSP1/2/2_lowEn/3/5 × (NPi2025, PkBudg650/1000, rollBack)
7. **SSPDB IMAGE/REMIND-MAGPIE** (38 scenarios): SSP1/2/5 × (Ref, 19/26/34/45/60)

**Scenario Structure**:
- SSP storylines (socioeconomic pathways)
- Climate policy targets (NDC, NPi, carbon budgets in GtCO2)
- Model coupling (REMIND energy-economy model projections)

**Data Source** (`input.gms:63-67`):
```
f60_bioenergy_dem(t,i,scen2nd60)  // mio. GJ per yr
```

**Selection** (`input.gms:45-46`):
- `c60_2ndgen_biodem`: Selected scenario (default: "R34M410-SSP2-NPi2025")
- `c60_2ndgen_biodem_noselect`: Scenario for non-selected countries (default: same as selected)

**Special Modes** (`input.gms:49-61`):
- `"coupling"`: Read demand from external coupling file (`reg.2ndgen_bioenergy_demand.csv`)
- `"emulator"`: Read global demand from emulator file, divide equally among regions (`glo.2ndgen_bioenergy_demand.csv`)
- `"none"`: Zero 2nd generation demand (`preloop.gms:24`)

### 1st Generation Bioenergy Scenarios (`scen1st60`)

**Options** (`sets.gms:117-118`, `input.gms:79-80`):
- `const2020`: Constant demand at 2020 levels
- `const2030`: Constant demand at 2030 levels
- `phaseout2020`: Phase out from 2020

**Default**: `const2020` (`input.gms:79`)

**Historical Period**: Until `sm_fix_SSP2`, always uses `const2020` scenario regardless of selection (`presolve.gms:15-16`).

### Residue Demand Scenarios (`scen2ndres60`)

**Options** (`sets.gms:120-121`, `input.gms:69-70`):
- SSP1, SSP2, SSP3, SSP4, SSP5, SDP, or "off"

**Default**: `ssp2` (`input.gms:69`)

**Historical Period**: Until `sm_fix_SSP2`, always uses `ssp2` scenario regardless of selection (`presolve.gms:17-18`).

---

## Regional vs. Global Demand Implementation

Module 60 allows bioenergy demand to be specified at **global** or **regional** level, controlled by `c60_biodem_level` switch (`input.gms:37`).

### Global Demand Mode (`c60_biodem_level = 0`)

**Mechanism**:
- `q60_bioenergy_glo` active (`equations.gms:43-44`): Global sum of 2nd gen dedicated bioenergy ≥ global target
- `q60_bioenergy_reg` inactive (right-hand side = 0) (`equations.gms:46-47`)
- Model optimizes regional distribution based on comparative advantage (land availability, yields, costs)

**Use Case**: Global bioenergy policy target (e.g., 100 EJ/yr globally) with flexible regional sourcing.

**Example** (illustrative):
- Global target: 50 mio. GJ per yr
- Model solution might allocate: 30 GJ to Brazil (high yields), 15 GJ to USA (low costs), 5 GJ to sub-Saharan Africa (land availability)
- Regional distribution endogenous to model optimization

### Regional Demand Mode (`c60_biodem_level = 1`, default)

**Mechanism**:
- `q60_bioenergy_reg` active (`equations.gms:46-47`): Each region's 2nd gen dedicated bioenergy ≥ regional target
- `q60_bioenergy_glo` inactive (right-hand side = 0) (`equations.gms:43-44`)
- Regional demand must be met locally (no spatial substitution)

**Use Case**: Region-specific bioenergy policies (e.g., EU biofuel mandate, US Renewable Fuel Standard).

**Example** (illustrative):
- Regional targets: EU 20 GJ, USA 30 GJ, China 10 GJ
- Model solution: Each region produces exactly its target (or more if cost-effective)
- No cross-regional substitution (EU cannot meet its target with imports from USA)

### Country-Level Scenario Selection

**Population-Weighted Regional Share** (`preloop.gms:8-17`):

1. **Country Switch** (`preloop.gms:12-13`):
```
p60_country_switch(iso) = 0
p60_country_switch(scen_countries60) = 1
```
Default: All 249 countries selected (`input.gms:9-33`).

2. **Regional Share Calculation** (`preloop.gms:14-17`):
```
p60_region_BE_shr(t,i) =
    sum(i_to_iso(i,iso), p60_country_switch(iso) * im_pop_iso(t,iso))
    / sum(i_to_iso(i,iso), im_pop_iso(t,iso))
```
- **Numerator**: Population in selected countries within region
- **Denominator**: Total population in region
- **Result**: Share of region affected by selected scenario (0-1)

3. **Demand Blending** (`preloop.gms:30-31`):
```
i60_bioenergy_dem(t,i) =
    f60_bioenergy_dem(t,i,"c60_2ndgen_biodem") * p60_region_BE_shr(t,i)
    + f60_bioenergy_dem(t,i,"c60_2ndgen_biodem_noselect") * (1 - p60_region_BE_shr(t,i))
```
- Weighted average of selected and non-selected scenarios based on population share

**Example** (illustrative):
- Region: South Asia (India, Pakistan, Bangladesh, others)
- Selected countries: India only (60% of South Asia population)
- Selected scenario: High bioenergy demand (100 GJ)
- Non-selected scenario: Low bioenergy demand (20 GJ)
- **Regional demand**: 100 × 0.6 + 20 × 0.4 = 68 GJ

---

## Subsidy and Price Implementation

Module 60 implements bioenergy subsidies/prices with three temporal trajectories, controlled by `c60_price_implementation` switch (`input.gms:44`).

### 1. Linear Price Trajectory (`c60_price_implementation = "lin"`, default)

**Formula** (`presolve.gms:44-49`):
```
if (m_year(t) > sm_fix_SSP2):
    i60_1stgen_bioenergy_subsidy(t) =
        s60_bioenergy_1st_price / (2100 - sm_fix_SSP2) * (m_year(t) - sm_fix_SSP2)
    i60_2ndgen_bioenergy_subsidy(t) =
        s60_bioenergy_2nd_price / (2100 - sm_fix_SSP2) * (m_year(t) - sm_fix_SSP2)
```

**Mechanism**:
- Subsidy starts at 0 in year `sm_fix_SSP2` (typically 2020 or 2025)
- Increases linearly to reach `s60_bioenergy_X_price` in 2100
- **Slope**: `price / (2100 - fix_year)`

**Example** (illustrative, assuming sm_fix_SSP2 = 2020, s60_bioenergy_2nd_price = 80 USD17MER/GJ):
- 2020: 0 USD17MER/GJ
- 2060: 80 / (2100 - 2020) × (2060 - 2020) = 80 / 80 × 40 = 40 USD17MER/GJ
- 2100: 80 USD17MER/GJ

### 2. Exponential Price Trajectory (`c60_price_implementation = "exp"`)

**Formula** (`presolve.gms:29-35`):
```
if (m_year(t) > sm_fix_SSP2):
    i60_1stgen_bioenergy_subsidy(t) =
        (s60_bioenergy_1st_price / 8) * (8^(1 / (2100 - sm_fix_SSP2)))^(m_year(t) - sm_fix_SSP2)
    i60_2ndgen_bioenergy_subsidy(t) =
        (s60_bioenergy_2nd_price / 8) * (8^(1 / (2100 - sm_fix_SSP2)))^(m_year(t) - sm_fix_SSP2)
```

**Mechanism**:
- Subsidy grows exponentially, multiplying by factor of 8 from fix year to 2100
- **Initial value**: `price / 8` in year `sm_fix_SSP2`
- **Growth rate**: `8^(1 / (2100 - fix_year))` per year
- **Final value**: `price` in 2100

**Rationale**: Reflects learning curves and scale economies in bioenergy technologies (costs decline exponentially → subsidies can increase exponentially to maintain competitiveness).

**Example** (illustrative, assuming sm_fix_SSP2 = 2020, s60_bioenergy_2nd_price = 80 USD17MER/GJ):
- 2020: 80 / 8 = 10 USD17MER/GJ
- 2060: 10 × 8^(40/80) = 10 × 8^0.5 ≈ 10 × 2.83 ≈ 28.3 USD17MER/GJ
- 2100: 80 USD17MER/GJ

### 3. Constant Price Trajectory (`c60_price_implementation = "const"`)

**Formula** (`presolve.gms:36-42`):
```
if (m_year(t) > sm_fix_SSP2):
    i60_1stgen_bioenergy_subsidy(t) = s60_bioenergy_1st_price
    i60_2ndgen_bioenergy_subsidy(t) = s60_bioenergy_2nd_price
```

**Mechanism**: Subsidy jumps to constant value `s60_bioenergy_X_price` immediately after fix year, remains constant.

**Use Case**: Policy scenario with fixed subsidy level (e.g., carbon tax at constant level).

### 1st Generation Subsidy Floor

**Enforcement** (`presolve.gms:52-54`):
```
i60_1stgen_bioenergy_subsidy(t)$(i60_1stgen_bioenergy_subsidy(t) < s60_bioenergy_1st_subsidy)
    = s60_bioenergy_1st_subsidy
```

**Mechanism**: 1st generation subsidy cannot fall below `s60_bioenergy_1st_subsidy` (default: 6.5 USD17MER/GJ) (`input.gms:38`).

**Rationale**: Mass-based subsidy baseline (constant over time) vs. energy-based subsidy (time-varying via price implementation) (`equations.gms:68-69`). The higher of the two is used.

### Configuration Parameters

**1st Generation** (`input.gms:38-39`):
- `s60_bioenergy_1st_subsidy`: Mass-based constant subsidy (default: 6.5 USD17MER/GJ)
- `s60_bioenergy_1st_price`: Energy-based time-varying subsidy target for 2100 (default: 0)

**2nd Generation** (`input.gms:40`):
- `s60_bioenergy_2nd_price`: Energy-based time-varying subsidy target for 2100 (default: 0)

**Historical Period**: Until `sm_fix_SSP2`, subsidies use default values (`presolve.gms:19-21`):
- 1st generation: `s60_bioenergy_1st_subsidy` (6.5 USD17MER/GJ)
- 2nd generation: 0

---

## Variable Bounds and Initialization

### Variable Fixing (`presolve.gms:8-12`)

**Non-bioenergy products** (food, feed, material):
```
vm_dem_bioen.fx(i,kap) = 0
```
All livestock products (`kap`) have zero bioenergy demand (fixed).

**Dedicated bioenergy crops**:
```
v60_2ndgen_bioenergy_dem_dedicated.fx(i,kall) = 0  // Fix all to zero
v60_2ndgen_bioenergy_dem_dedicated.up(i,kbe60) = Inf  // Release betr, begr
```
Only bioenergy grasses (begr) and trees (betr) can have positive dedicated 2nd generation demand.

**Residues**:
```
v60_2ndgen_bioenergy_dem_residues.fx(i,kall) = 0  // Fix all to zero
v60_2ndgen_bioenergy_dem_residues.up(i,kres) = Inf  // Release residues
```
Only crop residues (`kres`) can have positive 2nd generation residue demand.

**Purpose**: Restrict bioenergy demand to appropriate product types (1st gen: oils/ethanol, 2nd gen dedicated: betr/begr, 2nd gen residues: kres).

### Minimum Demand Floor (`presolve.gms:56-57`)

**Enforcement**:
```
i60_bioenergy_dem(t,i)$(i60_bioenergy_dem(t,i) < s60_2ndgen_bioenergy_dem_min)
    = s60_2ndgen_bioenergy_dem_min
```

**Parameter**: `s60_2ndgen_bioenergy_dem_min` (default: 1 mio. GJ per yr) (`input.gms:41`)

**Purpose**: Prevent zero or very small bioenergy demand that would cause numerical issues (zero prices, division by zero in postprocessing).

**Effect**: Each region has minimum 1 mio. GJ per yr 2nd generation dedicated bioenergy demand even in "no bioenergy" scenarios.

---

## Interface Variables

### Outputs to Other Modules

**1. Regional Bioenergy Demand** (`declarations.gms:20`):
```
vm_dem_bioen(i,kall)  // mio. tDM per yr
```
- **To Module 16 (Demand)**: Aggregated with food, feed, material, seed demands to create total commodity demand (`module.gms:11`)
- **Dimensions**: Region × all products (oils, ethanol, betr, begr, residues)
- **Constraint**: `q60_bioenergy` ensures demand (converted to energy units) meets minimum requirements

**2. Bioenergy Production Utility** (`declarations.gms:26`):
```
vm_bioenergy_utility(i)  // mio. USD17MER per yr (negative cost)
```
- **To Module 11 (Costs)**: Added to objective function as negative cost (incentive for bioenergy production) (`module.gms:15-16`)
- **Formula**: Production × subsidy × (-1) for 1st and 2nd generation bioenergy (`q60_bioenergy_incentive`)

### Inputs from Other Modules

**1. Gross Energy Content** (from data):
```
fm_attributes("ge",kall)  // GJ per tDM
```
- Converts mass-based demand (`vm_dem_bioen`, tDM) to energy-based demand (GJ)
- Used in `q60_bioenergy` to ensure energy equivalence (`equations.gms:17`)
- Used in `q60_bioenergy_incentive` to calculate energy-based subsidies (`equations.gms:74-75`)

**2. Population** (from Module 09):
```
im_pop_iso(t,iso)  // mio. people
```
- Used to calculate population-weighted regional shares for scenario selection (`preloop.gms:17`)
- Determines country influence on regional bioenergy demand when subset of countries selected

---

## Configuration Options

### Bioenergy Demand Level

**Switch** (`input.gms:37`):
```
c60_biodem_level = 1
```
**Options**:
- `0`: Global demand (model optimizes regional distribution)
- `1`: Regional demand (each region meets local target) - **default**

**Effect**: Activates either `q60_bioenergy_glo` or `q60_bioenergy_reg` constraint.

### 2nd Generation Dedicated Bioenergy Scenario

**Switches** (`input.gms:45-46`):
```
c60_2ndgen_biodem = "R34M410-SSP2-NPi2025"
c60_2ndgen_biodem_noselect = "R34M410-SSP2-NPi2025"
```

**Options**: 90+ scenarios from REMIND-MAgPIE, SSPDB, PIK (`sets.gms:15-103`)

**Special modes**:
- `"coupling"`: Read from external coupling file
- `"emulator"`: Read from emulator file (global, divided by regions)
- `"none"`: Zero 2nd generation demand

**Noselect Scenario**: Applied to non-selected countries (typically same as main scenario unless testing country-specific policies).

### 2nd Generation Residue Demand Scenario

**Switch** (`input.gms:69`):
```
c60_res_2ndgenBE_dem = "ssp2"
```

**Options**: ssp1, ssp2, ssp3, ssp4, ssp5, sdp, off

**Effect**: Selects residue demand trajectory based on SSP scenario.

### 1st Generation Bioenergy Scenario

**Switch** (`input.gms:79`):
```
c60_1stgen_biodem = "const2020"
```

**Options**: const2020, const2030, phaseout2020

**Effect**: Selects 1st generation demand trajectory (constant at 2020/2030 levels or phase out).

### Price Implementation

**Switch** (`input.gms:44`):
```
c60_price_implementation = "lin"
```

**Options**:
- `"lin"`: Linear increase to 2100 - **default**
- `"exp"`: Exponential increase (factor of 8 by 2100)
- `"const"`: Constant after fix year

**Effect**: Determines temporal trajectory of bioenergy subsidies.

### Price Levels

**1st Generation** (`input.gms:38-39`):
- `s60_bioenergy_1st_subsidy = 6.5`: Constant mass-based subsidy (USD17MER per GJ)
- `s60_bioenergy_1st_price = 0`: Energy-based price target for 2100 (USD17MER per GJ)

**2nd Generation** (`input.gms:40`):
- `s60_bioenergy_2nd_price = 0`: Price target for 2100 (USD17MER per GJ)

**Minimum Demand Floor** (`input.gms:41`):
- `s60_2ndgen_bioenergy_dem_min = 1`: Minimum 2nd gen demand per region (mio. GJ per yr)

---

## Key Assumptions and Limitations

### 1. Exogenous Demand Trajectories

**Assumption**: All bioenergy demand (1st generation, 2nd generation dedicated, 2nd generation residues) specified exogenously via scenario input files (`preloop.gms:20-36`, `presolve.gms:15-26`).

**Implication**: Bioenergy demand does NOT respond endogenously to:
- Energy prices (fossil fuel prices, electricity prices)
- Climate policies (carbon taxes beyond those embedded in scenarios)
- Land availability constraints (demand fixed even if land scarce)
- Technological change in bioenergy conversion (demand in energy units, not influenced by conversion efficiency improvements)

**Exception**: Subsidies (`q60_bioenergy_incentive`) provide incentive for production beyond minimum demand, allowing endogenous expansion if cost-effective (`equations.gms:66-71`).

### 2. 1st Generation Phase-Out Assumption

**Assumption** (`equations.gms:23-28`): 1st generation bioenergy demand trajectories only extend until 2050. After 2050, assumed that all bioenergy production transitions to 2nd generation (dedicated crops + residues) due to higher efficiency.

**Implication**:
- Model does NOT allow 1st generation bioenergy (oils, ethanol from food crops) post-2050 even if cost-competitive
- Reflects policy assumption that 1st generation bioenergy phased out due to food-fuel competition concerns
- May underestimate 1st generation if technological improvements (e.g., advanced fermentation) make food-crop bioenergy more sustainable

### 3. Perfect Substitutability Within Categories

**Assumption** (`equations.gms:12-14`):
- 2nd generation dedicated crops (betr, begr) fully substitutable based on gross energy content
- 2nd generation residues (all `kres` types) fully substitutable based on gross energy content

**Implication**: Model does NOT account for:
- Conversion technology specificity (e.g., some technologies optimized for woody vs. herbaceous biomass)
- Energy quality differences (e.g., lignin content affects conversion efficiency)
- Infrastructure constraints (e.g., existing ethanol plants cannot switch to advanced biofuels without investment)
- Regional preferences or mandates for specific bioenergy types

### 4. Residue Availability Estimate

**Assumption** (`equations.gms:57-58`): ~33% of available residues for recycling on cropland can be used for 2nd generation bioenergy.

**Limitations**:
- Fixed percentage, does NOT account for:
  - Competing uses (animal feed, bedding, material uses)
  - Soil carbon maintenance requirements (residue retention for soil health)
  - Collection costs and logistical constraints (dispersed biomass, seasonal availability)
  - Regional variability in agricultural practices (some regions already use all residues for feed, others burn)

**Implication**: May overestimate residue availability in regions with intensive livestock systems or underestimate in regions with residue burning.

### 5. Subsidy Feedback Loop Risk

**Warning** (`equations.gms:70-71`): Bioenergy subsidies combined with endogenous technological change (Module 13) can create positive feedback loop:
1. Subsidy → higher bioenergy production
2. Higher production → more land in bioenergy crops
3. More land → higher tau (intensification factor) via Module 13
4. Higher tau → higher yields
5. Higher yields → lower costs
6. Lower costs → even more bioenergy production (loop continues)

**Implication**: Scenarios with high subsidies (`s60_bioenergy_X_price > 0`) and endogenous TC should be carefully examined for unrealistic bioenergy expansion.

**Mitigation**: Use exogenous TC (Module 13 `exo` realization) when testing high bioenergy subsidy scenarios, or impose land constraints.

### 6. No End-Use Disaggregation

**Limitation**: Module 60 does NOT distinguish between bioenergy end uses:
- Liquid biofuels (transportation)
- Bioelectricity (power generation)
- Biogas (heating, cooking)
- Biojet fuel (aviation)
- Biochemicals (plastics, materials)

**Implication**: All bioenergy treated as homogeneous energy commodity (measured in GJ). Model does NOT capture:
- End-use-specific conversion efficiencies (different pathways have different energy losses)
- Infrastructure compatibility (e.g., drop-in fuels vs. requiring new infrastructure)
- Value differences (aviation biofuels command higher prices than bioethanol)
- Policy mandates by sector (e.g., renewable fuel standards for transport only)

### 7. Global vs. Regional Demand Trade-Off

**Limitation**: `c60_biodem_level` switch is binary (0 = fully global, 1 = fully regional) (`input.gms:37`).

**Implication**: Cannot represent:
- Partial trade (e.g., 80% regional, 20% traded)
- Trade constraints (e.g., regional demand with limited import/export quotas)
- Differentiated policies (some regions have local mandates, others rely on imports)

**Current Implementation**: Either model optimizes all regional distribution (global) or all regions self-sufficient (regional).

### 8. Historical Harmonization

**Assumption** (`preloop.gms:26-28, 33-35`, `presolve.gms:14-18`): All scenarios harmonized to "R34M410-SSP2-NPi2025" until `sm_fix_SSP2` (typically 2020-2025).

**Implication**:
- Historical period uses same demand trajectory regardless of scenario selection
- Prevents unrealistic historical divergence between scenarios
- May not match actual historical bioenergy production if SSP2-NPi deviates from reality

### 9. No Spatial Disaggregation Within Regions

**Limitation**: Bioenergy demand specified at MAgPIE regional level (10-15 regions globally).

**Implication**: Does NOT capture:
- Within-region variation in bioenergy policies (e.g., California low-carbon fuel standard vs. rest of USA)
- Subnational mandates or incentives
- Transport costs from production to consumption locations within regions

### 10. No Interannual Variability

**Limitation**: Bioenergy demand trajectories are smooth (no year-to-year fluctuations).

**Implication**: Does NOT represent:
- Policy changes (e.g., sudden mandate increases, subsidy reforms)
- Market shocks (e.g., oil price spikes driving biofuel demand)
- Technological breakthroughs (e.g., sudden cellulosic ethanol commercialization)

**Current Implementation**: Demand follows deterministic scenario trajectories.

---

## Data Sources and Input Files

### 2nd Generation Dedicated Bioenergy Demand

**Primary Data** (`input.gms:63-67`):
```
f60_bioenergy_dem(t,i,scen2nd60)  // mio. GJ per yr
```
**Source**: REMIND-MAgPIE coupled model projections, SSPDB scenarios

**Scenarios**: 90+ scenarios covering SSP storylines, climate policies (NDC, carbon budgets), and model variants

**Usage**: Selected via `c60_2ndgen_biodem` switch, blended with non-selected scenario using population weights (`preloop.gms:30-31`).

**Special Modes**:
- **Coupling** (`input.gms:49-53`): `f60_bioenergy_dem_coupling(t,i)` from external file
- **Emulator** (`input.gms:55-61`): `f60_bioenergy_dem_emulator(t)` global demand, divided by region count

### 2nd Generation Residue Demand

**Data** (`input.gms:72-76`):
```
f60_res_2ndgenBE_dem(t,i,scen2ndres60)  // mio. GJ per yr
```
**Scenarios**: ssp1, ssp2, ssp3, ssp4, ssp5, sdp, off

**Methodology**: Estimated as ~33% of available residues for recycling on cropland (`equations.gms:57-58`).

**Drivers**: Population and GDP (via SSP scenarios) determine residue production and use patterns.

**Usage**: Selected via `c60_res_2ndgenBE_dem` switch (`input.gms:69`).

### 1st Generation Bioenergy Demand

**Data** (`input.gms:82-86`):
```
f60_1stgen_bioenergy_dem(t,i,scen1st60,kall)  // mio. GJ per yr
```
**Products**: oils, ethanol

**Scenarios**: const2020, const2030, phaseout2020

**Methodology**: Based on currently established and planned bioenergy policies (Lotze-Campen et al. 2014) (`equations.gms:24-25`).

**Temporal Extent**: Trajectories until 2050, assumed zero after 2050 (`equations.gms:26-28`).

**Usage**: Selected via `c60_1stgen_biodem` switch (`input.gms:79`).

### Country Selection

**Data** (`input.gms:9-33`):
```
scen_countries60(iso)  // Set of 249 countries
```
**Default**: All countries included

**Usage**: Can be restricted to subset to test country-specific bioenergy policies. Population-weighted aggregation to regional level (`preloop.gms:17`).

---

## Computational Notes

### Variable Scaling

**Bioenergy Utility** (`scaling.gms:8`):
```
vm_bioenergy_utility.scale(i) = 10e4
```
Scale factor of 10^5 improves solver numerics (bioenergy subsidies can be large in absolute terms).

### Conditional Constraints

**Mutually Exclusive Constraints**: Only one of `q60_bioenergy_glo` or `q60_bioenergy_reg` is active at a time, controlled by `c60_biodem_level` switch (`equations.gms:33-47`).

**Implementation**:
- If `c60_biodem_level = 0`: `q60_bioenergy_glo` active (RHS = global demand), `q60_bioenergy_reg` inactive (RHS = 0)
- If `c60_biodem_level = 1`: `q60_bioenergy_reg` active (RHS = regional demand), `q60_bioenergy_glo` inactive (RHS = 0)

**Result**: No redundant constraints (avoids solver inefficiency).

### Historical Harmonization Logic

**Conditional Assignment** (`preloop.gms:26-35`, `presolve.gms:14-26`):
```
if (m_year(t) <= sm_fix_SSP2):
    use SSP2 baseline
else:
    use selected scenario
```

**Purpose**: Ensures all scenarios share common historical period (improves comparability, avoids unrealistic past divergence).

### Minimum Demand Floor

**Conditional Override** (`presolve.gms:56-57`):
```
i60_bioenergy_dem(t,i)$(i60_bioenergy_dem(t,i) < s60_2ndgen_bioenergy_dem_min)
    = s60_2ndgen_bioenergy_dem_min
```

**Purpose**: Prevents numerical issues when bioenergy demand approaches zero (division by zero in price calculations, degeneracy).

**Effect**: Every region has minimum 1 mio. GJ per yr 2nd generation dedicated demand.

---

## Module Flows and Interactions

### Execution Sequence (Typical Timestep)

**1. Preloop** (once before optimization):
- Calculate population-weighted regional shares for scenario selection (`preloop.gms:8-17`)
- Load bioenergy demand data based on scenario selection (`preloop.gms:19-36`)

**2. Presolve** (before each solve):
- Fix non-bioenergy products to zero demand (`presolve.gms:8`)
- Release bioenergy crops (betr, begr) and residues (kres) (`presolve.gms:9-12`)
- Load 1st generation, 2nd generation residue demands based on scenarios (`presolve.gms:14-27`)
- Calculate subsidies based on price implementation mode (`presolve.gms:29-50`)
- Enforce 1st generation subsidy floor (`presolve.gms:52-54`)
- Enforce minimum demand floor (`presolve.gms:56-57`)

**3. Equations** (solved simultaneously):
- `q60_bioenergy`: Total demand (mass × energy content) ≥ 1st gen + 2nd gen dedicated + 2nd gen residues (`equations.gms:16-21`)
- `q60_bioenergy_glo` OR `q60_bioenergy_reg`: Global or regional 2nd gen dedicated constraint (`equations.gms:43-47`)
- `q60_res_2ndgenBE`: Regional residue demand constraint (`equations.gms:61-64`)
- `q60_bioenergy_incentive`: Calculate utility from subsidies (`equations.gms:73-75`)

**4. Postsolve** (after solve):
- Record output variables (marginals, levels, bounds) (`postsolve.gms:10-47`)

### Critical Module Dependencies

**Upstream Dependencies** (Module 60 requires):
- **Module 09 (Drivers)**: Population (`im_pop_iso`) for regional share calculation
- **Data**: Gross energy content (`fm_attributes("ge",kall)`) for mass-to-energy conversion
- **Data**: Bioenergy demand scenarios (f60_bioenergy_dem, f60_res_2ndgenBE_dem, f60_1stgen_bioenergy_dem)

**Downstream Dependencies** (Other modules require Module 60):
- **Module 16 (Demand)**: Bioenergy demand (`vm_dem_bioen`) aggregated with food/feed/material/seed demands
- **Module 11 (Costs)**: Bioenergy utility (`vm_bioenergy_utility`) as negative cost in objective function

### Circular Dependencies

**None**: Module 60 has no circular dependencies. It provides demand to Module 16, but does NOT receive any variables back from Module 16.

**Data Flow**:
- Module 60 (exogenous scenarios) → `vm_dem_bioen` → Module 16 (aggregate demand) → Module 21 (trade) → Module 17 (production) → Module 30 (croparea) → Land allocation
- Feedback: Land allocation affects yields, costs → influences optimal bioenergy production → but does NOT affect `vm_dem_bioen` (exogenous)

---

## Interpretation and Use Cases

### Bioenergy Scenario Analysis

**Query**: "How much land is needed for bioenergy in SSP2-PkBudg650 vs. SSP1-PkBudg650?"

**Approach**:
1. Run scenario with `c60_2ndgen_biodem = "R34M410-SSP2-PkBudg650"`
2. Run scenario with `c60_2ndgen_biodem = "R34M410-SSP1-PkBudg650"`
3. Compare `vm_dem_bioen(i,kbe60)` (bioenergy crop demand) across scenarios
4. Trace to Module 30 (Croparea): `vm_area(j,kbe60)` (bioenergy cropland)

**Expected Pattern**:
- Higher climate ambition (PkBudg650 = carbon budget 650 GtCO2) → more bioenergy with CCS for negative emissions
- SSP1 (sustainability) → lower overall energy demand → less bioenergy than SSP2 (middle of the road)
- Land use: Higher bioenergy demand → more land allocated to betr/begr → potential competition with food production

### 1st vs. 2nd Generation Trade-Off

**Query**: "What happens to 1st generation bioenergy demand under 'phaseout2020' scenario?"

**Approach**:
1. Configure: `c60_1stgen_biodem = "phaseout2020"`
2. Extract `i60_1stgen_bioenergy_dem(t,i,kall)` over time
3. Compare with `const2020` baseline

**Expected Pattern**:
- **const2020**: 1st generation demand (oils, ethanol) constant until 2050, then zero
- **phaseout2020**: 1st generation demand decreases from 2020, reaches zero before 2050
- Land-use implication: Early phase-out → less competition between food and bioenergy → more land for food production

### Global vs. Regional Demand Implementation

**Query**: "How does regional distribution of bioenergy production change between global and regional demand modes?"

**Approach**:
1. Run with `c60_biodem_level = 0` (global): `vm_dem_bioen(i,kbe60)` endogenously distributed
2. Run with `c60_biodem_level = 1` (regional): `vm_dem_bioen(i,kbe60)` meets regional targets
3. Compare regional production patterns

**Expected Pattern**:
- **Global mode**: Bioenergy concentrated in regions with:
  - High yields (tropical regions)
  - Low land costs (extensive agricultural systems)
  - Large land availability (Brazil, sub-Saharan Africa)
- **Regional mode**: Each region produces locally, even if costly:
  - Some regions expand bioenergy despite low yields (e.g., arid regions)
  - Less total land needed (no transport losses, but less efficiency)

### Subsidy Impact Assessment

**Query**: "How does bioenergy production respond to a 50 USD17MER/GJ subsidy for 2nd generation?"

**Approach**:
1. Baseline: `s60_bioenergy_2nd_price = 0` (no subsidy beyond minimum demand)
2. Scenario: `s60_bioenergy_2nd_price = 50`, `c60_price_implementation = "const"`
3. Compare `vm_dem_bioen(i,kbe60)` between baseline and scenario

**Expected Pattern**:
- Baseline: Bioenergy production = minimum demand from `i60_bioenergy_dem`
- With subsidy: Bioenergy production > minimum demand (expansion driven by negative cost incentive)
- **Warning**: Check Module 13 (TC) response - high subsidy may trigger intensification feedback loop

### Residue Demand Scenario Comparison

**Query**: "How does residue demand for bioenergy vary across SSP scenarios?"

**Approach**:
1. Extract `i60_res_2ndgenBE_dem(t,i)` for SSP1, SSP2, SSP3, SSP4, SSP5
2. Compare temporal trajectories and regional patterns

**Expected Pattern** (based on ~33% of recyclable residues):
- **SSP1/SDP**: Lower population, sustainable consumption → lower crop production → fewer residues available → lower residue demand for bioenergy
- **SSP2**: Moderate population, moderate consumption → moderate residue demand
- **SSP3**: High population, low income → high crop production for food → high residue availability → potentially high bioenergy from residues (if policy enables)
- **SSP5**: High income, high meat consumption → high feed crop production → high residues → high potential for bioenergy

### Country-Specific Policy Analysis

**Query**: "What is the effect of EU-only high bioenergy demand on global land use?"

**Approach**:
1. Restrict `scen_countries60` to EU countries only
2. Set `c60_2ndgen_biodem` to high demand scenario (e.g., "R32M46-SSP1-PkBudg650")
3. Set `c60_2ndgen_biodem_noselect` to low demand scenario (e.g., "R34M410-SSP2-NPi2025")
4. Compare land use in EU vs. rest of world

**Expected Pattern**:
- EU region: High bioenergy demand (population-weighted), significant land conversion to bioenergy crops
- Non-EU regions: Low bioenergy demand, less land pressure from bioenergy
- **Leakage effect**: If EU imports bioenergy (depends on Module 21 trade rules), production may shift to other regions despite low local demand

---

## Related Modules

**Module 16 (Demand)**: Aggregates bioenergy demand with food/feed/material/seed; provides total commodity demand to trade
**Module 11 (Costs)**: Receives bioenergy utility (negative cost) as incentive in objective function
**Module 09 (Drivers)**: Provides population for regional share calculation in scenario selection
**Module 21 (Trade)**: Bioenergy crops (betr, begr) may be traded if comparative advantage exists
**Module 13 (Technological Change)**: Bioenergy subsidies can interact with endogenous intensification (feedback loop risk)
**Module 18 (Residues)**: Calculates residue supply; Module 60 specifies residue demand for bioenergy

---

## Summary Statistics

**Module Complexity**:
- 5 equations
- 2 interface variables (outputs): `vm_dem_bioen`, `vm_bioenergy_utility`
- 1 interface variable (input): `fm_attributes("ge",kall)`
- 90+ bioenergy demand scenarios (2nd generation dedicated)
- 7 SSP scenarios (residues)
- 3 scenarios (1st generation)
- 3 price implementation modes (linear, exponential, constant)
- ~250 lines of code

**Key Parameters**:
- Bioenergy demand: 90+ scenarios × 10-15 regions × time horizon (thousands of values)
- Subsidies: 2 types (1st, 2nd generation) × 3 implementation modes
- Region selection: 249 countries, population-weighted aggregation

**Computational Load**:
- Low equation count (5), straightforward constraints
- Conditional logic (global vs. regional, price implementation) adds branching
- No iterative calculations (all exogenous data)

---

## File Reference

**Core Files**:
- `modules/60_bioenergy/module.gms` - Module documentation
- `modules/60_bioenergy/1st2ndgen_priced_feb24/realization.gms` - Realization structure
- `modules/60_bioenergy/1st2ndgen_priced_feb24/sets.gms` - Bioenergy types, scenarios
- `modules/60_bioenergy/1st2ndgen_priced_feb24/declarations.gms` - Variables, equations, parameters
- `modules/60_bioenergy/1st2ndgen_priced_feb24/input.gms` - Configuration switches, input data
- `modules/60_bioenergy/1st2ndgen_priced_feb24/equations.gms` - 5 equation definitions
- `modules/60_bioenergy/1st2ndgen_priced_feb24/preloop.gms` - Regional share calculation, demand loading
- `modules/60_bioenergy/1st2ndgen_priced_feb24/presolve.gms` - Variable bounds, subsidy calculation
- `modules/60_bioenergy/1st2ndgen_priced_feb24/postsolve.gms` - Output recording
- `modules/60_bioenergy/1st2ndgen_priced_feb24/scaling.gms` - Variable scaling

**Input Data Directory**:
- `modules/60_bioenergy/input/` - All input data files (.cs3, .csv)
  - `f60_bioenergy_dem.cs3` - 2nd generation dedicated demand (90+ scenarios)
  - `f60_2ndgenBE_residue_dem.cs3` - 2nd generation residue demand (7 scenarios)
  - `f60_1stgen_bioenergy_dem.cs3` - 1st generation demand (3 scenarios)
  - `reg.2ndgen_bioenergy_demand.csv` - Coupling mode (if used)
  - `glo.2ndgen_bioenergy_demand.csv` - Emulator mode (if used)

---

**Verification**: All 5 equations verified against source code. All formulas, dimensions, and parameter names confirmed exact. All interface variables cross-referenced. Zero errors detected.

**MAgPIE Version**: 4.x series
**Lines Documented**: ~250 (1st2ndgen_priced_feb24 realization)
---

## Participates In

### Conservation Laws

**Not in conservation laws** (bioenergy demand driver)

### Dependency Chains

**Centrality**: Medium (demand provider)
**Details**: `core_docs/Module_Dependencies.md`

### Circular Dependencies

None

### Modification Safety

**Risk Level**: 🟡 **MEDIUM RISK**
**Testing**: Verify bioenergy demand reasonable

---

**Module 60 Status**: ✅ COMPLETE

---

**Last Verified**: 2025-10-13
**Verified Against**: `../modules/60_*/1st2ndgen_priced_feb24/*.gms`
**Verification Method**: Equations cross-referenced with source code
**Changes Since Last Verification**: None (stable)
