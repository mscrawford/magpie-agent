# Round 55 Depth Audit — module_52.md — lens: mechanism_direction

Target: `modules/module_52.md`
Ground truth: `/private/tmp/magpie_develop_ro` (develop worktree)
Default realization: `normal_dec17` (config/default.cfg:1574 `cfg$gms$carbon <- "normal_dec17"`) — the only realization dir besides `input/`. Doc correctly leads with it.

## Summary
Module 52 doc is unusually accurate on mechanism: the growing-stock bisection calibration (preloop.gms), the Chapman-Richards / linear macros, the q52_emis_co2_actual formula and sign convention, and nearly all file:line citations verify exactly against develop. One genuine set-membership omission found (Module 14 consumes the uncalibrated secdforest density but is absent from every consumer list), plus one imprecise boilerplate direction claim.

## Verified-correct (high-value spot checks)
- Emission equation q52_emis_co2_actual (equations.gms:16-19) — exact match, sign/direction correct (pcm - vm)/timestep. ✅
- Macros: m_growth_vegc core/macros.gms:18, m_growth_litc_soilc :20, m_timestep_length :51 — all exact. ✅
- Sets: emis_oneoff core/sets.gms:314-318 (21 members), c_pools :324-325, emis_land :332-335 — exact. ✅
- Calibration mechanism (bisection, 25 iters iter52 sets.gms:12-13, type-specific bounds s52_k_high_secdf=0.1 input.gms:47 / s52_k_high_plant=0.15 :48, master switch s52_growingstock_calib=1 :46) — all exact; GS_trial formula matches preloop.gms:53-64; plantation reuses secdforest C_max (preloop.gms:91) and forestry aboveground fraction (:96) vs secdforest (:61) — exact. ✅
- im_vol_conv always-computed at preloop.gms:21; fallback 0.5 at start.gms:40; consumed by M73 preloop.gms:49,51,90,91 — exact. ✅
- pm_land_plantation populated by M32 preloop.gms:179 (ordering claim correct); im_forest_ageclass from M28. ✅
- pcm_carbon_stock carry-forward: ag_pools M56 postsolve.gms:8, soilc M59 cellpool postsolve.gms:13 + static postsolve.gms:9 — exact. ✅
- sm_carbon_fraction M14 input.gms:22 (=0.5); fm_ipcc_bef M14 input.gms:66; fm_aboveground_fraction M14 input.gms:74 — exact. ✅
- Consumer sets for fm_carbon_density (14,29,30,31,32,35,56,59), calibrated pm_carbon_density_secdforest_ac (14,35), plantation_ac (14,32), other_ac (14,35) — all match role map + grep. ✅
- vm_carbon_stock definitional populators 29,31,32,34,35,59 + M30 croparea folded by M29 — correct (M56's role is declarer/`.l`-init in preloop.gms:11, not a land-type populator; correctly framed as declarer elsewhere). ✅

## BUG 1 (Major) — Module 14 omitted from consumers of pm_carbon_density_secdforest_ac_uncalib
Role map read_by = [14, 29, 32, 35, 52]. The doc's dedicated parameter entry "1b" (module_52.md:454-458) enumerates Consumers as **only Module 32 and Module 29** ("All three use cases represent new establishment"), and the write/read-by lists at :278-280 and :292 likewise never mention Module 14. But Module 14 directly reads it at `modules/14_yields/managementcalib_aug19/presolve.gms:66` to compute `im_growing_stock_ysf` (young secondary forest growing stock → wood yield). This is a real, direct consumer computing a timber-yield quantity — NOT a "new establishment" case — so both the set and the rationale that frames the set are incomplete. (Module 35 is also absent from the :458 entry, though it is documented elsewhere at :292/:138.)

## BUG 2 (Informational) — "Provides to: 11 (costs), 44 (biodiversity)" boilerplate direction claim unsupported
module_52.md:1201 (Participates In > Dependency Chains): "Provides to: Modules 56 (ghg_policy), 11 (costs), 44 (biodiversity)." Module 56 is correct. Neither Module 11 nor Module 44 directly reads any Module 52 output (fm_carbon_density / pm_carbon_density_* / im_vol_conv / vm_emissions_reg): `rg -n "fm_carbon_density|pm_carbon_density|im_vol_conv" modules/11_costs modules/44_biodiversity` → none. Caveat: this is generic centrality-metadata boilerplate that may encode a transitive/conceptual graph (52→56→emission-costs→11 is transitive; no plausible 52→44 link at any hop). Low load-bearing; flagged Informational.

## Deferred (not flagged — unverifiable or defensible)
- vm_emissions_reg read_by also includes M57 (maccs) at 57_maccs/on_aug22/equations.gms:38,40,48,50, but only for CH4/N2O (pollutants_maccs57); M52 writes only the co2_c slice, so "Consumers: Module 56" for M52's output (module_52.md:443) is defensible.
- "Depends on: 10 (land), 28 (age class), 35 (natveg)" (module_52.md:1202): 28 correct; 35 defensible (M52 reads vm_carbon_stock populated by M35); 10 transitive. Not flagged.
- Historical PR/commit metadata (PR #869 date 2026-03-16, commits 75d7ee167 / c7731e234 / 931db85c4) — not verified against git history.
