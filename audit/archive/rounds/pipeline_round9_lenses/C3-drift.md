# Pipeline Audit Round 9 — Lens C3 (DRIFT: derived value vs its source)

**Lens key:** C3-drift
**Failure class hunted:** a generated/derived value (count, SECTION_TOTAL, cumulative_stats field, version pin, freshness anchor, "Check N" reference) that has drifted from its source with NO check enforcing agreement.
**Method:** enumerate every derived value across the machinery; for each, recompute from source and either name the enforcing check or prove its ABSENCE.
**Develop reference:** `/tmp/magpie_develop_ro` (git worktree pinned at `ee98739fd`, == sync_log last_sync_commit).
**Validator baseline this run:** `VALIDATOR_RESULT: completed=1 checks=43 passed=39 warnings=4 errors=0 verdict=PASS` (SECTION_NUM reached 28, structural guard passed).

---

## METHOD NOTES / grep discipline

- Every absence claim was confirmed twice (isolated grep, EXIT code reported) + a positive control proving grep works in that dir/file.
- One near-miss trap caught mid-audit (see CLEAN item "22 of 46"): running AGENT.md's realization-count command WITHOUT its `grep -v '/input/$'` filter gave 40; WITH the filter (the actual command) gave 22 — the documented value is correct. Re-reasoned instead of filing a false positive.

---

## FINDINGS

### C3-1 — `modules/README.md:34` hardcodes "40 checks"; live count is 43; no enforcing check; fix already applied to the sibling top-level README

**Severity:** MEDIUM **Kind:** drift **Confidence:** HIGH

**Location:** `modules/README.md:34`

**Source of truth:** the validator's own live count — `latest_result.json` `"checks": 43`; `VALIDATOR_RESULT: ... checks=43`; `CHANGELOG.md:25` "32 -> 43 checks".

**The drift:** `modules/README.md:34`:
> "...mechanically guarded by `scripts/validate_consistency.sh` (**40 checks** across naming, citations, realizations, variables, equations, dependencies)."

The IDENTICAL sentence in the top-level `README.md:109` was de-hardcoded:
> "...mechanically guarded by `scripts/validate_consistency.sh` (run it; **the summary prints the live check count**)."

So the fix (remove the literal, defer to the live count) was applied to one of the two README copies and not the other. `diff` of the two lines shows they differ ONLY on this clause.

**Failure mode:** understates the validator's coverage (40 vs 43) in a subordinate README; future drift continues silently as checks are added (the count was 32, then 40, now 43 — it has moved twice already).

**No enforcing check:** confirmed `grep -Hn '40 checks' scripts/*.py scripts/*.sh` → EXIT 1 (no script contains the literal); positive control `grep README scripts/check_no_bare_cites.py` → EXIT 0. `validate_consistency.sh:341-344` only checks that README *references* `validation_rounds.json`, not any count.

**verify_cmd:**
```
grep -n "40 checks" <magpie-agent>/modules/README.md && cat <magpie-agent>/.cache/validation_reports/latest_result.json | grep checks
```
→ `modules/README.md:34:...(40 checks across...` AND `"checks": 43,`

**Suggested fix:** replace the parenthetical in `modules/README.md:34` with the same deferral phrasing used in `README.md:109` ("run it; the summary prints the live check count"). Do not re-hardcode 43. (DO NOT apply — read-only audit.)

blast_radius / what_it_protects / who_else_needs_it: n/a (not a removal/merge).

---

### C3-2 — `README.md:7` claims "matured to 47 rounds"; `validation_rounds.json` now has 48 rounds; no enforcing check

**Severity:** MEDIUM **Kind:** drift **Confidence:** HIGH

**Location:** `README.md:7`

**Source of truth:** `audit/validation_rounds.json` — `len(rounds)=48`, `max(round)=48`, `cumulative_stats.total_rounds=48`, last round date 2026-06-05.

**The drift:** `README.md:7`:
> "The semantic-validation flywheel has matured to **47 rounds** (recent rounds 9.3-9.6 / 10, periphery stabilized)..."

This is a "Latest" status line (not a frozen snapshot), so it is meant to be current. It is one round behind.

**Timeline (smoking gun):**
- `README.md` last committed 2026-06-05 **12:51** (`6d87471` "Release v1.1.0").
- `validation_rounds.json` R48 appended 2026-06-05 **14:10** (`1e0fb4f` "R48 semantic validation"), ~80 minutes LATER.
- R48 (`type: full`, scope "cross_module conservation docs + 2 core_docs ... post-R47 stale set") exists with a design file `audit/archive/rounds/round48_design.md`, but appears in NO markdown narrative (`rg -ln 'R48|round 48'` over `*.md` → EXIT 1). README + BACKLOG narratives both stop at R47.

**Failure mode:** the public-facing round count understates flywheel maturity by one and will keep drifting every time a round is appended (this is the documented precedent class — aggregate count markers drifting ~3 rounds unchecked).

**No enforcing check:** `grep -Hn 'matured to|47 rounds|48 rounds|README.*round' scripts/*.py scripts/*.sh` → EXIT 1; positive control `grep rounds scripts/selftest_validator.sh` → EXIT 0. No script compares README's round count to `len(rounds)`.

**verify_cmd:**
```
grep -n "matured to" <magpie-agent>/README.md && python3 -c "import json;print('rounds=',len(json.load(open('<magpie-agent>/audit/validation_rounds.json'))['rounds']))"
```
→ `README.md:7:...matured to 47 rounds...` AND `rounds= 48`

**Suggested fix:** either (a) defer ("matured to dozens of rounds — see `audit/validation_rounds.json` for the count"), mirroring how AGENT.md:216/418 already defers bug/round totals to `cumulative_stats`; or (b) add a one-line CI/validator check asserting README's stated round count == `len(rounds)`. Prefer (a) — it removes the drift surface entirely. (DO NOT apply.)

blast_radius / what_it_protects / who_else_needs_it: n/a.

---

### C3-3 — `CHANGELOG.md:23` cumulative bug totals ("~892 / ~653") disagree with `cumulative_stats` ("907 / 656")

**Severity:** LOW **Kind:** drift **Confidence:** HIGH

**Location:** `CHANGELOG.md:23` vs `audit/validation_rounds.json` `cumulative_stats.approx_total_bugs_found/_fixed`

**The drift:** CHANGELOG.md:23 "Cumulative doc bugs across all rounds: **~892 found / ~653 fixed**" vs cumulative_stats **907 found / 656 fixed** (Δ = 15 found / 3 fixed). Both purport to be the all-rounds cumulative total.

**Mitigating context (why LOW, not MEDIUM):**
- Both numbers are `~`-hedged.
- `cumulative_stats.approx_bug_counts_note` EXPLICITLY disclaims them: "approx_total_bugs_* are hand-aggregated across the heterogeneous per-round schema ... approximate, not machine-reconciled."
- The CHANGELOG entry is the v1.1.0 *release* block — a point-in-time snapshot. Release snapshots arguably SHOULD freeze, so divergence from a later-updated live counter is partly expected behavior, not a pure defect.

**No enforcing check:** neither value is computed by any script; the per-round schema is too heterogeneous for a clean machine sum (the note says as much). This is an accepted free-to-drift pair, surfaced here for completeness.

**verify_cmd:**
```
grep -n "Cumulative doc bugs" <magpie-agent>/CHANGELOG.md && python3 -c "import json;cs=json.load(open('<magpie-agent>/audit/validation_rounds.json'))['cumulative_stats'];print(cs['approx_total_bugs_found'],cs['approx_total_bugs_fixed'])"
```
→ `~892 found / ~653 fixed` AND `907 656`

**Suggested fix:** lowest-cost is to leave the frozen CHANGELOG release block alone and instead ensure the SINGLE live counter (`cumulative_stats`) is the only place anything claims "across all rounds". If a current (non-release) doc ever repeats the cumulative figure, point it at `cumulative_stats` rather than copying. No fix strictly required. (DO NOT apply.)

blast_radius / what_it_protects / who_else_needs_it: n/a.

---

### C3-4 — magpie4 pin-derived values (counts 106/117, line ranges L56-235 / L62-182, SHA a360d8c) are triplicated across three files with no check binding them to the pin; the existing pin canary is NOT wired into the validator

**Severity:** LOW **Kind:** drift **Confidence:** HIGH

**Location:** `agent/helpers/magpie4_reference.md:12,42,45`; `audit/flywheel_rubric.md` G4 (lines ~207-215); `audit/validation_rounds.json` regression_questions G4 (expected_answer_summary).

**Source of truth:** `.cache/sources/magpie4/R/getReport.R` at the `version_pins.json`-pinned SHA (`2.70.0 @ a360d8c9ec`, which currently MATCHES `../input/renv.lock`).

**The exposure:** the SAME derived values from getReport.R are hand-copied into three independent files:
- counts: "117 unconditional calls to 106 unique report* functions"
- line ranges: "getReport() spans L56-235; tryList dispatch block L62-182"
- pin: "v2.70.0 @ a360d8c9ec"

Recomputed from source at the pinned SHA: **105 unique** report* functions (not 106) and **116 call lines** (not 117) inside the tryList block (62-182); function def at L56, tryList opens at L62, file is 235 lines. So the docs are already **off-by-one** on both counts. This is within G4's own hedge ("~106", "off-by-few is Minor") and `magpie4_reference.md:261` self-flags it ("Plan said 108 ... actual count is 106"), so it is not actively misleading — but it shows the values are unreconciled.

**Why this is a structural drift exposure, not just an off-by-one:**
1. The workspace magpie4 clone is ALREADY ahead of the pin (helper line 257: "currently v2.75.1, ahead of the renv pin v2.70.0"). When the renv pin advances to catch up, all three copies of the line ranges + SHA + counts must be updated in lockstep, by hand.
2. A real check EXISTS for the pin itself — `scripts/sync_magpie4_clone.py --check` (the "pin canary", lines 189-204, compares `version_pins.json` stored `lock_file_sha256` vs live renv.lock). It currently reports `OK`. BUT: (a) it only guards `version_pins.json` vs `renv.lock`; it does NOT verify the getReport line-range/count claims in the three docs; and (b) it is NOT invoked by `validate_consistency.sh` (confirmed: `grep 'sync_magpie4|version_pins|magpie4' scripts/validate_consistency.sh` → EXIT 1). So on every doc-edit validator run, the pin freshness is never checked.

**No enforcing check on the doc claims:** `grep -rln 'getReport' scripts/` → EXIT 1 (no script reads getReport.R or verifies its derived doc claims); positive control `grep -rln 'magpie4|version_pins' scripts/` → EXIT 0 (sync_magpie4_clone.py, probe_dedup_check.py).

**verify_cmd:**
```
cd <magpie-agent> && sed -n '62,182p' .cache/sources/magpie4/R/getReport.R | grep -oE 'report[A-Z][A-Za-z0-9]*' | sort -u | wc -l ; grep -n "106 unique" agent/helpers/magpie4_reference.md
```
→ `105` (actual unique count) vs doc claim `...117 ... calls to 106 unique report* functions`

**Suggested fix (two independent levers):**
1. Collapse the triplication: keep the line-range/count claims in ONE place (magpie4_reference.md) and have G4's expected_answer_summary say "compute from the pinned getReport.R at audit time" — exactly the pattern G3 already mandates ("do not hardcode it here (pin advances)"). G4 currently violates the discipline G3 establishes.
2. Wire `python3 scripts/sync_magpie4_clone.py --check` into `validate_consistency.sh` as an advisory section so pin staleness surfaces on every validator run, not only when someone remembers to run the canary.
(DO NOT apply — read-only audit.)

blast_radius / what_it_protects / who_else_needs_it: n/a (not a removal/merge).

---

## CLEAN CATEGORIES (verified, not padded)

Each of these is a derived value I recomputed from source and found in agreement, OR a value that has a working enforcing check.

1. **SECTION_TOTAL=28 vs actual print_section calls** — `validate_consistency.sh:107` SECTION_TOTAL=28; counted exactly 28 `print_section` invocations (29 grep hits minus the function definition); the two advisory checks (27, 28) call `print_section ""` but still increment SECTION_NUM. **Self-checked**: the structural guard at lines 1120-1128 FATALs (exit 99) if `SECTION_NUM != SECTION_TOTAL`. Live run reached 28/28 with no FATAL. This is the GOOD pattern — the derived denominator has a hard self-check. (Note: the single hardcoded `SECTION_TOTAL=28` is the SSOT per the R7 comment that removed 28 scattered "/28" literals.)

2. **cumulative_stats.total_rounds (48) vs len(rounds) (48)** — currently MATCH; rounds numbered 1..48 with NO gaps and NO duplicates. There is no enforcing check (no script references validation_rounds.json for this), so it is free to drift, but it is correct RIGHT NOW. (The downstream README copy of this count is NOT correct — that is finding C3-2.)

3. **cumulative_stats.last_validation_date vs rounds[-1].date** — both 2026-06-05. MATCH.

4. **version_pins.json vs ../input/renv.lock** — version 2.70.0, SHA a360d8c9ec MATCH in both; clone HEAD aligned; pin canary reports `OK (renv.lock sha256 matches version_pins.json)`. A real working check exists (`sync_magpie4_clone.py --check`). (Its non-wiring into the main validator + the un-bound downstream count/line claims are finding C3-4.)

5. **"Check-10" cross-references (AGENT.md:5, AGENT.md:134) vs validator section numbering** — both reference "Check-10 validator failure" for AGENT.md-vs-deployed-copy drift; `validate_consistency.sh:597` is `print_section "10/28" "Checking AGENT.md deployment..."`. The reference is ACCURATE (survived the section renumbering).

6. **AGENT.md:205 "currently 22 of 46" modules with >1 realization** — recomputed via AGENT.md's OWN command (with its `grep -v '/input/$'` filter) against develop: exactly **22 of 46**. CORRECT. (Initial run without the input filter gave 40 — a false alarm I discarded after re-reading the exact command. The prose at line 202 naming hubs M10/M14/M52/M56 refers to a retired *static* list, not a current claim; verified those four hubs each have exactly ONE realization dir, so their absence from the 22 is correct.)

7. **AGENT.md "20 MANDATEs" (lines 216, 220, 288) vs verifiers.md** — verifiers.md contains exactly MANDATE 1..20 (unique count 20, max 20). CORRECT. No enforcing check (the one script hit, `check_gams_citations_impl.py`, mentions "MANDATE 16" only in comments/messages), but currently accurate. (History: README commit `cfbc5be` was "MANDATE count 16->20" — it drifted once and was fixed; worth a future guard but not a live defect.)

8. **metadata.rubric_version (1.2) vs flywheel_rubric.md declared version** — flywheel_rubric.md line 1 "(v1.2)" and line 5 "Version: 1.2". MATCH. The schema_version_history entry "v1.2 ... rubric bumped to v1.1" is a point-in-time historical record (rubric was 1.1 when JSON schema hit 1.2; both have since advanced), NOT a current claim — no live coherence defect.

9. **File-count claims: "46 modules", "6 GAMS reference docs", "6 cross_module docs"** — live counts are 46 / 6 / 6 respectively (modules/README.md:3,11; README.md:82; AGENT.md:346). All CORRECT. (Notes files = 13, helpers = 17, commands = 10; no doc hardcodes these, so nothing to drift.)

10. **Internal sync-log consistency: sync_log last_sync_commit (ee98739fd) == develop worktree HEAD** — 0 commits ahead. README "docs are current with develop" is internally consistent with sync_log. CAVEAT (not a finding I can prove either way from here): the /tmp worktree is itself pinned at ee98739fd, so this only proves sync_log ↔ worktree agreement, not freshness against the LIVE upstream develop (no network fetch available in this read-only audit).

---

## SUMMARY VERDICT

The machinery's MOST load-bearing derived value — the validator's section denominator — is properly self-checked (SECTION_TOTAL hard-guarded by SECTION_NUM==SECTION_TOTAL FATAL). The pin has a working canary. Most spot-checked counts (round total, last_validation_date, MANDATE count, file counts, realization count, rubric version) are currently ACCURATE.

The live drift is concentrated in **doc-prose copies of derived counts that lack any enforcing check**: a check-count literal fixed in one README but not its sibling (C3-1), a round count one behind because R48 landed after the README commit (C3-2), and triplicated pin-derived getReport values whose canary isn't wired into the validator (C3-4). All four are the documented precedent class — aggregate markers drifting because the value lives in prose with no link back to source. The pattern the maintainers ALREADY adopted in AGENT.md (defer to "the summary prints the live check count" / "see cumulative_stats for current totals") is the correct fix and just needs to be propagated to the three straggler sites.
