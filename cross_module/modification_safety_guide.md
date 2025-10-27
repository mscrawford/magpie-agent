# Modification Safety Guide for High-Centrality Modules

**Status**: ✅ Complete
**Created**: 2025-10-22
**Purpose**: Critical safety protocols for modifying MAgPIE's most interconnected modules

---

## ⚠️ WARNING: High-Risk Modification Zone

This guide covers the **4 highest-centrality modules** in MAgPIE:
- **Module 10 (Land)**: Central land allocation hub
- **Module 11 (Costs)**: Cost aggregator (highest dependency count)
- **Module 17 (Production)**: Spatial aggregation hub
- **Module 56 (GHG Policy)**: Environmental-economic bridge

**For exact dependency counts, see**: `core_docs/Module_Dependencies.md`

**Modifying these modules without proper precautions can break the entire model.**

**Before you modify ANY of these modules:**
1. Read this entire guide
2. Understand dependency chains
3. Check conservation law implications
4. Follow testing protocols
5. Verify all downstream modules still work

---

## 1. Module 10: Land Allocation (HIGHEST RISK)

### 1.1 Why Module 10 is Critical

**Centrality**: **HIGHEST** in entire model
- Role: **Central land allocation hub**
- See `core_docs/Module_Dependencies.md` for complete dependency list

**File**: `modules/10_land/landmatrix_dec18/`

**Core Function**: Maintains land area conservation and tracks transitions between 7 land types

### 1.2 Critical Variables Exported

| Variable | Consumers | Risk Level | Description |
|----------|-----------|------------|-------------|
| `vm_land(j,land)` | 11 modules | 🔴 EXTREME | Current land allocation by type |
| `vm_lu_transitions(j,land_from,land_to)` | 8 modules | 🔴 EXTREME | Transition matrix (net changes only) |
| `vm_landexpansion(j,land)` | 7 modules | 🟠 HIGH | Land gained from other types |
| `vm_landreduction(j,land)` | 6 modules | 🟠 HIGH | Land lost to other types |
| `pcm_land(j,land)` | 5 modules | 🟡 MEDIUM | Previous timestep land allocation |

**Downstream Modules** (ALL will break if vm_land breaks):
- 11_costs, 17_production, 22_land_conservation, 29_cropland, 30_croparea, 31_past, 32_forestry, 34_urban, 35_natveg, 52_carbon, 58_peatland, 59_som, 60_bioenergy, 62_material, 71_disagg_lvst

### 1.3 Conservation Law: LAND BALANCE (STRICT EQUALITY)

**Constraint**: `q10_land_area` enforces strict land area conservation

**For full equation details**: See `cross_module/land_balance_conservation.md`

**What This Means**:
- Total land area in each cell MUST remain constant
- If you break this equation, the model becomes **physically impossible**
- Land cannot be created or destroyed, only converted

**Violation Symptoms**:
- Model becomes infeasible
- Solver reports "no feasible solution"
- CONOPT error: "Equation infeasible"

**How to Avoid**:
- NEVER modify `vm_land` dimensions without updating ALL 15 consumers
- NEVER add land types without updating `land` set across entire model
- NEVER modify `pcm_land` calculation (in postsolve.gms:8-9)
- ALWAYS ensure transition matrix sums remain equal

### 1.4 Common Mistakes and Fixes

**❌ MISTAKE 1**: Adding a new land type to `land` set only in Module 10
```gams
* WRONG: Only updating sets.gms in Module 10
set land / crop, past, forest, urban, newtype /;
```

**✅ FIX**: Update land type across ALL modules and conservation law documentation
1. Update `core/sets.gms` (global land set)
2. Update ALL 15 consumer modules to handle new type
3. Update land balance conservation constraint
4. Update carbon pools (Module 52) if new type stores carbon
5. Update cost accounting (Module 11) for new land costs

---

**❌ MISTAKE 2**: Modifying transition matrix without ensuring row/column sums
```gams
* WRONG: Allowing transitions that violate conservation
vm_lu_transitions.fx(j,"primforest","crop") = 5;  * 5 Mha
* But forgetting that primforest must LOSE 5 Mha total
```

**✅ FIX**: Ensure matrix consistency
```gams
* Transition matrix MUST satisfy:
* Row sums: sum(land_to, vm_lu_transitions(j,land_from,land_to)) = pcm_land(j,land_from)
* Column sums: sum(land_from, vm_lu_transitions(j,land_from,land_to)) = vm_land(j,land_to)
```

See: `cross_module/land_balance_conservation.md` for full transition matrix rules

---

**❌ MISTAKE 3**: Changing land allocation without updating carbon stocks
```gams
* WRONG: Forest → Crop without CO2 emissions
vm_land.fx(j,"crop") = 100;
vm_land.fx(j,"forest") = 50;  * Lost 50 Mha forest
* Forgot: 50 Mha × carbon_density → CO2 emissions
```

**✅ FIX**: Always check carbon implications
1. Read `modules/52_carbon/` documentation
2. Understand `vm_carbon_stock` depends on `vm_land`
3. Verify CO2 emissions from Module 52 reflect land change
4. Check GHG policy costs (Module 56) update correctly

---

### 1.5 Testing Protocol for Module 10 Changes

**Minimum Test Suite** (MUST pass all):

1. **Land Conservation Test**:
   ```r
   # Verify total land area constant
   library(magpie4)
   land_total <- land(gdx, level="cell")
   stopifnot(all(abs(dimSums(land_total, dim=3) -
                     dimSums(land_total[,1,], dim=3)) < 1e-6))
   ```

2. **Transition Matrix Test**:
   ```r
   # Verify row sums = column sums
   transitions <- land_transitions(gdx)
   row_sums <- dimSums(transitions, dim="to")
   col_sums <- dimSums(transitions, dim="from")
   stopifnot(all(abs(row_sums - col_sums) < 1e-6))
   ```

3. **Downstream Module Test**:
   - Run model with modified Module 10
   - Verify ALL 15 consumer modules execute without errors
   - Check no new infeasibilities or warnings

4. **Conservation Law Test**:
   - Verify land balance holds for ALL cells in ALL time steps
   - Check carbon balance (Module 52) reflects land changes
   - Verify water balance (Module 43) if irrigation land changes

**Test Duration**: Expect 2-4 hours for full validation suite

---

### 1.6 Safe Modification Patterns

**✅ SAFE**: Adding new constraints on existing transitions
```gams
* Example: Prevent forest → crop conversion in protected areas
vm_lu_transitions.fx(j,"forest","crop")$(pm_land_conservation(j,"forest") > 0) = 0;
```

**✅ SAFE**: Modifying transition costs (affects Module 29, 30, 32, 35)
```gams
* Example: Higher cost for primary forest conversion
vm_cost_landcon.up(j,"primforest") = 1e6;  * USD/ha
```

**⚠️ RISKY**: Changing land type definitions
- Requires updating 20+ files across model
- MUST coordinate with Module 29-35 developers
- Recommend: Create new realization instead of modifying existing

**🔴 NEVER DO**: Breaking land conservation constraint
- Model will become infeasible
- No recovery possible without reverting changes

---

## 2. Module 11: Costs (CRITICAL)

### 2.1 Why Module 11 is Critical

**Centrality**: HIGHEST dependency count
- Role: **Defines MAgPIE's optimization objective**
- See `core_docs/Module_Dependencies.md` for complete dependency list

**File**: `modules/11_costs/default/`

**Core Function**: Aggregates all costs into `vm_cost_glo` which the solver minimizes

### 2.2 The Objective Function

**Objective**: `q11_cost_glo` aggregates regional costs into global objective function

**For full equation details**: See `modules/module_11.md`

**What This Means**:
- `vm_cost_glo` is **THE variable MAgPIE minimizes**
- Every cost component affects optimal land use
- Missing cost = "free" resource = model exploits it infinitely

**Critical Dependency**: Module 11 depends on cost variables from 27 modules:

| Cost Variable | Source Module | Typical Magnitude (USD17/yr) |
|---------------|---------------|------------------------------|
| `vm_cost_prod_crop` | 38_factor_costs | ~100-500 billion |
| `vm_cost_prod_past` | 38_factor_costs | ~50-100 billion |
| `vm_cost_prod_livst` | 70_livestock | ~200-400 billion |
| `vm_nr_inorg_fert_costs` | 50_nr_soil_budget | ~50-150 billion |
| `vm_emission_costs` | 56_ghg_policy | 0-500 billion (policy-dependent) |
| `vm_cost_landcon` | 29-35 (land modules) | ~10-50 billion |
| `vm_cost_trade` | 21_trade | ~5-20 billion |

**Source**: module_11.md (lines 84-115)

### 2.3 Common Mistakes and Fixes

**❌ MISTAKE 1**: Adding new production activity without adding cost
```gams
* WRONG: New crop type with production but no cost
* In Module 30: vm_prod(j,"newcrop") = ...
* In Module 11: [forgot to add vm_cost_prod_newcrop]
```

**Result**: Model uses "newcrop" infinitely (free lunch)

**✅ FIX**: Always add cost component
```gams
* In Module 11, equations.gms:
q11_cost_reg(i2) .. v11_cost_reg(i2) =e=
    ... existing terms ...
    + vm_cost_prod_newcrop(i2);  * ADD THIS
```

---

**❌ MISTAKE 2**: Wrong cost units (most common error)
```gams
* WRONG: Using USD/ha when should be mio. USD17/yr
vm_cost_landcon.up(j,land) = 500;  * Meant 500 USD/ha but interpreted as 500 mio. USD/yr
```

**✅ FIX**: Always check units
- **ALL costs in Module 11 must be**: `mio. USD17MER/yr`
- **Convert**: `(USD/ha) × (Mha) × (1e6 ha/Mha) / (1e6 mio.) = USD (same as mio.)`

---

**❌ MISTAKE 3**: Negative costs without justification
```gams
* WRONG: Negative cost = revenue = model does infinitely
vm_cost_timber(i) = -100;  * DANGER: Free money!
```

**✅ FIX**: Use reward variable instead
```gams
* Module 56 does this correctly for CDR:
vm_reward_cdr_aff(i) = [positive value]  * Explicit reward
* Then in Module 11:
q11_cost_reg(i2) =e= ... - vm_reward_cdr_aff(i2);  * Subtract reward
```

---

### 2.4 Testing Protocol for Module 11 Changes

**Minimum Test Suite**:

1. **Cost Magnitude Check**:
   ```r
   library(magpie4)
   costs <- costs(gdx, level="regglo")

   # Global costs should be 500-2000 billion USD17/yr (no policy)
   stopifnot(costs["GLO",,"total"] > 500 & costs["GLO",,"total"] < 5000)

   # Regional costs should be positive
   stopifnot(all(costs[,,"total"] > 0))
   ```

2. **Cost Component Audit**:
   ```r
   # Check all 30+ components sum to total
   component_sum <- sum(costs[,,setdiff(getNames(costs), "total")])
   total_cost <- costs[,,"total"]
   stopifnot(abs(component_sum - total_cost) < 0.01)  * 1% tolerance
   ```

3. **Optimization Behavior Test**:
   - Run model with baseline scenario
   - Introduce small perturbation to your new cost
   - Verify model responds appropriately (reduces activity if cost increases)
   - Check solution is NOT infinitely exploiting your cost variable

4. **Negative Cost Detection**:
   ```r
   # Flag any negative cost components (usually errors)
   negative_costs <- costs[costs < 0]
   if(length(negative_costs) > 0) warning("Negative costs detected!")
   ```

---

## 3. Module 17: Production (HIGH RISK)

### 3.1 Why Module 17 is Critical

**Centrality**: HIGH
- Role: **Spatial aggregation hub** (cell → region)
- See `core_docs/Module_Dependencies.md` for complete dependency list

**File**: `modules/17_production/flexreg_apr16/`

**Core Function**: Aggregates cell-level production to regional production for trade

### 3.2 Critical Variables Exported

| Variable | Consumers | Description |
|----------|-----------|-------------|
| `vm_prod_reg(i,k)` | 9 modules | Regional production (for trade, demand) |
| `pm_prod_init(j,k)` | 3 modules | Initial production (solver starting point) |

**Key Equation**: `q17_prod_reg` aggregates cell-level production to regional level

**For full equation details**: See `modules/module_17.md`

**What This Means**:
- Regional production = sum of all cells in region
- No inter-cell trade modeled (free transport within region)
- Provides supply for Module 21 (Trade) to balance against demand

### 3.3 Dependency Chain Impact

**Upstream → Module 17 → Downstream**:
```
Module 30 (Croparea) → vm_prod(j,k) → Module 17 → vm_prod_reg(i,k) → Module 21 (Trade)
                                                                      → Module 16 (Demand)
                                                                      → Module 11 (Costs)
                                                                      → Module 73 (Timber)
                                                                      → 9 other modules
```

**Implication**: Breaking Module 17 breaks the entire production-trade-demand system

### 3.4 Common Mistakes and Fixes

**❌ MISTAKE 1**: Forgetting that `vm_prod_reg` only covers PLANT commodities
```gams
* WRONG: Trying to aggregate livestock production
vm_prod_reg(i,"beef") = sum(cell(i,j), vm_prod(j,"beef"));
* ERROR: Livestock modeled at regional level (Module 70), not cell level
```

**✅ FIX**: Check commodity scope
- **Module 17 handles**: Crops (kcr), pasture
- **Module 70 handles**: Livestock (kli) — regional only
- **Module 73 handles**: Timber — special aggregation

---

**❌ MISTAKE 2**: Modifying `pm_prod_init` without understanding solver impact
```gams
* WRONG: Setting unrealistic initial production
pm_prod_init(j,"rice") = 1000;  * 1000 mio. tDM in one cell!
```

**Result**: Solver starts far from optimal solution, slow convergence or failure

**✅ FIX**: Use realistic initialization (presolve.gms:10-16)
```gams
* Correct initialization = Area × Yield
pm_prod_init(j,kcr) = sum(w, fm_croparea("y1995",j,w,kcr) * pm_yields_semi_calib(j,kcr,w));
```

---

**❌ MISTAKE 3**: Changing aggregation equation without checking conservation laws
```gams
* WRONG: Adding production from external source
vm_prod_reg(i,k) =e= sum(cell(i,j), vm_prod(j,k)) + external_prod(i,k);
```

**Problem**: Food balance expects production = cell-level sum. Adding external source breaks mass balance.

**✅ FIX**: If adding external production, update:
1. Module 21 (Trade) to account for new source
2. Module 16 (Demand) if demand changes
3. Food balance documentation (`cross_module/nitrogen_food_balance.md`)

---

### 3.5 Testing Protocol for Module 17 Changes

**Minimum Test Suite**:

1. **Aggregation Correctness**:
   ```r
   library(magpie4)
   prod_cell <- production(gdx, level="cell", products="kcr")
   prod_reg <- production(gdx, level="regglo", products="kcr")

   # Sum cells to regions and compare to vm_prod_reg
   prod_reg_calc <- dimSums(prod_cell, dim="cell", mapping=cell2region)
   stopifnot(all(abs(prod_reg - prod_reg_calc) < 0.01))
   ```

2. **Food Balance Check** (see `cross_module/nitrogen_food_balance.md:229-250`):
   ```r
   # Verify supply ≥ demand after trade
   production <- production(gdx, level="regglo", products="k")
   demand <- demand(gdx, level="regglo", products="k")
   trade_balance <- trade_balance(gdx)

   supply <- production + trade_balance
   shortage <- demand - supply
   stopifnot(max(shortage) < 0.01)  # Small tolerance for solver precision
   ```

3. **Downstream Module Check**:
   - Verify Module 21 (Trade) still balances
   - Verify Module 16 (Demand) receives correct supply signal
   - Check Module 11 (Costs) includes any new cost components

---

## 4. Module 56: GHG Policy (HIGH RISK)

### 4.1 Why Module 56 is Critical

**Centrality**: HIGH
- Role: **Environmental-economic bridge** (emissions → costs)
- See `core_docs/Module_Dependencies.md` for complete dependency list

**File**: `modules/56_ghg_policy/price_aug22/`

**Core Function**: Converts emissions to costs via carbon pricing, driving mitigation decisions

### 4.2 Critical Variables Exported

| Variable | Consumers | Description |
|----------|-----------|-------------|
| `vm_emission_costs(i)` | 11_costs | Total GHG costs (enters objective) |
| `vm_reward_cdr_aff(i)` | 11_costs | Carbon removal revenue (afforestation) |
| `im_pollutant_prices(t,i,pollutants,emis_source)` | 32_forestry, 60_bioenergy | Price signals for land-use decisions |

**Key Equation**: `q56_emission_costs` calculates GHG policy costs entering objective function

**For full equation details**: See `modules/module_56.md`

**What This Means**:
- Emission costs = Emissions × Price
- Enters Module 11 objective function
- Higher costs → model avoids emission-intensive activities

### 4.3 Policy Levers (100+ Scenarios)

**Configuration Switches** (input.gms:84-117):

| Switch | Default | Options | Impact |
|--------|---------|---------|--------|
| `c56_pollutant_prices` | SSP2-NPi2025 | 100+ IAM scenarios | Price trajectory (0-1000+ USD/tCO2) |
| `c56_emis_policy` | reddnatveg_nosoil | 60+ policies | Which emissions priced |
| `c56_carbon_stock_pricing` | actualNoAcEst | actual / actualNoAcEst | Accounting method |
| `s56_c_price_induced_aff` | 1 (ON) | 0/1 | Enable afforestation CDR |

**Source**: module_56.md (lines 32-42)

### 4.4 Complex Interactions

**Module 56 affects nearly everything**:

```
56_ghg_policy
   ├─ Emissions Pricing → 11_costs (objective function)
   │     └─ Drives land-use change across 10, 29-35
   ├─ CDR Rewards → 32_forestry (afforestation incentive)
   │     └─ Affects land competition (forest vs. crop)
   └─ Price Signals → 60_bioenergy (bioenergy vs. food)
         └─ Affects crop demand and trade (21, 16)
```

**Conservation Law Impact**:
- **Land balance**: GHG policy shifts land allocation (forest ↑, crop ↓)
- **Carbon balance**: Pricing drives carbon stock changes (sequestration)
- **Food balance**: Forest expansion reduces crop area → trade adjusts

See: `cross_module/carbon_balance_conservation.md:450-550` for full carbon-policy interactions

### 4.5 Common Mistakes and Fixes

**❌ MISTAKE 1**: Changing emission pricing without checking cost magnitude
```gams
* WRONG: Setting unrealistically high carbon price
im_pollutant_prices(t,i,"co2_c","all") = 10000;  * 10,000 USD/tCO2!
```

**Result**: Emission costs dominate objective function, model only optimizes for emissions (no food production)

**✅ FIX**: Use realistic price scenarios
- Typical range: 0-500 USD/tCO2 by 2100
- Check `vm_emission_costs` < 50% of `vm_cost_glo`
- Test sensitivity to price changes (±20%)

---

**❌ MISTAKE 2**: Pricing emissions without accounting for CDR
```gams
* WRONG: High CO2 price but no afforestation reward
im_pollutant_prices(t,i,"co2_c","all") = 200;
s56_c_price_induced_aff = 0;  * Disabled CDR!
```

**Result**: Model pays for emissions but cannot earn revenue from removals → unrealistic mitigation costs

**✅ FIX**: Enable CDR if pricing CO2 (input.gms:103)
```gams
s56_c_price_induced_aff = 1;  * Enable afforestation CDR
* Check vm_reward_cdr_aff provides incentive for forest expansion
```

---

**❌ MISTAKE 3**: Forgetting that Module 56 uses PREVIOUS carbon stocks
```gams
* WRONG: Expecting immediate emission cost response
* Reality: q56_emis_pricing_co2 uses (pcm_carbon_stock - vm_carbon_stock)
*          pcm_carbon_stock = PREVIOUS timestep (5-10 years ago)
```

**Implication**: Emission costs lag land-use change by one timestep

**✅ FIX**: Account for lag in scenario design
- Emission costs in 2040 reflect 2030-2040 land change
- Use cumulative emissions for climate policy scenarios
- Don't expect instant response to price changes

**Source**: module_56.md (lines 79-101)

---

### 4.6 Testing Protocol for Module 56 Changes

**Minimum Test Suite**:

1. **Cost Magnitude Check**:
   ```r
   library(magpie4)

   # Emission costs should be 0-50% of total costs
   costs <- costs(gdx, level="regglo")
   emis_costs <- costs[,,"emission_costs"]
   total_costs <- costs[,,"total"]

   stopifnot(all(emis_costs / total_costs < 0.5))
   stopifnot(all(emis_costs >= 0))  # No negative emission costs
   ```

2. **Carbon Balance Verification** (see `cross_module/carbon_balance_conservation.md`):
   ```r
   # Verify CO2 emissions = carbon stock change
   emis_co2 <- emissions(gdx, type="co2_c", level="regglo")
   carbon_stocks <- carbonstock(gdx, level="regglo")

   # Check: emissions ≈ -Δ(carbon stocks) / timestep
   # (Negative because emissions reduce stocks)
   ```

3. **Afforestation Response Test**:
   ```r
   # Compare baseline (no C-price) vs. policy scenario
   forest_baseline <- land(gdx_baseline, type="forestry")
   forest_policy <- land(gdx_policy, type="forestry")

   # Forest area should increase with high C-price
   stopifnot(forest_policy > forest_baseline)
   ```

4. **Downstream Module Check**:
   - Verify Module 32 (Forestry) responds to CDR rewards
   - Check Module 11 (Costs) includes emission costs
   - Confirm land allocation (Module 10) shifts toward carbon storage

---

## 5. Cross-Module Testing Protocols

### 5.1 Circular Dependency Verification

**Critical Feedback Cycles** (from Module_Dependencies.md:151-179):

1. **Production-Yield-Livestock Triangle**:
   ```
   17_production ←→ 14_yields ←→ 70_livestock ←→ 17_production
   ```

   **Test**: Verify cycle converges
   ```r
   # Compare yields between iterations
   yields_t1 <- readGDX(gdx, "ov_yld", select=list(t="y2025"))
   yields_t2 <- readGDX(gdx, "ov_yld", select=list(t="y2030"))

   # Yields should stabilize (not oscillate)
   yield_change <- abs(yields_t2 - yields_t1) / yields_t1
   stopifnot(all(yield_change < 0.5))  # <50% change per timestep
   ```

2. **Land-Vegetation Bidirectional**:
   ```
   10_land ←→ 35_natveg ←→ 22_land_conservation
   ```

   **Test**: Verify land conservation constraint not violated
   ```r
   # Check protected areas respected
   land_use <- land(gdx, type="natveg")
   land_protection <- land_conservation(gdx)

   # Natural vegetation in protected areas should remain constant
   protected_natveg <- land_use * land_protection
   # Verify: protected_natveg[t2] ≈ protected_natveg[t1]
   ```

3. **Forest-Carbon Cycle** (5-module feedback):
   ```
   32_forestry ←→ 30_croparea ←→ 10_land ←→ 35_natveg ←→ 56_ghg_policy
   ```

   **Test**: Verify carbon pricing affects forest allocation
   ```r
   # Compare baseline vs. high C-price
   forest_area_baseline <- land(gdx_baseline, type="forestry")
   forest_area_policy <- land(gdx_policy, type="forestry")
   carbon_price <- readGDX(gdx_policy, "im_pollutant_prices")[,,"co2_c"]

   # Forest should increase with C-price
   stopifnot(cor(carbon_price, forest_area_policy - forest_area_baseline) > 0.5)
   ```

### 5.2 Conservation Law Verification

After modifying **ANY** of the 4 high-centrality modules, verify ALL 5 conservation laws:

#### 5.2.1 Land Balance (Module 10)

**Constraint**: `cross_module/land_balance_conservation.md`

```r
# Test: Total land area constant in each cell
land_total <- land(gdx, level="cell")
land_area_t1 <- dimSums(land_total[,"y2020",], dim="land")
land_area_t2 <- dimSums(land_total[,"y2050",], dim="land")

stopifnot(all(abs(land_area_t2 - land_area_t1) < 1e-6))
```

#### 5.2.2 Water Balance (Module 43)

**Constraint**: `cross_module/water_balance_conservation.md`

```r
# Test: Water demand ≤ water availability
water_dem <- water_usage(gdx, level="cell", source="all")
water_avail <- water_avail(gdx, level="cell")

shortage <- water_dem - water_avail
stopifnot(all(shortage <= 0.01))  # Small tolerance for buffer
```

#### 5.2.3 Carbon Balance (Module 52)

**Constraint**: `cross_module/carbon_balance_conservation.md`

```r
# Test: CO2 emissions ≈ -Δ(carbon stocks) / timestep
emis_co2 <- emissions(gdx, type="co2_c", level="cell")
carbon_stocks <- carbonstock(gdx, level="cell", subcategories="all")

# Calculate stock change
delta_C <- carbon_stocks[,"y2030",] - carbon_stocks[,"y2025",]
timestep <- 5  # years

# Verify: emissions ≈ -delta_C / timestep (within 10%)
emis_expected <- -delta_C / timestep
stopifnot(all(abs(emis_co2 - emis_expected) / emis_expected < 0.10))
```

#### 5.2.4 Food Balance (Module 17, 21)

**Constraint**: `cross_module/nitrogen_food_balance.md`

```r
# Test: Production + trade ≥ demand
production <- production(gdx, level="regglo", products="k")
demand <- demand(gdx, level="regglo", products="k")
trade_balance <- trade_balance(gdx)  # Imports - Exports

supply <- production + trade_balance
shortage <- demand - supply

stopifnot(all(shortage < 0.01))  # Supply meets demand
```

#### 5.2.5 Nitrogen Balance (Module 50, 51)

**Constraint**: `cross_module/nitrogen_food_balance.md`

```r
# Test: Nitrogen inputs ≈ outputs + soil change (no strict constraint)
n_inputs <- nr_inputs(gdx)  # Fertilizer + fixation + deposition
n_outputs <- nr_outputs(gdx)  # Harvest + emissions + leaching
n_soil_change <- nr_soil_change(gdx)

# Check: inputs ≈ outputs + soil_change (within 20%, loose constraint)
n_balance <- n_inputs - n_outputs - n_soil_change
stopifnot(all(abs(n_balance / n_inputs) < 0.20))
```

### 5.3 Integration Test Suite

**Full Validation Protocol** (run after ANY modification to Modules 10, 11, 17, 56):

```r
# Full test suite (30-60 minutes runtime)
library(magpie4)
library(testthat)

test_modification_safety <- function(gdx_baseline, gdx_modified) {

  # 1. Conservation Laws
  test_that("Land balance conserved", {
    # [Land balance test from 5.2.1]
  })

  test_that("Water balance not violated", {
    # [Water balance test from 5.2.2]
  })

  test_that("Carbon balance consistent", {
    # [Carbon balance test from 5.2.3]
  })

  test_that("Food balance maintained", {
    # [Food balance test from 5.2.4]
  })

  # 2. Module-Specific Tests
  test_that("Module 10: Land transitions sum correctly", {
    # [Transition matrix test]
  })

  test_that("Module 11: All costs positive", {
    costs <- costs(gdx_modified, level="regglo")
    expect_true(all(costs >= 0))
  })

  test_that("Module 17: Production aggregation correct", {
    # [Aggregation test from 3.5]
  })

  test_that("Module 56: Emission costs reasonable", {
    # [Cost magnitude test from 4.6]
  })

  # 3. Circular Dependency Tests
  test_that("Production-yield cycle converges", {
    # [Cycle convergence test from 5.1]
  })

  # 4. Regression Tests
  test_that("Model output within 20% of baseline", {
    vars <- c("vm_land", "vm_prod_reg", "vm_cost_glo", "vm_emissions_reg")
    for(var in vars) {
      baseline <- readGDX(gdx_baseline, var)
      modified <- readGDX(gdx_modified, var)
      rel_diff <- abs(modified - baseline) / (baseline + 1e-6)
      expect_true(all(rel_diff < 0.20))  # <20% change
    }
  })
}

# Run test suite
test_modification_safety(gdx_baseline, gdx_modified)
```

---

## 6. Emergency Debugging Guide

### 6.1 Common Error Patterns

#### Error Pattern 1: Model Infeasible

**Symptoms**:
```
*** Solve status (1): MODEL INFEASIBLE
*** Model status (4): Infeasible
*** Equation q10_land_area infeasible
```

**Likely Causes** (Module 10):
1. Land conservation constraint violated (sum(vm_land) ≠ pcm_land)
2. Transition matrix row/column sums inconsistent
3. New land type added without updating conservation constraint

**Fix**:
1. Check `vm_land` bounds: `vm_land.lo`, `vm_land.up`
2. Verify transition matrix: `sum(land_from, vm_lu_transitions) = pcm_land`
3. Review recent changes to Module 10 equations

---

#### Error Pattern 2: Unrealistic Costs

**Symptoms**:
```
*** vm_cost_glo = -1e6  (negative!)
*** vm_cost_glo = 1e15  (too high!)
```

**Likely Causes** (Module 11):
1. Negative cost component (free money)
2. Missing cost for new activity (free resource)
3. Wrong cost units (USD vs. mio. USD)

**Fix**:
1. Check all cost components in `q11_cost_reg` equation
2. Verify units: ALL costs must be `mio. USD17MER/yr`
3. Run cost magnitude test (Section 2.4)

---

#### Error Pattern 3: Production-Demand Mismatch

**Symptoms**:
```
*** Food shortage in region SSA: 100 Mt DM
*** Trade infeasible: exports > production
```

**Likely Causes** (Module 17):
1. Production aggregation incorrect (vm_prod_reg ≠ sum(vm_prod))
2. Food balance broken (production + trade < demand)
3. Cell-region mapping changed

**Fix**:
1. Verify `q17_prod_reg` equation unchanged
2. Check `cell(i,j)` mapping set
3. Run food balance test (Section 5.2.4)

---

#### Error Pattern 4: Emission Costs Dominate

**Symptoms**:
```
*** vm_emission_costs > 90% of vm_cost_glo
*** Cropland area → 0 (model starving population to reduce emissions)
```

**Likely Causes** (Module 56):
1. Carbon price too high for scenario
2. CDR reward mechanism broken
3. Emission accounting double-counted

**Fix**:
1. Check `im_pollutant_prices`: should be 0-500 USD/tCO2
2. Verify `s56_c_price_induced_aff = 1` (CDR enabled)
3. Check emission costs < 50% of total costs (Section 4.6)

---

### 6.2 Debugging Decision Tree

```
Is model infeasible?
├─ YES → Check conservation constraints
│   ├─ Land balance (Module 10)
│   ├─ Water balance (Module 43)
│   └─ Food balance (Module 21)
│
└─ NO → Is solution unrealistic?
    ├─ YES → Check costs
    │   ├─ Negative costs (Module 11)
    │   ├─ Missing costs (new activities)
    │   └─ Wrong cost magnitude (Module 56)
    │
    └─ NO → Does model run but results differ from baseline?
        ├─ Production changes > ±20%? → Check Module 17
        ├─ Land use changes > ±30%? → Check Module 10
        ├─ Emissions changes > ±50%? → Check Module 56
        └─ Costs changes > ±40%? → Check Module 11
```

### 6.3 Rollback Protocol

**If modification causes catastrophic failure**:

1. **Immediate Rollback**:
   ```bash
   git checkout HEAD^ modules/XX_name/  # Revert to previous version
   git status  # Verify only modified module reverted
   ```

2. **Identify Breaking Change**:
   ```bash
   git diff HEAD^ modules/XX_name/  # See what changed
   git log --oneline modules/XX_name/  # Find last working commit
   ```

3. **Incremental Re-Implementation**:
   - Apply changes in small steps
   - Test after each step
   - Identify exact line that breaks model

4. **Report Issue**:
   - Document error message
   - Provide minimal reproducible example
   - Share with MAgPIE development team

---

## 7. Best Practices Summary

### 7.1 Before Modifying High-Centrality Modules

**Checklist**:
- [ ] Read this entire guide
- [ ] Read module documentation (`magpie-agent/modules/module_XX.md`)
- [ ] Understand dependency chains (Module_Dependencies.md)
- [ ] Check conservation law implications (cross_module/*.md)
- [ ] Create git branch for changes
- [ ] Set up baseline comparison scenario

### 7.2 During Modification

**Checklist**:
- [ ] Modify only ONE module at a time
- [ ] Test after EVERY equation change
- [ ] Verify conservation laws still hold
- [ ] Check cost magnitude after cost changes
- [ ] Document WHY you made each change (code comments)
- [ ] Update module documentation if interface changes

### 7.3 After Modification

**Checklist**:
- [ ] Run full test suite (Section 5.3)
- [ ] Compare to baseline: <20% difference for key variables
- [ ] Verify all downstream modules still function
- [ ] Test circular dependency convergence
- [ ] Update conservation law documentation if needed
- [ ] Create pull request with test results

### 7.4 Safe Modification Strategies

**✅ SAFEST**: Add constraints to existing equations
- Example: Prevent forest conversion in protected areas
- Minimal risk: Only affects optimization space, not structure

**✅ SAFE**: Add new cost components (Module 11)
- Always verify cost units
- Test that cost doesn't dominate objective
- Check activity response to cost changes

**⚠️ MODERATE RISK**: Modify existing equations
- Requires full testing protocol
- Check all downstream modules
- Verify conservation laws

**🔴 HIGH RISK**: Change interface variable dimensions
- Requires updating ALL consumers
- Can break multiple modules simultaneously
- Recommend: Create new realization instead

**🔴 NEVER DO**: Break conservation constraints
- Land balance (Module 10): Model becomes infeasible
- Food balance (Module 21): Starvation scenarios unrealistic
- Cost aggregation (Module 11): No objective function = no solution

---

## 8. Resources and Further Reading

### 8.1 Essential Documentation

**Module Documentation**:
- Module 10: `magpie-agent/modules/module_10.md` (Land allocation)
- Module 11: `magpie-agent/modules/module_11.md` (Costs)
- Module 17: `magpie-agent/modules/module_17.md` (Production)
- Module 56: `magpie-agent/modules/module_56.md` (GHG policy)

**Cross-Module Documentation**:
- Land Balance: `magpie-agent/cross_module/land_balance_conservation.md`
- Water Balance: `magpie-agent/cross_module/water_balance_conservation.md`
- Carbon Balance: `magpie-agent/cross_module/carbon_balance_conservation.md`
- Food Balance: `magpie-agent/cross_module/nitrogen_food_balance.md`

**Dependency Analysis**:
- Phase 2: `magpie-agent/core_docs/Module_Dependencies.md` (Complete dependency graph)

### 8.2 Testing Tools

**R Package**: `magpie4` (output analysis)
```r
library(magpie4)
?land          # Land use analysis
?production    # Production outputs
?costs         # Cost breakdown
?emissions     # Emission accounting
```

**GAMS Tools**:
- `gamspy` - Python interface to GAMS
- `gdx2sqlite` - Convert GDX to SQLite for analysis
- `gdxdiff` - Compare GDX files (baseline vs. modified)

### 8.3 Getting Help

**Internal Resources**:
1. Check `CLAUDE.md` (project instructions)
2. Search `magpie-agent/` documentation
3. Review module code with line numbers cited in docs

**External Resources**:
1. MAgPIE GitHub: https://github.com/magpiemodel/magpie
2. MAgPIE Documentation: https://rse.pik-potsdam.de/doc/magpie/
3. Model comparison: https://tntcat.iiasa.ac.at/ (IIASA scenario database)

**Development Team**:
- Create GitHub issue for bugs
- Tag module maintainer for questions
- Provide minimal reproducible example

---

## Appendix A: Module Centrality Rankings (Full List)

| Rank | Module | Connections | Provides To | Depends On | Risk Level |
|------|--------|-------------|-------------|------------|------------|
| 1 | 11_costs | 28 | 1 | 27 | 🔴 CRITICAL |
| 2 | 10_land | 17 | 15 | 2 | 🔴 CRITICAL |
| 3 | 56_ghg_policy | 16 | 13 | 3 | 🔴 HIGH |
| 4 | 32_forestry | 16 | 5 | 11 | 🟠 HIGH |
| 5 | 30_croparea | 15 | 9 | 6 | 🟠 HIGH |
| 6 | 70_livestock | 14 | 7 | 7 | 🟠 HIGH |
| 7 | 17_production | 14 | 13 | 1 | 🔴 HIGH |
| 8 | 09_drivers | 14 | 14 | 0 | 🟡 MEDIUM |
| 9 | 29_cropland | 13 | 6 | 7 | 🟠 MEDIUM |
| 10 | 35_natveg | 12 | 5 | 7 | 🟠 MEDIUM |

**Source**: Module_Dependencies.md (lines 29-40)

---

## Appendix B: Interface Variable Reference

### Most Critical Variables (11+ Consumers)

| Variable | Consumers | Producer | Type | Description |
|----------|-----------|----------|------|-------------|
| `vm_land(j,land)` | 11 | 10_land | vm_ | Land allocation by type |
| `im_pop_iso(t,iso)` | 11 | 09_drivers | im_ | Population by country |
| `pm_interest(t,i)` | 10 | 12_interest_rate | pm_ | Interest rates for NPV |
| `vm_prod(j,k)` | 9 | 17_production | vm_ | Cell-level production |
| `vm_prod_reg(i,k)` | 9 | 17_production | vm_ | Regional production |
| `vm_area(j,kcr,w)` | 9 | 30_croparea | vm_ | Cropland area by irrigation |

**Source**: Module_Dependencies.md (lines 46-59)

---

**Document Status**: ✅ Complete
**Verified Against**: module_10.md, module_11.md, module_17.md, module_56.md, Module_Dependencies.md
**Created**: 2025-10-22
**Validation**: All equation references, line numbers, and dependency counts verified against source

---

**REMEMBER**: These 4 modules are the **structural backbone** of MAgPIE. Treat modifications with extreme care. When in doubt, **test more, change less**.
