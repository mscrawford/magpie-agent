# Module 59 (Soil Organic Matter) — Round 34 Answer

**Question**: How does Module 59 (soil organic matter) compute the soil carbon pool and contribute to vm_carbon_stock? Name the default realization, the q59_* equations, and the vm_area / fm_carbon_density inputs it reads.

---

## Default Realization

`cellpool_jan23`

Confirmed in `config/default.cfg`: `cfg$gms$som <- "cellpool_jan23"`.

A legacy alternative `static_jan19` exists (IPCC 2006 factors, no temporal dynamics). A third directory `cellpool_aug16` exists on disk but has been removed from the model (no code files, not listed in `module.gms`).

---

## Computation Pipeline: Soil Carbon Pool to vm_carbon_stock

Module 59 uses a three-layer computation:

**Layer 1 — Compute the equilibrium target** (`v59_som_target`)

**Layer 2 — Move the actual pool toward that target** (`v59_som_pool`)

**Layer 3 — Assemble total soil carbon (topsoil + static subsoil) into vm_carbon_stock**

### Layer 1a: Cropland Equilibrium Target

**Equation**: `q59_som_target_cropland` (`equations.gms:20-27`)

```gams
v59_som_target(j2,"crop") =e=
    (sum((kcr,w), vm_area(j2,kcr,w) * i59_cratio(j2,kcr,w))
     + sum((kcr,w,ct), vm_area(j2,kcr,w) * i59_scm_target(ct,j2)
           * i59_cratio(j2,kcr,w) * (i59_cratio_scm(j2) - 1))
     + vm_fallow(j2) * i59_cratio_fallow(j2)
     + vm_treecover(j2) * i59_cratio_treecover)
    * sum(ct, f59_topsoilc_density(ct,j2));
```

**Key input read here**: `vm_area(j2,kcr,w)` — crop area by cell, crop type, and irrigation type (provided by Module 17).

The carbon ratio `i59_cratio(j,kcr,w)` is a product of four IPCC 2019 stock change factors assembled in preloop: land use × tillage × input × irrigation. Default management: full tillage = 1.0, medium input = 1.0 (`preloop.gms:52-55`). Natural topsoil carbon density `f59_topsoilc_density(ct,j)` is read from LPJmL output (`lpj_carbon_topsoil.cs2b`); under the default `c59_som_scenario = "cc"` it varies over time with climate change.

### Layer 1b: Non-Cropland Equilibrium Target

**Equation**: `q59_som_target_noncropland` (`equations.gms:31-34`)

```gams
v59_som_target(j2,noncropland59) =e=
    vm_land(j2,noncropland59) * sum(ct, f59_topsoilc_density(ct,j2));
```

Non-cropland land types (pasture, forestry, primforest, secdforest, other, urban) are assumed to hold carbon at natural density. Their SOM is therefore NOT dynamically responsive to land management — only land area changes drive the target.

**Key input read here**: `vm_land(j2,noncropland59)` — land area by type (provided by Module 10).

### Layer 2: Actual Pool (Dynamic Convergence)

**Equation**: `q59_som_pool` (`equations.gms:46-52`)

```gams
v59_som_pool(j2,land) =e=
    sum(ct, i59_lossrate(ct)) * v59_som_target(j2,land)
    + (1 - sum(ct, i59_lossrate(ct)))
      * sum((ct,land_from), p59_carbon_density(ct,j2,land_from)
            * vm_lu_transitions(j2,land_from,land));
```

The actual pool is a weighted blend:
- **Fraction `lossrate`** moves to the new equilibrium target.
- **Fraction `(1 - lossrate)`** retains the carbon density inherited from the land-use transition matrix `vm_lu_transitions`.

The lossrate is time-step-dependent (`preloop.gms:45`):

```gams
i59_lossrate(t) = 1 - 0.85^m_yeardiff(t);
```

For standard 5-year timesteps: lossrate ≈ 0.556 (56% of the gap closes). The 0.85 base encodes a 15% annual convergence toward equilibrium.

**Key input read here**: `vm_lu_transitions(j,land_from,land_to)` — transition matrix of land-use change (provided by Module 10). This is the key innovation: carbon densities from the *origin* land type are carried through transitions, preventing spurious jumps.

### Layer 3: Assembly into vm_carbon_stock

**Equation**: `q59_carbon_soil` (`equations.gms:61-64`)

```gams
vm_carbon_stock(j2, land, "soilc", stockType) =e=
    v59_som_pool(j2, land)
    + vm_land(j2, land) * sum(ct, i59_subsoilc_density(ct,j2));
```

Total soil carbon = dynamic topsoil pool + static subsoil reference.

**fm_carbon_density input**: Subsoil density is initialized in preloop as:

```gams
i59_subsoilc_density(t_all,j) = fm_carbon_density(t_all,j,"other","soilc") - f59_topsoilc_density(t_all,j);
```

(`preloop.gms:12`) — i.e., Module 59 reads `fm_carbon_density` for the "other" land type and strips out the topsoil component. Subsoil is then held static throughout the simulation; only topsoil (`v59_som_pool`) is computed dynamically.

The resulting `vm_carbon_stock(j,land,"soilc",stockType)` is the interface to Module 52 (carbon), which uses it for carbon stock accounting and emissions calculation.

---

## Complete q59_* Equation List

| Equation | Location | Purpose |
|----------|----------|---------|
| `q59_som_target_cropland` | `equations.gms:20-27` | Equilibrium SOM pool for cropland (crop-specific IPCC factors) |
| `q59_som_target_noncropland` | `equations.gms:31-34` | Equilibrium SOM pool for non-cropland (= natural density × area) |
| `q59_som_pool` | `equations.gms:46-52` | Actual pool as blend of target and transition-inherited carbon |
| `q59_carbon_soil` | `equations.gms:61-64` | Total soil C = topsoil pool + static subsoil → writes vm_carbon_stock |
| `q59_nr_som` | `equations.gms:69-75` | Nitrogen release from SOM loss (C:N = 15, annual rate) |
| `q59_nr_som_fertilizer` | `equations.gms:81-84` | Plant-available N <= total N released (inequality upper bound) |
| `q59_nr_som_fertilizer2` | `equations.gms:88-91` | Plant-available N additionally <= vm_landexpansion * s59_nitrogen_uptake |
| `q59_cost_scm` | `equations.gms:98-101` | Soil carbon management cost = area × SCM target share × recurring cost |

---

## vm_area and fm_carbon_density Inputs in Detail

**`vm_area(j,kcr,w)`** — consumed in two equations:
1. `q59_som_target_cropland`: multiplied by `i59_cratio(j,kcr,w)` to compute the cropland carbon equilibrium target; each crop × irrigation combination has a distinct IPCC stock change factor.
2. `q59_cost_scm`: summed over all crops and irrigation types to compute the total cropland area subject to SCM costs.

**`fm_carbon_density(t,j,"other","soilc")`** — consumed in `preloop.gms:12` to derive `i59_subsoilc_density`. This is the only use: Module 59 reads the total soil carbon density for the "other" (natural vegetation) land type from the input data, then subtracts the LPJmL-sourced topsoil component to isolate the subsoil fraction. After preloop, `fm_carbon_density` is not re-read in equations — the subsoil value is held fixed, and the topsoil is tracked via `v59_som_pool` and `p59_carbon_density`.

---

## Critical Limitations Relevant to the Question

- Pastures and forests are assumed to maintain natural SOM (their target = natural density × area). The SOM dynamics in `q59_som_pool` apply to all land types in the GAMS equation, but for non-cropland the target is always natural density, so the dynamic is driven purely by land-area changes and not by management.
- Subsoil carbon is static. Only the topsoil component (`v59_som_pool`) responds to land-use change.
- Default tillage is full tillage everywhere; default inputs are medium input everywhere. These are constant parameters in `i59_cratio`, not optimized variables.
- The 15% annual convergence rate (`i59_lossrate`) is uniform across all soils, climates, and timesteps.

---

**Source**: `modules/module_59.md` (verified 2026-03-06 against `../modules/59_*/cellpool_jan23/*.gms`; 8/8 equations documented)

**Epistemic hierarchy**:
- 🟡 **Documented** — All equation formulas, variable names, parameter names, and default values are drawn from `module_59.md`, which was cross-referenced against GAMS source at the time of documentation. Line numbers cited from the docs were current as of 2026-03-06; code changes since that date may have shifted them. For critical modification work, verify against current `equations.gms` and `preloop.gms` in the active realization directory.
