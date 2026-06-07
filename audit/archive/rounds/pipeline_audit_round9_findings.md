# Pipeline Audit Round 9 — Findings Report

**Date**: 2026-06-07
**Synthesis model**: claude-opus-4-8
**Lenses run**: C3-drift (derived value vs its source), C4-untested-testers (positive-control census)
**Pipeline**: lens agents -> adversarial verifier -> synthesis (this doc)
**Counts**: raw 16 / deduped 15 / verified 12 / UPHELD 11 / CORRECTED 1 / REFUTED 0

This round was scoped to two failure families rather than the default six lenses:
the **C3 drift** lens (a derived/computed value hand-copied into prose with no
mechanical link back to its source) and the **C4 untested-testers** lens (a census
of the validator's own positive controls — does each gating check actually prove it
still has detection capability?). All findings below were independently reproduced
during synthesis (commands re-run; see per-finding "Synthesis re-check").

**Root-cause summary**: 13 verified findings collapse to **2 interventions** under
**1 shared meta-pattern** — *no mechanical binding between a derived artifact and its
source-of-truth*. Cluster A (the C4 family, 6 findings) is the high-leverage one: a
structural hole that lets a gating check go false-GREEN after losing detection
capability, and a harness that can mint a FAKE positive control. Cluster B (the C3
family, 2 verified findings) is documentation counts drifting from their live source.

---

## CRITICAL / HIGH severity

### Cluster A — "Untested tester": a check with no real self-test silently exits 0

All six C4 findings share **one root mechanism**, verified at synthesis:

> A `check_*.py` that does not implement a `--self-test` branch **ignores the unknown
> flag and runs its normal pass over the (clean) corpus, exiting 0**. For the GATING
> checks that report `Accuracy: 100% (N/total)`, a silent regex break drives
> `total -> 0`, producing `100% (0/0)` and exit 0. There is no nonzero-denominator
> assertion, so a check that has lost all detection capability reports a clean PASS.

Synthesis re-check (verbatim):
```
check_gams_equations  --self-test -> rc=0   (handler: only --summary-only exists; line 48)
check_gams_realizations --self-test -> rc=0
check_no_bare_cites   --self-test -> rc=0
check_param_defaults  --self-test -> rc=0
check_renames         --self-test -> rc=0
check_multi_section_consistency --self-test -> rc=0  (no self_test handler)
check_units           --self-test -> rc=0           (no self_test handler)
```
Ground-truth live validator count (used by C3-1 below): `Total checks: 43`
(`VALIDATOR_RESULT: completed=1 checks=43 passed=39 warnings=4 errors=0 verdict=PASS`).

---

#### C4-4 (HIGH) — the harness mints a FALSE positive control [the keystone]

- **Location**: `scripts/selftest_validator.sh:95` (instruction) + `:100-108` (exit-code-only `ok` check)
- **Failure mode**: The harness instructs "ADD new --self-test scripts to this list",
  but the uncontrolled checks silently accept `--self-test` and exit 0 (no handler ->
  normal pass over clean corpus). The harness reports `pass` on **exit code alone**, so
  adding any of them mints a **false** positive control: it asserts the check is
  proven-capable when it has zero capability proof. CI (`validate.yml`) blocks on this
  guard health, amplifying the false assurance.
- **Evidence / synthesis re-check**: harness logic at `selftest_validator.sh:100-108`:
  ```bash
  elif python3 "$SCRIPT_DIR/$s.py" --self-test >/dev/null 2>&1; then
      pass "$s --self-test"
  ```
  `pass` is asserted on `rc==0` only. The registered set
  (`SELFTEST_SCRIPTS`, lines 97-99) is the 9 scripts
  `check_gams_citations_impl check_default_realizations check_gams_variables
  check_doc_var_existence check_scaling check_consumer_attribution check_hedged_claims
  check_module_realizations probe_dedup_check` — **disjoint** from the 6 uncontrolled
  checks. `validate.yml` contains a `selftest` reference (CI blocks on it). All 6
  uncontrolled checks exit 0 to `--self-test` (table above), so registering any one
  today would print `pass` with zero capability proof.
- **Proposed fix (NOT applied)**: make the harness prove the control exists — require
  each registered script to emit a `SELFTEST_OK <name>` sentinel under `--self-test`
  and grep for it (exit 0 alone insufficient). Independently, each `check_*.py`
  `main()` should treat `--self-test` as a hard error (exit 2) when no self-test is
  implemented, so a no-op cannot masquerade as a passing control.
- **Verdict**: UPHELD. **Corroboration**: single lens (C4); this is the structural root
  the other five C4 findings instantiate.
- **Root-cause cluster**: A (keystone).

#### C4-1 (HIGH, CORRECTED) — Check 15 (`check_gams_equations.py`) gates but is uncontrolled

- **Location**: `scripts/check_gams_equations.py:26` (`DOC_EQ_RE`); gated at `validate_consistency.sh:749-754` via `check_error`.
- **Failure mode**: Gating Check 15 has no `--self-test` and is absent from
  `SELFTEST_SCRIPTS`. If `DOC_EQ_RE` silently loses matches (compiles but matches
  nothing), `unique_total -> 0` and it prints `Accuracy: 100% (0/0 unique equations)`,
  exit 0 -> `check_pass` -> **false GREEN**, no structural guard.
- **CORRECTED SCOPE** (from verifier, confirmed at synthesis): only `DOC_EQ_RE`
  (line 26, the anchored ``` `(q\d+_...) ``` form) is silent-green. A broken
  `GAMS_EQ_RE` (line 25, the corpus scanner ``` \bq\d+_... ```) fails **loud** (~162
  mismatches, exit 1). The finding's literal mutation `verify_cmd` does NOT reproduce —
  it drops the opening capture paren and raises `re.error` unbalanced-parenthesis (a
  loud crash); a faithful repro needs a balanced-paren impossible-prefix mutation.
- **Synthesis re-check**: `check_gams_equations.py` has NO `--self-test` handler
  (`grep` finds only `--summary-only` at line 48); `--self-test` therefore exits 0
  (table above). Lines 25-26 confirm the two-regex split as corrected.
- **Proposed fix (NOT applied)**: add a real `--self-test` branch that runs the
  detector over an in-memory fixture with a real equation + a fabricated
  `q99_nonexistent` doc ref, asserting exit 1 + the fabricated name surfaces; assert the
  unique-ref denominator `> 0` on the real corpus (treat `0/0` as failure). THEN
  register `check_gams_equations` in `SELFTEST_SCRIPTS`. **Note**: `--self-test` is
  currently a silent no-op exit-0, so it cannot be registered as-is (doing so would mint
  a false control per C4-4).
- **Verdict**: CORRECTED (scope narrowed to `DOC_EQ_RE`; verify_cmd repro caveat).
  **Corroboration**: single lens (C4); instantiates root A.
- **Root-cause cluster**: A.

#### C4-2 (HIGH) — Check 16 (`check_gams_realizations.py`) gates but is uncontrolled

- **Location**: `scripts/check_gams_realizations.py:26-28` (`REAL_RE`), `:158` (gating `return 1`); invoked `validate_consistency.sh:768-782`.
- **Failure mode**: Gating Check 16 (gates on fabricated realization names) has no
  `--self-test`, not registered. If `REAL_RE` breaks -> 0 triples ->
  `Accuracy: 100% (0/0 references)` -> exit 0 -> `check_pass` -> false GREEN. Same
  `N/total` denominator structure as C4-1; no nonzero-denominator assertion.
- **Evidence / synthesis re-check**: `--self-test` exits 0 (table above); the unknown
  flag is swallowed and the normal check runs. `100% ({verified}/{total})` printed with
  no sanity check on `total`.
- **Proposed fix (NOT applied)**: add `--self-test` asserting a `module_15.md`-scoped
  fabricated name (e.g. `nosuch_jan99`) -> exit 1, plus denominator `> 0` sanity;
  register in `SELFTEST_SCRIPTS` (after the handler exists).
- **Verdict**: UPHELD. **Corroboration**: single lens (C4); instantiates root A.
- **Root-cause cluster**: A.

#### C4-3 (HIGH) — Check 25 (`check_no_bare_cites.py`) gates but is uncontrolled

- **Location**: `scripts/check_no_bare_cites.py:34` (`BARE_RE`), `:56` (FP guard); invoked `validate_consistency.sh:1009-1016` via `check_error`.
- **Failure mode**: Gating Check 25 has no `--self-test`, not registered. If `BARE_RE`
  breaks or the `modules/ in before[-40:]` guard over-broadens, every bare cite is
  silently skipped -> `Bare cites found: 0` -> exit 0 -> `check_pass` -> false GREEN.
  (Note: this check's GREEN is a zero-violations count rather than an `N/total`
  accuracy ratio, but the silent-skip-to-zero outcome is identical.)
- **Evidence / synthesis re-check**: `--self-test` exits 0 (table above); `return 0` on
  empty `all_violations` with no proof the scanner still matches.
- **Proposed fix (NOT applied)**: add `--self-test` feeding a bare `equations.gms:20`
  (assert flagged) and a full-path `modules/15_food/REAL/equations.gms:20` (assert NOT
  flagged); register.
- **Verdict**: UPHELD. **Corroboration**: single lens (C4); instantiates root A.
- **Root-cause cluster**: A.

#### C4-5 (MEDIUM) — Check 20 (`check_param_defaults.py`) advisory, uncontrolled

- **Location**: `scripts/check_param_defaults.py`; invoked `validate_consistency.sh:859-878` (advisory `check_warning`, always exits 0).
- **Failure mode**: Advisory Check 20 has no `--self-test`, not registered. A regression
  in its parameter-extraction regex would silently drop from "64 claims scanned" to 0
  and emit only a benign warning — Pattern-13 default-value drift goes unflagged.
  Signal-loss, not false-green (hence MEDIUM).
- **Evidence / synthesis re-check**: no `self_test`/`self-test` token in the file;
  `--self-test` exits 0 (table above).
- **Proposed fix (NOT applied)**: add `--self-test` injecting a doc claim that disagrees
  with a known source default; assert it surfaces; register.
- **Verdict**: UPHELD. **Corroboration**: single lens (C4); instantiates root A
  (advisory variant — signal-loss rather than false-green).
- **Root-cause cluster**: A.

#### C4-6 (MEDIUM) — Check 24 (`check_renames.py`) advisory, uncontrolled

- **Location**: `scripts/check_renames.py`; invoked `validate_consistency.sh:978-986` (advisory `check_warning`).
- **Failure mode**: Advisory Check 24 has no `--self-test`, not registered. Only 3
  renames tracked; a regex break in old-name matching would silently report "0 hits"
  forever. Signal-loss.
- **Evidence / synthesis re-check**: no `self_test`/`self-test` token in the file;
  `--self-test` exits 0 (table above).
- **Proposed fix (NOT applied)**: add `--self-test` with a fixture containing a tracked
  old name; assert it is flagged; register.
- **Verdict**: UPHELD. **Corroboration**: single lens (C4); instantiates root A
  (advisory variant — signal-loss).
- **Root-cause cluster**: A.

---

## MEDIUM severity

### Cluster B — Derived count hand-copied into prose with no source-binding

Both verified C3 findings share **one root mechanism**: a value derived from a live
artifact (the validator's check count; the round count in `validation_rounds.json`) is
hand-copied into a narrative doc, with no validator asserting the copy equals the
source. The documented precedent fix (already applied elsewhere in the same files) is
**deferral** — replace the literal with a pointer to the live source.

#### C3-1 (MEDIUM) — "40 checks" in `modules/README.md` understates live count (43); twin already fixed

- **Location**: `modules/README.md:34` (vs the already-fixed twin `README.md:109`).
- **Failure mode**: Hardcoded "40 checks" understates the validator's coverage; live
  count is 43. The identical sentence in `README.md:109` was already de-hardcoded to
  "run it; the summary prints the live check count" — the fix landed on one of two
  README copies, not the other. Continues to drift silently as checks are added
  (32 -> 40 -> 43 already).
- **Evidence / synthesis re-check**: the two lines differ ONLY on this clause —
  `modules/README.md:34` "(40 checks across...)" vs `README.md:109` "(run it; the
  summary prints the live check count)". Live count confirmed `Total checks: 43`
  (validator `VALIDATOR_RESULT ... checks=43`). No enforcing check greps for "40 checks".
- **Proposed fix (NOT applied)**: replace the parenthetical in `modules/README.md:34`
  with the same deferral phrasing used in `README.md:109` (defer to the live count; do
  NOT re-hardcode 43).
- **Verdict**: UPHELD. **Corroboration**: single lens (C3).
- **Root-cause cluster**: B.

#### C3-2 (MEDIUM) — "matured to 47 rounds" in `README.md` is one round behind (48)

- **Location**: `README.md:7` vs `audit/validation_rounds.json`.
- **Failure mode**: "matured to 47 rounds" status line is one round behind:
  `validation_rounds.json` now has 48 rounds. R48 was appended ~80 min AFTER the README
  commit on the same day and never propagated to README/BACKLOG narratives. Will drift
  every time a round is appended — the documented precedent class.
- **Evidence / synthesis re-check**: `README.md:7` reads "matured to 47 rounds";
  `python3` over `validation_rounds.json` gives `len(rounds)=48, max round=48`. The
  README commit predates the R48 append (per the finding's commit timestamps). No
  enforcing check.
- **Proposed fix (NOT applied)**: defer the count ("see audit/validation_rounds.json"),
  mirroring `AGENT.md` which already defers round/bug totals to `cumulative_stats`; OR
  add a validator check asserting README round count == `len(rounds)`. **Prefer
  deferral** (consolidation bias: removes the second source rather than adding a third
  guarded surface).
- **Verdict**: UPHELD. **Corroboration**: single lens (C3).
- **Root-cause cluster**: B.

---

## Verified clean / not clustered as real (UNVERIFIED status from upstream)

These two C3 findings were marked **UNVERIFIED** by the adversarial verifier (not
elevated to UPHELD/CORRECTED). They are recorded for completeness; **they are NOT
clustered as actionable defects**, and both are already-mitigated, accepted free-to-drift
pairs. No intervention proposed.

- **C3-3 (LOW, UNVERIFIED)** — `CHANGELOG.md:23` "~892 found / ~653 fixed" vs
  `cumulative_stats` "907 / 656" (delta 15/3). **Mitigated**: both are `~`-hedged,
  `cumulative_stats.approx_bug_counts_note` explicitly disclaims machine-reconciliation,
  and the CHANGELOG entry is a frozen v1.1.0 release snapshot (defensibly
  point-in-time). The per-round schema is too heterogeneous to sum, so no script
  computes either total. **Disposition**: leave the frozen CHANGELOG release block;
  keep `cumulative_stats` as the single live counter for any CURRENT all-rounds total,
  and point non-release docs at it. No fix strictly required.

- **C3-4 (LOW, UNVERIFIED)** — pin-derived `getReport.R` values (counts 106/117, line
  ranges, SHA) hand-copied into THREE files (`agent/helpers/magpie4_reference.md`,
  `audit/flywheel_rubric.md` G4, `audit/validation_rounds.json` regression_questions G4)
  with no check binding them to the renv pin; recomputed 105/116 (already off-by-one);
  the `sync_magpie4_clone.py --check` canary guards only `version_pins.json` vs
  `renv.lock` and is NOT wired into `validate_consistency.sh`. **Status: UNVERIFIED** —
  the synthesis did not independently re-derive the 105/116 vs 106/117 delta this round
  (the pinned clone was not re-walked), so this is surfaced as a *candidate* triplication
  drift, not a confirmed defect. **If a future round confirms it**, the right move is the
  same consolidation as Cluster B: keep counts/line-ranges in `magpie4_reference.md`
  only, make G4's expected answer "compute from the pinned `getReport.R` at audit time"
  (the discipline G3 already mandates), and optionally wire `sync_magpie4_clone.py
  --check` into the validator as an advisory section. It is logically part of Cluster B's
  root cause (derived value hand-copied, no source-binding) but is held out of the
  actionable cluster pending verification.

---

## Refuted (auditor false-positives)

**None.** The upstream pipeline reported 0 REFUTED / 0 CITATION_FAILED findings; the
verifier filtered before synthesis. No auditor false-positive pattern to note this round.
(The one scope correction — C4-1's `DOC_EQ_RE`-vs-`GAMS_EQ_RE` narrowing and the
verify_cmd-does-not-reproduce caveat — was a *tightening* of a real finding, not a
refutation.)

---

## Root-cause clusters -> interventions

| Cluster | Root cause | Findings | Intervention | Severity | Adds surface? |
|---|---|---|---|---|---|
| **A** | A `check_*.py` with no real `--self-test` ignores the flag and exits 0; gating checks then go false-GREEN on a `0/0` denominator after a silent regex break, and the harness can mint a FAKE positive control by `pass`-ing on exit-code-0 alone. | C4-1, C4-2, C4-3, C4-4, C4-5, C4-6 | **Two-part, deletion-biased.** (1) Harden the harness FIRST (`selftest_validator.sh`): `pass` only on a `SELFTEST_OK <name>` sentinel, not exit-code-0; and make every `check_*.py` `main()` treat `--self-test` as a HARD ERROR (exit 2) when unimplemented — this *closes* the no-op masquerade for all current and future checks in one edit and makes the existing silent no-ops fail loudly instead of adding per-check machinery. (2) THEN add real `--self-test` branches (fabricated-ref -> exit 1 + denominator `>0`) to the gating checks (C4-1/2/3 priority; C4-5/6 advisory, lower) and register them. Part (1) is the leverage: it converts 6 silent holes into 6 loud failures with one structural change. | HIGH | **Yes (justified)** — adds a sentinel contract + a hard-error guard. Justified because the alternative (the status quo) is strictly worse: it lets a capability-lost check report PASS and lets a no-op be registered as a passing control. The hard-error-on-unimplemented `--self-test` is itself a *consolidation*: one rule that makes the no-op class impossible, replacing N ad-hoc per-check audits. |
| **B** | A value derived from a live artifact (validator check count; round count) is hand-copied into a narrative doc with no validator binding the copy to its source. | C3-1, C3-2 | **Deferral (deletion of the duplicate source).** Replace each literal with a pointer to the live source — exactly the fix already applied to the C3-1 twin (`README.md:109`) and to `AGENT.md`'s round/bug totals. C3-1: copy `README.md:109`'s phrasing into `modules/README.md:34`. C3-2: defer `README.md:7` to `audit/validation_rounds.json`. **Prefer deferral over a new equality-asserting validator check** — deferral removes the drift surface entirely (consolidation bias), whereas a new check adds a third guarded surface for a LOW-frequency, MEDIUM-impact drift. | MEDIUM | **No** — removes duplicated sources of truth. |

**Shared meta-pattern**: both clusters are instances of *no mechanical binding between a
derived artifact and its source-of-truth*. They are kept as two clusters because the
*intervention differs*: Cluster B can DELETE the duplicate (deferral); Cluster A cannot
delete the check, so it must instead make the missing-control state FAIL LOUD. C3-4 (held
as UNVERIFIED) would belong to Cluster B's root if confirmed.

**Why Cluster A is ordered first** despite Cluster B having the same count of verified
findings: Cluster A is a *false-assurance* failure (a check reports GREEN while blind),
which silently erodes the entire validator's trustworthiness and is amplified by CI;
Cluster B is a *cosmetic drift* (a stale number in prose) with no downstream correctness
impact. False-GREEN >> stale-count in blast radius.
