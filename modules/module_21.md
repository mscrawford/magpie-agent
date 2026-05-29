# Module 21: Trade - Complete Documentation

**Status**: ✅ Fully Verified
**Realization**: `selfsuff_reduced` (default) | `exo` | `selfsuff_reduced_bilateral22` (alternatives)
**Source Files Verified**: declarations.gms, equations.gms, input.gms, sets.gms, preloop.gms, presolve.gms, postsolve.gms, scaling.gms
**Total Lines**: ~79 (equations.gms, selfsuff_reduced)
**Total Equations**: 9 (selfsuff_reduced default) | 3 (exo) | 8 (selfsuff_reduced_bilateral22)

---

> ⚙️ **Default Realization**: `selfsuff_reduced`
> The equations and algorithms below describe the **default `selfsuff_reduced` realization** (confirmed in `config/default.cfg`: `cfg$gms$trade <- "selfsuff_reduced"`). Sections or equations that exist **only** in the `selfsuff_reduced_bilateral22` alternative are clearly marked **`[⚠️ bilateral22 only]`**.
>
> **2026-05 update (PR #866, "Major Update to Bilateral trade implementation")**: All three realizations were rewritten. The interface variable *vm_cost_trade* was **removed** and **split into three** new interface variables — `vm_cost_trade_tariff`, `vm_cost_trade_margin`, `vm_cost_trade_feasibility` — each summed separately into the Module 11 objective.

---

## Overview

Module 21 implements **agricultural trade among world regions** using a **dual-pool system**: a self-sufficiency pool based on historical trade patterns, and a comparative advantage pool based on cost-efficient production. The module enforces global and regional trade balances, ensuring regional demand is met through domestic production and imports.

**Core Function**: Connects regional production (Module 17) to regional demand (Module 16) via trade flows, calculating trade costs (transport margins, tariffs, and a feasibility penalty) that feed into the objective function (Module 11) via three separate interface variables: `vm_cost_trade_tariff`, `vm_cost_trade_margin`, `vm_cost_trade_feasibility`.

**Key Design**: Uses **superregional self-sufficiency ratios and export shares** to manage trade flows. Margins and tariffs are applied at the superregional level `(h,k)` — not bilateral between region pairs. The `selfsuff_reduced_bilateral22` alternative replaces this with explicit bilateral trade flows between region pairs.

**Reference**: `module.gms:10-13`

---

## Trade Architecture

### Two-Pool Trade System

**Diagram**: `realization.gms:20` references `trade_pools.png`

Module 21 splits demand into two pools controlled by trade balance reduction factor `i21_trade_bal_reduction(t,k_trade)`:

1. **Self-Sufficiency Pool** (when `i21_trade_bal_reduction = 1`):
   - All demand enters this pool
   - Regional self-sufficiency ratios `f21_self_suff(t,h,k_trade)` dictate production levels
   - Ratios < 1 → region imports
   - Ratios > 1 → region exports
   - Fixed trade patterns based on historical data

2. **Comparative Advantage Pool** (when `i21_trade_bal_reduction = 0`):
   - All demand enters this pool
   - Free global production allocation
   - Based on cost efficiency
   - No regional constraints

**Configuration**: Set via `c21_trade_liberalization` global variable (`input.gms:8`)

**Source**: `realization.gms:8-16`, `equations.gms:25-30`

---

## Commodity Classification

### Tradable vs Non-Tradable (`sets.gms:11-21`)

**Non-Tradable Commodities** (`k_notrade`, 8 items):
```
oilpalm     - Not traded (only oil/oilcake, due to FAOSTAT complications)
foddr       - Too bulky to trade
pasture     - Too bulky to trade
res_cereals, res_fibrous, res_nonfibrous - Residues (not traded)
begr, betr  - Bioenergy (biomass traded in REMIND, not MAgPIE)
```

**Tradable Commodities** (`k_trade`, 38 items):
- **Crops**: tece, maiz, trce, rice_pro, soybean, rapeseed, groundnut, sunflower, puls_pro, potato, cassav_sp, sugr_cane, sugr_beet, others, cottn_pro
- **Processed**: oils, oilcakes, sugar, molasses, alcohol, ethanol, distillers_grain, brans, scp, fibres
- **Livestock**: livst_rum, livst_pig, livst_chick, livst_egg, livst_milk, fish
- **Forestry**: wood, woodfuel

**Limited Trade Products** (`k_hardtrade21`, 16 items, `sets.gms:26-29`):
```
sugr_cane, sugr_beet                     - Primary products (hardly traded in reality)
oils, oilcakes, alcohol, ethanol,        - Secondary products
distillers_grain, brans, scp, fibres     - (trade limited to prevent extreme specialization)
livst_rum, livst_pig, livst_chick,       - Livestock products
livst_egg, livst_milk, fish
```

**Rationale**: Limiting secondary product trade prevents unrealistic regional specialization (`sets.gms:23-25`)

---

## Equations

> **The default `selfsuff_reduced` realization has 9 equations** (`q21_trade_glo`, `q21_notrade`, `q21_trade_reg`, `q21_trade_reg_up`, `q21_excess_dem`, `q21_excess_supply`, `q21_cost_trade_tariff`, `q21_cost_trade_margin`, `q21_cost_trade_feasibility`). The three trade-cost equations replace a former pair of equations (*q21_cost_trade_reg* + *q21_cost_trade*) that computed trade cost as one combined stream; PR #866 split tariff, margin, and feasibility into separate equations and interface variables. The `selfsuff_reduced_bilateral22` alternative has a different set of 8 equations — see the comparison table below.

### 1. Global Production Constraint (`q21_trade_glo`)

**Formula** (`modules/21_trade/selfsuff_reduced/equations.gms:12-14`):
```gams
q21_trade_glo(k_trade)..
  sum(i2 ,vm_prod_reg(i2,k_trade)) =g=
  sum(i2, vm_supply(i2,k_trade)) + sum(ct,f21_trade_balanceflow(ct,k_trade));
```

**Meaning**: Global production ≥ global supply + balance flows

**Purpose**: Ensures the comparative advantage pool can fulfill global demand

**Variables**:
- `vm_prod_reg(i,k)` - Regional production (from Module 17)
- `vm_supply(i,k)` - Regional supply/demand (from Module 16)
- `f21_trade_balanceflow(t,k)` - Domestic balance flows (input file)

**Constraint Type**: Greater-than-or-equal (≥), allows production surplus

---

### 2. Non-Tradable Constraint (`q21_notrade`)

**Formula** (`modules/21_trade/selfsuff_reduced/equations.gms:18-19`):
```gams
q21_notrade(h2,k_notrade)..
  sum(supreg(h2,i2),vm_prod_reg(i2,k_notrade)) =g= sum(supreg(h2,i2), vm_supply(i2,k_notrade));
```

**Meaning**: Superregional production ≥ superregional supply (for non-tradables)

**Purpose**: Enforces superregional self-sufficiency for non-tradable commodities (production can be reallocated among regions within a super-region `h2`; this is NOT strict per-region self-sufficiency)

**Applies To**: 8 commodities in `k_notrade` (oilpalm, foddr, pasture, residues, begr, betr)

---

### 3. Minimum Self-Sufficiency / Lower Production Bound (`q21_trade_reg`)

**Formula** (`modules/21_trade/selfsuff_reduced/equations.gms:31-35`):
```gams
q21_trade_reg(h2,k_trade)..
 sum(supreg(h2,i2),vm_prod_reg(i2,k_trade)) =g=
  m21_baseline_production(vm_supply, v21_excess_prod, f21_self_suff)
  * sum(ct,i21_trade_bal_reduction(ct,k_trade))
  - v21_import_for_feasibility(h2,k_trade);
```

**Meaning**: Regional production must meet minimum self-sufficiency requirements (lower bound of the production band).

**Macro**: `m21_baseline_production(supply, excess_prod, self_suff)` is defined in `core/macros.gms:115-119`. It expands to the two-case baseline-production expression:
```gams
((sum(supreg(h2,i2),supply(i2,k_trade)) + excess_prod(h2,k_trade))
   $((sum(ct,self_suff(ct,h2,k_trade)) >= 1))
 + (sum(supreg(h2,i2),supply(i2,k_trade)) * sum(ct,self_suff(ct,h2,k_trade)))
   $((sum(ct,self_suff(ct,h2,k_trade)) < 1)))
```

**Two Cases** (within the macro):
1. **Exporters** (`f21_self_suff ≥ 1`): baseline = supply + excess production
2. **Importers** (`f21_self_suff < 1`): baseline = supply × self-suff ratio

The lower bound multiplies this baseline by `i21_trade_bal_reduction` and subtracts `v21_import_for_feasibility`.

**Key Parameters**:
- `f21_self_suff(t,h,k)` - Target self-sufficiency ratio (0-∞)
- `i21_trade_bal_reduction(t,k)` - Pool allocation factor (0-1)
- `v21_import_for_feasibility(h,k)` - Emergency imports to maintain feasibility (only wood, woodfuel)

**Reference**: Schmitz et al. 2012 (cited in `equations.gms:24-25`)

---

### 4. Maximum Self-Sufficiency / Upper Production Bound (`q21_trade_reg_up`)

**Formula** (`modules/21_trade/selfsuff_reduced/equations.gms:39-42`):
```gams
q21_trade_reg_up(h2,k_trade) ..
 sum(supreg(h2,i2),vm_prod_reg(i2,k_trade)) =l=
  m21_baseline_production(vm_supply, v21_excess_prod, f21_self_suff)
  / sum(ct,i21_trade_bal_reduction(ct,k_trade));
```

**Meaning**: Regional production must not exceed maximum self-sufficiency limits (upper bound of the production band).

**Purpose**: Upper bound to prevent over-production beyond trade pattern requirements

**Difference from Minimum**: Same `m21_baseline_production` macro, but **divided** by `i21_trade_bal_reduction` instead of multiplied, and no feasibility-import term.

---

### 5. Global Excess Demand (`q21_excess_dem`)

**Formula** (`modules/21_trade/selfsuff_reduced/equations.gms:47-51`):
```gams
q21_excess_dem(k_trade)..
 v21_excess_dem(k_trade) =g=
 sum(h2, sum(supreg(h2,i2),vm_supply(i2,k_trade))*(1 - sum(ct,f21_self_suff(ct,h2,k_trade)))
 $(sum(ct,f21_self_suff(ct,h2,k_trade)) < 1))
 + sum(ct,f21_trade_balanceflow(ct,k_trade)) + sum(h2, v21_import_for_feasibility(h2,k_trade));
```

**Meaning**: Global excess demand = sum of imports from importing regions + balance flows + feasibility imports

**Purpose**: Calculates total demand that enters the comparative advantage pool

**Logic**: Only regions with `f21_self_suff < 1` contribute to excess demand (importers)

---

### 6. Excess Supply Distribution (`q21_excess_supply`)

**Formula** (`modules/21_trade/selfsuff_reduced/equations.gms:56-58`):
```gams
q21_excess_supply(h2,k_trade)..
 v21_excess_prod(h2,k_trade) =e=
 v21_excess_dem(k_trade)*sum(ct,i21_exp_shr(ct,h2,k_trade));
```

**Meaning**: Regional excess production = global excess demand × regional export share

**Purpose**: Distributes global excess demand to exporting regions based on historical export shares

**Key Parameter**:
- `i21_exp_shr(t,h,k)` - Export shares **computed internally** in `preloop.gms` from `f21_dom_supply` and `f21_self_suff` (0 for importing regions). **Note**: This is an internal parameter (`i` prefix), NOT a file-read parameter (`f` prefix).

**Reference**: Schmitz et al. 2012 (cited in `equations.gms:53-54`)

---

### 7. Superregional Tariff Costs (`q21_cost_trade_tariff`)

> **PR #866**: This equation **replaces** the tariff portion of the former combined *q21_cost_trade_reg*. It defines the `vm_cost_trade_tariff` interface variable.

**Formula** (`modules/21_trade/selfsuff_reduced/equations.gms:62-65`):
```gams
q21_cost_trade_tariff(h2)..
 sum(supreg(h2,i2),vm_cost_trade_tariff(i2)) =g=
 sum(k_trade, i21_trade_tariff(h2,k_trade)
  * sum(supreg(h2,i2), vm_prod_reg(i2,k_trade) - vm_supply(i2,k_trade)));
```

**Meaning**: Superregional tariff cost = Σ over tradables of (superregional tariff rate × net exports)

**Purpose**: Aggregates tariff costs over all tradable commodities to the regional `vm_cost_trade_tariff(i)` interface variable.

**Key Parameter**:
- `i21_trade_tariff(h,k)` - Superregional tariff (USD17MER/tDM), set from `f21_trade_tariff(h,k)` when `s21_trade_tariff=1`, else 0 (`preloop.gms:27-31`)

**Units**: Million USD17MER per year

---

### 8. Superregional Transport Margin Costs (`q21_cost_trade_margin`)

> **PR #866**: This equation **replaces** the margin portion of the former combined *q21_cost_trade_reg*. It defines the `vm_cost_trade_margin` interface variable.

**Formula** (`modules/21_trade/selfsuff_reduced/equations.gms:69-72`):
```gams
q21_cost_trade_margin(h2)..
 sum(supreg(h2,i2),vm_cost_trade_margin(i2)) =g=
 sum(k_trade, i21_trade_margin(h2,k_trade)
  * sum(supreg(h2,i2), vm_prod_reg(i2,k_trade) - vm_supply(i2,k_trade)));
```

**Meaning**: Superregional transport margin cost = Σ over tradables of (superregional margin rate × net exports)

**Purpose**: Aggregates transport/insurance margin costs over all tradable commodities to the regional `vm_cost_trade_margin(i)` interface variable.

**Key Parameter**:
- `i21_trade_margin(h,k)` - Superregional transport + insurance costs (USD17MER/tDM), set from `f21_trade_margin(h,k)` in `preloop.gms:25`; floored at `s21_min_trade_margin_forestry` for wood/woodfuel.

**Units**: Million USD17MER per year

---

### 9. Superregional Feasibility Penalty Costs (`q21_cost_trade_feasibility`)

> **PR #866**: This equation **replaces** the feasibility-import penalty term of the former combined *q21_cost_trade_reg*. It defines the `vm_cost_trade_feasibility` interface variable.

**Formula** (`modules/21_trade/selfsuff_reduced/equations.gms:76-78`):
```gams
q21_cost_trade_feasibility(h2)..
 sum(supreg(h2,i2),vm_cost_trade_feasibility(i2)) =g=
 sum(k_trade, v21_import_for_feasibility(h2,k_trade) * s21_cost_import);
```

**Meaning**: Superregional feasibility cost = Σ over tradables of (emergency import volume × per-unit penalty)

**Purpose**: Aggregates the emergency-import penalty over all tradable commodities to the regional `vm_cost_trade_feasibility(i)` interface variable. In practice only `wood` and `woodfuel` have non-zero `v21_import_for_feasibility` (other commodities are fixed at 0 in `preloop.gms:36`).

**Key Parameter**:
- `s21_cost_import = 1500` USD17MER/tDM (emergency import penalty, `input.gms:18`)

**Units**: Million USD17MER per year

> **Note**: `presolve.gms` releases the fix on `vm_cost_trade_feasibility` each time step (`.lo = 0`, `.up = Inf`) so the solver can freely set its level via this equation (`modules/21_trade/selfsuff_reduced/presolve.gms:11-12`).

> **Bilateral22 / exo differ**: In `selfsuff_reduced_bilateral22` and `exo`, tariff and margin costs are computed differently and there is **no feasibility penalty** — `vm_cost_trade_feasibility.fx(i) = 0` is set in their `presolve.gms`. See the comparison table below.

---

## Key Algorithms

### Algorithm 1: Trade Pool Allocation (`modules/21_trade/selfsuff_reduced/preloop.gms:11-19`)

**Input Processing**:
```gams
loop(t_all,
 if(m_year(t_all) <= sm_fix_SSP2,
 i21_trade_bal_reduction(t_all,k_trade)=f21_trade_bal_reduction(t_all,"easytrade","l909090r808080");
 i21_trade_bal_reduction(t_all,k_hardtrade21)=f21_trade_bal_reduction(t_all,"hardtrade","l909090r808080");
 else
 i21_trade_bal_reduction(t_all,k_trade)=f21_trade_bal_reduction(t_all,"easytrade","%c21_trade_liberalization%");
 i21_trade_bal_reduction(t_all,k_hardtrade21)=f21_trade_bal_reduction(t_all,"hardtrade","%c21_trade_liberalization%");
 );
);
```

**Logic**:
1. Until `sm_fix_SSP2`, use the historical baseline regime `l909090r808080` so values match historical data
2. After `sm_fix_SSP2`, switch to the scenario regime selected by `%c21_trade_liberalization%`
3. Apply different reduction factors for "easytrade" vs "hardtrade" commodities
4. Reduction factor = 0 → all to comparative advantage pool
5. Reduction factor = 1 → all to self-sufficiency pool

**Trade Regimes** (`sets.gms:31-46`):
- `free2000` - Historical free trade baseline
- `regionalized` - Regional trade blocs
- `globalized` - Full global trade
- `fragmented` - Limited trade
- `l909090r808080` - Default scenario (livestock 90/90/90, rest 80/80/80)
- Various other scenarios (a909090, a908080, etc.)

---

### Algorithm 2: Tariff Configuration (`preloop.gms`) — `[⚠️ default version differs from bilateral22]`

**Switch Control** (`modules/21_trade/selfsuff_reduced/preloop.gms:27-31`):
```gams
if ((s21_trade_tariff=1),
    i21_trade_tariff(h,k_trade) = f21_trade_tariff(h,k_trade);
elseif (s21_trade_tariff=0),
    i21_trade_tariff(h,k_trade) = 0;
);
```

> **`[⚠️ bilateral22 only]`**: In `selfsuff_reduced_bilateral22`, tariffs use bilateral dimensions `(t_all,i_ex,i_im,k_trade)` and undergo an **optional linear fade** towards the `s21_trade_tariff_factor` target multiplier between `s21_trade_tariff_startyear` and `s21_trade_tariff_targetyear` (`modules/21_trade/selfsuff_reduced_bilateral22/preloop.gms:60-72`). **The bilateral dimensions and the `startyear`/`targetyear`/`factor` tariff-fade scalars do not exist in the default `selfsuff_reduced` realization** — `selfsuff_reduced` applies tariffs only as a single time-invariant superregional `(h,k)` rate, on/off via `s21_trade_tariff`.

**Scalars in default `selfsuff_reduced`** (`input.gms:16-20`):
- `s21_trade_tariff = 1` (1=on, 0=off)
- `s21_cost_import = 1500` USD17MER/tDM (emergency import penalty)
- `s21_min_trade_margin_forestry = 62` USD17MER/tDM (forestry margin floor)

**Purpose**: Populates superregional `i21_trade_tariff(h,k)` from file input `f21_trade_tariff(h,k)`

---

### Algorithm 3: Margin Floor for Forestry (`modules/21_trade/selfsuff_reduced/preloop.gms:33-34`)

**Implementation**:
```gams
i21_trade_margin(h,"wood")$(i21_trade_margin(h,"wood") < s21_min_trade_margin_forestry) = s21_min_trade_margin_forestry;
i21_trade_margin(h,"woodfuel")$(i21_trade_margin(h,"woodfuel") < s21_min_trade_margin_forestry) = s21_min_trade_margin_forestry;
```

**Purpose**: Ensures minimum transport costs for bulky forestry products

**Scalar**: `s21_min_trade_margin_forestry = 62` USD17MER per tDM (`input.gms:19`)

**Rationale**: Prevents unrealistically low transport costs for low-value, high-volume products

---

### Algorithm 4: Feasibility Import Bounds (`modules/21_trade/selfsuff_reduced/preloop.gms:36-38`)

**Configuration**:
```gams
v21_import_for_feasibility.fx(h,k_trade) = 0;              ! Fixed at 0 by default
v21_import_for_feasibility.lo(h,k_import21) = 0;           ! Lower bound 0
v21_import_for_feasibility.up(h,k_import21) = Inf;         ! Upper bound infinite
```

**Allowed Commodities** (`input.gms:12-13` (k_import21 is declared in selfsuff_reduced/input.gms, not sets.gms)):
```gams
k_import21(k_trade) = / wood, woodfuel /
```

**Purpose**: Emergency valve to maintain model feasibility for forestry products

**Penalty**: High cost (`s21_cost_import = 1500` USD/tDM) ensures this is last resort

---

## Input Data Files

### Core Trade Parameters

| File | Parameter | Description | Dimensions | Units |
|------|-----------|-------------|------------|-------|
| `f21_trade_self_suff.cs3` | `f21_self_suff` | Self-sufficiency ratios | (t,h,k) | Dimensionless (0-∞) |
| `f21_trade_domestic_supply.cs3` | `f21_dom_supply` | Domestic supply (used to compute export shares) | (t,h,k) | Mio. tDM/yr |
| `f21_trade_bal_reduction.cs3` | `f21_trade_bal_reduction` | Pool allocation factor | (t,trade_groups,regime) | Dimensionless (0-1) |
| `f21_trade_balanceflow.cs3` | `f21_trade_balanceflow` | Domestic balance flows | (t,k) | Mio. tDM/yr |

> **Note on export shares**: `i21_exp_shr(t,h,k)` is **NOT** read from a file. It is **computed internally** in `preloop.gms` from `f21_dom_supply` and `f21_self_suff`:
> ```gams
> i21_exports(t_all,h,k_trade) = ((f21_self_suff * f21_dom_supply) - f21_dom_supply)$(f21_self_suff > 1);
> i21_exp_glo(t_all,k_trade)   = sum(h, i21_exports(t_all,h,k_trade));
> i21_exp_shr(t_all,h,k_trade) = i21_exports / (i21_exp_glo + 0.001$(i21_exp_glo = 0));
> ```

### Bilateral Trade Costs — `[⚠️ bilateral22 only]`

> These input files are **not used** in the default `selfsuff_reduced` realization. They apply exclusively to `selfsuff_reduced_bilateral22`, which uses bilateral trade flows `v21_trade(i_ex,i_im,k)`.

| File | Parameter | Description | Dimensions | Units |
|------|-----------|-------------|------------|-------|
| `f21_trade_margin_bilat.cs5` | `f21_trade_margin` | Transport + admin costs | (i_ex,i_im,k) | USD17MER/tDM |
| `f21_trade_tariff_bilat.cs5` | `f21_trade_tariff` | Specific duty tariffs | (i_ex,i_im,k) | USD17MER/tDM |

**Source**: `modules/21_trade/selfsuff_reduced_bilateral22/input.gms:45-57`

**Note**: Files are in realization-specific subdirectory (`modules/21_trade/selfsuff_reduced_bilateral22/input/`)

---

## Interface Variables

### Provided by Module 21

> **PR #866**: the former single interface variable *vm_cost_trade* was **removed** and **split into three** separate `vm_`-prefixed interface variables. All three are positive variables present in **all three realizations** (`selfsuff_reduced`, `exo`, `selfsuff_reduced_bilateral22`), and all three are summed individually into the Module 11 cost equation.

| Variable | Description | Dimensions | Units | Used By |
|----------|-------------|------------|-------|---------|
| `vm_cost_trade_tariff` | Regional tariff costs across all commodities entering objective | (i) | Mio. USD17MER/yr | Module 11 (Costs) |
| `vm_cost_trade_margin` | Regional transport margin costs across all commodities entering objective | (i) | Mio. USD17MER/yr | Module 11 (Costs) |
| `vm_cost_trade_feasibility` | Regional feasibility penalty costs across all commodities entering objective | (i) | Mio. USD17MER/yr | Module 11 (Costs) |

**Source**: `modules/21_trade/selfsuff_reduced/declarations.gms:21-23`; consumed in Module 11 `modules/11_costs/default/equations.gms:30-32`.

**Note**: In `exo` and `selfsuff_reduced_bilateral22` there is no feasibility-import mechanism, so `vm_cost_trade_feasibility` is fixed at 0 in their `presolve.gms` (it still exists as an interface variable so Module 11 can sum it unconditionally).

### Used by Module 21

| Variable | Description | Dimensions | Units | Provided By |
|----------|-------------|------------|-------|-------------|
| `vm_prod_reg` | Regional production | (i,k) | Mio. tDM/yr | Module 17 (Production) |
| `vm_supply` | Regional supply/demand | (i,k) | Mio. tDM/yr | Module 16 (Demand) |

**Source**: Cross-verified with Module 17 `equations.gms:17` and Module 16 `equations.gms`

---

## Internal Variables

**Default `selfsuff_reduced`** (`modules/21_trade/selfsuff_reduced/declarations.gms:17-20`):

| Variable | Description | Dimensions | Units |
|----------|-------------|------------|-------|
| `v21_excess_dem` | Global excess demand | (k_trade) | Mio. tDM/yr |
| `v21_excess_prod` | Superregional excess production | (h,k_trade) | Mio. tDM/yr |
| `v21_import_for_feasibility` | Additional imports to maintain feasibility | (h,k_trade) | Mio. tDM/yr |

> **PR #866 removed *v21_cost_trade_reg*** (the former per-commodity superregional trade-cost variable). Trade costs are now defined directly on the three `vm_cost_trade_*` interface variables via `q21_cost_trade_tariff` / `q21_cost_trade_margin` / `q21_cost_trade_feasibility`.

> `[⚠️ bilateral22 only]`: `v21_trade(i_ex,i_im,k_trade)`, `v21_cost_tariff_reg(i,k_trade)`, and `v21_cost_margin_reg(i,k_trade)` exist **only** in `selfsuff_reduced_bilateral22`. `v21_excess_dem`, `v21_excess_prod`, and `v21_import_for_feasibility` do **not** exist in bilateral22.

---

### Realization Comparison (post PR #866)

The trade module has **three** realizations. All three share the three `vm_cost_trade_*` interface variables but compute them via different equations.

**Equation counts**: `selfsuff_reduced` = 9 | `exo` = 3 | `selfsuff_reduced_bilateral22` = 8.

#### `selfsuff_reduced` (default)
Production-band approach: self-sufficiency ratios and export shares define a baseline; production may fluctuate within a band. 9 equations: `q21_trade_glo`, `q21_notrade`, `q21_trade_reg`, `q21_trade_reg_up`, `q21_excess_dem`, `q21_excess_supply`, `q21_cost_trade_tariff`, `q21_cost_trade_margin`, `q21_cost_trade_feasibility`. Has a feasibility-import valve (`v21_import_for_feasibility`, wood/woodfuel only).

#### `exo`
Trade fully prescribed exogenously; regions do not interact. 3 equations only:

| Equation | Dims | Purpose |
|----------|------|---------|
| `q21_notrade` | `(h,kall)` | Regional production ≥ supply + exogenous `f21_trade_balance` (over **all** `kall`, tradable and non-tradable) |
| `q21_cost_trade_tariff` | `(h)` | Superregional tariff costs → `vm_cost_trade_tariff` |
| `q21_cost_trade_margin` | `(h)` | Superregional margin costs → `vm_cost_trade_margin` |

No feasibility penalty (`vm_cost_trade_feasibility.fx(i) = 0` in `modules/21_trade/exo/presolve.gms:10`). Source: `modules/21_trade/exo/equations.gms`, `modules/21_trade/exo/declarations.gms:20-24`.

#### `selfsuff_reduced_bilateral22`
Explicit **bilateral** trade flows `v21_trade(i_ex,i_im,k_trade)`, bounded by a corridor around historically observed import-supply ratios. 8 equations:

| Equation | Dims | Purpose |
|----------|------|---------|
| `q21_notrade` | `(h,k_notrade)` | Non-tradables produced within super-region |
| `q21_trade_reg` | `(h,k_trade)` | Regional material balance: production covers supply ± net bilateral trade + balance flows |
| `q21_trade_lower` | `(i_ex,i_im,k_trade)` | Lower bound on each bilateral flow (historical ratio − flexibility window) |
| `q21_trade_upper` | `(i_ex,i_im,k_trade)` | Upper bound on each bilateral flow (historical ratio + flexibility window) |
| `q21_costs_tariffs` | `(i,k_trade)` | Bilateral tariff costs per exporter → `v21_cost_tariff_reg` |
| `q21_costs_margins` | `(i,k_trade)` | Bilateral margin costs per exporter → `v21_cost_margin_reg` |
| `q21_cost_trade_tariff` | `(i)` | Aggregates `v21_cost_tariff_reg` over commodities → `vm_cost_trade_tariff` |
| `q21_cost_trade_margin` | `(i)` | Aggregates `v21_cost_margin_reg` over commodities → `vm_cost_trade_margin` |

No feasibility penalty (`vm_cost_trade_feasibility.fx(i) = 0` in `modules/21_trade/selfsuff_reduced_bilateral22/presolve.gms:11`). Source: `modules/21_trade/selfsuff_reduced_bilateral22/equations.gms`, `modules/21_trade/selfsuff_reduced_bilateral22/declarations.gms`.

> **Note**: the former bilateral22 equation *q21_trade_bilat* and the file-read parameter *f21_exp_shr* described in earlier versions of this doc no longer exist — PR #866 replaced the bilateral22 mechanism with the import-supply-ratio corridor (`q21_trade_lower` / `q21_trade_upper`) above.

**Key parameter dimensions in bilateral22** (`modules/21_trade/selfsuff_reduced_bilateral22/declarations.gms:8-14`):

| Parameter | Dimensions | Description |
|-----------|-----------|-------------|
| `i21_trade_margin` | `(i_ex,i_im,k_trade)` | Bilateral freight + insurance costs |
| `i21_trade_tariff` | `(t_all,i_ex,i_im,k_trade)` | Bilateral specific-duty tariff rates (time-varying via tariff fade) |
| `i21_import_supply_historical` | `(i_ex,i_im,t_all,k_trade)` | Share of importer domestic supply sourced from each exporter |
| `i21_trade_bilat_stddev` | `(t_all,i_ex,i_im,k_trade)` | Std-dev flexibility window |
| `i21_import_supply_scenario` | `(t_all)` | Time-varying scalar on import supply ratios |
| `i21_stddev_lib_factor` | `(t_all)` | Time-varying scalar on the flexibility-window width |

---

## Configuration Options

### Global Settings

> Defaults below verified against `config/default.cfg:644-708` (2026-05). PR #866 **removed** *s21_trade_tariff_fadeout* and **added** `s21_trade_tariff_factor`, `s21_stddev_lib_factor`, `s21_import_supply_scenario`, `s21_import_supply_scenario_targetyear`, `s21_trade_scenario_adjustments`.

**Applies to all / default realization (`selfsuff_reduced`)**:

| Setting | Description | Values | Default |
|---------|-------------|--------|---------|
| `c21_trade_liberalization` | Trade regime scenario (used after `sm_fix_SSP2`) | See `trade_regime21` set | `l909090r808080` |
| `s21_trade_tariff` | Tariff switch | 1=on, 0=off | 1 |
| `s21_cost_import` | Emergency import penalty | USD17MER/tDM | 1500 |
| `s21_min_trade_margin_forestry` | Minimum forestry transport cost | USD17MER/tDM | 62 |

`modules/21_trade/selfsuff_reduced/input.gms:16-19` declares `s21_trade_tariff`, `s21_cost_import`, `s21_min_trade_margin_forestry`. `c21_trade_liberalization` is set in `modules/21_trade/selfsuff_reduced/input.gms:8`.

**`selfsuff_reduced_bilateral22` scalars** (`modules/21_trade/selfsuff_reduced_bilateral22/input.gms:16-27`):

| Setting | Description | Default |
|---------|-------------|---------|
| `s21_trade_tariff` | Tariff switch (1=on, 0=off) | 1 |
| `s21_trade_tariff_factor` | Target multiplier for trade-tariff fade (1 = no change, 0 = fade to zero) | 1 |
| `s21_trade_tariff_startyear` | Year to start fading tariffs towards `s21_trade_tariff_factor` | 2025 |
| `s21_trade_tariff_targetyear` | Year to finish the tariff fade | 2050 |
| `s21_import_supply_scenario` | Multiplier on the import-supply ratio itself (linear fade-in) | 1 |
| `s21_import_supply_scenario_targetyear` | Target year for full implementation of `s21_import_supply_scenario` | 2050 |
| `s21_stddev_lib_factor` | Liberalization factor — multiplier on the flexibility window around the import-supply ratio | 1 |
| `s21_cost_import` | Cost for additional imports to maintain feasibility | 1500 |
| `s21_min_trade_margin_forestry` | Minimum trade margin for forestry products | 62 |
| `s21_trade_scenario_adjustments` | Switch to apply scenario adjustments to import supply (0=off, 1=on) | 0 |

> **Tariff fade (bilateral22)**: `s21_trade_tariff_startyear`/`_targetyear` now describe a linear interpolation of tariffs from their initial level towards `s21_trade_tariff_factor` (`modules/21_trade/selfsuff_reduced_bilateral22/preloop.gms:60-72`). The old binary *s21_trade_tariff_fadeout* (fade-to-zero on/off) no longer exists; setting `s21_trade_tariff_factor = 0` reproduces a full fade-out.

> **`exo` scalars** (`modules/21_trade/exo/input.gms:8-11`): only `s21_trade_tariff` and `s21_min_trade_margin_forestry`.

> **Config note**: `config/default.cfg` also lists `cfg$gms$s21_trade_bal_damper` (0.65) and a `c21_trade_scenario`-style scenario hook. In the current working tree neither is consumed by any realization's `.gms` code (`c21_trade_scenario` appears only in a `modules/21_trade/selfsuff_reduced_bilateral22/realization.gms` comment; the active scenario-adjustment path uses the `s21_trade_scenario_adjustments` switch with the `f21_trade_scenario_adjustments` table). Treat these two config entries as not yet wired into module code.

---

## Scaling

**Applied Factors** (`modules/21_trade/selfsuff_reduced/scaling.gms:8-10`):
```gams
vm_cost_trade_tariff.scale(i) = 1e5;
vm_cost_trade_margin.scale(i) = 1e5;
vm_cost_trade_feasibility.scale(i) = 1e5;
```

**Purpose**: Improves numerical stability by scaling the three trade-cost interface variables to similar magnitudes

**Magnitude**: Trade costs scaled to ~1-100 range for solver

**Note**: PR #866 replaced the former *vm_cost_trade* / *v21_cost_trade_reg* scaling with one `.scale` line per new interface variable. Equation-level scaling lines exist but are commented out.

---

## Key Dependencies

### Upstream Dependencies (Variables Used)

1. **Module 17 (Production)**:
   - `vm_prod_reg(i,k)` - Regional production totals
   - Used in: All trade balance equations

2. **Module 16 (Demand)**:
   - `vm_supply(i,k)` - Regional supply requirements
   - Used in: All trade balance equations

### Downstream Dependencies (Variables Provided)

1. **Module 11 (Costs)**:
   - `vm_cost_trade_tariff(i)`, `vm_cost_trade_margin(i)`, `vm_cost_trade_feasibility(i)` - Regional trade costs
   - All three included in the objective function (summed individually in `q11_cost_reg`)

---

## Participates In

### Conservation Laws

**Food Supply = Demand Balance**: ✅ **CRITICAL PARTICIPANT**

Module 21 implements the **regional trade balance mechanism** that ensures global food supply meets demand:

- **Global Production Constraint** (`q21_trade_glo`): Enforces that regional production plus net imports equals supply requirements
  - Formula: `sum(i2, vm_prod_reg(i2,k_trade)) =g= sum(i2, vm_supply(i2,k_trade)) + f21_trade_balanceflow(ct,k_trade)`
  - Location: `equations.gms:12-14`

- **Two-Pool Trade System**:
  - **Self-sufficiency pool**: Regions trade to meet minimum self-sufficiency targets (`i21_trade_bal_reduction`)
  - **Comparative advantage pool**: Remaining production allocated by comparative advantage
  - Balance reduction reduces reliance on trade over time

- **Cross-Module Reference**: `cross_module/nitrogen_food_balance.md` (Part 2, Section 2.4)

**Other Conservation Laws**:
- Land Balance: ❌ Does NOT participate (reads `vm_land` but doesn't affect land allocation)
- Water Balance: ❌ Does NOT participate (no direct water demand)
- Carbon Balance: ❌ Does NOT participate (trade flows are carbon-neutral in accounting)
- Nitrogen Tracking: ❌ Does NOT explicitly participate (N-embodied in trade is implicit)

---

### Dependency Chains

**Centrality Rank**: 6 of 46 modules
**Total Connections**: 9 (provides to 8 modules, depends on 1)
**Hub Type**: **Processing Hub** (aggregates regional supply/demand and balances via trade)

**Provides To** (8 modules):
1. **Module 11 (Costs)** - Trade costs (`vm_cost_trade_tariff`, `vm_cost_trade_margin`, `vm_cost_trade_feasibility`)
2. **Module 16 (Demand)** - Supply signals (import/export flows affect food availability)
3. **Module 17 (Production)** - Trade flows inform production decisions
4. **Module 73 (Timber)** - Timber trade balance
5. Plus 4 other modules receiving trade flow information

**Depends On** (1 direct dependency):
1. **Module 16 (Demand)** - Regional supply requirements (`vm_supply`)
2. **Module 17 (Production)** - Regional production totals (`vm_prod_reg`)

**Key Position**: Module 21 acts as the **trade intermediary** between regional production (Module 17) and regional demand (Module 16), ensuring global market clearing.

**Reference**: `core_docs/Module_Dependencies.md` (Section 6.2: "Most Dependent Modules")

---

### Circular Dependencies

**Participates In**: 1 circular dependency cycle

#### Cycle C5: Demand-Trade-Production (Simultaneous Resolution)

**Structure**:
```
Module 16 (Demand) ──→ vm_supply(i,k) ──→ Module 21 (Trade)
       ↑                                         │
       │                                         │
       └──── self-sufficiency constraints ←───────┘
                           ↓
                  Module 17 (Production)
                     vm_prod_reg(i,k)
```

**Resolution Mechanism**: **Type 2 - Simultaneous Equations**
- All three modules' variables (`vm_supply`, `vm_prod_reg`, `v21_excess_prod`, `v21_excess_dem`) are optimized **simultaneously** in the same GAMS SOLVE statement
- The coupled system of equations forms a square system (# variables = # equations) with unique solution
- GAMS solver (CONOPT/IPOPT) solves all equations together in one optimization

**Why It Works**:
1. Self-sufficiency constraints (`q21_trade_reg`) and excess demand/supply variables link supply and production
2. Global balance ensures total imports = total exports
3. Regional production + net imports must meet regional demand
4. System is economically consistent (market clearing)

**Testing Protocol** (if modifying Module 21):
- ✅ Verify food balance holds: `sum(i, vm_prod_reg(i,k)) = sum(i, vm_supply(i,k))`
- ✅ Verify trade balance: `sum(i, vm_prod_reg(i,k)) >= sum(i, vm_supply(i,k))` (global production covers global demand)
- ✅ Test infeasibility scenarios (regions with zero production but high demand)
- ✅ Check self-sufficiency constraints are not violated

**Reference**: `cross_module/circular_dependency_resolution.md` (Section 3.1, Table of Cycles - C5)

---

### Modification Safety

**Risk Level**: 🟡 **MEDIUM RISK**

**Safe Modifications**:
- ✅ Adjusting trade cost parameters (`f21_trade_margin`, `f21_trade_tariff`)
- ✅ Changing self-sufficiency reduction trajectories (`i21_trade_bal_reduction`)
- ✅ Modifying export share distributions (`i21_exp_shr` — computed internally in preloop.gms from `f21_dom_supply` and `f21_self_suff`)
- ✅ Adding new commodities to trade pools (requires set expansion)
- ✅ Implementing trade policy scenarios (tariff/margin adjustments)

**Dangerous Modifications**:
- ⚠️ Removing global production constraint → violates food balance
- ⚠️ Hardcoding trade flows → can make model infeasible
- ⚠️ Changing trade balance equations → affects 8 downstream modules
- ⚠️ Modifying feasibility import mechanism → can break emergency food supply

**Required Testing** (for ANY modification):
1. **Food Balance Conservation**:
   - Verify global production = global supply for all commodities
   - Check regional food security (no starvation scenarios)
   - Test with extreme self-sufficiency scenarios

2. **Dependency Chain Validation**:
   - Module 11 (Costs): Verify trade costs are reasonable (not infinite)
   - Module 16 (Demand): Verify supply signals reach demand module
   - Module 17 (Production): Verify production responds to trade opportunities

3. **Circular Dependency Check**:
   - Run model and verify convergence (simultaneous equations must have solution)
   - Check for oscillations in trade flows between regions
   - Test with constrained production scenarios (droughts, yield shocks)

4. **Infeasibility Testing**:
   - Test regions with zero production but non-zero demand
   - Verify feasibility imports activate when needed
   - Check that tariff costs don't become prohibitive

**Common Issues**:
- **Trade starvation**: Regions cannot import enough food → increase self-sufficiency reduction or enable feasibility imports
- **Unrealistic trade flows**: All production concentrated in one region → adjust export shares or trade margins
- **High trade costs**: Tariffs too high → model prefers autarky over trade → reduce tariff rates

**Reference**: `cross_module/modification_safety_guide.md` (mentions Module 21 as medium-risk trade hub)

---

## Limitations

### 1. Fixed Trade Patterns
**What**: Self-sufficiency ratios and export shares are predetermined from historical data
**Where**: `f21_self_suff` input file; `i21_exp_shr` computed internally in `preloop.gms`
**Impact**: Trade patterns adapt to price changes only within comparative advantage pool
**Source**: `realization.gms:22-23`

### 2. No Endogenous Trade Pattern Evolution
**What**: Export shares and self-sufficiency ratios do not respond to changing comparative advantages over time
**Where**: Parameters fixed exogenously, not optimized variables
**Impact**: Cannot model structural shifts in global trade patterns

### 3. Bilateral Costs Are Static
**What**: Trade margins and tariffs do not respond to trade volumes or infrastructure development
**Where**: `i21_trade_margin`, `i21_trade_tariff` set in preloop
**Impact**: No economies of scale in transport or dynamic tariff negotiations

### 4. Superregional Aggregation
**What**: Some constraints operate at superregional (h) level, not regional (i) level
**Where**: `q21_trade_reg`, `q21_trade_reg_up`, `q21_excess_supply`
**Impact**: Hides within-superregion trade heterogeneity

### 5. Tariffs Assigned to Exporters
**What**: Tariff (and margin) costs attributed to exporting region, not importing region
**Where**: `q21_cost_trade_tariff` / `q21_cost_trade_margin` in `selfsuff_reduced` (net exports `vm_prod_reg - vm_supply`); `q21_costs_tariffs` / `q21_costs_margins` in `selfsuff_reduced_bilateral22`
**Impact**: May not reflect real-world tariff incidence

### 6. Limited Feasibility Imports
**What**: Emergency imports only allowed for wood and woodfuel
**Where**: `k_import21` set (`input.gms:12-13` (k_import21 is declared in selfsuff_reduced/input.gms, not sets.gms))
**Impact**: Other commodities cannot use feasibility valve, may cause infeasibilities

### 7. No Trade Dynamics
**What**: No representation of trade lags, storage, or multi-year contracts
**Where**: Static within-timestep equations
**Impact**: Cannot model trade timing or buffering effects

### 8. No Explicit Transport Infrastructure
**What**: Trade margins represent transport costs but not infrastructure capacity constraints
**Where**: Margins are price-like parameters, not capacity-constrained
**Impact**: Cannot model port capacity, shipping lane congestion, or infrastructure investment

### 9. Secondary Product Trade Restrictions
**What**: Trade of processed products (oils, ethanol, etc.) is limited to prevent specialization
**Where**: `k_hardtrade21` set with higher trade balance reduction
**Impact**: May underestimate global value chains and processing specialization

### 10. No Bilateral Trade Policy Dynamics
**What**: Cannot model trade agreements, sanctions, or regional blocs evolving over time
**Where**: Tariffs and margins can fade out but not change structurally
**Impact**: Limited scenario capability for geopolitical trade shifts

---

## Verification Notes

**Equation Count**: ✅ 9 equations verified for default `selfsuff_reduced`
- `q21_trade_glo`, `q21_notrade`, `q21_trade_reg`, `q21_trade_reg_up`, `q21_excess_dem`, `q21_excess_supply`, `q21_cost_trade_tariff`, `q21_cost_trade_margin`, `q21_cost_trade_feasibility`
- All 9 equation formulas verified against `modules/21_trade/selfsuff_reduced/equations.gms`
- `exo` has 3 equations (`q21_notrade`, `q21_cost_trade_tariff`, `q21_cost_trade_margin`); `selfsuff_reduced_bilateral22` has 8 (see Realization Comparison)

**Variables**: ✅ 3 interface variables verified — `vm_cost_trade_tariff`, `vm_cost_trade_margin`, `vm_cost_trade_feasibility`
- Confirmed consumption in Module 11 `modules/11_costs/default/equations.gms:30-32`

**Formula Accuracy**: ✅ All equation formulas match source code exactly
**Code Truth Compliance**: ✅ All claims verified against source code

---

**Verified Against**:
- `../modules/21_trade/selfsuff_reduced/{declarations,equations,preloop,presolve,postsolve,sets,input,scaling}.gms`
- `../modules/21_trade/exo/{declarations,equations,presolve,postsolve,realization,sets,input}.gms`
- `../modules/21_trade/selfsuff_reduced_bilateral22/{declarations,equations,preloop,presolve,postsolve,sets,input,realization}.gms`
- `core/macros.gms:115-119` (`m21_baseline_production`)
- `../config/default.cfg:644-708`
**Verification Method**: Equations and scalars cross-referenced with current `develop` working-tree source code
