# Pipeline Audit Round 1 (R1) — 2026-05-23

**Round type**: Structural audit of the magpie-agent's machinery
**Scope**: 6 lenses, 6 parallel Opus sub-agents, ~71 findings total
**Auditor model**: claude-opus-4-7
**Status**: Triaged; fix + mechanize deferred to follow-up session (per user scope choice)

---

## Top-line numbers

| Lens | Findings | Notable |
|------|---------:|---------|
| 1. Doc↔code (code-reading) | 11 | **1 Critical** (Module 18 wrong-realization); 13/46 footers fabricated |
| 2. Doc↔code (empirical-grep) | 8 | Module 13 input.gms citation cluster (6 refs off by 35-45 lines) |
| 3. Validator soundness | 17 | Pattern 12 + Pattern 13 ZERO coverage; 94% citations are bare basenames |
| 4. Instruction-surface integrity | 19 | Stale counts everywhere; 11/16 MANDATEs unenforceable |
| 5. Cross-doc consistency | 9 | 6 Major attribution/dimension/count bugs |
| 6. Efficiency | 7 | Hoist underdelivered (7% reduction); 91% of validator time in one script |
| **Total** | **71** | |

**Severity distribution** (mapped to the rubric's 4-tier scale):
- CRITICAL: 1
- HIGH/Major: 14
- MEDIUM/Minor: 38
- LOW/Informational: 18

**The audit caught a confabulation introduced in this very session** — Lens 1 found that MANDATE 8's worked example in the freshly-hoisted `agent/helpers/verifiers.md` itself fabricates a realization name (`fbask_jul23`); the actual default is `fbask_jan16`, and `fbask_jul23` does not exist anywhere in the repo. This is exactly the failure mode the audit infrastructure exists to catch.

---

## Corroborated findings (high-confidence signal)

When the same defect is reported by ≥2 lenses, that's corroboration — not noise. Two corroborations emerged:

1. **Hoist underdelivered** (Lens 4 + Lens 6)
   - Lens 4: AGENT.md only shrank 10 lines (889→879), not the ~150 the pipeline-audit.md Lens 6 guidance predicted.
   - Lens 6: AGENT.md -7% (-477 words), but verifiers.md +1,888 words; with the broad `"module"` trigger the helper auto-loads on essentially every session — net token cost per session went **UP**, not down. AGENT.md still has a `CRITICAL WARNINGS` section (lines 606-635) that duplicates MANDATEs 7, 8, 16.
   - **Action**: this cluster's root fix is part of Cluster 3 below.

2. **Realization-aware verification gap** (Lens 1 + Lens 3 + Lens 5)
   - Lens 1: 13/46 (28%) module docs have `Verified Against:` footers pointing at nonexistent or non-default directories. Module 18 describes the non-default realization as if active (CRITICAL).
   - Lens 3: realization regex misses 20/59 non-month-format names (`default`, `static`, `off`, `nlp_ipopt`, `bii_target`, etc.) — those names are uncheckable.
   - Lens 5: Module 53.md uses wrong set (`kli` vs actual `kap`) for `vm_feed_intake` — a realization-aware variable check would catch this.
   - **Action**: this cluster's root fix is Cluster 1 below.

---

## Root-cause clusters (synthetic interventions)

Per `[[feedback_synthetic_interventions]]`: prefer the root fix over symptom patches. The 71 findings collapse to **8 root-cause clusters**, two of which (Clusters 1 and 3) drive >30 findings between them.

### Cluster 1 — Realization-aware verification missing (highest leverage)

**Findings**: ~20 across Lens 1, Lens 3, Lens 5.

**Symptoms**:
- Module 18 doc describes the non-default `flexcluster_jul23` realization as active (12 cluster-level equations) when the default `flexreg_apr16` has 9 regional equations. **CRITICAL** per the rubric's anchor.
- 13/46 module docs have stale or fabricated `Verified Against:` footers (Modules 09, 17, 28, 31, 44, 45, 50, 51, 53, 55, 57, 58, 59).
- MANDATE 8 worked example in the freshly-written `agent/helpers/verifiers.md` claims livestock default is `fbask_jul23` — that realization doesn't exist; actual default is `fbask_jan16`.
- `probe_dedup_ledger.json` (also fresh) carries the bad `fbask_jul23` name forward.
- Realization regex in `scripts/check_gams_realizations.sh:33` only matches month-format names; misses `nlp_ipopt`, `static`, `default`, `bii_target`, etc.
- `scripts/check_default_realizations.py:88-128` only catches three phrasings; misses `Realization: X (default)`.

**Root cause**: no validator cross-checks that (a) each module doc's claimed realization matches `config/default.cfg`, AND (b) the realization directory exists, AND (c) the documented equations/variables are present in that specific realization.

**Candidate intervention**: extend `scripts/validate_consistency.sh` with a **single new check** that for every `modules/module_XX.md`:
1. Extract the `Realization:` header (and any `Verified Against:` footer path).
2. Cross-reference against `grep "cfg\$gms\$<module>" ../config/default.cfg` for the actual default.
3. Verify the realization directory exists (`ls ../modules/XX_*/<realization>`).
4. Flag any mismatch as ERROR.

Estimated effort: ~80 LOC Python; closes 13 footer bugs + Module 18 + the MANDATE 8 fabrication detection + future drift in one pass. This is the strongest mechanical-guard candidate from R1.

### Cluster 2 — Citation drift (recurring class)

**Findings**: ~10 across Lens 2, Lens 3.

**Symptoms**:
- Module 13's 6 input.gms citations all off by 35-45 lines (file grew when conservation scalars added; citations not re-derived).
- Module 13's `q13_tau` and `q13_tau_consv` equation citations both drifted.
- 94% of file:line citations are bare basenames (no realization path) — silently resolved by walk-order; multi-realization modules like Module 38 may silently pick the wrong file.
- 61% of citations are ranges (`equations.gms:36-56`); the checker only validates the start, ignores the end.
- Pattern 12 (Content-Level Citation Mismatch) has **zero validator coverage**. Probe confirmed: `module_52.md` cites `q52_emis_co2_actual at equations.gms:19`, but actual line 19 reads something completely different.

**Root cause**: citation checker is a line-range validator only, not a content validator. Combined with the bare-basename ambiguity, this is the largest single coverage gap.

**Candidate intervention**: rewrite `scripts/check_gams_citations_impl.py` to:
1. Parse end-of-range (`:NN-MM` → check both NN and MM).
2. When a citation is adjacent (within ~80 chars) to a backticked identifier, grep the cited line ±5 for that identifier; flag mismatch.
3. When a bare basename matches multiple realizations, WARN explicitly with the candidate list.

Estimated effort: ~150 LOC Python; closes the largest coverage gap.

### Cluster 3 — Hoist incomplete (this session's work)

**Findings**: ~12 across Lens 1, Lens 4, Lens 6.

**Symptoms**:
- AGENT.md -10 lines (not ~150 predicted) — the hoist created a 25-line short-index table that duplicates the MANDATE summaries.
- `CRITICAL WARNINGS` section (AGENT.md:606-635) still carries content from MANDATEs 7, 8, 16.
- `verifiers.md` auto-load trigger keyword `"module"` is so broad it fires constantly; combined with the 1,888-word helper, net token cost per session is HIGHER than pre-hoist.
- MANDATE 8 worked example fabricates `fbask_jul23` (cross-cluster with Cluster 1).
- `verifiers.md:224` hardcodes `<magpie-agent>` — not portable.
- MANDATE 16 name mismatch: AGENT.md says "post-merge lines"; verifiers.md says "post-merge line numbers".
- `validate-semantic.md` doesn't mention the schema_version 1.1 bump or the new `regression_questions` array.
- `audit/README.md` doesn't list 4 new top-level files (flywheel_rubric.md, validation_rounds.json, pipeline_audit_rounds.json, probe_dedup_ledger.json).
- 11 of 16 MANDATEs have no mechanical guard (M1, M2, M3, M4, M5, M6, M9, M10, M11, M12, M13) — pure aspirational text.

**Root cause**: the hoist was structurally sound (numbering, deployed-copy diff, auto-load wiring) but didn't go far enough — content was duplicated rather than moved, triggers were too broad, and downstream docs weren't updated.

**Candidate intervention** (single follow-up session):
1. Drop `"module"` and `"equation"` from verifiers.md triggers; keep narrow triggers only.
2. Delete the `CRITICAL WARNINGS` section in AGENT.md (now redundant with verifiers.md).
3. Fix MANDATE 8 worked example (use `fbask_jan16` as the actual default).
4. Replace `~/...` path in verifiers.md with portable form.
5. Reconcile MANDATE 16 name.
6. Add schema 1.1 note to validate-semantic.md.
7. Update audit/README.md directory structure.
8. Mark each MANDATE explicitly with "Verified by: <script> | human review only".

### Cluster 4 — Validator coverage gaps (structural)

**Findings**: ~8 across Lens 3.

**Symptoms**:
- Pattern 12 (Content-Level Citation Mismatch) — 0% coverage; second-largest historical bug class.
- Pattern 13 (Wrong Parameter Default Value) — 0% coverage.
- `c<N>_*` (scenario switches), `cm_*` (interface config), `sm_*` (interface scalar) prefixes missing from GAMS-index regex — completely unchecked.
- 82% of variable references in docs are unbacktiked prose; entirely unchecked.
- Check 1 (dependency counts) only audits Modules 10, 11, 17 — 43 other modules' count claims could drift undetected.

**Root cause**: the validator was built incrementally; each check has narrow scope and the union doesn't cover the failure surface.

**Candidate intervention**: add three new Python checkers — `check_param_defaults.py`, `check_citation_content.py`, `check_unbacktiked_gams.py`. Extend regex in `check_gams_variables.sh` for `c<N>_*`/`cm_*`/`sm_*`. Generalize Check 1 to all 46 modules.

### Cluster 5 — Stale aggregate counts everywhere (drift surface)

**Findings**: ~8 across Lens 4.

**Symptoms** (canonical value in parentheses):
- "17 checks, 32 sub-checks" → actually **18 / 33** (AGENT.md:618, 687; validate.md:15, 48)
- "291 bugs" → actually **445** (AGENT.md:329; verifiers.md:3; pipeline-audit.md:19; validate-semantic.md:218)
- "213 bug fixes" → actually **297** (AGENT.md:610)
- "13 documented patterns" → actually **14** (AGENT.md:653)
- "~290,000 words" → actually **~342,000** (AGENT.md:485; guide.md:13)
- "13 rounds" → actually **21** (validate-semantic.md:218)
- /guide shows 6 of 11 commands (missing /explain, /trace, /update, /bootstrap, /validate-semantic, /pipeline-audit)
- validate-semantic.md metrics table stops at R13 (8 rounds stale)
- flywheel_rubric.md numbering skips §9

**Root cause**: counts hardcoded in multiple places; no mechanism keeps them in sync.

**Candidate intervention**: a single mechanical pass via `scripts/refresh_aggregate_counts.py` that reads canonical values from `audit/validation_rounds.json.cumulative_stats` + `wc -w` and updates a few well-defined doc placeholders. Alternative: drop precise numbers; use "21 rounds" → "21+ rounds" → cite cumulative_stats as the authoritative source.

### Cluster 6 — Cross-doc dependency-count drift

**Findings**: ~6 across Lens 5.

**Symptoms**:
- Module 11 dependency count internally inconsistent in its own doc (19, 27, 27) AND wrong vs code (32).
- Module 10 says "15 critical consumers of vm_land" but actual is **10** (5 of the 15 listed modules don't even reference vm_land).
- modification_safety_guide.md says "ALL 15 consumers" — same drift as Module 10.
- Module_Dependencies.md framing ambiguity for vm_carbon_stock (8) and vm_bv (7) — counts include the producer module.

**Root cause**: dependency counts hand-coded in multiple files; no recompute hook.

**Candidate intervention**: a single Python pass that recomputes consumer counts via `grep -l` and updates the four affected files.

### Cluster 7 — Cross-doc interface attribution / dimension drift

**Findings**: ~7 across Lens 1, Lens 2, Lens 5.

**Symptoms**:
- Module 51.md attributes `vm_manure_recycling` to Module 50; actually Module 55.
- Module 53.md declares `vm_feed_intake(i,kli,kall)`; actually `(i,kap,kall)`.
- Module 14.md still references `vm_tau(h,...)` post-f_btc2; actual is `vm_tau(j,...)`.
- carbon_balance_conservation.md:101 drops the `stockType` dimension from `vm_carbon_stock` (4D actual, doc shows 3D).
- Module 29.md drops the `w` dimension from `vm_area` in dependency section.
- Module 51.md cites declarations.gms:9-16 for `vm_emissions_reg` — that's Module 56's variable, not Module 51's.
- Module 39.md simplifies the equation, dropping the `sum((ct,cell(i2,j2)),...)` aggregation.

**Root cause**: when interface variables get renamed/re-dimensioned in code, the docs that describe them from a consumer perspective drift. No automated cross-check of interface-variable dimensions across docs.

**Candidate intervention**: a Python checker that for each `vm_*`/`pm_*` reference in a module doc, looks up the declared dimensions in the producer module's `declarations.gms` and flags mismatches.

### Cluster 8 — Module-specific spot bugs

**Findings**: ~5 spot bugs that don't cluster cleanly.

**Symptoms**:
- Module 44 claims "71 biomes"; actual `biome44` set has **70** elements (Lens 1).
- Module 60 missing default-state for `c60_biodem_level = 1 (regional)` (Lens 1).
- Module 42 unit inconsistency: `vm_water_cost` labelled `USD17MER per m^3` (GAMS-side typo) but computed unit is `USD/yr` (Lens 1).
- Module 45 climate-type count internally inconsistent (30 vs 31; actual is 31) (Lens 2).
- Module 17 imprecise region count "10-14" (actual 12) (Lens 2).

**Root cause**: hand-counted assertions in module docs without mechanical verification.

**Candidate intervention**: this overlaps with Cluster 5 and Cluster 4 (Pattern 13 coverage). One-off fixes for the spot bugs; the structural improvement is in Cluster 4.

---

## Recurring classes (candidates for mechanization)

Per `[[template_verifier_mandate_flywheel]]`, a class with ≥2 instances in a measurement round is a candidate for a mechanical guard. R1 surfaces 4 strong candidates:

1. **Stale realization name** (Cluster 1, 13+ instances) → realization-validity validator
2. **Citation content mismatch / line drift** (Cluster 2, 10+ instances) → citation content validator
3. **Stale aggregate count** (Cluster 5, 8+ instances) → aggregate-count refresh script
4. **Cross-doc dependency / dimension drift** (Cluster 6, 7, ~13+ instances) → interface-variable consistency checker

These are the **mechanize** candidates for the follow-up session. Per user scope choice, R1 stops at triage; mechanization is reviewed with the user before execution.

---

## Performance findings (Lens 6)

- `bash scripts/validate_consistency.sh` wall-clock: **51.7s total**, of which `check_gams_variables.sh` alone takes **47.2s (91%)** due to a nested per-variable grep loop (~2,300 subprocess invocations). A Python rewrite would drop total time to <10s.
- `audit/archive/` (112K) and `reference/archive/` (160K) contain stale planning docs referenced only in validator skip-paths. Candidate for removal.

---

## What R1 deliberately did NOT do

- Did not fix any findings (per user scope choice — "build + run + triage only").
- Did not mechanize any guards (mechanization requires ≥2 recurrences AND a planning decision; that's the follow-up cycle).
- Did not redesign the rubric or MANDATE structure (audit measures the current surface; redesign would invalidate the measurement).

---

## Suggested next session

The clear winners from R1 are:

1. **Cluster 1 root fix (realization-validity validator)** — single check, ~80 LOC, closes ~20 findings.
2. **Cluster 3 root fix (complete the hoist)** — single doc-editing session, closes ~12 findings, including the most embarrassing finding (MY own MANDATE 8 fabrication).
3. **Cluster 5 root fix (aggregate-count refresh)** — single script, ~50 LOC, closes ~8 findings.

Together these three closing actions address ~40 of 71 findings via 3 root interventions. Clusters 2, 4, 6, 7 are higher-effort but high-leverage; reserve for a second follow-up session.

The remaining ~31 findings (mostly LOW-severity spot bugs and edge-case validator logic issues) are best batched into a "doc-cleanup pass" once the structural fixes are in.
