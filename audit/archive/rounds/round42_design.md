# Round 42 — Design (follows R41)

**Date**: 2026-06-03
**Type**: full (classic question-based flywheel)
**Theme**: Follow-on to R41. Three design drivers: (1) **dedup** — R41 locked its 18 probed modules to retire_after=44, so R42 centers on *different* modules; (2) **deepen the fragile area** — R41's only doc-quality weak spot was M56 emissions (the emis-policy table had a Major bug; line 662 `redd+natveg_nosoil` is a suspected sibling defect), so R42-Q1 probes the pricing chain + the policy matrix structure to catch it; (3) **fill archetype gaps** — R41 used causal-chain/default-switch/timing/conservation; R42 adds quantitative, edge-case/failure-mode, R-to-GAMS provenance, and parameterization-vs-mechanism.

**Answerer model**: claude-sonnet-4-6 (Agent `model:sonnet`, `magpie-helper`), docs-only (+config/default.cfg)
**Auditor model**: claude-opus-4-8 (Agent `model:opus`, `general-purpose`), live GAMS + rubric

**Regression anchors this round**: G1 + G3 (rotated from R41's G2/G4). G1 = module 14 default realization (stability); G3 = magpie4 version-pin discipline (under-exercised: only R24, R28).

**Dedup**: R42 fresh probes avoid the R41-locked set {09,10,13,15,16,17,21,22,28,29,30,31,32,35,51,53,57,70} as PRIMARY targets. All R42 primary targets (45,50,59,18,43,42,44,60,62,11 + exempt 14,52,56) have retire_after ≤ 35 < 42 → re-probable.

---

## New probes (5)

### R42-Q1 — GHG emission-pricing chain + policy matrix (quantitative/chain) [FOLLOW-ON of R41-Q4]
**Modules**: 56, 52, 11
**Question**:
> Once a nonzero CO2 price is active in MAgPIE, trace exactly how a tonne of land-use-change CO2 becomes a cost in the global objective. (a) How does the `f56_emis_policy` matrix select which (pollutant, source) pairs are priced — name the parameter and how it gates pricing; (b) the pricing chain from carbon-stock change to `vm_emission_costs`; (c) where `vm_emission_costs` enters the Module 11 objective. Cite equations + file:line. Finally: which non-default `c56_emis_policy` scenarios additionally price agricultural CH4/N2O, and does `redd+natveg_nosoil` price them?

**Why**: directly follows R41-Q4 (which found `module_56.md`'s emis-policy table wrongly marking CH4/N2O unpriced under the default policy). The closing sub-question forces verification of the OTHER table rows (esp. line 662 `redd+natveg_nosoil`), catching any sibling defect. Quantitative chain into M11 (highest-centrality). M56/M52 calibration-exempt, M11 re-probable.

### R42-Q2 — Climate → yields → SOM, parameterization vs mechanism (causal chain + parameterization detection)
**Modules**: 45, 14, 59
**Question**:
> How does climate (Module 45) enter MAgPIE and affect crop yields (Module 14) and soil organic matter (Module 59)? (a) What is the default climate/CO2 scenario and where is it set; (b) is the climate effect on yields MECHANISTIC, or applied as exogenous input data (parameterization)? Show the equation/parameter that carries it; (c) how does M45 feed M59 SOM dynamics? Cite file:line. Be explicit about parameterization vs mechanistic modeling.

**Why**: exercises the parameterization-vs-mechanism discipline (Query Pattern 4 / the "uses data about X ≠ models X" rule) which R41 never tested — and M45 climate is the canonical trap (LPJmL input data, not in-model climate dynamics). Fresh high-value module (M45 never deeply probed). M45/M59 re-probable, M14 exempt.

### R42-Q3 — Cropland soil-nitrogen budget (quantitative)
**Modules**: 50, 59, 18
**Question**:
> Give the cropland soil-nitrogen budget in Module 50's default realization. (a) The balance equation and its inputs (fixation, deposition, fertilizer, residue recycling, manure) and outputs (withdrawal, surplus); (b) how organic inputs from residues (Module 18) and SOM (Module 59) enter; (c) how the N surplus is computed and what it feeds downstream. Name the equation(s) + variables, cite file:line.

**Why**: quantitative formula-precision probe (forces the exact balance equation, not a gloss). M50 soil-N budget is high-stakes and was only lightly touched (R29-Q3 did supply=demand + a brief N mention). M50/M59/M18 all re-probable (M51 n-emissions is R41-locked → referenced only peripherally).

### R42-Q4 — Water-module infeasibility + environmental flows (edge-case/failure-mode)
**Modules**: 43, 42, 44
**Question**:
> What can make MAgPIE's water module infeasible, and how do environmental flow requirements (EFR) constrain water availability? (a) The default water-availability realization + how EFR is represented (which parameter/variable reserves water for ecosystems); (b) the supply-demand constraint and its infeasibility buffer; (c) how biodiversity (Module 44) interacts with water/land here. Name variables, cite file:line, and state what diagnostic signals a water infeasibility.

**Why**: edge-case/failure-mode archetype (R41 had none). Builds on R29-Q2 (water balance) from a failure-mode angle, and adds the EFR + M44 interaction not previously probed. M43/M42/M44 all re-probable.

### R42-Q5 — Bioenergy demand: report.mif → magpie4 → GAMS provenance (R-to-GAMS provenance)
**Modules**: magpie4 + 60, 62
**Question**:
> Trace the report.mif IAMC bioenergy-demand variable (e.g. `Demand|Bioenergy|...` or the magpie4 equivalent) from the magpie4 `report*` function back to its GAMS origin. (a) Which magpie4 `report*` function produces it, and from which version-pinned source file; (b) the underlying GAMS variable (`vm_dem_*`?) and the module (60 bioenergy / 62 material) that defines it; (c) any aggregation/units conversion magpie4 applies. Cite the version-pinned magpie4 source path (`.cache/sources/magpie4/...`) + the GAMS file:line.

**Why**: R-to-GAMS provenance archetype (the magpie4 layer), which R41 only touched via the structural G4. Pairs with G3. Tests the source-of-truth clone discipline + the report.mif→GAMS pivot. M60/M62 re-probable.

---

## Regression anchors (2)

### R42-G1 — Module 14 default realization (stability anchor)
**Question**:
> What is the default realization of module 14 (yields)? List the equations defined in its equations.gms.

**Expected** (regression_questions G1): default `managementcalib_aug19` (verify `cfg$gms$yields` in default.cfg); equations.gms defines exactly 2 — `q14_yield_crop`, `q14_yield_past`. Watch for fabricated `q14_yieldcalib` (the corrected-in-R22 trap) and count drift.

### R42-G3 — magpie4 source-of-truth / version pin (version-pin anchor)
**Question**:
> Which version of magpie4 does this agent's source-of-truth clone reflect, and how was that version determined? Cite the file(s) you read.

**Expected** (regression_questions G3): read `project/version_pins.json` (NOT the workspace clone); report version + SHA (R41 confirmed v2.70.0 @ a360d8c9ec); identify upstream authority `../input/renv.lock` (`Packages.magpie4` Version + RemoteSha); workspace clone intentionally NOT source-of-truth. Auditor MUST read version_pins.json directly to compute expected.

---

## Archetype coverage (R42)
| Probe | Archetype |
|-------|-----------|
| Q1 | Quantitative + chain (+ follow-on table re-check) |
| Q2 | Causal chain + parameterization-vs-mechanism |
| Q3 | Quantitative verification |
| Q4 | Edge case / failure mode |
| Q5 | R-to-GAMS provenance (magpie4) |
| G1 | Default realization (anchor) |
| G3 | magpie4 version-pin (anchor) |

## Modules exercised (R42)
11, 14, 18, 42, 43, 44, 45, 50, 52, 56, 59, 60, 62 + magpie4
(Confirmed: none in the R41-locked set as primary targets.)
