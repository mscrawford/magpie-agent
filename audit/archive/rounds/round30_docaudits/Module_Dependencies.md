# Round 30 Doc Audit — core_docs/Module_Dependencies.md

**Auditor**: adversarial doc auditor (Opus, highest capability)
**Date**: 2026-05-29
**Ground truth**: `/tmp/magpie_develop_ro` @ `ee98739fd` (Merge PR #887)
**Config**: `/tmp/magpie_develop_ro/config/default.cfg`
**Method**: MANDATE 3/8/13/16/17 applied. Every consumer/populator SET enumerated from code via `rg -l` (cross-checked with a second method + positive control on declared-name presence). File:line citations re-read in current develop. Count claims reproduced with the doc's own stated grep methodology (line 60 footer).

## Overall Verdict: ACCURATE
## Accuracy Score: 9.5/10

This is one of the most accurate docs audited. The counts were demonstrably recomputed against current code (footers dated R3/R5, 2026-05-23/24) and they still hold at HEAD `ee98739fd`. The single confirmed issue is a Minor internal arithmetic inconsistency in the executive summary. Everything load-bearing — producer attributions, consumer SETS, file:line citations, realization defaults, the 32-cost-variable / 27-module aggregation, the optimization-sink default nuance, the G2 carbon-stock declaration distinction — verified exactly.

---

## Verified Claims (correct)

### Interface variable system (lines 16-18)
- `vm_` = 83, `pm_` = 21, `im_` = 17 distinct names in declarations files. **All three verified exactly.**
  `rg -oN 'vm_\w+' modules/ -g 'declarations.gms' | sed 's/.*://' | sort -u | wc -l` → 83; pm_ → 21; im_ → 17.

### Most-connected variables table (lines 50-58) — consumer counts via doc's stated methodology (line 60: distinct modules referencing the var, minus producer)
- `vm_land` = 10 ✓; `im_pop_iso` = 10 ✓ (11 referencing modules − producer 09); `pm_interest` = 9 ✓; `vm_prod` = 8 ✓; `vm_prod_reg` = 8 ✓; `vm_area` = 8 ✓; `vm_carbon_stock` = 7 ✓; `vm_bv` = 6 ✓; `vm_nr_inorg_fert_costs` = 1 ✓ (consumed by 11_costs only).
  All reproduced with `rg -l '\bVAR\b' modules/ -g '*.gms' | awk -F/ '{print $2}' | sort -u | grep -v PRODUCER | wc -l`.

### Producer attributions (lines 50-58, 79, 84, 232-234)
- `vm_land`→10_land; `vm_prod`/`vm_prod_reg`→17_production; `vm_area`→30_croparea; `vm_bv`→44_biodiversity; `vm_prod_forestry`→32_forestry; `vm_prod_natveg`→35_natveg; `vm_tech_cost`→13_tc; `vm_emissions_reg`→56_ghg_policy; `vm_nr_inorg_fert_costs`→50_nr_soil_budget; `pm_demand_forestry`→73_timber; `pm_land_conservation`→22_land_conservation. **All verified in declarations.gms.**

### G2 anchor — `vm_carbon_stock` declaration (critical distinction)
- DECLARED in Module 56 `price_aug22/declarations.gms:34` (NOT Module 52). Verified. Doc line 56 frames "56_ghg_policy → multiple" as the source/producer — correct.
- Referencing modules: 29, 31, 32, 34, 35, 52, 56, 59. M52 READS it (`normal_dec17/equations.gms:19`); land modules + 59 POPULATE it. Doc's count of 7 consumers = 8 referencing − producer 56 ✓ (consistent with its stated methodology, line 60).

### File:line citations (Yields section, lines 331-332)
- `vm_yld` consumed by croparea at `modules/30_croparea/simple_apr24/equations.gms:15` — **verified** (q30_prod, line 15).
- `vm_yld` consumed by past at `modules/31_past/endo_jun13/equations.gms:18` — **verified** (q31_prod spans 16-18; vm_yld on line 18).
- `pm_yields_semi_calib` consumed by production at `modules/17_production/flexreg_apr16/presolve.gms:10` — **verified** (line 10).

### Realization names + defaults (MANDATE 8 + 3)
- croparea default `simple_apr24` ✓; past default `endo_jun13` ✓; production `flexreg_apr16` (sole) ✓; optimization default `nlp_apr17` ✓; `lp_nlp_apr17` exists ✓; ghg_policy `price_aug22` ✓; carbon `normal_dec17` ✓. All from `config/default.cfg` + `ls modules/NN_*/`.

### Pure-source / pure-sink claims (lines 132-139)
- `28_ageclass → 2 modules (35_natveg, 52_carbon)` ✓ — `im_forest_ageclass` consumed by exactly 35, 52.
- `45_climate → 4 modules (14_yields, 52_carbon, 58_peatland, 59_som)` ✓ — `pm_climate_class` consumed by exactly those 4.
- `80_optimization ← vm_cost_glo (always; default nlp_apr17 minimizes only this); vm_landdiff additionally consumed only by non-default lp_nlp_apr17` ✓ — `nlp_apr17` references only `vm_cost_glo`; `lp_nlp_apr17` references `vm_cost_glo` + `vm_landdiff`. **Default nuance is precisely correct.**
- `11_costs ← 32 distinct cost vars from 27 source modules` ✓✓ — `awk '/^ q11_cost_reg/,/^;/' modules/11_costs/default/equations.gms | grep -oE 'vm_\w+' | sort -u | wc -l` → 32; mapping each var to its declaring module → 27 distinct modules. Both load-bearing counts exact. `q11_cost_reg` equation confirmed at `modules/11_costs/default/equations.gms:15`.

### Circular / chain claims (Section 4)
- `22_land_conservation → 35_natveg (pm_land_conservation)` ✓ (35 is a consumer; full consumer set 13,29,31,32,35).
- `10_land → 22_land_conservation (vm_land)` ✓ (22 reads vm_land in presolve_ini.gms).
- Cost chain `12→13→14→17→71→11`: `13_tc→14_yields` via `vm_tau` ✓; `71_disagg_lvst→11_costs` via `vm_costs_additional_mon` (`11_costs/default/equations.gms:40`) ✓.

### High-risk module consumer counts (Section 7.3)
- `Production (17) - 13 consumers` ✓ exactly (union vm_prod + vm_prod_reg = 16,18,20,21,30,31,38,40,42,50,70,71,73).
- `Land (10) - 18 consumers` ✓ exactly — partial 5-var union gives 15, but full union over all 9 M10 interface vars (adds vm_cost_land_transition, vm_landdiff, pm_land_hist, pm_land_start → +11_costs,14_yields,80_optimization) = 18. The doc's "etc." covers the remainder.
- `Carbon (52) - 4 consumers` ✓ — full union over all 5 M52 `pm_carbon_density_*_ac` outputs (incl. uncalib variants, consumed by 29_cropland) = 14_yields, 29_cropland, 32_forestry, 35_natveg = 4. (Calibrated-only subset is 3; the uncalib variants add 29 — multi-method check caught this.)
- `Yields (14) - 3 consumers` ✓ — M14 declares exactly vm_yld + pm_yields_semi_calib; full consumer union = 17, 30, 31 = 3.

### Variable existence spot-checks (MANDATE 7)
- pm_land_start, vm_landexpansion, vm_landreduction, vm_lu_transitions, pcm_land (all 10_land), pm_land_conservation (22), vm_emissions_reg (56) — all exist, correctly attributed. `pm_carbon_density_*` "secdforest, plantation, other" (line 85) ✓ — matches 52's 5 declared density params.

---

## Bugs Found

### Bug DEP-B1 — Executive-summary interface-variable total inconsistent with own table
- **Severity**: Minor
- **Class**: 6 (Hardcoded counts drift) — internal inconsistency variant
- **Trigger**: §1 Minor — "Wrong detail, but a careful reader wouldn't be misled into action." (Tie-breaker pulls down: I cannot prove 115 is *wrong* under a stricter "cross-consumed" definition, but it is reproducibly inconsistent with the doc's own table total of 121.)
- **Claim in doc** (`Module_Dependencies.md:6`): "The analysis identified **115 interface variables** facilitating 173 inter-module dependencies..."
- **Reality in code**: The doc's own table (lines 16-18) breaks interface variables into vm_=83, pm_=21, im_=17, which sums to **121**, not 115. All three table values are code-verified exactly (83/21/17 distinct names in declarations.gms). 115 ≠ 121.
- **File evidence**: `Module_Dependencies.md:6` (prose "115") vs `Module_Dependencies.md:16-18` (table 83+21+17=121); code: `rg -oN 'vm_\w+' /tmp/magpie_develop_ro/modules/ -g 'declarations.gms' | sed 's/.*://' | sort -u | wc -l` → 83 (and 21 / 17 for pm_/im_).
- **verify_cmd**: `rg -oN 'vm_\w+' /tmp/magpie_develop_ro/modules/ -g 'declarations.gms' | sed 's/.*://' | sort -u | wc -l` → `83`; pm_ → `21`; im_ → `17`; sum = 121.
- **Confirmed**: true (the 83/21/17 → 121 sum is reproducible and contradicts the line-6 "115").
- **Proposed fix**: Reconcile the executive-summary total with the verified table. Replace line 6 "115 interface variables" with "121 interface variables (83 vm_ + 21 pm_ + 17 im_; see §1.1)". If the original 115 was deliberately the count of variables that actually cross a module boundary (a subset of the 121 declared), instead clarify: "121 declared interface variables (83 vm_ + 21 pm_ + 17 im_), of which 115 are consumed cross-module". Do NOT change the table (83/21/17 are correct).

---

## Deferred (not code-verifiable / soft aggregate / scoping choice — NOT edited)

- **Centrality table "Provides To / Depends On" splits (lines 31-40)** and aggregate per-module "connections"/"dependencies" figures (Section 5/6 tables, lines 209-213, 254-273, 315-330 totals like "52_carbon ... 5", "11_costs 28/1/27"): produced by an external analysis tool with an unstated edge-counting convention (directional edges per module-pair, possibly deduped differently from raw var-reference counts). The component claims I could pin to a variable set verified; the rolled-up totals are not reproducible without the original tool's methodology. No confident bug.
- **"173 inter-module dependencies" and "26 circular dependency cycles" (lines 6, 150, 384, 388)**: graph-level aggregates from the analysis tool; not independently reproducible from greps. Internally consistent across the doc (173 and 26 each appear consistently).
- **`pm_demand_forestry` framed as "(73 → 32)" (line 234)**: variable also genuinely consumed by 62_material (`exo_flexreg_apr16/equations.gms:37`). But this is inside the "Forestry/Timber System" subsystem graph (Section 5.2), where restricting to the 32↔73 edge is a deliberate scoping choice, not a "consumers-of-X" table. Informational at most; not edited.
- **Croparea↔41 AEI cycle (lines 170-174, 239)**: `vm_AEI` is consumed by 30_croparea ONLY in `detail_apr24` (non-default); the default `simple_apr24` does NOT consume vm_AEI (`modules/30_croparea/detail_apr24/equations.gms:82` is the sole hit). The cycle therefore exists only under the non-default realization. The doc's circular-dependency analysis is an inherently structural (union-over-realizations) view and does not claim default-activity, so this is a nuance rather than a clear error. Flagged for awareness; not edited (adding a default caveat would be an improvement but is a judgment call, not a code-contradiction).
- **Architectural-layer module groupings (lines 93-128) and "09_drivers provides to 14 modules" (lines 38, 133)**: characterizations / aggregate provider counts; the structural direction (09_drivers has no upstream deps; declares many im_*) is consistent with code, but the exact "14" is a soft count tied to the analysis tool.
