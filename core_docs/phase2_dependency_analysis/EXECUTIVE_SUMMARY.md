# MAgPIE Module Dependency Analysis - Executive Summary

**Analysis Date:** 2025-10-10
**MAgPIE Version:** develop branch (commit beb125fe0)
**Total Modules Analyzed:** 45

---

## Key Findings

### 1. System Overview
- **Total Interface Variables:** 115
  - 81 vm_ (model variables - optimization variables)
  - 19 pm_ (model parameters - passed between modules)
  - 15 im_ (input parameters - external data)
- **Inter-module Dependencies:** 173 unique producer-consumer relationships
- **Circular Dependencies Found:** 26 cycles (indicating tightly coupled subsystems)

### 2. Module Centrality Analysis (Hub Modules)

The most connected modules in the MAgPIE system:

| Rank | Module | Total Score | Provides To | Depends On | Role |
|------|--------|-------------|-------------|------------|------|
| 1 | **11_costs** | 28 | 1 | 27 | **Cost aggregator** - collects all costs |
| 2 | **10_land** | 17 | 15 | 2 | **Land allocator** - core land use |
| 3 | **56_ghg_policy** | 16 | 13 | 3 | **Carbon/emissions hub** |
| 4 | **32_forestry** | 16 | 5 | 11 | **Forestry system** |
| 5 | **30_croparea** | 15 | 9 | 6 | **Cropland allocation** |
| 6 | **70_livestock** | 14 | 7 | 7 | **Livestock production** |
| 7 | **17_production** | 14 | 13 | 1 | **Production hub** - agricultural output |
| 8 | **09_drivers** | 14 | 14 | 0 | **Data source** - socioeconomic drivers |
| 9 | **29_cropland** | 13 | 6 | 7 | **Cropland management** |
| 10 | **35_natveg** | 12 | 5 | 7 | **Natural vegetation/forests** |

### 3. Critical Interface Variables

Most widely shared variables across modules:

**VM Variables (Model Variables):**
- `vm_land` - Used by 11 modules (land allocation)
- `vm_prod` / `vm_prod_reg` - Used by 9 modules (agricultural production)
- `vm_area` - Used by 9 modules (cropland area)
- `vm_carbon_stock` - Used by 8 modules (carbon stocks)
- `vm_bv` - Used by 7 modules (biodiversity)

**PM Parameters:**
- `pm_interest` - Used by 10 modules (interest rates for investment)
- `pm_land_start` - Used by 5 modules (initial land allocation)
- `pm_land_conservation` - Used by 5 modules (protected areas)
- `pm_carbon_density_*` - Used by 4-5 modules (carbon densities)

**IM Input Variables:**
- `im_pop_iso` - Used by 11 modules (population by country)
- `im_development_state` - Used by 6 modules (development status)
- `im_gdp_pc_ppp_iso` - Used by 5 modules (GDP per capita)

---

## Architectural Patterns

### 1. Hub-and-Spoke Pattern
- **Cost Module (11_costs)**: Pure aggregator - depends on 27 modules, provides only to optimization
- **Driver Module (09_drivers)**: Pure source - provides to 14 modules, no dependencies
- **Production Module (17_production)**: Central hub - provides to 13 modules, minimal dependencies

### 2. Circular Dependencies (Feedback Loops)

**Critical Cycles Identified:**

1. **Production-Yield-Livestock Cycle:**
   ```
   17_production ←→ 14_yields ←→ 70_livestock
   ```
   - Production depends on yields
   - Yields depend on pasture management from livestock
   - Livestock depends on production output

2. **Land-Vegetation Cycle:**
   ```
   10_land ←→ 35_natveg ←→ 22_land_conservation
   ```
   - Bidirectional land allocation between land module and natural vegetation

3. **Croparea-Irrigation Cycle:**
   ```
   30_croparea ←→ 41_area_equipped_for_irrigation
   ```
   - Cropland area determines irrigation needs
   - Irrigation capacity constrains cropland area

4. **Forestry-Land-Carbon Cycle:**
   ```
   32_forestry ←→ 30_croparea ←→ 10_land ←→ 35_natveg ←→ 56_ghg_policy
   ```
   - Complex 5-module feedback through land allocation and carbon accounting

### 3. Layer Architecture

The system exhibits a clear layered structure:

**Layer 1 - Input/Drivers (No dependencies):**
- 09_drivers (socioeconomic data)
- 28_ageclass (forest age structure)
- 45_climate (climate data)

**Layer 2 - Core Resource Allocation:**
- 10_land (land allocation)
- 12_interest_rate (economic parameters)
- 13_tc (technological change)
- 14_yields (productivity)

**Layer 3 - Sector Production:**
- 17_production (crops)
- 30_croparea (cropland)
- 31_past (pasture)
- 32_forestry (plantations)
- 35_natveg (natural forests)
- 70_livestock (animal products)

**Layer 4 - Environmental Accounting:**
- 52_carbon (carbon stocks)
- 53_methane (CH4 emissions)
- 51_nitrogen (N emissions)
- 59_som (soil organic matter)
- 58_peatland (peatland emissions)
- 44_biodiversity (biodiversity index)

**Layer 5 - Economic/Policy:**
- 56_ghg_policy (GHG pricing/policy)
- 57_maccs (mitigation options)
- 11_costs (cost aggregation)

**Layer 6 - Optimization:**
- 80_optimization (solver)

---

## Degradation System Analysis

### Module Interactions

The degradation system involves 6 key modules:

| Module | Role | Centrality | Key Dependencies |
|--------|------|------------|------------------|
| **58_peatland** | Peatland degradation/emissions | 5 | 10_land, 32_forestry, 56_ghg_policy |
| **59_som** | Soil organic matter loss | 8 | 10_land, 29_cropland, 30_croparea, 56_ghg_policy |
| **35_natveg** | Forest degradation/disturbance | 12 | 10_land, 14_yields, 52_carbon, 56_ghg_policy |
| **14_yields** | Yield impacts from degradation | 9 | 13_tc, 52_carbon, 70_livestock |
| **52_carbon** | Carbon density tracking | 5 | 56_ghg_policy |
| **56_ghg_policy** | GHG emissions/costs | 16 | 09_drivers, 12_interest_rate, 32_forestry |

**Key Findings:**
- Peatland module (58) has lowest centrality - relatively isolated
- SOM module (59) moderately integrated - feeds nitrogen budget
- Forest degradation (35_natveg) highly connected - 12 total connections
- GHG policy (56) acts as central hub for environmental modules

---

## Forestry/Timber System Analysis

### Module Subgraph

```
16_demand (product demand)
    ↓
73_timber (timber demand/costs) ←→ 32_forestry (plantations)
    ↑                                    ↑
35_natveg (natural harvest)         14_yields (productivity)
    ↑                                    ↑
28_ageclass (age structure)         13_tc (technology)
```

**Key Variables:**
- `vm_prod_forestry` - Plantation timber production (32 → 73)
- `vm_prod_natveg` - Natural forest harvest (35 → 73)
- `pm_demand_forestry` - Timber demand (73 → 32, 62_material)
- `pm_timber_yield` - Forest productivity (14 → 32, 35)
- `im_timber_prod_cost` - Production costs (73 → 32)

**Interactions:**
- Timber demand (73) drives plantation establishment (32)
- Natural forests (35) provide supplementary production
- Both feed into regional production totals (17)

---

## Critical Dependency Chains

Longest dependency chains in the system (showing information flow):

1. **Cost Chain:** `11_costs → 71_disagg_lvst → 17_production → 14_yields → 13_tc → 12_interest_rate` (Length 6)
2. **Livestock Chain:** `11_costs → 71_disagg_lvst → 17_production → 14_yields → 70_livestock → 16_demand` (Length 6)
3. **Land Chain:** `11_costs → 71_disagg_lvst → 17_production → 14_yields → 10_land → 32_forestry` (Length 6)

These chains highlight how changes in fundamental drivers (interest rates, technology, land availability) propagate through yields, production, and ultimately affect costs.

---

## Recommendations for Model Development

### 1. Module Coupling Analysis
- **High coupling detected:** 26 circular dependencies indicate tight coupling
- **Recommendation:** Consider breaking some cycles through:
  - Lagged variables (use previous timestep values)
  - Iterative solution approaches
  - Clearer separation of optimization variables vs. parameters

### 2. Testing Strategy
- **Critical path:** Test changes to modules 10, 17, 56, 09 first (highest centrality)
- **Isolated modules:** Modules 37, 45, 54 have minimal connections - safe for independent testing
- **Cycle testing:** Always test complete cycles together:
  - Production-Yields-Livestock (17-14-70)
  - Land-Vegetation (10-35)
  - Croparea-Irrigation (30-41)

### 3. Interface Variable Management
- **Most critical variables to track:**
  - `vm_land` (11 consumers)
  - `vm_prod` / `vm_prod_reg` (9 consumers each)
  - `pm_interest` (10 consumers)
  - `im_pop_iso` (11 consumers)
- **Recommendation:** Document and version control changes to these carefully

### 4. Degradation System Enhancement
- **Current state:** Relatively modular, especially peatland (58)
- **Opportunity:** Could expand degradation features in 14_yields and 35_natveg without major ripple effects
- **Caution:** Changes to 56_ghg_policy affect 13 modules - requires comprehensive testing

### 5. Module Independence
- **Most independent modules** (good targets for isolated development):
  - 37_labor_prod (1 connection)
  - 45_climate (1 connection)
  - 54_phosphorus (1 connection)
  - 40_transport (2 connections)
  - 43_water_availability (2 connections)

---

## Dependency Matrix Summary

The full dependency matrix shows:
- **Most dependent module:** 11_costs (relies on 27 modules)
- **Most depended upon:** 09_drivers (provides to 14 modules), 10_land (provides to 15 modules)
- **Most balanced:** 70_livestock (7 in, 7 out)
- **Pure sources:** 09_drivers, 28_ageclass, 45_climate (no dependencies)
- **Pure sinks:** 80_optimization (no dependents except final objective)

---

## Files Generated

1. **dependency_analysis.json** - Complete raw dependency data
2. **dependency_report.txt** - Full textual report with matrix
3. **detailed_module_analysis.txt** - Deep dive into top 10 modules
4. **EXECUTIVE_SUMMARY.md** - This document

---

## Methodology

The analysis was performed by:
1. Scanning all `declarations.gms` files for vm_, pm_, im_ variable declarations
2. Scanning all `.gms` files for variable usage patterns
3. Building producer-consumer maps based on declarations vs. usages
4. Calculating graph metrics (centrality, chains, cycles)
5. Filtering self-dependencies to show inter-module relationships only

**Note:** This analysis captures static code dependencies. Runtime behavior may differ based on:
- Realization selection (different module implementations)
- Switch settings (on/off modules)
- Conditional code paths
