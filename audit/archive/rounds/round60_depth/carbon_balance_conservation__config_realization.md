# R60 depth audit — `cross_module/carbon_balance_conservation.md`

**Lens**: `config_realization` (entry from `config/default.cfg` + realization directory listings; priority on default-value claims, `cfg$gms$*` switch behaviour, realization names, and default-vs-alternative framing)
**Ground truth**: MAgPIE `develop` read-only worktree at HEAD `2c02843ec` ("Merge pull request #919 from alexkoberle/dyn_reg_tau"), 2026-08-02.
**Convention**: `DEV` = the read-only develop worktree root; MAgPIE paths are repo-relative to it. Agent-repo paths are relative to `magpie-agent/`.

---

## 0. Method

Entry point was `config/default.cfg` plus `ls -d $DEV/modules/NN_*/` for every module the doc touches.
Every `vm_`/`pm_`/`im_`/`fm_`/`pcm_` attribution claim was checked against `audit/integrated/depth_rolemap.json`
**first**, then confirmed with a both-endpoints grep (`NAME(` *and* `NAME.`) over the whole `modules/` tree.
Every absence claim was run with a positive control in the same directory. Each grep probe was run as its
own standalone command (no `find -exec` chaining).

### Realization discipline: clean

Every realization the doc names is the module **default**, and every named directory exists:

| Module | `config/default.cfg` | Default | Doc leads with | OK |
|---|---|---|---|---|
| 52 carbon | 1577 | `normal_dec17` (sole realization) | `normal_dec17` | ✅ |
| 53 methane | 1604 | `ipcc2006_aug22` (alt `off`) | `ipcc2006_aug22` | ✅ |
| 56 ghg_policy | 1634 | `price_aug22` | `price_aug22` | ✅ |
| 57 maccs | 1843 | `on_aug22` | `on_aug22` | ✅ |
| 58 peatland | 1874 | `v2` (alt `off`) | `v2`, cited as `:1874` | ✅ |
| 59 som | 1937 | `cellpool_jan23` (alt `static_jan19`) | `cellpool_jan23` | ✅ |
| 29 cropland | 814 | `detail_apr24` | `detail_apr24` | ✅ |
| 32 forestry | 995 | `dynamic_may24` | `dynamic_may24` | ✅ |
| 34 urban | 1147 | `exo_nov21` | `exo_nov21` | ✅ |
| 35 natveg | 1156 | `pot_forest_may24` | `pot_forest_may24` | ✅ |
| 14 yields | 357 | `managementcalib_aug19` (alt `dynRegPastrTau_apr26`) | `managementcalib_aug19` | ✅ |
| 50 nr_soil_budget | 1500 | `macceff_aug22` | `macceff_aug22` | ✅ |
| 51 nitrogen | 1571 | `rescaled_jan21` | `rescaled_jan21` | ✅ |
| 11 costs / 36 employment | 236 / 1212 | `default` / `exo_may22` | (single realization each) | ✅ |

**No wrong-default-realization bug exists in this document.** Notable, because 14_yields has gained a
second realization (`dynRegPastrTau_apr26`) since the doc was last touched and the doc still correctly
cites `managementcalib_aug19`.

### Switch / scalar defaults: all correct

`s52_growingstock_calib = 1` (`modules/52_carbon/normal_dec17/input.gms:46`; confirmed **absent** from
`config/default.cfg` — repo-wide `rg` returns 4 hits, all inside `modules/52_carbon/`) ·
`c52_carbon_scenario = cc` (`input.gms:8`; `config/default.cfg:1590`) ·
`c56_carbon_stock_pricing = actualNoAcEst` (`modules/56_ghg_policy/price_aug22/input.gms:90`) ·
`s59_scm_target = 0` (`config/default.cfg:1978`, and `i59_scm_target` collapses to 0 because
`s59_scm_target_noselect = 0` too, `modules/59_som/cellpool_jan23/presolve.gms:31-33`) ·
`c59_irrigation_scenario = "on"` (`config/default.cfg:1956`; off-path at
`modules/59_som/cellpool_jan23/input.gms:70`) · `s58_fix_peatland = 2020` (`config/default.cfg:1931`) ·
`s59_cost_scm_recur = 65` USD17MER/ha (`config/default.cfg:1994`) · tillage/input shares hard-wired to
`full_tillage` / `medium_input` (`modules/59_som/cellpool_jan23/preloop.gms:52-55`, with **no** config
switch — `grep -n -i 'tillage\|input_share' $DEV/config/default.cfg` → no match, positive control
`grep -c 's59_'` → 8).

### Citations: 45 of 46 exact

All verified on current develop, including the fiddly ones: `core/macros.gms:18` (`m_growth_vegc`),
`:51` (`m_timestep_length`) · `core/sets.gms:314-318` (`emis_oneoff`, 21 members = 7 land × 3 pools),
`:322` (peatland ∈ `emis_annual`), `:324-325` (`c_pools`), `:332-354` (`emis_land`) ·
`modules/52_carbon/normal_dec17/{equations.gms:16-19; start.gms:17,19-20,28,30-31,43-44;
preloop.gms:29-30,71-73,114-116; input.gms:8-23,37-43,46,47}` ·
`modules/56_ghg_policy/price_aug22/{declarations.gms:34; sets.gms:212-213; equations.gms:15-17,19-22;
input.gms:90}` · `modules/59_som/cellpool_jan23/{equations.gms:20-27,46-52,61-64; preloop.gms:45;
input.gms:70; realization.gms:21-24}` · `modules/34_urban/exo_nov21/presolve.gms:8` (character-exact) ·
`modules/29_cropland/detail_apr24/{equations.gms:39; preloop.gms:46,48}` ·
`modules/32_forestry/dynamic_may24/presolve.gms:59,61,68` ·
`modules/35_natveg/pot_forest_may24/presolve.gms:117,177-180,240,242,248-252` ·
`modules/14_yields/managementcalib_aug19/presolve.gms:44,64-71` ·
`modules/53_methane/ipcc2006_aug22/equations.gms:29,52,63,70-72` ·
`modules/57_maccs/on_aug22/sets.gms:28-29` · `modules/51_nitrogen/rescaled_jan21/{sets.gms:15-16;
preloop.gms:8-10; equations.gms:30-39,62-64,71}` ·
`modules/50_nr_soil_budget/macceff_aug22/presolve.gms:54-64` ·
`modules/58_peatland/v2/{equations.gms:91-92; realization.gms:8-17}`. Commit `6b00f9dea` is real,
titled "Fix youngsecdf wood production: use uncalibrated growing stock", dated 2026-07-01 as claimed.
The single miss is C3 below.

### Attribution spine: correct

`vm_carbon_stock` populators (§7.5) match the role map and both-endpoint greps exactly —
M29 crop (`29_cropland/detail_apr24/equations.gms:39`), M31 past (`31_past/endo_jun13/equations.gms:23`),
M32 forestry (`32_forestry/dynamic_may24/equations.gms:108`), M34 urban `.fx`
(`34_urban/exo_nov21/presolve.gms:8`), M35 primforest/secdforest/other
(`35_natveg/pot_forest_may24/equations.gms:43,50,54`), M59 soilc
(`59_som/cellpool_jan23/equations.gms:62`); readers M52, M56, M59. The **parallel-not-serial** claim at
`:583` is right: M56 reads `vm_emissions_reg` only over `emis_annual`
(`modules/56_ghg_policy/price_aug22/equations.gms:17`) and recomputes CO₂ itself at `:19-22`, so it never
consumes M52's `vm_emissions_reg(...,"co2_c")`. The `stockType` mechanism is right too: both slices are
filled by every populator (all equations free over `stockType`), and they differ because
`m_carbon_stock_ac` sums over `ac` for `"actual"` and over `ac_sub` for `"actualNoAcEst"`
(`core/macros.gms:104-106`). The uncalibrated-curve reader set (M14, M29, M32, M35) is complete.
`i59_subsoilc_density = fm_carbon_density(…,"other","soilc") - f59_topsoilc_density`
(`modules/59_som/cellpool_jan23/preloop.gms:12`) is as described.

**13 defects follow: 1 Critical, 1 Major, 10 Minor, 1 Informational.**

---

## Bugs

### C1 — 🔴 Critical — `attribution_read` — the CALIBRATED-curve reader set omits Module 32

**Doc**: `carbon_balance_conservation.md:180`, verbatim duplicate at `:479`

> "The uncalibrated curves survive as `pm_carbon_density_*_ac_uncalib` … and are what M14's
> `im_growing_stock_ysf` …, M29's tree cover …, M32's afforestation and NDC curves
> (`32_forestry/dynamic_may24/presolve.gms:59,61,68`) and M35's youngsecdf … read.
> **M14 and M35 read the CALIBRATED curve as well** - M14 for regular secdforest growing stock
> (`modules/14_yields/managementcalib_aug19/presolve.gms:44`), M35 for secdforest carbon density …"

**Reality**: the calibrated plantation curve `pm_carbon_density_plantation_ac` — overwritten in
`modules/52_carbon/normal_dec17/preloop.gms:114-116` whenever `s52_growingstock_calib = 1`, which is
the hard default in every run — is read by **Module 32 in three places** and by **M14 for the forestry
growing stock**, none of which this enumeration lists:

- `modules/32_forestry/dynamic_may24/presolve.gms:65` —
  `p32_carbon_density_ac(t,j,"plant",ac,ag_pools) = pm_carbon_density_plantation_ac(t,j,ac,ag_pools);`
  This is the carbon density of **timber plantations**, i.e. the `vm_carbon_stock(j,"forestry",…)` slice
  produced by `q32_carbon` (`modules/32_forestry/dynamic_may24/equations.gms:108`) — the dominant
  forestry carbon pool.
- `modules/32_forestry/dynamic_may24/preloop.gms:18` — `p32_carbon_density_ac_forestry`.
- `modules/32_forestry/dynamic_may24/preloop.gms:56` — `p32_avg_increment`.
- `modules/14_yields/managementcalib_aug19/presolve.gms:26` — `im_growing_stock(t,j,ac,"forestry")`.

The paragraph does mention M32, but only as a reader of the **uncalibrated** curves — true for its `aff`
and `ndc` types and false for `plant`. A reader refactoring `pm_carbon_density_plantation_ac` on the
strength of this sentence would conclude its consumers are M14-secdforest and M35, and would miss
Module 32 entirely. This is the immutable R20 anchor in `audit/flywheel_rubric.md` §1 almost verbatim
(same parameter family, same omitted module, same refactor hazard) → **Critical** by the wrong-consumer-set
trigger, and it qualifies as a latent doc bug under the rubric's `doc_error_answerer_beat_it` mandate.

**Verify** (two independent methods, each run standalone):

```
DEV=/tmp/magpie_develop_ro
rg -n 'pm_carbon_density_plantation_ac|pm_carbon_density_secdforest_ac' $DEV/modules/32_forestry/
# → presolve.gms:59,61,68 (uncalib) AND presolve.gms:65 (CALIBRATED), preloop.gms:18, preloop.gms:56

grep -rn 'pm_carbon_density_plantation_ac\b' $DEV/modules/ --include=*.gms | grep -v uncalib | grep -v 52_carbon
# → 32_forestry/dynamic_may24/{presolve.gms:65, preloop.gms:18, preloop.gms:56}
#   14_yields/managementcalib_aug19/presolve.gms:26  (+ non-default dynRegPastrTau_apr26/presolve.gms:26)
```

Role map cross-check: `pm_carbon_density_plantation_ac` → `read_by: ["14","32","52"]` — agrees with both
greps; the doc lists neither M32 nor M14's forestry read.

**Fix** (apply to both `:180` and `:479`): replace the final sentence with

> M14, M32 and M35 read the CALIBRATED curves as well — M14 for the forestry and the regular-secdforest
> growing stock (`modules/14_yields/managementcalib_aug19/presolve.gms:26,44`), M32 for the
> **timber-plantation** carbon density `p32_carbon_density_ac(…,"plant",…)`
> (`modules/32_forestry/dynamic_may24/presolve.gms:65`, plus `preloop.gms:18,56`), and M35 for secdforest
> carbon density, which it BLENDS with the uncalibrated curve by natural-origin area share
> (`modules/35_natveg/pot_forest_may24/presolve.gms:248-252`). Within M32 only the `aff` and `ndc` types
> use the uncalibrated curves; `plant` uses the calibrated one.

---

### C2 — 🟠 Major — `default_value` — primary-forest carbon density *does* change over time in a default run

**Doc**: `carbon_balance_conservation.md:201` (and the three "Static" cells at `:194-196`)

> "- Carbon density does NOT change over time (climate change affects future forests, not current primary)"

**Reality**: under the **default** `c52_carbon_scenario = "cc"` (`config/default.cfg:1590`;
`modules/52_carbon/normal_dec17/input.gms:8`), `fm_carbon_density` keeps its full `t_all` trajectory —
the only two places the time dimension is flattened are `input.gms:22` (`nocc`) and `:23` (`nocc_hist`),
both `$if`-gated **off** by default. Primary-forest stock is computed by `q35_carbon_primforest`
(`modules/35_natveg/pot_forest_may24/equations.gms:42-44`) via
`m_carbon_stock(vm_land,fm_carbon_density,"primforest")`, which expands to
`vm_land(j2,"primforest") * sum(ct, fm_carbon_density(ct,j2,"primforest",ag_pools))`
(`core/macros.gms:99-101`) — the **current timestep's** density. So primary-forest carbon density (and
therefore stock at constant area) changes over time in a default run. The same holds for its soilc slice:
`f59_topsoilc_density` is time-varying under the default `c59_som_scenario = "cc"`
(`config/default.cfg:1951`).

There is no code path anywhere that exempts primforest from the climate trajectory — the parenthetical
"climate change affects future forests, not current primary" describes a mechanism that does not exist.
The doc contradicts itself at `:698-700` ("Module 52 updates `fm_carbon_density` over time; Carbon stocks
change even without land-use change").

**Verify**:
```
grep -n 'nocc' $DEV/modules/52_carbon/normal_dec17/input.gms
# → 22: $if "%c52_carbon_scenario%" == "nocc" fm_carbon_density(t_all,…) = fm_carbon_density("y1995",…);
#   23: $if … == "nocc_hist" …           (both inactive under the default cc)
sed -n '99,101p' $DEV/core/macros.gms
# → m_carbon_stock … sum(ct,carbon_density(ct,j2,item,ag_pools)) …  (current timestep, not y1995)
```

**Fix**: replace the bullet with two:
"- No age-class curve: density comes straight from `fm_carbon_density(t_all,j,"primforest",c_pools)`, not
from a Chapman-Richards curve.
- Density is **not** constant over time in a default run: with `c52_carbon_scenario = "cc"`
(`config/default.cfg:1590`) the LPJmL densities are time-varying, so primary-forest carbon changes with
climate even at constant area (see §8.3). Only `nocc` / `nocc_hist`
(`modules/52_carbon/normal_dec17/input.gms:22-23`) freeze it."
Soften the table's "**Static**" to "no age-class tracking (see note)".

---

### C3 — 🟡 Minor — `citation` — `config/default.cfg:1835` is three lines off (actual: 1838)

**Doc**: `carbon_balance_conservation.md:101`

> "⚠️ Do **not** cite `config/default.cfg:1835` for this default: that line omits the `cfg$gms$` prefix its
> siblings carry, so it never reaches GAMS…"

**Reality**: the prefix-less assignment is at **`config/default.cfg:1838`**. Line 1835 is a comment
(`# *   actual: CO2 emissions for pricing are based on the difference of actual carbon stocks between time steps`)
— of which "omits the `cfg$gms$` prefix" is meaningless, since comments never carry it. A reader who checks
1835 finds nothing supporting the warning and may dismiss a defect that is real. The substance holds at the
right line: `1838:c56_carbon_stock_pricing <- "actualNoAcEst"   # def = actualNoAcEst`, while its neighbours
(`:1831 cfg$gms$c56_emis_policy`, `:1843 cfg$gms$maccs`) carry the prefix, and `cfg$gms` is what
`lucode2::manipulateConfig(file.path(ll, "input.gms"), cfg$gms)` (`scripts/start_functions.R:346`) pushes
into the module `$setglobal`s.

**Verify**: `grep -n 'c56_carbon_stock_pricing' $DEV/config/default.cfg` → single hit at `1838`.

**Fix**: `1835` → `1838`.

---

### C4 — 🟡 Minor — `attribution_populate` — urban `vegc`/`litc` zeroing credited to Module 52

**Doc**: `carbon_balance_conservation.md:263-264` (§3.7 table) — `| vegc | Fixed to zero | None | 52 |`,
`| litc | Fixed to zero | None | 52 |`

**Reality**: Module 52 never touches urban `vegc`/`litc`. Its only urban statement is the *soilc* override
`fm_carbon_density(t_all,j,"urban","soilc") = fm_carbon_density(t_all,j,"other","soilc")`
(`modules/52_carbon/normal_dec17/input.gms:35`) — which the third row already attributes correctly to
"52, 59". The zeroing is Module 34's, in its default realization:
`vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0;` (`modules/34_urban/exo_nov21/presolve.gms:8`, with
`ag_pools /vegc, litc/` at `modules/56_ghg_policy/price_aug22/sets.gms:209-210`). The doc's own §7.5
(`:622`) states this correctly, so the table is a local inconsistency — but it is the row a reader trying
to *enable* urban vegetation carbon would follow, and it sends them to the wrong module.

**Verify**:
```
rg -n 'urban' $DEV/modules/52_carbon/normal_dec17/
# → realization.gms:10 (prose), preloop.gms:41 (unrelated comment), input.gms:33-35 (soilc only)
grep -n 'vm_carbon_stock' $DEV/modules/34_urban/exo_nov21/presolve.gms
# → 8:vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0;
```

**Fix**: Module column `52` → `34` for the vegc and litc rows; Source → "fixed by `vm_carbon_stock.fx`,
`modules/34_urban/exo_nov21/presolve.gms:8`". Leave the soilc row at "52, 59".

---

### C5 — 🟡 Minor — `attribution_read` — `vm_maccs_costs` consumer set omits Module 36

**Doc**: `carbon_balance_conservation.md:593` — "`vm_maccs_costs(i,factors)`: Labor and capital costs of
mitigation → to Module 11"

**Reality**: two consumers, both active in a default run —
`modules/11_costs/default/equations.gms:28` (`+ sum(factors,vm_maccs_costs(i2,factors))`; costs default is
`default`, `config/default.cfg:236`) and `modules/36_employment/exo_may22/equations.gms:28`, which reads
the `"labor"` slice to derive agricultural employment (36 has a single realization, selected at
`config/default.cfg:1212`, so the 57→36 edge is unconditional). Role map: `read_by: ["11","36","57"]`.
This matters because `cross_module/modification_safety_guide.md` treats this file as authoritative for the
carbon/GHG dependency surface.

**Verify**: `rg -n 'vm_maccs_costs' $DEV/modules/36_employment/` → `exo_may22/equations.gms:28`.

**Fix**: "→ to Module 11 (total costs, `modules/11_costs/default/equations.gms:28`) **and Module 36**
(the `"labor"` slice only → employment, `modules/36_employment/exo_may22/equations.gms:28`)".

---

### C6 — 🟡 Minor — `attribution_read` — CH₄ `vm_emissions_reg` consumer set omits Module 57

**Doc**: `carbon_balance_conservation.md:573` — "`vm_emissions_reg(i,emis_source,"ch4")`: Regional CH₄
emissions → to Module 56"

**Reality**: `vm_emissions_reg` has two readers (role map `read_by: ["56","57"]`). Besides
`q56_emis_pricing` (`modules/56_ghg_policy/price_aug22/equations.gms:15-17`), Module 57 reads it at
`modules/57_maccs/on_aug22/equations.gms:38,40,48,50` over
`pollutants_maccs57 /ch4, n2o_n_direct/` (`modules/57_maccs/on_aug22/sets.gms:25-26`) — i.e. the CH₄
emissions Module 53 computes feed Module 57's MACC cost integral. The doc records the 53↔57 relationship
only in the other direction (`im_maccs_mitigation`, `:578`), so §7.3 and §7.4 together present a one-way
link where the code has a loop.

**Verify**: `grep -n 'vm_emissions_reg' $DEV/modules/57_maccs/on_aug22/equations.gms` → `38,40,48,50`.

**Fix**: "→ to Module 56 (pricing, `modules/56_ghg_policy/price_aug22/equations.gms:15-17`) **and Module 57**
(MACC cost integration, `modules/57_maccs/on_aug22/equations.gms:38,48` — 57 divides by
`(1 - im_maccs_mitigation)` to recover the unmitigated level)."

---

### C7 — 🟡 Minor — `formula` — §7.2 still carries the four-term shorthand the doc itself retracts

**Doc**: `carbon_balance_conservation.md:552` — `v59_som_target(j,"crop") = Σ(crops) Area × C_ratio × Natural_density`

**Reality**: `q59_som_target_cropland` (`modules/59_som/cellpool_jan23/equations.gms:20-27`) has four
terms — cropland base, SCM uplift, `vm_fallow(j2) * i59_cratio_fallow(j2)`, and
`vm_treecover(j2) * i59_cratio_treecover`. The same document denounces exactly this shorthand at `:134`
("The simplified `Σ(crops) Area × C_ratio × Natural_density` shorthand used in earlier versions of this doc
omitted terms 2-4"). The §3.1 fix was applied; the §7.2 duplicate was left behind, so a reader landing in
§7.2 first gets the retracted version — and it sits three lines below a "Receives" list that correctly names
`vm_fallow` and `vm_treecover`.

**Verify**: `sed -n '20,27p' $DEV/modules/59_som/cellpool_jan23/equations.gms` → all four terms present.

**Fix**: replace with "cropland base + SCM uplift + fallow + treecover, all × natural density — see §3.1 for
the full four-term form (`modules/59_som/cellpool_jan23/equations.gms:20-27`)".

---

### C8 — 🟡 Minor — `default_value` — FLU presented as a selectable category with a default; no such set exists

**Doc**: `carbon_balance_conservation.md:429` ("**FLU** (Land Use): Cropland / Set-aside / Perennial
(default: annual cropland)") and the parallel bullet at `:137` ("Land use: Cropland vs set-aside")

**Reality**: `cellpool_jan23` has no FLU category set and no such default. Its only management sets are
`tillage59 /full_tillage,reduced_tillage,no_tillage/` and
`inputs59 /low_input,medium_input,high_input_nomanure,high_input_manure/`
(`modules/59_som/cellpool_jan23/sets.gms:13-17`) — which is precisely why the adjacent FMG and FI bullets
*are* correct (`i59_tillage_share(i,"full_tillage")=1`, `i59_input_share(i,"medium_input")=1`,
`preloop.gms:52-55`). The land-use factor is resolved **per crop type**:
`f59_cratio_landuse(i,climate59_2019,kcr)` (`input.gms:43`), consumed at `preloop.gms:60-67`. Fallow gets a
separate hard-wired factor (maize × reduced tillage × low input, `preloop.gms:73-77`) and cropland tree
cover a fixed `i59_cratio_treecover = 1` (`preloop.gms:82`).

**Verify**:
```
rg -in 'set.?aside|perennial' $DEV/modules/59_som/
# → only two prose comments (static_jan19/realization.gms:16, cellpool_jan23/input.gms:24); no set member
# positive control: rg -c 'cratio' $DEV/modules/59_som/cellpool_jan23/preloop.gms → 13
```

**Fix**: "- **FLU** (Land Use): resolved **per crop type**, not as selectable IPCC categories —
`f59_cratio_landuse(i,climate59_2019,kcr)` (`modules/59_som/cellpool_jan23/preloop.gms:60-67`). There is no
set-aside/perennial switch; fallow has its own fixed factor `i59_cratio_fallow` (`preloop.gms:73-77`) and
cropland tree cover a fixed `i59_cratio_treecover = 1` (`preloop.gms:82`)." Amend `:137` likewise, and note
that tillage/input shares are not exposed in `config/default.cfg` at all.

---

### C9 — 🟡 Minor — `formula` — §8.4 uses the legacy share (44%) as the 5-year convergence share

**Doc**: `carbon_balance_conservation.md:734` — "Year 5: 44% toward new equilibrium = +4 tC/ha"

**Reality**: `i59_lossrate(t) = 1 - 0.85**m_yeardiff(t)` (`modules/59_som/cellpool_jan23/preloop.gms:45`),
so at 5 years the convergence share is `1 - 0.85^5 = 0.556`; **44% is the legacy remainder**
(`0.85^5 = 0.444`) — exactly as the same doc states correctly at `:402` and `:412`. The derived value
inherits the error: 0.556 × 9 tC/ha = **+5.0**, not +4. The likely origin is the upstream code comment at
`preloop.gms:42` ("resulting in 44% in 5 years, 80% in 10 years and 96% in 20 years"), which is itself
internally inconsistent — 80% and 96% are convergence shares while 44% is a remainder.

**Verify**: `python3 -c "print(1-0.85**5, 1-0.85**10, 1-0.85**20)"` → `0.5563 0.8031 0.9612`; the §5.2 table
(`:401-404`) matches, §8.4 does not.

**Fix**: "Year 5: 56% toward new equilibrium = +5.0 tC/ha"; optionally note that the code comment quotes the
5-year remainder.

---

### C10 — 🟡 Minor — `citation` — four Module-52 signatures given over `t` instead of `t_all`

**Doc**: `carbon_balance_conservation.md:107` (under a "**Verified**:" badge) and `:513-516`; same shorthand at `:699`

**Reality**: all four are declared over `t_all`:
`table fm_carbon_density(t_all,j,land,c_pools)` (`modules/52_carbon/normal_dec17/input.gms:16`) and
`pm_carbon_density_secdforest_ac(t_all,j,ac,ag_pools)` / `pm_carbon_density_other_ac(t_all,…)` /
`pm_carbon_density_plantation_ac(t_all,…)` (`modules/52_carbon/normal_dec17/declarations.gms:9,11,12`).
This is load-bearing for C2 above — the point of `t_all` is that these carry the full annual climate
trajectory, and `start.gms` fills them over `t_all`, not `t`.

**Verify**: `cat -n $DEV/modules/52_carbon/normal_dec17/declarations.gms` → lines 9, 11, 12 all `t_all`.

**Fix**: `t` → `t_all` at `:107`, `:513-516`, `:699`.

---

### C11 — 🟡 Minor — `default_value` — the default `c56_emis_policy` price mask is never mentioned

**Doc**: `carbon_balance_conservation.md:583` — "Both are priced in Module 56 - but by **different paths** …"

**Reality**: the *paths* description is exactly right (verified). What is missing is the default *scope*.
Which sources actually carry a non-zero price is masked by `c56_emis_policy`, default `reddnatveg_nosoil`
(`config/default.cfg:1831`; `modules/56_ghg_policy/price_aug22/input.gms:86`), applied in a loop over
`t_all` at `modules/56_ghg_policy/price_aug22/preloop.gms:87` (hard-coded `reddnatveg_nosoil` for years
≤ `sm_fix_SSP2`) and `:89` (`%c56_emis_policy%` thereafter):
`im_pollutant_prices(...) = im_pollutant_prices(...) * f56_emis_policy(<scenario>,pollutants,emis_source)`.
Per the config's own description (`config/default.cfg:1811`) that scenario prices only "Above ground CO2
emis from LUC in forest and natveg; all CH4 and N2O emissions" — so in a default run cropland/pasture/urban
CO₂ and **all** `soilc` CO₂ are computed by `q56_emis_pricing_co2` but priced at zero. The switch appears
nowhere in this document.
*Scope of verification*: the switch, its default, the masking site and the loop structure are code-verified;
the per-source 0/1 values live in `f56_emis_policy.csv`, a run-time input (`modules/56_ghg_policy/input/`
contains only a `files` manifest), so the "which sources" semantics rest on the config comment.

**Verify**: `grep -n 'c56_emis_policy\|f56_emis_policy' $DEV/modules/56_ghg_policy/price_aug22/preloop.gms`
→ `87`, `89`; `sed -n '78,92p' …/preloop.gms` shows the `loop(t_all, if(m_year(t_all) <= sm_fix_SSP2, …))`.

**Fix**: append to §7.3 — "Both reach the pricing equations, but what carries a non-zero price is masked by
`c56_emis_policy` (default `reddnatveg_nosoil`, `config/default.cfg:1831`), applied at
`modules/56_ghg_policy/price_aug22/preloop.gms:87,89`. Under that default only above-ground CO₂ from forest
and natveg is priced; cropland/pasture/urban CO₂ and all `soilc` CO₂ are computed but priced at zero."

---

### C12 — 🟡 Minor — `set_membership` — §9.1's consistency check never selects the `"actual"` stock slice

**Doc**: `carbon_balance_conservation.md:760-778`

**Reality**: both symbols the snippet reads carry a `stockType` dimension —
`ov_carbon_stock(t,j,land,c_pools,stockType,type)` (`modules/56_ghg_policy/price_aug22/declarations.gms:49`)
and `pcm_carbon_stock(j,land,c_pools,stockType)` (populated for both slices,
`modules/59_som/cellpool_jan23/preloop.gms:30-35`) — while `q52_emis_co2_actual` uses **only** the
`"actual"` slice (`modules/52_carbon/normal_dec17/equations.gms:19`). The snippet's
`dimSums(stock_change, dim=c("cell","land","c_pools"))` never restricts `stockType`, and the two slices
differ by construction for every age-class land pool (`core/macros.gms:104-106`). Additionally
`field="l"` is passed on a **parameter** read (`pcm_carbon_stock`).
*Scope*: the dimensions and the slice mismatch are code-verified; I did not execute the R, so the exact
failure mode of `stopifnot` is inference, not reproduction.

**Fix**: select `[,,"actual"]` on both `carbon_stock_prev` and `carbon_stock_curr` before differencing, and
drop `field="l"` from the `pcm_carbon_stock` read.

---

### C13 — 🟢 Informational — `set_membership` — "appears in exactly these equations" is not exhaustive

**Doc**: `carbon_balance_conservation.md:595` — "**Applies to** (verified against code - the mitigation
factor `(1 - im_maccs_mitigation)` appears in exactly these equations)"

**Reality**: the application list that follows is correct and complete for emission-source equations, but
the literal `(1 - im_maccs_mitigation(...))` also appears twice inside Module 57 itself
(`modules/57_maccs/on_aug22/equations.gms:38,48`) as a **divisor** that grosses mitigated emissions back up
to the unabated baseline for the MACC cost integral. The header is also mildly inconsistent with its own
Module-50 bullet, whose code form is an NUE uplift
`im_maccs_mitigation * X / (1 + im_maccs_mitigation * (X - 1))`
(`modules/50_nr_soil_budget/macceff_aug22/presolve.gms:54-64`), not a `(1 - …)` factor.

**Verify**: `rg -n 'im_maccs_mitigation' $DEV/modules/ | grep -v declarations.gms` → M50 presolve
`:56,58,61,63`; M51 equations `:71`; M53 equations `:29,52,63`; M57 equations `:38,41,48,51`
(M57 preloop `:46-64` is the populator).

**Fix**: "the mitigation factor is applied to emissions in exactly these equations (Module 57's own cost
equations divide *by* `(1 - im_maccs_mitigation)` to back out unmitigated emissions —
`modules/57_maccs/on_aug22/equations.gms:38,48` — which is bookkeeping, not a second application)".

---

## Deferred (not verifiable here, or too weak to file — no edit proposed)

1. **§6.2 k ranges** ("Tropical k ≈ 0.05-0.08" etc.) and **§5.3 stock-change factors** (0.69 / 1.17):
   both come from run-time input tables (`f52_growth_par.csv`, `f59_ch5_F_*`); `modules/*/input/` holds only
   a `files` manifest in a clean checkout. Both are labelled illustrative. Not checked.
2. **§7.4 "Mitigation fractions (0 to ~0.3)"** — derived from `f57_maccs_*_2022`, absent input tables.
3. **§8.4 "SCM equilibrium … high input factor = 1.17"** — SCM uses `high_input_nomanure`
   (`modules/59_som/cellpool_jan23/preloop.gms:88-90`), whereas the doc's 1.17 anchor at `:438` is labelled
   "No-till + High input + **manure**". Worth a maintainer look, but both numbers are input-table values.
4. **§3.1 "Crop-specific equilibrium based on residue production"** — the crop-specific FLU factors are
   exogenous inputs; whether preprocessing derived them from residue production is a preproc-agent question.
5. **§2.3 "Subsoil … Static (fixed from LPJmL via M52)"** — under default `cc`, `i59_subsoilc_density(t_all,j)`
   is time-varying with climate; "static" is true only in the land-use sense the adjacent bullet gives.
   Wording nuance, not filed.
6. **§7.2's lists** omit `vm_landexpansion` (received, `modules/59_som/cellpool_jan23/equations.gms:91`) and
   `vm_nr_som_fertilizer` (provided, read by M50). Both nitrogen-side and the lists are not framed as
   exhaustive. Noted, not filed.
7. **`:876` attributes peatland emission factors to "Humpenoeder et al. 2020"**; `modules/58_peatland/v2/realization.gms:8-17`
   attributes the *methodology* to Humpenöder 2020 and the *factors* to IPCC 2013 Wetlands / Wilson 2016 /
   Tiemeyer 2020. Ambiguous scoping of the parenthetical; too weak to file.
8. **`:987` References "start.gms:8-39"** — the file is 51 lines and the other-land curves are at `:46-51`,
   outside the range. Reference-block metadata; not filed.
9. **`modules/59_som/cellpool_jan23/realization.gms:9` calls itself "the cellpool_aug23 realization"** — an
   upstream MAgPIE typo, not a doc bug; the doc uses `cellpool_jan23` correctly throughout.

---

## Claims verified

~96 code-checkable claims: 14 realization defaults, 9 switch/scalar defaults, 46 file:line citations,
~13 set-membership claims, ~14 attribution (declared/populated/read) claims.
**13 defects: 1 Critical, 1 Major, 10 Minor, 1 Informational.**
