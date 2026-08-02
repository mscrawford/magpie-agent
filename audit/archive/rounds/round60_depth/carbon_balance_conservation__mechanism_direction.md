# R60 depth audit — `cross_module/carbon_balance_conservation.md`

**Lens**: `mechanism_direction` (equation bodies, cross-module data-flow direction, mechanistic-vs-parameterized, causal direction, set membership/counts)
**Ground truth**: MAgPIE `develop` read-only worktree @ `2c02843ec` ("Merge pull request #919 from alexkoberle/dyn_reg_tau")
**Attribution reference**: `audit/integrated/depth_rolemap.json`, consulted **first** for every `vm_`/`pm_`/`im_`/`pcm_`/`fm_` claim, then confirmed at **both endpoints** with a standalone grep.
**Date**: 2026-08-02
**Claims verified**: 118
**Bugs**: 16 (1 Critical · 3 Major · 9 Minor · 3 Informational)

All paths repo-relative. **Provenance note**: an earlier pass over this same file/lens exists in this directory's history. Where a finding here coincides with it, it was **re-derived from code in this session** before being restated — a matching prior verdict is corroboration, never the evidence. Two findings are new (B4, B13) and one severity is deliberately raised against the earlier pass (B1, reasoning inline).

---

## 0. What checked out clean (so the negatives are interpretable)

The doc's **interface-attribution spine is correct**, which is notable given attribution is the highest-propagation
defect class measured. Verified this session:

| Claim | Evidence |
|---|---|
| `c_pools /vegc,litc,soilc/` | `core/sets.gms:324-325` exact |
| `land` = 7 members ⇒ `emis_oneoff` = 21 = 7 × 3 | `core/sets.gms:250-251`; `core/sets.gms:314-318` |
| `emis_land` mapping | `core/sets.gms:332-354` (closing `/` on 354) exact |
| `peatland ∈ emis_annual` | `core/sets.gms:322` |
| `q52_emis_co2_actual` body + `"actual"` slice | `modules/52_carbon/normal_dec17/equations.gms:16-19`; quoted GAMS block matches character-for-character |
| `vm_carbon_stock` DECLARED in M56 | `modules/56_ghg_policy/price_aug22/declarations.gms:34` |
| `stockType / actual, actualNoAcEst /` | `modules/56_ghg_policy/price_aug22/sets.gms:212-213` |
| Populating equations indexed over the free `stockType` and filling **both** slices; the slices differ *inside* the macro | `core/macros.gms:99-106` — `m_carbon_stock_ac` sums `ac` for `"actual"`, `ac_sub` for `"actualNoAcEst"` |
| Priced slice = `%c56_carbon_stock_pricing%` = `actualNoAcEst` ≠ M52's reported `"actual"` | `modules/56_ghg_policy/price_aug22/input.gms:90`; `.../equations.gms:22` vs `modules/52_carbon/normal_dec17/equations.gms:19` |
| **M52 ∥ M56 are PARALLEL readers of `vm_carbon_stock`, not a serial chain** (§7.3's anti-serial warning) | `q56_emis_pricing` is indexed over `emis_annual` only (`.../equations.gms:15-17`); M52 writes only `emis_oneoff`; the two subsets are disjoint (`core/sets.gms:314-322`); `q56_emis_pricing_co2` recomputes CO₂ itself (`:19-22`) |
| `vm_carbon_stock` populator set = {29 crop, 31 past, 32 forestry, 34 urban, 35 primf/secdf/other, 59 soilc-all-land}; readers = {52, 56, 59} | whole-tree `rg -n 'vm_carbon_stock' modules/`; identical to role map `populated_by ['29','31','32','34','35','59']`, `read_by ['52','56','59']`. §7.5's list at `:629-632` is complete |
| `s52_growingstock_calib = 1` hard default, **absent** from `config/default.cfg` | `modules/52_carbon/normal_dec17/input.gms:46`; positive controls `c52_carbon_scenario` (`:1590`) and `peatland` (`:1874`) *do* hit in `default.cfg`, this one does not |
| Calibration sites; asymptote unchanged; region-average `m` | `.../preloop.gms:71-73` (secdf), `:114-116` (plant), `:29-30` (`i52_m_avg_*`); both overwrites keep `fm_carbon_density(...,"secdforest","vegc")` as `A` |
| "FRA below LPJmL in most regions" is the code's own wording | `modules/52_carbon/normal_dec17/input.gms:47` |
| `pm_carbon_density_*_ac_uncalib` snapshot | `modules/52_carbon/normal_dec17/start.gms:43-44` |
| **Uncalibrated**-curve reader set (M14 `:66`, M29 `:46,48`, M32 `:59,61,68`, M35 `:242`, `:117`) | all five citations land exactly |
| `youngsecdf` fix history: commit `6b00f9dea` (2026-07-01), pre-fix line really did read `im_growing_stock(...,"secdforest")`, author's carbon-arbitrage motivation quoted accurately | `git show 6b00f9dea -- modules/35_natveg/pot_forest_may24/equations.gms`; `im_growing_stock_ysf` block at `modules/14_yields/managementcalib_aug19/presolve.gms:64-71`; consumed at `.../35_natveg/pot_forest_may24/equations.gms:166` |
| M35 blend `:248-252`; natural-origin harvest bound `:177-180`; 20 tC/ha maturation `:117`; othernat curve `:240`; caveat-2 algebra (`q35_prod_secdforest` reads pure calibrated `im_growing_stock` at `equations.gms:147`) | exact |
| M59 `q59_som_target_cropland :20-27` (all four terms, in order), `q59_som_pool :46-52`, `q59_carbon_soil :61-64` | exact; the doc's 4-term expansion at `:126-132` matches the GAMS one-for-one |
| `i59_lossrate(t)=1-0.85**m_yeardiff(t)` and the §5.2 table (56/44, 80/20, 96/4) | `modules/59_som/cellpool_jan23/preloop.gms:45`; re-derived 0.5563 / 0.8031 / 0.9612 |
| `i59_subsoilc_density` = `fm_carbon_density(...,"other","soilc") − f59_topsoilc_density` — the M52→M59 derivation **direction** and the "other land" qualifier are both right | `modules/59_som/cellpool_jan23/preloop.gms:12` |
| `s59_scm_target = 0` (`config/default.cfg:1978`), `s59_cost_scm_recur = 65` (`input.gms:15`), `c59_irrigation_scenario = "on"` (`config/default.cfg:1956`, `input.gms:61`) with off-branch forcing the factor to 1 (`input.gms:70`) | exact |
| FMG/FI factor sets **and** their stated defaults | `tillage59` `sets.gms:13-14`, `inputs59` `:16-17`; `preloop.gms:52-55` sets `full_tillage`=1, `medium_input`=1 |
| Pasture limitation | `modules/59_som/cellpool_jan23/realization.gms:21-24` |
| §7.4 MACC applicability map, **exhaustively** | M53 `:29`/`:52`/`:63` and `q53_emissions_resid_burn :70-72` MACC-free; `maccs_ch4 / rice_ch4, ent_ferm_ch4, awms_ch4 /` `modules/57_maccs/on_aug22/sets.gms:28-29`; M51 `:71` over all `n_pollutants_direct` per comment `:62-64`; `q51_emissions_inorg_fert :30-39` MACC-free; `emis_source_n51` `sets.gms:15-16` (no rice) + `preloop.gms:8-10` `.fx=0` with selective relax; M50 `macceff_aug22/presolve.gms:54-64`. Rice appears in `emis_source_n_cropsoils51` **only** as an emission-*factor* table dimension (`declarations.gms:20`, `input.gms:17`), never creating an emission — so "no rice N₂O at all" holds |
| §10.2 item 7 (peatland) end-to-end | `config/default.cfg:1874` (`v2`), `:1931` (`s58_fix_peatland 2020`); `modules/58_peatland/v2/equations.gms:91-92`; `realization.gms:8-17`; peat ∉ `c_pools`, so no double counting |
| No harvested-wood-product carbon pool (limitation 5) | M73 has wood *product demand* sets only; it is not among `vm_carbon_stock` populators |
| Urban soilc = other-land soilc | `modules/52_carbon/normal_dec17/input.gms:35` |
| Every realization named in the doc is the `config/default.cfg` default | 52 `normal_dec17` (1577), 59 `cellpool_jan23` (1937), 56 `price_aug22` (1634), 58 `v2` (1874), 34 `exo_nov21` (1147), 29 `detail_apr24` (814), 35 `pot_forest_may24` (1156), 32 `dynamic_may24` (995), 53 `ipcc2006_aug22` (1604), 57 `on_aug22` (1843), 51 `rescaled_jan21` (1571), 50 `macceff_aug22` (1500), 14 `managementcalib_aug19` (357), 36 `exo_may22` (1212) |
| Units | `vm_carbon_stock` "mio. tC", `vm_emissions_reg` "Tg per yr" (`price_aug22/declarations.gms:34,40`); 44/12 = 3.67; §8.1 immediate figure 56,833 re-derived exact |
| `vm_nr_som` → M51 only; `vm_cost_scm` → M11 only; `vm_feed_intake(i,kap,kall)` declared in M70; `pm_climate_class(j,clcl)` supplied by M45 | `51_nitrogen/rescaled_jan21/equations.gms:58`; `11_costs/default/equations.gms:37`; `70_livestock/fbask_jan16/declarations.gms:18`; `45_climate/static/input.gms:10` |
| GDX symbols used in §9 all exist | `ov_carbon_stock`, `ov_emissions_reg` (`price_aug22/postsolve.gms:25,27`), `ov59_som_pool`/`ov59_som_target` (`cellpool_jan23/postsolve.gms:29-30`), `ov32_land` (`dynamic_may24/postsolve.gms:64`) |

Citation discipline in the two ⚠️ growing-stock blocks is unusually strong — 14 file:line citations, all landing.
The failures cluster in three places: **(a)** the *calibrated*-side half of that same consumer map (B1);
**(b)** `§10 Limitations` prose asserting process states without checking the switch that governs them (B2, B3);
**(c)** worked examples and the verification recipe drifting free of formulas the doc itself sourced from code
(B4, B11, B12, B14).

---

## 1. Bugs

### B1 — **Critical** — `attribution_read` / set membership — the CALIBRATED-curve reader set omits Module 32 (timber plantations) and M14's plantation read

**Doc** `:180` (verbatim duplicate at `:479`):
> "M14 and M35 read the CALIBRATED curve as well - M14 for regular secdforest growing stock
> (`modules/14_yields/managementcalib_aug19/presolve.gms:44`), M35 for secdforest carbon density, which it BLENDS
> with the uncalibrated curve by natural-origin area share…"

**Reality**. The preloop calibration overwrites exactly two parameters: `pm_carbon_density_secdforest_ac`
(`modules/52_carbon/normal_dec17/preloop.gms:71-73`) and `pm_carbon_density_plantation_ac` (`:114-116`).
The **plantation** half of that pair has two readers the doc never names:

* **Module 32** — `p32_carbon_density_ac(t,j,"plant",ac,ag_pools) = pm_carbon_density_plantation_ac(t,j,ac,ag_pools);`
  at `modules/32_forestry/dynamic_may24/presolve.gms:65`, **unconditional** (no `s32_aff_plantation` guard).
  Also `preloop.gms:18` and `:56` (rotation-length inputs).
* **Module 14** — `im_growing_stock(t,j,ac,"forestry")` is built from
  `pm_carbon_density_plantation_ac(t,j,ac,"vegc")` at `modules/14_yields/managementcalib_aug19/presolve.gms:26`.

The paragraph is written as an exhaustive two-sided map — uncalibrated readers enumerated (M14/M29/M32/M35), then
"M14 and M35 read the CALIBRATED curve **as well**". M32 appears in it **only** on the uncalibrated side (`aff`
`:59`, `:61`; `ndc` `:68`). A maintainer scoping a change to `s52_growingstock_calib` would therefore conclude
M32 is untouched — when `"plant"` is the dominant forestry carbon pool and is precisely where the FRA-2025
**plantation** calibration (`i52_k_calib_plant`) lands.

**Severity reasoning (divergence noted)**: an earlier pass rated this Major. I rate it **Critical** by direct match
to the immutable R20 anchor in `audit/flywheel_rubric.md` §1 — *"module doc cited `pm_carbon_density_ac` as having
three consumers when a commit added two more … → Critical (doc said wrong consumer set; user would have missed two
modules in a refactor)"*. Same parameter family, same omission type, same refactor-scoping harm. Anchors are
immutable reference points and outrank the generic "pick the lower tier" tie-breaker.

**Verify** (standalone):
```
$ rg -n 'pm_carbon_density_(plantation|secdforest|other)_ac\(' modules/ --glob '*.gms' \
     | grep -v uncalib | grep -v 52_carbon
modules/32_forestry/dynamic_may24/preloop.gms:18:p32_carbon_density_ac_forestry(t_all,j,ac) = pm_carbon_density_plantation_ac(t_all,j,ac,"vegc");
modules/32_forestry/dynamic_may24/preloop.gms:56:  p32_avg_increment(t_all,j,ac) = pm_carbon_density_plantation_ac(t_all,j,ac,"vegc") / ((ord(ac)+1)*5);
modules/32_forestry/dynamic_may24/presolve.gms:65:p32_carbon_density_ac(t,j,"plant",ac,ag_pools) = pm_carbon_density_plantation_ac(t,j,ac,ag_pools);
modules/35_natveg/pot_forest_may24/presolve.gms:240,248,250   (other-land + secdforest blend)
modules/14_yields/managementcalib_aug19/presolve.gms:26,44,53 (plantation, secdforest, other)
modules/14_yields/dynRegPastrTau_apr26/presolve.gms:26,44,53  (non-default twin realization)
```
*(Precision note: `pm_carbon_density_other_ac` is **not** touched by the calibration, so the `:53` / `:240`
other-land reads are not calibration-sensitive and should not be added to the list.)*

**Fix** — replace the sentence in **both** copies (`:180` and `:479`):
> "M14, **M32** and M35 read the CALIBRATED curves as well: M14 for plantation growing stock
> (`modules/14_yields/managementcalib_aug19/presolve.gms:26`) and secdforest growing stock (`:44`);
> **M32 for the carbon density of existing timber plantations**
> (`modules/32_forestry/dynamic_may24/presolve.gms:65`, unconditional; plus rotation inputs at
> `preloop.gms:18,56`); M35 for secdforest carbon density, which it BLENDS with the uncalibrated curve by
> natural-origin area share (`modules/35_natveg/pot_forest_may24/presolve.gms:248-252`)."

---

### B2 — **Major** — `mechanism` (capability-vs-default) — fire is presented as an active carbon-loss channel; in a default run `wildfire` contributes exactly zero and the whole disturbance channel decays to zero by 2050

**Doc** `:870` (§10.2 item 6) "Fire disturbances (Module 35) cause carbon loss via stock change / But emissions
lumped with general LUC emissions"; also `:221` "Disturbed areas (fire, shifting agriculture)"; `:626`
"Disturbances (fire, shifting agriculture) → reset age classes → carbon loss".

**Reality**. M35 has four mutually exclusive branches keyed on `s35_forest_damage`
(`modules/35_natveg/pot_forest_may24/presolve.gms:13-33`). The default is **2**
(`.../input.gms:27` `/ 2 /`; `config/default.cfg:1184`). That branch (`presolve.gms:19-22`) applies **only**
`f35_forest_lost_share(i,"shifting_agriculture")`, multiplied by `(1 - p35_damage_fader(t))` — a sigmoid reaching 1
at `s35_forest_damage_end = 2050` (`preloop.gms:88`; `config/default.cfg:1186`) — so the disturbance loss decays to
**zero** by 2050.

The `wildfire` driver is a member of `combined_loss / shifting_agriculture, wildfire /` (`sets.gms:14-15`), and
`combined_loss` is read **only** in the `s35_forest_damage = 3` branch (`presolve.gms:24-27`) — not the default,
and not even listed in `input.gms:27`'s own option string (which documents 0, 1, 2, 4). Wildfire therefore causes
**no** carbon loss at all in a default run, rather than loss that is "lumped" with LUC emissions.

Three-check secondary point (AGENT.md primary directive): even under branch 3, `f35_forest_lost_share` is an
exogenous input table titled "Share of area damaged by forest fires" (`input.gms:32-36`) — **parameterized, not
mechanistically modelled**. The part the doc gets right is the *effect* mechanism: the area move `ac_sub → ac_est`
(`presolve.gms:36-38`), which is what produces the carbon loss.

**Verify**:
```
$ grep -n "s35_forest_damage <-" config/default.cfg
1184:cfg$gms$s35_forest_damage <- 2                  # def = 2
$ grep -n "combined_loss" modules/35_natveg/pot_forest_may24/{presolve,sets}.gms
sets.gms:14:  combined_loss(driver_source) Combined loss from fire plus agriculture
presolve.gms:25,26:   … sum((cell(i,j),combined_loss),f35_forest_lost_share(i,combined_loss)) …   # if(s35_forest_damage=3
$ grep -n "p35_damage_fader" modules/35_natveg/pot_forest_may24/preloop.gms
88:m_sigmoid_time_interpol(p35_damage_fader,sm_fix_SSP2,s35_forest_damage_end,0,1);
```

**Fix** — rewrite item 6 and apply the same qualifier at `:221`, `:626`:
> "**6. No fire disturbance in a default run.** Age-class disturbance is gated by `s35_forest_damage` (default
> **2**, `config/default.cfg:1184`), whose branch applies only the `shifting_agriculture` share and fades it to
> zero by `s35_forest_damage_end = 2050` (`modules/35_natveg/pot_forest_may24/presolve.gms:19-22`,
> `preloop.gms:88`). The `wildfire` share enters only under `s35_forest_damage = 3` via `combined_loss`
> (`sets.gms:14-15`, `presolve.gms:24-27`) — and even then it is an applied historical area share
> (`f35_forest_lost_share`), not a modelled fire process. Where active, it moves area `ac_sub → ac_est`
> (`presolve.gms:36-38`); the resulting carbon loss is indistinguishable from general LUC emissions in
> `vm_emissions_reg`."

---

### B3 — **Major** — `mechanism` — "primary forest carbon density does NOT change over time" is false under the default climate scenario, and contradicts §8.3 of this same doc

**Doc** `:201` "Carbon density does NOT change over time (climate change affects future forests, not current
primary)"; table `:194-196` marks all three primforest pools "Static"; `:841-843` (§10.1 item 1) "Primary forest
carbon density does NOT change over time … Implication: May underestimate sequestration in protected primary
forests".

**Reality**. `fm_carbon_density(t_all,j,land,c_pools)` is a **time-indexed** table
(`modules/52_carbon/normal_dec17/input.gms:16-20`). It is collapsed to `y1995` **only** under
`c52_carbon_scenario == "nocc"` (`:22`) and frozen after `sm_fix_cc` only under `nocc_hist` (`:23`); the default is
`cc` (`input.gms:8`; `config/default.cfg:1590`). `q35_carbon_primforest`
(`modules/35_natveg/pot_forest_may24/equations.gms:42-44`) expands via `m_carbon_stock`, whose body evaluates the
density at the **current** timestep: `land(j2,item) * sum(ct, carbon_density(ct,j2,item,ag_pools))`
(`core/macros.gms:99-101`). Primforest soilc likewise moves: M59's non-cropland target is
`vm_land(j2,noncropland59) * sum(ct,f59_topsoilc_density(ct,j2))`
(`modules/59_som/cellpool_jan23/equations.gms:31-34`), frozen only under `c59_som_scenario == "nocc"`
(default `cc`, `input.gms:72`).

The doc contradicts **itself** at `:697-701`: "LPJmL simulates vegetation carbon density under future climate →
Module 52 updates `fm_carbon_density` over time → Carbon stocks change even without land-use change."

The defensible, narrower claim: primforest has **no age-class / successional dynamics** — it sits at the LPJmL
mature density and never accumulates along Chapman-Richards, unlike secdforest.

**Verify**:
```
$ grep -n "c52_carbon_scenario" config/default.cfg
1590:cfg$gms$c52_carbon_scenario  <- "cc"   # def = "cc"
$ sed -n '8p;22p;23p' modules/52_carbon/normal_dec17/input.gms
$setglobal c52_carbon_scenario  cc
$if "%c52_carbon_scenario%" == "nocc"      fm_carbon_density(t_all,j,land,c_pools) = fm_carbon_density("y1995",…);
$if "%c52_carbon_scenario%" == "nocc_hist" … $(m_year(t_all) > sm_fix_cc) …
$ sed -n '99,101p' core/macros.gms      # m_carbon_stock sums over ct -> current timestep
```
*Honest caveat*: `modules/52_carbon/input/lpj_carbon_stocks.cs3` is a run-time input (the directory ships only a
`files` manifest), so I cannot exhibit the year-to-year values. The code path, the existence of the `nocc` freeze
branch, and the doc's own §8.3 all establish that the default leaves the density time-dependent.

**Fix** — `:194-196` "Static" cells → "No age-class dynamics (always at the LPJmL mature density)"; `:201` →
> "Primforest carries **no age/regrowth dynamics** (always at the LPJmL mature value). Its density *does* change
> over time under the default `c52_carbon_scenario = "cc"` (`config/default.cfg:1590`) and
> `c59_som_scenario = "cc"`, because `fm_carbon_density` and `f59_topsoilc_density` are time-varying LPJmL inputs
> evaluated at the current timestep (`core/macros.gms:99-101`); see §8.3."

Amend §10.1 item 1 so the limitation is the missing regrowth/age dynamic, not an absent climate response.

---

### B4 — **Major** — `data_flow_direction` — §9.1's verification recipe reads `pcm_carbon_stock` as if it were time-indexed; it has no `t` dimension *(new — not in the earlier pass)*

**Doc** `:756-779`, specifically `:760`:
```r
carbon_stock_prev <- readGDX(gdx, "pcm_carbon_stock", field="l")
…
stock_change <- (carbon_stock_prev - carbon_stock_curr) / timestep
```

**Reality** — three defects, all checkable against declarations:

1. **`pcm_carbon_stock(j,land,c_pools,stockType)` has no `t` dimension**
   (`modules/56_ghg_policy/price_aug22/declarations.gms:19`). It is overwritten every timestep in postsolve
   (`.../price_aug22/postsolve.gms:8` for `ag_pools`; `modules/59_som/cellpool_jan23/postsolve.gms:13` for
   `soilc`), so the GDX holds only the **final** timestep's values. Subtracting it from the year-indexed
   `ov_carbon_stock` cannot yield a per-timestep stock change — the recipe's central operation is unsound.
   *(This is the defect the surrounding prose is least likely to survive: the snippet's own comment block worries
   about the first timestep length while the previous-stock series does not exist at all.)*
2. **The `stockType` slice is never selected.** `ov_carbon_stock(t,j,land,c_pools,stockType,type)` carries the
   dimension (`.../price_aug22/postsolve.gms:25`); summing both slices double-counts and discards the very
   distinction §2.3 is built on.
3. **Cell-vs-region mismatch.** `vm_emissions_reg(i,emis_source,pollutants)` is regional and `emis_source`-indexed
   (`.../price_aug22/declarations.gms:40`), and `q52_emis_co2_actual` already performs `sum(cell(i2,j2),…)`
   (`modules/52_carbon/normal_dec17/equations.gms:17-19`). `dimSums(stock_change, dim=c("cell","land","c_pools"))`
   (`:775`) collapses to a global scalar and destroys the `emis_land` mapping, so `all.equal()` compares
   incompatible objects. The emissions side also needs restricting to `emis_oneoff`, since
   `ov_emissions_reg[,,"co2_c"]` additionally carries the annual `peatland` source (`core/sets.gms:322`).

**Verify**:
```
$ rg -n 'pcm_carbon_stock\(j' modules/56_ghg_policy/price_aug22/declarations.gms
19: pcm_carbon_stock(j,land,c_pools,stockType)   Carbon stock in vegetation soil and litter … (mio. tC)
$ rg -n 'ov_carbon_stock\(t' modules/56_ghg_policy/price_aug22/postsolve.gms
25: ov_carbon_stock(t,j,land,c_pools,stockType,"level") = vm_carbon_stock.l(j,land,c_pools,stockType);
```

**Fix** — build the lag from `ov_carbon_stock` itself, pin the slice, and aggregate through `emis_land`:
```r
cs   <- readGDX(gdx, "ov_carbon_stock", select = list(type = "level"))[,,"actual"]
yrs  <- getYears(cs, as.integer = TRUE)
step <- diff(yrs)                                  # m_timestep_length is 1 for ord(t)=1 (core/macros.gms:41,51)
prev <- setYears(cs[, -length(yrs), ], yrs[-1])
stock_change <- (prev - cs[, -1, ]) / step
```
plus a one-line warning: "`pcm_carbon_stock` is **not** time-indexed
(`modules/56_ghg_policy/price_aug22/declarations.gms:19`) — the GDX carries only its final-timestep value; never
use it for a time-series check." Drop `field="l"` (it is a parameter), and map cells → regions and
`land × c_pools` → `emis_oneoff` before comparing (or compare a single global total on both sides and say so).

---

### B5 — Minor — `attribution_populate` — the §3.7 table attributes the urban vegc/litc zeroing to Module 52; Module 34 does it

**Doc** `:263-264`: rows `vegc | Fixed to zero | None | **52**` and `litc | Fixed to zero | None | **52**`.

**Reality**: the zeroing is `vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0;` in **Module 34**
(`modules/34_urban/exo_nov21/presolve.gms:8`; default realization `config/default.cfg:1147`). Module 52 touches
urban only for **soilc**, setting the *density* to the other-land value
(`modules/52_carbon/normal_dec17/input.gms:35`) — it never zeroes vegc/litc. The doc's own §7.5 (`:622`)
attributes the fix correctly to M34, so the table contradicts the body. (The `soilc | 52, 59` row at `:265` is
right: M52 sets the density, M59 populates the stock via `q59_carbon_soil`.)

**Verify**: `rg -n 'vm_carbon_stock' modules/ | grep urban` → only
`modules/34_urban/exo_nov21/presolve.gms:8` and `modules/34_urban/static/presolve.gms:10`.

**Fix**: change the Module column of the vegc and litc rows from `52` to `34`, footnoted "fixed via
`vm_carbon_stock.fx`, `modules/34_urban/exo_nov21/presolve.gms:8`".

---

### B6 — Minor — `set_membership` — the "FLU: Cropland / Set-aside / Perennial" category set does not exist in Module 59

**Doc** `:428` "**FLU** (Land Use): Cropland / Set-aside / Perennial (default: annual cropland)"; `:137`
"Land use: Cropland vs set-aside".

**Reality**: `modules/59_som/cellpool_jan23/sets.gms` declares `tillage59`
(`/full_tillage,reduced_tillage,no_tillage/`, `:13-14`) and `inputs59`
(`/low_input,medium_input,high_input_nomanure,high_input_manure/`, `:16-17`) — so the doc's FMG and FI bullets and
their defaults (`preloop.gms:52-55`) are exactly right. There is **no** land-use-category set. The IPCC land-use
factor is pre-resolved **per MAgPIE crop type**: `table f59_cratio_landuse(i,climate59_2019,kcr)`
(`input.gms:43`), consumed at `preloop.gms:16,62`. Fallow and tree cover carry their own dedicated ratios
(`i59_cratio_fallow`, derived from the maize ratio at `preloop.gms:73-75`; `i59_cratio_treecover = 1` at `:82`) —
not a "set-aside" FLU member.

**Verify** (absence claim, second method + positive control):
```
$ rg -in 'setaside|set-aside|set_aside|perennial' modules/59_som/
modules/59_som/static_jan19/realization.gms:16   (prose)
modules/59_som/cellpool_jan23/input.gms:24       (prose)
$ rg -c 'cratio' modules/59_som/cellpool_jan23/preloop.gms
13                                                # positive control: the search works there
```

**Fix**: `:428` → "**FLU** (Land Use): not a category switch in MAgPIE — the IPCC land-use factor is pre-resolved
**per crop type** in `f59_cratio_landuse(i,climate59_2019,kcr)`
(`modules/59_som/cellpool_jan23/input.gms:43`); fallow and tree cover carry separate ratios
(`preloop.gms:73-75,82`)." Same correction at `:137`.

---

### B7 — Minor — `citation` — `config/default.cfg:1835` points at a comment line; the assignment is at `:1838`

**Doc** `:101`: "⚠️ Do **not** cite `config/default.cfg:1835` for this default: that line omits the `cfg$gms$`
prefix its siblings carry…"

**Reality**: the assignment is at **`:1838`**. Line 1835 is
`# *   actual: CO2 emissions for pricing are based on the difference of actual carbon stocks between time steps` —
inside the option-comment block, carrying no assignment, so "omits the prefix" does not describe it. The
**substance is re-derived and still correct**: `:1838` reads `c56_carbon_stock_pricing <- "actualNoAcEst"` with no
`cfg$gms$` prefix (siblings at `:1831`, `:1843`, `:1847` have it), and `scripts/start_functions.R:346` passes only
`cfg$gms` to `lucode2::manipulateConfig(file.path(ll,"input.gms"), …)`, so the bare assignment never reaches GAMS.
Values still agree with `modules/56_ghg_policy/price_aug22/input.gms:90`, so nothing miscomputes today.

**Verify**: `grep -n 'c56_carbon_stock_pricing' config/default.cfg` → `1838:…`.
**Fix**: `1835` → `1838`.

---

### B8 — Minor — `attribution_read` — the CH₄ consumer arrow omits Module 57

**Doc** `:573`: "`vm_emissions_reg(i,emis_source,"ch4")`: Regional CH₄ emissions → to Module 56".

**Reality**: role map `vm_emissions_reg: read_by ['56','57']`; both-endpoints grep confirms Module 57 reads it
directly at `modules/57_maccs/on_aug22/equations.gms:38,40,48,50`, dividing by `(1 - im_maccs_mitigation)` to back
out unmitigated emissions for MACC costing. `pollutants_maccs57 = / ch4, n2o_n_direct /`
(`modules/57_maccs/on_aug22/sets.gms:25-26`), so CH₄ is explicitly in scope. A direct read, not transitive.

**Verify**: `rg -n 'vm_emissions_reg' modules/57_maccs/on_aug22/` → four equation-level reads (positive control:
the same grep over `modules/56_ghg_policy/price_aug22/` returns `equations.gms:17`).

**Fix**: "→ **Module 56** (pricing, `modules/56_ghg_policy/price_aug22/equations.gms:15-17`) **and Module 57**
(MACC cost base — back-computes unmitigated emissions,
`modules/57_maccs/on_aug22/equations.gms:38,48`)."

---

### B9 — Minor — `attribution_read` — the `vm_maccs_costs` consumer arrow omits Module 36

**Doc** `:593`: "`vm_maccs_costs(i,factors)`: Labor and capital costs of mitigation → to Module 11".

**Reality**: role map `vm_maccs_costs: read_by ['11','36']`. `modules/36_employment/exo_may22/equations.gms:28`
reads the `"labor"` slice and converts it to employment; `exo_may22` is the only realization and the default
(`config/default.cfg:1212`). M11 sums over all `factors` (`modules/11_costs/default/equations.gms:28`).

**Verify**: `rg -n 'vm_maccs_costs' modules/ | grep -v 57_maccs` → exactly those two lines.

**Fix**: "→ **Module 11** (total-cost objective, `modules/11_costs/default/equations.gms:28`, all `factors`)
**and Module 36** (the `"labor"` factor becomes employment,
`modules/36_employment/exo_may22/equations.gms:28`)."

---

### B10 — Minor — `mechanism` — litter "decomposition to soil organic matter" is a flux MAgPIE does not model

**Doc** `:73` (§2.2 Litter → Dynamics): "**Decomposition**: Gradual breakdown to soil organic matter (20-year IPCC
timescale)".

**Reality**: there is **no litter → soil carbon flux anywhere in the model**. `m_growth_litc_soilc`
(`core/macros.gms:20`) linearly ramps the *litter pool itself* from `pc52_carbon_density_start(...,"litc")`
(= pasture litc, `modules/52_carbon/normal_dec17/start.gms:10`) to the land type's own litc equilibrium over 20
years (`start.gms:19-20,30-31,51`) — a convergence of `litc` toward its own LPJmL target, not a transfer into
`soilc`. The soil side is independent: `q59_som_target_cropland` (`modules/59_som/cellpool_jan23/equations.gms:20-27`)
and `q59_som_target_noncropland` (`:31-34`) are functions of area × `cratio` × `f59_topsoilc_density`, with no
litter term. `litc` does not appear anywhere in `modules/59_som/`.

**Verify** (absence claim, second method + positive control):
```
$ rg -n 'litc' modules/59_som/ ; echo "exit=$?"
exit=1                                                    # no match anywhere in module 59
$ rg -c 'soilc' modules/59_som/cellpool_jan23/equations.gms
6                                                         # positive control
$ sed -n '20p' core/macros.gms
$macro m_growth_litc_soilc(start,end,ac) (start + (end - start) * 1/20 * ac*5)$(ac <= 20/5) + end$(ac > 20/5);
```

**Fix**: `:73` → "**Convergence**: the litter pool is linearly interpolated toward its own land-type equilibrium
over 20 years (IPCC horizon, `core/macros.gms:20`, applied at
`modules/52_carbon/normal_dec17/start.gms:19-20,30-31`). MAgPIE does **not** model a decomposition flux from `litc`
into `soilc` — the pools converge independently to their own targets, and Module 59's soil equations contain no
litter term."

---

### B11 — Minor — `formula` — the §6.3 growth table does not satisfy Chapman-Richards with the A/k/m it states

**Doc** `:486-500`: "A = 100 tC/ha, k = 0.06, m = 2.0", then tabulates 14 / 26 / 44 / 58 / 75 / 88 / 93 tC/ha at
5 / 10 / 20 / 30 / 50 / 80 / 100 yr.

**Reality**: `m_growth_vegc(S,A,k,m,ac) = S + (A-S)*(1-exp(-k*(ac*5)))**m` (`core/macros.gms:18`). With
S=0, A=100, k=0.06, m=2.0 the curve is **6.72 / 20.36 / 48.83 / 69.67 / 90.29 / 98.36 / 99.50** — 2.1× off at 5 yr
and saturating far faster than the doc's column. The tabulated numbers instead track a k≈0.03, m=1 curve
(13.9 / 25.9 / 45.1 / 59.3 / 77.7 / 90.9 / 95.0). The error propagates into §8.2, which reuses "44 % of mature"
(`:676`) and "75 % of mature" (`:682`). The age-class ↔ year mapping (`ac1`=5 yr … `ac20`=100 yr) is correct
against `(ord(ac)-1)*5`.

**Verify**:
```
$ python3 -c "import math;A,k,m=100,0.06,2.0;print([round(A*(1-math.exp(-k*t))**m,2) for t in (5,10,20,30,50,80,100)])"
[6.72, 20.36, 48.83, 69.67, 90.29, 98.36, 99.5]
```

**Fix**: regenerate the column from the stated parameters (values above), or state the (k, m) that actually produce
the tabulated curve; update the two dependent figures in §8.2. Keep the "illustrative" note either way, and add
"computed from `core/macros.gms:18`" so the next editor can re-derive it.

---

### B12 — Minor — `formula` — §8.4 (and §8.2) convergence percentages contradict §5.2 and `preloop.gms:45`

**Doc** `:734` "Year 5: **44 %** toward new equilibrium = +4 tC/ha"; `:678` "soilc: 70 tC/ha (**80 %** toward
natural)" at **Year 20**; `:684` "soilc: 78 tC/ha (**96 %** toward natural)" at **Year 50**.

**Reality**: `i59_lossrate(t) = 1 - 0.85**m_yeardiff(t)` (`modules/59_som/cellpool_jan23/preloop.gms:45`) gives
**55.6 %** at 5 yr, 80.3 % at 10 yr, **96.1 %** at 20 yr, **99.97 %** at 50 yr. 44 % is the *remaining legacy*
share at 5 yr, and the doc's own §5.2 table (`:401-404`) already states 56/44 correctly — so `:734` contradicts
`:402`, and `:678`/`:684` are each shifted one row up that same table. (Root of the confusion: the code comment at
`preloop.gms:42` itself reads "resulting in 44 % in 5 years" — worth not inheriting.)

**Verify**: `python3 -c "print([round(100*(1-0.85**y),2) for y in (1,5,10,20,50)])"` → `[15.0, 55.63, 80.31, 96.12, 99.97]`

**Fix**: `:734` → "Year 5: **56 %** toward new equilibrium = +5 tC/ha"; `:678` → "(**96 %** toward natural)";
`:684` → "(**>99 %**, effectively at equilibrium)". Re-derive the dependent tC/ha figures and the sequestration
totals at `:688-689`. Optionally footnote that `preloop.gms:42`'s "44 %" is the remaining legacy.

---

### B13 — Minor — `formula` — `q29_carbon` is described as aggregating only `vm_carbon_stock_croparea`; it has three addends *(new — the earlier pass marked this row clean)*

**Doc** `:610`: "`q29_carbon` aggregates `vm_carbon_stock_croparea` (from M30) into the cropland slice of
`vm_carbon_stock(j2,"crop",...)` (`modules/29_cropland/detail_apr24/equations.gms:39`)".

**Reality** (`modules/29_cropland/detail_apr24/equations.gms:38-42`; default realization, `config/default.cfg:814`):
```gams
q29_carbon(j2,ag_pools,stockType) ..
  vm_carbon_stock(j2,"crop",ag_pools,stockType) =e=
    vm_carbon_stock_croparea(j2,ag_pools)
    + vm_fallow(j2) * sum(ct, fm_carbon_density(ct,j2,"crop",ag_pools))
    + m_carbon_stock_ac(v29_treecover,p29_carbon_density_ac,"ac","ac_sub");
```
Three terms, not one. The attribution half of the doc's sentence is right (M30 populates
`vm_carbon_stock_croparea`, M29 reads it — role map `populated_by ['30']`, `read_by ['29','30']`); the mechanism
half omits fallow and tree cover. The tree-cover addend matters for this doc's own narrative: it runs on
`p29_carbon_density_ac`, i.e. the **uncalibrated** curve (`modules/29_cropland/detail_apr24/preloop.gms:46,48`),
which the doc already discusses at `:180`/`:479`. This is the same omission class the doc explicitly corrected for
`v59_som_target` at `:134`.

**Verify**: `sed -n '38,42p' modules/29_cropland/detail_apr24/equations.gms` → the block above.

**Fix**: `:610` →
> "`q29_carbon` (`modules/29_cropland/detail_apr24/equations.gms:38-42`) populates the cropland slice as the sum of
> three terms: `vm_carbon_stock_croparea` (computed in M30), fallow area ×
> `fm_carbon_density(...,"crop",...)`, and the age-class tree-cover stock
> `m_carbon_stock_ac(v29_treecover,p29_carbon_density_ac,…)` — the last built on the **uncalibrated** growth curve
> (`preloop.gms:46,48`; see §6.2)."

---

### B14 — Informational — `formula` — §8.1 gradual soil-carbon emission is 550 Tg CO₂/yr, not 458

**Doc** `:656`: "Gradual (soilc over 20 years): 30 tC/ha × 100 Mha × (44/12) / 20 years = **458 Tg CO₂/year**".
**Reality**: `30 × 100 × 44/12 / 20 = 550.0` (458 corresponds to 25 tC/ha; the table at `:649` says 30). The
immediate-emission line at `:655` re-derives exactly (56,833), so this is an isolated slip, not a unit problem.
**Verify**: `python3 -c "print(30*100*44/12/20)"` → `550.0`. **Fix**: `458` → `550`.

---

### B15 — Informational — `citation` — interface-parameter domains written as `t` where the declaration is `t_all`

**Doc** `:513` `fm_carbon_density(t,j,land,c_pools)`; `:514-516` `pm_carbon_density_{plantation,secdforest,other}_ac(t,j,ac,ag_pools)`;
same form at `:101`, `:107`, `:699`.
**Reality**: `modules/52_carbon/normal_dec17/input.gms:16` and `declarations.gms:9-13` declare over `t_all`.
`t` and `t_all` are distinct MAgPIE sets (optimized vs. all timesteps); inside equations these are read as
`sum(ct, …)`.
**Fix**: use `t_all` in the "Provides" list, or the equation-side `(ct,…)` form — consistently.

---

### B16 — Informational — `set_membership` — §1's "Mathematical Concept" quantifies over cells; the identity is realized per region

**Doc** `:21-23`: "∀ j ∈ Cells, ∀ t ∈ Time: CO₂ Emissions(t) = [Carbon Stock(t−1) − Carbon Stock(t)] / Timestep Length".
**Reality**: `q52_emis_co2_actual(i2,emis_oneoff)` writes `vm_emissions_reg(i2,…)` — indexed by **region `i`** and
by `emis_oneoff`, with cells summed inside (`modules/52_carbon/normal_dec17/equations.gms:16-19`). Module 52 has no
cell-level CO₂ emission variable. §4.1 renders it correctly two sections later.
**Fix**: "∀ i ∈ Regions, ∀ s ∈ `emis_oneoff`, ∀ t ∈ Time: CO₂ Emissions(i,s,t) = Σ_{j∈i} [Stock(t−1) − Stock(t)] /
Timestep Length".

---

## 2. Deferred (no bug asserted, no edit proposed)

1. `:467-469` `f52_growth_par` k ranges ("tropical k ≈ 0.05-0.08" etc.) — `modules/52_carbon/input/` ships only a
   `files` manifest; the CSV is a run-time input. Not confirmable or refutable here.
2. `:436-438` IPCC stock-change factor values (0.69, 1.17) — labelled "typical values from IPCC"; the
   `f59_ch5_F_*` tables are run-time inputs, absent from the tree.
3. `:592` `im_maccs_mitigation` "(0 to ~0.3)" — depends on the PBL_2022 MACC input tables; not checkable offline.
4. `:875` "Module 59 models **mineral** soil carbon only" — structurally plausible (IPCC ch.5 mineral stock-change
   tables, LPJmL topsoil reference, peat absent from `c_pools`) but the `f59_ch5_*` inputs are gitignored.
5. `:95-96` / `:851` Subsoil "Static (fixed from LPJmL via M52)" — `i59_subsoilc_density(t_all,j)`
   (`modules/59_som/cellpool_jan23/preloop.gms:12`) *is* time-varying under the default `cc`; the adjacent bullet
   ("Not affected by land use") supplies the intended meaning, so not filed. Worth tightening if a fix pass
   touches §2.3.
6. `:255` caveat 2 (the `secdforest` yield-vs-carbon blend gap) is correctly self-labelled "unverified lead". The
   algebra re-checks out (`q35_prod_secdforest` reads the purely calibrated `im_growing_stock` at
   `modules/35_natveg/pot_forest_may24/equations.gms:147`; `q35_carbon_secdforest` reads the blend from
   `presolve.gms:248-252`), but confirming or refuting it needs a run.
7. M32's two *preloop*-phase reads of `pm_carbon_density_plantation_ac`
   (`modules/32_forestry/dynamic_may24/preloop.gms:18,56`) may capture pre-calibration values if module 32's
   preloop runs before module 52's. Plausible from `modules/include.gms` ordering, but I did not verify the phase
   dispatch end-to-end this session — **flagged, not asserted**, and deliberately excluded from B1's proposed edit
   (B1 rests on `presolve.gms:65`, which is unambiguous).
8. R-side semantics of the §9 snippets beyond the GAMS facts in B4 (e.g. `readGDX(..., field="l")` on a parameter)
   — magpie4/magclass behaviour is outside this lens's ground truth.
9. `:5` "Modules Covered: 52, 53, 59 (57 for mitigation costs)" understates the doc's actual coverage (29, 31, 32,
   34, 35, 56, 58 all appear substantively). Editorial, not a factual error — no fix proposed.
