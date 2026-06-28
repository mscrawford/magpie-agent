## Carbon Pool Partitioning in MAgPIE: M52 vs. M59, No Double-Counting

**Realizations described**: Module 52 `normal_dec17` (default), Module 59 `cellpool_jan23` (default).

---

### 1. The `c_pools` Set

🟢 **Verified**: `cross_module/carbon_balance_conservation.md:34-35`, citing `core/sets.gms:324-325`.

The `c_pools` set has exactly three elements:

| Element | Meaning | Timescale |
|---------|---------|-----------|
| `vegc` | Above-ground and below-ground live biomass | Years to centuries |
| `litc` | Dead plant material (leaf litter, residues, dead roots) | Years to decades |
| `soilc` | Soil organic matter in topsoil + subsoil | Decades to centuries |

There is also a structural **subset** called `ag_pools` = `{vegc, litc}` — the "above-ground pools." This subset appears explicitly in Module 52's parameter declarations (`pm_carbon_density_plantation_ac(t_all,j,ac,ag_pools)`, `pm_carbon_density_secdforest_ac`, `pm_carbon_density_other_ac`) and is the formal dividing line between what M52 covers and what M59 handles. 🟡 `module_52.md:449-451`.

---

### 2. `vm_carbon_stock` — Where It Lives

🟢 `vm_carbon_stock(j,land,c_pools,stockType)` is **declared in Module 56** (GHG Policy), not in M52 or M59:

> `modules/56_ghg_policy/price_aug22/declarations.gms:34`

It is a 4-dimensional interface variable (cell × land type × carbon pool × stock type). The `"actual"` slice of `stockType` is what equations normally use. `pcm_carbon_stock` (same dimensions) holds the previous timestep's realized values.

---

### 3. Who Populates Which Pool Slices

The key architectural rule: **Module 52 never writes to `vm_carbon_stock`.** M52 is a carbon-density data provider and emission calculator. The variable is populated by a clean split:

#### soilc — exclusively Module 59

🟢 Module 59 (`cellpool_jan23`) is the sole writer to the `soilc` slice of `vm_carbon_stock` for **all land types** via a single equation:

```gams
q59_carbon_soil(j2,land,stockType) ..
  vm_carbon_stock(j2, land, "soilc", stockType) =e=
    v59_som_pool(j2, land)
    + vm_land(j2, land) * sum(ct, i59_subsoilc_density(ct,j2));
```

`modules/59_som/cellpool_jan23/equations.gms:61-64`

- `v59_som_pool(j,land)` is the **dynamic topsoil** carbon pool, converging toward equilibrium via IPCC 2019 stock-change factors (15% annual convergence rate, `preloop.gms:45`).
- `vm_land(j,land) * i59_subsoilc_density(ct,j)` is the **static subsoil** reference, derived as `fm_carbon_density(t_all,j,"other","soilc") - f59_topsoilc_density(t_all,j)` (`preloop.gms:12`). It is not dynamically modeled.

Note: `fm_carbon_density` comes from Module 52 — M59 reads M52's LPJmL-derived density to compute the subsoil reference. M52 provides the ingredient; M59 assembles the soilc stock.

#### vegc and litc — land modules, using M52 densities

🟢 The `ag_pools` slices (`vegc`, `litc`) of `vm_carbon_stock` are populated by the five land modules, each owning its corresponding `land` slice: `module_52.md:424`.

| Land type | Populating module | Mechanism |
|-----------|------------------|-----------|
| `"crop"` | Module 29 (Cropland) via `q29_carbon` | Aggregates `vm_carbon_stock_croparea` from Module 30; `modules/29_cropland/detail_apr24/equations.gms:39` |
| `"past"` | Module 31 (Pasture) | Uses `fm_carbon_density(t,j,"past",ag_pools)` × area |
| `"forestry"` | Module 32 (Forestry) | Uses `pm_carbon_density_plantation_ac(t,j,ac,ag_pools)` × plantation area by age class |
| `"urban"` | Module 34 (Urban) | Fixes to zero: `vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0`; `modules/34_urban/exo_nov21/presolve.gms:8` |
| `"primforest"`, `"secdforest"`, `"other"` | Module 35 (NatVeg) | Uses `fm_carbon_density` (primforest), `pm_carbon_density_secdforest_ac` (secdforest), `pm_carbon_density_other_ac` (other) |

All these densities originate from Module 52 — either directly from the LPJmL input file `lpj_carbon_stocks.cs3` (via `fm_carbon_density(t_all,j,land,c_pools)`, `module_52.md:480-485`) or via Module 52's Chapman-Richards age-class growth curves (`start.gms:8-51`, potentially overwritten by bisection calibration in `preloop.gms:1-118` for secdforest and plantation `vegc` when `s52_growingstock_calib = 1`).

---

### 4. Why soilc Has No Age-Class Growth in Module 52

🟢 This is explicit in the documentation: `module_52.md:163-164`.

> "Despite being named `m_growth_litc_soilc`, this macro is applied **only to litter carbon (litc)** in Module 52 (start.gms:20,31,51). Soil carbon (`soilc`) has **no age-class growth function** in Module 52 — it is read directly from LPJmL static input data and is not age-class-specific."

This is why the age-class parameters are dimensioned over `ag_pools` (not `c_pools`): `pm_carbon_density_plantation_ac(t_all,j,ac,ag_pools)`. The `soilc` pool is deliberately absent from those parameters because M59 owns all soil dynamics.

---

### 5. How the Pools Aggregate in the Emission Equation

🟢 Module 52's single optimization-phase equation, `q52_emis_co2_actual` (`equations.gms:16-19`), reads the fully assembled `vm_carbon_stock` — all three pool slices now populated — and computes CO₂ flux:

```gams
q52_emis_co2_actual(i2,emis_oneoff) ..
  vm_emissions_reg(i2,emis_oneoff,"co2_c") =e=
    sum((cell(i2,j2), emis_land(emis_oneoff,land,c_pools)),
      (pcm_carbon_stock(j2,land,c_pools,"actual")
       - vm_carbon_stock(j2,land,c_pools,"actual"))
      / m_timestep_length
    );
```

The `emis_land(emis_oneoff,land,c_pools)` mapping indexes 21 distinct emission sources — the full cross-product of 7 land types × 3 pools (`core/sets.gms:314-318,332-335`). This means soil-carbon changes (e.g., `crop_soilc`) flow into `vm_emissions_reg` via M59's `q59_carbon_soil` populating the soilc slice, while vegetation and litter changes (e.g., `primforest_vegc`, `secdforest_litc`) flow in via the land modules' ag_pools equations.

There is no summation that would mix pools from different equations — the set membership structure enforces the partition.

---

### 6. The `pcm_carbon_stock` Carry-Forward: Split Ownership Mirrors Split Write Ownership

🟢 After each timestep solve, both `pcm_carbon_stock` entries are updated in postsolve — but by different modules, mirroring who owns the write during the solve itself: `module_52.md:430-432`, `module_59.md:174-178`.

| Pool subset | Carry-forward location |
|-------------|----------------------|
| `ag_pools` (vegc + litc) | Module 56 `postsolve.gms:8` |
| `soilc` | Module 59 `cellpool_jan23/postsolve.gms:13` (added in develop commit 931db85c4, 2026-06-25) |

Before that commit, the soilc carry-forward was absent; `pcm_carbon_stock(...,"soilc",...)` was never updated between timesteps, making the soilc term in `q52_emis_co2_actual` compute a cumulative-since-initialization flux rather than a per-timestep one. Default runs were unaffected because the default `c56_emis_policy = reddnatveg_nosoil` (`config/default.cfg:1810`) excludes the soilc pool from carbon pricing.

---

### 7. Double-Counting Prevention Architecture

The partition is enforced by three complementary mechanisms:

1. **Set-dimension constraint**: M52's age-class parameters are typed over `ag_pools`, not `c_pools`. The GAMS type system physically prevents M52 from assigning soilc values in those parameters.

2. **Equation exclusivity**: `q59_carbon_soil` is the only equation that appears on the left-hand side of an equality for `vm_carbon_stock(j,land,"soilc",...)`. No land module or M52 equation touches the soilc dimension.

3. **M52 reads, never writes `vm_carbon_stock`**: M52 only consumes `vm_carbon_stock` in `q52_emis_co2_actual`. The only variable M52 writes is `vm_emissions_reg`. `module_52.md:413-431`.

---

### Summary Schematic

```
                    POPULATES vm_carbon_stock(j,land,pool,type)
  ┌──────────┬─────────────────────────────────────────────────────┐
  │ c_pools  │ Who writes the LHS                                   │
  ├──────────┼─────────────────────────────────────────────────────┤
  │ vegc     │ M29 (crop), M31 (past), M32 (forestry),             │
  │ litc     │ M34 (urban=0), M35 (primf/secdf/other)              │
  │          │ using fm_carbon_density / pm_carbon_density_*_ac    │
  │          │ from Module 52 as density inputs                    │
  ├──────────┼─────────────────────────────────────────────────────┤
  │ soilc    │ Module 59 exclusively (q59_carbon_soil:61-64)       │
  │          │ = v59_som_pool + vm_land × i59_subsoilc_density     │
  └──────────┴─────────────────────────────────────────────────────┘

  Module 52 (normal_dec17): reads all three pools via q52_emis_co2_actual
  → outputs vm_emissions_reg(i,emis_oneoff,"co2_c")
  Module 52 does NOT write vm_carbon_stock at any point.
```

---

**Source statement:**

🟡 Based on `modules/module_52.md` (post-2026-04-20 update for calibration system), `modules/module_59.md` (verified 2026-03-06), and `cross_module/carbon_balance_conservation.md`.
🟢 Key claims verified in-session via module doc text with line-number cross-references to GAMS source.
📘 Consulted `module_56.md` for `vm_carbon_stock` declaration location and `q56_emis_pricing_co2` structure.
