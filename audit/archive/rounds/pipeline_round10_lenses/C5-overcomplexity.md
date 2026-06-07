# Pipeline Audit Round 10 — Lens C5: OVER-COMPLEXITY (cost > catch rate)

- **Lens key**: C5-overcomplexity
- **Failure class**: machinery whose cost (wall-time, advisory-noise, maintenance) exceeds its lifetime real catches
- **Method (decorrelation axis)**: EMPIRICAL — time the gate; count advisory-noise lines; for each check cross-reference its lifetime REAL catches (rounds logs + git fix-commits + structural reachability). Flag checks/scripts where cost clearly exceeds catch.
- **Date**: 2026-06-07
- **Auditor model**: claude-opus-4-8[1m]
- **Mode**: READ-ONLY (no edits applied; this report is the only file written)

---

## TL;DR

The gate is **fast** (`time bash scripts/validate_consistency.sh` = **6.2s real**), so the precedent's wall-time concern is unfounded today. The precedent's "~874 advisory noise lines" is also **largely RESOLVED**: the bare-basename advisory volume dropped from 779/874 to **22** (the 2026-06-05 comma-list rework + prior cleanup). Current advisory floor is ~**107 lines/run** and is not the dominant cost.

The real over-complexity is **green-count inflation + maintenance surface from zero-catch checks**. A prior Opus audit (**R7, 2026-05-29**) already classified Checks **1/2/4/6/23/26** as "catch ~nothing" and recommended retirement; it was **DEFERRED for session length and never applied** — it is still live in `audit/BACKLOG.md:45` and the current burst plan (`audit/BACKLOG.md:11`) names round 10 (C1/C2/C5) as the resumption point. This lens confirms that finding empirically and adds the structural-dead-check evidence (Check 4 cannot fail by construction).

---

## Empirical cost measurement

### Wall-time (NOT a problem)
```
$ { time bash scripts/validate_consistency.sh ; }
real    0m6.159s   user 0m3.446s   sys 0m3.189s
$ { time python3 scripts/check_units.py --summary ; }                 real 0m0.089s
$ { time python3 scripts/check_multi_section_consistency.py ... ; }    real 0m0.074s
```
The candidate-retirement scripts each run in <0.1s. Wall-time is NOT the cost axis here.

### Advisory-noise floor (current run, 2026-06-07)
Verdict line: `completed=1 checks=43 passed=39 warnings=4 errors=0 verdict=PASS`

| Source | Lines/run | Status vs precedent |
|---|---|---|
| Bare-basename ambiguity (Check 17 impl) | **22** | DOWN from 779/874 — RESOLVED |
| Multi-section "signature variants" (Check 23) | **75** | standing, never actioned |
| CLAUDE.md refs (Check 7) | 6 | standing |
| Doc unit mismatches (Check 26) | 4 | perpetual baseline |
| Arity mismatches (Check 23) | 2 | false positives (see C5-3) |
| Cross-cutting identifiers (Check 21) | 2 | pedagogical FPs (see C5-5) |

The dominant historical noise source (bare-basename) is gone. The residual is small and concentrated in two advisory scripts (Check 23 = 77 of the lines, Check 26 = 4).

### Green-count inflation
The 28 sections expand to **43 "checks"** counted in the verdict, because several sections call `check_pass` multiple times unconditionally. Section 4 alone adds **+3 to PASSED_CHECKS every run while being structurally incapable of failing** (see C5-1). This inflates `passed=39` relative to the number of things actually verified.

---

## Catch-history method & the FP trap

`audit/validation_rounds.json` records SEMANTIC answer-quality bugs, not gate catches — so "0 hits in that log" is NOT by itself proof a check never fired (avoided this trap). Gate catches surface as **fix-commits**. Positive control over `git log --grep`:

| Check class | fix-commits | verdict |
|---|---|---|
| KEEP: broken-link / citation / realization (Checks 3/8/17/18) | **109** | genuinely load-bearing |
| Check 14 (GAMS variable names) | **70** | genuinely load-bearing |
| Candidate: dependency-count / duplicate-eq / file-count (Checks 1/2/4/6) | **5** (all mechanization/refactor commits, none a catch) | low value |
| `check_units` + `check_multi_section` (Checks 26/23) | **16** (all CREATION + allowlist-maintenance + unrelated flywheel notes; none "caught a bug → fixed a doc") | cost, no evidenced catch |

The partition is sound: the KEEP set has 70–109 fix-commits; the retirement candidates have zero evidenced catches and only maintenance commits.

---

## FINDINGS

### C5-1 — Check 4 (duplicate equations) is structurally incapable of failing — pure green-count inflation
- **Severity**: MEDIUM | **Kind**: removal
- **Location**: `scripts/validate_consistency.sh:309-332` (section "[4/28] Checking duplicate equations...")
- **Failure mode**: All three branches of Check 4 call `check_pass`; **zero** call `check_warning`/`check_error`. The check can NEVER emit an error or warning — it only prints "found in N files" and a NOTE that says "Duplicate equations ... require manual review". It increments TOTAL_CHECKS and PASSED_CHECKS by 3 every run, inflating the green count without verifying anything verifiable. The "manual review" it defers to is never tracked or performed.
- **Evidence**:
  ```
  $ sed -n '309,332p' scripts/validate_consistency.sh | grep -c "check_pass"           -> 3
  $ sed -n '309,332p' scripts/validate_consistency.sh | grep -cE "check_warning|check_error" -> 0
  ```
- **verify_cmd**: `sed -n '309,332p' scripts/validate_consistency.sh | grep -cE "check_warning|check_error"`  (expect 0)
- **what_it_protects**: nominally, that a documented equation isn't contradictorily described in two files. In practice it protects nothing — it cannot detect a contradiction; it only counts file occurrences and always passes.
- **who_else_needs_it**: no live dependent. Not referenced by `selftest_validator.sh`, not in any helper, not cited by any doc.
- **blast_radius**: deleting the block + decrementing SECTION_TOTAL (28→27) removes 3 always-green checks. `print_section` auto-numbers (validate_consistency.sh:106-112), so no renumber cascade. The section-count guard (validate_consistency.sh:1120) enforces SECTION_NUM==SECTION_TOTAL, so the decrement is mandatory and self-checked.
- **suggested_fix**: delete lines 309-332; set `SECTION_TOTAL=27`. (Do NOT apply — read-only audit.) Real cross-file contradiction detection, if wanted, belongs in a content-diff checker, not a file-count counter.
- **confidence**: HIGH

### C5-2 — Checks 1/2/6 (dependency-count, equation-param, file-count) are best-effort with zero evidenced catches; R7 flagged them for retirement, deferred & still live
- **Severity**: MEDIUM | **Kind**: removal
- **Location**: `scripts/validate_consistency.sh:126-195` (Check 1), `:197-239` (Check 2), `:375-410` (Check 6); BACKLOG carry-over `audit/BACKLOG.md:45`
- **Failure mode**: These have warn/error branches (3 each) so they are not structurally dead like Check 4, but: (a) Check 1's own in-code R5 comment (`:131-137`) admits "the docs increasingly express dependency counts via dependency tables rather than 'N dependents' prose, so empty grep is now common ... This check is best-effort; canonical source is core_docs/Module_Dependencies.md" — i.e. it now always hits the 0-PASS branch; current run shows "No explicit count" for M10/M11/M17. (b) Check 2's Chapman-Richards probe prints empty " parameters (consistent)" (no count to compare). (c) Check 6 hardcodes "46 modules / 6 cross-module / 6 GAMS / 6 feedback" — brittle constants that will warn on *legitimate* growth, the opposite of a useful guard. R7 (a prior Opus structural audit) explicitly classified Checks 1/2/4/6 as catching "~nothing" and recommended deletion; status DEFERRED 2026-05-29 for session length, never applied.
- **Evidence**:
  ```
  $ grep -n "best-effort" scripts/validate_consistency.sh
  137:    # is best-effort; canonical source is core_docs/Module_Dependencies.md.
  # R7 report, audit/archive/rounds/pipeline_audit_round7.md:48:
  #   "Check-retirements (Checks 1/2/4/6/23/26 ...). Now LOW-risk ... LOW value
  #    (these checks catch ~nothing). Keep Checks 3 + 8 (real link integrity)."
  # Still open: audit/BACKLOG.md:45 "(1) check-retirements — drop Checks 1/2/4/6 ..."
  # git catch-history: git log --grep "dependency count|duplicate equation|file count" -> 5 commits, all mechanization/refactor
  ```
- **verify_cmd**: `grep -n "catch ~nothing" audit/archive/rounds/pipeline_audit_round7.md`
- **what_it_protects**: Check 1/2 = consistency of dependency/parameter COUNTS across docs (now expressed as tables, not prose, so the grep target no longer exists). Check 6 = file-count drift from expected inventory.
- **who_else_needs_it**: none of the three is referenced by `selftest_validator.sh` (its per-check positive-control list, `:97-99`, deliberately omits them). No helper or command depends on them.
- **blast_radius**: deleting all three inline blocks + decrementing SECTION_TOTAL accordingly. Auto-numbering + section-count guard make this safe and self-checked. Check 6's file-counts are the only mild loss (a genuinely-deleted module doc would no longer warn) — but Check 3 (broken module_XX.md refs, KEEP) already catches deletions that break a live reference, which is the failure that actually matters.
- **suggested_fix**: per R7/BACKLOG, delete Checks 1/2/6 blocks; KEEP Checks 3 + 8 (link integrity, 109 fix-commits). If file-inventory drift is still wanted, replace Check 6's hardcoded constants with a dynamic count that only warns on DECREASE. (Do NOT apply.)
- **confidence**: HIGH

### C5-3 — Check 23 (`check_multi_section_consistency.py`) produces a 77-line/run advisory floor that is self-described non-actionable, requires allowlist upkeep, and has never caught its target bug class
- **Severity**: MEDIUM | **Kind**: removal
- **Location**: `scripts/check_multi_section_consistency.py` (253 LOC); wired at `scripts/validate_consistency.sh:947-966`; allowlist entries in `audit/advisory_allowlist.json`
- **Failure mode**: The script's own header says "Exit: 0 always (advisory)". Per-run it emits **75 "signature variants"** (self-described in source as "usually legitimate context variation (subset vs parent set, literal ...)" — `check_multi_section_consistency.py:141-143`) plus **2 "arity mismatches"** which on inspection are FALSE POSITIVES: module_18.md uses `vm_prod_reg(i,kres)`, `(i,kcr)`, `(i2,kcr)`, `(i2,kres)` — all arity-2, differing only by set-alias (i/i2, kres/kcr are legitimate distinct crop subsets). The check counts distinct signature STRINGS, so aliases read as drift. It needs **3 allowlist entries** just to suppress its own FPs (module_29 vm_land, module_35 pm_carbon_density_secdforest_ac, module_80 p80_modelstat). The bug it was BUILT to catch (M14 `pcm_tau` h→j straggler) appears **0 times** in validation_rounds.json — never caught in the flywheel.
- **Evidence**:
  ```
  $ grep -n "Exit: 0 always (advisory)" scripts/check_multi_section_consistency.py    -> 30
  $ grep -nE "usually legitimate" scripts/check_multi_section_consistency.py          -> 142
  # current run: "Multi-section consistency: 2 arity mismatch(es), 75 variant(s) [advisory]"
  $ grep -nE "vm_prod_reg" modules/module_18.md   # all arity-2, alias-only differences
  $ grep -ci "pcm_tau" audit/validation_rounds.json    -> 0   (target bug never caught here)
  $ python3 -c "import json;print(len([e for e in json.load(open('audit/advisory_allowlist.json'))['allowlist'] if e['check']=='check_multi_section_consistency']))" -> 3
  ```
- **verify_cmd**: `grep -n "Exit: 0 always (advisory)" scripts/check_multi_section_consistency.py`
- **what_it_protects**: catching a rename straggler where some doc mentions use the old set-dimension after a MAgPIE set rename (the M14 pcm_tau class).
- **who_else_needs_it**: NOT in `selftest_validator.sh`'s per-check positive-control list (`:97-99`) — the maintainers' own test harness treats it as disposable. Only `validate_consistency.sh` Check 23 invokes it.
- **blast_radius**: deleting Check 23 block + the script + its 3 allowlist entries; decrement SECTION_TOTAL. Removes 77 advisory lines/run and the allowlist-maintenance burden. The arity-drift class it targets is also covered (more reliably) by Check 14 (variable existence) + Check 22 (consumer attribution) for the cases that produce wrong identifiers. R7 named it explicitly for deletion.
- **suggested_fix**: per R7/BACKLOG, delete `check_multi_section_consistency.py` + Check 23 + its allowlist entries; OR, if kept, suppress the 75-variant output entirely (variants are admitted-legitimate) and only surface arity mismatches AFTER set-alias normalization so the vm_prod_reg FP stops firing. (Do NOT apply.)
- **confidence**: HIGH

### C5-4 — Check 26 (`check_units.py`) is a perpetual 4–5-line advisory baseline, never disambiguable from no-test, requiring allowlist upkeep
- **Severity**: MEDIUM | **Kind**: removal
- **Location**: `scripts/check_units.py` (277 LOC); wired at `scripts/validate_consistency.sh:1025-1041`; allowlist entry `module_59.md / s59_nitrogen_uptake`
- **Failure mode**: Across many recorded rounds the output is a STANDING floor of 4–5 mismatches, every entry explicitly tagged "pre-existing", "NOT in this round's edited set", "advisory baseline", and one round's note: *"No unit-class bugs surfaced in R25; cannot disambiguate from no-test."* The mismatches are mostly unit-convention abbreviations the checker can't normalize (e.g. "USD17MER" vs "USD", "200 kg N/ha" vs "0.2 t N/ha"), so the floor is structural FPs, not findable bugs. It needs an allowlist entry to suppress one of its own FPs. Catch history (git): 16 commits referencing it, all creation/allowlist/flywheel — zero "caught a unit bug → fixed a doc".
- **Evidence**:
  ```
  # validation_rounds.json contexts (verbatim):
  #   "1a check_units.py: No unit-class bugs surfaced in R25; cannot disambiguate
  #    from no-test. Advisory baseline (5 mismatches)..."
  #   "...check_units 5 unit-claim mismatches (modules 60/57/12/56/39, all
  #    pre-existing, NOT in this round's edited set)..."
  $ grep -c "check_units" audit/validation_rounds.json     -> 9  (all advisory-baseline mentions)
  # allowlist:
  #   {check: check_param_defaults? no — check_units FP captured as s59 unit-conversion entry}
  # current run: "4 doc unit claim(s) differ from canonical (advisory; ...)"
  ```
- **verify_cmd**: `python3 -c "import json,re; s=json.dumps(json.load(open('audit/validation_rounds.json'))); print('No unit-class bugs surfaced' in s)"`  (expect True)
- **what_it_protects**: doc unit-string drift from declarations.gms canonical units.
- **who_else_needs_it**: NOT in `selftest_validator.sh` per-check controls (`:97-99`). Only Check 26 invokes it.
- **blast_radius**: deleting `check_units.py` + Check 26 + its allowlist entry; decrement SECTION_TOTAL. Removes the perpetual 4–5-line floor. NOTE: unit drift is a real class in principle — the issue is THIS implementation can't normalize units so it only ever reports the same un-fixable FPs. R7 named it for deletion. Lower-confidence than C5-1/2/3 because a unit checker WITH normalization would have value; the recommendation is to retire the current non-normalizing one, not to declare unit-checking worthless.
- **suggested_fix**: per R7/BACKLOG, delete `check_units.py` + Check 26 + allowlist entry; OR rebuild with a unit-normalization table (kg↔t, USD aliases) so it stops emitting structural FPs and can actually fail on a real drift. (Do NOT apply.)
- **confidence**: MEDIUM

### C5-5 — Check 21 flags deliberately-illustrative identifiers as "not in GAMS code" with no opt-out marker (recurring non-suppressible FP)
- **Severity**: LOW | **Kind**: inefficiency
- **Location**: `scripts/check_doc_var_existence.py` via `scripts/validate_consistency.sh:886-908`; offending lines `reference/GAMS_Advanced_Features.md:619,645,744`
- **Failure mode**: Check 21 reports `vm_production` and `vm_trade` as "identifier not in GAMS code". Both are explicitly labelled in the doc as *"illustrative; `vm_production` is not a real MAgPIE variable"* (three times). The author deliberately marked them fake; the checker has no per-line allow marker for "intentionally-fictional pedagogical identifier", so this FP recurs every run and trains readers to ignore Check 21 warnings (alarm fatigue on an otherwise load-bearing checker — Check 14/21 share the identifier-existence catch class with 70 fix-commits).
- **Evidence**:
  ```
  $ grep -nE "vm_production|vm_trade" reference/GAMS_Advanced_Features.md
  619:**Example - Non-zero lower bound** (illustrative; `vm_production` is not a real MAgPIE variable):
  645:**Example - Unbounded** (illustrative; `vm_trade` is not a real MAgPIE variable):
  744:(Illustrative; `vm_production` is not a real MAgPIE variable.)
  # current run: "Cross-cutting doc identifiers: Found 2 identifier not in GAMS code"
  ```
- **verify_cmd**: `grep -nE "vm_production|vm_trade" reference/GAMS_Advanced_Features.md`
- **what_it_protects**: n/a (not a removal — this is a precision fix to keep a useful check trustworthy)
- **who_else_needs_it**: n/a
- **blast_radius**: n/a
- **suggested_fix**: add a per-line opt-out marker (e.g. `<!-- not-a-real-var -->`) the checker honors, OR add these two to a pedagogical-identifier allowlist. Keeps Check 21's signal clean. (Do NOT apply.)
- **confidence**: HIGH

### C5-6 — Dead first argument to `print_section` (28 stale "N/28" literals the code ignores)
- **Severity**: LOW | **Kind**: coherence
- **Location**: `scripts/validate_consistency.sh:103-112` (function) + 28 call sites passing `"1/28"`…`"26/28"`
- **Failure mode**: The R7 refactor made `print_section` auto-number from `SECTION_NUM` and the code comment (`:103-105`) states the legacy first arg "is now ignored". Yet all 28 call sites still pass a hardcoded `"N/28"` literal as `$1`. These literals are dead, will silently drift if anyone reorders sections (they already disagree with the auto-numbered output for the two trailing sections that pass `""`), and invite a maintainer to "fix" the wrong number. Minor over-complexity / coherence debt left by the otherwise-good R7 self-counting refactor.
- **Evidence**:
  ```
  $ sed -n '103,112p' scripts/validate_consistency.sh   # "The legacy first arg ('N/M') is now ignored."
  $ grep -cE 'print_section "[0-9]+/28"' scripts/validate_consistency.sh   -> 26 (plus 2 sites pass "")
  ```
- **verify_cmd**: `grep -cE 'print_section "[0-9]+/28"' scripts/validate_consistency.sh`
- **what_it_protects**: n/a
- **who_else_needs_it**: n/a
- **blast_radius**: n/a
- **suggested_fix**: drop the first positional arg from all call sites (pass only the label), or change the signature to one arg. Cosmetic; bundle with any of the section deletions above. (Do NOT apply.)
- **confidence**: HIGH

---

## CLEAN categories (checked, genuinely clean — not padded)

- **Gate wall-time**: 6.2s full run; no slow check. The precedent's wall-time worry does not hold today.
- **Bare-basename advisory volume**: collapsed from 779/874 to 22 (2026-06-05 comma-list rework + prior cleanup). The single largest historical noise source is RESOLVED — explicitly reporting clean rather than re-flagging the stale number.
- **Load-bearing checkers (14 variables, 17 citations, 18 default-realizations, 3 broken-refs, 8 broken-links)**: rich catch history (70–109 fix-commits), each with a `--self-test` positive control in `selftest_validator.sh` (except 3/8 which are simple existence checks). These EARN their cost — not over-complex.
- **`selftest_validator.sh`**: 5 properties + 9 per-check positive controls; pointedly excludes the disposable advisory scripts. Well-scoped, not bloated.
- **Validator robustness machinery** (EXIT trap, completion sentinel, section-count guard, no `set -e`): justified by a documented 7-month silent-death incident; this is value, not over-complexity.
- **`advisory_allowlist.json`**: small (5 entries), every entry has a reason + review cadence. The allowlist itself is fine; the problem is that 3 of 5 entries exist only to suppress FPs from the two retirement-candidate scripts (Check 23/26) — they go away if those scripts go.

---

## Cross-lens notes (for synthesis)

- **C4-untested-testers** (prior round9): the checks I flag for removal (1/2/4/6/23/26) are exactly the ones C4's harness does NOT cover — agreement that they are second-class. C5 says: don't backfill tests for them, RETIRE them.
- **Standing R7 decision**: this is not a new proposal. C5 supplies the empirical confirmation (structural-dead Check 4; git catch-history partition; current advisory floor) that the R7 retirement was correct, and notes it is the explicitly-named next step in the current burst plan (`audit/BACKLOG.md:11`).
- **Net if all removals applied**: gate 28→~23 sections, ~43→~34 counted checks (less green-count inflation), ~81 advisory lines/run removed (75 multi-section + 4 units + 2 arity), 2 scripts + ~530 LOC + 3 allowlist entries deleted, with NO loss of an evidenced catch class (every load-bearing class retained).
