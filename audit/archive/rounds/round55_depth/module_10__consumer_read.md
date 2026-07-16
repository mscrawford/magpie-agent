# Round 55 depth audit — module_10.md — lens: consumer_read

**Target**: `modules/module_10.md` (Module 10: Land Allocation & Transitions)
**Ground truth**: `/private/tmp/magpie_develop_ro` @ `0d7ebeb90` (develop)
**Realization**: `landmatrix_dec18` (only realization; default confirmed `config/default.cfg:232`)
**Method**: consumer-side entry — role map (`audit/integrated/depth_rolemap.json`) checked FIRST for every interface-var attribution, then confirmed with BOTH-endpoints greps (`NAME(` and `NAME.`) plus macro-argument forms.

---

## Summary

The doc is highly accurate on the load-bearing consumer/read claims. Every DIRECT-consumer set in the authoritative sections (Section 5 PROVIDES-TO table, the 10-module `vm_land` list, the interface-variable table, the Code-Truth expansion/reduction consumer lists) matches both the role map AND my code greps — including module 58's reads of `vm_land`/`vm_landexpansion`/`vm_landreduction` that occur via the `m58_LandMerge(...)` macro and are invisible to a `NAME(` grep. All 7 equation citations, all set/subset memberships, all parameter/variable declarations, and all file:line citations verified correct.

**One Minor finding**: the Section 11 "Key downstream dependents" summary lists Module 42 and Module 52 as receiving "land area" from M10, but neither module reads ANY M10 interface variable directly (both are transitive-only, via `vm_area`/M30 and `vm_carbon_stock` respectively). This contradicts the doc's own precise Section 5 accounting.

---

## Verified correct (high-value spot checks)

**Direct `vm_land` consumers (10 modules)** — doc line 316 list `22,29,30,31,32,34,35,50,58,59`:
- Role map `vm_land.read_by` (excl. 10): `22,29,30,31,32,34,35,50,58,59` — exact match.
- Grep `\bvm_land\b` across modules (excl. 10/derived) returned `22,29,30,31,32,34,35,50,59`; module 58 reads `vm_land` via `m58_LandMerge(vm_land,...)` at `modules/58_peatland/v2/equations.gms:23` (macro arg, missed by paren-grep) → full set = 10 modules. CONFIRMED.

**`vm_landexpansion` consumers** — doc: `35,39,58,59`. Grep paren-form: `35,39,59`; module 58 via `m58_LandMerge(vm_landexpansion,...)` `58/v2/equations.gms:28`. Full = `35,39,58,59`. CONFIRMED.

**`vm_landreduction` consumers** — doc: `39,58` ("35 and 59 do not consume reduction"). Grep: `39`; module 58 via macro `58/v2/equations.gms:31`. Full = `39,58`. 35/59 absent. CONFIRMED.

**`vm_lu_transitions` consumers** — doc: `29,35,59`. Grep both forms: `29` (equations), `35` (equations+presolve `.` form at `35/pot_forest_may24/presolve.gms`), `59`. CONFIRMED.

**`vm_cost_land_transition`** → `11` only (`11/default/equations.gms`). CONFIRMED.
**`vm_landdiff`** → `80` (objective, `80/lp_nlp_apr17/solve.gms:76,196`). CONFIRMED.
**`pm_land_start`** → `14,32,59,71` (all `preloop.gms`). CONFIRMED.
**`pm_land_hist`** → `29` only (`29/detail_apr24/preloop.gms`). CONFIRMED.
**`pcm_land`** → 12 external consumers incl. `13,44,56` (all confirmed by grep). Doc "12 direct consumers" matches role map `read_by` (excl. 10) = `13,22,29,31,32,34,35,44,56,58,59,71`. CONFIRMED.

**DEPENDS-ON (2)**: `vm_landdiff_forestry`←M32, `vm_landdiff_natveg`←M35, both read by M10 in `q10_landdiff` (`equations.gms:50-54`). CONFIRMED.

**Equation citations** (`equations.gms`): q10_land_area 13-15, q10_transition_to 19-21, q10_transition_from 23-25, q10_landexpansion 30-33, q10_landreduction 35-38, q10_cost 42-44, q10_landdiff 50-54 — ALL exact.
**Presolve restrictions** (`presolve.gms:13-21`, doc cites 10-23 incl. `@code`/`@stop` markers): primforest→forestry fixed 0 (l.13); primforest→other & secdforest→other fixed 0 (l.16-17); all→primforest fixed 0 (l.20); primforest→primforest up=Inf (l.21). Doc's "Primary↔Other bidirectional", "secdforest→other blocked", "other→secdforest allowed", "primforest can only decrease", "primforest→primforest persistence" — ALL accurate.
**Sets**: `land` (core/sets.gms:250-251) = crop,past,forestry,primforest,secdforest,urban,other ✓; subsets land_ag/land_forest/land_natveg/land_timber (253-263) memberships ✓; `luh2_side_layers10` (sets.gms:12-13) 6 members ✓.
**Declarations/parameters/postsolve/start** citations all verified (declarations.gms:8-12 params, 14-24 vars; start.gms:8; postsolve.gms:9; input.gms:8-11/16/19-23/25-29).

---

## FINDING 1 (Minor) — Modules 42 & 52 listed as M10 "downstream dependents" but read no M10 interface variable

**doc_line**: module_10.md:841-842 (Section 11 → Dependency Chains → "Key downstream dependents")

**Claim**:
> - Module 42 (Water): Land area for water demand
> - Module 52 (Carbon): Land area for carbon stocks

**Reality**: Neither module 42 nor module 52 reads ANY M10 interface variable (`vm_land`, `vm_lu_transitions`, `vm_landexpansion`, `vm_landreduction`, `pm_land_start`, `pm_land_hist`, `pcm_land`) in any `.gms` file. Both are TRANSITIVE-only dependents:
- M42 (water_demand) reads `vm_area` (M30 croparea); M30 reads `vm_land`. → 2-hop.
- M52 (carbon) reads `vm_carbon_stock` (declared M56, populated by 29/31/32/34/35/59 which read `vm_land`), plus `vm_land_other`(M35)/`vm_land_forestry`(M32) — none is an M10 variable. → transitive.

This contradicts the doc's own precise Section 5 accounting, which correctly omits 42 and 52 from the 15-module PROVIDES-TO list and from the 10-module direct-`vm_land` consumer list. MANDATE 17 (direct vs transitive consumer): the mechanism phrasing ("Land area for water demand / carbon stocks") implies a direct land-area handoff that does not exist in code.

**verify_cmd + result**:
`rg -n "vm_land|pm_land_start|pm_land_hist|pcm_land|vm_lu_transitions|vm_landexpansion|vm_landreduction" modules/42_water_demand/ modules/52_carbon/ --glob '*.gms'` → **no matches in either module** (positive control: same pattern returns hits in modules/59_som and modules/29_cropland). Role map corroborates: `vm_land.read_by` excludes 42 and 52.

**confirmed**: true
**proposed_fix**: Label 42 and 52 as INDIRECT/transitive dependents, e.g. "Module 42 (Water): indirectly — via `vm_area` (M30), which reads `vm_land`" and "Module 52 (Carbon): indirectly — via `vm_carbon_stock` (populated by land-pool modules)". Or move them out of a list that sits alongside genuine direct consumers (11, 59).

---

## Deferred (not flagged as confirmed code bugs)

- **module_10.md:842 "Module 14 (Yields): Cropland area for production"** — M14 IS a direct consumer, but of `pm_land_start(j,"past")` (pasture init area for pasture-yield calibration, `14/managementcalib_aug19/preloop.gms:15-16`), NOT "cropland area." Mischaracterization of WHAT it reads; low value, summary-section wording.
- **module_10.md:13 "HIGHEST centrality in MAgPIE" vs :276/:833 "Rank #2 (after 09_drivers)"** — internal inconsistency; the underlying centrality metric is a derived graph number from `detailed_module_analysis.txt`, not cleanly code-verifiable. Human review.
- **module_10.md:850 "Cycle 2: Module 10 ←→ Module 22"** — M10 reads NO M22 variable (grep for `pm_land_conservation|vm_treecover|vm_bv|vm_cost_bv_loss` in `modules/10_land/` → NONE). The bidirectionality is solver-constraint coupling (q22 bounds `vm_land`), not an interface-var read. Borderline characterization; cross-refs `circular_dependency_resolution.md`.
- **pcm_land populators** — role map `pcm_land.populated_by = [10,32,34,35]`: M32 (`32/dynamic_may24/presolve.gms:101`), M34 (`34/exo_nov21/preloop.gms:17`), M35 (`35/pot_forest_may24/presolve.gms:39,131,137`) also reassign `pcm_land` slices in presolve. Doc says "populated in postsolve.gms:9" describing M10's recursive role — not claimed exclusive, so not a bug, but the multi-populator fact is undocumented.
- **Data vintage LUH3/LUH2, ~200/c200 cells, 67,420 0.5° cells, 249 ISO countries, ~292 LOC** — preproc-owned / config / hedged numeric claims outside the consumer_read lens; doc already routes vintage to PREPROC_AGENT.

---

**Claims verified**: ~35 code-checkable claims. **Confirmed bugs**: 1 (Minor). **False-positive guard**: module 58's macro-form reads and the both-endpoints re-grep prevented a spurious "58 is a phantom consumer" flag.
