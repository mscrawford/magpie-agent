# Round 55 depth audit — module_56.md — lens: consumer_read

**Target:** `modules/module_56.md` (Module 56 GHG Policy, realization `price_aug22`)
**Ground truth:** `/private/tmp/magpie_develop_ro` (develop worktree)
**Date:** 2026-07-16
**Verdict:** ACCURATE. This doc has clearly been hardened by the G2 flywheel; every load-bearing consumer/producer/citation claim under the lens checked out. One Minor confabulation (illustrative example uses non-existent `emis_source` labels). Three items deferred (input CSV data not readable + two non-exhaustive-summary observations).

---

## Method

Entered from the consumer side. For each interface var M56 declares (`vm_emission_costs`, `vm_reward_cdr_aff`, `vm_carbon_stock`, `im_pollutant_prices`) and each var M56 reads (`vm_emissions_reg`, `vm_cdr_aff`, `pm_interest`, `pcm_carbon_stock`), checked `audit/integrated/depth_rolemap.json` first, then confirmed with BOTH-endpoints greps (`NAME(` and `NAME.`) against develop, and verified the reader's realization is the config default and the cited line contains the claimed token.

---

## Verified correct (high-confidence, code-confirmed)

**Consumer/reader sets (whole-tree grep, both forms):**
- `im_pollutant_prices` — read outside M56 ONLY by M57 (`modules/57_maccs/on_aug22/preloop.gms:24-25`). Doc line 679 correct; M57 default = `on_aug22` (config:1840). Doc line 1026 "M57 only reads vm_emissions_reg; does not populate it" — confirmed (M57 reads `vm_emissions_reg` on RHS at `on_aug22/equations.gms:38,40,48,50`; never on LHS).
- `vm_reward_cdr_aff` — read outside M56 ONLY by M11 (`modules/11_costs/default/equations.gms:27`, **negative sign** `- vm_reward_cdr_aff(i2)`). Doc lines 314/573/1019 correct.
- `vm_emission_costs` — read outside M56 by M11 (`default/equations.gms:26`, positive) and M15 (`anthro_iso_jun22/intersolve.gms:23`, `vm_emission_costs.l` for `p15_tax_recycling`). Doc lines 564-566 correct; M15 default = `anthro_iso_jun22` (config:410); the `.l` postsolve read is invisible to a `vm_emission_costs(` grep — doc caught it. (Role map lists M15 as a "populator" too; that is only `anthro_iso_jun22/scaling.gms:22` `.scale=1e2`, a solver scale factor, not a real populate — doc correctly says M15 only *reads*.)
- `vm_carbon_stock` populators = 29, 31, 32, 34, 35, 59; NOT 58; M30 via `vm_carbon_stock_croparea`. Confirmed: 29/31/32/35 populate on equation LHS; 34 via `.fx=0` (`34_urban/exo_nov21/presolve.gms:8`, default `exo_nov21`); 59 soilc (`59_som/cellpool_jan23/equations.gms:62`, default `cellpool_jan23`); 58 has no `vm_carbon_stock` reference (positive control: 52 does). Doc lines 584, 1037-1046 correct — matches the G2 anchor.

**Carry-forward split (per-slice, MANDATE 18 corollary):** M56 postsolve carries `ag_pools` (`price_aug22/postsolve.gms:8`); M59 carries `soilc` (`59_som/cellpool_jan23/postsolve.gms:13`, comment explicitly "as done for the above-ground pools in 56_ghg_policy"). Doc line 581 correct including the develop provenance framing.

**Producer set for `vm_emissions_reg`** = 51, 52, 53, 58 (role map + doc lines 66, 591, 1026). Correct.

**Declarations (all exact):** `im_pollutant_prices` :9, `p56_c_price_aff` :11, `pcm_carbon_stock` :19, `vm_carbon_stock` :34, `vm_emission_costs` :39, `vm_reward_cdr_aff` :43. Doc citations at lines 152, 568, 575, 585, 676, 685 all correct.

**Equations:** all 7 present, line ranges exact (15-17, 19-22, 29-33, 45-52, 56-58, 67-71, 73-79). `q56_emis_pricing_co2` reads `pcm_carbon_stock("actual") - vm_carbon_stock("%c56_carbon_stock_pricing%")` directly (parallel to M52's read, not a serial hand-off) — doc section 2.2 "Architectural Note" (lines 88-92) correctly frames this as a direct read bypassing `vm_emissions_reg`. MANDATE 21 direction claim is right.

**Defaults (config + input.gms):** `price_aug22` (config:1631); `c56_pollutant_prices` R34M410-SSP2-NPi2025, `c56_emis_policy` reddnatveg_nosoil, `c56_cprice_aff` secdforest_vegc, `c56_carbon_stock_pricing` actualNoAcEst, `c56_mute_ghgprices_until` y2030; scalars s56_limit_ch4_n2o_price 4920 (input.gms:65), s56_cprice_red_factor 1 (:66), s56_minimum_cprice 3.67 (:67), s56_ghgprice_devstate_scaling 0 (:68), s56_c_price_induced_aff 1 (:69), s56_c_price_exp_aff 50 (:70), s56_buffer_aff 0.5 (:71), s56_ghgprice_fader 0 (:75). Every input.gms line number and value matches. `sm_fix_SSP2 = 2025` (config:225). All preloop stage citations (35-123) verified line-by-line.

**Counts:** `scen56` = 44 policies, `pollutants_all` = 16, `emis_source` = 31 (core/sets.gms:302-312) → doc's "44 × 16 × 31" (line 494) and "44 policies" (lines 37, 655) exact. `redd+natveg_nosoil` exists (sets.gms scen56). 709 LOC, 7 equations — both exact.

---

## Bugs found

### BUG 1 (Minor) — Illustrative "Selective Pricing Example" uses non-existent `emis_source` labels

- **doc_line:** module_56.md:505-508
- **Claim:** presents, in exact GAMS syntax, `f56_emis_policy("redd_nosoil","co2_c","deforest") = 1`, `...("redd_nosoil","co2_c","cropland_soil") = 0`, `...("redd_nosoil","ch4","livestock") = 0`.
- **Reality:** the third index of `f56_emis_policy` is an `emis_source` member. `deforest`, `cropland_soil`, and `livestock` are NOT members of `emis_source` (core/sets.gms:302-312 = inorg_fert, man_crop, awms, resid, man_past, som, rice, ent_ferm, resid_burn, {crop,past,forestry,primforest,secdforest,urban,other}_{vegc,litc,soilc}, peatland). The intended real analogs would be e.g. `secdforest_vegc` (deforestation CO2), `crop_soilc` (cropland soil), `ent_ferm`/`awms` (livestock CH4).
- **Why Minor not higher:** hedged with "might have" under a header labeled "Selective Pricing Example" — a careful reader reads it as illustration. But it is written in real GAMS index syntax with fabricated set members (MANDATE 5/12 anti-pattern), so a reader could mistake the labels for real indices; the surrounding doc is otherwise precise about `emis_source`.
- **Fix:** either relabel "Conceptually:" and drop the code syntax, or use real members, e.g. `f56_emis_policy("redd_nosoil","co2_c","secdforest_vegc") = 1`, `f56_emis_policy("redd_nosoil","co2_c","crop_soilc") = 0`, `f56_emis_policy("redd_nosoil","ch4","ent_ferm") = 0`.

---

## Deferred (not flagged — could not verify, or non-load-bearing)

1. **`f56_emis_policy.csv` data-content claims** (doc lines 499, 662-663: which co2_c/ch4/n2o entries = 1 under reddnatveg_nosoil / redd+natveg_nosoil). The CSV is a run-time input NOT present in the worktree (`modules/56_ghg_policy/input/` holds only a `files` manifest; `.csv`/`.cs3` regenerated at run start). All `emis_source` *labels* used in those lines are valid members; only the =1/=0 *values* are unverifiable. Not flagged (cannot read producer; per the R53 "find the producer" rule).
2. **`Depends on: Modules 52, 53, 51`** (doc line 1139, dependency-chain metadata) omits 58-peatland, which the body correctly lists as a `vm_emissions_reg` populator throughout. Internal inconsistency, but this is a condensed top-N centrality summary (footer-class metadata), not the load-bearing interface list (sections 4.2/12.2 are complete and correct). Left as an observation.
3. **Section 4.1 "Provided to" for `vm_carbon_stock`** (doc lines 580-582) lists the pcm carry-forward (M56, M59) and "Reporting modules" but does not explicitly name M52 as a direct equation-RHS reader (`52_carbon/normal_dec17/equations.gms`, the G2 relationship). Not a false claim and the section is not framed as an exhaustive consumer list; M52's role is documented elsewhere in the doc/ecosystem. Left as an observation rather than a confirmed omission (false-positive-averse).

---

## Summary

module_56.md is accurate under the consumer_read lens. All interface-variable reader/populator sets, per-slice carry-forward attribution, M11 cost signs, `.l` postsolve reads (M15, M56, M59), declarations, equation ranges, defaults, and set counts verified against develop. One Minor confabulation: an illustrative pricing example uses three non-existent `emis_source` labels in GAMS syntax (lines 505-508). No Critical/Major bugs.
