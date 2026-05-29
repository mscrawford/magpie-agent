# Pipeline Audit Round 7 — Design: CONSOLIDATION

**Date**: 2026-05-29
**Type**: consolidation audit (per-round override of the default doc<->code 6-lens)
**Auditor**: claude-opus-4-8 (1M context); 6 find + 7 verify subagents via a custom Workflow
**Report**: `pipeline_audit_round7.md` (this directory)

## Why this round overrides the default lens set

R1-R5 ran the canonical doc<->code-fidelity 6-lens; R6 ran a 7-lens doc-surface-drift
set. **Every one of those rounds FOUND doc bugs and then ADDED a validator.** The
motivating observation for R7 (end of the 2026-05-29 flywheel-hardening session): the
agent accretes machinery (validators, MANDATEs, ledgers, markers) FASTER than it verifies
the existing machinery still works -- confirmed when `probe_dedup_check.py` was found to
have been a multi-round no-op, the aggregate-count markers had drifted ~3 rounds with
nothing checking them, and two validator parsers false-positived on a normal cross-module
citation. So R7 inverts the reflex: it audits the agent's OWN machinery for CONSOLIDATION
(delete / merge / simplify), with a standing bias AGAINST adding surface area.
(Framing memories: `feedback_test_the_testers`, `template_multi_agent_audit`,
`feedback_synthetic_interventions`, `feedback_blast_radius_before_infrastructure`.)

## The 6 consolidation lenses

| # | Lens (failure class) | Method (decorrelation axis) | Ground-truth anchor |
|---|---|---|---|
| C1 | DEAD / no-op machinery | static liveness trace (follow each artifact's invocation path; prove LIVE or DEAD) | probe_dedup was a no-op |
| C2 | REDUNDANT / overlapping (-> merge) | static cross-comparison: {validator/MANDATE/command -> property} matrices | 3 realization validators |
| C3 | DRIFT (vertical) | derived-value-vs-source: enumerate generated values, name the enforcing check or its absence | count markers drifted unchecked |
| C4 | UNTESTED testers | self-test/positive-control census | a self-test caught a regex bug this session |
| C5 | OVER-COMPLEXITY (cost > catch rate) | EMPIRICAL: run the gate, measure time + noise, cross-ref lifetime real catches | ~874 advisory noise lines |
| C6 | COHERENCE (horizontal) | cross-surface agreement: do AGENT.md/rubric/commands/schema/ledgers state the same value? | R6 schema v1.1-vs-v1.2 drift |

## Decorrelation engineering (per `template_multi_agent_audit`)

- **The `scripts/` hot spot is TRIPLED** with three distinct methods: C1 (static liveness)
  || C2 (static redundancy) || C5 (empirical run). Read-and-reason vs run-and-measure fail
  differently, so together they catch more.
- **C3 vs C6 split on axis**: C3 is vertical (value vs the source it derives from -- "is
  there a check?"); C6 is horizontal (surface vs surface -- "do they agree right now?").
  Overlap on counts is intentional -> corroboration signal.
- **C4** is the clean meta-lens (positive-control coverage).
- **Standing bias** baked into every prompt: the default action is DELETE/MERGE/SIMPLIFY;
  any finding that ADDS machinery must justify why consolidation cannot achieve the same.
- **Blast-radius discipline**: every removal/merge finding carries `what_it_protects` +
  `who_else_needs_it` + `blast_radius`.
- **Stage 2 = adversarial removal-safety verify**: removal/merge candidates were deduped
  by artifact across lenses, then each was handed to a fresh skeptic agent prompted to
  REFUTE the removal (find any live dependent). Default verdict if any live dependent
  found: `refuted_still_needed`.

## Why a custom Workflow (not the `/pipeline-audit` command default)

The command's default is the doc<->code 6-lens; this round needed a bespoke consolidation
lens set + a find->verify pipeline + the blast-radius schema fields. Recorded here as the
per-round override the command's "Per-round overrides" clause sanctions (R6 precedent).
