# Adversarial Verification — module_52.md (Round 55 depth)

**Target doc**: `/Users/turnip/Documents/Work/Workspace/magpie/magpie-agent/modules/module_52.md` (1222 lines)
**Ground truth**: `/private/tmp/magpie_develop_ro` (read-only develop worktree)
**Role map**: `audit/integrated/depth_rolemap.json`
**Date**: 2026-07-16

## Default realizations (from `/private/tmp/magpie_develop_ro/config/default.cfg`)

```
cfg$gms$yields     <- "managementcalib_aug19"
cfg$gms$cropland   <- "detail_apr24"
cfg$gms$croparea   <- "simple_apr24"     <-- note: NOT detail_apr24
cfg$gms$forestry   <- "dynamic_may24"
cfg$gms$natveg     <- "pot_forest_may24"
cfg$gms$carbon     <- "normal_dec17"
cfg$gms$ghg_policy <- "price_aug22"
cfg$gms$som        <- "cellpool_jan23"
```

All realizations cited by the auditors are the DEFAULT ones. No realization-structure confabulation detected in this batch.

---

## Shared ground truth: `pm_carbon_density_secdforest_ac_uncalib` consumer set

Role map: `{"declared_in": "52_carbon", "populated_by": ["52"], "read_by": ["14","29","32","35","52"]}`

Independent re-derivation — **both** grep forms + file-list superset:

```
$ rg -n 'pm_carbon_density_secdforest_ac_uncalib\(' /private/tmp/magpie_develop_ro/modules/
29_cropland/detail_apr24/preloop.gms:46
14_yields/managementcalib_aug19/presolve.gms:66
52_carbon/normal_dec17/declarations.gms:10        (declaration)
52_carbon/normal_dec17/start.gms:43               (populate)
35_natveg/pot_forest_may24/presolve.gms:117
35_natveg/pot_forest_may24/presolve.gms:242
35_natveg/pot_forest_may24/presolve.gms:251
32_forestry/dynamic_may24/presolve.gms:59
32_forestry/dynamic_may24/presolve.gms:68

$ rg -n 'pm_carbon_density_secdforest_ac_uncalib\.' /private/tmp/magpie_develop_ro/modules/
NOMATCH   (no solution-level/attribute reads — no hidden consumers)

$ rg -ln 'pm_carbon_density_secdforest_ac_uncalib' /private/tmp/magpie_develop_ro/modules/
-> 29_cropland/detail_apr24, 29_cropland/simple_apr24/not_used.txt, 14_yields/managementcalib_aug19,
   52_carbon/normal_dec17 (decl+start), 32_forestry/dynamic_may24, 35_natveg/pot_forest_may24
```

**Confirmed reader set = {14, 29, 32, 35}** (+52 self-populate). Role map and code agree. The `.`-form grep returning NOMATCH is corroborated by the bare-name file list, which surfaces no additional module.

**M14 read verified verbatim** (`14_yields/managementcalib_aug19/presolve.gms`, 81 lines; line 66 in range):

```gams
*' Growing stock for young secondary forest (youngsecdf) regrowing on other land.
*' It is derived from the *uncalibrated* secondary-forest carbon curve (the same
*' curve youngsecdf carbon uses in 35_natveg), with the secondary-forest aboveground
*' fraction, so that its wood yield and its carbon stock are consistent.
im_growing_stock_ysf(t,j,ac) =
    (
     pm_carbon_density_secdforest_ac_uncalib(t,j,ac,"vegc")   <-- line 66
     / sm_carbon_fraction
     * fm_aboveground_fraction("secdforest")
     / sum(clcl, pm_climate_class(j,clcl) * fm_ipcc_bef(clcl))
    )
    ;
```

Doc state: line 458 Consumers = {32, 29}. Lines 138 / 292 add {35}. **Module 14 appears at NO location** for the uncalib variable. Omission confirmed.

---

## module_52:1 — UPHELD (Critical)

**Class**: consumer_set. **citation_ok**: true.

- `test -f modules/14_yields/managementcalib_aug19/presolve.gms` -> EXISTS; `wc -l` -> 81; line 66 in range.
- Line 66 contains `pm_carbon_density_secdforest_ac_uncalib(t,j,ac,"vegc")` -> token present.
- Re-derived set {14,29,32,35} matches role map; doc omits 14 at 458, 138, 292.

The auditor's tier_uncertainty note is fair (1 of 4 missed; M14 *is* documented for the calibrated sibling at line 452 and line 722-724, so the omission is localized to the uncalib entry). Rubric §1.5 mandates Critical for the `pm_carbon_density_*_ac_uncalib` incomplete-consumer-set class (R20 immutable anchor). Severity retained as Critical.

## module_52:2 — UPHELD (Major)

**Class**: producer_declaration. **citation_ok**: true.

- `ls -d modules/29_* modules/30_*` -> `29_cropland`, `30_croparea`. The doc's "Module 30 (Cropland)" at line 712 is a **name error**: 30 is Croparea.
- `rg -n 'vm_carbon_stock\('` -> populating equations in **29** (detail_apr24:39, simple_apr24:30), **31** (endo_jun13:23), **32** (dynamic_may24:108), **35** (pot_forest_may24:43,50,54), **59** (cellpool_jan23:62, static_jan19:12,18,22). **No 30_croparea hit.**
- `rg -n 'vm_carbon_stock\.'` -> **34** fixes it (`exo_nov21/presolve.gms:8`, `static/presolve.gms:10`, `.fx = 0`); 31/static fixes via `.fx` (presolve.gms:15); 56 only `.l`-initializes in preloop.gms:11 + scaling + postsolve reads. No 30 hit.
- One-hop chain confirmed: `30_croparea/{detail,simple}_apr24/equations.gms:{88,50}` populate `vm_carbon_stock_croparea`; `29_cropland/detail_apr24/equations.gms:39-42` (`q29_carbon`) folds it into `vm_carbon_stock(j2,"crop",...)`. Role map `vm_carbon_stock_croparea`: populated_by=[30], read_by=[29,30] — consistent.

**Minor discrepancy noted** (does not change the verdict): the auditor quotes the role map as `populated_by=[29,31,32,34,35,59]`; the actual map reads `[29,31,32,34,35,56,59]` — it includes **56**. That 56 entry reflects only the `vm_carbon_stock.l(...) = pcm_carbon_stock(...)` preloop initialization inside 56 (its own declaring module), not a land-type populator, so the doc's line-424 list is correct as written and the auditor's substantive claim stands. Direction verified at both endpoints. Line 712 is internally contradictory with line 424 and omits 29 and 59. Proposed fix is correct.

## module_52:4 — UPHELD (Major)

**Class**: mechanism (parallel-not-serial data flow). **citation_ok**: true.

- `modules/56_ghg_policy/price_aug22/equations.gms` -> 79 lines; lines 17 and 19-22 in range.
- Line 17 verbatim: `vm_emissions_reg(i2,emis_annual,pollutants);` — the `q56_emis_pricing` (line 15) RHS. **emis_annual slice only.**
- Lines 19-22 verbatim: `q56_emis_pricing_co2(i2,emis_oneoff) .. v56_emis_pricing(i2,emis_oneoff,"co2_c") =e= sum(..., (pcm_carbon_stock(...,"actual") - vm_carbon_stock(...,"%c56_carbon_stock_pricing%"))/m_timestep_length);` — **recomputes CO2 from carbon stocks directly**, does not read M52's output.
- M52 writes exactly `vm_emissions_reg(i2,emis_oneoff,"co2_c")` (`52_carbon/normal_dec17/equations.gms:17`, eq `q52_emis_co2_actual` at :16).
- **Disjointness proven** from `core/sets.gms:314-323`: `emis_oneoff` = {crop_vegc … other_soilc} (land carbon pools); `emis_annual` = {inorg_fert, man_crop, awms, resid, man_past, som, rice, ent_ferm, resid_burn, peatland}. **No overlap** -> M56's pricing equation provably cannot read M52's slice.
- **Only other reader ruled out**: M57 (`on_aug22/equations.gms:38,48`) reads `vm_emissions_reg(i2,emis_source,pollutants_maccs57)` over the *full* emis_source set — but `57_maccs/on_aug22/sets.gms:25-26` gives `pollutants_maccs57 / ch4, n2o_n_direct /`, which **excludes co2_c**. So M57 does not read M52's slice either.
- Remaining read of the slice: `56_ghg_policy/price_aug22/postsolve.gms:27` `ov_emissions_reg(...) = vm_emissions_reg.l(...)` — **reporting only**.

Conclusion: no equation consumes M52's `vm_emissions_reg(i,emis_oneoff,"co2_c")`. Doc line 443's "Module 56 … for carbon pricing and emission constraints" is false as to pricing; M56 is a reporting-only consumer of this slice. R51 parallel-not-serial anchor applies. Doc lines 740-741 and 765 carry the same error. Proposed fix is correct and precise.

## module_52:5 — UPHELD (Major) — duplicate of module_52:1

**Class**: consumer_set. **citation_ok**: true. Same evidence as module_52:1 (M14 presolve.gms:66 verified verbatim).

Substantively identical finding to module_52:1 at the same doc line (458). Both are correct; they should be **merged into one finding**, not double-counted. Bug 5's extra observation is accurate: line 458's formal Consumers entry omits **both** 14 and 35, while 138/292 carry 35. Its proposed fix additionally names line 727 — note that 727 sits inside the "Module 29 (Cropland)" per-module subsection, so adding M14 *there* is misplaced; M14 already has its own subsection at 722-724, which is where the uncalib variable should be added. Fix at 458/138/292 as stated.

## module_52:9 — UPHELD (Major)

**Class**: consumer_set. **citation_ok**: true.

- `rg -n 'im_vol_conv' modules/14_yields/managementcalib_aug19/presolve.gms` -> **NOMATCH**.
- **Positive control**: `rg -c 'sm_carbon_fraction'` on the same file -> **6** (search demonstrably works in that file).
- **Second method**: `rg -n 'im_vol_conv' modules/14_yields/` (whole module) -> **NOMATCH**.
- Full-repo `rg -n 'im_vol_conv' modules/` -> hits only in `52_carbon/normal_dec17` (declarations:23, start:40, preloop:21,63,98) and `73_timber/default` (preloop:49,51,90,91; realization.gms:14). Role map `read_by=[52,73]` agrees.
- M14's GS formula (presolve.gms:44-73) = `carbon_density / sm_carbon_fraction * fm_aboveground_fraction / sum(clcl, pm_climate_class*fm_ipcc_bef)` — **no division by wood density**; output is tDM/ha.
- M52's calibration GS formula (`preloop.gms:57-64`) is that same structure **plus** `/ i52_bef_avg(i) / im_vol_conv(i)` (line 63), converting to m3/ha.

The doc's own line 490 correctly lists only M73. Line 5's "shared with Module 14's growing-stock formula" attributes an `im_vol_conv` read to M14 that does not exist. (A charitable reading — "M52's calibration reuses M14's growing-stock formula *structure*" — is true, but that is not what the parenthetical says, and it is attached to `im_vol_conv`.) Proposed fix (delete the clause) is correct.

## module_52:10 — CORRECTED (Major)

**Class**: consumer_set. **citation_ok**: true (with one imprecision, below).

Citation check:
- `14_yields/managementcalib_aug19/presolve.gms:66` -> token present (verified verbatim above).
- `35_natveg/pot_forest_may24/presolve.gms` -> 294 lines; 117, 242, 250-251 all in range.
  - :117 -> `p35_land_other(t,j,"youngsecdf",ac)$(pm_carbon_density_secdforest_ac_uncalib(t,j,ac,"vegc") > 20);` — token present.
  - :242 -> `p35_carbon_density_other(t,j,"youngsecdf",ac,ag_pools) = pm_carbon_density_secdforest_ac_uncalib(t,j,ac,ag_pools);` — token present.
  - :251 -> `- (pm_carbon_density_secdforest_ac(...) - pm_carbon_density_secdforest_ac_uncalib(...))` — token present.
  - **:250 does NOT contain the token** (`pm_carbon_density_secdforest_ac(t,j,ac,ag_pools)` — the *calibrated* var). The rg hit list is 117, 242, **251** only. "250-251" is defensible as a span citation of the blend statement (249-252), but the precise anchor is 251.

Core finding is **correct and UPHELD**: the consumer set at line 458 is incomplete (omits 14 and 35), and the universal "All three use cases represent *new establishment*" is false.

**Correction to the auditor's characterization**: the claim that M14 and M35 "are both youngsecdf regrowth" is right for M14 (`im_growing_stock_ysf`) and for M35:117/:242 (youngsecdf), but **wrong for M35:249-252**, which is the *secdforest natural-origin blend* — a weighted average of the FRA-calibrated curve and the uncalibrated natveg curve via `pc35_secdforest_natural / pc35_secdforest`, i.e. existing secondary forest of natural origin, not youngsecdf regrowth. The proposed fix's "M14/M35 use it for youngsecdf regrowth" therefore under-describes M35's second use.

**corrected_claim**: Line 458's Consumers list must read: Module 32 (afforestation `"aff"` when `s32_aff_plantation = 0`, `dynamic_may24/presolve.gms:59`; NDC forest `"ndc"`, `:68`), Module 29 (tree cover on cropland when `s29_treecover_plantation = 0`, `detail_apr24/preloop.gms:46`), Module 14 (young-secondary-forest growing stock `im_growing_stock_ysf`, `managementcalib_aug19/presolve.gms:66`), Module 35 (youngsecdf land/carbon at `pot_forest_may24/presolve.gms:117,242` **and** the secdforest natural-origin blend at `:249-252`, anchor `:251`). Confirmed set = {14, 29, 32, 35}. Replace "All three use cases represent *new establishment*" with: M32/M29 use the uncalibrated curve for **new establishment**; M14 and M35:117/242 use it for **youngsecdf regrowth**; M35:249-252 uses it as the **natural-origin component of the secdforest blend**.

Note the M32/M29 uses are additionally **switch-conditional** (`s32_aff_plantation`, `s29_treecover_plantation`): at value 1 they read the *plantation* uncalib variable instead. The existing doc captures this at lines 478 and 280; line 458 should not imply an unconditional read.

---

## Summary

| Bug | Class | citation_ok | Verdict |
|-----|-------|-------------|---------|
| module_52:1 | consumer_set | true | UPHELD (Critical) |
| module_52:2 | producer_declaration | true | UPHELD (Major) |
| module_52:4 | mechanism | true | UPHELD (Major) |
| module_52:5 | consumer_set | true | UPHELD (Major) — duplicate of :1 |
| module_52:9 | consumer_set | true | UPHELD (Major) |
| module_52:10 | consumer_set | true | CORRECTED (Major) |

6/6 citations reproduced mechanically. No confabulated realizations, no phantom consumers, no out-of-range lines. Bugs 1/5/10 are three views of one defect (M14 missing from the uncalib consumer list at 458); recommend merging to a single Critical finding whose fix also restores M35 and adds the switch-conditionality note.

Notable near-miss caught by verification: the auditors' role-map quote in bug 2 dropped module 56 from `vm_carbon_stock` populated_by. Immaterial to the verdict (56's entry is a preloop `.l` init inside its own declaring module), but it shows the role-map quotes in this batch were paraphrased rather than read.
