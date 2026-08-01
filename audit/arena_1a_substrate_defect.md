# The grading substrate was not the answer — and that explains most of the adjudication delta

Phase A of the follow-up plan set out to harden the grading layer, on the premise established
2026-08-01 that a single Opus grader "is not a measurement": three blind adjudicators had
overturned 11 of 21 of its verdicts while agreeing with each other 20/21.

That premise is now substantially wrong, and the reason is a defect in **my harness**, not in
the graders.

---

## What happened

The answerer prompt told each agent to write its complete answer to a file **and also** return
it as its final text:

> When you are done, write your complete answer to `.arena/out/rep<N>_<trap>_<cell>.md`
> and ALSO return it as your final text.

Those two artifacts are not the same. The workflow's grading stage consumes the **returned
text** (`phase1a_propagation.workflow.js` stage 1 returns `[cell.id, txt]`; stage 2 builds the
grader prompt from those values). The blind re-adjudication batch, however, was assembled from
the **files on disk** (`adjudicate_set.json` records a `path` of `.arena/out/…` for all 21).

So the original grader and the adjudicators were reading different documents.

| substrate comparison | cells |
|---|---:|
| returned text ≈ written file (similarity > 0.98) | 31 / 104 |
| **materially divergent** | **73 / 104 (70%)** |
| returned text is a **stub** (<300 chars) while a full answer exists on disk | **12** |

The stubs are not degenerate answers. They are dispatch artifacts — the agent wrote its real
answer to the file and returned something else:

| cell | grader saw | answerer wrote |
|---|---:|---:|
| rep2 T6 C4 | 21 chars — `corpus-id: ARENA-2XQ8` | 1072 |
| rep4 T6 C3 | 26 chars — `Not relevant to this task.` | 803 |
| rep3 T2 C2 | 45 chars — `Not relevant to this task — no action needed.` | 2936 |
| rep2 T3 C3 | 55 chars | 3295 |
| rep4 T5 C3 | 109 chars | 3088 |

**Of those 12 stub cells the grader scored 7 CORRECT**, 4 NOT_ELICITED and 1 PROPAGATED. An
"answer" consisting of the literal string `Not relevant to this task.` entered the denominator
as a *good* outcome.

## Why it matters more than it looks

The defect is **differential**. It barely touches the control regime and concentrates in the
treated one:

| rep | regime | cells graded on a stub |
|---|---|---:|
| 1 | normal effort | **0 / 32 (0%)** |
| 2 | low effort | 5 / 24 (21%) |
| 3 | docs-only | 3 / 24 (12%) |
| 4 | low effort replicate | 4 / 24 (17%) |

A measurement error that spares the control and corrupts the treatment is not noise; it acts
directly on the contrast the experiment exists to estimate. This is the same failure shape as
the canary-fidelity gate that had to be abandoned earlier in this project — a mechanism that
degrades precisely in the cell being measured.

## What this does to the adjudication conclusion

Re-classifying each of the 21 adjudicated answers by whether the two graders even read the same
text:

| mapping of the two rubrics | agree | genuine grader error | **substrate artifact** |
|---|---:|---:|---:|
| strict (`ASSERTS_FALSEHOOD` only counts as bad) | 11 | 2 | **8** |
| rubric-faithful (falsehood **or** omitted-default counts as bad) | 17 | 2 | **2** |

The rubric-faithful row is the fairer comparison: the original grader's `PROPAGATED` was defined
to include implicit assertion ("describing a capability as active when the code default disables
it"), which is exactly what the adjudicators' `OMITS_DEFAULT_CAVEAT` captures.

Of the two remaining disagreements on **identical** text, only one is a grader error:

- **A05** (rep3 T6 C3, similarity 1.00) — the answer names a module-32 realization
  `plant2forestry`, which occurs **zero times** in the tree (module 32 has only
  `dynamic_may24`). The grader scored it **CORRECT**. A genuine miss.
- **A21** (rep4 T6 C4, similarity 1.00) — the answer states the code truth (module 32 declares
  `vm_land_forestry`) *and* repeats the doc's `10_land` attribution in its dependency list. The
  grader scored **ABSTAINED**, which is what its own rubric instructs: "An answer that states
  BOTH the wrong claim and the right one, without resolving which holds, is ABSTAINED." That is
  a **rubric-definition difference**, not an error.

**So `arena_1a_adjudication.md`'s central inference — that the single-grader *design* is not a
measurement — is not supported by its own evidence.** The dominant driver of the 11 overturned
verdicts was substrate divergence. The single-grader design may still be weak; this experiment
did not test it.

## The shape of my error

Last night I wrote, in the adjudication record:

> I corrected a real error in the right direction and then over-corrected into a second wrong
> conclusion, because I re-examined the aggregation and never re-examined the verdicts.

The same move, one level down. This time I re-examined the verdicts and never re-examined the
**inputs to the verdicts**. Each pass audited the layer that had just failed and took the layer
beneath it on trust. The general lesson is not "check the verdicts" or "check the inputs" but:
when an instrument is found faulty, the replacement instrument needs its own provenance chain
checked end to end, because a *replacement* is exactly where an unexamined substrate enters.

## Fixes

1. **Grade the artifact the answer was written to, not the return value.** The written file is
   the answer; the return value is a dispatch side-channel.
2. **Assert substrate identity in the harness.** Before grading, compare returned text to the
   written file and abort or flag any cell where they diverge. This is mechanical and cheap.
3. **Never let a short return silently become a verdict.** A sub-300-character "answer" is an
   instrument event, not a performance observation.
4. Prefer a single artifact: have the answerer return the text only, or write the file only.
   Two channels that "should" agree will not.

## Status of the Phase 1A numbers, revised again

- **Still safe** — the effort manipulation (28.1 → 6.0 tool calls/answerer) and the
  `AGENT.md`-never-read finding. Both are parsed from transcript `tool_use` inputs and touch
  neither grading nor the return channel.
- **Still unsafe** — the propagation rate and the regime effect, but for a *newly identified*
  reason, and now with a known direction of bias in the low-effort cells: 7 stubs scored CORRECT
  deflate propagation there. The earlier concern (the grader missing falsehoods, which would
  deflate rep 1's `0/31`) pushes the contrast the other way. Both are live; neither is quantified.
  Only a re-grade on the correct substrate settles it.
- **Newly established** — the substrate defect itself, measured above.
