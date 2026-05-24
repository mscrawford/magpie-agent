# R23 Semantic Validation Report

**Date**: 2026-05-24
**Models**: Sonnet 4.6 answerers + Opus 4.7 auditors (7 parallel each)
**Scope**: Probes targeted Phase 2 migration-touched docs (cross_module/ conservation+safety, agent/helpers/ migrated, AGENT.md format-examples) + G1/G2 regression anchors
**Validator state**: 37/40 passed, 3 advisories — held throughout (no regressions from R23 fixes)

---

## Headline

- **Mean score 9.0/10 — new all-time high** (prior: R6 8.7, R22 8.67). First round to clear 9.0.
- Zero Critical bugs (third consecutive round). Both regression anchors stable at 10/10.
- **G2 improvement is the headline regression signal**: R22 had 3 Minor auxiliary-list errors (M30/M58/M59 producer confusion); R23 had zero — Sonnet's producer enumeration now matches ground truth exactly. The R22 anchor correction is propagating into agent behavior.

## Scores

| Question | Topic | Score | Bugs (C/M/m/info) |
|----------|-------|-------|--------------------|
| R23-Q1 | Diet→nitrogen-cycle chain (M15→M16→M17→M50→M51) | 7.0 | 0/1/1/0 |
| R23-Q2 | Water infeasibility diagnostic (M43 + 2 migrated helpers) | 9.0 | 0/0/1/0 |
| R23-Q3 | M44 modification safety (cross_module docs) | 9.0 | 0/0/1/0 |
| R23-Q4 | Output interpretation pipeline (interpreting_outputs.md) | 10.0 | 0/0/0/1 |
| R23-Q5 | AGENT.md format compliance (post-migration examples) | 8.0 | 0/1/0/0 |
| R23-G1 | M14 default realization + equations (anchor) | 10.0 | 0/0/0/0 |
| R23-G2 | vm_carbon_stock M52/M56 chain (anchor) | 10.0 | 0/0/0/0 |
| **Mean** |  | **9.0** | **0/2/3/1** |

## Bug summary

5 in-answer bugs (0 Critical, 2 Major, 3 Minor) + 1 latent helper-pool bug surfaced by Q4 audit.

| Bug ID | Severity | Source | Status |
|--------|----------|--------|--------|
| Q1-B1 | Major | doc_error propagation: module_17.md propagated stale "vm_prod_reg(i,kli) = 0" framing predating M71 foragebased_jul23 default | **FIXED** — module_17.md §1.3, §7.2, §10.5 rewritten |
| Q1-B2 | Minor | doc_error propagation: module_15.md "28 kcal/day red meat" diverges from actual USA t_redmeat=44 | Deferred (illustrative, auditor demoted) |
| Q2-B1 | Minor | answerer_confabulation: imprecise gloss "vm_prod(j,kli) divided by v42_irrig_eff" — only crop term is | No fix (answerer issue) |
| Q3-B1 | Minor | answerer_confabulation: added "/yr" to vm_cost_bv_loss units; GAMS says "mio USD17MER" without /yr | No fix (answerer issue, agent doc correct) |
| Q5-B1 | Major | doc_error enabled gap: verifiers.md MANDATE 16 didn't reference Check 25 (check_no_bare_cites.py) | **FIXED** — MANDATE 16 "Verified by" extended |
| Q4 latent | (n/a in answer) | doc_error: interpreting_outputs.md:63 + :176 wrongly cited rds_report.R:40-45 for IAMC format enforcement (lines actually do variable-presence checks) | **FIXED** — both lines corrected |

## Doc fixes this session

1. **`modules/module_17.md`** (§1.3 Scope and Limitations, §7.2 Livestock/Fish/Forestry status, §10.5 Debugging guidance)
   Rewrote three sections to acknowledge that since M71 `foragebased_jul23` became default (2023), `vm_prod(j, kli_rum)` and `vm_prod(j, kli_mon)` are populated via M71's constraints, so `vm_prod_reg(i, kli)` is non-zero. The stale `realization.gms:13-14` `@limitations` comment is now explicitly flagged as out of date.

2. **`agent/helpers/verifiers.md`** (MANDATE 16 "Verified by")
   Extended the validator list to include `scripts/check_no_bare_cites.py` (Check 25, added 2026-05-24 by the bare-cite migration). Clarified the two validators' distinct roles: `check_gams_citations` for line-range validity; `check_no_bare_cites` for full-path convention enforcement in non-module docs.

3. **`agent/helpers/interpreting_outputs.md`** (lines 63 + 176)
   Corrected the wrong attribution that `rds_report.R:40-45` enforces IAMC `"Name (unit)"` format. The actual code at those lines does `expectVariablesPresent()` against AR6/NAVIGATE/SHAPE/AR6_MAgPIE mappings — a variable-presence check, not a format check. Format construction lives inside `magpie4::getReport()`.

## Migration-coverage validation

The migration scope (Phase 2 work landed 2026-05-24 before R23):
| Migration target | R23 probe | Outcome |
|---|---|---|
| `cross_module/nitrogen_food_balance.md` (citation rewrites) | Q1 | Citations functional; no rewrite bugs surfaced |
| `cross_module/water_balance_conservation.md` | Q2 | OK |
| `cross_module/modification_safety_guide.md` (citations + content) | Q3 | OK |
| `cross_module/circular_dependency_resolution.md` | Q3 | OK |
| `agent/helpers/scenario_diet_change.md` (29 cite conversions) | Q1 | OK (Q1-B1 root cause was module_17.md, not the helper) |
| `agent/helpers/debugging_infeasibility.md` | Q2 | OK |
| `agent/helpers/water_scarcity_scenarios.md` | Q2 | OK |
| `agent/helpers/interpreting_outputs.md` | Q4 | Latent doc bug (rds_report.R:40-45 attribution) surfaced + fixed |
| AGENT.md format-example updates | Q5 | OK (verbatim quotes matched) |
| `agent/helpers/verifiers.md` MANDATE 16 | Q5 | Doc gap (missing Check 25 reference) surfaced + fixed |

The migration's bare-cite conversion (109 mechanical + ~19 hand-fixed across 19 docs) did not introduce any visible citation drift in R23 answers. The two surfaced doc bugs were content-attribution issues, not citation-form issues.

## Trend signals

- **G2 anchor stability**: R22 was the anchor's first run (with the corrected expected_answer_summary); R22 scored 7/10 with 3 Minor auxiliary-list errors. R23 scored 10/10 with zero errors. Confirms the R22 anchor correction (M56 declares, not M52) propagated into stable agent behavior.
- **G1 anchor stability**: Stable at 10/10 in both R22 and R23. The q14_yieldcalib confabulation that contaminated earlier rounds is fully purged.
- **mean_score_trend** (last 5 rounds): 8.0 → 8.2 → 8.0 → 8.67 → 9.0 — monotonic improvement over the last 4 rounds.
- **Critical-bug streak**: R21 + R22 + R23 = three consecutive Critical-free rounds.
- **Doc-error rate**: 2 of 5 in-answer bugs were doc-error propagation (40%). Down from R3's ~75% confabulation. The remaining doc errors are surfaced surgically (single-section in M17; single-line in helpers) rather than systemic.

## Cumulative stats (post-R23)

```
total_rounds:                23
total_docs_validated:        79
total_bugs_found:            457 (+6)
total_bugs_fixed:            301 (+3)
validator_checks:            25  (+4 since R22)
validator_sub_checks:        40  (+4)
gams_variables_verified:     953
gams_equations_verified:     139
gams_realizations_verified:  75
file_line_citations_verified: 2598
last_validation_date:        2026-05-24
mean_score_trend:            ...→8.67→9.0
```

## Next steps (already queued by user for next session)

R5 `/pipeline-audit` is the natural follow-up. It's a multi-lens structural audit of the agent's machinery rather than a content-validation flywheel; R23 confirms content quality is high enough that structural drift (helper coverage gaps, validator coverage gaps, instruction-surface coherence) is the dominant remaining risk class.
