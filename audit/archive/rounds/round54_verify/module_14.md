# R54 Adversarial Verification - module_14.md

**Target doc:** `/Users/turnip/Documents/Work/Workspace/magpie/magpie-agent/modules/module_14.md` (1617 lines)
**Ground truth:** `/tmp/magpie_develop_ro` @ `0d7ebeb90` (develop worktree, read-only)
**Verifier:** adversarial, mechanical-first. Default = skepticism.
**Date:** 2026-07-14

## Headline

**26/26 citations passed the mechanical check. 0 REFUTED, 0 CITATION_FAILED.**
**11 UPHELD** (the attribution / realization-structure claims, each independently re-derived), **13 NOT_REVIEWABLE** (class *other* - citation verified, claim confirmed, passes to the fixer unchanged), **2 CORRECTED** (B10, B21 - the auditor's *diagnosis* is right but its proposed fix text would plant a small new error).

This is an unusually clean audit. I went in expecting the R33 confabulation class (invented realization structure, over/under-counted consumer sets) and probed hardest exactly there: B7 (M70 realization claim), B24 (M13 realization pointer), B13 (the full consumer/producer sets), B5 (4-module consumer set), B1 (the fabricated cycle). Every one reproduced against the code. I am not manufacturing disagreement to look diligent - the two CORRECTED verdicts below are real but small, and both are defects in the auditor's *proposed fix text*, not in its diagnosis.

## Method notes (what could have gone wrong and didn't)

- **A positive control caught my own broken probe.** My first pass at "does M59/M55/M50/M11/M70 read any M14 interface?" used `rg -c ... | paste -sd+ | bc`, which returned `vm_* hits = 0` for `11_costs` - impossible. `bc`/`paste` was the broken link, not `rg`. I discarded that pass and re-ran raw. Had I trusted it, I would have "confirmed" a negative with a dead command. This is exactly the failure mode the brief warns about.
- All absence claims were confirmed **twice, with two engines** (`rg` and `grep -r`), each with a **positive control** proving the search works in that directory.
- All consumer greps ran **both forms**: `NAME(` and `NAME.` (solution-level `.l/.lo/.up/.fx/.m`). This mattered: M14's `nl_fix.gms:10` reads `vm_tau.l(h,"crop")`, invisible to a `vm_tau(` grep.
- B6 (the "missing producer" class) was searched **repo-wide including `scripts/`, `config/` and the R layer** (`--hidden --no-ignore`), per the R53 lesson, not just `modules/*.gms`.

---

## Ground-truth base (established once, reused throughout)

`modules/14_yields/managementcalib_aug19/` line counts:

```
declarations 41 | equations 39 | input 96 | nl_fix 11 | nl_release 11
postsolve 24 | preloop 197 | presolve 81 | realization 41 | scaling 8 | sets 37
TOTAL = 586
```

`declarations.gms` anchors (drive B11/B15/B16):

```
:17  im_growing_stock(t,j,ac,land_timber)
:18  im_growing_stock_ysf(t,j,ac)
:19  pm_yields_semi_calib(j,kve,w)
:26  positive variables          <- block header
:27  vm_yld(j,kve,w)
```

**Exhaustive interface-symbol enumeration for M14** (`rg -o '\b(vm|pm|fm|sm|im|pcm)_[a-zA-Z0-9_]+'` over all `*.gms` + `module.gms`, sorted unique) - 20 real symbols (+1 comment typo `fm_croprea` at `preloop.gms:39`):

```
fm_aboveground_fraction  fm_carbon_density  fm_croparea  fm_ipcc_bef  fm_tau1995
im_growing_stock  im_growing_stock_ysf  pcm_tau
pm_carbon_density_other_ac  pm_carbon_density_plantation_ac
pm_carbon_density_secdforest_ac  pm_carbon_density_secdforest_ac_uncalib
pm_climate_class  pm_land_start  pm_past_mngmnt_factor  pm_yields_semi_calib
sm_carbon_fraction  sm_fix_cc  vm_tau  vm_yld
```

**No `vm_prod`. No soil-organic-matter, manure, or nitrogen symbol. Nothing from M59/M55/M50.** This single enumeration is the spine of B1.

Default realizations (`config/default.cfg`): land `landmatrix_dec18` (:232), tc `endo_jan22` (:293), yields `managementcalib_aug19` (:354), production `flexreg_apr16` (:612), cropland `detail_apr24` (:811), croparea `simple_apr24` (:912), past `endo_jun13` (:985), forestry `dynamic_may24` (:992), natveg `pot_forest_may24` (:1153), climate `static` (:1492), carbon `normal_dec17` (:1574), livestock `fbask_jan16` (:2164).

---

## Independently re-derived dependency sets (the R20/MANDATE-17 core)

**Downstream** (modules that DIRECTLY read an M14-declared/provided interface):

| Consumer | Symbol | Evidence |
|---|---|---|
| M30 croparea | `vm_yld` | `30_croparea/simple_apr24/equations.gms:15` (default) + `detail_apr24/equations.gms:15` |
| M31 past | `vm_yld` | `31_past/endo_jun13/equations.gms:18` (default) |
| M32 forestry | `im_growing_stock` | `32_forestry/dynamic_may24/equations.gms:249`, `presolve.gms:181,185` |
| M35 natveg | `im_growing_stock` | `35_natveg/pot_forest_may24/equations.gms:147,156,165` |
| M35 natveg | `im_growing_stock_ysf` | `35_natveg/pot_forest_may24/equations.gms:166` (sole consumer) |
| M17 production | `pm_yields_semi_calib` | `17_production/flexreg_apr16/presolve.gms:10` (sole consumer) |
| M52 carbon | `sm_carbon_fraction`, `fm_aboveground_fraction`, `fm_ipcc_bef` | `52_carbon/normal_dec17/preloop.gms:60,95` / `:61,96` / `:26` |

**= {17, 30, 31, 32, 35, 52}.** Exactly the auditor's set.

**Upstream** (modules M14 reads FROM): **{10, 13, 30, 45, 52, 70}** - `pm_land_start` (M10), `vm_tau`/`pcm_tau`/`fm_tau1995` (M13), `fm_croparea` (M30), `pm_climate_class` (M45), `pm_carbon_density_*` + `fm_carbon_density` (M52), `pm_past_mngmnt_factor` (M70).

**Direction checks (MANDATE 21):**
- **M70 is UPSTREAM, not downstream.** M14 reads `pm_past_mngmnt_factor` from M70 (`equations.gms:38`, `nl_fix.gms:11`). M70 reads **zero** M14 interfaces - confirmed twice, two engines, positive control. The doc listing M70 under "Modules that depend on Module 14" inverts the arrow.
- **M11 reads zero M14 interfaces** - transitive only.
- **M52 is BIDIRECTIONAL**: upstream (carbon densities -> M14 presolve) AND downstream (M14's `sm_carbon_fraction`/`fm_aboveground_fraction`/`fm_ipcc_bef` -> M52 preloop). Both halves are preloop/presolve *parameter* couplings, not an optimization cycle. **The fixer should state this explicitly in §21.2** - the auditor's B13 fix captures only the downstream half.

---

## Per-bug verdicts

### B1 - Critical - fabricated circular dependency - **UPHELD**

Citation: `preloop.gms` (197 lines, cited :8-197 in range), `presolve.gms` (81 lines), `17_production/flexreg_apr16/presolve.gms:10` = `pm_prod_init(j,kcr)=sum(w,fm_croparea("y1995",j,w,kcr)*pm_yields_semi_calib(j,kcr,w));` - contains the claimed token.

Every arrow in the doc's cycle (`module_14.md:1432-1446`) is independently false:
1. `vm_prod` -> M14: **zero occurrences of `vm_prod` in M14** (both forms; exit 1; positive control `vm_tau` found at `nl_fix.gms:10`, `equations.gms:16`).
2. `pm_yields_semi_calib` -> `vm_yld`: **false**. `pm_yields_semi_calib` is a 1995 snapshot written at `preloop.gms:116,149`; its only consumer is M17. `vm_yld` is computed from `i14_yields_calib` (`equations.gms:15`).
3. Manure/SOM -> yields: **no such path**. Word-boundary grep for `som|soilc|manure|nitrogen|excretion|vm_carbon_stock` in M14 -> exit 1 (positive control `pasture` found). M59/M55/M50 read zero M14 interfaces (2 engines + positive controls).

The doc contradicts itself: §8.3 (`:832`) "None directly in equations"; §11.6 (`:982`) nitrogen is external. The "SOM effects gradual: 15% annual convergence (Module 59)" resolution mechanism at `:1472` describes a feedback that does not exist.

*Note for fixer (no impact on the fix text):* the auditor's narrative says "exactly 18 symbols"; the true count is 20 (+1 comment typo). The substantive claim - none production/SOM/manure/nitrogen - is correct. The fix's input list (`f14_yields`, `f14_fao_yields_hist`, `f14_pyld_hist`, `f14_ir2rf_ratio`, `f14_yld_calib`, `f14_yld_ncp_report`, `f14_kcr_pollinator_dependence`, `fm_croparea`, `pm_land_start`, `fm_tau1995`) is complete and correct; `fm_tau1995` is indeed M13 (`13_tc/endo_jan22/input.gms:51`).

### B2 - Critical - `fm_croparea` attributed to M10 - **UPHELD**

`rg '(table|parameter)\s+fm_croparea' modules/` -> **only** `30_croparea/simple_apr24/input.gms:71` and `detail_apr24/input.gms:76`. Line 71 verbatim: `table fm_croparea(t_all,j,w,kcr) Different croparea type areas (mio. ha)`. `simple_apr24` is the default (`config/default.cfg:912`).

`rg -ni 'croparea' modules/10_land/` -> **exit 1** (zero). Positive control: `pm_land_start` found in the same dir at `declarations.gms:9`, `start.gms:8,11`. M10's real contribution to M14 is `pm_land_start(j,"past")` (`preloop.gms:15-16`).

### B3 - Major - four other-module parameters filed under "From Input Data" - **UPHELD**

All four declarations verified verbatim, each the sole declaration in the repo:
- `fm_croparea` -> `30_croparea/simple_apr24/input.gms:71`
- `pm_land_start` -> `10_land/landmatrix_dec18/declarations.gms:9` (populated `start.gms:8`)
- `fm_carbon_density` -> `52_carbon/normal_dec17/input.gms:16` (M52 has exactly one realization)
- `pm_climate_class` -> `45_climate/static/input.gms:10` = `table pm_climate_class(j,clcl) Koeppen-Geiger climate classification on the simulation cluster level (1)` (M45 has exactly one realization, `static`, also the default per `config/default.cfg:1492`)

The secondary claim also holds: `pm_climate_class` occurs in M14 **only** at `presolve.gms:29,38,47,56,69` - all five are the growing-stock BEF weighting. It appears **nowhere in `preloop.gms`**, so §21.2's "Climate class data for calibration" (`:1405`) is wrong.

Auditor's fix line-lists verified exactly: `fm_croparea` at `preloop.gms:60,68-73,127-128,138-143`; `pm_land_start` at `preloop.gms:15-16`.

### B4 - Major - "not an M52 parameter, which is why it is absent" - **UPHELD**

`52_carbon/normal_dec17/input.gms:16` declares AND `$include`s `fm_carbon_density`; `:22-23` apply the `c52_carbon_scenario` nocc/nocc_hist transform; `:31` zero-fills forest classes from `"other"`. All three lines verified verbatim. The literal sub-claim ("not a `pm_` parameter") is true; the doc's *inference* ("which is why it is absent from the From-Module-52 list") is false, and it hides a real coupling: M14's primforest growing stock inherits M52's carbon scenario switch.

*Bonus (auditor missed, no verdict impact):* `input.gms:35` also fixes urban `soilc` from `"other"`. Irrelevant to M14's `primforest`/`vegc` slice.

### B5 - Major - wrong commit + wrong consumer set for `pm_carbon_density_secdforest_ac_uncalib` - **UPHELD**

- `git show --stat 6b00f9dea` -> **4 files: CHANGELOG.md, 14_yields/declarations.gms (+1), 14_yields/presolve.gms (+16), 35_natveg/pot_forest_may24/equations.gms.** Nothing under `modules/52_carbon/`. Commit date **2026-07-01** (not 2026-07-14), author florianh, subject "Fix youngsecdf wood production: use uncalibrated growing stock".
- `git blame -L 10,10 52_carbon/normal_dec17/declarations.gms` -> **`896a9b728a` florianh 2026-03-21** "Address review comments: cost regionalization, naming conventions, calibration simplification". The parameter predates `6b00f9dea`.
- Consumer set (all occurrences, both forms) = **M14** `presolve.gms:66`, **M29** `detail_apr24/preloop.gms:46` (default realization), **M32** `dynamic_may24/presolve.gms:59,68`, **M35** `pot_forest_may24/presolve.gms:117,242,251`. Producer = M52 (`declarations.gms:10`, `start.gms:43`). **Four consumers, not one.** Corroboration: `29_cropland/simple_apr24/not_used.txt:6` explicitly lists it as "not needed" in the *non-default* M29 realization.

*Note for fixer:* the auditor's fix repeats the doc's slice notation `(t,j,ac,"vegc")`. The **declared** dimension is `(t_all,j,ac,ag_pools)`; `(t,j,ac,"vegc")` is M14's read-slice. Harmless as written (the fix labels it "declared ... declarations.gms:10"), but worth getting right.

### B6 - Major - invented producer for `f14_yld_ncp_report` - **UPHELD**

R53-safe search (`rg --hidden --no-ignore` over the **whole repo root**, not just `modules/`): `f14_yld_ncp_report` appears in exactly three places - `CHANGELOG.md:529`, `config/default.cfg:384` (a **comment**), and `modules/14_yields/` (`input.gms:83,85`; `preloop.gms:186,187,192,194`). **No module, script, or R file produces it.**

It is a module-local `$onEmpty` file table (`input.gms:82-88`), `$include`d only `$if exist`. If absent, `preloop.gms:186-188` sets it to **1** (no degradation). `s14_degradation` default 0 (`input.gms:17`, `config/default.cfg:389`). The doc's own §6.7 (`:678`) already calls it an optional input file - §3.6 (`:392`) contradicts it.

The auditor correctly did **not** make an R53-style "silently zero" claim: the guard sets it to 1, and provenance is attributed to the R preprocessing layer, not to a GAMS module. Fix is safe.

### B7 - Major - false realization-dependence for `pm_past_mngmnt_factor` - **UPHELD** (realization_structure, checked mechanically against BOTH realizations)

`ls modules/70_livestock/` -> exactly two realizations: `fbask_jan16`, `fbask_jan16_sticky`.

`diff fbask_jan16/presolve.gms fbask_jan16_sticky/presolve.gms` -> **only two differences**: (a) line 24, a comment-wording change ("The fbask_jan16 realization" vs "This realization"); (b) lines 71-95 appended, the sticky-capital block (`p70_capital_need`, `p70_capital`). The `pm_past_mngmnt_factor` code at lines 63-68 is **byte-identical** in both.

The real control is the scalar: `fbask_jan16/presolve.gms:63-68` reads
```gams
if (m_year(t) <= s70_past_mngmnt_factor_fix,
   pm_past_mngmnt_factor(t,i) = 1;
else
   pm_past_mngmnt_factor(t,i) = ( (s70_pyld_intercept + f70_pyld_slope_reg(i)*p70_incr_cattle(t,i)**...
```
with `s70_past_mngmnt_factor_fix` default **2005** (`fbask_jan16/input.gms:26` = `/ 2005 /`; `config/default.cfg:2173`). Switching realization changes nothing here. Declared `fbask_jan16/declarations.gms:41`.

### B8 - Major - `sm_carbon_fraction` mislabelled a bioenergy knob - **UPHELD**

`sm_carbon_fraction` (`input.gms:22`, `/ 0.5 /`) occurs in M14 only at `presolve.gms:27,36,45,54,67` (the five growing-stock curves) and outside M14 only at `52_carbon/normal_dec17/preloop.gms:60,95`. The bioenergy correction is `preloop.gms:11-12` and uses **`fm_tau1995` / `smax(h,fm_tau1995(h))` only** - no `sm_carbon_fraction`. Changing it would silently rescale all five growing-stock curves plus M52's FRA calibration and do nothing to bioenergy. Companion params confirmed: `fm_aboveground_fraction` -> M52 `preloop.gms:61,96`; `fm_ipcc_bef` -> M52 `preloop.gms:26`.

### B9 - Major - `s14_limit_calib` described as a continuous bound - **NOT_REVIEWABLE** (class: other; citation verified, claim independently confirmed)

`input.gms:15` verbatim: `s14_limit_calib   Relative managament calibration switch (1=limited 0=pure relative) / 1 /`. `preloop.gms:82-102` branches on exactly two values (`:85` `if (s14_limit_calib = 0)` -> `:86` lambda = 1; `:88` `Elseif (s14_limit_calib =1 )` -> `:89-92` lambda = 1 or `sqrt(LPJmL_reg/FAO)`). No bounds, no upper value. Doc §5.2 states it correctly; §21.4/§21.4-emergency do not. Fix is sound; pass through.

### B10 - Major - default config presented as a high-risk modification - **CORRECTED** (diagnosis right, fix text needs one word changed)

Diagnosis confirmed:
- `s14_use_yield_calib` default is **0** (`input.gms:18` = `/ 0 /`) - every stock run already has it. It only skips the optional post-hoc factors (`preloop.gms:165-173`).
- `s14_limit_calib = 0` does **not** remove calibration: `preloop.gms:86` sets lambda = 1, i.e. **pure relative FAO calibration**.
- Neither switch yields "pure LPJmL yields". The FAO calibration (`preloop.gms:108-116`) runs unconditionally.

**Correction to the proposed fix:** the fix says "The FAO calibration (`preloop.gms:108-116`) and the AQUASTAT ir2rf calibration (`preloop.gms:123-150`) **always run**." The ir2rf block is **gated**: `preloop.gms:123` is `if ((s14_calib_ir2rf = 1),`. It is on by default (`input.gms:16` = `/ 1 /`; `config/default.cfg:380`), but it is not unconditional, and writing "always run" into the doc would plant a fresh small error.

**Apply instead:** "...The FAO calibration (`preloop.gms:108-116`) always runs, and the AQUASTAT ir2rf calibration (`preloop.gms:123-150`) runs whenever `s14_calib_ir2rf = 1` (the default, `input.gms:16`; `config/default.cfg:380`) - **neither is affected by `s14_use_yield_calib` or `s14_limit_calib`**. To obtain uncalibrated LPJmL yields you would have to edit `preloop.gms` itself - a code change, not a config change."

### B11 - Major - `pm_yields_semi_calib` citation + sole consumer - **UPHELD**

`declarations.gms:18` = `im_growing_stock_ysf`; `pm_yields_semi_calib(j,kve,w)` is at **`:19`**. Both grep forms across all of `modules/`: the only reads are `preloop.gms:116,149` (writes, inside M14) and **`17_production/flexreg_apr16/presolve.gms:10`** (the sole external consumer). No `.l/.lo/.up/.fx/.m` reads anywhere. The doc's vague "Baseline reference for other modules" (`:750`) names no consumer; there is exactly one.

### B12 - Major - botched algebra at `module_14.md:276` - **NOT_REVIEWABLE** (class: other; formula independently re-derived)

Doc `:276` and `:277` both print the same "× 1" substitution. The code (`preloop.gms:108-112`) has the ratio raised to lambda:
```gams
(f14_yields(t,j,knbe14,w) / (sum(cell(i,j),i14_modeled_yields_hist(t,i,knbe14))+10**(-8))) ** sum(cell(i,j),i14_lambda_yields(t,i,knbe14))
```
I re-derived it independently. With R = LPJmL_cell / LPJmL_reg:
- lambda = 1: Factor = 1 + (FAO-LPJmL_reg)/LPJmL_cell × R = 1 + (FAO-LPJmL_reg)/LPJmL_reg = **FAO/LPJmL_reg** -> yield = LPJmL_cell × FAO/LPJmL_reg -> pure relative.
- lambda = 0: R^0 = 1 -> yield = LPJmL_cell + (FAO - LPJmL_reg) -> pure additive.

The auditor's replacement text is algebraically correct. Pass through.

### B13 - Major - incomplete/mis-directed dependency sets - **UPHELD**

See the re-derived table above. Confirmed exactly: downstream = {17, 30, 31, 32, 35, 52}; upstream = {10, 13, 30, 45, 52, 70}. §8.2 (`:817-828`) omits M35 and M52; §21.2 (`:1402-1414`) omits M10/M30/M70 upstream and M52 downstream, calls M35's dependency "implicit through land competition" when it is four direct reads, and lists **M70 as downstream when it is upstream**.

**Addition for the fixer:** state M52's **bidirectionality** explicitly (upstream carbon densities; downstream `sm_carbon_fraction`/`fm_aboveground_fraction`/`fm_ipcc_bef`). It is the only module on both lists, and a doc that lists it once will look like an error to the next reader.

### B14 - Minor - line count 569/557 vs actual - **NOT_REVIEWABLE** (verified: `wc -l` = **586**)

### B15 - Minor - `vm_yld` citation off-by-one - **NOT_REVIEWABLE** (verified: `:26` = `positive variables`, `:27` = `vm_yld(j,kve,w)`)

### B16 - Minor - stray contradictory citation at `module_14.md:736` - **NOT_REVIEWABLE**

Verified: `declarations.gms:17` = `im_growing_stock`, `:18` = `im_growing_stock_ysf`. Doc `:734` already says "**Declared:** `declarations.gms:18`" correctly; the trailing `:736` "**Citation:** `declarations.gms:17`" contradicts it two lines later. Deletion is safe.

### B17 - Minor - wrong commit for the `p14_pyield_corr` rewrite - **NOT_REVIEWABLE** (class: other; fully verified)

- `git blame -L 18,27 preloop.gms` -> lines **18-24 all blame to `2fa7b8bea9`** (florianh, **2026-04-28**, "refactor based on review comments"). That is the code the doc describes.
- `git show c7731e234 -- modules/14_yields/` -> **adds** `p14_corr_last(i)`, `p14_corr_prev(i)`, `p14_corr_trend(i)` plus the `sm_fix_SSP2` trend extrapolation capped at +/-10% per 5-year step. So "No new or renamed parameters" is false *as a statement about c7731e234*.
- `rg 'p14_corr_' modules/` -> **exit 1** (positive control: `p14_pyield_corr` found in `declarations.gms`, `preloop.gms`). Current develop has none - that version was superseded.

The same wrong attribution appears in the footer (`module_14.md:1617`).

### B18 - Minor - `@Heinke.2013` line - **NOT_REVIEWABLE** (verified: `preloop.gms:47` has no citation; `:54` = "(@Heinke.2013)"; `:106` = "eq. (9) in [@Heinke.2013]")

### B19 - Minor - `i14_fao_yields_hist` computed-in line - **NOT_REVIEWABLE**

Verified: `preloop.gms:88` = `Elseif (s14_limit_calib =1 ),` (would falsely imply conditionality); `:95` = `i14_fao_yields_hist(t,i,knbe14) = f14_fao_yields_hist(t,i,knbe14);` (unconditional inside the y1995 branch); `:99` carries it forward.

### B20 - Minor - `@FAOSTAT` citation - **NOT_REVIEWABLE**

Verified: `module.gms:16` = prose only ("level to meet the observed cropland and pasture area as reported by FAO"); `:17` = `[@FAOSTAT].`; `:21` = `[@fao_aquastat_2016]` (**not** @FAOSTAT). The fix's added pointers `realization.gms:11,17` both check out.

### B21 - Minor - `realization.gms` limitations range - **CORRECTED**

Verified: the `@limitations` block is `realization.gms:**24-27**`; line 23 is blank. So the fix for `module_14.md:31` (`:23-26` -> `:24-27`) is right.

**Correction to the proposed fix:** for `module_14.md:976` the auditor proposes `realization.gms:24-25`. The pasture-intensification limitation sentence actually spans **`:24-26`** ("...cannot / capture feedbacks between land scarcity and efforts to improve pasture / management."). `:24-25` truncates mid-sentence.

**Apply instead:** `module_14.md:976` -> ``(`realization.gms:24-26`)``.

### B22 - Minor - "18 crops" - **NOT_REVIEWABLE** (verified from `sets.gms:23-26`: `kcr` = **19** members; `kve` = 20; `knbe14` = 17, `sets.gms:28-31`)

### B23 - Minor - worked example - **NOT_REVIEWABLE** (arithmetic independently re-derived)

Doc §15.3 numbers: LPJmL_reg = 2, FAO = 6, LPJmL_cell(2050) = 4, lambda = sqrt(2/6) = 0.5774.
`yield = 4 + (6-2) × (4/2)^0.5774 = 4 + 4(1.4923) = 9.97 ≈ 10` tDM/ha = **1.7× FAO**, not 8 (1.3×).
Control: the doc's own lambda=1 line reproduces exactly (`4 + 4 × 2^1 = 12`), which validates my reading of the formula and isolates the error to the lambda=0.58 line.

### B24 - Minor - pointer into a non-default realization - **UPHELD** (realization_structure, both realizations read)

`config/default.cfg:293` -> `cfg$gms$tc <- "endo_jan22"`. Default declarations: `13_tc/endo_jan22/declarations.gms:13` = `vm_tau(j,tautype)`, `:27` = `pcm_tau(j, tautype)`. The doc points readers at `13_tc/exo/`, a **non-default** realization.

I checked the sibling rather than assuming: `13_tc/exo/declarations.gms:9` = `vm_tau(j,tautype)`, `:16` = `pcm_tau(j,tautype)`. So the auditor's parenthetical "(the `exo` realization agrees)" is **true** - both are cluster-level, and the doc's substantive claim survives. Only the pointer is wrong.

### B25 - Minor - deprecated *BCE* name - **NOT_REVIEWABLE**

Verified: `input.gms:66` = `parameter fm_ipcc_bef(clcl) IPCC biomass expansion factor BEF (1)`; used at `presolve.gms:29,38,47,56,69`. `f14_ipcc_bce` is **absent from the code** - two engines (`rg` whole-repo, `grep -r modules/`), both exit 1, positive control `fm_ipcc_bef` found (1 hit in `input.gms`, 5 in `presolve.gms`).

### B26 - Informational - non-verbatim code quote - **NOT_REVIEWABLE**

Verified: `input.gms:20` really does read `...into pasture yieldincreases  (1)     / 0.25 /` (missing space - an upstream typo). Doc `:605` silently fixes it to "yield increases". Name, default (0.25) and line number are all correct.

---

## Additional findings for the fixer (outside the audited bug set)

1. **`module_14.md:729` and `:1420`** also date commit `6b00f9dea` to **2026-07-14**. The true commit date is **2026-07-01** (`git show -s --format=%ad 6b00f9dea`). At these two lines the *commit* attribution is correct (it did add `im_growing_stock_ysf`); only the date is wrong. B5 fixes the date only at `:773`.
2. **M52 belongs on BOTH dependency lists** in §21.2 (see B13 note). Only module in the doc for which this is true.
3. **Possible upstream code issue, NOT verified further, out of scope:** `modules/14_yields/managementcalib_aug19/nl_fix.gms:10-11` index `vm_tau.l(h,"crop")` and `pcm_tau(h,"crop")` with the superregion set `h`, while both are declared over `(j,tautype)` and `equations.gms:16,39` use `j2`. If `nl_fix.gms` is compiled (NL mode), that reads like a domain violation. Flagging only; I did not chase it and it affects no verdict above.

## Verdict tally

| Verdict | Count | Bugs |
|---|---|---|
| UPHELD (attribution / realization claims, independently re-derived) | 11 | B1, B2, B3, B4, B5, B6, B7, B8, B11, B13, B24 |
| CORRECTED | 2 | B10 (ir2rf "always run"), B21 (`:24-25` -> `:24-26`) |
| NOT_REVIEWABLE (class *other*; citation verified, claim independently confirmed, pass through) | 13 | B9, B12, B14, B15, B16, B17, B18, B19, B20, B22, B23, B25, B26 |
| REFUTED | 0 | - |
| CITATION_FAILED | 0 | - |
| **Total** | **26** | |

All 26 bugs are safe to fix as written, **except** B10 and B21, which must use the corrected text above.
