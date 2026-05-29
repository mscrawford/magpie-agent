# Round 28 — Design

**Date**: 2026-05-29
**Type**: coverage (never-deeply-probed modules) + magpie4 regression rotation
**Schema**: validation_rounds.json v1.3 | rubric v1.2
**Mode**: autonomous (user away; conduct validation + code-verified corrections; commit locally, NO push)

## Provenance / guard

- **Target**: magpie-agent semantic flywheel R28 (continuation of the runplan `/tmp/magpie_overnight_runplan.md`; R26+R27 ran interactively this morning, R28 deferred).
- **DEVELOP GUARD**: parent repo on `experiment/tc-marginal-pb`; verification truth = `origin/develop` (`ee98739fd`, 2026-05-29). Docs last synced to `3836bbaa9` (2026-05-11), develop now 24 commits ahead.
  - **Key finding**: `git diff 3836bbaa9..origin/develop` and `git diff origin/develop` (working tree) are BOTH EMPTY for all 8 target/anchor modules (60,39,34,37,54,14,52,56). So for these modules, sync-baseline ≡ current-develop ≡ experiment-working-tree (byte-identical). Auditors read the working tree directly; every finding is a genuine doc-vs-code discrepancy, NOT a sync artifact. (Only M21 + M32 diverge on the experiment branch — not targets.)
- **Baseline validator**: `validate_consistency.sh` = 40/42 pass, 2 advisory warnings (5 doc-unit-claim diffs [advisory]; hedged-claims clean). Hold as regression baseline.
- **Dedup**: M60/M39/M34/M37/M54 all FREE in probe_dedup_ledger (R27 locked M18/M53/M31/M40/M20/M70). G3/G4 are calibration-exempt.

## Regression rotation rationale

G1/G2 were exercised every round R22–R27; **G3/G4 (magpie4 anchors) last used R24** and the command file flags them "especially load-bearing." R28 rotates to **G3 + G4**. This also gives the round magpie4 coverage the 5 GAMS-module probes otherwise lack.

**Ground truth (for synthesis cross-check only — NOT shown to answerers/auditors):**
- G3: magpie4 **v2.70.0** @ `a360d8c9ec1ee7af6c9287791e8b182bf391d355`, resolution `sha`, from `project/version_pins.json`; upstream authority `../input/renv.lock` (Packages.magpie4).
- G4: `.cache/sources/magpie4/R/getReport.R` = 235 lines, **106 unique `report*` functions, 117 call lines**, flat `tryList`, no `control`/`grepl` gating.

## Default realizations (verified from config/default.cfg)

| Module | Default realization | Note |
|--------|--------------------|------|
| 60 bioenergy | `1st2ndgen_priced_feb24` | |
| 39 landconversion | `calib` | |
| 34 urban | `exo_nov21` | exogenous; LUH2/LUH3 data-source caveat (rubric Minor anchor) |
| 37 labor_prod | **`off`** | bait: "active mechanism claimed when OFF by default" Critical trigger |
| 54 phosphorus | **`off`** | bait: same |

## Questions

| Q | Module(s) | Archetype | Bait / focus |
|---|-----------|-----------|--------------|
| Q1 | 60 (+30/17, 16/21, 11) | causal chain + default | 2nd-gen bioenergy demand → land → objective; begr/betr crop set; vm_dem_bioen |
| Q2 | 39 (+10, 11) | conservation/cost chain | landconversion cost → objective; transitions; vm_cost_landcon vs vm_lu_transitions |
| Q3 | 34 (+10, 52) | default/switch + edge case | exo vs endo; land balance; carbon; LUH2/LUH3 caveat |
| Q4 | 37 (+38, 11) | default/switch | **default=off** — must NOT describe on-mechanics as active |
| Q5 | 54 (+50, 18/59) | default/switch + cross-module | **default=off** — P budget vs N budget/residues/SOM |
| Q6 | magpie4 | G3 regression | version-pin source-of-truth discipline |
| Q7 | magpie4 | G4 regression | getReport dispatch structure + count |

Full question text in `round28_answers/qN_answer.md` headers and `round28_synthesis.md`.
