# R29 Q7 / Regression Anchor G2

## Question

Walk through how vm_carbon_stock is computed in Module 52 and where it enters the GHG-policy cost in Module 56. Cite the relevant equations and file:line locations.

---

## Answer

### 1. Declaration site of vm_carbon_stock

`vm_carbon_stock(j, land, c_pools, stockType)` is **declared in Module 56** (`modules/56_ghg_policy/price_aug22/declarations.gms:34`). It is an **interface variable**, not a Module 52 variable. Module 52 reads it; the land modules populate it.

Dimensions:
- `j` — simulation cells
- `land` — land types (crop, past, primforest, secdforest, urban, other, plus plantation pools)
- `c_pools` — carbon pools: vegc (vegetation), litc (litter), soilc (soil)
- `stockType` — stock type, including "actual" and "actualNoAcEst"

The corresponding **previous-timestep** parameter `pcm_carbon_stock(j, land, c_pools, stockType)` is also declared in Module 56 and is updated there each timestep by storing the solved `vm_carbon_stock`.

---

### 2. Who populates vm_carbon_stock

`vm_carbon_stock` is populated by the **land modules** during optimization, not by Module 52 itself. The docs confirm the full roster (`module_56.md`, Section 4.1):

- **Module 29 (Cropland)**: crop-pool carbon — folds in `vm_carbon_stock_croparea` from Module 30
- **Module 30 (Croparea)**: contributes via the separate `vm_carbon_stock_croparea` variable, which Module 29 aggregates in
- **Module 31 (Pasture)**: past carbon
- **Module 32 (Forestry)**: plantation/forestry carbon (vegc + litc pools via age-class densities supplied by M52)
- **Module 34 (Urban)**: urban carbon (fixed to 0)
- **Module 35 (Natural Vegetation)**: primforest, secdforest, and other land carbon
- **Module 59 (SOM)**: soilc pool for all land types

Module 58 (Peatland) does **not** populate `vm_carbon_stock`; its emissions enter via a separate path.

The carbon density values that the land modules use to compute their stocks are supplied by Module 52 as parameters (`fm_carbon_density`, `pm_carbon_density_secdforest_ac`, `pm_carbon_density_plantation_ac`, `pm_carbon_density_other_ac`) — but Module 52 does not write `vm_carbon_stock` directly.

---

### 3. How Module 52 uses vm_carbon_stock (q52_emis_co2_actual)

Module 52 contains **one equation**: `q52_emis_co2_actual`, declared at `declarations.gms:30` and defined at `equations.gms:16-19`.

**Formula** (`equations.gms:16-19`):

```gams
q52_emis_co2_actual(i2,emis_oneoff) ..
  vm_emissions_reg(i2,emis_oneoff,"co2_c") =e=
    sum((cell(i2,j2), emis_land(emis_oneoff,land,c_pools)),
      (pcm_carbon_stock(j2,land,c_pools,"actual")
       - vm_carbon_stock(j2,land,c_pools,"actual"))
      / m_timestep_length);
```

**What it computes**: Annual CO2-equivalent emissions from land-use change, as a **stock-difference divided by timestep length**. When `pcm_carbon_stock > vm_carbon_stock`, carbon was lost, yielding a positive emission. When the opposite holds, the land acted as a sink.

Key components:
- `pcm_carbon_stock(j2,land,c_pools,"actual")` — previous timestep carbon stock (mio. tC), held constant during the current solve
- `vm_carbon_stock(j2,land,c_pools,"actual")` — current timestep carbon stock (mio. tC), determined by land modules during optimization
- `m_timestep_length` — timestep duration in years (defined at `core/macros.gms:51`), converting the stock difference to an annual rate
- `emis_land(emis_oneoff,land,c_pools)` — set mapping emission sources to land types and carbon pools; covers `crop_vegc`, `past_litc`, `secdforest_vegc`, etc. (`core/sets.gms:332-335`)
- `cell(i2,j2)` — aggregates cells to region

**Output**: `vm_emissions_reg(i2,emis_oneoff,"co2_c")` — declared in Module 56 — represents regional CO2 emissions (Tg C per year) from land-use change, tracked separately per emission source (emis_oneoff).

---

### 4. Where vm_carbon_stock enters Module 56 policy costs

There are **two distinct pathways** through which `vm_carbon_stock` enters Module 56's cost accounting. These are separate equations with different purposes.

#### 4a. q52_emis_co2_actual → vm_emissions_reg → NOT used for CO2 pricing

The output of Module 52's equation is `vm_emissions_reg(...,"co2_c")`. However, for the **pricing of CO2 one-off emissions**, Module 56 does NOT route through `vm_emissions_reg`. This is the architectural surprise documented in module_56.md Section 2.2.

#### 4b. q56_emis_pricing_co2: Direct carbon stock pathway (primary CO2 pricing chain)

**File**: `equations.gms:19-22`

```gams
q56_emis_pricing_co2(i2,emis_oneoff) ..
  v56_emis_pricing(i2,emis_oneoff,"co2_c") =e=
    sum((cell(i2,j2), emis_land(emis_oneoff,land,c_pools)),
      (pcm_carbon_stock(j2,land,c_pools,"actual")
       - vm_carbon_stock(j2,land,c_pools,"%c56_carbon_stock_pricing%"))
      / m_timestep_length);
```

CO2 pricing **reads `vm_carbon_stock` directly** — bypassing `vm_emissions_reg` entirely. This is a deliberate design: the pricing calculation uses a configurable `stockType` dimension (`c56_carbon_stock_pricing`), whereas the Module 52 equation always uses "actual". The default value of `c56_carbon_stock_pricing` is "actualNoAcEst", which **excludes afforestation establishment** from pricing to avoid double-counting with CDR rewards (Section 2.2, module_56.md).

Key distinction:
- `q52_emis_co2_actual` always uses `stockType = "actual"` and writes to `vm_emissions_reg` (for reporting and non-CO2 gas routing)
- `q56_emis_pricing_co2` reads `vm_carbon_stock` directly with the configurable pricing stockType

#### 4c. q56_emission_cost_oneoff: Applying the carbon price

`v56_emis_pricing(i2,emis_oneoff,"co2_c")` from step 4b feeds into the cost equation at `equations.gms:45-52`:

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

This multiplies the annualized emission rate by:
- `m_timestep_length` — to reconvert from annual rate back to total timestep emissions
- `im_pollutant_prices(ct,i2,pollutants,emis_oneoff)` — the configured GHG price (USD17MER/Mg), constructed through the multi-stage preloop in `preloop.gms:35-124`
- `pm_interest(ct,i2)/(1 + pm_interest(ct,i2))` — the annuity due factor (infinite horizon), which levels a one-time deforestation cost with recurring annual emission costs

This annuity factor is essential: without it, one-off deforestation costs would appear cheaper than recurring emissions, biasing land use toward deforestation.

#### 4d. q56_emission_costs: Entry into objective function

**File**: `equations.gms:56-58`

```gams
q56_emission_costs(i2) ..
  vm_emission_costs(i2) =e=
    sum(emis_source, v56_emission_cost(i2,emis_source));
```

`vm_emission_costs(i)` is then passed to **Module 11 (Costs)**, where it enters the objective function and drives land-use optimization.

---

### 5. Full chain summary

```
Land modules (29,31,32,34,35,59)
  → populate vm_carbon_stock(j,land,c_pools,stockType)   [declared in M56 declarations.gms:34]

Module 52 equations.gms:16-19  [q52_emis_co2_actual]
  → reads vm_carbon_stock (stockType="actual") and pcm_carbon_stock
  → writes vm_emissions_reg(i,emis_oneoff,"co2_c")       [reporting + non-CO2 gas routing]

Module 56 equations.gms:19-22  [q56_emis_pricing_co2]
  → reads vm_carbon_stock DIRECTLY (stockType=c56_carbon_stock_pricing, default "actualNoAcEst")
  → reads pcm_carbon_stock
  → computes v56_emis_pricing(i,emis_oneoff,"co2_c")

Module 56 equations.gms:45-52  [q56_emission_cost_oneoff]
  → v56_emis_pricing × m_timestep_length × im_pollutant_prices × r/(1+r)
  → produces v56_emission_cost(i,emis_oneoff)

Module 56 equations.gms:56-58  [q56_emission_costs]
  → sums all v56_emission_cost(i,emis_source) → vm_emission_costs(i)

Module 11 (Costs)
  → vm_emission_costs enters objective function
```

---

### 6. Key architectural nuance (regression anchor G2)

The most important thing to get right for G2: **`vm_carbon_stock` is declared in Module 56, not Module 52**. Module 52 calculates carbon density parameters and CO2 emissions for reporting (via `q52_emis_co2_actual`), but the interface variable `vm_carbon_stock` lives in M56's declarations. For **pricing purposes**, Module 56 reads `vm_carbon_stock` directly in `q56_emis_pricing_co2` rather than routing through M52's `vm_emissions_reg`. The two equations (`q52_emis_co2_actual` and `q56_emis_pricing_co2`) are structurally parallel — both compute a stock difference divided by timestep length — but use different `stockType` values and serve different roles (reporting vs. pricing).

---

### Sources

- 🟡 `modules/module_52.md` — Section 3 (CO2 Emission Calculation), Section 4 (Interface Variables), execution sequence
- 🟡 `modules/module_56.md` — Sections 2.1-2.5, Section 4, Section 8.1 (Recursive time-step carbon accounting)
- Source files were not read this session; line numbers are from documentation last verified 2026-05-16 (M52) and 2025-10-13 (M56)
