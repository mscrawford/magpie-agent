# G2: vm_carbon_stock Computation in Module 52 and Entry into GHG-Policy Cost in Module 56

## Overview

`vm_carbon_stock` is **declared** in Module 56 and **populated** by the land modules (29, 31, 32, 34, 35, 59). Module 52 **reads** `vm_carbon_stock` (and its lagged companion `pcm_carbon_stock`) to compute CO2 emissions, and Module 56 reads `vm_carbon_stock` a second time, directly, to compute the emissions used for carbon pricing. These are two separate uses of the same variable.

---

## Part 1: What is vm_carbon_stock and who populates it?

**Declaration**: `vm_carbon_stock(j,land,c_pools,stockType)` is declared in Module 56's `declarations.gms:34`.
- Dimensions: `j` (simulation cells), `land` (land types), `c_pools` (vegc/litc/soilc), `stockType` (actual/actualNoAcEst)
- Units: mio. tC

**Populated by the land modules** (not by Module 52 itself):
- **Module 29** (Cropland): crop pool carbon (folds in `vm_carbon_stock_croparea` from Module 30)
- **Module 31** (Pasture): pasture carbon
- **Module 32** (Forestry): plantation/forestry carbon
- **Module 34** (Urban): urban carbon (fixed to 0)
- **Module 35** (Natural Vegetation): primforest, secdforest, other land carbon
- **Module 59** (SOM): soilc pool for all land types

Module 52 does NOT compute `vm_carbon_stock`; it computes the carbon densities that underpin the land modules' `vm_carbon_stock` calculations.

**Lagged companion**: `pcm_carbon_stock(j,land,c_pools,stockType)` holds the **previous** timestep's value. Module 56 stores the solved `vm_carbon_stock` into `pcm_carbon_stock` at the end of each timestep for use in the next.

🟡 Source: `module_52.md` §"Interface Variables" / `module_56.md` §4.1

---

## Part 2: How Module 52 Computes Carbon Densities (Inputs to vm_carbon_stock)

Module 52 does not set `vm_carbon_stock` directly. Instead, it computes the **per-ha carbon density parameters** that the land modules multiply by area to fill `vm_carbon_stock`.

### 2a. Base densities from LPJmL

**`fm_carbon_density(t_all,j,land,c_pools)`** — loaded in `input.gms:16-20` from `lpj_carbon_stocks.cs3`. These are static (or scenario-adjusted) LPJmL carbon densities for all land types including non-age-class land (cropland, pasture, primforest, urban). Climate scenario handling adjusts them:
- `nocc`: freeze at 1995 values (`input.gms:22`)
- `nocc_hist`: freeze after `sm_fix_cc` (`input.gms:23`)

`fm_carbon_density` is what Module 56 reads directly in its own preloop to initialize `pcm_carbon_stock` (`modules/56_ghg_policy/price_aug22/preloop.gms:10`).

🟡 Source: `module_52.md` §2, §"Data Inputs"

### 2b. Age-class densities (start.gms, then optionally overwritten by preloop.gms)

For plantations, secondary forests, and other land, Module 52 computes age-class-specific carbon densities in **start.gms** before each timestep's optimization:

**Vegetation carbon (vegc) — Chapman-Richards equation** (`core/macros.gms:18`):
```
m_growth_vegc(S, A, k, m, ac) = S + (A - S) * (1 - exp(-k * (ac*5)))^m
```
Applied to:
- `pm_carbon_density_plantation_ac(t_all,j,ac,"vegc")` — `start.gms:17`: S=0, A=secdforest vegc, k/m = plantation-specific parameters weighted by `pm_climate_class`
- `pm_carbon_density_secdforest_ac(t_all,j,ac,"vegc")` — `start.gms:28`: S=0, A=secdforest vegc, k/m = natveg parameters
- `pm_carbon_density_other_ac(t_all,j,ac,"vegc")` — `start.gms:48`: S=0, A=other land vegc, k/m = natveg parameters

**Litter carbon (litc) — linear 20-year equilibration** (`core/macros.gms:20`):
```
m_growth_litc_soilc(start, end, ac) = (start + (end-start)/4 * ac)$(ac<=4) + end$(ac>4)
```
Applied analogously at `start.gms:20,31,51` for plantations/secdforest/other land. Soil carbon (soilc) has **no age-class growth function**; it is read directly from LPJmL input.

**Growing-stock calibration (new as of 2026-04-20)**: When `s52_growingstock_calib = 1` (default), `preloop.gms:1-118` **overwrites** `pm_carbon_density_secdforest_ac(t_all,j,ac,"vegc")` and `pm_carbon_density_plantation_ac(t_all,j,ac,"vegc")` with FRA 2025-calibrated growth curves, tuning the `k` parameter via regional bisection. Uncalibrated copies are preserved in `pm_carbon_density_secdforest_ac_uncalib` (`start.gms:43`) and `pm_carbon_density_plantation_ac_uncalib` (`start.gms:44`).

🟡 Source: `module_52.md` §2A–C

### 2c. How land modules use these densities to fill vm_carbon_stock

The land modules (32, 35) multiply Module 52's age-class densities by the area held in each age class to compute their contribution to `vm_carbon_stock`. For example:
- Module 35 uses `pm_carbon_density_secdforest_ac` for secondary forest carbon stocks
- Module 32 uses `pm_carbon_density_plantation_ac` for plantation carbon stocks
- Non-age-class land types (crop, past, primforest, urban) use `fm_carbon_density` directly

Module 59 populates the `soilc` slice of `vm_carbon_stock` for all land types.

🟡 Source: `module_52.md` §"Downstream Dependencies", `module_56.md` §12.4

---

## Part 3: Module 52's Single Equation — q52_emis_co2_actual

**Declaration**: `declarations.gms:30`
**Formula** (`equations.gms:16-19`):
```gams
q52_emis_co2_actual(i2,emis_oneoff) ..
  vm_emissions_reg(i2,emis_oneoff,"co2_c") =e=
    sum((cell(i2,j2), emis_land(emis_oneoff,land,c_pools)),
      (pcm_carbon_stock(j2,land,c_pools,"actual")
       - vm_carbon_stock(j2,land,c_pools,"actual"))
      / m_timestep_length);
```

**What this computes**: For each region `i2` and one-off emission source `emis_oneoff` (e.g., secdforest_vegc), it calculates the **annualized CO2-C emission** as the carbon stock decline from the previous timestep to the current timestep, divided by the timestep length (years).

**Key points**:
- `pcm_carbon_stock` is always the `"actual"` stock type
- `vm_carbon_stock` is also `"actual"` here (fixed by this equation)
- Positive result → net carbon loss → emission; negative result → net carbon gain → sequestration
- Output written to `vm_emissions_reg(i,emis_oneoff,"co2_c")` — declared in Module 56

🟡 Source: `module_52.md` §3, §"Key Equations Explained"

---

## Part 4: Two Pathways into Module 56 — An Architectural Split

This is the most important architectural point. `vm_carbon_stock` enters Module 56's cost calculation via **two independent pathways**, and they are used for different purposes:

### Pathway A: Via vm_emissions_reg (indirect — from q52_emis_co2_actual)

Module 52's equation writes to `vm_emissions_reg(i,emis_oneoff,"co2_c")`. This feeds **`q56_emis_pricing`** (`equations.gms:12-17`):
```gams
q56_emis_pricing(i2,pollutants,emis_annual) ..
  v56_emis_pricing(i2,emis_annual,pollutants) =e=
    vm_emissions_reg(i2,emis_annual,pollutants);
```
However, this equation handles **annual** (`emis_annual`) emissions — CH4, N2O, and recurring CO2 flows. Land-use-change CO2 (`emis_oneoff`) does **not** flow through this equation.

### Pathway B: Direct carbon stock read (q56_emis_pricing_co2)

For `emis_oneoff` CO2, Module 56 bypasses `vm_emissions_reg` entirely and reads `vm_carbon_stock` **directly** in `equations.gms:19-22`:

```gams
q56_emis_pricing_co2(i2,emis_oneoff) ..
  v56_emis_pricing(i2,emis_oneoff,"co2_c") =e=
    sum((cell(i2,j2), emis_land(emis_oneoff,land,c_pools)),
      (pcm_carbon_stock(j2,land,c_pools,"actual")
       - vm_carbon_stock(j2,land,c_pools,"%c56_carbon_stock_pricing%"))
      / m_timestep_length);
```

This is structurally identical to `q52_emis_co2_actual` but with one critical difference: the current stock type is **`%c56_carbon_stock_pricing%`** (a configuration string), not hardcoded `"actual"`. The default is `"actualNoAcEst"`, which excludes afforestation establishment carbon from pricing to avoid double-counting with the CDR reward.

**Why two equations with nearly the same formula?** `q52_emis_co2_actual` feeds `vm_emissions_reg` for emission reporting and for any non-pricing consumers (e.g., emission constraints, reporting). `q56_emis_pricing_co2` independently computes the quantity for pricing, allowing the pricing stock type to differ from the reporting stock type via `c56_carbon_stock_pricing`.

🟡 Source: `module_56.md` §2.2, §"Architectural Note — Direct Carbon Stock Pathway"

---

## Part 5: From v56_emis_pricing to vm_emission_costs

Once `v56_emis_pricing(i,emis_oneoff,"co2_c")` is computed via Pathway B, it enters the cost chain:

### Step 1: One-off emission costs (q56_emission_cost_oneoff, equations.gms:35-52)

Because land-use-change CO2 is a stock change (one-time within the timestep), its cost uses an annuity factor:

```gams
q56_emission_cost_oneoff(i2,emis_oneoff) ..
  v56_emission_cost(i2,emis_oneoff) =e=
    sum(pollutants,
      v56_emis_pricing(i2,emis_oneoff,pollutants)
      * m_timestep_length
      * sum(ct,
          im_pollutant_prices(ct,i2,pollutants,emis_oneoff)
          * pm_interest(ct,i2) / (1+pm_interest(ct,i2))));
```

The formula: `annualRate × timestepLength × price × r/(1+r)`
- `v56_emis_pricing` is already an annual rate (Tg C/yr)
- `× m_timestep_length` recovers total stock change (mio. tC) for the timestep
- `× price` is USD17MER per Mg C
- `× r/(1+r)` is the annuity-due factor: converts a one-time total cost into an equivalent annual payment over a perpetuity, leveling the comparison with recurring annual emissions

This prevents deforestation from being under-penalized relative to fertilizer use.

🟡 Source: `module_56.md` §2.4

### Step 2: Total emission costs (q56_emission_costs, equations.gms:54-58)

```gams
q56_emission_costs(i2) ..
  vm_emission_costs(i2) =e=
    sum(emis_source, v56_emission_cost(i2,emis_source));
```

`vm_emission_costs(i)` aggregates across all emission sources (one-off + annual). This variable is then passed to **Module 11 (Costs)** where it enters MAgPIE's objective function and is minimized.

🟡 Source: `module_56.md` §2.5

---

## Part 6: What determines whether a given carbon pool is priced

The emission policy matrix `f56_emis_policy` (a binary 0/1 table) multiplies `im_pollutant_prices` in `preloop.gms:84-91`. Under the default `c56_emis_policy = "reddnatveg_nosoil"`, only the following `co2_c` emission sources receive a non-zero price:
- `primforest_vegc`, `primforest_litc`
- `secdforest_vegc`, `secdforest_litc`
- `other_vegc`, `other_litc`
- peatland emissions

Soil carbon (`soilc`), cropland, pasture, and forestry plantation carbon stocks are **not priced** under this default policy.

The default `c56_carbon_stock_pricing = "actualNoAcEst"` also means that afforestation establishment stock changes (age class 0 establishment events) are excluded from the pricing calculation in `q56_emis_pricing_co2` (though they remain in `vm_emissions_reg` via `q52_emis_co2_actual`).

🟡 Source: `module_56.md` §3.7, §5.2

---

## Summary: The Full Chain

```
LPJmL data (lpj_carbon_stocks.cs3)
  → fm_carbon_density [M52 input.gms:16-20]
    → age-class densities via Chapman-Richards [M52 start.gms:17,28,48]
      → optionally calibrated to FRA targets [M52 preloop.gms:45-116, when s52_growingstock_calib=1]
        → land modules (M29, M31, M32, M34, M35) multiply by area
          → vm_carbon_stock [DECLARED M56 declarations.gms:34; POPULATED by land modules]

vm_carbon_stock in optimization:

Path A (emission reporting):
  q52_emis_co2_actual [M52 equations.gms:16-19]:
    (pcm_carbon_stock - vm_carbon_stock["actual"]) / timestep → vm_emissions_reg

Path B (carbon pricing — DIRECT):
  q56_emis_pricing_co2 [M56 equations.gms:19-22]:
    (pcm_carbon_stock - vm_carbon_stock[c56_carbon_stock_pricing]) / timestep → v56_emis_pricing

  q56_emission_cost_oneoff [M56 equations.gms:35-52]:
    v56_emis_pricing × timestep × price × r/(1+r) → v56_emission_cost

  q56_emission_costs [M56 equations.gms:54-58]:
    sum(emis_source, v56_emission_cost) → vm_emission_costs

  vm_emission_costs → Module 11 (Costs) → objective function
```

---

## Docs Wished Existed but Not Found

1. **A diagram or table showing the stock-type dimension (`stockType`) of `vm_carbon_stock`**: What values the `stockType` set contains, which land modules populate which stock types, and how `"actualNoAcEst"` differs from `"actual"` mechanically. The docs state the distinction conceptually but do not detail the set members or which equations write to each type.

2. **An explicit note on execution order between `q52_emis_co2_actual` and `q56_emis_pricing_co2`**: Both equations compute nearly the same quantity from the same variables. The docs explain the split's purpose (different stock types) but do not describe whether GAMS solves these simultaneously or sequentially and whether there is any algebraic redundancy between them within the NLP.

---

## Source Statement

All claims in this answer are sourced from:
- 🟡 `modules/module_52.md` — §§2, 3, "Interface Variables", "Module Dependencies", "Verification Summary"
- 🟡 `modules/module_56.md` — §§2.2, 2.4, 2.5, 3.7, 4.1, 4.2, 5.2, 12.4

No raw `.gms` files were read. This is a docs-only answer. Line numbers cited are from the module docs and were verified at the docs' last verification date (M52: 2026-05-16; M56: 2025-10-13); code changes since then may have shifted them.
