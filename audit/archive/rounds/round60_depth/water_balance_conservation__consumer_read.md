# R60 depth audit — `cross_module/water_balance_conservation.md`

**Lens**: `consumer_read` (enter from the consumer side: presolve/postsolve/equation-RHS of every module the doc names as a reader; whole-tree greps of both `NAME(` and `NAME.` for each interface var; solution-level `.l`/`.lo`/`.m` reads)
**Ground truth**: MAgPIE `develop` worktree at `2c02843ec` (*Merge pull request #919 from alexkoberle/dyn_reg_tau*)
**Secondary ground truth**: `audit/integrated/depth_rolemap.json`; magpie4 SHA-pinned clone `.cache/sources/magpie4` (v2.76.4, SHA `43970cd`, per `project/version_pins.json`)
**GAMS 51.4.0 / CPLEX 22.1.2 available and used** for two reproducible sign derivations (see B3, B4).
**Claims verified**: 62 · **Bugs**: 11 (1 Critical, 6 Major, 2 Minor, 2 Informational)

---

## 0. Consumer/producer map re-derived from code (lens deliverable)

Whole-tree greps, both `NAME(` and `NAME.` forms, run as isolated commands:

| Interface object | DECLARED | POPULATED | READ | Doc agrees? |
|---|---|---|---|---|
| `vm_watdem(wat_dem,j)` | 42 (`.../all_sectors_aug13/declarations.gms:29`) | **42 only** — `q42_water_demand` LHS (`equations.gms:10-14`) for `agriculture`; `.fx` in `presolve.gms:41/45/48/51` for `watdem_ineldo`, `presolve.gms:87-88` for `ecosystem` | 42 (`equations.gms:17`), 43 (`equations.gms:11`; **solution-level** `vm_watdem.lo` in `presolve.gms:15-16`) | ✅ yes |
| `v43_watavail(wat_src,j)` | 43 (`declarations.gms:13`) | 43 (`presolve.gms:8-16`, all `.fx`) | 43 only | ✅ yes — and this confirms the doc's "Zero cost: no penalty for buffer groundwater" (doc:293): `v43_watavail` appears in **no** cost equation anywhere in the tree |
| `im_wat_avail(t,wat_src,j)` | 43 (`declarations.gms:9`) | 43 (`preloop.gms:8,10-12`) | 42 (`presolve.gms:58,64`), 43 (`presolve.gms:8-11`) | ✅ yes (doc:362) |
| `vm_water_cost(i)` | 42 (`declarations.gms:31`) | 42 (`equations.gms:16-17`) | **11** (`modules/11_costs/default/equations.gms:46`), 42 | ⚠️ module 11 never named in the doc (folded into B7) |
| `vm_AEI(j)` | 41 (`endo_apr13/declarations.gms:19`) | 41 (endogenous var; `q41_cost_AEI`, `presolve.gms:11` `.lo`) | 41 (`equations.gms:11,21`), 30 **only in the non-default `detail_apr24`** (`equations.gms:82`); the default `simple_apr24` lists `vm_AEI` in `not_used.txt:2` | ✅ substance OK (constraint lives in `q41_area_irrig`) |
| `vm_prod(j,k)` | 17 (`flexreg_apr16/declarations.gms:9`) | 30 (`kcr`), 31 (`past`), **71** (`kli_rum`,`kli_mon`), 73 (timber) | 17, 18, 31, 38, 40, **42**, 71, 73 | ❌ **B1** |

Role-map cross-check: `depth_rolemap.json` lists `vm_watdem` `populated_by: ["42","43"]`. My both-endpoints grep shows module 43 only **reads** `vm_watdem.lo` (`presolve.gms:15-16`) — the map is a superset that treats a `.lo` reference as a write. Code wins; noted, not a doc bug.

Also verified correct (no bug): `wat_dem` = 5 members and `wat_src` = 4 members (`core/sets.gms:244,247`); `watdem_exo` = domestic/manufacturing/electricity/ecosystem and `watdem_ineldo` = domestic/manufacturing/electricity (`modules/42_water_demand/all_sectors_aug13/sets.gms:9-13`); `land` = 7 pools (`core/sets.gms:250-251`); `EFP_countries` and `iso` both have exactly **249** members (doc:103 ✅); default cluster resolution `c200` (`config/default.cfg:26`) → doc:223 "~200 cells" ✅; realizations `all_sectors_aug13` / `total_water_aug13` / `endo_apr13` are the defaults (`config/default.cfg:1340,1427,1322`) ✅; every `file.gms:LINE` citation in the doc resolves to the claimed content in current `develop` ✅ (no citation drift found).

---

## B1 — 🔴 Critical — `vm_prod(j,kli)` attributed to Modules 17 and 70; the populator is Module 71 and Module 70 never touches `vm_prod`

- **doc_line**: `water_balance_conservation:430` (and `:910`, `:420`)
- **claim**: "`vm_prod(j,kli)`: Livestock production from **Module 17** (Mt DM/yr)"; summary table: "| **17, 70** | Livestock production (contributes to agricultural demand) | `vm_prod(j,kli)` |"; §6.5 heading "Module 17 (Production) and **Module 70 (Livestock)** — Role: Calculate production including livestock water demand".
- **reality**:
  - Module **17** (`flexreg_apr16`, default) **DECLARES** `vm_prod(j,k)` and **READS** it — `q17_prod_reg .. vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k));`. Its only write is a first-timestep starting *level* for **crops only**, `vm_prod.l(j,kcr)` (`presolve.gms:15`, gated on `c17_prod_init`). It never populates the `kli` slice.
  - Module **70** (`fbask_jan16`, default) contains **zero** references to `vm_prod` — it works exclusively on the regional `vm_prod_reg`. Phantom producer.
  - The cellular livestock slice is constrained by module **71** (`disagg_lvst`, default `foragebased_jul23`): `q71_feed_forage` reads `vm_prod(j2,kli_rum)` (`equations.gms:21-24`) and `q71_prod_mon_liv .. vm_prod(j2,kli_mon) =l= ...` (`equations.gms:55-59`).
- **file_evidence**: `modules/17_production/flexreg_apr16/equations.gms:10-11`; `modules/17_production/flexreg_apr16/presolve.gms:15`; `modules/70_livestock/fbask_jan16/equations.gms:18,28,36,60,65,70` (all `vm_prod_reg`); `modules/71_disagg_lvst/foragebased_jul23/equations.gms:21-24,55-59`
- **verify_cmd**: `rg -n "vm_prod" modules/70_livestock/fbask_jan16/equations.gms modules/70_livestock/module.gms` → 7 hits, **all `vm_prod_reg`**, none `vm_prod(`. `rg -ln "vm_prod" modules/` → 45 files; module 70 appears only via `vm_prod_reg`. Role map: `vm_prod.populated_by = ["30","31","71","73"]` — 17 and 70 absent.
- **confirmed**: true
- **severity rationale**: R20 anchor — a wrong producer/consumer set is Critical by harm to a future reader. A user tracing where cellular livestock production is determined would open modules 17 and 70, find only an aggregation identity and `vm_prod_reg` respectively, and miss module 71 entirely.
- **proposed_fix**: retitle §6.5 to "Module 71 (Livestock disaggregation) and Module 17 (Production)"; change doc:430 to "`vm_prod(j,kli)`: cellular livestock production — **declared** in Module 17 (`modules/17_production/flexreg_apr16/declarations.gms:9`), **populated/constrained** by Module 71 (`modules/71_disagg_lvst/foragebased_jul23/equations.gms:21-24,55-59`), **read** by Module 42's `q42_water_demand`. Module 17 only aggregates it to `vm_prod_reg` (`equations.gms:10-11`); Module 70 operates on `vm_prod_reg`, never on `vm_prod`." Change the doc:910 table row to "| 71 (+17 aggregation) | Cellular livestock production | `vm_prod(j,kli)` |".

---

## B2 — 🟠 Major — EFP policy ramp-up described as operative; `c42_env_flow_policy` defaults to `off` and the doc never says so

- **doc_line**: `water_balance_conservation:552` (also `:102`, `:534`, `:542`)
- **claim**: doc:102 "Linear ramp-up from 2025 (0%) to 2040 (100%)"; doc:534 "EFP policy ramps up 2025-2040 (linear increase from 0% to 100%)"; doc:542 "2040: Ecosystem demand = 20% (full EFP enforcement)"; doc:552-556 lists `off` / `on` / `mixed` with **no DEFAULT marker** — in a doc that marks "- DEFAULT" for SSP2 (doc:78), env-flow scenario 2 (doc:99) and `cc` (doc:139).
- **reality**: `$setglobal c42_env_flow_policy off` and `cfg$gms$c42_env_flow_policy <- "off"  # def = "off"`. With `off`, `i42_env_flow_policy(t,i) = p42_efp(t,"off") * shr + p42_efp(t,"off") * (1-shr)` and `p42_efp(t_all,"off") = 0`, so `ic42_env_flow_policy(i) = 0` and `vm_watdem.fx("ecosystem",j)` collapses to `i42_env_flows_base(t,j)` = **5 %** of available water (`s42_env_flow_base_fraction = 0.05`) for **every year**. In a default run the ecosystem sector never ramps and never reaches the Smakhtin/20 % level.
- **file_evidence**: `modules/42_water_demand/all_sectors_aug13/input.gms:122`; `config/default.cfg:1373`; `modules/42_water_demand/all_sectors_aug13/preloop.gms:15-17`; `modules/42_water_demand/all_sectors_aug13/presolve.gms:58,81-88`
- **verify_cmd**: `grep -n "c42_env_flow_policy" config/default.cfg` → `1373:cfg$gms$c42_env_flow_policy <- "off"             # def = "off"`; `grep -n "p42_efp(t_all" modules/42_water_demand/all_sectors_aug13/preloop.gms` → `15:p42_efp(t_all,"off") = 0;`
- **confirmed**: true
- **severity rationale**: the rubric's Critical trigger "Active mechanism claimed when actually OFF by default" fires on doc:534, but §7.4 sits under "§7 Conservation Law in Practice" alongside "§7.3 Climate Change **Scenario**", so it partly reads as a scenario walk-through. Tie-breaker (§1) → pick the lower tier. Recorded as Major with `tier_uncertainty`.
- **proposed_fix**: at doc:552 mark "`off`: No EFP (base protection only, 5 %) — **DEFAULT** (`config/default.cfg:1373`)". At doc:101-105 insert a leading bullet: "**Default: `c42_env_flow_policy = off`** — ecosystem demand stays at `s42_env_flow_base_fraction` (5 % of available water) in every year; the ramp-up below only occurs if the switch is set to `on` or `mixed`." Open §7.4 with "This section describes a **non-default** scenario (`c42_env_flow_policy = on`)."

---

## B3 — 🟠 Major — `oq43_water` marginal sign inverted; the shipped diagnostic silently returns an empty set

- **doc_line**: `water_balance_conservation:212` (and the R snippet at `:675`)
- **claim**: doc:212 "**Shadow price only when binding**: `oq43_water.marginal` **> 0** only if constraint tight"; doc:675 `high_value_water <- which(shadow_price > 0.01)  # >$0.01/m³`.
- **reality**: `q43_water` is `=l=` in a **cost-minimising** LP, so GAMS reports its marginal as **≤ 0** (negative when binding, `.`/0 when slack). magpie4 corroborates: `water_price()` reads `oq43_water[,,"marginal"]` and immediately applies `abs()`. Consequently `which(shadow_price > 0.01)` on the raw GDX values selects **nothing**, and the doc's diagnostic would report "0 water-scarce cells" in every run — a silent false negative.
- **file_evidence**: `modules/43_water_availability/total_water_aug13/equations.gms:10-11` (the `=l=`), `.../postsolve.gms:11` (`oq43_water(t,j,"marginal") = q43_water.m(j);`); magpie4 `.cache/sources/magpie4/R/water_price.R:27-33` (`p_water_cell <- abs(p_water_cell)`)
- **verify_cmd**: minimal reproducible GAMS 51.4.0 model, `q .. sum(s,d(s)) =l= sum(s,av(s));` minimising `z =e= -sum(s,d(s))`, `av` fixed at 10 → listing reports `---- EQU q   LOWER -INF   LEVEL .   UPPER .   MARGINAL **-1.0000**`. Slack variant (`z =e= +sum(s,d(s))`, demand forced to 3) → `MARGINAL .` (zero).
- **confirmed**: true
- **proposed_fix**: doc:212 → "**Shadow price only when binding**: `oq43_water(t,j,\"marginal\")` is **≤ 0** — negative when the constraint is tight, 0 when slack (GAMS convention for `=l=` under minimisation). magpie4's `water_price()` applies `abs()` before reporting (`.cache/sources/magpie4/R/water_price.R:33`)." doc:675 → `high_value_water <- which(abs(shadow_price) > 0.01)`, or better `water_price(gdx, level = "cell")`.

---

## B4 — 🟠 Major — `oq43_water` level described as a non-negative surplus; it is `withdrawals − available` and is ≤ 0

- **doc_line**: `water_balance_conservation:211`
- **claim**: "**Surplus variable**: `oq43_water.level` = available - withdrawals (≥ 0)"
- **reality**: three separate errors. (a) `oq43_water` is a **parameter** `oq43_water(t,j,type)`, not a variable — the handle is `oq43_water(t,j,"level")`, `.level` is not valid syntax on it. (b) `q43_water.l` is the *row activity* of the normalised row `Σ vm_watdem − Σ v43_watavail ≤ 0`, i.e. **withdrawals − available**, which is **≤ 0**, the negative of the surplus. (c) The doc's own §8.2 computes surplus the other way (`total_avail - total_demand`), so the two sections contradict each other.
- **file_evidence**: `modules/43_water_availability/total_water_aug13/declarations.gms:22-23` (parameter `oq43_water(t,j,type)`), `.../postsolve.gms:13` (`oq43_water(t,j,"level") = q43_water.l(j);`), `.../equations.gms:10-11`
- **verify_cmd**: same GAMS 51.4.0 harness, non-binding case (demand = 3, availability = 10): listing reports `---- EQU q   LOWER -INF   LEVEL **-7.0000**   UPPER .   MARGINAL .` — i.e. `3 − 10`, not `10 − 3`.
- **confirmed**: true
- **proposed_fix**: doc:211 → "**Slack**: `oq43_water(t,j,\"level\")` = withdrawals − available, and is **≤ 0**. Its magnitude is the unused water; it is a postsolve **parameter** (`declarations.gms:22-23`), not a variable. Surplus = `-oq43_water(t,j,\"level\")`."

---

## B5 — 🟠 Major — `water_demand()` is not a magpie4 function

- **doc_line**: `water_balance_conservation:607` (repeated at `:842`; the returned object is then used at `:773`, `:783-784`)
- **claim**: `watdem <- water_demand(gdx, level="cell", water_source=FALSE)`
- **reality**: magpie4 v2.76.4 exports **no** `water_demand`. The water-withdrawal reader is **`water_usage()`**, signature `water_usage(gdx, file = NULL, level = "reg", users = NULL, sum = FALSE, seasonality = "total", abstractiontype = "withdrawal", digits = 4)` — there is no `water_source` argument anywhere in it. Both §8.1 (constraint-satisfaction check) and §10.3 (post-modification testing protocol) fail at the first line with `could not find function "water_demand"`.
- **file_evidence**: magpie4 `.cache/sources/magpie4/R/water_usage.R:30`; `.cache/sources/magpie4/NAMESPACE:309` (`export(water_usage)`) — no `export(water_demand)` at any line
- **verify_cmd**: `rg -n "water_demand" .cache/sources/magpie4/ || echo "NO MATCH"` → `NO MATCH for water_demand` (isolated command). Second method `grep -rn "water_demand" .cache/sources/magpie4/` → empty, exit 0. Positive control `grep -rn "water_usage" .cache/sources/magpie4/R/water_usage.R` → 3 hits, proving the search reaches that tree.
- **confirmed**: true
- **proposed_fix**: replace both occurrences with `watdem <- water_usage(gdx, level = "cell", users = "sectors", seasonality = "grper")`, and drop the `water_source=FALSE` argument. Note `seasonality = "grper"` is what matches the GAMS growing-period constraint (the magpie4 default is `"total"`).

---

## B6 — 🟠 Major — "No feedback from Module 43 water constraint to Module 41 investment" is false under the default realization

- **doc_line**: `water_balance_conservation:414` (context `:411-416`)
- **claim**: "**Known Limitation** (Module 41): … **No feedback from Module 43 water constraint to Module 41 investment**" → "Result: **Stranded AEI assets**", "Model may overestimate irrigation expansion in water-stressed regions".
- **reality**: the default realization is `endo_apr13`, in which `vm_AEI(j)` is an **endogenous positive variable** solved in the *same* simultaneous LP as `q43_water`. The chain `q43_water` → `vm_watdem("agriculture",j)` → `q42_water_demand` → `vm_area(j,kcr,"irrigated")` → `q41_area_irrig` → `vm_AEI(j)` is all one solve, and `q41_cost_AEI` charges an annuity for every hectare of expansion. Water scarcity in a cell therefore *does* suppress AEI investment within the time step — the LP will not buy capacity it cannot use. The genuine limitations are different: (a) MAgPIE is recursive-dynamic/myopic, so the current solve cannot anticipate **future** runoff decline (this the doc states correctly at doc:412); (b) `s41_AEI_depreciation = 0` by default, so `vm_AEI.lo(j) = pc41_AEI_start(j)/(1-0)^len = pc41_AEI_start(j)` — AEI can never shrink, which is what actually strands *past* investment when water availability falls.
- **file_evidence**: `config/default.cfg:1322` (`area_equipped_for_irrigation <- "endo_apr13"`); `modules/41_area_equipped_for_irrigation/endo_apr13/declarations.gms:19` (`positive variables vm_AEI(j)`); `.../endo_apr13/equations.gms:10-11` (`q41_area_irrig .. sum(kcr, vm_area(j2,kcr,"irrigated")) =l= vm_AEI(j2);`) and `:19-23` (`q41_cost_AEI`); `.../endo_apr13/input.gms:11` (`s41_AEI_depreciation … / 0 /`); `.../endo_apr13/presolve.gms:11`
- **verify_cmd**: `rg -n "vm_AEI" modules/` → `endo_apr13/declarations.gms:19` declares it a positive **variable** (not `.fx`'d anywhere in `endo_apr13`; only the `static` realization does `vm_AEI.fx(j) = …` at `static/presolve.gms:9`). `grep -n "s41_AEI_depreciation" modules/41_area_equipped_for_irrigation/endo_apr13/input.gms` → `11: … / 0 /`.
- **confirmed**: true
- **proposed_fix**: replace doc:414 with "- Within a time step there **is** feedback: `vm_AEI` is endogenous in the same LP as `q43_water` (`endo_apr13/declarations.gms:19`, `equations.gms:10-11`), so a binding water constraint suppresses expansion directly. The real limitations are (i) recursive-dynamic myopia — no anticipation of **future** runoff decline — and (ii) `s41_AEI_depreciation = 0` by default (`endo_apr13/input.gms:11`), so `vm_AEI.lo` never falls below the previous step's AEI (`presolve.gms:11`) and past investment cannot be written off." Also note the `static` realization exists, where AEI is exogenous and the doc's "no feedback" statement *would* hold.

---

## B7 — 🟠 Major — pumping costs presented as a live cost channel; `s42_pumping = 0` makes `vm_water_cost` identically zero by default

- **doc_line**: `water_balance_conservation:830` (also `:333-336`, `:435`)
- **claim**: doc:333-336 lists `q42_water_cost` under Module 42's "Key Equations" with no default caveat; doc:435 "Water scarcity → higher **water cost** → affects livestock production costs"; doc:829-832 "✓ SAFE: Pumping costs — Module 42, `s42_pumping` and `s42_multiplier` — Affects agricultural production costs".
- **reality**: `ic42_pumping_cost(i) = 0;` is executed unconditionally each presolve, and is only overwritten inside `if ((s42_pumping = 1), …)`. Default `s42_pumping = 0` → `ic42_pumping_cost(i) = 0` → `vm_water_cost(i) = 0` for all regions and all years. There is **no monetary cost of water in a default run**; the only economic signal is the `q43_water` shadow price. (Even with `s42_pumping = 1`, `s42_multiplier = 0` zeroes the cost again after `s42_multiplier_startyear = 1995`.) The feature is documented as India-only.
- **file_evidence**: `modules/42_water_demand/all_sectors_aug13/presolve.gms:26` (`ic42_pumping_cost(i) = 0;`) and `:29-35`; `config/default.cfg:1415` (`s42_pumping <- 0`) and `:1423` (`s42_multiplier <- 0`); consumer: `modules/11_costs/default/equations.gms:46` (`+ vm_water_cost(i2)`)
- **verify_cmd**: `grep -n "s42_pumping\|s42_multiplier" config/default.cfg` → `1415:cfg$gms$s42_pumping <- 0      # def = 0`, `1423:cfg$gms$s42_multiplier <- 0      # def = 0`; `sed -n '25,35p' modules/42_water_demand/all_sectors_aug13/presolve.gms` → line 26 sets `ic42_pumping_cost(i) = 0` before the `s42_pumping = 1` guard.
- **confirmed**: true
- **proposed_fix**: at doc:333 add "⚠️ **Inactive by default**: `s42_pumping = 0` (`config/default.cfg:1415`) → `ic42_pumping_cost(i) = 0` (`presolve.gms:26`) → `vm_water_cost(i) = 0`. In a default run water carries no monetary cost; the only scarcity signal is the `q43_water` marginal. Pumping costs are currently parameterised for India only." At doc:435 replace "higher water cost" with "a higher `q43_water` shadow price". Add module 11 to the §11.3 role table — `vm_water_cost` is consumed by `q11_cost_reg` (`modules/11_costs/default/equations.gms:46`), the only route by which water enters the objective.

---

## B8 — 🟡 Minor — `water_avail()` returns km³ and is already source-summed; the doc's `mio. m³` thresholds are 1000× off and one `dimSums` is a no-op

- **doc_line**: `water_balance_conservation:611` (also `:612`, `:618`, `:621-622`, `:650`, `:654`, `:756`, `:843`)
- **claim**: `watavail <- water_avail(gdx, level="cell")` then `total_avail <- dimSums(watavail, dim=3.1)  # Sum over sources`, then `stopifnot(max_violation < 0.01)` with the comment "< 0.01 **mio. m³** = numerical tolerance"; scarcity cut-offs "< 1 mio. m³", "> 100 mio. m³", "< 0.1 mio. m³".
- **reality**: `water_avail()` defaults to `sum = TRUE`, so it **already** sums over `wat_src` before returning — the doc's `dimSums(..., dim = 3.1)` is a no-op on the returned object. And the last operation is `x <- x / 1000  # from mio m^3 to km^3`; `water_usage()` does the same (`outout / 1000`). Every threshold expressed in "mio. m³" is therefore 1000× too large against a km³-valued object.
- **file_evidence**: magpie4 `.cache/sources/magpie4/R/water_avail.R:20-22` (defaults), `:31-35` (`if (sum) x <- dimSums(x, dim = 3.1)`), `:46-47` (`x <- x / 1000`); `.cache/sources/magpie4/R/water_usage.R:245-246`
- **verify_cmd**: `grep -n "0.001\|/ 1000\|km\^3" .cache/sources/magpie4/R/water_usage.R .cache/sources/magpie4/R/water_avail.R` → `water_avail.R:14 #' @return … (km^3)`, `:46 # from mio m^3 to km^3`, `:47 x <- x / 1000`; `water_usage.R:22 … (km^3/yr)`, `:245-246`
- **confirmed**: true
- **proposed_fix**: use `water_avail(gdx, level = "cell", sum = FALSE)` if the per-source breakdown is wanted (then `dimSums(dim = 3.1)` is meaningful), or drop the redundant `dimSums`. Relabel all thresholds as km³ and rescale: `< 1e-5` km³ instead of `< 0.01 mio. m³`, `< 1e-3` km³ instead of "< 1 mio. m³", `> 0.1` km³ instead of "> 100 mio. m³". State once, near doc:602, that GAMS carries `mio. m³` while magpie4 returns `km³` (1 km³ = 1000 mio. m³).

---

## B9 — 🟡 Minor — agriculture is not strictly confined to surface water in buffered cells

- **doc_line**: `water_balance_conservation:285` (also `:300`, `:580`)
- **claim**: "**NOT agriculture**: Agricultural demand must stay within renewable water"; table row "| Agriculture | Endogenous | Must stay within renewable water (surface) |"; "Agricultural water demand must still fit within renewable water (**surface only**)".
- **reality**: `q43_water` is a single **pooled** inequality over all `wat_dem` and all `wat_src` — the buffer is *sized* from `watdem_exo` but is not earmarked to it. Algebra from `presolve.gms:14-16` (at evaluation time `v43_watavail.up("ground") = 0`, so `Σ_src .up = S`): buffer `G = 1.01·(E − S)` when `E > S`. Total availability `= S + 1.01(E − S) = E + 0.01(E − S)`. Since the exogenous sectors are `.fx`'d at `E`, `q43_water` leaves agriculture `A ≤ 0.01·(E − S)` — a small but strictly positive allowance drawn from the `ground` pool, not from surface water.
- **file_evidence**: `modules/43_water_availability/total_water_aug13/equations.gms:10-11`; `.../presolve.gms:8-16`
- **verify_cmd**: `cat -n modules/43_water_availability/total_water_aug13/presolve.gms` → lines 8-11 fix all four sources from `im_wat_avail` (ground/ren_ground/technical = 0 per `preloop.gms:10-12`), line 14-16 then adds `1.01·(Σ_exo vm_watdem.lo − Σ_src v43_watavail.up)` to `ground`. Substituting `Σ_src .up = S` gives the 1 % residual analytically.
- **confirmed**: true
- **proposed_fix**: doc:285 → "**Sizing excludes agriculture**: the shortfall is computed over `watdem_exo` only. Note the buffer is added to the shared `ground` pool, not earmarked — the 1.01 factor leaves agriculture a residual `≤ 0.01·(exogenous − surface)` in buffered cells, so agriculture is *approximately*, not strictly, confined to surface water there." Adjust doc:300 and doc:580 to match.

---

## B10 — 🟢 Informational — "shadow prices in objective function"

- **doc_line**: `water_balance_conservation:392`
- **claim**: "Module 30 responds indirectly via shadow prices **in objective function**"
- **reality**: the `q43_water` marginal is a **dual**; it never appears in `vm_cost_glo`/`q11_cost_glo`. Its influence on `vm_area(j,kcr,"irrigated")` runs through the *reduced cost* of that column via `q42_water_demand` and `q43_water`, inside a single simultaneous LP. (The doc's preceding bullet, "Module 43 constraint applies to Module 42", is fine.)
- **file_evidence**: `modules/11_costs/default/equations.gms` (objective terms; no water-marginal term); `modules/42_water_demand/all_sectors_aug13/equations.gms:10-14`
- **verify_cmd**: `rg -n "vm_water_cost" modules/` → the only water term in the objective is `modules/11_costs/default/equations.gms:46`, which is `vm_water_cost` (zero by default per B7), not a shadow price.
- **confirmed**: true
- **proposed_fix**: "Module 30 responds through the **reduced cost** of `vm_area(j,kcr,\"irrigated\")`: the `q43_water` dual propagates via `q42_water_demand`. All of this happens inside one simultaneous LP — no shadow price is ever written into the objective function."

---

## B11 — 🟢 Informational — AEI-stranding diagnostic omits the `sum(kcr, …)`

- **doc_line**: `water_balance_conservation:743`
- **claim**: `vm_AEI(j) high but vm_area(j,kcr,"irrigated") << vm_AEI(j)`
- **reality**: `q41_area_irrig` compares `vm_AEI(j)` with the **sum over all crops**: `sum(kcr, vm_area(j2,kcr,"irrigated")) =l= vm_AEI(j2)`. As written the diagnostic compares a crop-indexed quantity to a scalar and will look "stranded" whenever more than one crop is irrigated.
- **file_evidence**: `modules/41_area_equipped_for_irrigation/endo_apr13/equations.gms:10-11`
- **verify_cmd**: `rg -n "vm_AEI" modules/41_area_equipped_for_irrigation/endo_apr13/equations.gms` → `11:  sum(kcr, vm_area(j2,kcr,"irrigated")) =l= vm_AEI(j2);`
- **confirmed**: true
- **proposed_fix**: `vm_AEI(j) high but sum(kcr, vm_area(j,kcr,"irrigated")) << vm_AEI(j)`.

---

## Deferred (not flagged — unverifiable or judgment)

1. doc:55 / doc:346 "~64-90 %" irrigation-efficiency range. The formula `1/(1+e^((-22160 − im_gdp_pc_mer("y1995",i))/37767))` (`modules/42_water_demand/all_sectors_aug13/presolve.gms:18`) gives 64.3 % at GDPpc = 0 and ~90 % at ~60 000 USD17; the realised upper end depends on regional 1995 GDP-MER per capita, which lives in binary input I cannot read. The doc's mechanism claim ("GDP-based sigmoidal at `s42_irrig_eff_scenario = 2`, flat 0.66 only at `= 1`") **is** correct against code and against `config/default.cfg:1360-1367` — note `modules/42_water_demand/all_sectors_aug13/input.gms:16` calls scenario 2 "regional static values from CS", which is the stale label; the doc follows the code, correctly. Worth adding that scenario 2 uses **fixed 1995** GDP (time-invariant) while scenario 3 uses `im_gdp_pc_mer(t,i)`.
2. doc:279 "Factor 1.01 = 1 % safety margin for numerical stability" — plausible reading of `presolve.gms:15`, but the code carries no comment stating the intent. Interpretive.
3. doc:342 "Receives from Module 43: Shadow prices from `q43_water` … feed back to irrigation decisions" — LP-duality description, no code data flow to check. Not wrong, not verifiable as a data-flow claim.
4. doc:133-136 growing-period runoff fractions and doc:702-705 annualisation multipliers — explicitly labelled illustrative; the underlying split is computed in MAgPIE **preprocessing** (`realization.gms:9-10` says so), outside this tree.
5. doc:491 "$50-500 per m³" shadow-price magnitude and doc:683-686 typical ranges — labelled illustrative; would need a GDX to check.
6. doc:963-965 external references (Bondeau 2007, Biemans 2011, Smakhtin 2004) — Bondeau and Biemans are cited in `realization.gms:16,35`; Smakhtin appears in `modules/42_water_demand/all_sectors_aug13/input.gms:31`. Attributions are consistent; bibliographic accuracy not checked (no answer-time web access).
7. doc:5 "Modules Covered: 42, 43" understates the doc's scope (it also makes load-bearing claims about 17, 30, 41, 70/71 and, after B7, 11). Metadata, not a content error.

---

## Method notes

- Every grep probe was run as its **own** standalone command; absence claims (B5) were confirmed with two independent tools plus a positive control in the same tree.
- Both `NAME(` and `NAME.` forms were searched for every interface object, which is what surfaced module 43's solution-level `vm_watdem.lo` read (`presolve.gms:15-16`) — invisible to a `vm_watdem(` grep — and module 41's `vm_AEI.lo`/`.fx` writes.
- B3 and B4 rest on a **reproducible GAMS run**, not on recalled GAMS semantics: a 10-line LP with the same `=l=` shape, both binding and slack, whose listing pins the level and marginal signs.
- Data-flow direction was checked at **both endpoints** for every hand-off claim in §6. Modules 42 and 43 are genuinely serial in both directions (43 reads `vm_watdem` populated by 42; 42 reads `im_wat_avail` populated by 43) — the doc's §6.1/§6.2 "Provides/Receives" pairs are correct. No parallel-mistaken-for-serial defect found.
