# R54 Adversarial Verification - module_35.md

**Target doc**: `<magpie-agent>/modules/module_35.md` (1198 lines)
**Ground truth**: `/tmp/magpie_develop_ro` @ `0d7ebeb90` (read-only develop worktree; working tree NEVER consulted)
**Verifier**: adversarial, mechanical-only (test -f / wc -l / read the exact line / isolated rg + positive control)
**Date**: 2026-07-14

## Headline

**All 9 confirmed bugs SURVIVE.** 0 CITATION_FAILED, 0 REFUTED, 0 CORRECTED.

Every cited file exists, every cited line is in range, and every cited line contains the claimed token. The two highest-risk claims (B1 data-flow direction, B8 "the satellite path is the default") were independently re-derived from **both endpoints** plus the config/R layer, not from a single-file read.

A clean sweep is itself a reason for suspicion, so it is worth naming why this one holds: the auditor self-flagged tier uncertainty on B4/B8, explicitly told the fixer *not* to touch doc:62, and cited the doc's own self-contradictions (doc:578 vs doc:881; doc:134 vs doc:925; doc:127 vs doc:126) rather than asserting from recall. That is calibrated-auditor behaviour, and it reproduced under mechanical check.

Module 35 has exactly **one** realization (`pot_forest_may24`), so the R33 cross-realization confabulation class cannot fire on the M35 side. It *could* have fired on the cited **sibling** modules (M29 has 2 realizations, M59 has 2) - and B4 is precisely a catch of that, in the doc rather than in the auditor.

## Verdict table

| ID | Severity | Class | citation_ok | Verdict |
|----|----------|-------|-------------|---------|
| M35-B1 | Critical | producer_declaration | ✅ | **UPHELD** |
| M35-B2 | Major | other (count) | ✅ | NOT_REVIEWABLE (citation OK, claim independently confirmed) |
| M35-B3 | Major | other (set count) | ✅ | NOT_REVIEWABLE (citation OK, claim independently confirmed) |
| M35-B4 | Minor | consumer_set | ✅ | **UPHELD** |
| M35-B5 | Minor | consumer_set | ✅ | **UPHELD** |
| M35-B6 | Minor | other (pseudo-code) | ✅ | NOT_REVIEWABLE (citation OK, claim independently confirmed) |
| M35-B7 | Minor | realization_structure | ✅ | **UPHELD** |
| M35-B8 | Minor | other (stale-source) | ✅ | NOT_REVIEWABLE (citation OK, producer chain re-derived) |
| M35-B9 | Minor | producer_declaration | ✅ | **UPHELD** |

`NOT_REVIEWABLE` follows the protocol for class=`other` (citation validated in Step A, pass to fixer unchanged). It is **not** a doubt signal here: in each case I additionally re-derived the substance and the fix text is accurate. Apply all nine.

---

## STEP A - Mechanical citation check (all 20 cited files)

```
$ for f in ...; do test -f "$R/$f" && wc -l < "$R/$f"; done
EXISTS      52  modules/10_land/landmatrix_dec18/declarations.gms
EXISTS      54  modules/10_land/landmatrix_dec18/equations.gms
EXISTS     233  modules/35_natveg/pot_forest_may24/equations.gms
EXISTS      66  modules/35_natveg/pot_forest_may24/input.gms
EXISTS     294  modules/35_natveg/pot_forest_may24/presolve.gms
EXISTS     107  modules/35_natveg/pot_forest_may24/preloop.gms
EXISTS     143  modules/35_natveg/pot_forest_may24/declarations.gms
EXISTS      47  modules/35_natveg/pot_forest_may24/realization.gms
EXISTS     210  modules/35_natveg/pot_forest_may24/postsolve.gms
EXISTS      35  modules/35_natveg/pot_forest_may24/scaling.gms
EXISTS      30  modules/35_natveg/pot_forest_may24/sets.gms
EXISTS     362  core/sets.gms
EXISTS    2443  config/default.cfg
EXISTS     123  modules/29_cropland/detail_apr24/equations.gms
EXISTS      49  modules/29_cropland/simple_apr24/equations.gms
EXISTS     102  modules/59_som/cellpool_jan23/equations.gms
EXISTS      81  modules/14_yields/managementcalib_aug19/presolve.gms
EXISTS      37  modules/52_carbon/normal_dec17/declarations.gms
EXISTS      51  modules/52_carbon/normal_dec17/start.gms
EXISTS     118  modules/52_carbon/normal_dec17/preloop.gms
```

All exist; every cited line number is in range (tightest: `simple_apr24/equations.gms:49` in a 49-line file - in range, last line; `landmatrix_dec18/equations.gms:53` in a 54-line file - in range).

**Default-realization confirmations** (config/default.cfg, mechanically read):

| line | content | relevance |
|------|---------|-----------|
| 232 | `cfg$gms$land <- "landmatrix_dec18"` | validates B1/B9 M10 citations are on the default path |
| 354 | `cfg$gms$yields <- "managementcalib_aug19"` | validates B5 M14 citation |
| 802 | `cfg$gms$ageclass <- "oct24"` | validates B8 producer chain |
| 811 | `cfg$gms$cropland <- "detail_apr24"` | **B4: detail_apr24 IS default, simple_apr24 is NOT** |
| 1574 | `cfg$gms$carbon <- "normal_dec17"` | validates B5 M52 citations |
| 1934 | `cfg$gms$som <- "cellpool_jan23"` | validates B4 M59 citation |

---

## M35-B1 - UPHELD (Critical) - producer_declaration / inverted direction

**Claim**: doc:881 lists `vm_landexpansion` under "10.1 Provides To -> To Module 10". Direction is inverted: M10 produces it, M35 only reads it.

### Citation check
- `modules/10_land/landmatrix_dec18/declarations.gms:20` -> ` vm_landexpansion(j,land)                    Land expansion (mio. ha)` (inside `positive variables`) ✅
- `modules/10_land/landmatrix_dec18/equations.gms:30-33` ->
  ```
  30:  q10_landexpansion(j2,land_to) ..
  31:         vm_landexpansion(j2,land_to) =e=
  32:         sum(land_from$(not sameas(land_from,land_to)),
  33:         vm_lu_transitions(j2,land_from,land_to));
  ```
  Single variable on the LHS of `=e=` -> this is the **defining** equation. ✅
- `modules/35_natveg/pot_forest_may24/equations.gms:197` -> `                sum(land_forest, vm_landexpansion(j2,land_forest))` (inside `q35_max_forest_establishment(j2)..`, opened at :196, followed by `=l=` at :198) ✅
- `modules/35_natveg/pot_forest_may24/equations.gms:222` -> `                 + vm_landexpansion(j2,"other")` (RHS term inside `q35_other_regeneration(j2)..`, opened at :218) ✅

### Independent re-derivation (both grep forms + positive controls)

**DECLARED** - sweep of every `declarations.gms` in the model:
```
$ rg -n 'vm_landexpansion' /tmp/magpie_develop_ro/modules/*/*/declarations.gms
modules/10_land/landmatrix_dec18/declarations.gms:20: vm_landexpansion(j,land)  ...
modules/32_forestry/dynamic_may24/declarations.gms:74: vm_landexpansion_forestry(j,type32)  ...   <- DIFFERENT variable (co-located name; not a match)
```
Sole declaration: **Module 10**.

**M35 negative confirmed twice + positive control**:
```
$ grep -c 'vm_landexpansion' .../35_natveg/pot_forest_may24/declarations.gms  -> 0
$ grep -c 'vm_land_other'    .../35_natveg/pot_forest_may24/declarations.gms  -> 1   (positive control: grep works on this file)
```

**Attribute/solution-level form** (the R33 near-miss guard - a `NAME(` grep alone would miss `.l/.lo/.fx`):
```
$ rg -n 'vm_landexpansion\.' modules/ core/ scripts/
modules/10_land/landmatrix_dec18/postsolve.gms:14,27,40,53   (.m .l .up .lo -> ov_ reporting)
modules/10_land/landmatrix_dec18/scaling.gms:9               (commented out)
```
Zero M35 hits. Positive controls proving the `.` grep works in that directory:
- `vm_landreduction.` (sibling in the same declaration block) -> 5 hits in M10 ✅
- `vm_land.` -> hits in `35_natveg/pot_forest_may24/presolve.gms:40,130,136,157` and `postsolve.gms:22` ✅

So M35 **never** writes `vm_landexpansion` in any form: no `=e=` LHS, no `.fx/.lo/.up/.l`, no declaration. Its only two touches are a read on the LHS of a `=l=` **constraint** (:197 - constrains, does not define) and a read on the RHS of an `=e=` (:222).

### Per-slice-ownership contrast (why deleting doc:881 is safe and does not orphan its neighbours)

The adjacent lines 879/880 are **correct**, which is exactly what makes 881 wrong:
- doc:879 `vm_land(j,land_natveg)`: `vm_land` is also declared in M10, but M35 **owns the natveg slices** - `equations.gms:9` comment ("The interface `vm_land` provides aggregated natveg land pools (`ac`) to other modules"), `q35_land_secdforest` at `:11` (`vm_land(j2,"secdforest") =e= ...`), `q35_land_other` at `:13` (`vm_land(j2,"other") =e= ...`), plus `.l/.lo` on primforest in presolve. Genuine per-slice production.
- doc:880 `vm_landdiff_natveg`: declared in M35 (`declarations.gms:79`), defined by `q35_landdiff` (`equations.gms:92`), consumed by M10 (`equations.gms:53`). Genuine production. (See B9.)
- doc:881 `vm_landexpansion`: **zero** M35 writes of any kind. Not production.

The doc contradicts itself, as the auditor said: doc:578 correctly reads "`vm_landexpansion(j,"other")` (land expansion from Module 10)". And doc:900-901 ("From Module 10") lists only `vm_lu_transitions`, omitting `vm_landexpansion` - same root error, second instance. **Both edits in the proposed fix are correct and both are needed.**

Fix text spot-check: ":197 in `q35_max_forest_establishment`" ✅, ":222 in `q35_other_regeneration`" ✅, domain `(j,land)` matches `declarations.gms:20` ✅.

---

## M35-B2 - citation OK, claim confirmed (Major) - other (count)

### Citation check
- `input.gms:27` -> `s35_forest_damage Damage simulation in forests (0=none 1=shifting agriculture 2= Damage from shifting agriculture is faded out by c35_forest_damage_end 4= f35_forest_shock scenario) / 2 /` ✅ (contains the identifier **and** the `/ 2 /` default)
- `presolve.gms:13,19,24,30` -> `if(s35_forest_damage=1,` / `=2,` / `=3,` / `=4,` ✅ all four exact

### Substance
Five modes (0-4); `=0` fires no branch. The doc's four-item list at :18 enumerates 0, 1, 3, 4 and **drops mode 2 - the default**. Self-contradiction confirmed against the doc's own text: doc:36 / :161 / :833 / :1156 all say "0-4", and doc:182 is literally headed "#### 4.3 Mode 2: Shifting Agriculture Fade-Out (DEFAULT)".

Every mode label in the proposed replacement was verified against code:
- 1 = shifting agriculture: `presolve.gms:14-15` uses `f35_forest_lost_share(i,"shifting_agriculture")` ✅
- 2 = faded out (DEFAULT): `presolve.gms:20-21`, same but `*(1 - p35_damage_fader(t))`; default `/ 2 /` ✅
- 3 = **combined (shifting agriculture + wildfire)**: `presolve.gms:25-26` sums over `combined_loss`, and `sets.gms:14-15` defines `combined_loss(driver_source) / shifting_agriculture,wildfire /` ✅
- 4 = generic shock scenarios: `presolve.gms:31-32` uses `f35_forest_shock(t,"%c35_shock_scenario%")` ✅

Note (not a bug in the doc): MAgPIE's own inline description at `input.gms:27` omits mode 3 and misnames the fade-out switch as `c35_forest_damage_end` (the real scalar is `s35_forest_damage_end`, `input.gms:28`). The doc must not inherit that omission.

The auditor's instruction to leave doc:62 alone is sound ("4 disturbance modes" = the 4 modes in which disturbance occurs, 1-4).

---

## M35-B3 - citation OK, claim confirmed (Major) - other (set count)

### Citation check
`core/sets.gms:269-275` contains the `ac` set literal ✅. Mechanical member count:
```
$ sed -n '269,275p' core/sets.gms | ... | grep -c '^ac'
62
ac0 ac5 ac10 ... ac295 ac300 acx
```
Exactly **62** members. doc:925's "age-classes 1-15" is wrong; doc:134 ("62 age classes") is right.

### Steelman considered and rejected
The only 15-member age-class object in the model is `ac_gfad` (`modules/28_ageclass/oct24/sets.gms:9-12`, members `class1..class15`, the raw GFAD input indexing). It is confined to Module 28 and never indexes secondary forest. doc:925's own sentence names `v35_secdforest(j,ac)` and `vm_land_other(j,othertype,ac)` - and `declarations.gms:77-78` confirms both carry `ac`, the 62-member set. "1-15" is wrong under every reading.

Fix text spot-check: "see Section 3" -> doc:131 is "### 3. Age-Class System" ✅.

---

## M35-B4 - UPHELD (Minor) - consumer_set / non-default realization cited

### Citation check
- `config/default.cfg:811` -> `cfg$gms$cropland    <- "detail_apr24"               # def = detail_apr24` ✅
- `config/default.cfg:1934` -> `cfg$gms$som <- "cellpool_jan23"    # def = cellpool_jan23` ✅
- `modules/29_cropland/detail_apr24/equations.gms:60` -> `    sum(land_snv, vm_lu_transitions(j2,"crop",land_snv)) =g= sum(ct, p29_snv_relocation(ct,j2));` ✅
- `modules/29_cropland/simple_apr24/equations.gms:49` (the doc's current citation) -> same statement ✅ true, but in the **non-default** realization

### Independent full re-derivation of the `vm_lu_transitions` consumer set
```
$ rg -n 'vm_lu_transitions\(' modules/ core/
10_land/landmatrix_dec18/declarations.gms:23      DECLARED (M10)
10_land/landmatrix_dec18/equations.gms:20,24,33,38  q10_transition_to/_from, q10_landexpansion, q10_landreduction
29_cropland/detail_apr24/equations.gms:60         <- DEFAULT consumer
29_cropland/simple_apr24/equations.gms:49         <- non-default consumer
59_som/cellpool_jan23/equations.gms:51            <- DEFAULT consumer
59_som/cellpool_jan23/equations.gms:73            <- DEFAULT consumer, OMITTED by the doc
35_natveg/pot_forest_may24/equations.gms:25,26,31  (M35 itself)

$ rg -n 'vm_lu_transitions\.' modules/ core/
35_natveg/pot_forest_may24/presolve.gms:58        vm_lu_transitions.l(j,"forestry","other")   <- solution-level read by M35
10_land/landmatrix_dec18/postsolve.gms:17,30,43,56 ; presolve.gms:13,16,17,20,21 (.fx/.up bounds)
```
Consumer set outside M10 is exactly {M29, M35, M59}. No module is missing and none is a phantom. The defect is purely that the doc points M29 at a file the default run does not compile, plus the `:73` omission for M59. `cellpool_jan23/equations.gms:51` and `:73` both read verbatim (`vm_lu_transitions(j2,land_from,land)` in `q59_som_target`; `vm_lu_transitions(j2,land_from,"crop")` in the `vm_nr_som` equation) ✅.

Proposed fix text is accurate as written.

---

## M35-B5 - UPHELD (Minor) - consumer_set / omitted consumer

### Citation check
- `modules/35_natveg/pot_forest_may24/presolve.gms:248` -> `p35_carbon_density_secdforest(t,j,ac,ag_pools) = pm_carbon_density_secdforest_ac(t,j,ac,ag_pools);` ✅
- `:250` -> `  pm_carbon_density_secdforest_ac(t,j,ac,ag_pools)` ✅
- `:251` -> `  - (pm_carbon_density_secdforest_ac(t,j,ac,ag_pools) - pm_carbon_density_secdforest_ac_uncalib(t,j,ac,ag_pools))` ✅ (both twins on this line; the calibrated token is genuinely present, not a substring artefact of the `_uncalib` name)
- `modules/14_yields/managementcalib_aug19/presolve.gms:44` -> `     pm_carbon_density_secdforest_ac(t,j,ac,"vegc")` ✅ (inside `im_growing_stock(t,j,ac,"secdforest") = ...`, opened at :42)

### Twin separation (the trap this bug lives in)
Anchored grep `pm_carbon_density_secdforest_ac\(` cannot match `pm_carbon_density_secdforest_ac_uncalib(` (the char after `_ac` is `_`, not `(`). Full set for the **calibrated** parameter:

| role | location |
|------|----------|
| DECLARED | `52_carbon/normal_dec17/declarations.gms:9` |
| POPULATED | `52_carbon/normal_dec17/start.gms:28` ("vegc"), `:31` ("litc"); overwritten by the FRA calibration at `normal_dec17/preloop.gms:71` |
| READ (own module) | `52_carbon/normal_dec17/start.gms:43` (snapshot into the `_uncalib` twin) |
| READ (external) | **M14** `managementcalib_aug19/presolve.gms:44` **and M35** `pot_forest_may24/presolve.gms:248, 250, 251` |

Attribute form: `rg 'pm_carbon_density_secdforest_ac\.'` -> zero hits (it is a parameter, no `.l`). Nothing hidden.

M52's own code comment corroborates the auditor's description of the M35 use: `presolve.gms:244-247` reads "Blended secdforest carbon density: weighted average of FRA-calibrated curve (existing/managed) and uncalibrated natveg curve (natural-origin from succession)." So `:248-251` is precisely "the FRA-calibrated leg of the blended `p35_carbon_density_secdforest`", as the fix says.

The asymmetry the auditor flagged is real: doc:127 (the `_uncalib` twin's bullet) **does** say "and Module 35 itself"; doc:126 does not. Cross-checked doc:127 against code - M14 `:66` ✅, M29 `detail_apr24/preloop.gms:46` ✅, M32 `dynamic_may24/presolve.gms:59` and `:68` ✅, M35 `presolve.gms:117`, `:242` ✅, M52 `declarations.gms:10` + `start.gms:43` ✅. (doc:127 additionally omits the `_uncalib` occurrence at M35 `presolve.gms:251`; out of scope, optional polish.)

---

## M35-B6 - citation OK, claim confirmed (Minor) - other (pseudo-code as code)

### Citation check
`modules/35_natveg/pot_forest_may24/presolve.gms:77-78` reads verbatim:
```
77: pc35_land_other(j,"othernat",ac_est) = pc35_land_other(j,"othernat",ac_est) - p35_forest_recovery_area(t,j,ac_est);
78: pc35_land_other(j,"youngsecdf",ac_est) = pc35_land_other(j,"youngsecdf",ac_est) + p35_forest_recovery_area(t,j,ac_est);
```
✅ Exactly as the auditor reported, including the ordering (othernat subtraction first). GAMS has no compound-assignment operator; the `+=` at doc:289, inside a ```gams fence, is not valid GAMS. Confirmed.

Note for the fixer: the doc's fenced block lists youngsecdf (288-289) **before** othernat (290-291), i.e. reversed relative to code. Semantically harmless (the two statements are independent - both read `p35_forest_recovery_area`, which neither modifies), so the auditor's minimal fix is safe. Reordering to match `:77` then `:78` is optional polish.

---

## M35-B7 - UPHELD (Minor) - realization_structure (file count)

```
$ wc -l /tmp/magpie_develop_ro/modules/35_natveg/pot_forest_may24/*.gms
     143 declarations.gms
     233 equations.gms
      66 input.gms
     210 postsolve.gms
     107 preloop.gms
     294 presolve.gms
      47 realization.gms
      35 scaling.gms
      30 sets.gms
    1165 total
$ ls .../pot_forest_may24/*.gms | wc -l   -> 9
$ ls -A .../pot_forest_may24 | grep -v '\.gms$'   -> (none; the dir contains only .gms files)
```
**9 files, 1,165 lines.** doc:1147's "8 files" is wrong; doc:5 ("1,165 lines across 9 files") is right.

Equation count independently verified (the fix preserves "32 equations", so I checked it rather than assume):
```
$ grep -c '^ q35_\|^q35_' declarations.gms   -> 32
$ rg -c '^\s*q35_\w+' equations.gms          -> 32
```
Both agree on **32**. (A naive `q35_\w+\(.*\)\s*\.\.` regex returns 31 - it misses `q35_landdiff` at `equations.gms:92`, which is a **scalar** equation with no domain parentheses. Worth recording: that is exactly the kind of off-by-one a future audit could confabulate into a bug.) The fix's "1,165 lines, 32 equations, 9 files" is correct on all three counts.

Also verified: `realization.gms:38-47` includes exactly 8 phase files (sets, declarations, input, equations, scaling, preloop, presolve, postsolve) - `realization.gms` itself is the 9th file. That is the plausible origin of the "8", and it does not rescue the claim: the doc's own File Sizes block and doc:5 both count 9.

---

## M35-B8 - citation OK, claim confirmed (Minor) - other (stale upstream comment)

This is the bug most exposed to the R53 failure mode, so it got the deepest check. The auditor's claim runs *opposite* to R53's (they assert a path IS active, not that it is silently dead), so the hazard is the mirror image: if `im_forest_ageclass` were unpopulated, `preloop.gms:30-31` would silently collapse the distribution to `acx` and the default would behave like mode 0 - which would make the auditor's claim **false**. I therefore traced the producer end-to-end rather than reading M35 alone.

### Citation check
- `input.gms:26` -> `s35_secdf_distribution Flag for secdf initialization (0=all secondary forest in highest age class 1=Equal distribution among all age classes 2=Poulter distribution from MODIS satellite data) (1) / 2 /` ✅ **default = 2**
- `preloop.gms:18-34` -> `:18` `elseif s35_secdf_distribution = 2,`; `:19` comment "For the initialization of age-classes in secondary forest, forest area in 5-year age-classes based on GFAD is used"; `:20` ` p35_secdf_ageclass(j,ac) = im_forest_ageclass(j,ac);` ✅
- `realization.gms:30-34` -> the `@limitations` block, ending `:34` "Inclusion of this data in MAgPIE remains work in progess and is not available for release yet." ✅ (the doc faithfully paraphrases it - the doc's citation is accurate; the *upstream comment* is what is stale)

### Producer chain re-derived (the R53 guard)
```
$ rg -n 'im_forest_ageclass' /tmp/magpie_develop_ro          # WHOLE repo: modules, core, scripts, config, R
28_ageclass/module.gms:11                      interface doc
28_ageclass/oct24/declarations.gms:9           DECLARED  im_forest_ageclass(j,ac)  "... based on GFAD (mio. ha)"
28_ageclass/oct24/preloop.gms:10,11,14         POPULATED from f28_forestageclasses(j,ac_gfad)
35_natveg/pot_forest_may24/preloop.gms:20      READ (the mode-2 branch)
52_carbon/normal_dec17/preloop.gms:11,14,36,53,55,59   READ
```
1. `cfg$gms$ageclass <- "oct24"` (`config/default.cfg:802`) and `$setglobal ageclass oct24` (`main.gms:210`); M28 has exactly **one** realization -> `oct24` is always active. ✅
2. M28 `oct24/preloop.gms:10-14` populates `im_forest_ageclass` from `f28_forestageclasses`. ✅
3. `f28_forestageclasses` is read from `./modules/28_ageclass/input/forestageclasses.cs3` (`oct24/input.gms:8-12`), and `modules/28_ageclass/input/files` lists `forestageclasses.cs3` - the run-time delivery contract. The `.cs3` is absent from the git worktree, which is **expected and uninformative** (gitignored, delivered via input.tgz); the manifest is the evidence, not the on-disk bytes. ✅
4. Third-party corroboration from a module with no stake in this bug: M52 `normal_dec17/preloop.gms:11` ("Secdforest: uses GFAD age distribution (im_forest_ageclass from module 28)") and `:14` ("This runs in preloop (after module 28 preloop has populated im_forest_ageclass)"). ✅

The satellite-derived (GFAD/Poulter) age-class distribution **is** used in a default run. The MAgPIE `@limitations` text is stale, and doc bullet 6 inherits the staleness - its two sub-bullets are also mutually inconsistent (":1092" implies MODIS is unused; ":1093" lists "Poulter distribution" as a current default - and Poulter *is* the MODIS-derived dataset per `input.gms:26`).

Fix text spot-check: all elements verified. One imprecision, inherited from MAgPIE's own switch description and not worth blocking on: mode 1 is "equal across all age classes **except ac0**" (`preloop.gms:16-17` excludes `ac0`), which the fix renders as "equal across all age classes".

---

## M35-B9 - UPHELD (Minor) - producer_declaration / incomplete interface table

### Citation check
- `modules/35_natveg/pot_forest_may24/declarations.gms:79` -> `  vm_landdiff_natveg                                     Aggregated difference in natveg land compared to previous timestep (mio. ha)` (inside `positive variables`; **no domain -> scalar**) ✅
- `modules/10_land/landmatrix_dec18/equations.gms:53` -> `                                 + vm_landdiff_natveg` (inside `q10_landdiff`, opened at `:50`) ✅

### Independent re-derivation
```
$ rg -n 'vm_landdiff_natveg' modules/ core/
35_natveg/pot_forest_may24/declarations.gms:79   DECLARED (M35)
35_natveg/pot_forest_may24/equations.gms:92      POPULATED  q35_landdiff .. vm_landdiff_natveg =e= ...
35_natveg/pot_forest_may24/postsolve.gms:28,74,120,166   .m/.l/.up/.lo -> ov_ reporting (own module)
10_land/landmatrix_dec18/equations.gms:53        CONSUMED by M10 (q10_landdiff)
```
Genuine M35 -> M10 interface variable. M35's own comment at `equations.gms:88-91` says so outright: "The gross change in natural vegetation ... is then passed to the land module ([10_land])".

### Completeness of the fix (checked, since the table claims `declarations.gms` as its source)
M35 declares exactly **six** `vm_`/`pm_` interface identifiers:
```
$ rg -n '^\s*(vm_|pm_)\w+' .../pot_forest_may24/declarations.gms
27:  pm_max_forest_est(t,j)
78:  vm_land_other(j,othertype35,ac)
79:  vm_landdiff_natveg                 <- MISSING from the table
88:  vm_prod_natveg(j,land_natveg,kforestry)
89:  vm_cost_hvarea_natveg(i)
90:  vm_natforest_reduction(j)
```
The table (doc:1187-1191) lists five. `vm_landdiff_natveg` is the **only** omission - the proposed one-row fix is therefore complete, not partial. Its row text (`(scalar)` / "Aggregated difference in natveg land compared to previous timestep" / `mio. ha`) matches `declarations.gms:79` verbatim.

---

## Notes for the fixer

1. **Apply all nine.** No fix text needed correcting.
2. **B1 is two edits, not one** (delete doc:881 **and** add the entry under Section 10.2 "From Module 10"). Applying only the deletion leaves the second instance of the same root error in place.
3. B1's deletion is safe for its neighbours: doc:879 (`vm_land`) and doc:880 (`vm_landdiff_natveg`) are genuine M35 outputs under per-slice ownership, verified above. Do not "tidy" them away.
4. B6 optional polish: reorder the fenced block to match code order (`othernat` at `:77` before `youngsecdf` at `:78`). Semantically neutral.
5. Latent, out-of-scope, low value, recorded so it is not re-discovered as a "new bug": doc:127 omits the `_uncalib` occurrence at M35 `presolve.gms:251`.
6. Do not "fix" the "32 equations" figure - it is correct (32, incl. the domain-less `q35_landdiff`). Only "8 files" is wrong.
