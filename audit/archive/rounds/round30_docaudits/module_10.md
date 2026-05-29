# Round 30 Doc Audit — module_10.md (Land Allocation & Transitions)

**Auditor**: Opus adversarial doc-auditor
**Target**: `modules/module_10.md`
**Ground truth**: `/tmp/magpie_develop_ro` @ `ee98739fd57267c0f681a418e1d1b0513f5cb22d` (matches the SHA the doc itself cites at line 318).
**Realization**: `landmatrix_dec18` (only realization; `cfg$gms$land <- "landmatrix_dec18"`, default.cfg:232). Verified single realization on disk.
**Date**: 2026-05-29

---

## Method

Read the full doc. Enumerated load-bearing code-checkable claims: 7 equations + formulas, 6 variables + 3 parameters, all file:line citations, the `land` set + 4 subsets, realization name, the DEPENDS-ON set (2 modules), the PROVIDES-TO table (15 rows), the "Direct consumers of vm_land" list (line 316), the R29-fixed expansion/reduction consumer note (line 344), presolve restrictions, the centrality numbers, and line/cell counts. Each consumer/dependency set was re-enumerated from code with word-boundary greps, cross-checked with a second method, and guarded with positive controls. Look-alike siblings (`vm_landexpansion_forestry`, `vm_landdiff`) were explicitly excluded.

---

## Verified-correct claims (high-value confirmations)

- **All 7 equations** (q10_land_area, q10_transition_to, q10_transition_from, q10_landexpansion, q10_landreduction, q10_cost, q10_landdiff): bodies match `equations.gms:13-54` line-for-line, including the cited sub-ranges (13-15, 19-21, 23-25, 30-33, 35-38, 42-44, 50-54). Set-based sums preserved (no MANDATE-10 expansion). ✓
- **Variables**: 6 declared (`vm_landdiff` scalar + `vm_land`, `vm_landexpansion`, `vm_landreduction`, `vm_cost_land_transition`, `vm_lu_transitions`), declarations.gms:14-24. Units match. ✓
- **Parameters**: `pm_land_start`, `pm_land_hist`, `pcm_land` (declarations.gms:8-12). ✓
- **`land` set** at `core/sets.gms:250-251`; 4 subsets at 253-263 with correct members (land_ag, land_forest, land_natveg, land_timber). ✓ Citation and membership exact.
- **Citations**: `module.gms:10-14` (description, verbatim), `start.gms:8`, `postsolve.gms:9` (`pcm_land(j,land) = vm_land.l(j,land)`), `realization.gms:11` (net-only limitation, verbatim), `input.gms:8-11/19-23/25-29` (3 tables), `sets.gms:12-13` (side layers), `presolve.gms:13-21` (restrictions). All resolve to the cited content. ✓
- **Authors** (module.gms:16): Jan Philipp Dietrich, Florian Humpenoeder, Kristine Karstens. ✓
- **DEPENDS ON {32, 35}**: `vm_landdiff_forestry` declared+populated in M32 (declarations:67, equations:113), `vm_landdiff_natveg` in M35 (declarations:79, equations:92), both read by M10 equations.gms:53-54. ✓
- **Direct consumers of `vm_land` = {22, 29, 30, 31, 32, 34, 35, 50, 58, 59}** (line 316): re-enumerated independently; EXACT match. The cited authoritative source `cross_module/modification_safety_guide.md` carries the identical 10-module list. ✓ (Negative claim "11/14/39/71/80 contain zero `vm_land(` refs" — CONFIRMED with positive controls: 11 reads only vm_cost_land_transition; 39 only vm_landexpansion/reduction; 80 only vm_landdiff; 14 only pm_land_start; 71 only pm_land_start.)
- **R29 fix at line 344** — `vm_landexpansion` used by {35, 39, 58, 59}; `vm_landreduction` by {39, 58}: re-enumerated with word boundaries (excluding the `vm_landexpansion_forestry`/`vm_landreduction_forestry` siblings in M32, and capturing M58's bare-macro-arg usage `m58_LandMerge(vm_landexpansion,...)`). BOTH sets EXACT. The R29 fix HELD. (My first-pass grep falsely implicated M32 via the `_forestry` look-alike — refuted on inspection.)
- **PROVIDES-TO per-variable rows** for 59 (4 vars), 29 (3), 35 (3), 58 (3), 32 (2), 11 (vm_cost_land_transition), 30/31/34/50 (vm_land): all confirmed against code.
- **`vm_lu_transitions` consumers = {29, 35, 59}**, **`vm_cost_land_transition` = {11}**, **`pm_land_hist` = {29}**: confirmed.
- **Centrality "15 outputs, 2 inputs"** and the summary line-789 union {11,14,22,29,30,31,32,34,35,39,50,58,59,71,80}: this 15-set equals the verified union of modules reading any of vm_land/expansion/reduction/lu_transitions/cost/landdiff/pm_land_start/pm_land_hist. ✓ (But see BUG-5: the pcm_land consumers 13/44/56 push the true "touched-by-any-interface" union to 18, which the doc both acknowledges (line 318) and undercounts elsewhere.)
- **`ov_*` output params** used in the Testing section exist (declarations.gms:38-43). `vm_landdiff` is a true scalar (no index). ✓
- Equations all use set-based sums; no fabricated formulas; the two hypothetical extension equations (q10_deforestation, q10_urban_source) are correctly flagged as non-existent.

---

## Bugs found

### BUG-1 (Major) — "vm_land used by 11 modules" (actual: 10); contradicts the doc's own line 316
- **Doc**: module_10.md:176 "**Most shared variable in MAgPIE** (used by 11 modules!)"; repeated module_10.md:776 "most critical: `vm_land` used by 11 modules".
- **Reality**: exactly 10 modules directly reference `vm_land` (any suffix, all .gms): 22, 29, 30, 31, 32, 34, 35, 50, 58, 59. The doc's OWN authoritative list at line 316 says "10 modules", and the cited safety guide says 10. Lines 176/776 retained a stale "11".
- **Evidence**: `grep -rnE 'vm_land[ .(,]' /tmp/magpie_develop_ro/modules/ --include='*.gms' | grep -vE '/10_land/|ov_land|vm_land_|vm_landd|vm_lande|vm_landr'` → 10 distinct module numbers {22,29,30,31,32,34,35,50,58,59}. core/ hit is only a comment in macros.gms:13.
- **Class**: Hardcoded counts drift (Pattern 6). **Trigger**: "Right concept, wrong number." Tie-broken UP to Major (not Minor) because it is the most-shared, highest-stakes variable, the figure appears twice in load-bearing prose, and it self-contradicts the corrected line 316 — a reader doing impact analysis on `vm_land` gets two conflicting counts.
- **Fix**: line 176 → "**Most shared variable in MAgPIE** (used by 10 modules)"; line 776 → "most critical: `vm_land` used by 10 modules".

### BUG-2 (Major) — PROVIDES-TO table: 80_optimization labeled `vm_land`, actually `vm_landdiff`
- **Doc**: module_10.md:313 "| **80_optimization** | vm_land (1) | Objective function |".
- **Reality**: M80 reads `vm_landdiff` (the objective minimized), NOT `vm_land`. M80 contains zero `vm_land` refs.
- **Evidence**: `grep -rn 'vm_land' modules/80_optimization/` → only `vm_landdiff`: `lp_nlp_apr17/solve.gms:76 solve magpie USING nlp MINIMIZING vm_landdiff;` (also 77,196,197; module.gms:15). No `vm_land`.
- **Class**: Hallucinated/wrong variable name in a consumer table (Pattern 2-adjacent; consumer-attribution). **Trigger**: "Wrong variable" within a dependency set (R20-anchor family). Major (not Critical) because the variable IS a real M10 interface var and the same doc's clarifying paragraph (line 318) correctly says 80 doesn't consume vm_land.
- **Fix**: line 313 → "| **80_optimization** | vm_landdiff (1) | Objective function |".

### BUG-3 (Major) — PROVIDES-TO table: 14_yields labeled `vm_land`, actually `pm_land_start`
- **Doc**: module_10.md:306 "| **14_yields** | vm_land (1) | Yield calculations |".
- **Reality**: M14 reads `pm_land_start` (pasture-yield regional aggregation), NOT `vm_land`. M14 contains zero `vm_land` refs.
- **Evidence**: `grep -rnE 'vm_land|pm_land_start|...' modules/14_yields/` → only `managementcalib_aug19/preloop.gms:15-16 ... pm_land_start(j,"past") ...`. No vm_land.
- **Class**: Wrong variable in consumer table. **Trigger**: Wrong variable in dependency set. Major.
- **Fix**: line 306 → "| **14_yields** | pm_land_start (1) | Pasture-yield aggregation |".

### BUG-4 (Major) — PROVIDES-TO table: 71_disagg_lvst labeled `vm_land`, actually `pm_land_start`
- **Doc**: module_10.md:312 "| **71_disagg_lvst** | vm_land (1) | Livestock disaggregation |".
- **Reality**: M71 reads `pm_land_start` (urban-area share for disaggregation), NOT `vm_land`. M71 contains zero `vm_land` refs.
- **Evidence**: `grep -rnE 'vm_land|pm_land_start|...' modules/71_disagg_lvst/` → only `foragebased_jul23/preloop.gms:9 ... pm_land_start(j,"urban")...` (and foragebased_aug18). No vm_land.
- **Class**: Wrong variable in consumer table. **Trigger**: Wrong variable in dependency set. Major.
- **Fix**: line 312 → "| **71_disagg_lvst** | pm_land_start (1) | Livestock disaggregation |".

### BUG-5 (Major) — "13_tc / 44_biodiversity / 56_ghg_policy affected only indirectly" — they directly read `pcm_land`
- **Doc**: module_10.md:318 "`13_tc`/`14_yields`/`44_biodiversity`/`56_ghg_policy`/`71_disagg_lvst`/`80_optimization` are affected only indirectly via other Module-10 interface variables".
- **Reality**: 13_tc, 44_biodiversity, and 56_ghg_policy DIRECTLY consume `pcm_land`, a parameter declared in M10 (declarations.gms:11) and populated by M10 (postsolve.gms:9). They are direct consumers, not "indirect". (14 and 71 in the same sentence directly read `pm_land_start` — see BUG-3/4 — so "indirectly" is loose for them too, though pm_land_start IS counted elsewhere.)
- **Evidence**:
  - `modules/13_tc/endo_jan22/presolve.gms:9-10` `pc13_land(i,"pastr") = sum(cell(i,j),pcm_land(j,"past"));` (default realization).
  - `modules/44_biodiversity/bii_target/preloop.gms:15` `... pcm_land(j,land) * i44_biome_share(...)`.
  - `modules/56_ghg_policy/price_aug22/preloop.gms:10` `pcm_carbon_stock(...) = ...*pcm_land(j,land);`.
  - Full `pcm_land` consumer set (12 modules): 13,22,29,31,32,34,35,44,56,58,59,71 — matches the safety guide's "12 modules / EXTREME" row.
- **Root cause**: `pcm_land` is NOT listed in the doc's "Interface Variables → Provided to Other Modules" table (lines 882-890), despite being M10's second-most-shared interface parameter. Because pcm_land is invisible as a provided interface, its direct consumers (13/44/56) get mislabeled "indirect."
- **Class**: Latent doc error — wrong direct/indirect consumer classification (Pattern 15 / MANDATE 17). **Trigger**: R20-anchor (doc states wrong consumer set; a user refactoring `pcm_land` would consult M10 docs, see it only as an internal "previous timestep" parameter, and miss 12 consumers — including 13/44/56 the doc actively calls "indirect"). Tie-broken DOWN to Major (not the full R20 Critical) ONLY because the same line cites the safety guide's "18-module union," and the safety guide is correct — a reader who follows the citation recovers the truth.
- **Fix**: (a) line 318 — move 13_tc/44_biodiversity/56_ghg_policy out of "indirectly" and state "13_tc, 44_biodiversity, and 56_ghg_policy directly read `pcm_land` (M10's previous-timestep parameter; 12 direct consumers total — see safety guide)"; (b) add `pcm_land (j,land) | Land area in previous time step | mio. ha` as a row in the "Provided to Other Modules" interface table (lines 882-890), noting it is populated in postsolve.gms:9.

### BUG-6 (Minor) — "default h200 spatial resolution" — default token is `c200`, not `h200`
- **Doc**: module_10.md:224 "aggregated to ~200 MAgPIE cells (default h200 spatial resolution)"; module_10.md:412 "Each cell (~200 at default h200 resolution)".
- **Reality**: the default cellular input is `..._cellularmagpie_c200_...` (default.cfg:26) — the cluster resolution is **c200**. `h12` is the regional (12-world-region) setup; there is no `h200` token. The ~200-cell count is right; the token is wrong.
- **Evidence**: `config/default.cfg:25-26` `cfg$input <- c(regional = "rev4.131_h12_magpie.tgz", cellular = "rev4.131_h12_1b5c3817_cellularmagpie_c200_MRI-ESM2-0-ssp245_lpjml-8e6c5eb1.tgz")`. No `h200` anywhere in default.cfg.
- **Class**: Wrong default/filename token (Pattern 13-adjacent). **Trigger**: "wrong detail; careful reader not misled into action" (concept right, token wrong, recoverable). Minor.
- **Fix**: replace "h200" with "c200" at lines 224 and 412 (or "~200 clustered cells (c200)").

### BUG-7 (Minor) — "Secondary↔Other blocked" — only `secdforest→other` is blocked; `other→secdforest` is allowed
- **Doc**: module_10.md:348 "**No conversions within natveg** (Primary↔Other, Secondary↔Other blocked)".
- **Reality**: presolve fixes only the one direction `secdforest→other` (presolve.gms:17). `other→secdforest` is NOT blocked (secondary-forest regrowth from "other"). The bidirectional `↔` is correct for Primary↔Other (primforest→other via line 16, other→primforest via the all-to-primforest fix line 20) but wrong for Secondary↔Other.
- **Evidence**: `grep -n secdforest modules/10_land/landmatrix_dec18/presolve.gms` → only line 17 `vm_lu_transitions.fx(j,"secdforest","other") = 0;`. No fix on `(...,"secdforest")` as a target except the all-to-primforest line which targets primforest, not secdforest.
- **Class**: Conceptual prose imprecision (Pattern 4-adjacent). **Trigger**: "wrong detail." Minor (prose in a "Code Truth" bullet, not a variable/equation claim; a reader testing `other→secdforest==0` would be misled).
- **Fix**: line 348 → "(Primary↔Other blocked; `secdforest→other` blocked — note `other→secdforest` regrowth is allowed)".

### BUG-8 (Minor) — "Only 318 lines of code" — actual 292
- **Doc**: module_10.md:774 "Only 318 lines of code, but **15 modules depend on it**".
- **Reality**: total .gms in `landmatrix_dec18` = 292 lines (wc -l across all 9 .gms files).
- **Evidence**: `wc -l modules/10_land/landmatrix_dec18/*.gms` → 292 total (declarations 52, equations 54, input 29, postsolve 64, presolve 25, realization 22, scaling 12, sets 20, start 14).
- **Class**: Hardcoded count drift (Pattern 6). **Trigger**: "wrong number." Minor (rhetorical "only X lines" framing; not load-bearing). Tie-broken down.
- **Fix**: line 774 → "Only ~290 lines of code" (or "292 lines").

---

## Deferred (not code-verifiable here / out of scope — NOT edited)

- LUH2 category mapping (module_10.md:229-235: `c3ann+c4ann→crop`, `pastr+range→past`, etc.) — a preprocessing (mrcommons/mrland) fact; not present in M10 GAMS code and the doc does not cite a GAMS file for it. Route to preproc-agent if verification wanted.
- secdforest ">20 tC/ha" and other "<20 tC/ha" thresholds (module_10.md:159,161) — preprocessing-derived land-classification thresholds, not in M10 GAMS. Descriptive, uncited to GAMS; not flagged.
- "67,420 original 0.5° cells" (module_10.md:413) — a global LUH/preprocessing grid figure; not verifiable from the develop GAMS tree. The doc hedges ("cell count depends on spatial resolution setting"). Left as-is.
- "Source: Land-Use Harmonization 2 (LUH2)" provenance and "249 ISO countries" (module_10.md:223,265) — preprocessing/input-data facts; not GAMS-checkable here.
- "Last Verified 2026-03-06 … Changes Since Last Verification: None (stable)" footer — metadata; the equations/variables ARE stable, so not a content bug.

---

## Verdict

**MOSTLY ACCURATE (lower band).** The equation/variable/parameter/citation core is excellent (verbatim-accurate, set-sums preserved, hypotheticals flagged), and the two consumer claims the pre-run advisory flagged (line 316 `vm_land` list; line 344 expansion/reduction note) BOTH HELD against develop and survived adversarial re-enumeration including look-alike traps. The errors cluster in the dependency-presentation layer: a doc-internal count contradiction on `vm_land` (BUG-1), three wrong-variable labels in the PROVIDES-TO table (BUG-2/3/4, all because the table forces every row onto `vm_land`), and a wrong direct/indirect classification rooted in `pcm_land` being absent from the interface table (BUG-5). Estimated answer-equivalent score: 5 Major + 3 Minor → heavy, but every Major points the reader at a correct adjacent source (line 316 / the safety guide), keeping them out of Critical territory.

**Highest-value fixes**: BUG-5 (add `pcm_land` to the interface table + correct the 13/44/56 "indirect" claim) and BUG-1 (the self-contradicting "11 modules"). BUG-2/3/4 are mechanical table corrections.
