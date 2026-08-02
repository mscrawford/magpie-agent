# R60 depth audit — `cross_module/circular_dependency_resolution.md`

**Lens**: `config_realization` (defaults, `cfg$gms$*` switches, realization names, default-vs-alternative)
**Ground truth**: MAgPIE `develop` read-only worktree (referred to below as `<develop>`; all commands were run with cwd = that worktree unless the path starts with `audit/` or `core_docs/`, which are magpie-agent paths).
**Role-map reference**: `audit/integrated/depth_rolemap.json` (checked first for every `vm_`/`pm_`/`im_`/`pcm_`/`fm_` attribution claim, then confirmed with both-endpoints greps).
**Claims verified**: 57
**Result**: 15 bugs (1 Critical, 7 Major, 7 Minor), 6 deferred.

---

## Lens summary: what checked out

Everything in the realization/default layer that the doc names explicitly is **correct** — this doc leads with defaults throughout:

| Doc claim | Code | Verdict |
|---|---|---|
| `56_ghg_policy/price_aug22` | `cfg$gms$ghg_policy <- "price_aug22"` (`config/default.cfg:1634`) | ✅ default |
| `52_carbon/normal_dec17` | `config/default.cfg:1577` | ✅ default |
| `10_land/landmatrix_dec18` | `config/default.cfg:232` (only realization) | ✅ default |
| `13_tc/endo_jan22` | `config/default.cfg:293` | ✅ default |
| `14_yields/managementcalib_aug19` | `config/default.cfg:357` (alt: `dynRegPastrTau_apr26`) | ✅ default |
| `21_trade/selfsuff_reduced` is default, pool-based; `selfsuff_reduced_bilateral22` is non-default | `config/default.cfg:653`; `ls modules/21_trade/` | ✅ default, correctly flagged |
| `41_.../endo_apr13` | `config/default.cfg:1322` | ✅ default |
| `vm_import`/`vm_export` do not exist; `v21_trade` only in `selfsuff_reduced_bilateral22` | whole-tree grep empty (positive control `vm_supply` returns 5 files); `modules/21_trade/selfsuff_reduced_bilateral22/declarations.gms:23` | ✅ |
| `s56_buffer_aff` default 50 %, half of removals credited | `modules/56_ghg_policy/price_aug22/input.gms:71` `/ 0.5 /`; used as `(1-s56_buffer_aff)` at `equations.gms:77`; `config/default.cfg:1788` | ✅ |
| `s56_c_price_induced_aff` (1/0) | `input.gms:69` `/ 1 /`; `config/default.cfg:1762` | ✅ |
| `q52_emis_co2_actual` reads `pcm_carbon_stock` **and** `vm_carbon_stock` | `modules/52_carbon/normal_dec17/equations.gms:16-19` | ✅ |
| Land-conversion cost is area-based (`q39_cost_landcon`), no carbon density | `modules/39_landconversion/calib/equations.gms:12` (`calib` is the default, `config/default.cfg:1288`) | ✅ |
| `q10_land_area` snippet (doc §1.2) | `modules/10_land/landmatrix_dec18/equations.gms:13-15` — verbatim match | ✅ |
| §3.1 step 1 (the `i14_yields_calib` / `vm_tau` / `pcm_tau` paragraph) | `modules/14_yields/managementcalib_aug19/equations.gms:14-16` and `:35-39`; `modules/13_tc/endo_jan22/postsolve.gms:16` — all three citations land exactly | ✅ (previously repaired; still correct) |
| `q21_trade_glo` formula, `q21_trade_reg`/`q21_trade_reg_up` split | `modules/21_trade/selfsuff_reduced/equations.gms:12-14, 31-42` | ✅ |
| CONOPT / IPOPT / CPLEX are all real | `modules/80_optimization/nlp_ipopt/`, `lp_nlp_apr17/solve.gms:20-34`; default `cfg$gms$optimization <- "nlp_apr17"`, `c80_nlp_solver <- "conopt4"` | ✅ (checked because it looked like a fabrication — it is not) |
| Chapman-Richards forest growth | `core/sets.gms:281` `chap_par`, `modules/52_carbon/normal_dec17/start.gms:16` | ✅ |
| Run horizon "…until 2100" | `c_timesteps = "coup2100"` → `core/sets.gms:188`, last element `y2100` | ✅ |
| `pm_yields_semi_calib(j,kve,w)` signature | `modules/14_yields/managementcalib_aug19/declarations.gms:19` — exact | ✅ |
| `pcm_land`/`pcm_tau` Appendix-A citations (`10_land/.../postsolve.gms:9`, `13_tc/endo_jan22/postsolve.gms:16`) | exact match | ✅ |

---

## Bugs

### B01 — Critical — the livestock→manure→soil-fertility→yield feedback does not exist in the code
**Doc** `circular_dependency_resolution:241-245, 253, 273`
> `vm_prod_reg(i2,kap) [70] → manure availability` / `(Manure affects soil fertility)` / `pm_yields_semi_calib(j,kve,w) [14]`
> "3. **Across timesteps**: Manure from livestock(t) affects yields(t+1)"
> "Fix: … Limit manure impact on yields (Module 59, SOM)"

**Reality**: module 14 (both realizations) touches exactly two interface variables — `vm_tau` and `vm_yld`. It never reads `vm_manure`, `vm_manure_recycling`, `vm_nr_som`, `vm_nr_som_fertilizer`, `vm_nr_inorg_fert_reg`, or any module-17/50/55/59 output. `vm_manure` (declared 55_awms) is read only by 50, 51, 53. Module 59's outputs (`vm_cost_scm`, `vm_nr_som`, `vm_nr_som_fertilizer`) are read only by 11, 51, 50. There is no nutrient→yield channel anywhere in MAgPIE: `vm_yld` = `i14_yields_calib · vm_tau / fm_tau1995` (crops) or `i14_yields_calib · pm_past_mngmnt_factor · (1+s14_yld_past_switch·…)` (pasture).

The **real** 70→14 edge is `pm_past_mngmnt_factor` (declared `modules/70_livestock/fbask_jan16/declarations.gms:41`, computed in `presolve.gms:44-49` from cattle-number proxies driven by `im_pop` and `pm_kcal_pc_initial`, read at `modules/14_yields/managementcalib_aug19/equations.gms:38`) — a **pasture-management intensification factor**, not manure and not soil fertility, and it affects pasture yields only.

**Evidence**: `modules/14_yields/managementcalib_aug19/equations.gms:35-39`; `modules/70_livestock/fbask_jan16/presolve.gms:44-49`.
**Verify**:
```
rg -o 'vm_\w+' modules/14_yields/managementcalib_aug19/*.gms | sort -u
  → only vm_tau and vm_yld
rg -n 'vm_prod|manure|vm_nr_|nutrient|som' modules/14_yields/managementcalib_aug19/*.gms
  → 1 hit, a prose comment at preloop.gms:160 ("historical production and croparea"); positive control `rg -ln vm_tau modules/14_yields/managementcalib_aug19/` returns 2 files
rg -n 'vm_manure|vm_nr_som|vm_prod\(' modules/14_yields/dynRegPastrTau_apr26/*.gms  → empty
```
**Why Critical**: §3.1 is flagged "⭐⭐⭐ / 🔴 HIGH / Test always", and §6.3 tells the reader to "Verify all modules in dependency cycle still function". A reader acting on this tests/modifies 55/59 looking for a manure→yield channel that does not exist, and may report a model feedback MAgPIE does not implement. This is the AGENT.md primary-directive anti-pattern (parameterized ≠ mechanistic; here, not even parameterized).
**Fix**: replace the manure legs of the C1 chain with the actual coupling: `vm_yld [14] → vm_prod [30 q30_prod] → vm_prod_reg [17 q17_prod_reg] → feed demand [70 q70_feed]`, and the return leg `pm_past_mngmnt_factor [70 presolve] → q14_yield_past [14]` (cross-timestep, exogenous-proxy driven). State explicitly that **manure and soil nitrogen never feed back into yields in MAgPIE**. Drop the "Limit manure impact on yields (Module 59, SOM)" fix.

---

### B02 — Major — C1 arrow `vm_prod [17] → pm_yields_semi_calib [14]` is direction-inverted
**Doc** `circular_dependency_resolution:237`
> `vm_prod(j,kcr) [17] → pm_yields_semi_calib(j,kve,w) [14]`

**Reality**: the edge runs the other way and only the other way. `pm_yields_semi_calib` is assigned in module 14's **preloop** from `i14_yields_calib("y1995",…)` (`modules/14_yields/managementcalib_aug19/preloop.gms:116,149`) — before any solve — and is read by module 17 (`modules/17_production/flexreg_apr16/presolve.gms:10`, `pm_prod_init(j,kcr)=sum(w,fm_croparea(...)*pm_yields_semi_calib(j,kcr,w))`). Role map: `pm_yields_semi_calib` → `populated_by:["14"], read_by:["14","17"]`. Nothing in module 14 references `vm_prod`. (The offline calibration in `scripts/calibration/calc_calib.R` is not this edge either: it is off by default, `cfg$recalibrate <- FALSE`, `config/default.cfg:70`, and `get_areacalib()` targets **area** vs `pm_land_start`.)
**Verify**: `rg -n 'pm_yields_semi_calib' modules/` → 14 preloop/declarations + `17_production/flexreg_apr16/presolve.gms:10` only.
**Fix**: reverse the arrow to `pm_yields_semi_calib(j,kve,w) [14] → pm_prod_init [17]` and note it is a preloop-fixed parameter, i.e. not part of any within-run cycle.

---

### B03 — Major — `vm_prod_reg(i2,kap)` attributed to module 70
**Doc** `circular_dependency_resolution:241`
> `vm_prod_reg(i2,kap) [70] → manure availability`

**Reality**: `vm_prod_reg` is DECLARED in `17_production` and POPULATED by 17 (`q17_prod_reg`), 18, 20, 21. Module 70 only READS it — every occurrence in `modules/70_livestock/fbask_jan16/equations.gms` (lines 18, 28, 36, 60, 65, 70) is on an equation RHS. Every other entry in this doc's cycle chains tags the *populating* module, so `[70]` misdirects.
**Verify**: `rg -n 'vm_prod_reg' modules/70_livestock/fbask_jan16/*.gms` → 6 hits, all RHS. Role map: `populated_by:["17","18","20","21"]`.
**Fix**: `vm_prod_reg(i2,kap) [declared+populated 17; read by 70]`.

---

### B04 — Major — `vm_land(j,"crop")` attributed to module 30 in the C4 chain
**Doc** `circular_dependency_resolution:386`
> `vm_land(j,"crop") [30] → competes for land (crop ↓ as forest ↑)`

**Reality**: the `"crop"` slice of `vm_land` is populated by **29_cropland**, equation `q29_cropland`, in the default realization `detail_apr24` (`cfg$gms$cropland <- "detail_apr24"`, `config/default.cfg:814`): `vm_land(j2,"crop") =e= sum((kcr,w), vm_area(j2,kcr,w)) + vm_fallow(j2) + sum(ac, v29_treecover(j2,ac));` (`modules/29_cropland/detail_apr24/equations.gms:11-12`; the alternative `simple_apr24/equations.gms:12-13` drops the fallow and tree-cover terms). Module 30 (default `simple_apr24`, `config/default.cfg:915`) only *reads* `vm_land(j2,"crop")` (`modules/30_croparea/simple_apr24/equations.gms:23`, the bioenergy-tree target). Module 29 is also absent from the C4 module list at `:378` and from the C4 row in the §8.1 catalog (`:743`).
**Verify**: `rg -n 'vm_land\(j2?,"crop"\)' modules/` → LHS `=e=` only at `modules/29_cropland/detail_apr24/equations.gms:12` and `simple_apr24/equations.gms:13`; every module-30 hit is RHS. Role map: `vm_land populated_by:["10","29","31","32","34","35"]` — 30 absent.
**Fix**: `vm_land(j,"crop") [29 q29_cropland]`, and add 29_cropland to the C4 module list in §3.4 and §8.1.

---

### B05 — Major — `vm_carbon_stock(j,"forestry",…)` attributed to module 56 in the C4 chain
**Doc** `circular_dependency_resolution:390`
> `vm_carbon_stock(j,"forestry","vegc","actual") [56] → carbon sequestration`

**Reality**: 56_ghg_policy DECLARES `vm_carbon_stock` (`modules/56_ghg_policy/price_aug22/declarations.gms`) and READS it (`equations.gms:22`), but the `"forestry"` slice is POPULATED by module 32: `q32_carbon(j2,ag_pools,stockType) .. vm_carbon_stock(j2,"forestry",ag_pools,stockType) =e= …` (`modules/32_forestry/dynamic_may24/equations.gms:108`). Populators overall: 29 (crop), 31 (past), 32 (forestry), 34, 35 (primforest/secdforest/other), 59 (soilc).
**Verify**: `rg -n 'vm_carbon_stock\(j2,' modules/*/*/equations.gms` → LHS by 29/31/32/35/59; 52 and 56 appear on RHS only. Role map: `populated_by:["29","31","32","34","35","59"], read_by:["52","56","59"]`.
**Fix**: `vm_carbon_stock(j,"forestry","vegc","actual") [declared 56; populated by 32 q32_carbon; read by 52/56]`.

---

### B06 — Major — conservation bounds attributed to module 22 (they are set in 35_natveg / 31_past)
**Doc** `circular_dependency_resolution:302` (with `:288` and `:292` carrying the same error via `[10]`)
> `vm_land(j,land_natveg) ≥ pm_land_conservation(t,j,land_natveg,"protect")  [22, bounds]`

**Reality**: module 22 (`area_based_apr22`, the default) has **no** `presolve.gms` and **no** `equations.gms` — its only in-loop file is `presolve_ini.gms`, which merely *reads* `vm_land.lo(j,"crop")` (lines 86, 97, 108). The bounds are applied in module **35** and module **31**:
- `modules/35_natveg/pot_forest_may24/presolve.gms:162` — primforest floor raised to `pm_land_conservation(t,j,"primforest","protect")` when the harvest-share floor is lower;
- `:201` — `vm_land.lo(j,"secdforest") = pm_land_conservation(t,j,"secdforest","protect") + p35_land_restoration(j,"secdforest");`
- `:231` — same for `"other"`;
- `modules/31_past/endo_jun13/presolve.gms:9` — `vm_land.lo(j,"past") = sum(consv_type, pm_land_conservation(t,j,"past",consv_type));`

Two consequences: (a) `[22, bounds]` and `[10]` both point at modules that never assign the bound; (b) the rendered inequality omits the `+ p35_land_restoration` term for secdforest/other and the `max(…, (1-s35_natveg_harvest_shr)·pcm_land)` structure for primforest.
**Verify**: `rg -n 'vm_land\.(lo|up|fx)' modules/` → assignments only in 35_natveg, 34_urban, 31_past; `ls modules/22_land_conservation/area_based_apr22/` → `declarations input input.gms preloop.gms presolve_ini.gms realization.gms sets.gms`.
**Fix**: attribute the bound to `modules/35_natveg/pot_forest_may24/presolve.gms:162,201,231` (and `modules/31_past/endo_jun13/presolve.gms:9` for pasture); module 22 supplies the parameter only. Add the restoration term.

---

### B07 — Major — C3: previous-timestep AEI is a **lower** bound on `vm_AEI`, not an upper bound on irrigated area
**Doc** `circular_dependency_resolution:344-346`
> "1. **Within timestep**: AEI capacity from **previous timestep** is **upper bound**
>  3. **Next timestep**: Increased AEI allows more irrigation"

**Reality**: in the default `endo_apr13`, `vm_AEI(j)` is a **positive variable optimized in the current timestep** (`declarations.gms:19`). Presolve sets a *floor*, not a ceiling: `vm_AEI.lo(j) = pc41_AEI_start(j) / ((1 - s41_AEI_depreciation)**(m_timestep_length));` (`modules/41_area_equipped_for_irrigation/endo_apr13/presolve.gms:11`), and with the default `s41_AEI_depreciation = 0` (`input.gms:11`, `config/default.cfg:1332`) that floor equals last timestep's AEI exactly. The irrigated-area constraint `q41_area_irrig(j2) .. sum(kcr, vm_area(j2,kcr,"irrigated")) =l= vm_AEI(j2);` (`equations.gms:10-11`) therefore binds against the **current, endogenous** AEI — expansion happens *within* the same timestep, priced by `q41_cost_AEI` on `(vm_AEI - pc41_AEI_start)`. The previous timestep never caps irrigation; it only prevents disinvestment.
Related: in the **default** croparea realization `simple_apr24`, module 30 does not reference `vm_AEI` at all — it is listed in `modules/30_croparea/simple_apr24/not_used.txt:2`. `vm_AEI` enters a module-30 equation only in the non-default `detail_apr24` (`equations.gms:82`, rotation rules). So the 30↔41 coupling in a default run is entirely `q41_area_irrig` inside module 41.
**Verify**: `cat modules/41_area_equipped_for_irrigation/endo_apr13/presolve.gms` (line 11 = `.lo`); `rg -n 'vm_AEI' modules/30_croparea/` → `detail_apr24/equations.gms:82` + `simple_apr24/not_used.txt:2`.
**Fix**: rewrite as "Within timestep: previous AEI (depreciated) is a **lower** bound on the endogenous `vm_AEI`; irrigated area is capped by the *current* `vm_AEI`, which may expand in the same timestep at the cost of `q41_cost_AEI`." Reclassify C3 as **Simultaneous Equations** with a one-way ratchet, not "Simultaneous + Temporal". Note that with the default `simple_apr24`, module 30 has `vm_AEI` in `not_used.txt`.

---

### B08 — Major — "`im_*` = Input data (exogenous, never changes)" is false
**Doc** `circular_dependency_resolution:61`
> "- `im_*` = **Input data** (exogenous, never changes)"

**Reality**: `im_` denotes a module-**interface** input parameter, not immutability, and several are recomputed **inside the timestep loop**. `im_growing_stock(t,j,ac,land_timber)` is assigned in module 14's presolve every timestep from `pm_carbon_density_plantation_ac`, `pm_carbon_density_secdforest_ac`, `pm_carbon_density_other_ac`, `fm_carbon_density`, `pm_climate_class` and `fm_ipcc_bef` (`modules/14_yields/managementcalib_aug19/presolve.gms:24,33,42,51,64,76-81`), then read by 32 and 35. Role map: `im_growing_stock populated_by:["14"], read_by:["14","32","35"]`; `im_feed_baskets populated_by:["70"]`; `im_pollutant_prices populated_by:["56"]` (module 56 preloop rescales it by the devstate scaling, fader, `s56_cprice_red_factor` and the min/max caps).
This matters here specifically: §5.2's classification decision tree and §2.3's "Type 3: Sequential Execution" both lean on `im_*` being immutable preloop data, so the gloss propagates into wrong cycle classifications.
**Verify**: `rg -n '^\s*im_\w+\(' modules/*/*/presolve.gms` → `modules/14_yields/managementcalib_aug19/presolve.gms:24,33,42,51,64,76,78,80,81` (plus `dynRegPastrTau_apr26`).
**Fix**: "`im_*` = **interface input parameter** (module-external; usually loaded/derived in `preloop`, but some are recomputed each timestep in `presolve` — e.g. `im_growing_stock` in 14_yields)."

---

### B09 — Major — `pm_water_avail` does not exist
**Doc** `circular_dependency_resolution:593-594`
> `vm_area.up(j,kcr,"irrigated")$(pm_water_avail(j) < threshold) = 0;`
> `* Does NOT create new dependency (just uses existing pm_water_avail)`

**Reality**: no `pm_water_avail` anywhere in the model. The real water-availability interface is `im_wat_avail(t,wat_src,j)` (`modules/43_water_availability/total_water_aug13/declarations.gms:9`; `total_water_aug13` is the default, `config/default.cfg:1427`). The doc explicitly calls the invented name "existing".
**Verify**: `grep -rn "pm_water_avail" .` → 0 hits; `rg -n 'pm_water_avail' modules/ core/` → 0 hits; positive control `rg -ln 'pm_interest' modules/` → 3+ files. `rg -n 'water_avail' modules/43_water_availability/*/declarations.gms` → `im_wat_avail`.
**Fix**: use `im_wat_avail(t,"surface",j)` (or drop the example to a clearly-labelled `<pm_some_param>` placeholder).

---

### B10 — Major — Appendix A row for `pcm_carbon_stock`: wrong declared domain, and module 59 is missing as an updater
**Doc** `circular_dependency_resolution:976`
> `| `pcm_carbon_stock(j,land,ag_pools,stockType)` | 56_ghg_policy | Previous carbon stocks | modules/56_ghg_policy/price_aug22/postsolve.gms:8 |`

**Reality**: the declaration is `pcm_carbon_stock(j,land,c_pools,stockType)` (`modules/56_ghg_policy/price_aug22/declarations.gms:19`) — `c_pools` (`core/sets.gms:324`) is the superset that includes `soilc`; `ag_pools` is only the slice module 56's postsolve happens to write. The `soilc` slice is updated by module **59** in both its realizations — default `cellpool_jan23` (`cfg$gms$som <- "cellpool_jan23"`, `config/default.cfg:1937`) at `modules/59_som/cellpool_jan23/postsolve.gms:13`, and `static_jan19` at `postsolve.gms:9` (`pcm_carbon_stock(j,land,"soilc",stockType) = vm_carbon_stock.l(j,land,"soilc",stockType);`), with preloop initialisation at `59_som/*/preloop.gms` and `56_ghg_policy/price_aug22/preloop.gms:10`. A reader tracing lagged **soil** carbon to module 56 finds nothing there.
**Verify**: `rg -n '^\s*pcm_carbon_stock\(' modules/` → 56 (postsolve:8, preloop:10), 59 static (postsolve:9, preloop:11), 59 cellpool (postsolve:13, preloop:30,33). Role map: `pcm_carbon_stock populated_by:["56","59"]`.
**Fix**: signature → `pcm_carbon_stock(j,land,c_pools,stockType)`; "Updated in" → `56_ghg_policy/price_aug22/postsolve.gms:8` (ag_pools) **and** `59_som/<realization>/postsolve.gms:9|13` (soilc).

---

### B11 — Minor — §2.2 pseudo-equation over-broadens `q17_prod_reg` to `kall`
**Doc** `circular_dependency_resolution:143`
> `vm_prod_reg(i,kall) = sum(cell(i,j), vm_prod(j,kall))               [q17_prod_reg]`

**Reality**: `q17_prod_reg(i2,k) .. vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k));` (`modules/17_production/flexreg_apr16/equations.gms:10-11`). `k(kall)` = 28 *primary* products (`modules/14_yields/managementcalib_aug19/sets.gms:12-18`); `kall` has 41 members (`core/sets.gms:228-236`) and adds the secondary/processed goods (`oils, oilcakes, sugar, molasses, alcohol, ethanol, distillers_grain, brans, scp, fibres`, `res_*`), whose regional production is set in module 20, not by `q17_prod_reg`.
**Verify**: `cat -n modules/17_production/flexreg_apr16/equations.gms`; `sed -n '8,20p' modules/14_yields/managementcalib_aug19/sets.gms`.
**Fix**: write the domain as `k`, and add "secondary products (`kall \ k`) get `vm_prod_reg` from module 20_processing".

---

### B12 — Minor — `im_pollutant_prices` unit given as USD/tCO2
**Doc** `circular_dependency_resolution:410`
> "- `im_pollutant_prices`: Carbon price trajectory (0-1000 USD/tCO2)"

**Reality**: `im_pollutant_prices(t_all,i,pollutants,emis_source) Certificate prices for N2O-N CH4 CO2-C used in the model (**USD17MER per Mg**)` (`modules/56_ghg_policy/price_aug22/declarations.gms:9`) — for `co2_c` that is per Mg **carbon**, a factor 44/12 ≈ 3.67 from per-tCO2. Corroborated by the sibling scalars in the same realization: `s56_minimum_cprice … (USD17MER per tC) / 3.67 /` and `s56_limit_ch4_n2o_price … (USD17MER per tC) / 4920 /` (`input.gms:65,67`), and by `modules/module_56.md:152`.
**Verify**: `rg -n 'im_pollutant_prices' modules/56_ghg_policy/price_aug22/declarations.gms`.
**Fix**: "(USD17MER per Mg C for `co2_c`; ≈ ×3.67 lower in USD/tCO2 terms)". Also note the default price scenario is `c56_pollutant_prices <- "R34M410-SSP2-NPi2025"` (`config/default.cfg:1734`), not a free 0–1000 range.

---

### B13 — Minor — stale cross-doc citation: `Module_Dependencies.md (lines 149-179)`
**Doc** `circular_dependency_resolution:745`
**Reality**: `core_docs/Module_Dependencies.md:149-179` is the layered-architecture diagram plus §3.2 Hub-and-Spoke. The 4 core cycles it is cited for live at `:182-215` (`### 4. Circular Dependencies` at 182, the numbered cycle list 188-215).
**Verify**: `grep -n "" core_docs/Module_Dependencies.md | sed -n '145,190p'`.
**Fix**: cite `core_docs/Module_Dependencies.md:182-215`.

---

### B14 — Minor — stale cross-doc citation: `module_56.md (lines 60-79)`
**Doc** `circular_dependency_resolution:414`
**Reality**: `modules/module_56.md:60-79` covers `q56_emis_pricing` / `q56_emis_pricing_co2`. The parameters this line is sourcing (`s56_c_price_induced_aff`, `s56_buffer_aff`, `im_pollutant_prices`) are documented at `modules/module_56.md:40-41`, `:152`, `:257`, `:287`, `:310`.
**Verify**: `grep -n "s56_buffer_aff\|s56_c_price_induced_aff\|im_pollutant_prices" modules/module_56.md`.
**Fix**: cite `modules/module_56.md:40-41, 287, 310`.

---

### B15 — Minor — Appendix A "Pattern" sentence and the `/tmp/magpie_analysis/` pointer
**Doc** `circular_dependency_resolution:980` and `:497`
> ":980 **Pattern**: All `pcm_*` variables are updated in `postsolve.gms` from corresponding `vm_*` optimal values"
> ":497 Visualize using GraphViz (files in `/tmp/magpie_analysis/`)"

**Reality (980)**: `pcm_land` is additionally rewritten **inside the timestep, before the solve**: `modules/35_natveg/pot_forest_may24/presolve.gms:39` (`pcm_land(j,"primforest") = pcm_land(j,"primforest") - p35_disturbance_loss_primf(t,j);`), `:131`, `:137`, and `modules/32_forestry/dynamic_may24/presolve.gms:101` (from `v32_land.l`, a module-internal variable, not a `vm_`); `modules/34_urban/exo_nov21/preloop.gms:17` initialises it. So the parameter the optimiser sees is *previous state adjusted in presolve*, not a pure `vm_*.l` copy — material for a document whose thesis is that `pcm_*` provides clean temporal decoupling.
**Reality (497)**: `/tmp/magpie_analysis/` does not exist and is not in either repo; it is a machine-local scratch path in a shared public doc.
**Verify**: `rg -n '^\s*pcm_land\(' modules/`; `ls -d /tmp/magpie_analysis` → "No such file or directory".
**Fix**: qualify to "updated in `postsolve.gms` from `vm_*.l`; some (`pcm_land`) are additionally adjusted in `presolve` by 32/34/35 — see `modules/35_natveg/pot_forest_may24/presolve.gms:39,131,137`". Delete the `/tmp/...` pointer or replace it with a repo path/regeneration command.

---

## Deferred (not bugs — unverified or unverifiable here)

1. `:60` "`pcm_*` … ('p' = parameter, 'cm' = current module)" — the MAgPIE repo carries no naming-convention document (no `CONTRIBUTING.md`; `README.md` has none), so the etymology is not code-checkable. Note the internal inconsistency: `reference/GAMS_MAgPIE_Patterns.md:225,521` glosses `pcm_` as "Previous Current Module". One of the two agent docs should be corrected once a source is found.
2. `:5,11,749,1036` "26 circular dependency cycles" — traces to `core_docs/Module_Dependencies.md:6,186,424` with no re-runnable artifact behind it (the doc's own §8.2 concedes only 4 are documented and lists 6 more as "suspected"). Falls under AGENT.md rule 4 (no figure without an artifact) but I did not re-derive a cycle count, so I am not asserting 26 is wrong.
3. `:584` "Modifying Module 10 (Land): … 15 consumers" — matches `core_docs/Module_Dependencies.md:179` ("10_land: 15 out"). The role map gives 18 distinct reader modules for the non-`fm_` interfaces declared in `10_land` (`11,13,14,22,29,30,31,32,34,35,39,44,50,56,58,59,71,80`). The counting rule is undefined, so I did not flag it.
4. `:723-724` "Independent modules (37, 45, 54) can be run in parallel" / "water system: 41-42-43 … no cycles". Factually 37/45 are parameter-only modules with no equations, and 54_phosphorus has **only** the `off` realization (`ls modules/54_phosphorus/` → `off`; `cfg$gms$phosphorus <- "off"`, `config/default.cfg:1608`) yet still contributes `vm_p_fert_costs` to `q11_cost_reg`. The paragraph is speculative ("Opportunities"), so I did not score it.
5. `:135-137` the §2.2 ASCII diagram's return arrow `└── vm_supply/trade ─────┘` into Module 17. `vm_supply` is declared+populated by 16_demand and read only by 16 and 21 (`rg -n 'vm_supply' modules/17_production/` → 0 hits), so nothing flows 21→17 via `vm_supply`; but the arrow label is too vague to score, and the genuine simultaneity (21's inequalities constrain 17's `vm_prod_reg`) is real.
6. All R verification snippets (`land_conservation()`, `AEI()`, `costs(components=...)`, `yields(...)`, `gdx$status$solve_status`) — magpie4 API surface, not checkable against the GAMS worktree. Should be routed to `agent/helpers/magpie4_reference.md` in a separate pass.
