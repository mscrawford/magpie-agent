# Module 56: GHG Policy (price_aug22)

**Realization:** `price_aug22` (Price-based Policy, August 2022)
**Total Lines of Code:** 708
**Equation Count:** 7
**Status:** ✅ Fully Verified (2025-10-12)

---

## 1. Overview

### 1.1 Purpose

Module 56 is the **greenhouse gas policy hub** that **connects emissions to costs** in MAgPIE's objective function (`module.gms:8-24`). It translates physical emissions (CO2, CH4, N2O) into economic costs by multiplying emissions with pollutant prices, creating incentives for emission reduction and carbon dioxide removal (CDR).

**Core Function:** EmissionCosts = Σ(Emissions × Price) → Enters objective function → Optimized land use reduces emissions

**Architectural Role:** Module 56 is the **critical link between environmental and economic systems**, determining which emission sources are priced, at what level, and how CDR from afforestation is rewarded.

### 1.2 Key Features

1. **Flexible Pricing Scenarios** (`input.gms:84-86`): 100+ scenarios from various IAM models (REMIND, IMAGE, MESSAGE, etc.)
2. **Selective Emission Coverage** (`input.gms:113-117`): Policy scenarios determine which gases and sources are priced
3. **One-off vs. Annual Emissions** (`equations.gms:35-52`): Different treatment for deforestation (one-time) vs. fertilizer use (recurring)
4. **CDR Reward Calculation** (`equations.gms:60-79`): Discounted present value of future carbon removals from afforestation
5. **Regional and Temporal Faders** (`preloop.gms:54-63`): Gradual policy phase-in
6. **Development State Scaling** (`preloop.gms:50-51`): Price adjustment based on institutional capacity
7. **Carbon Stock Tracking** (`equations.gms:19-22`): Calculates CO2 emissions from land-use change based on carbon stock differences

### 1.3 Critical Policy Levers

The module provides extensive configurability through 6 key switches that determine mitigation ambition and scope:

| Switch | Purpose | Default | Range |
|--------|---------|---------|-------|
| `c56_pollutant_prices` | Price scenario (e.g., 1.5°C, 2°C, NDC) | SSP2-NPi2025 | 100+ scenarios |
| `c56_emis_policy` | Which gases/sources are priced | reddnatveg_nosoil | 60+ policies |
| `c56_carbon_stock_pricing` | Which carbon pools for LULUCF accounting | actualNoAcEst | actual / actualNoAcEst |
| `c56_cprice_aff` | Price used for afforestation decisions | secdforest_vegc | Various options |
| `s56_c_price_induced_aff` | Enable C-price driven afforestation | 1 (ON) | 0=OFF, 1=ON |
| `s56_buffer_aff` | CDR buffer (risk reserve for permanence) | 0.5 (50%) | 0-1 |

---

## 2. Core Equations

Module 56 implements 7 equations covering emission pricing, cost calculation, and CDR rewards.

### 2.1 Equation q56_emis_pricing: Annual Emissions for Pricing

**File:** `equations.gms:15-17`

```gams
q56_emis_pricing(i2,pollutants,emis_annual) ..
  v56_emis_pricing(i2,emis_annual,pollutants) =e=
    vm_emissions_reg(i2,emis_annual,pollutants);
```

**What This Does:**

For annual (recurring) emissions (CH4, N2O, annual CO2), the emissions subject to pricing equal the actual regional emissions from all sources.

**Components:**

- **v56_emis_pricing(i,emis_annual,pollutants)**: Emissions used for pricing calculation (Tg/yr)
- **vm_emissions_reg(i,emis_annual,pollutants)**: Actual regional emissions from Module 51-57 (Tg/yr)
- **emis_annual**: Recurring emission sources (fertilizer, livestock, etc.)

**Conceptual Meaning:**

Annual emissions occur every year under continuous management (e.g., N2O from fertilizer). Their full magnitude enters the pricing calculation without adjustment.

**Citation:** `equations.gms:12-17`

---

### 2.2 Equation q56_emis_pricing_co2: One-off CO2 Emissions for Pricing

**File:** `equations.gms:19-22`

```gams
q56_emis_pricing_co2(i2,emis_oneoff) ..
  v56_emis_pricing(i2,emis_oneoff,"co2_c") =e=
                 sum((cell(i2,j2),emis_land(emis_oneoff,land,c_pools)),
                 (pcm_carbon_stock(j2,land,c_pools,"actual") - vm_carbon_stock(j2,land,c_pools,"%c56_carbon_stock_pricing%"))/m_timestep_length);
```

**What This Does:**

Calculates CO2 emissions from land-use change as **carbon stock change between time steps** divided by timestep length.

**Mathematical Structure:**

```
CO2_emissions_for_pricing = Σ[(CarbonStock_previous - CarbonStock_current) / timestep_years]
```

**Components:**

- **pcm_carbon_stock**: Previous time step's carbon stock ("actual") (mio. tC)
- **vm_carbon_stock**: Current time step's carbon stock (configurable type) (mio. tC)
- **c56_carbon_stock_pricing**: Switch determining which carbon stock type to use ("actual" or "actualNoAcEst")
- **m_timestep_length**: Time step duration in years (typically 5 or 10 years)
- **emis_oneoff**: One-time emission sources (deforestation, forest degradation)

**Key Configuration:**

`c56_carbon_stock_pricing` determines which carbon pools are subject to pricing:
- **"actual"**: All carbon stock changes (including afforestation establishment)
- **"actualNoAcEst"** (default): Excludes afforestation establishment from pricing (avoids double-counting with CDR rewards)

**Why Division by Timestep Length:**

Carbon stocks are in total tC, but emissions must be expressed as annual rate (Tg C/yr) for consistency with annual emissions.

**Citation:** `equations.gms:12-22`

---

### 2.3 Equation q56_emission_cost_annual: Costs for Annual Emissions

**File:** `equations.gms:29-33`

```gams
q56_emission_cost_annual(i2,emis_annual) ..
                 v56_emission_cost(i2,emis_annual) =e=
                 sum(pollutants,
                     v56_emis_pricing(i2,emis_annual,pollutants) *
                     sum(ct, im_pollutant_prices(ct,i2,pollutants,emis_annual)));
```

**What This Does:**

Calculates emission costs for recurring sources by multiplying annual emissions with pollutant prices.

**Mathematical Structure:**

```
AnnualEmissionCost = Σ[Emissions_pollutant × Price_pollutant]  for pollutants ∈ {CO2, CH4, N2O}
```

**Components:**

- **v56_emission_cost(i,emis_annual)**: Emission costs for annual sources (mio. USD17MER/yr)
- **v56_emis_pricing(i,emis_annual,pollutants)**: Annual emissions (Tg/yr)
- **im_pollutant_prices(ct,i,pollutants,emis_annual)**: GHG prices (USD17MER/Tg)
- **ct**: Current time step indicator

**Units:**

- Emissions: Tg = million tons (Tg N for N2O, Tg CH4 for methane, Tg C for CO2)
- Prices: USD17MER per Tg (2017 US dollars at market exchange rates per million tons)
- Costs: mio. USD17MER/yr (millions of USD per year)

**Citation:** `equations.gms:26-33`

---

### 2.4 Equation q56_emission_cost_oneoff: Costs for One-off Emissions

**File:** `equations.gms:45-52`

```gams
q56_emission_cost_oneoff(i2,emis_oneoff) ..
                 v56_emission_cost(i2,emis_oneoff) =e=
                 sum(pollutants,
                     v56_emis_pricing(i2,emis_oneoff,pollutants)
                     * m_timestep_length
                     * sum(ct,
                       im_pollutant_prices(ct,i2,pollutants,emis_oneoff)
                      * pm_interest(ct,i2)/(1+pm_interest(ct,i2))));
```

**What This Does:**

Converts one-time emissions (deforestation) into annualized costs using infinite-horizon annuity factor.

**Mathematical Structure:**

```
OneOffEmissionCost = Σ[Emissions_annual × timestep_years × Price × r/(1+r)]

Where r/(1+r) = annuity due factor with infinite horizon
```

**Why This Formula:**

One-off emissions occur once but avoided emissions provide perpetual benefits. The annuity factor converts a one-time emission into equivalent annual cost:
- **m_timestep_length**: Converts annual emission rate back to total timestep emission
- **Price**: Cost of total emissions
- **r/(1+r)**: Annuity due factor levels one-time cost with recurring annual costs

**Example:**

- Deforestation emits 100 Tg C over 10 years (10 Tg C/yr)
- C price = $100/tC, interest rate = 5%
- Annual cost = 10 Tg/yr × 10 yr × $100/tC × 0.05/1.05 ≈ $4,762/yr
- This equals the annual payment on a $100,000 perpetuity at 5% interest

**Rationale:**

Without annuity factor, one-time emissions would be under-penalized relative to recurring emissions, biasing decisions toward deforestation instead of intensification.

**Citation:** `equations.gms:35-52`

---

### 2.5 Equation q56_emission_costs: Total Emission Costs

**File:** `equations.gms:56-58`

```gams
q56_emission_costs(i2) ..
                 vm_emission_costs(i2) =e=
                 sum(emis_source, v56_emission_cost(i2,emis_source));
```

**What This Does:**

Aggregates costs from all emission sources (annual + one-off) to produce total regional emission cost.

**Mathematical Structure:**

```
TotalEmissionCost = Σ[EmissionCost_source]  for all emission sources
```

**Output:**

**vm_emission_costs(i)** → Enters Module 11 (Costs) objective function → Minimized by MAgPIE

**Citation:** `equations.gms:54-58`

---

### 2.6 Equations q56_reward_cdr_aff_reg & q56_reward_cdr_aff: CDR Reward Calculation

**File:** `equations.gms:67-79`

```gams
q56_reward_cdr_aff_reg(i2) ..
                 vm_reward_cdr_aff(i2) =e=
                 sum(cell(i2,j2),
                 v56_reward_cdr_aff(j2)
                 );

q56_reward_cdr_aff(j2) ..
                 v56_reward_cdr_aff(j2) =e=
               sum(ct, p56_fader_cpriceaff(ct)) *
               sum(ac,
               (sum(aff_effect,(1-s56_buffer_aff)*vm_cdr_aff(j2,ac,aff_effect)) * sum((cell(i2,j2),ct), p56_c_price_aff(ct,i2,ac)))
               / ((1+sum((cell(i2,j2),ct),pm_interest(ct,i2)))**(ac.off*5)))
                 *sum((cell(i2,j2),ct),pm_interest(ct,i2)/(1+pm_interest(ct,i2)));
```

**What These Equations Do:**

Calculate the **average annual reward for CDR from afforestation** by:
1. Summing expected CDR across age classes
2. Multiplying by age-class-specific future C prices
3. Discounting to present value
4. Applying annuity factor to get annual payment

**Mathematical Structure (Simplified):**

```
AnnualCDRReward = fader × Σ[CDR_ac × (1 - buffer) × Price_future_ac / (1+r)^years_ac] × r/(1+r)

Where:
- ac = age class (5-year intervals)
- CDR_ac = expected carbon removal in age class ac
- buffer = risk reserve (default 50%)
- Price_future_ac = C price when ac reaches maturity
- r = discount rate
- years_ac = years until age class ac
```

**Components:**

- **vm_cdr_aff(j,ac,aff_effect)**: Expected CDR from afforestation per age class (tC/ha/yr) from Module 32
- **s56_buffer_aff**: Buffer fraction for permanence risk (default 0.5 = 50%) (`input.gms:71`)
- **p56_c_price_aff(ct,i,ac)**: Age-class-specific future C price (USD17MER/tC), constructed in preloop
- **pm_interest(ct,i)**: Regional discount rate from Module 12
- **ac.off**: Age class offset (0 for ac0, 1 for ac5, 2 for ac10, etc.)
- **p56_fader_cpriceaff(ct)**: Temporal fader for gradual policy introduction

**Why Age-Class-Specific Prices:**

Trees planted today sequester carbon over decades. Price expectations must reflect **future C prices when sequestration occurs**, not current prices. Module 56 constructs `p56_c_price_aff` with **price foresight** up to `s56_c_price_exp_aff` years (default 50 years, `input.gms:70`).

**Discounting Formula:**

`/ ((1+r)^(ac.off*5))` discounts future cash flows:
- ac0 (immediate): no discounting (ac.off=0)
- ac5 (5 years): discount by (1+r)^5
- ac20 (20 years): discount by (1+r)^20

**Annuity Factor:**

`× r/(1+r)` converts present value to equivalent annual payment (annuity due, infinite horizon).

**Buffer:**

`(1-s56_buffer_aff)`: Only 50% of CDR is credited; 50% pooled as risk reserve for non-permanence (e.g., fire, drought, management failure). This is standard practice in voluntary carbon markets.

**Sign Convention:**

`vm_reward_cdr_aff` has **negative sign in Module 11** → Rewards **reduce** total costs → Incentivizes afforestation.

**Citation:** `equations.gms:60-79`, `realization.gms:15-22`

---

## 3. Pollutant Price Configuration (Preloop Phase)

Module 56's complexity lies in extensive preloop logic that configures GHG prices based on policy scenarios. The process has 8 stages:

### 3.1 Stage 1: Select Price Scenario

**File:** `preloop.gms:35-45`

```gams
$ifthen "%c56_pollutant_prices%" == "coupling"
 im_pollutant_prices(t_all,i,pollutants,emis_source) = f56_pollutant_prices_coupling(t_all,i,pollutants);
$elseif "%c56_pollutant_prices%" == "emulator"
 im_pollutant_prices(t_all,i,pollutants,emis_source) = f56_pollutant_prices_emulator(t_all,i,pollutants);
$elseif "%c56_pollutant_prices%" == "none"
 im_pollutant_prices(t_all,i,pollutants,emis_source) = 0;
$else
 im_pollutant_prices(t_all,i,pollutants,emis_source) = f56_pollutant_prices(t_all,i,pollutants,"%c56_pollutant_prices%") * p56_region_price_shr(t_all,i)
                                         + f56_pollutant_prices(t_all,i,pollutants,"%c56_pollutant_prices_noselect%") * (1-p56_region_price_shr(t_all,i));
$endif
```

**What This Does:**

Loads GHG prices from one of three sources:
- **coupling**: External prices from coupled REMIND-MAgPIE runs
- **emulator**: Prices from climate policy emulator
- **scenario**: Prices from pre-defined scenarios in `f56_pollutant_prices.cs3`

**Regional Price Sharing:**

The `else` branch allows **selective regional policies**: Some countries follow one price scenario (`c56_pollutant_prices`), others follow a different scenario (`c56_pollutant_prices_noselect`). The share is determined by `p56_region_price_shr`, calculated as population-weighted country coverage (`preloop.gms:18-23`).

**Citation:** `preloop.gms:35-45`

---

### 3.2 Stage 2: Development State Scaling

**File:** `preloop.gms:50-51`

```gams
im_pollutant_prices(t_all,i,pollutants,emis_source)$(s56_ghgprice_devstate_scaling = 1) = im_pollutant_prices(t_all,i,pollutants,emis_source)*im_development_state(t_all,i);
```

**What This Does:**

Scales GHG prices by development state index (`im_development_state` ∈ [0,1]) to reflect institutional capacity for implementing carbon pricing.

**Rationale:**

Developing countries may lack governance, monitoring, and enforcement systems needed for effective carbon pricing. Development state scaling reduces effective price in low-capacity regions.

**Default:** OFF (`s56_ghgprice_devstate_scaling = 0`, `input.gms:68`)

**Citation:** `preloop.gms:50-51`

---

### 3.3 Stage 3: Temporal Fader

**File:** `preloop.gms:53-63`

```gams
if (s56_fader_functional_form = 1,
  m_linear_time_interpol(p56_fader,s56_fader_start,s56_fader_end,0,s56_fader_target);
elseif s56_fader_functional_form = 2,
  m_sigmoid_time_interpol(p56_fader,s56_fader_start,s56_fader_end,0,s56_fader_target);
);

p56_fader_reg(t_all,i) = p56_fader(t_all) * p56_region_fader_shr(t_all,i) + p56_fader(t_all) * (1-p56_region_fader_shr(t_all,i));
im_pollutant_prices(t_all,i,pollutants_fader,emis_source)$(s56_ghgprice_fader = 1) = im_pollutant_prices(t_all,i,pollutants_fader,emis_source) * p56_fader_reg(t_all,i);
```

**What This Does:**

Gradually phases in GHG policy from `s56_fader_start` (default 2035) to `s56_fader_end` (default 2050), reaching `s56_fader_target` (default 1 = 100% policy).

**Functional Forms:**

- **Linear (default):** Price increases linearly from 0 to target
- **Sigmoid:** S-curve with slow start, rapid middle, slow end

**Regional Faders:**

Similar to price sharing, faders can differ by country based on `fader_countries56` set.

**Default:** OFF (`s56_ghgprice_fader = 0`, `input.gms:75`)

**Citation:** `preloop.gms:53-63`

---

### 3.4 Stage 4: CO2 Price Reduction Factor

**File:** `preloop.gms:65-67`

```gams
im_pollutant_prices(t_all,i,"co2_c",emis_source) = im_pollutant_prices(t_all,i,"co2_c",emis_source)*s56_cprice_red_factor;
```

**What This Does:**

Applies a multiplier to CO2 prices to account for potential negative side effects of avoided deforestation (e.g., leakage, governance issues).

**Default:** 1 (no reduction, `input.gms:66`)

**Citation:** `preloop.gms:65-67`

---

### 3.5 Stage 5: Historical Period Zeroing

**File:** `preloop.gms:69-74`

```gams
im_pollutant_prices(t_all,i,pollutants,emis_source)$(m_year(t_all) <= sm_fix_SSP2) = 0;
im_pollutant_prices(t_all,i,pollutants,emis_source)$(m_year(t_all) > sm_fix_SSP2 AND m_year(t_all) <= max(m_year("%c56_mute_ghgprices_until%"),s56_fader_start*s56_ghgprice_fader)) = 0;
im_pollutant_prices(t_all,i,"co2_c",emis_source)$(im_pollutant_prices(t_all,i,"co2_c",emis_source) < s56_minimum_cprice) = s56_minimum_cprice;
```

**What This Does:**

1. **Zero historical prices:** GHG prices = 0 for years ≤ 2010 (no retrospective carbon pricing)
2. **Mute future prices until start year:** Prices = 0 until `c56_mute_ghgprices_until` (default 2030, `input.gms:88`)
3. **Minimum C price:** CO2 price floor = `s56_minimum_cprice` (default $3.67/tC, `input.gms:67`)

**Citation:** `preloop.gms:69-74`

---

### 3.6 Stage 6: CH4 and N2O Price Caps

**File:** `preloop.gms:76-82`

```gams
im_pollutant_prices(t_all,i,"ch4",emis_source)$(im_pollutant_prices(t_all,i,"ch4",emis_source) > s56_limit_ch4_n2o_price*12/44*28) = s56_limit_ch4_n2o_price*12/44*28;
im_pollutant_prices(t_all,i,"n2o_n_direct",emis_source)$(im_pollutant_prices(t_all,i,"n2o_n_direct",emis_source) > s56_limit_ch4_n2o_price*12/44*265*44/28) = s56_limit_ch4_n2o_price*12/44*265*44/28;
```

**What This Does:**

Caps CH4 and N2O prices at `s56_limit_ch4_n2o_price` (default $4,920/tC, `input.gms:65`) converted using Global Warming Potentials:
- **CH4 GWP:** 28 (AR5 100-year)
- **N2O GWP:** 265 (AR5 100-year)
- **Conversion factors:** 12/44 (C to CO2), 44/28 (N2O to N)

**Rationale:**

Very high N2O prices (>$50,000/tN) can cause numerical instability or unrealistic abatement decisions. Cap ensures model robustness.

**Citation:** `preloop.gms:76-82`

---

### 3.7 Stage 7: Emission Policy Matrix

**File:** `preloop.gms:84-91`

```gams
loop(t_all,
 if(m_year(t_all) <= sm_fix_SSP2,
  im_pollutant_prices(t_all,i,pollutants,emis_source) = im_pollutant_prices(t_all,i,pollutants,emis_source) * f56_emis_policy("reddnatveg_nosoil",pollutants,emis_source);
 else
  im_pollutant_prices(t_all,i,pollutants,emis_source) = im_pollutant_prices(t_all,i,pollutants,emis_source) * f56_emis_policy("%c56_emis_policy%",pollutants,emis_source);
 );
);
```

**What This Does:**

Multiplies prices by emission policy matrix (`f56_emis_policy`), which contains 0s and 1s indicating whether each gas-source combination is priced.

**Policy Matrix (`f56_emis_policy.csv`):**

Dimensions: 60+ policies × 15 pollutants × 20+ emission sources

Example policies:
- **"none":** All entries = 0 (no pricing)
- **"all":** All entries = 1 (price everything)
- **"reddnatveg_nosoil"** (default, `input.gms:86`): Price CO2 from natural vegetation loss, exclude soil C
- **"all_nosoil":** Price all gases except soil CO2
- **"sdp_all":** Comprehensive pricing for Sustainable Development Pathway scenarios

**Selective Pricing Example:**

Policy "redd_nosoil" might have:
- `f56_emis_policy("redd_nosoil","co2_c","deforest") = 1` (price deforestation CO2)
- `f56_emis_policy("redd_nosoil","co2_c","cropland_soil") = 0` (exclude soil CO2)
- `f56_emis_policy("redd_nosoil","ch4","livestock") = 0` (exclude livestock CH4)

**Historical Override:**

Before 2010, always use "reddnatveg_nosoil" regardless of `c56_emis_policy` setting.

**Citation:** `preloop.gms:84-91`, `input.gms:113-117`

---

### 3.8 Stage 8: Age-Class-Specific C Price for Afforestation

**File:** `preloop.gms:93-124`

```gams
*initialize age-class dependent C price with same C price for all age-classes
p56_c_price_aff(t_all,i,ac) = im_pollutant_prices(t_all,i,"co2_c","%c56_cprice_aff%");
*Shift C prices in age-classes for reflecting foresight.
p56_c_price_aff(t_all,i,ac)$(ord(t_all)+ac.off<card(t_all)) = p56_c_price_aff(t_all+ac.off,i,"ac0");
*limit foresight to X years
ac_exp(ac)$(ac.off = s56_c_price_exp_aff/5) = yes;
p56_c_price_aff(t_all,i,ac)$(ac.off >= s56_c_price_exp_aff/5) = sum(ac_exp, p56_c_price_aff(t_all,i,ac_exp));
```

**What This Does:**

Constructs `p56_c_price_aff(t,i,ac)` where each age class ac receives the C price expected when that age class matures.

**Price Foresight Logic:**

1. **Initialize:** All age classes start with current C price
2. **Shift forward:** ac5 in 2020 gets ac0's price in 2025, ac10 gets 2030's price, etc.
3. **Limit horizon:** After `s56_c_price_exp_aff` years (default 50), price held constant

**Example:**

If 2020 C price = $50/tC, 2030 = $100/tC, 2040 = $150/tC:
- In 2020 optimization:
  - ac0 (plant now): $50/tC
  - ac5 (matures 2025): $75/tC (interpolated)
  - ac10 (matures 2030): $100/tC
  - ac20 (matures 2040): $150/tC
  - ac30+ (beyond horizon): $150/tC (constant)

**Rationale:**

Afforestation decisions depend on **expected future revenue**, not current prices. Perfect foresight up to 50 years represents forward-looking investors (governments, carbon projects).

**Citation:** `preloop.gms:93-124`

---

## 4. Interface Variables

### 4.1 Outputs (Provided to Other Modules)

**vm_emission_costs(i)** - Total regional emission costs (mio. USD17MER/yr)
**Provided to:** Module 11 (Costs) → Enters objective function
**Calculated by:** Equation q56_emission_costs
**Citation:** `declarations.gms:39`

---

**vm_reward_cdr_aff(i)** - Regional CDR rewards from afforestation (mio. USD17MER/yr)
**Provided to:** Module 11 (Costs) → **Negative sign** → Reduces costs
**Calculated by:** Equations q56_reward_cdr_aff_reg and q56_reward_cdr_aff
**Citation:** `declarations.gms:43`

---

**vm_carbon_stock(j,land,c_pools,stockType)** - Current carbon stocks (mio. tC)
**Provided to:**
- Self (Module 56): Used in next time step as `pcm_carbon_stock` for emission calculation
- Reporting modules: Carbon accounting, validation

**Calculated by:** Land modules (30, 31, 32, 35, 58) sum to this interface variable
**Citation:** `declarations.gms:34`

---

### 4.2 Inputs (Received from Other Modules)

**From Module 51-55 (Emission Modules):**

- **vm_emissions_reg(i,emis_source,pollutants)**: Regional emissions by source and gas (Tg/yr)

**Sources include:** Enteric fermentation (CH4), fertilizer use (N2O), land-use change (CO2), peatland (CO2), etc.

**Citation:** Used in `equations.gms:17`

---

**From Module 32 (Forestry):**

- **vm_cdr_aff(j,ac,aff_effect)**: Expected carbon dioxide removal from afforestation per age class (tC/ha/yr)

**Citation:** Used in `equations.gms:77`

---

**From Module 12 (Interest Rate):**

- **pm_interest(ct,i)**: Regional discount rates (dimensionless, e.g., 0.05 = 5%)

**Citation:** Used in `equations.gms:52,78`

---

**From Land Modules (30, 31, 32, 35, 58):**

- **vm_carbon_stock(j,land,c_pools,stockType)**: Current time step carbon stocks (mio. tC)
- Modules populate different land types; Module 56 aggregates for emission accounting

**Citation:** Used in `equations.gms:22`

---

**From External Data:**

- **f56_pollutant_prices(t,i,pollutants,ghgscen56)**: GHG price scenarios (USD17MER/Tg)
- **f56_emis_policy(scen56,pollutants,emis_source)**: Emission policy matrix (0/1)

**Citation:** Used in `preloop.gms:35-91`

---

## 5. Configuration Scenarios

Module 56 provides 100+ price scenarios and 60+ policy scenarios. Key examples:

### 5.1 Price Scenarios (c56_pollutant_prices)

| Scenario | Description | 2050 CO2 Price | 2100 CO2 Price |
|----------|-------------|----------------|----------------|
| **R34M410-SSP2-NPi2025** | No additional policy (default) | ~$0/tC | ~$0/tC |
| **R34M410-SSP2-PkBudg650** | 1.5°C (650 GtCO2 budget) | ~$300/tC | ~$800/tC |
| **R34M410-SSP2-PkBudg1000** | 2°C (1000 GtCO2 budget) | ~$150/tC | ~$400/tC |
| **SSPDB-SSP2-19-REMIND-MAGPIE** | 1.9°C (SSP2 pathway) | ~$200/tC | ~$600/tC |
| **SSPDB-SSP2-Ref-REMIND-MAGPIE** | Reference (no mitigation) | ~$0/tC | ~$0/tC |

*(Approximate values; actual prices vary by region and year)*

**Citation:** `sets.gms:15-117`, `input.gms:93-96`

---

### 5.2 Emission Policy Scenarios (c56_emis_policy)

| Scenario | CO2 LULUCF | CO2 Soil | CH4 | N2O | Use Case |
|----------|------------|----------|-----|-----|----------|
| **none** | ✗ | ✗ | ✗ | ✗ | Reference (no policy) |
| **all** | ✓ | ✓ | ✓ | ✓ | Comprehensive carbon pricing |
| **all_nosoil** | ✓ | ✗ | ✓ | ✓ | Price all except soil C (measurement challenges) |
| **reddnatveg_nosoil** (default) | ✓ (natural veg only) | ✗ | ✗ | ✗ | REDD+ (reduce deforestation emissions) |
| **redd+natveg_nosoil** | ✓ (deforestation + reforestation) | ✗ | ✗ | ✗ | REDD+ with afforestation incentives |
| **sdp_all** | ✓ | ✓ | ✓ | ✓ | Sustainable Development Pathway |

**Citation:** `sets.gms:119-163`, `input.gms:113-117`

---

## 6. Key Parameters and Scalars

### 6.1 Pricing Parameters

**im_pollutant_prices(t,i,pollutants,emis_source)** - Configured GHG prices (USD17MER/Tg)
**Constructed in:** `preloop.gms:35-91` through 8-stage process
**Citation:** `declarations.gms:9`

---

**p56_c_price_aff(t,i,ac)** - Age-class-specific C price for afforestation decisions (USD17MER/tC)
**Constructed in:** `preloop.gms:93-124` with price foresight logic
**Citation:** `declarations.gms:11`

---

### 6.2 Key Scalars

**s56_c_price_induced_aff** - Enable C-price driven afforestation (1=ON, 0=OFF) / 1 /
**Citation:** `input.gms:69`

**s56_c_price_exp_aff** - Price expectation horizon for afforestation (years) / 50 /
**Citation:** `input.gms:70`

**s56_buffer_aff** - CDR buffer for permanence risk (fraction) / 0.5 /
**Citation:** `input.gms:71`

**s56_minimum_cprice** - Minimum C price floor (USD17MER/tC) / 3.67 /
**Citation:** `input.gms:67`

**s56_limit_ch4_n2o_price** - Upper limit for CH4/N2O prices (USD17MER/tC) / 4920 /
**Citation:** `input.gms:65`

**s56_cprice_red_factor** - CO2 price reduction factor / 1 /
**Citation:** `input.gms:66`

---

## 7. What This Module Does NOT Do

### 7.1 No Physical Emission Calculation

- **Does NOT calculate** emissions (CH4, N2O, CO2)
- **DOES price** emissions calculated by Modules 51-55
- Emission calculation is in source modules (livestock, soils, land-use change, etc.)

### 7.2 No Carbon Sequestration Modeling

- **Does NOT model** tree growth, photosynthesis, or carbon uptake rates
- **DOES reward** CDR calculated by Module 32 (Forestry) and Module 35 (Natural Vegetation)
- Carbon dynamics are in Module 52 (Carbon)

### 7.3 No Mitigation Technology Specification

- **Does NOT specify** how to reduce emissions (e.g., "use nitrification inhibitors" or "reduce livestock numbers")
- **DOES create incentives** via costs; MAgPIE optimization finds least-cost mitigation mix
- Technology choices emerge from cost minimization, not prescribed

### 7.4 No Climate Model

- **Does NOT model** atmospheric CO2 concentration, radiative forcing, or temperature change
- **DOES use** GHG prices that implicitly reflect climate targets (e.g., 1.5°C pathways)
- Climate impacts are external (IAM-provided price trajectories)

### 7.5 No Market Equilibrium

- **Does NOT model** carbon credit markets, supply-demand equilibrium, or price discovery
- **DOES apply** exogenous prices (from IAMs or scenarios)
- Prices are policy inputs, not model outputs

### 7.6 No Enforcement or Compliance

- **Does NOT model** monitoring, reporting, verification (MRV), or enforcement costs
- **DOES assume** perfect compliance (if policy active, all covered emissions are priced)
- Institutional barriers addressed only through optional development state scaling

---

## 8. Critical Code Patterns

### 8.1 Recursive Time Step Carbon Accounting

**Pattern:** Emissions = (previous carbon stock - current carbon stock) / timestep length (`equations.gms:22`)

**Why:** CO2 from land-use change is a stock change, not a flow. Must compare time steps.

**Implication:** First time step (1995) has no previous stock → emissions are initialization artifacts → zeroed via `preloop.gms:70`

---

### 8.2 Annuity Factor for One-Off Emissions

**Pattern:** `× m_timestep_length × price × r/(1+r)` (`equations.gms:49-52`)

**Why:** Levels one-time emissions with annual emissions for consistent optimization.

**Implication:** Without this, model would prefer deforestation (one-time penalty) over fertilizer reduction (recurring penalty), even if total emissions are equal.

---

### 8.3 Age-Class Price Shifting

**Pattern:** `p56_c_price_aff(t,i,ac) = p56_c_price_aff(t+ac.off,i,"ac0")` (`preloop.gms:118`)

**Why:** Trees planted in ac0 today will sequester most carbon when they're ac10-ac20 (10-20 years from now). Investors care about **future prices**, not current.

**Implication:** If C price expected to rise, afforestation becomes more attractive even if current price is low. This creates "carbon price anticipation" effect.

---

### 8.4 Buffer for Permanence Risk

**Pattern:** `(1-s56_buffer_aff) × vm_cdr_aff` (`equations.gms:77`)

**Why:** Afforestation carbon may be lost (fire, drought, conversion). Buffer ensures only verified, permanent CDR is credited.

**Implication:** With 50% buffer, need to sequester 2 tC to earn credit for 1 tC. Increases afforestation area needed to meet climate targets.

---

### 8.5 Policy Matrix Multiplication

**Pattern:** `im_pollutant_prices × f56_emis_policy` (`preloop.gms:87,89`)

**Why:** Single price scenario can generate many policy variants (e.g., "price CO2 only" vs. "price all gases") without creating separate price files.

**Implication:** Policy flexibility without data duplication. Can test 60 policies × 100 scenarios = 6000 combinations from 160 data files.

---

## 9. Testing and Validation

### 9.1 Equation Count Verification

```bash
grep "^[ ]*q56_" modules/56_ghg_policy/price_aug22/declarations.gms | wc -l
# Expected: 7
```

**Verified:** ✅ 7 equations

---

### 9.2 Price Configuration Validation

**After preloop:**

1. **Check prices are zero before start year:**
   ```gams
   display im_pollutant_prices;
   * All prices should be 0 for t ≤ 2010 and t ≤ c56_mute_ghgprices_until
   ```

2. **Check policy matrix application:**
   ```gams
   * If c56_emis_policy = "none", all im_pollutant_prices should be 0
   * If c56_emis_policy = "all", all gas-source combinations should have prices
   ```

3. **Check CH4/N2O caps:**
   ```gams
   * Max CH4 price ≤ 4920 × 12/44 × 28 ≈ $37,709/Tg CH4
   * Max N2O-N price ≤ 4920 × 12/44 × 265 × 44/28 ≈ $499,320/Tg N
   ```

---

### 9.3 CDR Reward Calculation Test

**After solve:**

1. **Check reward is negative cost:**
   ```gams
   * vm_reward_cdr_aff.l(i) should be positive (enters Module 11 with negative sign)
   * Should be > 0 only if afforestation occurs (vm_land("aff") > 0)
   ```

2. **Check discounting is correct:**
   ```gams
   * For r=5%, ac10 (10 years), discount factor = 1/1.05^10 ≈ 0.614
   * Verify formula: reward_ac10 ≈ CDR × price_2030 × 0.614 × 0.05/1.05
   ```

3. **Check buffer application:**
   ```gams
   * If s56_buffer_aff = 0.5, reward should be ~50% of undiscounted value
   ```

---

### 9.4 Emission Costs Sanity Check

**Expected Magnitudes (with carbon pricing):**

- **Low ambition (e.g., NDC):** $10-100 million/region/yr
- **Medium ambition (e.g., 2°C):** $100-1000 million/region/yr
- **High ambition (e.g., 1.5°C):** $500-5000 million/region/yr

**Relative Shares:**

- CO2 from land-use change: typically 40-60% of total AFOLU emission costs
- CH4 from livestock: typically 20-40%
- N2O from fertilizer: typically 10-30%

**Citation:** Order-of-magnitude checks, not exact targets

---

## 10. Common Issues and Debugging

### 10.1 Zero Emission Costs Despite Non-Zero Prices

**Symptom:** `vm_emission_costs.l(i)` = 0 even with `im_pollutant_prices` > 0.

**Likely Causes:**
1. **Policy matrix zeros out all emissions:** Check `f56_emis_policy("%c56_emis_policy%",...)` values
2. **Prices muted until future year:** Check `c56_mute_ghgprices_until` and current year
3. **Emissions themselves are zero:** Check `vm_emissions_reg` from source modules

**Diagnosis:**
```gams
display im_pollutant_prices, f56_emis_policy, vm_emissions_reg.l, v56_emis_pricing.l;
```

---

### 10.2 Unrealistic Afforestation (All Land Becomes Forest)

**Symptom:** Model converts most agricultural land to forest.

**Likely Causes:**
1. **CDR rewards too high:** C price × expected removal > agricultural profits
2. **No afforestation constraints:** Check Module 32 for area limits
3. **Buffer too low:** `s56_buffer_aff` < 0.3 may over-credit CDR

**Solutions:**
1. Reduce `s56_cprice_red_factor` to <1 (accounts for co-benefits/risks)
2. Enable afforestation constraints in Module 32
3. Increase `s56_buffer_aff` to 0.5-0.7

---

### 10.3 Negative vm_emission_costs

**Symptom:** Total emission costs are negative (revenue exceeds costs).

**Likely Cause:**
- **Expected behavior:** CDR rewards (`vm_reward_cdr_aff`) exceed emission costs in high-afforestation scenarios
- This is economically plausible if carbon sequestration is very profitable

**Check if Intended:**
- High C price (>$200/tC) + large afforestation potential → legitimately negative
- Low C price (<$50/tC) with negative costs → investigate potential bug in CDR calculation

---

### 10.4 Solver Reports "Carbon Stock Infeasible"

**Symptom:** `vm_carbon_stock` constraint infeasible.

**Likely Causes:**
1. **Initial carbon stock inconsistency:** `pcm_carbon_stock` doesn't match land modules' initial stocks
2. **Carbon dynamics in land modules violate physics:** Check Module 52, 35, 32

**Not a Module 56 issue:** Module 56 tracks stocks; land modules calculate them.

**Solution:** Verify `pcm_carbon_stock` initialization (`preloop.gms:10-11`) matches `fm_carbon_density × pcm_land`.

---

### 10.5 CH4/N2O Prices Hit Cap Unexpectedly

**Symptom:** CH4 or N2O prices plateau at ~$37,000/Tg CH4 or ~$500,000/Tg N despite input prices being higher.

**Likely Cause:**
- **Expected behavior:** `s56_limit_ch4_n2o_price` (default $4,920/tC) caps prices to prevent numerical instability
- Very high prices (equivalent to >$1000/tCO2) can cause abatement to dominate all other costs

**Solutions:**
1. If intentional high price: Increase `s56_limit_ch4_n2o_price`
2. If causing problems: Leave cap in place, recognizing real-world constraints on non-CO2 prices

---

## 11. Key Insights for Users

### 11.1 GHG Pricing is Optional, Not Default

With `c56_pollutant_prices = "SSP2-NPi2025"` (No Policy Improvement) and historical zeroing, **default runs have NO carbon pricing**. Users must explicitly select mitigation scenarios (e.g., "PkBudg650") to activate pricing.

**Implication:** Reference scenarios without climate policy require no special configuration.

---

### 11.2 Policy Choice Matters More Than Price Level

A high C price ($500/tC) with policy "reddnatveg_nosoil" (only deforestation CO2) produces **less** mitigation than moderate price ($100/tC) with "all_nosoil" (all gases except soil).

**Implication:** Comprehensive coverage (policy matrix) is often more important than price ambition for total emission reduction.

---

### 11.3 CDR Rewards Create Strong Afforestation Incentive

With C price >$100/tC and 50-year price foresight, afforestation can become **more profitable than agriculture** in land-abundant regions.

**Implication:**
- Realistic afforestation requires constraints (Module 32 land availability, Module 39 conversion costs)
- CDR buffer (50%) is essential to prevent over-crediting

---

### 11.4 One-Off Emission Treatment Prevents Deforestation Bias

Without annuity factor, deforestation would appear "cheap" (one-time cost) vs. intensification (recurring costs).

**Implication:** Annuity factor levels the playing field, ensuring deforestation is penalized proportionally to its **perpetual opportunity cost** (lost forest could sequester carbon forever).

---

### 11.5 Price Foresight Drives Anticipatory Behavior

If C price expected to reach $200/tC in 2040, afforestation in 2020 is incentivized **today** based on future revenue.

**Implication:**
- Models myopic decision-making (no foresight) vs. forward-looking investors
- Default 50-year horizon represents governments and institutional investors, not smallholders
- Reducing `s56_c_price_exp_aff` to 10-20 years models shorter-term decision-making

---

### 11.6 Development State Scaling Reflects Institutional Barriers

Even with high global C prices, countries with low development state receive reduced effective prices.

**Implication:**
- Captures reality that governance, MRV capacity, and enforcement limit carbon pricing effectiveness
- Can be controversial (perpetuates inequity) or pragmatic (reflects implementation challenges)
- Default OFF allows clean policy experiments

---

## 12. Relationship to Other Modules

### 12.1 Provides Emission Costs and CDR Rewards To

- **Module 11 (Costs):** `vm_emission_costs` (positive) and `vm_reward_cdr_aff` (negative) → Objective function
- **Downstream Impact:** ALL land-use decisions respond to GHG pricing via cost minimization

---

### 12.2 Receives Emissions From

- **Modules 51-55:** Regional emissions by source and gas (`vm_emissions_reg`)
- **Sources:** Livestock CH4, fertilizer N2O, land-use change CO2, peatland CO2, soil C, etc.

---

### 12.3 Receives CDR Estimates From

- **Module 32 (Forestry):** `vm_cdr_aff` (expected carbon removal per age class)

---

### 12.4 Receives Carbon Stocks From

- **Module 30 (Crop):** Cropland carbon
- **Module 31 (Pasture):** Pasture carbon
- **Module 32 (Forestry):** Plantation carbon
- **Module 35 (Natural Vegetation):** Forest and other natural land carbon
- **Module 58 (Peatland):** Peatland carbon

All populate `vm_carbon_stock` interface variable.

---

### 12.5 Coordinates With

- **Module 12 (Interest Rate):** Discount rates for CDR reward calculation

---

## 13. Summary

Module 56 is the **critical policy interface** that internalizes climate externalities into MAgPIE's economic optimization:

**What It Does:**
- Multiplies emissions by GHG prices to calculate costs (7 equations)
- Constructs complex price scenarios through 8-stage preloop configuration
- Calculates discounted CDR rewards for afforestation with price foresight
- Distinguishes one-off (deforestation) vs. annual (fertilizer) emissions via annuity factors
- Provides 100+ price scenarios × 60+ policy scenarios = vast policy space

**What It Doesn't Do:**
- Calculate emissions (done by Modules 51-55)
- Model carbon sequestration (done by Modules 32, 35, 52)
- Specify mitigation technologies (emergent from cost minimization)
- Model climate system or carbon markets

**Critical Principle:** Module 56 **creates incentives**, not mandates. Land-use decisions respond to prices via MAgPIE's cost minimization, finding least-cost mitigation portfolios.

**Key Dependencies:**
- **Upstream:** Emission modules (51-55), Forestry CDR (32), Carbon stocks (30,31,32,35,58), Discount rates (12)
- **Downstream:** Module 11 (Costs) → Objective function → ALL land-use decisions
- **No circular dependencies**

**Testing Priority:**
1. Verify prices are zero until policy start year
2. Check policy matrix correctly filters emission sources
3. Validate CDR reward calculation (discounting, buffer, annuity factor)
4. Confirm one-off emissions use annuity factor correctly
5. Test afforestation doesn't dominate unrealistically

**Common Use:**
- Reference scenarios: `c56_pollutant_prices = "NPi"` (No Policy)
- 2°C scenarios: `c56_pollutant_prices = "PkBudg1000"`
- 1.5°C scenarios: `c56_pollutant_prices = "PkBudg650"`
- Policy variants: Change `c56_emis_policy` (e.g., "all_nosoil", "redd+natveg_nosoil")

**For modifications:** Module 56 changes affect **climate mitigation ambition and coverage**. Always check:
1. Emission cost magnitudes (should be 10-1000 million USD/region/yr for mitigation scenarios)
2. CDR reward reasonableness (should not exceed total emission costs unless massive afforestation)
3. Policy matrix consistency (ensure intended gases and sources are priced)

---

**Documentation Status:** ✅ Fully Verified (2025-10-12)
**Verification Method:** All source files read, 7 equations verified, 708 lines analyzed, 8-stage preloop logic traced, policy matrix structure documented
**Citation Density:** 80+ file:line references
**Next Module:** Module 21 (Trade) or Module 30 (Crop) — core production/supply-demand hubs

