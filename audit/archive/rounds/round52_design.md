# Round 52 design — broader carbon/emissions cluster (post-sync)

**Date**: 2026-06-28
**Type**: full (thematic: carbon/emissions)
**Code base**: 6304d830b (canonical develop)
**Trigger**: user-requested "broader carbon/emissions round" after the 2026-06-28 sync adopted commit 931db85c4 (59_som soil pcm_carbon_stock carry-forward). R50 (2026-06-07) validated the module_56 emissions cluster but PRE-dates this code change, so the soil carry-forward mechanism + the module_52/56/59 doc edits made this session are unvalidated.

**Composition**: 5 new probes + G2 regression anchor (carbon-stock propagation — thematically central and directly stress-tests this session's edits to module_52.md/56.md/59.md).

**Dedup**: module_52/56/vm_carbon_stock are calibration-exempt (G2). module_59 eligible_after R51 (eligible at R52). module_50/51 (R50), 58 (R51), 53/57 (R45 → R48) all eligible. pcm_carbon_stock / q52_emis_co2_actual / q59_nr_som not in ledger.

## Questions

**G2 (regression / causal chain — modules 52, 56, + populators 29/31/32/34/35/59)**
Walk through how `vm_carbon_stock` is computed in Module 52 and where it enters the GHG-policy cost in Module 56. Cite the relevant equations and file:line locations.

**P1 (timing/sequencing + causal chain — modules 59, 52, 56)** [NEW-change focus]
Soil CO2 emissions in MAgPIE are a between-timestep change in soil carbon stock. Trace the full timestep mechanics of the previous-timestep soil carbon stock `pcm_carbon_stock(...,"soilc",...)`: where it is initialized, in which module's postsolve it is carried forward each timestep, and how it enters the per-timestep flux in `q52_emis_co2_actual` and the CO2 pricing in Module 56. Explicitly contrast the soil pool's carry-forward with the above-ground pools' carry-forward (which module owns each). Cite file:line.

**P2 (default vs switch — modules 56, 52, 58)**
Under MAgPIE's default configuration, which CO2 emission sources are actually priced and which are excluded? Is soil/SOM carbon priced by default? Name the default `c56_emis_policy` value, cite where it is set, and explain how peatland (Module 58) CO2 is handled relative to vegetation/soil carbon (Module 52).

**P3 (quantitative — modules 59, 50, 51)**
Quantitatively, how does cropland change drive nitrogen release from soil organic matter in Module 59? State the equation, the C:N ratio assumed, and the timestep handling (divisors), then explain how that nitrogen connects to the soil nitrogen budget (Module 50) and to N2O emissions (Module 51). Cite the equation and coefficients.

**P4 (cross-module causal chain — modules 56, 32, 52)**
Trace the causal chain by which a CO2 price drives afforestation and how the sequestered carbon is valued: from Module 56 pricing terms, through the afforestation incentive/reward, into Module 32 forestry, into Module 52 carbon-stock accounting. Which variables/equations connect them? Under the default emission policy, is afforestation actually C-price-driven? Cite file:line.

**P5 (conservation law — modules 52, 59, land 29/31/35)**
How does MAgPIE partition total carbon stock across pools without double-counting between Module 52 (vegetation/litter carbon) and Module 59 (soil carbon)? Explain the `c_pools` set (vegc/litc/soilc), which module populates `vm_carbon_stock` for which pool, and how the pools aggregate. Cite the equations and file:line.

## Pipeline
ANSWER: 6 × Sonnet (magpie-helper, docs-only) → AUDIT: 6 × Opus (general-purpose, vs GAMS code + flywheel_rubric.md) → SYNTHESIZE → FIX (Sonnet) → record R52 in validation_rounds.json → append probe_dedup_ledger.
