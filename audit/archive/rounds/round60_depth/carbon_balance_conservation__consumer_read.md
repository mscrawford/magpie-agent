# R60 depth audit — `cross_module/carbon_balance_conservation.md`

**Lens**: `consumer_read` (enter from the consumer side: presolve/postsolve/equation-RHS of every module the doc names as a reader, plus whole-tree greps of both `NAME(` and `NAME.` for each interface var)
**Ground truth**: MAgPIE `develop` read-only worktree, HEAD `2c02843ec` ("Merge pull request #919 from alexkoberle/dyn_reg_tau")
**Role map**: `audit/integrated/depth_rolemap.json` (checked first for every DECLARED/POPULATED/READ claim, then confirmed both endpoints in code)
**Claims checked**: ~118 load-bearing, code-checkable claims
**Bugs**: 1 Critical, 2 Major, 9 Minor, 1 Informational

---

## What the doc gets right (verified, not assumed)

Recorded because a clean result is evidence about the doc, and because these are the claims most likely to be re-flagged by a future auditor who does not re-derive them.

- **Populator set of `vm_carbon_stock` (§7.5) is complete and correct.** Role map `populated_by = [29,31,32,34,35,59]`; whole-tree grep of `vm_carbon_stock` finds exactly `modules/29_cropland/detail_apr24/equations.gms:39`, `modules/31_past/endo_jun13/equations.gms:23`, `modules/32_forestry/dynamic_may24/equations.gms:108`, `modules/34_urban/exo_nov21/presolve.gms:8`, `modules/35_natveg/pot_forest_may24/equations.gms:43,50,54`, `modules/59_som/cellpool_jan23/equations.gms:62`. The doc lists all six.
- **The `actual` / `actualNoAcEst` split (§2.3) is real and correctly attributed.** `stockType` declared `modules/56_ghg_policy/price_aug22/sets.gms:212-213`; M52 reads `"actual"` (`modules/52_carbon/normal_dec17/equations.gms:19`); M56 reads `"%c56_carbon_stock_pricing%"` (`modules/56_ghg_policy/price_aug22/equations.gms:22`) whose `$setglobal` default is `actualNoAcEst` (`modules/56_ghg_policy/price_aug22/input.gms:90`). The doc's conclusion — priced CO₂ and reported CO₂ come off different slices in a default run — holds.
- **The `config/default.cfg` missing-`cfg$gms$`-prefix warning is still live** (only the line number drifted — see B4).
- **The parallel-not-serial claim (§7.3) is correct** and survives a both-endpoints check: `q56_emis_pricing` (`modules/56_ghg_policy/price_aug22/equations.gms:15-17`) reads `vm_emissions_reg` only over `emis_annual`; CO₂ from LUC is recomputed in `q56_emis_pricing_co2` (`:19-22`). M56 never consumes M52's `emis_oneoff` `co2_c` output. No hand-off.
- **The whole FRA-2025 calibration warning block is accurate on every line number checked**: `s52_growingstock_calib` default `1` (`modules/52_carbon/normal_dec17/input.gms:46`, absent from `config/default.cfg` — confirmed by grep), `preloop.gms:29-30, 71-73, 114-116`, `start.gms:43-44`, and all five uncalibrated-curve consumers (`modules/14_yields/managementcalib_aug19/presolve.gms:66`, `modules/29_cropland/detail_apr24/preloop.gms:46,48`, `modules/32_forestry/dynamic_may24/presolve.gms:59,61,68`, `modules/35_natveg/pot_forest_may24/presolve.gms:117,242`). Its one defect is an omission, B1.
- **The youngsecdf invariant (§3.6) is accurate**, including commit `6b00f9dea` (2026-07-01, "Fix youngsecdf wood production: use uncalibrated growing stock") and the `im_growing_stock_ysf` citation `modules/14_yields/managementcalib_aug19/presolve.gms:64-71`. Caveat 2 (secdforest blend vs calibrated growing stock) is correctly labelled an unverified lead and its algebra checks out (`q35_prod_secdforest` at `modules/35_natveg/pot_forest_may24/equations.gms:144-147` reads calibrated `im_growing_stock`; `q35_carbon_secdforest` at `:49-51` reads the blend built at `presolve.gms:248-252`).
- **MACC applicability (§7.4) is correct in all four sub-claims**, including the two negatives: residue burning carries no mitigation factor (`modules/53_methane/ipcc2006_aug22/equations.gms:70-72`; `maccs_ch4 / rice_ch4, ent_ferm_ch4, awms_ch4 /` at `modules/57_maccs/on_aug22/sets.gms:28-29`), and rice has no N₂O at all (`emis_source_n51` at `modules/51_nitrogen/rescaled_jan21/sets.gms:15-16` excludes rice; `preloop.gms:8-10` fixes everything else to zero).
- **Peatland (§10.2 item 7) is correct**: `v2` default (`config/default.cfg:1874`), `s58_fix_peatland = 2020` (`:1931`), `q58_peatland_emis` (`modules/58_peatland/v2/equations.gms:91-92`), `peatland ∈ emis_annual` (`core/sets.gms:322`), peat absent from `c_pools` (`core/sets.gms:324-325`).
- **The §5.2 SOM convergence table is arithmetically right and is more accurate than the code's own comment**, which says "44% in 5 years" (`modules/59_som/cellpool_jan23/preloop.gms:42`) where `1-0.85^5 = 55.6%`. The doc's table has 56%/44% the right way round. (§8.4 then contradicts it — B5.)

---

## Bugs

### B1 — Critical — `attribution_read` — omitted consumer of the FRA-calibrated growth curve

**Doc** (`carbon_balance_conservation:180`, and the byte-identical duplicate at `:479`):
> "M14 and M35 read the CALIBRATED curve as well - M14 for regular secdforest growing stock (`modules/14_yields/managementcalib_aug19/presolve.gms:44`), M35 for secdforest carbon density, which it BLENDS with the uncalibrated curve by natural-origin area share (`modules/35_natveg/pot_forest_may24/presolve.gms:248-252`)."

**Code**: three modules read a calibrated curve, not two. **Module 32 assigns the FRA-calibrated `pm_carbon_density_plantation_ac` to the carbon density of established timber plantations**:

```
modules/32_forestry/dynamic_may24/presolve.gms:65
p32_carbon_density_ac(t,j,"plant",ac,ag_pools) = pm_carbon_density_plantation_ac(t,j,ac,ag_pools);
```

and that is the value `q32_carbon` turns into the forestry slice of the carbon-stock interface:

```
modules/32_forestry/dynamic_may24/equations.gms:108
q32_carbon(j2,ag_pools,stockType) .. vm_carbon_stock(j2,"forestry",ag_pools,stockType) =e=
            m_carbon_stock_ac(v32_land,p32_carbon_density_ac,"type32,ac","type32,ac_sub");
```

M14 also reads the calibrated plantation curve (`modules/14_yields/managementcalib_aug19/presolve.gms:26`, feeding `im_growing_stock(...,"forestry")`), which the doc likewise omits.

**Why this is Critical, not Major.** The sentence is the doc's authoritative summary of the calibration's blast radius, and the reader is explicitly told what M32 reads two clauses earlier — "M32's afforestation and NDC curves (`.../presolve.gms:59,61,68`)" — citing lines 59, 61 and 68 while skipping line 65, which sits between them. A reader auditing or changing `s52_growingstock_calib` would conclude M32 is a pure uncalibrated consumer and would miss the entire forestry vegetation-carbon pool. This is the R20 anchor case (immutable, rubric §1): "doc cited `pm_carbon_density_ac` as having three consumers when commit added two more … → Critical (doc said wrong consumer set; user would have missed two modules in a refactor)".

**Note on ordering (do not over-correct):** `modules/32_forestry/dynamic_may24/preloop.gms:18,56` also reference `pm_carbon_density_plantation_ac`, but the `preloop` phase runs module-by-module in numeric order (`modules/include.gms:12-57`, driven by `core/calculations.gms:15`), so M32's preloop executes *before* M52's calibration overwrite and sees uncalibrated values. Only the `presolve` read at `:65` is a genuine calibrated-curve read. A fix that lists `preloop.gms:18,56` as calibrated consumers would be wrong.

**Fix**: change to "M14, M32 and M35 read the CALIBRATED curve as well — M14 for regular secdforest and plantation growing stock (`modules/14_yields/managementcalib_aug19/presolve.gms:44,26`), **M32 for the carbon density of established timber plantations** (`modules/32_forestry/dynamic_may24/presolve.gms:65`, which feeds `q32_carbon` → `vm_carbon_stock(j,"forestry",...)`; note M32's *preloop* reads at `:18,56` run before M52's preloop and therefore see uncalibrated values), M35 for secdforest carbon density, which it BLENDS …". Apply to both copies (`:180` and `:479`).

---

### B2 — Major — `default_value` — fire disturbance is off in a default run

**Doc** (`carbon_balance_conservation:870`, §10.2 item 6; same claim at `:626` and `:221`):
> "Fire disturbances (Module 35) cause carbon loss via stock change"
> (`:626`) "Disturbances (fire, shifting agriculture) → reset age classes → carbon loss"

**Code**: `s35_forest_damage` default is **2** (`modules/35_natveg/pot_forest_may24/input.gms:27`, confirmed at `config/default.cfg:1184`). Branch 2 applies **only** the `shifting_agriculture` share, and fades it to zero by `s35_forest_damage_end = 2050` (`config/default.cfg:1186`):

```
modules/35_natveg/pot_forest_may24/presolve.gms:19-22
if(s35_forest_damage=2,
  p35_disturbance_loss_secdf(t,j,ac_sub) = pc35_secdforest(j,ac_sub) * sum(cell(i,j),f35_forest_lost_share(i,"shifting_agriculture"))*m_timestep_length_forestry*(1 - p35_damage_fader(t));
```

The `wildfire` member of `driver_source` (`modules/35_natveg/pot_forest_may24/sets.gms:12`) enters only through `combined_loss` (`sets.gms:14-15`) under `s35_forest_damage = 3` (`presolve.gms:24-27`) — a value the scalar's own description string does not even list. The generic shock branch (`s35_forest_damage = 4`) is likewise inactive, and `c35_shock_scenario` defaults to `"none"` (`config/default.cfg:1200`).

So in a default run there is no wildfire disturbance at all, and the one disturbance stream that does run (which the code header at `presolve.gms:9` calls "shifting agriculture fires") is faded out after 2050. This is precisely the pattern AGENT.md's PRIMARY DIRECTIVE names as its canonical anti-example.

**Fix**: replace with — "Disturbance losses (Module 35) cause carbon loss via stock change, but which disturbance depends on `s35_forest_damage` (default **2**, `config/default.cfg:1184`): only the `shifting_agriculture` share of `f35_forest_lost_share` is applied, faded to zero by `s35_forest_damage_end = 2050`. The `wildfire` driver is applied only at `s35_forest_damage = 3` (`modules/35_natveg/pot_forest_may24/presolve.gms:24-27`) and the generic shock scenarios only at `= 4` with `c35_shock_scenario ≠ none`. Emissions are in any case lumped with general LUC emissions, so fire cannot be tracked separately even when enabled." Apply the same qualification at `:221` and `:626`.

---

### B3 — Major — `formula` — §6.3 growth table does not follow from its own stated parameters

**Doc** (`carbon_balance_conservation:485-500`): "**Illustrative Example** (tropical plantation): A = 100 tC/ha, k = 0.06, m = 2.0", then a table giving 14 / 26 / 44 / 58 / 75 / 88 / 93 tC/ha at 5 / 10 / 20 / 30 / 50 / 80 / 100 years.

**Code**: the model's growth macro is `$macro m_growth_vegc(S,A,k,m,ac) S + (A-S)*(1-exp(-k*(ac*5)))**m` (`core/macros.gms:18`) — the same formula the doc quotes at `:450`. With A=100, k=0.06, m=2.0 it yields **6.7 / 20.4 / 48.8 / 69.7 / 90.3 / 98.4 / 99.5**. The table is off by 2.1× at 5 years and by 15-20% at 30-100 years, and its *shape* is wrong in the opposite direction from the doc's own claim: the tabulated values are a monomolecular curve `100·(1−e^(−0.03t))` (m = 1), i.e. fastest growth at t = 0, whereas m = 2.0 gives the sigmoid the doc asserts at `:828-831` ("Should follow sigmoidal pattern / Young plantations: slow growth"). §8.2 (`:676,682`) reuses the same numbers and attributes them to Chapman-Richards.

**Fix**: recompute the table from `m_growth_vegc` with the stated k = 0.06, m = 2.0 (0 / 6.7 / 20.4 / 48.8 / 69.7 / 90.3 / 98.4 / 99.5 / ~100), or restate the parameters as k = 0.03, m = 1.0 and drop the "sigmoidal" characterisation. Propagate the corrected 20-year and 50-year values into §8.2.

---

### B4 — Minor — `citation` — `config/default.cfg` line drift on the unreachable-switch warning

**Doc** (`carbon_balance_conservation:101`): "Do **not** cite `config/default.cfg:1835` for this default: that line omits the `cfg$gms$` prefix its siblings carry…"

**Code**: the prefix-less assignment is at **`config/default.cfg:1838`**; line 1835 is a comment (`# *   actual: CO2 emissions for pricing are based on the difference of actual carbon stocks between time steps`). The substantive claim is still true — `c56_carbon_stock_pricing <- "actualNoAcEst"` at `:1838` lacks the `cfg$gms$` prefix that `cfg$gms$c56_emis_policy` (`:1831`) and `cfg$gms$maccs` (`:1843`) carry.

**Fix**: `1835` → `1838`.

---

### B5 — Minor — `formula` — §8.4 five-year convergence uses the legacy share

**Doc** (`carbon_balance_conservation:734`): "Year 5: 44% toward new equilibrium = +4 tC/ha"

**Code**: `i59_lossrate(t) = 1-0.85**m_yeardiff(t)` (`modules/59_som/cellpool_jan23/preloop.gms:45`) → `1-0.85^5 = 55.6%`. 44% is the *remaining legacy* share, exactly as the doc's own §5.2 table states at `:401`. The following two rows (Year 10 = 80% → +7.2; Year 20 = 96% → +8.6) are correct, which isolates the error to the 5-year row. (The upstream code comment at `preloop.gms:42` makes the same slip — "44% in 5 years" — so the fix should not be reverted by a future reader who checks only that comment.)

**Fix**: "Year 5: 56% toward new equilibrium = +5.0 tC/ha".

---

### B6 — Minor — `formula` — §8.1 gradual soil-carbon emission arithmetic

**Doc** (`carbon_balance_conservation:656`): "Gradual (soilc over 20 years): 30 tC/ha × 100 Mha × (44/12) / 20 years = **458 Tg CO₂/year**"

**Code/arithmetic**: 30 tC/ha × 100 Mha = 3,000 Tg C; × 44/12 = 11,000 Tg CO₂; ÷ 20 = **550 Tg CO₂/yr**. 458 corresponds to 25 tC/ha, but the table at `:649` states a 30 tC/ha soil loss (80 → 50), and the totals row depends on it (250 − 65 = 185 = 140 + 15 + 30). The immediate-emission figure on the previous line (56,833) is correct, so only this line is wrong.

**Fix**: `458` → `550`.

---

### B7 — Minor — `attribution_populate` — urban vegc/litc zeroing attributed to Module 52

**Doc** (`carbon_balance_conservation:263-265`, §3.7 table): rows "vegc | Fixed to zero | None | **52**" and "litc | Fixed to zero | None | **52**".

**Code**: Module 52 contains nothing that zeroes urban vegc or litc — a grep of `urban` across `modules/52_carbon/normal_dec17/*.gms` returns only the soilc override (`input.gms:35`, `fm_carbon_density(t_all,j,"urban","soilc") = fm_carbon_density(t_all,j,"other","soilc")`) and a realization-doc mention. The zeroing is Module 34: `vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0` (`modules/34_urban/exo_nov21/presolve.gms:8`), which §7.5 (`:622`) states correctly. The soilc row's "52, 59" is right.

**Fix**: change the Module column for the vegc and litc rows from `52` to `34` and add the citation, matching §7.5.

---

### B8 — Minor — `attribution_read` — `vm_maccs_costs` has a second consumer

**Doc** (`carbon_balance_conservation:593`): "`vm_maccs_costs(i,factors)`: Labor and capital costs of mitigation → to Module 11"

**Code**: role map `read_by = [11, 36, 57]`; grep confirms `modules/11_costs/default/equations.gms:28` and **`modules/36_employment/exo_may22/equations.gms:28`**, where the labor slice is converted into employment:
`=e= (vm_maccs_costs(i2,"labor")) * (1 / sum(ct,f36_weekly_hours(ct,i2)*s36_weeks_in_year*pm_hourly_costs(ct,i2,"scenario")));`
(`exo_may22` is Module 36's only realization.)

**Fix**: "→ to Module 11 (total costs, `modules/11_costs/default/equations.gms:28`) and Module 36 (labor slice → employment, `modules/36_employment/exo_may22/equations.gms:28`)".

---

### B9 — Minor — `attribution_read` — `vm_emissions_reg` CH₄ also flows back to Module 57

**Doc** (`carbon_balance_conservation:573`): "`vm_emissions_reg(i,emis_source,"ch4")`: Regional CH₄ emissions → to Module 56"

**Code**: role map `read_by = [56, 57]`. Module 57 reads the same interface to size MACC costs:
`modules/57_maccs/on_aug22/equations.gms:38` (labor) and `:48` (capital) — `* vm_emissions_reg(i2,emis_source,pollutants_maccs57) / (1 - im_maccs_mitigation(ct,i2,emis_source,pollutants_maccs57))`, with `pollutants_maccs57 / ch4, n2o_n_direct /` (`modules/57_maccs/on_aug22/sets.gms:25-26`). This closes a loop the doc otherwise presents as one-way (§7.3 "Receives im_maccs_mitigation from Module 57"; §7.4 "Provides im_maccs_mitigation"): M57 → `im_maccs_mitigation` → M53 → `vm_emissions_reg` → M57's cost equations.

**Fix**: "→ to Module 56 for pricing (`modules/56_ghg_policy/price_aug22/equations.gms:15-17`) and back to Module 57, which divides out the mitigation factor to recover baseline emissions for the MACC cost integral (`modules/57_maccs/on_aug22/equations.gms:38,48`)".

---

### B10 — Minor — `attribution_read` — third reader of `vm_carbon_stock`, and no named populator of `pcm_carbon_stock`

**Doc** (`carbon_balance_conservation:101`): "The **two** readers then pick different slices"; and (`:632`) "All populated slices flow to Module 52 and Module 56".

**Code**: role map `vm_carbon_stock.read_by = [52, 56, 59]`. The third read is solution-level and invisible to a `vm_carbon_stock(` grep — it needs the `vm_carbon_stock.` form:
`modules/59_som/cellpool_jan23/postsolve.gms:13` — `pcm_carbon_stock(j,land,"soilc",stockType) = vm_carbon_stock.l(j,land,"soilc",stockType);`
Its counterpart for the above-ground pools is `modules/56_ghg_policy/price_aug22/postsolve.gms:8` — `pcm_carbon_stock(j,land,ag_pools,stockType) = vm_carbon_stock.l(j,land,ag_pools,stockType);`
Together these two postsolve statements are the *only* populators of `pcm_carbon_stock` (role map `populated_by = [56, 59]`), i.e. they are what makes §4.1's "Previous stock" exist. The doc names neither, and §4.1 (`:296`) says only "from end of previous timestep".

The statements as written are not false (M52 and M56 are the only *equation-level* readers), but the enumeration is incomplete in exactly the direction the doc's own §4.1 depends on.

**Fix**: at `:101` say "the two readers **in the optimization** then pick different slices"; add to §7.2 or §4.1: "`pcm_carbon_stock` is written in postsolve — above-ground pools by Module 56 (`modules/56_ghg_policy/price_aug22/postsolve.gms:8`), the soilc slice by Module 59 (`modules/59_som/cellpool_jan23/postsolve.gms:13`) — both by solution-level (`.l`) read of `vm_carbon_stock`."

---

### B11 — Minor — `mechanism` — why the two `stockType` slices differ is never stated

**Doc** (`carbon_balance_conservation:101`): "the populating equations are indexed over the free set and fill **both** slices."

**Code**: true, but the equations do not fill them with the same value, and the doc's whole point (priced ≠ reported CO₂) depends on the difference. The mechanism is in the macro, not the equations:

```
core/macros.gms:104-106
$macro m_carbon_stock_ac(land,carbon_density,sets,sets_sub) \
   sum((&&sets),     land(j2,&&sets)     * ...)$(sameas(stockType,"actual")) + \
   sum((&&sets_sub), land(j2,&&sets_sub) * ...)$(sameas(stockType,"actualNoAcEst"))
```

`actual` sums over the full age-class set, `actualNoAcEst` over `ac_sub` — i.e. it drops the newly established age classes. Used by M32 (`equations.gms:109`), M35 (`:51,:55`) and M29's tree cover (`:42`). For land without age classes the non-age-class macro `m_carbon_stock` (`core/macros.gms:99-101`) is byte-identical across the two slices, so M31's pasture stock is the same in both.

**Fix**: append "— but not with the same value: `m_carbon_stock_ac` (`core/macros.gms:104-106`) sums the `actual` slice over the full `ac` set and the `actualNoAcEst` slice over `ac_sub`, excluding newly established age classes; non-age-class pools (`m_carbon_stock`, `core/macros.gms:99-101`) are identical in both slices."

---

### B12 — Minor — `mechanism` — cropland soil-carbon equilibrium is not driven by modelled residue production

**Doc** (`carbon_balance_conservation:122`): "Crop-specific equilibrium based on residue production"; and (`:434`) "**Crop-specific**: Different crops produce different residue amounts".

**Code**: `q59_som_target_cropland` (`modules/59_som/cellpool_jan23/equations.gms:20-27`) contains no residue term — no `vm_res_*`, no residue variable of any kind. Crop specificity enters entirely through the exogenous IPCC land-use stock-change table `f59_cratio_landuse(i,climate59_2019,kcr)` (declared `modules/59_som/cellpool_jan23/input.gms:43-47`, read from `f59_ch5_F_LU_2019reg.cs3`), combined in `i59_cratio` at `preloop.gms:60-67`. Residue *inputs* are conceptually the IPCC **FI** factor, which MAgPIE holds fixed at `medium_input` (`preloop.gms:55`) and does not link to modelled residue flows. This is the parameterization-vs-mechanism distinction AGENT.md makes binding.

**Fix**: "Crop-specific equilibrium via exogenous IPCC FLU stock-change factors per MAgPIE crop type (`f59_cratio_landuse`, `modules/59_som/cellpool_jan23/input.gms:43-47`) — the crop dependence is a lookup, not a function of modelled residue production."

---

### B13 — Informational — `citation` — stale range for the Module 52 growth code

**Doc** (`carbon_balance_conservation:987`, References): "Module 52 growth: `modules/52_carbon/normal_dec17/start.gms:8-39`"

**Code**: growth-curve code now spans `start.gms:8-51`. Lines 33-44 are calibration-parameter initialization and the uncalibrated-curve snapshot, and the other-land curves are at `:46-51` — outside the cited range.

**Fix**: `start.gms:8-39` → `start.gms:8-51`.

---

## Deferred (not bugs; recorded so the next auditor does not re-derive them)

- §3.1 (`:140`) / §5.3 (`:428`) describe FLU as "Cropland / Set-aside / Perennial". `f59_cratio_landuse` is indexed by MAgPIE crop type `kcr` with no set-aside member; fallow is handled separately with `"maiz"` FLU + reduced tillage + low input (`modules/59_som/cellpool_jan23/preloop.gms:73-77`). Reads as a description of the IPCC scheme rather than of the code, so not flagged.
- §8.4 (`:730`) "SCM equilibrium … high input factor = 1.17" vs code, which uses `high_input_nomanure` for SCM (`preloop.gms:88-90`) while §5.3's 1.17 anchor example is "High input + manure". Both are labelled illustrative and I could not read the CSV factor values, so I cannot say which is numerically right.
- §7.4 (`:592`) "`im_maccs_mitigation` … Mitigation fractions (0 to ~0.3)" — range depends on `f57_maccs_*` input data I did not read.
- §7.2 (`:547`) "`vm_land(j,land)`: Non-cropland areas from Module 10" understates the read: M59 also uses `vm_land` for *all* land in `q59_carbon_soil` (`equations.gms:63`), and `vm_land` is populated by 10/29/31/32/34/35, not Module 10 alone. Direction and origin are right; too soft to flag.
- §9.1's R snippet (`:771`) assumes a leading 5-year timestep; the GAMS macro gives 1 for `ord(t)=1` (`core/macros.gms:51`). The snippet's own comment flags this, so it is self-consistent.
- `im_vol_conv` (M52 → M73, `modules/52_carbon/normal_dec17/preloop.gms:20-21`) is absent from §7.1's "Provides" list. Out of scope for a carbon-balance doc; not flagged.

## Method notes

- Every absence claim was cross-checked with a second tool (`rg` and `grep`) plus a positive control in the same directory. B1's negative — that `presolve.gms:65` is the *only* assignment to `p32_carbon_density_ac(...,"plant",...)` — was confirmed this way.
- Both grep forms (`NAME(` and `NAME.`) were run for every interface variable in the doc; that is what surfaced B10 (M59's `.l` postsolve read, invisible to `vm_carbon_stock(`).
- Every grep probe was issued as its own standalone command (no chained `find -exec … +`), per the repo's truncation hazard.
- Phase-ordering for B1 was derived from `core/calculations.gms:13-15` + `modules/include.gms:12-57`, not assumed.
