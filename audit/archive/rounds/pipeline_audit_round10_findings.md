# Pipeline Audit Round 10 — Synthesis (consolidation lenses C1/C2/C5)

- **Date**: 2026-06-07
- **Repo HEAD at synthesis**: `708fa87` (Audit burst: flywheel R49/R50 + reusable pipeline-audit workflow + R9 coherence fixes)
- **Lenses**: C1-dead (untested/dead machinery), C2-redundant (overlapping → merge), C5-overcomplexity (cost > catch rate)
- **Mode**: READ-ONLY. No fixes applied here — all interventions are user-reviewed per `agent/commands/pipeline-audit.md`.
- **Inputs**: lens reports `pipeline_round10_lenses/{C1-dead,C2-redundant,C5-overcomplexity}.md`; per-finding adversarial verifications `pipeline_round10_verify/{C1-1,C2-1,C5-1,C5-3,C5-4}.md`.
- **Counts**: raw 11 → deduped 10 → 5 adversarially verified (1 UPHELD, 4 CORRECTED, 0 REFUTED) + 3 deduped-but-UNVERIFIED merge candidates (C2-2/3/4). 0 auditor false-positives (no REFUTED/CITATION_FAILED).

---

## TL;DR for the maintainer

This round produced **no new architectural problem**. Every verified finding lands on one of **two already-approved, already-deferred work-items**, plus **one small safe deletion**, plus **three low-value doc-tidies the verify stage explicitly told us NOT to push**.

- **Root 1 (the headline)**: C5-1 + C5-3 + C5-4 are three instances of the **standing R7 zero-catch retirement** (`audit/BACKLOG.md:45`; named as the round-10 resumption point at `audit/BACKLOG.md:11`). ONE bundled removal sweep retires Checks 4/23/26 (+ scripts `check_multi_section_consistency.py`, `check_units.py`). Consolidation-positive: deletes ~530 LOC + 3 allowlist entries + ~81 advisory lines/run, with **no loss of an evidenced catch class**.
- **Root 2**: C1-1 is the **deferred "Cluster A" false-GREEN harness** (`burst_2026-06-07_continuation.md` PENDING item 1; R9 C4-1..C4-7). Fold this confirmation in; do not open a new item.
- **Sequencing link between the two roots**: Root 1 retires `check_multi_section_consistency` + `check_units`, which are **2 of the 7 scripts** Cluster A must harden. **Do Root 1 first** and Cluster A's scope shrinks 7 → 5 scripts (and 2 of the 3 advisory self-tests in Cluster A step (c) — checks 23/26 — become moot).
- **Root 3**: C2-1 (CORRECTED) — delete one advisory-only branch (`check_gams_citations_impl.py:702-710`). Safe, removes a latent FP, but **not** the redundancy the finding claimed.
- **Root 4 (do-not-act)**: C2-2/3/4 are UNVERIFIED LOW doc-tidies; each self-flags "DO NOT push / DO NOT merge." Park in BACKLOG; no intervention.

---

# FINDINGS (severity-ordered)

## HIGH

### C1-1 — 7 validator checks have no real `--self-test`; the flag falls through to a live scan and exits 0 (latent false-GREEN)
- **Verdict**: UPHELD (`pipeline_round10_verify/C1-1.md`) | **Lens**: C1-dead | **Kind**: untested | **Corroboration**: single-lens (C1-dead); cross-round corroborated by R9 C4-1..C4-7.
- **Location**: gates `scripts/check_gams_equations.py`, `check_gams_realizations.py`, `check_no_bare_cites.py`; advisory `check_param_defaults.py`, `check_renames.py`, `check_multi_section_consistency.py`, `check_units.py`. Harness `scripts/selftest_validator.sh:95-103`. CI `validate.yml:63-65`.
- **Failure mode**: All 7 contain ZERO self-test code (`grep -c 'self.test|self_test|selftest'` → 0 for each; positive control `check_default_realizations.py` → 11). `--self-test` is an unrecognized arg that falls through to the normal live-repo scan and exits 0 when clean (reproduced: `check_multi_section_consistency.py --self-test` prints "Arity mismatches: 2"; `check_units.py --self-test` prints "Mismatches: 4" — both exit 0, plainly the production scan, not a fixture). 3 of the 7 GATE (Checks 15/16/25 via `check_pass` on exit-0). The gates print a HARDCODED "Accuracy 100%" with no nonzero-denominator guard (`check_gams_equations.py:91` — "100%" is a literal, not computed): a future detection-regex regression → 0 refs → "100% (0/0)" → exit 0 → `check_pass` → false GREEN that nothing catches. **Present-tense the gates are healthy** (Check 15=153/153, Check 16=60/149, Check 25=44 scanned/0 found) — hence `kind=untested` (latent fragility, not a live break) is correct.
- **CI amplification**: `validate.yml:63` runs `selftest_validator.sh` "always blocking", and the harness comment (`:95`) instructs "ADD new --self-test scripts to this list." Adding any of these 7 (which exit 0 on the unknown flag) would mint a **CI-enforced FALSE positive control**.
- **Evidence**: see verify file STEP B1–B6; every claim reproduced mechanically.
- **Proposed fix (CONSOLIDATION-compatible — adds no artifact class; makes the existing harness actually exercise the existing checks)**: (a) harden `selftest_validator.sh` to require a `SELFTEST_OK <name>` stdout sentinel, not bare exit-0 — the leverage fix, closes all holes at once; (b) make every `check_*.py` treat an unimplemented `--self-test` as a hard error (exit 2); (c) add synthesize-bug-first `--self-test` branches to gates 15/16/25 FIRST (assert exit 1 + denominator>0; treat 0/0 as FAIL), then the surviving advisory checks; (d) register in `SELFTEST_SCRIPTS` only AFTER a real self-test exists.
- **Disposition**: **Already APPROVED + DEFERRED as "Cluster A"** (`burst_2026-06-07_continuation.md` PENDING item 1; R9 C4-1..C4-7). Fold this confirmation into that work-item. Do NOT open a new one; do NOT apply here. **See sequencing note under Cluster B below** — Root 1 retires 2 of these 7 scripts, shrinking this item's scope.

---

## MEDIUM

### C5-1 — Check 4 (duplicate equations) is structurally incapable of failing — pure green-count inflation
- **Verdict**: CORRECTED (`pipeline_round10_verify/C5-1.md`) | **Lens**: C5-overcomplexity | **Kind**: removal | **Corroboration**: single-lens; cross-round R7 (`pipeline_audit_round7.md:48`).
- **Location**: `scripts/validate_consistency.sh:309-332` (section "[4/28] Checking duplicate equations").
- **Failure mode**: `verify_cmd` confirms zero `check_warning`/`check_error` in the block — the check cannot fail by construction; it only prints "found in N files" + a NOTE deferring to a never-performed manual review, while incrementing PASSED_CHECKS every run (green-count inflation).
- **CORRECTED scope**: the magnitude is overstated. There are 3 `check_pass` STATEMENTS, but lines 324/326 are a mutually-exclusive Q52 if/else, so only **2 execute per run** (verified: full validator prints exactly 2 green lines for `[4/28]`). So it adds **+2** to PASSED_CHECKS, not "+3 / all 3 branches." Removal-safety claim stands: no live dependent (not in `selftest_validator.sh`, no helper, no doc cites it).
- **Proposed fix**: delete lines 309-332; set `SECTION_TOTAL=27` (`print_section` auto-numbers; the section-count guard at `:1120` makes the decrement self-checked). Non-breaking 1-line touch to `validate.md` + a BACKLOG line. **Do NOT apply.**
- **Disposition**: part of the standing R7 retirement (Cluster B below).

### C5-3 — Check 23 (`check_multi_section_consistency.py`) is a self-described non-actionable advisory floor that needs 3 allowlist entries to suppress its own FPs and has no evidenced catch
- **Verdict**: CORRECTED (`pipeline_round10_verify/C5-3.md`) | **Lens**: C5-overcomplexity | **Kind**: removal | **Corroboration**: single-lens; cross-round R7 (named for deletion); cross-lens C4 (round 9, the untested-tester set).
- **Location**: `scripts/check_multi_section_consistency.py` (253 LOC); wired `scripts/validate_consistency.sh:947-966` (Check 23); 3 entries in `audit/advisory_allowlist.json` (module_29 `vm_land`, module_35 `pm_carbon_density_secdforest_ac`, module_80 `p80_modelstat`).
- **Failure mode**: header says "Exit: 0 always (advisory)". Per run: 75 "signature variants" (source self-labels "usually legitimate context variation", `:142`) + 2 "arity mismatches" that are FALSE POSITIVES. Needs 3 allowlist entries purely to suppress its own FPs. The bug it was built to catch (M14 `pcm_tau` set-rename straggler) has no evidenced catch in the flywheel.
- **CORRECTED scope (two evidence sub-claims wrong; conclusion survives)**: (1) the FP **reason** is mischaracterized — the real trigger in module_18.md is an **arity-1 prose shorthand** `vm_prod_reg(kres)` at L223 (author dropped the `i`/`i2` dim in prose), not "arity-2 throughout, set-alias-only." (2) the cited command `grep -ci pcm_tau audit/validation_rounds.json -> 0` is FALSE; it returns **2** (lines 6660, 6733), though both hits are unrelated to a Check-23 catch, so the narrow "never caught its target class" claim still plausibly holds. The FP-floor and zero-catch conclusions reproduce.
- **Removal safety**: Check 23 (`:949-951`) IS a live dependent, so a naked `rm` is unsafe — but this is a **bundled** removal (script + Check 23 block + the 3 multi_section allowlist entries + SECTION_TOTAL decrement), already scoped LOW-risk in `audit/BACKLOG.md:45`. The allowlist is SHARED with `check_param_defaults` (Check 20) — delete ONLY the 3 `check_multi_section_consistency` entries, KEEP the 2 `check_param_defaults` entries + the file + its `_schema.consumers` key. Verify stage also caught two stale doc refs to fix on removal: `maintenance_protocol.md:37` (allowlist-consumer mention) and `session_cleanup.md:71` ("Check 23 will fail if AGENT.md drifts" — actually Check 10, pre-existing drift the finding missed).
- **Proposed fix**: bundled retirement per R7/BACKLOG. **Do NOT apply.** Do NOT endorse the blast-radius claim that "Check 14 + Check 22 cover the arity-drift class" — not verified equivalent.
- **Disposition**: part of the standing R7 retirement (Cluster B below).

### C5-4 — Check 26 (`check_units.py`) is a perpetual 4–5-line structural-FP advisory baseline, never disambiguable from no-test
- **Verdict**: CORRECTED (`pipeline_round10_verify/C5-4.md`) | **Lens**: C5-overcomplexity | **Kind**: removal | **Corroboration**: single-lens; cross-round R7 (named for deletion) + BACKLOG:35 (~40% FP rate).
- **Location**: `scripts/check_units.py` (277 LOC); wired `scripts/validate_consistency.sh:1025-1041` (Check 26).
- **Failure mode**: standing floor of 4–5 mismatches, all "pre-existing/advisory baseline"; one round note "No unit-class bugs surfaced in R25; cannot disambiguate from no-test." Empirically ≥3/4 current mismatches are regex-misparse FPs (e.g. grabs a conversion target "GJ", the module-13 abbreviation "(TC)", a description-as-unit) it cannot normalize. Git: 16 referencing commits, all creation/allowlist/flywheel — zero "caught a unit bug → fixed a doc."
- **CORRECTED scope (allowlist accounting wrong; removal otherwise correct)**: the finding says check_units owns "1 allowlist entry (`s59_nitrogen_uptake`)". **FALSE** — `check_units.py` reads NO allowlist (`grep -niE 'skip|allow|nitrogen_uptake|s59'` → none). The `s59_nitrogen_uptake` entry (`advisory_allowlist.json:30`) belongs to **`check_param_defaults.py` = Check 20** (corroborated `Bug_Taxonomy.md:277`, `BACKLOG.md:57`, `pipeline_audit_round3.md:150`). The "200 kg N/ha vs 0.2 t N/ha" example in the failure_mode is a Check-20 FP, not a check_units FP. So removal must **NOT** touch any allowlist entry.
- **Proposed fix**: delete `scripts/check_units.py` + the Check 26 block (`:1025-1041`) + decrement `SECTION_TOTAL` 28→27. Lower-confidence than C5-1/3 only because a unit checker WITH a normalization table (kg↔t, USD aliases) would have value — the recommendation is to retire THIS non-normalizing implementation, not to declare unit-checking worthless. **Do NOT apply.**
- **Disposition**: part of the standing R7 retirement (Cluster B below).

### C2-1 — `check_gams_citations_impl.py:702-710` mis-classifies placeholder/wildcard full-path .gms cites as "bare" (latent advisory FP; NOT a Check-25 duplicate)
- **Verdict**: CORRECTED (`pipeline_round10_verify/C2-1.md`) | **Lens**: C2-redundant | **Kind**: merge (re-scoped to removal of a latent FP) | **Corroboration**: single-lens; the finding cited R7 deferred item #2 but that scopes a DIFFERENT (module-doc, ~779) advisory than this non-module branch.
- **Location**: `scripts/check_gams_citations_impl.py:702-710` (the `if mod_num is None:` BARE-advisory branch).
- **Failure mode (as re-scoped by verify)**: this branch flags 22 advisories per direct invocation. The finding claimed they are (a) the same property as Check 25, (b) allowlist-cleared pedagogical cites, (c) 22 noise lines/run in the gate. **All three are FALSE**: (a) Check 25's `BARE_RE` lookbehind `(?<![./])` correctly treats slash-preceded `.gms` as non-bare → it reports 0 by CORRECT classification, not allowlist — different property (lexical-bare vs resolution-failure-after-misparse); (b) no `check-bare-cite` markers exist on these cites (`grep -rn 'check-bare-cite'` → none) — they are placeholder/wildcard FULL-PATH cites (`AGENT.md:232` `modules/XX_.../equations.gms:123`; `Infeasibility_Debugging_Guide.md:581-584` `modules/80_optimization/*/input.gms:9-12`) that the impl's `modules/[\w/]+/` prefix capture can't parse (breaks on `.`/`*`) → falls to bare-fallback; (c) the Check-17 harness (`validate_consistency.sh:795-797`) extracts ONLY the "verified:" line on exit-0 and discards the impl's `BARE:`/advisory lines → `bash scripts/validate_consistency.sh | grep -c 'BARE:'` → **0**. The 22 appear ONLY on direct invocation (the verify_cmd), never in the gate.
- **Removal safety**: SAFE. No external consumer of the `BARE:` string (`rg -n 'BARE:' --glob '!.../check_gams_citations_impl.py'` → only auditor .md files). The impl self-test (assertions A-G) exercises MODULE-doc bare-cite RESOLUTION, never the `mod_num is None` non-module branch → stays green. The `ambig` counter is advisory-only (`:1021/:1033`), never gated → no verdict change.
- **Proposed fix**: delete `check_gams_citations_impl.py:702-710` (or, better, narrow CITATION_RE / the FILE-branch to recognize placeholder paths). Removes a latent false-positive source. **Do NOT apply.** **Reject the original "redundant with Check 25 → merge" framing** — acting on it as written teaches the wrong model of the code (Check 25 does NOT own this property; there is no duplicate to merge away; there is no gate-visible noise to eliminate).
- **Disposition**: standalone safe deletion (Cluster C below). Independent of Roots 1/2.

---

## LOW (UNVERIFIED merge candidates — do-not-act this round)

> These three were deduped into the survivor set but were **NOT** adversarially verified (no `pipeline_round10_verify/` file). Each is a doc/regex tidy whose **own suggested_fix explicitly counsels against pushing it**. The verify stage's repeated CORRECTED verdicts on the C2 family (C2-1's "redundant" claim was wrong on the mechanism) is reason to treat un-verified C2 "redundancy" claims with extra suspicion. Recommended disposition: **BACKLOG note, no intervention.**

### C2-2 — verifiers.md MANDATE 18 generalizes MANDATE 9, but M9 carries a unique cost-variable provenance table
- **Verdict**: UNVERIFIED | **Lens**: C2-redundant | **Kind**: merge | **Severity**: LOW.
- **Location**: `agent/helpers/verifiers.md:139-152` (M9) vs `:285-302` (M18).
- **Failure mode**: M18's text says it "Generalizes MANDATE 9 (cost variables) to ALL interface variables", but M9 holds the only consolidated 5-row cost-attribution table (vm_cost_prod_crop→M38, livestock→M70, pasture→M31, residue→M18, forestry→M32) — M18 references but does not reproduce it.
- **Proposed fix / why not**: optionally fold M9's table into M18 as a worked sub-example. **DO NOT push** — round-7 verify ruled "no MANDATE demoted; demotion drops the answer-time guard" (M9 is the sole human-review guard for the R3 cost-misattribution bug). Also blast-radius: renumbering would force `AGENT.md` + `../AGENT.md` + `../CLAUDE.md` edits (verifiers.md hub-status warning). Negative EV.

### C2-3 — validate-module.md re-implements (inline bash) the link/citation property the whole-repo gate mechanizes
- **Verdict**: UNVERIFIED | **Lens**: C2-redundant | **Kind**: merge | **Severity**: LOW.
- **Location**: `agent/commands/validate-module.md` Check 3 (Links Validity) vs `validate_consistency.sh` Check 8 (links) + Check 17 (citations).
- **Failure mode**: duplicated INTENT across the interactive single-module command and the CI gate.
- **Proposed fix / why not**: point validate-module.md's link step at the canonical owner ("or run `validate_consistency.sh` Check 8/17"). **DO NOT merge the artifacts** — different invocation models (interactive single-module vs CI whole-repo); the command runs greps inline, so there is no maintained script to drift. Cosmetic at best.

### C2-4 — bare-cite regex is a duplicated literal across migrate_bare_cites.py and check_no_bare_cites.py
- **Verdict**: UNVERIFIED | **Lens**: C2-redundant | **Kind**: merge | **Severity**: LOW.
- **Location**: `scripts/migrate_bare_cites.py` (BARE regex literal) vs `scripts/check_no_bare_cites.py:33-34` (`BARE_RE`; comment literally says "Same bare-cite regex as migrate_bare_cites.py").
- **Failure mode**: regex can silently drift between the one-shot migration tool and its enforcing guard; the repo's good pattern is import-the-shared-engine.
- **Proposed fix / why not**: `migrate_bare_cites.py` is a one-shot tool applied 2026-05-24 and will not re-run, so drift is harmless. Consolidation-correct disposition: **BACKLOG note that the migration is complete and the tool is archive-ready** (do not import; do not edit).

---

# Verified clean (checked, genuinely clean — not padded)

From the C5-overcomplexity lens (`pipeline_round10_lenses/C5-overcomplexity.md` § CLEAN categories), independently corroborated where reproduced:

- **Gate wall-time**: 6.2s full run; no slow check. The precedent's wall-time concern does not hold today.
- **Bare-basename advisory volume**: collapsed from 779/874 to 22 (2026-06-05 comma-list rework). The single largest historical noise source is RESOLVED.
- **Load-bearing checkers** (Check 14 variables; 17 citations; 18 default-realizations; 3 broken-refs; 8 broken-links): 70–109 fix-commits each, each with a `--self-test` positive control. They EARN their cost.
- **`selftest_validator.sh`** scope: 9 per-check controls, pointedly excludes the disposable advisory scripts. Well-scoped.
- **Validator robustness machinery** (EXIT trap, completion sentinel, section-count guard, no `set -e`): justified by a documented silent-death incident; value, not over-complexity.
- **`advisory_allowlist.json`**: 5 entries, each with a reason + cadence; the allowlist itself is fine — 3 of 5 entries only exist to suppress the retirement-candidate scripts' FPs and go away with them.

Findings from the C5 lens NOT carried into the verified survivor set (lens produced them; no verify file → out of scope for this synthesis, left for a future round or the R7 bundle): **C5-2** (Checks 1/2/6 retirement — same R7 root as Cluster B), **C5-5** (Check 21 pedagogical-identifier FP — a precision fix, not a removal), **C5-6** (dead `print_section` first arg — cosmetic, bundle with any section deletion).

---

# Refuted (auditor false-positives)

**None.** 0 findings were REFUTED or CITATION_FAILED. All 5 verified findings had `citation_ok = true`; the 4 CORRECTED verdicts are scope/magnitude corrections, not refutations — in every case the underlying defect and the removal-safety conclusion survived.

**Auditor-pattern note (for the verifier flywheel, not a finding)**: the C2-redundant lens has a recurring over-claim signature — it labels "two things touch the same property" as "duplicate → merge" without checking that the two compute the SAME property under the SAME semantics. C2-1 was the clearest instance (different regex semantics: lexical-bare vs resolution-failure-after-misparse; the gate already suppresses the impl output). The 3 UNVERIFIED C2 candidates (C2-2/3/4) likely share this optimism — hence the do-not-act disposition until verified. This mirrors `feedback_verifier_layer_coupling`: distrust a "redundant" claim until you've confirmed identical property + identical scope + identical owner.

---

# Synthesis — root-cause clusters & interventions

Per `feedback_synthetic_interventions`: 8 surviving findings collapse to **3 actionable roots + 1 do-not-act bucket**. The dominant root (B) is a single bundled DELETE that subsumes 3 findings; it is consolidation-positive (removes machinery). Only the harness root (A) adds any surface, and that addition is justified and pre-approved.

### Cluster A — Latent false-GREEN: detection logic has no positive control [adds surface, justified]
- **Findings**: C1-1.
- **Root cause**: validator checks ship a `--self-test` flag that isn't implemented, so the harness/CI mint false positive controls and gating checks can go GREEN on a 0/0 denominator if a detection regex silently regresses.
- **Intervention**: the Cluster-A plan in `burst_2026-06-07_continuation.md` PENDING item 1 — (a) `SELFTEST_OK` sentinel in `selftest_validator.sh`; (b) unimplemented `--self-test` → exit 2; (c) real synthesize-bug-first self-tests for the gating checks (15/16/25) first; (d) register only after a real test exists. **Already approved + deferred; do not re-open.**
- **adds_surface = true** — justification: it ADDS self-test code + a sentinel check. This is the correct exception to the consolidation bias: the added surface is *test* surface that makes existing machinery trustworthy (it is the mechanical backstop the false-GREEN class needs; a doc rule cannot enforce it). Net new artifact CLASS = none (extends the existing `selftest_validator.sh` harness). Severity HIGH.
- **Sequencing**: execute **after** Cluster B — B retires `check_multi_section_consistency` + `check_units`, two of the seven scripts in C1-1's scope, shrinking A from 7 → 5 scripts and dropping checks 23/26 from step (c)'s advisory list.

### Cluster B — Standing R7 zero-catch retirement (one bundled DELETE) [removes surface]
- **Findings**: C5-1, C5-3, C5-4 (and, same root, lens-only C5-2).
- **Root cause**: machinery whose cost (green-count inflation, perpetual advisory FP floor, allowlist upkeep, maintenance LOC) exceeds its lifetime evidenced catches — already classified "catch ~nothing" by R7 and approved for retirement, then deferred for session length and never applied.
- **Intervention**: ONE bundled removal sweep (the R7 follow-up at `BACKLOG.md:45`): delete Check 4 block (`validate_consistency.sh:309-332`); delete Check 23 block (`:947-966`) + `scripts/check_multi_section_consistency.py` + its **3** `check_multi_section_consistency` allowlist entries (keep the 2 `check_param_defaults` entries + the file + its `_schema.consumers` key); delete Check 26 block (`:1025-1041`) + `scripts/check_units.py` (touch **no** allowlist entry — check_units owns none); decrement `SECTION_TOTAL` once per removed section (guarded at `:1120`); repoint the two stale doc refs (`maintenance_protocol.md:37`, `session_cleanup.md:71`) + a 1-line `validate.md` touch + BACKLOG close. (Optionally fold C5-2's Checks 1/2/6 + C5-6's dead `print_section` arg into the same sweep, since they share the root and the same auto-numbering safety net.)
- **adds_surface = false** — deletes ~530 LOC, 2 scripts, 3 allowlist entries, ~81 advisory lines/run, with no loss of an evidenced catch class. Severity MEDIUM (HIGH leverage on noise/maintenance, but no live correctness gap today).
- **Sequencing**: do this **first** (shrinks Cluster A).

### Cluster C — Latent advisory FP in the citation impl (one safe deletion) [removes surface]
- **Findings**: C2-1 (CORRECTED).
- **Root cause**: an advisory-only branch mis-bins placeholder/wildcard full-path `.gms` cites as "bare" because the citation regex's prefix capture breaks on `.`/`*`. It is NOT a duplicate of Check 25 (the finding's redundancy framing is wrong).
- **Intervention**: delete `check_gams_citations_impl.py:702-710` (advisory-only, no external consumer, self-test green). Removes a latent false-positive source. Independent of A/B.
- **adds_surface = false** — deletes a 9-line branch. Severity LOW-to-MEDIUM (no gate-visible noise; the gate already suppresses these lines).

### Bucket D — Do-not-act doc-tidies (BACKLOG note only)
- **Findings**: C2-2, C2-3, C2-4 (all UNVERIFIED LOW).
- **Root cause**: weak "duplicated intent" across docs/tools; each candidate's own analysis says the duplication is harmless or that merging would lose a load-bearing guard.
- **Intervention**: NONE this round. Add a single BACKLOG line: "C2-2/3/4 — LOW merge candidates examined R10; verify ruled against pushing (M9 cost-table is a load-bearing guard; validate-module.md is inline not a maintained script; migrate_bare_cites.py is one-shot/archive-ready). No action." Re-verify before ever acting.
- **adds_surface = false** (no change). Severity LOW.
