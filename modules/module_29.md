# Module 29: Cropland - Complete Documentation

**Status**: 🟡 Audited R58 (2026-07-17) — 18 defects found and fixed; see Verification Notes for the
scoped statement of what is and is **not** verified. *(The former "✅ Fully Verified" banner was itself
one of the defects — it was declared, not performed.)*
**Realization**: detail_apr24 (default with fallow land and tree cover dynamics)
**Source Files Verified**: declarations.gms, equations.gms, input.gms, sets.gms, presolve.gms, preloop.gms
**Total Lines**: 123 (equations.gms)
**Total Equations**: 16 (detail_apr24) · 5 (simple_apr24)

---

> ⚙️ **Default Realization**: `detail_apr24`
> Confirmed in `config/default.cfg:811`: `cfg$gms$cropland <- "detail_apr24"`.
>
> ⚠️ **CORRECTED (R58, 2026-07-17)**: this box previously said `simple_apr24` "uses simplified crop
> allocation without rotational constraints". Both halves are false for M29 — `simple_apr24` does no
> crop allocation (that is Module 30's job in **both** realizations), and the token `rotation` appears
> nowhere in `modules/29_cropland/` (positive control: `rg -nic 'cropland'` on the same tree returns
> matches). The sentence was transplanted from **Module 30**, which has identically-named
> `detail_apr24`/`simple_apr24` realizations and whose `simple_apr24` genuinely does crop allocation
> with rotational constraints (`modules/30_croparea/simple_apr24/realization.gms:8-10`,
> `modules/30_croparea/simple_apr24/equations.gms:34` `q30_rotation_max`).
>
> **The real contrast** (`modules/29_cropland/simple_apr24/realization.gms:8-12`): under `simple_apr24`
> total cropland equals croparea because **fallow land and tree cover are fixed to zero**, BII values
> are fixed to zero, and costs are fixed to zero. Mechanically `simple_apr24/preloop.gms:8-12` sets
> `vm_cost_cropland.fx(j)=0`, `vm_fallow.fx(j)=0`, `vm_treecover.fx(j)=0`, and both
> `vm_bv.fx(j,"crop_fallow"/"crop_tree",potnatveg)=0`. Choosing `simple_apr24` silently zeroes those
> five interfaces — that, not rotations, is the trade-off.


## Overview

Module 29 defines **total cropland** as the sum of **croparea** (from Module 30), **fallow land**, and **tree cover on cropland**. The module manages available cropland constraints, carbon stocks, and implements three policy mechanisms: **Semi-Natural Vegetation (SNV)** share requirements, **tree cover** targets, and **fallow land** targets.

**Core Function**: Aggregates cropland components, enforces land availability limits, tracks cropland carbon stocks, and implements landscape diversity policies (SNV, treecover, fallow) via rule-based or penalty-based mechanisms.

**Key Innovation**: Endogenizes fallow land and tree cover on cropland with flexible policy implementation (either hard constraints or incentive penalties), allowing landscape heterogeneity within agricultural areas.

> ⚠️ **CORRECTED (R58, 2026-07-17) — capability vs. default.** The "Key Innovation" above is a
> **capability, not the default behaviour**. Under stock `config/default.cfg`, fallow land and tree
> cover are both **identically zero**, and `detail_apr24` is numerically equivalent to `simple_apr24`:
>
> - **Fallow ≡ 0**: `s29_fallow_max = 0` (`input.gms:33`) ⇒ `q29_fallow_max` (`equations.gms:70-72`,
>   **unguarded**) forces `vm_fallow(j2) =l= 0`; `vm_fallow` is a positive variable
>   (`declarations.gms:44`) with `.lo = 0` (`presolve.gms:120`) ⇒ exactly 0 everywhere.
> - **Tree cover ≡ 0**: `s29_treecover_map = 0` (`input.gms:35`) ⇒ `pc29_treecover(j,ac) = 0`
>   (`preloop.gms:37-38`) ⇒ `v29_treecover.fx(j,ac_sub) = 0` (`presolve.gms:81`). `ac_est` stays free,
>   but `s29_treecover_target = 0` (`input.gms:24`) ⇒ no penalty is avoidable by planting, so planting
>   is strictly dominated: it costs `s29_cost_treecover_est` + `s29_cost_treecover_recur`, consumes
>   scarce cropland via `q29_cropland`, and earns nothing. **No carbon revenue reaches it either** —
>   although `config/default.cfg:1731` sets a non-zero carbon price
>   (`c56_pollutant_prices <- "R34M410-SSP2-NPi2025"`), `config/default.cfg:1828`
>   (`c56_emis_policy <- "reddnatveg_nosoil"`) zeroes `crop_vegc`, `crop_litc`, `crop_soilc` and `som`
>   in `modules/56_ghg_policy/input/f56_emis_policy.csv:114`.
> - **SNV off**: `s29_snv_shr = s29_snv_shr_noselect = 0` (`input.gms:12-13`) ⇒ `p29_snv_shr = 0`.
>
> Net: at defaults `q29_cropland` collapses to `vm_land(j,"crop") = sum((kcr,w), vm_area(j2,kcr,w))`
> and `q29_carbon` collapses to `vm_carbon_stock = vm_carbon_stock_croparea` — exactly
> `simple_apr24/equations.gms:12-13,29-31`. **Out of the box M29 is an accounting identity for
> croparea.** Diffing a default `detail_apr24` run against `simple_apr24` to "measure the effect of
> fallow and tree cover" returns a null result — that is correct behaviour, not a bug. To activate the
> machinery you must set `s29_fallow_max > 0` and/or `s29_treecover_target > 0` (see §8 and §11).
>
> *(Derived algebraically from bounds, equations, and defaults — not from a GDX.)*

**Policy Motivation** (`realization.gms:15-19`): Reserve semi-natural vegetation within cropland areas to provide species habitats and ecosystem services in agricultural landscapes.

**Reference**: `module.gms:8-12`

---

## Realization Differences

### detail_apr24 (Current Default)

**What**: Full implementation with fallow land, tree cover dynamics, and SNV policy
**Components**:
- Croparea (from Module 30)
- Fallow land (optimized with targets/penalties)
- Tree cover on cropland (age-class dynamics, optimized with targets/penalties)
- SNV share constraint

**Equations**: 16
**When**: April 2024

### simple_apr24 (Simplified Version)

**What**: Basic cropland accounting without fallow/treecover policies
**Components**:
- Croparea (from Module 30)
- Carbon stocks
- SNV constraint only

**Equations**: 5 (no fallow or treecover equations)
**Use Case**: Scenarios not focused on landscape diversity policies

---

## Cropland Definition

**Total Cropland** (`module.gms:10-11`):
```
Cropland = Croparea + Fallow Land + Tree Cover
```

**Croparea**: Managed by Module 30 (actual crop-producing area)
**Fallow Land**: Temporarily resting cropland (no crop production)
**Tree Cover**: Trees integrated within cropland (agroforestry)

**Carbon Stocks**: Sum of carbon in all three components

---

## Equations

### 1. Total Cropland (`q29_cropland`)

**⚠️ Realization-dependent:** The form of this equation differs between realizations.

**simple_apr24** (`equations.gms:12-13`):
```gams
q29_cropland(j2)..
  vm_land(j2,"crop") =e= sum((kcr,w), vm_area(j2,kcr,w));
```
**Meaning**: Cropland = harvested area only (no fallow or treecover in this realization)

**detail_apr24** (`equations.gms:11-12`):
```gams
q29_cropland(j2)..
  vm_land(j2,"crop") =e=
    sum((kcr,w), vm_area(j2,kcr,w)) + vm_fallow(j2) + sum(ac, v29_treecover(j2,ac));
```
**Meaning**: Cropland = harvested area + fallow + treecover (all age classes)

**Components**:
- `vm_area(j,kcr,w)` - Harvested area by crop and water type (from Module 30) — both realizations
- `vm_fallow(j)` - Fallow land (optimized in this module) — **detail_apr24 only**
- `v29_treecover(j,ac)` - Tree cover by age class (optimized in this module, **but only over `ac_est`** — see below) — **detail_apr24 only**

> ⚠️ **CORRECTED (R58, 2026-07-17)**: `v29_treecover` is **not** a free decision variable over its full
> `(j,ac)` domain. `presolve.gms:78-82`, under the code's own comment *"Bounds for treecover. Only
> ac_est can increase in optimization. ac_sub is fixed."*:
> ```gams
> v29_treecover.lo(j,ac_est) = 0;
> v29_treecover.up(j,ac_est) = Inf;
> v29_treecover.fx(j,ac_sub) = pc29_treecover(j,ac_sub);
> m_boundfix(v29_treecover,(j,ac_sub),l,1e-6);
> ```
> Only the **establishment** age classes `ac_est` are decision variables. All non-establishment slices
> `ac_sub` are pinned to `pc29_treecover(j,ac_sub)` — the previous timestep's age-shifted state
> (`presolve.gms:57-62`, carried forward at `postsolve.gms:8`). **The optimizer can plant trees but can
> never remove them.** Consequences: (a) the binding structure is "existing stock frozen, only new
> planting free", *not* the `q29_treecover_max` ceiling (`s29_treecover_max = 1`); (b) tree cover never
> declines in output — by construction; (c) the `ac_sub` term in `q29_cost_treecover_recur` is a
> **fixed** cost given the state, not a marginal one, so it cannot influence the planting decision at
> all — a consequential asymmetry with `q29_cost_treecover_est`. This `.fx` — not "no equations for
> tree removal" — is the real mechanism behind Limitation #8 below.

**Interface**: `vm_land(j,"crop")` used by Module 10 (Land) for total land balance

**Source**: `equations.gms:9-13`

---

### 2. Available Cropland Constraint (`q29_avl_cropland`)

**Formula** (`equations.gms:22-23`):
```gams
q29_avl_cropland(j2)..
  vm_land(j2,"crop") =l= sum(ct, p29_avl_cropland(ct,j2));
```

**Meaning**: Total cropland ≤ available cropland. The equation itself is a simple upper bound — it does **not** subtract SNV directly. SNV land requirements are enforced separately by `q29_land_snv` (see Section 4 below).

**Purpose** (`equations.gms:14-20`): Cropland production restricted to suitable areas based on:
- Suitability Index (SI) map from Zabel et al. 2014
- Excludes low-suitability areas (steep slopes, poor soils, etc.)

**Available Cropland Calculation** (`presolve.gms:35`):
The parameter `p29_avl_cropland` used in this equation is pre-computed in the presolve phase, where the SNV share is incorporated:
```gams
p29_avl_cropland(t,j) = f29_avl_cropland(j,"%c29_marginal_land%") * (1 - p29_snv_shr(t,j));
```

**Components**:
- `f29_avl_cropland(j,marginal_land29)` - Base suitability-constrained area
- `p29_snv_shr(t,j)` - SNV share applied during presolve (reduces available cropland before optimization)

**Marginal Land Options** (`input.gms:8`, `sets.gms:10-11`):
- `all_marginal` - Include all marginal land
- `q33_marginal` - Use marginal land definition from Module 33
- `no_marginal` - Exclude marginal land

**Source**: `equations.gms:22-23`, `presolve.gms`

---

### 3. Cropland Costs (`q29_cost_cropland`)

**Formula** (`equations.gms:28-32`):
```gams
q29_cost_cropland(j2)..
  vm_cost_cropland(j2) =e=
    v29_cost_treecover_est(j2) + v29_cost_treecover_recur(j2)
    + v29_fallow_missing(j2) * sum(ct, i29_fallow_penalty(ct))
    + v29_treecover_missing(j2) * sum(ct, i29_treecover_penalty(ct));
```

**Meaning**: Cropland costs = treecover establishment + treecover recurring + fallow penalty + treecover penalty

**Cost Components**:
1. **Treecover Establishment**: Annuitized establishment cost for new trees
2. **Treecover Recurring**: Annual management cost for existing trees
3. **Fallow Penalty**: Cost for violating fallow land target
4. **Treecover Penalty**: Cost for violating treecover target

**Penalty Mechanism**: When targets are not met, optimization pays penalty cost (creates incentive to meet targets)

**Interface**: `vm_cost_cropland(j)` → Module 11 (Costs) objective function

**Source**: `equations.gms:26-32`

---

### 4. Cropland Carbon Stocks (`q29_carbon`)

**Formula** (`equations.gms:38-42`):
```gams
q29_carbon(j2,ag_pools,stockType)..
  vm_carbon_stock(j2,"crop",ag_pools,stockType) =e=
    vm_carbon_stock_croparea(j2,ag_pools)
    + vm_fallow(j2) * sum(ct, fm_carbon_density(ct,j2,"crop",ag_pools))
    + m_carbon_stock_ac(v29_treecover, p29_carbon_density_ac, "ac", "ac_sub");
```

**Meaning**: Cropland carbon = croparea carbon + fallow carbon + treecover carbon

**Three Components**:
1. **Croparea Carbon**: From Module 30 (crops, residues, soil C)
2. **Fallow Carbon**: Fallow area × cropland carbon density
3. **Treecover Carbon**: Age-class-specific carbon (macro m_carbon_stock_ac)

**Age-Class Macro** (`m_carbon_stock_ac`):
- Sums carbon across age classes (ac) and subset (ac_sub)
- Accounts for age-dependent carbon accumulation in trees

> ⚠️ **CORRECTED (R58, 2026-07-17)**: the bullet above is silent on the macro's **control flow**, which
> matters. The two sums are **mutually exclusive branches selected by `stockType`**, not addends
> (`core/macros.gms:104-106`):
> ```gams
> $macro m_carbon_stock_ac(land,carbon_density,sets,sets_sub) \
>    sum((&&sets),     land(j2,&&sets)     * sum(ct, carbon_density(ct,j2,&&sets,ag_pools)))$(sameas(stockType,"actual")) + \
>    sum((&&sets_sub), land(j2,&&sets_sub) * sum(ct, carbon_density(ct,j2,&&sets_sub,ag_pools)))$(sameas(stockType,"actualNoAcEst"))
> ```
> The `+` is a GAMS **branch-selection idiom**, not accumulation: for `stockType = "actual"` the second
> term is 0 and the stock sums over **all** `ac`; for `stockType = "actualNoAcEst"` the first term is 0
> and the stock sums over `ac_sub` only, **excluding** newly established age classes. There is **no
> double-counting** of mature age classes in `q29_carbon`. The `actualNoAcEst` branch is what lets the
> GHG-policy module exclude establishment-year carbon from emission accounting.

**Carbon Pools** (ag_pools): Above-ground pools (vegetation, litter)

**Stock Types** (stockType): 🟢 `actual`, `actualNoAcEst` (`modules/56_ghg_policy/price_aug22/sets.gms:212-213`)

> ⚠️ **CORRECTED (R58, 2026-07-17)**: this line previously read "Actual vs reference stocks". **There is
> no `reference` member.** The set is declared `stockType Carbon stock types / actual, actualNoAcEst /`.
> The real axis is *all age classes* (`actual`) vs *excluding establishment age classes*
> (`actualNoAcEst`) — not actual-vs-reference. Writing a `$(sameas(stockType,"reference"))` guard
> against `vm_carbon_stock` yields a **silently empty expression** (GAMS does not error on `sameas`
> with a non-member string literal) — a zero that looks like data.

**Source**: `equations.gms:35-42`

---

### 5. SNV Land Constraint (`q29_land_snv`)

**Formula** (`modules/29_cropland/detail_apr24/equations.gms:49-52`):
```gams
q29_land_snv(j2)..
  sum(land_snv, vm_land(j2,land_snv)) =g=
    sum(ct, p29_snv_shr(ct,j2)) * vm_land(j2,"crop")
    + sum((ct,land_snv,consv_type), pm_land_conservation(ct,j2,land_snv,consv_type));
```

**Meaning**: SNV land ≥ SNV share × cropland + other conservation land

**Purpose** (`equations.gms:45-47`): Sustain critical regulating ecosystem services in agricultural landscapes, added on top of other conservation (intact ecosystems, biodiversity hotspots)

**Semi-Natural Vegetation** (`input.gms:70`):
```gams
land_snv = { secdforest, other }
```

**SNV Share Calculation** (`presolve.gms:14-16`):
```gams
p29_snv_shr(t,j) = i29_snv_scenario_fader(t) *
  (s29_snv_shr * sum(cell(i,j), p29_country_weight(i))
   + s29_snv_shr_noselect * sum(cell(i,j), 1-p29_country_weight(i)));
```

**Country Weighting**:
- Allows different SNV policies for selected vs non-selected countries
- Weight = fraction of region's cropland in policy-affected countries
- Calculated based on available cropland (`preloop.gms`)

**Source**: `equations.gms:45-49`

---

### 6. SNV Transition Constraint (`q29_land_snv_trans`)

**Formula** (`equations.gms`):
```gams
q29_land_snv_trans(j2)..
  sum(land_snv, vm_lu_transitions(j2,"crop",land_snv)) =g=
    sum(ct, p29_snv_relocation(ct,j2));
```

**Meaning**: Land transitions from cropland to SNV ≥ required relocation

**Purpose** (`equations.gms`): SNV constraint operates at km² scale; required cropland relocation derived from high-resolution Copernicus Global Land Service data (Buchhorn et al. 2020)

**Relocation Calculation** (`presolve.gms:22-32`):
```gams
p29_snv_relocation(t,j) = (i29_snv_scenario_fader(t) - i29_snv_scenario_fader(t-1)) *
  (i29_snv_relocation_target(j) * sum(cell(i,j), p29_country_weight(i))
   + s29_snv_shr_noselect * sum(cell(i,j), 1-p29_country_weight(i)));
```

**Logic**:
- Relocation rate = change in scenario fader × target cropland
- Target cropland from satellite imagery (f29_snv_target_cropland)
- Capped at maximum feasible relocation (`presolve.gms:29-32`)

**Source**: `equations.gms`

---

### 7. Fallow Land Minimum (`q29_fallow_min`)

**Formula** (`equations.gms`):
```gams
q29_fallow_min(j2)$(sum(ct, i29_fallow_penalty(ct)) > 0)..
  v29_fallow_missing(j2) =g=
    vm_land(j2,"crop") * sum(ct, i29_fallow_target(ct)) - vm_fallow(j2);
```

**Meaning**: Missing fallow land = max(0, target fallow - actual fallow)

**Purpose** (`equations.gms`): Penalty for violating fallow land target

**Conditional**: Only active when penalty > 0

**Target Calculation** (`presolve.gms`):
```gams
i29_fallow_target(t) = s29_fallow_target * i29_fallow_scenario_fader(t);
```

**Penalty Logic** (`presolve.gms`):
- Before scenario start: Penalty = 0, missing fixed to 0
- After scenario start: Penalty = s29_fallow_penalty (default 615 USD/ha)
- Missing variable unbounded if penalty > 0

**Source**: `equations.gms`

---

### 8. Fallow Land Maximum (`q29_fallow_max`)

**Formula** (`equations.gms:70-72`):
```gams
q29_fallow_max(j2)..
  vm_fallow(j2) =l= vm_land(j2,"crop") * s29_fallow_max;
```

**Meaning**: Fallow land ≤ maximum share of total cropland

**Purpose**: Prevent excessive fallowing

**Default** (`input.gms:33`): `s29_fallow_max = 0` (no fallow allowed by default)

**Conditional**: none — this equation is **unguarded** and active in every cell, every timestep.

> ⚠️ **CORRECTED (R58, 2026-07-17)**: this section previously ended with *"Note: Fallow only used when
> target > 0 or other policies incentivize it"* — which names the **wrong switch** and contradicts the
> correct default stated two lines above it.
>
> **`s29_fallow_max` is the enabling switch, not `s29_fallow_target`.** With `s29_fallow_max = 0`
> (default), `q29_fallow_max` forces `vm_fallow(j2) =l= 0`; combined with `vm_fallow` being a positive
> variable (`declarations.gms:44`) with `.lo = 0` (`presolve.gms:120`), fallow is **identically zero**
> regardless of any target.
>
> **Setting `s29_fallow_target > 0` alone does NOT enable fallow — it silently adds a spurious cost.**
> It makes `i29_fallow_target(t)` positive (`presolve.gms:104`), activating `q29_fallow_min`
> (`equations.gms:66-68`), which forces
> `v29_fallow_missing(j2) =g= vm_land(j2,"crop") * i29_fallow_target(ct) - 0`. That enters the objective
> at `i29_fallow_penalty = s29_fallow_penalty = 615` USD17MER/ha (`presolve.gms:110`, `input.gms:34`)
> via `q29_cost_cropland` (`equations.gms:31`). The run **solves cleanly** — no infeasibility, no
> warning — and produces **0% fallow plus an unbudgeted penalty** in every cell from 2025 onward,
> distorting every land-allocation margin.
>
> ✅ **To run a fallow scenario you must set `s29_fallow_max > 0`** (and normally
> `s29_fallow_target > 0` alongside it).

---

### 9. Fallow Land Biodiversity Value (`q29_fallow_bv`)

**Formula** (`equations.gms`):
```gams
q29_fallow_bv(j2,potnatveg)..
  vm_bv(j2,"crop_fallow",potnatveg) =e=
    vm_fallow(j2) * fm_bii_coeff("crop_per",potnatveg) * fm_luh2_side_layers(j2,potnatveg);
```

**Meaning**: Fallow biodiversity value = fallow area × perennial crop BII × potential vegetation weight

**Biodiversity Assumption** (`equations.gms`): Fallow land BII based on perennial crops

**Components**:
- `fm_bii_coeff("crop_per",potnatveg)` - BII coefficient for perennial crops
- `fm_luh2_side_layers(j,potnatveg)` - Potential natural vegetation weight

**Interface**: `vm_bv(j,"crop_fallow",potnatveg)` → Module 44 (Biodiversity)

**Source**: `equations.gms`

---

### 10. Tree Cover Aggregation (`q29_treecover`)

**Formula** (`equations.gms`):
```gams
q29_treecover(j2)..
  vm_treecover(j2) =e= sum(ac, v29_treecover(j2,ac));
```

**Meaning**: Total tree cover = sum across all age classes

**Purpose** (`equations.gms`): Interface variable for other modules

**Interface**: `vm_treecover(j)` used by other modules for total tree cover area

---

### 11. Tree Cover Minimum (`q29_treecover_min`)

**Formula** (`equations.gms`):
```gams
q29_treecover_min(j2)$(sum(ct, i29_treecover_penalty(ct)) > 0)..
  v29_treecover_missing(j2) =g=
    vm_land(j2,"crop") * sum(ct, i29_treecover_target(ct,j2)) - sum(ac, v29_treecover(j2,ac));
```

**Meaning**: Missing treecover = max(0, target treecover - actual treecover)

**Purpose** (`equations.gms`): Penalty for violating treecover target

**Conditional**: Only active when penalty > 0

**Target Calculation** (`presolve.gms`):
```gams
i29_treecover_target(t,j) = i29_treecover_scenario_fader(t) *
  (s29_treecover_target * sum(cell(i,j), p29_country_weight(i))
   + s29_treecover_target_noselect * sum(cell(i,j), 1-p29_country_weight(i)));
```

**Keep Existing Treecover** (`presolve.gms`):
- If `s29_treecover_keep = 1`, target cannot fall below current treecover share
- Prevents loss of existing tree cover

**Penalty Values** (`presolve.gms`, `input.gms:28-29`):
- Before scenario start: `s29_treecover_penalty_before = 0` USD/ha
- After scenario start: `s29_treecover_penalty = 6150` USD/ha

**Source**: `equations.gms`

---

### 12. Tree Cover Maximum (`q29_treecover_max`)

**Formula** (`equations.gms`):
```gams
q29_treecover_max(j2)..
  sum(ac, v29_treecover(j2,ac)) =l= vm_land(j2,"crop") * s29_treecover_max;
```

**Meaning**: Total treecover ≤ maximum share of total cropland

**Default** (`input.gms:27`): `s29_treecover_max = 1` (100% of cropland could be treecover)

**Purpose**: Prevent cropland becoming entirely tree-covered (would no longer be cropland)

---

### 13. Tree Cover Biodiversity Value (`q29_treecover_bv`)

**Formula** (`equations.gms`):
```gams
q29_treecover_bv(j2,potnatveg)..
  vm_bv(j2,"crop_tree",potnatveg) =e=
    sum(bii_class_secd, sum(ac_to_bii_class_secd(ac,bii_class_secd), v29_treecover(j2,ac)) *
    p29_treecover_bii_coeff(bii_class_secd,potnatveg)) * fm_luh2_side_layers(j2,potnatveg);
```

**Meaning**: Treecover BV = (area by age-class × age-specific BII) × potential vegetation weight

**BII Coefficient Options** (`presolve.gms`, `input.gms:21`):

**Switch** (`s29_treecover_bii_coeff`) — **only honoured for `m_year(t) > sm_fix_SSP2`**:
- `0` (default): Use secondary vegetation BII coefficients
- `1`: Use timber plantation BII coefficients

> ⚠️ **CORRECTED (R58, 2026-07-17)**: this switch was presented unconditionally; it is wrapped in a
> **year guard** (`presolve.gms:44-52`):
> ```gams
> if(m_year(t) <= sm_fix_SSP2,
>  p29_treecover_bii_coeff(bii_class_secd,potnatveg) = fm_bii_coeff(bii_class_secd,potnatveg)
> else
>  if(s29_treecover_bii_coeff = 0, ... = fm_bii_coeff(bii_class_secd,potnatveg)
>  elseif s29_treecover_bii_coeff = 1, ... = fm_bii_coeff("timber",potnatveg) );
> );
> ```
> For **every timestep with `m_year(t) <= sm_fix_SSP2` the secondary-vegetation coefficients are used
> regardless of the switch**. `sm_fix_SSP2 = 2025` by default (`config/default.cfg:225`) — a threshold
> living in a *different module's* config key — and `scripts/start/extra/input_REMIND.R` sets it to 2020
> for coupled runs, so the switch's effective start year silently moves between standalone and
> REMIND-coupled configs. A user setting `s29_treecover_bii_coeff <- 1` and diffing 2020/2025 BII
> output sees **no difference** and may wrongly conclude the switch is broken.
>
> Note the switch is *doubly* inert at stock defaults, since tree cover is 0 anyway (see the
> capability-vs-default box in the Overview) — `p29_treecover_bii_coeff` multiplies zero area. It is a
> live concern only in configs where tree cover is switched on.

**Age-Class Mapping**: `ac_to_bii_class_secd(ac,bii_class_secd)` maps age classes to BII categories

**Note** (`equations.gms`): BII value depends on whether tree cover treated as natural vegetation or plantations

**Source**: `equations.gms`

---

### 14. Tree Cover Establishment Cost (`q29_cost_treecover_est`)

**Formula** (`equations.gms`):
```gams
q29_cost_treecover_est(j2)..
  v29_cost_treecover_est(j2) =e=
    sum(ac_est, v29_treecover(j2,ac_est)) * s29_cost_treecover_est *
    sum((cell(i2,j2),ct), pm_interest(ct,i2)/(1+pm_interest(ct,i2)));
```

**Meaning**: Establishment cost = new treecover area × unit cost × annuity factor

**Annuity Factor**: `r/(1+r)` where r = interest rate
- Converts one-time establishment cost to annual payment
- Accounts for time value of money

**Unit Cost** (`input.gms:18`): `s29_cost_treecover_est = 2460` USD17MER/ha

**Age Classes** (`ac_est`): Only establishment age classes (ac0, ac5 for 10-year timestep)

**Source**: `equations.gms`

---

### 15. Tree Cover Recurring Cost (`q29_cost_treecover_recur`)

**Formula** (`equations.gms`):
```gams
q29_cost_treecover_recur(j2)..
  v29_cost_treecover_recur(j2) =e=
    sum(ac_sub, v29_treecover(j2,ac_sub)) * s29_cost_treecover_recur;
```

**Meaning**: Recurring cost = existing treecover area × annual maintenance cost

**Unit Cost** (`input.gms:19`): `s29_cost_treecover_recur = 615` USD17MER/ha/yr

**Age Classes** (`ac_sub`): Subset excluding establishment age classes (existing trees only)

**Purpose**: Annual management cost (pruning, pest control, etc.)

**Source**: `equations.gms`

---

### 16. Tree Cover Establishment Distribution (`q29_treecover_est`)

**Formula** (`equations.gms`):
```gams
q29_treecover_est(j2,ac_est)..
  v29_treecover(j2,ac_est) =e= sum(ac_est2, v29_treecover(j2,ac_est2))/card(ac_est2);
```

**Meaning**: Each establishment age class receives equal share of new treecover

**Purpose** (`equations.gms`): Distribute new tree establishment equally across age classes

**Example**:
- 5-year timestep: ac_est = {ac0} → all new trees in ac0
- 10-year timestep: ac_est = {ac0, ac5} → new trees split 50/50 between ac0 and ac5

**Rationale**: Simulates continuous planting throughout the timestep

**Source**: `equations.gms`

---

## Key Algorithms

### Algorithm 1: Scenario Fading

**Purpose**: Smooth interpolation from policy start to target year

**Functional Forms** (`preloop.gms:10-18`, `input.gms:36`):

1. **Linear** (`s29_fader_functional_form = 1`):
   - Macro: `m_linear_time_interpol`
   - Straight-line interpolation: fader = (year - start)/(target - start)

2. **Sigmoidal** (`s29_fader_functional_form = 2`, default):
   - Macro: `m_sigmoid_time_interpol`
   - S-curve: slow start, rapid middle, slow end
   - Smoother transition, avoids discontinuities

**Applied To**:
- `i29_snv_scenario_fader` (SNV share)
- `i29_treecover_scenario_fader` (treecover target)
- `i29_fallow_scenario_fader` (fallow target)

**Time Windows**:
- SNV: 2025-2050 (default)
- Treecover: 2025-2050 (default)
- Fallow: 2025-2050 (default)

**Source**: `preloop.gms:8-18`, `input.gms:14-31,36`

---

### Algorithm 2: Age-Class Shifting for Tree Cover

**Implementation** (`presolve.gms`):
```gams
s29_shift = m_timestep_length_forestry/5;  ! Number of 5-yr age-classes to shift

! Shift age classes forward
p29_treecover(t,j,ac)$(ord(ac) > s29_shift) = pc29_treecover(j, ac-s29_shift);

! Handle overflow (trees aging beyond acx)
p29_treecover(t,j,"acx") = p29_treecover(t,j,"acx")
  + sum(ac$(ord(ac) > card(ac)-s29_shift), pc29_treecover(j,ac));
```

**Logic**:
- **5-year timestep** (s29_shift = 1): ac0 → ac5, ac5 → ac10, ..., acx → acx
- **10-year timestep** (s29_shift = 2): ac0 → ac10, ac5 → ac15, ..., acx → acx
- **Overflow**: Trees in final age classes accumulate in acx (mature forests)

**Example**:
- Time t-1: 10 ha in ac5
- Time t (5-yr step): 10 ha now in ac10
- Trees continue aging until reaching acx (maximum age)

**Source**: `presolve.gms`

---

### Algorithm 3: SNV Relocation Target Interpolation

**Purpose**: Estimate cropland requiring relocation based on SNV share target

**Implementation** (`preloop.gms:22-28`):
```gams
if (s29_snv_shr = 0),
  i29_snv_relocation_target(j) = 0;
elseif (s29_snv_shr <= 0.2),
  ! Linear interpolation: 0% to 20%
  m_linear_cell_data_interpol(i29_snv_relocation_target, s29_snv_shr,
    0, 0.2, 0, f29_snv_target_cropland(j,"SNV20TargetCropland"));
elseif (s29_snv_shr > 0.2),
  ! Linear interpolation: 20% to 50%
  m_linear_cell_data_interpol(i29_snv_relocation_target, s29_snv_shr,
    0.2, 0.5, f29_snv_target_cropland(j,"SNV20TargetCropland"),
    f29_snv_target_cropland(j,"SNV50TargetCropland"));
```

**Data Points** (`input.gms:16-17`):
- `s29_snv_relocation_data_x1 = 0.2` (20% SNV)
- `s29_snv_relocation_data_x2 = 0.5` (50% SNV)

**Input Data**: Copernicus satellite imagery for 20% and 50% SNV scenarios

**Source**: `preloop.gms:20-28`, `input.gms`

---

### Algorithm 4: Country Policy Weighting

**Purpose**: Apply policies only to selected countries, aggregate to regional level

**Implementation** (`preloop.gms`):
```gams
! Set country switch (1 = affected by policy, 0 = not affected)
p29_country_switch(iso) = 0;
p29_country_switch(policy_countries29) = 1;

! Calculate available cropland by country
pm_avl_cropland_iso(iso) = f29_avl_cropland_iso(iso,"%c29_marginal_land%");

! Regional weight = affected cropland / total cropland
p29_country_weight(i) =
  sum(i_to_iso(i,iso), p29_country_switch(iso) * pm_avl_cropland_iso(iso)) /
  sum(i_to_iso(i,iso), pm_avl_cropland_iso(iso));
```

**Logic**:
- Region with 100% of cropland in policy countries: weight = 1.0
- Region with 50% of cropland in policy countries: weight = 0.5
- Region with 0% of cropland in policy countries: weight = 0.0

**Application**:
- SNV share: `s29_snv_shr * weight + s29_snv_shr_noselect * (1-weight)`
- Treecover target: `s29_treecover_target * weight + s29_treecover_target_noselect * (1-weight)`

**Default** (`input.gms:43-68`): All countries in `policy_countries29` (full global coverage)

**Source**: `preloop.gms`

---

### Algorithm 5: Tree Cover Initialization

**Purpose**: Initialize tree cover from maps or start from zero

**Implementation** (`preloop.gms:32-36`):

**Option 1** (`s29_treecover_map = 1`):
```gams
! Calculate share from 2015 map data
pc29_treecover_share(j) = f29_treecover(j) / pm_land_hist("y2015",j,"crop");
pc29_treecover_share(j)$(pc29_treecover_share(j) > s29_treecover_max) = s29_treecover_max;

! Distribute equally across age classes
pc29_treecover(j,ac) = (pc29_treecover_share(j) * pm_land_hist("y1995",j,"crop")) / card(ac);
```

**Option 2** (`s29_treecover_map = 0`, default):
```gams
pc29_treecover(j,ac) = 0;  ! Start with no tree cover
```

**Data Source** (`input.gms`): `f29_treecover(j)` from CroplandTreecover.cs2

**Source**: `preloop.gms:31-36`, `input.gms:35`

---

### Algorithm 6: Tree Cover Growth Curve Selection

**Purpose**: Choose carbon accumulation trajectory for tree cover

**Implementation** (`preloop.gms`):

**Option 0** (`s29_treecover_plantation = 0`, default):
```gams
p29_carbon_density_ac(t,j,ac,ag_pools) = pm_carbon_density_secdforest_ac_uncalib(t,j,ac,ag_pools);
```
- Uses uncalibrated natural vegetation regrowth curve (from Module 52)
- Slower carbon accumulation
- Converges to natural forest carbon density

**Option 1** (`s29_treecover_plantation = 1`):
```gams
p29_carbon_density_ac(t,j,ac,ag_pools) = pm_carbon_density_plantation_ac_uncalib(t,j,ac,ag_pools);
```
- Uses uncalibrated plantation growth curve (from Module 52)
- Faster carbon accumulation (managed trees)
- Converges to the **same** LPJmL natural-vegetation asymptote as Option 0

> ⚠️ **CORRECTED (R58, 2026-07-17): the previous "trade-off" was INVERTED, not merely unsupported.**
> This section claimed plantations converge to a *"plantation carbon density (typically lower than
> natural)"* and framed a **"Trade-off: Plantation grows faster initially but has lower final carbon
> density"**. That is a real-world ecological trade-off the model **does not implement**, and it is
> contradicted by the authoring comment three lines above the code this section quotes
> (`preloop.gms:42-44`):
> ```
> *' Switch for tree cover on cropland:
> *' 0 = Use natveg growth curve towards LPJmL natural vegetation
> *' 1 = Use plantation growth curve (faster than natveg) towards LPJmL natural vegetation
> ```
> Verified against the arrays themselves, not just the comment:
> 1. **Same asymptote symbol.** Both curves pass `fm_carbon_density(t_all,j,"secdforest","vegc")` as the
>    `A` argument of `m_growth_vegc` (`modules/52_carbon/normal_dec17/start.gms:17` plantation, `:27`
>    secdforest). The macro is `S + (A-S)*(1-exp(-k*(ac*5)))**m` (`core/macros.gms:18`), so for any
>    finite `k,m > 0` both converge to **exactly `A`**. **There is no "plantation carbon density"
>    asymptote in the model — the phrase names a quantity that does not exist.**
> 2. **`litc` is bit-identical.** The two `litc` assignments (`modules/52_carbon/normal_dec17/start.gms:20`
>    plantation vs `:30` secdforest) are the same
>    expression character-for-character (no `k`/`m`), so plantation `litc` ≡ secdforest `litc` at every
>    age class.
> 3. **The `vegc` inequality runs the *opposite* way.** `modules/52_carbon/input/f52_growth_par.csv`
>    gives plantations strictly **higher `k`** in every climate class where the two differ (Cfa: 0.042
>    vs 0.0219; Af: 0.0301 vs 0.0228), and mostly lower `m` — both raise the curve.
>
> **Therefore `pm_carbon_density_plantation_ac_uncalib` ≥ `pm_carbon_density_secdforest_ac_uncalib` at
> every age class, for both `ag_pools`, converging to equality — never lower.** The real choice is a
> **rate toward a shared endpoint**, with no long-run stock penalty. Under a carbon price (M56) the old
> framing inverted the sign of the expected long-run result and would send a reader hunting a
> nonexistent bug when plantation and natveg runs converge late-century.
>
> M29 does not compute either asymptote — it copies both arrays wholesale from M52
> (`modules/52_carbon/normal_dec17/start.gms:43-44`, snapshotted *before* calibration).

**Source**: `modules/29_cropland/detail_apr24/preloop.gms:45-49`, `input.gms:20`

---

## Input Data Files

| File | Parameter | Description | Dimensions | Units |
|------|-----------|-------------|------------|-------|
| `avl_cropland.cs3` | `f29_avl_cropland` | Available cropland by suitability | (j, marginal_land29) | Mio. ha |
| `avl_cropland_iso.cs3` | `f29_avl_cropland_iso` | Available cropland at country level | (iso, marginal_land29) | Mio. ha |
| `SNVTargetCropland.cs3` | `f29_snv_target_cropland` | Cropland requiring relocation for SNV | (j, relocation_target29) | Mio. ha |
| `CroplandTreecover.cs2` | `f29_treecover` | Initial tree cover from maps (2015) | (j) | Mio. ha |

**Source**: `input.gms`

---

## Interface Variables

### Provided by Module 29

| Variable | Description | Dimensions | Units | Used By |
|----------|-------------|------------|-------|---------|
| `vm_cost_cropland` | Cropland module costs | (j) | Mio. USD17MER/yr | Module 11 (Costs) |
| `vm_fallow` | Fallow land area | (j) | Mio. ha | Modules 32 (Forestry), 50 (NR Soil Budget), 59 (SOM) |
| `vm_treecover` | Tree cover area | (j) | Mio. ha | Modules 22 (Conservation), 59 (SOM) |
| `vm_bv` | Biodiversity value — M29 **populates only** the `crop_fallow` / `crop_tree` slices | (j,landcover44,potnatveg) | Mio. ha | Module 44 (Biodiversity) |

**Source**: `declarations.gms:38-45` covers the M29-declared positive variables only. `vm_bv` is
**declared in Module 44** (`modules/44_biodiversity/bv_btc_mar21/declarations.gms:19` →
`vm_bv(j,landcover44,potnatveg)`) and is merely **populated** here by `q29_fallow_bv` /
`q29_treecover_bv` (`detail_apr24/equations.gms:76-78,101-104`).

> ⚠️ **CORRECTED (R58, 2026-07-17)**: the `vm_bv` row previously sat under a blanket
> `declarations.gms:38-45` citation that cannot support it — M29 declares no `vm_bv` at all (verified:
> `rg -n 'vm_bv' detail_apr24/declarations.gms` → zero matches; positive control `vm_fallow` → `:44`).
> The dimension label was also wrong: the set is `landcover44`, not `landcover`. The row's *substance*
> (M29 supplies these two slices to M44) was and is correct — this is a DECLARED-vs-POPULATED
> distinction, and per-slice ownership is the right mental model.

### Used by Module 29

| Variable | Description | Dimensions | Units | Provided By |
|----------|-------------|------------|-------|-------------|
| `vm_land` | Total land by type | (j,land) | Mio. ha | Module 10 (Land) |
| `vm_area` | Harvested crop area | (j,kcr,w) | Mio. ha | Module 30 (Croparea) |
| `vm_carbon_stock_croparea` | Croparea carbon stocks | (j,ag_pools) | Mio. tC | Module 30 (Croparea) |
| `vm_lu_transitions` | Land use transitions | (j,land_from,land_to) | Mio. ha | Module 10 (Land); also read by Module 35 (Natveg) (`modules/35_natveg/pot_forest_may24/presolve.gms:58`), Module 59 (SOM) (`modules/59_som/cellpool_jan23/equations.gms:51`) |
| `pm_interest` | Regional interest rate | (t,i) | Dimensionless | Module 12 (Interest Rate) |
| `pm_land_conservation` | Conservation land | (t,j,land,consv_type) | Mio. ha | Module 22 (Conservation) |
| `fm_carbon_density` | Carbon density by land type | (t,j,land,ag_pools) | tC/ha | Core data |
| `fm_bii_coeff` | BII coefficients | (bii_class,potnatveg) | Dimensionless | Core data |
| `fm_luh2_side_layers` | Potential vegetation layers | (j,potnatveg) | Dimensionless | Core data |

**Source**: Cross-verified with source modules

---

## Internal Variables

| Variable | Description | Dimensions | Units |
|----------|-------------|------------|-------|
| `v29_treecover` | Tree cover by age class | (j,ac) | Mio. ha |
| `v29_treecover_missing` | Missing treecover towards target | (j) | Mio. ha |
| `v29_cost_treecover_est` | Treecover establishment cost | (j) | Mio. USD17MER/yr |
| `v29_cost_treecover_recur` | Treecover recurring cost | (j) | Mio. USD17MER/yr |
| `v29_fallow_missing` | Missing fallow towards target | (j) | Mio. ha |

**Source**: `declarations.gms:37-46`

---

## Configuration Options

### Core Switches

| Setting | Description | Values | Default |
|---------|-------------|--------|---------|
| `c29_marginal_land` | Marginal land inclusion | all_marginal, q33_marginal, no_marginal | q33_marginal |
| `s29_fader_functional_form` | Fader interpolation type | 1=linear, 2=sigmoidal | 2 |

**Source**: `input.gms:8,36`

### SNV Policy

| Setting | Description | Value | Default |
|---------|-------------|-------|---------|
| `s29_snv_shr` | SNV share (selected countries) | 0-1 | 0 |
| `s29_snv_shr_noselect` | SNV share (non-selected) | 0-1 | 0 |
| `s29_snv_scenario_start` | Policy start year | Year | 2025 |
| `s29_snv_scenario_target` | Policy target year | Year | 2050 |

**Source**: `input.gms:12-15`

### Tree Cover Policy

| Setting | Description | Value | Default |
|---------|-------------|-------|---------|
| `s29_treecover_target` | Target share (selected) | 0-1 | 0 |
| `s29_treecover_target_noselect` | Target share (non-selected) | 0-1 | 0 |
| `s29_treecover_max` | Maximum share | 0-1 | 1 |
| `s29_treecover_keep` | Prevent treecover loss | 0/1 | 0 |
| `s29_treecover_scenario_start` | Policy start year | Year | 2025 |
| `s29_treecover_scenario_target` | Policy target year | Year | 2050 |
| `s29_treecover_penalty_before` | Penalty before start | USD/ha | 0 |
| `s29_treecover_penalty` | Penalty after start | USD/ha | 6150 |
| `s29_cost_treecover_est` | Establishment cost | USD/ha | 2460 |
| `s29_cost_treecover_recur` | Recurring cost | USD/ha/yr | 615 |
| `s29_treecover_plantation` | Growth curve | 0=natveg, 1=plantation | 0 |
| `s29_treecover_bii_coeff` | BII coefficients | 0=secd, 1=timber | 0 |
| `s29_treecover_map` | Initialize from map | 0/1 | 0 |

**Source**: `input.gms:18-35`

### Fallow Land Policy

| Setting | Description | Value | Default |
|---------|-------------|-------|---------|
| `s29_fallow_target` | Target share | 0-1 | 0 |
| `s29_fallow_max` | Maximum share | 0-1 | 0 |
| `s29_fallow_scenario_start` | Policy start year | Year | 2025 |
| `s29_fallow_scenario_target` | Policy target year | Year | 2050 |
| `s29_fallow_penalty` | Penalty for violation | USD/ha | 615 |

**Source**: `input.gms:30-34`

---

## Scaling

**No scaling applied in this module.**

A scaling.gms file exists (`detail_apr24/scaling.gms`) but all scale statements are commented out, so no scaling is applied by default.

---

## Key Dependencies

### Upstream Dependencies (Variables Used)

1. **Module 10 (Land)**:
   - `vm_land(j,land)` - Total land by type
   - `vm_lu_transitions(j,land_from,land_to)` - Land transitions

2. **Module 30 (Croparea)**:
   - `vm_area(j,kcr,w)` - Harvested crop area
   - `vm_carbon_stock_croparea(j,ag_pools)` - Croparea carbon

3. **Module 12 (Interest Rate)**:
   - `pm_interest(t,i)` - Regional interest rate for annuity calculation

4. **Module 22 (Conservation)**:
   - `pm_land_conservation(t,j,land,consv_type)` - Conservation land areas

### Downstream Dependencies (Variables Provided)

1. **Module 10 (Land)**:
   - `vm_land(j,"crop")` - Total cropland (in land balance)

2. **Module 11 (Costs)**:
   - `vm_cost_cropland(j)` - Cropland costs (in objective function)

3. **Module 44 (Biodiversity)** — via `vm_bv` **only**:
   - `vm_bv(j,"crop_fallow",potnatveg)` - Fallow biodiversity value
   - `vm_bv(j,"crop_tree",potnatveg)` - Treecover biodiversity value

> ⚠️ **CORRECTED (R58, 2026-07-17)**: this list previously also named the area variables `vm_fallow(j)`
> and `vm_treecover(j)` here — but Module 44 reads **neither** of them, so both were phantom
> attributions. The old wording contradicted **this doc's own interface table above** (which is the
> correct one) and the code. Verified by grep in both paren- and dot-form:
> - `vm_fallow` outside M29 → `32_forestry/dynamic_may24/presolve.gms:18`;
>   `50_nr_soil_budget/macceff_aug22/equations.gms:26`; `59_som/static_jan19/equations.gms:13`;
>   `59_som/cellpool_jan23/equations.gms:25` ⇒ **{32, 50, 59}** — no M44.
> - `vm_treecover` outside M29 → `22_land_conservation/area_based_apr22/presolve_ini.gms:87,98,109`;
>   `59_som/static_jan19/equations.gms:14`; `59_som/cellpool_jan23/equations.gms:26` ⇒ **{22, 59}** —
>   no M44.
> - `rg -n 'vm_fallow|vm_treecover' modules/44_biodiversity/` → **zero matches** (positive control:
>   `vm_bv` returns matches in the same tree).
>
> **The M29↔M44 coupling is exclusively through the pre-multiplied `vm_bv` slices.** This matters:
> M29 owns the BII coefficient choice (`s29_treecover_bii_coeff`, §13) and M44 only aggregates — so
> changing how fallow or tree cover is *valued* for biodiversity means editing **M29**, not M44. A
> reader following the old list would look for area terms in `44_biodiversity/*/equations.gms` that do
> not exist.

---

## Participates In

### Conservation Laws

Module 29 participates in **FOUR of the five conservation laws** - one of the most interconnected modules:

#### 1. Land Area Balance: ✅ **CRITICAL PARTICIPANT**

Module 29 provides **total cropland area** to the land balance equation in Module 10:

- **Cropland Components** (realization-dependent):
  - **simple_apr24**: `vm_land(j,"crop") = sum((kcr,w), vm_area(j,kcr,w))` — harvested area only
  - **detail_apr24**: `vm_land(j,"crop") = sum((kcr,w), vm_area(j,kcr,w)) + vm_fallow(j) + sum(ac, v29_treecover(j,ac))` — harvested area + fallow + tree cover

- **Constraint**: Total cropland cannot exceed available cropland
  - Equation: `q29_avl_cropland` limits `vm_land(j,"crop")`
  - Ensures cropland expansion doesn't violate land availability

- **Cross-Module Reference**: `cross_module/land_balance_conservation.md` (Section 5.2, "Module 29 Aggregates Cropland Components")

#### 2. Carbon Balance: ✅ **PARTICIPANT**

Module 29 tracks **cropland carbon stocks** across two above-ground pools:

- **Two Above-Ground Carbon Pools** (ag_pools = {vegc, litc}):
  1. **Vegetation carbon** (vegc): Crops (annual, negligible stocks)
  2. **Litter carbon** (litc): Crop residues (small pool)

- **Note on pool coverage**: `q29_carbon` operates only over `ag_pools` (above-ground: vegc, litc). It does NOT set soil carbon (soilc) for cropland - the SOM module (59) populates the soilc slice separately. The full `c_pools` set is {vegc, litc, soilc}; there is no separate below-ground pool.

- **Tree Cover Carbon**:
  - Module 52 provides age-class carbon density: `pm_carbon_density_secdforest_ac_uncalib` (natural vegetation) and `pm_carbon_density_plantation_ac_uncalib` (plantation); Module 29 reads these into `p29_carbon_density_ac` in preloop
  - `v29_treecover(j,ac)` contributes to above-ground cropland carbon
  - Tree cover acts as carbon sink on cropland

- **Cross-Module Reference**: `cross_module/carbon_balance_conservation.md` (Section 3.1, "Cropland Carbon")

#### 3. Food Supply Balance: ✅ **PARTICIPANT**

Module 29 contributes to agricultural land that supports food production:

- **Indirect Participation**: Cropland area (vm_land("crop")) affects total production capacity
- **Mechanism**: Module 30 uses cropland area for crop allocation → Module 17 aggregates production
- **Equation**: `vm_land(j,"crop")` provides land base for Module 30 crop allocation

- **Cross-Module Reference**: `cross_module/nitrogen_food_balance.md` (Part 2, Food Supply)

#### 4. Nitrogen Tracking: ✅ **PARTICIPANT**

Module 29 provides land use data that Module 50/51 use for nitrogen accounting:

- **Cropland Nitrogen Demand**: Module 50 uses `vm_land(j,"crop")` for N fertilizer requirements; `vm_land` is also read by Module 22 (Land Conservation) (`modules/22_land_conservation/area_based_apr22/presolve_ini.gms:86`), Module 30 (Croparea) (`modules/30_croparea/simple_apr24/equations.gms:23`), Module 31 (Pasture) (`modules/31_past/static/presolve.gms:11`), Module 32 (Forestry) (`modules/32_forestry/dynamic_may24/presolve.gms:19`), Module 34 (Urban) (`modules/34_urban/static/presolve.gms:9`), Module 35 (Natveg) (`modules/35_natveg/pot_forest_may24/presolve.gms:40`), Module 58 (Peatland) (`modules/58_peatland/v2/equations.gms:23`), Module 59 (SOM) (`modules/59_som/cellpool_jan23/equations.gms:33`)
- **Soil Nitrogen Dynamics**: Cropland expansion/contraction affects soil N pools
- **Tree Cover Impact**: Trees on cropland affect N cycling (via soil carbon Module 59)

- **Cross-Module Reference**: `cross_module/nitrogen_food_balance.md` (Part 1, Section 1.2)

#### 5. Water Balance: ⚠️ **INDIRECT**

Module 29 does NOT directly participate in water balance (no water equations), but:
- Irrigated vs rainfed split in Module 30 affects water demand
- Cropland expansion can increase irrigation requirements (Module 41/42)

---

### Dependency Chains

**Centrality Rank**: 9 of 46 modules
**Total Connections**: 13 (provides to 6, depends on 7) — *per the cited source; see caveat below*
**Hub Type**: **Aggregation Hub** (aggregates cropland components: area + fallow + tree cover)

> ⚠️ **CORRECTED (R58, 2026-07-17)**: this line previously read "**12** (provides to 6 modules, depends
> on **6**)", attributed to `core_docs/Module_Dependencies.md`. **The cited source does not say that.**
> `core_docs/Module_Dependencies.md:39` says `| 9 | 29_cropland | 13 | 6 | 7 |` under the header
> `| Rank | Module | Total | Provides To | Depends On |` — i.e. **13 / 6 / 7**. Only "Rank 9" matched.
>
> ⚠️ **Both numbers understate the code.** Per the per-variable derivation below, M29's outward degree
> alone is **14 modules** (10, 11, 13, 22, 30, 31, 32, 34, 35, 44, 50, 52, 56, 59). Treat the 13/6/7
> figure as *what the cited doc records*, not as a verified count — `Module_Dependencies.md` is under
> human-adjudication hold this round and was not updated. Use the per-variable table below for blast
> radius.

> ⚠️ **CORRECTED (R58, 2026-07-17).** The previous list named 6 modules, omitted
> `pm_avl_cropland_iso`, `vm_carbon_stock` and `vm_bv` entirely, and hid four real consumers behind
> "plus potentially 1-2 other modules". Rewritten below from a per-variable derivation.

**Counting rule** (stated because the old list had none): M29 *provides* an interface variable if M29
**populates** it — i.e. the variable is the LHS of an M29 equation, or is a parameter M29 declares and
fills. Populating is NOT the same as declaring: three of the six variables below are declared in
*other* modules and populated here. A consumer is any other module referencing the variable in `.gms`
source, in either the `name(` (equation) or `name.` (solution-level) form.

**Provides To** — 6 interface variables, populated by the default realization `detail_apr24`:

| Variable | Declared in | Populated by M29 at | Consumed by |
|---|---|---|---|
| `vm_land(j,"crop")` — the **crop slice only** | M10 (`10_land/landmatrix_dec18/declarations.gms:19`) | `q29_cropland`, `detail_apr24/equations.gms:12` | M10's land balance (M29 owns only the `"crop"` slice; other modules own the other slices) |
| `vm_cost_cropland(j)` | M29 (`detail_apr24/declarations.gms:38`) | `equations.gms` | **11** |
| `vm_fallow(j)` | M29 | `equations.gms` | **32, 50, 59** |
| `vm_treecover(j)` | M29 | `equations.gms` | **22, 59** |
| `vm_carbon_stock(j,"crop",ag_pools,stockType)` | **M56** (`56_ghg_policy/price_aug22/declarations.gms:34`) | `detail_apr24/equations.gms:39` | **31, 32, 34, 35, 52, 56, 59** |
| `vm_bv(j,...)` | **M44** (`44_biodiversity/bv_btc_mar21/declarations.gms:19`) | `detail_apr24/equations.gms` | **30, 31, 32, 34, 35, 44** |
| `pm_avl_cropland_iso` | M29 | preloop/presolve | **13, 30, 59** |

**Modules that consume at least one variable M29 populates:** 10, 11, 13, 22, 30, 31, 32, 34, 35, 44,
50, 52, 56, 59. Note `simple_apr24` (non-default) populates only `vm_land` and `vm_carbon_stock`.

**Depends On** (6 modules):
1. **Module 10 (Land)** - Total land by type (`vm_land`), land use transitions (`vm_lu_transitions`)
2. **Module 30 (Croparea)** - Harvested crop area (`vm_area`), croparea carbon stocks (`vm_carbon_stock_croparea`)
3. **Module 12 (Interest Rate)** - Regional interest rate (`pm_interest`)
4. **Module 22 (Conservation)** - Conservation land targets (`pm_land_conservation`)
5. **Module 52 (Carbon)** - Age-class carbon density (`pm_carbon_density_secdforest_ac_uncalib`, `pm_carbon_density_plantation_ac_uncalib`)
6. Core data - Historical land use (`pm_land_hist`), carbon density (`fm_carbon_density`), BII coefficients (`fm_bii_coeff`), potential vegetation layers (`fm_luh2_side_layers`)

**Key Position**: Module 29 acts as **cropland aggregator** - it sums harvested area (Module 30), fallow land, and tree cover into total cropland area for the land balance.

**Reference**: `core_docs/Module_Dependencies.md` (**Section 1.2**, Module Centrality Rankings —
`core_docs/Module_Dependencies.md:25`; the previous pointer to §3.1 was wrong — §3.1 is "Architectural
Layers" at `:89`)

---

### Circular Dependencies

**Participates In**: 2 circular dependency cycles

#### Cycle C9: Cropland ↔ Crop Area ↔ Land (Simultaneous Resolution)

**Structure**:
```
Module 29 (Cropland) ──→ vm_land(j,"crop") ──→ Module 10 (Land)
       ↑                                              │
       │                                              │
       └─────────── Land availability ←───────────────┘
                           ↓
                  Module 30 (Croparea)
                    vm_area(j,kcr,w)
```

**Resolution Mechanism**: **Type 2 - Simultaneous Equations**
- All cropland variables optimized together in same SOLVE statement
- Module 29 aggregates: `vm_land("crop") = sum(kcr, vm_area(j,kcr,w)) + vm_fallow + vm_treecover`
- Module 30 allocates crops within available cropland
- Module 10 ensures total land balance via `q10_land_area`
  (`modules/10_land/landmatrix_dec18/equations.gms:13-15`):
  `sum(land, vm_land(j2,land)) =e= sum(land, pcm_land(j2,land))`

> ⚠️ **CORRECTED (R58, 2026-07-17)**: this doc previously stated M10's invariant as
> `sum(land, vm_land(j,land)) = pm_land_start(j)` — in **three** places, twice inside "✅ Verify"
> checklist items. Two errors: (a) the balance closes against **`pcm_land`** (the *previous timestep's*
> land state), not `pm_land_start` (the 1995 initialization,
> `modules/10_land/landmatrix_dec18/start.gms:8`); (b) `pm_land_start(j)` is **not a valid reference** —
> the parameter is `pm_land_start(j,land)` (`modules/10_land/landmatrix_dec18/declarations.gms:9`), so
> the expression as written is a **domain error**. The equation name `q10_land_area` was never given.
>
> *Nuance:* because `q10_land_area` conserves the per-cell total every step and `pcm_land` is seeded
> from `pm_land_start`, the *scalar total* does numerically match at every timestep — so the old check
> was not numerically wrong, it was **wrongly attributed and malformed**, and it tested a weaker
> invariant (constant total) than the one M10 actually enforces (closure against the immediately
> preceding state). Since M29 *defines* `vm_land(j,"crop")`, it is the module most likely to break that
> balance — pointing its modifiers at the wrong invariant has a real cost.

#### Cycle C29: Cropland ↔ SOM (Temporal Feedback)

<!-- check-gams-vars: allow pm_carbon_density_soilc -->
> ⚠️ **CORRECTED (R58, 2026-07-17): this is NOT a cycle.** The section previously showed a
> return edge `pm_carbon_density_soilc` from M59 back to M29. **No such variable exists anywhere
> in MAgPIE** (verified with positive controls: no interface variable containing `soilc` exists in
> `modules/` at all), and M29 reads *nothing* that M59 declares — M59's entire declared interface is
> `vm_cost_scm`, `vm_nr_som`, `vm_nr_som_fertilizer`. The relationship is a **one-way edge**, and
> the heading is retained only so the old "Cycle C29" label remains findable.

**Structure** (one-way, not a cycle):
```
Module 29 (Cropland) ──→ vm_treecover(j) ──→ Module 59 (SOM)
                          (no return edge)
```

- Forward edge is real: M59 consumes `vm_treecover` in its SOM equations
  (`modules/59_som/static_jan19/equations.gms:14`; `modules/59_som/cellpool_jan23/equations.gms:26`).
- **There is no return edge.** M29 does not read any M59 output, so there is no feedback to resolve.

**Resolution Mechanism**: **none required** — a one-way edge cannot deadlock.
- Module 59 calculates SOM equilibrium targets within the timestep, consuming M29's tree cover.
- Tree cover raises soil carbon **inside M59's own accounting**; that result does not flow back into
  M29's decisions.

**Testing Protocol** (if modifying Module 29):
- ✅ Verify land balance (`q10_land_area`): `sum(land, vm_land(j2,land)) =e= sum(land, pcm_land(j2,land))`
- ✅ Check cropland components sum correctly: `vm_land("crop") = vm_area + vm_fallow + vm_treecover`
- ✅ Test fallow/tree cover policies don't make cropland infeasible
- ✅ Verify soil carbon dynamics converge (Module 59 interaction)

**Reference**: `cross_module/circular_dependency_resolution.md` (Section 3, Major Cycles)

---

### Modification Safety

**Risk Level**: 🔴 **HIGH RISK**

**Justification**:
- Participates in **4 of 5 conservation laws** (land, carbon, food, nitrogen)
- Dependent modules affected by changes (see `core_docs/Module_Dependencies.md` for complete list)
- 2 circular dependency cycles (cropland allocation + soil carbon)
- Core module for land use policy (SNV, fallow, tree cover)

**Safe Modifications**:
- ✅ Adjusting fallow land policies (`s29_snv_shr`, `s29_snv_shr_noselect`)
- ✅ Changing tree cover targets (`s29_treecover_target`, `s29_treecover_bii_coeff`)
- ✅ Modifying semi-natural vegetation (SNV) cost parameters
- ✅ Adding new cropland management options (requires new equations)
- ✅ Updating biodiversity coefficients for fallow/tree cover

**Dangerous Modifications**:
- ⚠️ Removing cropland aggregation equation → breaks land balance in Module 10
- ⚠️ Hardcoding `vm_land("crop")` → prevents cropland expansion/contraction
- ⚠️ Changing fallow/tree cover equations without testing land availability
- ⚠️ Modifying soil carbon linkage (Module 59) → can break carbon balance convergence

**Required Testing** (for ANY modification):
1. **Land Balance Conservation**:
   - Verify (`q10_land_area`): `sum(land, vm_land(j2,land)) =e= sum(land, pcm_land(j2,land))` for all cells
   - Check cropland components sum correctly
   - Test that fallow + tree cover + harvested area ≤ available cropland

2. **Carbon Balance Conservation**:
   - Verify soil carbon converges to equilibrium (Module 59)
   - Check tree cover carbon accumulation is realistic
   - Test that cropland carbon stocks are tracked correctly

3. **Food Balance**:
   - Verify cropland expansion/contraction affects production (Module 30)
   - Test that fallow/tree cover policies don't cause food shortages

4. **Nitrogen Tracking**:
   - Check that N demand scales with cropland area
   - Verify soil N dynamics respond to land use changes

5. **Circular Dependency Check**:
   - Run model and verify convergence (no oscillations)
   - Test extreme scenarios (100% fallow, 100% tree cover)
   - Check that land allocation and SOM dynamics are stable

**Common Issues**:
- **Infeasibility from SNV/tree cover**: Fallow + tree cover targets exceed available cropland → reduce policy ambition
- **Soil carbon divergence**: SOM module doesn't converge → check Module 59 convergence rate
- **Biodiversity miscalculation**: BII coefficients wrong → verify `s29_treecover_bii_coeff` reasonable
- **Cost explosion**: SNV costs too high → model avoids cropland entirely → reduce cost parameters

**Reference**: `cross_module/modification_safety_guide.md` (High-Risk Modules)

---

## Limitations

### 1. Uniform Tree Cover Within Cells
**What**: All tree cover in a cell has same BII coefficient (by age class)
**Where**: `q29_treecover_bv` applies uniform coefficients
**Impact**: Cannot differentiate between different tree species or management intensities within a cell

### 2. Binary Growth Curve Choice
**What**: Must choose either natural vegetation OR plantation growth curve
**Where**: `s29_treecover_plantation` switch is 0 or 1
**Impact**: Cannot mix different tree cover types with different growth trajectories

### 3. No Spatial Heterogeneity in Costs
**What**: Treecover establishment and recurring costs are uniform globally
**Where**: `s29_cost_treecover_est`, `s29_cost_treecover_recur` are scalars
**Impact**: Ignores regional variation in labor costs, accessibility, species selection

### 4. Static Penalty Values
**What**: Penalties for violating targets do not change over time (except before/after scenario start)
**Where**: `i29_treecover_penalty(t)`, `i29_fallow_penalty(t)` fixed after start year
**Impact**: Cannot model increasing enforcement or changing policy stringency

### 5. Fallow Land Has No Age Dynamics
**What**: Fallow land treated as homogeneous (no young vs old fallow)
**Where**: `vm_fallow(j)` is single variable without age classes
**Impact**: Cannot model biodiversity or carbon benefits of long-term vs short-term fallow

### 6. SNV Constraint Applies to Secondary Forest and Other Land Only
**What**: SNV share enforced only on secdforest and other land, not primary forest or pasture
**Where**: `land_snv = {secdforest, other}` (`input.gms:70`)
**Impact**: Cannot redirect cropland to grassland for SNV requirements

### 7. Country Weighting by Available Cropland
**What**: Country influence weighted by available cropland, not actual cropland or population
**Where**: `p29_country_weight` calculation (`preloop.gms`)
**Impact**: Countries with large marginal land dominate even if they have little actual agriculture

### 8. No Tree Cover Harvest
**What**: Once established, tree cover cannot be harvested (only ages and accumulates carbon)
**Where**: `v29_treecover.fx(j,ac_sub) = pc29_treecover(j,ac_sub)` (`presolve.gms:81`) pins every
non-establishment age class to the previous timestep's state, so the optimizer can plant but never
remove. There are also no equations for timber production from cropland trees.
**Impact**: Cannot model agroforestry with periodic timber harvest cycles

> ⚠️ **CORRECTED (R58, 2026-07-17)**: the symptom was right but the **mechanism was misattributed** to
> "no equations for tree removal". The binding cause is the presolve `.fx` (see §1 Components).

### 9. Treecover Establishment Equally Distributed
**What**: New trees split equally among ac_est age classes (e.g., 50% ac0, 50% ac5 for 10-yr timestep)
**Where**: `q29_treecover_est` (`equations.gms`)
**Impact**: Assumes continuous planting, cannot model concentrated establishment events

### 10. SNV Relocation Based on 2019 Satellite Data
**What**: Relocation targets from static 2019 Copernicus data, not updated
**Where**: `f29_snv_target_cropland` from SNVTargetCropland.cs3
**Impact**: Does not account for land cover changes between 2019 and model run

### 11. No Explicit Tree Species
**What**: Tree cover treated generically, no species-specific parameters
**Where**: Carbon density and BII coefficients apply uniformly
**Impact**: Cannot model benefits/costs of specific agroforestry species (fruit trees, timber, nitrogen-fixing, etc.)

### 12. Fallow and Treecover Compete for Same Land
**What**: Both count towards total cropland, but no explicit interaction
**Where**: Both in `q29_cropland` equation, share same constraint
**Impact**: Cannot enforce combined targets (e.g., "20% treecover OR fallow")

---

## Verification Notes

> ⚠️ **CORRECTED (R58, 2026-07-17)**: this section previously certified the doc defect-free —
> *"**No Errors Found**: Zero discrepancies between code and documentation"*, *"**Verification Status**:
> 100% verified"*, *"**Code Truth Compliance**: ✅ All claims verified"*, and *"**Citation Density**: 80+
> file:line citations"*. **Those claims were false and are removed.** An adversarial audit plus an
> independent refutation pass (R58) found **18 confirmed defects, 2 of them Critical**, in this file.
>
> The banner's defect was **scope creep from a true narrow claim to a false total one**: the
> verification that *was* performed (equation formulas — genuinely clean) generalized least to the parts
> that were not (presolve bounds, macro expansion, interface sets, cross-module invariants). Its harm
> was asymmetric — it was most reassuring exactly where this doc was weakest, and it is why M29 carried
> a phantom parameter and an inverted carbon trade-off for ~20 months. **Scoped statements only below.**

### What IS verified (R58, 2026-07-17, against develop @ `0d7ebeb90`)

**Equation Count**: 🟢 16 equations (detail_apr24) — `rg -c '^\s*q29_' modules/29_cropland/detail_apr24/declarations.gms` → 16. `simple_apr24` has **5** (`modules/29_cropland/simple_apr24/declarations.gms:27-31`).

**Formula Accuracy**: 🟢 All 16 `q29_*` formulas match `modules/29_cropland/detail_apr24/equations.gms:11-123` — verified character-by-character. This claim survived the R58 audit intact and is the doc's strongest area.

**Line counts**: 🟢 `wc -l modules/29_cropland/detail_apr24/*.gms` → equations.gms **123**, input.gms **103**, sets.gms **16**, presolve.gms **130**, preloop.gms **68** = **440** lines.

> ⚠️ **CORRECTED (R58)**: previously "124 + 103 + 17 + 131 + 69 = **444**". Four of five components were
> off by exactly +1 while the arithmetic summed correctly — the signature of counts produced by
> recollection rather than measurement.

**Citation density**: 🟢 measured this session — 67 `file:line` citations (was "80+", inflated ~20%).
Note ~30 bare `equations.gms` references still carry **no line number**.

### What is NOT verified

- ❌ **Input data file contents** — `avl_cropland.cs3`, `avl_cropland_iso.cs3`, `SNVTargetCropland.cs3`, `CroplandTreecover.cs2` were not parsed. Units ("Mio. ha") and vintages ("2015", "2019") are verified against the **declaration text** (`modules/29_cropland/detail_apr24/input.gms:75-103`) only → 🟡 documented, not 🟢 data-verified. Limitation #10's "2019 Copernicus data" inherits this caveat.
- ❌ **No model was run.** All behavioural claims — most importantly the capability-vs-default box in the Overview — are derived **algebraically** from bounds, equations, and defaults, not from a GDX.
- ❌ **Cross-doc propagation** — this file's former phantom "Cycle C29" and malformed land-balance invariant may have propagated into `cross_module/circular_dependency_resolution.md` and `cross_module/land_balance_conservation.md`; not checked. `core_docs/Module_Dependencies.md` is known to disagree with this file (see the Centrality caveat) and is under human-adjudication hold.
- ❌ **Consumer greps are a lower bound** — macro-mediated reads that pass a variable as a bare macro argument (as `modules/58_peatland/v2/equations.gms:23` does with `m58_LandMerge`) would be missed by the `name(` / `name.` patterns used.

**Note**: Module uses macros (`m_carbon_stock_ac`, `m_linear_time_interpol`, `m_sigmoid_time_interpol`, `m_linear_cell_data_interpol`, `m_boundfix`) which are defined in core GAMS files, not module-specific. **Macro-expansion semantics are one indirection away from the cited file** and were a defect cluster in R58 — see the `m_carbon_stock_ac` dispatch box in §4.

---

**Last Verified**: 2026-07-17 (R58 audit + refutation + fix pass)
**Verified Against**: `../modules/29_cropland/{detail,simple}_apr24/*.gms` @ develop `0d7ebeb90`
**Verification Method**: Adversarial audit (168 claims), independent refutation pass, then per-finding re-derivation against `.gms` source before each fix.
**Changes Since Last Verification**: MAgPIE-side, `modules/29_cropland/` last changed **2026-03-21** (`896a9b728`); most recent structural change `75d7ee167` (2026-03-15, renamed `pm_carbon_density_{secdforest,plantation}_ac` → `*_ac_uncalib`), and `detail_apr24/scaling.gms` was created in `da316ed4a` (2026-03-12).

> ⚠️ **CORRECTED (R58, 2026-07-17)**: this footer previously read *"**Last Verified**: 2025-10-13"* /
> *"**Changes Since Last Verification**: None (stable)"*. That was **self-refuting**: five files changed
> across four commits after 2025-10-13, and the body demonstrably described code that did not exist on
> that date — it used the `_uncalib` names (introduced 2026-03-15) and described `scaling.gms` (created
> 2026-03-12). So the footer could not be trusted even as a lower bound. Because it fed the staleness
> badge (AGENT.md Step 1b) and `/sync` triage, "None (stable)" is how a high-centrality module
> accumulated 18 defects unreviewed.
