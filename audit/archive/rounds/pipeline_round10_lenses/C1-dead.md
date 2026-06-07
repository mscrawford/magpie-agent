# C1 — DEAD / no-op machinery (static liveness trace)

**Lens key:** C1-dead
**Round:** pipeline-audit round 10 (consolidation: C1/C2/C5)
**Failure class hunted:** artifacts (scripts, MANDATEs, ledgers, markers, helpers, allowlists) that are never invoked or never catch anything.
**Method:** static liveness trace. For each artifact, follow its invocation path and PROVE it is LIVE (something calls/reads it) or DEAD (nothing does). Greps cross-checked with a second method + positive controls per the repo's grep-unreliability rule.
**Mode:** READ-ONLY. No repo files edited except this report. The full `validate_consistency.sh` was run (PASS, 43 checks); all probes are read-only.
**Develop checkout:** `/tmp/magpie_develop_ro` @ `ee98739fd` (branch develop), 46 modules — matches the working-tree model.

---

## Headline

The repo's actual dead/no-op machinery is **one cluster, and it is already discovered and tracked**: the no-op `--self-test` flag on 7 validator checks (gating 15/16/25, advisory 20/23/24/26). Pipeline-audit **R9's C4 lens** (`audit/archive/rounds/pipeline_round9_lenses/C4-untested-testers.md`, findings C4-1..C4-7, recorded 2026-06-07) already censused this exhaustively and it is **deferred as "Cluster A"** in `pipeline_audit_rounds.json` + `audit/burst_2026-06-07_continuation.md` §PENDING item 1. I independently reproduced it from the C1-dead axis (no-op artifact view) and add two precisions (CI-amplification; present-tense non-vacuous → the risk is *future* silent death, not a dead-today check). I report it as **ONE confirmed-and-tracked finding** rather than seven novel ones, to avoid double-counting R9.

Everything else I traced is **LIVE**. Notably I formed and then **refuted** a dead-marker hypothesis (allowlist markers outside `modules/`) with a positive control — they are consumed by Check 21. A consolidation audit's worst error is a false "this is dead" call; I caught one before reporting it.

---

## Liveness census (every script + ledger + marker)

### scripts/*.py and *.sh — invocation proof

| Artifact | Invoked by | Verdict |
|---|---|---|
| check_consumer_attribution.py | validate_consistency.sh:920 (Check 22) | LIVE (22 claims scanned, non-vacuous) |
| check_default_realizations.py | Check 18 + selftest SELFTEST_SCRIPTS | LIVE |
| check_doc_var_existence.py | Check 21 + selftest | LIVE (52 docs, 445 refs) |
| check_gams_citations.sh → check_gams_citations_impl.py | Check 17; impl in selftest | LIVE |
| check_gams_equations.py | Check 15 | LIVE but **UNTESTED** (no self-test) |
| check_gams_realizations.py | Check 16 | LIVE but **UNTESTED** |
| check_gams_variables.py | Check 14 + selftest | LIVE |
| check_hedged_claims.py | Check 27 + selftest | LIVE |
| check_module_realizations.py | Check 19 + selftest | LIVE |
| check_multi_section_consistency.py | Check 23 | LIVE but **UNTESTED** |
| check_no_bare_cites.py | Check 25 | LIVE but **UNTESTED** |
| check_param_defaults.py | Check 20 | LIVE but **UNTESTED** |
| check_renames.py | Check 24 | LIVE but **UNTESTED** |
| check_scaling.py | Check 28 + selftest | LIVE |
| check_units.py | Check 26 | LIVE but **UNTESTED** |
| probe_dedup_check.py | validate-semantic.md Step 5c (`--append-latest`); flywheel_rubric §6; selftest | LIVE (real self-test passes) |
| selftest_validator.sh | agent/commands/validate.md:14; CI validate.yml:65 (always-blocking) | LIVE |
| sync_magpie4_clone.py | session_startup.md:55; magpie4_reference.md; bootstrap.md | LIVE |
| migrate_bare_cites.py | NOT invoked by any gate; cited as remediation in check_no_bare_cites.py:94 | ON-DEMAND remediation (spent one-shot, kept as fix tool) — NOT dead |
| audit/tools/viz_validation_coverage.py | NOT a guard; on-demand analysis (produced BACKLOG.md:18 figs) | ON-DEMAND analysis — NOT a guard, "never catches" N/A |
| audit/tools/doc_audit_round.workflow.js, pipeline_audit_round.workflow.js | on-demand Workflow-tool orchestration (this very round) | ON-DEMAND orchestration — NOT a guard |

### ledgers / config / markers

| Artifact | Reader | Verdict |
|---|---|---|
| audit/advisory_allowlist.json (5 entries) | check_param_defaults.py, check_multi_section_consistency.py | LIVE — all 5 entries target a present doc reference (verified `target_present=True` for every entry) |
| audit/renames.json (3 renames) | check_renames.py | LIVE |
| audit/probe_dedup_ledger.json (93 off_limits) | probe_dedup_check.py | LIVE — but see Observation A (currency) |
| `<!-- check-gams-vars: allow … -->` markers in agent/helpers/, reference/, core_docs/, cross_module/ | **check_doc_var_existence.py (Check 21)** SCAN_DIRS :46-51 | LIVE (hypothesis REFUTED — see below) |

---

## FINDING C1-1 — No-op `--self-test` on 7 validator checks → uncontrolled gates (CONFIRMED, already tracked as R9 "Cluster A")

**Severity: HIGH. Kind: untested.** (Reported as ONE finding; R9 split it into C4-1..C4-7.)

**What is no-op:** `check_gams_equations.py`, `check_gams_realizations.py`, `check_no_bare_cites.py`, `check_param_defaults.py`, `check_renames.py`, `check_multi_section_consistency.py`, `check_units.py` each contain **zero** self-test code (`grep -c 'self.test|self_test|selftest'` → 0 for all 7). They parse args by `"--flag" in sys.argv` membership (e.g. check_units.py:234), so `--self-test` is an unrecognized arg that falls through to the **normal scan against the live repo** and exits 0 when the repo is clean. The flag is a no-op: it proves nothing about the check's detection capability.

**Decisive proof the flag does NOT test anything:** two checks emit *non-zero defect counts* under `--self-test` and still exit 0 — i.e. they are plainly just running the normal scan:
```
$ python3 scripts/check_multi_section_consistency.py --self-test   # → "Arity mismatches (likely drift): 2"  exit 0
$ python3 scripts/check_units.py --self-test                       # → "Mismatches: 4 (advisory)"           exit 0
```
A real self-test plants a known bug on a synthetic fixture and asserts detection independent of repo state (cf. the genuine one in `check_default_realizations.py:150-224`, which builds a temp tree and asserts "positive control flagged mismatch").

**Why it matters (the dead-guard mechanism):** 3 of the 7 **gate** the validator (`check_error`): 15 (`validate_consistency.sh:754`), 16 (:782), 25 (:1016). Each prints `Accuracy: NN% (verified/total)`; if the detection regex silently breaks → 0 refs → `100% (0/0)` → exit 0 → `check_pass`. There is no nonzero-denominator guard (`grep '0/0|denominator' validate_consistency.sh` → only a comment at :104). The two structural safety-nets (`trap on_exit` exit 99; section-count-mismatch exit 99) guard *reaching/running a section*, NOT per-check *detection capability*. So a regex regression in 15/16/25 ships as a false "100% verified" GREEN that nothing catches.

**My added precision vs R9:**
1. **Present-tense the checks are NOT dead** — denominators are currently nonzero (Check 15 = 153/153; Check 16 = 60/149; Check 25 = 44 docs scanned, 0 found). The defect is the *absence of a guard against future silent death*, hence `kind: untested`, not a dead-today check.
2. **CI amplification.** `.github/workflows/validate.yml:64-65` runs `selftest_validator.sh` as **always-blocking**. So `selftest_validator.sh:95`'s instruction "ADD new --self-test scripts to this list" is a live foot-gun: adding any of these 7 (which exit 0 on the unknown flag) to `SELFTEST_SCRIPTS` would mint a **CI-enforced false positive control** — actively certifying a guard as healthy with zero capability proof. (This is R9's C4-4, here shown to be CI-amplified.)

**The registered set is sound (no active false control today):** all 9 in `SELFTEST_SCRIPTS` (selftest_validator.sh:97-99) DO plant real bugs (verified `check_default_realizations`/`check_hedged_claims`/`check_scaling`/`check_consumer_attribution` self-tests all assert detection on synthetic fixtures). The harness is healthy for what it covers; the gap is the 7 unregistered/uncontrolled checks.

**verify_cmd:** `for s in check_gams_equations check_gams_realizations check_no_bare_cites check_param_defaults check_renames check_multi_section_consistency check_units; do echo -n "$s: "; grep -c 'self.test\|self_test\|selftest' scripts/$s.py || true; done`  → all `0`.

**Suggested fix (matches the already-approved Cluster A plan; do NOT apply here):** (a) harden `selftest_validator.sh` to require a `SELFTEST_OK <name>` stdout sentinel, not bare exit-0; (b) make every `check_*.py` treat an unimplemented `--self-test` as a hard error (exit 2); (c) add real synthesize-bug-first `--self-test` branches to 15, 16, 25 first (gates), then 20/23/24/26; (d) register each in `SELFTEST_SCRIPTS` ONLY after its real self-test exists. This is CONSOLIDATION-compatible: it adds no new artifact class, it makes the existing harness actually exercise the existing checks. **Status: already deferred as Cluster A; round 10 should fold this confirmation into that work-item, not open a new one.**

---

## Observation A (cross-lens, NOT a standalone C1-dead finding) — probe_dedup_ledger currency lag

`probe_dedup_ledger.json` off_limits tops out at `first_named_round=42` / `retirement_eligible_after=51`, but `validation_rounds.json` is at R50 (2026-06-07). Step 5c `--append-latest` resolves to the latest recorded round, so rounds R43–R50 appear not to have been appended. The `rotation_policy` prose is also stale ("last round is R21, next round R22"; ledger captured_at 2026-06-05). **Why this is NOT a C1-dead finding for me:** the SCRIPT is live and correct (real self-test passes; wired into Step 5c); `append_round_to_ledger` reads `modules_tested` off a `questions` array, and the recent integrative-doc/cross_module rounds may legitimately carry no non-anchor probe-module names → a correct no-op append. The staleness is process-discipline + prose drift (R6 already flagged the rotation_policy prose; pipeline_audit_round6.md:212), squarely **C3-drift** territory, not dead machinery. Flagging for the C3 lens / synthesis, not claiming it here.

---

## Hypothesis I RAISED and REFUTED (recording the negative result, per anti-false-positive discipline)

**Hypothesis:** `<!-- check-gams-vars: allow … -->` markers in files OUTSIDE `modules/` (verifiers.md:107/116/117/266; reference/*.md:3; core_docs/*.md) are DEAD, because `check_gams_variables.py` (Check 14) scans only `DOCS_DIR = AGENT_DIR/"modules"` (line 304) — so markers in non-module files would suppress nothing.

**Refutation (positive control):** `check_doc_var_existence.py` (Check 21) has `SCAN_DIRS` (lines 46-51) = `cross_module, core_docs, agent/helpers, agent/commands, reference`, and imports/reuses the SAME marker parser (`collect_per_doc_allow`). Direct test:
```
$ python3 -c "import sys;sys.path.insert(0,'scripts');import check_doc_var_existence as c;
  print('vm_imagined_xyzzy' in c.collect_per_doc_allow(open('agent/helpers/verifiers.md').read()))"
True
$ python3 scripts/check_doc_var_existence.py   # → "Scopes scanned: cross_module, core_docs, helpers, commands, reference"  (52 docs, 445 refs)
```
The non-module markers ARE consumed — by Check 21, not Check 14. **Hypothesis dead-on-arrival; no finding.** (This is exactly the "X is dead" false-positive the brief warns is the highest risk; the second method + positive control caught it.)

---

## Clean categories (checked, genuinely live — NOT padded)

- **probe_dedup_check.py** — LIVE: wired into validate-semantic Step 5c (`--append-latest`), referenced by flywheel_rubric §6, real self-test plants bugs and passes, in CI selftest. (Was the ground-truth "multi-round no-op" precedent; FIXED 2026-05-29/R27.)
- **The 9 registered self-tests** (`SELFTEST_SCRIPTS`) — LIVE + genuine: each plants a synthetic bug and asserts detection; CI-blocking.
- **selftest_validator.sh structural safety-nets** — LIVE + proven firing: early-exit→99 (sub-test 3), section-count-mismatch→99 (sub-test 5); regression-tested.
- **validate_consistency.sh harness** — LIVE: ran clean (43 checks, 39 passed, 4 advisory warnings, 0 errors, completed=1, verdict=PASS); EXIT trap + completion sentinel + section-count guard all functional.
- **advisory_allowlist.json** — LIVE: 5 entries, all targeting a present doc reference (no dead suppressions); consumed by Check 20 + Check 23.
- **renames.json** — LIVE: consumed by check_renames.py (Check 24).
- **check-gams-vars allow markers (all locations)** — LIVE: modules/ markers via Check 14, all other dirs via Check 21 (refuted hypothesis above).
- **sync_magpie4_clone.py** — LIVE: session_startup + magpie4_reference + bootstrap; `--check` canary wired.
- **migrate_bare_cites.py** — NOT dead: on-demand remediation cited by check_no_bare_cites.py:94 (spent migration retained as the documented fix path). A C2/C5 dedup case exists (its bare-cite regex is duplicated in check_no_bare_cites.py:33), but that is not C1's axis.
- **viz_validation_coverage.py + the 2 workflow.js** — on-demand analysis/orchestration tools, not guards; "never catches" does not apply.
- **The 20 verifiers.md MANDATEs** — auto-loaded binding guidance (loaded on GAMS-identifier triggers); even the human-review-only MANDATEs (1,2,4,5,6,9,10,11,12) are behavior-shaping rules, not no-op guards. Outside the "never invoked / never catches" axis; no dead MANDATE found.

---

## Net assessment

The only genuine dead/no-op machinery is the **7 no-op `--self-test` flags** (C1-1), and it is already discovered (R9 C4-1..C4-7) and deferred (Cluster A). I confirmed it from the C1-dead axis, added the CI-amplification and present-tense-non-vacuous precisions, and **deliberately collapsed it to one tracked finding** so round 10 synthesis does not double-count R9. No other dead artifact exists: every script, ledger, allowlist, and marker traces to a live reader. One plausible "dead marker" lead was refuted by positive control. Standing consolidation bias upheld — the fix for C1-1 deletes/repairs the no-op flag rather than adding machinery.
