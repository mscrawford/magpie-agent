# R23 — Semantic Validation Round Design

**Date**: 2026-05-24
**Validator state at start**: 37/40 passed, 3 advisories (s38/s59 param defaults + I2 doc-convention)
**MAgPIE state**: develop @ d80549377 (7 commits since last sync 3836bbaa9; all Docker/codecheck, no GAMS impact)
**Schema**: v1.1 (regression questions G1/G2 required alongside 5 new probes)
**Scope bias**: Phase 2 migration-touched docs — cross_module/ (12 conservation/safety docs with 128 citation rewrites), agent/helpers/ (5 migrated; scenario_diet_change.md alone had 29 conversions), AGENT.md format examples
**Models**: Answerer = claude-sonnet-4-6, Auditor = claude-opus-4-7
**Coverage check**: All probe modules eligible per `audit/probe_dedup_ledger.json` (no name with retirement_eligible_after >= 23 used as the primary subject of any probe)

---

## R23-Q1 — Diet-shift → Nitrogen-cycle propagation

**Archetype**: cross-module causal chain
**Modules probed**: 15, 16, 17, 50, 51 (M70 named only as one downstream consumer)
**Migration coverage**: `agent/helpers/scenario_diet_change.md` (29 cite conversions), `cross_module/nitrogen_food_balance.md`

**Question**:
A user enables `s15_exo_diet=3` (the recommended EAT-Lancet bounds mode) with default `c15_EAT_scen` and `s15_exo_ruminant=1`. Trace the propagation of the resulting food-demand reduction for ruminant products through to the soil nitrogen budget. Specifically:
(a) What M15 mechanism enforces the bounds in diet=3 mode (per the helper)?
(b) What M15→M16 interface variable carries food demand, with what dimensions?
(c) Which M16 equation aggregates this into `vm_supply` for ruminant products, and where does it sit (file:line)?
(d) What M17 variable carries regional production to M50, and how is it produced?
(e) What is the form of the q50_nr_bal_crp equation in the default realization (`macceff_aug22`)? Cite the form and file:line.
(f) Name one downstream M51 equation that consumes the M50 inputs/balance.

**Expected answer summary** (auditor reference):
- (a) `f15_rec_EATLancet(t,i,kfo)` min/max bounds enforced by `q15_food_demand` in `anthro_iso_jun22` (helper line 33 notes "diet=3 → composition determined by `f15_rec_EATLancet` min/max bounds and `c15_EAT_scen` is ignored")
- (b) `vm_dem_food(i,kall)` (mio. tDM per yr) — declared `modules/15_food/anthro_iso_jun22/declarations.gms:14`
- (c) `q16_supply_livestock(i2,kap)` (kap covers ruminants + monogastrics) at `modules/16_demand/sector_may15/equations.gms:32-38`
- (d) `vm_prod_reg(i,kall)` aggregated from `vm_prod(j,k)` in M17; reaches M50 directly
- (e) q50_nr_bal_crp form: `vm_nr_inputs(i2) =e= sum(...)` reading `vm_prod_reg(i2,kcr) * fm_attributes("nr",kcr)` — cite `modules/50_nr_soil_budget/macceff_aug22/equations.gms:18-30` (per migrated nitrogen_food_balance.md line 38)
- (f) M51 q51_emissions / q51_emis_dynamic consumes M50 outputs (vm_nr_eff_n_soils etc.)

---

## R23-Q2 — Water-availability infeasibility diagnosis

**Archetype**: edge case / failure mode (cross-module)
**Modules probed**: 43 primary; 42 named only as the water-demand LHS source (no fresh M42 probe)
**Migration coverage**: `agent/helpers/debugging_infeasibility.md`, `agent/helpers/water_scarcity_scenarios.md`, `cross_module/water_balance_conservation.md`

**Question**:
A user runs MAgPIE with a counterfactual `lpj_runoff_minus30pct` water-availability input. The model returns `modelstat=4` at the 2030 timestep. Walk through the diagnostic logic combining `agent/helpers/debugging_infeasibility.md` AND `agent/helpers/water_scarcity_scenarios.md`:
(a) Which equation hard-constrains the water balance, in which module, and in which default realization? Cite the equation form (LHS, =l=/=e=/=g=, RHS) and file:line.
(b) Does that equation include a slack/buffer term, or is it strict?
(c) Per the helper, what are the top 3 diagnostic steps when modelstat=4 first appears?
(d) Per `water_scarcity_scenarios.md`, which CFG switch controls Environmental Flow Protection (EFP) and what is its default value?
(e) Briefly: what is the relationship among `vm_watdem`, `v43_watavail`, and the `wat_src` set?

**Expected answer summary**:
- (a) `q43_water(j2)` in `modules/43_water_availability/total_water_aug13/equations.gms:10-11`: `sum(wat_dem, vm_watdem(wat_dem,j2)) =l= sum(wat_src, v43_watavail(wat_src,j2))`. Default realization is `total_water_aug13` (single realization).
- (b) No slack term in q43_water — strict inequality. (The buffer is implicit in the availability term, not an additive slack.)
- (c) Per debugging_infeasibility.md: check `full.lst` for INFES rows / examine `fulldata.gdx` marginals / bisect timesteps. Exact wording from helper.
- (d) Per water_scarcity_scenarios.md: the EFP switch and default value (need helper read to verify exact name/default).
- (e) `vm_watdem(wat_dem,j2)` is sectoral demand by wat_dem set member (agriculture, manufacturing, etc.); `v43_watavail(wat_src,j2)` is availability by source (rainfed/irrig/groundwater types in wat_src); the equation sums both sides.

---

## R23-Q3 — Modification safety: extending M44 (biodiversity)

**Archetype**: modification impact + cross-module dependency
**Modules probed**: 44 (primary); incidental references to M10 / M30 / M11 are not the test target
**Migration coverage**: `cross_module/modification_safety_guide.md`, `cross_module/circular_dependency_resolution.md`
**Dedup note**: `vm_land` (off-limits per ledger as MANDATE-10 worked example) appears as one expected answer for Q3(b) because it is the canonical land-state variable any cropland-related modification would touch — naming it is not testing recognition of the MANDATE-10 example, it is the obvious answer to a modification-safety question. Classified per `audit/probe_dedup_check.py` option (b): the recognition signal being tested is whether the agent retrieves the right cross-module interface, not whether it can recall the variable name from rule text.

**Question**:
A developer wants to modify M44 (biodiversity) to add a "critical-habitat protection" constraint that further restricts cropland expansion in BII-loss-prone cells.
(a) Per `cross_module/modification_safety_guide.md`, what risk tier is M44 (its centrality category)?
(b) Which interface variables in M44 would a new constraint most likely need to interact with on the demand side? Name them and where they're declared.
(c) Per `cross_module/circular_dependency_resolution.md`, is M44 involved in any documented circular dependency? If yes, with which module(s) and how is the cycle resolved?
(d) What is the name of the M44 equation that computes the biodiversity-value-loss cost variable, and what's the variable's name + dimensions?
(e) Which module consumes that cost variable, and via which equation does it enter the objective?

**Expected answer summary**:
- (a) Risk tier per modification_safety_guide.md (verify by reading the doc's M44 entry — typically LOW or MEDIUM compared to M10/M11/M30/M70).
- (b) Likely `vm_bv(j,landcover44,potnatveg)` (M44 producer) and/or `vm_land(j,land)` reference (cross-module read from M10).
- (c) Need verification — likely no cycle (M44 reads land state and produces cost; one-way).
- (d) `q44_cost` produces `vm_cost_bv_loss(j)`. Per R6-Q5 note, q44_cost's LHS is `sum(cell(i2,j2), vm_cost_bv_loss(j2))`.
- (e) M11 consumes `vm_cost_bv_loss` via `q11_cost_reg`; reaches objective via `q11_cost_glo` → `vm_cost_glo` → M80.

---

## R23-Q4 — Interpreting MAgPIE outputs (report.mif tracing)

**Archetype**: timing/sequencing + quantitative interpretation
**Modules probed**: cross-cutting output pipeline (no module is the primary subject — tests the helper)
**Migration coverage**: `agent/helpers/interpreting_outputs.md`

**Question**:
A user has a MAgPIE run in `output/SSP2-base/`. They want to compare total food-related N₂O emissions across regions to a baseline. Per `agent/helpers/interpreting_outputs.md`:
(a) Which two output files contain (i) IAMC-formatted reporting variables and (ii) the full GAMS state including variable marginals? Give exact filenames.
(b) Where in the source code is the GDX dump triggered (cite file:line)?
(c) What R function produces `report.mif`, what is the path of the producing script, and what variable-naming convention does it enforce?
(d) Why does `fulldata.gdx` retain only the final-timestep state for raw `vm_*` variables, but multiple timesteps for `ov_*`/`oq_*`?
(e) When a user needs per-cell (`j`, ~200 cells) emissions detail rather than per-region (`i`, 12 regions), which output script disaggregates to 0.5° grid?

**Expected answer summary**:
- (a) (i) `report.mif`; (ii) `fulldata.gdx`. Both in `output/<run>/`.
- (b) `core/calculations.gms:92` — `Execute_Unload "fulldata.gdx"` inside time loop.
- (c) `magpie4::getReport(gdx)` called from `scripts/output/rds_report.R`; enforces `"Name (unit)"` format (space before paren); validated at `scripts/output/rds_report.R:40-45`.
- (d) Per helper line ~60 / line ~170: `fulldata.gdx` is rewritten each timestep (overwrite); `ov_*`/`oq_*` parameters have an explicit `t` dimension and accumulate across calls.
- (e) `scripts/output/extra/disaggregation.R` produces `cell.land_0.5.mz`.

---

## R23-Q5 — AGENT.md format compliance (post-migration examples)

**Archetype**: format / convention adherence
**Modules probed**: 17 (used as a concrete subject; not in ledger off-limits)
**Migration coverage**: AGENT.md format-example updates (the migration updated `🟢` example to use the full-path form `modules/XX_.../equations.gms:123`)

**Question**:
Per AGENT.md Step 2 "Cite Your Sources" (around line 356) and the Epistemic Hierarchy section (around line 583):
(a) Quote VERBATIM the four "closing source statement" format strings AGENT.md lists (the 🟡, 🟢, 💬, 📘 lines).
(b) Quote the 🟢 line from the Epistemic Hierarchy section that defines "Verified".
(c) For each of the four closing strings in (a), write one one-sentence worked example using Module 17 (production) as the subject.
(d) Post-migration, the 🟢 example uses a citation of the form `modules/XX_.../equations.gms:123`. Why is this form (rather than bare `equations.gms:123`) now required across non-module docs? Which validator enforces it?
(e) Per AGENT.md Step 2c "When to Say 'I Don't Know'", give the exact 4-bullet "format" the agent should use when uncertain.

**Expected answer summary**:
- (a) Verbatim from AGENT.md:363-366:
  - `- 🟡 "Based on module_XX.md documentation"`
  - `- 🟢 "Verified against module_XX.md and modules/XX_.../equations.gms:123"`
  - `- 💬 "Includes user feedback from module_XX_notes.md"`
  - `- 📘 "Consulted Query_Patterns_Reference.md"`
- (b) `🟢 Verified: Read actual code THIS session ('modules/NN_xxx/realization/file.gms:123')` from AGENT.md:586.
- (c) Each worked example uses Module 17 substituted into the format (the agent should NOT invent extra prose).
- (d) Full-path form distinguishes citations across cross-module / reference docs where multiple modules use same basenames; enforced by `scripts/check_no_bare_cites.py` (Check 25, added in this session's bare-cite migration).
- (e) AGENT.md Step 2c "Format" block: "I can tell you [what I DO know from docs/code], but I can't determine [specific thing] because [reason]. To verify, you could [specific suggestion]." (the agent should quote this exactly).

---

## R23-G1 — Module 14 default realization + equation list (calibration anchor)

(Verbatim from `audit/validation_rounds.json.regression_questions.G1`.)

**Question**: What is the default realization of module 14 (yields)? List the equations defined in its equations.gms.

**Expected answer**: Per G1 corrected in R22 — default `managementcalib_aug19` (verify via `cfg$gms$yields` in config/default.cfg); equations.gms defines exactly 2 equations: `q14_yield_crop` and `q14_yield_past`. Verify exact line ranges. (R22 corrected the anchor — earlier text claimed a spurious `q14_yieldcalib`.)

---

## R23-G2 — vm_carbon_stock propagation through M52 + M56 (calibration anchor)

(Verbatim from `audit/validation_rounds.json.regression_questions.G2`.)

**Question**: Walk through how `vm_carbon_stock` is computed in Module 52 and where it enters the GHG-policy cost in Module 56. Cite the relevant equations and file:line locations.

**Expected answer**: Per G2 corrected in R22 — `vm_carbon_stock` is DECLARED in M56 (`price_aug22/declarations.gms:34`), NOT in M52. Land modules (29, 31, 32, 34, 35) + M59 (soilc pool) POPULATE the variable. M52 only READS it for `q52_emis_co2_actual` (`normal_dec17/equations.gms:16-19`). M56 chain: `q56_emis_pricing_co2` → `v56_emis_pricing` → `q56_emission_cost_oneoff` → `v56_emission_cost` → `q56_emission_costs` → `vm_emission_costs(i)`. Default `%c56_carbon_stock_pricing%` is `actualNoAcEst`. Full-path citations required per MANDATE 16.

---

## Round budget

- 7 parallel Sonnet answerers (~3-5 min each, but truly parallel → ~5 min wall)
- 7 parallel Opus auditors (~5-8 min each → ~10 min wall)
- Synthesis + fix + record: ~30 min
- Total expected wall-clock: ~50 min
