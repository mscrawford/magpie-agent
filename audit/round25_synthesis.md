# R25 Synthesis — Phase 3 Re-measure Results

**Date**: 2026-05-25
**Plan**: `audit/get_under_control_plan.md` Phase 3
**Design**: `audit/round25_design.md`
**Pre-launch validator baseline**: `validate_consistency.sh` 39/41 + 2 acceptable warnings; `check_units` 5 advisory; `check_consumer_attribution` 0 mismatches + Pattern D clean.

## Per-question results

| ID | Score | Bugs (Crit/Major/Minor/Info) | Modules | Verdict |
|----|-------|------------------------------|---------|---------|
| Q1 — M30 rotation | 8.5 | 0/1/0/2 | 30, 29, 10 | MOSTLY ACCURATE; 1 doc_error in module_30.md (line citation drift) |
| Q2 — M80 solver | 8.0 | 0/0/3/1 | 80 | MOSTLY ACCURATE; 2 doc_errors in newly-added Parameters table + 1 answerer compression |
| Q3 — M57 N MACC | 9.0 | 0/0/1/0 | 57, 51, 11 | ACCURATE; 1 doc_error in module_11.md (line citation drift) |
| Q4 — M38 factor costs | 8.0 | 0/1/0/1 | 38, 11, 36 | MOSTLY ACCURATE; 1 doc_error (missing M36 consumer) |
| Q5 — magpie4 N2O AWMS | 9.0 | 0/0/1/0 | magpie4, 51, 55, 56 | ACCURATE; 1 off-by-one citation |
| G1 — M14 yields | 10.0 | 0/0/0/0 | 14 | ACCURATE; drift=false (stable across R22/R23/R25) |
| G2 — vm_carbon_stock | 10.0 | 0/0/0/0 | 52, 56 | ACCURATE; drift=false (R22 fix holds; AGENT.md trim non-degrading) |

**Mean score: 8.93/10** (vs R24: 7.5)

## Phase 3 gates

### A. Bomb rate

| Gate | Target | Result |
|------|--------|--------|
| Mean score | ≥8.0 (recover) / ≥8.5 (improvement) | ✅ 8.93 |
| CRITICAL bugs | 0 | ✅ 0 |
| HIGH bugs | ≤~6 | ✅ 2 Major |

Per plan's failure-mode table, R25 mean 8.93 ≥ 8.5 → **Recovery + improvement; proceed to Phase 4 design.**

### B. Phase 2 sweeps (structural integrity)

| Module | Sweep | Result |
|--------|-------|--------|
| M30 (Phase 2a) | simple_apr24 realization-aware labels | ⚠ Sweep STRUCTURE good (realization scoping intact), but a line-citation in module_30.md:522 drifted (`simple_apr24/input.gms:24` should be `:14`). 1 Major doc_error. |
| M80 (Phase 2b) | nlp_apr17 Parameters table | ⚠ Sweep added table correctly, but 2 of the line citations in the newly-added table are off by 1 (s80_counter `:13`→`:14`; s80_resolve_option `:14`→`:15`). 2 Minor doc_errors. |
| M11 (Phase 2c) | §17.2 cost-aggregator | ✅ The 32-term / 27-source-module structure verified clean by Q3. 1 Minor adjacent-line citation drift (line 58→60 for vm_maccs_costs comment), independent of §17.2 itself. |

**Pattern**: the sweeps were content-correct but the cited line numbers within sweep artifacts weren't re-verified against post-sweep source. This is the exact failure mode Phase 1 1d (citation-fingerprint hardening) was supposed to catch, except it ran clean on the pre-launch baseline. The drifts are recent (introduced during Phase 2) and the fingerprint check apparently didn't fire on the new tables and citations. **Worth investigating**: did `check_gams_citations_impl.py` skip the new content, or does its fingerprint heuristic have a hole?

### C. Phase 1 mechanizations

| Mechanization | Catches | R25 outcome |
|---|---|---|
| 1a check_units.py | Unit drift (Tg/Mg) | No unit bugs surfaced in R25 questions; can't disambiguate from no-test. |
| 1b check_consumer_attribution.py (Pattern D) | Wrong consumer attribution | ⚠ MISSED: M36 (employment) consumes vm_cost_prod_crop but module_38.md doesn't list it. Validator pre-launch said 0 mismatches, but its negative-evidence check (consumer modules that grep-match the variable but are absent from the producer doc's consumer list) appears to be a gap. |
| 1c MANDATE 17 (one-hop reads) | Direct vs transitive attribution | ✅ Q3 correctly disambiguated: M51 is upstream of M57 via emission quantities, not a cost intermediary. The "transitive vs direct" classifier worked. |
| 1d check_gams_citations_impl.py fingerprint | Citation drift to wrong content | ⚠ MISSED: 5 line-citation drifts surfaced in R25 (Q1, Q2 × 2, Q3, Q5) that the fingerprint check should ideally have flagged. Pre-launch baseline said clean. Either the check ran against pre-Phase-2 content snapshot, or the fingerprint heuristic missed these adjacent-line drifts (because content within ±5 lines IS similar — e.g., other scalar declarations near s80_counter). |

### D. AGENT.md trim degradation watch

| Indicator | R25 outcome |
|---|---|
| G1 score (regression) | 10/10 — stable across R22 (10), R23 (10), R25 (10). No degradation. |
| G2 score (regression) | 10/10 — R22 fix holds. The vm_carbon_stock declaration anchor survives the trim. |
| Q5 organic routing to magpie4 helper | ✅ Worked. Agent loaded `magpie4_reference.md`, cited `.cache/sources/magpie4/`, traced IAMC → reportEmissions → ov_emissions_reg → q51 → q55. The version-pin discipline (from Phase 0 magpie4 fold-in) held. |

**Verdict**: the AGENT.md trim (846 → 724 lines) did NOT degrade response quality on either regression anchor or on the magpie4 routing test.

### E. Routing additions

Q5 demonstrated the magpie4 helper auto-loads correctly under organic question framing (IAMC variable provenance). The Phase 0 magpie4 fold-in (5 scaffold sections + auto-load trigger) is functional.

## Root-cause cluster analysis (R25 bugs)

| Cluster | Bug count | Bugs | Doc_error vs answerer |
|---|---|---|---|
| **C1: Line-citation drift in docs** | 6 (1 Major + 5 Minor) | Q1-B1 (m30:522 input.gms:24→14), Q2-B1 (m80:316 :14→15), Q2-B2 (m80:315 :13→14), Q3-B1 (m11:452 :58→60), Q5-B1 (m55-related :21→22), plus Q2-B4 informational | 6 doc_error |
| **C2: Missing consumer in attribution lists** | 1 Major | Q4-B1 (m38 missing M36 consumer) | 1 doc_error |
| **C3: Answerer compression of multi-site behavior** | 1 Minor | Q2-B3 (s80_secondsolve described as 2 sites, actually 8) | 1 answerer_confabulation |
| **C4: Stylistic/informational** | 3 Info | Q1-B2 (off-by-one count "four respects" enumerated as 5), Q1-B3 (rotamax simplification), Q4-B2 (declarations line not separately verified) | 3 mixed |

**Doc_error : answerer_confabulation ratio = 8 : 3** — most bugs are in the docs, not Sonnet's reasoning. The fixes are largely mechanical line-citation updates.

## Fixes to apply (Step 5)

| File | Edit | Bug ID |
|------|------|--------|
| modules/module_30.md:522 | `simple_apr24/input.gms:24` → `:14` for `c30_rotation_constraints` | Q1-B1 |
| modules/module_80.md:316 | `s80_resolve_option` declarations.gms `:14` → `:15` | Q2-B1 |
| modules/module_80.md:315 | `s80_counter` declarations.gms `:13` → `:14` | Q2-B2 |
| modules/module_80.md:309 | Range header — re-verify with corrected lines | Q2-B1/B2 |
| modules/module_11.md:452 | `vm_maccs_costs` comment line `:58` → `:60` | Q3-B1 |
| modules/module_11.md:442 (parallel) | `vm_reward_cdr_aff` comment line `:57` → `:59` (auditor flagged as similar drift) | Q3-B1 parallel |
| modules/module_38.md (5 locations: L33, L121, L336, L357, L617) | Add M36 as consumer of vm_cost_prod_crop; cite `modules/36_employment/exo_may22/equations.gms:23-25` `q36_employment` | Q4-B1 |
| (file TBD by fix agent) | `vm_manure_confinement` declarations `:21` → `:22` | Q5-B1 |

## Validator gaps surfaced

These are NOT bugs to fix in R25 — they're follow-up work for a future infrastructure pass:

1. **Pattern D negative-evidence check**: `check_consumer_attribution.py` should grep for any module that mentions the variable in an equation and flag those NOT listed as consumers in the producer doc. Current check appears to only verify the listed-consumers-grep-positive direction.
2. **Citation-fingerprint sensitivity**: `check_gams_citations_impl.py` missed 5 line-citation drifts. The fingerprint heuristic may be too tolerant when adjacent lines contain similar content (e.g., scalar declarations near each other).

These should be added to Phase 1 follow-up backlog or fed into Phase 4 design.

## Conclusion

**R25 mean 8.93 / R24 mean 7.5 = +1.43 score recovery, passing the ≥8.5 "improvement" gate.**

Phase 0-2 work was net positive. The remaining bugs are:
- 6 mechanical line-citation drifts (easy fixes; suggests Phase 1 1d validator needs hardening)
- 1 consumer-attribution gap in M38 (suggests Phase 1 1b validator needs negative-evidence check)
- 1 answerer compression error (not a doc issue)
- Stylistic informationals

**Plan recommends R26** to re-probe Phase 2 sweep modules. With the line-drift fixes applied, R26 should confirm post-sweep stability. Phase 4 design can begin in parallel.
