# Anchor G2: vm_carbon_stock computation in M52 and entry into M56 GHG-policy cost

**Sources**: module_52.md, module_56.md (AI documentation, magpie-agent)
**Status**: 🟡 Documented (from AI docs this session; code not independently re-read)

---

## Part 1 — How vm_carbon_stock is populated (Module 56 declares it; land modules fill it)

`vm_carbon_stock(j, land, c_pools, stockType)` is **declared in Module 56** (`declarations.gms:34`) as the central interface variable for carbon stocks (mio. tC). Module 52 does **not** compute it directly. Instead, each land module computes the carbon stock for its own land type and writes into this shared variable during the optimization:

| Module | Land types populated |
|--------|---------------------|
| M29 (Cropland) | crop pool (folds in `vm_carbon_stock_croparea` from M30) |
| M31 (Pasture) | past |
| M32 (Forestry) | plantation (plant\_sec, plant\_pri) |
| M34 (Urban) | urban (fixed to 0) |
| M35 (Natural Veg) | primforest, secdforest, other |
| M59 (SOM) | soilc pool for all land types |

The carbon density parameters that each land module uses when computing those stocks flow from Module 52:
- `fm_carbon_density(t_all, j, land, c_pools)` — LPJmL-derived base densities, loaded in M52 `input.gms:16-20` from `lpj_carbon_stocks.cs3`
- `pm_carbon_density_secdforest_ac(t_all, j, ac, ag_pools)` — Chapman-Richards vegc growth curve, computed in M52 `start.gms:28,31`, then overwritten by the growing-stock calibration in `preloop.gms:71-73` (when `s52_growingstock_calib = 1`, default ON)
- `pm_carbon_density_plantation_ac(t_all, j, ac, ag_pools)` — analogous for plantations, `start.gms:17,20`, overwritten at `preloop.gms:114-116`
- `pm_carbon_density_other_ac(t_all, j, ac, ag_pools)` — other land, `start.gms:48,51` (NOT calibrated)

So `vm_carbon_stock` is the aggregation point filled by land modules using carbon-density parameters supplied by M52.

---

## Part 2 — Module 52's only optimization-phase equation: q52_emis_co2_actual

Module 52 has exactly **one equation** (`declarations.gms:30`, `equations.gms:16-19`):

```gams
q52_emis_co2_actual(i2, emis_oneoff) ..
  vm_emissions_reg(i2, emis_oneoff, "co2_c") =e=
    sum((cell(i2,j2), emis_land(emis_oneoff, land, c_pools)),
      (pcm_carbon_stock(j2, land, c_pools, "actual")
       - vm_carbon_stock(j2, land, c_pools, "actual"))
      / m_timestep_length);
```

- `pcm_carbon_stock` — previous timestep carbon stock (mio. tC), declared in M56 `declarations.gms`
- `vm_carbon_stock` — current timestep stock (mio. tC), filled by land modules as above
- `m_timestep_length` — 5 or 10 years, macro defined in `core/macros.gms:51`
- `emis_land(emis_oneoff, land, c_pools)` — mapping set linking emission-source labels (e.g., `secdforest_vegc`) to land types and carbon pools

The equation computes **annual CO2-C emission from land-use change as a stock-difference flow**. A positive result (stock fell) is an emission; a negative result (stock grew) is sequestration. Output is `vm_emissions_reg(i, emis_oneoff, "co2_c")` in Tg C/yr.

`pcm_carbon_stock` is updated each timestep by Module 56 in its postsolve: the current `vm_carbon_stock` is stored as `pcm_carbon_stock` for the next period.

---

## Part 3 — Two pathways from vm_carbon_stock into M56 GHG-policy cost

### Pathway A — Direct re-computation for pricing (q56_emis_pricing_co2)

Module 56 does **not** rely on `vm_emissions_reg` for CO2 pricing. Instead it recomputes the stock difference directly in `equations.gms:19-22`:

```gams
q56_emis_pricing_co2(i2, emis_oneoff) ..
  v56_emis_pricing(i2, emis_oneoff, "co2_c") =e=
    sum((cell(i2,j2), emis_land(emis_oneoff, land, c_pools)),
      (pcm_carbon_stock(j2, land, c_pools, "actual")
       - vm_carbon_stock(j2, land, c_pools, "%c56_carbon_stock_pricing%"))
      / m_timestep_length);
```

This is deliberately parallel to `q52_emis_co2_actual` but uses `c56_carbon_stock_pricing` (switch, default `"actualNoAcEst"`) rather than hard-coding `"actual"`. The `"actualNoAcEst"` type excludes afforestation establishment age classes from the stock entering the pricing formula, avoiding double-counting with the CDR reward.

This is the **direct pathway**: `vm_carbon_stock` → `v56_emis_pricing(i, emis_oneoff, "co2_c")`.

### Pathway B — Indirect via vm_emissions_reg for annual pollutants

For annual gases (CH4, N2O, and annual CO2), Module 56 uses `q56_emis_pricing` (`equations.gms:15-17`):

```gams
q56_emis_pricing(i2, pollutants, emis_annual) ..
  v56_emis_pricing(i2, emis_annual, pollutants) =e=
    vm_emissions_reg(i2, emis_annual, pollutants);
```

CO2 from land-use change goes through Pathway A, not this equation.

---

## Part 4 — From v56_emis_pricing to vm_emission_costs (the cost chain)

### One-off emissions (deforestation) — q56_emission_cost_oneoff (`equations.gms:45-52`)

```gams
q56_emission_cost_oneoff(i2, emis_oneoff) ..
  v56_emission_cost(i2, emis_oneoff) =e=
    sum(pollutants,
      v56_emis_pricing(i2, emis_oneoff, pollutants)
      * m_timestep_length
      * sum(ct,
          im_pollutant_prices(ct, i2, pollutants, emis_oneoff)
          * pm_interest(ct, i2) / (1 + pm_interest(ct, i2))));
```

The annuity factor `r/(1+r)` converts the one-time stock-change emission into an equivalent annual cost, levelling it against recurring annual emissions. Units: Tg C/yr * yr * USD/Mg * (dimensionless) = mio. USD/yr.

### Annual emissions — q56_emission_cost_annual (`equations.gms:29-33`)

```gams
q56_emission_cost_annual(i2, emis_annual) ..
  v56_emission_cost(i2, emis_annual) =e=
    sum(pollutants,
      v56_emis_pricing(i2, emis_annual, pollutants)
        * sum(ct, im_pollutant_prices(ct, i2, pollutants, emis_annual)));
```

### Aggregation — q56_emission_costs (`equations.gms:56-58`)

```gams
q56_emission_costs(i2) ..
  vm_emission_costs(i2) =e=
    sum(emis_source, v56_emission_cost(i2, emis_source));
```

`vm_emission_costs(i)` is declared in M56 `declarations.gms:39` and flows to **Module 11 (Costs)**, where it enters the objective function as a positive cost term.

---

## Part 5 — Which emission sources are actually priced (policy matrix gate)

`im_pollutant_prices` is constructed in `preloop.gms:35-123` from the price scenario, then multiplied element-wise by `f56_emis_policy(c56_emis_policy, pollutants, emis_source)`. Under the **default policy `reddnatveg_nosoil`**, the entries set to 1 for `co2_c` are: `primforest_vegc`, `primforest_litc`, `secdforest_vegc`, `secdforest_litc`, `other_vegc`, `other_litc`, and peatland. Cropland, pasture, and forestry (plantation) carbon pools have 0 entries under this policy, so their stock changes generate no pricing cost.

---

## Summary of the full chain

```
Land modules (M29, M31, M32, M34, M35, M59)
  → populate vm_carbon_stock(j, land, c_pools, stockType)
      using fm_carbon_density / pm_carbon_density_*_ac from M52

M52 equations.gms:16-19 (q52_emis_co2_actual)
  → vm_emissions_reg(i, emis_oneoff, "co2_c")
  [used for reporting; NOT the direct pricing input for CO2]

M56 equations.gms:19-22 (q56_emis_pricing_co2)
  → reads pcm_carbon_stock and vm_carbon_stock directly
  → v56_emis_pricing(i, emis_oneoff, "co2_c")

M56 equations.gms:45-52 (q56_emission_cost_oneoff)
  → v56_emission_cost(i, emis_oneoff)
  [applies carbon price × annuity factor]

M56 equations.gms:56-58 (q56_emission_costs)
  → vm_emission_costs(i)  [declared declarations.gms:39]

Module 11 (Costs)
  → objective function
```

**Key design point**: Module 56 deliberately bypasses `vm_emissions_reg` for CO2 pricing (Pathway A) to gain control over which `stockType` enters the pricing formula via `c56_carbon_stock_pricing`. The `vm_emissions_reg` route (Pathway B) is used only for annual non-CO2 pollutants.

---

**Sources**: module_52.md (especially sections 3, 4, and equation walkthrough at lines 300-334, 774-835); module_56.md (sections 2.2, 2.3, 2.4, 2.5, and 3.7); no raw GAMS code read this session — line numbers are from doc citations verified against source at their respective doc-update dates.
