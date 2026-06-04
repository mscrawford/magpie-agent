# Pipeline Audit Round 8 — Findings (C3 / C4 / C6 targeted machinery-delta)

**Date**: 2026-06-03 | **Commit**: b683388 | **Auditor**: claude-opus-4-8
**Lenses**: C3 (vertical drift), C4 (untested testers), C6 (horizontal coherence) — 3 read-only Opus find-agents + 1 adversarial removal-safety verify.
**Design**: `pipeline_audit_round8_design.md` | **Scope**: machinery delta since R7 (`717cd78`) + R7's deferred follow-up.

**Totals**: 15 findings — 0 CRITICAL, **4 HIGH**, 7 MEDIUM, 4 LOW. Plus 3 verified-clean (no defect): the live freshness/staleness badge, `probe_dedup_ledger.retire_after`, and the f4f44b0 bare-cite default-realization resolution are all exemplary anti-drift designs.

**C6 seed-anchor corrections (the lens refuted part of the orchestrator's prior):** source↔deployed copies are IDENTICAL (Check-10 clean); the session's preproc-path fix is fully applied (1 reference, no stragglers); the "Check N renumbering" worry is a non-issue (AGENT.md's Check refs match the validator; R7 left no dangling pointers); `validator_checks=28`/`sub_checks=43` are internally coherent (26 numbered + 2 advisory sections = 28; 43 = per-call count).

---

## Root-cause clusters (15 findings → 4 interventions)

### I1 — Orphaned snapshot counters (R7 removed the updater, left the data)
**Root**: commit `be17620` ("R7 I3: retire the aggregate-count marker system") deleted `refresh_aggregate_counts.py` (the only writer) + `check_marker_staleness.py` (its gate, Check 27), but left the output fields in `cumulative_stats` — now unmaintained mirrors.

- **[HIGH] 4 stale verified-counts** — `file_line_citations_verified` 2598 vs live **2946**; `gams_variables_verified` 953 vs **1003**; `gams_equations_verified` 139 vs **153**; `gams_realizations_verified` 75 vs **60**. Zero readers (verified adversarially; only the file itself + frozen archive). Corroborated by C3 + C6 + the Stage-2 skeptic. **Fix: DELETE all 4** (unread, already wrong).
- **[MEDIUM] `validator_checks=28`/`validator_sub_checks=43`** — currently correct but unenforced duplicates of the script's live `SECTION_TOTAL`/`TOTAL_CHECKS` and `latest_result.json`. Will drift the instant a check is added (the sync script that kept them current was deleted in R7). **Fix: DELETE both** (live source is `latest_result.json` + the script).
- **[HIGH] `total_bugs_found`/`total_bugs_fixed`** — hand-incremented per round (`+= N`), unreconstructable from the heterogeneous per-round schema + separate `doc_push_*` blocks. **Fix: relabel `approx_*` with a "hand-aggregated; not machine-reconciled" note** (do NOT build a reconciler — disproportionate for a vanity metric).

### I2 — Positive-control coverage hole (testers unbound where history says they break)
**Root**: 78429ca added a real self-test harness, but its clean fixture is an EMPTY tree, so the load-bearing Python checks vacuously pass and are never exercised; new/changed testers shipped without positive controls.

- **[HIGH] `check_gams_citations_impl.py` (Check 17) has no positive control** — f4f44b0 added +69 lines of NEW bare-cite default-realization resolution; this is the single most bug-prone check (71% of historical bugs) and a regression would resurrect the exact false-LINE-error symptom it fixed. **Fix: add `--self-test`** with a synthetic peatland off(18-line)/v2(85-line) tree + a bare cite that must resolve to the default, and a composite-default that must fall through. (Sanctioned C4 additive exception.)
- **[HIGH] `selftest_validator.sh` empty-fixture scope hole** — the clean fixture has no GAMS code / no citations, so Checks 14/15/16/17/18/19/21 all see empty input and vacuously pass; the planted defect only exercises Check 13. **Fix: extend the fixture** with one real `vm_foo` + `default.cfg` + a doc that cites it, and a 4th sub-test planting a fabricated `vm_NOTREAL` (Check 14) + out-of-range cite (Check 17), asserting FAIL.
- **[MEDIUM] Vacuous-pass-on-empty floor** — load-bearing Python checks `return 0` when their denominator is 0 (empty scan = green). A path-constant drift would show clean having verified nothing. **Fix: each check exits non-zero / emits a "NOTHING SCANNED" token when its denominator is 0.**
- **[MEDIUM] `completed=1` proves REACHED, not RAN** — `TOTAL_CHECKS` is a bare running counter with no `EXPECTED_CHECKS`; a silently-skipped section still reaches the verdict and records a pass. The d6e7376 sentinel guards death, not skip. **Fix: assert `TOTAL_CHECKS >= EXPECTED_CHECKS` in the verdict block; selftest sub-test that comments out a block and catches the count drop.**
- **[MEDIUM] R7-deferred self-tests still missing** — Checks 18 (default-realizations), 14 (variables), 21 (doc-var) — all with silent-failure histories (BACKLOG item 2). **Fix: minimal `--self-test` each** (one known-bug fixture).

### I3 — Hardcoded counts on secondary surfaces (should point at source)
**Root**: a count is restated on a 2nd/3rd surface while only the primary gets updated.

- **[MEDIUM] MANDATE count** — `agent/commands/pipeline-audit.md:50` says "17 MANDATEs"; actual is **20** (`grep -cE '^## MANDATE' verifiers.md` = 20; AGENT.md says 20). Live instruction that misleads a future auditor. **Fix: "17"→"20", or drop the literal → "the MANDATEs enumerated in verifiers.md".**
- **[MEDIUM] Stale rubric pointer** — `validation_rounds.json:35` `rubric_version: "1.1"`; `flywheel_rubric.md` is **v1.2**. **Fix: bump to "1.2".**
- **[LOW] `verifiers.md:344`** dated changelog "16 MANDATEs" — historically accurate (line 346 says "now 20"); soft skim hazard. **Fix: add scope marker "(the count at that time; now 20)".**
- **[LOW] Validator internal numbering** — `# Check N:` comments stop at 25; print_section labels go to 26/28 + 2 unnumbered advisory sections. Cosmetic. **Fix: add `# Check 26:` header + number the 2 advisory sections.**

### I4 — Documented-but-unwired control
- **[MEDIUM] `lock_file_sha256` canary** — `version_pins.json` stores it, but the stored-vs-live `renv.lock` comparison is prose-only in `magpie4_reference.md` (agent discretion), never wired into a script. Currently matches. **Fix: wire a ~6-line advisory check (recompute `sha256(../input/renv.lock)`, warn on mismatch), OR explicitly document that enforcement is agent-side.** Lean toward wiring (cheap; removes a diligence dependency).

### Verified-clean / LOW residual
- **[LOW] bare-cite resolution OSError path** — `check_gams_citations_impl.py:139-140` silently falls back to walk-order if `default.cfg` is unreadable. Unrealistic steady state; optional 1-line advisory.
- **[LOW] 7 more checks without self-tests** (equations, realizations, no_bare_cites, param_defaults, renames, + the 2 R7-retire candidates units/multi_section) — defer behind the load-bearing four; add when next touched.

---

## Disposition
Status: **triaged**. Fix phase gated on user review (command §Fix+mechanize). Deletions (I1) verified safe via adversarial Stage-2. The high-value bind is I2 (positive controls — the literal R7-deferred item), which the round's own thesis ("the agent accretes machinery faster than it verifies it") most directly addresses.
