# Module 09 — SSP Driver Propagation: Interface Parameters and Downstream Consumers

**Question**: How do the SSP population and GDP drivers in module 09 propagate to other modules? Name the key interface parameters module 09 provides and at least three downstream consumers (e.g. food demand 15, TC 13, yields 14).

---

## 1. Module 09's Role: Pure Source Hub

Module 09 (`modules/09_drivers/aug17/`) is a **pure data provider** with zero dependencies on any other MAgPIE module. All information flows outward. It loads exogenous SSP/SDP scenarios (SSP1–5, SDP, SDP_EI, SDP_MC, SDP_RC) from IIASA, World Bank, and WHO databases, then exposes **8 interface parameters** (all prefixed `im_`) to 14 downstream modules. There are no optimization equations, no `vm_` variables, and no solver involvement.

The scenario-switch mechanism (`sm_fix_SSP2 = 2025`, set in `input.gms:22`) is the one globally consequential design decision: all scenarios are identical to SSP2 before 2025, then diverge. Separate config flags (`c09_pop_scenario`, `c09_gdp_scenario`, `c09_pal_scenario`) allow mixing population and GDP narratives across scenarios.

---

## 2. Key Interface Parameters

All 8 interface parameters are declared in `declarations.gms:8-36` and assigned in `preloop.gms:36-56`.

| Parameter | Dimensions | Units | # Consumers |
|---|---|---|---|
| `im_pop_iso(t_all,iso)` | time × 249 ISO countries | mio. people/yr | 10 modules |
| `im_pop(t_all,i)` | time × 12 regions | mio. people/yr | 3 modules |
| `im_gdp_pc_ppp_iso(t_all,iso)` | time × ISO | USD17PPP per capita/yr | 4 modules |
| `im_gdp_pc_mer_iso(t_all,iso)` | time × ISO | USD17MER per capita/yr | 2 modules |
| `im_gdp_pc_mer(t_all,i)` | time × region | USD17MER per capita/yr | 1 module (42) |
| `im_development_state(t_all,i)` | time × region | dimensionless 0–1 | 5 modules |
| `im_demography(t_all,iso,sex,age)` | time × ISO × M/F × 21 age groups | mio. people/yr | 1 module (15) |
| `im_physical_inactivity(t_all,iso,sex,age)` | time × ISO × sex × age | share 0–1 | 1 module (15) |

**Construction notes** (from `preloop.gms`):
- `im_pop(t,i)` is aggregated from `im_pop_iso` via `i09_pop_raw(t,i,scen) = sum(i_to_iso(i,iso), f09_pop_iso(t,iso,scen))` (line 11, 50).
- `im_gdp_pc_ppp_iso` is computed as `f09_gdp_ppp_iso / f09_pop_iso` with missing-data fill from the SSP2 regional average (lines 23–27).
- `im_demography` carries a +0.000001 constant to prevent division-by-zero in Module 15's per-capita calculations (lines 39, 48).

---

## 3. Downstream Consumers and Propagation Mechanisms

### 3.1 Module 15 (Food Demand) — broadest consumer

Module 15 (`anthro_iso_jun22` realization) consumes **five** of module 09's parameters, making it the most coupled downstream module.

**Population → food demand constraint (q15_food_demand)**

`im_pop(t,i)` appears directly in `equations.gms:10-14`:

```gams
q15_food_demand(i2,kfo) ..
    (vm_dem_food(i2,kfo) + ...) * kcal_content =g=
    sum(ct, im_pop(ct,i2) * p15_kcal_pc_calibrated(ct,i2,kfo)) * 365;
```

This is the single equation linking Module 15's standalone food demand model to MAgPIE's optimization. A higher SSP3 population relative to SSP1 directly scales the right-hand side, requiring proportionally more food production from the rest of the model.

**GDP per capita PPP → budget constraint and BMI distribution (q15_budget, q15_regr_bmi_shr)**

`im_gdp_pc_ppp_iso(t,iso)` feeds into `q15_budget` (`equations.gms:48-52`):

```gams
q15_budget(iso) ..
    v15_income_pc_real_ppp_iso(iso) =e=
    sum(kfo, v15_kcal_regr(iso,kfo) * 365 * (initial_price - current_price))
    + sum(ct, im_gdp_pc_ppp_iso(ct,iso) + p15_tax_recycling(ct,iso)) + v15_income_balance(iso);
```

Real income is anchored to `im_gdp_pc_ppp_iso`. Rising SSP5 GDP inflates real income, which in turn shifts BMI distributions toward higher weight classes through `q15_regr_bmi_shr`, which drives larger average body mass, higher energy requirements, and a dietary composition that is more meat- and calorie-intensive. This is the key income-elastic demand mechanism in MAgPIE.

**Demographics and physical inactivity → caloric requirements**

`im_demography(t,iso,sex,age)` and `im_physical_inactivity(t,iso,sex,age)` determine age- and sex-specific Physical Activity Levels (PAL), which modulate the caloric requirement per capita within the standalone food demand model. Ageing populations (SSP1 vs SSP3) mechanically shift the demographic composition and thus aggregate food energy demand even holding GDP fixed.

**Net effect on the rest of the model**: Module 15 outputs `vm_dem_food(i,kfo)` (mio. tDM/yr) to Module 16 (Demand). Demand aggregation in Module 16 connects to supply-side modules — cropland (30), yields (14), trade (21) — so the SSP driver choice propagates to land allocation and intensification throughout the model.

---

### 3.2 Module 13 (Technological Change) — GDP drives intensification investment costs

Module 13 (`endo_jan22` realization) consumes `im_gdp_pc_ppp_iso(t,iso)` and `im_pop_iso(t,iso)` from Module 09.

The core mechanism is indirect: Module 09 does **not** appear in Module 13's optimization equations (`q13_cost_tc`, `q13_tech_cost`). Instead, `im_gdp_pc_ppp_iso` feeds into Module 13's **preloop** initialization, which calibrates `i13_tc_factor` and `i13_tc_exponent` — the regression coefficients in the intensification cost function. Higher income levels imply historically faster technology adoption, which translates into lower required investment cost per unit tau increase under wealthier SSP scenarios.

Additionally, `im_pop_iso` is used for ISO-level scaling in the preprocessing calculations that feed Module 13's initial tau calibration.

The pathway is therefore: `im_gdp_pc_ppp_iso` → calibration of TC cost parameters → `q13_cost_tc` (`equations.gms:20-23`): `v13_cost_tc(i2,tautype) = pc13_land * i13_tc_factor * v13_tau**i13_tc_exponent * (1+pm_interest)**15`. A higher SSP5 GDP lowers TC costs relative to SSP3, allowing more intensification per unit expenditure and thus less land expansion pressure.

---

### 3.3 Module 38 (Factor Costs) — GDP per capita scales wage levels

Module 38 (`sticky_feb18` default realization) consumes `im_gdp_pc_ppp_iso(t,iso)`. In the `sticky_feb18` preloop, `im_gdp_pc_ppp_iso` is used to compute `pm_hourly_costs(t,i,"scenario")` — the regional wage rate. This enters `q38_cost_prod_labor` (`equations.gms:15-17`):

```gams
q38_cost_prod_labor(i2) ..
  vm_cost_prod_crop(i2,"labor") =e=
  sum(kcr, vm_prod_reg(i2,kcr)
           * p38_labor_need(ct,i2,kcr)
           * (pm_hourly_costs(ct,i2,"scenario") / pm_hourly_costs(ct,i2,"baseline")));
```

Higher SSP5 GDP per capita → higher `pm_hourly_costs` → higher labor cost per unit of production → the optimizer substitutes toward labor-saving intensification (captured via tau in Module 13) and shifts production to regions with lower wages. This is MAgPIE's structural transformation mechanism: income-driven wage increases make labor-intensive smallholder production relatively more expensive over time.

---

### 3.4 Additional Downstream Consumers (brief)

- **Module 12 (Interest Rate)**: `im_development_state(t,i)` enters the interest rate calibration. Higher-income regions (closer to 1 on the 0–1 scale) receive lower real interest rates, affecting Module 13's 15-year cost shift term `(1+pm_interest)**15`.
- **Module 42 (Water Demand)**: `im_gdp_pc_mer(t,i)` and `im_development_state(t,i)` drive non-agricultural water demand (industrial, municipal). Higher GDP → more non-agricultural water use → more competition with irrigation.
- **Module 73 (Timber)**: `im_gdp_pc_ppp_iso` and `im_pop_iso` jointly drive timber demand via an income-elastic per-capita construction demand regression.
- **Module 55 (AWMS)** and **Module 56 (GHG Policy)**: `im_development_state` determines manure management system shares and GHG policy ambition levels, respectively.
- **Module 60 (Bioenergy)** and **Module 62 (Material)**: `im_pop_iso` and `im_pop` scale per-capita bioenergy and material demand to total demand.

---

## 4. Propagation Summary Diagram

```
External SSP/SDP inputs (IIASA, World Bank, WHO)
          |
    MODULE 09 (preloop only — no optimizer)
          |
          +--im_pop_iso / im_pop-----------> M15 (food demand constraint)
          |                                  M60, M62 (bioenergy, material)
          |                                  M70 (livestock demand)
          |                                  M50, M55, M56 (N, AWMS, GHG policy)
          |                                  M12, M42 (interest, water)
          |
          +--im_gdp_pc_ppp_iso ------------> M15 (budget + BMI → kcal demand)
          |                                  M13 (TC cost calibration)
          |                                  M38 (wage rates → labor costs)
          |                                  M73 (timber demand)
          |
          +--im_gdp_pc_mer_iso / im_gdp_pc_mer -> M36 (employment wages)
          |                                         M42 (water demand)
          |
          +--im_development_state ----------> M12 (interest rates)
          |                                   M18 (residue use)
          |                                   M42 (water demand)
          |                                   M55 (AWMS system shares)
          |                                   M56 (GHG policy ambition)
          |
          +--im_demography / im_physical_inactivity -> M15 (PAL, age/sex kcal req.)
```

---

## 5. What Module 09 Does NOT Provide

- **Yields (Module 14)**: Module 14 does NOT consume any `im_` parameter from Module 09 directly. Yields are driven by tau (from Module 13), biophysical crop suitability, and water availability — not directly by population or GDP. The SSP influence on yields is entirely indirect (via TC calibration in Module 13).
- No endogenous feedback: model outcomes (food prices, land-use change) do NOT flow back into Module 09's population or GDP trajectories.
- No within-region inequality: all parameters are regional or ISO averages.

---

## Epistemic Hierarchy

- `module_09.md` (module 09 documentation, last verified 2025-10-13 against `../modules/09_*/aug17/*.gms`) — primary source for all interface parameter names, consumer counts, and scenario logic described here.
- `module_15.md` (module 15 documentation, realization `anthro_iso_jun22`) — secondary source for the food demand constraint and budget equation mechanisms.
- `module_13.md` (module 13 documentation, realization `endo_jan22`) — secondary source for TC cost equation and GDP link.
- `module_38.md` (module 38 documentation, realization `sticky_feb18`) — secondary source for factor cost/wage mechanism.

All claims: **documented** (module docs read this session). High-stakes equation formulas cited with file:line from the docs. Raw GAMS code was NOT read per task constraints; line numbers should be verified against current code before code-level work.
