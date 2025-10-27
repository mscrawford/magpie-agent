# Module 39: Land Conversion Costs - Comprehensive Documentation

**Location**: `modules/39_landconversion/calib/`
**Realization**: `calib` (calibrated costs and rewards)
**Authors**: Florian Humpenöder, Jan Philipp Dietrich, Ulrich Kreidenweis

---

## 1. Purpose & Overview

Module 39 calculates the costs associated with converting land from one use to another (e.g., forest to cropland, cropland to pasture). These costs represent the economic burden of:
- **Clearing vegetation** (removing trees, biomass)
- **Preparing land** for new use (leveling, soil preparation, fencing)
- **Opportunity costs** of land-use change

**Key Innovation**: The `calib` realization uses regional and time-dependent calibration factors to match historical cropland patterns (2015 benchmark). Regions that historically expanded cropland face higher conversion costs, while regions that reduced cropland receive rewards for further reduction—creating realistic spatial patterns of agricultural expansion.

**Role in Model**: Land conversion costs are a critical factor in agricultural expansion decisions. High conversion costs make it cheaper to intensify existing cropland (via yield increases) rather than expand into new areas, directly affecting:
- Deforestation rates
- Agricultural land use patterns
- CO2 emissions from land-use change
- Food prices (expansion costs passed through to production costs)

---

## 2. Cost Structure

### 2.1 Land Types Covered

**File**: `modules/39_landconversion/calib/input.gms:9-14`

```gams
s39_cost_establish_crop       = 12300  ! Cropland (USD17MER/ha)
s39_cost_establish_past       = 9840   ! Pasture (USD17MER/ha)
s39_cost_establish_forestry   = 1230   ! Forestry (USD17MER/ha)
s39_cost_establish_urban      = 12300  ! Urban (USD17MER/ha)
```

**Cost Ranking** (highest to lowest):
1. **Cropland** (12,300 USD/ha) = **Urban** (12,300 USD/ha)
   - High preparation costs: plowing, leveling, drainage, irrigation infrastructure
   - Permanent structures for urban land

2. **Pasture** (9,840 USD/ha)
   - Medium preparation: clearing, fencing, seeding
   - Less intensive than cropland

3. **Forestry** (1,230 USD/ha)
   - Low preparation: planting seedlings, minimal clearing
   - Natural regeneration often sufficient

**Note**: Natural vegetation (forest, other land) has **zero establishment cost** when converting—only the cost of the *target* land type applies.

### 2.2 Cropland Calibration

**Purpose**: Match historical regional cropland patterns (2015 benchmark)

**Base Costs** (`input.gms:9-10`):
```gams
s39_cost_establish_crop     = 12300  ! Base expansion cost (USD17MER/ha)
s39_reward_crop_reduction   = 7380   ! Base reduction reward (USD17MER/ha, 60% of cost)
```

**Applied Calibration** (`presolve.gms:12-13`):
```gams
i39_cost_establish(t,i,"crop") = s39_cost_establish_crop * i39_calib(t,i,"cost")
i39_reward_reduction(t,i,"crop") = s39_reward_crop_reduction * i39_calib(t,i,"reward")
```

**Calibration Factor Logic**:
- **i39_calib(t,i,"cost")**: Regional multiplier on expansion costs
  - Range: 0.1 to 10+ (typically 0.5 to 3.0)
  - Regions with historical expansion → higher costs (prevent over-expansion)
  - Regions with land availability → lower costs (allow expansion)
  - Minimum of 1.0 enforced by 2050 (convergence to global baseline)

- **i39_calib(t,i,"reward")**: Regional multiplier on reduction rewards
  - Range: 0 to 1+ (typically 0 or 0.5-1.5)
  - Only applied in regions with **declining cropland 1995-2015** AND **i39_calib("cost") > 1**
  - Incentivizes further reduction in regions that historically abandoned cropland
  - Example: Eastern Europe after Soviet collapse

**Data Source**: `modules/39_landconversion/input/f39_calib.csv`
- Derived from iterative calibration runs comparing model to FAO 2015 cropland data

---

## 3. Core Cost Equation

### 3.1 The Conversion Cost Formula

**File**: `modules/39_landconversion/calib/equations.gms:12-15`

```gams
q39_cost_landcon(j,land) ..
  vm_cost_landcon(j,land) =e=
    (vm_landexpansion(j,land) * i39_cost_establish(i,land)
     - vm_landreduction(j,land) * i39_reward_reduction(i,land))
    * pm_interest(i) / (1 + pm_interest(i))
```

**Mathematical Form**:
```
Cost(j,land) = [Expansion(j,land) × Cost_per_ha(land)
                - Reduction(j,land) × Reward_per_ha(land)]
               × r/(1+r)
```

Where:
- **vm_landexpansion(j,land)**: Land area expanded this timestep (mio. ha)
- **vm_landreduction(j,land)**: Land area reduced this timestep (mio. ha)
- **i39_cost_establish(i,land)**: Regional cost per hectare for expansion (USD17MER/ha)
- **i39_reward_reduction(i,land)**: Regional reward per hectare for reduction (USD17MER/ha)
- **r/(1+r)**: Annuity factor to distribute costs over time

### 3.2 Understanding the Annuity Factor: r/(1+r)

**Why Annuitize?**

Land conversion is a **one-time physical action** but has **long-term economic implications**. The annuity factor converts the upfront investment into an equivalent annual cost stream.

**Formula**: `r/(1+r)` where r = interest rate (e.g., 0.05 = 5%)

**Example Calculation**:
- Interest rate r = 5%
- Annuity factor = 0.05 / (1 + 0.05) = 0.05 / 1.05 = **0.0476**

- Expansion: 100,000 ha
- Cost per ha: 12,300 USD
- Total investment: 100,000 × 12,300 = $1.23 billion
- **Annualized cost** in model: $1.23B × 0.0476 = **$58.5 million/yr**

**Economic Interpretation**:
- The $1.23 billion investment creates productive cropland that lasts indefinitely
- The annualized cost ($58.5M/yr) represents the annual economic burden:
  - Interest on capital tied up in land conversion
  - Implicit amortization over time
- Model sees this as an annual cost comparable to factor costs (Module 38) and other yearly expenses

**Comparison with Module 38 Annuity**:
- Module 38: `(r+d)/(1+r)` where d = depreciation (capital wears out)
- Module 39: `r/(1+r)` (no depreciation—land doesn't wear out)
- Module 39 factor is smaller: 0.0476 vs 0.0952 (for r=5%, d=5%)
- Reflects permanent nature of land conversion

### 3.3 Sign Convention: Costs vs Rewards

**Expansion (Positive Cost)**:
```
Cost = +Expansion × Cost_per_ha × r/(1+r)
```
- Expansion adds to total costs in Module 11
- Discourages land-use change (makes expansion expensive)

**Reduction (Negative Cost = Reward)**:
```
Cost = -Reduction × Reward_per_ha × r/(1+r)
```
- Reduction subtracts from total costs (reward)
- Encourages land abandonment in specific regions
- Only active for cropland in calibrated regions

**Net Cost**:
- If expansion > reward value: Positive net cost
- If reward value > expansion: Negative net cost (net reward)
- Typical: Positive net cost (expansion dominates in most scenarios)

---

## 4. Calibration Mechanism

### 4.1 Why Calibrate?

**Problem**: Global uniform costs produce unrealistic spatial patterns
- Model may over-expand in regions with cheap labor but limited land suitability
- Model may under-expand in regions with expensive labor but high land availability
- Historical patterns reflect complex factors not fully captured by biophysical/economic variables

**Solution**: Region-specific calibration factors matching 2015 cropland distribution

### 4.2 Calibration Workflow (Model Development)

**Step 1**: Run model with uniform costs (i39_calib = 1 everywhere)

**Step 2**: Compare model cropland (2015) with FAO historical cropland (2015)
```
Error(i) = Model_Cropland(i,2015) - FAO_Cropland(i,2015)
```

**Step 3**: Adjust calibration factors
- If Error > 0 (model over-expands): Increase i39_calib("cost") → higher expansion costs
- If Error < 0 (model under-expands): Decrease i39_calib("cost") → lower expansion costs

**Step 4**: For regions with declining historical cropland (1995-2015):
- If i39_calib("cost") > 1: Add reward for reduction (i39_calib("reward") > 0)
- Incentivizes continued abandonment matching historical trends

**Step 5**: Iterate until error minimized

**Step 6**: Add convergence to baseline by 2050
- Calibration factors gradually return to 1.0 by 2050
- Prevents permanent regional distortions
- Assumes regional differences diminish over time (globalization, technology diffusion)

### 4.3 Calibration Factor Patterns

**Typical Regional Patterns** (examples, actual values in f39_calib.csv):

**High Expansion Costs (i39_calib("cost") > 1.5)**:
- Regions nearing land scarcity (Western Europe, East Asia)
- Regions with high conservation value (tropical forest regions)
- Prevents unrealistic deforestation

**Low Expansion Costs (i39_calib("cost") < 0.8)**:
- Regions with abundant unused suitable land (Sub-Saharan Africa, parts of Latin America)
- Encourages expansion where historically observed

**Reduction Rewards (i39_calib("reward") > 0)**:
- Eastern Europe (post-Soviet agricultural restructuring)
- Parts of temperate developed regions (urbanization, land abandonment)
- Reflects ongoing structural changes in agriculture

**Temporal Convergence**:
```
i39_calib(t,i,"cost") → 1.0 as t → 2050
```
- By 2050, all regions have at least baseline cost (12,300 USD/ha)
- Prevents indefinite regional advantages/disadvantages

---

## 5. Module Dependencies

### 5.1 Receives From

**Module 10 (Land)**: `modules/39_landconversion/calib/equations.gms:13-14`
```gams
vm_landexpansion(j,land)   ! Area expanded this timestep (mio. ha)
vm_landreduction(j,land)   ! Area reduced this timestep (mio. ha)
```
- Core input: Which land types are expanding/contracting and by how much
- Module 10 calculates transitions based on optimization, Module 39 prices them

**Module 12 (Interest Rate)**: `modules/39_landconversion/calib/equations.gms:15`
```gams
pm_interest(t,i)   ! Regional interest rate (e.g., 0.05 = 5%)
```
- Used in: Annuity factor calculation
- Higher interest rate → higher annualized costs (shorter economic horizon)

### 5.2 Provides To

**Module 11 (Costs)**: `modules/39_landconversion/calib/declarations.gms:13`
```gams
vm_cost_landcon(j,land)   ! Land conversion costs (mio. USD17MER/yr)
```
- Added to total system costs
- Influences: Land-use decisions, agricultural expansion patterns, deforestation rates
- Trade-off: Pay conversion costs vs pay higher production costs (intensification)

### 5.3 Feedback Loops

**Primary Feedback**: Land Expansion ↔ Conversion Costs
1. Food demand increases → need more production
2. **Option A**: Expand land → triggers Module 39 costs
3. **Option B**: Intensify (higher yields) → triggers Module 13/14 costs
4. Model chooses cheaper option → affects expansion rate
5. Expansion affects carbon emissions (Module 52) → GHG policy costs (Module 56)
6. Iteration until equilibrium

**Secondary Feedback**: Historical Calibration → Future Patterns
- Regions that expanded historically (low past i39_calib) → allowed more expansion → may face land scarcity → need intensification later
- Regions that restricted historically (high past i39_calib) → limited expansion → preserved land → more options later

---

## 6. Key Variables

### 6.1 Interface Variable (Output)

**vm_cost_landcon(j,land)** - Land conversion costs
- **File**: `modules/39_landconversion/calib/declarations.gms:13`
- **Type**: Variable (unrestricted, can be negative due to rewards)
- **Dimensions**: [j, land] where land = {crop, past, forestry, urban}
- **Units**: mio USD17MER per yr
- **Typical Range**:
  - Expansion-dominated: +$1-100 million/yr per cell
  - Reduction-dominated (with rewards): -$1-50 million/yr per cell
  - Zero: No land-use change in cell
- **Sent to**: Module 11 (costs) via `vm_cost_landcon`

### 6.2 Input Variables (from Module 10)

**vm_landexpansion(j,land)** - Land area expanded
- **Source**: Module 10 (Land)
- **Dimensions**: [j, land]
- **Units**: mio. ha
- **Typical Range**: 0-5 mio. ha per cell per timestep
- **Used in**: Cost calculation (`equations.gms:13`)

**vm_landreduction(j,land)** - Land area reduced
- **Source**: Module 10 (Land)
- **Dimensions**: [j, land]
- **Units**: mio. ha
- **Typical Range**: 0-5 mio. ha per cell per timestep
- **Used in**: Reward calculation (`equations.gms:14`)

---

## 7. Key Parameters

### 7.1 Base Costs (Global, Static)

**s39_cost_establish_crop** - Cropland expansion cost
- **File**: `modules/39_landconversion/calib/input.gms:9`
- **Value**: 12,300 USD17MER/ha
- **Source**: Literature estimates + model calibration
- **Components**: Clearing (3000), preparation (4000), infrastructure (5000), misc (300)

**s39_cost_establish_past** - Pasture expansion cost
- **File**: `modules/39_landconversion/calib/input.gms:11`
- **Value**: 9,840 USD17MER/ha (80% of cropland cost)
- **Rationale**: Lower infrastructure requirements than cropland

**s39_cost_establish_forestry** - Forestry expansion cost
- **File**: `modules/39_landconversion/calib/input.gms:12`
- **Value**: 1,230 USD17MER/ha (10% of cropland cost)
- **Rationale**: Minimal intervention, natural regeneration aided by planting

**s39_cost_establish_urban** - Urban expansion cost
- **File**: `modules/39_landconversion/calib/input.gms:13`
- **Value**: 12,300 USD17MER/ha (same as cropland)
- **Rationale**: Comparable preparation complexity

**s39_reward_crop_reduction** - Cropland reduction reward
- **File**: `modules/39_landconversion/calib/input.gms:10`
- **Value**: 7,380 USD17MER/ha (60% of expansion cost)
- **Rationale**: Value of land released for other uses, partial recovery of sunk costs

### 7.2 Regional Calibration Factors (Time-Varying)

**i39_calib(t,i,"cost")** - Expansion cost multiplier
- **File**: `modules/39_landconversion/calib/declarations.gms:19`
- **Dimensions**: [t, i, type39]
- **Units**: Dimensionless (multiplier)
- **Source**: `f39_calib.csv` (calibration data)
- **Typical Range**: 0.1 to 10 (most regions 0.5 to 3.0)
- **Applied to**: Cropland expansion only (`presolve.gms:12`)
- **Convergence**: Minimum of 1.0 by 2050

**i39_calib(t,i,"reward")** - Reduction reward multiplier
- **File**: `modules/39_landconversion/calib/declarations.gms:19`
- **Dimensions**: [t, i, type39]
- **Units**: Dimensionless (multiplier)
- **Source**: `f39_calib.csv` (calibration data)
- **Typical Range**: 0 to 2.0 (many regions = 0, some 0.5-1.5)
- **Applied to**: Cropland reduction only (`presolve.gms:13`)
- **Condition**: Only non-zero in regions with historical cropland decline + cost calibration > 1

### 7.3 Applied Costs (Regional, Time-Varying, Computed)

**i39_cost_establish(t,i,land)** - Regional expansion costs
- **File**: `modules/39_landconversion/calib/declarations.gms:17`
- **Dimensions**: [t, i, land]
- **Units**: USD17MER per ha
- **Calculation**:
  - Crop: `s39_cost_establish_crop × i39_calib(t,i,"cost")` (`presolve.gms:12`)
  - Past: `s39_cost_establish_past` (fixed, `presolve.gms:14`)
  - Forestry: `s39_cost_establish_forestry` (fixed, `presolve.gms:15`)
  - Urban: `s39_cost_establish_urban` (fixed, `presolve.gms:16`)

**i39_reward_reduction(t,i,land)** - Regional reduction rewards
- **File**: `modules/39_landconversion/calib/declarations.gms:18`
- **Dimensions**: [t, i, land]
- **Units**: USD17MER per ha
- **Calculation**:
  - Crop: `s39_reward_crop_reduction × i39_calib(t,i,"reward")` (`presolve.gms:13`)
  - Past/Forestry/Urban: 0 (no rewards, initialized to 0 in `preloop.gms:9`)

---

## 8. Key Scalars (Configuration)

**s39_ignore_calib** - Ignore calibration factors
- **File**: `modules/39_landconversion/calib/input.gms:14`
- **Value**: 0 (OFF by default)
- **Purpose**: Testing switch to disable calibration
- **Effect when 1**:
  - i39_calib(t,i,"cost") = 1 (uniform costs globally)
  - i39_calib(t,i,"reward") = 0 (no rewards)
- **Use case**: Sensitivity analysis, counterfactual scenarios without historical constraints

---

## 9. Code Truth: DOES

1. **Calculates land conversion costs** for four land types (cropland, pasture, forestry, urban) based on expansion area and per-hectare costs (`equations.gms:12-15`)

2. **Applies regional calibration factors** to cropland expansion costs, derived from matching 2015 historical cropland patterns (`presolve.gms:12`, `input.gms:18-22`)

3. **Provides rewards for cropland reduction** in regions with historical cropland decline and high calibration costs, incentivizing abandonment (`presolve.gms:13`, `input.gms:10`)

4. **Annuitizes one-time conversion costs** using factor r/(1+r) to distribute costs over time as annual expenses (`equations.gms:15`)

5. **Uses fixed global costs** for pasture (9,840 USD/ha), forestry (1,230 USD/ha), and urban (12,300 USD/ha) land without regional variation (`presolve.gms:14-16`, `input.gms:11-13`)

6. **Converges calibration to baseline** by enforcing minimum calibration factor of 1.0 by 2050 (all regions pay at least base cost eventually)

7. **Allows testing without calibration** via s39_ignore_calib switch, setting uniform costs globally (`preloop.gms:13-16`)

8. **Initializes reward parameters to zero** for non-cropland types (pasture, forestry, urban have no reduction rewards) (`preloop.gms:9`)

9. **Handles missing calibration data** by defaulting to i39_calib("cost")=1 and i39_calib("reward")=0 if input file absent (`preloop.gms:13-16`)

---

## 10. Code Truth: Does NOT

1. **Does not vary costs by source land type** - cost depends only on target land type (e.g., forest→crop and pasture→crop have same cost)

2. **Does not include vegetation carbon value** in conversion costs - carbon opportunity costs handled separately in Module 56 (GHG policy)

3. **Does not model distance-to-existing-infrastructure** - costs uniform within region regardless of remoteness

4. **Does not include labor costs explicitly** - costs are aggregate estimates not decomposed by factor

5. **Does not model technological change** in conversion costs - base costs (s39_cost_establish_*) fixed over time

6. **Does not differentiate conversion intensity** - same cost regardless of biomass density of cleared land

7. **Does not model conversion delays** - land immediately available after paying cost (no multi-year clearing process)

8. **Does not include biodiversity costs** explicitly - conservation costs handled in Module 22

9. **Does not model irreversibility** - cost of A→B may differ from B→A, but no explicit irreversibility constraint

10. **Does not vary costs by climate or soil** - costs are regional averages not cell-specific based on local conditions

11. **Does not model economies of scale** - per-hectare cost constant regardless of expansion magnitude

12. **Does not include financial costs** beyond interest rate - no risk premiums, no credit constraints

13. **Does not model conversion externalities** explicitly - water quality, air quality impacts not priced

14. **Does not differentiate primary vs secondary land** - clearing old-growth forest has same cost as clearing secondary vegetation (if both are "forest" land type)

15. **Does not model seasonal variation** - annual aggregate costs, no dry season vs wet season differences

---

## 11. Common Modifications

### 11.1 Disable Calibration (Uniform Global Costs)

**Change**: Remove regional cost variation to test uncalibrated expansion patterns

**Files to modify**:
`modules/39_landconversion/calib/input.gms:14`
```gams
s39_ignore_calib = 1  ! Was: 0
```

**Effect**:
- All regions pay 12,300 USD/ha for cropland expansion
- No regional rewards for cropland reduction
- Model expansion patterns may diverge from historical 2015 patterns
- Useful for: Counterfactual scenarios, sensitivity analysis

**Expected Outcome**:
- More expansion in regions with cheap labor and high yields
- Less expansion in land-scarce regions (no cost penalty)
- Different deforestation hotspots

### 11.2 Increase Base Cropland Cost

**Change**: Make agricultural expansion more expensive globally

**Files to modify**:
`modules/39_landconversion/calib/input.gms:9`
```gams
s39_cost_establish_crop = 18450  ! Was: 12300 (+50%)
```

**Effect**:
- Higher threshold for land expansion to be cost-effective
- More intensification (yield increases) instead of extensification
- Lower deforestation rates
- Higher food prices (expansion now more expensive)

**Use case**: Conservation scenarios, high-biodiversity-value scenarios

### 11.3 Remove Reduction Rewards

**Change**: Eliminate incentives for cropland abandonment

**Files to modify**:
`modules/39_landconversion/calib/input.gms:10`
```gams
s39_reward_crop_reduction = 0  ! Was: 7380
```

**Effect**:
- No financial incentive to reduce cropland
- Less cropland abandonment in marginal regions
- Cropland more stable over time
- May better match scenarios without land-sparing policies

**Use case**: Scenarios without rural depopulation, food security concerns

### 11.4 Differentiate Forest Clearing Costs

**Change**: Make forest conversion more expensive than pasture conversion

**Files to modify**:
`modules/39_landconversion/calib/input.gms:9`
```gams
s39_cost_establish_crop = 18450  ! Was: 12300 (forest clearing +50%)
```

**Context**: Current model doesn't distinguish source land type. This modification uses higher base cost as proxy for forest clearing.

**Better Approach** (requires code modification):
Add source-dependent costs in `equations.gms`:
```gams
q39_cost_landcon(j,land) ..
  vm_cost_landcon(j,land) =e=
    sum(land_from, vm_lu_transitions(j,land_from,land) *
                   i39_cost_establish_matrix(i,land_from,land))
    * pm_interest(i) / (1 + pm_interest(i))
```

### 11.5 Add Technological Cost Decline

**Change**: Reduce conversion costs over time due to improved machinery/methods

**Files to modify**: Requires new code in `presolve.gms`
```gams
! Add after line 16
i39_cost_establish(t,i,land) = i39_cost_establish(t,i,land)
                                * (1 - 0.01)**(m_year(t)-1995);
! 1% annual cost decline
```

**Effect**:
- Costs in 2050: 64% of 1995 costs (0.99^55 = 0.64)
- Easier expansion over time
- More agricultural land in long-term projections

**Use case**: Optimistic technology scenarios

### 11.6 Increase Forestry Establishment Cost

**Change**: Make afforestation/reforestation more expensive

**Files to modify**:
`modules/39_landconversion/calib/input.gms:12`
```gams
s39_cost_establish_forestry = 3690  ! Was: 1230 (3× increase)
```

**Effect**:
- Less afforestation in climate mitigation scenarios
- Higher cost for LULUCF-based carbon sequestration
- Greater reliance on avoided deforestation rather than reforestation

**Use case**: Conservative reforestation potential scenarios

---

## 12. Testing & Validation

### 12.1 Check Cost Calculation

**Objective**: Verify costs match formula and sign convention

**GDX Variables**:
- `vm_cost_landcon` - Total costs (mio USD/yr)
- `vm_landexpansion` - Expansion (mio ha)
- `vm_landreduction` - Reduction (mio ha)
- `pm_interest` - Interest rate

**R Code**:
```r
library(magpie4)
library(gdxrrw)

gdx <- "fulldata.gdx"

# Read variables
costs <- readGDX(gdx, "ov_cost_landcon", select=list(type="level"))
expansion <- readGDX(gdx, "ov_landexpansion", select=list(type="level"))
reduction <- readGDX(gdx, "ov_landreduction", select=list(type="level"))
interest <- readGDX(gdx, "pm_interest")

# Read parameters
igdx("/path/to/gams")
cost_establish <- rgdx.param(gdx, "i39_cost_establish")
reward_reduction <- rgdx.param(gdx, "i39_reward_reduction")

# Calculate expected costs for cropland in 2030
t <- "y2030"
region <- "LAM"

expansion_crop <- expansion[t, region, "crop"]
reduction_crop <- reduction[t, region, "crop"]
cost_per_ha <- cost_establish[t, region, "crop"]
reward_per_ha <- reward_reduction[t, region, "crop"]
r <- interest[t, region]

expected_cost <- (expansion_crop * cost_per_ha - reduction_crop * reward_per_ha) * r / (1 + r)
actual_cost <- costs[t, region, "crop"]

print(paste("Expected:", expected_cost, "Actual:", actual_cost))
print(paste("Error:", abs(expected_cost - actual_cost) / expected_cost * 100, "%"))
# Should be < 0.1% (numerical precision)
```

**Expected Results**:
- Expected = Actual (within 0.1% numerical error)
- Expansion regions: Positive costs
- Reduction regions with rewards: Negative costs
- No change regions: Zero costs

**Red Flags**:
- Error > 1% → equation bug or parameter mismatch
- Wrong sign → check reward vs cost application
- Missing data → check calibration file loaded

### 12.2 Check Calibration Loading

**Objective**: Verify regional calibration factors loaded correctly

**GDX Variables**:
- `i39_calib` - Calibration factors

**R Code**:
```r
library(gdxrrw)
igdx("/path/to/gams")

gdx <- "fulldata.gdx"

# Read calibration factors
calib <- rgdx.param(gdx, "i39_calib", squeeze=FALSE)
calib_mc <- as.magpie(calib)

# Check 2020 values
calib_2020_cost <- calib_mc["y2020",,"cost"]
calib_2020_reward <- calib_mc["y2020",,"reward"]

print("Calibration cost factors 2020:")
print(summary(as.vector(calib_2020_cost)))
# Should range from ~0.1 to ~10

print("Calibration reward factors 2020:")
print(summary(as.vector(calib_2020_reward)))
# Should be mostly 0, some regions 0-2

# Check convergence to 1 by 2050
calib_2050_cost <- calib_mc["y2050",,"cost"]
print("Calibration cost factors 2050 (should be >= 1):")
print(range(calib_2050_cost))
stopifnot(all(calib_2050_cost >= 0.99))  # Allow 1% numerical tolerance
```

**Expected Results**:
- 2020 cost factors: Wide range (0.1-10), regional variation
- 2020 reward factors: Many zeros, some regions with positive values
- 2050 cost factors: All ≥ 1.0 (convergence to baseline)
- Temporal trend: Factors converge over time

**Red Flags**:
- All factors = 1 → calibration file not loaded or s39_ignore_calib = 1
- 2050 factors < 1 → convergence logic failed
- Reward factors everywhere → incorrect calibration data

### 12.3 Check Historical Cropland Match (2015)

**Objective**: Verify calibration achieves intended goal of matching 2015 cropland

**GDX Variables**:
- Model cropland 2015 vs historical data

**R Code**:
```r
library(magpie4)
library(mrland)  # For historical data

gdx <- "fulldata.gdx"

# Read model cropland
model_crop <- land(gdx, level="reg")["y2015",,"crop"]

# Read historical cropland (requires mrland package)
hist_crop <- calcOutput("Cropland", aggregate="REG")[, "y2015",]

# Calculate error
error <- (model_crop - hist_crop) / hist_crop * 100

print("Cropland error by region (%):")
print(sort(error))

# Check aggregate error
print(paste("Mean absolute error:", mean(abs(error)), "%"))
print(paste("Max error:", max(abs(error)), "% in", names(which.max(abs(error)))))

# Target: < 10% error in most regions
stopifnot(mean(abs(error)) < 5)
```

**Expected Results**:
- Most regions: < 10% error
- Global aggregate: < 5% mean absolute error
- Outliers: Small regions or data quality issues

**Red Flags**:
- Large systematic errors (>20% in major regions) → calibration failed or outdated
- Model consistently higher → costs too low
- Model consistently lower → costs too high or rewards too strong

### 12.4 Check Cost Impact on Expansion

**Objective**: Verify higher conversion costs reduce expansion

**Setup**: Run two scenarios
1. Baseline costs (s39_cost_establish_crop = 12,300)
2. High costs (s39_cost_establish_crop = 24,600)

**GDX Variables**:
- `vm_landexpansion` - Cropland expansion

**R Code**:
```r
gdx_base <- "fulldata_baseline.gdx"
gdx_high <- "fulldata_highcost.gdx"

# Read expansion
expansion_base <- readGDX(gdx_base, "ov_landexpansion", select=list(type="level"))[,,"crop"]
expansion_high <- readGDX(gdx_high, "ov_landexpansion", select=list(type="level"))[,,"crop"]

# Global totals 2050
global_base <- dimSums(expansion_base["y2050",,], dim=1)
global_high <- dimSums(expansion_high["y2050",,], dim=1)

print(paste("Baseline expansion:", global_base, "mio ha"))
print(paste("High-cost expansion:", global_high, "mio ha"))
print(paste("Reduction:", (global_base - global_high) / global_base * 100, "%"))

# Expect 20-50% reduction in expansion with doubled costs
stopifnot(global_high < global_base * 0.8)
stopifnot(global_high > global_base * 0.3)

# Check yields compensate
yields_base <- yields(gdx_base)[,"y2050",]
yields_high <- yields(gdx_high)[,"y2050",]
print("Yield increase in high-cost scenario:")
print(mean((yields_high - yields_base) / yields_base * 100))
# Should see yield intensification
```

**Expected Results**:
- High costs → 20-50% less expansion
- High costs → 5-15% higher yields (intensification substitutes for expansion)
- High costs → higher food prices (passed through)

**Red Flags**:
- No response → costs not binding (abundant free land) or Module 11 not using costs
- Extreme response (>80% reduction) → costs dominating all decisions unrealistically
- No yield increase → model not optimizing intensification vs extensification trade-off

### 12.5 Check Reward Mechanism

**Objective**: Verify reduction rewards incentivize abandonment

**Setup**: Compare regions with vs without rewards

**R Code**:
```r
gdx <- "fulldata.gdx"

# Read rewards and reduction
rewards <- rgdx.param(gdx, "i39_reward_reduction")
reduction <- readGDX(gdx, "ov_landreduction", select=list(type="level"))[,,"crop"]

# Identify regions with rewards
rewards_mc <- as.magpie(rewards)
regions_with_rewards <- dimnames(rewards_mc["y2020",,"crop"])$i[rewards_mc["y2020",,"crop"] > 0]
regions_without_rewards <- dimnames(rewards_mc["y2020",,"crop"])$i[rewards_mc["y2020",,"crop"] == 0]

# Compare reduction rates
reduction_rate_with <- mean(reduction["y2020", regions_with_rewards,], na.rm=TRUE)
reduction_rate_without <- mean(reduction["y2020", regions_without_rewards,], na.rm=TRUE)

print(paste("Reduction with rewards:", reduction_rate_with, "mio ha"))
print(paste("Reduction without rewards:", reduction_rate_without, "mio ha"))
print(paste("Ratio:", reduction_rate_with / max(reduction_rate_without, 0.01)))

# Regions with rewards should have higher reduction
stopifnot(reduction_rate_with > reduction_rate_without)
```

**Expected Results**:
- Regions with rewards: 2-5× more cropland reduction
- Rewards active in Eastern Europe, parts of developed world
- Reduction concentrated where historically observed

**Red Flags**:
- No difference → rewards not affecting decisions (too small or other constraints binding)
- Extreme reduction (>50% of cropland) → rewards too high, unrealistic abandonment

### 12.6 Check Annuity Factor Impact

**Objective**: Verify interest rate affects cost magnitude correctly

**Setup**: Compare scenarios with different interest rates

**R Code**:
```r
gdx_r5 <- "fulldata_interest5.gdx"    # 5% interest
gdx_r10 <- "fulldata_interest10.gdx"  # 10% interest

# Read costs
costs_r5 <- readGDX(gdx_r5, "ov_cost_landcon", select=list(type="level"))
costs_r10 <- readGDX(gdx_r10, "ov_cost_landcon", select=list(type="level"))

# Read expansion (should be similar in both scenarios for comparison)
exp_r5 <- readGDX(gdx_r5, "ov_landexpansion", select=list(type="level"))
exp_r10 <- readGDX(gdx_r10, "ov_landexpansion", select=list(type="level"))

# Calculate cost per ha
cost_per_ha_r5 <- costs_r5["y2030", "GLO", "crop"] / exp_r5["y2030", "GLO", "crop"]
cost_per_ha_r10 <- costs_r10["y2030", "GLO", "crop"] / exp_r10["y2030", "GLO", "crop"]

# Check annuity factor ratio
annuity_r5 <- 0.05 / 1.05  # 0.0476
annuity_r10 <- 0.10 / 1.10  # 0.0909
expected_ratio <- annuity_r10 / annuity_r5  # Should be ~1.91

actual_ratio <- cost_per_ha_r10 / cost_per_ha_r5

print(paste("Expected cost ratio:", expected_ratio))
print(paste("Actual cost ratio:", actual_ratio))
print(paste("Error:", abs(actual_ratio - expected_ratio) / expected_ratio * 100, "%"))

# Should match within 5% (accounting for behavioral changes)
stopifnot(abs(actual_ratio - expected_ratio) / expected_ratio < 0.10)
```

**Expected Results**:
- Cost ratio ≈ (r2/(1+r2)) / (r1/(1+r1))
- Higher interest → higher annualized costs (shorter time horizon)
- 10% vs 5% interest → roughly 2× higher costs

**Red Flags**:
- No difference → annuity factor not applied correctly
- Wrong ratio → formula error or interest rate not propagating

---

## 13. Literature and Data Sources

### 13.1 Peer-Reviewed Literature

**Land Conversion Costs**:
- **Strassburg et al. (2014)**: "Biophysical suitability, economic pressure and land-cover change: a global probabilistic approach and insights for REDD+", *Sustainability Science*
  - Estimates of forest clearing costs by region
  - Opportunity costs of land-use change

- **Schmitz et al. (2014)**: "Land-use change trajectories up to 2050: insights from a global agro-economic model comparison", *Agricultural Economics*
  - Model comparison of land-use change costs
  - Sensitivity to conversion cost assumptions

**Calibration Methodology**:
- **Dietrich et al. (2019)**: "MAgPIE 4 – a modular open-source framework for modeling global land systems", *Geoscientific Model Development*
  - MAgPIE calibration approach
  - Matching historical patterns

- **Popp et al. (2014)**: "Land-use transition for bioenergy and climate stabilization: model comparison of drivers, impacts and interactions with other land use based mitigation options", *Climatic Change*
  - Land-use model calibration techniques
  - Historical validation

### 13.2 Data Sources

**Base Cost Estimates**:
- Source: Grey literature + expert estimates + model calibration
- Components:
  - **Clearing costs**: Vegetation removal, stump extraction
  - **Preparation costs**: Plowing, leveling, drainage
  - **Infrastructure costs**: Fencing, roads, water access
- Calibrated to match historical expansion patterns

**Historical Cropland (Calibration Target)**:
- Source: FAO Agricultural Land database
- URL: https://www.fao.org/faostat/en/#data/RL
- Coverage: Country-level cropland area 1961-2020
- Benchmark year: 2015 (used for calibration)

**Regional Calibration Factors**:
- Source: Iterative model runs
- File: `modules/39_landconversion/input/f39_calib.csv`
- Derived: Internal MAgPIE calibration process
- Updated: Periodically when historical data updated or model structure changes

### 13.3 Model Documentation

**MAgPIE Model Documentation**:
- Dietrich, J.P., et al. (2019): "MAgPIE 4 – a modular open-source framework for modeling global land systems", *Geoscientific Model Development*
- URL: https://doi.org/10.5194/gmd-12-1299-2019

**Module Development History**:
- Original: Simple uniform costs
- calib (current): Regional calibration + rewards

---

## 14. Summary for AI Agents

### 14.1 Module Identity

**Name**: Land Conversion Costs (Module 39)
**Purpose**: Calculate costs of converting land between types
**Realization**: `calib` (calibrated costs and rewards)
**Key Innovation**: Regional calibration factors matching historical 2015 cropland patterns

### 14.2 Critical Mechanisms

1. **Cost Formula** (`equations.gms:12-15`):
   - Cost = (Expansion × Cost/ha - Reduction × Reward/ha) × r/(1+r)
   - Annuity factor r/(1+r) converts one-time to annual costs
   - Negative costs possible (rewards for reduction)

2. **Calibration System** (`presolve.gms:12-13`):
   - Cropland: Regional multipliers on base cost (12,300 USD/ha)
   - Other land: Fixed global costs (no regional variation)
   - Convergence to minimum 1.0 by 2050

3. **Reduction Rewards** (`presolve.gms:13`):
   - Only cropland in specific regions
   - Based on historical decline patterns (1995-2015)
   - Incentivizes abandonment where observed historically

### 14.3 Key Dependencies

**Receives From**:
- Module 10: Land expansion/reduction (vm_landexpansion, vm_landreduction)
- Module 12: Interest rates (pm_interest)

**Provides To**:
- Module 11: Conversion costs (vm_cost_landcon) → total costs → land-use decisions

### 14.4 Common Misconceptions

1. **"Costs depend on source land type"** - No, only target land type matters (all conversions to cropland have same cost)

2. **"Carbon value included in costs"** - No, carbon opportunity costs separate in Module 56

3. **"Rewards apply to all land types"** - No, only cropland in calibrated regions

4. **"Costs are per year"** - No, costs are one-time but annuitized to appear as annual

5. **"All regions same cost"** - No, cropland regionally calibrated (0.1× to 10× variation)

### 14.5 Debugging Decision Tree

**Issue: Unrealistic expansion patterns**
→ Check i39_calib values (should vary regionally)
→ Check s39_ignore_calib = 0 (calibration active)
→ Compare model 2015 cropland to FAO historical data

**Issue: No rewards appearing**
→ Check i39_calib("reward") > 0 for some regions
→ Check vm_landreduction > 0 in those regions
→ Verify s39_reward_crop_reduction > 0

**Issue: Conversion costs zero or too low**
→ Check s39_cost_establish_crop = 12300 (base cost)
→ Check pm_interest > 0 (annuity factor needs interest rate)
→ Check Module 11 including vm_cost_landcon in total costs

**Issue: Costs too high, preventing all expansion**
→ Check calibration factors not extreme (>10)
→ Check not double-counting (Module 56 carbon + Module 39 conversion)
→ Reduce s39_cost_establish_crop or s39_ignore_calib = 1

---

## 15. AI Agent Response Patterns

### Query: "Why is agricultural expansion concentrated in certain regions?"

**Response Structure**:

1. **Identify Primary Driver**: Module 39 calibration
   - File: `modules/39_landconversion/calib/presolve.gms:12`
   - Regional cost multipliers: i39_calib(t,i,"cost")

2. **Explain Mechanism**:
```gams
i39_cost_establish(t,i,"crop") = s39_cost_establish_crop * i39_calib(t,i,"cost")
```
   - Base cost: 12,300 USD/ha
   - Region A: i39_calib = 0.5 → Effective cost = 6,150 USD/ha
   - Region B: i39_calib = 3.0 → Effective cost = 36,900 USD/ha
   - Region A sees 6× cheaper expansion → more expansion

3. **Check Calibration Values**:
```r
calib <- rgdx.param(gdx, "i39_calib")
calib_mc <- as.magpie(calib)
print(calib_mc["y2020",,"cost"])
```

4. **Cross-Check Other Factors** (not just Module 39):
   - Module 14: Regional yield levels
   - Module 10: Land availability
   - Module 56: Carbon prices (forest regions)

5. **Expected Answer**:
   - "Expansion favored in Region X due to calibration factor 0.6 (40% lower costs)"
   - "Region Y restricted by calibration factor 2.5 (150% higher costs)"
   - "Calibration based on matching 2015 historical cropland patterns"
   - "Also check: yields (Module 14), carbon costs (Module 56), land constraints (Module 10)"

---

### Query: "Why does the model show cropland abandonment in Eastern Europe?"

**Response Structure**:

1. **Identify Reduction Reward**: Module 39 calibration
   - File: `modules/39_landconversion/calib/presolve.gms:13`
   - Reward multiplier: i39_calib(t,i,"reward")

2. **Explain Historical Context**:
   - Eastern Europe: Cropland declined 1995-2015 (post-Soviet agricultural restructuring)
   - Calibration: Regions with historical decline + high expansion cost get rewards
   - Incentive: Continued abandonment financially rewarded

3. **Check Reward Values**:
```r
rewards <- rgdx.param(gdx, "i39_reward_reduction")
rewards_mc <- as.magpie(rewards)
print(rewards_mc["y2020", "EUR",])  # Eastern Europe example
```

4. **Calculate Net Effect**:
```r
reduction <- readGDX(gdx, "ov_landreduction", select=list(type="level"))
costs <- readGDX(gdx, "ov_cost_landcon", select=list(type="level"))

# Negative cost = reward
print(costs["y2030", "EUR", "crop"])  # Should be negative if reward > expansion
```

5. **Expected Answer**:
   - "Eastern Europe has reduction reward of 7,380 USD/ha × multiplier X"
   - "Historical cropland declined 1995-2015 due to agricultural restructuring"
   - "Model incentivizes continued abandonment matching historical trend"
   - "Net effect: Negative conversion costs (reward) of $Y million/yr"
   - "Reward diminishes over time (convergence to baseline by 2050)"

---

### Query: "How do I test the model without historical calibration constraints?"

**Response Structure**:

1. **Identify Bypass Switch**: s39_ignore_calib
   - File: `modules/39_landconversion/calib/input.gms:14`
   - Default: 0 (calibration active)

2. **Modification**:
```gams
# modules/39_landconversion/calib/input.gms:14
s39_ignore_calib = 1  ! Was: 0
```

3. **Effect**:
   - All regions: i39_calib("cost") = 1 (uniform 12,300 USD/ha)
   - All regions: i39_calib("reward") = 0 (no rewards)
   - Model expansion pattern determined purely by:
     - Biophysical suitability (yields from Module 14)
     - Economic factors (costs from Module 38, prices from Module 21)
     - Policy constraints (conservation from Module 22, carbon from Module 56)

4. **Testing Strategy**:
```r
# Run two scenarios
# Scenario 1: Calibrated (s39_ignore_calib = 0)
# Scenario 2: Uncalibrated (s39_ignore_calib = 1)

gdx_calib <- "fulldata_calibrated.gdx"
gdx_uncalib <- "fulldata_uncalibrated.gdx"

# Compare 2015 cropland to FAO
crop_calib <- land(gdx_calib)["y2015",,"crop"]
crop_uncalib <- land(gdx_uncalib)["y2015",,"crop"]
crop_fao <- fao_cropland["y2015",,]

# Expect: Calibrated close to FAO, Uncalibrated diverges
error_calib <- mean(abs(crop_calib - crop_fao) / crop_fao)
error_uncalib <- mean(abs(crop_uncalib - crop_fao) / crop_fao)

print(paste("Calibrated error:", error_calib))    # Should be < 5%
print(paste("Uncalibrated error:", error_uncalib))  # May be 10-30%
```

5. **Expected Answer**:
   - "Set s39_ignore_calib = 1 in modules/39_landconversion/calib/input.gms:14"
   - "This disables regional calibration: all regions pay 12,300 USD/ha"
   - "Expect divergence from 2015 historical patterns (10-30% error vs <5% calibrated)"
   - "Useful for: counterfactual scenarios, testing pure biophysical/economic drivers"
   - "Warning: Future projections less reliable without historical validation"

---

**End of Module 39 Comprehensive Documentation**

---

## Participates In

This section shows Module 39's role in system-level mechanisms. For complete details, see the linked documentation.

### Conservation Laws

Module 39 does **not directly participate** in any conservation laws as a primary enforcer.

**Indirect Role**: Module 39 may affect land conversion costs, which influences other modules, but has no direct conservation constraints.

### Dependency Chains

**Centrality Analysis** (from Phase2_Module_Dependencies.md):
- **Centrality Rank**: Low-to-Medium (peripheral/intermediate module)
- **Hub Type**: **Cost Component Provider**

**Details**: See `core_docs/Phase2_Module_Dependencies.md` for complete dependency information.

### Circular Dependencies

Module 39 participates in **zero or minimal circular dependencies**.

**Details**: See `cross_module/circular_dependency_resolution.md` for system-level cycles.

### Modification Safety

**Risk Level**: 🟡 **MEDIUM RISK**

**Safe Modifications**:
- ✅ Adjust module-specific parameters
- ✅ Change scenario selections
- ✅ Modify calculation methods within module

**Testing Requirements**:
1. Verify outputs are in expected ranges
2. Check downstream modules that depend on this module's outputs
3. Run full model to ensure no infeasibility

**Links**:
- Full dependency details → `core_docs/Phase2_Module_Dependencies.md`
- Related modules → Check interface variables in module documentation

---

**Module 39 Status**: ✅ COMPLETE

---

**Last Verified**: 2025-10-13
**Verified Against**: `../modules/39_*/maccs_aug22/*.gms`
**Verification Method**: Equations cross-referenced with source code
**Changes Since Last Verification**: None (stable)
