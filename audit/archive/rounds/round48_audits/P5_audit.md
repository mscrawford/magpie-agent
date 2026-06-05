# Audit Report: R48-P5 (Tracing land-use initialisation input from .cs3 file through GAMS into the model)

## Overall Verdict: MOSTLY ACCURATE
## Accuracy Score: 8/10

Auditor: Opus, Round 48. Ground truth read this session from working tree @ ee98739fd (origin/develop).
Module 10 has a SINGLE realization (`landmatrix_dec18`, `config/default.cfg:232`), so M2 (active-realization) is trivially satisfied; the answer correctly names it implicitly via the `landmatrix_dec18` file paths.

---

## Verified Claims (correct)

- **`avl_land_t.cs3` exists and is loaded as `f10_land`**: confirmed. `modules/10_land/landmatrix_dec18/input.gms:8-12`:
  ```
  table f10_land(t_ini10,j,land) Different land type areas (mio. ha)
  $ondelim
  $include "./modules/10_land/input/avl_land_t.cs3"
  $offdelim
  ;
  ```
  Filename, parameter name `f10_land`, domain `(t_ini10,j,land)`, and the `$include` mechanism are all exact. (Answer cited `input.gms:8-11`; the table block actually spans 8-12 — off-by-one on the closing `;`, immaterial.) File exists on disk (`modules/10_land/input/avl_land_t.cs3`, listed in `input/files`).
- **Negative-value correction**: confirmed at `input.gms:16` — `f10_land(t_ini10,j,land)$(f10_land(t_ini10,j,land)<0) = 0;`. Answer's "input.gms:16" exact.
- **`pm_land_start`, `pm_land_hist`, `pcm_land` declared**: confirmed `declarations.gms:9-11` (answer cited 8-12 — the `parameters` block; correct). All three names exact.
- **Derivations in start.gms**: confirmed `start.gms:8-11`:
  - `pm_land_start(j,land) = f10_land("y1995",j,land);` (line 8) — matches answer's "1995 anchor" exactly.
  - `pm_land_hist(t_ini10,j,land) = f10_land(t_ini10,j,land);` (line 9) — matches.
  - `pcm_land(j,land) = pm_land_start(j,land);` (line 11) — matches.
- **`pcm_land` updated in postsolve**: confirmed `postsolve.gms:9` — `pcm_land(j,land) = vm_land.l(j,land);`. Answer's "postsolve.gms:9" exact.
- **First-consumer equation `q10_land_area`**: confirmed `equations.gms:13-15`:
  ```
  q10_land_area(j2) ..
   sum(land, vm_land(j2,land)) =e=
   sum(land, pcm_land(j2,land));
  ```
  Answer cited `equations.gms:13-15` exactly AND preserved the set-based `sum(land, ...)` form rather than enumerating members — correctly avoids the R16 set-expansion anchor bug.
- **`t_ini10` set members**: confirmed `sets.gms:8-10` — `/ y1995, y2000, y2005, y2010, y2015 /`. Matches answer's list.
- **`land` set members (7 types)**: confirmed `core/sets.gms:250-251` — `/ crop, past, forestry, primforest, secdforest, urban, other /`. Matches answer's list exactly.
- **`luh2_side_layers.cs3` exists and loads as `fm_luh2_side_layers`**: confirmed `input.gms:19-23`. (Answer named the file and treated it as a "second related file" — file/param correct; see Bug P5-B1 for the source mix-up.)
- **"PROVIDES TO" — pm_land_start consumed by M14, M32, M59, M71**: confirmed by grep — `pm_land_start` consumed in `14_yields/managementcalib_aug19/preloop.gms`, `32_forestry/dynamic_may24/preloop.gms`, `59_som/cellpool_jan23/preloop.gms`, `71_disagg_lvst/foragebased_jul23/preloop.gms` (and `foragebased_aug18`). All four modules the answer named are correct.
- **Yield parallel (secondary section) — all concrete claims correct**:
  - `f14_yields(t_all,j,kve,w)` loaded via `$include "./modules/14_yields/input/lpj_yields.cs3"` — confirmed `14_yields/managementcalib_aug19/input.gms:35,37`; description literally "LPJmL potential yields", so the LPJmL source attribution is correct.
  - `i14_yields_calib(t,j,kve,w)` declared `declarations.gms:9`, derived `preloop.gms:8` (`= f14_yields(...)`) — confirmed.
  - `q14_yield_crop` exists `equations.gms:30` — confirmed.

---

## Bugs Found

### Bug P5-B1 — Wrong upstream source for the main land-init data (LUH2 claimed; current source is LUH3)
- **Bug ID**: R48-P5-B1
- **Severity**: Major
- **Class**: 11 (Wrong GAMS filename / source attribution) — manifesting as wrong-source-version rather than wrong-filename
- **Trigger** (§1 Major): "Right concept, wrong number" — right KIND of source (a land-use harmonization product feeding `calcLanduseInitialisation`), wrong VERSION (LUH2 vs the current LUH3). Not Critical: no wrong-file edit or model-breaking action follows from a provenance mislabel; LUH2/LUH3 are successive versions of the same product, so it is not a fabricated nonexistent source.
- **Claim in answer**: "The land-use initialisation data originates from the **LUH2 (Land-Use Harmonization v2)** dataset." (Step 1, repeated in Summary Table row "Upstream source ... LUH2 v2".) Applied to `avl_land_t.cs3` / `f10_land`.
- **Reality in code/data**:
  1. The `avl_land_t.cs3` header (`modules/10_land/input/avl_land_t.cs3:1,4`) gives `description: Land use initialisation data for different land pools` and `origin: calcOutput(type = "LanduseInitialisation", ...) (madrat 3.35.1 | mrlandcore 1.6.5)`. It does **not** name LUH2.
  2. The authoritative upstream chain (preproc-agent smoke test `magpie-preproc-agent/tests/manual_smoke_questions.md:15-17`, and the live index `magpie-preproc-agent/index/functions.json:6216-6220` for `mrdownscale:::convertLUH3`): `mrlandcore::calcLanduseInitialisation` → `calcLanduseInitialisationBase` → `calcOutput("LUH3", ...)`, with **"LUH3 (CMIP7 input4MIPs, v3.1.1) named as the primary data source."**
  - Compounding sub-error (same bug): the answer inverted which file is the LUH2 one. The genuinely-LUH2 file is `luh2_side_layers.cs3` — its header (`modules/10_land/input/luh2_side_layers.cs3:1,3`) reads `description: Data from LUH2 provided by David Leclere from IIASA` / `origin: calcOutput(type = "Luh2SideLayers", ...) (... mrmagpie 1.64.2)`. The answer demoted this genuinely-LUH2 file to a "second related file" while attributing LUH2 to the main file, which the data does not support.
- **File evidence**:
  - `modules/10_land/input/avl_land_t.cs3:4` — `origin: calcOutput(type = "LanduseInitialisation", ... ) (madrat 3.35.1 | mrlandcore 1.6.5)` (no LUH2).
  - `modules/10_land/input/luh2_side_layers.cs3:1` — `description: Data from LUH2 provided by David Leclere from IIASA`.
  - `magpie-preproc-agent/tests/manual_smoke_questions.md:16-17` — `calcOutput("LUH3", ...)`; "LUH3 (CMIP7 input4MIPs, v3.1.1) named as the primary data source".
  - `magpie-preproc-agent/index/functions.json:6216-6220` — `mrdownscale:::convertLUH3` present in live index.
- **Anchor reference**: loosely resembles the R16 Module-34 "LUH2 vs LUH3" minor anchor (§1 Minor), but that anchor was a footer/realization-doc ambiguity a careful reader would catch by checking both. Here the wrong source is the *load-bearing answer to the question asked* ("what is the upstream data source?"), prominently in Step 1 and the summary table, with an added file-inversion — so it clears the Minor bar and lands at Major.

---

## Latent doc bugs (recorded independent of the answer score)

### Latent P5-D1 — Data_Flow.md "Land Use (LUH2)" heading is stale (current source is LUH3)
- **Class**: 15 (latent doc error)
- **Root cause**: `doc_stale_source_version` (NOT `doc_error_answerer_beat_it` — the §1.5 answerer-beat-it variant requires the answer to be correct; here the answer reproduced the wrong version, so the answer was *not* right. Recorded here so Step 5 fixes the doc regardless.)
- **Severity by future-reader harm**: Major (a reader trusting the heading cites the wrong harmonization version; not Critical because it is a source-version label, not a producer/consumer set).
- **Doc evidence**: `core_docs/Data_Flow.md:39` — `**Land Use (LUH2 - Land-Use Harmonization v2):**`; also `:414` — `LUH2 land-use patterns` (calibration-targets list).
- **Nuance that mitigates blame on the doc**: Data_Flow.md:39-41 actually lists *only* `luh2_side_layers_0.5.mz` and `fm_luh2_side_layers()` under the LUH2 heading — i.e. the doc correctly scopes LUH2 to the side layers and does NOT place `avl_land_t.cs3`/`f10_land` under LUH2. The answer's mis-attribution of LUH2 to the main file is therefore primarily **answerer confabulation** (it extended the heading to a file the doc did not cover), with the doc's terse heading a contributing latent ambiguity. The doc fix: (a) update the heading to LUH3 for the main land-init data and the calibration-target line; (b) add `avl_land_t.cs3` / `f10_land` to Data_Flow.md with its actual `calcLanduseInitialisation` (mrlandcore → LUH3) provenance, distinct from the LUH2 side layers.
- **Does not affect the P5 answer score** (per §1.5); fix in validate-semantic Step 5.

---

## Missing Nuances (not scored)

- The answer's prefix glosses are slightly loose but self-correcting: `pm_` rendered as "processing module parameter" (MAgPIE convention is parameter, module-declared-but-globally-shared) — the answer also states "cross-module shared" alongside, so a reader is not misled. `pcm_` = "previous-timestep cross-module" is a reasonable gloss. Informational at most; not counted.
- The answer frames `start.gms:8` as the "first consumption" and `input.gms` as the "reading mechanism." Defensible: `input.gms:16` already *reads* `f10_land` (in its own negative-value correction) before `start.gms` projects it into `pm_land_start`. Either could be called "first." Not a bug — the question distinguishes reading mechanism from the set/parameter consumed, and start.gms is the first projection into model state parameters.
- `f10_land` is also used to populate `fm_land_iso` chain via `avl_land_t_iso.cs3` (`input.gms:25-29`) — a third LUH-derived table the answer omits. Completeness gap, not an error.

---

## Mechanical checks

| Check | Result | Note |
|---|---|---|
| M1 file:line citations present | PASS | many exact `modules/10_land/landmatrix_dec18/*.gms:NN` |
| M2 active realization stated | PASS (trivial) | M10 single-realization; paths name `landmatrix_dec18` |
| M3 variable prefixes valid | PASS | `f10_/pm_/pcm_/vm_/q10_/f14_/i14_` all valid |
| M4 epistemic badges present | PASS | every step badged 🟡 |
| M5 tier matches depth | PARTIAL | all claims tagged 🟡 Documented; the LUH2 source claim was wrong *in the doc-derived form* — correct tag for a docs-only answer, but the underlying fact is wrong (Bug B1) |
| M6 closing source statement | PASS | "Based on ... Data_Flow.md / module_10.md" with file:line list |

---

## Summary

The mechanical spine of the trace is essentially flawless: `avl_land_t.cs3` → `f10_land(t_ini10,j,land)` (`input.gms:8-12`, exact filename + parameter + `$include`), negative-value correction (`input.gms:16`), derivation of `pm_land_start`/`pm_land_hist`/`pcm_land` (`start.gms:8-11`, `declarations.gms:9-11`), `pcm_land` carry-forward (`postsolve.gms:9`), first-consumer `q10_land_area` (`equations.gms:13-15`, set-sum preserved), and the four `pm_land_start` downstream consumers (M14/32/59/71) — all verified correct against code. The yield-parallel secondary section is likewise fully correct (`f14_yields`, `lpj_yields.cs3`, `i14_yields_calib`, `q14_yield_crop`, LPJmL).

The single substantive error is the upstream-source attribution — the heart of the explicit sub-question "what is the upstream data source?". The answer says LUH2; the current source for `avl_land_t.cs3`/`f10_land` is **LUH3** (`calcLanduseInitialisationBase` → `calcOutput("LUH3", ...)`, mrlandcore), and the answer additionally inverted which file is the genuinely-LUH2 one (the side layers). One Major bug → 10 − 2 = **8/10**.

One latent doc bug recorded (Data_Flow.md "Land Use (LUH2)" heading stale → LUH3; class 15, Major by future-reader harm) for Step-5 fixing; it does not change the answer score, and it is NOT the `doc_error_answerer_beat_it` variant because the answer did not beat it.
