# The regrade: numbers re-established on the correct substrate

All 104 Phase 1A answers re-graded from the **written-file** substrate with a hardened rubric —
two independent Opus graders per trap group, blind to arm/rep/cell, each required to verify the
code truth itself, plus an **un-anchored** step asking for any *other* assertion the code
contradicts. Disagreements went to an independent adjudicator. 17 agents, 2.23M tokens, 470 tool
uses, 0 errors.

Data: `audit/data/arena_1a_regrade.json` (paths scrubbed). Harness:
`audit/tools/regrade_phase1a.workflow.js`. Non-LLM key: `audit/tools/check_answer_identifiers.py`.

---

## 1. The single-grader design was not the problem — the substrate was

**Two independent graders agreed on 103 of 104 answers (99%).** One disagreement, one
adjudicator.

That is the cleanest possible confirmation of `arena_1a_substrate_defect.md`. The earlier
"11 of 21 overturned" was never evidence about grader reliability: graders reading the *same*
text agree essentially always. What differed before was the input, not the judgment.

**The `arena_1a_adjudication.md` retraction stands, and its replacement conclusion is now
positively supported rather than merely asserted.**

## 2. Propagation rate, re-established

Denominator excludes `NOT_ELICITED` (1 answer).

| definition | rate | 95% CI |
|---|---|---|
| **narrow** — asserts something the code contradicts | **12/103 = 11.7%** | [6.8, 19.3] |
| **wide** — falsehood *or* omitted default caveat | **20/103 = 19.4%** | [12.9, 28.1] |

The wide definition is the one comparable to the original rubric, whose `PROPAGATED` explicitly
covered implicit assertion. It lands at 19.4% against the withdrawn 20.0% — the old figure was
about right, but arrived at over a substrate that was wrong in 70% of cells. Right answer, broken
method; it is now measured rather than lucky.

## 3. The regime effect survives — and splits into two different failures

| rep | condition | narrow | wide |
|---|---|---:|---:|
| 1 | normal effort | 3.1% (1/32) | 3.1% (1/32) |
| 2 | low effort | 4.2% (1/24) | 20.8% (5/24) |
| 3 | **docs-only** (no GAMS access) | **29.2% (7/24)** | 29.2% (7/24) |
| 4 | low effort replicate | 13.0% (3/23) | 30.4% (7/23) |

Original framing (rep 1 vs reps 2–4 pooled): **wide p = 0.0058**, reproducing the withdrawn
p = 0.0062 almost exactly. Narrow: p = 0.0985.

The split rubric earns its keep here, because the two regimes fail in *different ways*:

- **Low effort degrades completeness.** Rep 2 asserts almost no falsehoods (4.2%) but its wide
  rate is 20.8% — a 16.6-point gap that is *entirely* omitted default caveats. A hurried agent
  still says true things; it stops saying which realization they are true of.
- **No code access degrades correctness.** Rep 3 (docs-only) is the only cell where narrow and
  wide coincide at 29.2%: those agents assert outright falsehoods. Against normal effort this is
  **p = 0.0157** on the narrow measure — the strongest single contrast in the experiment.

That is a mechanistically sensible result: an agent that cannot open the GAMS source cannot
refute a wrong doc line, so it repeats it. An agent that can, but is hurried, verifies the claim
and drops the caveat.

## 3b. Per-trap: the class effect is real, and so is the item effect

| trap | class | narrow | wide |
|---|---|---:|---:|
| T1 | set_member_label | 0/16 | 0/16 |
| T2 | phantom identifier | 0/15 | 0/15 |
| T3 | capability-vs-default | 12.5% | 12.5% |
| T4 | mechanism/realization | 0/16 | 0/16 |
| **T5** | attribution_role | **25.0%** | **75.0%** |
| **T6** | attribution_role | **31.2%** | 31.2% |
| T7 | citation | 0/4 | 0/4 |
| T8 | citation | 25.0% | 25.0% |

This settles two claims that were argued in both directions across the previous two sessions.

**The class effect is real.** The `attribution_role` pair runs **28.1% (9/32) against 4.2%
(3/71) for every other class**, Fisher **p = 0.0012** narrow, p < 0.0001 wide. The earlier worry
— that a class rate had been manufactured by pooling heterogeneous items so that one item drove
it — does not survive: *both* members are elevated, and the class separates from the rest of the
corpus decisively.

**The item effect is also real, but only on the wide measure.** T5 vs T6 is **p = 1.000 narrow**
(25.0% vs 31.2%) and **p = 0.032 wide** (75.0% vs 31.2%). Both prior positions were half right:
the re-adjudication's "these two items behave the same" holds for outright falsehoods, and the
synthesis's withdrawn §3 ("propagation is item-specific") holds for the omitted-caveat measure.
Its stronger clause — *"not class-specific"* — is wrong.

The honest statement is that propagation is **class-specific AND item-specific**, and which one
you see depends on whether you count omitted default caveats. T5's 75% wide against 25% narrow is
the single largest narrow/wide gap in the corpus: answers about which modules consume `vm_prod`
overwhelmingly name a realization without saying it is not the default.

That is a direct argument for Phase B — the non-default-realization checker targets exactly the
gap that dominates the worst trap in the corpus.

## 4. The arm null holds

| | narrow | wide |
|---|---:|---:|
| real `verifiers.md` (22 MANDATEs) | 9.6% (5/52) | 17.3% (9/52) |
| placebo stub | 13.7% (7/51) | 21.6% (11/51) |

Fisher p = 0.555 (narrow). The 22 MANDATEs show **no detectable effect on trap propagation**,
confirmed now on the correct substrate with a 99%-agreement instrument. This was the finding
already believed safe; it survives.

**And this time it is a real null, not a floor.** The reason rep 1's original `0/31` was
uninterpretable is that a control pinned at zero leaves no room for any effect to appear. Here
both arms sit well off the floor (5/52 and 7/51, 12 events total), so "no difference" is a
measurement rather than an artifact of the outcome having nowhere to move.

### What the arm null does and does not mean — scope it before quoting it

**The ablation never removed the instruction to cite.** `AGENT.md` is byte-identical in both arms
(bar the 2-line canary) and already mandates *"ALWAYS state where your information came from"*,
*"Reference specific files, equations, and line numbers"*, *"Cited `file:line` for factual
claims"* and *"NEVER FABRICATE"*. The placebo stub even keeps the accuracy framing. So this
experiment measured the **marginal** value of the 22 procedural MANDATEs on top of an
already-instructed baseline — **not** "instructions vs no instructions". Anyone reading the null
as "documentation rules do not change agent behaviour" is reading it several sizes too large.

Twelve mechanical surface measures (length, citation count, code fences, epistemic badges,
distinct identifiers, realization naming, "default" mentions, hedging, grep evidence,
DECLARED/POPULATED/READ language, attribution blocks, headings) are **flat across arms** — all
p > 0.45, including within rep 1 alone, the one cell where `AGENT.md` was reliably read. The same
measures move **2–7×** under regime changes (normal-vs-low effort; code access vs docs-only, where
citations run 8.8 vs 1.2). The instrument detects large behavioural differences easily; it detects
none from the MANDATEs.

Tested directly against what MANDATE 16 uniquely governs — full-path vs bare-basename citation —
the effect points the right way and is too small to resolve: full-path **share 60.9% real vs
53.9% placebo (p = 0.299)**; bare cites 3.42 vs 4.54 (p = 0.167); rep 1 alone 68.1% vs 64.1%
(p = 0.624).

**But see the separate, non-LLM result:** on *mechanically certain* defects (fabricated
identifiers and impossible line citations) the arms split 1/52 real vs 7/52 placebo, p = 0.06 —
see `arena_1a_substrate_defect.md` § and the caveats there (not pre-registered, n = 8, the defect
definition was widened after a first look). The two are compatible: the MANDATEs may not stop an
agent repeating a defect it *read*, while still reducing what it *invents*. Neither claim is
settled; the second needs a pre-registered replication.

## 5. The un-anchored field works — 6 of 6

Every one of the 6 answers carrying a mechanically certain fabrication was flagged by at least
one grader's `other_falsehoods`, against a non-LLM key. Five of the six still received a trap
verdict of `CORRECT_AND_COMPLETE` — correctly, because the trap claim *was* handled; the
fabrication was elsewhere in the answer.

That is precisely the blind spot of the original anchored rubric, which asked only "did the
answer repeat *this* defect?" and therefore scored those answers clean. Keep both fields.

Volume warning: the graders reported **261 other-falsehood items across 77 answers**. That is a
candidate pool, not a result — it is an LLM claim, unverified, and at that volume it certainly
contains false positives. Nothing from it enters the ledger without independent re-derivation.

## 6. The awareness covariate — recorded, underpowered, not load-bearing

10 of 104 answerers detected the canary instruction and refused it as a suspected prompt
injection (7 of them in rep 1). Those 10 produced **0 falsehoods** vs 12/93 among the rest, but
with zero events in one cell that is p = 0.601 — no evidence, only an absence.

The concern it raised is answered: excluding all aware answers, rep 1 vs reps 2/4 is 1/25 vs
4/44 (p = 0.646), materially unchanged. **Awareness is not driving the control's low rate.**

## 7. What is now safe to quote

- Inter-grader agreement 99%; the single-grader design is not implicated.
- Propagation 11.7% narrow / 19.4% wide, with the intervals above.
- The regime effect (wide, p = 0.0058) and its decomposition into completeness vs correctness.
- Docs-only vs normal on outright falsehoods, p = 0.0157.
- The arm null on trap propagation.
- The effort manipulation (28.1 → 6.0 tool calls) and the `AGENT.md`-never-read finding, both
  unchanged and both independent of grading.

Still **not** settled: the arm difference on mechanically certain defects (p = 0.06, exploratory)
and the 261 unverified other-falsehood candidates.
