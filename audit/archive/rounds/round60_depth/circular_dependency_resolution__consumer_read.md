# R60 depth audit — `cross_module/circular_dependency_resolution.md`

**Lens**: `consumer_read` (enter from the consumer side: presolve/postsolve, equation RHS, and a
whole-tree grep of both `NAME(` and `NAME.` for every interface variable; priority on READ /
consumer-SET claims — phantoms *and* omissions — and on solution-level `.l` / `.lo` / `.up` reads)
**Ground truth**: MAgPIE `develop` read-only worktree (referred to below as `<develop>`; HEAD `2c02843ec`)
**Role map**: `audit/integrated/depth_rolemap.json` (checked first for every `vm_`/`pm_`/`im_`/`pcm_`/`fm_`
attribution claim, then confirmed with both-endpoints greps against `<develop>`)
**magpie4** (for the R "Verification" recipes): pinned clone `.cache/sources/magpie4`, version **2.76.4**
**Date**: 2026-08-02

---

## 1. Scope and what was verified

**Claims verified: 58.** The doc is 1041 lines but only a minority of it is code-checkable: §5–§10
are protocol/advice, and §6.2, §7.2, §9.1 are explicitly *hypothetical* GAMS snippets. I checked
every concrete interface-variable attribution, every `file:line` citation, every equation rendering,
every named default, both R-recipe families, and the two headline counts.

### What held up (verified correct — do not "fix" these)

| Claim | Result |
|---|---|
| `q10_land_area` body reproduced verbatim (`:66-70`) | ✅ exact — `modules/10_land/landmatrix_dec18/equations.gms:13-15` |
| `pcm_land(j,land) = vm_land.l(j,land)` at `modules/10_land/landmatrix_dec18/postsolve.gms:9` (Appendix A) | ✅ exact line |
| `pcm_carbon_stock(...) = vm_carbon_stock.l(...)` at `modules/56_ghg_policy/price_aug22/postsolve.gms:8` | ✅ exact line |
| `q52_emis_co2_actual` reads **both** `pcm_carbon_stock` and `vm_carbon_stock` | ✅ `modules/52_carbon/normal_dec17/equations.gms:16-19` |
| The `:113-117` parenthetical — land-conversion costs are area-based (`q39_cost_landcon`), no carbon density | ✅ `modules/39_landconversion/calib/equations.gms:12-15` (`vm_landexpansion`/`vm_landreduction` × unit costs) |
| `pcm_tau` updated at `modules/13_tc/endo_jan22/postsolve.gms:16` (`:251`, Appendix A) | ✅ exact line |
| `q14_yield_crop` scales `i14_yields_calib` by the **current** `vm_tau`, `equations.gms:14-16`; `q14_yield_past` uses **lagged** `pcm_tau(j2,"crop")`, `equations.gms:35-39` (`:251`) | ✅ both exact, and the lagged term is live by default (`s14_yld_past_switch = 0.25`, `config/default.cfg:369`) |
| `q21_trade_glo` rendering (`:144-145`); `q21_trade_reg` / `q21_trade_reg_up` exist (`:146`) | ✅ `modules/21_trade/selfsuff_reduced/equations.gms:12-14, 31-42` |
| "`vm_import`/`vm_export` do NOT exist … `v21_trade` only in `selfsuff_reduced_bilateral22`" (`:151-153`) | ✅ whole-tree grep for `vm_import|vm_export` returns **nothing**; `v21_trade` declared only at `modules/21_trade/selfsuff_reduced_bilateral22/declarations.gms:23` |
| `pc41_AEI_start(j) = vm_AEI.l(j)` in M41 postsolve (`:354`) | ✅ `modules/41_area_equipped_for_irrigation/endo_apr13/postsolve.gms:8` |
| `im_pollutant_prices(t_all,i,pollutants,emis_source)` domain + order (`:382`) | ✅ `modules/56_ghg_policy/price_aug22/declarations.gms:9` |
| `s56_buffer_aff` default 0.5 = "half of removals credited" (`:411`) | ✅ `config/default.cfg:1788`; `(1-s56_buffer_aff)` at `modules/56_ghg_policy/price_aug22/equations.gms:77` |
| `s56_c_price_induced_aff` is a 1/0 switch (`:412`) | ✅ default `1`, `config/default.cfg:1762` / `input.gms:69` |
| "Module 54 (Phosphorus): 0 cycles, 1 connection" (`:586`) | ✅ M54 has one realization (`off`) and one interface, `vm_p_fert_costs`, read only by M11 |
| `land_natveg = {primforest, secdforest, other}` usage in Cycle 2 | ✅ `core/sets.gms:262-263` |
| `core/macros.gms` exists as cited (`:54`) | ✅ |
| Realization names used in citations (`landmatrix_dec18`, `price_aug22`, `normal_dec17`, `endo_jan22`, `managementcalib_aug19`, `endo_apr13`, `selfsuff_reduced`) | ✅ all real **and** all default per `config/default.cfg` |

### Where it failed

Fifteen defects. They cluster in three places: (a) the four ASCII cycle diagrams, which assert
producer/consumer edges that do not exist in code (§2.1, §2.2, §3.1, §3.4); (b) Cycle 3, whose
central bound claim is **inverted**; (c) the R "Verification" recipes, which call magpie4 functions
and arguments that do not exist. Two headline generalisations ("26 cycles", "all `pcm_*` updated in
postsolve") are also not code-derivable.

---

## 2. Bugs

### B1 — Critical — `mechanism` — Cycle 3 inverts the AEI bound: previous-timestep AEI is a **lower** bound, never an upper bound

**Doc** (`circular_dependency_resolution.md:344`, with `:346`):
> "1. **Within timestep**: AEI capacity from **previous timestep** is **upper bound**"
> "3. **Next timestep**: Increased AEI allows more irrigation"

**Code**: in the default realization `endo_apr13` the *only* bound carried across timesteps is a
**lower** bound —

```gams
* modules/41_area_equipped_for_irrigation/endo_apr13/presolve.gms:11
vm_AEI.lo(j) = pc41_AEI_start(j) / ((1 - s41_AEI_depreciation)**(m_timestep_length));
```

with `s41_AEI_depreciation = 0` by default (`modules/41_area_equipped_for_irrigation/endo_apr13/input.gms:11`,
`config/default.cfg:1332`), so the floor is exactly last timestep's AEI. **No `.up` is ever assigned
to `vm_AEI` anywhere in the tree** — the four `vm_AEI.up` hits are output-writing lines in the two
`postsolve.gms` R-sections. Expansion is unbounded above and is paid for *within the current
timestep* via `q41_cost_AEI` (`equations.gms:19-23`), and `q41_area_irrig` (`equations.gms:10-11`)
binds irrigated area to the **current** `vm_AEI`, not to `pc41_AEI_start`. So the model *can* build
and immediately use new AEI in the same timestep — the exact opposite of the documented mechanism.
It also makes the doc's remedy at `:371` ("Limit AEI expansion rate (Module 41 configuration)")
unactionable: the only M41 config knob is `s41_AEI_depreciation`, which moves the **floor**.

**Verify**: `rg -n "vm_AEI\." <develop>/modules/ <develop>/core/ <develop>/main.gms`
→ 11 hits; the single non-postsolve, non-output hit is `presolve.gms:11` (a `.lo`).
`grep -n "s41_" <develop>/config/default.cfg` → `1332:cfg$gms$s41_AEI_depreciation <- 0`.

**Fix**: replace 1./3. with: "Within timestep: the previous timestep's AEI (depreciated by
`s41_AEI_depreciation`, default 0) is a **lower** bound — `vm_AEI.lo` at
`modules/41_area_equipped_for_irrigation/endo_apr13/presolve.gms:11`; AEI is otherwise free to expand
**within the same timestep**, priced by `q41_cost_AEI`. The temporal element is the ratchet (capacity
cannot fall below the depreciated stock), not a cap." Drop "Limit AEI expansion rate (Module 41
configuration)" from the Fix list or replace it with "raise `s41_AEI_depreciation` (relaxes the
floor) / raise `f41_c_irrig` unit costs".

---

### B2 — Critical — `mechanism` — Cycle 1 asserts a manure → soil-fertility → yield feedback that does not exist in the model

**Doc** (`circular_dependency_resolution.md:253`, with `:243`, `:268`, `:273`):
> "3. **Across timesteps**: Manure from livestock(t) affects yields(t+1)"
> "(Manure affects soil fertility)" · "Unrealistic intensification: Manure contribution overestimated"
> "**Fix**: … Limit manure impact on yields (Module 59, SOM)"

**Code**: module 14 contains **zero** references to manure, nitrogen, nutrients, SOM or AWMS in
either realization. Its complete interface-input set is `vm_tau`, `pcm_tau`, `pm_past_mngmnt_factor`,
`fm_tau1995`, `fm_croparea`, `pm_land_start`, `pm_climate_class`, `pm_carbon_density_*`,
`im_growing_stock*`, `fm_carbon_density`, `fm_aboveground_fraction`, `fm_ipcc_bef`. Realized yield is
`vm_yld = i14_yields_calib × vm_tau / fm_tau1995` for crops
(`modules/14_yields/managementcalib_aug19/equations.gms:14-16`) and
`i14_yields_calib × pm_past_mngmnt_factor × (1 + s14_yld_past_switch·(pcm_tau/fm_tau1995 − 1))` for
pasture (`:35-39`); `i14_yields_calib` derives from the LPJmL input `f14_yields` plus FAO/management
calibration (`preloop.gms:8-172`). Manure enters the **soil nitrogen budget** (M55 → M50), where it
substitutes for purchased fertilizer and therefore changes *cost*, not `vm_yld`. The only genuine
livestock → yield channel is `pm_past_mngmnt_factor`, populated in
`modules/70_livestock/fbask_jan16/presolve.gms:64-67` from cattle numbers (not manure) and affecting
**pasture yields only**.

**Verify**: `rg -in "manure|nitrogen|nutrient|soilc|som\b|awms" <develop>/modules/14_yields/`
→ no matches (positive control: `rg -c "vm_yld" <develop>/modules/14_yields/managementcalib_aug19/declarations.gms` → 1).

**Fix**: delete the manure links from the Cycle-1 chain and from Common Problems / Fix. Replace with:
"Livestock feeds back to yields only through `pm_past_mngmnt_factor`
(`modules/70_livestock/fbask_jan16/presolve.gms:64-67` → `q14_yield_past`), i.e. **pasture** yields
scaled by cattle numbers. Manure (M55 → M50) offsets inorganic fertilizer in the N budget and
affects production **cost**, never `vm_yld` — MAgPIE has no nutrient-limitation yield response."

---

### B3 — Major — `attribution_populate` — Cycle 4 attributes the crop land pool `vm_land(j,"crop")` to module 30; it is defined in module 29

**Doc** (`circular_dependency_resolution.md:386`):
> "vm_land(j,"crop") [30] → competes for land (crop ↓ as forest ↑)"

**Code**: `vm_land(j2,"crop")` is *populated* by the default cropland realization —
`modules/29_cropland/detail_apr24/equations.gms:12`
(`vm_land(j2,"crop") =e= sum((kcr,w), vm_area(j2,kcr,w)) + vm_fallow(j2) + sum(ac, v29_treecover(j2,ac));`,
default per `config/default.cfg:814`) — and bounded by `p29_avl_cropland` at `:23`. Module 30 only
**reads** it, once, in the bioenergy-target equation
(`modules/30_croparea/simple_apr24/equations.gms:23`); module 30 owns `vm_area`, not `vm_land("crop")`.
The repo's own config says so: `config/default.cfg:911` — "30_croparea defines the croparea, which is
a subcomponent of total cropland defined in 29_cropland".

**Verify**: `rg -n 'vm_land\(j2,"crop"\)' <develop>/modules/` → 12 hits: 8 in `29_cropland` (incl. the
`=e=` definition), 2 in `30_croparea` (RHS reads only), 2 in `detail_apr24` duplicates.

**Fix**: change to `vm_land(j,"crop") [29_cropland, q29_cropland] → competes for land`, and either add
29 to the Cycle-4 module list (`:378`) or relabel the arrow as "`vm_area` [30] → `vm_land("crop")` [29]".

---

### B4 — Major — `attribution_populate` — the natveg conservation constraint is attributed to module 22 (and to `vm_land.lo` "[10]"); it lives in modules 35 and 31

**Doc** (`circular_dependency_resolution.md:302`, with `:288` and `:292`):
> "vm_land(j,land_natveg) ≥ pm_land_conservation(t,j,land_natveg,"protect")  [22, bounds]"
> "vm_land(j,land_natveg) [35] → conservation bounds set on vm_land.lo [10]"
> "pm_land_conservation(t,j,land,consv_type) [22] → vm_land.lo(j,land_natveg) [10]"

**Code**: the default M22 realization `area_based_apr22` (`config/default.cfg:717`) **has no
`equations.gms` at all** — it is a `preloop`/`presolve_ini` parameter module that fills
`pm_land_conservation` (`presolve_ini.gms:54-121`). The constraint the doc writes is
`q35_natveg_conservation` in **module 35** (`modules/35_natveg/pot_forest_may24/equations.gms:19-22`),
and the per-pool bounds are set in **module 35's** presolve
(`presolve.gms:162` primforest, `:201` secdforest, `:231` other) and **module 31's** presolve
(`modules/31_past/endo_jun13/presolve.gms:9` for `"past"`). **Module 10 assigns no `vm_land.lo`
anywhere** — its only `vm_land.lo` occurrence is the output-writing line
`modules/10_land/landmatrix_dec18/postsolve.gms:52`.

**Verify**: `rg -n "vm_land\.lo" <develop>/modules/ <develop>/core/` → 13 hits; producers are
`35_natveg` (×4 incl. 1 read), `31_past` (×1), `34_urban` (×1); `22_land_conservation` appears only as
a **reader** of `vm_land.lo(j,"crop")` (`presolve_ini.gms:86,97,108`); `10_land` appears only in the
postsolve output block. `ls <develop>/modules/22_land_conservation/area_based_apr22/` → no `equations.gms`.

**Fix**: retag as `[q35_natveg_conservation, modules/35_natveg/pot_forest_may24/equations.gms:19-22]`
and add: "per-pool floors are imposed as `vm_land.lo` in **M35** presolve (`:162/:201/:231`) and **M31**
presolve (`:9`); M22 only computes `pm_land_conservation` — it has no equations and sets no bounds."
Also note this makes Cycle 2's "Resolution Type: Simultaneous Equations" only half-right: the per-pool
floors are fixed **before** the solve (Type 3 by the doc's own taxonomy); only the aggregate
`q35_natveg_conservation` is in the simultaneous system.

---

### B5 — Major — `mechanism` — "All `pcm_*` variables are updated in `postsolve.gms`" is false, and the exceptions matter

**Doc** (`circular_dependency_resolution.md:980`, Appendix A):
> "**Pattern**: All `pcm_*` variables are updated in `postsolve.gms` from corresponding `vm_*` optimal values"

**Code**: `pcm_land` is rewritten **in presolve, before the solve**, by two modules —
`modules/35_natveg/pot_forest_may24/presolve.gms:39` (`pcm_land(j,"primforest") = pcm_land(j,"primforest") - p35_disturbance_loss_primf(t,j);`),
`:131` (`pcm_land(j,"secdforest") = sum(ac, pc35_secdforest(j,ac));`), `:137` (`"other"`), and
`modules/32_forestry/dynamic_may24/presolve.gms:101` (`pcm_land(j,"forestry") = sum((type32,ac), v32_land.l(j,type32,ac));`)
— plus initialisation in `modules/34_urban/exo_nov21/preloop.gms:17` and
`modules/10_land/landmatrix_dec18/start.gms:11`. `pcm_tau` is assigned in
`modules/13_tc/endo_jan22/presolve.gms:77` (first timestep) and, in the `exo` realization, from
`pc13_tau`/`pc13_tau_consv` rather than any `vm_` level (`modules/13_tc/exo/presolve.gms:77`).
`pcm_carbon_stock` is initialised from `fm_carbon_density × pcm_land` in
`modules/56_ghg_policy/price_aug22/preloop.gms:10`, and its `"soilc"` slice is updated by M59
(`modules/59_som/cellpool_jan23/postsolve.gms:13`), not M56.

This is load-bearing, not pedantic: `sum(land, pcm_land(j2,land))` is the RHS of `q10_land_area`, so a
reader who believes `pcm_land` is only ever written in M10's postsolve will mis-trace the land balance
and miss that M35 mutates the same-timestep RHS.

**Verify**: `rg -n "^\s*pcm_land\([^)]*\)\s*=" <develop>/modules/ | grep -v ov_` → **7** assignment
sites — `10_land/…/postsolve.gms:9`, `10_land/…/start.gms:11`, `34_urban/exo_nov21/preloop.gms:17`,
`35_natveg/pot_forest_may24/presolve.gms:39,131,137`, `32_forestry/dynamic_may24/presolve.gms:101` —
**only one of which is a `postsolve.gms`**.

**Fix**: "Most `pcm_*` interfaces are refreshed in `postsolve.gms` from `vm_*.l`, **but not all**:
`pcm_land` slices are also overwritten in M32/M35 **presolve** (age-class bookkeeping and primforest
disturbance loss) and initialised in M34 preloop / M10 `start.gms`; `pcm_tau` is set in M13 presolve on
the first timestep; `pcm_carbon_stock` is initialised in M56 preloop and its `soilc` slice is owned by
M59. Grep both `postsolve.gms` and `presolve.gms` before assuming a `pcm_` value is frozen for the solve."

---

### B6 — Major — `other` — "26 circular dependency cycles" is not reproducible from code (and §8.2 concedes 22 were guessed)

**Doc** (`circular_dependency_resolution.md:11`, echoed at `:1036`):
> "MAgPIE contains **26 circular dependency cycles** where modules depend on each other bidirectionally."
> "**Coverage**: 4 major cycles documented in detail, 26 total cycles cataloged"

**Code**: under the natural code definition (module A → B when A populates an interface B reads),
the `develop` tree yields **46 bidirectional module pairs (2-cycles) alone**, and a single strongly
connected component spanning **31 modules** (10, 13-18, 20-22, 29-32, 34-36, 38, 50-53, 55-59, 62,
70, 71, 73) plus a second SCC {42, 43} — which makes the number of simple cycles larger than 26 by
many orders of magnitude. §8.2 of the doc itself says the remaining 22 are "Inferred" / "Suspected"
and lists only six with "…", i.e. the headline number was never derived. This is the
NO-FIGURE-WITHOUT-AN-ARTIFACT class: one unmeasured number stated twice as fact.

**Verify**: Tarjan SCC + 2-cycle count over `audit/integrated/depth_rolemap.json` edges
(`populated_by × read_by`, `fm_*` excluded) → `non-fm bidirectional module pairs: 46`;
`largest SCC size: 31`. (Caveat recorded honestly: the role map is a superset across realizations,
so a default-config-only graph would be somewhat smaller — but every pair listed for M10/M29/M31/M32/M35
is a default-realization pair, so the count stays far above 26.)

**Fix**: replace "contains 26 circular dependency cycles" with a statement that is either measured or
qualitative — e.g. "MAgPIE's module dependency graph is strongly connected across ~30 modules; this
document treats **4 measured, code-verified cycles** in detail and lists further *candidate* cycles in
§8.2 as unverified." If a number is wanted, generate it with a named script and cite the artifact.

---

### B7 — Major — `other` — every R "Verification" recipe calls magpie4 functions or arguments that do not exist

**Doc** (`circular_dependency_resolution.md:309-310`, `:360-361`, `:420-421`):
> `land <- land(gdx, type="natveg", level="cell")` · `land_protection <- land_conservation(gdx, type="natveg")`
> `irrig_area <- croparea(gdx, level="cell", irrigation="irrigated")` · `aei_capacity <- AEI(gdx, level="cell")`
> `forest_area <- land(gdx, type="forestry", level="regglo")` · `cdr_revenue <- costs(gdx, components="reward_cdr_aff")`

**Code** (pinned magpie4 2.76.4, `.cache/sources/magpie4`):

| Doc call | Reality |
|---|---|
| `AEI(gdx, ...)` | no such export; the function is `water_AEI(gdx, file = NULL, level = "reg")` (`R/water_AEI.R:18`) |
| `land_conservation(gdx, type=)` | no such name; the function is `landConservation(gdx, file, level = "cell", cumuRestor, baseyear, annualRestor, sum)` (`R/landConservation.R:25-27`) |
| `land(gdx, type=)` | argument is `types` (plural): `land(gdx, file, level = "reg", types = NULL, subcategories = NULL, sum = FALSE)` (`R/land.R:29`) — and `"natveg"` is not a land type (`core/sets.gms`: `land = {crop, past, forestry, primforest, secdforest, urban, other}`) |
| `croparea(gdx, irrigation=)` | no such argument: `croparea(gdx, file, level, products, product_aggr, water_aggr)` (`R/croparea.R:27`) → "unused argument" error |
| `costs(gdx, components=)` | no such argument: `costs(gdx, file, level = "reg", type = "annuity", sum = TRUE)` (`R/costs.R:19`) |
| `yields(gdx, level="cell", products="kcr")` | ✅ valid (`R/yields.R:26-32`) |

**Verify**: `grep -nE "^export\((AEI|land_conservation)\)" NAMESPACE` → no match (positive control:
`export(costs)`, `export(croparea)`, `export(land)`, `export(yields)` all present);
`grep -rn "land_conservation" R/` → only `readGDX(gdx, "pm_land_conservation")` inside
`R/landConservation.R:43`.

**Fix**: rewrite the three recipes against the pinned API — `water_AEI(gdx, level="cell")`,
`landConservation(gdx, level="cell")`, `land(gdx, types=c("primforest","secdforest","other"), level="cell")`,
`croparea(gdx, level="cell", water_aggr=FALSE)`, `costs(gdx, level="regglo", sum=FALSE)["reward_cdr_aff"]` —
and add the standard caveat that magpie4 is version-pinned (`project/version_pins.json`).

---

### B8 — Major — `other` — `im_pollutant_prices` is quoted in USD/tCO2; it is USD per **tC**

**Doc** (`circular_dependency_resolution.md:410`):
> "`im_pollutant_prices`: Carbon price trajectory (0-1000 USD/tCO2)"

**Code**: declared "Certificate prices for N2O-N CH4 CO2-C used in the model (**USD17MER per Mg**)"
(`modules/56_ghg_policy/price_aug22/declarations.gms:9`), i.e. per Mg of the *pollutant* — per **tC**
for `co2_c`. The code states the conversion explicitly:
`modules/56_ghg_policy/price_aug22/preloop.gms:77` — `*12/44 conversion from USD17MER per tC to USD17MER per tCO2`,
used in the CH4/N2O price caps at `:80-82`. A user reading a `co2_c` price of e.g. 300 as USD/tCO2 is
off by 44/12 ≈ 3.67×.

**Verify**: `rg -n "44/12|12/44" <develop>/modules/56_ghg_policy/price_aug22/*.gms` → `preloop.gms:77,80,81,82`.

**Fix**: "`im_pollutant_prices`: GHG certificate prices, **USD17MER per Mg of pollutant** — for `co2_c`
that is USD per **tC** (multiply by 12/44 for USD/tCO2); default trajectory
`c56_pollutant_prices = R34M410-SSP2-NPi2025` (`config/default.cfg`)." Drop the unsourced "0-1000" range
or attribute it to a named scenario file.

---

### B9 — Major — `data_flow_direction` — §2.1's diagram makes module 52 the producer of `vm_carbon_stock` and module 10 a consumer of `pcm_carbon_stock`; neither is true

**Doc** (`circular_dependency_resolution.md:95-99`):
> `Module 10 (Land) ────────────→ Module 52 (Carbon)` … `pcm_carbon_stock ←──── vm_carbon_stock`

**Code**: module 52 contains **no reference to `vm_land` or `pcm_land` at all**, so there is no 10 → 52
edge; and `vm_carbon_stock` is declared in **56** (`modules/56_ghg_policy/price_aug22/declarations.gms:34`)
and populated by **29, 31, 32, 34, 35, 59** — module 52 is a pure *reader*
(`modules/52_carbon/normal_dec17/equations.gms:19`). `pcm_carbon_stock` is read only by 52, 56 and 59;
module 10 never touches it. The real Land↔Carbon loop runs M10 `vm_land` → M29/31/32/34/35 (which
populate `vm_carbon_stock` from their own area/age-class state) → M52 → `vm_emissions_reg`.

**Verify**: `rg -n "vm_land" <develop>/modules/52_carbon/` → no match (positive control:
`rg -n "pcm_carbon_stock" <develop>/modules/52_carbon/` → `equations.gms:19`);
`rg -rn "pcm_carbon_stock" <develop>/modules/` → hits only in 52, 56, 59.

**Fix**: redraw as `M10 vm_land → {M29,M31,M32,M34,M35} populate vm_carbon_stock (declared in M56) →
M52 q52_emis_co2_actual reads pcm_carbon_stock(t-1) and vm_carbon_stock(t)`. Keep the (correct) Code
Evidence block below the diagram.

---

### B10 — Major — `data_flow_direction` — §2.2's diagram routes `vm_supply` from module 21 back to module 17; module 17 never reads it, and module 16 owns it

**Doc** (`circular_dependency_resolution.md:133-136`):
> `vm_prod_reg(i,kall) ──→ Module 21 (Trade)` … `└── vm_supply/trade ─────┘`

**Code**: `vm_supply` is declared and populated in **16_demand**
(`modules/16_demand/sector_may15/declarations.gms:11`; `q16_supply_*` at `equations.gms:20-85`) and read
by 16 and 21 only. Module 17 has **zero** references to `vm_supply`. The 17↔21 coupling is not a
hand-off: both modules act on the **same shared variable** `vm_prod_reg` — M17 defines it
(`q17_prod_reg`), M21 constrains it (`q21_trade_glo/_reg/_reg_up`). That is parallel co-use, which is
precisely why the solver resolves it simultaneously.

**Verify**: `rg -n "vm_supply" <develop>/modules/17_production/` → no match (positive control:
`rg -n "vm_prod_reg" <develop>/modules/17_production/` → 6 hits).

**Fix**: relabel the return arrow "`vm_prod_reg` constrained by M21's trade equations (shared variable,
not a hand-off)" and note that `vm_supply` originates in **16_demand** and is consumed by M21.

---

### B11 — Major — `realization` — under the default croparea realization, module 30 does not consume `vm_AEI` at all

**Doc** (`circular_dependency_resolution.md:336`):
> "vm_AEI(j) [41] → constraint on vm_area(j,kcr,"irrigated") [30]"

**Code**: the default croparea realization is `simple_apr24` (`config/default.cfg:915`), and it
declares `vm_AEI` explicitly unused — `modules/30_croparea/simple_apr24/not_used.txt:2`
(`vm_AEI,input,questionnaire`). The only M30 reference to `vm_AEI` is in the **non-default**
`detail_apr24`, and it is a *rotation over-specialisation penalty*, not a capacity constraint:
`q30_rotation_max_irrig` at `modules/30_croparea/detail_apr24/equations.gms:79-82`. The capacity
constraint that actually couples them is `q41_area_irrig` in **module 41**
(`modules/41_area_equipped_for_irrigation/endo_apr13/equations.gms:10-11`).

**Verify**: `rg -n "vm_AEI" <develop>/modules/` → M30 hits are exactly
`detail_apr24/equations.gms:82` and `simple_apr24/not_used.txt:2`.

**Fix**: "`vm_AEI(j)` [41] caps irrigated area through **`q41_area_irrig` in module 41**
(`equations.gms:10-11`). Under the default `simple_apr24` croparea realization module 30 does not read
`vm_AEI` (`not_used.txt`); only the non-default `detail_apr24` uses it, in the rotation penalty
`q30_rotation_max_irrig`."

---

### B12 — Major — `other` — `vm_yields` is not a MAgPIE variable

**Doc** (`circular_dependency_resolution.md:844`):
> `vars <- c("vm_land", "vm_prod", "vm_carbon_stock", "vm_yields", ...)`

**Code**: no `vm_yields` exists anywhere in the tree; the yield variable is `vm_yld(j,kve,w)`
(`modules/14_yields/managementcalib_aug19/declarations.gms:27`). The other three names in the list are
real, which is what makes the fabricated one credible — `readGDX(gdx, "vm_yields")` fails.

**Verify**: `rg -n "vm_yields" <develop>/` → no matches (positive control:
`rg -c "vm_yld" <develop>/modules/14_yields/managementcalib_aug19/declarations.gms` → 1).

**Fix**: `"vm_yld"`.

---

### B13 — Minor — `other` — §7.3 calls 41-42-43 a cycle-free, isolatable subsystem; both 41 and 42 are coupled to the land/production core, and the doc's own C3 says so

**Doc** (`circular_dependency_resolution.md:724`):
> "**Subsystems** with no cycles (water system: 41-42-43) can be isolated"

**Code**: M41 constrains `vm_area` (M30) via `q41_area_irrig`
(`modules/41_area_equipped_for_irrigation/endo_apr13/equations.gms:10-11`); the default M42 realization
`all_sectors_aug13` (`config/default.cfg:1340`) reads `vm_area` **and** `vm_prod` in its equations
(`modules/42_water_demand/all_sectors_aug13/equations.gms`, interfaces also listed in
`realization.gms`), plus `im_wat_avail` (M43) and three M09 drivers in presolve. The claim also
contradicts the same document's C3 entry (`:742`), which lists 30-41 as a cycle.

**Verify**: `rg -o "\b(vm_|pm_|im_|pcm_)[A-Za-z0-9_]+" <develop>/modules/42_water_demand/all_sectors_aug13/*.gms | sort -u`
→ `vm_area`, `vm_prod`, `vm_watdem`, `vm_water_cost`, `im_wat_avail`, `im_development_state`,
`im_gdp_pc_mer`, `im_pop_iso`.

**Fix**: "42→43 is the only clean acyclic pair; 41 and 42 both consume `vm_area`/`vm_prod` from the
land-use core (and 41 constrains M30's `vm_area`), so the water modules cannot be isolated."

---

### B14 — Minor — `set_membership` — `q17_prod_reg` is written over `kall`; the equation is defined over `k`

**Doc** (`circular_dependency_resolution.md:143`):
> `vm_prod_reg(i,kall) = sum(cell(i,j), vm_prod(j,kall))               [q17_prod_reg]`

**Code**: `q17_prod_reg(i2,k) .. vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k));`
(`modules/17_production/flexreg_apr16/equations.gms:10-11`). `vm_prod` is declared **only** over
`(j,k)` (`declarations.gms:9`), so `vm_prod(j,kall)` is not a legal reference; `vm_prod_reg` is
declared over `(i,kall)` (`declarations.gms:10`) and its non-`k` slices are populated **elsewhere** —
`modules/20_processing/substitution_may21/equations.gms:41` (`"cottn_pro"`), and M18/M21 constrain
`kres`/`k_trade` slices. Writing `kall` in the equation hides that per-slice ownership.

**Verify**: `grep -n "vm_prod" <develop>/modules/17_production/flexreg_apr16/declarations.gms` →
`9: vm_prod(j,k)`, `10: vm_prod_reg(i,kall)`.

**Fix**: `vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k))   [q17_prod_reg — note: the k ⊂ kall
slices only; other kall slices of vm_prod_reg are set by M20 processing]`.

---

### B15 — Minor — `attribution_populate` — `vm_prod(kli)` is attributed to module 70; module 70 contains no `vm_prod` reference

**Doc** (`circular_dependency_resolution.md:204-206`):
> `Module 14 (Yields) ←→ Module 13 (TC) ←→ Module 70 (Livestock)` … `vm_prod(kli)`

**Code**: module 70 works exclusively at regional level with `vm_prod_reg(i2,kap/kli)`
(`modules/70_livestock/fbask_jan16/equations.gms:18, 28, 36, 60, 65, 70`). Cluster-level
`vm_prod(j,kli)` is populated by **71_disagg_lvst**, not 70. (Same note for `:239`, which tags
`vm_prod_reg` "[70]" although it is declared in 17.)

**Verify**: `rg -n "vm_prod\(" <develop>/modules/70_livestock/` → no match (positive control:
`rg -n "vm_prod_reg" <develop>/modules/70_livestock/fbask_jan16/*.gms` → 6 hits).

**Fix**: `vm_prod_reg(i,kli)` under Module 70; if cluster-level livestock production is meant, tag it
`vm_prod(j,kli) [71_disagg_lvst]`.

---

### B16 — Informational — `citation` — the postsolve snippet uses the equation alias `j2` where the code uses `j`

**Doc** (`circular_dependency_resolution.md:73`):
> `pcm_land(j2,land) = vm_land.l(j2,land);`

**Code**: `pcm_land(j,land) = vm_land.l(j,land);`
(`modules/10_land/landmatrix_dec18/postsolve.gms:9`). `j2` is the alias used *inside* equations; the
doc's own Appendix A cites the same line correctly. Harmless, but the block is presented as verbatim
postsolve code.

**Verify**: `sed -n '9p' <develop>/modules/10_land/landmatrix_dec18/postsolve.gms`.

**Fix**: use `j`.

---

## 3. Deferred (not filed — could not be verified, or definitionally ambiguous)

- `:584` "Modifying Module 10 (Land): EXTREME RISK (4+ cycles, **15 consumers**)". No definition I tested
  reproduces 15: readers of `vm_land` alone = 10 external modules; `vm_land ∪ pcm_land` = 14; all 11
  module-10 interfaces = 18 (11, 13, 14, 22, 29, 30, 31, 32, 34, 35, 39, 44, 50, 56, 58, 59, 71, 80).
  The number may be inherited from `core_docs/Module_Dependencies.md` under a different counting rule,
  so I am not filing it as a defect — but it is not code-derivable as stated.
- `:745` "**Source**: Module_Dependencies.md (lines 149-179)" — a doc-to-doc citation; out of scope for a
  code lens (the R60 structural pass should check whether those lines still hold the cycle table).
- §6.2 / §7.2 / §9.1 hypothetical snippets use identifiers that do not exist (`pm_water_avail` at `:593`,
  `pm_yields` at `:608`, `tau_factor` at `:811-815`). They are explicitly labelled as *proposed* edits,
  not as descriptions of current code, so I did not file them; a doc-style pass may still want them
  renamed to real analogues (`im_wat_avail`, `pm_yields_semi_calib`, `vm_tau`).
- `:60-62` naming-convention glosses (`pcm_` = "current module"; `im_` = "exogenous, never changes").
  `im_pollutant_prices` *is* modified after loading (`preloop.gms:67, 80-82`), so "never changes" is
  loose — but I found no authoritative in-repo statement of the prefix convention to check the gloss
  against, so I am not filing it.
- `:41-51` the 1995→2100 timestep schematic and `:1004` "FOR EACH TIMESTEP (t = 1995, 2000, …, 2100)"
  were not checked against `config/default.cfg` `gms$c_timesteps` / `main.gms` loop structure.
- All Section 9 symptom/threshold numbers (oscillation magnitudes, RMSE traces, "iteration limit
  10000") are illustrative and unverifiable from code.

---

## 4. Pattern for the flywheel

Every one of B3, B4, B9, B10, B15 is the **same failure mode**: an ASCII arrow diagram drawn from a
mental model of the domain rather than from the interface graph, in which the module that *conceptually
owns a topic* is drawn as the module that *produces the variable*. Carbon → M52, cropland → M30,
conservation → M22, trade-supply → M21, livestock production → M70 — all five are topic-ownership, and
all five are wrong at the code level. Any future pass on a cross-module doc should treat "the diagrams"
as a distinct, high-yield verification target and check each arrow against
`audit/integrated/depth_rolemap.json` + a both-endpoints grep, rather than reading only the prose.
