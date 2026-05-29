# Question: SSP Driver Data Flow — Module 09 to Modules 15/16 and Module 14

## Summary of the Chain

SSP driver data flows from external CSV/CS3 input files loaded by Module 09
through a set of interface parameters into the standalone food demand model
(Module 15), the demand aggregator (Module 16), and the yield-scaling equations
(Module 14). The chain has distinct shapes for food demand vs. yields, and SSP
data does NOT directly enter Module 14's equations — it reaches yields only
indirectly, via Module 09 -> Module 13 -> Module 14.

---

## Stage 1: Module 09 Loads and Publishes Driver Data

**Source files** (loaded in `modules/09_drivers/aug17/input.gms`):

| File | Parameter | Content | Units |
|------|-----------|---------|-------|
| `f09_pop_iso.csv` | `im_pop_iso(t_all,iso)` | Population by ISO country, all SSP variants | mio. capita/yr |
| `f09_pop_iso.csv` (aggregated) | `im_pop(t_all,i)` | Population by MAgPIE region (i = 12 regions) | mio. capita/yr |
| `f09_demography.cs3` | `im_demography(t_all,iso,sex,age)` | Population by sex x 21 age groups | mio. capita/yr |
| `f09_physical_inactivity.cs3` | `im_physical_inactivity(t_all,iso,sex,age)` | Physical inactivity fraction | share (0-1) |
| `f09_gdp_ppp_iso.csv` | `im_gdp_pc_ppp_iso(t_all,iso)` | GDP per capita PPP, ISO level | USD17PPP/cap/yr |
| `f09_gdp_mer_iso.csv` | `im_gdp_pc_mer_iso(t_all,iso)` | GDP per capita MER, ISO level | USD17MER/cap/yr |
| `f09_gdp_mer_iso.csv` (aggregated) | `im_gdp_pc_mer(t_all,i)` | GDP per capita MER, regional level | USD17MER/cap/yr |
| `f09_development_state.cs3` | `im_development_state(t_all,i)` | World Bank income classification | 0-1 scale |

**Scenario selection** (`modules/09_drivers/aug17/input.gms:8-18`):
```gams
$setglobal c09_pop_scenario  SSP2
$setglobal c09_gdp_scenario  SSP2
$setglobal c09_pal_scenario  SSP2
```
Separate switches for population, GDP, and physical activity allow scenario
mixing (e.g., SSP1 population + SSP3 GDP).

**Scenario lock-in until 2025** (`preloop.gms:36-56`): All scenarios are forced
to SSP2 values while `m_year(t_all) <= sm_fix_SSP2` (scalar default = 2025,
`input.gms:22`). After 2025, the selected `c09_*_scenario` values take effect.

Module 09 has zero dependencies on other modules. It is a pure data publisher.

---

## Stage 2: Module 09 Drivers -> Module 15 (Food Demand)

**All six Module 09 interface parameters are consumed by Module 15**
(`modules/15_food/anthro_iso_jun22/`, primarily in `presolve.gms`):

| Parameter from M09 | Role in M15 |
|--------------------|-------------|
| `im_pop(t,i)` | Scales kcal demand from per-capita to total in `q15_food_demand` (`equations.gms:57`) |
| `im_pop_iso(t,iso)` | Population denominator for ISO-level per-capita calculations in presolve |
| `im_gdp_pc_ppp_iso(t,iso)` | Direct input to budget constraint `q15_budget` and all income-demand saturation regressions |
| `im_gdp_pc_mer_iso(t,iso)` | Used in baseline price conversion (PPP/MER bridging) |
| `im_demography(t,iso,sex,age)` | Weight for BMI-based food intake equation `q15_intake` (`equations.gms:141-151`) |
| `im_physical_inactivity(t,iso,sex,age)` | Used to calculate Physical Activity Level (PAL), which scales Basic Metabolic Rate to energy requirements (`presolve.gms:194-197`) |

**Mechanistic path within Module 15 (how GDP and population drive food demand):**

1. **Budget constraint** (`q15_budget`, `equations.gms:48-52`):
   ```
   v15_income_pc_real_ppp_iso(iso) = im_gdp_pc_ppp_iso(t,iso) + price_adjustment + tax_recycling
   ```
   GDP per capita PPP sets the baseline real income. If elastic demand is
   enabled (`s15_elastic_demand = 1`), shadow prices from MAgPIE erode this.

2. **BMI regression** (`q15_regr_bmi_shr`, `equations.gms:71-76`): BMI group
   shares are saturation functions of `v15_income_pc_real_ppp_iso`, deflated to
   a comparable base year using `fm_gdp_defl_ppp`:
   ```
   v15_regr_overgroups = intercept + saturation * income / (halfsat + income)
   ```

3. **Dietary composition regressions** (`q15_regr`, `equations.gms:169-173`):
   overconsumption ratio, livestock share, processed share, and veg/fruit share
   are all saturation functions of the same real income variable. As income rises
   under higher-GDP SSP scenarios, livestock share and overconsumption rise.

4. **Food intake** (`q15_intake`, `equations.gms:141-151`): Integrates BMI
   shares with `im_demography` (age x sex population) and Schofield-equation
   energy requirements adjusted for PAL from `im_physical_inactivity`.

5. **Food tree** (Equations 15-18, `equations.gms:181-207`): Allocates total
   demand into specific products (crops, livestock, processed foods, staples).

6. **MAgPIE constraint** (`q15_food_demand`, `equations.gms:10-14`):
   ```
   (vm_dem_food(i,kfo) + f15_household_balanceflow) * kcal_content >=
       im_pop(t,i) * p15_kcal_pc_calibrated(t,i,kfo) * 365
   ```
   This is the single equation that links the standalone food demand model to
   MAgPIE's optimization. `im_pop` appears here directly; GDP enters via
   `p15_kcal_pc_calibrated`, which was computed by the standalone model from
   `im_gdp_pc_ppp_iso`.

**Key intermediate parameters:**

| Parameter | Role |
|-----------|------|
| `p15_kcal_pc_calibrated(t,i,kfo)` | Output of standalone food demand model; contains the GDP + demography + anthropometry signal; passed to MAgPIE constraint `q15_food_demand` |
| `p15_kcal_pc_iso(t,iso,kfo)` | ISO-level per-capita demand (before aggregation to regions) |
| `v15_income_pc_real_ppp_iso(iso)` | Real income variable in the standalone NLP; the main conduit for GDP effects |

**Default switch:** `s15_elastic_demand = 0` means food demand is set from the
standalone model before the main solve and is NOT updated by agricultural prices.
GDP effects are still present but work only through the income -> demand regression
path, not through price feedback.

---

## Stage 3: Module 15 Output -> Module 16 (Demand Aggregation)

`vm_dem_food(i,kfo)` is the sole food-side handoff from Module 15 to Module 16.
Module 16 (`modules/16_demand/sector_may15/`) has no direct dependency on Module
09 parameters itself; it receives `vm_dem_food` as an already-computed MAgPIE
optimization variable.

Module 16 aggregates `vm_dem_food` together with feed demand (`vm_dem_feed` from
Module 70), processing demand, material demand, bioenergy demand, and
endogenously-calculated seed and waste into total regional supply requirements:

**Crop supply balance** (`q16_supply_crops`, `equations.gms:19-29`):
```
vm_supply(i,kcr) = vm_dem_food(i,kcr)
                 + sum(kap4, vm_dem_feed(i,kap4,kcr))
                 + vm_dem_processing(i,kcr)
                 + vm_dem_material(i,kcr)
                 + vm_dem_bioen(i,kcr)
                 + vm_dem_seed(i,kcr)
                 + v16_dem_waste(i,kcr)
                 + f16_domestic_balanceflow(t,i,kcr)
```

Population growth under high-SSP scenarios thus enters `vm_supply` entirely
through `vm_dem_food` (and also through `vm_dem_feed` via livestock demand in
Module 70, which itself consumes `im_pop` and `im_pop_iso` from Module 09).
Module 16 then passes `vm_supply` to Module 21 (Trade) as the regional demand
that must be balanced.

---

## Stage 4: SSP Drivers -> Module 14 (Yields)

**Module 14 does NOT directly consume any Module 09 interface parameter.**

This is the important negative finding: `im_pop`, `im_gdp_pc_ppp_iso`, and the
other driver variables do not appear in Module 14's equations or preloop
calibration code. Module 14 (`modules/14_yields/managementcalib_aug19/`)
receives its inputs from:

- **LPJmL external model:** `f14_yields.cs3` (biophysical yield baseline with
  embedded climate change scenario, loaded at `input.gms:37`)
- **FAO statistics:** `f14_region_yields.cs3` (calibration target, `input.gms:53`)
- **Module 13 (Technological Change):** `vm_tau(j,"crop")` and
  `fm_tau1995(h)` — the yield-scaling mechanism
- **Module 70 (Livestock):** `pm_past_mngmnt_factor(ct,i)` — pasture management

**SSP data reaches Module 14 only via Module 13:**

Module 13 (`modules/13_tc/`) receives `im_gdp_pc_ppp_iso` from Module 09 to
drive technology adoption rates (documented in `module_09.md` Section 5.2:
"Module 13 (tc) <- im_gdp_pc_ppp_iso"). Module 13 then provides `vm_tau` to
Module 14's crop yield equation:

```
q14_yield_crop(j,kcr,w):
  vm_yld(j,kcr,w) = sum(ct, i14_yields_calib(ct,j,kcr,w))
                    * vm_tau(j,"crop")
                    / sum((cell(i,j),supreg(h,i)), fm_tau1995(h))
```
(`equations.gms:14-16`)

So a higher-GDP SSP scenario -> higher τ via Module 13 -> higher yields in
Module 14. But the carrier is tau, not a direct GDP parameter in Module 14.

**Pasture yields** additionally receive a spillover from crop technological
change (`equations.gms:35-39`), using the previous time step's tau `pcm_tau`
and a spillover scalar `s14_yld_past_switch = 0.25` (25% of crop intensification
benefits pasture). This is also GDP-mediated indirectly via Module 13.

**Climate scenario** does affect `i14_yields_calib` (the LPJmL baseline), via
switch `c14_yields_scenario` (options: `cc`, `nocc`, `nocc_hist`), but this is
entirely decoupled from the SSP socioeconomic scenario. A model run can use SSP5
GDP with the `nocc` yield trajectory and vice versa.

---

## Complete Parameter Chain Summary

```
Input files (IIASA SSP Database, World Bank, OECD)
  -> f09_pop_iso.csv, f09_gdp_ppp_iso.csv, f09_gdp_mer_iso.csv,
     f09_demography.cs3, f09_physical_inactivity.cs3
     [Module 09, preloop, loaded at input.gms:26-53]
         |
         | scenario switch: c09_pop_scenario / c09_gdp_scenario
         | SSP2 lock-in until sm_fix_SSP2 = 2025 (input.gms:22)
         |
         v
Module 09 interface parameters:
  im_pop_iso(t,iso)          [mio. capita/yr, ISO level]
  im_pop(t,i)                [mio. capita/yr, region level]
  im_demography(t,iso,sex,age)
  im_physical_inactivity(t,iso,sex,age)
  im_gdp_pc_ppp_iso(t,iso)   [USD17PPP/cap]
  im_gdp_pc_mer_iso(t,iso)   [USD17MER/cap]
         |                           \
         |                            -> Module 13 (tc)
         |                               vm_tau(j,"crop")
         v                               fm_tau1995(h)
Module 15 (food, anthro_iso_jun22)          \
  v15_income_pc_real_ppp_iso(iso)            v
  [budget constraint q15_budget]       Module 14 (yields)
  -> BMI regressions (income-dependent)  q14_yield_crop:
  -> dietary composition regressions       vm_yld = i14_yields_calib
  -> q15_intake (demography-weighted)           * vm_tau / fm_tau1995
  -> p15_kcal_pc_calibrated(t,i,kfo)     q14_yield_past:
  -> q15_food_demand:                       vm_yld_past = i14_yields_calib
       vm_dem_food(i,kfo) [mio. tDM/yr]         * pm_past_mngmnt_factor
                 |                              * [1 + 0.25*(tau-1)]
                 v
Module 16 (demand, sector_may15)
  q16_supply_crops / q16_supply_livestock / ... :
     vm_supply(i,kall) = vm_dem_food + vm_dem_feed + ...
                 |
                 v
Module 21 (Trade) -- uses vm_supply as regional demand
```

---

## Key Points / Distinctions

1. **GDP -> food demand** is a direct mechanistic link through Module 15's
   saturation income-demand regressions (q15_budget, q15_regr, q15_regr_bmi_shr).
   The carrier parameters are `im_gdp_pc_ppp_iso` (ISO-level PPP GDP) and the
   derived `v15_income_pc_real_ppp_iso`.

2. **Population -> food demand** is also direct: `im_pop(t,i)` multiplies
   `p15_kcal_pc_calibrated` in `q15_food_demand` to convert per-capita demand
   to total demand; `im_demography` weights the BMI-intake calculation.

3. **GDP -> yields** is INDIRECT only: GDP enters Module 13 (not documented in
   detail in module_14.md), Module 13 produces `vm_tau`, and tau enters Module
   14's equations. There is no GDP parameter inside Module 14 itself.

4. **Population does NOT enter Module 14 at all** — yields are biophysical and
   technological, not driven by population.

5. **The SSP scenario and the climate scenario are independent switches:**
   `c09_gdp_scenario = SSP5` does not imply `c14_yields_scenario = cc`. They
   must be set separately.

6. **Module 16 is a passive aggregator.** It does not consume any Module 09
   parameters directly; SSP effects enter only through `vm_dem_food` (from M15)
   and `vm_dem_feed` (from M70, which also consumes `im_pop` and `im_pop_iso`).

---

## Sources

- 🟡 Based on `modules/module_09.md` (Module 09 documentation, last verified 2025-10-13)
- 🟡 Based on `modules/module_15.md` (Module 15 documentation, last verified 2025-10-13)
- 🟡 Based on `modules/module_16.md` (Module 16 documentation, last verified 2025-10-13)
- 🟡 Based on `modules/module_14.md` (Module 14 documentation, last verified 2025-10-12)

Line numbers are from the documentation files and were verified at those docs'
last-sync dates. Code changes since then may have shifted line numbers; for
critical work, verify against current GAMS source in `../modules/`.

**Epistemic hierarchy:**
- Claims about Module 09 interface parameters and their consumers: 🟡 Documented
  (sourced from module_09.md Sections 3, 5.2; verified against declarations.gms
  at time of documentation)
- Claims about Module 15 equation structure (q15_budget, q15_food_demand,
  q15_regr): 🟡 Documented (sourced from module_15.md Sections 2, 5)
- Claims about Module 16 supply balance equations: 🟡 Documented (sourced from
  module_16.md, all 8 equations verified)
- Claims about Module 14 NOT consuming Module 09 parameters directly: 🟡
  Documented (module_14.md Section 7.2 lists only M13, M52, M35, M70 as
  upstream dependencies; no im_pop or im_gdp variables listed)
- Claim that Module 13 mediates GDP -> tau -> yields: 🟡 Documented (module_09.md
  Section 5.2 states "Module 13 (tc) <- im_gdp_pc_ppp_iso, im_pop_iso";
  module_14.md Section 7.2 confirms vm_tau from Module 13)
