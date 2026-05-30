# Module 35 (Natural Vegetation): Secondary-Forest Age Classes, Carbon Stocks, and Downstream Consumers

---

## Default Realization

`pot_forest_may24`
Location: `modules/35_natveg/pot_forest_may24/`

Source: module_35.md header.

---

## 1. Age-Class Structure

### Set definition
Age classes are defined by Module 28 (age_class): `ac0, ac5, ac10, ..., ac150, acx`, where `acx` is the mature open-ended class (> 150 years). The interval is 5 years.

Two land types track age classes in Module 35:
- `v35_secdforest(j,ac)` — secondary forest area by age class (mio. ha)
- `vm_land_other(j,othertype35,ac)` — other land by subtype (`"othernat"`, `"youngsecdf"`) and age class (mio. ha)

Primary forest `vm_land(j,"primforest")` has no age-class dimension; it is treated as always mature ("acx").

### Age progression (presolve.gms:84-97)

Each timestep, age classes shift forward by `s35_shift = m_timestep_length_forestry / 5` steps:

```gams
p35_secdforest(t,j,ac)$(ord(ac) > s35_shift) = pc35_secdforest(j,ac-s35_shift);
p35_secdforest(t,j,"acx") = p35_secdforest(t,j,"acx")
    + sum(ac$(ord(ac) > card(ac)-s35_shift), pc35_secdforest(j,ac));
```

For 5-year timesteps, `s35_shift = 1`: each ac cohort advances one class; the oldest cohorts accumulate in `acx`. The same shift logic applies to `vm_land_other` and to the natural-origin tracker `pc35_secdforest_natural` (see Section 2 below).

### Establishment and regeneration

New secondary forest enters only in the youngest "establishment" age classes (`ac_est`, typically `{ac0, ac5}` for a 10-year timestep). The key equation:

**q35_secdforest_regeneration** (equations.gms:208-214):
```gams
sum(ac_est, v35_secdforest(j2,ac_est))
=e=
sum(ac_sub, v35_hvarea_secdforest(j2,ac_sub))
+ v35_hvarea_primforest(j2)
+ p35_land_restoration(j2,"secdforest");
```
New secdforest = harvested secdforest area + harvested primforest area (one-way: primary becomes secondary, never the reverse) + restoration target.

**q35_secdforest_est** (equations.gms:228-229) distributes new area equally across the establishment classes:
```gams
v35_secdforest(j2,ac_est) =e= sum(ac_est2, v35_secdforest(j2,ac_est2)) / card(ac_est2);
```

### Graduation from youngsecdf to secdforest (the 20 tC/ha threshold)

`vm_land_other(j,"youngsecdf",ac)` holds recovering land whose carbon stock has not yet crossed the forest threshold. When the uncalibrated carbon density (see Section 2) exceeds 20 tC/ha, that area is promoted to secdforest in `presolve.gms:116-122`:
```gams
p35_maturesecdf(t,j,ac)$(not sameas(ac,"acx")) =
    p35_land_other(t,j,"youngsecdf",ac)$(pm_carbon_density_secdforest_ac_uncalib(t,j,ac,"vegc") > 20);
```
The uncalibrated curve (not the FRA-calibrated one) is used deliberately so that natural-succession land matures at realistic rates independent of Module 52's FRA calibration.

---

## 2. Carbon Stock Tracking

### The two carbon-density curves (both provided by Module 52)

| Parameter | Curve | Use |
|---|---|---|
| `pm_carbon_density_secdforest_ac(t,j,ac,ag_pools)` | FRA-calibrated Chapman-Richards (natveg) | Existing/managed secdforest |
| `pm_carbon_density_secdforest_ac_uncalib(t,j,ac,ag_pools)` | Uncalibrated (Braakhekke et al.) | Natural-origin secdforest, youngsecdf, 20 tC/ha test |

### Natural-origin tracking (introduced commit c7731e234, refactored 2fa7b8bea)

Two new parameters track which fraction of each secdforest age-class cohort originated from natural succession on abandoned cropland:
- `p35_secdforest_natural(t,j,ac)` — natural-origin area per time step and age class (mio. ha)
- `pc35_secdforest_natural(j,ac)` — current-timestep value (used inside solve)

Lifecycle:
1. **Initialization** (preloop.gms:49-50): set to zero — all initial secdforest is treated as existing/managed.
2. **Disturbance** (presolve.gms:42-45): natural-origin area reduced proportionally when a cohort is disturbed, preserving the natural-vs-existing ratio.
3. **Age shift** (presolve.gms:99-102): ages in lockstep with the secdforest age shift.
4. **Maturation** (presolve.gms:116-122): freshly matured youngsecdf is recorded as natural-origin (`p35_secdforest_natural`).
5. **Clamp** (presolve.gms:127-128; postsolve.gms:14-16): `pc35_secdforest_natural` never exceeds total `pc35_secdforest`.
6. **Protection** (presolve.gms:175-180): natural-origin area raises the lower bound on `v35_secdforest`, preventing the solver from harvesting it.

### Blended density p35_carbon_density_secdforest (presolve.gms:248-252)

Module 35 computes a per-cohort blended density before the solve:
```gams
p35_carbon_density_secdforest(t,j,ac,ag_pools) = pm_carbon_density_secdforest_ac(t,j,ac,ag_pools);
p35_carbon_density_secdforest(t,j,ac,ag_pools)$(pc35_secdforest(j,ac) > 1e-10) =
  pm_carbon_density_secdforest_ac(t,j,ac,ag_pools)
  - (pm_carbon_density_secdforest_ac(t,j,ac,ag_pools) - pm_carbon_density_secdforest_ac_uncalib(t,j,ac,ag_pools))
    * pc35_secdforest_natural(j,ac) / pc35_secdforest(j,ac);
```
When the natural-origin share = 0 the blend equals the FRA-calibrated curve; when the share = 1 it equals the uncalibrated curve.

### The three carbon stock equations

**q35_carbon_secdforest** (equations.gms:49-51):
```gams
vm_carbon_stock(j2,"secdforest",ag_pools,stockType) =e=
  m_carbon_stock_ac(v35_secdforest,p35_carbon_density_secdforest,"ac","ac_sub");
```
Carbon = sum over age classes of area x blended density. Since commit `c7731e234` the density argument is `p35_carbon_density_secdforest` (the blend), not the bare Module-52 FRA-calibrated curve. This is the primary mechanism by which natural-origin tracking affects carbon accounting.

**q35_carbon_primforest** (equations.gms:42-44):
```gams
vm_carbon_stock(j2,"primforest",ag_pools,stockType) =e=
  m_carbon_stock(vm_land,fm_carbon_density,"primforest");
```
No age-class dimension; uses `fm_carbon_density` directly (LPJmL input, mature forest values only).

**q35_carbon_other** (equations.gms:53-55):
```gams
vm_carbon_stock(j2,"other",ag_pools,stockType) =e=
  m_carbon_stock_ac(vm_land_other,p35_carbon_density_other,"othertype35,ac","othertype35,ac_sub");
```
Sums over both `othertype35` subtypes (othernat, youngsecdf) and age classes, using `p35_carbon_density_other` which is set from `pm_carbon_density_secdforest_ac_uncalib` for youngsecdf (consistent with the maturation logic).

All three equations write into the shared interface variable `vm_carbon_stock(j,land,ag_pools,stockType)`, which is Module 52's primary input from the land side.

---

## 3. vm_land_other

`vm_land_other(j,othertype35,ac)` is a **decision variable** (not a parameter), dimensioned by cluster (j), subtype (othertype35 = {"othernat","youngsecdf"}), and age class (ac). It represents other natural land in mio. ha.

- It aggregates to total "other" land via **q35_land_other** (equations.gms:13): `vm_land(j2,"other") =e= sum((othertype35,ac), vm_land_other(j2,othertype35,ac));`
- It provides the age-class detail used in the carbon stock equation `q35_carbon_other` and in the BII equation `q35_bv_other`.
- It is an output interface variable listed in module_35.md's Interface Variables table, consumed directly by Module 10 (land balance), Module 52 (carbon, via `vm_carbon_stock`), and Module 44 (biodiversity, via `vm_bv`).

---

## 4. Key Equations Summary

| Equation | Location | Function |
|---|---|---|
| `q35_land_secdforest` | equations.gms:11 | Aggregate age classes to `vm_land(j,"secdforest")` |
| `q35_land_other` | equations.gms:13 | Aggregate to `vm_land(j,"other")` |
| `q35_carbon_primforest` | equations.gms:42-44 | `vm_carbon_stock` for primary forest |
| `q35_carbon_secdforest` | equations.gms:49-51 | `vm_carbon_stock` for secdforest using blended density |
| `q35_carbon_other` | equations.gms:53-55 | `vm_carbon_stock` for other land |
| `q35_bv_secdforest` | equations.gms:63-66 | BII by age-class BII tier |
| `q35_bv_primforest` | equations.gms:59-61 | BII for primary forest ("primary" class) |
| `q35_bv_other` | equations.gms:68-71 | BII for other land |
| `q35_secdforest_reduction` | equations.gms:112-114 | Per-age-class area reduction |
| `q35_natforest_reduction` | equations.gms:84-85 | Total natural forest reduction (sum prim + secd) |
| `q35_landdiff` | equations.gms:92-98 | Global gross change penalty fed to Module 10 |
| `q35_secdforest_regeneration` | equations.gms:208-214 | New secdforest = harvest + primforest harvest + restoration |
| `q35_secdforest_est` | equations.gms:228-229 | Even distribution across establishment age classes |
| `q35_max_forest_establishment` | equations.gms:196-201 | Cap forest expansion by potential area minus youngsecdf |
| `q35_cost_hvarea` | equations.gms:132-138 | `vm_cost_hvarea_natveg` = area x differentiated harvest costs |
| `q35_natveg_conservation` | equations.gms:19-22 | Total natural land >= protection target |

---

## 5. Which Modules Consume M35 Land and Carbon-Density Outputs

Module 35 provides to five modules (verified against code, module_35.md:25):

| Downstream module | Interface variable consumed | Description |
|---|---|---|
| **Module 10 (land)** | `vm_land(j,land_natveg)`, `vm_landdiff_natveg`, `vm_landexpansion(j,land_natveg)` | Land balance and oscillation penalty |
| **Module 11 (costs)** | `vm_cost_hvarea_natveg(i)` | Harvest cost contribution to total cost |
| **Module 32 (forestry)** | `pm_max_forest_est(t,j)` | Cap on afforestation potential (remaining after natural veg) |
| **Module 52 (carbon)** | `vm_carbon_stock(j,land_natveg,ag_pools,stockType)` | Natural vegetation carbon stocks for emissions accounting |
| **Module 73 (timber)** | `vm_prod_natveg(j,land_natveg,kforestry)`, `vm_natforest_reduction(j)` | Woody biomass production and natural forest area loss |

Module 44 (biodiversity) receives `vm_bv(j,land_natveg,potnatveg)` for BII aggregation.

Note: Module 35 also provides `pm_carbon_density_secdforest_ac_uncalib` (via Module 52 upstream) to Modules 29 and 32 for their own presolve calculations, but that parameter is produced by Module 52, not by Module 35 itself.

Modules 22, 28, 52, and 56 do NOT directly consume M35 interface variables — they are upstream providers or indirect consumers. (Earlier documentation claiming M22/M28/M52/M56 as direct consumers was corrected in verification round R3 on 2026-05-23.)

---

## Source

- 🟢 **Verified against module_35.md** (last verified 2026-05-16 against `../modules/35_natveg/pot_forest_may24/*.gms`)
- 💬 module_35_notes.md consulted for warnings

**Epistemic hierarchy**:
- All variable names, equation names, and parameter names cited here are taken directly from module_35.md, which was itself verified against the GAMS source (`pot_forest_may24/*.gms`) as of 2026-05-16. Classification is 🟡 (documented this session, not re-verified in raw GAMS source per the question instructions).
- The natural-origin tracking mechanism (Section 2, commits `c7731e234` / `2fa7b8bea`) was the most recent significant change to this module and is explicitly documented and marked as verified in module_35.md Section 5.1.
- Line numbers cited are from the doc and may drift with subsequent commits.
