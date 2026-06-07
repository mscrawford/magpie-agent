# Doc Audit: cross_module/circular_dependency_resolution.md

**Auditor**: Opus adversarial documentation auditor (Round 49 doc-audit sweep)
**Date**: 2026-06-06
**Ground truth**: `/tmp/magpie_develop_ro` @ HEAD `ee98739fd` (develop worktree); `config/default.cfg` for defaults.
**Doc length**: 1037 lines.

---

## Scope note

This doc is a CONCEPTUAL document about how MAgPIE's recursive-dynamic structure resolves circular dependencies. Large portions are intentionally illustrative (ASCII feedback diagrams, pseudo-R verification snippets, decision trees, "Common Problems / Fix" advice). Per the audit method, only LOAD-BEARING, CODE-CHECKABLE claims are scored: interface variable/parameter/equation names, file:line citations, consumer/populator/declaration sets, realization names + defaults, parameter defaults, and equation forms. Pure prose/advice and the R verification snippets (which are explicitly illustrative, often using non-existent helper functions like `check_oscillation()`) are NOT scored.

Overall the doc is **high quality** on the items that matter most: the Appendix A lagged-variable citations, the corrected Cycle 1 yield nuance (lines 248), the Type 2 trade section, and the Cycle 4 variable declarations are all accurate and consistent with the G2 anchor (vm_carbon_stock declared in M56). The errors cluster in ONE conceptual example (Section 2.1 Type 1, Land↔Carbon) plus two minor equation-name shorthands.

---

## Claims verified CORRECT (high-value, confirmed against code)

### Appendix A — Lagged variable citations (all 3 confirmed exact)
- `pcm_land(j,land)` updated at `modules/10_land/landmatrix_dec18/postsolve.gms:9` — CONFIRMED (line 9: `pcm_land(j,land) = vm_land.l(j,land);`). Declared at declarations.gms:11.
- `pcm_carbon_stock(j,land,ag_pools,stockType)` updated at `modules/56_ghg_policy/price_aug22/postsolve.gms:8` — CONFIRMED (line 8 exact). Cited twice (lines 110, 973), both correct.
- `pcm_tau(j,tautype)` updated at `modules/13_tc/endo_jan22/postsolve.gms:16` — CONFIRMED (line 16: `pcm_tau(j, tautype) = vm_tau.l(j, tautype);`).

### q10_land_area equation (doc lines 65-69)
- `sum(land, vm_land(j2,land)) =e= sum(land, pcm_land(j2,land))` — CONFIRMED exact at `modules/10_land/landmatrix_dec18/equations.gms:13-15`. Equation name `q10_land_area` correct (declarations.gms:27). Good MANDATE-10 discipline: the doc preserves the set-based `sum(land, ...)` form, does NOT expand to member list.

### Cycle 1 corrected nuance (doc line 248) — EXEMPLARY
- `q14_yield_crop` scales `vm_yld` by decision variable `vm_tau`, cited `modules/14_yields/managementcalib_aug19/equations.gms:14-16` — CONFIRMED exact (lines 14-16). `i14_yields_calib` is indeed the calibrated baseline.
- `q14_yield_past` uses LAGGED `pcm_tau(j,'crop')`, cited `equations.gms:35-39` — CONFIRMED (line 39 has `pcm_tau(j2, "crop")`). The crop-vs-pasture distinction (crop = simultaneous NLP via current vm_tau; pasture = cross-timestep via pcm_tau) is accurate and well-explained.

### Type 2 — Production ↔ Trade (doc lines 121-154) — all confirmed
- `q17_prod_reg`: `vm_prod_reg = sum(cell(i,j), vm_prod)` — CONFIRMED `modules/17_production/flexreg_apr16/equations.gms:10-11`.
- `q21_trade_glo`: `sum(i2, vm_prod_reg) =g= sum(i2, vm_supply) + balanceflow` — CONFIRMED `modules/21_trade/selfsuff_reduced/equations.gms:12-14`.
- `q21_trade_reg` / `q21_trade_reg_up` exist — CONFIRMED (lines 31, 39).
- Default realization `selfsuff_reduced` — CONFIRMED (default.cfg: `cfg$gms$trade <- "selfsuff_reduced"`).
- `vm_import` / `vm_export` do NOT exist — CONFIRMED (whole-tree grep returns nothing; two methods + positive control on vm_supply).
- `v21_trade` exists ONLY in non-default `selfsuff_reduced_bilateral22`, NOT in default — CONFIRMED (declared in bilateral22/declarations.gms; absent from selfsuff_reduced). Excellent MANDATE-19 discipline.

### Cycle 4 — Forest-Carbon 5-way (doc lines 373-437) — variable declarations all correct
- `im_pollutant_prices(t_all,i,pollutants,emis_source) [56]` — CONFIRMED declared M56/declarations.gms; exact dims.
- `vm_carbon_stock(j,"forestry","vegc","actual") [56]` — CONFIRMED declared M56/declarations.gms:34 (NOT M52 — matches G2 anchor). "forestry" ∈ land, "vegc" ∈ c_pools (core/sets.gms: `/vegc,litc,soilc/`), "actual" ∈ stockType — valid indexing.
- `vm_emissions_reg(i,"co2_c") [52]` — declared in M56 (declarations.gms:40) but POPULATED by M52 for co2_c (`q52_emis_co2_actual`, `modules/52_carbon/normal_dec17/equations.gms`: `vm_emissions_reg(i2,emis_oneoff,"co2_c") =e= ...`). The `[52]` tag denotes the producer of the co2_c component — defensible in a producer-by-step data-flow chain. NOT scored as a bug.
- `vm_reward_cdr_aff(i) [56]` — CONFIRMED M56/declarations.gms:43.
- `vm_lu_transitions(j,...) [10]` — CONFIRMED M10/declarations.gms:23.
- `vm_cost_glo [11]` — CONFIRMED M11/declarations.gms:9.
- `s56_buffer_aff` default 0.5, "half of removals credited" — CONFIRMED (default.cfg:1767 = 0.5; input.gms semantics + equation `(1-n)*vm_cdr_aff` => 0.5 credited).
- `s56_c_price_induced_aff` default 1 (enable 1/0) — CONFIRMED (default.cfg:1741 = 1).

### Cycle 2 / Cycle 3 variable + dim claims
- `pm_land_conservation(t,j,land,consv_type) [22]` — CONFIRMED declared M22/area_based_apr22/declarations.gms; exact dims. Default realization `area_based_apr22` confirmed. Sets `vm_land.lo` in M35 (pot_forest_may24/presolve.gms:162,201,231) and M31 — the `[10]` tag on `vm_land.lo` denotes vm_land's owning module, defensible.
- `vm_area(j,kcr,"irrigated") [30]` — CONFIRMED declared M30 (both simple_apr24 + detail_apr24); "irrigated" ∈ w (core/sets.gms:241 `w / rainfed, irrigated /`). Default `simple_apr24` confirmed.
- `vm_AEI(j) [41]` — CONFIRMED declared M41/endo_apr13/declarations.gms:19. `pc41_AEI_start(j) = vm_AEI.l(j)` at postsolve.gms:8 — CONFIRMED exact (doc line 351). Default `endo_apr13` confirmed.

### Cross-reference + catalog
- Module_Dependencies.md "(lines 149-179)" (doc lines 411, 742) — CONFIRMED: those lines DO hold the C1-C4 cycle table the doc references.
- "10_land: 15 consumers" (doc line 581) — matches Module_Dependencies.md:143 ("10_land: 15 out"), its cited source. Internally consistent.
- "Independent modules (37, 45, 54)" (doc line 720) — defensible: M54 default `off` has no equations.gms; M45 default `static` has no vm_ references (input only); appropriately framed as parallelization "Opportunities".
- Section 8.2 "26 cycles" is explicitly hedged ("not fully documented", "Inferred", "Suspected") — self-aware, not a false claim.

---

## Bugs Found

### Bug CDR-B1 — False mechanism + wrong module attribution: land conversion costs do NOT use lagged carbon density, and are Module 39 not 29/30
- **Severity**: Major
- **Trigger**: "The claim is wrong in a way that misleads about behavior, but won't directly cause damaging action" (no specific variable/file named to edit; it is an illustrative Type-1 example). Borderline with the Critical "wrong module attribution for a cost variable" trigger, but that anchor is about naming a specific `vm_cost_*` to the wrong module; here the doc makes a conceptual data-flow claim. Tie-breaker -> Major.
- **Class**: 4 (Conceptual pseudo-code / false causal mechanism) + module mis-attribution.
- **Doc line**: cdr:113-114 (also the Section 2.1 diagram, cdr:97-106).
- **Claim in doc**: `* Module 29/30 (land conversion costs), equations.gms:` / `* Uses pm_carbon_density from PREVIOUS timestep for conversion costs`. The Type-1 example (cdr:92-106) frames "Land Allocation ↔ Carbon Stocks" as: `pm_carbon_density (previous timestep)` feeds "land costs", and "Timestep t: Use pm_carbon_density(t-1) as fixed parameter for land costs".
- **Reality in code**: Land conversion costs are **Module 39 (landconversion)**, default realization `calib`. The cost equation `q39_cost_landcon(j2,land)` (`modules/39_landconversion/calib/equations.gms`) computes cost from land expansion/reduction AREA (`vm_cost_landcon` = `ln(j,land)` cost), NOT from carbon density. M39 contains **zero** references to carbon density or carbon stock (whole-tree grep over M39 returns nothing). Modules 29 (cropland) and 30 (croparea) are not the conversion-cost modules. The `pm_carbon_density_*_ac` family (the real names; see B2) is consumed by M14/M29/M32/M35/M52 in preloop/presolve/start phases for carbon-stock accounting — never for conversion costs, and never by M39. The genuine carbon temporal-feedback is via `pcm_carbon_stock` (correctly cited at cdr:110), not via a carbon-density-driven land cost.
- **File evidence**: `modules/39_landconversion/calib/equations.gms` (q39_cost_landcon, area-based); `modules/39_landconversion/calib/declarations.gms:13` (`vm_cost_landcon(j,land) Costs for land expansion and reduction`); M39 has no carbon reference.
- **verify_cmd**: `rg -rn "carbon_density|carbon_stock" /tmp/magpie_develop_ro/modules/39_landconversion/` -> (no output) "M39 does NOT reference carbon density/stock". `grep -E "cfg\$gms\$landconversion" .../default.cfg` -> `calib`. `grep -rln "pm_carbon_density" .../modules/` -> 14_yields, 29_cropland, 32_forestry, 35_natveg, 52_carbon (NO 39).
- **confirmed**: true
- **Proposed fix**: Replace the Type-1 "Code Evidence" block (cdr:113-114) and align the diagram. The honest version: the Land↔Carbon temporal feedback runs through `pcm_carbon_stock` (lagged carbon stock), which M52 reads in `q52_emis_co2_actual` to compute CO2 emissions across timesteps. Land *conversion* costs (Module 39, `q39_cost_landcon`) are area-based and do NOT depend on carbon. Suggested replacement for cdr:113-114:
  ```
  * Module 52 (carbon), modules/52_carbon/normal_dec17/equations.gms:
  * q52_emis_co2_actual reads pcm_carbon_stock (PREVIOUS timestep) and
  * vm_carbon_stock (current) to compute CO2 emissions across timesteps.
  * (Land conversion costs themselves are area-based, Module 39 q39_cost_landcon,
  *  and do NOT use carbon density.)
  ```
  And in the diagram (cdr:97-99) replace `pm_carbon_density` with `pcm_carbon_stock` and relabel "(land costs)" to "(CO2 emissions / GHG cost)".

### Bug CDR-B2 — Variable name `pm_carbon_density` does not exist (real family is `pm_carbon_density_*_ac`)
- **Severity**: Minor
- **Trigger**: "Wrong detail, but a careful reader wouldn't be misled into action" — the name appears in a conceptual ASCII feedback diagram, and a real same-stem family exists (findable). (Confabulated variable names tend Critical, but the Critical trigger requires "presented as authoritative"; here it is diagram/illustrative, so Minor.)
- **Class**: 5/2 (generalized/approximate variable name).
- **Doc line**: cdr:98, cdr:105, cdr:114.
- **Claim in doc**: `pm_carbon_density ←──── vm_carbon_stock` (cdr:98); `Use pm_carbon_density(t-1) as fixed parameter` (cdr:105); `Uses pm_carbon_density from PREVIOUS timestep` (cdr:114).
- **Reality in code**: No plain `pm_carbon_density` (and no `pm_carbon_density_ac`) is declared anywhere. The actual family, all declared in `modules/52_carbon/normal_dec17/declarations.gms:9-13`, is: `pm_carbon_density_secdforest_ac`, `pm_carbon_density_other_ac`, `pm_carbon_density_plantation_ac` (+ `_uncalib` variants), each dimensioned `(t_all,j,ac,ag_pools)`.
- **File evidence**: `modules/52_carbon/normal_dec17/declarations.gms:9-13`.
- **verify_cmd**: `grep -rn "pm_carbon_density\b" /tmp/magpie_develop_ro/modules/*/*/declarations.gms` -> "no exact pm_carbon_density"; `grep -n "pm_carbon_density" .../52_carbon/normal_dec17/declarations.gms` -> the 5 `_ac`/`_ac_uncalib` names; `grep -rln "pm_carbon_density_ac" .../modules/` -> empty (even `_ac` alone is not a real name; positive control on `vm_cost_landcon` confirmed the grep works).
- **confirmed**: true
- **Proposed fix**: Subsumed by B1's fix (the diagram should use `pcm_carbon_stock`, the actual lagged interface, instead of the non-existent `pm_carbon_density`). If a carbon-density mention is retained anywhere, use the exact `pm_carbon_density_plantation_ac` / `_secdforest_ac` / `_other_ac` names with a note that they are age-class-resolved and declared in Module 52.

### Bug CDR-B3 — Wrong equation name `q10_land` (should be `q10_land_area`)
- **Severity**: Minor
- **Trigger**: "Off-by-detail in a conceptual block; correct full name used elsewhere in the same doc (cdr:67)". Wrong-equation-name tends Major, but this is a conceptual "Equations form system" block using `=` (not `=e=`) and the correct name `q10_land_area` appears at cdr:67 -> tie-breaker pulls to Minor.
- **Class**: 9 (Wrong equation name).
- **Doc line**: cdr:298.
- **Claim in doc**: `sum(land, vm_land(j,land)) = sum(land, pcm_land(j,land))  [q10_land, 10]`.
- **Reality in code**: The equation is named `q10_land_area` (declarations.gms:27; definition equations.gms:13). No equation named `q10_land` exists.
- **File evidence**: `modules/10_land/landmatrix_dec18/declarations.gms:27`; `equations.gms:13`.
- **verify_cmd**: `grep -rn "q10_land\b" .../10_land/ | grep -v "q10_land_area|..."` -> "NO bare q10_land".
- **confirmed**: true
- **Proposed fix**: In cdr:298 change `[q10_land, 10]` to `[q10_land_area, 10]`.

---

## Deferred (not scored — uncertain or not code-verifiable)

- **Module 41 equation orientation (cdr:348)**: doc shows `vm_AEI(j2) =g= sum(kcr, vm_area(j2,kcr,"irrigated"))`; code (`endo_apr13/equations.gms:11`) is `sum(kcr, vm_area(j2,kcr,"irrigated")) =l= vm_AEI(j2)`. Algebraically identical (A =g= B == B =l= A) and conceptually faithful ("irrigated area <= AEI capacity"); doc gives no line number and the relationship is correct. Not materially misleading -> deferred, no edit recommended.
- **Naming-convention gloss (cdr:60-63)**: "`pcm_*` ... ('p' = parameter, 'cm' = current module)". The `pcm` prefix meaning is a stylistic/etymological gloss, not strictly code-checkable. Plausible reading; deferred.
- **Internal doc-to-doc content refs**: "module_56.md (lines 60-79)" (cdr:411) — module_56.md exists (1160 lines) so the range is valid, but verifying the line-60-79 CONTENT against the claim is a doc-to-doc check outside this code audit's scope. Deferred.
- **Section 8.2 inferred cycles C5-C10 (cdr:750-756)**: explicitly labeled "Suspected"/"Inferred"; the doc disclaims they are unverified. Not asserted as fact -> not scored. (Spot impression: most module triplets named are plausible, but the doc itself flags them as needing verification.)
- **`s56_c_price_induced_aff` usage site**: confirmed to exist + default 1 in config; a clean grep for its in-code usage was muddied by a regex artifact (the trailing `_aff` matched fader lines). The doc's claim (exists, 1/0 enable) is satisfied by the config default alone, so no bug; deeper usage-site tracing deferred as not load-bearing for the doc's claim.

---

## Summary

Verified ~40 load-bearing claims. The doc is accurate on its highest-stakes content: all 3 Appendix A lagged-variable citations are exact; the corrected Cycle 1 yield nuance (vm_tau vs pcm_tau, crop vs pasture) is exemplary; the Type 2 trade section (q17_prod_reg, q21_trade_glo, vm_import/vm_export absence, v21_trade bilateral-only) is fully correct with good MANDATE-19 discipline; Cycle 4 variable declarations match code and the G2 anchor (vm_carbon_stock in M56). All cited realizations and defaults verified.

Three bugs, all clustered in conceptual/illustrative blocks: **1 Major** (CDR-B1: Section 2.1 falsely says land conversion costs use lagged carbon density and lives in Module 29/30 — actually Module 39, area-based, zero carbon dependence), **2 Minor** (CDR-B2: `pm_carbon_density` is not a real name, real family is `pm_carbon_density_*_ac` in M52; CDR-B3: `q10_land` should be `q10_land_area`). B1 and B2 share a fix: rewrite the Type-1 Land↔Carbon example to use the genuine `pcm_carbon_stock` temporal feedback (M52 q52_emis_co2_actual) instead of the confabulated carbon-density-driven land cost.

Per-question score equivalent: 10 - 2 (Major) - 1 - 1 (Minor) = 6/10 for the affected Section 2.1 cluster; the rest of the doc would score 9-10.
