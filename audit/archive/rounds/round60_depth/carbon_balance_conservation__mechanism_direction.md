# R60 depth audit — `cross_module/carbon_balance_conservation.md`

**Lens**: `mechanism_direction` (equation bodies, cross-module data-flow direction, mechanistic-vs-parameterized, set membership/counts)
**Ground truth**: MAgPIE `develop` read-only worktree @ `2c02843ec` (`Merge pull request #919 from alexkoberle/dyn_reg_tau`)
**Date**: 2026-08-02
**Claims verified**: 78
**Bugs**: 13 (0 Critical · 3 Major · 8 Minor · 2 Informational)

All paths below are repo-relative. `develop` = the read-only MAgPIE worktree.

---

## What checked out clean (so the negatives are informative)

Verified correct against current `develop`, in case a later reader wonders whether these were examined:

| Claim | Evidence |
|---|---|
| `c_pools = /vegc,litc,soilc/` at `core/sets.gms:324-325` | exact |
| `emis_oneoff` at `core/sets.gms:314-318`, **21** members = 7 land × 3 pools | counted; `land` set = 7 members at `core/sets.gms:250-251` |
| `emis_land` mapping at `core/sets.gms:332-354` | exact (closing `/` on 354) |
| `peatland ∈ emis_annual` at `core/sets.gms:322` | exact |
| `q52_emis_co2_actual` body + `"actual"` slice at `modules/52_carbon/normal_dec17/equations.gms:16-19` | quoted equation matches character-for-character |
| `vm_carbon_stock(j,land,c_pools,stockType)` DECLARED at `modules/56_ghg_policy/price_aug22/declarations.gms:34` | exact |
| `stockType / actual, actualNoAcEst /` at `modules/56_ghg_policy/price_aug22/sets.gms:212-213` | exact |
| `$setglobal c56_carbon_stock_pricing actualNoAcEst` at `modules/56_ghg_policy/price_aug22/input.gms:90` | exact |
| **M52 ∥ M56 are parallel readers of `vm_carbon_stock`, not serial** | `rg -n "vm_emissions_reg" modules/56_ghg_policy/` → the only equation-level read is `q56_emis_pricing` over `emis_annual` (`equations.gms:17`); M52 writes only `emis_oneoff`. Doc's §7.3 anti-serial warning is **correct** |
| `q56_emis_pricing` `:15-17`, `q56_emis_pricing_co2` `:19-22` | exact |
| Populator set of `vm_carbon_stock` = {29 crop, 31 past, 32 forestry, 34 urban, 35 primforest/secdforest/other, 59 soilc} | whole-tree `rg -n "vm_carbon_stock" modules/`; matches role map `populated_by ['29','31','32','34','35','59']`. §7.5 list is **complete and correct** |
| `s52_growingstock_calib` default `1`, **not** in `config/default.cfg` | `input.gms:46`; grep of `default.cfg` returns nothing for it while the positive controls `c52_carbon_scenario` (1590) and `s52_k_high_secdf/plant` (1597/1599) hit |
| M52 preloop calibration sites `:29-30`, `:71-73`, `:114-116`; asymptote unchanged | exact |
| `pm_carbon_density_*_ac_uncalib` created at `start.gms:43-44` | exact |
| Uncalibrated-curve reader set (M14 `:66`, M29 `:46,48`, M32 `:59,61,68`, M35 `:242` + `:117`) | whole-tree `rg` — all five citations land on the right lines |
| M35 blend `:248-252`, natural-origin bound `:177-180` | exact |
| commit `6b00f9dea` = 2026-07-01 "Fix youngsecdf wood production: use uncalibrated growing stock" | `git log -1 6b00f9dea` |
| `im_growing_stock_ysf` at `modules/14_yields/managementcalib_aug19/presolve.gms:64-71` | exact |
| M59 `q59_som_target_cropland` `:20-27` (all 4 terms), `q59_som_pool` `:46-52`, `q59_carbon_soil` `:61-64` | exact |
| `i59_lossrate(t)=1-0.85**m_yeardiff(t)` at `modules/59_som/cellpool_jan23/preloop.gms:45`; §5.2 table (56/80/96 %) | arithmetic re-derived: 0.5563 / 0.8031 / 0.9612 |
| `i59_subsoilc_density = fm_carbon_density(...,"other","soilc") − f59_topsoilc_density` at `preloop.gms:12` | exact — doc's M52→M59 derivation direction is right |
| `s59_scm_target = 0` (`default.cfg:1978`), `c59_irrigation_scenario = "on"` (`default.cfg:1956`), off-switch at `input.gms:70`, `s59_cost_scm_recur = 65` (`input.gms:15`) | exact |
| pasture limitation at `modules/59_som/cellpool_jan23/realization.gms:21-24` | exact |
| M53 MACC sites `:29 :52 :63`, `q53_emissions_resid_burn` `:70-72` with **no** mitigation term, `maccs_ch4 / rice_ch4, ent_ferm_ch4, awms_ch4 /` at `modules/57_maccs/on_aug22/sets.gms:28-29` | exact |
| M51 `:71` AWMS MACC over **all** `n_pollutants_direct`, comment `:62-64`; `q51_emissions_inorg_fert` `:30-39` MACC-free; `emis_source_n51` `sets.gms:15-16`; rice-fix `preloop.gms:8-10` | exact — the whole §7.4 N₂O block is right |
| M50 `inorg_fert_n2o` NUE uplift at `modules/50_nr_soil_budget/macceff_aug22/presolve.gms:54-64` | exact |
| M58 peatland: `v2` default (`default.cfg:1874`), `s58_fix_peatland = 2020` (`default.cfg:1931`), `q58_peatland_emis → vm_emissions_reg(i,"peatland",poll58)` at `modules/58_peatland/v2/equations.gms:91-92`, realization text `:8-17`; **no peat in M59** (`rg -n "peat" modules/59_som/cellpool_jan23/*.gms` → empty, positive control `soil` → 17 hits) | §10.2 item 7 is correct end-to-end |
| `m_timestep_length` at `core/macros.gms:51`; `m_growth_vegc` at `:18` | exact |
| All 13 realizations named in the doc are the `config/default.cfg` defaults | 52 normal_dec17, 59 cellpool_jan23, 56 price_aug22, 58 v2, 34 exo_nov21, 29 detail_apr24, 35 pot_forest_may24, 32 dynamic_may24, 53 ipcc2006_aug22, 57 on_aug22, 51 rescaled_jan21, 50 macceff_aug22, 14 managementcalib_aug19 |
| `vm_nr_som` "Mt N per yr", `vm_cost_scm` "mio. USD17MER per yr", `vm_carbon_stock` "mio. tC", `vm_emissions_reg` "Tg per yr" | declarations |
| §8.1 immediate-emission arithmetic (56,833 Tg CO₂) and §8.4 cost arithmetic (48,750 mio USD; 144 USD/tC) | re-derived, correct |

Notably, the §2.3 `actual` vs `actualNoAcEst` paragraph — the highest-risk mechanism claim in the doc — is **right**: the `m_carbon_stock_ac` macro (`core/macros.gms:104-106`) sums over the full `ac` set for `"actual"` and over `ac_sub` for `"actualNoAcEst"`, so the populating equations do fill both slices, and M52 (reporting) and M56 (pricing) really do pick different ones in a default run.

---

## Bugs

### CB-01 — Major — `set_membership` — the CALIBRATED-curve reader set omits M32 (and M14's plantation read)

**Doc** `carbon_balance_conservation.md:180` (and the verbatim duplicate at `:479`):

> "M14 and M35 read the CALIBRATED curve as well - M14 for regular secdforest growing stock (`modules/14_yields/managementcalib_aug19/presolve.gms:44`), M35 for secdforest carbon density, which it BLENDS with the uncalibrated curve by natural-origin area share"

**Reality**: **M32 also reads the calibrated curve**, and it is the reader that matters most — `p32_carbon_density_ac(t,j,"plant",ac,ag_pools) = pm_carbon_density_plantation_ac(t,j,ac,ag_pools);` at `modules/32_forestry/dynamic_may24/presolve.gms:65` is the carbon density of **existing timber plantations**, unconditional, in the presolve phase (i.e. after M52's preloop overwrite). **M14 additionally** reads the calibrated *plantation* curve at `modules/14_yields/managementcalib_aug19/presolve.gms:26` for `im_growing_stock(t,j,ac,"forestry")`.

The paragraph's structure — an apparently exhaustive uncalibrated-reader list, then "M14 and M35 read the CALIBRATED curve as well" — reads as the complete calibrated/uncalibrated map. M32 appears in the paragraph only under *uncalibrated* (`aff`, `ndc`). A maintainer changing or disabling `s52_growingstock_calib` would conclude M32's plantation carbon is untouched. It is not.

**Evidence**: `modules/32_forestry/dynamic_may24/presolve.gms:65`, `modules/14_yields/managementcalib_aug19/presolve.gms:26`.

**Verify**:
```
rg -n "pm_carbon_density_plantation_ac|pm_carbon_density_secdforest_ac" /tmp/magpie_develop_ro/modules/ --glob '*.gms' | grep -v uncalib
```
→ writers `52_carbon/normal_dec17/start.gms:17,20,28,31` and `preloop.gms:71,114`; readers `14_yields/managementcalib_aug19/presolve.gms:26,44`, `14_yields/dynRegPastrTau_apr26/presolve.gms:26,44`, `32_forestry/dynamic_may24/preloop.gms:18,56`, **`32_forestry/dynamic_may24/presolve.gms:65`**, `35_natveg/pot_forest_may24/presolve.gms:248,250` (the `:251` blend term is filtered by `grep -v uncalib`); plus `declarations.gms:9,12`.

**Fix**: replace the sentence with — "M14, M32 and M35 read the CALIBRATED curves as well: M14 for `forestry` growing stock (`modules/14_yields/managementcalib_aug19/presolve.gms:26`) and regular secdforest growing stock (`:44`); M32 for existing timber-plantation carbon density (`modules/32_forestry/dynamic_may24/presolve.gms:65`); M35 for secdforest carbon density, which it BLENDS with the uncalibrated curve by natural-origin area share (`modules/35_natveg/pot_forest_may24/presolve.gms:248-252`)." Apply to **both** copies (`:180` and `:479`).

**Note (not asserted in the fix)**: M32's `preloop.gms:18` / `:56` reads run in the *preloop* phase, where modules execute in numeric order (`modules/include.gms`), so module 32 reads `pm_carbon_density_plantation_ac` **before** module 52's preloop calibration overwrites it — those two capture uncalibrated values. Worth a separate investigation; deliberately excluded from the proposed edit.

---

### CB-02 — Major — `mechanism` — "primary forest carbon density does NOT change over time" is false under the default climate scenario

**Doc** `carbon_balance_conservation.md:201` (§3.4), with the §3.4 table at `:194-196` marking all three pools **Static**, and §10.1 item 1 at `:840-843`:

> "Carbon density does NOT change over time (climate change affects future forests, not current primary)"

**Reality**: `fm_carbon_density` is declared over `t_all` (`modules/52_carbon/normal_dec17/input.gms:16`) and is only collapsed to y1995 when `c52_carbon_scenario == "nocc"` (`:22`). The default is `cc` (`config/default.cfg:1590`). `q35_carbon_primforest` (`modules/35_natveg/pot_forest_may24/equations.gms:42-44`) uses `m_carbon_stock`, which evaluates the density at the **current** timestep: `land(j2,item) * sum(ct, carbon_density(ct,j2,item,ag_pools))` (`core/macros.gms:99-101`). Primforest soilc is likewise time-varying: M59's non-cropland target is `vm_land(j2,noncropland59) * sum(ct, f59_topsoilc_density(ct,j2))` (`modules/59_som/cellpool_jan23/equations.gms:31-34`), and `f59_topsoilc_density` is only frozen when `c59_som_scenario == "nocc"` — default is `cc` (`config/default.cfg:1951`).

The doc contradicts **itself**: §8.3 (`:698-700`) states "LPJmL simulates vegetation carbon density under future climate → Module 52 updates `fm_carbon_density(t,j,land,c_pools)` over time → Carbon stocks change even without land-use change."

The defensible claim is narrower: primforest has **no age-class dynamics** — it is always at the LPJmL mature density, unlike secdforest which accumulates along the Chapman-Richards curve. That is not the same as "does not change over time".

**Evidence**: `modules/52_carbon/normal_dec17/input.gms:16,22`; `core/macros.gms:99-101`; `modules/35_natveg/pot_forest_may24/equations.gms:43-45`; `config/default.cfg:1590,1951`.

**Verify**:
```
sed -n '99,101p' /tmp/magpie_develop_ro/core/macros.gms
grep -nE '^cfg.gms.c52_carbon_scenario|^cfg.gms.c59_som_scenario' /tmp/magpie_develop_ro/config/default.cfg
```
→ macro sums over `ct`; `1590:cfg$gms$c52_carbon_scenario <- "cc"`, `1951:cfg$gms$c59_som_scenario <- "cc"`.

**Fix**: change §3.4 "Static" cells to "No age-class dynamics (always at LPJmL mature density)" and replace `:201` with — "Carbon density carries **no age/regrowth dynamics** (primforest is always at the LPJmL mature value). It *does* change over time under the default `c52_carbon_scenario = "cc"` / `c59_som_scenario = "cc"`, because `fm_carbon_density` and `f59_topsoilc_density` are time-varying LPJmL inputs evaluated at the current timestep (`core/macros.gms:99-101`); see §8.3." Amend §10.1 item 1 to say the limitation is the missing regrowth/age dynamic, not the absence of climate response.

---

### CB-03 — Major — `mechanism` (capability-vs-default) — wildfire disturbance is not active in a default run

**Doc** `carbon_balance_conservation.md:870` (§10.2 item 6), plus `:221` and `:626`:

> "Fire disturbances (Module 35) cause carbon loss via stock change / But emissions lumped with general LUC emissions / Implication: Cannot track fire emissions specifically"
> "- Disturbed areas (fire, shifting agriculture)" (`:221`)
> "- Disturbances (fire, shifting agriculture) → reset age classes → carbon loss" (`:626`)

**Reality**: M35 has four mutually exclusive damage branches keyed on `s35_forest_damage` (`modules/35_natveg/pot_forest_may24/presolve.gms:13-33`). The **default is 2** (`modules/35_natveg/pot_forest_may24/input.gms:27` `/ 2 /`; `config/default.cfg:1184`), which applies **only** the `"shifting_agriculture"` column of `f35_forest_lost_share`, multiplied by `(1 - p35_damage_fader(t))` — a sigmoid fader that reaches 1 at `s35_forest_damage_end = 2050` (`config/default.cfg:1186`; `preloop.gms:88`), i.e. disturbance loss decays to **zero by 2050**.

The distinct `wildfire` driver is a member of `combined_loss / shifting_agriculture, wildfire /` (`modules/35_natveg/pot_forest_may24/sets.gms:14-15`), and `combined_loss` is read **only** in the `s35_forest_damage = 3` branch (`presolve.gms:25-26`) — not the default. So in a default run, the `wildfire` column of `f35_forest_lost_share` is never read: wildfire causes **no** carbon loss at all, rather than loss that is "lumped" with LUC emissions.

Secondary point for the three-check protocol: even in branch 3, `f35_forest_lost_share(i,driver_source)` is an exogenous input table ("Share of area damaged by forest fires", `input.gms:32-36`) — the disturbance is **parameterized**, not mechanistically modelled.

**Evidence**: `modules/35_natveg/pot_forest_may24/presolve.gms:13-33`, `sets.gms:14-15`, `input.gms:27,32-36`, `preloop.gms:88`; `config/default.cfg:1184,1186`.

**Verify**:
```
sed -n '9,33p' /tmp/magpie_develop_ro/modules/35_natveg/pot_forest_may24/presolve.gms
grep -n "s35_forest_damage" /tmp/magpie_develop_ro/config/default.cfg
```
→ `if(s35_forest_damage=2, ... f35_forest_lost_share(i,"shifting_agriculture") ... *(1 - p35_damage_fader(t)))`; `1184:cfg$gms$s35_forest_damage <- 2   # def = 2`, `1186:cfg$gms$s35_forest_damage_end <- 2050`.

**Fix**: rewrite §10.2 item 6 as — "**6. Wildfire is OFF in a default run.** With the default `s35_forest_damage = 2` (`config/default.cfg:1184`) M35 applies only the exogenous `shifting_agriculture` share of `f35_forest_lost_share` (`modules/35_natveg/pot_forest_may24/presolve.gms:20-21`), faded to zero by `s35_forest_damage_end = 2050`. The separate `wildfire` driver enters only via `combined_loss` under `s35_forest_damage = 3` (`presolve.gms:25-26`). Even then it is a fixed input share, not a modelled fire process. Disturbance loss is booked as an age-class reset and therefore surfaces as a `vm_carbon_stock` change indistinguishable from other LUC emissions." Amend `:221` and `:626` to say "shifting agriculture (default); wildfire only with `s35_forest_damage = 3`".

---

### CB-04 — Minor — `citation` — `config/default.cfg:1835` drifts to a comment line

**Doc** `carbon_balance_conservation.md:101`:

> "Do **not** cite `config/default.cfg:1835` for this default: that line omits the `cfg$gms$` prefix its siblings carry"

**Reality**: the switch line is `config/default.cfg:**1838**`. Line 1835 is a comment (`# *   actual: CO2 emissions for pricing are based on the difference of actual carbon stocks between time steps`). The substantive finding is **true** at 1838 — `c56_carbon_stock_pricing <- "actualNoAcEst"` genuinely lacks the `cfg$gms$` prefix, and a whole-repo grep confirms no script re-attaches it (`rg -n "carbon_stock_pricing" .` → only `config/default.cfg:1838` and `CHANGELOG.md:891`, plus module 56 itself).

**Verify**:
```
awk 'NR>=1833 && NR<=1839 {print NR": "$0}' /tmp/magpie_develop_ro/config/default.cfg
```
→ `1835: # *   actual: …`, `1838: c56_carbon_stock_pricing <- "actualNoAcEst"   # def = actualNoAcEst`.

**Fix**: `1835` → `1838`.

---

### CB-05 — Minor — `formula` — §6.3 growth table does not match its own stated k and m

**Doc** `carbon_balance_conservation.md:487-500`: parameters "A = 100 tC/ha, k = 0.06, m = 2.0", then a table giving 14 / 26 / 44 / 58 / 75 / 88 / 93 tC/ha at 5 / 10 / 20 / 30 / 50 / 80 / 100 years.

**Reality**: `m_growth_vegc(S,A,k,m,ac) = S + (A-S)*(1-exp(-k*(ac*5)))**m` (`core/macros.gms:18`). With A=100, k=0.06, m=2 the values are **6.7 / 20.4 / 48.8 / 69.7 / 90.3 / 98.4 / 99.5** — the doc's numbers instead trace a roughly k≈0.03, m=1 curve (13.9 / 25.9 / 45.1 / 59.3 / 77.7 / 90.9 / 95.0). The table is labelled illustrative, but it is the doc's only worked demonstration of its central growth equation, and a reader checking the formula against it will conclude the formula is wrong.

**Verify**:
```
python3 -c "import math;A,k,m=100,0.06,2.0;print([round(A*(1-math.exp(-k*y))**m,1) for y in (5,10,20,30,50,80,100)])"
```
→ `[6.7, 20.4, 48.8, 69.7, 90.3, 98.4, 99.5]`.

**Fix**: recompute the table from A=100, k=0.06, m=2.0 (values above), or change the stated parameters to k=0.03, m=1.0 and recompute. Either way the table must be reproducible from `core/macros.gms:18`.

---

### CB-06 — Minor — `formula` — §8.4 (and §8.2) convergence percentages contradict §5.2 and `preloop.gms:45`

**Doc** `carbon_balance_conservation.md:734`:

> "- Year 5: 44% toward new equilibrium = +4 tC/ha"

**Reality**: `i59_lossrate(t) = 1 - 0.85**m_yeardiff(t)` (`modules/59_som/cellpool_jan23/preloop.gms:45`) gives `1 - 0.85^5 = 0.5563` → **56 %** toward equilibrium at 5 years (44 % is the *residual legacy*). The doc's own §5.2 table (`:399-404`) correctly states 56 % / 44 %. The 44 % figure appears to have been lifted from the in-code comment at `preloop.gms:42`, which is itself internally inconsistent ("44% in 5 years, 80% in 10 years and 96% in 20 years" mixes remaining with converged).

Same section, §8.2 `:684` labels Year-50 soil carbon "96 % toward natural"; 96 % is the 20-year value — at 50 years `1 - 0.85^50 = 0.9997`.

**Verify**:
```
python3 -c "print(round(1-0.85**5,4), round(1-0.85**20,4), round(1-0.85**50,5))"
```
→ `0.5563 0.9612 0.99969`.

**Fix**: §8.4 → "Year 5: 56 % toward new equilibrium = +5.0 tC/ha"; §8.2 Year-50 → "≈100 % toward natural". Optionally note that the code comment at `modules/59_som/cellpool_jan23/preloop.gms:42` is the source of the confusion.

---

### CB-07 — Minor — `formula` — §8.1 gradual soil-carbon emission arithmetic is wrong

**Doc** `carbon_balance_conservation.md:656`:

> "- Gradual (soilc over 20 years): 30 tC/ha × 100 Mha × (44/12) / 20 years = **458 Tg CO₂/year**"

**Reality**: 30 tC/ha × 100 Mha = 3,000 Tg C; × 44/12 = 11,000 Tg CO₂; ÷ 20 = **550 Tg CO₂/yr**. (458 corresponds to dividing by 24.) The immediate-emission line directly above it, `:655`, is arithmetically correct at 56,833 Tg CO₂ — so the error is isolated.

**Verify**:
```
python3 -c "print(30*100*(44/12)/20)"
```
→ `550.0`.

**Fix**: `458` → `550`.

---

### CB-08 — Minor — `attribution_populate` — urban vegc/litc zeroing attributed to Module 52

**Doc** `carbon_balance_conservation.md:263-264` (§3.7 table): rows `vegc | Fixed to zero | None | **52**` and `litc | Fixed to zero | None | **52**`.

**Reality**: the zeroing is done by **Module 34**: `vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0;` at `modules/34_urban/exo_nov21/presolve.gms:8` (default realization). Module 52 touches urban only for **soilc**, where `fm_carbon_density(t_all,j,"urban","soilc") = fm_carbon_density(t_all,j,"other","soilc")` (`modules/52_carbon/normal_dec17/input.gms:35`) — so the table's soilc row ("52, 59") is right and the vegc/litc rows are not. The doc's own §7.5 (`:622`) attributes the fix correctly to M34, so §3.7 contradicts §7.5.

**Verify**:
```
rg -n 'vm_carbon_stock\.fx' /tmp/magpie_develop_ro/modules/
```
→ `modules/34_urban/exo_nov21/presolve.gms:8` and `modules/34_urban/static/presolve.gms:10` only.

**Fix**: change the Module column for urban vegc and litc from `52` to `34`, and note "fixed by `vm_carbon_stock.fx` in M34's presolve, not by a carbon density".

---

### CB-09 — Minor — `attribution_read` — CH₄ consumer arrow omits Module 57

**Doc** `carbon_balance_conservation.md:573` (§7.3 "Provides"):

> "- `vm_emissions_reg(i,emis_source,"ch4")`: Regional CH₄ emissions → to Module 56"

**Reality**: Module **57** also reads `vm_emissions_reg` at equation level, to size MACC costs: `modules/57_maccs/on_aug22/equations.gms:38,40,48,50` (inside `q57_labor_costs`, declared at `:35`, and `q57_capital_costs`, declared at `:45`, which back out un-mitigated emissions via `/(1 - im_maccs_mitigation)`). Role map: `vm_emissions_reg.read_by = ['56','57']`.

**Verify**:
```
rg -n "vm_emissions_reg" /tmp/magpie_develop_ro/modules/57_maccs/
```
→ `on_aug22/equations.gms:38,40,48,50`.

**Fix**: "→ to Module 56 (pricing, `q56_emis_pricing`) and Module 57 (MACC cost sizing, `modules/57_maccs/on_aug22/equations.gms:38,48`)".

---

### CB-10 — Minor — `attribution_read` — `vm_maccs_costs` consumer arrow omits Module 36

**Doc** `carbon_balance_conservation.md:593` (§7.4 "Provides"):

> "- `vm_maccs_costs(i,factors)`: Labor and capital costs of mitigation → to Module 11"

**Reality**: Module **36 (employment)** reads the labor slice: `(vm_maccs_costs(i2,"labor")) * (1 / sum(ct, f36_weekly_hours(...)*s36_weeks_in_year*pm_hourly_costs(...)))` at `modules/36_employment/exo_may22/equations.gms:28`. Module 11 reads it at `modules/11_costs/default/equations.gms:28`. Role map: `read_by = ['11','36','57']`.

**Verify**:
```
rg -n "vm_maccs_costs" /tmp/magpie_develop_ro/modules/11_costs/ /tmp/magpie_develop_ro/modules/36_employment/
```
→ `11_costs/default/equations.gms:28`, `36_employment/exo_may22/equations.gms:28`.

**Fix**: "→ to Module 11 (`modules/11_costs/default/equations.gms:28`) and, for the `labor` slice, Module 36 (`modules/36_employment/exo_may22/equations.gms:28`)".

---

### CB-11 — Minor — `mechanism` — litter "decomposition to soil organic matter" is not modelled

**Doc** `carbon_balance_conservation.md:73` (§2.2 "Dynamics"):

> "- **Decomposition**: Gradual breakdown to soil organic matter (20-year IPCC timescale)"
> (and `:72` "- **Accumulation**: From plant death, harvest residues, forest turnover")

**Reality**: there is **no litter→soil carbon flux anywhere in MAgPIE**. `litc` is a linear ramp of *density by age class* — `m_growth_litc_soilc(start,end,ac) = (start + (end-start)*1/20*ac*5)$(ac<=4) + end$(ac>4)` (`core/macros.gms:20`), applied at `modules/52_carbon/normal_dec17/start.gms:20,31,51`. It interpolates from the pasture litter density to the target-land-type litter density over 20 years of age class; nothing is transferred to the soil pool. M59's soil pool is built from `f59_topsoilc_density`, `i59_cratio*` and `i59_subsoilc_density` and never references `litc`.

**Verify**:
```
rg -n "litc" /tmp/magpie_develop_ro/modules/59_som/ /tmp/magpie_develop_ro/modules/50_nr_soil_budget/
```
→ no matches (positive control: `rg -cn "litc" .../modules/52_carbon/normal_dec17/start.gms` → 4).

**Fix**: replace the two "Dynamics" bullets with what the code does — "**Implementation**: `litc` is not a tracked flux. Per age class it is a linear interpolation from the pasture litter density to the target land type's LPJmL equilibrium litter density over 20 years (`core/macros.gms:20`; `modules/52_carbon/normal_dec17/start.gms:20,31,51`). There is no litter→soil transfer: M59's soil pool never reads `litc`."

---

### CB-12 — Informational — `citation` — MANDATE-16 path prefixes missing in the repeated warning paragraph

**Doc** `carbon_balance_conservation.md:180` and `:479` (also `:247`, `:254`).

Six citations omit the required `modules/` prefix: `14_yields/managementcalib_aug19/presolve.gms:66`, `29_cropland/detail_apr24/preloop.gms:46,48`, `32_forestry/dynamic_may24/presolve.gms:59,61,68`, `35_natveg/pot_forest_may24/presolve.gms:242`, `normal_dec17/preloop.gms:71-73`, and the bare `:114-116` / `:29-30` continuation forms. All resolve to the right lines — this is style, not content.

**Fix**: expand to full `modules/NN_name/realization/file.gms:LINE` form in both copies.

---

### CB-13 — Informational — `set_membership` — "appears in exactly these equations" is falsified literally

**Doc** `carbon_balance_conservation.md:595`:

> "**Applies to** (verified against code - the mitigation factor `(1 - im_maccs_mitigation)` appears in exactly these equations)"

**Reality**: a whole-tree grep also returns `modules/57_maccs/on_aug22/equations.gms:38` and `:48`, where `(1 - im_maccs_mitigation(ct,i2,emis_source,pollutants_maccs57))` appears as a **divisor** — un-mitigating emissions back to their baseline so the MACC cost curve can be integrated. The doc's intent ("applied to these emission streams") is right; the exhaustiveness wording is not.

**Verify**:
```
rg -n "im_maccs_mitigation" /tmp/magpie_develop_ro/modules/ --glob '*.gms'
```
→ applications at `53/.../equations.gms:29,52,63` and `51/.../equations.gms:71`; divisor uses at `57/.../equations.gms:38,48`; NUE uplift at `50/.../presolve.gms:56,58,61,63`; population at `57/.../preloop.gms:46-64`.

**Fix**: "…appears as an *emission-reducing* factor in exactly these equations (it also appears as a divisor inside M57's own cost equations, `modules/57_maccs/on_aug22/equations.gms:38,48`, which un-mitigate emissions for the cost integral)."

---

## Deferred (not verifiable this session — no bug asserted, no edit proposed)

1. `im_maccs_mitigation` range "0 to ~0.3" (`:592`) — depends on `f57_maccs_*` input tables; `*.cs*` are gitignored runtime products.
2. IPCC stock-change factor example values 0.69 and 1.17 (`:437-438`) — read from `f59_ch5_F_I.csv` / `f59_ch5_F_LU.csv`, not in the repo.
3. Doc writes `fm_carbon_density(t,j,land,c_pools)` and `pm_carbon_density_*_ac(t,j,ac,ag_pools)` (`:107,:513-516,:948`) where declarations use `t_all` (`modules/52_carbon/normal_dec17/input.gms:16`, `declarations.gms:9-13`). Since `t ⊂ t_all` this is harmless and may be a deliberate convention — flagged, not filed.
4. §7.2 attributes `vm_land(j,land)` "Non-cropland areas from Module 10" (`:547`). M10 declares `vm_land` and enforces the area/transition identities (`modules/10_land/landmatrix_dec18/equations.gms:14,21`), but the non-cropland slices are actually shaped by M31/M32/M34/M35 bounds and equations. Arguably a corpus-wide convention; not filed to avoid a false positive.
5. §7.5 line 610 describes `q29_carbon` as aggregating `vm_carbon_stock_croparea` into the crop slice; the equation (`modules/29_cropland/detail_apr24/equations.gms:38-42`) has two further terms (fallow × `fm_carbon_density`, and treecover via `m_carbon_stock_ac`). Incomplete rather than wrong; not filed.
6. §9 R snippets use `readGDX(gdx, "pcm_carbon_stock", field="l")` on a GAMS *parameter*; `ov59_som_pool`, `ov59_som_target`, `ov32_land`, `ov_carbon_stock` all exist as declared. Snippet-level R correctness not executed.
7. M32's `preloop.gms:18` / `:56` phase-ordering question raised under CB-01 — needs its own investigation before any doc claim is made.
