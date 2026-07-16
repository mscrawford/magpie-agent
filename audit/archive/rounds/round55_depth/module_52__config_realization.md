# Round 55 depth audit — module_52.md (lens: config_realization)

**Target**: `modules/module_52.md` (Module 52 Carbon, realization `normal_dec17`)
**Ground truth**: `/private/tmp/magpie_develop_ro` (develop worktree)
**Auditor lens**: config_realization (defaults, cfg switches, realization names/default, per-slice ownership)

## Verdict: MOSTLY ACCURATE — 1 Major + 3 Minor bugs

The doc is unusually well-verified on the config/realization axis. Default realization (`normal_dec17`, the only one), all three config switches (`c52_carbon_scenario=cc`, `c52_land_carbon_sink_rcp=RCPBU`), and all three growing-stock scalars (`s52_growingstock_calib=1`, `s52_k_high_secdf=0.1`, `s52_k_high_plant=0.15`) match `input.gms` + `config/default.cfg` exactly. All 24 declaration-line citations, the equation formula, both growth macros, `m_timestep_length`, the core sets (`land`, `emis_oneoff`, `c_pools`, `emis_land`), and all 8 `fm_carbon_density` consumer citations (with correct default realizations) verified clean. The R52 land-set MANDATE-22 bug is fixed (land = crop, past, forestry, primforest, secdforest, urban, other). The G2 `vm_carbon_stock` populator set and `pcm_carbon_stock` per-slice carry-forward (M56 ag_pools / M59 soilc) are correct.

The residual bugs are all in the CONSUMER-SET / mechanism-description layer, not the config layer.

---

## BUG 1 (Major) — M14 omitted as consumer of `pm_carbon_density_secdforest_ac_uncalib`

- **doc_line**: module_52.md:458 (also 138, 292, 727 — omitted in all four)
- **Claim**: "1b. pm_carbon_density_secdforest_ac_uncalib ... Consumers: Module 32 (afforestation ... and NDC ...), Module 29 (tree cover ...)." Line 292 adds Module 35; **no location in the doc lists Module 14.**
- **Reality**: Module 14 reads `pm_carbon_density_secdforest_ac_uncalib` at `modules/14_yields/managementcalib_aug19/presolve.gms:66` to compute `im_growing_stock_ysf` (young secondary forest growing stock, used for youngsecdf wood yield). Role map read_by = [14, 29, 32, 35]; doc's fullest statement (line 292) covers only {29,32,35}, missing 14. The formal Parameters entry (line 458) is worse — {29,32} only, also dropping the M35 that line 292 has.
- **verify_cmd**: `rg -n "pm_carbon_density_secdforest_ac_uncalib" modules/14_yields/` → `.../presolve.gms:66:     pm_carbon_density_secdforest_ac_uncalib(t,j,ac,"vegc")`; `rg -n "ysf|presolve.gms:66" modules/module_52.md` → NO MENTION.
- **Why Major (Critical-prone)**: This is the exact R20 immutable anchor class (missed consumer of the `pm_carbon_density_*_ac` family → Critical). A user refactoring the `_uncalib` parameter and trusting module_52.md's consumer list would silently break M14's `im_growing_stock_ysf`. Tie-broken down to Major (one narrower consumer vs the anchor's two whole pathways; the primary consumers are covered). Flag `tier_uncertainty`.
- **Fix**: Add "Module 14 (`modules/14_yields/managementcalib_aug19/presolve.gms:66` — young-secondary-forest growing stock `im_growing_stock_ysf`)" to the consumer lists at lines 458, 138, 292, 727. Also restore Module 35 to the line-458 list (it is present at 138/292 but dropped at 458).

## BUG 2 (Minor) — Module 34 wrongly listed as an `fm_carbon_density` consumer

- **doc_line**: module_52.md:747
- **Claim**: "7. All Land Modules (30, 31, 32, 34, 35): fm_carbon_density ... Used for carbon stock calculations for non-age-class land types."
- **Reality**: Module 34 (urban) does NOT read `fm_carbon_density`; it fixes urban carbon to zero (`modules/34_urban/exo_nov21/presolve.gms:8: vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0;`). The doc's own authoritative consumer lists (lines 265–273 and 484) correctly EXCLUDE 34 and read {14,29,30,31,32,35,56,59}. Role map read_by has no 34.
- **verify_cmd**: `rg -n "fm_carbon_density" modules/34_urban/` → NO HIT (positive control: `rg -c fm_carbon_density modules/35_natveg/pot_forest_may24/equations.gms` → 1). 
- **Fix**: Drop 34 from the "All Land Modules (30, 31, 32, 34, 35)" grouping at line 747 (→ 30, 31, 32, 35), or note "34 (urban) fixes carbon to 0 and does not read fm_carbon_density."

## BUG 3 (Minor) — Bisection direction misstated ("else raise upper bound")

- **doc_line**: module_52.md:258
- **Claim**: "Bisection: if `GS_trial < f52_fra_nrf_gs(i)`, raise lower bound; else raise upper bound."
- **Reality**: When `GS_trial >= target`, the code sets the UPPER bound to the midpoint — i.e. it LOWERS the upper bound, not raises it. `preloop.gms:67: i52_k_high(i)$(i52_gs_current(i) >= f52_fra_nrf_gs(i)) = i52_k_calib_secdf(i);` (midpoint `= (i52_k_low+i52_k_high)/2 < i52_k_high`). GS is monotone increasing in k, so overshoot ⇒ shrink the interval from the top. "Raise lower bound" (line 66) is correct.
- **verify_cmd**: `sed -n '50,67p' preloop.gms` — line 50 midpoint, 66 `k_low := mid` when GS<target, 67 `k_high := mid` when GS>=target.
- **Fix**: "else **lower** the upper bound (set it to the midpoint)."

## BUG 4 (Minor) — "Start phase (each timestep)" — start runs once, not per-timestep

- **doc_line**: module_52.md:757
- **Claim**: "2. Start phase (each timestep, before optimization): Module 52: Calculate age-class carbon densities ..."
- **Reality**: The `start` phase runs ONCE in the preprocessing block, before the timestep loop. `core/calculations.gms:13 $batinclude "./modules/include.gms" start` and `:15 ... preloop` sit ABOVE the `loop (t...` at `:40`; the timestep loop contains only presolve/solve/postsolve. The `pm_carbon_density_*` params are `t_all`-indexed and computed once. (Section 2 line 78 correctly says "start phase (before optimization)"; only this summary adds the wrong "each timestep".)
- **verify_cmd**: `sed -n '13,40p' core/calculations.gms` — start(13), preloop(15), `loop (t...`(40).
- **Fix**: "Start phase (once, before the timestep loop)."

---

## Verified-correct (high-value spot checks)

- Realization `normal_dec17` is the only realization and the default (`config/default.cfg:1587` region; `module.gms` single `$Ifi`). Doc leads with it. ✓
- `c52_carbon_scenario=cc` (default.cfg:1587), `c52_land_carbon_sink_rcp=RCPBU` (default.cfg:1580), `s52_growingstock_calib=1`/`s52_k_high_secdf=0.1`/`s52_k_high_plant=0.15` (input.gms:46-48). ✓
- q52_emis_co2_actual formula = exact match (equations.gms:16-19). ✓
- Macros `m_growth_vegc` (macros.gms:18), `m_growth_litc_soilc` (macros.gms:20, applied only to litc in M52), `m_timestep_length` (macros.gms:51). ✓
- `vm_carbon_stock` DECLARED 56 (price_aug22/declarations.gms:34), populators {29,31,32,34,35,59} + M30→croparea folded via M29, M58 does NOT populate. G2 anchor clean. ✓
- `pcm_carbon_stock` carry-forward split: ag_pools M56 postsolve.gms:8; soilc M59 cellpool postsolve.gms:13 + static postsolve.gms:9. ✓
- `pm_carbon_density_secdforest_ac`→{14 presolve:44, 35 presolve:248}; `_plantation_ac`→{14 presolve:26, 32 presolve:65}; `_other_ac`→{14,35}; all uncalib/aff/ndc citations (M32 presolve:59/61/68, M29 preloop:46/48). ✓
- `fm_carbon_density` consumers 14/29/30/31/32/35/56/59 all cited at correct lines with correct default realizations (managementcalib_aug19, detail_apr24, simple_apr24, endo_jun13, dynamic_may24, pot_forest_may24, price_aug22, cellpool_jan23). ✓
- Upstream reads `im_forest_ageclass` (M28, preloop:53), `pm_land_plantation` (M32 preloop:88; populated M32 preloop.gms:179, precedes M52 preloop by module order), `fm_ipcc_bef`/`fm_aboveground_fraction` (M14, preloop:26/61), `sm_carbon_fraction` (M14 input.gms:22 /0.5/). ✓
- Phase ordering: start before preloop (both once, pre-loop); M28/M32 preloop before M52 preloop by numeric module order — doc claims correct. ✓
- Core sets `land`, `emis_oneoff` (21 members), `c_pools`, `emis_land` correct; no MANDATE-11/22 range/membership errors. ✓

## Deferred (not code-verifiable in this worktree / low value)
- Git-history/provenance claims: commit SHAs `75d7ee167`, `c7731e234`, `931db85c4`, PR #869 number/dates, "Georg Schroeter" authorship — require git log, out of scope for code ground truth. Base authors (Bodirsky, Humpenoeder, Mishra) match module.gms.
- Line 78 cites start.gms:8-39 for age-class calcs but "other land" is at start.gms:48,51 (outside the range); other-land is separately and correctly cited at lines 140/199/464, so this is a benign anchor-range imprecision, not flagged.
