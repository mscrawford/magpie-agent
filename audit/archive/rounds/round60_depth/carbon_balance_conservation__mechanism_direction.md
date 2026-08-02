# R60 depth audit — `cross_module/carbon_balance_conservation.md`

**Lens**: `mechanism_direction` (equation bodies, cross-module data-flow direction, mechanistic-vs-parameterized, causal direction, set membership/counts)
**Ground truth**: MAgPIE `develop` read-only worktree @ `2c02843ec` ("Merge pull request #919 from alexkoberle/dyn_reg_tau")
**Date**: 2026-08-02
**Claims verified**: ~118
**Bugs**: 15 (0 Critical · 3 Major · 10 Minor · 2 Informational)

All paths repo-relative. Every claim below was derived from code this session; where a finding coincides with the earlier `04:18` pass over this same file, it was **re-derived independently** (grep + positive control) before being restated — a matching prior verdict is corroboration, not the evidence.

---

## 0. What checked out clean (so the negatives are interpretable)

| Claim | Evidence |
|---|---|
| `c_pools /vegc,litc,soilc/` | `core/sets.gms:324-325` exact |
| `emis_oneoff` 21 members = 7 land × 3 pools | `core/sets.gms:314-318`; `land` set 7 members `core/sets.gms:250-251` |
| `emis_land` mapping | `core/sets.gms:332-354` exact (closing `/` on 354) |
| `peatland ∈ emis_annual` | `core/sets.gms:322` |
| `q52_emis_co2_actual` body, `"actual"` slice | `modules/52_carbon/normal_dec17/equations.gms:16-19`, `:19` — quoted block matches |
| `vm_carbon_stock(j,land,c_pools,stockType)` DECLARED in M56 | `modules/56_ghg_policy/price_aug22/declarations.gms:34` |
| `stockType / actual, actualNoAcEst /` | `modules/56_ghg_policy/price_aug22/sets.gms:212-213` |
| `c56_carbon_stock_pricing` default `actualNoAcEst`; M56 prices that slice | `.../price_aug22/input.gms:90`; `.../equations.gms:19-22` |
| Un-prefixed `default.cfg` line never reaches GAMS (substance) | `scripts/start_functions.R:346` passes only `cfg$gms` to `lucode2::manipulateConfig` — **re-derived**, correct (line number wrong, B9) |
| **M52 ∥ M56 are PARALLEL readers of `vm_carbon_stock`, not a serial chain** | `q56_emis_pricing` is over `emis_annual` only (`.../equations.gms:15-17`); M52 writes only `emis_oneoff`; `emis_oneoff ∩ emis_annual = ∅` (`core/sets.gms:314-322`); `q56_emis_pricing_co2` recomputes from `pcm_carbon_stock − vm_carbon_stock` (`:19-22`). §7.3's anti-serial warning is **correct** |
| §2.3 `actual` vs `actualNoAcEst` mechanism | `m_carbon_stock_ac` sums `ac` for `"actual"` and `ac_sub` for `"actualNoAcEst"` (`core/macros.gms:104-106`); populating equations are indexed over the free set and do fill both |
| Populator set of `vm_carbon_stock` = {29 crop, 31 past, 32 forestry, 34 urban, 35 primf/secdf/other, 59 soilc} | whole-tree `rg -n 'vm_carbon_stock' modules/ core/`; matches `audit/integrated/depth_rolemap.json` `populated_by ['29','31','32','34','35','59']`. §7.5 list is **complete and correct** |
| `s52_growingstock_calib = 1` hard default, absent from `config/default.cfg` | `modules/52_carbon/normal_dec17/input.gms:46`; positive controls `c52_carbon_scenario` (1590), `s52_k_high_*` hit in `default.cfg`, this one does not |
| M52 calibration sites; asymptote unchanged; region-average `m` | `.../preloop.gms:29-30, 71-73, 114-116`; FRA-2025 log at `:106` |
| `pm_carbon_density_*_ac_uncalib` snapshot | `.../start.gms:43-44` |
| **Uncalibrated**-curve reader set (M14 `:66`, M29 `:46,48`, M32 `:59,61,68`, M35 `:242`, `:117`) | whole-tree `rg` — all five citations land exactly |
| `im_growing_stock_ysf` block | `modules/14_yields/managementcalib_aug19/presolve.gms:64-71`; `yields <- managementcalib_aug19` (`config/default.cfg:357`) |
| M35 blend `:248-252`; natural-origin harvest bound `:177-180`; 20 tC/ha maturation `:117`; othernat curve `:240` | exact |
| M59 `q59_som_target_cropland :20-27` (all 4 terms), `q59_som_pool :46-52`, `q59_carbon_soil :61-64` | exact |
| `i59_lossrate(t)=1-0.85**m_yeardiff(t)` and the §5.2 table (56/44, 80/20, 96/4) | `modules/59_som/cellpool_jan23/preloop.gms:45`; re-derived 0.5563 / 0.8031 / 0.9612 ✓ |
| `i59_subsoilc_density = fm_carbon_density(...,"other","soilc") − f59_topsoilc_density` | `.../preloop.gms:12` — the M52→M59 derivation **direction** is right |
| `s59_scm_target = 0` (`default.cfg:1978`), `c59_irrigation_scenario = "on"` (`default.cfg:1956`), off-branch `input.gms:70` | exact |
| FMG/FI factor sets + defaults | `tillage59` `sets.gms:13-14`, `inputs59` `:16-17`; `preloop.gms:52-55` |
| Pasture limitation | `modules/59_som/cellpool_jan23/realization.gms:21-24` |
| §7.4 MACC applicability set, **exhaustively** | `im_maccs_mitigation` consumers = {50, 51, 53} only; M53 `:29,:52,:63`, `q53_emissions_resid_burn :70-72` MACC-free; `maccs_ch4 / rice_ch4, ent_ferm_ch4, awms_ch4 /` `modules/57_maccs/on_aug22/sets.gms:28-29`; M51 `:71` over all `n_pollutants_direct`, comment `:62-64`, `q51_emissions_inorg_fert :30-39` MACC-free, `emis_source_n51 sets.gms:15-16` (no rice), `preloop.gms:8-10`; M50 `macceff_aug22/presolve.gms:56,58,61,63` |
| §10.2 item 7 (peatland) end-to-end | `config/default.cfg:1874`, `:1931`; `modules/58_peatland/v2/equations.gms:91-92`; `realization.gms:8-17`; `core/sets.gms:322`; peat ∉ `c_pools` |
| M34 urban fix statement itself | `modules/34_urban/exo_nov21/presolve.gms:8` (default realization `config/default.cfg:1147`) |
| M29 `q29_carbon` populates crop slice from M30's `vm_carbon_stock_croparea` | `modules/29_cropland/detail_apr24/equations.gms:38-42`; `cropland <- detail_apr24` (`config/default.cfg:814`) |
| Macros | `m_growth_vegc core/macros.gms:18`; `m_growth_litc_soilc :20`; `m_timestep_length :51` |
| Every realization named in the doc is the `config/default.cfg` default | 52 normal_dec17 (1577), 59 cellpool_jan23 (1937), 56 price_aug22, 58 v2 (1874), 34 exo_nov21 (1147), 29 detail_apr24 (814), 35 pot_forest_may24 (1156), 32 dynamic_may24 (995), 53 ipcc2006_aug22 (1604), 57 on_aug22 (1843), 51 rescaled_jan21 (1571), 50 macceff_aug22 (1500), 14 managementcalib_aug19 (357) |
| Units | `vm_carbon_stock` "mio. tC", `vm_emissions_reg` "Tg per yr" (`declarations.gms:34,40`), `vm_nr_som` "Mt N per yr", `vm_cost_scm` "mio. USD17MER per yr" (`modules/59_som/cellpool_jan23/declarations.gms:31,35`); 44/12 = 3.67 |
| §8.1 immediate-emission arithmetic (56,833 Tg CO₂) | re-derived exact |

The citation discipline in this doc is unusually strong — the two ⚠️ growing-stock-calibration blocks alone carry 14 file:line citations and **every one lands on the right line**. The failures cluster in three places: (a) the *calibrated*-side half of that same map; (b) `§10 Limitations` prose asserting process states without checking the switch that governs them; (c) illustrative arithmetic that drifts free of formulas the doc itself sourced from code.

---

## 1. Bugs

### B1 — Major — `set_membership` — the CALIBRATED-curve reader set omits Module 32 (timber plantations) and M14's plantation read

**Doc** `:180` (verbatim duplicate at `:479`):
> "M14 and M35 read the CALIBRATED curve as well - M14 for regular secdforest growing stock (`modules/14_yields/managementcalib_aug19/presolve.gms:44`), M35 for secdforest carbon density, which it BLENDS with the uncalibrated curve by natural-origin area share"

**Reality**: **M32 reads the calibrated plantation curve for existing timber plantations** — `p32_carbon_density_ac(t,j,"plant",ac,ag_pools) = pm_carbon_density_plantation_ac(t,j,ac,ag_pools);` at `modules/32_forestry/dynamic_may24/presolve.gms:65`, unconditional. And **M14 also reads the calibrated plantation curve** at `modules/14_yields/managementcalib_aug19/presolve.gms:26` for `im_growing_stock(t,j,ac,"forestry")`.

This matters more than the omissions look. The paragraph is structured as an exhaustive map — uncalibrated readers enumerated, then "M14 and M35 read the CALIBRATED curve as well" — and M32 appears in it **only** under *uncalibrated* (`aff` at `:59/:61`, `ndc` at `:68`). A maintainer reading this would conclude that changing or disabling `s52_growingstock_calib` leaves M32 untouched. In fact `"plant"` is the dominant forestry carbon pool and is exactly where the FRA-2025 **plantation** calibration (`i52_k_calib_plant`, `modules/52_carbon/normal_dec17/preloop.gms:114-116`) lands. The doc documents the calibration and then omits its principal consumer.

**Evidence**: `modules/32_forestry/dynamic_may24/presolve.gms:65`; `modules/14_yields/managementcalib_aug19/presolve.gms:26`.

**Verify** (standalone):
```
rg -n 'pm_carbon_density_plantation_ac|pm_carbon_density_secdforest_ac|pm_carbon_density_other_ac' \
   modules/ --glob '*.gms' | grep -v uncalib
```
→ writers `52_carbon/normal_dec17/start.gms:17,20,28,31,48,51` + `preloop.gms:71,114`; readers `14_yields/managementcalib_aug19/presolve.gms:26,44,53` (and the `dynRegPastrTau_apr26` twin), `32_forestry/dynamic_may24/preloop.gms:18,56`, **`32_forestry/dynamic_may24/presolve.gms:65`**, `35_natveg/pot_forest_may24/presolve.gms:240,248,250`; plus `declarations.gms:9,11,12`.

**Fix**: replace the sentence (in **both** copies, `:180` and `:479`) with — "M14, M32 and M35 read the CALIBRATED curves as well: M14 for plantation growing stock (`modules/14_yields/managementcalib_aug19/presolve.gms:26`) and secdforest growing stock (`:44`); **M32 for the carbon density of existing timber plantations** (`modules/32_forestry/dynamic_may24/presolve.gms:65`); M35 for secdforest carbon density, which it BLENDS with the uncalibrated curve by natural-origin area share (`modules/35_natveg/pot_forest_may24/presolve.gms:248-252`)."

**Verified side-note, not part of the proposed edit** — M32's *other* two reads (`preloop.gms:18`, `:56`, feeding rotation-length calculation) run in the **preloop** phase. `core/calculations.gms:15` drives that phase via `$batinclude "./modules/include.gms" preloop`, and `modules/include.gms` includes modules in strict numeric order, so **module 32's preloop executes before module 52's preloop** — those two reads capture *uncalibrated* values while `presolve.gms:65` (presolve phase, `core/calculations.gms:54`) captures *calibrated* ones. Whether that split is intended is a separate question; flagged, not asserted as a defect.

---

### B2 — Major — `mechanism` (capability-vs-default) — fire is claimed as an active carbon-loss channel; in a default run it contributes exactly zero, and the whole disturbance channel decays to zero by 2050

**Doc** `:870` (§10.2 item 6): "Fire disturbances (Module 35) cause carbon loss via stock change"; also `:221` "Disturbed areas (fire, shifting agriculture)"; `:626` "Disturbances (fire, shifting agriculture) → reset age classes → carbon loss".

**Reality**: M35 has four mutually exclusive branches keyed on `s35_forest_damage` (`modules/35_natveg/pot_forest_may24/presolve.gms:13-33`). The default is **2** (`.../input.gms:27` `/ 2 /`; `config/default.cfg:1184`), whose branch (`presolve.gms:19-22`) applies **only** `f35_forest_lost_share(i,"shifting_agriculture")`, multiplied by `(1 - p35_damage_fader(t))` — a sigmoid fader reaching 1 at `s35_forest_damage_end = 2050` (`preloop.gms:88`; `config/default.cfg:1186`). So the disturbance loss **decays to zero by 2050** in a default run.

The distinct `wildfire` driver is a member of `combined_loss / shifting_agriculture, wildfire /` (`.../sets.gms:14-15`), and `combined_loss` is read **only** in the `s35_forest_damage = 3` branch (`presolve.gms:24-27`) — not the default, and not even listed in `input.gms:27`'s own option string (which documents 0, 1, 2, 4). So wildfire causes **no** carbon loss at all in a default run, rather than loss that is "lumped" with LUC emissions.

Three-check secondary point: even in branch 3, `f35_forest_lost_share(i,driver_source)` is an exogenous input table ("Share of area damaged by forest fires", `input.gms:32-36`) — **parameterized, not mechanistically modelled**. The mechanism the doc does describe correctly is the area move `ac_sub → ac_est` (`presolve.gms:36-38`), which is what produces the carbon loss.

**Verify**:
```
sed -n '13,33p' modules/35_natveg/pot_forest_may24/presolve.gms
grep -n 's35_forest_damage' config/default.cfg modules/35_natveg/pot_forest_may24/input.gms
grep -n 'p35_damage_fader' modules/35_natveg/pot_forest_may24/preloop.gms
```
→ branch 2 = shifting_agriculture × `(1 - p35_damage_fader)`; `config/default.cfg:1184: <- 2`, `:1186: _end <- 2050`; `preloop.gms:88: m_sigmoid_time_interpol(p35_damage_fader, sm_fix_SSP2, s35_forest_damage_end, 0, 1)`.

**Fix**: `:870` → "Forest disturbance in Module 35 is **exogenous and carries no fire component in a default run**: `s35_forest_damage = 2` (`config/default.cfg:1184`) applies only the `shifting_agriculture` share (`modules/35_natveg/pot_forest_may24/presolve.gms:19-22`), faded to zero by `s35_forest_damage_end = 2050`. The `wildfire` share is summed only under `s35_forest_damage = 3` (`presolve.gms:24-27`). Where active it is an applied historical share (`f35_forest_lost_share`), not a modelled fire process; it moves area `ac_sub → ac_est` (`presolve.gms:36-38`) and the carbon loss is indistinguishable from general LUC emissions." Apply the same qualifier at `:221` and `:626`.

---

### B3 — Major — `mechanism` — "primary forest carbon density does NOT change over time" is false under the default climate scenario, and contradicts §8.3 of this same doc

**Doc** `:841` (§10.1 item 1) "Primary forest carbon density does NOT change over time"; `:201` "Carbon density does NOT change over time (climate change affects future forests, not current primary)"; table `:194-196` marks all three pools "Static".

**Reality**: `fm_carbon_density(t_all,j,land,c_pools)` is time-indexed (`modules/52_carbon/normal_dec17/input.gms:16`) and is collapsed to y1995 **only** under `c52_carbon_scenario == "nocc"` (`:22`); the default is `cc` (`input.gms:8`; `config/default.cfg:1590`). `q35_carbon_primforest` (`modules/35_natveg/pot_forest_may24/equations.gms:42-44`) uses `m_carbon_stock`, which evaluates the density at the **current** timestep: `land(j2,item) * sum(ct, carbon_density(ct,j2,item,ag_pools))` (`core/macros.gms:99-101`). Primforest soilc likewise moves: M59's non-cropland target is `vm_land(j2,noncropland59) * sum(ct, f59_topsoilc_density(ct,j2))` (`modules/59_som/cellpool_jan23/equations.gms:31-34`), frozen only under `c59_som_scenario == "nocc"` — default `cc` (`config/default.cfg:1951`). Nothing in `modules/52_carbon/` special-cases primforest (`rg -n 'primforest' modules/52_carbon/` → two comment lines in `preloop.gms` only).

The doc contradicts **itself** at `:698-700`: "LPJmL simulates vegetation carbon density under future climate → Module 52 updates `fm_carbon_density(t,j,land,c_pools)` over time → Carbon stocks change even without land-use change."

The defensible claim is narrower: primforest has **no age-class / successional dynamics** — always at the LPJmL mature density, unlike secdforest which accumulates along Chapman-Richards.

**Verify**:
```
sed -n '99,101p' core/macros.gms
grep -nE '^cfg.gms.c52_carbon_scenario|^cfg.gms.c59_som_scenario' config/default.cfg
```
→ macro sums over `ct`; `1590: c52_carbon_scenario <- "cc"`, `1951: c59_som_scenario <- "cc"`.

**Fix**: change the `:194-196` "Static" cells to "No age-class dynamics (always at LPJmL mature density)"; replace `:201` with — "Carbon density carries **no age/regrowth dynamics** (primforest is always at the LPJmL mature value). It *does* change over time under the default `c52_carbon_scenario = "cc"` / `c59_som_scenario = "cc"`, because `fm_carbon_density` and `f59_topsoilc_density` are time-varying LPJmL inputs evaluated at the current timestep (`core/macros.gms:99-101`); see §8.3." Amend §10.1 item 1 so the limitation is the missing regrowth/age dynamic, not an absent climate response.

---

### B4 — Minor — `attribution_read` — `vm_maccs_costs` consumer arrow omits Module 36

**Doc** `:593`: "`vm_maccs_costs(i,factors)`: Labor and capital costs of mitigation → to Module 11".

**Reality**: `modules/36_employment/exo_may22/equations.gms:28` reads `vm_maccs_costs(i2,"labor")` and converts it to employment; `exo_may22` is the default (`config/default.cfg:1212`). The other reader is `modules/11_costs/default/equations.gms:28`. Role map `read_by ['11','36','57']`; both-endpoints grep confirms 11 and 36 outside M57.

**Verify**: `rg -n 'vm_maccs_costs' modules/ | grep -v 57_maccs` → exactly those two lines.

**Fix**: "→ **Module 11** (total cost objective, `modules/11_costs/default/equations.gms:28`) **and Module 36** (the `"labor"` factor becomes employment, `modules/36_employment/exo_may22/equations.gms:28`)."

---

### B5 — Minor — `attribution_read` — the CH₄ consumer arrow omits Module 57

**Doc** `:573`: "`vm_emissions_reg(i,emis_source,"ch4")`: Regional CH₄ emissions → to Module 56".

**Reality**: **Module 57 also reads `vm_emissions_reg`** — `modules/57_maccs/on_aug22/equations.gms:38,40,48,50` read `vm_emissions_reg(i2,emis_source,pollutants_maccs57)` and divide by `(1 - im_maccs_mitigation)` to back out unmitigated emissions for MACC costing. `pollutants_maccs57 = / ch4, n2o_n_direct /` (`modules/57_maccs/on_aug22/sets.gms:25-26`), so CH₄ is explicitly in scope. This is a genuine second consumer, not a transitive one.

**Verify**: `rg -n 'vm_emissions_reg' modules/57_maccs/` → four equation-level reads (positive control: the same grep over `modules/56_ghg_policy/` returns `equations.gms:17`).

**Fix**: "→ **Module 56** (pricing, `modules/56_ghg_policy/price_aug22/equations.gms:15-17`) **and Module 57** (MACC cost calculation back-computes unmitigated emissions, `modules/57_maccs/on_aug22/equations.gms:38,48`)."

---

### B6 — Minor — `attribution_populate` — urban vegc/litc zeroing attributed to Module 52; Module 34 does it

**Doc** `:263-264` (§3.7 table): rows `vegc | Fixed to zero | None | **52**` and `litc | Fixed to zero | None | **52**`.

**Reality**: the zeroing is `vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0;` in **Module 34** (`modules/34_urban/exo_nov21/presolve.gms:8`; default realization per `config/default.cfg:1147`). Module 52 touches urban only for **soilc**, setting the *density* to other-land soilc (`modules/52_carbon/normal_dec17/input.gms:35`) — it never zeroes vegc/litc. The doc's own §7.5 (`:622`) attributes the fix correctly to M34, so the table contradicts the body. (The `soilc | 52, 59` row at `:265` is right: M52 sets the density, M59 populates the stock.)

**Verify**: `rg -n 'vm_carbon_stock' modules/ core/ | grep urban` → only `modules/34_urban/exo_nov21/presolve.gms:8` and `modules/34_urban/static/presolve.gms:10`.

**Fix**: change the Module column of the vegc and litc rows from `52` to `34`, and footnote "fixed via `vm_carbon_stock.fx`, `modules/34_urban/exo_nov21/presolve.gms:8`".

---

### B7 — Minor — `mechanism` — litter "decomposition to soil organic matter" is not modelled

**Doc** `:73` (§2.2 Litter, Dynamics): "**Decomposition**: Gradual breakdown to soil organic matter (20-year IPCC timescale)".

**Reality**: there is **no litter → soil carbon flux anywhere in the model**. `m_growth_litc_soilc` (`core/macros.gms:20`) linearly ramps the *litter pool itself* from `pc52_carbon_density_start(...,"litc")` (= pasture litc, `modules/52_carbon/normal_dec17/start.gms:10`) to the forest litc equilibrium over 20 years — a convergence of the litter pool toward its own LPJmL target, not a transfer of carbon into `soilc`. The soil side is entirely independent: `q59_som_target_cropland` (`modules/59_som/cellpool_jan23/equations.gms:20-27`) and `q59_som_target_noncropland` (`:31-34`) are functions of area × `cratio` × `f59_topsoilc_density`, with no litter term. `litc` does not appear anywhere in `modules/59_som/`.

**Verify**:
```
rg -n 'litc' modules/59_som/          # -> no matches
rg -c 'soilc' modules/59_som/cellpool_jan23/equations.gms   # positive control -> 6
```

**Fix**: `:73` → "**Convergence**: the litter pool is linearly interpolated toward its land-type equilibrium over 20 years (IPCC horizon, `core/macros.gms:20`). MAgPIE does **not** model a decomposition flux from `litc` into `soilc` — the two pools converge independently to their own targets, and Module 59's soil equations contain no litter term."

---

### B8 — Minor — `set_membership` — the "FLU: Cropland / Set-aside / Perennial" category set does not exist in Module 59

**Doc** `:428`: "**FLU** (Land Use): Cropland / Set-aside / Perennial (default: annual cropland)"; `:137`: "Land use: Cropland vs set-aside".

**Reality**: `modules/59_som/cellpool_jan23/sets.gms` declares `tillage59 /full_tillage,reduced_tillage,no_tillage/` (`:13-14`) and `inputs59 /low_input,medium_input,high_input_nomanure,high_input_manure/` (`:16-17`) — so the doc's FMG and FI bullets and their stated defaults (`preloop.gms:52-55`) are exactly right. There is **no** land-use-category set. FLU is pre-resolved **per MAgPIE crop type**: `table f59_cratio_landuse(i,climate59_2019,kcr)` (`input.gms:43`), consumed at `preloop.gms:62`. Fallow and tree cover carry their own dedicated ratios (`i59_cratio_fallow`, `preloop.gms:73-75`; `i59_cratio_treecover = 1`, `:82`), not a "set-aside" FLU member.

**Verify**:
```
rg -in 'setaside|set-aside|set_aside|perennial' modules/59_som/
```
→ only two unrelated prose comments (`static_jan19/realization.gms:16`, `cellpool_jan23/input.gms:24`). Positive control: `rg -c 'cratio' modules/59_som/cellpool_jan23/preloop.gms` → 13.

**Fix**: `:428` → "**FLU** (Land Use): not a category switch in MAgPIE — the IPCC land-use factor is pre-resolved **per crop type** in `f59_cratio_landuse(i,climate59_2019,kcr)` (`modules/59_som/cellpool_jan23/input.gms:43`); fallow and tree cover carry separate ratios." Same at `:137`.

---

### B9 — Minor — `citation` — `config/default.cfg:1835` points at a comment line; the assignment is at `:1838`

**Doc** `:101`: "⚠️ Do **not** cite `config/default.cfg:1835` for this default: that line omits the `cfg$gms$` prefix its siblings carry".

**Reality**: `grep -n 'c56_carbon_stock_pricing' config/default.cfg` → `1838:c56_carbon_stock_pricing <- "actualNoAcEst"   # def = actualNoAcEst`. Line 1835 is `# *   actual: CO2 emissions for pricing are based on ...` — inside the option comment block, carrying no assignment, so "omits the prefix" does not describe it. The **substance is correct and was re-derived**: `scripts/start_functions.R:346` calls `lucode2::manipulateConfig(file.path(ll,"input.gms"), cfg$gms)`, so only `cfg$gms$*` entries ever reach a module `input.gms`; the bare assignment is inert.

**Fix**: `1835` → `1838`.

---

### B10 — Minor — `formula` — the §6.3 growth table does not satisfy the Chapman-Richards formula with the A/k/m it states

**Doc** `:486-500`: "A = 100 tC/ha, k = 0.06, m = 2.0", then tabulates 14 / 26 / 44 / 58 / 75 / 88 / 93 tC/ha at 5 / 10 / 20 / 30 / 50 / 80 / 100 yr.

**Reality**: `m_growth_vegc` (`core/macros.gms:18`) is `S + (A-S)*(1-exp(-k*(ac*5)))**m`. With S=0, A=100, k=0.06, m=2.0 the curve is **6.72 / 20.36 / 48.83 / 69.67 / 90.29 / 98.36 / 99.50** — off by 2.1× at 5 yr and ~1.2× through 30-80 yr; the doc's curve saturates far more slowly than its own parameters imply. (The age-class ↔ year mapping `ac1`=5 yr … `ac20`=100 yr is correct against `(ord(ac)-1)*5`.)

**Verify**:
```
python3 -c "import math; A,k,m=100,0.06,2.0; print([round(A*(1-math.exp(-k*t))**m,2) for t in (5,10,20,30,50,80,100)])"
```
→ `[6.72, 20.36, 48.83, 69.67, 90.29, 98.36, 99.5]`

**Fix**: regenerate the column from the stated parameters (values above), or state the (k, m) that actually produce the tabulated curve. Keep the "illustrative" note either way.

---

### B11 — Minor — `formula` — §8.4 (and §8.2) convergence percentages contradict §5.2 and `preloop.gms:45`

**Doc** `:734`: "Year 5: 44% toward new equilibrium = +4 tC/ha"; `:678`: "soilc: 70 tC/ha (80% toward natural…)" at **Year 20**; `:684`: "soilc: 78 tC/ha (96% toward natural)" at **Year 50**.

**Reality**: `i59_lossrate(t) = 1 - 0.85**m_yeardiff(t)` (`modules/59_som/cellpool_jan23/preloop.gms:45`) gives **55.6%** at 5 yr, **96.1%** at 20 yr, **99.97%** at 50 yr. 44% is the *legacy* share at 5 yr, and the doc's own §5.2 table (`:401-404`) already states 56/44 correctly — so `:734` contradicts `:402`, and `:678`/`:684` are each shifted one row up that same table. Independently, on the scenario's own numbers (50 → 80 tC/ha target) 96.1% convergence gives **78.8** tC/ha at year 20, not 70. (Root of the confusion: the code comment at `preloop.gms:42` itself mislabels "44% in 5 years" as a loss while quoting the 10- and 20-year figures as losses.)

**Verify**:
```
python3 -c "print([round(100*(1-0.85**y),2) for y in (1,5,10,20,50)])"
```
→ `[15.0, 55.63, 80.31, 96.12, 99.97]`

**Fix**: `:734` → "Year 5: 56% toward new equilibrium = +5 tC/ha". `:678` → "soilc: 79 tC/ha (96% toward natural)"; `:684` → "soilc: 80 tC/ha (>99% toward natural)". Re-derive the sequestration totals at `:688-689` from the corrected column. Optionally footnote that `preloop.gms:42`'s "44% in 5 years" is the remaining legacy.

---

### B12 — Minor — `formula` — §8.1 gradual soil-carbon emission is 550 Tg CO₂/yr, not 458

**Doc** `:656`: "Gradual (soilc over 20 years): 30 tC/ha × 100 Mha × (44/12) / 20 years = **458 Tg CO₂/year**".

**Reality**: `30 × 100 × 44/12 / 20 = 550.0`. (458 corresponds to a 25 tC/ha loss; the table at `:649` says 30.) The immediate-emission line at `:655` re-derives exactly, so this is an isolated slip, not a unit problem.

**Verify**: `python3 -c "print(30*100*44/12/20)"` → `550.0`

**Fix**: `458` → `550`.

---

### B13 — Minor — `data_flow_direction` — the §9.1 stock-change consistency recipe cannot pass as written

**Doc** `:756-779`.

**Reality**: three defects, all checkable against declarations.
1. `vm_emissions_reg(i,emis_source,pollutants)` is **regional** and indexed by `emis_source` (`modules/56_ghg_policy/price_aug22/declarations.gms:40`), and `q52_emis_co2_actual(i2,emis_oneoff)` already performs `sum(cell(i2,j2),…)` (`modules/52_carbon/normal_dec17/equations.gms:17-19`). The recipe's `dimSums(stock_change, dim=c("cell","land","c_pools"))` (`:775`) collapses to a **global scalar** and destroys the `emis_land` mapping, so `all.equal(emissions_co2, emissions_calculated)` compares incompatible objects.
2. `ov_carbon_stock` / `pcm_carbon_stock` both carry `stockType` (`declarations.gms:19,49`); the recipe never selects `"actual"`, so it silently mixes both slices — the exact distinction §2.3 is built on.
3. `pcm_carbon_stock` is a GAMS **parameter** (`declarations.gms:8,19`), so `field="l"` at `:760` is inapplicable.

**Fix**: select `stockType = "actual"` on both stock reads; drop `field="l"` on the parameter; map cells → regions and aggregate `land × c_pools` **through `emis_land`** into `emis_oneoff` before comparing — or compare a single global total on both sides and say so explicitly.

---

### B14 — Informational — `citation` — interface-parameter domains written as `t` where the declaration is `t_all`

**Doc** `:513` `fm_carbon_density(t,j,land,c_pools)`; `:514-516` `pm_carbon_density_{plantation,secdforest,other}_ac(t,j,ac,ag_pools)`; same at `:101`, `:107`, `:180`, `:479`, `:699`.
**Reality**: `modules/52_carbon/normal_dec17/input.gms:16` and `declarations.gms:9-13` declare over `t_all`. `t` and `t_all` are distinct sets in MAgPIE (optimized vs. all time steps); inside equations these are read as `sum(ct, …)`.
**Fix**: use `t_all` in the "Provides" list, or the equation-side `(ct,…)` form — consistently.

---

### B15 — Informational — `set_membership` — §1's "Mathematical Concept" quantifies over cells; the identity is realized per region

**Doc** `:21-23`: "∀ j ∈ Cells, ∀ t ∈ Time: CO₂ Emissions(t) = [Carbon Stock(t-1) − Carbon Stock(t)] / Timestep Length".
**Reality**: `q52_emis_co2_actual(i2,emis_oneoff)` writes `vm_emissions_reg(i2,…)` — indexed by **region `i`** and by `emis_oneoff`, cells summed inside (`modules/52_carbon/normal_dec17/equations.gms:16-19`). There is no cell-level CO₂ emission variable in Module 52. The doc's own §4.1 renders it correctly two sections later.
**Fix**: "∀ i ∈ Regions, ∀ s ∈ emis_oneoff, ∀ t ∈ Time: CO₂ Emissions(i,s,t) = Σ_{j∈i} [Stock(t−1) − Stock(t)] / Timestep Length".

---

## 2. Deferred (no bug asserted, no edit proposed)

1. `:875` "Module 59 models **mineral** soil carbon only" — structurally plausible (IPCC ch.5 mineral stock-change tables, LPJmL topsoil reference, peat absent from `c_pools`), but the `f59_ch5_*` input files are gitignored, so "mineral-only" is not confirmable from the GAMS tree.
2. `:95-96` / `:851` Subsoil "Static (fixed from LPJmL via M52)" — `i59_subsoilc_density(t_all,j)` (`preloop.gms:12`) *is* time-varying under the default `cc`; the adjacent bullet ("Not affected by land use") supplies the intended meaning, so not filed. Worth tightening if a fix pass touches §2.3.
3. `:436-438` IPCC stock-change factor values (0.69, 1.17) — labeled "typical values from IPCC"; the `f59_ch5_F_*` tables are gitignored and not checkable here.
4. `:255` caveat 2 (the `secdforest` yield-vs-carbon blend gap) is correctly self-labeled "unverified lead". The algebra re-checks out (`q35_prod_secdforest` reads the purely calibrated `im_growing_stock` at `modules/35_natveg/pot_forest_may24/equations.gms:147`; `q35_carbon_secdforest` reads the blend from `presolve.gms:248-252`), but confirming or refuting it needs a run.
5. `:595` "verified against code - the mitigation factor `(1 - im_maccs_mitigation)` appears in exactly these equations" — the *set* of modules is right (50, 51, 53), but the M50 site is a division-form NUE uplift (`macceff_aug22/presolve.gms:56-63`), not a literal `(1 - …)` factor. The doc's own bullet 3 explains this correctly, so the sentence is loose rather than wrong. Not filed.
6. `:180` / `:479` cite `14_yields/…`, `29_cropland/…`, `32_forestry/…`, `35_natveg/…` without the leading `modules/` their siblings in the same sentence carry (MANDATE 16 form). Cosmetic.
7. `:1002` footer freshness against `project/sync_log.json` — out of lens, not checked.

---

## 3. Pattern note for the flywheel

The two most consequential findings (B1, B3) and the second Major (B2) share one shape: **the doc is rigorous where it quotes code and loose where it summarises state.** B1 is a *half*-verified map — the uncalibrated column was enumerated by grep (all five citations exact), the calibrated column was written from memory and lost its largest consumer. B2 and B3 are `§10 Limitations` prose asserting that a process is on (fire) or off (primforest climate response) without opening the switch that governs it.

Two cheap mechanical guards would have caught all three:
- **Enumerate both sides of a producer/consumer split with the same grep.** A one-sided `rg` that skips `| grep -v uncalib`'s complement is how B1 happened.
- **Any doc line asserting a process state — "does NOT", "cannot", "causes", "is fixed" — must carry a switch citation with its default value.** B2 and B3 both fail this and both contradict other passages in the same file (§8.3 for B3; §7.5's own correct M34 attribution for B6).
