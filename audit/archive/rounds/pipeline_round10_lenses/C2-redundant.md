# Pipeline Audit Round 10 — Lens C2: REDUNDANT / overlapping (→ merge)

**Date**: 2026-06-07 | **Auditor model**: claude-opus-4-8 [1m] | **Mode**: READ-ONLY (no repo files edited except this report)
**Method**: static cross-comparison — build a {validator/MANDATE/command → property checked} matrix; find cells covered 2+ times; propose the merge. Standing bias: DELETE/MERGE/SIMPLIFY; for every removal/merge fill what_it_protects + who_else_needs_it + blast_radius.
**Develop ground truth**: `/tmp/magpie_develop_ro` at `ee98739fd` (= `project/sync_log.json` last_sync_commit — in sync).

---

## Executive summary

The two ground-truth precedents for this lens — **(a) 3 realization validators overlapped**, **(b) dual GAMS .sh/.py checkers** — were **BOTH already remediated in pipeline-audit round 7** (2026-05-29) and the remediations **HELD**:

- **Dual .sh/.py twins**: round-7 cluster I1 ("collapse dual .sh/.py GAMS checkers to one .py") APPLIED at `65f6718`. Verified in round 10: **zero** `check_*.sh`/`check_*.py` twin pairs remain. The only surviving `.sh` checker is `check_gams_citations.sh` (21 lines, pure delegation to `check_gams_citations_impl.py`) — round 7 explicitly kept it as a "genuine wrapper, not a duplicate."
- **Realization trio (Checks 16/18/19)**: round-7 verify stage built a **synthesized known-bug test** proving Check 18 and Check 19 catch **DISJOINT** classes and **REFUTED** the merge. Verified in round 10: they remain disjoint on different surfaces; the merge is correctly NOT done.

After re-deriving the full current property matrix for the 18 active validators + 20 MANDATEs + command family, **one genuine residual redundancy survives** (round-7's own deferred item #2): the **`check_gams_citations_impl.py` BARE-advisory path duplicates Check 25 (`check_no_bare_cites.py`)** for bare-basename cites in non-module docs — same property, **contradictory signal** (Check 25 honors the allowlist → 0; the impl path ignores it → 22 noise lines/run), inferior implementation. That is the one MEDIUM finding. Three further LOW items are recorded with the explicit note that they touch decisions round 7 already adjudicated, so the consolidation bias is held in check.

**A clean bill is a weak result, so I dug across all four C2 surfaces (scripts, MANDATEs, commands, helpers). The architecture is genuinely well-consolidated post-round-7 — the reuse pattern is "import the shared engine, assert a different property," not "duplicate the checker."** I did not pad.

---

## The property matrix (18 active validators in validate_consistency.sh)

| Check | Script | Property asserted | Scope | Overlaps? |
|---|---|---|---|---|
| 14 | check_gams_variables.py | identifier EXISTS in current GAMS | `modules/module_*.md` | with 21 → DISJOINT scope (see below) |
| 15 | check_gams_equations.py | `q<N>_*` equation name exists | `modules/module_*.md` | none |
| 16 | check_gams_realizations.py | realization token exists as a dir (module-scoped) | `modules/module_*.md` body | with 18/19 → DISJOINT (see below) |
| 17 | check_gams_citations(_impl).py | file:line within EOF + Pattern-12 content + **BARE-advisory** | module + non-module docs | **BARE path ⟷ Check 25 → REDUNDANT** |
| 18 | check_default_realizations.py | doc's `(default)` LABEL matches config/default.cfg | `modules/module_NN.md` | with 16/19 → DISJOINT |
| 19 | check_module_realizations.py | header/footer/body-cite realization exists + matches default | `modules/module_NN.md` | with 16/18 → DISJOINT |
| 20 | check_param_defaults.py | `(default V)` scalar value matches source | `modules/module_NN.md` | none (value, not realization) |
| 21 | check_doc_var_existence.py | identifier EXISTS in current GAMS | cross_module/core_docs/helpers/commands/reference | with 14 → DISJOINT scope; imports 14's engine |
| 22 | check_consumer_attribution.py | consumer-COUNT claim matches recomputed count | module docs + Module_Dependencies + safety_guide | imports 14's index; UNIQUE property |
| 23 | check_multi_section_consistency.py | within-doc DIMENSION-signature consistency | `modules/module_*.md` | none (arity, not existence/units) |
| 24 | check_renames.py | doc does NOT use a historically-renamed OLD name | modules/core_docs/cross_module/agent/reference | none (old-name, not current-existence) |
| 25 | check_no_bare_cites.py | bare-basename `.gms:N` cite (allowlist-aware) | cross_module/core_docs/reference/helpers/AGENT.md/README.md | **owns the property the Check-17 BARE path duplicates** |
| 26 | check_units.py | unit string matches declarations.gms | `modules/module_XX.md` | none |
| 28 | check_scaling.py | `.scale` numeric value matches scaling.gms | `modules/module_XX.md` | none (mirrors 26's STRATEGY, different PROPERTY) |

(Checks 1-13 + 27 are structural/self-referential — dependency counts, links, deployment, fences, hardcoding; round-7 I5 proposed retiring 1/2/4/6/23/26 but that's a value/dead-code question for lens C1/C5, not redundancy. No two of them cover the same property.)

---

## FINDING C2-1 (MEDIUM) — `check_gams_citations_impl.py` BARE-advisory duplicates Check 25, with contradictory output

**Location**: `scripts/check_gams_citations_impl.py:702-710` (the `if mod_num is None:` BARE-advisory branch) vs `scripts/check_no_bare_cites.py` (Check 25, whole file).

**The duplicated property**: "a bare-basename `.gms:N` citation appears in a NON-module doc (cross_module/, core_docs/, reference/, agent/helpers/, AGENT.md, README.md)." Both checkers compute exactly this.

**Why it is a defect, not benign double-coverage — they DISAGREE in the same run**:

```
$ bash scripts/validate_consistency.sh 2>&1 | grep -iE '\[17/|\[25/|citation|bare-basename'
[17/28] Checking file:line citations in docs...
✓ File:line citations verified: 3001/3001 valid          # (Check 17 — but its 22 BARE advisories fire internally)
[25/28] Checking for bare-basename .gms citations in non-module docs...
✓ No bare-basename .gms citations in non-module docs       # (Check 25 — clean)

$ python3 scripts/check_gams_citations_impl.py . .. 2>&1 | grep -c 'BARE:'   # full count via "...17 more"
# 22 BARE advisories, e.g.:
#   BARE: /equations.gms:123 (in AGENT.md)
#   BARE: /input.gms:9..12 (in Infeasibility_Debugging_Guide.md)   [core_docs]

$ python3 scripts/check_no_bare_cites.py 2>&1 | grep -E 'Bare cites found|No bare'
Bare cites found: 0
✅ No bare cites in non-module docs (all use full-path form)
```

Check 25 reports **0**; the Check-17 BARE path reports **22** — for the SAME docs. The discriminator is the allowlist: Check 25 honors the `<!-- check-bare-cite -->` (per-line) and `<!-- check-bare-cites: allow -->` (whole-doc) markers (`check_no_bare_cites.py:41-42,48,52`), so it correctly clears pedagogical examples. The Check-17 BARE branch (`check_gams_citations_impl.py:702-710`) consults **no allowlist at all** — it re-flags the very cites Check 25 already cleared. So the impl path is the **inferior, redundant copy** of a property Check 25 owns authoritatively.

**Round-7 already saw this and deferred it** (`audit/archive/rounds/pipeline_audit_round7.md:49`, deferred item #2: "`check_gams_citations_impl.py` still computes ~779 non-actionable bare-basename advisories/run for module docs (**redundant with Check 25**)"). The module-doc flood (779) has since shrunk, but the residual non-module overlap (22/run) is the same redundancy, still live in round 10.

**failure_mode**: 22 contradictory advisory lines emitted per validator run for cites that the authoritative checker (25) has already cleared → reviewer noise; a future maintainer could "fix" a flagged pedagogical cite that was intentionally allowlisted, or distrust Check 25's clean result. Two checkers as source-of-truth for one property is the classic drift seed.

### Removal/merge dossier (mandatory)
- **what_it_protects**: catching a genuine, un-allowlisted bare-basename cite in a non-module doc (ambiguous: which module's `equations.gms`?).
- **who_else_needs_it**: **Check 25 (`check_no_bare_cites.py`) fully owns this property**, on the same scope, allowlist-aware, and **gated as an ERROR** (exit 1) rather than buried as advisory. Verified: Check 25's `SCOPE_PATTERNS` = cross_module/core_docs/reference/agent-helpers/AGENT.md/README.md — a superset of where the 22 impl advisories fire.
- **blast_radius**: removing only the `mod_num is None` BARE branch (impl:702-710). Confirmed safe:
  - No external consumer parses the `"BARE:"` string: `rg -n "BARE:" --glob '!scripts/check_gams_citations_impl.py' .` → **empty** (cross-checked: the grep ran repo-wide minus the source and found nothing).
  - The impl **self-test** asserts only the load-bearing bare-basename *resolution* behavior for MODULE docs (the f4f44b0 fix, impl:~440-470) — it does NOT assert the non-module advisory; the self-test stays green.
  - The `ambig` counter the branch feeds is "advisory only / not counted as errors" (impl:1021,1033) — never gated; removing its BARE contribution changes only the noise count, no verdict.
- **Consolidation move (preferred over adding machinery)**: delete the `if mod_num is None:` advisory branch (impl:702-710); let Check 25 be the sole bare-cite owner. Net: −22 noise lines/run, one property → one checker. (Alternative, if the impl signal is wanted: have it consult the same allowlist markers — but that ADDS coupling to do worse than the existing Check 25, so deletion is the consolidation-correct fix.)

**confidence**: HIGH (reproduced in the gate run; round 7 independently identified the same overlap).

---

## LOW findings (recorded; each touches a round-7-settled decision — bias held in check)

### C2-2 (LOW, merge) — MANDATE 9 ⊂ MANDATE 18 (self-admitted generalization)
- **Location**: `agent/helpers/verifiers.md:139-152` (M9) vs `:285-302` (M18).
- M18's own text (`:300`) says: "Generalizes MANDATE 9 (cost variables) to ALL interface variables." So 18 subsumes 9's *rule*.
- **But** M9 carries a UNIQUE load-bearing payload M18 does NOT reproduce: the 5-row cost-variable provenance table (`vm_cost_prod_crop`→M38, livestock→M70, pasture→M31, residue→M18, forestry→M32). `rg` confirms this table is not consolidated anywhere else (the M70/M31/M18 facts appear scattered in cross_module docs but not as a cost-attribution table).
- **what_it_protects**: the answer-time guard against the exact R3 bug (5 cost vars wrongly attributed to M38). **who_else_needs_it**: M18 references but does not contain the table; deleting M9 loses the concrete mapping. **blast_radius**: AGENT.md Step-1d short-index lists "cost-variable attribution" as a MANDATE; renumbering 9→merged would require an AGENT.md + deployed-copy edit (hub-status warning, verifiers.md:351).
- **Why NOT pushed**: round-7 verify stage explicitly ruled "No MANDATE demoted — none is fully mechanized; every check-backed MANDATE has a documented coverage gap, so demotion would drop the answer-time guard" (`pipeline_audit_round7.md:25`). M9 is human-review-only (no mechanical guard), i.e. it IS the only guard for cost attribution. Suggested fix is at most: fold M9's table into M18 as a worked sub-example and drop the standalone heading — a doc tidy, LOW value, and only if a maintainer wants fewer MANDATE headings. confidence: MEDIUM.

### C2-3 (LOW, merge) — `validate-module.md` re-implements link/citation checks the gate already owns
- **Location**: `agent/commands/validate-module.md:~45` (Check 3 "Links Validity", inline bash) overlaps `validate_consistency.sh` Check 8 (markdown link targets) and Check 17 (citations).
- **Property overlap**: "do this module doc's links/citations resolve?" — covered both by the per-module command (ad-hoc) and the whole-repo gate.
- **what_it_protects**: targeted single-module validation when a user runs `/validate-module 14`. **who_else_needs_it**: the global gate covers all modules at once; the command is the ONLY per-module-on-demand path. **blast_radius**: none (it's an agent-instruction prompt, not a maintained script; nothing imports it).
- **Why NOT pushed to merge**: the two have different invocation models (interactive single-module vs CI whole-repo) and the command runs greps inline rather than maintaining parallel code — there is no duplicated *artifact* to drift, only duplicated *intent*. Consolidating would couple the command to the script for marginal gain. Suggested fix: have `validate-module.md` Step "Links" say "or run `scripts/validate_consistency.sh` Check 8/17 for the mechanized version" to point at the canonical owner. confidence: MEDIUM.

### C2-4 (LOW, merge) — `migrate_bare_cites.py` re-declares the bare-cite regex instead of importing it
- **Location**: `scripts/migrate_bare_cites.py` BARE regex vs `scripts/check_no_bare_cites.py:33-34` (`BARE_RE`), whose comment literally says "Same bare-cite regex as migrate_bare_cites.py".
- The good pattern in this repo is import-the-shared-engine (e.g. `check_doc_var_existence.py` imports `DOC_VAR_RE` from `check_gams_variables.py`; `check_consumer_attribution.py` imports `GAMS_INTERFACE_RE`). Here the regex is a duplicated literal across the migration tool and its guard, so they can silently drift.
- **what_it_protects**: nothing operational — `migrate_bare_cites.py` is a one-shot migration tool (applied 2026-05-24; the prior round's C4 lens correctly classified it as "one-shot, correctly excluded"). **who_else_needs_it**: only the guard `check_no_bare_cites.py` shares the regex. **blast_radius**: trivial (one literal).
- **Why LOW**: a one-shot tool that won't be re-run rarely drifts in a way that matters. Suggested fix: if `migrate_bare_cites.py` is kept, import `BARE_RE` from `check_no_bare_cites.py` (single source of truth) — or, consolidation-correct, note in BACKLOG that the migration is complete and the tool is archive-ready. confidence: HIGH (the duplication is explicit in the comment).

---

## Clean categories (verified, NOT padded)

1. **Dual .sh/.py twins** — RESOLVED round 7 (I1 @ `65f6718`); re-verified zero twin pairs remain; the lone `check_gams_citations.sh` is a 21-line wrapper (1 `python3` line), intentionally kept.
2. **Realization trio (16/18/19)** — DISJOINT, merge REFUTED round 7 with a synthesized known-bug test. Re-verified: Check 18's inline `(default)` label form is live in ~8 docs (module_13 ×6, _18/_21 ×2, …) so not dormant; Check 19's `Default Realization:` header form is in 45 docs; Check 16 covers all-body month-format tokens. Three properties (token-exists / label-is-default / header+footer+body-cite-validity) on overlapping docs but different assertions.
3. **Identifier-existence (14 vs 21)** — DISJOINT scopes (`modules/module_*.md` vs cross_module+core_docs+helpers+commands+reference); Check 21 IMPORTS the engine from Check 14 (`DOC_VAR_RE`, `build_gams_index`, `filter_doc_vars`). Correct import-don't-duplicate. No third identifier-existence checker exists (only 2).
4. **Consumer-grep MANDATE triad (13/17/20)** — LAYERED, orthogonal failure modes: 13 = completeness (don't under-count), 17 = precision (don't count transitive as direct), 20 = grep-form (grep `.l`/`.lo` too). Each recurred independently (R20/R24/R33). Merging would blur three distinct classes.
5. **Consumer-attribution / units / scaling (22/26/28)** — each a UNIQUE property (consumer COUNT / unit STRING / .scale VALUE); 22 imports 14's index; 28 "mirrors 26's strategy" but on a different property. Parallel structure ≠ redundant coverage.
6. **Shared allowlist infra** — single `audit/advisory_allowlist.json` shared by 2 checkers (param_defaults, multi_section); single `audit/renames.json` for Check 24. No N-copies infra duplication.
7. **Command family (update/sync/validate/validate-semantic/validate-module)** — `update.md` CHAINS to `sync.md` (delegation); `validate.md` (syntactic gate) vs `validate-semantic.md` (adversarial answer-quality flywheel, "the engine") are orthogonal axes; `validate-module.md` is per-module DOC-STRUCTURE (sections present), a different property from the gate's GAMS-fidelity.
8. **Dead-script check** — `probe_dedup_check.py` (live: invoked `validate-semantic.md:193` + selftest:99) and `migrate_bare_cites.py` (one-shot, intentionally excluded) are NOT dead — no false-positive removal proposed.

---

## Method notes / caveats
- Grep discipline per the prompt: every absence claim cross-checked with a second method + the suite was actually RUN (gate + per-checker) so verdicts rest on observed output, not on reading alone. `rg` used (isolated, no chaining) given the known `grep -r` silent-empty hazard in this tree.
- I deliberately did NOT re-propose the realization-trio merge or a MANDATE demotion: both were adversarially settled in round 7 with recorded evidence (synthesized test / "would drop the answer-time guard"). Re-litigating a test-backed decorrelation would be the consolidation-bias overshooting into removing decorrelation that earns its keep.
- The single actionable consolidation (C2-1) REMOVES machinery (−22 advisory lines, one branch) and assigns one property to one owner — fully consistent with the standing DELETE/MERGE bias, and it is round-7's own deferred item, independently re-derived here.
