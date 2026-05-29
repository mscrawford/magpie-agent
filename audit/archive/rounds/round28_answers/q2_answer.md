# How do land-conversion costs enter MAgPIE in the DEFAULT configuration?

---

## 1. Default Realization: Module 39

**Module 39 (`39_landconversion`) default realization: `calib`**

Confirmed from `config/default.cfg`:
```
cfg$gms$landconversion <- "calib"           # def = calib
```

Location: `modules/39_landconversion/calib/`

---

## 2. What Triggers Land-Conversion Costs

Module 39 charges costs for **land expansion** (area gained from other land types) and awards rewards for **land reduction** (area lost to other land types, cropland only in calibrated regions). Both are gross flows, not net.

**Land types covered** (target land type determines cost; source land type does NOT affect cost):
- Cropland: 12,300 USD17MER/ha base
- Pasture: 9,840 USD17MER/ha (fixed global)
- Forestry: 1,230 USD17MER/ha (fixed global)
- Urban: 12,300 USD17MER/ha (fixed global)

Any conversion of one land type to another that results in **net expansion** of the target type triggers these costs. For example, forest→cropland, pasture→cropland, other→cropland all trigger the cropland expansion cost equally. The cost depends only on the **target** land type, not the source.

Reduction rewards apply only to cropland in regions with both historical cropland decline (1995–2015) AND a cost calibration factor > 1. They reduce (or may reverse the sign of) the net cost term for that land type in that region.

---

## 3. Module 10's Role: Defining the Expansion and Reduction Variables

Module 10 (`10_land`, realization `landmatrix_dec18`) is the **central land accounting hub**. It does not itself impose economic costs beyond a 1 USD/ha token penalty; all economic conversion costs come from Module 39.

Module 10 defines the full land-transition matrix and derives the expansion/reduction variables that Module 39 prices:

### Equation q10_landexpansion (`equations.gms:30-33`)
```gams
q10_landexpansion(j2,land_to) ..
    vm_landexpansion(j2,land_to) =e=
    sum(land_from$(not sameas(land_from,land_to)),
    vm_lu_transitions(j2,land_from,land_to));
```
`vm_landexpansion(j,land)` = sum of all off-diagonal inflows to `land_to` from any other land type. It represents area gained from other land types this timestep (mio. ha).

### Equation q10_landreduction (`equations.gms:35-38`)
```gams
q10_landreduction(j2,land_from) ..
    vm_landreduction(j2,land_from) =e=
    sum(land_to$(not sameas(land_from,land_to)),
    vm_lu_transitions(j2,land_from,land_to));
```
`vm_landreduction(j,land)` = sum of all off-diagonal outflows from `land_from` to any other land type. It represents area lost to other land types this timestep (mio. ha).

Both are derived from `vm_lu_transitions(j,land_from,land_to)`, the full 7×7 transition matrix per cell tracking every possible land conversion (49 transitions/cell). The transition matrix is itself constrained by:
- `q10_transition_to` (`equations.gms:19-21`): sum of all inflows to a land type = current area of that type
- `q10_transition_from` (`equations.gms:23-25`): sum of all outflows from a land type = previous area of that type
- `q10_land_area` (`equations.gms:13-15`): total land area per cell conserved strictly (∑land types = constant)

Module 10 also applies transition restrictions in `presolve.gms:10-23` (e.g., no plantation forestry on primary forest, no conversions within natveg pools).

---

## 4. Module 39's Core Cost Equation

### Equation q39_cost_landcon (`equations.gms:12-15`)
```gams
q39_cost_landcon(j,land) ..
  vm_cost_landcon(j,land) =e=
    (vm_landexpansion(j,land) * i39_cost_establish(i,land)
     - vm_landreduction(j,land) * i39_reward_reduction(i,land))
    * pm_interest(i) / (1 + pm_interest(i))
```

**Variable computed:** `vm_cost_landcon(j,land)` — land conversion costs per cell and land type (mio. USD17MER/yr)

**Components:**
- `vm_landexpansion(j,land)`: FROM Module 10 — area expanded this timestep (mio. ha)
- `vm_landreduction(j,land)`: FROM Module 10 — area reduced this timestep (mio. ha)
- `i39_cost_establish(t,i,land)`: Regional per-hectare expansion cost (USD17MER/ha), set in `presolve.gms:12-16`
- `i39_reward_reduction(t,i,land)`: Regional per-hectare reduction reward (USD17MER/ha), set in `presolve.gms:13`
- `pm_interest(t,i)`: Regional interest rate from Module 12; used as annuity factor `r/(1+r)` to annuitize the one-time conversion cost

**Sign convention:** Expansion adds to cost (positive). Reduction subtracts from cost (negative = reward). Net `vm_cost_landcon(j,land)` can be negative in regions receiving cropland reduction rewards.

### Applied costs (set in presolve.gms)

For cropland (calibrated):
```
i39_cost_establish(t,i,"crop") = s39_cost_establish_crop * i39_calib(t,i,"cost")  [presolve.gms:12]
i39_reward_reduction(t,i,"crop") = s39_reward_crop_reduction * i39_calib(t,i,"reward")  [presolve.gms:13]
```
where:
- `s39_cost_establish_crop = 12300` (input.gms:9)
- `s39_reward_crop_reduction = 7380` (input.gms:10) — 60% of expansion cost
- `i39_calib(t,i,"cost")` and `i39_calib(t,i,"reward")`: regional calibration multipliers loaded from `f39_calib.csv`, converging to minimum 1.0 by 2050

For pasture, forestry, urban: fixed global base costs are used (`presolve.gms:14-16`); no regional calibration or reduction rewards apply.

The switch `s39_ignore_calib = 0` by default (`input.gms:14`), meaning calibration is active. Setting it to 1 disables regional variation and sets all calibration factors to 1.

---

## 5. How the Cost Reaches Module 11's Objective

`vm_cost_landcon(j,land)` is a **cell- and land-type-level variable** (dimensions j, land). Module 11 (`11_costs`, realization `default`) aggregates it to the regional level in equation `q11_cost_reg`.

### Module 11 aggregation (`equations.gms:20`)
The relevant term in `q11_cost_reg(i2)`:
```gams
+ sum((cell(i2,j2),land), vm_cost_landcon(j2,land))
```
The `cell(i,j)` set maps each cell j to its region i. This sums `vm_cost_landcon` over all cells in region i and all land types, yielding the total land-conversion cost contribution to regional cost `v11_cost_reg(i)`.

### Module 11 global equation (`equations.gms:10`)
```gams
q11_cost_glo .. vm_cost_glo =e= sum(i2, v11_cost_reg(i2));
```
`vm_cost_glo` is the **objective function** MAgPIE minimizes. Every other optimization decision (land allocation, production levels, trade flows, intensification) is driven by minimizing this scalar.

### Complete cost-propagation chain

```
Module 10 (landmatrix_dec18)
  vm_lu_transitions(j, land_from, land_to)   [transition matrix, 7×7 per cell]
    → q10_landexpansion → vm_landexpansion(j, land)
    → q10_landreduction → vm_landreduction(j, land)
        ↓
Module 39 (calib)
  q39_cost_landcon(j, land):
    vm_cost_landcon(j, land) =e=
      (vm_landexpansion(j,land) * i39_cost_establish(i,land)
       - vm_landreduction(j,land) * i39_reward_reduction(i,land))
      * pm_interest(i)/(1+pm_interest(i))
        ↓
Module 11 (default)
  q11_cost_reg(i):
    v11_cost_reg(i) =e= ... + sum((cell(i,j),land), vm_cost_landcon(j,land)) + ...
  q11_cost_glo:
    vm_cost_glo =e= sum(i, v11_cost_reg(i))   ← OBJECTIVE FUNCTION
```

---

## 6. Module 10's Own Cost Variable (Distinct from Module 39)

Module 10 also produces `vm_cost_land_transition(j)` via equation `q10_cost` (`equations.gms:42-44`):
```gams
q10_cost(j2) ..
    vm_cost_land_transition(j2) =e=
    sum(land, vm_landexpansion(j2,land) + vm_landreduction(j2,land)) * 1;
```
This is a **1 USD/ha stabilization penalty** on gross land-use change (summed over all land types and both expansion and reduction). It prevents unrealistic cycling in the transition matrix. It enters Module 11 as a **separate term**:
```gams
+ sum(cell(i2,j2), vm_cost_land_transition(j2))
```
(`equations.gms:41` in Module 11)

This is entirely distinct from `vm_cost_landcon(j,land)` produced by Module 39. The Module 10 term is a numerics-stabilization token; the Module 39 term is the economically meaningful land-conversion cost.

---

## 7. Summary of Key Variables and Equations Across Three Modules

| Item | Module | File:Line (from docs) | Description |
|------|--------|-----------------------|-------------|
| `vm_lu_transitions(j,land_from,land_to)` | 10 | `declarations.gms:14-24` | Full 7×7 land transition matrix (mio. ha) |
| `q10_landexpansion(j,land)` | 10 | `equations.gms:30-33` | Defines vm_landexpansion as sum of off-diagonal inflows |
| `q10_landreduction(j,land)` | 10 | `equations.gms:35-38` | Defines vm_landreduction as sum of off-diagonal outflows |
| `vm_landexpansion(j,land)` | 10 | `declarations.gms:14-24` | Area gained from other land types (mio. ha); consumed by M39 |
| `vm_landreduction(j,land)` | 10 | `declarations.gms:14-24` | Area lost to other land types (mio. ha); consumed by M39 |
| `vm_cost_land_transition(j)` | 10 | `declarations.gms:14-24` | 1 USD/ha stabilization penalty; enters M11 separately |
| `q10_cost(j)` | 10 | `equations.gms:42-44` | Computes vm_cost_land_transition |
| `q39_cost_landcon(j,land)` | 39 | `equations.gms:12-15` | Core M39 equation: prices expansion/reduction using annuity |
| `vm_cost_landcon(j,land)` | 39 | `declarations.gms:13` | M39 output; mio. USD17MER/yr per cell-land; the interface cost variable |
| `i39_cost_establish(t,i,land)` | 39 | `declarations.gms:17` | Regional expansion cost/ha (computed in presolve.gms:12-16) |
| `i39_reward_reduction(t,i,land)` | 39 | `declarations.gms:18` | Regional reduction reward/ha (computed in presolve.gms:13) |
| `i39_calib(t,i,type39)` | 39 | `declarations.gms:19` | Calibration multipliers from f39_calib.csv |
| `s39_cost_establish_crop` | 39 | `input.gms:9` | Base cropland expansion cost: 12,300 USD17MER/ha |
| `s39_reward_crop_reduction` | 39 | `input.gms:10` | Base cropland reduction reward: 7,380 USD17MER/ha |
| `s39_ignore_calib` | 39 | `input.gms:14` | Testing switch (default 0 = calibration active) |
| `pm_interest(t,i)` | 12→39 | — | Regional interest rate; provides annuity factor r/(1+r) |
| `q11_cost_reg(i)` | 11 | `equations.gms:15-47` | Regional cost aggregation including M39 term at line 20 |
| `v11_cost_reg(i)` | 11 | `declarations.gms:10` | Regional total cost (mio. USD17MER/yr) |
| `q11_cost_glo` | 11 | `equations.gms:10` | Global cost = sum(i, v11_cost_reg(i)); objective function |
| `vm_cost_glo` | 11 | `declarations.gms:9` | Global total cost; MAgPIE **minimizes** this |

---

## 8. Key Distinctions

1. **Module 39 owns `vm_cost_landcon(j,land)`** — the economically meaningful conversion cost. Module 10 provides the land-change quantities that feed into it; Module 10 does NOT compute economic conversion costs.

2. **Module 10 owns `vm_cost_land_transition(j)`** — a 1 USD/ha numerical stabilization penalty on gross change. It enters Module 11 under a different term than Module 39's cost and serves a different purpose (preventing cycling artifacts, not representing economic conversion costs).

3. **Costs are by target land type only.** Converting forest to cropland costs the same as converting pasture to cropland: both are priced at the cropland establishment rate. The source land type does not affect conversion costs in the `calib` realization (`module_39.md` §10, "Does NOT vary costs by source land type").

4. **Calibration is cropland-only.** Pasture, forestry, and urban expansion use fixed global base costs with no regional variation and no reduction rewards (`presolve.gms:14-16`; `preloop.gms:9`).

5. **Module 11 is a pure aggregator** with no independent logic. It blindly sums `vm_cost_landcon(j,land)` over cells and land types into the regional total, which then enters the global objective function.

---

**Source:** 🟡 Based on `modules/module_39.md`, `modules/module_10.md`, `modules/module_11.md` documentation. Realization confirmed against `config/default.cfg` (`cfg$gms$landconversion <- "calib"`). Line numbers cited from documentation verified against GAMS code as of last verification dates (M39: 2025-10-13; M10: 2026-03-06; M11: 2026-05-16).
