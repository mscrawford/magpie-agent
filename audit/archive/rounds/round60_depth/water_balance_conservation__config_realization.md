# R60 depth audit — `cross_module/water_balance_conservation.md`

**Lens**: `config_realization` (entry point: `config/default.cfg` + realization directories)
**Ground truth**: MAgPIE `develop` worktree (read-only checkout)
**Auditor**: adversarial depth-first, whole-tree greps with positive controls
**Date**: 2026-08-02

---

## Scope and method

Entered from `config/default.cfg` and `ls modules/NN_*/`, then walked every default-value,
switch, realization-name and realization-selection claim in the doc, plus the
DECLARED/POPULATED/READ attribution claims in §6 and §11.3. Attribution claims were checked
against `audit/integrated/depth_rolemap.json` first and then re-confirmed with both-endpoints
greps (`NAME(` **and** `NAME.`). Absence claims were confirmed with two independent tools
(`rg` and `grep`) plus a positive control in the same directory.

**Claims verified: 58.** All 22 file:line citations in the doc were re-checked against current
`develop` — **all 22 resolve to the claimed content** (no citation drift found; this is a
genuinely well-cited doc on that axis).

Realization ground truth established:

| Module | Realizations on disk | `default.cfg` default | Doc covers |
|---|---|---|---|
| 41 | `endo_apr13`, `static` | `endo_apr13` (`config/default.cfg:1323`) | `endo_apr13` ✅ |
| 42 | `agr_sector_aug13`, `all_sectors_aug13` | `all_sectors_aug13` (`config/default.cfg:1340`) | `all_sectors_aug13` ✅ |
| 43 | `total_water_aug13` (only) | `total_water_aug13` (`config/default.cfg:1427`) | `total_water_aug13` ✅ |

The doc leads with the default realization everywhere — the Critical-prone "non-default
described as active" failure mode is **not** present. The defects below are default-**value**
(switch) defects, one attribution defect, and R-API defects.

---

## Bugs

### B1 — 🔴 Critical — `default_value` — EFP is OFF by default; default ecosystem demand is a flat 5%, not cell-specific Smakhtin

**Doc** (`water_balance_conservation.md:96-105`):

> **Three Scenarios** (Module 42, `modules/42_water_demand/all_sectors_aug13/input.gms:22`):
> - **Scenario 0**: No environmental flows
> - **Scenario 1**: Fixed fraction (20% of available water, uniform)
> - **Scenario 2**: LPJmL Smakhtin algorithm (cell-specific) - DEFAULT
>
> **Environmental Flow Protection (EFP) Policy** (Module 42, `.../input.gms:35-36`):
> - Linear ramp-up from 2025 (0%) to 2040 (100%)
> - Country-specific targeting (default: all ISO countries/territories -- the full 249-member iso set)

**Reality.** `s42_env_flow_scenario = 2` is indeed the default — but the Smakhtin values it
selects are multiplied by `ic42_env_flow_policy`, which is **identically zero** in a default
run, because the *policy* switch `c42_env_flow_policy` defaults to `off`. Full chain
(all in `develop`):

1. `modules/42_water_demand/all_sectors_aug13/input.gms:122` — `$setglobal c42_env_flow_policy  off`
   (and `config/default.cfg:1373` — `cfg$gms$c42_env_flow_policy <- "off"   # def = "off"`)
2. `modules/42_water_demand/all_sectors_aug13/preloop.gms:15` — `p42_efp(t_all,"off") = 0;`
3. `.../presolve.gms:81-82` — `i42_env_flow_policy(t,i) = p42_efp(t,"off")*shr + p42_efp(t,"off")*(1-shr)` → **0**
4. `.../presolve.gms:85` — `ic42_env_flow_policy(i) = i42_env_flow_policy(t,i);` → **0**
5. `.../presolve.gms:87-88` — `vm_watdem.fx("ecosystem",j) = ... i42_env_flows_base(t,j)*(1-0) + i42_env_flows(t,j)*0`

So in a default run: **ecosystem water demand = `i42_env_flows_base` = `s42_env_flow_base_fraction`
(0.05) × total available water** (`.../presolve.gms:58`, `input.gms:37`) — a spatially uniform 5%
fraction, constant in time. The cell-specific Smakhtin values (`f42_env_flows`, loaded at
`input.gms:110-117`, assigned at `preloop.gms:9`) are computed and then multiplied by zero.
The 2025→2040 fader (`preloop.gms:16-17`) only ever populates `p42_efp(t,"on")`, which the
default configuration never reads.

The two adjacent claims — "Scenario 2 … DEFAULT" and "(default: all ISO countries)" — are
individually true but jointly imply that a stock MAgPIE run applies ramping, cell-specific
environmental flow requirements. It does not. This is the rubric's Critical trigger *"active
mechanism claimed when actually OFF by default"* (§1, and the `s42_pumping` anchor).

**Same root cause, two more locations:**
- `:552-556` — "**Policy Modes** (Module 42, `.../input.gms:122`): `off` / `on` / `mixed`" cites the
  *exact line that sets the default* yet does not say which mode is default.
- `:824-827` — "✓ SAFE: Environmental flow policy — Module 42, `c42_env_flow_policy` …" — no default stated.

**verify_cmd**
```
sed -n '122p' modules/42_water_demand/all_sectors_aug13/input.gms
  → $setglobal c42_env_flow_policy  off
sed -n '1373p' config/default.cfg
  → cfg$gms$c42_env_flow_policy <- "off"             # def = "off"
sed -n '15p' modules/42_water_demand/all_sectors_aug13/preloop.gms
  → p42_efp(t_all,"off") = 0;
sed -n '58p;80,88p' modules/42_water_demand/all_sectors_aug13/presolve.gms
  → i42_env_flows_base(t,j) = s42_env_flow_base_fraction * sum(wat_src, im_wat_avail(t,wat_src,j));
    ...
    vm_watdem.fx("ecosystem",j) = sum(cell(i,j), i42_env_flows_base(t,j) * (1 - ic42_env_flow_policy(i)) +
                                                 i42_env_flows(t,j) * ic42_env_flow_policy(i));
```

**Proposed fix.** In §2.3, before the scenario list, insert the default-state paragraph:

> **Default behaviour**: `c42_env_flow_policy = "off"` (`modules/42_water_demand/all_sectors_aug13/input.gms:122`;
> `config/default.cfg:1373`). With the policy off, `ic42_env_flow_policy(i) = 0`
> (`preloop.gms:15` → `presolve.gms:81-85`), so ecosystem demand collapses to the **base**
> protection `i42_env_flows_base = s42_env_flow_base_fraction (0.05) × available water`
> (`presolve.gms:58`) — a uniform 5% in every cell, constant over time. The cell-specific
> Smakhtin values selected by `s42_env_flow_scenario = 2` and the 2025→2040 fader only take
> effect when `c42_env_flow_policy` is set to `"on"` or `"mixed"`.

Then re-label the §2.3 EFP bullets as "when the policy is enabled", add "— DEFAULT" to the `off`
entry in the §7.4 Policy-Modes list, and add "(default `off`)" to the §10.2 EFP bullet.

---

### B2 — 🟠 Major — `attribution_populate` — `vm_prod(j,kli)` attributed to Module 70, which never references it

**Doc** (`water_balance_conservation.md:910`, §11.3 Module Roles table):

> | 17, 70 | Livestock production (contributes to agricultural demand) | vm_prod(j,kli) |

and (`:430`):

> - `vm_prod(j,kli)`: Livestock production from Module 17 (Mt DM/yr)

plus the §6.5 heading (`:420`): "Module 17 (Production) and Module 70 (Livestock)".

**Reality.** Role map + both-endpoints greps agree:
- **DECLARED**: `modules/17_production/flexreg_apr16/declarations.gms:9` — `vm_prod(j,k) … (mio. tDM per yr)`.
  Module 17 also *reads* it, aggregating to `vm_prod_reg` (`.../equations.gms:11`), and seeds
  `vm_prod.l(j,kcr)` in `presolve.gms:15`. It does **not** determine the cellular livestock split.
- **POPULATED** (for `kli`): `71_disagg_lvst` — `foragebased_jul23/equations.gms:56`
  (`vm_prod(j2,kli_mon) =l= …`) and `:23,:37` for `kli_rum`; `foragebased_aug18/equations.gms:38,45`.
  Default realization is `foragebased_jul23` (`config/default.cfg:2221`).
- **Module 70 has ZERO references to `vm_prod`** — it works exclusively on the regional
  `vm_prod_reg`. Confirmed with two tools plus a positive control.

**verify_cmd**
```
rg -n "vm_prod\(" modules/70_livestock/            → (no output) EXIT=1
grep -rn "vm_prod(" modules/70_livestock/          → (no output) EXIT=1
grep -rn "vm_prod\." modules/70_livestock/         → (no output) EXIT=1   [attribute form checked too]
grep -rln "vm_prod_reg" modules/70_livestock/      → module.gms, fbask_jan16/equations.gms,
                                                     fbask_jan16_sticky/equations.gms   [positive control passes]
grep -rn "vm_prod(j2,kli" modules/                 → 71_disagg_lvst/foragebased_jul23/equations.gms:23,37,56
                                                     71_disagg_lvst/foragebased_aug18/equations.gms:38,45
                                                     42_water_demand/*/equations.gms:14 (read)
grep -n "cfg\$gms\$disagg_lvst" config/default.cfg → cfg$gms$disagg_lvst <- "foragebased_jul23"  # def
```

Tier note: rated Major rather than Critical under the rubric tie-breaker — Module 17 genuinely
owns the declaration, so a reader lands in the right neighbourhood; the wrong element is the
inclusion of 70 and the omission of 71.

**Proposed fix.** §11.3 row → `| 17 (declares), 71 (populates cellular kli), 42 (reads) | … | vm_prod(j,kli) |`.
§6.5 heading → "Module 17 (Production) and Module 71 (Livestock disaggregation)". Line 430 →
"`vm_prod(j,kli)`: cellular livestock production — **declared** in
`modules/17_production/flexreg_apr16/declarations.gms:9` (mio. tDM/yr), **populated** by
`modules/71_disagg_lvst/foragebased_jul23/equations.gms:23,37,56` (default realization),
**read** here by `modules/42_water_demand/all_sectors_aug13/equations.gms:14`. Module 70
(livestock) operates on the regional `vm_prod_reg`, not on `vm_prod`."

---

### B3 — 🟠 Major — `default_value` — pumping costs presented without the default-OFF caveat (zero in every default run, India-only data)

**Doc** (`water_balance_conservation.md:333-336`, §6.1 "Key Equations"):

> **Pumping Costs** (`modules/42_water_demand/all_sectors_aug13/equations.gms:16-17`):
> ```gams
> vm_water_cost(i) =e= sum(cell(i,j), vm_watdem("agriculture",j)) * ic42_pumping_cost(i);
> ```

and (`:829-832`):

> **✓ SAFE: Pumping costs** — Module 42, `s42_pumping` and `s42_multiplier` — Affects
> agricultural production costs, not water balance — May reduce irrigation (higher cost)…

**Reality.** `s42_pumping` defaults to **0** (`.../input.gms:39`; `config/default.cfg:1415`), so
`presolve.gms:26` leaves `ic42_pumping_cost(i) = 0` and the whole `if (s42_pumping = 1, …)` block
(`presolve.gms:29-35`) never executes → `vm_water_cost(i) = 0` in every default run. Even with
`s42_pumping = 1`, `s42_multiplier` defaults to 0 (`input.gms:41`, `config/default.cfg:1423`), which
zeroes the cost again for all years after `s42_multiplier_startyear = 1995`, i.e. all of them.
`config/default.cfg:1414` states the data is "only available for India currently".

This is the rubric's own Major trigger *"missing default-state caveat"*, and the switch it names
(`s42_pumping`) is the rubric's Critical anchor example.

**verify_cmd**
```
sed -n '39p;41p' modules/42_water_demand/all_sectors_aug13/input.gms
  → s42_pumping   … / 0 /
    s42_multiplier … / 0 /
sed -n '26,35p' modules/42_water_demand/all_sectors_aug13/presolve.gms
  → ic42_pumping_cost(i) = 0;
    if ((s42_pumping = 1), ic42_pumping_cost(i) = f42_pumping_cost(t,i); … );
sed -n '1414,1415p;1423p' config/default.cfg
  → # * Switch to activate pumping costs (only available for India currently)…
    cfg$gms$s42_pumping <- 0      # def = 0
    cfg$gms$s42_multiplier <- 0      # def = 0
```

**Proposed fix.** Append to the §6.1 Pumping Costs block: "**Inactive by default**:
`s42_pumping = 0` (`.../input.gms:39`; `config/default.cfg:1415`) leaves
`ic42_pumping_cost(i) = 0` (`.../presolve.gms:26`), so `vm_water_cost(i) = 0` in a default run.
The cost data (`f42_pumping_cost`) is India-only. Note that even with `s42_pumping = 1`,
`s42_multiplier = 0` (default) re-zeroes the cost for every year after
`s42_multiplier_startyear = 1995`." Mirror one clause into §10.2.

---

### B4 — 🟠 Major — `other` — the verification snippets call `water_demand()`, which does not exist in magpie4

**Doc** (`water_balance_conservation.md:607`, repeated at `:842`):

> ```r
> watdem <- water_demand(gdx, level="cell", water_source=FALSE)
> ```

**Reality.** In the renv-pinned magpie4 clone (v2.76.4, sha `43970cd4`, per
`project/version_pins.json`) there is **no** `water_demand` symbol anywhere in `R/`, `NAMESPACE`
or `man/`. The function that returns sectoral water withdrawals is **`water_usage()`**
(`R/water_usage.R`, exported at `NAMESPACE:309`), whose signature is
`water_usage(gdx, file, level, users, sum, seasonality, abstractiontype, digits)` — there is no
`water_source` argument. Both `water_usage()` and `water_avail()` return **km³**, not mio. m³, so
the doc's `"mio. m³"` print labels and the `stopifnot(max_violation < 0.01)` threshold are off by
1000×. `water_avail()` also defaults to `sum = TRUE` (already collapsed over sources), so the
following `dimSums(watavail, dim = 3.1)` is at best redundant.

**verify_cmd**
```
grep -rn "water_demand" R/ NAMESPACE man/   (in .cache/sources/magpie4)  → (no output) GREP_EXIT=1
rg -n "water_usage|water_avail" NAMESPACE                                 → 306:export(water_avail)
                                                                             309:export(water_usage)   [positive control]
sed -n '20,30p' R/water_usage.R  → "@return A MAgPIE object containing the water usage (km^3/yr)"
sed -n '14,22p' R/water_avail.R  → "@return A MAgPIE object containing the available water (km^3)"
                                    water_avail(gdx, file=NULL, level="reg", sources=NULL, sum=TRUE, digits=4)
```

**Proposed fix.** Replace all three occurrences with
`watdem <- water_usage(gdx, level = "cell", users = "sectors", sum = TRUE)` (drop the trailing
`dimSums(..., dim = 3.1)` when `sum = TRUE`), replace `dimSums(watavail, dim = 3.1)` with a plain
`water_avail(gdx, level = "cell")` call, and relabel every printed unit as `km³` (tolerance
`< 1e-5 km³`).

---

### B5 — 🟡 Minor — `formula` — `oq43_water.level` is not a surplus (and is not valid syntax)

**Doc** (`water_balance_conservation.md:211-213`):

> 2. **Surplus variable**: `oq43_water.level` = available - withdrawals (≥ 0)
> 3. **Shadow price only when binding**: `oq43_water.marginal` > 0 only if constraint tight

**Reality.** `oq43_water` is a **parameter** with an explicit `type` dimension —
`oq43_water(t,j,type)` (`modules/43_water_availability/total_water_aug13/declarations.gms:23`) —
so `.level` / `.marginal` are not attributes of it; the slices are `oq43_water(t,j,"level")` and
`oq43_water(t,j,"marginal")` (`.../postsolve.gms:11,13`). Substantively, the `"level"` slice is
`q43_water.l(j)` — the GAMS row **activity** of `sum(wat_dem,vm_watdem) =l= sum(wat_src,v43_watavail)`
(`equations.gms:10-11`), i.e. withdrawals **minus** availability (≤ 0), not availability minus
withdrawals. It is not a surplus/penalty variable and there is no such variable in module 43.
On the marginal's sign, magpie4's `water_price()` applies `abs()` to
`readGDX(gdx,"oq43_water")[,,"marginal"]` (`R/water_price.R:31`), so the raw sign is not reliably
positive — see Deferred.

**verify_cmd**
```
sed -n '21,24p' modules/43_water_availability/total_water_aug13/declarations.gms
  → oq43_water(t,j,type)  Local seasonal water constraints (mio. m^3 per yr)
sed -n '10,17p' modules/43_water_availability/total_water_aug13/postsolve.gms
  → oq43_water(t,j,"marginal") = q43_water.m(j);
    oq43_water(t,j,"level")    = q43_water.l(j);
sed -n '31p' .cache/sources/magpie4/R/water_price.R  → p_water_cell <- abs(p_water_cell)
```

**Proposed fix.** Rewrite the two bullets as: "2. **Slack is implicit**: there is no surplus
variable; compute it as `sum(wat_src, ov43_watavail(t,,j,"level")) - sum(wat_dem, ov_watdem(t,,j,"level"))`.
The GDX parameter `oq43_water(t,j,"level")` (`postsolve.gms:13`) holds the GAMS row activity
`q43_water.l`, i.e. withdrawals − availability (≤ 0). 3. **Shadow price**:
`oq43_water(t,j,"marginal")` (`postsolve.gms:11`) is non-zero only when the constraint binds;
magpie4's `water_price()` takes its absolute value (`R/water_price.R:31`)."

---

### B6 — 🟡 Minor — `mechanism` — "No feedback from Module 43 water constraint to Module 41 investment" is false within a time step

**Doc** (`water_balance_conservation.md:411-416`):

> **Known Limitation** (Module 41):
> - AEI expansion decisions do not account for future water scarcity
> - May over-invest in irrigation infrastructure that cannot be fully utilized
> - **No feedback from Module 43 water constraint to Module 41 investment**

**Reality.** All of these live in the **same LP solve**. `q41_area_irrig`
(`modules/41_area_equipped_for_irrigation/endo_apr13/equations.gms:10-11`) ties `vm_AEI(j2)` to
`sum(kcr, vm_area(j2,kcr,"irrigated"))`; that same `vm_area(...,"irrigated")` enters
`q42_water_demand` (`modules/42_water_demand/all_sectors_aug13/equations.gms:10-13`) → `vm_watdem("agriculture",j)`
→ `q43_water` (`modules/43_water_availability/total_water_aug13/equations.gms:10-11`). Since AEI
expansion carries a strictly positive cost (`q41_cost_AEI`, `.../equations.gms:19-23`), a binding
water constraint in the current period *does* suppress current-period AEI investment.

The genuine limitation is (a) intertemporal — MAgPIE is recursive-dynamic, so this period's
investment cannot anticipate *future* runoff decline (the doc's first bullet, which is correct),
and (b) the AEI floor: `vm_AEI.lo(j) = pc41_AEI_start(j) / ((1 - s41_AEI_depreciation)**m_timestep_length)`
(`.../presolve.gms:11`) with `s41_AEI_depreciation = 0` by default (`.../input.gms:11`;
`config/default.cfg:1332`), so inherited AEI can never shrink — that, not blind investment, is
what produces "stranded" AEI.

**verify_cmd**
```
sed -n '10,11p;19,23p' modules/41_area_equipped_for_irrigation/endo_apr13/equations.gms
  → q41_area_irrig(j2) .. sum(kcr, vm_area(j2,kcr,"irrigated")) =l= vm_AEI(j2);
    q41_cost_AEI(i2).. vm_cost_AEI(i2) =e= sum(cell(i2,j2),(vm_AEI(j2)-pc41_AEI_start(j2))) * pc41_unitcost_AEI(i2) * …
sed -n '11p' modules/41_area_equipped_for_irrigation/endo_apr13/presolve.gms
  → vm_AEI.lo(j) = pc41_AEI_start(j) / ((1 - s41_AEI_depreciation)**(m_timestep_length));
sed -n '11p' modules/41_area_equipped_for_irrigation/endo_apr13/input.gms
  → s41_AEI_depreciation … / 0 /
```

**Proposed fix.** Replace the third bullet with: "Within a time step the water constraint *does*
feed back: `q41_area_irrig` (`.../endo_apr13/equations.gms:10-11`) caps irrigated area at `vm_AEI`,
and that area drives `q42_water_demand` → `q43_water` in the same solve, so a binding water
constraint suppresses costly AEI expansion. The limitations are instead (i) recursive-dynamic
myopia — no anticipation of *future* runoff decline — and (ii) `vm_AEI.lo` being pinned to the
inherited stock with `s41_AEI_depreciation = 0` by default (`.../presolve.gms:11`,
`.../input.gms:11`, `config/default.cfg:1332`), so AEI built in a wet period can never be retired."

---

### B7 — 🟡 Minor — `default_value` — the default irrigation-efficiency scenario is **static** (frozen at 1995 GDP), not time-evolving

**Doc** (`water_balance_conservation.md:344-347`):

> **Irrigation Efficiency** (`modules/42_water_demand/all_sectors_aug13/presolve.gms:12-22`):
> - Default: GDP-based sigmoidal function (richer regions more efficient)
> - Range: ~64% (low GDP) to ~90% (high GDP)

**Reality.** The default `s42_irrig_eff_scenario = 2` (`.../input.gms:14`; `config/default.cfg:1363`)
evaluates the sigmoid on `im_gdp_pc_mer("y1995",i)` — a **fixed 1995** GDP per capita
(`.../presolve.gms:18`), so efficiency is constant over the whole run. The time-varying variant
that uses `im_gdp_pc_mer(t,i)` is the **non-default** scenario 3 (`.../presolve.gms:20`). Code
comments call scenario 2 "regional static values" (`input.gms:16`). The doc's phrasing invites the
reader to assume efficiency improves as regions develop, which it does not by default. (The doc's
line 55 statement about `s42_irrig_eff_scenario = 2` vs. the flat 0.66 under scenario 1 is
**correct** and was verified.)

**verify_cmd**
```
sed -n '11,22p' modules/42_water_demand/all_sectors_aug13/presolve.gms
  → Elseif (s42_irrig_eff_scenario = 2), v42_irrig_eff.fx(j) = 1/(1+2.718282**((-22160-sum(cell(i,j),im_gdp_pc_mer("y1995",i)))/37767));
    Elseif (s42_irrig_eff_scenario = 3), v42_irrig_eff.fx(j) = 1/(1+2.718282**((-22160-sum(cell(i,j),im_gdp_pc_mer(t,i)))/37767));
sed -n '14,17p' modules/42_water_demand/all_sectors_aug13/input.gms
  → s42_irrig_eff_scenario … / 2 /   (2: regional static values from CS; 3: gdp driven increase)
grep -n "s42_irrig_eff_scenario" config/default.cfg → 1363: cfg$gms$s42_irrig_eff_scenario <- 2  # def = 2
```

**Proposed fix.** First bullet → "Default (`s42_irrig_eff_scenario = 2`): sigmoid of **1995**
regional GDP per capita (`im_gdp_pc_mer("y1995",i)`, `.../presolve.gms:18`) — regionally
differentiated but **constant over time**. Only the non-default scenario 3 lets efficiency rise
with GDP over the run (`.../presolve.gms:20`)."

---

### B8 — 🟡 Minor — `formula` — index order of `vm_watdem` / `v43_watavail` is inverted in the expanded forms

**Doc** (`water_balance_conservation.md:183-187`, repeated at `:192-195` and `:595-599`):

> ```
> vm_watdem(j,"agriculture") + vm_watdem(j,"manufacturing") + …
> ≤
> v43_watavail(j,"surface") + v43_watavail(j,"ground") + …
> ```

**Reality.** The declared domains are `vm_watdem(wat_dem,j)`
(`modules/42_water_demand/all_sectors_aug13/declarations.gms:29`) and `v43_watavail(wat_src,j)`
(`modules/43_water_availability/total_water_aug13/declarations.gms:13`) — sector/source **first**,
cell second. The doc gets this right in every `gams`-tagged block (§1, §6.1, §6.2) and wrong in
every plain expanded block. Transcribed literally, these would be GAMS domain violations.

**verify_cmd**
```
sed -n '29p' modules/42_water_demand/all_sectors_aug13/declarations.gms
  →   vm_watdem(wat_dem,j)  Amount of water needed in different sectors (mio. m^3 per yr)
sed -n '13p' modules/43_water_availability/total_water_aug13/declarations.gms
  →   v43_watavail(wat_src,j)  Water available from different sources (mio. m^3 per yr)
```

**Proposed fix.** Swap the indices in all three expanded blocks:
`vm_watdem("agriculture",j) + vm_watdem("manufacturing",j) + …` and
`v43_watavail("surface",j) + v43_watavail("ground",j) + …`.

---

### B9 — 🟡 Minor — `mechanism` — the "LPJmL Processing" steps happen in R preprocessing, not in Module 43

**Doc** (`water_balance_conservation.md:127-131`):

> **LPJmL Processing** (Module 43, `modules/43_water_availability/total_water_aug13/realization.gms:9-42`):
> 1. **Basin runoff** … 2. **Growing period restriction** … 3. **Dam exception** … 4. **Cell distribution** …

**Reality.** The citation resolves correctly, but the very first line of the cited passage says
what the doc omits: `realization.gms:9-10` — *"The calculation of available water as described
below happens in the MAgPIE preprocessing."* All four steps are R-side (`mrwater`/`mrmagpie`
producing `lpj_watavail_grper.cs2`). MAgPIE itself only `$include`s that file (`input.gms:19`) and
assigns it (`preloop.gms:8` — `im_wat_avail(t,"surface",j) = f43_wat_avail(t,j);`). Per AGENT.md's
parameterization-vs-mechanism rule, presenting these as Module 43 behaviour overstates what the
GAMS code does.

**verify_cmd**
```
sed -n '9,10p' modules/43_water_availability/total_water_aug13/realization.gms
  → *' The calculation of available water as described below happens
    *' in the MAgPIE preprocessing.
sed -n '16,21p' modules/43_water_availability/total_water_aug13/input.gms
  → f43_wat_avail(t_all,j) … $include "./modules/43_water_availability/input/lpj_watavail_grper.cs2"
```

**Proposed fix.** Retitle to "**LPJmL Processing — happens in the R preprocessing, not in GAMS**
(documented at `.../realization.gms:9-42`)" and add a closing line: "MAgPIE reads the finished
product `modules/43_water_availability/input/lpj_watavail_grper.cs2` (`input.gms:19`) and assigns
it unchanged to `im_wat_avail(t,"surface",j)` (`preloop.gms:8`). Provenance questions belong to
the preprocessing agent (`PREPROC_AGENT.md`)."

---

### B10 — 🟢 Informational — `realization` — the doc never states which realizations it covers

**Doc**: header block (`:1-6`) lists "**Modules Covered**: 42, 43"; no realization is named anywhere
outside file paths.

**Reality.** Module 42 has two realizations and module 41 (covered in §6.4, §9.1, §11.3) has two.
Every path in the doc points at the default (`all_sectors_aug13`, `endo_apr13`,
`total_water_aug13`), so nothing is *wrong* — but AGENT.md Step 1c requires docs to state the
realization they describe. It matters here: under the non-default `agr_sector_aug13` there is no
WATERGAP data at all — `vm_watdem.fx("electricity",j) = 0` and `vm_watdem.fx("domestic",j) = 0`,
and manufacturing is simply `s42_reserved_fraction (0.5) × available water`
(`modules/42_water_demand/agr_sector_aug13/presolve.gms:38-40`), which invalidates the doc's entire
§2.2 and much of §5/§7.5.

**verify_cmd**
```
ls -d modules/42_water_demand/*/  → agr_sector_aug13/  all_sectors_aug13/  input/
ls -d modules/41_area_equipped_for_irrigation/*/ → endo_apr13/  input/  static/
ls -d modules/43_water_availability/*/ → input/  total_water_aug13/
sed -n '36,44p' modules/42_water_demand/agr_sector_aug13/presolve.gms
  → vm_watdem.fx("manufacturing",j) = sum(wat_src, im_wat_avail(t,wat_src,j)) * s42_reserved_fraction;
    vm_watdem.fx("electricity",j) = 0;
    vm_watdem.fx("domestic",j) = 0;
grep -n "cfg\$gms\$water_demand\|cfg\$gms\$water_availability\|cfg\$gms\$area_equipped" config/default.cfg
  → 1340: cfg$gms$water_demand<- "all_sectors_aug13"   # def
    1427: cfg$gms$water_availability <- "total_water_aug13"  # def
    1323: cfg$gms$area_equipped_for_irrigation <- "endo_apr13"  # def
```

**Proposed fix.** Extend the header block to:
"**Realizations covered**: 42 → `all_sectors_aug13` (default; alternative `agr_sector_aug13` sets
electricity and domestic demand to zero and manufacturing to `s42_reserved_fraction × available
water`); 43 → `total_water_aug13` (only realization); 41 → `endo_apr13` (default; alternative
`static`)."

---

### B11 — 🟢 Informational — `other` — unlabeled pseudo-GAMS in §2.2 uses a symbol that does not exist

**Doc** (`water_balance_conservation.md:70-72`):

> ```gams
> vm_watdem.fx(watdem_ineldo,j) = f42_watdem_ineldo(t,j,ssp_scenario,watdem_ineldo,"withdrawal");
> ```

**Reality.** There is no `ssp_scenario` symbol. The code hard-codes the literal in each branch —
`"ssp1"` / `"ssp2"` / `"ssp3"` at `.../presolve.gms:45,48,51`, plus an unconditional `"ssp2"` for
all years `m_year(t) <= sm_fix_SSP2` (`presolve.gms:40-41`). The block is fenced as ```gams``` with
no "schematic" label.

**verify_cmd**
```
sed -n '40,54p' modules/42_water_demand/all_sectors_aug13/presolve.gms
  → if (m_year(t) <= sm_fix_SSP2, vm_watdem.fx(watdem_ineldo,j) = f42_watdem_ineldo(t,j,"ssp2",…);
    else … Elseif (s42_watdem_nonagr_scenario = 2), … "ssp2" … );
```

**Proposed fix.** Label the block "*(schematic — the SSP label is a literal chosen by the
`s42_watdem_nonagr_scenario` branch)*", and add: "for `m_year(t) <= sm_fix_SSP2` the code uses
`"ssp2"` unconditionally regardless of the switch (`presolve.gms:40-41`)."

---

## Verified-correct (no bug — recorded so future rounds don't re-litigate)

- `q43_water` formula, both sides, `=l=` operator — exact match, `.../43_.../equations.gms:10-11`.
- `wat_dem` = 5 members, `wat_src` = 4 members — `core/sets.gms:244,247`; the "4 potential / only
  surface active" framing matches `preloop.gms:8,10-12`.
- Infeasibility-buffer algebra, incl. the 1.01 factor, `watdem_exo` membership (domestic,
  manufacturing, electricity, ecosystem — `.../42_.../sets.gms:9-10`) and the agriculture exclusion
  — `.../43_.../presolve.gms:14-16`.
- "default: all ISO countries/territories — the full 249-member iso set": **249 exactly**
  (`.../42_.../input.gms:52-76`), matching `core/sets.gms:37-58`.
- `s42_env_flow_scenario = 2` default (`input.gms:22`, `config/default.cfg:1401`);
  `s42_env_flow_fraction = 0.2`; `s42_env_flow_base_fraction = 0.05`;
  `s42_watdem_nonagr_scenario = 2` (SSP2) default; `s42_efp_startyear/targetyear` = 2025/2040;
  `c43_watavail_scenario = "cc"` default (`input.gms:9`, `config/default.cfg:1433`).
- Line 55's irrigation-efficiency claim (sigmoid default vs. flat 0.66 under the non-default
  `s42_irrig_eff_scenario = 1`) — correct, `.../42_.../presolve.gms:15-18`.
- "~200 MAgPIE cells" — default cellular input is `…_c200_…` (`config/default.cfg:26`).
- §11.4 "7 land types (all endogenous except urban)" — `core/sets.gms:250-251` (7 members);
  `cfg$gms$urban <- "exo_nov21"` (`config/default.cfg:1147`) is exogenous.
- `vm_AEI(j)` (`.../41_.../endo_apr13/declarations.gms:19`), `vm_area(j,kcr,w)`
  (`.../30_croparea/simple_apr24/declarations.gms:18`, default realization) — names and domains correct.
- `im_wat_avail` flow 43 → 42: genuine (declared+populated in 43, read in
  `.../42_.../all_sectors_aug13/presolve.gms:58,64`). Role map agrees.
- All 22 file:line citations resolve to the claimed content in current `develop`.

---

## Deferred (not verifiable here — no edit proposed)

1. Sign of `oq43_water(t,j,"marginal")`. The doc says "> 0 only if constraint tight"
   (`:213`); LP duality for a `=l=` row in a cost **minimisation** argues for ≤ 0, and magpie4
   applies `abs()` (`R/water_price.R:31`), but I cannot run GAMS here to settle the reported sign.
2. The realized numeric range of `v42_irrig_eff` ("~64% to ~90%", `:346`). The sigmoid floor at
   GDP → 0 is 0.643 (arithmetic), but the upper end depends on `im_gdp_pc_mer("y1995",i)` values
   that live in gitignored module-09 input data.
3. `readGDX(gdx, "oq43_water", select = list(type = "marginal"), field = "level")` (`:667`, `:860`)
   — combining `select=` and `field=` on a GDX *parameter* looks wrong (magpie4 itself uses
   `readGDX(gdx,"oq43_water")[,,"marginal"]`), but I did not exercise gdx/readGDX to confirm it errors.
4. §6.1/§6.2/§6.3's "shadow prices flow from Module 43 to Module 42 / enter Module 30's objective
   function" (`:342`, `:363`, `:392`). Module 42 contains **zero** references to `q43_water`
   (`rg -n "q43_water|oq43_water" modules/42_water_demand/` → EXIT 1, positive control on
   `im_wat_avail` passes), so this is LP simultaneity rather than a code-level hand-off, and duals
   never appear in the objective — but the passage reads as deliberate economic exposition, so I am
   not calling it a defect.
5. Whether the doc's numbered §3.1 "Growing Period Examples" percentages (`:134-136`) match the
   preprocessing output — requires the `.cs2` input, which is gitignored.
6. `readRDS("baseline_water_demand.rds")` in §10.3 Step 5 (`:867`) — a user-supplied artifact, not a
   magpie4/MAgPIE object; nothing to verify.
