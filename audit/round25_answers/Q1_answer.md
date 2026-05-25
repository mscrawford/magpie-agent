# R25-Q1: Rotational Constraints in Module 30 (Default Configuration)

## Active Realization

The default realization is **`simple_apr24`**, as set in `config/default.cfg`:
`cfg$gms$croparea <- "simple_apr24"` 🟡 (module_30.md, header block)

The alternative realization is `detail_apr24`.

---

## Rotational Constraints in `simple_apr24` (Default)

`simple_apr24` implements rotational constraints as **hard bounds only** — there is no penalty-based variant and no `i30_implementation` toggle in this realization. The constraints can be disabled entirely via the compile-time switch `c30_rotation_constraints` (set to `"off"` zeroes out all shares). 🟡 (module_30.md §10)

### On/Off Switch

`c30_rotation_constraints` (`input.gms:24`) — compile-time global, options: `"on"` / `"off"`. When `"off"`, `f30_rotation_max_shr` is set to 1 and `f30_rotation_min_shr` is set to 0, making all constraints non-binding. The default configuration uses `"on"`. 🟡 (module_30.md §10)

### Equations

#### q30_rotation_max — Maximum Rotational Share
**File:line**: `simple_apr24/equations.gms:34-36` 🟡 (module_30.md §10)

```gams
q30_rotation_max(j2,crpmax30,w) ..
  sum((crp_kcr30(crpmax30,kcr)), vm_area(j2,kcr,w)) =l=
    sum(kcr, vm_area(j2,kcr,w)) * f30_rotation_max_shr(crpmax30);
```

**Mechanism**: For each cell `j2`, each binding crop-rotation group `crpmax30`, and each water supply type `w` independently, the total area of crops belonging to that group cannot exceed the total cropland of that water type multiplied by the maximum allowed share `f30_rotation_max_shr(crpmax30)`. The shares are read statically from `input/f30_rotation_max.csv` (`input.gms:80-85`). 🟡 (module_30.md §10)

The active set `crpmax30` is populated in `presolve.gms:23` to include only crop-rotation types where `f30_rotation_max_shr < 1` (i.e., only genuinely binding upper limits). 🟡 (module_30.md §10)

#### q30_rotation_min — Minimum Rotational Share
**File:line**: `simple_apr24/equations.gms:42-44` 🟡 (module_30.md §10)

```gams
q30_rotation_min(j2,crpmin30,w) ..
  sum((crp_kcr30(crpmin30,kcr)), vm_area(j2,kcr,w)) =g=
    sum(kcr, vm_area(j2,kcr,w)) * f30_rotation_min_shr(crpmin30);
```

**Mechanism**: The mirror constraint — the area of crops in group `crpmin30` must be at least the total cropland of that water type times the minimum required share `f30_rotation_min_shr(crpmin30)` from `input/f30_rotation_min.csv` (`input.gms:89-94`). 🟡 (module_30.md §10)

The active set `crpmin30` is populated in `presolve.gms:24` to include only groups where `f30_rotation_min_shr > 0`. 🟡 (module_30.md §10)

**Crop-group mapping**: The mapping `crp_kcr30(crp30,kcr)` links 20 crop-rotation types to the 19 MAgPIE crops (`sets.gms:18-37`). 🟡 (module_30.md §10)

### Key structural feature: constraint is per water type (`w`)

Both `q30_rotation_max` and `q30_rotation_min` in `simple_apr24` carry the `w` dimension explicitly — rainfed and irrigated area portfolios are constrained **independently**. 🟡 (module_30.md §10)

---

## How `detail_apr24` Differs in Mechanism

`detail_apr24` differs in four mechanistic respects, not merely in file name: 🟡 (module_30.md §§3-5, table in §10)

1. **Dual implementation modes.** `detail_apr24` switches between rule-based (hard `=l=`/`=g=` constraints, active when `i30_implementation = 1`) and penalty-based (soft constraints that calculate a violation amount and price it, active when `i30_implementation = 0`). `simple_apr24` has no such toggle — it is always hard-bound.

2. **Penalty-based variant uses different equation bodies.** In penalty mode, `q30_rotation_max2` and `q30_rotation_min2` compute a surplus/shortfall variable `v30_penalty(j2,rota30)` (declared positive, so it clips at zero when the constraint is satisfied). That variable is priced via `q30_rotation_penalty`, which aggregates region-level costs into `vm_rotation_penalty(i2)` and enters Module 11's objective. In `simple_apr24`, `vm_rotation_penalty` carries only the BETR shortfall penalty (`q30_cost`, `simple_apr24/equations.gms:25-27`); there is no rotation-violation pricing at all.

3. **Larger and different crop-group sets.** `detail_apr24` uses `rotamax30` (30 maximum groups) and `rotamin30` (6 minimum groups), driven by time-varying parameter `i30_rotation_rules(ct,rota30)` that fades between a "default" and a user-selected scenario over 2025-2050. `simple_apr24` uses `crpmax30`/`crpmin30` subsets of a 20-type `crp30` set with static shares from CSV files; there is no within-horizon scenario fading of the shares themselves.

4. **Water dimension aggregation.** `detail_apr24` sums over `w` inside its constraints (total area regardless of water source). `simple_apr24` keeps `w` as an explicit index, enforcing separate max/min shares for rainfed and irrigated portfolios.

5. **Irrigated-area-specific constraint.** `detail_apr24` adds `q30_rotation_max_irrig`, which constrains the irrigated sub-portfolio against `vm_AEI(j2)` (area equipped for irrigation) via penalty regardless of the overall implementation mode. `simple_apr24` has no equivalent equation — its per-`w` structure of `q30_rotation_max`/`min` is the sole mechanism covering irrigated area. 🟡 (module_30.md §5)

---

## Summary Table

| Feature | simple_apr24 (DEFAULT) | detail_apr24 (alternative) |
|---|---|---|
| Hard constraints | `q30_rotation_max` (L34-36), `q30_rotation_min` (L42-44) | `q30_rotation_max` (L36-38), `q30_rotation_min` (L40-42) when `i30_implementation=1` |
| Penalty mode | None | `q30_rotation_max2`, `q30_rotation_min2`, `q30_rotation_penalty` when `i30_implementation=0` |
| Crop-group count | 20 types (`crp30`) with static shares | 30 max + 6 min groups (`rota30`) with time-varying scenario fader |
| Water dimension | Per `w` (rainfed and irrigated separately) | Summed over `w` |
| Irrigated-specific constraint | Not present | `q30_rotation_max_irrig` (always penalty-based) |
| Switch | `c30_rotation_constraints` (compile-time on/off) | `s30_implementation` (0/1, runtime) |

---

Based on **module_30.md** documentation (R6 Phase 2 sweep, 2026-05-25 verified), §§3-5, §§9-10, header block, and comparison table.
