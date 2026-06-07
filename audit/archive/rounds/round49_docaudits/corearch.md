# Audit Report: Core_Architecture.md

**Target**: `core_docs/Core_Architecture.md`
**Ground truth**: `/tmp/magpie_develop_ro` @ HEAD `ee98739fd` (matches working tree)
**Auditor**: adversarial doc auditor (round 49 doc-audits)
**Date**: 2026-06-06

## Overall Verdict: ACCURATE
## Accuracy Score: 9.5/10

This is a structural/architecture overview doc. Nearly every load-bearing, code-checkable claim verifies EXACTLY against develop: main.gms line citations, solver options, the full module list, core file structure, the 12 execution phases + their module attributions, the fundamental sets (region list, cluster count, time ranges, product/land/nutrient sets), the intersolve mechanism with its default switch, and config globals. Zero Critical or Major bugs. The only candidate issues are low-severity convention-list items (the `x_` / `o_` prefix descriptions) that I could not confirm as wrong against code alone (they may be documented in MAgPIE's upstream goxygen naming standard, which is not in-repo) — recorded as DEFERRED, not bugs.

---

## Verified Claims (correct)

### Section 2.1 — main.gms execution flow line citations
All verified against `/tmp/magpie_develop_ro/main.gms`:
- "Core Macros (line 257)" → `$include "./core/macros.gms"` at 257 ✓
- "Core Sets (line 261)" → `$include "./core/sets.gms"` at 261; "Module Sets (line 262)" → batinclude sets at 262 ✓
- "Core Declarations (line 266)" → 266; "Module Declarations (line 267)" → 267 ✓
- "Data Import (line 271)" → batinclude input at 271 ✓
- "Equations Definition (line 275)" → batinclude equations at 275 ✓
- "Model Definition (line 279)" → `model magpie / all - m15_food_demand /;` at 279 ✓
- "Variable Scaling (line 291)" → batinclude scaling at 291 ✓
- "General Calculations (line 295)" → `$include "./core/calculations.gms"` at 295 ✓
- "Module Setup (lines 193-253)" → setup block runs main.gms:193 (`$setglobal drivers aug17`) to 252 (`$setglobal optimization nlp_apr17`); `END MODULE SETUP` comment at 254; line 253 is blank. Essentially correct (off-by-one on the trailing blank line; the range visually covers the section). Informational, not flagged.

### Section 2.2 / 5.1 — execution phases
All 12 phase names are real (confirmed via `find modules -name '*.gms'` distinct-basename count): sets, declarations, input, equations, scaling, start, preloop, presolve_ini, presolve, solve, intersolve, postsolve ✓
- Phase ordering matches main.gms + core/calculations.gms (sets→declarations→input→equations→[model def]→scaling→[calculations: start, preloop, then time loop]) ✓
- "presolve_ini ... 22_land_conservation bounds" → the single `presolve_ini.gms` is at `modules/22_land_conservation/area_based_apr22/presolve_ini.gms` ✓
- "intersolve ... 15_food demand coupling" → the single `intersolve.gms` is at `modules/15_food/anthro_iso_jun22/intersolve.gms` ✓
- "solve ... routed through 80_optimization" → all 4 `solve.gms` files are under `modules/80_optimization/` (lp_nlp_apr17, nlp_apr17, nlp_ipopt, nlp_par) ✓

### Section 3.1 — core/ file structure
Doc lists exactly: calculations.gms, declarations.gms, load_gdx.gms, macros.gms, sets.gms. `ls core/` returns exactly these 5 ✓

### Section 3.2 — fundamental sets (verified against core/sets.gms)
- `i` = 12 regions `CAZ, CHA, EUR, IND, JPN, LAM, MEA, NEU, OAS, REF, SSA, USA` → EXACT match (sets.gms:20-21) ✓
- `j` = 200 clusters "aggregated from 0.5°" → CAZ_1*...*USA_200 = 200 cells, comment "number of LPJ cells" (sets.gms:57-69) ✓
- `iso` ISO codes (sets.gms:37) ✓; `cell(i,j)` cluster→region mapping (sets.gms:71) ✓
- `t_all` "All time periods (1965-2150)" → y1965...y2150 (sets.gms:154-159) ✓
- `t` "default 1995-2100" → default c_timesteps=coup2100 = y1995...y2100 (sets.gms:188) ✓
- `t_past` historical configured (sets.gms:177); `ct` current (sets.gms:218); `pt` previous (sets.gms:219) ✓
- `kall` all products (sets.gms:228) ✓
- Livestock `livst_rum, livst_pig, livst_chick, livst_egg, livst_milk` → EXACT (sets.gms:233) ✓
- `w` water supply `rainfed, irrigated` (sets.gms:241) ✓
- `nutrients` `dm, ge, nr, p, k` → EXACT (sets.gms:288-289) ✓
- `land` 7-pool grouping (crop/past agricultural; forestry/primforest/secdforest forest; urban/other) → matches `/ crop, past, forestry, primforest, secdforest, urban, other /` (sets.gms:251) ✓
- `ac` forest age classes "5-year intervals" → ac0...ac300, acx (sets.gms:269-275) ✓
- `emis_source` (sets.gms:302) ✓

### Section 4.2 — complete module list (46 modules)
`ls -d modules/*/` returns exactly 46 numbered module dirs; the doc's named list matches all directory names including `71_disagg_lvst` ✓ (cross-checked against modules/include.gms includes 12-57).

### Section 5.2 — time-step / intersolve mechanism
Verified against core/calculations.gms (loop at 36-102) and modules/15_food/anthro_iso_jun22/intersolve.gms:
- start + preloop run ONCE before loop (calculations.gms:13-15, before loop at 40) ✓
- ct/pt set (43-45), presolve_ini (52), presolve (54) ✓
- `sm_intersolve=0` before while (57); while(sm_intersolve=0) (59); load_gdx inside loop (62); solve (76); `sm_intersolve=1` unconditional after solve (79); intersolve (81) ✓
- postsolve (87), Execute_Unload "fulldata.gdx" (92), clear ct/pt + save restart (95-99) ✓
- Note default `s15_elastic_demand=0` cited at `config/default.cfg:414` ✓ and `modules/15_food/anthro_iso_jun22/input.gms:66` ✓ (both verified exact)
- `s15_maxiter=10` cited at input.gms:70 → exact ✓ (also default.cfg:422)
- Module 15 resets sm_intersolve to 0 only when elastic+unconverged → intersolve.gms:125 `sm_intersolve=0` under `if (s15_elastic_demand = 1 ...` (line 30) and convergence/iter guard (line 121) ✓

### Section 7 — model definition + solver
- `model magpie / all - m15_food_demand /;` (main.gms:279) → EXACT; "all equations except food demand model" ✓ (m15_food_demand block declared in 15_food declarations.gms)
- Solver options "lines 281-287" → iterlim=1000000, reslim=1000000, sysout=Off, limcol=0, limrow=0, decimals=3, savepoint=1, all at main.gms:281-287 → EXACT (7/7 values + line range) ✓

### Section 9.3 — dynamic set pattern
`h2(h) = yes; i2(i) = yes; j2(j) = yes;` → EXACT (sets.gms:126-128) ✓

### Section 10 — config globals
- `$setglobal land landmatrix_dec18` (main.gms:194) ✓; `$setglobal yields managementcalib_aug19` (main.gms:198) ✓
- `$setglobal c_timesteps coup2100` (main.gms:182) ✓; `$setglobal c_past till_2015` (main.gms:183) ✓
- Default optimization realization = `nlp_apr17` (config/default.cfg:2282) ✓; default uses `option nlp = conopt4` (nlp_apr17/solve.gms:14)

### Section 11 — dependency chains
Pedagogical "→" chains; directionally defensible (interfaces exist: 73_timber↔32_forestry, 32_forestry↔35_natveg, 56_ghg_policy reads vm_carbon_stock). Not precise interface-set claims, so not graded for completeness.

---

## Bugs Found
**None confirmed.** No claim contradicts code with reproducible evidence at a severity warranting a doc edit.

---

## Deferred (uncertain / not code-verifiable against in-repo ground truth)

1. **Section 6, line 243 — `x_` "Critical output parameters" prefix.** Verified UNUSED in current develop: `grep -rEl 'xm_[a-z]|x[0-9][0-9]_[a-z]' modules/ core/` returns zero files (exit 0, no output), cross-checked with positive control (`vm_[a-z]` regex correctly finds core/macros.gms). HOWEVER, MAgPIE's canonical naming convention lives in the upstream goxygen / model-coding-etiquette standard, which is NOT in this repo — `x` may be a documented-but-presently-unused prefix letter. I cannot confirm the claim is WRONG (only that no `x_` identifier currently exists in .gms code). Recording an edit here risks a false positive against the official standard. NOT flagged as a bug.

2. **Section 6, line 242 — `o_` "Output parameters" prefix.** The actual output-object family in code is `ov_` (output variable, 1251 files), `oq_` (output equation), and `o##_` (e.g., `o15_kcal_regr_initial`). Bare `o_` (no module number, no v/q) is unused. But Section 6 is describing the GENERAL prefix grammar (single letters), and `o` is the legitimate root of the o-family. Same upstream-convention uncertainty as `x_`. Convention-list imprecision at most (Informational); not confirmed wrong vs code. NOT flagged.

3. **Section 5.2, line 224 — "(80_optimization → CONOPT/IPOPT)".** Default realization `nlp_apr17` uses `conopt4` (solve.gms:14); `nlp_ipopt` is a separate non-default realization. Listing both as the solver family is loosely correct (both NLP solvers are available) and the default IS conopt-family. Not misleading enough to flag.

4. **Section 2.1 "Module Setup (lines 193-253)".** Setup spans 193-252; `END MODULE SETUP` at 254; line 253 blank. Off-by-one on trailing blank; effectively correct. Informational; not worth an edit.

5. **Time loop locality.** Section 2.1 step 12 "Time Loop Execution" is listed in the main.gms sequence, but the loop physically lives in `core/calculations.gms:40-102` (reached via the main.gms:295 include). The doc presents a logical flow, not a literal "loop is in main.gms" claim. Acceptable; not flagged.

---

## Methodology notes
- Grep guard applied: a false-negative on `vm_yld` (caused by an rg `-o` flag rendering artifact) was caught and corrected with plain grep — `vm_yld` IS declared at modules/14_yields/managementcalib_aug19/declarations.gms:26. The doc does not name `vm_yld`, so no impact, but it confirms the grep-guard discipline was necessary.
- All absence claims (`x_`, `o_`, `xm_`) confirmed by two methods + positive control before treating as absent.
- Bash tool truncated multi-section output after blank lines in several calls; re-ran isolated probes to confirm (default.cfg:2282 optimization, intersolve/solve locations, solver option values).
