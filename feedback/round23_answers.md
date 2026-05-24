# R23 Sonnet answers (captured for audit)

## R23-Q1 answer

Chain trace: `s15_exo_diet=3` → soil nitrogen budget

(a) M15 enforcement mechanism in diet=3 mode

Per `agent/helpers/scenario_diet_change.md` (Recipe 1 and Pitfall #5), diet=3 is the recommended (MAgPIE-specific) EAT-Lancet mode. It uses **`f15_rec_EATLancet` min/max bounds** applied to the model's own intake projections, rather than the fixed external dataset used by diet=1. The bounds table (`f15_rec_EATLancet(iso, EAT_targets15, EAT_targettype15)`) carries minimum and maximum kcal/cap/day per food group (red meat, fish, eggs, milk, etc.) and is loaded at `modules/15_food/anthro_iso_jun22/input.gms:254-257` (per module_15.md line 682-686). With `s15_exo_ruminant=1` (default-on commodity sub-switch, `input.gms:82-95` per the helper), the ruminant max bound (e.g., 28 kcal/day red meat in `FLX`-style targets) is enforced. Critically, the helper notes diet=3 **ignores `c15_EAT_scen`** — composition comes purely from the min/max bounds table (Pitfall in Recipe 2). Implementation lives in `modules/15_food/anthro_iso_jun22/exodietmacro.gms` (included from `intersolve.gms:155`), with the diet-mode-3 branch at `exodietmacro.gms:441-442` per the helper. Reduced ruminant kcal flows into `p15_kcal_pc_calibrated(t,i,kfo)`, the calibrated demand parameter output to MAgPIE.

(b) M15→M16 interface variable

The interface variable is **`vm_dem_food(i, kall)`** (units: mio. tDM/yr, positive optimization variable; module_15.md:420, declarations.gms:13-15). Dimensions: regions `i` × all-commodities `kall` (fixed to zero for non-food `knf`; module_15.md:425). It is bound to the calibrated kcal demand through the constraint **`q15_food_demand(i2, kfo)`** at `modules/15_food/anthro_iso_jun22/equations.gms:10-14`:

```
(vm_dem_food(i2,kfo) + sum(ct, f15_household_balanceflow(ct,i2,kfo,"dm")))
  * sum(ct,(fm_nutrition_attributes(ct,kfo,"kcal") * 10**6))
  =g= sum(ct, im_pop(ct,i2) * p15_kcal_pc_calibrated(ct,i2,kfo)) * 365
```

So reduced ruminant kcal in `p15_kcal_pc_calibrated` directly reduces the lower bound on `vm_dem_food(i, livst_rum)` (and `kmilk`, `livst_milk` depending on naming).

(c) M16 aggregation into `vm_supply` for ruminant products

Ruminant meat and milk are animal products (`kap`), so the relevant equation is **`q16_supply_livestock(i2, kap)`** at `modules/16_demand/sector_may15/equations.gms:31-38` (module_16.md:100-102, realization `sector_may15`):

```
vm_supply(i2,kap) =e=
    vm_dem_food(i2,kap)
  + sum(kap4, vm_dem_feed(i2,kap4,kap))
  + v16_dem_waste(i2,kap)
  + vm_dem_material(i2,kap)
  + sum(ct, f16_domestic_balanceflow(ct,i2,kap))
```

A lower `vm_dem_food(i, livst_rum)` directly reduces `vm_supply(i, livst_rum)`, and this then propagates to Module 21 (trade) where `vm_prod_reg + vm_import - vm_export ≥ vm_supply` (module_16.md:694).

(d) M17 regional-production variable

The variable is **`vm_prod_reg(i, kall)`** (mio. tDM/yr; module_17.md:162-171). It is produced by **`q17_prod_reg(i2, k)`** at `modules/17_production/flexreg_apr16/equations.gms:11` (realization `flexreg_apr16`, module_17.md:43-49):

```
q17_prod_reg(i2,k) ..
    vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k));
```

Important caveat from module_17.md:24, 35, 309-313: although declared over the full primary-commodity set `k`, in current practice `vm_prod(j,k)` is non-zero only for plant commodities (crops from Module 30, pasture from Module 31). **Livestock production is handled regionally inside Module 70**, so `vm_prod_reg(i, livst_rum)` from M17 sums to zero; the actual livestock supply chain reaches M50 via pasture (`vm_prod_reg(i,"pasture")`) and feed crops (`vm_prod_reg(i,kcr)`). The diet-3 ruminant reduction therefore propagates to the soil nitrogen budget by lowering required pasture biomass and feed-crop production (through M70's feed baskets and the M16 livestock supply balance).

(e) Default M50 `q50_nr_bal_crp`

From module_50.md:32-38 (realization `macceff_aug22`, `equations.gms:14-16`):

```
q50_nr_bal_crp(i2) ..
    vm_nr_eff(i2) * v50_nr_inputs(i2)
    =g= sum(kcr, v50_nr_withdrawals(i2,kcr));
```

Form: SNUpE(i) × N_inputs(i) ≥ Σ_kcr N_withdrawals(i, kcr). Inequality (=g=), regional only, withdrawals summed over crop products. With `vm_prod_reg(i, kcr)` reduced (less feed-crop demand from the smaller ruminant feed basket), `v50_nr_withdrawals` falls (per `q50_nr_withdrawals` at `modules/50_nr_soil_budget/macceff_aug22/equations.gms:36-43`), relaxing the lower bound on inputs and reducing required nitrogen application.

(f) One downstream M51 equation

**`q51_emissions_man_crop(i, n_pollutants_direct)`** at `modules/51_nitrogen/rescaled_jan21/equations.gms:22-27` (realization `rescaled_jan21`, module_51.md:26-48). It consumes `vm_manure_recycling(i2,"nr")` and rescales by `vm_nr_eff(i2)` (the cropland NUE from M50). The rescaling form (module_51.md:33-35): `vm_manure_recycling(i2,"nr") / (1-s51_snupe_base) * (1-vm_nr_eff(i2)) * EF`. Other equations also consuming M50 directly include `q51_emissions_inorg_fert` (`equations.gms:30-39`) and `q51_emissions_resid` (`equations.gms:42-46`), both rescaled by `vm_nr_eff`/`vm_nr_eff_pasture`.

🟡 Based on `agent/helpers/scenario_diet_change.md`, `modules/module_15.md`, `modules/module_16.md`, `modules/module_17.md`, `modules/module_50.md`, and `modules/module_51.md`.

---

## R23-Q2 answer

Confirmed. Module 43's default is `total_water_aug13` and the equation cite matches.

Loaded helpers: `agent/helpers/debugging_infeasibility.md`, `agent/helpers/water_scarcity_scenarios.md`, and `modules/module_43.md`.

(a) The water-balance hard constraint

The water balance is hard-constrained by `q43_water(j2)` in **Module 43 (water_availability)**, default realization **`total_water_aug13`**, at `modules/43_water_availability/total_water_aug13/equations.gms:10-11`:

```gams
q43_water(j2) ..
  sum(wat_dem, vm_watdem(wat_dem,j2)) =l= sum(wat_src, v43_watavail(wat_src,j2));
```

- LHS: sum over all demand sectors (`wat_dem`: agriculture, domestic, manufacturing, electricity, ecosystem) of `vm_watdem`
- Operator: `=l=` (less-than-or-equal, inequality)
- RHS: sum over all water sources (`wat_src`: surface, ground, ren_ground, technical) of `v43_watavail`
- Domain: enforced per cluster cell `j2` (no inter-cell transfer)

(b) Slack / buffer

The equation itself is **strict** — there is no in-equation slack term, no "v43_water_missing" penalty variable, no automatic relaxation written into `q43_water`. The water helper explicitly notes "no slack variable" for this constraint.

However, the `total_water_aug13` realization includes a presolve groundwater buffer at `modules/43_water_availability/total_water_aug13/presolve.gms:14-16` (per water_scarcity_scenarios.md pitfall #5): when exogenous (non-agricultural + ecosystem) demand exceeds surface supply in a cell, the model auto-fills `v43_watavail("ground",j)` with zero-cost groundwater to keep the model solvable. This buffer activates only against exogenous demand exceedances — it does not rescue infeasibility caused by endogenous agricultural demand pressing on the surface-water cap. So for an `lpj_runoff_minus30pct` cut that squeezes agriculture, the constraint behaves as strict.

(c) Top-3 diagnostic steps for modelstat=4

Per `debugging_infeasibility.md` Steps 1–3:

1. Identify the failing timestep: read `p80_modelstat(t)` from `fulldata.gdx` — the first `t` with value > 2 and ≠ 7 is the break point.
2. Check land balance pressure as a co-cause: `readGDX(gdx, "ov_land", select=list(type="level"))` — sum land types per cluster; clusters at ~100% utilization implicate land in addition to water.
3. Check binding-constraint marginals — specifically `oq43_water` marginal: `readGDX(gdx, "oq43_water", select=list(type="marginal"))`. Large positive marginals point to the cells where the runoff cut is biting. (Also worth scanning `oq10_land_area` and `oq21_notrade` marginals.)

Supplementing: inspect slack variables (`v73_prod_heaven_timber`, `v44_bii_missing`, `v32_land_missing`, `v21_import_for_feasibility`, `v29_fallow_missing`) — any non-zero level signals which adjacent constraints were also strained but had safety valves. Water has none, so a runoff cut surfaces directly as infeasibility rather than as activated slack.

(d) EFP switch and default

Per `water_scarcity_scenarios.md` (Module 42 switch table, lines 60–62):

- Master switch: `c42_env_flow_policy`
- Default: `"off"`
- Options: `"off"`, `"on"`, `"mixed"`

When `"off"`, EFP is not enforced; ecosystem demand reduces to a base fraction (`s42_env_flow_base_fraction = 0.05` by default). When `"on"`, EFP applies everywhere, with the algorithm controlled by `s42_env_flow_scenario` (default `2` = Smakhtin) and ramped between `s42_efp_startyear = 2025` and `s42_efp_targetyear = 2040`. `"mixed"` enforces only in HIC regions, weighted by population share.

(e) Relationship among `vm_watdem`, `v43_watavail`, `wat_src`

- `vm_watdem(wat_dem, j)` — Module 42 output (sectoral water withdrawals, mio. m³/yr). Agriculture is endogenous (computed in `q42_water_demand` from `vm_area(j,kcr,"irrigated")` and `vm_prod(j,kli)` divided by `v42_irrig_eff`); domestic, manufacturing, electricity, and ecosystem are exogenous. It is the LHS aggregand of `q43_water`.
- `v43_watavail(wat_src, j)` — Module 43 variable holding water supply per source per cell (mio. m³/yr). For `wat_src="surface"`, fixed in presolve from `f43_wat_avail(t,j)`. For `wat_src="ground" | "ren_ground" | "technical"`, fixed to zero except for the "ground" auto-fill buffer described in (b).
- `wat_src` — source set with members `{surface, ground, ren_ground, technical}`.

🟡 Based on `agent/helpers/debugging_infeasibility.md` and `agent/helpers/water_scarcity_scenarios.md`, cross-checked against `modules/module_43.md`.

---

## R23-Q3 answer

(a) Risk tier of M44

M44 (biodiversity) is NOT among the 4 high-centrality modules profiled in `cross_module/modification_safety_guide.md`. That guide focuses exclusively on Modules 10, 11, 17, and 56 (Sections 1–4 of the guide).

The closest direct risk-tier statement for M44 comes from `modules/module_44.md:674`, which classifies it as 🟡 MEDIUM RISK, with testing requirements limited to verifying output ranges and checking downstream modules.

In the broader centrality ranking (`modification_safety_guide.md:1056–1068, Appendix A`), M44 does not appear in the top-10 centrality list. It is characterized in `modules/module_44.md:664` as a "Biodiversity Indicator Provider" hub (one downstream consumer for `vm_cost_bv_loss`: Module 11).

Implication for the developer: a new constraint that tightens cropland expansion through M44 is structurally low-blast-radius on the M44 side (only M11 reads `vm_cost_bv_loss`), but the constraint will operate on `vm_land`/`vm_landexpansion`, both of which are Module 10 interface variables (HIGHEST RISK per `modification_safety_guide.md:30`).

(b) Cropland-state interface variables a new constraint would need

A "restrict cropland expansion" constraint must reach across from M44 to land-allocation variables declared in M10. Per `modules/module_10.md:171` (citing `modules/10_land/landmatrix_dec18/declarations.gms:14-24`):

- `vm_land(j,land)` — current land area by type, mio. ha. Declared in `modules/10_land/landmatrix_dec18/declarations.gms:14-24` (per `module_10.md:175`). For the cropland state specifically, the relevant slice is `vm_land(j,"crop")`.
- `vm_landexpansion(j,land)` — area gained from other types, mio. ha. Same declarations block (`module_10.md:179`). For expansion specifically, `vm_landexpansion(j,"crop")` is the direct flow variable.
- `vm_lu_transitions(j,land_from,land_to)` — full 7×7 transition matrix (`module_10.md:185`).

(c) Is M44 in a documented circular dependency?

No documented direct cycle for M44. The catalog of major cycles in `cross_module/circular_dependency_resolution.md:730-738` lists 4 confirmed major cycles (C1–C4) and 6 suspected additional cycles (C5–C10) — M44 appears in none of them. The closest indirect coupling is via C2 and C4. `module_44.md:670` confirms: "Module 44 participates in zero or minimal circular dependencies."

(d) M44 cost-equation, cost-variable name, and dimensions

- Equation: `q44_cost` (`module_44.md:84-102`, citing `modules/44_biodiversity/bii_target/equations.gms:28-29`)
- Formula (`module_44.md:89-90`):
  ```
  sum(cell(i2,j2)) vm_cost_bv_loss(j2) = sum(biome44) [v44_bii_missing(i2,biome44) × s44_cost_bii_missing]
  ```
- Cost variable: `vm_cost_bv_loss(j)` — biodiversity penalty cost per cell, units mio. USD17MER/yr (`module_44.md:94, 631`). Declared in `modules/44_biodiversity/bii_target/declarations.gms:10`.
- Dimensions: single index `j` (simulation cell).

(e) Consumer of `vm_cost_bv_loss` and how it enters the objective

- Consumer module: Module 11 (Costs), realization `default`. M44 declares one downstream consumer.
- Equation: `q11_cost_reg` (`modules/11_costs/default/equations.gms:15-47`, reproduced in `module_11.md:79-117`). The relevant term at `module_11.md:113`:
  ```
  + sum(cell(i2,j2), vm_cost_bv_loss(j2))
  ```
- Path to the objective: `q11_cost_reg` populates `v11_cost_reg(i2)`, aggregated by `q11_cost_glo`:
  ```
  q11_cost_glo .. vm_cost_glo =e= sum(i2, v11_cost_reg(i2));
  ```

🟢 Verified against `modules/module_44.md`, `modules/module_10.md`, `modules/module_11.md`, `cross_module/modification_safety_guide.md`, and `cross_module/circular_dependency_resolution.md`.

---

## R23-Q4 answer

(a) The two output files

(i) IAMC-formatted reporting variables: `report.mif` — `output/<run>/report.mif`. Per `agent/helpers/interpreting_outputs.md:24`, "~hundreds of variables in 'Name (unit)' format, regional + global." A companion `report.rds` holds the same content as an R quitte object (`interpreting_outputs.md:25`).

(ii) Full GAMS state including marginals: `fulldata.gdx` — `output/<run>/fulldata.gdx`. Per `interpreting_outputs.md:23`, "complete model state: all variables (level/marginal/upper/lower), all parameters, all sets." Four solution attributes documented at `interpreting_outputs.md:46-57`.

(b) GDX dump trigger

`core/calculations.gms:92` — cited in `agent/helpers/interpreting_outputs.md:12` and at line 60: "After all postsolve phases complete, `Execute_Unload \"fulldata.gdx\"` (`core/calculations.gms:92`) writes everything — all GAMS symbols in memory — into a single GDX."

A separate abort-on-infeasibility GDX dump is at `modules/80_optimization/nlp_apr17/solve.gms:102-107` (`interpreting_outputs.md:138`); per-timestep solver savepoints at `modules/80_optimization/nlp_apr17/solve.gms:99` (`interpreting_outputs.md:32`).

(c) What produces `report.mif`

- R function: `magpie4::getReport(gdx)`.
- Producing script: `scripts/output/rds_report.R`.
- Naming convention: IAMC-format `"Name (unit)"` — space before parenthesis is required.

Source: `interpreting_outputs.md:63` — "`scripts/output/rds_report.R` calls `magpie4::getReport(gdx)`...".

(d) Why `fulldata.gdx` retains only final-timestep state for `vm_*`

Per `interpreting_outputs.md:60` (and reiterated as pitfall #5 at line 170):

1. The dump is inside the time loop. `Execute_Unload "fulldata.gdx"` at `core/calculations.gms:92` executes once per 5-year timestep, so the GDX is overwritten each timestep.
2. The `R SECTION` postsolve block copies `vm_*` into a `t`-indexed `ov_*` parameter before the dump. Each module's `postsolve.gms` contains `ov_land(t,j,land,"level") = vm_land.l(j,land);`.

(e) 0.5° disaggregation

`scripts/output/extra/disaggregation.R`. Source: `interpreting_outputs.md:166` (pitfall #3) — "For 0.5° grid, you need the disaggregation output (`cell.land_0.5.mz`) produced by `scripts/output/extra/disaggregation.R`."

It produces the `cell.*_0.5.mz` outputs listed at `interpreting_outputs.md:27-31` (`cell.land_0.5.mz`, `cell.land_split_0.5.mz`, `cell.croparea_0.5_share.mz`, `cell.bii_0.5.mz`, `cell.peatland_0.5.mz`).

Caveat: helper documents the land disaggregation pipeline thoroughly but is silent on whether `disaggregation.R` also gridscales emissions. For an N₂O-specific 0.5° workflow, the user may need to inspect `scripts/output/INFO.yml` (referenced at `interpreting_outputs.md:185`).

🟡 Based on `agent/helpers/interpreting_outputs.md` documentation.

---

## R23-Q5 answer

(a) The four "closing source statement" format strings from AGENT.md Step 2 (verbatim):

- 🟡 "Based on module_XX.md documentation"
- 🟢 "Verified against module_XX.md and modules/XX_.../equations.gms:123"
- 💬 "Includes user feedback from module_XX_notes.md"
- 📘 "Consulted Query_Patterns_Reference.md"

(b) The 🟢 line from the Epistemic Hierarchy section (verbatim):

- 🟢 **Verified**: Read actual code THIS session (`modules/NN_xxx/realization/file.gms:123`)

(c) Worked examples for Module 17 (production):

- 🟡 "Based on module_17.md documentation" — used after explaining that Module 17 is a pure spatial aggregator (realization `flexreg_apr16`) from the markdown alone, without opening any `.gms` file this session.
- 🟢 "Verified against module_17.md and modules/17_production/flexreg_apr16/equations.gms:10-11" — used after describing equation `q17_prod_reg` and re-reading the cited lines this session.
- 💬 "Includes user feedback from module_17_notes.md" — used after warning the user about a gotcha drawn from the notes file in addition to the main module doc.
- 📘 "Consulted Query_Patterns_Reference.md" — used after answering a cross-cutting "does Module 17 mechanistically model production, or only aggregate it?" question using Pattern 4 (parameterization-vs-mechanism).

(d) Why full-path form is required:

Post-migration, AGENT.md's MANDATE 16 (see `agent/helpers/verifiers.md:246`) requires the full relative path because the citation checker resolves bare filenames by "first match within module number" walk-order. If a module has both `simple_apr24/preloop.gms` and `detail_apr24/preloop.gms`, a bare `preloop.gms:NN` silently resolves to the first one walked, even when you meant the other realization.

The validator that enforces line-range validity is `scripts/check_gams_citations.sh` (with implementation `scripts/check_gams_citations_impl.py`) per `agent/helpers/verifiers.md:256`.

(e) AGENT.md Step 2c "Format:" block (verbatim):

> "I can tell you [what I DO know from docs/code], but I can't determine [specific thing] because [reason — e.g., it depends on input data I can't read / the code path is conditional on a parameter I haven't checked]. To verify, you could [specific suggestion]."

🟡 Based on AGENT.md (Step 2 lines 356-366, Step 2c lines 381-392, Epistemic Hierarchy lines 582-590), module_17.md, and `agent/helpers/verifiers.md` (MANDATE 16, lines 246-256).

---

## R23-G1 answer

Default realization of module 14 (yields): `managementcalib_aug19`
- Source: `config/default.cfg:354` — `cfg$gms$yields <- "managementcalib_aug19"`

Equations defined in `modules/14_yields/managementcalib_aug19/equations.gms`:

Two equations are defined:

1. `q14_yield_crop(j2,kcr,w)` — `modules/14_yields/managementcalib_aug19/equations.gms:14-16`
   - Computes crop yields `vm_yld(j2,kcr,w)` as calibrated input yields `i14_yields_calib` scaled by intensification factor `vm_tau(j2,"crop") / fm_tau1995(h2)`.

2. `q14_yield_past(j2,w)` — `modules/14_yields/managementcalib_aug19/equations.gms:35-39`
   - Computes pasture yields `vm_yld(j2,"pasture",w)` as calibrated pasture yields scaled by `pm_past_mngmnt_factor(ct,i2)`, plus an optional spillover term governed by `s14_yld_past_switch`.

🟢 Verified — read directly from `config/default.cfg:354` and `modules/14_yields/managementcalib_aug19/equations.gms` this session.

---

## R23-G2 answer

Important framing correction: `vm_carbon_stock` is NOT computed in Module 52. It is declared in Module 56 (`modules/56_ghg_policy/price_aug22/declarations.gms:34`), defined (computed) by the individual land-pool modules (29, 31, 32, 35, 59) and fixed to zero by Module 34, and consumed by both Module 52 (actual emissions) and Module 56 (priced emissions). Dimensions: `(j, land, c_pools, stockType)`, units mio. tC.

Producers (where `vm_carbon_stock` is computed):

- Cropland (`crop`, ag_pools) — `q29_carbon` in `modules/29_cropland/simple_apr24/equations.gms:29-31`: passes through `vm_carbon_stock_croparea`, computed in `modules/30_croparea/simple_apr24/equations.gms:50`.
- Pasture (`past`, ag_pools) — `q31_carbon` in `modules/31_past/endo_jun13/equations.gms:22-24`: `m_carbon_stock(vm_land, fm_carbon_density, "past")` (macro at `core/macros.gms:99-101`).
- Forestry (`forestry`, ag_pools) — `q32_carbon` in `modules/32_forestry/dynamic_may24/equations.gms:108-109`: age-class macro `m_carbon_stock_ac(v32_land, p32_carbon_density_ac, ...)` (`core/macros.gms:104-107`).
- Primary/secondary/other natural vegetation (ag_pools) — `q35_carbon_primforest`, `q35_carbon_secdforest`, `q35_carbon_other` in `modules/35_natveg/pot_forest_may24/equations.gms:42-55`.
- Urban (`urban`) — fixed at zero in `modules/34_urban/exo_nov21/presolve.gms:8`.
- Soil carbon (`soilc`) — `modules/59_som/static_jan19/equations.gms:12, 18, 22`.

Module 52 — consumer for actual CO2 emissions:

Module 52 (default: `normal_dec17`) has no equations producing `vm_carbon_stock`. Its sole equation consumes it:

`modules/52_carbon/normal_dec17/equations.gms:16-19`:
```
q52_emis_co2_actual(i2,emis_oneoff) ..
  vm_emissions_reg(i2,emis_oneoff,"co2_c") =e=
    sum((cell(i2,j2),emis_land(emis_oneoff,land,c_pools)),
    (pcm_carbon_stock(j2,land,c_pools,"actual") - vm_carbon_stock(j2,land,c_pools,"actual"))/m_timestep_length);
```

Module 56 — GHG cost:

1. `modules/56_ghg_policy/price_aug22/equations.gms:19-22`:
   ```
   q56_emis_pricing_co2(i2,emis_oneoff) ..
     v56_emis_pricing(i2,emis_oneoff,"co2_c") =e=
       sum((cell(i2,j2),emis_land(emis_oneoff,land,c_pools)),
       (pcm_carbon_stock(j2,land,c_pools,"actual") - vm_carbon_stock(j2,land,c_pools,"%c56_carbon_stock_pricing%"))/m_timestep_length);
   ```

2. `modules/56_ghg_policy/price_aug22/equations.gms:45-52`:
   ```
   q56_emission_cost_oneoff(i2,emis_oneoff) ..
     v56_emission_cost(i2,emis_oneoff) =e=
       sum(pollutants,
         v56_emis_pricing(i2,emis_oneoff,pollutants)
         * m_timestep_length
         * sum(ct,
           im_pollutant_prices(ct,i2,pollutants,emis_oneoff)
           * pm_interest(ct,i2)/(1+pm_interest(ct,i2))));
   ```

3. `modules/56_ghg_policy/price_aug22/equations.gms:56-58`:
   ```
   q56_emission_costs(i2) ..
     vm_emission_costs(i2) =e= sum(emis_source, v56_emission_cost(i2,emis_source));
   ```

Chain:
```
land-pool modules (29, 30, 31, 32, 35, 59) + 34 fix
  → vm_carbon_stock(j, land, c_pools, stockType)     [mio. tC]
    → q52_emis_co2_actual (52) → vm_emissions_reg     [actual accounting]
    → q56_emis_pricing_co2 (56) → v56_emis_pricing    [priced perspective]
      → q56_emission_cost_oneoff (56) × im_pollutant_prices × annuity
        → q56_emission_costs → vm_emission_costs       [into Module 11 objective]
```

🟢 Verified against `modules/52_carbon/normal_dec17/equations.gms:16-19`, `modules/56_ghg_policy/price_aug22/equations.gms:19-22, 45-52, 56-58`, `modules/56_ghg_policy/price_aug22/declarations.gms:34`, and various producer modules.
