# Round 55 depth audit — module_52.md — lens: citation_formula

**Target**: `modules/module_52.md` (Module 52 Carbon, realization `normal_dec17`)
**Ground truth**: `/private/tmp/magpie_develop_ro` (develop worktree)
**Default realization confirmed**: `cfg$gms$carbon <- "normal_dec17"` (config/default.cfg) ✓

## Method
Entered from every file:line citation in the doc; mechanically checked file existence, line-range, and that the cited line contains the claimed token. Cross-checked all interface-var producer/consumer claims against `audit/integrated/depth_rolemap.json`, then confirmed each with a both-endpoints grep (`NAME(` and `NAME.`) in the develop worktree.

## Citations verified CORRECT (high-confidence sample)
- Equation `q52_emis_co2_actual` formula (doc:306-311, 780-785) — exact match `equations.gms:16-19`. ✓
- Macros: `m_growth_vegc` `core/macros.gms:18`, `m_growth_litc_soilc` `:20`, `m_timestep_length` `:51` — all exact. ✓
- start.gms citations 9,10,17,20,28,31,43,44,48,51 — all correct token match. ✓
- preloop.gms citations 21,26-30,45-73,53,60,61,84-116,96,106-111,114-116 — all correct. ✓
- `land` set (`core/sets.gms:251`) = crop,past,forestry,primforest,secdforest,urban,other — doc:54/545-552 correct (R52 land-set bug is fixed). ✓
- `emis_oneoff` (sets.gms:314-318, 21 members), `emis_land` (:332-335), `c_pools` (:324-325) — doc enumerations exact. ✓
- Interface declarations: `vm_carbon_stock` M56 decl:34, `pcm_carbon_stock` decl:19, `vm_emissions_reg` decl:40, `q52` decl:30. ✓
- `vm_carbon_stock` populators 29/31/32/34/35/59 + "58 does NOT populate" + "30 populates vm_carbon_stock_croparea folded via M29" (doc:424) — matches role map + G2 anchor. ✓
- `pcm_carbon_stock` carry-forward: ag_pools M56 postsolve:8, soilc M59 cellpool postsolve:13 / static postsolve:9 (doc:431). ✓
- Calibrated-param consumer citations: M14 presolve:44/26, M35 presolve:248, M32 presolve:65 (doc:4,290,291). ✓
- Uncalib consumers M32 presolve:59/61/68, M29 preloop:46/48 (doc:279,458,478). ✓
- `im_vol_conv` consumed by M73 (preloop:49,51,90,91); `im_forest_ageclass` by M35 preloop:20; `im_growing_stock` by M32 presolve:181 / M35 equations:147. ✓
- `sm_carbon_fraction` M14 input.gms:22 `/ 0.5 /`; `fm_ipcc_bef` M14 input:66; `fm_aboveground_fraction` M14 input:74. ✓
- All 6 default realizations for fm_carbon_density consumers confirmed; citations M30 simple_apr24 eq:51, M31 endo_jun13 eq:24, M32 dynamic_may24 presolve:176, M35 pot_forest_may24 eq:44, M56 price_aug22 preloop:10, M59 cellpool_jan23 preloop:12 — all exact. ✓

## Bugs

### BUG 1 (Major) — doc:5 — im_vol_conv falsely attributed to Module 14
Doc header: "interface parameter `im_vol_conv(i)` (used by Module 73 **and shared with Module 14's growing-stock formula**)".
Reality: Module 14 does NOT reference `im_vol_conv` anywhere (`grep -rn im_vol_conv modules/14_yields/` → 0 hits; positive control in M73 works). M14's growing-stock formula (`modules/14_yields/managementcalib_aug19/presolve.gms:44-73`) is `pm_carbon_density_*(...,"vegc") / sm_carbon_fraction * fm_aboveground_fraction / (climate-weighted fm_ipcc_bef)` and yields **tDM/ha stem biomass** — it never divides by basic wood density. The `÷ im_vol_conv` (→ m³/ha) step exists only in M52's calibration (`preloop.gms:63,98`) and M73. The doc's own authoritative consumer section (doc:490) correctly lists ONLY M73, so this is an internal contradiction + phantom read. Class: attribution_read.

### BUG 2 (Major) — doc:458 — pm_carbon_density_secdforest_ac_uncalib consumer set incomplete + false "all three" claim
Doc "1b" parameter subsection: "**Consumers**: Module 32 (aff at :59 and ndc at :68), Module 29 (tree cover at preloop:46). **All three use cases represent *new establishment*** rather than existing managed forest."
Reality: role map read_by = [14, 29, 32, 35, 52]. Two consumers are omitted from this list:
- **Module 14** reads it at `modules/14_yields/managementcalib_aug19/presolve.gms:66` (computes `im_growing_stock_ysf` for young secondary forest) — undocumented anywhere in module_52.md.
- **Module 35** reads it at `modules/35_natveg/pot_forest_may24/presolve.gms:117,242,250-251` (youngsecdf land + calibrated/uncalib correction term).
Both uses are youngsecdf regrowth, NOT afforestation "new establishment", so the "all three use cases represent new establishment" universal is false as well as incomplete. (Mitigation: M35's read IS noted separately at doc:292; M14's is not noted anywhere.) Resembles the R20 Critical consumer-set anchor; rated Major under the tie-breaker because M35 is partially covered elsewhere. Class: attribution_read.

### BUG 3 (Minor) — doc:747 — fm_carbon_density grouping wrongly includes Module 34 (Urban)
Doc downstream-dependencies summary: "**7. All Land Modules** (30, 31, 32, **34**, 35): `fm_carbon_density` ... Used for carbon stock calculations for non-age-class land types."
Reality: Module 34 (Urban) does NOT reference `fm_carbon_density` (`grep -rn fm_carbon_density modules/34_urban/` → 0 hits, positive control in 31_past works). Urban carbon stock is fixed to 0 (doc:424 itself says so). The doc's own authoritative consumer lists (doc:265-273, doc:484) correctly EXCLUDE 34. This grouping also omits 29 (a real consumer). Phantom-consumer in a rough summary grouping that contradicts the doc's correct lists; low harm (extra module, not a missed one). Class: attribution_read.

## Deferred (not flagged — unverifiable or defensible)
- doc:443 lists only M56 as vm_emissions_reg consumer; M57 also reads vm_emissions_reg (57_maccs on_aug22 eq:38,40,48,50) but only for CH4/N2O slices (pollutants_maccs57), not the co2_c rows M52 writes — defensible in context.
- doc:28 "~24 params, 4 new calibration params" — declarations.gms parameter block has ~17 params and >4 new calibration params; hedged low-stakes structure metadata.
- doc:1201-1202 graph-summary "Provides to: 56, 11, 44 / Depends on: 10, 28, 35" — auto-generated centrality summary, no file:line citations, imprecise but out of lens scope.
- Commit hashes 75d7ee167 / c7731e234 / 931db85c4 and "NEW consumer as of 2026-04-20" newness claims — require git history, not verifiable from the code snapshot.
