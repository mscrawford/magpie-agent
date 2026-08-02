# R60 depth audit — `cross_module/modification_safety_guide.md`

**Lens**: `consumer_read` (enter from the consumer side; whole-tree greps of both `NAME(` and `NAME.`; prioritise READ/consumer set claims, phantoms and omissions, solution-level `.l/.lo` reads)
**Ground truth**: MAgPIE `develop` read-only worktree, HEAD `2c02843ec` (*Merge pull request #919 from alexkoberle/dyn_reg_tau*)
**Role map**: `audit/integrated/depth_rolemap.json` consulted FIRST for every `vm_/pm_/im_/pcm_/fm_` attribution claim, then confirmed by an independent both-endpoints grep.
**Claims verified**: 88 · **Bugs**: 12 (1 Critical, 9 Major, 2 Minor)

---

## 0. What the lens CLEARED (report the negatives — they are the decorrelation value)

Every consumer/producer count and set in this doc that I could check was **correct**. That is unusual and worth recording, because it means the residual defects are not in the count machinery.

| Doc claim | Verified? | Code-derived set (producer excluded) |
|---|---|---|
| `vm_land` → **10** consumers, listed as 22, 29, 30, 31, 32, 34, 35, 50, 58, 59 (§1.2 L46, L55) | ✅ exact | {22, 29, 30, 31, 32, 34, 35, 50, 58, 59} |
| `vm_lu_transitions` → 3 (§1.2 L47) | ✅ | {29, 35, 59} |
| `vm_landexpansion` → 4 (§1.2 L48) | ✅ | {35, 39, 58, 59} |
| `vm_landreduction` → 2 (§1.2 L49) | ✅ | {39, 58} |
| `pcm_land` → 12 (§1.2 L50) | ✅ | {13, 22, 29, 31, 32, 34, 35, 44, 56, 58, 59, 71} |
| 18-module union over ALL M10 interface vars (§1.2 L58) | ✅ exact | union of the five above + `vm_landdiff`→{80}, `pm_land_hist/start`→{14,29,32,59,71}, `vm_cost_land_transition`→{11} = 18 |
| "ALL 11 modules touched by `vm_land`+`landexpansion`+`landreduction`+`lu_transitions`" (§1.5 L157) | ✅ | {22,29,30,31,32,34,35,39,50,58,59} = 11 |
| `vm_prod_reg` → 8: 16, 18, 20, 21, 38, 50, 70, 71 (§3.2 L335, L338) | ✅ exact | same 8 |
| `pm_prod_init` → 1: 38_factor_costs (§3.2 L336, L338) | ✅ | {38} |
| `vm_emission_costs` → 11_costs, 15_food (§4.2 L462) | ✅ | {11, 15}; the 15_food read is solution-level, `modules/15_food/anthro_iso_jun22/intersolve.gms:23` |
| `im_pollutant_prices` → 57_maccs at `on_aug22/preloop.gms:24-25` (§4.2 L464) | ✅ line-exact | {57} |
| `vm_reward_cdr_aff` → 11_costs (§4.2 L463) | ✅ | {11} |
| Appendix B: `vm_land` 10 / `im_pop_iso` 10 / `pm_interest` 9 / `vm_prod` 8 / `vm_prod_reg` 8 / `vm_area` 8, with producers (§Appendix B L1094-1099) | ✅ all 12 | — |
| Appendix A centrality table, all 44 cells + banding rule + `11_costs` owns-1/reaches-1/depends-27 footnote | ✅ reproduced exactly | `python3 audit/tools/compute_module_centrality.py --table` |
| "Module 11 depends on cost variables from **27** modules" (§2.2 L217) | ✅ | 27 distinct producers across the 35 terms of `q11_cost_reg` |
| All 7 cost-variable → source-module rows (§2.2 L221-227) | ✅ all 7 | — |
| Module 56 switch defaults: `c56_pollutant_prices`, `c56_emis_policy`, `c56_carbon_stock_pricing`, `s56_c_price_induced_aff` (§4.3 L481-484) + `input.gms:69` citation (§4.5 L535) | ✅ incl. `config/default.cfg` | — |
| `q56_emis_pricing_co2` uses `(pcm_carbon_stock − vm_carbon_stock)` (§4.5 L546) | ✅ | `modules/56_ghg_policy/price_aug22/equations.gms:19-22` |
| `pcm_land` calculation at `10_land/landmatrix_dec18/postsolve.gms:8-9` (§1.3 L79) | ✅ line-exact | — |
| `pm_prod_init` init formula at `17_production/flexreg_apr16/presolve.gms:10` (§3.4 L389-392) | ✅ line-exact and character-exact | — |
| §1.4 transition-matrix row/column identities (L109-110) | ✅ | matches `q10_transition_from` / `q10_transition_to` |
| Realization paths for M10/M11/M17/M56 (§1.1, §2.1, §3.1, §4.1) | ✅ all four are the sole/default realization | — |

Two lens-specific catches worth noting as *cleared*, not bugs:

- **58_peatland is a genuine `vm_land` consumer even though `rg 'vm_land\('` misses it.** It reads `vm_land` bare, as a macro argument: `m58_LandMerge(vm_land, vm_land_forestry, "j2")` at `modules/58_peatland/v2/equations.gms:23`. Both `NAME(` and `NAME.` greps return nothing for M58 — only a `\bvm_land\b` grep finds it. The role map had it right and my first grep was wrong. Default `peatland = v2`, so this is live.
- **22_land_conservation is a genuine `vm_land` consumer only through the attribute form** — `vm_land.lo(j,"crop")` on the RHS at `modules/22_land_conservation/area_based_apr22/presolve_ini.gms:86,97,108`. Invisible to `vm_land(`. Exactly the R33 pattern.

---

## 1. Bugs

### B1 — Critical — `mechanism` — §3.4 MISTAKE 1 (doc L367-378)

**Doc claims**
> "**❌ MISTAKE 1**: Forgetting that `vm_prod_reg` only covers PLANT commodities … `* ERROR: Livestock modeled at regional level (Module 70), not cell level`"
> "**✅ FIX**: Check commodity scope — **Module 17 handles**: Crops (kcr), pasture · **Module 70 handles**: Livestock (kli) — regional only · **Module 73 handles**: Timber — special aggregation"

**Reality** — every clause is false in a default run.

1. `q17_prod_reg(i2,k) .. vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k));` — `modules/17_production/flexreg_apr16/equations.gms:10-11`. Its domain is the set `k`, not `kcr`+pasture.
2. `k(kall)` = `… begr, betr, livst_rum, livst_pig, livst_chick, livst_egg, livst_milk, fish, wood, woodfuel` — `modules/14_yields/managementcalib_aug19/sets.gms:12-18` (the default yields realization; identical in `dynRegPastrTau_apr26`). Livestock, fish and timber are all in `k`.
3. Livestock **is** at cell level. `71_disagg_lvst` (default realization `foragebased_jul23`, `config/default.cfg:2221`) writes `vm_prod(j2,kli_rum)` and `vm_prod(j2,kli_mon)`: `modules/71_disagg_lvst/foragebased_jul23/equations.gms:23` and `:56`.
4. Timber is not "special aggregation": `73_timber` writes `vm_prod(j2,"wood")` / `vm_prod(j2,"woodfuel")` at cell level (`modules/73_timber/default/equations.gms:44,53`) and `q17_prod_reg` aggregates them like everything else.

The GAMS line the doc labels **WRONG** (`vm_prod_reg(i,"beef") = sum(cell(i,j), vm_prod(j,"beef"))`) is, modulo the phantom commodity name, *precisely what `q17_prod_reg` already does* for livestock.

**Why Critical (not Major)**: this guide exists to tell a developer what breaks when they touch Module 17. A developer who believes "vm_prod_reg only covers plants" and narrows `q17_prod_reg`'s domain from `k` to `kcr` silently severs livestock and timber from regional production — the R20-anchor harm class (a refactor that misses modules), on the model's highest-traffic aggregation equation.

**Verify**
```
rg -n 'q17_prod_reg' /tmp/<develop>/modules/17_production/flexreg_apr16/equations.gms
  -> 10:q17_prod_reg(i2,k) ..
sed -n '12,18p' modules/14_yields/managementcalib_aug19/sets.gms
  -> k(kall) ... livst_rum, livst_pig, livst_chick, livst_egg, livst_milk, fish, wood, woodfuel
rg -n 'vm_prod\(j2,kli' modules/71_disagg_lvst/foragebased_jul23/equations.gms
  -> 23: ... vm_prod(j2,kli_rum)   56: vm_prod(j2,kli_mon) =l=
grep -n 'disagg_lvst' config/default.cfg
  -> 2221:cfg$gms$disagg_lvst <- "foragebased_jul23"   # def = foragebased_jul23
```

**Fix**: replace MISTAKE 1 entirely. `q17_prod_reg` covers the whole set `k` (crops, pasture, **livestock, fish, wood, woodfuel**). The slices of `vm_prod_reg(i,kall)` that M17 does *not* determine are the ones outside `k`: `kres` (fixed by `q18_prod_res_reg`, `modules/18_residues/flexreg_apr16/equations.gms:79-82`) and `ksd` (`q20_processing`, `modules/20_processing/substitution_may21/equations.gms:59-66`). Recast the mistake as "forgetting that the `kres`/`ksd` slices of `vm_prod_reg` are owned by M18/M20, not M17".

---

### B2 — Major — `attribution_populate` — §3.3 (doc L353)

**Doc claims**
> `Module 30 (Croparea) → vm_prod(j,k) → Module 17 → vm_prod_reg(i,kall) → Module 21 (Trade) …`

**Reality**: `vm_prod` is declared in 17 (`modules/17_production/flexreg_apr16/declarations.gms:9`) and populated by **four** modules, not one: 30 (`30_croparea/detail_apr24/equations.gms:15`), 31 (`31_past/endo_jun13/equations.gms:17`), 71 (`71_disagg_lvst/foragebased_jul23/equations.gms:23,56`), 73 (`73_timber/default/equations.gms:44,53`). Appendix B of this same doc counts 8 modules touching `vm_prod`, so the diagram and the appendix disagree.

**Verify**
```
rg -n 'vm_prod\(' modules/ | grep -vE '^(17_production|.*vm_prod_reg)' | awk -F/ '{print $1}' | sort -u
  -> 18_residues 30_croparea 31_past 38_factor_costs 40_transport 42_water_demand 71_disagg_lvst 73_timber
(writers among those: 30, 31, 71, 73)
```

**Fix**: `Modules 30 (crops), 31 (pasture), 71 (livestock), 73 (timber) → vm_prod(j,k) → Module 17 → …`

---

### B3 — Major — `data_flow_direction` — §4.4 (doc L496-497)

**Doc claims**
> ```
> 56_ghg_policy
>    ├─ Emissions Pricing → 11_costs (objective function)
>    ├─ CDR Rewards → 32_forestry (afforestation incentive)
>    └─ Price Signals → 57_maccs (…preloop.gms:24-25)
> ```

**Reality**: the sibling branches are genuine reads annotated with real edges (11 reads `vm_emission_costs`; 57 reads `im_pollutant_prices`), so the CDR branch reads as the same kind of edge. It is not — and it is **inverted**:

- `vm_reward_cdr_aff` is read only by `11_costs` (`modules/11_costs/default/equations.gms:27`). Module 32 never references it.
- The only 32↔56 interface is `vm_cdr_aff`, declared and written in **32** (`modules/32_forestry/dynamic_may24/declarations.gms:83`, `equations.gms:37,42`) and read by **56** (`modules/56_ghg_policy/price_aug22/equations.gms:77`). Direction is **32 → 56**.
- A full sweep of module 32's interface identifiers turns up nothing from 56 at all (`im_growing_stock`, `im_timber_prod_cost`, `pm_carbon_density_*`, `pm_demand_forestry`, `pm_interest`, `pm_land_conservation`, `pm_land_plantation`, `pm_land_start`, `pm_max_forest_est`).

M32 responds to the CDR reward only through the shared objective, exactly the "economic knock-on" the doc annotates on the *third* branch. This is the R51/MANDATE-21 pattern.

**Verify**
```
rg -n '\bvm_reward_cdr_aff\b' modules/
  -> only 11_costs/default/equations.gms:27 and 56_ghg_policy/{equations,declarations,postsolve}.gms
grep -rhoE '\b(im|pm)_[a-zA-Z0-9_]+' --include='*.gms' modules/32_forestry | sort -u
  -> no 56_* interface present
```

**Fix**: `└─ CDR valuation ← vm_cdr_aff from 32_forestry (32 → 56); the reward vm_reward_cdr_aff is subtracted in 11_costs (equations.gms:27) — 32 responds via the objective, not via any variable it reads from 56.`

---

### B4 — Major — `formula` — §6.1 Error Pattern 1, Fix step 2 (doc L827)

**Doc claims**: "Verify transition matrix: `sum(land_from, vm_lu_transitions) = pcm_land`"

**Reality — indices inverted** (`modules/10_land/landmatrix_dec18/equations.gms:19-25`):
```
q10_transition_to(j2,land_to)   .. sum(land_from, vm_lu_transitions(j2,land_from,land_to)) =e= vm_land(j2,land_to);
q10_transition_from(j2,land_from) .. sum(land_to,   vm_lu_transitions(j2,land_from,land_to)) =e= pcm_land(j2,land_from);
```
Summing over `land_from` yields `vm_land`, not `pcm_land`. The doc's own §1.4 (L109-110) states this correctly, so §6.1 also contradicts §1.4.

**Verify**: `sed -n '19,25p' modules/10_land/landmatrix_dec18/equations.gms` → as quoted.

**Fix**: `sum(land_to, vm_lu_transitions(j,land_from,land_to)) = pcm_land(j,land_from)` (q10_transition_from) **and** `sum(land_from, …) = vm_land(j,land_to)` (q10_transition_to).

*(Same section, L821: "sum(vm_land) ≠ pcm_land" should be `sum(land, vm_land(j,land)) ≠ sum(land, pcm_land(j,land))` — `q10_land_area` at equations.gms:13-15 constrains the cell **totals**, not per-type equality. Folded here.)*

---

### B5 — Major — `formula` — §1.5 Testing Protocol, test 2 (doc L146-153)

**Doc claims** (in a suite headed "MUST pass all"):
```r
row_sums <- dimSums(transitions, dim="to")
col_sums <- dimSums(transitions, dim="from")
stopifnot(all(abs(row_sums - col_sums) < 1e-6))
```

**Reality**: `row_sums` (sum over `land_to`, indexed by `land_from`) **is** `pcm_land`; `col_sums` (sum over `land_from`, indexed by `land_to`) **is** `vm_land` — `modules/10_land/landmatrix_dec18/equations.gms:19-25`. They are equal element-wise only when nothing converts, i.e. the test fails on **every** run with land-use change. Only the grand totals match (`q10_land_area`, equations.gms:13-15).

**Verify**: same `sed -n '13,25p' modules/10_land/landmatrix_dec18/equations.gms`.

**Fix**: test `row_sums == pcm_land` and `col_sums == vm_land` separately, or test only the grand total `sum(row_sums) == sum(col_sums)`.

---

### B6 — Major — `formula` (units) — §4.3 L481, §4.5 L520, §6.1 L886

**Doc claims**: `c56_pollutant_prices` → "Price trajectory (0-1000+ **USD/tCO2**)"; "Typical range: 0-500 **USD/tCO2** by 2100"; "Check `im_pollutant_prices`: should be 0-500 **USD/tCO2**".

**Reality**: for `co2_c`, `im_pollutant_prices` is **USD17MER per t C**, not per t CO2 — a factor 44/12 = 3.67.
- `im_pollutant_prices(t_all,i,pollutants,emis_source) … (USD17MER per Mg)` of the pollutant's own mass unit — `modules/56_ghg_policy/price_aug22/declarations.gms:9` ("N2O-**N** CH4 CO2-**C**").
- The floor applied directly to it is `s56_minimum_cprice … (USD17MER per tC) / 3.67 /` — `input.gms:67`, applied at `preloop.gms:74`. 3.67 USD/tC ≡ 1 USD/tCO2.
- `p56_c_price_aff … (USD17MER per tC)` is a straight copy of `im_pollutant_prices(t_all,i,"co2_c",…)` — `declarations.gms:11`, `preloop.gms:115`.
- Dimensional check: `v56_emis_pricing` for `co2_c` derives from `vm_carbon_stock … (mio. tC)` (`declarations.gms:34`), so price × quantity = mio. USD only if price is per tC.

A user following L886 and setting `im_pollutant_prices(...,"co2_c",...) = 200` intending 200 USD/tCO2 actually imposes ~54.5 USD/tCO2.

**Verify**
```
grep -n 'im_pollutant_prices\|p56_c_price_aff\|vm_carbon_stock' modules/56_ghg_policy/price_aug22/declarations.gms
grep -n 's56_minimum_cprice' modules/56_ghg_policy/price_aug22/input.gms   -> 67: ... (USD17MER per tC) / 3.67 /
```

**Fix**: state the range as USD/tC, or keep USD/tCO2 and add "× 44/12 to convert to the model's `im_pollutant_prices` units (USD17MER per tC)". Same edit at all three lines.

---

### B7 — Major — `attribution_read` — §1.6 (doc L177)

**Doc claims**: "**✅ SAFE**: Modifying transition costs (affects Module 29, 30, 32, 35)" — illustrated with `vm_cost_landcon`.

**Reality**: `vm_cost_landcon(j,land)` is declared in **39_landconversion** (`modules/39_landconversion/calib/declarations.gms:13`, the module's only realization) and referenced outside 39 in exactly **one** place: `modules/11_costs/default/equations.gms:20`. Modules 29, 30, 32 and 35 contain **zero** references to it (positive control: those same directories return hits for `vm_land`, so the search works there). Separately, this is not Module 10's transition cost — that is `vm_cost_land_transition(j)` (`modules/10_land/landmatrix_dec18/declarations.gms:22`, `q10_cost` at equations.gms:42-44), whose only consumer is likewise 11_costs.

**Verify**
```
rg -n '\bvm_cost_landcon\b' modules/   -> 11_costs/default/equations.gms:20 + 39_landconversion/calib/* only
rg -n '\bvm_cost_land_transition\b' modules/ -> 11_costs/default/equations.gms:39 + 10_land/* only
```

**Fix**: "Modifying land-conversion costs — `vm_cost_landcon` is declared in 39_landconversion and read only by 11_costs; modules 29/30/32/35 are affected *economically*, through the objective, not by any code reference. Module 10's own transition cost is `vm_cost_land_transition(j)` (`q10_cost`)."

---

### B8 — Major — `formula` (units) — §1.6 (doc L180)

**Doc claims**: `vm_cost_landcon.up(j,"primforest") = 1e6;  * USD/ha` — presented under **✅ SAFE**.

**Reality**: `vm_cost_landcon(j,land) Costs for land expansion and reduction (**mio. USD17MER per yr**)` — `modules/39_landconversion/calib/declarations.gms:13`. The annotation is off by the exact confusion this document calls "**most common error**" in §2.3 (L252-260), where it correctly writes "ALL costs in Module 11 must be `mio. USD17MER/yr`". A ✅ SAFE snippet contradicting the doc's own ❌ MISTAKE is the worst place for it.

**Verify**: `grep -n 'vm_cost_landcon' modules/39_landconversion/calib/declarations.gms` → as quoted.

**Fix**: drop the `* USD/ha` comment (or write `* mio. USD17MER per yr`).

---

### B9 — Major — `citation` — magpie4 functions that do not exist (doc L149, 433, 581, 637, 695, 715, 729-731)

Checked against the renv-pinned magpie4 clone under `.cache/sources/magpie4` (`NAMESPACE`).

| Doc call | Doc line(s) | Exists? | Actual export |
|---|---|---|---|
| `land_transitions(gdx)` | 149 | ❌ | `landTransitionMatrix` |
| `trade_balance(gdx)` | 433, 715 | ❌ | `trade` / `tradeValue` |
| `emissions(gdx, type=…)` | 581, 695 | ❌ | `Emissions` (capital E), `emisCO2` |
| `land_conservation(gdx)` | 637 | ❌ | `landConservation` |
| `nr_inputs` / `nr_outputs` / `nr_soil_change` | 729-731 | ❌ | `NitrogenBudget`, `NitrogenBudgetPasture`, `NitrogenBudgetNonagland` |
| `land`, `production`, `costs`, `carbonstock`, `water_usage`, `water_avail`, `demand` | various | ✅ | — |

Six of thirteen named functions in the "Minimum Test Suite" sections do not exist.

**Verify**
```
grep -cE '^export\((land_transitions|trade_balance|emissions|land_conservation|nr_inputs|nr_outputs|nr_soil_change)\)$' .cache/sources/magpie4/NAMESPACE   -> 0
grep -nE '^export\((landTransitionMatrix|landConservation|Emissions|NitrogenBudget)\)$' .cache/sources/magpie4/NAMESPACE  -> 4 hits
```

**Fix**: substitute the real exports; per AGENT.md, any magpie4 claim must cite `.cache/sources/magpie4/…` at the pinned version.

---

### B10 — Major — `set_membership` — §1.6 (doc L174), the first ✅ SAFE pattern

**Doc claims**
```gams
vm_lu_transitions.fx(j,"forest","crop")$(pm_land_conservation(j,"forest") > 0) = 0;
```

**Reality**: two domain errors in one line presented as a safe pattern to copy.
1. `"forest"` is **not** a member of `land` (and `land_from`/`land_to` alias `land`): `/ crop, past, forestry, primforest, secdforest, urban, other /` — `core/sets.gms:250-251`. The forested subsets are `land_forest / forestry, primforest, secdforest /` (`core/sets.gms:263-264`).
2. `pm_land_conservation` has **four** dimensions, not two: `pm_land_conservation(t,j,land,consv_type)` — `modules/22_land_conservation/area_based_apr22/declarations.gms:15` (cf. real usage `pm_land_conservation(t,j,"past",consv_type)` at `modules/31_past/endo_jun13/presolve.gms:9`).

As written this raises GAMS $170/$171 domain errors.

**Verify**
```
sed -n '249,266p' core/sets.gms                                        -> land set, no "forest"
grep -rn 'pm_land_conservation' --include='declarations.gms' modules/  -> (t,j,land,consv_type)
```

**Fix**: e.g. `vm_lu_transitions.fx(j,land_forest,"crop")$(sum(consv_type, pm_land_conservation(t,j,land_forest,consv_type)) > 0) = 0;`

---

### B11 — Minor — `set_membership` — phantom members inside the ❌ WRONG illustration blocks (doc L121, 370, 514, 529)

- L121 `vm_land.fx(j,"forest") = 50;` — `"forest"` ∉ `land` (`core/sets.gms:250-251`).
- L370 `vm_prod_reg(i,"beef")` / `vm_prod(j,"beef")` — `"beef"` ∉ `kall`; the livestock members are `livst_rum, livst_pig, livst_chick, livst_egg, livst_milk` (`core/sets.gms:228-236`).
- L514, L529 `im_pollutant_prices(t,i,"co2_c","all")` — `"all"` ∉ `emis_source`; members are `inorg_fert … peatland` (`core/sets.gms:302-313`). The whole-set idiom is `im_pollutant_prices(t_all,i,"co2_c",emis_source)` as used in `modules/56_ghg_policy/price_aug22/preloop.gms:67`.

Minor (not Major) because each sits in a block already labelled WRONG, so a reader is not being told the usage is valid — but the tokens still read as real MAgPIE identifiers.

**Verify**: `sed -n '228,236p;249,252p;300,313p' core/sets.gms` → none of `forest`, `beef`, `all` present.

**Fix**: use real members (`"primforest"`, `"livst_rum"`, `emis_source`) so the illustrations stay copy-safe.

---

### B12 — Major — `citation` — magpie4 `costs()` indexing and units (doc L287-301, L572-574)

**Doc claims**: `costs <- costs(gdx, level="regglo")`, then `costs["GLO",,"total"]`, `costs[,,"emission_costs"]`, `setdiff(getNames(costs), "total")`, with the range "500-2000 billion USD17/yr" — and the assertion immediately below uses `< 5000`.

**Reality** (`.cache/sources/magpie4/R/costs.R`):
- Signature `costs(gdx, file, level = "reg", type = "annuity", sum = TRUE)`; with the default `sum = TRUE` the function ends with `x <- dimSums(x, dim = 3)` (line 193-195), so the returned object has **no** third-dimension names at all. `costs[,,"total"]` and `getNames(costs)` do not resolve.
- With `sum = FALSE` the GHG component label is `"GHG Emissions"` (line 189), not `"emission_costs"`.
- Return unit is documented `@return A MAgPIE object containing the goal function costs including investments [**million US$17**]` (line 10) — so a global total is ~1e6, and the `> 500 & < 5000` bounds are off by 1e3 even setting the naming aside.
- Prose ("500-2000 billion") and code (`< 5000`) also disagree with each other.

**Verify**
```
sed -n '9,20p;188,196p' .cache/sources/magpie4/R/costs.R
  -> "[million US$17]" ; costs(gdx, file=NULL, level="reg", type="annuity", sum=TRUE) ; if (sum) x <- dimSums(x, dim=3)
grep -n '"GHG Emissions"' .cache/sources/magpie4/R/costs.R -> 189
```

**Fix**: `costs(gdx, level = "regglo", sum = FALSE)` for component work; index the GHG component as `"GHG Emissions"`; state thresholds in million US$17; reconcile 2000 vs 5000.

---

## 2. Deferred (not scored — unverified or judgment, no edit proposed)

- §2.2 "Typical Magnitude (USD17/yr)" column (L221-227): requires a solved GDX; not checkable from source.
- §5.1 cycle diagrams (L613, L629, L645): drawn with `←→` on every edge. At the interface level each edge I checked is one-directional — `14 → 17` (`pm_yields_semi_calib`, `modules/17_production/flexreg_apr16/presolve.gms:10`), `17 → 70` (`vm_prod_reg`), `70 → 14` (`pm_past_mngmnt_factor`, declared `modules/70_livestock/fbask_jan16/declarations.gms:41`, read `modules/14_yields/managementcalib_aug19/equations.gms:38`). The *triangle* is real and over exactly those three modules, so `←→` may just denote cycle membership; not flagged.
- §3.3's arrows into 18/20/21 (L355-356): M18 and M20 both read `vm_prod_reg(i,kcr)` **and** own other slices of it (`kres` via `q18_prod_res_reg`; `ksd`/`cottn_pro` via `q20_processing*`). Per-slice ownership nuance the diagram flattens; subsumed by B1's fix, not separately scored.
- §5.2.2 / §5.2.3 / §5.2.5 R snippets beyond function existence (argument names such as `source="all"`, `subcategories="all"`, `products="k"`): not individually validated against each magpie4 signature.
- §2.4 "Check all 30+ components sum to total": `q11_cost_reg` has 35 terms across 27 producer modules — consistent with "30+", so not flagged.
- §1.2 footnote's historical claim that `pcm_land` "was previously UNDERSTATED (5 → 12)": a claim about a past doc state; not checkable against code.

---

## 3. Method notes

- Every absence claim was cross-checked with a second method and a positive control (e.g. `vm_cost_landcon` absent from 29/30/32/35 was confirmed by first proving `vm_land` *is* found in those directories).
- `rg -n` used throughout (never `rg -r`, which is `--replace`); each probe run as its own standalone command so a no-match exit-1 could not truncate a chain.
- Role map consulted first for all 17 interface-variable attributions; it disagreed with my grep exactly once (`vm_land` ← 58_peatland) and the role map was correct — the macro-argument form defeats both `NAME(` and `NAME.`.
