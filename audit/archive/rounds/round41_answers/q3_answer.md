# Q3: Age Classes (Module 28), Forest Growth (Module 32), and Carbon Accumulation (Module 52)

**Question**: How do age classes (Module 28) govern forest growth and carbon accumulation in MAgPIE?
(a) Full extent of the `ac` set; (b) how stands move between age classes in Module 32; (c) how standing biomass feeds Module 52 carbon stock.

---

## (a) Full Extent of the `ac` (Age Class) Set

The `ac` set has **62 elements** total 🟡 (module_28.md, overview box).

The elements are:
- `ac0, ac5, ac10, ac15, ..., ac295, ac300` — 61 regular classes in 5-year increments spanning 0–300 years
- `acx` — one catch-all element for mature/primary forests (forests that were ≥150 years old in the GFAD baseline circa 2000)

The last named regular element is **`ac300`**; `acx` is the final element in the set and has no fixed upper age limit.

The set is defined in `modules/28_ageclass/oct24/sets.gms` 🟡 (module_28.md:module_structure section). Module 28 has a single realization (`oct24`) — there are no alternative realizations.

**Provenance of the 62-element count**: GFAD v1.1 provides 15 ten-year classes. Classes 1–14 each split into two 5-year MAgPIE classes (×2 = 28 regular classes from 0–140 years, i.e., `ac5` through `ac140`... the full series runs to `ac300`). Class 15 (150+ years) maps directly to `acx` without splitting. The total span of 61 named regular classes (`ac0` through `ac300`, stepping by 5) plus `acx` = **62** 🟡 (module_28.md:age-class-system section, and the warning box explicitly states "do NOT truncate this range").

---

## (b) How Stands Move Between Age Classes in Module 32 (`dynamic_may24`)

Module 32 (`dynamic_may24`) is the only realization of the Forestry module.

### The shift mechanism

Age-class progression is a **deterministic per-timestep shift**, not an equation solved during optimization. It is applied in the **presolve phase**, before the GAMS solver runs 🟡 (module_32.md, Section 6 "Age-Class Dynamics").

**Shift size** (`presolve.gms:83`):
```
s32_shift = m_yeardiff_forestry(t) / 5
```

For a 5-year timestep: `s32_shift = 1` (each class advances one position).  
For a 10-year timestep: `s32_shift = 2` (two positions).

**Shifting logic** (`presolve.gms:89–91`):
```gams
p32_land(t,j,type32,ac)$(ord(ac) > s32_shift) = pc32_land(j,type32,ac-s32_shift);
p32_land(t,j,type32,"acx") = p32_land(t,j,type32,"acx")
                            + sum(ac$(ord(ac) > card(ac)-s32_shift), pc32_land(j,type32,ac));
```

What this does:
- Every area parcel that was in age class `ac-s32_shift` moves to age class `ac`.
- Any parcels that would advance beyond the last regular class (`ac300`) accumulate in `acx`.
- The oldest regular classes overflow into `acx`; `acx` itself is never cleared — area in it grows monotonically unless harvested.

### What governs the rate

The **rate of aging is governed entirely by `m_yeardiff_forestry(t)`** — the calendar length of the current model timestep in years 🟡 (module_28.md:dynamic-age-class-sets section). This macro is:

```gams
m_yeardiff_forestry(t) = 5$(ord(t)=1) + (m_year(t)-m_year(t-1))$(ord(t)>1)
```

The first timestep is always treated as 5 years; subsequent timesteps use the actual inter-year gap. There is no intrinsic growth equation controlling when a stand "graduates" — progression is purely calendar-time-driven. The shift is applied uniformly to all three plantation types (`plant`, `ndc`, `aff`) across all spatial cells.

### Establishment age classes vs. sub-rotation age classes

Module 28's `presolve.gms` computes two dynamic sets each timestep 🟡 (module_28.md:dynamic-age-class-sets section):

- **`ac_est`**: `ord(ac) <= m_yeardiff_forestry(t)/5` — age classes young enough to have been established during the current timestep.
- **`ac_sub`**: `ord(ac) > m_yeardiff_forestry(t)/5` — all older age classes.

Module 32 uses these to:
- Fix establishment-period stands (`ac_est`) so they **cannot** be harvested or reduced during the current timestep (`v32_hvarea_forestry.fx(j,ac_est) = 0`, `v32_land_reduction.fx(j,type32,ac_est) = 0`) 🟡 (module_28.md:usage-module-32 section).
- Apply disturbance losses only to `ac_sub` stands (`p32_disturbance_loss_ftype32(t,j,"aff",ac_sub)`, `presolve.gms:75`) and redistribute the lost area back to `ac_est`.
- Allow harvesting of `plant`-type stands in `ac_sub` once they exceed the rotation age (`p32_rotation_cellular_harvesting(t,j)`).

New establishments are distributed **evenly across all `ac_est` classes** via the equation `q32_forestry_est` (`equations.gms:231–232`):
```gams
v32_land(j2,type32,ac_est) =e= sum(ac_est2, v32_land(j2,type32,ac_est2)) / card(ac_est2);
```

So, for a 10-year timestep where `ac_est = {ac0, ac5}`, new plantation area is split 50/50 between the two youngest classes.

---

## (c) How Standing Biomass Feeds Carbon Stock in Module 52

### The carbon density lookup

Module 52 (`normal_dec17`) pre-computes **age-class-specific carbon densities** using the Chapman-Richards growth equation, applied in `start.gms:8–51` 🟡 (module_52.md, Section 2 "Age-Class Carbon Density Calculations"):

```
m_growth_vegc(S, A, k, m, ac) = S + (A−S) × (1 − exp(−k × (ac×5)))^m
```

where:
- `S` = 0 tC/ha (bare land start)
- `A` = asymptotic carbon density from LPJmL (secondary forest vegc)
- `k`, `m` = growth rate and shape parameters, climate-class-weighted from `f52_growth_par(clcl,chap_par,forest_type)`
- `ac×5` converts the age-class index to years

This produces two interface parameters:
- **`pm_carbon_density_plantation_ac(t_all,j,ac,ag_pools)`** (vegc + litc pools) — for `plant`-type stands. As of 2026-04-20, the `vegc` pool is **calibrated via bisection** in `preloop.gms` to match FAO FRA 2025 growing-stock targets when `s52_growingstock_calib = 1` (default) 🟡 (module_52.md, Section 2.C).
- **`pm_carbon_density_secdforest_ac(t_all,j,ac,ag_pools)`** — for `ndc`- and secondary-forest stands (calibrated `vegc` pool). The uncalibrated copies (`pm_carbon_density_secdforest_ac_uncalib`, `pm_carbon_density_plantation_ac_uncalib`) are used for new-establishment contexts (`aff`, NDC) where observed suppression should not be applied to newly planted trees.

### How Module 32 assembles the carbon stock

Module 32 equation **`q32_carbon`** (`equations.gms:108–109`) computes `vm_carbon_stock(j,"forestry",ag_pools,stockType)` by expanding the macro `m_carbon_stock_ac` over all types and age classes 🟡 (module_32.md, Section 4.5):

```gams
q32_carbon(j2,ag_pools,stockType) ..
  vm_carbon_stock(j2,"forestry",ag_pools,stockType) =e=
    m_carbon_stock_ac(v32_land, p32_carbon_density_ac, "type32,ac", "type32,ac_sub");
```

This expands to a weighted sum: `Σ(type32,ac) v32_land(j2,type32,ac) × p32_carbon_density_ac(t,j2,type32,ac,ag_pools)`.

The internal parameter `p32_carbon_density_ac(t,j,type32,ac,ag_pools)` is populated in `presolve.gms:58–68` by selecting the correct Module 52 output per type:
- `plant` → `pm_carbon_density_plantation_ac` (calibrated)
- `ndc` → `pm_carbon_density_secdforest_ac_uncalib` (uncalibrated; new-establishment context)
- `aff` → `pm_carbon_density_secdforest_ac_uncalib` (default, switch=0) or `pm_carbon_density_plantation_ac_uncalib` (switch=1)

### How `vm_carbon_stock` feeds CO2 emissions in Module 52

Module 52's single equation **`q52_emis_co2_actual`** (`equations.gms:16–19`) converts stock changes to emissions 🟡 (module_52.md, Section 3):

```gams
vm_emissions_reg(i2,emis_oneoff,"co2_c") =e=
  sum((cell(i2,j2), emis_land(emis_oneoff,land,c_pools)),
    (pcm_carbon_stock(j2,land,c_pools,"actual") − vm_carbon_stock(j2,land,c_pools,"actual"))
    / m_timestep_length
  );
```

- `pcm_carbon_stock` = previous timestep's stock (lagged); `vm_carbon_stock` = current (optimized) stock.
- A stock **decrease** (deforestation, harvest) → positive CO2 emission.
- A stock **increase** (afforestation, forest growth) → negative emission (sequestration).
- Division by `m_timestep_length` annualizes the stock-change flux.

`vm_carbon_stock` is declared in Module 56 (GHG Policy) and **populated by Module 32** (forestry land) as well as Modules 29, 31, 34, 35, and 59. Module 52 reads it but does not write it; it only writes `vm_emissions_reg` 🟡 (module_52.md, Interface Variables section).

### Summary of the age-class → carbon chain

```
Module 28 presolve   → ac_est, ac_sub (dynamic sets, time-varying)
Module 52 start.gms  → pm_carbon_density_plantation_ac(t,j,ac,"vegc"/"litc")
                        pm_carbon_density_secdforest_ac(t,j,ac,"vegc"/"litc")
Module 52 preloop    → calibrate vegc pool k via bisection vs. FRA 2025 GS targets
                        (reads im_forest_ageclass from M28 and pm_land_plantation from M32)
Module 32 presolve   → age-class shift: pc32_land → p32_land (via s32_shift = timestep/5)
                        populate p32_carbon_density_ac from M52 output (type-specific)
Module 32 equations  → q32_carbon: vm_carbon_stock(j,"forestry") = Σ(type,ac) area × density
Module 52 equations  → q52_emis_co2_actual: emissions = (pcm − vm_carbon_stock) / timestep
```

---

## Key Variables Cited

| Variable | Dimensions | Source/Set | Role |
|---|---|---|---|
| `ac` | 62 elements (ac0–ac300, acx) | M28 `sets.gms` | Age-class set |
| `ac_est` | dynamic subset of `ac` | M28 `presolve.gms:9–10` | Establishment-period classes |
| `ac_sub` | dynamic subset of `ac` | M28 `presolve.gms:12–13` | Harvestable/mature classes |
| `im_forest_ageclass(j,ac)` | cell × age class | M28 `declarations.gms:9` | GFAD area distribution (Mha) |
| `p32_carbon_density_ac(t,j,type32,ac,ag_pools)` | time×cell×type×ac×pool | M32 `declarations.gms:19` | Type-specific density lookup |
| `v32_land(j,type32,ac)` | cell × type × age class | M32 | Plantation area by age class (Mha) |
| `vm_carbon_stock(j,land,c_pools,stockType)` | cell×land×pool×type | M56 declarations, written by M32 | Total carbon stock (mio. tC) |
| `pm_carbon_density_plantation_ac(t,j,ac,ag_pools)` | time×cell×ac×pool | M52 `declarations.gms:12` | Calibrated plantation growth curve |
| `pm_carbon_density_secdforest_ac(t,j,ac,ag_pools)` | time×cell×ac×pool | M52 `declarations.gms:9` | Calibrated secdforest growth curve |
| `pm_carbon_density_secdforest_ac_uncalib` | same | M52 `declarations.gms:10` | Uncalibrated (new-establishment use) |
| `pm_carbon_density_plantation_ac_uncalib` | same | M52 `declarations.gms:13` | Uncalibrated (new-establishment use) |
| `vm_emissions_reg(i,emis_source,pollutants)` | region×source×pollutant | M56 declarations, written by M52 | CO2 emissions from stock change |

---

## Closing Source Statement

All claims in this answer are 🟡 **documented** — drawn from:
- `/magpie-agent/modules/module_28.md` (realization `oct24`, sole realization)
- `/magpie-agent/modules/module_32.md` (realization `dynamic_may24`, sole realization)
- `/magpie-agent/modules/module_52.md` (realization `normal_dec17`, sole realization, substantially extended 2026-04-20 by PR #869)

No raw GAMS `.gms` files were opened during this session. Line numbers cited (e.g., `presolve.gms:83`, `equations.gms:108–109`) are as documented in the module markdown files at their last verification dates; they may drift if code has changed since verification.
