# Flywheel rubric (v1.0)

Used by the Opus auditor to score Sonnet magpie-agent answers in semantic-validation rounds (`/validate-semantic`). Designed to maximize stability across rounds (so trends are real) while staying sensitive to actual agent improvements.

**Version**: 1.0 (2026-05-23). Hoisted from the rubric content previously embedded in `agent/commands/validate-semantic.md`. Bumps required for any change to severity criteria, anchor examples, or bug-class definitions. Adding new bug classes is permitted at minor versions (1.x). See §9 Changelog.

**Anchor examples are immutable across rubric versions** — they are the empirical reference points that prevent rubric drift. If reality contradicts an anchor, fix the underlying issue or bump the major version; do not silently re-interpret the anchor.

---

## 1. Severity tiers

Opus assigns each bug exactly one tier via top-down decision-tree match. **First trigger that fires wins**; document which trigger matched in the bug record.

### 🔴 Critical
**Definition**: If the user acted on this answer, they would do the wrong thing on a high-stakes decision — edit the wrong file, build on a false foundation, or make a load-bearing modification that breaks the model.

**Triggers** (any one suffices):
- Wrong realization claimed as default for a module the user wants to modify (would point at a non-default file).
- Module described as if a non-default realization were active (cascading errors — wrong variables, equations, mechanism).
- Active mechanism claimed when actually OFF by default (e.g., `s42_pumping = 1` claimed when default is 0).
- Inverted Boolean default (e.g., `s15_exo_diet = 1` claimed when default is 0).
- Invented variable name presented as authoritative (no such `vm_*`/`pm_*`/`v{N}_*` exists in declarations.gms).
- Invented equation name presented as authoritative.
- Wrong module attribution for a cost variable (e.g., `vm_cost_prod_crop` attributed to a non-Module-38 module).
- Claimed a function/variable/file does not exist when it does (false-negative honest disclaim).
- Fabricated formula presented as the code's actual implementation.

**Anchor examples** (immutable):
- 2026-03-07 (R3): agent described livestock feed as using non-default `fbask_jan16` mechanics when default config has been `fbask_jul23` for years. Cascading: wrong feed basket equations, wrong variables, wrong calibration parameters cited. → **Critical** (cascading wrong-realization).
- 2026-04-20 (R20, doc bug): module doc cited `pm_carbon_density_ac` as having three consumers when commit added two more (M32 afforestation + NDC presolve); answerer trusted the doc and missed the consumers. → **Critical** (doc said wrong consumer set; user would have missed two modules in a refactor).
- 2026-03-08 (R16): agent claimed age classes go to `ac140, acx`; actual set extends to `ac300` (62 elements). Doc was correct at line 443; agent truncated. → **Critical** (downstream calculations off by 35× in element count).

### 🟠 Major
**Definition**: The claim is wrong in a way that misleads about behavior, but won't directly cause damaging action.

**Triggers**:
- Right concept, wrong number (parameter range, default value off by a moderate factor).
- Missing default-state caveat (mechanism described as if always active when it's OFF by default — `s42_pumping`, `s56_pollutant_prices` ON only with non-default config).
- Citation points at content that's no longer at the cited line, AND the actual cited content says something materially different (citation drift to wrong content).
- File:line citation drift to *adjacent* but different content (would mislead a careful reader).
- Wrong variable prefix (vm_ vs v{N}_, pm_ vs p{N}_) — semantic scope wrong.
- Recommendation that contradicts maintainer practice without an anchor citation (advisory drift).
- Fabricated count for a set/parameter/realization list (e.g., "Module X has 5 realizations" when it has 3).

**Anchor examples**:
- 2026-03-08 (R16): agent fabricated an expanded `q10_land_area` equation by enumerating set members instead of preserving the set-based sum. Code uses `sum(land, vm_land(j,land))`; agent wrote `vm_land(j,"crop") + vm_land(j,"past") + ...`. → **Major** (would mislead a reader about how the code reads, but not into a wrong code edit).
- 2026-03-07 (R6): claimed `m15_food_demand` model block has 22 equations; actual is 17. → **Major** (descriptive incompleteness on a load-bearing structure).
- 2026-04-20 (R20): line numbers cited from diff output rather than post-merge code; 13 file:line citations drifted by 5-20 lines. → **Major** (citation drift).

### 🟡 Minor
**Definition**: Wrong detail, but a careful reader wouldn't be misled into action or misunderstanding.

**Triggers**:
- Stale realization name in a verification footer (the footer is metadata; readers don't act on it).
- Off-by-few line citation where adjacent lines say similar things.
- Imprecise capitalization in a function/variable name (e.g., `calcCropArea` vs `calcCroparea` — capital-A typo).
- Module renamed but old name still readable (e.g., `m15_food_demand` vs `15_food_demand`).
- Stale package/realization citation that's recoverable (correct concept, findable in a different location).

**Anchor examples**:
- 2026-03-08 (R16): claimed static realization for Module 34 uses LUH2 data, but `default.cfg` says LUH3. → **Minor** (doc ambiguity — the realization.gms file says LUH2 but config defaults to LUH3; a careful reader would check both).
- Citing `calcCroparea` as living in `mrcommons` when it's actually `mrlandcore` post-split — function name correct, package stale but findable. → **Minor**.

### 🟢 Informational
**Definition**: Style or doc issue, not a content error.

**Triggers**:
- Preamble before verb-first opening.
- Missing or malformed closing block (epistemic hierarchy markers 🟢/🟡/🟠/🔴/🔵 absent).
- Overlong response when a concise answer would suffice.
- Conservative tag (🟡 issued when 🟢 was earned and supported by source-read).
- Ordinal-syntax typos that don't change meaning (`t = 1` instead of GAMS `ord(t) = 1`).

**Anchor examples**:
- 2026-03-08 (R16): wrote `t = 1` instead of GAMS ordinal `ord(t) = 1`. Reader knows what was meant. → **Informational** (nitpick).
- Omitting the epistemic hierarchy badge on a low-stakes factual claim. → **Informational**.

### Tie-breaker

When between two tiers, **pick the lower** (less severe). Set `tier_uncertainty: true` in the bug record so trend analysis can flag if too many bugs are getting downgraded.

---

## 2. Mechanical checks (binary, per question)

Run these first; results are pre-computable and stable. Failures are NOT bugs — they're indicators that bugs are likely. Tracked separately from severity counts.

| # | Check | Pass criterion |
|---|---|---|
| **M1** | File:line citations present | Answer contains at least one `modules/XX_name/realization/file.gms:NN` citation when claiming concrete behavior |
| **M2** | Active realization stated | When discussing a module with multiple realizations, the answer states which realization it covers (and whether it matches default) |
| **M3** | Variable prefixes valid | All `vm_*`/`pm_*`/`v{N}_*`/`p{N}_*`/`s{N}_*`/`f{N}_*`/`i{N}_*` names use prefixes consistent with the prefix table in `core_docs/Bug_Taxonomy.md` Pattern 1 |
| **M4** | Epistemic hierarchy badges present | Each substantive claim has a 🟢/🟡/🟠/🔴/🔵 badge per AGENT.md "Epistemic Hierarchy" |
| **M5** | Confidence tier matches verification depth | A 🟢 source-verified claim must cite the file:line read THIS session; a 🟡 documented claim must cite the doc; a 🔴 inferred claim must say so |
| **M6** | Closing source statement | Answer ends with one of: "Based on module_XX.md documentation", "Verified against module_XX.md and modules/XX_.../file.gms:NN", or "Includes user feedback from module_XX_notes.md" |

---

## 3. Bug classes

The 14 patterns in `core_docs/Bug_Taxonomy.md` are restated here as scoring categories. Trend analysis can track class drift over rounds (which classes shrink, which persist).

| # | Class | Severity tendency | Detection |
|---|---|---|---|
| 1 | GAMS prefix confusion | Major | `scripts/check_gams_variables.sh` |
| 2 | Hallucinated variable name | Critical | `scripts/check_gams_variables.sh` |
| 3 | Suffix truncation | Major | Manual review |
| 4 | Conceptual pseudo-code | Major | Manual review |
| 5 | Stale reference after rename | Minor | `scripts/check_gams_variables.sh` post-rename grep |
| 6 | Hardcoded counts drift | Major | `scripts/validate_consistency.sh` Check 1 |
| 7 | Broken cross-reference | Minor | `scripts/validate_consistency.sh` Check 8 |
| 8 | Stale realization name (footer) | Minor | `scripts/check_gams_realizations.sh` |
| 9 | Wrong equation name | Major | `scripts/check_gams_equations.sh` |
| 10 | Stale file:line citation | Major | `scripts/check_gams_citations.sh` |
| 11 | Wrong GAMS filename | Major | Manual review |
| 12 | Content-level citation mismatch | Major | Manual review (verifier candidate) |
| 13 | Wrong parameter default value | Critical | `scripts/check_default_realizations.py` |
| 14 | Deployment copy drift | Minor | `scripts/validate_consistency.sh` Check 10 |

**Read this together with the Bug_Taxonomy.md anchor examples** — the taxonomy documents prevention strategies per pattern; this rubric scores when prevention failed.

---

## 4. Per-question scoring

```
raw_severity_weighted = 4·(critical count) + 2·(major count) + 1·(minor count) + 0·(informational count)
score_0_10 = max(0, 10 - raw_severity_weighted)
```

A question with zero bugs → 10. A question with one Major + two Minor → 10 − 2 − 1 − 1 = 6. A question with one Critical → 10 − 4 = 6 minimum.

**Why this weighting**: a single Critical bug is functionally equivalent to ~2 Major bugs or ~4 Minor bugs in terms of user harm. The weighting reflects the action-cost asymmetry, not bug-count parity.

---

## 5. Round composition

**Every round MUST include at least 1 regression question** alongside new probes. See `audit/validation_rounds.json` → `regression_questions` array.

- Regression questions are **calibration anchors** — they recur across rounds (`scope: "calibration_anchor"`, `exempt: true` in `probe_dedup_ledger.json`).
- If a regression question regresses (`drift_observed: true`), this is signal that something near it broke — investigate before introducing new probes.
- Initial regression set (R16+): G1 (module 14_yields default realization), G2 (vm_carbon_stock propagation). See §6 below for full text.

**Question dedup**: before finalizing the round design, run `python3 scripts/probe_dedup_check.py <round_design.md>`. Names appearing in past rounds within the lock-out window (3 rounds) flag a warning. Calibration anchors are exempt.

**Question count target**: 5 new probes + 1-2 regression questions per round. Targeted rounds (post-sync, single-module) may use 2-3 questions.

---

## 6. Initial regression-question set

These are the first 2 calibration anchors. They will be carried forward as `regression_questions` in every future round. Update only when the underlying ground truth changes (config default flip, equation rename, module refactor).

### G1 — Module 14 default realization (stability anchor)

**Question**: "What is the default realization of module 14 (yields)? List the equations defined in its equations.gms."

**Expected answer summary**: Default is `managementcalib_aug19`. Equations include `q14_yield_crop`, `q14_yield_past`, `q14_yieldcalib` (verify count and names against `modules/14_yields/managementcalib_aug19/equations.gms`).

**Ground truth source**: `config/default.cfg` line ~42 (search `cfg$gms$yields`) for default; `modules/14_yields/managementcalib_aug19/equations.gms` for equation list.

**Calibration intent**: tests whether the agent (a) consults default.cfg before describing the realization, (b) reads the actual equations file rather than reconstructing from memory, (c) reports the equation count correctly (Pattern 6 — Hardcoded counts drift).

### G2 — Carbon stock propagation (citation/chain anchor)

**Question**: "Walk through how `vm_carbon_stock` is computed in Module 52 and where it enters the GHG-policy cost in Module 56. Cite the relevant equations and file:line locations."

**Expected answer summary**: Module 52 defines `vm_carbon_stock` via equations linking land-use → carbon density → stock. Module 56's GHG policy multiplies `vm_carbon_stock` deltas by a carbon price into `vm_emission_costs`. Citations must point at actual lines in `modules/52_carbon/*/equations.gms` and `modules/56_ghg_policy/*/equations.gms`.

**Ground truth source**: `modules/52_carbon/*/equations.gms`, `modules/52_carbon/*/declarations.gms`, `modules/56_ghg_policy/*/equations.gms`.

**Calibration intent**: tests (a) cross-module dependency tracing, (b) precise file:line citations, (c) variable-name fidelity (no confabulation of related-sounding names like `vm_carbon_stocks`), (d) gate-tabulation behavior when the chain has multiple branches.

---

## 7. Audit report format

```markdown
## Audit Report: QN (Topic)

### Overall Verdict: [ACCURATE / MOSTLY ACCURATE / SIGNIFICANT ERRORS / FUNDAMENTALLY FLAWED]
### Accuracy Score: X/10

### Verified Claims (correct):
- [claim]: [evidence from code]

### Bugs Found:
- **Bug ID**: QN-BX
- **Severity**: [Critical / Major / Minor / Informational]
- **Class**: [one of the 14 classes from §3]
- **Trigger**: [which §1 trigger matched]
- **Claim in answer**: "exact quote"
- **Reality in code**: what the code actually does
- **File evidence**: `file_path:line_number` with the relevant snippet
- **Anchor reference**: [if this resembles an immutable anchor example, name it]

### Missing Nuances:
### Summary:
```

**Verdict to score mapping**:
| Score | Verdict | Typical profile |
|-------|---------|-----------------|
| 9-10 | Accurate | 0-1 Minor bugs; 95%+ claims confirmed |
| 8-8.5 | Mostly Accurate | 1-2 bugs (may include Major); structural simplifications |
| 6.5-7.5 | Mostly Accurate (lower band) | 3-5 bugs, some Major; missing nuances |
| 5-6 | Significant Errors | Heavy confabulation OR key var/eq wrong |
| 3-4 | Fundamentally Flawed | Fabricated formulas, wrong realization, invented variables |

---

## 8. Stability mechanisms

These exist specifically to prevent rubric drift across rounds:

1. **Immutable anchor examples** (§1) — each tier has 2-3 historical anchors that bound the meaning. New bugs are scored relative to them.
2. **Decision-tree triggers**, not feeling — pick the first trigger that fires, not the tier that "feels right".
3. **Tie-breaker pulls down** (§1) — when ambiguous between two tiers, the lower one is chosen. Tracked via `tier_uncertainty` so excessive downgrade can be detected.
4. **Finite bug-class list** (§3) — 14 classes; new classes added only at minor versions with rationale.
5. **Probe-dedup ledger** (`audit/probe_dedup_ledger.json`) — prevents rounds from re-probing names already in rule text (would conflate recognition with capability).
6. **Calibration anchors** (§6) — 1-2 questions recur every round. A regressing anchor flags something broke; a stable anchor with rising score is real improvement.

---

## 9. Changelog

- **v1.0 (2026-05-23)**: Initial hoist from `agent/commands/validate-semantic.md`. Severity tiers and bug-class list preserved verbatim from prior practice; anchor examples drawn from R3, R6, R16, R20, R21 detailed bug records in `audit/validation_rounds.json`. Established §5 (round composition with regression questions) and §6 (initial regression-question set G1/G2) as new structural requirements.
