# Audit Report: R54-youngsecdf (calibration anchor) — youngsecdf wood/carbon consistency

**Auditor**: Opus 4.8 (1M) | **Date**: 2026-07-15 | **Ground truth**: `/tmp/magpie_develop_ro` @ develop HEAD 0d7ebeb90

## Overall Verdict: ACCURATE
## Accuracy Score: 10/10
## drift_observed: false

---

## Verified Claims (all confirmed against code)

| Claim in answer | Code evidence | Status |
|---|---|---|
| Interface param `im_growing_stock_ysf(t,j,ac)` | `14_yields/managementcalib_aug19/declarations.gms:18` (verbatim) | ✅ |
| Populated `presolve.gms:64-71` | assignment spans exactly lines 64-71 | ✅ |
| Clamps `presolve.gms:80-81` | positivity + s14_minimum_growing_stock clamps at 80-81 | ✅ |
| Formula from `pm_carbon_density_secdforest_ac_uncalib(t,j,ac,"vegc")` / sm_carbon_fraction * fm_aboveground_fraction("secdforest") / sum(clcl,...) | matches presolve.gms:64-71 exactly | ✅ |
| SOLE consumer = `q35_prod_other`, `35_natveg/pot_forest_may24/equations.gms:166` | bare-name repo grep: only equation-level ref is line 166; other refs are decl:18 + presolve populate/clamp. Positive control passed (grep found known sites, exit 0). `im_` param has no `.l/.lo` forms to miss. | ✅ |
| youngsecdf term repointed FROM `im_growing_stock(...,"secdforest")` TO `im_growing_stock_ysf` | commit 6b00f9dea diff on equations.gms:166 shows exactly this one-line change | ✅ |
| Commit `6b00f9dea` "Fix youngsecdf wood production: use uncalibrated growing stock" | git show 6b00f9dea | ✅ |
| Commit message quote ("evade land-CO2 caps/prices by relocating wood harvest onto youngsecdf, booking almost no carbon…") | faithful to actual commit message | ✅ |
| `youngsecdf` NOT a member of `land_timber` = `/forestry, primforest, secdforest, other/` → needed standalone (t,j,ac) param | `core/sets.gms:257`; youngsecdf not in `land` set at all | ✅ |
| Carbon side: `p35_carbon_density_other(...,"youngsecdf",...) = pm_carbon_density_secdforest_ac_uncalib` | `35_natveg/pot_forest_may24/presolve.gms:242` | ✅ (cited 241-242; range contains correct line 242) |
| Producer of uncalibrated curve in M52 normal_dec17 | declared `52_carbon/normal_dec17/declarations.gms`, snapshot in `start.gms` | ✅ |
| **REGIONAL direction caveat** — FRA calib raises k in some regions, lowers in others; "not a safe global claim"; zero-clamp interaction | M52 `input.gms:47`: "FRA NRF growing stock is below LPJmL potential **in most regions**" — the exact grounding | ✅ CRITICAL REQ MET |
| Date nuance: commit is 2026-07-01, "2026-07-14" is doc-sync date | git author+committer date = 2026-07-01 09:07:26; answer correct, MORE precise than GT summary | ✅ |
| April carbon-switch commit `c7731e234` (2026-04-20) | exists: "Natural-origin tracking for secondary forest carbon density", touched M35 presolve/equations + M52 | ✅ |

## Bugs Found
**None.** No Critical, Major, Minor, or scoreable Informational.

## Notes on non-bugs considered
- **presolve.gms:241-242 carbon-side citation**: youngsecdf carbon assignment is a single line (242); range 241-242 contains it. Not off ("off-by-few where adjacent lines similar" doesn't fire — 242 is in range). No deduction.
- **🟡 Documented tags on code-verifiable facts**: answer declared docs-only mode and honestly tagged 🟡; facts nonetheless 100% correct vs code. Honest calibration, not conservative-tag Informational. No deduction.
- **"Adjacent open leads" (A/B)**: explicitly labeled unverified/not-asserted; lead A (secdforest-proper mismatch, calib prod vs natural-origin-blend carbon) is plausible given presolve.gms:251 blend. Not scoreable.

## Mechanical checks
M1 ✅ (many file:line) · M2 ✅ (managementcalib_aug19, pot_forest_may24 — correct realizations) · M3 ✅ (all prefixes valid) · M4 ✅ (🟡/⚠️) · M5 ✅ (docs-only → 🟡, honest) · M6 ✅ (source-docs footer)

## Summary
Textbook anchor answer. Every load-bearing ground-truth element matches code exactly: parameter name, declaration/population/clamp lines, sole consumer, derivation curve, and the pre/post-fix repointing. The CRITICAL non-universal-direction requirement is not merely met but grounded in the exact M52 code comment ("in most regions"). The answer is MORE precise than the ground-truth summary on dating (correctly separates the Jul-1 commit from the Jul-14 doc-sync). No drift; nothing near the anchor broke.
