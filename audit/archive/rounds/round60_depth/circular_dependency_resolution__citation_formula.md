# R60 depth audit — `cross_module/circular_dependency_resolution.md`

**Lens**: citation_formula (entry via file:line citations + equation-formula fidelity; all cross-module
attribution claims cross-checked against `audit/integrated/depth_rolemap.json` and re-confirmed with
both-endpoints greps in the develop worktree)
**Ground truth**: MAgPIE develop worktree @ `2c02843ec` ("Merge pull request #919 from alexkoberle/dyn_reg_tau")
**Claims verified**: 96
**Bugs**: 12 confirmed (10 Major, 2 Minor)

All paths below are repo-relative. GAMS paths are relative to the MAgPIE repo root in the develop
worktree; doc paths are relative to the magpie-agent repo root.

---

## What checked out clean (recorded so the next round does not re-derive)

| Claim (doc line) | Verdict |
|---|---|
| `modules/10_land/landmatrix_dec18/postsolve.gms:9` → `pcm_land(j,land) = vm_land.l(j,land);` (975) | ✅ exact |
| `modules/56_ghg_policy/price_aug22/postsolve.gms:8` → `pcm_carbon_stock(...) = vm_carbon_stock.l(...)` (110-111, 976) | ✅ exact |
| `modules/13_tc/endo_jan22/postsolve.gms:16` → `pcm_tau(j, tautype) = vm_tau.l(j, tautype);` (977) | ✅ exact |
| `q14_yield_crop` at `modules/14_yields/managementcalib_aug19/equations.gms:14-16`, scales `i14_yields_calib` by current-timestep `vm_tau` (251) | ✅ exact |
| `q14_yield_past` at `.../equations.gms:35-39` uses lagged `pcm_tau(j2,"crop")` (251) | ✅ exact |
| `q10_land_area(j2) .. sum(land,vm_land) =e= sum(land,pcm_land)` (65-69, 301) | ✅ `modules/10_land/landmatrix_dec18/equations.gms:13-15` |
| `q52_emis_co2_actual` reads `pcm_carbon_stock` **and** `vm_carbon_stock` (113-117) | ✅ `modules/52_carbon/normal_dec17/equations.gms:16-19` |
| Land-conversion costs are area-based, `q39_cost_landcon`, no carbon density (116-117) | ✅ `modules/39_landconversion/calib/equations.gms:12-15` |
| `q21_trade_glo` formula incl. balanceflow (144-145) | ✅ `modules/21_trade/selfsuff_reduced/equations.gms:12-14` |
| `vm_import`/`vm_export` do NOT exist; `v21_trade` only in `selfsuff_reduced_bilateral22` (151-153) | ✅ 0 hits tree-wide (positive control `vm_supply` → 5 files) |
| `pc41_AEI_start(j) = vm_AEI.l(j);` in module 41 postsolve (354) | ✅ `modules/41_area_equipped_for_irrigation/endo_apr13/postsolve.gms:8` |
| `pm_land_conservation(t,j,land,consv_type)` dims + `"protect"` is a real `consv_type` member (292, 302) | ✅ `modules/22_land_conservation/area_based_apr22/declarations.gms:15`, `sets.gms:28-29` |
| `im_pollutant_prices(t_all,i,pollutants,emis_source)` dims (382) | ✅ `modules/56_ghg_policy/price_aug22/declarations.gms:9` |
| `s56_buffer_aff` default 0.5 = 50 % of removals credited (411) | ✅ `input.gms:71`, `config/default.cfg:1788`, used as `(1-s56_buffer_aff)` in `equations.gms:77` |
| `s56_c_price_induced_aff` default 1 (411-412) | ✅ `config/default.cfg:1762`, `preloop.gms:60` |
| All 11 realization names cited or implied (`landmatrix_dec18`, `endo_jan22`, `managementcalib_aug19`, `normal_dec17`, `price_aug22`, `selfsuff_reduced`, `selfsuff_reduced_bilateral22`, `endo_apr13`, `area_based_apr22`, `flexreg_apr16`, `nlp_apr17`) | ✅ exist and are the config defaults where claimed |
| `modification_safety_guide.md` §5.2 = "verify ALL 5 conservation laws" (629) | ✅ `cross_module/modification_safety_guide.md:659-661` |
| CONOPT / IPOPT / CPLEX all exist as solver options (150, 831, 1012) | ✅ `nlp_apr17` (default, conopt4), `nlp_ipopt`, `lp_nlp_apr17` — no bug, but the default-state caveat is absent |
| `land_natveg` = primforest + secdforest + other (284) | ✅ `core/sets.gms:262-263` |

---

## Bugs

### CDR-01 (Major, mechanism / data_flow_direction) — the canonical "Type 1" example cycle does not exist between the modules named

**Doc** `cross_module/circular_dependency_resolution.md:94-100`:
```
Module 10 (Land) ────────────→ Module 52 (Carbon)
       ↑                             │
       │                             ↓
  pcm_carbon_stock ←──── vm_carbon_stock
```
**Code**: module 10 contains **no carbon reference at all**, and module 52 references **neither `vm_land`
nor `pcm_land`**. `pcm_carbon_stock` is declared in 56 and consumed only by 52, 56, 59.
`vm_carbon_stock` is declared in 56, populated by 29/31/32/34/35/59, read by 52/56/59.
Neither arrow of the drawn cycle is a code edge: the land→carbon coupling runs *land modules →
`vm_carbon_stock` (declared in 56) → 52*, with 52 supplying carbon densities (`fm_carbon_density`,
`pm_carbon_density_*`) in the other direction.

**Verify**
- `rg -ni "carbon" modules/10_land/` → **exit 1, no output** (positive control: `rg -c "vm_land" modules/10_land/landmatrix_dec18/equations.gms` → `9`)
- `rg -n "vm_land|pcm_land" modules/52_carbon/` → **exit 1, no output** (positive control: `rg -n "vm_|pcm_" modules/52_carbon/normal_dec17/*.gms` → `equations.gms:17,19` only)
- `rg -ln "pcm_carbon_stock" modules/` → `52_carbon/normal_dec17/equations.gms`, `56_ghg_policy/price_aug22/{declarations,equations,postsolve,preloop}.gms`, `59_som/{cellpool_jan23,static_jan19}/{postsolve,preloop}.gms` — **module 10 absent**

**Fix**: redraw the example as `land modules (29/31/32/34/35/59) → vm_carbon_stock → 52 (q52_emis_co2_actual)
→ vm_emissions_reg → 56`, with `pcm_carbon_stock` (declared + updated in 56, `postsolve.gms:8`) as the
lag closing the loop back into 52/56/59. Module 10 owns `vm_land`/`pcm_land` and has no carbon interface;
if a 10↔carbon framing is wanted, say the land *pools* enter carbon stocks through the pool-owning
modules, not through module 10 itself.

---

### CDR-02 (Major, citation) — `module_56.md (lines 60-79)` points at a different section

**Doc** `circular_dependency_resolution.md:414`: "**Source**: module_56.md (lines 60-79), cross_module/carbon_balance_conservation.md"
— cited as the source for the *Critical Parameters* block (`im_pollutant_prices`, `s56_buffer_aff`,
`s56_c_price_induced_aff`).

**Reality**: `modules/module_56.md:60-79` is §2.1's "What This Does / Components" prose for
`q56_emis_pricing` plus the §2.2 heading — none of the three parameters appears there. They are at
`modules/module_56.md:40-41` (§1.3 *Critical Policy Levers*, with the correct defaults `1 (ON)` and
`0.5 (50%)`) and §6.2 *Key Scalars* (from line 689).

**Verify**: `grep -n "s56_buffer_aff\|s56_c_price_induced_aff" modules/module_56.md` → `40`, `41`, `257`, `287`, `310` (none in 60-79);
`awk 'NR>=55&&NR<=85' modules/module_56.md` → q56_emis_pricing components block.

**Fix**: cite `modules/module_56.md:40-41` (§1.3) for the three levers, and `module_56.md:287` for the
`s56_buffer_aff` semantics.

---

### CDR-03 (Major, citation) — `Module_Dependencies.md (lines 149-179)` points at the layer diagram, not the cycles

**Doc** `circular_dependency_resolution.md:745`: "**Source**: Module_Dependencies.md (lines 149-179)"
— attached to the §8.1 table of core cycles C1-C4.

**Reality**: `core_docs/Module_Dependencies.md:149-179` is the Layer 4-6 architecture diagram plus
§3.2 *Hub-and-Spoke Patterns*. The C1-C4 cycles are §4/§4.1 at lines **182-217**.

**Verify**: `awk 'NR>=140&&NR<=185' core_docs/Module_Dependencies.md` → layer diagram + hubs; line 182 = "### 4. Circular Dependencies (Feedback Loops)", 184 = "#### 4.1 Critical Feedback Cycles", 188-216 = the four cycles.

**Fix**: change to `Module_Dependencies.md:182-217`.

---

### CDR-04 (Major, set_membership) — `q17_prod_reg` written over `kall`; the equation is over `k`

**Doc** `circular_dependency_resolution.md:144` (and the diagram at :133):
`vm_prod_reg(i,kall) = sum(cell(i,j), vm_prod(j,kall))               [q17_prod_reg]`

**Code**: `modules/17_production/flexreg_apr16/equations.gms:10-11`
```gams
q17_prod_reg(i2,k) ..
vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k));
```
`vm_prod` is declared `(j,k)` (`declarations.gms:9`); `vm_prod_reg` is declared `(i,kall)`
(`declarations.gms:10`) — the *variable* spans `kall`, the *equation* only `k`. `kall \ k` =
oils, oilcakes, sugar, molasses, alcohol, ethanol, distillers_grain, brans, scp, fibres,
res_cereals, res_fibrous, res_nonfibrous. Those slices are set elsewhere: module 20
(`q20_processing`, `modules/20_processing/substitution_may21/equations.gms:59-62`) and module 18
(residues). `vm_prod(j,kall)` as written is a domain violation.

**Verify**: `awk` of `modules/17_production/flexreg_apr16/equations.gms` (15 lines total) → only
`q17_prod_reg(i2,k)`; `rg -n "k\(kall\)" --glob "*.gms" .` → `modules/14_yields/*/sets.gms:12  k(kall) Primary products`
(28 members, no secondary products); `core/sets.gms:228-235` = `kall` (41 members).

**Fix**: `vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k))   [q17_prod_reg, modules/17_production/flexreg_apr16/equations.gms:10-11]`,
with a one-line note that the `kall \ k` slices of `vm_prod_reg` are populated by modules 18, 20 and 21.
*(tier note: Minor↔Major boundary; kept at Major because the mis-set changes which module produces which commodity.)*

---

### CDR-05 (Major, mechanism) — AEI: previous-timestep capacity is a **lower** bound, not an upper bound

**Doc** `circular_dependency_resolution.md:344-346`:
"1. **Within timestep**: AEI capacity from **previous timestep** is **upper bound**
 2. **Investment**: New AEI capacity based on **current irrigation use**
 3. **Next timestep**: Increased AEI allows more irrigation"

**Code**: `modules/41_area_equipped_for_irrigation/endo_apr13/presolve.gms:11`
```gams
vm_AEI.lo(j) = pc41_AEI_start(j) / ((1 - s41_AEI_depreciation)**(m_timestep_length));
```
i.e. the previous timestep sets a **floor** (depreciated existing capital), not a ceiling. No upper
bound derived from the previous timestep exists anywhere (`rg -n "vm_AEI\." modules/ core/` → only
`.lo` in `endo_apr13/presolve.gms:11`, `.fx` in the non-default `static/presolve.gms:9`, and `.l/.m/.up/.lo`
report writes in postsolve). Irrigated area is capped by the **current-timestep** decision variable
`vm_AEI` (`equations.gms:10-11`, `q41_area_irrig`), and `vm_AEI` may expand *within the same timestep*
at investment cost (`q41_cost_AEI`, `equations.gms:19-23`, priced on `vm_AEI(j2)-pc41_AEI_start(j2)`).

**Verify**: `rg -n "vm_AEI\." modules/ core/` (11 hits, listed above); `awk` of
`modules/41_area_equipped_for_irrigation/endo_apr13/{presolve,equations,postsolve}.gms`.

**Fix**: "Within timestep: the depreciated previous-timestep AEI (`pc41_AEI_start`) is a **lower** bound on
`vm_AEI` (`endo_apr13/presolve.gms:11`); irrigated area is capped by the *current* `vm_AEI` via
`q41_area_irrig` (`equations.gms:10-11`), and expansion above the floor is paid for in the same timestep
through `q41_cost_AEI`. The temporal element is the ratchet/depreciation of the floor, not a capacity ceiling."

---

### CDR-06 (Major, mechanism) — Cycle 1 asserts a manure→soil-fertility→yield feedback and a 17→14 flow; neither exists

**Doc** `circular_dependency_resolution.md:237-245` and `:253`:
```
vm_prod(j,kcr) [17] → pm_yields_semi_calib(j,kve,w) [14]
    ↓ (Yields drive feed availability)
vm_prod_reg(i2,kap) [70] → manure availability
    ↓ (Manure affects soil fertility)
pm_yields_semi_calib(j,kve,w) [14] → vm_prod(j,kcr) [17]
```
"3. **Across timesteps**: Manure from livestock(t) affects yields(t+1)"

**Code**:
- `pm_yields_semi_calib` is populated **only** in module 14 preloop from the 1995 slice of the calibrated
  yields: `modules/14_yields/managementcalib_aug19/preloop.gms:116` and `:149`
  (`pm_yields_semi_calib(j,knbe14,w) = i14_yields_calib("y1995",j,knbe14,w);`). No optimization variable
  enters it. It is read by module 17's **presolve** only:
  `modules/17_production/flexreg_apr16/presolve.gms:10`. Flow is **14 → 17**, not 17 → 14.
- Module 14 (default realization `managementcalib_aug19`) has **no** manure / SOM / nitrogen input. Its
  complete external-interface input set is: `fm_carbon_density`, `fm_croparea`, `fm_tau1995`, `pcm_tau`,
  `pm_carbon_density_*`, `pm_climate_class`, `pm_land_start`, `pm_past_mngmnt_factor`, `vm_tau`.
  The only livestock link is `pm_past_mngmnt_factor` (declared `70_livestock`, built from cattle numbers
  in `modules/70_livestock/fbask_jan16/presolve.gms:64-67`), and it scales **pasture** yields only
  (`modules/14_yields/managementcalib_aug19/equations.gms:35-39`).

**Verify**
- `rg -n "pm_yields_semi_calib" modules/ core/ config/ scripts/` → 7 hits: 14 declarations/preloop (both realizations) + `modules/17_production/flexreg_apr16/presolve.gms:10`
- `rg -ni "manure|som|nr_soil|awms|nitrogen" modules/14_yields/managementcalib_aug19/*.gms` → 1 hit, `preloop.gms:160`, a substring match inside the English word "some" (positive control: `rg -c "vm_tau" .../equations.gms` → `1`)
- role map: `pm_yields_semi_calib` → populated `['14']`, read `['14','17']`

**Fix**: replace the chain with the mechanism the corrected prose at `:251` already describes
(`vm_tau` within-timestep, `pcm_tau` across timesteps), and replace the manure claim with the actual
70→14 link: `pm_past_mngmnt_factor` (cattle-number-driven, pasture yields only). Note that the same
"Livestock provides manure affecting yields" line exists at `core_docs/Module_Dependencies.md:194` and
should be fixed with it.

---

### CDR-07 (Major, attribution_populate) — `vm_land(j,"crop")` attributed to module 30; module 29 populates it

**Doc** `circular_dependency_resolution.md:386`: `vm_land(j,"crop") [30] → competes for land (crop ↓ as forest ↑)`

**Code**: the crop slice is on the LHS of `q29_cropland` in module 29 —
`modules/29_cropland/detail_apr24/equations.gms:11-12` (default realization; `config/default.cfg:814`)
and `modules/29_cropland/simple_apr24/equations.gms:12-13`. Module 30 only **reads** it
(`modules/30_croparea/simple_apr24/equations.gms:23`, `detail_apr24/equations.gms:23`, in `q30_betr_target`).
The bracket convention in this same chain is populator-based — `vm_land(j,"forestry") [32]` is correct
(`modules/32_forestry/dynamic_may24/equations.gms:56`) and `vm_emissions_reg(...) [52]` is correct
(`modules/52_carbon/normal_dec17/equations.gms:17`) — so `[30]` is a genuine mis-attribution, not shorthand.

**Verify**: `rg -n 'vm_land\(j2,"crop"\)' modules/*/*/equations.gms` → LHS `=e=` only in
`29_cropland/{detail_apr24:12, simple_apr24:13}`; all module-30 hits are RHS.
Role map: `vm_land` populated `['10','29','31','32','34','35']`, read `['10','22','29','30','31','32','34','35','50','58','59']`.

**Fix**: `vm_land(j,"crop") [29 — q29_cropland; croparea (30) supplies vm_area into it]`. While editing,
note that `vm_carbon_stock(...) [56]` on the next chain line is the *declaring* module — the forestry
slice is populated by 32 — so the bracket meaning should be stated once at the top of the chain.

---

### CDR-08 (Major, attribution_populate) — conservation lower bounds are applied in module 35 (and 31), not in 22 or 10

**Doc** `circular_dependency_resolution.md:288`, `:292`, `:302-303`:
"vm_land(j,land_natveg) [35] → conservation bounds set on vm_land.lo [10]" /
"pm_land_conservation(t,j,land,consv_type) [22] → vm_land.lo(j,land_natveg) [10]" /
"`vm_land(j,land_natveg) ≥ pm_land_conservation(t,j,land_natveg,"protect")  [22, bounds]`"

**Code**: every assignment to `vm_land.lo` for the natural-vegetation pools is in module 35's presolve
(default realization `pot_forest_may24`, `config/default.cfg:1156`):
`presolve.gms:157,159,162` (primforest), `:201` (secdforest), `:231` (other) — and pasture in module 31
(`modules/31_past/endo_jun13/presolve.gms:9`). Module 22 assigns **no** bound; it *reads*
`vm_land.lo(j,"crop")` while sizing restoration potentials
(`modules/22_land_conservation/area_based_apr22/presolve_ini.gms:86,97,108`) and populates
`pm_land_conservation`. Module 10 never touches `vm_land.lo` (its only occurrence is the report write
`postsolve.gms:52`). The stated inequality is also incomplete for secdforest/other, whose bound is
`pm_land_conservation(...,"protect") + p35_land_restoration(...)`.

**Verify**: `rg -n "vm_land\.lo" modules/ core/` → 13 hits: 22 (3 reads), 32 (1 read), 10 (1 report write),
35 (5 assignments + 1 read), 31 (1 assignment), 34 (1 assignment). Role map: `pm_land_conservation`
declared `22_land_conservation`, populated `['22','32','35']`, read `['13','22','29','31','32','35']` — module 10 is not a consumer.

**Fix**: "`pm_land_conservation` [22, populated] → applied as `vm_land.lo(j,land_natveg)` **in module 35's
presolve** (`modules/35_natveg/pot_forest_may24/presolve.gms:162,201,231`; pasture in
`modules/31_past/endo_jun13/presolve.gms:9`) on module 10's `vm_land`", and add the
`+ p35_land_restoration` term to the inequality.

---

### CDR-09 (Major, formula — units) — carbon price is USD per **tC**, not per tCO2

**Doc** `circular_dependency_resolution.md:410`: "`im_pollutant_prices`: Carbon price trajectory (0-1000 USD/tCO2)"

**Code**: `modules/56_ghg_policy/price_aug22/declarations.gms:9` — "(USD17MER per Mg)"; the `co2_c` slice
is per Mg **C**. Confirmed by `preloop.gms:77` (comment: "*12/44 conversion from USD17MER per tC to
USD17MER per tCO2") and `input.gms:67` (`s56_minimum_cprice  Minium C price (USD17MER per tC) / 3.67 /`
— 3.67 = 44/12, i.e. 1 USD/tCO2). Mislabelling the unit misstates any configured price by 44/12 ≈ 3.67x.
The "0-1000" range is also unsourced in code or config.

**Verify**: `rg -n "44/12|12/44|3\.67|s56_minimum_cprice" modules/56_ghg_policy/price_aug22/*.gms`
→ `preloop.gms:74,77,80,81,82`, `input.gms:67`; `rg -n "f56_pollutant_prices" .../input.gms:93`
→ "GHG certificate prices for N2O-N CH4 CO2-C (USD17MER per t)".

**Fix**: "`im_pollutant_prices`: GHG certificate prices, USD17MER per Mg of the pollutant unit — for
`co2_c` that is per **t C** (multiply by 12/44 for USD/tCO2); see
`modules/56_ghg_policy/price_aug22/declarations.gms:9` and `preloop.gms:77`." Drop the unsourced range or
cite a scenario file.

---

### CDR-10 (Major, realization — hallucinated identifier asserted as existing) — `pm_water_avail` does not exist

**Doc** `circular_dependency_resolution.md:592-594` (a "✅ SAFE" modification pattern):
```gams
vm_area.up(j,kcr,"irrigated")$(pm_water_avail(j) < threshold) = 0;
* Does NOT create new dependency (just uses existing pm_water_avail)
```
The comment explicitly asserts the parameter exists.

**Code**: `pm_water_avail` appears **nowhere** in the model. The water-availability interface is
`im_wat_avail(t,wat_src,j)` (`modules/43_water_availability/total_water_aug13/declarations.gms:9`,
default realization per `config/default.cfg:1427`), populated by 43 and read by 42.

**Verify**: `rg -n "pm_water_avail" modules/ core/` → **0 hits** (positive controls in the same command:
`vm_cost_landcon` → 5 hits, `pm_yields_semi_calib`-family → 5 hits, `vm_yld` → 14 files).

**Fix**: use `im_wat_avail(t,wat_src,j)` (or state plainly that the parameter in the snippet is
hypothetical). Note the neighbouring `pm_yields(j,kcr)` at `:608` is fine — that block is explicitly
labelled a hypothetical "⚠️ RISKY" modification; only the `:594` line claims existence.
*(tier note: Critical↔Major boundary; kept at Major because the error surfaces as a GAMS compile failure, not a silent wrong result.)*

---

### CDR-11 (Minor, other — hallucinated identifier) — `vm_yields` is not a MAgPIE symbol

**Doc** `circular_dependency_resolution.md:844`:
`vars <- c("vm_land", "vm_prod", "vm_carbon_stock", "vm_yields", ...)`

**Code**: the yield variable is `vm_yld(j,kve,w)` (declared in `14_yields`, populated by 14, read by 14/30/31).
`vm_yields` has 0 hits tree-wide; `readGDX(gdx,"vm_yields")` would return nothing while the other three
names in the vector are real.

**Verify**: `rg -n "vm_yields" modules/ core/` → **0 hits**; positive control `rg -l "vm_yld" modules/` → 14 files.

**Fix**: `"vm_yld"`.

---

### CDR-12 (Minor, other — naming convention) — `pcm_` gloss contradicts the coding etiquette

**Doc** `circular_dependency_resolution.md:60`:
"`pcm_*` = **Parameter from previous timestep** ("p" = parameter, "cm" = current module)"

**Code**: `main.gms:107-121` (MAgPIE coding etiquette) — `?c_` = "value for the **Current timestep**",
`?m_` = "**module-relevant object** — used by at least one module and the core code". So `pcm_` decomposes
as p + c(urrent timestep) + m(odule interface); there is no "current module" letter. (The functional gloss
"holds the previous timestep's solution during timestep t" is fine and worth keeping.)
Related, same block: `im_*` is glossed as "exogenous, **never changes**" (`:61`) — `i_` means "not
influenced by the optimization" (`main.gms:100`); `im_pollutant_prices` is re-assigned seven times in
`modules/56_ghg_policy/price_aug22/preloop.gms:37-82`.

**Verify**: `awk 'NR>=88&&NR<=135' main.gms` → prefix table at :96-105, second-letter rules at :109-110 and :119-121.

**Fix**: "`pcm_*` = processing parameter, **c**urrent-timestep value, **m**odule interface (`main.gms:109,119`);
in equations during timestep t it carries the previous timestep's solution, written in `postsolve.gms`."
And soften `im_*` to "not influenced by the optimization (but may be recomputed in preloop/presolve)".

---

## Deferred (not flagged — insufficient evidence or out of lens)

- **"26 circular dependency cycles"** (`:5`, `:11`, `:749`, `:1036`): not code-verifiable without a graph
  cycle-detection run; the doc itself labels 22 of them "Inferred". No artifact exists behind the 26.
- **"Modifying Module 10 (Land): 4+ cycles, 15 consumers"** (`:584`): traces to
  `core_docs/Module_Dependencies.md:179` ("10_land: 15 out, 2 in"). Code-derived consumer unions are 13
  (modules reading a module-10 `vm_*`) or 18 (all non-`fm_` module-10 interfaces, incl. `pcm_land`,
  `pm_land_start`, `pm_land_hist`). Counting method is unstated in both docs → cannot call 15 wrong.
- **§8.2 "Additional Cycles (22 More, Inferred)"** (`:747-759`): explicitly hedged as suspected. C10
  (14-13-12) looks acyclic in code (12 → 13 via `pm_interest`, no return edge), but the doc does not
  assert it as verified.
- **R verification snippets** (`:257-263`, `:308-312`, `:359-363`, `:418-428`, `:530-565`): magpie4 calls
  (`land_conservation()`, `AEI()`, `costs(components=...)`, `gdx$status$solve_status`) not checked — needs
  the version-pinned magpie4 clone, outside this lens.
- **Solver mentions** (`:150`, `:831`, `:1012`): CONOPT, IPOPT and CPLEX all exist (`nlp_apr17` default =
  conopt4 with conopt3 fallback; `nlp_ipopt` and `lp_nlp_apr17` are non-default realizations). Correct as
  written, but a "default is conopt4 via `nlp_apr17`" caveat would help — style, not a bug.
- **`vm_emissions_reg(i,"co2_c")`** (`:392`): declared `(i,emis_source,pollutants)`, so the two-index form
  puts the pollutant in the `emis_source` slot. Read as diagram shorthand in a chain that elsewhere elides
  indices; not flagged.
