# Round 33 Doc Audit — module_30.md (Croparea)

**Auditor**: Opus (adversarial doc-vs-code audit)
**Target**: `magpie-agent/modules/module_30.md` (1742 lines)
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree); `config/default.cfg` for defaults
**Date**: 2026-05-30

---

## Summary verdict

The doc's equation bodies, formulas, scalar defaults, realization split, and detail_apr24
file:line citations are overwhelmingly accurate (the equation-level content is high quality).
The serious problems are all in the **interface/dependency SET claims**, which are internally
self-contradictory and wrong against code in three independent places:

1. The `vm_area` consumer list is wrong in every section that states it (overview, Interface
   Variables, Downstream Dependencies, Quick Reference) — phantom M17 + M38, omitted M29 + M32.
2. The `vm_carbon_stock_croparea` Interface-Variables block still claims direct M52/M56
   consumption — the exact MANDATE-17 / R24 bug that was supposedly fixed (it was fixed only in
   §6 narrative at line 369, not in the Interface Variables block at lines 608-620).
3. The "Depends On (6 modules)" list invents M16 (demand) and M13 (TC) as direct dependencies;
   code shows neither is read by any Module-30 file.

These are Critical-prone per the R20 anchor (wrong consumer/producer set → user misses modules
in a refactor). Equation/citation drift is minor.

---

## Ground-truth facts established (with commands)

### Default realization
- `grep -n "croparea" config/default.cfg` → line 896: `cfg$gms$croparea <- "simple_apr24"   # def = simple_apr24`.
- CONFIRMED: default is `simple_apr24`. (`grep "cfg\$gms\$croparea"` returned empty due to `$` escaping; broader grep found it.)
- Realizations present: `ls modules/30_croparea/` → `simple_apr24/`, `detail_apr24/`, shared `module.gms`. CONFIRMED 2 realizations.

### vm_area direct consumers (THE load-bearing set)
Command: `grep -rln "vm_area" /tmp/magpie_develop_ro/modules/ /tmp/magpie_develop_ro/core/ --include="*.gms" | grep -v 30_croparea`
Result (exit 0, cross-checked twice, plus positive controls):
- 18_residues (flexcluster_jul23, flexreg_apr16) — eq read
- 29_cropland (detail_apr24:12, simple_apr24:13) — `q29` read
- 32_forestry (dynamic_may24/presolve.gms:17) — reads `vm_area.l`/`vm_area.lo` (afforestation potential). **dynamic_may24 IS default** (config:976).
- 41_area_equipped_for_irrigation (endo_apr13, static) — eq read
- 42_water_demand (agr_sector_aug13, all_sectors_aug13) — eq read
- 50_nr_soil_budget (macceff_aug22:25) — eq read
- 53_methane (ipcc2006_aug22:61) — eq read
- 59_som (cellpool_jan23, static_jan19) — eq read

**Direct consumer set = {18, 29, 32, 41, 42, 50, 53, 59} = 8 modules.** No core/ refs.
`not_used.txt` hits only in 18_residues/off and 53_methane/off (non-default; explicitly mark vm_area unused).

Positive controls run (captured-var pattern, exit-0 forced):
- M17 vm_area = `<none>`; M17 vm_prod present (4 files) → M17 reads vm_prod, NOT vm_area.
- M38 vm_area = `<none>`; M38 vm_cost_prod_crop present → M38 reads vm_prod-derived costs, NOT vm_area.
- M73 vm_area = `<none>`; M73 vm_prod present → M73 reads vm_prod (betr), NOT vm_area.

### vm_carbon_stock_croparea consumers
Command: `grep -rn "vm_carbon_stock_croparea" modules/ --include=*.gms | grep -v 30_croparea`
Result: ONLY `29_cropland/simple_apr24/equations.gms:31` and `29_cropland/detail_apr24/equations.gms:40`.
M52/M56 do NOT read `vm_carbon_stock_croparea`; they read the aggregated `vm_carbon_stock` produced by M29's `q29_carbon`.

### vm_rotation_penalty consumers
Command: `grep -rn "vm_rotation_penalty" modules/ --include=*.gms | grep -v 30_croparea`
Result: ONLY `11_costs/default/equations.gms:23`. Doc correct.

### Module 30 external inputs (what it depends ON)
Command: `grep -rhoE "(vm_|pm_|im_|fm_|sm_)[A-Za-z_0-9]+" modules/30_croparea/*/{equations,presolve,preloop}.gms | sort -u`
Result: `vm_yld, vm_land, vm_AEI, fm_carbon_density, fm_bii_coeff, fm_luh2_side_layers, pm_avl_cropland_iso, sm_fix_SSP2` (+ own vm_area/vm_prod/vm_bv/vm_carbon_stock_croparea/vm_rotation_penalty).
NO demand variable (M16), NO TC variable (M13) is read. Direct providers: M10 (vm_land), M14 (vm_yld), M41 (vm_AEI).

### Declaration lines
- `vm_area`: simple_apr24/declarations.gms:**18**; detail_apr24/declarations.gms:**21**. Doc cites bare `declarations.gms:21` (line 570) — correct for detail, wrong for the stated default (simple).
- `vm_rotation_penalty`: simple:19 / detail:22. `vm_carbon_stock_croparea`: simple:20 / detail:23. (Doc Interface block cites :22 and :23 — detail values.)

### Equation counts
- simple_apr24: 9 q30_ equations (grep -c) ✓. detail_apr24: 12 ✓. Union unique = 13 ✓.

### Rotation crop-group counts (detail_apr24)
- `rotamax30` = 30 members (sets.gms:27-35). `rotamin30` = 6 members (sets.gms:37-38). Total rota30 = 36.
- Doc §3 "30 maximum constraint groups" ✓ and "6 minimum constraint groups" ✓.
- BUT doc says "29 crop groups" at lines 45, 1030, 1274, 1463 — contradicts both the code (30 max / 36 total) and the doc's own §3.

### Scalars / switches (detail_apr24 input.gms — doc's Key Parameters section matches detail)
- s30_implementation /1/ (L24) ✓ ; c30_rotation_rules default (L14) ✓ ; c30_rotation_incentives none (L17) ✓ ;
  c30_bioen_type all (L8) ✓ ; c30_bioen_water rainfed (L11) ✓ ; s30_betr_penalty /2460/ (L31) ✓ ;
  s30_annual_max_growth /Inf/ (L32) ✓ ; policy_countries30 (L38-63) ✓.
- simple_apr24 has these at DIFFERENT lines (s30_betr_penalty L26, s30_annual_max_growth L27,
  c30_rotation_constraints L14). Doc §9 correctly cites simple input.gms:26 for s30_betr_penalty.

### detail_apr24 citation spot-checks (ALL correct for detail)
- q30_rotation_max 36-38 ✓; q30_rotation_min 40-42 ✓; q30_rotation_penalty 46-53 ✓;
  q30_rotation_max2 59-62 ✓; rotamax_red30 presolve:28 ✓; rotamin_red30 presolve:29 ✓;
  penalty-rotamax presolve:31 ✓; v30_penalty decl:25 ✓; preloop fixation 30-32 ✓;
  penalty-application eq:52 ✓; algorithm presolve 26-33/36-41/43-54 ✓; preloop 10-21/24-27 ✓.
- module.gms:18-19 (realization includes) ✓.

### simple_apr24 citation spot-checks (ALL correct for simple)
- q30_prod 14-15 ✓; q30_betr_missing 21-23 ✓; q30_cost 25-27 ✓; q30_rotation_max 34-36 ✓;
  q30_rotation_min 42-44 ✓; crp_kcr30 sets:18-37 ✓; f30_rotation_max_shr input:80-85 + off:86 ✓;
  f30_rotation_min_shr input:89-94 + off:95 ✓; c30_rotation_constraints input:14 ✓;
  header-note carbon/bv/reg lines (simple 49,56,60,66 / detail 87,94,99,105) ✓;
  q30_cost presolve:34-36 ✓; not_used.txt lists vm_AEI ✓.

---

## Bugs

### BUG-30-1 (Critical) — vm_area "Used by" list: phantom M17 + M38, omitted M29 + M32
- **Class**: 15 (latent doc error) / wrong consumer set.
- **Trigger**: R20 anchor — "doc said wrong consumer set; user would have missed modules in a refactor."
- **Doc**: module_30.md:575-584 (Interface Variables → vm_area → "Used by"). Lists Module 17, 18, 38, 41, 42, 50, 53, 59.
- **Reality**: direct vm_area consumers are 18, 29, 32, 41, 42, 50, 53, 59. M17 reads `vm_prod` (not vm_area); M38 has zero vm_area refs; M29 (`q29_cropland`/`q29_carbon`) and M32 (`dynamic_may24` afforestation, default realization) are omitted.
- **Evidence**: `grep -rln "vm_area" modules/ | grep -v 30_croparea` → 8 modules listed above. M17 positive control: vm_area `<none>`, vm_prod present. M38: vm_area `<none>`. M32: `32_forestry/dynamic_may24/presolve.gms:17`.
- **Fix**: replace the list with: Module 18 (Residues), Module 29 (Cropland — q29_cropland + q29_carbon), Module 32 (Forestry — `dynamic_may24` afforestation potential, reads vm_area.l/.lo), Module 41 (AEI), Module 42 (Water Demand), Module 50 (N Soil Budget), Module 53 (Methane — rice only), Module 59 (SOM). Remove Module 17 and Module 38.

### BUG-30-2 (Critical) — Downstream Dependencies "Modules Using vm_area": same phantom M17/M38, omitted M29/M32
- **Class**: 15 / wrong consumer set.
- **Trigger**: R20 anchor.
- **Doc**: module_30.md:1493-1502 ("Downstream Dependencies (Modules Using vm_area)"). Lists 17, 18, 38, 41, 42, 50, 53, 59.
- **Reality**: identical to BUG-30-1 — same set error.
- **Evidence**: same grep as BUG-30-1.
- **Fix**: same corrected set as BUG-30-1 (drop 17, 38; add 29, 32).

### BUG-30-3 (Critical) — vm_carbon_stock_croparea "Used by" claims direct M52/M56 consumption (contradicts code AND the doc's own §6 fix)
- **Class**: 15 / MANDATE-17 (transitive vs direct). This is the verbatim R24 Q4-B3 bug; the §6 narrative (line 369) was corrected but the Interface block was not.
- **Trigger**: R20/MANDATE-17 — wrong consumer set; misleads modification-safety reasoning.
- **Doc**: module_30.md:614-616 ("Used by: Module 52 (Carbon)... Module 56 (GHG Policy)").
- **Reality**: only Module 29 reads `vm_carbon_stock_croparea` (simple:31, detail:40). M52/M56 read the aggregated `vm_carbon_stock` from M29's `q29_carbon`, NOT `vm_carbon_stock_croparea`.
- **Evidence**: `grep -rn "vm_carbon_stock_croparea" modules/ | grep -v 30_croparea` → only `29_cropland/{simple_apr24:31,detail_apr24:40}/equations.gms`.
- **Fix**: change "Used by" to: "Module 29 (Cropland) only — aggregated into cluster-level `vm_carbon_stock(j,\"crop\",ag_pools)` via `q29_carbon` (`modules/29_cropland/simple_apr24/equations.gms:31`, `detail_apr24/equations.gms:40`). M52/M56 read the aggregate `vm_carbon_stock`, not `vm_carbon_stock_croparea` directly." (Mirror the already-correct §6 wording at line 369.)

### BUG-30-4 (Major) — "Depends On (6 modules)" invents M16 (Demand) and M13 (TC) as direct dependencies
- **Class**: 2 (causal-mechanism provenance) / MANDATE-17.
- **Trigger**: §1 Major — wrong about behavior (transitive presented as direct dependency).
- **Doc**: module_30.md:1344-1348. Lists Module 16 (Demand) "Demand signals for crop allocation" and Module 13 (TC) "Technological change affecting productivity" as 2 of the dependencies.
- **Reality**: Module 30 reads no demand variable and no TC variable in any of its `.gms` files. Direct providers are M10 (vm_land), M14 (vm_yld), M41 (vm_AEI). TC reaches M30 only transitively (M13 → M14 yields → vm_yld). The doc's own "Critical Dependencies" block (lines 1486-1491) correctly lists M10/M14/M11/M41.
- **Evidence**: `grep -rhoE "(vm_|pm_|im_|fm_|sm_)..." modules/30_croparea/*/{equations,presolve,preloop}.gms | sort -u` → no vm_dem*, no TC var. Direct external inputs: vm_yld, vm_land, vm_AEI, fm_carbon_density, fm_bii_coeff, fm_luh2_side_layers, pm_avl_cropland_iso, sm_fix_SSP2.
- **Fix**: replace M16/M13 entries with the real direct providers (M10 Land via vm_land; M41 AEI via vm_AEI), or relabel M13/M16 explicitly as "indirect (via M14 yields / global optimization), not a direct variable read." Keep M14.

### BUG-30-5 (Major) — "29 crop groups" contradicts code (30 max / 36 total) and the doc's own §3
- **Class**: 6 (hardcoded counts drift).
- **Trigger**: §1 Major — fabricated/stale count for a set.
- **Doc**: module_30.md:45 ("Full rotational constraints system (29 crop groups)"), 1030 ("29 crop rotation groups"), 1274 ("rotation diversity requirements (29 crop groups)"), 1463 ("50% of 29 crop groups").
- **Reality**: detail_apr24 `rotamax30` = 30 members; `rotamin30` = 6; full `rota30` = 36. The doc's own §3 says "30 maximum constraint groups" (line 157) and "6 minimum constraint groups" (line 201).
- **Evidence**: `modules/30_croparea/detail_apr24/sets.gms:16-25` (rota30, 36 names), :27-35 (rotamax30, 30 names), :37-38 (rotamin30, 6 names).
- **Fix**: replace "29 crop groups" with "30 maximum + 6 minimum rotation groups (36 total rota30 rules)" (or "30 max-constraint crop groups" where the max set is meant).

### BUG-30-6 (Minor) — vm_area declaration cited as `declarations.gms:21` without realization; default (simple) is :18
- **Class**: 10 (stale/imprecise file:line citation) / MANDATE-16 (full path needed).
- **Trigger**: §1 Minor → Major boundary; the cited line is correct for detail_apr24 but the doc's stated default is simple_apr24, where it is :18. Adjacent content differs only by realization, so a careful reader checking the default file finds the wrong line. Tie-breaker → Minor.
- **Doc**: module_30.md:570 ("Declaration: `declarations.gms:21`").
- **Reality**: simple_apr24/declarations.gms:18 (default); detail_apr24/declarations.gms:21.
- **Evidence**: both declarations.gms read; `vm_area(j,kcr,w)` at simple L18, detail L21.
- **Fix**: "Declaration: `modules/30_croparea/simple_apr24/declarations.gms:18` (default) / `detail_apr24/declarations.gms:21`". Apply the same realization-qualification to vm_rotation_penalty (simple:19/detail:22) and vm_carbon_stock_croparea (simple:20/detail:23) in the same block, and to the Conservation-Laws references to `declarations.gms:21,22,23,24,25,26` (lines 1225,1233,1253) which are detail-only line numbers.

---

## Deferred (NOT edited — not cleanly code-verifiable or low-confidence)

- "Centrality Rank 5 of 46", "15 total connections", "provides to 9 / depends on 6" (lines 1329-1330,
  1356) — sourced from `core_docs/Module_Dependencies.md`, not directly code-checkable here; the
  "provides to 9 / depends on 6" counts are internally inconsistent with the corrected sets but I did
  not verify the Module_Dependencies table. Flag for a cross-doc pass.
- "Provides To (9 modules)" list (lines 1333-1342) includes Module 73 (Timber) and Module 52 (Carbon).
  M52 is explicitly caveated "(indirectly)" (OK). M73 "Bioenergy tree production" is via the vm_prod
  (betr) chain, not a vm_area read — defensible as a production-chain link; not flagged as a hard bug.
- q30_betr_missing "Conditional ... (presolve.gms:47)" (line 98): the `$()` conditional is inline in
  equations.gms:21, not presolve; presolve:47 sets the penalty/target fix. Citation is imprecise but
  not clearly wrong (presolve does control the penalty). Left as-is.
- Key Files Summary line counts (lines 1686-1697) are wc+1 vs actual (trailing-newline counting):
  decl 69→doc70, eq 107→108, sets 109→110, input 96→97, preloop 50→51, presolve 61→62, postsolve
  86→87. Off-by-one, Informational; not worth an edit. (detail_apr24 also has a `scaling.gms` not in
  the table — minor omission.)
- BII coefficient magnitude guesses ("likely ~0.3", "likely 0.5 vs 0.3", lines 397, 429) are
  hedged-speculative and labeled "likely"; not code claims. Left as-is.
- "Verification Summary" / footers claiming "12 equations" and "Zero Errors" (lines 1691, 1704-1714,
  1721) describe detail_apr24 as if canonical; metadata, not acted-on content → would be Informational.

---

## Mechanical-check notes
- M1 (file:line present): pass — doc is citation-dense and detail citations verify.
- M2 (active realization stated): pass for the header note, but the Interface/Dependencies/Algorithm
  sections silently use detail_apr24 line numbers while the stated default is simple_apr24 — the
  source of BUG-30-6 and the deferred footer items.
