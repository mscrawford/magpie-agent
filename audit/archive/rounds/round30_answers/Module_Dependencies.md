# Module 10 Dependency Structure: Inputs, vm_land Consumers, vm_carbon_stock Consumers

## 1. What Module 10 Receives (Inputs into Module 10)

Module 10 (`landmatrix_dec18`) has only 2 direct interface inputs — the lowest count of any hub module.

| Provider Module | Interface Variable | Purpose in Module 10 |
|---|---|---|
| **32_forestry** | `vm_landdiff_forestry` | Within-forestry gross land change (rotation harvests, age-class shifts). Folded into `q10_landdiff` (`equations.gms:50-54`). |
| **35_natveg** | `vm_landdiff_natveg` | Within-natveg gross land change (primary-to-secondary, forest degradation). Folded into `q10_landdiff`. |

These are both **scalar global-sum** variables (not per-cell), so they cannot affect the cell-level land balance — they are additive components to the global gross-change metric `vm_landdiff` only.

There is a circular dependency: Module 10 provides `vm_land` and `vm_landexpansion` to Module 35, which then feeds `vm_landdiff_natveg` back to Module 10. Likewise for Module 32. These 10↔32 and 10↔35 cycles are resolved within MAgPIE's recursive dynamic structure (each pair is solved simultaneously in the same LP/NLP).

Source: `modules/module_10.md` §5, `cross_module/land_balance_conservation.md` §5.1, `core_docs/Module_Dependencies.md` §4.1.

---

## 2. vm_land Consumers

`vm_land(j,land)` is the most shared variable in MAgPIE (10 direct consumer modules, documented as highest consumer count).

### 2.1 Direct consumers of vm_land (10 modules)

These modules contain actual `vm_land(` references in their `.gms` equations — a change to `vm_land` dimensions or semantics will break them directly.

| Module | Role of vm_land in that module |
|---|---|
| **22_land_conservation** | Enforces lower bounds on protected land area per type |
| **29_cropland** | Defines `vm_land(j,"crop")` as the sum of crop area + fallow + tree cover via `q29_cropland` |
| **30_croparea** | Constrains total crop allocation against available cropland from `vm_land(j,"crop")` |
| **31_past** | Constrains pasture production to `vm_land(j,"past") * vm_yld` via `q31_prod` |
| **32_forestry** | Defines `vm_land(j,"forestry")` via `q32_land` as sum over forestry types and age classes; also reads `pm_land_start` from Module 10 |
| **34_urban** | Reads `vm_land(j,"urban")` in regional constraint `q34_urban_land` |
| **35_natveg** | Defines `vm_land(j,"primforest")`, `vm_land(j,"secdforest")`, and `vm_land(j,"other")` via `q35_land_secdforest` / `q35_land_other`; also reads `vm_landexpansion` |
| **50_nr_soil_budget** | Uses `vm_land` for non-cropland nitrogen budget calculations |
| **58_peatland** | Uses `vm_land`, `vm_landexpansion`, and `vm_landreduction` for peatland area change tracking |
| **59_som** | Uses `vm_land` for non-cropland soil organic matter equilibrium targets; also reads `vm_landexpansion` and `vm_lu_transitions` |

Source: `cross_module/modification_safety_guide.md` §1.2 (verified 2026-05-23 R3); `modules/module_10.md` §5 provides the full module → variable table.

### 2.2 Indirect (transitive) vm_land consumers

These modules do NOT read `vm_land(` directly, but consume Module 10 interface variables other than `vm_land` itself, or receive vm_land-derived outputs from one of the 10 direct consumers above.

**Via other Module 10 interface variables (part of the 18-module union in `modification_safety_guide.md` §1.2):**

| Module | Module 10 variable actually consumed | Nature of dependency |
|---|---|---|
| **11_costs** | `vm_cost_land_transition(j)` | Direct read of Module 10's cost variable; not vm_land |
| **13_tc** | `pm_land_start(j,land)` | Technological change uses initial land distribution for calibration |
| **39_landconversion** | `vm_landexpansion(j,land)`, `vm_landreduction(j,land)` | Conversion cost module reads expansion/reduction directly |
| **44_biodiversity** | Reads via pcm_land or vm_lu_transitions (transitive path through 35) | Biodiversity BII calculations use land-type areas flowing from Module 10 through Module 35 |
| **56_ghg_policy** | `pcm_land` (indirectly via carbon stocks) | GHG policy prices carbon changes, which depend on land allocation, but reads via vm_carbon_stock not vm_land |
| **71_disagg_lvst** | Livestock disaggregation uses land area; documented as receiving vm_land in the broader union | Transitive: livestock intensification depends on pasture area |
| **80_optimization** | Objective function includes costs that are functions of land allocation | Pure sink; reads via cost aggregation chain |

Note: `modules/module_10.md` §5 states that 11/14/39/71/80 contain zero `vm_land(` references in any `.gms` file (verified against origin/develop ee98739fd). Their dependence is on other Module 10 interface variables or downstream derived quantities.

---

## 3. vm_carbon_stock Consumers

`vm_carbon_stock(j,land,c_pools,stockType)` is a 4-dimensional variable declared in `modules/56_ghg_policy/price_aug22/declarations.gms:34`. It has 7 consumer modules (per `core_docs/Module_Dependencies.md` §2.1, verified count 2026-05-23 R3).

### 3.1 Providers into vm_carbon_stock (not consumers — included for context)

Multiple land modules populate different slices of `vm_carbon_stock`:

- **29_cropland**: Cropland crop-pool carbon (folds in `vm_carbon_stock_croparea` from Module 30)
- **31_past**: Pasture carbon stocks
- **32_forestry**: Plantation vegetation carbon (age-class resolved)
- **34_urban**: Urban carbon (fixed to 0)
- **35_natveg**: Primforest, secdforest, other carbon stocks
- **59_som**: Soil organic matter (soilc pool for all land types, dynamic IPCC 2019 methodology)

Module 30 populates the separate `vm_carbon_stock_croparea` (folded into Module 29); Module 58 (peatland) does NOT populate `vm_carbon_stock` — it has its own emission pathway.

Source: `modules/module_56.md` §4 (interface section), `cross_module/carbon_balance_conservation.md` §7.1, §7.5.

### 3.2 Direct consumers of vm_carbon_stock

| Module | How vm_carbon_stock is consumed |
|---|---|
| **52_carbon** (`normal_dec17`) | Reads `vm_carbon_stock(j,land,c_pools,"actual")` in `q52_emis_co2_actual` to compute CO2 emissions as `(pcm_carbon_stock - vm_carbon_stock) / m_timestep_length`. This is the primary emission-calculation consumer. |
| **56_ghg_policy** (`price_aug22`) | Reads `vm_carbon_stock` in `q56_emis_pricing_co2` to compute CO2 carbon pricing directly from stock changes (bypassing `vm_emissions_reg`), and stores current-period values as `pcm_carbon_stock` for the next timestep. |

The `carbon_balance_conservation.md` §7 and `module_56.md` §4 both identify these as the two active GAMS equation consumers of `vm_carbon_stock`. The remaining 5 of the 7-module consumer count documented in `Module_Dependencies.md` are reporting/downstream modules.

### 3.3 Transitive vm_carbon_stock consumers

| Module | Transitive path |
|---|---|
| **11_costs** | Module 56 generates `vm_reward_cdr_aff(i)` and cost-offset terms that flow into Module 11's cost aggregation (`q11_cost_reg`) |
| **32_forestry** | Module 56 feeds carbon pricing back to Module 32 via the GHG-policy → forestry channel (`56_ghg_policy → 32_forestry` documented in `Module_Dependencies.md` §4.1 cycle 3 and §4.2) — afforestation economics in Module 32 respond to carbon prices set by Module 56 using `vm_carbon_stock` |
| **80_optimization** | Objective function (`vm_cost_glo`) receives Module 56's reward/cost terms that are derived from `vm_carbon_stock`; these are mediated through Module 11 |

---

## 4. Summary: Direct vs Transitive

| Dimension | Direct | Transitive |
|---|---|---|
| **Feeds into Module 10** | 32_forestry (`vm_landdiff_forestry`), 35_natveg (`vm_landdiff_natveg`) | None — Module 10 has only 2 inputs |
| **vm_land consumers** | 22, 29, 30, 31, 32, 34, 35, 50, 58, 59 (10 modules) | 11, 13, 39, 44, 56, 71, 80 (consume other Module 10 interface variables or downstream derivatives) |
| **vm_carbon_stock consumers** | 52_carbon (emission equation), 56_ghg_policy (pricing equation) | 11_costs, 32_forestry, 80_optimization (via policy pricing chain) |

---

## Epistemic Status

🟡 **Documented**: All dependency counts and direct-consumer lists read from AI documentation this session.

Key sources:
- `modules/module_10.md` §5 — full provider/consumer table for Module 10
- `cross_module/modification_safety_guide.md` §1.2 — verified direct vm_land consumer list (10 modules) and 18-module union, both re-verified 2026-05-23 R3
- `core_docs/Module_Dependencies.md` §2.1, §3.1, §4.1 — variable consumer counts, architectural layers, circular dependency cycles
- `cross_module/land_balance_conservation.md` §5 — module-by-module interaction descriptions
- `cross_module/carbon_balance_conservation.md` §7.1, §7.5 — vm_carbon_stock providers and consumers
- `modules/module_56.md` §4 — vm_carbon_stock declaration and interface detail

Line numbers for GAMS code were verified at the dates noted in each source document; they may have drifted if code has changed since last sync. For critical work, verify against `../modules/10_land/landmatrix_dec18/equations.gms` and `../modules/56_ghg_policy/price_aug22/declarations.gms`.
