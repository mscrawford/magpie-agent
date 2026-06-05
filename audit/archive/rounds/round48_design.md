# Round 48 — cross_module conservation docs + 2 core_docs (post-R47 stale set)

**Type**: full (6 probes + 1 regression G4)
**Date**: 2026-06-05
**magpie-agent commit_before**: 6d87471
**magpie code citation base**: ee98739fd (develop, == origin/develop, 0/0)
**Answerer**: claude-sonnet-4-6 (Agent model:sonnet, magpie-helper), docs-only (no raw GAMS)
**Auditor**: claude-opus-4-8 (Agent model:opus, general-purpose), verify vs GAMS @ee98739fd, rubric=audit/flywheel_rubric.md

**Motivation**: R47 (capstone, same day) re-validated the 3 *worst-scoring* cross_module docs (modification_safety 3->10, circular_dependency 5->10, nitrogen_food 7->10) plus core_docs Core_Architecture (0->10) and Module_Dependencies (5->7). It deliberately left the 3 conservation docs that scored well at R30 (carbon 7, land 10, water 10) and the Data_Flow core doc (R30 score 7). Those are the docs "not tested in a long time": last direct test R30 (2026-05-29, doc-centric audit), last *question-based* round R7 (2026-03-07). User scope: the 3 conservation docs + Data_Flow + Module_Dependencies (fresh angle) + a 2nd carbon deep-dive = 6 probes.

| Doc | last direct test | last score | this round |
|-----|-----------------:|-----------:|------------|
| cross_module/carbon_balance_conservation | R30 2026-05-29 | 7 | P1 (conservation) + P2 (deep dive) |
| cross_module/land_balance_conservation | R30 2026-05-29 | 10 | P3 |
| cross_module/water_balance_conservation | R30 2026-05-29 | 10 | P4 |
| core_docs/Data_Flow | R30 2026-05-29 | 7 | P5 |
| core_docs/Module_Dependencies | R47 2026-06-05 (P4, vm_land angle) | 7 | P6 (fresh angle: trade<->prod<->demand) |

**Regression rotation**: G1 R47, G2 R46, G3 R45, G4 R44 -> G4 is the oldest/due anchor; also satisfies "magpie4 every 2-3 rounds" (magpie4 last tested R45). Same rotation discipline R47 used.

**Probe-dedup**: balance variables (vm_land, vm_carbon_stock, vm_water_available/demand, q10_land_area, q43_water) are calibration-exempt or past lock-out (retire_after 24/26 << R48). No recognition-probe risk.

## Probes (answerer reads magpie-agent docs ONLY: cross_module/ + core_docs/ + module docs; NO raw GAMS)

### R48-P1 — Carbon conservation across land-use transitions (carbon_balance_conservation) [conservation-law]
docs_tested: cross_module/carbon_balance_conservation.md ; modules 52,35,32,59
> In MAgPIE, when land is converted between uses (e.g. forest -> cropland), how is the change in carbon stock computed and accounted for so carbon is conserved (i.e. a stock loss becomes a CO2 emission, not vanishing)? Trace the conservation accounting: which equation(s) compute the stock change, where does the released carbon go, and which carbon pools are tracked? Name the variables/equations and cite file:line.

### R48-P2 — vm_carbon_stock structure deep dive (carbon_balance_conservation) [quantitative/structural]
docs_tested: cross_module/carbon_balance_conservation.md ; modules 52,59,58
> Be precise about `vm_carbon_stock`: what are its exact dimensions/index domain, which carbon pools does it span (e.g. vegc/litc/soilc), and which land types carry it? How is a stock computed from carbon density and area, and which module DECLARES vm_carbon_stock vs which POPULATE it? (R7 found fabricated trade vars + wrong vm_carbon_stock dimensions in this doc — verify the current doc is right.) Cite file:line.

### R48-P3 — Land balance / double-counting (land_balance_conservation) [conservation-law]
docs_tested: cross_module/land_balance_conservation.md ; modules 10,29,30,31,32,35
> How does MAgPIE's land balance guarantee that the sum of all land-use types equals total available land at every cell, with no double-counting and no creation/destruction of area? Which equation enforces this (q10_land_area or similar), how is it structured (set-based sum over land types), and how are land-use TRANSITIONS constrained so area is conserved across timesteps? Name the variables/equations and cite file:line.

### R48-P4 — Water supply=demand + infeasibility (water_balance_conservation) [conservation + edge-case]
docs_tested: cross_module/water_balance_conservation.md ; modules 42,43,41
> How does MAgPIE enforce the water balance (sectoral water demand <= available water) by default? Which equation(s) balance supply and demand, what are the demand sectors, how are environmental flow requirements handled, and what configuration/conditions make the water module INFEASIBLE? Be explicit about the default realization. Name variables/equations and cite file:line.

### R48-P5 — Input-data provenance trace (Data_Flow) [provenance]
docs_tested: core_docs/Data_Flow.md ; (input pipeline + first-consumer module)
> Per the Data_Flow documentation, trace how a key input data set enters MAgPIE: pick the land-use initialisation (or yield) input and follow it from the input file format (.cs2/.cs3/.mz) through the GAMS reading mechanism into the set/parameter the model uses, and name the first module/phase that consumes it. What file types and parameter names are involved, and what is the data source? Cite the doc + file:line.

### R48-P6 — Trade<->production<->demand dependency edge (Module_Dependencies) [dependency structure; fresh angle vs R47-P4]
docs_tested: core_docs/Module_Dependencies.md ; modules 21,17,16,15
> Using the Module_Dependencies documentation, describe the dependency relationships among the trade module (21), production (17), and food/material demand (15/16): which interface variables does trade consume and which does it produce, which modules sit on each side of those edges, and is the doc's stated dependency set accurate and complete vs the actual module interfaces? Cite file:line.

### R48-G4 (regression, magpie4 getReport dispatch) [calibration anchor — exempt]
docs_tested: agent/helpers/magpie4_reference.md + .cache/sources/magpie4/R/getReport.R
> How does `magpie4::getReport` organize its reporting? Describe the dispatch pattern, how many unique `report*` functions it calls, and cite the file:line range from the pinned clone. (Auditor: verify against the version_pins.json-pinned SHA, NOT the workspace clone.)

## Method
- Answer: 7 parallel Sonnet (magpie-helper), docs-only. Each writes round48_answers/{id}_answer.md.
- Audit: 7 parallel Opus (general-purpose), verify doc claims vs GAMS @ee98739fd; rubric = audit/flywheel_rubric.md; record latent doc bugs (doc_error_answerer_beat_it) per rubric 1.5. Each writes round48_audits/{id}_audit.md.
- Synthesize -> fix doc errors (Sonnet) regardless of score (Step 5 doc-error rule) -> validate_consistency.sh -> record R48 in validation_rounds.json -> probe_dedup_check.py --append-latest.
