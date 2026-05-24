# R24-Q4 Sonnet answer (Croparea infeasibility / cross-module)

📋 Loaded helper: `agent/helpers/debugging_infeasibility.md`

---

## Module 30 (`simple_apr24`): Infeasibility Conditions, Cross-Module Interface, and Debugging

### (a) Primary Constraint Equations in `simple_apr24`

The `simple_apr24` default realization declares **9 equations** total (`modules/module_30_notes.md`, warning 2). The ones that can directly produce or contribute to infeasibility are:

**1. `q30_rotation_max(j2,crpmax30,w)` — Maximum Rotational Share**
Location: `simple_apr24/equations.gms:34-36`

```gams
q30_rotation_max(j2,crpmax30,w) ..
  sum((crp_kcr30(crpmax30,kcr)), vm_area(j2,kcr,w)) =l=
    sum(kcr, vm_area(j2,kcr,w)) * f30_rotation_max_shr(crpmax30);
```

This is a hard `=l=` (less-than-or-equal) constraint per water supply type `w`. It prevents any crop-rotation group from exceeding a maximum fractional share of rainfed or irrigated area within a cluster. The active set `crpmax30` is populated in `presolve.gms:23` where `f30_rotation_max_shr < 1`. Unlike `detail_apr24`, there is no penalty fallback — violations are infeasible by construction.

**2. `q30_rotation_min(j2,crpmin30,w)` — Minimum Rotational Share**
Location: `simple_apr24/equations.gms:42-44`

```gams
q30_rotation_min(j2,crpmin30,w) ..
  sum((crp_kcr30(crpmin30,kcr)), vm_area(j2,kcr,w)) =g=
    sum(kcr, vm_area(j2,kcr,w)) * f30_rotation_min_shr(crpmin30);
```

A hard `=g=` (greater-than-or-equal) constraint, again per `w`. It mandates that specific crop-rotation groups occupy at least a minimum share. The active set `crpmin30` is populated where `f30_rotation_min_shr > 0` (`presolve.gms:24`). Share parameters come from static CSV input files `f30_rotation_max.csv` / `f30_rotation_min.csv` (`input.gms:80-95`).

A critical design difference from `detail_apr24`: in `simple_apr24`, the max and min constraints are applied **separately per `w`** (rainfed, irrigated), not summed across water types. This means a cluster can violate minimum diversity on the irrigated side independently of the rainfed side — and there is no penalty-based escape valve.

**3. `q30_betr_missing(j2)` — Bioenergy Tree Shortfall**
Location: `simple_apr24/equations.gms:21-23`

```gams
q30_betr_missing(j2)$(sum(ct, i30_betr_penalty(ct)) > 0) ..
  v30_betr_missing(j2) =g=
    vm_land(j2,"crop") * sum(ct, i30_betr_target(ct,j2)) - vm_area(j2,"betr","rainfed");
```

This is a soft constraint (the slack `v30_betr_missing` can be positive and is penalized), but it interacts with a hard structural risk: if `i30_betr_target` is set above 1.0, the constraint can never be satisfied and the model becomes infeasible or unbounded (`modules/module_30.md`, Conservation Law 4).

**4. `q29_avl_cropland(j2)` and `q29_cropland(j2)` — external but load-bearing**
The upper bound on all cropland area is not in Module 30 but in Module 29, which enforces `vm_land(j,"crop") =l= p29_avl_cropland(t,j)` (`modules/module_29.md`, equation `q29_avl_cropland:22-23`). Because `q30_rotation_min` requires minimum areas of specific crop groups out of total cropland, and total cropland is capped by Module 29, the two constraints can jointly become infeasible (see cross-module section below).

---

### Conditions Under Which `simple_apr24` Contributes to Infeasibility

There are four distinct infeasibility pathways:

**1. Rotation rule conflict (max < min for a crop group)**
If `f30_rotation_max_shr(crp30) < f30_rotation_min_shr(crp30)` for any group, the hard upper and lower bounds are simultaneously contradictory. The model cannot place the required minimum without exceeding the maximum. This is not automatically checked — it is a pure input-data consistency requirement (`modules/module_30.md`, Conservation Law 3).

**2. Per-`w` tightening under small irrigated area**
Because constraints are applied per water supply type, a cluster where irrigated area is very small (near zero) can violate `q30_rotation_min` for the irrigated dimension even when total cropland rotation is fine. In `detail_apr24`, the irrigated shortfall would trigger a penalty payment via `q30_rotation_max_irrig`; in `simple_apr24` with only hard constraints, there is no fallback (`modules/module_30.md`, Critical Implementation Note 1 and the `simple_apr24`-specific comparison table).

**3. Cropland expansion rate cap interacting with strict rotation floors**
When `s30_annual_max_growth` is set to a finite value, the growth constraint (`q30_crop_reg` + `presolve.gms` bound) limits how fast regional cropland can expand. If demand simultaneously pushes the model toward a new crop-mix composition that requires a proportionally larger area of some rotation group, the per-`w` floor from `q30_rotation_min` may become infeasible before the cropland ceiling can be raised enough to accommodate it.

**4. Bioenergy tree target > available area**
If `i30_betr_target(t,j)` evaluates above 1.0 — possible if `s30_betr_target` and/or `s30_betr_target_noselect` are set incorrectly — the `q30_betr_missing` right-hand side exceeds total cropland area. Since `vm_area(j,"betr","rainfed")` is bounded by total cropland, the inequality can never be satisfied. The penalty (`q30_cost`) would be unbounded, causing a numerical failure or infeasibility (`modules/module_30.md`, Conservation Law 4). The scenario is disabled before `s30_betr_scenario_start` via `v30_betr_missing.fx(j) = 0` (`presolve.gms:34-36`), but misconfigured start/target years can expose this.

---

### (b) Cross-Module Interface: What Module 30 Receives and Produces

**Module 30 receives from Module 10 (Land):**
- `vm_land(j2,"crop")` — total cropland area per cluster (mio. ha). Used in `q30_betr_missing` to calculate the absolute BETR target from the fractional target parameter (`modules/module_30.md`, interface variable section). Module 30 does NOT enforce the land balance itself; that identity is maintained by Module 10's equation `q10_land_area(j)`.

**Module 30 receives from Module 29 (Cropland) via the land balance, not directly:**
The direction is actually reversed: Module 29 aggregates `vm_area(j,kcr,w)` from Module 30 to compute `vm_land(j,"crop")`. In `simple_apr24`, Module 29's `q29_cropland` is:

```gams
q29_cropland(j2) ..
  vm_land(j2,"crop") =e= sum((kcr,w), vm_area(j2,kcr,w));
```
(`modules/module_29.md`, equations section 1, `simple_apr24` form). Module 29 then enforces `vm_land(j,"crop") =l= p29_avl_cropland(t,j)` via `q29_avl_cropland`. The combination creates the critical constraint chain:

```
Module 30 produces: vm_area(j,kcr,w)
  → Module 29 sums: vm_land(j,"crop") = Σ vm_area
  → Module 29 caps: vm_land(j,"crop") ≤ p29_avl_cropland(t,j)   [q29_avl_cropland]
  → Module 10 enforces: Σ_land vm_land(j,land) = pm_land_start(j) [q10_land_area, strict equality]
```

**Module 30 produces:**
- `vm_area(j,kcr,w)` — the primary output, crop area by cluster, crop type, and water supply (mio. ha). Consumed by 8+ downstream modules (17, 18, 38, 41, 42, 50, 53, 59) (`modules/module_30.md`, Interface Variables section).
- `vm_rotation_penalty(i)` — in `simple_apr24`, computed by `q30_cost` as the BETR shortfall penalty only (not rotation-rule violations, which have no penalty path in this realization). Enters Module 11's objective function.
- `vm_carbon_stock_croparea(j,ag_pools)` — computed by `q30_carbon`, consumed by Modules 52 and 56.

The critical asymmetry: Module 30's minimum rotational shares impose floors on `vm_area(j,kcr,w)`, while Module 29 imposes a ceiling on the sum. If the floor requirements sum to more than the ceiling (especially under tight `p29_avl_cropland` values or after Module 22 conservation area lock-in), the system is infeasible.

---

### (c) Documented Debugging Steps

Per `agent/helpers/debugging_infeasibility.md` and `modules/module_30.md` (Modification Safety / Common Issues):

**Step 1: Identify the failing timestep.**
Check `p80_modelstat(t)` in the output GDX. The first timestep with modelstat > 2 (and ≠ 7) is the point of failure. Module 30-related infeasibilities often appear in post-2025 timesteps when rotation scenarios begin phasing in (scenario fader starts at `s30_rotation_scenario_start = 2025`).

**Step 2: Check whether rotation constraints are binding.**
Rotation infeasibility from `q30_rotation_max` / `q30_rotation_min` in `simple_apr24` will show as a primal infeasibility (modelstat = 4 or 5), not a high slack cost. There are no rotation-specific slack variables in `simple_apr24`. Read marginals on rotation constraint equations to identify which crop group is causing the conflict.

**Step 3: Check land availability pressure.**
```r
land <- readGDX(gdx, "ov_land", select = list(type = "level"))
# Look for clusters where conservation + forestry + cropland exhausts cell area
```
If `p29_avl_cropland` is very tight in some clusters, the minimum share floors from `q30_rotation_min` may not be achievable even with full cropland allocation.

**Step 4: Switch to penalty-based mode as a diagnostic.**
Since `simple_apr24` has no switch to penalty-based rotation (unlike `detail_apr24` which has `s30_implementation`), the comparable diagnostic is to switch the realization entirely to `detail_apr24` with `s30_implementation = 0`. If this resolves the infeasibility, the hard bounds in `simple_apr24` are the cause, and the relevant rotation rules need relaxation via the input CSVs.

**Step 5: Disable rotation constraints temporarily.**
Set `c30_rotation_constraints = "off"` (`input.gms:24`; referenced in `modules/module_30.md`, `simple_apr24` description). This sets all `f30_rotation_max_shr` values to 1 and `f30_rotation_min_shr` to 0, effectively deactivating both `q30_rotation_max` and `q30_rotation_min`. If the run completes, rotation constraints in `simple_apr24` are the infeasibility source.

**Step 6: Verify BETR target feasibility.**
Confirm `s30_betr_target` and `s30_betr_target_noselect` produce `i30_betr_target(t,j) ≤ 1.0` for all clusters. If the penalty is active but the target is unachievable, the model will strain. Since BETR is penalized (not hard) in `simple_apr24`, this shows up as very high `vm_rotation_penalty` costs rather than primal infeasibility, but it can interact with other constraints to produce infeasibility.

**Step 7: Check configuration interactions (from dangerous configurations table).**
Module 30 infeasibility is often not isolated. Known dangerous combinations include:
- `c22_protect_scenario = "GSN_HalfEarth"` (Module 22 locks >50% land) combined with strict rotation floors — cropland is compressed so far that minimum shares become unreachable
- High `c60_2ndgen_biodem` (bioenergy demand) combined with tight rotation maxima on `betr` or `begr` groups
- `s30_annual_max_growth` at any finite value combined with tightening rotation scenarios that require rapid crop mix recomposition

---

### Source Statement

- 🟡 `modules/module_30.md` — primary source for all equation formulas, interface variables, algorithm logic, conservation laws, and common issues; `simple_apr24`-specific section last verified 2026-03-06
- 🟡 `modules/module_30_notes.md` — warning on realization-specific equation sets
- 🟡 `modules/module_29.md` — `q29_cropland` and `q29_avl_cropland` equations and Module 29/30 interface; realization-dependent form documented
- 🟡 `agent/helpers/debugging_infeasibility.md` — standard debugging workflow, dangerous configurations table, slack variable reference

**Caveat on line numbers**: The R3 audit warning in `modules/module_30.md` (line 14) flags that some file:line citations in that document point at `detail_apr24` rather than `simple_apr24`. Equations cited here from the `simple_apr24`-specific section (`equations.gms:25-27`, `:34-36`, `:42-44`) were verified in the 2026-03-06 session and are specific to the default realization. For critical modification work, verify against `../modules/30_croparea/simple_apr24/equations.gms` directly.
