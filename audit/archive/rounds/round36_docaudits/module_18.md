# Round 36 Doc Audit: module_18.md (Residues)

**Target**: `<magpie-agent>/modules/module_18.md`
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree) + `config/default.cfg`
**Auditor**: Opus (highest capability), adversarial doc-vs-code
**Date**: 2026-05-30

---

## Overall Verdict: SIGNIFICANT ERRORS (on consumer/interface attribution); equation core is ACCURATE

The equation formulas, set definitions, realization names, default realization, line counts, and most inbound dependencies are verified correct. The errors are concentrated in **interface-variable CONSUMER SETS** — exactly the R20-anchor failure class (wrong consumer set = Critical-prone). The doc:
1. Attributes the `vm_prod_reg(i,kres)` (residue) slice to 6 modules that actually read the `kcr`/`kap`/`kli_rum` slices (Module 17's product, not Module 18's).
2. Mislabels two genuine M50-consumed interface variables (`vm_res_biomass_ag`, `vm_res_biomass_bg`) as "Internal".
3. Omits Module 51 as a consumer of `vm_res_recycling("nr")`, and falsely attributes a P/K-slice consumer to Module 50 (no module reads the P/K slice).
4. Lists Module 57 as a downstream GHG consumer (M57 reads no M18 variable; should be M51 + M53).
5. One attribute imprecision (M51 reads `"dm"` not `"nr"` slice of `vm_res_ag_burn`).

---

## Verified Claims (correct — high confidence)

- **Default realization** `flexreg_apr16` — confirmed `config/default.cfg:622` (`cfg$gms$residues <- "flexreg_apr16"`). Three realizations `flexcluster_jul23`, `flexreg_apr16`, `off` — confirmed `ls`.
- **Line counts** all exact: declarations 58, equations 124, input 51, sets 40, presolve 10, preloop 9, realization 37, scaling 14; flexcluster declarations 76, equations 145.
- **Equation count**: flexreg 9 equations (`grep -cE "^ q18_"` = 9), flexcluster 12 (= 9). Doc "9 → 12" correct.
- **All 9 equation formulas** copied verbatim and match `flexreg_apr16/equations.gms:14-119`. q18_prod_res_ag_reg (14-19), q18_prod_res_bg_reg (24-28), q18_res_field_balance (38-43), q18_res_field_burn (52-57), q18_translate (70-73), q18_prod_res_reg (78-81), q18_res_recycling_nr (90-96), q18_res_recycling_pk (104-110), q18_cost_prod_res (116-119). All accurate.
- **Sets**: `dm_nr = {dm,nr,c}` (sets.gms:11-12 ✓), `pk18 = {p,k}` (sets.gms:14-15 ✓), `nonused18 = {sunflower,oilpalm,foddr,begr,betr}` (sets.gms:23-24 ✓), `kres_kcr` mapping (sets.gms:28-34 ✓), `burn_scen18 = {constant,phaseout}` ✓.
- **presolve.gms:8** `v18_res_ag_removal.fx(i,nonused18,attributes)=0;` ✓. **preloop.gms:9** burn-scenario assignment ✓. **scaling.gms:8** `vm_cost_prod_kres.scale(i,kres)=1e3;` ✓ (rest commented out ✓).
- **Default burn switch** `c18_burn_scen = phaseout` (input.gms:8) ✓.
- **Burn shares** 15% developed / 25% developing, 2050 → 10%/0% — match equations.gms:47-50 comment ✓.
- **Inbound deps**: `vm_area(j,kcr,w)`←M30 (declarations.gms:18/21 ✓), `vm_prod_reg(i,kcr)`←M17 ✓, `im_development_state(t_all,i)`←M09 (aug17/declarations.gms:32 ✓), `fm_attributes`←core ✓.
- **`vm_cost_prod_kres`→M11**: `11_costs/default/equations.gms:16` `sum(kres,vm_cost_prod_kres(i2,kres))` ✓.
- **`vm_res_ag_burn`→M51,M53**: M51 rescaled_jan21:52, M53 ipcc2006_aug22:72 — both genuine consumers, correct line numbers ✓ (attribute caveat below).
- **`vm_prod_reg(i,kres)`→M21**: M21 default `selfsuff_reduced` reads it via `k_notrade` (which includes res_cereals/res_fibrous/res_nonfibrous, sets.gms:12) at equations.gms:19 ✓. M21 IS a genuine kres consumer.
- **flexcluster_jul23 summary**: 3 added equations (q18_prod_res_ag_clust, q18_clust_field_constraint, q18_regional_removals) and the new variables (v18_res_biomass_ag_clust, v18_res_ag_removal at j, v18_res_ag_removal_reg) all match flexcluster_jul23/equations.gms + declarations.gms ✓.
- **`f18_fac_req_kres` unit subtlety**: docstring "USD17MER per tDM" (input.gms:44) vs equation × `fm_attributes("wm",kres)` — doc's nuance note is correct ✓.

---

## ADVISORY RESOLUTION (pre-run checker)

> "Verify q18_* residue equations and the vm_res_* / residue consumer sets with BOTH 'name(' AND 'name.' greps + positive control."

**Resolved**: The q18_* equation formulas and the M18-side reads of `vm_area` (equations.gms:17) are CORRECT. `vm_area.` solution-level reads exist elsewhere (M32 presolve) but NOT relevant to M18's documented use. The ERRORS are in the **consumer sets** of M18's OUTPUT variables (`vm_prod_reg(kres)`, `vm_res_recycling`, `vm_res_biomass_ag/bg`), not in the equations. Confirmed via `vm_*(` AND `vm_*.` greps + `grep -c` positive controls + per-module positive-control scans.

---

## Bugs Found

### BUG-18-1 (Critical) — `vm_prod_reg(i,kres)` consumer set conflates residue slice with crop/livestock slices
- **Class**: 15 (latent doc error / wrong consumer set) — R20 anchor
- **Trigger**: "module doc cited [variable] as having [wrong] consumers" (R20 Critical anchor); MANDATE 13 + 17.
- **doc_line**: module_18.md:223 and module_18.md:406
- **Claim**: "`vm_prod_reg(i,kres)` is consumed by Module 21 (Trade) and Module 16 (Demand), Module 20 (Processing; ...:41), Module 38 (Factor Costs; ...:16), Module 50 (Nr Soil Budget; ...:39), Module 70 (Livestock; ...:18), Module 71 (Disagg Lvst; ...:37)."
- **Reality**: Of the 7 listed modules, only **M21** reads the `kres` (residue) slice. The cited lines for M20/M38/M50/M70/M71 read OTHER slices of the shared `vm_prod_reg` symbol — all of which are Module 17's product, not Module 18's residues:
  - M20 substitution_may21:41 → `vm_prod_reg(i2,"cottn_pro")` (a `kcr` crop)
  - M38 sticky_feb18:16 → `sum(kcr,vm_prod_reg(i2,kcr) ...)` (`kcr` slice)
  - M50 macceff_aug22:39 → `vm_prod_reg(i2,kcr)` (`kcr` slice)
  - M70 fbask_jan16:18 → `vm_prod_reg(i2,kap)` (`kap` animal products)
  - M71 foragebased_jul23:37 → `vm_prod_reg(i2,kli_rum)` (`kli_rum` ruminants)
  - M16 sector_may15:79 → `vm_prod_reg(i2,kcr)` (`kcr` seed share); residues handled via `vm_supply` (q16_supply_residues:51-58), which does NOT read `vm_prod_reg(kres)`.
  `kres = {res_cereals,res_fibrous,res_nonfibrous}` (16_demand/sector_may15/sets.gms:13-14) is disjoint from `kcr` (14_yields/managementcalib_aug19/sets.gms:23-26) and from `kap`/`kli`. The doc itself notes the symbol is shared (line 410) but then attributes the crop-slice consumers to the residue slice.
- **file_evidence**: `modules/21_trade/selfsuff_reduced/equations.gms:19` (only true kres consumer); `modules/20_processing/substitution_may21/equations.gms:41`, `modules/38_factor_costs/sticky_feb18/equations.gms:16`, `modules/50_nr_soil_budget/macceff_aug22/equations.gms:39`, `modules/70_livestock/fbask_jan16/equations.gms:18`, `modules/71_disagg_lvst/foragebased_jul23/equations.gms:37` (all read non-kres slices)
- **verify_cmd**: `rg -ln 'vm_prod_reg' /tmp/magpie_develop_ro/modules/ --glob '*.gms'` then read each cited line via `sed -n`. Slice sets confirmed via Read of `16_demand/sector_may15/sets.gms:13-14`, `14_yields/managementcalib_aug19/sets.gms:23-26`, `21_trade/selfsuff_reduced/sets.gms:11-12`.
- **confirmed**: true
- **proposed_fix**: Replace the "Used By" cell (line 406) and line 223 consumer prose with: residue (`kres`) slice of `vm_prod_reg` is read directly only by **Module 21 (Trade)** via the `k_notrade` balance (`modules/21_trade/selfsuff_reduced/equations.gms:19`; `k_notrade` includes the three residue groups, `sets.gms:12`). Module 16 (Demand) is the demand-side counterpart but reads `vm_dem_*`/writes `vm_supply(i2,kres)` (`sector_may15/equations.gms:51-58`); it does NOT read `vm_prod_reg(kres)`. Modules 20/38/50/70/71 read the `kcr`/`kap`/`kli_rum` slices (Module 17's crop/livestock production), NOT the residue slice — remove them from the residue-slice consumer list.

### BUG-18-2 (Critical) — `vm_res_biomass_ag` and `vm_res_biomass_bg` mislabeled "Internal"; both consumed by Module 50
- **Class**: 15 (latent doc error / wrong consumer set)
- **Trigger**: R20 Critical anchor (doc gives wrong consumer set — user editing the variable would not expect M50 to break); MANDATE 13.
- **doc_line**: module_18.md:401-402
- **Claim**: line 401 `vm_res_biomass_ag` "Used By: Internal (field balance, burning, BG biomass)"; line 402 `vm_res_biomass_bg` "Used By: Internal (N recycling)".
- **Reality**: Both are `vm_`-prefixed interface variables (declarations.gms:11-12) and BOTH are read externally by **Module 50** (`q50_nr_withdrawals`): residue N counts toward crop N withdrawals. `vm_res_biomass_ag(i2,kcr,"nr")` at macceff_aug22:40 and `vm_res_biomass_bg(i2,kcr,"nr")` at macceff_aug22:41. M50 default realization confirmed `macceff_aug22` (`config/default.cfg:1479`).
- **file_evidence**: `modules/50_nr_soil_budget/macceff_aug22/equations.gms:40` (ag) and `:41` (bg)
- **verify_cmd**: `grep -rn 'vm_res_biomass_ag' /tmp/magpie_develop_ro/modules/ --include='*.gms' | grep -v 18_residues | grep -v 'ov_\|oq_'` → `50_nr_soil_budget/macceff_aug22/equations.gms:40`; same for `_bg` → `:41`. Positive control via `grep -c` confirmed grep works.
- **confirmed**: true
- **proposed_fix**: Change line 401 "Used By" to: "Module 50 (Nr Soil Budget — `q50_nr_withdrawals`, `macceff_aug22/equations.gms:40`) + Internal (field balance, burning, BG biomass)". Change line 402 to: "Module 50 (Nr Soil Budget — `q50_nr_withdrawals`, `macceff_aug22/equations.gms:41`) + Internal (N recycling within M18)." Also add M50 as a consumer of these in the Downstream Dependencies and Key Dependencies sections.

### BUG-18-3 (Major) — `vm_res_recycling` consumer set: M51 omitted; P/K slice falsely attributed to M50
- **Class**: 15 (latent doc error / wrong consumer set)
- **Trigger**: Major — consumer-set error misleads about behavior; tie-breaker keeps it below Critical because the N-slice→M50 attribution (the dominant path) is correct and the missed M51 is an additive omission. (R20 anchor would push Critical for the full-set error; downgraded one tier per §1 tie-breaker since half the set is right and harm is "miss one module / wrong target for an unused slice" rather than "edit wrong file".)
- **doc_line**: module_18.md:404 (and 248, 272, 482-483)
- **Claim**: line 404 `vm_res_recycling` "Used By: Module 50 (nitrogen and P/K budgets)"; line 272 `vm_res_recycling(i,pk18)` → "Module 50 (nutrient budget consumers)"; lines 482-483 list M50 for P/K.
- **Reality**: `vm_res_recycling` is read externally by exactly two modules, both on the `"nr"` slice: **M50** macceff_aug22:24 and **M51** rescaled_jan21:45 (`q51_emissions_resid`, residue N emission factor). **No module reads the P/K (`pk18`) slice** — `q18_res_recycling_pk` populates `vm_res_recycling(i,pk18)` but it has zero downstream consumers (M54 phosphorus is `off` by default and contains no `vm_res_recycling` reference). So: (a) M51 omitted; (b) "P/K budgets" in M50 is a phantom.
- **file_evidence**: `modules/51_nitrogen/rescaled_jan21/equations.gms:45` (omitted nr consumer); `modules/50_nr_soil_budget/macceff_aug22/equations.gms:24` (nr only, no pk18); no file reads the pk18 slice.
- **verify_cmd**: `grep -rn 'vm_res_recycling' /tmp/magpie_develop_ro/modules/ --include='*.gms' | grep -v 18_residues | grep -vi 'ov_res_recycling'` → only `51_nitrogen/...:45` and `50_nr_soil_budget/...:24`, both `(i2,"nr")`. M54 scan (`ls 54_phosphorus/` = module.gms, off) confirms no pk18 reader.
- **confirmed**: true
- **proposed_fix**: line 404 "Used By" → "Module 50 (`macceff_aug22/equations.gms:24`) and Module 51 (`rescaled_jan21/equations.gms:45`) — both read the `nr` slice only. The P/K slice (`vm_res_recycling(i,pk18)`) is computed by `q18_res_recycling_pk` but currently has no downstream consumer (M54 phosphorus is `off` by default)." Update lines 272 and 479-483 accordingly: add M51 under the N-recycling consumer; mark the P/K slice as populated-but-unconsumed rather than attributing it to M50.

### BUG-18-4 (Minor) — "Participates In / Provides to" lists Module 57 (no M18 variable reaches M57)
- **Class**: 15 (wrong consumer attribution)
- **Trigger**: Minor — appears only in the low-stakes "Dependency Chains" summary and is internally contradicted by the doc's own correct Downstream section (485-489 lists M51+M53). A careful reader cross-checking would catch it; harm is bounded. (Tie-breaker: not Major because it is not in the load-bearing interface table and the correct info is present elsewhere in the same doc.)
- **doc_line**: module_18.md:603
- **Claim**: "Provides to: Modules 11 (costs), 16 (demand), 21 (trade), 50 (N and P/K budgets), 57 (GHG emissions)"
- **Reality**: Module 57 (maccs, default `on_aug22`) reads NO M18 interface variable. Residue-burning GHG emissions flow to **M51** (nitrogen, N2O/NOx) and **M53** (methane, CH4). The doc's own lines 485-489 correctly state M51 + M53.
- **file_evidence**: scan of `modules/57_maccs/` returns no reference to any of vm_res_ag_burn / vm_res_recycling / vm_res_biomass_ag / vm_res_biomass_bg / vm_prod_reg / vm_cost_prod_kres; M51 rescaled_jan21:52 and M53 ipcc2006_aug22:72 are the actual burn-emission consumers.
- **verify_cmd**: per-variable `grep -rn "$v" /tmp/magpie_develop_ro/modules/57_maccs/ --include='*.gms' | grep -v 'ov_\|oq_'` for all 6 M18 outputs → empty; positive control `grep -rln 'vm_btm_reg|vm_maccs_costs|im_maccs' 57_maccs/` → 5 files (grep works).
- **confirmed**: true
- **proposed_fix**: line 603 → replace "57 (GHG emissions)" with "51 (N emissions from residue burning), 53 (CH4 from residue burning)". (Aligns the summary with the doc's own correct lines 403, 485-489.)

### BUG-18-5 (Minor) — M51 consumer attribute: doc says `vm_res_ag_burn(i,kcr,"nr")`, code uses `"dm"`
- **Class**: 12 (content-level citation mismatch — attribute)
- **Trigger**: Minor — line number, module, and variable are all correct; only the attribute slice in the parenthetical is wrong, and it does not change the module-attribution or break a code edit.
- **doc_line**: module_18.md:486
- **Claim**: "Module 51 (Nitrogen Emissions): `vm_res_ag_burn(i, kcr, "nr")` - N from burned residues (used at `modules/51_nitrogen/rescaled_jan21/equations.gms:52`)"
- **Reality**: `51_nitrogen/rescaled_jan21/equations.gms:52` reads `sum(kcr, vm_res_ag_burn(i2,kcr,"dm")) * f51_ef_resid_burn(...)` — it uses the **dry-matter** (`"dm"`) slice times an emission factor, not the `"nr"` slice. (N emissions are derived from DM burned × EF, not from the nr attribute of the burned residue.)
- **file_evidence**: `modules/51_nitrogen/rescaled_jan21/equations.gms:52`
- **verify_cmd**: `sed -n '48,56p' /tmp/magpie_develop_ro/modules/51_nitrogen/rescaled_jan21/equations.gms` → shows `vm_res_ag_burn(i2,kcr,"dm")`.
- **confirmed**: true
- **proposed_fix**: line 486 → `vm_res_ag_burn(i, kcr, "dm")` and reword to "DM of burned residues × emission factor `f51_ef_resid_burn`". (The doc's interface table line 403 already correctly says `(i, kcr, attributes)`; only line 486's `"nr"` is wrong.)

---

## Deferred (not code-verifiable / out of scope — NO edit)

- Whether `kli_rum` is exactly `{livst_rum}` vs a broader ruminant set: not load-bearing for the BUG-18-1 verdict (any non-kres slice suffices); the M71 read is `vm_prod_reg(i2,kli_rum)` regardless, disjoint from kres.
- The flexcluster_jul23 narrative micro-structure (it also renames q18_prod_res_bg_reg→q18_prod_res_bg_clust and moves q18_translate to j2) is more than "3 cluster equations added", but the doc explicitly labels the section a summary and the net count (12) + the 3 named additions are correct. No edit; informational only.
- Prose/advice (Limitations, Modification Safety, Key Innovation) — not code-checkable claims; spot-checks (no-residue-trade at equations.gms:121-122; fixed CGF; regional field balance) are consistent with code.
- magpie4 / report.mif provenance for residue variables — out of scope for this GAMS-side audit.

---

## Summary

Equation core, sets, defaults, realization names, and line counts are accurate. Five consumer/interface-attribution bugs: 2 Critical (vm_prod_reg(kres) attributed to 6 wrong modules incl. the crop/livestock slices; vm_res_biomass_ag/bg mislabeled "Internal" though M50 reads them), 1 Major (vm_res_recycling: M51 omitted + phantom P/K consumer in M50), 2 Minor (M57 phantom in dependency summary; M51 `"nr"`-vs-`"dm"` attribute). Root cause: the shared `vm_prod_reg` symbol's kres slice was conflated with the kcr/kap slices, and external M50 reads of the biomass/recycling variables were not grepped.
