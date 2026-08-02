# Adversarial verification — `cross_module/carbon_balance_conservation.md`

**Round**: 60 (depth)
**Target doc**: `cross_module/carbon_balance_conservation.md` (1007 lines)
**Ground truth**: read-only MAgPIE `develop` worktree at `2c02843ec` (same HEAD as the local checkout)
**Role map**: `audit/integrated/depth_rolemap.json`
**Bugs adjudicated**: 21

## Verdict summary

| Bug | Class | Citation | Verdict |
|-----|-------|----------|---------|
| :1  | mechanism | OK | **UPHELD** |
| :2  | formula_or_value | OK | **CORRECTED** |
| :3  | mechanism | OK | **UPHELD** |
| :4  | mechanism | OK | **CORRECTED** |
| :15 | consumer_set | OK | **UPHELD** |
| :16 | mechanism | OK | **UPHELD** |
| :17 | mechanism | OK | **UPHELD** |
| :18 | consumer_set | OK | **UPHELD** |
| :19 | formula_or_value | OK | **CORRECTED** |
| :20 | consumer_set | OK | **UPHELD** |
| :21 | consumer_set | OK | **UPHELD** |
| :22 | formula_or_value | OK | **UPHELD** |
| :30 | mechanism | OK | **UPHELD** |
| :31 | consumer_set | OK | **UPHELD** |
| :42 | consumer_set | OK | **CORRECTED** |
| :43 | formula_or_value | OK | **UPHELD** |
| :44 | formula_or_value | OK | **UPHELD** |
| :54 | consumer_set | OK | **CORRECTED** |
| :55 | mechanism | OK | **UPHELD** |
| :56 | mechanism | OK | **UPHELD** |
| :57 | mechanism | OK | **UPHELD** |

Zero CITATION_FAILED. Every `file:line` in every `file_evidence` block resolved to a real file, in range, containing the claimed token. That is unusual for this corpus and is itself worth recording.

---

## The one finding that would have introduced a NEW error

Bugs **:42** and **:54** both propose adding `modules/32_forestry/dynamic_may24/preloop.gms:18,56` to the list of **calibrated**-curve readers. **That is wrong**, and bug **:15** — which flags exactly this trap — is right.

Mechanically established phase ordering:

```
core/calculations.gms:13   $batinclude "./modules/include.gms" start     <- ALL modules, start phase
core/calculations.gms:15   $batinclude "./modules/include.gms" preloop   <- ALL modules, preloop phase
modules/include.gms:12+    modules included in NUMERIC order (09,10,...,32,...,52,...)
```

Each realization dispatches on `%phase%` (`modules/32_forestry/dynamic_may24/realization.gms:44-45`, `modules/52_carbon/normal_dec17/realization.gms:32-33`). Therefore:

- `modules/52_carbon/normal_dec17/start.gms:17` writes the **uncalibrated** plantation curve (start phase).
- `modules/32_forestry/dynamic_may24/preloop.gms:18,56` read it (preloop phase, module 32) — **still uncalibrated**.
- `modules/52_carbon/normal_dec17/preloop.gms:114` overwrites it with the FRA-2025-calibrated curve (preloop phase, module 52 — later).
- `modules/32_forestry/dynamic_may24/presolve.gms:65` reads it inside the time loop — **calibrated**.

Extra nail: `preloop.gms:56` sits in the `$elseif "%c32_rot_calc_type%" == "mean_annual_increment"` branch, and the default is `current_annual_increment` (`config/default.cfg:1133`, `modules/32_forestry/dynamic_may24/input.gms:15`), so it is not even compiled in a default run.

**Apply bug :15's fix text. Do not apply :42's or :54's `preloop.gms:18,56` clause.**

---

## Per-bug verification

### :1 / :16 / :30 / :56 — primforest carbon density is NOT static (mechanism) — **UPHELD** (all four)

Citations, all verified by direct line read:

- `modules/52_carbon/normal_dec17/input.gms:8` = `$setglobal c52_carbon_scenario  cc`
- `:16` = `table fm_carbon_density(t_all,j,land,c_pools) LPJmL carbon density...`
- `:22` = `$if "%c52_carbon_scenario%" == "nocc" fm_carbon_density(t_all,...) = fm_carbon_density("y1995",...)`
- `:23` = the `nocc_hist` partial freeze
- `config/default.cfg:1590` = `cfg$gms$c52_carbon_scenario  <- "cc"   # def = "cc"`
- `core/macros.gms:99-101` = `m_carbon_stock(...)` expanding to `land(j2,item) * sum(ct,carbon_density(ct,j2,item,ag_pools))`
- `modules/35_natveg/pot_forest_may24/equations.gms:42-44` = `q35_carbon_primforest ... =e= m_carbon_stock(vm_land,fm_carbon_density,"primforest")`
- `modules/59_som/cellpool_jan23/equations.gms:31-34` = `q59_som_target_noncropland ... vm_land(j2,noncropland59) * sum(ct,f59_topsoilc_density(ct,j2))`; `config/default.cfg:1951` = `c59_som_scenario <- "cc"`

Independent check for a primforest-specific freeze: `grep -rn "primforest" modules/52_carbon/` returns only two **comment** lines (`normal_dec17/preloop.gms:36,38`) about age-class decomposition. Positive control: `grep -rln "fm_carbon_density" modules/52_carbon/` returns `start.gms`, `input.gms`, `preloop.gms` — the search works in that directory. No freeze exists.

`primforest_vegc/_litc/_soilc` are members of `emis_oneoff` (`core/sets.gms:314-318`), so the time-varying density does propagate into `q52_emis_co2_actual`.

Doc lines confirmed verbatim: `:194-196` (three "Static" cells), `:201`, `:841`. Self-contradiction confirmed at `:697-700` ("Module 52 updates `fm_carbon_density` over time / Carbon stocks change even without land-use change").

Verdict: the doc claim is false under the default. All four bugs describe the same real defect; **:56** has the most complete evidence (it is the only one that also covers the `soilc` half via M59 and both `nocc`/`nocc_hist` gates). **:1** is the least complete (omits `nocc_hist`) but is not wrong.

### :2 / :19 — Chapman-Richards illustrative table (formula) — **CORRECTED** (both)

`core/macros.gms:18` = `$macro m_growth_vegc(S,A,k,m,ac) S + (A-S)*(1-exp(-k*(ac*5)))**m;` — verified.
`modules/52_carbon/normal_dec17/start.gms:17,28,48` all call it with `(ord(ac)-1)` — verified.
Doc `:485-487` states A=100, k=0.06, m=2.0; doc `:490-500` is the table — verified verbatim.

Recomputed independently at years 0/5/10/20/30/50/80/100/150:

```
k=0.06, m=2  ->  0.0  6.7  20.4  48.8  69.7  90.3  98.4  99.5  100.0
k=0.03, m=1  ->  0.0 13.9  25.9  45.1  59.3  77.7  90.9  95.0   98.9
doc table    ->  0   14    26    44    58    75    88    93    ~100
```

**Core finding UPHELD**: the table does not come from the stated parameters (2.1x error at year 5).

**Correction**: both bugs' fallback remedy — "restate the parameters as k=0.03, m=1.0" — does **not** reproduce the table either. The doc's numbers fall systematically 2-3 points *below* the k=0.03/m=1 curve from year 30 on (75 vs 77.7; 88 vs 90.9; 93 vs 95.0). The table matches no exact (k, m) pair; it is a hand-drawn concave curve. Bug :19's hedged phrasing ("~100*(1-exp(-0.03t))") is defensible as a *shape* statement; bug :2's flat "matches k=0.03, m=1" is not.

Bug :19's ancillary claims verified: the doc's own `:828-831` asserts a sigmoidal shape ("Young plantations: slow growth / Middle age: rapid growth"), which is true for m=2 and false for m=1 — so the "restate the parameters" option would create a new internal contradiction. Downstream propagation confirmed at `:676` (44), `:682` (75), `:688-689` (totals 3,200 / 5,400 Tg C).

**Apply**: recompute the table from the stated k=0.06, m=2.0. Do not take the "restate the parameters" branch.

### :3 / :17 / :55 — fire/disturbance is not active in a default run (mechanism) — **UPHELD** (all three)

Verified by direct read:

- `modules/35_natveg/pot_forest_may24/input.gms:27` = `s35_forest_damage ... (0=none 1=shifting agriculture 2= Damage from shifting agriculture is faded out by c35_forest_damage_end 4= f35_forest_shock scenario) / 2 /` — **the switch's own description omits 3**
- `:28` = `s35_forest_damage_end ... / 2050 /`
- `presolve.gms:19-22` = the `s35_forest_damage=2` branch, `f35_forest_lost_share(i,"shifting_agriculture")` only, `*(1 - p35_damage_fader(t))`
- `presolve.gms:24-27` = the `s35_forest_damage=3` branch, the **only** use of `combined_loss`
- `presolve.gms:30-33` = the `=4` branch, gated on `%c35_shock_scenario%`
- `presolve.gms:36-39` = the age-class reset (real mechanism, correctly described)
- `preloop.gms:88` = `m_sigmoid_time_interpol(p35_damage_fader,sm_fix_SSP2,s35_forest_damage_end,0,1)` -> fader 0->1 by 2050, so `(1-fader)` -> 0
- `sets.gms:10-12` `driver_source` (includes `wildfire`); `sets.gms:14-15` `combined_loss / shifting_agriculture,wildfire /`
- `config/default.cfg:1180-1183` lists options 0/1/2/4 only; `:1184` = `s35_forest_damage <- 2`; `:1186` = `2050`; `:1200` = `c35_shock_scenario = "none"`

Whole-tree greps (each isolated, with positive control):

```
rg -n "wildfire" .        -> CHANGELOG.md:1127
                             modules/35_natveg/pot_forest_may24/sets.gms:12
                             modules/35_natveg/pot_forest_may24/sets.gms:15
rg -n "combined_loss" .   -> sets.gms:14; presolve.gms:25; presolve.gms:26
positive control "driver_source" -> sets.gms:10,14; input.gms:32  (search works)
```

Exactly as claimed: `wildfire` has three hits repo-wide, two of them set definitions and one a CHANGELOG line; `combined_loss` is consumed only in the non-default branch. A default run has no wildfire term, and the one live disturbance stream is zero from 2050 on.

Doc lines confirmed: `:221` ("Disturbed areas (fire, shifting agriculture)"), `:626` ("Disturbances (fire, shifting agriculture) -> reset age classes -> carbon loss"), `:869-872` (item 6).

All three bugs are substantively identical. **:55** has the fullest fix text and correctly preserves the true part (the age-class reset at `presolve.gms:36-38`); **:17** adds the `=4` branch. Merge and apply once.

### :4 — SS "Topsoil Equilibrium" default framing (mechanism) — **CORRECTED**

Module 29 default realization is `detail_apr24` (`config/default.cfg:814`) — verified.

Citations verified by direct read:
- `modules/29_cropland/detail_apr24/input.gms:24` (`s29_treecover_target ... / 0 /`), `:33` (`s29_fallow_max ... / 0 /`), `:35` (`s29_treecover_map ... / 0 /`)
- `equations.gms:70-72` = `q29_fallow_max(j2) .. vm_fallow(j2) =l= vm_land(j2,"crop") * s29_fallow_max;`
- `presolve.gms:81` = `v29_treecover.fx(j,ac_sub) = pc29_treecover(j,ac_sub);`
- `presolve.gms:120` = `vm_fallow.lo(j) = 0;`
- `config/default.cfg:863` (`s29_treecover_map <- 0`), `:868` (`s29_treecover_target <- 0`), `:901` (`s29_fallow_max <- 0`), `:1978` (`s59_scm_target <- 0`)

**Fallow: airtight.** `s29_fallow_max = 0` makes `q29_fallow_max` read `vm_fallow =l= 0`, and `.lo = 0`, so `vm_fallow ≡ 0` by hard bound. Term 3 is structurally zero.

**Treecover: the proposed fix overstates it.** Two gaps found:

1. The argument is incomplete without the `_noselect` siblings. `presolve.gms:66-68` computes
   `i29_treecover_target(t,j) = fader * (s29_treecover_target * weight + s29_treecover_target_noselect * (1-weight))`.
   Both must be zero. They are (`config/default.cfg:868` and `:869`), so the conclusion survives — but the fix text as written cites only one of the two and does not close the argument. Same for SCM: `s59_scm_target` **and** `s59_scm_target_noselect` (`config/default.cfg:1978,1979`).
2. "leaves treecover pinned at 0" is too strong. Only `ac_sub` is pinned (`presolve.gms:81`, and `preloop.gms:37-38` initializes `pc29_treecover(j,ac) = 0` under `s29_treecover_map = 0`). `ac_est` is *free* (`presolve.gms:79-80`: `.lo = 0`, `.up = Inf`) — it is zero because establishment and recurring costs (`equations.gms:108-117`) are unopposed once the target is 0 and the penalty equation `q29_treecover_min` is gated off (`equations.gms:90`), not because a bound forces it.

**corrected_claim**: terms 3-4 are indeed dead in a default run, but state it precisely — fallow is zero *by hard bound*; treecover is zero because the standing stock (`ac_sub`) is fixed to an all-zero initialization and establishment (`ac_est`) is costed with no target or penalty, so a cost-minimizing solve leaves it at zero. Include the `_noselect` scalars for both treecover and SCM.

### :15 — calibrated-curve reader set (consumer_set) — **UPHELD**

The decisive grep, run isolated, with the uncalib form separated by open-paren discipline (`pm_carbon_density_plantation_ac_uncalib` shares a prefix with the calibrated name, so a naive substring grep conflates them):

```
rg -n 'pm_carbon_density_plantation_ac\(' modules/ core/
  modules/32_forestry/dynamic_may24/preloop.gms:18     (READ - but preloop, see below)
  modules/32_forestry/dynamic_may24/preloop.gms:56     (READ - non-default branch, see below)
  modules/32_forestry/dynamic_may24/presolve.gms:65    (READ - calibrated)
  modules/52_carbon/normal_dec17/preloop.gms:114       (POPULATE - the calibration)
  modules/52_carbon/normal_dec17/declarations.gms:12   (DECLARE)
  modules/52_carbon/normal_dec17/start.gms:17,20       (POPULATE - uncalibrated)
  modules/52_carbon/normal_dec17/start.gms:44          (READ - copy to _uncalib)
  modules/14_yields/dynRegPastrTau_apr26/presolve.gms:26  (READ - non-default realization)
  modules/14_yields/managementcalib_aug19/presolve.gms:26 (READ - calibrated, DEFAULT realization)

rg -n 'pm_carbon_density_plantation_ac\.' modules/ core/   -> no match (it is a parameter; no
                                                              solution-level read channel exists)
```

Role map agrees: `pm_carbon_density_plantation_ac` -> `read_by ['14','32','52']`.

Confirmed sinks and defaults:
- `modules/32_forestry/dynamic_may24/presolve.gms:65` = `p32_carbon_density_ac(t,j,"plant",ac,ag_pools) = pm_carbon_density_plantation_ac(t,j,ac,ag_pools);`
- `modules/32_forestry/dynamic_may24/equations.gms:108-109` = `q32_carbon ... vm_carbon_stock(j2,"forestry",ag_pools,stockType) =e= m_carbon_stock_ac(v32_land,p32_carbon_density_ac,...)`
- `modules/14_yields/managementcalib_aug19/presolve.gms:26` feeds `im_growing_stock(t,j,ac,"forestry")` (`:24`); `:44` feeds the `"secdforest"` slice; `:66` reads the `_uncalib` secdforest curve for `im_growing_stock_ysf`
- M14 default realization = `managementcalib_aug19` (`config/default.cfg:357`); M32 default = `dynamic_may24` (`config/default.cfg:995`)
- Doc's uncalibrated list checks out: `modules/32_forestry/dynamic_may24/presolve.gms:59,61,68` all read `*_uncalib`; `modules/29_cropland/detail_apr24/preloop.gms:48` reads `*_uncalib`; `modules/35_natveg/pot_forest_may24/presolve.gms:242` reads `*_uncalib`, `:248-252` is the blend

Doc `:180` and `:479` confirmed **byte-identical** (1581 chars each). Both omit M32 from the calibrated side while listing it on the uncalibrated side — the aggravating framing the bug describes is real.

The phase-ordering caveat is correct (see the boxed section above). This bug's fix text is the only one of the three that is safe to apply as written.

### :42 — same omission, unsafe fix (consumer_set) — **CORRECTED**

Core finding identical to :15 and confirmed. Two defects in the fix:

1. It adds `preloop.gms:18,56` as **calibrated** reads. They are not — M32's preloop precedes M52's preloop calibration. Applying this would substitute one attribution error for another.
2. `preloop.gms:56` is inside `$elseif "%c32_rot_calc_type%" == "mean_annual_increment"`, and the default is `current_annual_increment` (`config/default.cfg:1133`; `modules/32_forestry/dynamic_may24/input.gms:15`) — not compiled in a default run at all.

The rotation-length claim ("M32 ... for rotation lengths") is therefore doubly wrong: wrong phase, and for `:56` a non-default compile branch.

**corrected_claim**: keep the M32-`presolve.gms:65` and M14-`presolve.gms:26` additions; drop the `preloop.gms:18,56` clause; optionally add bug :15's explicit ordering note so a future reader does not re-add them.

### :54 — same omission, same unsafe parenthetical (consumer_set) — **CORRECTED**

Core finding confirmed. Its main fix text is clean (it names only `presolve.gms:65` and `presolve.gms:26`) and its guard "Do not add the other-land reads — `pm_carbon_density_other_ac` is not calibrated" is **verified correct**: `rg -n 'pm_carbon_density_other_ac' modules/52_carbon/` returns only `declarations.gms:11` and `start.gms:48,51` — no preloop overwrite. But the trailing parenthetical "(also `modules/32_forestry/dynamic_may24/preloop.gms:18,56`)" carries the same phase-ordering error as :42 and must be dropped.

### :18 — Module 52 "Receives" list is incomplete (consumer_set) — **UPHELD**

Doc `:518-519` confirmed: the entire Receives list is one bullet (`vm_carbon_stock`).

All cited producers verified at both endpoints:

| Input | Declared | Populated | Read by M52 |
|---|---|---|---|
| `im_forest_ageclass(j,ac)` | `modules/28_ageclass/oct24/declarations.gms:9` | `.../oct24/preloop.gms:10,11,14` | `modules/52_carbon/normal_dec17/preloop.gms:53,55,59` |
| `pm_land_plantation(j,ac)` | `modules/32_forestry/dynamic_may24/declarations.gms:59` | `.../preloop.gms:179` | `modules/52_carbon/normal_dec17/preloop.gms:88,90,94` |
| `pcm_carbon_stock` | `modules/56_ghg_policy/price_aug22/declarations.gms:19` | M56 `postsolve.gms:8` (ag_pools), M59 `cellpool_jan23/postsolve.gms:13` (soilc) | `modules/52_carbon/normal_dec17/equations.gms:19` |
| `pm_climate_class` | module 45 (role map) | — | `modules/52_carbon/normal_dec17/preloop.gms:21,26,29,30` |
| `fm_ipcc_bef`, `fm_aboveground_fraction` | `modules/14_yields/managementcalib_aug19/input.gms:66` etc. | — | `modules/52_carbon/normal_dec17/preloop.gms:26,61,96` |

`rg -n 'pm_land_plantation' modules/` returns exactly 5 hits: the M32 declaration and population, and the three M52 reads. Nothing else touches it — a clean two-module interface.

M28 default realization = `oct24` (`config/default.cfg:805`) — verified.
`modules/52_carbon/normal_dec17/preloop.gms:14` = `*' This runs in preloop (after module 28 preloop has populated im_forest_ageclass).` — the code documents its own ordering constraint, exactly as the bug claims.

The M32<->M52 two-way loop is real and ordering-consistent: M32 preloop:179 populates `pm_land_plantation` -> M52 preloop:88-94 calibrates -> M32 presolve:65 reads the calibrated curve back.

### :20 — `vm_maccs_costs` has two consumers, not one (consumer_set) — **UPHELD**

```
rg -n 'vm_maccs_costs\(' modules/
  modules/57_maccs/on_aug22/declarations.gms:25   (DECLARE)
  modules/57_maccs/on_aug22/equations.gms:36,46   (POPULATE: "labor", "capital")
  modules/11_costs/default/equations.gms:28       (READ: sum(factors,...))
  modules/36_employment/exo_may22/equations.gms:28 (READ: "labor" slice only)

rg -n 'vm_maccs_costs\.' modules/
  modules/57_maccs/on_aug22/postsolve.gms:11,14,17,20  (own postsolve)
  modules/57_maccs/on_aug22/scaling.gms:8
```

Role map: `read_by ['11','36','57']` — agrees. M36 default realization = `exo_may22` (`config/default.cfg:1212`) and M11 = `default` (`config/default.cfg:236`), so this is a default-run path, not a scenario branch. Doc `:593` names only Module 11. The per-slice point is real: M11 sums all `factors`, M36 reads only `"labor"`.

### :21 / :31 — `vm_emissions_reg(...,"ch4")` has two readers (consumer_set) — **UPHELD** (both)

```
rg -n 'vm_emissions_reg\(' modules/   (by module)
  51_nitrogen/rescaled_jan21   10   (populate)
  52_carbon/normal_dec17        1   (populate, equations.gms:17)
  53_methane/ipcc2006_aug22     4   (populate)
  56_ghg_policy/price_aug22     2   (declare :40; READ equations.gms:17)
  57_maccs/on_aug22             4   (READ equations.gms:38,40,48,50)
  58_peatland/v2                1   (populate)

rg -n 'vm_emissions_reg\.' modules/  -> only .fx/.lo/.up bound-setting (M51,M53,M58 preloop)
                                        and M56 postsolve output copies. No hidden reader.
```

Role map: `read_by ['56','57']` — agrees exactly.

Verified equation bodies:
- `modules/56_ghg_policy/price_aug22/equations.gms:15-17` = `q56_emis_pricing(i2,pollutants,emis_annual) .. v56_emis_pricing =e= vm_emissions_reg(i2,emis_annual,pollutants);`
- `modules/57_maccs/on_aug22/equations.gms:38` (and `:48` for capital) = `... * vm_emissions_reg(i2,emis_source,pollutants_maccs57) / (1 - im_maccs_mitigation(ct,i2,emis_source,pollutants_maccs57))` — the divide-out-to-recover-baseline step the bugs describe
- `modules/57_maccs/on_aug22/equations.gms:40,50` = the implicit-fertilizer term over `emis_source_inorg_fert_n2o`
- `modules/57_maccs/on_aug22/sets.gms:25-26` = `pollutants_maccs57(pollutants) / ch4, n2o_n_direct /` — **CH4 is in scope**, so this is not an N2O-only path

M57 default realization = `on_aug22` (`config/default.cfg:1843`); M53 = `ipcc2006_aug22` (`:1604`); M56 = `price_aug22` (`:1634`).

The mutual dependency is real: M57 -> `im_maccs_mitigation` -> M53 -> `vm_emissions_reg` -> M57's cost equations, all inside one simultaneous LP. Doc `:573` shows only the M56 arrow, and SS7.4 (`:587-593`) has a Provides list with no Receives list — confirmed. The two bugs are the same finding; :21 has the better fix text (it also patches SS7.4).

### :22 — SOM convergence: 44% is the legacy share, not the gain (formula) — **UPHELD**

`modules/59_som/cellpool_jan23/preloop.gms:45` = `i59_lossrate(t)=1-0.85**m_yeardiff(t);` — verified.
`preloop.gms:41-43` = the upstream comment `"...a lossrate of 15% per year resulting in 44% in 5 years, 80% in 10 years / and 96% in 20 years."` — the slip is genuinely in the source comment (`"44% in 5 years"` sits on `:42`).

Recomputed: `1-0.85^5 = 0.5563` (56%); `1-0.85^10 = 0.8031` (80%); `1-0.85^20 = 0.9612` (96%); `1-0.85^50 = 0.99970`.

So `0.4437` is the **remaining legacy**, not the fraction of the way to the new equilibrium.

Doc `:734` = `- Year 5: 44% toward new equilibrium = +4 tC/ha` -> should be 56%, `+5.0` tC/ha on the stated `+9` gain. Neighbours are correct: `:735` (80% -> +7.2 = 0.803x9 ✓), `:736` (96% -> +8.6 = 0.961x9 ✓) — the defect is isolated to one row, which is the signature of a copy from the source comment rather than a systematic error.

The doc contradicts itself: SS5.2 `:399-404` tabulates 5 years -> Loss Rate 56% / Remaining Legacy 44%, and `:412` reads "After 5 years: 56% toward new equilibrium, 44% legacy" — correct. SS8.4 contradicts SS5.2.

SS8.2 slip confirmed one row off: `:678` "(80% toward natural)" under **Year 20** (should be 96%); `:684` "(96% toward natural)" under **Year 50** (should be >99.9%).

### :43 — `config/default.cfg:1835` is a comment; the assignment is `:1838` (citation) — **UPHELD**

Direct read:

```
1831: cfg$gms$c56_emis_policy <- "reddnatveg_nosoil"     # def = reddnatveg_nosoil   <- prefixed sibling
1833: # * CO2 emissions subject to carbon pricing
1834: # * options:  actual, actualNoAcEst
1835: # *   actual: CO2 emissions for pricing are based on the difference of actual...  <- COMMENT
1836: # *   actualNoAcEst: ...
1837: # *     without newly established forest and non-forest areas. ...
1838: c56_carbon_stock_pricing <- "actualNoAcEst"   # def = actualNoAcEst              <- ASSIGNMENT, no cfg$gms$
```

Corroboration: `CHANGELOG.md:891` = "- **config** added option for CO2 emission pricing `cfg$gms$c56_carbon_stock_pricing`" — the intended name carries the prefix. `modules/56_ghg_policy/price_aug22/input.gms:90` = `$setglobal c56_carbon_stock_pricing  actualNoAcEst` — the effective default.

The **substance survives fully** (the upstream MAgPIE config defect is real and `:1838` is genuinely unprefixed while `:1831` is prefixed); only the doc's line pointer at `:101` is off by three. The bug's own warning is well-founded: a reader who checks `:1835` finds a comment, which trivially has no `<-` and no prefix, and would dismiss a real upstream bug as a doc confabulation.

Classification note: the schema's `class` enum has no "citation" member; recorded as `formula_or_value` because the defective element is a value (a line number) that I re-derived mechanically. It is fully reviewable and was reviewed.

### :44 — age-class labels in the SS6.3 table do not exist in `ac` (set membership) — **UPHELD**

`core/sets.gms:269-275` = `ac Age classes / ac0,ac5,ac10,...,ac300, acx /`. Mechanical member count: **62** (61 five-year steps `ac0`..`ac300`, plus `acx`) — matches the bug exactly.

Doc `:493-499` Age Class column: `ac1, ac2, ac4, ac6, ac10, ac16, ac20`.

- `ac1`, `ac2`, `ac4`, `ac6`, `ac16` are **not members of `ac`**.
- `ac10` and `ac20` **are** members but denote **10 and 20 years**, while the doc assigns them to 50 and 100 years — a 5x mislabel.

Root cause confirmed: `modules/52_carbon/normal_dec17/start.gms:17` (and `:28,:48`) pass `(ord(ac)-1)` — an **ordinal** — as the macro's `ac` argument, which `core/macros.gms:18` then multiplies by 5. The doc's table author read the ordinal as the set label. The doc's own SS3.5 `:224` gets it right (`ac0 -> ac5 -> ac10 -> ... -> acx`).

The proposed replacement column (`ac0, ac5, ac10, ac20, ac30, ac50, ac80, ac100, acx`) checks out — every one of those labels exists in the set and maps to the stated year.

### :57 — SS9.1 GDX verification recipe is not runnable as written (mechanism) — **UPHELD**

All four sub-claims verified:

1. **No time dimension.** `modules/56_ghg_policy/price_aug22/declarations.gms:19` = `pcm_carbon_stock(j,land,c_pools,stockType)` — declared in the **parameters** block (lines 17-21), 4 dims, no `t`. It is overwritten every timestep (`modules/56_ghg_policy/price_aug22/postsolve.gms:8`; `modules/59_som/cellpool_jan23/postsolve.gms:13`), so it cannot supply a per-timestep lag, and `field="l"` is meaningless on a parameter. Structurally certain from the declaration alone.
2. **`stockType` not selected.** `postsolve.gms:25` = `ov_carbon_stock(t,j,land,c_pools,stockType,"level")` — the output carries `stockType`. The doc recipe (`:749`) never subsets to `"actual"`, silently mixing the two slices whose distinction the doc itself builds SS2.3 on (`:101`).
3. **Dimension collapse.** `modules/52_carbon/normal_dec17/equations.gms:16-19` shows `q52_emis_co2_actual` already sums cells within region `i2` and maps `emis_land(emis_oneoff,land,c_pools)`. `dimSums(stock_change, dim=c("cell","land","c_pools"))` collapses to a global scalar per year, which cannot be compared with a regional, `emis_source`-indexed `vm_emissions_reg` (`declarations.gms:40`).
4. **Peatland contamination.** `core/sets.gms:320-322` puts `peatland` in `emis_annual`; `core/sets.gms:314-318` shows `emis_oneoff` excludes it. `modules/58_peatland/v2/sets.gms:37` = `poll58(pollutants) / co2_c, ch4, n2o_n_direct /` and `equations.gms:91-92` writes `vm_emissions_reg(i2,"peatland",poll58)`. So `ov_emissions_reg[,,"co2_c"]` does carry an annual peatland CO2 stream that the stock-change side cannot produce.

The proposed replacement recipe (build the lag from `ov_carbon_stock` itself, pin `[,,"actual"]`, aggregate through `emis_land`) is sound.

---

## Notes for the fix pass

1. **Merge the duplicate groups before editing.** :1/:16/:30/:56 are one defect (primforest static); :2/:19 are one (growth table); :3/:17/:55 are one (fire); :15/:42/:54 are one (calibrated readers); :21/:31 are one (`vm_emissions_reg`). Twenty-one bug records describe **thirteen** distinct defects.
2. **`:180` and `:479` are byte-identical.** Any fix must be applied to both, or the pair drifts. Consider replacing one with a pointer.
3. **The doc contradicts itself in two places**, and in both the *later* section is the correct one: SS8.3 (`:697-700`) vs SS3.4/SS10.1 on primforest; SS5.2 (`:401,:412`) vs SS8.4 (`:734`) on the SOM loss rate. Fix the wrong copy, not the right one.
4. **Check `modules/module_52.md` and `modules/module_32.md`** for the same calibrated-reader omission before closing :15.
