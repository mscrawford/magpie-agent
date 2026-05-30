# Anchor Question G2: vm_carbon_stock computation in Module 52 and GHG-policy cost in Module 56

## Overview

`vm_carbon_stock` is **declared in Module 56** (GHG Policy) but **populated by the land modules** (29, 31, 32, 34, 35, 59). Module 52 does not compute `vm_carbon_stock` — it reads it as an input to calculate CO2 emissions. Module 56 then takes those emissions (and also reads `vm_carbon_stock` directly) to compute policy costs. The chain has two distinct pathways, detailed below.

---

## Part 1: How vm_carbon_stock is populated (not by Module 52)

`vm_carbon_stock(j, land, c_pools, stockType)` is declared in Module 56's `declarations.gms:34` with dimensions: simulation cell `j`, land type `land`, carbon pool `c_pools` (vegc/litc/soilc), and stock type `stockType`.

The variable is **populated by land modules** during optimization:

- Module 29 (Cropland) — crop pool carbon (folds in `vm_carbon_stock_croparea` from Module 30)
- Module 31 (Pasture) — pasture carbon
- Module 32 (Forestry) — plantation/forestry carbon
- Module 34 (Urban) — urban carbon (fixed to 0)
- Module 35 (Natural Vegetation) — primforest, secdforest, and other natural land carbon
- Module 59 (SOM) — soilc pool for all land types

These modules compute per-cell, per-land-type carbon stocks using the carbon density data supplied by Module 52 (`fm_carbon_density`, `pm_carbon_density_secdforest_ac`, `pm_carbon_density_plantation_ac`, `pm_carbon_density_other_ac`).

Module 52's role in the carbon stock chain is as a **density data provider**, not as a stock calculator. The densities it supplies (from LPJmL input and Chapman-Richards growth equations) are the building blocks, but the stock values `vm_carbon_stock = density × area` are assembled by the land modules.

---

## Part 2: Module 52's single equation — q52_emis_co2_actual

Module 52 has exactly **one equation**: `q52_emis_co2_actual` (declared at `declarations.gms:30`, implemented at `equations.gms:16-19`).

### Formula (verbatim from module_52.md, verified against equations.gms:16-19):

```gams
q52_emis_co2_actual(i2,emis_oneoff) ..
  vm_emissions_reg(i2,emis_oneoff,"co2_c") =e=
    sum((cell(i2,j2),emis_land(emis_oneoff,land,c_pools)),
      (pcm_carbon_stock(j2,land,c_pools,"actual") - vm_carbon_stock(j2,land,c_pools,"actual"))
      / m_timestep_length
    );
```

### What each term does

| Term | Source | Role |
|------|--------|------|
| `vm_emissions_reg(i2,emis_oneoff,"co2_c")` | Module 56 `declarations.gms` | LHS: regional annual CO2-C emissions (Tg C/yr), written by Module 52 |
| `pcm_carbon_stock(j2,land,c_pools,"actual")` | Module 56 `declarations.gms` | Previous timestep carbon stock (mio. tC) — read by Module 52 |
| `vm_carbon_stock(j2,land,c_pools,"actual")` | Land modules (29,31,32,34,35,59) | Current timestep carbon stock (mio. tC) — read by Module 52 |
| `m_timestep_length` | `core/macros.gms:51` | Timestep length in years — annualizes the stock difference |
| `cell(i2,j2)` | Set mapping | Cells j2 belonging to region i2 |
| `emis_land(emis_oneoff,land,c_pools)` | Set mapping | Maps emission source labels (e.g., `secdforest_vegc`) to (land, c_pool) pairs |

### Logic

Positive result (pcm > vm): carbon lost from land → positive emission.
Negative result (pcm < vm): carbon gained → sequestration (negative emission).
Division by `m_timestep_length` converts the stock change (mio. tC over the timestep) to an annualized rate (Tg C/yr; 1 mio. tC = 1 Tg C).

### Carbon pools tracked

`emis_oneoff` emission sources (from `core/sets.gms:314-318`) include `crop_vegc`, `crop_litc`, `crop_soilc`, `past_vegc`, `past_litc`, `past_soilc`, `forestry_vegc`, `forestry_litc`, `forestry_soilc`, `primforest_vegc`, `primforest_litc`, `primforest_soilc`, `secdforest_vegc`, `secdforest_litc`, `secdforest_soilc`, `urban_vegc`, `urban_litc`, `urban_soilc`, `other_vegc`, `other_litc`, `other_soilc`.

---

## Part 3: How vm_carbon_stock and vm_emissions_reg enter Module 56's GHG-policy cost

Module 56 uses **two separate pathways** to compute carbon pricing costs — one through `vm_emissions_reg` (from Module 52), the other by reading `vm_carbon_stock` directly.

### Pathway A: Annual emissions (CH4, N2O, recurring CO2) via vm_emissions_reg

**Equation q56_emis_pricing** (`equations.gms:15-17`):
```gams
q56_emis_pricing(i2,pollutants,emis_annual) ..
  v56_emis_pricing(i2,emis_annual,pollutants) =e=
    vm_emissions_reg(i2,emis_annual,pollutants);
```
For recurring emission sources, the pricing variable equals `vm_emissions_reg` directly. This pathway carries Module 52's `co2_c` outputs for annual CO2 categories, as well as CH4 (Module 53) and N2O (Module 51).

**Equation q56_emission_cost_annual** (`equations.gms:29-33`):
```gams
q56_emission_cost_annual(i2,emis_annual) ..
  v56_emission_cost(i2,emis_annual) =e=
    sum(pollutants,
        v56_emis_pricing(i2,emis_annual,pollutants) *
        sum(ct, im_pollutant_prices(ct,i2,pollutants,emis_annual)));
```
Cost = emissions × price, summed over pollutants.

### Pathway B: One-off CO2 emissions (deforestation-type) direct from vm_carbon_stock

**Equation q56_emis_pricing_co2** (`equations.gms:19-22`):
```gams
q56_emis_pricing_co2(i2,emis_oneoff) ..
  v56_emis_pricing(i2,emis_oneoff,"co2_c") =e=
    sum((cell(i2,j2),emis_land(emis_oneoff,land,c_pools)),
      (pcm_carbon_stock(j2,land,c_pools,"actual")
        - vm_carbon_stock(j2,land,c_pools,"%c56_carbon_stock_pricing%"))
      / m_timestep_length);
```

This is the **critical architectural point**: one-off CO2 emissions for pricing purposes are computed **directly from `vm_carbon_stock`**, **bypassing `vm_emissions_reg`**. Module 56 recomputes the carbon stock difference itself, rather than consuming the value already computed by Module 52's `q52_emis_co2_actual`. The key difference is the `stockType` dimension: Module 52's equation always uses `"actual"`, whereas Module 56 uses the configurable `%c56_carbon_stock_pricing%` (default `"actualNoAcEst"`, which excludes afforestation establishment from pricing to avoid double-counting with the CDR reward mechanism).

**Equation q56_emission_cost_oneoff** (`equations.gms:45-52`):
```gams
q56_emission_cost_oneoff(i2,emis_oneoff) ..
  v56_emission_cost(i2,emis_oneoff) =e=
    sum(pollutants,
        v56_emis_pricing(i2,emis_oneoff,pollutants)
        * m_timestep_length
        * sum(ct,
            im_pollutant_prices(ct,i2,pollutants,emis_oneoff)
           * pm_interest(ct,i2)/(1+pm_interest(ct,i2))));
```

One-off emissions are converted to an annualized perpetuity cost using the annuity factor `r/(1+r)`. The `m_timestep_length` factor converts the annualized emission rate back to the total timestep emission before applying price and annuity. This ensures one-time deforestation events are penalized on the same basis as recurring emissions.

### Aggregation to vm_emission_costs

**Equation q56_emission_costs** (`equations.gms:56-58`):
```gams
q56_emission_costs(i2) ..
  vm_emission_costs(i2) =e=
    sum(emis_source, v56_emission_cost(i2,emis_source));
```

Sums over all emission sources (annual + one-off) to produce the total regional emission cost `vm_emission_costs(i)`, which enters Module 11 (Costs) and the objective function.

---

## Part 4: Which carbon pools are priced under the default policy

The policy matrix `f56_emis_policy` (applied at `preloop.gms:84-91`) controls which gas-source combinations are actually priced. Under the default policy `"reddnatveg_nosoil"`:

- Priced (co2_c = 1): `primforest_vegc`, `primforest_litc`, `secdforest_vegc`, `secdforest_litc`, `other_vegc`, `other_litc`, and peatland
- Not priced (co2_c = 0): cropland, pasture, forestry (plantation), urban, and all soilc pools

The `c56_carbon_stock_pricing` switch (default `"actualNoAcEst"`) further excludes afforestation establishment carbon from the one-off pricing equation to prevent double-counting with the CDR reward (`vm_reward_cdr_aff`) calculated by `q56_reward_cdr_aff` (`equations.gms:67-79`).

---

## Summary: the full chain

```
LPJmL input data (fm_carbon_density)
  → Module 52 start.gms: Chapman-Richards age-class density calculations
      (pm_carbon_density_secdforest_ac, pm_carbon_density_plantation_ac, pm_carbon_density_other_ac)
  → [optionally calibrated in Module 52 preloop.gms via bisection to FRA 2025 targets]
  → Land modules (29, 31, 32, 34, 35, 59) use densities to compute vm_carbon_stock

vm_carbon_stock (populated by land modules, declared in Module 56):
  → Module 52 q52_emis_co2_actual (equations.gms:16-19):
      vm_emissions_reg = (pcm_carbon_stock - vm_carbon_stock) / m_timestep_length
      [uses stockType="actual"; annualizes stock difference as Tg C/yr]
  
  → Module 56 q56_emis_pricing_co2 (equations.gms:19-22):
      v56_emis_pricing (oneoff, co2_c) = (pcm_carbon_stock - vm_carbon_stock[stockType=c56_carbon_stock_pricing]) / m_timestep_length
      [direct read; uses configurable stockType, default "actualNoAcEst"]
  
  → Module 56 q56_emission_cost_oneoff (equations.gms:45-52):
      v56_emission_cost = v56_emis_pricing × m_timestep_length × price × r/(1+r)
      [annuity factor converts one-off stock loss to perpetuity cost]
  
  → Module 56 q56_emission_costs (equations.gms:56-58):
      vm_emission_costs = sum(emis_source, v56_emission_cost)
  
  → Module 11 (Costs): vm_emission_costs enters objective function
```

---

## Sources

- module_52.md (Sections 3, Interface Variables, Key Equations)
- module_56.md (Sections 2.1–2.5, 3.7, 4.1–4.2, 8.1)
- Equation citations: `equations.gms:16-19` (Module 52), `equations.gms:12-22`, `equations.gms:29-33`, `equations.gms:45-52`, `equations.gms:56-58` (Module 56)
- Declarations: Module 56 `declarations.gms:34` (vm_carbon_stock), `declarations.gms:39` (vm_emission_costs)
- Preloop: Module 56 `preloop.gms:84-91` (emission policy matrix)
