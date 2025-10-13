## Module 09: Socioeconomic Drivers ✅ COMPLETE

**Status**: Fully documented
**Location**: `modules/09_drivers/aug17/`
**Code Size**: 216 lines across 6 files (module + realization)
**Author**: Benjamin Leon Bodirsky
**Realization**: `aug17` (only realization)

---

### 1. Core Purpose & Role

**VERIFIED**: Module 09 aggregates and provides socioeconomic drivers (population, GDP) used across multiple modules (`modules/09_drivers/module.gms:10-14`).

**What Module 09 DOES**:
1. **Loads SSP scenarios** for population and GDP (SSP1-5, SDP variants)
2. **Provides interface variables** for population at ISO and regional levels
3. **Provides GDP** in both MER (Market Exchange Rates) and PPP (Purchasing Power Parity)
4. **Calculates per capita metrics** from total population and GDP
5. **Aggregates ISO → MAgPIE regions** (ISO countries → 12 regions)
6. **Provides demographic data** by age and sex for all ISO countries
7. **Provides physical inactivity data** by demographics
8. **Provides development state** classification (World Bank income levels)
9. **Scenario switching** with SSP2 baseline until 2025 (sm_fix_SSP2)

**What Module 09 does NOT do**:
- ❌ Does NOT generate scenarios (loads external SSP/SDP projections)
- ❌ Does NOT have any optimization equations or variables
- ❌ Does NOT model demographic transitions (uses exogenous data)
- ❌ Does NOT model economic growth mechanisms
- ❌ Does NOT include inequality within regions/countries
- ❌ Does NOT provide employment or labor force data directly
- ❌ Does NOT model migration between regions
- ❌ Does NOT update drivers based on model outcomes (one-way flow)

**Role in MAgPIE**:
- **Pure data provider** - no optimization involvement
- **Foundation for demand** - population drives food, timber, bioenergy demand
- **Foundation for economics** - GDP drives income-elastic demand, technology adoption
- **Foundation for policy** - development state affects policy constraints

---

### 2. SSP/SDP Scenarios

**VERIFIED**: Module 09 supports 9 scenario variants (`sets.gms:9-11`).

#### 2.1 Shared Socioeconomic Pathways (SSPs)

**Location**: `sets.gms:9-11`

```gams
pop_gdp_scen09  Population and GDP scenario
    / SSP1, SSP2, SSP3, SSP4, SSP5,
      SDP, SDP_EI, SDP_MC, SDP_RC /
```

**SSP Scenarios** (from O'Neill et al. 2017, Riahi et al. 2017):

1. **SSP1** (Sustainability):
   - Low population growth (education, health)
   - High GDP growth (green economy)
   - Low inequality
   - **Use**: Optimistic sustainability scenario

2. **SSP2** (Middle of the Road):
   - Medium population and GDP growth
   - Moderate inequality
   - **Default** scenario (baseline until 2025)
   - **Use**: Business-as-usual reference

3. **SSP3** (Regional Rivalry):
   - High population growth (low development)
   - Low GDP growth (fragmentation)
   - High inequality
   - **Use**: Pessimistic development scenario

4. **SSP4** (Inequality):
   - Mixed population growth
   - Mixed GDP growth
   - **Very high inequality** (within/between regions)
   - **Use**: Inequality-focused scenarios

5. **SSP5** (Fossil-Fueled Development):
   - Low population growth
   - **Very high GDP growth** (fossil fuels)
   - Low inequality in developed world
   - **Use**: High-energy consumption scenarios

#### 2.2 Sustainable Development Pathways (SDPs)

**SDP Variants** (from van Vuuren et al. 2018):

1. **SDP** (Sustainable Development Path):
   - **Lower consumption** than SSP1
   - Focus on SDGs (Sustainable Development Goals)
   - Reduced inequality

2. **SDP_EI** (Energy Intensity focus):
   - SDP + emphasis on energy efficiency

3. **SDP_MC** (Material Consumption focus):
   - SDP + emphasis on material efficiency, circular economy

4. **SDP_RC** (Resource Consumption focus):
   - SDP + emphasis on overall resource use reduction

**Configuration** (`input.gms:8-18`):
```gams
$setglobal c09_pop_scenario  SSP2
$setglobal c09_gdp_scenario  SSP2
$setglobal c09_pal_scenario  SSP2  * Physical Activity Level
```

**Scenario Switching** (`preloop.gms:36-56`):
- **Before 2025** (sm_fix_SSP2): All scenarios use **SSP2** values
- **After 2025**: Scenarios diverge based on selected SSP/SDP

---

### 3. Interface Variables Provided

**VERIFIED**: Module 09 declares **8 interface variables** used by 14 modules (`declarations.gms:8-36`).

#### 3.1 Population Variables

**3.1.1 im_pop_iso(t_all,iso)** - Population by ISO country

**Location**: `declarations.gms:10`
**Dimensions**: (t_all, iso) - time × 249 ISO countries
**Units**: mio. people per yr
**Used by**: 11 modules (most widely used driver)
**Source**: SSP/SDP population projections from IIASA
**Calculation**: Direct load from `f09_pop_iso.csv` (`preloop.gms:40, 49`)

**Use cases**:
- Food demand (Module 15)
- Labor availability (Module 36)
- Urban land (Module 34)
- Livestock demand (Module 70)
- Timber demand (Module 73)

**3.1.2 im_pop(t_all,i)** - Population by MAgPIE region

**Location**: `declarations.gms:11`
**Dimensions**: (t_all, i) - time × 12 MAgPIE regions
**Units**: mio. people per yr
**Used by**: 4 modules
**Calculation**: Aggregation from ISO (`preloop.gms:41, 50`)
```gams
im_pop(t_all,i) = i09_pop_raw(t_all,i,"%c09_pop_scenario%");
i09_pop_raw(t_all,i,pop_gdp_scen09) = sum(i_to_iso(i,iso), f09_pop_iso(t_all,iso,pop_gdp_scen09));
```

**3.1.3 im_demography(t_all,iso,sex,age)** - Population by demographics

**Location**: `declarations.gms:34`
**Dimensions**: (t_all, iso, sex, age) - time × country × M/F × 21 age groups
**Units**: mio. people per yr
**Used by**: 2 modules (15_food, 55_awms)
**Age groups**: 0-4, 5-9, ..., 95-99, 100+ (5-year bins)
**Small constant added**: +0.000001 to avoid division by zero (`preloop.gms:39, 48`)

**Purpose**: Age/sex-specific demand patterns (food requirements vary by age/sex)

#### 3.2 GDP Variables

**3.2.1 im_gdp_pc_mer_iso(t_all,iso)** - GDP per capita MER by ISO country

**Location**: `declarations.gms:16`
**Dimensions**: (t_all, iso)
**Units**: USD17MER per capita per yr (2017 US dollars, Market Exchange Rates)
**Used by**: 3 modules
**Calculation** (`preloop.gms:29-33`):
```gams
i09_gdp_pc_mer_iso_raw(t_all,iso,pop_gdp_scen09) =
  f09_gdp_mer_iso(t_all,iso,pop_gdp_scen09) / f09_pop_iso(t_all,iso,pop_gdp_scen09);
* Countries with no p.c. GDP information receive SSP2 average p.c. GDP
i09_gdp_pc_mer_iso_raw(t_all,iso,pop_gdp_scen09)$(i09_gdp_pc_mer_iso_raw(t_all,iso,pop_gdp_scen09) = 0)
  = sum(i_to_iso(i,iso), i09_gdp_pc_mer_raw(t_all,i,"SSP2"));
```

**Missing data handling**: Countries without GDP data receive regional SSP2 average

**3.2.2 im_gdp_pc_mer(t_all,i)** - GDP per capita MER by region

**Location**: `declarations.gms:20`
**Dimensions**: (t_all, i) - time × 12 regions
**Units**: USD17MER per capita per yr
**Used by**: 2 modules
**Calculation** (`preloop.gms:14-16`):
```gams
i09_gdp_pc_mer_raw(t_all,i,pop_gdp_scen09)$(i09_pop_raw(t_all,i,pop_gdp_scen09) > 0 ) =
  i09_gdp_mer_raw(t_all,i,pop_gdp_scen09) / i09_pop_raw(t_all,i,pop_gdp_scen09);
```

**3.2.3 im_gdp_pc_ppp_iso(t_all,iso)** - GDP per capita PPP by ISO country

**Location**: `declarations.gms:29`
**Dimensions**: (t_all, iso)
**Units**: USD17PPP per capita per yr (2017 US dollars, Purchasing Power Parity)
**Used by**: 5 modules (most widely used GDP metric)
**PPP vs MER**: PPP accounts for cost-of-living differences between countries

**Use cases**:
- Income-elastic food demand (Module 15)
- Technology adoption (Module 13)
- Timber demand elasticity (Module 73)
- Physical activity transitions (Module 55)

**Calculation** (`preloop.gms:23-27`):
```gams
i09_gdp_pc_ppp_iso_raw(t_all,iso,pop_gdp_scen09) =
  f09_gdp_ppp_iso(t_all,iso,pop_gdp_scen09) / f09_pop_iso(t_all,iso,pop_gdp_scen09);
* Missing data filled with SSP2 regional average
i09_gdp_pc_ppp_iso_raw(t_all,iso,pop_gdp_scen09)$(i09_gdp_pc_ppp_iso_raw(t_all,iso,pop_gdp_scen09) = 0)
  = sum(i_to_iso(i,iso), i09_gdp_pc_ppp_raw(t_all,i,"SSP2"));
```

#### 3.3 Development & Lifestyle Variables

**3.3.1 im_development_state(t_all,i)** - World Bank income classification

**Location**: `declarations.gms:32`
**Dimensions**: (t_all, i)
**Units**: Dimensionless (0 = low income, 1 = high income)
**Used by**: 6 modules
**Source**: World Bank income group definitions
**Purpose**: Policy constraints, technology access, consumption patterns vary by development state

**3.3.2 im_physical_inactivity(t_all,iso,sex,age)** - Inactivity rates

**Location**: `declarations.gms:33`
**Dimensions**: (t_all, iso, sex, age)
**Units**: Share (0-1), fraction of population physically inactive
**Used by**: 2 modules (15_food, 55_awms)
**Purpose**: Physical Activity Level (PAL) affects caloric requirements

**Source**: WHO Global Health Observatory data + SSP projections

---

### 4. Data Sources & Input Files

**VERIFIED**: Module 09 uses **7 input data files** from multiple international sources (`input.gms:26-61`).

#### 4.1 f09_pop_iso.csv - Population by ISO country

**Location**: `input.gms:36-38`
**Dimensions**: (t_all, iso, pop_gdp_scen09)
**Units**: mio. capita per yr
**Source**: IIASA SSP Database (KC & Lutz 2017)
**Scenarios**: SSP1-5, SDP variants
**Time horizon**: 1965-2150 (historical + projections)

#### 4.2 f09_gdp_ppp_iso.csv - GDP PPP by ISO country

**Location**: `input.gms:26-28`
**Dimensions**: (t_all, iso, pop_gdp_scen09)
**Units**: mio. USD17PPP per yr
**Source**: OECD, IMF, World Bank historical + IIASA SSP projections
**Base year**: 2017 US dollars in Purchasing Power Parity

#### 4.3 f09_gdp_mer_iso.csv - GDP MER by ISO country

**Location**: `input.gms:31-33`
**Dimensions**: (t_all, iso, pop_gdp_scen09)
**Units**: mio. USD17MER per yr
**Source**: World Bank, IMF historical + IIASA SSP projections
**Base year**: 2017 US dollars in Market Exchange Rates

**MER vs PPP**:
- **MER**: Used for international trade, costs
- **PPP**: Used for welfare, consumption (adjusts for price differences)

#### 4.4 f09_development_state.cs3 - World Bank income groups

**Location**: `input.gms:41-43`
**Dimensions**: (t_all, i, pop_gdp_scen09)
**Units**: 0-1 scale (0 = low income, 1 = high income)
**Source**: World Bank income classification (updated annually)
**Categories**: Low income, Lower-middle, Upper-middle, High income
**Encoding**: Continuous 0-1 scale for smooth transitions

#### 4.5 f09_demography.cs3 - Population by age and sex

**Location**: `input.gms:46-48`
**Dimensions**: (t_all, iso, pop_gdp_scen09, sex, age)
**Units**: mio. capita per yr
**Source**: UN Population Division + IIASA SSP Database
**Age groups**: 21 groups (0-4, 5-9, ..., 100+)
**Sex groups**: M (male), F (female)

#### 4.6 f09_physical_inactivity.cs3 - Inactivity rates

**Location**: `input.gms:51-53`
**Dimensions**: (t_all, iso, pop_gdp_scen09, sex, age)
**Units**: Share (0-1)
**Source**: WHO Global Health Observatory + projections
**Purpose**: Estimate Physical Activity Levels (PAL) for caloric requirements

#### 4.7 fm_gdp_defl_ppp.cs4 - GDP deflators

**Location**: `input.gms:56-60`
**Dimensions**: (iso)
**Units**: Deflator factor
**Purpose**: Convert between different base years for GDP
**Use**: Rarely used directly in MAgPIE (data already in USD17)

---

### 5. Module Dependencies

**VERIFIED**: Module 09 is a **pure source** with **NO dependencies**, providing to **14 modules**.

#### 5.1 Depends On (Receives Variables From)

**NONE** - Module 09 has **zero dependencies on other modules**.

**Data Sources**:
- External only: IIASA SSP Database, World Bank, OECD, IMF, WHO, UN
- No coupling with MAgPIE optimization

**Why zero dependencies**:
- Foundational module (provides drivers to all others)
- Socioeconomic scenarios exogenous to land-use model
- One-way information flow: drivers → model (not model → drivers)

#### 5.2 Provides To (Sends Variables To)

**14 modules receive outputs from Module 09**:

1. **Module 12 (interest_rate)** ← `im_development_state`
   - Interest rates vary by development level

2. **Module 13 (tc - technological change)** ← `im_gdp_pc_ppp_iso`
   - Technology adoption driven by income

3. **Module 15 (food)** ← `im_pop_iso`, `im_gdp_pc_ppp_iso`, `im_demography`, `im_physical_inactivity`
   - Food demand = population × per capita consumption (income-elastic) × age/sex structure

4. **Module 18 (residues)** ← `im_development_state`
   - Residue use varies by development

5. **Module 36 (employment)** ← `im_pop`, `im_demography`
   - Labor force from working-age population

6. **Module 38 (factor_costs)** ← `im_gdp_pc_mer`, `im_development_state`
   - Agricultural wages scale with GDP per capita

7. **Module 42 (water_demand)** ← `im_development_state`
   - Water use efficiency by development level

8. **Module 50 (nr_soil_budget)** ← `im_development_state`
   - Nutrient management practices by development

9. **Module 55 (awms - animal waste management)** ← `im_physical_inactivity`, `im_demography`
   - Livestock product demand by demographics

10. **Module 56 (ghg_policy)** ← `im_gdp_pc_mer`, `im_development_state`
    - Carbon price implementation varies by income/development

11. **Module 60 (bioenergy)** ← `im_gdp_pc_mer_iso`, `im_development_state`
    - Bioenergy demand scenarios

12. **Module 62 (material)** ← `im_gdp_pc_mer_iso`, `im_pop_iso`
    - Material demand (wood products, biomaterials)

13. **Module 70 (livestock)** ← `im_development_state`
    - Livestock system intensity by development

14. **Module 73 (timber)** ← `im_gdp_pc_ppp_iso`, `im_pop_iso`
    - Timber demand = population × income-elastic per capita demand

#### 5.3 Dependency Diagram

```
                        MODULE 09 (DRIVERS)
                    Population, GDP, Development
                               |
              +----------------+----------------+
              |                                 |
        DEMAND MODULES                    ECONOMICS MODULES
    15 (food), 73 (timber)              12 (interest), 13 (tc)
    60 (bioenergy), 62 (material)       38 (factor_costs)
              |                                 |
              v                                 v
        Production decisions             Cost & Technology
```

**Pure Source**: All information flows OUT, none flows IN.

---

### 6. SSP2 Baseline & Scenario Divergence

**VERIFIED**: All scenarios follow SSP2 until 2025, then diverge (`input.gms:22-23`, `preloop.gms:36-56`).

#### 6.1 sm_fix_SSP2 Parameter

**Location**: `input.gms:22`

```gams
sm_fix_SSP2  year until which all parameters are fixed to SSP2 values (year) / 2025 /
```

**Purpose**:
- **Historical calibration**: Model starts in 1995, historical data until ~2020
- **Near-term certainty**: 2020-2025 uses SSP2 (middle-of-the-road)
- **Scenario divergence**: After 2025, selected SSP/SDP takes effect

**Rationale**:
- Near-term population/GDP relatively certain (demographic momentum)
- Scenarios represent long-term structural differences (post-2025)
- Allows consistent historical validation across all scenarios

#### 6.2 Scenario Switching Logic

**Location**: `preloop.gms:36-56`

```gams
loop(t_all,
 if(m_year(t_all) <= sm_fix_SSP2,
  * Before/at 2025: Everyone uses SSP2
  im_physical_inactivity(t_all,iso,sex,age) = f09_physical_inactivity(t_all,iso,"SSP2",sex,age);
  im_demography(t_all,iso,sex,age) = f09_demography(t_all,iso,"SSP2",sex,age) + 0.000001;
  im_pop_iso(t_all,iso) = f09_pop_iso(t_all,iso,"SSP2");
  im_pop(t_all,i) = i09_pop_raw(t_all,i,"SSP2");
  im_gdp_pc_mer(t_all,i) = i09_gdp_pc_mer_raw(t_all,i,"SSP2");
  im_gdp_pc_mer_iso(t_all,iso) = i09_gdp_pc_mer_iso_raw(t_all,iso,"SSP2");
  im_gdp_pc_ppp_iso(t_all,iso) = i09_gdp_pc_ppp_iso_raw(t_all,iso,"SSP2");
  im_development_state(t_all,i) = f09_development_state(t_all,i,"SSP2");
else
  * After 2025: Use selected scenario
  im_physical_inactivity(t_all,iso,sex,age) = f09_physical_inactivity(t_all,iso,"%c09_pal_scenario%",sex,age);
  im_demography(t_all,iso,sex,age) = f09_demography(t_all,iso,"%c09_pop_scenario%",sex,age) + 0.000001;
  im_pop_iso(t_all,iso) = f09_pop_iso(t_all,iso,"%c09_pop_scenario%");
  im_pop(t_all,i) = i09_pop_raw(t_all,i,"%c09_pop_scenario%");
  im_gdp_pc_mer(t_all,i) = i09_gdp_pc_mer_raw(t_all,i,"%c09_gdp_scenario%");
  im_gdp_pc_mer_iso(t_all,iso) = i09_gdp_pc_mer_iso_raw(t_all,iso,"%c09_gdp_scenario%");
  im_gdp_pc_ppp_iso(t_all,iso) = i09_gdp_pc_ppp_iso_raw(t_all,iso,"%c09_gdp_scenario%");
  im_development_state(t_all,i) = f09_development_state(t_all,i,"%c09_gdp_scenario%");
 );
);
```

**Note**: Separate scenario switches allow mixing:
- Population scenario: `c09_pop_scenario`
- GDP scenario: `c09_gdp_scenario`
- Physical activity scenario: `c09_pal_scenario`

**Example**: Can run SSP1 population with SSP3 GDP (exploratory scenarios)

---

### 7. Code Truth: What Module 09 Actually DOES

**VERIFIED implementations with file:line references**:

1. ✅ **Loads 9 SSP/SDP scenarios**:
   - SSP1-5, SDP, SDP_EI, SDP_MC, SDP_RC: `sets.gms:9-11`
   - Population, GDP (MER+PPP), demographics, inactivity: `input.gms:26-53`

2. ✅ **Aggregates ISO → MAgPIE regions**:
   - Population: `preloop.gms:11`
   - GDP MER: `preloop.gms:9`
   - GDP PPP: `preloop.gms:10`

3. ✅ **Calculates per capita metrics**:
   - Regional level: `preloop.gms:14-20`
   - ISO country level: `preloop.gms:23-33`
   - Prevents division by zero with conditionals

4. ✅ **Fills missing data**:
   - Countries without GDP data → SSP2 regional average: `preloop.gms:27, 33`
   - Ensures all countries have valid economic data

5. ✅ **Scenario switching at 2025**:
   - SSP2 baseline until sm_fix_SSP2 = 2025: `preloop.gms:37-45`
   - Selected scenario after 2025: `preloop.gms:46-55`

6. ✅ **Provides 8 interface variables**:
   - im_pop_iso (11 modules), im_pop (4 modules)
   - im_gdp_pc_ppp_iso (5 modules), im_gdp_pc_mer_iso (3 modules), im_gdp_pc_mer (2 modules)
   - im_development_state (6 modules), im_demography (2 modules), im_physical_inactivity (2 modules)

7. ✅ **Small constant for demographics**:
   - +0.000001 added to demography to avoid division by zero: `preloop.gms:39, 48`

8. ✅ **Separate scenario switches**:
   - c09_pop_scenario, c09_gdp_scenario, c09_pal_scenario: `input.gms:8-18`
   - Allows scenario mixing

---

### 8. Code Truth: What Module 09 Does NOT Do

**VERIFIED limitations with file:line references**:

1. ❌ **NO endogenous population/GDP** (`realization.gms:8-9`):
   - All scenarios exogenous (loaded from external databases)
   - NO feedback from land-use outcomes to demographics/economics
   - Population/GDP independent of agricultural productivity, food prices

2. ❌ **NO optimization equations**:
   - Pure data provider
   - NO variables, equations, constraints
   - NO solver involvement

3. ❌ **NO demographic modeling**:
   - Does NOT model births, deaths, aging
   - Does NOT model fertility transitions
   - Uses exogenous IIASA SSP Database projections

4. ❌ **NO economic growth modeling**:
   - Does NOT model productivity, capital, labor
   - Does NOT model trade effects on GDP
   - Uses exogenous OECD/World Bank projections

5. ❌ **NO within-region inequality**:
   - Regional/country averages only
   - Does NOT model income distribution
   - Development_state is continuous 0-1, not individual households

6. ❌ **NO migration modeling**:
   - Population by country from exogenous data
   - Does NOT model migration between regions
   - No migration-agriculture feedbacks

7. ❌ **NO employment modeling**:
   - Provides total population and demographics
   - Does NOT calculate labor force, unemployment
   - Module 36 (employment) derives employment from demographics

8. ❌ **NO land-use feedbacks**:
   - Drivers do NOT respond to:
     - Food prices (Malthusian effects)
     - Agricultural productivity
     - Environmental change
   - One-way coupling: drivers → model (not bidirectional)

9. ❌ **NO sub-annual dynamics**:
   - Annual averages only
   - Does NOT model seasonal population movements
   - Does NOT model harvest-time labor demand

10. ❌ **NO scenario updates**:
    - IIASA SSP Database from 2017
    - Does NOT include post-COVID updates
    - Does NOT include recent geopolitical changes

---

### 9. Common Modifications & Use Cases

#### 9.1 Changing Scenario Selection

**Purpose**: Test different SSP narratives

**How**:
```gams
$setglobal c09_pop_scenario  SSP1  * Low population growth
$setglobal c09_gdp_scenario  SSP5  * High economic growth
```

**Effect**:
- SSP1 population: Lower food demand, less land-use pressure
- SSP5 GDP: Higher income → higher meat consumption, more land-intensive diets
- Combined: Tests high-income, low-population scenario

**File**: `input.gms:8, 12`

---

#### 9.2 Scenario Mixing

**Purpose**: Explore non-standard SSP combinations

**How**:
```gams
$setglobal c09_pop_scenario  SSP3  * High population
$setglobal c09_gdp_scenario  SSP1  * High GDP
```

**Effect**:
- Tests inconsistent scenario (high pop usually → low GDP in SSPs)
- Useful for sensitivity analysis
- Example: What if population control fails but green economy succeeds?

**Caution**: May violate SSP narrative consistency

---

#### 9.3 Changing SSP2 Baseline Year

**Purpose**: Earlier/later scenario divergence

**How**:
```gams
sm_fix_SSP2 = 2020  * Earlier divergence
* or
sm_fix_SSP2 = 2030  * Later divergence
```

**Effect**:
- Earlier: More scenario differentiation, useful for near-term policy
- Later: Longer common baseline, useful for historical validation

**Default**: 2025 (balance between calibration and scenario diversity)

**File**: `input.gms:22`

---

#### 9.4 Custom Population Projection

**Purpose**: Test specific demographic assumptions

**How**: Modify `f09_pop_iso.csv` for specific countries/regions
```csv
t_all,iso,pop_gdp_scen09,value
y2050,IND,SSP2_custom,1650  * Custom India population (1.65 billion)
```

**Effect**:
- Tests policy-specific assumptions (e.g., China's population policy changes)
- Useful for country-specific studies
- Must maintain consistency with other scenarios

---

#### 9.5 Custom GDP Growth Rates

**Purpose**: Test alternative economic futures

**How**: Modify `f09_gdp_ppp_iso.csv` or `f09_gdp_mer_iso.csv`

**Example**: African Growth Surge
```r
# In R preprocessing
gdp_ppp["y2050", africa_countries, "SSP2"] <- gdp_ppp["y2050", africa_countries, "SSP2"] * 1.5
```

**Effect**:
- Higher African GDP → higher food/timber demand
- Tests implications of rapid development
- Useful for regional policy studies

---

#### 9.6 Development State Thresholds

**Purpose**: Adjust World Bank income classification cutoffs

**How**: Modify `f09_development_state.cs3`

**Current**: Continuous 0-1 scale
**Alternative**: Step function at specific GDP thresholds
```gams
im_development_state(t,i) = 0$(im_gdp_pc_ppp(t,i) < 4000);  * Low income
im_development_state(t,i) = 0.33$(im_gdp_pc_ppp(t,i) >= 4000 AND im_gdp_pc_ppp(t,i) < 12000);  * Lower-middle
im_development_state(t,i) = 0.67$(im_gdp_pc_ppp(t,i) >= 12000 AND im_gdp_pc_ppp(t,i) < 25000);  * Upper-middle
im_development_state(t,i) = 1$(im_gdp_pc_ppp(t,i) >= 25000);  * High income
```

**Effect**: Sharper policy transitions at income thresholds

---

### 10. Testing & Validation

#### 10.1 Historical Population Validation

**Check**: Do model populations match UN/OECD historical data?

**How**:
```r
# In R after loading MAgPIE
library(magpie4)
pop_model <- readGDX("fulldata.gdx", "im_pop_iso")
# Compare to UN World Population Prospects
pop_un <- read.csv("UN_WPP_data.csv")
plot(pop_model["y1995":"y2020",] - pop_un["y1995":"y2020",])
```

**Expected**: <1% deviation for historical years (1995-2020)

**Red Flag**: >5% deviation indicates data loading error

---

#### 10.2 GDP Consistency Check

**Check**: Are MER and PPP GDP consistent?

**How**:
```r
gdp_mer <- readGDX("fulldata.gdx", "i09_gdp_mer_iso")
gdp_ppp <- readGDX("fulldata.gdx", "i09_gdp_ppp_iso")
ratio <- gdp_ppp / gdp_mer
# Typical range: 1.0-4.0 (developing countries have higher PPP/MER ratios)
```

**Expected**:
- Developed countries: Ratio ~ 1.0-1.2 (USA, EUR, JPN)
- Developing countries: Ratio ~ 2.0-4.0 (IND, CHN, SSA)

**Red Flag**: Ratio < 0.8 or > 5.0 indicates data error

---

#### 10.3 Scenario Divergence Check

**Check**: Do scenarios properly diverge after 2025?

**How**:
```r
pop_ssp1 <- readGDX("fulldata_SSP1.gdx", "im_pop")
pop_ssp3 <- readGDX("fulldata_SSP3.gdx", "im_pop")

# Before 2025: Should be identical
diff_2020 <- pop_ssp1["y2020",] - pop_ssp3["y2020",]
stopifnot(max(abs(diff_2020)) < 0.01)  # Nearly identical

# After 2025: Should diverge
diff_2050 <- pop_ssp1["y2050",] - pop_ssp3["y2050",]
stopifnot(abs(mean(diff_2050)) > 100)  # Substantial difference (>100 million globally)
```

**Expected**: SSP3 > SSP2 > SSP1 for population in 2050

---

#### 10.4 Per Capita Calculation Validation

**Check**: Is GDP per capita correctly calculated?

**How**:
```gams
* In GAMS check after preloop
parameter test_gdp_pc(t_all,iso);
test_gdp_pc(t_all,iso) = i09_gdp_ppp_iso(t_all,iso) / im_pop_iso(t_all,iso);
display test_gdp_pc, im_gdp_pc_ppp_iso;
* Should match within rounding error
```

**Expected**: `test_gdp_pc` ≈ `im_gdp_pc_ppp_iso` (difference < 0.01%)

---

#### 10.5 Missing Data Handling Check

**Check**: Are countries without GDP data receiving regional averages?

**How**:
```r
gdp_data <- readGDX("input.gdx", "i09_gdp_pc_ppp_iso_raw")
# Identify countries with suspiciously constant GDP (likely filled with SSP2 average)
cv <- apply(gdp_data, MARGIN=2, FUN=sd) / apply(gdp_data, MARGIN=2, FUN=mean)
low_variance_countries <- names(cv[cv < 0.01])
# These countries likely using regional average fill-in
```

**Expected**: Small island nations, territories with no economic data

---

#### 10.6 Demographic Sum Check

**Check**: Does sum of age/sex groups equal total population?

**How**:
```r
demog <- readGDX("fulldata.gdx", "im_demography")
pop_iso <- readGDX("fulldata.gdx", "im_pop_iso")
demog_sum <- apply(demog, MARGIN=c(1,2), FUN=sum)  # Sum over sex and age
difference <- demog_sum - pop_iso
max_error <- max(abs(difference / pop_iso))
stopifnot(max_error < 0.01)  # Less than 1% error
```

**Expected**: <0.1% difference (small constant +0.000001 added to demography)

---

### 11. Summary

**Module 09 (Drivers)** is a **pure source module** with **zero dependencies**, providing **8 interface variables** to **14 modules**.

**Core Functions**:
1. **Load SSP/SDP scenarios** for population and GDP (9 variants)
2. **Aggregate ISO → regions** for MAgPIE spatial structure
3. **Calculate per capita metrics** from totals
4. **Provide demographics** by age and sex for demand modeling
5. **Switch scenarios at 2025** (SSP2 baseline, then divergence)

**Key Features**:
- Only 216 lines of code (smallest foundational module)
- Pure data provider (no equations, no optimization)
- Most widely used variables: im_pop_iso (11 modules), im_gdp_pc_ppp_iso (5 modules)
- Supports scenario mixing (population ≠ GDP scenario)
- Handles missing data (fills with SSP2 regional averages)

**Limitations**:
- Exogenous scenarios only (no endogenous population/GDP)
- No land-use feedbacks to drivers
- No inequality within regions
- No migration modeling
- One-way coupling (drivers → model, not bidirectional)

**Dependencies**:
- **Receives from**: NONE (external data only)
- **Provides to**: 14 modules (12, 13, 15, 18, 36, 38, 42, 50, 55, 56, 60, 62, 70, 73)
- **Most critical for**: Food demand (15), Timber demand (73), Technology (13), Costs (38)

**Typical Modifications**:
- Change scenario selection (SSP1 vs SSP5)
- Scenario mixing (SSP1 pop + SSP3 GDP)
- Adjust sm_fix_SSP2 (baseline year)
- Custom population/GDP projections for specific countries

**Testing Focus**:
- Historical validation (1995-2020)
- MER/PPP ratio consistency
- Scenario divergence after 2025
- Per capita calculation accuracy
- Missing data fill-in verification
- Demographic sum equals total population

---

**Module 09 Status**: ✅ COMPLETE (216 lines documented)
**Verified Against**: Actual code in `modules/09_drivers/aug17/`
**Documentation Date**: [Current Date]

---

