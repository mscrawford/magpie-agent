# Next Session Plan — magpie-agent

**Origin**: deferred items from the 2026-05-23 R1+R2 lens-audit + fix session (`feedback/pipeline_audit_round1.md`, `feedback/pipeline_audit_rounds.json` R2 entry).

**Context**: R2 closed Clusters 1, 2 (partial), 3, 5, 6, 7 from the 71-finding R1 audit. Clusters 4 (validator coverage gaps) and one Cluster-7 cleanup (Module 18 body) remain deferred. Two new advisory streams now surface from R2's enhanced citation validator: 874 bare-basename ambiguity warnings + 25 Pattern-12 content-mismatch advisories.

Per [[feedback_confabulation_relocates]] — closing some surfaces pushes bugs to others. R3 audit (item 7 below) will probe the unguarded surfaces and tell us where confabulation has relocated.

---

## Tier 1 — Highest leverage (do early)

### 1. Module 18 full body rewrite (~1-2 hr)

R2 added a prominent Quick Reference + warning at the top, but the body (~700 lines) still walks through the non-default `flexcluster_jul23` realization. A reader skipping the warning will still get incorrect cluster-level equations.

**Action**: rewrite the body to lead with `flexreg_apr16`'s 9 regional equations (the actual default). Move `flexcluster_jul23` content to a clearly labeled "Alternative Realization" section. Verify against `modules/18_residues/flexreg_apr16/equations.gms`.

**Verification**: `python3 scripts/check_module_realizations.py --module 18` should still pass; new doc body should describe regional-level variables (no `j2`-indexed cluster constraints).

### 2. Pattern 13 validator — wrong parameter default values (~80 LOC)

Bug_Taxonomy.md Pattern 13 has **zero validator coverage**. R1 Lens 3 estimated ~hundreds of `(default N)` claims across module docs that could drift undetected. Scenario switches and scalars are particularly dangerous.

**Action**: write `scripts/check_param_defaults.py` that:
- Greps for `(default N)`, `default: N`, `default value: N` patterns in module docs
- Extracts the parameter name from surrounding backticks
- Looks up the actual default in `../config/default.cfg` or `../modules/XX_*/<real>/input.gms`
- WARNs on mismatch (likely ~30-50% noise from legitimate scenario ambiguity, so advisory not blocking)

**Hook**: Check 20 in `validate_consistency.sh`.

### 3. GAMS variable regex extension (~10 LOC)

Lens 3 found that `c<N>_*` (scenario switches), `cm_*` (interface config), `sm_*` (interface scalar) prefixes are missing from the GAMS-index regex in `scripts/check_gams_variables.sh`. Confabulations like `c99_invented_switch` sail through silently. Highest-leverage tiny fix — `c56_pollutant_prices`, `sm_fix_SSP2`, etc. are common variables.

**Action**: extend line 41 regex to include `c{N}_`, `cm_`, `sm_`. Update line 69 doc-side extraction to match.

**Verification**: `bash scripts/validate_consistency.sh` — should still pass (no current docs invent these), but coverage is now real.

---

## Tier 2 — Worth doing in same session if time

### 4. Performance: Python rewrite of `check_gams_variables.sh` (~2 hr)

Lens 6 measured `check_gams_variables.sh` at **47.2s of 51.7s total** validator time (91%) due to a nested per-variable grep loop (~2,300 subprocess invocations). The other 17 checks combined run in ~4.5s.

**Action**: rewrite as `scripts/check_gams_variables.py` (single-pass index of declarations.gms + dict lookup per doc-cited name). Expected: total validator drops from 52s → <10s. Pre-commit hooks become feasible.

**Verification**: same pass/fail behavior on current docs (0 errors, 830/830 verified); 10x faster wall-clock.

### 5. Pattern 12 advisory cleanup (~1 hr)

The enhanced citation checker surfaces **25 content-mismatch advisories** — backticked GAMS identifiers near citations that don't appear within ±5 lines of the cited line. These are likely a mix of real Pattern-12 bugs and false positives (identifiers referenced by name in prose but not in the cited equation block).

**Action**: sample all 25, classify into (a) real citation drift → fix, (b) false positive → leave (the advisory is intentionally noisy).

**Stretch**: tighten the heuristic — only fire when the nearby identifier is the *equation name* being cited (vs incidental variable references).

### 6. Aggregate-count refresh script (~50 LOC)

R2 manually updated 8 stale counts across 5 files. Same drift will recur on every flywheel round.

**Action**: write `scripts/refresh_aggregate_counts.py` that reads canonical values from `feedback/validation_rounds.json.cumulative_stats` + `wc -w` + grep counts and updates well-defined HTML-comment-marked placeholders in AGENT.md / validate-semantic.md / pipeline-audit.md / verifiers.md.

**Hook**: run as a post-`/sync` step or before every flywheel round.

---

## Tier 3 — Strategic / closes the loop

### 7. R3 pipeline-audit run (~30-45 min wall-clock, ~10 min triage)

Per [[feedback_confabulation_relocates]] — R2's fixes closed surfaces; we expect bugs to have relocated. R3 should specifically probe **unguarded surfaces**:
- Pattern 13 (param defaults) — until item 2 lands
- Unbacktiked-prose variable references — Lens 3 said 82% of variable mentions are unbacktiked and unchecked
- Cross-doc interface dimensions beyond R2's spot fixes
- AGENT.md / verifiers.md MANDATE-rule consistency after the hoist-completion pass

**Action**: run `/pipeline-audit` again. Expected output: ~30-50 findings (lower than R1's 71 since 4 clusters are now mechanized).

**Then**: triage; identify whether confabulation relocated (per the meta-warning in `[[template-verifier-mandate-flywheel]]`); decide next mechanization candidate.

### 8. Validation_rounds R22 — first round under schema v1.1 (~1.5 hr)

The new `regression_questions` slots (G1, G2) need a first real test. R22 will be the first round to include them.

**Action**: design a round of 4 new probes + G1 + G2; run via `/validate-semantic`. Confirm:
- The auditor uses `feedback/flywheel_rubric.md` correctly (no inline rubric inheritance from validate-semantic.md)
- G1 and G2 scores are recorded; `used_in_rounds` is appended; `drift_observed` is set
- `python3 scripts/probe_dedup_check.py round22_design.md` warns appropriately

---

## Won't fix this cycle (explicitly deferred)

- **Unbacktiked-prose variable scanner**: needs its own design pass (heuristic for what's a "variable mention" vs incidental prose). Estimated 4-6 hr; lower priority than Pattern 13 since most user-facing claims use backticks.
- **Bulk bare-basename citation cleanup**: 874 advisories is mostly noise (single-realization modules where the basename is unambiguous). Spot-fix only the high-risk cases (multi-realization modules: 13_tc, 17_production, 21_trade, 38_factor_costs, 44_biodiversity, 53_methane, 56_ghg_policy, 70_livestock, 80_optimization) — leave the rest as advisory.
- **Module 13 internal vm_tau cleanup**: spot-checked in R2; deeper sweep deferred.

---

## Recommended execution order

Do items in numbered order. Stop at the natural breakpoint when:
- Tier 1 (1-3) complete → safe to commit + push; the agent is meaningfully more accurate.
- Tier 2 (4-6) complete → infrastructure is materially faster + drift-resistant.
- Tier 3 (7-8) complete → next measurement cycle has run; we know what's relocated.

Each tier has clean stopping points. A 2-3 hour session can plausibly close Tier 1 + 1-2 items from Tier 2.

---

## Verification at session end

```bash
bash scripts/validate_consistency.sh   # should still pass (34/34 + Check 20 if added)
python3 scripts/check_module_realizations.py  # 0 errors
git diff --stat                         # review scope
```

If R3 runs (item 7), log to `feedback/pipeline_audit_rounds.json` as round 3 with the same schema as R1/R2.
