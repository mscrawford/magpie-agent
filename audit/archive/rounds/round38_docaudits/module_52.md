# Round 38 doc audit — module_52.md (Carbon, normal_dec17)

**Auditor**: Opus adversarial doc auditor
**Date**: 2026-05-30
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree), HEAD `5ea394f` (Merge PR #877 rc2-4.14.0)
**Doc**: `/Users/turnip/Documents/Work/Workspace/magpie/magpie-agent/modules/module_52.md` (1224 lines)

## Overall verdict: ACCURATE (9.5/10)

This is an exceptionally accurate doc. It documents the 2026-04 growing-stock calibration overhaul of Module 52 (preloop.gms bisection, FRA-2025 targets, `im_vol_conv`, calibrated vs uncalibrated carbon-density siblings) and every load-bearing code claim I checked against develop is correct: equation, macros, sets, scalars + defaults, realization names, file:line citations across 9+ consumer modules, the full producer/consumer sets for 6 carbon-density parameters, and the G2 `vm_carbon_stock` DECLARED/POPULATED/READ split. Only one Minor citation issue found (a single non-default realization cited in an otherwise default-realization consumer list) plus a couple of non-code-verifiable provenance items deferred.

---

## Pre-run advisory (G2 / MANDATE-18 producer-declaration) — CONFIRMED CORRECT

The advisory asked to verify: `vm_carbon_stock` DECLARED in M56, POPULATED by M29/31/32/34/35/59, READ by M52 via `q52_emis_co2_actual`; and that `pm_carbon_density_*` consumer sets distinguish `_calib` vs `_uncalib` (M29/M32 consume `_uncalib`).

All confirmed:
- `vm_carbon_stock` DECLARED in `modules/56_ghg_policy/price_aug22/declarations.gms:34` (doc states "declared in Module 56" — lines 415-416, 695). ✓
- `pcm_carbon_stock` DECLARED in `price_aug22/declarations.gms:19`. ✓
- `vm_emissions_reg` DECLARED in `price_aug22/declarations.gms:40`. ✓
- POPULATORS of `vm_carbon_stock`: M29 (crop, `29_cropland/{detail,simple}_apr24/equations.gms` LHS), M31 (past, `endo_jun13/equations.gms:23-24`), M32 (forestry, `dynamic_may24/equations.gms` q32_carbon), M34 (urban, **`.fx` form** `exo_nov21/presolve.gms:8` `vm_carbon_stock.fx(j,"urban",...) = 0`), M35 (primforest/secdforest/other, `pot_forest_may24/equations.gms`), M59 (soilc, `cellpool_jan23/equations.gms`). EXACTLY the doc's list (line 424). ✓
  - NOTE: M34's populate is via `.fx` and is INVISIBLE to a `vm_carbon_stock(` grep — caught only by the MANDATE-20 `.fx` form grep. Doc correctly says "34 (Urban, fixed to 0)".
- M58 (peatland) does NOT reference `vm_carbon_stock` (verified absence + positive control on `vm_peatland`). Doc correctly says "Module 58 (peatland) does NOT populate it" (line 424). ✓
- M52 READS `vm_carbon_stock`/`pcm_carbon_stock` only via `q52_emis_co2_actual` (`normal_dec17/equations.gms:16-19`). ✓
- `_uncalib` consumers: M29 (`detail_apr24/preloop.gms:46,48`, switched on `s29_treecover_plantation` default 0), M32 (`dynamic_may24/presolve.gms:59` aff-secdf, `:61` aff-plant, `:68` ndc-secdf, switched on `s32_aff_plantation` default 0), M35 (`pot_forest_may24/presolve.gms:117,242,251`). Doc lists all. ✓
- Calibrated consumers: M14 (`managementcalib_aug19/presolve.gms:26` plant, `:44` secdf, `:53` other), M32 (`dynamic_may24/presolve.gms:65` plant + `preloop.gms:18,56`), M35 (`pot_forest_may24/presolve.gms:248,250` secdf, `:240` other). Doc lists all. ✓

---

## Verified claims (high-value sample)

### Module 52 own files
- Realization `normal_dec17` is default (`config/default.cfg`: `cfg$gms$carbon <- "normal_dec17"`). ✓
- `preloop.gms` exists, 118 lines (doc lines 4, 33, 220, 296). ✓
- `scaling.gms` exists: `q52_emis_co2_actual.scale(i,emis_oneoff) = 1e2` (`scaling.gms:8`; doc line 31). ✓
- Equation `q52_emis_co2_actual` at `equations.gms:16-19`, formula EXACT match (doc lines 302, 775-825). ✓
- `sets.gms:12-13`: `iter52 / iter1*iter25 /` = 25 iterations (doc lines 27, 225, 258, 262). ✓
- declarations.gms: all 6 carbon-density params (secdforest_ac:9, secdforest_ac_uncalib:10, other_ac:11, plantation_ac:12, plantation_ac_uncalib:13), `im_vol_conv(i):23`, equation:30. Doc citations all correct. ✓
- Scalars (`input.gms:45-49`): `s52_growingstock_calib /1/`, `s52_k_high_secdf /0.1/`, `s52_k_high_plant /0.15/`. Doc lines 221, 226-227, 677-679. ✓
- `c52_carbon_scenario` default `cc` (`input.gms:8`); `c52_land_carbon_sink_rcp` default `RCPBU` (`input.gms:13`). ✓
- `start.gms:43-44` saves `_uncalib` copies on `ag_pools` (both vegc+litc). Doc lines 278, 455-457, 477. ✓
- `start.gms:40` `im_vol_conv(i) = 0.5` fallback. Doc line 491. ✓
- preloop structure: `im_vol_conv` at :21 (always computed, outside if-block); `i52_bef_avg` :26; `i52_m_avg_*` :29-30; secdf bisection loop :49-68, overwrite :71-73; plantation loop :84-103, overwrite :114-116; log table :106-111. All doc citations correct. ✓
- preloop reads: `im_forest_ageclass` (secdf weight), `pm_land_plantation` (plant weight), `fm_ipcc_bef`, `fm_aboveground_fraction("secdforest")`/`("forestry")`, `sm_carbon_fraction`, `pm_climate_class`, `f52_volumetric_conversion`. ✓
- Plantation calibration reuses secdforest C_max `fm_carbon_density("y2025",j,"secdforest","vegc")` at preloop.gms:91 (doc line 263). ✓

### Macros & core sets
- `m_growth_vegc(S,A,k,m,ac) S + (A-S)*(1-exp(-k*(ac*5)))**m` at `core/macros.gms:18`. ✓
- `m_growth_litc_soilc(start,end,ac) (start + (end-start)*1/20*ac*5)$(ac<=20/5) + end$(ac>20/5)` at `core/macros.gms:20`. ✓
- `m_timestep_length` at `core/macros.gms:51`. ✓
- `emis_oneoff` at `core/sets.gms:314-318` (21 members, exact match), `c_pools` :324-325, `emis_land` :332-335. ✓

### Upstream interface-param declarations (MANDATE 18)
- `im_forest_ageclass` DECLARED M28 `oct24/declarations.gms:9`, POPULATED `oct24/preloop.gms:11,14`. M28 default `oct24`. ✓
- `pm_land_plantation` DECLARED M32 `dynamic_may24/declarations.gms:59`, POPULATED `dynamic_may24/preloop.gms:179`. ✓
- `fm_ipcc_bef` DECLARED M14 `managementcalib_aug19/input.gms:66`. ✓
- `fm_aboveground_fraction(land_timber)` DECLARED M14 `input.gms:74`. ✓
- `sm_carbon_fraction` defined M14 `input.gms:22` `/ 0.5 /` (doc lines 288, 528 cite input.gms:22). ✓

### Phase ordering (doc lines 220, 278, 451 — claim preloop runs AFTER start)
- `core/calculations.gms:13` runs `start` phase, `:15` runs `preloop` phase, BOTH once before the time loop, start FIRST. Confirms doc's "preloop runs after start; start saves uncalib before preloop overwrites." Also M28.preloop (module 28) runs before M52.preloop within the same preloop pass (numeric module order), so `im_forest_ageclass` is populated before M52 reads it. ✓

### fm_carbon_density consumer set (doc lines 265-273, 484)
- M14 `presolve.gms:35` ✓ | M29 `detail_apr24/equations.gms:41` ✓ | M30 `simple_apr24/equations.gms:51` ✓ | M32 `dynamic_may24/presolve.gms:176` ✓ | M35 `pot_forest_may24/equations.gms:44` ✓ | M56 `price_aug22/preloop.gms:10` ✓ | M59 `cellpool_jan23/preloop.gms:12` ✓ | M31 — see Minor bug below.

### im_growing_stock transitive consumers (doc line 725)
- DECLARED M14 `managementcalib_aug19/declarations.gms:17`. Consumed by M32 `dynamic_may24/presolve.gms:181` (+185) and M35 `pot_forest_may24/equations.gms:147` (+156,165-166). Doc cites :181 and :147. ✓

### im_vol_conv consumers in M73 (doc lines 16, 490, 744-746)
- M73 default `default`. `pm_demand_forestry(...) = round(... * im_vol_conv(i),3)` at `default/preloop.gms:49,51`; `im_timber_prod_cost(i,"wood"|"woodfuel") = s73_..._cost_... / im_vol_conv(i)` at `:90,91`. Shared wood/woodfuel. ✓

### Realization names (MANDATE 8) — all correct + all match defaults
managementcalib_aug19 (M14), detail_apr24 (M29 default), simple_apr24 (M30 default), endo_jun13 (M31 default), dynamic_may24 (M32), pot_forest_may24 (M35), price_aug22 (M56), cellpool_jan23 (M59), default (M73), oct24 (M28), exo_nov21 (M34 default). ✓

### Sets / switches
- `type32 / aff, ndc, plant /` at M32 `sets.gms:16-17` (doc line 138 parenthetical "set type32"). ✓
- `s32_aff_plantation` default 0, M32 `input.gms:35`; aff conditional `presolve.gms:58-63`. ✓
- `s29_treecover_plantation` default 0, M29 `detail_apr24/input.gms:20`; conditional `preloop.gms:45-49`. ✓

### Input files (`input/files`)
lpj_carbon_stocks.cs3, f52_growth_par.csv (`input.gms:40`), f52_land_carbon_sink_adjust_grassi.cs3 (`input.gms:83`), f52_fra_pla_gs.cs4 (`input.gms:62`), f52_fra_nrf_gs.cs4 (`input.gms:54`), f52_volumetric_conversion.csv (`input.gms:70`). All present and cited correctly. ✓

---

## Bugs found

### BUG module_52-B1 (Minor) — non-default realization cited in fm_carbon_density consumer list

- **Severity**: Minor
- **Class**: 10 (stale/off-target file:line citation) — citation drift trigger (off-realization)
- **Doc line**: module_52.md:269
- **Claim in doc**: "Module 31 (Past) — `modules/31_past/static/presolve.gms:16`"
- **Reality in code**: M31's DEFAULT realization is `endo_jun13` (not `static`). The default realization consumes `fm_carbon_density` at `modules/31_past/endo_jun13/equations.gms:24` (`m_carbon_stock(vm_land,fm_carbon_density,"past")`). The cited line content (`pcm_land(j,"past")*fm_carbon_density(t,j,"past",ag_pools)`) is correct only for the non-default `static` realization. Every OTHER consumer in this same list (lines 266-273) is cited via its DEFAULT realization (detail_apr24, simple_apr24, dynamic_may24, pot_forest_may24, price_aug22, cellpool_jan23), so the lone `static` citation is inconsistent and would send a careful reader to a non-default file.
- **File evidence**: `modules/31_past/endo_jun13/equations.gms:23-24` (default consumer); `modules/31_past/static/presolve.gms:16` (the cited non-default line); `config/default.cfg`: `cfg$gms$past <- "endo_jun13"`.
- **Confirmed**: true.
- **Proposed fix**: Replace `modules/31_past/static/presolve.gms:16` with `modules/31_past/endo_jun13/equations.gms:24` (the default realization). M31 genuinely belongs in the list; only the cited realization/line is off-default.

---

## Deferred (not code-verifiable here / low-priority, NOT edited)

- **Git provenance metadata** (doc lines 3-5 "PR #869 ipopt_part1, commit `75d7ee167`", 39 author "Georg Schroeter", 225/681 "commit `c7731e234`", 296 "PR #869 (2026-03-16)", 1220 "synced to commit `c7731e234` 2026-05-16"): the develop clone is shallow (1 commit visible, HEAD `5ea394f`), so commit hashes, PR numbers, author attribution, and dates cannot be confirmed. The CODE STATE these claims describe is fully present and correct in develop; only the VCS metadata is unverifiable. No edit.
- **"previously absent" for preloop.gms** (doc line 4): historical claim about prior code state; cannot verify against shallow clone. The file currently exists (118 lines). No edit.
- **Participates-In footer "Provides to: Modules 56, 11, 44" / "Depends on: 10, 28, 35"** (doc lines 1202-1203): M11 and M44 are NOT direct consumers of any M52 interface variable (verified: no `vm_carbon_stock`/`pm_carbon_density*`/`fm_carbon_density`/`vm_emissions_reg`/`im_vol_conv`/`i52_land_carbon_sink` read in `modules/11_costs/` or `modules/44_biodiversity/`; positive controls on `q11_*`/`vm_bv` confirm greps reliable). HOWEVER this block is auto-generated centrality/dependency-graph metadata in a footer (states "Centrality", "Hub Type"), where "Provides to" plausibly encodes transitive/cost-aggregation graph edges (M52 emissions → M56 pricing → M11 cost objective; M52 carbon densities → M35/M32 → land → M44 BII) rather than direct interface reads. Per rubric, footer metadata is low-stakes and I cannot confirm the schema intends "direct read", so I do not record a confirmed MANDATE-17 bug. Flagged here for maintainer judgment: if the schema means direct interface consumers, lines 1202-1203 overstate M11/M44.
- **m_growth_vegc written with `=`** (doc line 84: `m_growth_vegc(S,A,k,m,ac) = S + ...`): the `$macro` form has no `=`. The block is labelled "Macro definition" and the RHS is exact; this is a cosmetic illustration choice (Informational at most). No edit.
- **Step-4 plantation aboveground_fraction omission** (doc line 263): the "analogous to Step 3" summary lists the plantation-vs-secdf differences but does not mention that the secdf trial uses `fm_aboveground_fraction("secdforest")` (preloop.gms:61) while the plantation trial uses `fm_aboveground_fraction("forestry")` (preloop.gms:96). This is summarization incompleteness, not a stated falsehood. No edit.

---

## Summary

module_52.md is among the cleanest docs audited. Substance fully matches develop: 1 equation, 2 macros, all sets/scalars/defaults, 11 realization names (all = defaults), and the complete producer/consumer sets for `vm_carbon_stock`, `vm_emissions_reg`, `pcm_carbon_stock`, `fm_carbon_density`, `im_vol_conv`, and all 6 `pm_carbon_density_*[_uncalib]` siblings — including the MANDATE-20 `.fx` populate by M34 and the `_calib`/`_uncalib` split (M29/M32 new-establishment vs M14/M32/M35 existing-forest). 1 Minor bug (M31 consumer cited via non-default `static` realization instead of default `endo_jun13`). Provenance metadata (PR/commit/author/dates) deferred as not verifiable against the shallow develop clone.
