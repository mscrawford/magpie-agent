# Round 30 Answer: Nitrogen Balance (M50 -> M51, SOM from M59) and Food Supply=Demand Constraint

**Question**: Trace the nitrogen balance from the cropland soil-N budget (module 50) to nitrogen emissions (module 51), including the SOM contribution (module 59). Separately, which equation enforces food supply equals demand, and across which modules?

**Sources consulted**:
- `cross_module/nitrogen_food_balance.md`
- `modules/module_50.md` (realization: `macceff_aug22`)
- `modules/module_51.md` (realization: `rescaled_jan21`)
- `modules/module_59.md` (realization: `cellpool_jan23`)
- `modules/module_21.md` (realization: `selfsuff_reduced`)

---

## Part 1: Nitrogen Balance Trace (M50 -> M51, with M59 SOM contribution)

### Overview of the flow

Module 50 is the soil nitrogen budget calculator. It does NOT emit nitrogen — it calculates how much nitrogen enters and leaves agricultural soils, and produces two interface variables that Module 51 uses to back-calculate losses and emissions. Module 59 contributes to both sides of this: it releases nitrogen from SOM decomposition, which enters Module 50 as a fertilizer input AND enters Module 51 directly as an emissions source.

The chain is:

```
M59 (SOM dynamics)
  |-- vm_nr_som_fertilizer(j) --> M50 nitrogen inputs (q50_nr_inputs)
  |-- vm_nr_som(j)             --> M51 emissions (q51_emissions_som)

M50 (soil N budget)
  |-- vm_nr_eff(i)             --> M51 NUE rescaling in ALL crop-side equations
  |-- vm_nr_eff_pasture(i)     --> M51 NUE rescaling in pasture equations
  |-- vm_nr_inorg_fert_reg(i,land_ag) --> M51 inorganic-fertilizer emission source
```

---

### Step 1: Module 59 calculates SOM nitrogen release

**Realization**: `cellpool_jan23`

Module 59 tracks topsoil carbon pools using IPCC 2019 stock change factors. When land converts to cropland, the existing soil organic matter decomposes, releasing nitrogen. The core equation is `q59_nr_som` (`modules/59_som/cellpool_jan23/equations.gms:69-75`):

```gams
q59_nr_som(j2) ..
  vm_nr_som(j2) =e=
    sum(ct,i59_lossrate(ct))/m_timestep_length * 1/15
    * (sum((ct,land_from), p59_carbon_density(ct,j2,land_from) *
           vm_lu_transitions(j2,land_from,"crop"))
       - v59_som_target(j2,"crop"));
```

Key points:
- **Variable**: `vm_nr_som(j)` is a free variable (can be positive = N release, or negative = N sink when cropland is abandoned)
- **C:N ratio**: Fixed at 15:1 (`equations.gms:76`). All carbon-to-nitrogen conversion uses this single global ratio
- **Convergence**: The 15% annual convergence rate `i59_lossrate(t) = 1 - 0.85^m_yeardiff(t)` governs how fast SOM approaches equilibrium

Module 59 then splits this nitrogen release into two sub-flows:

1. **`vm_nr_som_fertilizer(j)`**: The plant-available fraction, constrained by two inequalities:
   - `q59_nr_som_fertilizer`: `vm_nr_som_fertilizer(j) =l= vm_nr_som(j)` — cannot exceed total SOM N release
   - `q59_nr_som_fertilizer2`: `vm_nr_som_fertilizer(j) =l= vm_landexpansion(j,"crop") * s59_nitrogen_uptake` — additionally limited by crop uptake capacity on newly expanded land (default `s59_nitrogen_uptake = 200 kg N/ha`)

2. **`vm_nr_som(j)` itself** (the total release): passed directly to Module 51 for emissions

---

### Step 2: Module 50 assembles the soil nitrogen budget

**Realization**: `macceff_aug22`

Module 50's central constraint is `q50_nr_bal_crp` (`equations.gms:14-16`):

```gams
q50_nr_bal_crp(i2) ..
    vm_nr_eff(i2) * v50_nr_inputs(i2)
    =g= sum(kcr,v50_nr_withdrawals(i2,kcr));
```

This says: SNUpE (soil nitrogen uptake efficiency) times total nitrogen inputs must be at least as large as crop nitrogen withdrawals. The optimizer chooses `vm_nr_inorg_fert_reg` (inorganic fertilizer, the main free variable) to satisfy this at minimum cost.

The full nitrogen inputs equation is `q50_nr_inputs` (`equations.gms:22-32`):

```gams
q50_nr_inputs(i2) ..
    v50_nr_inputs(i2) =e=
    vm_res_recycling(i2,"nr")          -- residues (M18)
    + area * f50_nr_fix_area(kcr)      -- biological N fixation
    + vm_fallow(j2) * fixation_rate    -- fallow fixation
    + vm_manure_recycling(i2,"nr")     -- recycled manure (M55)
    + vm_manure(i2,kli,"stubble_grazing","nr") -- stubble-grazing manure (M55)
    + vm_nr_inorg_fert_reg(i2,"crop")  -- inorganic fertilizer [endogenous]
    + sum(cell(i2,j2), vm_nr_som_fertilizer(j2)) -- SOM N contribution [from M59]
    + f50_nitrogen_balanceflow(ct,i2)  -- calibration balance flow
    + v50_nr_deposition(i2,"crop");    -- atmospheric deposition
```

The SOM fertilizer contribution (`vm_nr_som_fertilizer`) from M59 appears in line 30 of this equation. It acts as a substitute for inorganic fertilizer: when SOM releases nitrogen on newly converted land, the model needs less `vm_nr_inorg_fert_reg` to meet the efficiency constraint.

**Nitrogen surplus** (`q50_nr_surplus`, `equations.gms:46-49`):

```gams
v50_nr_surplus_cropland(i2) =e= v50_nr_inputs(i2) - sum(kcr, v50_nr_withdrawals(i2,kcr));
```

This surplus (inputs minus withdrawals) is the nitrogen that was applied but not taken up by crops. It feeds the environment through the pathways Module 51 calculates.

**NUE is NOT optimized**: `vm_nr_eff` and `vm_nr_eff_pasture` are FIXED in presolve (`presolve.gms:76-77`) based on scenario trajectories and MACC curves from Module 57. They are positive variables technically, but scenario inputs in practice.

---

### Step 3: Module 51 calculates nitrogen emissions using M50's NUE parameters and M59's SOM release

**Realization**: `rescaled_jan21`

Module 51 receives three things from M50 and one from M59:
- `vm_nr_eff(i)` — cropland SNUpE (fixed)
- `vm_nr_eff_pasture(i)` — pasture NUE (fixed)
- `vm_nr_inorg_fert_reg(i,"crop")` and `vm_nr_inorg_fert_reg(i,"past")` — fertilizer amounts
- `vm_nr_som(j)` — total SOM nitrogen release (from M59, NOT the fertilizer fraction)

The **NUE rescaling formula** is the core methodological innovation of M51. It adjusts IPCC 2006 emission factors (which implicitly assume 50% NUE, `s51_snupe_base = 0.5`) to match the model's actual NUE. The general form, applied across 5 of 8 equations:

```
Emissions = N_input / (1 - s51_snupe_base) * (1 - vm_nr_eff) * EF
          = N_input * [(1 - vm_nr_eff) / (1 - 0.5)] * EF
```

This rescaling factor `(1 - vm_nr_eff) / (1 - 0.5)` adjusts downward when actual NUE exceeds IPCC's assumed 50%: higher NUE leaves less nitrogen available for loss.

**The SOM-specific emission equation** is `q51_emissions_som` (`equations.gms:55-59`):

```gams
q51_emissions_som(i2,n_pollutants_direct) ..
  vm_emissions_reg(i2,"som",n_pollutants_direct) =e=
  sum(cell(i2,j2),vm_nr_som(j2))           -- cell-level SOM N release aggregated to region
  * sum(ct, i51_ef_n_soil(ct,i2,n_pollutants_direct,"som"))
  / (1-s51_snupe_base) * (1-vm_nr_eff(i2));  -- NUE rescaling applied
```

Note: `vm_nr_som(j)` — the TOTAL SOM nitrogen release from M59 — is what feeds M51, not the plant-available fraction `vm_nr_som_fertilizer`. The emissions calculation uses the total nitrogen entering the "SOM decomposition" pool, not just what crops absorb. This is correct: the remainder of `vm_nr_som` that is not `vm_nr_som_fertilizer` is precisely the nitrogen lost through emissions and leaching pathways.

**All 8 equations in M51 by source**:

| Equation | Source | NUE Rescaled? | Key M59/M50 variable |
|----------|--------|---------------|----------------------|
| `q51_emissions_man_crop` | Manure on cropland | Yes (crop NUE) | `vm_nr_eff` from M50 |
| `q51_emissions_inorg_fert` | Inorganic fertilizer | Yes (crop+pasture NUE) | `vm_nr_inorg_fert_reg` from M50 + both NUEs |
| `q51_emissions_resid` | Residue decay | Yes (crop NUE) | `vm_nr_eff` from M50 |
| `q51_emissions_resid_burn` | Residue burning | No | (not NUE-related) |
| `q51_emissions_som` | SOM loss | Yes (crop NUE) | `vm_nr_som` from M59 + `vm_nr_eff` from M50 |
| `q51_emissionbal_awms` | Confined manure | No (MACC instead) | `im_maccs_mitigation` from M57 |
| `q51_emissionbal_man_past` | Pasture manure | Yes (pasture NUE) | `vm_nr_eff_pasture` from M50 |
| `q51_emissions_indirect_n2o` | Indirect N2O | No (derived) | Own outputs (NH3, NOx, NO3) |

The pollutants tracked across all sources are: `n2o_n_direct`, `nh3_n`, `no2_n`, `no3_n` (direct) and `n2o_n_indirect` (via equation 8). Emissions go to Module 56 (GHG Policy) via `vm_emissions_reg(i,emis_source,pollutants)`.

---

### SOM contribution: the two-pathway split

M59's nitrogen release participates in two separate accounting pathways simultaneously:

1. **Fertilizer pathway**: `vm_nr_som_fertilizer(j)` enters M50's `q50_nr_inputs`, reducing the inorganic fertilizer demand required by the SNUpE constraint. This represents the nitrogen crops can actually absorb from freshly decomposing SOM.

2. **Emissions pathway**: `vm_nr_som(j)` (the total, not just the plant-available fraction) enters M51's `q51_emissions_som`, where the NUE rescaling formula distributes it across N2O, NH3, NOx, and NO3 pathways. This represents the nitrogen that leaves the SOM pool but is NOT taken up by crops — it becomes a loss to air and water.

The difference `vm_nr_som - vm_nr_som_fertilizer` is the SOM nitrogen that goes to emissions rather than plant uptake.

---

### What the nitrogen balance IS and IS NOT

The nitrogen balance in MAgPIE is an accounting framework, NOT a strict conservation law. Key characteristics:

- M50's `q50_nr_bal_crp` enforces `SNUpE * inputs >= withdrawals` (inequality, not equality)
- There is no single equation that closes the N budget to zero — nitrogen enters via fertilizer (endogenous), exits via harvest and emissions (to atmosphere/water), and these are tracked but not constrained to balance
- The surplus `v50_nr_surplus_cropland` can accumulate indefinitely; M50 has no "soil N stock" that builds up and constrains future withdrawals
- The C:N ratio of 15:1 in M59 is a fixed global parameter, not calibrated to soil type or region

---

## Part 2: Food Supply = Demand — Which Equation, Which Modules?

### The enforcing equation

Food supply equals demand is enforced primarily by `q21_trade_glo` in **Module 21** (`selfsuff_reduced` realization), at the GLOBAL level (`modules/21_trade/selfsuff_reduced/equations.gms:12-14`):

```gams
q21_trade_glo(k_trade)..
  sum(i2, vm_prod_reg(i2,k_trade)) =g=
  sum(i2, vm_supply(i2,k_trade)) + sum(ct,f21_trade_balanceflow(ct,k_trade));
```

**Meaning**: Summed across all regions, total production of each tradeable commodity must be >= total supply requirements plus a historical balance flow correction term.

The balance flow `f21_trade_balanceflow(ct,k_trade)` is a residual calibration term that reproduces observed FAO trade in the base year; it is near zero outside the calibration period.

For non-tradeable commodities (pasture, fodder, residues, bioenergy), the analogous constraint is `q21_notrade` at the superregional level (`equations.gms:18-19`):

```gams
q21_notrade(h2,k_notrade)..
  sum(supreg(h2,i2),vm_prod_reg(i2,k_notrade)) =g= sum(supreg(h2,i2), vm_supply(i2,k_notrade));
```

### The three modules involved

**Module 16 (demand)** calculates `vm_supply(i,k)`:
- Aggregates food, feed, processing, material, seed, and waste demand streams
- Food waste is modeled via `v16_dem_waste(i,kall)` using `q16_waste_demand` with `f16_waste_shr` waste shares
- `vm_supply` is the right-hand side of the food balance constraint in M21

**Module 17 (production)** produces `vm_prod_reg(i,k)`:
- Aggregates from cell-level: `vm_prod_reg(i,k) = sum(cell(i,j), vm_prod(j,k))`
- This is the left-hand side of the food balance constraint in M21

**Module 21 (trade)** enforces the balance:
- `q21_trade_glo`: globally for tradeables (`k_trade`, 38 commodities)
- `q21_notrade`: superregionally for non-tradeables (`k_notrade`, 8 commodities)
- Regional self-sufficiency requirements are enforced by `q21_trade_reg`, which sets lower bounds on regional production
- The `v21_import_for_feasibility` slack variable prevents hard infeasibility when trade constraints bind

### Important nuances

- The constraint is `=g=` (greater-than-or-equal), not `=e=` (equality). Production can exceed demand (surplus is allowed but costly to produce)
- "Supply" in MAgPIE terminology (`vm_supply`) means total demand from all end uses, not physical supply. The equation reads: production >= demand
- Trade rebalances production and consumption, but the global production constraint is the hard enforcement point
- If the constraint binds with no slack, the solver's shadow price on `q21_trade_glo` is the model's implicit food price

---

## Summary

**Nitrogen trace (M50 -> M51, with M59)**:

1. M59 calculates SOM N release `vm_nr_som(j)` via `q59_nr_som` (C:N = 15, IPCC 2019 convergence)
2. M59 splits this into plant-available `vm_nr_som_fertilizer(j)` (constrained by `q59_nr_som_fertilizer` + `q59_nr_som_fertilizer2`) and total release `vm_nr_som(j)`
3. M50 receives `vm_nr_som_fertilizer` as one of 8 nitrogen input sources in `q50_nr_inputs`; it optimizes `vm_nr_inorg_fert_reg` to satisfy the SNUpE efficiency constraint `q50_nr_bal_crp`
4. M50 exports fixed NUE parameters `vm_nr_eff` and `vm_nr_eff_pasture` (set in presolve from scenario + MACC) and `vm_nr_inorg_fert_reg` to M51
5. M51 receives `vm_nr_som(j)` from M59 and all M50 interface variables; it applies NUE rescaling across 7 emission equations (equations 1-7), computing N2O, NH3, NOx, NO3 for each N source; equation 8 derives indirect N2O from the direct emission outputs
6. All `vm_emissions_reg(i,emis_source,pollutants)` pass to Module 56 (GHG Policy)

**Food supply = demand**:

- Enforced by `q21_trade_glo` in Module 21 (`selfsuff_reduced/equations.gms:12-14`): global production (`vm_prod_reg` from M17) >= global supply (`vm_supply` from M16) for tradeables
- For non-tradeables: `q21_notrade` at superregional level
- The constraint is an inequality (>=); global trade acts as the balancing mechanism

---

## Epistemic Hierarchy

All claims in this answer are based on documentation read in this session:

- 🟡 **Documented**: `cross_module/nitrogen_food_balance.md`, `modules/module_50.md`, `modules/module_51.md`, `modules/module_59.md`, `modules/module_21.md` — all consulted this session
- The cross-module doc is marked "Last Verified: 2025-10-22"; module docs for M50 and M51 are "Last Verified: 2025-10-13"; M59 "Last Verified: 2026-03-06"; M21 is marked "Fully Verified" with a 2026-05 note on PR #866 trade variable split
- No raw GAMS code was read this session per task instructions; line-number citations come from module docs, which were verified against code at the dates above
- Claims about `q21_trade_glo`, `q50_nr_bal_crp`, `q51_emissions_som`, `q59_nr_som`, `q59_nr_som_fertilizer` are 🟡 (documented); code-level verification would elevate to 🟢

**Source badge**: 🟡 Based on AI documentation consulted this session
