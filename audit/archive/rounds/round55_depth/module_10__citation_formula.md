# Round 55 depth audit — module_10.md — lens: citation_formula

**Target**: `modules/module_10.md`
**Ground truth**: `/private/tmp/magpie_develop_ro` @ `0d7ebeb9037c675f8e6e4c9765ff31f1c7047792` (develop HEAD)
**Realization**: `landmatrix_dec18` (only realization; `cfg$gms$land <- "landmatrix_dec18"` confirmed in config/default.cfg)
**Role map**: `audit/integrated/depth_rolemap.json`

## Verdict: ACCURATE (one Minor completeness finding)

This doc is exceptionally faithful. All 7 equation formulas are reproduced verbatim from `equations.gms`, every file:line citation lands in-range on the claimed token, and every affirmative interface-variable attribution matches the role map exactly (confirmed by both-endpoints grep). One Minor finding: the pervasive "provides to / affects 15 modules" centrality count omits the three modules that consume `pcm_land` only (13_tc, 44_biodiversity, 56_ghg_policy), even though the doc lists `pcm_land` as a provided interface variable and enumerates those consumers elsewhere.

---

## Citations verified (all PASS)

Equations (formula fidelity — exact match to code):
- Eq1 `q10_land_area` doc:39-41 vs `equations.gms:13-15` — PASS
- Eq2 `q10_transition_to` doc:54-57 vs `equations.gms:19-21` — PASS
- Eq3 `q10_transition_from` doc:68-71 vs `equations.gms:23-25` — PASS
- Eq4 `q10_landexpansion` doc:82-86 vs `equations.gms:30-33` — PASS
- Eq5 `q10_landreduction` doc:97-101 vs `equations.gms:35-38` — PASS
- Eq6 `q10_cost` doc:113-116 vs `equations.gms:42-44` (incl. `* 1` multiplier) — PASS
- Eq7 `q10_landdiff` doc:128-132 vs `equations.gms:50-54` — PASS

Structural citations:
- module.gms:10-14 @description quote — exact match — PASS
- `land` set `core/sets.gms:250-251` (7 pools crop,past,forestry,primforest,secdforest,urban,other) — PASS
- subsets `core/sets.gms:253-263` (land_ag 253-254, land_timber 256-257, land_forest 259-260, land_natveg 262-263) — all in range, members correct — PASS
- declarations.gms:14-24 (6 variables: vm_landdiff + 5 positive) — PASS
- declarations.gms:8-12 (3 parameters) — PASS; pcm_land at declarations.gms:11 — PASS
- start.gms:8 `pm_land_start(j,land)=f10_land("y1995",j,land)` — PASS
- postsolve.gms:9 `pcm_land(j,land)=vm_land.l(j,land)` — PASS
- input.gms:8-11 / :16 (negative→0) / :19-23 / :25-29 — PASS (doc snippets omit `$ondelim/$offdelim`, harmless simplification)
- sets.gms:12-13 side layers (6 members) — PASS
- presolve.gms:10-23 restrictions (fx at 13,16,17,20; up Inf at 21) — PASS
- realization.gms:11 "@limitations ... only accounts for net land use transitions" — PASS
- "~292 lines" — exact (52+54+29+64+25+22+12+20+14 = 292 across the 9 realization .gms) — PASS

Attribution (role map + both-endpoints grep):
- vm_land direct consumers (10): 22,29,30,31,32,34,35,50,58,59 — matches role map read_by exactly — PASS
- "11/14/39/71/80 contain zero `vm_land(`" — CONFIRMED by grep (positive control 30_croparea hits) — PASS
- vm_landexpansion readers 35,39,58,59; vm_landreduction readers 39,58 — matches role map — PASS
- pcm_land 12 direct consumers incl. 13_tc, 44_biodiversity, 56_ghg_policy — CONFIRMED (13 endo_jan22 presolve.gms:9-10,40; 44 default bii_target preloop.gms:15; 56 price_aug22 preloop.gms:10) — PASS
- DEPENDS ON: vm_landdiff_forestry (declared 32_forestry), vm_landdiff_natveg (declared 35_natveg) — role map confirms M10 reads both — PASS
- Full PROVIDES-TO table (59,29,35,58,32,39,11,14,22,30,31,34,50,71,80 with per-var lists) — every cell matches role map — PASS
- default c200 resolution (cellular input "...c200...") — PASS

Note on module 44: default realization is `bii_target` (config/default.cfg `cfg$gms$biodiversity <- "bii_target"`), which DOES read pcm_land (preloop.gms:15). The `bv_btc_mar21` realization marks it "not used" — but that is the non-default. Doc's attribution is correct for the default.

---

## BUG-1 (Minor, set_membership) — "provides to 15 modules" undercounts pcm_land-only consumers

**doc_line**: module_10:789 (also 13, 14, 295, 763, 791, 861)

**Claim**: "**Provides to**: 15 modules (11, 14, 22, 29, 30, 31, 32, 34, 35, 39, 50, 58, 59, 71, 80)" and repeatedly "Changes to this module affect **15 other modules**".

**Reality**: `pcm_land` is declared in M10 (declarations.gms:11), populated in M10 (postsolve.gms:9), and listed by this same doc in the "Provided to Other Modules" interface table (line 891). Its consumers include **13_tc, 44_biodiversity, 56_ghg_policy**, which appear in NONE of the other module-10 variables' reader sets. So the true set of modules receiving a module-10-provided interface variable is 18 (the 15 + {13, 44, 56}), not 15.

**Evidence**:
- role map pcm_land read_by = [10,13,22,29,31,32,34,35,44,56,58,59,71]; vm_land/exp/red/cost/lu/pm_land_start/pm_land_hist/landdiff reader union = {11,14,22,29,30,31,32,34,35,39,50,58,59,71,80}. Set difference contributed only by pcm_land = {13,44,56}.
- grep confirms all three read pcm_land in their DEFAULT realizations (13_tc endo_jan22, 44_biodiversity bii_target, 56_ghg_policy price_aug22).

**Mitigation / why Minor**: the doc explicitly documents pcm_land's 12 consumers (incl. 13/44/56) in prose at lines 315-318 and 891, so a careful reader is not misled into a broken action; the "15" is a count/framing inconsistency, not a false attribution. Tie-breaker (§1) pulls Major→Minor.

**Proposed fix**: reconcile the count — either state "provides to 18 modules" (adding 13_tc, 44_biodiversity, 56_ghg_policy via pcm_land) in the centrality/impact lines (13-14, 295, 789, 791, 861), or explicitly scope the "15" as "modules receiving a non-`pcm_land` allocation variable; `pcm_land` adds 3 more (13, 44, 56) for 18 total downstream dependents."

---

## Deferred (not code-verifiable in this worktree; no edit proposed)

1. **Residual "LUH2" mentions vs the doc's own LUH3 correction.** Lines 363, 365, 771 still say "LUH2 Historical Data / LUH2 0.5° data", while the Data Sources section (lines 223-229) corrected the vintage to LUH3 with madrat provenance and flags vintage as preproc-owned. This is a doc-internal inconsistency, but the LUH2-vs-LUH3 vintage is NOT determinable from the develop GAMS code (only the side-layer set is code-named `luh2_side_layers10`, sets.gms:12); route to PREPROC_AGENT. Worth a maintainer reconciliation but not asserted as a confirmed code bug.
2. **"Rank: 2nd most depended-upon module (after 09_drivers)"** (line 277) and **"Reality: 67,420 original 0.5° cells"** (line 413) and **"249 ISO countries"** (line 265) — require cross-module centrality computation / preproc constants not verifiable from this worktree.
3. **`detailed_module_analysis.txt:35-65`** (line 273) — internal agent artifact, not code ground truth.
