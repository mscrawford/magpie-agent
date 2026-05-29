# Module 10: vm_land, vm_landexpansion, vm_landreduction consumers and q10_land conservation

**Realization**: `landmatrix_dec18` (only realization)
**Source docs**: `modules/module_10.md`, `cross_module/modification_safety_guide.md`, `cross_module/land_balance_conservation.md`

---

## 1. Consumers of vm_land

`vm_land(j,land)` — current land area by type (mio. ha) — is consumed by **10 modules** (excluding the producing module 10_land itself). The authoritative list, recomputed 2026-05-23, is from `cross_module/modification_safety_guide.md:54-55`:

| Module | Use |
|--------|-----|
| **22_land_conservation** | Enforces protected area floor constraints on each land type |
| **29_cropland** | Cropland management and suitability accounting |
| **30_croparea** | Crop allocation across cells |
| **31_past** | Pasture management |
| **32_forestry** | Plantation area accounting |
| **34_urban** | Urban land expansion (exogenous) |
| **35_natveg** | Natural vegetation dynamics |
| **50_nr_soil_budget** | Nitrogen budget per land type |
| **58_peatland** | Peatland area changes |
| **59_som** | Soil carbon tracking |

Modules 11, 14, 39, 71, and 80 do NOT directly read `vm_land`. They are affected only via other Module 10 interface variables (`vm_landexpansion`, `vm_landreduction`, `vm_lu_transitions`, `pcm_land`). The broader 18-module union touched by any Module 10 output variable is listed in `cross_module/modification_safety_guide.md:57-58`.

---

## 2. Consumers of vm_landexpansion

`vm_landexpansion(j,land)` — land area gained from other types (mio. ha) — is consumed by **4 modules** (`cross_module/modification_safety_guide.md:48-49`):

| Module | Use |
|--------|-----|
| **35_natveg** | Expansion into natural vegetation land triggers secondary forest regrowth accounting |
| **39_landconversion** | Land conversion costs depend on gross expansion |
| **58_peatland** | Peatland area gained used to update peat balances |
| **59_som** | Soil organic matter responds to newly expanded land areas |

---

## 3. Consumers of vm_landreduction

`vm_landreduction(j,land)` — land area lost to other types (mio. ha) — is consumed by **2 modules** (`cross_module/modification_safety_guide.md:48-49`, confirmed by `modules/module_10.md:304,344`):

| Module | Use |
|--------|-----|
| **39_landconversion** | Land conversion costs depend on gross reduction (land abandoned or cleared) |
| **58_peatland** | Peatland area lost used to update peat emission balances |

Note: modules 35 and 59 consume `vm_landexpansion` but NOT `vm_landreduction`.

---

## 4. How q10_land enforces land conservation

Land conservation is enforced by equation **`q10_land_area`**, defined at `modules/10_land/landmatrix_dec18/equations.gms:13-15`:

```gams
q10_land_area(j2) ..
  sum(land, vm_land(j2,land)) =e=
  sum(land, pcm_land(j2,land));
```

**Mechanism:**

- **LHS** (`sum(land, vm_land(j2,land))`): the sum of all 7 current-timestep land types in cell j — an optimization variable that the solver determines.
- **RHS** (`sum(land, pcm_land(j2,land))`): the sum of all 7 land types from the **previous** timestep, stored in the carry-forward parameter `pcm_land`. This is a fixed number at solve time.
- **Operator `=e=`**: strict equality — a hard constraint with zero tolerance. The solver has no slack. If no feasible allocation exists that satisfies this equality, the model becomes infeasible.

**Expanded form** (all 7 land types; from `cross_module/land_balance_conservation.md:106-113`):
```
vm_land(j,"crop") + vm_land(j,"past") + vm_land(j,"forestry") +
vm_land(j,"primforest") + vm_land(j,"secdforest") + vm_land(j,"other") + vm_land(j,"urban")
=
pcm_land(j,"crop") + pcm_land(j,"past") + pcm_land(j,"forestry") +
pcm_land(j,"primforest") + pcm_land(j,"secdforest") + pcm_land(j,"other") + pcm_land(j,"urban")
```

**Recursive update**: After each optimization, `postsolve.gms:9` updates `pcm_land(j,land) = vm_land.l(j,land)`, so the solved allocation becomes the fixed RHS for the next timestep. The conservation constant is thus the initial total land area (from LUH2 1995 data), carried forward every 5-year step.

**What this guarantees**: In every spatial cell (of ~200 at default h200 resolution), the total land area is identical in every timestep. Land can only move between the 7 types; it cannot be created or destroyed. Any module that fixes or bounds `vm_land` for a specific land type (e.g., Module 34 prescribes urban expansion, Module 22 floors conservation areas) implicitly forces compensating changes in the remaining free types — the conservation equation is what enforces those compensating adjustments.

**Relationship to the transition matrix**: `q10_land_area` operates on totals, while `q10_transition_to` (`equations.gms:19-21`) and `q10_transition_from` (`equations.gms:23-25`) enforce consistency of the full 7x7 transition matrix `vm_lu_transitions`. Together, the three equations ensure not just that totals match but that every unit of land change is traced to a specific source-destination pair. Conservation is the aggregate consequence; the transition equations are the per-type bookkeeping.

---

## Epistemic status

- 🟡 **Documented**: All consumer lists and equation text sourced from `modules/module_10.md` and `cross_module/modification_safety_guide.md`, both read this session. Consumer counts in the safety guide were recomputed 2026-05-23 via grep across the GAMS codebase (noted in `modification_safety_guide.md:52`).
- The documentation explicitly states that modules 11/14/39/71/80 were verified to contain zero direct `vm_land(` references (`module_10.md:318`), supporting the 10-module direct-consumer count.
- Line numbers for equations cite the verified document state as of last sync (2026-03-06 for module_10.md). Code changes since that date could shift them; for critical work, verify against current `modules/10_land/landmatrix_dec18/equations.gms`.
