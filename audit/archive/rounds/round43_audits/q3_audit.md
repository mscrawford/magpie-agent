# Audit Report: Q3 (Module 58 Peatland — GHG Emission Representation)

**Round**: 43 | **Auditor**: Opus | **Date**: 2026-06-03
**Ground truth**: develop @ HEAD ee98739fd (clean), live GAMS at `modules/58_peatland/v2/`, `modules/56_ghg_policy/price_aug22/`, `modules/52_carbon/normal_dec17/`, `core/sets.gms`, `config/default.cfg`.

---

## Overall Verdict: ACCURATE
## Accuracy Score: 10/10

`score = max(0, 10 − 4·0 − 2·0 − 1·0) = 10`

This is a near-exemplary answer. Every load-bearing claim — default realization, parameterization framing, the two emission equations and their line numbers, and (most importantly) the central thesis that peatland emissions **bypass Module 52 / `vm_carbon_stock` and reach Module 56 directly via `vm_emissions_reg` as an `emis_annual` source** — is verified correct against code. The few imperfections found are all Informational (illustrative-pseudocode index elision; a slightly-wide citation range; a units phrasing that matches the input file's own header). None would mislead a reader into a wrong action, so none score.

---

## Mechanical Checks (M1–M6)

| # | Check | Result | Note |
|---|---|---|---|
| M1 | File:line citations present | ✅ PASS | Many `equations.gms:NN`, `preloop.gms:NN`, `default.cfg` cites |
| M2 | Active realization stated | ✅ PASS | "Default realization: `v2`", alternative `off` named, confirmed vs default.cfg |
| M3 | Variable prefixes valid | ✅ PASS | `vm_`, `v58_`, `p58_`, `f58_`, `pc58_`, `s58_`, `im_`, `pm_` all correct scope |
| M4 | Epistemic badges present | ⚠️ PARTIAL | Single 🟡 blanket badge in closing block; no per-claim badges. Acceptable (uniform-confidence answer), not scored |
| M5 | Confidence tier matches depth | ✅ PASS | All claims tagged 🟡 documented; closing states "No raw `.gms` files were opened" — honest about depth |
| M6 | Closing source statement | ✅ PASS | "Based on module_58.md documentation" form, with full source list |

M4 partial is not a bug — the answer uses one uniform 🟡 tag because it was docs-only; the §1 Informational trigger for "missing badge" is reserved for cases that mislead, which this does not.

---

## Verified Claims (correct)

**(a) Default realization + drivers**
- ✅ Default `v2`: `config/default.cfg:1853` → `cfg$gms$peatland <- "v2"   # def = v2`. Initial grep with escaped `$` failed; plain grep confirmed.
- ✅ Realizations are exactly `v2` and `off`: `ls modules/58_peatland/` → `input, module.gms, off, v2`. Answer's "alternative `off` disables the module" correct.
- ✅ Seven peatland states (intact, crop, past, forestry, peatExtract, unused, rewetted): `sets.gms:10-11` (`land58`). Cite exact.
- ✅ Area driven by managed-land dynamics from M10/M32 via scaling factors: `q58_peatlandMan` at `equations.gms:46-50` (header line 46, body 47-50). The `m58_LandMerge(vm_land, vm_land_forestry, ...)` macro (`q58_manLand`, eq:22-23) confirms M10 (`vm_land`) + M32 (`vm_land_forestry`) inputs.
- ✅ `p58_scalingFactorExp` = available-peatland / available-non-managed-land: `presolve.gms:60-67` — `p58_availPeatlandExp = totalPeatland − manPeatland` (line 60), `p58_availLandExp = totalLand − manLand` (line 61), ratio at line 63. Capped at 1 (line 67). Description accurate.
- ✅ `p58_scalingFactorRed` = drained-peatland-of-type / total-peatland: `presolve.gms:71-75`; in-block comment line 70 literally reads "manPeatland / totalPeatland". Accurate.
- ✅ Total peatland conserved by `q58_peatland` at `equations.gms:12-13` (`sum(land58, v58_peatland) =e= sum(land58, pc58_peatland)`). Cite exact.
- ✅ Historical fixing before `s58_fix_peatland` (default 2020): `presolve.gms:9-32` block (`if (m_year(t) <= s58_fix_peatland ...`, `v58_peatland.fx` at line 23); default `s58_fix_peatland <- 2020` at `default.cfg:1910`. Cite exact.

**(b) Parameterization, not mechanistic**
- ✅ Emission equation `q58_peatland_emis_detail` at `equations.gms:84-87` — verbatim: `v58_peatland_emis(j2,land58,emis58) =e= sum(clcl58, v58_peatland(j2,land58) * p58_mapping_cell_climate(j2,clcl58) * f58_ipcc_wetland_ef(clcl58,land58,emis58))`. Answer's rendered form matches. Cite exact (84-87).
- ✅ "Area × climate-zone indicator × emission factor" framing is exactly the equation structure. PARAMETERIZATION verdict correct.
- ✅ `f58_ipcc_wetland_ef` is exogenous, `$include`-loaded: declared `table f58_ipcc_wetland_ef(clcl58,land58,emis58)` at `input.gms:74`, `$include "./modules/58_peatland/input/f58_ipcc_wetland_ef2.cs3"` at `input.gms:76`. Filename `f58_ipcc_wetland_ef2.cs3` confirmed to exist. Time-invariant (no `t` index). Three-check (equation / source / feedback) is sound.
- ✅ Dimensions "3 climate zones × 7 states × 4 gases": `clcl58 = {tropical, temperate, boreal}` (sets.gms:45-46); `land58` 7 states; `emis58 = {co2, doc, ch4, n2o}` (sets.gms:30-31). Correct.
- ✅ **Example EF table — all three rows match the input file exactly**:
  - Tropical/crop CO2 14.0 / CH4 0.007 / N2O 0.005 → cs3 line 10 `tropical,crop,14,0.82,0.007,0.005` ✓
  - Temperate/crop CO2 9.5 / CH4 0.0206 / N2O 0.0111 → cs3 line 9 `temperate,crop,9.5,0.31,0.0206,0.0111` ✓
  - Boreal/rewetted CO2 −0.34 / CH4 0.041 / N2O 0.0001 → cs3 line 23 `boreal,rewetted,-0.34,0.08,0.041,1e-04` ✓
- ✅ Sources "IPCC Wetlands 2014, Tiemeyer et al. 2020": cs3 header lines 2-3 confirm "IPCC, Wetlands, 2014" + "Tiemeyer et al. 2020". (Answer also lists "Wilson et al. 2016" — not in this cs3 header; see Missing Nuances, not scored.)
- ✅ DOC tracked as separate gas, mapped to `co2_c`: `emis58` includes `doc` (sets.gms:31); `emisSub58_to_poll58` maps `doc .(co2_c)` (sets.gms:39-43, specifically line 41). Cite exact. The nuance that "CO2 and DOC both contribute to co2_c" is correct.
- ✅ Intact-EF override at `preloop.gms:43`: verbatim `f58_ipcc_wetland_ef(clcl58,"intact",emis58) = f58_ipcc_wetland_ef(clcl58,"rewetted",emis58)`. Rationale (prevent optimizer exploiting zero intact EFs) matches code comment lines 41-42. Cite exact.
- ✅ `p58_mapping_cell_climate` derived from `pm_climate_class` (M45) at `preloop.gms:36`: `p58_mapping_cell_climate(j,clcl58) = sum(clcl_mapping(clcl,clcl58), pm_climate_class(j,clcl))`. Cite exact.

**(c) Routing to M52 / M56 — the central thesis**
- ✅✅ **Bypass-M52 claim is CORRECT.** Verified three independent ways:
  1. `grep vm_carbon_stock modules/58_peatland/` → **empty** (exit 1). M58 never reads or writes `vm_carbon_stock`.
  2. `peatland` ∈ `emis_annual` (`core/sets.gms:320-323`: `/ inorg_fert, man_crop, awms, resid, man_past, som, rice, ent_ferm, resid_burn, peatland /`) and **NOT** ∈ `emis_oneoff` (`core/sets.gms:315-319` — list ends at `other_soilc`, no peatland). So peatland routes through `q56_emis_pricing` (the `emis_annual` branch reading `vm_emissions_reg`), not `q56_emis_pricing_co2` (the `emis_oneoff` branch reading `vm_carbon_stock`).
  3. M52 `q52_emis_co2_actual` reads only `vm_carbon_stock`, which M58 does not populate. Answer's "Module 52 does not read from Module 58" holds.
- ✅ M58 writes `vm_emissions_reg(i2,"peatland",poll58)` via `q58_peatland_emis` at `equations.gms:91-94`. Verbatim match. Cite exact (91-94).
- ✅ `poll58 = {co2_c, ch4, n2o_n_direct}` (sets.gms:36-37). Correct.
- ✅ `vm_emissions_reg` bounds at `preloop.gms:31-33` (`.fx`/`.lo`/`.up`). (Answer labels this "Declaration" — minor mislabel; these set bounds, the interface is declared elsewhere. Lines cited are accurate. Informational, not scored — see below.)
- ✅ M56 reads it in `q56_emis_pricing(i2,pollutants,emis_annual)` at `equations.gms:15-17`: `v56_emis_pricing(i2,emis_annual,pollutants) =e= vm_emissions_reg(i2,emis_annual,pollutants)`. Cite exact (15-17).
- ✅ Separate stock-change path exists and is distinct: `q56_emis_pricing_co2(i2,emis_oneoff)` at `equations.gms:19-21` uses `vm_carbon_stock` + `emis_land` + `c_pools`. Confirms the two-path distinction the answer draws.
- ✅ Cost chain to objective: `im_pollutant_prices` used in `q56_emission_cost_annual` (eq:29-33, the `emis_annual` branch) → `v56_emission_cost` → `q56_emission_costs` (eq:49-51) → `vm_emission_costs(i2)` → enters M11 objective at `modules/11_costs/default/equations.gms:26`. Answer's "M56 → emission cost → M11 (objective)" chain correct.
- ✅ Default pricing config: `c56_pollutant_prices <- "R34M410-SSP2-NPi2025"` (`default.cfg:1713`), `c56_emis_policy <- "reddnatveg_nosoil"` (referenced `default.cfg:1022`). Answer's near-zero-near-term caveat is reasonable for an NPi2025 scenario.

---

## Bugs Found

**None that score.** No Critical, Major, or Minor bugs. Items below are Informational (style/precision, do not mislead into action) and are listed for completeness only — they contribute 0 to the score.

- **Q3-I1** — *Informational* — Class 4 (conceptual pseudo-code, benign). Section (a) pseudocode writes `* p58_scalingFactorExp(j)` (and the displayed `q58_peatlandMan` block) with the time index dropped; the actual parameter is `p58_scalingFactorExp(t,j)`, accessed in-equation via `sum(ct, p58_scalingFactorExp(ct,j2))` (`equations.gms:49`). The block is explicitly framed as illustrative ("+/- balance terms" shorthand), so a reader is not misled about the real code. No score.
- **Q3-I2** — *Informational*. EF units stated as "t C or t N per ha per year". The `input.gms:74` table header literally says "Tg per ha per yr", while the cs3 file's own header (line 1) says "t CO2-C N2O-N CH4 per ha". The **source is internally inconsistent**; the answer matched the cs3 file's header. Not the answer's error. No score.
- **Q3-I3** — *Informational* — Class 10-adjacent (citation slightly wide, not drifted). Scaling factors cited as "presolve.gms:54-75"; the actual formula block is lines 60-75 (54-59 are comment lines + the `p58_availLandExp` setup). The range encompasses the correct content; no drift to *wrong* content. No score.
- **Q3-I4** — *Informational*. "Declaration: preloop.gms:31-33" mislabels bound-setting lines (`vm_emissions_reg.fx/.lo/.up`) as a declaration. Lines cited are accurate for what they do (constraining the interface). No score.

---

## Missing Nuances (not bugs)

- The answer attributes the EF sources to "IPCC Wetlands 2014, Tiemeyer et al. 2020, **Wilson et al. 2016**." The cs3 header (lines 2-3) cites only IPCC 2014 + Tiemeyer 2020 (+ a note that drained-unused uses Tiemeyer). "Wilson et al. 2016" is not in this input file's header — likely carried from doc text or an older EF provenance. Harmless (a provenance footnote, not a model-behavior claim), but worth a doc note if it traces to module_58.md.
- The answer's diagram routes peatland cost via "q56_emis_pricing → emission cost". Strictly, for an `emis_annual` source the cost is formed in `q56_emission_cost_annual` (eq:29-33), not the one-off branch. The answer's prose correctly says "enters the annual emission pricing equation — not the stock-change CO2 path," so the diagram's compression is not a content error.
- The answer's claim that peatland prices come from `im_pollutant_prices(t,i,pollutants,"peatland")` is exactly right because peatland is the `emis_annual` index value in `q56_emission_cost_annual` (line 33 uses `im_pollutant_prices(ct,i2,pollutants,emis_annual)`).

---

## Latent Doc Bugs (§1.5)

**None recorded.** This was a docs-only answer that got everything load-bearing right. I spot-checked the doc claims the answer leaned on:
- "Module 58 does NOT populate `vm_carbon_stock`" (attributed to `module_56.md:§4.1`) — **matches code** (grep empty). No latent bug.
- "No carbon stock accounting" (attributed to `module_58.md:§13.1`) — **matches code** (no `vm_carbon_stock`, no carbon-pool tracking in M58). No latent bug.
- "peatland is `emis_annual`" / routing claims — match `core/sets.gms`. No latent bug.

I did not exhaustively read module_58.md / module_56.md line-by-line (the answer's code-corroborated claims all checked out), so I cannot certify those docs globally — only that the **load-bearing** claims the answer used are code-consistent. No `doc_error_answerer_beat_it` warranted.

---

## Summary

Verdict **ACCURATE**, score **10/10**. The answer correctly: (a) identifies `v2` as the default realization (`default.cfg:1853`; only `v2`/`off` exist) and attributes area dynamics to M10/M32 managed-land changes scaled by `p58_scalingFactorExp/Red`; (b) classifies the emission representation as **parameterization** — endogenous peatland area × exogenous, time-invariant, `$include`-loaded IPCC EFs (`f58_ipcc_wetland_ef`, cs3 file) via `q58_peatland_emis_detail` (`equations.gms:84-87`), with all three example EF values matching the input file exactly; and (c) nails the central routing thesis — peatland is an `emis_annual` source (`core/sets.gms:320-323`), **not** `emis_oneoff`, so it enters M56 directly through `vm_emissions_reg` → `q56_emis_pricing` (`equations.gms:15-17`) → annual emission cost → M11 objective, and **bypasses M52 / `vm_carbon_stock` entirely** (verified: M58 contains zero `vm_carbon_stock` references; M52 never reads M58). The four imperfections are all Informational and do not affect the score. The "emission accounting map" suggested in *Doc Wished Existed* is a legitimately useful artifact and matches a real gap.

**Verified M58 default**: `v2` (confirmed `config/default.cfg:1853`).
**Bypass-M52 claim**: CORRECT — peatland ∈ `emis_annual`, ∉ `emis_oneoff`; M58 never touches `vm_carbon_stock`; emissions flow only through `vm_emissions_reg` → M56 annual pricing.
