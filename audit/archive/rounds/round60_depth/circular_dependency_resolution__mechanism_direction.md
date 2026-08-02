# Depth audit — `cross_module/circular_dependency_resolution.md`
## Lens: mechanism_direction (R60 depth)

**Ground truth**: MAgPIE `develop` read-only worktree (referred to below as `<develop>`; all cited
code paths are repo-relative `modules/NN_name/realization/file.gms:LINE`).
**Attribution reference**: `audit/integrated/depth_rolemap.json` (checked first for every
DECLARED/POPULATED/READ claim, then confirmed with a both-endpoints grep in code).
**Claims verified**: ~65 code-checkable claims.
**Result**: 17 bugs (3 Critical, 7 Major, 7 Minor).

Default realizations confirmed from `config/default.cfg` before any module claim was judged:
10 `landmatrix_dec18`, 13 `endo_jan22`, 14 `managementcalib_aug19`, 17 `flexreg_apr16`,
21 `selfsuff_reduced`, 22 `area_based_apr22`, 29 `detail_apr24`, 30 `simple_apr24`,
31 `endo_jun13`, 32 `dynamic_may24`, 35 `pot_forest_may24`, 41 `endo_apr13`, 52 `normal_dec17`,
54 `off`, 56 `price_aug22`, 59 `cellpool_jan23`, 80 `nlp_apr17`.

---

## What the doc gets RIGHT (verified, no bug)

Recorded so the fixes below are not mistaken for a general indictment:

| Doc claim | Code |
|---|---|
| `q10_land_area` = `sum(land, vm_land(j2,land)) =e= sum(land, pcm_land(j2,land))` | `modules/10_land/landmatrix_dec18/equations.gms:13-15` — exact match |
| `pcm_land(j,land) = vm_land.l(j,land)` in postsolve:9 | `modules/10_land/landmatrix_dec18/postsolve.gms:9` |
| `pcm_carbon_stock(...) = vm_carbon_stock.l(...)` in 56 postsolve:8 | `modules/56_ghg_policy/price_aug22/postsolve.gms:8` |
| `q52_emis_co2_actual` reads `pcm_carbon_stock` AND `vm_carbon_stock` | `modules/52_carbon/normal_dec17/equations.gms:16-19` |
| Land-conversion costs are area-based, no carbon density (`q39_cost_landcon`) | `modules/39_landconversion/calib/equations.gms:12-15` |
| `vm_import`/`vm_export` do not exist; `v21_trade` only in the non-default bilateral realization | whole-tree grep: 0 hits / `modules/21_trade/selfsuff_reduced_bilateral22/declarations.gms:23` |
| `q21_trade_glo` = global supply ≥ demand + balanceflow | `modules/21_trade/selfsuff_reduced/equations.gms:12-14` |
| `q14_yield_crop` scales `i14_yields_calib` by current-timestep `vm_tau`; `q14_yield_past` uses lagged `pcm_tau` | `modules/14_yields/managementcalib_aug19/equations.gms:14-16` and `:35-39` |
| `pcm_tau` updated at `modules/13_tc/endo_jan22/postsolve.gms:16` | exact match |
| `pc41_AEI_start(j) = vm_AEI.l(j)` in 41 postsolve | `modules/41_area_equipped_for_irrigation/endo_apr13/postsolve.gms:8` |
| `s56_buffer_aff` = 0.5 (half of CDR credited, `(1-s56_buffer_aff)`) | `modules/56_ghg_policy/price_aug22/input.gms:71`, `equations.gms:77` |
| `s56_c_price_induced_aff` is a 1/0 switch | `modules/56_ghg_policy/price_aug22/input.gms:69` (default 1) |
| `vm_reward_cdr_aff` reduces `vm_cost_glo` | `modules/11_costs/default/equations.gms:27` (`- vm_reward_cdr_aff(i2)`) |
| `im_pollutant_prices` loaded in preloop (§2.3 step 1) | `modules/56_ghg_policy/price_aug22/preloop.gms:37-43` |
| Solver parentheticals `(CONOPT/IPOPT/CPLEX)` | not fabricated: `nlp_apr17` uses conopt4/conopt3, `nlp_ipopt` and `lp_nlp_apr17` exist |

---

## BUGS

### CDR-1 — 🔴 Critical — `mechanism`
**Doc** (`circular_dependency_resolution.md:241-245`, reinforced at `:253`, `:268`, `:273`):
```
vm_prod_reg(i2,kap) [70] → manure availability
    ↓
  (Manure affects soil fertility)
    ↓
pm_yields_semi_calib(j,kve,w) [14] → vm_prod(j,kcr) [17]
```
plus "3. **Across timesteps**: Manure from livestock(t) affects yields(t+1)" (`:253`),
"**Unrealistic intensification**: Manure contribution overestimated" (`:268`) and the fix advisory
"Limit manure impact on yields (Module 59, SOM)" (`:273`).

**Reality**: there is no manure→soil-fertility→yield feedback anywhere in MAgPIE. `vm_yld` is
populated only by module 14, from `i14_yields_calib` (a preloop parameter derived from LPJmL input
yields), `vm_tau`/`pcm_tau`, `pm_past_mngmnt_factor`, `s14_yld_past_switch` and `fm_tau1995`. The
default realization of module 14 references **no** manure, nitrogen or SOM interface at all.
Manure (`vm_manure`, `vm_manure_recycling`, module 55) is read only by 50, 51, 53 — it enters the
**nitrogen budget and fertilizer costs**, never a yield. Module 59's `vm_nr_som_fertilizer` is read
only by 50 (same channel).

The *genuine* livestock→yield edge is `pm_past_mngmnt_factor` (declared `70_livestock`, computed in
`modules/70_livestock/fbask_jan16/presolve.gms:64-67` from cattle-number growth `p70_incr_cattle`,
recursively on its own `t-1` value) applied to **pasture** yields only in `q14_yield_past`.

**Evidence**: `modules/14_yields/managementcalib_aug19/equations.gms:14-16, 35-39`;
`modules/70_livestock/fbask_jan16/presolve.gms:64-67`.
**Verify**:
`rg -n "vm_prod|vm_manure|nr_soil|vm_res_recycling|som" <develop>/modules/14_yields/managementcalib_aug19/*.gms`
→ 1 hit, a prose comment at `preloop.gms:160` about outlier correction; no interface use.
Positive control `rg -c "vm_tau" .../equations.gms` → 1 (grep works in that dir).
`python3` on `depth_rolemap.json`: `vm_yld` → populated_by `['14']`, read_by `['14','30','31']`;
`vm_manure` → read_by `['50','51','53','55']`.

**Why Critical**: a fabricated mechanism presented as implemented, with an action item telling the
reader to "limit manure impact on yields (Module 59)" — a user would go edit a module that has no
such lever. Note the same wrong edge exists in `core_docs/Module_Dependencies.md:194`
("Livestock provides manure affecting yields") — fix both.

**Fix**: replace the manure edge with the real one:
`vm_prod_reg(i,kli) [70] → p70_incr_cattle → pm_past_mngmnt_factor(t,i) [70] → q14_yield_past [14]`
(pasture yields only, cross-timestep because `pm_past_mngmnt_factor(t)` builds on `(t-1)`), and
state explicitly that crop yields have **no** feedback from livestock, manure or soil carbon.
Delete "Limit manure impact on yields (Module 59, SOM)" from the fix list.

---

### CDR-2 — 🔴 Critical — `mechanism` (inverted bound direction)
**Doc** (`circular_dependency_resolution.md:344-346`):
```
1. **Within timestep**: AEI capacity from **previous timestep** is **upper bound**
2. **Investment**: New AEI capacity based on **current irrigation use**
3. **Next timestep**: Increased AEI allows more irrigation
```
and the fix "Limit AEI expansion rate (Module 41 configuration)" (`:371`).

**Reality**: the previous timestep's AEI is a **lower** bound, not an upper bound:
`vm_AEI.lo(j) = pc41_AEI_start(j) / ((1 - s41_AEI_depreciation)**(m_timestep_length));`
(`modules/41_area_equipped_for_irrigation/endo_apr13/presolve.gms:11`), and with the default
`s41_AEI_depreciation = 0` this reduces exactly to `vm_AEI.lo(j) = pc41_AEI_start(j)` — AEI can
never shrink. There is **no** upper bound derived from the previous timestep. Expansion happens
**within the current timestep**: `vm_AEI` is free upward, `q41_area_irrig` couples it to current
irrigated area simultaneously (`equations.gms:10-11`), and the extra capacity is charged in the
same timestep via `q41_cost_AEI` (`equations.gms:19-23`, `(vm_AEI - pc41_AEI_start) * unitcost *
annuity`). So irrigation expansion is *not* deferred to the next timestep.
Module 41 also exposes only two config switches (`c41_initial_irrigation_area`,
`s41_AEI_depreciation`, `config/default.cfg:1328,1332`) — there is no expansion-rate limiter.

**Evidence**: `modules/41_area_equipped_for_irrigation/endo_apr13/presolve.gms:11`,
`equations.gms:10-11, 19-23`, `input.gms:11` (`s41_AEI_depreciation ... / 0 /`).
**Verify**: `rg -n "vm_AEI" <develop>/modules/` → the only bound assignment in the default
realization is the `.lo` at `presolve.gms:11` (the `static` realization instead does
`vm_AEI.fx(j) = f41_irrig("y1995",j,...)` at `static/presolve.gms:9`).
`grep -n "s41_AEI_depreciation" <develop>/config/default.cfg` → `1332:cfg$gms$s41_AEI_depreciation <- 0 # def = 0`.

**Fix**: rewrite the three steps as: (1) previous-timestep AEI, depreciated by
`s41_AEI_depreciation` (default 0), is a **lower** bound `vm_AEI.lo` — capacity cannot fall;
(2) additional AEI is decided **in the same timestep**, constrained by `q41_area_irrig`
(`sum(kcr, vm_area(j2,kcr,"irrigated")) =l= vm_AEI(j2)`) and priced by `q41_cost_AEI`;
(3) the cross-timestep element is the ratchet (`pc41_AEI_start`), not a delay in benefit.
Replace the "Limit AEI expansion rate" fix with the levers that exist (unit costs
`f41_c_irrig`, `s41_AEI_depreciation`, or the `static` realization).

---

### CDR-3 — 🔴 Critical — `attribution_populate`
**Doc** (`circular_dependency_resolution.md:390`): `vm_carbon_stock(j,"forestry","vegc","actual") [56] → carbon sequestration`

**Reality**: module 56 **declares** `vm_carbon_stock` and **reads** it (`q56_emis_pricing_co2`,
`equations.gms:19-22`) — it computes no carbon stock. The `"forestry"` slice is populated by
`q32_carbon` in `modules/32_forestry/dynamic_may24/equations.gms:108`. Every other tag in the same
chain names the module that *computes* the quantity, so `[56]` reads as "computed in 56" and sends
a reader tracing afforestation carbon accounting to the wrong file. Full populator set:
29 (crop), 31 (past), 32 (forestry), 34 (urban), 35 (primforest/secdforest/other), 59 (soilc slice).

**Evidence**: `modules/32_forestry/dynamic_may24/equations.gms:108`;
`modules/56_ghg_policy/price_aug22/declarations.gms:19` (declaration only, over `c_pools`).
**Verify**: `rg -n "^\s*vm_carbon_stock" <develop>/modules/*/*/equations.gms` → LHS hits in
31, 35, 29, 59, 32 only; role map `vm_carbon_stock` → declared_in `56_ghg_policy`,
populated_by `['29','31','32','34','35','59']`, read_by `['52','56','59']`.

**Why Critical**: this is the immutable G2 anchor class (wrong populator set for
`vm_carbon_stock`), scored Critical by future-reader harm in `audit/flywheel_rubric.md` §1.

**Fix**: `vm_carbon_stock(j,"forestry",ag_pools,"actual") [populated by 32, q32_carbon; declared in 56]`.

---

### CDR-4 — 🟠 Major — `data_flow_direction`
**Doc** (`circular_dependency_resolution.md:288,292`):
```
vm_land(j,land_natveg) [35] → conservation bounds set on vm_land.lo [10]
pm_land_conservation(t,j,land,consv_type) [22] → vm_land.lo(j,land_natveg) [10]
```
and `:302` `vm_land(j,land_natveg) ≥ pm_land_conservation(t,j,land_natveg,"protect")  [22, bounds]`.

**Reality**: module 10 never reads `pm_land_conservation` and never sets `vm_land.lo`. The
conservation floors are applied in **module 35** presolve —
`vm_land.lo(j,"primforest")` (`modules/35_natveg/pot_forest_may24/presolve.gms:162`),
`vm_land.lo(j,"secdforest")` (`:201`), `vm_land.lo(j,"other")` (`:231`) — and in **module 31**
for pasture (`modules/31_past/endo_jun13/presolve.gms:9`). Module 10's presolve only fixes
`vm_lu_transitions` and applies `m_boundfix(vm_land,...,up,...)`
(`modules/10_land/landmatrix_dec18/presolve.gms:13-25`). `pm_land_conservation` consumers are
13, 22, 29, 31, 32, 35 — module 10 is not among them. (Module 35 also writes back into
`pm_land_conservation` in its presolve, `:149,197,198,221,229`.)

**Evidence**: `modules/35_natveg/pot_forest_may24/presolve.gms:162,201,231`;
`modules/31_past/endo_jun13/presolve.gms:9`; `modules/10_land/landmatrix_dec18/presolve.gms:13-25`.
**Verify**: `rg -n "vm_land\.lo" <develop>/modules/ <develop>/core/` → assignments only in 35, 31,
34 (`urban`), plus reads in 22/32 and the postsolve output line in 10.
`rg -n "pm_land_conservation" <develop>/modules/` → no hit in `10_land`.

**Fix**: retarget the arrow — `pm_land_conservation(t,j,land,consv_type) [22] → vm_land.lo(j,land_natveg)
applied in 35 presolve (and 31 for "past")`. Note that the current
`core_docs/Module_Dependencies.md:196-199` already records 22→35 and 10→22 as **unidirectional**,
so §3.2's "10 ↔ 35 ↔ 22" should say the only bidirectional pair is 10↔35.

---

### CDR-5 — 🟠 Major — `data_flow_direction`
**Doc** (`circular_dependency_resolution.md:95-99`):
```
Module 10 (Land) ────────────→ Module 52 (Carbon)
       ↑                             │
       │                             ↓
  pcm_carbon_stock ←──── vm_carbon_stock
```

**Reality**: neither edge exists as drawn. Module 52 (`normal_dec17`) references **no** module-10
interface (`vm_land`, `pcm_land`, `vm_lu_transitions`) in any of its 9 files, and it does not
populate `vm_carbon_stock` — it reads it (CDR-3). Nor does module 10 read `pcm_carbon_stock`;
that parameter is populated by 56 and 59 and read by 52, 56, 59 only. The real topology is
**parallel, not serial**: the land modules (29/31/32/34/35, plus 59 for soilc) populate
`vm_carbon_stock` from `vm_land`; module 52 reads it alongside `pcm_carbon_stock`; the loop back
to land allocation closes only through the objective function (`vm_emissions_reg` → 56 →
`vm_emission_costs` → 11).

**Evidence**: `modules/52_carbon/normal_dec17/equations.gms:16-19` (its only equation);
role map `pcm_carbon_stock` → populated_by `['56','59']`, read_by `['52','56','59']`.
**Verify**: `rg -n "vm_land|pcm_land|vm_lu_transitions" <develop>/modules/52_carbon/normal_dec17/`
→ no match; positive control `rg -c "vm_carbon_stock" .../equations.gms` → 2.

**Fix**: redraw as
`land modules 29/31/32/34/35 → vm_carbon_stock (declared 56) → 52 (q52_emis_co2_actual, together
with pcm_carbon_stock) → vm_emissions_reg → 56 → vm_emission_costs → 11 → objective → land`,
and state that the lagged term `pcm_carbon_stock` is written in 56/59 postsolve, not consumed by 10.

---

### CDR-6 — 🟠 Major — `data_flow_direction`
**Doc** (`circular_dependency_resolution.md:392-394`):
```
vm_emissions_reg(i,"co2_c") [52] → reduced (or negative) CO2 emissions
    ↓
vm_reward_cdr_aff(i) [56] → revenue from carbon removal
```

**Reality**: the afforestation reward is not computed from `vm_emissions_reg`. `q56_reward_cdr_aff`
(`modules/56_ghg_policy/price_aug22/equations.gms:73-79`) is a function of `vm_cdr_aff(j2,ac,aff_effect)`
(declared and populated in **32_forestry**, `equations.gms:37,42`), `p56_c_price_aff`,
`s56_buffer_aff`, `p56_fader_cpriceaff` and `pm_interest` — expected *future* CDR by age class, not
realized emissions. `vm_emissions_reg` enters a **separate, parallel** channel:
`q56_emis_pricing`/`q56_emis_pricing_co2` → `v56_emission_cost` → `vm_emission_costs`
(`equations.gms:15-22, 29-58`). Both channels reach the objective independently
(`modules/11_costs/default/equations.gms:26-27`).

**Evidence**: `modules/56_ghg_policy/price_aug22/equations.gms:73-79` vs `:15-22,56-58`;
`modules/32_forestry/dynamic_may24/equations.gms:37,42`.
**Verify**: `rg -n "vm_emissions_reg" <develop>/modules/56_ghg_policy/price_aug22/*.gms`
→ equations only at `:17` (annual pricing) and prose at `:40`; nothing in `q56_reward_cdr_aff`.

**Fix**: split the chain into two parallel arms after `vm_carbon_stock`:
(a) `→ q52_emis_co2_actual → vm_emissions_reg → q56_emis_pricing_co2 → vm_emission_costs → 11`;
(b) `vm_cdr_aff [32] → q56_reward_cdr_aff → vm_reward_cdr_aff [56] → 11 (negative cost)`.

---

### CDR-7 — 🟠 Major — `data_flow_direction`
**Doc** (`circular_dependency_resolution.md:237`): `vm_prod(j,kcr) [17] → pm_yields_semi_calib(j,kve,w) [14]`
(and the return edge at `:245`).

**Reality**: the arrow is inverted and the variable is the wrong one. `pm_yields_semi_calib(j,kve,w)`
is declared in `modules/14_yields/managementcalib_aug19/declarations.gms:19` and assigned **only in
preloop** from the 1995 slice of the input-derived `i14_yields_calib`
(`preloop.gms:116` and `:149`). Its sole out-of-module consumer is module 17's presolve,
`pm_prod_init(j,kcr) = sum(w, fm_croparea("y1995",j,w,kcr) * pm_yields_semi_calib(j,kcr,w))`
(`modules/17_production/flexreg_apr16/presolve.gms:10`), which is then used as a **starting value**
(`presolve.gms:15`, `vm_prod.l(j,kcr) = pm_prod_init(j,kcr)`) and by module 38 for initial capital
stocks. Production never writes it. The endogenous yield→production edge is `vm_yld` via
`q30_prod`: `vm_prod(j2,kcr) =e= sum(w, vm_area(j2,kcr,w) * vm_yld(j2,kcr,w))`
(`modules/30_croparea/simple_apr24/equations.gms:14-15`).

**Evidence**: `modules/14_yields/managementcalib_aug19/preloop.gms:116,149`;
`modules/17_production/flexreg_apr16/presolve.gms:10,15`;
`modules/30_croparea/simple_apr24/equations.gms:14-15`.
**Verify**: `rg -ln "pm_yields_semi_calib" <develop>/modules/` → only `14_yields/*` and
`17_production/flexreg_apr16/presolve.gms`.

**Fix**: drop the `vm_prod → pm_yields_semi_calib` arrow; label `pm_yields_semi_calib` as a
preloop initialization parameter (1995) feeding `pm_prod_init`, and use
`vm_yld [14] → q30_prod → vm_prod [30/17]` for the yield→production edge.

---

### CDR-8 — 🟠 Major — `formula` (unit basis)
**Doc** (`circular_dependency_resolution.md:410`):
"`im_pollutant_prices`: Carbon price trajectory (0-1000 USD/tCO2)"

**Reality**: `im_pollutant_prices(t_all,i,pollutants,emis_source)` is declared as
"Certificate prices for N2O-N CH4 CO2-C used in the model (**USD17MER per Mg**)"
(`modules/56_ghg_policy/price_aug22/declarations.gms:9`) — per Mg of the *pollutant species named
by the set element*, i.e. per Mg **C** for `"co2_c"` and per Mg N for `n2o_n_*`. Module 56's own
preloop confirms the basis by converting CO2-equivalent caps to a carbon basis with `12/44`
(`preloop.gms:80-82`, e.g. `s56_limit_ch4_n2o_price*12/44*28`). A USD/tCO2 reading is off by
44/12 ≈ 3.67x. (`modules/module_56.md:152` already states USD17MER/Mg correctly.)

**Evidence**: `modules/56_ghg_policy/price_aug22/declarations.gms:9`, `preloop.gms:80-82`.
**Verify**: `rg -n "im_pollutant_prices" <develop>/modules/56_ghg_policy/price_aug22/declarations.gms`
→ `9: ... (USD17MER per Mg)`.

**Fix**: "`im_pollutant_prices`: GHG certificate prices, USD17MER per Mg of the priced species
(`co2_c` = per Mg **C**; multiply by 12/44 to convert a USD/tCO2 figure)". Drop the unsourced
"0-1000" range or replace it with a figure re-derived from the active
`c56_pollutant_prices` scenario (default `R34M410-SSP2-NPi2025`).

---

### CDR-9 — 🟠 Major — `citation`
**Doc** (`circular_dependency_resolution.md:745`): "**Source**: Module_Dependencies.md (lines 149-179)"
for the 4-cycle catalogue table.

**Reality**: `core_docs/Module_Dependencies.md:149-179` is the architecture-layer listing
(Layers 4-6) plus §3.2 "Hub-and-Spoke Patterns" — nothing about cycles. The cycle content is
§4 "Circular Dependencies (Feedback Loops)" at `:182`, with the 4 key cycles at `:186-215`.

**Evidence**: `core_docs/Module_Dependencies.md:182` (`### 4. Circular Dependencies`), `:186`
(`**26 circular dependencies identified, key cycles:**`).
**Verify**: `grep -n "^### 4\.\|^#### 4\.\|^### 5\." core_docs/Module_Dependencies.md`
→ `182`, `184`, `218`, `237`; `sed -n '145,185p'` shows layer/hub content at the cited range.

**Fix**: cite `core_docs/Module_Dependencies.md` §4.1 (lines 184-215).

---

### CDR-10 — 🟠 Major — `set_membership`
**Doc** (`circular_dependency_resolution.md:143`):
`vm_prod_reg(i,kall) = sum(cell(i,j), vm_prod(j,kall))               [q17_prod_reg]`

**Reality**: `q17_prod_reg(i2,k) .. vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k));`
(`modules/17_production/flexreg_apr16/equations.gms:10-11`). The domain is `k` (primary products,
28 members, `modules/14_yields/managementcalib_aug19/sets.gms:12-17`), not `kall` (41 members,
`core/sets.gms:228-235`). `vm_prod` is itself declared over `k`
(`modules/17_production/flexreg_apr16/declarations.gms:9`), so `vm_prod(j,kall)` is out of domain.
The `kall\k` slices of `vm_prod_reg` (secondary products, residues) are populated elsewhere —
module 20 (`modules/20_processing/substitution_may21/equations.gms:41,62`) and module 18
(`modules/18_residues/flexreg_apr16/equations.gms:73,81`).

**Evidence**: `modules/17_production/flexreg_apr16/equations.gms:10-11`, `declarations.gms:9-10`.
**Verify**: `rg -n "q17_prod_reg" -A 4 <develop>/modules/17_production/*/equations.gms` → domain `(i2,k)`.

**Fix**: write `vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k))  [q17_prod_reg]` and add a
one-line note that secondary products and residues get their `vm_prod_reg` from modules 20 and 18.

---

### CDR-11 — 🟡 Minor — `attribution_populate`
**Doc** (`circular_dependency_resolution.md:386`): `vm_land(j,"crop") [30] → competes for land`

**Reality**: the `"crop"` slice of `vm_land` is populated by `q29_cropland`
(`modules/29_cropland/simple_apr24/equations.gms:12-13`; default realization `detail_apr24` has the
same equation) — `vm_land(j2,"crop") =e= sum((kcr,w), vm_area(j2,kcr,w))`. Module 30 only *reads*
`vm_land(j2,"crop")` (`modules/30_croparea/simple_apr24/equations.gms:23`) and owns `vm_area`.
Role map: `vm_land` populated_by `['10','29','31','32','34','35']` — 30 is not a populator.

**Verify**: `rg -n "vm_land" <develop>/modules/30_croparea/simple_apr24/*.gms` → 1 read, no LHS.
**Fix**: tag it `[29]` (or write `vm_land(j,"crop") [29, from vm_area of 30]`).

---

### CDR-12 — 🟡 Minor — `other` (count)
**Doc** (`circular_dependency_resolution.md:584`): "Modifying Module 10 (Land): 🔴 EXTREME RISK
(4+ cycles, **15 consumers**)"

**Reality**: 18 distinct modules reference at least one module-10 interface
(`pm_land_start`, `pm_land_hist`, `pcm_land`, `vm_landdiff`, `vm_land`, `vm_landexpansion`,
`vm_landreduction`, `vm_cost_land_transition`, `vm_lu_transitions`) across all realizations:
11, 13, 14, 22, 29, 30, 31, 32, 34, 35, 39, 44, 50, 56, 58, 59, 71, 80. Restricted to the default
realization of each module it is **17** (80's only consumer, `vm_landdiff`, lives in the non-default
`lp_nlp_apr17`). `vm_land` alone has 10 consumer modules. None of these is 15; the figure appears to
be inherited from `core_docs/Module_Dependencies.md:179` ("10_land: 15 out"), which needs the same
recomputation.

**Verify**:
`rg -l "\b(pm_land_start|pm_land_hist|pcm_land|vm_landdiff|vm_land|vm_landexpansion|vm_landreduction|vm_cost_land_transition|vm_lu_transitions)\b" <develop>/modules/*/*/*.gms | awk -F/ '{print $5}' | sort -u | grep -v '^10_land$' | wc -l`
→ `18` (per-module default-realization check → 17; `80_optimization/nlp_apr17` = 0 hits).

**Fix**: "(4+ cycles; 17 consumer modules in the default configuration, 18 across all
realizations; `vm_land` alone is read by 10)" and add the re-derivation command so the number has
an artifact.

---

### CDR-13 — 🟡 Minor — `other` (naming-convention gloss)
**Doc** (`circular_dependency_resolution.md:60-61`):
"`pcm_*` = **Parameter from previous timestep** ("p" = parameter, "cm" = current module)";
"`im_*` = **Input data** (exogenous, never changes)".

**Reality**: in MAgPIE's prefix scheme the trailing `m` marks a **module interface** (visible to all
modules) — the opposite of "current module". `pcm_land` is declared in 10 and read by 13 other
modules (`13, 22, 29, 31, 32, 34, 35, 44, 56, 58, 59, 71` + 10); `pcm_carbon_stock` is declared in
56 and populated by 56 **and** 59. The `c` marks the carried state of the last solved timestep.
`im_*` is likewise not immutable: `im_pollutant_prices` is time-indexed and rewritten a dozen times
in `modules/56_ghg_policy/price_aug22/preloop.gms:37-108` depending on config switches.

**Verify**: `rg -n "pcm_land" <develop>/modules/ | awk -F/ '{print $5}' | sort -u` → 14 module dirs.
**Fix**: "`pcm_*` = interface parameter (`m`) carrying the last solved timestep's value (`c`),
written in `postsolve.gms`"; "`im_*` = interface input parameter — exogenous to the optimization,
but may be time-dependent and transformed in `preloop`/`presolve`".

---

### CDR-14 — 🟡 Minor — `attribution_populate` (per-slice ownership)
**Doc** (`circular_dependency_resolution.md:976`, Appendix A):
`pcm_carbon_stock(j,land,ag_pools,stockType) | 56_ghg_policy | ... | modules/56_ghg_policy/price_aug22/postsolve.gms:8`

**Reality**: true for the `ag_pools` (vegc, litc) slice only. The parameter is **declared** over
`c_pools` (`modules/56_ghg_policy/price_aug22/declarations.gms:19`), and its `"soilc"` slice is
carried forward by module 59: `modules/59_som/cellpool_jan23/postsolve.gms:13` (default) and
`modules/59_som/static_jan19/postsolve.gms:9`. `CHANGELOG.md:36` documents this split explicitly.

**Verify**: `rg -n "pcm_carbon_stock" <develop>/` → postsolve writers in 56 (`:8`) and 59
(`cellpool_jan23:13`, `static_jan19:9`).
**Fix**: add the 59 row (or a "populated per slice" note): `ag_pools` slice ← 56 postsolve:8,
`"soilc"` slice ← 59 postsolve.

---

### CDR-15 — 🟡 Minor — `set_membership`
**Doc** (`circular_dependency_resolution.md:723`): "**Independent modules** (37, 45, 54) can be run in parallel"

**Reality**: none of the three is dependency-free. `pm_labor_prod` (37) is read by 38;
`pm_climate_class` (45) is read by 14, 52, 58, 59; `vm_p_fert_costs` (54) is an **optimization
variable** that enters the objective at `modules/11_costs/default/equations.gms:25`, i.e. module 54
is inside the single simultaneous NLP and cannot be solved separately in any implementation sense
(its default realization is `off`, which fixes it: `modules/54_phosphorus/off/preloop.gms:10`).
What is true is that these three participate in no *cycle* (pure source / pure sink).

**Verify**: role map — `pm_labor_prod` read_by `['37','38']`; `pm_climate_class` read_by
`['14','45','52','58','59']`; `vm_p_fert_costs` read_by `['11','54']`.
**Fix**: "Acyclic modules (37, 45, 54) — each is a pure source or sink, so they add no feedback;
they are still part of the single NLP solve and are not independently executable."

---

### CDR-16 — 🟡 Minor — `citation`
**Doc** (`circular_dependency_resolution.md:414`): "**Source**: module_56.md (lines 60-79)" for the
critical-parameter list (`im_pollutant_prices`, `s56_buffer_aff`, `s56_c_price_induced_aff`).

**Reality**: `modules/module_56.md:60-79` is the components/prose block of §2.1
`q56_emis_pricing` and the header of §2.2. The three parameters are documented at
`modules/module_56.md:40-41` (switch table with defaults) and `:287,310` (buffer semantics).

**Verify**: `sed -n '60,79p' modules/module_56.md`; `grep -n "s56_buffer_aff\|s56_c_price_induced_aff" modules/module_56.md` → `40, 41, 257, 287, 310`.
**Fix**: cite `modules/module_56.md:40-41` (parameter table) and `:287,310` (buffer).

---

### CDR-17 — 🟡 Minor — `realization` / invented identifier in an example
**Doc** (`circular_dependency_resolution.md:593`):
```gams
vm_area.up(j,kcr,"irrigated")$(pm_water_avail(j) < threshold) = 0;
* Does NOT create new dependency (just uses existing pm_water_avail)
```
and `:608` `pm_yields(j,kcr) = base_yield * irrigation_factor(vm_area(j,kcr,"irrigated"));`

**Reality**: neither `pm_water_avail` nor `pm_yields` exists anywhere in the model. The word
"existing" asserts otherwise. The real water-availability interface is
`im_wat_avail(t,wat_src,j)` (`modules/43_water_availability/total_water_aug13/declarations.gms:9`);
the yield interfaces are `vm_yld` (14) and `pm_yields_semi_calib` (14).

**Verify**: `rg -n "pm_water_avail|pm_yields\b" <develop>/modules/ <develop>/core/` → no match;
positive control `rg -c "pm_yields_semi_calib" .../14_yields/managementcalib_aug19/declarations.gms` → 1.
**Fix**: use `im_wat_avail(t,"surface",j)` and `vm_yld`, or mark the block explicitly as
illustrative pseudocode with placeholder names.

---

## Deferred (not verified — no bug recorded)

- **"26 circular dependency cycles"** (`:11`, `:749`, `:1036`): a doc-internal figure inherited from
  `core_docs/Module_Dependencies.md`; re-deriving it requires an actual SCC run over the interface
  graph, which I did not perform. The doc's own §8.2 concedes only 4 are documented.
- **§8.2 speculative cycles C5-C10** (`:753-758`): explicitly labelled "Suspected"/"Inferred".
  C10 (14-13-12) looks unlikely (module 12 reads no 13/14 interface), but the hedged framing means
  a bug record would be a false positive.
- **"GAMS reports circular dependencies during compilation … `*** WARNING: Circular reference
  detected between modules X and Y`"** (`:501-503`, `:641-643`): the string appears nowhere in the
  MAgPIE tree, and GAMS has no notion of MAgPIE "modules" (they are `$include` text), so a
  module-named warning cannot be emitted — but I cannot verify GAMS compiler behaviour offline, so
  no bug is filed. Worth a targeted check by someone with GAMS docs.
- **R/magpie4 verification snippets** (`:257-263`, `:307-312`, `:358-363`, `:417-428`, `:530-565`,
  `:838-851`): `AEI(gdx, …)`, `land_conservation(gdx, …)`, `costs(gdx, components="reward_cdr_aff")`,
  `gdx$status$solve_status` etc. were not checked against the pinned magpie4 clone (outside this
  lens's ground truth).
- **§4.1 reliability percentages (100%/95%/70%)** and **§6.3 "1-3 hours"**: not code-checkable.
- **§5.1 "Visualize using GraphViz (files in `/tmp/magpie_analysis/`)"**: points at a scratch
  directory that is not part of the repo; housekeeping, not a code claim.
- **§3.3 bracket `[30]` on "constraint on vm_area(j,kcr,"irrigated")"** (`:336`): the binding
  constraint `q41_area_irrig` lives in module 41, and the default croparea realization
  `simple_apr24` lists `vm_AEI` in `not_used.txt`, but the doc's `[NN]` brackets are ambiguous
  between "module that owns the variable" and "module where the step happens", so no separate bug —
  covered by CDR-2's rewrite.
- **§3.3 code block rendering `vm_AEI(j2) =g= sum(kcr, vm_area(...))`** (`:351`): mathematically
  identical to `q41_area_irrig`'s `=l=` with the sides swapped; not recorded (naming the equation
  would still improve it).
