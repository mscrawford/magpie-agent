# G2: vm_carbon_stock computation in Module 52 and its entry into Module 56 GHG policy costs

---

## Architectural note: declaration vs. computation vs. population

A critical disambiguation before the walkthrough:

- `vm_carbon_stock(j,land,c_pools,stockType)` is **DECLARED in Module 56** (`modules/56_ghg_policy/price_aug22/declarations.gms:34`), not Module 52.
- It is **POPULATED by the land modules** (29, 31, 32, 34, 35, 59), each writing the carbon stocks for their land type.
- It is **READ by Module 52** as an input to equation `q52_emis_co2_actual`.
- It is **READ by Module 56** in equation `q56_emis_pricing_co2` for the carbon pricing calculation.

Module 52's own contribution to the carbon-stock system is twofold: (a) it provides the carbon density parameters that the land modules use to compute their entries into `vm_carbon_stock`, and (b) it runs the single equation `q52_emis_co2_actual` that produces `vm_emissions_reg(...,"co2_c")`. Module 52 does not itself write to `vm_carbon_stock`.

---

## Part 1: How vm_carbon_stock is built up (the density → stock pipeline)

### Step 1a: LPJmL carbon densities (Module 52 input.gms)

Module 52 loads base carbon densities from LPJmL:

```
fm_carbon_density(t_all,j,land,c_pools)   [tC per ha]
```

Source: `lpj_carbon_stocks.cs3`, loaded at `module_52.md → input.gms:16-20`. Three carbon pools: `vegc` (vegetation), `litc` (litter), `soilc` (soil). Climate-scenario handling at `input.gms:22-23` (cc / nocc / nocc_hist).

### Step 1b: Age-class carbon densities (Module 52 start.gms)

For forests and other land that age over time, Module 52 computes age-class-specific densities before each optimization. These are calculated in `start.gms` using two macros defined in `core/macros.gms`:

**Vegetation carbon (vegc) — Chapman-Richards equation** (`macros.gms:18`):
```
m_growth_vegc(S,A,k,m,ac) = S + (A-S)*(1-exp(-k*(ac*5)))^m
```
- S = start carbon (0 tC/ha for new plantations/forests; `start.gms:9`)
- A = asymptotic (mature) carbon = `fm_carbon_density(t_all,j,"secdforest","vegc")`
- k, m = climate-weighted growth parameters: `sum(clcl, pm_climate_class(j,clcl)*f52_growth_par(clcl,par,type))` where `pm_climate_class` comes from Module 45 (`start.gms:17`)
- ac = age class (integer), so `ac*5` gives years

Applied at:
- Plantations: `pm_carbon_density_plantation_ac(t_all,j,ac,"vegc")` at `start.gms:17`
- Secondary forests: `pm_carbon_density_secdforest_ac(t_all,j,ac,"vegc")` at `start.gms:28`
- Other land: `pm_carbon_density_other_ac(t_all,j,ac,"vegc")` at `start.gms:48`

**Litter carbon (litc) — linear 20-year equilibrium** (`macros.gms:20`):
```
m_growth_litc_soilc(start,end,ac) =
  (start + (end-start)*1/20*ac*5)$(ac <= 20/5) + end$(ac > 20/5)
```
Applied to litc pools for the same three land types at `start.gms:20, 31, 51`.

**Note on growing-stock calibration:** As of 2026-04-20, when `s52_growingstock_calib = 1` (default ON; `input.gms:46`), `preloop.gms` runs a bisection calibration against FAO FRA 2025 targets and **overwrites** `pm_carbon_density_secdforest_ac(...,"vegc")` (`preloop.gms:71-73`) and `pm_carbon_density_plantation_ac(...,"vegc")` (`preloop.gms:114-116`). Uncalibrated copies are preserved in `pm_carbon_density_secdforest_ac_uncalib` and `pm_carbon_density_plantation_ac_uncalib` for new-establishment use cases.

Soil carbon (soilc) has no age-class growth function — it is read directly from `fm_carbon_density` and is not age-class-specific (`module_52.md` Section 4, "Soil carbon (soilc) NOT age-class-specific").

### Step 1c: Land modules populate vm_carbon_stock

Using the densities provided by Module 52, the land modules each compute carbon stocks for their land type and write to `vm_carbon_stock(j,land,c_pools,"actual")`:

| Module | Land type written |
|--------|------------------|
| 29 (Cropland) | crop (folds in `vm_carbon_stock_croparea` from Module 30) |
| 31 (Pasture) | past |
| 32 (Forestry) | plant (plantations) |
| 34 (Urban) | urban (fixed to 0) |
| 35 (Natural Vegetation) | primforest, secdforest, other |
| 59 (SOM) | soilc pool for all land types |

`vm_carbon_stock` is declared in Module 56 at `modules/56_ghg_policy/price_aug22/declarations.gms:34`.

The previous timestep's value is stored in `pcm_carbon_stock(j,land,c_pools,stockType)`, also declared in Module 56 (`declarations.gms`), and updated by Module 56 at the end of each timestep.

---

## Part 2: Module 52's CO2 emission equation

### Equation q52_emis_co2_actual (`equations.gms:16-19`)

```gams
q52_emis_co2_actual(i2,emis_oneoff) ..
  vm_emissions_reg(i2,emis_oneoff,"co2_c") =e=
    sum((cell(i2,j2),emis_land(emis_oneoff,land,c_pools)),
      (pcm_carbon_stock(j2,land,c_pools,"actual") - vm_carbon_stock(j2,land,c_pools,"actual"))
      / m_timestep_length);
```

**What this computes**: Annual CO2-C emissions (Tg C/yr) as the per-cell carbon stock loss between the previous timestep (`pcm_carbon_stock`) and the current timestep (`vm_carbon_stock`), annualized by dividing by `m_timestep_length` (years).

- Positive value (previous stock > current): carbon loss = emission
- Negative value (current stock > previous): carbon gain = sequestration
- `emis_land(emis_oneoff,land,c_pools)` is the set that maps emission-source labels (e.g., `secdforest_vegc`) to (land type, carbon pool) combinations; defined at `core/sets.gms:332-335`
- `emis_oneoff` covers crop/past/primforest/secdforest/urban/other/forestry for each of vegc, litc, soilc (`core/sets.gms:314-318`)
- **Output**: `vm_emissions_reg(i,emis_oneoff,"co2_c")` — declared in Module 56 (`declarations.gms`)

This is Module 52's only equation (the module has 1 equation total; `module_52.md` module structure section).

---

## Part 3: How vm_carbon_stock enters Module 56 GHG policy costs

### The dual CO2 pathway (critical architectural point)

CO2 from land-use change enters Module 56 via **two parallel paths** that serve different purposes:

| Path | Equation | Input | Output | Purpose |
|------|----------|-------|--------|---------|
| M52 emission path | `q52_emis_co2_actual` | `pcm_carbon_stock`, `vm_carbon_stock` | `vm_emissions_reg(...,"co2_c")` | Emission accounting (used by `q56_emis_pricing` for annual gases) |
| M56 direct CO2 path | `q56_emis_pricing_co2` | `pcm_carbon_stock`, `vm_carbon_stock` | `v56_emis_pricing(...,"co2_c")` | CO2 pricing (bypasses `vm_emissions_reg`) |

The M56 notes file (`module_56_notes.md:34`) captures this: "M56 cost chain is `q56_emis_pricing_co2` → `v56_emis_pricing` → `q56_emission_cost_oneoff` → `vm_emission_costs`."

### Equation q56_emis_pricing_co2 (`equations.gms:19-22`)

```gams
q56_emis_pricing_co2(i2,emis_oneoff) ..
  v56_emis_pricing(i2,emis_oneoff,"co2_c") =e=
    sum((cell(i2,j2),emis_land(emis_oneoff,land,c_pools)),
      (pcm_carbon_stock(j2,land,c_pools,"actual") - vm_carbon_stock(j2,land,c_pools,"%c56_carbon_stock_pricing%"))
      / m_timestep_length);
```

This equation **directly reads `vm_carbon_stock`** — the same stock variable written by land modules and declared in M56. It does NOT route through `vm_emissions_reg`. The key difference from `q52_emis_co2_actual` is the dimension on `vm_carbon_stock`: it uses `c56_carbon_stock_pricing` (a config string switch) instead of the hard-coded `"actual"`. The default value is `"actualNoAcEst"`, which excludes afforestation establishment-phase carbon from pricing to avoid double-counting with the CDR reward mechanism.

This computes `v56_emis_pricing(i,emis_oneoff,"co2_c")` — an internal Module 56 variable holding CO2 emissions that are subject to pricing.

### Equation q56_emission_cost_oneoff (`equations.gms:45-52`)

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

This converts the annualized CO2 emission rate back to a total-timestep emission (`× m_timestep_length`), multiplies by the GHG price (`im_pollutant_prices`), and applies the annuity factor `r/(1+r)` to level the one-time deforestation cost against recurring annual emission costs. The annuity factor treats deforestation as a perpetual opportunity cost.

`im_pollutant_prices(ct,i,pollutants,emis_source)` is configured in `preloop.gms:35-123` through up to 8 sequential stages (scenario selection, development-state scaling, temporal faders, CO2 reduction factor, historical zeroing, CH4/N2O caps, emission policy matrix, and afforestation price construction). The policy matrix stage at `preloop.gms:84-91` multiplies prices by `f56_emis_policy`, which is a 0/1 matrix selecting which gas-source combinations are priced. Under the default `c56_emis_policy = "reddnatveg_nosoil"`, CO2 is priced for primforest_vegc, primforest_litc, secdforest_vegc, secdforest_litc, other_vegc, other_litc, and peatland (but NOT cropland, pasture, or forestry CO2, and NOT soilc).

### Equation q56_emission_costs (`equations.gms:56-58`)

```gams
q56_emission_costs(i2) ..
  vm_emission_costs(i2) =e=
    sum(emis_source, v56_emission_cost(i2,emis_source));
```

Aggregates costs from all emission sources (annual + one-off, all gases) into the regional total `vm_emission_costs(i)`. This is the variable that Module 11 (Costs) puts into the objective function. Minimizing `vm_emission_costs` is what creates the economic incentive for land-use-change mitigation in the optimization.

---

## Summary: the full chain

```
LPJmL densities (fm_carbon_density, input.gms:16-20)
  ↓ start.gms:17,28,48 (Chapman-Richards) / preloop.gms:71,114 (calibration)
pm_carbon_density_{secdforest,plantation,other}_ac
  ↓ consumed by M32, M35 to compute carbon stocks for each ha
vm_carbon_stock(j,land,c_pools,"actual")      [declared M56 decl.gms:34; populated M29/31/32/34/35/59]
  ↓ read by M52 equations.gms:16
q52_emis_co2_actual  →  vm_emissions_reg(i,emis_oneoff,"co2_c")   [accounting]
  ↓ ALSO read directly by M56 equations.gms:19
q56_emis_pricing_co2  →  v56_emis_pricing(i,emis_oneoff,"co2_c")  [pricing, uses actualNoAcEst]
  ↓ equations.gms:45-52
q56_emission_cost_oneoff  →  v56_emission_cost(i,emis_oneoff)     [× price × r/(1+r)]
  ↓ equations.gms:56-58
q56_emission_costs  →  vm_emission_costs(i)                        [→ M11 objective function]
```

The `vm_carbon_stock` variable is the pivot: it is the physical quantity that both the emission accounting equation in Module 52 and the pricing equation in Module 56 independently read, which is why both modules produce similar-looking stock-difference expressions with the same cell/emis_land summation structure.

---

## Source statement

All claims are 🟡 documented from:
- `module_52.md` (primary) — equations, start.gms, preloop.gms, input.gms, interface variable documentation
- `module_56.md` (primary) — equations q56_emis_pricing_co2, q56_emission_cost_oneoff, q56_emission_costs; preloop configuration stages; declarations
- `module_56_notes.md` — declaration/population disambiguation, cost-chain lesson (2026-05-25)

No `.gms` files were opened in this session. All equation text is reproduced from the documentation's "verified" blocks, which were cross-referenced against source code at the times noted in each module's "Last Verified" footer (M52: 2026-05-16; M56: 2025-10-13).

---

## Doc gap noted

One doc that would be useful: a short cross-module reference ("carbon stock bridge note") in `cross_module/carbon_balance_conservation.md` that explicitly shows the dual-pathway architecture — the fact that `vm_carbon_stock` feeds both `q52_emis_co2_actual` (accounting) and `q56_emis_pricing_co2` (pricing) simultaneously, and why the two expressions are nearly identical but use different `stockType` arguments. Currently this distinction appears only as a section note in `module_56.md:90-92` and is easy to miss when reading either module doc in isolation.
