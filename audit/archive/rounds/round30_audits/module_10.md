# Audit Report: Module 10 — vm_land / vm_landexpansion / vm_landreduction consumers + q10_land conservation

**Round**: 30
**Question** (anchored on `modules/module_10.md`): In MAgPIE's default land realization, list the consumers of `vm_land` and the consumers of `vm_landexpansion` and `vm_landreduction`, and explain how `q10_land` enforces land conservation. Cite file:line.
**Ground truth worktree**: `/tmp/magpie_develop_ro` (develop, read-only)
**Auditor**: Opus

---

## Overall Verdict: ACCURATE
## Accuracy Score: 10/10

Zero answer-level bugs against code. All three consumer lists are an exact match to the code. All equation/variable names and all file:line citations verified correct in current develop. The answer correctly preserved the set-based `sum(land, ...)` form (did NOT repeat the R16 expanded-enumeration fabrication) and correctly applied MANDATE-17 (39_landconversion consumes expansion/reduction but NOT `vm_land` itself). Two loose "Use"-column characterizations and one input-provenance parenthetical are Informational, not scored.

**One LATENT doc bug recorded** (rubric §1.5, `doc_error_answerer_beat_it`): `module_10.md` lines 306/312/313 attribute `vm_land` consumption to 14_yields / 71_disagg_lvst / 80_optimization, which the code contradicts (and which line 318 of the same doc also contradicts). The answer beat it; doc gets fixed regardless.

---

## Verified Claims (correct)

### Realization / default (MANDATE 8, 3)
- `landmatrix_dec18` is the ONLY realization and the default.
  - Evidence: `ls /tmp/magpie_develop_ro/modules/10_land/` → only `landmatrix_dec18/` + `input/`; `config/default.cfg:232` `cfg$gms$land <- "landmatrix_dec18"  # def = landmatrix_dec18`. ✓

### vm_land consumers — 10 modules (MANDATE 13)
- Answer list: 22, 29, 30, 31, 32, 34, 35, 50, 58, 59.
- Code ground truth (active realizations, excluding `not_used.txt`):
  `grep -rln 'vm_land\b' .../modules/ | grep -v /10_land/ | grep -v not_used` →
  **22, 29, 30, 31, 32, 34, 35, 50, 58, 59** (10). **EXACT MATCH.** ✓
  - Cross-checked with both `rg` and `grep`; both agree.
  - Spot-verified genuine reads: M34 `vm_land.fx(j,"urban")` + `vm_land(j2,"urban")` (`modules/34_urban/exo_nov21/presolve.gms:11`, `equations.gms:18,21,31,35`); M22 `vm_land.lo(j,"crop")` (`modules/22_land_conservation/area_based_apr22/presolve_ini.gms:86,97,108`); M50 `vm_land(j2,"past")`, `vm_land(j2,land)` (`modules/50_nr_soil_budget/macceff_aug22/equations.gms:79,90`); M58 via `m58_LandMerge(vm_land,...)` (`modules/58_peatland/v2/equations.gms:23`).
  - M58 default realization confirmed `v2` (`config/default.cfg:1853`), so the `v2` match is active.

### vm_landexpansion consumers — 4 modules
- Answer list: 35, 39, 58, 59. Code: **35, 39, 58, 59.** EXACT MATCH. ✓
  - M35 `q35_max_forest_establishment` (`modules/35_natveg/pot_forest_may24/equations.gms:197`) + `q35_other_regeneration` (line 222); M39 `modules/39_landconversion/calib/equations.gms:13`; M58 `modules/58_peatland/v2/equations.gms:28`; M59 `vm_landexpansion(j2,"crop")` `modules/59_som/cellpool_jan23/equations.gms:91`.
  - M39 default = `calib` (`config/default.cfg:1267`); M59 active = `cellpool_jan23` (the `static_jan19/not_used.txt` hit is correctly excluded).

### vm_landreduction consumers — 2 modules
- Answer list: 39, 58. Code: **39, 58.** EXACT MATCH. ✓
  - M39 `modules/39_landconversion/calib/equations.gms:14`; M58 `modules/58_peatland/v2/equations.gms:31`.
- Answer's note "Modules 35 and 59 consume `vm_landexpansion` but NOT `vm_landreduction`": VERIFIED. ✓

### MANDATE 17 (direct vs transitive)
- Answer: "39_landconversion consumes `vm_landexpansion`/`vm_landreduction` — NOT `vm_land` itself"; "11/14/71/80 contain zero `vm_land(` references."
  - `grep -rln 'vm_land\b' .../modules/39_landconversion/` → exit 1 (zero). ✓
  - 14_yields, 71_disagg_lvst, 80_optimization: zero `vm_land` (positive control: each has `vm_*` refs, so grep works in-dir — `14_yields/managementcalib_aug19/equations.gms`, `71_disagg_lvst/foragebased_jul23/equations.gms`, `80_optimization/module.gms` all match `vm_`). ✓
  - 11_costs: zero `vm_land`, positive control `vm_cost` present in `11_costs/default/equations.gms`. ✓

### q10 conservation mechanism (MANDATE 1, 7, 16)
- `q10_land_area(j2) .. sum(land, vm_land(j2,land)) =e= sum(land, pcm_land(j2,land));`
  - `modules/10_land/landmatrix_dec18/equations.gms:13-15`. EXACT. ✓ Answer reproduced verbatim.
- `=e=` strict equality, LHS optimization var, RHS carry-forward parameter `pcm_land`: all correct. `pcm_land` declared `modules/10_land/landmatrix_dec18/declarations.gms:11` ("Land area in previous time step including possible changes after optimization"). ✓
- Recursive carry-forward `pcm_land(j,land) = vm_land.l(j,land);` at `modules/10_land/landmatrix_dec18/postsolve.gms:9`: VERIFIED (line 9 exact). ✓
- 7 land pools `/crop, past, forestry, primforest, secdforest, urban, other/` at `core/sets.gms:250-251`: VERIFIED. ✓ Answer's expanded enumeration matches and is correctly attributed to `cross_module/land_balance_conservation.md:106-113` (NOT presented as the code's literal form — the code `sum(land,...)` form is shown first). Does NOT trigger the R16 Major anchor.
- Transition equations:
  - `q10_transition_to` (`equations.gms:19-21`): `sum(land_from, vm_lu_transitions(j2,land_from,land_to)) =e= vm_land(j2,land_to)` — answer "inflows into each land type equal its current area". VERIFIED. ✓
  - `q10_transition_from` (`equations.gms:23-25`): `sum(land_to, vm_lu_transitions(j2,land_from,land_to)) =e= pcm_land(j2,land_from)` — answer "outflows ... equal its previous area". VERIFIED. ✓
- 1995 initialization: `pm_land_start(j,land) = f10_land("y1995",j,land)` then `pcm_land = pm_land_start` (`start.gms:8,11`). Answer's "1995 ... total per cell carried forward" — VERIFIED on the year. ✓
- Question said "q10_land"; no such equation exists (only `q10_land_area`, `q10_landexpansion`, `q10_landreduction`, etc. — `declarations.gms:27-33`). Answer correctly resolved to `q10_land_area` and did NOT fabricate a `q10_land`. ✓

### Mechanical checks
- M1 file:line citations present ✓ | M2 realization stated (only realization) ✓ | M3 prefixes valid (all `vm_`/`pcm_`/`q10_`) ✓ | M4 epistemic badge present (🟡) ✓ | M5 tier matches (🟡 documented + grep-recompute note) ✓ | M6 closing source statement present ✓.

---

## Bugs Found (answer-level)

**None at Minor or above.** Two Informational observations (not scored, listed for completeness):

- **INFO-1 (Informational, style/framing)**: The 35_natveg "Use" cell reads "Secondary forest regrowth accounting on newly expanded natveg." The actual `vm_landexpansion` uses in M35 are (a) a forest-establishment ceiling, `q35_max_forest_establishment` constrains `sum(land_forest, vm_landexpansion)` to remaining potential forest area (`equations.gms:197-201`), and (b) `q35_other_regeneration` adds `vm_landexpansion(j2,"other")` to *other*-land regeneration (`equations.gms:222`). "Secondary forest regrowth" is a loose label; the module is correctly identified as a consumer, and the framing is in the right domain. Root cause: `answerer_style_or_framing`.

- **INFO-2 (Informational, framing)**: "the 1995 LUH2 total per cell, carried forward at each 5-year step." The "5-year step" is a default-timestep assumption (MAgPIE timesteps are configurable and not uniformly 5 yr). The "LUH2" data-version label is not verifiable from GAMS (`f10_land` is preprocessed input); the companion doc references LUH3 for related urban data (`land_balance_conservation.md:85`), so "LUH2" may be stale. Neither affects the conservation mechanism. Root cause: `answerer_style_or_framing` (provenance hedge would have been cleaner).

`raw_severity_weighted = 4*0 + 2*0 + 1*0 = 0` → **score = 10**.

---

## Latent Doc Bugs (doc_errors_latent[] — fixed regardless of score, rubric §1.5)

### LATENT-1 — module_10.md consumer table attributes `vm_land` to 14/71/80 (phantom consumers)

- **Severity**: Major (by future-reader harm; see tier rationale below)
- **Class**: 15 (latent doc error, answer beat the doc)
- **Root cause**: `doc_error_answerer_beat_it`
- **Doc location**: `modules/module_10.md:306` (`14_yields | vm_land (1) | Yield calculations`), `:312` (`71_disagg_lvst | vm_land (1) | Livestock disaggregation`), `:313` (`80_optimization | vm_land (1) | Objective function`).
- **Code reality**: 14_yields, 71_disagg_lvst, 80_optimization each contain **zero** `vm_land` references in any `.gms` file. Verified twice (grep + rg) with positive controls (all three DO match `vm_*`, so the search works in-dir).
  - `grep -rln 'vm_land\b' .../modules/14_yields/` → exit 1; same for 71, 80.
- **Self-contradiction inside the doc**: `module_10.md:318` already states "11/14/39/71/80 contain zero `vm_land(` references in any `.gms` file (origin/develop ee98739fd)", and `:315-316` gives the correct 10-module direct-consumer list. The table at 306/312/313 contradicts the prose 2-3 lines below it.
- **Why the answer scored 10 anyway**: the answerer followed the line-315/318 list + `modification_safety_guide.md:54-55` (both correct) and explicitly placed 14/71/80 in the "affected only indirectly" category. It beat the bad table.
- **Tier rationale**: A reader doing a `vm_land` refactor who trusts the table would chase 3 phantom consumers (wasted effort) — this is the *inverse* of the R20 anchor (R20 = missing real consumers, which is strictly worse). Phantom-add is less damaging than omission, and the same doc self-corrects 2 lines later, so a careful reader catches it. Tie-breaker between Critical (R20-style wrong-consumer-set) and Minor pulls to **Major**. `tier_uncertainty: true`.
- **Note**: The `modification_safety_guide.md` table (10/4/2 counts, lines 46-49, 54-55) is CORRECT vs code; only `module_10.md`'s own §5 table is wrong. Fix: the table at 306/312/313 should move 14/71/80 out of the `vm_land` column (they consume other M10 interface vars, not `vm_land`), consistent with line 318. This makes the table agree with its own prose.

---

## Missing Nuances (non-bugs)

- The answer does not mention that M58's consumption routes through the `m58_LandMerge` macro (combining `vm_land`/`vm_landexpansion`/`vm_landreduction` with their `_forestry` counterparts), but this is detail beyond the question's scope; the consumer identification is correct.
- The answer's "Module 22 floors protected land" via `vm_land` is slightly loose: M22 reads `vm_land.lo(j,"crop")` (the existing lower bound) to compute available conservation area rather than itself setting the floor on `vm_land`. M22 is correctly listed as a consumer; the characterization is in the right ballpark.

---

## Summary

The answer is fully correct at the level it will be acted upon: all three consumer sets exactly match a fresh code grep (10 / 4 / 2 modules), every equation and variable name is faithful to `declarations.gms`, and every file:line citation (`equations.gms:13-15/19-21/23-25`, `postsolve.gms:9`, `core/sets.gms:250-251`, `config/default.cfg:232/1853/1267`) is verified in current develop. It correctly preserved the set-based equation form and correctly applied the direct-vs-transitive distinction (MANDATE 17). Score **10/10**.

One latent doc bug is recorded and must be fixed this session: `module_10.md`'s §5 consumer table (lines 306/312/313) lists 14/71/80 as `vm_land` consumers, which the code contradicts and which the same doc contradicts 2-3 lines later (line 318). This is the G2-pattern blind spot — the answer beat it, so it is invisible to the score, but a future answerer trusting the table could regress. Fix the table to match line 318.
