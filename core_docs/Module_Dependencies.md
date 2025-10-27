# MAgPIE Module Dependency Analysis
## Phase 2: Complete Module Interaction Mapping

### Executive Summary

This phase analyzed all 45 MAgPIE modules to create a comprehensive dependency graph showing how modules interact through interface variables. The analysis identified 115 interface variables facilitating 173 inter-module dependencies with 26 circular dependency cycles, revealing the model's complex feedback structure.

### 1. Dependency Architecture Overview

#### 1.1 Interface Variable System

MAgPIE modules communicate through three types of interface variables:

| Type | Prefix | Count | Purpose | Scope |
|------|--------|-------|---------|-------|
| **Variables** | `vm_` | 81 | Optimization variables | Shared across modules |
| **Parameters** | `pm_` | 19 | Model parameters | Calculated and shared |
| **Input Data** | `im_` | 15 | External input data | Read from files |

**Key Design Pattern:**
- **Producers**: Modules that declare interface variables (in `declarations.gms`)
- **Consumers**: Modules that use interface variables (in equations/calculations)
- **Bidirectional**: Some modules both produce and consume the same variables

#### 1.2 Module Centrality Rankings

**Top 10 Hub Modules by Total Connections:**

| Rank | Module | Total | Provides To | Depends On | Primary Role |
|------|--------|-------|-------------|------------|--------------|
| 1 | **11_costs** | 28 | 1 | 27 | Cost aggregator |
| 2 | **10_land** | 17 | 15 | 2 | Core land allocation |
| 3 | **56_ghg_policy** | 16 | 13 | 3 | Carbon/GHG hub |
| 4 | **32_forestry** | 16 | 5 | 11 | Forestry plantations |
| 5 | **30_croparea** | 15 | 9 | 6 | Cropland allocation |
| 6 | **70_livestock** | 14 | 7 | 7 | Livestock production |
| 7 | **17_production** | 14 | 13 | 1 | Production hub |
| 8 | **09_drivers** | 14 | 14 | 0 | Socioeconomic drivers |
| 9 | **29_cropland** | 13 | 6 | 7 | Cropland management |
| 10 | **35_natveg** | 12 | 5 | 7 | Natural vegetation |

### 2. Critical Interface Variables

#### 2.1 Most Connected Variables

**Variables with Highest Consumer Count:**

| Variable | Consumers | Type | Description | Key Modules |
|----------|-----------|------|-------------|-------------|
| `vm_land` | 11 | vm_ | Land allocation by type | 10_land → multiple |
| `im_pop_iso` | 11 | im_ | Population by country | 09_drivers → multiple |
| `pm_interest` | 10 | pm_ | Interest rates | 12_interest_rate → multiple |
| `vm_prod` | 9 | vm_ | Agricultural production | 17_production → multiple |
| `vm_prod_reg` | 9 | vm_ | Regional production | 17_production → multiple |
| `vm_area` | 9 | vm_ | Cropland area | 30_croparea → multiple |
| `vm_carbon_stock` | 8 | vm_ | Carbon stocks | 52_carbon → multiple |
| `vm_bv` | 7 | vm_ | Biodiversity value | 44_biodiversity → multiple |
| `vm_nr_inorg_fert_costs` | 6 | vm_ | Nitrogen fertilizer costs | 50_nr_soil_budget → multiple |

#### 2.2 Variable Categories by Function

**Land Variables:**
- `vm_land` - Total land by type (crop, past, forest, other)
- `pm_land_start` - Initial land distribution
- `pm_land_conservation` - Protected area constraints
- `vm_landexpansion` / `vm_landreduction` - Land use changes

**Production Variables:**
- `vm_prod` - Production at cell level
- `vm_prod_reg` - Regional aggregated production
- `vm_prod_forestry` - Plantation timber
- `vm_prod_natveg` - Natural forest harvest

**Economic Variables:**
- `vm_cost_*` - Various cost components (27 different types)
- `pm_interest` - Interest rates for NPV calculations
- `vm_tech_cost` - Technology costs
- `vm_nr_inorg_fert_costs` - Fertilizer costs

**Environmental Variables:**
- `vm_carbon_stock` - Carbon storage
- `vm_emissions_reg` - Regional emissions
- `pm_carbon_density_*` - Carbon densities by pool
- `vm_btc_reg` - Below-ground carbon

### 3. Module Dependency Patterns

#### 3.1 Architectural Layers

The dependency analysis reveals a clear 6-layer architecture:

```
Layer 1: Input/Drivers (No dependencies)
├── 09_drivers (socioeconomic data)
├── 28_ageclass (forest age structure)
└── 45_climate (climate data)
    ↓
Layer 2: Core Resource Allocation
├── 10_land (land allocation)
├── 12_interest_rate (economic parameters)
├── 13_tc (technological change)
└── 14_yields (productivity)
    ↓
Layer 3: Sector Production
├── 17_production (crops)
├── 30_croparea (cropland)
├── 31_past (pasture)
├── 32_forestry (plantations)
├── 35_natveg (natural forests)
└── 70_livestock (animal products)
    ↓
Layer 4: Environmental Accounting
├── 52_carbon (carbon stocks)
├── 53_methane (CH4 emissions)
├── 51_nitrogen (N emissions)
├── 59_som (soil organic matter)
├── 58_peatland (peatland emissions)
└── 44_biodiversity (biodiversity index)
    ↓
Layer 5: Economic/Policy
├── 56_ghg_policy (GHG pricing/policy)
├── 57_maccs (mitigation options)
└── 11_costs (cost aggregation)
    ↓
Layer 6: Optimization
└── 80_optimization (solver)
```

#### 3.2 Hub-and-Spoke Patterns

**Pure Sources (provide only):**
- 09_drivers → 14 modules
- 28_ageclass → 3 modules
- 45_climate → 1 module

**Pure Sinks (consume only):**
- 80_optimization ← all cost components
- 11_costs ← 27 modules

**Central Hubs (high bidirectional):**
- 17_production: 13 out, 1 in
- 10_land: 15 out, 2 in
- 56_ghg_policy: 13 out, 3 in

### 4. Circular Dependencies (Feedback Loops)

#### 4.1 Critical Feedback Cycles

**26 circular dependencies identified, key cycles:**

1. **Production-Yield-Livestock Triangle**
   ```
   17_production ←→ 14_yields ←→ 70_livestock ←→ 17_production
   ```
   - Production affects yields through intensification
   - Yields determine livestock feed availability
   - Livestock provides manure affecting yields

2. **Land-Vegetation Bidirectional**
   ```
   10_land ←→ 35_natveg
   10_land ←→ 22_land_conservation
   35_natveg ←→ 22_land_conservation
   ```
   - Natural vegetation competes for land
   - Conservation constraints affect both

3. **Croparea-Irrigation Cycle**
   ```
   30_croparea ←→ 41_area_equipped_for_irrigation
   ```
   - Cropland expansion drives irrigation
   - Irrigation capacity limits cropland

4. **Complex Forest-Carbon Cycle**
   ```
   32_forestry ←→ 30_croparea ←→ 10_land ←→ 35_natveg ←→ 56_ghg_policy
   ```
   - 5-module feedback through land competition and carbon pricing

#### 4.2 Dependency Chains

**Longest information flow paths:**

1. **Cost Aggregation Chain** (Length 6):
   ```
   12_interest_rate → 13_tc → 14_yields → 17_production → 71_disagg_lvst → 11_costs
   ```

2. **Demand-to-Land Chain** (Length 5):
   ```
   16_demand → 70_livestock → 14_yields → 10_land → 32_forestry
   ```

3. **Policy-to-Production Chain** (Length 4):
   ```
   56_ghg_policy → 32_forestry → 30_croparea → 17_production
   ```

### 5. System Subsystem Analysis

#### 5.1 Degradation System

**Module Connectivity for Degradation:**

| Module | Function | Total Connections | Key Dependencies |
|--------|----------|-------------------|------------------|
| 58_peatland | Peatland degradation | 5 | 10_land, 56_ghg_policy |
| 59_som | Soil organic matter | 8 | 10_land, 29_cropland, 56_ghg_policy |
| 35_natveg | Forest degradation | 12 | 10_land, 14_yields, 52_carbon |
| 14_yields | Yield impacts | 9 | 13_tc, 70_livestock |
| 52_carbon | Carbon tracking | 5 | 56_ghg_policy |

**Key Finding:** Peatland module is relatively isolated (centrality: 5), making it easier to modify independently.

#### 5.2 Forestry/Timber System

**Module Interaction Graph:**
```
16_demand → 73_timber ←→ 32_forestry
                ↑              ↑
          35_natveg      14_yields
                ↑              ↑
          28_ageclass      13_tc
```

**Key Variables:**
- `vm_prod_forestry` (32 → 73): Plantation production
- `vm_prod_natveg` (35 → 73): Natural forest harvest
- `pm_demand_forestry` (73 → 32): Timber demand
- `pm_timber_yield` (14 → 32, 35): Forest productivity

#### 5.3 Water System

**Relatively Isolated Subsystem:**
```
41_area_equipped_for_irrigation ←→ 30_croparea
                ↓
        42_water_demand
                ↓
        43_water_availability
```

Only 2-3 connections per module, minimal integration with core system.

### 6. Module Independence Analysis

#### 6.1 Most Independent Modules

**Minimal Dependencies (good for isolated development):**

| Module | Connections | Safe for Independent Testing |
|--------|-------------|------------------------------|
| 37_labor_prod | 1 | Yes - labor productivity |
| 45_climate | 1 | Yes - climate data |
| 54_phosphorus | 1 | Yes - phosphorus cycle |
| 40_transport | 2 | Yes - transport costs |
| 43_water_availability | 2 | Yes - water resources |
| 36_employment | 3 | Yes - employment factors |

#### 6.2 Most Dependent Modules

**Require Comprehensive Testing:**

| Module | Dependencies | Critical Interfaces |
|--------|--------------|-------------------|
| 11_costs | 27 inputs | All cost components |
| 32_forestry | 11 inputs | Land, yields, policy |
| 21_trade | 10 inputs | Production, demand |
| 16_demand | 9 inputs | Population, production |
| 60_bioenergy | 8 inputs | Land, production, policy |

### 7. Testing and Development Guidelines

#### 7.1 Change Impact Matrix

**High Impact Variables (affect 9+ modules):**
- `vm_land` - Test all land-using modules
- `vm_prod` / `vm_prod_reg` - Test entire production chain
- `pm_interest` - Test all investment decisions
- `im_pop_iso` - Test demand and land modules

**Medium Impact (5-8 modules):**
- `vm_carbon_stock` - Test environmental modules
- `vm_area` - Test cropland modules
- `pm_land_conservation` - Test land and biodiversity

**Low Impact (1-4 modules):**
- Module-specific vm_ variables
- Technical parameters

#### 7.2 Testing Strategy

**Test Order for Major Changes:**

1. **Core Testing** (Always test first):
   - 10_land - Core land allocation
   - 17_production - Production hub
   - 11_costs - Cost aggregation
   - 09_drivers - Input data

2. **Cycle Testing** (Test as units):
   - Production cycle: 17 + 14 + 70
   - Land cycle: 10 + 35 + 22
   - Croparea cycle: 30 + 41
   - Forest-carbon cycle: 32 + 30 + 10 + 35 + 56

3. **Independent Testing** (Can test alone):
   - 37, 45, 54, 40, 43, 36

#### 7.3 Module Modification Risk Assessment

**Low Risk (Few dependencies):**
- Peatland (58) - 4 dependencies
- Phosphorus (54) - 1 dependency
- Labor (37) - 1 dependency
- Climate (45) - 1 dependency

**Medium Risk (Moderate dependencies):**
- SOM (59) - 5 dependencies
- Carbon (52) - 1 dependency but 4 consumers
- Water modules (41, 42, 43) - 2-6 dependencies

**High Risk (Many dependencies or consumers):**
- Land (10) - 15 consumers
- Production (17) - 13 consumers
- GHG policy (56) - 13 consumers
- Yields (14) - 5 consumers + circular deps

### 8. Recommendations

#### 8.1 For Model Architecture

1. **Reduce Circular Dependencies:**
   - Consider lagged variables for some feedbacks
   - Separate optimization variables from parameters more clearly
   - Document which cycles are essential vs. artifacts

2. **Improve Modularity:**
   - Group water modules into single super-module
   - Consider separating cost aggregation from optimization
   - Create clearer interfaces for degradation components

3. **Interface Management:**
   - Version control interface variable changes
   - Document consumer requirements for each interface
   - Create validation tests for interface contracts

#### 8.2 For Development Workflow

1. **Module Development:**
   - Start with independent modules for new features
   - Always check centrality before modifications
   - Test circular dependency groups together

2. **Testing Protocol:**
   - Maintain test suites for each dependency cycle
   - Create integration tests for hub modules
   - Use mock data for testing independent modules

3. **Documentation:**
   - Maintain dependency graph visualization
   - Document interface variable semantics
   - Track breaking changes to interfaces

### 9. Dependency Matrix

**Full 45x45 Dependency Matrix Summary:**

```
From\To  09 10 11 12 13 14 15 16 17 18 20 21 22 28 29 30 31 32 34 35...
09_drv   .  X  .  .  .  .  X  X  .  .  .  .  .  .  .  .  .  .  .  .
10_land  .  .  .  .  .  .  .  .  .  .  .  .  X  .  X  X  X  X  X  X
11_cost  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .
...
```
(X = dependency exists, . = no dependency)

**Key Statistics:**
- Total dependencies: 173
- Average per module: 3.84
- Maximum dependencies: 27 (11_costs)
- Minimum dependencies: 0 (09_drivers, 28_ageclass, 45_climate)
- Circular dependencies: 26 cycles

### 10. Data Files Generated

All analysis outputs are available in `/tmp/magpie_analysis/`:

**Core Reports:**
- `EXECUTIVE_SUMMARY.md` - High-level findings
- `dependency_report.txt` - Full matrix and details
- `detailed_module_analysis.txt` - Deep module analysis
- `dependency_analysis.json` - Machine-readable data

**Visualizations (GraphViz DOT format):**
- `full_dependencies.dot` - Complete 45-module graph
- `core_dependencies.dot` - Top 20 modules
- `degradation_system.dot` - Degradation subsystem
- `forestry_system.dot` - Forestry subsystem

**Raw Data:**
- `vm_declarations.csv` - All vm_ variable declarations
- `pm_declarations.csv` - All pm_ variable declarations
- Module-specific usage files (90 files)

### Summary

The dependency analysis reveals MAgPIE as a tightly coupled system with clear architectural layers and significant feedback loops. The 26 circular dependencies reflect real-world feedbacks in the land-use system (e.g., production-yield interactions). Key insights:

1. **Hub modules** (10_land, 17_production, 56_ghg_policy) are critical integration points
2. **Circular dependencies** create computational complexity but model real feedbacks
3. **Independent modules** exist for safe isolated development
4. **Clear architectural layers** from inputs through optimization

This dependency map provides essential guidance for model development, testing strategies, and understanding change propagation through the system.