# R60 depth audit — `modules/module_34.md` — lens: `declare_populate`

**Target doc**: `modules/module_34.md` (Module 34, Urban Land)
**Ground truth**: MAgPIE `develop` read-only worktree, HEAD `2c02843ec` ("Merge pull request #919 from alexkoberle/dyn_reg_tau")
**Default realization** (`config/default.cfg:1147`): `cfg$gms$urban <- "exo_nov21"` — doc leads with `exo_nov21` ✓
**Role map consulted**: `audit/integrated/depth_rolemap.json` (all attribution claims cross-checked, then confirmed by both-endpoints grep in code)

---

## 1. What checked out (no bug)

The doc's core equation layer is clean. Verified line-by-line against `modules/34_urban/exo_nov21/equations.gms`:

| Doc claim | Code | Verdict |
|---|---|---|
| `q34_urban_cost1` formula, `equations.gms:17-18` | matches exactly | ✓ |
| `q34_urban_cost2` formula, `equations.gms:20-21` | matches exactly | ✓ |
| `q34_urban_cell` formula, `equations.gms:25-26` | matches exactly | ✓ |
| `q34_urban_land` formula, `equations.gms:30-31` | matches exactly | ✓ |
| `q34_bv_urban` formula, `equations.gms:34-35` | matches exactly | ✓ |
| 5 equations (exo_nov21), 0 (static) | `exo_nov21/declarations.gms:18-24` declares exactly 5; `static/` has no `equations.gms` | ✓ |
| `s34_urban_deviation_cost = 1e6` USD17MER/ha, `input.gms:13` | `/ 1e+06 /` | ✓ |
| `c34_urban_scenario` default `SSP2`, `input.gms:8` | `$setglobal c34_urban_scenario SSP2`; `config/default.cfg:1150` `<- "SSP2"` | ✓ |
| `urban_scen34 / SSP1..SSP5 /`, `sets.gms:9-10` | exact | ✓ |
| `vm_cost_urban.scale(j) = 1e3`, `scaling.gms:8` | exact | ✓ |
| `v34_cost1/2.scale = 1e-4` commented out, `scaling.gms:9-10` | exact | ✓ |
| `vm_carbon_stock.fx(j,"urban",ag_pools,stockType)=0`, `presolve.gms:8` | exact | ✓ (but see BUG-1 for what the doc infers from it) |
| t=1 `vm_land.fx`, t>1 `.lo/.l/.up`, `presolve.gms:10-15` | exact | ✓ (range citation drifts — BUG-7) |
| `pcm_land(j,"urban") = i34_urban_area("y1995",j)`, `preloop.gms:17` | exact; phase order confirms it wins over M10's `start.gms:11` (`core/calculations.gms:13` start → `:15` preloop) | ✓ |
| `vm_bv.l` init, `preloop.gms:20-21` | exact | ✓ |
| static fixes `vm_land`/`vm_carbon_stock`/`vm_bv`/`vm_cost_urban`, `static/presolve.gms:9-14` | lines 9, 10, 12, 14 | ✓ |
| static eliminates 5 eqs + 2 vars, `vm_cost_urban` persists fixed to 0 | `static/declarations.gms:10`, `static/presolve.gms:14` | ✓ |

**Attribution claims that survived the role map + both-endpoints grep:**

- "`vm_carbon_stock` is declared in Module 56, not Module 52" (doc:288) — **correct**: `modules/56_ghg_policy/price_aug22/declarations.gms:34`. No declaration in `52_carbon`.
- `q52_emis_co2_actual` (`modules/52_carbon/normal_dec17/equations.gms:16`) and `q56_emis_pricing_co2` (`modules/56_ghg_policy/price_aug22/equations.gms:19`) — both equation names correct, both read `vm_carbon_stock` directly (parallel readers, not a 52→56 hand-off). Doc:288 states this correctly.
- `vm_cost_urban` → Module 11 only: sole external consumer is `modules/11_costs/default/equations.gms:45`. ✓
- `vm_bv` → Module 44: declared `modules/44_biodiversity/bii_target/declarations.gms:11`; `urban` ∈ `landcover44` (`bii_target/sets.gms:11`). ✓
- `fm_bii_coeff` "from biodiversity module" (doc:181) — correct, declared `modules/44_biodiversity/bii_target/input.gms:17`.
- `fm_luh2_side_layers` (doc:183) — declared `modules/10_land/landmatrix_dec18/input.gms:19`; `potnatveg(luh2_side_layers10) / forested, nonforested /` at `modules/10_land/landmatrix_dec18/sets.gms:15-16`. Doc's gloss ("potential natural vegetation share") is acceptable.
- Land-balance participation: `q10_land_area` sums over `land` which includes `urban` (`core/sets.gms:251`). ✓

---

## 2. Bugs

### BUG-1 — 🔴 Critical — `set_membership` — "urban carbon stocks are zero" over-generalizes `ag_pools` to all `c_pools`

**Doc** (`module_34.md:304`, and the same error at `:28`, `:33`, `:198`, `:288-289`, `:359-361`, `:473`, `:474`, `:585`):

> **Carbon Balance**: ⚠️ **LIMITATION** - Urban land carbon set to **ZERO** (no data for urban vegetation).

and `module_34.md:473-474`:

> **Module 52 (Carbon)**: Receives `vm_carbon_stock(j,"urban",*) = 0` … **Module 56 (GHG Policy)**: Receives `vm_carbon_stock(j,"urban",*) = 0`

and `module_34.md:289`: "Urban land contributes zero to carbon balance (data limitation)".

**Reality in code.** Module 34 fixes **only the above-ground slice**:
`modules/34_urban/exo_nov21/presolve.gms:8` → `vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0;`
with `ag_pools(c_pools) / vegc, litc /` (`modules/56_ghg_policy/price_aug22/sets.gms:209-210`) and `c_pools / vegc, litc, soilc /` (`core/sets.gms:324-325`).

The **`soilc` slice of urban is populated by Module 59 (som)** and is structurally non-zero:

- `modules/59_som/cellpool_jan23/sets.gms:10-11` — `noncropland59(land) / past, forestry, primforest, secdforest, other, urban /` (urban is a member).
- `modules/59_som/cellpool_jan23/equations.gms:31-33` — `q59_som_target_noncropland(j2,noncropland59) .. v59_som_target(j2,noncropland59) =e= vm_land(j2,noncropland59) * sum(ct,f59_topsoilc_density(ct,j2));`
- `modules/59_som/cellpool_jan23/equations.gms:61-65` — `q59_carbon_soil(j2,land,stockType) .. vm_carbon_stock(j2,land,"soilc",stockType) =e= v59_som_pool(j2,land) + vm_land(j2,land)*sum(ct,i59_subsoilc_density(ct,j2));`
- `modules/59_som/cellpool_jan23/preloop.gms:33-35` — initialises `pcm_carbon_stock(j,noncropland59,"soilc",stockType)` and `vm_carbon_stock.l(j,noncropland59,"soilc",stockType)` from `fm_carbon_density("y1995",j,noncropland59,"soilc") * pm_land_start(j,noncropland59)`.
- The alternative realization does the same: `modules/59_som/static_jan19/sets.gms:9-10` `regularland59 / past, forestry, primforest, secdforest, urban /`, used at `static_jan19/equations.gms:18`.

Decisively, Module 52 **explicitly** gives urban a non-zero soil carbon density, with a comment saying so:

```
* Fix urban area soilc to natural land soilc as long as preprocessed
* fm_carbon_density does not provide meaningful numbers for urban.
fm_carbon_density(t_all,j,"urban","soilc") = fm_carbon_density(t_all,j,"other","soilc")
```
(`modules/52_carbon/normal_dec17/input.gms:32-35`)

And urban soil carbon **is** an emission source that reaches both consumers: `urban_soilc ∈ emis_oneoff` (`core/sets.gms:318`), mapped `urban_soilc . (urban) . (soilc)` (`core/sets.gms:350`), summed in `q52_emis_co2_actual` (`modules/52_carbon/normal_dec17/equations.gms:16-19`) and priced in `q56_emis_pricing_co2` (`modules/56_ghg_policy/price_aug22/equations.gms:19-22`).

Note that the equation-level non-zero-ness does **not** depend on unreadable input data: `q59_carbon_soil` scales `f59_topsoilc_density` and `i59_subsoilc_density` (both land-type-independent) by `vm_land(j,"urban")`.

**Why Critical.** A reader acting on this doc would (a) report zero urban carbon emissions from a MAgPIE run when `urban_soilc` CO2 is actually computed and priced, and (b) if extending the model to "add urban carbon", duplicate a soil pool Module 59 already maintains. This is the R20 anchor class (wrong producer set for a carbon-stock slice) — the G2 carbon-stock distinction the MANDATEs single out.

**Proposed fix.** Everywhere the doc says urban carbon is zero, qualify the pool set:
- `:28` → "Fixes urban **above-ground** carbon stocks (`ag_pools` = vegc, litc) to zero (`presolve.gms:8`); urban **soil** carbon is set by Module 59 (som)."
- `:33` → "Does NOT include urban **vegetation/litter** carbon — `vm_carbon_stock(j,"urban",ag_pools,*)` fixed to 0. Urban `soilc` **is** modelled (M59 `q59_carbon_soil`, `urban ∈ noncropland59`), with density set to that of `other` land (`modules/52_carbon/normal_dec17/input.gms:35`)."
- `:198`, `:288-289`, `:304`, `:359-368`, `:585` → same qualification; replace "Urban land contributes zero to carbon balance" with "Urban contributes zero **vegc/litc**; `urban_soilc` is an active `emis_oneoff` source (`core/sets.gms:318`) entering `q52_emis_co2_actual` and `q56_emis_pricing_co2`."
- `:473-474` → replace the wildcard `vm_carbon_stock(j,"urban",*) = 0` with `vm_carbon_stock(j,"urban",ag_pools,stockType) = 0` (M34's slice only) and add M59 as the populator of the `soilc` slice.

---

### BUG-2 — 🟠 Major — `attribution_populate` — Module 59 (som) is absent from the doc although it reads M34's urban land and populates the urban soil-carbon slice

**Doc** (`module_34.md:318`, and the whole "Downstream Modules" list at `:278-294`):

> **Provides To**: Module 10 (Land), Module 11 (Costs - deviation penalties), Module 22 (Conservation - potentially), Module 44 (Biodiversity - urban BII)

`grep -n "59\|som\b" modules/module_34.md` → **no match**. Module 59 appears nowhere in the doc.

**Reality in code.** Module 59 is a **direct** reader of `vm_land(j,"urban")` and a **direct** populator of `vm_carbon_stock(j,"urban","soilc",stockType)`:

- read: `modules/59_som/cellpool_jan23/equations.gms:31-33` (`vm_land(j2,noncropland59)`, `urban ∈ noncropland59` per `sets.gms:11`) and `equations.gms:61-65`.
- populate: LHS of `q59_carbon_soil` at `modules/59_som/cellpool_jan23/equations.gms:62`.

Role map agrees: `vm_carbon_stock.populated_by` includes `59`; `vm_land.read_by` includes `59`.

Secondary defect in the same line: the `Provides To` list also omits **Module 52** and **Module 56**, which the doc's own body (`:288`, `:473-474`) names as consumers — the summary line and the body disagree. And `**Total Connections**: 3-4` (`:316`) is consequently wrong.

**Proposed fix.** `:318` → `**Provides To**: Module 10 (Land, `vm_land`), Module 11 (Costs, `vm_cost_urban`), Module 44 (Biodiversity, `vm_bv`), Module 52 + Module 56 (`vm_carbon_stock(j,"urban",ag_pools,*)`), Module 59 (som — reads `vm_land(j,"urban")` in `q59_som_target_noncropland` and populates the urban `soilc` stock), Module 22 + Module 35 (via `pcm_land(j,"urban")`)`. Update `Total Connections` accordingly and add a "Module 59 (SOM)" entry to the Downstream Modules section.

---

### BUG-3 — 🟠 Major — `attribution_read` — "Upstream Modules … None" is false and contradicts the doc's own dependency line

**Doc** (`module_34.md:274-276`):

> ### Upstream Modules (provide data to Module 34)
> None - Module 34 is a data provider, reads only from external input files (LUH3)

**Reality in code.** `exo_nov21` reads four interface objects owned by other modules:

| Object | Declared in | Read by M34 at |
|---|---|---|
| `sm_fix_SSP2` | `modules/09_drivers/aug17/input.gms:22` (`/ 2025 /`) | `exo_nov21/preloop.gms:10` |
| `fm_bii_coeff` | `modules/44_biodiversity/bii_target/input.gms:17` | `exo_nov21/equations.gms:35`, `preloop.gms:21` |
| `fm_luh2_side_layers` | `modules/10_land/landmatrix_dec18/input.gms:19` | `exo_nov21/equations.gms:35`, `preloop.gms:21` |
| `pcm_land` | `modules/10_land/landmatrix_dec18/declarations.gms:11` | `exo_nov21/preloop.gms:20-21`; `static/presolve.gms:9,12` |

The `static` realization's own `not_used.txt` ("`sm_fix_SSP2, input, not needed`") confirms `sm_fix_SSP2` is a declared *input interface* of module 34 — which only makes sense if the module has upstream inputs. The doc contradicts itself 44 lines later at `:320` ("**Depends On**: Module 09").

**Proposed fix.** `:274-276` → "**Upstream Modules**: Module 09 (`sm_fix_SSP2`, `modules/09_drivers/aug17/input.gms:22`) gates the historical SSP2 freeze; Module 44 (`fm_bii_coeff`) and Module 10 (`fm_luh2_side_layers`, `pcm_land`) supply the BV inputs. The urban trajectory itself comes from M34's own input file `f34_urbanland.cs3` (`input.gms:16-19`)."

---

### BUG-4 — 🟡 Minor — `attribution_populate` — the "Outputs" list omits `pcm_land(j,"urban")`, which M34 writes and M22/M35 read

**Doc** (`module_34.md:185-202`): the "Outputs (to other modules)" section lists exactly four items (`vm_land`, `vm_cost_urban`, `vm_carbon_stock`, `vm_bv`). `pcm_land` appears only as an aside under *Inputs* (`:179`).

**Reality in code.** `modules/34_urban/exo_nov21/preloop.gms:17` — `pcm_land(j,"urban") = i34_urban_area("y1995",j);` — overwrites the module-10 initialization (`modules/10_land/landmatrix_dec18/start.gms:11`; phase order start→preloop per `core/calculations.gms:13,15`). Two modules read that slice directly:

- `modules/22_land_conservation/area_based_apr22/presolve_ini.gms:83, 93, 104` — `- pcm_land(j, "urban")` in the secdforest / pasture / other restoration-potential calculations (default realization, `config/default.cfg:717`).
- `modules/35_natveg/pot_forest_may24/presolve.gms:64, 66` — `pcm_land(j,"urban")` in the denominator of `pc35_forest_recovery_shr` (default realization, `config/default.cfg:1156`).

This also resolves the doc's hedge "Module 22 (Conservation - **potentially**)" at `:318` — the consumption is confirmed, not speculative — and shows Module 35 is a consumer, not merely a land-competitor (`:467`).

*Tier note*: between Minor and Major (an omitted produced interface parameter is refactor-relevant); taken to the lower tier per the rubric tie-breaker because `:179` does surface the assignment.

**Proposed fix.** Add a fifth Outputs entry: "`pcm_land(j,"urban")` — populated in `preloop.gms:17` from `i34_urban_area("y1995",j)`, overriding M10's `f10_land` initialization. Read by M22 (restoration potential, `area_based_apr22/presolve_ini.gms:83,93,104`) and M35 (`pot_forest_may24/presolve.gms:64,66`); thereafter maintained by M10 (`landmatrix_dec18/postsolve.gms:9`)." Drop "potentially" at `:318` and add Module 35.

---

### BUG-5 — 🟡 Minor — `attribution_declare` — `pcm_land` attributed to "core initialization"; it is declared and initialized in Module 10

**Doc** (`module_34.md:515`):

> **All t**: vm_land.fx(j,"urban") = pcm_land(j,"urban") (fixed to the 1995 baseline; static reads pcm_land from **core initialization** and does not use M34's i34_urban_area parameter)

**Reality in code.** `pcm_land` is declared at `modules/10_land/landmatrix_dec18/declarations.gms:11` and initialized at `modules/10_land/landmatrix_dec18/start.gms:8,11` (`pm_land_start(j,land) = f10_land("y1995",j,land); pcm_land(j,land) = pm_land_start(j,land);`), then updated each timestep at `modules/10_land/landmatrix_dec18/postsolve.gms:9`. Nothing in `core/` assigns `pcm_land` (grep over `core/*.gms` returns no assignment). In MAgPIE, `core/` is a specific directory, so "core initialization" points a reader at the wrong file. The *substance* of the claim (1995 baseline, no `i34_urban_area`) is correct.

**Proposed fix.** `:515` → "static reads `pcm_land`, which Module 10 initializes from `f10_land("y1995",…)` (`modules/10_land/landmatrix_dec18/start.gms:8,11`) and updates in `postsolve.gms:9`; the static realization has no preloop and therefore never touches `i34_urban_area`."

---

### BUG-6 — 🟡 Minor — `other` — "Depends On: Module 09 (Drivers - LUH3 scenarios)" misattributes the LUH3 data to Module 09

**Doc** (`module_34.md:320`): `**Depends On**: Module 09 (Drivers - LUH3 scenarios)`.

**Reality in code.** Module 09 supplies exactly one thing to Module 34: the scalar `sm_fix_SSP2` (`modules/09_drivers/aug17/input.gms:22`, `/ 2025 /`), used at `exo_nov21/preloop.gms:10` to decide when the SSP2 freeze ends. The LUH3 urban trajectory is Module 34's own input table `f34_urbanland(t_all,j,urban_scen34)` (`exo_nov21/input.gms:16-19`), not something Module 09 provides. The parenthetical would send a reader to `09_drivers` looking for urban data.

**Proposed fix.** `:320` → `**Depends On**: Module 09 (`sm_fix_SSP2`, historical-freeze year); Module 44 (`fm_bii_coeff`); Module 10 (`fm_luh2_side_layers`, `pcm_land`). LUH3 urban data is M34's own input `f34_urbanland.cs3`.`

---

### BUG-7 — 🟡 Minor — `citation` — `presolve.gms` line ranges do not cover the statements they introduce

**Doc** `:254` — "**t>1 (optimization timesteps)** (`presolve.gms:12-14`)" then lists `.lo`, `.l` **and** `.up = Inf`.
**Doc** `:510` — "**exo_nov21** (`presolve.gms:11-14`)" then correctly cites "lines 13-14" and "line 15" in the body.

**Reality in code.** `modules/34_urban/exo_nov21/presolve.gms`: line 12 = `else`, 13 = `.lo = 0`, 14 = `.l = i34_urban_area`, 15 = `.up = Inf`. The cited ranges stop at 14 while the described content runs to 15.

**Proposed fix.** `:254` → `presolve.gms:12-15`; `:510` → `presolve.gms:10-16`.

---

### BUG-8 — 🟢 Informational — `other` — static-realization size metadata is off by ~65%

**Doc** `:6` "**Lines of Code**: ~217 (exo_nov21), ~40 (static)"; `:557` "**static structure** (4 files, ~40 lines)"; `:600` "Lines Documented: 217 (exo_nov21) + 40 (static)".

**Reality**: `wc -l` over `modules/34_urban/static/*.gms` = 66 (declarations 18, postsolve 14, presolve 14, realization 20), plus `not_used.txt`. `exo_nov21` = 220 across 9 `.gms` files, so "~217" is fine; "~40" is not.

**Proposed fix.** `:6`/`:557`/`:600` → "~220 (exo_nov21, 9 files), ~66 (static, 4 `.gms` files + `not_used.txt`)".

---

## 3. Deferred (not bugs — unverifiable or out of reach here)

1. `:386` "`i34_urban_area` monotonically increasing in all SSPs" — depends on `f34_urbanland.cs3`, which is gitignored/run-time generated (`exo_nov21/input/` contains only `files`). Cannot verify; the structural claim around it (`vm_land.lo = 0`, regional `=e=`) is correct.
2. `:163`/`:444` "Urban land has LOW BII coefficients" and "urban biodiversity value likely OVER-estimated" — `f44_bii_coeff.cs3` is not in the repo. Also note the internal tension: "all urban treated as equally low BII, but parks/gardens have moderate BII" argues for *under*-estimation, not over-. Judgment claim, not code-checkable.
3. `:55` "static … 1995 LUH2 baseline" vs `config/default.cfg:1145` which says "static urban land fixed on 1995 patterns from LUH3" — this exact discrepancy is the immutable R16 Minor anchor in `audit/flywheel_rubric.md` §1; the doc matches `static/realization.gms:9`. Not re-filed.
4. `:306` "Does NOT participate … Nitrogen" — `q50_nr_deposition(i2,land)` (`modules/50_nr_soil_budget/macceff_aug22/equations.gms:88-90`) *does* read `vm_land(j2,"urban")`, but `v50_nr_deposition` is consumed only for `"crop"` (`:32`) and `"past"` (`:80`), so the urban slice is computed-and-reported, never fed into the N budget. Doc claim stands; recorded here so a future auditor does not re-open it.
5. `:36` "Does NOT interact with other modules dynamically - only reduces available land pool" — faithfully restates `exo_nov21/realization.gms:12`, so not filed as a doc error. But two concrete couplings exist beyond the land pool and are absent from the whole doc: urban expansion carries a conversion cost of 12300 USD17MER/ha (`modules/39_landconversion/calib/presolve.gms:16` + `input.gms:13`, `config/default.cfg:1303`) applied via `q39_cost_landcon(j2,land)` (`calib/equations.gms:12-15`), and urban soil carbon scales with `vm_land(j,"urban")` (BUG-1). Module 39 reads `vm_landexpansion` (M10-populated), so it is a *transitive*, not direct, consumer — worth a sentence in the doc, not a bug record.
6. `:314` "**Centrality**: ~30 of 46 modules" — the metric's definition is not stated; cannot verify.
7. `:548` "60+ file:line citations" — actual `.gms:NN` occurrences = 55. Self-metadata, not a code claim.

---

## 4. Method notes

- Every attribution claim was checked against `audit/integrated/depth_rolemap.json` first, then confirmed by grepping **both** endpoints in code (`NAME(` and `NAME.`). No map/code disagreements arose.
- `rg -r` trap avoided after one hit: an early `rg -rn fm_luh2_side_layers …` silently rendered the match as `table n(j,luh2_side_layers10)` (`-r` = `--replace`). Re-run with `grep -n`, which gave the true line `modules/10_land/landmatrix_dec18/input.gms:19`.
- Absence claims (Module 59 not in the doc; no `pcm_land` assignment in `core/`) were each cross-checked with a second method and a positive control in the same directory.
