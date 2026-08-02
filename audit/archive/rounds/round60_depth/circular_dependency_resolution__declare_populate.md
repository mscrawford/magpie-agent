# R60 depth audit — `cross_module/circular_dependency_resolution.md`

**Lens**: `declare_populate` (enter from the DECLARING / POPULATING side; verify which module declares
vs. populates vs. reads each interface variable, and whether the formulas the doc attributes to a
module's equations match the equation bodies).

**Ground truth**: MAgPIE `develop` worktree (read-only checkout), `audit/integrated/depth_rolemap.json`,
and the renv-pinned `magpie4` clone under `.cache/sources/magpie4`.

**Claims verified**: ~55. **Bugs found**: 18 (1 Critical, 12 Major, 5 Minor).

---

## Method note

Every absence claim below was confirmed with **two independent methods** (`rg` and `grep -rl`) plus a
**positive control** in the same directory, because a bare recursive grep in this tree has previously
returned empty on live matches. `rg -r` was deliberately avoided (`-r` = `--replace`, which silently
mangles matches — it bit me once mid-audit on `CHANGELOG.md` and the result was discarded).

---

## Critical

### B01 — Type-1 flagship cycle "Land ↔ Carbon" is wrong at both endpoints

**Doc** `circular_dependency_resolution.md:92-99` (and repeated as the Temporal-Feedback example at `:450`)

```
**Example**: Land Allocation ↔ Carbon Stocks

Module 10 (Land) ────────────→ Module 52 (Carbon)
       ↑                             │
       │                             ↓
  pcm_carbon_stock ←──── vm_carbon_stock
  (previous timestep)    (current timestep)
```

**Reality in code** — neither arrow exists:

1. **Module 52 does not produce `vm_carbon_stock`.** It is DECLARED in
   `modules/56_ghg_policy/price_aug22/declarations.gms:34` and POPULATED by modules 29, 31, 32, 34, 35, 59:
   - `modules/29_cropland/detail_apr24/equations.gms:39`
   - `modules/31_past/endo_jun13/equations.gms:23`
   - `modules/32_forestry/dynamic_may24/equations.gms:108`
   - `modules/34_urban/exo_nov21/presolve.gms:8` (`.fx` = 0)
   - `modules/35_natveg/pot_forest_may24/equations.gms:43,50,54`
   - `modules/59_som/cellpool_jan23/equations.gms:62`

   Module 52 only READS it, in `q52_emis_co2_actual`
   (`modules/52_carbon/normal_dec17/equations.gms:16-19`). This is exactly the G2 carbon-stock
   DECLARED/POPULATED/READ distinction the MANDATEs call out.

2. **Module 10 never touches carbon stock.** `modules/10_land/` contains zero occurrences of
   `carbon_stock` (either `vm_` or `pcm_`), so the return arrow `pcm_carbon_stock → Module 10`
   is a phantom consumer.

3. Symmetrically, `modules/52_carbon/` contains zero occurrences of `vm_land`/`pcm_land`, so the
   forward arrow `Module 10 → Module 52` has no interface behind it either.

The genuine mechanism the section is reaching for is: 10 declares `vm_land` → 29/31/32/34/35/59
convert land to `vm_carbon_stock` → 56 lags it to `pcm_carbon_stock`
(`modules/56_ghg_policy/price_aug22/postsolve.gms:8`) and 59 lags the `soilc` slice
(`modules/59_som/cellpool_jan23/postsolve.gms:13`) → 52 differences the two into
`vm_emissions_reg` → 56 prices it → 11 → objective → land allocation.

**Verify**
```
rg -n "carbon_stock" modules/10_land/            # -> no match
grep -rl "carbon_stock" modules/10_land/          # -> exit 1 (2nd method)
grep -rl "vm_land" modules/10_land/               # -> 5 files (positive control)
grep -rl "vm_land\|pcm_land" modules/52_carbon/   # -> exit 1
grep -rl "pcm_carbon_stock" modules/52_carbon/    # -> normal_dec17/equations.gms (positive control)
rg -n "^\s*vm_carbon_stock\s*\(" modules/         # -> 29,31,32,34,35,59 (never 52)
```

**Fix**: redraw the Type-1 example as `10 → {29,31,32,34,35,59} → vm_carbon_stock → 56/59 postsolve →
pcm_carbon_stock → 52 (q52_emis_co2_actual) → vm_emissions_reg → 56 → 11 → objective`, and state that
module 52 *reads* carbon stocks and *writes* CO2 emissions; it does not compute stocks.

---

## Major

### B02 — AEI bound direction inverted (upper vs. lower), and the constraint is on the current-timestep variable

**Doc** `:344` — "**Within timestep**: AEI capacity from **previous timestep** is **upper bound**"

**Reality**: `pc41_AEI_start` (the previous timestep's AEI) sets the **LOWER** bound on the *current*
`vm_AEI`:

```gams
* modules/41_area_equipped_for_irrigation/endo_apr13/presolve.gms:11
vm_AEI.lo(j) = pc41_AEI_start(j) / ((1 - s41_AEI_depreciation)**(m_timestep_length));
```
with `s41_AEI_depreciation = 0` by default (`endo_apr13/input.gms:11`, `config/default.cfg:1332`), i.e.
AEI cannot shrink below last period's level. The cap on irrigated area is the **current, endogenous**
`vm_AEI`, which can expand within the same timestep at investment cost:

```gams
* modules/41_area_equipped_for_irrigation/endo_apr13/equations.gms:10-11
q41_area_irrig(j2) .. sum(kcr, vm_area(j2,kcr,"irrigated")) =l= vm_AEI(j2);
```
`pc41_AEI_start` enters only the *cost* equation `q41_cost_AEI` (`equations.gms:19-23`).

The doc's own `Code` block at `:351` (a current-timestep constraint) already contradicts its `:344`
prose. Consequence: the doc's "Common Problem — Rapid expansion: Irrigation area jumps beyond
capacity" is not a symptom, it is the intended design.

**Fix**: "Within timestep: irrigated area is capped by the *current-timestep* endogenous `vm_AEI`
(`q41_area_irrig`); the previous timestep's AEI enters as a **lower** bound on `vm_AEI`
(`presolve.gms:11`) and as the baseline for investment cost in `q41_cost_AEI`."

### B03 — "Manure affects soil fertility → yields" feedback does not exist in MAgPIE

**Doc** `:239-245` (dependency chain), `:253` ("Across timesteps: Manure from livestock(t) affects
yields(t+1)"), `:273` ("Limit manure impact on yields (Module 59, SOM)")

**Reality**: the complete set of external symbols referenced anywhere in the default yields
realization is: `fm_aboveground_fraction, fm_carbon_density, fm_croparea, fm_ipcc_bef, fm_tau1995,
im_growing_stock, im_growing_stock_ysf, pcm_tau, pm_carbon_density_{other,plantation,secdforest}_ac,
pm_carbon_density_secdforest_ac_uncalib, pm_climate_class, pm_land_start, pm_past_mngmnt_factor,
pm_yields_semi_calib, vm_tau, vm_yld`. **Nothing from modules 50, 55 or 59.** `vm_yld` is populated
only by module 14 (`q14_yield_crop`, `q14_yield_past`), whose right-hand sides contain only
`i14_yields_calib`, `vm_tau`/`pcm_tau`, `fm_tau1995`, `pm_past_mngmnt_factor` and
`s14_yld_past_switch`. There is no nitrogen/SOM/manure term.

The real 70 → 14 link is `pm_past_mngmnt_factor`, declared and computed in module 70's **default**
realization (`modules/70_livestock/fbask_jan16/declarations.gms:41`; computed in `presolve.gms:64-67`
from `p70_incr_cattle`, recursively on `pm_past_mngmnt_factor(t-1,i)`) and read at
`modules/14_yields/managementcalib_aug19/equations.gms:38`. It is a *cattle-stock-driven pasture
management factor* — a genuine cross-timestep feedback, but not a manure/soil-fertility channel.

Also in the same chain: `vm_prod(j,kcr) [17] → pm_yields_semi_calib(j,kve,w) [14]`.
`pm_yields_semi_calib` is set in preloop from the 1995 slice of `i14_yields_calib`
(`modules/14_yields/managementcalib_aug19/preloop.gms:116,149`) and never depends on `vm_prod`; the
flow is 14 → 17 (`modules/17_production/flexreg_apr16/presolve.gms:10`), not 17 → 14.

**Verify**
```
rg -oN "\b(vm_|pm_|im_|fm_|pcm_)[a-zA-Z0-9_]*" modules/14_yields/managementcalib_aug19/ | sed 's/.*://' | sort -u
rg -n "pm_yields_semi_calib" modules/     # 14 preloop+declarations, 17 presolve only
```

**Fix**: replace the manure loop with the two real couplings — 70 → 14 via `pm_past_mngmnt_factor`
(pasture yields) and 13 ↔ 14 via `vm_tau` (crop yields, simultaneous) / `pcm_tau` (pasture yields,
lagged) — and delete the "Limit manure impact on yields (Module 59, SOM)" fix, which has no code
hook.

### B04 — "All `pcm_*` variables are updated in `postsolve.gms` from corresponding `vm_*` optimal values" is false

**Doc** `:980`

**Reality**: `pcm_land` is rewritten *outside* postsolve and *not* from `vm_*.l` in four places:

| Where | Statement |
|---|---|
| `modules/35_natveg/pot_forest_may24/presolve.gms:39` | `pcm_land(j,"primforest") = pcm_land(j,"primforest") - p35_disturbance_loss_primf(t,j);` |
| `modules/35_natveg/pot_forest_may24/presolve.gms:131` | `pcm_land(j,"secdforest") = sum(ac, pc35_secdforest(j,ac));` |
| `modules/35_natveg/pot_forest_may24/presolve.gms:137` | `pcm_land(j,"other") = sum((othertype35,ac), pc35_land_other(j,othertype35,ac));` |
| `modules/34_urban/exo_nov21/preloop.gms:17` | `pcm_land(j,"urban") = i34_urban_area("y1995",j);` |
| `modules/32_forestry/dynamic_may24/presolve.gms:101` | `pcm_land(j,"forestry") = sum((type32,ac), v32_land.l(j,type32,ac));` (presolve, module-local variable) |
| `modules/10_land/landmatrix_dec18/start.gms:11` | `pcm_land(j,land) = pm_land_start(j,land);` (initialisation) |

`pcm_carbon_stock` is likewise initialised in preloop from input data
(`modules/56_ghg_policy/price_aug22/preloop.gms:10`).

This matters: a developer who believes `pcm_land` is written only by module 10's postsolve will miss
that natural vegetation *modifies the lagged land state in presolve*, before the solve, which is the
mechanism by which primforest disturbance loss enters the model.

**Fix**: "Most `pcm_*` variables are updated in `postsolve.gms` from the corresponding `vm_*` levels;
notable exceptions are `pcm_land`, which module 35 rewrites in presolve for the natveg pools
(disturbance loss, age-class re-aggregation) and modules 32/34 rewrite for their own pools, and the
preloop initialisations of `pcm_land` / `pcm_carbon_stock`."

### B05 — Appendix A `pcm_carbon_stock` row: wrong declared domain and omits module 59 as populator

**Doc** `:976` — `` `pcm_carbon_stock(j,land,ag_pools,stockType)` | 56_ghg_policy | Previous carbon stocks | modules/56_ghg_policy/price_aug22/postsolve.gms:8 ``

**Reality**:
- DECLARED as `pcm_carbon_stock(j,land,c_pools,stockType)` over **`c_pools`** (`vegc, litc, soilc`) —
  `modules/56_ghg_policy/price_aug22/declarations.gms:19`. `ag_pools` is the *assignment* domain of
  the module-56 postsolve line (`ag_pools(c_pools) / vegc, litc /`,
  `modules/56_ghg_policy/price_aug22/sets.gms:209-210`), not the declaration.
- The `soilc` slice is populated by **module 59**, not 56:
  `modules/59_som/cellpool_jan23/postsolve.gms:13` and `modules/59_som/static_jan19/postsolve.gms:9`
  (`pcm_carbon_stock(j,land,"soilc",stockType) = vm_carbon_stock.l(j,land,"soilc",stockType);`),
  plus preloop initialisation at `cellpool_jan23/preloop.gms:30,33`. `CHANGELOG.md:36` documents this
  as a deliberate change. `q52_emis_co2_actual` sums over `emis_land(...,c_pools)` including `soilc`,
  so the 59-written slice is load-bearing.

**Fix**: `pcm_carbon_stock(j,land,c_pools,stockType)` | declared 56_ghg_policy | updated in
`modules/56_ghg_policy/price_aug22/postsolve.gms:8` (`ag_pools` slice) **and**
`modules/59_som/cellpool_jan23/postsolve.gms:13` (`soilc` slice).

### B06 — Natveg conservation bound attributed to module 10; it is set in module 35

**Doc** `:288` — "`vm_land(j,land_natveg) [35]` → conservation bounds set on `vm_land.lo` **[10]**"
**Doc** `:292` — "`pm_land_conservation(t,j,land,consv_type) [22]` → `vm_land.lo(j,land_natveg)` **[10]**"
**Doc** `:302` — "`vm_land(j,land_natveg) ≥ pm_land_conservation(t,j,land_natveg,"protect")`  **[22, bounds]**"

**Reality**: module 10 never assigns `vm_land.lo` (its only reference is the postsolve output line
`modules/10_land/landmatrix_dec18/postsolve.gms:52`). The natveg conservation bounds are set in
**module 35**:

```gams
* modules/35_natveg/pot_forest_may24/presolve.gms:162
vm_land.lo(j,"primforest")$(vm_land.lo(j,"primforest") < pm_land_conservation(t,j,"primforest","protect")) = pm_land_conservation(t,j,"primforest","protect");
* :201
vm_land.lo(j,"secdforest") = pm_land_conservation(t,j,"secdforest","protect") + p35_land_restoration(j,"secdforest");
* :231
vm_land.lo(j,"other")      = pm_land_conservation(t,j,"other","protect")      + p35_land_restoration(j,"other");
```
(module 31 sets the pasture analogue at `modules/31_past/endo_jun13/presolve.gms:9`). So the flow is
22 → 35, not 22 → 10, and the secdforest/other lower bound is `protect + restoration`, not `protect`
alone. `core_docs/Module_Dependencies.md:199-200` has already been corrected to
"22_land_conservation → 35_natveg (unidirectional: pm_land_conservation)"; this doc is stale relative
to its own cited source.

**Fix**: retag the bound-setting as `[35]`, note the `+ p35_land_restoration` term, and re-classify
the cycle as bound-driven (presolve) rather than "Simultaneous Equations" — the doc's own decision
tree at `:517` routes presolve-computed dependencies to Type 3.

### B07 — `vm_land(j,"crop")` attributed to module 30; it is module 29's equation

**Doc** `:386` — "`vm_land(j,"crop") [30]` → competes for land"

**Reality**: `vm_land` is DECLARED in `modules/10_land/landmatrix_dec18/declarations.gms:19`; the
crop slice is POPULATED by **module 29 (cropland)**:
`modules/29_cropland/detail_apr24/equations.gms:12`
(`vm_land(j2,"crop") =e= sum((kcr,w), vm_area(j2,kcr,w)) + vm_fallow(j2) + sum(ac, v29_treecover(j2,ac));`,
default realization per `config/default.cfg:814`). Module 30 (croparea) only *reads* it
(`modules/30_croparea/simple_apr24/equations.gms:23`). Module 29 does not appear anywhere in the C4
cycle definition (`:378`, `:743`), so a reader tracing the forest-carbon feedback would edit the
wrong module. Contrast the adjacent, correct tag `vm_land(j,"forestry") [32]` —
`modules/32_forestry/dynamic_may24/equations.gms:56`.

**Fix**: `vm_land(j,"crop") [29]` and add 29_cropland to the C4 module list at `:378` / `:743`.

### B08 — `vm_prod(kli)` attributed to module 70; module 70 never references `vm_prod`

**Doc** `:206` (Type-4 diagram) — `Module 70 (Livestock)` … `vm_prod(kli)`

**Reality**: `vm_prod(j,k)` is DECLARED in `modules/17_production/flexreg_apr16/declarations.gms:9`
and populated by modules 30, 31, 71, 73. The default livestock realization references
**`vm_prod_reg` only** — `modules/70_livestock/fbask_jan16/equations.gms:18,28,36,60,65,70` — never
`vm_prod`. The doc's own `:239` uses the correct `vm_prod_reg(i2,kap)`.

**Verify**
```
rg -n "vm_prod" modules/70_livestock/fbask_jan16/     # only vm_prod_reg
rg -c "vm_dem_feed" modules/70_livestock/fbask_jan16/equations.gms   # 2 (positive control)
```

**Fix**: `vm_prod_reg(i,kli)` under Module 70.

### B09 — Citation drift: `module_56.md (lines 60-79)`

**Doc** `:414` — "**Source**: module_56.md (lines 60-79), cross_module/carbon_balance_conservation.md"
attached to the "Critical Parameters" block listing `im_pollutant_prices`, `s56_buffer_aff`,
`s56_c_price_induced_aff`.

**Reality**: `modules/module_56.md:60-79` is the `q56_emis_pricing` / `q56_emis_pricing_co2`
walkthrough (annual vs. one-off emission pricing) — materially different content. The three named
parameters are documented at `modules/module_56.md:40-41` (switch table) and `:287`, `:310`
(`s56_buffer_aff` detail).

**Fix**: cite `modules/module_56.md:40-41` (switch table) and `:287,310`.

### B10 — Citation drift: `Module_Dependencies.md (lines 149-179)`

**Doc** `:745` — "**Source**: Module_Dependencies.md (lines 149-179)" attached to the C1-C4 cycle table.

**Reality**: `core_docs/Module_Dependencies.md:149-179` is the Layer-4/5/6 hierarchy plus §3.2
Hub-and-Spoke Patterns. §4 "Circular Dependencies (Feedback Loops)" begins at `:182`, §4.1 at `:184`,
and the four cycles occupy roughly `:186-215`.

**Fix**: cite `core_docs/Module_Dependencies.md:184-215`.

### B11 — `im_pollutant_prices` units given as USD/tCO2; the model uses USD per Mg **carbon**

**Doc** `:410` — "`im_pollutant_prices`: Carbon price trajectory (0-1000 USD/tCO2)"

**Reality**: `modules/56_ghg_policy/price_aug22/declarations.gms:9` —
"Certificate prices for N2O-N CH4 CO2-C used in the model (**USD17MER per Mg**)", i.e. per Mg of the
*carbon* in `co2_c`. Corroborated by the scalars: `s56_minimum_cprice ... (USD17MER per tC) / 3.67 /`
and `s56_limit_ch4_n2o_price ... (USD17MER per tC) / 4920 /`
(`modules/56_ghg_policy/price_aug22/input.gms:65,67`) — 3.67 USD/tC is exactly 1 USD/tCO2 — and by
the 12/44 conversions at `preloop.gms:80-82`. `modules/module_56.md:152` already says "USD17MER/Mg".
The stated range is therefore off by 44/12 ≈ 3.67x in interpretation.

**Fix**: "`im_pollutant_prices`: GHG certificate prices, USD17MER per Mg of pollutant (for `co2_c`:
per tC — divide by 3.67 to read as USD/tCO2)". The numeric range `0-1000` is scenario-file dependent
and could not be verified offline (input `.cs*` files are run-time products) — drop it or label it
illustrative.

### B12 — magpie4 function `AEI()` does not exist

**Doc** `:361` — `aei_capacity <- AEI(gdx, level="cell")`

**Reality**: the exported magpie4 function is `water_AEI(gdx, file = NULL, level = "reg")`
(`.cache/sources/magpie4/R/water_AEI.R:18`, `NAMESPACE:305`). No `AEI` symbol is defined or exported
anywhere in the package.

**Fix**: `aei_capacity <- water_AEI(gdx, level = "cell")`.

### B13 — magpie4 function `land_conservation()` does not exist (and has no `type` argument)

**Doc** `:310` — `land_protection <- land_conservation(gdx, type="natveg")`

**Reality**: the exported function is `landConservation(gdx, file = NULL, level = "cell",
cumuRestor = FALSE, baseyear = 1995, annualRestor = FALSE, sum = FALSE)`
(`.cache/sources/magpie4/R/landConservation.R:25`, `NAMESPACE:128`). There is no `type` argument and
no snake_case alias.

**Fix**: `land_protection <- landConservation(gdx, level = "cell")` and subset the natveg pools from
the result.

### B14 — `vm_yields` is not a MAgPIE variable

**Doc** `:844` — `vars <- c("vm_land", "vm_prod", "vm_carbon_stock", "vm_yields", ...)`

**Reality**: no `vm_yields` exists anywhere in `modules/` or `core/`. The yield variable is
`vm_yld(j,kve,w)` (`modules/14_yields/managementcalib_aug19/declarations.gms`). `readGDX(gdx,
"vm_yields")` returns NULL.

**Verify**
```
rg -n "vm_yields" modules/ core/                                        # -> no match
rg -c "vm_yld" modules/14_yields/managementcalib_aug19/declarations.gms  # -> 1 (positive control)
```

**Fix**: `"vm_yld"`. (Note the GDX names are `ov_*`/`ov14_*` in a postsolve GDX, so the snippet also
needs `ov_yld`; flagged as advisory, not counted as a separate bug.)

---

## Minor

### B15 — magpie4 argument names invalid in three verification snippets

| Doc line | Written | Actual signature |
|---|---|---|
| `:309`, `:420` | `land(gdx, type="natveg", ...)` / `land(gdx, type="forestry", ...)` | `land(gdx, file, level, types, subcategories, sum)` — argument is **`types`**; and `"natveg"` is not a member of the `land` set (`crop, past, forestry, primforest, secdforest, urban, other`) — `land_natveg` is the *set alias* for `{primforest, secdforest, other}` (`core/sets.gms:262-263`) |
| `:360` | `croparea(gdx, level="cell", irrigation="irrigated")` | `croparea(gdx, file, level, products, product_aggr, water_aggr)` — no `irrigation` argument |
| `:421` | `costs(gdx, components="reward_cdr_aff")` | `costs(gdx, file, level, type, sum)` — no `components` argument (use `sum = FALSE`) |

Source: `.cache/sources/magpie4/R/{land,croparea,costs}.R:29,27,19`.

### B16 — `q17_prod_reg` written over `kall`; the equation domain is `k`

**Doc** `:143` — `vm_prod_reg(i,kall) = sum(cell(i,j), vm_prod(j,kall))  [q17_prod_reg]`

**Reality**: `modules/17_production/flexreg_apr16/equations.gms:10-11` —
`q17_prod_reg(i2,k) .. vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k));`. `vm_prod` is declared
over `(j,k)` (`declarations.gms:9`), so `vm_prod(j,kall)` is a domain violation; only `vm_prod_reg`
is declared over `kall` (`declarations.gms:10`).

**Fix**: use `k` in the equation body.

### B17 — `vm_emissions_reg(i,"co2_c")` drops the `emis_source` index

**Doc** `:392` — `vm_emissions_reg(i,"co2_c") [52] → reduced (or negative) CO2 emissions`

**Reality**: declared `vm_emissions_reg(i,emis_source,pollutants)`
(`modules/56_ghg_policy/price_aug22/declarations.gms:40`); module 52 populates the
`(i,emis_oneoff,"co2_c")` slice only (`modules/52_carbon/normal_dec17/equations.gms:16-17`). Note the
declaring module is 56, not 52 — the `[52]` tag is the *populating* module here, whereas two lines
earlier `vm_carbon_stock ... [56]` is the *declaring* module, so the bracket convention is
self-inconsistent inside one diagram.

**Fix**: `vm_emissions_reg(i,emis_oneoff,"co2_c")` and state the convention once ("[NN] = module whose
equation populates this slice").

### B18 — "15 consumers" for module 10

**Doc** `:584` — "Modifying Module 10 (Land): 🔴 **EXTREME RISK** (4+ cycles, 15 consumers)"

**Reality**: 18 distinct modules reference at least one module-10-declared interface
(`pm_land_start, pm_land_hist, pcm_land, vm_landdiff, vm_land, vm_landexpansion, vm_landreduction,
vm_cost_land_transition, vm_lu_transitions`): 11, 13, 14, 22, 29, 30, 31, 32, 34, 35, 39, 44, 50, 56,
58, 59, 71, 80. The figure traces to `core_docs/Module_Dependencies.md:179` ("10_land: 15 out, 2 in").

**Caveat, stated honestly**: "consumer" is definitionally fuzzy here — several of those 18 both read
and write module-10 interfaces (29/31/32/34/35 populate `vm_land`; 32/34/35 rewrite `pcm_land`), so a
narrower definition could yield a different count. Severity kept Minor for that reason; the point is
that the number should carry its derivation.

**Verify**
```
for v in pm_land_start pm_land_hist pcm_land vm_landdiff vm_land vm_landexpansion \
         vm_landreduction vm_cost_land_transition vm_lu_transitions; do
  rg -l "\b$v\b" modules/ | grep -v "^modules/10_land/" | grep -v not_used.txt \
    | sed -E 's|modules/([0-9]+)_.*|\1|' | sort -u
done | sort -u | wc -l    # -> 18
```

**Fix**: replace with the derived count and name the derivation, or drop the number.

---

## Verified correct (no bug) — recorded so the next auditor doesn't re-litigate

- Realization names, all defaults, all confirmed against `config/default.cfg`: `landmatrix_dec18`
  (:232), `endo_jan22` (:293), `managementcalib_aug19` (:357), `selfsuff_reduced` (:653),
  `normal_dec17` (:1577), `price_aug22` (:1634), `endo_apr13` (:1322).
- `q10_land_area` formula quoted at doc `:66-69` and `:301` matches
  `modules/10_land/landmatrix_dec18/equations.gms:13-15` **exactly**, set-sum preserved (this is the
  R16 anchor's failure mode, and the doc passes it).
- Appendix A `pcm_land` → `modules/10_land/landmatrix_dec18/postsolve.gms:9` ✓ (but see B04).
- Appendix A `pcm_tau` → `modules/13_tc/endo_jan22/postsolve.gms:16` ✓.
- Doc `:110-111` `pcm_carbon_stock` → `modules/56_ghg_policy/price_aug22/postsolve.gms:8` ✓.
- Doc `:251` — the whole rewritten Cycle-1 item 1 is correct: `q14_yield_crop` at
  `modules/14_yields/managementcalib_aug19/equations.gms:14-16` scales by the current-timestep
  `vm_tau`; `q14_yield_past` at `:35-39` uses the lagged `pcm_tau(j,"crop")`. Line ranges verified in
  current develop.
- Doc `:113-117` — `q52_emis_co2_actual` reads both `pcm_carbon_stock` and `vm_carbon_stock` ✓; and
  the parenthetical is right: `q39_cost_landcon` (`modules/39_landconversion/calib/equations.gms:12-15`,
  default realization `calib`) is area-based (`vm_landexpansion`/`vm_landreduction` × unit cost) and
  uses no carbon density.
- Doc `:151-153` — `vm_import`/`vm_export` genuinely do not exist anywhere in `modules/` or `core/`
  (confirmed, with `vm_supply` as positive control); `v21_trade(i_ex,i_im,k_trade)` exists **only** in
  `modules/21_trade/selfsuff_reduced_bilateral22/declarations.gms:23`.
- Doc `:145` — `q21_trade_glo` matches `modules/21_trade/selfsuff_reduced/equations.gms:12-14`
  including the `f21_trade_balanceflow` term; `q21_trade_reg` / `q21_trade_reg_up` exist at `:31,39`.
- Doc `:411-412` — `s56_buffer_aff = 0.5` and `s56_c_price_induced_aff = 1`
  (`modules/56_ghg_policy/price_aug22/input.gms:69,71`; `config/default.cfg:1762,1788`); the
  `(1-s56_buffer_aff)` crediting reading matches `equations.gms:77`.
- Doc `:284`, `:302` — `land_natveg = {primforest, secdforest, other}` (`core/sets.gms:262-263`),
  `consv_type = {protect, restore}`
  (`modules/22_land_conservation/area_based_apr22/sets.gms:28-29`),
  `pm_land_conservation(t,j,land,consv_type)` (`.../declarations.gms:15`) — all correct.
- Doc `:390` — `ag_pools = {vegc, litc}`, `stockType = {actual, actualNoAcEst}`
  (`modules/56_ghg_policy/price_aug22/sets.gms:209-213`), so `"vegc"`/`"actual"` are valid members.
- Doc `:150`, `:831`, `:1012` — CONOPT / IPOPT / CPLEX are all real solver paths
  (`modules/80_optimization/{nlp_apr17,nlp_ipopt,lp_nlp_apr17,nlp_par}`; default
  `c80_nlp_solver = conopt4`). **Not** a bug, though the default is never stated.
- Doc `:586` — Module 54 (`off`, the only realization) declares exactly one interface,
  `vm_p_fert_costs(i)` → module 11. "0 cycles, 1 connection" holds.
- Doc `:600` — the hypothetical `vm_cost_landcon(j,land)` uses the correct declared domain
  (`modules/39_landconversion/calib/declarations.gms:13`).

---

## Deferred (unverified / not proposed as edits)

1. `:60` — the gloss "`pcm_*` … (\"p\" = parameter, \"cm\" = current module)". MAgPIE's authoritative
   Coding Etiquette is not in the repo (README points off-repo), so I cannot settle whether `c` and
   `m` are separate slots (`m` = *module interface*, which would make "current module" backwards).
   In-repo circumstantial evidence: module-local carry parameters use `pc<NN>_` (`pc13_tau`,
   `pc35_secdforest`, `pc41_AEI_start`) while interface carry parameters use `pcm_`. The agent's own
   `reference/GAMS_MAgPIE_Patterns.md:225` carries the same "Previous Current Module" gloss, so this
   is a repo-wide convention question, not a defect of this doc. Not flagged.
2. `:61` — "`im_*` = Input data (exogenous, **never changes**)". `im_pollutant_prices` is rescaled,
   faded, floored and capped throughout `modules/56_ghg_policy/price_aug22/preloop.gms:37-108`, so
   "never changes" is loose; but the intended sense ("not optimized") is defensible. Not flagged.
3. `:410` — the numeric range "0-1000" for the carbon price. Depends on run-time-generated `.cs*`
   input files (gitignored, regenerated by `scripts/`), unverifiable offline.
4. `:1004` — "FOR EACH TIMESTEP (t = 1995, 2000, 2005, ..., 2100)". Under the default
   `c_timesteps = coup2100` (`core/sets.gms:188`) the steps are 5-yearly only to 2060, then 2070,
   2080, 2090, 2100. The "..." reads as illustrative; harm ≈ 0.
5. `:41-44` — "Timestep 1 … Fix previous state: `pcm_land("1995") ← vm_land("1995")`". The 1995 state
   actually comes from `modules/10_land/landmatrix_dec18/start.gms:11`
   (`pcm_land(j,land) = pm_land_start(j,land);`), not from a 1995 solve. Illustrative pseudocode.
6. `:723-724` — "Independent modules (37, 45, 54) can be run in parallel" and "water system 41-42-43
   has no cycles". 45_climate is a pure source with four consumers, and 42 reads `vm_area` from 30, so
   "isolable subsystem" is doubtful — but "independent" is too vague to falsify cleanly.
7. `:497` — "Visualize using GraphViz (files in `/tmp/magpie_analysis/`)" points at a scratch
   directory that does not exist; style/hygiene, not a code claim.
8. `:11`, `:749` — the "26 circular dependencies" total and the C5-C10 "inferred" table. The doc
   explicitly labels these unverified ("Note: Complete list … not fully documented"), and no cycle
   enumeration artifact exists in the repo. The count traces to
   `core_docs/Module_Dependencies.md:186` with no derivation behind it either — worth a separate
   NO-FIGURE-WITHOUT-AN-ARTIFACT pass, not an edit here.
9. `:351` — the doc renders `q41_area_irrig` flipped (`vm_AEI(j2) =g= sum(kcr, ...)` vs. the code's
   `sum(kcr, ...) =l= vm_AEI(j2)`). Mathematically identical; the equation name is omitted. Style.
10. `:136` — the diagram label "vm_supply/trade" as a return arrow from module 21 to 17. `vm_supply`
    is declared and populated by module 16 (`modules/16_demand/sector_may15/declarations.gms:11`),
    read by 16 and 21 — but the arrow is too loose to falsify as a specific claim.
