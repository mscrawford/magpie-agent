# R60 depth audit — `modules/module_34.md` — lens: `consumer_read`

**Target doc**: `modules/module_34.md` (609 lines)
**Ground truth**: MAgPIE `develop` read-only worktree @ `2c02843ec` ("Merge pull request #919 from alexkoberle/dyn_reg_tau")
**Default realization confirmed**: `config/default.cfg:1147` → `cfg$gms$urban <- "exo_nov21"` ✓ (doc:10-11 correct)
**Role map consulted**: `audit/integrated/depth_rolemap.json` for `vm_land`, `vm_cost_urban`, `vm_carbon_stock`, `vm_bv`, `pcm_land`, `fm_bii_coeff`, `fm_luh2_side_layers` — every direction confirmed with a both-endpoints grep (`NAME(` **and** `NAME.`).

**Claims verified**: 61
**Bugs found**: 10 (2 Critical, 4 Major, 4 Minor)

---

## What the doc gets RIGHT (verified, not re-flagged)

To bound the false-positive surface, these were checked and confirmed:

- All 5 equation formulas are byte-accurate against `modules/34_urban/exo_nov21/equations.gms:17-18, 20-21, 25-26, 30-31, 34-35`. Equation count 5/0 (exo_nov21/static) ✓ (`declarations.gms:18-24`).
- `s34_urban_deviation_cost = 1e6 USD17MER/ha` ✓ (`modules/34_urban/exo_nov21/input.gms:13`).
- `c34_urban_scenario` default `SSP2`, options SSP1-5 ✓ (`input.gms:8-9`, `sets.gms:9-10`, `config/default.cfg:1150`).
- `vm_cost_urban(j)` → **Module 11 only** ✓ — `modules/11_costs/default/equations.gms:45`; whole-tree grep of `vm_cost_urban` returns no other consumer. Doc:114/284/471 correct.
- `vm_bv(j,"urban",potnatveg)` → **Module 44 only** ✓ — `modules/44_biodiversity/bii_target/equations.gms:16` (default realization, `config/default.cfg:1438`) plus a solution-level read at `bii_target/presolve.gms:16` (`vm_bv.l`). Doc:292/472 correct.
- `vm_carbon_stock` **declared in Module 56, not Module 52** ✓ — `modules/56_ghg_policy/price_aug22/declarations.gms:34`. Doc:288 correct, and the doc's *parallel-not-serial* framing ("Both read `vm_carbon_stock`") correctly avoids the R51 hand-off trap.
- `vm_land.fx / .lo / .l / .up` bound logic ✓ (`exo_nov21/presolve.gms:10-15`); static fixations ✓ (`static/presolve.gms:9,10,12,14`).
- Scaling: `vm_cost_urban.scale(j) = 1e3` ✓ (`scaling.gms:8`); `v34_cost1/2` scale lines commented out ✓ (`scaling.gms:9-10`).
- "Eliminate 5 equations and 2 variables; `vm_cost_urban` persists, fixed to 0" ✓ (`static/declarations.gms:9-11`, `static/presolve.gms:14`).
- Module 58 (peatland) correctly **omitted**: `manPeat58 / crop, past, forestry /` (`modules/58_peatland/v2/sets.gms:16-17`) excludes urban.
- Module 71 correctly **omitted**: `modules/71_disagg_lvst/foragebased_jul23/preloop.gms:9` reads `pm_land_start(j,"urban")`, which is populated by Module 10 from `f10_land` (`modules/10_land/landmatrix_dec18/start.gms:8`) — **not** from M34's `f34_urbanland`. Not an M34 consumer.
- Doc:55 "static … 1995 LUH2 baseline" matches `static/realization.gms:8-9`; the LUH2-vs-LUH3 tension is the **immutable R16 Minor anchor** in `audit/flywheel_rubric.md` §1 and is deliberately not re-flagged.

---

## BUGS

### BUG-1 — 🔴 Critical — `formula` — Urban carbon stocks are NOT zero; only the **above-ground** pools are

**doc_line**: `module_34.md:198` (same error at `:28`, `:33`, `:59`, `:289`, `:304`, `:361`, `:363`, `:366`, `:473`, `:474`)

**Claim in doc** (`:196-198`):
> `vm_carbon_stock(j,"urban",ag_pools,stockType)` — urban carbon stocks … **Fixed to zero** (no urban carbon density data) (`presolve.gms:8`)

and (`:304`):
> **Carbon Balance**: ⚠️ **LIMITATION** — Urban land carbon set to **ZERO** (no data for urban vegetation).

and (`:473-474`):
> Receives `vm_carbon_stock(j,"urban",*) = 0` …

**Reality in code**: `ag_pools` is a **proper subset** of `c_pools`:
`ag_pools(c_pools) Above ground carbon pools / vegc, litc /` — `modules/56_ghg_policy/price_aug22/sets.gms:209-210`
`c_pools Carbon pools /vegc,litc,soilc/` — `core/sets.gms:324-325`

So `modules/34_urban/exo_nov21/presolve.gms:8` zeroes **only `vegc` and `litc`**. The **`soilc`** pool for urban land is left free and is populated by **Module 59** (default realization `cellpool_jan23`, `config/default.cfg:1937`):

- `noncropland59(land) /past, forestry, primforest, secdforest, other, urban/` — `modules/59_som/cellpool_jan23/sets.gms:10-11` (**urban is a member**)
- `q59_som_target_noncropland(j2,noncropland59) .. v59_som_target(j2,noncropland59) =e= vm_land(j2,noncropland59) * sum(ct,f59_topsoilc_density(ct,j2))` — `modules/59_som/cellpool_jan23/equations.gms:31-34`
- `q59_carbon_soil(j2,land,stockType) .. vm_carbon_stock(j2,land,"soilc",stockType) =e= v59_som_pool(j2,land) + vm_land(j2,land) * sum(ct,i59_subsoilc_density(ct,j2))` — `modules/59_som/cellpool_jan23/equations.gms:61-64` (unconditioned over **all** `land`, urban included)
- Initialization: `vm_carbon_stock.l(j,noncropland59,"soilc",stockType) = pcm_carbon_stock(...)` where `pcm_carbon_stock(j,noncropland59,"soilc",stockType) = fm_carbon_density("y1995",j,noncropland59,"soilc") * pm_land_start(j,noncropland59)` — `modules/59_som/cellpool_jan23/preloop.gms:33-35`

And the "no data" premise is **explicitly handled elsewhere**, not by zeroing — Module 52 assigns urban the natural-land soil carbon density:
```
* Fix urban area soilc to natural land soilc as long as preprocessed
* fm_carbon_density does not provide meaningful numbers for urban.
fm_carbon_density(t_all,j,"urban","soilc") = fm_carbon_density(t_all,j,"other","soilc")
```
— `modules/52_carbon/normal_dec17/input.gms:33-35`

Urban soil carbon is therefore **structurally non-zero** (it is the natural-reference topsoil+subsoil density × urban area), and it **does** reach emission accounting: `urban_soilc` is a member of `emis_oneoff` (`core/sets.gms:314-318`) and of `emis_land` (`core/sets.gms:350`), which is the summation set of `q52_emis_co2_actual` (`modules/52_carbon/normal_dec17/equations.gms:16-19`) and `q56_emis_pricing_co2` (`modules/56_ghg_policy/price_aug22/equations.gms:19-22`). Conversion of forest/other land → urban therefore produces a **real, priced CO2 flux** through the soil pool, and the doc's "urban contributes zero to carbon balance" is false.

**Consequence**: doc:366 ("Carbon emissions from land conversion to urban UNDER-estimated") inverts the actual design, and doc:363's "soil carbon under pavement" is listed as missing when it is in fact modelled at natural-land density. Anyone auditing MAgPIE's land-conversion CO2 or building an urban-greening extension would start from a false foundation.

**verify_cmd**:
```
sed -n '209,210p' modules/56_ghg_policy/price_aug22/sets.gms
  -> ag_pools(c_pools) Above ground carbon pools
     / vegc, litc /
sed -n '10,11p' modules/59_som/cellpool_jan23/sets.gms
  -> noncropland59(land) Soil carbon conserving landuse types
     /past, forestry, primforest, secdforest, other, urban/
sed -n '33,35p' modules/52_carbon/normal_dec17/input.gms
  -> fm_carbon_density(t_all,j,"urban","soilc") = fm_carbon_density(t_all,j,"other","soilc")
sed -n '314,318p' core/sets.gms
  -> emis_oneoff(...) / ... urban_vegc, urban_litc, urban_soilc, ... /
grep -n 'cfg$gms$som' config/default.cfg
  -> 1937:cfg$gms$som <- "cellpool_jan23"    # def = cellpool_jan23
```
Cross-check (second method + positive control): whole-tree `rg -n '"urban"' modules/ core/ --glob '*.gms'` returns exactly two `vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0;` sites (`34_urban/exo_nov21/presolve.gms:8`, `34_urban/static/presolve.gms:10`) and **no** site zeroing the urban `soilc` slice; positive control — the same grep does return the known-present `vm_bv(j2,"urban",…)` and `pcm_land(j,"urban")` tokens, proving the search reaches those directories.

**confirmed**: true

**proposed_fix**: Replace "urban carbon stocks fixed to zero" with the pool-resolved statement everywhere it appears (`:28`, `:33`, `:59`, `:196-198`, `:288-290`, `:304`, `:359-368`, `:473-474`):
> `modules/34_urban/exo_nov21/presolve.gms:8` fixes only the **above-ground** pools to zero — `ag_pools = {vegc, litc}` (`modules/56_ghg_policy/price_aug22/sets.gms:209-210`). Urban **soil** carbon (`soilc`) is NOT zero: it is computed by Module 59 (`q59_carbon_soil`, `modules/59_som/cellpool_jan23/equations.gms:61-64`; urban ∈ `noncropland59`, `sets.gms:10-11`) at the natural-land soil carbon density that Module 52 assigns explicitly (`modules/52_carbon/normal_dec17/input.gms:33-35`). `urban_soilc` is in `emis_oneoff`/`emis_land` (`core/sets.gms:318, 350`), so conversion to/from urban land generates real CO2 in `q52_emis_co2_actual` and priced CO2 in `q56_emis_pricing_co2`.

Rewrite Limitation §2 (`:359-368`): the limitation is "no urban-specific **vegetation/litter** carbon (above-ground assumed zero) and no urban-specific **soil** parameterization (urban soil is proxied by natural 'other' land)" — not "urban carbon is zero", and **not** "conversion emissions under-estimated" (the soil term is fully counted).

---

### BUG-2 — 🔴 Critical — `attribution_read` — Consumer set of `vm_land(j,"urban")` omits Modules 59 and 50

**doc_line**: `module_34.md:187-189` (and `:280`, `:318`, `:463`)

**Claim in doc** (`:187-189`):
> `vm_land(j,"urban")` — urban land area by cell — **To: Module 10 (Land)** for land balance constraint

`:318` **Provides To**: Module 10, Module 11, Module 22 (potentially), Module 44. `:315` **Total Connections: 3-4**.

**Reality in code**: three modules read the urban slice of `vm_land` in **active equations** (not just M10):

| Module | Site | How urban enters |
|---|---|---|
| 10 | `modules/10_land/landmatrix_dec18/equations.gms:13-15, 19-25` | `sum(land, vm_land(j2,land))`, `vm_land(j2,land_to)`; `land` ∋ urban (`core/sets.gms:250-251`). Also `postsolve.gms:9` `pcm_land(j,land) = vm_land.l(j,land)` |
| **59** | `modules/59_som/cellpool_jan23/equations.gms:31-34` and `:61-64` | `vm_land(j2,noncropland59)` with urban ∈ `noncropland59`; `vm_land(j2,land)` over all land. Plus a solution-level read `pc59_land_before(j,land) = vm_land.l(j,land)` at `cellpool_jan23/postsolve.gms:9` |
| **50** | `modules/50_nr_soil_budget/macceff_aug22/equations.gms:88-90` | `q50_nr_deposition(i2,land) .. v50_nr_deposition(i2,land) =e= sum((ct,cell(i2,j2)), i50_atmospheric_deposition_rates(ct,j2,land) * vm_land(j2,land))` — `land` ∋ urban |

Module 59's read is the load-bearing one: it is what turns urban land area into urban soil carbon (BUG-1). Module 59 is entirely absent from the doc — from "Downstream Modules" (`:278-294`), "Provides To" (`:318`), and "Related Modules" (`:459-474`).

Module 50's urban slice **is** computed but is inert downstream (`v50_nr_deposition` is consumed only for `"crop"` at `equations.gms:32` and `"past"` at `:80`), so the doc's "does not participate in the Nitrogen law" (`:306`) stands — but the *read* exists and belongs in the consumer list.

The `:318` "Provides To" list is additionally **self-inconsistent**: it drops Modules 52 and 56, which the doc itself names as `vm_carbon_stock` consumers 30 lines earlier at `:288` and at `:473-474`. "Total Connections: 3-4" (`:315`) undercounts a verified reader set of at least eight ({10, 11, 22, 35, 44, 50, 52, 56, 59}).

**verify_cmd**:
```
rg -n 'vm_land[(.]' modules/ core/ | grep -v '^modules/34_urban'
  -> modules/59_som/cellpool_jan23/equations.gms:33:  =e= vm_land(j2,noncropland59) * sum(ct,f59_topsoilc_density(ct,j2))
  -> modules/59_som/cellpool_jan23/equations.gms:63:  =e= v59_som_pool(j2, land) + vm_land(j2, land) *
  -> modules/59_som/cellpool_jan23/postsolve.gms:9:pc59_land_before(j,land) = vm_land.l(j,land);
  -> modules/50_nr_soil_budget/macceff_aug22/equations.gms:90: ... * vm_land(j2,land));
  -> modules/10_land/landmatrix_dec18/equations.gms:14,21  (+ postsolve.gms:9, start.gms:12)
sed -n '250,251p' core/sets.gms
  -> land Land pools / crop, past, forestry, primforest, secdforest, urban, other /
```
Both `NAME(` and `NAME.` forms were grepped (the `.l` reads in `10_land/postsolve.gms:9` and `59_som/.../postsolve.gms:9` are invisible to a `vm_land(` grep). Role-map cross-check: `vm_land.read_by = [10, 22, 29, 30, 31, 32, 34, 35, 50, 58, 59]`; of these, 29/30/31/32/35 index only non-urban literals (`"crop"`, `"past"`, `"forestry"`, `land_snv`, `land_forest`, `land_natveg`), 22 indexes only `vm_land.lo(j,"crop")`, and 58 restricts to `manPeat58 = {crop, past, forestry}` — so **59 and 50 are the only additions**, and 29/30/31/32/35/58 are correctly excluded (guards against an over-broad "omitted consumer" claim).

**confirmed**: true

**proposed_fix**: In `:185-203` ("Outputs"), `:278-294` ("Downstream Modules") and `:318` ("Provides To"), list the verified consumers of `vm_land(j,"urban")` as **Module 10** (`modules/10_land/landmatrix_dec18/equations.gms:13-15, 19-25`), **Module 59** (`modules/59_som/cellpool_jan23/equations.gms:31-34, 61-64` — urban ∈ `noncropland59`; this is what generates urban soil carbon) and **Module 50** (`modules/50_nr_soil_budget/macceff_aug22/equations.gms:88-90` — atmospheric N deposition is computed for urban land but the urban slice of `v50_nr_deposition` is not consumed by any budget equation, so it is inert). Make "Provides To" (`:318`) agree with "Downstream Modules" by re-adding 52 and 56, and replace "Total Connections: 3-4" (`:315`) with the enumerated set.

---

### BUG-3 — 🟠 Major — `set_membership` — M52/M56 read `c_pools`, not `ag_pools`; and M56's default `stockType` is `actualNoAcEst`

**doc_line**: `module_34.md:288`

**Claim in doc**:
> **Module 52 (Carbon)** and **Module 56 (GHG Policy)**: Both read `vm_carbon_stock(j,"urban",ag_pools,stockType)` (the urban slice, fixed to 0).

**Reality in code**: neither reader uses `ag_pools`. `ag_pools` is the index set of M34's **fix**, not of anyone's **read**:
- `q52_emis_co2_actual`: `vm_carbon_stock(j2,land,c_pools,"actual")` — `modules/52_carbon/normal_dec17/equations.gms:19` — `c_pools = {vegc, litc, soilc}` (`core/sets.gms:324-325`), `stockType` pinned to the literal `"actual"`.
- `q56_emis_pricing_co2`: `vm_carbon_stock(j2,land,c_pools,"%c56_carbon_stock_pricing%")` — `modules/56_ghg_policy/price_aug22/equations.gms:22` — default `c56_carbon_stock_pricing = actualNoAcEst` (`modules/56_ghg_policy/price_aug22/input.gms:90`; `config/default.cfg:1838`), **not** `"actual"` and not a free `stockType` index.

This is the precise index-set error that makes the doc's "(the urban slice, fixed to 0)" parenthetical false (see BUG-1): the readers reach `soilc`, which M34 never fixes.

**verify_cmd**:
```
sed -n '16,19p' modules/52_carbon/normal_dec17/equations.gms
  -> ... sum((cell(i2,j2),emis_land(emis_oneoff,land,c_pools)),
         (pcm_carbon_stock(j2,land,c_pools,"actual") - vm_carbon_stock(j2,land,c_pools,"actual"))/m_timestep_length);
sed -n '19,22p' modules/56_ghg_policy/price_aug22/equations.gms
  -> ... vm_carbon_stock(j2,land,c_pools,"%c56_carbon_stock_pricing%") ...
grep -n 'c56_carbon_stock_pricing' modules/56_ghg_policy/price_aug22/input.gms
  -> 90:$setglobal c56_carbon_stock_pricing  actualNoAcEst
grep -n 'c56_carbon_stock_pricing <-' config/default.cfg
  -> 1838:c56_carbon_stock_pricing <- "actualNoAcEst"   # def = actualNoAcEst
```

**confirmed**: true

**proposed_fix**: `:288` → "Both read `vm_carbon_stock(j,"urban",c_pools,·)` over the **full** pool set `c_pools = {vegc, litc, soilc}` (`core/sets.gms:324-325`), of which only `{vegc, litc}` (`ag_pools`) is fixed to 0 by `modules/34_urban/exo_nov21/presolve.gms:8`. M52 reads `stockType = "actual"` (`modules/52_carbon/normal_dec17/equations.gms:19`); M56 reads `stockType = %c56_carbon_stock_pricing%`, default `actualNoAcEst` (`modules/56_ghg_policy/price_aug22/input.gms:90`)."

---

### BUG-4 — 🟠 Major — `attribution_read` — "Upstream Modules: None" is false and self-contradicted

**doc_line**: `module_34.md:276`

**Claim in doc**:
> ### Upstream Modules (provide data to Module 34)
> **None** - Module 34 is a data provider, reads only from external input files (LUH3)

**Reality in code**: `modules/34_urban/exo_nov21/` reads four interface objects owned by three other modules:

| Object | Owner (declared in) | Read by M34 at |
|---|---|---|
| `sm_fix_SSP2` | Module 09 — `modules/09_drivers/aug17/input.gms:22` (`/ 2025 /`) | `exo_nov21/preloop.gms:10` |
| `fm_bii_coeff` | Module 44 — `modules/44_biodiversity/bii_target/input.gms:17` | `exo_nov21/equations.gms:35`, `preloop.gms:21` |
| `fm_luh2_side_layers` | Module 10 — role map `declared_in: 10_land` | `exo_nov21/equations.gms:35`, `preloop.gms:21` |
| `pcm_land`, `vm_land` | Module 10 — `modules/10_land/landmatrix_dec18/declarations.gms:11, 19` | `exo_nov21/preloop.gms:17, 20-21`; `equations.gms:18,21,31,35`; `presolve.gms:11-15` |

The doc contradicts itself 44 lines later at `:320` ("**Depends On**: Module 09 (Drivers - LUH3 scenarios)"), and that line's parenthetical is also wrong: what M34 takes from Module 09 is the scalar `sm_fix_SSP2`, not "LUH3 scenarios" (LUH3 comes from M34's own `f34_urbanland.cs3`).

The `static` realization's own `not_used.txt` corroborates: it declares **only** `sm_fix_SSP2` as unused, confirming `pcm_land`, `vm_land`, `vm_bv`, `vm_carbon_stock`, `fm_bii_coeff` and `fm_luh2_side_layers` are used inputs.

**verify_cmd**:
```
grep -n 'sm_fix_SSP2' modules/09_drivers/aug17/input.gms
  -> 22:  sm_fix_SSP2  year until which all parameters are fixed to SSP2 values (year) / 2025 /
grep -n 'fm_bii_coeff' modules/44_biodiversity/*/input.gms
  -> modules/44_biodiversity/bv_btc_mar21/input.gms:15:table fm_bii_coeff(bii_class44,potnatveg) ...
  -> modules/44_biodiversity/bii_target/input.gms:17:table fm_bii_coeff(bii_class44,potnatveg) ...
cat modules/34_urban/static/not_used.txt
  -> name,type,reason
     sm_fix_SSP2, input, not needed
```

**confirmed**: true

**proposed_fix**: `:274-276` → replace "None" with:
> **Module 09 (Drivers)**: `sm_fix_SSP2` (`modules/09_drivers/aug17/input.gms:22`, default 2025) — the year until which all SSP scenarios are frozen to SSP2 (`exo_nov21/preloop.gms:10`).
> **Module 10 (Land)**: `pcm_land`, `vm_land`, `fm_luh2_side_layers` (`modules/10_land/landmatrix_dec18/declarations.gms:11, 19`).
> **Module 44 (Biodiversity)**: `fm_bii_coeff` (`modules/44_biodiversity/bii_target/input.gms:17`).
> Cellular urban areas themselves come from M34's own input file `f34_urbanland.cs3` (`exo_nov21/input.gms:16-19`), not from another module.

Fix `:320` to say "Module 09 (Drivers — `sm_fix_SSP2` historical-freeze year), Module 10 (Land), Module 44 (Biodiversity)".

---

### BUG-5 — 🟠 Major — `attribution_read` — `pcm_land(j,"urban")` is an M34 **output**; Modules 22 and 35 read it

**doc_line**: `module_34.md:179` (placement), `:318` (hedge), `:185-203` (omission)

**Claim in doc**: `:179` lists, under the heading "### Inputs (from other modules/external)":
> Initialization: `pcm_land(j,"urban") = i34_urban_area("y1995",j)` (`preloop.gms:17`)

and `:318` hedges the consumer as "Module 22 (Conservation - **potentially**)".

**Reality in code**: `exo_nov21/preloop.gms:17` is a **write** to a Module-10-owned parameter (role map: `pcm_land.declared_in = 10_land`, `populated_by = [10, 32, 34, 35]`), so it belongs under **Outputs**, not Inputs. Phase order confirms M34's write lands *after* Module 10's initialization and therefore overrides it for the urban slice: `core/calculations.gms:13` (`start`) → `:15` (`preloop`), with `modules/10_land/landmatrix_dec18/start.gms:11` `pcm_land(j,land) = pm_land_start(j,land);` running first.

Two modules read that urban slice directly — the doc's "potentially" is an unnecessary hedge on a confirmed dependency, and Module 35 is missing entirely:

- **Module 22**: `modules/22_land_conservation/area_based_apr22/presolve_ini.gms:83, 93, 104` — `- pcm_land(j, "urban")` subtracted when computing `p22_secdforest_restore_pot`, `p22_past_restore_pot`, `p22_other_restore_pot`. Urban area directly caps restoration potential.
- **Module 35**: `modules/35_natveg/pot_forest_may24/presolve.gms:64, 66` — `(sum(land_ag, pcm_land(j,land_ag)) + pcm_land(j,"urban"))` is the denominator of `pc35_forest_recovery_shr`, which scales forest-recovery allocation.

**verify_cmd**:
```
rg -n '"urban"' modules/ core/ --glob '*.gms'
  -> modules/22_land_conservation/area_based_apr22/presolve_ini.gms:83:  - pcm_land(j, "urban")
  -> modules/22_land_conservation/area_based_apr22/presolve_ini.gms:93:  - pcm_land(j, "urban")
  -> modules/22_land_conservation/area_based_apr22/presolve_ini.gms:104: - pcm_land(j, "urban")
  -> modules/35_natveg/pot_forest_may24/presolve.gms:64,66: ... + pcm_land(j,"urban") ...
  -> modules/34_urban/exo_nov21/preloop.gms:17:pcm_land(j,"urban") = i34_urban_area("y1995",j);
rg -n 'include.gms' core/calculations.gms
  -> 13:$batinclude "./modules/include.gms" start
     15:$batinclude "./modules/include.gms" preloop
```
(Positive control for the same grep: it also returns the known-present `modules/34_urban/static/presolve.gms:9` and `modules/39_landconversion/calib/presolve.gms:16`, proving the search reaches both directories.)

**confirmed**: true

**proposed_fix**: Move the `pcm_land(j,"urban")` line from "Inputs" (`:179`) into "Outputs (to other modules)" (`:185-203`) as a 5th entry:
> **`pcm_land(j,"urban")`** — initialized by M34 at `exo_nov21/preloop.gms:17` from `i34_urban_area("y1995",j)`, overriding Module 10's `start.gms:11` value for the urban slice (phase order `start` → `preloop`, `core/calculations.gms:13,15`); refreshed each timestep by `modules/10_land/landmatrix_dec18/postsolve.gms:9`. Read by **Module 22** (`area_based_apr22/presolve_ini.gms:83, 93, 104` — caps restoration potential), **Module 35** (`pot_forest_may24/presolve.gms:64, 66` — denominator of `pc35_forest_recovery_shr`) and Module 10.

At `:318`, drop the "potentially" hedge on Module 22 and add Module 35.

---

### BUG-6 — 🟠 Major — `mechanism` — "only reduces available land pool" omits the 12 300 USD17MER/ha urban establishment cost

**doc_line**: `module_34.md:36` (and `:341`)

**Claim in doc**:
> 5. **Does NOT interact with other modules dynamically** - only reduces available land pool

and `:341` "only affects land availability and total costs".

**Reality in code**: urban land expansion carries a land-conversion establishment cost charged in the objective, independent of `vm_cost_urban`:
- `q39_cost_landcon(j2,land) .. vm_cost_landcon(j2,land) =e= (vm_landexpansion(j2,land)*sum((ct,cell(i2,j2)), i39_cost_establish(ct,i2,land)) - …) * annuity` — `modules/39_landconversion/calib/equations.gms:12-15`, indexed over **all** `land` (urban included).
- `i39_cost_establish(t,i,"urban") = s39_cost_establish_urban;` — `modules/39_landconversion/calib/presolve.gms:16`
- `s39_cost_establish_urban … / 12300 /` — `modules/39_landconversion/calib/input.gms:13`; `config/default.cfg:1303` `cfg$gms$s39_cost_establish_urban <- 12300`
- Default realization `calib` — `config/default.cfg:1288`.

Per MANDATE 17 this is a **transitive** (two-hop) link — M39 reads `vm_landexpansion`, which Module 10 derives from `vm_lu_transitions` (`modules/10_land/landmatrix_dec18/equations.gms:30-33`) — so M39 must **not** be listed as a direct consumer of `vm_land(j,"urban")`. But the doc's blanket "only reduces available land pool" is wrong: urban expansion also (a) costs 12 300 USD17MER/ha in M39, (b) emits soil CO2 through M59→M52/M56 (BUG-1), (c) caps restoration potential in M22 and forest recovery in M35 (BUG-5).

Note the source's own `@limitations` comment says the same thing (`modules/34_urban/exo_nov21/realization.gms:12`), so the fix is to annotate the quote, not silently delete it.

**verify_cmd**:
```
cat -n modules/39_landconversion/calib/equations.gms
  -> 12: q39_cost_landcon(j2,land) .. vm_cost_landcon(j2,land) =e=
     13:   (vm_landexpansion(j2,land)*sum((ct,cell(i2,j2)), i39_cost_establish(ct,i2,land))
grep -n 's39_cost_establish_urban' modules/39_landconversion/
  -> calib/input.gms:13: s39_cost_establish_urban  Cost for urban land expansion (USD17MER per hectare) / 12300 /
  -> calib/presolve.gms:16:i39_cost_establish(t,i,"urban") = s39_cost_establish_urban;
grep -n 'cfg$gms$landconversion' config/default.cfg
  -> 1288:cfg$gms$landconversion <- "calib"           # def = calib
```

**confirmed**: true

**proposed_fix**: `:36` → "**Does NOT model endogenous urbanization dynamics** — MAgPIE-internal drivers cannot alter the trajectory. (The realization's own `@limitations` at `exo_nov21/realization.gms:12` says urban land 'does not interact with other model dynamics, except for reducing available non-urban land pool'; that is narrower than the code. Urban land *area* additionally drives: land-conversion establishment cost of 12 300 USD17MER/ha via `q39_cost_landcon` (`modules/39_landconversion/calib/equations.gms:12-15`, `presolve.gms:16`, `input.gms:13` — reached transitively through `vm_landexpansion` from Module 10), soil-carbon CO2 via Module 59 → M52/M56, restoration-potential caps in Module 22, and biodiversity value in Module 44.)" Apply the same correction at `:341`.

---

### BUG-7 — 🟡 Minor — `attribution_populate` — `pcm_land` is initialized by Module 10, not by "core"

**doc_line**: `module_34.md:515`

**Claim in doc**:
> **All t**: `vm_land.fx(j,"urban") = pcm_land(j,"urban")` (fixed to the 1995 baseline; static reads `pcm_land` from **core initialization** and does not use M34's `i34_urban_area` parameter)

**Reality in code**: `pcm_land` is declared and initialized by **Module 10**, not by `core/`:
- `pcm_land(j,land)` declared at `modules/10_land/landmatrix_dec18/declarations.gms:11`
- `pm_land_start(j,land) = f10_land("y1995",j,land);` then `pcm_land(j,land) = pm_land_start(j,land);` — `modules/10_land/landmatrix_dec18/start.gms:8, 11`
- refreshed each timestep at `modules/10_land/landmatrix_dec18/postsolve.gms:9`

Grep of `core/` for `pcm_land` returns nothing (positive control: the same grep of `modules/10_land/` returns 6 hits), so "core initialization" is a wrong producer attribution. The rest of the sentence ("does not use M34's `i34_urban_area`") is correct — `static` has no `preloop` phase (`static/realization.gms:16-20`).

**verify_cmd**:
```
rg -n 'pcm_land' modules/10_land/landmatrix_dec18/ core/
  -> modules/10_land/landmatrix_dec18/declarations.gms:11: pcm_land(j,land) ...
  -> modules/10_land/landmatrix_dec18/start.gms:11:pcm_land(j,land) = pm_land_start(j,land);
  -> modules/10_land/landmatrix_dec18/postsolve.gms:9:pcm_land(j,land) = vm_land.l(j,land);
  (zero hits under core/ ; positive control = 6 hits under modules/10_land/)
```

**confirmed**: true

**proposed_fix**: `:515` → "…static reads `pcm_land`, which **Module 10** initializes from `f10_land("y1995",…)` (`modules/10_land/landmatrix_dec18/start.gms:8, 11`) and refreshes each timestep (`postsolve.gms:9`); `static` has no `preloop` phase (`static/realization.gms:16-20`) and therefore never applies M34's `i34_urban_area`."

---

### BUG-8 — 🟡 Minor — `mechanism` — "urban land cannot convert back" is not a code property

**doc_line**: `module_34.md:37` (mechanism restated at `:384-386`)

**Claim in doc**:
> 6. **Does NOT model urban-rural land transitions** - expansion is one-way (urban land cannot convert back)

with the stated mechanism at `:386`: "…`i34_urban_area` monotonically increasing in all SSPs".

**Reality in code**: nothing in the code forbids urban contraction.
- `vm_land.lo(j,"urban") = 0` and `vm_land.up(j,"urban") = Inf` for t>1 — `modules/34_urban/exo_nov21/presolve.gms:13, 15`.
- `q34_urban_land` is an **equality** to the prescribed regional total (`equations.gms:30-31`), so if the prescribed total falls, regional urban land falls with it.
- Module 10's transition matrix places no restriction on urban as a source: `q10_transition_from(j2,land_from) .. sum(land_to, vm_lu_transitions(j2,land_from,land_to)) =e= pcm_land(j2,land_from);` — `modules/10_land/landmatrix_dec18/equations.gms:23-25`, `land_from` ∋ urban; and `q10_landreduction(j2,land_from)` (`:35-38`) computes urban land reduction explicitly.

Whether urban land actually declines is therefore a **data** property of `f34_urbanland.cs3` — which is gitignored (`.gitignore:7` `*.cs*`) and absent from the worktree, so the doc's monotonicity premise is not verifiable here. What is verifiable is that the *mechanism* claim is wrong.

**verify_cmd**:
```
sed -n '13,15p' modules/34_urban/exo_nov21/presolve.gms
  -> vm_land.lo(j,"urban") = 0;
     vm_land.l(j,"urban") = i34_urban_area(t,j);
     vm_land.up(j,"urban") = Inf;
sed -n '23,38p' modules/10_land/landmatrix_dec18/equations.gms
  -> q10_transition_from(j2,land_from) .. sum(land_to, vm_lu_transitions(j2,land_from,land_to)) =e= pcm_land(j2,land_from);
     q10_landreduction(j2,land_from) .. vm_landreduction(j2,land_from) =e= sum(land_to$(not sameas(land_from,land_to)), vm_lu_transitions(j2,land_from,land_to));
git check-ignore -v modules/34_urban/exo_nov21/input/f34_urbanland.cs3
  -> .gitignore:7:*.cs*  modules/34_urban/exo_nov21/input/f34_urbanland.cs3
ls modules/34_urban/exo_nov21/input/
  -> files          (the .cs3 is a run-time product, absent from the repo)
```

**confirmed**: true (for the code-mechanism half; the data-monotonicity premise is unverifiable — see Deferred)

**proposed_fix**: `:37` → "**Does NOT model urban shrinkage endogenously** — urban land follows the prescribed trajectory in both directions. The code does *not* forbid contraction: `vm_land.lo(j,"urban") = 0` (`exo_nov21/presolve.gms:13`), `q34_urban_land` is an equality to the prescribed regional total (`equations.gms:30-31`), and Module 10 admits urban as a transition source (`modules/10_land/landmatrix_dec18/equations.gms:23-25, 35-38`). Whether urban land ever declines depends entirely on `f34_urbanland.cs3` (a run-time input, gitignored)." At `:386`, mark the monotonicity statement as an unverified data assumption rather than a fact.

---

### BUG-9 — 🟡 Minor — `citation` — bound-list citation range truncates the line it describes

**doc_line**: `module_34.md:254`

**Claim in doc**: "**t>1 (optimization timesteps)** (`presolve.gms:12-14`)" — followed by three bullets, the third of which is `vm_land.up(j,"urban") = Inf`.

**Reality in code**: the three assignments are at `exo_nov21/presolve.gms:13, 14, 15`; line 12 is the bare `else`. `up = Inf` sits at **line 15**, outside the cited range. (The doc gets this right at `:512`, which cites "line 15" — so `:254` is an internal inconsistency too.)

**verify_cmd**:
```
sed -n '10,16p' modules/34_urban/exo_nov21/presolve.gms
  -> 10 if(ord(t) = 1,
     11   vm_land.fx(j,"urban") = i34_urban_area(t,j);
     12 else
     13   vm_land.lo(j,"urban") = 0;
     14   vm_land.l(j,"urban") = i34_urban_area(t,j);
     15   vm_land.up(j,"urban") = Inf;
     16 );
```

**confirmed**: true

**proposed_fix**: `:254` → "(`presolve.gms:12-15`)".

---

### BUG-10 — 🟡 Minor — `other` — line-count figures drift from the code

**doc_line**: `module_34.md:6` (also `:552`, `:557`, `:600`)

**Claim in doc**: "**Lines of Code**: ~217 (exo_nov21), ~40 (static)"; `:552` "exo_nov21 structure (9 files, 217 lines)"; `:557` "static structure (4 files, ~40 lines)"; `:600` "Lines Documented: 217 (exo_nov21) + 40 (static)".

**Reality in code**: totalling the `.gms` files (the method that yields ~217 for exo_nov21) gives **220** and **66**. The file counts (9 and 4 `.gms` files) are correct.

**verify_cmd**:
```
wc -l modules/34_urban/exo_nov21/*.gms   -> 220 total   (9 files)
wc -l modules/34_urban/static/*.gms      ->  66 total   (4 files, + not_used.txt)
```

**confirmed**: true

**proposed_fix**: `:6`, `:552`, `:557`, `:600` → "220 (exo_nov21, 9 `.gms` files), 66 (static, 4 `.gms` files)", and state the counting method (total `.gms` lines including licence headers) so future re-measurement is reproducible.

---

## Deferred (not verifiable / insufficient evidence — no edit proposed)

1. `:386` "`i34_urban_area` monotonically increasing in all SSPs" — `f34_urbanland.cs3` is gitignored (`.gitignore:7`) and is a run-time product; only `input/files` is tracked. Data trajectory not checkable in this worktree. (The *code-mechanism* half is flagged as BUG-8.)
2. `:314` "Centrality: ~30 of 46 modules (moderate-low centrality)" — no defined metric or persisted artifact in the repo; cannot be re-derived, so no correct value can be proposed.
3. `:306` "Does NOT participate (Food, Water, **Nitrogen**)" — kept as correct: Module 50 *does* read `vm_land(j,"urban")` (`macceff_aug22/equations.gms:88-90`), but `v50_nr_deposition(i2,"urban")` feeds no budget equation (only `"crop"` at `:32` and `"past"` at `:80` are consumed), so the urban slice is inert in the nitrogen balance. Recorded in BUG-2 as a consumer-list addition only.
4. `:444` "Urban biodiversity value likely OVER-estimated" — depends on the numeric `fm_bii_coeff("urban",potnatveg)` values in Module 44's input table; input file not read.
5. `:525` "Reason for disabling: Likely caused solver issues (extreme rescaling)" — pure speculation about the commented `scaling.gms:9-10` lines; no code or history evidence either way.
6. `:3` "Status: ✅ Fully Verified", `:548` "60+ file:line citations", `:599` "Errors Found: 0", `:608` "Changes Since Last Verification: None (stable)" — doc metadata, not code-checkable. (BUG-1 through BUG-10 do falsify `:599` in substance.)
7. `modules/module_34_notes.md` does not exist, so no user-feedback layer was available to cross-check.

---

## Lens note

The `consumer_read` entry point paid off twice over. The doc's carbon claim survived every previous audit because it is *internally* consistent — `presolve.gms:8` really does say `= 0`. It only breaks when you enter from the consumer side and ask **what index set does the reader actually use**: M52/M56 read `c_pools`, M34 fixes `ag_pools`, and the gap between those two sets is exactly `soilc` — a pool that a third module (M59) fills for urban land and that a fourth (M52's own `input.gms:33-35`) deliberately parameterizes at natural-land density. Three of the four modules involved in falsifying "urban carbon = zero" (59, and the `ag_pools`/`c_pools` distinction in 56 and 52) are invisible from inside `modules/34_urban/`.
