# Round 55 depth audit — module_56.md — lens: declare_populate

**Target:** `modules/module_56.md` (Module 56 GHG Policy, realization `price_aug22`)
**Ground truth:** `/private/tmp/magpie_develop_ro` (develop worktree); config `config/default.cfg`; role map `audit/integrated/depth_rolemap.json`.
**Verdict:** MOSTLY ACCURATE (2 Minor bugs). The declare/populate spine — the exact area the G2 anchor guards — is clean.

---

## Summary

The doc is highly accurate on the declare/populate lens. Every interface-variable declaration citation, populator set, and equation-formula attribution I checked resolves correctly against develop. Two Minor discrepancies found (a wrong index-set name in one parameter signature; one omitted source in the default-policy N2O coverage enumeration). No Critical/Major bugs.

---

## Verified correct (load-bearing declare/populate claims)

- **Declaration sites** (all exact): `vm_carbon_stock` positive var `declarations.gms:34`; `vm_emission_costs` `declarations.gms:39`; `vm_reward_cdr_aff` `declarations.gms:43`; `im_pollutant_prices` `declarations.gms:9`; `p56_c_price_aff` `declarations.gms:11`. All match doc.
- **`vm_carbon_stock` populators** = 29, 31, 32, 34, 35, 59 (doc line 584/1039-1046). Role map `populated_by [29,31,32,34,35,56,59]` — the extra "56" is the declaring module's postsolve `.l` read (`postsolve.gms:8`, carries `ag_pools` into `pcm_carbon_stock`), not a value population; doc's exclusion of 56 as populator is correct. M30 populates the separate `vm_carbon_stock_croparea` (role map `populated_by [30]`), which M29 folds in — doc's nuance is correct and more precise than the model's own `module.gms:18-19` prose (which loosely says "30_crop").
- **M59 soilc carry-forward**: `modules/59_som/cellpool_jan23/postsolve.gms:13` = `pcm_carbon_stock(j,land,"soilc",stockType) = vm_carbon_stock.l(...)`. Confirmed. Commit `931db85c4` ("59_som: carry soil pcm_carbon_stock forward each timestep") exists and touched both SOM postsolves. Doc line 581 accurate.
- **`vm_emissions_reg` populators** = 51, 52, 53, 58 (doc). Confirmed via LHS grep: M52 `52_carbon/normal_dec17/equations.gms:17`, M53 `53_methane/ipcc2006_aug22/equations.gms:22,49,60,71`, M58 `58_peatland/v2/equations.gms:92`, M51 nitrogen. **M57 only reads, does not populate** (role map `read_by [56,57]`, not in populated_by) — doc line 1026 correct.
- **`vm_emission_costs` M15 reader**: `modules/15_food/anthro_iso_jun22/intersolve.gms:23` reads `vm_emission_costs.l(i)` for tax recycling (doc line 566). The role-map `populated_by [15,...]` is the `scaling.gms:22` `.scale` assignment, not a value populate; doc correctly says M15 *reads* `.l`. Default realization `anthro_iso_jun22` confirmed (`default.cfg:410`).
- **`im_pollutant_prices` M57 consumer**: `modules/57_maccs/on_aug22/preloop.gms:24-25` (doc line 679). Confirmed; default realization `on_aug22`.
- **`vm_cdr_aff`**: declared_in 32, populated_by 32, read by 56 at `equations.gms:77`. Correct.
- **All 7 equations** verbatim-match `equations.gms:15-79`; equation count 7 confirmed in `declarations.gms:24-30`. CDR-reward formula (annuity, discount `(1+r)^(ac.off*5)`, buffer `(1-s56_buffer_aff)`, fader `p56_fader_cpriceaff`) matches. Section 2.2 "reads `vm_carbon_stock` directly, parallel to M52" is correct (both read it independently — the R51/MANDATE-21 correction is honored).
- **Preloop stage citations** (`preloop.gms:35-45,50-51,53-63,65-67,69-74,76-82,84-91,93-123`) all resolve; age-class shift `preloop.gms:118` correct.
- **All defaults** (config + input.gms line numbers 65-71,75): `c56_pollutant_prices=R34M410-SSP2-NPi2025`, `c56_emis_policy=reddnatveg_nosoil`, `c56_carbon_stock_pricing=actualNoAcEst`, `c56_cprice_aff=secdforest_vegc`, `s56_c_price_induced_aff=1`, `s56_buffer_aff=0.5`, `s56_c_price_exp_aff=50`, `s56_minimum_cprice=3.67`, `s56_limit_ch4_n2o_price=4920`, `s56_cprice_red_factor=1`, `s56_ghgprice_devstate_scaling=0`, `s56_ghgprice_fader=0`. All correct.
- **CSV dimensions**: `f56_emis_policy` = 44 policies × 16 pollutants × 31 emission sources — all three counts confirmed. `reddnatveg_nosoil` CO2 (primforest/secdforest/other vegc+litc + peatland) and CH4 (awms, resid_burn, rice, ent_ferm, peatland) lists match the CSV exactly. `redd+natveg_nosoil` adds forestry_vegc+litc — confirmed. (CSV is a run-time input, not git-tracked in develop; verified against the working-tree input copy per the R53 regenerated-input caveat.)
- **LOC 709** = sum of `price_aug22/*.gms` — exact.

---

## Bugs

### Bug 56-DP-1 — wrong index set in `f56_emis_policy` signature (Minor)
- **Class:** set_membership
- **Doc:** module_56.md:629 — "**f56_emis_policy(scen56,pollutants,emis_source)**: Emission policy matrix (0/1)"
- **Reality:** declared `table f56_emis_policy(scen56,pollutants_all,emis_source)` — indexed over `pollutants_all` (16 members, `sets.gms:171`), **not** `pollutants` (the 7-member taxable subset, `sets.gms:187`).
- **Evidence:** `modules/56_ghg_policy/price_aug22/input.gms:113`; contrast `input.gms:93` where `f56_pollutant_prices(...,pollutants,ghgscen56)` correctly uses `pollutants`.
- **Note:** Internally the doc's own dimension count at line 494 ("16 pollutants") is correct — it is only the signature that names the subset. A reader could infer the matrix covers only 7 taxable pollutants. Minor (tie-breaker down; count corrects it two paragraphs earlier).
- **Fix:** change `pollutants` → `pollutants_all` in the line-629 signature.

### Bug 56-DP-2 — `peatland` omitted from reddnatveg_nosoil N2O coverage (Minor)
- **Class:** set_membership
- **Doc:** module_56.md:662 (and :499, :663) — N2O for `reddnatveg_nosoil`: "(ag: inorg_fert, man_crop, awms, resid, resid_burn, man_past, som, rice + indirect N)" — omits `peatland`.
- **Reality:** `f56_emis_policy("reddnatveg_nosoil","n2o_n_direct","peatland") = 1` — peatland N2O IS priced under the default policy. The doc includes `peatland` in the CH4 and CO2 lists under the same "ag:" convention but drops it from N2O — an internal-convention inconsistency / oversight.
- **Evidence:** `modules/56_ghg_policy/input/f56_emis_policy.csv` (run-time input; working-tree copy) — reddnatveg_nosoil / n2o_n_direct row: peatland column = 1.
- **Note:** Low harm — peatland's coverage is conveyed by the correct CO2/CH4 entries; only the specific gas-source cell is missing. Minor.
- **Fix:** add `peatland` to the N2O source lists at lines 499, 662, 663 (or drop it from CH4 for consistency, matching whatever "ag:" scoping is intended — but code prices peatland N2O, so adding it is the faithful fix).

---

## Deferred (noted, not flagged — no edit proposed)

- **Line 759 vs 961 tension (mechanism, negligible magnitude):** Section 8.1 says 1995/historic emission cost is "zero because GHG prices are zeroed for years <= sm_fix_SSP2 (preloop.gms:70)". But `preloop.gms:74` (min-cprice floor, no year condition) runs *after* the line-70 zeroing and re-floors `co2_c` to 3.67 for all years; policy-covered historic LULUCF CO2 is therefore priced at ~3.67 USD/tC (~$1/tCO2), not exactly 0. Section 11.1 (line 961) itself acknowledges the "unconditional" 3.67 floor, so the doc is internally aware; practical magnitude negligible. Not flagged (defensible as ~zero; would risk over-flagging an interpretive nuance).
- **Line 110 `emis_oneoff` gloss:** described as "One-time emission sources (deforestation, forest degradation)"; the set actually contains ALL land carbon-pool sources (crop/past/forestry/primforest/secdforest/urban/other × vegc/litc/soilc — `core/sets.gms:314-320`). Illustrative "e.g." framing throughout; mechanism (carbon-stock-difference, one-off treatment) correctly described. Under-description, not a hard bug.
- **Section 5.1 approximate price values** (~$0/$300/tC etc.) are explicitly labelled illustrative; not code-checkable.
- **Centrality "Rank #3", "Provides to 13 modules", circular-dependency chain (lines 1136-1146):** agent-internal metrics / cross_module doc references; outside this lens's code-checkable scope.
- **Limitation 1** ("agents cannot anticipate future carbon price increases"): true for the general recursive-dynamic solver but in tension with the afforestation price-foresight mechanism the doc documents elsewhere; not a code-vs-doc contradiction per se.
