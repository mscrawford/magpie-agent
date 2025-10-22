# Water Balance Conservation Law in MAgPIE

**Status**: ✅ Complete
**Created**: 2025-10-22
**Modules Covered**: 42, 43
**Conservation Law Type**: Inequality constraint (soft via infeasibility buffer)

---

## 1. Overview

The **Water Balance Conservation Law** ensures that **total water withdrawals do not exceed available renewable water resources** in every spatial unit (cell) during each growing period. Unlike land balance (strict equality), water balance is an **inequality constraint** that allows surplus water but prevents over-extraction of renewable resources.

**Source**: Module 43 (Water Availability), equation q43_water (`modules/43_water_availability/total_water_aug13/equations.gms:10-11`)

**Mathematical Statement**:
```
∀ j ∈ Cells, ∀ t ∈ Time:
  Σ(water demands) ≤ Σ(water sources)
```

**Code Implementation**:
```gams
q43_water(j2) ..
  sum(wat_dem, vm_watdem(wat_dem,j2)) =l=
  sum(wat_src, v43_watavail(wat_src,j2));
```

**Translation**: In every cell j, total water withdrawals across all demand sectors must be less than or equal to total water available from all sources.

---

## 2. Water Demand Sectors (5 Total)

**Verified**: `modules/43_water_availability/total_water_aug13/equations.gms:17-18`

MAgPIE distinguishes 5 water demand sectors, calculated by Module 42:

### 2.1 Endogenous Demand: Agriculture

| Sector | Code | Module | Status | Calculation |
|--------|------|--------|--------|-------------|
| **Agriculture** | `agriculture` | 42 | Endogenous | Optimized based on irrigation area and livestock production |

**Calculation** (Module 42, `equations.gms:10-14`):
```gams
vm_watdem("agriculture",j) * v42_irrig_eff(j) =e=
  sum(kcr, vm_area(j,kcr,"irrigated") * ic42_wat_req_k(j,kcr))
  + sum(kli, vm_prod(j,kli) * ic42_wat_req_k(j,kli) * v42_irrig_eff(j));
```

**Components**:
- **Crop irrigation**: Irrigated area × water requirement per ha (from LPJmL)
- **Livestock water**: Production × water requirement per ton (from FAO)
- **Irrigation efficiency**: Accounts for conveyance losses (66% default)

**Key Point**: Agricultural demand is **optimized** - responds to water scarcity via shadow prices

---

### 2.2 Exogenous Demands: Non-Agricultural Sectors

| Sector | Code | Module | Status | Data Source |
|--------|------|--------|--------|-------------|
| **Manufacturing** | `manufacturing` | 42 | Exogenous | WATERGAP model (SSP scenarios) |
| **Electricity** | `electricity` | 42 | Exogenous | WATERGAP model (SSP scenarios) |
| **Domestic** | `domestic` | 42 | Exogenous | WATERGAP model (SSP scenarios) |

**Fixed Values** (Module 42, `presolve.gms:40-54`):
```gams
vm_watdem.fx(watdem_ineldo,j) = f42_watdem_ineldo(t,j,ssp_scenario,watdem_ineldo,"withdrawal");
```

**Key Point**: These sectors do **not respond** to water scarcity - demands fixed by SSP scenario

**SSP Scenarios** (Module 42, `input.gms:9`):
- SSP1: Low demand (sustainability)
- SSP2: Medium demand (middle of the road) - DEFAULT
- SSP3: High demand (fragmentation)

---

### 2.3 Exogenous Demands: Environmental Flows

| Sector | Code | Module | Status | Purpose |
|--------|------|--------|--------|---------|
| **Ecosystem** | `ecosystem` | 42 | Exogenous | Maintain aquatic ecosystem health |

**Calculation** (Module 42, `presolve.gms:87-88`):
```gams
vm_watdem.fx("ecosystem",j) =
  sum(cell(i,j), i42_env_flows_base(t,j) * (1 - ic42_env_flow_policy(i))
                + i42_env_flows(t,j) * ic42_env_flow_policy(i));
```

**Three Scenarios** (Module 42, `input.gms:22`):
- **Scenario 0**: No environmental flows
- **Scenario 1**: Fixed fraction (20% of available water, uniform)
- **Scenario 2**: LPJmL Smakhtin algorithm (cell-specific) - DEFAULT

**Environmental Flow Protection (EFP) Policy** (Module 42, `input.gms:35-36`):
- Linear ramp-up from 2025 (0%) to 2040 (100%)
- Country-specific targeting (default: all 195 countries)
- Development-state dependent: HIC only, or all countries, or none

**Key Point**: Environmental flows **compete** with human water use for limited renewable water

---

## 3. Water Supply Sources (4 Potential)

**Verified**: `modules/43_water_availability/total_water_aug13/equations.gms:19-20`

MAgPIE defines 4 potential water sources, but **only surface water is active** in current implementation:

### 3.1 Active Source: Surface Water

| Source | Code | Module | Status | Data Source |
|--------|------|--------|--------|-------------|
| **Surface Water** | `surface` | 43 | Active | LPJmL runoff during growing period |

**Calculation** (Module 43, `preloop.gms:8`):
```gams
im_wat_avail(t,"surface",j) = f43_wat_avail(t,j);
```

**LPJmL Processing** (Module 43, `realization.gms:9-42`):
1. **Basin runoff**: Total runoff from LPJmL climate simulations
2. **Growing period restriction**: Only runoff during crop growing period available
3. **Dam exception**: Cells with dams → full annual runoff (not just growing period)
4. **Cell distribution**: Basin runoff distributed using LPJmL discharge as weight

**Growing Period Examples** (illustrative):
- Temperate regions: ~40-50% of annual runoff (150-180 day growing season)
- Tropical regions: ~55-80% of annual runoff (200-300 day growing season)
- With dams: 100% of annual runoff (storage captures off-season flows)

**Climate Scenarios** (Module 43, `input.gms:9-12`):
- `cc` (climate change): Time-varying runoff from LPJmL projections - DEFAULT
- `nocc`: Fixed at 1995 levels (no climate change)
- `nocc_hist`: Historical until sm_fix_cc, then frozen

---

### 3.2 Inactive Sources (Set to Zero)

| Source | Code | Module | Status | Reason |
|--------|------|--------|--------|--------|
| **Groundwater (fossil)** | `ground` | 43 | Inactive* | Used only for infeasibility buffer |
| **Renewable groundwater** | `ren_ground` | 43 | Inactive | Not modeled |
| **Technical** | `technical` | 43 | Inactive | Desalination not modeled |

**Implementation** (Module 43, `preloop.gms:10-12`):
```gams
im_wat_avail(t,"ground",j) = 0;
im_wat_avail(t,"ren_ground",j) = 0;
im_wat_avail(t,"technical",j) = 0;
```

***Exception**: Fossil groundwater (`ground`) activated only when exogenous demands exceed surface water (see Section 5)

---

## 4. Core Water Balance Constraint

### 4.1 Mathematical Formulation

**Equation**: q43_water (Module 43, `equations.gms:10-11`)

```gams
q43_water(j2) ..
  sum(wat_dem, vm_watdem(wat_dem,j2)) =l=
  sum(wat_src, v43_watavail(wat_src,j2));
```

**Components**:
- **LHS**: `sum(wat_dem, vm_watdem(wat_dem,j2))` - Total water withdrawals in cell j
- **RHS**: `sum(wat_src, v43_watavail(wat_src,j2))` - Total water available in cell j
- **Operator**: `=l=` - Inequality (less than or equal)

**Expanded Form**:
```
vm_watdem(j,"agriculture") + vm_watdem(j,"manufacturing") +
vm_watdem(j,"electricity") + vm_watdem(j,"domestic") + vm_watdem(j,"ecosystem")
≤
v43_watavail(j,"surface") + v43_watavail(j,"ground") +
v43_watavail(j,"ren_ground") + v43_watavail(j,"technical")
```

**In Practice** (with inactive sources):
```
vm_watdem(j,"agriculture") + vm_watdem(j,"manufacturing") +
vm_watdem(j,"electricity") + vm_watdem(j,"domestic") + vm_watdem(j,"ecosystem")
≤
v43_watavail(j,"surface")  [+ buffer if needed]
```

---

### 4.2 Inequality vs. Equality

**Key Difference from Land Balance**:

| Conservation Law | Constraint Type | Reason |
|------------------|-----------------|--------|
| **Land Balance** | Equality (=e=) | Land is stock - cannot have surplus or deficit |
| **Water Balance** | Inequality (=l=) | Water is flow - can have surplus (unused water flows downstream) |

**Implications of Inequality**:
1. **Surplus water allowed**: Not all renewable water must be used
2. **Slack variable**: `oq43_water.level` = available - withdrawals (≥ 0)
3. **Shadow price only when binding**: `oq43_water.marginal` > 0 only if constraint tight

**Interpretation**:
- **Binding constraint** (slack = 0): Water-scarce region, withdrawals = availability
- **Slack > 0**: Water-abundant region, surplus flows unused (e.g., to ocean or downstream)

---

### 4.3 Spatial Resolution

**Applied at Cell Level** (Module 43, `equations.gms:10-11`):
- Each of ~200 MAgPIE cells has independent water balance
- No inter-cell water trading or transfers
- Each cell must balance its own water budget

**Implication**: Water-scarce cell cannot import water from water-abundant neighbor

**Limitation**: Does not model:
- River basin agreements (e.g., Nile Basin Initiative)
- Inter-basin transfers (e.g., California State Water Project)
- Water markets (e.g., Australia Murray-Darling Basin)

---

## 5. Infeasibility Buffer Mechanism

### 5.1 The Problem

**Situation**: Exogenous non-agricultural demands (manufacturing, electricity, domestic, ecosystem) may exceed available surface water.

**Risk**: Model infeasibility - optimization cannot find solution satisfying all constraints.

**Example** (illustrative):
- Available surface water: 100 mio. m³
- Manufacturing demand (exogenous, fixed): 50 mio. m³
- Electricity demand (exogenous, fixed): 30 mio. m³
- Domestic demand (exogenous, fixed): 25 mio. m³
- Ecosystem demand (exogenous, fixed): 20 mio. m³
- **Total exogenous: 125 mio. m³ > 100 mio. m³ available** → INFEASIBLE

*Note: These are made-up numbers for illustration.*

---

### 5.2 The Solution: Groundwater Buffer

**Automatic Activation** (Module 43, `presolve.gms:14-16`):

```gams
v43_watavail.fx("ground",j) = v43_watavail.up("ground",j)
  + (((sum(watdem_exo, vm_watdem.lo(watdem_exo,j))
      - sum(wat_src, v43_watavail.up(wat_src,j))) * 1.01))
  $(sum(watdem_exo, vm_watdem.lo(watdem_exo,j))
    - sum(wat_src, v43_watavail.up(wat_src,j)) > 0);
```

**Breaking Down the Logic**:

1. **Calculate shortfall**:
   ```
   Shortfall = Min. exogenous demand - Total available water
   ```

2. **If shortfall > 0**:
   ```
   Add shortfall × 1.01 to groundwater availability
   ```
   - Factor 1.01 = 1% safety margin for numerical stability

3. **Result**: Groundwater buffer exactly covers the shortfall, making model feasible

**Applied only to**:
- `watdem_exo`: Manufacturing, electricity, domestic, ecosystem
- **NOT agriculture**: Agricultural demand must stay within renewable water

---

### 5.3 Interpretation and Implications

**What the buffer represents**:
- **Unsustainable groundwater mining** (fossil aquifer depletion)
- **Zero cost**: No penalty for using buffer groundwater
- **Infinite supply** (for exogenous demands): Always expands to meet shortfall

**Asymmetric treatment**:

| Sector | Status | Water Constraint |
|--------|--------|------------------|
| Agriculture | Endogenous | Must stay within renewable water (surface) |
| Manufacturing | Exogenous | Can use buffer if surface insufficient |
| Electricity | Exogenous | Can use buffer if surface insufficient |
| Domestic | Exogenous | Can use buffer if surface insufficient |
| Ecosystem | Exogenous | Can use buffer if surface insufficient |

**Implication**:
- Agriculture bears full burden of water scarcity
- Non-agricultural sectors always meet demands (via unsustainable extraction)
- Model cannot explore trade-offs between sectors when water scarce

**Justification** (Module 43, `realization.gms:40-42`):
- Non-agricultural sectors typically have higher economic value
- Politically difficult to cut manufacturing/domestic water
- Agricultural water use is more elastic (can switch to rainfed, import food)

---

## 6. Module Interactions for Water Balance

### 6.1 Module 42 (Water Demand) - Calculates Demands

**Role**: Determines water withdrawals for all 5 sectors

**Key Equations**:

**Agricultural Water** (`modules/42_water_demand/all_sectors_aug13/equations.gms:10-14`):
```gams
vm_watdem("agriculture",j) * v42_irrig_eff(j) =e=
  sum(kcr, vm_area(j,kcr,"irrigated") * ic42_wat_req_k(j,kcr))
  + sum(kli, vm_prod(j,kli) * ic42_wat_req_k(j,kli) * v42_irrig_eff(j));
```

**Pumping Costs** (`modules/42_water_demand/all_sectors_aug13/equations.gms:16-17`):
```gams
vm_water_cost(i) =e= sum(cell(i,j), vm_watdem("agriculture",j)) * ic42_pumping_cost(i);
```

**Provides to Module 43**:
- `vm_watdem(wat_dem,j)`: Water demand by sector and cell

**Receives from Module 43**:
- Shadow prices from q43_water constraint → feed back to irrigation decisions

**Irrigation Efficiency** (`modules/42_water_demand/all_sectors_aug13/presolve.gms:12-22`):
- Default: GDP-based sigmoidal function (richer regions more efficient)
- Range: ~50% (low GDP) to ~90% (high GDP)
- Affects agricultural water demand (higher efficiency → lower withdrawals)

---

### 6.2 Module 43 (Water Availability) - Enforces Constraint

**Role**: Provides water supply, enforces balance constraint

**Key Equation** (`modules/43_water_availability/total_water_aug13/equations.gms:10-11`):
```gams
q43_water(j) ..
  sum(wat_dem, vm_watdem(wat_dem,j)) =l= sum(wat_src, v43_watavail(wat_src,j));
```

**Provides to Module 42**:
- `im_wat_avail(t,wat_src,j)`: Available water for environmental flow calculations
- Shadow prices: Water scarcity signals

**Receives from Module 42**:
- `vm_watdem(wat_dem,j)`: Water demands (all sectors)

**Water Availability Fixation** (`modules/43_water_availability/total_water_aug13/presolve.gms:8-11`):
```gams
v43_watavail.fx("surface",j) = im_wat_avail(t,"surface",j);
```

**Why variable if fixed?**
- To provide shadow prices (marginal values)
- Shadow price = economic value of additional 1 m³ water in cell j
- GAMS only computes marginals for variables, not parameters

---

### 6.3 Module 30 (Croparea) - Responds to Water Scarcity

**Role**: Allocates crops between rainfed and irrigated systems

**Water Scarcity Response**:
1. Module 43 water constraint binds → high shadow price
2. Shadow price increases cost of irrigation
3. Module 30 shifts crops from irrigated to rainfed (if yields allow)
4. Reduces agricultural water demand → relieves constraint

**Does NOT directly constrain Module 30**:
- Module 43 constraint applies to Module 42 (water demand)
- Module 30 responds indirectly via shadow prices in objective function

**Irrigated Area Decision**:
- Depends on: Yield advantage (irrigated vs rainfed), water cost, land availability
- Water-scarce regions: More rainfed production
- Water-abundant regions: More irrigated production

---

### 6.4 Module 41 (Area Equipped for Irrigation - AEI)

**Role**: Determines irrigation infrastructure capacity

**Interaction with Water Balance**:
1. Module 41 invests in AEI based on expected profitability
2. But actual irrigated area (Module 30) cannot exceed AEI
3. If water scarce (Module 43 binding), irrigated area < AEI capacity
4. Result: **Stranded AEI assets** in water-scarce regions

**Known Limitation** (Module 41):
- AEI expansion decisions do not account for future water scarcity
- May over-invest in irrigation infrastructure that cannot be fully utilized
- No feedback from Module 43 water constraint to Module 41 investment

**Implication**: Model may overestimate irrigation expansion in water-stressed regions

---

### 6.5 Module 17 (Production) and Module 70 (Livestock)

**Role**: Calculate production including livestock water demand

**Livestock Water** (Module 42, `equations.gms:14`):
```gams
sum(kli, vm_prod(j,kli) * ic42_wat_req_k(j,kli) * v42_irrig_eff(j))
```

**Components**:
- `vm_prod(j,kli)`: Livestock production from Module 17 (Mt DM/yr)
- `ic42_wat_req_k(j,kli)`: Water requirement per ton (from FAO data)
- Contributes to agricultural water demand

**Feedback**:
- Water scarcity → higher water cost → affects livestock production costs
- May shift livestock to less water-intensive systems or locations

---

## 7. Conservation Law in Practice

### 7.1 Water-Abundant Scenario

**Characteristics**:
- High surface water availability (humid climate, high runoff)
- Low water demand relative to supply

**Behavior**:
- q43_water constraint **not binding** (slack > 0)
- Shadow price = 0 (no scarcity value)
- Surplus water flows unused (to ocean or downstream basin)

**Example** (illustrative):
- Available water: 500 mio. m³
- Agricultural demand: 100 mio. m³
- Manufacturing: 50 mio. m³
- Electricity: 30 mio. m³
- Domestic: 20 mio. m³
- Ecosystem: 100 mio. m³
- **Total demand: 300 mio. m³ << 500 mio. m³**
- **Slack: 200 mio. m³ (surplus)**

*Note: Made-up numbers for illustration.*

**Land-use implications**:
- Irrigation expansion limited by other factors (land availability, crop prices)
- Water scarcity not a constraint on agricultural development

---

### 7.2 Water-Scarce Scenario

**Characteristics**:
- Low surface water availability (arid/semiarid climate)
- High water demand (intensive irrigation agriculture)

**Behavior**:
- q43_water constraint **binding** (slack = 0)
- Shadow price > 0 (high scarcity value)
- All renewable water fully utilized

**Example** (illustrative):
- Available water: 200 mio. m³
- Agricultural demand: 120 mio. m³
- Manufacturing: 30 mio. m³
- Electricity: 20 mio. m³
- Domestic: 15 mio. m³
- Ecosystem: 15 mio. m³
- **Total demand: 200 mio. m³ = 200 mio. m³**
- **Slack: 0 (constraint binding)**
- **Shadow price: High** (e.g., $50-500 per m³ depending on agricultural productivity)

*Note: Made-up numbers for illustration.*

**Land-use implications**:
- Irrigation expansion blocked by water availability
- Module 30 shifts to rainfed production where possible
- Food production may decline or shift to less water-intensive crops
- Food prices increase (scarcity premium)
- May trigger food imports from water-abundant regions

---

### 7.3 Climate Change Scenario

**Mechanism**:
1. LPJmL projects runoff changes under climate scenarios
2. Module 43 updates `f43_wat_avail(t,j)` over time
3. Water availability changes affect q43_water constraint

**Typical Patterns** (from LPJmL literature):
- **Wetter regions**: Increased runoff (e.g., +10-30% in monsoon Asia)
- **Drier regions**: Decreased runoff (e.g., -20-50% in Mediterranean, Middle East)
- **High latitudes**: Increased runoff (glacier/snowmelt changes)
- **Seasonal shifts**: Changed timing (not captured in growing period average)

**Implications**:
- Water-scarce regions face intensifying constraints
- May trigger:
  - Shift from irrigated to rainfed agriculture
  - Crop switching (to less water-intensive crops)
  - Agricultural abandonment (if rainfed also fails)
  - Increased reliance on food imports

**No-climate-change counterfactual** (`c43_watavail_scenario = nocc`):
- Fix water availability at 1995 levels
- Isolates climate change impact on water from other drivers

---

### 7.4 Environmental Flow Protection (EFP) Policy

**Mechanism**:
1. EFP policy ramps up 2025-2040 (linear increase from 0% to 100%)
2. Ecosystem water demand increases over time
3. Less water available for human use (agriculture, manufacturing, etc.)

**Example Timeline** (illustrative):
- 2024: Ecosystem demand = 5% of available water (base protection)
- 2025: Ecosystem demand = 5% (EFP starts but 0% enforcement)
- 2032: Ecosystem demand = ~12% (halfway through ramp-up, assuming 20% target)
- 2040: Ecosystem demand = 20% (full EFP enforcement)
- 2050: Ecosystem demand = 20% (continues)

*Note: Actual values depend on EFP scenario (fraction vs LPJmL) and cell-specific characteristics.*

**Trade-offs**:
- **Environmental benefit**: Protects aquatic ecosystems, fisheries, biodiversity
- **Agricultural cost**: Less water for irrigation → lower yields or area
- **Food security**: May increase food prices, shift production, require imports

**Policy Modes** (Module 42, `input.gms:122`):
- `off`: No EFP (base protection only, 5%)
- `on`: Full EFP (all countries)
- `mixed`: Development-state dependent (high-income countries only)

---

### 7.5 Infeasibility Buffer Activation

**When it activates**:
- Exogenous demands (manufacturing + electricity + domestic + ecosystem) > Surface water

**Example** (illustrative):
- Surface water: 150 mio. m³
- Manufacturing (exogenous): 40 mio. m³
- Electricity (exogenous): 30 mio. m³
- Domestic (exogenous): 30 mio. m³
- Ecosystem (exogenous): 60 mio. m³ (full EFP)
- **Total exogenous: 160 mio. m³ > 150 mio. m³**
- **Shortfall: 10 mio. m³**
- **Buffer activates**: groundwater = 10 × 1.01 = 10.1 mio. m³
- **Result**: Exogenous demands fully met via unsustainable groundwater

*Note: Made-up numbers for illustration.*

**Implications**:
- Model remains feasible (can find solution)
- But represents **unsustainable water use** (fossil aquifer depletion)
- Agricultural water demand must still fit within renewable water (surface only)

**Diagnostic**:
- If `v43_watavail("ground",j) > 0` in output → buffer activated
- Indicates exogenous demands exceed sustainable water supply
- Suggests need for demand reduction or alternative sources (desalination)

---

## 8. Water Balance Verification

### 8.1 Constraint Satisfaction Check

**Equation**: For every cell j and timestep t:
```
vm_watdem(j,"agriculture") + vm_watdem(j,"manufacturing") +
vm_watdem(j,"electricity") + vm_watdem(j,"domestic") + vm_watdem(j,"ecosystem")
≤
v43_watavail(j,"surface") + v43_watavail(j,"ground") +
v43_watavail(j,"ren_ground") + v43_watavail(j,"technical")
```

**R Code Example**:
```r
library(magpie4)

# Read water demand (all sectors)
watdem <- water_demand(gdx, level="cell", water_source=FALSE)
total_demand <- dimSums(watdem, dim=3.1)  # Sum over sectors

# Read water availability (all sources)
watavail <- water_avail(gdx, level="cell")
total_avail <- dimSums(watavail, dim=3.1)  # Sum over sources

# Check constraint satisfaction
violation <- total_demand - total_avail
max_violation <- max(violation)

print(paste("Maximum constraint violation:", max_violation, "mio. m³"))

# Should be ≤ 0 (demand ≤ supply)
# Small positive values (< 0.01 mio. m³) = numerical tolerance
stopifnot(max_violation < 0.01)
```

**Expected Result**: `max_violation ≤ 0` (or tiny positive value < 0.01 mio. m³ for numerical tolerance)

**If Violated** (max_violation >> 0):
- Model bug in Module 42 or 43
- Infeasibility buffer not working correctly
- Check solver status (may have failed to converge)

---

### 8.2 Slack Variable Check

**Slack** = Available water - Total demand (≥ 0 if constraint satisfied)

**R Code**:
```r
# Calculate slack
slack <- total_avail - total_demand

# Positive slack = surplus water (abundant)
# Zero slack = binding constraint (scarce)
# Negative slack = violation (should not occur!)

summary(slack)

# Identify water-scarce cells (slack near zero)
scarce_cells <- which(slack < 1)  # < 1 mio. m³ slack
print(paste("Number of water-scarce cells:", length(scarce_cells)))

# Identify water-abundant cells (large slack)
abundant_cells <- which(slack > 100)  # > 100 mio. m³ surplus
print(paste("Number of water-abundant cells:", length(abundant_cells)))
```

---

### 8.3 Shadow Price Interpretation

**Shadow Price** = Economic value of 1 additional m³ water

**R Code**:
```r
# Read shadow prices from water constraint
shadow_price <- readGDX(gdx, "oq43_water", select=list(type="marginal"), field="level")

# High shadow price → water is scarce (binding constraint)
# Zero shadow price → water abundant (slack > 0)

summary(shadow_price)

# Cells with high water scarcity value
high_value_water <- which(shadow_price > 0.01)  # >$0.01/m³
print(paste("Cells with scarce water:", length(high_value_water)))

# Visualize
plot(as.vector(shadow_price), ylab="Shadow Price ($/m³)", main="Water Scarcity by Cell")
```

**Typical Values** (illustrative):
- Abundant water: Shadow price = $0/m³
- Moderate scarcity: Shadow price = $0.01-0.10/m³
- High scarcity: Shadow price = $0.10-1.00/m³
- Extreme scarcity: Shadow price > $1/m³

*Note: Actual values depend on agricultural productivity, food prices, trade costs.*

---

### 8.4 Growing Period Caveat

**Important**: Water balance applies to **growing period only**, not full year

**Check**:
```r
# Water values in MAgPIE are growing-period withdrawals
# NOT annual withdrawals

# To get full-year equivalent (approximate):
# - Temperate regions: multiply by ~2-2.5
# - Tropical regions: multiply by ~1.25-1.8
# - Regions with dams: multiply by 1 (already annual)

# This is rough approximation! Actual growing period varies by cell and crop.
```

**Implication**: Cannot directly compare MAgPIE water withdrawals to annual statistics without accounting for growing period fraction

---

## 9. Violations and Diagnostics

### 9.1 Common Causes of Issues

**1. Infeasibility (No Solution Found)**:
```
Exogenous demands too high + Agricultural demands + No groundwater buffer
```
- **Check**: Sum of exogenous demands vs surface water
- **Solution**: Reduce demands, increase water availability, or enable buffer

**2. Unrealistic Groundwater Use**:
```
v43_watavail("ground",j) >> 0 for many cells
```
- **Indicates**: Exogenous demands exceed renewable water in many regions
- **Implications**: Unsustainable scenario (fossil aquifer depletion)
- **Solutions**: Reduce exogenous demands, increase efficiency, explore desalination

**3. Agriculture Water-Constrained, Manufacturing Not**:
```
Agricultural production lower than expected
Non-agricultural demands fully met
```
- **Cause**: Asymmetric treatment (agriculture must stay within renewable, others buffered)
- **Diagnostic**: Check if agriculture shadow price high but manufacturing unconstrained
- **Implication**: All water scarcity burden on agriculture

**4. Stranded AEI in Water-Scarce Regions**:
```
vm_AEI(j) high but vm_area(j,kcr,"irrigated") << vm_AEI(j)
```
- **Cause**: Module 41 invested in irrigation without accounting for water scarcity
- **Diagnostic**: Compare AEI capacity to actual irrigated area
- **Implication**: Over-investment in irrigation infrastructure

---

### 9.2 Diagnostic Checks

**Check 1: Water Constraint Binding**
```r
# For each cell, check if constraint binding
binding <- (slack < 0.1)  # < 0.1 mio. m³ slack
fraction_binding <- sum(binding) / length(slack)
print(paste("Fraction of cells water-scarce:", round(fraction_binding*100, 1), "%"))
```

**Check 2: Groundwater Buffer Activation**
```r
# Check if groundwater buffer used
ground_use <- readGDX(gdx, "ov43_watavail", select=list(type="level"))
ground_use <- ground_use[,,"ground",]
cells_with_buffer <- sum(ground_use > 0.01)
print(paste("Cells using groundwater buffer:", cells_with_buffer))
```

**Check 3: Exogenous Demand Feasibility**
```r
# Check if exogenous demands exceed surface water
exo_demand <- dimSums(watdem[,,c("manufacturing","electricity","domestic","ecosystem")], dim=3.1)
surface_avail <- watavail[,,"surface",]
shortfall <- exo_demand - surface_avail
cells_infeasible <- sum(shortfall > 0)
print(paste("Cells where exogenous demands exceed surface water:", cells_infeasible))
```

**Check 4: Agricultural vs Non-Agricultural Water**
```r
# Compare agricultural to non-agricultural water use
agri_water <- watdem[,,"agriculture",]
nonagri_water <- dimSums(watdem[,,c("manufacturing","electricity","domestic")], dim=3.1)
agri_share <- agri_water / (agri_water + nonagri_water)
summary(agri_share)
```

---

## 10. Implications for Model Modifications

### 10.1 High-Risk Modifications

**⚠️ DANGER: Changing Module 43 water constraint**
- Water balance is critical for model feasibility
- Removing or relaxing constraint creates unrealistic water use
- **Always verify**: Total demand ≤ total supply after any change

**⚠️ DANGER: Modifying exogenous demands without checking availability**
- Increasing manufacturing/electricity/domestic demands may trigger buffer
- Represents unsustainable groundwater mining
- **Check**: Will new demands exceed surface water? If so, acknowledge unsustainability

**⚠️ DANGER: Changing infeasibility buffer**
- Buffer prevents model crashes when exogenous demands too high
- Removing buffer without reducing demands → model infeasible
- **Test**: Run without buffer to check if demands sustainable

---

### 10.2 Safe Modifications

**✓ SAFE: Adjusting irrigation efficiency**
- Module 42, `s42_irrig_eff_scenario` or `s42_irrigation_efficiency`
- Higher efficiency → lower water demand for same irrigation
- Reduces water stress, does not affect balance constraint itself

**✓ SAFE: Changing climate scenario**
- Module 43, `c43_watavail_scenario` (cc/nocc/nocc_hist)
- Affects water supply, but constraint remains intact
- May affect feasibility (less water → more binding constraint)

**✓ SAFE: Environmental flow policy**
- Module 42, `c42_env_flow_policy` and `s42_efp_startyear/targetyear`
- Changes ecosystem demand (exogenous)
- May trigger trade-offs but does not break water balance

**✓ SAFE: Pumping costs**
- Module 42, `s42_pumping` and `s42_multiplier`
- Affects agricultural production costs, not water balance
- May reduce irrigation (higher cost) but constraint still satisfied

---

### 10.3 Testing Protocol After Modifications

**Step 1**: Run scenario with modified settings

**Step 2**: Check water balance
```r
watdem <- water_demand(gdx, level="cell", water_source=FALSE)
watavail <- water_avail(gdx, level="cell")
total_demand <- dimSums(watdem, dim=3.1)
total_avail <- dimSums(watavail, dim=3.1)
violation <- total_demand - total_avail
stopifnot(max(violation) < 0.01)
```

**Step 3**: Check groundwater buffer use
```r
ground_use <- readGDX(gdx, "ov43_watavail", select=list(type="level"))[,,"ground",]
if(sum(ground_use > 0.01) > 0) {
  warning("Groundwater buffer activated - unsustainable water use!")
}
```

**Step 4**: Check shadow prices
```r
shadow_price <- readGDX(gdx, "oq43_water", select=list(type="marginal"), field="level")
plot(as.vector(shadow_price))  # Should show reasonable distribution
```

**Step 5**: Compare to baseline
```r
# Load baseline run
baseline_demand <- readRDS("baseline_water_demand.rds")
diff_demand <- total_demand - baseline_demand
plot(diff_demand, main="Change in Water Demand vs Baseline")
```

---

## 11. Summary

### 11.1 Key Principles

1. **Renewable Resource Balance**: Water withdrawals ≤ renewable water availability
2. **Inequality Constraint**: Unlike land (equality), water can have surplus (flows unused)
3. **Cell-Level Enforcement**: Each cell has independent water budget (no inter-cell trading)
4. **Growing Period Only**: Balance applies to growing period, not full year
5. **Infeasibility Buffer**: Exogenous demands can trigger unsustainable groundwater use

### 11.2 Critical Equations

**Water Balance** (Module 43, equations.gms:10-11):
```
Σ(demand sectors) Water Withdrawals ≤ Σ(water sources) Available Water
```

**Agricultural Demand** (Module 42, equations.gms:10-14):
```
Agricultural Water × Efficiency = Crop Irrigation + Livestock Water
```

**Infeasibility Buffer** (Module 43, presolve.gms:14-16):
```
IF Exogenous Demands > Surface Water
THEN Groundwater Buffer = Shortfall × 1.01
```

### 11.3 Module Roles

| Module | Role | Key Variables |
|--------|------|---------------|
| 42 | Calculates water demands (5 sectors) | vm_watdem(wat_dem,j) |
| 43 | Provides water supply, enforces constraint | v43_watavail(wat_src,j), q43_water |
| 30 | Responds to water scarcity (rainfed vs irrigated) | vm_area(j,kcr,w) |
| 41 | Irrigation infrastructure (may be stranded if water scarce) | vm_AEI(j) |
| 17, 70 | Livestock production (contributes to agricultural demand) | vm_prod(j,kli) |

### 11.4 Key Differences from Land Balance

| Feature | Land Balance | Water Balance |
|---------|--------------|---------------|
| **Constraint Type** | Equality (=e=) | Inequality (=l=) |
| **Resource Type** | Stock (finite, conserved) | Flow (renewable each period) |
| **Surplus Allowed?** | No (must sum to constant) | Yes (unused water flows away) |
| **Temporal Scope** | All year | Growing period only |
| **Infeasibility Response** | Model fails | Buffer activates (unsustainable extraction) |
| **Sectors** | 7 land types (all endogenous except urban) | 5 water sectors (only agriculture endogenous) |

### 11.5 Practical Implications

**For Users**:
- Water balance satisfied if model solves (constraint enforced)
- Surplus water common in humid regions (slack > 0)
- Shadow prices indicate water scarcity value
- Groundwater buffer use indicates unsustainable water use

**For Developers**:
- Module 43 constraint is critical for feasibility
- Exogenous demands must be checked against surface water availability
- Infeasibility buffer prevents crashes but represents unrealistic extraction
- Agricultural water is the only elastic demand (responds to scarcity)

### 11.6 Verification Checklist

- [ ] Total water demand ≤ total water available (all cells, all time)
- [ ] Shadow prices reasonable (high where scarce, zero where abundant)
- [ ] Groundwater buffer minimal (ideally zero, or acknowledged as unsustainable)
- [ ] Agricultural water adapts to scarcity (shift to rainfed in scarce regions)
- [ ] Growing period fraction accounted for when comparing to annual data

---

## References

**Module Documentation**:
- Module 42: `magpie-agent/modules/module_42.md`
- Module 43: `magpie-agent/modules/module_43.md`

**Core Documentation**:
- Phase 1: Core Architecture (`magpie-agent/core_docs/Phase1_Core_Architecture.md`)
- Phase 2: Module Dependencies (`magpie-agent/core_docs/Phase2_Module_Dependencies.md`)

**Source Code**:
- Module 42 equations: `modules/42_water_demand/all_sectors_aug13/equations.gms:10-17`
- Module 43 equations: `modules/43_water_availability/total_water_aug13/equations.gms:10-11`
- Module 43 buffer: `modules/43_water_availability/total_water_aug13/presolve.gms:14-16`

**External References**:
- Bondeau et al. (2007): LPJmL model and runoff calculations
- Biemans et al. (2011): Dam data for water storage
- Smakhtin et al. (2004): Environmental flow requirements algorithm

---

**Document Status**: ✅ Complete
**Verified Against**: MAgPIE 4.x source code and module documentation
**Created**: 2025-10-22
**Last Updated**: 2025-10-22
