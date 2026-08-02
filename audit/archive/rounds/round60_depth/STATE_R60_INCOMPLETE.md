# magpie R60 — INCOMPLETE. Not a measurement.

**Status: HALTED mid-run on a monthly spend limit, 2026-08-02.** 27 of 60 agents completed;
33 failed with `You've hit your monthly spend limit`. **No number in this round may be
quoted as a result.** The pre-registered decision rules in
`audit/corpus_investigation_plan.md` are **all UNDECIDED** — see *What cannot be answered*.

## What ran

| phase | ran | expected |
|---|---:|---:|
| Enumerate (ledgers → denominators) | **9** | 9 |
| Audit lenses (structured return) | **18** | 45 |
| Audit lenses (report written to disk) | **21** | 45 |
| Verify (adversarial refutation) | **0** | 9 |
| Measure | **0** | 1 |

| doc | arm | claims | lens coverage |
|---|---|---:|---|
| `carbon_balance_conservation` | cross_module | 210 | **5/5** |
| `circular_dependency_resolution` | cross_module | 110 | **5/5** |
| `modification_safety_guide` | cross_module | 156 | **5/5** |
| `water_balance_conservation` | cross_module | 94 | 2/5 returned, **5/5 on disk** |
| `land_balance_conservation` | cross_module | 181 | 1/5 |
| `nitrogen_food_balance` | cross_module | 123 | 0/5 |
| `module_35` / `module_34` / `module_56` | **module** | 364 / 117 / 594 | **0/5 — arm entirely missing** |

## ⚠️ The returned matrix is invalid, in two independent ways

**1. `Critical: 0` and `Major: 0` in every cell is an ARTIFACT, not a finding.**
`isConfirmed()` requires a Critical/Major to carry a surviving refuter verdict. Zero
refuters ran, so `verdictByBug[b.id]` was undefined for all of them and **122 Critical/Major
findings were silently zeroed**. A reader glancing at the matrix would conclude the
`cross_module/` docs contain no serious defects. The opposite is closer to true.

**2. Full denominator, partial numerator.** Ledgers are cheap and run first, so all 9
returned (1,949 claims). Findings came from 18 of 45 lenses. Every rate off the pooled
matrix is therefore biased **downward** by construction.

Both are now guarded: the workflow counts `crit_major_dropped_unadjudicated` explicitly and
emits a `validity` block with `reportable:false` plus a warning, and the measure agent is
instructed to return UNDECIDED unless every criterion can be evaluated on fully covered docs
alone. Verified by replaying this round's exact completion pattern (refuses) against a
complete run (passes).

## What the salvageable part shows — LEAD ONLY, below the confirmation bar

The 3 docs with complete structured coverage, **476 claims**:

```
raw findings                 201
after prose-key dedup        170
after code-fact dedup         98   <- distinct defects
                            ----
distinct / claims          98/476 = 20.6%   95% CI [17.2%, 24.4%]

Critical      13 raw ->  7 distinct
Crit+Major   122 raw -> 59 distinct
```

**Why this is not a result:** zero adversarial refutation ran. This project's bar is
refuted-survived; R58's refuters left 46 of 47 findings standing but moved several
severities *down*, so the Critical/Major split is precisely the least reliable part of an
unrefuted tally. Treat 20.6% as an upper envelope on 3 docs, not a density.

**Why it is still worth recording:** R55 measured 5.6% on 3 module hubs. Even if refutation
halved this, `cross_module/` would sit well above — the direction Sprint X predicted. And 7
distinct Criticals on 3 docs against R55's 1 on 3 docs is a large gap. A lead to test, not a
finding to cite.

**The dedup earned its keep on first contact:** 201 → 98 is 2.05x. Without it this round
would have reported ~42%.

**Selection caveat:** the 3 complete docs are simply the first 3 in the dispatch array — they
finished before the limit hit. Arrival order, not a doc property, but not random either.

## What cannot be answered, at any confidence

- **The locus comparison — the round's primary question.** The within-module arm has zero
  lens coverage on all 3 docs. There is no within-module rate to compare against.
- **Any Critical/Major rate**, unrefuted.
- **Every pre-registered decision rule.** All UNDECIDED at this n.

## Recovery, when budget allows

1. `water_balance_conservation` has **5/5 complete reports on disk**; 3 failed only on the
   structured return. Those findings are recoverable without re-running the agents, but they
   are prose and must not be hand-merged into a structured tally — different substrate.
2. Re-run with the same args. The 3 complete docs plus 9 ledgers replay from cache
   (`resumeFromRunId: wf_5e1dec91-4bf` **plus the full args payload** — a resume does NOT
   restore args; that is what voided the 03:23 attempt).
3. The refutation phase is the priority: without it nothing here clears the bar.

## Also in this directory

`MEASUREMENT_VOID_2026-08-02.md` — output of the **earlier void run** (zero docs audited, an
all-zero matrix from an argless invocation). Kept as evidence of that failure mode. Its
corpus-Criticals extrapolation is built entirely on inherited numerators and **must not be
cited**; its diagnosis of the void, which it got right and refused to paper over, is the
part worth reading.
