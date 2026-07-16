# Round 55 depth audit — module_10.md — lens: declare_populate

**Auditor vantage**: enter from the declaring/populating side. Verify which module DECLARES/POPULATES each interface var, and whether M10's equation bodies match the doc's described formulas.
**Ground truth**: `/private/tmp/magpie_develop_ro` @ `0d7ebeb90` (develop worktree).
**Role map**: `audit/integrated/depth_rolemap.json`.

## Verdict

Doc is unusually clean on this lens — heavy prior auditing shows. All 7 equation formulas match the code verbatim with correct line cites; all 9 interface-object declarations are correctly attributed to `10_land`; the `vm_land` 10-consumer set, `vm_landexpansion` {35,39,58,59}, `vm_landreduction` {39,58}, `vm_lu_transitions` {29,35,59}, and `pcm_land` 12-consumer count are all confirmed correct against both the role map AND both-endpoints ripgrep. Two real defects found (both Minor).

---

## Findings

### F1 (Minor, attribution_populate) — pcm_land co-populators 32/34/35 omitted

- **doc_line**: module_10.md:318 (also 209, 368-371, 891)
- **claim**: `pcm_land` "declared in `declarations.gms:11`, populated in `postsolve.gms:9`" — presents M10's postsolve as the sole population point. Code-Truth #8 (368-371): "Updates Land State Recursively (postsolve.gms:9)".
- **reality**: `pcm_land` is populated by M10 postsolve.gms:9 (full recursive update) AND overwritten in slices by three downstream modules each timestep:
  - `34_urban/exo_nov21/preloop.gms:17` → `pcm_land(j,"urban")`
  - `32_forestry/dynamic_may24/presolve.gms:101` → `pcm_land(j,"forestry")`
  - `35_natveg/pot_forest_may24/presolve.gms:39,131,137` → `pcm_land(j,"primforest"|"secdforest"|"other")`
- **role map**: `pcm_land.populated_by = ["10","32","34","35"]` — confirms co-population.
- **verify_cmd**: `grep -rn "pcm_land(" modules/{32,34,35}/*/ | grep "pcm_land(.*="` → returns the 5 slice-assignments above (confirmed).
- **assessment**: The doc makes no FALSE claim (M10 genuinely populates pcm_land at postsolve.gms:9), but the populate attribution is INCOMPLETE. Decision-relevant for a CRITICAL-centrality module: a reader modifying M10's postsolve pcm_land update would not learn that 32/34/35 reconcile their own pool slices in presolve. Per-slice-ownership MANDATE.
- **proposed_fix**: In the pcm_land descriptions (318, 209-210, 891) add: "M10 sets the full recursive update in postsolve.gms:9; modules 32 (forestry), 34 (urban), and 35 (natveg) then overwrite their own pool slices of pcm_land in their (pre)loop/presolve phases."

### F2 (Minor, citation) — LUH3 vintage correction not propagated to Code-Truth #7 / Summary

- **doc_line**: module_10.md:363, 365, 771
- **claim**: line 363 "Initializes from **LUH2** Historical Data"; line 365 "Uses **LUH2** 0.5° data aggregated to 200 cells"; line 771 "Initialize from **LUH2** data (1995-2015 historical)". All three describe File 1 = `f10_land`/`avl_land_t.cs3` (the historical land INITIALIZATION data).
- **reality**: The doc's own Section 4 (line 223) corrected this exact File-1 source on 2026-07-09: "Land-Use Harmonization 3 (**LUH3**) dataset ... (Corrected from 'LUH2') ... via calcLUH3". Line 229 also uses "LUH3 categories". So lines 363/365/771 are stale/self-contradictory — the correction was not propagated. (Line 239 "File 2: LUH2 Side Layers" is CORRECT and should stay: the code identifier is genuinely `fm_luh2_side_layers` / `luh2_side_layers10`.)
- **verify_cmd**: `grep -n "LUH2\|LUH3" module_10.md` → line 223 asserts LUH3 (corrected-from-LUH2) for File 1; lines 363/365/771 still say LUH2 for the same File-1 data (confirmed internal contradiction).
- **note on confirmation**: The vintage itself (LUH2 vs LUH3) is preproc-owned and gitignored (`.cs3`), NOT independently code-verifiable here. The bug is the un-propagated internal correction, which is directly reproducible by reading the doc. Fix propagates the doc's own established position.
- **proposed_fix**: Change "LUH2" → "LUH3" on lines 363, 365, 771 (File-1 historical-initialization references only; leave line 239 File-2 Side Layers as LUH2).

---

## Deferred (unverifiable / out of code-lens — no bug claimed)

- module_10.md:159/161 — secdforest ">20 tC/ha" / other "<20 tC/ha" carbon thresholds: not present in GAMS module 10; classification is preproc-owned (LUH/potnatveg). Could not verify from code; not chasing to avoid false positive.
- module_10.md:413 — "67,420 original 0.5° cells": preproc gridding claim, not code-verifiable in this module.
- module_10.md:13 vs 275 — "HIGHEST centrality" vs "2nd most depended-upon (after 09_drivers)": internal tension, but both derive from legacy `detailed_module_analysis.txt` (not in the code tree). Also "15 outputs": M10 actually provides to 18 modules once pcm_land-only consumers 13/44/56 are counted, but the doc footnotes those at line 318 — defensible definitional framing, not flagged.
- module_10.md:224 — "~200 cells (default c200)": config/resolution-dependent; not checked against a resolution setting.

## Positive confirmations (spot list)

- Equations q10_land_area/transition_to/transition_from/landexpansion/landreduction/cost/landdiff: formulas + line cites (13-15,19-21,23-25,30-33,35-38,42-44,50-54) all exact.
- Declarations: 6 vars + 3 params, cites declarations.gms:8-12 (params), 14-24 (vars) — correct; all declared in 10_land per role map.
- Sets: land (core/sets.gms:250-251), land_ag/land_timber/land_forest/land_natveg (253-263), t_ini10 (y1995-y2015), luh2_side_layers10 (sets.gms:12-13) — all correct incl. membership.
- presolve restrictions (13,16,17,20,21): all 5 doc claims correct, incl. "other->secdforest allowed", "primforest->primforest allowed".
- vm_land direct consumers (10): 22,29,30,31,32,34,35,50,58,59 — confirmed via role map + comma/paren/dot-form rg (58 reads via `m58_LandMerge(vm_land,...)`, invisible to `vm_land(`).
- pcm_land 12 direct consumers; vm_landexpansion/reduction/lu_transitions consumer sets; DEPENDS-ON {32,35} via vm_landdiff_forestry/natveg — all confirmed.
- Default realization: `cfg$gms$land <- "landmatrix_dec18"` (only realization) — correct.
