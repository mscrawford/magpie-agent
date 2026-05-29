# Doc Audit: cross_module/nitrogen_food_balance.md (Round 30)

**Auditor**: Opus adversarial doc-auditor
**Ground truth**: `/tmp/magpie_develop_ro` @ `ee98739fd` (Merge PR #887)
**Config**: `/tmp/magpie_develop_ro/config/default.cfg`
**Date**: 2026-05-29

---

## Realization / default verification (all PASS)

| Module | Doc-implied realization | Default (default.cfg) | Dir exists | Verdict |
|--------|------------------------|-----------------------|-----------|---------|
| 50 nr_soil_budget | macceff_aug22 | `macceff_aug22` | yes (only one) | OK |
| 51 nitrogen | rescaled_jan21 | `rescaled_jan21` | yes (+off) | OK |
| 59 som | cellpool_jan23 | `cellpool_jan23` | yes (+static_jan19) | OK |
| 16 demand | sector_may15 | `sector_may15` | yes (only one) | OK |
| 17 production | flexreg_apr16 | `flexreg_apr16` | yes (only one) | OK |
| 21 trade | selfsuff_reduced | `selfsuff_reduced` | yes (+exo, +bilateral22) | OK |

`grep -E "cfg\$gms\$(nr_soil_budget|nitrogen|som|demand|production|trade|awms)" config/default.cfg` → all confirmed.

---

## Verified-correct load-bearing claims

1. **`vm_nr_inorg_fert_reg(i,land_ag)`** declared `modules/50_nr_soil_budget/macceff_aug22/declarations.gms:10`. Doc line 32 cites this declaration file correctly. ✓
2. **`vm_manure_recycling` from M55** — declared `modules/55_awms/ipcc2006_aug16/declarations.gms:21` (`vm_manure_recycling(i, npk)`). Doc line 34 correct. ✓
3. **`v50_nr_surplus_cropland`** — declared `declarations.gms:16`, defined `equations.gms:46-49`. Doc lines 59, 60 correct. ✓
4. **`s51_snupe_base`** + NUE-rescaling emission formula — Doc line 64 `emission = source / (1 - s51_snupe_base) * (1 - vm_nr_eff) * ef` matches code structure `vm_nr_inorg_fert_reg / (1-s51_snupe_base) * (1-vm_nr_eff(i2)) * i51_ef_n_soil` (`modules/51_nitrogen/rescaled_jan21/equations.gms:33-35`). ✓ (`ef` = `i51_ef_n_soil`, faithful conceptually.)
5. **Pollutant set members** `n2o_n_direct`, `n2o_n_indirect`, `nh3_n`, `no2_n`, `no3_n` (doc lines 54-57) — all real set members in `modules/56_ghg_policy/price_aug22/sets.gms:171-205` (`pollutants_all`, `n_pollutants_direct`). ✓
6. **`q21_trade_glo` equation** (doc lines 167-172) — EXACT match to code `modules/21_trade/selfsuff_reduced/equations.gms:12-14`: `sum(i2,vm_prod_reg(i2,k_trade)) =g= sum(i2, vm_supply(i2,k_trade)) + sum(ct,f21_trade_balanceflow(ct,k_trade));`. Cite `:12-14` correct. ✓
7. **`vm_import` / `vm_export` do NOT exist** (doc line 176) — CONFIRMED: `grep -rln "vm_import" modules/` → exit 1 (no match); `vm_export` → exit 1; positive control `vm_supply` → found in M16/M21. Doc's strong claim is correct. ✓
8. **`v21_excess_dem`, `v21_excess_prod`** (doc line 176) — real (`equations.gms:48, 57`). ✓
9. **`vm_supply(i,kall)`** declared M16 `sector_may15/declarations.gms:11`. **`vm_prod_reg(i,kall)`** declared M17 `flexreg_apr16/declarations.gms:10`. ✓
10. **`q17_prod_reg`** (doc line 153) — code `vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k))` (`modules/17_production/flexreg_apr16/equations.gms:10-11`). Doc pseudocode faithful. ✓
11. **Part 2.8 waste machinery** — `v16_dem_waste(i,kall)` (decl:12), `q16_waste_demand` (decl:22, eq:69-71), `f16_waste_shr` (input.gms:15). ALL correct. ✓
12. **`f21_trade_balanceflow`** — `selfsuff_reduced/input.gms:37` "Domestic balance flows"; used in q21_trade_glo:14. Doc characterization (residual) reasonable. ✓
13. **M59 SOM N interfaces** — `vm_nr_som(j)` + `vm_nr_som_fertilizer(j)` declared `modules/59_som/cellpool_jan23/declarations.gms:45-46`; read by M50 (eq:30) and M51 (eq:58). Doc's M59→M50/M51 N link correct. ✓

---

## Bugs found

### Bug 1 — Module 13 falsely credited with "N-responsive yields" (Major)

- **doc_line**: nitrogen_food_balance.md:103
- **Claim**: "Module 13 (TC) handles N-responsive yields, but default assumes N met"
- **Reality**: Module 13 (technological change) contains ZERO references to nitrogen. It models land-use intensity via the tau factor / yield-increasing technological-change investment. There is no N→yield response mechanism anywhere in M13.
- **file_evidence**: `modules/13_tc/` (realizations `endo_jan22` [default], `exo`).
- **verify_cmd**: `grep -rln "nitrogen" /tmp/magpie_develop_ro/modules/13_tc/` → exit 1 (NO MATCH). Positive control `grep -rln "tau|vm_tau|landuse_intensity" .../13_tc/` → 20 files matched. So tau is pervasive, nitrogen absent.
- **Severity rationale**: Wrong module characterization of a mechanism (MANDATE 6). Decision tree: not a cost-var attribution (Critical #7 no); falls to Major "wrong in a way that misleads about behavior" — a user wanting to model N-limited yields would be pointed at M13 and find nothing about nitrogen. The N↔yield linkage that DOES exist is NUE (`vm_nr_eff`, M50) controlling fertilizer needed to meet withdrawals from production; there is no N-limitation-on-yield feedback.
- **confirmed**: true
- **proposed_fix**: Replace line 103 with: "MAgPIE has no N-limitation-on-yield feedback. Nitrogen demand (`vm_nr_inorg_fert_reg`, a free variable in Module 50) adjusts to meet crop withdrawals at the given nutrient-use efficiency (`vm_nr_eff`); yields are set independently (Modules 14/13 tau), so fertilizer follows yields rather than constraining them."

### Bug 2 — Citation `equations.gms:18-30` points at the inputs-sum, not the balance constraint (Minor)

- **doc_line**: nitrogen_food_balance.md:38 (repeated at :74)
- **Claim**: "Source: Module 50, `modules/50_nr_soil_budget/macceff_aug22/equations.gms:18-30`" attached to the "Key Equation (nitrogen soil budget)" `vm_nr_inorg_fert_reg + other_inputs ≥ N_withdrawal`, and to "Inputs = Outputs + ΔSoil_N_stock".
- **Reality**: Lines 18-30 are `q50_nr_inputs` (an `=e=` definition summing all N inputs), NOT a balance/inequality. The crop N balance constraint shown (`... =g= ... withdrawals`) is `q50_nr_bal_crp` at lines **14-16**.
- **file_evidence**: `modules/50_nr_soil_budget/macceff_aug22/equations.gms:14-16` (q50_nr_bal_crp), `:22-32` (q50_nr_inputs).
- **verify_cmd**: `cat -n .../50_nr_soil_budget/macceff_aug22/equations.gms` → line 14 `q50_nr_bal_crp(i2) ..`, line 15 `vm_nr_eff(i2) * v50_nr_inputs(i2)`, line 16 `=g= sum(kcr,v50_nr_withdrawals(i2,kcr));`; lines 18-21 are comment, 22 `q50_nr_inputs(i2) ..`.
- **Severity rationale**: Citation to adjacent-but-different content (inputs equation vs balance constraint). Same module/realization, closely related nitrogen-budget material, so a reader reading 14-30 still sees the whole crop balance → tie-breaker pulls to Minor (tier_uncertainty: could be Major under the "drift to different content" trigger).
- **confirmed**: true
- **proposed_fix**: Change both `equations.gms:18-30` citations (doc lines 38 and 74) to `equations.gms:14-16` (the balance `q50_nr_bal_crp`), or `:14-32` to span balance + inputs.

### Bug 3 — Doc asserts a soil-N "pool" state that does not exist in the code (Minor)

- **doc_line**: nitrogen_food_balance.md:94 (related: :83, :86)
- **Claim**: "Soil nitrogen pool can go negative (physically impossible)"; "Soil N pool can increase (accumulation) or decrease (depletion)"; "Expanded" budget adds `+ ΔSoil_pool` to outputs.
- **Reality**: Module 50 declares NO soil-N stock/state variable. All M50 variables are flows: `v50_nr_inputs`, `v50_nr_withdrawals`, `v50_nr_surplus_cropland`, `v50_nr_deposition`, plus efficiencies `vm_nr_eff(_pasture)`. The "surplus" is a residual flow (inputs − withdrawals) that exits as emissions/leaching; there is no pool that accumulates across timesteps or that "can go negative."
- **file_evidence**: `modules/50_nr_soil_budget/macceff_aug22/declarations.gms:10-20` (full variable list — no stock term).
- **verify_cmd**: `grep -nE "^\s+(v50_|i50_|p50_|vm_nr)" .../50_nr_soil_budget/macceff_aug22/declarations.gms` → only flows/efficiencies/rates; `grep -rn "soil_n|nr_soil_stock|v50_nr_pool" .../50_nr_soil_budget/` → no match.
- **Severity rationale**: The surrounding prose explicitly and correctly states N is "NOT a Conservation Law", "NO Strict Constraint", surplus unconstrained — so the reader gets the right top-level message and is not led to a wrong edit. The narrow factual error is asserting a *pool state variable* exists. Tie-breaker → Minor (tier_uncertainty: a strict reading of "Fabricated formula" could push the ΔSoil_pool budget toward Major, but it is labeled conceptual and hedged).
- **confirmed**: true
- **proposed_fix**: Reword to flow language. Line 94 → "**No soil-N stock tracked**: the N surplus (`v50_nr_surplus_cropland` = inputs − withdrawals) is an unconstrained residual flow that leaves the system as emissions/leaching; MAgPIE does not carry a soil mineral-N pool across periods, so it cannot enforce that withdrawals never exceed available soil N." Drop `+ ΔSoil_pool` from the "Expanded" block (lines 81-84) or relabel it "(residual = surplus, not a tracked pool)".

### Bug 4 — Module 16 mischaracterized as "calculating" food demand (Minor)

- **doc_line**: nitrogen_food_balance.md:116 (related: table at :130-140)
- **Claim**: "Module 16 (Demand): Calculates food, feed, processing demands"; Part 2.2 table "Module 16 Calculates" with Food / "income elasticity 0.3-0.8" / "diet preferences".
- **Reality**: Module 16 (`sector_may15`) AGGREGATES demand streams into `vm_supply` (`q16_supply_*`). Its own equations note (`equations.gms:15-17`): "Demand for seed, waste and the domestic balance flow are calculated internally within the [16_demand] module, while the other relevant demand values are taken from other modules." Food demand `vm_dem_food` is declared and owned by Module 15 (`modules/15_food/anthro_iso_jun22/declarations.gms:14`); feed by M70, processing by M20, material by M62, bioenergy by M60. Income elasticities / diet preferences live in M15, not M16.
- **file_evidence**: `modules/16_demand/sector_may15/equations.gms:15-17, 19-29`; `modules/15_food/anthro_iso_jun22/declarations.gms:14`.
- **verify_cmd**: `grep -rln "vm_dem_food" modules/*/*/declarations.gms` → `modules/15_food/anthro_iso_jun22/declarations.gms`; M16 q16_supply_crops sums `vm_dem_food + vm_dem_feed + vm_dem_processing + ...` (does not compute them).
- **Severity rationale**: Wrong module characterization (MANDATE 6). The doc DOES acknowledge M15's calorie/diet role later (lines 196-198, 142-145), bounding the harm; tie-breaker → Minor. (Could be Major if a reader trusted only Part 2.2 and looked for food-demand elasticities in M16.)
- **confirmed**: true
- **proposed_fix**: Line 116 → "Module 16 (Demand): **Aggregates** food, feed, processing, material, bioenergy, seed and waste demand into `vm_supply` (food demand itself is computed in Module 15; feed M70; processing M20; material M62; bioenergy M60; seed and waste internal to M16)." In the Part 2.2 table, retitle "Module 16 Calculates" → "Demand components aggregated by Module 16 (sources in parentheses)" and tag Food→M15, Feed→M70, Processing→M20, Material→M62.

### Bug 5 — Food Balance labeled "Equality" in summary table; code is inequality (`=g=`) (Minor)

- **doc_line**: nitrogen_food_balance.md:281 (related: :112, :289)
- **Claim**: Summary table "**Food Balance** | Flow (**Equality**) | Hard (with trade)"; line 289 "Food: Supply = Demand at global level".
- **Reality**: The global food balance is an inequality. `q21_trade_glo` uses `=g=` (production ≥ supply + balanceflow). The doc's own overview (line 112) more accurately says "inequality constraint (supply ≥ demand) or equality"; the summary table then collapses it to "Equality."
- **file_evidence**: `modules/21_trade/selfsuff_reduced/equations.gms:12-14` (`=g=`).
- **verify_cmd**: `grep -nE "^\s*q21_" .../21_trade/selfsuff_reduced/equations.gms` + read of q21_trade_glo → `=g=`.
- **Severity rationale**: Right concept (production must meet demand), wrong constraint type label. In practice the `=g=` binds tightly (production won't exceed demand without reason), so calling it "equality" is a defensible economic shorthand → Minor, tier_uncertainty.
- **confirmed**: true
- **proposed_fix**: Summary table line 281: "Flow (Equality)" → "Flow (Inequality, supply ≥ demand)". Optionally line 289 → "Food: Supply ≥ Demand at global level (binds tightly via trade)".

---

## Deferred (not code-verifiable / not edited)

- Numerical magnitude ranges in the input/output tables (e.g., "50-250 kg N/ha/yr", "10-40% of N surplus", "income elasticity 0.3-0.8", "1-3% of N applied (IPCC)") — illustrative ranges, not single code constants; not checkable against a scalar default.
- "f21_trade_balanceflow ... near zero outside base period" — quantitative behavioral claim about input data values; not checkable from .gms (would need the .cs3 data).
- Doc lines 196-199 (calories/protein/fat tracked in M15; balance in DM) — directionally consistent with M15 being the food/nutrition module; not deeply verified this round (out of the M50/51/59/16/17/21 scope).
- `q51_emissions_*` glob (doc lines 59, 68) — two of the seven emission equations are named `q51_emissionbal_awms` / `q51_emissionbal_man_past` (not `q51_emissions_*`); substantively M51 does compute all pathways, so this is a harmless wildcard shorthand, not flagged as a bug.
- Part 2.4 "Regional Balance (Module 21, `q21_trade_reg`)": `q21_trade_reg` is the self-sufficiency production-band lower bound, not a supply=demand balance (that role for non-tradables is `q21_notrade`). The equation NAME is correct and the prose ("managed through vm_supply and trade variables") is accurate at a high level; characterization is loose but not clearly wrong → noted, not flagged.

---

## Summary

13 load-bearing code claims verified correct (realizations, q21_trade_glo verbatim, vm_import/vm_export correctly stated non-existent, M16 waste machinery, M59 N interfaces, all variable/equation names). 5 bugs: 1 Major (M13 falsely credited with N-responsive yields — M13 has zero nitrogen refs, models tau), 4 Minor (citation `:18-30`→balance is at `:14-16`; nonexistent soil-N pool asserted; M16 "calculates" vs aggregates food demand; Food Balance labeled "Equality" but code is `=g=`). No Critical: no inverted defaults, no invented variable/equation names, no wrong realization-as-default.
