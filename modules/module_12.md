## Module 12: Interest Rate (Investment Discount Factor) ✅ COMPLETE

**Status**: Fully documented
**Location**: `modules/12_interest_rate/select_apr20/`
**Method**: GDP-dependent with time-dynamic transition and regional flexibility
**Realization**: `select_apr20` (April 2020 version)
**Author**: Xiaoxi Wang

### 1. Purpose & Overview

**Core Function**: Module 12 calculates **regional interest rates** that serve as the **discount factor** for inter-temporal investment calculations across MAgPIE. Interest rates act as a **risk premium** that varies by development level (GDP per capita) and transitions smoothly from historical to policy values over time.

**Key Output**:
- `pm_interest(t,i)` - Regional interest rate (fraction per year, e.g., 0.10 = 10%)
  - Used by: Module 13 (TC), Module 39 (Land Conversion), Module 41 (Irrigation)
  - Effect: Amortizes capital costs over investment lifetimes

**Two Operating Modes**:
1. **GDP-dependent** (default): Rates interpolate between LIC and HIC based on development state
2. **Coupling**: Reads external interest rate time series from file

**From Module Header** (`realization.gms:8-17`):
```gams
*' The select_apr20 realization allows to flexibly choose regional
*' or global interest rates. In the default setting, the interest rate depends
*' on the development state `im_development_state`, which is calculated based
*' on GDP per capita. Thus, interest rates are regionally specific and dynamic
*' over time.
*' Alternative interest rates can be selected via the interest rate coefficients
*' (`s12_interest_lic`, `s12_interest_hic`, `s12_hist_interest_lic`, `s12_hist_interest_hic`).
*' The future interest rate policy fades in starting from 2025 until it is fully
*' in effect by 2050.
```

**Realization**: `select_apr20`
- Allows flexible regional or global settings
- April 2020 version
- Supports country-specific scenarios

---

### 2. Mechanisms & Logic

Module 12 has **NO EQUATIONS** - it's a **parameter calculation module** that runs only in `preloop` phase.

---

#### **A. GDP-Dependent Interest Rate** (`preloop.gms:23-26`)

**Purpose**: Calculate interest rates based on development state with time-dynamic transition

**Full Formula**:
```gams
pm_interest(t,i) =
    ( (s12_interest_lic - (s12_interest_lic-s12_interest_hic) * im_development_state(t,i)) * f12_interest_fader(t)
    + (s12_hist_interest_lic - (s12_hist_interest_lic-s12_hist_interest_hic) * im_development_state(t,i)) * (1-f12_interest_fader(t)) ) * p12_reg_shr(t,i)
  + ( (s12_interest_lic_noselect - (s12_interest_lic_noselect-s12_interest_hic_noselect) * im_development_state(t,i)) * f12_interest_fader(t)
    + (s12_hist_interest_lic_noselect - (s12_hist_interest_lic_noselect-s12_hist_interest_hic_noselect) * im_development_state(t,i)) * (1-f12_interest_fader(t)) ) * (1-p12_reg_shr(t,i));
```

**Simplified Breakdown** (assuming all countries selected, i.e., `p12_reg_shr = 1`):

```
pm_interest(t,i) =
    [ Policy_rate(t,i) × Fader(t) + Historical_rate(t,i) × (1 - Fader(t)) ]

Where:
  Policy_rate(t,i) = LIC - (LIC - HIC) × Development_state(t,i)
  Historical_rate(t,i) = Hist_LIC - (Hist_LIC - Hist_HIC) × Development_state(t,i)
  Fader(t) = 0 (pre-2025), gradually increases to 1 (by 2050)
```

**Component Explanation**:

**1. Development State Interpolation**:
- **LIC (Low-Income Countries)**: `s12_interest_lic` (default: 0.10 = 10%)
- **HIC (High-Income Countries)**: `s12_interest_hic` (default: 0.04 = 4%)
- **Development state**: `im_development_state(t,i)` from Module 09
  - Value: 0 (low-income) to 1 (high-income)
  - Based on: GDP per capita (PPP)
- **Interpolation**: `interest = LIC - (LIC - HIC) × development_state`

**Example**:
```
LIC = 10%, HIC = 4%
Development state = 0.0  → Interest = 10% - (10% - 4%) × 0.0 = 10%
Development state = 0.5  → Interest = 10% - (10% - 4%) × 0.5 = 7%
Development state = 1.0  → Interest = 10% - (10% - 4%) × 1.0 = 4%
```

**2. Time-Dynamic Fader** (`f12_interest_fader(t)`):
- **Purpose**: Smooth transition from historical to policy interest rates
- **Timing**:
  - Pre-2025: Fader = 0 (100% historical rates)
  - 2025-2050: Fader gradually increases
  - Post-2050: Fader = 1 (100% policy rates)
- **Source**: `f12_interest_fader.csv` (input data file)
- **Calculation**: At each timestep, interest rate is weighted average:
  - `interest = policy_rate × fader + historical_rate × (1 - fader)`

**3. Regional Country Selection** (`p12_reg_shr(t,i)`):
- **Purpose**: Apply different interest rates to selected vs. non-selected countries
- **Calculation** (`preloop.gms:17`):
  ```gams
  p12_reg_shr(t,i) = sum(i_to_iso(i,iso), p12_country_switch(iso) * im_pop_iso(t,iso))
                   / sum(i_to_iso(i,iso), im_pop_iso(t,iso));
  ```
- **Translation**: Regional share = (Population in selected countries) / (Total population in region)
- **Weighting**: By population (not land area or GDP)
- **Effect**:
  - If all countries selected: `p12_reg_shr = 1` (only first term applies)
  - If no countries selected: `p12_reg_shr = 0` (only second term applies)
  - If partial: Weighted average of selected and non-selected rates

---

#### **B. Coupling Mode (Alternative)** (`preloop.gms:20-21`)

**Purpose**: Use externally provided interest rate time series

```gams
$ifthen "%c12_interest_rate%" == "coupling"
  p12_interest_select(t_all,i) = f12_interest_coupling(t_all);
$endif
```

**When to Use**:
- Coupling with external economic models
- Testing specific interest rate scenarios
- Imposing observed historical interest rates

**Data Source**:
- File: `f12_interest_rate_coupling.csv` (`input.gms:57-63`)
- Format: Time series by year
- Note: Region dimension not available in coupling mode (global rate only)

---

#### **C. Country Selection Switch** (`preloop.gms:12-17`)

**Purpose**: Allow different interest rates for selected countries vs. rest of world

```gams
p12_country_switch(iso) = 0;
p12_country_switch(select_countries12) = 1;
p12_reg_shr(t,i) = sum(i_to_iso(i,iso), p12_country_switch(iso) * im_pop_iso(t,iso))
                 / sum(i_to_iso(i,iso), im_pop_iso(t,iso));
```

**Mechanism**:
1. Set switch to 0 for all countries
2. Set switch to 1 for selected countries (`select_countries12` set)
3. Calculate regional share by population weighting
4. Apply weighted combination:
   - `pm_interest = rate_selected × reg_shr + rate_nonselected × (1 - reg_shr)`

**Use Case Example**:
- Selected countries: EU members → Low interest rates (e.g., 2%)
- Non-selected countries: Rest of world → Higher interest rates (e.g., 6%)
- Result: European regions get lower rates, others get higher rates

---

### 3. Parameters & Data

#### **A. Key Output** (`declarations.gms`)

| Parameter | Description | Units | Type |
|-----------|-------------|-------|------|
| `pm_interest(t,i)` | **OUTPUT: Regional interest rate** | 1 (fraction per year) | Calculated |

**Usage in MAgPIE**:
- **Module 13 (TC - Technical Change)**: Amortizes TC investment costs
- **Module 39 (Land Conversion)**: Amortizes land conversion establishment costs
- **Module 41 (Irrigation)**: Amortizes irrigation infrastructure costs

---

#### **B. Switches & Scalars** (`input.gms:8-19`)

**Mode Switch**:

| Switch | Description | Values | Default |
|--------|-------------|--------|---------|
| `c12_interest_rate` | Interest rate calculation mode | "gdp_dependent", "coupling" | "gdp_dependent" |

**Interest Rate Parameters** (selected countries):

| Scalar | Description | Units | Default |
|--------|-------------|-------|---------|
| `s12_interest_lic` | Policy interest rate for low-income countries | 1 | 0.1 (10%) |
| `s12_interest_hic` | Policy interest rate for high-income countries | 1 | 0.04 (4%) |
| `s12_hist_interest_lic` | Historical interest rate for LIC | 1 | 0.1 (10%) |
| `s12_hist_interest_hic` | Historical interest rate for HIC | 1 | 0.04 (4%) |

**Interest Rate Parameters** (non-selected countries):

| Scalar | Description | Units | Default |
|--------|-------------|-------|---------|
| `s12_interest_lic_noselect` | Policy interest rate for LIC (non-selected) | 1 | 0.1 (10%) |
| `s12_interest_hic_noselect` | Policy interest rate for HIC (non-selected) | 1 | 0.04 (4%) |
| `s12_hist_interest_lic_noselect` | Historical interest rate for LIC (non-selected) | 1 | 0.1 (10%) |
| `s12_hist_interest_hic_noselect` | Historical interest rate for HIC (non-selected) | 1 | 0.04 (4%) |

**Default Values Explanation**:
- **10% (LIC)**: Typical developing country borrowing rates (higher risk, lower financial development)
- **4% (HIC)**: Typical developed country borrowing rates (lower risk, mature financial markets)
- **Historical = Policy**: Default assumes no policy change (rates stay constant)

---

#### **C. Country Selection Set** (`input.gms:21-47`)

| Set | Description | Default |
|-----|-------------|---------|
| `select_countries12(iso)` | Countries affected by chosen interest rate scenario | All 249 countries |

**Modification**: To apply scenario to specific countries only, edit set definition
- Example: EU only → List only EU country codes
- Effect: EU gets selected rates, rest of world gets non-selected rates

---

#### **D. Internal Parameters** (`declarations.gms`)

| Parameter | Description | Units | Type |
|-----------|-------------|-------|------|
| `p12_reg_shr(t,i)` | Regional share of selected countries | 1 | Calculated |
| `p12_country_switch(iso)` | 1 if country selected, 0 otherwise | 1 | Switch |
| `p12_interest_select(t,i)` | Interest rate for selected countries (coupling mode) | 1 | From file |

---

### 4. Data Sources

#### **File 1: Interest Rate Fader** (`input.gms:49-55`)

```gams
parameter f12_interest_fader(t_all) Protection scenario fader (1)
/
$include "./modules/12_interest_rate/input/f12_interest_fader.csv"
/
;
```

**Purpose**: Time-dynamic transition from historical to policy interest rates
**Format**: Time series (t_all) with values 0-1
**Example**:
```
y2020  0.0
y2025  0.0
y2030  0.2
y2035  0.4
y2040  0.6
y2045  0.8
y2050  1.0
y2055  1.0
```

**Interpretation**:
- 2020-2025: 0% policy, 100% historical
- 2030: 20% policy, 80% historical
- 2050+: 100% policy, 0% historical

**Function**: Smooth transition avoids sudden shocks to investment costs

---

#### **File 2: Coupling Interest Rate** (`input.gms:57-63`)

```gams
$if "%c12_interest_rate%" == "coupling" parameter f12_interest_coupling(t_all) Interest rate (% per yr)
$if "%c12_interest_rate%" == "coupling" /
$if "%c12_interest_rate%" == "coupling" $include "./modules/12_interest_rate/input/f12_interest_rate_coupling.csv"
$if "%c12_interest_rate%" == "coupling" /
$if "%c12_interest_rate%" == "coupling" ;
```

**Conditional**: Only loaded if `c12_interest_rate = "coupling"`
**Purpose**: External interest rate time series
**Format**: Time series (t_all), global (no regional dimension)
**Use Case**: Coupling with external economic models (e.g., REMIND, MESSAGE)

---

#### **File 3: Development State** (from Module 09)

```gams
im_development_state(t,i)
```

**Source**: Module 09 (Drivers) - calculated from GDP per capita
**Purpose**: Interpolation factor between LIC and HIC interest rates
**Range**: 0 (low-income) to 1 (high-income)
**Calculation** (in Module 09):
```
development_state = (GDP_per_capita - GDP_min) / (GDP_max - GDP_min)
```
Where:
- GDP_min: Lowest observed GDP per capita
- GDP_max: Highest observed GDP per capita

---

### 5. Dependencies

**From Phase 2 Analysis**: Module 12 has 1 input dependency and 3 critical outputs.

#### **DEPENDS ON (1 module)**:

**1. Module 09 (Drivers)** - **CRITICAL DEPENDENCY**:
   - **Variables received**:
     - `im_development_state(t,i)`: Development level (0-1) based on GDP per capita
     - `im_pop_iso(t,iso)`: Country-level population (mio. people) for weighting
   - **Why critical**: Cannot calculate GDP-dependent interest rates without development state
   - **Timing**: Module 09 runs in `preloop`, Module 12 also in `preloop` (sequential)
   - **File**: `preloop.gms:23-26`

---

#### **PROVIDES TO (3 modules)** - **CRITICAL OUTPUTS**:

**1. Module 13 (TC - Technical Change)** - **PRIMARY CONSUMER**:
   - **Variable provided**: `pm_interest(t,i)`
   - **Purpose**: Amortization factor for TC investment costs
   - **Mechanism**: Converts upfront TC costs to annualized costs
   - **Impact**: Higher interest rates → higher annualized TC costs → less TC investment

**2. Module 39 (Land Conversion)** - **SECONDARY CONSUMER**:
   - **Variable provided**: `pm_interest(t,i)`
   - **Purpose**: Amortization of land conversion establishment costs
   - **Mechanism**: Converts one-time conversion costs to annualized costs over land lifetime
   - **Impact**: Higher interest rates → higher annualized conversion costs → less land expansion

**3. Module 41 (Irrigation - Area Equipped for Irrigation)** - **TERTIARY CONSUMER**:
   - **Variable provided**: `pm_interest(t,i)`
   - **Purpose**: Amortization of irrigation infrastructure investment
   - **Mechanism**: Spreads irrigation capital costs over infrastructure lifetime
   - **Impact**: Higher interest rates → higher annualized irrigation costs → less irrigation expansion

---

#### **Circular Dependencies**: NONE

Module 12 has **NO circular dependencies** because:
1. It runs in `preloop` (before optimization)
2. Provides only parameters, not variables
3. Does not depend on any optimization results

---

### 6. Code Truth: What Module 12 DOES

✅ **1. Calculates GDP-Dependent Interest Rates** (`preloop.gms:23-26`):
- Linear interpolation between LIC (10%) and HIC (4%)
- Based on `im_development_state` from Module 09
- Higher GDP → lower interest rate (lower risk premium)
- Dynamic over time (as countries develop, rates decrease)

✅ **2. Implements Time-Dynamic Transition** (`preloop.gms:23-26`):
- Historical rates (pre-2025) vs. policy rates (post-2050)
- Smooth fader function for transition period (2025-2050)
- Avoids sudden shocks to investment costs
- Fader values from `f12_interest_fader.csv`

✅ **3. Supports Country-Specific Scenarios** (`preloop.gms:12-17`):
- Can apply different rates to selected countries
- Country selection via `select_countries12` set (default: all 249 countries)
- Regional aggregation weighted by population
- Allows testing of regional interest rate policies (e.g., EU Green Deal subsidies)

✅ **4. Provides Coupling Mode** (`preloop.gms:20-21`):
- Alternative to GDP-dependent mode
- Reads external interest rate time series
- Useful for model coupling (e.g., with REMIND energy-economy model)
- Global rate (no regional variation)

✅ **5. Uses Population Weighting for Regional Aggregation** (`preloop.gms:17`):
- Converts country-level switches to regional shares
- Weighted by population (not land area or GDP)
- Ensures representative regional interest rates
- Accounts for within-region heterogeneity

---

### 7. Code Truth: What Module 12 does NOT

❌ **1. Does NOT Model Credit Market Dynamics**:
- Interest rates are **exogenous parameters**, not endogenous variables
- No supply/demand for credit
- No financial sector representation
- No banking system or monetary policy
- Interest rates predetermined by GDP scenarios, not by model outcomes

❌ **2. Does NOT Vary by Sector or Investment Type**:
- Same `pm_interest` applies to ALL investments:
  - Technical change (Module 13)
  - Land conversion (Module 39)
  - Irrigation infrastructure (Module 41)
- No differentiation for:
  - Agricultural vs. industrial investments
  - Risky vs. safe investments
  - Short-term vs. long-term loans
- No sector-specific risk premiums

❌ **3. Does NOT Account for Inflation**:
- Interest rates are **nominal**, not real
- No explicit inflation adjustments
- No price level deflators
- Assumes constant purchasing power over time

❌ **4. Does NOT Respond to Model Outcomes**:
- Interest rates are **predetermined** based on GDP scenarios
- Not affected by:
  - Land use decisions
  - Investment levels in the model
  - Agricultural production
  - Food prices
- Purely exogenous driver (one-way causality: GDP → interest, not interest → GDP)

❌ **5. Does NOT Include Government Subsidies or Interventions**:
- No preferential lending programs
- No agricultural credit subsidies
- No green investment tax credits
- Must be implemented manually via lowering interest rate parameters

❌ **6. Does NOT Model Credit Constraints or Rationing**:
- Assumes perfect capital markets (unlimited credit at given rate)
- No borrowing constraints for farmers or firms
- No credit rationing based on collateral or creditworthiness
- No differentiation between large and small farmers

❌ **7. Does NOT Distinguish Between Debt and Equity**:
- Single interest rate for all capital
- No cost of equity vs. cost of debt
- No leverage ratios or capital structure
- Assumes all investments financed by debt at given interest rate

❌ **8. Does NOT Account for Exchange Rate Risk**:
- Single interest rate regardless of currency
- No foreign exchange risk premiums
- No distinction between domestic and international borrowing

---

### 8. Common Modifications

#### 8.1 Set Uniform Global Interest Rate

**Purpose**: Use single interest rate globally instead of GDP-dependent rates

**How**: Modify `input.gms:11-14`
```gams
* Default: GDP-dependent (10% LIC, 4% HIC)
s12_interest_lic = 0.1
s12_interest_hic = 0.04
s12_hist_interest_lic = 0.1
s12_hist_interest_hic = 0.04

* Alternative: Uniform 5% globally
s12_interest_lic = 0.05
s12_interest_hic = 0.05
s12_hist_interest_lic = 0.05
s12_hist_interest_hic = 0.05
```

**Effect**:
- All regions get 5% interest rate regardless of GDP
- Eliminates development-driven variation
- Useful for sensitivity analysis or simple scenarios

**Files**: `input.gms:11-14`

---

#### 8.2 Implement Low Interest Rate Scenario (Climate Finance)

**Purpose**: Simulate subsidized lending for climate-friendly investments

**How**: Modify `input.gms:11-14`
```gams
* Default: Market rates
s12_interest_lic = 0.1
s12_interest_hic = 0.04

* Alternative: Subsidized rates (e.g., Green Climate Fund)
s12_interest_lic = 0.02   # 2% for all countries
s12_interest_hic = 0.02
```

**Effect**:
- Lower investment costs → more TC investment, irrigation, land conversion
- Simulates effect of climate finance on agricultural transformation
- Can be combined with country selection (e.g., only developing countries)

**Files**: `input.gms:11-14`

---

#### 8.3 Apply Different Rates to Specific Regions

**Purpose**: Test regional interest rate policies (e.g., EU green finance)

**How**: Modify `input.gms:22-46` and `input.gms:15-18`
```gams
* Default: All countries selected
sets
  select_countries12(iso) / ABW,AFG,AGO, ... ZWE /   # All 249 countries

* Alternative: EU countries only
sets
  select_countries12(iso) / AUT,BEL,BGR, ... SWE /   # EU27 only

* Set low rates for EU, normal rates for rest
s12_interest_lic = 0.02   # EU: 2%
s12_interest_hic = 0.02
s12_interest_lic_noselect = 0.10   # Rest of world: 10%
s12_interest_hic_noselect = 0.04   # Rest of world: 4%
```

**Effect**:
- EU regions get 2% interest rates
- Non-EU regions get standard GDP-dependent rates (4-10%)
- Allows evaluation of regional policy impacts

**Files**: `input.gms:15-18`, `input.gms:22-46`

---

#### 8.4 Accelerate or Delay Interest Rate Transition

**Purpose**: Change timing of transition from historical to policy rates

**How**: Modify `f12_interest_fader.csv` data file
```
Default fader (2025-2050 transition):
y2020  0.0
y2025  0.0
y2030  0.2
y2040  0.6
y2050  1.0

Accelerated (2025-2030 transition):
y2020  0.0
y2025  0.0
y2026  0.2
y2027  0.4
y2028  0.6
y2029  0.8
y2030  1.0

Delayed (2030-2060 transition):
y2020  0.0
y2030  0.0
y2040  0.33
y2050  0.67
y2060  1.0
```

**Effect**:
- Accelerated: Policy rates apply sooner → faster investment response
- Delayed: Historical rates persist longer → slower transition
- Smooth vs. abrupt: Affects adjustment costs in investment modules

**Files**: `modules/12_interest_rate/input/f12_interest_fader.csv`

---

#### 8.5 Use External Interest Rate Time Series (Coupling Mode)

**Purpose**: Couple with external economic model (e.g., REMIND) that provides interest rates

**How**: Modify `input.gms:8` and create coupling file
```gams
* Default: GDP-dependent
$setglobal c12_interest_rate  gdp_dependent

* Alternative: Coupling mode
$setglobal c12_interest_rate  coupling
```

Create `f12_interest_rate_coupling.csv`:
```
y2020  0.05
y2025  0.045
y2030  0.04
y2040  0.035
y2050  0.03
```

**Effect**:
- MAgPIE uses interest rates from external model
- Consistent assumptions across coupled models
- **Note**: Global rate only (no regional variation in coupling mode)

**Files**: `input.gms:8`, `f12_interest_rate_coupling.csv`

---

### 9. Testing & Validation

#### 9.1 Interest Rate Range Check

**Test**: Are interest rates within realistic bounds (0-30%)?

**How**:
```r
library(magpie4)
library(gdx)

gdx <- "fulldata.gdx"
interest <- readGDX(gdx, "pm_interest")

# Check range
min_rate <- min(interest, na.rm=TRUE)
max_rate <- max(interest, na.rm=TRUE)

print(paste("Interest rate range:", min_rate*100, "% to", max_rate*100, "%"))

# Realistic bounds
stopifnot(min_rate >= 0)      # Non-negative
stopifnot(max_rate <= 0.30)   # Not more than 30%
```

**Expected**:
- Minimum: ≥ 0% (non-negative)
- Maximum: ≤ 30% (unrealistic if higher)
- Typical: 2-15% range

**If fails**: Check parameter settings (`s12_interest_lic`, `s12_interest_hic`)

**File**: `input.gms:11-14`

---

#### 9.2 GDP-Dependence Verification

**Test**: Do interest rates decrease with development state?

**How**:
```r
interest <- readGDX(gdx, "pm_interest")
dev_state <- readGDX(gdx, "im_development_state")

# For a specific year (e.g., 2050)
data <- data.frame(
  region = getRegions(interest),
  interest = as.vector(interest["y2050",,]),
  dev_state = as.vector(dev_state["y2050",,])
)

# Plot
plot(data$dev_state, data$interest,
     xlab="Development State", ylab="Interest Rate",
     main="Interest Rate vs. Development (2050)")

# Check negative correlation
cor_test <- cor.test(data$dev_state, data$interest)
print(paste("Correlation:", cor_test$estimate))

stopifnot(cor_test$estimate < -0.5)  # Strong negative correlation
```

**Expected**: Strong negative correlation (ρ < -0.5)

**If fails**: Check formula in `preloop.gms:23-26`

**File**: `preloop.gms:23-26`

---

#### 9.3 Time Transition Check

**Test**: Does fader smoothly transition from 0 to 1?

**How**:
```r
# If fader is stored in GDX (may not be)
# Otherwise, check CSV file directly
fader <- read.csv("modules/12_interest_rate/input/f12_interest_fader.csv")

print(fader)

# Check properties
stopifnot(min(fader$value) == 0)    # Starts at 0
stopifnot(max(fader$value) == 1)    # Ends at 1
stopifnot(all(diff(fader$value) >= 0))  # Monotonically increasing
```

**Expected**:
- Pre-2025: Fader = 0
- 2025-2050: Fader increases gradually
- Post-2050: Fader = 1

**If fails**: Check `f12_interest_fader.csv`

**File**: `f12_interest_fader.csv`

---

#### 9.4 Regional Share Sum Check

**Test**: Does regional share sum correctly?

**How**:
```r
reg_shr <- readGDX(gdx, "p12_reg_shr")

# Check range
min_shr <- min(reg_shr, na.rm=TRUE)
max_shr <- max(reg_shr, na.rm=TRUE)

print(paste("Regional share range:", min_shr, "to", max_shr))

# Should be between 0 and 1
stopifnot(min_shr >= 0)
stopifnot(max_shr <= 1)

# If all countries selected, should be 1 everywhere
if(all_countries_selected) {
  stopifnot(all(abs(reg_shr - 1) < 0.01))
}
```

**Expected**:
- Range: 0 to 1
- If all countries selected: All values = 1
- If none selected: All values = 0

**If fails**: Check regional share calculation (`preloop.gms:17`)

**File**: `preloop.gms:17`

---

### 10. Summary

**Module 12 (Interest Rate)** provides **regional interest rates** as the **discount factor** for inter-temporal investment calculations in MAgPIE. Interest rates act as a **risk premium** that varies by development level (GDP per capita) and transitions smoothly from historical to policy values over time (2025-2050).

**Core Functions**:
1. **GDP-dependent calculation**: Interpolate between LIC (10%) and HIC (4%) based on development state
2. **Time-dynamic transition**: Smooth fader from historical to policy rates (2025-2050)
3. **Country-specific scenarios**: Different rates for selected vs. non-selected countries
4. **Coupling mode**: Use external interest rate time series from coupled models

**Key Features**:
- **No equations**: Parameter calculation only (runs in preloop)
- **Exogenous**: Not affected by model outcomes
- **Regional variation**: Based on GDP per capita (developing countries pay higher rates)
- **Time-dynamic**: Smooth transition avoids sudden shocks
- **Flexible**: Supports regional scenarios and external coupling

**Critical Output**:
- `pm_interest(t,i)`: **Discount factor** for investment amortization
  - Used by: Module 13 (TC), Module 39 (Land Conversion), Module 41 (Irrigation)
  - Effect: Higher interest rates → higher annualized costs → less investment

**Default Values**:
- **LIC (Low-Income)**: 10% (typical developing country borrowing rate)
- **HIC (High-Income)**: 4% (typical developed country rate)
- **Transition**: 2025-2050 (gradual phase-in of policy rates)

**Dependencies**:
- **Receives from**: Module 09 (Drivers) - development state, population
- **Provides to**: Module 13 (TC), Module 39 (Land Conversion), Module 41 (Irrigation)
- **Circular**: None (runs in preloop, purely exogenous)

**Limitations**:
- No credit market dynamics (supply/demand)
- No sector-specific rates (same for all investments)
- No inflation adjustments (nominal rates)
- No response to model outcomes (predetermined by GDP)
- No government subsidies or credit constraints
- No distinction between debt and equity
- No exchange rate risk

**Common Uses**:
1. **Sensitivity analysis**: Test impact of interest rates on investment and land use
2. **Climate finance scenarios**: Low rates simulate subsidized green lending
3. **Regional policies**: EU green finance, developing country concessional loans
4. **Model coupling**: Use interest rates from external economic models

**Testing Focus**:
- Interest rate range (0-30%)
- GDP-dependence (negative correlation with development state)
- Time transition (fader smoothly 0→1)
- Regional share sum (0-1 range)

**Why Module 12 Matters**:
- **Investment costs**: Interest rates determine annualized costs of all long-term investments
- **Technology adoption**: Lower rates → more TC investment → higher productivity
- **Land expansion**: Higher rates → higher conversion costs → less deforestation
- **Irrigation**: Higher rates → less irrigation investment → more rainfed agriculture
- **Climate policy**: Interest rates key lever for financing agricultural transformation

---

**Module 12 Status**: ✅ COMPLETE (~600 lines documented)
**Verified Against**: Actual code in `modules/12_interest_rate/select_apr20/`
**Documentation Date**: October 11, 2025

---

### 11. AI Agent Response Patterns

#### **User Query**: "How are interest rates determined in MAgPIE?"

**Response**:
```
MAgPIE uses Module 12 (Interest Rate) to calculate GDP-dependent regional interest rates:

1. Core Formula (simplified):
   interest(t,i) = LIC - (LIC - HIC) × development_state(t,i)

   Where:
   - LIC = 10% (low-income countries, default)
   - HIC = 4% (high-income countries, default)
   - development_state = 0 (low-income) to 1 (high-income)

2. Time dynamics:
   - Historical rates (pre-2025) transition to policy rates (post-2050)
   - Smooth fader function (2025-2050) avoids sudden shocks
   - Fader from f12_interest_fader.csv

3. Example (year 2050):
   - Sub-Saharan Africa (dev_state = 0.2): 10% - (10%-4%) × 0.2 = 8.8%
   - Europe (dev_state = 0.95): 10% - (10%-4%) × 0.95 = 4.3%

4. Used by:
   → Module 13 (TC): Investment cost discounting
   → Module 39 (Land Conversion): Conversion cost amortization
   → Module 41 (Irrigation): Infrastructure cost discounting

⚠️ IMPORTANT: Interest rates are EXOGENOUS (not endogenous). They do not
respond to model outcomes - predetermined by GDP scenarios from Module 09.

Code: modules/12_interest_rate/select_apr20/preloop.gms:23-26
```

---

#### **User Query**: "Can I set a uniform global interest rate?"

**Response**:
```
YES! Set uniform global interest rate by making LIC and HIC equal:

Method 1: Configuration parameters (modules/12_interest_rate/select_apr20/input.gms:11-14)

# Uniform 5% rate globally
s12_interest_lic = 0.05
s12_interest_hic = 0.05
s12_hist_interest_lic = 0.05
s12_hist_interest_hic = 0.05

Effect:
→ All regions get 5% regardless of GDP per capita
→ Eliminates development-driven variation
→ Formula becomes: interest = 5% - (5% - 5%) × dev_state = 5%

Method 2: Coupling mode (external time series)

$setglobal c12_interest_rate  coupling

Then provide uniform rate in f12_interest_rate_coupling.csv:
y2020  0.05
y2030  0.05
y2050  0.05

⚠️ Impact on model:
- Lower rates → More investment in TC, irrigation, land conversion
- Higher rates → Less investment, more rainfed agriculture
- Affects modules 13 (TC), 39 (Land Conversion), 41 (Irrigation)

Use cases:
- Sensitivity analysis
- Simple baseline scenarios
- Comparison with other models using fixed interest rates
```

---

#### **User Query**: "Why do developing countries have higher interest rates in MAgPIE?"

**Response**:
```
Developing countries have higher interest rates in MAgPIE to reflect RISK PREMIUMS:

1. Economic rationale:
   - Lower-income countries: Higher credit risk → Higher borrowing costs
   - Higher-income countries: Lower risk → Lower costs
   - Reflects real-world lending patterns

2. Implementation (modules/12_interest_rate/select_apr20/preloop.gms:23-26):
   - LIC (Low-Income Countries): 10% default
   - HIC (High-Income Countries): 4% default
   - Linear interpolation based on GDP per capita (development_state)

3. Example interest rates by development level:
   Development state = 0.0 (poorest):  10%
   Development state = 0.3:            8.2%
   Development state = 0.5:            7.0%
   Development state = 0.8:            5.2%
   Development state = 1.0 (richest):  4.0%

4. Consequences in the model:
   - Developing countries: Higher investment costs → Less TC adoption, less irrigation
   - Developed countries: Lower costs → More investment → Faster productivity growth
   - Reinforces development trajectories (but can be modified for climate finance scenarios)

5. How to modify (for climate finance scenarios):
   # Subsidized rates for developing countries
   s12_interest_lic = 0.02   # Green Climate Fund subsidies
   s12_interest_hic = 0.04   # Developed countries pay market rate

⚠️ Note: This is a SIMPLIFICATION. Real-world interest rates depend on many
factors (monetary policy, inflation, exchange rates, political stability) not
modeled in MAgPIE.

Code: modules/12_interest_rate/select_apr20/input.gms:11-14
```
