# Adversarial verification — `modules/module_34.md` (Round 60 depth)

Ground truth: read-only `develop` worktree at HEAD `2c02843ec`. All paths below are repo-relative.
Role map: `audit/integrated/depth_rolemap.json`.

**19 bugs adjudicated: 11 UPHELD, 8 CORRECTED, 0 REFUTED, 0 CITATION_FAILED.**

UPHELD: 34:3, 34:10, 34:11, 34:13, 34:14, 34:20, 34:25, 34:31, 34:32, 34:33, 34:34 (11)
CORRECTED: 34:1, 34:2, 34:9, 34:12, 34:19, 34:24, 34:26, 34:30 (8)

Every `file_evidence` path in all 19 bugs passed `test -f` + range + token check. Not one
citation failed — unusually clean for this corpus.

---

## 0. Shared ground truth (established once, reused below)

| Fact | Evidence | Status |
|---|---|---|
| `vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0;` | `modules/34_urban/exo_nov21/presolve.gms:8` | 🟢 |
| `ag_pools(c_pools) Above ground carbon pools / vegc, litc /` | `modules/56_ghg_policy/price_aug22/sets.gms:209-210` | 🟢 |
| `c_pools Carbon pools /vegc,litc,soilc/` | `core/sets.gms:324-325` | 🟢 |
| `land Land pools / crop, past, forestry, primforest, secdforest, urban, other /` | `core/sets.gms:250-251` | 🟢 |
| `noncropland59(land) /past, forestry, primforest, secdforest, other, urban/` | `modules/59_som/cellpool_jan23/sets.gms:10-11` | 🟢 |
| `q59_som_target_noncropland(j2,noncropland59) .. v59_som_target =e= vm_land(j2,noncropland59) * f59_topsoilc_density` | `modules/59_som/cellpool_jan23/equations.gms:31-33` | 🟢 |
| `q59_carbon_soil(j2,land,stockType) .. vm_carbon_stock(j2,land,"soilc",stockType) =e= v59_som_pool + vm_land*i59_subsoilc_density` | `modules/59_som/cellpool_jan23/equations.gms:61-64` | 🟢 |
| `fm_carbon_density(t_all,j,"urban","soilc") = fm_carbon_density(t_all,j,"other","soilc")` | `modules/52_carbon/normal_dec17/input.gms:35` (comment :33-34) | 🟢 |
| `urban_soilc` ∈ `emis_oneoff`; `urban_soilc . (urban) . (soilc)` ∈ `emis_land` | `core/sets.gms:318`, `core/sets.gms:350` | 🟢 |
| `q52_emis_co2_actual` reads `vm_carbon_stock(j2,land,c_pools,"actual")` | `modules/52_carbon/normal_dec17/equations.gms:16-19` | 🟢 |
| `q56_emis_pricing_co2` reads `vm_carbon_stock(j2,land,c_pools,"%c56_carbon_stock_pricing%")` | `modules/56_ghg_policy/price_aug22/equations.gms:19-22` | 🟢 |
| `$setglobal c56_carbon_stock_pricing actualNoAcEst` / `c56_carbon_stock_pricing <- "actualNoAcEst"` | `modules/56_ghg_policy/price_aug22/input.gms:90`; `config/default.cfg:1838` | 🟢 |
| `vm_carbon_stock(j,land,c_pools,stockType)` declared in M56 | `modules/56_ghg_policy/price_aug22/declarations.gms:34` | 🟢 |
| Defaults: `som <- cellpool_jan23`, `urban <- exo_nov21`, `carbon <- normal_dec17`, `ghg_policy <- price_aug22`, `land <- landmatrix_dec18`, `landconversion <- calib`, `biodiversity <- bii_target`, `drivers <- aug17`, `natveg <- pot_forest_may24`, `land_conservation <- area_based_apr22`, `nr_soil_budget <- macceff_aug22`, `costs <- default` | `config/default.cfg:1937,1147,1577,1634,232,1288,1438,210,1156,717,1500,236` | 🟢 |
| Role map: `vm_carbon_stock {declared_in: 56_ghg_policy, populated_by: [29,31,32,34,35,59], read_by: [52,56,59]}` | `audit/integrated/depth_rolemap.json` | 🟢 |
| Role map: `vm_land {declared_in: 10_land, populated_by: [10,29,31,32,34,35], read_by: [10,22,29,30,31,32,34,35,50,58,59]}` | same | 🟢 |
| Role map: `pcm_land {declared_in: 10_land, populated_by: [10,32,34,35], read_by: [10,13,22,29,31,32,34,35,44,56,58,59,71]}` | same | 🟢 |

### 0.1 The central factual question — is urban `soilc` non-zero? YES

`presolve.gms:8` restricts the `.fx` to `ag_pools` = {vegc, litc}, a **proper 2-member subset** of
the 3-member `c_pools`. The `soilc` slice is never fixed. In the **default** som realization
(`cellpool_jan23`), `q59_carbon_soil` is declared over the full `land` set (which contains `urban`),
so `vm_carbon_stock(j,"urban","soilc",stockType)` is an equation-defined, area-proportional,
structurally non-zero quantity. Its two drivers both resolve:

- `v59_som_pool(j,"urban")` ← `q59_som_target_noncropland` (urban ∈ `noncropland59`) × `f59_topsoilc_density`
- `i59_subsoilc_density(t_all,j) = fm_carbon_density(t_all,j,"other","soilc") - f59_topsoilc_density(t_all,j)`
  (`modules/59_som/cellpool_jan23/preloop.gms:12`)

and the initialization at `modules/59_som/cellpool_jan23/preloop.gms:33-35` writes
`pcm_carbon_stock(j,noncropland59,"soilc",stockType)` **and** `vm_carbon_stock.l(j,noncropland59,...)`
from `fm_carbon_density("y1995",j,noncropland59,"soilc")` — which for the urban member is exactly the
value M52 assigns at `modules/52_carbon/normal_dec17/input.gms:35`. So M52's urban-soilc assignment is
live in the default configuration.

**The auditors' shared core claim is correct.** The doc's blanket "urban carbon = ZERO" is wrong at
:28, :33, :198, :288-289, :304, :359-368, :473-474, :545, :585, :593.

### 0.2 ⚠️ THE ONE THING ALL FIVE CARBON AUDITORS GOT WRONG — "priced"

Five bugs (34:1, 34:9, 34:19, 34:24, 34:30) assert that `urban_soilc` is a **"real, priced CO2 source"**
/ **"PRICED by q56_emis_pricing_co2 in a default run"**. **This is false under the default config**, and
applying those proposed fixes verbatim would replace one error with another.

Pricing is gated by a per-`emis_source` multiplier applied in preloop:

```
modules/56_ghg_policy/price_aug22/preloop.gms:89
  im_pollutant_prices(t_all,i,pollutants,emis_source) =
    im_pollutant_prices(t_all,i,pollutants,emis_source)
    * f56_emis_policy("%c56_emis_policy%",pollutants,emis_source);
```

The default scenario is `reddnatveg_nosoil` (`config/default.cfg:1831`;
`modules/56_ghg_policy/price_aug22/input.gms:86`), documented in-repo at `config/default.cfg:1815` as:

> `redd+natveg_nosoil (Above ground CO2 emis from LUC in forest, forestry and natveg; all CH4 and N2O emissions)`

Urban is excluded on **both** counts — it is not forest/forestry/natveg, and `soilc` is excluded by
`_nosoil`. Cross-confirmed at `config/default.cfg:1043`: *"Without a price on CO2 emissions from
land-use change in module 32_forestry, which is the current default (`c56_emis_policy <- "reddnatveg_nosoil"`)"*.

**Correct statement**: `urban_soilc` change is **computed and reported** as CO2 via
`q52_emis_co2_actual` → `vm_emissions_reg(i,urban_soilc,"co2_c")`; it is **structurally present** in
`q56_emis_pricing_co2` (the equation is indexed over `emis_oneoff`, which contains `urban_soilc`), but
carries a **zero price** under the default `c56_emis_policy = reddnatveg_nosoil`, so it produces **no
cost term** in a default run. Pricing requires switching `c56_emis_policy` to a scenario that includes
soil and urban (e.g. `all`).

Provenance caveat: `f56_emis_policy.csv` is a **run-time input** (listed in
`modules/56_ghg_policy/input/files`, delivered via `input.tgz`), so the literal `0` multiplier is not
readable from the repo. The claim rests on the in-repo scenario documentation at
`config/default.cfg:1815`+`:1043` — 🟡 documented, not 🟢 value-verified. It is nonetheless strong
enough to forbid asserting "priced" as fact.

---

## Per-bug adjudication

### `module_34:1` — CORRECTED (class: mechanism)
Citations: all 10 evidence paths pass. `presolve.gms:8` ✔ token `ag_pools`; `56/sets.gms:209-210` ✔
`ag_pools(c_pools) / vegc, litc /`; `core/sets.gms:324-325` ✔ `/vegc,litc,soilc/`; `59/sets.gms:10-11`
✔ urban member; `59/equations.gms:31-33,61-65` ✔ (61-64 substantive, 65 blank, in range of 102);
`59/preloop.gms:33-35` ✔; `52/input.gms:32-35` ✔ (32 blank, 33-34 comment, 35 assignment);
`core/sets.gms:318,350` ✔; `52/equations.gms:16-19` ✔; `56/equations.gms:19-22` ✔.
Core claim UPHELD. **Corrected**: strike "as a real, priced CO2 source" (§0.2).

### `module_34:2` — CORRECTED (class: producer_declaration)
Citations pass, incl. the verbatim role-map quote `vm_carbon_stock.populated_by = [29,31,32,34,35,59]`.
M59 is a genuine **reader** of `vm_land(j,"urban")` (`59/cellpool_jan23/equations.gms:33`, urban ∈
`noncropland59`) **and** a genuine **populator** of the urban `soilc` slice
(`59/cellpool_jan23/equations.gms:61-64`, LHS). :318 omitting 52/56/59 while :288 and :473-474 name
52/56 is a real internal contradiction. **Corrected**: the proposed fix says "Update Total Connections
at :316" — that line is at **:315** (`grep -n "Total Connections" modules/module_34.md` → `315:`).

### `module_34:3` — UPHELD (class: consumer_set)
All 7 citations pass: `09_drivers/aug17/input.gms:22` ✔ `sm_fix_SSP2 ... / 2025 /`;
`44_biodiversity/bii_target/input.gms:17` ✔ `table fm_bii_coeff`;
`10_land/landmatrix_dec18/input.gms:19` ✔ `table fm_luh2_side_layers`;
`10_land/landmatrix_dec18/declarations.gms:11` ✔ `pcm_land(j,land)`;
`34_urban/exo_nov21/preloop.gms:10` ✔ `if(m_year(t_all) <= sm_fix_SSP2,`; `:20-21` ✔ reads `pcm_land`,
`fm_bii_coeff`, `fm_luh2_side_layers`; `exo_nov21/equations.gms:35` ✔ same three;
`34_urban/static/not_used.txt:2` ✔ `sm_fix_SSP2, input, not needed`.
The `static` realization additionally reads `pcm_land` at `static/presolve.gms:9,12` — where it is a
**genuine** upstream read (static has no preloop, so M10's `start.gms:11` value is what it sees).
:274-276 "None" is false; the doc contradicts itself at :320. Cleanest and most precise of the four
upstream-lens duplicates.

### `module_34:9` — CORRECTED (class: mechanism)
All citations pass (superset of 34:1 plus `config/default.cfg:1937` ✔ `cfg$gms$som <- "cellpool_jan23"`,
`core/sets.gms:314-318` ✔ `emis_oneoff`). Core UPHELD. The `:366` sub-claim is also upheld on logic:
zeroing an urban carbon *sink* **over**-states conversion emissions, so "UNDER-estimated" is sign-inverted;
independently, urban `soilc` is retained at `other`-land density, so forest→urban does not release the
full soil pool. Note `:59` is a weak instance — it says the static realization's variables are "fixed",
not "fixed to zero" (`static/presolve.gms:10` is still `ag_pools`-restricted, so a slice qualifier is
still warranted, but it is not the same defect).
**Corrected**: strike "priced CO2 in q56_emis_pricing_co2" from the proposed fix (§0.2).

### `module_34:10` — UPHELD (class: consumer_set)
All 6 citations pass. Independently re-derived the urban-slice reader set of `vm_land` by enumerating
every `vm_land(` occurrence outside M10/M34 and resolving each index set:
- **M10** `q10_land_area` `sum(land, vm_land(j2,land))` (`10/equations.gms:14`) and `q10_transition_to`
  (`:21`) — urban ∈ `land`. ✔
- **M59** `vm_land(j2,noncropland59)` (`59/cellpool_jan23/equations.gms:33`) and `vm_land(j2, land)`
  (`:63`) — urban in both. ✔
- **M50** `q50_nr_deposition(i2,land)` `vm_land(j2,land)` (`50/macceff_aug22/equations.gms:90`). ✔
- Solution-level: `pc59_land_before(j,land) = vm_land.l(j,land)` (`59/cellpool_jan23/postsolve.gms:9`) —
  invisible to a `vm_land(` grep. ✔
- Excluded (index sets that do **not** contain urban): M29 `"crop"`/`land_snv`, M30 `"crop"`,
  M31 `"past"`, M32 `"forestry"`, M35 `land_natveg`/`land_forest`/`"other"`/`"primforest"`/`"secdforest"`.
  M58 has **zero** `vm_land(` matches (positive control: `rg -c 'vm_land' 10/landmatrix_dec18/equations.gms`
  → 9, so rg works in that tree); it reaches `vm_land` only through the `m58_LandMerge` macro over
  `manPeat58`.
The "M50 urban slice is inert" qualifier is **confirmed**: `rg -n 'v50_nr_deposition'` over
`50_nr_soil_budget/macceff_aug22/` shows budget consumption only at `equations.gms:32` (`"crop"`) and
`:80` (`"past"`); every other hit is its own definition or a postsolve `ov50_*` dump.

### `module_34:11` — UPHELD (class: consumer_set)
All 6 citations pass, and the claim reproduces **exactly**. `q52_emis_co2_actual` reads
`vm_carbon_stock(j2,land,c_pools,"actual")` — `c_pools`, with `stockType` pinned to the string literal
`"actual"`. `q56_emis_pricing_co2` reads `vm_carbon_stock(j2,land,c_pools,"%c56_carbon_stock_pricing%")`,
default `actualNoAcEst` (`56/input.gms:90`; `config/default.cfg:1838`). Neither reader uses `ag_pools`
and neither carries a free `stockType` index. The doc's `:288` parenthetical "(the urban slice, fixed
to 0)" is therefore false — both readers reach `soilc`, which M34 never fixes. This is the most
precisely-argued bug in the set.

### `module_34:12` — CORRECTED (class: consumer_set)
All 6 citations pass and the headline defect (:276 "None") is real. **Corrected** on one detail: the
claim *"pcm_land and vm_land … read/written at preloop.gms:17,20-21"* misattributes `vm_land`.
`exo_nov21/preloop.gms:17` writes `pcm_land(j,"urban")`; `:20-21` writes `vm_bv.l` and reads `pcm_land`,
`fm_bii_coeff`, `fm_luh2_side_layers`. `vm_land` appears in `exo_nov21` only at `presolve.gms:11,13,14,15`
(all writes: `.fx`/`.lo`/`.l`/`.up`) and in `equations.gms:18,21,31,35` (reads). Corrected claim below.

### `module_34:13` — UPHELD (class: producer_declaration)
All 8 citations pass. Verified end to end:
- `exo_nov21/preloop.gms:17` `pcm_land(j,"urban") = i34_urban_area("y1995",j);` — a **write** to a
  M10-owned parameter (`10/landmatrix_dec18/declarations.gms:11`), so it belongs under Outputs. The doc
  files it under `### Inputs (from other modules/external)` (heading at :173). ✔
- Phase order: `core/calculations.gms:13` `$batinclude "./modules/include.gms" start` then `:15` `preloop`
  → M10's `start.gms:11` `pcm_land(j,land) = pm_land_start(j,land);` runs **first**, M34 then overrides
  the urban slice. ✔
- M22 reads `- pcm_land(j, "urban")` at `22_land_conservation/area_based_apr22/presolve_ini.gms:83, 93, 104`
  (in `p22_secdforest_restore_pot`, `p22_past_restore_pot`, `p22_other_restore_pot` respectively) — a
  direct, unconditional subtraction. The doc's ":318 Module 22 (Conservation - potentially)" hedge is
  unwarranted. ✔
- M35 reads `pcm_land(j,"urban")` at `35_natveg/pot_forest_may24/presolve.gms:64` (guard) and `:66`
  (denominator of `pc35_forest_recovery_shr`). M35 is absent from the doc. ✔
- `10/landmatrix_dec18/postsolve.gms:9` refreshes `pcm_land` each timestep. ✔

### `module_34:14` — UPHELD (class: mechanism)
All 6 citations pass: `39/calib/input.gms:13` ✔ `s39_cost_establish_urban … / 12300 /`;
`39/calib/presolve.gms:16` ✔ `i39_cost_establish(t,i,"urban") = s39_cost_establish_urban;`;
`39/calib/equations.gms:12-15` ✔ `q39_cost_landcon(j2,land)` over the full `land` set;
`config/default.cfg:1288` ✔ `landconversion <- "calib"`, `:1303` ✔ `s39_cost_establish_urban <- 12300`;
`10/landmatrix_dec18/equations.gms:30-33` ✔ `q10_landexpansion`; `34_urban/exo_nov21/realization.gms:12`
✔ the `@limitations` line quoted verbatim.
Credit where due: this bug **correctly applies MANDATE 17** — it explicitly forbids listing M39 as a
*direct* consumer of `vm_land(j,"urban")` (M39 reads `vm_landexpansion`, which M10 derives from
`vm_lu_transitions`), and flags only the omitted **cost channel**. That discipline is right.
Minor caveat carried into the fix text: "emits soil CO2 through M59 → M52/M56" — the M52 reporting leg
holds; the M56 leg is zero-priced by default (§0.2).

### `module_34:19` — CORRECTED (class: mechanism)
All 7 citations pass, including `59/cellpool_jan23/preloop.gms:19-20` ✔ (`pc59_som_pool(j,noncropland59)
= f59_topsoilc_density("y1995",j) * pm_land_start(j,noncropland59);`). Core UPHELD.
**Corrected**: this bug states the pricing claim most explicitly — *"PRICED by q56_emis_pricing_co2 in a
default run"* — and it is false under `c56_emis_policy = reddnatveg_nosoil` (§0.2). Highest-risk fix text
of the five; do not apply as written.

### `module_34:20` — UPHELD (class: producer_declaration)
All 3 citations pass. `59/cellpool_jan23/postsolve.gms:13`
`pcm_carbon_stock(j,land,"soilc",stockType) = vm_carbon_stock.l(j,land,"soilc",stockType);` is a genuine
**solution-level read** that a `vm_carbon_stock(` grep misses — the bug correctly ran the `NAME.` probe.
The `*` wildcard at :473-474 does assert all three pools are zero, which is false for `soilc`. Role-map
quote is verbatim-correct. The :318 roll-up omits 52, 56 **and** 59.

### `module_34:24` — CORRECTED (class: mechanism)
All 10 citations pass, including `modules/34_urban/module.gms` — verified the module header does say the
module "estimates their corresponding carbon content", which sits awkwardly with the doc's blanket zero.
Core UPHELD. **Corrected**: "live emis_oneoff source in q52_emis_co2_actual / q56_emis_pricing_co2" must
be split — live and reported in q52; structurally present but zero-priced in q56 by default (§0.2).

### `module_34:25` — UPHELD (class: formula_or_value)
All 3 citations pass. Purely notational and exactly right: the fixed slice is
`(j,"urban",ag_pools,stockType)`, a 2-of-3 pool restriction; `*` over-claims the whole pool dimension.
Occurs verbatim at :473, :474 and :545 (`grep -n` confirms :545 is `- vm_carbon_stock(j,"urban",*) to
Module 52 ✓`, inside the `**Interface Variables**: All checked` block that starts at :542). Narrowest
and most mechanically certain bug in the set; no pricing over-reach in its fix text.

### `module_34:26` — CORRECTED (class: consumer_set)
All citations pass, incl. `56/price_aug22/sets.gms:209` (`ag_pools`) and `:212` (`stockType Carbon stock
types`), `10/landmatrix_dec18/sets.gms:15` (`potnatveg(luh2_side_layers10)`).
The headline defect (:276 "None", :315 "depends on 1") is real. **Corrected** on framing: the bug says
M34 *"reads interface identifiers declared in FOUR other modules"* and lists `vm_bv` (M44) and
`vm_carbon_stock` (M56) among them. Per the DECLARED/POPULATED/READ split, M34 **populates** both —
`vm_bv` at `exo_nov21/equations.gms:35` (LHS) and `preloop.gms:20` (`.l`), `vm_carbon_stock` at
`presolve.gms:8` (`.fx`) — it does not read them. Role map agrees: `vm_bv.read_by = [44]` only;
`vm_carbon_stock.read_by = [52,56,59]`, no 34. Listing set definitions (`ag_pools`, `stockType`,
`potnatveg`, `land`) as "upstream data providers" also conflates a compile-time symbol dependency with a
data hand-off. Genuine upstream **data** providers are three: M09, M10, M44.

### `module_34:30` — CORRECTED (class: mechanism)
All 10 citations pass, including the non-default `59_som/static_jan19` cross-check:
`static_jan19/sets.gms:9-10` ✔ `regularland59(land) / past, forestry, primforest, secdforest, urban /`
and `static_jan19/equations.gms:17-19` ✔ `q59_soilcarbon_regular` populating
`vm_carbon_stock(j2,regularland59,"soilc",stockType)` — so urban soilc is non-zero in **both** M59
realizations, not just the default. Useful robustness check.
Core UPHELD. **Corrected**: the `reality_in_code` wording ("reaches BOTH q52 and q56") is structurally
true, but the `proposed_fix` escalates to *"is emitted/priced through the emis_land member urban_soilc"* —
the "priced" half is false by default (§0.2).

### `module_34:31` — UPHELD (class: producer_declaration)
All 4 citations pass. The framing is the sharpest of the M59-omission bugs: the urban slice of
`vm_carbon_stock` has **two owners** — M34 owns `ag_pools` via `.fx` (`presolve.gms:8`), M59 owns `soilc`
via equation (`59/cellpool_jan23/equations.gms:61-64`). That per-slice split ownership is exactly what
the doc's `*` wildcard erases. The :318-vs-:288/:473-474 internal contradiction is real. No pricing
over-reach in its fix text.

### `module_34:32` — UPHELD (class: consumer_set)
All 9 citations pass. The most **precisely scoped** of the four upstream-lens duplicates: it names
exactly three read-only interface objects — `fm_bii_coeff` (M44), `fm_luh2_side_layers` (M10),
`sm_fix_SSP2` (M09) — and avoids 34:26's read/populate conflation. Both directional corrections check out:
1. M09 supplies only `sm_fix_SSP2`, **not** the LUH3 trajectory. `f34_urbanland` is M34's own input table
   (`exo_nov21/input.gms:16-20`) loading `f34_urbanland.cs3`, which is a **run-time** file — the repo ships
   only the manifest `modules/34_urban/exo_nov21/input/files` listing `f34_urbanland.cs3`. So :320's
   "Module 09 (Drivers - LUH3 scenarios)" is wrong on both the identifier and the direction.
2. M34 **writes** `pcm_land(j,"urban")` in preloop, after M10's start-phase init (`core/calculations.gms:13,15`).

### `module_34:33` — UPHELD (class: mechanism)
All 3 citations pass. Re-derived independently; this is a textbook **parameterization-vs-mechanism**
conflation and every leg holds:
- `exo_nov21/presolve.gms:13` `vm_land.lo(j,"urban") = 0;` — for `ord(t) > 1` the lower bound is **zero**,
  not the previous level. (At `ord(t) = 1` only, `:11` fixes it.) ✔
- `exo_nov21/equations.gms:30-31` `q34_urban_land(i2) .. sum(cell(i2,j2), vm_land(j2,"urban")) =e=
  sum((ct,cell(i2,j2)), i34_urban_area(ct,j2));` — an **equality**. A declining prescribed trajectory
  would *force* urban land down, not be blocked by it. ✔
- `10/landmatrix_dec18/equations.gms:23-25` `q10_transition_from(j2,land_from) .. sum(land_to,
  vm_lu_transitions(j2,land_from,land_to)) =e= pcm_land(j2,land_from);` with
  `alias(land,land_from)` / `alias(land,land_to)` at `10/landmatrix_dec18/sets.gms:19-20` — so
  `land_from = "urban"` and `land_to = "urban"` are both representable, with **no exclusion**. ✔
No code constraint forbids urban→non-urban conversion. The doc's :386 already half-concedes by
attributing one-wayness to SSP monotonicity — and since `f34_urbanland.cs3` is a run-time input absent
from the repo, that monotonicity assertion is **not verifiable in-repo** and must be labeled as an
unverified input-data property, exactly as the fix proposes.

### `module_34:34` — UPHELD (class: mechanism)
All 6 citations pass (same M39/M11 chain as 34:14, plus `11_costs/default/equations.gms:20`
✔ `+ sum((cell(i2,j2),land), vm_cost_landcon(j2,land))`). Independently confirmed
`ls -d modules/39_landconversion/*/` returns only `calib/` and `input/` — **`calib` is the sole
realization**, so the cost channel is unconditional. Like 34:14 it correctly labels M39 as transitive,
not a direct `vm_land(j,"urban")` consumer. Complementary to 34:14 rather than a pure duplicate: 34:34
traces the channel through to the objective function (M11), 34:14 anchors on the `@limitations` quote.

---

## Consolidated corrected claim (safe to apply)

> **Module 34 fixes only the ABOVE-GROUND urban carbon pools.**
> `vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0` (`modules/34_urban/exo_nov21/presolve.gms:8`),
> where `ag_pools(c_pools) / vegc, litc /` (`modules/56_ghg_policy/price_aug22/sets.gms:209-210`) is a
> 2-member subset of `c_pools /vegc,litc,soilc/` (`core/sets.gms:324-325`).
>
> **Urban SOIL carbon is not zero and is not Module 34's.** In the default som realization
> `cellpool_jan23` (`config/default.cfg:1937`), Module 59 populates
> `vm_carbon_stock(j,"urban","soilc",stockType)` via `q59_carbon_soil`
> (`modules/59_som/cellpool_jan23/equations.gms:61-64`, indexed over the full `land` set), driven by
> `q59_som_target_noncropland` (`:31-33`; urban ∈ `noncropland59`, `sets.gms:10-11`) and initialized from
> the urban soil density Module 52 assigns equal to `other` land
> (`modules/52_carbon/normal_dec17/input.gms:35` → `modules/59_som/cellpool_jan23/preloop.gms:33-35`).
> The urban slice of `vm_carbon_stock` therefore has **two owners**: M34 (`ag_pools`, via `.fx`) and
> M59 (`soilc`, via equation).
>
> **Emissions: reported, not priced by default.** `urban_soilc` ∈ `emis_oneoff` (`core/sets.gms:318`),
> mapped `urban_soilc . (urban) . (soilc)` in `emis_land` (`core/sets.gms:350`), so urban soil-carbon
> change is computed and reported as CO2 by `q52_emis_co2_actual`
> (`modules/52_carbon/normal_dec17/equations.gms:16-19`, reading `c_pools` at `stockType = "actual"`).
> It is structurally present in `q56_emis_pricing_co2`
> (`modules/56_ghg_policy/price_aug22/equations.gms:19-22`, reading `c_pools` at
> `%c56_carbon_stock_pricing%`, default `actualNoAcEst`), but the default emission policy
> `c56_emis_policy = reddnatveg_nosoil` (`config/default.cfg:1831`, semantics at `:1815`) zeroes its
> price multiplier (`modules/56_ghg_policy/price_aug22/preloop.gms:89`), so **it generates no cost term
> in a default run**. Do not write "priced". 🟡 (multiplier value lives in the run-time
> `f56_emis_policy.csv`; scenario semantics are documented in-repo.)
>
> **Restate Limitation 2 (:359-368)** as: *no urban-specific vegetation/litter carbon (both fixed to
> zero), and no urban-specific soil parameterization (urban soil proxied by natural `other`-land
> density)* — not "urban carbon is zero", and not "conversion emissions under-estimated" (zeroing an
> urban sink over-states conversion emissions).
>
> **Upstream is not "None" (:274-276).** Module 09 supplies `sm_fix_SSP2`
> (`modules/09_drivers/aug17/input.gms:22`, default 2025) read at `exo_nov21/preloop.gms:10`; Module 10
> supplies `fm_luh2_side_layers` (`modules/10_land/landmatrix_dec18/input.gms:19`) and `pcm_land`
> (`declarations.gms:11`); Module 44 supplies `fm_bii_coeff`
> (`modules/44_biodiversity/bii_target/input.gms:17`). The LUH3 trajectory is M34's **own** input table
> `f34_urbanland` (`exo_nov21/input.gms:16-20`), not Module 09's — fix :320 accordingly, and :315
> "depends on 1" → 3. M34 does **not** read `vm_bv` or `vm_carbon_stock`; it populates them.
>
> **`pcm_land(j,"urban")` is an OUTPUT, not an input** — move it from :179 to the Outputs block. M34
> writes it at `exo_nov21/preloop.gms:17`, overriding M10's start-phase value
> (`modules/10_land/landmatrix_dec18/start.gms:11`; phase order `core/calculations.gms:13,15`). It is
> read by Module 22 (`modules/22_land_conservation/area_based_apr22/presolve_ini.gms:83,93,104` —
> unconditionally caps restoration potential, so drop the "potentially" hedge at :318) and Module 35
> (`modules/35_natveg/pot_forest_may24/presolve.gms:64,66`).
>
> **`vm_land(j,"urban")` consumers**: Module 10 (`10/landmatrix_dec18/equations.gms:13-15,19-25`),
> Module 59 (`59/cellpool_jan23/equations.gms:31-33,61-64`, plus `postsolve.gms:9` at solution level),
> Module 50 (`50/macceff_aug22/equations.gms:88-90` — computed but **inert**: only the `"crop"` and
> `"past"` slices of `v50_nr_deposition` feed budget equations, at `equations.gms:32` and `:80`).
>
> **Urban expansion is not cost-free beyond `vm_cost_urban` (:36, :341).** It incurs a land-conversion
> establishment cost of **12300 USD17MER/ha** — `i39_cost_establish(t,i,"urban") = s39_cost_establish_urban`
> (`modules/39_landconversion/calib/presolve.gms:16`, `input.gms:13`; `config/default.cfg:1303`) entering
> `q39_cost_landcon(j2,land)` (`calib/equations.gms:12-15`, full `land` set) and the objective via
> `modules/11_costs/default/equations.gms:20`. `calib` is Module 39's only realization. This is a
> **transitive** link (M39 reads `vm_landexpansion`, derived by M10 from `vm_lu_transitions` at
> `10/landmatrix_dec18/equations.gms:30-33`) — do **not** list M39 as a direct consumer of
> `vm_land(j,"urban")`.
>
> **One-way transition (:37, :382-393) is a data property, not a code constraint.**
> `vm_land.lo(j,"urban") = 0` for `ord(t) > 1` (`exo_nov21/presolve.gms:13`), `q34_urban_land` is an
> equality (`equations.gms:30-31`), and `q10_transition_from` covers `land_from = "urban"` via
> `alias(land,land_from)` (`10/landmatrix_dec18/sets.gms:19-20`, `equations.gms:23-25`) with no exclusion.
> Label the SSP-monotonicity premise as unverified — `f34_urbanland.cs3` is a run-time input.
>
> **:315/:318** — replace "Total Connections: 3-4 / depends on 1" and the four-module Provides-To with the
> enumerated set: provides to 10, 11, 22, 35, 44, 50, 52, 56, 59 (+ 39 transitively); depends on 09, 10, 44.

## Note for the doc editor
Bugs 34:1 / 34:9 / 34:19 / 34:24 / 34:30 are five lenses on one defect, and **all five proposed fixes
contain the "priced" error**. Apply the consolidated claim above, not the individual fix texts.
