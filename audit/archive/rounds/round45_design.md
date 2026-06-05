# Round 45 — Least-verified-module flywheel (set A)

**Type**: full (5 new probes + 1 regression G3)
**Date**: 2026-06-05
**Motivation**: User goal — confirm answer-quality is stabilizing in a good place, targeting the *least-verified* modules. Coverage analysis (latest-score-per-module via `modules_tested` aggregation over R1–R44) isolated the thinnest / weakest-scoring corners that the broad R41–R43 sweeps and the R44 diagnostic did NOT re-confirm:

| Module | n_tests | last_round | last_score | why targeted |
|--------|--------:|-----------:|-----------:|--------------|
| 57 MACC | 6 | R41 | **7** | weakest recent score among low-coverage; abatement parameterization risk |
| 53 methane | 8 | R41 | **7** | weak score; emission-factor parameterization risk |
| 62 material | 4 | R42 | 10 | THINNEST coverage in the model |
| 45 climate | 5 | R42 | 10 | thin + classic "uses data ≠ models" parameterization trap |
| 55 awms | 6 | R42 | 10 | thin; manure N/CH4 split parameterization |

Quality context: R41 8.43 → R42 9.29 → R43 9.57 (doc_q 10.0, 0 doc bugs) → R44 9.28 (doc_q 10.0, 0 doc bugs). Docs are clean in the swept core; this round probes whether the under-swept periphery is equally clean.

## Probes

### R45-P1 — MACC abatement mechanism (module 57) [parameterization + default/switch]
Modules: 57, 56, 51, 53
> In MAgPIE, explain how the MACC module (57) achieves greenhouse-gas abatement. Specifically: (a) Are the marginal abatement cost curves computed mechanistically inside MAgPIE, or applied from exogenous input data? (b) Which emission sources do they act on, and how does the abatement connect to the GHG-pricing module (56)? (c) Is any abatement active by default, or only under a non-default switch? Name the relevant interface variables, equations, and scenario switches, and cite file:line.

### R45-P2 — Material demand chain (module 62) [causal chain + default/switch]
Modules: 62, 16, 20, 17
> Trace how demand for the material use of agricultural products (module 62) is determined and satisfied in MAgPIE. (a) Is material demand endogenous to the optimization or exogenously prescribed? (b) How does it enter the supply-demand balance (module 16 / 17), and what is module 20's (processing) role for material commodities? (c) What is the default behavior? Name the demand variable(s), the equation that adds material demand to total demand, and cite file:line.

### R45-P3 — Climate module provenance (module 45) [parameterization / provenance trap]
Modules: 45, 14, 52, 58
> What does module 45 (climate) actually do in MAgPIE? (a) Does MAgPIE simulate climate dynamics, or does module 45 distribute exogenous climate-input data (e.g., climate-zone classifications) to other modules? (b) Which downstream modules consume module 45's outputs, and for what (yields in 14? carbon densities in 52? peatland in 58?)? (c) Name the specific interface parameter(s) module 45 provides and cite file:line. Be explicit about what is parameterized vs mechanistically modelled.

### R45-P4 — Animal-waste nitrogen pathway (module 55) [causal chain + parameterization]
Modules: 55, 50, 51, 70
> Trace nitrogen flows originating from livestock manure in MAgPIE. (a) How does the animal-waste-management module (55) allocate manure between confinement and grazing systems, and is this split mechanistic or applied from IPCC/input parameters? (b) How do the resulting nitrogen flows enter the soil-nitrogen budget (module 50) and nitrogen emissions (module 51)? (c) What activity drives manure production (livestock from module 70)? Name the key awms→50 and awms→51 interface variables and cite file:line.

### R45-P5 — Methane sources & accounting (module 53) [quantitative + conservation]
Modules: 53, 70, 55, 56
> Trace methane (CH4) emissions in MAgPIE. (a) What distinct CH4 sources does module 53 account for (e.g. enteric fermentation, manure management, rice)? (b) For each source, is the emission factor mechanistic or applied from input data, and what activity variable drives it (livestock numbers from module 70? rice area? manure from module 55?)? (c) How do these CH4 emissions reach the GHG-pricing in module 56? Name the emission variables / equations and cite file:line.

### R45-G3 (regression, magpie4 source-of-truth) [calibration anchor — exempt]
> Which version of magpie4 does this agent's source-of-truth clone reflect, and how was that version determined? Cite the file(s) you read.

Rotation: G3 last used R42 (G1/G2 used R43, G4 used R44) — G3 is the due magpie4 anchor.

## Method
- Answer: 5 parallel Sonnet (magpie-helper), docs-only, no raw GAMS.
- Audit: 5 parallel Opus (general-purpose), verify every claim + load-bearing doc claims against GAMS source; rubric = `audit/flywheel_rubric.md`; record `doc_errors_latent[]`.
- G3 auditor reads `project/version_pins.json` directly for ground truth.
- Parameterization lens (P1/P3/P4/P5): apply the three-check (equation structure / parameter source / dynamic feedback) — flag any "models X" claim that is actually parameterized.
