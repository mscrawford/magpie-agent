# Flywheel rubric (v1.2)

Used by the Opus auditor to score Sonnet magpie-agent answers in semantic-validation rounds (`/validate-semantic`). Designed to maximize stability across rounds (so trends are real) while staying sensitive to actual agent improvements.

**Version**: 1.2 (2026-05-29). Bumps required for any change to severity criteria, anchor examples, or bug-class definitions. Adding new bug classes and extending the regression-question set is permitted at minor versions (1.x). See §9 Changelog.

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

### Latent doc bugs (record independent of the answer score)

The score above measures the ANSWER. A correct answer can still rest on a WRONG doc: the answerer (docs-only) sometimes re-derives the right fact from code, or guesses correctly, despite a doc claim that contradicts the code. The bug is then invisible to the score - and the next round's answerer may trust the bad doc and reproduce it.

**Mandate**: when the answer is correct but relied on a **load-bearing** doc claim (interface variable, equation, populator/consumer set, realization, or default) that is WRONG versus code, the auditor MUST record a bug with root cause `doc_error_answerer_beat_it`. It does NOT lower the answer's score (the answer was right), but it is recorded in the question's `doc_errors_latent[]` and FIXED this session anyway (validate-semantic.md Step 5). Severity is assessed by the harm to a future reader who trusts the doc: a wrong producer/consumer set is **Critical** per the R20 anchor even when this round's answer dodged it.

**Anchor example (immutable)** - G2 carbon-stock populators: R22 found the doc's populator list wrong (3 bugs) but the answer's spine was right; R23 scored 10 because the answerer re-enumerated from code, and the doc fix was declined ("answer was right, no doc bug"); the wrong list stayed in `module_56.md`/`module_52.md` and R26 regressed to 7 when a later answerer trusted it. Under this mandate the R23 auditor records a `doc_error_answerer_beat_it` (Critical, by future-reader harm), Step 5 fixes the doc unconditionally, and the regression never happens. (Fixed R26; anchor recovered to 9 at R27.)

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
| 15 | Latent doc error (answer beat the doc) | by future-reader harm (often Critical) | doc-vs-code cross-check; `scripts/check_consumer_attribution.py` (prose) |

Classes 1-14 map to the `core_docs/Bug_Taxonomy.md` patterns; **class 15 is flywheel-specific** (added v1.2) - it has no Bug_Taxonomy entry because it is a scoring category for the §1.5 latent-doc-bug case (answer correct, doc wrong), not a doc-authoring pattern.

**Read this together with the Bug_Taxonomy.md anchor examples** — the taxonomy documents prevention strategies per pattern; this rubric scores when prevention failed.

---

## 4. Per-question scoring

```
raw_severity_weighted = 4·(critical count) + 2·(major count) + 1·(minor count) + 0·(informational count)
score_0_10 = max(0, 10 - raw_severity_weighted)
```

A question with zero bugs → 10. A question with one Major + two Minor → 10 − 2 − 1 − 1 = 6. A question with one Critical → 10 − 4 = 6 minimum.

**Why this weighting**: a single Critical bug is functionally equivalent to ~2 Major bugs or ~4 Minor bugs in terms of user harm. The weighting reflects the action-cost asymmetry, not bug-count parity.

### Round-level doc-quality mean (v1.2)

The headline `mean_score` (and `cumulative_stats.mean_score_trend`) is the RAW per-question mean and **stays raw** for cross-round comparability. Report a second figure alongside it:

> `doc_quality_mean` = mean of per-question scores **excluding** questions whose bugs are exclusively `answerer_confabulation` (the doc was correct; the answerer was sloppy). Questions with any `doc_error` / `doc_error_answerer_beat_it` bug stay IN. Also report `n_questions_doc_quality` (count kept) and a one-line `doc_quality_mean_method`.

This separates doc quality (what the flywheel exists to improve) from answerer noise. Example - R27: the raw mean 7.1 was dragged by Q5/M20 (4/10), a pure answerer confabulation against a verified-correct doc; excluding it, doc-quality is ~7.6. Never substitute `doc_quality_mean` for the raw mean; report both.

---

## 5. Round composition

**Every round MUST include at least 1 regression question** alongside new probes. See `audit/validation_rounds.json` → `regression_questions` array.

- Regression questions are **calibration anchors** — they recur across rounds (`scope: "calibration_anchor"`, `exempt: true` in `probe_dedup_ledger.json`).
- If a regression question regresses (`drift_observed: true`), this is signal that something near it broke — investigate before introducing new probes.
- Initial regression set (R16+): G1 (module 14_yields default realization), G2 (vm_carbon_stock propagation). See §6 below for full text.

**Question dedup**: before finalizing the round design, run `python3 scripts/probe_dedup_check.py <round_design.md>`. Names appearing in past rounds within the lock-out window (3 rounds) flag a warning. Calibration anchors are exempt.

**Question count target**: 5 new probes + 1-2 regression questions per round. Targeted rounds (post-sync, single-module) may use 2-3 questions.

---

## 6. Regression-question set

These calibration anchors are carried forward as `regression_questions` in every future round. Each round must score against at least one. Update only when the underlying ground truth changes (config default flip, equation rename, module refactor, version pin advance).

The authoritative source for the full text and expected-answer details is `audit/validation_rounds.json` → `regression_questions[]`. The summaries below are the rubric-side reference; on conflict, the JSON wins (it gets updated as bugs are corrected — e.g., the G1 equation list was corrected in R22 audit).

### G1 — Module 14 default realization (stability anchor)

**Question**: "What is the default realization of module 14 (yields)? List the equations defined in its equations.gms."

**Expected answer summary**: Default is `managementcalib_aug19` (verify via `grep cfg$gms$yields ../config/default.cfg`). Equations defined in `modules/14_yields/managementcalib_aug19/equations.gms`: exactly 2 — `q14_yield_crop` and `q14_yield_past`. (R22 audit corrected an earlier rubric draft that listed a non-existent `q14_yieldcalib`.)

**Ground truth source**: `config/default.cfg` (search `cfg$gms$yields`) for default; `modules/14_yields/managementcalib_aug19/equations.gms` for the equation list.

**Calibration intent**: tests whether the agent (a) consults default.cfg before describing the realization, (b) reads the actual equations file rather than reconstructing from memory, (c) reports the equation count correctly (Pattern 6 — Hardcoded counts drift).

### G2 — Carbon stock propagation (citation/chain anchor)

**Question**: "Walk through how `vm_carbon_stock` is computed in Module 52 and where it enters the GHG-policy cost in Module 56. Cite the relevant equations and file:line locations."

**Expected answer summary**: `vm_carbon_stock` is DECLARED in Module 56 (`price_aug22/declarations.gms:34`) — NOT in Module 52. Land modules (29, 31, 32, 34, 35) and Module 59 (SOM) POPULATE it. Module 52 only READS it via `q52_emis_co2_actual` (`normal_dec17/equations.gms:16-19`). The Module-56 chain is `q56_emis_pricing_co2` → `v56_emis_pricing` → `q56_emission_cost_oneoff` → `v56_emission_cost` → `q56_emission_costs` → `vm_emission_costs(i)`. (R22 audit corrected an earlier rubric draft that attributed the declaration to M52.)

**Ground truth source**: `modules/56_ghg_policy/price_aug22/declarations.gms` (declaration site), `modules/52_carbon/normal_dec17/equations.gms` (reader), `modules/56_ghg_policy/price_aug22/equations.gms` (pricing chain), `modules/29_cropland/`, `31_past/`, `32_forestry/`, `34_urban/`, `35_natveg/`, `59_som/` (populators).

**Calibration intent**: tests (a) cross-module dependency tracing, (b) precise file:line citations, (c) variable-name fidelity (no confabulation of related-sounding names like `vm_carbon_stocks`), (d) gate-tabulation behavior when the chain has multiple branches, (e) producer-vs-consumer distinction.

### G3 — magpie4 source-of-truth discipline (version-pin anchor) — added v1.1

**Question**: "Which version of magpie4 does this agent's source-of-truth clone reflect, and how was that version determined? Cite the file(s) you read."

**Expected answer summary**: Agent must read `project/version_pins.json` (NOT the workspace clone at `~/Documents/Work/Workspace/magpie4/`). Reports the version and SHA from that file; identifies the upstream authoritative source as `../input/renv.lock` (`Packages.magpie4`, fields `Version` + `RemoteSha`). The workspace clone is intentionally NOT source-of-truth (drifts ahead of the renv pin). Pin can be regenerated via `python3 scripts/sync_magpie4_clone.py`.

**Ground truth source**: `project/version_pins.json` (the cached pin snapshot), `../input/renv.lock` (Packages.magpie4 entry). The auditor MUST read `project/version_pins.json` directly to compute the expected version/SHA at audit time — do not hardcode it here (pin advances when the user pulls upstream MAgPIE).

**Calibration intent**: tests (a) source-of-truth discipline for the two-clone setup (SHA-pinned `.cache/sources/magpie4/` vs drift-prone workspace clone), (b) auto-load of `agent/helpers/magpie4_reference.md` before answering (its three pre-answer rules), (c) version-pin awareness (no confabulation from training data).

### G4 — magpie4 getReport dispatch (R-package structural anchor) — added v1.1

**Question**: "How does `magpie4::getReport` organize its reporting? Describe the dispatch pattern, how many unique `report*` functions it calls, and cite the file:line range from the pinned clone."

**Expected answer summary**: Agent reads from `.cache/sources/magpie4/R/getReport.R` (the SHA-pinned clone). Dispatch is a flat `tryList(...)` of unconditional calls to ~106 unique `report*` functions (117 total call lines — some functions called multiple times with different argument combos: `reportYields(..., physical=T/F)`, `reportProcessing(..., indicator=...)`, `reportPriceFoodIndex(..., baseyear=...)`, `reportAgEmployment(..., type=...)`, `reportWageDevelopment(..., baseYear=...)`, `reportFactorCostShares(..., type=...)`, `reportGrowingStock(..., indicator=...)`). There is NO `control` argument and NO `if (any(grepl(...)))` filtering. Signature: `getReport(gdx, file=NULL, scenario=NULL, filter=c(1,2,7), detail=TRUE, level="regglo", ...)`. Body lines ~56-235; tryList block ~62-181 (v2.70.0 @ a360d8c9ec — re-verify on the pinned clone).

**Ground truth source**: `.cache/sources/magpie4/R/getReport.R` at the version_pins.json-pinned SHA.

**Calibration intent**: tests (a) reading from the SHA-pinned clone rather than the workspace clone, (b) faithful description of dispatch (no confabulation of control-based gating or grepl filtering — this was the magpie4 plan's initial-but-wrong description), (c) reasonable count of unique `report*` functions (off-by-few = Minor; off-by-order = Critical), (d) precise file:line citation with version pin per MANDATE 16.

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
- **v1.1 (2026-05-24)**: Extended the §6 regression-question set with G3 (magpie4 source-of-truth / version-pin discipline) and G4 (magpie4 getReport dispatch structure), following the 2026-05-24 magpie4 lean-scaffolding initiative (commit d44823f). G1 expected-answer text in §6 corrected to remove the non-existent `q14_yieldcalib` reference (R22 audit had already corrected the JSON; v1.0 rubric was stale on this point). §1 severity tiers unchanged — the existing "Invented variable name", "Citation drift", and "Module attribution" triggers cover magpie4-specific bugs naturally (with `report*` function names and the two-clone source-of-truth distinction as the new surface).
- **v1.2 (2026-05-29)**: Added §1.5 "Latent doc bugs" - record a `doc_error_answerer_beat_it` when the answer is correct but relied on a wrong doc, and fix it regardless of the answer score - with the G2 regression as its immutable anchor. Added bug class 15 (flywheel-specific, beyond the 14 Bug_Taxonomy patterns). Added §4 "Round-level doc-quality mean". Closes the score-the-answer-not-the-doc blind spot that let the G2 anchor regress R22->R23->R26. Companion edits: validate-semantic.md Steps 3/5/5b; validation_rounds.json schema 1.3.
