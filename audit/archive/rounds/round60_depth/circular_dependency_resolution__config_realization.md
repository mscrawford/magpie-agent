# R60 depth audit — `cross_module/circular_dependency_resolution.md`

**Lens**: `config_realization` (entry from `config/default.cfg` + realization directory listings; defaults, `cfg$gms$*` switches, realization names, default-vs-alternative)
**Ground truth**: MAgPIE `develop` read-only worktree (`<develop>`). Every shell command below was run with cwd = that worktree, except paths starting `audit/`, `core_docs/` or `modules/module_*.md`, which are magpie-agent paths.
**Role-map reference**: `audit/integrated/depth_rolemap.json`, consulted **first** for every `vm_`/`pm_`/`im_`/`pcm_`/`fm_` attribution claim, then confirmed with both-endpoints greps against code.
**Claims verified**: 58
**Result**: **20 bugs** (2 Critical, 10 Major, 8 Minor), 8 deferred.

> **Merge note**: an earlier pass of this same lens/doc pair had written a 15-bug report to this path. This file is a **superset**: every finding retained from that pass was **re-derived independently against code this session** (marked `[re-derived]`), and 5 findings are new to this pass (marked `[new]`). Two of that pass's findings were demoted to *deferred* here where I could not reproduce the claimed harm. Nothing was carried over on trust.

---

## 0. What the lens cleared (negative results — do not re-litigate)

The realization/default layer of this doc is in good shape: **every realization it names is the config default**, and it never describes a non-default realization as active. No wrong-realization Critical.

| Doc claim | Code | Verdict |
|---|---|---|
| `10_land/landmatrix_dec18` | `config/default.cfg:232` (sole realization) | ✅ default |
| `13_tc/endo_jan22` | `config/default.cfg:293` (alt: `exo`) | ✅ default |
| `14_yields/managementcalib_aug19` | `config/default.cfg:357` (alt: `dynRegPastrTau_apr26`) | ✅ default |
| `21_trade/selfsuff_reduced`, pool-based; `selfsuff_reduced_bilateral22` non-default | `config/default.cfg:653`; `ls -d modules/21_trade/*/` | ✅ default, correctly flagged |
| `41_.../endo_apr13` | `config/default.cfg:1322` (alt: `static`) | ✅ default |
| `52_carbon/normal_dec17` | `config/default.cfg:1577` (sole realization) | ✅ default |
| `56_ghg_policy/price_aug22` | `config/default.cfg:1634` (sole realization) | ✅ default |
| "`vm_import`/`vm_export` do NOT exist"; bilateral `v21_trade` only in `selfsuff_reduced_bilateral22` | `rg -n "vm_import\|vm_export" modules/ core/` → 0 hits; positive control `rg -ln "v21_trade" modules/21_trade/` → 3 files, **all** under `selfsuff_reduced_bilateral22/` | ✅ |
| `s56_buffer_aff` = 0.5, "half of removals credited" | `config/default.cfg:1788`; used as `(1-s56_buffer_aff)` at `modules/56_ghg_policy/price_aug22/equations.gms:77` | ✅ |
| `s56_c_price_induced_aff` is a 1/0 switch | default **1**, `config/default.cfg:1762` (doc omits the default value but does not misstate it) | ✅ |
| `q10_land_area` snippet (doc §1.2) | `modules/10_land/landmatrix_dec18/equations.gms:13-15` — verbatim | ✅ |
| `pcm_land` / `pcm_carbon_stock` / `pcm_tau` Appendix-A **citations** | `modules/10_land/landmatrix_dec18/postsolve.gms:9`, `modules/56_ghg_policy/price_aug22/postsolve.gms:8`, `modules/13_tc/endo_jan22/postsolve.gms:16` — all three land exactly | ✅ |
| §3.1 step 1 (`i14_yields_calib` / `vm_tau` / `pcm_tau` paragraph) | `modules/14_yields/managementcalib_aug19/equations.gms:14-16` and `:35-39` — exact | ✅ |
| `q52_emis_co2_actual` reads `pcm_carbon_stock` **and** `vm_carbon_stock` | `modules/52_carbon/normal_dec17/equations.gms:16-19` | ✅ |
| Land-conversion cost is area-based (`q39_cost_landcon`), no carbon density | `modules/39_landconversion/calib/equations.gms:12-15` (`calib` is default, `config/default.cfg:1288`) | ✅ |
| `q21_trade_glo` formula; `q21_trade_reg`/`q21_trade_reg_up` split | `modules/21_trade/selfsuff_reduced/equations.gms:12-14, 31, 39` | ✅ |
| `pm_land_conservation(t,j,land,consv_type)` signature, declared M22 | `modules/22_land_conservation/area_based_apr22/declarations.gms:15` | ✅ |
| `im_pollutant_prices(t_all,i,pollutants,emis_source)` signature | `modules/56_ghg_policy/price_aug22/declarations.gms:9` | ✅ |
| `"vegc"` ∈ `c_pools`; `"actual"` ∈ `stockType`; `land_natveg = {primforest, secdforest, other}` | `core/sets.gms:324-325, 262-263`; `modules/56_ghg_policy/price_aug22/sets.gms:212-213` | ✅ |
| "Module 54 (Phosphorus): 0 cycles, 1 connection" | M54's only interface object is `vm_p_fert_costs` (→ M11); it reads none. Sole realization `off`, `config/default.cfg:1608` | ✅ |
| CONOPT / IPOPT / CPLEX all real | `modules/80_optimization/{nlp_apr17,nlp_ipopt,lp_nlp_apr17}`; default `optimization <- "nlp_apr17"`, `c80_nlp_solver <- "conopt4"` (`config/default.cfg:2303,2312`) | ✅ (checked because it read like a fabrication — it is not) |
| `vm_cost_landcon` exists (used in a pseudocode example) | `modules/39_landconversion/calib/declarations.gms:13` | ✅ |
| `pc41_AEI_start(j) = vm_AEI.l(j)` in M41 postsolve | `modules/41_area_equipped_for_irrigation/endo_apr13/postsolve.gms:8` | ✅ |

---

## 1. Bugs

### CDR-01 🔴 Critical — M41: previous-timestep AEI is a **lower** bound, not an upper bound `[re-derived]`

**Doc** `circular_dependency_resolution.md:344`
> "1. **Within timestep**: AEI capacity from **previous timestep** is **upper bound**"

**Reality** — default realization `endo_apr13` (`config/default.cfg:1322`). `vm_AEI(j)` is a positive variable **optimized in the current timestep** (`declarations.gms:19`). Presolve sets a *floor*:
```gams
* modules/41_area_equipped_for_irrigation/endo_apr13/presolve.gms:11
vm_AEI.lo(j) = pc41_AEI_start(j) / ((1 - s41_AEI_depreciation)**(m_timestep_length));
```
With the default `s41_AEI_depreciation = 0` (`input.gms:11`; `config/default.cfg:1332`) that floor is exactly last timestep's AEI. **No `vm_AEI.up` assignment exists anywhere in the model.** The irrigated-area constraint binds against the *current, endogenous* AEI —
`q41_area_irrig(j2) .. sum(kcr, vm_area(j2,kcr,"irrigated")) =l= vm_AEI(j2);` (`equations.gms:10-11`) — and expansion happens **within** the same timestep, priced by `q41_cost_AEI` on `(vm_AEI - pc41_AEI_start)` (`equations.gms:19-23`). The previous timestep never caps irrigation; it only prevents disinvestment. The doc's own step 2 ("Investment: New AEI capacity based on current irrigation use") contradicts its step 1.

Related default-config point: in the **default** croparea realization `simple_apr24` (`config/default.cfg:915`), module 30 does not reference `vm_AEI` at all — it is listed in `modules/30_croparea/simple_apr24/not_used.txt:2`. `vm_AEI` enters a module-30 equation only in the non-default `detail_apr24` (`equations.gms:82`). So in a default run the 30↔41 coupling is entirely `q41_area_irrig` inside module 41.

**Verify**
```
rg -n "vm_AEI\.(up|lo|fx)" modules/
  -> endo_apr13/presolve.gms:11  (.lo)  |  static/presolve.gms:9 (.fx, non-default)
     + 4 ov_AEI output-writing lines in postsolve
positive control: rg -n "vm_land.up" modules/  -> 3 hits (proves ".up" greps work)
rg -n "vm_AEI" modules/30_croparea/  -> detail_apr24/equations.gms:82 ; simple_apr24/not_used.txt:2
```

**Why Critical**: this is the sole "How It Works" mechanism for cycle C3. A modeller debugging "irrigated area exceeded last period's AEI" would conclude the model is broken, or would add a redundant/incorrect `.up` bound — building a modification on an inverted constraint.

**Fix**: "Within timestep: the previous timestep's (depreciated) AEI is a **lower** bound on the endogenous `vm_AEI` (`modules/41_area_equipped_for_irrigation/endo_apr13/presolve.gms:11`); irrigated area is capped by the *current* `vm_AEI`, which may expand in the same timestep at the annuitised cost `q41_cost_AEI`. The temporal link is the cost anchor `pc41_AEI_start`, not a capacity ceiling." Reclassify C3 as **Simultaneous Equations with a one-way ratchet**. Note that under the default `simple_apr24`, module 30 lists `vm_AEI` in `not_used.txt`; and that the non-default `static` realization fixes `vm_AEI.fx` at 1995 levels, dissolving the cycle entirely.

---

### CDR-02 🔴 Critical — the livestock → manure → soil-fertility → yield feedback does not exist in the code `[re-derived]`

**Doc** `circular_dependency_resolution.md:241-245`, `:253`, `:273`
> `vm_prod_reg(i2,kap) [70] → manure availability` / `(Manure affects soil fertility)` / `pm_yields_semi_calib(j,kve,w) [14] → vm_prod(j,kcr) [17]`
> ":253 3. **Across timesteps**: Manure from livestock(t) affects yields(t+1)"
> ":273 - Limit manure impact on yields (Module 59, SOM)"

**Reality** — MAgPIE yields have **no nutrient input at all**. A complete inventory of every interface object referenced anywhere in the default yields realization contains no nitrogen, manure or SOM object:
```
rg -no "(vm_|pm_|im_|fm_|pcm_|sm_)[a-zA-Z0-9_]*" modules/14_yields/managementcalib_aug19/ \
  | awk -F: '{print $NF}' | sort -u
-> fm_aboveground_fraction, fm_carbon_density, fm_croparea, fm_ipcc_bef, fm_tau1995,
   im_growing_stock, im_growing_stock_ysf, pcm_tau, pm_carbon_density_{other,plantation,secdforest}_ac,
   pm_climate_class, pm_land_start, pm_past_mngmnt_factor, pm_yields_semi_calib,
   sm_carbon_fraction, sm_fix_cc, vm_tau, vm_yld
```
`vm_manure` (declared 55_awms) is read only by **50, 51, 53**; `vm_nr_som` and `vm_nr_som_fertilizer` (declared 59_som) are read only by **51** and **50** respectively. Manure and SOM enter the **nitrogen budget / fertiliser requirement**, never `vm_yld` or `i14_yields_calib`. `vm_yld` is fully determined by `q14_yield_crop` / `q14_yield_past` (`equations.gms:14-16, 35-39`).

The **real** 70→14 edge is `pm_past_mngmnt_factor` — declared `modules/70_livestock/fbask_jan16/declarations.gms:41`, computed in `presolve.gms:64-67` from a cattle-number proxy (`p70_incr_cattle`, `f70_pyld_slope_reg`), read at `modules/14_yields/managementcalib_aug19/equations.gms:38`. It is a **pasture-management intensification factor**, not manure, and scales **pasture yields only**.

Secondary defect on the same line: the tag `vm_prod_reg(i2,kap) [70]` is a *reader* tag. `vm_prod_reg` is declared in 17_production and populated by 17/18/20/21; every module-70 occurrence is on an equation RHS (`modules/70_livestock/fbask_jan16/equations.gms:18,28,36,60,65,70`). Elsewhere in the same chain the tags name the declaring/populating module.

**Verify**
```
rg -ln "vm_manure" modules/    -> 55_awms/*, 50_nr_soil_budget/macceff_aug22, 51_nitrogen/rescaled_jan21,
                                  53_methane/ipcc2006_aug22  (no 14_yields)
rg -n  "vm_prod\(" modules/70_livestock/  -> 0 hits
positive control: rg -c "vm_prod_reg\(" modules/70_livestock/fbask_jan16/equations.gms -> 6
rg -n "pm_past_mngmnt_factor" modules/     -> 70 presolve:64-67 (populate) ; 14 equations.gms:38 (read)
```
Role map agrees: `vm_manure {declared 55, read_by [50,51,53,55]}`, `vm_nr_som {declared 59, read_by [51,59]}`, `vm_nr_som_fertilizer {declared 59, read_by [50,59]}`, `pm_past_mngmnt_factor {declared 70, read_by [14,70]}`.

**Cross-doc**: the same false claim is in `core_docs/Module_Dependencies.md:194` ("Livestock provides manure affecting yields") — a shared latent doc error; fix both or the fix will be re-imported.

**Why Critical**: §3.1 is flagged ⭐⭐⭐ / 🔴 HIGH / "Test always", and §6.3 instructs the reader to verify every module in the cycle. A reader acting on this modifies/tests 55 and 59 hunting a manure→yield channel that does not exist, and may report a MAgPIE feedback the model does not implement — the AGENT.md primary-directive anti-pattern (here not even parameterized, simply absent).

**Fix**: replace the manure legs with the actual coupling — `vm_yld [14] → vm_prod [30] → vm_prod_reg [17 q17_prod_reg] → feed demand [70 q70_feed]`, return leg `pm_past_mngmnt_factor [70 presolve.gms:64-67] → q14_yield_past [14 equations.gms:35-39]` (cross-timestep, exogenous-proxy driven, pasture only). State explicitly that **manure and soil nitrogen never feed back into yields in MAgPIE**. Delete the ":273 Limit manure impact on yields (Module 59, SOM)" fix. Retag `vm_prod_reg(i2,kap) [declared+populated 17; read by 70]`.

---

### CDR-03 🟠 Major — C1 arrow `vm_prod [17] → pm_yields_semi_calib [14]` is direction-inverted `[re-derived]`

**Doc** `circular_dependency_resolution.md:237`
> `vm_prod(j,kcr) [17] → pm_yields_semi_calib(j,kve,w) [14]`

**Reality** — the edge runs the other way and only the other way. `pm_yields_semi_calib` is declared in M14 (`modules/14_yields/managementcalib_aug19/declarations.gms:19`), assigned in M14's **preloop** from the 1995 calibrated yields (`preloop.gms:116,149`: `pm_yields_semi_calib(j,knbe14,w) = i14_yields_calib("y1995",j,knbe14,w)`) — i.e. **before any solve** — and read by exactly one other module: 17, in presolve (`modules/17_production/flexreg_apr16/presolve.gms:10`, feeding `pm_prod_init`). Nothing in module 14 references `vm_prod` (see the CDR-02 interface inventory). The doc's own prose at `:251` states the correct within-timestep coupling (`vm_tau`), so the diagram contradicts the paragraph beneath it.

**Verify**
```
rg -n "pm_yields_semi_calib" modules/ core/
-> 14_yields/managementcalib_aug19/{declarations.gms:19, preloop.gms:116,149}
   17_production/flexreg_apr16/presolve.gms:10        (+ the dynRegPastrTau_apr26 mirror)
```
Role map: `{declared_in: 14_yields, populated_by: [14], read_by: [14,17]}`.

**Fix**: reverse to `pm_yields_semi_calib(j,kve,w) [14] → pm_prod_init [17]`, and mark it a **preloop-fixed parameter** — it is not part of any within-run cycle. The genuine 17↔14 within-timestep coupling is via `vm_tau`.

---

### CDR-04 🟠 Major — C4: `vm_emissions_reg → vm_reward_cdr_aff` is a false serial hand-off; the branches are parallel `[new]`

**Doc** `circular_dependency_resolution.md:392-396`
> `vm_emissions_reg(i,"co2_c") [52] → reduced (or negative) CO2 emissions` ↓ `vm_reward_cdr_aff(i) [56] → revenue from carbon removal` ↓ `vm_cost_glo [11]`

**Reality** — `vm_reward_cdr_aff` never sees `vm_emissions_reg`:
```gams
* modules/56_ghg_policy/price_aug22/equations.gms:73-79
q56_reward_cdr_aff(j2) .. v56_reward_cdr_aff(j2) =e=
   sum(ct, p56_fader_cpriceaff(ct)) *
   sum(ac, (sum(aff_effect,(1-s56_buffer_aff)*vm_cdr_aff(j2,ac,aff_effect))
            * sum((cell(i2,j2),ct), p56_c_price_aff(ct,i2,ac))) / ((1+...pm_interest...)**(ac.off*5)))
   * sum((cell(i2,j2),ct), pm_interest(ct,i2)/(1+pm_interest(ct,i2)));
```
`vm_cdr_aff` is declared **and populated in M32** (`modules/32_forestry/dynamic_may24/declarations.gms:83`; `equations.gms:37,42`) and read only by 32 and 56. `vm_emissions_reg` is read in M56 only by `q56_emis_pricing` / `q56_emis_pricing_co2` (`equations.gms:15-22`), which flow to `v56_emission_cost` → `vm_emission_costs`. The two routes into the objective are **parallel**, not serial:

- carbon stock → `q52_emis_co2_actual` → `vm_emissions_reg` → `q56_emis_pricing_co2` → `v56_emission_cost` → `vm_emission_costs` → `vm_cost_glo`
- **`vm_cdr_aff` (M32)** → `q56_reward_cdr_aff` → `vm_reward_cdr_aff` → `vm_cost_glo`

This is the R51 pattern (MANDATE 21): both consumers read shared/independent inputs; neither reads the other's output. The chain also drops `vm_cdr_aff` — the actual afforestation-incentive interface — entirely.

**Verify**
```
rg -n "vm_cdr_aff" modules/
  -> 32_forestry/dynamic_may24/{declarations.gms:83, equations.gms:37,42}  (populate)
     56_ghg_policy/price_aug22/equations.gms:77                            (read)
rg -n "vm_emissions_reg" modules/56_ghg_policy/price_aug22/equations.gms   -> line 17 only
```
Role map: `vm_cdr_aff {declared 32_forestry, populated_by [32], read_by [32,56]}`.

**Fix**: split the C4 chain into the two parallel branches above and insert the missing node `vm_cdr_aff(j,ac,aff_effect) [32 q32_cdr_aff]` between forestry expansion and the M56 reward. State that `vm_emissions_reg` and `vm_reward_cdr_aff` meet only in the objective (`vm_cost_glo`, M11).

---

### CDR-05 🟠 Major — `vm_land(j,"crop")` attributed to module 30; the crop slice is populated by module 29 `[re-derived]`

**Doc** `circular_dependency_resolution.md:386`
> `vm_land(j,"crop") [30] → competes for land (crop ↓ as forest ↑)`

**Reality** — `vm_land` is declared in M10; the `"crop"` slice is set on the LHS of `q29_cropland` in the **default** cropland realization `detail_apr24` (`config/default.cfg:814`):
```gams
* modules/29_cropland/detail_apr24/equations.gms:12
vm_land(j2,"crop") =e= sum((kcr,w), vm_area(j2,kcr,w)) + vm_fallow(j2) + sum(ac, v29_treecover(j2,ac));
```
(the alternative `simple_apr24/equations.gms:13` drops the fallow and tree-cover terms). M30 (default `simple_apr24`) only **reads** it, on the RHS of the bioenergy-tree target `modules/30_croparea/simple_apr24/equations.gms:23`. The neighbouring C4 entries tag the populating module (`vm_land(j,"forestry") [32]` ✓, `vm_emissions_reg [52]` ✓), so `[30]` is wrong under the chain's own convention and under both alternatives (declaring module would be `[10]`). Module 29 is also missing from the C4 module list at `:378` and from the C4 row of the §8.1 catalog (`:743`).

**Verify**
```
rg -n 'vm_land\(j2,"crop"\)' modules/
-> LHS "=e=" only at 29_cropland/detail_apr24/equations.gms:12 and simple_apr24/equations.gms:13;
   every 30_croparea hit is RHS.
```
Role map: `vm_land populated_by [10,29,31,32,34,35]` — 30 appears only under `read_by`.

**Fix**: `vm_land(j,"crop") [29 q29_cropland]`, and add 29_cropland to the C4 module list in §3.4 and to the §8.1 C4 row.

---

### CDR-06 🟠 Major — conservation bounds attributed to module 22; they are applied in 35_natveg / 31_past, and the rendered inequality drops the restore term `[re-derived]`

**Doc** `circular_dependency_resolution.md:302` (with `:288` and `:292` carrying the same misdirection via `[10]`)
> `vm_land(j,land_natveg) ≥ pm_land_conservation(t,j,land_natveg,"protect")  [22, bounds]`

**Reality** — module 22 (`area_based_apr22`, the only realization) has **no `presolve.gms` and no `equations.gms`**; its only in-loop file is `presolve_ini.gms`, which merely *reads* `vm_land.lo(j,"crop")` (lines 86, 97, 108). The bounds are set elsewhere:
```
modules/35_natveg/pot_forest_may24/presolve.gms:162  vm_land.lo(j,"primforest") <- pm_land_conservation(...,"protect")  [conditional]
modules/35_natveg/pot_forest_may24/presolve.gms:201  vm_land.lo(j,"secdforest") = pm_land_conservation(...,"protect") + p35_land_restoration(j,"secdforest")
modules/35_natveg/pot_forest_may24/presolve.gms:231  vm_land.lo(j,"other")      = pm_land_conservation(...,"protect") + p35_land_restoration(j,"other")
modules/31_past/endo_jun13/presolve.gms:9            vm_land.lo(j,"past")       = sum(consv_type, pm_land_conservation(t,j,"past",consv_type))
```
Two consequences: (a) `[22, bounds]` and `[10]` both point at modules that never assign the bound; (b) the rendered inequality omits `+ p35_land_restoration` for secdforest/other. A related classification issue: M22's own inputs are all **lagged or presolve** values (`pcm_land` at `presolve_ini.gms:16,17,55,66`), so the 10→22 leg is sequential/temporal, not the "Simultaneous Equations" the doc assigns to the whole C2 cycle at `:295`.

**Verify**
```
ls modules/22_land_conservation/area_based_apr22/
  -> declarations.gms input input.gms preloop.gms presolve_ini.gms realization.gms sets.gms
rg -n "vm_land" modules/22_land_conservation/   -> only vm_land.lo(j,"crop") reads at :86,97,108
rg -n "pm_land_conservation" modules/35_natveg/ modules/31_past/  -> the bound assignments above
```

**Fix**: attribute the bound to `modules/35_natveg/pot_forest_may24/presolve.gms:162,201,231` and `modules/31_past/endo_jun13/presolve.gms:9`; module 22 supplies the *parameter* only. Add the `+ p35_land_restoration` term. Split the C2 resolution type: "10↔35 simultaneous; 22→35 sequential (parameter computed in M22's `presolve_ini.gms` from lagged `pcm_land`)".

---

### CDR-07 🟠 Major — `im_pollutant_prices` units are USD per **tC**, not USD/tCO2 `[re-derived]`

**Doc** `circular_dependency_resolution.md:410`
> "- `im_pollutant_prices`: Carbon price trajectory (0-1000 USD/tCO2)"

**Reality** — `modules/56_ghg_policy/price_aug22/declarations.gms:9`: "Certificate prices for N2O-N CH4 CO2-C used in the model (**USD17MER per Mg**)", i.e. per Mg of the carrier species; for `co2_c` that is per Mg **carbon** — a factor 44/12 ≈ 3.67 from per-tCO2. Corroborated in the same realization:
```gams
* modules/56_ghg_policy/price_aug22/input.gms:67
s56_minimum_cprice   Minium C price (USD17MER per tC) / 3.67 /
* preloop.gms:74 clips im_pollutant_prices(...,"co2_c",...) to exactly this scalar
* preloop.gms:80-82 converts the CO2-eq caps to the model basis by *12/44
```

**Verify**
```
rg -n "im_pollutant_prices|s56_minimum_cprice" \
   modules/56_ghg_policy/price_aug22/{declarations,input,preloop}.gms
```

**Fix**: "(USD17MER per Mg C for `co2_c`; ≈ ×3.67 lower than the same price quoted per tCO2)". Replace the unsourced "0-1000" range with the default scenario `c56_pollutant_prices <- "R34M410-SSP2-NPi2025"` (`config/default.cfg:1734`).

---

### CDR-08 🟠 Major — "`im_*` = Input data (exogenous, never changes)" is false `[re-derived]`

**Doc** `circular_dependency_resolution.md:61`
> "- `im_*` = **Input data** (exogenous, never changes)"

**Reality** — `im_` marks a module **interface** parameter, not immutability; several are recomputed **inside the timestep loop**. `im_growing_stock(t,j,ac,land_timber)` is assigned every timestep in module 14's presolve from `pm_carbon_density_*`, `fm_carbon_density`, `pm_climate_class` and `fm_ipcc_bef`, then read by 32 and 35:
```
modules/14_yields/managementcalib_aug19/presolve.gms:24,33,42,51,64,76,78,80,81
```
`im_pollutant_prices` is likewise rescaled in M56 preloop by the devstate scaling, the fader, `s56_cprice_red_factor` and the min/max caps (`preloop.gms:37-89`).

This matters *here specifically*: §5.2's classification decision tree and §2.3's "Type 3: Sequential Execution" both lean on `im_*` being immutable preloop data, so the gloss propagates into cycle mis-classification.

**Verify**
```
rg -n "^ *im_growing_stock" modules/14_yields/managementcalib_aug19/presolve.gms   -> 9 assignment lines
rg -n "im_growing_stock" modules/*/*/declarations.gms  -> declared in 14_yields (both realizations)
```
Role map: `im_growing_stock {declared 14_yields, populated_by [14], read_by [14,32,35]}`.

**Fix**: "`im_*` = **interface input parameter** (module-external; usually loaded or derived in `preloop`, but some are recomputed each timestep in `presolve` — e.g. `im_growing_stock` in 14_yields)."

---

### CDR-09 🟠 Major — "All `pcm_*` variables are updated in `postsolve.gms`" is false for `pcm_land` `[re-derived]`

**Doc** `circular_dependency_resolution.md:980`
> "**Pattern**: All `pcm_*` variables are updated in `postsolve.gms` from corresponding `vm_*` optimal values"

**Reality** — `pcm_land` is re-assigned *outside* postsolve in three other modules, all in default realizations, and — critically — **inside the timestep, before the solve**:
```
modules/35_natveg/pot_forest_may24/presolve.gms:39   pcm_land(j,"primforest") = pcm_land(j,"primforest") - p35_disturbance_loss_primf(t,j);
modules/35_natveg/pot_forest_may24/presolve.gms:131  pcm_land(j,"secdforest") = sum(ac, pc35_secdforest(j,ac));
modules/35_natveg/pot_forest_may24/presolve.gms:137  pcm_land(j,"other")      = sum((othertype35,ac), pc35_land_other(j,othertype35,ac));
modules/32_forestry/dynamic_may24/presolve.gms:101   pcm_land(j,"forestry")   = sum((type32,ac), v32_land.l(j,type32,ac));
modules/34_urban/exo_nov21/preloop.gms:17            pcm_land(j,"urban")      = i34_urban_area("y1995",j);
modules/10_land/landmatrix_dec18/start.gms:11        pcm_land(j,land)         = pm_land_start(j,land);
```
So the parameter the optimiser actually sees is *previous state adjusted in presolve* (M35 line 39 subtracts disturbance losses from the lagged primforest state), not a pure `vm_*.l` copy — material for a document whose thesis is that `pcm_*` provides clean temporal decoupling.

**Verify**
```
rg -n "^ *pcm_land\(" modules/    -> 17 hits, including all six lines above
```

**Fix**: "Most `pcm_*` are refreshed in `postsolve.gms` from `vm_*.l`, but some are **additionally rewritten in `presolve.gms`/`preloop.gms`** by the module that owns the land pool — `pcm_land` for `primforest`/`secdforest`/`other` (M35 presolve), `forestry` (M32 presolve), `urban` (M34 preloop). Grep `^ *pcm_<name>(` model-wide before assuming a single writer."

---

### CDR-10 🟠 Major — `pm_water_avail` does not exist, yet is presented as "existing" `[re-derived]`

**Doc** `circular_dependency_resolution.md:591-594`, under "✅ SAFE"
```gams
vm_area.up(j,kcr,"irrigated")$(pm_water_avail(j) < threshold) = 0;
* Does NOT create new dependency (just uses existing pm_water_avail)
```

**Reality** — no such object anywhere. The real interface is `im_wat_avail(t,wat_src,j)` (`modules/43_water_availability/total_water_aug13/declarations.gms:9`, "Water availability (mio. m^3 per yr)"). The doc explicitly asserts the invented name is "existing".

**Verify**
```
rg -n "pm_water_avail" modules/ core/          -> 0 hits
positive control: rg -c "im_wat" modules/43_water_availability/  -> non-zero in 3 files
rg -n "wat_avail" modules/43_water_availability/*/declarations.gms -> im_wat_avail(t,wat_src,j)
```

**Fix**: use `im_wat_avail`, respecting its time and source dimensions — e.g. `$(sum((ct,wat_src), im_wat_avail(ct,wat_src,j)) < threshold)` — or relabel the whole snippet with an explicit `<pm_placeholder>`.

---

### CDR-11 🟠 Major — citation drift: `Source: module_56.md (lines 60-79)` `[re-derived]`

**Doc** `circular_dependency_resolution.md:414`, sourcing the "Critical Parameters" block (`im_pollutant_prices`, `s56_buffer_aff`, `s56_c_price_induced_aff`).

**Reality** — `modules/module_56.md:60-79` is the **q56_emis_pricing / q56_emis_pricing_co2** equation walkthrough (`v56_emis_pricing` components, `emis_annual` vs `emis_oneoff`). None of the three parameters appears there; they live at `modules/module_56.md:40-41` (switch table with defaults), `:287`, `:310`, `:691-697`.

**Verify**
```
rg -n "s56_buffer_aff|s56_c_price_induced_aff" modules/module_56.md
-> 40, 41, 257, 287, 310, 691, 697, 785, 858, 906   (nothing in 60-79)
```

**Fix**: `Source: modules/module_56.md:40-41 (switch table) and :287-310 (buffer semantics)`.

---

### CDR-12 🟠 Major — citation drift: `Source: Module_Dependencies.md (lines 149-179)` `[re-derived]`

**Doc** `circular_dependency_resolution.md:745`, sourcing the four core cycles C1-C4.

**Reality** — `core_docs/Module_Dependencies.md:149-179` is the layered-architecture diagram (Layers 4-6) plus §3.2 Hub-and-Spoke Patterns. The circular-dependency content starts at `:182` (`### 4. Circular Dependencies (Feedback Loops)`), with the numbered cycle list at `:186-215`.

**Verify**
```
awk 'NR>=145 && NR<=215 {print NR"\t"$0}' core_docs/Module_Dependencies.md
```

**Fix**: `Source: core_docs/Module_Dependencies.md:182-215`.

---

### CDR-13 🟡 Minor — `vm_emissions_reg(i,"co2_c")` drops the `emis_source` dimension `[new]`

**Doc** `circular_dependency_resolution.md:392`
**Reality** — `vm_emissions_reg(i,emis_source,pollutants)` (`modules/56_ghg_policy/price_aug22/declarations.gms:40`); M52 populates only the slice `vm_emissions_reg(i2,emis_oneoff,"co2_c")` (`modules/52_carbon/normal_dec17/equations.gms:17`). Every other entry in the same diagram is dimensionally complete (`im_pollutant_prices(t_all,i,pollutants,emis_source)`, `vm_carbon_stock(j,"forestry","vegc","actual")`), so the truncation reads as authoritative.
**Verify**: `rg -n "vm_emissions_reg" modules/56_ghg_policy/price_aug22/declarations.gms`
**Fix**: `vm_emissions_reg(i,emis_oneoff,"co2_c") [52]`.

---

### CDR-14 🟡 Minor — §2.2 pseudo-equation over-broadens `q17_prod_reg` to `kall` `[re-derived]`

**Doc** `circular_dependency_resolution.md:143`
> `vm_prod_reg(i,kall) = sum(cell(i,j), vm_prod(j,kall))               [q17_prod_reg]`

**Reality** — `q17_prod_reg(i2,k) .. vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k));` (`modules/17_production/flexreg_apr16/equations.gms:10-11`). `k(kall)` = **28 primary** products (`modules/14_yields/managementcalib_aug19/sets.gms:12-16`); `kall` = **41** members (`core/sets.gms:228-235`), adding the secondary/processed goods (`oils, oilcakes, sugar, molasses, alcohol, ethanol, distillers_grain, brans, scp, fibres`, `res_*`), whose regional production is set in module 20, not by `q17_prod_reg`. (The *declaration* `vm_prod_reg(i,kall)` at `flexreg_apr16/declarations.gms:10` is over `kall` — it is the **equation domain** the doc gets wrong.)
**Verify**: `cat -n modules/17_production/flexreg_apr16/equations.gms`; `sed -n '8,20p' modules/14_yields/managementcalib_aug19/sets.gms`
**Fix**: write the equation domain as `k`, and add "secondary products (`kall \ k`) get `vm_prod_reg` from 20_processing".

---

### CDR-15 🟡 Minor — `vm_carbon_stock(j,"forestry",…) [56]` misdirects under the chain's own tagging convention `[re-derived]`

**Doc** `circular_dependency_resolution.md:390`
> `vm_carbon_stock(j,"forestry","vegc","actual") [56] → carbon sequestration`

**Reality** — 56_ghg_policy *declares* `vm_carbon_stock` (`declarations.gms:34`) and *reads* it (`equations.gms:22`), but the `"forestry"` slice is **populated by module 32**:
```gams
* modules/32_forestry/dynamic_may24/equations.gms:108
q32_carbon(j2,ag_pools,stockType) .. vm_carbon_stock(j2,"forestry",ag_pools,stockType) =e= ...
```
Role map: `populated_by [29,31,32,34,35,59]`, `read_by [52,56,59]`. Every *other* tag in this C4 chain names the populating module, so a reader following `[56]` looks for the forestry carbon equation in a module that does not contain it.
**Severity note**: graded Minor rather than Major because `[56]` is defensible as the *declaring* module and the doc never states its tagging convention.
**Verify**: `rg -n "vm_carbon_stock" modules/32_forestry/` → `dynamic_may24/equations.gms:108` (LHS).
**Fix**: `vm_carbon_stock(j,"forestry","vegc","actual") [declared 56; populated by 32 q32_carbon; read by 52/56]`.

---

### CDR-16 🟡 Minor — C1 diagram puts `vm_prod(kli)` under Module 70; M70 never touches cellular `vm_prod` `[new]`

**Doc** `circular_dependency_resolution.md:206`
> `Module 14 (Yields) ←→ Module 13 (TC) ←→ Module 70 (Livestock)` / `… vm_prod(kli)`

**Reality** — `rg -n "vm_prod\(" modules/70_livestock/` → **0 hits** (positive control: `rg -c "vm_prod_reg\(" modules/70_livestock/fbask_jan16/equations.gms` → 6). M70 (default `fbask_jan16`) works exclusively with the *regional* `vm_prod_reg`. The cellular livestock slices are populated by **M71**: `vm_prod(j2,kli_rum)` / `vm_prod(j2,kli_mon)` at `modules/71_disagg_lvst/foragebased_aug18/equations.gms:38,45`. The doc's own line `:241` uses `vm_prod_reg` correctly.
**Fix**: `vm_prod_reg(i,kli)` under M70, or move `vm_prod(j,kli)` under M71.

---

### CDR-17 🟡 Minor — Appendix A `pcm_carbon_stock` row: wrong declared domain, and M59 missing as co-updater `[re-derived]`

**Doc** `circular_dependency_resolution.md:976`
> `| pcm_carbon_stock(j,land,ag_pools,stockType) | 56_ghg_policy | Previous carbon stocks | modules/56_ghg_policy/price_aug22/postsolve.gms:8 |`

**Reality** — declared over `c_pools`, not `ag_pools` (`modules/56_ghg_policy/price_aug22/declarations.gms:19`); `c_pools = {vegc,litc,soilc}` (`core/sets.gms:324-325`), `ag_pools = {vegc,litc}` (`modules/56_ghg_policy/price_aug22/sets.gms:209-210`) is only the slice M56's postsolve writes. The `"soilc"` slice is updated by **M59** in both realizations — default `cellpool_jan23` (`config/default.cfg:1937`) at `postsolve.gms:13`, and `static_jan19` at `postsolve.gms:9`. A reader tracing lagged *soil* carbon to module 56 finds nothing there.
**Verify**: `rg -n "^ *pcm_carbon_stock\(" modules/` → 56 (postsolve:8, preloop:10), 59 static (postsolve:9, preloop:11), 59 cellpool (postsolve:13, preloop:30,33). Role map: `populated_by ["56","59"]`.
**Fix**: signature → `pcm_carbon_stock(j,land,c_pools,stockType)`; "Module" → `56 (ag_pools) + 59 (soilc)`; "Updated in" → `.../price_aug22/postsolve.gms:8` **and** `modules/59_som/cellpool_jan23/postsolve.gms:13`.

---

### CDR-18 🟡 Minor — timesteps are not uniformly 5-yearly under the default `c_timesteps` `[new]`

**Doc** `circular_dependency_resolution.md:41-51` and `:1004`
> "Timestep 1: Optimize 1995-2000 (5 years) … … continue until 2100" / "FOR EACH TIMESTEP (t = 1995, 2000, 2005, ..., 2100)"

**Reality** — default `cfg$gms$c_timesteps <- "coup2100"` (`config/default.cfg:133`) resolves to
```
core/sets.gms:188
$If "%c_timesteps%"== "coup2100" /y1995,...,y2050,y2055,y2060,y2070,y2080,y2090,y2100/;
```
— 5-yearly through 2060, then **10-yearly** (2060→2070→2080→2090→2100). The doc's own stability test inherits the wrong step length for the second half of the century ("<20% per 5-year timestep", `:263`), where `m_timestep_length` doubles and per-timestep changes mechanically grow.
**Verify**: `rg -n "coup2100" core/sets.gms config/default.cfg`
**Fix**: "…5-yearly to 2060, then 10-yearly to 2100 under the default `c_timesteps = "coup2100"` (`core/sets.gms:188`); normalise stability thresholds by `m_timestep_length`."

---

### CDR-19 🟡 Minor — "Modifying Module 10 (Land): … 15 consumers" undercounts under every definition tried `[new]`

**Doc** `circular_dependency_resolution.md:584`

**Reality** — modules reading any M10-declared interface object (`vm_land`, `pcm_land`, `vm_lu_transitions`, `vm_landexpansion`, `vm_landreduction`, `vm_landdiff`, `vm_cost_land_transition`, `pm_land_start`, `pm_land_hist`, `fm_land_iso`, `fm_luh2_side_layers`) = **18**. Excluding M80 — which lists `vm_landdiff` in `modules/80_optimization/nlp_apr17/not_used.txt:2` and therefore consumes nothing from M10 under the **default** realization — gives **17**. Restricting to `vm_*`/`pcm_*` only gives 17 (16 without M80). No definition reaches 15.
The figure is inherited from `core_docs/Module_Dependencies.md:179` ("10_land: 15 out"), so fix both or it will be re-imported.
**Severity note**: graded Minor, not Major, because the counting rule ("consumers") is nowhere defined in either doc — the direction and magnitude of the error are solid, the exact target number is convention-dependent.
**Verify**: role-map aggregation over `declared_in == "10_land"`, cross-checked with `rg -n "vm_landdiff" modules/80_optimization/`.
**Fix**: "≈17 consuming modules under the default config (M80 consumes M10 output only in the non-default `lp_nlp_apr17`)"; better, replace the hard-coded number with the re-runnable role-map derivation.

---

### CDR-20 🟡 Minor — machine-local scratch path published in a public doc `[re-derived]`

**Doc** `circular_dependency_resolution.md:497`
> "Visualize using GraphViz (files in `/tmp/magpie_analysis/`)"

**Reality** — `/tmp/magpie_analysis` does not exist and is in neither repository (`ls -d /tmp/magpie_analysis` → "No such file or directory"). This is a dead machine-local pointer in a public repo, and it instructs the reader to look somewhere that will never contain anything.
**Fix**: delete, or replace with the command that regenerates the graph plus a repo-relative output path.

---

## 2. Deferred (checked; not scored)

1. `:60` — "`pcm_*` … ('p' = parameter, 'cm' = current module)". MAgPIE's naming table lives in the external Coding Etiquette; `README.md:44-45` only points at it and the repo carries no `CONTRIBUTING.md`. Not code-checkable. Note the internal tension worth resolving once a source exists: `reference/GAMS_MAgPIE_Patterns.md:225,521` glosses `pcm_` as "Previous Current Module", and `pcm_land` is declared in M10 but read by 17 other modules — "current module" reads oddly for an interface parameter.
2. `:11`, `:749`, `:1036` — the "26 circular dependency cycles" figure. It matches `core_docs/Module_Dependencies.md:186`, but neither doc carries a re-runnable artifact, and §8.2 concedes only 4 are documented plus 6 "suspected". Falls under AGENT.md rule 4 (no figure without an artifact); I did not re-derive a cycle count, so I do not assert 26 is wrong.
3. `:390` tagging convention generally — the C4 chain mixes declaring-module and populating-module tags. Scored only where the tag matches neither (CDR-05) or contradicts the chain's dominant convention (CDR-15); the convention itself should be stated once in the doc rather than audited per-line.
4. `:723-724` — "Independent modules (37, 45, 54) can be run in parallel" / "water system: 41-42-43 … no cycles". Checked: M37→38, M45→{14,52,58,59}, M54→11 are all pure sources with no inbound interface reads; within {42,43} both couplings run 43→42 (`im_wat_avail` read by 42; `vm_watdem` slices set by 43), so no 42↔43 cycle. But M41 is coupled to M30 (the doc's own C3) and M42 reads M17/M30 outputs, so "isolatable" is architecturally loose rather than code-false. The paragraph is explicitly speculative ("Opportunities").
5. `:135-137` — the §2.2 ASCII return arrow `└── vm_supply/trade ─────┘` into Module 17. `vm_supply` is declared+populated by 16_demand and read only by 16 and 21 (`rg -n "vm_supply" modules/17_production/` → 0 hits), so nothing flows 21→17 via `vm_supply`; but the label is too vague to score, and the genuine simultaneity (M21's inequalities constrain M17's `vm_prod_reg`) is real.
6. `:600`, `:608`, `:683-711` — hypothetical "BEFORE/AFTER" snippets. `vm_cost_landcon` exists (M39) but is paired with a 2-index `pcm_carbon_stock`; all are explicitly labelled examples, so no bug recorded (unlike CDR-10, where the doc asserts the invented name is "existing").
7. `:150`, `:831`, `:1012` — CONOPT / IPOPT / CPLEX. All three exist; the doc never claims which is default (`nlp_apr17` + `c80_nlp_solver = "conopt4"`). An omission of the default, not an error.
8. All R verification snippets (`land_conservation()`, `AEI()`, `costs(components=...)`, `yields(...)`, `gdx$status$solve_status`, `readGDX(..., select=list(t=...))`) — magpie4 API surface, not checkable against the GAMS worktree. Route to `agent/helpers/magpie4_reference.md` in a separate pass.

---

## 3. Suggested fix ordering

1. **CDR-01, CDR-02** (Critical) — both invert or invent a *mechanism*; both also require a matching edit to `core_docs/Module_Dependencies.md:194` (manure→yields) so the error is not re-imported.
2. **CDR-03, CDR-04, CDR-05, CDR-06** — the two cycle chains (§3.1 C1, §3.4 C4) should be rewritten as units rather than patched arrow-by-arrow; state the `[NN]` tagging convention explicitly while doing so.
3. **CDR-07, CDR-08, CDR-09** — glossary/appendix claims that the rest of the doc leans on (unit, `im_*` semantics, `pcm_*` write pattern).
4. **CDR-11, CDR-12, CDR-20** — pointer hygiene, mechanical.
5. Remaining Minors.
