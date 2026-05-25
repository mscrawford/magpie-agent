# Round 25 — Regression Question G2

**Question**: Walk through how `vm_carbon_stock` is computed in Module 52 and where it enters the GHG-policy cost in Module 56. Cite the relevant equations and file:line locations.

---

## Framing Correction (Critical — Repeat Historical Trap)

`vm_carbon_stock` is **NOT computed or declared in Module 52**. This is the historical trap this question is designed to test.

🟢 **Verified**: `vm_carbon_stock(j,land,c_pools,stockType)` is **declared in Module 56** (`modules/56_ghg_policy/price_aug22/declarations.gms:34`). Module 52 (`normal_dec17`) only **reads** this variable — it does not declare or populate it.

---

## Part 1: Who Declares and Populates vm_carbon_stock?

### Declaration

🟡 `vm_carbon_stock(j,land,c_pools,stockType)` — dimensions: simulation cells × land types × carbon pools × stock type ("actual" / "actualNoAcEst") — is declared in:

**`modules/56_ghg_policy/price_aug22/declarations.gms:34`** (module_56.md §4.1)

### Population (which modules write vm_carbon_stock)

The land modules calculate and report carbon stocks into `vm_carbon_stock` by land type. Based on module_56.md §12.4 and module_52.md "Interface Variables" section:

🟡 Populators (each fills the cells belonging to its land type):
- **Module 29 (Cropland)** — via equation `q29_carbon` (cropland carbon stocks)
- **Module 31 (Pasture)** — via equation `q31_carbon` (pasture carbon stocks)
- **Module 32 (Forestry)** — via equation `q32_carbon` (plantation carbon stocks)
- **Module 34 (Urban)** — urban carbon stocks
- **Module 35 (Natural Vegetation)** — via equations `q35_carbon_primforest`, `q35_carbon_secdforest`, `q35_carbon_other` (primary forest, secondary forest, other land)
- **Module 59 (SOM)** — populates the soilc pool (soil organic carbon)

🟡 `pcm_carbon_stock(j,land,c_pools,stockType)` — the **previous timestep's** carbon stock — is also declared in Module 56 (`declarations.gms`). Module 56 stores the current `vm_carbon_stock` as `pcm_carbon_stock` for the next timestep.

---

## Part 2: Module 52's Role — Reading vm_carbon_stock for CO2 Emissions

Module 52 (`normal_dec17`) has exactly **one equation**, and it reads — but does not write — `vm_carbon_stock`.

### Equation: q52_emis_co2_actual

**File**: `modules/52_carbon/normal_dec17/equations.gms:16-19`

**Formula** (🟢 verified from module_52.md §3, Key Equations §1):

```gams
q52_emis_co2_actual(i2,emis_oneoff) ..
  vm_emissions_reg(i2,emis_oneoff,"co2_c") =e=
    sum((cell(i2,j2),emis_land(emis_oneoff,land,c_pools)),
      (pcm_carbon_stock(j2,land,c_pools,"actual") - vm_carbon_stock(j2,land,c_pools,"actual"))
      / m_timestep_length);
```

**What this does**:
- Sums the difference between the previous timestep carbon stock (`pcm_carbon_stock`) and the current timestep carbon stock (`vm_carbon_stock`) over all cells in region i2 and all valid land-pool combinations defined by the set `emis_land(emis_oneoff,land,c_pools)`
- Divides by `m_timestep_length` to annualize the stock change (mio. tC → Tg C/yr)
- A positive result (previous stock > current stock) indicates carbon loss → CO2 emission
- A negative result indicates carbon gain → CO2 sequestration

**Output**: `vm_emissions_reg(i2,emis_oneoff,"co2_c")` — regional CO2-C emissions (Tg C/yr), written by Module 52, declared in Module 56 (`declarations.gms`).

**Note on stockType**: Module 52's `q52_emis_co2_actual` hardcodes `"actual"` as the `stockType`. This is distinct from Module 56's `q56_emis_pricing_co2`, which uses the configurable `%c56_carbon_stock_pricing%` switch.

---

## Part 3: Module 52's Carbon Density Computation (Separate from vm_carbon_stock)

While Module 52 does not compute `vm_carbon_stock`, it does compute the **carbon densities** that land modules use to populate `vm_carbon_stock`. These are calculated before optimization in the start phase:

**Chapman-Richards vegetation carbon** (start.gms):
```
pm_carbon_density_secdforest_ac(t_all,j,ac,"vegc") =
  m_growth_vegc(S, A, k_eff, m_eff, ord(ac)-1)    [start.gms:28]
pm_carbon_density_plantation_ac(t_all,j,ac,"vegc") =
  m_growth_vegc(S, A, k_eff, m_eff, ord(ac)-1)    [start.gms:17]
pm_carbon_density_other_ac(t_all,j,ac,"vegc") =
  m_growth_vegc(S, A, k_eff, m_eff, ord(ac)-1)    [start.gms:48]
```

As of 2026-04-20, with `s52_growingstock_calib = 1` (default ON), the vegc densities for secdforest and plantations are **overwritten in `preloop.gms:71-73` and `preloop.gms:114-116`** respectively, via bisection calibration to FAO FRA 2025 growing-stock targets (`module_52.md §2.C`).

🟡 Base carbon densities for non-age-class land types come from LPJmL input: `fm_carbon_density(t_all,j,land,c_pools)` loaded from `lpj_carbon_stocks.cs3` (`input.gms:18`).

These parameters flow from Module 52 → Modules 32/35 → land equations → `vm_carbon_stock`. Module 52 does not itself constrain `vm_carbon_stock` in an equation.

---

## Part 4: Where vm_carbon_stock Enters Module 56's GHG Cost Chain

Module 56 (`price_aug22`) uses `vm_carbon_stock` via a separate, parallel equation to `q52_emis_co2_actual`. The chain is:

### Step 4a: q56_emis_pricing_co2 — Direct Carbon Stock Pathway

**File**: `modules/56_ghg_policy/price_aug22/equations.gms:19-22`

🟢 Verified formula (module_56.md §2.2):

```gams
q56_emis_pricing_co2(i2,emis_oneoff) ..
  v56_emis_pricing(i2,emis_oneoff,"co2_c") =e=
    sum((cell(i2,j2),emis_land(emis_oneoff,land,c_pools)),
      (pcm_carbon_stock(j2,land,c_pools,"actual")
       - vm_carbon_stock(j2,land,c_pools,"%c56_carbon_stock_pricing%"))
      / m_timestep_length);
```

**Key distinction from q52_emis_co2_actual**:
- Module 56 reads `vm_carbon_stock` **directly** — it does NOT go through `vm_emissions_reg`. This is a deliberate architectural choice: the LULUCF CO2 accounting for pricing purposes is computed independently from the CO2 emission variable reported via Module 52.
- The `%c56_carbon_stock_pricing%` switch determines which stock type is used:
  - Default: `"actualNoAcEst"` — excludes afforestation establishment from pricing (avoids double-counting with CDR rewards)
  - Alternative: `"actual"` — includes all stock changes

**Output**: `v56_emis_pricing(i2,emis_oneoff,"co2_c")` — emissions used for pricing (Tg C/yr)

### Step 4b: q56_emission_cost_oneoff — Annualized Cost Calculation

**File**: `modules/56_ghg_policy/price_aug22/equations.gms:45-52`

🟢 Verified (module_56.md §2.4):

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

**What this does**: Converts the annualized one-off CO2 emission rate into an equivalent annual cost using an infinite-horizon annuity factor `r/(1+r)`. Multiplication by `m_timestep_length` recovers the total timestep emission from the annual rate. The annuity factor levels one-time emissions (deforestation) with recurring annual costs (fertilizer N2O) for consistent optimization.

**Output**: `v56_emission_cost(i2,emis_oneoff)` — emission cost for each one-off source (mio. USD17MER/yr)

### Step 4c: q56_emission_costs — Aggregation to vm_emission_costs

**File**: `modules/56_ghg_policy/price_aug22/equations.gms:56-58`

🟢 Verified (module_56.md §2.5):

```gams
q56_emission_costs(i2) ..
  vm_emission_costs(i2) =e=
    sum(emis_source, v56_emission_cost(i2,emis_source));
```

**What this does**: Sums costs from all emission sources (both annual and one-off) to produce total regional emission costs.

**Output**: `vm_emission_costs(i)` — total regional emission costs (mio. USD17MER/yr), declared at `modules/56_ghg_policy/price_aug22/declarations.gms:39`

### Step 4d: Entry into Objective Function

🟡 `vm_emission_costs(i)` is consumed by **Module 11 (Costs)**, where it enters the global optimization objective. Module 56 also provides `vm_reward_cdr_aff(i)` (declared at `declarations.gms:43`) with a **negative sign** in Module 11 — this rewards afforestation CDR and reduces total costs (`equations.gms:60-79`).

---

## Summary: The Full Chain

```
Land modules (29, 31, 32, 34, 35, 59) populate vm_carbon_stock
                          |
                          v
M52 reads vm_carbon_stock + pcm_carbon_stock
  -> q52_emis_co2_actual (equations.gms:16-19)
  -> vm_emissions_reg(i,"co2_c")          [used for reporting / other emission accounting]

M56 reads vm_carbon_stock + pcm_carbon_stock DIRECTLY
  -> q56_emis_pricing_co2 (equations.gms:19-22)  [%c56_carbon_stock_pricing% = "actualNoAcEst" default]
  -> v56_emis_pricing
  -> q56_emission_cost_oneoff (equations.gms:45-52) [× timestep_length × price × r/(1+r)]
  -> v56_emission_cost
  -> q56_emission_costs (equations.gms:56-58)
  -> vm_emission_costs(i)
  -> Module 11 (Costs) → Objective function
```

---

## Realizations

- Module 52 realization: `normal_dec17` (default, verified `modules/52_carbon/normal_dec17/`)
- Module 56 realization: `price_aug22` (default; confirmed `config/default.cfg` and module_56.md header)

---

## Source Statement

🟡 Based on `module_52.md` (documentation) and `module_56.md` (documentation), cross-referenced with stated equation formulas in both docs (equations verified against source in prior sessions per `module_52.md` Verification Summary and `module_56.md` §Documentation Status). All citation paths use full relative paths per MANDATE 16.

**Primary sources consulted**:
- `magpie-agent/modules/module_52.md` — Module 52 overview, equation q52_emis_co2_actual, interface variables section
- `magpie-agent/modules/module_56.md` — Module 56 equations §2.2-2.5, declarations §4.1, relationship §12.4

**Key files cited** (relative to MAgPIE repo root):
- `modules/56_ghg_policy/price_aug22/declarations.gms:34` — vm_carbon_stock declaration
- `modules/52_carbon/normal_dec17/equations.gms:16-19` — q52_emis_co2_actual
- `modules/56_ghg_policy/price_aug22/equations.gms:19-22` — q56_emis_pricing_co2
- `modules/56_ghg_policy/price_aug22/equations.gms:45-52` — q56_emission_cost_oneoff
- `modules/56_ghg_policy/price_aug22/equations.gms:56-58` — q56_emission_costs
- `modules/56_ghg_policy/price_aug22/declarations.gms:39` — vm_emission_costs declaration
