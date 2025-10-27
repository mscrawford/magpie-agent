# MAgPIE Core Architecture Analysis
## Phase 1: Complete Model Structure and Execution Flow

### 1. Overview

MAgPIE (Model of Agricultural Production and its Impact on the Environment) is a global land-use optimization model implemented in GAMS (General Algebraic Modeling System). The model operates as a partial equilibrium model of the land-use sector with recursive dynamic optimization.

**Core Design Principles:**
- Modular architecture with 46 independent modules
- Phase-based execution flow (8 distinct phases)
- Recursive dynamic optimization (5-year time steps)
- Spatial disaggregation (12 world regions, 200 cluster cells)

### 2. Model Entry Point and Execution Flow

#### 2.1 Main Entry Point
**File**: `main.gms`

The execution follows this sequence:

```
1. Module Setup (lines 193-253)
   ↓
2. Core Macros (line 257)
   ↓
3. Core Sets (line 261)
   ↓
4. Module Sets (line 262)
   ↓
5. Core Declarations (line 266)
   ↓
6. Module Declarations (line 267)
   ↓
7. Data Import (line 271)
   ↓
8. Equations Definition (line 275)
   ↓
9. Model Definition (line 279)
   ↓
10. Variable Scaling (line 291)
   ↓
11. General Calculations (line 295)
   ↓
12. Time Loop Execution
```

#### 2.2 Module Integration Mechanism

**File**: `modules/include.gms`

Each module is included via:
```gams
$batinclude "./modules/include.gms" [phase]
```

Where `[phase]` can be:
- `sets` - Define module-specific sets
- `declarations` - Declare variables, equations, parameters
- `input` - Load input data
- `equations` - Define optimization equations
- `scaling` - Set variable scaling factors
- `start` - Initialize before time loop
- `preloop` - Execute before each time step
- `presolve` - Prepare for solving
- `postsolve` - Post-processing after solving

### 3. Core Components

#### 3.1 Core Files Structure
```
core/
├── calculations.gms   # General calculations
├── declarations.gms    # Core variable/parameter declarations
├── load_gdx.gms       # GDX file loading utilities
├── macros.gms         # Reusable macro definitions
└── sets.gms           # Core set definitions
```

#### 3.2 Fundamental Sets (from `core/sets.gms`)

**Spatial Dimensions:**
- `i` - 12 world regions (CAZ, CHA, EUR, IND, JPN, LAM, MEA, NEU, OAS, REF, SSA, USA)
- `j` - 200 spatial clusters (aggregated from 0.5° resolution)
- `iso` - ISO country codes
- `cell(i,j)` - Mapping of clusters to regions

**Temporal Dimensions:**
- `t_all` - All time periods (1965-2150)
- `t` - Simulated periods (configured, default: 1995-2100)
- `t_past` - Historical periods (configured)
- `ct` - Current time step (dynamic)
- `pt` - Previous time step (dynamic)

**Product Categories:**
- `kall` - All products (crops, livestock, residues, timber)
- Primary crops: tece, maiz, trce, rice_pro, soybean, etc.
- Livestock: livst_rum, livst_pig, livst_chick, livst_egg, livst_milk
- Processed: oils, sugar, ethanol, etc.

**Land Types:**
- `land` - All land pools
  - Agricultural: crop, past (pasture)
  - Forest: forestry, primforest, secdforest
  - Other: urban, other

**Other Key Sets:**
- `w` - Water supply (rainfed, irrigated)
- `nutrients` - dm (dry matter), ge (energy), nr (nitrogen), p, k
- `emis_source` - Emission sources
- `ac` - Forest age classes (5-year intervals)

### 4. Module System Architecture

#### 4.1 Module Numbering Convention
```
09-16: Demand & Production Core
17-22: Trade & Conservation
28-35: Land Use Categories
36-45: Resources & Environment
50-59: Biogeochemistry
60-73: Specialized Production
80: Optimization
```

#### 4.2 Complete Module List (46 modules)

**Demand & Drivers:**
- 09_drivers - Population, GDP drivers
- 15_food - Food demand
- 16_demand - Total agricultural demand
- 60_bioenergy - Bioenergy demand
- 62_material - Material demand

**Production Systems:**
- 14_yields - Crop yields
- 17_production - Agricultural production
- 18_residues - Crop residues
- 20_processing - Food processing
- 70_livestock - Livestock systems
- 71_disagg_lvst - Livestock disaggregation
- 73_timber - Timber production

**Land Use:**
- 10_land - Land coordination
- 29_cropland - Cropland dynamics
- 30_croparea - Crop area allocation
- 31_past - Pasture management
- 32_forestry - Forest management
- 34_urban - Urban areas
- 35_natveg - Natural vegetation

**Economic Components:**
- 11_costs - Production costs
- 12_interest_rate - Interest rates
- 13_tc - Technological change
- 21_trade - International trade
- 38_factor_costs - Factor costs
- 39_landconversion - Conversion costs
- 40_transport - Transport costs

**Environmental:**
- 22_land_conservation - Protected areas
- 44_biodiversity - Biodiversity indicators
- 45_climate - Climate impacts
- 56_ghg_policy - GHG policies
- 57_maccs - Marginal abatement costs

**Water:**
- 41_area_equipped_for_irrigation - Irrigation infrastructure
- 42_water_demand - Water demand
- 43_water_availability - Water resources

**Biogeochemistry:**
- 50_nr_soil_budget - Nitrogen soil budget
- 51_nitrogen - Nitrogen emissions
- 52_carbon - Carbon dynamics
- 53_methane - Methane emissions
- 54_phosphorus - Phosphorus cycle
- 55_awms - Animal waste management
- 58_peatland - Peatland dynamics
- 59_som - Soil organic matter

**System:**
- 28_ageclass - Age class dynamics
- 36_employment - Employment
- 37_labor_prod - Labor productivity
- 80_optimization - Solver configuration

### 5. Execution Phases

#### 5.1 Phase Execution Order

Each module processes through these phases sequentially:

1. **sets** - Define module-specific sets and mappings
2. **declarations** - Declare all variables, equations, parameters
3. **input** - Load and process input data files
4. **equations** - Define optimization constraints and objectives
5. **scaling** - Configure numerical scaling for solver stability
6. **start** - One-time initialization before time loop
7. **preloop** - Execute at start of each iteration
8. **presolve** - Prepare data for current time step
9. **[SOLVE]** - Optimization solver execution
10. **postsolve** - Process results after solving

#### 5.2 Time Step Execution

```
FOR each time step t:
    1. Set ct(t) = current time
    2. Execute all module preloop phases
    3. Execute all module presolve phases
    4. SOLVE optimization model
    5. Execute all module postsolve phases
    6. Store results
    7. Advance to next time step
```

### 6. Variable Naming Convention

**Prefixes:**
- `q_` - Equations
- `v_` - Variables (optimization)
- `s_` - Scalars
- `f_` - File parameters (raw input)
- `i_` - Input parameters
- `p_` - Processing parameters
- `o_` - Output parameters
- `x_` - Critical output parameters
- `c_` - Configuration switches
- `m_` - Macros

**Module Prefixes:**
- `vm_` - Module interface variable (visible to other modules)
- `v##_` - Module-internal variable (## = module number)
- `pm_` - Module interface parameter
- `p##_` - Module-internal parameter

**Suffixes:**
- `_reg` - Regional aggregation
- `_glo` - Global aggregation
- No suffix - Highest disaggregation level

### 7. Model Definition and Solver

#### 7.1 Model Definition (line 279)
```gams
model magpie / all - m15_food_demand /;
```

This includes all equations except the food demand model equations.

#### 7.2 Solver Configuration (lines 281-287)
```gams
option iterlim    = 1000000;  # Max iterations
option reslim     = 1000000;  # Max resource units
option sysout     = Off;      # System output
option limcol     = 0;        # Column listing limit
option limrow     = 0;        # Row listing limit
option decimals   = 3;        # Output decimals
option savepoint  = 1;        # Save points for restart
```

### 8. Data Flow Architecture

#### 8.1 Input Data Sources
- **LPJmL**: Biophysical inputs (yields, water, carbon)
- **FAO**: Agricultural statistics
- **IMAGE**: Socioeconomic projections
- **Custom calibration**: Regional parameters

#### 8.2 Data Processing Pipeline
```
Raw Data Files (.csv, .cs3, .mz)
    ↓
Input Phase (f_ parameters)
    ↓
Processing Phase (i_, p_ parameters)
    ↓
Optimization Model (v_ variables)
    ↓
Output Phase (o_, x_ parameters)
    ↓
GDX Output Files
```

### 9. Key Design Patterns

#### 9.1 Realization Pattern
Each module can have multiple "realizations" (implementations):
```
modules/[##_modulename]/
├── [realization1]/
│   ├── equations.gms
│   ├── presolve.gms
│   └── ...
├── [realization2]/
└── module.gms
```

#### 9.2 Interface Pattern
Modules communicate through interface variables/parameters:
- `vm_*` - Variables visible across modules
- `pm_*` - Parameters visible across modules
- Internal objects use module number prefix

#### 9.3 Dynamic Set Pattern
Sets can be dynamic (change during execution):
```gams
h2(h) = yes;  # Dynamic superregional set
i2(i) = yes;  # Dynamic regional set
j2(j) = yes;  # Dynamic cluster set
```

### 10. Critical Execution Controls

#### 10.1 Configuration Loading
Global variables control module selection:
```gams
$setglobal land landmatrix_dec18
$setglobal yields managementcalib_aug19
```

#### 10.2 Time Step Configuration
```gams
$setglobal c_timesteps coup2100  # Coupled run to 2100
$setglobal c_past till_2015      # Historical data until 2015
```

#### 10.3 Restart Mechanism
```gams
$if set RESTARTPOINT $goto %RESTARTPOINT%
```
Allows restarting from specific execution points.

### 11. Module Dependencies

**Critical Dependencies:**
- All modules depend on: 09_drivers, 10_land
- Production chain: 14_yields → 17_production → 70_livestock
- Land chain: 35_natveg → 32_forestry → 73_timber
- Emissions chain: 52_carbon → 56_ghg_policy → 57_maccs

### 12. Performance Considerations

**Computational Bottlenecks:**
1. Spatial resolution (200 clusters)
2. Equation count (~100,000s)
3. Variable count (~1,000,000s)
4. Non-linear relationships

**Optimization Strategies:**
- Variable scaling for numerical stability
- Equation ordering for solver efficiency
- Savepoints for restart capability
- Dynamic set reduction

### Summary

MAgPIE's architecture is designed for:
1. **Modularity** - Independent modules with clear interfaces
2. **Scalability** - Handles global scale with detailed resolution
3. **Flexibility** - Multiple realizations per module
4. **Reproducibility** - Configuration-driven execution
5. **Extensibility** - Easy to add new modules/features

The phase-based execution ensures proper initialization, data flow, and solution processing across all 46 modules in a coordinated manner.