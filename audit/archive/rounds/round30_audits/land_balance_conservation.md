# Audit Report: R30 — Land-area conservation in the default land realization

**Question (anchored on `cross_module/land_balance_conservation.md`)**: How does MAgPIE enforce land-area conservation in the default land realization? Cite the equation and the variable (`vm_land`), and explain which land types and modules can shift area while the regional total is conserved.

**Auditor**: Opus, semantic-validation flywheel R30
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree), `config/default.cfg`

---

## Overall Verdict: ACCURATE
## Accuracy Score: 10/10

raw_severity_weighted = 4·0 + 2·0 + 1·0 = 0 → score = max(0, 10 − 0) = **10**

This is one of the cleanest answers audited. Every equation name, variable name, file:line citation, set definition, default value, and cross-module mechanism I checked verified exactly against develop code. Zero confabulated identifiers.

---

## Mechanical checks (M1–M6)

| Check | Result | Evidence |
|---|---|---|
| M1 file:line citations present | ✓ | Full-path citations: `modules/10_land/landmatrix_dec18/equations.gms:13-15`, `postsolve.gms:9`, etc. |
| M2 active realization stated | ✓ | "Module 10's only realization, `landmatrix_dec18`" — verified as default at `config/default.cfg:232` (`cfg$gms$land <- "landmatrix_dec18"`). Module 10 has exactly one realization dir (`ls` confirms). |
| M3 variable prefixes valid | ✓ | `vm_land`, `pcm_land`, `v29_treecover`, `v32_land`, `v35_secdforest`, `vm_land_other`, `vm_lu_transitions` — all prefixes correct. |
| M4 epistemic badges present | ✓ | Closing 🟡 Documented block. |
| M5 confidence tier matches depth | ✓ | Tagged 🟡 (docs), explicitly states "Raw GAMS source was not re-read this session" — honest and correct tier. |
| M6 closing source statement | ✓ | "drawn from `module_10.md` and `land_balance_conservation.md` … verified against `equations.gms`". |

All six pass.

---

## Verified Claims (correct against code)

1. **`q10_land_area` equation + citation** — `equations.gms:13-15`: `q10_land_area(j2) .. sum(land, vm_land(j2,land)) =e= sum(land, pcm_land(j2,land));`. Answer quotes this verbatim, including the set-based `sum(land, ...)` form (does NOT expand to member list — satisfies MANDATE 10, contrast the R16 anchor bug). ✓
2. **`=e=` strict equality, per-cell `j2`** — confirmed; answer correctly notes "applies per cell j, not per region — regional totals are conserved only as an aggregate consequence." ✓
3. **`pcm_land(j,land) = vm_land.l(j,land)` at `postsolve.gms:9`** — exact. ✓
4. **Seven land types at `core/sets.gms:250-251`** — `/ crop, past, forestry, primforest, secdforest, urban, other /` exact. ✓
5. **Pool → module mapping** — crop:29/30, past:31, forestry:32, primforest/secdforest/other:35, urban:34. The `=e=` definers in code: M29 defines crop, M32 defines forestry, M35 defines secdforest+other; M34 sets urban via regional `q34_urban_land`; M31 governs pasture via the `q31_prod` production constraint + presolve lower bound; primforest has no defining equation (one-way decline via transition restriction). All consistent. ✓
6. **Defining/constraint equations all exist with matching content**: `q29_cropland` (eq:11-12, `vm_land(j2,"crop") =e= sum((kcr,w), vm_area(j2,kcr,w)) + vm_fallow(j2) + sum(ac, v29_treecover(j2,ac))`); `q31_prod` (eq:16-18, `vm_prod =l= vm_land(j2,"past") * vm_yld(...)`); `q32_land` (eq:55-56, `vm_land(j2,"forestry") =e= sum((type32,ac), v32_land(...))`); `q35_land_secdforest` (eq:11); `q35_land_other` (eq:13); `q34_urban_land(i2)` (eq:30-31, regional `=e=`). ✓
7. **`type32 = {aff, ndc, plant}`** — `32_forestry/dynamic_may24/sets.gms:16-17`. Answer wrote `{plant, ndc, aff}` (same members). ✓
8. **`s34_urban_deviation_cost = 1e6 USD/ha`** — `34_urban/exo_nov21/input.gms:13` (`/ 1e+06 /`). ✓ (not exposed in default.cfg; input.gms is the canonical default for this non-exposed scalar — MANDATE 3 satisfied via the declaring file).
9. **20 tC/ha secdforest maturation threshold** — `35_natveg/pot_forest_may24/presolve.gms:111,117`. ✓
10. **Transition restrictions** — `presolve.gms:13` (no primforest→forestry), `:16-17` (no primforest/secdforest→other), `:20` (all `land_from`→primforest fixed 0), `:21` (primforest→primforest re-opened to Inf). Answer's "primforest one-way decline, except primforest→primforest persistence" and "no land can enter this pool" are exact. The cited range `presolve.gms:10-23` brackets the `@code`(10)…`@stop`(23) annotation block; defensible. ✓
11. **`q10_transition_to` (eq:19-21) and `q10_transition_from` (eq:23-25)** — exact citations and content (`sum(land_from, vm_lu_transitions) =e= vm_land(j2,land_to)` and `sum(land_to, ...) =e= pcm_land(j2,land_from)`). ✓
12. **"`vm_land` consumed directly by 10 modules"** — VERIFIED EXACTLY 10. Whole-tree `rg -ln 'vm_land\b'` over all `*.gms` (excluding M10) yields: **22, 29, 30, 31, 32, 34, 35, 50, 58, 59**. Positive control: `vm_land_other\(` resolves to a DIFFERENT set (35, 59), proving the grep distinguishes the look-alike. M22 reads `vm_land.lo(j,"crop")` (`area_based_apr22/presolve_ini.gms:86,97,108`); M58 reads `vm_land` via macro `m58_LandMerge(vm_land,...)` (`v2/equations.gms:23`); M50 reads `vm_land(j2,"past")` and `vm_land(j2,land)` (`macceff_aug22/equations.gms:79,90`); M59 reads `vm_land` (`cellpool_jan23/equations.gms:33,63`). All 10 are genuine DIRECT consumers (MANDATE 13 + 17 satisfied). ✓
13. **`pm_max_forest_est` interface M35 → M32** — computed in M35 (`pot_forest_may24/preloop.gms:63`, `postsolve.gms:22`), declared the interface parameter (`realization.gms:16`). Answer's "forestry expansion constrained by maximum forest establishment potential provided by Module 35" is correct. ✓
14. **All variable names exist** — `v29_treecover`, `vm_fallow`, `vm_area`, `v32_land`, `v35_secdforest`, `vm_land_other`, `pcm_land`, `vm_lu_transitions`, `vm_landexpansion`, `vm_landreduction` all present in code. Zero confabulation. ✓
15. **"19 crop types"** — corroborated: the `kall` crop members (`core/sets.gms:230-231`) are tece, maiz, trce, rice_pro, soybean, rapeseed, groundnut, sunflower, oilpalm, puls_pro, potato, cassav_sp, sugr_cane, sugr_beet, others, cottn_pro, foddr (17) + begr, betr (2) = 19. ✓
16. **primforest can only decrease "as a source for crop, past, secdforest, or urban"** — presolve blocks primforest→{forestry, other, primforest-as-target}; leaves primforest→{crop, past, secdforest, urban} open. Exactly the four listed. ✓

---

## Bugs Found

**None.** No Critical, Major, Minor, or Informational content bugs in the answer.

---

## Latent doc bugs (rubric §1.5 — recorded independent of answer score)

The answer scored 10 and relied almost entirely on doc claims that I confirmed against code. Two doc items relayed by the answer warrant recording, but neither is a hard doc-vs-code contradiction:

### LATENT-1 (soft, NOT a hard doc error): "LUH3" urban-data provenance
- **Doc**: `cross_module/land_balance_conservation.md:85` ("prescribed by LUH3 data") and `:342` ("Regional total fixed to LUH3 data"). Answer relayed as "forces the regional sum to match LUH3 input data."
- **Code reality**: `34_urban/exo_nov21/input.gms:16-18` reads `f34_urbanland.cs3` indexed by `urban_scen34` SSP scenarios (`preloop.gms:11,13`, default `SSP2`). GAMS is **silent** on the LUH version — the LUH2-vs-LUH3 provenance is a preprocessing-layer (mr* package) fact, not resolvable in the consuming GAMS code.
- **Disposition**: NOT scored as a doc error (no GAMS contradiction). Flag for the preproc-agent to confirm the urban land source is LUH3 (vs LUH2). Note the parallel to the immutable R16 Minor anchor where module_34 doc said LUH2 but config defaulted to LUH3 — the version label for urban data has a history of ambiguity. **Recommend**: add a one-line "(provenance per preproc-agent; GAMS reads `f34_urbanland.cs3`)" hedge to the doc rather than asserting LUH3 as GAMS-verified.

### LATENT-2 (doc-internal inconsistency, NOT relied on by the answer's wording): centrality "HIGHEST" vs "Rank #2"
- **Doc**: `modules/module_10.md:13` ("HIGHEST centrality in MAgPIE") vs `module_10.md:833` ("As Central Hub (Rank #2 by centrality)"). `land_balance_conservation.md:230` says "Highest in MAgPIE."
- **Code reality**: graph-topology metric, not directly grep-verifiable; the checkable sub-claim ("`vm_land` consumed by 10 modules") is correct (see Verified #12). The "17 connections (2 inputs, 15 outputs)" figure is internally consistent across `module_10.md:13` and `land_balance_conservation.md:230`.
- **Disposition**: NOT a doc-vs-code error and NOT load-bearing for this answer (the answer said "highest connectivity (17 connections)"; it did not invoke the conflicting "Rank #2" line). Recorded only as a doc-hygiene note: reconcile `module_10.md:13` vs `:833` so a future answerer can't relay the wrong one.

No latent bug rises to the §1.5 `doc_error_answerer_beat_it` bar (which requires a load-bearing doc claim that is WRONG vs code). The doc here was correct on every load-bearing claim I checked.

---

## Missing Nuances (non-scoring)

- **Urban cellular fixing in t=1**: `34_urban/exo_nov21/presolve.gms:10-16` hard-FIXES `vm_land.fx(j,"urban")` cellularly in the first timestep (`ord(t)=1`), then relaxes to `lo=0, up=Inf` for optimization timesteps (steered by the regional `=e=` + 1e6 penalty). The answer's "regional sum forced, cell-level deviation costs make reduction impossible" framing is accurate for the optimization timesteps and matches the doc; the t=1 hard-fix is an extra detail neither doc nor answer mentions. Not a bug.
- **"Urban one-way sink (can only increase)"**: true under default monotone-SSP trajectories; strictly, urban tracks the prescribed `i34_urban_area` trajectory and would follow it down if it ever decreased. Matches the doc's framing; defensible simplification.
- **Within-natveg transition framing**: the answer says "no direct type-switching within the natural vegetation pools via the transition matrix." Code only fixes `primforest→other` and `secdforest→other` to 0; `primforest→secdforest` and `other→secdforest` are NOT blocked at the M10 matrix level (handled by M35 dynamics). The answer's hedge ("those are handled internally by Module 35 age-class dynamics") matches the doc (lines 201-207) and is a reasonable simplification, not a misstatement.

---

## Summary

The answer is faithful to the develop code on every load-bearing claim: equation `q10_land_area` and its exact set-based form, the `vm_land` variable, the seven-member `land` set, `pcm_land` recursion, all per-pool defining/constraint equations, the transition-matrix balance equations, the primforest one-way restriction, and — critically — the cross-module consumer count ("10 modules consume `vm_land`"), which I independently confirmed to be exactly 10 with a positive control against the `vm_land_other` look-alike. No confabulated names, no citation drift (every cited line verified in current develop), correct default realization, correct `s34_urban_deviation_cost` default. The closing epistemic tier (🟡 Documented, source not re-read) is honest and correctly chosen.

**Score: 10/10.** Two doc-hygiene items recorded (LUH3 provenance should be hedged/preproc-confirmed; reconcile module_10.md centrality "HIGHEST" vs "Rank #2") — neither is a doc-vs-code error and neither lowers the score.
