# MAgPIE Nitrogen Soil Budget: Module 50 Trace

## Active Realization

Module 50 runs under realization `macceff_aug22`. Module 51 runs under `rescaled_jan21`. Module 55 runs under `ipcc2006_aug16`.
Sources: `module_50.md`, `module_51.md`, `module_55.md`.

---

## The Central Balance Equations

Module 50 contains **two** soil nitrogen balance equations — one for cropland, one for pasture — not a single unified equation.

### Cropland balance: `q50_nr_bal_crp`

`modules/50_nr_soil_budget/macceff_aug22/equations.gms:14-16`

```gams
q50_nr_bal_crp(i2) ..
    vm_nr_eff(i2) * v50_nr_inputs(i2)
    =g= sum(kcr, v50_nr_withdrawals(i2,kcr));
```

Mathematical form: `SNUpE(i) x N_inputs(i) >= N_withdrawals(i)`

This is an inequality (`=g=`), not strict equality. It enforces that the fraction of nitrogen inputs taken up by crops (SNUpE = Soil Nitrogen Uptake Efficiency) is enough to cover what the crops withdraw. The model optimizes inorganic fertilizer (`vm_nr_inorg_fert_reg`) to satisfy this constraint at minimum cost.

### Pasture balance: `q50_nr_bal_pasture`

`modules/50_nr_soil_budget/macceff_aug22/equations.gms:55-59`

```gams
q50_nr_bal_pasture(i2) ..
    vm_nr_eff_pasture(i2) *
    v50_nr_inputs_pasture(i2)
    =g=
    v50_nr_withdrawals_pasture(i2);
```

Same structure, separate efficiency parameter (`vm_nr_eff_pasture` rather than `vm_nr_eff`).

---

## Input Terms

### Cropland inputs: `q50_nr_inputs`

`modules/50_nr_soil_budget/macceff_aug22/equations.gms:22-32`

```gams
q50_nr_inputs(i2) ..
    v50_nr_inputs(i2) =e=
    vm_res_recycling(i2,"nr")
      + sum((cell(i2,j2),kcr,w), vm_area(j2,kcr,w) * f50_nr_fix_area(kcr))
      + sum(cell(i2,j2), vm_fallow(j2) * f50_nr_fix_area("tece"))
      + vm_manure_recycling(i2,"nr")
      + sum(kli, vm_manure(i2, kli, "stubble_grazing","nr"))
      + vm_nr_inorg_fert_reg(i2,"crop")
      + sum(cell(i2,j2), vm_nr_som_fertilizer(j2))
      + sum(ct, f50_nitrogen_balanceflow(ct,i2))
      + v50_nr_deposition(i2,"crop");
```

Eight terms:

| Term | Variable / Parameter | Description |
|------|---------------------|-------------|
| Crop residues recycled | `vm_res_recycling(i,"nr")` | Above+below-ground residues left on field; declared by M18 |
| Biological N fixation (area-based, legumes) | `crop_area * f50_nr_fix_area(kcr)` | `vm_area` from M30; rate `f50_nr_fix_area` is input parameter |
| Biological N fixation (fallow) | `vm_fallow(j2) * f50_nr_fix_area("tece")` | `vm_fallow` from M29 |
| Manure/organic recycling (confinement) | `vm_manure_recycling(i2,"nr")` | Collected manure applied to crops; declared by M55 |
| Manure/organic recycling (stubble grazing) | `vm_manure(i2,kli,"stubble_grazing","nr")` | Manure deposited by animals grazing crop residues; declared by M55 |
| Inorganic fertilizer | `vm_nr_inorg_fert_reg(i2,"crop")` | Endogenous optimization variable; declared by M50 |
| SOM mineralization | `vm_nr_som_fertilizer(j2)` | N from soil organic matter turnover; declared by M59 |
| Balance flow correction | `f50_nitrogen_balanceflow(ct,i2)` | Parameter (input data), not a variable |
| Atmospheric deposition | `v50_nr_deposition(i2,"crop")` | Computed by `q50_nr_deposition` below |

Atmospheric deposition equation: `modules/50_nr_soil_budget/macceff_aug22/equations.gms:88-90`

```gams
q50_nr_deposition(i2,land) ..
    v50_nr_deposition(i2,land) =e=
    sum((ct,cell(i2,j2)), i50_atmospheric_deposition_rates(ct,j2,land) * vm_land(j2,land));
```

Rate data from `f50_AtmosphericDepositionRates.cs3` (exogenous input; applied uniformly over land area — this is parameterization, not mechanistic atmospheric modeling).

### Pasture inputs: `q50_nr_inputs_pasture`

`modules/50_nr_soil_budget/macceff_aug22/equations.gms:74-80`

Four terms:

1. Grazing manure: `vm_manure(i2,kli,"grazing","nr")` — declared by M55
2. Inorganic fertilizer on pasture: `vm_nr_inorg_fert_reg(i2,"past")` — declared by M50
3. Biological fixation (area-based): `vm_land(j2,"past") * f50_nr_fixation_rates_pasture(ct,i2)` — parameter rate, exogenous
4. Atmospheric deposition: `v50_nr_deposition(i2,"past")`

---

## Withdrawal Terms

### Cropland withdrawals: `q50_nr_withdrawals`

`modules/50_nr_soil_budget/macceff_aug22/equations.gms:36-43`

```gams
q50_nr_withdrawals(i2,kcr) ..
    v50_nr_withdrawals(i2,kcr) =e=
    (1 - sum(ct, f50_nr_fix_ndfa(ct,i2,kcr))) *
    (vm_prod_reg(i2,kcr) * fm_attributes("nr",kcr)
       + vm_res_biomass_ag(i2,kcr,"nr")
       + vm_res_biomass_bg(i2,kcr,"nr"))
    - vm_dem_seed(i2,kcr) * fm_attributes("nr",kcr);
```

- `(1 - NDFA)`: Fraction not derived from biological fixation — only the soil-sourced fraction counts as a withdrawal
- `vm_prod_reg(i2,kcr)`: Harvested crop production (N content via `fm_attributes`); declared by M17
- `vm_res_biomass_ag`, `vm_res_biomass_bg`: N in above-ground and below-ground residues; declared by M18
- `vm_dem_seed(i2,kcr)`: Seed nitrogen is SUBTRACTED — seeds bring N onto the field, reducing net withdrawal; declared by M16

### Pasture withdrawals: `q50_nr_withdrawals_pasture`

`modules/50_nr_soil_budget/macceff_aug22/equations.gms:83-85`

```gams
q50_nr_withdrawals_pasture(i2) ..
    v50_nr_withdrawals_pasture(i2) =e=
    vm_prod_reg(i2,"pasture") * fm_attributes("nr","pasture");
```

Simpler: just the N content of harvested grass.

### Nitrogen surplus (the "loss" residual)

Cropland: `q50_nr_surplus` at `equations.gms:46-49`
```gams
v50_nr_surplus_cropland(i2) =e= v50_nr_inputs(i2) - sum(kcr, v50_nr_withdrawals(i2,kcr));
```

Pasture: `q50_nr_surplus_pasture` at `equations.gms:62-66`
```gams
v50_nr_surplus_pasture(i2) =e= v50_nr_inputs_pasture(i2) - v50_nr_withdrawals_pasture(i2);
```

The surplus represents nitrogen not taken up by crops. It is NOT used directly in emission equations. Instead, Module 51 reconstructs losses from the efficiency parameters (see below).

---

## Interface Variables: M50 to M51 (nitrogen emissions) and M55 (animal waste)

### Variables flowing from M50 to M51

Module 51 (`rescaled_jan21`) uses three variables that originate in M50 (`macceff_aug22/declarations.gms`):

| Variable | Declared by | Populated by | Consumed in M51 at | Description |
|----------|------------|--------------|---------------------|-------------|
| `vm_nr_eff(i)` | M50 `macceff_aug22/declarations.gms:12` | M50 `presolve.gms:76` (`.fx()` assignment) | `equations.gms:26, 34, 46, 59` | Cropland soil nitrogen uptake efficiency (SNUpE); FIXED each timestep, not an optimization variable |
| `vm_nr_eff_pasture(i)` | M50 `macceff_aug22/declarations.gms:13` | M50 `presolve.gms:77` (`.fx()` assignment) | `equations.gms:37, 80` | Pasture nitrogen use efficiency (NUE); also FIXED each timestep |
| `vm_nr_inorg_fert_reg(i,land_ag)` | M50 `macceff_aug22/declarations.gms:10` | M50 solve (optimization variable) | `equations.gms:33, 36` | Inorganic fertilizer applied to crop and pasture land |

How M51 uses them: in the NUE-rescaling formula applied to each direct emission source:

```
Emissions = N_source / (1 - s51_snupe_base) * (1 - vm_nr_eff) * EF
```

where `s51_snupe_base = 0.5` (`module_51.md`, `input.gms:8`). Higher actual NUE (vm_nr_eff) → smaller loss fraction → lower emissions.

### Variables flowing from M55 to M50 (organic recycling/manure inputs)

Module 55 (`ipcc2006_aug16`) declares and populates the manure variables that M50 consumes as organic nitrogen inputs:

| Variable | Declared by | Populated by | Consumed in M50 at | Description |
|----------|------------|--------------|---------------------|-------------|
| `vm_manure_recycling(i,npk)` | M55 `ipcc2006_aug16/declarations.gms:21` | M55 `q55_manure_recycling` (`equations.gms:84`) | M50 `equations.gms:27` | Total manure N recycled from confinement systems to cropland |
| `vm_manure(i,kli,"stubble_grazing","nr")` | M55 `declarations.gms` | M55 `q55_bal_manure` (`equations.gms:68-71`) | M50 `equations.gms:28` | Stubble-grazing manure deposited on cropland |
| `vm_manure(i,kli,"grazing","nr")` | M55 `declarations.gms` | M55 `q55_bal_manure` (`equations.gms:68-71`) | M50 `equations.gms:77` (pasture inputs) | Grazing manure deposited directly on pasture |

### Variables flowing from M55 to M51 (for emission calculation)

Module 51 reads three additional M55-declared variables to compute AWMS and pasture emissions:

| Variable | Declared by | Populated by | Consumed in M51 at | Description |
|----------|------------|--------------|---------------------|-------------|
| `vm_manure_confinement(i,kli,awms_conf,npk)` | M55 `declarations.gms` | M55 `q55_manure_confinement` (`equations.gms:76`) | M51 `equations.gms:69` | Manure in each of 9 confinement management systems; used for AWMS N emission calculation |
| `vm_manure(i,kli,awms_prp,npk)` where `awms_prp={grazing,stubble_grazing}` | M55 `declarations.gms` | M55 `q55_bal_manure` (`equations.gms:68-71`) | M51 `equations.gms:78` | Pasture/range/paddock manure; used for pasture manure emission calculation |
| `vm_manure_recycling(i,npk)` | M55 `declarations.gms:21` | M55 `q55_manure_recycling` (`equations.gms:84`) | M51 `equations.gms:25` | Manure-on-cropland N; used for `q51_emissions_man_crop` |

Note: `vm_manure_recycling` is shared between both M50 and M51 — M50 uses it as a nitrogen input to cropland soil, M51 uses it to compute manure-on-cropland emissions.

---

## Summary: DECLARED vs POPULATED for Each Named Interface Variable

| Variable | DECLARED | POPULATED | Consumed |
|----------|----------|-----------|---------|
| `vm_nr_eff(i)` | M50 `declarations.gms:12` | M50 `presolve.gms:76` | M51 `equations.gms:26,34,46,59` |
| `vm_nr_eff_pasture(i)` | M50 `declarations.gms:13` | M50 `presolve.gms:77` | M51 `equations.gms:37,80` |
| `vm_nr_inorg_fert_reg(i,land_ag)` | M50 `declarations.gms:10` | M50 solver (optimization) | M51 `equations.gms:33,36` |
| `vm_manure_recycling(i,npk)` | M55 `declarations.gms:21` | M55 `equations.gms:84` | M50 `equations.gms:27`; M51 `equations.gms:25` |
| `vm_manure(i,kli,awms,npk)` | M55 `declarations.gms` | M55 `equations.gms:68-71` | M50 `equations.gms:28,77`; M51 `equations.gms:78` |
| `vm_manure_confinement(i,kli,awms_conf,npk)` | M55 `declarations.gms` | M55 `equations.gms:76` | M51 `equations.gms:69` |

---

## What Module 50 Does NOT Do

Critical for accuracy:

- M50 does NOT calculate emissions. It calculates nitrogen surplus (`v50_nr_surplus_cropland`, `v50_nr_surplus_pasture`), but Module 51 does not use the surplus variable directly — it reconstructs losses from the efficiency parameters `vm_nr_eff`/`vm_nr_eff_pasture`.
- `vm_nr_eff` and `vm_nr_eff_pasture` are declared as `positive variables` but are FIXED (not optimized) each timestep via `.fx()` in `presolve.gms:76-77`. The model optimizes fertilizer amount, not efficiency.
- Biological N fixation and atmospheric deposition are applied via exogenous rates (parameter tables) multiplied by area — this is parameterization, not mechanistic process modeling.

---

## Epistemic Status

All claims here are sourced from AI documentation files read this session:

- `modules/module_50.md` — 🟡 Documented (module doc, last verified 2025-10-13 against `macceff_aug22` source)
- `modules/module_51.md` — 🟡 Documented (module doc, last verified 2025-10-13 against `rescaled_jan21` source)
- `modules/module_55.md` — 🟡 Documented (module doc, last verified 2025-10-13 against `ipcc2006_aug16` source)
- `cross_module/nitrogen_food_balance.md` — 🟡 Documented (cross-module balance doc)

Line numbers for equations cite the verified-at-2025-10-13 code state. Code changes since that date may have shifted them.
