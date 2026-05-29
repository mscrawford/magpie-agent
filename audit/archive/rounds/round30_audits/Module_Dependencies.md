# Audit Report: Module 10 Dependency Structure (inputs / vm_land consumers / vm_carbon_stock consumers)

**Anchored on**: `core_docs/Module_Dependencies.md` §2.1/§3.1/§4.1; `cross_module/modification_safety_guide.md` §1.2; `modules/module_10.md` §5
**Ground truth**: develop worktree `/tmp/magpie_develop_ro` (read-only)
**Date**: 2026-05-29 (Round 30)

## Overall Verdict: MOSTLY ACCURATE (lower band)
## Accuracy Score: 5/10

score = max(0, 10 − 4·crit − 2·major − 1·minor) = 10 − 2·2 − 1·1 = **5**
(0 Critical, 2 Major, 1 Minor, 0 Informational)

---

## Mechanical checks (all pass)
- **M1** file:line citations present — yes (`equations.gms:50-54`, `declarations.gms:34`).
- **M2** active realization stated — yes (landmatrix_dec18, normal_dec17, price_aug22, endo_jun13, exo_nov21 etc.); all match `config/default.cfg`.
- **M3** variable prefixes valid — yes.
- **M4** epistemic badge present — yes (🟡 Documented).
- **M6** closing source statement — yes.

Default realizations verified in `config/default.cfg`: land=`landmatrix_dec18` (l.232), carbon=`normal_dec17` (l.1556), ghg_policy=`price_aug22` (l.1613), natveg=`pot_forest_may24` (l.1135), forestry=`dynamic_may24` (l.976), cropland=`detail_apr24` (l.795), tc=`endo_jan22` (l.293), disagg_lvst=`foragebased_jul23` (l.2200), peatland=`v2` (l.1853). All consistent with the answer.

---

## Verified Claims (correct)

**Inputs into Module 10 — §1 (fully correct):**
- Exactly 2 external interface inputs: `vm_landdiff_forestry` (from 32_forestry) and `vm_landdiff_natveg` (from 35_natveg). Confirmed: the only `vm_*` referenced in `modules/10_land/landmatrix_dec18/*.gms` that are NOT declared in M10 are these two (`vm_landdiff_natveg` declared `modules/35_natveg/pot_forest_may24/declarations.gms:79`; `vm_landdiff_forestry` declared `modules/32_forestry/dynamic_may24/declarations.gms:67`). `fm_*` are input-data tables, not module interfaces.
- Both enter `q10_landdiff` at `modules/10_land/landmatrix_dec18/equations.gms:50-54` (q10_landdiff at :50, vm_landdiff_natveg at :53, vm_landdiff_forestry at :54). **Line numbers exact.**
- Both are scalar (no indices) — "global scalar sums, not per-cell": confirmed (declarations show no domain). q10_landdiff is a single global equation; the claim that these cannot affect the per-cell balance `q10_land_area` is sound.
- Circular dependencies 10↔35 and 10↔32: sound (M10 provides vm_land/vm_landexpansion to 35/32; they feed vm_landdiff_natveg/forestry back).

**vm_land direct consumers — §2.1 (correct):**
- The 10-module DIRECT list (22, 29, 30, 31, 32, 34, 35, 50, 58, 59) is COMPLETE and CORRECT. Whole-tree `rg 'vm_land'` (excluding 10_land) returns exactly these 10 modules referencing vm_land in `.gms` files. Cross-checks: 29 (`q29_cropland` eq:11–12, reads :50,68), 30 (`detail_apr24/equations.gms:23`), 31 (`q31_prod` :17, presolve `.lo` :9), 32 (presolve `.l/.lo(j,"past")` :19, sets `.l(j,"forestry")` :100), 34 (`q34_urban_land` :30–31, also :18,21,35), 35 (eq populates+reads), 50 (eq:79,90), 58 v2 (macro `m58_LandMerge(vm_land,…)` `equations.gms:23`), 59 (eq:33,63 + vm_lu_transitions), 22 (reads `vm_land.lo(j,"crop")` `area_based_apr22/presolve_ini.gms:86,97,108`). Matches `modification_safety_guide.md:54-55`.
- Equation names `q29_cropland`, `q31_prod`, `q34_urban_land` all verified.
- §2.2 framing of 11_costs (reads `vm_cost_land_transition`, `11_costs/default/equations.gms:41`), 39 (reads `vm_landexpansion`/`vm_landreduction`, `39_landconversion/calib/equations.gms:13-14`), 56 (touches `pcm_land` not vm_land, `56_ghg_policy/price_aug22/preloop.gms:10`) — all correctly placed as NOT direct vm_land consumers.

**vm_carbon_stock — §3 (G2 anchor, correct):**
- Declared ONLY at `modules/56_ghg_policy/price_aug22/declarations.gms:34` — exact. (G2 anchor satisfied.)
- Direct consumers = 52 + 56. Confirmed: 52 reads it in `q52_emis_co2_actual` (`normal_dec17/equations.gms:16-19`), formula `(pcm_carbon_stock − vm_carbon_stock)/m_timestep_length` at "actual" stockType — exact. 56 reads it in `q56_emis_pricing_co2` (`price_aug22/equations.gms:19-22`).
- CO2-vs-(CH4/N2O) pricing asymmetry: CORRECT. `q56_emis_pricing` (annual pollutants, :15-17) sets `v56_emis_pricing = vm_emissions_reg`; `q56_emis_pricing_co2` (one-off CO2, :19-22) computes from carbon stocks directly (`pcm_carbon_stock − vm_carbon_stock(...,"%c56_carbon_stock_pricing%")`), bypassing vm_emissions_reg.
- M56 stores `pcm_carbon_stock = vm_carbon_stock.l` for next timestep: confirmed `price_aug22/postsolve.gms:8`.
- Populators 29 (`equations.gms:39`, folds in `vm_carbon_stock_croparea` from M30 at :40), 31 (:23), 32 (`q32_carbon` :108), 34 (`presolve.gms:8` `vm_carbon_stock.fx(...,"urban")=0`), 35 (:43,50,54), 59 (soilc pool) — all confirmed. 58 does NOT reference vm_carbon_stock — confirmed (answer correct).
- §3.3: 11_costs transitive via `vm_reward_cdr_aff` — confirmed (declared `price_aug22/declarations.gms:43`, defined `equations.gms:68`, consumed `11_costs/default/equations.gms:27`).

---

## Bugs Found

### Bug Module_Dependencies-B1 — 13_tc attributed to wrong Module-10 variable
- **Severity**: Major
- **Class**: 2/13 (variable-name confabulation / interface-consumer attribution)
- **Trigger** (§1 Major): "Wrong variable … semantic scope wrong" / consumer-attribution error in a load-bearing table.
- **Claim in answer** (§2.2 + §4 table): "13_tc | `pm_land_start(j,land)` | TC calibration uses initial land distribution".
- **Reality in code**: 13_tc (default `endo_jan22`) does NOT reference `pm_land_start` anywhere. It reads **`pcm_land`** at `modules/13_tc/endo_jan22/presolve.gms:9,10,40` (builds `pc13_land` for the per-timestep crop/pasture TC calibration). Positive control: `pcm_land` and `pm_land_conservation` are present in the same file, so the search works. `pm_land_start` is read by 14/32/59/71, not 13.
- **Why it matters**: a reader tracing `pm_land_start` consumers, or editing 13_tc, gets the wrong interface variable. Right module, right concept, **wrong variable name** (look-alike within M10's own parameter set: pm_land_start vs pcm_land).
- **Root cause**: `answerer_confabulation` (the cited docs do NOT make this specific claim — `module_10.md:318` correctly leaves 13's variable unspecified).

### Bug Module_Dependencies-B2 — 14_yields omitted from the Module-10 transitive consumer set
- **Severity**: Major
- **Class**: 13 (interface-parameter consumer omission)
- **Trigger** (§1 Major): "Fabricated/incomplete count for a … list" — the answer's transitive set is incomplete vs the documented 18-module union.
- **Claim in answer** (§2.2 + §4): transitive vm_land consumers = {11, 13, 39, 44, 56, 71, 80}. 14_yields is absent from §2.2, §3, and the §4 summary.
- **Reality in code**: 14_yields consumes the Module-10 parameter `pm_land_start` at `modules/14_yields/managementcalib_aug19/preloop.gms:15-16` (pasture-yield regional calibration weighting). The doc's own 18-module union (`modification_safety_guide.md:58`) includes 14_yields. 18-union minus the 10 direct = {11,13,14,39,44,56,71,80} (8 modules); the answer listed 7, dropping 14.
- **Why it matters**: a user assessing "what is affected by Module-10 land parameters" misses the yield-calibration dependence — the MANDATE-13 / R20-anchor omission class.
- **Root cause**: `answerer_confabulation` (answerer reproduced 7 of 8 union members from the doc but dropped 14).
- **Note**: B1 and B2 share one root cause — the answer mishandled the `pm_land_start` consumer set (wrongly attached it to 13, dropped the real consumer 14). Recorded as two bugs because the reader harms differ (false positive vs missing entry).

### Bug Module_Dependencies-B3 — 44_biodiversity transitive path mischaracterized
- **Severity**: Minor
- **Class**: 2 (causal-mechanism precision) / 17 (transitive-path labeling)
- **Trigger** (§1 Minor): "Wrong detail, but a careful reader wouldn't be misled into action."
- **Claim in answer** (§2.2): "44_biodiversity | Transitive via `vm_lu_transitions` and Module 35".
- **Reality in code**: 44_biodiversity does NOT reference `vm_lu_transitions` (whole-tree consumers of vm_lu_transitions = 29, 35, 59 only). 44 is correctly NOT a direct vm_land consumer, but the named transitive path (`vm_lu_transitions`) is wrong; 44 receives land-type signal via `vm_bv` populated by land modules.
- **Why it matters**: low — the claim is hedged ("Transitive"), 44's non-direct status is correct, and the imprecision is in the mechanism gloss, not the consumer classification.
- **Root cause**: `answerer_confabulation` (plausible mechanism, not code-verified).

---

## Latent doc bugs (recorded per rubric §1.5; fix regardless of answer score)

The answer did NOT reproduce these — it correctly excluded 14/71/80 from the vm_land DIRECT list — so they did not lower the score. But the source doc is wrong vs code and the next answerer may trust it.

### DOC-L1 — module_10.md "PROVIDES TO" table lists vm_land for 14_yields (contradicts code + same doc's line 318)
- **File**: `modules/module_10.md:306` — `| **14_yields** | vm_land (1) | Yield calculations |`
- **Code reality**: 14_yields has ZERO `vm_land` references; it consumes `pm_land_start` (`14_yields/managementcalib_aug19/preloop.gms:15-16`). Same doc at `:318` explicitly states "11/14/39/71/80 contain zero `vm_land(` references." The table at :306 contradicts the prose at :318.
- **Severity (future-reader harm)**: Critical per the R20 anchor (wrong consumer/variable set in the canonical Module-10 table).
- **Root cause**: `doc_error_answerer_beat_it`.

### DOC-L2 — module_10.md "PROVIDES TO" table lists vm_land for 71_disagg_lvst
- **File**: `modules/module_10.md:312` — `| **71_disagg_lvst** | vm_land (1) | ... |`
- **Code reality**: 71 (default `foragebased_jul23`) has ZERO vm_land refs; it reads `pm_land_start` (`preloop.gms:9`) and `pcm_land` (`nl_fix.gms:13-14`). Contradicts :318.
- **Severity**: Critical (same anchor).
- **Root cause**: `doc_error_answerer_beat_it`.

### DOC-L3 — module_10.md "PROVIDES TO" table lists vm_land for 80_optimization
- **File**: `modules/module_10.md:313` — `| **80_optimization** | vm_land (1) | Objective function |`
- **Code reality**: 80 references `vm_landdiff` (NLP minimization objective, `lp_nlp_apr17/solve.gms:76,77,196,197`), NOT `vm_land`. Contradicts :318.
- **Severity**: Major (the variable should read `vm_landdiff`, not `vm_land`; semantic-scope wrong in the canonical table).
- **Root cause**: `doc_error_answerer_beat_it`.

**Shared fix**: the "Variables Provided" column at `module_10.md:299-313` conflates "provided to module X (transitively)" with "the variable is vm_land". For 14/71/80 the provided var is `pm_land_start`/`pcm_land`/`vm_landdiff` respectively, as the same doc's :318 prose and the safety-guide 18-union (which lists these as indirect) already make clear. Reconcile the table (rows 306/312/313) with the verified prose at :315-318.

(Not a bug, but worth a doc note: `module_10.md:307` lists 22_land_conservation as a vm_land consumer — correct, but 22 only READS `vm_land.lo` to compute restoration potential; it does not "enforce lower bounds on protected area" as the answer's §2.1 gloss says. Minor descriptive slip in the answer, folded into the verified-claims caveat, not separately scored.)

---

## Missing nuances (not scored)
- The answer calls 71 a transitive consumer that "uses pasture area transitively"; 71 actually reads `pm_land_start`/`pcm_land` DIRECTLY (in preloop/nl_fix) — it is a direct reader of Module-10 *parameters*, just not of `vm_land`. Framing understates the directness.
- The answer calls 80 a "pure sink … via cost aggregation chain"; mechanically 80 directly references `vm_landdiff` as the NLP objective (`solve … MINIMIZING vm_landdiff`). The cost-aggregation gloss is true for `vm_cost_glo` but the concrete Module-10 link is `vm_landdiff`.

## Summary
Spine is strong: the 2 inputs, the 10 direct vm_land consumers, the vm_carbon_stock declaration site (G2), the 52/56 direct readers, the populator set, and the CO2-pricing asymmetry are all code-accurate with exact citations. Errors are confined to the lower-stakes transitive enumeration of Module-10 *auxiliary-parameter* consumers: pm_land_start was attached to the wrong module (13, should be pcm_land) and the real pm_land_start consumer 14_yields was dropped (2 Major), plus an imprecise transitive path for 44 (Minor). Three latent doc errors in `module_10.md`'s PROVIDES-TO table (rows 306/312/313 list vm_land for 14/71/80, contradicting the same doc's verified prose at line 318 and the code) are recorded for unconditional fix.
