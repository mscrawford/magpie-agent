# Seeded-bug benchmark — 2026-07-31 re-run, and a reassessment of the benchmark itself

**Run** 2026-07-31 · `audit/tools/seed_known_bugs.py` · supersedes
`audit/seeded_bug_benchmark_2026-07-20.md`, which stays for the comparison.

Two questions were asked: *did eleven days of reliability work move detection?* and
*is this benchmark actually measuring what it claims?* The second turned out to be the
more informative one.

---

## Headline

| | 2026-07-20 | 2026-07-31 |
|---|---|---|
| measured | 49 | 48 |
| caught | 16 | **20** |
| skipped (no longer applies) | 4 | 5 |
| **raw detection** | **32.7%** | **41.7%** |

**Compare raw to raw.** The older doc's banner-adjusted 30.4% does not apply here: this
run contains **zero** banner-only hunks (pure additions of an advisory banner, which
inject no wrong claim when reversed), so there is nothing to adjust away.

### The attribution check the last run left unmeasured

The 2026-07-20 caveat said a "catch" only means *some* checker emitted a new finding on
that doc, not that the finding names the injected defect — and flagged the inflation as
unmeasured. Measured now, by comparing each injected hunk's identifiers, numbers and
edited line against the finding text:

- **18 of 20 catches are attributable** to their injection.
- **2 are unresolved** (`module_10.md` hunk 1, `module_52.md` hunk 5) — not shown to be
  coincidental, only not provable by token overlap.
- **0 catches came only from a finding in a different file.**

So the attribution-verified floor is **37.5% (18/48)** and the raw figure is 41.7%. The
feared inflation is real but small — at most 2 catches, not the large effect the caveat
allowed for.

> Method note, because it nearly produced a wrong answer: a first pass reported 4-5
> unattributable catches. That was an artifact of splitting hunks with `--unified=0`
> while the harness uses `git show`'s default 3-line context, so the hunk INDICES did not
> line up. Re-run against the harness's own `split_hunks()`, the number fell to 2. An
> analysis of an instrument needs the instrument's own conventions.

---

## The reassessment: what was wrong with the benchmark

**The checker list held 11 entries while 29 checkers existed**, and the headline was read
as "what fraction of real doc bugs does the gate catch". It was measuring a subset and
naming it the gate. Corrected to 22 (the 7 exclusions are now named in the source with
reasons, so an exclusion is distinguishable from an oversight).

**The hypothesis this was supposed to fix was WRONG, and that is the useful part.**
`citation` scored 0/2 while *neither citation checker was in the list*, so it looked like
a measurement artifact. Prediction stated before measuring: adding them would move
`citation` off zero.

**It did not. The rate did not move at all — 20/48 before, 20/48 after — and every one of
the 11 added checkers fired ZERO times.**

That is a stronger result than a correction would have been: the blind spots are **real
blind spots, not instrument gaps**, and the 11-checker list was empirically sufficient.
The correction still belongs — the measurement should match its name — but it changed no
number.

### What the failed hypothesis uncovered instead

Chasing *why* the citation checkers cannot fire produced a concrete, previously unrecorded
coverage gap.

Both `citation` bugs are in `modules/module_80.md`, and both are bare-basename cites that
should be realization-qualified:

```
-  ... (solve.gms:16, 174)
+  ... (lp_nlp_apr17/solve.gms:16, 174)
```

`check_no_bare_cites` (Check 25) **explicitly exempts** `modules/module_NN.md`, on the
stated grounds that "context is the module itself". **That exemption is unsafe for
multi-realization modules.** M80 has **four** realizations — `lp_nlp_apr17`, `nlp_apr17`,
`nlp_ipopt`, `nlp_par` — and **each has its own `solve.gms`**. A bare `solve.gms:16` inside
module_80.md is four-way ambiguous.

This is the same failure class that made CI red on 2026-07-31 (a bare cite resolving by
filesystem walk order), one level in: *inside* a module doc, where the checker deliberately
does not look. **23 of 46** modules have more than one realization — counted from
`module.gms` dispatch lines, and note this is one more than the 22 recorded in `AGENT.md`,
because the develop sync gave M14 a second realization — so the exposed surface is exactly
half the corpus. M80 is the worst case at four.

**Actionable**: narrow Check 25's module-doc exemption to SINGLE-realization modules. That
is the one mechanical fix this benchmark run identified.

---

## By bug class

| Class | 2026-07-20 | 2026-07-31 |
|---|---|---|
| `attribution_phantom` | 2/2 | **2/2** |
| `diagram_phantom` | 1/1 | **2/2** |
| `set_membership` | 1/2 | **2/2** |
| `attribution_read` | 10/26 | **12/26** |
| `attribution_set` | 0/5 | **1/5** |
| `mixed` | 0/4 | **1/4** |
| `data_source` | 0/1 | 0/2 🔴 |
| `attribution_role` | 0/2 | 0/2 🔴 |
| `citation` | 0/2 | 0/2 🔴 (diagnosed above) |
| `mechanism` | 0/1 | 0/1 🔴 (LLM territory by decision) |

`attribution_set` moved off zero for the first time — Check 41 fired on the module_59
Critical, the exact bug that motivated it.

## The number that should bother us most

**15 of the 22 checkers never fired on any seeded bug.** Only seven ever fire:
`check_dependent_counts` (6), `check_module_set_claims` (5), `check_consumer_attribution`
(4), `check_dependent_direction` (2), `check_attribution_omissions` (2),
`check_attribution_prose` (2), `check_fenced_identifiers` (2).

This is **not** proof the other fifteen are broken — their classes may be absent from a
sample of 48 drawn from 12 commits. But combined with mutation survival at 45.6%, the
honest reading is that a large part of the battery has never been shown to catch a real
bug **or** to survive mutation. Those are the checkers to point the next measurement at.

---

## Caveats that still stand

- **n=48 from 12 commits**, weighted toward recent attribution work. Not a random sample
  of doc bugs; the per-class split is more meaningful than the aggregate.
- **The sample drifts as the corpus does.** Skips went 4 -> 5 partly because this session
  edited docs the harness injects into (`module_10/14/17/29/30/52`). Cross-run comparison
  is therefore approximate, not exact — the denominator is not fixed.
- **This measures the CHECKER BATTERY, not the whole gate.** The inline bash checks
  (3, 5, 7-12) are not represented at all.
- Every bug in this sample *was* eventually found — by expensive LLM audits, not by the
  gate. 41.7% is the deterministic layer's share, not a claim that the rest go undetected
  forever.
