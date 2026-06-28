# magpie-agent — Backlog

**Single source of truth for OPEN work.** Completed campaigns and per-round artifacts live in `archive/` and the append-only ledgers (`validation_rounds.json`, `pipeline_audit_rounds.json`). System-wide lessons: `global/agent_lessons.md`.

**Last reconciled**: 2026-06-07 — cleanup pass: cleared finished campaigns (now recorded in the ledgers / `archive/`) and low-EV or accepted items. Per-item rationale is in that commit's message; the pre-cleanup list is in git history.

---

## Open work

- **R53 plan — mechanize the two R52 bug classes, then sibling-sweep (verifier+MANDATE flywheel; queued 2026-06-28).** R52 (broader carbon/emissions, post-`931db85c4` sync; `validation_rounds.json` round 52) + R51's calibration converge: the residual risk is **COVERAGE, not auditor accuracy.** The two real doc bugs R52 found — module_52 land set inventing `plant_pri`/`plant_sec` (omitting `forestry`); module_59 `s59_nitrogen_uptake` `0.0002`→`0.2` (1000× unit error, self-contradicting its own :627) — had survived ~51 rounds because no probe ever touched those lines. Re-sampling won't close that gap; mechanize the *classes* (template [[template_verifier_mandate_flywheel]]). **Phase 1 (MECHANIZE, test-first per [[synthesize-known-bug-test-for-new-validator]]):** (a) NEW check — doc set-member enumeration drift vs `core/sets.gms` + module `sets.gms`, scoped to closed sets (land, c_pools, ag_pools, pool/land lists); positive control = revert the module_52 plant_pri/plant_sec fix and confirm it flags. (b) HARDEN check 20 / Pattern-13 — flag the SAME scalar cited with DIFFERENT default values within ONE doc (intra-doc contradiction); positive control = module_59 :245-vs-:627 pre-fix. Use intra-doc-contradiction, NOT unit-parsing, to sidestep the known `s59_nitrogen_uptake` unit FP (see Validator notes below). Append as NEW check numbers (no middle-renumber → clears the stable-check-ID gate). **Phase 2 (BIND):** if a class recurs, add a `verifiers.md` MANDATE ("enumerate set members from `sets.gms`, never from prose/memory"); also evaluate the R52 answerer pattern — mechanism over-generalization across pools/realizations (P1-B1: applied ag_pools-init logic to soilc) — as a MANDATE candidate. **Phase 3 (RE-MEASURE / sweep):** run both new checks across all 46 module docs (mechanical, cheap, FULL coverage) and fix the siblings they surface — this is the coverage win vs question-sampling. **Phase 4 (gated):** a small targeted `/validate-semantic` round ONLY on docs the sweep flags heavily, for the non-mechanical (causal/mechanism) siblings the checks can't see. Extends R51's MANDATE-21 verifier work; consistent with "drift-triggered" mode (R52 was the trigger). Effort ≈ half a session for Phase 1 (2 checks + 2 fixtures), cheaper + higher-coverage than another full Q-round. Record: `validation_rounds.json` round 52 + `archive/rounds/round52_*` (design + answers).

- **R51 auditor-calibration follow-up — PRIMARY DELIVERABLE DONE 2026-06-11; residual items below.** The R51 round (`archive/rounds/round51_calibration/`, `validation_rounds.json` round 51) measured the flywheel auditor's own FNR and located one blind spot: cross-module causal/data-flow-DIRECTION claims needing non-local inference (soilc serial-vs-parallel missed twice in long-doc audits). **DONE:** MANDATE 21 (both-endpoints / default parallel-not-serial) written into `agent/helpers/verifiers.md`, mirrored into the `doc_audit_round.workflow.js` GREP_GUARD, count refs bumped to 21 (AGENT.md redeployed, validator PASS). The 2 borderline `Module_Dependencies.md` items (:198, :212) were VERIFIED against code and need NO edit (:212 was a sub-agent false positive — it missed `pm_past_mngmnt_factor`, owned by M70, so the 70->14 dep is real; :198 is defensible as a dependency/influence edge). **(a) DONE 2026-06-11:** tighter class-B find-rate (0/4 unmitigated) + MANDATE-21 VALIDATED via A/B (2/2 inter-module variable-arrow bugs recovered MISSED->CAUGHT with the both-endpoints instruction; abstract-causal subclass still a small residual). 3 real Data_Flow.md input-filename bugs found+fixed. See `archive/rounds/round51_calibration/ITEM3_findrate_and_mitigation.md`. **REMAINING (gated/decision):** (b) a Fable/Mythos round ONLY if the live model is confirmed un-downgraded, pointed at the abstract-causal residual + unknown-unknowns; (c) push decision for the local R51 commits (12aa462..1c3c18f). **Prompt + context:** `archive/rounds/round51_calibration/NEXT_SESSION_PROMPT.md`. Memory: `magpie_agent_auditor_calibration_r51` (method: global `feedback_calibrate_llm_judge_fnr`).

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
