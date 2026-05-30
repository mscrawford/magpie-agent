# Round 35 Doc Audit — module_22.md (Land Conservation)

**Target doc**: `magpie-agent/modules/module_22.md` (1597 lines)
**Ground truth**: `/tmp/magpie_develop_ro` develop worktree, `area_based_apr22` realization.
**Auditor**: Opus adversarial doc auditor.
**Date**: 2026-05-30.

---

## Setup verification (all confirmed)

- **Realization**: Only `area_based_apr22` exists (`ls /tmp/magpie_develop_ro/modules/22_land_conservation/` → `area_based_apr22`, `input`, `module.gms`). Doc's realization name is correct.
- **Default config key**: `cfg$gms$land_conservation <- "area_based_apr22"` (config/default.cfg:714). The doc never states the config key but the realization is right. (Note: the key is `land_conservation`, not the doc-implied module-number form — not a doc bug, just recorded.)
- **No equations**: `realization.gms:33-39` shows phases sets/declarations/input/preloop/presolve_ini only. Doc's "no equations, runs in preloop + presolve_ini" is CORRECT.
- **Country count**: `policy_countries22` has 249 ISO codes (`sed -n '24,48p' input.gms | grep -o '[A-Z][A-Z][A-Z]' | wc -l` → 249). Doc's "all 249 countries" CORRECT.
- **s22_base_protect_reversal default = Inf**: input.gms:17 `/ Inf /`. Doc CORRECT.
- **s22_restore_land default = 1**: input.gms:14 `/ 1 /`. Doc CORRECT.
- **base22 set = {none, WDPA, WDPA_I-II-III, WDPA_IV-V-VI}**: sets.gms:10-11. Doc CORRECT.
- **land_consv set = {primforest, secdforest, other}**: input.gms:51-52. Doc CORRECT (future conservation 3 types, baseline all 4).
- **consv_type = {protect, restore}**: sets.gms:26-27. Doc CORRECT.
- **presolve_ini.gms code citations** (IFL primforest 16-17, baseline 20-26, additional 28-44, protect 47-55, restoration 58-118, no-restore 113-118, reversal 120-122): all verified against the file. CORRECT.

---

## CONSUMER/PRODUCER SET RE-DERIVATION (the load-bearing finding)

### Actual direct consumers of `pm_land_conservation` (grep, two methods, cross-checked)

`rg -n 'pm_land_conservation' /tmp/magpie_develop_ro/modules/ -g '*.gms'` (minus module 22 itself, minus declarations):

| Module | Realization (default?) | File:line | How it reads |
|--------|------------------------|-----------|--------------|
| **M29 cropland** | detail_apr24 (DEFAULT), simple_apr24 | equations.gms:52 (detail), :41 (simple) | `q29_land_snv`: `+ sum((ct,land_snv,consv_type), pm_land_conservation(ct,j2,land_snv,consv_type))` |
| **M31 past** | endo_jun13 (DEFAULT) | presolve.gms:9 | `vm_land.lo(j,"past") = sum(consv_type, pm_land_conservation(t,j,"past",consv_type))` |
| **M32 forestry** | dynamic_may24 (DEFAULT) | presolve.gms:20, 214-216 | reads `pm_land_conservation(t,j,"other","restore")`; reads + REWRITES `(...,"secdforest","restore")` |
| **M35 natveg** | pot_forest_may24 (DEFAULT) | equations.gms:22; presolve.gms:149,162,174,177,179,186,189,197-201,221,225,228-231 | `q35_natveg_conservation` reads `(...,land_natveg,"protect")`; presolve reads + REWRITES |
| **M13 tc** | endo_jan22 (DEFAULT), exo | presolve.gms:40 (endo), :16 (exo) | `p13_cropland_consv_shr(t,j) = sum(consv_type, pm_land_conservation(t,j,"crop",consv_type))/pcm_land(j,"crop")` |

All five consumer realizations are DEFAULT (verified each `cfg$gms$...` in default.cfg: cropland 795, past 969, forestry 976, natveg 1135, tc 293).

**Actual direct consumer set = {M13, M29, M31, M32, M35}.**

### Module 10 is NOT a direct consumer (highest-risk claim — confirmed twice + positive control)

- `rg -n 'pm_land_conservation' /tmp/magpie_develop_ro/modules/10_land/` → no match (exit 1).
- `grep -rn 'pm_land_conservation' /tmp/magpie_develop_ro/modules/10_land/` → no match (exit 1).
- Positive control: `rg -lc 'vm_land' /tmp/magpie_develop_ro/modules/10_land/` → many hits (postsolve, declarations, scaling, equations, start, presolve). Grep works in that dir; `pm_land_conservation` is genuinely absent.

**Mechanism (MANDATE 17)**: consumers M29/M31/M32/M35 set `vm_land.lo(...)` bounds and add to `=g=` constraints. Module 10's `vm_land` must then satisfy those bounds, but Module 10 never references `pm_land_conservation`. **M10 is a TRANSITIVE/downstream beneficiary, not a direct consumer** — exactly the R24 Q4-B3 / MANDATE 17 pattern, and the R20 wrong-consumer-set anchor.

### Doc's consumer claims vs reality

- Doc §5 "PROVIDES TO (3 modules)": **Module 10 (PRIMARY CONSUMER), Module 35 (SECONDARY), Module 31 (TERTIARY)** (lines 509-528). → M10 phantom; M29, M32, M13 omitted.
- Doc §5.1 "Provides To (5-7 modules)": lists M10 #1, M31, M35, M32, "Plus 2-3 other" (lines 579-584). → M10 phantom; M29 + M13 unnamed.
- Doc Summary (line 1312) + §3 header: "Used by: Module 10 (Land), Module 35 (NatVeg), Module 31 (Pasture)" → same M10 phantom + omissions.

---

## ADVISORY-CHECKER CROSS-LEAD (refuted)

Pre-run advisory: "module_35 reportedly lists M22 as consumer of vm_land_other / v35_secdforest — does M22 read/constrain vm_land_other?"

**REFUTED**: M22 reads neither.
- `rg 'vm_land_other'` (with `(`, with `.`, and bare) in module 22 → NONE AT ALL (three variants).
- `rg 'v35_secdforest'` in module 22 → NONE.
- Full enumeration of vm_/v-vars M22 reads (`rg -o 'v[m0-9]+_[a-z_]+' area_based_apr22/*.gms | sort -u`): only `vm_land`, `vm_treecover`, and local `v22_all`.

The relationship is the reverse: **M35 reads/writes `pm_land_conservation` (M22's output)**; M22 does not read M35 variables. The doc correctly lists M35 as a consumer. No bug from this cross-lead; the lead is a producer/consumer-direction confusion that the doc does NOT make.

---

## Bugs found

### 22-B1 — Module 10 falsely claimed as direct (and primary) consumer of `pm_land_conservation`
- **Severity**: Critical. **Class**: 15 (latent doc error) / MANDATE 17 (transitive-vs-direct). **Trigger**: R20 anchor "doc said wrong consumer set" + R24 Q4-B3 MANDATE-17 pattern.
- **Doc quote** (line 511): "**1. Module 10 (Land)** - **PRIMARY CONSUMER**: Variable provided: `pm_land_conservation(t,j,land,consv_type)`". Also lines 580, 724, 1312, 1338, 1404.
- **Reality**: `pm_land_conservation` has ZERO references in `modules/10_land/`. M10 receives the constraint only transitively via `vm_land.lo` bounds set by M29/M31/M32/M35.
- **File evidence**: `rg`/`grep -rn 'pm_land_conservation' /tmp/magpie_develop_ro/modules/10_land/` → no match (positive control `vm_land` present). Direct consumers at modules/31_past/endo_jun13/presolve.gms:9; modules/29_cropland/detail_apr24/equations.gms:52; modules/35_natveg/pot_forest_may24/equations.gms:22; modules/32_forestry/dynamic_may24/presolve.gms:20.
- **verify_cmd**: `rg -n 'pm_land_conservation' /tmp/magpie_develop_ro/modules/10_land/ ; echo exit $?` → exit 1 (no match); positive control `rg -lc 'vm_land' .../10_land/` → 6 files.
- **Confirmed**: true.
- **Proposed fix**: Remove Module 10 from the direct-consumer list. Replace §5 "PROVIDES TO" block so the direct consumers are **M29 (cropland), M31 (pasture), M32 (forestry), M35 (natveg), M13 (tc)**, and add a MANDATE-17 note: "Module 10 (Land) does NOT directly read `pm_land_conservation`; it is constrained transitively — M29/M31/M32/M35 translate the parameter into `vm_land.lo` bounds and `=g=` constraints that Module 10's `vm_land` must satisfy."

### 22-B2 — Direct consumers M29 (cropland) and M13 (tc) omitted from dependency lists
- **Severity**: Critical. **Class**: 15 (latent doc error). **Trigger**: R20 wrong-consumer-set anchor (omissions in a refactor-relevant set).
- **Doc quote** (lines 509-528, 579-584): consumer list = {M10, M35, M31} (+ "2-3 other modules"); M29 and M13 are never named.
- **Reality**: M29 reads it in `q29_land_snv` (semi-natural vegetation constraint, DEFAULT detail_apr24); M13 reads `pm_land_conservation(t,j,"crop",consv_type)` to compute cropland-in-conservation share (DEFAULT endo_jan22). Both default realizations.
- **File evidence**: `modules/29_cropland/detail_apr24/equations.gms:52`; `modules/13_tc/endo_jan22/presolve.gms:40`.
- **verify_cmd**: `rg -n 'pm_land_conservation' /tmp/magpie_develop_ro/modules/ -g '*.gms' | grep -v 22_land_conservation | grep -v declarations` → shows 29, 31, 32, 35, 13 (not 10).
- **Confirmed**: true.
- **Proposed fix**: Add M29 and M13 to the consumer list with their roles (M29: `q29_land_snv` semi-natural-veg cropland constraint; M13: `p13_cropland_consv_shr` TC adjustment for cropland inside conservation areas). Fold into the 22-B1 rewrite.

### 22-B3 — `vm_treecover` attributed to Module 32 (Forestry); it is a Module 29 (cropland) variable
- **Severity**: Major. **Class**: 6/Module-characterization (MANDATE 6/9 wrong-module attribution). **Trigger**: "Wrong variable prefix/scope" → here wrong producing module for an interface var the doc explicitly sources.
- **Doc quote** (line 504): "**Module 32 (Forestry)**: `vm_treecover.l(j)` - tree cover area (mio. ha)". Also line 234 "Tree cover (from Module 32)".
- **Reality**: `vm_treecover(j)` "Cropland tree cover" is declared in **Module 29** (`detail_apr24/declarations.gms:39`, `simple_apr24/declarations.gms:23`) and populated by `q29_treecover` (`detail_apr24/equations.gms:84`). Module 32 has ZERO references to `vm_treecover`.
- **File evidence**: `modules/29_cropland/detail_apr24/declarations.gms:39`; `modules/29_cropland/detail_apr24/equations.gms:84`. `rg 'vm_treecover' modules/32_forestry/` → NONE.
- **verify_cmd**: `rg -n 'vm_treecover' /tmp/magpie_develop_ro/modules/*/*/declarations.gms` → only 29_cropland (detail + simple); `rg -n 'vm_treecover' .../modules/32_forestry/` → no match.
- **Confirmed**: true.
- **Proposed fix**: Change both occurrences from "Module 32 (Forestry)" to "Module 29 (Cropland)"; describe as "cropland tree cover (agroforestry), declared/populated in Module 29". Line 234 "Tree cover (from Module 32)" → "Cropland tree cover (from Module 29)".

### 22-B4 — `fm_land_iso` attributed to Module 09 (Drivers); it is a Module 10 (Land) input table
- **Severity**: Major. **Class**: 6/Module-characterization (wrong-module attribution). **Trigger**: wrong module attribution for a named interface parameter.
- **Doc quote** (line 483): "**Source**: `fm_land_iso` from Module 09 (Drivers)". Also line 505 "Module 09 (Drivers): `fm_land_iso(t,iso,land)`", and line 587 "Depends On (1 module): Module 09 (Drivers) - Population and scenario data".
- **Reality**: `fm_land_iso(t_ini10,iso,land)` "Land area for different land pools at ISO level" is declared in **Module 10** (`landmatrix_dec18/input.gms:25`). It is referenced only there and in module 22's preloop. Module 09 declares no `fm_land_iso` (positive control: M09 input.gms declares `fm_gdp_defl_ppp`). It is land area, not "population/scenario data".
- **File evidence**: `modules/10_land/landmatrix_dec18/input.gms:25`; `modules/22_land_conservation/area_based_apr22/preloop.gms:20`.
- **verify_cmd**: `grep -rln 'fm_land_iso' /tmp/magpie_develop_ro/modules/` → only `10_land/.../input.gms` and `22_.../preloop.gms`; `grep -rn 'fm_land_iso' .../09_drivers/` → no match; positive control `grep -rhno 'fm_[a-z_]*' .../09_drivers/aug17/input.gms` → `fm_gdp_defl_ppp`.
- **Confirmed**: true.
- **Proposed fix**: Change "Module 09 (Drivers)" → "Module 10 (Land)" at lines 483, 505, 587; fix the §5.1 "Depends On" description from "Population and scenario data" to "ISO-level land area (`fm_land_iso`)". Note: M22's true single external dependency is Module 10 (`pcm_land`, `vm_land.lo`, `fm_land_iso`) plus `vm_treecover` from M29 — so the "Depends On (1 module): Module 09" line is doubly wrong.

### 22-B5 — `realization.gms:8-24` header citation drift (quoted block is lines 10-18)
- **Severity**: Minor. **Class**: 10 (file:line citation drift, adjacent/same content). **Trigger**: off-by-few citation where adjacent lines say similar things.
- **Doc quote** (line 41): "**From Module Header** (`realization.gms:8-24`):" followed by a block beginning "Land reserved for area-based conservation is derived from WDPA and @wang_over_2024 ... grassland ('past') within protected areas cannot be converted to other land types."
- **Reality**: That quoted text is `realization.gms:10-18`. Line 8 is `*' @description The realization initialises land stocks...` (not quoted); lines 19-24 are the BH/IFL/CBD/LW continuation (not quoted). The cited range 8-24 brackets but does not match the quoted lines.
- **File evidence**: `modules/22_land_conservation/area_based_apr22/realization.gms:10-18`.
- **verify_cmd**: Read realization.gms:8-24 — quoted sentence spans lines 10-18.
- **Confirmed**: true.
- **Proposed fix**: Change citation to `realization.gms:10-18` (the lines actually quoted).

---

## Claims verified correct (not bugs)

- `pm_land_conservation` DECLARED in M22 `declarations.gms:15`; M35/M32 also WRITE to it in presolve (legitimate populate-then-consume) — doc treats it as M22's output, correct.
- DEPENDS-ON Module 10 for `pcm_land` (declarations.gms:11) and `vm_land.lo(j,"crop")` (declarations.gms:19): correct.
- Restoration-potential translations (subtract urban, `land_timber`, protected pasture, `vm_land.lo(j,"crop")`, `vm_treecover.l`): faithful to presolve_ini.gms:82-111. `land_timber`/`land_natveg` are core sets (core/sets.gms:256,262).
- Restoration priority order secdforest → past → other: matches presolve_ini.gms:82-111 sequencing.
- Country-weight logic, `p22_country_switch` "from `policy_countries22` set": preloop.gms:15-21. Correct.
- consv22_all / consv_prio22 / wdpa_cat22 set members: sets.gms:16-24. Doc's scenario lists match.
- All input.gms switch line citations (8, 10, 14, 15-16, 17, 23-48, 51, 57): verified against file.
- WDPA header numbers 954.9 / 1855.7 Mha, 14.3%: realization.gms:12-13. Correct.
- m_fillmissingyears in input.gms (doc says :57): the call is at input.gms:63; the table+include block is 57-63. Doc §2A says "input.gms:57" for fillmissingyears — slightly off (actual line 63) but within the cited table block; not flagged (within the 57-63 block the doc elsewhere cites).

---

## Deferred (not code-verifiable; NOT edited)

- "30by30 scenario restores 3,094 Mha globally by 2030" (line 556) and "30by30 with 3,094 Mha restoration" (line 660): depends on `.cs3` input data + a model run; cannot verify from code.
- All approximate per-land-type coverage figures (forest ~400-500 Mha, grassland ~200-300, etc., lines 414-419) and per-scenario "% of land" estimates (IrrC bands, BH ~2-3%, etc.): input-data dependent, not in code.
- Literature attributions (Myers 2000, Potapov 2008/2017, Dinerstein 2020, Brooks 2006, CBD 2022) and IUCN-category descriptions: not code claims.
- "Protected forests store ~200-300 GtC", "Centrality Rank ~25 of 46": external/estimative, not code-checkable.
- `sm_fix_SSP2` numeric value: defined in Module 09 (`09_drivers/aug17/input.gms`) + config; doc uses it only as a gate and asserts no number, so nothing to flag.
- §2B doc GAMS snippet (lines 100-112) omits the intermediate `p22_conservation_area(t,j,land) = sum(...)` statement at code lines 31-34 inside the `else` branch, and has a stray trailing `)`. This is a reproduction abbreviation, not a code-fact error; citation range 28-44 is correct. Noted, not flagged as a bug.

---

## Summary

5 bugs. Two Critical (consumer-set): Module 10 is falsely the "primary" direct consumer of `pm_land_conservation` (it is transitive only — MANDATE 17 / R20 anchor), and the real direct consumers M29 + M13 are omitted (actual direct set = M13, M29, M31, M32, M35; M31/M32/M35 correctly listed). Two Major wrong-module attributions: `vm_treecover` is Module 29 (cropland), not 32; `fm_land_iso` is Module 10 (land), not 09 (drivers) — which also makes the "Depends On: Module 09" line wrong. One Minor header-citation drift (8-24 → 10-18). The advisory cross-lead (M22 reads vm_land_other/v35_secdforest) is REFUTED: M22 reads neither; M35 is correctly a consumer of M22's output.
