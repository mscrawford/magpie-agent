# Validate Semantic Accuracy (Flywheel)

**Purpose**: Run adversarial semantic validation of the documentation — test whether the docs produce *correct answers*, not just syntactically valid references.

**When user says**: "/validate-semantic", "semantic validation", "test doc quality", "run the flywheel", etc.

**Complements**: `/validate` (syntactic checks) — this tests *meaning*, that tests *form*.

---

## Overview

The semantic validation flywheel generates expert questions, answers them from docs, audits answers against GAMS source code, and identifies documentation inaccuracies that syntactic checks can't catch.

```
GENERATE → ANSWER (Sonnet) → AUDIT (Opus) → SYNTHESIZE → IMPROVE → EXPAND
```

**Baseline**: See `audit/validation_rounds.json.cumulative_stats` for current totals (<!--count:total_rounds-->24<!--/count--> rounds, <!--count:total_docs_validated-->85<!--/count--> docs validated, <!--count:total_bugs_found-->474<!--/count--> bugs found, <!--count:total_bugs_fixed-->314<!--/count--> fixed as of last update). Authoritative trend is the `mean_score_trend` field in that file — do not duplicate it here (would drift).

---

## Targeted Mode

When specific modules need re-validation (e.g., after a sync updates them), use targeted mode:

**Usage**: `/validate-semantic --modules 14,29,32`

**Targeted workflow** (lighter than full round):
1. Generate 2-3 questions specifically about the named modules and their interactions
2. Answer via Sonnet 4.6 from docs only
3. Audit via Opus 4.6 against GAMS source
4. Fix any bugs found
5. Log as a targeted round in validation_rounds.json (type: "targeted")

**When to use targeted mode**:
- After `/sync` updates >3 module docs
- When a user reports an error in a specific module doc
- After adding a new realization to a module
- Before a release, for modules changed since last validation

**Targeted rounds are lighter**: ~15 min, 2-3 questions, 4-6 agents total.

---

## Drift-Triggered Validation

The maintenance protocol defines when semantic validation should run automatically:

### Automatic Triggers
| Trigger | Action | Priority |
|---------|--------|----------|
| `/sync` updates >3 modules | Targeted validation on updated modules | High |
| Quarterly (no validation in 90 days) | Full round (5 questions) | Medium |
| User reports doc error | Targeted on affected module + neighbors | High |
| New realization added | Targeted on that module | Medium |
| GAMS variable/equation check fails | Targeted on affected modules | Critical |

### Integration with `/sync`
When `/sync` completes and has updated module docs:
1. Sync reports which modules were updated
2. Agent suggests: "📋 Updated modules 14, 29, 32. Run `/validate-semantic --modules 14,29,32` to verify accuracy?"
3. User confirms → targeted round runs
4. Results appended to validation_rounds.json

### Integration with Session Startup
Session startup checks `validation_rounds.json` for last validation date:
- If >90 days since last round → include in greeting: "⚠️ Semantic validation overdue (last: [date])"
- If last round had Critical bugs → warn: "🔴 Last validation found Critical issues"

---

## Step-by-Step Execution

> **Round artifacts convention**: write the round's scratch markdown (design, `answers/`, `audits/`, synthesis) to `audit/archive/rounds/round{N}_*` — NOT the `audit/` top level. The living record is `audit/validation_rounds.json` (top level); the per-round markdown is frozen history kept in `archive/rounds/`, where validators skip it.

### Step 1: Generate Questions

**Before designing questions**: review `audit/probe_dedup_ledger.json`. Names appearing there within their lock-out window are off-limits for fresh probes (would test recognition, not capability). Calibration anchors are exempt — they recur by design.

**Each round MUST include at least 1 regression question** from `audit/flywheel_rubric.md` §6 (current set: G1 module-14 default realization, G2 vm_carbon_stock propagation, G3 magpie4 source-of-truth / version-pin discipline, G4 magpie4 getReport dispatch structure) alongside new probes. See `audit/validation_rounds.json` → `regression_questions` array. **Rotate** so all four are exercised over a few rounds — the magpie4 anchors (G3, G4) are especially load-bearing because they protect the version-pin discipline the agent depends on for correct magpie4 source reads.

Design 5 new probes + 1-2 regression questions using this rotation of **6 archetypes**:

| Archetype | Description | Example |
|-----------|-------------|---------|
| **Cross-module causal chain** | Trace a signal through 3+ modules | "How does carbon price → afforestation → carbon stock?" |
| **Default vs. switch behavior** | Ask what happens with default config | "By default, is water cost enabled?" |
| **Quantitative verification** | Request specific numbers/formulas | "Calculate the N release from SOM loss" |
| **Timing/sequencing** | Ask about execution order | "Is preloop per-timestep or once?" |
| **Conservation law enforcement** | Ask how constraints work | "How does land balance prevent double-counting?" |
| **Edge case/failure mode** | Ask what causes problems | "What makes the water module infeasible?" |
| **R-to-GAMS provenance** (magpie4) | Trace a report.mif variable back to its GAMS origin | "Where does the IAMC variable `Emissions\|N2O\|Land` come from? Trace from the magpie4 function to the underlying GAMS module." |

**Question design rules**:
1. Each GAMS-side question must span **≥3 modules**. *Exception*: magpie4 R-package questions can be single-package since magpie4 itself is one layer above all modules — but they must still cite version-pinned source paths (`.cache/sources/magpie4/...`).
2. Each question must require reading **≥2 doc files** (or for magpie4: ≥1 source file from the pinned clone + the helper)
3. Cover modules **not tested in previous rounds** (check coverage matrix below)
4. Bias toward **high-centrality modules**: 11, 10, 56, 32, 30, 70, 17, 09
5. Include specific requests for variable names, equations, formulas, or `report*` function names (forces precision)
6. **Include at least one magpie4 question every 2-3 rounds**: the helper is new (2026-05-24) and under-validated. Good targets: report.mif variable provenance, version-pin discipline, getReport dispatch structure, IAMC-hierarchy traversal. The auto-loaded helper is `agent/helpers/magpie4_reference.md`.

### Step 2: Answer with Sonnet

Launch **5 parallel Sonnet 4.6 agents** (or current answering model), each with:
- The question
- Instructions to answer using **ONLY magpie-agent docs** (no raw GAMS code)
- Instructions to cite specific variable names, equations, file references

Use the `magpie-helper` agent type. This simulates what a real user would get.

**Prompt template**:
```
You are answering an expert-level question about MAgPIE's inner workings.
Answer using ONLY the magpie-agent AI documentation files (in the magpie-agent/ directory).
Do NOT read raw GAMS source code files.
Cite specific variable names (vm_*, pm_*), equation names (q*), and file references.

QUESTION: [question]
```

### Step 3: Audit with Opus

Launch **5 parallel Opus 4.6 agents** (or highest-capability model), each with:
- The question + the Sonnet answer
- Instructions to verify **every claim** against raw GAMS source code
- A pointer to **`audit/flywheel_rubric.md`** for severity tiers, mechanical checks, bug classes, and the audit report format.

Use the `general-purpose` agent type with `model: claude-opus-4.6`.

**Scoring spec** (severity tiers, immutable anchor examples, per-question scoring formula, audit report format) is in `audit/flywheel_rubric.md`. The auditor MUST read it before scoring. Do NOT inline-restate the rubric here — it drifts; the rubric file is the authority.

### Step 4: Synthesize

After all audits complete:

1. **Create a SQL bugs table** for structured analysis:
```sql
CREATE TABLE bugs (id TEXT PRIMARY KEY, question TEXT, severity TEXT, bug_type TEXT, description TEXT);
```

2. **Run analysis queries**:
```sql
-- By severity
SELECT severity, COUNT(*) FROM bugs GROUP BY severity;
-- By type (find systemic patterns)
SELECT bug_type, COUNT(*) FROM bugs GROUP BY bug_type ORDER BY COUNT(*) DESC;
-- By question (find weakest areas)
SELECT question, COUNT(*) FROM bugs GROUP BY question;
```

3. **Classify into the three known root-cause patterns**:
   - **"Interesting Over Default"**: Agent picks non-default realization or switched-off features
   - **"Plausible Confabulation"**: Agent invents formulas, causal chains, or numbers
   - **"Documentation Drift"**: Line numbers, defaults, or terms are stale

4. **Update the coverage matrix** (see below)

### Step 5: Improve

Fix bugs in priority order:
1. **Critical** bugs → fix immediately in module docs
2. **Major** bugs → fix in the same session
3. **Minor** bugs → batch into notes files for later

Use Sonnet 4.6 agents (NOT Opus) for fixes — the audit reports already specify exactly what's wrong and what the correct code says.

After fixing, run `bash scripts/validate_consistency.sh` to ensure no syntactic regressions.

### Step 5b: Record Results

**MANDATORY**: Append results to `audit/validation_rounds.json` (schema v<!--count:validation_schema_version-->1.2<!--/count-->; latest entries describe G3/G4 magpie4 regression questions). This is the persistent record for tracking quality over time. Include:
- Round number, date, commit hashes (before/after)
- Per-question: topic, modules tested, score, bug counts by severity
- **Regression questions section**: score the round's regression questions (rotate across G1-G4 per `regression_questions` top-level array; minimum 1 per round). Set `drift_observed=true` if any answer drifted from the expected_answer_summary. Append round number to `used_in_rounds` for each used. For G3 (magpie4 version pin), the auditor must read `project/version_pins.json` directly to compute the expected version/SHA — do NOT score against a hardcoded version, the pin advances when upstream renv.lock updates.
- Summary: mean score, total bugs, bug sources (doc_error vs answerer_confabulation), root causes, files fixed, safeguards added
- Update `cumulative_stats` at the bottom

**Schema v1.1 changes** (2026-05-23): top-level `regression_questions` array added; each new round MUST include at least 1 regression question alongside new probes. Severity tiers and audit format are now in `audit/flywheel_rubric.md` (hoisted from this command file).

This file allows future agents to compute trends: score over time, confabulation rate, calibration-anchor drift, which modules are reliable vs fragile.

### Step 5c: Update probe-dedup ledger (R6 H3)

After Step 5b records the round, run the dedup-check to append new probe names to `audit/probe_dedup_ledger.json` and increment `retirement_eligible_after` per the ledger's `rotation_policy`. This was previously dead — the policy said "next round R22" while actual was R24, meaning R22-R24 names never entered the ledger.

```bash
python3 scripts/probe_dedup_check.py
```

The script reads the last round in `validation_rounds.json`, extracts probe names that should enter the ledger, appends them with `retirement_eligible_after = current_round + 3` per policy. If new probes added: commit the ledger update with the round commit.

### Step 6: Expand Coverage

Update the coverage matrix and design next round's questions to fill gaps:

**Coverage Matrix Template** (module × archetype):

| Module | Causal Chain | Default/Switch | Quantitative | Timing | Conservation | Edge Case |
|--------|:-----------:|:--------------:|:------------:|:------:|:------------:|:---------:|
| 10_land | R1 | | | | | |
| 11_costs | R1 | | | | | |
| 12_interest | R1 | | | | | |
| 13_tc | R1 | | | | | |
| 14_yields | R1 | | | | | |
| ... | | | | | | |

Mark each cell with the round number (R1, R2, ...) when tested.

---

## Metrics

Track across rounds:

| Metric | R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 | R9 | R10 | R11 | R12 | R13 |
|--------|-----|-----|-----|-----|-----|-----|-----|-----|-----|------|------|------|------|
| Mean accuracy score | 6.7 | 8.2 | 5.8 | 8.6 | 7.2 | 8.7 | 6.9 | 6.0 | 7.5 | 7.0 | 7.6 | 7.3 | 8.6 |
| Total bugs | 40 | 17 | 52 | 11 | 16 | 7 | 26 | 47 | 18 | 22 | 30 | 18 | ~10 |
| Critical bugs | 3 | 0 | 4 | 0 | 0 | 0 | 6 | 12 | 1 | 7 | 3 | 4 | — |
| Doc errors | ~20 | ~9 | 32 | 3 | 0 | 0 | 26 | 47 | 16 | 17 | 15 | 18 | — |
| Answerer errors | ~20 | ~8 | 44 | 8 | 16 | 7 | 0 | 0 | 2 | 5 | 15 | 0 | — |
| Scope | modules | modules | modules | modules | modules | modules | cross-mod | core/arch | modules | ref docs | helpers | GAMS lang | re-test |

**R1-R6** (module docs): Mean ≥8.5 ✅ (R6: 8.7), zero Critical ✅ (since R4), zero doc errors ✅ (R5+R6).

**R7-R10** (non-module docs): 113 bugs across 16 docs. Worst: fabricated variables, missing execution phases.

**R11** (helpers): Found vegan diet recipe silently broken (diet=3 ignores c15_EAT_scen), fabricated slack variable, wrong file paths. debugging_infeasibility.md was worst helper (5/10).

**R12** (GAMS language docs vs official gams.com): Wrong inline comment syntax throughout GAMS_Fundamentals, power() incorrectly allowing non-integer exponents, reversed .prior branching priority.

**R13** (module re-test): Post-fix quality check on 5 previously-validated modules. 4/5 scored ≥9.0, confirming fixes hold. ~10 bugs found, mostly minor drift.

**Key insight**: Every doc category had errors when first validated. The flywheel's value is systematic first-pass coverage — scores jump 2-3 points after fixes. Authoritative cumulative counts live in `audit/validation_rounds.json.cumulative_stats`; cite those rather than restating numbers here (the restated form drifts as rounds accumulate).

---

## Quality Trend Analysis

### Score Progression
- **Module docs** (R1→R6): 6.7 → 8.2 → 5.8 → 8.6 → 7.2 → 8.7 (converging upward)
- **Non-module docs** (R7→R10): 6.9 → 6.0 → 7.5 → 7.0 (needed more work)
- **Specialized docs** (R11→R12): 7.6 → 7.3 (helpers + GAMS language)
- **Re-test** (R13): 8.6 (confirms fixes hold)

### Recurring Bug Patterns (top 5)
1. **Fabricated counts** (23% of bugs): AI invents plausible numbers for stages, sets, parameters
2. **Wrong equation name** (18%): Prefix/suffix errors (q18_prod_res_ag_clust vs _reg)
3. **Realization confusion** (15%): Features from wrong realization described
4. **Missing default caveat** (12%): Mechanisms described without noting they're OFF by default
5. **Stale parameter values** (10%): Numbers that were correct when written but drifted

### Recommended Focus for Future Rounds
- Modules with most equation changes since last sync
- Helper docs (highest fabrication rate: 7.6/10 mean)
- Any module scoring <7.0 in its last validation

---

## Resource Usage

| Phase | Model | Count | ~Duration Each | Total |
|-------|-------|-------|----------------|-------|
| Answer | Sonnet 4.6 | 5 | 3-4 min | ~18 min |
| Audit | Opus 4.6 | 5 | 5-7 min | ~30 min |
| Fix | Sonnet 4.6 | 5 | 3-5 min | ~20 min |

**Per round**: ~5 Opus calls (audit only) + ~10 Sonnet calls (answer + fix).
**Opus is needed ONLY for the audit phase** — everything else uses Sonnet.

---

## Question Bank (Validated, Round 1)

These questions were used in Round 1 and can be reused for regression testing after doc improvements:

1. **Land-Carbon-Forestry** (modules 10, 32, 52, 56): "When a carbon price incentivizes afforestation in MAgPIE, trace the complete causal chain..."
2. **Livestock-Feed-Cropland** (modules 70, 21, 30, 29, 14): "Explain the full cascade from livestock demand to cropland allocation..."
3. **Water-Irrigation-Yield** (modules 42, 43, 14, 30): "Describe the coupling between water availability and agricultural yields..."
4. **Nitrogen-SOM-Emissions** (modules 50, 51, 59, 53): "Trace the nitrogen cycle through MAgPIE..."
5. **Cost Aggregation** (modules 11, 12, 56, 57, 39): "MAgPIE minimizes total global costs — explain exactly what enters the objective function..."

---

## When to Run

- **After major doc updates** (post-sync, post-audit fix cycle)
- **Monthly** as routine quality assurance
- **Before releases** to verify documentation quality
- **When new modules are documented** to ensure accuracy from the start
