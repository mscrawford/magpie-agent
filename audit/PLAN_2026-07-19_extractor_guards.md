# Plan — cover the detection half of `check_consumer_attribution`

**Written** 2026-07-19, self-contained overnight work.
**Needs nothing from Mike.** No doc edits, no pushes, no outward actions, no
adjudication. Test code only, in one checker.

---

## Correction: this plan's first draft was wrong

Draft 1 targeted "the unasserted ground-truth extractors" and carried a table
claiming `build_producer_map`, `build_gams_index`, `build_canonical_map` and four
others had neither a self-test nor a guard. **That table was false.**

The measurement behind it was an AST scan for direct calls by name inside each
`self_test` body. The 2026-07-17 retrofit (R58) drives those extractors over a
synthetic tree via a **`MAGPIE_DIR`-overridden subprocess** — which a scan for
direct `Name` calls structurally cannot see. Fingerprints `_write_fixture` /
`_scan_only` are present in five checkers. Mutation confirms it empirically:
`build_producer_map`, `build_consumer_map` and `strip_dims` now have **zero**
surviving mutants.

So the extractor work is DONE and this plan is the *sequel* the memory
`feedback_test_the_testers` already predicted: retrofitting moved dead-to-test
41% → 22.9% but mutation survival only 54.9% → 51.2%, because a neuter probe
resurrects a function without covering its branches. **The instruments were made
better, not fixed.**

## Measured baseline — reproduced twice, 2026-07-19

`python3 audit/tools/mutate_checkers.py --scripts-dir scripts --only check_consumer_attribution`

```
107 mutants, 80 survived (74.8%)      <- matches the R58 figure exactly
HALT THRESHOLD: >20% survival => "fix the instruments"   (exceeded 3.7x)
```

Survivors by function — the residue is entirely the DETECTION half:

| Function | Survived | Note |
|---|---|---|
| `scan_prose_omissions` | **24 / 24** | zero coverage |
| `main` | 21 / 24 | verdict emitter — HIGH per harness triage |
| `scan_table_rows` | **12 / 12** | zero coverage |
| `scan_prose_attribution` | **12 / 12** | zero coverage |
| `scan_populator_claims` | 5 / 15 | partial |
| `expected_consumer_count` | **4 / 4** | zero coverage |
| `scan_critical_consumers` | 1 / 1 | |
| `line_listed_nums` | 1 / 1 | |
| `build_producer_map`, `build_consumer_map`, `strip_dims` | 0 | ✅ already covered |

Survivor kinds: `cmp0` 39, `not` 25, `boolop` 13, `bool` 3 — i.e. comparison and
boolean *predicates*, which is precisely what the harness's triage calls HIGH
(detection predicate or verdict emitter), never formatting noise.

## Target

**52 of the 80 survivors sit in four functions with ZERO current coverage**:
`scan_prose_omissions` (24), `scan_table_rows` (12), `scan_prose_attribution` (12),
`expected_consumer_count` (4). Those four are the whole job. `main` (21) is the
stretch goal and is partly arg-parsing, so triage its survivors by line before
claiming them.

## Method

For each of the four, add self-test cases that drive the function directly over a
fixture and assert on its RETURN VALUE, not merely that it ran:

1. Read the function; enumerate its branches (each `if`, each `and`/`or` arm, each
   comparison against 0/empty).
2. Write one fixture per branch — positive AND negative, so a predicate flip has
   somewhere to show up. A single happy-path case cannot kill a `cmp0` mutant.
3. Re-run the harness `--only check_consumer_attribution` and confirm that
   function's survivor count DROPPED. That is the acceptance test — not a green
   self-test.

## Acceptance criteria — binding

1. **Mutation-verified per function.** Survivor count for the target function must
   fall. A green new self-test that does not move the survivor count is exactly the
   neuter-probe failure this plan exists to avoid — it would repeat R58's lesson
   rather than apply it.
2. **Report ABSOLUTE counts and the intervention size**, never the rate alone. Two
   denominator traps are on record: adding covered helper functions inflates the
   function count (164 → 231 last time, flattering the percentage), and a rate delta
   without "N of M functions retrofitted" is the numerator-without-denominator move
   this whole exercise exists to stop.
3. **No new helpers unless needed.** They land in the denominator as covered-by-
   construction and flatter the result.
4. **Vacuity control**: each new case must FAIL if the assertion target is stubbed.
5. Full gate green after each commit: `bash scripts/validate_consistency.sh` → 0 errors.
6. One commit per function, independently revertible.

## Non-goals — do NOT drift

- **Do not "fix" `check_consumer_attribution`'s logic.** This is test coverage only.
  Any real defect the new cases expose gets RECORDED, not fixed, so the fix is a
  separate reviewable change.
- **B4 role-map `.scale`/`.lo` misclassification** — Mike reserved it ("touches
  ground-truth machinery"). Confirmed real and broader than the ledger says
  (`_classify_statement` takes the LHS leading identifier, so `vm_prod_reg.lo(...) =`
  counts as POPULATE). Detecting it is in scope; changing the classifier is not.
- **`core_docs/` scan-scope gap**, **M36/M57 headings**, **the module_17 omissions**,
  **A3** — all need Mike's judgement.
- **Any push.** 13 commits sit local-only on `fix-attribution-bare-labels`.

## Operational notes

- `timeout(1)` does not exist on macOS. Do not wrap the harness in it.
- Run `--self-check` first (0.1s; positive/negative control pair).
- The harness JSON status values are `'SURVIVED'` and `'killed'` — **case differs**.
  A lowercase `== 'survived'` filter silently reports zero survivors and reads as
  perfect coverage. Cost me one wrong reading tonight; compare against the printed
  `MUTATION_RESULT` line every time.
- Full-battery re-measure at the end for the honest headline, since a single-checker
  delta says nothing about the suite.

---

# RESULTS — executed 2026-07-19, same night

All four target functions retrofitted. Four commits, one per function, each
independently revertible. **Test code only; no checker logic changed.**

## The numbers, absolute and with the intervention size

| Scope | Before | After | Delta |
|---|---|---|---|
| `check_consumer_attribution` survivors | 80 / 107 (74.8%) | **28 / 107 (26.2%)** | −52 |
| Full battery survivors | 507 / 987 (51.4%) | **455 / 987 (46.1%)** | −52 (−5.3 pp) |
| Checkers touched | — | **1 of 23** | — |
| Functions retrofitted | — | **4** | — |

Per function: `scan_prose_omissions` 24→1, `scan_table_rows` 12→0,
`scan_prose_attribution` 12→0, `expected_consumer_count` 4→0, and
`line_listed_nums` 1→0 fell out with the label-length case. **52 of the 52
zero-coverage survivors killed**, one of which is unkillable (below).

**The denominator did not move**: 107 mutants before and after in the checker,
987 before and after in the battery. No new helpers were added, so the rate
improvement is not the covered-by-construction inflation that took the function
count 164 → 231 last time. Per-checker diff confirms exactly 1 of 23 changed.

The full-battery baseline was **measured, not derived** — a detached worktree at
`c04094a` re-run through the harness — and came back 507, matching the derived
455 + 52 exactly. Both instruments agree.

## Finding 1 — equivalent mutant at `check_consumer_attribution.py:549`

RECORDED, NOT FIXED (this was test-only work by design).

The single surviving mutant in `scan_prose_omissions` is unkillable. The
walk-back guard is dead code:

```
for j in range(lineno - 2, max(-1, lineno - 10), -1):
    if j < 0 or j >= len(lines):
```

Both disjuncts are always False. The range stop is `max(-1, ...)`, so with step
−1 the lowest `j` yielded is `stop + 1 >= 0`; and `j <= lineno - 2 <= len(lines) - 2`,
so `j` is always in bounds. Swapping `or` for `and` cannot change behaviour.

Two independent confirmations: the bounds argument, and an instrumented run over
the real corpus where the branch fired **0 times** and an
`assert 0 <= j < len(lines)` never tripped.

*The first attempt at that empirical run was a FALSE NEGATIVE* — executing the
patched copy from `/tmp` made `MAGPIE_DIR` resolve to `/private/tmp`, so the
checker skipped the corpus silently and reported zero firings for the wrong
reason. The rerun was done in place and carries a positive control showing real
findings were emitted. This is the standing measurement hazard exactly: an
instrument that cannot see the thing it counts, failing toward the flattering
answer.

Harmless dead defensive code, not a bug. Removing it is a logic change and
belongs in a separate reviewable commit.

## Method note for the next session

The four target functions all share the shape `(text, rel_path, producers,
consumers) -> findings`, so they are testable directly against synthetic maps —
no `MAGPIE_DIR` subprocess needed. That is why this was cheap (the harness runs
in 9s on one checker) and why the same approach should work on the remaining
survivors: `main` (21), `scan_populator_claims` (5), `scan_critical_consumers` (1).

Two fixture details turned out to be load-bearing rather than cosmetic, and are
worth reusing:

1. **`vm_declonly`** — a variable whose producer is ABSENT from its own read set.
   That is the only shape in which the producer-skip rule is observable; with a
   normal variable, skipping the producer and not skipping it give the same
   answer, so the rule could be deleted with every test still green.
2. **The hedged far bullet** in the double-blank cases — it emits nothing of its
   own and exists purely to be wrongly unioned if the walk overruns, which keeps
   the expectation down to the findings the boundary actually governs.

Expected values were derived by hand from the loop bounds BEFORE running, and the
implementation agreed on all eight omission cases including the asymmetric
one-blank/two-blank behaviour.
