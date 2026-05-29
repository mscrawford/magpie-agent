# Audit Report: Round 30 — Nitrogen balance trace (M50→M51 + M59 SOM) & food supply=demand

**Auditor**: Opus (semantic-validation flywheel)
**Date**: 2026-05-29
**Question anchor**: `cross_module/nitrogen_food_balance.md`
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree), `config/default.cfg`

---

## Overall Verdict: MOSTLY ACCURATE
## Accuracy Score: 7/10

The answer is structurally excellent: the M59→M50→M51 trace is correct in direction, the consumer attributions are accurate (verified at the equation level), the NUE-rescaling methodology is correctly described, the food-balance enforcement equation is correctly identified, and the M16/M17/M21 roles are right. Two content errors: one Major (a wrong `k_trade` commodity count copied from a wrong doc) and one Minor (an internal "eight vs nine" inconsistency in the M50 input list), plus one Informational label generalization.

---

## Realization verification (all correct — matched against config/default.cfg)

| Module | Answer claim | default.cfg | Verdict |
|--------|-------------|-------------|---------|
| 59 som | `cellpool_jan23` | `cellpool_jan23` | ✅ |
| 50 nr_soil_budget | `macceff_aug22` | `macceff_aug22` | ✅ |
| 51 nitrogen | `rescaled_jan21` | `rescaled_jan21` | ✅ |
| 21 trade | `selfsuff_reduced` | `selfsuff_reduced` | ✅ |
| 16 demand | (implied `sector_may15`) | `sector_may15` | ✅ (not explicitly stated) |
| 17 production | (implied `flexreg_apr16`) | `flexreg_apr16` | ✅ (not explicitly stated) |

---

## Verified Claims (correct)

### Part 1 — Nitrogen trace

- **`vm_nr_som_fertilizer` → M50; `vm_nr_som` → M51** (the two SOM sub-flows split correctly): `vm_nr_som_fertilizer` is read at `modules/50_nr_soil_budget/macceff_aug22/equations.gms:30`; `vm_nr_som` is read at `modules/51_nitrogen/rescaled_jan21/equations.gms:58`. Both are DIRECT equation-level reads (MANDATE 17 satisfied). Whole-tree grep confirms no other equation-file consumers.
- **`q59_nr_som` (equations.gms:69-75)**: formula structure matches code `sum(ct,i59_lossrate(ct))/m_timestep_length*1/15*(transition_sum - v59_som_target(j2,"crop"))`. The answer's `C_from_transitions_to_cropland` is a clearly-labeled conceptual placeholder for the `vm_lu_transitions` sum — acceptable, not fabricated.
- **C:N ratio 15:1** — comment at equations.gms:76 (`vm_nr_som = ... *1/15`, "carbon to nitrogen ratio of soils assumed to be 15:1"). ✅
- **Lossrate `1 - 0.85^timestep_length`, ~56% per 5-yr**: `i59_lossrate(t)=1-0.85**m_yeardiff(t)` (preloop.gms:45); 1−0.85⁵ = 0.556. ✅
- **`s59_nitrogen_uptake` = 0.2 tN/ha = 200 kg N/ha (input.gms:9)**: confirmed `/ 0.2 /` at input.gms:9. ✅
- **`q59_nr_som_fertilizer` (=l= vm_nr_som) and `q59_nr_som_fertilizer2` (=l= vm_landexpansion*s59_nitrogen_uptake)** as two simultaneous upper bounds (effective value = min): matches equations.gms:81-91. ✅
- **`q50_nr_bal_crp` (equations.gms:14-16) is `=g=`**: `vm_nr_eff(i2)*v50_nr_inputs(i2) =g= sum(kcr,v50_nr_withdrawals(i2,kcr))`. ✅ Exact match. Inorganic fertilizer is the free balancing variable (doc comment equations.gms:20). ✅
- **SOM term at q50_nr_inputs line 30**: `+ sum(cell(i2,j2),vm_nr_som_fertilizer(j2))` at equations.gms:30. ✅
- **`q50_nr_withdrawals` (equations.gms:36-43)** with NDFA fixation fraction and minus-seed: matches. NDFA = "Nitrogen Derived From Atmosphere" — confirmed `f50_nr_fix_ndfa`, module_50.md:311. ✅
- **`q50_nr_surplus` (equations.gms:46-49)**: `v50_nr_surplus_cropland(i) = v50_nr_inputs(i) - sum(kcr, v50_nr_withdrawals(i,kcr))`. ✅ Exact match.
- **`vm_nr_eff.fx` / `vm_nr_eff_pasture.fx` FIXED in presolve.gms:76-77**: `vm_nr_eff.fx(i) = 1 - (1-i50_nr_eff_bau(t,i)) * (1 - i50_maccs_mitigation_transf(t,i))` (line 76). ✅ Exact match. Efficiency is a scenario input, not endogenous. ✅ `vm_nr_eff`/`vm_nr_eff_pasture` declared in M50. ✅
- **MACC mitigation from M57**: `im_maccs_mitigation` declared `modules/57_maccs/on_aug22/declarations.gms:13`. ✅
- **`s51_snupe_base` = 0.5 (input.gms:8)**: confirmed `/ 0.5 /`. ✅ NUE-rescaling formula `source/(1-0.5)*(1-vm_nr_eff)*EF` matches q51 equations.
- **`q51_emissions_som` (equations.gms:55-59)** uses `vm_nr_som` (total, not `vm_nr_som_fertilizer`): confirmed `sum(cell(i2,j2),vm_nr_som(j2)) * sum(ct, i51_ef_n_soil(...,"som")) / (1-s51_snupe_base) * (1-vm_nr_eff(i2))`. ✅
- **All 8 emission equations + NUE-rescaling status table** — verified equation by equation against equations.gms:22-89:
  - `q51_emissions_man_crop` (22-27) crop-rescaled, `vm_manure_recycling`. ✅
  - `q51_emissions_inorg_fert` (30-39) crop+pasture rescaled, `vm_nr_inorg_fert_reg`. ✅ (both NUEs at lines 34, 37)
  - `q51_emissions_resid` (42-46) crop-rescaled, `vm_res_recycling`. ✅
  - `q51_emissions_resid_burn` (49-52) NOT rescaled, `vm_res_ag_burn`. ✅
  - `q51_emissions_som` (55-59) crop-rescaled, `vm_nr_som`+`vm_nr_eff`. ✅
  - `q51_emissionbal_awms` (65-71) MACC not NUE, `im_maccs_mitigation`. ✅
  - `q51_emissionbal_man_past` (74-80) pasture-rescaled, `vm_manure`+`vm_nr_eff_pasture`. ✅
  - `q51_emissions_indirect_n2o` (83-89) own direct outputs (EF4 on NH3+NO2, EF5 on NO3). ✅
- **Variable provenance** (MANDATE 13): `vm_res_recycling`→M18, `vm_manure_recycling`→M55, `vm_manure`→M55, `vm_res_ag_burn`→M18, `vm_nr_inorg_fert_reg`→M50, `im_maccs_mitigation`→M57. All confirmed via declarations.gms greps. ✅
- **`vm_emissions_reg` declared in M56** (`price_aug22/declarations.gms`). ✅
- **`n_pollutants_direct` = {n2o_n_direct, nh3_n, no2_n, no3_n}** + `n2o_n_indirect`: defined in `modules/56_ghg_policy/price_aug22/sets.gms:199-202` (and 174-176 / 204-205). ✅ Exact set-member match including `no2_n`.
- **"No equation closes the N budget to zero; M50 has no cross-timestep memory"**: consistent with code (surplus is a pure accounting residual; no soil-N stock state variable). ✅

### Part 2 — Food supply = demand

- **`q21_trade_glo` (equations.gms:12-14)** is the global enforcing constraint: `sum(i2,vm_prod_reg(i2,k_trade)) =g= sum(i2,vm_supply(i2,k_trade)) + sum(ct,f21_trade_balanceflow(ct,k_trade))`. ✅ Exact match. `=g=` not `=e=`. ✅
- **`q21_notrade` (equations.gms:18-19)** for non-tradables at superregional level. ✅ Exact match.
- **`q21_trade_reg`** lower bound with `v21_import_for_feasibility` slack: confirmed equations.gms:31-35. ✅
- **k_notrade = 8** (oilpalm, foddr, pasture, res_cereals, res_fibrous, res_nonfibrous, begr, betr): `selfsuff_reduced/sets.gms:11-12`. ✅ Count correct.
- **M16 `vm_supply`** = food+feed+processing+material+(bioenergy)+seed+waste+balanceflow: `q16_supply_crops` (sector_may15/equations.gms:19-29). ✅ Waste via `v16_dem_waste`/`q16_waste_demand` (69-72) with `f16_waste_shr`. ✅ All three names confirmed.
- **M17 `vm_prod_reg(i,k) = sum(cell(i,j), vm_prod(j,k))`**: `q17_prod_reg` (flexreg_apr16/equations.gms:10-11). ✅ Exact match.
- **`vm_supply` is total demand, not a physical stock**: correct framing. ✅

---

## Bugs Found

### Bug QN30-B1 — Wrong `k_trade` commodity count
- **Severity**: Major
- **Class**: 6 (Hardcoded counts drift) / §1 Major trigger "Fabricated count for a set/parameter/realization list"
- **Trigger**: Fabricated/wrong count for a set.
- **Claim in answer**: "There are 38 tradeable commodities (`k_trade`) and 8 non-tradeables (`k_notrade`)."
- **Reality in code**: `k_trade` has **33 members** (`modules/21_trade/selfsuff_reduced/sets.gms:17-21`): 15 crops + 10 processed + 6 livestock/fish + 2 forestry = 33. Independently counted in Python (=33). `k_notrade` = 8 is correct.
- **File evidence**: `modules/21_trade/selfsuff_reduced/sets.gms:17-21` (tece…woodfuel = 33).
- **Root cause**: `doc_error` — the answer faithfully copied `module_21.md:70` ("**Tradable Commodities** (`k_trade`, **38 items**)"), which is wrong. The doc's own enumeration (module_21.md:71-74) sums to 33, so the doc is internally inconsistent (header 38, body 33). The answerer trusted the header.
- **Note**: also recorded as a latent doc bug below (the doc is the upstream cause and must be fixed regardless of this answer's score).

### Bug QN30-B2 — "Eight sources" stated, nine terms listed (M50 inputs)
- **Severity**: Minor
- **Class**: 6 (count) / 4 (descriptive)
- **Trigger**: Wrong detail a careful reader notices but isn't misled into action.
- **Claim in answer**: "The full input aggregate is `q50_nr_inputs` … which includes **eight sources**: residues, biological N fixation (area-based for legumes), fallow fixation, recycled manure, stubble-grazing manure, inorganic fertilizer, SOM fertilizer from M59, a calibration balance flow, and atmospheric deposition."
- **Reality in code**: `q50_nr_inputs` has **nine** distinct additive terms (`equations.gms:24-32`): residue recycling, area-based fixation, fallow fixation, manure recycling, stubble-grazing manure, inorganic fertilizer, SOM fertilizer, nitrogen balanceflow, deposition. The answer's own list enumerates nine items, contradicting its "eight" count.
- **File evidence**: `modules/50_nr_soil_budget/macceff_aug22/equations.gms:24-32` (9 additive terms).
- **Root cause**: `ambiguous`. The "8" framing comes from `module_50.md:437,751` ("8 nitrogen input sources"), which groups the two fixation terms (crop area + fallow) into one "fixation" category. That grouping is defensible as a *category* count; the literal *term* count is 9. The flaw is the answer's internal inconsistency: it adopts the doc's "eight" but then expands fixation into two, listing nine. A careful reader would notice but not be misled mechanistically.

### Bug QN30-B3 — Generalized pollutant label "NOx" in indirect-N2O table cell
- **Severity**: Informational
- **Class**: 12 (label generalization, MANDATE 12)
- **Trigger**: Style/label issue, no action impact.
- **Claim in answer**: indirect-N2O row provenance column reads "Own direct outputs (NH3, **NOx**, NO3)".
- **Reality in code**: the set member is `no2_n`, not "NOx". The answer's own prose pollutant list correctly uses `no2_n` — so this is an internal inconsistency between the prose and the table cell.
- **File evidence**: `modules/56_ghg_policy/price_aug22/sets.gms:201` (`no2_n`).
- **Root cause**: `answerer_style_or_framing`. Real-world "NOx" gloss substituted for the exact set member in one table cell.

---

## Latent Doc Bugs (rubric §1.5 — recorded independent of answer score; fix regardless)

### Latent-1 — `module_21.md:70` claims `k_trade` has 38 items (actual 33)
- **Severity (future-reader harm)**: Major (wrong count; a reader building a commodity loop or sizing an array would be off by 5). Not Critical (would not cause a wrong code edit / missed module in a refactor — it is a descriptive count, and the correct member list is enumerated right below).
- **Doc location**: `cross_module/../modules/module_21.md:70` — "**Tradable Commodities** (`k_trade`, 38 items):"
- **Code reality**: 33 members at `modules/21_trade/selfsuff_reduced/sets.gms:17-21`. The doc's OWN enumeration at module_21.md:71-74 sums to 33 (15+10+6+2) — so the header "38" contradicts the doc's body. Internal inconsistency.
- **Root cause**: `doc_error_answerer_beat_it` — except here the answerer did NOT beat it (it reproduced the error, see B1). Recorded so Step 5 fixes `module_21.md:70` → "33 items" unconditionally.
- **Suggested fix**: change "38 items" to "33 items" at module_21.md:70. (k_hardtrade21 "16 items" at module_21.md:76 is CORRECT — verified — leave it.)

### Latent-2 (soft / borderline) — `module_50.md:437,751` "8 nitrogen input sources" vs 9 algebraic terms
- **Severity (future-reader harm)**: Informational/borderline-Minor. The doc is internally consistent (it lists exactly 8 *categories*, merging crop-area and fallow fixation under "fixation"). The literal additive-term count in `q50_nr_inputs` is 9. This is a categorization choice, not a hard count of a SET, so it is not a clear doc error. Flagged only because it propagated the "eight vs nine" inconsistency into the answer (B2).
- **Doc location**: `modules/module_50.md:437` ("Accounts for 8 nitrogen input sources for croplands - equations.gms:22-32") and `:751`.
- **Code reality**: 9 additive terms at `macceff_aug22/equations.gms:24-32`.
- **Root cause**: `ambiguous`. Recommend NOT changing the count, but adding a half-sentence clarifying that "fixation" covers two terms (area-based + fallow), so the algebraic term count is 9. Low priority.

---

## Missing Nuances (not bugs)

- The M51 SOM-emission formula in the answer drops the `sum(ct, ...)` wrapper on `i51_ef_n_soil` (writes `i51_ef_n_soil(ct,...)`); the code wraps it in `sum(ct, ...)`. This is a single-element time sum — cosmetic, borderline MANDATE 10 but negligible (ct is effectively the current timestep).
- The answer's k_notrade gloss "(pasture, fodder, residues, bioenergy)" omits `oilpalm` (a member that is none of those). The count (8) is right and this is an illustrative parenthetical, so no bug; worth noting the full member list is oilpalm/foddr/pasture/res_cereals/res_fibrous/res_nonfibrous/begr/betr.
- M16/M17 realizations are not explicitly stated (only implied). M2 partially soft on these two modules; both happen to be the defaults, so no error.

---

## Mechanical checks

| Check | Result |
|---|---|
| M1 file:line citations | PASS (extensive, full-path style) |
| M2 active realization stated | PASS for M59/M50/M51/M21; soft for M16/M17 (implied only) |
| M3 variable prefixes valid | PASS |
| M4 epistemic badges present | PASS (closing block) |
| M5 confidence tier matches depth | PASS (🟡 documented; honest "no raw GAMS read") |
| M6 closing source statement | PASS |

---

## Summary

A strong, accurate trace. The entire nitrogen flow (M59 SOM split → M50 budget assembly → M51 NUE-rescaled emissions) is correct down to the equation, line number, formula structure, NUE-fixing-in-presolve detail, and cross-module variable provenance. Part 2 correctly identifies `q21_trade_glo` as the global supply≥demand enforcer, `q21_notrade` for non-tradables, and the M16/M17/M21 division of labor. The only Major error is the `k_trade = 38` count, which is a faithful copy of a wrong (and internally inconsistent) `module_21.md:70` — a clean latent-doc-bug case to fix this session. The "eight vs nine" M50 input inconsistency is Minor. The "NOx" label is Informational.

**Score**: 10 − 2(Major) − 1(Minor) − 0(Info) = **7/10**.

**Doc fixes required this session**: (1) `module_21.md:70` "38 items" → "33 items" (Major latent). (2) Optional: `module_50.md` clarify fixation = 2 terms (low priority).
