# Pipeline Audit Round 8 — Design: TARGETED MACHINERY-DELTA (C3/C4/C6)

**Date**: 2026-06-03
**Type**: targeted consolidation/coherence audit (per-round override of the default doc↔code 6-lens; subset of R7's consolidation C-set)
**Auditor**: claude-opus-4-8; 3 find lenses + adversarial removal-safety verify, via the Agent tool (orchestrated in the main loop, fixes gated on user review)
**Report**: `pipeline_audit_round8.md` (this directory)

## Why this round, and why these 3 lenses

The behavioral flywheel is saturating (R43 found 0 doc bugs; R41–R42 found 5, 4 in one fixed artifact), so the marginal value has shifted from doc *content* to the *machinery*. The machinery has NOT had a structural pass since R7 (`717cd78`, 2026-05-29), and in that window it churned materially:
- `d6e7376` — a `set -e` + `((VAR++))`-from-0 bug that **silently killed `validate_consistency.sh` at check 1** (the canonical untested-tester failure).
- `78429ca` + `bbd447b` — NEW `selftest_validator.sh` (+96) + tamper-evident execution in `validate_consistency.sh`.
- `2b43eb4` — NEW `check_scaling.py` (+239) + MANDATEs 18–20.
- `f4f44b0` (teammate) — `check_gams_citations_impl.py` rewrite ("resolve bare cites to default realization", +69/-10) + freshness re-anchor to canonical develop.
- This session — `AGENT.md` preproc-path fix; `validation_rounds.json` + ledger appends (and a serialization-fragility near-miss).

Plus R7 **deferred** follow-up still open (BACKLOG): retire low-value Checks 1/2/4/6/23/26; add self-tests for the 3 load-bearing checks with silent-failure histories (Check 17 citations, 18 default-realizations, 14/21 var/doc-var).

User chose a focused 3-lens subset (not the full 6) because R7 just pruned ~1900 LOC five days ago, so re-running the dead-code (C1) / over-complexity (C5) lenses is low-yield now. The live, high-yield failure modes are: a freshly-changed tester (C4), values that derive from a source with no enforcing check (C3), and surfaces that have drifted out of agreement (C6).

## The 3 lenses (subset of R7's C-set)

| # | Lens (failure class) | Axis (decorrelation) | Ground-truth anchor |
|---|---|---|---|
| C3 | DRIFT (vertical) | derived-value-vs-source: enumerate generated/derived values, name the enforcing check or its absence | post-R7: freshness re-anchor; cumulative_stats vs rounds array; SECTION_TOTAL; version_pins vs renv.lock canary |
| C4 | UNTESTED testers | self-test / positive-control census | 16 `check_*` scripts, only 1 self-test; the d6e7376 die-at-check-1 precedent; the f4f44b0 freshly-changed citation checker |
| C6 | COHERENCE (horizontal) | cross-surface agreement: do AGENT.md / verifiers.md / commands / rubric / schema / ledgers state the same value NOW? | MANDATE count drift (AGENT.md 20 / pipeline-audit.md 17 / verifiers.md 16+20); check-count + Check-N numbering post-R7 retirement |

C3 vs C6 split on axis (vertical value-vs-source vs horizontal surface-vs-surface); C4 is the clean meta-lens. Overlap on counts is intentional → corroboration signal.

## Orchestrator-spotted seed anchors (handed to the lenses to VERIFY + EXTEND)
- **C6**: MANDATE count is inconsistent — `AGENT.md`=20, `agent/commands/pipeline-audit.md`=17, `agent/helpers/verifiers.md`= BOTH 16 and 20 (internal). Reconcile against the actual MANDATE count in verifiers.md; find sibling drifts.
- **C4**: 16 `check_*.py/.sh` scripts but only `selftest_validator.sh` exists. Census which checks it positive-controls; the freshly-changed `check_gams_citations_impl.py` (f4f44b0) and new `check_scaling.py` (2b43eb4) are prime "no positive control on changed/new tester" candidates.
- **C3**: `validate_consistency.sh` reports `checks=43`; `cumulative_stats.validator_checks=28`/`validator_sub_checks=43`. After R7 retired Check 27 + renumbered 28→27, the derived counts and the "Check N" references may have drifted with nothing enforcing them.

## Standing bias + blast-radius discipline
Default action = DELETE / MERGE / SIMPLIFY; any finding that ADDS surface area must justify why consolidation cannot achieve the same. **Sanctioned exception**: C4 remediation legitimately adds *self-tests* (the only way to bind a tester's correctness) — but prefer the minimal positive control. Every removal/merge finding carries `what_it_protects` + `who_else_needs_it` + `blast_radius`.

## Stage 2 — adversarial removal-safety verify
Removal/merge candidates deduped by artifact across lenses, then each handed to a fresh skeptic prompted to REFUTE the removal (find any live dependent). Default verdict if any live dependent found: `refuted_still_needed`.

## Fix phase
Reviewed with the user before execution (command §"Fix + mechanize"). Additive/safe coherence fixes may be proposed for batch approval; deletions/merges gated on explicit go.
