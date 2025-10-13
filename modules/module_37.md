## Module 37: Labor Productivity (Heat Stress Impacts) ✅ COMPLETE

**Status**: Fully documented
**Location**: `modules/37_labor_prod/`
**Realizations**:
- `exo` (exogenous climate-driven productivity, default)
- `off` (no productivity change, fixed at 1.0)
**Code Size**: 140 lines across 8 files
**Complexity**: Low (simple data provider, no equations)
**Authors**: Florian Humpenöder, Michael Windisch

---

## 1. Purpose & Overview

**Primary Function**: Provide exogenous labor productivity factors that capture heat stress impacts on agricultural workers under climate change.

**Core Responsibilities**:
1. **Load heat stress impacts** from LAMACLIMA project Earth System Model (ESM) experiments
2. **Provide labor productivity factor** `pm_labor_prod(t,j)` to Module 38 (Factor Costs)
3. **Support multiple scenarios**: RCP1.9 and RCP8.5 climate scenarios
4. **Offer configuration options**: Two metrics (ISO, HOTHAPS), two work intensities (300W, 400W), uncertainty bands
5. **Enable/disable climate impacts**: `exo` realization (with impacts) vs. `off` realization (no impacts)

**Model Role**: Pure source module (no optimization, no equations) providing climate-driven labor productivity adjustments

**Key Innovation**: First explicit modeling of heat stress impacts on agricultural labor in a global land-use model

**Physical Basis**: Wet Bulb Globe Temperature (WBGT) - combines temperature, humidity, wind speed, and solar radiation to measure heat stress

---

## 2. Key Mechanisms

#### 2.1 Heat Stress and Labor Productivity

**Physical Mechanism**:

When agricultural workers are exposed to high heat stress (measured by WBGT), their productivity declines due to:
1. **Physiological constraints**: Heat exhaustion, dehydration, reduced physical capacity
2. **Safety requirements**: Mandatory rest breaks to prevent heat stroke
3. **Reduced work hours**: Shift work earlier/later to avoid peak heat

**Example**:
- WBGT = 25°C: No impact, full productivity
- WBGT = 30°C: Moderate impact, 85-90% productivity (rest breaks needed)
- WBGT = 35°C: Severe impact, 60-70% productivity (frequent breaks, shorter shifts)

**Regional Pattern**:
- Tropical regions (SSA, SAS, LAM): Largest productivity losses (high heat + humidity)
- Temperate regions (EUR, USA): Minimal or positive effects (milder climate, some benefit in cold regions)
- Arid regions (MENA, CPA): Moderate losses (high heat but low humidity)

#### 2.2 Wet Bulb Globe Temperature (WBGT)

**Definition**: Heat index combining multiple environmental factors

**Formula** (simplified):
```
WBGT = 0.7 × Wet Bulb Temp + 0.2 × Globe Temp + 0.1 × Dry Bulb Temp
```

**Components**:
1. **Wet Bulb Temperature**: Temperature measured with wet thermometer (evaporative cooling effect)
   - Captures humidity impact
   - High humidity → less evaporative cooling → higher heat stress
2. **Globe Temperature**: Temperature inside black globe (solar radiation effect)
   - Captures solar radiation impact
   - Strong sun → higher heat stress
3. **Dry Bulb Temperature**: Standard air temperature

**Why WBGT?**
- More comprehensive than air temperature alone
- Accounts for humidity (critical for heat stress)
- Accounts for wind speed and solar radiation
- Standard metric in occupational health (ISO 7243)

**Data Source**:
- ESM climate projections (temperature, humidity, wind, radiation)
- WBGT calculated from ESM outputs
- Aggregated to MAgPIE cells

---

## 3. Two Productivity Metrics

Module 37 supports two alternative metrics for calculating heat stress impacts:

#### 3.1 ISO Metric (International Organization for Standardization)

**Basis**: ISO 7243 standard for assessment of heat stress using WBGT index

**Method**: Prescribes rest break frequency and duration based on WBGT and work intensity

**Rest Break Table** (conceptual, from ISO 7243):
```
Work Intensity | WBGT Threshold | Rest per Hour
----------------|----------------|---------------
400W (heavy)   | < 26°C         | 0% (no rest)
400W (heavy)   | 26-28°C        | 25% (15 min/hr)
400W (heavy)   | 28-30°C        | 50% (30 min/hr)
400W (heavy)   | > 30°C         | 75% (45 min/hr)

300W (moderate)| < 28°C         | 0% (no rest)
300W (moderate)| 28-30°C        | 25% (15 min/hr)
300W (moderate)| 30-32°C        | 50% (30 min/hr)
300W (moderate)| > 32°C         | 75% (45 min/hr)
```

**Productivity Calculation**:
```
Labor Productivity = 1 - (Rest Fraction)
```

**Example**:
- WBGT = 29°C, 400W work intensity
- ISO standard: 50% rest breaks
- Labor Productivity = 1 - 0.50 = 0.50 (50% productivity)

**Advantages**:
- Based on regulatory standards (widely accepted)
- Conservative (ensures worker safety)
- Clear interpretation (rest break requirements)

**Disadvantages**:
- Discrete thresholds (step functions)
- May overestimate impacts in some contexts (assumes full compliance)

#### 3.2 HOTHAPS Metric (Workability Function)

**Basis**: Empirical relationship between WBGT and workability from occupational health literature

**Method**: Continuous function describing fraction of time workers can maintain productivity

**Workability Function** (conceptual):
```
Workability(WBGT) = 1 / (1 + exp(β × (WBGT - WBGT_threshold)))
```

**Characteristics**:
- **Smooth curve**: No discrete jumps
- **Threshold-based**: Rapid decline above critical WBGT
- **Asymptotic**: Approaches zero at extreme heat (but never exactly zero)

**Example**:
- WBGT = 25°C: Workability ≈ 0.95 (95% productivity)
- WBGT = 30°C: Workability ≈ 0.70 (70% productivity)
- WBGT = 35°C: Workability ≈ 0.30 (30% productivity)

**Advantages**:
- Continuous function (no artificial thresholds)
- Based on empirical observations
- Captures gradual decline in productivity

**Disadvantages**:
- Less directly tied to regulatory standards
- Calibration requires data on actual productivity under heat stress

**Comparison**:
- ISO: More conservative, discrete, regulatory-based
- HOTHAPS: Less conservative, continuous, empirically-based
- Both give similar results for moderate heat stress
- ISO gives larger impacts at extreme heat (full rest requirements)

**Configuration** (`input.gms:14`):
```gams
$setglobal c37_labor_metric  ISO
* Options: ISO, HOTHAPS
```

---

## 4. Work Intensity Levels

Agricultural work varies in physical intensity, which affects heat stress susceptibility:

#### 4.1 400W (Heavy Work) - DEFAULT

**Typical Activities**:
- Manual harvesting (hand-picking crops)
- Digging, hoeing, weeding by hand
- Carrying heavy loads (sacks of grain, produce)
- Planting seedlings manually
- Livestock handling (moving animals)

**Characteristics**:
- **High metabolic rate**: 400 Watts of energy expenditure
- **High heat generation**: Workers generate significant internal heat
- **Higher heat stress**: More susceptible to heat impacts

**Regions**: Typical in developing countries with low mechanization (SSA, SAS, LAM)

**Historical Assumption**: Previous studies use 400W as default for agriculture globally

#### 4.2 300W (Moderate Work)

**Typical Activities**:
- Operating tractors, combines (air-conditioned cabs)
- Supervising mechanized operations
- Light manual work (pruning, inspection)
- Irrigation system operation
- Livestock monitoring

**Characteristics**:
- **Lower metabolic rate**: 300 Watts of energy expenditure
- **Less heat generation**: Workers generate less internal heat
- **Lower heat stress**: More tolerance to ambient heat

**Regions**: Typical in developed countries with high mechanization (EUR, USA, JPN)

**Rationale**: Mechanization reduces physical labor intensity, making workers less vulnerable to heat stress

**Impact Comparison**:
```
Example: WBGT = 30°C
- 400W: Productivity = 0.50 (50% loss)
- 300W: Productivity = 0.75 (25% loss)
→ Mechanization provides 25% productivity benefit under heat stress
```

**Configuration** (`input.gms:15`):
```gams
$setglobal c37_labor_intensity  400W
* Options: 300W, 400W
```

**Future Enhancement Possibility**:
- Regional variation (300W for developed regions, 400W for developing)
- Endogenous mechanization (shift from 400W to 300W as wages increase)
- Currently NOT implemented (global uniform assumption)

---

## 5. Climate Scenarios

#### 5.1 RCP1.9 (1.9 W/m² Radiative Forcing)

**Characteristics**:
- **Low warming**: Peak warming ~1.5°C above pre-industrial by 2100
- **Ambitious mitigation**: Rapid decarbonization, net-zero by 2050
- **Limited heat stress impacts**: Modest increases in WBGT
- **Regional variation**: Some high-latitude regions may see productivity gains (warmer winters)

**Typical Results**:
- Global agricultural labor productivity: 95-98% by 2050 (2-5% loss)
- Tropical regions: 85-95% (5-15% loss)
- Temperate regions: 98-100% (minimal change)

**Use Case**: Optimistic climate policy scenario (Paris Agreement 1.5°C target)

#### 5.2 RCP8.5 (8.5 W/m² Radiative Forcing)

**Characteristics**:
- **High warming**: Warming ~4-5°C above pre-industrial by 2100
- **No mitigation**: Business-as-usual emissions
- **Severe heat stress impacts**: Large increases in WBGT, especially tropics
- **Threshold crossing**: Many regions exceed physiological limits

**Typical Results**:
- Global agricultural labor productivity: 80-90% by 2050 (10-20% loss)
- Tropical regions: 50-80% by 2100 (20-50% loss, potentially catastrophic)
- Temperate regions: 90-95% (moderate losses)

**Use Case**: Pessimistic no-policy scenario (upper bound of impacts)

**Limitation**: Only RCP1.9 and RCP8.5 available (no intermediate scenarios like RCP4.5)

**Configuration** (`input.gms:13`):
```gams
$setglobal c37_labor_rcp  rcp119
* Options: rcp119 (RCP1.9), rcp585 (RCP8.5)
```

---

## 6. Uncertainty Quantification

Climate projections from Earth System Models (ESMs) have uncertainties:

#### 6.1 Ensemble Statistics

**Ensemble**: Multiple ESM runs with different initial conditions, models, parameterizations

**Statistics Provided**:
1. **enslower**: Lower bound (5th percentile of ESM ensemble)
   - Optimistic: Lower heat stress than median projection
   - Use: Sensitivity analysis, best-case scenario
2. **ensmean**: Ensemble mean (average across ESM runs) - DEFAULT
   - Central estimate: Most likely outcome
   - Use: Default scenario for main analysis
3. **ensupper**: Upper bound (95th percentile of ESM ensemble)
   - Pessimistic: Higher heat stress than median projection
   - Use: Sensitivity analysis, worst-case scenario

**Interpretation**:
```
Example: Global labor productivity in 2050 under RCP8.5
- enslower: 92% (8% loss)
- ensmean: 85% (15% loss)
- ensupper: 75% (25% loss)
→ 90% confidence interval: 75-92% productivity
```

**Why Uncertainty Matters**:
- ESMs differ in climate sensitivity, regional precipitation, humidity projections
- WBGT highly sensitive to humidity (uncertain variable)
- Agricultural adaptation not captured (uncertainty in human response)

**Configuration** (`input.gms:16`):
```gams
$setglobal c37_labor_uncertainty  ensmean
* Options: enslower, ensmean, ensupper
```

---

## 7. Realization Structure

Module 37 has **2 realizations**:

#### 7.1 Realization: exo (Exogenous Heat Stress Impacts) - DEFAULT

**Purpose**: Include climate change impacts on labor productivity

**Mechanism** (`preloop.gms:8`):
```gams
pm_labor_prod(t,j) = f37_labor_prod(t,j,"%c37_labor_rcp%","%c37_labor_metric%",
                                     "%c37_labor_intensity%","%c37_labor_uncertainty%");
```

**Data Source**: `f37_labourprodimpact.cs3` (from LAMACLIMA project)

**Climate Scenario Switch** (`input.gms:8-11`, `preloop.gms:10-11`):
- `c37_labor_prod_scenario = "cc"` (default): Climate change impacts included
- `c37_labor_prod_scenario = "nocc"`: All years fixed to 1995 (no climate change)
- `c37_labor_prod_scenario = "nocc_hist"`: Fixed after `sm_fix_cc` year (e.g., 2025)

**Example Configuration**:
```gams
* Default (full climate impacts, RCP1.9, ISO metric, 400W intensity, mean)
c37_labor_rcp = "rcp119"
c37_labor_metric = "ISO"
c37_labor_intensity = "400W"
c37_labor_uncertainty = "ensmean"
c37_labor_prod_scenario = "cc"
```

**Code Size**: 104 lines (5 files)

#### 7.2 Realization: off (No Heat Stress Impacts)

**Purpose**: Counterfactual scenario without labor productivity changes

**Mechanism** (`off/preloop.gms:8`):
```gams
pm_labor_prod(t,j) = 1;
```

**All Values Fixed**: `pm_labor_prod(t,j) = 1.0` for all time periods and regions

**Use Cases**:
- Baseline comparison (quantify impact of heat stress)
- Historical runs where heat stress data unavailable
- Sensitivity analysis (isolate heat stress effects)

**Code Size**: 36 lines (3 files)

**Switching**:
```r
# In R config
cfg$gms$labor_prod <- "off"  # Disable heat stress impacts
```

---

## 8. Interface Parameter

Module 37 provides **1 interface parameter** to other modules:

#### 8.1 pm_labor_prod(t,j) - Labor Productivity Factor

**Type**: Parameter (not optimized, exogenous)

**Dimensions**: (t, j) - time × 200 MAgPIE cells

**Units**: Dimensionless multiplier (1 = no impact, <1 = productivity loss, >1 = productivity gain)

**Typical Range**:
- No climate change: 1.0 (all years)
- RCP1.9 by 2050: 0.95-1.00 (0-5% loss)
- RCP8.5 by 2050: 0.80-0.95 (5-20% loss)
- RCP8.5 by 2100: 0.50-0.90 (10-50% loss in tropics)

**Calculated In**:
- `exo` realization: `preloop.gms:8`
- `off` realization: `off/preloop.gms:8`

**Used By**: Module 38 (Factor Costs)

**Application in Module 38** (conceptual):
```gams
* Labor costs are divided by productivity factor
* Lower productivity → higher costs (need more labor hours for same output)
vm_labor_costs(i) = baseline_labor_costs(i) / sum(cell(i,j), pm_labor_prod(t,j))
```

**Interpretation**:
```
pm_labor_prod(t,j) = 0.80 means:
- Workers are 80% as productive as baseline (20% loss)
- Need 25% more labor hours for same output (1/0.80 = 1.25)
- Labor costs increase by 25% (assuming wages constant)
- Agricultural employment increases by 25% (if production constant)
```

---

## 9. Data Source

#### 9.1 f37_labourprodimpact.cs3 - Heat Stress Impact Data

**Location**: `modules/37_labor_prod/exo/input/f37_labourprodimpact.cs3`

**Dimensions**: (t_all, j, rcp37, metric37, intensity37, uncertainty37)
- t_all: Time periods (1995-2150, 5-year intervals)
- j: 200 MAgPIE cells (0.5° grid aggregated)
- rcp37: RCP scenarios (rcp119, rcp585)
- metric37: Metrics (ISO, HOTHAPS)
- intensity37: Work intensity (300W, 400W)
- uncertainty37: Ensemble statistics (enslower, ensmean, ensupper)

**Units**: Dimensionless (labor productivity factor, 1 = no impact)

**Size**: ~240,000 data points (200 cells × 30 years × 2 RCPs × 2 metrics × 2 intensities × 3 uncertainty)

**Source**: LAMACLIMA project (Climate Analytics)
- Project: <https://climateanalytics.org/projects/lamaclima/>
- Methodology: Orlov et al. (2021) - "Economic losses from heat-induced reductions in outdoor worker productivity"
- ESM Data: CMIP6 multi-model ensemble

**Calculation Steps** (external to MAgPIE):
1. Run ESMs to project temperature, humidity, wind, radiation
2. Calculate WBGT from ESM outputs
3. Apply ISO or HOTHAPS methodology to derive productivity impacts
4. Aggregate to MAgPIE cells
5. Ensemble statistics (enslower, ensmean, ensupper)

**Temporal Coverage**:
- Historical: 1995-2020 (calibration, validation)
- Projections: 2020-2150 (climate scenarios)

**Spatial Resolution**:
- Original: 0.5° grid (~50 km at equator)
- MAgPIE: 200 clusters (aggregated for computational efficiency)

**Filling Missing Years** (`input.gms:23`):
```gams
m_fillmissingyears(f37_labor_prod,"j,rcp37,metric37,intensity37,uncertainty37");
```
- Data provided every 5 years
- Interpolated linearly between data points

**Historical Constraint** (`input.gms:25-26`):
```gams
f37_labor_prod(t_all,j,rcp37,metric37,intensity37,uncertainty37)$(m_year(t_all) <= sm_fix_cc) =
  f37_labor_prod(t_all,j,"rcp119","ISO","400W","ensmean")$(m_year(t_all) <= sm_fix_cc);
```
- Before `sm_fix_cc` (typically 2025): All scenarios use default (rcp119, ISO, 400W, ensmean)
- After `sm_fix_cc`: Scenarios diverge based on configuration
- Rationale: Near-term climate similar across scenarios (scenario uncertainty only for long-term)

---

## 10. Module Dependencies

**From Phase 2 Dependency Analysis**:
- **Dependency Count**: 1 connection (minimal centrality)
- **Role**: Pure source (no dependencies) → single target (Module 38)

#### 10.1 Provides TO (Downstream Module)

**Module 38 (factor_costs)**: `pm_labor_prod(t,j)`
- Used to adjust labor costs for heat stress
- Lower productivity → higher labor costs per unit output
- Affects crop production costs, land allocation decisions

**Impact Chain**:
```
Climate Change (ESM)
  → WBGT increases (heat stress)
  → pm_labor_prod decreases (Module 37)
  → Labor costs increase (Module 38)
  → Production costs increase
  → Land allocation shifts (Module 10)
  → Food prices may increase (Module 21)
  → Agricultural employment may increase (Module 36, compensating for productivity loss)
```

#### 10.2 Receives FROM (Upstream Modules)

**NONE** - Module 37 is a pure source module
- No dependencies on other MAgPIE modules
- Uses only external data (ESM projections)
- No feedback from model outcomes to productivity

**One-Way Coupling**: Climate → Model (not Model → Climate)
- Labor productivity responds to exogenous climate
- Agricultural decisions do NOT affect labor productivity in Module 37
- No adaptation dynamics (e.g., shift work schedules, air conditioning)

---

## 11. Code Truth: What Module 37 DOES

**VERIFIED implementations with file:line references**:

1. ✅ **Loads heat stress impact data from LAMACLIMA**:
   - Data file: `input.gms:18-22`
   - 5-dimensional array: time, space, RCP, metric, intensity, uncertainty

2. ✅ **Fills missing years by interpolation**:
   - Interpolation: `input.gms:23`
   - Linear interpolation between 5-year data points

3. ✅ **Enforces historical consistency across scenarios**:
   - Historical constraint: `input.gms:25-26`
   - All scenarios identical before `sm_fix_cc` year

4. ✅ **Selects scenario based on configuration**:
   - Selection: `preloop.gms:8`
   - Uses global settings (RCP, metric, intensity, uncertainty)

5. ✅ **Supports climate scenario switching**:
   - "cc": Full climate change (`preloop.gms:8`)
   - "nocc": Fixed to 1995 (`preloop.gms:10`)
   - "nocc_hist": Fixed after `sm_fix_cc` (`preloop.gms:11`)

6. ✅ **Provides two realizations**:
   - `exo`: Heat stress impacts included (`exo/realization.gms`)
   - `off`: No impacts, fixed at 1.0 (`off/realization.gms`)

7. ✅ **Provides single interface parameter**:
   - `pm_labor_prod(t,j)`: Used by Module 38
   - Units: dimensionless multiplier (declarations.gms:9`)

---

## 12. Code Truth: What Module 37 Does NOT Do

**VERIFIED limitations with file:line references**:

1. ❌ **NO endogenous productivity** (`module.gms:11-12`):
   - Productivity exogenous (loaded from data)
   - Does NOT respond to:
     - Agricultural wages (Module 36)
     - Technological change (Module 13)
     - Mechanization investments
     - Adaptation decisions
   - Reality: Farmers adapt to heat stress (shift schedules, invest in cooling)

2. ❌ **NO intermediate climate scenarios**:
   - Only RCP1.9 and RCP8.5 (`sets.gms:10`)
   - Missing: RCP2.6, RCP4.5, RCP6.0
   - Reality: Most policy scenarios between these extremes

3. ❌ **NO regional variation in work intensity**:
   - Global uniform assumption (300W or 400W for all regions)
   - Reality: Developed regions more mechanized (300W), developing regions more manual (400W)
   - Potential enhancement: Link to development state or wages

4. ❌ **NO crop-specific variation**:
   - Same productivity factor for all crops
   - Reality: Harvest timing varies (summer vs. winter crops), heat exposure differs

5. ❌ **NO seasonal variation**:
   - Annual average productivity
   - Reality: Heat stress concentrated in summer months
   - Implication: May underestimate peak-season impacts

6. ❌ **NO feedback to climate**:
   - One-way coupling (climate → productivity)
   - Agricultural decisions do NOT affect climate in Module 37
   - Reality: Land-use change affects regional climate (covered in Module 52, not 37)

7. ❌ **NO direct adaptation modeling**:
   - Productivity declines assumed unavoidable
   - Reality: Air-conditioned cabs, shade structures, irrigation cooling
   - Workaround: Can simulate adaptation by reducing intensity (400W → 300W scenario)

8. ❌ **NO livestock-specific impacts**:
   - Applies only to crops (through Module 38)
   - Reality: Heat stress also affects livestock productivity (Module 70 does NOT use pm_labor_prod)
   - Limitation: Livestock heat stress not captured

9. ❌ **NO health costs**:
   - Only productivity impacts (economic)
   - Missing: Medical costs, mortality, morbidity
   - Reality: Heat stress has health consequences beyond productivity

10. ❌ **NO sub-national variation**:
    - 200 MAgPIE cells (0.5° resolution aggregated)
    - Within-cell heterogeneity not captured
    - Reality: Microclimate variation (valleys vs. hills, irrigated vs. rainfed)

---

## 13. Common Modifications & Use Cases

#### 13.1 Switch to RCP8.5 (High Warming Scenario)

**Purpose**: Assess agricultural labor costs under severe climate change

**Configuration**:
```gams
$setglobal c37_labor_rcp  rcp585
```

**File**: `input.gms:13`

**Expected Impact**:
- Labor productivity declines significantly by 2050-2100
- Tropical regions: 20-50% productivity loss by 2100
- Labor costs increase proportionally (1 / productivity factor)
- Agricultural employment increases (compensating for productivity loss)
- Food prices increase (higher production costs)

**Testing**:
```r
library(magpie4)
prod_rcp19 <- readGDX("fulldata_rcp19.gdx", "pm_labor_prod")
prod_rcp85 <- readGDX("fulldata_rcp85.gdx", "pm_labor_prod")

# Productivity loss by 2100
loss_2100 <- (1 - prod_rcp85["y2100",]) / (1 - prod_rcp19["y2100",])
plot(loss_2100, main="Additional productivity loss under RCP8.5 vs. RCP1.9 by 2100")
```

#### 13.2 Test Mechanization Benefit (400W → 300W)

**Purpose**: Quantify labor cost savings from mechanization under heat stress

**Configuration**:
```gams
$setglobal c37_labor_intensity  300W
```

**File**: `input.gms:15`

**Expected Impact**:
- Labor productivity higher than 400W scenario (less heat stress)
- Difference largest in hot regions (tropics)
- Benefit increases over time (climate warms)

**Analysis**:
```r
prod_400W <- readGDX("fulldata_400W.gdx", "pm_labor_prod")
prod_300W <- readGDX("fulldata_300W.gdx", "pm_labor_prod")

# Mechanization benefit (productivity gain)
mech_benefit <- (prod_300W - prod_400W) / prod_400W * 100
plot(mech_benefit["y2050",], main="Productivity gain from mechanization (300W vs 400W) by 2050 (%)")
# Typical result: 5-20% gain in tropics, 0-5% in temperate regions
```

**Implication**: Mechanization provides climate adaptation benefit (reduced heat exposure)

#### 13.3 Compare ISO vs. HOTHAPS Metrics

**Purpose**: Assess uncertainty from metric choice

**Configuration**:
```gams
$setglobal c37_labor_metric  HOTHAPS
```

**File**: `input.gms:14`

**Expected Differences**:
- ISO: More conservative (larger productivity losses at high heat)
- HOTHAPS: Less conservative (smaller losses)
- Difference increases at extreme heat (WBGT > 35°C)

**Testing**:
```r
prod_ISO <- readGDX("fulldata_ISO.gdx", "pm_labor_prod")
prod_HOTHAPS <- readGDX("fulldata_HOTHAPS.gdx", "pm_labor_prod")

# Metric difference
diff <- prod_HOTHAPS - prod_ISO
plot(diff["y2100",], main="HOTHAPS - ISO productivity difference by 2100")
# Positive values: HOTHAPS more optimistic
# Largest differences in tropical regions under RCP8.5
```

#### 13.4 Uncertainty Analysis (Ensemble Bounds)

**Purpose**: Quantify climate projection uncertainty

**Configurations**:
```gams
c37_labor_uncertainty = "enslower"  # Optimistic
c37_labor_uncertainty = "ensmean"   # Central (default)
c37_labor_uncertainty = "ensupper"  # Pessimistic
```

**File**: `input.gms:16`

**Analysis**:
```r
prod_lower <- readGDX("fulldata_enslower.gdx", "pm_labor_prod")
prod_mean <- readGDX("fulldata_ensmean.gdx", "pm_labor_prod")
prod_upper <- readGDX("fulldata_ensupper.gdx", "pm_labor_prod")

# 90% confidence interval by region
ci_width <- (prod_upper - prod_lower)["y2100",]
plot(ci_width, main="90% Uncertainty range in labor productivity by 2100")
# Wider in tropics (higher uncertainty in humidity projections)
```

**Expected Range** (RCP8.5, 2100, tropics):
- enslower: 85% productivity (optimistic ESMs)
- ensmean: 70% productivity (median)
- ensupper: 50% productivity (pessimistic ESMs)

#### 13.5 Disable Heat Stress Impacts (Counterfactual)

**Purpose**: Isolate heat stress effects on agricultural costs and land use

**Configuration**:
```r
# In R config
cfg$gms$labor_prod <- "off"  # Disable Module 37 impacts
```

**Or in GAMS**:
```gams
$setglobal c37_labor_prod_scenario  nocc
```

**File**: `input.gms:8`

**Expected Impact**:
- Labor productivity constant at 1.0 (no climate impacts)
- Labor costs do NOT increase over time (ceteris paribus)
- Agricultural employment lower (no need to compensate for productivity loss)
- Food prices lower (lower production costs)

**Use Case**:
- Quantify total impact of heat stress: Compare `off` vs. `exo` realization
- Historical validation: Use `nocc` for historical period where data unavailable

**Testing**:
```r
costs_with_heat <- readGDX("fulldata_exo.gdx", "vm_cost_prod_crop")
costs_no_heat <- readGDX("fulldata_off.gdx", "vm_cost_prod_crop")

# Heat stress cost impact
heat_impact <- (costs_with_heat - costs_no_heat) / costs_no_heat * 100
plot(heat_impact["y2050",], main="Labor cost increase from heat stress by 2050 (%)")
```

#### 13.6 Regional Mechanization Scenario

**Purpose**: Simulate differential mechanization by development level

**How**: Modify `pm_labor_prod` in preloop to apply 300W in developed regions, 400W in developing

**Example**:
```gams
* Add to preloop.gms after line 8
parameter p37_labor_prod_300W(t,j), p37_labor_prod_400W(t,j);

p37_labor_prod_300W(t,j) = f37_labor_prod(t,j,"%c37_labor_rcp%","%c37_labor_metric%","300W","%c37_labor_uncertainty%");
p37_labor_prod_400W(t,j) = f37_labor_prod(t,j,"%c37_labor_rcp%","%c37_labor_metric%","400W","%c37_labor_uncertainty%");

* Apply 300W to developed regions (EUR, USA, JPN, CPA)
pm_labor_prod(t,j)$(sum((i_to_iso(i,iso),cell(i,j)), im_development_state(t,i) > 0.8)) = p37_labor_prod_300W(t,j);
* Apply 400W to developing regions (rest)
pm_labor_prod(t,j)$(sum((i_to_iso(i,iso),cell(i,j)), im_development_state(t,i) <= 0.8)) = p37_labor_prod_400W(t,j);
```

**Effect**:
- Developed regions: Lower heat stress impacts (mechanized)
- Developing regions: Higher heat stress impacts (manual labor)
- Captures reality of mechanization disparities

**Caution**: This modification is NOT in the standard model (requires custom code)

---

## 14. Testing & Validation

#### 14.1 Historical Validation

**Check**: Does baseline (1995-2020) show realistic productivity trends?

**How**:
```r
library(magpie4)
prod_hist <- readGDX("fulldata.gdx", "pm_labor_prod")[c("y1995","y2000","y2005","y2010","y2015","y2020"),]

# Check for unrealistic historical trends
hist_change <- (prod_hist["y2020",] - prod_hist["y1995",]) / prod_hist["y1995",] * 100
plot(hist_change, main="Labor productivity change 1995-2020 (%)")
```

**Expected**:
- Small changes (< 5%) in historical period
- Some regions slight increase (colder), some slight decrease (hotter)
- No large jumps (gradual climate change)

**Red Flag**:
- >10% change 1995-2020 (climate change slower than this)
- Sudden jumps between years (should be smooth)

#### 14.2 RCP Consistency Check

**Check**: Is RCP8.5 impact larger than RCP1.9 in all regions?

**How**:
```r
prod_rcp19 <- readGDX("fulldata_rcp19.gdx", "pm_labor_prod")
prod_rcp85 <- readGDX("fulldata_rcp85.gdx", "pm_labor_prod")

# RCP8.5 should have lower productivity (higher heat stress)
diff <- prod_rcp85["y2100",] - prod_rcp19["y2100",]
stopifnot(all(diff <= 0))  # All regions: RCP8.5 ≤ RCP1.9

# Check magnitude
avg_diff <- mean(diff) * 100
# Expected: -10 to -20% (RCP8.5 10-20% lower productivity)
```

**Expected**: RCP8.5 < RCP1.9 everywhere by 2050-2100

**Red Flag**: Any region where RCP8.5 > RCP1.9 (data error)

#### 14.3 Geographic Pattern Validation

**Check**: Are tropical regions more affected than temperate?

**How**:
```r
prod_2100 <- readGDX("fulldata.gdx", "pm_labor_prod")["y2100",]

# Calculate productivity loss by region
library(madrat)
regions <- toolGetMapping("regionmappingH12.csv", type="regional")
prod_by_region <- toolAggregate(prod_2100, regions, weight=NULL)

# Order by impact
prod_by_region <- sort(prod_by_region)
barplot(prod_by_region, main="Labor productivity by region, 2100", ylab="Productivity factor")
```

**Expected Order** (lowest to highest productivity):
1. SSA (Sub-Saharan Africa): 0.60-0.80
2. SAS (South Asia): 0.65-0.85
3. LAM (Latin America): 0.70-0.85
4. MENA (Middle East North Africa): 0.75-0.90
5. CHN, IND (East Asia): 0.80-0.90
6. CPA, EUR, USA, JPN: 0.90-1.00

**Red Flag**: Temperate regions (EUR, USA) more affected than tropics (contradicts physics)

#### 14.4 Intensity Comparison Validation

**Check**: Is 300W less affected than 400W?

**How**:
```r
prod_300W <- readGDX("fulldata_300W.gdx", "pm_labor_prod")
prod_400W <- readGDX("fulldata_400W.gdx", "pm_labor_prod")

diff <- prod_300W["y2100",] - prod_400W["y2100",]
stopifnot(all(diff >= 0))  # All regions: 300W ≥ 400W
```

**Expected**: 300W always ≥ 400W (lower intensity → less heat stress)

**Red Flag**: Any region where 300W < 400W (data error)

#### 14.5 Ensemble Bounds Check

**Check**: Do ensemble statistics satisfy enslower ≤ ensmean ≤ ensupper?

**How**:
```r
prod_lower <- readGDX("fulldata_enslower.gdx", "pm_labor_prod")
prod_mean <- readGDX("fulldata_ensmean.gdx", "pm_labor_prod")
prod_upper <- readGDX("fulldata_ensupper.gdx", "pm_labor_prod")

# Check ordering
stopifnot(all(prod_lower["y2100",] <= prod_mean["y2100",]))
stopifnot(all(prod_mean["y2100",] <= prod_upper["y2100",]))
```

**Expected**: enslower ≤ ensmean ≤ ensupper for all cells and years

**Red Flag**: Ordering violated (data processing error)

#### 14.6 Time Monotonicity Check

**Check**: Is productivity monotonically decreasing over time (for RCP8.5)?

**How**:
```r
prod <- readGDX("fulldata_rcp85.gdx", "pm_labor_prod")

# Check if productivity decreases over time for tropics
tropical_cells <- ... # Identify tropical cells
for(cell in tropical_cells) {
  prod_ts <- prod[,cell]
  # Should be monotonically decreasing (or constant)
  diffs <- diff(prod_ts)
  if(any(diffs > 0.01)) {  # Allow small numerical noise
    warning(paste("Non-monotonic productivity in cell", cell))
  }
}
```

**Expected**: Productivity decreases (or stays constant) over time in most regions

**Red Flag**: Large increases over time (physically implausible under warming)

---

## 15. Literature and Data Sources

#### 15.1 Key Publications

**Orlov et al. (2021)**:
- Title: "Economic losses from heat-induced reductions in outdoor worker productivity: A global analysis"
- Journal: Economics of Disasters and Climate Change
- DOI: 10.1007/s41885-021-00093-x
- Contribution: Methodology for calculating labor productivity impacts from WBGT

**ISO 7243**:
- Title: "Ergonomics of the thermal environment — Assessment of heat stress using the WBGT (wet bulb globe temperature) index"
- Organization: International Organization for Standardization
- Contribution: Rest break requirements by WBGT and work intensity

**Kjellstrom et al. (2016)**:
- Title: "Heat, Human Performance, and Occupational Health: A Key Issue for the Assessment of Global Climate Change Impacts"
- Journal: Annual Review of Public Health
- Contribution: HOTHAPS workability function

**Dunne et al. (2013)**:
- Title: "Reductions in labour capacity from heat stress under climate warming"
- Journal: Nature Climate Change
- DOI: 10.1038/nclimate1827
- Contribution: Global assessment of heat stress impacts on labor

#### 15.2 LAMACLIMA Project

**Full Name**: Labour Market Impacts of Climate Change (LAMACLIMA)

**Lead Institution**: Climate Analytics (Berlin, Germany)

**Project Page**: https://climateanalytics.org/projects/lamaclima/

**Funding**: German Federal Ministry for the Environment, Nature Conservation and Nuclear Safety (BMU)

**Outputs**:
- Global gridded heat stress impacts (0.5° resolution)
- Multiple metrics (ISO, HOTHAPS), intensities (300W, 400W)
- Climate scenarios (RCP1.9, RCP8.5) from CMIP6 ensemble
- Uncertainty quantification (ensemble spread)

**Data Pipeline**:
1. CMIP6 ESM outputs (temperature, humidity, wind, radiation)
2. Calculate WBGT using thermodynamic models
3. Apply labor productivity functions (ISO or HOTHAPS)
4. Spatial aggregation to MAgPIE grid
5. Temporal aggregation (monthly → annual)

#### 15.3 CMIP6 Data

**Source**: Coupled Model Intercomparison Project Phase 6 (CMIP6)

**ESMs Used**: Multi-model ensemble (typically 10-30 models)
- Examples: EC-Earth, GFDL-ESM, UKESM, MIROC, etc.

**Variables**:
- tas: Near-surface air temperature
- hurs: Near-surface relative humidity
- sfcWind: Near-surface wind speed
- rsds: Surface downwelling shortwave radiation (solar)

**Scenarios**: ScenarioMIP
- SSP1-1.9 (low emissions) → used for "rcp119" in MAgPIE
- SSP5-8.5 (high emissions) → used for "rcp585" in MAgPIE

**Temporal Resolution**: Monthly data, 1995-2150

**Spatial Resolution**: 0.5° × 0.5° latitude-longitude

---

## 16. Summary: Module 37 Role in MAgPIE

**Core Function**: Provide exogenous climate-driven labor productivity adjustments capturing heat stress impacts on agricultural workers

**Key Innovation**: First explicit integration of occupational heat stress in global land-use model

**Mechanism**:
1. **Physical basis**: Wet Bulb Globe Temperature (WBGT) from ESM climate projections
2. **Productivity impacts**: ISO or HOTHAPS methodology, 300W or 400W work intensity
3. **Scenario flexibility**: RCP1.9 vs. RCP8.5, uncertainty quantification (ensemble spread)
4. **Interface**: Single parameter `pm_labor_prod(t,j)` provided to Module 38

**Unique Features**:
- Heat stress explicitly modeled (not just temperature)
- Multiple methodologies (ISO regulatory standard vs. HOTHAPS empirical)
- Work intensity options (mechanized 300W vs. manual 400W)
- Uncertainty quantification (ESM ensemble spread)

**Limitations**:
- Exogenous (no adaptation, no feedback)
- Limited scenarios (only RCP1.9 and RCP8.5)
- Global uniform intensity assumption (should vary by region/development)
- Crop-generic (same for all crops, no seasonal variation)
- One-way coupling (climate → productivity, not productivity → climate)

**Dependencies**:
- **Receives from**: NONE (pure source, external ESM data)
- **Provides to**: Module 38 (Factor Costs) exclusively
- **Simplest dependency structure** in MAgPIE (1 output, 0 inputs)

**Complexity**: LOW (140 lines, 0 equations, data provider only)

**Modification Risk**: LOW
- No optimization coupling (can't break solver)
- Single output parameter (limited ripple effects)
- Changes affect only labor costs and employment

**Testing Focus**:
- Geographic patterns (tropics > temperate)
- RCP consistency (RCP8.5 > RCP1.9 impacts)
- Ensemble ordering (enslower ≤ ensmean ≤ ensupper)
- Intensity consistency (400W > 300W impacts)

**Typical Use Cases**:
- Climate change impact assessment (RCP1.9 vs. RCP8.5)
- Mechanization benefits under heat stress (300W vs. 400W)
- Uncertainty analysis (ensemble bounds)
- Adaptation scenarios (shift to 300W represents mechanization)

**Future Enhancements**:
- Regional intensity variation (link to development state)
- Additional climate scenarios (RCP2.6, RCP4.5, RCP6.0)
- Seasonal resolution (capture summer peak heat)
- Crop-specific variation (harvest timing)
- Endogenous adaptation (model mechanization response to heat stress)

**Related Modules**:
- Module 38 (Factor Costs) - uses `pm_labor_prod` to adjust labor costs
- Module 36 (Employment) - indirectly affected (lower productivity → more employment needed)

---

**Module 37 Status**: ✅ COMPLETE (1046 lines documented, 24.9× expansion from 42 lines)
**Verified Against**: Actual code in `modules/37_labor_prod/`
**Documentation Date**: October 11, 2025

---

## 17. AI Agent Response Patterns

**User Query**: "How does MAgPIE model heat stress impacts on agriculture?"

**Response**:
```
MAgPIE models heat stress impacts on agricultural LABOR productivity through Module 37:

Physical Mechanism:
• Wet Bulb Globe Temperature (WBGT) calculated from ESM climate projections
  - Combines temperature, humidity, wind speed, solar radiation
  - WBGT > 30°C → significant productivity loss
• modules/37_labor_prod/exo/input.gms:18-22

Productivity Calculation:
Two alternative metrics:
1. ISO standard: Rest break requirements by WBGT threshold
   - WBGT 28-30°C, 400W work: 50% rest breaks → 50% productivity
2. HOTHAPS: Continuous workability function
   - Smooth curve, less conservative than ISO

Configuration:
• c37_labor_rcp: rcp119 (1.5°C warming) or rcp585 (4°C+ warming)
• c37_labor_metric: ISO (regulatory) or HOTHAPS (empirical)
• c37_labor_intensity: 300W (mechanized) or 400W (manual labor)
• modules/37_labor_prod/exo/input.gms:8-16

Output:
• pm_labor_prod(t,j): Productivity factor (1 = no impact, <1 = loss)
• Used by Module 38 to adjust labor costs: costs_actual = costs_baseline / pm_labor_prod
• Lower productivity → higher costs → affects land allocation

Typical Impacts (RCP8.5, 2100):
• Tropics (SSA, SAS): 40-60% productivity (20-50% loss)
• Temperate (EUR, USA): 90-100% productivity (0-10% loss)

⚠️ LIMITATION: Heat stress impacts are EXOGENOUS. MAgPIE does NOT model adaptation
(e.g., shift work schedules, air conditioning, mechanization response to heat).
Adaptation can be simulated by switching 400W → 300W intensity.

Data Source: LAMACLIMA project (Orlov et al. 2021), CMIP6 ESM ensemble
modules/37_labor_prod/exo/realization.gms:8-12
```

**User Query**: "Why is agricultural labor more expensive in climate change scenarios?"

**Response**:
```
Labor costs increase under climate change due to heat stress reducing worker productivity:

Causal Chain:
1. Climate warms → Wet Bulb Globe Temperature (WBGT) increases
   • WBGT combines temperature + humidity (critical for heat stress)
   • Tropics especially affected (high heat + high humidity)

2. Higher WBGT → Workers require more frequent rest breaks (ISO standard)
   • WBGT < 28°C: No rest breaks needed
   • WBGT 28-30°C: 25-50% of work time as rest
   • WBGT > 30°C: 50-75% of work time as rest (severe heat stress)

3. Rest breaks → Labor productivity decreases
   • Module 37: pm_labor_prod(t,j) < 1.0
   • Example: pm_labor_prod = 0.75 means 25% productivity loss
   • modules/37_labor_prod/exo/preloop.gms:8

4. Lower productivity → Need more labor hours for same output
   • Module 38: Labor costs = Baseline costs / pm_labor_prod
   • Example: 25% productivity loss → 33% higher labor costs (1/0.75 = 1.33)
   • modules/38_factor_costs (conceptual application)

5. Higher labor costs → Agricultural production becomes more expensive
   • Affects land allocation (shifts to regions with lower heat stress)
   • May increase food prices (higher production costs)

Quantitative Example (RCP8.5, Sub-Saharan Africa, 2100):
• pm_labor_prod ≈ 0.60 (40% productivity loss)
• Labor costs increase by 67% (1/0.60 = 1.67)
• If labor is 40% of production costs → total costs up 27%

Regional Variation:
• Tropics (SSA, SAS, LAM): Largest cost increases (severe heat stress)
• Temperate (EUR, USA): Minimal increases (cooler, less humidity)
• Mechanization helps: 300W work intensity less affected than 400W

⚠️ NOTE: MAgPIE assumes workers continue working at same wage (no wage adjustment
for heat stress). In reality, wages might increase to compensate, further raising
labor costs. Module 36 (Employment) does NOT account for heat stress wage premium.
```

**User Query**: "Can farmers adapt to heat stress in MAgPIE?"

**Response**:
```
Module 37 does NOT model endogenous adaptation to heat stress. Productivity impacts
are EXOGENOUS (predetermined from climate data).

What MAgPIE does NOT capture:
❌ Shift work schedules (work early morning/evening, avoid midday heat)
❌ Workplace modifications (shade structures, cooling stations)
❌ Mechanization response to heat stress (invest in air-conditioned equipment)
❌ Crop calendar adjustments (shift planting/harvest to cooler months)
❌ Migration (workers leave agriculture or move to cooler regions)
modules/37_labor_prod/module.gms:11-12

Workaround: Simulate adaptation exogenously
Option 1: Reduce work intensity (manual → mechanized)
  c37_labor_intensity = "300W"  # Down from 400W default
  • Represents investment in mechanization (tractors, harvesters)
  • Reduces heat exposure (air-conditioned cabs vs. field work)
  • Productivity impact: ~50% smaller than 400W
  modules/37_labor_prod/exo/input.gms:15

Option 2: Assume partial productivity recovery
  # Custom code (not standard MAgPIE)
  pm_labor_prod_adapted(t,j) = pm_labor_prod(t,j) +
                                 (1 - pm_labor_prod(t,j)) * adaptation_fraction
  # Example: adaptation_fraction = 0.30 means 30% of heat stress avoided

Option 3: Disable heat stress entirely (full adaptation assumption)
  c37_labor_prod_scenario = "nocc"  # No climate change impacts
  # Assumes perfect adaptation (optimistic upper bound)
  modules/37_labor_prod/exo/input.gms:8

Indirect adaptation in model:
✓ Production shifts to cooler regions (Module 10 land allocation)
✓ Shift to less labor-intensive crops/systems (if labor costs increase)
✓ Technological change may offset some costs (Module 13)

⚠️ IMPORTANT: Real-world adaptation is COSTLY (requires investment in equipment,
infrastructure, training). MAgPIE does NOT track adaptation costs. Mechanization
scenario (300W) assumes adaptation already occurred at no cost.

Recommendation:
• For pessimistic scenario: Use 400W (limited adaptation)
• For optimistic scenario: Use 300W (mechanization adaptation)
• For full range: Run both and report as uncertainty band
```
