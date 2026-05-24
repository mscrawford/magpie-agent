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

---

## Progress log (2026-05-24 infrastructure-buildout session, Phase 1)

Plan: `~/.claude/plans/magpie-agent-infrastructure-buildout.md`. Phase 1 (quick-win validators) complete.

**Phase 1 — done**:

10. ✅ **I1 — Consumer-attribution checker** (`scripts/check_consumer_attribution.py`, ~250 LOC). Builds producer map from `declarations.gms` (1133 vars), consumer map from all module `.gms` files (1780 vars), then validates every `| \`var\` | N |` consumer-table row across `core_docs/Module_Dependencies.md`, `cross_module/modification_safety_guide.md`, all `modules/module_*.md`. Header-gated (only fires inside tables whose 2nd column header contains `Consumer`/`Used by`/etc.) to avoid false-positives on scalar default-value tables. Wired as Check 22 advisory. Surfaced 2 real drift cases in `modification_safety_guide.md` §3.2 — `vm_prod_reg` 9→8, `pm_prod_init` 3→1 — both fixed and verified.

11. ✅ **I3 — Multi-path VERIFIED_RE fix** (`scripts/check_module_realizations.py`). Split single-pattern parsing into two-stage: VERIFIED_LINE_RE captures the footer line; PATH_RE finds ALL `modules/NN_name/realization/` paths within it. Surfaced 4 multi-realization footers (M18, M38, M80) that were previously invisible. Added classification logic: when at least one cited realization matches the default, additional non-default cites are treated as documented-alternative INFO (not ERROR). All 4 cases pass cleanly under this rule.

12. ✅ **I4 — Allowlist marker robustness** (`scripts/check_gams_variables.py`). Added `PER_DOC_ALLOW_LOOSE_RE` + `find_typo_allow_markers()`. When the loose pattern matches but the strict regex does not, the marker is silently failing — emit WARN. Unit-tested on 7 cases (strict markers, underscore/missing-colon typos, valid no-space variants). Validator-side: `|| true` guard added to handle `set -e` + `grep` no-match exit code 1. Current tree has 0 typo'd markers.

13. ✅ **I2 — Multi-section consistency check** (`scripts/check_multi_section_consistency.py`, ~140 LOC). For each module doc, finds all backticked `var(dims)` references outside code blocks, groups by var, flags vars with >1 distinct normalized dim signature. Normalization: whitespace, quote unification, set-alias collapse (j/j2/j3 → j; i/i2 → i; h/h2 → h; cell2 → cell; supreg2 → supreg), quoted-literal masking (`"crop"` → `<lit>`). Two-tier output: arity mismatches (likely drift) vs signature variants (usually legit context). Convention-suppression filters out `...` ellipsis, `t-1`/`t+1` annotations, and pure-literal partial references. Wired as Check 23 advisory. Surfaced 2 real arity-drift bugs in `module_71.md` (`im_feed_baskets` missing t dim) and `module_73.md` (`im_timber_prod_cost` missing i dim) — both fixed. 3 remaining arity findings are doc-convention false positives (M29 vm_land shorthand, M35 partial reference, M80 multi-realization variant).

**Validator state at end of Phase 1**: 38 total checks, 35 passed, 3 warnings (pre-existing s38/s59 param-default advisories + new I2 advisory + CLAUDE.md ref). Wall-clock ~7s.

**Triage budget vs spend**: plan budgeted ~30 min for I1 surface; spent ~10 min (only 2 real drift cases; less than expected 5-15). Plan budget total ~3 hours for Phase 1; actual ~2 hours. Under budget.

**Insights captured for future**:
- Header-gated table parsing (look at table's 2nd column header before treating row counts as consumer claims) — reusable pattern for any markdown-table consistency check.
- Two-stage parsing of footer constructs ("locate header → find paths within") is cleaner than a single regex when the construct has multiple instances per line.
- Set-alias collapsing in dim comparisons (j↔j2) is essential — otherwise legitimate solver-rename variants false-positive overwhelmingly.
- I2's signature-variant tier is mostly noise on current docs (75 variants); the arity tier (3 findings after fix) is the actionable signal. Same-arity-different-set drift (e.g., the original M14 pcm_tau h→j case) is now caught at the arity-collapse boundary — h is NOT aliased to j.

---

## Verification at Phase 1 session end (2026-05-24)

```bash
bash scripts/validate_consistency.sh   # 35/38 passed, 3 advisory warnings
python3 scripts/check_consumer_attribution.py    # 23/23 claims verified, 0 mismatches
python3 scripts/check_module_realizations.py     # 0 errors, 0 warnings, 64 docs (I3 multi-path now resolves)
python3 scripts/check_gams_variables.py          # 100% (973/973 verified)
python3 scripts/check_multi_section_consistency.py  # 3 arity mismatches (false-positive doc conventions)
```

---

## Progress log (2026-05-24 infrastructure-buildout session, Phase 3)

User chose Phase 3 (opportunistic cleanup) over Phase 2 (PR-integration ~2 weeks) after Phase 1 landed. All Phase 3 items except D1 done in one ~1h session.

**Phase 3 — done**:

14. ✅ **D2 — Conservation-law equation simplifications**. `nitrogen_food_balance.md` q21_trade_glo: added missing `+ sum(ct, f21_trade_balanceflow(ct,k_trade))` term with brief annotation explaining the historical FAO-trade residual. `carbon_balance_conservation.md` q59_som_target_cropland: replaced one-line simplification with full 4-term equation (cropland base + SCM uplift + fallow + treecover).

15. ✅ **D4 — Module_Dependencies §5.2 diagram**. Stale solid `↑` arrow on `14_yields → 32_forestry` converted to dashed `⇡` with explanatory caption (shared climate/age-structure context, not a real interface).

16. ✅ **I5 — Generic rename checker** (`scripts/check_renames.py` + `feedback/renames.json`, Check 24). Reads JSON-declared historical renames (3 initial entries: pm_timber_yield → im_growing_stock; vm_cost_trade split; sm_cdr_target removed); greps for old names in non-exempt docs. Italic-historical convention (`*old*`) and allowlist marker lines auto-suppressed. Surfaced + fixed 2 real bugs: `reference/Verification_Protocol.md` (pm_timber_yield cited as the canonical "right way" example) and `reference/dependency_analysis/EXECUTIVE_SUMMARY.md` (old name in variable table).

17. ✅ **C1 — Python rewrites of equations.sh + realizations.sh** (`scripts/check_gams_equations.py` + `scripts/check_gams_realizations.py`). Mirror of check_gams_variables.py's single-pass index + O(1) set-membership pattern. Speedups: equations 3.76s → 0.095s (40x), realizations 1.01s → 0.100s (10x). Validator total wall-clock dropped from ~7s to ~5s. Validator now prefers .py and falls back to .sh.

**D1 skipped**: GAMS reference revalidation requires a targeted /validate-semantic run which the plan explicitly defers (R22 just completed).

**Validator state at end of Phase 3**: 39 total checks, 36 passed, 3 advisory warnings (pre-existing s38/s59 + I2 doc-convention advisories + CLAUDE.md ref). Wall-clock ~5s (down from ~7s).

**Insights captured for future**:
- Header-gated markdown table parsing: look at table header before treating row values as semantic claims. Avoids false-positives where same `| name | N |` row format means different things in different tables (consumer count vs default value). See [[header_gated_markdown_tables]].
- Rename ledger as defensive infrastructure: declarative `renames.json` + grep-based checker turns out to be a high-leverage mechanism. 19 raw hits collapsed to 2 real bugs via 2 convention-suppression rules (italics + allowlist markers). See [[rename_ledger_defensive_infra]].

---

## Verification at Phase 3 session end (2026-05-24)

```bash
bash scripts/validate_consistency.sh         # 36/39 passed, 3 advisory warnings
python3 scripts/check_renames.py             # 0 hits across 3 tracked renames
python3 scripts/check_gams_equations.py      # 100% (147/147 equations)
python3 scripts/check_gams_realizations.py   # 100% (77/77 realizations)
```

**Next session**: Phase 2 — S2 PR-integration pipeline (~2 weeks focused). Start with 5a (PR impact analyzer, ~200 LOC). See `~/.claude/plans/magpie-agent-infrastructure-buildout.md` §5.

Phase 3 cumulative: 6 real drift cases caught and fixed across both phases (M71 + M73 missing-dim drift surfaced by I2; safety_guide vm_prod_reg + pm_prod_init surfaced by I1; Verification_Protocol + EXECUTIVE_SUMMARY pm_timber_yield refs surfaced by I5). Each finding represents a doc bug that would have misled a downstream user; each was caught mechanically rather than via human review.

---

## Progress log (2026-05-24 Phase 2 session — 5a landed)

Plan: `~/.claude/plans/magpie-agent-infrastructure-buildout.md` §5.

**5a — done**:

18. ✅ **PR impact analyzer** (`scripts/pr_doc_impact.py`, ~500 LOC incl. docstrings). Given a MAgPIE commit range (`--base`/`--head`, `--since-last-sync`, or `--pr N`), emits structured JSON listing each magpie-agent doc that needs updates. Four change classes:
    - `identifier_added` / `identifier_removed` — diff `declarations.gms` lines; dedup by name across multi-realization modules; skip removals with zero stale-reference docs
    - `default_value_change` — parse `input.gms` scalar `/ VALUE /` declarations at both revs
    - `line_shift` — per-file diff hunk headers; cumulative deltas applied to each cited line
    - `new_realization` — added `modules/NN_x/REAL/` directory (gated by `realization.gms` existence at head)

    Per-doc confidence tier (`mechanical | semantic | manual`) for 5b/5c dispatch.

    **Acceptance tests (all 4 PRs from sync_log)**:
    | PR | Commit | Changes | Docs touched | Matches sync_log? |
    |----|--------|---------|--------------|-------------------|
    | #866 trade-cost split | 1c2e7031c | 41 | 6 | ✅ M21+M11+nitrogen_food_balance |
    | #876 secdforest carbon | c7731e234 | 15 | 7 | ✅ M35+M52 (+ ripple) |
    | #869 timber overhaul | 75d7ee167 | 56 | 9 | ✅ M14+M21+M32+M35+M52+M73 |
    | #871 IPOPT solver | 9cba74ab7 | 7 | 3 | ✅ new_realization detected: nlp_ipopt → M80 doc + AGENT.md |

19. ✅ **Surfaced gap: `pc<N>_` prefix missing from check_gams_variables regex**. Same R3-class bug as ic/oq/ov\d+_. `pc35_secdforest_natural` was uncheckable. Extended both `GAMS_NUMBERED_RE` and `DOC_VAR_RE`. Validator stays 36/39 pass — no new false positives. Inherited by `pr_doc_impact.py` (which imports `GAMS_NUMBERED_RE`); PR #876 now correctly surfaces the pc35 addition.

**Noise-reduction iterations during MVP** (each was a measurable win, not a stylistic choice):
- Bare-basename citation matches (`equations.gms:N`) now restricted to the module's OWN doc (`modules/module_NN.md`). Cross-module and reference docs must use the full-path form `modules/NN_name/REAL/equations.gms:N` to match. Reduced PR #866 from 78 → 6 docs touched.
- Identifier add/remove dedup by name across realizations — a var added in 3 realizations is one finding with 3 `in_files`, not three findings.
- `identifier_removed` entries with empty `affected_docs` suppressed (when the rename has already been synced to docs, nothing to flag).

**Insights captured for future**:
- **Prefix surface auto-discovery (candidate future work)**: this is the SECOND time we've found a missing numbered prefix in `check_gams_variables.py` (R3: ic/oq/ov; today: pc). The conservative-hardcoded approach lets prefixes silently slip in. A more robust check: derive the prefix set from observed declarations.gms patterns and warn when a new prefix appears. Memory candidate: [[gams_prefix_autodiscovery]].
- **MVP citation-matching defensiveness pays off immediately**: 78 → 6 docs after the bare-basename restriction. The lossy initial regex would have generated dozens of false-positive doc-update tasks for downstream 5b/5c, eroding trust before 5b/5c even shipped. Always defang citation matching at the source.

**Validator state at end of 5a**: unchanged — 36/39 passed, 3 known advisories. New tool is invocation-only; not wired into validate_consistency.sh.

---

## Verification at 5a session end (2026-05-24)

```bash
bash scripts/validate_consistency.sh         # 36/39 passed (unchanged)
python3 scripts/check_gams_variables.py      # 100% verified (1806-var index, up from ~944 — pc<N>_ extension)
python3 scripts/pr_doc_impact.py --base 1c2e7031c~1 --head 1c2e7031c   # 41 changes, 6 docs
python3 scripts/pr_doc_impact.py --base c7731e234~1 --head c7731e234   # 15 changes, 7 docs
python3 scripts/pr_doc_impact.py --base 75d7ee167~1 --head 75d7ee167   # 56 changes, 9 docs
python3 scripts/pr_doc_impact.py --base 9cba74ab7~1 --head 9cba74ab7   # 7 changes, 3 docs (new_realization)
python3 scripts/pr_doc_impact.py --since-last-sync --head origin/develop   # 0 changes (only Docker/codecheck since 3836bbaa9)
```

**Next session**: 5b — mechanical updater (`scripts/pr_mechanical_update.py`, ~150 LOC). For each "mechanical" entry from 5a JSON: apply line-citation offsets in docs, refresh scalar value markers. Run validators after. The line_shift entries from PR #876 are the natural first test case (8 hunks, mostly small deltas). Once 5b lands, the full 5a→5b loop can auto-fix line-citation drift on every PR.
