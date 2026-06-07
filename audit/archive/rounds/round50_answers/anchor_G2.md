# Anchor Question G2: vm_carbon_stock computation in Module 52 and its entry into GHG-policy cost in Module 56

**Sources**: `modules/module_52.md`, `modules/module_56.md`

---

## Part 1: How vm_carbon_stock is populated (Module 52 context)

`vm_carbon_stock(j,land,c_pools,stockType)` is declared in **Module 56** (`declarations.gms:34`), not Module 52. Module 52 is a consumer (reader) of this variable — it does not write to it. Instead, the land modules populate it:

- Module 29 (cropland) — crop pool, folding in `vm_carbon_stock_croparea` from Module 30
- Module 31 (pasture) — pasture carbon
- Module 32 (forestry) — plantation/forestry carbon
- Module 34 (urban) — fixed to 0
- Module 35 (natural vegetation) — primforest, secdforest, other land
- Module 59 (SOM) — soilc pool for all land types

Module 56 also tracks the previous timestep's value as `pcm_carbon_stock(j,land,c_pools,stockType)` for use in emission equations.

The **carbon densities** that drive what goes into `vm_carbon_stock` originate from Module 52 as follows:

### 1a. Base carbon densities (exogenous)

Parameter: `fm_carbon_density(t_all,j,land,c_pools)` (tC/ha)
Source: LPJmL output file `lpj_carbon_stocks.cs3` (Module 52 `input.gms:18`)
Dimensions: time, simulation cell, land type (crop/past/primforest/secdforest/urban/other), carbon pool (vegc/litc/soilc)

Climate scenario modifies this at load time (`input.gms:22-23`): under `nocc`, all years are fixed at 1995 values; under `nocc_hist`, fixed after `sm_fix_cc`.

### 1b. Age-class carbon densities (calculated in start phase)

Module 52 computes age-class-specific densities in `start.gms` for three land types, which downstream land modules (32 and 35) use to calculate their contributions to `vm_carbon_stock`:

**Vegetation carbon — Chapman-Richards equation** (`core/macros.gms:18`):
```
m_growth_vegc(S,A,k,m,ac) = S + (A-S)*(1-exp(-k*(ac*5)))^m
```
- S = start carbon density (0 for new stands, `start.gms:9`)
- A = LPJmL asymptote (mature secdforest vegc)
- k, m = climate-weighted parameters from `f52_growth_par.csv` (`input.gms:40`)

Applied to produce:
- `pm_carbon_density_plantation_ac(t_all,j,ac,"vegc")` — `start.gms:17`
- `pm_carbon_density_secdforest_ac(t_all,j,ac,"vegc")` — `start.gms:28`
- `pm_carbon_density_other_ac(t_all,j,ac,"vegc")` — `start.gms:48`

**Litter carbon — linear growth** (`core/macros.gms:20`):
```
m_growth_litc_soilc(start,end,ac) = (start + (end-start)*1/20*ac*5)$(ac<=20/5) + end$(ac>20/5)
```
Applied to litc pool only (soilc is NOT age-class-specific; read directly from LPJmL):
- `pm_carbon_density_plantation_ac(t_all,j,ac,"litc")` — `start.gms:20`
- `pm_carbon_density_secdforest_ac(t_all,j,ac,"litc")` — `start.gms:31`
- `pm_carbon_density_other_ac(t_all,j,ac,"litc")` — `start.gms:51`

**Growing-stock calibration (as of 2026-04-20)**: When `s52_growingstock_calib = 1` (default, `input.gms:46`), `preloop.gms:71-73` overwrites `pm_carbon_density_secdforest_ac(t_all,j,ac,"vegc")` with a calibrated Chapman-Richards growth curve tuned to match FAO FRA 2025 growing-stock targets via bisection (25 iterations; interval `[0.001, s52_k_high_secdf=0.1]`). Plantation vegc is similarly overwritten at `preloop.gms:114-116` (interval `[0.001, s52_k_high_plant=0.15]`). The uncalibrated values are preserved as `pm_carbon_density_secdforest_ac_uncalib` and `pm_carbon_density_plantation_ac_uncalib` (`start.gms:43-44`) for afforestation/NDC/tree-cover use cases that represent new establishment rather than existing managed forest.

### 1c. The one CO2 equation in Module 52

Module 52 uses `vm_carbon_stock` (and `pcm_carbon_stock`) as **inputs** to its single equation:

**Equation `q52_emis_co2_actual`** (`equations.gms:16-19`):
```gams
q52_emis_co2_actual(i2,emis_oneoff) ..
  vm_emissions_reg(i2,emis_oneoff,"co2_c") =e=
    sum((cell(i2,j2),emis_land(emis_oneoff,land,c_pools)),
      (pcm_carbon_stock(j2,land,c_pools,"actual")
       - vm_carbon_stock(j2,land,c_pools,"actual"))
      / m_timestep_length);
```

- `pcm_carbon_stock` is the previous timestep's stock (mio. tC)
- `vm_carbon_stock` is the current timestep's stock (mio. tC)
- The difference, divided by `m_timestep_length`, gives an annual CO2-C flow (Tg C/yr)
- Positive when carbon is lost (deforestation); negative when carbon is gained (afforestation/regrowth)
- Output: `vm_emissions_reg(i,emis_oneoff,"co2_c")` — regional CO2 emissions by one-off source, declared in Module 56

The `emis_land` mapping set links each `emis_oneoff` label (e.g., `secdforest_vegc`) to a specific land type and carbon pool (`core/sets.gms:332-335`).

---

## Part 2: How vm_carbon_stock enters GHG-policy cost in Module 56

Module 56 (`price_aug22`) has two parallel pathways for CO2 emissions entering cost calculations. The key architectural point is that **one-off (land-use-change) CO2 is NOT routed through `vm_emissions_reg`** — it is computed directly from `vm_carbon_stock` inside Module 56 itself.

### 2a. Equation q56_emis_pricing_co2 (direct carbon-stock pathway)

**`equations.gms:19-22`**:
```gams
q56_emis_pricing_co2(i2,emis_oneoff) ..
  v56_emis_pricing(i2,emis_oneoff,"co2_c") =e=
    sum((cell(i2,j2),emis_land(emis_oneoff,land,c_pools)),
      (pcm_carbon_stock(j2,land,c_pools,"actual")
       - vm_carbon_stock(j2,land,c_pools,"%c56_carbon_stock_pricing%"))
      / m_timestep_length);
```

This intentionally **bypasses `vm_emissions_reg`**. Module 56 re-derives the CO2 flow directly from the carbon stock difference. The switch `c56_carbon_stock_pricing` (default `actualNoAcEst`) selects which stock type enters; `actualNoAcEst` excludes afforestation establishment carbon from pricing to avoid double-counting with the CDR reward.

Note: Module 52's equation `q52_emis_co2_actual` also computes a stock-difference CO2 flow but writes to `vm_emissions_reg`. That output is used by reporting and Module 56's annual-emission pathway (Section 2b), but the **one-off CO2 pricing in Module 56 uses its own re-computation from `vm_carbon_stock`**, not `vm_emissions_reg`.

### 2b. Equation q56_emis_pricing (annual emissions pathway)

**`equations.gms:15-17`**:
```gams
q56_emis_pricing(i2,pollutants,emis_annual) ..
  v56_emis_pricing(i2,emis_annual,pollutants) =e=
    vm_emissions_reg(i2,emis_annual,pollutants);
```

This routes recurring emissions (CH4, N2O, annual CO2) through `vm_emissions_reg`. CO2 from one-off sources (deforestation, land conversion) takes the `q56_emis_pricing_co2` path above, not this one.

### 2c. Equation q56_emission_cost_oneoff (annualized cost)

**`equations.gms:45-52`**:
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

The annuity factor `r/(1+r)` converts a one-time carbon loss into an equivalent infinite-horizon annual cost. `m_timestep_length` converts the annual emission rate back to a timestep total. `im_pollutant_prices` is the configured GHG price (USD17MER/Mg), built in preloop (`preloop.gms:35-123`) through 8 sequential configuration stages (price-scenario selection, development-state scaling, temporal fader, CO2 reduction factor, historical zeroing, CH4/N2O caps, policy-matrix multiplication, afforestation price foresight).

The policy matrix (`f56_emis_policy`, `preloop.gms:84-91`) is a 0/1 filter that determines which `emis_oneoff × pollutant` combinations carry a non-zero price. Under the default `reddnatveg_nosoil` policy, `co2_c` entries are 1 for `primforest_vegc`, `primforest_litc`, `secdforest_vegc`, `secdforest_litc`, `other_vegc`, `other_litc`, and peatland; cropland, pasture, and forestry (plantation) CO2 and all soil carbon (`soilc`) are excluded.

### 2d. Equation q56_emission_costs (aggregation to objective)

**`equations.gms:56-58`**:
```gams
q56_emission_costs(i2) ..
  vm_emission_costs(i2) =e=
    sum(emis_source, v56_emission_cost(i2,emis_source));
```

`vm_emission_costs(i)` (mio. USD17MER/yr) aggregates costs from all emission sources and is passed to **Module 11 (Costs)**, where it enters MAgPIE's objective function. The optimizer minimizes total costs, creating incentives to avoid carbon-stock-reducing land use when carbon prices are active.

---

## Summary of the vm_carbon_stock → cost chain

```
Land modules (29,31,32,34,35,59)
  populate vm_carbon_stock(j,land,c_pools,stockType)   [declared in M56]

Module 56 stores it as pcm_carbon_stock for the next timestep

q56_emis_pricing_co2 (M56 equations.gms:19-22):
  v56_emis_pricing(i,emis_oneoff,"co2_c")
    = Σ (pcm_carbon_stock - vm_carbon_stock) / m_timestep_length

q56_emission_cost_oneoff (M56 equations.gms:45-52):
  v56_emission_cost(i,emis_oneoff)
    = v56_emis_pricing × m_timestep_length
      × im_pollutant_prices × r/(1+r)   [annuity factor]

q56_emission_costs (M56 equations.gms:56-58):
  vm_emission_costs(i) = Σ v56_emission_cost(i,emis_source)

Module 11 (Costs):
  vm_emission_costs → objective function → minimized by optimizer
```

Module 52's role is to supply the **carbon density inputs** that land modules use when computing `vm_carbon_stock`, and to compute `vm_emissions_reg` for the reporting and annual-emission pathways — it does not directly write `vm_carbon_stock` or enter cost calculations.

---

**Documentation sources**: `modules/module_52.md` (equations.gms:16-19; start.gms:17,20,28,31,48,51; preloop.gms:71-73,114-116; declarations.gms:9-13; input.gms:18,22-23,40,46-48), `modules/module_56.md` (equations.gms:15-22,29-33,45-58; preloop.gms:35-91; declarations.gms:9,34,39)
