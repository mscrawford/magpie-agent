# Module 70: Livestock (fbask_jan16)

**Status**: Verified against `0d7ebeb90`; R58 (2026-07-17) corrected 11 defects — see §Verification for scope
**Realization**: `fbask_jan16` (feed basket-based, January 2016)
**Alternative**: `fbask_jan16_sticky` (same methodology with additional stickiness mechanism, 8 equations)
**Equations**: 7 (`fbask_jan16`) / 8 (`fbask_jan16_sticky`)
**Lines of Code**: 625 (main realization, raw `wc -l` over its 9 `.gms` files; 466 excluding `input.gms` + `sets.gms`)
**Authors**: Isabelle Weindl, Benjamin Bodirsky

---

> ⚙️ **Default Realization**: `fbask_jan16`
> Confirmed in `config/default.cfg`: `cfg$gms$livestock <- "fbask_jan16"`. Alternative `fbask_jan16_sticky` adds production stickiness to prevent abrupt regional livestock shifts.


## Overview

Module 70 (Livestock) calculates regional feed demand for livestock production using exogenous feed baskets and livestock productivity trajectories (`realization.gms:8-81`). The module implements the methodology of Weindl et al. (2017) based on Wirsenius (2000), converting livestock production targets into feed requirements across multiple feed types (cereals, fodder, pasture, crop residues, etc.) (`realization.gms:20-35`).

**Core Function**: Livestock production → Feed baskets → Feed demand → Pass to demand/pasture/methane modules

**Key Mechanism**: Feed baskets (tDM feed per tDM product) are pre-calculated outside GAMS using regression models linking feed conversion and feed composition to livestock productivity, then applied to regional production volumes (`realization.gms:37-75`).

**Critical Interface**: Provides `vm_dem_feed(i,kap,kall)` to Module 16 (Demand), which aggregates feed demand with food/material/bioenergy demands and passes aggregated demand to Module 21 (Trade) (`module.gms:18-19`).

---

## Core Equations (7 total)

### 1. Feed Intake Pre-Calculation (`q70_feed_intake_pre`)

**Purpose**: Calculate feed intake before balance flow adjustments

**Formula** (`equations.gms:35-37`):
```
v70_feed_intake_pre(i2,kap,kall) =e=
    vm_prod_reg(i2,kap) * sum(ct, im_feed_baskets(ct,i2,kap,kall))
```

**Dimensions**:
- `i`: Region
- `kap`: Livestock products (kli) + fish
- `kall`: All feed items (cereals, fodder, pasture, residues, SCP, etc.)

**Mechanism**: Multiply regional production (tDM) by feed basket coefficient (tDM feed per tDM product) to get feed intake before any balance flow corrections (`equations.gms:10-15`).

**Units**: mio. tDM per yr

---

### 2. Feed Intake (`q70_feed_intake`)

**Purpose**: Adjust feed intake by optionally incorporating balance flows

**Formula** (`equations.gms:39-42`):
```
vm_feed_intake(i2,kap,kall) =e=
    v70_feed_intake_pre(i2,kap,kall) * (1 - s70_feed_intake_weight_balanceflow)
    + vm_dem_feed(i2,kap,kall) * s70_feed_intake_weight_balanceflow
```

**Parameters**:
- `s70_feed_intake_weight_balanceflow`: Weight for including balance flows (default: 1) (`input.gms:28`)

**Mechanism** (`equations.gms:31-33`):
- If weight = 0: Feed intake = pure feed basket calculation (no balance flows)
- If weight = 1: Feed intake = feed demand (includes all balance flows)
- Intermediate values blend both approaches

**Purpose**: Feed intake (used for nutrient calculations in other modules) can differ from feed demand (used for production constraint) depending on whether balance flow inconsistencies should propagate to nutrient budgets.

**Units**: mio. tDM per yr

---

### 3. Feed Demand (`q70_feed`)

**Purpose**: Calculate regional feed demand including balance flow corrections

**Formula** (`equations.gms:17-20`):
```
vm_dem_feed(i2,kap,kall) =g=
    vm_prod_reg(i2,kap) * sum(ct, im_feed_baskets(ct,i2,kap,kall))
    + sum(ct, vm_feed_balanceflow(i2,kap,kall))
```

**Constraint Type**: Inequality (≥) - feed demand must be at least production × feed basket + balance flows

**Components** (`equations.gms:10-15`):
1. **Production × Feed Basket**: Core feed requirement from regression-based feed baskets
2. **Balance Flow**: Correction term to reconcile model estimates with FAO feed statistics and account for alternative feed sources (scavenging, roadside grazing)

**Units**: mio. tDM per yr

**Critical Output**: `vm_dem_feed(i,kap,kall)` is passed to Module 16 (Demand) where it contributes to total commodity demand alongside food, material, seed, and bioenergy demands (`module.gms:18-19`).

---

### 4. Feed Balance Flow for Ruminants (`q70_feed_balanceflow`)

**Purpose**: Calculate pasture balance flows for ruminant products, accounting for scavenging and roadside grazing

**Formula** (`equations.gms:25-29`):
```
vm_feed_balanceflow(i2,kli_rum,"pasture") =e=
    (sum(ct, fm_feed_balanceflow(ct,i2,kli_rum,"pasture")))
        $ (p70_endo_scavenging_flag(i2,kli_rum) = 0)
    - (vm_prod_reg(i2,kli_rum) * sum(ct, im_feed_baskets(ct,i2,kli_rum,"pasture"))
        * s70_scavenging_ratio)
        $ (p70_endo_scavenging_flag(i2,kli_rum) > 0)
```

**Dimensions**:
- `kli_rum`: Ruminant products (livst_rum, livst_milk)
- Only applies to "pasture" feed item

**Parameters**:
- `s70_scavenging_ratio`: Ratio to adjust pasture demand using scavenged feed (default: 0.385) (`input.gms:27`)

**Conditional Logic** (`equations.gms:22-29`):
1. **If scavenging flag = 0**: Use exogenous balance flow from FAO inventory (`fm_feed_balanceflow`)
2. **If scavenging flag > 0**: Apply endogenous scavenging adjustment (reduce pasture demand by 38.5% of baseline pasture requirement)

**Scavenging Flag Calculation** (`presolve.gms:14-20`):
- Flag computed in the **last historical timestep** (under the default config: `t = y2015`), then
  frozen — see the correction under §Feed Balance Flows → Scavenging Flag Activation
- Compares previous balance flow ratio to scavenging threshold
- If `(-fm_feed_balanceflow(t-1) / pc70_dem_feed_pasture) ≥ s70_scavenging_ratio`, enable endogenous scavenging for that region

**Interpretation**: Negative balance flows reduce net pasture demand, representing feed from scavenging (household waste, roadside grazing) that substitutes for conventional pasture (`equations.gms:22-23`).

**Units**: mio. tDM

---

### 5. Livestock Labor Costs (`q70_cost_prod_liv_labor`)

**Purpose**: Calculate labor costs for livestock production with wage scenario adjustments

**Formula** (`equations.gms:59-62`):
```
vm_cost_prod_livst(i2,"labor") =e=
    sum(kli, vm_prod_reg(i2,kli) * sum(ct, i70_fac_req_livst(ct,i2,kli)))
    * sum(ct, pm_factor_cost_shares(ct,i2,"labor"))
    * sum(ct, (1 / pm_productivity_gain_from_wages(ct,i2))
        * (pm_hourly_costs(ct,i2,"scenario") / pm_hourly_costs(ct,i2,"baseline")))
```

**Components** (`equations.gms:45-57`):
1. **Production × Factor Requirements**: `vm_prod_reg × i70_fac_req_livst` (USD17MER per tDM)
2. **Labor Share**: `pm_factor_cost_shares(i,"labor")` (from Module 38)
3. **Wage Scaling**: `(hourly_costs_scenario / hourly_costs_baseline)` adjusts for external wage scenario
4. **Productivity Adjustment**: `1 / pm_productivity_gain_from_wages` reduces costs if higher wages boost productivity (from Module 36)

**Factor Requirements** (`preloop.gms:88`):
```
i70_fac_req_livst(t_all,i,kli) = i70_cost_regr(i,kli,"cost_regr_b")
    * sum(sys_to_kli(sys,kli), i70_livestock_productivity(t_all,i,sys))
    + i70_cost_regr(i,kli,"cost_regr_a")
```
(indexed by `t_all`, not the optimization time set `t` — `t_all` spans all timesteps including history; both `i70_fac_req_livst` and `i70_livestock_productivity` are declared over `t_all`.)

**Regression Logic** (`equations.gms:48-53`):
- **Ruminants (beef, milk)**: Costs increase with productivity (linear regression: `b * productivity + a`)
- **Non-ruminants (pork, poultry, eggs)**: Constant per-unit costs (`b = 0`, only intercept `a`)
- **Fish**: Constant per-unit costs from GTAP data

**Units**: mio. USD17MER per yr

---

### 6. Livestock Capital Costs (`q70_cost_prod_liv_capital`)

**Purpose**: Calculate capital costs for livestock production

**Formula** (`equations.gms:64-66`):
```
vm_cost_prod_livst(i2,"capital") =e=
    sum(kli, vm_prod_reg(i2,kli) * sum(ct, i70_fac_req_livst(ct,i2,kli)))
    * sum(ct, pm_factor_cost_shares(ct,i2,"capital"))
```

**Mechanism**: Same production × factor requirements calculation as labor, but without wage scenario adjustments (capital costs independent of hourly wages) (`equations.gms:48-53`).

**Units**: mio. USD17MER per yr

**Total Livestock Costs**: `vm_cost_prod_livst(i,"labor") + vm_cost_prod_livst(i,"capital")` passed to Module 11 (Costs) for aggregation into the objective function (`modules/11_costs/default/equations.gms`).

**`vm_cost_prod_livst` has TWO consumers, not one.** Module 36 (Employment) also reads it — the `"labor"` slice — to compute agricultural employment: `vm_cost_prod_crop(i2,"labor") + vm_cost_prod_livst(i2,"labor") + ...` (`modules/36_employment/exo_may22/equations.gms:24`).

> ⚠️ **CORRECTED (R58, 2026-07-17)**: M36 was missing from this consumer set. This also means the
> M70↔M36 relationship is **reciprocal** — M36 reads `vm_cost_prod_livst` while M70 reads M36's wage
> scenario parameters (see §Depends On) — a real cycle the doc did not record.

---

### 7. Fish Production Costs (`q70_cost_prod_fish`)

**Purpose**: Calculate factor input costs for fish production

**Formula** (`equations.gms:68-70`):
```
vm_cost_prod_fish(i2) =e=
    vm_prod_reg(i2,"fish") * i70_cost_regr(i2,"fish","cost_regr_a")
```

**Mechanism**: Simple linear cost function using only intercept term (no productivity scaling) (`equations.gms:48-53`).

**Regression Coefficient**: `i70_cost_regr(i,"fish","cost_regr_a")` derived from GTAP database (`preloop.gms:85`).

**Units**: mio. USD17MER per yr

**Output**: `vm_cost_prod_fish(i)` passed to Module 11 (Costs).

---

## Alternative Realization: `fbask_jan16_sticky` (8 equations)

The `fbask_jan16_sticky` realization shares 6 of 7 equations with `fbask_jan16` (`q70_feed_intake_pre`, `q70_feed_intake`, `q70_feed`, `q70_feed_balanceflow`, `q70_cost_prod_liv_labor`, `q70_cost_prod_fish`). It **replaces** `q70_cost_prod_liv_capital` with an investment-based formulation and **adds** a new `q70_investment` equation, implementing a "sticky" capital stock mechanism analogous to the `sticky_feb18` pattern used in other modules.

### Modified: Livestock Capital Costs (`q70_cost_prod_liv_capital`)

**Purpose**: Calculate capital costs using annuitized investment with depreciation (replaces the factor-cost-shares approach in `fbask_jan16`)

**Formula** (`fbask_jan16_sticky/equations.gms`):
```
vm_cost_prod_livst(i2,"capital") =e=
    sum(kli, v70_investment(i2,kli))
    * ((1 - s70_depreciation_rate) * sum(ct, pm_interest(ct,i2) / (1 + pm_interest(ct,i2)))
       + s70_depreciation_rate)
```

**Components**:
1. **Investment Sum**: `sum(kli, v70_investment(i2,kli))` — total new investment across all livestock products (mio. USD17MER per yr)
2. **Annuity Factor**: `(1 - s70_depreciation_rate) * pm_interest / (1 + pm_interest)` — annuitized interest on non-depreciated capital
3. **Depreciation**: `s70_depreciation_rate` — annual depreciation charge on capital stock

**Parameters**:
- `s70_depreciation_rate`: Yearly depreciation rate for capital stocks (default: 0.05) (`fbask_jan16_sticky/input.gms:34`)
- `pm_interest(t,i)`: Regional interest rate (from Module 12)

**Key Difference from `fbask_jan16`**: In `fbask_jan16`, capital costs are computed as `production × factor_requirements × capital_share`, a simple proportional cost. In `fbask_jan16_sticky`, capital costs are based on *investment* in immobile farm capital, creating path dependency — existing capital stocks carry over between timesteps and only need replacement when depreciated or when production expands.

**Units**: mio. USD17MER per yr

---

### New: Livestock Investment (`q70_investment`)

**Purpose**: Ensure sufficient investment to cover capital requirements for livestock production, accounting for pre-existing capital stocks

**Formula** (`fbask_jan16_sticky/equations.gms`):
```
v70_investment(i2,kli) =g=
    vm_prod_reg(i2,kli) * sum(ct, p70_capital_need(ct,i2,kli))
    - sum(ct, p70_capital(ct,i2,kli))
```

**Constraint Type**: Inequality (≥) — investment must cover at least the gap between required and existing capital

**Components**:
1. **Required Capital**: `vm_prod_reg × p70_capital_need` — total capital needed for current production level
2. **Existing Capital**: `p70_capital(t,i,kli)` — pre-existing immobile capital stocks after depreciation

**Capital Need Calculation** (`fbask_jan16_sticky/presolve.gms`):
```
p70_capital_need(t,i,kli) = i70_fac_req_livst(t,i,kli)
    * pm_factor_cost_shares(t,i,"capital")
    / (pm_interest(t,i) + s70_depreciation_rate)
    * s70_multiplicator_capital_need
```

**Capital Stock Update** — a **two-phase** lifecycle. Both phases are required; presolve alone does
not produce a stock.

*Phase 1 — presolve* (`fbask_jan16_sticky/presolve.gms:83-95`):
- First timestep (`ord(t) = 1`, `:87`): `p70_capital(t,i,kli) = p70_capital_need(t,i,kli) * p70_initial_1995_prod(i,kli)`
- Subsequent timesteps (`else`, `:93`): `p70_capital(t,i,kli) = p70_capital(t,i,kli) * (1-s70_depreciation_rate)**(m_timestep_length)`

*Phase 2 — postsolve* (`fbask_jan16_sticky/postsolve.gms:13`):
```
p70_capital(t+1,i,kli) = p70_capital(t,i,kli) + v70_investment.l(i,kli);
```
Realized investment (a `.l` solution-level read) is accumulated into the **next** timestep's stock.

> ⚠️ **CORRECTED (R58, 2026-07-17)**: the doc previously documented only the presolve phase, leaving
> a mechanism that cannot carry anything over. Note the direction of the gap precisely: the
> presolve `else`-branch at `:93` reads `p70_capital(t,...)` on its **right-hand side**, and the
> **only** writer of `p70_capital(t,...)` for `t > 1` is `postsolve.gms:13`. Without the postsolve
> line, `p70_capital(t>1)` would be **identically zero** (GAMS parameters default to 0), so the
> else-branch would yield `0 × (1-δ)^len = 0` — not a stock decaying from its 1995 initialization.
> The postsolve carry-forward is what makes the path dependency described above real. Non-default
> realization, so the blast radius is capped.

**Parameters**:
- `s70_multiplicator_capital_need`: Multiplier for capital need (default: 1) (`fbask_jan16_sticky/input.gms:35`)
- `p70_initial_1995_prod(i,kli)`: Initial 1995 production from historical data (`fbask_jan16_sticky/preloop.gms`)

**Mechanism**: When production increases, `v70_investment` must rise to cover the additional capital requirement. When production decreases, existing capital exceeds needs, so no new investment is required (the inequality allows `v70_investment` to be zero). This creates asymmetric adjustment costs — expansion is costly but contraction is "free" (sunk capital).

**Units**: mio. USD17MER per yr

---

## Livestock Production Systems

Module 70 uses 5 livestock production systems (`sets.gms:20-21`):

1. **sys_pig**: Pig/pork production
2. **sys_beef**: Beef cattle production
3. **sys_chicken**: Broiler chicken production (meat)
4. **sys_hen**: Laying hen production (eggs)
5. **sys_dairy**: Dairy cattle production (milk)

**System-to-Product Mapping** (`sets.gms:30-36`):
- sys_pig → livst_pig
- sys_beef → livst_rum (ruminant meat)
- sys_chicken → livst_chick
- sys_hen → livst_egg
- sys_dairy → livst_milk

**Fish**: Handled separately (not part of 5-system framework), has own cost equation.

---

## Feed Basket Methodology

### Preprocessing (Outside GAMS)

Feed baskets are calculated via preprocessing routines before entering MAgPIE-GAMS code (`realization.gms:18-35`):

1. **Feed Energy Balances**: Compile system-specific feed energy balances using bio-energetic equations from Wirsenius (2000) for maintenance, growth, lactation, reproduction, activity, temperature effects
2. **Country-Level Feed Distribution**: Distribute available feed to animal systems according to feed energy demand
3. **Feed Conversion**: Calculate feed conversion (total feed input per product output in DM) by dividing feed use by production volume
4. **Feed Baskets**: Derive feed baskets (demand for different feed types per product output in DM) from feed distribution
5. **Regression Models**: Create regression models with livestock productivity as predictor to enable scenario projections

### Feed Conversion vs. Livestock Productivity

**Power Function** (`realization.gms:47-51`):
Feed conversion depends on livestock productivity via power function relationship (see `feed_conv.jpg` diagram).

**Livestock Productivity Definition** (`realization.gms:42-45`):
- **Beef, pork, broilers**: Meat production per animals in stock (ton FM / animal / yr)
- **Dairy, laying hens**: Milk/egg production per producing animals (ton FM / animal / yr)

### Feed Composition vs. Livestock Productivity

**Dual Predictors** (`realization.gms:53-62`):
1. **Universal aspects**: Energy-rich feed needs at higher productivity (applies globally)
2. **Geographical aspects**: Climate-zone specific factors influence feed type availability (arid/cold climate zones affect pasture vs. cropland feed preference)

**Climate Proxy**: For cattle systems, proxy determined by share of national population in arid and cold climate zones (`realization.gms:59-62`).

**Regression Relationships**: See `feed_comp_beef.jpg` and `feed_comp_dairy.jpg` for relationship between feed basket composition (crop residues, occasional feed, grazed biomass) and livestock productivity for beef and dairy cattle systems (`realization.gms:64-70`).

### Feed Basket Input Data

**Primary Input** (`input.gms:36-39`):
```
f70_feed_baskets(t_all,i,kap,kall,feed_scen70)
```

**Scenarios** (`sets.gms:16-18`):
- SSPs: ssp1, ssp2, ssp3, ssp4, ssp5
- SDP variants: SDP, SDP_EI, SDP_MC, SDP_RC
- Other: constant

**Selection Logic** (`preloop.gms:13-23`):
- Historical period (≤ sm_fix_SSP2): Use SSP2 feed baskets
- Future period: Use scenario selected by `c70_feed_scen` switch (default: ssp2)

> **Scope note**: the same `preloop.gms:13-23` loop also uses `c70_feed_scen` to select the `feed_scen70` slice of **two other** tables in the same pass — `f70_livestock_productivity` → `i70_livestock_productivity` and `f70_slaughter_feed_share` → `im_slaughter_feed_share`. `i70_livestock_productivity` propagates beyond feed composition into livestock factor costs and Module 14 pasture yields. See **Configuration Options → Feed Scenario Selection** below for the full scope and the downstream path.

**SSP Narratives** (`realization.gms:72-75`): Feed basket scenarios reflect SSP storylines regarding intensification trajectories, affecting feed conversion efficiency and feed composition.

**Units**: tDM feed per tDM livestock product (dimensionless ratio)

---

## Feed Balance Flows

### Purpose

Balance flows reconcile two data sources (`equations.gms:10-15`):
1. **Model estimates**: Production × feed baskets (from regression models)
2. **FAO statistics**: Actual national feed use inventories

### Components

**Historical Balance Flows** (`input.gms:41-44`):
```
fm_feed_balanceflow(t_all,i,kap,kall)
```
Pre-calculated difference between FAO-reported feed use and model-estimated feed baskets.

**Endogenous Scavenging Adjustment** (`equations.gms:22-29`):
For ruminants in regions where historical balance flows exceed threshold, future balance flows are calculated endogenously as fraction of pasture requirement (38.5% default) to represent scavenging and roadside grazing.

### Balance Flow Logic

**Non-Pasture Feed Items** (`presolve.gms:9`):
Balance flows fixed to historical FAO values:
```
vm_feed_balanceflow.fx(i,kap,kall) = fm_feed_balanceflow(t,i,kap,kall)
```

**Pasture Feed for Ruminants** (`presolve.gms:10-11`):
Bounds relaxed to allow endogenous calculation:
```
vm_feed_balanceflow.up(i,kli_rum,"pasture") = Inf
vm_feed_balanceflow.lo(i,kli_rum,"pasture") = -Inf
```

**Scavenging Flag Activation** (`presolve.gms:14-20`):
```
p70_endo_scavenging_flag(i,kli_rum) =
    -fm_feed_balanceflow(t-1,i,kli_rum,"pasture") / pc70_dem_feed_pasture(i,kli_rum)
```
If ratio ≥ s70_scavenging_ratio (0.385), flag set to ratio value; otherwise flag = 0.

**Timing — fires in the LAST HISTORICAL timestep** (`presolve.gms:14`, `:16`):
- **Outer guard** (`presolve.gms:14`): `if (sum(sameas(t_past,t),1) = 1, ...)` — true **iff the
  current timestep `t` is itself in `t_past`**, i.e. iff `t` is a *historical* timestep. It can
  never be true in a future timestep.
- **Inner guard** (`presolve.gms:16`): `if (ord(t) = smax(t2, ord(t2)$(t_past(t2))) AND card(t) >
  sum(t_all$(t(t_all) and t_past(t_all)), 1), ...)` — narrows to the **last** historical timestep,
  and only when future timesteps exist at all.
- **Resolved against the default config**: `c_past = "till_2015"` (`config/default.cfg:136`) →
  `t_past = {y1965…y2015}`; `c_timesteps = "coup2100"` (`config/default.cfg:133`) →
  `t = {y1995, y2000, …, y2100}`. So the flag is computed at **`t = y2015`**, and because presolve
  precedes the solve, the switch to endogenous scavenging takes effect **within that same
  historical timestep**. Every shipped `c_timesteps` option starts at `y1995`, so no configuration
  makes this a future timestep.
- **The flag then persists**: `p70_endo_scavenging_flag` is a parameter written once and never
  reset (the outer guard never fires again once `t` leaves `t_past`). Every future timestep reads a
  value computed at the historical boundary — scavenging is **fixed at the seam**, not recomputed
  from each timestep's pasture demand.

> ⚠️ **CORRECTED (R58, 2026-07-17)**: the doc previously stated (in two places) that the flag is
> "activated in first future timestep after historical period". That is the exact negation of the
> outer guard. Consequence for readers: the last historical year (`y2015` by default) does **not**
> still use exogenous FAO balance flows in flagged regions — it is already endogenous. Anyone
> validating M70 against FAO history in that year, or attributing a discontinuity to the
> historical/future boundary, is off by one timestep and on the wrong side of the seam. The doc's
> *rationale* ("to avoid overwriting in subsequent timesteps") was correct; only the firing timestep
> was wrong.

**Interpretation**: Regions with large negative historical pasture balance flows (indicating substantial non-pasture feed sources like scavenging) continue to use scavenging in future, scaled to production levels.

---

## Single-Cell Protein (SCP) Substitution

Module 70 includes scenarios for substituting conventional feed (cereals, fodder) with single-cell protein (SCP) produced via nitrogen-based processes (`preloop.gms:58-78`).

### Configuration

**Switches** (`input.gms:18-19`) — ⚠️ **INERT, do not use**:
- `c70_cereal_scp_scen`: `$setglobal ... constant` (`input.gms:18`)
- `c70_foddr_scp_scen`: `$setglobal ... constant` (`input.gms:19`)

> ⚠️ **CORRECTED (R58, 2026-07-17)**: these two switches were documented as the SCP scenario
> control. **They select nothing.** Each occurs in exactly 4 places repo-wide — the `$setglobal`
> line in each of the two realizations' `input.gms` — and is never expanded (`%c70_cereal_scp_scen%`
> does not exist), never compared in a `$if`, never used as an index. They are also absent from
> `config/default.cfg`, so they have no config surface at all. (Positive controls on the same search:
> `c70_feed_scen` returns its `$setglobal` **plus** `%c70_feed_scen%` expansions at `preloop.gms:19-21`
> **plus** `config/default.cfg:2170`; `c70_fac_req_regr` returns `$if "%c70_fac_req_regr%" ==` guards at
> `preloop.gms:82,83,90` **plus** `config/default.cfg:2206`.)
>
> The SCP mechanism is driven **entirely** by the `s70_*` scalars below — substitution shares
> (`s70_cereal_scp_substitution` / `s70_foddr_scp_substitution`), functional form
> (`s70_subst_functional_form`), and the window (`s70_feed_substitution_start` / `_target`) — see
> `preloop.gms:40-55`, which references the `c70_*` switches nowhere.

**Scenario names** (`sets.gms:41-45`) — these are members of the set `fadeoutscen70`, which is
declared and **never referenced again** anywhere in the repository. They are the legal values of an
unexpanded switch, i.e. a transcription with no behavioral meaning. Listed for completeness only:
- constant (no substitution)
- Linear fadeout variants: lin_zero_10_50, lin_zero_20_50, lin_50pc_20_50, lin_80pc_20_50, etc.
- Sigmoid fadeout variants: sigmoid_20pc_20_50, sigmoid_50pc_20_50, sigmoid_80pc_20_50
- Naming convention: `lin/sigmoid_TARGET_START_END` (e.g. `lin_50pc_20_50` reads as "linear to 50%
  substitution from 2020-2050"). ⚠️ The name is **never parsed by any code** — nothing reads the
  target, start, or end out of the string. The actual shape/target/window come only from the `s70_*`
  scalars.

**Substitution Levels** (`input.gms:32-33`):
- `s70_cereal_scp_substitution`: Cereal substitution share (default: 0)
- `s70_foddr_scp_substitution`: Fodder substitution share (default: 0)

**Functional Form** (`input.gms:29`):
- `s70_subst_functional_form`: 1 = linear, 2 = sigmoid (default: 1)

**Transition Period** (`input.gms:30-31`):
- `s70_feed_substitution_start`: Start year (default: 2025)
- `s70_feed_substitution_target`: Target year (default: 2050)

### Mechanism

**1. Generate Time Fader** (`preloop.gms:40-50`):
```
if (s70_subst_functional_form = 1):
    m_linear_time_interpol(p70_cereal_subst_fader, 2025, 2050, 0, s70_cereal_scp_substitution)
elseif (s70_subst_functional_form = 2):
    m_sigmoid_time_interpol(p70_cereal_subst_fader, 2025, 2050, 0, s70_cereal_scp_substitution)
```

**2. Calculate Fadeout Factor** (`preloop.gms:52-55`):
```
i70_cereal_scp_fadeout(t,i) = 1 - p70_feedscen_region_shr(t,i) * p70_cereal_subst_fader(t)
i70_foddr_scp_fadeout(t,i) = 1 - p70_feedscen_region_shr(t,i) * p70_foddr_subst_fader(t)
```
- `p70_feedscen_region_shr(t,i)`: Regional share affected by scenario (weighted by population) (`preloop.gms:37`)
- Default: All countries affected (share = 1)

**3. Cereal → SCP Substitution** (`preloop.gms:58-67`):
Convert cereals to nitrogen, then convert substituted nitrogen to SCP dry matter:
```
im_feed_baskets(t,i,kap,"scp") +=
    sum(kcer70, im_feed_baskets(t,i,kap,kcer70)
        * (1 - i70_cereal_scp_fadeout(t,i))
        * fm_attributes("nr",kcer70)) / fm_attributes("nr","scp")

im_feed_baskets(t,i,kap,kcer70) *= i70_cereal_scp_fadeout(t,i)
```
- `kcer70`: Cereals (tece, maiz, trce, rice_pro) (`sets.gms:38-39`)
- Preserves nitrogen content during substitution

**4. Fodder → SCP Substitution** (`preloop.gms:69-78`):
Same nitrogen-based conversion:
```
im_feed_baskets(t,i,kap,"scp") +=
    (im_feed_baskets(t,i,kap,"foddr")
        * (1 - i70_foddr_scp_fadeout(t,i))
        * fm_attributes("nr","foddr")) / fm_attributes("nr","scp")

im_feed_baskets(t,i,kap,"foddr") *= i70_foddr_scp_fadeout(t,i)
```

**Result**: Feed baskets dynamically shift from cereals/fodder to SCP over transition period, reducing land-based feed requirements.

---

## Factor Cost Regression

Module 70 calculates livestock factor costs using regression relationships between per-unit factor requirements and livestock productivity (`equations.gms:45-53`).

### Regression Formula

**Factor Requirements** (`preloop.gms:88`):
```
i70_fac_req_livst(t_all,i,kli) =
    i70_cost_regr(i,kli,"cost_regr_b")
    * sum(sys_to_kli(sys,kli), i70_livestock_productivity(t_all,i,sys))
    + i70_cost_regr(i,kli,"cost_regr_a")
```
(indexed by `t_all`, not `t` — `t_all` spans all timesteps including history; both `i70_fac_req_livst` and `i70_livestock_productivity` are declared over `t_all`, per `declarations.gms:47` and `:35` respectively.)

**Interpretation**: Linear relationship where:
- Slope (b): Change in costs per unit productivity increase (USD17MER per tDM per (ton FM/animal/yr))
- Intercept (a): Base cost at zero productivity (USD17MER per tDM)

### Regression Coefficients

**Data Source**: GTAP 7 database (Narayanan et al. 2008) (`equations.gms:48-49`)

**Input Table** (`input.gms:51-54`):
```
f70_cost_regr(kap,cost_regr)  // cost_regr = {cost_regr_a, cost_regr_b}
```

**Product-Specific Slopes** (`preloop.gms:86`):
```
i70_cost_regr(i,kap,"cost_regr_b") = f70_cost_regr(kap,"cost_regr_b")
```
- **Ruminants (beef, milk)**: `b > 0` → costs rise with intensification
- **Non-ruminants (pork, poultry, eggs)**: `b = 0` → constant per-unit costs
- **Fish**: `b = 0` → constant per-unit costs

**Rationale** (`equations.gms:50-53`): Ruminant systems show strong productivity-cost relationship (intensive systems require more infrastructure, labor, veterinary care), while monogastric and fish systems have more uniform cost structures.

### Regional vs. Global Regression

**Configuration** (`input.gms:21-22`):
- `c70_fac_req_regr = "glo"`: Use global regression intercept (default)
- `c70_fac_req_regr = "reg"`: Calibrate intercept to regional historical costs

**Global Intercept** (`preloop.gms:82`):
```
i70_cost_regr(i,kli,"cost_regr_a") = f70_cost_regr(kli,"cost_regr_a")
```

**Regional Intercept** (`preloop.gms:83`):
Solve for intercept that makes regression match last historical year:
```
$if "%c70_fac_req_regr%" == "reg" i70_cost_regr(i,kli,"cost_regr_a") =
    sum(t_past$(ord(t_past) eq card(t_past)),
        (f70_hist_factor_costs_livst(t_past,i,kli) / f70_hist_prod_livst(t_past,i,kli,"dm"))
        - f70_cost_regr(kli,"cost_regr_b") * sum(sys_to_kli(sys,kli), i70_livestock_productivity(t_past,i,sys)));
```
The `sum(t_past$(ord(t_past) eq card(t_past)), ...)` wrapper is how "last historical year" is
expressed in the code — there is no `t_past_last` set in MAgPIE.

> ⚠️ **CORRECTED (R58, 2026-07-17)**: this block previously rendered the productivity term as
> `livestock_productivity(t_past_last,i,sys)` — an identifier that **exists nowhere in MAgPIE**
> (the real name is `i70_livestock_productivity`, `declarations.gms:35`) — and dropped the
> `sum(sys_to_kli(sys,kli), ...)` mapping sum, which left `sys` dangling as an uncontrolled set that
> would not compile as written. The doc renders the same construct correctly under §Core Equations →
> Livestock Labor Costs (`preloop.gms:88`), with both the `i70_` prefix and the mapping sum.
- Uses historical factor costs and production data (`input.gms:72-82`)
- Keeps slope from global regression, adjusts intercept to match regional baseline

**Historical Override** (`preloop.gms:90`):
If regional regression enabled, use actual historical values instead of regression for years
**strictly after 1990** up to and including the last historical year — i.e. the range is
`(1990, t_past_last]`, **not** `[1990, t_past_last]`:
```
$if "%c70_fac_req_regr%" == "reg" i70_fac_req_livst(t_all,i,kli)$(m_year(t_all) <= sum(t_past$(ord(t_past) eq card(t_past)), m_year(t_past))
                                                                 and m_year(t_all) > 1990) =
    (f70_hist_factor_costs_livst(t_all,i,kli) / f70_hist_prod_livst(t_all,i,kli,"dm"));
```

> ⚠️ **CORRECTED (R58, 2026-07-17)**: the range was stated as "years 1990-t_past_last". The guard is
> `m_year(t_all) > 1990` — **strictly greater** — so a `y1990` slice keeps its regression value and is
> not overridden. Doubly inert in practice: this path is gated behind the non-default
> `c70_fac_req_regr = "reg"` (default `glo`, `config/default.cfg:2206`), and no shipped `c_timesteps`
> option includes `y1990` in `t` (all start at `y1995`), so the misstated slice is one no equation
> reads.

---

## Pasture Management Factor

Module 70 calculates exogenous pasture management intensification factor `pm_past_mngmnt_factor(t,i)` that is passed to Module 14 (Yields) to scale pasture yields (`presolve.gms:23-70`).

**Interface**: `pm_past_mngmnt_factor(t,i)` defined in Module 70 declarations, used by Module 14 to adjust `vm_yld(j,"pasture",w)`.

### Cattle Stock Proxies

**Beef Cattle Stock** (`presolve.gms:32-33`):
```
p70_cattle_stock_proxy(t,i) =
    im_pop(t,i) * pm_kcal_pc_initial(t,i,"livst_rum")
    / i70_livestock_productivity(t,i,"sys_beef")
```
- `im_pop(t,i)`: Regional population
- `pm_kcal_pc_initial(t,i,"livst_rum")`: Initial per capita kcal demand for ruminant meat
- `i70_livestock_productivity(t,i,"sys_beef")`: Meat production per animal (ton FM/animal/yr)
- **Units**: mio. animals per yr

**Dairy Cattle Stock** (`presolve.gms:35-36`):
```
p70_milk_cow_proxy(t,i) =
    im_pop(t,i) * pm_kcal_pc_initial(t,i,"livst_milk")
    / i70_livestock_productivity(t,i,"sys_dairy")
```
- **Units**: mio. animals per yr

**Lower Bound** (`presolve.gms:38-42`):
Prevent unrealistic collapse of cattle stocks:
```
p70_cattle_stock_proxy(t,i) = max(p70_cattle_stock_proxy(t,i), 0.2 * p70_cattle_stock_proxy("y1995",i))
p70_milk_cow_proxy(t,i) = max(p70_milk_cow_proxy(t,i), 0.2 * p70_milk_cow_proxy("y1995",i))
```
Stocks cannot fall below 20% of 1995 levels.

### Per Capita Feed Demand Proxy

**Calculation** (`presolve.gms:44-47`):
```
p70_cattle_feed_pc_proxy(t,i,kli_rd) =
    pm_kcal_pc_initial(t,i,kli_rd)
    * im_feed_baskets(t,i,kli_rd,"pasture")
    / (fm_nutrition_attributes(t,kli_rd,"kcal") * 10^6)
```
- `kli_rd`: Ruminant products (livst_rum, livst_milk)
- **Purpose**: Weight beef vs. dairy contribution to cattle stock changes
- **Units**: tDM per capita per day

### Incremental Cattle Stock Change

**Calculation** (`presolve.gms:52-58`):
```
p70_incr_cattle(t,i) =
    [(p70_cattle_feed_pc_proxy(t,i,"livst_rum") + 1e-6)
        * (p70_cattle_stock_proxy(t,i) / p70_cattle_stock_proxy(t-1,i))
    + (p70_cattle_feed_pc_proxy(t,i,"livst_milk") + 1e-6)
        * (p70_milk_cow_proxy(t,i) / p70_milk_cow_proxy(t-1,i))]
    / sum(kli_rd, p70_cattle_feed_pc_proxy(t,i,kli_rd) + 1e-6)
```
- **Numerator**: Weighted sum of beef and dairy stock changes (weighted by per capita pasture feed demand)
- **Denominator**: Total per capita pasture feed demand (normalization)
- **Result**: Composite cattle stock change ratio (1 = no change, >1 = increase, <1 = decrease)
- **Initial timestep**: `p70_incr_cattle(t=1,i) = 1` (`presolve.gms:57`)

### Management Factor Calculation

**Fixed Period** (`presolve.gms:63-64`):
```
if (m_year(t) <= s70_past_mngmnt_factor_fix):
    pm_past_mngmnt_factor(t,i) = 1
```
- `s70_past_mngmnt_factor_fix`: Year until factor fixed to 1 (default: 2005) (`input.gms:26`)
- **Interpretation**: No pasture intensification before 2005

**Dynamic Period** (`presolve.gms:65-68`):
```
pm_past_mngmnt_factor(t,i) =
    [(s70_pyld_intercept + f70_pyld_slope_reg(i) * p70_incr_cattle(t,i)^(5/(m_year(t)-m_year(t-1))))
        ^((m_year(t)-m_year(t-1))/5)]
    * pm_past_mngmnt_factor(t-1,i)
```

**Linear Relationship Components**:
- `s70_pyld_intercept`: Global intercept (default: 0.24) (`input.gms:25`)
- `f70_pyld_slope_reg(i)`: Regional slope (`input.gms:65-70`)
- `p70_incr_cattle(t,i)`: Cattle stock change from previous timestep

**Time Scaling Logic**:
- Inner exponent `5/(m_year(t)-m_year(t-1))`: Annualize cattle stock change (assume 5-year base period)
- Outer exponent `(m_year(t)-m_year(t-1))/5`: Compound annualized rate over timestep length
- **Purpose**: Normalize to 5-year increments regardless of actual timestep length

**Cumulative Mechanism**:
```
pm_past_mngmnt_factor(t,i) = [factor_increment] * pm_past_mngmnt_factor(t-1,i)
```
Management factor accumulates over time (multiplicative path dependence).

**Interpretation** (`presolve.gms:60-62`):
Linear relationship links pasture management intensification to cattle stock changes:
- More cattle → higher pasture intensification (improved management, fertilization, reseeding)
- Fewer cattle → lower intensification (extensification)
- Regional slopes capture different intensification potentials

---

## Feed Intake vs. Feed Demand

Module 70 distinguishes between **feed intake** and **feed demand** (`equations.gms:31-42`):

### Feed Intake (`vm_feed_intake`)

**Definition**: Feed actually consumed by livestock, used for:
- Nutrient flow calculations (nitrogen, phosphorus, methane in other modules)
- Slaughter calculations (biomass incorporated in animal products)

**Equation**: `q70_feed_intake` (`equations.gms:39-42`)

**Control Parameter**: `s70_feed_intake_weight_balanceflow` (default: 1) (`input.gms:28`)

### Feed Demand (`vm_dem_feed`)

**Definition**: Feed required from production system, used for:
- Commodity balance constraints in Module 16 (Demand)
- Trade and production allocation

**Equation**: `q70_feed` (`equations.gms:17-20`)

**Always Includes**: Production × feed baskets + balance flows

### Why the Distinction?

**Balance Flow Propagation Control**:
- Balance flows correct for FAO inventory inconsistencies and scavenging
- Including balance flows in intake would propagate data inconsistencies to nutrient budgets
- Separating intake from demand allows flexible handling of balance flows

**Example**:
- If weight = 0: Intake excludes balance flows (pure feed basket calculation) → nutrient calculations unaffected by FAO corrections
- If weight = 1: Intake = demand (includes balance flows) → nutrient calculations account for all feed sources

**Default Behavior** (weight = 1): Feed intake equals feed demand, no distinction.

---

## Interface Variables

### Outputs to Other Modules

**1. Feed Demand** (`declarations.gms:11`):
```
vm_dem_feed(i,kap,kall)  // mio. tDM per yr
```
- **To Module 16 (Demand)**: Aggregated with food, material, seed, bioenergy demands (`module.gms:18`)
- **To Module 31 (Pasture) - INDIRECT**: pasture feed demand reaches M31 transitively (vm_dem_feed -> Module 16 demand balance -> Module 21 trade -> vm_prod_reg); M31 reads vm_prod/vm_land/vm_yld, NOT vm_dem_feed directly (`modules/31_past/endo_jun13/equations.gms:16-18`, q31_prod). Interface flow organized via Modules 16 and 21 (`module.gms:18-19`).
- **Dimensions**: Region × livestock products × all feed items

**2. Feed Intake** (`declarations.gms:18`):
```
vm_feed_intake(i,kap,kall)  // mio. tDM per yr
```
- **To Module 53 (Methane)**: Feed intake determines enteric fermentation emissions (`module.gms:20`)
- **To Module 55 (AWMS)**: Feed intake determines manure production (`module.gms:20`)

**3. Feed Balance Flows** (`declarations.gms:17`):
```
vm_feed_balanceflow(i,kap,kall)  // mio. tDM
```
- Used for FAO consistency and scavenging adjustments
- Contributes to `vm_dem_feed` via `q70_feed`
- **To Module 71 (Livestock Disaggregation)**: consumed by M71's **default** realization
  `foragebased_jul23` (`modules/71_disagg_lvst/foragebased_jul23/equations.gms`), and also by
  `foragebased_aug18`.
  > ⚠️ **CORRECTED (R58, 2026-07-17)**: this entry previously read "Used **internally** for FAO
  > consistency..." — an affirmative claim that no other module reads it. It is false: M71's default
  > realization consumes it. Note this variable is listed under *Outputs to Other Modules* while
  > being described as internal-only, so the doc contradicted its own section heading.

**3b. Feed Baskets** (`declarations.gms:36`):
```
im_feed_baskets(t,i,kli,kall)
```
- **To Module 71 (Livestock Disaggregation)**: consumed by the **default** realization
  `foragebased_jul23` (`modules/71_disagg_lvst/foragebased_jul23/equations.gms:24`) and by
  `foragebased_aug18` (`equations.gms:17,32`).
  > ⚠️ **ADDED (R58, 2026-07-17)**: this interface output was absent from this section entirely.
  > The M70→M71 blind spot spanned **two** identifiers, not one.

**4. Livestock Production Costs** (`declarations.gms:12-13`):
```
vm_cost_prod_livst(i,factors)  // mio. USD17MER per yr (factors = labor, capital)
vm_cost_prod_fish(i)          // mio. USD17MER per yr
```
- **To Module 11 (Costs)**: `vm_cost_prod_livst` and `vm_cost_prod_fish` enter `q11_cost_reg` directly (see module_11.md §3). Separately, Module 71 declares its own `vm_costs_additional_mon(i)` (1D — region only; declared at `modules/71_disagg_lvst/foragebased_jul23/declarations.gms:11` — the default realization) which is a penalty cost for additionally-transported monogastric `livst_egg`. The two `vm_cost_*` paths are independent — `vm_costs_additional_mon` is not an aggregator of M70 costs.

**5. Pasture Management Factor** (`declarations.gms:41`):
```
pm_past_mngmnt_factor(t,i)  // dimensionless (≥1)
```
- **To Module 14 (Yields)**: Scales pasture yields to account for exogenous intensification
  (`presolve.gms:23-26`). M14's default and only realization `managementcalib_aug19`
  (`config/default.cfg:354`) reads it at **two** sites:
  - `modules/14_yields/managementcalib_aug19/equations.gms:38` — inside `q14_yield_past` (NLP path)
  - `modules/14_yields/managementcalib_aug19/nl_fix.gms:11` — inside the `vm_yld.fx(j,"pasture",w)`
    fixing statement used to linearize the model (LP path)
  > ⚠️ **CORRECTED (R58, 2026-07-17)**: only `equations.gms:38` was cited. The `nl_fix` site is a
  > `.fx`-form read that a paren-only consumer grep misses. It matters because `nl_fix.gms` is what
  > runs when the model is fixed to linear behavior — anyone changing this parameter's domain would
  > break an LP-mode run while the NLP-mode path the doc points at still looks fine.

**6. Slaughter Feed Share** (`declarations.gms:34`):
```
im_slaughter_feed_share(t_all,i,kap,attributes)  // dimensionless
```
- **To Other Modules**: Share of feed incorporated in animal biomass (for mass balance calculations)

### Inputs from Other Modules

**1. Regional Production** (from Module 16 via Module 17):
```
vm_prod_reg(i,kap)  // mio. tDM per yr
```
- **From Module 17 (Production)**: Regional production target drives feed demand (`equations.gms:18-19`)

**2. Factor Cost Shares** (from Module 38):
```
pm_factor_cost_shares(t,i,factors)  // dimensionless
```
- **From Module 38 (Factor Costs)**: Split total factor costs into labor vs. capital components (`equations.gms:61-66`)

**3. Wage Scenario Parameters** (from Module 36):
```
pm_hourly_costs(t,i,"scenario")    // USD17MER per hour
pm_hourly_costs(t,i,"baseline")    // USD17MER per hour
pm_productivity_gain_from_wages(t,i)  // dimensionless
```
- **From Module 36 (Employment)**: Adjust labor costs for external wage scenarios (`equations.gms:62`)

**4. Initial Per Capita Food Demand** (from Module 15):
```
pm_kcal_pc_initial(t,i,kap)  // kcal per capita per day
```
- **From Module 15 (Food Demand)**: Used in cattle stock proxy calculations (`presolve.gms:32-36`)

**5. Population** (from drivers):
```
im_pop(t,i)  // mio. people
```
- **From Module 09 (Drivers)**: Used in cattle stock proxy and scenario region share calculations (`presolve.gms:32-37`)

**6. Nutrition Attributes** (from data):
```
fm_nutrition_attributes(t,kap,"kcal")  // kcal per ton
```
- Used in per capita feed proxy calculation (`presolve.gms:47`)

**7. Nutrient Attributes** (from data):
```
fm_attributes("nr",kall)  // nitrogen content
```
- Used in SCP substitution calculations (`preloop.gms:64-76`)

---

## Configuration Options

### Feed Scenario Selection

**Switch** (`input.gms:8`):
```
c70_feed_scen = "ssp2"
```
**Options**: ssp1, ssp2, ssp3, ssp4, ssp5, SDP, SDP_EI, SDP_MC, SDP_RC, constant

**Effect**: `preloop.gms:13-23` uses `c70_feed_scen` to select the `feed_scen70` slice of **three** input tables, not just the feed baskets — the historical period (≤ `sm_fix_SSP2`) always uses `"ssp2"` for all three; the future period uses whichever scenario `c70_feed_scen` selects, for all three, in the same loop:

1. `f70_feed_baskets` → `im_feed_baskets` — feed basket composition (tDM feed per tDM product)
2. `f70_livestock_productivity` → `i70_livestock_productivity` — productivity indicator (t FM per animal per yr)
3. `f70_slaughter_feed_share` → `im_slaughter_feed_share` — share of feed incorporated in animal biomass

**Downstream propagation beyond feed composition**: `i70_livestock_productivity` also feeds two paths that do not run through feed baskets at all:
- **Livestock factor costs**: `i70_livestock_productivity` → `i70_fac_req_livst` (`preloop.gms:88`) → `vm_cost_prod_livst` via `q70_cost_prod_liv_labor` / `q70_cost_prod_liv_capital` (`equations.gms:59-66`) — part of the objective function.
- **Module 14 pasture yields**: `i70_livestock_productivity` → `p70_cattle_stock_proxy` / `p70_milk_cow_proxy` (`presolve.gms:32,35`) → `p70_incr_cattle` (`presolve.gms:53`) → `pm_past_mngmnt_factor` (`presolve.gms:63-68`) → pasture yield scaling in `modules/14_yields/managementcalib_aug19/equations.gms:38` and `nl_fix.gms:11`.

A user who flips `c70_feed_scen` expecting only a feed-basket-composition change and then observes different livestock factor costs or Module 14 pasture yields would misattribute the cause without tracing this switch here.

### SCP Substitution Scenarios

> ⚠️ **CORRECTED (R58, 2026-07-17)**: `c70_cereal_scp_scen` (`input.gms:18`) and
> `c70_foddr_scp_scen` (`input.gms:19`) are **inert** — declared `$setglobal`s that are never
> expanded, never compared, and absent from `config/default.cfg`. Setting either one has **no
> effect**. They are NOT the SCP control surface; the `s70_*` scalars below are. See §SCP
> Substitution → Configuration for the search evidence.

**Substitution Levels** (`input.gms:32-33`) — the real magnitude control:
```
s70_cereal_scp_substitution = 0  // 0 = no substitution, 1 = complete substitution
s70_foddr_scp_substitution = 0
```

**Functional Form** (`input.gms:29`):
```
s70_subst_functional_form = 1  // 1 = linear, 2 = sigmoid
```

**Transition Period** (`input.gms:30-31`):
```
s70_feed_substitution_start = 2025
s70_feed_substitution_target = 2050
```

### Factor Cost Regression

**Regression Type** (`input.gms:21-22`):
```
c70_fac_req_regr = "glo"
```
**Options**:
- "glo": Use global regression intercept from GTAP
- "reg": Calibrate regional intercept to historical costs, use actual historical values for past

### Pasture Management

**Fixed Period** (`input.gms:26`):
```
s70_past_mngmnt_factor_fix = 2005
```
**Effect**: Pasture management factor = 1 (no intensification) until this year.

**Intercept** (`input.gms:25`):
```
s70_pyld_intercept = 0.24
```
**Effect**: Global intercept in linear relationship between pasture management and cattle stock change.

### Scavenging

**Scavenging Ratio** (`input.gms:27`):
```
s70_scavenging_ratio = 0.385
```
**Effect**: Threshold for activating endogenous scavenging adjustment (38.5% of pasture feed demand).

**Balance Flow Weight** (`input.gms:28`):
```
s70_feed_intake_weight_balanceflow = 1
```
**Effect**:
- 0 = Feed intake excludes balance flows
- 1 = Feed intake includes balance flows (equals feed demand)
- 0-1 = Weighted blend

### Country Selection for Feed Scenarios

**Default** (`input.gms:87-112`):
```
scen_countries70(iso) = all 249 countries
```
**Effect**: All countries affected by selected feed scenario. Can be restricted to subset of countries.

**Regional Share** (`preloop.gms:37`):
Calculated as population-weighted share of affected countries:
```
p70_feedscen_region_shr(t,i) =
    sum(iso in region i and in scen_countries70, im_pop_iso(t,iso))
    / sum(iso in region i, im_pop_iso(t,iso))
```

---

## Key Assumptions and Limitations

### 1. Exogenous Feed Intensification

**Limitation** (`realization.gms:77-80`): Intensification of livestock production and changes in livestock feeding are modeled exogenously via scenario-based feed baskets and productivity trajectories.

**Implication**: The livestock sector does NOT endogenously respond to:
- Food demand shocks (elasticity of feed conversion to prices)
- Climate shocks (adaptation of feed composition to yield changes)
- GHG policies (shift to less emission-intensive feed or systems)
- Feed price signals (substitution between feed types based on relative costs)

**Exception**: Scavenging adjustment provides limited endogenous response for pasture balance flows in regions with historical scavenging patterns (`equations.gms:25-29`).

### 2. System-Level Homogeneity

**Assumption**: All animals within a production system (e.g., sys_beef) in a region have identical feed conversion and feed baskets, determined by average livestock productivity.

**Implication**: Does NOT model:
- Farm-level heterogeneity in feeding practices
- Within-region variation in intensification levels
- Individual animal characteristics (age, breed, health status)

### 3. Feed Basket Preprocessing

**Methodology** (`realization.gms:18-35`): Feed baskets derived from regression models fitted to historical data outside GAMS.

**Limitations**:
- Regression relationships assumed stable over projection period (no structural breaks)
- Does NOT dynamically update regressions with new data
- Extrapolation beyond historical productivity range may be unreliable
- Climate zone proxy for feed composition may not capture all geographical determinants

### 4. Factor Cost Regression

**Ruminant Cost Assumption** (`equations.gms:48-53`): Linear relationship between per-unit factor costs and livestock productivity for ruminants, based on GTAP 7 snapshot.

**Limitations**:
- Assumes same slope across all future years (no technological change in cost structure)
- Non-ruminant and fish costs fixed per unit (no productivity-cost relationship)
- Regional regression option uses single historical year for calibration (no trend fitting)

### 5. Pasture Management Factor

**Calculation** (`presolve.gms:60-68`): Exogenous relationship between cattle stock changes and pasture yield intensification.

**Limitations**:
- Linear relationship parameters (intercept, regional slopes) are static (no learning or saturation effects)
- Driven by food demand proxies, not actual optimized cattle stocks from model
- Does NOT account for:
  - Pasture quality constraints (biophysical limits to intensification)
  - Cost-benefit optimization of pasture management investments
  - Climate change impacts on pasture management effectiveness
  - Policy incentives/disincentives for intensification

### 6. Balance Flow Handling

**Approach** (`equations.gms:10-15`): Balance flows fix discrepancies between model estimates and FAO statistics.

**Limitations**:
- Assumes historical FAO-model discrepancies persist into future (structural assumption)
- Scavenging adjustment applies uniform ratio (38.5%) regardless of regional context beyond flag threshold
- Non-pasture balance flows completely fixed (no endogenous adjustment)
- May propagate FAO data errors if statistics are incorrect

### 7. SCP Substitution

**Implementation** (`preloop.gms:58-78`): Nitrogen-content-based substitution of cereals/fodder with SCP.

**Limitations**:
- Assumes perfect digestibility equivalence (1 kg N from SCP = 1 kg N from cereals/fodder)
- Does NOT model:
  - Animal acceptance of SCP (palatability, adaptation periods)
  - Nutritional balance beyond nitrogen (amino acid profiles, energy density, fiber)
  - Production costs of SCP (exogenous to Module 70)
  - Infrastructure requirements for SCP integration
  - Regional suitability for SCP production

### 8. Fish Production

**Treatment**: Fish handled as separate product with simple linear cost function, no feed basket detail.

**Limitations**:
- Feed composition for fish NOT modeled (lumped into single cost coefficient)
- No distinction between aquaculture (feed-dependent) and capture fisheries (not feed-dependent)
- Factor costs independent of productivity (unlike ruminants)

### 9. Geographic Aggregation

**Spatial Resolution**: All calculations at MAgPIE regional level (typically 10-15 regions globally).

**Limitations**:
- Does NOT capture within-region variation in:
  - Livestock system prevalence (some areas more intensive than others)
  - Feed availability and costs (distance to markets, local feed production)
  - Climate impacts on feed quality (regional averages may miss local extremes)

### 10. Temporal Dynamics

**Timestep Structure**: Feed baskets and productivity change between timesteps, applied instantaneously.

**Limitations**:
- No intertemporal smoothing (herd dynamics, capital stock turnover, farmer learning)
- Livestock stocks proxies used for pasture management are snapshots, not tracked variables
- Does NOT model:
  - Age structure of livestock herds
  - Breeding cycles and replacement rates
  - Capital investment in livestock infrastructure

---

## Data Sources and References

### Primary Methodology

**Weindl et al. (2017)**:
- Weindl, I., Lotze-Campen, H., Popp, A., et al. (2017). "Livestock in a changing climate: production system transitions as an adaptation strategy for agriculture." *Environmental Research Letters*, 12(9), 094021. (`realization.gms:9`)
- Weindl, I., Lotze-Campen, H., Popp, A., et al. (2017). "Livestock production and the water challenge of future food supply: Implications of agricultural management and dietary choices." *Global Environmental Change*, 47, 121-132. (`realization.gms:10`)

**Wirsenius (2000)**:
- Wirsenius, S. (2000). "Human Use of Land and Organic Materials: Modeling the Turnover of Biomass in the Global Food System." PhD thesis, Chalmers University of Technology, Göteborg, Sweden. (`realization.gms:20`)
- Source of bio-energetic equations for feed energy requirements (maintenance, growth, lactation, reproduction, activity, temperature) (`realization.gms:24-29`)

### Factor Cost Data

**GTAP 7 Database**:
- Narayanan, B., & Walmsley, T. L. (Eds.). (2008). "Global Trade, Assistance, and Production: The GTAP 7 Data Base." Center for Global Trade Analysis, Purdue University. (`equations.gms:48`)
- Source of regression coefficients for factor requirements (`input.gms:51-54`)

### Input Data Files

**Feed Baskets** (`input.gms:36-39`):
```
f70_feed_baskets.cs3  // (t_all, i, kap, kall, feed_scen70)
```
Pre-calculated feed requirement per unit livestock product output for each scenario.

**Balance Flows** (`input.gms:41-44`):
```
f70_feed_balanceflow.cs3  // (t_all, i, kap, kall)
```
Historical difference between FAO-reported feed use and model estimates.

**Livestock Productivity** (`input.gms:46-49`):
```
f70_livestock_productivity.cs3  // (t_all, i, sys, feed_scen70)
```
Annual production per animal for each production system and scenario.

**Factor Cost Regression** (`input.gms:51-54`):
```
f70_capit_liv_regr.csv  // (kap, cost_regr)
```
Regression coefficients (slope, intercept) from GTAP analysis.

**Slaughter Feed Share** (`input.gms:57-62`):
```
f70_slaughter_feed_share.cs4  // (t_all, i, kap, attributes, feed_scen70)
```
Share of feed incorporated in animal biomass.

**Pasture Yield Slope** (`input.gms:65-70`):
```
f70_pyld_slope_reg.cs4  // (i)
```
Regional slope for linear relationship in pasture management factor calculation.

**Historical Factor Costs** (`input.gms:72-76`):
```
f70_hist_factor_costs_livst.cs3  // (t_all, i, kli)
```
Used for regional regression calibration if `c70_fac_req_regr = "reg"`.

**Historical Production** (`input.gms:78-82`):
```
f70_hist_prod_livst.cs3  // (t_all, i, kli, attributes)
```
Used for regional regression calibration.

---

## Computational Notes

### Variable Scaling

**Cost Variables** (`scaling.gms:9-10`):
```
vm_cost_prod_livst.scale(i,factors) = 1e4
vm_cost_prod_fish.scale(i) = 1e5
```
Scale factors (10,000 for livestock factor costs, 100,000 for fish) improve solver numerics for the cost equations. (Identical in fbask_jan16 and fbask_jan16_sticky.)

### Initial Values

**Pasture Feed Demand** (`preloop.gms:10`):
```
pc70_dem_feed_pasture(i,kli_rum) = 0.001
```
Small positive initial value prevents division by zero in scavenging flag calculation (`presolve.gms:17`).

**Livestock Productivity** (`preloop.gms:26`):
```
i70_livestock_productivity(t_all,i,sys)$(i70_livestock_productivity(t_all,i,sys)=0) = 0.02;
```
Substitutes 0.02 ton FM/animal/yr **only where the value is exactly zero**, to prevent division by
zero in the cattle stock proxies (`presolve.gms:32-36`). The code comment on the preceding line
(`preloop.gms:25`) confirms the narrow intent: "set default livestock productivity to avoid division
of zero in presolve.gms".

> ⚠️ **CORRECTED (R58, 2026-07-17)**: this was rendered as
> `max(i70_livestock_productivity(t,i,sys), 0.02)` and described as a "minimum productivity".
> **It is not a floor.** `$(x = 0) = 0.02` substitutes at exact zero only; a productivity of 0.005
> survives the code untouched but would be lifted to 0.02 under the `max()` reading. Consequence: a
> very small but nonzero `i70_livestock_productivity` still produces an enormous
> `p70_cattle_stock_proxy`, and the 20%-of-1995 bound at `presolve.gms:41-42` is a *lower* bound, so
> it does not catch the blow-up. A reader debugging an implausible cattle-stock proxy would wrongly
> eliminate this as the cause.
>
> The doc's `max()` house idiom is legitimate where the code really is a floor — e.g.
> `presolve.gms:41-42` (`p70_cattle_stock_proxy(t,i)$(... < 0.2*...) = 0.2*...`), rendered as `max(...)`
> under §Pasture Management Factor → Lower Bound, which is exactly equivalent. The rule does not
> extend to `x$(x = 0) = c`.

### Conditional Statements

**Scavenging Flag** (`presolve.gms:14-20`):
Flag calculation only executed in the **last historical timestep** (`t = y2015` under the default
config), then frozen — the outer guard `sum(sameas(t_past,t),1) = 1` restricts it to timesteps in
`t_past`, so it never fires in a future timestep. The intent is to avoid overwriting in subsequent
timesteps. Full guard analysis: §Feed Balance Flows → Scavenging Flag Activation.

**Pasture Management** (`presolve.gms:63-68`):
Conditional logic ensures factor = 1 during fixed period, dynamic calculation thereafter.

### Postsolve Updates

**Pasture Feed Demand Tracking** (`postsolve.gms:9`):
```
pc70_dem_feed_pasture(i,kli_rum) = max(vm_dem_feed.l(i,kli_rum,"pasture"), 0.001)
```
Updates parameter with current solution for use in next timestep's scavenging flag calculation. Maximum ensures nonzero denominator.

---

## Module Flows and Interactions

### Execution Sequence (Typical Timestep)

**1. Preloop** (once before optimization loop):
- Select feed baskets based on scenario (`preloop.gms:13-23`)
- Apply SCP substitution to feed baskets (`preloop.gms:58-78`)
- Calculate factor cost regression coefficients (`preloop.gms:82-90`)

**2. Presolve** (before each solve):
- Fix balance flows for non-pasture items (`presolve.gms:9`)
- Calculate scavenging flag if in transition timestep (`presolve.gms:14-20`)
- Calculate cattle stock proxies from food demand (`presolve.gms:32-42`)
- Calculate pasture management factor (`presolve.gms:63-68`)

**3. Equations** (solved simultaneously):
- `q70_feed_intake_pre`: Calculate baseline feed intake (`equations.gms:35-37`)
- `q70_feed_intake`: Adjust intake with balance flow weight (`equations.gms:39-42`)
- `q70_feed`: Demand constraint (≥ production × baskets + balance flows) (`equations.gms:17-20`)
- `q70_feed_balanceflow`: Scavenging adjustment for ruminant pasture (`equations.gms:25-29`)
- `q70_cost_prod_liv_labor`: Labor costs with wage scaling (`equations.gms:59-62`)
- `q70_cost_prod_liv_capital`: Capital costs (`equations.gms:64-66`); in `fbask_jan16_sticky`: investment-based capital costs (`fbask_jan16_sticky/equations.gms`)
- `q70_cost_prod_fish`: Fish production costs (`equations.gms:68-70`)
- `q70_investment` (`fbask_jan16_sticky` only): Investment to cover capital requirements (`fbask_jan16_sticky/equations.gms`)

**4. Postsolve** (after solve):
- Update pasture feed demand parameter for next timestep (`postsolve.gms:9`)

### Critical Module Dependencies

**Upstream Dependencies** (Module 70 requires):
- **Module 09 (Drivers)**: Population for cattle stock proxies, scenario region shares
- **Module 15 (Food Demand)**: Initial per capita kcal demands for cattle stock proxies
- **Module 17 (Production)**: Regional production (`vm_prod_reg`) to calculate feed demand
- **Module 36 (Employment)**: Wage scenario parameters for labor cost scaling
- **Module 38 (Factor Costs)**: Factor cost shares (labor/capital split)

**Downstream Dependencies** (Other modules require Module 70):
- **Module 11 (Costs)**: Livestock and fish production costs added to objective function
- **Module 14 (Yields)**: Pasture management factor scales pasture yields
- **Module 16 (Demand)**: Feed demand aggregated with food/material/bioenergy demands
- **Module 31 (Pasture) - INDIRECT**: pasture feed demand reaches M31 transitively via Modules 16 and 21 (vm_dem_feed -> M16 demand balance -> M21 trade -> vm_prod_reg); M31 reads vm_prod/vm_land/vm_yld, not vm_dem_feed directly
- **Module 53 (Methane)**: Feed intake determines enteric fermentation emissions
- **Module 55 (AWMS)**: Feed intake determines manure production

### Circular Dependencies

**Potential Circular Dependency**: Module 70 (feed demand) → Module 16 (demand aggregation) → Module 21 (trade) → Module 17 (production) → Module 70 (feed demand)

**Resolution**: `vm_prod_reg(i,kap)` is **endogenous**, not exogenous — it is a decision variable declared at `modules/17_production/flexreg_apr16/declarations.gms:10` and set by `q17_prod_reg` (`vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k));`, `equations.gms:11`) within the same solve as `q70_feed`, `q16_supply_*`, and `q21_trade_glo`. It is never `.fx`-ed anywhere in the model — an attribute-form grep (`vm_prod_reg.`) across `modules/` and `core/` finds only `.lo` bounds set in `modules/71_disagg_lvst/foragebased_jul23/preloop.gms:17` (and the prior `foragebased_aug18` realization), plus postsolve output writes. The inequality (`=g=`) in `q70_feed` (`equations.gms:17-20`) lets feed demand exceed the production × feed-basket minimum without forcing equality, so the solver finds a joint equilibrium across `q70_feed`, `q16_supply_*`, `q21_trade_glo`, and `q17_prod_reg` **simultaneously within one timestep** — there is no presolve fixing at this seam. Contrast this with the genuinely *lagged* M70→M14 `pm_past_mngmnt_factor` channel (`presolve.gms:63-68`), which IS a presolve-computed parameter, not a decision variable.

---

## Interpretation and Use Cases

### Feed Demand Analysis

**Query**: "How much pasture is needed for beef production in region X in 2050?"

**Approach**:
1. Check `vm_prod_reg(X,"livst_rum")` in 2050 (from Module 17)
2. Read `im_feed_baskets(2050,X,"livst_rum","pasture")` (tDM feed per tDM product)
3. Calculate: Pasture demand = production × feed basket + balance flow
4. Check `vm_feed_balanceflow(X,"livst_rum","pasture")` for scavenging adjustment

**Example** (illustrative numbers):
- Production: 10 mio. tDM beef
- Feed basket: 15 tDM pasture per tDM beef
- Balance flow: -20 mio. tDM (scavenging reduces net demand)
- **Pasture demand**: 10 × 15 + (-20) = 130 mio. tDM

### Intensification Scenario Analysis

**Query**: "How does livestock intensification (SSP1 vs. SSP3) affect feed demand?"

**Approach**:
1. Run scenario with `c70_feed_scen = "ssp1"` (high intensification)
2. Run scenario with `c70_feed_scen = "ssp3"` (low intensification)
3. Compare `vm_dem_feed(i,kap,"pasture")` across scenarios

**Expected Pattern**:
- SSP1: Higher productivity → lower feed conversion → less total feed per unit product
- SSP3: Lower productivity → higher feed conversion → more total feed per unit product
- SSP1: Higher concentrate share (cereals, SCP) → lower pasture share
- SSP3: Higher roughage share (pasture, residues) → higher pasture share

### SCP Substitution Impact

**Query**: "What is the land-sparing effect of replacing 50% of cereal feed with SCP by 2050?"

**Approach**:
1. Configure: `s70_cereal_scp_substitution = 0.5` (magnitude), `s70_feed_substitution_start = 2020`
   and `s70_feed_substitution_target = 2050` (window), `s70_subst_functional_form = 1` (linear).
   > ⚠️ **CORRECTED (R58, 2026-07-17)**: this step previously read
   > `c70_cereal_scp_scen = "lin_50pc_20_50"`. That switch is **inert** and selects nothing — the
   > shape, target and window come only from the `s70_*` scalars, so the `_20_50` in the scenario
   > name buys nothing. Setting the switch alone yields **zero substitution** and a plausible-looking
   > run. Note also that `s70_feed_substitution_start` defaults to **2025**, not 2020, so the window
   > must be set explicitly to match the query.
2. Run model and compare cereal feed demand with and without SCP scenario
3. Calculate: Cereal feed reduction = baseline - SCP scenario
4. Trace to cropland via Module 30 (Croparea)

**Mechanism**:
- SCP substitution reduces `im_feed_baskets(t,i,kap,kcer70)` by 50% in 2050 (`preloop.gms:66-67`)
- Increases `im_feed_baskets(t,i,kap,"scp")` by N-equivalent amount (`preloop.gms:63-65`)
- Lower cereal feed demand → lower cereal production → less cropland for feed crops

### Factor Cost Sensitivity

**Query**: "How do livestock production costs change with intensification in region X?"

**Approach**:
1. Extract `i70_livestock_productivity(t,X,sys)` over time
2. Extract `i70_fac_req_livst(t,X,kli)` = `b * productivity + a`
3. Calculate total costs: `vm_cost_prod_livst(X,"labor") + vm_cost_prod_livst(X,"capital")`
4. Decompose: intensive margin (higher per-unit costs) vs. extensive margin (more production)

**Expected Pattern** (for ruminants):
- Productivity doubles → per-unit costs increase linearly (slope `b`)
- Total costs = per-unit costs × production volume
- Net effect depends on production trajectory and regression slope

### Pasture Management Pathways

**Query**: "How does pasture yield intensification compensate for livestock demand growth?"

**Approach**:
1. Extract cattle stock proxies: `p70_cattle_stock_proxy(t,i)`, `p70_milk_cow_proxy(t,i)`
2. Extract pasture management factor: `pm_past_mngmnt_factor(t,i)`
3. Compare scenarios with different food demand trajectories (e.g., SSP1 low demand vs. SSP3 high demand)
4. Trace to pasture yields in Module 14: `vm_yld(j,"pasture",w)` scaled by `pm_past_mngmnt_factor(t,i)`

**Expected Pattern**:
- High demand growth → more cattle → higher `p70_incr_cattle(t,i)` → higher `pm_past_mngmnt_factor(t,i)` → higher pasture yields → less pasture area expansion
- Low demand growth → fewer cattle → lower `p70_incr_cattle(t,i)` → lower `pm_past_mngmnt_factor(t,i)` → extensification → potentially more pasture area but lower total production

---

## Related Modules

**Module 16 (Demand)**: Aggregates feed demand with food/material/seed/bioenergy demands; passes to trade module
**Module 17 (Production)**: Provides regional production targets (`vm_prod_reg`) that drive feed demand
**Module 31 (Pasture)**: Pasture area reached via Modules 16+21 (INDIRECT: vm_dem_feed -> M16 demand balance -> M21 trade -> vm_prod_reg -> M31 q31_prod); M31 does not read vm_dem_feed directly
**Module 14 (Yields)**: Pasture yields `vm_yld(j,"pasture",w)` scaled by `pm_past_mngmnt_factor` from Module 70
**Module 11 (Costs)**: Livestock and fish production costs added to objective function
**Module 38 (Factor Costs)**: Provides factor cost shares for labor/capital split
**Module 36 (Employment)**: Provides wage scenario parameters for labor cost scaling
**Module 53 (Methane)**: Enteric fermentation emissions based on feed intake
**Module 55 (AWMS)**: Manure production based on feed intake

---

## Summary Statistics

**Module Complexity**:
- 7 equations
- **8 interface identifiers (outputs)** — `vm_dem_feed`, `vm_cost_prod_livst`, `vm_cost_prod_fish`,
  `vm_feed_balanceflow`, `vm_feed_intake`, `im_slaughter_feed_share`, `im_feed_baskets`,
  `pm_past_mngmnt_factor`. Of these, **5 are GAMS variables** (`vm_`); the other 3 are parameters.
- **7 interface identifiers (inputs from other modules)** — `vm_prod_reg` (M17),
  `pm_factor_cost_shares` (M38), `pm_hourly_costs` + `pm_productivity_gain_from_wages` (M36),
  `pm_kcal_pc_initial` (M15), `im_pop` + `im_pop_iso` (M09). Plus core data `fm_attributes`,
  `fm_nutrition_attributes`, `sm_fix_SSP2` (not module interfaces).
- 5 livestock production systems
- 10 feed scenarios (SSPs, SDPs, constant)
- 17 SCP substitution scenarios (set `fadeoutscen70`, `sets.gms:41-45` — declared but never
  referenced by any code; see §SCP Substitution)
- 2 factor cost regression modes (global/regional)
- **625 lines of code** (fbask_jan16 realization, raw `wc -l` over its 9 `.gms` files; 706 for
  `fbask_jan16_sticky`)

> ⚠️ **CORRECTED (R58, 2026-07-17)**: the counts read "4 interface variables (outputs) / 6 interface
> variables (inputs)". Both were tallies of a *wrong enumeration* rather than fabrications — `4` was
> the 5 `vm_` outputs minus `vm_feed_balanceflow` (which the doc wrongly called internal-only), and
> `6` was the doc's own 8 input identifiers minus the 2 core `fm_` ones, an enumeration that itself
> omitted `im_pop_iso`. The counts above are re-derived from the corrected §Interface Variables
> section under an explicit rule: an *interface identifier* carries a `vm_`/`pm_`/`im_` prefix; it is
> an **output** if declared in `fbask_jan16/declarations.gms` and an **input** if read here but
> declared elsewhere; core-owned `fm_`/`sm_` are data, not module interfaces. Edge case worth naming:
> `fm_feed_balanceflow` carries an `fm_` prefix but is declared by M70 itself
> (`fbask_jan16/input.gms:41`), so it is neither an input from another module nor counted above.

> ⚠️ **CORRECTED (R58, 2026-07-17)**: "~450 lines of code" (stated in 3 places) was **wrong when
> written, not stale**. At this doc's own Last-Verified date (2026-03-06, MAgPIE `ce6e1a89a`) the
> realization was already **624** lines; it is **625** at `0d7ebeb90` — a one-line delta across the
> whole period, so nothing drifted and re-deriving on sync would never have caught it. Note **466**
> is a defensible logic-only count (625 minus `input.gms` 113 and `sets.gms` 46), within 3.4% of
> "~450" — so the original figure may have intended a logic-only rule it never stated. The counts
> here use raw `wc -l` and say so.

**Key Parameters**:
- Feed baskets: Scenario-dependent, region × product × feed item (thousands of values)
- Livestock productivity: Scenario-dependent, region × system (hundreds of values)
- Factor cost regression: 2 coefficients per product (slope, intercept)
- Pasture management: 1 global intercept + regional slopes

**Computational Load**:
- Low equation count (7), but large data tables (feed baskets)
- Preloop preprocessing intensive (SCP substitution loops over all time/region/product/feed combinations)
- Scavenging flag calculation adds conditional logic in presolve
- Pasture management factor calculation nested exponentiation in presolve

---

## File Reference

**Core Files**:
- `modules/70_livestock/module.gms` - Module documentation
- `modules/70_livestock/fbask_jan16/realization.gms` - Realization documentation
- `modules/70_livestock/fbask_jan16/sets.gms` - Livestock systems, scenarios, mappings
- `modules/70_livestock/fbask_jan16/declarations.gms` - Variables, equations, parameters
- `modules/70_livestock/fbask_jan16/input.gms` - Configuration switches, input data
- `modules/70_livestock/fbask_jan16/equations.gms` - 7 equation definitions
- `modules/70_livestock/fbask_jan16/preloop.gms` - Feed basket selection, SCP substitution, regression setup
- `modules/70_livestock/fbask_jan16/presolve.gms` - Pasture management factor, scavenging flag
- `modules/70_livestock/fbask_jan16/postsolve.gms` - Pasture feed demand update
- `modules/70_livestock/fbask_jan16/scaling.gms` - Variable scaling

**Input Data Directory**:
- `modules/70_livestock/fbask_jan16/input/` - All input data files (.cs3, .cs4, .csv)

---

**Verification** (scope-corrected R58, 2026-07-17):
- **Equations — strong**: all 7 default formulas and both `fbask_jan16_sticky` formulas verified exact
  against source; 33 of 34 `file:line` citations resolve to the right content (the exception,
  `preloop.gms:26`, is corrected above).
- **Interfaces — was the weak dimension, now repaired**: R58 found the consumer/producer sets wrong in
  four places — `vm_feed_balanceflow` documented as internal-only (M71's default consumes it),
  `im_feed_baskets` missing from §Outputs entirely, M36 missing from the `vm_cost_prod_livst` consumer
  set, `pm_past_mngmnt_factor`'s `nl_fix.gms:11` site uncited, and the §Participates In upstream set
  inverted. All are corrected above.

> ⚠️ **CORRECTED (R58, 2026-07-17)**: this footer previously asserted "All interface variables
> cross-referenced with Phase 2 dependency documentation. **Zero errors detected.**", and the header
> read "**Status**: Fully Verified". Both were falsified by R58. The failure is worth naming because it
> is systematic, not incidental: the footer was **loudest about the exact dimension that was weakest**
> (interfaces), so a reader triaging what to re-check would have deprioritized the section that most
> needed it. A clean-bill claim embedded in the artifact it certifies is not falsifiable by its own
> reader — treat any such claim in these docs as a prompt to re-derive, not as evidence.
>
> The doc's consumer analysis appears to have been **hypothesis-driven** (checking edges it suspected)
> rather than **sweep-driven** (enumerating every reader of each declared identifier). That explains the
> pattern: it carefully verified a *non*-edge (M31, correctly hedged as INDIRECT in three places) while
> missing two real ones. Interface claims here should be re-derived by grepping each declared identifier
> repo-wide in **both** `name(` and `name.` forms.

**MAgPIE Version**: 4.x series
**Lines Documented**: 625 (fbask_jan16 realization, raw `wc -l`)
---

## Participates In

### Conservation Laws

**Food Balance** (livestock products component)
- **Role**: Calculates livestock production (meat, dairy, eggs) based on feed availability
- **Indirect**: Affects food supply side of food balance
- **Details**: `cross_module/nitrogen_food_balance.md`

**Not in** land, water, carbon balance directly (though affects them via feed demand)

### Dependency Chains

**Centrality**: HIGH (Rank #6 - livestock production hub)
**Hub Type**: Livestock Production & Feed Demand Calculator
**Provides to**: 7 modules (production, costs, emissions, manure)
**Depends on**: Modules 09 (drivers), 15 (food demand), 17 (production), 36 (employment), 38 (factor costs)

> ⚠️ **CORRECTED (R58, 2026-07-17)**: this line read "Modules 14 (yields), 17 (production), 70 (self -
> feed baskets)" — wrong in every element. **M14 is not upstream of M70**: across all 9 `.gms` files of
> `fbask_jan16` there is no M14 identifier of any kind (no `vm_yld`, no `i14_*`, no `f14_*`, no `q14_*`;
> verified against a positive control — `vm_prod_reg` returns 6 hits from the same search). The edge runs
> the **other way**: M70 *produces* `pm_past_mngmnt_factor` (`presolve.gms:63-68`), which M14 consumes
> (`modules/14_yields/managementcalib_aug19/equations.gms:38` and `nl_fix.gms:11`). "70 (self)" is not a
> module dependency at all. And four real upstream providers (09, 15, 36, 38) were dropped — all four are
> listed correctly in §Critical Module Dependencies above, so the doc contradicted itself. The corrected
> set matches that section.
>
> ⚠️ This block cites `core_docs/Module_Dependencies.md` for details. That file is under
> human-adjudication hold and was **not** touched in R58 — if it carries the same inverted edge, it needs
> the same fix; **this file is the corrected one**.

**Details**: `core_docs/Module_Dependencies.md`

### Circular Dependencies

**Pasture-Yield-Livestock Cycle** (M70 → M14 → M31 → M17 → M70):
**70 (livestock)** → 14 (yields) → 31 (pasture) → 17 (production) → **70**

Each leg verified at `0d7ebeb90`:
- M70 → M14: `pm_past_mngmnt_factor` (`presolve.gms:63-68`) read by `q14_yield_past`
  (`modules/14_yields/managementcalib_aug19/equations.gms:38`), scaling `vm_yld`
- M14 → M31: `q31_prod` reads `vm_yld` — `vm_prod(j2,"pasture") =l= vm_land(j2,"past") * vm_yld(j2,"pasture","rainfed")`
  (`modules/31_past/endo_jun13/equations.gms:16-18`)
- M31 → M17: `q17_prod_reg` aggregates — `vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k))`
  (`modules/17_production/flexreg_apr16/equations.gms:10-11`)
- M17 → M70: `q70_feed` reads `vm_prod_reg` (`equations.gms:18`)

> ⚠️ **CORRECTED (R58, 2026-07-17)**: this cycle read "Module 17 (production) → 14 (yields) →
> **70 (livestock)** → 17", which contains the same reversed 14→70 edge as the "Depends on" line above
> and therefore **does not close as drawn** (M14 sends nothing to M70). The old "Resolution: Feed
> conversion efficiencies and feed baskets resolved simultaneously" described a mechanism for an edge
> that does not exist — feed baskets are exogenous (`preloop.gms:13-23`) and are not resolved with M14.

**Resolution**: The cycle is **not** simultaneous — it is broken at the M70 → M14 leg. Three of the
four legs (M14 → M31 → M17 → M70) are equations solved together, but `pm_past_mngmnt_factor` is a
**parameter**, not a variable (`declarations.gms:41`, declared under `parameters`). It is computed in
M70's presolve *before* the solve, from exogenous drivers and lagged proxies — `im_pop` and
`pm_kcal_pc_initial` feed the cattle stock proxies (`presolve.gms:32-36`), and `p70_incr_cattle`
compares against `t-1` (`presolve.gms:52-58`). None of its inputs is a solution variable of the
current solve, so it enters as a constant. The feedback from livestock to pasture yields is therefore
**lagged across timesteps**, not resolved within one.

**A second cycle the doc did not record — M70 ↔ M36**:
M70 → M36: `vm_cost_prod_livst(i2,"labor")` read by `q36_employment`
(`modules/36_employment/exo_may22/equations.gms:24`). M36 → M70: `pm_hourly_costs` and
`pm_productivity_gain_from_wages` read by `q70_cost_prod_liv_labor` (`equations.gms:59-62`). Both
realizations involved are defaults and M36's `exo_may22` is its sole realization, so this cycle is
unconditionally live.

**Details**: `cross_module/circular_dependency_resolution.md`

### Modification Safety

**Risk Level**: ⚠️ **MEDIUM-HIGH RISK** (Hub module - see `core_docs/Module_Dependencies.md` for dependency details)
**Testing**: Verify feed demand reasonable, check livestock production feasible

---

**Module 70 Status**: ✅ COMPLETE

---

**Last Verified**: 2026-07-17 (R58 adversarial audit + refutation pass; 11 defects corrected)
**Previously**: 2026-03-06 (sticky realization added, 8/8 equations documented — i.e. all 8 of the
newly-added `fbask_jan16_sticky` equations; the default realization has 7, see header)
**Verified Against**: `../modules/70_livestock/{fbask_jan16,fbask_jan16_sticky}/*.gms` @ develop `0d7ebeb90`
**Verification Method**: Equations cross-referenced with source code; R58 additionally swept each
declared interface identifier repo-wide in both `name(` and `name.` forms, and resolved config
switches against `config/default.cfg` rather than the `input.gms` literal alone
**Changes Since Last Verification**: MAgPIE code effectively unchanged (`fbask_jan16` went 624 → 625
lines between `ce6e1a89a` and `0d7ebeb90`, a one-line delta in `scaling.gms`). The R58 corrections are
doc defects, not code drift.
