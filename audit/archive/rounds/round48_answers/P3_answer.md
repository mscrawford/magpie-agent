# P3 Answer: MAgPIE Land Balance Guarantee

## Question
How does MAgPIE's land balance guarantee that the sum of all land-use types equals the total available land in every spatial unit, with no double-counting and no creation or destruction of area? Which equation enforces this, how is it structured, and how are land-use transitions constrained so that area is conserved across timesteps?

---

## Answer

### 1. The Seven Mutually Exclusive Land Pools

MAgPIE partitions every spatial cell into **7 mutually exclusive land types** defined in the `land` set (`core/sets.gms:250-251`):

| Code | Description | Module |
|------|-------------|--------|
| `crop` | Cropland (food, feed, bioenergy, fallow, tree cover) | 29, 30 |
| `past` | Pasture (grazed grassland) | 31 |
| `forestry` | Managed forestry (plantations, NPI/NDC, CDR) | 32 |
| `primforest` | Primary (intact, undisturbed) forest | 35 |
| `secdforest` | Secondary (regenerating) forest | 35 |
| `other` | Other natural land (grassland, savanna, shrubland) | 35 |
| `urban` | Built-up area (exogenous, prescribed by SSPs) | 34 |

These types are mutually exclusive by construction: each hectare in a cell belongs to exactly one type at any point in time. Double-counting is therefore structurally impossible.

---

### 2. The Core Conservation Equation: `q10_land_area`

The strict land-area conservation law is enforced by a single GAMS equality constraint in Module 10, the only realization of which is `landmatrix_dec18`:

**Source**: `modules/10_land/landmatrix_dec18/equations.gms:13-15`

```gams
q10_land_area(j2) ..
  sum(land, vm_land(j2,land)) =e=
  sum(land, pcm_land(j2,land));
```

**Structure**:
- **LHS**: `sum(land, vm_land(j2,land))` — the sum of the optimization variable `vm_land` over all 7 land types in cell `j2` for the current timestep. This is what the solver must determine.
- **RHS**: `sum(land, pcm_land(j2,land))` — the sum of the previous-timestep parameter `pcm_land` over all 7 land types in cell `j2`. This is the starting-point total area from the prior solve.
- **Operator**: `=e=` — strict equality. This is a hard constraint; the solver cannot violate it even by epsilon.

Expanded, the equation reads:

```
vm_land(j,"crop") + vm_land(j,"past") + vm_land(j,"forestry") +
vm_land(j,"primforest") + vm_land(j,"secdforest") + vm_land(j,"other") + vm_land(j,"urban")
  =
pcm_land(j,"crop") + pcm_land(j,"past") + pcm_land(j,"forestry") +
pcm_land(j,"primforest") + pcm_land(j,"secdforest") + pcm_land(j,"other") + pcm_land(j,"urban")
```

This applies **to every cell `j` and every timestep** — there are no exceptions.

---

### 3. Recursive Dynamics: How `pcm_land` Chains Timesteps

After the optimizer solves timestep t, Module 10's postsolve step updates the parameter:

**Source**: `modules/10_land/landmatrix_dec18/postsolve.gms:9`

```gams
pcm_land(j,land) = vm_land.l(j,land);
```

The `.l` suffix accesses the solution-level value of `vm_land`. This value becomes the RHS constant in `q10_land_area` for the next timestep. The chain is:

- **1995 (start)**: `pcm_land` initialized from LUH2 historical data (`f10_land("y1995",j,land)`) via `start.gms:8`.
- **Each subsequent timestep**: `pcm_land` = previous solution's `vm_land.l`. Since `q10_land_area` required the previous solution's total to equal the one before it, and so on back to 1995, total area per cell is invariant across all timesteps.

This means land area is **path-conserved**: no area is created or destroyed anywhere in the simulation horizon.

---

### 4. Transition Matrix: Full Accounting of Where Area Goes

Conservation of the *aggregate total* (Section 2) is necessary but not sufficient for proper accounting. Area must also be tracked at the transition level: every hectare that leaves one land type must arrive at another. Module 10 implements a full **7×7 transition matrix** per cell:

**Variable**: `vm_lu_transitions(j, land_from, land_to)` — area (mio. ha) transitioning from `land_from` to `land_to` in cell `j` between the previous and current timestep. There are 49 possible transitions per cell (7×7).

Two equations enforce double-entry bookkeeping on this matrix:

#### Destination Conservation: `q10_transition_to`

**Source**: `modules/10_land/landmatrix_dec18/equations.gms:19-21`

```gams
q10_transition_to(j2,land_to) ..
  sum(land_from, vm_lu_transitions(j2,land_from,land_to)) =e=
  vm_land(j2,land_to);
```

Every hectare of current-timestep `land_to` area must be accounted for by an incoming transition from *some* `land_from` (including `land_to → land_to` for land that persists). This prevents any land type from gaining area without a documented source.

#### Source Conservation: `q10_transition_from`

**Source**: `modules/10_land/landmatrix_dec18/equations.gms:23-25`

```gams
q10_transition_from(j2,land_from) ..
  sum(land_to, vm_lu_transitions(j2,land_from,land_to)) =e=
  pcm_land(j2,land_from);
```

Every hectare of previous-timestep `land_from` area must be assigned to *some* destination (including persistence). This prevents any land type from losing area without a documented destination.

Together, `q10_transition_to` and `q10_transition_from` guarantee that the transition matrix is doubly balanced: column sums equal current area, row sums equal previous area. No land is created or destroyed at the transition level either.

---

### 5. Derived Expansion and Reduction Variables

From the transition matrix, Module 10 derives two additional variables that quantify gross change:

**Land Expansion** (`equations.gms:30-33`):
```gams
q10_landexpansion(j2,land_to) ..
    vm_landexpansion(j2,land_to) =e=
    sum(land_from$(not sameas(land_from,land_to)),
    vm_lu_transitions(j2,land_from,land_to));
```
Off-diagonal inflows only — area *gained from other types*. Used by modules 35, 39, 58, 59.

**Land Reduction** (`equations.gms:35-38`):
```gams
q10_landreduction(j2,land_from) ..
    vm_landreduction(j2,land_from) =e=
    sum(land_to$(not sameas(land_from,land_to)),
    vm_lu_transitions(j2,land_from,land_to));
```
Off-diagonal outflows only — area *lost to other types*. Used by modules 39, 58.

---

### 6. Transition Restrictions That Prevent Physically Impossible Conversions

Certain transitions are fixed to zero before the optimizer runs, via bound-fixing in presolve:

**Source**: `modules/10_land/landmatrix_dec18/presolve.gms:10-23`

Key restrictions:
1. **No plantation forestry on primary forest**:
   `vm_lu_transitions.fx(j,"primforest","forestry") = 0`
2. **Primary forest cannot be created** (one-way decline):
   `vm_lu_transitions.fx(j,land_from,"primforest") = 0` for all `land_from ≠ primforest`
   (Primforest persistence is allowed: `vm_lu_transitions.up(j,"primforest","primforest") = Inf`)
3. **Direct primforest → other blocked**:
   `vm_lu_transitions.fx(j,"primforest","other") = 0`
4. **Direct secdforest → other blocked**:
   `vm_lu_transitions.fx(j,"secdforest","other") = 0`
   (Regrowth from other → secdforest is handled internally by Module 35's age-class dynamics)

These `.fx()` bounds make the forbidden transitions structurally infeasible — the optimizer cannot choose them even if economically attractive.

---

### 7. A Note on Net vs. Gross Accounting

The transition matrix tracks **net** transitions between land types within a 5-year timestep (stated in `realization.gms:11`). If forest is cleared to cropland and the same cell's cropland regenerates to forest within the same timestep, the net is zero. Sub-timestep gross changes are not captured in `vm_lu_transitions`. However, within-type gross changes (e.g., forestry age-class rotation, natveg disturbance) are captured separately via `vm_landdiff_forestry` (Module 32) and `vm_landdiff_natveg` (Module 35), which feed into `q10_landdiff` (`equations.gms:50-54`).

---

### 8. Summary of Equations and Variables

| Name | Type | Location | Role |
|------|------|----------|------|
| `q10_land_area` | equation | `equations.gms:13-15` | Strict equality: total area constant per cell per timestep |
| `q10_transition_to` | equation | `equations.gms:19-21` | Column sums of transition matrix = current area |
| `q10_transition_from` | equation | `equations.gms:23-25` | Row sums of transition matrix = previous area |
| `q10_landexpansion` | equation | `equations.gms:30-33` | Expansion = off-diagonal inflows |
| `q10_landreduction` | equation | `equations.gms:35-38` | Reduction = off-diagonal outflows |
| `vm_land(j,land)` | variable | `declarations.gms` | Current-timestep land area per type (mio. ha) — most-shared variable |
| `pcm_land(j,land)` | parameter | `declarations.gms:11` | Previous-timestep land area; updated by `postsolve.gms:9` |
| `vm_lu_transitions(j,land_from,land_to)` | variable | `declarations.gms` | 7×7 transition matrix per cell (mio. ha) |
| `vm_landexpansion(j,land)` | variable | `declarations.gms` | Area gained from other types (mio. ha) |
| `vm_landreduction(j,land)` | variable | `declarations.gms` | Area lost to other types (mio. ha) |

---

## Source Statement

🟡 Based on: `cross_module/land_balance_conservation.md` (primary) and `modules/module_10.md` (supplementary). Equation text, line numbers, and variable names are cited as given in those documentation files, which were last verified against `modules/10_land/landmatrix_dec18/*.gms` as of 2026-03-06 (per `module_10.md` footer). Line numbers may drift if code has changed since that verification date.
