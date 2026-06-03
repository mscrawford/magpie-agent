# Q1 Answer: Socioeconomic Drivers → Food Demand → Production (Default Configuration)

**Question**: Trace how Module 09 (socioeconomic drivers) propagates into food demand and then into production in MAgPIE's default configuration. Specifically: (a) the default SSP/driver scenario and where it is set; (b) which variables/parameters carry population and per-capita income from M09 into M15; (c) how per-capita food demand becomes total demand entering M16 and M17.

---

## Active Realizations (Step 1c check)

All three modules involved have single or confirmed-default realizations per `config/default.cfg`:

| Module | Active Realization | cfg line |
|--------|-------------------|----------|
| 09_drivers | `aug17` | `cfg$gms$drivers <- "aug17"` |
| 15_food | `anthro_iso_jun22` | `cfg$gms$food <- "anthro_iso_jun22"` |
| 16_demand | `sector_may15` | `cfg$gms$demand <- "sector_may15"` |

Module 09 has only one realization (`aug17`). Module 15's `anthro_iso_jun22` and Module 16's `sector_may15` are both defaults. All claims below are for these realizations.

---

## (a) Default SSP/Driver Scenario and Where It Is Set

**Active scenario**: SSP2 for population, GDP (both MER and PPP), and Physical Activity Level.

This is set in two places:

**1. `config/default.cfg` (user-facing configuration)**:
```
cfg$gms$c09_pop_scenario  <- "SSP2"    # def = SSP2
cfg$gms$c09_gdp_scenario  <- "SSP2"    # def = SSP2
cfg$gms$c09_pal_scenario  <- "SSP2"    # def = SSP2
```
🟡 (module_09.md §2.2, confirmed against default.cfg)

These are GAMS `$setglobal` strings, internally referenced as `%c09_pop_scenario%`, `%c09_gdp_scenario%`, and `%c09_pal_scenario%`.

**2. An additional `sm_fix_SSP2` override applies through 2025**: All scenarios, regardless of the c09 settings, use SSP2 values until the year `sm_fix_SSP2 = 2025`. This is declared in `modules/09_drivers/aug17/input.gms:22` and enforced in `preloop.gms:36-56`. The practical effect in default runs is that scenarios are SSP2 throughout—both before 2025 (forced) and after 2025 (selected). Divergence from SSP2 only occurs when a non-SSP2 scenario is explicitly chosen.

**Summary**: The default run is SSP2 from start to finish. The scenario names are declared in `default.cfg` and the switching logic lives in `modules/09_drivers/aug17/preloop.gms:36-56`. 🟡

---

## (b) Variables and Parameters Carrying Population and Income from M09 into M15

Module 09 produces **interface variables** in its `preloop.gms` that are consumed throughout the run. Module 15 reads six of them. All are declared in `modules/09_drivers/aug17/declarations.gms`.

### Population variables

| Variable | Dimensions | Units | Where M09 populates it | Where M15 reads it |
|----------|------------|-------|------------------------|--------------------|
| `im_pop(t_all,i)` | time × 12 MAgPIE regions | mio. people / yr | `preloop.gms:41,50` | `equations.gms:57` — RHS of `q15_food_demand` |
| `im_pop_iso(t_all,iso)` | time × 249 ISO countries | mio. people / yr | `preloop.gms:40,49` | `presolve.gms` (ISO-level demand calculations) |
| `im_demography(t_all,iso,sex,age)` | time × iso × M/F × 21 age groups | mio. people / yr | `preloop.gms:39,48` | `equations.gms:258-261` — `q15_intake` food-intake equation |

**Population propagation detail**: The critical link to MAgPIE's optimization constraint is `im_pop(t,i)`, the regional-level total. It appears on the right-hand side of `q15_food_demand` (`equations.gms:10-14`):

```gams
q15_food_demand(i2,kfo) ..
    (vm_dem_food(i2,kfo) + sum(ct, f15_household_balanceflow(ct,i2,kfo,"dm")))
    * sum(ct,(fm_nutrition_attributes(ct,kfo,"kcal") * 10**6)) =g=
    sum(ct, im_pop(ct,i2) * p15_kcal_pc_calibrated(ct,i2,kfo)) * 365
```

The inequality enforces: (food-use tonnes × kcal content) ≥ (population × daily-kcal-per-capita × 365 days). Population thus directly determines the minimum food supply MAgPIE must provide.

`im_demography` is used more deeply inside the standalone food demand model to compute energy requirements by sex and age group in `q15_intake`.

### Income variables

| Variable | Dimensions | Units | Where M09 populates it | Where M15 reads it |
|----------|------------|-------|------------------------|--------------------|
| `im_gdp_pc_ppp_iso(t_all,iso)` | time × iso | USD17PPP / cap / yr | `preloop.gms:23-27` | `equations.gms:105` — `q15_budget` (real income calculation) |
| `im_gdp_pc_mer_iso(t_all,iso)` | time × iso | USD17MER / cap / yr | `preloop.gms:29-33` | M15 uses MER for price-conversion (conditional on `s15_elastic_demand = 1`) |

**Income propagation detail**: `im_gdp_pc_ppp_iso` enters the budget constraint of the standalone food demand model (`q15_budget`, `equations.gms:48-52`):

```gams
q15_budget(iso) ..
    v15_income_pc_real_ppp_iso(iso) =e=
    sum(kfo, v15_kcal_regr(iso,kfo) * 365
    * (i15_prices_initial_kcal(iso,kfo) - sum((ct,prev_iter15), p15_prices_kcal(ct,iso,kfo,prev_iter15))))
    + sum(ct, im_gdp_pc_ppp_iso(ct,iso) + p15_tax_recycling(ct,iso)) + v15_income_balance(iso);
```

GDP per capita PPP sets the real income baseline. Income then drives:
- BMI distribution shares (via saturation functions in `q15_regr_bmi_shr`, `equations.gms:71-76`)
- Dietary composition factors — livestock share, processed food share, overconsumption ratio (via `q15_regr`, `equations.gms:169-173`)

Both regressions use Michaelis-Menten-style saturation curves: demand components rise with income but approach asymptotes. Higher GDP per capita → higher livestock share, higher overconsumption (waste), higher processed food share. 🟡

### Physical inactivity

| Variable | Dimensions | Used for |
|----------|------------|---------|
| `im_physical_inactivity(t_all,iso,sex,age)` | time × iso × sex × age | Physical Activity Level (PAL) → caloric energy requirements in `q15_intake` |

M09 populates this from `f09_physical_inactivity.cs3` (WHO data) via `preloop.gms:39,48`.

---

## (c) Per-Capita Food Demand → Total Demand → M16 and M17

The propagation runs through three distinct steps.

### Step 1: Standalone food demand model produces per-capita demand (M15 presolve)

The standalone NLP model (`m15_food_demand`) runs in M15's `presolve.gms` before MAgPIE's optimization. Its output is `v15_kcal_regr(iso,kfo)` — per capita demand in kcal/cap/day by ISO country and food product. This is aggregated and calibrated to historical FAO observations (when `s15_calibrate = 1`, which is the default per `default.cfg`) to produce:

**`p15_kcal_pc_calibrated(t,i,kfo)`** — calibrated per-capita demand in kcal/cap/day at the MAgPIE region level. 🟡 (module_15.md §3.C)

This parameter is the bridge between the standalone food demand model and MAgPIE's optimization.

Note: In the default configuration `s15_elastic_demand = 0` (confirmed in `default.cfg`), demand is **fixed** — the standalone model runs once per timestep and its output is exogenous to the optimizer.

### Step 2: Per-capita demand × population → total food supply constraint (M15 → optimizer via q15_food_demand)

The equation `q15_food_demand` (M15, `equations.gms:10-14`) is the **only connection** between the standalone demand model and MAgPIE's optimization. It enforces:

```
vm_dem_food(i, kfo) [mio. tDM/yr]  ≥  im_pop(t,i) × p15_kcal_pc_calibrated(t,i,kfo) × 365
                                        ÷ (fm_nutrition_attributes(kfo,"kcal") × 10⁶)
```

(Balance flow adjustments `f15_household_balanceflow` are also incorporated.)

The optimization variable `vm_dem_food(i,kfo)` is declared in M15's `declarations.gms:13-15` (positive variable, mio. tDM/yr). The inequality (=g=) allows overproduction but not underproduction. 🟡 (module_15.md §2.A)

### Step 3: vm_dem_food enters M16 as one component of total supply (M15 → M16)

Module 16 (`sector_may15`) is a **demand aggregation hub**. It does not re-derive food demand; it takes `vm_dem_food` as a given input and adds it to feed, processing, material, bioenergy, seed, and waste demands to compute total supply requirements. Specifically:

- **Crops** (`q16_supply_crops`, `equations.gms:19-29`):
  `vm_supply(i,kcr) =e= vm_dem_food(i,kcr) + vm_dem_feed + vm_dem_processing + vm_dem_material + vm_dem_bioen + vm_dem_seed + v16_dem_waste + f16_domestic_balanceflow`

- **Livestock products** (`q16_supply_livestock`, `equations.gms:31-38`):
  `vm_supply(i,kap) =e= vm_dem_food(i,kap) + vm_dem_feed + v16_dem_waste + vm_dem_material + f16_domestic_balanceflow`

- **Secondary products** (`q16_supply_secondary`, `equations.gms:40-49`): also includes `vm_dem_food`.

**Output**: `vm_supply(i,kall)` — total regional supply requirement, declared in M16 `declarations.gms:11`. 🟡 (module_16.md §Equations 1–3)

`vm_supply` feeds Module 21 (Trade), which enforces the global food balance:
`vm_prod_reg(i,k) + vm_import(i,k) - vm_export(i,k) ≥ vm_supply(i,k)`

### Step 4: M16 → M17 connection (indirect, via M21 → production decisions)

Module 17 (`flexreg_apr16`) is a **pure spatial aggregator** — it aggregates cell-level production to regional totals via:

```gams
q17_prod_reg(i2,k) .. vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k));
```
(`equations.gms:10-11`)

Module 17 does **not** read `vm_dem_food` or `vm_supply` directly. The production-demand link is enforced in Module 21 (Trade), which requires `vm_prod_reg + vm_import - vm_export ≥ vm_supply`. The optimizer then determines how much to produce at cell level (Module 30 for crops, Module 31 for pasture, etc.) to satisfy that constraint. 🟡 (module_17.md §1.1)

---

## Summary Trace (Default SSP2 Configuration)

```
M09 preloop (once, before optimization timestep begins)
  f09_pop_iso.csv × SSP2 → im_pop_iso(t,iso), im_pop(t,i)      [population]
  f09_gdp_ppp_iso.csv × SSP2 → im_gdp_pc_ppp_iso(t,iso)         [income PPP]
  f09_physical_inactivity.cs3 × SSP2 → im_physical_inactivity    [PAL]
  f09_demography.cs3 × SSP2 → im_demography(t,iso,sex,age)       [age/sex structure]
                  ↓ (all six im_ variables passed to M15)
M15 presolve (runs standalone NLP before optimizer)
  im_gdp_pc_ppp_iso → v15_income_pc_real_ppp_iso (q15_budget)
    → BMI distribution (q15_regr_bmi_shr, q15_bmi_shr_*)
    → Dietary composition shares (q15_regr): livestockshare, processedshare, vegfruitshare
    → v15_kcal_regr(iso,kfo) per capita demand by ISO + product
  Aggregated + calibrated to FAO (s15_calibrate=1):
    → p15_kcal_pc_calibrated(t,i,kfo)  [kcal/cap/day at region level]
                  ↓
M15 constraint (inside MAgPIE optimization)
  q15_food_demand: vm_dem_food(i,kfo) × nutrition ≥ im_pop(t,i) × p15_kcal_pc_calibrated × 365
  [per-capita × regional population → total tonnes]
                  ↓
M16 aggregation (inside MAgPIE optimization)
  q16_supply_crops / _livestock / _secondary:
    vm_supply(i,kall) = vm_dem_food + vm_dem_feed + ... (all demand sectors summed)
                  ↓
M21 Trade: vm_prod_reg + imports - exports ≥ vm_supply
                  ↓
M17: vm_prod_reg(i,k) = Σ vm_prod(j,k)  [cell production aggregated to region]
  (cell-level production optimization in M30/31 etc. drives vm_prod)
```

---

## Key Variable/Parameter Name Summary

| Name | Type | Where declared | Purpose in the chain |
|------|------|----------------|----------------------|
| `im_pop_iso(t,iso)` | interface param | M09 `declarations.gms:10` | ISO population, used in M15 presolve |
| `im_pop(t,i)` | interface param | M09 `declarations.gms:11` | Regional population, RHS of q15_food_demand |
| `im_gdp_pc_ppp_iso(t,iso)` | interface param | M09 `declarations.gms:29` | Income driver in q15_budget |
| `im_gdp_pc_mer_iso(t,iso)` | interface param | M09 `declarations.gms:16` | MER income (used in elastic-demand price conversion) |
| `im_demography(t,iso,sex,age)` | interface param | M09 `declarations.gms:34` | Age/sex energy requirements in q15_intake |
| `im_physical_inactivity(t,iso,sex,age)` | interface param | M09 `declarations.gms:33` | PAL → caloric needs |
| `p15_kcal_pc_calibrated(t,i,kfo)` | parameter | M15 `declarations.gms` | Output of standalone model; calibrated per-capita demand |
| `vm_dem_food(i,kfo)` | optimization variable | M15 `declarations.gms:13-15` | Total food supply (mio. tDM/yr); connects M15 → M16 |
| `q15_food_demand` | equation | M15 `equations.gms:10-14` | Converts per-capita × population → minimum supply requirement |
| `vm_supply(i,kall)` | optimization variable | M16 `declarations.gms:11` | Total regional demand; connects M16 → M21 → M17 |
| `vm_prod_reg(i,k)` | optimization variable | M17 `declarations.gms:10` | Regional production (aggregated from cells by q17_prod_reg) |

---

## Epistemic Notes

- All claims are 🟡 (documented) — sourced from AI documentation read this session. No `.gms` files were opened.
- `default.cfg` was read directly to confirm active realizations and scenario settings.
- The `im_gdp_pc_mer_iso` is listed as a M15 consumer in module_09.md §5.2, but module_15.md makes clear it is primarily relevant when `s15_elastic_demand = 1` (default is 0). In the default run, the income-demand pathway flows almost entirely through `im_gdp_pc_ppp_iso`.
- Line numbers for M15 equations are from a doc last verified 2026-03-06; for M17 from 2025-10-12. These may have drifted if code has changed since.

---

## Closing Source Statement

- 🟡 `modules/module_09.md` (Last verified: 2025-10-13)
- 🟡 `modules/module_15.md` (Last verified: 2026-03-06)
- 🟡 `modules/module_16.md`
- 🟡 `modules/module_17.md` (Last verified: 2025-10-12)
- Direct read: `config/default.cfg` — confirmed realizations and scenario settings
