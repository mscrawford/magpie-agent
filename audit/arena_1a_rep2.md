# Phase 1A rep 2 — the effort ablation: the floor breaks, the arms still don't separate

Pre-registration: `audit/arena_1a_prereg.md` (`bd5134f`, before any dispatch).
Rep 1: `audit/arena_1a_rep1.md` — 0/31 propagation, a floor rather than a null.

Rep 2 changes **one** thing: answerer reasoning effort, set to `low`. Same arenas, same
traps, same prompt, same controls, same pinned `sonnet` answerer. The two `citation` traps
were dropped by the **pre-registered** drop order, not chosen after seeing rep 1.

Run: 30 agents (24 answerers + 6 graders), 0 errors, 1,875,849 subagent tokens, 5.6 min
(`duration_ms` 337,927).

## The manipulation worked

| | rep 1 | rep 2 | change |
|---|---:|---:|---:|
| answerer tool uses (mean) | **28.1** | **6.0** | **4.7× fewer** |
| subagent tokens | 4,986,894 | 1,875,849 | 2.7× fewer |
| wall clock | 30.8 min | 5.6 min | 5.5× faster |

Counted by parsing each transcript for content blocks of `type == "tool_use"` — not by
substring-matching the log, where `"tool_use"` also appears in `stop_reason` and
`tool_use_id`.

**A correction to rep 1's record.** It reported 28.8 tool uses per answerer, computed as the
workflow's total (920) over answerers only (32) — a numerator that includes grader tool use
over a denominator that excludes graders. Parsed properly, rep 1 answerers used **900** tool
calls, mean **28.1**, and its 8 graders used 20. The figure was an over-estimate of about 2%
and changes no conclusion, but it was wrong as stated.

## Result

| cell | arm | phrasing | PROP | CORR | ABST | N/E | propagation rate |
|---|---|---|---:|---:|---:|---:|---:|
| C1 | real | naive | 1 | 5 | 0 | 0 | **1/6** |
| C2 | placebo | naive | 1 | 5 | 0 | 0 | **1/6** |
| C3 | real | trigger | 1 | 5 | 0 | 0 | **1/6** |
| C4 | placebo | trigger | 1 | 4 | 0 | 1 | **1/5** |

24 of 24 valid. **The floor broke** — propagation is no longer identically zero — and the
four cells are indistinguishable.

Per trap: `T1` `T2` `T3` `T4` CORRECT in all four cells; **`T5` PROPAGATED in all four**;
`T6` CORRECT in three, NOT_ELICITED in the fourth.

## What the propagation actually was, checked by hand

The entire signal is **T5**, and it failed the same way in every condition. Each answer
names Module 18's `flexcluster_jul23` realization as a direct cell-level consumer of
`vm_prod` — without flagging that `flexcluster_jul23` is **not the default**. The default is
`flexreg_apr16` (`config/default.cfg:625`), which reads regional `vm_prod_reg`, not cellular
`vm_prod`. That is exactly the defect `ec119a9` fixed, and exactly what AGENT.md Step 1c
("ALWAYS LEAD WITH THE DEFAULT REALIZATION") exists to prevent.

The `vm_prod`-producer half was handled better than the grader's single verdict suggests:
`T5/C1` says *"`vm_prod(j,k)` is set by module 30 (croparea)"* and `T5/C4` says
*"30_croparea … **producer**, not consumer"*. Both then blur it in a summary line that lists
producers and consumers together. So the PROPAGATED verdicts rest on the non-default
realization half, which is genuine; the producer half is closer to CORRECT than the verdict
implies. Recorded because the honest reading is narrower than the headline number.

**One likely grader miscall, in the conservative direction.** `T6/C4` was scored
NOT_ELICITED, but the answer states plainly that *"`vm_land_forestry` is declared in module
32 (forestry), realization `dynamic_may24`"* — which is the trap's primary defect, answered
correctly. NOT_ELICITED is excluded from the denominator, so this shrinks n rather than
flattering any cell. Left as graded rather than hand-adjusted; hand-tuning verdicts to taste
is how a scoreboard stops meaning anything.

## What this does and does not license

**Does:** the propagation channel is real and measurable. Rep 1's zero was an artifact of the
regime, not a property of the corpus — drop verification effort 4.7× and defects reach the
user.

**Does not:** it still does not answer the MANDATE question, though for a better reason than
rep 1. With a non-zero baseline, C3 ≈ C4 is a genuine null rather than a floor artifact — but
the entire signal is **one item that behaved identically in all four conditions**. A single
condition-insensitive item cannot discriminate conditions. The correct summary is: no
evidence of a MANDATE effect, on evidence too thin to support an equivalence claim either.

**C1 ≈ C2 held exactly** (1/6 vs 1/6). The pre-registered control for the control passes in
both reps: with no trigger keyword, the content of `verifiers.md` on disk does not matter.

## The finding that matters most

At low effort, **16 of 24 answerers never emitted the canary** — against 29 of 32 at normal
effort. Transcript analysis (below) proves all 24 nonetheless stayed inside their assigned
arena. So the failure is not "read the wrong corpus"; it is **"never read AGENT.md"**.

That sharpens the hypothesis this experiment was built around. The concern was that the
auto-load trigger table is matched against the user's *input* while the risk lives in the
*output*. Rep 2 shows a blunter failure upstream of that: **a hurried agent never loads the
routing table at all**, so no trigger — matched or not — can fire. `verifiers.md` is
unreachable in exactly the regime where its grep procedures would have been worth having.

This is arm-independent and does not depend on the null above.

## Methodological upgrade: fidelity by observation, not self-report

The canary (a per-arm build ID in each arena's `AGENT.md`, required in every answer) worked
at normal effort and **collapsed** at low effort, because emitting it requires reading *and*
obeying `AGENT.md` — the very behaviour low effort suppresses. Scored on the canary, rep 2
would have discarded 16 of 24 answers and reported a propagation rate over 8 observations
with C3 empty.

Replaced by direct observation: parse each answerer's own transcript for the corpus paths it
actually opened, and check containment in its assigned arm. Result: **24 of 24 answerers
touched only their assigned arena; 0 touched the other arm; 0 touched the real corpus.**
(Three transcripts show both arms — all three are graders, which legitimately read answer
files from both.) The map is persisted as `fidelity_rep{N}.json` and `score_phase1a.py` now
prefers it over the canary when present.

The general form: when a harness mediates what a subject can see, verify the environment by
observing it, not by asking the subject to report on it. A self-report gate fails precisely
when the subject is least attentive — which is the condition you most want to measure.

## Also handled

- **5 of 24 answerers skipped the disk write** at low effort (some returned only a pointer
  stub; one returned nothing but the canary line). Their text was recovered from
  `journal.jsonl` by joining on the grader's verbatim `evidence` quote, requiring a **unique**
  match — 5 recovered, 0 ambiguous.
- All 6 traps returned 4/4 grader verdicts: the `"ANSWER A"` label normalisation added after
  rep 1 held.

## Standing limitations

- 6 traps, n = 1 per cell per trap, one propagating item.
- Effort is confounded with run order (rep 1 default, rep 2 low). A within-run effort factor
  would be the cleaner design.
- Propagation rate on chosen traps is not a corpus-cleanliness verdict (R58).
- `magpie-helper` carries `model: opus`; the dispatch overrides to `sonnet`. Established
  project pattern, still not independently observable from a subagent's output.
