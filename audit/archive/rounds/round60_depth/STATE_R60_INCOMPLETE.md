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
| `module_34` | **module** | 114 | **5/5 + REFUTED — completed 2026-08-02 morning, see below** |
| `module_35` / `module_56` | **module** | 364 / 594 | 0/5 |

> **UPDATE 2026-08-02 morning — this document was written before `module_34` completed.**
> The "within-module arm entirely missing" statement below is superseded: `module_34` now
> has full lens coverage AND a refuter verdict, making it the round's first — and the
> project's only — clean within-module measurement. The arm is 1 of 3 docs, not 0 of 3.

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

## `module_34` — the one complete, refuted result (2026-08-02, commit 6f446ba)

Within-module arm, drawn at random (seed 60), and the **coldest doc in the corpus** — 2 prior
round records, never depth-audited. `validity.reportable: true`, 5/5 lenses, refuter ran.

```
claims                    114
findings (prose key)       37   32.5%  95% CI [24.6%, 41.5%]
distinct (code-fact)       22   19.3%  95% CI [13.1%, 27.5%]
Critical 6   Major 13   fully refuted 0   CORRECTED 8
classes: other 7, mechanism 7, attribution_* 11, set_membership 4, citation 4
```

**This is the gradient's third point, and it is the one that matters:**

```
R55  3 MOST-audited hubs      498 claims   5.6%    1 Critical
R58  3 stale hubs             595 claims   7.7%    7 Criticals
R60  module_34, never audited 114 claims  19-32%   6 Criticals
```

Audit ATTENTION drives measured residual down, so a hub result is a **floor**, not a ceiling.
Caveats that must travel: n=1 doc; as the coldest doc this is plausibly a within-module upper
bound; and the refuter CORRECTED 8 of 19 Critical/Major rather than upholding them as
written, so the severity mix is softer than the raw counts suggest.

## What cannot be answered, at any confidence

- **The locus comparison — the round's primary question.** `module_34` gives a refuted
  within-module rate, but the cross_module side is still UNREFUTED, so the two are not
  comparable. **The cheapest possible completion is 3 refuters over already-cached lens
  results** — that alone answers the round's primary question.
- **Any cross_module Critical/Major rate**, unrefuted.
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
