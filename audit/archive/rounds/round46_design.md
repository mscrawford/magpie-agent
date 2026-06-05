# Round 46 — Least-verified-module flywheel (set B)

**Type**: full (5 new probes + 1 regression G2)
**Date**: 2026-06-05
**Motivation**: Second round of the user's two-round stabilization campaign. R45 (set A: thinnest 5 modules) came back raw 10.0 / doc_q 10.0. R46 targets the NEXT tier of least-verified modules, deliberately weighted to the **sub-9-scoring** ones and the **R16 Critical-anchor structural area**, using HARDER archetypes (timing/sequencing, conservation-law, edge-case) absent from R45 — a genuine stress test of whether the periphery is clean.

| Module | n_tests | last_round | last_score | why targeted |
|--------|--------:|-----------:|-----------:|--------------|
| 13 tech-change | 8 | R41 | **8** | weak score; vm_tau decision-vs-exo + conservation-tau |
| 22 land-conservation | 8 | R41 | **8** | weak score; hard-constraint-vs-cost + default policy |
| 28 age-class | 7 | R41/R44(periph) | 10 | R16 CRITICAL anchor area (ac set -> ac300, 62 elements truncation bug) |
| 18 residues | 7 | R42 | 10 | thin; ag/bg split, recycle/burn/remove/bioen routing |
| 12 interest-rate | 6 | R43 | 10 | thin; pm_interest endogeneity + discounting (probe the VARIABLE, eligible per ledger; not module recognition) |

Dedup: 13, 22 last focus-probed R41 (retired-in). 28 R41. 18 R42 (retired-in at R46). pm_interest retire_after=22 (eligible). Probes ask the answerer to RETRIEVE names (capability), not recognize handed-over ones.

## Probes

### R46-P1 — Land-use intensity (tau) / technological change (module 13) [quantitative + timing]
Modules: 13, 14, 38, 11
> In MAgPIE, how is agricultural land-use intensity (the tau factor) determined? (a) Is tau a decision variable the optimizer chooses, or exogenously fixed? (b) What does raising tau COST, and which equation/variable carries that cost into the objective (via factor costs in 38 / costs in 11)? (c) How does tau connect to yields in module 14, and what is "conservation tau" (the f_btc2 feature) — does it differ from the standard tau pathway? Name the variable(s) and equation(s) and cite file:line.

### R46-P2 — Land conservation enforcement (module 22) [conservation-law + default/switch]
Modules: 22, 35, 10, 29
> How does MAgPIE enforce land conservation / protected areas (module 22)? (a) Is protection a hard constraint on the land variables or a cost penalty? (b) Which land pools are protected and how does it constrain natural vegetation (35) and cropland (29) via the land balance (10)? (c) Under the DEFAULT configuration, what is actually protected (which data / policy), and is any biodiversity/conservation switch off by default? Name the constraining variable(s)/equation(s) and cite file:line.

### R46-P3 — Age-class dynamics (module 28) [timing/sequencing — R16 Critical anchor]
Modules: 28, 35, 32, 52
> Explain how age classes work in MAgPIE (module 28). (a) What set indexes age classes, and how many elements does it have / what is the maximum age class? (b) How does land move between age classes over time (the aging/shifting mechanism), and is this per-timestep? (c) How do forestry (32), natural vegetation (35) and carbon (52) use age classes? Give the exact set name and its full extent, and cite file:line. [Do NOT truncate the age-class set — state its actual maximum element.]

### R46-P4 — Crop residues (module 18) [causal chain + quantitative]
Modules: 18, 17, 53, 60
> Trace agricultural crop residues in MAgPIE (module 18). (a) How are above-ground and below-ground residue quantities computed from production (17)? (b) How is the above-ground residue pool split among its competing uses (recycling to soil, burning, removal/field-balance, bioenergy in 60)? (c) Which residue flows drive downstream emissions (e.g. residue-burn CH4 in 53)? Name the key residue variable(s)/equation(s) and cite file:line.

### R46-P5 — Interest rate & discounting (module 12) [default + edge-case]
Modules: 12, 11, 13, 38
> How does the interest rate enter MAgPIE (module 12)? (a) Is the interest rate endogenous or an exogenous regional time series, and what is its default source? (b) Where is it USED — how does it discount or annuitize investment costs (e.g. technological-change investment in 13, factor/capital costs in 38) into the regional cost objective (11)? (c) Is the interest rate uniform globally or differentiated by region, and does it change over time? Name the interface parameter and the consuming equation(s) and cite file:line.

### R46-G2 (regression, carbon-stock propagation) [calibration anchor — exempt]
> Walk through how `vm_carbon_stock` is computed in Module 52 and where it enters the GHG-policy cost in Module 56. Cite the relevant equations and file:line locations.

Rotation: G2 last used R43 (G3 used R45, G4 R44, G1 R42/R43). G2 is the historically-fragile cross-module anchor (regressed R22->R26), carbon-adjacent to the R46 theme — strongest regression signal here. Auditor must confirm: vm_carbon_stock DECLARED in M56 (price_aug22/declarations.gms), POPULATED by land modules 29/31/32/34/35 + 59 SOM, READ by M52 q52_emis_co2_actual (producer-vs-consumer distinction).

## Method
- Answer: 5 parallel Sonnet (magpie-helper), docs-only, no raw GAMS. G2 same.
- Audit: 5+1 parallel Opus (general-purpose), verify every claim + load-bearing doc claims vs GAMS source; rubric = audit/flywheel_rubric.md; record doc_errors_latent[].
- P3 age-class: the auditor MUST independently grep the ac set definition and confirm the answer did NOT truncate it (R16 Critical anchor: ac140/acx truncation when actual extends to ac300).
- Parameterization lens (P1/P2/P5): apply the three-check — flag any "models X" claim that is actually parameterized (tau cost calibration, interest-rate source, protection data).
