# The Arena — a third flywheel type

Two flywheels already exist in this repo:

| flywheel | question it answers | ledger |
|---|---|---|
| **semantic** (`/validate-semantic`) | is the documentation *accurate*? | `audit/validation_rounds.json` |
| **pipeline audit** (`/pipeline-audit`) | is the agent's own *machinery* sound? | `audit/pipeline_audit_rounds.json` |
| **arena** (this document) | does a corpus defect *reach the user's answer*? | `audit/arena_rounds.json` |

The arena is the only one that measures an **outcome** rather than an artifact. The others ask
whether a doc is right; the arena asks whether being wrong changes what a person is told. That
makes it the only place where "does this intervention help?" is answerable at all.

> **Naming.** "Round N" is now three-way ambiguous — semantic rounds, pipeline-audit rounds, and
> arena rounds, plus the preproc-agent's own rounds. Always say **"arena round 1A"**, never a bare
> "round 1A". See `agent/helpers/twin_agent_disambiguation.md`.

---

## What an arena round is

1. Build **two or more sealed corpora** that differ in exactly one thing.
2. Ask a **pinned answerer** user-style questions whose correct answer is fixed by the GAMS source.
3. Grade the answers against the **code**, not against the docs.
4. Report an outcome rate with an interval, and say which cells could not have produced an effect.

## Invariants — every one of these was learned by violating it

**1. Build the arena outside any git work tree.**
An arena built inside a work tree silently injected 0 of 5 seeded hunks while still producing a
plausible-looking corpus. Build in a temp dir; expose it through a symlink so prompts stay
relative.

**2. Ablate to a placebo, never to a deletion.**
Deleting a file leaves dangling pointers and makes the treatment "a read that 404s". Ship a
same-named stub with the same framing and no procedure. This isolates the *content* from the act
of loading.

**3. Never let one agent emit the same content through two channels.**
The answerer was told to write a file *and* return the text. They diverged in **70% of cells**;
in 12 the return value was a 21–109-character stub while a full answer sat on disk. One grading
pass read the return value and another read the files, and the disagreement was charged to the
graders for a full day. Pick one channel, or assert identity in the harness and fail loudly.
Grade the **written artifact**. See `arena_1a_substrate_defect.md`.

**4. Fidelity by parsed `tool_use` inputs — never a self-report, never a blob scan.**
A canary the agent must echo collapses at low effort, i.e. exactly in the cell being measured, and
can also be *refused on principle* (10 of 104 answers declined it as a suspected prompt
injection). A self-report gate fails **differentially**, deleting the treatment cell and keeping
the control.

**5. Pin the subagent working directory, or place the arena where no live sibling of the same
name exists.** Three of 24 agents resolved a relative path into the live tree and were caught only
because they happened to write. Make corpus reachability step 0 of the agent's own task, with an
instruction to **stop rather than substitute**.

**6. Pre-register the predictions, including the one that would falsify your hypothesis.**
Commit the pre-registration before any dispatch, and record the degradation ladder (what gets
dropped if compute runs short) *before* seeing results, so a shrunken n is a stated limitation
rather than a silent one. **Never drop a cell; drop items.**

**7. Check dynamic range before reading equal cells as a null.**
A control pinned at 0% cannot show an effect. Check the control's absolute value first, then check
whether your own prompt handed the treatment to every arm.

**8. An ablation only tests what it actually removed.**
Enumerate every surface that states the same rule before interpreting the null. Arena round 1A's
ablation removed `verifiers.md` but left `AGENT.md`, which already mandates citing, precision and
non-fabrication — so it measured the *marginal* value of the procedural layer, not "do
instructions work". Reported without that scope, the null reads several sizes too large.

**9. The rubric must be un-anchored as well as anchored.**
A grader pointed at one designated defect will score an answer CORRECT while it fabricates
elsewhere. Ask both "did it repeat *this* defect?" and "does it assert anything *else* the code
contradicts?". The second field caught 6 of 6 mechanically certain defects the first missed.

**10. Get a non-LLM key wherever the outcome allows it.**
Fabricated identifiers and impossible line citations are decidable by `test -e` and `wc -l`. Any
subset you can decide mechanically becomes an answer key no LLM produced, and is the only place a
grader's error rate can be measured rather than assumed. Tools: `audit/tools/check_*.py`.

**11. Verify a random, class-stratified sample before quoting any rate.**
Verifying findings you *chose* measures your ability to choose. Hand-picked 6/6 implied ~100%
precision where a stratified sample of 21 gave 57–67%.

## Standing components

| component | purpose |
|---|---|
| `audit/tools/prepare_audit_arena.py` | builds the sealed corpora (`--self-test` before use) |
| `audit/tools/phase1a_propagation.workflow.js` | answerer fan-out across cells |
| `audit/tools/regrade_phase1a.workflow.js` | hardened grading: split rubric + un-anchored field |
| `audit/tools/score_phase1a.py` | mechanical first-pass scoring |
| `audit/tools/calibrate_graders.py` | joins the non-LLM key to grader verdicts |
| `audit/tools/check_answer_identifiers.py` | fabricated names (non-LLM key) |
| `audit/tools/check_citation_content.py` | cited `file:line` contains what it is cited for |
| `audit/tools/check_default_realization.py` | non-default realization described without saying so |

Every checker ships `--selftest` with positive **and** negative controls. Run the positives: a dead
check passes its negatives vacuously, which has happened here.

## Reporting

Append to `audit/arena_rounds.json`. Every rate carries n, an interval, and the cells excluded
from its denominator. A finding that is not independently re-derived is a **candidate**, not a
result, and is labelled as one wherever it appears.
