# Audit Report: Module_Dependencies.md (R49 doc-audit)

**Target doc**: `core_docs/Module_Dependencies.md`
**Ground truth**: `/tmp/magpie_develop_ro` @ HEAD `ee98739fd` (Merge #887; identical to working-tree develop HEAD)
**Auditor model**: Opus (highest capability)
**Date**: 2026-06-06

## Overall Verdict: ACCURATE
## Accuracy Score: 10/10

This is an exceptionally accurate document. Every load-bearing, code-checkable claim I tested reproduced against the develop code, in most cases EXACTLY (interface-variable counts, consumer sets, producer attributions, the 32-cost-var / 27-module decomposition, default realizations, and all spot-checked file:line citations). **0 confirmed bugs.** The only items I could not confirm are a small set of aggregate graph-metric numbers (per-module "Depends On" / "inputs" for trade/demand/bioenergy, the 173-dependency total, the 26-cycle count) whose construction methodology I cannot reproduce from code — these are recorded in `deferred`, NOT as bugs, because (a) my crude alternative metric is demonstrably too coarse and (b) every number whose stated method I COULD reproduce matched exactly.

---

## Verified Claims (correct)

### Executive summary & §1.1 interface-variable system
- **121 interface vars = 83 vm_ + 21 pm_ + 17 im_** — EXACT.
  - `grep -rhoE '\bvm_[A-Za-z0-9_]+' modules/*/*/declarations.gms | sort -u | wc -l` → 83
  - same for pm_ → 21; im_ → 17. Sum 121. ✓
- Producer/consumer/bidirectional design pattern (§1.1) — consistent with code structure.

### §2.1 Most-connected variables (consumer counts via the doc's own stated methodology, line 60: file-presence minus producer)
All seven counts EXACT, and the "Key Modules" producer column verified against `declarations.gms`:
| Variable | Doc count | Code count | Producer (doc → code) |
|---|---|---|---|
| vm_land | 10 | 10 | 10_land (landmatrix_dec18/declarations.gms) ✓ |
| im_pop_iso | 10 | 10 | 09_drivers/aug17/declarations.gms:10 ✓ |
| pm_interest | 9 | 9 | 12_interest_rate/select_apr20/declarations.gms:9 ✓ |
| vm_prod | 8 | 8 | 17_production/flexreg_apr16/declarations.gms:9 ✓ |
| vm_prod_reg | 8 | 8 | 17_production/flexreg_apr16/declarations.gms:10 ✓ |
| vm_area | 8 | 8 | 30_croparea/{simple,detail}_apr24/declarations.gms ✓ |
| vm_bv | 6 | 6 | 44_biodiversity/bv_btc_mar21/declarations.gms:19 ✓ |
| vm_carbon_stock | 7 | 7 | declared 56_ghg_policy/price_aug22/declarations.gms:34 ✓ |
| vm_nr_inorg_fert_costs | 1 | 1 (→11_costs) | 50_nr_soil_budget/macceff_aug22/declarations.gms:11 ✓ |

vm_land consumers (excl 10): 22,29,30,31,32,34,35,50,58,59 (=10). ✓

### §2.2 variable-category names (anti-confabulation — all exist)
pm_land_start, vm_landexpansion, vm_landreduction, vm_lu_transitions, pcm_land (all 10_land); vm_tech_cost (13_tc/exo); vm_emissions_reg, vm_emission_costs (56_ghg_policy/price_aug22); pm_carbon_density_* family = {secdforest, plantation, other}(_ac) — all present. ✓ No hallucinated names found anywhere in the doc.

### §3.2 pure sources / pure sinks
- 09_drivers, 28_ageclass, 45_climate read NO foreign interface vars in their equation/solve files → genuine pure sources (verified by enumerating foreign vm_/pm_/im_ in each module's equations/presolve/postsolve/preloop = empty). ✓
- **09_drivers → 14 modules**: union of consumers across all 09 interface vars (excl 09) = 12,13,15,18,36,38,42,50,55,56,60,62,70,73 (=14). EXACT. ✓
- **28_ageclass → 2 (35_natveg, 52_carbon)**: im_forest_ageclass consumers (excl 28) = exactly {35_natveg, 52_carbon}. EXACT. ✓
- **45_climate → 4 (14,52,58,59)**: pm_climate_class consumers (excl 45) = exactly {14_yields, 52_carbon, 58_peatland, 59_som}. EXACT. ✓
- **80_optimization pure sink** (line 138): default `nlp_apr17` minimizes only vm_cost_glo (nlp_apr17/solve.gms:34); vm_landdiff is `MINIMIZING`-target ONLY in `lp_nlp_apr17/solve.gms` (76,77,196,197) and is in `not_used.txt` for nlp_apr17/nlp_ipopt/nlp_par. EXACT — including the non-default-realization nuance. ✓ (vm_cost_glo declared 11_costs/default/declarations.gms:9; vm_landdiff declared 10_land/landmatrix_dec18/declarations.gms:15.)
- **11_costs ← 32 vars from 27 modules**: `awk '/q11_cost_reg/,/^;/' modules/11_costs/default/equations.gms | grep -oE 'vm_[A-Za-z0-9_]+' | sort -u` → 32 distinct vm_; mapping each to its declaring module → 27 distinct modules. EXACT. ✓
- Realization names `nlp_apr17` (default) and `lp_nlp_apr17` both real (`ls modules/80_optimization/`). ✓

### §4.1 circular / conservation arrows
- vm_land consumed by 22_land_conservation (in the 10-module consumer set) → "10_land → 22 (vm_land)" ✓
- pm_land_conservation declared 22_land_conservation/area_based_apr22/declarations.gms:15; consumers (excl 22) include 35_natveg → "22 → 35_natveg (pm_land_conservation)" ✓

### §4.2 dependency chains
- "...→ 71_disagg_lvst → 11_costs": M71 declares vm_costs_additional_mon; 11_costs reads it. ✓

### §5.1 degradation table
- 58_peatland deps {10_land, 56_ghg_policy}: reads vm_land (M10) ✓; reads vm_emissions_reg (declared M56) ✓ — the M56 link is via vm_emissions_reg, not vm_carbon_stock, but the connectivity claim holds.
- 59_som deps {10_land, 29_cropland, 56_ghg_policy}: reads vm_land ✓ and vm_carbon_stock (M56-declared) ✓.

### §5.2 forestry/timber system
- vm_prod_forestry (32→73): declared 32_forestry/dynamic_may24/declarations.gms:73; consumed by 73_timber. ✓
- vm_prod_natveg (35→73): declared 35_natveg/pot_forest_may24/declarations.gms:88. ✓
- pm_demand_forestry (73→32): declared 73_timber/default/declarations.gms:11; consumed by 32_forestry/dynamic_may24/presolve.gms (multiple lines). ✓
- **Dashed-arrow claim "M32 does not consume any M14 yield variable (verified R3+R4)"** — CONFIRMED via the high-risk double-check: `rg 'vm_yld\(' modules/32_forestry/` → exit 1; `rg 'vm_yld\.' modules/32_forestry/` → exit 1; `rg 'pm_yields_semi_calib' modules/32_forestry/` → exit 1; positive control `rg 'vm_land' modules/32_forestry/` → hits. M14 declares exactly {vm_yld, pm_yields_semi_calib}; neither is read by M32. ✓ (MANDATE 20 / solution-level form checked.)

### §7.3 yields consumers + citations (all three file:line citations content-verified)
- "Yields (14) - 3 consumers": vm_yld consumers (excl 14) = {30_croparea, 31_past}; pm_yields_semi_calib consumer = {17_production}. Union = 3. EXACT. M14 produces exactly these two interface vars, so 3 is the complete set. ✓
- `modules/30_croparea/simple_apr24/equations.gms:15` contains `vm_yld` (q30_prod). ✓
- `modules/31_past/endo_jun13/equations.gms:18` contains `vm_yld`. ✓
- `modules/17_production/flexreg_apr16/presolve.gms:10` contains `pm_yields_semi_calib`. ✓

### Defaults / realization names
- M14 default `managementcalib_aug19` (config/default.cfg:354), only realization. ✓
- M80 default `nlp_apr17` (config/default.cfg:2282). ✓

### §1.2 centrality (the subset reproducible by stated method)
- 11_costs Depends On 27 ✓ (matches §9 "Maximum dependencies: 27").
- 09_drivers Provides To 14 ✓.
- 32_forestry Depends On 11 ✓ (my distinct-producer-module count also = 11; matches §6.2 "11 inputs").
- §9 min dependencies 0 (09,28,45) ✓.

### Internal-consistency note (not a bug)
- §9 "Total 173 / Average 3.84": 173/45 = 3.844 → rounds to 3.84. Consistent under a 45-module denominator (e.g., excluding the terminal sink 80_optimization). Mutually consistent, so NOT flagged.

---

## Bugs Found
**None confirmed.**

---

## Deferred (could not verify against code; NOT edited, NOT proposed as bugs)

1. **§1.2 / §6.2 / §9 aggregate graph metrics for trade/demand/bioenergy** — "21_trade 10 inputs", "16_demand 9 inputs", "60_bioenergy 8 inputs", and the centrality "Depends On" columns for these rows. My crude reproduction (distinct producer-modules of foreign vm_/pm_/im_ read in equation files, producer mapped via declarations.gms/input.gms) gave 21_trade=2, 16_demand=6, 60_bioenergy=1 — but this metric is demonstrably too coarse: e.g., 21_trade plainly reads vm_prod_reg (M17) + vm_supply (M16) and obviously depends on more than 2 modules via f21_*/i21_* input parameters and assignment-populated pm_. I cannot reconstruct the doc's original graph-construction algorithm (`/tmp/magpie_analysis/` artifacts referenced in §10 are not present), and every number whose stated method I COULD reproduce matched exactly. Insufficient evidence to call these wrong.

2. **"173 inter-module dependencies"** and **"26 circular dependency cycles"** (exec summary, §4, §9) — aggregate counts from the same unreproducible analysis. No code-derivable ground truth without re-running the original dependency-graph script. The 173/45=3.84 internal consistency check passes; the cycle count is not independently checkable here.

3. **§1.2 centrality "Provides To / Depends On" for rows I did not exhaustively reproduce** (e.g., 56_ghg_policy 13/3, 10_land 15/2, 17_production 13/1, 30_croparea 9/6, 70_livestock 7/7, 29_cropland 6/7, 35_natveg 5/7) — same methodology dependence. Spot-checks of the reproducible subset (11_costs=27, 09_drivers=14, 32_forestry=11) all matched, which raises confidence in the table, but I did not verify every cell.

4. **§6.1 "1 connection" counts for 37_labor_prod / 45_climate / 54_phosphorus** — verified the qualitative claim (these modules read no foreign interface vars → genuinely low-centrality/independent), but the exact integer "1" is the doc's edge metric (presumably their single output edge to a consumer), not separately reproduced.

---

## Missing nuances (informational, not scored)
- §2.1 places `vm_nr_inorg_fert_costs` (1 consumer) inside a table titled "Highest Consumer Count" — it is the LOWEST. It is clearly there to illustrate the producer→consumer notation (row note "Consumers count excludes the producer module"), and the count 1 is correct, so not a content error.
- §5.1 "Key Dependencies" columns are curated highlights, not exhaustive consumer-of sets; verified the listed links are real (no false links found).

## Summary
Module_Dependencies.md is code-faithful. All interface-variable counts (121 = 83+21+17), §2.1 consumer counts (9/9 exact), producer attributions, pure-source/pure-sink sets, the 32-var/27-module 11_costs decomposition, M14's 3-consumer set, M32's "no M14 yield" claim (double-checked with attribute-form grep + positive control), and all spot-checked file:line citations reproduce against develop HEAD ee98739fd. 0 confirmed bugs. Unreproducible aggregate graph metrics (per-module input counts for trade/demand/bioenergy, 173 total deps, 26 cycles) are deferred, not flagged — every number whose method I could reproduce was exact.
