# Round 30 Doc Audit — land_balance_conservation.md

**Target**: `cross_module/land_balance_conservation.md`
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree) + `config/default.cfg`
**Auditor**: adversarial doc auditor (Opus)
**Date**: 2026-05-29

---

## Summary verdict

**MOSTLY ACCURATE.** This is a high-quality, well-cited conservation-law doc. The core land-balance and transition equations (q10_*), all module equation citations (M29/31/32/34/35), the seven-pool land set, the presolve restrictions, the postsolve recursion, and — notably — the highest-risk cross-module consumer sets (`vm_landexpansion` / `vm_landreduction` producer-to lists) are all CORRECT against develop. The authors correctly navigated the `vm_landexpansion_forestry` look-alike trap (M32 uses the `_forestry` variants, not the bare vars) and the M58-via-`m58_LandMerge`-macro subtlety.

Three real but low-severity defects found:
1. **Wrong crop-type breakdown** ("15 food + 4 bioenergy"; reality is 2 bioenergy / 17 food; total 19 is right). [Minor]
2. **Non-existent GDX symbol** `oq_land_area` in the Step-4 testing R snippet (real symbol is `oq10_land_area`). [Minor]
3. **Citation drift** at M32 presolve 208-210 → the described secdforest-restoration-conflict logic is at lines 213-215. [Minor]

No Critical or Major bugs. No inverted defaults, no phantom/omitted consumers, no invented interface variable/equation names presented as authoritative model behavior.

---

## Claims verified CORRECT (high-value confirmations)

### Core equations (Module 10, landmatrix_dec18 — DEFAULT, config/default.cfg:232)
- `q10_land_area` @ equations.gms:13-15 — `sum(land, vm_land(j2,land)) =e= sum(land, pcm_land(j2,land));` — doc:14, doc:24-27, doc:96-99 ✓ (set-based sum preserved, MANDATE 10 respected)
- `q10_transition_to` @ equations.gms:19-21 — doc:170-175 ✓
- `q10_transition_from` @ equations.gms:23-25 — doc:161-166 ✓
- `q10_landexpansion` @ equations.gms:30 — doc:221 ✓
- `q10_landreduction` @ equations.gms:35 — doc:222 ✓
- `pcm_land(j,land) = vm_land.l(j,land);` @ postsolve.gms:9 — doc:117-119, doc:815 ✓

### Land set (core/sets.gms:250-251)
- `land = / crop, past, forestry, primforest, secdforest, urban, other /` (7 members) — doc:35 "Verified: core/sets.gms:250-251", doc:37 "7 mutually exclusive land types" ✓
- Note: doc's expanded ordering (doc:108-112) lists urban last; code order is `...primforest, secdforest, urban, other`. Cosmetic only (it is a sum); not flagged.

### Presolve transition restrictions (landmatrix_dec18/presolve.gms; doc §4.3 header "Verified: presolve.gms:10-23")
- `vm_lu_transitions.fx(j,"primforest","forestry") = 0;` @ presolve.gms:13 — doc:188 ✓
- `vm_lu_transitions.fx(j,land_from,"primforest") = 0;` @ presolve.gms:20 — doc:194 ✓
- `vm_lu_transitions.up(j,"primforest","primforest") = Inf;` @ presolve.gms:21 — doc:199 ✓
- `vm_lu_transitions.fx(j,"primforest","other") = 0;` / `secdforest","other") = 0;` @ presolve.gms:16-17 — doc:201-205 ✓
- Whole-tree grep confirms these 5 are the ONLY `.fx/.up` bounds on `vm_lu_transitions` anywhere; matrix §4.1 forbidden cells are consistent.

### Module equation citations
- M29 `q29_cropland` @ detail_apr24/equations.gms:11-12 (DEFAULT, default.cfg:795) — `vm_land(j2,"crop") =e= sum((kcr,w), vm_area(j2,kcr,w)) + vm_fallow(j2) + sum(ac, v29_treecover(j2,ac));` — doc:238-242 ✓
- M31 `q31_prod` @ endo_jun13/equations.gms:16-18 (DEFAULT, default.cfg:969) — doc:283-287 ✓; conservation `vm_land.lo(j,"past") = sum(consv_type, pm_land_conservation(t,j,"past",consv_type));` @ endo_jun13/presolve.gms:9 — doc:299-302 ✓
- M32 `q32_land` @ dynamic_may24/equations.gms:55-56 (DEFAULT, default.cfg:976) — doc:310-313 ✓; `type32 = {aff,ndc,plant}` (sets.gms) — doc:58-60 ✓
- M34 `q34_urban_land` @ exo_nov21/equations.gms:30-31 (DEFAULT, default.cfg:1126) — doc:335-338 ✓; deviation cost `s34_urban_deviation_cost = 1e+06` USD17MER/ha @ exo_nov21/input.gms:13 — doc:157,343 ✓
- M35 `q35_land_secdforest` @ pot_forest_may24/equations.gms:11; `q35_land_other` @ :13 (DEFAULT natveg, default.cfg:1135) — doc:364-373 ✓; `othertype35 = {othernat, youngsecdf}` (sets.gms) — doc:72-73 ✓
- M35 carbon threshold 20 tC/ha @ pot_forest_may24/presolve.gms:111,117 (`> 20` on `pm_carbon_density_secdforest_ac_uncalib`) — doc:73,380,390,571 (value correct; citation 99-107 slightly above the threshold logic at 106-117 — borderline, NOT flagged: same mechanism block, value verified)
- M35 abandonment/recovery @ pot_forest_may24/presolve.gms:47-73 (recovery distribution at 56-73) — doc:566 ✓

### Interface variables
- `vm_lu_transitions(j,land_from,land_to)` @ landmatrix_dec18/declarations.gms:23 — doc:137 ✓
- `vm_landexpansion(j,land)`, `vm_landreduction(j,land)` @ declarations.gms:20-21 ✓
- `vm_area(j,kcr,w)` "Agricultural production area (mio. ha)" declared in Module 30 @ detail_apr24/declarations.gms:21 — doc:261 ✓
- `pm_max_forest_est(t,j)` declared in M35 @ pot_forest_may24/declarations.gms:27, READ by M32 @ dynamic_may24/presolve.gms:22-23 & equations.gms:86 — doc:386,521 ✓ (doc elides `t` dim in conceptual formula; not load-bearing)

### Cross-module consumer sets — HIGHEST-RISK CLAIMS, ALL CORRECT
Verified with word-boundary grep EXCLUDING the `_forestry` look-alike + checking the `m58_LandMerge` macro (core/macros.gms — expands `vm_landexpansion` directly into M58's equation, so M58 IS a direct consumer):

- **doc:227** `vm_landexpansion(j,land)` → "modules 35, 39, 58, 59"
  ACTUAL external consumers (bare var): M35 (equations.gms:197,222), M39 (equations.gms:13), M58 (equations.gms:28 via macro), M59 (equations.gms:91). **EXACT MATCH ✓**
- **doc:228** `vm_landreduction(j,land)` → "modules 39, 58 (NOT 35/59 — they consume only vm_landexpansion)"
  ACTUAL external consumers (bare var): M39 (equations.gms:14), M58 (equations.gms:31 via macro). **EXACT MATCH ✓** — and the parenthetical is correct: M35 & M59 have NO bare `vm_landreduction` reads (confirmed absent, positive control passed).
  NOTE: M32 references `vm_landexpansion_forestry`/`vm_landreduction_forestry` (its own produced variables, equations.gms:62,65,85) — NOT the bare interface vars. Doc correctly omits M32. A naive `rg -l "vm_landexpansion"` falsely includes M32; the doc authors got this right.

### Centrality (doc:230 "17 connections (2 inputs, 15 outputs) - Highest in MAgPIE")
- Matches the SSOT `core_docs/Module_Dependencies.md:32` (`| 10_land | 17 | 15 | 2 |`) EXACTLY. Internally consistent with the canonical dependency table. The absolute correctness of "17" is a methodology-dependent derived metric (not directly code-checkable); doc faithfully reproduces SSOT → NOT flagged. (Sanity: 11 distinct modules reference `vm_land` directly; the 15/2 figure counts variable-level edges, a different metric.)

---

## Bugs found

### BUG L-1 — Wrong crop-type food/bioenergy breakdown
- **Severity**: Minor (tier_uncertainty: true — leans Major as a count error, but headline total 19 is correct and tie-breaker pulls down)
- **Class**: 6 (Hardcoded counts drift)
- **doc_line**: land_balance_conservation.md:263
- **Claim**: "`kcr`: 19 crop types (15 food crops + 4 bioenergy)"
- **Reality**: `kcr` total = 19 ✓, but the split is wrong. Bioenergy set `kbe30 = {betr, begr}` = **2** bioenergy crops, not 4. Food crops = 17. Alternatively 19 = 15 annual (`crop_ann30`) + 4 perennial (`crop_per30 = {oilpalm, begr, sugr_cane, betr}`). The doc appears to have mislabeled the 15-annual / 4-perennial split as 15-food / 4-bioenergy.
- **file_evidence**: `modules/30_croparea/detail_apr24/sets.gms` — `kbe30(kcr) / betr, begr /`; `crop_ann30` (15 members); `crop_per30 / oilpalm, begr, sugr_cane, betr /` (4). Same in `simple_apr24/sets.gms`.
- **verify_cmd**: `rg -n -A1 "kbe30" .../30_croparea/detail_apr24/sets.gms` → `/ betr, begr /` ; python count of crop_ann30=15, crop_per30=4.
- **confirmed**: true
- **proposed_fix**: Replace "19 crop types (15 food crops + 4 bioenergy)" with "19 crop types (17 food crops + 2 bioenergy: `begr`, `betr`)".

### BUG L-2 — Non-existent GDX symbol `oq_land_area` in testing R snippet
- **Severity**: Minor (tier_uncertainty: true — a wrong symbol that errors on execution; lands as Minor because it is illustrative R protocol code, recoverable, and sibling symbols in the same block are correct)
- **Class**: 2 (Hallucinated variable name) / 10-adjacent (wrong symbol)
- **doc_line**: land_balance_conservation.md:721
- **Claim**: `land_previous <- readGDX(gdx, "oq_land_area", select=list(type="level"))`
- **Reality**: No GDX symbol `oq_land_area` exists. The land-balance equation's output symbol is `oq10_land_area` (postsolve.gms:18,31). `readGDX(gdx, "oq_land_area", ...)` would return NULL / error. (The two sibling reads on doc:719-720 — `ov_lu_transitions`, `ov_land` — are both valid symbols.)
- **file_evidence**: `modules/10_land/landmatrix_dec18/postsolve.gms:18` ` oq10_land_area(t,j,"marginal") = q10_land_area.m(j);`
- **verify_cmd**: `grep -rn "oq_land_area" /tmp/magpie_develop_ro/modules/ | wc -l` → `0`; positive control `grep "oq10_land_area" .../postsolve.gms` → present (lines 18,31,44,57); python: `'oq_land_area' in 'oq10_land_area'` → False (not a substring; genuinely absent).
- **confirmed**: true
- **proposed_fix**: Change `"oq_land_area"` to `"oq10_land_area"` on doc:721. (Note also that the equation `.m` value is the marginal/shadow price, not "previous land" — the variable name `land_previous` is conceptually loose, but symbol-name fix is the load-bearing correction.)

### BUG L-3 — Citation drift: M32 presolve 208-210 → secdforest-restoration logic is at 213-215
- **Severity**: Minor (tier_uncertainty: true; adjacent ~3-5 lines, soft paraphrase citation)
- **Class**: 10 (Stale file:line citation) / 12 (content-level mismatch)
- **doc_line**: land_balance_conservation.md:325
- **Claim**: "Land Conservation (`modules/32_forestry/dynamic_may24/presolve.gms:208-210`): Avoids conflict with secdforest restoration targets / Respects protected area constraints"
- **Reality**: Lines 208-210 contain `p32_future_to_current_demand_ratio` (forestry demand ratios), NOT conservation logic. The described "Avoid conflict between afforestation for carbon uptake ... and secdforest restoration" comment is at presolve.gms:213, with the adjusting assignment at 214-215.
- **file_evidence**: `modules/32_forestry/dynamic_may24/presolve.gms:213` `* Avoid conflict between afforestation for carbon uptake on land and secdforest restoration`; logic at 214-215 (`pm_land_conservation(t,j,"secdforest","restore")...`).
- **verify_cmd**: `sed -n '205,215p' .../32_forestry/dynamic_may24/presolve.gms` → 208-210 = demand-ratio params; 213-215 = the restoration-conflict block.
- **confirmed**: true
- **proposed_fix**: Change citation `presolve.gms:208-210` to `presolve.gms:213-215`. ("Respects protected area constraints" is not literally at 213-215; consider trimming that second bullet or generalizing the citation to the conservation block.)

---

## Deferred (not code-verifiable / methodology-dependent — NO edits)

- doc:230 centrality "17 connections (2 inputs, 15 outputs)": derived graph metric; matches SSOT Module_Dependencies.md:32 exactly. Absolute correctness depends on the (undocumented-here) edge-counting methodology; not independently code-checkable. Doc is internally consistent → no bug.
- doc §4.1 7×7 transition matrix ASCII (doc:142-149): illustrative; the forbidden cells (✗) it marks are all consistent with presolve.gms:13,16,17,20. The "M35" annotations for prim/secd→secd are a modeling-narrative simplification, consistent with doc:207. Not flagged.
- doc:35 header "Verified: core/sets.gms:250-251" — set spans exactly 250-251 (label line 250, members line 251). Correct.
- R-code magpie4 examples (§6.2, §8.2) `land(gdx, level="cell")`, `dimSums(...)` — magpie4 API, out of scope for GAMS-code verification; not the target ground truth. (Only the GDX symbol name in L-2 is GAMS-side checkable.)
- doc:73,390 "carbon < 20 tC/ha" vs presolve uses `> 20` for the youngsecdf→secdforest shift: value (20) confirmed; the citation 99-107 is ~5 lines above the actual `> 20` at line 117. Borderline; the value is right and the section header is at 106 — left as a non-flagged near-miss rather than risk a false positive.

---

## Mechanical-check notes
- All equation/variable/realization names that ARE flagged in the doc resolve to real code symbols (except `oq_land_area`, L-2).
- Default realizations: every realization the doc relies on (landmatrix_dec18, detail_apr24 cropland, endo_jun13, dynamic_may24, exo_nov21, pot_forest_may24) is the config default. (Croparea default is `simple_apr24`, but the doc cites M30's *variable* `vm_area`, not a croparea-realization file — so no realization error there.)
- MANDATE 17 (direct vs transitive): consumer sets on doc:227-228 are direct equation-level reads (verified), and the M32 `_forestry`-variant exclusion is correct.
