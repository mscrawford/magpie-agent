# Audit Report: G2 (vm_carbon_stock propagation — Module 52 → Module 56 GHG-policy cost)

**Round**: 50 (calibration anchor, regression question)
**Auditor model**: Opus 4.8 (1M)
**Date**: 2026-06-07
**Ground-truth worktree**: `/tmp/magpie_develop_ro` (develop)

## Overall Verdict: ACCURATE
## Accuracy Score: 10/10
## drift_observed: false

---

## Verified Claims (all confirmed against code)

### Declaration / producer-consumer spine (the core anchor assertion)
- **`vm_carbon_stock` DECLARED in Module 56, NOT Module 52** — CONFIRMED.
  `modules/56_ghg_policy/price_aug22/declarations.gms:34` (`positive variables`, `vm_carbon_stock(j,land,c_pools,stockType)`).
  Double-confirmed absent from `modules/52_carbon/normal_dec17/declarations.gms` by two methods (rg + read); positive control (`vm_emissions_reg` 2 hits in 56 eq, `vm_carbon_stock` 2 hits in 52 eq) proves the search works.
  Answer cited `price_aug22/declarations.gms:34` — exact.
- **`pcm_carbon_stock`** declared in 56/declarations.gms:19 (parameter) — consistent with answer's use.
- **Module 52 only READS** `vm_carbon_stock`/`pcm_carbon_stock` via `q52_emis_co2_actual` — CONFIRMED.
  `modules/52_carbon/normal_dec17/equations.gms:16-19`. Formula in answer matches the code character-for-character (incl. `pcm_carbon_stock - vm_carbon_stock` at `"actual"`, `/m_timestep_length`, `sum((cell,emis_land(...)))`). Output is `vm_emissions_reg(i,emis_oneoff,"co2_c")`. Answer's citation `normal_dec17/equations.gms:16-19` — exact.

### Populators (high-risk direction: a "does NOT populate" or wrong-populator claim is the worst false positive)
All confirmed at the DEFAULT realization (config keys verified in `config/default.cfg`):
- **29 cropland** (`detail_apr24`, default.cfg:795): `detail_apr24/equations.gms:39` writes `vm_carbon_stock(j2,"crop",ag_pools,stockType)`. ✓
- **31 pasture** (`endo_jun13`, default.cfg:969): `endo_jun13/equations.gms:23`. ✓
- **32 forestry** (`dynamic_may24`, default.cfg:976): `q32_carbon`, `dynamic_may24/equations.gms:108`. ✓
- **34 urban, "fixed to 0"** (`exo_nov21`, default.cfg:1126): `exo_nov21/presolve.gms:8` `vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0;`.
  NOTE: this is a SOLUTION-LEVEL `.fx` write in presolve, invisible to a `vm_carbon_stock(` equation grep — the answer correctly characterized urban as populated-to-zero (R33-class near-miss avoided). ✓
- **35 natveg** (`pot_forest_may24`, default.cfg:1135): primforest/secdforest/other at `pot_forest_may24/equations.gms:43,50,54`. ✓
- **59 SOM, soilc pool** (`cellpool_jan23`, default.cfg:1916): `cellpool_jan23/equations.gms:62` writes `vm_carbon_stock(j2,land,"soilc",stockType)`. Answer named Module 59 (soilc) WITHOUT pinning a realization, so the static_jan19-vs-cellpool_jan23 distinction did not produce an error. ✓

### Module 56 pricing chain
- **`q56_emis_pricing_co2`** — `price_aug22/equations.gms:19-22`. Formula exact, incl. `vm_carbon_stock(...,"%c56_carbon_stock_pricing%")`. ✓
- **`q56_emission_cost_oneoff`** — `equations.gms:45-52`. Formula exact, incl. `* m_timestep_length` and annuity `pm_interest/(1+pm_interest)`. ✓
- **`q56_emission_costs`** — `equations.gms:56-58`: `vm_emission_costs(i2) =e= sum(emis_source, v56_emission_cost(i2,emis_source));`. ✓
- Chain order `q56_emis_pricing_co2 → v56_emis_pricing → q56_emission_cost_oneoff → v56_emission_cost → q56_emission_costs → vm_emission_costs(i)` — CONFIRMED.
- **`vm_emission_costs` → Module 11** — CONFIRMED. `modules/11_costs/default/equations.gms:26: + vm_emission_costs(i2)` in objective cost sum. ✓

### Defaults / switches
- **`c56_carbon_stock_pricing <- "actualNoAcEst"`** — default.cfg:1817. ✓
- **`c56_emis_policy <- "reddnatveg_nosoil"`** — default.cfg:1810. ✓
- **`s52_growingstock_calib` default = 1** — `52_carbon/normal_dec17/input.gms:46`. ✓

### Density-parameter machinery (Part 1 supporting detail)
- **`fm_carbon_density` from LPJmL**, `input.gms:18`, file `lpj_carbon_stocks.cs3` — table declared input.gms:16-20, `$include` at line 18. ✓
- **`m_growth_vegc(S,A,k,m,ac) = S + (A-S)*(1-exp(-k*(ac*5)))**m`** — `core/macros.gms:18`. Exact (GAMS uses `**`; answer's prose `^m` is math-notation, not a copy-paste claim). ✓
- **`m_growth_litc_soilc`** linear 20-yr approach — `core/macros.gms:20`. ✓
- **start.gms age-class densities**: plantation vegc:17/litc:20, secdforest vegc:28/litc:31, other vegc:48/litc:51 — ALL exact. ✓
- **preloop.gms calibration overwrite**: secdforest vegc assignment at line 71, plantation at line 114; answer's `71-73,114-116` covers the multi-line assignments; gated by `s52_growingstock_calib = 1` (`preloop.gms:23`). ✓
- **`im_pollutant_prices` build** in `preloop.gms:35-123` (selection starts line 35 "select ghg prices"; file is 123 lines); policy-matrix multiply via `f56_emis_policy` at **`preloop.gms:84-91`** (assignments lines 87/89) — answer cited 84-91, EXACT. ✓

---

## Bugs Found
**None.**

## Claim not directly file-verifiable this session (NOT a bug)
- Answer lists the exact pools priced under `reddnatveg_nosoil` (primforest_vegc/litc, secdforest_vegc/litc, other_vegc/litc, peatland; cropland/pasture/forestry CO2 + all soilc = 0). The matrix lives in `modules/56_ghg_policy/input/f56_emis_policy.csv`, which is supplied via input.tgz and is ABSENT from the read-only worktree (the `input/` dir holds only a `files` manifest). The claim is corroborated by (a) the config note at default.cfg:1021 ("no price on CO2 emissions from land-use change in module 32_forestry ... reddnatveg_nosoil") and (b) the policy-name semantics (redd + natveg, nosoil). Consistent with all available evidence and with prior knowledge of this policy; the answer did not overstate its verification basis. No score impact.

## Mechanical checks
- M1 (file:line citations): PASS — dense, exact citations throughout.
- M2 (active realization): PASS — single-realization modules (52 normal_dec17, 56 price_aug22) noted; defaults named (actualNoAcEst, reddnatveg_nosoil, s52_growingstock_calib=1).
- M3 (variable prefixes): PASS — vm_/pm_/pcm_/v56_/s52_/c56_/fm_ all valid.
- M4/M5 (epistemic badges/depth): answer uses GAMS code blocks + doc-source footer rather than per-claim 🟢/🟡 glyphs. Footer present ("Documentation sources: module_52.md ...; module_56.md ..."). Informational at most, not scored (consistent with prior G2 anchor scoring).
- M6 (closing source statement): PASS — closes with documentation-source line citing module_52.md and module_56.md with line ranges.

## Anchor comparison
Matches the immutable §1.5 / §6 G2 ground truth exactly: declaration in M56 (NOT M52, the corrected-R22 attribution), M52 read-only, the 5 land modules + M59 SOM as populators, the full M56 chain to vm_emission_costs(i), actualNoAcEst default. This is the post-recovery quality level (anchor recovered to 9 at R27 per rubric §1.5). This round reaches 10 — clean, no latent doc bug surfaced.

## Summary
Reference-quality answer. Every load-bearing claim — the declaration site, the producer/reader/consumer distinction, all six populators at their default realizations (including the `.fx` solution-level urban write that defeats a naive grep), the complete Module-56 pricing chain with exact formulas and line numbers, both governing switch defaults, and the density-parameter machinery — verified against `/tmp/magpie_develop_ro`. Zero bugs. The single non-file-verifiable detail (priced-pools matrix) is gated behind a runtime-only input file and is independently corroborated. No drift; the anchor is healthy this round.
