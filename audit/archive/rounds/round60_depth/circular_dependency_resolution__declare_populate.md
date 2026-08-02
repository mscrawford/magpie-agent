# R60 depth audit — `cross_module/circular_dependency_resolution.md`

**Lens**: `declare_populate` — enter from the DECLARING / POPULATING side (`declarations.gms`, equation LHS,
`.fx`/`.lo`/`.up` writes, preloop/presolve/postsolve assignments); verify which module declares vs. populates
vs. reads each interface variable, and whether the formulas the doc attributes to a module's equations match
the equation bodies.

**Ground truth**: MAgPIE `develop` read-only worktree (written below as `$DEV`; all MAgPIE paths quoted
repo-relative), `audit/integrated/depth_rolemap.json` (checked first for every role claim, then confirmed with
a both-endpoints grep), and the renv-pinned `magpie4` clone under `.cache/sources/magpie4/`.

**Claims verified**: 52 load-bearing, code-checkable claims. **Bugs**: 18 (4 Critical, 6 Major, 8 Minor).

Active realizations re-read from `config/default.cfg` before any attribution call: `land=landmatrix_dec18`,
`tc=endo_jan22`, `yields=managementcalib_aug19`, `production=flexreg_apr16`, `trade=selfsuff_reduced`,
`cropland=simple_apr24`, `croparea=simple_apr24`, `land_conservation=area_based_apr22`,
`natveg=pot_forest_may24`, `forestry=dynamic_may24`, `area_equipped_for_irrigation=endo_apr13`,
`carbon=normal_dec17`, `ghg_policy=price_aug22`, `landconversion=calib`, `livestock=fbask_jan16`.

**Method note**: every absence claim was confirmed with two methods and a **positive control** in the same
directory (a bare recursive grep has silently returned empty in this tree before). `rg -r` was never used
(`-r` = `--replace`, which silently mangles matches); each probe ran as its own standalone command so that a
no-match exit-1 could not truncate a chain.

---

## 🔴 Critical

### B01 — The Type-1 flagship diagram "Land ↔ Carbon" is wrong at both endpoints
**Doc** `circular_dependency_resolution.md:92-99` (echoed in the mechanism table at `:450`)
```
Module 10 (Land) ────────────→ Module 52 (Carbon)
       ↑                             │
       │                             ↓
  pcm_carbon_stock ←──── vm_carbon_stock
```
**Reality**: modules 10 and 52 share **no interface variable in either direction**.
- `vm_carbon_stock` is DECLARED in `modules/56_ghg_policy/price_aug22/declarations.gms:34` and POPULATED by
  29, 31, 32, 34, 35, 59 — `modules/29_cropland/simple_apr24/equations.gms:30`,
  `modules/31_past/endo_jun13/equations.gms:23`, `modules/32_forestry/dynamic_may24/equations.gms:108`,
  `modules/35_natveg/pot_forest_may24/equations.gms:43,50,54`,
  `modules/59_som/cellpool_jan23/equations.gms:62`. Module 52 only READS it, in `q52_emis_co2_actual`
  (`modules/52_carbon/normal_dec17/equations.gms:16-19`).
- `modules/10_land/` contains **zero** occurrences of `carbon_stock` (so the `pcm_carbon_stock → Module 10`
  return arrow is a phantom), and `modules/52_carbon/` contains **zero** occurrences of `vm_land`/`pcm_land`
  (so the forward arrow has no interface behind it either).

**Verify**
```
rg -n "carbon_stock" $DEV/modules/10_land/        → no match   (positive control: rg -l "vm_land" → 6 files)
rg -n "vm_land|pcm_land" $DEV/modules/52_carbon/  → no match   (positive control: pcm_carbon_stock → 1 hit)
rg -n "vm_carbon_stock\(j2" $DEV/modules/*/*/equations.gms → LHS in 29,31,32,35,59; RHS-only in 52 and 56
```
**Why Critical**: this is the G2 carbon-stock anchor case verbatim — a wrong populator attribution for
`vm_carbon_stock`, presented as the doc's flagship example of the model's core resolution mechanism. Note the
doc's own **Code Evidence** block two paragraphs later (`:110-117`) is correct and says module 52 *reads*; the
diagram contradicts it.

**Fix**: redraw as `10 declares vm_land → {29,31,32,34,35,59} populate vm_carbon_stock → 56 postsolve (ag_pools
slice) / 59 postsolve (soilc slice) lag it into pcm_carbon_stock → 52 differences the two in q52_emis_co2_actual
→ vm_emissions_reg → 56 prices → 11 → objective → next timestep's land allocation`, and say explicitly that
module 52 computes CO2 *emissions*, not carbon *stocks*.

---

### B02 — Cycle 1 asserts a manure → soil-fertility → yields feedback that does not exist in the code
**Doc** `:241`, `:253`, `:273`
> `(Manure affects soil fertility)` … `3. **Across timesteps**: Manure from livestock(t) affects yields(t+1)`
> … `- Limit manure impact on yields (Module 59, SOM)`

**Reality**: `vm_yld` is written **only** by module 14 (`q14_yield_crop`, `q14_yield_past`, plus `nl_fix.gms`);
no module outside 14 assigns `vm_yld` or any of its attributes. The complete set of foreign symbols module 14
(default `managementcalib_aug19`) touches is `fm_aboveground_fraction, fm_carbon_density, fm_croparea,
fm_ipcc_bef, fm_tau1995, im_growing_stock(_ysf), pcm_tau, pm_carbon_density_*_ac, pm_climate_class,
pm_land_start, pm_past_mngmnt_factor, vm_tau` — **nothing from 50 (N budget), 55 (awms/manure) or 59 (SOM)**.
The real livestock → yields channel is `pm_past_mngmnt_factor`, declared and computed in module 70's default
realization (`modules/70_livestock/fbask_jan16/declarations.gms:41`; `presolve.gms:64-67`, driven by
`p70_incr_cattle` and recursive on `pm_past_mngmnt_factor(t-1,i)`) and read at
`modules/14_yields/managementcalib_aug19/equations.gms:38` — a cattle-stock-driven **pasture** management
factor, not a manure/soil-fertility pathway.

**Verify**
```
rg -n "manure|soilc|nr_soil|som" $DEV/modules/14_yields/managementcalib_aug19/   → no match
rg -o "vm_[a-z_]+" $DEV/modules/14_yields/managementcalib_aug19/ | sort -u        → vm_tau, vm_yld  (control)
rg -n "vm_yld\.(fx|lo|up|l)\s*\(" $DEV/modules/ | grep -v 14_yields              → no match
```
**Why Critical**: the "Fix" bullet sends a user to edit Module 59 for a pathway that has no code hook, and the
false edge is the load-bearing content of cycle **C1** (tagged 🔴 HIGH / "Test always"). The same false edge
is inherited from `core_docs/Module_Dependencies.md:190-193` ("Livestock provides manure affecting yields") —
fix both, or the next round re-imports it.

**Fix**: replace the manure loop with the two real couplings — 70 → 14 via `pm_past_mngmnt_factor` (pasture
yields) and 13 ↔ 14 via `vm_tau` (crop yields, simultaneous) / `pcm_tau` (pasture yields, lagged) — and delete
the Module-59 fix bullet.

---

### B03 — Cycle 3 inverts the AEI bound: the previous timestep's AEI is the **lower** bound
**Doc** `:344` — "**Within timestep**: AEI capacity from **previous timestep** is **upper bound**"

**Reality**: `modules/41_area_equipped_for_irrigation/endo_apr13/presolve.gms:11`
```gams
vm_AEI.lo(j) = pc41_AEI_start(j) / ((1 - s41_AEI_depreciation)**(m_timestep_length));
```
is a **lower** bound (a ratchet floor; with the default `s41_AEI_depreciation = 0` — `endo_apr13/input.gms:11`,
`config/default.cfg:1332` — it equals last period's AEI exactly). **No `vm_AEI.up` is set anywhere.** Irrigated
area is capped by the *current, endogenous* `vm_AEI` (`q41_area_irrig`, `equations.gms:10-11`), which may
expand inside the same timestep against the investment cost in `q41_cost_AEI` (`equations.gms:19-23`, where
`pc41_AEI_start` is only the cost baseline).

**Verify**
```
rg -n "vm_AEI" $DEV/modules/ $DEV/core/   → .lo only in endo_apr13/presolve.gms:11; .fx in static/presolve.gms:9;
                                            no .up assignment anywhere
```
**Why Critical**: the mechanism is exactly reversed, so the doc's "Common Problem — rapid expansion beyond
capacity" is actually the intended design, and its fix ("Limit AEI expansion rate (Module 41 configuration)")
is unactionable: module 41 exposes only `c41_initial_irrigation_area` and `s41_AEI_depreciation`
(`endo_apr13/input.gms:8,11`) — there is no expansion-rate lever.

**Fix**: "Within timestep, irrigated area is capped by the *current-timestep* endogenous `vm_AEI`
(`q41_area_irrig`); the depreciated previous-timestep AEI enters as a **lower** bound (`presolve.gms:11`) and
as the baseline for investment cost in `q41_cost_AEI`. AEI can only ratchet up." Re-target the fix advice at
the investment cost `f41_c_irrig` / `s41_AEI_depreciation`.

---

### B04 — Natveg conservation bounds attributed to module 10; they are written by module 35 (and 31)
**Doc** `:288`, `:292`, `:302`
> `vm_land(j,land_natveg) [35] → conservation bounds set on vm_land.lo [10]` …
> `pm_land_conservation(t,j,land,consv_type) [22] → vm_land.lo(j,land_natveg) [10]` …
> `vm_land(j,land_natveg) ≥ pm_land_conservation(t,j,land_natveg,"protect")   [22, bounds]`

**Reality**: module 10 never assigns `vm_land.lo` — its presolve only fixes `vm_lu_transitions` and calls
`m_boundfix(vm_land,(j,land),up,1e-6)` (`modules/10_land/landmatrix_dec18/presolve.gms:13-25`); the only other
occurrence is the postsolve output line `:52`. The conservation bounds are set in **module 35**:
```gams
* modules/35_natveg/pot_forest_may24/presolve.gms:162
vm_land.lo(j,"primforest")$(vm_land.lo(j,"primforest") < pm_land_conservation(t,j,"primforest","protect")) = pm_land_conservation(t,j,"primforest","protect");
* :201  vm_land.lo(j,"secdforest") = pm_land_conservation(t,j,"secdforest","protect") + p35_land_restoration(j,"secdforest");
* :231  vm_land.lo(j,"other")      = pm_land_conservation(t,j,"other","protect")      + p35_land_restoration(j,"other");
```
with the pasture analogue in `modules/31_past/endo_jun13/presolve.gms:9`. The aggregate floor is module 35's
**equation** `q35_natveg_conservation` (`modules/35_natveg/pot_forest_may24/equations.gms:19-22`), a sum over
`land_natveg` — not a per-type bound and not module 22's. Module 22 only *populates* the parameter
(`modules/22_land_conservation/area_based_apr22/presolve_ini.gms:54`) and *reads* `vm_land.lo(j,"crop")`
(`:86,97,108`); it never writes `vm_land.lo`.

**Verify**
```
rg -n "vm_land\.lo|vm_land\.up|vm_land\.fx" $DEV/modules/   → 35 (157,159,162,163,201,231), 31 (9), 34; none in 10 except postsolve output
rg -n "pm_land_conservation" $DEV/modules/10_land/          → no match (control: same grep in modules/35_natveg/ → 12 hits)
```
Role map corroborates: `pm_land_conservation` → `{declared_in: 22_land_conservation, populated_by: [22,32,35],
read_by: [13,22,29,31,32,35]}` — module 10 appears in neither list.

**Fix**: retag the bound-setting as `[35]` (and `[31]` for pasture), note the `+ p35_land_restoration` term,
and reclassify this leg as bound-driven presolve (the doc's own decision tree at `:517` routes
presolve-computed dependencies to Type 3, not "Simultaneous Equations").

---

## 🟠 Major

### B05 — Cycle 4 chain mislabels the owning module for two interface slices
**Doc** `:386`, `:390` — `vm_land(j,"crop") [30]` … `vm_carbon_stock(j,"forestry","vegc","actual") [56]`

**Reality**:
- `vm_land(j2,"crop")` is populated by **module 29** (`modules/29_cropland/simple_apr24/equations.gms:13`,
  `q29_cropland`; `detail_apr24/equations.gms:12` in the non-default variant). Module 30 only *reads* it
  (`modules/30_croparea/simple_apr24/equations.gms:23`). Module 29 appears nowhere in the C4 module list
  (`:378`, `:743`).
- The forestry slice of `vm_carbon_stock` is populated by **module 32**
  (`modules/32_forestry/dynamic_may24/equations.gms:108`, `q32_carbon`); module 56 declares
  (`price_aug22/declarations.gms:34`) and reads it. Contrast the adjacent, correct tag
  `vm_land(j,"forestry") [32]` (`modules/32_forestry/dynamic_may24/equations.gms:56`).

**Verify**
```
rg -n 'vm_land\(j2,"crop"\)' $DEV/modules/*/*/equations.gms   → 29 on the =e= LHS; 30 RHS-only
rg -n "vm_carbon_stock\(j2" $DEV/modules/*/*/equations.gms    → 32:108 forestry LHS; 56:22 / 52:19 RHS-only
```
**Fix**: `vm_land(j,"crop") [29]`, `vm_carbon_stock(j,"forestry",…) [declared 56, populated 32]`, and add
29_cropland to the C4 module list at `:378`/`:743`.

### B06 — Cycle 4 chain invents a serial link `vm_emissions_reg → vm_reward_cdr_aff` (the two are parallel)
**Doc** `:392-394` — `vm_emissions_reg(i,"co2_c") [52] → … ↓ … vm_reward_cdr_aff(i) [56] → revenue from carbon removal`

**Reality**: `vm_reward_cdr_aff` is computed from **`vm_cdr_aff`** — declared and populated in module 32
(`modules/32_forestry/dynamic_may24/declarations.gms:83`, `equations.gms:37,42`) — times `p56_c_price_aff`,
discounted, in `q56_reward_cdr_aff_reg` / `q56_reward_cdr_aff`
(`modules/56_ghg_policy/price_aug22/equations.gms:67-79`). `vm_emissions_reg` does not appear in those
equations. Emission costs (`q56_emission_cost_annual/_oneoff`, `:29-58`) and the CDR reward are **two parallel
entries** into the objective, not a chain — the R51 serial-vs-parallel trap.

Same line, secondary defect: `vm_emissions_reg` is declared `(i,emis_source,pollutants)`
(`price_aug22/declarations.gms:40`) and module 52 populates only the `(i,emis_oneoff,"co2_c")` slice, so the
two-index form drops `emis_source`. The bracket convention is also self-inconsistent inside one diagram
(`[52]` = populating module, `[56]` two lines earlier = declaring module).

**Verify**
```
rg -n "vm_cdr_aff" $DEV/modules/   → declared+populated 32 (declarations.gms:83, equations.gms:37,42); read only by 56 (equations.gms:77)
```
**Fix**: split into two parallel arrows into `vm_cost_glo`: (a) `vm_carbon_stock → vm_emissions_reg (52) →
v56_emis_pricing → vm_emission_costs (56)`; (b) `vm_cdr_aff (32) → vm_reward_cdr_aff (56)`. Write
`vm_emissions_reg(i,emis_oneoff,"co2_c")` and state the bracket convention once.

### B07 — Cycle 1 chain reverses the `pm_yields_semi_calib` edge (17 → 14 does not exist)
**Doc** `:237` — `vm_prod(j,kcr) [17] → pm_yields_semi_calib(j,kve,w) [14]`

**Reality**: `pm_yields_semi_calib(j,kve,w)` is declared in
`modules/14_yields/managementcalib_aug19/declarations.gms:19` and written **once, in module 14's preloop**,
from the 1995 slice of the calibrated yields (`preloop.gms:116,149`:
`pm_yields_semi_calib(j,knbe14,w) = i14_yields_calib("y1995",j,knbe14,w);`). Its only consumer is **module 17's
presolve** (`modules/17_production/flexreg_apr16/presolve.gms:10`, building `pm_prod_init`). The flow is
14 → 17; module 17 never writes it, and module 14 reads no interface variable declared in module 17 at all.

**Verify**
```
rg -n "pm_yields_semi_calib" $DEV/modules/   → 14 (declarations:19, preloop:116,149) + 17 (presolve:10) only
```
**Fix**: delete the upward arrow; keep the correct downward arrow at `:245` and rely on the (already correct)
prose at `:251` for the real 13↔14 coupling.

### B08 — Type-4 diagram puts `vm_prod(kli)` under module 70; module 70 never references `vm_prod`
**Doc** `:206` — `Module 14 (Yields) ←→ Module 13 (TC) ←→ Module 70 (Livestock)` … `vm_prod(kli)`

**Reality**: `vm_prod(j,k)` is declared in `modules/17_production/flexreg_apr16/declarations.gms:9` and
populated by modules 30, 31, 71, 73. Module 70 (both realizations) references **`vm_prod_reg` only** —
`modules/70_livestock/fbask_jan16/equations.gms:18,28,36,60,65,70`, e.g.
`vm_dem_feed(i2,kap,kall) =g= vm_prod_reg(i2,kap) * …`. The doc's own chain at `:239` uses the correct
`vm_prod_reg(i2,kap)`.

**Verify**
```
rg -n "vm_prod\(" $DEV/modules/70_livestock/   → no match (control: vm_prod_reg → 6 hits in fbask_jan16/equations.gms)
```
(`kli(kap)` and `kap(k)` are real sets — `modules/16_demand/sector_may15/sets.gms:16,21`.)

**Fix**: `vm_prod_reg(i,kli)` under Module 70.

### B09 — Appendix A: "All `pcm_*` variables are updated in `postsolve.gms`" is false, and the rows are incomplete
**Doc** `:975-980`

**Reality**: `pcm_*` state is written in **preloop, presolve and start** as well as postsolve, and not always
from a `vm_*.l`:

| Where | Statement |
|---|---|
| `modules/10_land/landmatrix_dec18/start.gms:11` | `pcm_land(j,land) = pm_land_start(j,land);` (initialisation) |
| `modules/34_urban/exo_nov21/preloop.gms:17` | `pcm_land(j,"urban") = i34_urban_area("y1995",j);` |
| `modules/35_natveg/pot_forest_may24/presolve.gms:39` | `pcm_land(j,"primforest") = pcm_land(j,"primforest") - p35_disturbance_loss_primf(t,j);` |
| `modules/35_natveg/pot_forest_may24/presolve.gms:131,137` | `pcm_land("secdforest"/"other")` rebuilt from the `pc35_*` age-class pools |
| `modules/32_forestry/dynamic_may24/presolve.gms:101` | `pcm_land(j,"forestry") = sum((type32,ac), v32_land.l(j,type32,ac));` |
| `modules/13_tc/endo_jan22/presolve.gms:77` | `pcm_tau` reassigned in presolve |
| `modules/56_ghg_policy/price_aug22/preloop.gms:10` | `pcm_carbon_stock` initialised from `fm_carbon_density * pcm_land` |
| `modules/59_som/cellpool_jan23/postsolve.gms:13` (and `static_jan19/postsolve.gms:9`) | `pcm_carbon_stock(j,land,"soilc",stockType)` — the **soilc slice is module 59's**, not 56's |

Also: the table quotes `pcm_carbon_stock(j,land,ag_pools,stockType)`, but the **declared** domain is
`(j,land,c_pools,stockType)` (`modules/56_ghg_policy/price_aug22/declarations.gms:19`); `ag_pools(c_pools) =
{vegc,litc}` (`price_aug22/sets.gms:209-210`) is merely the slice module 56's postsolve writes. Since
`q52_emis_co2_actual` sums over `emis_land(...,c_pools)` including `soilc`, the 59-written slice is
load-bearing.

**Verify**
```
rg -n "^\s*pcm_[a-z_]+\(" $DEV/modules/*/*/postsolve.gms $DEV/modules/*/*/presolve.gms $DEV/modules/*/*/preloop.gms | grep "="
   → 18 assignment sites: postsolve 5, presolve 5, preloop 5+, plus start.gms
```
**Why Major**: §9.1's damping recipe (`pcm_variable(j) = 0.7*vm_variable.l(j) + 0.3*pcm_variable(j)`) applied
only in postsolve would be silently overwritten by the presolve reassignments in 32/35 — the doc's own remedy
fails on its own headline variable, and a developer would miss that module 35 modifies the lagged land state
*before* the solve (this is how primforest disturbance loss enters the model).

**Fix**: "Most `pcm_*` are refreshed in `postsolve.gms` from `vm_*.l`; exceptions: `pcm_land` is rewritten by
32/34/35 in presolve/preloop and initialised in `10_land/.../start.gms:11`; `pcm_tau` is reassigned in
`13_tc/endo_jan22/presolve.gms:77`; `pcm_carbon_stock` is initialised in preloop (56, 59) and its `soilc`
slice is updated by 59." Correct the declared domain to `c_pools` and add the 59 row.

### B10 — Fabricated GAMS identifiers presented as existing (`vm_yields`, `pm_water_avail`)
**Doc** `:844` and `:593-594`
> `vars <- c("vm_land", "vm_prod", "vm_carbon_stock", "vm_yields", ...)` …
> `vm_area.up(j,kcr,"irrigated")$(pm_water_avail(j) < threshold) = 0;` `* … just uses existing pm_water_avail`

**Reality**: neither identifier exists anywhere in `modules/` or `core/`. The yield variable is `vm_yld`
(`modules/14_yields/managementcalib_aug19/declarations.gms`); water availability is the variable
`v43_watavail` (`modules/43_water_availability/*/declarations.gms:13`) — no `pm_water_avail` parameter exists.

**Verify**
```
rg -n "vm_yields" $DEV/modules/ $DEV/core/   → no match   (control: "vm_yld" found in 14/declarations.gms)
rg -n "pm_water_avail" $DEV/                 → no match   (control: v43_watavail found in 43/*/declarations.gms:13)
```
**Fix**: `vm_yld` (and note that a postsolve GDX exposes it as `ov_yld`); rewrite the "SAFE" example against a
real parameter, or drop the word "existing".

---

## 🟡 Minor

### B11 — `q17_prod_reg` written over `kall`; the equation domain is `k`
**Doc** `:144` — `vm_prod_reg(i,kall) = sum(cell(i,j), vm_prod(j,kall))   [q17_prod_reg]`
**Reality**: `modules/17_production/flexreg_apr16/equations.gms:10-11` —
`q17_prod_reg(i2,k) .. vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k));`. `vm_prod` is declared `(j,k)`
(`declarations.gms:9`), so `vm_prod(j,kall)` is a domain violation; only `vm_prod_reg` is declared over `kall`
(`declarations.gms:10`), the extra slices being populated by 18/20/21/73.
**Fix**: use `k` in the equation body and note who fills the `kall\k` slices.

### B12 — magpie4 API in the verification snippets does not exist as written
**Doc** `:309-310`, `:360-361`, `:420-421`
**Reality** (pinned clone `.cache/sources/magpie4/`):

| Doc | Written | Actual |
|---|---|---|
| `:310` | `land_conservation(gdx, type="natveg")` | `landConservation(gdx, file, level, cumuRestor, baseyear, annualRestor, sum)` — `R/landConservation.R:25`; no snake_case alias, no `type` arg |
| `:361` | `AEI(gdx, level="cell")` | `water_AEI(gdx, file, level)` — `R/water_AEI.R:18`, `NAMESPACE`; no `AEI` symbol exists |
| `:309`,`:420` | `land(gdx, type="natveg"/"forestry")` | `land(gdx, file, level, types, subcategories, sum)` — `R/land.R:29`; arg is `types`, and `"natveg"` is not a land member (`land_natveg = {primforest,secdforest,other}`, `core/sets.gms:262-263`) |
| `:360` | `croparea(gdx, level="cell", irrigation="irrigated")` | `croparea(gdx, file, level, products, product_aggr, water_aggr)` — `R/croparea.R:27` |
| `:421` | `costs(gdx, components="reward_cdr_aff")` | `costs(gdx, file, level, type, sum)` — `R/costs.R:19`; use `sum = FALSE` |

**Fix**: rewrite the four snippets against the real signatures.

### B13 — Citation drift: `Module_Dependencies.md (lines 149-179)`
**Doc** `:745` (cited as the source of the C1-C4 catalog)
**Reality**: `core_docs/Module_Dependencies.md:149-179` is the Layer-4/5/6 hierarchy plus §3.2 Hub-and-Spoke
Patterns. §4.1 "Critical Feedback Cycles" begins at `:184`; the four cycles occupy roughly `:186-215`.
**Fix**: cite `core_docs/Module_Dependencies.md:184-215`.

### B14 — Citation drift: `module_56.md (lines 60-79)`
**Doc** `:414` (cited as the source of the "Critical Parameters" block)
**Reality**: `modules/module_56.md:60-79` is the `q56_emis_pricing` / `q56_emis_pricing_co2` walkthrough. The
three named parameters are documented at `modules/module_56.md:40-41` (switch table) and `:287`, `:310`.
**Fix**: cite `modules/module_56.md:40-41,287-310`.

### B15 — Type-4 "Code Evidence" misattributes the iterative calibration to module 14's preloop as *tau* calibration
**Doc** `:217-221` — `* Module 14, preloop.gms:` `* Iterative calibration of tau factors`
**Reality**: `modules/14_yields/managementcalib_aug19/preloop.gms` calibrates **yields** (`i14_yields_calib`,
`i14_managementcalib`, pasture correction at `:15-27`, irrigated/rainfed ratio at `:127-134`); `tau` appears
only as the `fm_tau1995` scaling of bioenergy yields (`:11-12`). The multi-run loop lives in
`scripts/calibration/calc_calib.R` ("calculates a regional calibration factor based on a pre run of magpie"),
and endogenous `tau` is module 13 (`endo_jan22`).
**Fix**: cite `scripts/calibration/calc_calib.R` for the iteration and `modules/13_tc/endo_jan22/` for tau;
drop "tau" from the module-14 caption.

### B16 — Speculative cycle C10 (14-13-12) is impossible: module 12 is a pure source
**Doc** `:758` — `| **C10** | 14-13-12 | Yields-TC-Interest | Temporal |`
**Reality**: module 12 declares one interface (`pm_interest`,
`modules/12_interest_rate/select_apr20/declarations.gms:9`) and reads only `im_development_state` /
`im_pop_iso` from 09_drivers. Nothing in 12 reads anything declared in 13 or 14, so no cycle can close through
it. (The table is hedged as "Suspected"/"Inferred", hence Minor.)
**Verify**: `rg -o "(vm_|pm_|im_|pcm_|fm_)[a-z_]+" $DEV/modules/12_interest_rate/select_apr20/ | sort -u`
→ `im_development_state`, `im_pop_iso`, `pm_interest`.
**Fix**: drop C10 or replace it with a verified candidate; better, mark §8.2 unverified and give the
re-derivation command.

### B17 — `im_pollutant_prices` unit given as USD/tCO2; the model uses USD per Mg **carbon**
**Doc** `:410` — "`im_pollutant_prices`: Carbon price trajectory (0-1000 USD/tCO2)"
**Reality**: declared "Certificate prices for N2O-N CH4 CO2-C used in the model (**USD17MER per Mg**)"
(`modules/56_ghg_policy/price_aug22/declarations.gms:9`), i.e. per Mg of the *carbon* in `co2_c`. Corroborated
by `s56_minimum_cprice … (USD17MER per tC) / 3.67 /` and `s56_limit_ch4_n2o_price … (USD17MER per tC) / 4920 /`
(`price_aug22/input.gms:65,67`) — 3.67 USD/tC is exactly 1 USD/tCO2 — and by the 12/44 conversions at
`preloop.gms:80-82`. Reading the figure as USD/tCO2 is off by 44/12 ≈ 3.67×.
**Fix**: "USD17MER per Mg of pollutant (for `co2_c`: per tC — multiply by 12/44 to compare with USD/tCO2)".
The `0-1000` range itself is scenario-input dependent and could not be verified offline — label it
illustrative or drop it.

### B18 — "15 consumers" for module 10
**Doc** `:584` — "Modifying Module 10 (Land): 🔴 **EXTREME RISK** (4+ cycles, 15 consumers)"
**Reality**: 18 distinct modules consume at least one module-10-declared interface (`pm_land_start`,
`pm_land_hist`, `pcm_land`, `vm_land`, `vm_landdiff`, `vm_landexpansion`, `vm_landreduction`,
`vm_cost_land_transition`, `vm_lu_transitions`): 11, 13, 14, 22, 29, 30, 31, 32, 34, 35, 39, 44, 50, 56, 58,
59, 71, 80. `core_docs/Module_Dependencies.md:363` also says 18; the "15" traces to the looser "10_land: 15
out, 2 in" line at `:179`.
**Caveat, stated honestly**: "consumer" is definitionally fuzzy — several of those 18 both read and write
module-10 interfaces (29/31/32/34/35 populate `vm_land`; 32/34/35 rewrite `pcm_land`), so a narrower
definition yields a different count. Severity kept Minor for that reason; the point is that the number should
carry its derivation.
**Fix**: replace with the derived count plus its basis, or drop the number.

---

## Verified correct (recorded so the next auditor does not re-litigate)

- Realization names and defaults, all confirmed in `config/default.cfg`: `landmatrix_dec18` (:232),
  `endo_jan22` (:293), `managementcalib_aug19` (:357), `selfsuff_reduced` (:653), `normal_dec17` (:1577),
  `price_aug22` (:1634), `endo_apr13` (:1322), `calib` (:1288).
- `q10_land_area` quoted at doc `:66-69` and `:301` matches `modules/10_land/landmatrix_dec18/equations.gms:13-15`
  exactly, **set-sum preserved** (the R16 anchor's failure mode — the doc passes it).
- Appendix A `pcm_land → modules/10_land/landmatrix_dec18/postsolve.gms:9` ✓; `pcm_tau →
  modules/13_tc/endo_jan22/postsolve.gms:16` ✓; doc `:110-111` `pcm_carbon_stock →
  modules/56_ghg_policy/price_aug22/postsolve.gms:8` ✓ (all three exact, but see B09 for completeness).
- Doc `:251` (the rewritten Cycle-1 item 1) is correct end to end: `q14_yield_crop`
  (`modules/14_yields/managementcalib_aug19/equations.gms:14-16`) scales `i14_yields_calib` by the
  current-timestep `vm_tau`; `q14_yield_past` (`:35-39`) uses the lagged `pcm_tau(j,"crop")`. Line ranges
  verified in current develop.
- Doc `:113-117` — `q52_emis_co2_actual` reads both `pcm_carbon_stock` and `vm_carbon_stock`
  (`modules/52_carbon/normal_dec17/equations.gms:16-19`) ✓, and the parenthetical is right:
  `q39_cost_landcon` (`modules/39_landconversion/calib/equations.gms:12-15`) is area-based
  (`vm_landexpansion`/`vm_landreduction` × unit cost) and uses no carbon density.
- Doc `:145` — `q21_trade_glo` matches `modules/21_trade/selfsuff_reduced/equations.gms:12-14` including the
  `f21_trade_balanceflow` term; `q21_trade_reg` / `q21_trade_reg_up` exist at `:31,39`.
- Doc `:151-153` — `vm_import`/`vm_export` genuinely do not exist anywhere in `modules/` or `core/` (confirmed
  with a positive control); `v21_trade` exists **only** under
  `modules/21_trade/selfsuff_reduced_bilateral22/` (declarations, equations, postsolve).
- Doc `:180`, `:382` — `im_pollutant_prices(t_all,i,pollutants,emis_source)`
  (`price_aug22/declarations.gms:9`), populated in preloop (`preloop.gms:37-107`) ✓.
- Doc `:411-412` — `s56_buffer_aff = 0.5`, `s56_c_price_induced_aff = 1` (`price_aug22/input.gms:69,71`;
  `config/default.cfg:1762,1788`); the `(1-s56_buffer_aff)` crediting reading matches `equations.gms:77`.
- Doc `:284`, `:292`, `:302` — `land_natveg = {primforest, secdforest, other}` (`core/sets.gms:262-263`),
  `consv_type = {protect, restore}` (`modules/22_land_conservation/area_based_apr22/sets.gms:28-29`),
  `pm_land_conservation(t,j,land,consv_type)` (`.../declarations.gms:15`) — all correct (the *attribution* is
  the bug, see B04).
- Doc `:390` — `ag_pools = {vegc, litc}`, `stockType = {actual, actualNoAcEst}`
  (`price_aug22/sets.gms:209-213`), so `"vegc"`/`"actual"` are valid members.
- Doc `:150`, `:831`, `:1012` — CONOPT / IPOPT / CPLEX are all real solver paths
  (`modules/80_optimization/{nlp_apr17,nlp_ipopt,lp_nlp_apr17}`; default `c80_nlp_solver = conopt4`,
  `config/default.cfg:2312`). Not a bug, though the default is never stated.
- Doc `:586` — module 54 declares exactly one interface, `vm_p_fert_costs`, consumed by module 11:
  "0 cycles, 1 connection" holds. Doc `:723` — 37/45/54 are pure sources (37→38, 45→14/52/58/59, 54→11), so
  "no cycles" holds.
- Doc `:600` — the hypothetical `vm_cost_landcon(j,land)` uses a real, correctly-scoped variable
  (declared in `modules/39_landconversion/calib/declarations.gms`).

---

## Deferred (unverified or deliberately not filed)

1. `:60` — the gloss "`pcm_*` … (\"p\" = parameter, \"cm\" = current module)". MAgPIE's coding-etiquette
   document is not in the repo, so the letter-by-letter convention cannot be settled from source. In-repo
   circumstantial evidence points the other way (module-local carry parameters use `pcNN_`: `pc13_tau`,
   `pc35_secdforest`, `pc41_AEI_start`; `pcm_land` is read by 13 modules, i.e. global interface scope, not
   "current module"). The agent's own `reference/GAMS_MAgPIE_Patterns.md` carries the same gloss, so this is a
   repo-wide convention question rather than a defect of this doc. Not filed.
2. `:61` — "`im_*` = Input data (exogenous, **never changes**)". `im_pollutant_prices` is rescaled, faded,
   floored and capped throughout `modules/56_ghg_policy/price_aug22/preloop.gms:37-108`, so "never changes" is
   loose, but the intended sense ("not optimized") is defensible. Not filed.
3. `:11`, `:749` — the "26 circular dependencies" total and the C5-C9 inferred table. No enumeration artifact
   exists in the repo; the count traces to `core_docs/Module_Dependencies.md:186` with no derivation behind it
   either. Needs a NO-FIGURE-WITHOUT-AN-ARTIFACT pass, not a line edit here. (Only C10 was re-derived, because
   module 12's interface surface is trivially small — see B16.)
4. The doc's edge semantics are undefined: C1/C2/C4 are optimisation-level couplings, not bidirectional
   *interface* edges (module 14 reads nothing declared in 17; module 13 reads nothing declared in 14). Worth a
   definitional sentence; not scored.
5. `:41-49` — `pcm_land("1995") ← vm_land("1995")` in the execution-flow diagram implies a time index that
   `pcm_land(j,land)` does not have, and the 1995 state actually comes from
   `modules/10_land/landmatrix_dec18/start.gms:11`. Clearly illustrative pseudocode.
6. `:351` — `q41_area_irrig` is rendered flipped (`vm_AEI(j2) =g= sum(kcr, …)` vs. the code's
   `sum(kcr, …) =l= vm_AEI(j2)`) and the equation name is omitted. Mathematically identical; style.
7. `:1004` — "t = 1995, 2000, …, 2100": under the default `c_timesteps = coup2100` the steps are 5-yearly only
   to 2060, then decadal. Reads as illustrative.
8. `:410` — the numeric range "0-1000". Depends on run-time-generated `.cs*` inputs (gitignored, regenerated
   by `scripts/`), unverifiable offline. Only the unit was filed (B17).
9. `:497` — "files in `/tmp/magpie_analysis/`" points at a scratch directory that does not exist; hygiene, not
   a code claim.
10. `:136` — the return-arrow label "vm_supply/trade" from 21 to 17. `vm_supply` is declared and populated by
    module 16 (`modules/16_demand/sector_may15/declarations.gms:11`), read by 16 and 21 — but the label is too
    loose to falsify as a specific claim.
11. `:723-724` — "water system (41-42-43) can be isolated": module 42 reads `vm_area` from 30 and 41 reads it
    too, so the subsystem is not closed; "independent" is too vague to falsify cleanly.
