# Next Session Plan — magpie-agent

**Origin**: deferred items from the 2026-05-23 R1+R2 lens-audit + fix session (`feedback/pipeline_audit_round1.md`, `feedback/pipeline_audit_rounds.json` R2 entry).

**Context**: R2 closed Clusters 1, 2 (partial), 3, 5, 6, 7 from the 71-finding R1 audit. Clusters 4 (validator coverage gaps) and one Cluster-7 cleanup (Module 18 body) remain deferred. Two new advisory streams now surface from R2's enhanced citation validator: 874 bare-basename ambiguity warnings + 25 Pattern-12 content-mismatch advisories.

Per [[feedback_confabulation_relocates]] — closing some surfaces pushes bugs to others. R3 audit (item 7 below) will probe the unguarded surfaces and tell us where confabulation has relocated.

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

## Remaining work (Tier 3 — strategic / closes the loop)

### 7. R3 pipeline-audit run (~30-45 min wall-clock, ~10 min triage)

Per [[feedback_confabulation_relocates]] — R2's fixes closed surfaces; expect bugs to have relocated. The follow-up session also added new infrastructure (Python validator, Pattern 13, marker refresher, resolver fix). R3 should specifically probe **unguarded surfaces**:
- Pattern 13 (param defaults) — Check 20 advisory, but no upstream enforcement
- Unbacktiked-prose variable references — Lens 3 said 82% of variable mentions are unbacktiked and unchecked
- Cross-doc interface dimensions beyond R2's spot fixes
- AGENT.md / verifiers.md MANDATE-rule consistency after the hoist-completion pass
- New surface: any docs that relied on the buggy citation resolver's silent walk-order resolution

**Action**: run `/pipeline-audit` again. Expected output: ~30-50 findings (lower than R1's 71 since 4 clusters are now mechanized).

**Then**: triage; identify whether confabulation relocated (per the meta-warning in [[template-verifier-mandate-flywheel]]); decide next mechanization candidate.

**Why not run autonomously**: spawns 6 parallel Opus sub-agents (substantial compute) and produces findings that need user-aware triage. Best run with the user present to make triage calls.

### 8. Validation_rounds R22 — first round under schema v1.1 (~1.5 hr)

The new `regression_questions` slots (G1, G2) need a first real test. R22 will be the first round to include them.

**Action**: design a round of 4 new probes + G1 + G2; run via `/validate-semantic`. Confirm:
- The auditor uses `feedback/flywheel_rubric.md` correctly (no inline rubric inheritance from validate-semantic.md)
- G1 and G2 scores are recorded; `used_in_rounds` is appended; `drift_observed` is set
- `python3 scripts/probe_dedup_check.py round22_design.md` warns appropriately

---

## Won't fix this cycle (explicitly deferred)

- **Unbacktiked-prose variable scanner**: needs its own design pass (heuristic for what's a "variable mention" vs incidental prose). Estimated 4-6 hr; lower priority than Pattern 13 since most user-facing claims use backticks. Note: now that the Python validator runs in <1s, the cost of a stricter scanner is lower.
- **Bulk bare-basename citation cleanup**: 766 advisories remain (down from 874 after resolver fix — the fix only helped citations that already had a realization prefix). Mostly noise (single-realization modules where the basename is unambiguous). Spot-fix only the high-risk cases (multi-realization modules: 13_tc, 17_production, 21_trade, 38_factor_costs, 44_biodiversity, 53_methane, 56_ghg_policy, 70_livestock, 80_optimization) — leave the rest as advisory.
- **Module 13 internal vm_tau cleanup**: spot-checked in R2; deeper sweep deferred.
- **Pattern 12 remaining 2 advisories**: both are legitimate false positives — M14 vm_tau (doc explicitly notes absence), M52 s32_aff_plantation (cite-paragraph spans the var location but the cite line itself doesn't).

---

## Three commits landed locally (not pushed)

| # | SHA | Title |
|---|-----|-------|
| 1 | `8932040` | audit+fix: R1+R2 pipeline audit + Tier 1 follow-ups (M18, Pattern 13, GAMS regex) |
| 2 | `88eee98` | perf+infra: Python check_gams_variables (~50x faster) + aggregate-count refresher |
| 3 | `41d92b2` | cit-fix: Pattern 12 cleanup (25 → 2 advisories) + tighter heuristic + resolver fix |

All three are stacked on `9b58fa8` (docs(module_14)). NOT pushed pending user review.

---

## Verification at session end

```bash
bash scripts/validate_consistency.sh   # 34 passed, 1 advisory warning (s59_nitrogen_uptake unit-conversion)
python3 scripts/check_module_realizations.py   # 0 errors
python3 scripts/check_gams_variables.py        # 944/944 verified
git log --oneline origin/main..HEAD            # 3 unpushed commits
```

If R3 runs (item 7), log to `feedback/pipeline_audit_rounds.json` as round 3 with the same schema as R1/R2.
