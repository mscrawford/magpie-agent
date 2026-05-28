## Audit Report: Q4 (M38 factor_costs — `per_ton_fao_may22` interface variables and consumers)

### Overall Verdict: SIGNIFICANT ERRORS
### Accuracy Score: 8/10

### Pre-condition verification

- **Default realization for M38**: `cfg$gms$factor_costs <- "sticky_feb18"` confirmed at `config/default.cfg:1233`. Question specifies `per_ton_fao_may22` (non-default) — Sonnet correctly flags this in its "Realization Context" preamble. ✓
- **Completeness gate — list of `vm_cost_*` variables declared in `per_ton_fao_may22/declarations.gms`**:
  - The ONLY `vm_*` declaration in `modules/38_factor_costs/per_ton_fao_may22/declarations.gms:14` is `vm_cost_prod_crop(i,factors)`.
  - No `vm_cost_prod_kres`, no `vm_cost_prod_past`, no `vm_cost_prod_livst`, no `vm_cost_prod_fish` declared here.
  - Sonnet's "exactly one `vm_cost_*` interface variable" claim is **CORRECT**. Completeness gate passes.

### Verified Claims (correct):

- **Single interface variable**: `vm_cost_prod_crop(i,factors)` is the sole `vm_cost_*` declared in `per_ton_fao_may22`. Verified at `modules/38_factor_costs/per_ton_fao_may22/declarations.gms:14`. 🟢
- **Realization context**: Sonnet correctly flags that `per_ton_fao_may22` is NOT the default (`sticky_feb18` is). Verified at `config/default.cfg:1233`. 🟢
- **Cost-aggregator citation (M11)**: `q11_cost_reg(i2) .. v11_cost_reg(i2) =e= sum(factors,vm_cost_prod_crop(i2,factors)) ...` at `modules/11_costs/default/equations.gms:15`. Citation accurate. 🟢
- **Global cost rollup citation (M11)**: `q11_cost_glo .. vm_cost_glo =e= sum(i2, v11_cost_reg(i2));` at `modules/11_costs/default/equations.gms:10`. Citation accurate. 🟢
- **`factors` set membership**: `{labor, capital}`. Confirmed by `q38_cost_prod_crop_labor` / `q38_cost_prod_crop_capital` in `per_ton_fao_may22/equations.gms:10-17`. 🟢
- **Cross-realization claim**: All three M38 realizations (`sticky_feb18`, `sticky_labor`, `per_ton_fao_may22`) declare `vm_cost_prod_crop(i,factors)` as the cost interface. Verified by `grep "vm_cost_prod_crop" modules/38_factor_costs/*/declarations.gms` (all three contain it).
- **Equation form for `per_ton_fao_may22`**: Sonnet's "Conceptually" pseudocode form (vm_prod_reg × fac_req × share × wage_scaling) matches the actual equation structure at `per_ton_fao_may22/equations.gms:10-17`. Pseudocode is properly labeled (MANDATE 5 compliant). 🟡 (labeled "Conceptually:" not presented as exact)

### Bugs Found:

#### Bug Q4-B1: Missed Module 36 (employment) as a consumer of `vm_cost_prod_crop`

- **Severity**: **Major**
- **Class**: #12 Content-level citation mismatch (consumer-attribution drift); also #4 conceptual pseudo-code in the sense that the dependency graph diagram in module_38.md is incomplete
- **Trigger**: "Citation points at content that's no longer at the cited line, AND the actual cited content says something materially different" — in this case the assertion "There is no other consuming module" is contradicted by actual code.
- **Claim in answer**: "**There is no other consuming module.** Module 38's `vm_cost_prod_crop` is not consumed anywhere except Module 11's `q11_cost_reg`. The docs describe Module 11 as the single convergence point for all cost variables, with Module 38 among the 27 upstream providers."
- **Reality in code**: `vm_cost_prod_crop(i,"labor")` is ALSO read by Module 36 (`exo_may22` — the default and only realization) in the agricultural-employment equation:
  ```gams
  q36_employment(i2) .. v36_employment(i2)
           =e= (vm_cost_prod_crop(i2,"labor") + vm_cost_prod_livst(i2,"labor") + sum(ct,p36_nonmagpie_labor_costs(ct,i2))) *
               (1 / sum(ct,f36_weekly_hours(ct,i2)*s36_weeks_in_year*pm_hourly_costs(ct,i2,"scenario")));
  ```
- **File evidence**: `modules/36_employment/exo_may22/equations.gms:23-25` (default realization per `config/default.cfg:1189`: `cfg$gms$employment <- "exo_may22"`). Verified by `grep -rn "vm_cost_prod_crop" modules/ --include="*.gms"` which returns exactly two consumer hits outside M38 itself — M11 and M36.
- **doc_error vs answerer_confabulation**: This is a **doc_error**. `module_38.md` itself omits M36 as a consumer at line 33 ("Aggregated by Module 11..."), line 121 ("consumed by Module 11 via `q11_cost_reg`"), line 336 ("Consumer: Module 11..."), line 357 ("Module 11 (Costs)..."), and line 617 ("consumed by Module 11's `q11_cost_reg`"). Five locations in module_38.md attribute the variable's consumption exclusively to M11; none mention M36. Sonnet trusted the doc and propagated the omission. Notably, `module_36.md:223` and `module_36.md:528` correctly document the M36→M38 dependency from the consumer side, so the consumer-side docs are correct — the producer-side doc has the gap.
- **Pattern D class miss**: **YES** — this is exactly the bug class the Phase 1 1b `check_consumer_attribution` validator was supposed to catch (cross-checking producer-doc consumer lists against actual `grep` results). Pre-launch baseline reported "0 Pattern D mismatches"; this audit shows the validator missed a real one. Likely cause: the validator may scan `vm_cost_*` declarations for a "Consumer:" or "consumed by" enumeration and check whether those listed modules grep-positive — but it may not flag the inverse case (consumer modules grep-positive but absent from the producer-doc consumer list). Recommend: re-examine the validator's negative-evidence check.
- **Anchor reference**: Resembles R20 (2026-04-20) anchor "module doc cited `pm_carbon_density_ac` as having three consumers when commit added two more (M32 afforestation + NDC presolve)" — same Pattern D shape (producer-side doc consumer list incomplete; consumer-side docs correct). That R20 anchor was tiered Critical because the missing consumers were load-bearing for refactor work. Here, the missed consumer (M36 employment) is an exogenous output module (employment calculation only — does not feed back into cost equations or model behavior), so the action-cost is lower. The answer would not cause "would do the wrong thing on a high-stakes decision" (the user editing M38 would not break M11's cost aggregation), but it would mislead anyone tracing employment-cost dependencies, refactoring labor-cost variables, or verifying that all consumers of a renamed `vm_cost_prod_crop` get updated. **Tier-down to Major** per the tie-breaker rule (§1 "When between two tiers, pick the lower"), with `tier_uncertainty: true`.

#### Bug Q4-B2: Inferred declarations.gms line without verification

- **Severity**: **Informational**
- **Class**: #10 Stale file:line citation (precursor variant — no line cited at all)
- **Trigger**: Style/doc issue, not a content error. Sonnet was honest about this in its Confidence Notes ("LOW confidence: The docs do not provide an explicit `declarations.gms:NN` line citation for this non-default realization"), but a session-time tool call (`Read modules/38_factor_costs/per_ton_fao_may22/declarations.gms`) would have produced the verified citation `declarations.gms:14`. The agent had the tools to verify and elected not to. The cost was low (no false claim was made), but a 🟢 verification was available and skipped.
- **Claim in answer**: "**Declaration file**: `modules/38_factor_costs/per_ton_fao_may22/declarations.gms` (the docs note this is the same interface variable exposed by all three Module 38 realizations)" — no line number.
- **Reality in code**: Line 14 of that file. Verifiable in <2 seconds with a Read tool call.
- **File evidence**: `modules/38_factor_costs/per_ton_fao_may22/declarations.gms:14: vm_cost_prod_crop(i,factors)      Regional factor costs of capital and labor for crop production (mio. USD17MER per yr)`
- **doc_error vs answerer_confabulation**: Neither — process gap. The agent should have used Read for a self-cited "🔴 cannot rule out without reading directly" claim.

### Missing Nuances:

- **The `per_ton_fao_may22` realization is not just "simpler" — it's the *original* MAgPIE factor-cost realization, with `sticky_feb18` (default) introducing capital stocks, immobile/mobile investment dynamics, and depreciation/annuitization**. Sonnet correctly notes "purely volume-based per-ton costs" but doesn't explicitly mention that `sticky_feb18` adds `v38_investment_immobile`, `v38_capital_stock`, and depreciation — making the realization choice mechanistically significant (a switch from `sticky_feb18` to `per_ton_fao_may22` removes endogenous capital dynamics entirely). Not a bug — outside the question scope — but worth flagging.

- **`pm_factor_cost_shares(t,i,factors)` is an interface parameter declared in `per_ton_fao_may22/declarations.gms:20`** — Sonnet did not enumerate it, but the question asked specifically about `vm_cost_*`, so this is not an omission. The question scope was correctly bounded.

- **The wage-scaling term in `q38_cost_prod_crop_labor` couples M38 to M36 via `pm_hourly_costs` and `pm_productivity_gain_from_wages`** (declared by M36 employment realization), which is the reverse direction of the missed-consumer bug. M36 produces wage drivers that M38 reads, AND M38 produces labor-cost variables that M36 reads — there's a bidirectional dependency that the docs partially describe (M38→M36 direction missed; M36→M38 documented in module_36.md:506).

### Mechanical Checks (§2):

- M1 (file:line citations present): **PASS** — multiple file:line citations.
- M2 (active realization stated): **PASS** — Sonnet correctly identifies `sticky_feb18` as default and `per_ton_fao_may22` as the question-specified non-default.
- M3 (variable prefixes valid): **PASS** — `vm_`, `v11_`, `v36_`, `pm_` all used correctly.
- M4 (epistemic hierarchy badges present): **PASS** — 🟡 / 🟢 / 🔴 badges throughout.
- M5 (confidence tier matches verification depth): **PARTIAL** — Sonnet correctly used 🔴 for the unverified declarations-line claim, but missed an opportunity to verify and upgrade to 🟢.
- M6 (closing source statement): **PASS** — "Based on module_38.md documentation (§4, §5, §6) and module_11.md documentation (§2.2)."

### Severity-weighted score

```
critical = 0
major    = 1  (Q4-B1)
minor    = 0
info     = 1  (Q4-B2)

raw_severity_weighted = 4·0 + 2·1 + 1·0 + 0·1 = 2
score_0_10 = max(0, 10 - 2) = 8
```

### Summary

Sonnet's answer is technically careful and well-flagged with epistemic markers, and it nails the completeness gate (`vm_cost_prod_crop` IS the only `vm_cost_*` declared in `per_ton_fao_may22`). However, it inherits a real doc_error from `module_38.md` — the omission of Module 36 (employment) as a second consumer of `vm_cost_prod_crop`. The producer-side doc claims M11 is the sole consumer in five locations; actual code shows M36's `q36_employment` reads `vm_cost_prod_crop(i,"labor")` to compute agricultural employment. **The Phase 1 1b consumer-attribution validator should have caught this and didn't — the gate failed.** The consumer-side doc (`module_36.md`) correctly documents the M36→M38 dependency, so this is an asymmetric drift: producer-doc consumer list is incomplete while consumer-doc producer reference is correct. Action recommendation: (a) patch `module_38.md` to add M36 to the consumer enumeration at lines 33, 121, 336, 357, 617; (b) audit `check_consumer_attribution`'s logic for the negative-evidence case (consumer modules that grep-positive but are absent from producer-doc consumer lists).

**Score: 8/10** — Mostly Accurate. The doc_error is a real bug worth fixing, but the action-cost for a model user is low (M36 is an exogenous output module — employment calculation doesn't feed back into M11 or any cost equation).

**doc_error vs answerer_confabulation split**:
- 1 doc_error (Q4-B1) — `module_38.md` omits M36 from consumer list
- 0 answerer_confabulation — Sonnet faithfully reported what the doc said
- 1 process gap (Q4-B2) — Sonnet had tools to verify but elected to inherit doc uncertainty

**Pattern D class miss**: YES (1 instance). Phase 1 1b validator pre-launch baseline of "0 Pattern D mismatches" appears to be a false negative for the omission direction (producer-doc missing a real consumer). The validator's positive-evidence check may pass even when the consumer enumeration is incomplete.
