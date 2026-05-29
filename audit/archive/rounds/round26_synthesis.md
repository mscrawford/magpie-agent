# Round 26 synthesis (re-measure) — 2026-05-29

**Context**: Interactive recovery run after the scheduled 00:00 Berlin overnight run failed to fire (ScheduleWakeup timer frozen by macOS sleep; root cause in project memory `project_overnight_run_scheduling` / global `feedback_unattended_run_wake_source`). User directed 2 rounds (R26+R27), not 3; overnight 05:30 time guard overridden by explicit instruction. Verification baseline `origin/develop` (parent tree on `experiment/tc-marginal-pb`, read-only fetch). Answerer Sonnet 4.6 (magpie-helper, docs-only); auditor Opus 4.8 (general-purpose, vs origin/develop). Commits local only; nothing pushed.

**Type**: re-measure of R25 Phase-2 sweep modules M30/M11/M80 + regression anchors G1/G2.

## Results

| Q | Module(s) | Archetype | Score | Crit | Maj | Min | Source | Fixed? |
|---|---|---|---|---|---|---|---|---|
| R26-Q1 | 30 / 10 / 14 | default+causal | 8 | 0 | 0 | 2 | answerer slip | no (doc correct) |
| R26-Q2 | 11 / 38 / 56 / 39 / 13 / 50 | cost aggregation | 9 | 0 | 0 | 1 | answerer slip | no (doc correct) |
| R26-Q3 | 80 / 11 | solver edge case | 7 | 0 | 1 | 1 | doc_error | **yes** |
| R26-G1 | 14 | regression anchor | 10 | 0 | 0 | 0 | clean | n/a |
| R26-G2 | 52 / 56 / 29 / 31 / 32 / 34 / 35 / 59 | regression anchor | 7 | 0 | 0 | 3 | doc_error | **yes** |

**Mean 8.2** (range 7-10). Bugs: 8 total (0 Critical, 1 Major, 7 Minor); root cause doc_error 5, answerer_confabulation 3. **Fixed this session: 5** (all doc_error). Deferred: 0.

**Gate**: PARTIAL. 0 bombs (Critical) in M30/M80/M11 = PASS. Mean 8.2 < 8.5 target = MISS, driven entirely by the two doc errors below — both root-cause-fixed, so a re-measure should recover.

## Fixes applied (all verified vs origin/develop, validators re-run clean)

1. **M80 modelstat-7 mischaracterization** (Q3-B1 Major + B2 Minor, doc_error). `module_80.md` Limitation #8 + Modelstat-table row 7 claimed modelstat 7 is "accepted as success," importing `lp_nlp_apr17`'s `if(modelstat=1 or 7)` `vm_landdiff` gate (`lp_nlp_apr17/solve.gms:74,194`) into the default `nlp_apr17` description. Code truth (`nlp_apr17/solve.gms`): 7 (`>2`) enters the retry loop (`:47`), never satisfies the `<=2` success-exit (`:91`), saves no timestep GDX (`:98` requires `<=2`) and does not abort (`:102` excludes `ne 7`) — "silent limbo." Rewrote both locations and re-attributed the gate to `lp_nlp_apr17`.

2. **G2 vm_carbon_stock populator list** (G2-B1/B2/B3, 3 Minor, doc_error; calibration-anchor regression 10→7). `module_56.md` (583/616/1037-43) and `module_52.md` (423) listed populators as (30,31,32,35,58). Verified-correct set (default realizations, vs origin/develop): **29 (crop, eq:39), 31 (past, :23), 32 (forestry, :108), 34 (urban .fx=0, presolve:8), 35 (natveg, :43/50/54), 59 (SOM soilc, :62)**. M30 populates the separate `vm_carbon_stock_croparea` (`:88`) which M29 folds in; M58 peatland has zero `vm_carbon_stock` references. Corrected both docs; reconciled `module_52.md` self-contradiction (267-272 was already correct). Also aligned `module_52.md:483` (`fm_carbon_density` consumers) to the in-doc 265-272 list, and rephrased `module_56.md:1044` to avoid a consumer-attribution-checker false positive.

   **Root cause of the regression**: R23 declined to fix this doc ("the answer was right, so no doc bug"), conflating a correct *answer* (Sonnet re-deriving from code) with a correct *doc*. The wrong list stayed; R26's Sonnet trusted it. Overrode the R23 decline on new, code-verified, load-bearing evidence.

## Validators (post-fix, vs baseline)
- `validate_consistency.sh`: 39/41 pass, 2 pre-existing advisories — unchanged.
- `check_consumer_attribution.py`: 9 — unchanged (after rephrasing the one phrasing-induced FP).
- `check_units.py`: 5 advisory — unchanged.

## Anchors
- G1 (M14): 10, stable (R22/23/25/26 = 10). No drift.
- G2 (M52/56): 7, **drift=YES** (regression), root-caused + fixed this round.
