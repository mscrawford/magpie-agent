# Round 30 Answer: CO2 Stock-Difference Accounting in MAgPIE

**Question**: How does MAgPIE compute CO2 emissions from carbon-stock changes over time (the stock-difference accounting)? Which modules' carbon stocks enter, and which equation in module 52 produces the actual CO2 emissions?

---

## The Core Emission Equation

Module 52 (realization `normal_dec17`) has exactly one GAMS equation that produces CO2 emissions:

**`q52_emis_co2_actual`** (`modules/52_carbon/normal_dec17/equations.gms:16-19`)

```gams
q52_emis_co2_actual(i2,emis_oneoff) ..
  vm_emissions_reg(i2,emis_oneoff,"co2_c") =e=
    sum((cell(i2,j2),emis_land(emis_oneoff,land,c_pools)),
      (pcm_carbon_stock(j2,land,c_pools,"actual")
       - vm_carbon_stock(j2,land,c_pools,"actual"))
      / m_timestep_length
    );
```

This is the entirety of Module 52's optimization content; the module declares one equation and no optimization variables.

## Stock-Difference Accounting Mechanics

The logic is a straightforward mass-balance:

```
CO2 emissions (Tg C/yr) = (previous carbon stock - current carbon stock) / timestep length
```

- `pcm_carbon_stock(j,land,c_pools,"actual")` — the carbon stock at the END of the previous timestep (a parameter, carried forward)
- `vm_carbon_stock(j,land,c_pools,"actual")` — the carbon stock being optimized in the CURRENT timestep (an interface variable declared in Module 56)
- `m_timestep_length` — years in the timestep (macro from `core/macros.gms:51`; typically 5 years in mid-run periods)

Sign convention:
- Previous > Current: positive emission (land is a carbon source — e.g., deforestation)
- Previous < Current: negative emission (land is a carbon sink — e.g., afforestation)

The summation is indexed by `cell(i2,j2)` (mapping cells to regions) and `emis_land(emis_oneoff,land,c_pools)` (a set that maps each named emission source to its land type and carbon pool combination). There are 21 such combinations — 7 land types x 3 carbon pools.

## Carbon Pools

Three pools are tracked (`c_pools` set, `core/sets.gms:324-325`):
- `vegc` — vegetation carbon (above- and below-ground live biomass)
- `litc` — litter carbon (dead plant material, converges linearly over 20 years)
- `soilc` — soil organic carbon

## Which Modules Contribute Carbon Stocks to `vm_carbon_stock`

`vm_carbon_stock(j,land,c_pools,"actual")` is an interface variable declared in Module 56 (`modules/56_ghg_policy/price_aug22/declarations.gms:34`). The following modules populate it:

| Module | Land types covered | Notes |
|--------|-------------------|-------|
| **Module 29 (Cropland)** | `crop` | Folds in crop-area carbon from Module 30 |
| **Module 31 (Pasture)** | `past` | Pasture carbon stock |
| **Module 32 (Forestry)** | `forestry` | Plantation carbon, age-class-weighted using `pm_carbon_density_plantation_ac` |
| **Module 34 (Urban)** | `urban` | Fixed to 0 (vegc/litc); soilc = other-land value (placeholder) |
| **Module 35 (Natural Vegetation)** | `primforest`, `secdforest`, `other` | Uses `pm_carbon_density_secdforest_ac`, `pm_carbon_density_other_ac` for age-class-resolved vegc/litc |
| **Module 59 (SOM)** | all land types (`soilc` pool) | Provides dynamic topsoil carbon; Module 52 provides static subsoil component |

Module 58 (Peatland) does NOT populate `vm_carbon_stock` — peatland emissions are handled outside this stock-difference chain.

## Carbon Density Inputs to Those Stocks

Module 52 is a data provider: it does not compute `vm_carbon_stock` itself, but it supplies the density parameters that other modules use to calculate it.

- **`fm_carbon_density(t_all,j,land,c_pools)`** — LPJmL-derived base densities for all land types, all pools (`modules/52_carbon/normal_dec17/input.gms:16-20`, source file `lpj_carbon_stocks.cs3`). Non-age-class land (cropland, pasture, primary forest, urban, other as a type) uses this directly.

- **`pm_carbon_density_plantation_ac(t_all,j,ac,ag_pools)`** — age-class-specific vegc and litc for plantations (`start.gms:17,20`). As of 2026-04-20, the vegc pool is **overwritten** in `preloop.gms` by a bisection calibration to FAO FRA 2025 growing-stock targets when `s52_growingstock_calib = 1` (the default). The uncalibrated version is preserved in `pm_carbon_density_plantation_ac_uncalib`.

- **`pm_carbon_density_secdforest_ac(t_all,j,ac,ag_pools)`** — age-class-specific vegc and litc for secondary forests (`start.gms:28,31`), similarly overwritten by calibration in preloop (uncalibrated copy in `pm_carbon_density_secdforest_ac_uncalib`).

- **`pm_carbon_density_other_ac(t_all,j,ac,ag_pools)`** — age-class-specific vegc and litc for other land (`start.gms:48,51`); not subject to FRA calibration.

Vegetation carbon (vegc) for age-classed land types follows the Chapman-Richards equation (`core/macros.gms:18`):

```
m_growth_vegc(S, A, k, m, ac) = S + (A - S) * (1 - exp(-k * (ac*5)))^m
```

Litter carbon (litc) follows linear convergence over 20 years (`core/macros.gms:20`). Soil carbon (soilc) is NOT age-class-specific in Module 52; Module 59 provides dynamic topsoil soilc for all land types using IPCC 2019 stock-change-factor methodology.

## Module 59's Role in soilc

Module 59 (`cellpool_jan23` realization) computes topsoil organic carbon per cell per land type (`v59_som_pool`) using a 15%-per-year convergence toward an equilibrium target (`v59_som_target`). Over a 5-year timestep this is ~56% toward the new equilibrium. Module 59 writes the soilc component of `vm_carbon_stock` for all land types. Module 52 provides the static subsoil soilc component (read from LPJmL). Together they form the total soilc entering `vm_carbon_stock`.

## Aggregation and Output

`q52_emis_co2_actual` aggregates cell-level stock differences to the region level (`i2`) and partitions them by emission source (`emis_oneoff`: `crop_vegc`, `crop_litc`, `crop_soilc`, `past_vegc`, ..., `other_soilc` — 21 combinations total). The output lands in `vm_emissions_reg(i,emis_oneoff,"co2_c")`, which Module 56 then uses for carbon pricing and policy constraints.

Units: carbon stocks in mio. tC; emissions in Tg C/yr (1 mio. tC = 1 Tg C, so division by timestep years is all that is needed).

## Key Structural Points

- Carbon balance is a **stock-flow tracking system, not a conservation law**. Carbon leaves the system as atmospheric CO2 or enters via photosynthesis; total terrestrial carbon is not conserved.
- Module 52 contains **no optimization variables** — emissions are derived consequences of land-allocation decisions made elsewhere.
- The emission equation fires **inside the optimization** (each solve), so the optimizer can internalize the carbon-price cost associated with changing land use.
- Module 56 stores `vm_carbon_stock` at the end of each timestep into `pcm_carbon_stock` for use as the "previous" stock in the next timestep.

---

**Sources consulted**:
- `modules/module_52.md` (fully verified against `../modules/52_carbon/normal_dec17/*.gms`, last verification 2026-05-16)
- `cross_module/carbon_balance_conservation.md`

**Epistemic status**:
- 🟡 Documented — all claims derived from `modules/module_52.md` and `cross_module/carbon_balance_conservation.md`, both of which are verified against source code. The equation text for `q52_emis_co2_actual` is quoted in the docs as an exact match with `equations.gms:16-19`. Module 52 docs were last verified against GAMS source on 2026-05-16 (commit `c7731e234`). For a high-stakes code modification, direct verification of the current GAMS files would upgrade this to 🟢.
