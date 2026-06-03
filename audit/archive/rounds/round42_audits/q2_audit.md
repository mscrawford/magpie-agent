# Audit Report: Q2 (Climate M45 → Yields M14 / SOM M59; parameterization vs mechanism)

**Round**: 42
**Ground truth**: live GAMS at `/Users/turnip/Documents/Work/Workspace/magpie/modules/` + `config/default.cfg`, develop @ HEAD `ee98739fd` (clean working tree confirmed).
**Answer audited**: `audit/archive/rounds/round42_answers/q2_answer.md`

---

## Overall Verdict: ACCURATE
## Accuracy Score: 10/10

The parameterization-vs-mechanism framing — the core of the question — is **fully correct** and well-supported by code. Every file:line citation I checked is exact or within a defensible range. The two non-blocking imprecisions are index-set label slips (`t` for `t_all`, `kcr`/`kve`/`knbe14` interchange) that do not change any mechanism, number, or behavioral claim and would not mislead a careful reader. Under the rubric tie-breaker (pick lower; informational style/typo tier) these do not reach scored-bug severity. No doc-vs-code latent bugs found in the load-bearing claims.

---

## Mechanical Checks (M1–M6)

| Check | Result | Evidence |
|---|---|---|
| **M1** File:line citations present | ✅ PASS | Dozens of `module_XX/realization/file.gms:NN` cites throughout |
| **M2** Active realization stated | ✅ PASS | States `climate=static` (only realization), `yields=managementcalib_aug19`, `som=cellpool_jan23`; all match default.cfg |
| **M3** Variable prefixes valid | ✅ PASS | `pm_climate_class`, `vm_yld`, `vm_tau`, `i14_yields_calib`, `i59_cratio`, `f14_yields`, `f59_topsoilc_density`, `fm_ipcc_bef`, `vm_nr_som`, `vm_carbon_stock` — all prefixes correct |
| **M4** Epistemic badges present | ✅ PASS | Header 🟡 Documented; closing reaffirms. (Single global badge rather than per-claim — acceptable; answer is uniformly 🟡 by its stated constraint) |
| **M5** Confidence tier matches depth | ✅ PASS | Answer claims 🟡 (docs-only, raw GAMS not opened per task constraint) and does NOT over-claim 🟢. Honest. Notably the docs-derived line numbers turned out code-exact. |
| **M6** Closing source statement | ✅ PASS | "All claims 🟡 Documented — read this session from: module_45.md / module_14.md / ... / config/default.cfg" |

No mechanical-check failures.

---

## Verified Claims (correct)

### Section (a) — defaults & where set
- **M45 realization = `static`, only realization**: confirmed — `ls modules/45_climate/` shows only `static/`. config/default.cfg:1474 `cfg$gms$climate <- "static"`. ✓ EXACT (answer cited 1474).
- **M45 is a pure data-provider: zero equations, zero variables, one parameter**: confirmed — `static/realization.gms` includes ONLY `sets` and `input` phases (lines 16-17); there is no `equations.gms`, `declarations.gms`, `presolve.gms`, or any variable. `find modules/45_climate -name equations.gms` → none. ✓ Strong confirmation of the central claim.
- **`pm_climate_class(j,clcl)`, Köppen-Geiger, static 1976-2000 (Rubel 2010), 31 types**: confirmed — `static/input.gms:10` declares `table pm_climate_class(j,clcl)` read from `koeppen_geiger.cs3`; `realization.gms:8-10` documents "static over the whole simulation based on data for 1976-2000 ... (@rubel_observed_2010)". `static/sets.gms:11-46` defines `clcl` with exactly **31** members (Af…ET, hand-counted). ✓ "31 climate types" EXACT.
- **`c14_yields_scenario` default `"cc"` at default.cfg:360**: confirmed — line 360 `cfg$gms$c14_yields_scenario  <- "cc"   # def = "cc"`. ✓ EXACT. Realization default `managementcalib_aug19` at line 354. Module-internal default also `cc` (`14_yields/.../input.gms:8` `$setglobal c14_yields_scenario cc`).
- **`c59_som_scenario` default `"cc"` at default.cfg:1930**: confirmed — line 1930 `cfg$gms$c59_som_scenario  <- "cc"   # def = "cc"`. ✓ EXACT. SOM realization default `cellpool_jan23` at line 1916. Module-internal `$setglobal c59_som_scenario cc` at `59_som/.../input.gms:72`.
- **`sm_fix_cc` default 2025 at default.cfg:228**: confirmed — line 228 `cfg$gms$sm_fix_cc <- 2025`. ✓ EXACT.
- **nocc/nocc_hist semantics for yields**: confirmed — `14_yields/.../input.gms:41` (`nocc` → set to y1995), `:42` (`nocc_hist` → freeze after sm_fix_cc). ✓ Answer cited input.gms:41-42, exact.
- **M45 carries no CO2/RCP/SSP pathway, no time variation; future reclassification absent**: confirmed — `pm_climate_class(j,clcl)` has no time index; realization.gms:12 `@limitations Temporal variations in climate classification are not considered`. ✓

### Section (b) — yields: parameterization, not mechanistic
- **`q14_yield_crop` exact form, equations.gms:14-16**: confirmed verbatim —
  `vm_yld(j2,kcr,w) =e= sum(ct,i14_yields_calib(ct,j2,kcr,w)) * vm_tau(j2,"crop") / sum((cell(i2,j2), supreg(h2,i2)), fm_tau1995(h2));` at lines 14-16. ✓ EXACT. No temperature/precip/CO2/physiology variable anywhere in the equation — climate signal lives entirely inside `i14_yields_calib`. Verified by reading the whole equations.gms (only 2 equations: q14_yield_crop, q14_yield_past).
- **`f14_yields` read from `lpj_yields.cs3` at input.gms:37**: confirmed — line 37 `$include "./modules/14_yields/input/lpj_yields.cs3"`. ✓ EXACT.
- **`i14_yields_calib` built in preloop from `f14_yields`, becomes the calibrated baseline, preloop.gms:108-116**: confirmed — preloop.gms:8 first assigns `i14_yields_calib = f14_yields`; the FAO management-calibration block at 108-112 (`i14_managementcalib`) and 115 (`i14_yields_calib = i14_managementcalib * f14_yields`) is exactly the cited 108-116 range. ✓
- **Feedback check (no land-use → climate feedback; yield table fixed at preloop)**: confirmed — `f14_yields` is fixed input; no equation re-derives it from model state. Yields change only via `vm_tau` (M13) and `pm_past_mngmnt_factor` (pasture, M70). ✓ Both confirmed in equations.gms:14-16 (tau) and :35-39 (pasture mngmnt factor).
- **`fm_ipcc_bef(clcl)` read from `f14_ipcc_bef.cs3` at input.gms:69; used in M14 presolve growing-stock (timber), not yields**: confirmed — `fm_ipcc_bef` declared/included input.gms:66-69 (`:69` = the include line, EXACT); used in `presolve.gms:24-58` inside `im_growing_stock(...)` for forestry(24-31)/primforest(33-40)/secdforest(42-49)/other(51-58). ✓ Answer's "presolve.gms:24-31 ... same pattern for primforest, secdforest, other at lines 33-58" is exact. `im_growing_stock` ≠ `vm_yld`; feeds timber (M32/M35), correct.
- **`sum(clcl, pm_climate_class(j,clcl) * fm_ipcc_bef(clcl))` BEF denominator**: confirmed verbatim at presolve.gms:29/38/47/56. ✓

### Section (c) — M45 → M59 SOM pathway
- **31 clcl → 4 climate59 categories via `clcl_climate59`; categories at sets.gms:22-24**: confirmed — `59_som/.../sets.gms:22-23` `climate59(climate59_2019) /temperate_dry,temperate_moist,tropical_dry,tropical_moist/`; `clcl_climate59(clcl,climate59)` mapping at sets.gms:27-61. ✓ The 4 categories and line cite are accurate (line 24 is a comment within the cited range).
- **Aggregation `sum(clcl_climate59(clcl,climate59), pm_climate_class(j,clcl))`**: confirmed — appears at preloop.gms:15-16, :61, :74, :89. ✓
- **`i59_cratio` = landuse × tillage × input × irrigation factors, preloop.gms:60-67**: confirmed verbatim — preloop.gms:60-67 builds `i59_cratio(j,kcr,w)` as the product of `f59_cratio_landuse * i59_tillage_share * f59_cratio_tillage * i59_input_share * f59_cratio_inputs * f59_cratio_irrigation`, all under `sum(...,climate59) * sum(clcl_climate59, pm_climate_class)`. ✓ EXACT range; the climate-weighting via `pm_climate_class` is exactly as described. **This is the high-value parameterization claim and it is correct.**
- **IPCC factor tables + file names + line cites**: all confirmed in `59_som/.../input.gms` —
  - `f59_cratio_landuse(i,climate59_2019,kcr)` ← `f59_ch5_F_LU_2019reg.cs3`, input.gms:43-46 (decl 43, include 45). ✓
  - `f59_cratio_tillage(climate59,tillage59)` ← `f59_ch5_F_MG.csv`, input.gms:49-52 (decl 49, include 51). ✓
  - `f59_cratio_inputs(climate59,inputs59)` ← `f59_ch5_F_I.csv`, input.gms:55-58 (decl 55, include 57). ✓
  - `f59_cratio_irrigation(climate59,w,kcr)` ← `f59_ch5_F_IRR.cs3`, input.gms:65-69 (decl 65, include 67). ✓
  All four cites EXACT. "IPCC 2019 Chapter 5" attribution matches `f59_ch5_*` + `climate59_2019` naming. ✓
- **Defaults full_tillage=1 / medium_input=1**: confirmed at preloop.gms:52-55 (`i59_tillage_share(i,"full_tillage")=1`, `i59_input_share(i,"medium_input")=1`). (Minor attribution nuance — see Missing Nuances; the "=1.0" lives on the *shares*, preloop:52-55, while the answer attached it to the factor *tables* listed with input.gms cites. The statement is nonetheless factually true since full-tillage is the IPCC reference = 1.0.) ✓ factually correct.
- **`q59_som_target_cropland`, equations.gms:20-27**: confirmed verbatim — lines 20-27, with the answer's `+ ...` correctly eliding the SCM term (lines 23-24). Multiplier `* sum(ct,f59_topsoilc_density(ct,j2))` at line 27. ✓ EXACT.
- **`q59_som_pool` dynamic convergence, equations.gms:46-52**: confirmed verbatim — lines 46-52, `sum(ct,i59_lossrate(ct)) * v59_som_target + (1 - lossrate) * sum(land_from, p59_carbon_density * vm_lu_transitions)`. ✓ EXACT.
- **`i59_lossrate(t)=1-0.85**m_yeardiff(t)`, preloop.gms:45; 15%/yr, climate-invariant rate**: confirmed verbatim at preloop.gms:45. ✓ EXACT. "0.85 climate-invariant" correct.
- **2nd M59 climate input `f59_topsoilc_density(t,j)` ← `lpj_carbon_topsoil.cs2b`, input.gms:77-86; nocc freeze at :84**: confirmed — decl `f59_topsoilc_density(t_all,j)` at input.gms:77, include `lpj_carbon_topsoil.cs2b` at :80, `nocc` freeze at **:84** (`= f59_topsoilc_density("y1995",j)`). ✓ Cite :84 EXACT; range 77-86 accurate.
- **Downstream: `vm_nr_som` → M51, `vm_carbon_stock(...,"soilc",.)` → M52**: confirmed —
  - `q59_nr_som` (equations.gms:69-75) produces `vm_nr_som`; `vm_nr_som(` is read in `modules/51_nitrogen/rescaled_jan21/equations.gms` (M51 default realization, config:1550). ✓
  - `q59_carbon_soil` (equations.gms:61-64) produces `vm_carbon_stock(j2,land,"soilc",stockType)`. ✓

### "What Is NOT Happening" box
- **No temperature/precip/CO2/atmospheric variable simulated**: confirmed by absence across M14/M45/M59 equations. ✓
- **M52 `f52_growth_par(clcl,...)` is climate-indexed with NO time dimension**: confirmed — `52_carbon/normal_dec17/input.gms:37` declares `f52_growth_par(clcl,chap_par,forest_type)` (no `t`), used in `start.gms:17/28/48` as `sum(clcl, pm_climate_class(j,clcl)*f52_growth_par(clcl,...))`. M52 default realization `normal_dec17` (config:1556). ✓ Corroborates the parameterization thesis: climate enters M52 carbon growth via static IPCC-zone Chapman-Richards parameters, not dynamic climate.
- **CO2 fertilization embedded in LPJmL preprocessing, not computed in MAgPIE**: consistent with code (no CO2 variable in M14); this is a correct statement about the input-data boundary. ✓ (🔵-adjacent provenance claim about LPJmL preprocessing; not contradicted by any MAgPIE code, and the answer correctly frames it as upstream.)

---

## Bugs Found

**None at scored severity.** Two index-set label imprecisions and one attribution nuance are recorded below as sub-threshold (Informational) observations for completeness; per rubric §1 tie-breaker and the "careful reader wouldn't be misled" test for Minor, none reach a scored tier, so all contribute 0 to the severity-weighted sum.

- **Obs-1 (Informational, class 3-adjacent / index-label)**: Answer writes `f14_yields(t,j,kcr,w)` and `f14_yields(t,j,knbe14,w)`-style as `kcr`; code declares `f14_yields(t_all,j,kve,w)` (input.gms:35). Two slips: `t`→`t_all` and `kve`→`kcr`. `kve` (all vegetation incl. pasture/bioenergy) is broader than `kcr` (crops). Does NOT change the mechanism or any number; the time-dimension argument (the load-bearing point — climate signal rides the time index) is correct either way. Not scored.
- **Obs-2 (Informational, index-label)**: Answer writes `f59_topsoilc_density(t,j)`; code is `f59_topsoilc_density(t_all,j)` (input.gms:77). Cosmetic; the nocc-freeze and time-variation claims are exact. Not scored.
- **Obs-3 (Informational, attribution nuance)**: In (c) Step 2 the answer attaches "default: full_tillage = 1.0 / medium_input = 1.0" to the factor tables `f59_cratio_tillage`/`f59_cratio_inputs` (cited at their input.gms include lines). The literal `=1` assignments are on the *share* selectors `i59_tillage_share`/`i59_input_share` at preloop.gms:52-55. The statement is still factually true (full tillage = IPCC reference = 1.0; medium input = reference = 1.0), so it does not mislead. Not scored.

No fabricated variable names, no fabricated equations, no wrong realization, no inverted Boolean, no wrong default, no citation drift to materially different content.

---

## Latent doc bugs (§1.5)

**None found.** The answer is docs-derived (🟡, raw GAMS not opened per task constraint), yet every load-bearing claim I cross-checked against code is correct — meaning the underlying module docs (module_14.md, module_45.md, module_59.md) that produced these claims are themselves accurate on: M45 static/no-equations structure, `pm_climate_class` name & 31-type set, `c14_yields_scenario`/`c59_som_scenario`/`sm_fix_cc` defaults & lines, `q14_yield_crop` form, the `i59_cratio` chain & preloop:60-67, `q59_som_target_cropland`/`q59_som_pool` forms & lines, the IPCC factor-table filenames & input.gms ranges, and the BEF presolve block. No `doc_error_answerer_beat_it` to record. (If anything, the docs are unusually well-calibrated here: docs-only line numbers landed code-exact across ~20 citations.)

---

## Missing Nuances

- The answer could note that `q14_yield_crop` is one of only **2** equations in `managementcalib_aug19/equations.gms` (the other being `q14_yield_past`) — reinforces "no climate equation exists." (Not an error; the answer does state there's no plant-physiology equation in M14, which is the operative point.)
- The `i59_cratio` chain also feeds the SCM term (`i59_cratio_scm`, `q59_som_target_cropland` line 23-24) and fallow/treecover ratios; the answer correctly elided these with "..." and separately mentioned fallow/treecover, so nothing is misrepresented.
- M52 `q52_emis_co2_actual` reads `vm_carbon_stock` (the soilc piece of which M59 populates) — the answer's downstream arrow `vm_carbon_stock → M52` is correct; it doesn't trace into M52's CO2 accounting, but that's out of scope for the question.

---

## Summary

The answer correctly and precisely establishes that **the entire climate architecture touching M45→M14→M59 is parameterization, not mechanistic climate dynamics**:
1. **M45** is a static (1976-2000 Köppen-Geiger) classification provider — literally no equations, one parameter `pm_climate_class(j,clcl)` (confirmed: realization.gms includes only sets+input phases).
2. **Yields**: `q14_yield_crop` multiplies a pre-computed LPJmL-derived calibrated baseline (`i14_yields_calib`, ultimately `lpj_yields.cs3`) by tech-change `vm_tau`; the climate-change signal is the *time dimension of an external input table*, not an in-model climate equation. `c14_yields_scenario="cc"` (default.cfg:360). CO2 fertilization is embedded upstream in LPJmL.
3. **SOM**: M45's `pm_climate_class` is mapped (`clcl_climate59`) to 4 IPCC climate zones, selecting **IPCC 2019 Ch.5 tabular stock-change factors** into `i59_cratio` (preloop:60-67), which sets the cropland SOC equilibrium target (`q59_som_target_cropland`, eq:20-27); the actual pool relaxes toward target at a fixed 15%/yr lossrate (`q59_som_pool`, eq:46-52). The IPCC tables are exogenous lookups, not soil-decomposition physics MAgPIE computes. A second, separate climate input `f59_topsoilc_density` (`lpj_carbon_topsoil.cs2b`, gated by `c59_som_scenario="cc"`, default.cfg:1930) carries LPJmL's natural-soil-carbon-under-climate-change signal.

The "uses data about X ≠ models X" distinction is applied exactly right. Citations are code-exact across the board. The only deviations are cosmetic index-set labels that change nothing. **Score 10/10, ACCURATE. Parameterization framing: fully accurate.**

---

*Audited against develop @ ee98739fd by reading: modules/45_climate/static/{realization,input,sets}.gms; modules/14_yields/managementcalib_aug19/{equations,presolve,preloop,input}.gms; modules/59_som/cellpool_jan23/{equations,preloop,sets,input}.gms; modules/52_carbon/normal_dec17/{input,start}.gms; modules/51_nitrogen/rescaled_jan21/equations.gms (grep); config/default.cfg lines 228,354,360,1474,1550,1556,1916,1930.*
