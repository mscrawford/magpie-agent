# R60 depth audit — `cross_module/carbon_balance_conservation.md`

**Lens**: `config_realization` (entry from `config/default.cfg` + realization directory listings)
**Ground truth**: MAgPIE develop worktree, HEAD `2c02843ec` ("Merge pull request #919 from alexkoberle/dyn_reg_tau")
**Auditor**: adversarial depth-first, Opus
**Date**: 2026-08-02

---

## 0. Scope and method

Entry point was `config/default.cfg` and `ls -d modules/NN_*/` for every module the doc touches.
For every `vm_`/`pm_`/`im_`/`fm_`/`pcm_` attribution claim, `audit/integrated/depth_rolemap.json`
was queried first, then confirmed with a both-endpoints grep (`NAME(` **and** `NAME.`) over the
whole `modules/` tree. Absence claims were run with a positive control in the same directory.

**Realization defaults confirmed against `config/default.cfg`** (all match what the doc leads with):

| Module | `cfg$gms$` line | Default | Doc leads with | OK |
|---|---|---|---|---|
| 52 carbon | 1577 | `normal_dec17` | `normal_dec17` | ✅ |
| 53 methane | 1604 | `ipcc2006_aug22` | `ipcc2006_aug22` | ✅ |
| 56 ghg_policy | 1634 | `price_aug22` | `price_aug22` | ✅ |
| 57 maccs | 1843 | `on_aug22` | `on_aug22` | ✅ |
| 58 peatland | 1874 | `v2` | `v2` (cited as :1874) | ✅ |
| 59 som | 1937 | `cellpool_jan23` | `cellpool_jan23` | ✅ |
| 29 cropland | 814 | `detail_apr24` | `detail_apr24` | ✅ |
| 32 forestry | 995 | `dynamic_may24` | `dynamic_may24` | ✅ |
| 34 urban | 1147 | `exo_nov21` | `exo_nov21` | ✅ |
| 35 natveg | 1156 | `pot_forest_may24` | `pot_forest_may24` | ✅ |
| 14 yields | 357 | `managementcalib_aug19` | `managementcalib_aug19` | ✅ |
| 50 nr_soil_budget | 1500 | `macceff_aug22` | `macceff_aug22` | ✅ |
| 51 nitrogen | 1571 | `rescaled_jan21` | `rescaled_jan21` | ✅ |
| 31 past | 988 | `endo_jun13` | (no file cited) | ✅ |
| 11 costs / 36 employment | 236 / 1212 | `default` / `exo_may22` | (single-realization) | ✅ |

**No wrong-default-realization bug found.** The doc's realization discipline is clean — notable
given that 14_yields has gained a second realization (`dynRegPastrTau_apr26`) since the doc's last
touch, and the doc still (correctly) cites `managementcalib_aug19`.

**Scalar / switch defaults confirmed:**

| Switch | Doc claim | Code | Verdict |
|---|---|---|---|
| `s52_growingstock_calib` | `= 1`, hard default, not in `default.cfg` | `modules/52_carbon/normal_dec17/input.gms:46` `/ 1 /`; absent from `config/default.cfg` | ✅ |
| `c52_carbon_scenario` | `cc` / `nocc` / `nocc_hist` | `input.gms:8` `$setglobal ... cc`; `config/default.cfg:1590` | ✅ |
| `c56_carbon_stock_pricing` | `actualNoAcEst`, unreachable from cfg | `modules/56_ghg_policy/price_aug22/input.gms:90`; `config/default.cfg:1838` lacks `cfg$gms$` | ✅ claim, ❌ line no. (CBC-02) |
| `s59_scm_target` | `0` at `config/default.cfg:1978` | `cfg$gms$s59_scm_target <- 0` at :1978 | ✅ exact |
| `c59_irrigation_scenario` | `"on"` at `config/default.cfg:1956` | `cfg$gms$c59_irrigation_scenario <- "on"` at :1956 | ✅ exact |
| `s58_fix_peatland` | `2020` at `config/default.cfg:1931` | `cfg$gms$s58_fix_peatland <- 2020` at :1931 | ✅ exact |
| `s59_cost_scm_recur` | `65 USD17/ha` | `modules/59_som/cellpool_jan23/input.gms:15` `/ 65 /` | ✅ |

**Citations spot-checked and exact** (a sample of ~45 verified; every one below landed on the
claimed content in current develop):
`core/sets.gms:314-318` (emis_oneoff, 21 members) · `core/sets.gms:322` (peatland ∈ emis_annual) ·
`core/sets.gms:324-325` (c_pools) · `core/sets.gms:332-354` (emis_land) · `core/macros.gms:18`
(`m_growth_vegc`) · `core/macros.gms:51` (`m_timestep_length`) ·
`modules/52_carbon/normal_dec17/equations.gms:16-19` · `.../start.gms:17,19-20,28,30-31,43-44` ·
`.../preloop.gms:29-30, 71-73, 114-116` · `.../input.gms:37-43, 46, 47` ·
`modules/56_ghg_policy/price_aug22/declarations.gms:34`, `sets.gms:212-213`, `equations.gms:15-17,
19-22`, `input.gms:90` · `modules/59_som/cellpool_jan23/equations.gms:20-27, 46-52, 61-64`,
`preloop.gms:45`, `input.gms:70`, `realization.gms:21-24` ·
`modules/34_urban/exo_nov21/presolve.gms:8` (character-exact) ·
`modules/29_cropland/detail_apr24/equations.gms:39` and `preloop.gms:46,48` ·
`modules/32_forestry/dynamic_may24/presolve.gms:59,61,68` ·
`modules/35_natveg/pot_forest_may24/presolve.gms:117, 177-180, 240, 242, 248-252` ·
`modules/14_yields/managementcalib_aug19/presolve.gms:44, 64-71` ·
`modules/53_methane/ipcc2006_aug22/equations.gms:29, 52, 63, 70-72` ·
`modules/57_maccs/on_aug22/sets.gms:28-29` (character-exact) ·
`modules/51_nitrogen/rescaled_jan21/sets.gms:15-16`, `preloop.gms:8-10`, `equations.gms:30-39, 62-64, 71` ·
`modules/50_nr_soil_budget/macceff_aug22/presolve.gms:54-64` ·
`modules/58_peatland/v2/equations.gms:91-92`, `realization.gms:8-17`.

**Populator set for `vm_carbon_stock` (§7.5, doc:629-632) is CORRECT** — role map
`populated_by: [29,31,32,34,35,59]`, confirmed by whole-tree grep on both `vm_carbon_stock(` and
`vm_carbon_stock.`:

```
29_cropland/detail_apr24/equations.gms:39   (crop, ag_pools)
31_past/endo_jun13/equations.gms:23         (past, ag_pools)
32_forestry/dynamic_may24/equations.gms:108 (forestry, ag_pools)
34_urban/exo_nov21/presolve.gms:8           (urban, ag_pools, .fx = 0)
35_natveg/pot_forest_may24/equations.gms:43,50,54 (primforest/secdforest/other)
59_som/cellpool_jan23/equations.gms:62      (soilc, all land)
```

**The youngsecdf / uncalibrated-curve block (§3.6, doc:246-255) is fully accurate**, including the
commit reference: `6b00f9dea`, "Fix youngsecdf wood production: use uncalibrated growing stock",
`Wed Jul 1 09:07:26 2026`. Its stated motivation matches the commit body verbatim, and
`modules/35_natveg/pot_forest_may24/equations.gms:166` does now read `im_growing_stock_ysf` for the
youngsecdf harvest term while `:147` still reads the calibrated `im_growing_stock(...,"secdforest")`
for secdforest proper — i.e. the doc's caveat-2 "unverified lead" is correctly characterised.

10 defects follow.

---

## Bugs

### CBC-01 — Major — `default_value`
**Doc**: `carbon_balance_conservation:201`
> "- Carbon density does NOT change over time (climate change affects future forests, not current primary)"

**Reality**: Under the **default** `c52_carbon_scenario = "cc"` (`config/default.cfg:1590`;
`modules/52_carbon/normal_dec17/input.gms:8`), `fm_carbon_density` keeps its full `t_all` time
profile — the flattening assignments at `input.gms:22` (`nocc`) and `:23` (`nocc_hist`) are the ONLY
places the time dimension is collapsed, and both are `$if`-gated off by default. Primary-forest
carbon stock is computed by `q35_carbon_primforest` (`modules/35_natveg/pot_forest_may24/equations.gms:42-44`)
via `m_carbon_stock(vm_land,fm_carbon_density,"primforest")`, which expands to
`vm_land(j2,"primforest") * sum(ct, fm_carbon_density(ct,j2,"primforest",ag_pools))`
(`core/macros.gms:99-101`) — i.e. the **current timestep's** density. Primary-forest carbon density
therefore *does* change over time in a default run. The same holds for its soilc slice:
`f59_topsoilc_density` is time-varying under the default `c59_som_scenario = "cc"`
(`config/default.cfg:1951`; `modules/59_som/cellpool_jan23/input.gms:72`).

The doc contradicts itself: §8.3 (doc:698-700) states "Module 52 updates `fm_carbon_density(t,j,land,c_pools)`
over time; Carbon stocks change even without land-use change".

The parenthetical "(climate change affects future forests, not current primary)" is not a mechanism
that exists anywhere in the code — no grep hit distinguishes primforest from other land types in
module 52 (positive control: `secdforest` matches 5× in `start.gms` / 2× in `input.gms`;
`primforest` matches only in two preloop *comments*).

**Fix**: replace the bullet with
"- No age-class curve: density is taken directly from `fm_carbon_density(t,j,"primforest",c_pools)`, not from a Chapman-Richards curve.
- Density is **not** constant over time in a default run: under the default `c52_carbon_scenario = "cc"` (`config/default.cfg:1590`) the LPJmL densities are time-varying, so primary-forest stock changes with climate even at constant area (see §8.3). Only `c52_carbon_scenario = "nocc"`/`"nocc_hist"` freeze it (`modules/52_carbon/normal_dec17/input.gms:22-23`)."
Also soften the §3.4 table's "**Static**" to "no age-class tracking (see note)".

---

### CBC-02 — Major — `citation`
**Doc**: `carbon_balance_conservation:101`
> "⚠️ Do **not** cite `config/default.cfg:1835` for this default: that line omits the `cfg$gms$` prefix its siblings carry, so it never reaches GAMS…"

**Reality**: the assignment is at **`config/default.cfg:1838`**, not 1835. Line 1835 is a *comment*
(`# *   actual: CO2 emissions for pricing are based on the difference of actual carbon stocks between time steps`),
of which the claim "omits the `cfg$gms$` prefix" is meaningless — comment lines never carry it.
A reader who checks 1835 finds nothing that supports the warning and may dismiss the (true) upstream
defect. The substantive claim is still correct at the right line:
`config/default.cfg:1838` reads `c56_carbon_stock_pricing <- "actualNoAcEst"   # def = actualNoAcEst`,
with no `cfg$gms$` prefix, while its neighbours (`:1831` `cfg$gms$c56_emis_policy`, `:1843`
`cfg$gms$maccs`) have it.

**Fix**: `1835` → `1838`.

---

### CBC-03 — Major — `attribution_read`
**Doc**: `carbon_balance_conservation:593`
> "- `vm_maccs_costs(i,factors)`: Labor and capital costs of mitigation → to Module 11"

**Reality**: `vm_maccs_costs` has **two** consumers, both active in a default run:
- `modules/11_costs/default/equations.gms:28` — `+ sum(factors,vm_maccs_costs(i2,factors))`
- `modules/36_employment/exo_may22/equations.gms:28` — `q36_employment_maccs`, reading the `"labor"` slice

Role map agrees: `vm_maccs_costs → read_by: ["11","36","57"]`. Module 36 has exactly one realization
directory (`exo_may22`) and `config/default.cfg:1212` selects it, so the 57→36 edge is unconditional.
This matters because this file is cited by `cross_module/modification_safety_guide.md` as
authoritative for the carbon/GHG dependency surface — a reader planning a change to `vm_maccs_costs`
would miss module 36 entirely.

**Fix**: "→ to Module 11 (total costs, `modules/11_costs/default/equations.gms:28`) **and Module 36**
(the `"labor"` slice only, converted to employment, `modules/36_employment/exo_may22/equations.gms:28`)".

---

### CBC-04 — Minor — `formula`
**Doc**: `carbon_balance_conservation:552`
> "v59_som_target(j,"crop") = Σ(crops) Area × C_ratio × Natural_density"

**Reality**: this is the exact shorthand that the *same document* denounces at doc:134 ("The
simplified `Σ(crops) Area × C_ratio × Natural_density` shorthand used in earlier versions of this doc
omitted terms 2-4"). The actual `q59_som_target_cropland`
(`modules/59_som/cellpool_jan23/equations.gms:20-27`) has four terms: cropland base, SCM uplift,
`vm_fallow(j2) * i59_cratio_fallow(j2)`, and `vm_treecover(j2) * i59_cratio_treecover`. The §3.1 fix
was applied but the §7.2 duplicate was left behind — a reader who lands in §7.2 first gets the
retracted version. (This is also why §7.2's own "Receives" list correctly names `vm_fallow` and
`vm_treecover` while the formula three lines below drops them.)

**Fix**: replace the §7.2 line with a pointer — `v59_som_target(j,"crop")` = cropland base + SCM
uplift + fallow + treecover, all × natural density — **see §3.1 for the full four-term form**
(`modules/59_som/cellpool_jan23/equations.gms:20-27`).

---

### CBC-05 — Minor — `attribution_read`
**Doc**: `carbon_balance_conservation:595`
> "**Applies to** (verified against code - the mitigation factor `(1 - im_maccs_mitigation)` appears in exactly these equations):"

**Reality**: the literal `(1 - im_maccs_mitigation(...))` also appears twice inside module 57 itself —
`modules/57_maccs/on_aug22/equations.gms:38` and `:48`, as a **divisor** (`vm_emissions_reg(...) /
(1 - im_maccs_mitigation(...))`) that recovers unmitigated emissions for MACC cost integration. So
"exactly these equations" is false as written. The bullet list itself is also internally inconsistent
with the header: the module-50 entry (doc:598) correctly describes an NUE *uplift*, whose code form
(`modules/50_nr_soil_budget/macceff_aug22/presolve.gms:54-64`) is
`im_maccs_mitigation * X / (1 + im_maccs_mitigation * (X - 1))` — not the `(1 - …)` factor at all.

Full whole-tree enumeration of `im_maccs_mitigation` reads (excluding `declarations.gms` and
`not_used.txt`): M50 presolve `:56,58,61,63`; M51 equations `:71`; M53 equations `:29,52,63`;
M57 equations `:38,41,48,51` (M57 preloop `:46-64` is the populator).

**Fix**: reword to "the mitigation factor is applied to emissions in exactly these equations
(module 57's own `q57_maccs_costs_*` divide *by* `(1 - im_maccs_mitigation)` to back out unmitigated
emissions for cost integration — that is bookkeeping, not a second application)".

---

### CBC-06 — Minor — `set_membership`
**Doc**: `carbon_balance_conservation:429` (and the parallel bullet at `:138`)
> "- **FLU** (Land Use): Cropland / Set-aside / Perennial (default: annual cropland)"
> "- Land use: Cropland vs set-aside"

**Reality**: module 59's default realization has **no** FLU category set and no such default. Its
sets are only `tillage59 /full_tillage,reduced_tillage,no_tillage/` and
`inputs59 /low_input,medium_input,high_input_nomanure,high_input_manure/`
(`modules/59_som/cellpool_jan23/sets.gms:13-17`) — which is exactly why the FMG and FI bullets on
the adjacent lines *are* correct (`i59_tillage_share(i,"full_tillage")=1`,
`i59_input_share(i,"medium_input")=1`, `preloop.gms:52-55`). The land-use factor is resolved
per **crop type**: `f59_cratio_landuse(i,climate59_2019,kcr)` (`input.gms:43-47`), consumed at
`preloop.gms:60-67`. A grep for `set.?aside|perennial` across `modules/59_som/` returns only two
prose hits (`static_jan19/realization.gms:16`, `cellpool_jan23/input.gms:24`), never a set member
or a switch (positive control: `cratio` matches 13/4/8/5 times in the four `cellpool_jan23` files).
Fallow is handled by a *separate* hard-coded factor, not an FLU choice: `i59_cratio_fallow(j)` =
maize × reduced tillage × low input (`preloop.gms:73-77`).

**Fix**: "- **FLU** (Land Use): resolved **per crop type**, not as selectable IPCC categories —
`f59_cratio_landuse(i,climate59_2019,kcr)` (`modules/59_som/cellpool_jan23/preloop.gms:60-67`).
There is no set-aside/perennial switch; fallow gets its own fixed factor `i59_cratio_fallow`
(maize + reduced tillage + low input, `preloop.gms:73-77`) and cropland tree cover a fixed
`i59_cratio_treecover = 1` (`preloop.gms:82`)."

---

### CBC-07 — Minor — `attribution_populate`
**Doc**: `carbon_balance_conservation:263-264` (§3.7 Urban table)
> "| vegc | Fixed to zero | None | 52 |"
> "| litc | Fixed to zero | None | 52 |"

**Reality**: module 52 does not zero urban vegc/litc anywhere. The zeroing is done by **module 34**,
in its default realization: `modules/34_urban/exo_nov21/presolve.gms:8` —
`vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0;` (with `ag_pools = /vegc, litc/`,
`modules/56_ghg_policy/price_aug22/sets.gms:209-210`). Module 52's only urban-specific line is the
*soilc* override at `modules/52_carbon/normal_dec17/input.gms:35`
(`fm_carbon_density(t_all,j,"urban","soilc") = fm_carbon_density(t_all,j,"other","soilc")`), which the
third table row already attributes correctly to "52, 59". The doc's own §7.5 (doc:621-622) gets this
right, so the table row is a local inconsistency — but it is the row a reader trying to *enable*
urban vegetation carbon would follow, sending them to the wrong module.

**Fix**: change the Module column for the vegc and litc rows from `52` to `34` and note the
mechanism: "fixed by `vm_carbon_stock.fx` in `modules/34_urban/exo_nov21/presolve.gms:8`".

---

### CBC-08 — Minor — `attribution_read`
**Doc**: `carbon_balance_conservation:573`
> "- `vm_emissions_reg(i,emis_source,"ch4")`: Regional CH₄ emissions → to Module 56"

**Reality**: `vm_emissions_reg` has **two** readers — role map `read_by: ["56","57"]`, confirmed by
grep. Besides `q56_emis_pricing` (`modules/56_ghg_policy/price_aug22/equations.gms:15-17`), module 57
reads it at `modules/57_maccs/on_aug22/equations.gms:38,40,48,50` over
`pollutants_maccs57 = /ch4, n2o_n_direct/` (`modules/57_maccs/on_aug22/sets.gms:25-26`) — i.e. the
CH₄ emissions computed by module 53 feed module 57's MACC cost equations. The doc records the
53→57 edge only in the opposite direction (`im_maccs_mitigation` at doc:578); the 53→57 emissions
edge appears nowhere, so §7.3/§7.4 together describe a one-way link where the code has a loop.

**Fix**: "→ to Module 56 (pricing, `modules/56_ghg_policy/price_aug22/equations.gms:15-17`)
**and Module 57** (MACC cost integration, `modules/57_maccs/on_aug22/equations.gms:38,48` —
note 57 divides by `(1 - im_maccs_mitigation)` to recover the unmitigated level)."

---

### CBC-09 — Minor — `set_membership`
**Doc**: `carbon_balance_conservation:107, 513-516`
> "**Verified**: Module 52 (`fm_carbon_density(t,j,land,c_pools)`)"
> "- `fm_carbon_density(t,j,land,c_pools)` … `pm_carbon_density_plantation_ac(t,j,ac,ag_pools)` … `pm_carbon_density_secdforest_ac(t,j,ac,ag_pools)` … `pm_carbon_density_other_ac(t,j,ac,ag_pools)`"

**Reality**: all four are declared over **`t_all`**, not `t`:
`table fm_carbon_density(t_all,j,land,c_pools)` (`modules/52_carbon/normal_dec17/input.gms:16`), and
`pm_carbon_density_secdforest_ac(t_all,j,ac,ag_pools)` /
`pm_carbon_density_other_ac(t_all,j,ac,ag_pools)` /
`pm_carbon_density_plantation_ac(t_all,j,ac,ag_pools)`
(`modules/52_carbon/normal_dec17/declarations.gms:9,11,12`). This is load-bearing for the doc's own
CBC-01 topic — the whole point of `t_all` is that these carry the full annual climate trajectory, and
they are filled in `start.gms` over `t_all`, not `t`. Carrying a `Verified:` badge on the wrong index
set compounds it.

**Fix**: `t` → `t_all` in all four signatures (doc:107, 513, 514, 515, 516). Note doc:699 has the same
shorthand and should follow.

---

### CBC-10 — Minor — `default_value`
**Doc**: `carbon_balance_conservation:583`
> "Both are priced in Module 56 - but by **different paths**: …"

**Reality**: the *paths* description is exactly right (verified: `q56_emis_pricing` at
`modules/56_ghg_policy/price_aug22/equations.gms:15-17` over `emis_annual`; `q56_emis_pricing_co2` at
`:19-22` recomputing from `pcm_carbon_stock - vm_carbon_stock`; module 56 never reads module 52's
`vm_emissions_reg(...,"co2_c")` because `q56_emis_pricing` is restricted to `emis_annual` and the CO₂
land-use sources live in `emis_oneoff`). What is missing is the default *scope*: the price applied to
each source is masked by `c56_emis_policy`, whose default is `"reddnatveg_nosoil"`
(`config/default.cfg:1831`; `modules/56_ghg_policy/price_aug22/input.gms:86`), applied at
`modules/56_ghg_policy/price_aug22/preloop.gms:87` as
`im_pollutant_prices(...) = im_pollutant_prices(...) * f56_emis_policy("reddnatveg_nosoil",pollutants,emis_source)`.
Per `config/default.cfg:1811` that policy prices only "Above ground CO2 emis from LUC in forest and
natveg; all CH4 and N2O emissions" — so in a default run cropland/pasture/urban CO₂ and **all**
`soilc` CO₂ carry a zero price even though `q56_emis_pricing_co2` computes them. The switch is not
mentioned anywhere in the document. *(Scope of verification: the switch, its default and the masking
site are code-verified; the per-source 0/1 mask values live in `f56_emis_policy`, an input table not
present in the repo, so the semantics above rest on the `config/default.cfg:1810-1811` comment.)*

**Fix**: append to §7.3 — "Both reach the pricing equations, but what actually carries a non-zero
price is masked by `c56_emis_policy` (default `reddnatveg_nosoil`, `config/default.cfg:1831`),
applied at `modules/56_ghg_policy/price_aug22/preloop.gms:87`. Under that default only above-ground
CO₂ from forest and natveg is priced; cropland/pasture/urban CO₂ and all `soilc` CO₂ are computed but
priced at zero."

---

## Deferred (not verifiable / not asserted as bugs)

1. **§6.2 k-value ranges** ("Tropical k ≈ 0.05-0.08" etc.) and **§5.3 example stock-change factors**
   (0.69 / 1.17): both come from input tables (`f52_growth_par.csv`, `f59_ch5_F_*`) that are not in
   the repo (`modules/*/input/` holds only a `files` manifest — the `.cs3`/`.csv` are run-time
   products). Both are explicitly labelled illustrative/typical, so no claim is being made about
   code. Not checked.
2. **§7.4 "Mitigation fractions (0 to ~0.3)"** — `im_maccs_mitigation` is derived from
   `f57_maccs_ch4_2022` / `f57_maccs_n2o_2022` (`modules/57_maccs/on_aug22/input.gms:32-54`), input
   tables absent from the repo. Range unverifiable here.
3. **§9.1 R verification snippet** — `ov_carbon_stock` is 6-D `(t,j,land,c_pools,stockType,type)`
   (`modules/56_ghg_policy/price_aug22/declarations.gms:49`), and the snippet never selects
   `stockType = "actual"`, so `emissions_calculated` would retain a `stockType` dimension that
   `emissions_co2` lacks. This looks like it would fail, but it is advisory R pseudo-code I did not
   execute — flagging it would be a claim about runtime behaviour I have not reproduced.
4. **§7.2 "Receives" list for module 59** omits `vm_landexpansion(j2,"crop")`
   (`modules/59_som/cellpool_jan23/equations.gms:91`) and the "Provides" list omits
   `vm_nr_som_fertilizer` (read at `modules/50_nr_soil_budget/macceff_aug22/equations.gms:30`).
   Both are on the nitrogen side, not the carbon balance the section documents; the lists are not
   framed as exhaustive. Noted, not filed.
5. **doc:876 attributes peatland GHG emission factors to "Humpenoeder et al. 2020"**;
   `modules/58_peatland/v2/realization.gms:8-17` attributes the *methodology* to Humpenöder 2020 and
   the *emission factors* to IPCC 2013 Wetland supplement / Wilson 2016 (boreal, tropical) and
   Tiemeyer 2020 (temperate). Ambiguous whether the doc's parenthetical scopes the methodology or the
   factors; too weak to file.
6. **doc:987 "Module 52 growth: `modules/52_carbon/normal_dec17/start.gms:8-39`"** — the file is 51
   lines and the other-land curves are at `:46-51`, outside the cited range. Arguably a truncated
   range, but the References block is metadata and `8-39` does cover plantation + secdforest. Not
   filed.
7. **§7.1 / §8.3 never state which `c52_carbon_scenario` is default** (they list `cc` first, which is
   in fact the default). Borderline capability-vs-default; folded into CBC-01's fix rather than filed
   separately.

---

## Claims verified

~96 code-checkable claims: 18 realization defaults, 7 scalar/switch defaults, ~45 file:line citations,
12 set-membership claims, ~14 attribution (declared/populated/read) claims. 10 defects found:
3 Major, 7 Minor, 0 Critical.
