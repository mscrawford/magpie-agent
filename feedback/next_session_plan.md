# Next Session Plan — magpie-agent

**Origin**: deferred items from the 2026-05-23 R1+R2+R3 lens-audit + fix sessions (`feedback/pipeline_audit_round1.md`, `feedback/pipeline_audit_round3.md`, `feedback/pipeline_audit_rounds.json`).

**Context**: R3 closed Clusters 1 (partial — headers added; full body rewrites deferred), 2, 3, 4, 5, 6, 7, 8 (partial — .bak deleted; archives + Python rewrites deferred). 82 findings → ~70 addressed (CRITICAL+HIGH all fixed except M30/M80 body rewrites which got prominent header warnings; LOW mostly documented not fixed). All validators pass (34/35, 1 known advisory).

Per [[feedback_confabulation_relocates]] — R3 confirmed confabulation relocated from header drift (R1+R2-closed) to body-citation drift (new class), fabricated-identifier templates (new class), and dependency-count drift in cross-cutting docs (recurring). Each closure pushes bugs to adjacent unguarded surfaces.

---

## Progress log (2026-05-23 follow-up session)

**Tier 1 — done**:
1. ✅ Module 18 full body rewrite — replaced flexcluster_jul23 walkthrough with default `flexreg_apr16` (9 regional equations). `flexcluster_jul23` moved to clearly labelled Alternative Realization section. Commit `8932040`.
2. ✅ Pattern 13 validator (`scripts/check_param_defaults.py`) — wired as Check 20, advisory. 1 remaining advisory (`s59_nitrogen_uptake` unit-conversion case). Commit `8932040`.
3. ✅ GAMS variable regex extension — added `c<N>_`, `sm_`, `cm_` to GAMS-index and doc-side regexes in `check_gams_variables.sh`. Surfaced + fixed real confabulation: M56 cited fabricated `sm_cdr_target` (replaced with actual price-driven CDR mechanism). Commit `8932040`.

**Tier 2 — done**:
4. ✅ Python rewrite of `check_gams_variables.sh` (`scripts/check_gams_variables.py`) — ~50x speedup (52s → 6s for full validator). Bash kept as thin wrapper. Tighter wildcard filter surfaced 2 more issues (M09 `im_gdp_pc_ppp` real bug, M57 `f57_maccs_<type>` template placeholder — now handled via template detection + per-doc `<!-- check-gams-vars: allow ... -->` markers). Commit `88eee98`.
5. ✅ Pattern 12 advisory cleanup — went from 25 advisories to 2 legitimate false positives. Two interventions: (a) tighter heuristic (40-char-back / 10-char-forward window per citation, no cross-attribution between siblings); (b) citation resolver fix to honor realization-prefix paths (`flexreg_apr16/equations.gms` no longer silently resolves to `flexcluster_jul23/equations.gms` via walk-order). Fixed 5 real drift/wrong-file cases. Commit `41d92b2`.
6. ✅ Aggregate-count refresh script (`scripts/refresh_aggregate_counts.py`) — reads canonical values from `validation_rounds.json.cumulative_stats` + live validator runs, updates HTML-comment markers in AGENT.md, validate-semantic.md, pipeline-audit.md, verifiers.md. Markers added for `total_rounds`, `total_bugs_found`, `total_bugs_fixed`, `total_docs_validated`, `last_validation_date`, `latest_round_id`. Commit `88eee98`.

**Cumulative validator state at session end**: 34/35 passed, 1 warning (s59_nitrogen_uptake Pattern 13 unit advisory). Wall-clock ~6s.

---

## R3 progress (2026-05-23 autonomous session)

**Tier 3 — done (R3)**:

7. ✅ R3 pipeline-audit run (6 parallel Opus lens agents, 82 raw findings, ~75 unique after dedup). Triage + fix + verify + 7 root-cause-cluster commits landed. Validator status: 34/35 passed, 1 known advisory. Report at `feedback/pipeline_audit_round3.md`; JSON entry in `feedback/pipeline_audit_rounds.json`.

**R3 commits stacked** (on top of R2's 4 commits):
| # | SHA | Cluster |
|---|-----|---------|
| 1 | `a0ad71a` | C7 — instruction surface (AGENT.md, helpers/README.md, verifiers.md) |
| 2 | `7a0ab02` | C4 — dep-counts (Module_Dependencies, safety guide, M12/15/35) |
| 3 | `ae3763f` | C3 — post-PR citation/value/dim drift (M73, M22, M21, M32, M11, M51, M53, M70) |
| 4 | `49cc6f0` | C2 — M11 §17.2 rewrite (CRITICAL fabrication fix) |
| 5 | `ecad717` | C1 — multi-realization body drift header warnings (M38, M30, M80) |
| 6 | `6ba3ed7` | C5 — validator soundness (silent-fallback HIGH, regex coverage) + 5 surfaced cite bugs |
| 7 | `41970b3` | C6 — markerize validator-count + bug-taxonomy-count (7 strings, 5 files) |

**R3 corroborated findings** (high-confidence signal):
- M11 §17.2 fabricated 14 cost-variable names (Lens 2 + Lens 5; CRITICAL) — FIXED
- Validator check-count markers stale across 4+ files (Lens 4 + Lens 6; HIGH) — FIXED
- R2 spot-fix on M51 vm_manure_recycling attribution was incomplete (Lens 5; MED) — FIXED

---

## Remaining work (Tier 4 — strategic / closes the loop)

### 8. M30 / M80 body rewrites (M38 DONE in R3-followup; M30/M80 still pending)

R3 added prominent header warnings to M38, M30, and M80. R3-followup session (2026-05-23, after the great-work-thank-you-woolly-clock plan) completed the M38 full body rewrite — see commit `4a07b88`. M30 and M80 are still pending:

- ~~**M38**: DONE 2026-05-23. sticky_feb18 leads, sticky_labor demoted to alternative. 665 lines (down from 1666). Body-realization-mismatch flag cleared. Interim R3 warning header removed.~~
- **M30**: declarations.gms cites detail_apr24 line numbers but default is simple_apr24. Need realization-prefixed citations throughout. Header warning remains.
- **M80**: missing `Parameters (nlp_apr17)` table for the default realization. Header warning remains.

### 9. ~~check_doc_var_existence.py mechanization~~ — DONE in R3-followup

✅ `scripts/check_doc_var_existence.py` landed as Check 21 in commit `2a92985`. Closes R3 Cluster 2 (fabricated identifiers in backticked prose) for cross_module/ and core_docs/ (modules/module_*.md was already covered by Check 14). Surfaced 22 cases; all triaged + allowlisted in the same commit.

### 10. ~~check_module_realizations.py body-citation extension~~ — DONE in R3-followup

✅ Body-citation drift check landed in commit `bf53c4d`. Catches dominant-realization-in-body ≠ header-claimed-realization (with zero-equation suppression for M37/M80-style no-equation defaults). Caught M38 as the one expected case; M38 was then fixed in commit `4a07b88` Phase C.

### 11. Python rewrites of check_gams_equations.sh and check_gams_realizations.sh (R3 Cluster 8)

Per Lens 6: check_gams_equations.sh = 3.4s (38% of 8.8s wall-clock); check_gams_realizations.sh = 1.0s. Both use the same O(N*M) bash anti-pattern that made check_gams_variables.sh slow. Python rewrites would drop validator total to ~4.5s.

### 12. Archive removal (R3 Cluster 8 — needs user confirmation)

`feedback/archive/` (112KB) + `reference/archive/` (160KB) = 272KB dead weight. Referenced only in validator skip-paths (and validate_consistency.sh.bak which R3 deleted). Per Lens 6, candidate for deletion — but needs user sign-off since git history preservation may matter.

### 13. AGENT.md "LINK DON'T DUPLICATE" hoist (R3 Cluster 8 — judgment call)

The 75-line LINK-DON'T-DUPLICATE section in AGENT.md is editorial guidance only relevant when editing docs. Could move to `agent/helpers/maintenance_protocol.md` (which already auto-loads on doc-maintenance triggers). Would shave ~10% off AGENT.md. Defer until M30/M38/M80 rewrites are landed (avoid mid-session churn).

### 14. Helper trigger overlap cleanup (R3 Cluster 8 — low priority)

Per Lens 6: `realization` keyword fires both `verifiers.md` AND `realization_selection.md` (~4000 words when ~2000 would do); `scenario` substring fires 5 helpers. Each overlap is a judgment call about narrowing vs keeping broad-coverage.

### 15. Validation_rounds R22 — first round under schema v1.1 (~1.5 hr)

The new `regression_questions` slots (G1, G2) need a first real test. R22 will be the first round to include them.

**Action**: design a round of 4 new probes + G1 + G2; run via `/validate-semantic`. Confirm:
- The auditor uses `feedback/flywheel_rubric.md` correctly (no inline rubric inheritance from validate-semantic.md)
- G1 and G2 scores are recorded; `used_in_rounds` is appended; `drift_observed` is set
- `python3 scripts/probe_dedup_check.py round22_design.md` warns appropriately

---

## Won't fix this cycle (explicitly deferred)

- **Unbacktiked-prose variable scanner**: needs its own design pass (heuristic for what's a "variable mention" vs incidental prose). Estimated 4-6 hr; lower priority than the new `check_doc_var_existence.py` candidate above (which catches backticked fabrications first). Note: now that the Python validator runs in <1s, the cost of a stricter scanner is lower.
- **Bulk bare-basename citation cleanup**: ~760 advisories remain (R3 resolver fix only changed behavior for paths that previously had a realization hint; bare basenames in single-realization modules are still passed). Mostly noise. Spot-fix only the high-risk cases (multi-realization modules: 13_tc, 17_production, 21_trade, 38_factor_costs, 44_biodiversity, 53_methane, 56_ghg_policy, 70_livestock, 80_optimization).
- **Module 13 internal vm_tau cleanup**: spot-checked in R2; deeper sweep deferred.
- **Pattern 12 remaining 2 advisories**: both are legitimate false positives — M14 vm_tau (doc explicitly notes absence), M52 s32_aff_plantation (cite-paragraph spans the var location but the cite line itself doesn't).
- **s59_nitrogen_uptake Pattern 13 advisory**: the only remaining validator warning (1 of 35). Caused by unit-conversion FP (`200 kg N/ha` doc claim vs `0.2 tN/ha` source value — same number, different units). Per Lens 3 fix candidate: extend check_param_defaults.py with a per-claim allowlist comment OR a unit-conversion table. Low priority since the advisory clearly identifies the issue.
- **R3 LOW-severity spot bugs not fixed**: Lens-by-lens, ~25 LOW findings not individually addressed. Most are minor stylistic or single-occurrence drifts that don't warrant a commit. See `feedback/pipeline_audit_round3.md` for the full enumeration.

---

## All R1+R2+R3 commits

R1+R2 commits are pushed to origin/main as of plan-commit `5708b6f`. R3 commits below are pushed as part of this session:

| # | SHA | Title |
|---|-----|-------|
| R1+R2 (1) | `8932040` | audit+fix: R1+R2 pipeline audit + Tier 1 follow-ups |
| R1+R2 (2) | `88eee98` | perf+infra: Python check_gams_variables + aggregate-count refresher |
| R1+R2 (3) | `41d92b2` | cit-fix: Pattern 12 cleanup + tighter heuristic + resolver fix |
| R1+R2 (4) | `66f2833` | session-wrap: progress log + cumulative_stats sync |
| R3 plan | `5708b6f` | plan: R3 lens audit execution plan (autonomous mode) |
| R3 (1) | `a0ad71a` | C7 instruction-surface fixes |
| R3 (2) | `7a0ab02` | C4 dependency-counts |
| R3 (3) | `ae3763f` | C3 post-PR citation/value/dimension fixes (8 modules) |
| R3 (4) | `49cc6f0` | C2 M11 §17.2 fabrication rewrite (CRITICAL) |
| R3 (5) | `ecad717` | C1 multi-realization body drift header warnings (M30/M38/M80) |
| R3 (6) | `6ba3ed7` | C5 validator soundness (silent-fallback HIGH + regex coverage) + 5 cite cleanups |
| R3 (7) | `41970b3` | C6 markerize validator-count + bug-taxonomy-count |

---

## Verification at R3 session end (2026-05-23)

```bash
bash scripts/validate_consistency.sh   # 34/35 passed, 1 known advisory (s59_nitrogen_uptake unit conversion FP)
python3 scripts/check_module_realizations.py   # 0 errors, 0 warnings, 64 docs checked
python3 scripts/check_gams_variables.py        # 100% (953/953 verified; up from 944 thanks to R3 regex extension)
python3 scripts/refresh_aggregate_counts.py    # all markers up to date
git log --oneline 5708b6f..HEAD                # 7 R3 commits stacked on plan commit
```

R3 logged to `feedback/pipeline_audit_round3.md` (full report) and `feedback/pipeline_audit_rounds.json` round 3 entry (R1 schema mirrored).
