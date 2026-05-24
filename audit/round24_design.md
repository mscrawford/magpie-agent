# Round 24 design

**Date**: 2026-05-24
**Type**: full (5 new probes + 2 regression anchors)
**Predecessor**: R23 (mean 9.0/10, new high water mark; G1+G2 regression at 10/10 each)

## Goals

1. **First exercise of G3 + G4 magpie4 regression anchors**. Both have `used_in_rounds: []`. The magpie4 helper is new (2026-05-24) and under-validated — G3/G4 establish the calibration baseline.
2. **Cover fresh modules** not in `probe_dedup_ledger.json` off-limits (modules 13, 30, 53, 60 are clean).
3. **Test multi-realization defaults under recent infrastructure** — the `check_module_realizations.py` (multi-path fix), `check_renames.py`, and bare-cite migration all landed in 2026-05-24 sessions; probes that touch their territory test whether the docs survived the migration.

## Off-limits check (against `audit/probe_dedup_ledger.json`)

Modules NOT off-limits and chosen as primary subjects:
- module_13 (tc) — endo_jan22 default — clean (last named in R3 spot-check, eligible since R6)
- module_30 (croparea) — simple_apr24 default — clean (M30 header warning in R3; default body rewrite still pending per next_session_plan §8)
- module_53 (methane) — ipcc2006_aug22 default — clean (R3 named M53 in cite-fix commit; eligible by R6)
- module_60 (bioenergy) — 1st2ndgen_priced_feb24 default — clean (never named in off_limits)

Modules incidentally mentioned (not primary subjects): module_56 (Q1 GHG-pricing chain), module_10/29 (Q4 cross-module).

## Round composition

| ID | Archetype | Modules | Why |
|----|-----------|---------|-----|
| G3 | Regression: version-pin discipline | magpie4 helper, project/version_pins.json | First use; magpie4 helper validation |
| G4 | Regression: R-package dispatch | magpie4 R/getReport.R | First use; tests `report*` enumeration capability |
| Q1 | Causal chain | 53 (primary), 56 (incidental) | Methane→GHG-pricing chain, default realization probe |
| Q2 | Default vs. switch | 60 (primary) | Bioenergy switches surface; fresh module |
| Q3 | Quantitative | 13 (primary) | Tau cost formula + objective-function entry |
| Q4 | Edge case / failure mode | 30 (primary), 10/29 (incidental) | M30 has header warning re: body-realization drift — does answerer get tripped? |

## Question text

### G3 (regression — magpie4 version pin)
Per `audit/validation_rounds.json` → `regression_questions[2]`:

> Which version of magpie4 does this agent's source-of-truth clone reflect, and how was that version determined? Cite the file(s) you read.

**Auditor must read `project/version_pins.json` at audit time** (current pin: `2.70.0` @ `a360d8c9ec1ee7af6c9287791e8b182bf391d355`, lock_file_sha256 `de41e0ce...`).

### G4 (regression — getReport dispatch)
Per `audit/validation_rounds.json` → `regression_questions[3]`:

> How does `magpie4::getReport` organize its reporting? Describe the dispatch pattern, how many unique `report*` functions it calls, and cite the file:line range from the pinned clone.

**Auditor must read `.cache/sources/magpie4/R/getReport.R` at audit time.**

### Q1 — Methane CH4-from-rice → GHG-pricing chain
> In Module 53's default realization, how are CH4 emissions from rice cultivation computed, and how do they propagate to the GHG-policy cost in Module 56? Walk through (a) the equation that populates `vm_emissions(i,kli_rd,"ch4_rice")` (or the analogous rice CH4 entry), (b) the source of the emission factor (which input file / parameter), and (c) where Module 56 picks up these CH4 emissions for pricing. Cite specific equations and file:line locations using full relative paths.

*Tests*: default-realization discipline (M53 has 3 realizations; ipcc2006_aug22 is default since 2022); cross-module CH4 routing; full-path citation convention.

### Q2 — Bioenergy default + switches
> What is the default scenario for bioenergy demand in MAgPIE? Identify (a) the default realization of Module 60, (b) the key scenario switches that change bioenergy behavior (`s60_2ndgen_bioenergy_dem_min`, `s60_biodem_level_min_em`, `s60_2ndgen_bioenergy_dem_min_post`, or similar — list whichever are in declarations.gms with default values), and (c) which equation enforces the 2nd-generation bioenergy floor. Cite full relative paths.

*Tests*: switch enumeration (Pattern 6 hardcoded-counts risk); default-vs-non-default discipline (Pattern 4 capability vs default); MANDATE 3 default-parameter verification.

### Q3 — Tau cost formula → objective function
> In Module 13's default realization (`endo_jan22`), how is the cost of technological change (`vm_cost_tc` or analogous) calculated from the tau rate? Walk through (a) the equation that links tau to its cost, (b) how tau is bounded over time (initial value, growth limits), (c) where this cost enters the global objective function (which `vm_cost_*` variable, and where Module 11 sums it). Cite specific equations and any key parameters with default values.

*Tests*: MANDATE 9 cost-variable attribution; cross-module cost-aggregation chain; MANDATE 1 formula provenance.

### Q4 — Croparea infeasibility / cross-module
> Module 30 (croparea) covers crop area allocation. Under what conditions can the simple_apr24 default realization contribute to model infeasibility? Identify (a) the primary constraint equations in `modules/30_croparea/simple_apr24/equations.gms`, (b) how Module 30 interacts with Module 10 (land) and Module 29 (cropland) — what variable does Module 30 receive vs. produce, (c) any documented debugging steps. Cite full relative paths.

*Tests*: M30 body-realization-drift risk (next_session_plan §8 flagged this as pending); MANDATE 6 module characterization lookup; the answerer must NOT describe `detail_apr24` (the cropland default, not croparea's) as if it were Module 30's default.

## Round-design checks

- ✅ ≥1 regression anchor (using TWO: G3 + G4)
- ✅ All new probes span ≥3 modules OR are magpie4 single-package (G3/G4 are magpie4-package)
- ✅ All probes target fresh primary modules (off-limits check passed)
- ✅ Bias toward high-centrality modules — Q3 targets module 13 (high TC dependency), Q1 targets module 53→56 (high-centrality GHG-pricing chain)
- ✅ ≥1 magpie4 question per 2-3 rounds — G3 + G4 both magpie4 (first round to exercise them)
- ✅ Each question requires reading ≥2 doc files (helper + module docs)
- ✅ Question count = 6 (within target 5 + 1-2 regression = 6-7)

## Expected calibration outcomes

- **G3 baseline**: Looking for whether the agent reads `project/version_pins.json` (not the workspace clone). Per the magpie4_reference.md auto-load rules. A 10/10 should cite version 2.70.0 + SHA a360d8c9ec + identify `../input/renv.lock` as upstream source-of-truth.
- **G4 baseline**: Looking for accurate enumeration of unique `report*` functions (~106 expected) + correct dispatch description (flat `tryList(...)`, NOT conditional `if(any(grepl(...)))`). Per the rubric §6 expected-answer summary.
- **Q1-Q4 probes**: Looking for default-realization fidelity, full-path citations (Check 25 enforced this), and no Pattern-4/Pattern-13 confabulations.
