# Carbon Balance Tracking System in MAgPIE

**Status**: ✅ Complete
**Created**: 2025-10-22
**Modules Covered**: 52, 53, 59 (57 for mitigation costs)
**System Type**: Stock-Flow tracking (NOT a strict conservation law)

---

## 1. Overview

The **Carbon Balance System** in MAgPIE is a comprehensive **stock and flow tracking mechanism** that calculates carbon stocks in vegetation, litter, and soil across all land types, and derives CO₂ emissions from changes in these stocks. Unlike land balance (strict equality) or water balance (inequality constraint), carbon balance is **not enforced as a conservation law** - carbon can be emitted to the atmosphere or sequestered from it.

**Key Modules**:
- **Module 52 (Carbon)**: Provides carbon densities, calculates CO₂ emissions from stock changes
- **Module 59 (SOM)**: Tracks dynamic soil organic matter with IPCC 2019 methodology
- **Module 53 (Methane)**: Calculates non-CO₂ emissions (CH₄ from agriculture)

**Mathematical Concept**:
```
∀ j ∈ Cells, ∀ t ∈ Time:
  CO₂ Emissions(t) = [Carbon Stock(t-1) - Carbon Stock(t)] / Timestep Length
```

**NOT a Conservation Law Because**:
- Carbon leaves the system as emissions (CO₂ to atmosphere)
- Carbon enters via photosynthesis (captured in LPJmL carbon densities)
- Total terrestrial carbon changes over time (not conserved)

---

## 2. Carbon Pools (3 Types)

**Verified**: `core/sets.gms:324-325`

MAgPIE tracks carbon in 3 pools for each land type:

### 2.1 Vegetation Carbon (vegc)

| Pool | Code | Description | Typical Timescale |
|------|------|-------------|-------------------|
| **Vegetation** | `vegc` | Above-ground and below-ground live biomass | Years to centuries |

**Contains**:
- Trees (forests, plantations, tree cover on cropland)
- Shrubs and grasses (pastures, natural vegetation)
- Crops (annual biomass, harvested each year)

**Dynamics**:
- **Forests**: Grows over decades following Chapman-Richards equation (Module 52)
- **Crops**: Annual cycle (grows, harvested, residues left)
- **Pasture**: Relatively stable (grazing removes biomass but regrows)

**Sources** (Module 52):
- LPJmL simulations (`lpj_carbon_stocks.cs3`)
- Age-class-specific for forests/plantations (Chapman-Richards growth)

---

### 2.2 Litter Carbon (litc)

| Pool | Code | Description | Typical Timescale |
|------|------|-------------|-------------------|
| **Litter** | `litc` | Dead plant material, not yet decomposed to soil | Years to decades |

**Contains**:
- Crop residues (straw, stover)
- Leaf litter (from forests)
- Dead roots and branches

**Dynamics**:
- **Accumulation**: From plant death, harvest residues, forest turnover
- **Decomposition**: Gradual breakdown to soil organic matter (20-year IPCC timescale)

**Sources** (Module 52):
- LPJmL simulations for equilibrium values
- Linear convergence over 20 years (IPCC assumption, `start.gms:19,30,37`)

---

### 2.3 Soil Carbon (soilc)

| Pool | Code | Description | Typical Timescale |
|------|------|-------------|-------------------|
| **Soil Organic Matter** | `soilc` | Decomposed organic matter in topsoil and subsoil | Decades to centuries |

**Two Components**:

**Topsoil** (Module 59):
- Dynamic, responds to land use and management
- IPCC 2019 methodology with stock change factors
- 15% annual convergence to equilibrium

**Subsoil** (Module 52):
- Static (fixed from LPJmL)
- Not affected by land use (assumption)

**Key Difference**:
- **Module 52 provides** total soil carbon densities (topsoil + subsoil)
- **Module 59 tracks** dynamic topsoil carbon pools separately
- Interface: `vm_carbon_stock(j,land,c_pools)` includes both

---

## 3. Carbon Stocks by Land Type

**Verified**: Module 52 (`fm_carbon_density(t,j,land,c_pools)`)

Carbon densities (tC per ha) provided for all 7 land types:

### 3.1 Cropland

| Pool | Source | Dynamics | Module |
|------|--------|----------|--------|
| vegc | LPJmL annual crops | Low (harvested each year) | 52 |
| litc | LPJmL | Crop residues | 52 |
| soilc | IPCC 2019 | Dynamic (converges to equilibrium) | 59 |

**Key Features**:
- Lowest vegetation carbon (annual crops)
- Soil carbon responds to tillage, inputs, irrigation (Module 59)
- Crop-specific equilibrium based on residue production

**Topsoil Equilibrium** (Module 59, `equations.gms:20-27`):
```
SOM_equilibrium = Σ(crops) Area × C_ratio × Natural_density
```

**C_ratio Factors** (Module 59):
- Land use: Cropland vs set-aside
- Tillage: Full, reduced, no-till (default: full)
- Input level: Low, medium, high without manure (default: medium)
- Irrigation: Increases carbon (optional, controlled by `c59_irrigation_scenario`)

---

### 3.2 Pasture

| Pool | Source | Dynamics | Module |
|------|--------|----------|--------|
| vegc | LPJmL grassland | Moderate (grazed but permanent) | 52 |
| litc | LPJmL | Moderate | 52 |
| soilc | LPJmL + Module 59 | **Assumed constant** | 59 |

**Key Assumption** (Module 59, `realization.gms:21-24`):
- Pastures assumed to maintain **natural carbon density**
- Does NOT model degradation from overgrazing
- Does NOT model improvement from rotational grazing

**Limitation**: Pasture soil carbon changes only when converting from/to other land types, not from management intensity

---

### 3.3 Forestry (Plantations)

| Pool | Source | Dynamics | Module |
|------|--------|----------|--------|
| vegc | Chapman-Richards growth | Grows over rotation | 52 |
| litc | Linear growth (20 years) | Converges to forest equilibrium | 52 |
| soilc | LPJmL + Module 59 | Converges to natural density | 59 |

**Vegetation Growth** (Module 52, `start.gms:17`):
```
vegc(ac) = S + (A - S) * (1 - exp(-k * ac*5))^m
```

**Parameters**:
- S = 0 (start with bare land)
- A = Secondary forest vegc (mature target)
- k, m = Climate-specific growth parameters (from `f52_growth_par.csv`)
- ac = Age class (5-year intervals)

**Growth Rates** (illustrative):
- **Tropical plantations** (high k): Approach equilibrium in ~30-50 years
- **Temperate plantations** (low k): Approach equilibrium in ~50-80 years

*Note: Actual values depend on cell-specific climate class and species.*

---

### 3.4 Primary Forest

| Pool | Source | Dynamics | Module |
|------|--------|----------|--------|
| vegc | LPJmL mature forest | **Static** (assumed mature) | 52 |
| litc | LPJmL | Static | 52 |
| soilc | LPJmL | Static | 52, 59 |

**Key Assumption**:
- Primary forests at equilibrium carbon density
- No age-class tracking (assumed mature "acx")
- Carbon density does NOT change over time (climate change affects future forests, not current primary)

---

### 3.5 Secondary Forest

| Pool | Source | Dynamics | Module |
|------|--------|----------|--------|
| vegc | Chapman-Richards growth | Grows with age | 52 |
| litc | Linear growth (20 years) | Converges to forest equilibrium | 52 |
| soilc | LPJmL + Module 59 | Converges to natural density | 59 |

**Vegetation Growth** (Module 52, `start.gms:28`):
```
vegc(ac) = 0 + (A - 0) * (1 - exp(-k * ac*5))^m
```

**Sources**:
- Abandoned agricultural land (regrowth)
- Harvested primary forest (transitions to youngest age class)
- Disturbed areas (fire, shifting agriculture)

**Age-Class Dynamics** (Module 35):
- Forests progress through age classes: ac0 → ac5 → ac10 → ... → acx
- Carbon accumulates according to Chapman-Richards curve
- Mature forests (acx) at equilibrium density

---

### 3.6 Other Land

| Pool | Source | Dynamics | Module |
|------|--------|----------|--------|
| vegc | Chapman-Richards growth | Grows if young secondary forest | 52 |
| litc | Linear growth | Converges to equilibrium | 52 |
| soilc | LPJmL | Static or converging | 59 |

**Two Subtypes** (Module 35):
- `othernat`: Natural grassland, savanna, shrubland (stable)
- `youngsecdf`: Young secondary forest with vegc < 20 tC/ha (recovering)

**Maturation Threshold**:
- When vegc exceeds 20 tC/ha → graduates to secondary forest
- Tracked by Module 35 age-class dynamics

---

### 3.7 Urban

| Pool | Source | Dynamics | Module |
|------|--------|----------|--------|
| vegc | Fixed to zero | None | 52 |
| litc | Fixed to zero | None | 52 |
| soilc | Set to "other" land value | None | 52, 59 |

**Key Limitations**:
- No carbon density data for urban vegetation (street trees, parks)
- Urban carbon fixed at zero vegc/litc
- Soil carbon assumed equal to other land (placeholder)

---

## 4. CO₂ Emission Calculation

### 4.1 Core Equation

**Source**: Module 52, `equations.gms:16-19`

```gams
q52_emis_co2_actual(i2) ..
  vm_emissions_reg(i2,emis_oneoff,"co2_c") =e=
    sum((cell(i2,j2),emis_land(emis_oneoff,land,c_pools)),
      (pcm_carbon_stock(j2,land,c_pools,"actual")
       - vm_carbon_stock(j2,land,c_pools,"actual"))
      / m_timestep_length
    );
```

**Translation**:
```
CO₂ Emissions = (Previous Carbon Stock - Current Carbon Stock) / Timestep Length
```

**Components**:
- **Previous stock**: `pcm_carbon_stock` - from end of previous timestep
- **Current stock**: `vm_carbon_stock` - optimized for current timestep
- **Timestep length**: Years between timesteps (e.g., 5 or 10 years)

---

### 4.2 Emission Sign Convention

| Scenario | Stock Change | Sign | Interpretation |
|----------|--------------|------|----------------|
| **Deforestation** | Previous > Current | **Positive** | Emission to atmosphere |
| **Afforestation** | Previous < Current | **Negative** | Sequestration from atmosphere |
| **Stable land use** | Previous = Current | **Zero** | No net emissions |

**Example** (illustrative):
- Previous forest carbon: 150 tC/ha × 100 Mha = 15,000 Tg C
- Current cropland carbon: 50 tC/ha × 100 Mha = 5,000 Tg C
- Stock change: 15,000 - 5,000 = 10,000 Tg C lost
- Timestep: 5 years
- **Annual emission**: 10,000 / 5 = **2,000 Tg C/yr (emission to atmosphere)**

*Note: Made-up numbers for illustration.*

---

### 4.3 Emission Sources (emis_oneoff)

**Verified**: `core/sets.gms:314-318`

Emissions tracked by land type and carbon pool (21 sources total = 7 land types × 3 pools):

**Land Types**:
- crop, past, forestry, primforest, secdforest, urban, other

**Pools**:
- vegc, litc, soilc

**Examples**:
- `crop_vegc`: Vegetation carbon from cropland
- `primforest_soilc`: Soil carbon from primary forest
- `forestry_litc`: Litter carbon from plantations

**Mapping** (`emis_land` set, `core/sets.gms:332-335`):
- Links emission sources to land types and carbon pools
- Example: `crop_vegc . (crop) . (vegc)`

---

### 4.4 Units and Conversions

**Carbon Stocks**:
- Input: mio. tC (from `vm_carbon_stock`)
- Unit: Million metric tons of carbon

**Emissions**:
- Output: Tg C per year (from `vm_emissions_reg`)
- Unit: Teragram carbon per year (1 Tg = 1 million metric tons)

**Conversion**:
- 1 mio. tC = 1 Tg C ✓ (units consistent)

**CO₂ Equivalent** (not calculated by Module 52, done in post-processing):
```
CO₂ emissions (Tg CO₂) = C emissions (Tg C) × (44/12)
                        = C emissions × 3.67
```

---

## 5. Soil Organic Matter Dynamics (Module 59)

### 5.1 Dynamic Convergence to Equilibrium

**Core Concept**: Topsoil carbon gradually moves toward a new equilibrium when land use or management changes.

**Equation** (Module 59, `equations.gms:46-52`):
```gams
v59_som_pool(j,land) =e=
  lossrate * v59_som_target(j,land)
  + (1 - lossrate) * Σ(land_from) carbon_density(land_from) * lu_transitions(land_from, land)
```

**Components**:

1. **lossrate fraction**: Proportion converging to new equilibrium this timestep
   ```
   lossrate(t) = 1 - 0.85^(years in timestep)
   ```

2. **som_target**: Equilibrium carbon under current land use/management

3. **legacy fraction**: Remaining carbon from previous land use (via transitions)

---

### 5.2 Convergence Rates

**Annual Loss Rate** (Module 59, `preloop.gms:45`):
- 15% per year toward equilibrium
- 85% remains from previous state

**Multi-Year Convergence**:

| Timestep Length | Loss Rate | Remaining Legacy |
|-----------------|-----------|------------------|
| 1 year | 15% | 85% |
| 5 years | 44% | 56% |
| 10 years | 80% | 20% |
| 20 years | 96% | 4% |

**Calculation**:
```
lossrate = 1 - 0.85^years
```

**Interpretation**:
- After 5 years: 44% toward new equilibrium, 56% legacy
- After 10 years: 80% toward new equilibrium, 20% legacy
- After 20 years: Essentially at equilibrium (96%)

---

### 5.3 Cropland Equilibrium Factors

**IPCC 2019 Stock Change Factors** (Module 59):

**Base Equation**:
```
C_equilibrium = C_natural × FLU × FMG × FI
```

**Factors**:
- **FLU** (Land Use): Cropland / Set-aside / Perennial (default: annual cropland)
- **FMG** (Management): Full till / Reduced till / No-till (default: full tillage)
- **FI** (Input): Low / Medium / High / High with manure (default: medium, no manure)

**Additional**:
- **Irrigation effect**: Optional increase in equilibrium (controlled by `c59_irrigation_scenario`)
- **Crop-specific**: Different crops produce different residue amounts

**Example Stock Change Factors** (typical values from IPCC):
- Cropland + Full till + Medium input: F = 0.69 (31% carbon loss vs natural)
- Cropland + No-till + High input + manure: F = 1.17 (17% carbon gain vs natural!)

*Note: Actual factors are cell-specific (climate-dependent) in Module 59.*

---

## 6. Chapman-Richards Growth for Forests

### 6.1 Vegetation Carbon Growth Equation

**Formula** (Module 52, `core/macros.gms:18`):
```
vegc(ac) = S + (A - S) * (1 - exp(-k * ac*5))^m
```

**Parameters**:
- **S**: Start carbon density (tC/ha) = 0 for new forests
- **A**: Asymptotic (mature) carbon density (tC/ha) from LPJmL
- **k**: Growth rate parameter (climate-specific)
- **m**: Shape parameter (climate-specific)
- **ac**: Age class (integer, converted to years via `ac*5`)

---

### 6.2 Climate-Specific Growth Parameters

**Source**: `f52_growth_par.csv` (Module 52, `input.gms:37-43`)

**Climate Classes** (Köppen-Geiger classification):
- **Tropical**: High k (fast growth), typical values k ≈ 0.05-0.08
- **Temperate**: Medium k, typical values k ≈ 0.03-0.05
- **Boreal**: Low k (slow growth), typical values k ≈ 0.02-0.03

**Effective Parameters** (Module 52, `start.gms:17`):
```
k_eff = Σ(climate_class) climate_share × k(climate_class)
m_eff = Σ(climate_class) climate_share × m(climate_class)
```

**Climate shares** from Module 45 (Climate): `pm_climate_class(j,clcl)`

---

### 6.3 Growth Trajectories

**Illustrative Example** (tropical plantation):
- A = 100 tC/ha (mature forest carbon)
- k = 0.06, m = 2.0
- Timestep = 5 years

| Age (years) | Age Class | vegc (tC/ha) | % of Mature |
|-------------|-----------|--------------|-------------|
| 0 | ac0 | 0 | 0% |
| 5 | ac1 | 14 | 14% |
| 10 | ac2 | 26 | 26% |
| 20 | ac4 | 44 | 44% |
| 30 | ac6 | 58 | 58% |
| 50 | ac10 | 75 | 75% |
| 80 | ac16 | 88 | 88% |
| 100 | ac20 | 93 | 93% |
| 150+ | acx | ~100 | ~100% |

*Note: Values are illustrative based on typical tropical forest parameters. Actual growth depends on cell-specific climate and soil conditions.*

---

## 7. Module Interactions for Carbon Balance

### 7.1 Module 52 (Carbon) - Central Data Provider

**Role**: Provides carbon densities and calculates CO₂ emissions

**Provides**:
- `fm_carbon_density(t,j,land,c_pools)`: Base carbon densities (tC/ha) from LPJmL
- `pm_carbon_density_plantation_ac(t,j,ac,c_pools)`: Age-class densities for plantations
- `pm_carbon_density_secdforest_ac(t,j,ac,c_pools)`: Age-class densities for secondary forests
- `pm_carbon_density_other_ac(t,j,ac,c_pools)`: Age-class densities for other land

**Receives**:
- `vm_carbon_stock(j,land,c_pools,"actual")`: Current carbon stocks from all land modules

**Key Equation**:
```gams
vm_emissions_reg(i,emis_oneoff,"co2_c") =
  (pcm_carbon_stock - vm_carbon_stock) / timestep_length
```

**Climate Scenarios** (Module 52, `input.gms:22-23`):
- `cc`: Time-varying carbon densities from LPJmL climate projections
- `nocc`: Fixed at 1995 levels
- `nocc_hist`: Historical until sm_fix_cc, then frozen

---

### 7.2 Module 59 (SOM) - Dynamic Soil Carbon

**Role**: Tracks topsoil carbon with IPCC 2019 methodology

**Provides**:
- `v59_som_pool(j,land)`: Actual topsoil carbon pools (mio. tC)
- `vm_nr_som(j)`: Nitrogen release from SOM loss (Mt N/yr) → to Module 51
- `vm_cost_scm(j)`: Soil carbon management costs → to Module 11

**Receives**:
- `vm_area(j,kcr,w)`: Crop areas from Module 30 → for equilibrium calculation
- `vm_fallow(j)`: Fallow land from Module 29 → for equilibrium
- `vm_treecover(j)`: Tree cover from Module 29 → for equilibrium
- `vm_land(j,land)`: Non-cropland areas from Module 10
- `vm_lu_transitions(j,land_from,land_to)`: Transitions from Module 10

**Key Equations**:
```gams
v59_som_target(j,"crop") = Σ(crops) Area × C_ratio × Natural_density
v59_som_pool(j,land) = lossrate × target + (1-lossrate) × legacy
```

**Interface with Module 52**:
- Module 59 calculates topsoil carbon dynamics
- Module 52 provides total soil carbon (topsoil + subsoil) to `vm_carbon_stock`
- Topsoil from Module 59 + Subsoil from Module 52 = Total soil carbon

---

### 7.3 Module 53 (Methane) - Non-CO₂ Emissions

**Role**: Calculates CH₄ emissions from agriculture

**Four Sources**:
1. **Enteric fermentation**: Ruminant digestion (largest source)
2. **Animal waste management**: Manure decomposition
3. **Rice cultivation**: Flooded paddy anaerobic decomposition
4. **Residue burning**: Incomplete combustion of crop residues

**Provides**:
- `vm_emissions_reg(i,emis_source,"ch4")`: Regional CH₄ emissions → to Module 56

**Receives**:
- `vm_feed_intake(i,kli,kfo)`: Livestock feed from Module 70 → for enteric fermentation
- `vm_area(j,kcr,w)`: Rice area from Module 30 → for rice emissions
- `im_maccs_mitigation(t,i,emis_source,"ch4")`: Mitigation fractions from Module 57

**Not Part of Carbon Balance**:
- CH₄ tracked separately from CO₂
- CH₄ emissions do NOT appear in `vm_carbon_stock` changes
- Both sent to Module 56 (GHG Policy) for carbon pricing

---

### 7.4 Module 57 (MACCs) - Mitigation Costs

**Role**: Calculates costs of technical GHG mitigation

**Provides**:
- `im_maccs_mitigation(t,i,emis_source,pollutant)`: Mitigation fractions (0 to ~0.3)
- `vm_maccs_costs(i,factors)`: Labor and capital costs of mitigation → to Module 11

**Applies to**:
- CH₄ from enteric fermentation, AWMS, rice, residue burning (Module 53)
- N₂O from fertilizer, manure, rice (Module 51)

**Does NOT affect**:
- CO₂ emissions from land-use change (Module 52) - no technical mitigation
- Biological CO₂ sequestration (driven by land use decisions, not technical fixes)

---

### 7.5 Modules 30, 31, 32, 35 - Land Use Drives Carbon

**Module 30 (Croparea)**:
- Determines crop areas → affects cropland carbon stocks
- Irrigated vs rainfed → affects soil carbon equilibrium (Module 59)

**Module 31 (Pasture)**:
- Determines pasture area → affects pasture carbon stocks
- Grazing intensity does NOT affect carbon (limitation in Module 59)

**Module 32 (Forestry)**:
- Determines plantation age distribution → affects vegetation carbon accumulation
- Harvest removes biomass → carbon loss (but regrows in next rotation)

**Module 35 (Natural Vegetation)**:
- Determines forest age distributions → affects secondary forest carbon
- Disturbances (fire, shifting agriculture) → reset age classes → carbon loss
- Abandoned land recovery → carbon sequestration

**All Provide**:
- `vm_carbon_stock(j,land,c_pools,"actual")`: Current carbon stocks → to Module 52

---

## 8. Carbon Balance in Practice

### 8.1 Deforestation Scenario

**Land Use Change**:
- Primary forest → Cropland (100 Mha converted)

**Carbon Stock Changes** (illustrative):

| Pool | Primary Forest (tC/ha) | Cropland (tC/ha) | Loss (tC/ha) |
|------|------------------------|------------------|--------------|
| vegc | 150 | 10 | **-140** |
| litc | 20 | 5 | **-15** |
| soilc | 80 | 50 (equilibrium after 20 yrs) | **-30** |
| **Total** | **250** | **65** | **-185** |

*Note: Soil carbon loss gradual over 20 years (Module 59 dynamics)*

**Emissions**:
- Immediate (vegc + litc): (140 + 15) tC/ha × 100 Mha × (44/12) = **56,833 Tg CO₂**
- Gradual (soilc over 20 years): 30 tC/ha × 100 Mha × (44/12) / 20 years = **458 Tg CO₂/year**

*Note: Made-up numbers for illustration. Actual values cell-specific from LPJmL.*

---

### 8.2 Afforestation Scenario

**Land Use Change**:
- Cropland → Forestry plantation (50 Mha planted)

**Carbon Stock Trajectory** (illustrative):

**Year 0 (Cropland)**:
- vegc: 10 tC/ha
- litc: 5 tC/ha
- soilc: 50 tC/ha
- **Total: 65 tC/ha**

**Year 20 (Young Plantation)**:
- vegc: 44 tC/ha (44% of mature, from Chapman-Richards)
- litc: 15 tC/ha (converging to forest)
- soilc: 70 tC/ha (80% toward natural, from Module 59)
- **Total: 129 tC/ha**

**Year 50 (Mature Plantation)**:
- vegc: 75 tC/ha (75% of mature)
- litc: 20 tC/ha (at equilibrium)
- soilc: 78 tC/ha (96% toward natural)
- **Total: 173 tC/ha**

**Sequestration**:
- 20-year: (129 - 65) = 64 tC/ha × 50 Mha = 3,200 Tg C
- 50-year: (173 - 65) = 108 tC/ha × 50 Mha = 5,400 Tg C

*Note: Values illustrative. Actual growth depends on climate, species, management.*

---

### 8.3 Climate Change Impact on Carbon Stocks

**Mechanism**:
1. LPJmL simulates vegetation carbon density under future climate
2. Module 52 updates `fm_carbon_density(t,j,land,c_pools)` over time
3. Carbon stocks change even without land-use change

**Typical Patterns**:
- **Tropical forests**: May increase carbon (CO₂ fertilization) or decrease (drought stress)
- **Boreal forests**: Generally increase carbon (longer growing season, warmer)
- **Croplands**: Variable (water stress vs CO₂ fertilization trade-off)

**Example** (hypothetical cell, tropical forest):
- 2020 carbon density: 150 tC/ha
- 2050 carbon density: 165 tC/ha (+10% from CO₂ fertilization)
- If forest area constant: Net sequestration of 15 tC/ha over 30 years

*Note: This is a simplified example. Actual LPJmL projections include complex climate-vegetation feedbacks.*

**Configuration** (Module 52, `input.gms:22-23`):
- `c52_carbon_scenario = "cc"`: Use time-varying LPJmL projections
- `c52_carbon_scenario = "nocc"`: Fix carbon densities at 1995 (no climate effect)

---

### 8.4 Soil Carbon Management Scenario

**Intervention**: Implement high-input practices on 50% of cropland

**Configuration** (Module 59):
- `s59_scm_target = 0.5` (50% of cropland under SCM)
- `s59_cost_scm_recur = 65 USD17/ha` (annual cost)

**Effect on Equilibrium** (illustrative):
- Base equilibrium: 50 tC/ha (cropland, medium input)
- SCM equilibrium: 59 tC/ha (high input factor = 1.17)
- **Gain: +9 tC/ha on 50% of cropland**

**Convergence Timeline** (Module 59):
- Year 5: 44% toward new equilibrium = +4 tC/ha
- Year 10: 80% toward new equilibrium = +7.2 tC/ha
- Year 20: 96% toward new equilibrium = +8.6 tC/ha

**Costs**:
- 50% of cropland area × 65 USD17/ha/year
- If global cropland = 1,500 Mha → 750 Mha under SCM
- **Annual cost: 48,750 million USD17/year**

**Carbon Benefit**:
- 750 Mha × 9 tC/ha = 6,750 Tg C sequestered (after 20 years)
- **Cost per tC: 48,750 / (6,750/20) = 144 USD17/tC** (annualized)

*Note: Illustrative calculation with made-up cropland area.*

---

## 9. Carbon Balance Verification

### 9.1 Stock-Change Consistency Check

**For every land type and timestep**:
```r
library(magpie4)

# Read carbon stocks
carbon_stock_prev <- readGDX(gdx, "pcm_carbon_stock", field="l")
carbon_stock_curr <- readGDX(gdx, "ov_carbon_stock", select=list(type="level"), field="l")

# Read emissions
emissions_co2 <- readGDX(gdx, "ov_emissions_reg", select=list(type="level"))
emissions_co2 <- emissions_co2[,,"co2_c",]

# Read timestep length
timestep <- readGDX(gdx, "pm_timestep_length")  # or calculate from years

# Check consistency
stock_change <- (carbon_stock_prev - carbon_stock_curr) / timestep
emissions_calculated <- dimSums(stock_change, dim=c("cell","land","c_pools"))

# Should match
stopifnot(all.equal(emissions_co2, emissions_calculated, tolerance=0.01))
```

**Expected**: Emissions from stock change equation match reported emissions

---

### 9.2 SOM Convergence Check

**Verify Module 59 convergence**:
```r
# Read SOM pools and targets
som_pool <- readGDX(gdx, "ov59_som_pool", select=list(type="level"))
som_target <- readGDX(gdx, "ov59_som_target", select=list(type="level"))

# Calculate convergence distance
distance <- abs(som_pool - som_target)
relative_distance <- distance / som_target

# After 20 years, should be <5% from target (96% convergence)
# Assuming 5-year timesteps:
time_since_change <- 20  # years
expected_convergence <- 1 - 0.85^(time_since_change)

# Check
max_distance <- max(relative_distance, na.rm=TRUE)
print(paste("Maximum relative distance from equilibrium:", round(max_distance*100, 1), "%"))

# Should be near 4% after 20 years
stopifnot(max_distance < 0.05)
```

---

### 9.3 Forest Growth Verification

**Verify Chapman-Richards growth**:
```r
# Read plantation age-class distribution
plantation_area <- readGDX(gdx, "ov32_land", select=list(type="level"))
plantation_vegc <- readGDX(gdx, "pm_carbon_density_plantation_ac")[,,"vegc",]

# For a specific cell, plot growth curve
cell <- "GLO.1"  # Example cell
vegc_by_age <- plantation_vegc[cell,,]
ages <- as.numeric(gsub("ac", "", getNames(vegc_by_age))) * 5

plot(ages, vegc_by_age, xlab="Age (years)", ylab="Vegetation Carbon (tC/ha)",
     main="Plantation Vegetation Growth Curve")

# Should follow sigmoidal pattern
# Young plantations: slow growth
# Middle age: rapid growth
# Mature: asymptotic approach to equilibrium
```

---

## 10. Limitations and Assumptions

### 10.1 Carbon Stock Limitations

**1. Static Primary Forest Carbon**:
- Primary forest carbon density does NOT change over time
- Reality: Old-growth forests continue slow net growth or may be carbon neutral
- Implication: May underestimate sequestration in protected primary forests

**2. No Urban Carbon**:
- Urban vegetation (street trees, parks) set to zero
- Reality: Significant carbon in urban green spaces (10-50 tC/ha in vegetation)
- Implication: Urban expansion carbon loss overestimated

**3. Static Subsoil Carbon**:
- Subsoil carbon does not respond to land use
- Reality: Subsoil carbon changes slowly (decades to centuries)
- Implication: Soil carbon changes underestimated for deep-rooting systems

**4. Pasture Management Simplification**:
- Pasture carbon assumed constant (natural vegetation equivalent)
- Reality: Degraded pastures have lower carbon, improved pastures higher
- Implication: Cannot model pasture improvement/degradation scenarios

---

### 10.2 Emission Calculation Limitations

**5. Instantaneous Biomass Emissions**:
- Vegetation and litter carbon loss assumed emitted immediately
- Reality: Wood products (timber, furniture) store carbon for years/decades
- Implication: Short-term emissions overestimated, long-term underestimated

**6. No Fire Emissions Separately**:
- Fire disturbances (Module 35) cause carbon loss via stock change
- But emissions lumped with general LUC emissions
- Implication: Cannot track fire emissions specifically (important for some policies)

**7. Peatland Carbon Not Modeled**:
- Module 59 uses mineral soil carbon dynamics (IPCC 2019 for mineral soils)
- Reality: Peatlands have different dynamics (very high carbon, sensitive to drainage)
- Implication: Peatland drainage/restoration not accurately represented

---

### 10.3 Soil Carbon Dynamics Limitations

**8. 20-Year Convergence Assumption**:
- Module 59 uses 15% annual convergence (based on IPCC)
- Reality: Convergence rate varies by soil type, climate (some faster, some slower)
- Implication: May overestimate speed in some soils, underestimate in others

**9. No Tillage Dynamics**:
- Default assumes full tillage for all crops
- Reality: No-till, reduced tillage increasingly adopted
- Implication: Soil carbon loss may be overestimated in regions with conservation agriculture

**10. No Manure Application**:
- Default IPCC factor assumes "medium input without manure"
- Reality: Manure application common and increases soil carbon
- Implication: Soil carbon potential underestimated where manure used

---

### 10.4 Climate and Model Coupling Limitations

**11. One-Way Climate-Carbon Coupling**:
- LPJmL provides carbon densities under future climate
- But MAgPIE land-use change does NOT feed back to climate
- Reality: Deforestation affects local/regional climate (temperature, precipitation)
- Implication: Climate-vegetation feedbacks incomplete

**12. Static LPJmL Runs**:
- LPJmL simulations done in preprocessing (fixed)
- MAgPIE cannot respond to unanticipated climate shocks during run
- Implication: Cannot model climate surprises or tipping points

---

## 11. Summary

### 11.1 Key Principles

1. **Stock-Flow Accounting**: Carbon tracked as stocks (tC), emissions as flows (tC/yr)
2. **Three Pools**: Vegetation, litter, soil carbon for each land type
3. **Dynamic Processes**: Forest growth (Chapman-Richards), soil convergence (IPCC)
4. **Emissions = Stock Change**: CO₂ emissions calculated from difference in stocks
5. **NOT Conserved**: Carbon emitted to atmosphere or sequestered from it (open system)

### 11.2 Critical Equations

**CO₂ Emissions** (Module 52):
```
Emissions = (Previous Stock - Current Stock) / Timestep Length
```

**Forest Vegetation Growth** (Module 52):
```
vegc(age) = 0 + (Mature - 0) × (1 - exp(-k × age))^m
```

**Soil Organic Matter Dynamics** (Module 59):
```
SOM_pool = lossrate × SOM_equilibrium + (1 - lossrate) × Legacy_carbon
lossrate = 1 - 0.85^years
```

### 11.3 Module Roles

| Module | Role | Key Outputs |
|--------|------|-------------|
| 52 | Carbon densities, CO₂ emissions | fm_carbon_density, vm_emissions_reg("co2_c") |
| 59 | Dynamic soil carbon (IPCC 2019) | v59_som_pool, vm_nr_som |
| 53 | CH₄ emissions from agriculture | vm_emissions_reg(*,"ch4") |
| 57 | GHG mitigation costs | im_maccs_mitigation, vm_maccs_costs |

### 11.4 Practical Implications

**For Users**:
- Carbon stocks change with land use and time
- Emissions positive = loss to atmosphere, negative = sequestration
- Soil carbon converges over ~20 years (not instant)
- Forest carbon accumulates over decades (age-dependent)

**For Developers**:
- Carbon balance NOT enforced as constraint (unlike land/water)
- Stock changes must be consistent with emissions
- Modules 52 and 59 must interface correctly (topsoil + subsoil)
- LPJmL carbon densities are fundamental input (verify data quality)

### 11.5 Verification Checklist

- [ ] CO₂ emissions match carbon stock changes (Module 52 equation)
- [ ] SOM pools converging to targets (Module 59, ~96% after 20 years)
- [ ] Forest vegetation growing along Chapman-Richards curve
- [ ] No negative carbon stocks (physical impossibility)
- [ ] Deforestation = positive emissions, afforestation = negative emissions

---

## References

**Module Documentation**:
- Module 52: `magpie-agent/modules/module_52.md`
- Module 53: `magpie-agent/modules/module_53.md`
- Module 57: `magpie-agent/modules/module_57.md`
- Module 59: `magpie-agent/modules/module_59.md`

**Source Code**:
- Module 52 emissions: `modules/52_carbon/normal_dec17/equations.gms:16-19`
- Module 52 growth: `modules/52_carbon/normal_dec17/start.gms:8-39`
- Module 59 equilibrium: `modules/59_som/cellpool_jan23/equations.gms:20-27`
- Module 59 dynamics: `modules/59_som/cellpool_jan23/equations.gms:46-52`

**External References**:
- IPCC 2006 Guidelines (Modules 53, 59)
- IPCC 2019 Refinement (Module 59)
- Chapman-Richards growth: Humpenöder et al. (2014)
- LPJmL carbon stocks: Bondeau et al. (2007)

---

**Document Status**: ✅ Complete
**Verified Against**: MAgPIE 4.x source code and module documentation
**Created**: 2025-10-22
**Last Updated**: 2025-10-22
