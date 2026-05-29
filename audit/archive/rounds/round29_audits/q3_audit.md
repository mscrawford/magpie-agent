# Audit Report: Q3 (Food/Material Supply≥Demand Enforcement + Cropland Soil-N Budget)

**Round**: R29 | **Auditor**: Opus (adversarial) | **Date**: 2026-05-29
**Verification worktree**: `/tmp/magpie-develop-r29/` @ `ee98739fd` (clean origin/develop)
**Answer audited**: `audit/archive/rounds/round29_answers/q3_answer.md`

---

### Overall Verdict: MOSTLY ACCURATE
### Accuracy Score: 8/10

The answer is structurally correct and unusually well-cited. Every equation name, constraint operator (`=g=` vs `=e=`), file:line range for the core equations, and the NUE-rescaling mechanism is verified against code. Two defects: one off-by-one declaration citation (`vm_prod_reg` cited at `declarations.gms:9`, actually line 10 — line 9 is a *different* variable `vm_prod`), and one set-member-label imprecision ("residues" for the three distinct `k_notrade` members `res_cereals/res_fibrous/res_nonfibrous`, inherited from a wrong doc line). One latent doc bug recorded (§1.5).

---

### Verified Claims (correct)

**Realizations** — all default, all correctly named:
- M15 `anthro_iso_jun22`, M16 `sector_may15`, M21 `selfsuff_reduced`, M50 `macceff_aug22`, M51 `rescaled_jan21` — all confirmed against `config/default.cfg`. M17 single-realization `flexreg_apr16`.

**Part (a) — supply ≥ demand:**
- `q15_food_demand(i2,kfo)` at `modules/15_food/anthro_iso_jun22/equations.gms:10-14` — EXACT match incl. `f15_household_balanceflow`, `fm_nutrition_attributes(...,"kcal")*10**6`, `im_pop * p15_kcal_pc_calibrated * 365`, and `=g=`. ✓
- `q16_supply_crops(i2,kcr)` at `equations.gms:19-29` — formula verbatim correct (8 demand streams + domestic balanceflow), `=e=` correct. ✓
- All 5 sibling supply equations exist and named correctly: `q16_supply_livestock` (31), `q16_supply_secondary` (40), `q16_supply_residues` (51), `q16_supply_pasture` (62), `q16_supply_forestry` (85). ✓
- `q21_trade_glo(k_trade)` at `equations.gms:12-14` — EXACT, incl. `+ sum(ct,f21_trade_balanceflow(ct,k_trade))` and `=g=`. ✓ Correctly identified as the **binding global supply≥demand constraint**.
- `q21_notrade(h2,k_notrade)` at `equations.gms:18-19` — EXACT, `=g=`, superregional. ✓
- `q21_trade_reg(h2,k_trade)` at `equations.gms:31-35` — correct (lower production bound). ✓
- `q17_prod_reg(i2,k)` at `equations.gms:10-11` — EXACT (`vm_prod_reg =e= sum(cell, vm_prod)`). ✓
- `vm_supply(i,kall)` declared M16 `declarations.gms:11` — EXACT. ✓
- `vm_emissions_reg(i,emis_source,pollutants)` declared M56 `declarations.gms:40` — EXACT. ✓
- Causal framing correct: M15 enforces per-capita kcal floor; M16 *defines* `vm_supply` as the demand sum (`=e=`); M21 `q21_trade_glo` is the binding production≥demand inequality. The answer's distinction "binding enforcement variable is `vm_supply`, produced by M16, consumed by M21" is accurate.

**Part (b) — soil-N budget:**
- `q50_nr_bal_crp(i2)` at `equations.gms:14-16` — EXACT: `vm_nr_eff(i2)*v50_nr_inputs(i2) =g= sum(kcr,v50_nr_withdrawals(i2,kcr))`. ✓ `=g=` correctly identified as inequality (not `=e=`), with surplus as the slack.
- `q50_nr_inputs(i2)` at `equations.gms:22-32` — all 9 input terms verbatim correct (residues, area-based fixation, fallow fixation, manure recycling, stubble-grazing manure, inorg fert, SOM fertilizer, balanceflow, deposition). ✓
- `q50_nr_withdrawals(i2,kcr)` at `equations.gms:36-43` — EXACT incl. `(1-NDFA)` factor and seed subtraction. ✓
- `q50_nr_surplus(i2)` at `equations.gms:46-49` — EXACT (inputs − withdrawals). ✓
- `q50_nr_bal_pasture` at `equations.gms:55-59`, `q50_nr_surplus_pasture` at `62-66` — both correct. ✓
- `vm_nr_eff.fx(i)` fixed in `presolve.gms:76` — answer's "FIXED in presolve, scenario-driven" verified. ✓
- `vm_nr_inorg_fert_reg(i,land_ag)` declared M50 `declarations.gms:10` — answer's domain `(i,land_ag)` and "endogenous optimization variable" correct. ✓
- M50 does NOT compute emissions; surplus is an accounting variable; conversion happens in M51 — correct.

**Part (b) — M51 emissions (NUE rescaling):**
- `s51_snupe_base = 0.5` at `input.gms:8`; `s51_nue_pasture_base = 0.5` at `input.gms:9` — EXACT. ✓
- `q51_emissions_man_crop` (22-27), `q51_emissions_inorg_fert` (30-39, incl. pasture term with `s51_nue_pasture_base`/`vm_nr_eff_pasture`), `q51_emissions_resid` (42-46), `q51_emissions_som` (55-59), `q51_emissions_indirect_n2o` (83-89) — all equation names, line ranges, and formula skeletons EXACT. ✓
- NUE-rescaling formula `source / (1-s51_snupe_base) * (1-vm_nr_eff) * EF` — matches code at lines 26, 34, 46, 59. ✓
- Worked example (NUE 60% → 0.4/0.5 = 0.8 → 20% reduction) — internally consistent and matches module_51.md:48. ✓
- EF4=1% / EF5=0.75% — consistent with module_51.md:208-209,274-275 and standard IPCC-2006 defaults. (Numeric values live in gitignored `f51_ipcc_ef.csv`; equation structure `f51_ipcc_ef("ef_4"/"ef_5","best")` verified at lines 87-88. Answer flagged 🟡.)

---

### Bugs Found

#### Bug Q3-B1 — `vm_prod_reg` declaration cited one line off (adjacent ≠ same variable)
- **Severity**: Minor
- **Class**: 10 (Stale file:line citation)
- **Trigger** (§1 Minor): "Off-by-few line citation where adjacent lines say similar things." (Pulled DOWN from the Major "citation drift to adjacent but different content" trigger via the §1 tie-breaker — see note.)
- **Claim in answer**: Step 3, line 92: "Module 17 provides the supply side via `vm_prod_reg(i,k)` (`declarations.gms:9`, `equations.gms:10-11`...)".
- **Reality in code**: `vm_prod_reg(i,kall)` is declared at `modules/17_production/flexreg_apr16/declarations.gms:**10**`. Line **9** is a *different* variable: `vm_prod(j,k)` ("Production in each cell"). The `equations.gms:10-11` half of the citation is correct.
- **File evidence**: `modules/17_production/flexreg_apr16/declarations.gms:9-10`:
  ```
  9  vm_prod(j,k)                    Production in each cell (mio. tDM per yr)
  10 vm_prod_reg(i,kall)             Regional aggregated production (mio. tDM per yr)
  ```
- **Tier note**: The cited line 9 points at a *different but closely related* variable (`vm_prod`, the cell-level production that `vm_prod_reg` aggregates). A careful reader scanning line 9 would see `vm_prod`, not `vm_prod_reg` — mild risk of confusion, which is why the Major "adjacent-but-different" trigger is plausible. But the two variables are tightly coupled (same equation `q17_prod_reg`), the equations.gms citation is correct, and the variable *name in prose* is right, so the harm is small. Tie-breaker → Minor. `tier_uncertainty: true`.

#### Bug Q3-B2 — `k_notrade` set members collapsed to "residues" (imprecise labels)
- **Severity**: Minor
- **Class**: 12 (Content-level / set-member label imprecision; adjacent to MANDATE 12 "exact set-member labels")
- **Trigger** (§1 Minor): "Wrong detail, but a careful reader wouldn't be misled into action."
- **Claim in answer**: Step 3, line 77: "For non-tradable commodities (oilpalm, foddr, pasture, **residues**, begr, betr)...".
- **Reality in code**: `k_notrade` = `/ oilpalm, foddr, pasture, **res_cereals, res_fibrous, res_nonfibrous**, begr, betr /` — 8 members; the residue group is three distinct set elements, not one element "residues".
- **File evidence**: `modules/21_trade/selfsuff_reduced/sets.gms:11-12`.
- **Note**: The conceptual claim (residues are non-tradable) is TRUE; the list is presented as an illustrative parenthetical, not a formal set enumeration. The answer inherited this imprecise labeling directly from `module_21.md:127` (which itself writes "8 commodities … (oilpalm, foddr, pasture, residues, begr, betr)" — a wrong label list, see latent doc bug below). So the answerer did NOT beat the doc here; it reproduced the doc's imprecision. Minor because no action-harm and the conceptual claim holds.

---

### Latent Doc Bugs (§1.5 — recorded independent of answer score)

#### Latent Doc Bug Q3-L1 — `module_21.md:127` mislabels `k_notrade` members AND miscounts
- **Root cause**: `doc_error_answerer_beat_it` (partial — see note) / doc internal inconsistency
- **Severity**: Minor (by future-reader harm)
- **Class**: 12 (content-level label) + 6 (count drift)
- **Doc claim**: `module_21.md:127`: "**Applies To**: 8 commodities in `k_notrade` (oilpalm, foddr, pasture, **residues**, begr, betr)" — the parenthetical lists **6** umbrella names while asserting **8** members, and uses "residues" instead of the three actual members `res_cereals/res_fibrous/res_nonfibrous`.
- **Code reality**: 8 members, residue group = 3 distinct elements (`modules/21_trade/selfsuff_reduced/sets.gms:12`).
- **Internal inconsistency**: The SAME doc gets it RIGHT at `module_21.md:66` ("res_cereals, res_fibrous, res_nonfibrous - Residues (not traded)"). So line 66 is correct; line 127 is the wrong copy.
- **Note**: This is the source the answer's Bug Q3-B2 inherited from. Not strictly "answer beat the doc" (the answer reproduced the bug), but it IS a load-bearing doc error on set membership and should be FIXED this session per §1.5 Step 5: change `module_21.md:127` to "8 commodities in `k_notrade` (oilpalm, foddr, pasture, res_cereals, res_fibrous, res_nonfibrous, begr, betr)".
- **Severity rationale**: NOT Critical despite being a set-membership error, because (a) the count "8" is correct, (b) the correct enumeration is present elsewhere in the same doc (line 66), (c) a refactor reader would consult `sets.gms` directly. Distinguished from the R20 wrong-consumer-set anchor (Critical), where the WRONG set would be acted upon with no in-doc corrective.

#### Non-bug observations on `cross_module/nitrogen_food_balance.md` (the §1.5 primary target)

Scrutinized for latent bugs; findings below were assessed and did NOT rise to recordable load-bearing doc bugs, but two are worth a cleanup pass:

1. **Citation `equations.gms:18-30`** (doc lines 38, 74) for the inputs/budget: actual is `q50_nr_bal_crp` 14-16 and `q50_nr_inputs` 22-32 (lines 18-21 are comments). This is approximate citation drift, but (a) the answer did NOT inherit it — the answer cited 14-16 and 22-32 correctly, matching code and matching the well-cited `module_50.md`; (b) it's a line-range approximation, not a wrong equation/variable/set/realization/default. Below the §1.5 load-bearing bar. **Recommend** tightening to `:14-16` (budget) and `:22-32` (inputs) on a cleanup pass; not scored.
2. **Section 1.4 framing** `Inputs = Outputs + ΔSoil_N_stock` (presented as an equality with a soil-N stock-change term): the *actual* code is `=g=` (inequality) with the slack named `v50_nr_surplus_cropland`, and there is no soil-N stock state variable. The doc's own surrounding prose (lines 86 "NO Strict Constraint", 94 "Soil N pool can go negative") makes clear this is a conceptual mass-balance sketch, not a claim about a literal GAMS equation, so it would not mislead a careful reader into citing a non-existent stock variable. Borderline; the answer correctly described the real `=g=`/surplus structure and did not inherit the sketch. Not scored, but a one-line "this is a conceptual sketch; the code uses `=g=` + surplus slack, no soil-N state variable" would harden it.
3. **`module_21.md:478`** labels `exo`-realization `q21_notrade` as `(h,kall)` "over all kall"; the default `selfsuff_reduced` and bilateral use `(h,k_notrade)` (lines 119-120, 489). This pertains to the **non-default `exo`** realization (out of scope for this question), and I did not read `modules/21_trade/exo/equations.gms` to confirm/refute. Not scored against this answer (the answer correctly described the default `(h2,k_notrade)`, verified in code).

---

### Mechanical Checks

| # | Check | Result |
|---|---|---|
| M1 | File:line citations present | ✅ PASS — pervasive, e.g. `equations.gms:10-14`, `12-14`, `22-32`. |
| M2 | Active realization stated | ✅ PASS — names `anthro_iso_jun22`, `sector_may15`, `selfsuff_reduced`, `macceff_aug22`, `rescaled_jan21`; all defaults. |
| M3 | Variable prefixes valid | ✅ PASS — `vm_`, `v50_`, `s51_`, `f50_`, `i51_`, `p15_`, `im_`, `fm_` all consistent. |
| M4 | Epistemic hierarchy badges | 🟡 PARTIAL — closing status uses 🟡 but per-claim badges are sparse in-body. Informational only. |
| M5 | Confidence tier matches depth | ✅ PASS — answer honestly flags 🟡 "based on docs, not independently verified in raw GAMS this session" and an explicit "Items not covered by docs" section. (Auditor confirms the docs were faithful to code for everything load-bearing.) |
| M6 | Closing source statement | ✅ PASS — Sources list + "🟡 Based on module AI documentation." |

No M4 informational bug deducted (badge sparsity is style; closing block present).

---

### Missing Nuances (not scored)

- The `q21_trade_reg` *lower* bound and `q21_trade_reg_up` *upper* bound together form the production band; the answer mentioned only the lower bound (`q21_trade_reg`) and explicitly flagged the upper bound as "not read in full" — honest disclosure, no penalty. (Both verified present: `equations.gms:31-35` and `39-42`.)
- The answer correctly noted `vm_supply` carries material demand via `vm_dem_material` (M62) — directly answering the question's "material supply ≥ demand" sub-part. Good coverage of the "material" half that a food-only answer would miss.
- `q16_waste_demand` and `q16_seed_demand` make `v16_dem_waste`/`vm_dem_seed` endogenous within M16 — answer stated this correctly (lines 51-52), verified at `equations.gms:69-79`.

---

### Summary

Score **8/10**. Verdict **MOSTLY ACCURATE**. Two Minor answer bugs (off-by-one `vm_prod_reg` declaration line citing the adjacent `vm_prod`; "residues" collapsing three `k_notrade` set members) → 10 − 1 − 1 = 8. Both Part (a) supply-chain (M15→M16→M21, with `q21_trade_glo` correctly identified as the binding constraint and material demand included) and Part (b) soil-N budget (`q50_nr_bal_crp` `=g=`, inputs/withdrawals/surplus, NUE-rescaling in M51) are verified correct against code with accurate equation names, operators, and the core file:line ranges. One latent doc bug fixed this session: `module_21.md:127` set-member label/count (`res_cereals/res_fibrous/res_nonfibrous`, not "residues"). Recommend (not required) tightening the `equations.gms:18-30` citation in `cross_module/nitrogen_food_balance.md` to `:14-16`/`:22-32` and adding a "conceptual sketch" caveat to its §1.4 equality framing.

**Latent doc errors**: 1 recorded (Q3-L1, Minor) + 3 non-recordable cleanup observations.
**doc_quality classification**: this question has a `doc_error_answerer_beat_it`-adjacent bug (Q3-L1), so it stays IN the doc_quality_mean.
