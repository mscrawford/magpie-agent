# Compute-burst continuation checkpoint — 2026-06-07

## NEXT-SESSION TRIGGER PROMPT (paste into a fresh session to resume)

```
You are the magpie-agent. Resume the deferred NEXT STAGE of the 2026-06-07 audit burst.
FIRST read audit/burst_2026-06-07_continuation.md in full + the BACKLOG "Validator check IDs"
item. Work on branch burst-2026-06-07-audit (already pushed to origin/mscrawford). Before
starting, confirm the 5h usage window has headroom (~/.claude/.statusline-burn + usage-log.csv)
- this stage is moderately heavy. Then do, committing + pushing value-first after EACH step so
a cap can't lose progress:

1. CLUSTER A - harden the validator self-test harness (R9 C4-1..7, corroborated by R10 C1-1).
   The 5 still-untested checks: 15 (check_gams_equations.py), 16 (check_gams_realizations.py),
   25 (check_no_bare_cites.py) [gating] + 20 (check_param_defaults.py), 24 (check_renames.py)
   [advisory]. (23/26 were retired in Cluster B.)
   a. selftest_validator.sh: require a "SELFTEST_OK <name>" stdout sentinel per per-check
      control, NOT exit-0 (so a check that ignores --self-test can't mint a false pass).
   b. each check_*.py main(): exit 2 on an unimplemented --self-test.
   c. add REAL --self-tests to 15/16/25 first, then 20/24: factor each check's detection into a
      fixture-accepting function per the check_default_realizations.py convention (tempdir
      fixture, positive + clean control, print SELFTEST_OK on pass). Synthesize the known bug
      FIRST; assert the check flags it (exit 1 + denominator > 0; treat 0/0 as FAIL).
   d. register in SELFTEST_SCRIPTS only AFTER a real test exists.
   e. neuter-test each: break the check's regex, confirm its --self-test now FAILS, then restore.
   f. run scripts/selftest_validator.sh (PASS) + scripts/validate_consistency.sh (0 errors);
      redeploy AGENT.md if touched (cp to ../AGENT.md + ../CLAUDE.md). Commit + push.
2. C2-1 - delete the advisory-only branch check_gams_citations_impl.py:702-710 (mis-bins
   placeholder/wildcard full-path cites as "bare"; NOT a Check-25 merge - the lens's merge
   framing was rejected by verify). Confirm no external consumer; run the gate; commit + push.
3. Update this continuation file + BACKLOG; record a pipeline-audit re-measure round if warranted.

Rules: push ONLY to origin (mscrawford fork) - NEVER pik-piam. A vacuously-passing self-test is
worse than none (neuter-test each). Leave the NOT-actionable items (R9 C3-3/C3-4/C6-5; R10
C2-2/3/4/C5-5/6) - BACKLOG notes only.
```

---

## UPDATE 2026-06-07 (third window) — Cluster A DONE; C2-1 NOT actionable as written

Worked on branch `burst-2026-06-07-audit` (origin/mscrawford). Value-first: committed + **pushed** after each step. Gate PASS (39 checks, 0 errors) and selftest PASS (14/14 controls) at every commit.

**CLUSTER A — COMPLETE (3 commits, all pushed).**
- `3b1c722` **(a) harness leverage fix**: `selftest_validator.sh` now requires each per-check control to print `SELFTEST_OK <name>` as its OWN exact line (`grep -qx`, anchored — a flawed neuter-test surfaced that a plain `grep -q` lets `SELFTEST_OK foo` match a substring of `SELFTEST_OK foo_bar`; fixed). Exit-0-without-sentinel is now a FAIL. Added the sentinel to all 9 already-registered self-tests. Negative path proven (neutered one sentinel → harness correctly FAILed).
- `58e515e` **(c) 3 gating checks**: real synthesize-bug-first `--self-test`s for **15** `check_gams_equations` (factored `build_equation_index(modules_root)` + `find_doc_eq_mismatches`), **16** `check_gams_realizations` (factored the index builders + `find_realization_issues`; fixture cites `fabricated_jan99`), **25** `check_no_bare_cites` (drove existing `scan_doc`). Registered (item d). Neuter-tested each (broke the detector regex → self-test FAILed → restored). Normal-mode output unchanged (153/153 eqns, 0 bare cites, advisory cross-module list).
- `8f031b5` **(c) 2 advisory checks**: **20** `check_param_defaults` (drove `scan_doc` with an injected `defaults_map`), **24** `check_renames` (factored `find_rename_hits_in_text` out of the `os.walk` loop; hoisted `ALLOWLIST_LINE_RE` to module scope; dropped the already-dead local `ITALIC_HISTORICAL_RE`). Registered. Neuter-tested each. Normal-mode unchanged (64 claims/0 mismatches; 3 renames/0 refs).
- **All 14 registered check_*.py now have a neuter-tested positive control.**

**Item (b) "main() exit 2 on UNIMPLEMENTED --self-test" — satisfied by construction (reasoned deviation from the literal stubs).** After Cluster A, every check_*.py implements `--self-test`, so none can masquerade. The argparse-based checks already exit 2 on an unrecognized flag for free; the `sys.argv`-based ones now have real handlers. The harness sentinel (a) is the enforcement layer for any FUTURE registered check that forgets one. I did NOT add dead exit-2 stubs to 14 already-implemented files (they'd be unreachable). The harness comment documents the "implement a real --self-test before registering" contract.

**C2-1 — NOT ACTIONABLE AS WRITTEN (the deletion is a regression; verify's safety claim CORRECTED).** Empirically tested: deleting the `if mod_num is None:` BARE branch in `check_gams_citations_impl.py` (now ~:705-713) drives the gate **PASS → FAIL** (`errors=1, verdict=FAIL`; Check-17 reports `❌ ... 11 problems`, e.g. `FILE: nlp_apr17/solve.gms:103 (in Infeasibility_Debugging_Guide.md) — bare hint ... module None_*`). Root cause: the branch's `continue` is **load-bearing** — it keeps non-module-doc pedagogical/placeholder cites in the advisory `ambig` bucket. Deleting it lets them fall through to `file_missing` (`issues = file_missing + line_over; if issues>0: sys.exit(1)` at impl:1012-1029) → the validate_consistency.sh Check-17 harness (which only treats exit-0 as pass) goes red. The R10 `pipeline_round10_verify/C2-1.md` "deletion is mechanically safe" conclusion **missed the continue's flow-control role** (it reasoned "ambig isn't gated → safe"). REVERTED; nothing committed for C2-1. The branch's only genuine defect is a cosmetic MISLABEL ("bare-basename" for placeholder/wildcard full-paths the regex can't parse) — advisory-only and **gate-suppressed**, so near-zero impact. Future options (user decision): (a) relabel the advisory string only (safe, cosmetic); (b) narrow `CITATION_RE`/FILE-branch to recognize `modules/XX_.../` and `modules/NN/*/` placeholders; (c) won't-fix. Recommend (c) or (a) — the finding was already CORRECTED (impact overstated).

**Pipeline-audit re-measure — NOT run.** Not warranted now: Cluster A is directly verifiable (14/14 sentineled controls), and C2-1 is resolved as not-actionable. A fresh ~10-agent workflow is premature and was not an explicit opt-in; left for the user to trigger if they want confirmation.

**STILL untouched** (BACKLOG notes only): R9 C3-3/C3-4/C6-5; R10 C2-2/3/4 + C5-5/6; the stable-check-ID refactor ("Validator check IDs" in BACKLOG).

---

Deferred to the next usage window (session cap). The working tree is **gate-clean**
(`validate_consistency.sh`: 43 checks, 0 errors, PASS) and contains no half-applied
machinery — a safe deferral point. Nothing is committed or pushed. Branch: `main`
(→ branch first before committing).

This burst was the "lens-audit vs flywheels + would-a-workflow-help" investigation.
Outcome: did BOTH (targeted flywheels on the still-drifting integrative docs, AND
built the pipeline-audit as a reusable Workflow-tool script) — they are complementary,
each caught a different bug class.

---

## UPDATE 2026-06-07 (second window)

Progressed and committed (branch, no push):
- All 6 R9 **coherence/drift fixes APPLIED + gate-clean**: C6-1 (CRITICAL `flywheel_rubric.md:30` fbask anchor inverted -> corrected + rubric **v1.2 -> v2.0** bump), C6-2 (`AGENT.md:436` "schema v1.3" de-hardcoded + redeployed), C6-3 (`flywheel_rubric.md` "14 classes" -> 15 at :234/:262), C6-4 (`verifiers.md:13` lessons-count 0 -> 3), C3-1 (`modules/README.md:34` live-count phrasing), C3-2 (`README.md:7` round-count deferred to the ledger).
- **R49 + R50 recorded** to `validation_rounds.json` (now 50 rounds); **R9 recorded** to `pipeline_audit_rounds.json` (now 9). Record script: `audit/archive/rounds/burst_record_R49_R50_R9.py`.
- Round-901 smoke artifacts deleted (C6-3 fixed; superseded by R9).

**C1/C2/C5 pipeline-audit (round 10): DONE + recorded** (pipeline_audit_rounds.json now 10). It corroborated Cluster A (C1-1) and made the R7 zero-catch retirements actionable. Findings: `audit/archive/rounds/pipeline_audit_round10_findings.md`.

**STILL PENDING (next window) — recommended sequence (R10 set the order):**

> UPDATE 2026-06-07 (later): **Cluster B is DONE via tombstone.** Lifetime grep confirmed zero catches (Check 4 can-never-fire; 23/26 advisory FP floors, all output allowlisted, no recorded real catch). Full removal was deferred because deleting middle sections renumbers everything after + breaks the hundreds of by-number "Check N" refs across live docs AND the immutable audit history (no mechanical check links a doc "Check N" to its validator section, so renumber errors can't be auto-caught). Done instead: deleted `check_units.py` + `check_multi_section_consistency.py` (~530 LOC) + 3 allowlist entries; stubbed the 3 gate sections (numbering kept at 28); repointed 2 helper refs (incl. fixing a pre-existing Check-23→Check-10 bug in session_cleanup.md). Gate PASS (warnings 4→2), selftest PASS. Proper removal = the stable-check-ID refactor flagged in BACKLOG "Validator check IDs". **Remaining: step 2 (Cluster A — scope now 5, not 7) + step 3 (C2-1).**
1. **Cluster B retirements FIRST** (R10 C5-1/3/4; already R7-approved per BACKLOG.md:45, just never applied). One bundled removal sweep: delete Check 4 (`validate_consistency.sh:309-332`, all-`check_pass` → can never fail); delete Check 23 (`:947-966`) + `check_multi_section_consistency.py` (253 LOC) + its 3 allowlist entries; delete Check 26 (`:1025-1041`) + `check_units.py` (277 LOC); decrement `SECTION_TOTAL`; repoint `maintenance_protocol.md:37` + `session_cleanup.md:71`. Do this FIRST — it drops 2 of the 7 untested checks, shrinking Cluster A's scope 7→5.
2. **Cluster A harness hardening** (R9 C4-1..7, corroborated by R10 C1-1): `SELFTEST_OK <name>` sentinel in `selftest_validator.sh` + exit-2 on unimplemented `--self-test` + synthesize-bug-first `--self-test`s for the gating checks (factor each detection into a fixture-accepting function, per the `check_default_realizations.py` convention). Risky per-check surgery; do it unhurried. Full plan in §"PENDING" item 1 below (scope now 5 checks after step 1).
3. **C2-1**: delete the advisory-only branch `check_gams_citations_impl.py:702-710` (mis-bins placeholder/wildcard cites as "bare"; NOT a Check-25 merge — the lens's merge framing was rejected by verify). Independent of A/B.
- **NOT actionable** (UNVERIFIED or load-bearing on inspection — BACKLOG notes only): R9 C3-3/C3-4/C6-5; R10 C2-2/3/4 + C5-5/6 (e.g. `verifiers.md` MANDATE 9 is the sole human-review guard for the R3 bug — do not demote/renumber).

---

## DONE this burst (applied, uncommitted, validator-clean)

**Flywheel R49** — cross_module integrative docs (mean 8.63; anchors G1=9, G3=10, no drift; verify 0 refuted/6 upheld; gate clean).
- Fixes applied (7 edits, 4 files): `nitrogen_food_balance.md` (1), `circular_dependency_resolution.md` (2), `modification_safety_guide.md` (2), `carbon_balance_conservation.md` (2).
- Artifacts: `audit/archive/rounds/round49_{docaudits,answers,audits,verify}/`.
- Surfaced 4 cross-doc bugs it could not auto-fix (single-doc fixer); 3 handled below.

**AGENT.md self-bug** — FIXED + redeployed + validator PASS. The Step-1c snippet `ls -d ${m}*/` counted each module's `input/` dir as a realization → "~40 of 46"; true is **22 of 46** (verified two ways: dirs-excl-input AND `module.gms` `$include` count). Fixed snippet (`grep -v '/input/$'`) + comment; redeployed to `../AGENT.md` + `../CLAUDE.md`.

**Flywheel R50** — module_56 emissions cluster + 2 core docs (mean 8.14; anchors G2=10, G4=10, no drift; verify 0 refuted/3 corrected/8 upheld; gate clean). NOTE: hit the cap mid-run; completed via resume (see resume lesson below).
- Fixes applied (23 edits, 5 files): `module_56.md` (17 — incl. the R49-deferred M57-as-`vm_emissions_reg`-producer relabel: M57 only READS it; real populators = {51,52,53,58}), `module_55.md` (1: `sm_fix_SSP2` 2015→2025), `module_51.md` (2), `Data_Flow.md` (2), `Query_Patterns_Reference.md` (1).
- Artifacts: `audit/archive/rounds/round50_{docaudits,answers,audits,verify}/`.

**NEW reusable infra** — `audit/tools/pipeline_audit_round.workflow.js`: the pipeline-audit as a Workflow-tool script (modeled on `doc_audit_round.workflow.js`). N decorrelated lens agents → light cross-lens dedup → per-finding adversarial verify (defects reproduced; removals refuted via live-dependent search) → synthesis clusters survivors by root cause. READ-ONLY (no auto-fix, no rounds-log mutation; returns `round_log_ready`). Presets: `consolidation` (C1–C6), `standard` (6-lens doc↔code); `args.lensKeys` subsets a preset. Validated: ESM-as-async-fn parse + smoke (round 901) + R9.

**Pipeline-audit R9** — C3/C4/C6 triad via the new workflow (1 CRIT, 4 HIGH, 7 MED, 3 LOW; verify 0 refuted / 1 corrected / 11 upheld). READ-ONLY → **nothing applied**. Full report: `audit/archive/rounds/pipeline_audit_round9_findings.md`. Round-901 smoke artifacts retained on disk (they hold finding C6-3 "14 classes→15", which R9 did not re-surface).

---

## PENDING (user-approved 2026-06-07, execute in this order)

### 1. R9 fixes — "Implement Cluster A + safe fixes"

**Cluster A (HIGH — false-GREEN validator harness).** A `check_*.py` with no real `--self-test` ignores the flag, runs normally, exits 0; `selftest_validator.sh` (loop at :100-108, trusts exit-0) then mints a FALSE positive control; gating checks 15/16/25 go GREEN on a 0/0 denominator if their regex silently breaks. CI blocks on this guard health → amplifies the false assurance.
- (a) **Harden `scripts/selftest_validator.sh` FIRST** (the leverage fix — closes all 6 holes at once): require each per-check control to print a `SELFTEST_OK <name>` sentinel on stdout (grep for it), NOT just exit 0.
- (b) Make every `scripts/check_*.py` `main()` treat `--self-test` as a HARD ERROR (exit 2) when unimplemented, so a check can no longer masquerade.
- (c) Add REAL `--self-test` branches (synthesize a known bug FIRST, assert the check flags it: exit 1 + denominator>0; treat 0/0 as FAIL; print `SELFTEST_OK <name>`) to gating checks: **15** `check_gams_equations.py`, **16** `check_gams_realizations.py` (REAL_RE :26-28; fixture = a `module_NN.md` citing a fabricated `xxx_jan99` realization → expect exit 1, fabricated>0), **25** `check_no_bare_cites.py`. Then advisory **20** `check_param_defaults.py`, **24** `check_renames.py` (and 23 `check_multi_section_consistency.py`, 26 `check_units.py`).
- (d) Register each in `selftest_validator.sh` SELFTEST_SCRIPTS (:97-99) ONLY AFTER its real self-test exists (registering first would mint a false control — finding C4-4).
- Verify: `bash scripts/selftest_validator.sh` (expect PASS) + neuter-test one new self-test (break the regex, confirm its `--self-test` now FAILS) per the "synthesize-known-bug-test-first" rule.

**Safe coherence/drift fixes** (all independently verified this session):
- **C6-1 (CRITICAL)** `audit/flywheel_rubric.md:30` — anchor has the fbask realization INVERTED. Reword to keep the cascading-wrong-realization lesson with correct facts: the agent invoked `fbask_jul23` (a non-existent/non-default realization) when the default IS `fbask_jan16` (only `fbask_jan16` + `fbask_jan16_sticky` exist). Per rubric §1, fixing an "immutable" anchor REQUIRES a major version bump → bump the rubric header v1.2→v2.0 + add a changelog line.
- **C6-2 (MED)** `AGENT.md:436` "schema v1.3" → v1.4 (and G3/G4 were added at v1.2, not v1.3). Redeploy both copies after.
- **C6-3 (MED)** `audit/flywheel_rubric.md:233` and `:262` "14 classes" → "15 classes" (the §3 table already has 15; class 15 added v1.2).
- **C6-4 (MED)** `agent/helpers/verifiers.md:13` "Lessons count: 0 entries" → actual body count (3). (README.md:84 says the agent scans when count>0, so 0 is functionally wrong.)
- **C3-1 (MED)** `modules/README.md:34` "40 checks" → copy the already-fixed phrasing at `README.md:109` ("the summary prints the live check count"); do NOT re-hardcode 43.
- **C3-2 (MED)** `README.md:7` "matured to 47 rounds" → defer to `audit/validation_rounds.json` (don't hardcode; mirror how AGENT.md defers totals to cumulative_stats).
- **NOT actionable** (per R9 synthesis): C3-3 (CHANGELOG frozen snapshot), C3-4 (UNVERIFIED magpie4-pin triplication — re-verify before any edit), C6-5 (UNVERIFIED rubric:120 cross-ref mapping).
- After fixes: `bash scripts/validate_consistency.sh` (expect 0 errors) and redeploy AGENT.md if C6-2 touched it.

### 2. Record rounds to the ledgers
- **R49 + R50** → `audit/validation_rounds.json` (schema v1.4). Template: `audit/archive/rounds/round48_record.py`. Use the per-round stats captured above + the per-doc detail in `round49_audits/` and `round50_audits/`. (The compact task-output JSONs were in /tmp and are gone — rebuild from the archive dirs + this file's summaries.)
- **R9** → `audit/pipeline_audit_rounds.json` as round 9 (C3/C4/C6 subset; mirror R8's entry shape). The `round_log_ready` object is reproduced in `pipeline_audit_round9_findings.md`; stamp `date:"2026-06-07"` + `commit` at record time.

### 3. Commit (NO push)
- `git -C magpie-agent` is on `main` → **branch first** (e.g. `burst-2026-06-07-audit`). Commit: the 10 doc fixes, AGENT.md (+ redeployed copies are in the PARENT repo, commit separately/appropriately), the new workflow script, the round archive dirs, the ledger updates. End message with the Co-Authored-By line. Do NOT push (user rule: only mscrawford forks, and only when asked).
- Then delete the round-901 smoke artifacts (`pipeline_audit_round901_findings.md`, `pipeline_round901_{lenses,verify}/`) once C6-3 is fixed (their only unique value).

### 4. Run the remaining consolidation lenses — pipeline-audit round 10
- `Workflow({scriptPath:"audit/tools/pipeline_audit_round.workflow.js", args:{round:10, preset:"consolidation", lensKeys:["C1-dead","C2-redundant","C5-overcomplexity"], verify:true}})`. Then record R10, present findings (read-only — user-reviewed fixes), and fold into the commit.

---

## Lessons from this burst (save at session-close)
- **Workflow resume + arg-driven scripts**: `resumeFromRunId` does NOT replay the `args` input — the journal caches agent *results* keyed by prompt, but `args` is `undefined` on resume unless you RE-PASS it. A bare resume of an arg-driven script is a no-op (DOCS=[]). Always re-pass identical args on resume. (Cost me one wasted no-op resume; the re-resume with args completed but effectively re-ran ~all agents — the no-op likely perturbed the journal.)
- **Don't stack workflows on the Mac**: two ~10-agent fan-outs oversubscribe the cores and crawl; sequence them.
- **Cap-resilience**: a heavy round (~30 agents / ~2M tokens) can exhaust the window mid-run. Sequence value-first (apply→gate→record→COMMIT before launching the next cap-risky run) so a mid-run cap never loses committed work.
- **The integrative corpus (cross_module + core_docs) still drifts** even at 0 code-drift; the 46-module corpus is converged. Targeted flywheels there + periodic C-lens coherence audits are the live maintenance surfaces (doc↔code lenses are saturated).
