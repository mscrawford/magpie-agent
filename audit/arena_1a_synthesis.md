# Phase 1A synthesis — four runs, 89 scored answers, and what actually moves propagation

Pre-registration `audit/arena_1a_prereg.md` (`bd5134f`, before any dispatch).
Per-run records: `audit/arena_1a_rep1.md`, `audit/arena_1a_rep2.md`.

Four runs, one arena pair, one trap set, one pinned `sonnet` answerer. Each run changes
exactly one thing from the last.

| rep | regime | agents | tool uses / answerer | tokens | propagation | 95% CI |
|---|---|---:|---:|---:|---:|---|
| 1 | normal effort, GAMS source available | 40 | 28.1 | 5.0M | **0/31 = 0.0%** | [0.0, 11.0] |
| 2 | **low** effort, GAMS source available | 30 | 6.0 | 1.9M | **3/18 = 16.7%** | [5.8, 39.2] |
| 3 | low effort, **docs only** (no GAMS) | 30 | 5.3 | 1.9M | **4/22 = 18.2%** | [7.3, 38.5] |
| 4 | low effort + GAMS (exact replicate of 2) | 30 | 8.6 | 1.8M | **4/15 = 26.7%** | [10.9, 52.0] |

**Numbers revised 2026-08-01 after a fidelity defect was found; the first published version of
this table read rep 2 as 4/23 = 17.4%.** See §6. Rep 4 was added as an exact replicate of rep 2
and lands at 22.2%, within rep 2's interval.

Tool-use means are answerers only (900/32, 143/24, 128/24, 207/24), counted by parsing transcripts
for content blocks of `type == "tool_use"` — not by substring-matching a log where that
string also appears in `stop_reason` and `tool_use_id`.

`NOT_ELICITED` excluded from every denominator. Fidelity is established per answer by parsing
its transcript for the corpus paths it actually opened (§6): **0 cross-arm reads in any run**,
but **9 answerers did touch the live checkout** and are excluded. Rep 3 is the only fully
clean run (24/24 contained, and 0 opened a `.gms`, `config/` or `core/` path, so the
docs-only manipulation was exact).

## 1. Verification opportunity is the dominant lever

rep 1 (0/31) vs the three low-effort runs pooled (11/55 = 20.0%, CI [11.6, 32.4]):
**Fisher exact two-tailed p = 0.0062**.

Cut answerer effort 4.7× and roughly one in six documentation defects reaches the user.
That is the first measurement of propagation rate this project has, and it says the number is
not a property of the corpus — it is a property of the *regime the agent is answering in*.

## 2. The MANDATEs make no difference where they could act

Pooled over the three low-effort runs, which are the ones with dynamic range:

| `verifiers.md` | propagation | 95% CI |
|---|---:|---|
| real (22 MANDATEs) | 5/28 = **17.9%** | [7.9, 35.6] |
| placebo (framing only, no procedure) | 6/27 = **22.2%** | [10.6, 40.8] |

**Fisher exact p = 0.75**, at n = 55. The placebo arm is nominally *worse for the MANDATEs*
— 22.2% vs 17.9%, one event's difference, in the direction that would be expected if the
rules helped, and far inside the noise.

The pre-registered control for the control held in every run: **C1 ≈ C2** — with no trigger
keyword, what is on disk in `verifiers.md` does not matter, because it is never loaded.

This is a null, not an equivalence claim: at n = 55 the CIs are still wide enough to hide a
moderate effect. What can be said is that no MANDATE benefit was detectable in the only
regimes where a grep procedure had room to change an answer.

## 3. Propagation is ITEM-specific, not class-specific — a figure I nearly reported wrong

Pooled by class, `attribution_role` looked like a dramatic finding: 10/18 = 56% versus ~1%
for everything else, p = 0.0005. **That framing is wrong and it is worth recording why.**

| trap | class | propagated |
|---|---|---:|
| T1 | set_member_label | 0/11 |
| T2 | phantom_identifier | 0/8 |
| T3 | capability_vs_default | 1/9 |
| T4 | mechanism | 0/12 |
| **T5** | attribution_role | **10/11** |
| **T6** | attribution_role | **0/7** |

The class rate is two items with opposite behaviour averaged together. One trap propagates
almost always; its same-class sibling never propagates at all. A "50% for `attribution_role`"
headline would have been a real-looking number with nothing behind it — the failure mode this
repo already has a name for. **Report the item, not the class**, until there are enough items
per class to support one.

What T5 actually is: every propagating answer names Module 18's `flexcluster_jul23`
realization as a cellular `vm_prod` consumer without flagging that it is **not the default**
(`flexreg_apr16` reads regional `vm_prod_reg`, `config/default.cfg:625`). That is a
capability-vs-default failure wearing an attribution costume, and it is exactly what AGENT.md
Step 1c and the `ec119a9` fix both target.

## 4. The finding with the clearest action attached

At low effort, **16 of 24 answerers never emitted the arena's build ID** — against 3 of 32
at normal effort — while transcripts prove all of them stayed in their assigned arena. They
did not read the wrong corpus. **They never read `AGENT.md` at all.**

The hypothesis this experiment was built on was that the auto-load trigger table is matched
against the user's *input* while the risk lives in the *output*. The data shows a blunter
failure upstream of that: a hurried agent never loads the routing table, so no trigger —
matched or not — can fire. `verifiers.md` is unreachable in precisely the regime where its
procedures would have been worth having.

That is arm-independent, does not depend on the null in §2, and points at a mechanism rather
than at prose: **the trigger needs enforcement that does not depend on the model choosing to
read a file** (a hook, or a pre-answer gate), not better rule text.

## 5. Removing code access did not increase propagation — it increased abstention

rep 2 → rep 3 is one change: the GAMS source is taken away. Propagation is flat (16.7% →
18.2%, well inside noise), but `ABSTAINED` goes 0 → 2 and `NOT_ELICITED` 1 → 2.

Read carefully, and at this n it is a hint rather than a result: the docs-only answerers that
could not settle a question tended to say so rather than to invent. `T3` is the clean example
— the same trap produced PROPAGATED, ABSTAINED, ABSTAINED and CORRECT across the four cells,
with one answer refusing outright: *"Per the agent's Step 2c rule, I won't guess here."* The
inline epistemic instructions in `AGENT.md` appear to be doing work that the MANDATEs are not.

## What this does not support

- **Any corpus-cleanliness verdict.** This is a propagation rate on 6 chosen traps (R58: a
  4-question QA arm scored 8.375 while a depth arm found 46 defects in 595 claims).
- **Any per-class rate** — see §3.
- **Equivalence of the arms.** Absence of a detected effect at n = 55, not proof of no effect.
- **Anything about the 16 MANDATEs no trap touches.** 6 traps cannot speak for 22 rules.
- Effort is confounded with run order (rep 1 default, reps 2–4 low); a within-run effort
  factor would be cleaner.
- 12 of 86 scored answers were dropped for touching the live checkout or for cwd drift, and that exclusion is not
  random — it correlates with an agent failing to resolve the arena path. Rep 3, the only
  run with zero such reads, reproduces the same rate and the same arm null, which is the
  main reason the conclusions are not held hostage to it.

## Instrument changes earned during these runs

1. **Fidelity by observation, not self-report.** The canary (a per-arm build ID in each
   arena's `AGENT.md`) worked at normal effort and collapsed at low effort, because emitting
   it requires reading *and obeying* `AGENT.md` — the behaviour low effort suppresses. Scored
   on the canary, rep 2 would have discarded 16 of 24 answers and reported a rate with one
   cell empty. Replaced by parsing each agent's transcript for the paths it opened.
2. **Grader label normalisation.** Three of eight rep-1 graders returned `"ANSWER A"` rather
   than `"A"`, silently voiding 12 of 32 verdicts. Caught only because a second, mechanical
   scorer produced verdicts for exactly those cells.
3. **Answer recovery.** 21 low-effort answerers across reps 2–4 skipped the disk write;
   their text was recovered from `journal.jsonl` by joining on the grader's verbatim
   `evidence` quote with a **unique-match** requirement (21 recovered, 0 ambiguous).
4. **Vacuity guard.** The first invocation returned `{"results":[]}` in 49 ms with zero agents
   because `args` arrives JSON-encoded; the script now parses it and refuses to run empty.

## Where this leaves the original question

The plan asked whether the 22 MANDATEs change what an end user is told. Three runs say:
**not detectably, in any regime tested** — and more usefully, in the regime where they would
matter most they are never loaded. Combined with R55/R56 (every *mechanized* class at 0.00
residual, all residual in unmechanized classes), the weight of evidence now points the same
way from both the auditor side and the answerer side: **spend on mechanization and on making
the helper actually load, not on rewriting the rules.**

## 6. The fidelity defect found after first publication, and how it was found

The first version of this synthesis stated "0 read the real corpus". **That was false**, and
the way it became false is worth more than the correction.

Fidelity was originally checked by counting `.arena/real/...` vs `.arena/placebo/...` path
mentions per transcript. That test can only detect a *cross-arm* read. It cannot detect an
answerer reading the **live checkout**, because a live read produces neither token. Adding
rep 4 surfaced the gap: a grader remarked that one answerer "read the live checkout after
reporting the sandbox path missing".

Two failed detectors preceded the working one, both worth recording:

1. **A blob regex over the whole transcript.** It flagged 5–8 answers per run — but an
   answer that merely *cites* a doc path in prose (the workspace-relative form of
   `modules/module_60.md`) was counted as having opened it. Scanning a log is not parsing it.
2. **A regex with a negative lookbehind.** It placed a "not preceded by the arena prefix"
   lookbehind *before* an optional absolute-path group, so the lookbehind was evaluated at
   the wrong position and flagged legitimate **absolute arena paths** as live reads. Every
   "hit" it reported was in fact under `.arena/`.

The working test parses `tool_use` blocks, pulls `file_path` / `path` / `command` / `pattern`
out of the tool *input*, and classifies each corpus-naming token by plain substring: arena-real,
arena-placebo, or live. Result across all four runs:

| rep | transcript-mapped | contained | live-checkout reads |
|---|---:|---:|---:|
| 1 | 16 | 15 | 1 |
| 2 | 24 | 19 | 4 |
| 3 | 24 | **24** | **0** |
| 4 | 23 | 16 | 4 (+3 cwd-drift) |

The leak is **relative paths in Bash**: an agent that `cat`s a workspace-relative corpus path
(observed: the residues/production doc under the corpus root) from the workspace root reads the
live tree even though it was pointed at the arena. Rep 3 is
immune because a docs-only answerer had no reason to roam.

**Root cause, found by noticing a stray directory.** Rep 4 left an untracked `.arena/out/`
*inside the corpus repo* containing three answers. Those three agents ran with their working
directory set to the repo rather than the workspace root, so the relative arena path resolved
to somewhere that does not exist — they reported the sandbox missing and fell back to whatever
`modules/` and `core_docs/` resolved to, which is the live corpus. **Subagent cwd is not
guaranteed.**

That also exposes a hole in the gate itself: a relative read of `modules/module_60.md` from
inside the repo contains no corpus-root token at all, so the classifier cannot see it. The
three cells were caught only by the stray write and are excluded as `cwd_drift`; an equivalent
read that never wrote a file would still be invisible.

Fix for any future run: give the answerer a corpus root it cannot mis-resolve (pin the
subagent's working directory, or place the arena where no live sibling exists), assert the
corpus is reachable as step 1 of the answer, and keep the parsed transcript check as the gate
rather than the canary. Note also that rep 4's per-answerer tool use (8.6) ran higher than
rep 2's (6.0) on an identical config — consistent with agents burning calls hunting for a
corpus they could not resolve.
