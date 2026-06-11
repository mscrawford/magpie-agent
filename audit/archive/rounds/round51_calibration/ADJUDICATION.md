# R51 Phase 0 — Calibration result (hand-adjudicated)

**Date**: 2026-06-11
**Auditor under test**: claude-opus-4-8 (the R1-R50 production auditor tier; Fable was unavailable — nitrogen-content safeguard downgrades it to Opus in this workspace).
**Code base**: ea383032d (origin/develop). **Isolation**: each of 37 auditors restricted to `/tmp/r51_cal` (fixture + rubric) + `/tmp/magpie_develop_ro` (code). Verified post-hoc: 368 tool calls parsed, ZERO touched a forbidden path (no `magpie-agent/`, no git, no AI docs, no key). Every catch is code-grounded.
**Run**: 37 agents, 1.89M subagent tokens, 407 tool uses, 323 s wall.

## What was measured

The same-tier auditor's false-negative and false-positive rate in the **per-claim verification regime**: one bug isolated in a short answer, with a question pointing at the topic, audited against code. This is the regime the flywheel's question-probes operate in.

## Headline result (hand-adjudicated; the heuristic scorer mis-scored 3 fixtures, corrected below)

| Metric | Result | Wilson 95% CI |
|---|---|---|
| Overall sensitivity (planted caught) | **24 / 24 = 100%** | [86%, 100%] |
| Critical | 12 / 12 = 100% | [76%, 100%] |
| Major | 12 / 12 = 100% | [76%, 100%] |
| Replay (historically-survived bugs) | 7 / 7 = 100% | [65%, 100%] |
| Invented | 17 / 17 = 100% | [82%, 100%] |
| **Genuine** false-positive rate on clean controls | **0 / 13 = 0%** | [0%, 21%] |
| Bonus: errors the auditor caught in the "clean" controls | 2 / 2 | — |
| Severity-tier: under-called | 0 | the auditor only ever matched or **escalated** |

## Adjudications that overturned the heuristic scorer

- **fixture_06 (replay, realization count 40-vs-22)** — scorer flagged MISSED; actually CAUGHT. The auditor independently re-derived "22 multi-realization, 24 single" via directory count + positive control and called the planted "40 of 46" a Major fabricated count. Scorer's token-matcher under-extracted on a numeric claim (fixed). This is the bug that survived ~19 rounds historically; the auditor caught it cleanly when pointed at it.
- **fixture_18 (labelled CLEAN)** — scorer flagged as a false positive; actually a TRUE catch of an error I introduced. My "clean" control wrote that `fbask_jan16_sticky` "adds inertial feed-basket adjustment." The auditor read `fbask_jan16_sticky/realization.gms:8-10` and corrected: sticky = **capital-stock** inertia, not feed-basket. My key was wrong; the auditor was right.
- **fixture_24 (labelled CLEAN)** — scorer flagged as a false positive; actually a TRUE (Minor) catch. My control said endo_jun13 "endogenously determines pasture management"; the auditor cited the realization's own `@limitations` ("No consideration of explicit pasture management options") and noted it models pasture **area + carbon**, not management. My wording was imprecise; the auditor caught it.
- **"9 spurious findings on planted fixtures"** — NOT false positives. They are the auditor splitting one planted bug across multiple sub-findings (e.g. fixture_35 reported the fabricated `normal_apr22` realization as 3 findings), plus one legitimate *secondary* catch (fixture_04: it noticed that even the "wildfire" framing is non-default — active only under `s35_forest_damage=3`, default is 2). No spurious finding contradicted a genuinely-true claim.

## Interpretation — H1 vs H2

**H1 (corpus genuinely clean) is substantially supported for the per-claim verification regime.** The auditor is NOT grossly blind: it caught every planted bug across all classes — including the hardest (solution-level `.l/.lo` consumer blind spot; soilc parallel-vs-serial data flow; the `c13_croparea_consv=0` default-OFF gate) and all 7 replay bugs that historically survived audits — with zero genuine false positives, and it even caught two errors the (same-generation) fixture designer introduced. When the R1-R50 auditor was pointed at a claim, it could verify it. The clean late-round scores are, to that degree, real.

**Three honest limits (this does NOT fully close H2):**
1. **Easier than production.** Each fixture isolates ONE bug in ~3 sentences with a topic-pointing question. Production bugs are embedded in 600-line docs among hundreds of claims. 100% here measures *can-verify-when-pointed*, not *can-find-in-a-long-doc*. This is a competence ceiling / difficulty floor, not the production find-rate.
2. **Known classes only.** The planted bugs are classes a same-generation mind conceives. The unknown-unknown class — the deepest H2 — is untestable by same-generation fixtures and remains open. This is the specific residual a strictly stronger auditor (Fable/Mythos) or a human expert would still address.
3. **The replay reconciliation is the key actionable finding.** The 7 replay bugs survived historically yet were caught here. The reconciliation: they survived via **coverage gaps** (the claim was not probed that round), not auditor blindness. So the flywheel's dominant residual risk is **coverage** (which load-bearing claims get audited), NOT auditor false-negatives.

## Decision on Phase B / C / D

- **Phase B (diversity ensemble): SKIP for this regime.** Its purpose is to lower FNR by combining diverse auditors; FNR is already ~0 here, so it adds nothing. The genuinely informative harder test is a different design (below).
- **Phase B-prime (RECOMMENDED next): find-in-long-doc FNR.** Re-inject these same planted bugs into FULL doc copies and have the auditor audit the whole doc with NO pointing question. This isolates the coverage / needle-in-haystack variable that this run identified as the real residual, and yields the production-relevant find-rate.
- **Phase C (mechanical-coverage map): RECOMMENDED.** Partition load-bearing doc claims into (a) mechanically checked (LLM-independent), (b) ever LLM-audited, (c) never probed. Directly targets the coverage risk this run surfaced.
- **Phase D (human anchor): low urgency, targeted.** The auditor proved a strong check (caught the designer's own slips); spend human time on the "never probed" tail from Phase C.

## Implication for the original Fable plan

A future Fable round's marginal value is NOT re-auditing per-claim known-class bugs (Opus is already ~100%). It is specifically (a) the find-in-long-doc regime and (b) the unknown-unknown class via open-ended "what is wrong in this whole doc" auditing. If/when Fable is available (non-nitrogen workspace or Mythos path), point it there, not at isolated per-claim fixtures.
