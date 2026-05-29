# Q1: How does MAgPIE enforce conservation of total land area, and what prevents double-counting when land moves between uses?

## 1. The Conservation Constraint

**Equation**: `q10_land_area` — strict equality (`=e=`)

```gams
q10_land_area(j2) ..
  sum(land, vm_land(j2,land)) =e=
  sum(land, pcm_land(j2,land));
```

**Source**: `modules/10_land/landmatrix_dec18/equations.gms:13-15`

This is a **hard equality constraint**, not an inequality. The solver cannot satisfy the model unless, in every cell `j`, the sum of all seven land types at the current timestep equals the sum at the previous timestep. There is no tolerance: `=e=` in GAMS means algebraic equality. Land cannot be created or destroyed; it can only be reallocated.

**Variables**:
- LHS: `vm_land(j,land)` — current-period land area, optimization variable (mio. ha)
- RHS: `pcm_land(j,land)` — previous-period land area, parameter updated after each solve via `postsolve.gms:9`:
  ```gams
  pcm_land(j,land) = vm_land.l(j,land);
  ```
  This recursive update creates the path-dependent dynamics: each timestep's solution becomes the next timestep's starting point.

---

## 2. The Seven Land Pools

All seven `land` set members participate in `q10_land_area`. From `core/sets.gms:250-251`:

| Code | Description | Module responsible |
|------|-------------|-------------------|
| `crop` | Cropland (cultivated; includes fallow, tree cover) | 29, 30 |
| `past` | Pasture (grazed grassland) | 31 |
| `forestry` | Timber plantations + NPI/NDC afforestation + CDR afforestation | 32 |
| `primforest` | Intact, undisturbed primary forest | 35 |
| `secdforest` | Regenerating/disturbed secondary forest (age-class tracked) | 35 |
| `other` | Natural non-forest vegetation: savanna, shrubland, young secondary forest | 35 |
| `urban` | Built-up area (exogenous, prescribed by SSP/LUH3) | 34 |

The expanded form of `q10_land_area` is:

```
vm_land(j,"crop") + vm_land(j,"past") + vm_land(j,"forestry") +
vm_land(j,"primforest") + vm_land(j,"secdforest") + vm_land(j,"other") + vm_land(j,"urban")
= same sum from previous timestep
```

No land pool is outside this sum.

---

## 3. The Transition Matrix and Double-Counting Prevention

The conservation constraint alone prevents total area drift, but it does not by itself prevent double-counting within a timestep (e.g., the same hectare being counted as both a source and a destination). That is handled by **two companion equality constraints** on the transition matrix variable `vm_lu_transitions(j,land_from,land_to)` (mio. ha), a 7×7 matrix (49 entries per cell):

### 3a. Source conservation (`q10_transition_from`)

```gams
q10_transition_from(j2,land_from) ..
  sum(land_to, vm_lu_transitions(j2,land_from,land_to)) =e=
  pcm_land(j2,land_from);
```

**Source**: `modules/10_land/landmatrix_dec18/equations.gms:23-25`

Every hectare that was in `land_from` at the previous timestep must be routed to exactly one destination. The total outflow from any source type equals its prior-period area. There is no remainder; there is no double-assignment.

### 3b. Destination conservation (`q10_transition_to`)

```gams
q10_transition_to(j2,land_to) ..
  sum(land_from, vm_lu_transitions(j2,land_from,land_to)) =e=
  vm_land(j2,land_to);
```

**Source**: `modules/10_land/landmatrix_dec18/equations.gms:19-21`

Every hectare that ends up in `land_to` at the current timestep must have come from exactly one source. The total inflow to any destination type equals its current-period area.

### How these two constraints close the double-counting gap

- `q10_transition_from` guarantees: no hectare leaves a source type more than once (each row of the matrix sums to the prior-period row total).
- `q10_transition_to` guarantees: no hectare enters a destination type more than once (each column of the matrix sums to the current-period column total).
- Together with `q10_land_area`, they form a fully closed, doubly-balanced accounting system: row sums = previous-period areas, column sums = current-period areas, and both total the same fixed cell area.

The diagonal entries `vm_lu_transitions(j,land,"same land")` represent persistence — land that stays in its type — and are explicitly included. This is not counted as expansion or reduction.

---

## 4. Expansion and Reduction Metrics (Off-Diagonal Summaries)

Two additional equations derive the gross change variables used by other modules:

**Land expansion** (`q10_landexpansion`, `equations.gms:30-33`):
```gams
q10_landexpansion(j2,land_to) ..
    vm_landexpansion(j2,land_to) =e=
    sum(land_from$(not sameas(land_from,land_to)),
    vm_lu_transitions(j2,land_from,land_to));
```
Expansion = inflows from types other than itself (off-diagonal columns).

**Land reduction** (`q10_landreduction`, `equations.gms:35-38`):
```gams
q10_landreduction(j2,land_from) ..
    vm_landreduction(j2,land_from) =e=
    sum(land_to$(not sameas(land_from,land_to)),
    vm_lu_transitions(j2,land_from,land_to));
```
Reduction = outflows to types other than itself (off-diagonal rows).

Both are `=e=` (strict equality). These variables are consumed by modules 35, 39, 58, and 59.

---

## 5. Transition Restrictions (Presolve)

Several transition matrix entries are fixed to zero via bounds in `presolve.gms:10-23`, enforcing ecological and policy constraints:

- **No plantation forestry on primary forest**: `vm_lu_transitions.fx(j,"primforest","forestry") = 0`
- **No new primary forest from any source**: `vm_lu_transitions.fx(j,land_from,"primforest") = 0` for all `land_from` (except self-persistence: `vm_lu_transitions.up(j,"primforest","primforest") = Inf`)
- **No direct primforest → other or secdforest → other**: these within-natveg transitions are handled by Module 35's internal age-class dynamics, not via Module 10's transition matrix

These restrictions reduce the feasible space but do not alter the conservation structure; the equality constraints continue to hold for all non-fixed entries.

---

## 6. Is Any Land Ever Lost or Created?

No. `q10_land_area` is a strict equality (`=e=`), enforced for every cell at every timestep. Land is also initialized from LUH2 data in `start.gms:8`:

```gams
pm_land_start(j,land) = f10_land("y1995",j,land);
```

The total per-cell area observed in 1995 becomes the conserved constant. Because each timestep's solution is transferred to `pcm_land` via `postsolve.gms:9`, the constant propagates forward indefinitely. There is no mechanism in Module 10 for land addition or removal.

The only nuance: urban land (`urban`) is prescribed exogenously by Module 34 and cannot decrease. When urban expands, the remaining six pools must collectively contract by the same amount — enforced by `q10_land_area`. This is still conservation: urban expansion does not create land, it displaces other land uses.

---

## 7. Gross Land-Use Change Aggregation

A final equation aggregates global gross change:

```gams
q10_landdiff ..
    vm_landdiff =e= sum((j2,land), vm_landexpansion(j2,land)
                                 + vm_landreduction(j2,land))
                                 + vm_landdiff_natveg
                                 + vm_landdiff_forestry;
```

**Source**: `modules/10_land/landmatrix_dec18/equations.gms:50-54`

- `vm_landexpansion` + `vm_landreduction`: captures between-type transitions (Module 10's transition matrix)
- `vm_landdiff_natveg`: within-natveg changes (primary→secondary, age-class shifts) from Module 35
- `vm_landdiff_forestry`: within-forestry age-class and harvest changes from Module 32

This is a reporting variable; it does not alter the conservation constraint.

**Note from documentation** (`realization.gms:11`): Module 10 accounts only for **net** land-use transitions between types. If 10 ha of forest is cleared while 10 ha of cropland recovers to forest in the same timestep, the net transition matrix entry is zero. Sub-timestep opposing flows are not captured.

---

## 8. Summary Table

| Mechanism | Equation | Type | Variables | File:line |
|-----------|----------|------|-----------|-----------|
| Total area conservation | `q10_land_area` | `=e=` equality | `vm_land(j,land)`, `pcm_land(j,land)` | `equations.gms:13-15` |
| Source non-duplication | `q10_transition_from` | `=e=` equality | `vm_lu_transitions(j,land_from,land_to)`, `pcm_land(j,land_from)` | `equations.gms:23-25` |
| Destination non-duplication | `q10_transition_to` | `=e=` equality | `vm_lu_transitions(j,land_from,land_to)`, `vm_land(j,land_to)` | `equations.gms:19-21` |
| Gross expansion metric | `q10_landexpansion` | `=e=` equality | `vm_landexpansion(j,land)` | `equations.gms:30-33` |
| Gross reduction metric | `q10_landreduction` | `=e=` equality | `vm_landreduction(j,land)` | `equations.gms:35-38` |
| Global gross change | `q10_landdiff` | `=e=` equality | `vm_landdiff` | `equations.gms:50-54` |
| Recursive state update | (postsolve) | assignment | `pcm_land` ← `vm_land.l` | `postsolve.gms:9` |

All constraints are strict equalities. No land pool is exempt. No land is ever created or destroyed.

---

## Sources

- 🟢 **Verified**: `modules/module_10.md` — equations, variables, line numbers, realization
- 🟢 **Verified**: `cross_module/land_balance_conservation.md` — conservation law detail, module interactions, all 7 land pools
- Both documents state the source code reference: `modules/10_land/landmatrix_dec18/equations.gms`
- Line numbers cited from those documents; may drift with code changes since last sync (see `project/sync_log.json` for last-sync date)
