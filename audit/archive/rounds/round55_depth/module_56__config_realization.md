# Round 55 Depth Audit — module_56.md — Lens: config_realization

**Target:** `modules/module_56.md`
**Ground truth:** `/private/tmp/magpie_develop_ro` (develop worktree), `config/default.cfg`, `audit/integrated/depth_rolemap.json`
**Date:** 2026-07-16
**Verdict:** Doc is very high quality. All default values, realization names, cfg$gms switch behaviors, and interface-variable attributions verified correct. Two low-severity findings only.

---

## Summary

Module 56 has a single realization `price_aug22` (config/default.cfg:1631 `cfg$gms$ghg_policy <- "price_aug22"`), and the doc correctly leads with it. Every scalar default (4920, 1, 3.67, 0, 1, 50, 0.5, 0, 2035, 2050, 1), every c56/s56 switch default, `sm_fix_SSP2=2025`, the equation reproductions/line citations, and the vm_/pm_/im_/pcm_ attribution claims were checked against code + role map and all hold. Only two low-severity issues found: an illustrative example using non-existent `emis_source` labels, and one abbreviated dependency-metadata line that omits module 58.

---

## Verified CORRECT (high-value config/realization/attribution claims)

**Defaults (config/default.cfg + input.gms, both agree):**
- `ghg_policy` realization = `price_aug22` (single realization) — config:1631, ls confirms only `price_aug22/` dir. ✓
- `c56_pollutant_prices` = R34M410-SSP2-NPi2025 (config:1731, input:84) ✓
- `c56_pollutant_prices_noselect` = R34M410-SSP2-NPi2025 (config:1732, input:85) ✓
- `c56_emis_policy` = reddnatveg_nosoil (config:1828, input:86) ✓
- `c56_carbon_stock_pricing` = actualNoAcEst; options actual/actualNoAcEst (config:1835, input:90-91, sets.gms:212-213 stockType) ✓
- `c56_cprice_aff` = secdforest_vegc (config:1772, input:87) ✓
- `c56_mute_ghgprices_until` = y2030 (config:1744, input:88) ✓
- `s56_limit_ch4_n2o_price` = 4920 (config:1798 "4000*1.23", input:65) ✓
- `s56_cprice_red_factor` = 1 (config:1638, input:66) ✓
- `s56_minimum_cprice` = 3.67 (config:1747, input:67) ✓
- `s56_ghgprice_devstate_scaling` = 0 (config:1634, input:68) ✓
- `s56_c_price_induced_aff` = 1 (config:1759, input:69) ✓
- `s56_c_price_exp_aff` = 50 (config:1778, input:70) ✓
- `s56_buffer_aff` = 0.5 (config:1785, input:71) ✓
- `s56_ghgprice_fader` = 0 (config:1641, input:75) ✓
- `s56_fader_start`/`end`/`target` = 2035/2050/1 (config:1645/1647/1649, input:76-78) ✓
- `sm_fix_SSP2` = 2025 (config/default.cfg:225) ✓

**Set cardinalities:**
- scen56 = 44 policies (sets.gms:120-163, counted) ✓
- pollutants_all = 16 (sets.gms:172-185, counted) — f56_emis_policy indexed on pollutants_all ✓
- emis_source = 31 (core/sets.gms:302-312, counted) ✓
- ghgscen56 = 100+ (sets.gms:16-117, ~102 members) ✓
- All policy/price scenario names in doc tables (§5.1, §5.2) are real set members ✓

**Equation reproductions + citations (equations.gms):** q56_emis_pricing (15-17), q56_emis_pricing_co2 (19-22), q56_emission_cost_annual (29-33), q56_emission_cost_oneoff (45-52), q56_emission_costs (56-58), q56_reward_cdr_aff_reg/q56_reward_cdr_aff (67-79) — all match exactly. 7 equations (declarations.gms:24-31). ✓

**Interface-variable attribution (role map + both-endpoints grep):**
- `vm_emissions_reg` populated by 51/52/53/58, read by 56/57 — doc §2.1, §4.2, §12.2 correct incl. "M57 only reads, does not populate." ✓
- `vm_carbon_stock` populated by 29/31/32/34/35/59 (+56 init), read by 52/56/59; peatland (58) does NOT populate — doc §4.1, §12.4 correct. ✓
- `vm_carbon_stock_croparea` populated by 30, read by 29 — doc "M30 folds into M29" correct. ✓
- `vm_emission_costs` read by 11 (+15 post-solve tax recycling) — module 15 anthro_iso_jun22/intersolve.gms:23 confirmed. ✓
- `vm_reward_cdr_aff` enters module 11 with NEGATIVE sign — 11_costs/default/equations.gms:27 `- vm_reward_cdr_aff(i2)` confirmed; vm_emission_costs positive (11 default eq:26). ✓
- `im_pollutant_prices` read by 57 — 57_maccs/on_aug22/preloop.gms:24-25 confirmed. ✓
- `pcm_carbon_stock` carry-forward: M56 postsolve.gms:8 (ag_pools), M59 cellpool_jan23/postsolve.gms:13 (soilc); git commit 931db85c4 = "59_som: carry soil pcm_carbon_stock forward each timestep" confirmed. cellpool_jan23 is default (config:1934). ✓
- Module 34 urban carbon fixed to 0: both realizations `.fx(j,"urban",ag_pools,stockType)=0` (static/presolve.gms:10, exo_nov21/presolve.gms:8). ✓

**Preloop stage citations (§3.1-3.8):** all preloop.gms line ranges (36-45, 51, 53-63, 67, 70/72/74, 80-82, 85-91, 115/118/120-121) verified against code. The "direct vm_carbon_stock, bypassing vm_emissions_reg / parallel-to-M52" framing (doc §2.2) is correct and consistent with the R51 fix (56 reads vm_carbon_stock directly in q56_emis_pricing_co2). ✓

**Corroborated:** Doc line 666 ("CDR reward active under default reddnatveg_nosoil because c56_cprice_aff=secdforest_vegc is priced") is directly confirmed by config/default.cfg:1771 comment.

---

## FINDINGS

### F1 — Minor (set_membership): illustrative "Selective Pricing Example" uses non-existent emis_source labels

**doc_line:** module_56.md:505-508
**Claim:** 
```
Policy "redd_nosoil" might have:
- f56_emis_policy("redd_nosoil","co2_c","deforest") = 1
- f56_emis_policy("redd_nosoil","co2_c","cropland_soil") = 0
- f56_emis_policy("redd_nosoil","ch4","livestock") = 0
```
**Reality:** `deforest`, `cropland_soil`, and `livestock` are NOT members of the `emis_source` set (core/sets.gms:302-312). The real members are `primforest_vegc`/`secdforest_vegc` (deforestation CO2), `crop_soilc` (cropland soil CO2), and `ent_ferm`/`awms` (livestock CH4). A user copying `f56_emis_policy(...,"deforest")` into a `display` would get an empty/domain result.
**verify_cmd:** `grep -c 'deforest\|cropland_soil\|\<livestock\>' core/sets.gms` → 0 (labels absent); emis_source members listed at core/sets.gms:303-312.
**Note:** Framed as illustrative ("might have", header "Selective Pricing Example"), so severity is Minor — but the strings are formatted as real GAMS set-member lookups and violate the exact-set-member-label convention.
**Proposed fix:** Replace with real emis_source members, e.g. `f56_emis_policy("redd_nosoil","co2_c","secdforest_vegc") = 1`, `...,"crop_soilc") = 0`, `f56_emis_policy("redd_nosoil","ch4","ent_ferm") = 0`.

### F2 — Informational (other): "Dependency Chains" metadata omits module 58

**doc_line:** module_56.md:1139
**Claim:** "Depends on: Modules 52 (carbon stocks), 53 (methane), 51 (N₂O)"
**Reality:** `vm_emissions_reg` (a direct input to M56) is populated by 51, 52, 53 AND 58 (peatland) — role map + confirmed populators. Module 58 is genuinely omitted from this abbreviated dependency line (also absent: 32 vm_cdr_aff, 12 pm_interest, land carbon-stock modules 29/31/34/35/59). The complete list IS given correctly at module_56.md:1076 ("Upstream: Emission modules (51,52,53,58), Forestry CDR (32), Carbon stocks (29,31,32,34,35,59; M30 via croparea), Discount rates (12)").
**verify_cmd:** role map `vm_emissions_reg.populated_by = ['51','52','53','58']`.
**Note:** Abbreviated auto-generated centrality block; the body text is complete and correct. Low priority.
**Proposed fix:** Add module 58 (peatland) to the line, or note it is an abbreviated top-dependency summary (see line 1076 for the full list).

---

## Deferred (could not verify / out of scope — no bug asserted)

- **f56_emis_policy.csv detailed content** (doc lines 499, 662-663: which pollutant×source combos are priced under reddnatveg_nosoil / redd+natveg_nosoil): the CSV is gitignored (`git check-ignore` confirms `modules/56_ghg_policy/input/f56_emis_policy.csv`) and is a run-time input product — not present in the develop tree. Cannot verify the per-cell 0/1 coverage claims. (R53-class caution: did not flag as a bug.)
- **Centrality metrics** (doc: "Rank #3", "Provides to: 13 modules", "Affects 13 modules"): cross_module centrality analysis, not directly checkable from module 56 code.
- **Approximate CO2 price magnitudes** in §5.1 table and §9.4 sanity ranges: explicitly labeled "approximate"/"order-of-magnitude"; not exact-checkable.
- **Total Lines of Code: 709**: soft metric, not independently recomputed.
