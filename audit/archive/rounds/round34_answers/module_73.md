# Module 73 (Timber) — Production Mechanics and Cross-Module Interactions

**Source**: `magpie-agent/modules/module_73.md` (verified 2026-04-20 against MAgPIE PR #869/#872)

---

## Default Realization

Module 73 has exactly **one realization**: `default` (`modules/73_timber/default/`). There is no alternative realization to select.

---

## Production Aggregation: q73_prod_wood and q73_prod_woodfuel

Module 73's central job is to aggregate cell-level timber production from two physical sources — managed plantations (Module 32) and natural vegetation (Module 35) — into the model's unified production variable `vm_prod`. It does this via two balance equations in `equations.gms`.

### q73_prod_wood (equations.gms:35-42)

Populates `vm_prod(j2, "wood")` — industrial roundwood:

```gams
q73_prod_wood(j2)..
  vm_prod(j2,"wood")
  =e=
  vm_prod_forestry(j2,"wood")
  + sum((land_natveg), vm_prod_natveg(j2,land_natveg,"wood"))
  + v73_prod_heaven_timber(j2,"wood");
```

Three terms:
1. `vm_prod_forestry(j,"wood")` — plantation harvest from Module 32
2. `sum(land_natveg, vm_prod_natveg(j,land_natveg,"wood"))` — natural forest harvest from Module 35, summed over natural vegetation land classes
3. `v73_prod_heaven_timber(j,"wood")` — emergency slack variable (cost 1,000,000 USD17MER/tDM) that activates only when real supply cannot meet demand

### q73_prod_woodfuel (equations.gms:44-53)

Populates `vm_prod(j2, "woodfuel")` — wood energy:

```gams
q73_prod_woodfuel(j2)..
  vm_prod(j2,"woodfuel")
  =e=
  vm_prod_forestry(j2,"woodfuel")
  + sum((land_natveg), vm_prod_natveg(j2,land_natveg,"woodfuel"))
  + v73_prod_residues(j2)
  + v73_prod_heaven_timber(j2,"woodfuel");
```

Identical structure to `q73_prod_wood` plus a **fourth term**:
- `v73_prod_residues(j)` — logging residues (branches, tops) from industrial roundwood harvest, recoverable as woodfuel

The residue term is woodfuel-only because residues represent low-value biomass unsuitable for industrial roundwood markets.

### The residue constraint: q73_prod_residues (equations.gms:72-79)

Caps residue recovery at 15% of all real timber harvest (plantations + natveg, both wood + woodfuel categories):

```
v73_prod_residues(j) =l= (sum_forestry + sum_natveg) × s73_residue_ratio
```

The 15% parameter (`s73_residue_ratio = 0.15`, `input.gms:20`) reflects ~30% theoretical residue potential (Oswalt et al. 2019) × ~52% technical recovery rate (Thiffault et al. 2015). The slack variable `v73_prod_heaven_timber` is deliberately excluded from the residue base — phantom harvest cannot generate real residues.

---

## vm_prod Members Populated

Module 73's two balance equations together populate both `kforestry` members of `vm_prod`:

| vm_prod member | Populated by | Equation |
|---|---|---|
| `vm_prod(j, "wood")` | q73_prod_wood | equations.gms:35-42 |
| `vm_prod(j, "woodfuel")` | vm_prod(j, "woodfuel") | equations.gms:44-53 |

These map to the FAO categories via the set mapping `kforestry_to_woodprod`: `wood . (industrial_roundwood)` and `woodfuel . (wood_fuel)` (`sets.gms:37-41`).

---

## Interaction with Module 32 (Forestry)

The relationship is bidirectional:

**M32 → M73 (production supply):**
- Module 32 provides `vm_prod_forestry(j, kforestry)` — the plantation harvest component consumed by both q73_prod_wood and q73_prod_woodfuel

**M73 → M32 (demand signal):**
- Module 73 pre-computes `pm_demand_forestry(t, i, kforestry)` in `preloop.gms` using a GDP/population demand equation (Lauri et al. 2019 methodology, income elasticities from Morland et al. 2018)
- Module 32 reads `pm_demand_forestry` in its presolve to drive plantation establishment and harvest scheduling (`dynamic_may24/presolve.gms:186`)
- Module 73 also computes `im_timber_prod_cost(i, kforestry)` (regional base cost, USD17MER/tDM, derived from UNECE price scalars converted by Module 52's regional wood density `im_vol_conv(i)`). Module 32 uses this in `q32_cost_establishment`.

The demand projection applies income-elastic growth with a saturation threshold: when per-capita GDP exceeds `s73_income_threshold = 10,000 USD17PPP/cap/yr`, income elasticity is set to zero (demand saturates). Woodfuel has a negative elasticity (decreases with income) that remains active regardless of the threshold.

---

## Interaction with Natural Vegetation (Module 35)

Module 35 provides `vm_prod_natveg(j, land_natveg, kforestry)` — harvest from primary forests, secondary forests, and other natural vegetation classes. Module 73 consumes this in both balance equations via `sum(land_natveg, vm_prod_natveg(...))`.

Unlike the M32 relationship, Module 73 does not send a demand signal back to Module 35 directly. Natural vegetation harvest is governed by Module 35's own sustainable harvest constraints. Module 73 simply aggregates what Module 35 makes available.

Natural-vegetation timber carries a **cost premium** relative to plantation timber. The cost equation `q73_cost_timber` (`equations.gms:16-27`) charges natveg harvest at `im_timber_prod_cost(i, kforestry) × (1 + s73_natveg_cost_premium)` where `s73_natveg_cost_premium = 0.15` (`input.gms:23`) — a 15% premium reflecting heterogeneous species mix and variable dimensions (expert estimate).

---

## Full Equation Set (Module 73 has 4 equations)

| Equation | Location | Purpose |
|---|---|---|
| `q73_cost_timber` | equations.gms:16-27 | Regional timber production cost (4 components: base, natveg premium, residue removal, slack) |
| `q73_prod_wood` | equations.gms:35-42 | Balance: vm_prod "wood" = plantation + natveg + slack |
| `q73_prod_woodfuel` | equations.gms:44-53 | Balance: vm_prod "woodfuel" = plantation + natveg + residues + slack |
| `q73_prod_residues` | equations.gms:72-79 | Inequality: residues =l= 15% of all real harvest |

---

## Key Parameters at Default Values

| Parameter | Default | Unit | Note |
|---|---|---|---|
| `s73_residue_ratio` | 0.15 | fraction | Residue ceiling relative to total real harvest |
| `s73_residue_removal_cost` | 2.7 | USD17MER/tDM | Residue collection cost |
| `s73_timber_prod_cost_wood` | 89 | USD17MER/m3 | Converted to per-tDM via im_vol_conv(i) |
| `s73_timber_prod_cost_woodfuel` | 44 | USD17MER/m3 | Half of roundwood price |
| `s73_natveg_cost_premium` | 0.15 | fraction | Natveg cost surcharge over plantation |
| `s73_free_prod_cost` | 1,000,000 | USD17MER/tDM | Emergency slack — prohibitive |
| `s73_income_threshold` | 10,000 | USD17PPP/cap/yr | GDP saturation threshold |
| `s73_woodfuel_stacking_factor` | 0.65 | solid m3/stere | FAO stacked-m3 to solid-m3 correction |
| `s73_timber_demand_switch` | 1 | 1/0 | Turn entire timber demand on/off |

---

## Epistemic Status

All claims above are sourced from:

- **Source**: `magpie-agent/modules/module_73.md` — 🟡 Documented (AI documentation, verified against GAMS source 2026-04-20 following MAgPIE PRs #869 and #872).

Line numbers for GAMS equations (`equations.gms:35-42`, `:44-53`, `:16-27`, `:72-79`) are as recorded in documentation at sync date. Line numbers may drift if subsequent commits have been merged since the last `/sync`. For critical code-modification work, verify directly against `../modules/73_timber/default/equations.gms`.
