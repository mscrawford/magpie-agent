# Round 35 Adversarial Verification - module_22.md

Verifier: Opus 4.8 (1M). Ground truth: /tmp/magpie_develop_ro (develop worktree).
Default realizations confirmed from config/default.cfg:
- land_conservation = area_based_apr22 (L714)
- cropland = detail_apr24 (L795)
- tc = endo_jan22 (L293)
- past = endo_jun13 (L969)
- forestry = dynamic_may24 (L976)
- natveg = pot_forest_may24 (L1135)
- land = landmatrix_dec18 (L232)

All five cited consumers are DEFAULT realizations. No non-default trap.

---

## Master grep: producer + all consumers of pm_land_conservation

`rg -n 'pm_land_conservation\(' /tmp/magpie_develop_ro/modules/`
`rg -n 'pm_land_conservation\.' /tmp/magpie_develop_ro/modules/`  -> NO-MATCH (no `.l/.lo` attribute reads; only the `(...)` form is used)

Producer (sets the parameter): module 22 area_based_apr22/presolve_ini.gms:54-121, declarations.gms:15.

Consumers / writers-back found (excluding M22 self):
- 29_cropland/detail_apr24/equations.gms:52  (DEFAULT) - reads sum over consv_type into q29_land_snv
- 29_cropland/simple_apr24/equations.gms:41  (non-default sibling, same read)
- 35_natveg/pot_forest_may24/equations.gms:22 (DEFAULT) - reads "protect"; presolve.gms:149-231 reads AND writes back restore/protect, sets vm_land.lo
- 13_tc/endo_jan22/presolve.gms:40 (DEFAULT) - p13_cropland_consv_shr reads sum over consv_type
- 13_tc/exo/presolve.gms:16 (non-default sibling, same read)
- 32_forestry/dynamic_may24/presolve.gms:20,214-216 (DEFAULT) - reads "other"/"secdforest" restore, writes back secdforest restore
- 31_past/endo_jun13/presolve.gms:9 (DEFAULT) - vm_land.lo(j,"past") = sum(consv_type, pm_land_conservation(...))

=> True DIRECT consumer set = {M13, M29, M31, M32, M35}. M10 absent.

---

## 22-B1  M10 is NOT a direct consumer (phantom) -- VERDICT: UPHELD

class_is_consumer_set = TRUE (direct-vs-transitive consumer claim, MANDATE 17).

Phantom check (confirm twice + positive control):
- `rg -n 'pm_land_conservation' /tmp/magpie_develop_ro/modules/10_land/`  -> NO-MATCH (both `(` and `.` forms covered by bare-name search; empty)
- POSITIVE CONTROL `rg -n 'pcm_land' /tmp/magpie_develop_ro/modules/10_land/` -> 5 hits (postsolve.gms:9, declarations.gms:11, equations.gms:15,25, start.gms:11). Search works in M10; absence of pm_land_conservation is real, not a broken probe.

M10 is a transitive beneficiary: M29/M31/M35 translate pm_land_conservation into vm_land.lo bounds (e.g. 31_past/endo_jun13/presolve.gms:9; 35_natveg/pot_forest_may24/presolve.gms:162,201,231) and M29 q29_land_snv (equations.gms:52) constrains vm_land(crop). M10's own vm_land must satisfy those bounds/constraints but M10 never reads the parameter. Auditor's correction is exactly right.

Auditor's direct-consumer replacement {M29,M31,M32,M35,M13} reproduces my independent set. UPHELD.

---

## 22-B2  Omitted direct consumers M29 + M13 -- VERDICT: UPHELD

class_is_consumer_set = TRUE (omitted-member claim).

- M29 (cropland, DEFAULT detail_apr24): equations.gms:52, q29_land_snv semi-natural-vegetation constraint reads `sum((ct,land_snv,consv_type), pm_land_conservation(ct,j2,land_snv,consv_type))`. Genuine direct read. The doc's PROVIDES TO list (lines 509-528, 579-584) never names M29.
- M13 (tc, DEFAULT endo_jan22): presolve.gms:40, p13_cropland_consv_shr reads `sum(consv_type, pm_land_conservation(t,j,"crop",consv_type))/pcm_land(j,"crop")`. Genuine direct read. Never named in doc.

Both confirmed against the master grep above. The true direct set {M13,M29,M31,M32,M35} matches the auditor's claim. UPHELD.

---

## 22-B3  vm_treecover declared in M29 not M32 -- VERDICT: UPHELD (with scope note for fixer)

class_is_consumer_set = TRUE (wrong producer/source attribution for an interface variable).

Producer search:
- `rg -ln 'vm_treecover' /tmp/magpie_develop_ro/modules/` -> 29_cropland (detail_apr24 + simple_apr24), 59_som, 22_land_conservation. NO 32_forestry.
- Declaration: 29_cropland/detail_apr24/declarations.gms:39 ` vm_treecover(j)  Cropland tree cover (mio. ha)`; populated by q29_treecover at equations.gms:84 `vm_treecover(j2) =e= sum(ac, v29_treecover(j2,ac))`. simple_apr24/declarations.gms:23 fixes it to 0.

M32 phantom check (confirm twice + positive control):
- `rg -n 'vm_treecover' /tmp/magpie_develop_ro/modules/32_forestry/` -> NO-MATCH (covers both `(` and `.` forms).
- POSITIVE CONTROL `rg -ln 'vm_land' /tmp/magpie_develop_ro/modules/32_forestry/` -> dynamic_may24 postsolve/declarations/equations etc. Search works in M32; absence is real.

Scope note for fixer: the doc line (504) sits in M22's "Depends On / Additional Dependencies (indirect)" block. M22 itself reads `vm_treecover.l(j)` (presolve_ini.gms:87,98,109) to deduct cropland tree cover from restoration potential. So the precise correction is: vm_treecover is sourced from **Module 29 (Cropland)** -- "Cropland tree cover (agroforestry), declared and populated in M29 q29_treecover" -- NOT Module 32. Auditor's M32->M29 fix is correct.

---

## 22-B4  fm_land_iso declared in M10 not M09 -- VERDICT: UPHELD

class_is_consumer_set = TRUE (wrong source/dependency attribution for an interface parameter).

- `rg -n 'fm_land_iso' /tmp/magpie_develop_ro/modules/` -> exactly 2 hits: 10_land/landmatrix_dec18/input.gms:25 `table fm_land_iso(t_ini10,iso,land) Land area for different land pools at ISO level (mio. ha)` (declaration) and 22_land_conservation/area_based_apr22/preloop.gms:20 (the consumer). No third site.
- M09 phantom check: `rg -n 'fm_land_iso' /tmp/magpie_develop_ro/modules/09_drivers/` -> NO-MATCH. POSITIVE CONTROL `rg -ln 'fm_' /tmp/magpie_develop_ro/modules/09_drivers/` -> aug17/input.gms, input/files present. Search works in M09; M09 does not declare fm_land_iso.

It is ISO-level land area from M10, not population/scenario data from M09. M22's sole external GAMS-parameter source here is M10. Auditor's M09->M10 fix + description fix ("ISO-level land area (fm_land_iso)") is correct. UPHELD.

Caveat (out of scope, do not act on without separate check): the upstream R/preprocessing origin of the land-area input is a different layer; this verdict concerns the GAMS declaring module only.

---

## 22-B5  Citation drift realization.gms:8-24 -> 10-18 -- VERDICT: NOT_CONSUMER_SET

class_is_consumer_set = FALSE. This is a file:line citation-accuracy finding (Check-10 / citation-drift class), not a consumer/producer/dependency-set claim. Passes to the fixer unchanged; no consumer-set effort spent.

FYI only (not a verification of this class): `sed -n '8,24p' realization.gms` shows line 8 = `*' @description The realization initialises...`, the quoted WDPA sentence begins at line 10 ("Land reserved for area-based conservation is derived from WDPA...") and the doc's quoted text ends at line 18 ("...cannot be converted to other land types."); lines 19-24 are the BH/CBD/IFL/LW continuation. Consistent with auditor, but adjudication of citation drift is outside this verifier's mandate.

---

## Summary

| Bug | class_is_consumer_set | Verdict |
|-----|----------------------|---------|
| 22-B1 | true  | UPHELD |
| 22-B2 | true  | UPHELD |
| 22-B3 | true  | UPHELD (M29 source; note M22 itself reads vm_treecover.l) |
| 22-B4 | true  | UPHELD |
| 22-B5 | false | NOT_CONSUMER_SET |

No refutations. All four consumer-set findings reproduce independently with both grep forms + positive controls. No phantom-deletion risk (M10 truly absent; M32 truly absent for vm_treecover; M09 truly absent for fm_land_iso) and no over-deletion (the omitted M29/M13 are genuine default-realization direct reads).
