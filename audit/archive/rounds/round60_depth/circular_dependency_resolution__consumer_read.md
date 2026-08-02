# R60 depth audit — `cross_module/circular_dependency_resolution.md`

**Lens**: `consumer_read` — enter from the consumer side (presolve / postsolve / equation RHS), and for
every interface variable run a whole-tree grep of BOTH `NAME(` and `NAME.`; priority on READ/consumer
SET claims (phantoms *and* omissions) and on solution-level `.l` / `.lo` / `.up` reads.
**Ground truth**: MAgPIE `develop` read-only worktree (referred to below as `<develop>`), HEAD `2c02843ec`
("Merge pull request #919 from alexkoberle/dyn_reg_tau").
**Role map**: `audit/integrated/depth_rolemap.json` consulted FIRST for every
`vm_`/`pm_`/`im_`/`pcm_`/`fm_` attribution claim, then confirmed with a both-endpoints grep. Two
role-map entries proved to be extractor artifacts — see §5.
**magpie4** (for the R "Verification" recipes): pinned clone `.cache/sources/magpie4`, **version 2.76.4**.
**Date**: 2026-08-02

> **Provenance note.** A prior `consumer_read` report existed at this path from an earlier invocation of
> this round. I ran my own pass first and then **re-derived from code**, with my own commands, every
> prior finding I did not independently reach (marked ⟳ below). Nothing was inherited on the prior
> report's authority; four prior findings I could not confirm as stated are recorded in §4 with my
> reasoning. Findings unique to this pass are marked ★.

---

## 1. Scope

**Claims verified: 84.** The doc is 1041 lines, but much of it (§5 protocol, §6.2 / §7.2 / §9.1
hypothetical GAMS, §10 best-practice lists) is advisory rather than code-checkable. I checked every
concrete interface-variable attribution, every named equation and formula rendering, every `file:line`
and cross-doc citation, every named default/switch, both magpie4 R-recipe families, the `pcm_` appendix,
and both headline counts.

**Bugs: 26** — 2 Critical, 14 Major, 9 Minor, 1 Informational. All 26 carry a reproducible command with
its result.

### 1.1 What held up (verified correct — do NOT "fix" these)

| Claim | Result |
|---|---|
| `q10_land_area` reproduced verbatim (`:66-70`) | ✅ exact, `modules/10_land/landmatrix_dec18/equations.gms:13-15` |
| `pcm_land(j,land) = vm_land.l(j,land)` at `modules/10_land/landmatrix_dec18/postsolve.gms:9` | ✅ exact line |
| `pcm_carbon_stock(...) = vm_carbon_stock.l(...)` at `modules/56_ghg_policy/price_aug22/postsolve.gms:8` | ✅ exact line |
| `q52_emis_co2_actual` reads **both** `pcm_carbon_stock` and `vm_carbon_stock` (`:113-115`) | ✅ `modules/52_carbon/normal_dec17/equations.gms:16-19` |
| `:115-117` parenthetical — land-conversion costs are area-based (`q39_cost_landcon`), no carbon density | ✅ `modules/39_landconversion/calib/equations.gms:12-15` |
| `q14_yield_crop` scales the calibrated baseline by the **current** `vm_tau` (`equations.gms:14-16`); `q14_yield_past` uses the **lagged** `pcm_tau(j2,"crop")` (`:35-39`) — the `:251` prose | ✅ both exact, `modules/14_yields/managementcalib_aug19/` |
| `pcm_tau` updated at `modules/13_tc/endo_jan22/postsolve.gms:16` | ✅ `pcm_tau(j, tautype) = vm_tau.l(j, tautype);` |
| `q21_trade_glo` rendering (`:144-145`); `q21_trade_reg` / `q21_trade_reg_up` exist (`:146`) | ✅ `modules/21_trade/selfsuff_reduced/equations.gms:12-14, 31-42` |
| "`vm_import`/`vm_export` do NOT exist … `v21_trade` only in `selfsuff_reduced_bilateral22`" (`:151-153`) | ✅ `rg 'vm_import'` / `rg 'vm_export'` both rc=1 tree-wide; `v21_trade` declared only at `modules/21_trade/selfsuff_reduced_bilateral22/declarations.gms:23` |
| §2.2 return arrow **mechanism** (`:134-136`) — M21's trade equations constrain `vm_prod_reg` using `vm_supply` | ✅ `q21_trade_reg`/`_reg_up`/`_glo` all do exactly this; M17 itself never references `vm_supply` (rc=1), consistent with the arrow as drawn |
| `pc41_AEI_start(j)=vm_AEI.l(j)` in M41 postsolve (`:354`) | ✅ `modules/41_area_equipped_for_irrigation/endo_apr13/postsolve.gms:8` |
| `q41` inequality (`:351`) written flipped (`=g=`, operands swapped) but **mathematically identical** to `endo_apr13/equations.gms:10-11` | ✅ not a bug |
| `im_pollutant_prices(t_all,i,pollutants,emis_source)` domain + order (`:382`) | ✅ `modules/56_ghg_policy/price_aug22/declarations.gms:9` |
| `s56_buffer_aff` = 0.5, "half of removals credited" (`:411`) | ✅ `input.gms:71` `/ 0.5 /`, `config/default.cfg:1788`; `(1-s56_buffer_aff)` at `equations.gms:77` |
| `s56_c_price_induced_aff` is a 1/0 switch (`:412`) | ✅ `input.gms:69`, default `1` (`config/default.cfg:1762`) |
| `vm_carbon_stock(j,"forestry","vegc","actual")` is the right slice **in this chain** (`:390`) | ✅ M52 prices the `"actual"` stockType (`normal_dec17/equations.gms:19`); the `%c56_carbon_stock_pricing%` default `actualNoAcEst` applies only to M56's own pricing equation |
| `pm_land_conservation(t,j,land,consv_type)` domain, owned by M22 (`:292`) | ✅ `modules/22_land_conservation/area_based_apr22/declarations.gms:15` |
| `pm_yields_semi_calib(j,kve,w)` exists with that exact domain | ✅ `modules/14_yields/managementcalib_aug19/declarations.gms:19` |
| `vm_cost_landcon(j,land)` domain in the §6.2 hypothetical (`:600`) | ✅ `modules/39_landconversion/calib/declarations.gms:13` |
| "Module 54 (Phosphorus): 0 cycles, 1 connection" (`:586`) | ✅ M54 default realization is `off` (`config/default.cfg:1608`) |
| CONOPT / IPOPT / CPLEX all named (`:150`, `:831`, `:1012`) | ✅ **not a bug** — `modules/80_optimization/nlp_ipopt/solve.gms:13` (`option nlp = ipopt;`) and `cfg$gms$c80_nlp_solver <- "conopt4"` / `"conopt4+cplex"` (`config/default.cfg:2308-2312`). Only the default caveat is missing — see §4 |
| All eight named default realizations (10, 13, 14, 21, 35, 41, 52, 56) | ✅ match `config/default.cfg` |

---

## 2. Bugs

### 🔴 B01 (Critical) ★ — Fabricated manure → soil-fertility → yield feedback (the doc's flagship Cycle 1)

**Doc** `circular_dependency_resolution:239-245`, restated `:253`, `:268`, `:273`:
> ```
> vm_prod_reg(i2,kap) [70] → manure availability
>     ↓
>   (Manure affects soil fertility)
>     ↓
> pm_yields_semi_calib(j,kve,w) [14] → vm_prod(j,kcr) [17]
> ```
> `:253` "**Across timesteps**: Manure from livestock(t) affects yields(t+1)"
> `:268` "**Unrealistic intensification**: Manure contribution overestimated"
> `:273` "Limit manure impact on yields (Module 59, SOM)"

**Reality**: no manure → soil-fertility → yield pathway exists. Yields are closed-form —
`vm_yld = i14_yields_calib × vm_tau / fm_tau1995` (`modules/14_yields/managementcalib_aug19/equations.gms:14-16`)
and the pasture analogue at `:35-39` — with no nitrogen, SOM or manure term. Module 14's **complete**
interface-read set is `fm_aboveground_fraction, fm_carbon_density, fm_croparea, fm_ipcc_bef, fm_tau1995,
im_growing_stock, im_growing_stock_ysf, pcm_tau, pm_carbon_density_{other,plantation,secdforest}_ac,
pm_carbon_density_secdforest_ac_uncalib, pm_climate_class, pm_land_start, pm_past_mngmnt_factor,
pm_yields_semi_calib, vm_tau, vm_yld` — nothing from 50 / 55 / 59. Module 59 (default `cellpool_jan23`)
exports `vm_nr_som`, `vm_nr_som_fertilizer`, `vm_cost_scm` and the `soilc` slice of `vm_carbon_stock`;
none reach module 14. Manure enters the **soil-nitrogen budget** (M55 → M50), where it substitutes for
purchased fertilizer and therefore changes *cost*, never `vm_yld`. The one genuine livestock→yield
channel is `pm_past_mngmnt_factor` — declared `modules/70_livestock/fbask_jan16/declarations.gms:41`,
computed from **cattle numbers** at `modules/70_livestock/fbask_jan16/presolve.gms:64-67`, applied to
**pasture yields only** via `q14_yield_past`.

**Why Critical**: `:273` is an actionable instruction to edit module 59 for a coupling that is not there
("edit the wrong file"), and `:268` invites the conclusion that MAgPIE represents manure fertility
benefits ("build on a false foundation") — the parameterization-vs-mechanism trap AGENT.md flags.

**Propagation**: the same false claim is the third bullet of `core_docs/Module_Dependencies.md:194`
("Livestock provides manure affecting yields"). Fix both.

**Verify**
```
rg -no '\b(vm|pm|im|fm|pcm)_[a-zA-Z_0-9]*' modules/14_yields/managementcalib_aug19/*.gms \
  | sed 's/.*://' | sort -u            → the 16 names above; no manure/N/SOM interface
rg -n 'vm_nr_som|vm_manure|vm_nr_soil' modules/14_yields/                       → rc=1
rg -c 'vm_yld' modules/14_yields/managementcalib_aug19/equations.gms            → 2  (positive control)
```

**Fix**: delete the "manure availability / (Manure affects soil fertility)" links from `:236-246` and
substitute the real channel — `vm_prod_reg(i,kli_rum)` [70] → `p70_incr_cattle` →
`pm_past_mngmnt_factor(t,i)` (`modules/70_livestock/fbask_jan16/presolve.gms:64-67`) → `q14_yield_past`
(`modules/14_yields/managementcalib_aug19/equations.gms:35-39`), **pasture yields only**. Delete `:253`;
rewrite `:268` and `:273` (there is no manure→yield knob; the pasture-spillover knob is
`s14_yld_past_switch`). Also fix `core_docs/Module_Dependencies.md:194`.

---

### 🔴 B02 (Critical, tier-uncertain) ★ — Cycle 3 inverts the AEI bound: the previous timestep's AEI is a **lower** bound

**Doc** `circular_dependency_resolution:344` (with `:346`, `:367`, `:371`):
> "1. **Within timestep**: AEI capacity from **previous timestep** is **upper bound**"

**Reality**: it is a **lower** bound. `modules/41_area_equipped_for_irrigation/endo_apr13/presolve.gms:11`:
```gams
vm_AEI.lo(j) = pc41_AEI_start(j) / ((1 - s41_AEI_depreciation)**(m_timestep_length));
```
With the default `s41_AEI_depreciation = 0` (`endo_apr13/input.gms:11` `/ 0 /`, `config/default.cfg:1332`)
this is exactly last timestep's AEI — a **floor** (no disinvestment). **No `vm_AEI.up` is ever assigned**
in the default realization; a whole-tree `vm_AEI` grep finds `.up` only in postsolve output-writing.
Expansion above the previous level is unbounded and is disciplined by *cost*, inside the current
timestep, via `q41_cost_AEI` (`equations.gms:19-23`, charging
`(vm_AEI − pc41_AEI_start) × pc41_unitcost_AEI × annuity`); `q41_area_irrig` (`equations.gms:10-11`)
binds irrigated area to the **current** `vm_AEI`, not to `pc41_AEI_start`. The only realization that
pins AEI is the **non-default** `static` (`static/presolve.gms:9`, `vm_AEI.fx`).

The inversion propagates to `:346`, to `:367` ("Irrigation area jumps beyond capacity" — describes a cap
that does not exist) and to the remedy at `:371` ("Limit AEI expansion rate (Module 41 configuration)"),
which is unactionable: the only M41 knob, `s41_AEI_depreciation`, moves the **floor**.

*Tier note*: rated Critical by analogy to the rubric's "inverted Boolean default" trigger plus the
unactionable remedy; `tier_uncertainty: true` (a defensible Major).

**Verify**
```
rg -n 'vm_AEI' --glob '*.gms' .
→ the only .lo/.fx assignments are endo_apr13/presolve.gms:11 (.lo) and static/presolve.gms:9 (.fx);
  every .up hit is an ov_AEI output line in the two postsolve.gms R-sections
grep -n 's41_AEI_depreciation' config/default.cfg → 1332: cfg$gms$s41_AEI_depreciation <- 0  # def = 0
```

**Fix**: "Within timestep: the previous timestep's AEI, depreciated by `s41_AEI_depreciation`
(default 0), is a **lower** bound — `vm_AEI.lo`,
`modules/41_area_equipped_for_irrigation/endo_apr13/presolve.gms:11`. AEI is otherwise free to expand
**within the same timestep**, priced by `q41_cost_AEI` (`equations.gms:19-23`). The temporal element is
a ratchet, not a cap." Replace the `:371` remedy with "raise `f41_c_irrig` unit costs" or "raise
`s41_AEI_depreciation` (relaxes the floor)".

---

### 🟠 B03 (Major) ★ — `vm_prod(j,kcr) [17] → pm_yields_semi_calib [14]` is inverted; module 14 never reads `vm_prod`

**Doc** `:237`. **Reality**: module 14 contains **zero** references to `vm_prod`.
`pm_yields_semi_calib` is assigned exactly twice, both in **preloop**, both from the fixed 1995 slice —
`pm_yields_semi_calib(j,knbe14,w) = i14_yields_calib("y1995",j,knbe14,w);`
(`modules/14_yields/managementcalib_aug19/preloop.gms:116` and `:149`) — and is never updated again.
Its only cross-module reader is `modules/17_production/flexreg_apr16/presolve.gms:10`. The arrow runs
**14 → 17 only**. The doc already knows this: `:251` was patched in an earlier round to call the
calibrated baseline "a fixed parameter"; the diagram at `:236-246` was left stale and now contradicts it.

**Verify**
```
rg -n 'vm_prod' modules/14_yields/                                    → rc=1
rg -c 'vm_yld' modules/14_yields/managementcalib_aug19/equations.gms  → 2  (positive control)
rg -n 'pm_yields_semi_calib' --glob '*.gms' .  → 7 hits: 6 inside 14_yields, 1 at
                                                  modules/17_production/flexreg_apr16/presolve.gms:10
```

**Fix**: reverse the arrow and mark the parameter static —
`pm_yields_semi_calib(j,kve,w) [14, preloop-fixed at y1995] → pm_prod_init [17]
(modules/17_production/flexreg_apr16/presolve.gms:10)`. Remove the `[17] → [14]` direction.

---

### 🟠 B04 (Major) ⟳ — Cycle 4 attributes `vm_land(j,"crop")` to module 30; it is produced by module 29

**Doc** `:386` (and the `C4` catalog row `:743`, `32-30-10-35-56`).
**Reality**: `vm_land` is declared in module 10 (`landmatrix_dec18/declarations.gms:19`) and its
`"crop"` slice is **produced by module 29** — LHS of `q29_cropland`,
`modules/29_cropland/detail_apr24/equations.gms:12` (default per `config/default.cfg:814`), bounded by
`p29_avl_cropland` at `:23`. Module 30 (default `simple_apr24`, `config/default.cfg:915`) references
`vm_land(j2,"crop")` exactly once, on the **RHS** of one bioenergy-target constraint
(`modules/30_croparea/simple_apr24/equations.gms:23`). Module 30 owns `vm_area`, not `vm_land("crop")`.
Because 29 is the real node, the `C4` list omits it.

**Verify**
```
rg -n 'vm_land' modules/29_cropland/detail_apr24/*.gms  → 8 hits, LHS definition at equations.gms:12
rg -n 'vm_land' modules/30_croparea/simple_apr24/*.gms  → 1 hit, RHS at equations.gms:23
grep -nE 'gms\$(cropland|croparea)' config/default.cfg  → 814: detail_apr24 ; 915: simple_apr24
```

**Fix**: `vm_land(j,"crop") [29, q29_cropland]` at `:386`; update `:378` and `:743` to include 29.

---

### 🟠 B05 (Major) ⟳ — The natveg conservation constraint is tagged `[22, bounds]`; it is `q35_natveg_conservation` in module 35, and M22 has no equations at all

**Doc** `:302` (with `:288`, `:292`):
> `vm_land(j,land_natveg) ≥ pm_land_conservation(t,j,land_natveg,"protect")  [22, bounds]`

**Reality**: that inequality is verbatim `q35_natveg_conservation` in **module 35** —
`modules/35_natveg/pot_forest_may24/equations.gms:19-22`:
```gams
 q35_natveg_conservation(j2) ..
            sum(land_natveg, vm_land(j2,land_natveg))
            =g=
            sum((ct,land_natveg), pm_land_conservation(ct,j2,land_natveg,"protect"));
```
It is an **equation in the solve**, not a bound. The default M22 realization `area_based_apr22`
(`config/default.cfg:717`) **contains no `equations.gms`** — it is a parameter module
(`declarations, input, preloop, presolve_ini, realization, sets`) that fills `pm_land_conservation` in
`presolve_ini.gms:54-121`. The *per-pool* floors are separately imposed as `vm_land.lo` in **module 35's**
presolve (`:162` primforest, `:201` secdforest, `:231` other) and **module 31's**
(`modules/31_past/endo_jun13/presolve.gms:9`). Module 10 assigns no `vm_land.lo` anywhere — its only
occurrence is the output line `modules/10_land/landmatrix_dec18/postsolve.gms:52`.

**Verify**
```
ls modules/22_land_conservation/area_based_apr22/
→ declarations.gms input.gms preloop.gms presolve_ini.gms realization.gms sets.gms   (no equations.gms)
rg -n 'vm_land\.lo' --glob '*.gms' .
→ setters: 35_natveg/pot_forest_may24/presolve.gms:157,159,162,201,231 ; 31_past/endo_jun13/presolve.gms:9 ;
  34_urban/exo_nov21/presolve.gms:13.  22_land_conservation appears only as a READER
  (presolve_ini.gms:86,97,108) ; 10_land only in postsolve output
```

**Fix**: retag as `[q35_natveg_conservation, modules/35_natveg/pot_forest_may24/equations.gms:19-22]`
and add: "per-pool floors are `vm_land.lo` set in **M35** presolve (`:162/:201/:231`) and **M31**
presolve (`:9`); M22 has no equations and sets no bounds — it only computes `pm_land_conservation`."
This also makes Cycle 2's "Resolution Type: Simultaneous Equations" only half-right: the per-pool floors
are fixed **before** the solve (Type 3 by the doc's own taxonomy).

---

### 🟠 B06 (Major) ★ — Cycle 4 draws a serial `vm_emissions_reg [52] → vm_reward_cdr_aff [56]` hand-off; the branches are parallel

**Doc** `:392-394`. **Reality**: `vm_reward_cdr_aff` does not read `vm_emissions_reg` — not directly,
not transitively. `modules/56_ghg_policy/price_aug22/equations.gms:67-79`:
```gams
q56_reward_cdr_aff_reg(i2) .. vm_reward_cdr_aff(i2) =e= sum(cell(i2,j2), v56_reward_cdr_aff(j2));
q56_reward_cdr_aff(j2)     .. v56_reward_cdr_aff(j2) =e= … (1-s56_buffer_aff)*vm_cdr_aff(j2,ac,aff_effect)
                                                          * p56_c_price_aff(ct,i2,ac) … ;
```
The input is `vm_cdr_aff`, declared and populated in **module 32**
(`modules/32_forestry/dynamic_may24/declarations.gms:83`; `equations.gms:37,42`). `vm_emissions_reg`
feeds a **separate** branch: `q56_emis_pricing` / `q56_emis_pricing_co2` (`:15-22`) → `v56_emis_pricing`
→ `q56_emission_cost_annual`/`_oneoff` (`:29-52`) → `q56_emission_costs` (`:56-58`) →
`vm_emission_costs`. The two meet only in module 11's cost sum. Related: `:390-392` implies M56's carbon
accounting routes *through* M52; it does not — M56 reads `vm_carbon_stock` **directly** in
`q56_emis_pricing_co2` (`equations.gms:19-22`), in parallel with M52's `q52_emis_co2_actual`. This is the
R51 / MANDATE-21 pattern.

**Verify**
```
rg -n 'vm_emissions_reg' modules/56_ghg_policy/price_aug22/equations.gms  → only :17 (q56_emis_pricing)
rg -n 'vm_cdr_aff' --glob '*.gms' .
→ declared modules/32_forestry/dynamic_may24/declarations.gms:83 ; populated equations.gms:37,42 ;
  consumed only at modules/56_ghg_policy/price_aug22/equations.gms:77
```

**Fix**: split `:390-396` into two parallel branches from `vm_carbon_stock` / `vm_cdr_aff`.

---

### 🟠 B07 (Major) ⟳ — §2.1's diagram asserts two phantom edges: `Module 10 → Module 52`, and `Module 10` consuming `pcm_carbon_stock`

**Doc** `:95-99`. **Reality**: module 52 (default `normal_dec17`) references **no** module-10 interface;
its entire surface is `vm_emissions_reg` (populated), `vm_carbon_stock` and `pcm_carbon_stock` (read).
And `pcm_carbon_stock` is read only by 52, 56 and 59 — **module 10 never touches it**, so the upward
arrow into "Module 10 (Land)" is a phantom consumer edge. The real loop is transitive:
M10 `vm_land` → M29/31/32/34/35/59 (which populate `vm_carbon_stock`, declared in **M56**,
`price_aug22/declarations.gms:34`) → M52 reads it. A reader applying the doc's own §5.1 Method 1 would
find no 10↔52 edge.

**Verify** (two methods + positive control)
```
rg -n 'vm_land|pcm_land|vm_lu_transitions|vm_landexpansion|vm_landreduction|vm_landdiff|pm_land_start' \
   modules/52_carbon/                                                  → rc=1
grep -rl "vm_land" modules/52_carbon/                                  → rc=1
rg -c 'vm_carbon_stock' modules/52_carbon/normal_dec17/equations.gms   → 2   (positive control)
rg -n 'pcm_carbon_stock' --glob '*.gms' .   → 14 hits, all in modules 52, 56, 59 — none in 10
```

**Fix**: redraw as `M10 vm_land → {29,31,32,34,35,59} populate vm_carbon_stock (declared M56) →
M52 q52_emis_co2_actual reads pcm_carbon_stock(t−1) and vm_carbon_stock(t)`, and note that M10 does not
consume `pcm_carbon_stock`. Keep the (correct) Code Evidence block below the diagram.

---

### 🟠 B08 (Major) ★ — "All `pcm_*` variables are updated in `postsolve.gms`" is false, and the exceptions are load-bearing

**Doc** `:980` (Appendix A), restated at `:1017-1018`.
**Reality**: `pcm_*` is assigned in `start.gms`, `preloop.gms` and — critically — `presolve.gms`, in
default-active realizations:

| Site | What it does |
|---|---|
| `modules/10_land/landmatrix_dec18/start.gms:11` | `pcm_land(j,land) = pm_land_start(j,land);` |
| `modules/35_natveg/pot_forest_may24/presolve.gms:39` | `pcm_land(j,"primforest") = pcm_land(j,"primforest") - p35_disturbance_loss_primf(t,j);` — **mutates the lagged state mid-timestep** |
| `modules/35_natveg/pot_forest_may24/presolve.gms:131,137` | rebuilds `pcm_land(j,"secdforest")` / `(j,"other")` from age-class pools |
| `modules/32_forestry/dynamic_may24/presolve.gms:101,102` | `pcm_land(j,"forestry")`, `pcm_land_forestry(j,type32)` from `v32_land.l` |
| `modules/34_urban/exo_nov21/preloop.gms:17` | `pcm_land(j,"urban") = i34_urban_area("y1995",j);` |
| `modules/13_tc/endo_jan22/presolve.gms:77` | `pcm_tau(j,tautype) = vm_tau.l(j,tautype);` |
| `modules/56_ghg_policy/price_aug22/preloop.gms:10` | initialises `pcm_carbon_stock` from `fm_carbon_density × pcm_land` |
| `modules/59_som/cellpool_jan23/preloop.gms:30,33` | initialises the `soilc` slice |

This matters because `sum(land, pcm_land(j2,land))` is the RHS of `q10_land_area`: a reader who believes
`pcm_land` is written only in M10's postsolve will mis-trace the land balance and miss that M35 rewrites
the same-timestep RHS.

**Verify**
```
rg -n '^\s*pcm_[a-zA-Z_0-9]*\(.*=' --glob '*.gms' . | sed 's/:.*//' | sort | uniq -c | sort -rn
→ 3 35_natveg/pot_forest_may24/presolve.gms · 2 59_som/cellpool_jan23/preloop.gms
  2 32_forestry/dynamic_may24/presolve.gms · 1 each: 59/static_jan19/{preloop,postsolve},
  59/cellpool_jan23/postsolve, 56/price_aug22/{preloop,postsolve}, 34/exo_nov21/preloop,
  13/{exo,endo_jan22}/{presolve,postsolve}, 10/landmatrix_dec18/{start,postsolve}
```

**Fix**: "`pcm_*` is *primarily* refreshed in `postsolve.gms` from `vm_*.l`, **but not always**: several
modules initialise it (`start.gms`/`preloop.gms`) and some **rewrite it in `presolve.gms`** — notably
`modules/35_natveg/pot_forest_may24/presolve.gms:39,131,137` and
`modules/32_forestry/dynamic_may24/presolve.gms:101-102`. Grep both `postsolve.gms` and `presolve.gms`
before assuming a `pcm_` value is frozen for the solve." Mirror the caveat at `:1017-1018`.

---

### 🟠 B09 (Major) ★ — Appendix A `pcm_carbon_stock` row: wrong declared domain, and the module-59 update site is missing

**Doc** `:976`:
> `| pcm_carbon_stock(j,land,ag_pools,stockType) | 56_ghg_policy | Previous carbon stocks | modules/56_ghg_policy/price_aug22/postsolve.gms:8 |`

**Reality**: declared over `c_pools`, not `ag_pools` —
`modules/56_ghg_policy/price_aug22/declarations.gms:19`:
```gams
pcm_carbon_stock(j,land,c_pools,stockType)   Carbon stock in vegetation soil and litter …
```
`ag_pools` is only the slice **module 56 owns**. The `soilc` slice is updated by the default SOM
realization (`cfg$gms$som <- "cellpool_jan23"`, `config/default.cfg:1937`) at
`modules/59_som/cellpool_jan23/postsolve.gms:13`; both modules also initialise their slice in preloop
(`56/preloop.gms:10`; `59/cellpool_jan23/preloop.gms:30,33`). A reader taking the row at face value
misses half the variable — the per-slice-ownership failure the G2 anchor guards.

**Verify**
```
rg -n 'pcm_carbon_stock' --glob '*.gms' .  → 14 hits across 52, 56 and both 59 realizations
grep -n 'gms\$som' config/default.cfg      → 1937: cfg$gms$som <- "cellpool_jan23"  # def = cellpool_jan23
```

**Fix**: `| pcm_carbon_stock(j,land,c_pools,stockType) | declared 56_ghg_policy | ag_pools slice:
modules/56_ghg_policy/price_aug22/postsolve.gms:8 · soilc slice:
modules/59_som/cellpool_jan23/postsolve.gms:13 |`. While editing, complete the table — there are exactly
**four** `pcm_*` parameters (`pcm_land`, `pcm_land_forestry`, `pcm_tau`, `pcm_carbon_stock`);
`pcm_land_forestry` (module 32, `dynamic_may24/presolve.gms:102`) is currently hidden behind the `…` row.

---

### 🟠 B10 (Major) ★ — The Type-4 "Code Evidence" points at the wrong file *and* the wrong mechanism

**Doc** `:216-221`:
> ```gams
> * Module 14, preloop.gms:
> * Iterative calibration of tau factors
> * Multiple model runs required for full calibration
> ```

**Reality**: `modules/14_yields/managementcalib_aug19/preloop.gms` performs a **closed-form, single-pass**
calibration of *yields* to historical FAO levels — `i14_lambda_yields` (`:85-101`), `i14_managementcalib`
(`:110`), `i14_yields_calib` (`:115`). No loop over runs, no tau; the only `tau` token in the file is
`fm_tau1995` at `:11-12`, rescaling bioenergy yields. The real multi-run iterative calibration is the R
driver `scripts/calibration/calc_calib.R` (0 occurrences of "tau" — it calibrates area/land-conversion
factors from a pre-run), gated by `cfg$recalibrate`, whose **default is FALSE**
(`config/default.cfg:70`), with `cfg$calib_accuracy = 0.05` / `cfg$calib_maxiter = 20`
(`config/default.cfg:72,74`). `vm_tau` itself is an **endogenous decision variable** of module 13
(`modules/13_tc/endo_jan22/declarations.gms:13`), not a calibrated parameter. The doc also never states
that the whole Type-4 mechanism is off by default.

**Verify**
```
rg -n 'tau' modules/14_yields/managementcalib_aug19/preloop.gms  → only :11,:12 (fm_tau1995)
grep -c 'tau' scripts/calibration/calc_calib.R                   → 0
grep -nE 'recalibrate|calib_accuracy|calib_maxiter' config/default.cfg
→ 70: cfg$recalibrate <- FALSE   72: cfg$calib_accuracy <- 0.05   74: cfg$calib_maxiter <- 20
```

**Fix**: cite `scripts/calibration/calc_calib.R` + `config/default.cfg:70,72,74`, state that
`cfg$recalibrate` defaults to FALSE (a default run does **not** iterate), and note `vm_tau` is
endogenous. Update `:214` and `:223-225` to match.

---

### 🟠 B11 (Major) ⟳ — Under the default croparea realization, module 30 does not consume `vm_AEI` at all

**Doc** `:336`: `vm_AEI(j) [41] → constraint on vm_area(j,kcr,"irrigated") [30]`.
**Reality**: the default croparea realization is `simple_apr24` (`config/default.cfg:915`), which
declares `vm_AEI` explicitly unused — `modules/30_croparea/simple_apr24/not_used.txt:2` reads literally
`vm_AEI,input,questionnaire`. The only M30 reference is in the **non-default** `detail_apr24`, and it is
a rotation over-specialisation term, not a capacity constraint
(`modules/30_croparea/detail_apr24/equations.gms:82`). The constraint that actually couples them is
`q41_area_irrig` in **module 41** (`endo_apr13/equations.gms:10-11`).

**Verify**
```
rg -n 'vm_AEI' modules/30_croparea/
→ detail_apr24/equations.gms:82  and  simple_apr24/not_used.txt:2
rg -c 'vm_area' modules/30_croparea/simple_apr24/equations.gms → 10   (positive control)
```

**Fix**: "`vm_AEI(j)` [41] caps irrigated area through **`q41_area_irrig` in module 41**
(`endo_apr13/equations.gms:10-11`). Under the default `simple_apr24` croparea realization module 30 does
not read `vm_AEI` (`not_used.txt`); only the non-default `detail_apr24` uses it."

---

### 🟠 B12 (Major) ⟳ — `im_pollutant_prices` quoted in USD/tCO2; it is USD per **tC**

**Doc** `:410`: "`im_pollutant_prices`: Carbon price trajectory (0-1000 USD/tCO2)".
**Reality**: declared "Certificate prices for N2O-N CH4 CO2-C used in the model (**USD17MER per Mg**)"
(`modules/56_ghg_policy/price_aug22/declarations.gms:9`) — per Mg of the named species, i.e. per **tC**
for `co2_c`. The code states the conversion explicitly at
`modules/56_ghg_policy/price_aug22/preloop.gms:77`:
`*12/44 conversion from USD17MER per tC to USD17MER per tCO2`, used in the CH4/N2O caps at `:79-81`.
A reader treating a `co2_c` value of 300 as USD/tCO2 is off by 44/12 ≈ 3.67×.

**Verify**
```
sed -n '74,84p' modules/56_ghg_policy/price_aug22/preloop.gms
→ :77 "*12/44 conversion from USD17MER per tC to USD17MER per tCO2" ; :79-81 use 12/44 in the caps
```

**Fix**: "`im_pollutant_prices`: GHG certificate prices, **USD17MER per Mg of pollutant** — for `co2_c`
that is USD per **tC** (× 12/44 for USD/tCO2)." Drop the unsourced "0-1000" range or attribute it to a
named scenario file.

---

### 🟠 B13 (Major) ⟳ — "26 circular dependency cycles" is not reproducible, and §8.2 concedes 22 were guessed

**Doc** `:11`, echoed `:749` and `:1036`.
**Reality**: under the natural code definition (module A → B when A populates an interface B reads), the
dependency graph has **46 bidirectional module pairs (2-cycles) alone**, a single strongly connected
component of **31 modules**, plus a second SCC `{42, 43}`. The number of simple cycles in a 31-node SCC
exceeds 26 by many orders of magnitude. §8.2 itself labels the remaining 22 as "Inferred"/"Suspected"
and lists only six, i.e. the headline number was never derived — the NO-FIGURE-WITHOUT-AN-ARTIFACT class.

**Verify** (re-derived this session with my own script over `audit/integrated/depth_rolemap.json`,
edges = `populated_by × read_by`, `fm_*` excluded; Tarjan SCC):
```
modules in graph: 45
bidirectional module pairs (2-cycles): 46
SCC size 31 : 10,13,14,15,16,17,18,20,21,22,29,30,31,32,34,35,36,38,50,51,52,53,55,56,57,58,59,62,70,71,73
SCC size 2  : 42,43
```
*Caveat recorded honestly*: the role map is a realization-superset, so a default-config-only graph would
be somewhat smaller — but the M10/M29/M31/M32/M35 pairs are all default-realization pairs, so the count
stays far above 26.

**Fix**: replace the headline with something measured or qualitative — e.g. "MAgPIE's module dependency
graph is strongly connected across ~30 modules; this document treats **4 code-verified cycles** in detail
and lists further *candidate* cycles in §8.2 as unverified." If a number is wanted, generate it with a
named, committed script and cite the artifact.

---

### 🟠 B14 (Major) ⟳ — magpie4 verification recipes call functions that do not exist

**Doc** `:310` (`land_conservation(gdx, type="natveg")`) and `:361` (`AEI(gdx, level="cell")`).
**Reality**, magpie4 **2.76.4** (`.cache/sources/magpie4/DESCRIPTION:4`): neither symbol exists. The real
functions are `landConservation(gdx, file = NULL, level = "cell", cumuRestor = FALSE, baseyear = 1995,
annualRestor = FALSE, sum = FALSE)` (`R/landConservation.R:25`, `NAMESPACE:128`) and
`water_AEI(gdx, file = NULL, level = "reg")` (`R/water_AEI.R:18`, `NAMESPACE:305`).

**Verify**
```
ls .cache/sources/magpie4/R/land_conservation.R  → No such file
ls .cache/sources/magpie4/R/AEI.R                → No such file
grep -niE 'conserv|AEI' .cache/sources/magpie4/NAMESPACE
→ CostsAEI, disaggregateLandConservation, landConservation, reportAEI, reportLandConservation, water_AEI
```

**Fix**: `landConservation(gdx, level = "cell")` at `:310`; `water_AEI(gdx, level = "cell")` at `:361`.

---

### 🟠 B15 (Major) ⟳ — magpie4 recipes pass arguments those functions do not have

**Doc** `:309`, `:360`, `:421`. **Reality** (magpie4 2.76.4):
- `land <- memoise(function(gdx, file = NULL, level = "reg", types = NULL, subcategories = NULL, sum = FALSE))` — `R/land.R:29`. The argument is **`types`** (plural), and the documented options (`R/land.R:14-15`) are `"crop","past","forestry","primforest","secdforest","urban","other","primother","secdother"` — **`"natveg"` is not one**.
- `croparea <- memoise(function(gdx, file = NULL, level = "reg", products = "kcr", product_aggr = TRUE, water_aggr = TRUE))` — `R/croparea.R:27`. **No `irrigation` argument.**
- `costs <- function(gdx, file = NULL, level = "reg", type = "annuity", sum = TRUE)` — `R/costs.R:19`. **No `components` argument.**

(`yields(gdx, level = "cell", products = "kcr")` at `:259` is valid — `R/yields.R:26-32`.)

**Verify**
```
grep -n '^costs <- function\|croparea <- memoise\|^land <- memoise' .cache/sources/magpie4/R/*.R
→ R/costs.R:19 · R/croparea.R:27 · R/land.R:29   (signatures as quoted)
sed -n '14,15p' .cache/sources/magpie4/R/land.R  → types options list; no "natveg"
```

**Fix**: `:309` → `land(gdx, types = c("primforest","secdforest","other"), level = "cell")`;
`:360` → `croparea(gdx, level = "cell", water_aggr = FALSE)[, , "irrigated"]`;
`:421` → drop `components=` and select from `costs(gdx, level = "regglo", sum = FALSE)`.

---

### 🟠 B16 (Major) ★ — `Source: module_56.md (lines 60-79)` cites unrelated content

**Doc** `:414`, placed under the "Critical Parameters" block (`im_pollutant_prices`, `s56_buffer_aff`,
`s56_c_price_induced_aff`). **Reality**: `modules/module_56.md:60-79` is the **q56_emis_pricing (annual
emissions)** "What This Does / Components / Conceptual Meaning" block; it mentions none of the three.
Their actual locations: `s56_c_price_induced_aff` → `:40`; `s56_buffer_aff` → `:41`, `:287`, `:310`;
`im_pollutant_prices` → `:152`.

**Verify**
```
grep -n 's56_buffer_aff\|s56_c_price_induced_aff\|im_pollutant_prices' modules/module_56.md
→ 40, 41, 135, 152, 176, 257, 287, 310, 330…   (nothing in 60-79)
sed -n '58,82p' modules/module_56.md → the q56_emis_pricing Components block
```

**Fix**: `**Source**: modules/module_56.md:40-41 (switch table), :287/:310 (buffer semantics), :152
(im_pollutant_prices); cross_module/carbon_balance_conservation.md`.

---

### 🟡 B17 (Minor) ★ — `Source: Module_Dependencies.md (lines 149-179)` cites unrelated content

**Doc** `:745`. **Reality**: `core_docs/Module_Dependencies.md:149-179` is the Layer-4/5/6 architecture
listing plus §3.2 "Hub-and-Spoke Patterns". The four cycles are in §4.1 "Critical Feedback Cycles" at
`:184-215` ("26 circular dependencies identified, key cycles:" is `:186`). Rated Minor rather than Major
because it is a doc-to-doc pointer, easily recoverable by the reader.

**Verify**
```
sed -n '184,215p' core_docs/Module_Dependencies.md → §4.1, the four cycles
sed -n '145,183p' core_docs/Module_Dependencies.md → Layer 4/5/6 + §3.2; no cycles
```

**Fix**: `**Source**: core_docs/Module_Dependencies.md:184-215 (§4.1 Critical Feedback Cycles)`.

---

### 🟡 B18 (Minor) ★ — `vm_yields` is not a MAgPIE variable

**Doc** `:844`: `vars <- c("vm_land", "vm_prod", "vm_carbon_stock", "vm_yields", ...)`.
**Reality**: no `vm_yields` exists. The yield variable is `vm_yld(j,kve,w)`
(`modules/14_yields/managementcalib_aug19/equations.gms:15`); in a solved GDX it is `ov_yld`
(`.cache/sources/magpie4/R/yields.R:37`, `readGDX(gdx, "ov_yld")`). The other three names are real, which
is what makes the fabricated one credible.

**Verify**: `rg -n 'vm_yields' --glob '*.gms' .` → rc=1 (positive control:
`rg -c 'vm_yld' modules/14_yields/managementcalib_aug19/equations.gms` → 2).
**Fix**: `"vm_yld"` (note `readGDX` wants `"ov_yld"`).

---

### 🟡 B19 (Minor) ★ — §6.2 / §7.2 hypotheticals assert non-existent identifiers as "existing"

**Doc** `:593-594` (`pm_water_avail(j)` … "just uses **existing** `pm_water_avail`") and `:608`
(`pm_yields(j,kcr)`). **Reality**: neither exists. Module 43 (default `total_water_aug13`,
`config/default.cfg:1427`) exposes exactly two interfaces — `im_wat_avail` (in) and `vm_watdem` (out);
the yield parameter is `pm_yields_semi_calib` / the variable `vm_yld`. The blocks are labelled examples,
but the `:594` comment explicitly asserts existence.

**Verify**
```
rg -n 'pm_water_avail' --glob '*.gms' .   → rc=1
rg -n 'pm_yields\(' --glob '*.gms' .      → rc=1
rg -no '\b(vm|pm|im|fm)_[a-zA-Z_0-9]*' modules/43_water_availability/*/*.gms | sed 's/.*://' | sort -u
→ im_wat_avail, vm_watdem            (positive control: the search works in that dir)
```
**Fix**: use `im_wat_avail` and `pm_yields_semi_calib`, or relabel the blocks as pseudocode.

---

### 🟡 B20 (Minor) ★ — The `pcm_` naming gloss mis-parses the MAgPIE prefix convention

**Doc** `:60`: "(\"p\" = parameter, \"cm\" = current module)".
**Reality**: the split is `pc` + **scope**. The scope slot is `m` for *module-interface* (globally
visible) objects and the **module number** for module-local ones — proven by the module-local siblings
`pc13_tau`, `pc13_tcguess`, `pc29_treecover`, `pc32_land`, `pc35_secdforest`, `pc41_AEI_start`,
`pc44_bv_weighted`, `pc52_carbon_density_start`, `pc56_c_price_induced_aff`, `pc58_manLand`. So `m` means
*module interface / global* — close to the opposite of "current module". (The functional description,
"parameter from previous timestep", is correct.)

**Verify**: `rg -no '\bpc[0-9]{2}_[a-zA-Z_0-9]*' --glob '*.gms' . | sed 's/.*://' | sort -u`
→ 20 module-local `pc<NN>_` names across modules 13, 29, 32, 35, 41, 44, 52, 56, 58.
**Fix**: "`pcm_*` = parameter carrying state across timesteps, module-interface scope (`pc` = carried
parameter; `m` = visible to all modules — the module-local form is `pc<NN>_`, e.g. `pc41_AEI_start`)."

---

### 🟡 B21 (Minor) ★ — "`im_*` = Input data (exogenous, never changes)"

**Doc** `:62`. **Reality**: `im_` marks *exogenous to the optimization* + module-interface scope — not
time-invariant and not immutable. `im_growing_stock` / `im_growing_stock_ysf` are recomputed **every
timestep** in `modules/14_yields/managementcalib_aug19/presolve.gms:24-81`, and `im_pollutant_prices` is
rewritten 15 times in `modules/56_ghg_policy/price_aug22/preloop.gms:37-70`.

**Verify**
```
rg -n '^\s*im_' modules/14_yields/managementcalib_aug19/presolve.gms → :24,33,42,51,64,76,78,80,81
rg -n 'im_pollutant_prices.*=' modules/56_ghg_policy/price_aug22/preloop.gms | wc -l → 15
```
**Fix**: "`im_*` = **exogenous** module-interface parameter (never a decision variable). It *can* be
recomputed per timestep in `presolve.gms` — e.g. `im_growing_stock`."

---

### 🟡 B22 (Minor) ⟳ — §7.3 calls 41-42-43 a cycle-free, isolatable subsystem

**Doc** `:724`. **Reality**: M41 constrains `vm_area` (owned by M30) via `q41_area_irrig`
(`endo_apr13/equations.gms:10-11`), and the default M42 realization `all_sectors_aug13`
(`config/default.cfg:1340`) reads **`vm_area` and `vm_prod`** from the land/production core. The claim
also contradicts the same document's `C3` row (`:742`), which lists 30-41 as a cycle.

**Verify**
```
rg -no '\b(vm|pm|im|fm)_[a-zA-Z_0-9]*' modules/42_water_demand/all_sectors_aug13/*.gms \
  | sed 's/.*://' | sort -u
→ im_development_state, im_gdp_pc_mer, im_pop_iso, im_wat_avail, vm_area, vm_prod, vm_watdem, vm_water_cost
```
**Fix**: "42→43 is the only clean acyclic pair; 41 and 42 both consume `vm_area`/`vm_prod` from the
land-use core, so the water modules cannot be isolated."

---

### 🟡 B23 (Minor) ★ — Catalog row `C10 | 14-13-12 | Yields-TC-Interest` is not a cycle

**Doc** `:758`. **Reality**: module 12 (default `select_apr20`, `config/default.cfg:240`) touches exactly
three interfaces — `im_development_state`, `im_pop_iso` (in) and `pm_interest` (out). It reads nothing
from 13 or 14, so it is a **pure source** and cannot close a cycle. (§8.2 is hedged as "Inferred" /
"Suspected", hence Minor rather than Major — but the row is checkable and wrong.)

**Verify**: `rg -no '\b(vm|pm|im|fm|pcm)_[a-zA-Z_0-9]*' modules/12_interest_rate/*/*.gms | sed 's/.*://' | sort -u`
→ `im_development_state, im_pop_iso, pm_interest`.
**Fix**: drop C10, or restate as `14-13` with 12 shown as a one-way input.

---

### 🟡 B24 (Minor) ⟳ — `q17_prod_reg` written over `kall`; the equation is defined over `k`

**Doc** `:143`. **Reality**: `q17_prod_reg(i2,k) .. vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k));`
(`modules/17_production/flexreg_apr16/equations.gms:10-11`; declared `q17_prod_reg(i,k)` at
`declarations.gms:14`). `vm_prod` is declared **only** over `(j,k)` (`declarations.gms:9`), so
`vm_prod(j,kall)` is not a legal reference. `vm_prod_reg` *is* declared over `(i,kall)`
(`declarations.gms:10`) — the `:133` label is fine — but its non-`k` slices are populated elsewhere,
e.g. `modules/20_processing/substitution_may21/equations.gms:41`
(`vm_prod_reg(i2,"cottn_pro") =e= …`, default realization per `config/default.cfg:636`). Writing `kall`
in the equation hides that per-slice ownership.

**Verify**
```
grep -n 'vm_prod' modules/17_production/flexreg_apr16/declarations.gms → 9: vm_prod(j,k) · 10: vm_prod_reg(i,kall)
rg -n 'vm_prod_reg' modules/20_processing/substitution_may21/equations.gms → :41, :62, :120
```
**Fix**: `vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k))  [q17_prod_reg]`, with a note that the
other `kall` slices are set by M18 / M20 / M21.

---

### 🟡 B25 (Minor) ⟳ — `vm_prod(kli)` attributed to module 70; module 70 contains no `vm_prod(` reference

**Doc** `:204-206`. **Reality**: module 70 works exclusively at regional level with `vm_prod_reg(i2,kap)`
/ `(i2,kli)` (`modules/70_livestock/fbask_jan16/equations.gms:18,28,36,60,65,70`). Cluster-level
`vm_prod(j,kli_rum)` / `(j,kli_mon)` is populated by **71_disagg_lvst** (default `foragebased_jul23`,
`config/default.cfg:2221`).

**Verify**: `rg -n 'vm_prod\(' modules/70_livestock/` → rc=1 (positive control:
`rg -c 'vm_prod_reg' modules/70_livestock/fbask_jan16/equations.gms` → 6).
**Fix**: `vm_prod_reg(i,kli)` under Module 70; if cluster level is meant, tag it `vm_prod(j,kli) [71]`.

---

### 🟡 B26 (Informational) ⟳ — the postsolve snippet uses the equation alias `j2` where the code uses `j`

**Doc** `:73`: `pcm_land(j2,land) = vm_land.l(j2,land);`
**Reality**: `pcm_land(j,land) = vm_land.l(j,land);`
(`modules/10_land/landmatrix_dec18/postsolve.gms:9`). `j2` is the alias used *inside* equations; the
doc's own Appendix A cites the same line correctly. The block is presented as verbatim postsolve code.

**Verify**: `sed -n '9p' modules/10_land/landmatrix_dec18/postsolve.gms`.
**Fix**: use `j`.

---

## 3. Deferred (not filed — unverifiable or definitionally ambiguous)

- `:584` "Modifying Module 10 (Land): EXTREME RISK (4+ cycles, **15 consumers**)". Traces to
  `core_docs/Module_Dependencies.md:180` ("10_land: 15 out, 2 in"), so it is internally consistent, but
  not code-reproducible: readers of `vm_land` alone = 10 external modules; the union over all eight
  module-10 interfaces = **18** (11,13,14,22,29,30,31,32,34,35,39,44,50,56,58,59,71,80). No convention I
  tried yields 15. Needs a stated counting rule before it can be called wrong.
- `:150`, `:831`, `:1012` CONOPT / IPOPT / CPLEX — **not a bug**; all three are reachable
  (`modules/80_optimization/nlp_ipopt/solve.gms:13`; `config/default.cfg:2308-2312`). Missing only the
  default caveat (`cfg$gms$optimization <- "nlp_apr17"`, `config/default.cfg:2303`, conopt4). Optional polish.
- §2.2's "`vm_supply/trade`" label (`:136`). The arrow's *mechanism* is correct (M21's trade equations
  constrain `vm_prod_reg` using `vm_supply`), but the diagram never says `vm_supply` originates in
  **16_demand** (`modules/16_demand/sector_may15/equations.gms:20,32,41,52,62`; default per
  `config/default.cfg:611`). That is an omission, not an assertion — clarity note only.
- §8.2 rows C5-C9 not exhaustively checked (only C10 was); the table is explicitly hedged.
- §5.3 Test 3 (`gdx$status$solve_status`, `:559-565`) and §9.1's damping/`tau_factor` snippets are
  illustrative pseudocode; not checked against the `gdx`/`gdx2` R API.
- `:41-51` and `:1004` timestep schematics not checked against `cfg$gms$c_timesteps` / `main.gms`.
- All §9 symptom thresholds, `:263` / `:427-428` / `:541` numeric gates: heuristics with no code
  counterpart.

## 4. Prior-report claims I could NOT confirm as stated

Recorded so they are not silently re-inherited:

1. Prior B10 read §2.2's return arrow as "routes `vm_supply` from module 21 back to **module 17**". On my
   reading of the ASCII the `↑` sits under `vm_prod_reg`, so the arrow returns to the *variable*, which is
   exactly what `q21_trade_reg`/`_up`/`_glo` do. I did not file it as a phantom edge; the surviving,
   weaker point (ownership of `vm_supply`) is in §3 above.
2. Prior B7's suggested replacement `costs(gdx, level="regglo", sum=FALSE)["reward_cdr_aff"]` — I did not
   verify that the `reward_cdr_aff` component is exposed under that name by `costs()`; my fix for B15
   deliberately stops at "drop `components=`".
3. Prior B12 cited `vm_yld` at `modules/14_yields/managementcalib_aug19/declarations.gms:27`; the
   declaration I read this session is at a different line, so I cite `equations.gms:15` instead.
4. Prior §3 stated `s14_yld_past_switch = 0.25` at `config/default.cfg:369`. I did not re-verify that
   value and do not rely on it anywhere above.

## 5. Role-map notes (for the map maintainer)

Two entries in `audit/integrated/depth_rolemap.json` are **inequality-constraint artifacts** — the
extractor appears to treat any equation LHS as "populate", which is wrong for `=l=` / `=g=`:

- `vm_area.populated_by` includes `41`, but module 41's only `vm_area` occurrence is the LHS of the
  inequality `q41_area_irrig` (`modules/41_area_equipped_for_irrigation/endo_apr13/equations.gms:10-11`);
  module 41 does not produce `vm_area`.
- `vm_AEI.read_by` includes `30`, but under the **default** croparea realization it does not
  (`modules/30_croparea/simple_apr24/not_used.txt:2`). The map is realization-agnostic — fine as a
  superset, but consumers must re-check against `config/default.cfg`.

Both were caught by the both-endpoints grep, as designed; noted so the same near-misses do not become
false positives in a future round.

## 6. Pattern for the flywheel

B04, B05, B06, B07, B25 are one failure mode: **ASCII arrow diagrams drawn from topic ownership rather
than from the interface graph**. Carbon → M52, cropland → M30, conservation → M22, CDR → downstream of
M52, livestock production → M70 — all five are the module that conceptually owns the *topic*, and all
five are wrong about who declares, populates or reads the *variable*. A cross-module doc's diagrams
should be treated as a distinct, high-yield verification target: check every arrow against
`audit/integrated/depth_rolemap.json` plus a both-endpoints grep, not just the prose around them.
