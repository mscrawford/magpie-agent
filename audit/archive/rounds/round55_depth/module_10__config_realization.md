# Round 55 Depth Audit — module_10.md — lens: config_realization

**Target**: `modules/module_10.md`
**Ground truth**: `/private/tmp/magpie_develop_ro` (develop HEAD `0d7ebeb90`)
**Lens**: config_realization (defaults, cfg$gms switches, realization names, default-first framing)
**Date**: 2026-07-16

## Lens summary

The config/realization core of this doc is **clean**:
- Realization name `landmatrix_dec18` — correct. `ls modules/10_land/` shows only `input/` and `landmatrix_dec18/`. Doc line 4/25 correctly states "only realization".
- Default switch `cfg$gms$land <- "landmatrix_dec18"` (config/default.cfg:232) — matches. Single realization, so no default-vs-alternative framing hazard.
- Default spatial resolution "c200" (doc:224, 412) — matches the default cellular input `...cellularmagpie_c200_...` (config/default.cfg:26).
- Parameter defaults: 1 USD/ha transition cost (equations.gms:44 `* 1`), y1995 start (start.gms:8), t_ini10 = {1995,2000,2005,2010,2015} (sets.gms:9-10) — all correct.

Equation line citations (equations.gms 13-15, 19-21, 23-25, 30-33, 35-38, 42-44, 50-54), declarations citations (8-12 params, 14-24 vars), presolve restrictions (13-21 within the 10-23 @code block), `land` set (core/sets.gms:250-251) and subsets (253-263), postsolve.gms:9 recursion — all verified accurate.

Interface attribution against `audit/integrated/depth_rolemap.json` + both-endpoints greps: the per-variable consumer sets are all correct (vm_land 10 consumers; vm_landexpansion 35/39/58/59; vm_landreduction 39/58; vm_lu_transitions 29/35/59; vm_cost_land_transition 11; vm_landdiff 80; pm_land_start 14/32/59/71; pm_land_hist 29; pcm_land 12 incl. 13/44/56). The "zero vm_land refs in 11/14/39/71/80" claim (line 318) verified true in BOTH `vm_land(` and `vm_land.` forms.

## Bugs

### BUG 1 — Major — set_membership — module_10.md:791 (also :14, :789)

**Claim**: "Changes to Module 10 affect **15 modules** - most critical module for testing" / line 789 enumerates "Provides to: 15 modules (11, 14, 22, 29, 30, 31, 32, 34, 35, 39, 50, 58, 59, 71, 80)".

**Reality**: M10 also owns interface parameter `pcm_land` (declared declarations.gms:11, populated postsolve.gms:9), which is read by **13_tc, 44_biodiversity, 56_ghg_policy** — three modules absent from the "15" list and reading NONE of M10's other interface vars. True distinct-dependent count = **18**. The doc's own §5 (lines 316-318) and Interface table (line 891) correctly state pcm_land has "12 direct consumers including 13_tc, 44_biodiversity, 56_ghg_policy" — so the aggregate "15 / affects 15 modules" contradicts the doc's own detailed breakdown. A maintainer following the Modification Safety block (lines 858-869, "Changes affect 15 downstream modules; Comprehensive validation of all dependents") using only the summary figure would omit testing 13/44/56 for pcm_land-mediated effects. (cf. rubric R20 anchor: wrong/incomplete consumer set → Critical-prone when a refactor misses modules; downgraded here to Major because the correct full breakdown IS present in §5.)

**Evidence**:
- 13_tc/endo_jan22/presolve.gms:9 `pc13_land(i,"pastr") = sum(cell(i,j),pcm_land(j,"past"));`
- 44_biodiversity/bii_target/preloop.gms:15 `... pcm_land(j,land) * i44_biome_share(...)`
- 56_ghg_policy/price_aug22/preloop.gms:10 `pcm_carbon_stock(...) = fm_carbon_density(...)*pcm_land(j,land);`
- rolemap pcm_land.read_by = [10,13,22,29,31,32,34,35,44,56,58,59,71] (12 non-self); 13/44/56 have 0 files referencing any of vm_land/vm_landexpansion/vm_landreduction/vm_lu_transitions/vm_landdiff/pm_land_start/pm_land_hist.

**verify_cmd**: `rg -n 'pcm_land[.(]' modules/{13,44,56}_*/` → hits shown above; `rg -c 'vm_land\(|vm_landexpansion|vm_landreduction|vm_lu_transitions|vm_landdiff|pm_land_start|pm_land_hist' modules/{13,44,56}_*/` → 0 files each. Confirmed.

**Fix**: Reconcile the aggregate with §5. Either state total distinct dependents = 18, or scope "15" explicitly as "consumers of M10 decision variables + initialization parameters, excluding the 3 additional pcm_land-only consumers (13_tc, 44_biodiversity, 56_ghg_policy) listed in §5" — and update lines 14/791 blast-radius wording to 18 so impact analysis is complete.

### BUG 2 — Minor — citation — module_10.md:363 (also :365, :771)

**Claim**: "Initializes from **LUH2** Historical Data" (363); "Uses **LUH2** 0.5° data aggregated to 200 cells" (365); "Initialize from **LUH2** data (1995-2015 historical)" (771).

**Reality**: These three summary lines describe File 1 (`avl_land_t.cs3` → `f10_land`, input.gms:8-10) — the same historical-land source that doc line 223 **corrected to LUH3** (CMIP7 input4MIPs) on 2026-07-09 with a dated, sourced note. The summary sections were not updated in that correction, leaving an internal contradiction. (Line 239 "File 2: LUH2 Side Layers" is CORRECT and must stay — that file is literally `luh2_side_layers.cs3` / table `fm_luh2_side_layers`.)

**Evidence**: input.gms:8-10 (`f10_land` ← `avl_land_t.cs3`); doc-internal contradiction line 223 (LUH3, corrected) vs 363/365/771 (LUH2).

**verify_cmd**: `grep -n 'LUH2\|LUH3' modules/module_10.md` → line 223 LUH3 (corrected/sourced), lines 363/365/771 still LUH2. Data-source vintage is preproc-owned and NOT verifiable from the GAMS worktree, so confirmed=false on the vintage itself; the internal contradiction is reproducible.

**Fix**: Update lines 363, 365, 771 "LUH2" → "LUH3" to match the line-223 correction. Leave line 239 (File 2 side layers) unchanged.

## Deferred (not flagged — unverifiable or out-of-lens)

- Centrality "17 total connections / HIGHEST centrality" (line 13) vs "Rank #2 by centrality, after 09_drivers" (lines 276, 833) — internal tension, but the metric derives from `detailed_module_analysis.txt` (not verified) and is not a code-checkable quantity.
- "67,420 original 0.5° cells" (line 413) — grid/preproc fact, not GAMS-verifiable in the develop worktree.
- LUH3 vintage itself — preproc-owned (mrlandcore); route to PREPROC_AGENT. Only the doc-internal LUH2/LUH3 inconsistency is reported (BUG 2).
- `detailed_module_analysis.txt:35-65` citation (line 273) — referenced Phase-2 artifact not checked.
