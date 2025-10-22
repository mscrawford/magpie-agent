# Nitrogen and Food Balance in MAgPIE

**Status**: ✅ Complete (Concise Version)
**Created**: 2025-10-22
**Conservation Laws**: Nitrogen Balance + Food Balance

---

## Part 1: Nitrogen Balance (Modules 50, 51, 59)

### 1.1 Overview

**Nitrogen Balance** in MAgPIE tracks nitrogen flows through agricultural systems but does **NOT enforce strict conservation**. Nitrogen enters (fixation, fertilizer, manure, atmospheric deposition) and leaves (harvest, emissions, leaching) the system.

**Key Modules**:
- **Module 50 (nr_soil_budget)**: Soil nitrogen budget accounting
- **Module 51 (nitrogen)**: Nitrogen demand for crops, emissions (N₂O)
- **Module 59 (SOM)**: N release from soil organic matter turnover

**NOT a Conservation Law Because**:
- Nitrogen added via fertilizer (exogenous input)
- Nitrogen removed via harvest (food/feed export)
- Nitrogen lost via emissions (N₂O, NH₃, NOₓ to atmosphere)
- Nitrogen lost via leaching (NO₃⁻ to groundwater)

---

### 1.2 Nitrogen Inputs

| Source | Module | Description | Typical Magnitude |
|--------|--------|-------------|-------------------|
| **Mineral Fertilizer** | 51 | Synthetic N applied to crops | 50-250 kg N/ha/yr (optimized) |
| **Biological N Fixation** | 50 | Legume crops (soybean, pulses) | 50-300 kg N/ha/yr (crop-specific) |
| **Manure** | 50, 18 | Livestock excreta recycled to crops | Variable (regional) |
| **Atmospheric Deposition** | 50 | Wet/dry deposition from atmosphere | 1-20 kg N/ha/yr (exogenous) |
| **SOM Mineralization** | 59 | N release from soil organic matter loss | Variable (land-use dependent) |

**Source**: Module 50, `equations.gms:18-30`

**Key Equation** (Module 51, crop N demand):
```gams
vm_nr_inorg_fert(j,kcr) + inputs_other ≥ N_demand
```

**Optimization**: MAgPIE minimizes fertilizer costs subject to meeting crop N requirements

---

### 1.3 Nitrogen Outputs

| Pathway | Module | Description | Typical Magnitude |
|---------|--------|-------------|-------------------|
| **Harvest Removal** | 51 | N in harvested biomass (food/feed/fiber) | 50-150 kg N/ha/yr |
| **N₂O Emissions** | 51, 53 | Direct + indirect nitrous oxide | 1-3% of N applied (IPCC) |
| **NH₃ Volatilization** | 50 | Ammonia losses from fertilizer/manure | 10-30% of N applied |
| **NO₃⁻ Leaching** | 50 | Nitrate runoff to groundwater | 10-40% of N surplus |
| **NOₓ Emissions** | 50 | Nitrogen oxides | <5% of N applied |

**Source**: Module 50, `equations.gms:35-60`

**Critical Emissions** (Module 51, N₂O calculation):
```gams
N2O_direct = N_applied × EF_direct × (1 - MACC_mitigation)
EF_direct = 0.01 (1% IPCC default)
```

**Source**: Module 51, `equations.gms:20-45`

---

### 1.4 Soil Nitrogen Budget

**Equation** (Module 50, `equations.gms:18-30`):
```
Inputs = Outputs + ΔSoil_N_stock
```

**Expanded**:
```
Fertilizer + Fixation + Manure + Deposition + SOM_mineralization
=
Harvest + N2O + NH3 + Leaching + NOx + ΔSoil_pool
```

**NO Strict Constraint**: Soil N pool can increase (accumulation) or decrease (depletion)

**Implication**: Model can deplete or build soil N based on management

---

### 1.5 Key Limitations

**1. No Soil N Constraint**: Soil nitrogen pool can go negative (physically impossible)
- Reality: Crops cannot extract more N than available in soil
- Implication: Model may overestimate yields in N-depleted soils

**2. Fixed IPCC Emission Factors**: Do not vary by soil type, climate, management
- Reality: EFs vary 0.3-3% depending on conditions
- Implication: Emissions may be under/overestimated regionally

**3. No N Limitation on Yields**: Yields assume sufficient N available
- Module 13 (TC) handles N-responsive yields, but default assumes N met
- Implication: Cannot model N-limited systems without fertilizer

---

## Part 2: Food Balance (Modules 16, 17, 21)

### 2.1 Overview

**Food Balance** ensures that **food supply meets food demand** at regional or global level through production and trade. This IS enforced as an **inequality constraint** (supply ≥ demand) or **equality constraint** with trade flexibility.

**Key Modules**:
- **Module 16 (Demand)**: Calculates food, feed, processing demands
- **Module 17 (Production)**: Aggregates crop and livestock production
- **Module 21 (Trade)**: Balances regional supply and demand via trade

**Mathematical Statement**:
```
∀ i ∈ Regions, ∀ k ∈ Products:
  Production(i,k) + Imports(i,k) - Exports(i,k) ≥ Demand(i,k)
```

---

### 2.2 Food Demand Components

**Module 16 Calculates** (demand driven by):

| Demand Type | Drivers | Typical Elasticities |
|-------------|---------|----------------------|
| **Food** | Population, income, diet preferences | Income elasticity: 0.3-0.8 |
| **Feed** | Livestock production (endogenous) | Derived from livestock demand |
| **Material** | Population, economic activity | Low elasticity (~0.1-0.3) |
| **Processing** | Food processing industry | Linked to food demand |
| **Seed** | Crop area (endogenous) | Fixed % of production |

**Source**: Module 16, `equations.gms` (demand system)

**Diet Scenarios**:
- **Exogenous**: SSP-based diet trajectories (meat consumption trends)
- **Endogenous** (optional): Food demand responds to prices (elasticities)

---

### 2.3 Food Supply

**Module 17 Aggregates Production**:

```gams
vm_prod_reg(i,k) = sum(cell(i,j), vm_prod(j,k))
```

**Components**:
- **Crop production**: Area × Yield (from Modules 30, 14)
- **Livestock production**: Herd size × productivity (from Module 70)
- **Primary products only**: No processing (e.g., wheat, not bread)

**Units**: Million tons dry matter per year (Mt DM/yr)

---

### 2.4 Food Balance Constraint

**Regional Self-Sufficiency** (optional):
```gams
vm_prod_reg(i,k) ≥ vm_demand(i,k)  [if trade disabled]
```

**Global Trade Balance** (Module 21):
```gams
vm_prod_reg(i,k) + vm_import(i,k) - vm_export(i,k) = vm_demand(i,k)
```

**Global Check**:
```gams
sum(i, vm_prod_reg(i,k)) = sum(i, vm_demand(i,k))  [at global level]
```

**Trade Costs**: Transport costs proportional to distance (Module 21)

**Source**: Module 21, `equations.gms:10-25`

---

### 2.5 Key Mechanisms

**1. Price Formation**:
- Food scarcity → higher prices → multiple effects:
  - Demand reduction (if price-responsive)
  - Supply increase (area expansion, intensification)
  - Trade rebalancing (imports increase, exports decrease)

**2. Food Availability**:
- If production < demand and trade constrained → food shortage
- Model becomes **infeasible** or prices spike very high

**3. Nutrition vs. Calories**:
- Module 15 (Food) tracks calories, protein, fat
- But balance enforced in DM terms (Module 21)
- Nutritional balance NOT explicitly constrained

---

### 2.6 Scenarios

**Scenario 1: Food-Abundant World**
- Production > Demand globally
- Surplus stored or wasted (not modeled explicitly)
- Low food prices

**Scenario 2: Regional Food Deficit**
- Production < Demand in region
- Imports meet shortfall
- Higher food prices in deficit region

**Scenario 3: Global Food Scarcity**
- Production < Demand globally
- Cannot be resolved by trade alone
- Triggers:
  - Demand reduction (if endogenous)
  - Emergency land expansion
  - Very high prices (shadow price of food constraint)

---

### 2.7 Verification

**Food Balance Check**:
```r
library(magpie4)

# Read production and demand
production <- production(gdx, level="regglo", products="k")
demand <- demand(gdx, level="regglo", products="k")

# Read trade
trade_balance <- trade_balance(gdx)  # Imports - Exports

# Check constraint
supply <- production + trade_balance
shortage <- demand - supply

# Should be ≤ 0 (supply ≥ demand)
max_shortage <- max(shortage)
print(paste("Maximum food shortage:", max_shortage, "Mt DM"))

stopifnot(max_shortage < 0.01)  # Small tolerance for numerical error
```

**Expected**: All regions have supply ≥ demand (or very close)

---

### 2.8 Limitations

**1. No Food Waste**: Waste not modeled explicitly
- Reality: ~30% of food wasted globally
- Implication: Actual demand for production lower than gross consumption

**2. No Strategic Reserves**: No stocks or buffer storage
- Reality: Countries maintain emergency grain reserves
- Implication: Cannot model buffer stock policies

**3. Perfect Markets**: No market failures or access constraints
- Reality: Food may be available globally but not accessible locally (poverty, conflict)
- Implication: Cannot model food security vs. food availability distinction

**4. Aggregated Products**: Detailed food types aggregated to ~20 commodities
- Reality: Diets more diverse (1000s of food items)
- Implication: Substitution within commodity groups not modeled

---

## Summary: Five Conservation/Balance Laws in MAgPIE

### Comparison Table

| Law | Type | Enforcement | Modules | Can Violate? |
|-----|------|-------------|---------|--------------|
| **Land Balance** | Stock (Equality) | Hard | 10, 29-35 | No - model fails if violated |
| **Water Balance** | Flow (Inequality) | Soft (buffer) | 42, 43 | Yes - groundwater buffer for exogenous |
| **Carbon Balance** | Stock-Flow | None | 52, 53, 59 | N/A - emissions allowed (open system) |
| **Nitrogen Balance** | Flow | None | 50, 51, 59 | N/A - inputs/outputs allowed |
| **Food Balance** | Flow (Equality) | Hard (with trade) | 16, 17, 21 | No - trade adjusts to meet demand |

---

### Key Insights

**Strictly Conserved**:
1. **Land**: Total area constant in each cell (physical constraint)
2. **Food**: Supply = Demand at global level (with trade adjustment)

**Soft Constraints**:
3. **Water**: Supply ≥ Demand (but buffer allows violation for exogenous)

**Not Conserved** (Open System):
4. **Carbon**: Emissions/sequestration to/from atmosphere
5. **Nitrogen**: Fertilizer inputs, emission outputs

**Verification Priority**:
1. **Land balance** - most critical (physical impossibility if violated)
2. **Food balance** - important for model realism (shortages unrealistic)
3. **Water balance** - check for excessive buffer use (unsustainable)
4. **Carbon/Nitrogen** - verify accounting consistency, not conservation

---

## References

**Nitrogen Documentation**:
- Module 50: `magpie-agent/modules/module_50.md`
- Module 51: `magpie-agent/modules/module_51.md`
- Module 59: `magpie-agent/modules/module_59.md`

**Food Documentation**:
- Module 16: `magpie-agent/modules/module_16.md`
- Module 17: `magpie-agent/modules/module_17.md`
- Module 21: `magpie-agent/modules/module_21.md`

**Core Documentation**:
- Phase 1: `magpie-agent/core_docs/Phase1_Core_Architecture.md`
- Phase 2: `magpie-agent/core_docs/Phase2_Module_Dependencies.md`

---

**Document Status**: ✅ Complete (Concise)
**Verified Against**: MAgPIE 4.x module documentation
**Created**: 2025-10-22
**Note**: This is a concise summary. Full documentation available in individual module docs.
