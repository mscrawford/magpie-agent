# vm_carbon_stock: computation in Module 52 and GHG-policy costs in Module 56

**Active realizations** (verified against `<magpie-root>/config/default.cfg`):
- Module 52: `normal_dec17` (default and only realization)
- Module 56: `price_aug22` (default and only realization)

---

## Part 1: Declaration and population of vm_carbon_stock (MANDATE 18 compliance)

**vm_carbon_stock** is DECLARED in Module 56, not Module 52 (`modules/56_ghg_policy/price_aug22/declarations.gms:34`). Its full signature is:

```
vm_carbon_stock(j, land, c_pools, stockType)   [mio. tC]
```

Module 52 only READS this variable; it does not declare it. The producers (modules that populate vm_carbon_stock during optimization) are:

| Module | Land types populated |
|--------|---------------------|
| 29 (Cropland, `detail_apr24`) | crop pool (folds in vm_carbon_stock_croparea from M30) |
| 31 (Pasture, `endo_jun13`) | past |
| 32 (Forestry, `dynamic_may24`) | plant_pri, plant_sec |
| 34 (Urban) | urban (fixed to 0) |
| 35 (Natveg, `pot_forest_may24`) | primforest, secdforest, other |
| 59 (SOM, `cellpool_jan23`) | soilc pool for all land types |

Module 30 (Croparea) populates a separate `vm_carbon_stock_croparea`, which Module 29 folds into its vm_carbon_stock equations. Module 58 (Peatland) does NOT populate vm_carbon_stock; it uses its own emission path. (Sources: 🟡 `modules/module_56.md:580-585`, `module_52.md:422-424`)

Each land module uses Module 52's carbon density parameters as inputs for their own carbon-stock equations. The key density parameters Module 52 supplies:

- `fm_carbon_density(t_all, j, land, c_pools)` — LPJmL-derived base densities for all land types (tC/ha), loaded from `lpj_carbon_stocks.cs3` (`module_52.md:480-484`, `input.gms:18`)
- `pm_carbon_density_secdforest_ac(t_all, j, ac, ag_pools)` — age-class vegetation carbon for secondary forests, computed via Chapman-Richards in `start.gms:28,31`, then overwritten by bisection calibration in `preloop.gms:71-73` when `s52_growingstock_calib = 1` (default ON, `input.gms:46`) (`module_52.md:446-452`)
- `pm_carbon_density_plantation_ac(t_all, j, ac, ag_pools)` — same for plantations, from `start.gms:17,20`, overwritten in `preloop.gms:114-116` (`module_52.md:467-471`)
- `pm_carbon_density_other_ac(t_all, j, ac, ag_pools)` — other land, from `start.gms:48,51`; NOT calibrated (`module_52.md:460-464`)

🟢 These are what land modules use to build vm_carbon_stock. Module 52 is the carbon-density supplier; the land modules are the stock calculators.

---

## Part 2: The previous-timestep carry-forward (pcm_carbon_stock)

`pcm_carbon_stock(j, land, c_pools, stockType)` — declared also in M56 — holds the PREVIOUS timestep's realized carbon stock. Its update is split by pool:

- Above-ground pools (vegc, litc) carried forward in **Module 56** postsolve: `modules/56_ghg_policy/price_aug22/postsolve.gms:8`
- Soil pool (soilc) carried forward in **Module 59** postsolve: `modules/59_som/cellpool_jan23/postsolve.gms:13`

(The soilc carry-forward was added in develop commit 931db85c4, 2026-06-25; before that, soilc in `pcm_carbon_stock` was frozen at preloop initialization.) (Source: 🟡 `module_52.md:429-431`, `module_56.md:581`)

---

## Part 3: Module 52's single optimization equation — q52_emis_co2_actual

Module 52 has **one equation** that fires during optimization (Source: 🟡 `module_52.md:36`):

**q52_emis_co2_actual** (`modules/52_carbon/normal_dec17/equations.gms:16-19`):

```gams
q52_emis_co2_actual(i2, emis_oneoff) ..
  vm_emissions_reg(i2, emis_oneoff, "co2_c") =e=
    sum((cell(i2,j2), emis_land(emis_oneoff, land, c_pools)),
      (pcm_carbon_stock(j2, land, c_pools, "actual")
       - vm_carbon_stock(j2, land, c_pools, "actual"))
      / m_timestep_length);
```

**Mechanics:**

- **LHS**: `vm_emissions_reg(i2, emis_oneoff, "co2_c")` — regional CO2-C emissions, annualized, in Tg C/yr. Declared in Module 56.
- **Numerator**: `pcm_carbon_stock(...,"actual") - vm_carbon_stock(...,"actual")` — positive when carbon is lost (emission), negative when gained (sequestration).
- **Denominator**: `m_timestep_length` — converts stock change (mio. tC) to annual flux (mio. tC/yr = Tg C/yr), since 1 mio. tC = 1 Tg C.
- **emis_oneoff**: One-off land-use change sources — the set spans all land-pool combinations: `crop_vegc`, `crop_litc`, `crop_soilc`, `past_vegc`, ... `other_soilc` (7 land types × 3 pools, minus those excluded by the `emis_land` mapping) (`module_52.md:329-338`).
- **emis_land**: Maps each `emis_oneoff` label to its `(land, c_pools)` pair (e.g., `crop_vegc → (crop, vegc)`).

M52 reads `vm_carbon_stock` with `stockType = "actual"` specifically. The output `vm_emissions_reg(emis_oneoff, "co2_c")` is the reporting variable — it records actual CO2 flux for the post-solve and for `magpie4::reportEmissions()`. (Source: 🟡 `module_52.md:300-327`, verified formula matches `equations.gms:16-19` ✅)

---

## Part 4: Module 56's parallel, direct read of vm_carbon_stock — q56_emis_pricing_co2

**Critical architectural point (MANDATE 21):** M52 and M56 are PARALLEL readers of `vm_carbon_stock`, NOT a serial M52→M56 producer-consumer chain. M56 reads `vm_carbon_stock` DIRECTLY for its pricing equation and does NOT route through M52's `vm_emissions_reg` output for the LULUCF CO2 cost.

**q56_emis_pricing_co2** (`modules/56_ghg_policy/price_aug22/equations.gms:19-22`):

```gams
q56_emis_pricing_co2(i2, emis_oneoff) ..
  v56_emis_pricing(i2, emis_oneoff, "co2_c") =e=
    sum((cell(i2,j2), emis_land(emis_oneoff, land, c_pools)),
      (pcm_carbon_stock(j2, land, c_pools, "actual")
       - vm_carbon_stock(j2, land, c_pools, "%c56_carbon_stock_pricing%"))
      / m_timestep_length);
```

This is the **pricing** pathway. It uses the same stock-difference formula as M52's q52_emis_co2_actual with one important difference: the current-period carbon stock is indexed by `%c56_carbon_stock_pricing%` instead of `"actual"`. The switch `c56_carbon_stock_pricing` defaults to `"actualNoAcEst"`, which excludes afforestation establishment carbon from pricing (avoiding double-counting with the CDR reward mechanism `q56_reward_cdr_aff`). (Source: 🟡 `module_56.md:86-116`)

The output `v56_emis_pricing(i2, emis_oneoff, "co2_c")` is a module-internal variable (v56_ prefix, not vm_) that feeds the cost equations within Module 56.

For completeness: annual (recurring) emissions — CH4, N2O, and any annual-category CO2 — take the parallel pathway via **q56_emis_pricing** (`equations.gms:15-17`), which reads `vm_emissions_reg(i2, emis_annual, pollutants)`. Since M52's q52_emis_co2_actual writes into `emis_oneoff` (not `emis_annual`), M52's `vm_emissions_reg` output does NOT feed M56's annual-emission pricing equation. (`module_56.md:54-73`)

---

## Part 5: The cost chain — from v56_emis_pricing to the objective function

**q56_emission_cost_oneoff** (`equations.gms:45-52`): converts the one-off CO2 pricing amount into an annualized cost using an infinite-horizon annuity factor:

```gams
q56_emission_cost_oneoff(i2, emis_oneoff) ..
  v56_emission_cost(i2, emis_oneoff) =e=
    sum(pollutants,
      v56_emis_pricing(i2, emis_oneoff, pollutants)
      * m_timestep_length
      * sum(ct, im_pollutant_prices(ct, i2, pollutants, emis_oneoff)
               * pm_interest(ct, i2) / (1 + pm_interest(ct, i2))));
```

The `m_timestep_length × price × r/(1+r)` structure converts an annualized stock-change flux back to a per-timestep aggregate (× timestep_length), prices it, and levels it with recurring costs via the annuity factor r/(1+r). Without this, one-time deforestation events would be penalized less than recurring emissions of equivalent magnitude. (Source: 🟡 `module_56.md:165-211`)

`im_pollutant_prices(ct, i2, pollutants, emis_oneoff)` — the configured GHG price in USD17MER/Mg (per tonne) — is built during preloop via 8+ sequential stages in `preloop.gms:35-123`: scenario selection, development-state scaling (default OFF), temporal fader (default OFF), CO2 reduction factor (default = 1), historical zeroing (<= `sm_fix_SSP2`, i.e., <=2025), CH4/N2O caps, and emission-policy matrix multiplication. The emission-policy matrix `f56_emis_policy` (44 policies × pollutants × sources) zeros out prices for source-gas combinations not covered by the active policy. Default policy `reddnatveg_nosoil` prices `co2_c` for primforest, secdforest, and other land (vegc + litc only; no soilc, no cropland, no pasture CO2). (Source: 🟡 `module_56.md:474-514`, `module_56_notes.md:18-21`)

**q56_emission_costs** (`equations.gms:56-58`): aggregates all sources:

```gams
q56_emission_costs(i2) ..
  vm_emission_costs(i2) =e=
    sum(emis_source, v56_emission_cost(i2, emis_source));
```

`vm_emission_costs(i)` is declared in Module 56 (`declarations.gms:39`) and provided to **Module 11 (Costs)**, where it enters the objective function. Module 11 sums all cost components, and MAgPIE minimizes total cost — so a higher `vm_emission_costs` from carbon-stock loss creates an incentive to avoid deforestation or expand forests. (Source: 🟡 `module_56.md:214-238`, `module_56.md:564-568`)

The CDR reward pathway (`vm_reward_cdr_aff`) is a separate Module 56 output that also goes to Module 11 with a negative sign, incentivizing afforestation. It uses `vm_cdr_aff` from Module 32, NOT vm_carbon_stock directly. (Source: 🟡 `module_56.md:242-316`)

---

## Summary of the full chain

```
Land modules (M29/31/32/34/35/59)
  → vm_carbon_stock [declared in M56; populated by land modules using M52 densities]

M52 (parallel reader 1):
  vm_carbon_stock("actual") + pcm_carbon_stock →
  q52_emis_co2_actual (equations.gms:16-19) →
  vm_emissions_reg(emis_oneoff, "co2_c")  [reporting / magpie4 use]

M56 (parallel reader 2, INDEPENDENT of M52's output for CO2 cost):
  vm_carbon_stock("%c56_carbon_stock_pricing%") + pcm_carbon_stock →
  q56_emis_pricing_co2 (equations.gms:19-22) →
  v56_emis_pricing(emis_oneoff, "co2_c")  [pricing quantity]
  → q56_emission_cost_oneoff (equations.gms:45-52) ×  im_pollutant_prices × annuity_factor →
  v56_emission_cost(emis_oneoff)
  → q56_emission_costs (equations.gms:56-58): sum over all emis_source →
  vm_emission_costs(i)
  → Module 11 (Costs) → objective function → land-use optimization
```

M56 also reads `vm_emissions_reg(emis_annual, pollutants)` in `q56_emis_pricing` for CH4/N2O; M52's one-off CO2 contribution to `vm_emissions_reg` is NOT the pathway into M56's cost equation — that pathway reads vm_carbon_stock directly (MANDATE 21, verifiers.md).

---

**Source statement:**
Based on 🟡 `modules/module_52.md` and 🟡 `modules/module_56.md` documentation, supplemented by 🟡 `modules/module_56_notes.md` warnings and 🟡 `agent/helpers/verifiers.md` MANDATEs 18 and 21. Active realizations verified against `<magpie-root>/config/default.cfg`. No raw GAMS code read this session; for high-stakes modifications, verify equation line numbers against `../modules/52_carbon/normal_dec17/equations.gms` and `../modules/56_ghg_policy/price_aug22/equations.gms` before acting.
