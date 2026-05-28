# Pipeline audit — Round 5 (R5)

**Date**: 2026-05-24
**Commit**: e7bbb39 (HEAD at audit time)
**Auditor**: 6 parallel Opus 4.7 sub-agents, one per lens, run via `/pipeline-audit`
**Context**: R5 follows a major-change session — magpie4 lean scaffolding (d44823f), `/feedback` machinery removal (327116c), `feedback/` → `audit/` rename (1c7df77), and G3+G4 regression questions (e7bbb39). The audit deliberately biased lens 4 toward the new instruction surface; other lenses ran their standard scope on out-of-off-limits modules.

---

## Topline

**Total findings**: 54 across 6 lenses.

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 6 |
| MEDIUM | 16 |
| LOW | 32 |

**By lens**:

| Lens | Findings | HIGH | Notes |
|---|---|---|---|
| L1 doc↔code (reading) | 8 | 2 | Hot-spots: M18 wrong consumer, M30 default-realization drift |
| L2 doc↔code (grep) | 8 | 2 | Hot-spot: M13 interface table multiple issues |
| L3 validator soundness | 12 | 2 | Check 1 vacuous-pass; Check 17 scope gap (Pattern 10) |
| L4 instruction surface | 10 | 0 | Sed-sweep collateral + count drift; AGENT.md / deployed copies clean |
| L5 cross-doc | 9 | 0 | magpie4_reference cross-ref table incomplete; M50/M51 attribution |
| L6 efficiency | 7 | 0 | Validator fork-storms; archive material |

**Surface verified clean** (no findings):
- `diff AGENT.md ../AGENT.md` and `diff AGENT.md ../CLAUDE.md` — both empty.
- All 14 helper "Auto-load triggers" lines match their AGENT.md table rows.
- magpie4_reference.md core claims (106 unique `report*`, line ranges, v2.70.0 @ a360d8c9ec pin, all 80 named functions exist) verified against `.cache/sources/magpie4/R/`.
- 16 MANDATEs in verifiers.md match AGENT.md's short index.
- No active-surface `feedback/` paths or `/feedback` command references survive.
- HTML `<!--count:...-->` markers consistent with cumulative_stats.
- magpie4_reference.md ↔ interpreting_outputs.md reciprocal cross-link is clean (template-worthy).
- Response_Guidelines.md "When the user corrects you" ↔ AGENT.md "Internal iteration loop" mutually consistent.

---

## Root-cause clusters

### Cluster A — Hardcoded count drift (Pattern 6) — 10 findings

Counts written into prose drift from their underlying sources. Recurring class.

| Location | Doc value | Actual | Lens |
|---|---|---|---|
| `audit/validation_rounds.json` `metadata.schema_version` | `"1.1"` | `"1.2"` (latest history) | L4 |
| `README.md:107` "6 commands" | 6 | 10 | L4 |
| `README.md:107` "9 helpers" | 9 | 14 | L4 |
| `modules/module_09.md:228` im_development_state "Used by: 6 modules" | 6 | 5 (12, 18, 42, 55, 56) | L1 |
| `modules/module_53.md:1067` k_conc53 "24" | 24 | 27 | L1 |
| `modules/module_60.md:282-289` scenario family counts | R21M42=18, R32M46=16, R34M410=12, SSPDB=38 | 20, 15, 15, 22 | L1 |
| `modules/module_30.md:155,510` rotamax30 "29" | 29 | 30 | L1 |
| `modules/module_36.md:501 vs :572` | 6 vs 2 (internal inconsistency) | 3 downstream + ~4 upstream | L1 |
| `core_docs/Module_Dependencies.md:139 vs :269` cost vars | 31 vs 32 (internal) | 32 (per module_11.md) | L5 |
| `core_docs/Module_Dependencies.md:16-18` interface vars | 81/19/15 = 115 | 83/21/17 = 121 (post PR #866) | L5 |

**Proposed intervention**: extend the `<!--count:foo-->N<!--/count-->` HTML-comment marker mechanism (already in use for validator_main_checks, total_rounds, etc.) to GAMS set counts and module-count claims. `scripts/refresh_aggregate_counts.py` computes them from the canonical sources (`../modules/*/sets.gms`, declarations.gms grep). One added marker per claim closes the recurrence.

### Cluster B — Stale file:line citations (Pattern 10) — 7 findings + scope gap

| Location | Cited | Actual |
|---|---|---|
| module_13.md:141 `pm_interest` source | `declarations.gms:26` (in M13) | Module 12 `select_apr20/declarations.gms:9`; M13 line 26 is `pc13_land(i,tautype)` |
| module_13.md:142 `pcm_land` | `presolve.gms:9-10` | `presolve.gms:8-9` |
| module_13.md:142 `pm_land_conservation` | `presolve.gms:41` | `presolve.gms:40` |
| module_34.md:512 vm_land bounds | `presolve.gms:12-14` | `presolve.gms:13-15` |
| module_57.md:166 N₂O conversion | `preloop.gms:24` | `preloop.gms:25` |
| module_57.md:167 CH₄ conversion | `preloop.gms:25` | `preloop.gms:26` |
| module_31.md:376 `s31_fac_req_past` reset | `equations.gms:34-35` (comment) | `postsolve.gms:10` |

**Scope gap discovered**: `scripts/check_gams_citations_impl.py:64` only scans `agent_dir/modules/`. Citations in `cross_module/*.md`, `core_docs/*.md`, `agent/helpers/*.md`, `agent/commands/*.md`, `reference/*.md`, `AGENT.md`, and `README.md` are NOT validated. Pattern 10 was the **biggest historical bug class (151 bugs)** and is unprotected outside module-docs where most modification activity now happens.

**Proposed intervention**: one-line scope extension in `check_gams_citations_impl.py` — add the missing directories to the scan list. The downstream logic does not require module-doc structure.

### Cluster C — Default-realization discipline (Pattern 8 body-scope FN) — 3 findings

| Location | Issue |
|---|---|
| `modules/module_30.md` body (§3-§5) | Describes detail_apr24 penalty equations (q30_rotation_max2, v30_penalty, ...) as if default. Default is `simple_apr24` which lacks those entirely. R3 banner acknowledges; body unfixed since R3 (2026-05-23). |
| `modules/module_80.md:35` + `core_docs/Module_Dependencies.md:138` | Module 80's `vm_landdiff` dependency listed without scoping. `vm_landdiff` is consumed only by non-default `lp_nlp_apr17`; default `nlp_apr17` minimizes only `vm_cost_glo`. Violates AGENT.md "lead with default" rule. |
| `scripts/check_gams_realizations.py:65-96` (Check 16) | Realization names verified globally, not per-module. A doc citing `select_apr20` (M12 realization) in a `module_70.md` body context would pass. Latent FN. |

**Proposed intervention**:
- Complete the M30 body rewrite that's been pending since R3.
- Realize-scope the M80 mentions.
- Make Check 16 module-aware: index realizations by `{module_num: {realization_name}}`, look up M-scoped citations only in their own module's set.

### Cluster D — Sed-sweep collateral from feedback→audit rename — 5 findings (all LOW)

Commit 1c7df77 ran `sed 's|feedback/|audit/|g'` across all .md/.py/.sh/.json. This correctly rewrote path references but also rewrote the historical narrative referring to the OLD name `feedback/` — producing nonsensical `audit/ → audit/` text and stale "rename will happen" comments.

| Location | Sed-sweep damage |
|---|---|
| `audit/README.md:5` | Blockquote says "directory will be renamed `audit/`" — the rename already happened |
| `audit/README.md:32` | File-tree comment shows nonsensical `audit/ → audit/` rename |
| `audit/agent_simplification_plan.md:1, 17, 70, 74, 133` | Title + section headers + acceptance criteria all read `audit/ → audit/` |
| `audit/magpie4_scaffolding_plan.md:22` | Preserves discredited "108 unique / `if/grepl` dispatch" claim that the helper corrected to "106 / flat tryList" |

**Proposed intervention**: targeted edits restoring `feedback/` on the LEFT side of historical `→ audit/` descriptions. Add a "post-execution correction" note to magpie4_scaffolding_plan.md noting the helper's accurate figures supersede §22.

### Cluster E — Validator infrastructure gaps — 6 findings

| Location | Issue | Severity |
|---|---|---|
| `validate_consistency.sh:88-134` (Check 1) | `grep ... \| wc -l` returns 1 on empty input → vacuous PASS. Three "consistent" claims meaningless. | HIGH |
| `check_gams_citations_impl.py:64` (Check 17) | Scope is `modules/` only; Pattern 10 unprotected in cross_module/, core_docs/, etc. (see Cluster B). | HIGH |
| `check_gams_realizations.py:65-96` (Check 16) | Global, not module-aware (see Cluster C). | MEDIUM |
| `check_doc_var_existence.py:45` (Check 21) | SCAN_DIRS excludes `reference/`; 19 fabricated identifiers found there. | MEDIUM |
| `probe_dedup_check.py:106,116` | `--round=99` default rotates everything back in → 0 off-limits at default. Help text says default = "all off-limits" — inverted. | MEDIUM |
| `core_docs/Bug_Taxonomy.md:294-295` | Patterns 12+13 marked "Manual" but Check 17 (partial advisory) and Check 20 (full) exist. Stale. | LOW |

**Proposed intervention**: per-check fixes per L3's report. Highest-leverage: Cluster B scope extension (closes biggest FN class) + fix Check 1 emptiness handling.

### Cluster F — magpie4_reference.md "Module cross-references" table incomplete — 2 findings (MEDIUM)

| Row | Currently lists | Missing |
|---|---|---|
| `reportEmissions / reportFireEmissions / reportBiochar` | M51, M52, M56, M57 | M53 (methane), M55 (AWMS), M58 (peatland), M59 (SOM) — all directly read by reportEmissions.R |
| `reportLandUse / reportCroparea / reportPeatland` | M10, M29, M30, M58 | M31 (pasture), M32 (forestry), M34 (urban), M35 (natveg) — all read by reportLandUse.R |

**Root cause**: helper written from memory of magpie4 dispatch rather than derived from actual `reportX.R` contents.

**Proposed intervention**: re-derive table by grep'ing `.cache/sources/magpie4/R/report*.R` for the gdx-readers / IAMC variables each function emits, then map to the corresponding GAMS module docs. Could be automated.

### Cluster G — Consumer/provider misattribution — 2 findings

| Location | Doc claim | Actual |
|---|---|---|
| `modules/module_18.md:403, ~486` | `vm_res_ag_burn` consumed by M50 (nitrogen budget), M57 (GHG emissions) | M51 (nitrogen), M53 (methane) — verified by grep |
| `cross_module/nitrogen_food_balance.md:32` | Mineral Fertilizer attributed to Module 51 | `vm_nr_inorg_fert_reg` declared in Module 50 (verified) |

**Proposed intervention**: extend Check 22 (consumer-count attribution) to also flag wrong-module attribution. Could grep declarations.gms for the variable and verify the doc's "from Module X" matches the actual declaration's module number.

### Cluster H — Trigger keyword overlaps — 2 findings (LOW)

| Pair | Overlap |
|---|---|
| `interpreting_outputs.md` ↔ `magpie4_reference.md` | Bare "report.mif" substring matches both. Probably intentional sibling-scoping (explicit reciprocal cross-link exists). |
| `verifiers.md` ↔ `realization_selection.md` | "default realization" exact-keyword overlap. verifiers should win for the active-realization-check; realization_selection should fire only for choice-oriented queries. |

**Proposed intervention**: tighten `realization_selection.md` triggers to drop "default realization" (keep "which realization", "choose realization", etc.). The interpreting_outputs ↔ magpie4_reference overlap is fine as-is.

### Cluster I — Variable signature mismatches — 3 findings (MEDIUM)

| Location | Doc signature | Actual |
|---|---|---|
| `module_55.md:242,252,501` | `vm_feed_intake(i,kli,feed_type)` | `vm_feed_intake(i,kap,kall)` (declared in M70/fbask_jan16/declarations.gms:18); kli is iteration subset only |
| `module_13.md:141` | `pm_interest(t,i)` | `pm_interest(t_all,i)` |
| `module_12.md:224-230` | `p12_interest_select(t,i)` listed as declared in declarations.gms | Actually implicitly declared via assignment in `preloop.gms:21`; dimension `(t_all,i)` |

**Proposed intervention**: build a check that verifies dimension signatures in interface-variable doc tables against declarations.gms.

### Cluster J — Validator fork-storms — 2 findings (LOW)

| Check | Time | Subprocesses |
|---|---|---|
| Check 7 (naming conventions) | 4.3s (36% of total) | ~298 grep forks |
| Check 13 (unclosed code blocks) | 2.3s (19% of total) | 145 grep forks |

**Proposed intervention**: Python port (precedent: `check_gams_variables.sh` → `.py` migration achieved 100× speedup at R3-followup). Expected: 6.6s of validator runtime reclaimed.

### Cluster K — Archive material — 1 finding (LOW)

`audit/archive/` (108KB, 11 files) documents the now-removed `/feedback` workflow. Zero live references. WORKFLOW_GUIDE.md and integrate-feedback.md reference `audit/pending/` which no longer exists.

**Proposed intervention**: (a) delete (history is in git) OR (b) add `audit/archive/README.md` disclaiming the contents as historical, superseded by 327116c. (b) preserves the design history.

### Cluster L — `sync_magpie4_clone.py` exit-code semantics — 2 findings

| Issue | Severity |
|---|---|
| Silent HEAD-downgrade on `git fetch` failure → writes `resolution: "head"` to version_pins.json, exits 0. Callers cannot detect. | MEDIUM |
| `--check` returns exit 1 for BOTH "not cloned" AND "misaligned SHA" — caller cannot distinguish "never cloned" from "drifted cache". | LOW |

**Proposed intervention**: distinct exit codes (0 aligned, 1 misaligned, 2 not cloned) and either exit 1 OR refuse to write version_pins.json when resolution != "sha" (caller must explicitly accept downgrade).

---

## Recurring classes (candidates for mechanization)

Per `[[template_verifier_mandate_flywheel]]`: each closed class via a new validator check binds the rule and prevents silent re-occurrence.

| Recurring class | Cluster | Mechanization candidate |
|---|---|---|
| Pattern 6 — hardcoded count drift | A | Extend `<!--count:foo-->N<!--/count-->` macro to GAMS set counts; refresh_aggregate_counts.py computes |
| Pattern 10 — stale file:line citations | B | Extend Check 17 scope to all doc directories (one-line scope list edit) |
| Pattern 8 — body-doc realization scope-coupling | C | Make Check 16 module-aware |
| Consumer/provider misattribution | G | Extend Check 22 to verify the "from Module X" attribution against declarations.gms |
| Variable signature mismatches | I | New check: parse interface-variable doc tables, verify dimensions match declarations.gms |

---

## Top concerns (priority order)

1. **Cluster B + L3 Check-17 scope gap** — Pattern 10 was the largest historical bug class (151 bugs); the validator's coverage gap leaves cross_module/, core_docs/, AGENT.md citations unchecked. One-line fix → broad protection.
2. **Cluster G — wrong consumer attribution in module_18.md and nitrogen_food_balance.md** — if a user trusted these attributions for a code modification, they'd edit the wrong module.
3. **Cluster F — magpie4_reference.md cross-ref table** — would mislead users looking for module-doc context for IAMC variables.
4. **Cluster A — count drift** — many small bugs that compound user trust erosion.
5. **Cluster D — sed-sweep collateral** — easy targeted cleanup.

---

## Proposed next steps (user decides)

Per command spec, "Phase 'fix + mechanize' is reviewed with the user before execution — do NOT proactively fix." Fix order suggestion:

**Phase 1 — high-leverage spot fixes (~30 min)**:
- Cluster A: fix the schema_version drift (1 line), README.md counts (2 numbers), Module_Dependencies.md cost vars (1 number), im_development_state count, k_conc53, module_60 family counts.
- Cluster G: fix module_18.md and nitrogen_food_balance.md consumer attributions.
- Cluster F: re-derive magpie4_reference.md cross-ref table from getReport.R dispatch.
- Cluster D: targeted sed-sweep cleanup.

**Phase 2 — mechanize the recurring classes (~1-2 hr)**:
- Extend Check 17 (citations) scope to all doc directories.
- Make Check 16 (realizations) module-aware.
- Add Bug_Taxonomy.md mention of the new mechanizations.
- Extend Check 22 (consumer attribution) to flag wrong-module claims.

**Phase 3 — opportunistic cleanup (~30 min)**:
- Fix `sync_magpie4_clone.py` exit codes / HEAD-downgrade detection.
- Tighten realization_selection.md triggers.
- Decide on audit/archive/ — delete or disclaim.
- Update Bug_Taxonomy.md Pattern 12+13 statuses.

**Phase 4 — performance (deferred)**:
- Port Check 7 + Check 13 to Python (6.6s reclaim).

**Phase 5 — completing R3 work**:
- Module 30 body rewrite against simple_apr24.

---

## Logging

Round entry appended to `audit/pipeline_audit_rounds.json` (schema mirrors R4).
This report: `audit/pipeline_audit_round5.md`.
