# Round 33 Doc Audit — module_29.md (Cropland)

**Auditor**: adversarial doc auditor (Opus, highest capability)
**Target**: `magpie-agent/modules/module_29.md`
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree) + `config/default.cfg`
**Date**: 2026-05-30
**Realization audited**: `detail_apr24` (confirmed default)

---

## Pre-run advisory verdict

The advisory flagged three things. Verdict:

1. **"Default realization detail_apr24 (NOT simple_apr24)"** — **CONFIRMED CORRECT in doc**. `config/default.cfg:795` = `cfg$gms$cropland <- "detail_apr24"` and `:806` = `cfg$gms$c29_marginal_land <- "q33_marginal"`. The doc's `> ⚙️ Default Realization: detail_apr24` block (lines 11-12) is accurate. No bug.
   (Note: initial `grep "cfg\$gms\$cropland"` returned empty due to `$` shell-escaping; positive control on `cfg$gms$yields` proved the search method, and a bracket-class grep recovered line 795. Verified twice.)

2. **"Verify vm_carbon_stock_croparea producer/consumer attribution (R24 issue)"** — doc is **CORRECT** here. `vm_carbon_stock_croparea` is declared in M30 (`30_croparea/detail_apr24/declarations.gms:23`) and read only by M29 (`q29_carbon`) and M30 itself — verified via `rg -ln`. The doc (line 694) attributes it to "Provided By Module 30 (Croparea)" and shows q29_carbon reading it. No mis-attribution to M52/M56. No bug on this specific point.

3. **"Keep cropland-specific carbon variables distinct from M52's vm_carbon_stock"** — partially violated, but via a DIFFERENT variable. The doc correctly keeps `vm_carbon_stock_croparea` distinct. BUT the doc uses the WRONG carbon-density parameter names in Algorithm 6 and in the Carbon-Balance prose (uses `pm_carbon_density_secdforest_ac` / `pm_carbon_density_plantation_ac` instead of the `_uncalib` variants the code actually reads) AND mis-attributes them to Module 59 when they live in Module 52. See Bug B.

---

## Claims verified CORRECT (high-value confirmations)

- **All 16 equation formulas** (Sections 1-16) match `detail_apr24/equations.gms` exactly: q29_cropland, q29_avl_cropland, q29_cost_cropland, q29_carbon, q29_land_snv, q29_land_snv_trans, q29_fallow_min, q29_fallow_max, q29_fallow_bv, q29_treecover, q29_treecover_min, q29_treecover_max, q29_treecover_bv, q29_cost_treecover_est, q29_cost_treecover_recur, q29_treecover_est. Equation count 16 confirmed (declarations.gms:48-65).
- **simple_apr24**: q29_cropland = croparea only (`simple_apr24/equations.gms:12-13`); 5 equations; fallow/treecover fixed to zero (`simple_apr24/preloop.gms:9-10`). Doc correct.
- **Equation citations** (sampled, all correct): q29_cropland detail 11-12; q29_avl_cropland 22-23; q29_cost_cropland 28-32; q29_carbon 38-42.
- **Scalar defaults** (input.gms): s29_cost_treecover_est=2460 (:18), s29_cost_treecover_recur=615 (:19), s29_treecover_plantation=0 (:20), s29_treecover_bii_coeff=0 (:21), s29_treecover_max=1 (:27), s29_treecover_penalty_before=0 (:28), s29_treecover_penalty=6150 (:29), s29_fallow_target=0 (:32), s29_fallow_max=0 (:33), s29_fallow_penalty=615 (:34), s29_treecover_map=0 (:35), s29_fader_functional_form=2 (:36). All match doc config tables.
- **c29_marginal_land** default = q33_marginal: input.gms:8 + config:806. Correct.
- **land_snv = {secdforest, other}** at input.gms:70. Correct (doc lines 208, 1046).
- **ag_pools = {vegc, litc}** (above-ground), defined `56_ghg_policy/price_aug22/sets.gms:209-210`. Doc Section 4 line 185 ("Above-ground pools (vegetation, litter)") is CORRECT — which makes the "four pools" claim elsewhere a self-contradiction (Bug C).
- **vm_carbon_stock declared in Module 56** (`56_ghg_policy/price_aug22/declarations.gms:34`), NOT M52. (G2 anchor consistent; doc never claims M52 declares it.)
- **Provided-variable consumer sets** (verified via rg -ln, cross-checked):
  - vm_fallow → M32 (forestry/dynamic_may24/presolve.gms:19), M50 (nr_soil_budget/macceff_aug22/equations.gms), M59 (som/cellpool_jan23/equations.gms). Doc line 682 lists 32, 50, 59. CORRECT.
  - vm_treecover → M22 (land_conservation/area_based_apr22/presolve_ini.gms), M59. Doc line 683 lists 22, 59. CORRECT.
  - vm_cost_cropland → M11 (costs/default/equations.gms). CORRECT.
  - vm_bv → M44 (declared there: bii_target/declarations.gms:11, bv_btc_mar21/declarations.gms:19). CORRECT.
  - All consuming-module default realizations confirmed in default.cfg: costs=default, som=cellpool_jan23, nr_soil_budget=macceff_aug22, forestry=dynamic_may24, land_conservation=area_based_apr22.
- **vm_land / vm_lu_transitions supplementary citations** (doc lines 695, 871) — ALL verified against current develop:
  - vm_lu_transitions: 35_natveg/pot_forest_may24/presolve.gms:58 ✓; 59_som/cellpool_jan23/equations.gms:51 ✓
  - vm_land: 22_land_conservation/area_based_apr22/presolve_ini.gms:86 ✓; 30_croparea/simple_apr24/equations.gms:23 ✓; 31_past/static/presolve.gms:11 ✓; 32_forestry/dynamic_may24/presolve.gms:19 ✓; 34_urban/static/presolve.gms:9 ✓; 35_natveg/pot_forest_may24/presolve.gms:40 ✓; 58_peatland/v2/equations.gms:23 ✓; 59_som/cellpool_jan23/equations.gms:33 ✓
- **Upstream interface set actually read by M29** (definitive enumeration from equations+presolve+preloop): vm_area, vm_carbon_stock_croparea (M30); vm_land, vm_lu_transitions (M10); pm_interest (M12); pm_land_conservation (M22); pm_carbon_density_secdforest_ac_uncalib, pm_carbon_density_plantation_ac_uncalib (M52); pm_land_hist (core/M10); fm_* (core). The doc's "Upstream Dependencies" prose section (lines 786-801) correctly lists M10/M30/M12/M22 but omits M52.

---

## BUGS

### Bug 29-B1 — Major — Fabricated upstream dependencies (Module 14 Yields, Module 16 Demand)

- **Doc line**: module_29.md:899-903 ("Depends On (7 modules): ... 2. Module 14 (Yields) - Yield parameters for fallow/tree cover productivity; 3. Module 16 (Demand) - Demand signals affecting land use; Plus 4 other modules ...")
- **Reality**: Module 29 reads NO yield variable and NO demand variable. Definitive interface enumeration of all M29 detail_apr24 files shows only: vm_area, vm_carbon_stock_croparea (M30), vm_land, vm_lu_transitions (M10), pm_interest (M12), pm_land_conservation (M22), pm_carbon_density_*_ac_uncalib (M52), pm_land_hist, fm_*.
- **Verify cmd**:
  - `grep -rc 'vm_yld' .../29_cropland/detail_apr24/*.gms` → zero in all files
  - `grep -rc 'vm_dem\|vm_supply' .../29_cropland/detail_apr24/*.gms` → zero in all files
  - Positive control `grep -rc 'vm_area'` → equations.gms:1 (search works).
- **Severity reasoning**: §1 Major trigger "Fabricated count/membership for a set/dependency list". Misleads modification-impact analysis (a user would hunt for non-existent yield/demand couplings). Between Major and Critical (R20 wrong-dependency-set anchor) → tie-breaker pulls to Major (these are invented padding, not omitted real consumers in a refactor; upstream direction).
- **Proposed fix**: Replace the fabricated entries. Real upstream dependencies are: Module 10 (Land: vm_land, vm_lu_transitions), Module 30 (Croparea: vm_area, vm_carbon_stock_croparea), Module 12 (Interest: pm_interest), Module 22 (Conservation: pm_land_conservation), Module 52 (Carbon: pm_carbon_density_secdforest_ac_uncalib / pm_carbon_density_plantation_ac_uncalib), plus core data (fm_carbon_density, fm_bii_coeff, fm_luh2_side_layers, pm_land_hist). Remove Module 14 and Module 16.

### Bug 29-B2 — Major — Wrong carbon-density parameter names (missing `_uncalib`) + wrong module attribution

- **Doc lines**: module_29.md:642, :650 (Algorithm 6 code blocks), and :851 (Carbon-Balance prose).
- **Claim in doc** (line 642): `p29_carbon_density_ac(t,j,ac,ag_pools) = pm_carbon_density_secdforest_ac(t,j,ac,ag_pools);` and (line 650) `= pm_carbon_density_plantation_ac(...)`. Line 851: "Module 59 calculates equilibrium: `pm_carbon_density_secdforest_ac` for tree cover".
- **Reality**: `29_cropland/detail_apr24/preloop.gms:46` uses `pm_carbon_density_secdforest_ac_uncalib`; `:48` uses `pm_carbon_density_plantation_ac_uncalib`. Both `_uncalib` parameters are declared in **Module 52** (`52_carbon/normal_dec17/declarations.gms:10,13`), NOT Module 59 (M59 has zero references — verified). The non-`_uncalib` forms exist too (52_carbon/.../declarations.gms:9,12) and are SEMANTICALLY DIFFERENT (calibrated vs uncalibrated density), so the doc cites the wrong one as the literal assignment.
- **Verify cmd**:
  - `rg -n 'p29_carbon_density_ac' .../29_cropland/detail_apr24/` → preloop.gms:46 (= ..._secdforest_ac_uncalib), :48 (= ..._plantation_ac_uncalib)
  - `rg -n 'pm_carbon_density_(secdforest|plantation)_ac' .../modules/*/*/declarations.gms` → all four declared in 52_carbon/normal_dec17
  - `rg -ln 'pm_carbon_density_secdforest_ac' .../59_som/` → NOT in module 59
- **Severity reasoning**: §1 Major "Wrong variable ... semantic scope wrong". This is the exact MANDATE 13 / R20 `_uncalib` pattern. Both names exist (so not the Critical "invented variable" trigger), but a user copying line 642/650 into the model would silently reference the calibrated parameter and get different carbon values. Compounded by wrong-module attribution (M59 vs M52) on line 851.
- **Proposed fix**:
  - Line 642 → `p29_carbon_density_ac(t,j,ac,ag_pools) = pm_carbon_density_secdforest_ac_uncalib(t,j,ac,ag_pools);`
  - Line 650 → `p29_carbon_density_ac(t,j,ac,ag_pools) = pm_carbon_density_plantation_ac_uncalib(t,j,ac,ag_pools);`
  - Line 851 → "Module 52 provides the age-class carbon density `pm_carbon_density_secdforest_ac_uncalib` (natveg curve) / `pm_carbon_density_plantation_ac_uncalib` (plantation curve); Module 29 reads it in preloop into `p29_carbon_density_ac`."
  - Also update Algorithm 6 prose (lines 640, 648) and Source line 658 to name the `_uncalib` parameters.

### Bug 29-B3 — Major — "Four carbon pools" claim contradicts code (q29_carbon is above-ground only) and invents a below-ground pool

- **Doc lines**: module_29.md:840-849 ("tracks cropland carbon stocks across four pools: 1. Vegetation carbon ... 2. Litter carbon ... 3. Soil carbon (largest pool, dynamic via Module 59) ... 4. Below-ground carbon: Root biomass") and module_29.md:894 ("Module 52 (Carbon) - Cropland carbon stocks (four pools)").
- **Reality**: `q29_carbon(j2,ag_pools,stockType)` operates over `ag_pools = {vegc, litc}` only — TWO above-ground pools. It produces `vm_carbon_stock(j2,"crop",ag_pools,stockType)` for vegc+litc. Soil carbon (`soilc`) for cropland is NOT set by q29_carbon (it is populated separately by the SOM module). The full carbon-pool set `c_pools = {vegc, litc, soilc}` (core/sets.gms:325) has only three members — there is NO separate "below-ground" pool. The doc's own Section 4 (line 185) correctly states ag_pools = above-ground (vegetation, litter), so this section self-contradicts.
- **Verify cmd**: `grep -n -A2 'ag_pools' .../56_ghg_policy/price_aug22/sets.gms` → `ag_pools(c_pools) / vegc, litc /`; `sed -n '324,325p' core/sets.gms` → `c_pools /vegc,litc,soilc/`.
- **Severity reasoning**: §1 Major — misleads about what the cropland carbon equation actually computes (a reader would think q29_carbon tracks soil and root carbon; it tracks neither). Invents a non-existent pool. Not Critical (no wrong code edit directly), but a clear behavior misdescription.
- **Proposed fix**: In the Carbon-Balance section, replace "four pools" with "two above-ground pools (`ag_pools = {vegc, litc}`)" and clarify: "q29_carbon sets only the above-ground crop carbon (vegetation + litter). Cropland SOIL carbon (soilc) is populated separately by the SOM module (59), not by q29_carbon. There is no separate below-ground pool — c_pools = {vegc, litc, soilc}." Fix line 894 likewise ("Cropland above-ground carbon stocks (vegc, litc)").

### Bug 29-B4 — Minor — "Scaling file not present in module" is false (file exists; statements commented out)

- **Doc lines**: module_29.md:778-780 ("No scaling applied in this module. Scaling file not present in module.")
- **Reality**: `detail_apr24/scaling.gms` EXISTS (638 bytes) and is included via realization.gms:28. All seven scale statements (q29_avl_cropland, q29_cropland, q29_fallow_max, q29_fallow_min, q29_land_snv_trans, q29_treecover, q29_treecover_est) are COMMENTED OUT (`*` prefix), so the operative claim "no scaling applied" is correct.
- **Verify cmd**: `ls -la .../detail_apr24/` shows scaling.gms (638 B); `cat scaling.gms` shows all lines `*`-commented.
- **Severity**: Minor — the substantive claim (no active scaling) is right; only the file-existence statement is wrong. A reader is not misled into a wrong action.
- **Proposed fix**: Replace "Scaling file not present in module." with "A `scaling.gms` file exists (`detail_apr24/scaling.gms`) but all scale statements are commented out, so no scaling is applied by default."

### Bug 29-B5 — Minor — q29_land_snv citation range end wrong (`equations.gms:49-49`)

- **Doc line**: module_29.md:194 ("**Formula** (`equations.gms:49-49`)").
- **Reality**: q29_land_snv spans `equations.gms:49-52` (4 lines). The doc displays the full correct multi-line formula but cites only line 49 as the range end.
- **Verify cmd**: `sed -n '49,52p' .../detail_apr24/equations.gms` → equation body runs 49-52.
- **Severity**: Minor (MANDATE 16 range-end gap; content shown is correct and complete).
- **Proposed fix**: Change `equations.gms:49-49` to `equations.gms:49-52`.

### Bug 29-B6 — Informational — set name `marginal_land` vs actual `marginal_land29`

- **Doc lines**: module_29.md:124, :666, :692 (dimension label "marginal_land" / "(j, marginal_land)").
- **Reality**: The GAMS set is `marginal_land29` (`detail_apr24/sets.gms:10`). The option members (all_marginal, q33_marginal, no_marginal) are listed correctly.
- **Severity**: Informational/Minor — recoverable, correct concept, only the bare set name drops the `29` suffix.
- **Proposed fix**: Use `marginal_land29` for the set name where the doc references the set (optional; low priority).

### Informational — verification-footer over-claim

module_29.md:1097 ("No Errors Found: Zero discrepancies between code and documentation") and :1104 ("Verification Status: 100% verified") are over-claims given B1-B3. Footer metadata (rubric §1 Informational — readers don't act on it). Recommend softening after fixes land.

---

## Deferred (NOT edited — uncertain or not code-verifiable)

- Centrality "Rank 9 / 13 connections / provides to 6 / depends on 7" (lines 887-888): these match `core_docs/Module_Dependencies.md:39`, so they are internally consistent cross-doc numbers, not a code bug. The *named* fabricated members (M14/M16) are the code-checkable error (Bug B1); the count itself is left alone.
- "Provides To (6 modules)" summary (lines 891-897) lists M10/M11/M52/M59/M22 and omits M44/M50/M32 (all real consumers), while the "Downstream Dependencies" section (lines 802-814) lists M10/M11/M44. The listed members are all real (no phantoms); the inconsistency/incompleteness is a doc-internal tidiness issue rather than a false code claim — deferred to avoid over-flagging a count section that cites Module_Dependencies.md.
- vm_land/vm_lu_transitions supplementary citations point at the `static`/`simple_apr24` realization files for M31/M30/M34 (non-default realizations), though vm_land is referenced in those files at the cited lines and the claim "vm_land is read by these modules" is true. Whether to prefer the default-realization file for each citation is a stylistic call, not a falsified claim — deferred.
- Doc's "tree cover increases soil carbon (100% of natural levels)" (line 848) — could not cleanly verify the "100%" figure against code in scope (soilc handling is in M59); deferred rather than invent a bug.

---

## Summary

equations/defaults/realization-default/consumer-sets for provided variables: all verified correct. Three Major content bugs: (B1) fabricated upstream deps M14/M16 (code reads neither vm_yld nor any demand var); (B2) wrong carbon-density param names — uses non-`_uncalib` forms and attributes them to M59 when code uses `pm_carbon_density_*_ac_uncalib` from M52; (B3) "four carbon pools incl. soil + below-ground" contradicts code (q29_carbon is ag_pools={vegc,litc} only; c_pools has no below-ground member). Two Minor (scaling-file-not-present false; q29_land_snv 49-49 range end) + Informational set-name and footer over-claim. Pre-run advisory confirmed on default; vm_carbon_stock_croparea attribution is correct in doc.
