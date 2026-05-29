# R29 Q3: Food/Material Supply-Demand Enforcement and Cropland Soil Nitrogen Budget

## Part (a): How MAgPIE enforces food/material supply >= demand

### Overview

Supply-demand balance is enforced through a three-module chain: Module 15 (Food) → Module 16 (Demand) → Module 21 (Trade). Module 17 (Production) provides the production-side variable. The binding enforcement equation lives in Module 21.

### Step 1: Food demand is computed in Module 15

Module 15 (realization `anthro_iso_jun22`) runs as a standalone optimization model that produces calibrated per-capita food demand (`p15_kcal_pc_calibrated`). It connects to MAgPIE's main optimization via one equation:

**`q15_food_demand(i,kfo)`** — `modules/15_food/anthro_iso_jun22/equations.gms:10-14`

```gams
q15_food_demand(i2,kfo) ..
    (vm_dem_food(i2,kfo) + sum(ct, f15_household_balanceflow(ct,i2,kfo,"dm")))
    * sum(ct,(fm_nutrition_attributes(ct,kfo,"kcal") * 10**6)) =g=
    sum(ct,im_pop(ct,i2) * p15_kcal_pc_calibrated(ct,i2,kfo)) * 365
```

This enforces: (food use + balance flow) x kcal content >= population x daily kcal demand x 365. It is an inequality (>=): overproduction is allowed, underproduction is not. The variable `vm_dem_food(i,kfo)` is the optimization variable representing food demand in million tonnes dry matter per year.

### Step 2: Module 16 aggregates all demands into vm_supply

Module 16 (realization `sector_may15`) is the demand aggregation hub. For each commodity type it computes `vm_supply(i,kall)`, which represents total regional demand (food + feed + processing + material + bioenergy + seed + waste + balance flow).

The key equation for crops is:

**`q16_supply_crops(i,kcr)`** — `modules/16_demand/sector_may15/equations.gms:19-29`

```gams
vm_supply(i2,kcr) =e=
    vm_dem_food(i2,kcr)
    + sum(kap4, vm_dem_feed(i2,kap4,kcr))
    + vm_dem_processing(i2,kcr)
    + vm_dem_material(i2,kcr)
    + vm_dem_bioen(i2,kcr)
    + vm_dem_seed(i2,kcr)
    + v16_dem_waste(i2,kcr)
    + sum(ct, f16_domestic_balanceflow(ct,i2,kcr))
```

This is an equality (`=e=`): `vm_supply` is defined as the exact sum of all demand streams. Analogous equations exist for livestock (`q16_supply_livestock`), secondary products (`q16_supply_secondary`), residues (`q16_supply_residues`), pasture (`q16_supply_pasture`), and forestry (`q16_supply_forestry`).

**Key variables in vm_supply:**
- `vm_dem_food(i,kfo)` — from Module 15
- `vm_dem_feed(i,kap,kall)` — from Module 70 (Livestock)
- `vm_dem_material(i,kall)` — from Module 62
- `vm_dem_bioen(i,kall)` — from Module 60
- `vm_dem_seed(i,kcr)` — calculated endogenously in Module 16 via `q16_seed_demand`
- `v16_dem_waste(i,kall)` — calculated endogenously via `q16_waste_demand`

Material demand is part of `vm_supply` through `vm_dem_material`, sourced from Module 62.

### Step 3: Module 21 enforces the binding supply >= demand constraint

Module 21 (realization `selfsuff_reduced`) is where the binding supply >= demand constraint is enforced. There are two key enforcement equations operating at different spatial scales:

**`q21_trade_glo(k_trade)`** — `modules/21_trade/selfsuff_reduced/equations.gms:12-14` — GLOBAL SCALE

```gams
q21_trade_glo(k_trade)..
  sum(i2, vm_prod_reg(i2,k_trade)) =g=
  sum(i2, vm_supply(i2,k_trade)) + sum(ct,f21_trade_balanceflow(ct,k_trade));
```

**Meaning**: Sum of regional production across all regions >= sum of regional supply (demand) plus a historical balance flow. This is the primary equation that ensures global production meets global demand for all tradable commodities (`k_trade`). It operates on `vm_prod_reg(i,k)` (from Module 17) vs. `vm_supply(i,k)` (from Module 16).

**`q21_notrade(h,k_notrade)`** — `modules/21_trade/selfsuff_reduced/equations.gms:18-19` — SUPERREGIONAL SCALE (non-tradables)

```gams
q21_notrade(h2,k_notrade)..
  sum(supreg(h2,i2),vm_prod_reg(i2,k_notrade)) =g= sum(supreg(h2,i2), vm_supply(i2,k_notrade));
```

For non-tradable commodities (oilpalm, foddr, pasture, residues, begr, betr), production must meet demand within each superregion `h`. This enforces superregional (not strict per-region) self-sufficiency.

**`q21_trade_reg(h,k_trade)`** — `modules/21_trade/selfsuff_reduced/equations.gms:31-35` — minimum regional production bound

This additional equation enforces a lower production bound based on historical self-sufficiency ratios, preventing full specialization to comparative advantage. It applies only to tradable commodities.

### Summary of enforcement

| Equation | Module | Scale | Commodity scope | Constraint type |
|----------|--------|-------|-----------------|-----------------|
| `q15_food_demand` | 15 | Regional (i) | Food commodities (kfo) | >= |
| `q16_supply_*` | 16 | Regional (i) | All (kall) | =e= (definition) |
| `q21_trade_glo` | 21 | Global | Tradables (k_trade) | >= |
| `q21_notrade` | 21 | Superregional (h) | Non-tradables (k_notrade) | >= |

**The binding enforcement variable is `vm_supply(i,kall)` (declared in `modules/16_demand/sector_may15/declarations.gms:11`), produced by Module 16 and consumed by Module 21's global trade constraint.** Module 17 provides the supply side via `vm_prod_reg(i,k)` (`declarations.gms:9`, `equations.gms:10-11`: a single spatial aggregation equation `q17_prod_reg` summing cell-level `vm_prod(j,k)` to regional level).

---

## Part (b): Cropland soil nitrogen budget — how it is balanced and how surplus becomes emissions

### The budget equation

**Module 50** (realization `macceff_aug22`) enforces the cropland nitrogen budget. The primary budget constraint is:

**`q50_nr_bal_crp(i)`** — `modules/50_nr_soil_budget/macceff_aug22/equations.gms:14-16`

```gams
q50_nr_bal_crp(i2) ..
    vm_nr_eff(i2) * v50_nr_inputs(i2)
    =g= sum(kcr,v50_nr_withdrawals(i2,kcr));
```

**Mathematical form**: SNUpE(i) x N_inputs(i) >= N_withdrawals(i)

Where SNUpE = Soil Nitrogen Uptake Efficiency (vm_nr_eff, a scenario-fixed fraction from 0 to 1). This is an inequality (>=) not a strict equality: inputs can exceed withdrawals, with the excess forming the nitrogen surplus.

### Main inputs (v50_nr_inputs)

The inputs term is defined by:

**`q50_nr_inputs(i)`** — `modules/50_nr_soil_budget/macceff_aug22/equations.gms:22-32`

```gams
q50_nr_inputs(i2) ..
    v50_nr_inputs(i2) =e=
    vm_res_recycling(i2,"nr")                                         -- crop residues (Module 18)
      + sum((cell(i2,j2),kcr,w), vm_area(j2,kcr,w) * f50_nr_fix_area(kcr))  -- biological N fixation (area-based)
      + sum(cell(i2,j2),vm_fallow(j2) * f50_nr_fix_area("tece"))     -- fallow area fixation
      + vm_manure_recycling(i2,"nr")                                  -- manure applied (Module 55)
      + sum(kli, vm_manure(i2, kli, "stubble_grazing","nr"))          -- stubble-grazing manure (Module 55)
      + vm_nr_inorg_fert_reg(i2,"crop")                               -- inorganic fertilizer (optimization variable)
      + sum(cell(i2,j2),vm_nr_som_fertilizer(j2))                     -- N from SOM mining (Module 59)
      + sum(ct,f50_nitrogen_balanceflow(ct,i2))                       -- correction balanceflow
      + v50_nr_deposition(i2,"crop");                                 -- atmospheric deposition
```

**Key inputs**: residues (vm_res_recycling), biological N fixation (area-based via f50_nr_fix_area), manure (vm_manure_recycling + stubble grazing manure), inorganic fertilizer (vm_nr_inorg_fert_reg — the endogenous optimization variable), SOM mineralization (vm_nr_som_fertilizer from Module 59), atmospheric deposition (v50_nr_deposition).

### Main outputs (withdrawals)

**`q50_nr_withdrawals(i,kcr)`** — `modules/50_nr_soil_budget/macceff_aug22/equations.gms:36-43`

```gams
q50_nr_withdrawals(i2,kcr) ..
    v50_nr_withdrawals(i2,kcr) =e=
    (1-sum(ct,f50_nr_fix_ndfa(ct,i2,kcr))) *
    (vm_prod_reg(i2,kcr) * fm_attributes("nr",kcr)
       + vm_res_biomass_ag(i2,kcr,"nr")
       + vm_res_biomass_bg(i2,kcr,"nr"))
    - vm_dem_seed(i2,kcr) * fm_attributes("nr",kcr);
```

**Mathematical form**: N_withdrawal(i,crop) = (1 - NDFA(i,crop)) x [N_harvest + N_residue_above + N_residue_below] - N_seed

Where NDFA = Nitrogen Derived From Atmosphere (fraction of biomass N from biological fixation, 0-0.8 for legumes). Seeds subtract from withdrawals because they bring N into the field. Net N withdrawal from soil is reduced for legumes by (1-NDFA) because atmospheric fixation replaces soil N supply.

### The nitrogen surplus

**`q50_nr_surplus(i)`** — `modules/50_nr_soil_budget/macceff_aug22/equations.gms:46-49`

```gams
q50_nr_surplus(i2) ..
    v50_nr_surplus_cropland(i2)
    =e= v50_nr_inputs(i2)
    - sum(kcr, v50_nr_withdrawals(i2,kcr));
```

Surplus = total inputs minus withdrawals. This represents N not taken up by crops and therefore available for environmental losses. The surplus is NOT directly an emission: Module 50 only computes it as an accounting variable. The conversion of surplus to emissions happens in Module 51.

### How surplus nitrogen becomes emissions (Module 51)

Module 51 (realization `rescaled_jan21`) converts nitrogen flows to emissions via **NUE-based rescaling**, not simple surplus multiplication. The key conceptual link: Module 50's `vm_nr_eff(i)` (cropland SNUpE) is the bridge between the budget and the emission equations.

The general NUE-rescaling formula applied to each nitrogen source is:

```
Emissions = N_source / (1 - s51_snupe_base) * (1 - vm_nr_eff(i)) * EF
```

Where `s51_snupe_base = 0.5` (`modules/51_nitrogen/rescaled_jan21/input.gms:8`) — the baseline 50% NUE assumed in IPCC emission factors. The rescaling factor `(1 - vm_nr_eff) / (1 - 0.5)` adjusts IPCC factors to actual NUE: if actual NUE is 60%, only 40% of inputs are available for losses vs. 50% assumed by IPCC, so emissions scale by 0.4/0.5 = 0.8.

**Key emission equations in Module 51:**

1. **Manure on cropland emissions** — `q51_emissions_man_crop(i,n_pollutants_direct)` — `equations.gms:22-27`:

   ```gams
   vm_emissions_reg(i2,"man_crop",n_pollutants_direct) =e=
   vm_manure_recycling(i2,"nr")
   / (1-s51_snupe_base) * (1-vm_nr_eff(i2))
   * sum(ct, i51_ef_n_soil(ct,i2,n_pollutants_direct,"man_crop"))
   ```

2. **Inorganic fertilizer emissions** — `q51_emissions_inorg_fert(i,n_pollutants_direct)` — `equations.gms:30-39`:

   ```gams
   vm_emissions_reg(i2,"inorg_fert",n_pollutants_direct) =e=
   vm_nr_inorg_fert_reg(i2,"crop")
   / (1-s51_snupe_base) * (1-vm_nr_eff(i2))
   * sum(ct, i51_ef_n_soil(ct,i2,n_pollutants_direct,"inorg_fert"))
   + vm_nr_inorg_fert_reg(i2,"past")
   / (1-s51_nue_pasture_base) * (1-vm_nr_eff_pasture(i2))
   * sum(ct, i51_ef_n_soil(ct,i2,n_pollutants_direct,"inorg_fert"))
   ```

3. **Residue emissions** — `q51_emissions_resid(i,n_pollutants_direct)` — `equations.gms:42-46`

4. **SOM loss emissions** — `q51_emissions_som(i,n_pollutants_direct)` — `equations.gms:55-59`

5. **Indirect N2O** — `q51_emissions_indirect_n2o(i,emis_source_n51)` — `equations.gms:83-89`: Indirect emissions from volatilized NH3/NOx (IPCC EF4 = 1%) and leached NO3- (IPCC EF5 = 0.75%).

All emissions populate `vm_emissions_reg(i,emis_source,pollutants)`, declared by Module 56 (`modules/56_ghg_policy/price_aug22/declarations.gms:40`). This variable carries N2O, NH3, NO2, and NO3 by source ({inorg_fert, man_crop, awms, resid, resid_burn, man_past, som}) to Module 56 for optional GHG pricing.

**Critical point**: Module 50 does NOT calculate emissions. It calculates the nitrogen surplus (`v50_nr_surplus_cropland`) and provides the efficiency parameter (`vm_nr_eff`). Module 51 takes those and calculates emissions by applying NUE-rescaled IPCC emission factors to each nitrogen source independently.

### Pasture nitrogen budget (parallel structure)

An analogous budget equation exists for pasture:

**`q50_nr_bal_pasture(i)`** — `equations.gms:55-59`:

```gams
q50_nr_bal_pasture(i2) ..
    vm_nr_eff_pasture(i2) * v50_nr_inputs_pasture(i2)
    =g= v50_nr_withdrawals_pasture(i2);
```

With surplus defined by `q50_nr_surplus_pasture` (`equations.gms:62-66`) and emissions calculated in Module 51 using `vm_nr_eff_pasture(i)` (pasture-specific NUE).

---

## Key Variables Summary

| Variable | Module | Purpose |
|----------|--------|---------|
| `vm_dem_food(i,kfo)` | 15 | Food demand optimization variable |
| `vm_supply(i,kall)` | 16 | Total demand (supply requirement) aggregator |
| `vm_prod_reg(i,k)` | 17 | Regional production (spatial aggregation of vm_prod) |
| `vm_nr_inorg_fert_reg(i,land_ag)` | 50 | Endogenous inorganic fertilizer (optimization variable) |
| `vm_nr_eff(i)` | 50 | Cropland SNUpE — FIXED in presolve, scenario-driven |
| `v50_nr_inputs(i)` | 50 | Total N inputs to cropland soil |
| `v50_nr_withdrawals(i,kcr)` | 50 | N withdrawn by crops |
| `v50_nr_surplus_cropland(i)` | 50 | N inputs minus withdrawals (potential emission pool) |
| `vm_emissions_reg(i,source,pollutant)` | 56 (declared), 51 (computed) | Agricultural nitrogen emissions by source and pollutant |

---

## Items not covered by docs

- The exact line numbers for `q21_trade_reg` upper bound (`q21_trade_reg_up`) were not read in full; docs cite the equation name and general structure but I did not read lines 36+ of module_21.md.
- `q16_supply_forestry` and `q16_supply_secondary` formulas cited from module_16.md; not independently verified against GAMS code this session.
- The precise line numbers for `q50_nr_surplus_pasture` in equations.gms cited from module_50.md (lines 62-66) were not independently re-verified this session.

---

## Sources

- `modules/module_15.md` (equations.gms:10-14)
- `modules/module_16.md` (equations.gms:19-88, declarations.gms:11)
- `modules/module_17.md` (equations.gms:10-11)
- `modules/module_21.md` (equations.gms:12-14, 18-19, 31-35)
- `modules/module_50.md` (equations.gms:14-16, 22-32, 36-43, 46-49, 55-59, 62-66, 74-80)
- `modules/module_51.md` (equations.gms:22-27, 30-39, 42-46, 55-59, 83-89; input.gms:8-9)
- `cross_module/nitrogen_food_balance.md` (Part 1 and Part 2)

Status: 🟡 Based on module AI documentation. Not independently verified in raw GAMS code this session.
