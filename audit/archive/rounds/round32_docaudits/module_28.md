# Round 32 Doc Audit — module_28.md (Ageclass)

**Auditor**: Opus adversarial doc auditor
**Doc**: `<magpie-agent>/modules/module_28.md`
**Ground truth**: develop worktree `/tmp/magpie_develop_ro` @ HEAD `ee98739fd` (detached, clean)
**Date**: 2026-05-30
**Realization audited**: `oct24` (only realization; default per `config/default.cfg:786`)

---

## Verdict: MOSTLY ACCURATE (lower band)

The doc's spine is correct: module 28 is a pure data provider (0 equations, 0 variables, 1 parameter `im_forest_ageclass`, dynamic sets `ac_est`/`ac_sub` populated in presolve). The transformation logic, mapping table, divide-by-2, `m_yeardiff_forestry` macro, GFAD class15→acx, and the 62-element age-class summary are all verified correct. The errors cluster in **consumer/dependency sets** (the highest-harm class per the R20 anchor) and in one stale citation block.

**Pre-run advisory (R16 age-class range) — REFUTED for this doc.** The doc states the full range correctly: lines 22-27 and 450 give "62 five-year age-classes … ac0, ac5, … ac295, ac300, acx … 61 regular classes + acx = 62". This matches `core/sets.gms:269-275` exactly (counted 62 elements, ac0..ac300 + acx). The doc explicitly warns "do NOT truncate this range." No truncation bug here.

---

## Claims verified CORRECT

| Claim (doc line) | Evidence |
|---|---|
| Realization `oct24`, only one, is default (L4, L62) | `config/default.cfg:786` `cfg$gms$ageclass <- "oct24"`; `ls modules/28_ageclass/` → only `oct24` |
| 0 equations, 0 variables (L13-14) | `rg q28_ modules/28_ageclass/` → none; `rg v28_/vm_ …/declarations.gms` → none (positive control: `im_forest_ageclass` line found) |
| 1 parameter `im_forest_ageclass(j,ac)`, declarations.gms:9 (L15, L211) | `declarations.gms:9` exact match, "(mio. ha)" |
| Phases sets/declarations/input/preloop/presolve; no equations/postsolve/scaling (L42-47) | `oct24/realization.gms:16-22` lists exactly these 5 phases |
| 62 age-classes ac0..ac300, acx (L22-27, L450) | `core/sets.gms:269-275`, counted 62 — **R16 advisory refuted** |
| 15 GFAD classes class1..class15 (L70, L757) | `sets.gms:9-12` |
| `ac_young` = {ac0..ac30}, sets.gms:14-15 (L130-133) | `sets.gms:14-15` exact |
| ac_gfad_to_ac mapping table, class1→(ac5,ac10)…class14→(ac135,ac140) (L104-118) | `sets.gms:17-32` exact |
| class15 → acx, no class for class15 in the to_ac map (L119, L122-126) | `sets.gms` map stops at class14; `preloop.gms:14` `im_forest_ageclass(j,"acx") = f28_forestageclasses(j,"class15")` |
| Divide-by-2 transform, preloop.gms:11 (L98, L534) | `preloop.gms:11` exact |
| `ac_est`/`ac_sub` populated in presolve.gms:9-10/12-13 (L145-147, L168-170) | `presolve.gms:9-13` exact |
| `m_yeardiff_forestry` macro = `5$(ord(t)=1)+(m_year(t)-m_year(t-1))$(ord(t)>1)` (L564-566) | `core/macros.gms:45` exact |
| First timestep = 5 years (L192, L569) | macro confirms |
| M35 reads `im_forest_ageclass` at `pot_forest_may24/preloop.gms:20` (L224, L312) | `modules/35_natveg/pot_forest_may24/preloop.gms:20` `p35_secdf_ageclass(j,ac) = im_forest_ageclass(j,ac)`; default natveg = `pot_forest_may24` (`default.cfg:1135`) |
| M32 `v32_hvarea_forestry.fx(j,ac_est)=0`, `v32_land_reduction.fx(j,type32,ac_est)=0` at `dynamic_may24/presolve.gms:9-10` (L238, L241-242) | `modules/32_forestry/dynamic_may24/presolve.gms:9-10` exact; default forestry = `dynamic_may24` (`default.cfg:976`) |
| `im_forest_ageclass` NOT used by Module 32 (L228) | `rg im_forest_ageclass modules/32_forestry/` → no hits; only M35 + M52 read it |
| `pm_carbon_density_secdforest_ac`, `pm_carbon_density_plantation_ac` real (L423) | `modules/52_carbon/normal_dec17/declarations.gms:9,12` |

---

## Bugs Found

### Bug 28-B1 — `ac_est` consumer set omits M29 and M35 (Major)

- **Severity**: Major (Class 15 latent doc error / consumer-set omission; per R20 anchor the consumer-set error class is Critical-prone, but here the *primary* documented consumer M32 is correct and the omission is of additional consumers in advisory/interface prose, so tie-breaker → Major)
- **Trigger**: MANDATE 13 (interface-consumer grep) — documented consumer set incomplete.
- **Claim in doc** (L230-246): "#### 2. ac_est(ac) … **Used by**: 1. **Module 32 (Forestry)** - Plantation dynamics". Only M32 listed.
- **Reality in code**: `ac_est` is directly read as live code (equations + bounds) in **Module 29 (cropland)** and **Module 35 (natveg)** as well as M32.
  - M29: `detail_apr24/equations.gms:110,122-123` (`q29_treecover_est`), `detail_apr24/presolve.gms:79-80` (`v29_treecover.lo/.up(j,ac_est)`).
  - M35: `pot_forest_may24/equations.gms:102,110,228-232` (`q35_secdforest_est`, `q35_other_est`), `pot_forest_may24/presolve.gms:36,58,71,213,269-272` (recovery-area + harvest/reduction fixes).
- **File evidence**: `modules/29_cropland/detail_apr24/presolve.gms:79`; `modules/35_natveg/pot_forest_may24/equations.gms:228`.
- **verify_cmd**: `rg -ln "ac_est" /tmp/magpie_develop_ro/modules/` → returns 29_cropland (equations+presolve), 35_natveg (4 files), 32_forestry (3 files), 28_ageclass (definition). M29 and M35 verified as real code (not comments) via line-level `rg`.
- **Confirmed**: true.
- **Proposed fix**: Under "ac_est(ac) … Used by", list all direct consumers: "1. Module 32 (Forestry) — plantation establishment/harvest bounds (`dynamic_may24/presolve.gms:9-10`); 2. Module 35 (NatVeg) — secondary-forest & other-land establishment equations and forest-recovery redistribution (`pot_forest_may24/equations.gms:228,231`, `pot_forest_may24/presolve.gms:36,269-272`); 3. Module 29 (Cropland) — tree-cover establishment (`detail_apr24/equations.gms:122`, `detail_apr24/presolve.gms:79-80`)."

### Bug 28-B2 — `ac_sub` consumer set omits M29 and M35 (Major)

- **Severity**: Major (same class/trigger as B1; tie-breaker → Major).
- **Trigger**: MANDATE 13.
- **Claim in doc** (L248-263): "#### 3. ac_sub(ac) … **Used by**: 1. **Module 32 (Forestry)** - Plantation dynamics". Only M32 listed.
- **Reality in code**: `ac_sub` is directly read as live code in **M29**, **M35**, and M32.
  - M29: `detail_apr24/equations.gms:42,117`, `detail_apr24/presolve.gms:81-82` (`v29_treecover.fx(j,ac_sub)`).
  - M35: `pot_forest_may24/equations.gms` (many: 51,85,95-97,104-114,135-189,209-221), `pot_forest_may24/presolve.gms:14-45,172-214,275-281` (disturbance loss, protection, harvest bounds).
- **File evidence**: `modules/29_cropland/detail_apr24/presolve.gms:81`; `modules/35_natveg/pot_forest_may24/presolve.gms:14`.
- **verify_cmd**: `rg -ln "ac_sub" /tmp/magpie_develop_ro/modules/` → 29_cropland (equations+presolve), 35_natveg (equations+presolve), 32_forestry (equations+presolve), 28_ageclass. Verified real code at line level.
- **Confirmed**: true.
- **Proposed fix**: Mirror B1 fix for `ac_sub`: add M35 (`pot_forest_may24/equations.gms:104,112`, `pot_forest_may24/presolve.gms:14,275-281`) and M29 (`detail_apr24/equations.gms:42,117`, `detail_apr24/presolve.gms:81`) as direct consumers alongside M32.

### Bug 28-B3 — `im_forest_ageclass` consumer set omits direct M52 read (Major)

- **Severity**: Major. The doc both omits M52 from the parameter's "Used by" list AND mischaracterizes M52's dependency as merely indirect (via the `ac` set), when M52 directly reads the `im_forest_ageclass` *parameter*.
- **Trigger**: MANDATE 13 + MANDATE 17 (direct vs transitive). Here M52 is a genuine *direct* consumer that the doc demotes to indirect.
- **Claim in doc**: L221-228 ("im_forest_ageclass … **Used by**: 1. Module 35 …") lists only M35. L421-425 frames M52's link as "INDIRECT — Age-classes used in Module 52 carbon growth calculations … Module 28 provides the age-class indexing structure" (i.e., the `ac` set, not the parameter).
- **Reality in code**: Module 52 directly reads the `im_forest_ageclass` parameter in a Chapman-Richards `k`-calibration bisection: `normal_dec17/preloop.gms:53,55,59` compute `i52_gs_current(i)` as an area-weighted growing stock using `im_forest_ageclass(j,ac)` (lines 53-59), gated on `sum(...,im_forest_ageclass) > 0`.
- **File evidence**: `modules/52_carbon/normal_dec17/preloop.gms:53-59` (and comment refs at :11,:14,:36).
- **verify_cmd**: `rg -n "im_forest_ageclass" /tmp/magpie_develop_ro/modules/` → M52 `normal_dec17/preloop.gms:53,55,59` are code (not just comments). `rg -n "ac_sub|ac_est" …/52_carbon/normal_dec17/` → exit 1 (M52 uses the `ac` set + the parameter, NOT the dynamic subsets).
- **Confirmed**: true.
- **Proposed fix**: In the `im_forest_ageclass` "Used by" list add: "2. Module 52 (Carbon) — directly reads `im_forest_ageclass` to compute the area-weighted secondary-forest growing stock for Chapman-Richards `k` calibration (`modules/52_carbon/normal_dec17/preloop.gms:53-59`)." Revise L421-425 to note M52 consumes the actual parameter, not merely the `ac` index.

### Bug 28-B4 — M32 "Usage" citations point at nonexistent lines (~280-320) (Major)

- **Severity**: Major (Class 10/12 citation drift). Cited lines are off by ~270 and exceed EOF; a reader checking the source finds nothing there.
- **Trigger**: §1 Major — "Citation … no longer at the cited line." MANDATE 16 (post-merge line numbers).
- **Claim in doc**: "Usage by Other Modules → Module 32" repeatedly cites `dynamic_may24/presolve.gms:~280` (L160, L340), `~281` (L346), `~285` (L182,368), `~286` (L359), `~287` (L375), `~290` (L388), `~295` (L352), `~300` (L382). Also L256 cites `dynamic_may24/presolve.gms:~285-320`.
- **Reality in code**: M32 `dynamic_may24/presolve.gms` is **231 lines total**. The cited snippets actually live at: `v32_hvarea_forestry.fx(j,ac_est)=0` line 9; `v32_land_reduction.fx` line 10; `p32_disturbance_loss_ftype32` line 75; disturbance redistribution `pc32_land(...,ac_est)=…/card(ac_est2)` line 76; subtraction line 78; `v32_land.fx(j,"ndc",ac_sub)` line 144; `v32_land.lo/.up(j,"plant",ac_est)` lines 138-139. Lines 280-320 do not exist.
- **File evidence**: `modules/32_forestry/dynamic_may24/presolve.gms:9,10,75,76,78,144` (file EOF at 231).
- **verify_cmd**: `wc -l …/32_forestry/dynamic_may24/presolve.gms` → 231; `rg -n "v32_hvarea_forestry|p32_disturbance_loss_ftype32|v32_land.fx.*ndc" …/presolve.gms` → lines 9,75,144. Note: the SAME doc cites the correct line 9-10 in the Interface section (L238), so this is also an internal inconsistency.
- **Confirmed**: true.
- **Proposed fix**: Replace every `presolve.gms:~28x`/`~29x`/`~30x`/`~285-320` in the "Usage by Other Modules → Module 32" subsection with the real line numbers: `.fx(ac_est)` zeros → :9-10; disturbance loss → :75; redistribution → :76; subtraction → :78; ndc fix → :144; plant bounds → :138-139. Drop the `~` (the exact lines are known).

### Bug 28-B5 — Fabricated set name `ac_ff` (Major)

- **Severity**: Major. A non-existent set presented in backticks alongside two real sets in a "safe to modify" bullet; a reader could treat it as a real dynamic set. (Critical trigger "invented name presented as authoritative" is for `vm_/pm_/v{N}_` in declarations; `ac_ff` is a set in advisory prose → tie-breaker pulls to Major.)
- **Trigger**: MANDATE 7 (variable/set-name lookup); Class 2 (hallucinated name).
- **Claim in doc** (L480): "Modifying dynamic age-class sets (`ac_sub`, `ac_est`, `ac_ff`) generation logic".
- **Reality in code**: `ac_ff` does not exist anywhere. Only `ac`, `ac_young`, `ac_gfad`, `ac_gfad_to_ac`, `ac_est`, `ac_sub` (+ aliases `ac2`, `ac_gfad2`, `ac_est2`, `ac_sub2`) exist.
- **File evidence**: absent from `core/sets.gms` and all `modules/`.
- **verify_cmd**: `rg -n "ac_ff" /tmp/magpie_develop_ro/core/ /tmp/magpie_develop_ro/modules/` → empty (exit 1); second method `grep -rn "ac_ff" …` → empty (exit 0, no lines); positive control `rg -ln "ac_est" core/sets.gms` → found (search works).
- **Confirmed**: true.
- **Proposed fix**: Delete `` `ac_ff` `` from L480 → "Modifying dynamic age-class sets (`ac_sub`, `ac_est`) generation logic".

### Bug 28-B6 — "15 classes covering 0-75+ years" contradicts the 62-class ac set (Major)

- **Severity**: Major. Conflates GFAD's 15 classes with MAgPIE's 62-element `ac` set and gives a flatly wrong range (0-75 vs 0-300). Contradicts the doc's own Critical summary box (L22-27, 62 classes, 0-300).
- **Trigger**: §1 Major — wrong number on a load-bearing structure; Class 6 (count drift) + Class 11 (range).
- **Claim in doc** (L482): "Changing the number of age-classes (currently 15 classes covering 0-75+ years)".
- **Reality in code**: The MAgPIE `ac` set has **62** elements spanning **0-300 years** (`core/sets.gms:269-275`); "15 classes" is the GFAD input bands (`ac_gfad`), and "0-75+ years" is wrong for either set (GFAD spans 0-150+; the MAgPIE ac set spans 0-300).
- **File evidence**: `core/sets.gms:269-275` (62 elements ac0..ac300+acx); `sets.gms:9-12` (15 GFAD bands to class15=150+).
- **verify_cmd**: `sed -n '269,275p' core/sets.gms | grep -oE 'ac[0-9]+|acx' | sort -u | wc -l` → 62.
- **Confirmed**: true.
- **Proposed fix**: Replace "(currently 15 classes covering 0-75+ years)" with "(MAgPIE uses 62 five-year `ac` classes spanning 0-300 years plus `acx`; GFAD input has 15 ten-year bands)".

### Bug 28-B7 — GFAD class15 described as "140+ class" (Minor)

- **Severity**: Minor. Prose detail; contradicts the code comment and the doc's own GFAD table.
- **Trigger**: §1 Minor — wrong detail a careful reader wouldn't act on.
- **Claim in doc** (L286): "15 classes (14 ten-year classes + 1 open-ended 140+ class)".
- **Reality in code**: `preloop.gms:12` comment: "`class15` in GFAD1.1 includes forests that are 150 years or older". The doc's own table (L87) and L26/L119 say "150+". So "140+" is internally inconsistent and off vs code.
- **File evidence**: `modules/28_ageclass/oct24/preloop.gms:12`.
- **verify_cmd**: `sed -n '12p' …/preloop.gms` → "150 years or older".
- **Confirmed**: true.
- **Proposed fix**: "…+ 1 open-ended 150+ class" (align with code and the rest of the doc). Note: GFAD's class14 = 130-140 and class15 = 150+, leaving a documented 140-150 gap inherent to GFAD (not a doc bug).

### Bug 28-B8 — "Provides To" attributes `ac_sub` to Module 52 (Minor)

- **Severity**: Minor. The broader claim (M52 depends on M28) is true via the `ac` set + `im_forest_ageclass`, but the specific `ac_sub` tag is a phantom; a reader tracing `ac_sub` consumers to M52 finds nothing.
- **Trigger**: §1 Minor (phantom tag on an otherwise-true dependency) — borders Major but the dependency itself is real, so tie-breaker → Minor.
- **Claim in doc** (L442): "3. **Module 52 (Carbon)** - Age-class index for carbon density lookups (`ac`, `ac_sub`)".
- **Reality in code**: M52 `normal_dec17` does NOT reference `ac_sub` (or `ac_est`); it uses the `ac` set and the `im_forest_ageclass` parameter.
- **File evidence**: `rg -n "ac_sub" modules/52_carbon/normal_dec17/` → no hits (exit 1); positive control `rg -ln '\bac\b' …/preloop.gms` → found.
- **verify_cmd**: `rg -n "ac_sub|ac_est" /tmp/magpie_develop_ro/modules/52_carbon/normal_dec17/` → empty (exit 1).
- **Confirmed**: true.
- **Proposed fix**: Change L442 to "Module 52 (Carbon) - `ac` age-class set + `im_forest_ageclass` for the secondary-forest growing-stock / Chapman-Richards `k` calibration". Drop `ac_sub`.

---

## Cross-cutting note: "Provides To (3 modules)" undercounts

The doc states "Total Connections: 3 … Provides To (3 modules): M35, M32, M52" (L436-442). Across all three interface objects the true direct-consumer set is **{M29, M32, M35, M52} = 4 modules**. M29 (tree cover, `detail_apr24`) directly consumes both `ac_est` and `ac_sub` and is entirely absent from the doc. (Fix folds into B1/B2: add M29; update the connection count to 4 and the centrality note accordingly.) Treated as part of B1/B2 rather than a separate bug to avoid double-counting the same root cause (incomplete consumer enumeration).

---

## Deferred (not code-verifiable in worktree → no edit proposed)

- `forestageclasses.cs3` is not present in the develop worktree (`modules/28_ageclass/input/` contains only a `files` manifest; the .cs3 is downloaded at runtime). Therefore all claims sourced to `forestageclasses.cs3:N` cannot be verified: file size "206 lines" (L300,L796), header "GFAD v1.1" (L833), processing-tool versions "madrat 3.24.1 + mrmagpie 1.61.0" (L60,L288,L834), the `calcOutput(type="AgeClassDistribution", …)` command (L289-296), and "circa 2000" period. These are preprocessing-provenance claims; route to the preproc-agent for verification.
- "~200 cells", "0.5° native resolution", cluster aggregation (L216,L282,L669-671): runtime/clustering config, not GAMS-verifiable here.
- "Centrality Rank ~25 of 46" (L435): derived metric, not directly code-checkable.
- Poulter et al. (2019) GFAD methodology details (L274-284): external literature, not code.

---

## Summary

R16 age-class-range advisory **refuted** — the doc correctly states the 62-element ac0..ac300+acx set. Eight confirmed bugs: 6 Major (3 consumer-set omissions on `ac_est`/`ac_sub`/`im_forest_ageclass` missing M29/M35/M52; 1 citation-drift block citing nonexistent M32 presolve lines ~280-320 when file is 231 lines; 1 fabricated set `ac_ff`; 1 wrong "15 classes / 0-75 yr" contradicting the 62-class/0-300 reality) + 2 Minor (GFAD "140+" vs code's "150+"; phantom `ac_sub` tag on M52). Root cause of the Majors is incomplete/under-traced consumer enumeration plus a stale citation block.
