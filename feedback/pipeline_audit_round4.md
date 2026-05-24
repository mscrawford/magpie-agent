# Pipeline Audit Round 4 (R4) — 2026-05-24

**Round type**: Structural audit of the magpie-agent's machinery (re-measure after R3 + R3-followup mechanizations)
**Scope**: 6 lenses, 6 parallel Opus sub-agents, **55 raw findings**
**Auditor model**: claude-opus-4-7
**Status**: Triaged + most CRITICAL/HIGH fixed + remaining LOW deferred
**Predecessors**: R1+R2 (`feedback/pipeline_audit_round1.md`), R3 (`feedback/pipeline_audit_round3.md`)

---

## Top-line numbers

| Lens | Findings | Notable |
|------|---------:|---------|
| 1. Doc↔code (code-reading) | 8 | M14 pcm_tau dimension stragglers; M39 fabricated cost breakdown |
| 2. Doc↔code (empirical-grep) | 16 | **9 wrong consumer attributions in M09**; M34 scaling 10× error |
| 3. Validator soundness | 8 | **Check 18 Pattern C regex was dormant** (HIGH); Check 14/21 don't scan helpers/commands |
| 4. Instruction-surface integrity | 8 | maintenance_protocol stale denominator; broken anchor templates |
| 5. Cross-doc consistency | 8 | M11 §3 attribution row drift (6 wrong); shadow-table sync gap |
| 6. Efficiency | 7 | Validator wall-clock 8.78s → 6.34s (-28%); trigger overlap persists from R3 |
| **Total** | **55** | |

**Severity distribution**:
- CRITICAL: **0** (down from R3's 3)
- HIGH: ~12
- MEDIUM: ~17
- LOW: ~26

**R3 mechanizations held**: The new Check 21 (`check_doc_var_existence.py`) and Check 19 body-citation extension caught zero net-new fabrications or body-realization drifts that the R3-followup work didn't already fix. The infrastructure is doing its job.

**Comparison to R3 (82 findings, 3 CRITICAL)**:
- Total findings: **-33%** (82 → 55)
- CRITICAL count: **3 → 0** (R3 fixed M11 §17.2 fabrication, M38 body drift, M73 wrong defaults; no new CRITICAL emerged in R4)
- HIGH count: ~17 → ~12 (-29%)
- The relocation pattern visible in R3 (bugs moved to body-citations and §17.2-style fabrications) did NOT recur — R3-followup's new validators are watching those surfaces now.

**Where R4 bugs concentrate** (per `[[feedback_confabulation_relocates]]`):
- **Cross-cutting doc consumer/attribution tables** (M09 §5.2; M11 §3; Module_Dependencies shadow tables; modification_safety_guide Appendix B). These are "hand-maintained denormalizations" of grep-derivable facts. R3 fixed primary tables; secondary "shadow" copies remained stale.
- **Validator coverage gaps** that R3-followup didn't close: Check 18 Pattern C regex broken (HIGH; was dormant in production!); helpers/commands not scanned by Check 14/21.
- **Numerical and citation drift** in less-trafficked sections (M52 Other land, M53 vm_feed_intake lines).

---

## Corroborated findings (high-confidence signal)

Three corroborations:

### 1. Shadow-table sync gap (Lens 4 + Lens 5)
- **Lens 4**: Module_Dependencies.md L268 says "25 modules" for M11, but L139 (R3 fix) says "27 modules" and L31 hub table says "27"
- **Lens 5**: modification_safety_guide.md Appendix B (L1075-1080) has all 6 consumer counts off by +1 — R3 fixed §1.2 but missed Appendix B
- **Root cause**: when R3 recomputed primary tables, secondary copies weren't swept
- **Action**: FIXED — see Cluster 3 below

### 2. Trigger overlap (Lens 4 + Lens 6, also R3 finding)
- "default realization" appears as trigger in BOTH verifiers.md and realization_selection.md
- "modify code" appears in BOTH verifiers.md and GAMS_MAgPIE_Patterns
- "scenario" substring fires 5 helpers
- **Persistent from R3**; not a new finding
- **Action**: DEFERRED (judgment call — narrow the triggers or accept the overlap)

### 3. M11 attribution drift across multiple sections (Lens 1 + Lens 5)
- Lens 1 found M14 pcm_tau dimension still wrong in M14 sections 7.2, 16.2 (cross-section sync)
- Lens 5 found M11 §3 had 6 wrong-attribution rows ("M50 or M51" for vm_p_fert_costs when actual is M54)
- **Pattern**: when a doc has multiple sections describing the same interface variable, fixes propagate to one section but not all
- **Action**: FIXED — see Cluster 4 below

---

## Root-cause clusters (synthetic interventions)

55 findings collapse to 11 clusters; Clusters 1-2 + 4 + 11 closed the highest-leverage issues.

### Cluster 1: Validator fix — Check 18 Pattern C regex was dormant (HIGH)

**Finding**: Lens 3 found `check_default_realizations.py:118` had regex `r"[Dd]efault\s+[Rr]ealization[:\s]*\`?(\w+)\`?"` that did NOT match the canonical `**Default Realization**: \`name\`` format used by ALL 46 module-doc headers (the `**` between Realization and `:` broke the match). Check 18 Pattern C was effectively dormant — only catching incidental matches in narrative prose.

**Action**: FIXED. Regex relaxed to allow optional bold wrappers. All 46 module docs now scanned cleanly.

### Cluster 2: Validator coverage extension — helpers/commands now scanned (HIGH)

**Finding**: Lens 3 found Check 14 (`check_gams_variables.py`) scoped to `modules/`, Check 21 (`check_doc_var_existence.py`) scoped to `cross_module/` + `core_docs/`. NEITHER scanned `agent/helpers/*.md` or `agent/commands/*.md`, where Lens 3 found a real bug: `s22_protect_scenario` in `debugging_infeasibility.md:119` should be `c22_protect_scenario` (config switch, not scalar).

**Action**: FIXED. Check 21 SCAN_DIRS extended to include `agent/helpers/` and `agent/commands/`. Surfaced 3 intentional fabrication examples in `verifiers.md` MANDATE 7 (allowlisted). The s22→c22 bug was fixed manually.

### Cluster 3: Shadow-table sync (HIGH; corroborated Lens 4 + Lens 5)

**Findings**: 
- Module_Dependencies.md L268: "25 modules" should be 27 (matches §3.2 R3 recount)
- modification_safety_guide.md Appendix B L1075-1080: 6 consumer counts off by +1 (R3 fixed §1.2 only)

**Root cause**: R3 spot-fixed primary tables but shadow copies remained.

**Action**: FIXED. Both tables updated; counts now consistent across documents.

### Cluster 4: M09 consumer table — 9 wrong attributions (HIGH)

**Findings**: M09 §5.2 "Provides To" table had wrong variable attributions for 7 of 14 consumer modules:
- M36 (im_pop → im_gdp_pc_mer_iso)
- M38 (im_gdp_pc_mer + im_development_state → im_gdp_pc_ppp_iso)
- M50 (im_development_state → im_pop_iso)
- M55 (im_gdp_pc_ppp_iso wrong; should be im_development_state)
- M60 (im_gdp_pc_mer_iso + im_development_state → im_pop_iso only)
- M62 (im_gdp_pc_mer_iso + im_pop_iso → im_pop only)
- M70 (im_development_state → im_pop + im_pop_iso)

Plus undercounts for M12 (missing im_pop_iso) and M42 (missing 2 vars), plus 1 wrong "im_development_state (6 modules)" → 5, plus 1 wrong "Urban land (Module 34)" attribution.

**Action**: FIXED. Recomputed all 14 module attributions via `find ../modules/<NN> -name '*.gms' -exec grep -oE 'im_<var>\b' {} \;` and rewrote the section.

### Cluster 5: M11 §3 attribution drift (HIGH; corroborated Lens 1 + Lens 5)

**Findings**: M11 §3 had 6 cost-variable rows with two-module attribution ("Module X or Module Y") despite each variable having a single producer. Worst case: `vm_p_fert_costs` attributed to "M50 or M51" — actual is M54 (phosphorus). Also 6× "30+ modules" should be "27 modules" (matches §17.2 authoritative).

**Action**: FIXED. All 6 attribution rows corrected; "30+" → "27" globally.

### Cluster 6: M14 cross-section consistency (MEDIUM)

**Finding**: M14 §2.2 has the correct `pcm_tau(j,"crop")` dimension after the f_btc2 rename to cluster level, but sections 7.2 and 16.2 still show `pcm_tau(h,...)`.

**Action**: FIXED. Both stragglers updated.

### Cluster 7: M29 vm_fallow/vm_treecover consumer attribution (HIGH)

**Finding**: M29.md table at L682-683 attributed vm_fallow and vm_treecover consumption to Module 44 (Biodiversity). Verified: neither M44 realization consumes either. Actual consumers: vm_fallow → M32/M50/M59; vm_treecover → M22/M59.

**Action**: FIXED.

### Cluster 8: M34 scaling values 10× off (HIGH)

**Finding**: M34.md at L112, L518, L520, L523: `vm_cost_urban.scale(j) = 10e3` was wrong by 10× (actual `scaling.gms:8` is `1e3`). Same for `v34_cost1.scale` and `v34_cost2.scale`.

**Action**: FIXED.

### Cluster 9: M53 overview contradicts its own section (HIGH + LOW)

**Findings**: M53 L13, L57 claimed "MACC technical mitigation for all 4 sources" / "All 4 sources include (1 - im_maccs_mitigation(...))". Only 3 of 4 sources have MACC mitigation; resid_burn does not. Doc's own §326 said this — internal contradiction. Plus 3 citation-line drifts.

**Action**: FIXED.

### Cluster 10: M52 Other land cite + M39 fabrication (MEDIUM)

**Findings**:
- M52 "Other land (start.gms:35)" and ":38" off by 13 lines (PR-shifted) — corrected to :48 and :51
- M39 fabricated cost breakdown "Clearing (3000), preparation (4000), infrastructure (5000), misc (300)" — no such breakdown in GAMS
- M39 Section 11.4 modification example mislabeled cropland-establishment cost as "forest clearing"

**Action**: FIXED.

### Cluster 11: AGENT.md cleanups (LOW)

**Findings**:
- L736-737 broken anchor templates (`#module-XX`, `#enforcement`)
- L777 broken anchor `#equation-1`
- L844 "Steps 2-3" should be "Step 2"
- maintenance_protocol.md L212 stale denominator (`/35`) after marker bump to 36

**Action**: FIXED.

---

## Findings deferred to future round

**LOW severity / judgment calls / structural-not-mechanical**:

1. M17 LOC count (115 → 124)
2. M40 systematic file-size +1 drift (5 table cells)
3. M14 preloop ~7-line cite drift
4. nitrogen_food_balance.md missing balanceflow term in q21_trade_glo
5. carbon_balance_conservation.md SCM/fallow/treecover terms omission
6. Module_Dependencies §5.2 diagram stale 14_yields arrow (own footnote contradicts)
7. **Multi-path VERIFIED_RE only validates first path** — mechanical, but adds a class of false negatives
8. **Allowlist marker typo silently fails** — brittleness fix
9. **Body-realization 50/50 split not flagged** — edge case
10. **Trigger overlap** (realization, modify code, scenario) — R3 finding persists; judgment call
11. **check_gams_equations.sh + check_gams_realizations.sh** Python rewrites — perf win
12. **Archives** (272KB; needs user confirmation per R3 plan)
13. **Session_startup.md section numbering** (mix of "### 0." and "### Step 2b:")
14. **pipeline-audit.md "new verifiers.md"** — stale "new" adjective

These will be queued in `feedback/next_session_plan.md` for a future round.

---

## Recurring classes (mechanization candidates for R5/R6)

Per `[[template_verifier_mandate_flywheel]]` — a class with ≥2 instances in this round is a candidate:

| Class | R4 instances | Prior rounds | Trajectory | Next mechanization |
|-------|-------------:|--------------|------------|--------------------|
| Shadow-table sync gap | 2 (M_Dep L268, safety_guide App B) | 1 (R3 Cluster 4) | RECURRING | Cross-doc dep-count checker (covers ALL tables, not just primary) |
| Wrong consumer attribution tables | 9 (M09) + 1 (M29) + 6 (M11) | 5+ (R3) | RECURRING | Generic "for every backticked `vm_*/pm_*/im_*`, verify producer/consumer claim against grep" |
| Validator coverage gaps in new scopes | 2 (Check 14/21 don't scan helpers, Check 18 dormant) | 2 (R3) | RECURRING | Periodic "regex coverage audit" — explicit test cases for each common format variant |
| Multi-section consistency within one doc | 1 (M14 pcm_tau) | 0 | NEW | New check: when a backticked identifier is mentioned >1× in a single doc, verify all mentions use consistent dimensions/attribution |
| Citation line drift after code changes | 4+ (M14, M52, M53, M40) | 12+ (R3 Cluster 3) | RECURRING | Already addressed by Pattern 12 (advisory) + R3's resolver fix; persists at advisory level |

**Strongest R4 mechanization candidates** (queued for next session):
1. **Generic dep-count checker** — would close Clusters 3 + 5 entirely (M09 + M11 + Module_Dependencies + safety_guide all in one pass).
2. **Multi-section consistency check** — would catch M14 pcm_tau stragglers and similar.
3. **VERIFIED_RE multi-path fix** — ~5 LOC; closes a known FN class.

---

## Comparison to prior rounds

| Category | R1 | R2 closed | R3 | R3-followup | R4 | Trend |
|----------|---:|----------:|---:|------------:|---:|-------|
| Total findings | 71 | — | 82 | — | 55 | ↘ NEW LOW |
| CRITICAL | 1 | 1 | 3 | 3 | **0** | ↘↘ excellent |
| HIGH | 14 | 11 | 17 | many | ~12 | ↘ improving |
| Cross-doc consumer/attribution drift | 6 | 3 spot | 8 | 4 spot | 16 | ↗ chronic — needs generic checker |
| Validator coverage gaps | 8 | 2 | 12 | 4 | 4 | ↘ improving |
| Confabulation in §17.2-style | 0 (then) | — | 14 | 14 | **0** | ✅ Closed by Check 21 |
| Multi-realization body drift | 13 (footer) | 13 | 4 (body) | 1 (M38 fixed) | 0 | ✅ Closed |
| Citation drift | 10 | 5 | 12 | 6 | 4+ | ↘ improving |

**Confabulation-relocation prediction REVERSED in R4**: R1→R3 showed the textbook pattern (each closure pushes bugs to new surfaces; total stayed ~constant). R3→R4 shows actual reduction (82 → 55 = -33%) and CRITICAL elimination (3 → 0). This suggests R3-followup's new validators (Check 21 + body-citation extension) closed CLASSES of bugs, not just individual instances. The infrastructure is converging.

---

## What R4 did (this session, 2026-05-24)

**Fixed in this session**: ~25 findings across 11 clusters. Single commit `d0870ae`.

**Validator state at session end**:
- `bash scripts/validate_consistency.sh`: **35/36 passed**, 1 known advisory (`s59_nitrogen_uptake` Pattern 13 unit-conv FP)
- `python3 scripts/check_module_realizations.py`: **0 errors, 0 warnings**
- `python3 scripts/check_gams_variables.py`: **100% (953/953 verified)**
- `python3 scripts/check_doc_var_existence.py`: **100% (312/312 verified)** — scope now includes helpers + commands
- `python3 scripts/check_default_realizations.py`: **all 46 modules clean** — Check 18 actually operational now after regex fix
- Validator wall-clock: **6.34s** (-28% from R3's 8.78s)

**Deferred** (with explicit reasons): see "Findings deferred" section above; queued in `feedback/next_session_plan.md`.

---

## Status (final, post-fix session)

R4 fixes landed in 1 commit (cluster-bundled per autonomous-mode triage):
- `d0870ae` — fix(R4): triage and fix wave for pipeline-audit round 4 (covers Clusters 1-11)

Plus this commit (R4 audit log + JSON entry + next_session_plan update).
