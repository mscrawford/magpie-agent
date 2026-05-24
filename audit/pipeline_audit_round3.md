# Pipeline Audit Round 3 (R3) — 2026-05-23

**Round type**: Structural audit of the magpie-agent's machinery (re-measure after R2 mechanizations)
**Scope**: 6 lenses, 6 parallel Opus sub-agents, **82 raw findings** (~75 unique after dedup)
**Auditor model**: claude-opus-4-7
**Status**: Triaged + fixed (this session); validators re-passed
**Predecessor**: R1+R2 (`audit/pipeline_audit_round1.md`, R2 in JSON)

---

## Top-line numbers

| Lens | Findings | Notable |
|------|---------:|---------|
| 1. Doc↔code (code-reading) | 20 | **2 CRITICAL** (M38 default-realization mismatch; M73 wrong defaults + stale cites) |
| 2. Doc↔code (empirical-grep) | 10 | **1 CRITICAL** (M11 §17.2 invents 14 cost-var names — corroborates Lens 5) |
| 3. Validator soundness | 12 | citation resolver silent-fallback (HIGH); 3 false-positive cases; 5 false-negative cases |
| 4. Instruction-surface integrity | 13 | validator-count markers stale in 4 files; helpers/README routing table 5+ helpers behind AGENT.md |
| 5. Cross-doc consistency | 15 | **1 CRITICAL** (M11 §17.2 fabrications — corroborates Lens 2); 9 consumer counts off by 1; `pm_timber_yield` fabricated |
| 6. Efficiency | 12 | validator now 8.8s (from 51.7s in R1); 2 bash scripts still slow; ~272KB dead archives |
| **Total raw** | **82** | |

**Severity distribution** (post-dedup, ~75 unique):
- CRITICAL: 3 (M11 §17.2 corroborated; M38 realization; M73 defaults)
- HIGH: 17
- MEDIUM: 30
- LOW: 25

**Comparison to R1 (71 findings, 1 CRITICAL)**: more raw findings (+11) but the CRITICAL count rose from 1 to 3 — confabulation **relocated** rather than diminishing. The Module 18 wrong-realization CRITICAL from R1 was fixed; in its place, two new structural classes emerged:
- **Multi-realization body drift** (M38, M30): docs lead with default-realization header but body content was written against a richer non-default realization (Pattern 8 escalated; Check 19 catches header drift but not body-citation drift)
- **Fabricated identifier templates** (M11 §17.2 with 14 invented `v<modnum>_*`/`vm_cost_<topic>` names following a naming pattern): a class the variable validator (`check_gams_variables.py`) does NOT catch because the names are in backticks of section-bodies that look syntactically valid

---

## Corroborated findings (high-confidence signal)

Three corroborations emerged:

### 1. Module 11 §17.2 fabricates 14 cost-variable names (CRITICAL)
**Lenses**: Lens 2 (empirical-grep) + Lens 5 (cross-doc)
**Independent verification**: `grep -rln "\\bv12_interest\\b\\|\\bvm_cost_natveg\\b\\|..." ../modules/` returns 0 occurrences for all 14 names.
**Why corroborated independently**: Lens 2 hit it from the code→doc direction (M11 references variables that don't exist); Lens 5 hit it from cross-doc direction (Section 17.2 contradicts Section 3 of same file).
**Root cause**: The author wrote Section 17.2 from a template (`v<modnum>_<topic>` or `vm_cost_<topic>`) without grepping for the actual names. Section 3 of the same file lists the real cost variables correctly.
**Action**: fix (see Cluster 3 below).

### 2. Validator check-count markers stale in 4+ files (HIGH)
**Lenses**: Lens 4 (instruction-surface) + Lens 6 (efficiency)
**Evidence**: AGENT.md L618 + L663 + validate.md L15 + L55 + maintenance_protocol.md L21 + L212 + Response_Guidelines.md L286 + validate-module.md L271 all hardcode counts (`18 checks, 33 sub-checks`, or `32 checks`, or `11 patterns`); actual: 20 main / 35 sub-checks; 14 patterns.
**Why corroborated**: Lens 4 came at it from MANDATE-system completeness; Lens 6 came at it from marker-system coverage.
**Root cause**: R2 added the marker system but didn't markerize the specific validator-count strings. New markers (`validator_main_checks`, `validator_sub_checks`) needed.
**Action**: fix (see Cluster 6 below).

### 3. R2's spot-fix on M51 attribution (M50→M55) was incomplete
**Lenses**: Lens 5 (single agent but cross-references R2's JSON log)
**Evidence**: R2 fixed M51.md:40 attribution from M50 to M55 for `vm_manure_recycling`. But M51.md:455 (Upstream Dependencies table) still attributes it to M50 — a row that R2 missed.
**Action**: fix (see Cluster 4 below).

---

## Root-cause clusters (synthetic interventions)

Per `[[feedback_synthetic_interventions]]`: 82 findings collapse to **8 root-cause clusters**, several of which (Clusters 1, 3, 4) drive >30 findings between them.

### Cluster 1 — Multi-realization body drift (escalation of R1 Cluster 1)

**Findings**: ~6 across Lens 1, Lens 2, Lens 4.

**Symptoms**:
- M38 (`modules/module_38.md`): default realization is `sticky_feb18` (4 equations), but body content (Sections 3, 5, 6, 7, 10, 11, 18) describes `sticky_labor` (6 equations including q38_ces_prodfun and q38_labor_share_target). CES content, v38_capital_need / v38_laborhours_need variables, and most parameter tables describe sticky_labor exclusively. **CRITICAL** (matches the R1 anchor severity).
- M30 (`modules/module_30.md`): declarations.gms line citations (L559, 583, 598, 1214, 1222, 1242) point at `detail_apr24` line numbers but header states `simple_apr24` as default. In simple_apr24, `vm_area` is line 18 (doc says 21), `vm_rotation_penalty` is line 19 (doc says 22), `vm_carbon_stock_croparea` is line 20 (doc says 23). The cited line numbers match `detail_apr24` exactly — doc was written against non-default. **HIGH**.
- M80 (`modules/module_80.md`): no dedicated `Parameters (nlp_apr17)` table for the DEFAULT realization. Only `Parameters (lp_nlp_apr17)` table exists, despite distinct declarations (nlp_apr17 has `s80_resolve_option` which lp_nlp_apr17 lacks). **HIGH**.
- AGENT.md L325: "Modules with multiple realizations" list omits Modules 71 (foragebased_aug18, foragebased_jul23, off) and 80 (lp_nlp_apr17, nlp_apr17, nlp_ipopt, nlp_par). Says "20+" — actual is 22. **HIGH**.

**Root cause**: Check 19 (`check_module_realizations.py`) catches header/footer drift but does NOT cross-check body citations or content against the claimed realization. When a doc says header=X but cites line numbers from realization Y, no validator flags it.

**Candidate intervention**:
1. **AGENT.md L325 list**: trivial 5-min fix (add modules 71, 80; update "22 modules").
2. **M38, M30, M80 doc rewrites**: each is a substantial doc revision (~30 min each). Defer M30 + M80 to a future session; flag prominently in module headers.
3. **Mechanization** (LOW priority next mechanization candidate): extend `check_module_realizations.py` to also validate the FIRST 5 file:line citations in the doc against the claimed realization. If a citation's line content matches the OTHER realization's line N but not the claimed realization's, flag as `body-realization-mismatch`.

### Cluster 2 — Fabricated identifiers in backticked prose (NEW class)

**Findings**: ~5 across Lens 1, Lens 2, Lens 5.

**Symptoms**:
- M11 §17.2: 14 fabricated cost-variable names (CRITICAL, corroborated; see above).
- M11 §17.2: `vm_cost_prod` attributed to M38 — doesn't exist (actual: `vm_cost_prod_crop`, `vm_cost_prod_livst`).
- M22 §2.B: code block uses set name `land_natveg` — doesn't exist in `area_based_apr22`; actual is `land_consv` (defined at input.gms:51).
- `core_docs/Module_Dependencies.md:230`: `pm_timber_yield` — doesn't exist in codebase. Likely an interpolation of the "M14 yields → M32" diagram arrow.
- M32: parameter suffix truncation drift (`pm_carbon_density_plantation_ac` vs `pm_carbon_density_plantation_ac_uncalib`).

**Root cause**: `check_gams_variables.py` validates backticked GAMS identifiers, but the validation passes if the identifier exists ANYWHERE in the codebase. It cannot flag identifiers that don't exist anywhere (the M11 case) because the doc-side regex only flags KNOWN variables. Need a different approach: scan all `vm_*`/`pm_*`/`v<N>_*`/`p<N>_*` backticked tokens in module docs and verify each exists in `../modules/*/*.gms`.

**Candidate intervention**: Extend `check_gams_variables.py` to also do a "doc-side strict mode" pass:
- For each backticked `[vmps]<\d*>?_[a-z_]+` token in module docs,
- Verify it exists in `../modules/*/*.gms` (any realization),
- Flag if not found.

This would close the largest single coverage gap exposed by R3 (the 14 M11 §17.2 fabrications would have been blocked at commit time).

### Cluster 3 — Post-PR citation/value drift (chronic class, R1 Cluster 2 recurrence)

**Findings**: ~12 across Lens 1, Lens 2, Lens 5.

**Symptoms**:
- **M73**: post-PR-#869/#872 drift. Wrong cost values (148 → 89, 2.5 → 2.7); wrong residue equation transcription (pre-PR #869 form); stale preloop.gms cites (off by 1-12 lines); stale input.gms cites (s73_residue_removal_cost claimed at line 19, actual line 21). **CRITICAL** (two stale defaults publicly cited).
- **M32**: stale presolve.gms cites (off by 5-7 lines); _uncalib suffix drift in carbon-density params.
- **M22**: stale input.gms cites (f22_wdpa_baseline at :51-57 vs actual :57-61; f22_consv_prio at :59-63 vs :65-69).
- **M11**: 14 cost-variable cites off by 2 from line 31 onward (post-PR-#866 trade-cost split).
- **M21**: k_import21 cited at sets.gms:12-13 but actually at input.gms:12-13 (wrong filename).
- **M73**: Code Size header says "394 lines across 8 files" — actual 415 lines.
- **M32**: Code Size header says "1,313 lines across 11 files" — actual 1,331 lines across 9 files.
- **M51:455**: vm_manure_recycling still attributed to M50 (R2 partial fix).
- **M53:404**: `vm_manure(i,kli,awms_conf,npk)` — wrong set; actual is `awms`.
- **M70:712**: `vm_costs_additional_mon(i,"factor_costs","livst_egg")` — wrong dimensions; actual is `(i)` 1D.

**Root cause**: When MAgPIE PRs land that change line numbers or rename/redimension variables, the agent docs don't get re-synced. R2 enhanced the citation validator (Pattern 12 advisory), but the validator's window (±5 lines, advisory-only) is too narrow for the larger drifts (M73 off by up to 12, M11 off by 2 systematic).

**Candidate intervention**:
1. **Immediate**: spot-fix all enumerated cases above (mechanical edits with grep-verified replacements).
2. **Mechanization**: widen Pattern 12 window to ±15 + add full-file fallback ("found at line X, claimed at Y, off by Z"); already proposed by Lens 3.

### Cluster 4 — Dependency-count drift across cross-cutting docs (R1 Cluster 6 recurrence)

**Findings**: ~8 across Lens 4, Lens 5.

**Symptoms** (recomputed vs claimed):
- Module_Dependencies.md §2.1 (L50-58): 9 consumer counts systematically inflated by 1. Verified `vm_land`: 10 consumers (claim 11); `pm_interest`: 9 (claim 10); `im_pop_iso`: 10 (claim 11). Suggests counts include the producer.
- Module_Dependencies.md L133: M28 → 1 module (actual: 2, since M52 also consumes `im_forest_ageclass`).
- Module_Dependencies.md L137: "25 source modules" provide costs to M11 (actual recount: 27; matches module_11.md L1132 which already says 27).
- Module_Dependencies.md L230: `pm_timber_yield` — fabricated (Cluster 2).
- Module_Dependencies.md L327: "Yields (14) — 5 consumers" (actual: 3 = M30, M31, M17).
- modification_safety_guide.md L46-50: M10 export counts wrong: `vm_lu_transitions` (8 → 3 consumers + producer); `vm_landexpansion` (7 → 4); `vm_landreduction` (6 → 2); `pcm_land` undercounted (5 → 12).
- modification_safety_guide.md L53: "15 Downstream Modules" includes M11, M17, M52, M60, M62, M71 which do NOT directly consume `vm_land`.
- M12 (`module_12.md` L15, 173-176, 836): `pm_interest` consumer list misses M32 + M56 (which use it heavily).
- M35 (`module_35.md` L25): "Provides to" list overstates direct consumers (claims 22, 28, 52, 56 — none directly consume M35 interface vars).
- M15 (`module_15.md` L20): "Provides to Module 16" — actual consumers also include M20, M62.

**Root cause**: Dependency counts hand-coded in multiple files; no recompute hook. R2 spot-fixed 3 counts (Module_Dependencies.md cost vars, modification_safety_guide.md vm_land) but didn't generalize.

**Candidate intervention**:
1. **Immediate**: spot-fix the 9 high-confidence cases above.
2. **Mechanization**: Generic Python checker that for each `vm_*`/`pm_*` reference in `Module_Dependencies.md` and `modification_safety_guide.md`, recomputes consumer count via `grep -l` and flags mismatches >0. ~80 LOC.

### Cluster 5 — Validator soundness: false-positives and false-negatives (NEW class for R3)

**Findings**: ~12 across Lens 3.

**False positives**:
- `check_param_defaults.py` over-fires on `s59_nitrogen_uptake` because the doc converts units (`200 kg N/ha = 0.0002 Mt N/Mha` vs source `0.2 tN/ha`); validator doesn't see unit-conversion intent.
- `check_gams_citations_impl.py` Pattern 12 over-fires on `s32_aff_plantation` in M52:269 because the nearby_ids window inherits an identifier from the prior cite's parenthetical.
- Same false-positive class on `vm_tau` advisory in M14.

**False negatives**:
- `check_module_realizations.py` HEADER_REAL_RE only matches `**Realization**:` (colon outside bold); misses `**Realization:**` (colon inside bold, used in module_11.md) and `# Module N: name (real)` parenthetical headers.
- `check_module_realizations.py` VERIFIED_RE requires `.{1,2}/modules/`; footers like `modules/15_food/anthro_iso_jun22/` (no leading dot, used in M15, M22, M36, M37, M73) are scanned but not validated.
- `check_gams_realizations.sh` realization-name regex requires `monthYY` suffix; misses 12 real realizations (`bii_target, calib, default, exo, nlp_ipopt, nlp_par, off, selfsuff_reduced, selfsuff_reduced_bilateral22, static, sticky_labor, v2`).
- `check_gams_citations_impl.py` silent-fallback: when a full path's realization directory doesn't exist (e.g., `modules/55_awms/bogus/declarations.gms:10`), the resolver falls through to bare-basename lookup and silently launders the fabricated path into a real file. **HIGH** — defeats MANDATE 16.
- `check_gams_variables.py` regex `[vpfisc]\d+_` doesn't cover `ic\d+_`, `oq\d+_`, `ov\d+_` (single-char class); M42's `ic42_pumping_cost`, `ic42_wat_req_k` are unchecked.

**Coverage gaps**:
- Bug_Taxonomy Pattern 5 (Stale References After Renames): only "command:" pattern detected; no generic rename audit.
- Bug_Taxonomy Pattern 6 (Hardcoded Counts Drift): Check 1 only audits Modules 10/11/17.

**Brittleness**:
- Allowlist marker `<!-- check-gams-vars: allow X -->` typos (e.g., underscore instead of dash) silently fail.
- `refresh_aggregate_counts.py` exit code never non-zero on unknown keys → CI pre-commit would silently pass.
- `check_gams_citations_impl.py` warning truncation (`[:5]`) hides Pattern 12 advisories alphabetically below AMBIG advisories.

**Root cause**: Each validator was built incrementally; regex narrowness; advisory-only mode silently truncates.

**Candidate intervention**: targeted fixes per finding. The **HIGH** finding (silent-fallback in citation resolver) is the most important — directly defeats MANDATE 16.

### Cluster 6 — Aggregate-count markers incomplete (R1 Cluster 5 recurrence in a narrower form)

**Findings**: ~6 across Lens 4, Lens 6.

**Symptoms**:
- AGENT.md L618, L663: `(18 checks, 33 sub-checks)` — actual 20/35
- agent/commands/validate.md L15, L55: same
- agent/helpers/maintenance_protocol.md L21, L212: `32 structural checks` — actual 35 sub-checks
- core_docs/Response_Guidelines.md L286: `11 known error patterns` — actual 14
- agent/commands/validate-module.md L271: `All 24 checks passed` (illustrative) — drift
- AGENT.md L659: "two warnings here" — only one warning shown

**Root cause**: R2 added the marker system but didn't markerize the specific validator-count and pattern-count strings that drift most.

**Candidate intervention**:
1. Add `validator_main_checks`, `validator_sub_checks`, `bug_taxonomy_patterns` keys to `refresh_aggregate_counts.py` MARKER_VALUES + `validation_rounds.json.cumulative_stats`.
2. Markerize the ~7 occurrences and refresh.

### Cluster 7 — Instruction-surface drift (NEW)

**Findings**: ~5 across Lens 4.

**Symptoms**:
- `agent/helpers/README.md` L23-32: auto-load routing table 5+ helpers behind AGENT.md L424-444 (missing: verifiers, adding_new_scenario, comparing_model_runs, water_scarcity_scenarios, maintenance_protocol).
- AGENT.md L407: "Phase 5 is mandatory for any GAMS work" — Phase numbering was removed; dangling reference.
- AGENT.md L325: missing modules 71, 80 from multi-realization list (Cluster 1).
- AGENT.md L409, 496, 529, 705: bare `Response_Guidelines.md` references; should be `core_docs/Response_Guidelines.md` (4 occurrences).
- Allowlist marker `<!-- check-gams-vars: allow ... -->`: actively used (M09), undocumented in instruction-surface files. Future-author trap.

**Root cause**: Multiple update-cadence streams (R2 follow-up + R1+R2 own changes + helpers added independently) without a sync pass.

**Candidate intervention**:
1. helpers/README.md L23-32: replace duplicate table with pointer to AGENT.md (single source of truth).
2. AGENT.md L407: rephrase to drop Phase reference.
3. AGENT.md L325: add modules 71, 80.
4. AGENT.md path prefixes: fix 4 bare references.
5. verifiers.md: add note about allowlist marker under MANDATE 7.

### Cluster 8 — Efficiency wins (LOW priority)

**Findings**: ~7 across Lens 6.

**Symptoms**:
- `scripts/check_gams_equations.sh` takes 3.4s (38% of total wall-clock); same bash anti-pattern that made `check_gams_variables.sh` slow before its Python rewrite.
- `scripts/check_gams_realizations.sh` takes 1.0s; same pattern.
- `scripts/validate_consistency.sh.bak` (804 lines) — dead weight from R2 Python rewrite.
- `audit/archive/` (112KB) + `reference/archive/` (160KB) — referenced only in validator skip-paths.
- AGENT.md "LINK DON'T DUPLICATE" section (~75 lines) — editorial guidance; only relevant when editing docs; could be hoisted to `maintenance_protocol.md`.
- AGENT.md trigger overlaps: `realization` keyword fires both verifiers.md AND realization_selection.md (~4000 words of helper context when ~2000 would do); `scenario` substring fires 5 helpers.
- adding_new_scenario.md + realization_selection.md teach the same `cfg$gms$<module>` mechanism redundantly.

**Root cause**: Incremental growth without periodic profiling/pruning.

**Candidate intervention**:
1. **Tier-1 quick wins**: delete `.bak` file; archive directories candidate for removal (defer to user confirmation).
2. **Tier-2 LATER**: Python rewrites of `check_gams_equations.sh` + `check_gams_realizations.sh` — would drop validator wall-clock from 8.8s → ~4.5s.
3. **Tier-3 DEFER**: trigger narrowing; helper consolidation — these are judgment calls.

---

## Recurring classes (candidates for next mechanization)

Per `[[template_verifier_mandate_flywheel]]` — a class with ≥2 instances in this round is a mechanization candidate:

| Class | R3 instances | R1 instances | Trajectory | Next mechanization |
|-------|-------------:|-------------:|------------|--------------------|
| Multi-realization body drift | 4 | 13 (header-only) | NEW class; Check 19 closed header drift; body drift now visible | Extend check_module_realizations.py to scan body citations |
| Fabricated identifiers in backticks | 5 | implicit | NEW prominent class | New `check_doc_var_existence.py` |
| Post-PR citation/value drift | 12 | 10 | RECURRING | Widen Pattern 12 to ±15 + full-file fallback |
| Dependency-count drift | 8 | 7 | RECURRING | Generic Python checker for cross-doc dep counts |
| Validator FP/FN cases | 12 | 17 | DECLINING but persistent | Targeted regex fixes (this session) |
| Marker-system coverage gaps | 6 | 8 | DECLINING (markers exist but not applied) | Markerize validator counts + bug-taxonomy counts |

**Strongest R3 mechanization candidates**:
1. **`check_doc_var_existence.py`** (closes Cluster 2) — scans all backticked GAMS identifiers in docs, verifies each exists. Would have blocked all 14 M11 §17.2 fabrications at commit time. ~80 LOC.
2. **Citation resolver silent-fallback fix** (Cluster 5; HIGH severity defect) — when full-path realization doesn't exist, emit FILE warning instead of silently launder. ~5-line patch.
3. **Validator-count markers** (Cluster 6) — markerize the 7 stale strings. ~30 min mechanical.

---

## Comparison to R1

| Category | R1 | R2 closed | R3 new | Trend |
|----------|---:|----------:|-------:|-------|
| CRITICAL | 1 | 1 (M18) | 3 (M38, M73, M11§17.2) | ↑ ESCALATED |
| Realization-aware (Cluster 1) | 13 | 13 (all footers + M18) | 4 (body drift) | ↘ class shifted from header to body |
| Citation drift (Cluster 2) | 10 | 5 (M13) | 12 | → stable (chronic class) |
| Hoist incomplete (Cluster 3) | 12 | 12 | 1 (LINK-DONT-DUPLICATE bloat) | ↘ ↘ near-complete |
| Validator coverage gaps (Cluster 4) | 8 | 2 (Pattern 12+13 added) | 12 (FPs+FNs in new checks) | → guard surface moved |
| Aggregate-count drift (Cluster 5) | 8 | 8 | 6 (different counts) | → drift class persistent, specific strings differ |
| Cross-doc dep counts (Cluster 6) | 6 | 3 spot | 8 | ↗ R2's spot fixes didn't generalize |
| Interface attribution (Cluster 7) | 7 | 7 | 3 (M51, M53, M70) | ↘ improving |
| Module-specific spot bugs (Cluster 8) | 5 | 5 | 5 (different bugs) | → spot bugs are unavoidable noise |

**Confabulation relocation evidence** (per `[[feedback_confabulation_relocates]]`):
- R2 closed: header/footer realization drift, simple citation drift, hoist completion, aggregate-count drift in audit-doc headers
- R3 shows bugs surfaced at: **body-level realization drift, fabricated identifier templates, dependency-count drift in cross-cutting docs, validator FP/FNs in new code**

This is **textbook** confabulation relocation. Each mechanization closes one surface; bugs move to adjacent unguarded surfaces.

---

## What R3 did (this session)

**Triage decision**: per autonomous-mode rules, fix CRITICAL + HIGH directly; mechanical MEDIUM; document LOW.

**Fixed in this session** (see Status section below for verification).

**Deferred** (with explicit reason):
- M30 + M80 body rewrites (substantial; need their own session)
- M73 q73_prod_residues equation transcription (substantial rewrite of Section 2.1.x)
- Tier-2 validator Python rewrites (check_gams_equations.sh → .py; check_gams_realizations.sh → .py)
- Archive directory removal (asks user permission — 272KB delete)
- AGENT.md "LINK DON'T DUPLICATE" hoist to maintenance_protocol.md
- Helper trigger narrowing (judgment calls)
- New `check_doc_var_existence.py` mechanization (strongest candidate, but adding a new validator script needs separate test/sign-off)

---

## Status (final, post-fix session)

R3 fixes landed in 7 root-cause-cluster commits stacked on plan commit `5708b6f`:

| # | SHA | Cluster | What |
|---|-----|---------|------|
| 1 | `a0ad71a` | C7 | Instruction surface (AGENT.md realization list, helpers/README, verifiers allowlist marker doc) |
| 2 | `7a0ab02` | C4 | Dependency counts (Module_Dependencies §2.1, safety guide, M12/M15/M35) |
| 3 | `ae3763f` | C3 | Post-PR citation/value/dimension drift (M73 CRITICAL defaults, M22, M21, M32, M11, M51, M53, M70) |
| 4 | `49cc6f0` | C2 | M11 §17.2 rewrite (CRITICAL — replaced 14 fabricated names with actual 31 cost variables) |
| 5 | `ecad717` | C1 | Multi-realization body drift header warnings (M38/M30/M80) |
| 6 | `6ba3ed7` | C5 | Validator soundness (citation silent-fallback HIGH; HEADER/VERIFIED regex MED; prefix gap MED) + 5 surfaced cite bugs |
| 7 | `41970b3` | C6 | Markerize 7 validator-count + bug-taxonomy-count strings across 5 files |

**Validator status at session end**:
- `bash scripts/validate_consistency.sh`: **34/35 passed**, 1 known advisory (`s59_nitrogen_uptake` Pattern 13 unit-conversion FP — known, deferred to a future fix per [[feedback_synthetic_interventions]] unit-conversion table)
- `python3 scripts/check_module_realizations.py`: **0 errors, 0 warnings** (64 module docs checked, up from 46 because regex now accepts the `**Realization:**` form too)
- `python3 scripts/check_gams_variables.py`: **100% (953/953 verified)** — up from 944 thanks to R3 regex extension (now covers `ic\d+_`, `oq\d+_`, `ov\d+_` prefixes)
- `python3 scripts/refresh_aggregate_counts.py`: **all markers up to date**

**Deferred to future session(s)** (with explicit reasons, see `audit/next_session_plan.md`):
- M30 + M38 + M80 full body rewrites (substantial; prominent header warnings added as interim mitigation)
- M73 Section 2.1.x equation transcription rewrite (q73_prod_residues uses sum-over-natveg-and-plantation, not just wood)
- Tier-2 validator Python rewrites (check_gams_equations.sh, check_gams_realizations.sh — would drop validator wall-clock from 8.8s → ~4.5s)
- Archive directory removal (272KB; needs user confirmation)
- AGENT.md "LINK DON'T DUPLICATE" hoist to maintenance_protocol.md (judgment call; ~75 lines off AGENT.md)
- Helper trigger narrowing (judgment call; current overlap is intentional but undocumented)
- Strongest next mechanization candidate: **`scripts/check_doc_var_existence.py`** — for each backticked `[vmps]\d*_[a-z_]+` token in module docs, verify it exists in `../modules/*/*.gms`. Would have blocked all 14 M11 §17.2 fabrications at commit time. ~80 LOC.
- Second-strongest: **`check_module_realizations.py` body-citation extension** — scan first 5 file:line citations in body; if they match realization Y while header claims X, flag as `body-realization-mismatch`. ~30 LOC. Would catch the M38/M30/M80 class.

**R3 meta-finding (per `[[feedback_confabulation_relocates]]`)**: R3 produced 82 raw findings vs R1's 71 — MORE findings, not fewer, despite R2 closing 4 surfaces. This confirms the textbook prediction: each mechanization closes one surface; bugs relocate. Specifically:
- **R2 closed**: header/footer realization drift, simple citation drift, hoist incomplete, aggregate-count drift in audit docs
- **R3 found bugs at**: body-level realization drift (M38 CRITICAL), fabricated identifier templates (M11 §17.2 CRITICAL), dependency-count drift in cross-cutting docs, FP/FN in newly-added validators
- **CRITICAL count rose 1 → 3**: not regression — confabulation moved to higher-stakes surfaces (default-realization mismatches in M38 mislead modification-safety reasoning).

This is the audit infrastructure working as designed: measure → mechanize → re-measure exposes where bugs go next, so the next mechanization can target the now-uncovered surface.
