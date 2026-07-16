# Round 55 depth audit — module_52.md — lens: declare_populate

**Target**: `modules/module_52.md` (realization `normal_dec17`, confirmed default via `config/default.cfg:1574`)
**Ground truth**: `/private/tmp/magpie_develop_ro`
**Role map**: `audit/integrated/depth_rolemap.json`

## Verdict: MOSTLY ACCURATE (1 Critical, 1 Major, 1 Minor)

The doc is unusually accurate: the q52 equation formula, both growth macros (`m_growth_vegc`, `m_growth_litc_soilc`), `m_timestep_length`, every start.gms / preloop.gms populate-and-overwrite citation, all scalar defaults (`s52_growingstock_calib=1`, `s52_k_high_secdf=0.1`, `s52_k_high_plant=0.15`), the `fm_carbon_density` consumer set {14,29,30,31,32,35,56,59}, and the pcm_carbon_stock split-populator claim (M56 ag_pools postsolve:8 / M59 soilc postsolve:13,9) all verify exactly against develop. Realization citations lead with the default in every module. Three defects found.

---

## BUG 1 (Critical) — Module 14 omitted from `pm_carbon_density_secdforest_ac_uncalib` consumer set

- **doc_line**: module_52.md:458 (also 138, 292 — the other two places the uncalib secdforest consumer list appears)
- **Claim**: "Consumers: Module 32 (afforestation "aff" ... and NDC forest "ndc" ...), Module 29 (tree cover on cropland ...). All three use cases represent *new establishment*..." (line 292/138 add Module 35). Module 14 is nowhere in the uncalib-secdforest consumer list.
- **Reality**: Module 14 (default realization `managementcalib_aug19`) READS `pm_carbon_density_secdforest_ac_uncalib` on the RHS of the `im_growing_stock_ysf` (young secondary forest growing stock) assignment.
- **Evidence**: `modules/14_yields/managementcalib_aug19/presolve.gms:66` — `pm_carbon_density_secdforest_ac_uncalib(t,j,ac,"vegc") / sm_carbon_fraction * fm_aboveground_fraction("secdforest") / ...`
- **Role map**: `pm_carbon_density_secdforest_ac_uncalib` read_by = [14,29,32,35,52]. Doc lists 29,32,35 — omits 14.
- **verify_cmd**: `grep -n "pm_carbon_density_secdforest_ac_uncalib" modules/14_yields/managementcalib_aug19/presolve.gms` → `66:     pm_carbon_density_secdforest_ac_uncalib(t,j,ac,"vegc")` (RHS of im_growing_stock_ysf, lines 64-71).
- **Anchor**: R20 immutable Critical anchor — the `pm_carbon_density_*_ac_uncalib` family with an incomplete consumer set; a user refactoring the parameter would silently break Module 14's youngsecdf growing-stock/wood-yield consistency. Per rubric §1.5 mandate, wrong/incomplete consumer sets in this family are Critical by future-reader harm.
- **Note**: Module 14's youngsecdf use is itself a new-establishment (regrowth on other land) context, so it fits the doc's own rationale for why the uncalibrated curve is used — it simply was not enumerated.
- **Fix**: Add Module 14 to the `pm_carbon_density_secdforest_ac_uncalib` consumer list (Section 1b line 458, plus lines 138 and 292): "Module 14 (young secondary forest growing stock `im_growing_stock_ysf`, `modules/14_yields/managementcalib_aug19/presolve.gms:66`)". Confirmed read_by set = {14,29,32,35}.

## BUG 2 (Major) — Wrong crop-pool populator: "Module 30 (Cropland)" listed as direct provider of carbon stocks to M56

- **doc_line**: module_52.md:712
- **Claim**: Under "Land Modules (provide carbon stocks to Module 56)": "Module 30 (Cropland): Cropland carbon stocks".
- **Reality**: (a) Module 30 is `30_croparea`, not "Cropland" (`29_cropland` is Cropland). (b) Module 30 does NOT populate `vm_carbon_stock`; it populates the separate `vm_carbon_stock_croparea`, which Module 29 folds into `vm_carbon_stock` (one hop). The direct crop-pool populator of `vm_carbon_stock` is Module 29. This summary also omits Module 29 and Module 59 entirely.
- **Evidence**: dir names `modules/29_cropland`, `modules/30_croparea`; role map `vm_carbon_stock` populated_by = [29,31,32,34,35,59] (56 is a bounds/pcm-assignment artifact, not a land populator — verified below). The doc's OWN line 424 states this correctly: "Modules 29 (Cropland, crop pool), 31, 32, 34, 35, and 59 (SOM...) populate `vm_carbon_stock`... Module 30 populates the separate `vm_carbon_stock_croparea`, which Module 29 folds in". Line 712 contradicts line 424.
- **verify_cmd**: `ls -d modules/29_* modules/30_*` → `29_cropland`, `30_croparea`; role map read/populate for vm_carbon_stock as above.
- **Class**: MANDATE 17 (transitive-as-direct) + MANDATE 18 (populator attribution). Major (main interface section at 424 is correct; this is a summary list, but names the wrong module for the crop carbon stock).
- **Fix**: Change line 712 to "Module 29 (Cropland): Cropland carbon stocks (crop pool)"; note Module 30 (Croparea) is one hop removed via `vm_carbon_stock_croparea` → M29; add Module 59 (soilc) for completeness, matching line 424.

## BUG 3 (Minor) — "Provides to: Modules 56, 11 (costs), 44 (biodiversity)" — M11 and M44 do not consume any M52 output

- **doc_line**: module_52.md:1201 (Participates In > Dependency Chains, boilerplate centrality metadata)
- **Claim**: "Provides to: Modules 56 (ghg_policy), 11 (costs), 44 (biodiversity)".
- **Reality**: Module 52 provides `vm_emissions_reg`("co2_c") to Module 56 (correct). Neither Module 11 (costs) nor Module 44 (biodiversity) reads any M52-provided variable (`vm_emissions_reg`, `im_vol_conv`, `pm_carbon_density_*`, `fm_carbon_density`, `i52_land_carbon_sink`). M11 gets carbon into the cost objective via M56's `vm_emission_costs` (one hop through M56, not from M52). M44 has no path from M52 carbon outputs at all.
- **Evidence**: `grep -rn "vm_emissions_reg|im_vol_conv|pm_carbon_density|fm_carbon_density|i52_land_carbon_sink" modules/11_costs/*/*.gms` → no matches; same grep on `modules/44_biodiversity/*/*.gms` → no matches.
- **Class**: attribution_read (transitive/false "provides to" in centrality footer). Minor — footer metadata that readers are unlikely to act on directly; the main body interface docs are correct. tier_uncertainty: could be Major under MANDATE 17 if a reader uses it for modification-impact reasoning.
- **Fix**: Change "Provides to: Modules 56, 11, 44" to "Provides to: Module 56 (ghg_policy, via `vm_emissions_reg`); Module 73 (via `im_vol_conv`); Modules 14/29/32/35 (via age-class carbon densities). Carbon enters costs (M11) transitively through M56's `vm_emission_costs`." Drop Module 44.

---

## Verified-correct (high-value checks that passed)

- q52_emis_co2_actual formula: exact match, `equations.gms:16-19`.
- `m_growth_vegc` `core/macros.gms:18`, `m_growth_litc_soilc` `core/macros.gms:20`, `m_timestep_length` `core/macros.gms:51` — all exact.
- start.gms populate lines 17/20/28/31/48/51; uncalib copies 43-44; im_vol_conv fallback 40 — all correct.
- preloop.gms: im_vol_conv 21 (outside if-block), i52_bef_avg 26, m-averages 29-30, secdforest overwrite 71-73, plantation overwrite 114-116, `fm_aboveground_fraction("forestry")` at :96 vs `("secdforest")` at :61 — all correct. 25 iterations (`iter52 = iter1*iter25`, sets.gms:13) correct; interval-width arithmetic (~3e-9) correct.
- Scalar defaults: `s52_growingstock_calib=1` (input.gms:46), `s52_k_high_secdf=0.1` (47), `s52_k_high_plant=0.15` (48). `c52_carbon_scenario=cc`, `c52_land_carbon_sink_rcp=RCPBU`.
- Declarations line numbers 9/10/11/12/13/23/30 — all correct.
- Interface providers: `sm_carbon_fraction` M14 input.gms:22 (/0.5/); `fm_ipcc_bef` M14 input.gms:66; `fm_aboveground_fraction` M14 input.gms:74; `pm_climate_class` M45 (static); `im_forest_ageclass` M28; `pm_land_plantation` M32.
- `fm_carbon_density` consumer citations M14 presolve:35, M30 simple_apr24 eq:51, M31 endo_jun13 eq:24, M56 preloop:10, M59 preloop:12 — all correct; consumer set {14,29,30,31,32,35,56,59} matches role map exactly.
- `pcm_carbon_stock` carry-forward: M56 postsolve:8 (ag_pools), M59 cellpool postsolve:13 + static postsolve:9 (soilc) — all correct (per-slice populator claim right).
- `vm_carbon_stock` declared M56 declarations.gms:34; populator set {29,31,32,34,35,59} at line 424 correct (M56 in role map is a pcm-assignment/scale artifact, not a land populator).
- `vm_emissions_reg` co2_c-slice consumer = M56 only: correct. M57 reads `vm_emissions_reg` only for `pollutants_maccs57` (CH4/N2O) + n2o_n_direct (`modules/57_maccs/on_aug22/equations.gms:38-50`), NOT the co2_c oneoff slice — so the doc's scoped claim is right, no omission.
- Switch/set names not confabulated: `s32_aff_plantation` (M32 input:35, def 0), `s29_treecover_plantation` (M29 input:20, def 0), `type32` (M32 sets:16) all real. M32 aff/ndc/plant carbon-density assignments at presolve:59/61/65/68 match doc.
- Core sets: `emis_oneoff` 314-318, `c_pools` 324-325, `emis_land` 332-335 — members match doc.

## Deferred (not flagged — lower confidence / unverifiable)

- "Depends on: Modules 10 (land), 28 (age class), 35 (natveg)" (line 1202): 28 is a genuine upstream (im_forest_ageclass); 10 and 35 are not direct reads of M52 (M52's real upstreams are 45,56,28,32,14). Likely coarse cycle-graph semantics (the circular-dep line 1206 puts 10 in the M56→32→10→52→56 cycle), so not flagged as a confirmed populate/read bug.
- "Previously both loops used a hardcoded `i52_k_high(i) = 0.3`" (line 229) and PR/commit refs (#869 / 75d7ee167 / c7731e234 / 931db85c4): historical claims not checkable from the current develop worktree.
- "~24 params" (line 28): declarations.gms has 17 parameters + 1 output param; "~" makes it approximate, not flagged.
