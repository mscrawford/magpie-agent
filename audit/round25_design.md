# R25 Design — Phase 3 Re-measure

**Created**: 2026-05-25
**Plan reference**: `audit/get_under_control_plan.md` Phase 3 — "Did the bomb rate drop?"
**Baseline at launch**: `scripts/validate_consistency.sh` 39/41 + 2 acceptable warnings (1 advisory + units); `check_units` 5 advisory; `check_consumer_attribution` 0 mismatches + Pattern D clean.
**Pre-condition**: magpie4 SHA-pinned clone present at `.cache/sources/magpie4/` (v2.70.0 @ a360d8c9ec).

## Question budget

5 new probes + 2 regression (G1, G2) = **7 questions**.

Regression rotation: G3/G4 (magpie4 anchors) used in R24; per plan "Rotate back to G1+G2 anchors" — both G1 and G2 fired to maximize signal on whether the AGENT.md trim degraded coverage.

## Module targets

Plan-mandated targets:
- **Phase 2 sweep modules** (must surface no bombs to validate sweep): M30, M80, M11.
- **High-bomb-probability fresh modules**: M11, M38, M52, M53, M70.
- **magpie4 routing** must be exercised organically (not just via G3/G4).

Probe-dedup status (`audit/probe_dedup_ledger.json`): M30 (eligible R23), M80 (eligible R24), M11 (not in ledger), M38 (eligible R24), M52 (calibration-exempt), magpie4 (new helper). All clear for R25.

## Questions

### Q1 — Phase 2a sweep test (M30 default rotational constraints)

**Archetype**: Default-vs-Switch + Cross-module Causal-chain
**Modules**: 30, 29, 10 (cropland → rotation constraints → land balance)

> In MAgPIE's default configuration, what rotational constraints apply to cropland allocation in Module 30? Name the active realization, the equation(s) implementing the constraint(s), and the file:line where they are declared. Then say how the alternative realization differs in mechanism (not just file name).

**Phase 2a gate**: answer must cite `simple_apr24` file:line for any default-behavior claim. If the answer surfaces `detail_apr24/equations.gms:NN` for default behavior, the 2a sweep was superficial.

### Q2 — Phase 2b sweep test (M80 default solver scalars)

**Archetype**: Quantitative + Default-vs-Switch
**Modules**: 80, 11, 09 (optimization → cost objective → drivers)

> List the scalars in MAgPIE's default optimization realization that control solver behavior (re-solve attempts, max iterations, optfile selection, NLP relaxation), with each scalar's default value and source file:line. Name the active realization explicitly, and contrast 2-3 scalars against the alternative realization where the defaults differ.

**Phase 2b gate**: answer must use the new `nlp_apr17` Parameters table. If the answer pulls scalars from `lp_nlp_apr17/declarations.gms` for default-behavior claims, the 2b sweep was superficial.

### Q3 — Phase 2c sweep test (M11 §17.2 cost-aggregator)

**Archetype**: Cross-module Causal-chain (≥3 modules) + Quantitative
**Modules**: 57, 51, 11 (N MACCs → emission costs → cost objective)

> Trace how nitrogen-MACC costs from Module 57 enter MAgPIE's objective function. Name (a) the cost variable Module 57 produces, (b) any intermediary variable in Module 51 (nitrogen emissions) it flows through, and (c) the term in `q11_cost_reg` (Module 11 default realization) that incorporates it. Cite the producer-module attribution per cost variable.

**Phase 2c gate**: answer must correctly attribute every cost variable in the chain to its producing module (R3 §17.2 fix tested 32 terms / 27 source modules). MANDATE 9 + Pattern D coverage.

### Q4 — Fresh-fragile + Pattern D consumer attribution (M38 factor costs)

**Archetype**: Default-vs-Switch + Consumer attribution (probes Phase 1 1b validator's bug class)
**Modules**: 38, 70, 30 (factor costs → livestock cost consumer + cropland cost consumer)

> Module 38 (factor_costs) supplies per-unit production costs in the default `per_ton_fao_may22` realization. Name each cost variable Module 38 declares as an interface (`vm_cost_*`), identify the consuming module(s) for each, and quote (file:line) the consumer equation that reads it.

**Pattern-D gate**: answer must grep-verify every (cost variable, consumer module) pair. This is the exact class Phase 1 1b is now armed to catch — the audit should confirm 0 wrong attributions.

### Q5 — magpie4 R-to-GAMS provenance (organic routing test)

**Archetype**: R-to-GAMS provenance via magpie4
**Modules**: magpie4 helper + M55 (AWMS) or M53 (CH4) + M51 (N emissions)

> The IAMC variable `Emissions|N2O|Land|Agriculture|+|Animal Waste Management` appears in `report.mif`. Trace its origin: which magpie4 function produces it (cite the version-pinned path under `.cache/sources/magpie4/...`), which GAMS variable does that function read from the GDX, and which GAMS module/equation populates that variable?

**Routing gate**: answer must (a) cite `.cache/sources/magpie4/` paths (not the workspace clone), (b) load `agent/helpers/magpie4_reference.md` (not just route via core_docs), (c) trace through to the GAMS source. Tests the magpie4 scaffolding from Phase 0 in-context, not just via G3/G4 anchors.

### G1 — Regression (M14 default realization)

**Exact text** (from `validation_rounds.json.regression_questions[0].question`):

> What is the default realization of module 14 (yields)? List the equations defined in its equations.gms.

**Expected answer summary** (rubric ground truth): `managementcalib_aug19`; **exactly 2** equations (`q14_yield_crop`, `q14_yield_past`). `q14_yieldcalib` is NOT a defined equation. Verify line ranges against `modules/14_yields/managementcalib_aug19/equations.gms`.

### G2 — Regression (vm_carbon_stock propagation)

**Exact text** (from `validation_rounds.json.regression_questions[1].question`):

> Walk through how vm_carbon_stock is computed in Module 52 and where it enters the GHG-policy cost in Module 56. Cite the relevant equations and file:line locations.

**Expected answer summary** (rubric ground truth): `vm_carbon_stock` is **DECLARED in Module 56** (`price_aug22/declarations.gms:34`), NOT Module 52. Land modules (29, 31, 32, 34, 35) + M59 (SOM) populate it; Module 52 only **reads** it and `pcm_carbon_stock` to compute CO2 in `q52_emis_co2_actual` (`normal_dec17/equations.gms:16-19`). The pricing chain in M56: `q56_emis_pricing_co2` (`:19-22`) → `v56_emis_pricing` → `q56_emission_cost_oneoff` (`:45-52`) → `v56_emission_cost` → `q56_emission_costs` (`:56-58`) → `vm_emission_costs(i)`. Default `c56_carbon_stock_pricing = actualNoAcEst`. MANDATE 16 full-path citations.

## Success gates (per plan §Phase 3)

**A. Bomb rate**:
- Mean ≥8.0 (R24 was 7.5)
- 0 CRITICAL bugs (R4/R5 baseline)
- ≤~6 HIGH bugs total (R24 had 16)

**B. Phase 2 sweeps**:
- Q1: 0 HIGH bugs in M30 default behavior
- Q2: 0 HIGH bugs in M80 default behavior
- Q3: 0 HIGH bugs in M11 §17.2 cost-aggregator

**C. Phase 1 mechanizations**:
- Q4: Pattern D (1b) should catch any consumer-attribution drift before the auditor does — pre-launch baseline says 0 mismatches
- Q3: MANDATE 17 (one-hop reads) should prevent direct-vs-transitive attribution errors

**D. AGENT.md trim degradation watch**:
- G1, G2 scores should NOT drop materially from R22/R23 baselines (both scored well there)
- Q5 should organically route through `magpie4_reference.md` — if it doesn't, the auto-load trigger needs tightening

**E. Routing additions**:
- Q5 tests magpie4 routing in-context (G3/G4 tested it as anchor questions in R24)

## Outcomes — failure-mode response

| R25 mean | Action |
|---|---|
| <7.5 | Phase 0-2 regressed quality. Rollback assessment; do NOT proceed to R26 until root cause known. |
| 7.5-7.9 | No material recovery. Re-strategize before Phase 4. |
| 8.0-8.4 | Recovery achieved. Run R26 next session to confirm Phase 2 swept modules hold under repeat probing. |
| ≥8.5 | Recovery + improvement. Proceed to Phase 4 design. |

## Files

- Questions launched as 7 parallel Sonnet 4.6 magpie-helper agents (Step 2).
- Audits run as 7 parallel Opus 4.6 general-purpose agents (Step 3).
- Answers → `audit/round25_answers/{Q1-Q5,G1,G2}_answer.md`
- Audits → `audit/round25_audits/{Q1-Q5,G1,G2}_audit.md`
- Synthesis → `audit/round25_synthesis.md`
- JSON record → append to `audit/validation_rounds.json`
