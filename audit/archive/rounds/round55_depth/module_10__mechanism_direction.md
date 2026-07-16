# Round 55 depth audit — module_10.md — lens: mechanism_direction

**Target**: `modules/module_10.md` (Module 10, Land Allocation & Transitions)
**Ground truth**: develop worktree `/private/tmp/magpie_develop_ro` @ `0d7ebeb90`
**Default realization**: `landmatrix_dec18` (only realization; `config/default.cfg:232` `cfg$gms$land <- "landmatrix_dec18"`)
**Role map**: `audit/integrated/depth_rolemap.json`

## Verdict: MOSTLY ACCURATE (high quality). No Critical/Major confirmed. 4 Minor findings, all in narrative/populate framing.

The doc's load-bearing spine is correct: all 7 equations verbatim with correct line citations (equations.gms:13-15,19-21,23-25,30-33,35-38,42-44,50-54); `land` set (7 pools) and its 4 subsets with correct membership and citations (core/sets.gms:250-263); 6 declared variables + 3 parameters with correct citations; presolve transition restrictions (presolve.gms:10-23) all correct; realization.gms:11 limitation quote correct; module.gms:10-14 header correct; default resolution c200 correct.

**Interface attribution against role map + both-endpoints grep — all correct**:
- `vm_land` direct consumers (doc:315-316): 22,29,30,31,32,34,35,50,58,59 = role map read_by exactly. ✓
- `vm_landexpansion` (doc:344): 35,39,58,59 ✓; `vm_landreduction` (doc:344): 39,58 ✓ (doc correctly notes 35/59 do NOT read reduction).
- `pcm_land` 12 direct consumers (doc:318,891) = role map read_by (excl. 10) exactly. ✓
- PROVIDES-TO table (doc:297-313), all 15 rows / ~24 var-module attributions cross-checked against role map read_by — every one correct.
- DEPENDS-ON: `vm_landdiff_forestry` (declared+populated M32, read by M10) and `vm_landdiff_natveg` (declared+populated M35, read by M10) — genuine serial hand-offs, confirmed at equations.gms:50-54. ✓
- Doc:318 "11/14/39/71/80 contain zero `vm_land(`" — reverified on develop (both `vm_land(` and `vm_land.` forms): zero. ✓

---

## Findings

### Finding 1 — Minor — Module 14 mischaracterized ("cropland" vs pasture) — attribution_read
**doc_line**: module_10.md:840
**Claim**: "Module 14 (Yields): Cropland area for production" (Section 11 "Key downstream dependents").
**Reality**: Module 14 reads `pm_land_start(j,"past")` (PASTURE), for pasture-yield calibration — not cropland, not generic "production".
**Evidence**: `modules/14_yields/managementcalib_aug19/preloop.gms:15-16` (`i14_yields_calib(...,"pasture",...) * pm_land_start(j,"past") / sum(cell,pm_land_start(j,"past"))`).
**Internal contradiction**: the doc's own authoritative provides-to table (module_10.md:306) correctly says "14_yields | pm_land_start (1) | Pasture-yield aggregation".
**verify_cmd**: `rg -n 'pm_land_start' modules/14_*/` → only preloop.gms:15-16, both `pm_land_start(j,"past")`.
**Fix**: change line 840 to "Module 14 (Yields): pm_land_start(past) for pasture-yield calibration" to match line 306.

### Finding 2 — Minor — Modules 42 & 52 listed as direct downstream dependents receiving "Land area" — data_flow_direction (MANDATE 17, direct-vs-transitive)
**doc_line**: module_10.md:841-842
**Claim**: "Module 42 (Water): Land area for water demand" / "Module 52 (Carbon): Land area for carbon stocks" as key downstream dependents.
**Reality**: Neither module directly reads ANY module-10 interface variable. M52 reads `vm_carbon_stock` (declared M56, populated by land modules 29/31/32/34/35/59) at `modules/52_carbon/normal_dec17/equations.gms:19` — a transitive path (M10→land modules→vm_carbon_stock→M52), not direct land-area provision. M42 reads its own `vm_watdem` and (transitively) cropland `vm_area` from M30, not `vm_land`.
**Evidence**: grep of all M10 vars (`vm_land`, `pcm_land`, `vm_lu_transitions`, `pm_land_start`, `vm_landexpansion`, `vm_landreduction`, both `(` and `.` forms) in `modules/42_*/` and `modules/52_*/` = zero hits; positive control (`vm_watdem` in 42, `vm_carbon_stock` in 52) confirms greps work. Role map read_by for every M10 var excludes 42 and 52.
**Note**: the authoritative provides-to table (Section 5) CORRECTLY omits 42/52. The transitive cascade is real, so the modification-safety advice at module_10.md:869 ("verify no cascading failures in water/carbon") is fine; only the "Land area for X" mechanism label implies a false direct hand-off.
**verify_cmd**: `for v in vm_land pcm_land vm_lu_transitions pm_land_start vm_landexpansion vm_landreduction; do rg -n "${v}\(|${v}\." modules/42_*/ modules/52_*/; done` → no matches; positive control returns hits.
**Fix**: label 42/52 as transitive/indirect dependents (e.g. "affected via land-allocation modules"), not recipients of "Land area", or drop the "Land area for" phrasing.

### Finding 3 — Minor — pcm_land populate-side incompleteness (per-slice overwrites by M32/M34/M35) — attribution_populate (MANDATE 18 per-slice corollary)
**doc_line**: module_10.md:891 (also 208-211, 318)
**Claim**: `pcm_land` "populated in `postsolve.gms:9`" — presented as module-10's product (`pcm_land(j,land)=vm_land.l`), dropping the declaration's own qualifier.
**Reality**: `pcm_land` declaration (declarations.gms:11) is "Land area in previous time step **including possible changes after optimization**". Modules 32/34/35 overwrite specific slices AFTER M10's postsolve assignment: M32 recomputes `pcm_land(j,"forestry")` from age classes (`modules/32_forestry/dynamic_may24/presolve.gms:101`), M34 sets `pcm_land(j,"urban")` exogenously (`modules/34_urban/exo_nov21/preloop.gms:17`), M35 overwrites `pcm_land(j,"primforest"/"secdforest"/"other")` (`modules/35_natveg/pot_forest_may24/presolve.gms:39,131,137`). Role map populated_by = ['10','32','34','35'].
**Impact**: relevant to modification-safety reasoning on the hub's key recursive-state parameter; a reader treating pcm_land as purely `vm_land.l` carried forward would miss the natveg/forestry/urban slice overwrites.
**verify_cmd**: `rg -n 'pcm_land\([^)]*\)\s*=' modules/*/ | rg -v 10_land` → 32/presolve:101, 34/preloop:17, 35/presolve:39,131,137.
**Fix**: add a note that pcm_land is initialized by M10 (postsolve.gms:9) but its forestry/urban/primforest/secdforest/other slices are subsequently modified by M32/M34/M35 (per the declaration's "including possible changes after optimization").

### Finding 4 — Minor — "affects/provides to 15 modules" undercounts total downstream reach — set_membership/count
**doc_line**: module_10.md:14 (also 275, 791)
**Claim**: "Changes to this module affect **15 other modules**"; "Centrality Score: 17 (Provides to: 15, Depends on: 2)".
**Reality**: The provides-to table's 15 excludes the pcm_land-only consumers 13_tc, 44_biodiversity, 56_ghg_policy. The union of direct consumers across ALL module-10-declared variables (incl. pcm_land) is 18 modules: 11,13,14,22,29,30,31,32,34,35,39,44,50,56,58,59,71,80. The doc IS internally transparent (it lists 13/44/56 as pcm_land consumers at line 318), so "15" is a defined provides-to-table metric — but the modification-safety headline "affect 15 modules … testing must be comprehensive" undercounts by 3.
**verify_cmd**: role map read_by union across vm_land/vm_landexpansion/vm_landreduction/vm_lu_transitions/vm_cost_land_transition/vm_landdiff/pm_land_start/pm_land_hist/pcm_land (excl. 10) = 18 distinct modules.
**Fix**: reconcile the "affects N modules" headline with the pcm_land consumers, or state "15 via the shared vm_/pm_ interface, plus 13/44/56 via pcm_land (18 total)".

---

## Deferred (not flagged as bugs)
- LUH2/LUH3 internal inconsistency: Section 4 File 1 (line 223) corrected to LUH3 with a dated note, but Section 6 item 7 (363-365), summary (771), and File-2 title still say "LUH2". Data-source vintage is preproc-owned (routed to PREPROC_AGENT.md) and the .cs3 inputs are runtime products not in this repo — not GAMS-code-verifiable here. Worth a doc-internal-consistency pass but out of this lens's verifiable scope.
- "67,420 original 0.5° cells" (line 413), "249 ISO countries" (line 265): input-data/preproc claims, not verifiable from GAMS code.
- Circular-dependency framing "10↔32↔35" (line 290) and "Rank #2 centrality after 09_drivers" (line 276): sourced from detailed_module_analysis.txt legacy analysis; cross_module docs are the authority.
- pcm_land is also initialized in start.gms:11 (`pcm_land = pm_land_start`) in addition to postsolve.gms:9 — a completeness detail, not an error.
