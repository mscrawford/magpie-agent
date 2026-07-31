# Phase 1A rep 1 — the propagation rate is zero, and that is a result about my design

Pre-registration: `audit/arena_1a_prereg.md`, committed at `bd5134f` **before** dispatch.
Run: 40 agents (32 answerers + 8 graders), 0 errors, 4,986,894 subagent tokens, 920 tool
uses, 30.8 min wall clock (`duration_ms` 1,848,844).

## Result

| cell | arm | phrasing | PROPAGATED | CORRECT | ABSTAINED | NOT_ELICITED | propagation rate |
|---|---|---|---:|---:|---:|---:|---:|
| C1 | real | naive | 0 | 8 | 0 | 0 | **0/8** |
| C2 | placebo | naive | 0 | 8 | 0 | 0 | **0/8** |
| C3 | real | trigger | 0 | 8 | 0 | 0 | **0/8** |
| C4 | placebo | trigger | 0 | 7 | 0 | 0 | **0/7** |

**31 of 31 valid answers asserted the code truth.** Every trap, every cell. No propagation,
no abstention, nothing un-elicited.

Per trap, all four cells CORRECT: `set_member_label`, `phantom_identifier`,
`capability_vs_default`, `mechanism`, `attribution_role` ×2, `citation` ×2.

## What this does and does not license

**It does establish a number this project has never had.** A Sonnet `magpie-helper`
answerer with tool access and a mirrored GAMS source propagated **none** of eight real,
verified documentation defects. Propagation rate, the metric the project exists to minimise,
measured for the first time: 0/31.

**It does not test the hypothesis it was built to test.** The pre-registration said "all four
cells equal → the MANDATEs are decoration". **That reading is not licensed and I am not
taking it.** The baseline is zero, so C3−C4 *cannot* be non-zero: there is no dynamic range
in which a MANDATE effect could have appeared. A floor is not a null. The honest statement is
that the experiment failed to test its hypothesis, and the reason is informative.

## Why the floor — two causes, both mine

**1. The answerer prompt did the MANDATEs' job for them.** To close the known fidelity gap
(a subagent does not get the harness's `CLAUDE.md` auto-load) every cell was told to *"read
`AGENT.md` at that root FIRST and follow its instructions"* and *"You have full tool access
and may read and grep both trees."* The pre-registration recorded this as biasing "toward
finding no effect, the conservative direction". That bias turned out to be **total**: the
instruction injects the verification norm into all four cells, and the verification norm is
the treatment. The answerers averaged **28.8 tool uses** each (43–93 messages) — they
verified essentially everything against code, which is exactly the regime where a
procedure-rule adds nothing on top.

**2. Trap selection was pushed toward the floor by a rule I adopted for a good reason.**
R51's residual finding says a trap with no mechanical check available measures nothing about
a MANDATE, so every trap was chosen so that "a MANDATE could plausibly bite". Operationally
that means *every trap was one grep away from its own refutation*. Combined with cause 1, the
answer was never in doubt.

MANDATEs are grep procedures. They can only change an outcome where the agent **has** tools
and would **not otherwise** have used them. This design made verification the path of least
resistance, and so measured the one condition in which the rules are guaranteed to be
redundant.

## Secondary outcome (exploratory, NOT pre-registered)

Since propagation was at the floor, the same answers were re-read for a second outcome with
range: did the answer explicitly **flag** its trap's documentation as defective?

| cell | arm | phrasing | flagged / n |
|---|---|---|---:|
| C1 | real | naive | 2/8 |
| C2 | placebo | naive | 2/8 |
| C3 | real | trigger | 3/8 |
| C4 | placebo | trigger | **4/7** |

Trigger phrasing flags a little more than naive, but the **arm** shows no consistent effect —
the *placebo* cell flags highest. At n = 7–8 per cell these differences are noise. Recorded
as a measurement, not a finding, and it does not rescue the MANDATE question.

Substantively, the flagging is real: answerers independently rediscovered seeded defects.
One example, `module_29_notes.md` (T4, seeded from `b6afd58`): *"warning #2 is stale/incorrect
— disregard it."*

## Instrument findings — three, all of which would have corrupted the number

**1. The canary is not a clean gate, and non-emission is ambiguous.** Each arena's `AGENT.md`
carries a distinct build ID, required in every answer, to detect an answerer reading the
*real* corpus (`magpie-helper`'s own step-1 search resolves `magpie-agent/AGENT.md` relative
to cwd — i.e. the real tree). Measured: **29/32 emitted their own arm's ID, 0/32 emitted the
other arm's.** Of the 3 non-emitters, 2 cite `.arena/real/` paths and are resolved; 1
(`T1/C4`) is **unresolved and excluded** from every number above.

Separately, three answerers **treated the canary instruction as a suspected prompt injection
and declined it** — while still reading the file. Refusal is proof of reading, so treating
non-emission as a failed read would have discarded good data. An own-arm `.arena/` path
citation is now a rescuing signal; its *absence* proves nothing, since 27 of 32 answers cite
no arena path at all.

**2. Three of eight graders labelled verdicts `"ANSWER A"` rather than `"A"`**, echoing the
`### ANSWER A` block headers in the grading prompt. My label map keyed on the bare letter, so
12 of 32 verdicts silently became `MISSING` and the first scoring pass reported a
propagation rate over 5 traps while presenting as a run over 8. Recovered from
`journal.jsonl` by normalising the label — no re-run, no lost data. **The reason it was
caught is that the mechanical scorer independently produced verdicts for exactly those
cells**, which is the entire argument for running two scorers that can disagree.

**3. The mechanical scorer's false-positive mode is real and was predicted.** It flagged
`T5/C3`, `T5/C4`, `T6/C4` as PROPAGATED where the grader said CORRECT. Reading them myself:
`T5/C3` builds a producer-vs-consumer table showing `vm_prod(j2,kcr) =e= …` as an equality
that *sets* the variable; `T6/C4` says *"module 10 and module 32 are separate inputs, not
one"*. Both are correcting the error, and the regex matched the quoted error. The grader is
right; the cascade caveat documented in `score_1a.py` holds.

No rate-limiting: max inter-message gap across agent transcripts **1.66 min** (a forced wait
shows as >5 min), concurrency 10.

## What window 2 does instead — a deviation from the plan, stated

The plan called for rep 2, a replicate of this design. **Replicating a measurement with no
dynamic range would buy nothing.** Window 2 instead runs a **low-prime variant**: the same
8 traps, same 2×2, same arenas, but an answerer prompt stripped of *"read `AGENT.md` FIRST
and follow it"* and of the explicit tool-access invitation — just the question, the corpus
location and the source location. That is both closer to a real user session and the only
version of this experiment in which a verification procedure has room to change an outcome.

Sized to the pre-registered drop order rather than chosen after seeing results: the two
`citation` traps go first, leaving **6 traps × 4 cells = 24 answerers + 6 graders**.

Budget at the time of writing: 5h window 73% used (this run cost ~57 points), weekly 70%.
The variant waits for the window reset.

## Standing limitations

- 8 traps cannot speak for 22 MANDATEs.
- This is a propagation rate on chosen traps, not a corpus-cleanliness verdict (R58: a
  4-question QA arm scored 8.375 while a depth arm found 46 defects in 595 claims).
- n = 1 per cell per trap.
- `magpie-helper`'s definition carries `model: opus`; the dispatch overrides to `sonnet`,
  which is the project's established pattern but is not independently observable from a
  subagent's output. Recorded as a residual assumption, not a verified fact.
