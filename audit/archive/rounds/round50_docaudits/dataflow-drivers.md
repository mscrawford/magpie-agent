# Audit Report: Data_Flow.md (Round 50 doc audit)

**Target**: `core_docs/Data_Flow.md`
**Ground truth**: `/tmp/magpie_develop_ro` @ `ee98739fd` (Merge PR #887)
**Auditor**: adversarial doc auditor (Opus)
**Date**: 2026-06-06

## Overall Verdict: MOSTLY ACCURATE
## Accuracy Score: 8/10

Data_Flow.md is a high-quality, code-grounded document. The flagship cross-module claim (the `pm_carbon_density_secdforest_ac` populator/consumer set at line 294) is essentially perfect against current develop, including exact file:line citations and the calibrated-vs-uncalibrated sibling distinction. Variable signatures, the carbon postsolve example, the lambda calibration formula, the `i14_managementcalib` data-loading example, the time sets, the 12 regions, the model block declaration, and all 10 magpie4 report functions all verify. Two real bugs: a reworked yield equation the doc still shows in its pre-rework form, and a non-default trade variable presented in the flagship optimization-variable table without caveat.

---

## Verified Claims (correct)

### Realizations / defaults (all confirmed against config/default.cfg)
- `managementcalib_aug19` is the default for module 14 — `cfg$gms$yields <- "managementcalib_aug19"`. Only realization dir present. ✓
- `normal_dec17` default for module 52 ✓; `pot_forest_may24` default for module 35 ✓; `all_sectors_aug13` default for module 42 ✓; `landmatrix_dec18` default for module 10 ✓.
- `c14_yields_scenario` default `"cc"` ✓; `nocc`/`nocc_hist` scenario handling at `modules/14_yields/managementcalib_aug19/input.gms:41-42` matches doc lines 98-99. ✓

### Line 294 — pm_carbon_density_secdforest_ac (the load-bearing cross-module claim) — FULLY CORRECT
- DECLARED in M52: `modules/52_carbon/normal_dec17/declarations.gms:9` ✓
- SET in preloop: `modules/52_carbon/normal_dec17/preloop.gms:71` ✓ (also start.gms:28,31)
- READ by M14: `modules/14_yields/managementcalib_aug19/presolve.gms:44` (im_growing_stock calc) ✓
- READ by M35: `modules/35_natveg/pot_forest_may24/presolve.gms:248-251` ✓
- Uncalibrated sibling `pm_carbon_density_secdforest_ac_uncalib` read by M29 (`detail_apr24/preloop.gms:46`), M32 (`dynamic_may24/presolve.gms:59,68`), M35 (`pot_forest_may24/presolve.gms:117,242,251`) ✓
This claim correctly distinguishes DECLARED/POPULATED/READ (MANDATE 18) and correctly routes the calib vs uncalib siblings (MANDATE 17). Exemplary.

### Optimization variable signatures (Section 3.4 table, lines 204-211)
- `vm_land(j,land)` — `modules/10_land/landmatrix_dec18/declarations.gms:19` ✓
- `vm_area(j,kcr,w)` — `modules/30_croparea/detail_apr24/declarations.gms:21` (and simple_apr24:18) ✓
- `vm_prod(j,k)` — `modules/17_production/flexreg_apr16/declarations.gms:9` ✓
- `vm_yld(j,kve,w)` — `modules/14_yields/managementcalib_aug19/declarations.gms:26` ✓
- `vm_carbon_stock(j,land,c_pools,stockType)` — `modules/56_ghg_policy/price_aug22/declarations.gms:34` ✓ (declared in M56, consistent with G2 anchor)
- `vm_tau(j,tautype)` — `modules/13_tc/endo_jan22/declarations.gms:13` ✓
- `vm_watdem(wat_dem,j)` — `modules/42_water_demand/all_sectors_aug13/declarations.gms:29` ✓

### Other verified items
- Model block: `model magpie / all - m15_food_demand /;` — `main.gms:279` EXACT ✓; `option iterlim = 1000000; option reslim = 1000000;` — main.gms:281-282 ✓ (doc lines 191-193). [Initial false alarm: I grepped core/ first and missed it; positive-control confirmed it lives in main.gms.]
- Objective `minimize vm_cost_glo` — `vm_cost_glo` declared `modules/11_costs/default/declarations.gms:9`; solve `modules/80_optimization/nlp_apr17/solve.gms:34` ✓
- `presolve_ini` is a real phase — `core/calculations.gms:52` ✓
- `sm_intersolve` intersolve loop — `core/declarations.gms:9` (default /0/), logic in `modules/15_food/anthro_iso_jun22/intersolve.gms` ✓ (food default `anthro_iso_jun22` ✓)
- Carbon postsolve example (lines 227-230): `oq52_emis_co2_actual(t,i,emis_oneoff,...)` with .l/.m/.up/.lo — `modules/52_carbon/normal_dec17/postsolve.gms:9-12` ✓ (doc reorders level/marginal — cosmetic, not a bug). `q52_emis_co2_actual(i2,emis_oneoff)` — equations.gms:16 ✓
- Land system params (Section 5.1): `pcm_land(j,land)` (10:11), `pm_land_start(j,land)` (10:9), `vm_lu_transitions(j,land_from,land_to)` (10:23) all ✓
- presolve example line 171: `vm_land.lo(j,"primforest") = (1-s35_natveg_harvest_shr) * pcm_land(j,"primforest")` — EXACT match `modules/35_natveg/pot_forest_may24/presolve.gms:159` ✓ (s35_natveg_harvest_shr default /1/ ✓); `pm_land_conservation` declared `modules/22_land_conservation/area_based_apr22/declarations.gms:15` ✓
- Time sets: `t_all` = y1965..y2150 5-yr (sets.gms:154, doc says "1965-2150" ✓); `ct(t)` (218), `pt(t)` (219), `t_past` (177) all ✓
- Regions (line 253): CAZ, CHA, EUR, IND, JPN, LAM, MEA, NEU, OAS, REF, SSA, USA = exactly 12 — `core/sets.gms:21` EXACT ✓. Super-regions `h` "Same as regions" — `core/sets.gms:18` + supreg 1:1 mapping ✓
- 200 clusters / c200 default — default input file `..._cellularmagpie_c200_...tgz` in default.cfg ✓
- Lambda calibration (lines 308-311): `λ=1 if FAO≤LPJmL`, `λ=√(LPJmL/FAO) if FAO>LPJmL` — `preloop.gms:86` (=1) and `:91` (`sqrt(i14_modeled_yields_hist/f14_fao_yields_hist)`) ✓
- `i14_managementcalib` data-loading example (doc lines 108-115) — EXACT match `modules/14_yields/managementcalib_aug19/preloop.gms:108-114` ✓
- Input file references in GAMS code: `lpj_yields.cs3` (14 input.gms:37), `lpj_carbon_stocks.cs3` (52 input.gms:18), `f14_region_yields.cs3` (14 input.gms:53), `avl_land_t.cs3`→`f10_land` (10 input.gms:10) all ✓ (raw files absent from code-only worktree, expected; references confirmed in-code)
- magpie4 functions (lines 334-339): reportLandUse, reportEmissions, reportProduction, reportPriceAgriculture, reportPriceFoodIndex, reportPriceLand, reportWaterUsage, reportWaterAvailability, reportWaterIndicators, reportBII — all present in `.cache/sources/magpie4/R/` ✓

---

## Bugs Found

### Bug DF-B1 — q14_yield_crop formula drift (equation reworked, doc shows pre-rework form)
- **Severity**: Major
- **Class**: 4 (Conceptual pseudo-code) / formula drift
- **Trigger** (§1 Major): "Citation points at content that's no longer at the cited line, AND the actual cited content says something materially different" (here no line is cited, but the formula is presented under "Core Constraint Types" as the code's actual equation; MANDATE 1 — a formula must match code).
- **Claim in doc** (lines 216-221):
  ```
  q14_yield_crop(j2,kcr,w) ..
      vm_yld(j2,kcr,w) =e=
          sum(ct, i14_yields_calib(ct,j2,kcr,w))
          * sum((cell(i2,j2), supreg(h2,i2)),
              vm_tau(j2,"crop") / fm_tau1995(h2));
  ```
- **Reality in code** (`modules/14_yields/managementcalib_aug19/equations.gms:14-16`):
  ```
  q14_yield_crop(j2,kcr,w) ..
   vm_yld(j2,kcr,w) =e= sum(ct,i14_yields_calib(ct,j2,kcr,w)) *
                           vm_tau(j2,"crop") / sum((cell(i2,j2), supreg(h2,i2)), fm_tau1995(h2));
  ```
  The `sum(...)` scope differs materially. Doc puts the whole ratio `vm_tau(j2,"crop") / fm_tau1995(h2)` inside the sum (summing the ratio over the cell/supreg mapping); code divides `vm_tau(j2,"crop")` by `sum(..., fm_tau1995(h2))` (the sum wraps only the denominator `fm_tau1995`). The equation was reworked in commit `7af46385c` ("rework conservation tau") — the pre-rework form had `sum((ct, cell(i2,j2), supreg(h2,i2)), (vm_tau(h2,"crop")*(1-p14_cropland_consv_shr...)+...)/fm_tau1995(h2))`, i.e. sum-wraps-ratio, closer to the doc's structure. So the doc reflects an older structure.
- **File evidence**: `modules/14_yields/managementcalib_aug19/equations.gms:14-16`
- **verify_cmd** + result:
  `sed -n '14,16p' modules/14_yields/managementcalib_aug19/equations.gms` →
  `q14_yield_crop(j2,kcr,w) ..` / ` vm_yld(j2,kcr,w) =e= sum(ct,i14_yields_calib(ct,j2,kcr,w)) *` / `                         vm_tau(j2,"crop") / sum((cell(i2,j2), supreg(h2,i2)), fm_tau1995(h2));`
  `git show 7af46385c -- .../equations.gms` confirmed the RHS was changed in this commit.
- **confirmed**: true
- **proposed_fix**: Replace doc lines 216-221 with the current equation:
  ```gams
  # Example: Yield constraint with technology change
  q14_yield_crop(j2,kcr,w) ..
      vm_yld(j2,kcr,w) =e=
          sum(ct, i14_yields_calib(ct,j2,kcr,w))
          * vm_tau(j2,"crop")
          / sum((cell(i2,j2), supreg(h2,i2)), fm_tau1995(h2));
  ```
  Optionally add citation `(modules/14_yields/managementcalib_aug19/equations.gms:14-16)`.

### Bug DF-B2 — v21_trade presented in flagship variable table but exists ONLY in non-default realization
- **Severity**: Major
- **Class**: 4 (capability-vs-default) — MANDATE 4 / lead-with-default
- **Trigger** (§1 Major): "Missing default-state caveat (mechanism described as if always active when it's OFF by default)". `v21_trade` is the bilateral-trade variable; it does not exist in the default trade realization.
- **Claim in doc** (line 210, "Key Optimization Variables" table): `` `v21_trade(i_ex,i_im,k_trade)` | Trade flows | mio. tDM `` — presented alongside core always-present variables (vm_land, vm_prod, etc.) with no caveat.
- **Reality in code**: default trade realization is `selfsuff_reduced` (`config/default.cfg`: `cfg$gms$trade <- "selfsuff_reduced"`). `v21_trade(` is declared ONLY in the non-default `selfsuff_reduced_bilateral22`. The default `selfsuff_reduced` has no `v21_trade`; it uses `v21_excess_dem`, `v21_excess_prod`, `v21_import_for_feasibility` (declarations.gms:18-20). A user inspecting a default-config run's GDX for `v21_trade` would not find it.
- **File evidence**: `modules/21_trade/selfsuff_reduced_bilateral22/declarations.gms:23` (only declaration site); `modules/21_trade/selfsuff_reduced/declarations.gms:18-20` (default has different trade vars); `config/default.cfg` (`cfg$gms$trade <- "selfsuff_reduced"`).
- **verify_cmd** + result:
  `grep "cfg$gms$trade" config/default.cfg` → `cfg$gms$trade <- "selfsuff_reduced"             # def = selfsuff_reduced`
  `rg -ln 'v21_trade\(' modules/21_trade/*/declarations.gms` → only `modules/21_trade/selfsuff_reduced_bilateral22/declarations.gms`
  `rg -n 'v21_|vm_.*trade' modules/21_trade/selfsuff_reduced/declarations.gms` → v21_excess_dem, v21_excess_prod, v21_import_for_feasibility, vm_cost_trade_tariff/margin/feasibility (NO v21_trade)
- **confirmed**: true
- **proposed_fix**: Annotate the row to mark it non-default, e.g. change line 210 to:
  `` | `v21_trade(i_ex,i_im,k_trade)` | Bilateral trade flows (only in non-default `selfsuff_reduced_bilateral22`; default `selfsuff_reduced` uses `v21_excess_prod`/`v21_excess_dem`) | mio. tDM | ``
  Alternatively replace with a default-realization trade representation, or move it out of the "Key Optimization Variables" table into a clearly-labeled non-default note.

---

## Deferred (not code-verifiable against the code-only worktree, or config/run-dependent — NOT edited)
- File-format COUNTS table (lines 12-21: ".cs3 = 20", ".csv = 76", ".mz = 26", "~172 files", "~72 MB"): require the populated `input.tgz` data (absent from the code worktree). Could not verify. Not flagged.
- "Example Cell Distribution" (lines 256-261: "CHA: 19 cells CHA_6 through CHA_24", etc.): depends entirely on the clustering run (c200) and is explicitly labeled "Example". core/sets.gms in this worktree shows a smaller test layout (CAZ_1*CAZ_5); cluster-to-region counts are run-config-dependent. Deferred.
- Run statistics (Section 8.2: "~100,000 variables", "~150,000 equations", "5-30 min/timestep", "50-100 MB/timestep"): empirical run characteristics, not code-checkable. Deferred.
- "67,420 grid cells", "259,200 theoretical cells" (360x720 = 259,200 is arithmetically right; 67,420 land cells is data-dependent): the 0.5deg land-cell count depends on input data. Deferred.
- Validation metrics (Section 9.1: "R²>0.8", "±10%"): qualitative/empirical, not in code. Deferred.
- `.rds = 22 (Configuration files)` and prefix-table semantics (Section 2.1): conventions/prose, not directly falsifiable against a single code location. Deferred.
- GDX file sizes / restart file behavior (Section 6.1): runtime artifacts. Deferred.
- t_past "1965-2015, configurable" and t "1995-2100, configurable": doc explicitly says configurable; t_past membership is config-driven. Left as-is (accurate as a configurable default statement).

---

## Notes on method / false-positive guards run
- For the `model magpie` block I initially grepped `core/` and got zero hits — ran a positive control (`magpie` token count in core), discovered `core/equations.gms` does not exist, then found the declaration in `main.gms:279`. The doc claim is CORRECT; recorded as verified, not a bug. (Avoided a false "fabricated model block" call.)
- For `pm_carbon_density_secdforest_ac` consumers I grepped BOTH `name(` and `name.` forms (MANDATE 20); no solution-level reads exist, so the paren-grep set is complete.
- All consumer/producer sets cross-checked with `rg` (ripgrep) as the second method; each probe run as its own standalone command to avoid the find-exec / chained-exit truncation trap.
