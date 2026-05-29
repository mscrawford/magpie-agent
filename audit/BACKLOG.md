# magpie-agent — Backlog

**Single source of truth for open work.** Completed campaigns and per-round artifacts live in `archive/`. Append-only logs: `validation_rounds.json` (semantic flywheel) and `pipeline_audit_rounds.json` (structural audits). System-wide lessons: `global/agent_lessons.md`.

**Last reconciled**: 2026-05-28 (audit/ consolidation — superseded `next_session_plan.md`, now in `archive/plans/`).

---

## Active

- **Bomb-rate follow-up** — R26 (mean 8.2) and R27 (7.1) ran 2026-05-29 (logged in `validation_rounds.json`), both below the R24 campaign's >= 8.5 target. The re-measure is done; the goal is NOT durably met. Decide whether a further targeted sweep (e.g. M20 + the R27-flagged docs) is warranted, or accept the current mean and close the campaign.

## Validator hardening (open mechanization gaps)

Classes of drift not yet caught prospectively, or checks that fire too loosely. Bias: raise precision of existing checks over adding new ones — syntactic audits are saturated (< 1 bug per angle).

- **Citation-fingerprint sensitivity** (`scripts/check_gams_citations_impl.py`) — in R25 it did not pre-flag 5 adjacent-line citation drifts (too tolerant of similar-content neighbors). Tighten the content-fingerprint match within the search window.
- **`probe_dedup_check.py` append-on-completion** — CLOSED 2026-05-29 (`--append-latest` + a TTY guard + `--self-test` added; Step 5c now appends to `probe_dedup_ledger.json` automatically).
- **`check_consumer_attribution.py` FP-generators** (documented in `archive/plans/pattern_d2_omission_backlog.md`) — (1) long lines with multiple backticked vars cross-attribute consumers; (2) bullet-aggregation cannot bridge `**bold-header**` paragraph breaks; (3) `input.gms` `table` declarations do not register as producer (e.g. `pm_climate_class` / M45).
- **`check_units.py` FP rate** (~40% on first run) — advisory tier. Add a contrastive-phrase filter or unit-token denylist before considering wiring as error.
- **Dead skip-globs in `validate_consistency.sh`** (lines ~381, ~422-425, ~631) — reference pre-consolidation top-level paths (`next_session_plan.md`, `pipeline_audit_round*.md`, `round*_answers/`) now covered by the `audit/archive/*` exclusion. Harmless no-ops; trim the next time the validator is touched. (Left in place during the 2026-05-28 consolidation to keep that change purely structural.)

## Deferred (deliberate — with reactivation gates)

- **Phase 4: PR-time drift prevention** — DEEP SHELF; scaffolds REMOVED in R7 (consolidation: ~1192 LOC unwired, 0 lifetime catches). The three scripts (`pr_doc_impact.py`, `pr_mechanical_update.py`, `pr_semantic_update.py`) are recoverable from git history if the reactivation gate is ever met. Gate: missed-drift cost > CI cost — NOT met (0 doc-relevant GAMS changes in the 7 develop commits since last sync, checked 2026-05-28; the flywheel catches rare drift within a round). Design rationale: `get_under_control_plan.md` §Phase 4.
- **Archive *deletion*** (distinct from the 2026-05-28 archive *move*) — `audit/archive/` legacy /feedback infra (~112KB) + `reference/archive/` (~160KB). Dead weight vs git-history preservation; needs user sign-off. NOTE: the `rounds/` + `plans/` subdirs just moved into `audit/archive/` are intentional history, NOT deletion candidates.
- **AGENT.md F5 trims** (~80 lines) — hoist the Twin-agent disambiguation block + trim COMPLETE DOCUMENTATION STRUCTURE. Revisit if AGENT.md feels large at a future re-measure. Redeploy both parent copies after.
- **Helper-trigger overlap residual** — `realization` fires both `verifiers.md` + `realization_selection.md`; `scenario` substring fires 5 helpers. Each narrowing is a judgment call. (4 broad triggers already tightened in R6 Cluster F.)
- **Bulk bare-basename citation cleanup** — ~760 advisories remain in single-realization modules; mostly noise. Spot-fix only multi-realization modules (13, 17, 21, 38, 44, 53, 56, 70, 80).

## Cross-agent / environment

- **Broken parent renv** — `magpie/renv/library/` is missing ~14 packages, so the *preproc-agent* index cannot rebuild and stays stale. Root-cause it (never-restored vs failed-restore vs toolchain). Key fact: the index build needs *installed* packages, not just cloned sources. Preproc-side blocker, tracked here per user initiative.
- **Port remaining preproc-agent design patterns** — regression-questions-in-flywheel already ported (G1-G4). Survey the rest (index-freshness hard-fail, structured re-verify queues) and judge what is worth porting.

## Won't-fix this cycle (rationale documented)

- Unbacktick'd-prose variable scanner — needs its own heuristic-design pass (~4-6h); lower priority than the backticked coverage already shipped.
- Module 13 internal `vm_tau` deep sweep — spot-checked clean in R2.
- 2 legitimate Pattern-12 FPs — M14 `vm_tau` (doc notes absence), M52 `s32_aff_plantation` (cite-paragraph spans the var, cite line does not).
- `s59_nitrogen_uptake` Pattern-13 advisory — unit-conversion FP (200 kg N/ha doc vs 0.2 tN/ha source); clearly identified, low priority.
- ~25 R3 LOW-severity spot bugs — minor/single-occurrence; do not warrant commits. Enumerated in `archive/rounds/pipeline_audit_round3.md`.

---

## History pointers

| What | Where |
|------|-------|
| Semantic flywheel rounds (R1-R25) | `validation_rounds.json` + `archive/rounds/round*`, `archive/rounds/validation_round22.md` |
| Structural pipeline audits (R1-R6) | `pipeline_audit_rounds.json` + `archive/rounds/pipeline_audit_round*` |
| R24 bomb-rate campaign (Phases 0-3 done) | `get_under_control_plan.md` (kept live at top level for R26) |
| Completed initiative plans | `archive/plans/` (feedback removal, magpie4 scaffolding, R3 execution, Pattern-D2) |
| System-wide lessons | `global/agent_lessons.md` |
