# Q4: Which MAgPIE modules are the highest-centrality / riskiest to modify, and why? (R29)

---

## 1. High-Centrality Modules: The Four Structural Hubs

According to `cross_module/modification_safety_guide.md` and `core_docs/Module_Dependencies.md`, four modules carry extreme modification risk:

| Rank | Module | Total Connections | Provides To | Risk |
|------|--------|-------------------|-------------|------|
| 1 | **11_costs** | 28 | 1 | CRITICAL |
| 2 | **10_land** | 17 | 15 | CRITICAL |
| 3 | **56_ghg_policy** | 16 | 13 | HIGH |
| 4 | **17_production** | 14 | 13 | HIGH |

Source: `core_docs/Module_Dependencies.md:29-40`, `cross_module/modification_safety_guide.md:11-17`

**Why these four?**

- **Module 11 (Costs)** has the highest dependency count: 27 source modules feed it cost variables; its output `vm_cost_glo` is the sole variable MAgPIE's solver minimizes. A missing cost term creates a "free lunch" — unbounded exploitation of the zero-cost activity (`modification_safety_guide.md:214-216`).

- **Module 10 (Land)** has the highest "provides to" count: its primary interface variable `vm_land(j,land)` is consumed directly by 10 downstream modules, and additional Module 10 interface variables (`pcm_land`, `vm_landexpansion`, `vm_landreduction`, `vm_lu_transitions`) extend the blast radius to 18 modules total. It also enforces the model's hard physical constraint `q10_land_area` — a strict equality (=e=) that will render the model infeasible if violated (`modification_safety_guide.md:62-70`; `land_balance_conservation.md:14-15`).

- **Module 56 (GHG Policy)** is the environmental-economic bridge: its output `vm_emission_costs(i)` enters the objective function via Module 11, and its price signals propagate land-use decisions through Module 32 (afforestation/CDR) and Module 60 (bioenergy). Misconfigured carbon prices can cause emission costs to dominate the objective and drive cropland area to zero (`modification_safety_guide.md:512-519`).

- **Module 17 (Production)** is the spatial aggregation hub: 13 downstream modules depend on `vm_prod_reg(i,kall)`. Breaking the cell-to-region aggregation equation `q17_prod_reg` severs the production-trade-demand system (`modification_safety_guide.md:329-360`).

---

## 2. Focused Deep-Dive: Module 10 and `vm_land`

Module 10 is chosen for the deep-dive because it holds both the highest out-degree and enforces MAgPIE's hardest physical constraint.

**Location**: `modules/10_land/landmatrix_dec18/`  
**Realization**: `landmatrix_dec18` (only realization)  
**Centrality score**: 17 connections (15 out, 2 in) — highest in the model  
Source: `modules/module_10.md:11-14`, `core_docs/Module_Dependencies.md:31-32`

### 2.1 The interface variable: `vm_land(j,land)`

**Declaration**: `modules/10_land/landmatrix_dec18/declarations.gms:14`  
**Dimensions**: cell `j` × land type `land` (7 types: crop, past, forestry, primforest, secdforest, other, urban)  
**Units**: mio. ha  
**Description**: Current-timestep land area by type. This is the foundational spatial allocation from which all land-area-dependent computations derive.

`vm_land` is verified as the most-shared variable in the model with 10 direct consuming modules (excluding the producer module 10_land):  
22, 29, 30, 31, 32, 34, 35, 50, 58, 59 (plus 71 and 80 via land-consistency constraints).  
Source: `modules/module_10.md:315-318`, `cross_module/modification_safety_guide.md:54-55`, `core_docs/Module_Dependencies.md:50`

### 2.2 Conserved by `q10_land_area` (Module 10, `equations.gms:13-15`)

The key controlling equation:

```gams
q10_land_area(j2) ..
  sum(land, vm_land(j2,land)) =e=
  sum(land, pcm_land(j2,land));
```

This is a strict equality per cell, enforced at every timestep. `pcm_land(j,land)` (previous-timestep land) is updated in `postsolve.gms:9` via `pcm_land(j,land) = vm_land.l(j,land)`. The constraint means land is physically conserved — no cell can create or destroy area.

Source: `cross_module/land_balance_conservation.md:93-104`; `modules/module_10.md:37-48`

---

## 3. What Breaks Downstream if `vm_land` Changes Incompatibly

An "incompatible change" means: altering the `land` set dimension, adding a new land type, renaming a land type, or removing a type — any change that shifts which elements of `vm_land` exist or what they represent.

The following describes what each direct consumer module would break, with the specific consuming equation and its file:line as documented.

---

### 3.1 Module 29 (Cropland) — `q29_cropland`

**File**: `modules/29_cropland/detail_apr24/equations.gms:11-12`

```gams
q29_cropland(j2)..
  vm_land(j2,"crop") =e=
    sum((kcr,w), vm_area(j2,kcr,w)) + vm_fallow(j2) + sum(ac, v29_treecover(j2,ac));
```

This equation defines total cropland as the sum of harvested area, fallow, and treecover. If the `"crop"` element of `vm_land` were renamed or removed, the equality constraint becomes undefined. The equation `q29_avl_cropland` (`equations.gms:22-23`) also bounds `vm_land(j2,"crop")` from above, and `q29_land_snv` enforces semi-natural vegetation shares within the `"crop"` land type. All three would break simultaneously.

**Cascade**: Module 29's `vm_land(j,"crop")` is in turn consumed by Module 10 to enforce `q10_land_area` — meaning a rename in `vm_land("crop")` would immediately make the land-area conservation constraint infeasible.

Source: `modules/module_29.md:73-99`, `cross_module/land_balance_conservation.md:234-254`

---

### 3.2 Module 31 (Pasture) — `q31_prod`

**File**: `modules/31_past/endo_jun13/equations.gms:16-18`

```gams
q31_prod(j2) ..
  vm_prod(j2,"pasture") =l= vm_land(j2,"past") * vm_yld(j2,"pasture","rainfed");
```

This production-capacity constraint says pasture production cannot exceed pasture area times yield. If `vm_land(j,"past")` were altered — wrong dimension, wrong name, or zero by error — the right-hand side collapses, and the solver either drives pasture production to zero (starving livestock feed) or makes the constraint infeasible. Because Module 70 (Livestock) depends on pasture feed supply through this constraint chain, loss of `vm_land(j,"past")` propagates into livestock feed deficits and then into Module 11 costs.

Module 31 also enforces a lower bound on `vm_land(j,"past")` via `presolve.gms:9`:  
`vm_land.lo(j,"past") = sum(consv_type, pm_land_conservation(t,j,"past",consv_type))`  
which requires Module 22's conservation parameter to act on the same `"past"` element.

Source: `cross_module/land_balance_conservation.md:279-303`, `modules/module_35.md:26` (dependency table)

---

### 3.3 Module 35 (Natural Vegetation) — `q35_land_secdforest`, `q35_land_other`

**Files**: `modules/35_natveg/pot_forest_may24/equations.gms:11` and `:13`

```gams
q35_land_secdforest(j2) ..
  vm_land(j2,"secdforest") =e= sum(ac, v35_secdforest(j2,ac));

q35_land_other(j2) ..
  vm_land(j2,"other") =e= sum((othertype35,ac), vm_land_other(j2,othertype35,ac));
```

Both equations tie the `vm_land` elements for natural vegetation types to Module 35's internal age-class variables. If `vm_land(j,"secdforest")` or `vm_land(j,"other")` were altered, these equalities break and the age-class accounting becomes inconsistent — the sum of age classes no longer equals the land-type total. This violates the land balance and makes the model infeasible.

Additionally, primary forest is tracked as `vm_land(j,"primforest")` with a one-way decline constraint (`presolve.gms:143-145`). If `"primforest"` were renamed or removed, the no-creation restriction disappears and primary forest could regenerate freely — a physical impossibility.

Source: `modules/module_35.md:87-103`, `cross_module/land_balance_conservation.md:359-384`

---

### 3.4 Module 50 (Nitrogen Soil Budget) — `q50_nr_inputs_pasture`

**File**: `modules/50_nr_soil_budget/macceff_aug22/equations.gms:74-80`

```gams
q50_nr_inputs_pasture(i2) ..
    v50_nr_inputs_pasture(i2)
    =e=
    sum(kli,vm_manure(i2, kli, "grazing", "nr"))
    + vm_nr_inorg_fert_reg(i2,"past")
    + sum((cell(i2,j2)), vm_land(j2,"past")) * sum(ct,f50_nr_fixation_rates_pasture(ct,i2))
    + ...
```

The third term computes area-based biological nitrogen fixation on pasture as `pasture_area × fixation_rate`. If `vm_land(j,"past")` were dimensioned differently or its values corrupted, the nitrogen fixation term becomes wrong — over- or under-estimating nitrogen inputs. This cascades to `q50_nr_bal_pasture` (the nitrogen balance inequality), which determines how much inorganic fertilizer the model applies. Incorrect nitrogen balance feeds incorrect fertilizer costs into Module 11 and incorrect emissions into Module 51 (Nitrogen Emissions).

Source: `modules/module_50.md:110-119`

---

### 3.5 Module 32 (Forestry) — `q32_land`

**File**: `modules/32_forestry/dynamic_may24/equations.gms:55-56`

```gams
q32_land(j2) ..
  vm_land(j2,"forestry") =e= sum((type32,ac), v32_land(j2,type32,ac));
```

This equality links the `"forestry"` element of `vm_land` to Module 32's internal plantation age-class variable `v32_land`. If `"forestry"` were removed from `vm_land` or redimensioned, the equation becomes undefined and all three plantation types (plant, ndc, aff) become disconnected from the land balance. Carbon-price-driven afforestation (`aff`) would lose its physical anchor, breaking the CDR mechanism that feeds `vm_cdr_aff` into Module 56 and ultimately `vm_reward_cdr_aff` into Module 11.

Module 32 also reads `pm_land_start(j,land)` (initialized from `vm_land` in `start.gms:8`), so initial plantation establishment calculations would also break.

Source: `cross_module/land_balance_conservation.md:309-328`, `modules/module_32.md:34-38`

---

### 3.6 Module 22 (Land Conservation) — `pm_land_conservation`

Module 22 has no equations, but its output parameter `pm_land_conservation(t,j,land,consv_type)` is indexed over the same `land` set as `vm_land`. It provides lower bounds to Modules 31, 35, and the land allocation in Module 10. If the `land` set were changed (e.g., a land type added), Module 22's presolve calculations — which assign protection targets by `land` element — would need updating or they silently produce zeros for the new type, eliminating conservation constraints on it.

Source: `modules/module_22.md:18-19`, `cross_module/modification_safety_guide.md:84-95`

---

### 3.7 Module 59 (Soil Organic Matter)

Module 59 (`cellpool_jan23`) receives both `vm_land` and `vm_landexpansion` from Module 10 to calculate soil organic carbon pools and transitions between land-type equilibria. It receives these variables for the IPCC 2019 stock-change-factor framework: when land transitions from one type to another, the SOC pool moves toward a new equilibrium. If `vm_land`'s land type elements changed, the mapping between land types and IPCC factors (`f59_cpeat_factor`, `f59_aglim_factor`) would silently fail, producing incorrect SOC loss or gain estimates — and incorrect `vm_nr_som` (nitrogen release) and `vm_cost_scm` (soil carbon management cost) — without the solver detecting the error.

Source: `modules/module_59.md:19-21`, `modules/module_10.md:299` (dependency table entry for 59_som)

---

## 4. Summary of the Downstream Cascade

```
vm_land(j,land) changed incompatibly
  |
  +-- q29_cropland [29/detail_apr24/equations.gms:11-12] ........... crop accounting breaks
  |     +-- q10_land_area [10/equations.gms:13-15] .................. land balance infeasible
  |
  +-- q31_prod [31/endo_jun13/equations.gms:16-18] .................. pasture production collapses
  |     +-- livestock feed deficit --> Module 70 --> Module 11
  |
  +-- q35_land_secdforest [35/pot_forest_may24/equations.gms:11] ... age-class sum breaks
  +-- q35_land_other [35/pot_forest_may24/equations.gms:13] ........ other-land sum breaks
  |     +-- land balance infeasible; forest/other carbon stocks wrong
  |
  +-- q32_land [32/dynamic_may24/equations.gms:55-56] ............... forestry disconnects
  |     +-- CDR/afforestation mechanism breaks (vm_cdr_aff, vm_reward_cdr_aff --> Module 11)
  |
  +-- q50_nr_inputs_pasture [50/macceff_aug22/equations.gms:74-80] . N fixation wrong
  |     +-- fertilizer demand wrong --> Module 11 costs wrong, Module 51 emissions wrong
  |
  +-- pm_land_conservation (Module 22) ............................... conservation bounds lost silently
  |
  +-- Module 59 SOC pools ............................................. soil carbon deltas wrong
        +-- vm_nr_som wrong --> Module 51; vm_cost_scm wrong --> Module 11
```

All paths converge on either:
1. **Model infeasibility** (land balance violated: `q10_land_area` cannot be satisfied), or
2. **Silent numerical errors** in carbon, nitrogen, and cost accounting that pass the solver but produce wrong results

---

## 5. Conservation Law Anchor

The reason Module 10 has this cascade property is that `q10_land_area` is a strict equality (=e=) — not a penalty, not an inequality. There is zero tolerance. Every module that consumes `vm_land` implicitly relies on this equality holding, because they use `vm_land` values as physical areas that must sum to the cell total. The constraint is documented and reproduced identically in:
- `modules/module_10.md:37-48` (equations section)  
- `cross_module/land_balance_conservation.md:93-129` (full derivation and expanded form)  
- `cross_module/modification_safety_guide.md:62-79` (modification risk section)

---

## Documentation Relied Upon

- `cross_module/modification_safety_guide.md` — centrality rankings, risk tiers, all 4 hubs
- `core_docs/Module_Dependencies.md:29-60` — dependency counts, hub-and-spoke table, variable consumer counts
- `cross_module/land_balance_conservation.md` — `q10_land_area`, transition matrix equations, module-by-module land-type roles
- `modules/module_10.md` — variable declarations, equation list, full provides-to table
- `modules/module_29.md` — `q29_cropland` equation (equations.gms:11-12)
- `modules/module_35.md` — `q35_land_secdforest`, `q35_land_other` (equations.gms:11,13)
- `modules/module_32.md` — `q32_land` (equations.gms:55-56), CDR/aff dependency
- `modules/module_50.md` — `q50_nr_inputs_pasture` (equations.gms:74-80)
- `modules/module_22.md` — conservation parameter structure
- `modules/module_59.md` — SOC dependencies on vm_land and vm_landexpansion

## Not in Docs

- Exact line numbers for Module 59 GAMS equations consuming `vm_land` directly are not cited in the module doc; the dependency is established at the variable-provider level in module_10.md and module_59.md (Quick Reference), but no specific consuming equation in 59's equations.gms is named with a line number.
- Module 71 (`71_disagg_lvst`) consumes `vm_land` (listed in module_10.md:313), but the specific equation in 71's equations.gms is not cited in the docs reviewed.
- The `vm_land` consumer count differs slightly between sources: `modification_safety_guide.md` (updated 2026-05-23 R3) states 10 direct consumers; `module_10.md:315-318` lists a union of 15 in the provides-to table. The discrepancy is explained by the footnote in `modification_safety_guide.md:52`: the 10-module figure counts modules that consume `vm_land` directly; the 15-module figure counts modules that consume ANY Module 10 interface variable. Both are documented as such.
