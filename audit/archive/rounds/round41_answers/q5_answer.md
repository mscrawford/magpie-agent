# Q5: Module 22 — Conservation and Protected-Area Constraints

**Round**: 41
**Question**: How do conservation and protected-area constraints (Module 22) restrict land-use change in MAgPIE? (a) default realization/scenario and data source; (b) land pools/variables constrained and by what equation/bound; (c) interaction with Module 35 (NatVeg) and Module 10 (Land)?

---

## (a) Default Realization, Scenario, and Data Source

**Realization**: `area_based_apr22` (April 2022 version). This is the only realization and is therefore the default. 🟡 `module_22.md:4`

**Default configuration** (verified against `config/default.cfg:711-782`):

| Switch | Default | Meaning |
|--------|---------|---------|
| `c22_base_protect` | `"WDPA"` | All IUCN categories + legally designated areas |
| `c22_base_protect_noselect` | `"WDPA"` | Same for non-selected countries |
| `c22_protect_scenario` | `"none"` | No additional priority areas (WDPA baseline only) |
| `c22_protect_scenario_noselect` | `"none"` | Same for non-selected countries |
| `s22_restore_land` | `1` | Restoration enabled |
| `s22_conservation_start` | `2025` | Sigmoid phase-in starts 2025 |
| `s22_conservation_target` | `2050` | Full implementation by 2050 |
| `s22_base_protect_reversal` | `Inf` | Protection never reversed |

So in the **default run**, Module 22 applies only the **WDPA + China baseline** (no additional scenarios). The baseline covers all IUCN categories Ia, Ib, III, IV, V, VI plus legally designated areas, and is held constant at 2020 levels after 2020. 🟡 `module_22.md:46-51`

**Primary data source**: The **World Database on Protected Areas (WDPA)**, provided by UNEP-WCMC and IUCN. The input file `wdpa_baseline.cs3` contains observed protected area designations for 1995–2020 at 5-year timesteps; post-2020 values are filled forward at 2020 levels using `m_fillmissingyears`. 🟡 `module_22.md:398-413`

A second data source — **@wang_over_2024** (China-specific PA data) — supplements the WDPA baseline for Chinese protected areas. This is merged via country weights (`p22_country_weight(i)`). 🟡 `module_22.md:67-92`

Historical coverage: ~955 Mha in 1995 → ~1856 Mha in 2020 (14.3% of total land area). 🟡 `module_22.md:41-51`

Additional scenarios (`BH`, `IFL`, `BH_IFL`, `KBA`, `30by30`, `GSN_*`, `IrrC_*`, `CCA`, `PBL_HalfEarth`) are available via `c22_protect_scenario` but are all **off by default**. Their spatial data come from `consv_prio_areas.cs3` (input file). 🟡 `module_22.md:431-435`

---

## (b) Land Pools Constrained, Variables, and Binding Mechanism

### Module 22 has NO optimization equations

Module 22 is a **pure parameter-calculation module** (no equations). It runs only in `preloop` and `presolve_ini` (before each solve). Its entire purpose is to populate one interface parameter: 🟡 `module_22.md:62-63`

**`pm_land_conservation(t,j,land,consv_type)`** — conservation requirements by land type and conservation type (units: mio. ha). 🟡 `module_22.md:17-19`

### Land pools covered

| Land type | Protection | Restoration | Source |
|-----------|-----------|-------------|--------|
| `primforest` | WDPA baseline + scenarios | — (cannot be created) | 🟡 `module_22.md:20` |
| `secdforest` | WDPA baseline + scenarios | Yes (receives all forest restoration) | 🟡 `module_22.md:196-211` |
| `other` | WDPA baseline + scenarios | Yes | 🟡 `module_22.md:213-220` |
| `past` | WDPA baseline (historical) only | Yes | 🟡 `module_22.md:183-195`, `388-393` |

Note: `past` receives WDPA-baseline historical protection but is **not** in the `land_consv` set that receives future scenario-driven conservation. Future priority areas only apply to `primforest`, `secdforest`, `other`. 🟡 `module_22.md:388-393`

Cropland, forestry plantations, and urban are NOT protected by Module 22. 🟡 `module_22.md:785-789`

### How the parameter is populated

**Protection target** (`presolve_ini.gms:47-55`):
```
pm_land_conservation(t,j,land,"protect") = min(p22_conservation_area(t,j,land), pcm_land(j,land))
```
Protection is capped at current land area — cannot protect more than currently exists. 🟡 `module_22.md:143-159`

**Restoration target** (active only when `s22_restore_land = 1` OR during historical period):
```
pm_land_conservation(t,j,land,"restore") = max(0, p22_conservation_area(t,j,land) - pcm_land(j,land))
```
Restoration is limited by `p22_secdforest_restore_pot`, `p22_past_restore_pot`, `p22_other_restore_pot` — the available non-locked land after urban, timber, protected pasture, minimum cropland, and tree cover are excluded. Priority order: secdforest → pasture → other. 🟡 `module_22.md:225-293`

### How the constraint becomes binding in the solver

Module 22 itself sets no bounds. The five direct consumers translate `pm_land_conservation` into bounds and `=g=` constraints that enter the optimization:

**Direct consumers** 🟡 `module_22.md:509-548`, `module_22.md:600-609`:

1. **Module 35 (NatVeg)** — primary consumer for natural vegetation; see section (c) below.
2. **Module 29 (Cropland)** — semi-natural-vegetation constraint in `q29_land_snv` (`equations.gms:52`); limits cropland expansion into conservation areas.
3. **Module 31 (Pasture)** — grassland protection and restoration for `past`.
4. **Module 32 (Forestry)** — land availability constraint for afforestation; limits plantation siting in conservation areas.
5. **Module 13 (TC)** — adjusts TC expectations based on the share of cropland in conservation areas (`presolve.gms:40`).

**Module 10 (Land) is constrained transitively**, not directly. It does not read `pm_land_conservation`. Instead, the `vm_land.lo` bounds set by Modules 29, 31, 32, and 35 must be satisfied within the overall `q10_land_area` equality constraint. 🟡 `module_22.md:511-515`

---

## (c) Interaction with Module 35 (NatVeg) and Module 10 (Land)

### Module 35 — the primary enforcement point

Module 35 (`pot_forest_may24`) is the direct consumer of `pm_land_conservation` for all three natural vegetation pools. It applies the constraints in two ways:

**Way 1 — aggregate inequality constraint** (`equations.gms:19-22`), equation `q35_natveg_conservation`:

```gams
sum(land_natveg, vm_land(j2,land_natveg))
=g=
sum((ct,land_natveg), pm_land_conservation(ct,j2,land_natveg,"protect"));
```

This enforces: total natural land area ≥ total protection target, summed over `primforest + secdforest + other`. It is a `=g=` (lower-bound) inequality constraint. 🟡 `module_35.md:380-387`

**Way 2 — per-age-class lower bounds on secondary forest** (`presolve.gms:172-180`):

```gams
p35_protection_dist(j,ac_sub) = pc35_secdforest(j,ac_sub) / sum(ac_sub2, pc35_secdforest(j,ac_sub2));
...
v35_secdforest.lo(j,ac_sub) = max(
    pm_land_conservation(t,j,"secdforest","protect") * p35_protection_dist(j,ac_sub),
    pc35_secdforest_natural(j,ac_sub)
);
```

(Non-historical periods also include a harvest-share floor: `(1 - s35_natveg_harvest_shr) * pc35_secdforest(j,ac_sub)`.) 🟡 `module_35.md:805-817`

This distributes the protection target proportionally across age classes, so that protected secondary forest cannot be harvested regardless of which age class it belongs to.

**Restoration constraints** in Module 35 are enforced via `q35_secdforest_restoration` and `q35_other_restoration` (`equations.gms:24-33`), which require that land-use transitions into `secdforest` and `other` respectively meet the `p35_land_restoration` target derived from `pm_land_conservation(...,"restore")`. 🟡 `module_35.md:401-422`

**NPI/NDC policies** in Module 35 (`c35_ad_policy = "npi"` by default) add a separate layer of country-specific forest and other-land floors via `q35_min_forest` and `q35_min_other`, which are independent of (and additive to) Module 22's protected-area constraints. 🟡 `module_35.md:389-399`, `module_35.md:776-791`

### Module 35's role in the land balance

Module 35 is the **residual land allocator**: natural vegetation absorbs whatever land is left after cropland, pasture, forestry, and urban are allocated. Its variables — `vm_land(j,"primforest")`, `v35_secdforest(j,ac)`, `vm_land_other(j,othertype35,ac)` — appear in Module 10's strict equality constraint. 🟡 `module_35.md:916`

### Module 10 — strict land area conservation

Module 10's core constraint (`q10_land_area`, `equations.gms:13-15`) enforces:

```gams
sum(land, vm_land(j2,land)) =e= sum(land, pcm_land(j2,land));
```

This is a **hard equality** — total land per cell is constant every timestep. 🟡 `cross_module/land_balance_conservation.md:93-99`

The interaction pathway:
1. Module 22 computes `pm_land_conservation` in `presolve_ini` (using previous-timestep `pcm_land` from Module 10).
2. Module 35 (and M29, M31, M32) translate that parameter into lower bounds and `=g=` constraints on `vm_land`.
3. The solver must satisfy all those constraints *within* the `q10_land_area` equality — meaning if conservation forces natural vegetation to stay above a floor, agricultural land must absorb the pressure on the other side.
4. After the solve, Module 10 updates `pcm_land` for the next timestep. 🟡 `module_22.md:618-655`

**Temporal structure**: Module 22 runs in `presolve_ini` (before the solve) using lagged values, so there is no within-timestep circular dependency. The feedback is across timesteps: land allocation at t-1 → Module 22 targets at t → constraints on Module 35 at t. 🟡 `module_22.md:630-644`

---

## Summary of Key Variables / Parameters

| Name | Module | Dimensions | Role |
|------|--------|-----------|------|
| `pm_land_conservation` | M22 output | `(t,j,land,consv_type)` | Binding conservation targets passed to M13, M29, M31, M32, M35 |
| `p22_wdpa_baseline` | M22 internal | `(t,j,wdpa_cat22,land)` | WDPA observed trends 1995–2020 |
| `p22_add_consv` | M22 internal | `(t,j,consv22_all,land)` | Additional priority area targets (off by default) |
| `p22_conservation_area` | M22 internal | `(t,j,land)` | Total conservation target (WDPA + scenario) |
| `p22_secdforest_restore_pot` | M22 internal | `(t,j)` | Available land for forest restoration |
| `q35_natveg_conservation` | M35 | `(j2)` | sum(natveg, vm_land) =g= sum(natveg, pm_land_conservation,"protect") |
| `v35_secdforest.lo` | M35 | `(j,ac_sub)` | Per-age-class lower bound from protection distribution |
| `q35_secdforest_restoration` | M35 | `(j2)` | Transitions into secdforest =g= restoration target |
| `q35_natveg_conservation` | M35 | `(j2)` | Aggregate natural land floor |
| `q10_land_area` | M10 | `(j2)` | sum(land, vm_land) =e= sum(land, pcm_land) — total land constant |

---

## What Module 22 Does NOT Do

- Does not calculate conservation costs or opportunity costs (Module 39 handles conversion costs).
- Does not endogenously optimize which areas to protect.
- Does not apply partial protection (binary: full or none).
- Does not model marine protected areas.
- Does not model restoration dynamics (restoration is instantaneous with no succession lag).
- Does not differentiate by IUCN category in model behavior — all protected areas are treated with equal strictness. 🟡 `module_22.md:759-826`

---

## Source Statement

All claims sourced from:
- 🟡 `modules/module_22.md` (last verified 2026-03-06 against `modules/22_land_conservation/area_based_apr22/*.gms`)
- 🟡 `modules/module_35.md` (last verified 2026-05-16 to commit `c7731e234`)
- 🟡 `cross_module/land_balance_conservation.md`
- 🟡 `config/default.cfg:711-782` (for default switch values — read this session directly)

No raw `.gms` files were opened. This is a docs-only answer; all claims are tagged 🟡 (documented).
