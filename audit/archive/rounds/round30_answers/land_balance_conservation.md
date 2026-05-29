# Land Area Conservation in MAgPIE (Default Realization)

## Core enforcement equation

MAgPIE enforces land-area conservation through **equation `q10_land_area`**, implemented in Module 10's only realization, `landmatrix_dec18`:

```
q10_land_area(j2) ..
  sum(land, vm_land(j2,land)) =e=
  sum(land, pcm_land(j2,land));
```

Source: `modules/10_land/landmatrix_dec18/equations.gms:13-15` (module_10.md, section 2, Equation 1; also cross_module/land_balance_conservation.md, section 3.1)

**Operator `=e=`** is a strict equality constraint — hard, with no tolerance. The left-hand side is the sum of the optimization variable `vm_land(j,land)` over all land types in the current timestep; the right-hand side is `pcm_land(j,land)`, the parameter holding the previous timestep's solved allocation. The constraint applies independently to **every spatial cell `j`**, so regional totals are not being conserved — **cell-level totals** are conserved, and regional totals follow as an aggregate consequence.

After each timestep solve, `postsolve.gms:9` updates the recursive state:
```
pcm_land(j,land) = vm_land.l(j,land);
```
This means each timestep's solved allocation becomes the fixed reference total for the next timestep, producing path-dependent dynamics where past decisions constrain future land availability.

---

## The seven land types in `vm_land`

`vm_land(j,land)` is dimensioned over the `land` set (`core/sets.gms:250-251`), which contains exactly seven mutually exclusive pools:

| Code | Land type | Module responsible |
|---|---|---|
| `crop` | Cropland (cultivated area) | 29, 30 |
| `past` | Pasture (grazed grassland) | 31 |
| `forestry` | Managed forest (plantations + NPI/NDC + CDR afforestation) | 32 |
| `primforest` | Primary (intact, undisturbed) forest | 35 |
| `secdforest` | Secondary (regenerating) forest, >20 tC/ha threshold | 35 |
| `other` | Other natural land (savanna, shrubland, young secondary forest) | 35 |
| `urban` | Built-up area, settlements | 34 |

The conservation constraint requires:
```
vm_land(j,"crop") + vm_land(j,"past") + vm_land(j,"forestry") +
vm_land(j,"primforest") + vm_land(j,"secdforest") + vm_land(j,"other") + vm_land(j,"urban")
= constant(j) for all t
```

---

## Which land types and modules can shift area

Module 10 does not determine allocation — it enforces accounting. Six other modules set individual land-type values; their changes must sum to zero across the seven pools.

**`crop` (Modules 29, 30)** — endogenous, optimized. Module 29 (`q29_cropland`) constrains `vm_land(j,"crop")` to equal the sum of harvested crop area `vm_area(j,kcr,w)` across 19 crop types and water regimes, plus fallow land `vm_fallow(j)`, plus tree cover `v29_treecover(j,ac)`. Module 30 then allocates the crop area among specific crops. Cropland can expand into or release to any other pool except primary forest (transition restriction — see below).

**`past` (Module 31)** — endogenous. Pasture area is optimized to meet livestock feed demand (equation `q31_prod`: production <= area x yield). It competes with crop and forestry for available land.

**`forestry` (Module 32)** — endogenous, age-class tracked. Equation `q32_land` aggregates three forestry sub-types (`plant`, `ndc`, `aff`) across age classes `ac` into `vm_land(j,"forestry")`. Area can expand via afforestation or shrink through harvest rotation. Expansion is constrained by the maximum forest establishment potential from Module 35.

**`primforest` (Module 35)** — one-way decline only. Primary forest can only decrease; no transition into this pool is allowed (`vm_lu_transitions.fx(j,land_from,"primforest") = 0` in `presolve.gms:20`, with the exception `vm_lu_transitions.up(j,"primforest","primforest") = Inf` allowing persistence). The variable `vm_land(j,"primforest")` decreases when conversion to crop, past, or secdforest occurs.

**`secdforest` (Module 35)** — endogenous, age-class tracked. Equation `q35_land_secdforest` aggregates age classes `v35_secdforest(j,ac)`. Area grows through natural recovery and the maturation of young secondary forest once carbon density exceeds 20 tC/ha; it shrinks through conversion to managed land types.

**`other` (Module 35)** — endogenous. Equation `q35_land_other` aggregates sub-components `vm_land_other(j,othertype35,ac)`. This pool is the typical residual recipient of abandoned agricultural land, and the source when natural land is converted to agriculture or forestry.

**`urban` (Module 34)** — exogenous, prescribed. Equation `q34_urban_land` forces the regional sum of `vm_land(j,"urban")` to equal externally-provided LUH3 data `i34_urban_area`. Urban land can only increase (high deviation costs of 1e6 USD/ha effectively prevent reduction). Because this pool is prescribed but still included in the `q10_land_area` balance, any urban expansion directly compresses the other six pools.

---

## Transition restrictions inside the balance

Module 10 also enforces which conversions are permitted via a 7x7 transition matrix variable `vm_lu_transitions(j,land_from,land_to)`. Two companion equations link this matrix to `vm_land`:

- `q10_transition_to`: sum of all inflows to `land_to` = current `vm_land(j,land_to)` (`equations.gms:19-21`)
- `q10_transition_from`: sum of all outflows from `land_from` = previous `pcm_land(j,land_from)` (`equations.gms:23-25`)

Together these guarantee that all land has an accounting source and destination, reinforcing `q10_land_area` at the transition level.

**Key hard restrictions (`presolve.gms:10-23`):**
- `primforest -> forestry` = 0 (no plantation on intact forest)
- Any `land_from -> primforest` = 0 (primary forest cannot be created)
- `primforest -> other` = 0 and `secdforest -> other` = 0 (natural vegetation type-switching blocked via the transition matrix; Module 35 age-class dynamics handle internal transitions)

---

## Summary of what can shift

Within the conserved cell total, the following are free to shift competitively:

- crop <-> past <-> forestry <-> secdforest <-> other (all bidirectional, subject to costs and conservation policy constraints)
- primforest can only decrease (one-way source)
- urban can only increase (exogenously prescribed, one-way sink)

Module 10 is the central enforcer with the highest connectivity in the model (17 connections; `vm_land` consumed directly by 10 modules). Any modification to Module 10 equations propagates to 15 downstream modules.

---

**Epistemic status:**
- 🟡 Documented: equation text and variable names drawn from `modules/module_10.md` (verified against GAMS code as of last doc sync; `cross_module/land_balance_conservation.md` sections 3-5) — not re-read from raw GAMS source this session.
- Line numbers carry the standard caveat: they were verified at the module doc's last update; code changes since then may have shifted them.

Sources consulted:
- `magpie-agent/cross_module/land_balance_conservation.md` (sections 1-5, 10)
- `magpie-agent/modules/module_10.md` (sections 2-7)
