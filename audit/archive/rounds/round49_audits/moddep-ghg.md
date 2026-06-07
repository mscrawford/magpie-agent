# Audit Report: moddep-ghg (Carbon / GHG-policy cluster: M52, M56, M57 dependency edges)

## Overall Verdict: MOSTLY ACCURATE
## Accuracy Score: 8/10

Anchored on `core_docs/Module_Dependencies.md`. Ground truth: develop worktree `/tmp/magpie_develop_ro`.
Realizations verified: M52 = `normal_dec17`, M56 = `price_aug22`, M57 = `on_aug22` (`ls /tmp/magpie_develop_ro/modules/{52,56,57}_*/`).

---

## Verified Claims (correct)

- **M56 declares `vm_carbon_stock` and `pcm_carbon_stock`.** `vm_carbon_stock` at `modules/56_ghg_policy/price_aug22/declarations.gms:34` (positive variables block); `pcm_carbon_stock` at `declarations.gms:19` (parameters block). Both DECLARED in M56. ✓
- **M52 READS both in its sole equation.** `q52_emis_co2_actual` at `modules/52_carbon/normal_dec17/equations.gms:16-19` reads `pcm_carbon_stock(...,"actual") - vm_carbon_stock(...,"actual")`. Answer's quoted equation is verbatim-correct. ✓ (Edge 1, direction M56→M52, correct.)
- **The CO2-pricing bypass is real.** `q56_emis_pricing_co2` at `equations.gms:19-22` reads `pcm_carbon_stock`/`vm_carbon_stock` directly (with the `%c56_carbon_stock_pricing%` stockType), NOT `vm_emissions_reg`. module_56.md:90-92 documents this. Answer correctly flags it as undocumented in Module_Dependencies.md. ✓
- **M52→M56 `fm_carbon_density` edge is real and absent from Module_Dependencies.md.** M56 reads `fm_carbon_density("y1995",...)` at `modules/56_ghg_policy/price_aug22/preloop.gms:10`; `fm_carbon_density` is declared (as a `table` input) in M52 `normal_dec17/input.gms:16`. Whole-tree grep confirms M56 is a consumer; positive control (`pm_carbon_density_secdforest_ac`) proves the search works. Module_Dependencies.md has no mention. ✓ (One nuance the answer soft-pedals: `fm_carbon_density` is an `f`-prefix INPUT parameter, not computed by M52 — "M52 provides" is the doc-convention sense of "input.gms-declared in M52", not a produced variable. Not scored.)
- **M56→M57 `im_pollutant_prices` edge.** `im_pollutant_prices` declared at M56 `declarations.gms:9`, populated across M56 `preloop.gms:37-115`; M57 reads it at `modules/57_maccs/on_aug22/preloop.gms:24-25` to set MACC step indices. ✓
- **M57→M56 "no direct variable".** Confirmed: `im_maccs_mitigation` (declared M57 `declarations.gms:13`) is consumed by M50 (`50_nr_soil_budget/macceff_aug22/presolve.gms:56-63`), M51 (`51_nitrogen/rescaled_jan21/equations.gms:71`), M53 (`53_methane/ipcc2006_aug22/equations.gms:29,52,63`) — NOT M56. `vm_maccs_costs` (declared M57 `declarations.gms:25`) is consumed by M11 (`11_costs/default/equations.gms:28`) and M36 (`36_employment/exo_may22/equations.gms:28`) — NOT M56. Answer's Edge 5 is correct. ✓
- **Doc-characterization claims all accurate:** M56 centrality "#3, 16 total, 13 provides-to, 3 depends-on" (Module_Dependencies.md:33); M52 "1 dependency but 4 consumers" (:323); M57 appears only in the Layer-5 tree (:123) with no cluster-specific interface description; forest-carbon circular path `32 ←→ 30 ←→ 10 ←→ 35 ←→ 56` (:178); layer placement M52=Layer4 (:114), M56/M57=Layer5 (:122-123). ✓
- **M52 upstream count understated by the doc — directionally correct.** Code shows M52 `normal_dec17` reads module-interface vars from M56 (`vm_carbon_stock`), M45 (`pm_climate_class`), M28 (`im_forest_ageclass`), M32 (`pm_land_plantation`), plus inputs (`fm_carbon_density`, `fm_ipcc_bef`, `fm_aboveground_fraction`, `im_vol_conv`). The doc's "1 dependency" (:323) and the single-dep listing at :213 do understate this. ✓ (The PR-#869 / M14 attribution is a module_52.md claim not independently re-verified here; peripheral to the cluster-edge question.)
- **M12→M56 via `pm_interest` is real.** `pm_interest` read in M56 `equations.gms:52,78,79`. Answer's point #5 is correct that this is a genuine coordination dependency. ✓

---

## Bugs Found

### moddep-ghg-B1 — M52→M56 `vm_emissions_reg` edge mischaracterized (the CO2 contribution does NOT reach M56's pricing)
- **Severity**: Major
- **Class**: 4 (conceptual/behavioral mischaracterization) / MANDATE-17 (direct-vs-transitive; here a non-edge presented as a consumed edge)
- **Trigger**: "wrong in a way that misleads about behavior, but won't directly cause damaging action" (§1 Major).
- **Claim in answer**: Edge 2 — "M52's equation populates the CO2 slice of `vm_emissions_reg(i,emis_oneoff,"co2_c")`. M56 reads this via `q56_emis_pricing` (`equations.gms:17`)." And in the Architectural note: "This means M52's `vm_emissions_reg` contribution is used by M56's `q56_emis_pricing` (annual-type path) ...". And summary table row "M52 → M56 | `vm_emissions_reg(...,"co2_c")` | M52 populates CO2 slice; M56 prices".
- **Reality in code**:
  - M52 writes ONLY the `emis_oneoff` co2_c slice: `q52_emis_co2_actual(i2,emis_oneoff)` → `vm_emissions_reg(i2,emis_oneoff,"co2_c")` (`modules/52_carbon/normal_dec17/equations.gms:16-17`).
  - `q56_emis_pricing` is indexed `(i2,pollutants,emis_annual)` and reads `vm_emissions_reg(i2,emis_annual,pollutants)` — **`emis_annual` ONLY** (`modules/56_ghg_policy/price_aug22/equations.gms:15-17`).
  - `emis_oneoff` and `emis_annual` are DISJOINT sets (`core/sets.gms:314-323`): `emis_oneoff` = the LULUCF *_vegc/_litc/_soilc sources (what M52 writes); `emis_annual` = inorg_fert, man_crop, awms, resid, man_past, som, rice, ent_ferm, resid_burn, peatland.
  - Therefore `q56_emis_pricing` (annual) does NOT read M52's contribution. The one-off/CO2 path in M56 is `q56_emis_pricing_co2` (`equations.gms:19-22`), which re-derives from `vm_carbon_stock`/`pcm_carbon_stock` and **bypasses `vm_emissions_reg`** (the answer documents this bypass two paragraphs later, then contradicts it here).
  - Net: M56's pricing does NOT consume M52's `vm_emissions_reg` contribution. The only reads of M52's oneoff/co2_c slice of `vm_emissions_reg` are M56 postsolve reporting (`postsolve.gms:13,27,41,55`, `.l/.m/.up/.lo`) — not a structural/optimization edge. Confirmed twice; positive control: the same grep finds vm_emissions_reg consumers in M51/M53/M57/M58, so the search is working.
- **File evidence**: `modules/56_ghg_policy/price_aug22/equations.gms:15-17` (annual-only read); `:19-22` (oneoff CO2 bypass); `modules/52_carbon/normal_dec17/equations.gms:16-17` (M52 writes oneoff); `core/sets.gms:314-323` (disjoint sets).
- **Why Major not Critical**: both the equation (`q56_emis_pricing`) and variable (`vm_emissions_reg`) exist and are correctly named; no wrong-realization/invented-name/default-inversion. The error is a false coupling claim about behavior — a reader tracing "does editing M52's emission equation change M56's CO2 price?" would wrongly answer "yes, via q56_emis_pricing" when the truth is "no, M56's CO2 pricing re-derives from carbon stocks independently." Misleads about behavior → Major.
- **Root cause**: `doc_error` — the answer faithfully reproduced module_56.md:66 (see latent bug L1), which lists "52 LULUCF CO2" among providers of the `emis_annual` slice that `q56_emis_pricing` reads. The answer inherited the doc's conflation rather than re-deriving from the set definitions.
- **tier_uncertainty**: false.

---

## Latent Doc Bugs (recorded regardless of answer score — rubric §1.5)

### L1 — module_56.md:66 lists "52 LULUCF CO2" as a provider of `vm_emissions_reg(i,emis_annual,pollutants)`
- **Severity (future-reader harm)**: Major (borderline Critical)
- **Doc**: `magpie-agent/modules/module_56.md:66` — "**vm_emissions_reg(i,emis_annual,pollutants)**: Actual regional emissions from the emission modules (51 N2O, **52 LULUCF CO2**, 53 CH4, 57 MACC-adjusted, 58 peatland)". This bullet sits directly under the `q56_emis_pricing` equation (`module_56.md:54-56`), which is indexed by `emis_annual`.
- **Code reality**: M52 populates `vm_emissions_reg(i2,emis_oneoff,"co2_c")` only (`modules/52_carbon/normal_dec17/equations.gms:16-17`). `emis_oneoff ∩ emis_annual = ∅` (`core/sets.gms:314-323`). So M52 is NOT a provider of the `emis_annual` slice that `q56_emis_pricing` reads; M52's CO2 reaches pricing only through `q56_emis_pricing_co2`'s direct carbon-stock read, NOT through `vm_emissions_reg`. The general "providers of vm_emissions_reg" lists (module_56.md:590-592, :1024, :1066) are fine — M52 does provide the oneoff slice — but line 66 is specifically tied to the `emis_annual` equation and is wrong there.
- **Fix direction**: on module_56.md:66, drop M52 (it provides oneoff, not annual) OR rephrase to "from the annual-emission modules (51 N2O, 53 CH4, 58 peatland; CH4/N2O MACC-adjusted via M57's `im_maccs_mitigation`)" and point the M52 LULUCF-CO2 contribution at `q56_emis_pricing_co2`'s bypass.
- **Root cause**: `doc_error_answerer_beat_it` is NOT the right tag here — the answer did NOT beat it (B1 reproduced it). Tag: `doc_error`. Recorded as latent because it is the doc claim B1 inherited and it remains wrong for future readers even if B1's score is set aside.

### L2 — "57 MACC-adjusted" listed as a PROVIDER of `vm_emissions_reg` (DECLARED-vs-POPULATED-vs-READ, MANDATE 18)
- **Severity (future-reader harm)**: Major
- **Doc**: `module_56.md:66, :590-592, :714, :1024, :1066` all list "57 MACC-adjusted" among the emission modules that provide `vm_emissions_reg`.
- **Code reality**: M57 `on_aug22` only READS `vm_emissions_reg` (RHS in `q57_labor_costs`/`q57_capital_costs`, `equations.gms:38,40,48,50`) — it has NO LHS assignment to `vm_emissions_reg`. M57 PRODUCES `im_maccs_mitigation` (`declarations.gms:13`), which M51 (`rescaled_jan21/equations.gms:71`) and M53 (`ipcc2006_aug22/equations.gms:29,52,63`) apply to reduce THEIR OWN `vm_emissions_reg` populations. So the "MACC adjustment" of vm_emissions_reg happens INSIDE M51/M53 via M57's mitigation fraction; M57 is not a populator of vm_emissions_reg. Listing "57" as a provider conflates READ + mediated-mitigation with POPULATE.
- **Answer's handling**: the answer reproduced this provider list verbatim in Edge 2, but its OWN Edge 5 analysis is correct ("`im_maccs_mitigation` goes to emission modules, not M56" / "no direct variable from M57 to M56"). So for the M57→M56 question the answer beat the doc; it only inherited the imprecise label in the quoted §4.2 list. Tag: `doc_error` (the doc is wrong for future readers; this round's answer dodged the harm on the M57 edge).
- **Fix direction**: change "57 MACC-adjusted" to a parenthetical "(CH4/N2O MACC-adjusted in M51/M53 via M57's `im_maccs_mitigation`)" wherever M57 is listed as a vm_emissions_reg *provider*; keep M57 out of the producer set proper.

---

## Missing Nuances (not scored)

- The answer never states M57's realization name (`on_aug22`) even though it discusses M57's preloop/equations; M2 (active-realization stated) is satisfied for M52/M56 but thin for M57. Informational at most; not separately counted.
- The answer's `pcm_carbon_stock` declaration is cited as "declarations.gms:34" in the Edge-1 prose ("declaration home of `vm_carbon_stock` and `pcm_carbon_stock` (declarations.gms:34)") — line 34 is correct for `vm_carbon_stock` but `pcm_carbon_stock` is at `declarations.gms:19`. The Edge-1 table softens this (lists pcm as "declarations.gms" with no line). Off-by-content for one of two vars in one prose citation; immaterial (both ARE declared in M56), not scored as a separate bug.
- Layer architecture (M52 Layer4 below M56 Layer5) implies M52→M56 flow, but code shows M52 DEPENDS on M56 (reads M56-declared `vm_carbon_stock`) and M56's CO2 pricing re-derives carbon stocks — a bidirectional coupling the layering flattens. The answer already notes the circular nature, so no bug.

---

## Mechanical checks
- M1 (file:line citations present): PASS.
- M2 (active realization stated): PARTIAL — M52/M56 covered; M57 realization name not stated.
- M3 (variable prefixes valid): PASS (`vm_`, `pm_`, `im_`, `fm_`, `pcm_`, `q56_`, etc. all valid).
- M4/M5 (epistemic badges + tier-matches-depth): PASS — answer's 🟡/🟢 split is honest (docs-only read, no raw GAMS this session, flagged for high-stakes re-verify).
- M6 (closing source statement): PASS.

---

## Summary

The answer gets the cluster's structure right on almost every axis: M56→M52 (`vm_carbon_stock`/`pcm_carbon_stock`, correct declaration home and reader), the `fm_carbon_density` M52→M56 edge missing from Module_Dependencies.md, the M56→M57 `im_pollutant_prices` price edge, the M57→M56 "no direct variable" finding (im_maccs_mitigation → M50/51/53; vm_maccs_costs → M11/M36), and the doc-vs-code completeness critique (M57 absent from cluster descriptions, M52 upstream count understated, the CO2 bypass undocumented). It also correctly surfaces the `q56_emis_pricing_co2` bypass as the key architectural subtlety.

The one substantive error (B1, Major) is that it then claims M52's `vm_emissions_reg` CO2 contribution reaches M56 "via `q56_emis_pricing` (annual-type path)". It does not: M52 writes the `emis_oneoff` slice, `q56_emis_pricing` reads only the disjoint `emis_annual` slice, and the oneoff/CO2 path bypasses `vm_emissions_reg`. The answer is internally contradictory (it documents the bypass, then asserts the contribution is used via the annual path). Root cause is `doc_error`: module_56.md:66 lists "52 LULUCF CO2" as a provider of the `emis_annual` slice (latent bug L1). A second latent doc bug (L2, MANDATE-18) lists "57 MACC-adjusted" as a vm_emissions_reg *provider* when M57 only reads it and mediates via `im_maccs_mitigation` consumed by M51/M53 — the answer beat this one on the M57 edge but reproduced the label in its quoted §4.2 list.

Score: 10 − 2(1 Major) = **8/10**. Latent doc bugs L1 and L2 are fixed this session regardless of score (rubric §1.5).
