# R60 Depth Audit — `modules/module_34.md` — lens: `config_realization`

**Auditor**: adversarial depth-first, single doc
**Ground truth**: MAgPIE `develop` read-only worktree, HEAD `2c02843ec`
**Config source of truth**: `config/default.cfg`
**Role map**: `audit/integrated/depth_rolemap.json`
**Claims verified**: 47
**Bugs confirmed**: 9 (1 Critical, 2 Major, 4 Minor, 2 Informational)

---

## 0. Lens entry — realization & switch inventory (all CLEAN)

| Doc claim | Doc line | Code | Verdict |
|---|---|---|---|
| Realizations = `exo_nov21`, `static` | 4 | `ls modules/34_urban/` → `exo_nov21`, `static`, `module.gms` | ✅ |
| Default = `exo_nov21` | 4, 10-11, 43 | `config/default.cfg:1147` `cfg$gms$urban <- "exo_nov21"  # def = exo_nov21` | ✅ |
| Doc **leads with** the default | 43 | § "1. exo_nov21 (Default)" precedes "2. static" | ✅ |
| `c34_urban_scenario` default `"SSP2"` | 210-213 | `modules/34_urban/exo_nov21/input.gms:8` `$setglobal c34_urban_scenario SSP2`; `config/default.cfg:1150` `cfg$gms$c34_urban_scenario <- "SSP2"  # def = SSP2` | ✅ |
| Options SSP1–SSP5 | 211, 177 | `exo_nov21/sets.gms:9-10` `urban_scen34 / SSP1, SSP2, SSP3, SSP4, SSP5 /`; `input.gms:9`; `default.cfg:1151` | ✅ |
| `s34_urban_deviation_cost` = 1e6 USD17MER/ha | 26, 51, 97, 111, 217-219 | `exo_nov21/input.gms:13` `... (USD17MER per ha) / 1e+06 /` — **not** exposed in `default.cfg` (correctly filed under "Scalar Parameters", not "Configuration Switches") | ✅ |
| `vm_cost_urban.scale(j) = 1e3` | 112, 519 | `exo_nov21/scaling.gms:8` | ✅ |
| Equation count 5 / 0 | 5, 533-538 | `exo_nov21/declarations.gms:18-24` (5 eqs); `static/` has no `equations.gms` | ✅ |
| All 5 formulas verbatim | 69, 90, 105, 124, 153 | `exo_nov21/equations.gms:17-18, 20-21, 25-26, 30-31, 34-35` | ✅ exact character match |
| `static` fixes 4 vars in presolve | 59 | `static/presolve.gms:9` (`vm_land`), `:10` (`vm_carbon_stock`), `:12` (`vm_bv`), `:14` (`vm_cost_urban`) | ✅ |
| `static` eliminates 5 eqs + 2 vars; `vm_cost_urban` persists fixed to 0 | 490 | `static/declarations.gms:9-11` declares it; `static/presolve.gms:14` `vm_cost_urban.fx(j) = 0;` | ✅ |
| `vm_cost_urban` → Module 11 | 114, 284, 471, 544 | role map `{declared_in: 34_urban, populated_by:[34], read_by:[11,34]}`; `modules/11_costs/default/equations.gms:45` `+ sum(cell(i2,j2), vm_cost_urban(j2))` | ✅ |
| `vm_bv` → Module 44 | 200, 292, 546 | role map `{declared_in: 44_biodiversity, read_by:[44]}`; `modules/44_biodiversity/bii_target/equations.gms:16` | ✅ |
| `vm_carbon_stock` **declared in M56, not M52** | 288 | role map `declared_in: 56_ghg_policy`; `modules/56_ghg_policy/price_aug22/declarations.gms` | ✅ (good catch already in doc) |
| `q52_emis_co2_actual` / `q56_emis_pricing_co2` names | 288 | `modules/52_carbon/normal_dec17/equations.gms:16`; `modules/56_ghg_policy/price_aug22/equations.gms:19` | ✅ |
| M52 & M56 read `vm_carbon_stock` in **parallel** (not serial hand-off) | 288 | both build the same `sum((cell,emis_land(...)), pcm_carbon_stock - vm_carbon_stock)` independently | ✅ (MANDATE 21 satisfied) |
| Presolve bounds t=1 / t>1 | 249-258, 510-512 | `exo_nov21/presolve.gms:10-15` | ✅ values correct (range cites off — see BUG-08) |
| `pcm_land(j,"urban") = i34_urban_area("y1995",j)` | 179 | `exo_nov21/preloop.gms:17`; effective because `start` phase (`core/calculations.gms:13`) precedes `preloop` (`:15`) | ✅ |
| `vm_bv.l` init in preloop | 167 | `exo_nov21/preloop.gms:20-21` | ✅ |
| Nitrogen / Water / Food non-participation | 306 | urban not referenced in 42/43/15/16/50-budget path — `v50_nr_deposition(i2,"urban")` is computed (`modules/50_nr_soil_budget/macceff_aug22/equations.gms:88-90`) but only the `"crop"` and `"past"` instances feed the budget (`:32`, `:80`) | ✅ (see DEFER-3) |

---

## 1. BUGS

---

### BUG-01 — **CRITICAL** — Urban carbon stocks are **not** zero: only the *aboveground* pools are fixed to 0; urban **soil carbon is non-zero and emits CO2**

**bug_class**: `set_membership`
**doc_line**: `module_34.md:33` (and 28, 289, 304, 361, 366)
**confirmed**: ✅ true

**Claim in doc**

> `module_34.md:33` — "**Does NOT include urban land carbon stocks** - assumed zero due to missing data"
> `module_34.md:28` — "**Fixes urban carbon stocks to zero** (no data available on urban land carbon density) (`presolve.gms:8`)"
> `module_34.md:304` — "**Carbon Balance**: ⚠️ **LIMITATION** - Urban land carbon set to **ZERO** (no data for urban vegetation)."
> `module_34.md:289` — "Urban land contributes zero to carbon balance (data limitation)"
> `module_34.md:366` — "Carbon emissions from land conversion to urban UNDER-estimated (only previous land's carbon counted, not urban carbon accumulation)"

**Reality in code**

Module 34 fixes **only the `ag_pools` slice**:

```
modules/34_urban/exo_nov21/presolve.gms:8
vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0;
```

and `ag_pools` is a **two-member subset** of `c_pools`:

```
modules/56_ghg_policy/price_aug22/sets.gms:209-210
   ag_pools(c_pools) Above ground carbon pools
         / vegc, litc /
```

`c_pools` is `/vegc, litc, soilc/` (`core/sets.gms:325`). The **`soilc` slice for urban is never fixed** — an exhaustive search finds exactly two `vm_carbon_stock` fixations in the whole model for urban, both `ag_pools`-restricted (`exo_nov21/presolve.gms:8`, `static/presolve.gms:10`).

Instead, urban soil carbon is **populated with a non-zero value by Module 59 (SOM)**, whose default realization is `cellpool_jan23` (`config/default.cfg:1937`):

```
modules/59_som/cellpool_jan23/sets.gms:10-11
noncropland59(land) Soil carbon conserving landuse types
/past, forestry, primforest, secdforest, other, urban/          <-- urban IS a member

modules/59_som/cellpool_jan23/equations.gms:61-64
q59_carbon_soil(j2,land,stockType) ..
                vm_carbon_stock(j2, land,"soilc",stockType)
                =e= v59_som_pool(j2, land) + vm_land(j2, land) *
                     sum(ct,i59_subsoilc_density(ct,j2));

modules/59_som/cellpool_jan23/equations.gms:30-33   (target for urban)
q59_som_target_noncropland(j2,noncropland59) ..
              v59_som_target(j2,noncropland59)
              =e= vm_land(j2,noncropland59) * sum(ct,f59_topsoilc_density(ct,j2));
```

Initialisation is likewise non-zero:

```
modules/59_som/cellpool_jan23/preloop.gms:19-20
pc59_som_pool(j,noncropland59) = f59_topsoilc_density("y1995",j) * pm_land_start(j,noncropland59);

modules/59_som/cellpool_jan23/preloop.gms:33-35
pcm_carbon_stock(j,noncropland59,"soilc",stockType) =
  fm_carbon_density("y1995",j,noncropland59,"soilc") * pm_land_start(j,noncropland59);
vm_carbon_stock.l(j,noncropland59,"soilc",stockType) = pcm_carbon_stock(j,noncropland59,"soilc",stockType);
```

and Module 52 **deliberately supplies a non-zero urban soil carbon density**, with an explicit code comment:

```
modules/52_carbon/normal_dec17/input.gms:33-35
* Fix urban area soilc to natural land soilc as long as preprocessed
* fm_carbon_density does not provide meaningful numbers for urban.
fm_carbon_density(t_all,j,"urban","soilc") = fm_carbon_density(t_all,j,"other","soilc")
```

Finally, the urban soil pool **does reach the emissions accounting**, because `urban_soilc` is a member of `emis_oneoff` and is mapped in `emis_land`:

```
core/sets.gms:314-318   emis_oneoff(...) / ... urban_vegc, urban_litc, urban_soilc, other_vegc, ... /
core/sets.gms:348-350   urban_vegc . (urban) . (vegc)
                        urban_litc . (urban) . (litc)
                        urban_soilc . (urban) . (soilc)
```

which is exactly the set `q52_emis_co2_actual` and `q56_emis_pricing_co2` sum over
(`modules/52_carbon/normal_dec17/equations.gms:16-19`, `modules/56_ghg_policy/price_aug22/equations.gms:19-22`).

**Consequence**: in a *default* run, urban land carries a soil-carbon stock proportional to `vm_land(j,"urban")` × natural-reference topsoil+subsoil density, and urban expansion/contraction produces `urban_soilc` CO2 emissions that are both reported (M52) and **priced** (M56). Every "urban carbon = zero" statement in the doc is wrong for 1 of the 3 carbon pools — and `soilc` is the *largest* pool for non-forest land. A user reading this doc would wrongly conclude urban land is carbon-inert and, e.g., wrongly attribute an urban CO2 line item in `report.mif` to a bug.

**file_evidence**: `modules/34_urban/exo_nov21/presolve.gms:8` + `modules/56_ghg_policy/price_aug22/sets.gms:209-210` + `modules/59_som/cellpool_jan23/sets.gms:11` + `modules/59_som/cellpool_jan23/equations.gms:61-64` + `core/sets.gms:350`

**verify_cmd**
```
$ rg -n 'vm_carbon_stock.*"urban"' /tmp/magpie_develop_ro/modules/
  modules/34_urban/exo_nov21/presolve.gms:8: vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0;
  modules/34_urban/static/presolve.gms:10:   vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0;
  -> only these two; both restricted to ag_pools

$ grep -n "ag_pools(c_pools)\|/ vegc, litc /" modules/56_ghg_policy/price_aug22/sets.gms
  209:   ag_pools(c_pools) Above ground carbon pools
  210:         / vegc, litc /

$ grep -n "noncropland59(land)\|/past, forestry" modules/59_som/cellpool_jan23/sets.gms
  10:noncropland59(land) Soil carbon conserving landuse types
  11:/past, forestry, primforest, secdforest, other, urban/

$ grep -n "urban_soilc" core/sets.gms
  310, 318 (emis_source / emis_oneoff members), 350 (urban_soilc . (urban) . (soilc))
```

**proposed_fix**
Replace the blanket "zero" language throughout. Suggested wording:

- `:28` → "**Fixes urban *aboveground* carbon stocks to zero** — `vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0` (`modules/34_urban/exo_nov21/presolve.gms:8`); `ag_pools = {vegc, litc}` (`modules/56_ghg_policy/price_aug22/sets.gms:209-210`). The `soilc` pool is **not** fixed here."
- `:33` → "**Does NOT set urban aboveground carbon** (vegc, litc fixed to 0, no data). Urban **soil** carbon *is* modelled — by Module 59 (`cellpool_jan23`, default), since `urban ∈ noncropland59` (`modules/59_som/cellpool_jan23/sets.gms:11`)."
- `:289`, `:304`, `:366` → state that urban contributes zero *aboveground* carbon but a non-zero, area-proportional *soil* carbon stock, and that `urban_soilc` CO2 is both reported (`q52_emis_co2_actual`) and priced (`q56_emis_pricing_co2`) because `urban_soilc ∈ emis_oneoff` (`core/sets.gms:318, 350`).
- Add a cross-reference to `cross_module/carbon_balance_conservation.md`.

---

### BUG-02 — **MAJOR** — Consumer/producer set for the urban `vm_carbon_stock` slice omits Module 59, and the `*` wildcard falsely asserts all pools are 0

**bug_class**: `attribution_populate`
**doc_line**: `module_34.md:473`
**confirmed**: ✅ true

**Claim in doc**

> `module_34.md:473-474` —
> "- **Module 52 (Carbon)**: Receives vm_carbon_stock(j,"urban",\*) = 0 for carbon emissions accounting
>  - **Module 56 (GHG Policy)**: Receives vm_carbon_stock(j,"urban",\*) = 0 for emission pricing"
> `module_34.md:196-198` — "vm_carbon_stock(j,"urban",ag_pools,stockType) … To: Module 52 … and Module 56 … Fixed to zero"
> `module_34.md:288` — "Both read vm_carbon_stock(j,"urban",ag_pools,stockType) (the urban slice, fixed to 0)"

**Reality in code**

Role map (`audit/integrated/depth_rolemap.json`):

```json
"vm_carbon_stock": {
  "declared_in": "56_ghg_policy",
  "populated_by": ["29","31","32","34","35","59"],
  "read_by":      ["52","56","59"]
}
```

Module **59 is both a populator and a reader** and is absent from the doc's list — and, per BUG-01, 59 is precisely the module that owns the urban `soilc` slice the doc claims is zero:

- populates: `modules/59_som/cellpool_jan23/equations.gms:61-64` (`q59_carbon_soil` LHS, `land` includes `urban`)
- reads (solution level): `modules/59_som/cellpool_jan23/postsolve.gms:13` `pcm_carbon_stock(j,land,"soilc",stockType) = vm_carbon_stock.l(j,land,"soilc",stockType);`
  (invisible to a `vm_carbon_stock(` grep — found only via the `.l` attribute form)

The `*` in `vm_carbon_stock(j,"urban",*) = 0` reads as "all pools", which is false for `soilc`. Module 34's own fixation index is `ag_pools`, correctly written at `:196` and `:288` but discarded at `:473-474`.

The same omission appears in the "Provides To" roll-up:

> `module_34.md:318` — "**Provides To**: Module 10 (Land), Module 11 (Costs …), Module 22 (Conservation - potentially), Module 44 (Biodiversity …)"

which omits 52, 56 **and** 59 entirely, even though 52 and 56 are named at `:288` and `:473-474`. Module 59 also directly reads `vm_land(j,"urban")` (`q59_som_target_noncropland` over `noncropland59 ∋ urban`, `modules/59_som/cellpool_jan23/equations.gms:30-33`), so it is a direct downstream consumer on two interfaces, not a transitive one.

**file_evidence**: `modules/59_som/cellpool_jan23/equations.gms:61-64`; `modules/59_som/cellpool_jan23/postsolve.gms:13`; `modules/59_som/cellpool_jan23/equations.gms:30-33`

**verify_cmd**
```
$ python3 -c "import json;d=json.load(open('audit/integrated/depth_rolemap.json'));print(d['vm_carbon_stock'])"
  {'declared_in': '56_ghg_policy', 'populated_by': ['29','31','32','34','35','59'], 'read_by': ['52','56','59']}

$ rg -n "vm_carbon_stock" /tmp/magpie_develop_ro/modules/59_som/
  cellpool_jan23/postsolve.gms:13  pcm_carbon_stock(j,land,"soilc",stockType) = vm_carbon_stock.l(j,land,"soilc",stockType);
  cellpool_jan23/preloop.gms:35    vm_carbon_stock.l(j,noncropland59,"soilc",stockType) = ...
  cellpool_jan23/equations.gms:62  vm_carbon_stock(j2, land,"soilc",stockType)
  (BOTH-endpoints grep: `vm_carbon_stock(` AND `vm_carbon_stock.` -> M59 confirmed on both roles)
```

**proposed_fix**
- `:473-474` → replace `vm_carbon_stock(j,"urban",*) = 0` with `vm_carbon_stock(j,"urban",ag_pools,stockType) = 0` and add "(aboveground pools only — `vegc`, `litc`; the `soilc` slice is populated by Module 59)".
- Add a fourth bullet under "Downstream Modules" (`:469-474`) and to "Provides To" (`:318`):
  "**Module 59 (SOM)**: populates `vm_carbon_stock(j,"urban","soilc",stockType)` via `q59_carbon_soil` and reads `vm_land(j,"urban")` via `q59_som_target_noncropland` (`urban ∈ noncropland59`)."
- `:318` → add Modules 52, 56, 59 to the "Provides To" list so it agrees with `:288` and `:473-474`.

---

### BUG-03 — **MAJOR** — "Upstream Modules … None" is false (M09, M10, M44 all supply Module 34), and contradicts the doc's own "Depends On" line 6 lines later

**bug_class**: `attribution_read`
**doc_line**: `module_34.md:276`
**confirmed**: ✅ true

**Claim in doc**

> `module_34.md:274-276` — "### Upstream Modules (provide data to Module 34)
>  None - Module 34 is a data provider, reads only from external input files (LUH3)"

**Reality in code** — Module 34 reads three interface objects owned by other modules, plus one core-land parameter:

| Object | Owner (declaration) | Read by M34 at |
|---|---|---|
| `sm_fix_SSP2` (scalar, `/ 2025 /`) | `modules/09_drivers/aug17/input.gms:22` | `modules/34_urban/exo_nov21/preloop.gms:10` |
| `fm_bii_coeff(bii_class44,potnatveg)` | `modules/44_biodiversity/bii_target/input.gms:17` (default realization, `config/default.cfg:1438`) | `exo_nov21/equations.gms:35`, `exo_nov21/preloop.gms:21`, `static/presolve.gms:12` |
| `fm_luh2_side_layers(j,luh2_side_layers10)` | `modules/10_land/landmatrix_dec18/input.gms:19` | `exo_nov21/equations.gms:35`, `exo_nov21/preloop.gms:21`, `static/presolve.gms:12` |
| `pcm_land(j,land)` | `modules/10_land/landmatrix_dec18/declarations.gms:11`, initialised `start.gms:8,11` | `static/presolve.gms:9,12` (**static's only source of urban area**) |

That `sm_fix_SSP2` is a *module input* of 34 is confirmed by MAgPIE's own interface bookkeeping: `modules/34_urban/static/not_used.txt:2` reads `sm_fix_SSP2, input, not needed` — a realization can only list an object there if it is declared an input of the module.

The doc contradicts itself 44 lines later:

> `module_34.md:320` — "**Depends On**: Module 09 (Drivers - LUH3 scenarios)"

**file_evidence**: `modules/09_drivers/aug17/input.gms:22`; `modules/34_urban/exo_nov21/preloop.gms:10`; `modules/44_biodiversity/bii_target/input.gms:17`; `modules/10_land/landmatrix_dec18/input.gms:19`; `modules/34_urban/static/not_used.txt:2`

**verify_cmd**
```
$ rg -n "sm_fix_SSP2" /tmp/magpie_develop_ro/modules/09_drivers/ /tmp/magpie_develop_ro/modules/34_urban/
  modules/09_drivers/aug17/input.gms:22:  sm_fix_SSP2  year until which all parameters are fixed to SSP2 values (year) / 2025 /
  modules/34_urban/exo_nov21/preloop.gms:10: if(m_year(t_all) <= sm_fix_SSP2,
  modules/34_urban/static/not_used.txt:2: sm_fix_SSP2, input, not needed

$ rg -n "fm_bii_coeff|fm_luh2_side_layers" /tmp/magpie_develop_ro/modules/44_biodiversity/bii_target/input.gms /tmp/magpie_develop_ro/modules/10_land/landmatrix_dec18/input.gms
  modules/44_biodiversity/bii_target/input.gms:17: table fm_bii_coeff(bii_class44,potnatveg) ...
  modules/10_land/landmatrix_dec18/input.gms:19:   table fm_luh2_side_layers(j,luh2_side_layers10) ...
```

**proposed_fix**
Rewrite `:274-276` as:

> ### Upstream Modules (provide data to Module 34)
> 1. **Module 09 (Drivers)** — `sm_fix_SSP2` (`modules/09_drivers/aug17/input.gms:22`, default 2025): the year until which all scenarios are harmonised to SSP2. Read at `modules/34_urban/exo_nov21/preloop.gms:10`. Listed as `not needed` by `static` (`modules/34_urban/static/not_used.txt:2`).
> 2. **Module 44 (Biodiversity)** — `fm_bii_coeff("urban",potnatveg)` (`modules/44_biodiversity/bii_target/input.gms:17`, default realization).
> 3. **Module 10 (Land)** — `fm_luh2_side_layers(j,potnatveg)` (`modules/10_land/landmatrix_dec18/input.gms:19`) and `pcm_land(j,"urban")` (`modules/10_land/landmatrix_dec18/start.gms:8,11`), the latter being `static`'s only source of urban area.
>
> The urban *trajectory* itself is not from another module: it comes from M34's own input file `f34_urbanland.cs3` (`modules/34_urban/exo_nov21/input.gms:16-19`).

Also fix `:320` — see BUG-09.

---

### BUG-04 — **MINOR** — `static`'s `pcm_land` is attributed to "core initialization"; it is Module 10's `start` phase

**bug_class**: `attribution_populate`
**doc_line**: `module_34.md:515`
**confirmed**: ✅ true

**Claim in doc**

> `module_34.md:515` — "**All t**: vm_land.fx(j,"urban") = pcm_land(j,"urban") (fixed to the 1995 baseline; **static reads pcm_land from core initialization** and does not use M34's i34_urban_area parameter)"

**Reality in code** — `pcm_land` is declared and populated entirely inside **Module 10**, not in `core/`:

```
modules/10_land/landmatrix_dec18/declarations.gms:11
 pcm_land(j,land)  Land area in previous time step including possible changes after optimization (mio. ha)

modules/10_land/landmatrix_dec18/start.gms:8
pm_land_start(j,land) = f10_land("y1995",j,land);
modules/10_land/landmatrix_dec18/start.gms:11
pcm_land(j,land) = pm_land_start(j,land);
```

Role map agrees: `"pcm_land": {"declared_in": "10_land", "populated_by": ["10","32","34","35"], ...}`. `core/` contains no `pcm_land` assignment. The second half of the doc's claim ("does not use M34's `i34_urban_area`") is **correct** — `static` has no `preloop` phase (`modules/34_urban/static/realization.gms:17-19` includes only `declarations`, `presolve`, `postsolve`), so `modules/34_urban/exo_nov21/preloop.gms:17` never runs and the urban slice keeps M10's `f10_land("y1995",...)` value.

**file_evidence**: `modules/10_land/landmatrix_dec18/start.gms:8,11`; `modules/10_land/landmatrix_dec18/declarations.gms:11`

**verify_cmd**
```
$ rg -n "pcm_land" /tmp/magpie_develop_ro/modules/10_land/landmatrix_dec18/*.gms
  start.gms:11: pcm_land(j,land) = pm_land_start(j,land);
  declarations.gms:11: pcm_land(j,land)  Land area in previous time step ...
$ rg -n "pcm_land" /tmp/magpie_develop_ro/core/   ->  (no matches)
$ rg -n "vm_land" /tmp/magpie_develop_ro/core/    ->  core/macros.gms:13  (POSITIVE CONTROL: search does work in core/, so the pcm_land zero is real)
```

**proposed_fix**
`:515` → "…fixed to `pcm_land(j,"urban")`, which **Module 10** initialises in its `start` phase from the LUH land-initialisation file (`modules/10_land/landmatrix_dec18/start.gms:8,11`: `pm_land_start(j,land) = f10_land("y1995",j,land); pcm_land(j,land) = pm_land_start(j,land);`). `static` has no `preloop` phase (`modules/34_urban/static/realization.gms:17-19`), so it never touches `i34_urban_area`."

---

### BUG-05 — **MINOR** — "urban land cannot convert back" is stated as a model property; nothing in the code enforces it

**bug_class**: `mechanism`
**doc_line**: `module_34.md:37`
**confirmed**: ✅ true (for the code facts; the practical outcome depends on input data — see caveat)

**Claim in doc**

> `module_34.md:37` — "**Does NOT model urban-rural land transitions** - expansion is one-way (urban land cannot convert back)"
> `module_34.md:384` — "**What's missing**: Urban land cannot convert back to non-urban uses"

**Reality in code** — urban contraction is fully representable and, if the prescribed trajectory fell, would be *forced*:

```
modules/34_urban/exo_nov21/presolve.gms:13
  vm_land.lo(j,"urban") = 0;            <-- explicitly permits shrinking to zero (t>1)

modules/34_urban/exo_nov21/equations.gms:30-31
q34_urban_land(i2) .. sum(cell(i2,j2), vm_land(j2,"urban")) =e= sum((ct,cell(i2,j2)), i34_urban_area(ct,j2));
                                       ^^^ equality: urban must FALL if i34_urban_area falls

modules/10_land/landmatrix_dec18/equations.gms:23-25, 35-38
q10_transition_from(j2,land_from) .. sum(land_to, vm_lu_transitions(j2,land_from,land_to)) =e= pcm_land(j2,land_from);
q10_landreduction(j2,land_from)  .. vm_landreduction(j2,land_from) =e= sum(land_to$(not sameas(land_from,land_to)), vm_lu_transitions(j2,land_from,land_to));
```

`land_from`/`land_to` range over the full `land` set, which includes `urban`; there is no `$` filter excluding urban from the transition matrix. So `urban → other` transitions exist as decision variables and `vm_landreduction(j,"urban")` is a defined quantity.

The doc's own Limitation #4 body gets this right — `module_34.md:386` correctly attributes the one-way behaviour to "`i34_urban_area` monotonically increasing in all SSPs", i.e. to the **input data**, not to model structure. The two headline bullets (`:37`, `:384`) drop that qualifier and read as structural impossibility.

**Caveat**: I could not verify the monotonicity of `f34_urbanland.cs3` — the file is not in the repo (`modules/34_urban/exo_nov21/input/` contains only a `files` manifest; the `.cs*` is unpacked from `input.tgz` at run start). So the *practical* claim may well hold; the *structural* claim does not.

**file_evidence**: `modules/34_urban/exo_nov21/presolve.gms:13`; `modules/34_urban/exo_nov21/equations.gms:30-31`; `modules/10_land/landmatrix_dec18/equations.gms:23-25,35-38`

**verify_cmd**
```
$ sed -n '10,16p' modules/34_urban/exo_nov21/presolve.gms
  if(ord(t) = 1, vm_land.fx(j,"urban") = i34_urban_area(t,j); else
    vm_land.lo(j,"urban") = 0;  vm_land.l(j,"urban") = i34_urban_area(t,j);  vm_land.up(j,"urban") = Inf; );
$ cat -n modules/10_land/landmatrix_dec18/equations.gms   -> q10_transition_from / q10_landreduction over full `land`, no urban exclusion
$ ls modules/34_urban/exo_nov21/input/   ->  files       (the .cs3 is a run-time product, not in git)
```

**proposed_fix**
`:37` → "**Does NOT model *endogenous* urban→rural reversion** — urban area is pinned to the prescribed regional total. Nothing in the code forbids contraction (`vm_land.lo(j,"urban") = 0`, `modules/34_urban/exo_nov21/presolve.gms:13`; `q10_landreduction` covers `urban`); with the default SSP trajectories the prescribed total does not fall, so urban land does not shrink in practice."
`:384` → same qualifier ("the *input trajectory* never declines; the model would follow a declining trajectory if given one").

---

### BUG-06 — **MINOR** — `static` line count understated by ~65% (claimed ~40, actual 66) under the doc's own counting convention

**bug_class**: `formula`
**doc_line**: `module_34.md:6`
**confirmed**: ✅ true

**Claim in doc**

> `module_34.md:6` — "**Lines of Code**: ~217 (exo_nov21), ~40 (static)"
> `module_34.md:557` — "**static structure** (4 files, ~40 lines)"
> `module_34.md:600` — "**Lines Documented**: 217 (exo_nov21) + 40 (static)"

**Reality in code**

```
exo_nov21  9 .gms files  220 lines   (doc: ~217  -> consistent, headers INCLUDED)
static     4 .gms files   66 lines   (doc: ~40   -> off by 65%)
```

The exo_nov21 figure (217 vs 220) can only be reproduced by counting *with* the 6-line AGPL headers. Under that same convention `static` is 66, not 40. (Excluding headers gives exo=166 / static=42 — so no single convention reproduces both stated numbers.) File counts (9 / 4 `.gms`) are correct.

**file_evidence**: `modules/34_urban/exo_nov21/*.gms` (220); `modules/34_urban/static/*.gms` (66)

**verify_cmd**
```
$ wc -l /tmp/magpie_develop_ro/modules/34_urban/exo_nov21/*.gms | tail -1
  220 total
$ wc -l /tmp/magpie_develop_ro/modules/34_urban/static/*.gms | tail -1
   66 total
```

**proposed_fix**
`:6`, `:557`, `:600` → "220 (exo_nov21, 9 `.gms` files) / 66 (static, 4 `.gms` files), AGPL headers included — measured `wc -l modules/34_urban/<realization>/*.gms` against develop `2c02843ec`." Per the repo's "no figure without an artifact" rule, note the measurement command inline.

---

### BUG-07 — **MINOR** — `Depends On: Module 09 (Drivers - **LUH3 scenarios**)`: M09 supplies only `sm_fix_SSP2`; the LUH3 data comes from M34's own input file

**bug_class**: `data_flow_direction`
**doc_line**: `module_34.md:320`
**confirmed**: ✅ true

**Claim in doc**

> `module_34.md:320` — "**Depends On**: Module 09 (Drivers - LUH3 scenarios)"

**Reality in code** — the only Module 09 object Module 34 reads is the scalar `sm_fix_SSP2`:

```
modules/09_drivers/aug17/input.gms:22
  sm_fix_SSP2   year until which all parameters are fixed to SSP2 values (year) / 2025 /

modules/34_urban/exo_nov21/preloop.gms:9-15
loop(t_all,
 if(m_year(t_all) <= sm_fix_SSP2,
  i34_urban_area(t_all, j) = f34_urbanland(t_all, j,"SSP2");
else
i34_urban_area(t_all, j) = f34_urbanland(t_all, j,"%c34_urban_scenario%");
 ););
```

The LUH3 urban trajectory is read by Module 34 from **its own** input table, not routed through Module 09:

```
modules/34_urban/exo_nov21/input.gms:16-19
table f34_urbanland(t_all, j, urban_scen34)   Urban land
$include "./modules/34_urban/exo_nov21/input/f34_urbanland.cs3"
```

M09's `%c09_pop_scenario%` / `%c09_gdp_scenario%` switches are *not* read by M34 (`rg -n "c09_" modules/34_urban/` → no matches; positive control: `rg -n "c34_" modules/34_urban/` → 2 matches). The doc's own `:8` comment in `preloop.gms` ("get the scenario GDP & Population data for iso countries") is a stale copy-paste in the *code*, and may be what seeded this.

**file_evidence**: `modules/09_drivers/aug17/input.gms:22`; `modules/34_urban/exo_nov21/preloop.gms:9-15`; `modules/34_urban/exo_nov21/input.gms:16-19`

**verify_cmd**
```
$ rg -n "c09_" /tmp/magpie_develop_ro/modules/34_urban/     -> (no matches)
$ rg -n "c34_" /tmp/magpie_develop_ro/modules/34_urban/     -> input.gms:8, preloop.gms:13   (positive control: search works)
$ grep -n "sm_fix_SSP2" modules/09_drivers/aug17/input.gms  -> 22:  sm_fix_SSP2 ... / 2025 /
```

**proposed_fix**
`:320` → "**Depends On**: Module 09 (Drivers) — **only** the scalar `sm_fix_SSP2` (`modules/09_drivers/aug17/input.gms:22`, default **2025**), the harmonisation year before which all SSP scenarios use SSP2 urban data. The LUH3 urban trajectory itself is M34's own input table `f34_urbanland` (`modules/34_urban/exo_nov21/input.gms:16-19`). Also Module 44 (`fm_bii_coeff`) and Module 10 (`fm_luh2_side_layers`, `pcm_land`)." Consider stating the `sm_fix_SSP2 = 2025` default at `:213` and `:225` too, where it is currently referenced by name only.

---

### BUG-08 — **INFORMATIONAL** — presolve citation ranges truncate by one line (`vm_land.up` at line 15 falls outside both cited ranges)

**bug_class**: `citation`
**doc_line**: `module_34.md:254`
**confirmed**: ✅ true

**Claim in doc**

> `module_34.md:254` — "**t>1 (optimization timesteps)** (`presolve.gms:12-14`)" followed by three bullets, the third of which is `vm_land.up(j,"urban") = Inf`
> `module_34.md:510` — "**exo_nov21** (`presolve.gms:11-14`)"

**Reality in code** — the `else` branch spans **13-15**, and the whole `if` block spans **10-16**:

```
modules/34_urban/exo_nov21/presolve.gms
 10  if(ord(t) = 1,
 11    vm_land.fx(j,"urban") = i34_urban_area(t,j);
 12  else
 13    vm_land.lo(j,"urban") = 0;
 14    vm_land.l(j,"urban")  = i34_urban_area(t,j);
 15    vm_land.up(j,"urban") = Inf;
 16  );
```

The doc's *per-bullet* line numbers at `:512` ("lines 13-14", "line 15") are correct; only the two range headers are short by one line. Content is otherwise exact.

**file_evidence**: `modules/34_urban/exo_nov21/presolve.gms:10-16`

**verify_cmd**
```
$ cat -n /tmp/magpie_develop_ro/modules/34_urban/exo_nov21/presolve.gms | sed -n '10,16p'
  (as quoted above)
```

**proposed_fix**
`:254` → `presolve.gms:13-15`; `:510` → `presolve.gms:11-15`.

---

### BUG-09 — **INFORMATIONAL** — Doc footer metadata is stale/unbacked: "Changes Since Last Verification: None (stable)" is false, and "60+ file citations" measures 55

**bug_class**: `other`
**doc_line**: `module_34.md:608`
**confirmed**: ✅ true

**Claims in doc**

> `module_34.md:605-608` — "**Last Verified**: 2025-10-13 … **Changes Since Last Verification**: None (stable)"
> `module_34.md:548` / `:601` — "**File Citations**: 60+ file:line citations throughout documentation ✓"

**Reality**

1. Module 34 *did* change after 2025-10-13: commit `da316ed4a` (2026-03-12) rewrote `exo_nov21/scaling.gms`, changing `vm_cost_urban.scale(j)` from `10e3` to `1e3`, `v34_cost1/2.scale` from `10e-4` to `1e-4`, and adding three new commented `.scale` lines (`q34_urban_cost1`, `q34_urban_cost2`, `q34_urban_land`). The doc *body* reflects the post-change values (`:112`, `:519`, `:524`), so the footer is simply out of date — but "None (stable)" is a checkable false statement.
2. Measured citation count: **55** backticked `file:line` references (31 unique), below the asserted "60+". Per the repo's "no figure without an artifact" rule this figure needs a re-runnable measurement or a softer wording.
3. Related: `:523-525` describes the commented-out scaling as `scaling.gms:9-10` only; the file now has commented `.scale` statements at **9-13** (five, not two).

**file_evidence**: commit `da316ed4a`, `modules/34_urban/exo_nov21/scaling.gms:8-13`

**verify_cmd**
```
$ git -C /tmp/magpie_develop_ro log --format="%ad %h %s" --date=short -- modules/34_urban/ | head -3
  2026-03-12 da316ed4a changelog entries
  2025-09-22 4211e1237 Makes LUH references more explicit
  2025-09-18 e8770b868 Changes irrigation, urban, and land_convservation settings and documentation to LUH3
$ git -C /tmp/magpie_develop_ro show da316ed4a -- modules/34_urban/
  -vm_cost_urban.scale(j) = 10e3;  +vm_cost_urban.scale(j) = 1e3;   (+3 new commented .scale lines)
$ grep -oE '`[a-zA-Z0-9_/.]+:[0-9]+(-[0-9]+)?`' modules/module_34.md | wc -l
  55
```

**proposed_fix**
- `:605-608` → "**Last Verified**: <date of this audit> against develop `2c02843ec`. **Changes since 2025-10-13**: `modules/34_urban/exo_nov21/scaling.gms` rewritten by `da316ed4a` (2026-03-12) — `vm_cost_urban.scale` `10e3 → 1e3`, three additional commented `.scale` statements added."
- `:548`, `:601` → "**File Citations**: 55 (`grep -oE '\`[A-Za-z0-9_/.]+:[0-9]+(-[0-9]+)?\`' modules/module_34.md | wc -l`)".
- `:523-525` → cite `scaling.gms:9-13` and list all five commented statements; drop or explicitly label as speculation the unsourced "Reason for disabling: Likely caused solver issues" (git shows these lines were never active in the recorded history — they were commented at `10e-4` before and `1e-4` after).

---

## 2. DEFERRED (not verifiable / no edit proposed)

1. **`:314` "Centrality: ~30 of 46 modules (moderate-low centrality)" and `:315` "Total Connections: 3-4"** — these come from the agent's own dependency analysis, not from GAMS. No artifact located in this session to re-derive them; the phrasing "~30 of 46 modules" is also ambiguous (rank? count of reachable modules?). Not flagged, but worth an owner check.
2. **`:242-245` SSP narrative characterisations** ("SSP1: Lower urban expansion", "SSP3: Higher urban sprawl", "SSP5: Rapid urbanization") — properties of `f34_urbanland.cs3`, which is not in the repo (`modules/34_urban/exo_nov21/input/` holds only a `files` manifest; the `.cs3` is unpacked from `input.tgz` at run start by `scripts/start_functions.R`). Cannot confirm or refute the ordering of the SSP trajectories.
3. **`:306` "All Other Laws: ❌ Does NOT participate (Food, Water, Nitrogen)"** — I did **not** flag this, but note that Module 50 formally reads `vm_land(j,"urban")`: `q50_nr_deposition(i2,land)` is declared over the full `land` set (`modules/50_nr_soil_budget/macceff_aug22/equations.gms:88-90`), so `v50_nr_deposition(i2,"urban")` is computed. It is a dangling quantity — only the `"crop"` (`:32`) and `"past"` (`:80`) instances enter the nitrogen budget — so the doc's substantive claim holds. Optional precision-improving note, not a defect.
4. **Module 39 (`i39_cost_establish(t,i,"urban") = s39_cost_establish_urban`, `modules/39_landconversion/calib/presolve.gms:16`; default `12300` USD17MER/ha, `config/default.cfg:1303`)** — urban expansion does incur land-conversion establishment costs, which sits awkwardly with `:36` "Does NOT interact with other modules dynamically - only reduces available land pool". Not flagged: M39 consumes `vm_landexpansion` from Module 10, so it is a **transitive**, not a direct, consumer of a Module-34 variable (MANDATE 17), and the doc statement mirrors the code's own `@limitations` text at `modules/34_urban/exo_nov21/realization.gms:12`. Worth a one-line "see also" cross-reference at the doc author's discretion.
5. **`config/default.cfg:1145` vs `modules/34_urban/static/realization.gms:9`** — the cfg comment says `static` is "fixed on 1995 patterns from **LUH3**" while `static/realization.gms:9` says "1995 from the **LUH2** data set [@hurtt2018luh2]". This is an inconsistency in the *MAgPIE code*, not in the doc (the doc follows `realization.gms`). Flagging upstream is out of scope here.
6. **`:448` / `:571` "publication pending as of Nov 2021"** — the LUH3 wording in `exo_nov21/realization.gms:8` was introduced by commits `e8770b868` / `4211e1237` (Sept 2025), not in Nov 2021; the "as of Nov 2021" attribution is therefore anachronistic. Too weak/interpretive to file as a bug.

---

## 3. Summary table

| ID | Sev | Class | Doc line | One-liner |
|---|---|---|---|---|
| BUG-01 | Critical | set_membership | 34:33 | Urban carbon is zero only for `ag_pools={vegc,litc}`; `soilc` is non-zero (M59) and emits priced CO2 |
| BUG-02 | Major | attribution_populate | 34:473 | `vm_carbon_stock(j,"urban",*) = 0` wildcard is false; M59 omitted from populator+reader sets |
| BUG-03 | Major | attribution_read | 34:276 | "Upstream Modules … None" false — M09 (`sm_fix_SSP2`), M44 (`fm_bii_coeff`), M10 (`fm_luh2_side_layers`, `pcm_land`) |
| BUG-04 | Minor | attribution_populate | 34:515 | `pcm_land` attributed to "core initialization"; it is M10 `landmatrix_dec18/start.gms:8,11` |
| BUG-05 | Minor | mechanism | 34:37 | "urban cannot convert back" not enforced anywhere (`vm_land.lo=0`; `q10_landreduction` covers urban) |
| BUG-06 | Minor | formula | 34:6 | `static` line count ~40 vs measured 66 (exo 217 vs 220 is fine) |
| BUG-07 | Minor | data_flow_direction | 34:320 | M09 supplies only `sm_fix_SSP2` (=2025), not "LUH3 scenarios" |
| BUG-08 | Informational | citation | 34:254 | presolve ranges truncate `vm_land.up` at line 15 (`12-14`→`13-15`, `11-14`→`11-15`) |
| BUG-09 | Informational | other | 34:608 | "Changes … None (stable)" false (`da316ed4a`, 2026-03-12); "60+ citations" measures 55 |
