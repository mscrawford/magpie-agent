# Module 38: Factor Costs - Comprehensive Documentation

**Location**: `modules/38_factor_costs/`
**Current Realization**: `sticky_labor` (most sophisticated)
**Authors**: Jan Philipp Dietrich, Benjamin Bodirsky, Kristine Karstens, Edna J. Molina Bacca, Debbora Leip

---

## 1. Purpose & Overview

Module 38 calculates the costs of production factors (labor and capital) in crop production activities. These costs are crop-specific and spatially explicit, influencing the model's choice of production patterns through the cost function in Module 11.

**Key Innovation**: The `sticky_labor` realization introduces capital immobility and labor-capital substitution via a CES production function, creating path dependency in agricultural land use. Existing capital stocks make it cheaper to continue production in established locations, while climate change and rising wages affect the optimal mix of labor and capital inputs.

**What Factor Costs Include**:
- Labor costs (wages × hours worked)
- Capital costs (machinery, equipment, irrigation infrastructure, buildings)

**What Factor Costs Exclude** (to avoid double-counting):
- Land rents (calculated endogenously in Module 11)
- Chemical fertilizer costs (calculated in Module 50)
- Seeds and agricultural inputs (would double-count intermediate products)

---

## 2. Three Realizations: Evolution of Approaches

### 2.1 per_ton_fao_may22: Volume-Based Costs

**Approach**: Factor costs proportional to production volume
**Data**: FAO Value of Production + USDA cost shares

**Equations** (`modules/38_factor_costs/per_ton_fao_may22/equations.gms:10-18`):
```gams
vm_cost_prod_crop(i,"labor") = sum(kcr, vm_prod_reg(i,kcr) * i38_fac_req(i,kcr))
                                * pm_factor_cost_shares(i,"labor")
                                * (wage_scenario / wage_baseline)
                                * (1/pm_productivity_gain_from_wages)

vm_cost_prod_crop(i,"capital") = sum(kcr, vm_prod_reg(i,kcr) * i38_fac_req(i,kcr))
                                 * pm_factor_cost_shares(i,"capital")
```

**Characteristics**:
- Simple linear relationship: Cost = Production × Factor_Requirements
- Factor requirements fixed over time (FAO 2005 baseline)
- No spatial incentives to concentrate production
- No labor-capital substitution

**Use Case**: Baseline scenarios, sensitivity analysis, computational efficiency

### 2.2 sticky_feb18: Introducing Capital Stickiness

**New Features**:
- Capital separated into mobile and immobile components
- Capital stocks depreciate (5% per year) and accumulate
- Investment costs annuitized to represent long-term value

**Innovation**: Creates spatial inertia - expansion favored in locations with existing capital stocks

### 2.3 sticky_labor: Full Factor Substitution (Current Default)

**Built on sticky_feb18 + adds**:
- CES production function for labor-capital substitution
- Climate change impacts on labor productivity (Module 37)
- Wage increase impacts on labor productivity (Module 36)
- Optional labor share targets (e.g., maintain rural employment)

**Location**: `modules/38_factor_costs/sticky_labor/`

---

## 3. Core Mechanism: CES Production Function

### 3.1 The CES Equation

**File**: `modules/38_factor_costs/sticky_labor/equations.gms:19-23`

```gams
q38_ces_prodfun(j,kcr) ..
  i38_ces_scale(j,kcr) *
  (i38_ces_shr(j,kcr) * sum(mobil38, v38_capital_need(j,kcr,mobil38))**(-s38_ces_elast_par) +
   (1 - i38_ces_shr(j,kcr)) * (pm_labor_prod(j) * pm_productivity_gain_from_wages(i)
                               * v38_laborhours_need(j,kcr))**(-s38_ces_elast_par)
  )**(-1/s38_ces_elast_par)
  =e= 1 + v38_relax_CES_lp(j,kcr);
```

**Mathematical Form**:
```
Y = A * [α*K^(-ρ) + (1-α)*(L_eff)^(-ρ)]^(-1/ρ)
```

Where:
- **Y** = Output (fixed at 1 per unit of crop production)
- **A** = `i38_ces_scale` = Total factor productivity (calibration parameter)
- **α** = `i38_ces_shr` = Capital share parameter (0-1)
- **K** = `v38_capital_need` = Capital per unit output (USD17MER/tDM)
- **L_eff** = Effective labor = `pm_labor_prod × pm_productivity_gain_from_wages × v38_laborhours_need`
- **ρ** = `s38_ces_elast_par` = Elasticity parameter = (1/σ) - 1 = (1/0.3) - 1 = 2.33
- **σ** = `s38_ces_elast_subst` = Elasticity of substitution = 0.3

### 3.2 Understanding Elasticity of Substitution (σ = 0.3)

**Physical Interpretation**:
- σ = 0.3 means **low substitutability** between labor and capital
- A 10% increase in relative wage leads to only ~3% reduction in labor intensity
- Agricultural capital (tractors, irrigation) cannot fully replace human labor
- Contrast with manufacturing (σ ~ 0.6-1.0) where automation is easier

**Implications**:
- Rising wages → gradual mechanization (not rapid automation)
- Climate-driven labor productivity losses → modest capital intensification
- Labor-intensive crops (vegetables, fruits) remain labor-dependent
- Capital-intensive crops (grains, oilseeds) already mechanized

**Calibration** (`modules/38_factor_costs/sticky_labor/input.gms:16`):
```gams
s38_ces_elast_subst = 0.3  ! Elasticity of substitution
```

### 3.3 Labor Productivity Adjustments

**Effective Labor** = Base Labor × Two Adjustment Factors:

1. **Climate Impacts** (`pm_labor_prod` from Module 37):
   - Heat stress reduces labor productivity (WBGT-based)
   - Range: 0.5-1.0 (50-100% productivity)
   - Tropical regions: 0.5-0.7 by 2100 under RCP8.5
   - Temperate regions: 0.9-1.0 (minimal impacts)

2. **Wage-Productivity Relationship** (`pm_productivity_gain_from_wages` from Module 36):
   - Higher wages → worker efficiency (better nutrition, health, training)
   - Efficiency elasticity with respect to wages
   - Range: 1.0-1.5 (0-50% productivity gain)
   - Based on development economics literature

**Combined Effect**:
- **Hot climate + low wages**: Labor productivity = 0.5 × 1.0 = 0.5 (severe constraint)
- **Temperate + high wages**: Labor productivity = 1.0 × 1.5 = 1.5 (optimal conditions)
- **Trade-off**: Rising wages can offset some climate impacts

---

## 4. Capital Stickiness: Immobile vs Mobile Capital

### 4.1 Capital Types

**Defined in** `modules/38_factor_costs/sticky_labor/sets.gms:9-10`:
```gams
sets mobil38 types of capital
  / mobile, immobile /
```

**Immobile Capital** (crop-specific, location-specific):
- Specialized equipment (rice transplanters, combine harvesters for specific crops)
- Crop-specific irrigation infrastructure
- Processing facilities linked to specific crops
- Storage facilities designed for particular commodities

**Mobile Capital** (location-specific, crop-flexible):
- General tractors and tillage equipment
- Transportation vehicles
- General irrigation pumps
- Farm buildings

### 4.2 Immobility Share

**Configuration** (`modules/38_factor_costs/sticky_labor/input.gms:15`):
```gams
s38_immobile = 1  ! 100% immobile by default
```

**Calculation** (`modules/38_factor_costs/sticky_labor/presolve.gms:21-22`):
```gams
p38_capital_need(t,i,kcr,"mobile") = i38_fac_req(t,i,kcr)
                                     * pm_factor_cost_shares(t,i,"capital")
                                     / (pm_interest(t,i) + s38_depreciation_rate)
                                     * (1 - s38_immobile)

p38_capital_need(t,i,kcr,"immobile") = i38_fac_req(t,i,kcr)
                                       * pm_factor_cost_shares(t,i,"capital")
                                       / (pm_interest(t,i) + s38_depreciation_rate)
                                       * s38_immobile
```

**Default (s38_immobile = 1)**:
- 100% of capital is crop-specific and location-specific
- Creates maximum "stickiness" in production patterns
- Favors expansion where capital stocks already exist
- Penalizes crop switching (must build new capital)

**Alternative (s38_immobile = 0.5)**:
- 50% immobile (crop-specific)
- 50% mobile (shared across crops)
- More flexibility for crop rotation
- Lower switching costs

### 4.3 Capital Stock Dynamics

**Initialization (t=1)** (`modules/38_factor_costs/sticky_labor/presolve.gms:84-85`):
```gams
p38_capital_immobile(t,j,kcr) = p38_capital_need(t,i,kcr,"immobile")
                                 * pm_prod_init(j,kcr)
                                 * (1 - s38_depreciation_rate)

p38_capital_mobile(t,j) = sum(kcr, p38_capital_need(t,i,kcr,"mobile")
                               * pm_prod_init(j,kcr))
                          * (1 - s38_depreciation_rate)
```
- Capital stocks estimated from 1995 production levels
- Assume one year depreciation from 1994 to 1995

**Depreciation Between Timesteps** (`modules/38_factor_costs/sticky_labor/presolve.gms:91-92`):
```gams
p38_capital_immobile(t,j,kcr) = p38_capital_immobile(t,j,kcr)
                                 * (1 - s38_depreciation_rate)**(m_timestep_length)

p38_capital_mobile(t,j) = p38_capital_mobile(t,j)
                          * (1 - s38_depreciation_rate)**(m_timestep_length)
```
- Annual depreciation rate: 5% (s38_depreciation_rate = 0.05)
- Implies ~20-year linear depreciation lifespan
- For 5-year timestep: (1-0.05)^5 = 0.774 (22.6% loss)
- For 10-year timestep: (1-0.05)^10 = 0.599 (40.1% loss)

**Investment Requirement** (`modules/38_factor_costs/sticky_labor/equations.gms:83-94`):
```gams
q38_investment_immobile(j,kcr) ..
  v38_investment_immobile(j,kcr) =g=
    vm_prod(j,kcr) * v38_capital_need(j,kcr,"immobile")
    - p38_capital_immobile(t,j,kcr)

q38_investment_mobile(j) ..
  v38_investment_mobile(j) =g=
    sum(kcr, vm_prod(j,kcr) * v38_capital_need(j,kcr,"mobile"))
    - p38_capital_mobile(t,j)
```
- Investment needed when: Required Capital > Existing Stock
- Required capital = Production × Capital per Unit Output
- If existing stock sufficient, no investment needed

**Stock Updating (Post-Solve)** (`modules/38_factor_costs/sticky_labor/postsolve.gms:9-10`):
```gams
p38_capital_immobile(t+1,j,kcr) = p38_capital_immobile(t,j,kcr)
                                   + v38_investment_immobile.l(j,kcr)

p38_capital_mobile(t+1,j) = p38_capital_mobile(t,j)
                            + v38_investment_mobile.l(j)
```
- Investment adds to capital stock for next timestep
- Creates path dependency over time

---

## 5. Cost Calculation

### 5.1 Labor Costs

**Equation** (`modules/38_factor_costs/sticky_labor/equations.gms:39-41`):
```gams
q38_cost_prod_labor(i) ..
  vm_cost_prod_crop(i,"labor") =e=
    sum(kcr, sum(cell(i,j),
      vm_prod(j,kcr) * v38_laborhours_need(j,kcr) * pm_hourly_costs(i,"scenario")
    ))
```

**Components**:
- **vm_prod(j,kcr)**: Production (tDM/yr) from Module 17
- **v38_laborhours_need(j,kcr)**: Labor hours per ton output (hours/tDM) - endogenous
- **pm_hourly_costs(i,"scenario")**: Wage rate (USD17MER/hour) from Module 36

**Calculation**:
```
Labor Cost = Production × Labor_Hours_Per_Ton × Hourly_Wage
```

**Example (India rice, 2050)**:
- Production = 100 million tDM/yr
- Labor hours = 50 hours/tDM (moderately mechanized)
- Wage = $5/hour
- Labor cost = 100M × 50 × $5 = $25 billion/yr

### 5.2 Capital Costs (Annualized Investment)

**Equation** (`modules/38_factor_costs/sticky_labor/equations.gms:46-49`):
```gams
q38_cost_prod_capital(i) ..
  vm_cost_prod_crop(i,"capital") =e=
    (sum(cell(i,j), sum(kcr, v38_investment_immobile(j,kcr)))
     + sum(cell(i,j), v38_investment_mobile(j)))
    * (pm_interest(i) + s38_depreciation_rate) / (1 + pm_interest(i))
```

**Annuitization Factor**: `(r + d) / (1 + r)`

Where:
- **r** = pm_interest(i) = Interest rate (e.g., 0.05 = 5%)
- **d** = s38_depreciation_rate = 0.05 (5% depreciation)

**Why Annuitize?**

The model must compare investment costs (one-time) to production benefits (per timestep).

**Economic Logic** (documented in `equations.gms:51-76`):

1. **True Utility**: Investment I₀ provides utility over infinite horizon:
   ```
   U_total = K₀*z * (1+r)/(r+d)
   ```
   Where z = utility per dollar of capital

2. **Model Sees Only Current Period**: MAgPIE evaluates only current utility U₀ = K₀*z

3. **Annuitization**: To make investment worthwhile, model must see cost:
   ```
   C₀ = I₀ * (r+d)/(1+r)
   ```

**Example Calculation**:
- Interest rate r = 5%
- Depreciation d = 5%
- Annuitization factor = (0.05 + 0.05)/(1 + 0.05) = 0.10/1.05 = 0.0952

- Investment = $1 billion
- Annualized cost = $1B × 0.0952 = $95.2 million/yr

**Interpretation**: A $1 billion investment appears as $95.2 million/yr cost in the model, representing the annual economic burden (interest + depreciation).

---

## 6. Labor-Capital Substitution Timeline

### 6.1 Three Phases

**Phase 1: Fixed Historical (1995-2025)** (`modules/38_factor_costs/sticky_labor/presolve.gms:67-68`):
```gams
if (m_year(t) <= s38_startyear_labor_substitution,
  v38_capital_need.fx(j,kcr,mobil38) = p38_capital_need(t,i,kcr,mobil38)
```
- Capital and labor requirements fixed to historical calibration
- CES function not active
- Ensures model matches historical patterns

**Phase 2: Transition (2025-2050)** (`modules/38_factor_costs/sticky_labor/presolve.gms:63-64`):
```gams
v38_laborhours_need.lo(j,kcr) = 0.1 * v38_laborhours_need.l(j,kcr)
v38_laborhours_need.up(j,kcr) = 10 * v38_laborhours_need.l(j,kcr)
```
- CES function activated
- Labor and capital can adjust within bounds (0.1× to 10×)
- Gradual transition to endogenous factor choice

**Phase 3: Full Flexibility (2050+)**:
- Labor-capital mix fully optimized
- Climate impacts (Module 37) fully active
- Wage-productivity feedback (Module 36) fully active

### 6.2 Configuration

**File**: `modules/38_factor_costs/sticky_labor/input.gms:17`
```gams
s38_startyear_labor_substitution = 2025
```

**Rationale**:
- Historical period (1995-2025): Match observed technology adoption
- Future (2025+): Allow endogenous mechanization response to:
  - Rising wages (labor becomes expensive)
  - Climate change (heat stress reduces labor productivity)
  - Technological change (capital becomes cheaper/better)

---

## 7. Optional Labor Share Target

### 7.1 Purpose

**Policy Goal**: Maintain minimum rural employment despite mechanization pressures

**Use Cases**:
- Food security scenarios (employment concerns)
- Rural development policies
- Social stability objectives

### 7.2 Configuration

**File**: `modules/38_factor_costs/sticky_labor/input.gms:18-20`
```gams
s38_target_labor_share = 0      ! Target labor share (0 = OFF)
s38_targetyear_labor_share = 2050  ! Year to reach target
s38_target_fulfillment = 0.5    ! Adjustment speed (50%)
```

**Default**: OFF (s38_target_labor_share = 0)

### 7.3 Enforcement Equation

**File**: `modules/38_factor_costs/sticky_labor/equations.gms:28-34`
```gams
q38_labor_share_target(j) ..
  sum(kcr, vm_prod(j,kcr) * v38_laborhours_need(j,kcr) * pm_hourly_costs(i,"scenario"))
  =g=
  p38_min_labor_share(j) *
    (sum(kcr, vm_prod(j,kcr) * v38_laborhours_need(j,kcr) * pm_hourly_costs(i,"scenario"))
     + sum((mobil38,kcr), vm_prod(j,kcr) * v38_capital_need(j,kcr,mobil38)
                          * (pm_interest(i) + s38_depreciation_rate)))
```

**Interpretation**:
```
Labor_Costs ≥ p38_min_labor_share × (Labor_Costs + Capital_Costs)
```

**Example (Target 40% labor share)**:
- Labor costs = $40M
- Capital costs = $60M
- Total = $100M
- Labor share = 40% (exactly at target)
- Constraint satisfied

If model tries to substitute to 30% labor:
- Labor costs = $30M
- Capital costs = $70M
- Total = $100M
- Labor share = 30% < 40% target
- Constraint violated → forces more labor use

### 7.4 Dynamic Target Calculation

**File**: `modules/38_factor_costs/sticky_labor/presolve.gms:25-40`

**Phase 1 (t ≤ 2025)**: No target
```gams
p38_min_labor_share(t,j) = 0
```

**Phase 2 (2025 < t ≤ 2050)**: Linear ramp
```gams
p38_min_labor_share(t,j) =
  pm_factor_cost_shares(t,i,"labor") +
  ((year(t) - 2025)/(2050 - 2025)) *
  s38_target_fulfillment * (s38_target_labor_share - pm_factor_cost_shares(2050,i,"labor"))
```

**Phase 3 (t > 2050)**: Hold at target (if below) or allow higher
```gams
if baseline_share ≤ target:
  p38_min_labor_share(t,j) = p38_min_labor_share(2050,j)  ! Hold at 2050 level
else:
  p38_min_labor_share(t,j) = max(current_share, target)  ! Allow decline to target
```

**Example Timeline (Target 40%, Fulfillment 50%)**:
- 2025: Baseline 60% → No target yet
- 2050: Target 40%, Fulfillment 50% → Minimum = 60% + 0.5×(40%-60%) = 50%
- 2075: Hold at 50% (or allow decline to 40% if baseline < 40%)

---

## 8. Data Sources and Calibration

### 8.1 Factor Requirements

**Global Average** (Default):
**File**: `modules/38_factor_costs/input/f38_fac_req_fao.csv`
- Source: FAO Value of Production (2005)
- Applied: USDA factor cost shares
- Dimension: [kcr] - crop-specific
- Units: USD17MER per tDM

**Regional Time-Varying** (Alternative):
**File**: `modules/38_factor_costs/input/f38_fac_req_fao_regional.cs4`
- Source: FAO regional data
- Dimension: [t_all, i, kcr]
- Allows regional technology differences
- Time-varying (limited to 1995, 2010 benchmarks)

**Configuration** (`modules/38_factor_costs/sticky_labor/input.gms:8`):
```gams
$setglobal c38_fac_req  glo  ! Options: glo, reg
```

### 8.2 Capital Share Calibration

**Historical Data**:
**File**: `modules/38_factor_costs/input/f38_historical_share_iso.csv`
- Source: Country-level factor cost data
- Dimension: [t_all, iso]
- Range: 0.2-0.8 (20-80% capital share)

**Regression Model** (`modules/38_factor_costs/sticky_labor/presolve.gms:14-18`):
```gams
capital_share(iso) = slope * log10(GDP_per_capita_PPP(iso)) + intercept + calibration_offset
```

**Regression Parameters**:
**File**: `modules/38_factor_costs/input/f38_regression_cap_share.csv`
```gams
/slope, intercept/
```

**Logic**:
- Wealthier countries → higher capital shares (more mechanized)
- Poorer countries → higher labor shares (labor-intensive)
- Calibration offset ensures match to historical data
- Projection: Apply regression to future GDP scenarios

**Example**:
- Low-income country: GDP per capita PPP = $2,000 → Capital share = 25%
- High-income country: GDP per capita PPP = $50,000 → Capital share = 75%

### 8.3 CES Function Calibration

**File**: `modules/38_factor_costs/sticky_labor/presolve.gms:54-56`

**Step 1: Calibrate Share Parameter (α)**:
```gams
i38_ces_shr(j,kcr) =
  (p38_intr_depr * K^(1+ρ)) /
  (p38_intr_depr * K^(1+ρ) + wage * L^(1+ρ))
```
- Ensures CES function matches baseline labor-capital ratio
- Uses historical capital and labor requirements

**Step 2: Calibrate Scale Parameter (A)**:
```gams
i38_ces_scale(j,kcr) =
  1 / ([α * K^(-ρ) + (1-α) * L^(-ρ)]^(-1/ρ))
```
- Ensures CES function produces exactly 1 unit output at baseline
- Normalizes total factor productivity

**Result**: CES function perfectly replicates baseline factor mix, but allows substitution when prices or productivity change.

---

## 9. Module Dependencies

### 9.1 Receives From

**Module 12 (Interests)**: `modules/38_factor_costs/sticky_labor/presolve.gms:21`
```gams
pm_interest(t,i)  ! Interest rate (e.g., 0.05 = 5%)
```
- Used in: Annuitization factor, capital requirement calculation
- Typical range: 2-10% depending on region and scenario

**Module 17 (Production)**: `modules/38_factor_costs/sticky_labor/equations.gms:40`
```gams
vm_prod(j,kcr)  ! Crop production (tDM/yr)
```
- Used in: Labor cost calculation, capital requirement calculation
- Core link: Production volume drives factor costs

**Module 30 (Cropland)**: `modules/38_factor_costs/sticky_labor/presolve.gms:84`
```gams
pm_prod_init(j,kcr)  ! Initial production for capital stock estimation
```
- Used in: First timestep capital stock initialization (1995)

**Module 36 (Employment)**: `modules/38_factor_costs/sticky_labor/equations.gms:22,40`
```gams
pm_hourly_costs(t,i,"scenario")           ! Wage rate (USD17MER/hour)
pm_hourly_costs(t,i,"baseline")           ! Baseline wage for comparison
pm_productivity_gain_from_wages(t,i)      ! Efficiency factor from wages (1.0-1.5)
```
- Used in: CES function (labor productivity), labor cost calculation
- Critical feedback: Rising wages → mechanization incentive

**Module 37 (Labor Productivity)**: `modules/38_factor_costs/sticky_labor/equations.gms:22`
```gams
pm_labor_prod(t,j)  ! Climate-driven labor productivity factor (0.5-1.0)
```
- Used in: CES function effective labor calculation
- Critical feedback: Heat stress → mechanization incentive

**GDP Data** (Global Input): `modules/38_factor_costs/sticky_labor/preloop.gms:15`
```gams
im_gdp_pc_ppp_iso(t,iso)  ! GDP per capita PPP for capital share regression
```
- Used in: Capital share projection (wealth → mechanization)

### 9.2 Provides To

**Module 11 (Costs)**: `modules/38_factor_costs/sticky_labor/declarations.gms:18`
```gams
vm_cost_prod_crop(i,factors)  ! Regional factor costs (mio USD17MER/yr)
                               ! factors = {labor, capital}
```
- Used in: Total production cost calculation
- Influences: Optimal crop allocation, land use patterns, food prices

### 9.3 Internal Coupling (CES Function)

The CES function creates a two-way relationship:
1. **Wage/climate → factor mix**: High wages or heat stress → more capital
2. **Factor mix → costs**: More capital → higher costs → production shifts

This creates dynamic adjustments:
- **Short run**: Fixed capital, adjust labor (limited)
- **Medium run**: Adjust capital through investment
- **Long run**: Optimize factor mix for new climate/wage conditions

---

## 10. Key Variables

### 10.1 Interface Variable (Output)

**vm_cost_prod_crop(i,factors)** - Regional factor costs
- **File**: `modules/38_factor_costs/sticky_labor/declarations.gms:18`
- **Type**: Positive variable
- **Dimensions**: [i, factors] where factors = {labor, capital}
- **Units**: mio USD17MER per yr
- **Typical Range**:
  - Labor: $10-200 billion/yr per region
  - Capital: $5-150 billion/yr per region
  - Higher in populous/intensive agriculture regions (Asia)
- **Sent to**: Module 11 (costs) via `vm_cost_prod_crop`

### 10.2 Endogenous Factor Requirements

**v38_laborhours_need(j,kcr)** - Labor hours per unit output
- **File**: `modules/38_factor_costs/sticky_labor/declarations.gms:21`
- **Type**: Positive variable (endogenous in sticky_labor, fixed in per_ton_fao)
- **Dimensions**: [j, kcr]
- **Units**: hours per ton DM
- **Bounds**: 0.1× to 10× baseline (`presolve.gms:63-64`)
- **Typical Range**: 10-200 hours/tDM
  - Low (mechanized grains): 10-30 hours/tDM
  - High (labor-intensive vegetables): 100-200 hours/tDM
- **Determined by**: CES function optimization given wages and climate

**v38_capital_need(j,kcr,mobil38)** - Capital per unit output
- **File**: `modules/38_factor_costs/sticky_labor/declarations.gms:22`
- **Type**: Positive variable (endogenous in sticky_labor after 2025)
- **Dimensions**: [j, kcr, mobil38] where mobil38 = {mobile, immobile}
- **Units**: USD17MER per ton DM
- **Bounds**: 0.1× to 10× baseline (`presolve.gms:75-76`)
- **Typical Range**: 5-50 USD/tDM
  - Low (extensive systems): 5-15 USD/tDM
  - High (irrigated, mechanized): 30-50 USD/tDM
- **Determined by**: CES function optimization given interest rates and productivity

### 10.3 Investment Variables

**v38_investment_immobile(j,kcr)** - Immobile capital investment
- **File**: `modules/38_factor_costs/sticky_labor/declarations.gms:19`
- **Type**: Positive variable
- **Dimensions**: [j, kcr]
- **Units**: mio USD17MER per yr
- **Typical Range**: $0-500 million per cell-crop
- **Determined by**: Gap between required and existing capital (`equations.gms:83-86`)

**v38_investment_mobile(j)** - Mobile capital investment
- **File**: `modules/38_factor_costs/sticky_labor/declarations.gms:20`
- **Type**: Positive variable
- **Dimensions**: [j]
- **Units**: mio USD17MER per yr
- **Typical Range**: $0-1 billion per cell
- **Determined by**: Gap between required and existing mobile capital (`equations.gms:91-94`)

### 10.4 Relaxation Variable (Linear Model Only)

**v38_relax_CES_lp(j,kcr)** - CES feasibility relaxation
- **File**: `modules/38_factor_costs/sticky_labor/declarations.gms:23`
- **Type**: Positive variable
- **Units**: Dimensionless (1)
- **Purpose**: Allow CES constraint to be slightly violated in linear model
- **Value**:
  - Non-linear model: Fixed to 0 (`presolve.gms:97`)
  - Linear model: Released (`nl_fix.gms:14-16`)
- **Reason**: Linear approximation of CES may have slight infeasibilities

---

## 11. Key Parameters

### 11.1 Capital Stocks (Dynamic State Variables)

**p38_capital_immobile(t,j,kcr)** - Immobile capital stock
- **File**: `modules/38_factor_costs/sticky_labor/declarations.gms:29`
- **Dimensions**: [t, j, kcr]
- **Units**: mio USD17MER
- **Initialized**: `presolve.gms:84` (from 1995 production)
- **Depreciated**: `presolve.gms:91` (5% annually)
- **Updated**: `postsolve.gms:9` (add investments)
- **Typical Range**: $10-1000 million per cell-crop

**p38_capital_mobile(t,j)** - Mobile capital stock
- **File**: `modules/38_factor_costs/sticky_labor/declarations.gms:30`
- **Dimensions**: [t, j]
- **Units**: mio USD17MER
- **Lifecycle**: Same as immobile
- **Typical Range**: $50-2000 million per cell

### 11.2 Factor Cost Shares

**pm_factor_cost_shares(t,i,factors)** - Labor/capital split
- **File**: `modules/38_factor_costs/sticky_labor/declarations.gms:34`
- **Dimensions**: [t, i, factors] where factors = {labor, capital}
- **Units**: Dimensionless (share, 0-1)
- **Calculated**: `preloop.gms:21-24` (from historical data + GDP regression)
- **Typical Range**:
  - Low-income regions: Labor 70-80%, Capital 20-30%
  - High-income regions: Labor 20-30%, Capital 70-80%
- **Sent to**: Other modules via `pm_` interface
- **Note**: Shares sum to 1 (labor + capital = 100%)

### 11.3 CES Calibration Parameters

**i38_ces_shr(j,kcr)** - Capital share in CES function (α)
- **File**: `modules/38_factor_costs/sticky_labor/declarations.gms:39`
- **Dimensions**: [j, kcr]
- **Units**: Dimensionless (0-1)
- **Calculated**: `presolve.gms:55` (calibrated to baseline factor mix)
- **Typical Range**: 0.3-0.7 (matches pm_factor_cost_shares roughly)

**i38_ces_scale(j,kcr)** - Total factor productivity in CES (A)
- **File**: `modules/38_factor_costs/sticky_labor/declarations.gms:40`
- **Dimensions**: [j, kcr]
- **Units**: Dimensionless (1)
- **Calculated**: `presolve.gms:56` (calibrated to produce 1 unit output)
- **Typical Range**: 0.8-1.2 (close to 1 by construction)

### 11.4 Target Parameters

**p38_min_labor_share(t,j)** - Minimum labor share enforcement
- **File**: `modules/38_factor_costs/sticky_labor/declarations.gms:35`
- **Dimensions**: [t, j]
- **Units**: Dimensionless (0-1)
- **Calculated**: `presolve.gms:25-45` (ramp to target)
- **Default**: 0 (off)
- **Active**: Only if s38_target_labor_share > 0

---

## 12. Key Scalars (Configuration)

**s38_depreciation_rate** - Annual capital depreciation
- **File**: `modules/38_factor_costs/sticky_labor/input.gms:13`
- **Value**: 0.05 (5% per year)
- **Interpretation**: 20-year linear depreciation (1/20 = 0.05)
- **Range**: 0.03-0.10 (3-10%, depending on asset type)

**s38_immobile** - Immobile capital share
- **File**: `modules/38_factor_costs/sticky_labor/input.gms:15`
- **Value**: 1 (100% immobile)
- **Interpretation**: All capital is crop-specific and location-specific
- **Range**: 0-1 (0% to 100%)

**s38_ces_elast_subst** - Elasticity of substitution (σ)
- **File**: `modules/38_factor_costs/sticky_labor/input.gms:16`
- **Value**: 0.3
- **Interpretation**: Low substitutability (agricultural constraints)
- **Converted to**: s38_ces_elast_par = (1/0.3) - 1 = 2.33 (`preloop.gms:9`)

**s38_startyear_labor_substitution** - Year to activate CES
- **File**: `modules/38_factor_costs/sticky_labor/input.gms:17`
- **Value**: 2025
- **Interpretation**: Historical lock until 2025, endogenous after

**s38_target_labor_share** - Target labor share
- **File**: `modules/38_factor_costs/sticky_labor/input.gms:18`
- **Value**: 0 (OFF)
- **Interpretation**: No minimum labor share enforcement
- **Range**: 0-1 (0% to 100%)

**s38_targetyear_labor_share** - Year to reach target
- **File**: `modules/38_factor_costs/sticky_labor/input.gms:19`
- **Value**: 2050
- **Interpretation**: Linear ramp from 2025 to 2050

**s38_target_fulfillment** - Adjustment speed to target
- **File**: `modules/38_factor_costs/sticky_labor/input.gms:20`
- **Value**: 0.5 (50%)
- **Interpretation**: Close 50% of gap to target by 2050

---

## 13. Code Truth: DOES

1. **Calculates crop-specific factor costs** separated into labor and capital components, based on production volumes, factor requirements, wages, and interest rates (`equations.gms:39-49`)

2. **Implements CES production function** with elasticity of substitution σ=0.3 to allow labor-capital substitution after 2025 (`equations.gms:19-23`, `input.gms:16-17`)

3. **Incorporates climate change impacts** on labor productivity via pm_labor_prod from Module 37, reducing effective labor in hot climates (`equations.gms:22`)

4. **Incorporates wage-productivity feedback** via pm_productivity_gain_from_wages from Module 36, increasing labor efficiency with rising wages (`equations.gms:22`)

5. **Creates capital stickiness** by separating capital into immobile (crop-specific, 100% by default) and mobile (crop-shared) types, with depreciation and accumulation dynamics (`sets.gms:9-10`, `input.gms:15`, `presolve.gms:84-92`, `postsolve.gms:9-10`)

6. **Annuitizes investment costs** using factor (r+d)/(1+r) to represent long-term economic value of capital in current-period optimization (`equations.gms:46-49`)

7. **Maintains historical factor requirements** fixed until 2025 (s38_startyear_labor_substitution), then allows endogenous adjustment (`presolve.gms:67-77`, `input.gms:17`)

8. **Supports optional labor share target** to enforce minimum rural employment, with linear ramp from baseline to target between 2025-2050 (`equations.gms:28-34`, `presolve.gms:25-45`, `input.gms:18-20`)

9. **Calibrates capital shares to GDP per capita** using regression on historical data, projecting mechanization trends with economic development (`preloop.gms:14-24`)

10. **Provides three realizations** with increasing sophistication: per_ton_fao_may22 (simple volume-based), sticky_feb18 (capital stocks), sticky_labor (full CES with climate/wages) (`module.gms:22-24`)

11. **Estimates initial capital stocks** from 1995 production levels with one year depreciation, creating starting conditions for dynamic capital accumulation (`presolve.gms:84-85`)

12. **Triggers investment only when needed**, requiring new capital only when production demands exceed existing (depreciated) stocks (`equations.gms:83-94`)

---

## 14. Code Truth: Does NOT

1. **Does not model livestock factor costs** - only crop production factor costs are calculated; livestock costs handled separately elsewhere

2. **Does not include land rent** - excluded to avoid double-counting with endogenous land rent calculation in Module 11

3. **Does not include fertilizer costs** - excluded to avoid double-counting with Module 50 (nitrogen soil budget)

4. **Does not include seeds, pesticides, or intermediate inputs** - excluded to avoid double-counting of agricultural products used as inputs

5. **Does not differentiate capital types beyond mobility** - all capital aggregated into "mobile" and "immobile" categories; no distinction between machinery, irrigation, buildings, etc.

6. **Does not model capital reallocation** - immobile capital is crop-specific and cannot be transferred to other crops; must depreciate before switching

7. **Does not model within-region capital mobility** - mobile capital pooled at cell level, not transferable between cells within a region

8. **Does not model technological change in factor productivity** - CES scale parameter i38_ces_scale fixed after calibration; no exogenous productivity growth

9. **Does not model vintage effects** - all capital of same type treated identically regardless of age (beyond depreciation)

10. **Does not model maintenance costs separately** - maintenance implicitly included in depreciation rate (5%/yr)

11. **Does not model capital utilization rates** - assumes full utilization of capital stocks; no idle capacity

12. **Does not model seasonal labor variation** - annual average labor requirements; no planting/harvest peaks

13. **Does not model labor types/skills** - all labor aggregated; no distinction between skilled and unskilled workers

14. **Does not model off-farm employment** - labor assumed to be allocated to agriculture; no opportunity cost from non-farm wages

15. **Does not allow capital mobility between regions** - capital stocks cell-specific; international capital flows not modeled

16. **Does not model learning-by-doing** - no endogenous cost reductions from cumulative investment or production

17. **Does not model economies of scale at farm level** - factor requirements per ton constant regardless of farm/field size

18. **Does not model financial constraints** - investment always feasible if economically optimal; no credit limits or liquidity constraints

---

## 15. Common Modifications

### 15.1 Use Regional Factor Requirements

**Change**: Switch from global average to region-specific factor requirements

**Files to modify**:
`modules/38_factor_costs/sticky_labor/input.gms:8`
```gams
$setglobal c38_fac_req  reg  ! Was: glo
```

**Effect**:
- Asia: Lower factor costs (labor-abundant)
- North America: Higher capital costs (mechanized)
- Africa: Higher labor costs per ton (lower productivity)
- Europe: Higher overall costs (high wages + mechanization)

**Use case**: Regional technology heterogeneity, development scenarios

### 15.2 Increase Capital Mobility

**Change**: Allow more capital sharing across crops

**Files to modify**:
`modules/38_factor_costs/sticky_labor/input.gms:15`
```gams
s38_immobile = 0.5  ! Was: 1 (50% immobile, 50% mobile)
```

**Effect**:
- Easier crop switching (lower sunk costs)
- More dynamic crop rotation patterns
- Faster response to price shocks
- Less path dependency in land use

**Use case**: Policy reforms enabling capital reallocation, crop diversification scenarios

### 15.3 Adjust Substitution Elasticity

**Change**: Make labor and capital more substitutable

**Files to modify**:
`modules/38_factor_costs/sticky_labor/input.gms:16`
```gams
s38_ces_elast_subst = 0.6  ! Was: 0.3 (double substitutability)
```

**Effect**:
- Stronger mechanization response to wage increases
- Stronger mechanization response to heat stress
- More capital-intensive agriculture in future
- Lower agricultural employment

**Use case**: Automation scenarios, technological breakthrough scenarios

**Warning**: Literature suggests 0.3 is realistic for agriculture; higher values may overestimate automation potential.

### 15.4 Enforce Minimum Labor Share

**Change**: Maintain 40% labor share to preserve rural employment

**Files to modify**:
`modules/38_factor_costs/sticky_labor/input.gms:18-20`
```gams
s38_target_labor_share = 0.4       ! Was: 0 (set to 40%)
s38_targetyear_labor_share = 2050  ! Keep
s38_target_fulfillment = 0.5       ! Keep (50% adjustment)
```

**Effect**:
- Agricultural employment maintained above baseline
- Higher production costs (prevented optimization)
- More labor-intensive agriculture
- Possible food price increases

**Use case**: Social policy scenarios, food security with employment objectives, inclusive growth

### 15.5 Change Depreciation Rate

**Change**: Assume longer capital lifetime (slower depreciation)

**Files to modify**:
`modules/38_factor_costs/sticky_labor/input.gms:13`
```gams
s38_depreciation_rate = 0.033  ! Was: 0.05 (3.3% = 30-year lifetime)
```

**Effect**:
- Capital stocks persist longer
- Lower annualized capital costs
- Stronger path dependency (capital lasts longer)
- Less frequent reinvestment

**Use case**: Durable infrastructure scenarios (irrigation), developing country context (longer use of old equipment)

### 15.6 Delay Labor Substitution Start Year

**Change**: Keep factor mix fixed until 2035 (extend historical period)

**Files to modify**:
`modules/38_factor_costs/sticky_labor/input.gms:17`
```gams
s38_startyear_labor_substitution = 2035  ! Was: 2025
```

**Effect**:
- Mechanization response delayed by 10 years
- More labor-intensive agriculture in 2025-2035
- Historical trends extended longer
- Abrupt adjustment after 2035

**Use case**: Technological lock-in scenarios, slow adoption scenarios

---

## 16. Testing & Validation

### 16.1 Check Factor Cost Components

**Objective**: Verify labor and capital costs are reasonable

**GDX Variables**:
- `vm_cost_prod_crop` - Regional factor costs (mio USD17MER/yr)
- `vm_prod` - Production (tDM/yr)

**R Code**:
```r
library(magpie4)
library(magclass)

gdx <- "fulldata.gdx"

# Read costs and production
costs_labor <- readGDX(gdx, "ov_cost_prod_crop", select=list(type="level", factors="labor"))
costs_capital <- readGDX(gdx, "ov_cost_prod_crop", select=list(type="level", factors="capital"))
prod <- readGDX(gdx, "ov_prod_reg", select=list(type="level"))

# Calculate cost per ton
costs_total <- costs_labor + costs_capital
cost_per_ton <- costs_total / prod

# Check ranges
print("Cost per ton (USD17MER/tDM):")
print(range(cost_per_ton["y2020",,], na.rm=TRUE))  # Should be 50-300

# Check labor share
labor_share <- costs_labor / costs_total
print("Labor share (dimensionless):")
print(range(labor_share["y2020",,], na.rm=TRUE))  # Should be 0.2-0.8

# Visualize trends
plot(costs_total["y1995:y2100", "GLO",],
     main="Global Factor Costs",
     ylab="Costs (billion USD/yr)")
```

**Expected Results**:
- Cost per ton: 50-300 USD17MER/tDM (higher for labor-intensive crops)
- Labor share: 20-80% (lower in high-income regions)
- Trend: Rising costs over time (wage growth + mechanization)

**Red Flags**:
- Cost per ton < 20 USD/tDM → unrealistically cheap production
- Labor share > 90% or < 10% → extreme mechanization/labor intensity
- Flat trends → factor costs not responding to wages/climate

### 16.2 Check Capital Stock Dynamics

**Objective**: Verify capital depreciates and accumulates correctly

**GDX Variables**:
- `p38_capital_immobile` - Immobile capital stocks
- `v38_investment_immobile` - Immobile investments

**R Code**:
```r
library(gdxrrw)

# Read parameters directly (not standard outputs)
igdx("/path/to/gams")
stocks <- rgdx.param(gdx, "p38_capital_immobile", squeeze=FALSE)
invest <- rgdx.param(gdx, "ov38_investment_immobile", squeeze=FALSE)

# Convert to magclass objects
stocks_mc <- as.magpie(stocks)
invest_mc <- as.magpie(invest)

# Check depreciation between timesteps (example: 2020 to 2030)
stock_2020 <- stocks_mc["y2020",,]
stock_2030_expected <- stock_2020 * (1-0.05)^10  # 10 years depreciation
stock_2030_actual <- stocks_mc["y2030",,] - invest_mc["y2030",,] * 10  # Remove investments

# Check match (should be close)
diff <- stock_2030_actual - stock_2030_expected
print("Depreciation error (should be near zero):")
print(max(abs(diff), na.rm=TRUE))

# Visualize capital trajectory
cell_crop <- "AFR.1.tece"  # Example: Africa, cell 1, temperate cereals
plot(stocks_mc[,cell_crop,], main=paste("Capital Stock:", cell_crop), ylab="Stock (mio USD)")
```

**Expected Results**:
- Depreciation matches formula: Stock(t+1) = Stock(t)×(1-0.05)^years + Investment(t)
- Capital stocks decline in contracting sectors
- Capital stocks rise in expanding sectors
- Smooth transitions (no jumps except investment events)

**Red Flags**:
- Depreciation error > 1% → calculation bug
- Negative stocks → investment formula wrong
- Stocks growing without production growth → unrealistic accumulation

### 16.3 Check CES Function Response to Wages

**Objective**: Verify mechanization responds to wage increases

**Setup**: Run two scenarios
1. Baseline wages (SSP2)
2. High wages (+50%)

**GDX Variables**:
- `v38_laborhours_need` - Labor per ton (hours/tDM)
- `v38_capital_need` - Capital per ton (USD/tDM)

**R Code**:
```r
gdx_base <- "fulldata_ssp2_baseline.gdx"
gdx_high <- "fulldata_ssp2_highwage.gdx"

# Read factor requirements
labor_base <- readGDX(gdx_base, "ov38_laborhours_need", select=list(type="level"))
labor_high <- readGDX(gdx_high, "ov38_laborhours_need", select=list(type="level"))

capital_base <- readGDX(gdx_base, "ov38_capital_need", select=list(type="level"))
capital_high <- readGDX(gdx_high, "ov38_capital_need", select=list(type="level"))

# Calculate changes (2050)
labor_change <- (labor_high["y2050",,] - labor_base["y2050",,]) / labor_base["y2050",,] * 100
capital_change <- (capital_high["y2050",,] - capital_base["y2050",,]) / capital_base["y2050",,] * 100

# Check direction and magnitude
print("Labor change with +50% wage (%):")
print(mean(labor_change, na.rm=TRUE))  # Should be -10% to -20% (substitution)

print("Capital change with +50% wage (%):")
print(mean(capital_change, na.rm=TRUE))  # Should be +5% to +15% (substitution)

# Visualize substitution
plot(labor_change, capital_change,
     xlab="Labor Change (%)", ylab="Capital Change (%)",
     main="Labor-Capital Substitution Response")
abline(h=0, v=0, col="gray")
```

**Expected Results**:
- Higher wages → 10-20% labor reduction
- Higher wages → 5-15% capital increase
- Negative correlation (substitution)
- Larger response in flexible crops (grains) than sticky crops

**Red Flags**:
- No response → CES function not active
- Positive labor response → wrong sign (complementarity instead of substitution)
- Extreme response (>50%) → elasticity too high or unbounded variables

### 16.4 Check Climate Impacts on Factor Mix

**Objective**: Verify heat stress drives mechanization

**Setup**: Compare RCP1.9 vs RCP8.5 scenarios

**GDX Variables**:
- `pm_labor_prod` - Climate-driven labor productivity (from Module 37)
- `v38_laborhours_need` - Labor per ton
- `v38_capital_need` - Capital per ton

**R Code**:
```r
gdx_rcp19 <- "fulldata_rcp19.gdx"
gdx_rcp85 <- "fulldata_rcp85.gdx"

# Read labor productivity factors
labprod_rcp19 <- readGDX(gdx_rcp19, "pm_labor_prod")
labprod_rcp85 <- readGDX(gdx_rcp85, "pm_labor_prod")

# Read factor requirements
labor_rcp19 <- readGDX(gdx_rcp19, "ov38_laborhours_need", select=list(type="level"))
labor_rcp85 <- readGDX(gdx_rcp85, "ov38_laborhours_need", select=list(type="level"))

capital_rcp19 <- readGDX(gdx_rcp19, "ov38_capital_need", select=list(type="level"))
capital_rcp85 <- readGDX(gdx_rcp85, "ov38_capital_need", select=list(type="level"))

# Focus on tropical regions (severe heat stress)
tropics <- c("LAM", "SSA", "SAS", "PAS")

# Calculate 2100 differences
labprod_diff <- labprod_rcp85["y2100",tropics] - labprod_rcp19["y2100",tropics]  # Should be negative
labor_diff <- labor_rcp85["y2100",tropics,] - labor_rcp19["y2100",tropics,]
capital_diff <- capital_rcp85["y2100",tropics,] - capital_rcp19["y2100",tropics,]

# Check causality
print("Labor productivity loss (RCP8.5 vs RCP1.9):")
print(mean(labprod_diff, na.rm=TRUE))  # Should be -0.1 to -0.3 (10-30% loss)

print("Labor hours increase to compensate (%):")
print(mean(labor_diff / labor_rcp19["y2100",tropics,] * 100, na.rm=TRUE))  # Partial compensation

print("Capital increase (substitution, %):")
print(mean(capital_diff / capital_rcp19["y2100",tropics,] * 100, na.rm=TRUE))  # Should be positive

# Scatter plot
plot(labprod_diff, capital_diff,
     xlab="Labor Productivity Loss", ylab="Capital Increase (USD/tDM)",
     main="Climate-Driven Mechanization")
abline(lm(capital_diff ~ labprod_diff), col="red")  # Should be negative slope
```

**Expected Results**:
- RCP8.5 → 10-30% labor productivity loss in tropics by 2100
- RCP8.5 → 5-15% more capital per ton (mechanization response)
- RCP8.5 → modest labor increase (partial compensation for productivity loss)
- Temperate regions: minimal changes

**Red Flags**:
- No climate effect on factor mix → Module 37 not active or CES not responding
- More labor in RCP8.5 than RCP1.9 without capital increase → inefficient response
- Extreme mechanization (>50% capital increase) → unrealistic substitution

### 16.5 Check Historical Calibration (1995-2020)

**Objective**: Verify model reproduces historical factor cost patterns

**GDX Variables**:
- `pm_factor_cost_shares` - Calibrated labor/capital shares
- `f38_historical_share` - Historical data

**R Code**:
```r
library(gdxrrw)
igdx("/path/to/gams")

gdx <- "fulldata.gdx"

# Read calibrated shares
calib_shares <- rgdx.param(gdx, "pm_factor_cost_shares", squeeze=FALSE)
hist_shares <- rgdx.param(gdx, "f38_historical_share", squeeze=FALSE)

# Convert to magclass
calib_mc <- as.magpie(calib_shares)
hist_mc <- as.magpie(hist_shares)

# Compare 2010 (last historical benchmark)
calib_2010 <- calib_mc["y2010",,"capital"]
hist_2010 <- hist_mc["y2010",,]

# Check match
error <- calib_2010 - hist_2010
print("Calibration error 2010 (capital share):")
print(summary(as.vector(error)))  # Should be near zero

# Check GDP relationship
gdp <- rgdx.param(gdx, "im_gdp_pc_ppp_iso", squeeze=FALSE)
gdp_mc <- as.magpie(gdp)

plot(log10(gdp_mc["y2010",,]), calib_2010,
     xlab="log10(GDP per capita PPP)", ylab="Capital Share",
     main="Capital Share vs GDP (2010)")
# Should show positive correlation (richer → more capital)

# Check projection trends
plot(calib_mc[,"GLO","capital"],
     main="Global Capital Share Projection",
     ylab="Capital Share")
# Should show rising trend (global wealth increase)
```

**Expected Results**:
- 2010 calibration error < 5 percentage points
- Capital share increases with GDP per capita
- Future capital share rising (mechanization trend)
- Regional differences: Asia mechanizing faster than Africa

**Red Flags**:
- Large calibration error → regression parameters wrong
- No GDP correlation → calibration not working
- Declining capital share → counter to development trends

### 16.6 Check Labor Share Target Enforcement

**Objective**: Verify labor share constraint works (if activated)

**Setup**: Run scenario with s38_target_labor_share = 0.4

**GDX Variables**:
- `vm_cost_prod_crop` - Factor costs by type
- `oq38_labor_share_target` - Shadow price of constraint

**R Code**:
```r
gdx_target <- "fulldata_laborshare40.gdx"
gdx_free <- "fulldata_baseline.gdx"

# Read costs
costs_labor_target <- readGDX(gdx_target, "ov_cost_prod_crop", select=list(type="level", factors="labor"))
costs_capital_target <- readGDX(gdx_target, "ov_cost_prod_crop", select=list(type="level", factors="capital"))

costs_labor_free <- readGDX(gdx_free, "ov_cost_prod_crop", select=list(type="level", factors="labor"))
costs_capital_free <- readGDX(gdx_free, "ov_cost_prod_crop", select=list(type="level", factors="capital"))

# Calculate labor shares
labor_share_target <- costs_labor_target / (costs_labor_target + costs_capital_target)
labor_share_free <- costs_labor_free / (costs_labor_free + costs_capital_free)

# Check enforcement (2050, when target should be partially met)
print("Labor share 2050 (target scenario):")
print(summary(labor_share_target["y2050",,]))  # Should be ≥0.4 (or moving toward it)

print("Labor share 2050 (free scenario):")
print(summary(labor_share_free["y2050",,]))  # Baseline for comparison

# Check shadow prices (binding constraint)
shadow <- readGDX(gdx_target, "oq38_labor_share_target", select=list(type="marginal"))
print("Share of cells with binding constraint:")
print(sum(shadow["y2050",,] > 0, na.rm=TRUE) / length(shadow["y2050",,]))  # >0 means binding

# Visualize impact
plot(labor_share_free["y2050",,], labor_share_target["y2050",,],
     xlab="Free Labor Share", ylab="Target Labor Share",
     main="Target Enforcement (2050)")
abline(a=0, b=1, col="gray")
abline(h=0.4, col="red", lty=2)  # Target line
```

**Expected Results**:
- Target scenario: 50% of regions moved halfway toward 40% target by 2050 (if s38_target_fulfillment=0.5)
- Binding constraint: Shadow price >0 in regions where baseline < target
- Higher labor share → higher total costs (prevented optimization)

**Red Flags**:
- No change between scenarios → constraint not active
- Labor share below target in 2050+ → constraint violated
- No shadow prices → constraint never binding (target too low)

---

## 17. Literature and Data Sources

### 17.1 Peer-Reviewed Literature

**CES Function and Labor Productivity**:
- **Orlov et al. (2021)**: "Incorporating climate change impacts on labor productivity into model-based policy analysis", *Environmental Research Letters*
  - CES function specification for agriculture
  - Labor-capital substitution elasticity
  - Integration of heat stress impacts (Module 37 linkage)
  - File reference: `equations.gms:17`

**Factor Cost Economics**:
- **Dietrich et al. (2014)**: "Measuring agricultural land-use intensity – A global analysis using a model-based approach", *Ecological Modelling*
  - FAO Value of Production methodology
  - Factor cost share estimation

**Capital Depreciation**:
- **Hertel (1999)**: "Global Trade Analysis: Modeling and Applications", Cambridge University Press
  - Agricultural capital depreciation rates (5% standard)
  - Annuitization of investment costs

**Elasticity of Substitution**:
- **Mundlak & Hellinghausen (1982)**: "The Intercountry Agricultural Production Function", *American Journal of Agricultural Economics*
  - Estimates σ = 0.2-0.4 for agriculture (Module uses 0.3)

- **Duffy & Papageorgiou (2000)**: "A cross-country empirical investigation of the aggregate production function specification", *Journal of Economic Growth*
  - General substitution elasticities (agriculture lower than manufacturing)

### 17.2 Data Sources

**FAO Value of Production**:
- Source: FAOSTAT (2005 benchmark)
- URL: https://www.fao.org/faostat/en/#data/QV
- Used in: `f38_fac_req_fao.csv`, `f38_fac_req_fao_regional.cs4`
- Coverage: ~150 crops, global and regional

**USDA Cost of Production**:
- Source: USDA Economic Research Service
- URL: https://www.ers.usda.gov/data-products/commodity-costs-and-returns/
- Used in: Factor cost share estimation
- Note: U.S.-specific data extrapolated globally with adjustments

**Historical Factor Costs**:
- Source: GTAP database + national agricultural accounts
- Used in: `f38_historical_share_iso.csv`, `f38_hist_factor_costs_iso.csv`
- Coverage: 1995-2010 country-level data

**GDP per Capita (PPP)**:
- Source: World Bank Development Indicators + SSP scenarios
- Used in: Capital share regression (`im_gdp_pc_ppp_iso`)
- Coverage: 1995-2100

### 17.3 Model Documentation

**MAgPIE Model Documentation**:
- Dietrich, J.P., et al. (2020): "MAgPIE 4 – a modular open-source framework for modeling global land systems", *Geoscientific Model Development*
- URL: https://doi.org/10.5194/gmd-12-1299-2019

**Module Development History**:
- per_ton_fao_may22: FAO-based volume costs (Bodirsky, Molina Bacca)
- sticky_feb18: Capital stickiness introduction (Dietrich, Karstens)
- sticky_labor: CES + climate/wage integration (Leip, Orlov et al.)

---

## 18. Summary for AI Agents

### 18.1 Module Identity

**Name**: Factor Costs (Module 38)
**Purpose**: Calculate labor and capital costs for crop production
**Current Realization**: `sticky_labor` (most sophisticated)
**Key Innovation**: Capital stickiness + labor-capital substitution via CES function + climate/wage impacts

### 18.2 Critical Mechanisms

1. **CES Production Function** (`equations.gms:19-23`):
   - Elasticity of substitution σ = 0.3 (low, agriculture-appropriate)
   - Labor efficiency affected by climate (Module 37) and wages (Module 36)
   - Active only after 2025 (historical lock before)

2. **Capital Stickiness** (`presolve.gms:84-92`, `postsolve.gms:9-10`):
   - 100% immobile by default (crop-specific, location-specific)
   - 5% annual depreciation (20-year lifetime)
   - Investment only when required > existing stock
   - Creates path dependency in land use

3. **Cost Calculation** (`equations.gms:39-49`):
   - Labor: Production × Hours/ton × Wage
   - Capital: Annuitized investment × (r+d)/(1+r)
   - Regional aggregation to Module 11

### 18.3 Key Dependencies

**Receives From**:
- Module 17: Production (vm_prod) - core driver
- Module 36: Wages, wage-productivity (pm_hourly_costs, pm_productivity_gain_from_wages)
- Module 37: Climate impacts on labor (pm_labor_prod)
- Module 12: Interest rates (pm_interest)

**Provides To**:
- Module 11: Factor costs (vm_cost_prod_crop) → total costs → production patterns

### 18.4 Common Misconceptions

1. **"Factor costs are fixed per ton"** - Only true in per_ton_fao realization; sticky_labor allows endogenous substitution

2. **"All capital is mobile"** - Default is 100% immobile (crop-specific)

3. **"Labor-capital substitution is immediate"** - Only active after 2025, CES prevents rapid shifts

4. **"Factor costs include everything"** - Excludes land rent, fertilizer, seeds (avoid double-counting)

5. **"Module 38 drives employment"** - Calculates costs; employment in Module 36

### 18.5 Debugging Decision Tree

**Issue: Factor costs seem too low/high**
→ Check `c38_fac_req` setting (glo vs reg)
→ Check pm_factor_cost_shares (labor/capital split)
→ Check pm_hourly_costs (wage levels from Module 36)

**Issue: No mechanization response to wages/climate**
→ Check m_year(t) > s38_startyear_labor_substitution (2025)
→ Check v38_laborhours_need bounds (should be 0.1× to 10×)
→ Check pm_labor_prod and pm_productivity_gain_from_wages values

**Issue: Unrealistic crop switching patterns**
→ Check s38_immobile (should be 0.8-1.0 for realism)
→ Check capital stock depreciation (5% realistic)
→ Check p38_capital_immobile values (sufficient stickiness?)

**Issue: Labor share target not working**
→ Check s38_target_labor_share > 0 (default OFF)
→ Check oq38_labor_share_target marginals (constraint binding?)
→ Check p38_min_labor_share values (ramp working?)

---

## 19. AI Agent Response Patterns

### Query: "Why is agriculture becoming more capital-intensive in my scenario?"

**Response Structure**:

1. **Identify Drivers**: Check three potential causes:
   - Rising wages (Module 36: pm_hourly_costs increasing)
   - Heat stress (Module 37: pm_labor_prod declining)
   - Both combined

2. **Quantify Effect**: Compare scenarios:
```r
# Read labor productivity and wages
labprod <- readGDX(gdx, "pm_labor_prod")  # From Module 37
wages <- readGDX(gdx, "pm_hourly_costs", select=list(scenario="scenario"))  # From Module 36

# Check trends
plot(labprod["y1995:y2100", "LAM",], main="Labor Productivity (Climate)")
plot(wages["y1995:y2100", "LAM",], main="Hourly Wages")
```

3. **Explain Mechanism**: CES function in Module 38:
   - Effective labor = pm_labor_prod × pm_productivity_gain_from_wages × base_labor
   - When effective labor drops (climate) or becomes expensive (wages) → substitute capital
   - Elasticity σ=0.3 → 10% wage increase → ~3% labor reduction

4. **Verify Factor Mix**:
```r
labor_need <- readGDX(gdx, "ov38_laborhours_need", select=list(type="level"))
capital_need <- readGDX(gdx, "ov38_capital_need", select=list(type="level"))
```

5. **Expected Answer**:
   - "Agriculture mechanizing due to [X% wage increase / Y% labor productivity loss]"
   - "CES function substituting toward capital (σ=0.3)"
   - "Labor per ton decreased by Z%, capital per ton increased by W%"
   - "This is economically optimal given factor prices and productivity"

---

### Query: "Why is cropland expansion favored in existing agricultural regions?"

**Response Structure**:

1. **Identify Stickiness Mechanism**: Module 38 capital stocks
   - File: `modules/38_factor_costs/sticky_labor/presolve.gms:84-92`
   - Immobile capital: 100% by default (s38_immobile = 1)
   - Depreciation: 5% per year

2. **Explain Cost Advantage**:
```gams
# Investment requirement (equations.gms:83-86):
v38_investment_immobile(j,kcr) =g=
  vm_prod(j,kcr) * v38_capital_need(j,kcr,"immobile") - p38_capital_immobile(t,j,kcr)
```
   - Existing production: p38_capital_immobile > 0 → lower/zero investment
   - New production: p38_capital_immobile = 0 → full investment required
   - Cost difference: ~50-150 USD/tDM × production

3. **Quantify Path Dependency**:
```r
# Check capital stocks
capital_stocks <- rgdx.param(gdx, "p38_capital_immobile")
investments <- readGDX(gdx, "ov38_investment_immobile", select=list(type="level"))

# Compare costs: expansion in existing vs new regions
cost_existing <- investments[existing_cells] / production[existing_cells]
cost_new <- investments[new_cells] / production[new_cells]
```

4. **Check Alternative Drivers**: Not just Module 38!
   - Module 14: Higher yields in established regions (management calibration)
   - Module 13: Technological change concentrated in intensive areas
   - Module 59: Better soil quality in established cropland

5. **Expected Answer**:
   - "Capital stickiness in Module 38 creates ~$X billion cost advantage for existing regions"
   - "Depreciation rate 5%/yr → stocks persist 10-20 years"
   - "Also check: yield levels (Module 14), technology (Module 13), soil (Module 59)"
   - "To reduce stickiness: decrease s38_immobile or increase s38_depreciation_rate"

---

### Query: "How do I modify the model to test rapid automation scenarios?"

**Response Structure**:

1. **Identify Relevant Parameters**:
   - Primary: `s38_ces_elast_subst` (elasticity of substitution)
   - Secondary: `s38_startyear_labor_substitution` (when substitution starts)
   - Tertiary: `s38_immobile` (capital mobility)

2. **Suggest Modifications**:

**Option A: Higher Substitution Elasticity** (easier automation)
```gams
# modules/38_factor_costs/sticky_labor/input.gms:16
s38_ces_elast_subst = 0.6  ! Was: 0.3 (double substitutability)
```
Effect: 10% wage increase → 6% labor reduction (vs 3% baseline)

**Option B: Earlier Substitution Start** (technology available sooner)
```gams
# modules/38_factor_costs/sticky_labor/input.gms:17
s38_startyear_labor_substitution = 2015  ! Was: 2025 (10 years earlier)
```
Effect: Mechanization response active from 2015

**Option C: More Mobile Capital** (easier reallocation)
```gams
# modules/38_factor_costs/sticky_labor/input.gms:15
s38_immobile = 0.3  ! Was: 1 (70% mobile, 30% immobile)
```
Effect: Tractors/equipment shared across crops, faster adoption

3. **Recommend Testing Strategy**:
```r
# Run three scenarios
scenarios <- c("baseline", "highsub", "earlysub", "mobile")

# Compare outcomes
for (scen in scenarios) {
  gdx <- paste0("fulldata_", scen, ".gdx")
  labor <- readGDX(gdx, "ov38_laborhours_need", select=list(type="level"))
  employment <- readGDX(gdx, "ov_laborhours_total", select=list(type="level"))  # From Module 36

  print(paste(scen, "Agricultural employment 2050:", sum(employment["y2050",,])))
}
```

4. **Warn About Realism**:
   - Literature: σ = 0.2-0.4 for agriculture (vs 0.6-1.0 manufacturing)
   - Agricultural tasks resist automation (irregular terrain, biological variability)
   - High elasticity may overestimate automation potential
   - Check against historical mechanization rates

5. **Expected Answer**:
   - "Increase s38_ces_elast_subst to 0.5-0.7 for automation scenario"
   - "Earlier start year (2015-2020) if breakthrough already occurred"
   - "More mobile capital (30-50% mobile) if equipment is multipurpose"
   - "Caution: σ > 0.5 may be unrealistic for agriculture (check literature)"
   - "Validate against historical mechanization trends (e.g., U.S. 1950-2000)"

---

**End of Module 38 Comprehensive Documentation**
