# Round 47 — Capstone: cross_module/ + core_docs/ re-validation

**Type**: full (5 probes + 1 regression G1)
**Date**: 2026-06-05
**Motivation**: User flagged that the "least-verified" framing (and the quality-map viz) were module-keyed, leaving cross_module/ + fact-bearing core_docs/ a blind spot. The new non-module doc-quality map (fig 9) confirmed it: the entire non-module corpus is STALE (last tested R30) and several docs carried bad last-scores — **Core_Architecture 0.0, modification_safety_guide 3.0, circular_dependency_resolution 5.0, Module_Dependencies 5.0** (all R30, all *pre-fix* — R30 applied 51 edits but never re-confirmed clean). This capstone re-validates the worst non-module docs and confirms the R30 Critical fixes hold (R13-style), then the campaign goes reactive.

| Doc | R30 score (pre-fix) | this round |
|-----|--------------------:|------------|
| core_docs/Core_Architecture | **0.0** | P1 (re-confirm s15_elastic_demand loop-once fix) |
| cross_module/modification_safety_guide | **3.0** | P2 (re-confirm centrality/risk claims) |
| cross_module/circular_dependency_resolution | 5.0 (4.0@R8) | P3 (persistently weak — resolution mechanisms) |
| core_docs/Module_Dependencies | 5.0 | P4 (re-confirm M10 phantom-consumer fix) |
| cross_module/nitrogen_food_balance | 7.0 (4.0@R7) | P5 (balance + supply=demand) |

## Probes (each verifies the DOC's claims against GAMS; answerer may read cross_module/+core_docs/, not raw GAMS)

### R47-P1 — Optimization-loop iteration (core_docs/Core_Architecture) [edge-case + timing]
docs_tested: core_docs/Core_Architecture.md ; modules 15,16,80,09
> By default, how many times does MAgPIE's nonlinear optimization loop run per time step? Walk through the demand<->supply iteration. Does `s15_elastic_demand` change this, and what is its default? Be precise about whether the loop iterates "2-5 times" or runs once. Cite the switch default and the loop control.

### R47-P2 — Modification safety / centrality (cross_module/modification_safety_guide) [conservation + safety]
docs_tested: cross_module/modification_safety_guide.md ; modules 10,11,56,52
> Which MAgPIE modules are the highest-centrality / most dangerous to modify, and why? Concretely: what breaks downstream if you change the land balance (`vm_land` / `q10_land_area`) or the cost aggregation (module 11)? Name the specific interface variables and the modules that would be affected. Is the safety guide's risk ranking accurate vs the actual dependency structure?

### R47-P3 — Circular-dependency resolution (cross_module/circular_dependency_resolution) [timing/sequencing]
docs_tested: cross_module/circular_dependency_resolution.md ; modules 13,14,52,56
> MAgPIE has circular dependencies between modules. Take (a) the tau<->yield coupling (13<->14) and (b) the carbon-stock / GHG-pricing loop (52<->56). For each: is it a genuine circular dependency, and exactly how is it resolved (lagged previous-timestep value? presolve ordering? a `pc`/`pcm` parameter)? Name the variable/parameter that breaks each cycle and cite file:line.

### R47-P4 — vm_land provider/consumer set (core_docs/Module_Dependencies + module_10) [provenance — R20 anchor class]
docs_tested: core_docs/Module_Dependencies.md ; modules 10,29,30,31,32,34,35,14,71,80
> Which modules CONSUME `vm_land`, and which PROVIDE to it (set its bounds / initial value)? Specifically: is module 14 (yields) a `vm_land` consumer? Is module 80 (optimization)? Be exact — list the real consumer/provider set and flag any module that does NOT touch `vm_land` directly (e.g. reads `pm_land_start`/`pcm_land` instead). Cite file:line.

### R47-P5 — Nitrogen + food balance (cross_module/nitrogen_food_balance) [conservation-law]
docs_tested: cross_module/nitrogen_food_balance.md ; modules 50,51,15,16,18
> How does MAgPIE enforce (a) the soil-nitrogen balance and (b) food supply = demand? Trace the conservation accounting: what equation guarantees food supply meets demand, and how do nitrogen inputs/outputs balance in module 50? Name the balancing equations and cite file:line.

### R47-G1 (regression, module 14 default realization) [calibration anchor — exempt]
docs_tested: modules/module_14.md
> What is the default realization of module 14 (yields)? List the equations defined in its equations.gms.

Rotation: G1 last used R43 (G2 R46, G3 R45, G4 R44) — G1 is the due anchor.

## Method
- Answer: 6 parallel Sonnet (magpie-helper), docs-only (cross_module/ + core_docs/ + module docs allowed; NO raw GAMS).
- Audit: 6 parallel Opus (general-purpose), verify the doc's claims against GAMS source; rubric = audit/flywheel_rubric.md.
- P1: confirm the R30 score-0 fix (loop-once) holds. P4: confirm the R30 phantom-consumer fix (14/71/80 NOT vm_land consumers) holds — R20-anchor class (wrong consumer set = Critical).
- Record per-question `docs_tested` with the cross_module/core_docs paths so fig 9 updates with post-fix scores.
- This is the LAST standing-campaign round; afterwards semantic validation is reactive (drift-triggered).
