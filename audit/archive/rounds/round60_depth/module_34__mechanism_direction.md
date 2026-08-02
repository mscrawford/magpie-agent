# Round 60 depth audit — `modules/module_34.md`

**Lens**: `mechanism_direction` (equation bodies, cross-module data-flow direction, mechanism-vs-parameterization, set membership)
**Ground truth**: MAgPIE `develop` read-only worktree @ `2c02843ec` ("Merge pull request #919 from alexkoberle/dyn_reg_tau")
**Default realization confirmed**: `config/default.cfg:1147` → `cfg$gms$urban <- "exo_nov21"` ✓ (doc leads with it correctly)
**Realization dirs verified**: `modules/34_urban/` → `exo_nov21`, `static` (2, matches doc)
**Claims verified**: 61
**Bugs confirmed**: 8 (1 Critical, 4 Major, 2 Minor, 1 Informational)

---

## Headline

The doc's single most-repeated factual claim — *urban land carbon is zero* — is **false for the soil carbon pool**, and this propagates through eight separate passages including the Conservation-Laws section, the Limitations section, the Module-Interactions section and the Verification-Summary checkmarks. Module 34 fixes only `ag_pools` = {`vegc`, `litc`}. Urban **soil** carbon is an endogenous model variable computed by Module 59, priced by Module 56, and emitted by Module 52 — and Module 52 contains an explicit line whose entire purpose is to give urban land a non-zero soil carbon density.

Secondary: the doc asserts Module 34 has **no upstream modules** (it has three), that urban→non-urban transition is structurally impossible (nothing in the code forbids it), and it omits Module 39's 12 300 USD17MER/ha urban establishment cost and Module 59 entirely from every interaction list.

---

## BUG-1 — Critical — `mechanism`

**Doc** (`module_34.md:304`):
> **Carbon Balance**: ⚠️ **LIMITATION** - Urban land carbon set to **ZERO** (no data for urban vegetation).

Same false generalization at `module_34.md:33`, `:289`, `:359-368`, `:473`, `:474`, `:545`, `:585`, `:593`.

**Reality in code.** Module 34 fixes **only the above-ground pools**:

- `modules/34_urban/exo_nov21/presolve.gms:8` — `vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0;`
- `modules/56_ghg_policy/price_aug22/sets.gms:209-210` — `ag_pools(c_pools) Above ground carbon pools / vegc, litc /`

The **`soilc` pool for urban land is endogenous and non-zero**, under *both* Module 59 realizations:

- default `cfg$gms$som <- "cellpool_jan23"` (`config/default.cfg:1937`)
  `modules/59_som/cellpool_jan23/equations.gms:61-64`:
  `q59_carbon_soil(j2,land,stockType) .. vm_carbon_stock(j2,land,"soilc",stockType) =e= v59_som_pool(j2,land) + vm_land(j2,land) * sum(ct,i59_subsoilc_density(ct,j2));`
  Domain is the full core `land` set — `core/sets.gms:250` `/ crop, past, forestry, primforest, secdforest, urban, other /` — with no `$`-exclusion. `urban` is also an explicit member of `noncropland59` (`modules/59_som/cellpool_jan23/sets.gms:10-11`), so it gets its own `q59_som_target_noncropland` target too.
- alternative `static_jan19`: `modules/59_som/static_jan19/equations.gms:17-19`
  `q59_soilcarbon_regular(j2,regularland59,stockType) .. vm_carbon_stock(j2,regularland59,"soilc",stockType) =e= sum(ct, vm_land(j2,regularland59) * fm_carbon_density(ct,j2,regularland59,"soilc"));`
  with `regularland59 / past, forestry, primforest, secdforest, urban /` (`modules/59_som/static_jan19/sets.gms:9-10`).

And Module 52 contains a line whose *only* purpose is to give urban land a meaningful non-zero soil carbon density — `modules/52_carbon/normal_dec17/input.gms:33-35`:

```
* Fix urban area soilc to natural land soilc as long as preprocessed
* fm_carbon_density does not provide meaningful numbers for urban.
fm_carbon_density(t_all,j,"urban","soilc") = fm_carbon_density(t_all,j,"other","soilc")
```

That non-zero urban soil carbon **reaches both emission accounting and emission pricing**, because the `emis_land` mapping contains `urban_soilc` (`core/sets.gms:350` — `urban_soilc . (urban) . (soilc)`), and both equations sum over `emis_land(...,land,c_pools)` — i.e. all three pools, not `ag_pools`:

- `modules/52_carbon/normal_dec17/equations.gms:16-19` (`q52_emis_co2_actual`)
- `modules/56_ghg_policy/price_aug22/equations.gms:12-15` (`q56_emis_pricing_co2`)

**Absence cross-check (2 methods + positive control).** `rg -n 'vm_carbon_stock\.fx' modules/` returns exactly three hits repo-wide (34 exo_nov21, 34 static, 31_past/static) — nothing zeroes urban `soilc`. `rg -n 'urban.*soilc|soilc.*urban' modules/` returns only the Module 52 *assignment* above. Positive control: `rg -c "vm_carbon_stock" modules/59_som/cellpool_jan23/equations.gms` → `1` (search works in that tree).

**Harm.** A reader who wants to lift the "no urban carbon" assumption would edit `modules/34_urban/exo_nov21/presolve.gms`. Adding `vm_carbon_stock.fx(j,"urban","soilc",stockType) = X` there **collides with `q59_carbon_soil`** (a fixed variable on the LHS of an equality) and makes the model infeasible. They would also wrongly conclude that forest→urban conversion loses no soil carbon in MAgPIE, when in fact the soil term is computed and priced.

**Proposed fix.** Replace every "urban carbon = zero" statement with the slice-qualified truth:
> Module 34 fixes only the **above-ground** urban carbon pools to zero — `vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0` with `ag_pools = {vegc, litc}` (`modules/56_ghg_policy/price_aug22/sets.gms:209-210`). Urban **soil** carbon is *not* zero: it is computed endogenously by Module 59 (`q59_carbon_soil`, default `cellpool_jan23`), using the same soil-carbon density as natural "other" land (`modules/52_carbon/normal_dec17/input.gms:35`), and it enters both `q52_emis_co2_actual` and `q56_emis_pricing_co2` through the `emis_land` member `urban_soilc` (`core/sets.gms:350`).

Correspondingly rewrite `:304` to "PARTIAL PARTICIPANT (soil pool only)", drop the `= 0` from the wildcard forms at `:473-474`/`:545`, and rewrite Limitation 2 (`:359-368`) — the "conversion to urban under-estimated because urban carbon is not accumulated" reasoning is wrong for `soilc`.

---

## BUG-2 — Major — `attribution_populate`

**Doc** (`module_34.md:545`):
> **Interface Variables**: All checked
> - vm_land(j,"urban") to Module 10 ✓
> - vm_cost_urban(j) to Module 11 ✓
> - vm_carbon_stock(j,"urban",*) to Module 52 ✓
> - vm_bv(j,"urban",potnatveg) to Module 44 ✓

Same incomplete set at `:185-202` ("Outputs to other modules"), `:278-294` ("Downstream Modules"), `:318` ("Provides To"), `:469-474` ("Related Modules → Downstream").

**Reality in code.** **Module 59 is missing from every one of those lists**, and it is a *direct* consumer/co-populator of two slices Module 34 owns:

- reads `vm_land(j2,"urban")` directly (via `land` / `noncropland59` / `regularland59`) — `modules/59_som/cellpool_jan23/equations.gms:31-34` and `:61-64`
- **populates** the complementary slice of the same interface variable: `vm_carbon_stock(j2,"urban","soilc",stockType)` — same equation. So the urban slice of `vm_carbon_stock` has **two owners**: M34 (ag_pools, by `.fx`) and M59 (soilc, by equation).

Two further set errors in the same block:

- The `*` wildcard in `vm_carbon_stock(j,"urban",*)` (`:473`, `:474`, `:545`) is wrong — M34 only owns `ag_pools`.
- `:318` ("**Provides To**: Module 10, Module 11, Module 22 (potentially), Module 44") **omits Modules 52 and 56**, which the same document lists at `:288` and `:473-474`. Internal contradiction.

Role-map cross-check (`audit/integrated/depth_rolemap.json`): `vm_carbon_stock` → `read_by: ['52','56','59']`, `populated_by: ['29','31','32','34','35','59']`; `vm_land` → `read_by: ['10','22','29','30','31','32','34','35','50','58','59']`. Both agree with the greps.

**Proposed fix.** Add Module 59 (`59_som`, default `cellpool_jan23`) to the Outputs / Downstream / Provides-To / Related-Modules lists with the note "reads `vm_land(j,'urban')` and populates the complementary `soilc` slice of `vm_carbon_stock(j,'urban',...)`". Replace `vm_carbon_stock(j,"urban",*)` with `vm_carbon_stock(j,"urban",ag_pools,stockType)` everywhere. Add Modules 52 and 56 to the `:318` "Provides To" line and update `:315` accordingly.

---

## BUG-3 — Major — `data_flow_direction`

**Doc** (`module_34.md:276`):
> ### Upstream Modules (provide data to Module 34)
> None - Module 34 is a data provider, reads only from external input files (LUH3)

Reinforced at `:315` ("depends on 1") and `:320` ("**Depends On**: Module 09 (Drivers - LUH3 scenarios)").

**Reality in code.** Module 34 reads **three** interface objects owned by other modules — and the doc itself lists two of them 95 lines earlier (`:181-183`), so the two passages contradict each other:

| Object read by M34 | Declared in | M34 read site |
|---|---|---|
| `fm_bii_coeff("urban",potnatveg)` | `modules/44_biodiversity/bii_target/input.gms:17` | `modules/34_urban/exo_nov21/equations.gms:35`, `preloop.gms:21` |
| `fm_luh2_side_layers(j2,potnatveg)` | `modules/10_land/landmatrix_dec18/input.gms:19` | `modules/34_urban/exo_nov21/equations.gms:35`, `preloop.gms:21` |
| `sm_fix_SSP2` | `modules/09_drivers/aug17/input.gms:22` (`/ 2025 /`) | `modules/34_urban/exo_nov21/preloop.gms:10` |

And the *direction* attached to Module 09 is wrong: LUH3 urban data does **not** come from Module 09. It is Module 34's own input table `f34_urbanland(t_all,j,urban_scen34)` loaded from `./modules/34_urban/exo_nov21/input/f34_urbanland.cs3` (`modules/34_urban/exo_nov21/input.gms:16-20`; file listed in `modules/34_urban/exo_nov21/input/files`). The only thing M34 takes from Module 09 is the scalar cut-off year `sm_fix_SSP2` = 2025.

There is also an **undocumented write in the reverse direction**: `modules/34_urban/exo_nov21/preloop.gms:17` sets `pcm_land(j,"urban") = i34_urban_area("y1995",j)`, and `pcm_land` is declared in Module 10 (`modules/10_land/landmatrix_dec18/declarations.gms:11`). Phase order confirms this is an override, not a read: `core/calculations.gms:13` runs the `start` phase (where `modules/10_land/landmatrix_dec18/start.gms:11` sets `pcm_land(j,land) = pm_land_start(j,land)`) **before** `core/calculations.gms:15` runs `preloop`. So M34 overwrites Module 10's urban initialization. Role map agrees: `pcm_land` → `populated_by: ['10','32','34','35']`.

**Proposed fix.** Replace `:276` with an explicit upstream table listing `fm_bii_coeff` (M44), `fm_luh2_side_layers` (M10) and `sm_fix_SSP2` (M09, `/2025/`); correct `:320` to "Module 09 (Drivers — supplies only the `sm_fix_SSP2` cut-off year; the LUH3 urban trajectory is Module 34's own input file `f34_urbanland.cs3`)"; correct `:315` from "depends on 1" to "depends on 3"; and add a line noting that M34 **writes** `pcm_land(j,"urban")` in `preloop`, overriding Module 10's `start`-phase initialization.

---

## BUG-4 — Major — `mechanism`

**Doc** (`module_34.md:37`, restated at `:382-386`):
> **Does NOT model urban-rural land transitions** - expansion is one-way (urban land cannot convert back)
> … **What's missing**: Urban land cannot convert back to non-urban uses

**Reality in code.** Nothing in the model forbids urban land from shrinking. This is a property of the *input trajectory*, not of the code — a parameterization-vs-mechanism conflation (AGENT.md three-check rule):

- `modules/34_urban/exo_nov21/presolve.gms:13` — `vm_land.lo(j,"urban") = 0;` (lower bound is zero, not the previous level)
- `modules/34_urban/exo_nov21/equations.gms:30-31` — `q34_urban_land(i2)` is an **equality** to whatever `i34_urban_area` prescribes. A declining prescribed trajectory would *force* urban land down, not be blocked.
- `modules/10_land/landmatrix_dec18/equations.gms:23-25` — `q10_transition_from(j2,land_from) .. sum(land_to, vm_lu_transitions(j2,land_from,land_to)) =e= pcm_land(j2,land_from);` covers `land_from = "urban"` with no exclusion, so urban→other transitions are representable in the land-transition matrix.

The doc's own `:386` half-concedes this ("with `i34_urban_area` monotonically increasing in all SSPs"), but `:37` and `:384` state it flatly as a model capability limit in the "What Module 34 does NOT do" / "What's missing" lists.

**Harm.** A user wanting an urban-shrinkage scenario would conclude they must change model *structure*, when in fact they only need to supply a declining `f34_urbanland.cs3` trajectory.

**Proposed fix.** Rewrite `:37` as: "**Does NOT itself restrict urban→non-urban transitions** — `vm_land.lo(j,'urban') = 0` and `q34_urban_land` is an equality, so urban land follows the prescribed trajectory in *either* direction; one-way expansion is a property of the SSP input data, not a code constraint." Rewrite Limitation 4 (`:382-393`) the same way and label the monotonicity statement as an unverified data property.

---

## BUG-5 — Major — `mechanism`

**Doc** (`module_34.md:36`, `:284-286`, `:341`, `:471`, `:496`): Module 34 "**Does NOT interact with other modules dynamically** - only reduces available land pool"; the cost narrative presents `vm_cost_urban(j)` as the sole cost consequence of urban land, and `:496` tells readers `vm_cost_urban(j)` "should be near-zero in feasible solutions".

**Reality in code.** Urban land **expansion carries a second, always-active cost** that the doc never mentions — Module 39 land-conversion establishment cost, 12 300 USD17MER/ha:

- `modules/39_landconversion/calib/input.gms:13` — `s39_cost_establish_urban … / 12300 /`
- `config/default.cfg:1303` — `cfg$gms$s39_cost_establish_urban <- 12300  # def = 10000 * 1.23`; realization default `cfg$gms$landconversion <- "calib"` (`config/default.cfg:1288`); `calib` is the only realization (`ls -d modules/39_landconversion/*/` → `calib`, `input` — `input` is a data dir, not a realization)
- `modules/39_landconversion/calib/presolve.gms:16` — `i39_cost_establish(t,i,"urban") = s39_cost_establish_urban;`
- `modules/39_landconversion/calib/equations.gms:12-15` — `q39_cost_landcon(j2,land) .. vm_cost_landcon(j2,land) =e= (vm_landexpansion(j2,land)*sum(...,i39_cost_establish(ct,i2,land)) - …) * annuity;` — domain is the full `land` set
- `modules/11_costs/default/equations.gms:20` — `+ sum((cell(i2,j2),land), vm_cost_landcon(j2,land))` enters the objective over all `land`, urban included

(Module 39 reaches urban via `vm_landexpansion` — Module 10's variable — so it is a **transitive**, not direct, consumer of `vm_land(j,"urban")`; the doc omission being flagged is the missing cost channel and the missing Module-39 entry, not a direct-consumer claim.)

**Proposed fix.** Add to the Data Flow / Module Interactions sections: "Urban land expansion additionally incurs Module 39 land-conversion establishment cost `i39_cost_establish(t,i,'urban') = s39_cost_establish_urban = 12300 USD17MER/ha` (`modules/39_landconversion/calib/input.gms:13`, `presolve.gms:16`), entering the objective via `vm_cost_landcon(j,'urban')` (`modules/11_costs/default/equations.gms:20`) — this is separate from, and normally much larger in aggregate than, `vm_cost_urban`." Soften `:36` accordingly (it currently paraphrases the code's own `@limitations` comment at `modules/34_urban/exo_nov21/realization.gms:12`, which is itself narrower than the doc's flat restatement).

---

## BUG-6 — Minor — `attribution_populate`

**Doc** (`module_34.md:515`):
> **static** (`static/presolve.gms:9`): **All t**: vm_land.fx(j,"urban") = pcm_land(j,"urban") (fixed to the 1995 baseline; static reads pcm_land **from core initialization** and does not use M34's i34_urban_area parameter)

**Reality in code.** `pcm_land` is neither declared nor initialized in `core/`. It is a Module 10 parameter:

- `modules/10_land/landmatrix_dec18/declarations.gms:11` — `pcm_land(j,land) Land area in previous time step …`
- `modules/10_land/landmatrix_dec18/start.gms:8,11` — `pm_land_start(j,land) = f10_land("y1995",j,land);` then `pcm_land(j,land) = pm_land_start(j,land);`
- `modules/10_land/landmatrix_dec18/postsolve.gms:9` — `pcm_land(j,land) = vm_land.l(j,land);` (per-timestep update)

Cross-check: `rg -n "pcm_land" core/` returns **no** matches; positive control `rg -n "pcm_land" modules/10_land/landmatrix_dec18/` returns the six hits above. Role map: `pcm_land` → `declared_in: 10_land`.

The rest of the sentence is correct (`static` has no `preloop`, so `i34_urban_area` is genuinely unused there — `modules/34_urban/static/realization.gms:17-19` includes only `declarations`, `presolve`, `postsolve`).

**Proposed fix.** "…static reads `pcm_land`, which is declared and initialized in Module 10 (`modules/10_land/landmatrix_dec18/declarations.gms:11`; `start.gms:8,11` sets it from `f10_land('y1995',j,land)`), and does not use M34's `i34_urban_area` parameter."

---

## BUG-7 — Minor — `other` (hardcoded count drift)

**Doc** (`module_34.md:6`, restated `:552`, `:557`, `:600`):
> **Lines of Code**: ~217 (exo_nov21), ~40 (static)
> **static structure** (4 files, ~40 lines)

**Reality**: `wc -l modules/34_urban/exo_nov21/*.gms` → **220** total across **9** files; `wc -l modules/34_urban/static/*.gms` → **66** total across **4** files. File counts are right; the static line count is understated by ~65 %.

**Proposed fix.** Update to "220 (exo_nov21, 9 files) / 66 (static, 4 files)" at `:6`, `:552`, `:557`, `:600`, and note the measurement command (`wc -l`) so the figure has a re-runnable artifact.

---

## BUG-8 — Informational — `citation`

Two citation ranges truncate the block they describe, and one self-referential count is over-stated:

- `module_34.md:254` cites `presolve.gms:12-14` for the `t>1` bounds block, but `vm_land.up(j,"urban") = Inf` is at `modules/34_urban/exo_nov21/presolve.gms:15`. (`:512` gets this right — "line 15" — so the doc is internally inconsistent.)
- `module_34.md:510` cites `presolve.gms:11-14` for a block that actually spans lines 10-15.
- `module_34.md:578` cites `exo_nov21/realization.gms:8-12`; the `@limitations` text runs to line 13.
- `module_34.md:548` claims "**File Citations**: 60+"; measured **55** (31 unique) via `grep -oE '`[A-Za-z0-9_/]*\.gms:[0-9]+(-[0-9]+)?`' modules/module_34.md | wc -l`.

**Proposed fix.** Widen the three ranges to `presolve.gms:12-15`, `presolve.gms:10-15`, `realization.gms:8-13`; change `:548` to "55 file:line citations (31 unique)" with the `grep -oE … | wc -l` command recorded as the artifact.

---

## Verified-correct claims (no action)

The following load-bearing claims were checked and hold in current `develop`:

- Default realization `exo_nov21` (`config/default.cfg:1147`) ✓; both realization dir names correct ✓; equation count 5 / 0 ✓ (`modules/34_urban/exo_nov21/declarations.gms:18-24`).
- All five equation formulas reproduce the source **character-for-character** (`equations.gms:17-18`, `20-21`, `25-26`, `30-31`, `34-35`) ✓ — including the `sum(ct, …)` wrappers, the `=g=` directions on both cost equations, and the `sum(cell(i2,j2), …)` regional aggregation.
- `s34_urban_deviation_cost = 1e6` USD17MER/ha (`modules/34_urban/exo_nov21/input.gms:13`) ✓; `c34_urban_scenario` default `SSP2` (`input.gms:8`, `config/default.cfg:1150`) ✓; scenario set `urban_scen34 / SSP1..SSP5 /` (`sets.gms:9-10`) ✓ — 5 members, no truncation.
- `vm_cost_urban` → Module 11 (`modules/11_costs/default/equations.gms:45`) ✓; role map `read_by: ['11','34']` agrees.
- `vm_bv(j,"urban",potnatveg)` → Module 44 only (`modules/44_biodiversity/bii_target/equations.gms:16`, `presolve.gms:16`) ✓; `urban` is a member of `landcover44` (`modules/44_biodiversity/bii_target/sets.gms:11`) and of `bii_class44` ✓. The doc's "likely Module 44" hedge at `:165` is unnecessarily weak — it is confirmed.
- `module_34.md:288` (added by an earlier round) is **correct on direction**: M52 and M56 each read `vm_carbon_stock` *directly and in parallel* (`modules/52_carbon/normal_dec17/equations.gms:16-19` vs `modules/56_ghg_policy/price_aug22/equations.gms:12-15`) — no M52→M56 hand-off — and `vm_carbon_stock` is indeed declared in Module 56 (`modules/56_ghg_policy/price_aug22/declarations.gms:34`), not Module 52. Only its "fixed to 0 / contributes zero" clause is wrong (BUG-1).
- `vm_cost_urban.scale(j) = 1e3` (`scaling.gms:8`) ✓; `v34_cost1/2` scaling commented out (`scaling.gms:9-10`) ✓ (the doc omits that `q34_urban_cost1/2` and `q34_urban_land` scalings are also commented out at `scaling.gms:11-13` — cosmetic).
- `static` fixes `vm_land`, `vm_carbon_stock`, `vm_bv`, `vm_cost_urban` (`modules/34_urban/static/presolve.gms:9,10,12,14`) ✓; `vm_cost_urban.fx(j) = 0` persists as claimed at `:490` ✓.
- Module 22 does use urban land — `pcm_land(j,"urban")` is subtracted from all three restoration potentials (`modules/22_land_conservation/area_based_apr22/presolve_ini.gms:83,93,104`) — so the `:318` hedge "Module 22 (Conservation - potentially)" is under-confident but not wrong. Module 35 likewise reads `pcm_land(j,"urban")` in the forest-recovery share (`modules/35_natveg/pot_forest_may24/presolve.gms:64,66`). Both go through `pcm_land`, a Module 10 parameter that Module 10's `postsolve` refreshes each timestep, so neither is a *direct* consumer of a Module 34 variable (MANDATE 17) — recorded here as context, not as a bug.
- Module 58 (peatland) does **not** touch urban: `manPeat58 / crop, past, forestry /` (`modules/58_peatland/v2/sets.gms`) — the doc correctly omits it.

---

## Deferred (not verified — no edit proposed)

1. `module_34.md:386` — "`i34_urban_area` monotonically increasing in all SSPs". The input table `f34_urbanland.cs3` is a run-time download (listed in `modules/34_urban/exo_nov21/input/files`, absent from the repo); monotonicity is unverifiable offline. BUG-4 refutes only the *structural* claim, not the data claim.
2. `module_34.md:314` — "**Centrality**: ~30 of 46 modules". The metric's definition is not stated anywhere in the doc or in `core_docs/`, so the number is not checkable.
3. `module_34.md:306` — "All Other Laws: ❌ Does NOT participate (… Nitrogen)". Urban land does appear in `q59_nr_som`'s `sum((ct,land_from), p59_carbon_density(ct,j2,land_from) * vm_lu_transitions(j2,land_from,"crop"))` (`modules/59_som/cellpool_jan23/equations.gms:69-75`), i.e. urban→crop conversion releases soil N. This is a transitive chain through Module 10's `vm_lu_transitions`, and "participation in the nitrogen conservation law" is not precisely defined in the doc — flagged for a maintainer, not asserted as a bug.
4. Whether `fm_carbon_density(t_all,j,"urban","soilc")` (M52 `input.gms:35`) is consumed anywhere under the *default* `som = cellpool_jan23` path (which uses `f59_topsoilc_density`/`i59_subsoilc_density` instead). It is definitively consumed under `som = static_jan19`. BUG-1 does not depend on resolving this.
5. All 55 citations in this doc use the short form (`equations.gms:17-18`) rather than the full `modules/34_urban/exo_nov21/equations.gms:17-18` form. The doc establishes realization context in its section headers, so this may be intended house style for module docs rather than a defect — a maintainer call, not filed as a bug.
