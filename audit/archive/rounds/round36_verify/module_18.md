# Round 36 Adversarial Verification — module_18.md (Residues)

Verifier model: Opus 4.8 (1M). Ground truth: `/tmp/magpie_develop_ro` @ HEAD `ee98739fd`.
Default realizations confirmed in `config/default.cfg`:
- residues=flexreg_apr16, production=flexreg_apr16 (612), trade=selfsuff_reduced (650),
  processing=substitution_may21 (633), factor_costs=sticky_feb18 (1235),
  nr_soil_budget=macceff_aug22 (1479), nitrogen=rescaled_jan21 (1550),
  methane=ipcc2006_aug22 (1583), phosphorus=off (1587, M54 only has `off/`),
  maccs=on_aug22 (1822), livestock=fbask_jan16 (2146), disagg_lvst=foragebased_jul23 (2200),
  demand=sector_may15 (608).

## Foundational set facts (canonical sources read, not grepped-and-trusted)

- `modules/16_demand/sector_may15/sets.gms:10-16`:
  - `ksd(kall) = {oils,oilcakes,sugar,molasses,alcohol,ethanol,distillers_grain,brans,scp,fibres}`
  - `kres(kall) = {res_cereals, res_fibrous, res_nonfibrous}`
  - `kap(k)` animal products
- `modules/18_residues/flexreg_apr16/sets.gms:14-34`:
  - `pk18(npk) = {p,k}` (confirms doc:270)
  - `kres_kcr(kres,kcr)` maps residue groups FROM crops `{tece,maiz,trce,rice_pro,soybean,rapeseed,groundnut,puls_pro,sugr_beet,sugr_cane,cottn_pro,potato,cassav_sp,others}`
  - => **kres and kcr are DISJOINT** (residue groups vs source crops). kap/kli also disjoint from kres.
- `modules/21_trade/selfsuff_reduced/sets.gms:11-12` (DEFAULT trade realization — read in full):
  - `k_notrade(kall) = {oilpalm, foddr, pasture, res_cereals, res_fibrous, res_nonfibrous, begr, betr}`
  - => `k_notrade ⊇ kres`. So a read of `vm_prod_reg(i,k_notrade)` IS a read of the residue slice.
  - `k_trade` (lines 17-21) excludes residues.
  - NOTE: the non-default `selfsuff_reduced_bilateral22` realization renames this set to `n(kall)`; an early rg pass conflated the two dirs — resolved by reading the default-realization file directly.

## vm_prod_reg complete consumer scan (both forms)

`grep -rln 'vm_prod_reg' modules/ | grep -vE '17_production|18_residues'` =>
M16, M20, M21(x3 realiz dirs), M38(x2), M50, M70(x2), M71(x2). No other module. No `vm_prod_reg.` attribute reads outside M17/M18 (M16 attribute grep exited 1 = none).

Per-consumer slice (equation-form, default realization, index copied from code):

| Module | File:line | Slice read | Residue (kres)? |
|--------|-----------|-----------|-----------------|
| M16 | sector_may15/equations.gms:79 | `vm_prod_reg(i2,kcr)` (seed demand) | NO (kcr) |
| M20 | substitution_may21/equations.gms:41,62,120 | `"cottn_pro"`, `ksd`, `"scp"` | NO |
| M21 | selfsuff_reduced/equations.gms:13,32,40,65,72 | `k_trade` | NO |
| M21 | selfsuff_reduced/equations.gms:19 | `k_notrade` (⊇ kres) | **YES** |
| M38 | sticky_feb18/equations.gms:16 | `sum(kcr, vm_prod_reg(i2,kcr))` | NO (kcr) |
| M50 | macceff_aug22/equations.gms:39,85 | `kcr`, `"pasture"` | NO |
| M70 | fbask_jan16/equations.gms:18,28,36,60,65,70 | `kap`,`kli_rum`,`kli`,`"fish"` | NO |
| M71 | foragebased_jul23/equations.gms:37,57 | `kli_rum`,`kli_mon` | NO |

Only M21 (line 19, via k_notrade) is a true direct consumer of the kres slice.

---

## BUG-18-1 — UPHELD (consumer-set; phantom members)

Doc lines 223 + 406 claim `vm_prod_reg(kres)` is consumed by all 7 of M16/M20/M21/M38/M50/M70/M71.
Reality (table above): only **M21 (Trade), selfsuff_reduced/equations.gms:19** reads the residue slice (k_notrade ⊇ {res_cereals,res_fibrous,res_nonfibrous}). M20/M38/M50/M70/M71 read disjoint kcr/kap/kli slices of the shared symbol. M16 reads vm_prod_reg(i2,kcr) at line 79 (seed), NOT the kres slice.

Auditor correct to remove M20/38/50/70/71 from the residue-slice consumer list and keep M21 as the true one.

One refinement to the auditor's proposed_fix prose: it says M16 "reads vm_dem_*/writes vm_supply(i2,kres) (sector_may15/equations.gms:51-58), NOT vm_prod_reg(kres)." That is correct about the kres slice, but M16 DOES read `vm_prod_reg(i2,kcr)` at line 79 (q16_seed_demand). The vm_supply(i2,kres) write is at q16_supply_residues, equations.gms:51-58 (reads vm_dem_feed/vm_dem_material/vm_dem_bioen/v16_dem_waste). So M16 is correctly excluded from kres consumers; just note line 79 reads the kcr slice rather than implying M16 never touches vm_prod_reg.

corrected_set: see field below.

## BUG-18-2 — UPHELD (consumer-set; "Internal" mislabel, omitted external consumer M50)

`vm_res_biomass_ag(i,kcr,attributes)` and `vm_res_biomass_bg(i,kcr,dm_nr)` are vm_-prefixed interface vars (flexreg_apr16/declarations.gms:11-12, read in full).
External consumers (both forms):
- `grep -rln 'vm_res_biomass_ag' modules/ | grep -v 18_residues` => only `50_nr_soil_budget/macceff_aug22/equations.gms`
- `grep -rln 'vm_res_biomass_bg' ...` => only macceff_aug22
- attribute-form (`vm_res_biomass_ag.` / `_bg.`) outside M18 => none; positive control found the attribute form INSIDE M18 (flexreg_apr16/postsolve.gms etc.), proving the search works.
Exact lines: `vm_res_biomass_ag(i2,kcr,"nr")` at macceff_aug22:40; `vm_res_biomass_bg(i2,kcr,"nr")` at :41 (q50_nr_withdrawals).
=> Both are NOT internal-only. Doc lines 401-402 "Internal" labels are wrong. Auditor's fix (add M50 @ :40 ag, :41 bg) is correct and exhaustive (M50 is the sole external consumer).

## BUG-18-3 — UPHELD (consumer-set; omitted M51, phantom P/K-budget consumer)

`vm_res_recycling(i,npk)` external consumers (both forms):
- equation-form outside M18: `50_nr_soil_budget/macceff_aug22/equations.gms` and `51_nitrogen/rescaled_jan21/equations.gms` (the M51 `off/not_used.txt` hit is off-realization doc, not a consumer).
- attribute-form outside M18: none.
Slices (index copied from code):
- M50 macceff_aug22:24 — `vm_res_recycling(i2,"nr")` inside q50_nr_inputs (a **nitrogen** budget). nr only.
- M51 rescaled_jan21:45 — `vm_res_recycling(i2,"nr")` * EF. nr only.
pk18/npk/p/k slice: `grep -rn 'vm_res_recycling(i2,pk18)|...(i2,npk)|...(i2,"p")|...(i2,"k")' modules/ | grep -v 18_residues` => NO external read. Positive control with the same syntax on the nr slice DID return M50:24 + M51:45, proving the search is valid. M54 (phosphorus, off) has zero vm_res_recycling refs (count check all-zero; only files: declarations/postsolve/preloop/realization).
=> Doc line 404 "Module 50 (nitrogen and P/K budgets)" is wrong on two counts: (a) M51 omitted; (b) no module reads the P/K slice, so "P/K budgets" is a phantom and M50's read is the nr slice in a nitrogen budget. Doc lines 272 and 479-483 (which split M50 into "Nitrogen Budget" + "Phosphorus/Potassium Budget", both attributing vm_res_recycling) carry the same error. Auditor's fix is correct.

## BUG-18-4 — UPHELD (consumer-set; phantom consumer M57)

Doc line 603 "Provides to: ... 57 (GHG emissions)".
M57 (maccs/on_aug22) references NONE of M18's outputs:
- count of {vm_res_biomass_ag|_bg|vm_res_ag_burn|vm_res_recycling|vm_cost_prod_kres} in 57_maccs/on_aug22/*.gms => all zero.
- vm_prod_reg in 57_maccs => grep exited 1 (none).
- Positive control: `grep vm_` in 57_maccs/on_aug22/equations.gms returns vm_maccs_costs / vm_emissions_reg (proves search dir valid). M57 reads vm_emissions_reg (from emission modules), not M18.
True residue-burn GHG consumers (both forms, exhaustive): vm_res_ag_burn read externally only by M51 (rescaled_jan21:52, N pollutants) and M53 (ipcc2006_aug22:72, CH4) — `sum(kcr, vm_res_ag_burn(i2,kcr,"dm"))`. (off/not_used.txt hits are off-realization docs.) No attribute-form external reads.
Doc's own lines 403 + 485-489 already say M51 + M53 => line 603 "57" is an internal contradiction. Auditor's fix (replace "57 (GHG emissions)" with "51 (N from residue burning), 53 (CH4 from residue burning)") is correct.

## BUG-18-5 — NOT_CONSUMER_SET (passes through unchanged)

bug_class 12 (content-level attribute citation), not a WHICH-modules claim => class_is_consumer_set = false; out of this verifier's mandate. For the record the auditor's evidence reproduces exactly: rescaled_jan21:52 reads `sum(kcr, vm_res_ag_burn(i2,kcr,"dm")) * f51_ef_resid_burn(n_pollutants_direct)` — the **"dm"** slice, not "nr". Module/line/variable all correct; only the doc:486 parenthetical attribute "nr" is wrong. Fixer should apply the auditor's "dm" correction.

---

### Summary
| Bug | class_is_consumer_set | Verdict |
|-----|----------------------|---------|
| 18-1 | true | UPHELD (with prose refinement on M16) |
| 18-2 | true | UPHELD |
| 18-3 | true | UPHELD |
| 18-4 | true | UPHELD |
| 18-5 | false | NOT_CONSUMER_SET |
