# R60 depth audit — `cross_module/carbon_balance_conservation.md`

**Lens**: `consumer_read` — enter from the consumer side (presolve/postsolve/equation-RHS of every module the doc names as a reader), whole-tree greps of BOTH `NAME(` and `NAME.` for each interface var, priority on READ/consumer SET claims (phantoms AND omissions) and solution-level `.l/.lo` reads.
**Ground truth**: MAgPIE `develop` read-only worktree, HEAD `2c02843ec` ("Merge pull request #919 from alexkoberle/dyn_reg_tau").
**Role map**: `audit/integrated/depth_rolemap.json` consulted FIRST for every DECLARED/POPULATED/READ claim, then confirmed at both endpoints in code with a second method + positive control.
**Claims verified**: 96 load-bearing, code-checkable claims.
**Bugs**: 13 — 1 Critical, 5 Major, 7 Minor. All confirmed with reproducible evidence.

### Provenance of this report (read this before acting on it)

A prior pass of this same lens/doc existed at this path. I completed my own independent derivation
**before** opening it. Each bug below is tagged:

- **[independent]** — derived by me from code before reading the prior pass (7 bugs).
- **[re-derived]** — the prior pass raised it; I re-verified it from code myself this session and it holds (6 bugs). None was accepted on the prior pass's authority.
- The prior pass also raised a **phase-ordering caveat that falsified part of my own proposed fix for BUG-1**. I re-derived the ordering from `core/calculations.gms:13-15` + `modules/include.gms:12-57` and it is correct; BUG-1's fix below is the corrected version. Flagging this explicitly because my first draft would have introduced a new error.
- Two bugs (**BUG-3**, **BUG-12**) are not in the prior pass at all.

---

## What the doc gets right (verified this session, not assumed)

Recorded so a future auditor does not re-derive them, and because a clean result is evidence.

- **`vm_carbon_stock` populator set (§7.5:630) is complete and exact.** Role map `populated_by = [29,31,32,34,35,59]`; both grep forms find exactly `modules/29_cropland/detail_apr24/equations.gms:39`, `modules/31_past/endo_jun13/equations.gms:23`, `modules/32_forestry/dynamic_may24/equations.gms:108`, `modules/34_urban/exo_nov21/presolve.gms:8`, `modules/35_natveg/pot_forest_may24/equations.gms:43,50,54`, `modules/59_som/cellpool_jan23/equations.gms:62`.
- **The `actual` / `actualNoAcEst` split (§2.3:101) is real and correctly attributed.** `stockType /actual, actualNoAcEst/` at `modules/56_ghg_policy/price_aug22/sets.gms:212-213`; declaration at `modules/56_ghg_policy/price_aug22/declarations.gms:34` (exact); M52 reads `"actual"` (`modules/52_carbon/normal_dec17/equations.gms:19`); M56 reads `"%c56_carbon_stock_pricing%"` (`modules/56_ghg_policy/price_aug22/equations.gms:22`), `$setglobal` default `actualNoAcEst` (`modules/56_ghg_policy/price_aug22/input.gms:90`). The conclusion — priced and reported CO₂ come off different slices in a default run — holds.
- **The parallel-not-serial claim (§7.3:583) is correct under a both-endpoints check.** `q56_emis_pricing` (`modules/56_ghg_policy/price_aug22/equations.gms:15-17`) is indexed over `emis_annual` only; LUC CO₂ is recomputed in `q56_emis_pricing_co2` (`:19-22`). M56 never consumes M52's `emis_oneoff` `co2_c`. No hand-off.
- **The uncalibrated-curve consumer set is complete** for default realizations: `modules/14_yields/managementcalib_aug19/presolve.gms:66`, `modules/29_cropland/detail_apr24/preloop.gms:46,48`, `modules/32_forestry/dynamic_may24/presolve.gms:59,61,68`, `modules/35_natveg/pot_forest_may24/presolve.gms:117,242` (+ `:251` inside the blend, which the doc describes separately). Only the *calibrated* side is defective (BUG-1).
- **`s52_growingstock_calib = 1` is the hard default and is genuinely not exposed in config** (`modules/52_carbon/normal_dec17/input.gms:46`; `grep -n "s52_growingstock_calib" config/default.cfg` returns nothing, while `s52_k_high_secdf` / `s52_k_high_plant` ARE exposed at `config/default.cfg:1597,1599` — positive control).
- **All §7.4 MACC applicability claims are exact, including both negatives**: M53 mitigation at `modules/53_methane/ipcc2006_aug22/equations.gms:29,52,63`; `q53_emissions_resid_burn` (`:70-72`) carries no mitigation term; `maccs_ch4 / rice_ch4, ent_ferm_ch4, awms_ch4 /` (`modules/57_maccs/on_aug22/sets.gms:28-29`); M51 AWMS-only MACC at `modules/51_nitrogen/rescaled_jan21/equations.gms:71` over all `n_pollutants_direct` with the code comment at `:62-64`; `q51_emissions_inorg_fert` (`:30-39`) carries none; M50's `inorg_fert_n2o` MACC at `modules/50_nr_soil_budget/macceff_aug22/presolve.gms:54-64`; rice absent from `emis_source_n51` (`modules/51_nitrogen/rescaled_jan21/sets.gms:15-16`) with everything else pinned at zero by `preloop.gms:8-10`.
- **All `core/sets.gms` citations exact**: `emis_oneoff` `:314-318` (21 = 7 × 3), `emis_annual` incl. `peatland` `:322`, `c_pools` `:324-325`, `emis_land` `:332-354`.
- **Peatland (§10.2 item 7) is exact**: `v2` default (`config/default.cfg:1874`), `s58_fix_peatland = 2020` (`:1931`), `modules/58_peatland/v2/realization.gms:8-17`, `q58_peatland_emis` (`modules/58_peatland/v2/equations.gms:91-92`), peat absent from `c_pools`.
- **Every realization named in the doc exists AND is the config default** (`normal_dec17`, `cellpool_jan23`, `ipcc2006_aug22`, `on_aug22`, `v2`, `detail_apr24` for M29, `endo_jun13`, `dynamic_may24`, `exo_nov21`, `pot_forest_may24`, `rescaled_jan21`, `macceff_aug22`, `managementcalib_aug19`). Note M14 now has a second realization `dynRegPastrTau_apr26`, but `config/default.cfg:357` still selects `managementcalib_aug19`, so the doc's M14 citations are on the default path.
- **All M59 equation and default citations exact**: `equations.gms:20-27`, `:46-52`, `:61-64`; `preloop.gms:45` (`i59_lossrate = 1-0.85**m_yeardiff`); `realization.gms:21-24` (pasture limitation); `input.gms:70` (irrigation off-switch); defaults `s59_scm_target = 0` (`config/default.cfg:1978`), `c59_irrigation_scenario = "on"` (`:1956`), `s59_cost_scm_recur = 65` (`:1994`), full-tillage/medium-input shares (`preloop.gms:52-55`).
- **`m_growth_vegc` (§6.1) and `m_timestep_length` (§9.1) quoted exactly** (`core/macros.gms:18`, `:51`).
- **§5.2's convergence table is right and is more accurate than the code's own comment**, which says "44% in 5 years" (`modules/59_som/cellpool_jan23/preloop.gms:42`) where `1-0.85^5 = 55.6%`.

---

## Bugs

### BUG-1 — Critical — `attribution_read` — calibrated-curve consumer set omits Module 32 — **[independent]**

**Doc** (`carbon_balance_conservation:180`, and the byte-identical duplicate at `:479`):
> "…and are what M14's `im_growing_stock_ysf` …, M29's tree cover …, **M32's afforestation and NDC curves** (`32_forestry/dynamic_may24/presolve.gms:59,61,68`) and M35's youngsecdf … read. **M14 and M35 read the CALIBRATED curve as well** — M14 for regular secdforest growing stock (`modules/14_yields/managementcalib_aug19/presolve.gms:44`), M35 for secdforest carbon density…"

**Reality**: the calibrated-curve reader set is **{M14, M32, M35}**, not {M14, M35}. Module 32 assigns the FRA-2025-calibrated `pm_carbon_density_plantation_ac` to the carbon density of **established timber plantations**:

```
modules/32_forestry/dynamic_may24/presolve.gms:65
p32_carbon_density_ac(t,j,"plant",ac,ag_pools) = pm_carbon_density_plantation_ac(t,j,ac,ag_pools);
```

and that parameter is exactly what `q32_carbon` turns into the forestry slice of the interface:

```
modules/32_forestry/dynamic_may24/equations.gms:108
q32_carbon(j2,ag_pools,stockType) .. vm_carbon_stock(j2,"forestry",ag_pools,stockType) =e=
            m_carbon_stock_ac(v32_land,p32_carbon_density_ac,"type32,ac","type32,ac_sub");
```

M14 also reads the calibrated **plantation** curve at `modules/14_yields/managementcalib_aug19/presolve.gms:26` (plantation growing stock), so "M14 for regular secdforest growing stock" understates M14's read too.

**⚠ Phase-ordering caveat — do not over-correct.** `modules/32_forestry/dynamic_may24/preloop.gms:18` and `:56` also name `pm_carbon_density_plantation_ac`, but they are **not** calibrated-curve reads. Phase order is `start` (all modules) → `preloop` (all modules) → time loop → `presolve` (`core/calculations.gms:13-15`), and `modules/include.gms:12-57` includes modules in strict numeric order, so M32's preloop (include line 29) runs **before** M52's preloop calibration overwrite (include line 44) and sees the uncalibrated `start.gms` values. Only the `presolve` read at `:65` is genuinely calibrated. A fix that lists `preloop.gms:18,56` as calibrated consumers would introduce a new error.

**Why Critical**: this box is the doc's authoritative statement of the FRA-2025 calibration's blast radius, written specifically to support curve-mismatch / carbon-arbitrage reasoning. It names M32 **only** under the uncalibrated readers, citing `presolve.gms:59,61,68` while skipping `:65`, which sits between them. A reader auditing or toggling `s52_growingstock_calib` would conclude M32 is a pure uncalibrated consumer and would miss the entire forestry vegetation-carbon pool. This is the immutable R20 anchor (rubric §1): doc stated a consumer set, code has more → **Critical** by future-reader harm.

**verify_cmd**:
```
rg -n "pm_carbon_density_plantation_ac(?!_uncalib)" -P modules/ core/
→ 52_carbon: declarations.gms:12, start.gms:17,20,44, preloop.gms:114 (declare/populate)
  32_forestry/dynamic_may24: preloop.gms:18,56 (pre-calibration), presolve.gms:65 (CALIBRATED)
  14_yields/managementcalib_aug19: presolve.gms:26 (CALIBRATED)
2nd method + positive control:
grep -rn "pm_carbon_density_plantation_ac"        modules/32_forestry/   → 4 hits (3 calibrated + 1 _uncalib at :61)
grep -rn "pm_carbon_density_secdforest_ac_uncalib" modules/32_forestry/  → 2 hits (positive control: search works)
Role map: pm_carbon_density_plantation_ac.read_by = ["14","32","52"]  (agrees)
```

**Proposed fix** (apply to both `:180` and `:479`):
> "**M14, M32 and M35 read the CALIBRATED curves as well** — M14 for secdforest growing stock (`modules/14_yields/managementcalib_aug19/presolve.gms:44`) and plantation growing stock (`:26`); **M32 for the carbon density of established timber plantations (`modules/32_forestry/dynamic_may24/presolve.gms:65`), which `q32_carbon` (`modules/32_forestry/dynamic_may24/equations.gms:108`) turns into `vm_carbon_stock(j,"forestry",…)` — i.e. M32's *afforestation* and *NDC* curves are uncalibrated but its *timber plantations* are calibrated** (M32's preloop references at `preloop.gms:18,56` run before M52's preloop and therefore see uncalibrated values); M35 for secdforest carbon density, which it BLENDS with the uncalibrated curve by natural-origin area share (`modules/35_natveg/pot_forest_may24/presolve.gms:248-252`)."

---

### BUG-2 — Major — `default_value` — wildfire disturbance is OFF in a default run — **[re-derived]**

**Doc** (`carbon_balance_conservation:870`, §10.2 item 6 "No Fire Emissions Separately"; same premise at `:221` and `:626`):
> "Fire disturbances (Module 35) cause carbon loss via stock change / But emissions lumped with general LUC emissions"
> (`:626`) "Disturbances (fire, shifting agriculture) → reset age classes → carbon loss"

**Reality**: `s35_forest_damage` defaults to **2** (`modules/35_natveg/pot_forest_may24/input.gms:27`, confirmed `config/default.cfg:1184`). Branch 2 applies **only** the `shifting_agriculture` share and fades it to zero:

```
modules/35_natveg/pot_forest_may24/presolve.gms:19-22
if(s35_forest_damage=2,
  p35_disturbance_loss_secdf(t,j,ac_sub) = pc35_secdforest(j,ac_sub)
    * sum(cell(i,j),f35_forest_lost_share(i,"shifting_agriculture"))
    * m_timestep_length_forestry * (1 - p35_damage_fader(t));
```

The fader runs 0→1 between `sm_fix_SSP2` and `s35_forest_damage_end` (`m_sigmoid_time_interpol(p35_damage_fader,sm_fix_SSP2,s35_forest_damage_end,0,1)`, `modules/35_natveg/pot_forest_may24/preloop.gms:88`), so `(1 - fader)` decays to **zero by 2050** (`config/default.cfg:1186`).

The `wildfire` member of `driver_source` (`modules/35_natveg/pot_forest_may24/sets.gms:10-12`) enters **only** through `combined_loss` (`sets.gms:14-15`) under `s35_forest_damage = 3` (`presolve.gms:24-27`) — a value the scalar's own description string does not even list. The generic shock branch (`= 4`) needs `c35_shock_scenario ≠ "none"`, and the default is `"none"` (`config/default.cfg:1200`).

So in a default run **no wildfire disturbance is applied at all**, and the one disturbance stream that does run is faded out after 2050. This is the capability-vs-default class AGENT.md names as the second-largest measured defect type, and its canonical anti-example ("MAgPIE models fire disturbance" — it does not).

**Tier note**: the rubric's Critical trigger "active mechanism claimed when actually OFF by default" fires for `wildfire`. I hold it at **Major** under the §1 tie-breaker, because the branch that *is* active is called "shifting agriculture fires" in the code's own header (`presolve.gms:9`), so "fire disturbances cause carbon loss" is not wholly false before 2050. `tier_uncertainty: true`.

**verify_cmd**:
```
grep -n "s35_forest_damage" modules/35_natveg/pot_forest_may24/input.gms  → :27 ... / 2 /
grep -n "s35_forest_damage\|c35_shock_scenario" config/default.cfg        → 1184 (2), 1186 (2050), 1200 ("none")
rg -n "p35_damage_fader" modules/35_natveg/pot_forest_may24/*.gms         → preloop.gms:88 (0→1 sigmoid), presolve.gms:20,21
sed -n '10,15p' modules/35_natveg/pot_forest_may24/sets.gms               → wildfire ∈ driver_source; combined_loss = {shifting_agriculture, wildfire}
```

**Proposed fix** at `:870`:
> "Disturbance losses (Module 35) cause carbon loss via stock change, but **which** disturbance depends on `s35_forest_damage` (default **2**, `config/default.cfg:1184`): only the `shifting_agriculture` share of `f35_forest_lost_share` is applied, faded to zero by `s35_forest_damage_end = 2050`. The `wildfire` driver is applied **only** at `s35_forest_damage = 3` (`modules/35_natveg/pot_forest_may24/presolve.gms:24-27`), and the generic shock scenarios only at `= 4` with `c35_shock_scenario ≠ none`. Even when enabled, emissions are lumped with general LUC emissions, so fire cannot be tracked separately."
Apply the same qualification at `:221` and `:626`.

---

### BUG-3 — Major — `attribution_read` — §7.1's M52 "Receives" list omits two upstream interfaces — **[independent; not in prior pass]**

**Doc** (`carbon_balance_conservation:518-519`, §7.1 "Module 52 (Carbon) — Central Data Provider"):
> "**Receives**: - `vm_carbon_stock(j,land,c_pools,"actual")`: Current carbon stocks from all land modules"

**Reality**: since the FRA-2025 calibration landed, M52's preloop reads **two further interfaces the doc never names**, and the reads are phase-order-sensitive:

- `im_forest_ageclass(j,ac)` — declared and populated in **Module 28** (`modules/28_ageclass/oct24/declarations.gms:9`, `preloop.gms:11,14`); read by M52 at `modules/52_carbon/normal_dec17/preloop.gms:53,55,59` as the age-class weight in the secdforest `k` bisection.
- `pm_land_plantation(j,ac)` — declared and populated in **Module 32** (`modules/32_forestry/dynamic_may24/declarations.gms:59`, `preloop.gms:179`); read by M52 at `modules/52_carbon/normal_dec17/preloop.gms:88,90,94` as the weight in the plantation `k` bisection.

The code states the ordering constraint itself: `modules/52_carbon/normal_dec17/preloop.gms:14` — "This runs in preloop (after module 28 preloop has populated `im_forest_ageclass`)". Ordering holds because `modules/include.gms` runs 28 → 32 → 52 in numeric order.

This also means **M32 ↔ M52 is now a two-way loop** — M32 supplies `pm_land_plantation` → M52 calibrates `pm_carbon_density_plantation_ac` → M32 reads it back in presolve (BUG-1). §7 presents M52 as a pure upstream provider and shows no inbound arrow from M28 or M32 anywhere.

**verify_cmd**:
```
grep -rn "im_forest_ageclass\|pm_land_plantation" modules/52_carbon/
→ preloop.gms:53,55,59 (im_forest_ageclass); preloop.gms:88,90,94 (pm_land_plantation); comments :11,:14,:36,:77
Role map: im_forest_ageclass.read_by = ["28","35","52"]; pm_land_plantation.read_by = ["32","52"]  (agrees)
```

**Proposed fix**: extend §7.1 "Receives" to —
> "- `vm_carbon_stock(j,land,c_pools,"actual")` — current carbon stocks from all land modules
>  - `im_forest_ageclass(j,ac)` (**Module 28**) — GFAD age distribution weighting the secdforest `k` bisection (`modules/52_carbon/normal_dec17/preloop.gms:53-59`)
>  - `pm_land_plantation(j,ac)` (**Module 32**) — plantation age distribution weighting the plantation `k` bisection (`modules/52_carbon/normal_dec17/preloop.gms:88-94`); this closes a loop, since M32 reads the calibrated plantation curve back in presolve (§3.3)
>  - `pm_climate_class(j,clcl)` (**Module 45**) — climate shares for the uncalibrated k/m
>
> Ordering: M52's preloop must run after M28's and M32's (`modules/include.gms` runs modules in numeric order)."

---

### BUG-4 — Major — `formula` — §6.3 growth table does not follow from its own stated parameters — **[re-derived]**

**Doc** (`carbon_balance_conservation:485-500`): "**Illustrative Example** (tropical plantation): A = 100 tC/ha, **k = 0.06, m = 2.0**", then a table of 14 / 26 / 44 / 58 / 75 / 88 / 93 tC/ha at 5 / 10 / 20 / 30 / 50 / 80 / 100 years.

**Reality**: the model's growth macro — quoted correctly by the doc at `:450` — is
`$macro m_growth_vegc(S,A,k,m,ac) S + (A-S)*(1-exp(-k*(ac*5)))**m` (`core/macros.gms:18`).
With A = 100, k = 0.06, m = 2.0 it yields **6.7 / 20.4 / 48.8 / 69.7 / 90.3 / 98.4 / 99.5** — off by 2.1× at 5 years. Worse, the tabulated numbers are a **monomolecular** curve (`≈100·(1−e^(−0.03t))`, i.e. m = 1: 13.9 / 25.9 / 45.1 / 59.3 / 77.7 / 90.9 / 95.0), whose shape is fastest-at-t=0 — the opposite of the sigmoid the doc asserts 330 lines later at `:828-831` ("Should follow sigmoidal pattern / Young plantations: slow growth"). §8.2 (`:676`, `:682`) reuses 44 and 75 and attributes them to Chapman-Richards.

The "illustrative" label covers the *choice* of parameters, not the arithmetic linking stated parameters to stated outputs; a reader checking the implementation against this table would wrongly conclude the code is broken.

**verify_cmd**:
```
python3 -c "import math;A,k,m=100,0.06,2.0;print([round(A*(1-math.exp(-k*y))**m,1) for y in (5,10,20,30,50,80,100)])"
→ [6.7, 20.4, 48.8, 69.7, 90.3, 98.4, 99.5]      (doc: [14, 26, 44, 58, 75, 88, 93])
python3 -c "import math;print([round(100*(1-math.exp(-0.03*y)),1) for y in (5,10,20,30,50,80,100)])"
→ [13.9, 25.9, 45.1, 59.3, 77.7, 90.9, 95.0]     (matches the doc's table ⇒ the table is m=1, k=0.03)
```

**Proposed fix**: recompute the table from `m_growth_vegc` at the stated k = 0.06, m = 2.0 (0 / 6.7 / 20.4 / 48.8 / 69.7 / 90.3 / 98.4 / 99.5 / ~100), or restate the parameters as k = 0.03, m = 1.0 and drop the "sigmoidal" characterisation. Propagate the corrected 20-year and 50-year values into §8.2 (`:676`, `:682`) and the sequestration totals at `:688-689`.

---

### BUG-5 — Major — `attribution_read` — `vm_maccs_costs` has a second consumer — **[independent]**

**Doc** (`carbon_balance_conservation:593`, §7.4 "Module 57 — Provides"):
> "`vm_maccs_costs(i,factors)`: Labor and capital costs of mitigation **→ to Module 11**"

**Reality**: two consumers, not one. Module 36 reads the `"labor"` element to convert mitigation labour spending into employment:

- `modules/11_costs/default/equations.gms:28` — `+ sum(factors,vm_maccs_costs(i2,factors))`
- `modules/36_employment/exo_may22/equations.gms:28` — `=e= (vm_maccs_costs(i2,"labor")) * (1 / sum(ct,f36_weekly_hours(ct,i2)*s36_weeks_in_year*pm_hourly_costs(ct,i2,"scenario")));`

M36 has a single realization (`exo_may22`) and is active by default (`config/default.cfg:1212`), so this is not a non-default path. A reader doing modification-impact analysis on M57 from this doc would miss M36.

**verify_cmd**:
```
rg -n "vm_maccs_costs\(" modules/ core/   → 11_costs:28, 36_employment:28, 57_maccs decl+eqs 36,46
rg -n "vm_maccs_costs\."  modules/ core/   → 57 postsolve/scaling only (no hidden .l/.lo reads)
grep -rn "vm_maccs_costs" modules/36_employment/   (2nd method) → equations.gms:28
grep -rn "vm_cost_prod"   modules/36_employment/   (positive control) → equations.gms:24
Role map: vm_maccs_costs.read_by = ["11","36","57"]  (agrees)
```

**Proposed fix**: "→ to Module 11 (total costs, `modules/11_costs/default/equations.gms:28`) **and Module 36** (labor slice → employment, `modules/36_employment/exo_may22/equations.gms:28`)".

---

### BUG-6 — Major — `attribution_read` — M53's CH₄ also flows back to Module 57 — **[independent]**

**Doc** (`carbon_balance_conservation:573`, §7.3 "Module 53 — Provides"):
> "`vm_emissions_reg(i,emis_source,"ch4")`: Regional CH₄ emissions **→ to Module 56**"

**Reality**: Module 57 reads the same interface to size the MACC cost integral, dividing out the mitigation factor to recover baseline emissions:

- `modules/57_maccs/on_aug22/equations.gms:38` (labor) and `:48` (capital) — `* vm_emissions_reg(i2,emis_source,pollutants_maccs57) / (1 - im_maccs_mitigation(ct,i2,emis_source,pollutants_maccs57))`
- `pollutants_maccs57(pollutants) / ch4, n2o_n_direct /` (`modules/57_maccs/on_aug22/sets.gms:25-26`) — so CH₄ is in scope.

This closes a loop the doc presents as one-way (§7.3 "Receives `im_maccs_mitigation` from Module 57"; §7.4 "Provides `im_maccs_mitigation`"): M57 → `im_maccs_mitigation` → M53 → `vm_emissions_reg` → M57's cost equations. §7.4 has no "Receives" list at all.

**verify_cmd**:
```
rg -n "vm_emissions_reg" modules/56_ghg_policy/ modules/57_maccs/
→ 57_maccs/on_aug22/equations.gms:38,40,48,50 ; 56_ghg_policy: equations.gms:17 + declarations/postsolve only
Role map: vm_emissions_reg.read_by = ["56","57"]  (agrees)
```

**Proposed fix**: "→ to Module 56 for pricing (`modules/56_ghg_policy/price_aug22/equations.gms:15-17`) **and back to Module 57**, which divides out the mitigation factor to recover baseline emissions for the MACC cost curves (`modules/57_maccs/on_aug22/equations.gms:38,48`; `ch4 ∈ pollutants_maccs57`, `modules/57_maccs/on_aug22/sets.gms:25-26`). M53 and M57 are mutually dependent." Add a matching "Receives" bullet to §7.4.

---

### BUG-7 — Major — `formula` — §8.4's five-year convergence uses the legacy share — **[independent]**

**Doc** (`carbon_balance_conservation:734`):
> "- Year 5: **44%** toward new equilibrium = **+4 tC/ha**"

**Reality**: `i59_lossrate(t) = 1-0.85**m_yeardiff(t)` (`modules/59_som/cellpool_jan23/preloop.gms:45`) gives `1-0.85^5 = 0.5563` → **56% toward equilibrium**; 44% is the *remaining legacy* share. The doc's own §5.2 table (`:401`) and interpretation (`:412`) state this correctly, so §8.4 contradicts §5.2. With the stated +9 tC/ha equilibrium gain, year 5 is **+5 tC/ha**, not +4. The neighbouring rows are right (year 10 → 80% → +7.2; year 20 → 96% → +8.6), which isolates the defect to the year-5 row. The convergence percentage is a model quantity, not part of the "made-up cropland area" the section's caveat covers.

Origin note: the upstream code comment makes the same slip — `modules/59_som/cellpool_jan23/preloop.gms:42` says "44% in 5 years, 80% in 10 years and 96% in 20 years", internally inconsistent (44% is remaining, 80/96% are converged). The formula, not the comment, is authoritative — flag this in the fix so a future reader checking only the comment does not revert it.

**verify_cmd**:
```
python3 -c "print([(y, round(1-0.85**y,4)) for y in (1,5,10,20)])"
→ [(1,0.15), (5,0.5563), (10,0.8031), (20,0.9612)]
python3 -c "print(0.44*9, round((1-0.85**5)*9,2))"  → 3.96   5.01
```

**Proposed fix**: "- Year 5: 56% toward new equilibrium = +5 tC/ha", plus a footnote that `preloop.gms:42`'s "44% in 5 years" is the legacy share.

---

### BUG-8 — Minor — `mechanism` — cropland soil-carbon equilibrium is not driven by modelled residue production — **[re-derived]**

**Doc** (`carbon_balance_conservation:122`): "Crop-specific equilibrium based on **residue production**"; and (`:434`) "**Crop-specific**: Different crops produce different residue amounts".

**Reality**: `q59_som_target_cropland` (`modules/59_som/cellpool_jan23/equations.gms:20-27`) contains no residue term — no `vm_res_*`, no residue variable of any kind. A grep of `vm_res|res_ag|residue` across `modules/59_som/cellpool_jan23/*.gms` returns only three prose comments (`input.gms:22,23`, `preloop.gms:86`) and zero code references (positive control: `vm_area` appears 3× in the same `equations.gms`). Crop specificity is an exogenous lookup: `f59_cratio_landuse(i,climate59_2019,kcr)` (`modules/59_som/cellpool_jan23/input.gms:43-47`, read from `f59_ch5_F_LU_2019reg.cs3`), combined into `i59_cratio` at `preloop.gms:60-67`. Residue *inputs* are conceptually the IPCC **FI** factor, which MAgPIE pins at `medium_input` (`preloop.gms:55`) with no link to modelled residue flows. This is the parameterization-vs-mechanism distinction AGENT.md makes binding.

**verify_cmd**:
```
grep -rn "vm_res\|res_ag\|residue" modules/59_som/cellpool_jan23/*.gms
→ input.gms:22,23 and preloop.gms:86 — all prose comments, no code
grep -c "vm_area" modules/59_som/cellpool_jan23/equations.gms  (positive control) → 3
```

**Proposed fix**: "Crop-specific equilibrium via exogenous IPCC FLU stock-change factors per MAgPIE crop type (`f59_cratio_landuse`, `modules/59_som/cellpool_jan23/input.gms:43-47`) — the crop dependence is a **lookup**, not a function of modelled residue production." Same correction at `:434`.

---

### BUG-9 — Minor — `attribution_populate` — urban vegc/litc zeroing attributed to Module 52 — **[re-derived]**

**Doc** (`carbon_balance_conservation:263-264`, §3.7 table): rows "vegc | Fixed to zero | None | **52**" and "litc | Fixed to zero | None | **52**".

**Reality**: Module 52 contains nothing that zeroes urban vegc or litc. A grep of `urban` across `modules/52_carbon/normal_dec17/` returns only the **soilc** override (`input.gms:33-35`, `fm_carbon_density(t_all,j,"urban","soilc") = fm_carbon_density(t_all,j,"other","soilc")`) and a realization-doc mention. The zeroing is Module 34: `vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0` (`modules/34_urban/exo_nov21/presolve.gms:8`) — which the doc itself states correctly at §7.5 `:622`, so the table contradicts §7.5. The soilc row's "52, 59" is right.

**verify_cmd**:
```
grep -rn "urban" modules/52_carbon/normal_dec17/  → input.gms:33,34,35 (soilc only), realization.gms:10, preloop.gms:41 (unrelated)
rg -n "vm_carbon_stock\." modules/ core/          → 34_urban/exo_nov21/presolve.gms:8 is the only urban .fx
```

**Proposed fix**: change the Module column for the vegc and litc rows from `52` to `34`, citing `modules/34_urban/exo_nov21/presolve.gms:8`, matching §7.5.

---

### BUG-10 — Minor — `attribution_populate` — `pcm_carbon_stock` has two populators and the doc names neither — **[independent]**

**Doc** (`carbon_balance_conservation:101`): "The **two readers** then pick different slices"; (`:296`, §4.1 Components): "**Previous stock**: `pcm_carbon_stock` — from end of previous timestep"; §7.2 "Provides" (`:538-542`) omits it.

**Reality**: `pcm_carbon_stock` — the parameter that carries the previous timestep into M52's core emission equation — is populated by **two** modules, split by pool, via solution-level reads invisible to a `vm_carbon_stock(` grep:

- `modules/56_ghg_policy/price_aug22/postsolve.gms:8` — `pcm_carbon_stock(j,land,ag_pools,stockType) = vm_carbon_stock.l(j,land,ag_pools,stockType);` (**vegc + litc only**)
- `modules/59_som/cellpool_jan23/postsolve.gms:13` — `pcm_carbon_stock(j,land,"soilc",stockType) = vm_carbon_stock.l(j,land,"soilc",stockType);` (**soilc**)

That same `.l` read also makes M59 a third reader of `vm_carbon_stock`, so "the two readers" at `:101` and "All populated slices flow to Module 52 and Module 56" at `:632` are incomplete (they are correct for *equation-level* readers). Per-slice ownership of an interface is exactly what the DECLARED/POPULATED/READ mandate targets.

**verify_cmd**:
```
rg -n "vm_carbon_stock\." modules/ core/
→ 56/postsolve.gms:8 (ag_pools), 59/cellpool_jan23/postsolve.gms:13 (soilc), 34/presolve.gms:8 (.fx),
  31/static/presolve.gms:15 (.fx, non-default), 56/preloop.gms:11, 59/preloop.gms:32,35, 56/scaling.gms:10
Role map: pcm_carbon_stock.populated_by = ["56","59"], read_by = ["52","56","59"]  (agrees)
```

**Proposed fix**: at `:101` write "the two readers **in the optimization**"; add to §7.2 "Provides" and cross-reference from §4.1: "`pcm_carbon_stock` is written in postsolve — above-ground pools by Module 56 (`modules/56_ghg_policy/price_aug22/postsolve.gms:8`), the soilc slice by Module 59 (`modules/59_som/cellpool_jan23/postsolve.gms:13`) — both by solution-level (`.l`) read of `vm_carbon_stock`."

---

### BUG-11 — Minor — `citation` — `config/default.cfg` line drift on the unreachable-switch warning — **[independent]**

**Doc** (`carbon_balance_conservation:101`): "Do **not** cite `config/default.cfg:1835` for this default: that line omits the `cfg$gms$` prefix its siblings carry…"

**Reality**: the prefix-less assignment is at **`config/default.cfg:1838`**; line 1835 is a comment (`# *   actual: CO2 emissions for pricing are based on the difference of actual carbon stocks between time steps`). The substantive claim still holds — `c56_carbon_stock_pricing <- "actualNoAcEst"` at `:1838` lacks the `cfg$gms$` prefix that `cfg$gms$c56_emis_policy` (`:1831`) and `cfg$gms$maccs` (`:1843`) carry, and a whole-repo grep finds no other producer, so GAMS falls back to `$setglobal` (`modules/56_ghg_policy/price_aug22/input.gms:90`). Only the line number drifted (+3).

**verify_cmd**:
```
grep -n "c56_carbon_stock_pricing" config/default.cfg  → 1838:c56_carbon_stock_pricing <- "actualNoAcEst"
sed -n '1835p' config/default.cfg                      → "# *   actual: CO2 emissions ..."  (comment)
rg -n "c56_carbon_stock_pricing" .                     → only 56 realization/input/equations, CHANGELOG:891, config:1838
```

**Proposed fix**: `config/default.cfg:1835` → `config/default.cfg:1838`.

---

### BUG-12 — Minor — `set_membership` — four parameter signatures given over `t` instead of `t_all` — **[independent; not in prior pass]**

**Doc**: `:107` "`fm_carbon_density(t,j,land,c_pools)`"; `:513-516` "`pm_carbon_density_plantation_ac(t,j,ac,ag_pools)`", "`pm_carbon_density_secdforest_ac(t,j,ac,ag_pools)`", "`pm_carbon_density_other_ac(t,j,ac,ag_pools)`"; same form at `:699`.

**Reality**: all four are declared over **`t_all`**, not `t`:
- `modules/52_carbon/normal_dec17/input.gms:16` — `table fm_carbon_density(t_all,j,land,c_pools)`
- `modules/52_carbon/normal_dec17/declarations.gms:9,11,12` — `pm_carbon_density_secdforest_ac(t_all,j,ac,ag_pools)`, `pm_carbon_density_other_ac(t_all,j,ac,ag_pools)`, `pm_carbon_density_plantation_ac(t_all,j,ac,ag_pools)`

`t ⊂ t_all` (optimised time steps vs all years), and M52 populates these across the full `t_all` range in `start.gms`/`preloop.gms`. A reader copying these signatures into new code would under-declare. Consumers correctly index with `t` when reading inside the loop — the defect is in the reported *declaration*, not the reads.

**verify_cmd**:
```
rg -n "pm_carbon_density_(plantation|secdforest|other)_ac" modules/52_carbon/normal_dec17/declarations.gms
→ lines 9-13, all (t_all,j,ac,ag_pools)
sed -n '16p' modules/52_carbon/normal_dec17/input.gms → table fm_carbon_density(t_all,j,land,c_pools)
```

**Proposed fix**: replace `(t,` with `(t_all,` in those four signatures at `:107`, `:513-516`, `:699`, keeping `t`-indexed forms only where the doc quotes a *read* inside the time loop.

---

### BUG-13 — Minor — `citation` — stale line range for the Module 52 growth code — **[re-derived]**

**Doc** (`carbon_balance_conservation:987`, References): "Module 52 growth: `modules/52_carbon/normal_dec17/start.gms:8-39`"

**Reality**: `start.gms` is 51 lines and the growth code spans `:8-51`. Lines 33-44 are calibration-parameter initialization and the uncalibrated-curve snapshot (`:43-44`, which the doc cites elsewhere), and the other-land curves are at `:46-51` — outside the cited range.

**verify_cmd**:
```
wc -l < modules/52_carbon/normal_dec17/start.gms  → 51
sed -n '46,51p' modules/52_carbon/normal_dec17/start.gms → pm_carbon_density_other_ac vegc/litc assignments
```

**Proposed fix**: `start.gms:8-39` → `start.gms:8-51`.

---

## Deferred (not filed as bugs — unverified, or judgment calls)

- **`m_carbon_stock_ac` is the mechanism behind the two `stockType` slices, and the doc never says so.** `:101` says "the populating equations are indexed over the free set and fill **both** slices" — true, but not with the same value: `core/macros.gms:104-106` sums `actual` over the full `ac` set and `actualNoAcEst` over `ac_sub` (dropping newly established age classes), while the non-age-class `m_carbon_stock` (`:99-101`) is identical in both. Not filed as a bug because the doc's sentence is not false; worth adding as a clarification if the file is edited anyway.
- **M32's `p32_carbon_density_ac_forestry` (`preloop.gms:18`) and `p32_avg_increment` (`:56`) are built from the *uncalibrated* plantation curve** (phase ordering, see BUG-1) while `p32_carbon_density_ac(...,"plant",...)` (`presolve.gms:65`) is calibrated. Whether that intra-M32 split is intentional is an upstream-MAgPIE question, not a doc defect — flagged as an unverified lead only.
- §7.3's "Receives" for M53 omits `vm_manure` (M55, `modules/53_methane/ipcc2006_aug22/equations.gms:50`) and `vm_res_ag_burn` (M18, `:72`); §7.2's for M59 omits `vm_landexpansion` (M10, `modules/59_som/cellpool_jan23/equations.gms:91`), `pcm_land` and `pm_land_start`. Real reads, but the lists read as illustrative and the omitted vars sit outside the carbon balance.
- §7.2 (`:547`) "`vm_land(j,land)`: Non-cropland areas from Module 10" understates it: M59 also uses `vm_land` over **all** land in `q59_carbon_soil` (`equations.gms:63`), and `vm_land` is populated by 10/29/31/32/34/35, not M10 alone. Direction and origin are right; too soft to flag.
- §3.1 (`:140`) / §5.3 (`:428`) describe FLU as "Cropland / Set-aside / Perennial". `f59_cratio_landuse` is indexed by MAgPIE crop type `kcr` with no set-aside member; fallow is handled separately with `"maiz"` FLU + reduced tillage + low input (`modules/59_som/cellpool_jan23/preloop.gms:73-77`). Reads as IPCC nomenclature rather than a code claim. (FMG and FI **do** map exactly onto `tillage59` and `inputs59`, `sets.gms:13-17`.)
- §8.1 (`:656`) "Gradual (soilc over 20 years): 30 tC/ha × 100 Mha × (44/12) / 20 years = **458** Tg CO₂/year" — the arithmetic gives **550** (458 corresponds to 25 tC/ha, but the table at `:649` states 30). The immediate-emission figure on the previous line (56,833) checks out exactly. Not filed separately because the whole block is explicitly "made-up numbers for illustration"; fold the `458 → 550` correction into any edit of §8.1.
- §8.4 (`:730`) "SCM equilibrium … high input factor = 1.17" vs code, which uses `high_input_nomanure` for SCM (`modules/59_som/cellpool_jan23/preloop.gms:86-90`) while §5.3's 1.17 anchor is "High input **+ manure**". Both labelled illustrative; I could not read the `f59_ch5_F_I.csv` factor values, so I cannot say which is numerically right.
- §7.4 (`:592`) "`im_maccs_mitigation` … Mitigation fractions (0 to ~0.3)" — range depends on `f57_maccs_*` input data I did not read.
- §9.1's R snippet passes `field="l"` to `readGDX` for `pcm_carbon_stock` (a parameter) and combines `select=list(type="level")` with `field="l"` for `ov_carbon_stock`. Possibly wrong R, but outside GAMS ground truth and outside this lens — not verified. The variable names it uses (`ov_carbon_stock`, `ov59_som_pool`, `ov59_som_target`, `ov32_land`, `pm_carbon_density_plantation_ac`) all exist.
- Several citations inside the two calibration warning boxes drop the `modules/` prefix (`14_yields/…`, `29_cropland/…`, `32_forestry/…`, `35_natveg/…`, `normal_dec17/preloop.gms:71-73`), against the full-path convention in MANDATE 16. Style, not content.
- `im_vol_conv` (M52 → M73, `modules/52_carbon/normal_dec17/preloop.gms:20-21,40`) is absent from §7.1's "Provides". Out of scope for a carbon-balance doc.
- The doc's own assertion that `c56_carbon_stock_pricing` "is currently unreachable from config" — I re-confirmed both premises this session (no `cfg$gms$` prefix at `config/default.cfg:1838`; no other producer in a whole-repo grep incl. `scripts/` and `.R`) but did **not** run the model to confirm the R-side consequence empirically.

## Method notes

- Every absence claim was cross-checked with a second tool (`rg` and `grep`) plus a positive control in the same directory; every probe was issued as its own standalone command (no chained `find -exec … +`).
- Both grep forms (`NAME(` and `NAME.`) were run for every interface variable named in the doc. That is what surfaced BUG-10 (M59's `.l` postsolve read of `vm_carbon_stock`, invisible to `vm_carbon_stock(`).
- Phase ordering for BUG-1 and BUG-3 was derived from `core/calculations.gms:13-15` (`start` → `preloop` → time loop → `presolve`) plus `modules/include.gms:12-57` (strict numeric module order), not assumed.
- Data-flow direction was checked at both endpoints for every "A → B" claim; the doc's parallel-not-serial claim at `:583` survived, and BUG-3/BUG-6 are cases where the doc showed one arrow where the code has two.
