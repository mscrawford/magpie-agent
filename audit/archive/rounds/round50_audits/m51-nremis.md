# Audit Report: M51-nremis (Module 51 nitrogen emissions — vm_emissions_reg population + MACC application)

**Anchor doc**: `modules/module_51.md`
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree), `config/default.cfg`
**Default realizations confirmed**: 51 nitrogen → `rescaled_jan21` (`config/default.cfg:1550`); 56 ghg_policy → `price_aug22` (:1613); 57 maccs → `on_aug22` (:1822); 53 methane → `ipcc2006_aug22` (:1583); 58 peatland → `v2` (:1853); 52 carbon → `normal_dec17` (:1556); 50 nr_soil_budget → `macceff_aug22` (:1479). All match the realizations the answer used. ✓

## Overall Verdict: SIGNIFICANT ERRORS
## Accuracy Score: 6/10

score = max(0, 10 - 4*1 - 2*0 - 1*0) = 6

---

## Mechanical checks
M1 citations present PASS · M2 realization stated PASS (rescaled_jan21, default) · M3 prefixes valid PASS · M4 badges PASS · M5 tier vs depth PASS (answer honestly flags it did not read raw GAMS this session) · M6 closing source PASS.

---

## Verified Claims (correct)

**DECLARES**
- `vm_emissions_reg(i,emis_source,pollutants)` DECLARED in M56 `price_aug22/declarations.gms:40` (Tg/yr). ✓ EXACT.
- `im_maccs_mitigation(t,i,emis_source,pollutants)` DECLARED in M57 `on_aug22/declarations.gms:13`. ✓ EXACT.

**M51 POPULATES (Section 2)** — all 8 equation names + line ranges EXACT vs `modules/51_nitrogen/rescaled_jan21/equations.gms`:
q51_emissions_man_crop 22-27 · q51_emissions_inorg_fert 30-39 · q51_emissions_resid 42-46 · q51_emissions_resid_burn 49-52 · q51_emissions_som 55-59 · q51_emissionbal_awms 65-71 · q51_emissionbal_man_past 74-80 · q51_emissions_indirect_n2o 83-89. ✓
- `emis_source_n51 = {inorg_fert, man_crop, awms, resid, resid_burn, man_past, som}` (`sets.gms:15-16`). ✓
- direct pollutants = `n_pollutants_direct`; eq8 adds `n2o_n_indirect` per source. ✓
- preloop.gms:8-10 fixes all sources to 0, then unbounds the 7 n51 sources. ✓ EXACT.
- NUE-rescaled column (man_crop/inorg_fert/resid/som/man_past yes; resid_burn/awms no) matches code and module_51.md appendix. ✓

**MACC application in M51 (Section 3)**
- Applied ONLY in eq6 `q51_emissionbal_awms` (`equations.gms:71`). Positive grep: `im_maccs_mitigation` appears in M51 ONLY at `rescaled_jan21/equations.gms:71`. ✓
- Slice consumed = `im_maccs_mitigation(ct,i2,"awms","n2o_n_direct")`; the `(1-…)` N2O factor multiplies the entire `n_pollutants_direct` dimension (NH3/NO2/NO3 cut by the N2O fraction). ✓ (lines 65-71; doc note module_51.md:159,418-419, with code comment lines 62-64).
- `im_maccs_mitigation` computed (not solved) in M57 `preloop.gms` via MACC-curve table lookup. ✓ (computation lines 46-66; answer's 41-66 includes the comment header — acceptable).
- "MACC influence on soil N2O works through the NUE in Module 50, not a direct M51 multiplier." ✓ Confirmed by realization header `equations.gms:18-19` and by the consumer grep showing `50_nr_soil_budget/macceff_aug22/presolve.gms` consumes `im_maccs_mitigation`.

**Other populators (Section 4)**
- M53 (methane) via q53_emissionbal_ch4_ent_ferm (21-29), q53_emissionbal_ch4_awms (48-52), q53_emissionbal_ch4_rice (59-63), q53_emissions_resid_burn (70-72). "3 of 4 have (1-im_maccs_mitigation); resid_burn the exception" — VERIFIED ✓ (resid_burn uses `s53_ef_ch4_res_ag_burn`). Eq-name + 21-29 exact; "40-72" loose but acceptable.
- M58 (peatland, v2) via q58_peatland_emis `v2/equations.gms:91-94`, `vm_emissions_reg(i2,"peatland",poll58)`; poll58 = {co2_c, ch4, n2o_n_direct} (`v2/sets.gms:36-37`) — "CO2, CH4, N2O" ✓.

**READS (Section 5)**
- M56 q56_emis_pricing reads `vm_emissions_reg(i2,emis_annual,pollutants)` (`equations.gms:15-17`). ✓ EXACT.
- M57 q57_labor_costs (35-43) + q57_capital_costs (45-52) read `vm_emissions_reg(...,pollutants_maccs57)` and back out pre-mitigation via `/(1-im_maccs_mitigation)`. ✓ EXACT. The "logical loop" framing (M57 writes im_maccs_mitigation → M51/M53 reduce vm_emissions_reg → M57 reads the reduced value) is accurate.

---

## Bugs Found

### Bug M51-B1 — Module 52 wrongly declared a NON-populator of vm_emissions_reg
- **Severity**: 🔴 Critical
- **Class**: wrong populator set (Bug_Taxonomy class 15 / producer-attribution; R20+G2 anchor class)
- **Trigger (§1 Critical)**: load-bearing populator enumeration wrong such that a refactor of `vm_emissions_reg` populators would miss Module 52 — same harm as the R20 `pm_carbon_density_ac` consumer-omission anchor and the G2 carbon-stock populator anchor.
- **Claim in answer** (Section 4): "Module 52 (carbon) does **not** write into `vm_emissions_reg` for GHG pricing. Land-use-change CO2 is computed inside Module 56's own equation `q56_emis_pricing_co2` (`equations.gms:19-22`) by reading `vm_carbon_stock` directly — a deliberate bypass of `vm_emissions_reg` for one-off CO2."
- **Reality in code**: M52 (`normal_dec17`) DOES populate `vm_emissions_reg`. `q52_emis_co2_actual` at `modules/52_carbon/normal_dec17/equations.gms:16-19`:
  ```gams
  q52_emis_co2_actual(i2,emis_oneoff) ..
   vm_emissions_reg(i2,emis_oneoff,"co2_c") =e=
     sum((cell(i2,j2),emis_land(emis_oneoff,land,c_pools)),
     (pcm_carbon_stock(j2,land,c_pools,"actual") - vm_carbon_stock(j2,land,c_pools,"actual"))/m_timestep_length);
  ```
  `emis_oneoff` = all LULUCF carbon-pool sources (`core/sets.gms:314-318`). M52 populates the one-off CO2 ("actual") slices of `vm_emissions_reg`. (LHS confirmed by positive-control re-grep with context.)
- **What the answer conflated**: two distinct CO2 paths exist; the answer got the pricing nuance right but the global conclusion wrong:
  1. TRUE — for GHG **pricing**, M56's `q56_emis_pricing_co2` (`equations.gms:19-22`) recomputes one-off CO2 from `vm_carbon_stock` (with the `c56_carbon_stock_pricing` switch), NOT from the CO2 slice of `vm_emissions_reg`. So that slice IS bypassed *for pricing*.
  2. FALSE — "M52 does not write into `vm_emissions_reg`." M52 populates the "actual" one-off CO2 into `vm_emissions_reg` (the accounting/reporting figure on the same interface). The bypass concerns which value M56 *prices*, not whether M52 *populates*.
- **File evidence**: `modules/52_carbon/normal_dec17/equations.gms:16-19` (populator); `modules/56_ghg_policy/price_aug22/equations.gms:19-22` (pricing recompute).
- **Anchor reference**: R20 (`pm_carbon_density_ac` consumer omission) + G2 (carbon-stock populator set). Wrong producer/populator set = Critical by future-reader harm even when adjacent reasoning is sound.
- **Root cause**: `answerer_confabulation`. NOT inherited from the docs — `module_56.md:66` correctly lists "52 LULUCF CO2" as a populator and `module_56.md:88-92` correctly scopes the bypass to `q56_emis_pricing_co2`. The answerer misread the doc's pricing-bypass nuance as a blanket "M52 doesn't populate."

---

## Latent doc findings (rubric §1.5 — do not change the answer score)

### LD-1 — doc was CORRECT (recorded so a future round does not "fix" it)
`module_56.md:66` lists `vm_emissions_reg` populators as "(51 N2O, **52 LULUCF CO2**, 53 CH4, 57 MACC-adjusted, 58 peatland)" — M52 IS listed. `module_56.md:88-92` scopes the bypass correctly to the pricing equation. The doc would have led the answerer to the right M52 answer; the answer contradicted it. No fix needed for the M52 fact.

### LD-2 — minor latent imprecision in module_56.md (NOT relied on by this answer)
- **Doc**: `module_56.md:66` calls Module 57 a populator ("57 MACC-adjusted") of `vm_emissions_reg`.
- **Code**: M57 only READS `vm_emissions_reg` (RHS in q57_labor_costs/q57_capital_costs, `on_aug22/equations.gms:38,40,48,50`; LHS there is `vm_maccs_costs`). The "after technical mitigation" adjustment is applied INSIDE M51/M53 via `(1-im_maccs_mitigation)`, not by M57. Listing M57 among populators conflates "the variable HOLDS post-mitigation values" with "M57 WRITES the variable."
- **Severity**: Minor (the rest of the populator list — 51/52/53/58 — is right; M57 is a producer-vs-consumer slip on one line). Purely latent: the answer correctly listed M57 as a reader only, so it did not inherit this. Suggested fix: drop M57 from the `module_56.md:66` populator list (or relabel: "values reflect M57 MACC mitigation applied within M51/M53"). MANDATE 18.

---

## Missing nuances (not bugs)
- The question asked to name equations + cite file:line for the populators. The answer did this well for M51 (all 8) and adequately for M53/M58; for M52 it not only omitted the equation but denied the populator role (→ B1).
- M50 (`macceff_aug22`) also consumes `im_maccs_mitigation` (`presolve.gms`); the answer correctly described this as the NUE channel for soil N2O but did not list M50 in a formal consumer enumeration. Acceptable given the M51-centric framing.

## Summary
Strong, well-cited answer on the M51 spine: declaration attribution (M56/M57) exact, all 8 M51 equation names + line ranges exact, the AWMS-only MACC application and the N2O-factor-applied-to-all-pollutants subtlety correct, the M50-NUE channel correct, and the M56/M57 reader chain (including the M57 back-calculation loop) correct. One Critical error: Section 4 asserts Module 52 does NOT populate `vm_emissions_reg`, contradicting `q52_emis_co2_actual` (`modules/52_carbon/normal_dec17/equations.gms:16-19`), which populates the one-off CO2 ("actual") slices. The answerer mistook M56's pricing-time bypass of the CO2 slice for blanket non-population by M52 — against a doc (`module_56.md:66,88-92`) that had the distinction right. Wrong populator set on the question's core ask → Critical (R20/G2 harm class). Score 6/10.
