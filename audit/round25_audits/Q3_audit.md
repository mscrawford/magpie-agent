## Audit Report: Q3 (Nitrogen-MACC Cost Flow into Objective Function)

### Overall Verdict: ACCURATE
### Accuracy Score: 9/10

### Verified Claims (correct)

1. **M57 active realization** — `on_aug22` is the only realization; `config/default.cfg` confirms `cfg$gms$maccs <- "on_aug22"`. (Verified `modules/57_maccs/module.gms:27` — only `on_aug22` include guarded.)

2. **`vm_maccs_costs(i,factors)` declared in M57** — exactly at `modules/57_maccs/on_aug22/declarations.gms:25` with description "Costs of technical mitigation of GHG emissions (mio. USD17MER per yr)". Citation precise.

3. **`q57_labor_costs(i)` and `q57_capital_costs(i)` exist** — declared at `declarations.gms:20-21`. Body of `q57_labor_costs` spans `equations.gms:35-43`; body of `q57_capital_costs` spans `equations.gms:45-52`. The answer's cited ranges match.

4. **Cost formula structure** — both equations multiply `p57_maccs_costs_integral × vm_emissions_reg / (1 - im_maccs_mitigation)` (back-calculating to pre-mitigation baseline), plus a fertilizer-cost correction term `vm_emissions_reg(i2, emis_source_inorg_fert_n2o, "n2o_n_direct") / s57_implicit_emis_factor × ... × s57_implicit_fert_cost`, multiplied by factor-share scaling. The answer's prose description of "integral of the MACC curve multiplied by back-calculated baseline emissions, plus a fertilizer-cost correction" matches the code.

5. **`factors` set = `/labor, capital/`** — verified `modules/38_factor_costs/per_ton_fao_may22/sets.gms:8-10`. Answer's "region × {labor, capital}" dimensions correct.

6. **No M51 intermediary cost variable** — VERIFIED CORRECT. M51 active realization is `rescaled_jan21` (`cfg$gms$nitrogen <- "rescaled_jan21"`). `modules/51_nitrogen/rescaled_jan21/declarations.gms` contains ONLY: 8 equations (`q51_emissions_*`, `q51_emissionbal_*`, `q51_emissions_indirect_n2o`), 1 parameter (`i51_ef_n_soil`), and R-section OQ output parameters. NO cost variables declared. M51 reads/writes `vm_emissions_reg` (declared in M56) and consumes `im_maccs_mitigation` from M57 — the relationship to M57 is exactly as the answer describes (M57 reads M51's emissions to compute MACC costs; M57 provides MACC mitigation fractions back to M51 to reduce baseline emissions). The cost flow goes M57 → M11 directly without M51 intermediation.

7. **`q11_cost_reg` term `+ sum(factors, vm_maccs_costs(i2, factors))`** — VERIFIED CORRECT at exactly `modules/11_costs/default/equations.gms:28`. Line 28 reads `+ sum(factors,vm_maccs_costs(i2,factors))`.

8. **`q11_cost_glo .. vm_cost_glo =e= sum(i2, v11_cost_reg(i2))`** — VERIFIED CORRECT at `modules/11_costs/default/equations.gms:10`.

9. **`v11_cost_reg(i)` declared at `declarations.gms:10`** — VERIFIED CORRECT.

10. **`q51_emissionbal_awms` at `equations.gms:65-71`** — VERIFIED CORRECT.

11. **M11 default realization** — only `default` exists; `cfg$gms$costs <- "default"`. Correct.

12. **32 regional cost terms in `q11_cost_reg`** — counted 31 lines starting with `+` or `-` plus the first term on line 15 = 32 total. Correct.

13. **Module attribution chain** — `vm_maccs_costs` correctly attributed to M57 (producer); flows directly into M11's `q11_cost_reg` (consumer). No M51 attribution in the cost path. MANDATE 9 (cost-variable attribution) and MANDATE 17 (one-hop reads — distinguished direct consumer M11 from transitive M51 emission-quantity provider role) both satisfied.

14. **`im_maccs_mitigation` flows from M57 to M51's `q51_emissionbal_awms`** — verified at `equations.gms:71` `* (1-sum(ct, im_maccs_mitigation(ct,i2,"awms","n2o_n_direct")))`. Answer's `equations.gms:65-71` range is correct.

15. **`vm_emissions_reg` not declared in M51** — confirmed; `grep -l "vm_emissions_reg" modules/*/*/declarations.gms` returns only `modules/56_ghg_policy/price_aug22/declarations.gms`. Answer correctly identifies M51 as a populator (not declarer) of this variable, and correctly distinguishes that this is an emission quantity, not a cost variable.

### Bugs Found

#### Bug Q3-B1: Misleading documentation citation propagated from module_11.md

- **Severity**: Minor
- **Class**: Class 10 (Stale file:line citation) — but propagated from a doc bug, not a fresh fabrication.
- **Trigger**: §1 Minor — "Off-by-few line citation where adjacent lines say similar things"
- **Claim in answer**: "Citation: `equations.gms:28`, documented in `equations.gms:58`"
- **Reality in code**: At `modules/11_costs/default/equations.gms:58` the line is `*' Emission costs ([56_ghg_policy]),` — which describes M56 emission costs, NOT M57 abatement costs. The actual documentation comment for `vm_maccs_costs` / abatement costs is at line 60: `*' Abatement costs ([57_maccs]),`. Off-by-two citation.
- **File evidence**: `modules/11_costs/default/equations.gms:58-60`:
  ```
  58: *' Emission costs ([56_ghg_policy]),
  59: *' Rewarded CDR from afforestation (Benefits as negative costs) ([56_ghg_policy]),
  60: *' Abatement costs ([57_maccs]),
  ```
- **Doc vs answerer attribution**: This is a **doc_error**. `modules/module_11.md:452` states verbatim "Citation: `equations.gms:28`, documented in `equations.gms:58`" — the answerer quoted this faithfully. The doc itself is stale (likely lines shifted by 2 since the cost-component documentation block was authored). The answerer did not independently verify line 58 against current code.
- **Anchor reference**: Resembles R20 2026-04-20 citation-drift anchor (post-merge line shifts), but smaller magnitude (2 lines vs 5-20).
- **Action**: Update `modules/module_11.md:452` (and the parallel entry at line 442 for `vm_reward_cdr_aff`, which says `:57` but actual rewards-CDR comment is at line 59) to reflect the current line numbers.

### Missing Nuances

1. **Indirect M51 role via M56 pricing**: The answer correctly notes that M51's `vm_emissions_reg` feeds into M56's pricing (which then enters M11 via `vm_emission_costs`). This is a separate (non-MACC) nitrogen-cost path. The question scoped to MACC specifically, so this is not a defect — but a more complete trace would mention that nitrogen emissions enter the cost objective via TWO pathways: (a) MACC abatement costs (M57 → M11) and (b) emission pricing (M51 → M56 → M11). The answer mentioned this in passing in the Key Clarification footer ("`vm_emissions_reg` is itself a cost variable" — clarifying it isn't), but didn't trace the M51 → M56 → M11 emission-cost path. Acceptable per scope.

2. **`vm_nr_inorg_fert_costs` (M50)**: Another nitrogen-related cost in `q11_cost_reg:24` is `vm_nr_inorg_fert_costs(i2)` produced by M50 (`nr_soil_budget/macceff_aug22`), not by M51 or M57. The question's "nitrogen-MACC costs" framing makes M57 the unambiguous focus, but a sophisticated reader might wonder why M50's nitrogen-related cost variable isn't in the MACC chain. M50 sells the inorganic fertilizer as an input cost (not as a MACC cost) — orthogonal to the M57 MACC abatement flow.

3. **`vm_maccs_costs` also consumed by M36 (employment)**: `modules/36_employment/exo_may22/equations.gms:28` reads `vm_maccs_costs(i2,"labor")` for employment accounting. This is a secondary consumer (not in the cost chain to the objective function), so omitting it is acceptable for the scope of this question.

### Summary

The answer is highly accurate. All three parts of the question (a/b/c) are correctly answered with verifiable code citations:
- (a) `vm_maccs_costs(i,factors)` produced by M57 `on_aug22` — correct
- (b) No M51 intermediary in the cost chain — correctly identified, with sophisticated treatment of the seemingly-contradictory dependency note in module_51.md
- (c) `+ sum(factors, vm_maccs_costs(i2, factors))` at `q11_cost_reg :28` — exact citation correct

Module attribution per cost variable is correct (M57 → M11 chain, no M51 misattribution). MANDATE 9 (cost-variable attribution) and MANDATE 17 (one-hop reads — M51 is NOT a direct consumer of `vm_maccs_costs`, only a transitive participant via emission quantities) both satisfied.

One **Minor** citation-drift bug (Q3-B1) caused by faithful quotation of a stale doc citation in `module_11.md:452`. This is a **doc_error**, not answerer confabulation — the answerer should have verified the cited line content against current code (Step 2b), but the underlying claim about which line of equations.gms contains the term itself (line 28) is correct.

**Phase 2c gate (M11 §17.2 cost-aggregator)**: **PASSED**. The answer correctly attributed every cost variable in the chain to its producing module (M57 → M11), respected MANDATE 9 attribution, and the one Minor bug was a doc-citation drift, not an attribution error. M11 §17.2's 32-term cost aggregator was named correctly with the right term-count (32) and the right producer-module attribution for `vm_maccs_costs`.

**MANDATE 17 (one-hop reads) gate**: **PASSED**. The answer explicitly disambiguated M51's transitive role (provides emission quantities to M57) from a direct cost-conduit role (which it does not have). This is the exact pattern MANDATE 17 was added to catch.

**Score calculation**: 1 Minor × 1 = 1; 10 − 1 = **9/10**.

**Verdict**: ACCURATE.
