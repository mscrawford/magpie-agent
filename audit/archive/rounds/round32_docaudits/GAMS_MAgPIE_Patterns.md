# Doc Audit — reference/GAMS_MAgPIE_Patterns.md (Round 32)

**Auditor**: adversarial doc auditor (Opus)
**Date**: 2026-05-30
**Ground truth**: `/tmp/magpie_develop_ro` @ `ee98739fd` (develop HEAD; `git log` confirmed) + official GAMS docs (gams.com).
**Method**: enumerated load-bearing code-checkable claims (interface var/eq/param names, file:line citations, consumer/populator SETS, realization defaults, set definitions, macro formulas), verified each against code with reliable greps (rg + grep -rn second method + positive controls), and verified GAMS-language claims against gams.com.

---

## Pre-run advisory verdict

> "Most-loaded GAMS reference (R10 scored it 5.0). Verify MAgPIE-convention claims (naming prefixes, module structure, file layout) against develop; verify GAMS-language claims against gams.com."

**CONFIRMED with findings.** GAMS-language claims (singleton `ct` set, `$macro`, `=e=/=l=/=g=`, "equations can't reference loop index t" → use `ct`) are ACCURATE against gams.com (UG_FlowControl confirms equation definitions are illegal inside loops; the `ct` singleton pattern is the correct workaround). Naming-prefix conventions (vm_/pm_/v{N}_/p{N}_/s{N}_/q{N}_/f{N}_/i{N}_/pcm_/m_) and module file layout are ACCURATE. **BUT** the MAgPIE-convention SET-MEANING table (§2.3) and the interface-variable CONSUMER SETS (§3.1, §3.2) contain code-verifiable errors, and two pattern-teaching code blocks (§3.4, §4.6) contain fabricated formulas (one with a nonexistent variable). These are the substantive bugs below.

---

## Verified-correct claims (sample)

- **Default realizations**: land=`landmatrix_dec18` (config:232), yields=`managementcalib_aug19` (config:354), livestock=`fbask_jan16` (config:2146). Module 10 has only `landmatrix_dec18`; module 70 has `fbask_jan16` + `fbask_jan16_sticky`. All correct.
- **§1.4 Module-10 declarations block**: `pm_land_start/pm_land_hist/pcm_land`, `vm_landdiff`, `vm_land/vm_landexpansion/vm_landreduction/vm_cost_land_transition/vm_lu_transitions`, equations `q10_land_area…q10_landdiff` — all match `landmatrix_dec18/declarations.gms` verbatim. R-section `ov_*`/`oq10_*` block matches.
- **§1.6 presolve snippet** (`vm_lu_transitions.fx(...)`, `m_boundfix(vm_land,(j,land),up,1e-6)`): matches `presolve.gms:13-25`. Cited range "lines 10-25" accurate.
- **§6.1 `q10_land_area` citation `…/equations.gms:13-15`**: EXACT match (lines 13-15).
- **§6.2 transition equations**: `q10_transition_to`/`q10_transition_from` FROM/TO algebra matches `equations.gms:19-25` correctly (NOT inverted).
- **§3.2 owners**: `vm_prod`→M17 (`flexreg_apr16/declarations.gms:9`), `vm_carbon_stock`→M56 (`price_aug22/declarations.gms:34`, signature `(j,land,c_pools,stockType)` exact), `vm_cost_glo`→M11 (`default/declarations.gms:9`), `vm_watdem`→M42 (`declarations.gms:29`). All correct. `vm_watdem` Used-By:43 correct (only M42+M43 reference it).
- **§3.3 `fm_carbon_density`**: loaded in M52 `normal_dec17/input.gms:16`, signature `(t_all,j,land,c_pools)` exact. Correct.
- **Macros**: `m_weightedmean` @ `core/macros.gms:16` (formula `(sum(s,x*w)/sum(s,w))$(sum(s,w)>0) + 0$(sum(s,w)<=0)` exact), `m_growth_vegc` @18 (`S + (A-S)*(1-exp(-k*(ac*5)))**m` exact), `m_boundfix` @14, `m_annuity_ord` @25, `m_annuity_due` @31, `m_linear_time_interpol` @79, `m_sigmoid_time_interpol` @86. All correct, including `\` multi-line continuation format.
- **§6.6 `q11_cost_reg`/`q11_cost_glo`**: exist at `11_costs/default/equations.gms:15`/`:10`; the doc's term list is a `+ ...`-elided subset of the real (much longer) sum — acceptable as illustrative.
- **`type` set** `/level,marginal,upper,lower/` (sets.gms) matches §1.5/§2.2.
- **Set members** `land /crop,past,forestry,primforest,secdforest,urban,other/`, `kli(kap)`="Livestock products", `kap(k)`="Animal products" — all correct.
- **Scalar examples** `s10_fix_transition/s70_feed_waste/s10_timestep/s10_scenario/s70_feed_factor` do NOT exist in code (positive control: module 70 has s70_subst_functional_form etc.; module 10 has no s10_ scalars). These are framed under "**Example**" headers and the key two are in the doc's `check-gams-vars: allow` allowlist (line 3) → legitimate illustrative placeholders, NOT bugs.

---

## Bugs Found

### BUG-01 (Major, tier_uncertainty) — §2.3 `kve` set meaning wrong
- **Class**: 12 (content-level mismatch) / set-member-label.
- **Doc** (GAMS_MAgPIE_Patterns:326): `| kve | Veg etables/fruits |`.
- **Reality**: `kve(k) Land-use activities` — its member list is `tece…others, foddr, pasture, cottn_pro, begr, betr` (crops + **pasture** + bioenergy grasses + fodder). It is the land-use/cropping-activity superset, NOT the food category "vegetables and fruits".
- **Evidence**: `modules/14_yields/managementcalib_aug19/sets.gms:18`. Repo-wide there is exactly ONE `kve` definition (grep confirmed, no global `kve`).
- **verify_cmd**: `grep -rhn 'kve' /tmp/magpie_develop_ro/modules/*/*/sets.gms /tmp/magpie_develop_ro/core/sets.gms | grep -iE 'kve\('` → `18:  kve(k) Land-use activities`.
- **Harm**: a coder summing over `kve` expecting produce would instead include pasture/bioenergy/fodder. Right table slot, wrong semantics → Major. (tie-breaker down from any higher read; tier_uncertainty because it's a reference-table entry a careful reader might cross-check.)
- **Fix**: change description to `Land-use activities (crops + pasture + bioenergy/fodder)`.

### BUG-02 (Major, tier_uncertainty) — §2.3 `kfo` set meaning wrong
- **Class**: 12 (content-level mismatch) / set-member-label.
- **Doc** (GAMS_MAgPIE_Patterns:327): `| kfo | Forestry products |`.
- **Reality**: `kfo(kall) All products in the sectoral version` — it is the FOOD-relevant product set (parent of `kfo_pp`/`kfo_ap`/`kfo_st`/`kfo_lp` etc.), defined in the food module. Forestry products are the separate set `kforestry(k)` (in `16_demand/sector_may15/sets.gms:27`), NOT `kfo`.
- **Evidence**: `modules/15_food/anthro_iso_jun22/sets.gms:77` (`kfo(kall) All products…`); `modules/16_demand/sector_may15/sets.gms:27` (`kforestry(k) forestry products`). Repo-wide exactly ONE `kfo(kall)` definition.
- **verify_cmd**: `grep -rhn 'kfo' .../sets.gms | grep -iE 'kfo\(kall\)'` → `77:   kfo(kall) All products in the sectoral version`; separately `kforestry(k) forestry products`.
- **Harm**: `kfo` mislabeled as forestry is badly wrong — a coder writing a forestry sum over `kfo` would sum all food products. Major (borders Critical for the inverted-domain mislabel; tie-breaker → Major; tier_uncertainty set).
- **Fix**: change description to `Food-relevant products (all products considered as food; defined in module 15)`. If a "forestry products" row is wanted, use set name `kforestry`.

### BUG-03 (Major) — §3.1 `vm_land` "Used by" set lists phantom consumers (14, 17, 52) and omits real ones
- **Class**: 15 (latent doc error / consumer-set) — R20 anchor (wrong consumer set).
- **Doc** (GAMS_MAgPIE_Patterns:368): "**Used by**: Modules 14 (Yields), 17 (Production), 30 (Croparea), 31 (Pasture), 32 (Forestry), 35 (Natural vegetation), 52 (Carbon), etc."
- **Reality**: Modules **14, 17, and 52 do NOT reference `vm_land` at all** (they read `vm_area`/`vm_yld` and `vm_carbon_stock`/`fm_carbon_density` respectively — MANDATE-17 transitive-not-direct). Actual direct consumers of `vm_land` (equations/presolve): **29, 30, 31, 32, 34, 35, 50, 58, 59** (plus owner 10). Doc omits 29, 34, 50, 58, 59.
- **Evidence**: `rg 'vm_land\b'` in `14_yields/*/*.gms`, `17_production/*/*.gms`, `52_carbon/*/*.gms` → EMPTY (all three). Positive controls in the same dirs: `vm_yld` present in M14, `vm_prod` in M17, `vm_carbon_stock` in M52 (grep works). Second method `grep -rn 'vm_land'` in all three dirs → EMPTY. Real-consumer enumeration: `rg -l 'vm_land\b' modules/*/*/equations.gms modules/*/*/presolve.gms` → 10,29,30,31,32,34,35,50,58,59.
- **verify_cmd**: `rg -n 'vm_land\b' /tmp/magpie_develop_ro/modules/52_carbon/*/*.gms` → (empty); `rg -ln 'vm_carbon_stock\b' /tmp/magpie_develop_ro/modules/52_carbon/*/*.gms` → `…/normal_dec17/equations.gms` (positive control passes).
- **Harm**: modification-impact reasoning on Module 10 is misdirected — user checks 14/17/52 (false positives) and misses 29/34/50/58/59 (false negatives). R20 anchor makes wrong consumer sets Critical-prone; the "etc." hedge + pedagogical "What are Interface Variables?" framing pull it to Major.
- **Fix**: replace with "**Used by**: Modules 29 (cropland), 30 (croparea), 31 (pasture), 32 (forestry), 34 (urban), 35 (natural vegetation), 50 (nitrogen budget), 58 (peatland), 59 (SOM). (Yields/production/carbon read `vm_area`/`vm_yld`/`vm_carbon_stock`, not `vm_land` directly.)"

### BUG-04 (Major) — §3.2 `vm_prod(j,k)` "Used By: 20, 21, 70" lists consumers of the SIBLING `vm_prod_reg`, not `vm_prod`
- **Class**: 12/15 — consumer-set / cell-vs-regional conflation.
- **Doc** (GAMS_MAgPIE_Patterns:375): `| vm_prod(j,k) | 17 | 20, 21, 70 | Production by product |`.
- **Reality**: Modules **20, 21, 70 do NOT reference `vm_prod`** (cell-level); they consume `vm_prod_reg` (regional). Actual direct consumers of `vm_prod(j,k)`: **18, 30, 31, 38, 40, 42, 71, 73** (plus owner 17).
- **Evidence**: `rg 'vm_prod\b'` (word boundary) in `20_processing/*/*.gms`, `21_trade/*/*.gms`, `70_livestock/*/*.gms` → EMPTY. Positive control: `vm_prod_reg` IS present in all three (20 `substitution_may21`, 21 `exo`/`selfsuff_reduced*`, 70 `fbask_jan16*`). Real consumers: `rg -l 'vm_prod\b' modules/*/*/{equations,presolve,postsolve}.gms` → 17,18,30,31,38,40,42,71,73 (sample lines confirmed in 18/30/38).
- **verify_cmd**: `rg -n 'vm_prod\b' /tmp/magpie_develop_ro/modules/21_trade/*/*.gms` → (empty); `rg -ln 'vm_prod_reg\b' /tmp/magpie_develop_ro/modules/21_trade/*/*.gms` → 3 files (positive control passes).
- **Harm**: subtle cell-vs-regional confusion; a user tracing `vm_prod` would check the wrong modules. Major (summary table, but a real consumer-set error).
- **Fix**: change Used-By to "18, 30, 31, 38, 40, 42, 71, 73" (and note 20/21/70 consume the regional aggregate `vm_prod_reg`).

### BUG-05 (Major, tier_uncertainty — Critical-adjacent) — §4.6 fabricated `p70_cattle_stock_proxy` formula + nonexistent variable `pm_gdp_pc_ppp` + invalid line citation
- **Class**: 2 (hallucinated var) + 4 (conceptual pseudo-code presented as real) + 10 (stale citation).
- **Doc** (GAMS_MAgPIE_Patterns:561-570): "**Example** (Module 70, lines 69-75)" code block, `* In presolve.gms`, `p70_cattle_stock_proxy(t,i) = im_pop(t,i) * pm_gdp_pc_ppp(t,i) / sum(i_to_iso(i,iso), im_pop_iso("y1995",iso)) * sum(i_to_iso(i,iso), im_gdp_pc_ppp_iso("y1995",iso));` guarded by `if (ord(t) = smax(...) AND card(t) > ...)`.
- **Reality**: actual code is `p70_cattle_stock_proxy(t,i) = im_pop(t,i)*pm_kcal_pc_initial(t,i,"livst_rum") / i70_livestock_productivity(t,i,"sys_beef");` — **unconditional** (no `if(ord(t)=smax… AND card…)` guard around it). Uses `pm_kcal_pc_initial` + `i70_livestock_productivity`, NOT `pm_gdp_pc_ppp`/`im_pop_iso`/`im_gdp_pc_ppp_iso`. **`pm_gdp_pc_ppp` does not exist anywhere in the codebase.** Cited "lines 69-75" is invalid: `presolve.gms` is only 70 lines (lines 69-70 = blank + `*' @stop`); the proxy calc is at lines 32-33. The doc's formula is an OLD GDP-based proxy that current MAgPIE no longer uses.
- **Evidence**: `modules/70_livestock/fbask_jan16/presolve.gms:32-33` (real formula); `wc -l` = 70; `sed -n '69,75p'` = blank + `@stop`. `rg -ln 'pm_gdp_pc_ppp\b' modules/` → EMPTY (nonexistent). `im_pop_iso`/`im_gdp_pc_ppp_iso` exist but in modules 60/50/38, not 70.
- **verify_cmd**: `rg -ln 'pm_gdp_pc_ppp\b' /tmp/magpie_develop_ro/modules/` → (empty); `sed -n '32,33p' .../fbask_jan16/presolve.gms` → kcal/productivity formula; `wc -l` → 70.
- **Harm**: presented as `* In presolve.gms` with a real parameter name; a reader believes `p70_cattle_stock_proxy` is GDP-driven (it is kcal-demand/productivity-driven). The nonexistent `pm_gdp_pc_ppp` matches the Critical "invented variable presented as authoritative" trigger; tie-breaker → Major because the section header is "**Example**" teaching the historical→projection pattern. tier_uncertainty=true.
- **Fix**: replace the code block with the real unconditional formula at `presolve.gms:32-33` (`im_pop * pm_kcal_pc_initial(...,"livst_rum") / i70_livestock_productivity(...,"sys_beef")`), drop the `if(ord(t)=smax…)` wrapper and the GDP-based variables, and fix the citation to `modules/70_livestock/fbask_jan16/presolve.gms:32-33`. (Or relabel the whole block "Conceptually" and remove the file:line + the nonexistent variable.)

### BUG-06 (Major, tier_uncertainty) — §3.4 fabricated `q56_emis_pricing_co2` formula (wrong LHS, wrong indices, wrong terms)
- **Class**: 4 (conceptual pseudo-code as real) + 9-adjacent (equation algebra wrong).
- **Doc** (GAMS_MAgPIE_Patterns:396-401): `* In equations.gms — carbon pricing creates incentive`, `q56_emis_pricing_co2(i2) .. vm_emission_costs(i2) =e= sum((emis_source, pollutants_co2), vm_emissions_reg(i2,emis_source,pollutants_co2) * sum(ct, im_pollutant_prices(ct,i2,pollutants_co2,emis_source)));`.
- **Reality**: actual `q56_emis_pricing_co2(i2,emis_oneoff) .. v56_emis_pricing(i2,emis_oneoff,"co2_c") =e= sum((cell(i2,j2),emis_land(emis_oneoff,land,c_pools)), (pcm_carbon_stock(j2,land,c_pools,"actual") - vm_carbon_stock(j2,land,c_pools,"%c56_carbon_stock_pricing%"))/m_timestep_length);`. The real equation: (a) has indices `(i2,emis_oneoff)` not `(i2)`; (b) LHS is `v56_emis_pricing` not `vm_emission_costs`; (c) computes a carbon-stock difference, not `vm_emissions_reg * im_pollutant_prices`; (d) uses set `emis_oneoff`/`pollutants`, not `emis_source`/`pollutants_co2`. The `vm_emissions_reg * im_pollutant_prices` pattern in the doc actually resembles a DIFFERENT equation (`q56_emission_cost_annual`, equations.gms:30-34).
- **Evidence**: `modules/56_ghg_policy/price_aug22/equations.gms:19-22` (real `q56_emis_pricing_co2`); `:30-34` (the `v56_emission_cost = sum(pollutants, v56_emis_pricing * im_pollutant_prices)` equation the doc conflated). `vm_emissions_reg` is real (declared M56) but not used in `q56_emis_pricing_co2`.
- **verify_cmd**: `sed -n '19,40p' /tmp/magpie_develop_ro/modules/56_ghg_policy/price_aug22/equations.gms` → real LHS `v56_emis_pricing(i2,emis_oneoff,"co2_c")` and carbon-stock-difference RHS.
- **Harm**: presented as `* In equations.gms` with a real equation name; misleads about the equation's actual LHS/structure. The conceptual mechanism (emissions×price=cost) is sound and all named variables exist, so tie-breaker → Major (Critical-adjacent for the fabricated formula on a real equation name). tier_uncertainty=true.
- **Fix**: either (a) replace with the real `q56_emis_pricing_co2` algebra from equations.gms:19-22, or (b) relabel "Conceptually, carbon pricing turns emissions into costs via `vm_emissions_reg` × `im_pollutant_prices`" and drop the `q56_emis_pricing_co2(i2) .. vm_emission_costs(i2) =e=` framing that misattributes this to that named equation. The cleaner fix is (b) since the section's goal is the dependency *concept*, not the literal algebra.

### BUG-07 (Minor) — §1.2 "Every MAgPIE module realization contains these files" overstates `scaling.gms` (and `sets.gms`) universality
- **Class**: 6-adjacent (count/universality drift).
- **Doc** (GAMS_MAgPIE_Patterns:45 + table): "**Every MAgPIE module realization contains these files**" listing `declarations.gms, equations.gms, sets.gms, input.gms, preloop.gms, presolve.gms, postsolve.gms, realization.gms, scaling.gms, start.gms".
- **Reality**: `scaling.gms` exists in only ~41 of ~74 realizations (~55%); `start.gms` is optional (the doc's own table marks it "(Optional)", contradicting the "Every" header); `sets.gms`/`preloop.gms` are also not universal.
- **Evidence**: `ls modules/*/*/scaling.gms | wc -l` = 41 vs `ls -d modules/*/*/ | grep -v input | wc -l` ≈ 74. (`landmatrix_dec18` happens to have all of them, which is why the example looks complete.)
- **verify_cmd**: `withscaling=$(ls /tmp/magpie_develop_ro/modules/*/*/scaling.gms | wc -l)` → 41; total realizations ≈ 74.
- **Harm**: low — a reader finding no `scaling.gms` in a given realization just sees it absent. Code-verifiable false universality claim → Minor.
- **Fix**: change header to "Most MAgPIE module realizations contain these files (the required ones are `realization.gms`, `declarations.gms`, `equations.gms`; `sets.gms`, `preloop.gms`, `scaling.gms`, `start.gms` are present only when the module needs them)."

---

## Deferred (not edited — uncertain or not cleanly code-verifiable)

- §2.1 lists `kcr` as a "Global set" example (line 278) while it is actually defined in module 14 (`kcr(kve)`), and also lists it again as module-specific (line 279). Internally inconsistent classification, but `kcr` is used model-wide and the §2.3 "Crop products" gloss is conceptually fine (code: "Cropping activities"). Borderline; not flagging as a discrete bug.
- §2.3 `i` = "Regions (10-14 aggregated regions)" and `j` = "default ~200 clusters" — both are config-dependent soft claims (hedged with "~"/"resolution-dependent"); default H12=12 regions, default clustering ~200. Within hedge tolerance; not flagged.
- §2.3 `i2`/`j2` called "Aliases" — `i2(i)` is actually a *dynamic subset* ("World regions (dynamic set)", sets.gms:122), not a pure `alias`. Minor imprecision; the doc's intent (multi-index companion of i) is close enough. Not flagged (would be Informational at most).
- §1.3/§4.1 `solve magpie using nlp minimizing vm_cost_glo` shown inside a `loop(t,…)` "in main.gms": the literal solve is generated via `$batinclude "./modules/include.gms" solve` from `core/calculations.gms` (inside a `while(sm_intersolve=0,…)` intersolve loop), not a bare `loop(t,…)` in main.gms. The objective (`vm_cost_glo`) and solver (nlp) are correct; the loop/location is a pedagogical simplification. Not flagging (conceptually accurate; flagging would be Informational).
- All GAMS-language semantic claims (singleton set, `$macro` compile-time substitution, `.fx/.lo/.up/.l` suffixes, `$()` conditions, `=e=/=l=/=g=`) — verified consistent with gams.com and with real macros.gms; no bug.

---

## Summary

7 bugs: 0 Critical, 6 Major (4 with tier_uncertainty; BUG-05/06 Critical-adjacent — fabricated formulas in pattern-teaching blocks, BUG-05 also uses the nonexistent var `pm_gdp_pc_ppp`), 1 Minor. Core conventions (prefixes, file layout, default realizations, M10 declarations, macros, GAMS-language semantics) are accurate. The errors cluster in (a) the §2.3 product-set MEANING table (`kve`, `kfo` wrong), (b) interface-variable CONSUMER sets (§3.1 `vm_land`, §3.2 `vm_prod` — phantom consumers from transitive/cell-vs-regional confusion), and (c) two illustrative code blocks (§3.4, §4.6) presenting fabricated/stale algebra as real `In equations.gms`/`In presolve.gms` code. The pre-run advisory is confirmed: MAgPIE-convention claims needed code verification and surfaced real set-meaning + consumer-set defects.
