# C4 — UNTESTED testers (positive-control census)

**Lens key:** C4-untested-testers
**Failure class hunted:** a `check_*.py/.sh` or `validate_consistency.sh` check with no positive control proving it still catches its target bug class — especially freshly-changed or brand-new testers.
**Ground-truth precedent:** a self-test once caught a regex bug; the `d6e7376` `set -e` bug silently killed `validate_consistency.sh` at check 1 while commit messages recorded "NN/NN clean".
**Mode:** READ-ONLY. No repo files edited. All temp files created under `mktemp`/in-place twins were removed; verified.

---

## Method

1. Censused every `scripts/check_*.{py,sh}` and every numbered check in `validate_consistency.sh`.
2. For each, determined: (a) is it **invoked by the live validator** (load-bearing)? (b) does it **gate** (`check_error` → false-GREEN risk) or is it **advisory** (`check_warning` → signal-loss only)? (c) does a **positive control** exist — a `--self-test` branch that injects the target bug and asserts it is caught, AND is it **registered** in `selftest_validator.sh`'s `SELFTEST_SCRIPTS` array (the only place controls are actually run, incl. in CI)?
3. Proved each gap with a neutering demonstration (regex-bug analogue) where feasible.

---

## Census matrix

| Check | Script | Gates? | `--self-test` branch | In `SELFTEST_SCRIPTS` | Controlled? |
|---|---|---|---|---|---|
| 14 | `check_gams_variables.py` | error (gate) | yes | yes | ✓ |
| **15** | **`check_gams_equations.py`** | **error (gate)** | **NO** | **NO** | **✗** |
| **16** | **`check_gams_realizations.py`** | **error (gate; fabricated-only)** | **NO** | **NO** | **✗** |
| 17 | `check_gams_citations.sh` → `check_gams_citations_impl.py` | error (gate) | yes (impl) | yes (impl) | ✓ |
| 18 | `check_default_realizations.py` | error (gate) | yes | yes | ✓ |
| 19 | `check_module_realizations.py` | error (gate) | yes | yes | ✓ |
| **20** | **`check_param_defaults.py`** | warning (advisory) | **NO** | **NO** | **✗** |
| 21 | `check_doc_var_existence.py` | warning | yes | yes | ✓ |
| 22 | `check_consumer_attribution.py` | warning | yes | yes | ✓ |
| **23** | **`check_multi_section_consistency.py`** | warning (advisory) | **NO** | **NO** | **✗** |
| **24** | **`check_renames.py`** | warning (advisory) | **NO** | **NO** | **✗** |
| **25** | **`check_no_bare_cites.py`** | **error (gate)** | **NO** | **NO** | **✗** |
| **26** | **`check_units.py`** | warning (advisory) | **NO** | **NO** | **✗** |
| 27 | `check_hedged_claims.py` | warning | yes | yes | ✓ |
| 28 | `check_scaling.py` | warning | yes | yes | ✓ |
| — | `probe_dedup_check.py` (pipeline-audit tool, not a validator check) | n/a | yes | yes | ✓ |

`migrate_bare_cites.py` is a one-shot migration tool (referenced only in a Check-25 comment, not invoked as a check) — correctly excluded.

**Self-test suite currently PASSES** (ran `bash scripts/selftest_validator.sh` → `SELFTEST_RESULT: PASS`, all 9 registered controls `ok`, both structural safety-nets fire). CI (`.github/workflows/validate.yml:64-65`) runs it as "always blocking". So the 9 registered controls ARE healthy and exercised. The gap is the **6 unregistered checks**.

---

## What the existing guards do and do NOT catch

`validate_consistency.sh` has two structural safety-nets (both proven firing by selftest sub-tests 3 & 5):
- early death → `trap on_exit EXIT` → exit 99 (`validate_consistency.sh:25,42`)
- silently-skipped **section** → `SECTION_NUM != SECTION_TOTAL` → ABORTED (`validate_consistency.sh:1120-1126`)

Neither guards per-check **detection capability**. A check that RUNS to completion but has silently lost its ability to detect (e.g., its detection regex breaks and matches nothing → reports `100% (0/0)` → exit 0 → `check_pass`) sails through every structural guard. The ONLY thing that catches that class is a per-check positive control. There is no denominator-sanity guard in the validator (grep for `0/0|denominator|nonzero` in `validate_consistency.sh` → only a comment at line 104).

---

## FINDINGS

### C4-1 — Gating Check 15 `check_gams_equations.py` has no positive control (regex-bug → silent false GREEN)
**Severity: HIGH. Kind: untested.**
`check_gams_equations.py` gates the validator (`validate_consistency.sh:754` `check_error` on mismatch) but has no `--self-test` branch and is not in `SELFTEST_SCRIPTS`. Its detection depends on `DOC_EQ_RE` (`check_gams_equations.py:26`) and `GAMS_EQ_RE` (line 25) — two separate regexes. If either silently stops matching (the exact precedent class — "a self-test caught a regex bug"), the check reports `Accuracy: 100% (0/0 unique equations)` and exits 0 → `check_pass`. The `(0/0)` tell is never asserted on.

**Proof (neutering demonstration, in-place twin, removed after):** broke `DOC_EQ_RE` so it matches nothing, ran against the real MAgPIE tree:
```
=== REAL check_gams_equations.py --summary-only (baseline) ===
Equation names verified: Accuracy: 100% (153/153 unique equations)   exit=0
=== NEUTERED twin (DOC_EQ_RE broken) --summary-only ===
Equation names verified: Accuracy: 100% (0/0 unique equations)        exit=0   <- FALSE GREEN
=== NEUTERED twin --self-test ===
Equation names verified: Accuracy: 100% (0/0 unique equations)        exit=0   <- NO control fires
```
**verify_cmd:** `cd scripts && cp check_gams_equations.py _t.py && python3 - _t.py <<'P'`<br>`import sys;p=sys.argv[1];s=open(p).read();s=s.replace('DOC_EQ_RE = re.compile(r"`+'`'+`(q\\d+_[a-zA-Z_]+[a-zA-Z])\\b")','DOC_EQ_RE = re.compile(r"ZZZ_NEVER")');open(p,'w').write(s)`<br>`P`<br>`python3 _t.py --summary-only; rm -f _t.py`  → prints `100% (0/0)` exit 0.
**Suggested fix:** add a `--self-test` branch that runs the detector over an in-memory fixture containing (a) a valid equation that exists in source and (b) a fabricated `q99_nonexistent` doc ref, asserting exit 1 + the fabricated name surfaces; assert the unique-ref denominator is > 0 on the real corpus (a `(0/0)` result should itself be a failure). Then add `check_gams_equations` to `SELFTEST_SCRIPTS` (`selftest_validator.sh:97`).

### C4-2 — Gating Check 16 `check_gams_realizations.py` has no positive control (regex-bug → silent false GREEN)
**Severity: HIGH. Kind: untested.**
Gates on *fabricated* realization names (`check_gams_realizations.py:158` `return 1`; cross-module drift is advisory). No `--self-test`, not registered. Detection depends on `REAL_RE` (`check_gams_realizations.py:26-28`). If `REAL_RE` breaks → 0 triples → `Accuracy: 100% (0/0 references)` → exit 0 → `check_pass` (`validate_consistency.sh:779`). Same `(N/total)` denominator structure as C4-1; same silent-false-green class.
**Evidence:** `grep -c "self-test" scripts/check_gams_realizations.py` → 0; `python3 scripts/check_gams_realizations.py --self-test` runs the normal check and exits 0 (flag silently swallowed). Code read: lines 96-168 show no self-test branch and the `100% ({verified}/{total})` print at line 160 with no nonzero-denominator assertion.
**verify_cmd:** `cd scripts && python3 check_gams_realizations.py --self-test; echo "exit=$?"`  → runs normal output, `exit=0` (no control).
**Suggested fix:** add `--self-test` asserting a fabricated `module_15.md`-scoped name (e.g. `nosuch_jan99`) → exit 1, and a denominator > 0 sanity check; register in `SELFTEST_SCRIPTS`.

### C4-3 — Gating Check 25 `check_no_bare_cites.py` has no positive control
**Severity: HIGH. Kind: untested.**
Gates the validator (`validate_consistency.sh:1016` `check_error`). No `--self-test`, not registered. Detection depends on `BARE_RE` (`check_no_bare_cites.py:34`) plus the false-positive guard at lines 56 (`"modules/" in before[-40:]`). If `BARE_RE` breaks or the guard over-broadens, every bare cite is silently skipped → `Bare cites found: 0` → `✅` → exit 0. No control would notice.
**Evidence:** `grep -c "self-test" scripts/check_no_bare_cites.py` → 0. Code read lines 45-98: no self-test branch; `return 0` on empty `all_violations` with no proof the scanner can still match.
**verify_cmd:** `cd scripts && grep -c "self-test\|self_test\|selftest" check_no_bare_cites.py`  → `0`.
**Suggested fix:** add `--self-test` that feeds a fixture string `equations.gms:20` (bare) and asserts it is flagged, plus a full-path `modules/15_food/anthro_iso_jun22/equations.gms:20` and asserts it is NOT; register in `SELFTEST_SCRIPTS`.

### C4-4 — `selftest_validator.sh` "ADD new --self-test scripts to this list" is a false-positive-control trap
**Severity: HIGH. Kind: defect.**
`selftest_validator.sh:95` instructs maintainers: "ADD new --self-test scripts to this list." But the 6 uncontrolled checks (C4-1,2,3,5,6,7) **silently accept `--self-test` and exit 0** — they have no flag handler, so the unknown arg is ignored and they run their normal pass over the (currently clean/advisory) corpus, exiting 0. The selftest harness reports `ok` purely on exit code (`selftest_validator.sh:103` `python3 "$s.py" --self-test >/dev/null 2>&1`). Therefore a maintainer who follows the instruction and adds any of these would get a **spurious green `ok`** that asserts the check is "proven capable" when it has zero capability proof — the precise failure this lens hunts, manufactured by the harness's own instruction.
**Proof:**
```
=== check_renames --self-test would report 'ok' (exit 0) despite NO control ===
captured rc=0 (reports ok = FALSE positive control)
```
Same exit-0-on-unknown-flag confirmed for `check_gams_equations`, `check_gams_realizations`, `check_param_defaults`, `check_multi_section_consistency`, `check_units` (all `exit=0` to `--self-test`, all running their normal output).
**verify_cmd:** `cd scripts && python3 check_renames.py --self-test >/dev/null 2>&1; echo "rc=$?"`  → `rc=0`.
**Suggested fix:** make the harness *prove the control exists* before trusting exit 0 — e.g. require each registered script to print a recognizable `SELFTEST_OK <name>` sentinel under `--self-test` and grep for it (exit 0 alone is insufficient). Independently, each `check_*.py` `main()` should treat an unrecognized `--self-test` as a hard error (`exit 2`) when no self-test is implemented, so a no-op cannot masquerade as a passing control.

### C4-5 — Advisory Check 20 `check_param_defaults.py` has no positive control
**Severity: MEDIUM. Kind: untested.**
Advisory (`validate_consistency.sh:867` `check_warning`; "Script always exits 0 (advisory)" comment at line 863). No `--self-test`, not registered. Because it's advisory, a silent break loses signal (Pattern-13 default-value drift goes unflagged) but does NOT produce a false GREEN — hence MEDIUM not HIGH. Still uncontrolled: a regression in its parameter-extraction regex would silently drop from "64 claims scanned" to "0 claims scanned" and the validator would print a benign warning line.
**Evidence:** `grep -c "self-test" scripts/check_param_defaults.py` → 0; `python3 scripts/check_param_defaults.py --self-test` prints `64 claims scanned ... 0 mismatches` exit 0.
**verify_cmd:** `cd scripts && grep -c "self-test\|selftest" check_param_defaults.py`  → `0`.
**Suggested fix:** add `--self-test` injecting a doc claim that disagrees with a known source default and assert it surfaces; register.

### C4-6 — Advisory Check 24 `check_renames.py` has no positive control
**Severity: MEDIUM. Kind: untested.**
Advisory (`validate_consistency.sh:986` `check_warning`). No `--self-test`, not registered. Only 3 renames tracked (`Renames tracked: 3`), so the corpus is thin; a regex break in old-name matching would silently report "0 hits" forever. Signal-loss, not false-green.
**Evidence:** `grep -c "self-test" scripts/check_renames.py` → 0; `python3 scripts/check_renames.py --self-test` → normal output, exit 0.
**verify_cmd:** `cd scripts && grep -c "self-test\|selftest" check_renames.py`  → `0`.
**Suggested fix:** `--self-test` injecting a doc line containing a tracked old name (non-italicized, non-allowlist) and asserting it is flagged; register.

### C4-7 — Advisory Checks 23 & 26 (`check_multi_section_consistency.py`, `check_units.py`) have no positive control
**Severity: MEDIUM. Kind: untested.**
Both advisory (`validate_consistency.sh:959` and `:1037` `check_warning`). Neither has `--self-test`; neither registered. `check_units.py` is the most recently added of the un-controlled set (`e5d4aaa 2026-05-25`) and parses 1302 canonical identifiers — a brittle extraction with no proof it still matches. `check_multi_section_consistency.py` detects arity drift (the M14 `pcm_tau` h→j class). Signal-loss class.
**Evidence:** `grep -c "self-test" scripts/check_units.py` → 0; `grep -c "self-test" scripts/check_multi_section_consistency.py` → 0; both run normally under `--self-test` and exit 0.
**verify_cmd:** `cd scripts && for f in check_units check_multi_section_consistency; do echo -n "$f: "; grep -c "self-test\|selftest" $f.py; done`  → both `0`.
**Suggested fix:** add `--self-test` to each (units: a doc claiming the wrong unit for a known identifier → flagged; multi-section: a fixture doc citing `var(h)` in one section and `var(j)` in another → arity mismatch flagged); register both.

---

## Clean categories (checked, genuinely controlled)

- **Check 14 `check_gams_variables.py`** — `--self-test` present (7 refs), registered, passes in suite.
- **Check 17 `check_gams_citations_impl.py`** (via `.sh` wrapper) — control present, registered, passes. Most-recently-modified tester (`3620958 2026-06-05`) and it IS controlled — good.
- **Checks 18/19 `check_default_realizations.py`, `check_module_realizations.py`** — controls present, registered, pass.
- **Checks 21/22 `check_doc_var_existence.py`, `check_consumer_attribution.py`** — controls present, registered, pass.
- **Checks 27/28 `check_hedged_claims.py`, `check_scaling.py`** — controls present, registered, pass.
- **`probe_dedup_check.py`** — pipeline-audit tool (not a validator check); has `--self-test`, registered, passes.
- **Structural safety-nets** — early-exit (exit 99) and section-count-mismatch (exit 99) both proven firing by selftest sub-tests 3 & 5; CI runs the selftest as always-blocking (`validate.yml:64-65`).

## Net assessment
The self-test machinery is real, healthy, and CI-enforced for the 9 registered scripts — a genuinely strong foundation. The defect is **coverage**: 6 of 15 validator checks have no positive control, and **3 of those gate** (Checks 15, 16, 25), so a regex/extraction regression in any of them ships as a false "100% verified" GREEN that no structural guard catches — the exact precedent class. Compounding it, the harness's own "ADD new scripts to this list" instruction (C4-4) will mint *false* controls because the uncontrolled scripts silently exit 0 on `--self-test`. Fix priority: C4-1, C4-2, C4-3 (close the false-green gates), then C4-4 (stop the harness from trusting bare exit-0), then C4-5/6/7 (advisory signal integrity).
