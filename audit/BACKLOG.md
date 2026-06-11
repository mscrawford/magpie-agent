# magpie-agent — Backlog

**Single source of truth for OPEN work.** Completed campaigns and per-round artifacts live in `archive/` and the append-only ledgers (`validation_rounds.json`, `pipeline_audit_rounds.json`). System-wide lessons: `global/agent_lessons.md`.

**Last reconciled**: 2026-06-07 — cleanup pass: cleared finished campaigns (now recorded in the ledgers / `archive/`) and low-EV or accepted items. Per-item rationale is in that commit's message; the pre-cleanup list is in git history.

---

## Open work

- **⏭️ NEXT COMPUTE SESSION — R51 auditor-calibration follow-up** (added 2026-06-11). The R51 round (`archive/rounds/round51_calibration/`, `validation_rounds.json` round 51) measured the flywheel auditor's own FNR and located one real blind spot: cross-module causal/data-flow-DIRECTION claims needing non-local inference (soilc serial-vs-parallel missed twice in long-doc audits). **Primary deliverable:** write the "both-endpoints / default parallel-not-serial" check into `agent/helpers/verifiers.md` as a new MANDATE (the class-B mitigation; runs on Opus). Plus 2 borderline `Module_Dependencies.md` items (:198, :212), an optional tighter class-B find-rate re-run, a gated Fable/Mythos round, and a push decision. **Paste-able continuation prompt + full context:** `archive/rounds/round51_calibration/NEXT_SESSION_PROMPT.md`. Memory: `magpie_agent_auditor_calibration_r51` (method: global `feedback_calibrate_llm_judge_fnr`).

- **Stable check-ID refactor** — give validator checks STABLE IDs (decouple a check's identity from its section position) and add a ref-integrity check linking each doc "Check N" to its validator section (none exists today). **This is the single gate** for (a) fully removing the 3 tombstoned zero-catch checks — Check 4 + `check_multi_section_consistency.py`/Check 23 + `check_units.py`/Check 26, currently stubbed in `validate_consistency.sh` with numbering kept — and (b) dropping the still-droppable inline Checks 1/2/6. Both are blocked because deleting/renumbering middle sections breaks the hundreds of by-number "Check N" references across live docs AND the **immutable audit history** (round designs / findings / `validation_rounds.json` cite checks by their number-at-the-time). Not blocking anything today (the tombstones are inert no-ops); this is a real engineering task, not a quick cleanup. **Gate:** when someone takes it on.

- **Semantic validation is drift-triggered (standing mode, not a task)** — the R1–R50 campaign concluded 2026-06-05 (R43–R50 doc_quality ≥ 9.5, zero surviving Critical/Major *doc* defects; module periphery + non-module corpus covered; all R30 Criticals held). Henceforth run a targeted `/validate-semantic --modules ...` when `/sync` touches module docs (per `agent/commands/validate-semantic.md` "Drift-Triggered Validation"), NOT as a standing campaign.

## Deferred (with reactivation gates)

- **Phase 4: PR-time drift prevention** — DEEP SHELF. The 3 scaffold scripts (`pr_doc_impact.py`, `pr_mechanical_update.py`, `pr_semantic_update.py`) were removed in R7 (~1192 LOC, 0 lifetime catches) and are recoverable from git history. **Gate:** missed-drift cost > CI cost — not met (the drift-triggered flywheel catches rare drift within a round). Rationale: `get_under_control_plan.md` §Phase 4.
- **AGENT.md Twin-agent block hoist** (~1.8 KB) — would add headroom but trades always-loaded misroute-prevention for an on-demand trigger. **Gate:** revisit if AGENT.md re-approaches the 40 KB CLAUDE.md warning threshold (currently ~37.4 KB).

## Cross-agent / environment (not magpie-agent core)

- **Broken parent renv** — `magpie/renv/library/` is missing ~14 packages, so the *preproc-agent* index cannot rebuild and stays stale. Preproc-side blocker, tracked here per user initiative; not actionable from magpie-agent. Root-cause it (never-restored vs failed-restore vs toolchain); the index build needs *installed* packages, not just cloned sources.

## Validator notes (recorded to prevent re-litigation — no action)

- **Known-OK false-positives** (surfaced as advisory, never errors, gate-tolerated): Pattern-12 — M14 `vm_tau` (doc notes its absence), M52 `s32_aff_plantation` (cite-paragraph spans the var, the cited line does not); Pattern-13 — `s59_nitrogen_uptake` (unit-conversion FP, 200 kg N/ha doc vs 0.2 tN/ha source).
- **Accepted advisory volume** — ~760 bare-basename `.gms` citations in single-realization module docs are accepted noise: the citation checker resolves a bare cite to the module's default realization (MANDATE 16), so they are advisory-only and gate-tolerated. Not worth a bulk rewrite.
- **Known low-EV gap (unmechanized):** prose parameter-arity / signature drift — e.g. a doc writing `im_pollutant_prices(t,...)` when the declaration is `(t_all,...)`. Out of `check_gams_citations_impl` scope (not a line-citation issue); would belong in `check_doc_var_existence` as a signature check. Caught one real bug by hand in R50; low frequency, left unmechanized.

---

## History pointers

| What | Where |
|------|-------|
| Semantic flywheel rounds (R1–R50) | `validation_rounds.json` + `archive/rounds/` |
| Structural pipeline audits (R1–R10) | `pipeline_audit_rounds.json` + `archive/rounds/` |
| R24 bomb-rate campaign | `get_under_control_plan.md` |
| Completed initiative plans (feedback removal, magpie4 scaffolding, R3 execution, Pattern-D2, Phase-4 scaffolds) | `archive/plans/` |
| 2026-06-07 work (R49/R50, Cluster A/B, C2-1 relabel, CI ripgrep fix, this cleanup) | git history + `audit/burst_2026-06-07_continuation.md` + the ledgers |
| System-wide lessons | `global/agent_lessons.md` |
