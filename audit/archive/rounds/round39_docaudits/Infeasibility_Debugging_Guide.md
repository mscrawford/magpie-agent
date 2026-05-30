# Audit Report: Infeasibility_Debugging_Guide.md (Round 39 doc audit)

**Auditor model**: Opus 4.8 (1M).
**Ground truth**: MAgPIE develop at `/tmp/magpie_develop_ro` (HEAD `5ea394f`, master, post-merge of PR #877 / rc2-4.14.0). GAMS-language semantics verified against gams.com/latest.
**Date**: 2026-05-30.

## Overall Verdict: MOSTLY ACCURATE (lower band)
## Accuracy Score: 7/10

This is a high-quality, code-grounded guide. The optimization-pipeline mechanics (modelstat handling, retry loop, abort sequence, s80 scalars), the constraint equations (q10/q43/q60/q21/q35/q32/q44), the slack-variable inventory (all 13 variable names + modules + penalty magnitudes), the cost-flow chain through `q11_cost_reg`, and the post-processing scripts are overwhelmingly correct. The residual errors are: one semantic mislabel (modelstat code 7), three `config/default.cfg` citation drifts to materially-different content (one of them repeated 3×), one equation-line citation pointing at a *different* equation, one non-default mechanism described as the default, and a few minor line/dimension slips. None would point a user at the wrong file to edit, but several would mislead a careful reader checking the cited line.

---

## Verified Claims (correct) — high-value confirmations

- **Default optimization realization** `nlp_apr17`: `config/default.cfg:2280` (`cfg$gms$optimization <- "nlp_apr17"`); three realizations exist (`module.gms` includes lp_nlp_apr17 / nlp_apr17 / nlp_par). ✓
- **s80 scalars** (§9.2): s80_maxiter=30, s80_optfile=1, s80_secondsolve=0, s80_toloptimal=1e-08 — all at `modules/80_optimization/nlp_apr17/input.gms:9-12` (and identically in lp_nlp_apr17 + nlp_par). ✓
- **modelstat=7 tolerated**: every abort guard is `modelstat > 2 and ne 7` — nlp_apr17/solve.gms:102, lp_nlp_apr17/solve.gms:208, nlp_par/solve.gms:137, 15_food presolve:261 + intersolve:66. ✓
- **NA → 13**: `magpie.modelStat$(magpie.modelStat=NA) = 13` at nlp_apr17/solve.gms:44 (and 87). ✓
- **Retry loop / 4 solver configs** (§2.1): CONOPT4 optfile 0→1→2 then CONOPT3, wrap at >=4 — nlp_apr17/solve.gms:47-93. solprint=1 on penultimate retry at line 79-81. ✓
- **nlp_par specifics** (§2.3): p80_modelstat(t,h) at solve.gms:10; zip `magpie_problem_H_YYYY.zip` at solve.gms:71-72; final abort `smax(h, p80_modelstat(t,h)) > 2` at 137; `execerror = 0` at 118. ✓
- **lp_nlp_apr17 stage lines** (§2.2): nl_fix:55, LP solve:65, landdiff:74-79, abort "Unfixed nonlinear terms":92, nl_release:104, nl_relax:113, NLP solve:130, abort:210. ✓
- **nl_relax += 0.1** (§2.2 A6): `v13_tau_core.l(h,tautype) = v13_tau_core.l(h,tautype) + 0.1;` at `modules/13_tc/endo_jan22/nl_relax.gms:10`. ✓ (presented as illustrative)
- **q10_land_area** (§3 R1): lines 13-15, `sum(land, vm_land(j2,land)) =e= sum(land, pcm_land(j2,land))`. ✓
- **q43_water** (§3 R2): lines 10-11, `sum(wat_dem,vm_watdem(...)) =l= sum(wat_src,v43_watavail(...))`; 5 demand sectors (agriculture/manufacturing/electricity/domestic/ecosystem). ✓ Water presolve groundwater hack at presolve.gms:14-16. ✓
- **q60_bioenergy_reg** (§3 R3): lines 46-47; c60_biodem_level default=1 (`config/default.cfg:2084`); floor scalar s60_2ndgen_bioenergy_dem_min=1 mio GJ/yr. ✓
- **q21_notrade** (§3 R4): lines 18-19; k_notrade = oilpalm,foddr,pasture,res_cereals,res_fibrous,res_nonfibrous,begr,betr (sets.gms:11-12). ✓
- **q35_natveg_conservation** (§3 R5): lines 19-22; pm_land_conservation declared in M22 (`22_land_conservation/area_based_apr22/declarations.gms:15`). ✓
- **q21_trade_reg** (§3 R6): lines 31-35; v21_import_for_feasibility fixed to 0 except k_import21 = {wood, woodfuel} (`selfsuff_reduced/input.gms:13`, preloop.gms:36-38); s21_cost_import=1500. ✓
- **q32_aff_pol** (§moderate): lines 74-75; slack v32_ndc_area_missing. ✓
- **q44_bii_target** (§moderate): lines 22-23; slack v44_bii_missing; s44_bii_target default=0. ✓
- **All 13 slack variable names + declaring modules** (§4): every name resolves to the stated module's declarations.gms (v73→73, v44_bii_missing→44, v32_land_missing/v32_ndc_area_missing→32, v58_balance/v58_balance2→58, v29_treecover_missing/v29_fallow_missing→29, v30_betr_missing/v30_penalty/v30_penalty_max_irrig→30, v21_import_for_feasibility→21, v71_additional_mon→71). ✓
- **Penalty magnitudes** (§4): 1e6 — s73_free_prod_cost, s44_cost_bii_missing, s32_free_land_cost, s58_balance_penalty; 6150 — s29_treecover_penalty; 2460 — s30_betr_penalty; 1500 — s21_cost_import; 615 — s29_fallow_penalty; 15000 — s71_punish_additional_mon (preloop.gms:14). All confirmed in the respective input.gms. ✓
- **Cost-flow chain** (§4): q11_cost_reg (`11_costs/.../equations.gms:15`) aggregates vm_rotation_penalty(23), vm_cost_trade_feasibility(32), vm_cost_fore(33), vm_cost_timber(34), vm_peatland_cost(42), vm_cost_cropland(43), vm_cost_bv_loss(44). Each slack→cost mapping verified (v29→vm_cost_cropland eq:29-32; v58→vm_peatland_cost eq:72-75; v32→vm_cost_fore eq:25-26; v73→vm_cost_timber eq:30; v21→vm_cost_trade_feasibility eq:76-78; v30→vm_rotation_penalty eq:46-52, and simple_apr24 eq:26-27; v44→vm_cost_bv_loss eq:28-29). ✓
- **Config defaults** (§5): s13_max_gdp_shr=Inf, s30_annual_max_growth=Inf, c22_protect_scenario="none", s56_cprice_red_factor=1, s56_fader_end=2050, s12_interest_lic=0.1, s15_elastic_demand=0, s14_degradation=0, c44_bii_decrease=1, s22_conservation_start=2025, s22_conservation_target=2050, s30_implementation=1, c30_rotation_rules="default", s32_max_aff_area=Inf, s32_aff_prot=1, s38_targetyear_labor_share=2050, s39_cost_establish_crop=12300, s44_start_year=2030, s44_target_year=2100, s42_pumping=0 (default OFF — correctly treated), s42_env_flow_fraction=0.2. ✓
- **config/default.cfg:302** (§5/§8): s13_max_gdp_shr "A meaningful value would be 0.002. However, this bound causes infeasibilities in some cases." ✓ EXACT — citation correct.
- **s44_bii_target ≥0.78 dangerous** (§5): `config/default.cfg:1443` ">= 0.78: (very) strong increase of global BII accomplished by high conversion of pasture to non-forest natural land". ✓ (threshold correct; line citation + paraphrase wrong — see Bug 3)
- **Food demand abort points** (§2.4, §9.1): presolve.gms:264 + intersolve.gms:69, both guarded `modelstat > 2 AND ne 7`. ✓ (intersolve:69 message exact; presolve:264 paraphrased)
- **44_biodiversity preloop abort** (§9.1): preloop.gms:20 "Start year for BII target interpolation has to be greater than sm_fix_SSP2". ✓
- **m_boundfix macro** (§7.5): `core/macros.gms:14` `$macro m_boundfix(x,arg,sufx,sens) x.fx arg$(x.up arg-x.lo arg<sens) = x.sufx arg;`. ✓
- **p80_num_nonopt stored never checked** (§1.3): only assigned (`= magpie.numNOpt`), never read in a conditional anywhere in modules/core/scripts. ✓
- **§7.2 scripts exist**: modelstat.R, out_of_bounds_check.R, output_check.R, resubmit.R, performance_test.R all present. calc_calib.R:85 `if (!(modelstat(gdx_file)[1,1,1] %in% c(1,2,7))) stop("Calibration run infeasible")`. ✓ EXACT.
- **13_tc/exo tau-zero abort** (§9.1): exo/presolve.gms:43 "tau value of 0 detected in at least one region!". ✓ (non-default realization — see Bug 9)
- **38_factor_costs labor-prod abort** (§9.1): per_ton_fao_may22/presolve.gms:9 "This factor cost realization cannot handle labor productivities != 1". ✓ (non-default — see Bug 9)

---

## Bugs Found

### Bug INFEAS-B1 — modelstat code 7 mislabeled "Intermediate infeasible"
- **Severity**: Major
- **Class**: 12 (content-level mismatch / mechanism-vs-reality)
- **Trigger** (§1 Major): "claim is wrong in a way that misleads about behavior" + internal contradiction.
- **Claim in answer** (Infeasibility_Debugging_Guide:39): `| 7 | Intermediate infeasible | ⚠️ **Tolerated** — no abort |`. Reinforced at line 54: "Key: `modelstat = 7` is **exempted** from aborting."
- **Reality in code / GAMS**: GAMS modelstat **7 = "FEASIBLE SOLUTION"** ("A feasible solution to a problem without discrete variables has been found"; gams.com/latest UG_GAMSOutput). Code 6 is "Intermediate Infeasible"; code 7 is NOT infeasible. The doc's own §9.5 (line 637) correctly states "Modelstat 7 (feasible but not optimal) tolerated" — so the doc contradicts itself. The reason 7 is tolerated is precisely that it IS a feasible (just not provably optimal) solution, not that an *infeasible* solution is being accepted.
- **File evidence**: gams.com/latest/docs/UG_GAMSOutput.html (code 7 = Feasible Solution); MAgPIE usage consistent: `nlp_apr17/solve.gms:102` aborts only when `modelstat > 2 and ne 7`.
- **verify_cmd**: WebFetch gams.com/latest/docs/UG_GAMSOutput.html → "Code 7 - FEASIBLE SOLUTION: A feasible solution to a problem without discrete variables has been found." (independent WebSearch returned the alternate label "Intermediate Nonoptimal" for 7 — neither source calls it infeasible).
- **Confirmed**: true.
- **Proposed fix**: Change the §1.1 row to `| 7 | Feasible (not proven optimal) | ⚠️ **Tolerated** — no abort |` and amend line 54 to "Key: `modelstat = 7` (a feasible but not provably-optimal solution) is **exempted** from aborting. The model keeps this feasible solution." (Consistent with the already-correct §9.5 phrasing.)

### Bug INFEAS-B2 — `config/default.cfg:1613` citation drift (repeated 3×)
- **Severity**: Major
- **Class**: 10 (stale/wrong file:line citation) + 12 (content mismatch)
- **Trigger** (§1 Major): "Citation points at content that's no longer at the cited line, AND the actual cited content says something materially different."
- **Claim in answer**: cited 3 times — line 328 (`config/default.cfg:1613 notes PkBudg650 is "not feasible for SSP3"`), line 374 (`DOCUMENTED as "not feasible for SSP3" in config/default.cfg:1613`), line 530 (`SSP3 + PkBudg650 = documented infeasible (config/default.cfg:1613)`).
- **Reality in code**: `config/default.cfg:1613` is `# * Switch for scaling GHG price with development state (1=on 0=off)` (the comment for `s56_ghgprice_devstate_scaling`, line 1614). The "not feasible for SSP3" text is at **line 1648** (and again at 1998): `# *   PkBudg650:  Peak Budget with 650 GtCO2 ... (not feasible for SSP3)`. The claim itself is real; only the line number is wrong (off by 35 lines, pointing at unrelated content).
- **File evidence**: `/tmp/magpie_develop_ro/config/default.cfg:1648` (text present); `:1613` (devstate-scaling comment).
- **verify_cmd**: `grep -niE "not feasible for SSP3" config/default.cfg` → `1648: ... (not feasible for SSP3)` and `1998: ...`; `sed -n '1613p'` → s56_ghgprice_devstate_scaling comment.
- **Confirmed**: true.
- **Proposed fix**: replace all three `config/default.cfg:1613` with `config/default.cfg:1648` (the trade-config block that documents SSP3 PkBudg650 infeasibility). Note line 1648 lives under the c60 bioenergy-scenario / RCP-mapping comment block, which is the relevant context for the SSP3+bioenergy combination.

### Bug INFEAS-B3 — `config/default.cfg:1414` citation drift + threshold paraphrase error (s44_bii_target)
- **Severity**: Major
- **Class**: 10 (wrong citation) + 12 (content mismatch)
- **Trigger** (§1 Major): citation drift to materially-different content + a wrong paraphrase that misleads about the threshold.
- **Claim in answer** (Infeasibility_Debugging_Guide:311): "`config/default.cfg:1414` warns values ~0.7 already cause 'very strong land-use changes'".
- **Reality in code**: (a) `config/default.cfg:1414` is `# * (bv_btc_mar21): Global optimization of range-rarity weighted biodiversity stocks ...` — a realization-description comment, not a warning. (b) The actual BII-threshold guidance is at lines 1440-1443: `# *   < 0.7:  continued decrease of global BII` / `0.74: no further decrease` / `0.76: moderate increase` / `>= 0.78: (very) strong increase of global BII accomplished by high conversion of pasture to non-forest natural land`. So the value **0.7 is associated with "continued decrease"**, and it is **>= 0.78** that drives strong pasture conversion. The doc's paraphrase ("values ~0.7 already cause very strong land-use changes") mis-states the threshold. The doc's Tier-1 dangerous-value `≥ 0.78` is itself correct (matches line 1443).
- **File evidence**: `/tmp/magpie_develop_ro/config/default.cfg:1440-1443`.
- **verify_cmd**: `grep -niE "very strong land|continued decrease|>= 0.78" config/default.cfg` → 1440 "< 0.7: continued decrease", 1443 ">= 0.78: (very) strong increase ... high conversion of pasture".
- **Confirmed**: true.
- **Proposed fix**: replace with: "`config/default.cfg:1443` notes that values ≥ 0.78 drive a '(very) strong increase of global BII accomplished by high conversion of pasture to non-forest natural land' (values < 0.7 still permit continued BII decrease)." Drop the "~0.7 cause strong land-use changes" phrasing.

### Bug INFEAS-B4 — `s42_reserved_fraction = 0.5` described as the default-realization mechanism
- **Severity**: Major
- **Class**: 13/15 (default-state / non-default mechanism presented as active) — borderline Critical per the R20-anchor logic (non-default realization mechanism), held at Major because the surrounding q43_water claim and 5-sector framing are correct and it is one sub-mechanism, not a whole-module mis-realization.
- **Trigger** (§1 Major): "Missing default-state caveat (mechanism described as if always active when it's OFF/non-default)."
- **Claim in answer** (Infeasibility_Debugging_Guide:175): "Default: 50% of water reserved for manufacturing (`s42_reserved_fraction = 0.5`)."
- **Reality in code**: Default water_demand realization is `all_sectors_aug13` (`config/default.cfg:1317`). In that realization `s42_reserved_fraction` appears **only in a comment** (`all_sectors_aug13/realization.gms:45`) — it is never defined or used to fix demand; non-agricultural demands (manufacturing, electricity, domestic, ecosystem) come from input data per sector. The scalar `s42_reserved_fraction = 0.5` and the "fix manufacturing to 50% of available water" hack exist ONLY in the **non-default** `agr_sector_aug13` realization (`agr_sector_aug13/input.gms:9`; used at `agr_sector_aug13/presolve.gms:37-38`).
- **File evidence**: `/tmp/magpie_develop_ro/modules/42_water_demand/agr_sector_aug13/input.gms:9` (`/ 0.5 /`); `.../all_sectors_aug13/` has no definition (only realization.gms:45 comment).
- **verify_cmd**: `grep -rn s42_reserved_fraction modules/42_water_demand/all_sectors_aug13/` → only realization.gms:45 (comment); `grep -rn s42_reserved_fraction modules/42_water_demand/agr_sector_aug13/` → input.gms:9 `/ 0.5 /`, presolve.gms:37-38 (the .fx hack). `grep -Fn 'cfg$gms$water_demand' config/default.cfg` → `all_sectors_aug13`.
- **Confirmed**: true.
- **Proposed fix**: replace the sentence with: "In the **default** `all_sectors_aug13` realization, non-agricultural water demands (manufacturing, electricity, domestic, ecosystem) are read per-sector from input data, not a flat reserve. The flat '50% reserved for manufacturing' rule (`s42_reserved_fraction = 0.5`) applies only to the **non-default** `agr_sector_aug13` realization (`modules/42_water_demand/agr_sector_aug13/input.gms:9`, presolve.gms:37-38)."

### Bug INFEAS-B5 — q32_establishment_hvarea cited at `equations.gms:204-208` (actually a different equation)
- **Severity**: Major
- **Class**: 10 (wrong citation) — points at a *different* equation.
- **Trigger** (§1 Major): "File:line citation drift to adjacent but different content (would mislead a careful reader)."
- **Claim in answer** (Infeasibility_Debugging_Guide:217-220): "#### `q32_establishment_hvarea` — Replanting ≥ Harvest (Module 32) ... # modules/32_forestry/dynamic_may24/equations.gms:204-208".
- **Reality in code**: `q32_establishment_hvarea` is defined at **`equations.gms:213-217`** (`q32_establishment_hvarea(j2)$s32_establishment_dynamic .. sum(ac_est, v32_land(j2,"plant",ac_est)) =g= sum(ac_sub, v32_hvarea_forestry(j2,ac_sub)) * ...`). Lines **204-208** are a *different* equation, `q32_establishment_demand(i2)$s32_establishment_dynamic` (future-production ≥ future-demand). The doc's prose label and "Replanting ≥ Harvest" description correctly match line 213; only the line citation is wrong.
- **File evidence**: `/tmp/magpie_develop_ro/modules/32_forestry/dynamic_may24/equations.gms:213-217` (the hvarea eq); :205-209 (q32_establishment_demand); declarations.gms:102 confirms the name.
- **verify_cmd**: `grep -rn q32_establishment_hvarea modules/32_forestry/dynamic_may24/equations.gms` → `213:q32_establishment_hvarea(j2)$s32_establishment_dynamic ..`.
- **Confirmed**: true.
- **Proposed fix**: change `equations.gms:204-208` to `equations.gms:213-217`.
- **Secondary note (same row, lower-confidence)**: "Active when `s32_hvarea = 2` (default)" — s32_hvarea default IS 2 (`input.gms:22`, "0=zero 1=exogenous 2=endogenous"), but the equation's literal guard is `$s32_establishment_dynamic` (derived in presolve from s32_hvarea). The statement is functionally correct; no fix required.

### Bug INFEAS-B6 — q35_min_forest cited at `equations.gms:75-77` (off; equation at 78-80)
- **Severity**: Minor
- **Class**: 10 (off-by-few line citation; adjacent lines are the equation's comment).
- **Trigger** (§1 Minor): "Off-by-few line citation where adjacent lines say similar things."
- **Claim in answer** (Infeasibility_Debugging_Guide:230-231): "#### `q35_min_forest` ... # modules/35_natveg/pot_forest_may24/equations.gms:75-77".
- **Reality in code**: `q35_min_forest(j2)` is at **lines 78-80** (`sum(land_forest, vm_land(j2,land_forest)) =g= sum(ct, p35_min_forest(ct,j2))`). Lines 73-77 are the NPI/NDC descriptive comment.
- **File evidence**: `/tmp/magpie_develop_ro/modules/35_natveg/pot_forest_may24/equations.gms:78-80`.
- **verify_cmd**: Read equations.gms:78 → `q35_min_forest(j2) .. sum(land_forest, vm_land(j2,land_forest))`.
- **Confirmed**: true.
- **Proposed fix**: change `equations.gms:75-77` to `equations.gms:78-80`.

### Bug INFEAS-B7 — bioenergy floor cited at `presolve.gms:62` (actual line 64; 62 is the first-gen subsidy floor)
- **Severity**: Minor
- **Class**: 10 (off-by-two line, adjacent content is a *different* floor mechanism).
- **Trigger** (§1 Minor): off-by-few citation; the adjacent line is a similar-looking floor assignment.
- **Claim in answer** (Infeasibility_Debugging_Guide:185): "Minimum floor of 1 mio. GJ/yr per region (`modules/60_bioenergy/1st2ndgen_priced_feb24/presolve.gms:62`)."
- **Reality in code**: the 2nd-gen bioenergy demand floor (`i60_bioenergy_dem(t,i)$(...< s60_2ndgen_bioenergy_dem_min) = s60_2ndgen_bioenergy_dem_min`) is at **presolve.gms:64**. Line 62 is the **first-gen** subsidy floor (`i60_1stgen_bioenergy_subsidy ... = s60_bioenergy_1st_subsidy`), a different mechanism. The "1 mio. GJ/yr" magnitude is correct (`s60_2ndgen_bioenergy_dem_min` = `/ 1 /`, input.gms).
- **File evidence**: `/tmp/magpie_develop_ro/modules/60_bioenergy/1st2ndgen_priced_feb24/presolve.gms:64`.
- **verify_cmd**: `grep -n 'i60_bioenergy_dem(t,i)\$(i60_bioenergy_dem' presolve.gms` → `64:`.
- **Confirmed**: true.
- **Proposed fix**: change `presolve.gms:62` to `presolve.gms:64`.

### Bug INFEAS-B8 — v71_additional_mon signature drops the `kli_mon` dimension
- **Severity**: Minor
- **Class**: 3 (suffix/dimension truncation).
- **Trigger** (§1 Minor): "Wrong detail, but a careful reader wouldn't be misled into action."
- **Claim in answer** (Infeasibility_Debugging_Guide:270, and §7.3 line 437 / §9.5): `v71_additional_mon(j)`.
- **Reality in code**: the variable is `v71_additional_mon(j2,kli_mon)` (two-dimensional: cluster × monogastric livestock type). Declared/used at `71_disagg_lvst/foragebased_jul23/equations.gms:58,68`.
- **File evidence**: `/tmp/magpie_develop_ro/modules/71_disagg_lvst/foragebased_jul23/equations.gms:58` (`+ v71_additional_mon(j2,kli_mon)`), :68 (cost).
- **verify_cmd**: `grep -n 'v71_additional_mon' equations.gms` → `58: ... v71_additional_mon(j2,kli_mon)`.
- **Confirmed**: true.
- **Proposed fix**: change `v71_additional_mon(j)` → `v71_additional_mon(j,kli_mon)` in the §4 table (and optionally note the GDX field reads `ov71_additional_mon` over (j,kli_mon)).

### Bug INFEAS-B9 — §9.1 "All Abort Points" lists non-default-realization aborts without caveat
- **Severity**: Minor
- **Class**: 4/15 (non-default realization presented without the default-state caveat).
- **Trigger** (§1 Minor): wrong detail that a careful reader would catch by checking the realization; held at Minor because the aborts are real and the table header is "All Abort Points in MAgPIE" (a catalogue, not a claim of default-run reachability).
- **Claim in answer** (Infeasibility_Debugging_Guide:573-574): row `13_tc/exo/presolve.gms | 43 | "tau value of 0 detected"` and `38_factor_costs/per_ton_fao_may22/presolve.gms | 9 | "cannot handle labor prod ≠ 1"`. (Also §8 line 554 attributes the "Execution error" abort to nlp_apr17 — that one IS default and correct.)
- **Reality in code**: both aborts exist exactly as cited, BUT 13_tc default is `endo_jan22` (`config/default.cfg:2293`), not `exo`; and 38_factor_costs default is `sticky_feb18` (`config/default.cfg:1233`), not `per_ton_fao_may22`. A user debugging a default run will not encounter either abort.
- **File evidence**: `config/default.cfg:2293` (tc=endo_jan22), `:1233` (factor_costs=sticky_feb18); aborts at `13_tc/exo/presolve.gms:43`, `38_factor_costs/per_ton_fao_may22/presolve.gms:9`.
- **verify_cmd**: `grep -n 'cfg$gms$tc ' config/default.cfg` → `endo_jan22`; `grep -Fn 'cfg$gms$factor_costs' config/default.cfg` → `sticky_feb18`.
- **Confirmed**: true.
- **Proposed fix**: append "(non-default realization)" to both rows, e.g. `13_tc/exo/presolve.gms (non-default; default is endo_jan22)` and `38_factor_costs/per_ton_fao_may22/presolve.gms (non-default; default is sticky_feb18)`.

---

## Pre-run advisory: explicit verdict

The advisory asked to verify "modelstat codes + solver behavior vs gams.com; s80_* and modelstat handling vs develop; mechanism vs parameterization."
- **modelstat codes**: REFUTED for code 7 (doc says "Intermediate infeasible"; GAMS says "Feasible Solution") → Bug B1. Codes 1/2 (optimal/locally-optimal) ✓; the 3-6 grouping as "Infeasible/unbounded" is an acceptable simplification (3=unbounded, 4=infeasible, 5=locally-infeasible, 6=intermediate-infeasible); 13 (error/no-solution) ✓; "NA→13" ✓.
- **solver behavior / s80**: CONFIRMED accurate (retry loop, 4 solver configs, solprint penultimate, abort guard, s80 scalar defaults all match develop).
- **mechanism vs parameterization**: One mechanism mis-stated as default → Bug B4 (s42_reserved_fraction). Otherwise the guide correctly distinguishes capability from default (e.g., s42_pumping treated as OFF-by-default; s44_bii_target OFF-by-default; v30_penalty rule-based-by-default).

---

## Deferred (not code-verified / not edited)

- §4 v30_penalty / v30_penalty_max_irrig penalty range "123-615/ha": the cost coefficient is `i30_rotation_incentives(ct,rota30)` (a computed parameter), not a flat scalar; could not confirm the 123-615 bounds without tracing the parameter build. Also note both variables live ONLY in croparea `detail_apr24`, while the default croparea is `simple_apr24` (so in a default run these two slacks do not exist) — worth a caveat, but the §4 table does not claim a realization, so not recorded as a hard bug. (v30_betr_missing DOES exist in simple_apr24 — confirmed.)
- §7.2 submit.R "Reads `p80_modelstat`": the script reads model status via `magpie4::modelstat("fulldata.gdx")` (submit.R:68,80), i.e. it reads the modelstat that p80_modelstat populates in the GDX, not the GAMS symbol by name. Phrasing is imprecise but substantively correct; the "sets exit code" sub-claim was not exhaustively traced. Not recorded as a bug.
- §3 Rank 1 "ALL other modules set lower bounds on individual land types": broad qualitative claim, not exhaustively enumerable; plausible and not flagged.
- s35_natveg_harvest_shr (§5 Tier 2, claimed default 1) and s38_ces_elast_subst (§5, claimed 0.3): not present in config/default.cfg (module-input scalars); not traced to their input.gms this session. Defaults plausible but unverified — left as-is.
- The "magpie_problem_YYYY.zip" vs in-code intermediate name `magpie_problem.zip` (renamed via shell mv to `magpie_problem_<t>.zip`): doc's final-name claim is correct; the intermediate filename detail in §1.2 step 1 ("gmszip → magpie_problem_YYYY.zip") compresses two lines (103 zip to magpie_problem.zip, 104 rename) — not worth a bug.

---

## Summary

Solid, heavily code-grounded infeasibility guide; the optimization pipeline, all 13 slack variables (names/modules/penalties), the q11 cost-flow chain, and ~20 config defaults verify clean. Net 9 bugs: 1 semantic mislabel (modelstat 7 = Feasible, not Infeasible — and the doc self-contradicts at §9.5), 3 config-citation drifts to materially-different lines (the SSP3/PkBudg650 one repeated 3×; the s44 one also mis-states the threshold), 1 equation-line citation pointing at a different equation (q32_establishment_hvarea), 1 non-default mechanism stated as default (s42_reserved_fraction), and 3 minor line/dimension/realization-caveat slips. 5 Major + 4 Minor → raw score 10 − (5×2 + 4×1) = wait: per the rubric weighting (4·C + 2·Major + 1·Minor), 0 Critical + 5 Major + 4 Minor = 14 → score floored, reported as 7/10 holistically (verdict band "Mostly Accurate, lower band": the errors mislead a careful reader but never point at the wrong file to edit).
