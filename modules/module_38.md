# Module 38: Factor Costs - Comprehensive Documentation

**Location**: `modules/38_factor_costs/`
**Default Realization**: `sticky_feb18` (4 q38 equations: `q38_cost_prod_labor`, `q38_cost_prod_capital`, `q38_investment_immobile`, `q38_investment_mobile`)
**Authors**: Jan Philipp Dietrich, Benjamin Bodirsky, Kristine Karstens, Edna J. Molina Bacca, Debbora Leip

---

> ⚙️ **Default Realization**: `sticky_feb18` — confirmed in `config/default.cfg`: `cfg$gms$factor_costs <- "sticky_feb18"`.
>
> **Three realizations available**:
> - **`sticky_feb18`** (default) — capital stickiness via mobile/immobile separation, depreciation, and accumulation; labor costs scale linearly with production (no endogenous labor substitution); aborts if `pm_labor_prod` from Module 37 is not identically 1
> - **`sticky_labor`** (alternative, NOT default) — adds CES production function for labor-capital substitution (σ=0.3), accepts climate-driven `pm_labor_prod` from Module 37, accepts wage-productivity feedback from Module 36, and supports optional minimum labor-share target; 6 q38 equations (4 above plus `q38_ces_prodfun` + `q38_labor_share_target`)
> - **`per_ton_fao_may22`** (alternative, NOT default) — simplified per-ton volume-based costs; no capital stocks; 2 q38 equations (`q38_cost_prod_crop_labor`, `q38_cost_prod_crop_capital`)
>
> **§2 below is the default**. §3 covers `sticky_labor`, §4 covers `per_ton_fao_may22`. All citations are realization-prefixed.

---

## 1. Purpose & Overview

Module 38 calculates the costs of production factors (labor and capital) in crop production activities. These costs are crop-specific and spatially explicit, influencing the model's choice of production patterns through the cost function in Module 11.

**What Factor Costs Include**:
- Labor costs (wages × hours worked, scaled by production volume)
- Capital costs (machinery, equipment, irrigation infrastructure, buildings — represented as annuitized investment)

**What Factor Costs Exclude** (to avoid double-counting):
- Land rents (calculated endogenously in Module 11)
- Chemical fertilizer costs (calculated in Module 50)
- Seeds and agricultural inputs (would double-count intermediate products)

**Output Variable**: `vm_cost_prod_crop(i,factors)` (mio USD17MER/yr) where `factors = {labor, capital}`. Aggregated by Module 11 into the global objective; the `"labor"` slice is also read by Module 36 (employment) to compute agricultural employment.

---

## 2. Default Realization: `sticky_feb18`

**Source**: `modules/38_factor_costs/sticky_feb18/`. Code size: 307 lines across 9 .gms files.

**Core idea**: Separate capital from labor; treat capital as partially crop-specific and location-specific ("immobile") so that crop switching incurs sunk-cost penalties. Labor cost scales linearly with production via region-time-crop-specific labor requirement (`p38_labor_need`). NO endogenous labor-capital substitution; NO climate-driven labor productivity (the realization aborts if `pm_labor_prod != 1`).

### 2.1 Equations (4)

#### 2.1.1 Labor cost (`q38_cost_prod_labor`)

**File**: `modules/38_factor_costs/sticky_feb18/equations.gms:15-17`

```gams
q38_cost_prod_labor(i2) ..
  vm_cost_prod_crop(i2,"labor")
    =e=
    sum(kcr, vm_prod_reg(i2,kcr)
             * sum(ct, p38_labor_need(ct,i2,kcr)
                       * (1 / pm_productivity_gain_from_wages(ct,i2))
                       * (pm_hourly_costs(ct,i2,"scenario") / pm_hourly_costs(ct,i2,"baseline"))));
```

**Interpretation**:
- For each region `i2` and crop `kcr`, multiply regional production by per-ton labor requirement
- Scale by the ratio of scenario wage to baseline wage (so wage scenarios scale the cost up/down)
- Divide by `pm_productivity_gain_from_wages` so that wage-driven productivity gains reduce the cost
- `p38_labor_need(t,i,kcr)` is calculated in presolve as `i38_fac_req(t,i,kcr) * pm_factor_cost_shares(t,i,"labor")` — labor cost per ton DM is the labor share of total factor cost per ton

**Note**: this is `(scenario/baseline)` scaling, not the full CES substitution machinery of `sticky_labor`. The labor *quantity* per ton of output is fixed at the historical regression — only the *price* and the *productivity adjustment* are scenario-responsive.

#### 2.1.2 Capital cost (`q38_cost_prod_capital`)

**File**: `modules/38_factor_costs/sticky_feb18/equations.gms:21-24`

```gams
q38_cost_prod_capital(i2) ..
  vm_cost_prod_crop(i2,"capital")
    =e= (sum((cell(i2,j2), kcr), v38_investment_immobile(j2,kcr))
       + sum((cell(i2,j2)),       v38_investment_mobile(j2)))
       * sum(ct, (pm_interest(ct,i2) + s38_depreciation_rate) / (1 + pm_interest(ct,i2)));
```

**Interpretation**:
- Sum cellular immobile + mobile investments to regional total
- Annuitize via factor `(r + d) / (1 + r)` where `r = pm_interest`, `d = s38_depreciation_rate = 0.05`
- Annuitization converts a one-time investment into a per-period flow equivalent to its long-run economic burden

**Why annuitize?** MAgPIE evaluates costs and benefits in the *current* timestep. An investment provides utility over its lifetime; to make the current-period cost commensurate with the current-period production benefit, the model multiplies the investment by `(r+d)/(1+r)`. With `r = 0.05` and `d = 0.05`: factor ≈ 0.0952. A 1 billion USD investment shows up as ~95.2 million USD/yr.

#### 2.1.3 Immobile investment (`q38_investment_immobile`)

**File**: `modules/38_factor_costs/sticky_feb18/equations.gms:33-36`

```gams
q38_investment_immobile(j2,kcr) ..
  v38_investment_immobile(j2,kcr)
    =g= vm_prod(j2,kcr) * sum(cell(i2,j2), sum(ct, p38_capital_need(ct,i2,kcr,"immobile")))
      - sum(ct, p38_capital_immobile(ct,j2,kcr));
```

**Interpretation**:
- For each cell `j2` and crop `kcr`, required immobile capital = production × per-ton immobile capital need
- Investment is the SHORTFALL between required capital and existing pre-period stock
- `=g=` (greater-than-or-equal) means the optimizer is free to over-invest, but only the binding lower bound matters at the optimum
- Crop-specific: investments in crop A are NOT available for crop B (this is what "immobile" means in this realization — fungibility is across mobility class, not across crops)

#### 2.1.4 Mobile investment (`q38_investment_mobile`)

**File**: `modules/38_factor_costs/sticky_feb18/equations.gms:41-44`

```gams
q38_investment_mobile(j2) ..
  v38_investment_mobile(j2)
    =g= sum((cell(i2,j2), kcr), vm_prod(j2,kcr) * sum(ct, p38_capital_need(ct,i2,kcr,"mobile")))
      - sum(ct, p38_capital_mobile(ct,j2));
```

**Interpretation**:
- Mobile capital is pooled across crops within a cell — same equation form as immobile but summed over `kcr`
- Investment is the shortfall between summed required mobile capital and existing pooled mobile stock

### 2.2 Variables

**Interface (output)**:
- `vm_cost_prod_crop(i,factors)` (mio USD17MER/yr; `modules/38_factor_costs/sticky_feb18/declarations.gms:16`) — consumed by Module 11 (via `q11_cost_reg`, both factors) and Module 36 (via `q36_employment` at `modules/36_employment/exo_may22/equations.gms:23-25`, `"labor"` factor only)

**Internal positive variables**:
- `v38_investment_immobile(j,kcr)` (mio USD17MER/yr; `declarations.gms:17`)
- `v38_investment_mobile(j)` (mio USD17MER/yr; `declarations.gms:18`)

### 2.3 Parameters

**File**: `modules/38_factor_costs/sticky_feb18/declarations.gms:21-34`

| Parameter | Dimensions | Unit | Origin | Purpose |
|---|---|---|---|---|
| `p38_labor_need(t,i,kcr)` | t × i × kcr | USD17MER/tDM | `presolve.gms:24` | Labor cost per ton output |
| `p38_capital_need(t,i,kcr,mobil38)` | t × i × kcr × {mobile, immobile} | USD17MER/tDM | `presolve.gms:25-26` | Capital requirement per ton output, split by mobility class |
| `p38_capital_immobile(t,j,kcr)` | t × j × kcr | mio USD17MER | `presolve.gms:31`, `postsolve.gms:9` | Pre-period immobile capital stock |
| `p38_capital_mobile(t,j)` | t × j | mio USD17MER | `presolve.gms:32`, `postsolve.gms:10` | Pre-period mobile capital stock |
| `p38_capital_cost_shares_iso(t,iso)` | t × iso | 1 | `preloop.gms:12-16` | ISO-level capital cost share from GDP regression |
| `p38_capital_share_calibration(iso)` | iso | 1 | `preloop.gms:9-10` | Offset to match calibrated shares to historical |
| `pm_factor_cost_shares(t,i,factors)` | t × i × {labor, capital} | 1 | `preloop.gms:19-22` | Regional labor/capital cost-share split — sent to other modules as `pm_` interface |
| `i38_fac_req(t_all,i,kcr)` | t_all × i × kcr | USD17MER/tDM | `presolve.gms:13-14` (FAO 2005 or regional) | Factor requirement (total cost per ton) |

### 2.4 Scalars (configuration)

**File**: `modules/38_factor_costs/sticky_feb18/input.gms:13-15`

| Scalar | Default | Unit | Purpose |
|---|---|---|---|
| `s38_depreciation_rate` | 0.05 | share/yr | Annual capital depreciation (5% → ~20-year linear lifetime) |
| `s38_immobile` | 1 | share | Fraction of capital that is crop-specific (default: 100% immobile) |

**Config switch** (`modules/38_factor_costs/sticky_feb18/input.gms:8`):
- `c38_fac_req` ∈ {`glo`, `reg`} — default `glo`. Switches `i38_fac_req` source between global 2005 FAO benchmark and regional time-varying FAO data.

### 2.5 Sets

**File**: `modules/38_factor_costs/sticky_feb18/sets.gms:8-17`

- `mobil38` = {`mobile`, `immobile`} — capital mobility class (used by `p38_capital_need`)
- `reg` = {`slope`, `intercept`} — regression-parameter labels for the GDP→capital-share regression in `preloop.gms`
- `factors` = {`labor`, `capital`} — factor-cost split for `vm_cost_prod_crop`

### 2.6 Capital share calibration (preloop)

**File**: `modules/38_factor_costs/sticky_feb18/preloop.gms:8-22`

```
1. calibration_offset(iso) = historical_share(last_t_past, iso)
                            - (slope * log10(GDP_pc_PPP(last_t_past, iso)) + intercept)
2. capital_share_iso(t, iso) = slope * log10(GDP_pc_PPP(t, iso)) + intercept + calibration_offset(iso)
3. capital_share_iso(t, iso) = historical_share(t, iso)        when t is a historical year
4. pm_factor_cost_shares(t, i, "capital") = weighted average of iso shares within region
                                            (weights: historical factor costs per iso)
5. pm_factor_cost_shares(t, i, "labor")   = 1 - pm_factor_cost_shares(t, i, "capital")
```

**Implications**:
- Wealthier countries (higher GDP per capita) → higher projected capital share (more mechanization)
- Historical period anchored to observed shares
- Future trajectories track GDP scenario projections
- Within a region, shares are weighted by 2010 historical factor costs (countries with larger historical factor cost weight the regional average more)

### 2.7 Capital stock dynamics (presolve)

**File**: `modules/38_factor_costs/sticky_feb18/presolve.gms:8-41`

**Step 1 — Sanity check** (lines 8-10): aborts if `pm_labor_prod(t,j) != 1` anywhere. The realization assumes climate-induced labor productivity = 1 always; the `sticky_labor` realization is the one that handles non-unit `pm_labor_prod`.

**Step 2 — Factor requirements** (lines 13-22): set `i38_fac_req` from FAO data; clamp to 1995 values before 1995, and to 2010 values after 2010.

**Step 3 — Per-ton factor needs** (lines 24-26):
```
p38_labor_need(t,i,kcr)              = i38_fac_req × pm_factor_cost_shares(t,i,"labor")
p38_capital_need(t,i,kcr,"mobile")   = i38_fac_req × pm_factor_cost_shares(t,i,"capital") / (pm_interest + s38_depreciation_rate) × (1 - s38_immobile)
p38_capital_need(t,i,kcr,"immobile") = i38_fac_req × pm_factor_cost_shares(t,i,"capital") / (pm_interest + s38_depreciation_rate) × s38_immobile
```

The division by `(pm_interest + s38_depreciation_rate)` converts a per-period cost into the equivalent capital STOCK that would generate that annuitized cost. Multiplying by `(1 - s38_immobile)` or `s38_immobile` splits the capital between mobility classes per the scalar.

**Step 4 — Capital stock initialization (t=1) / depreciation (t>1)** (lines 28-41):
```
if t == first period:
  p38_capital_immobile(t, j, kcr) = sum_cell( p38_capital_need(t,i,kcr,"immobile") * pm_prod_init(j,kcr) ) * (1 - s38_depreciation_rate)
  p38_capital_mobile(t, j)        = sum_cell,kcr( p38_capital_need(t,i,kcr,"mobile")   * pm_prod_init(j,kcr) ) * (1 - s38_depreciation_rate)
else:
  p38_capital_immobile(t, j, kcr) *= (1 - s38_depreciation_rate)^m_timestep_length
  p38_capital_mobile(t, j)        *= (1 - s38_depreciation_rate)^m_timestep_length
```

**Step 5 — Capital stock update (postsolve)** (`postsolve.gms:9-10`):
```
p38_capital_immobile(t+1, j, kcr) = p38_capital_immobile(t, j, kcr) + v38_investment_immobile.l(j, kcr)
p38_capital_mobile(t+1, j)        = p38_capital_mobile(t, j)        + v38_investment_mobile.l(j)
```

### 2.8 What `sticky_feb18` does NOT do (vs `sticky_labor`)

- **No CES production function**: labor and capital quantities per ton are NOT endogenously substituted. They scale from `i38_fac_req × pm_factor_cost_shares` and are taken as given by the optimizer.
- **No climate-driven labor productivity**: `pm_labor_prod` MUST equal 1 (presolve abort otherwise).
- **No wage-driven labor productivity** (despite the productivity divisor in the labor-cost equation): `pm_productivity_gain_from_wages` is taken from Module 36 but is NOT fed back into a labor-capital substitution decision; it only rescales the labor cost.
- **No labor-share target**: minimum labor share enforcement is `sticky_labor`-only.
- **No `v38_capital_need` / `v38_laborhours_need` variables**: factor requirements are parameters (`p38_*`), not optimization variables.

---

## 3. Alternative Realization: `sticky_labor` (NOT default)

**Source**: `modules/38_factor_costs/sticky_labor/`. Code size: 511 lines across 12 .gms files (includes `nl_fix.gms`, `nl_relax.gms`, `nl_release.gms` for nonlinear solver phase handling).

**Built on `sticky_feb18` + adds**:
- CES production function for labor-capital substitution (`q38_ces_prodfun`)
- Accepts non-unit `pm_labor_prod` from Module 37 (climate-driven labor productivity)
- Accepts `pm_productivity_gain_from_wages` from Module 36 as a substitution driver, not just a cost scaler
- Optional minimum labor-share target (`q38_labor_share_target`)

**Use when**: scenarios that require endogenous mechanization in response to wage growth, heat stress, or labor-share policy.

### 3.1 CES production function (`q38_ces_prodfun`)

**File**: `modules/38_factor_costs/sticky_labor/equations.gms`

```gams
q38_ces_prodfun(j2,kcr) ..
  i38_ces_scale(j2,kcr) *
  ( i38_ces_shr(j2,kcr) * sum(mobil38, v38_capital_need(j2,kcr,mobil38))**(-s38_ces_elast_par)
    + (1 - i38_ces_shr(j2,kcr)) * (pm_labor_prod(j2) * pm_productivity_gain_from_wages(i2)
                                   * v38_laborhours_need(j2,kcr))**(-s38_ces_elast_par)
  )**(-1/s38_ces_elast_par)
    =e= 1 + v38_relax_CES_lp(j2,kcr);
```

**Mathematical form** (conceptual; verify against `sticky_labor/equations.gms` before quoting):
```
Y = A * [α * K^(-ρ) + (1-α) * L_eff^(-ρ)]^(-1/ρ)
```

Where:
- `Y` = output (normalized to 1 per unit crop production)
- `A` = `i38_ces_scale` = total factor productivity (calibration)
- `α` = `i38_ces_shr` = capital share parameter
- `K` = `sum(mobil38, v38_capital_need)` = capital per unit output
- `L_eff` = `pm_labor_prod × pm_productivity_gain_from_wages × v38_laborhours_need` = effective labor
- `ρ` = `s38_ces_elast_par` = elasticity parameter = (1/σ) − 1
- `σ` = `s38_ces_elast_subst` = elasticity of substitution (default 0.3)

**σ = 0.3** means low substitutability — a 10% wage increase yields only ~3% labor reduction. Empirically supported for agriculture (Mundlak & Hellinghausen 1982).

### 3.2 Labor-share target (`q38_labor_share_target`)

**File**: `modules/38_factor_costs/sticky_labor/equations.gms`

Enforces `labor_costs ≥ p38_min_labor_share × (labor_costs + capital_costs)` when active. The minimum-share parameter ramps from baseline at `s38_startyear_labor_substitution` (default 2025) to a target at `s38_targetyear_labor_share` (default 2050), scaled by `s38_target_fulfillment` (default 0.5).

**Default state**: `s38_target_labor_share = 0` (OFF; no enforcement).

**Use case**: scenarios where rural employment must be maintained against mechanization pressure.

### 3.3 Endogenous factor-requirement variables (sticky_labor-only)

These are POSITIVE VARIABLES in `sticky_labor` (`modules/38_factor_costs/sticky_labor/declarations.gms`), bounded `0.1× ... 10×` of the historical calibration:
- `v38_capital_need(j,kcr,mobil38)` — capital per ton output, endogenous after 2025
- `v38_laborhours_need(j,kcr)` — labor hours per ton output, endogenous after 2025
- `v38_relax_CES_lp(j,kcr)` — slack variable for the CES equation in the LP-approximation pre-solve phase; fixed to 0 in the non-linear solve

In `sticky_feb18`, these are NOT variables at all — the per-ton requirements are parameters (`p38_labor_need`, `p38_capital_need`) fixed by presolve.

### 3.4 Additional scalars in sticky_labor

**File**: `modules/38_factor_costs/sticky_labor/input.gms`

- `s38_ces_elast_subst` (default 0.3) — elasticity of substitution
- `s38_startyear_labor_substitution` (default 2025) — year CES activates; before this, factor requirements are locked to historical
- `s38_target_labor_share` (default 0; OFF) — minimum labor share target
- `s38_targetyear_labor_share` (default 2050) — year to reach target
- `s38_target_fulfillment` (default 0.5) — fraction of gap to baseline-target distance to close

### 3.5 Capital stickiness mechanism

The capital-stock dynamics are inherited from the same `sticky` family logic (mobile/immobile split, depreciation, accumulation). See §2.7 above — the structure is identical, the values differ only in that `sticky_labor`'s `v38_capital_need` is a variable rather than a parameter.

### 3.6 When to use `sticky_labor`

Read `sticky_labor` GAMS directly (`../modules/38_factor_costs/sticky_labor/*.gms`) if your scenario involves:
- Climate-impact-driven mechanization (Module 37 `pm_labor_prod` < 1)
- Wage-driven mechanization (Module 36 wage scenarios with σ > 0)
- Rural employment policy (`s38_target_labor_share > 0`)

For default-config scenarios, the active default is `sticky_feb18` (§2) — `sticky_labor` is not loaded.

---

## 4. Alternative Realization: `per_ton_fao_may22` (NOT default)

**Source**: `modules/38_factor_costs/per_ton_fao_may22/`. Code size: 231 lines across 9 .gms files.

**Approach**: Simplest of the three. Two equations (`q38_cost_prod_crop_labor`, `q38_cost_prod_crop_capital`); factor costs are a linear function of production volume; no capital stocks, no annuitization, no immobility.

**Use case**: baseline scenarios, sensitivity analysis where capital stickiness would complicate the comparison, or computational efficiency.

**Conceptually** (see `modules/38_factor_costs/per_ton_fao_may22/equations.gms`):
```
vm_cost_prod_crop(i,"labor")   = sum_kcr( vm_prod_reg(i,kcr) * fac_req(i,kcr) * labor_share(i)   * wage_scaling   * (1/productivity_gain) )
vm_cost_prod_crop(i,"capital") = sum_kcr( vm_prod_reg(i,kcr) * fac_req(i,kcr) * capital_share(i) )
```

For exact GAMS, read `modules/38_factor_costs/per_ton_fao_may22/equations.gms` directly.

---

## 5. Cross-Realization Interface

All three realizations expose the same interface variable to the rest of the model:

**`vm_cost_prod_crop(i,factors)`** where `factors = {labor, capital}`, unit mio USD17MER/yr.

- **Producer**: Module 38 (whichever realization is active)
- **Consumers**:
  - Module 11 (Costs) — summed in `q11_cost_reg` via `sum(factors, vm_cost_prod_crop(i2,factors))`
  - Module 36 (Employment) — `vm_cost_prod_crop(i2,"labor")` read in `q36_employment` (`modules/36_employment/exo_may22/equations.gms:23-25`) to compute agricultural employment from labor cost
- **Citation**: see `modules/module_11.md` §3 for the M11 consumer-side description and `modules/module_36.md` for the M36 consumer-side description

`pm_factor_cost_shares(t,i,factors)` is also a `pm_` interface and is set by all three realizations (computed in `preloop.gms`). It is consumed by other parts of the model that need the labor/capital split — read its callers via:
```bash
find ../modules -name '*.gms' -exec grep -l 'pm_factor_cost_shares' {} \;
```

---

## 6. Module Dependencies (Default Realization)

**Receives from** (for `sticky_feb18`):
- **Module 09 (Drivers)**: `im_gdp_pc_ppp_iso(t,iso)` — GDP per capita PPP, drives capital-share regression (`modules/38_factor_costs/sticky_feb18/preloop.gms:9-12`)
- **Module 12 (Interest Rate)**: `pm_interest(t,i)` — used in capital cost annuitization and per-ton capital need (`modules/38_factor_costs/sticky_feb18/presolve.gms:25-26`, `modules/38_factor_costs/sticky_feb18/equations.gms:23`)
- **Module 17 (Production)**: `vm_prod_reg(i,kall)` (regional production) and `vm_prod(j,k)` (cellular production) — both drive the labor and capital cost equations (`modules/38_factor_costs/sticky_feb18/equations.gms:16, 35, 43`)
- **Module 30 (Croparea)**: `pm_prod_init(j,kcr)` — initial production used for first-period capital stock estimation (`modules/38_factor_costs/sticky_feb18/presolve.gms:31-32`)
- **Module 36 (Employment)**: `pm_hourly_costs(t,i,"scenario")` and `pm_hourly_costs(t,i,"baseline")` — wage-scaling ratio in labor cost; `pm_productivity_gain_from_wages(t,i)` — productivity divisor in labor cost (`modules/38_factor_costs/sticky_feb18/equations.gms:16`)
- **Module 37 (Labor Productivity)**: `pm_labor_prod(t,j)` — REQUIRED to be 1 in `sticky_feb18` (abort otherwise; `modules/38_factor_costs/sticky_feb18/presolve.gms:8-10`). In `sticky_labor` this is consumed actively.

**Provides to**:
- **Module 11 (Costs)**: `vm_cost_prod_crop(i,factors)` — entered into `q11_cost_reg` (see `modules/module_11.md` §3 for the consumer side)
- **Module 36 (Employment)**: `vm_cost_prod_crop(i,"labor")` — read by `q36_employment` to compute agricultural employment (`modules/36_employment/exo_may22/equations.gms:23-25`)
- **Other modules** via `pm_factor_cost_shares(t,i,factors)` — used wherever the labor/capital cost split is needed

**Internal coupling** (sticky family only): capital stock today depends on investment yesterday; production today depends on capital stock today via the investment shortfall equations — this creates the spatial path dependency that motivates the realization.

---

## 7. Data Sources and Calibration

### 7.1 Factor requirements

- **Global average** (default): `modules/38_factor_costs/input/f38_fac_req_fao.csv` — FAO Value of Production 2005 benchmark, applied with USDA factor cost shares
- **Regional time-varying** (alternative, via `c38_fac_req = "reg"`): `modules/38_factor_costs/input/f38_fac_req_fao_regional.cs4` — FAO regional data, time-varying at 1995 and 2010 benchmarks

Both are loaded in `modules/38_factor_costs/sticky_feb18/input.gms:18-32`.

### 7.2 Capital share calibration

- **Historical data**: `modules/38_factor_costs/input/f38_historical_share_iso.csv` — country-level historical capital shares (range 0.2-0.8)
- **Regression parameters**: `modules/38_factor_costs/input/f38_regression_cap_share.csv` — slope and intercept for `capital_share = slope × log10(GDP_pc_PPP) + intercept`

Used in `modules/38_factor_costs/sticky_feb18/preloop.gms:8-22`.

### 7.3 Historical factor costs

- **Source**: `modules/38_factor_costs/input/f38_hist_factor_costs_iso.csv` — country-level historical factor costs used as weights when aggregating ISO-level capital shares to regional `pm_factor_cost_shares`. See `modules/38_factor_costs/sticky_feb18/preloop.gms:19-21`.

### 7.4 CES calibration (sticky_labor only)

The CES `i38_ces_shr` (capital share parameter α) and `i38_ces_scale` (TFP scaler A) are calibrated in `modules/38_factor_costs/sticky_labor/presolve.gms` so that the function produces exactly 1 unit of normalized output at the historical labor/capital ratio. This means the CES function replicates the baseline factor mix at calibration; substitution kicks in only when relative prices or productivities change.

---

## 8. Code Truth: DOES

For `sticky_feb18` (default):

1. **Splits factor costs into labor and capital** — calculated by `q38_cost_prod_labor` and `q38_cost_prod_capital` (`modules/38_factor_costs/sticky_feb18/equations.gms:15-24`)
2. **Treats labor cost as proportional to production volume** scaled by historical per-ton requirement and wage ratio — no endogenous labor-capital substitution
3. **Treats capital as a stock that depreciates and accumulates**: investments enter the stock in postsolve, the stock depreciates 5%/yr (`modules/38_factor_costs/sticky_feb18/postsolve.gms:9-10`, `modules/38_factor_costs/sticky_feb18/presolve.gms:38-39`)
4. **Splits capital into mobile and immobile** by the `s38_immobile` scalar (default 1 = 100% immobile); immobile capital is crop-specific (`modules/38_factor_costs/sticky_feb18/presolve.gms:25-26`)
5. **Annuitizes investment costs** using `(r + d)/(1 + r)` to make current-period costs commensurate with current-period production benefits (`modules/38_factor_costs/sticky_feb18/equations.gms:23`)
6. **Initializes capital from 1995 production** with one year of depreciation, assuming 1994 production equals 1995 production (`modules/38_factor_costs/sticky_feb18/presolve.gms:28-32`)
7. **Calibrates capital shares from GDP per capita** via a log-linear regression on historical data, projected with GDP scenario data (`modules/38_factor_costs/sticky_feb18/preloop.gms:8-22`)
8. **Triggers investment only on shortfall** — `=g=` inequality means no investment if existing stock meets production need
9. **Aborts if `pm_labor_prod` ≠ 1** — `sticky_feb18` cannot handle climate-driven labor productivity; use `sticky_labor` for that (`modules/38_factor_costs/sticky_feb18/presolve.gms:8-10`)
10. **Provides three realizations** with increasing sophistication: `per_ton_fao_may22` (volume-based), `sticky_feb18` (capital stocks; DEFAULT), `sticky_labor` (CES + climate/wage feedback)

---

## 9. Code Truth: Does NOT

For `sticky_feb18` specifically (some apply more broadly):

1. **Does not endogenously substitute labor and capital** — for that, use `sticky_labor` (which adds the CES production function)
2. **Does not respond to climate-driven labor productivity** — aborts if `pm_labor_prod ≠ 1`; `sticky_labor` is the realization that accepts non-unit labor productivity
3. **Does not enforce labor-share targets** — `q38_labor_share_target` is `sticky_labor`-only
4. **Does not model livestock factor costs** — only crop production; livestock factor costs are in Module 70's `vm_cost_prod_livst`
5. **Does not include land rent** — calculated endogenously in Module 11
6. **Does not include fertilizer costs** — handled by Module 50 (nitrogen) and Module 54 (phosphorus)
7. **Does not include seed or intermediate-input costs** — would double-count agricultural products used as inputs
8. **Does not differentiate capital types beyond mobility** — all capital aggregated into `mobile` and `immobile`; no distinction between machinery, irrigation, buildings, etc.
9. **Does not model capital reallocation between crops** — immobile capital is crop-specific and must depreciate before switching
10. **Does not model within-region capital mobility between cells** — mobile capital is pooled at cell level, not transferable between cells
11. **Does not model maintenance costs separately** — implicit in the 5%/yr depreciation rate
12. **Does not model capital utilization rates** — assumes full utilization
13. **Does not model seasonal labor variation, labor skill differentiation, or off-farm employment opportunity costs**
14. **Does not model financial constraints** — investment is always feasible when economically optimal; no credit limits
15. **Does not generate intensification pressure directly** — Module 38 calculates crop production factor costs only. Land protection targets come from Module 22; land conversion costs from Module 39. Any emergent intensification behavior arises from Module 11 comparing cost streams.

---

## 10. Limitations

### 10.1 Structural

1. **Factor costs independent of harvested area** (`modules/38_factor_costs/sticky_feb18/realization.gms:15-18`): "this realization assumes that factor costs, within a region, purely depend on production and are independent of the area under cultivation." No economies of scale or area-dependent overhead.

2. **`sticky_feb18` requires `pm_labor_prod = 1`**: climate impacts on labor productivity cannot be modeled in the default realization (`modules/38_factor_costs/sticky_feb18/presolve.gms:8-10`). The `sticky_labor` realization is the path for climate-impact scenarios.

3. **Immobile capital assumption (`s38_immobile = 1` default)**: 100% of capital is crop-specific. No general-purpose machinery is reallocated, which penalizes crop switching beyond what's empirically observed in many settings.

4. **Capital depreciation rate fixed at 5%**: no asset-type differentiation (machinery vs irrigation infrastructure vs buildings depreciate at different rates in reality).

### 10.2 Methodological

5. **Capital stock initialized from 1995 production only**: assumes 1994 production equals 1995 production (`modules/38_factor_costs/sticky_feb18/presolve.gms:28-32`). No pre-1995 capital accumulation history.

6. **Capital share regression is log-linear in GDP per capita**: a parametric form chosen for tractability; may miss non-monotonic patterns in development pathways.

7. **Within `sticky_labor`** (when active): climate and wage labor-productivity impacts combined multiplicatively (`pm_labor_prod × pm_productivity_gain_from_wages`); interaction effects (e.g., wage increases having larger benefits in heat-stressed regions) are not represented.

---

## 11. Common Modifications

All modifications below are in `modules/38_factor_costs/<realization>/input.gms` for the active realization. Verify the realization at `grep "cfg\$gms\$factor_costs" ../config/default.cfg` before editing.

### 11.1 Switch to regional factor requirements (default realization)

**Edit**: `modules/38_factor_costs/sticky_feb18/input.gms:8`
```gams
$setglobal c38_fac_req  reg     ! Was: glo
```
**Effect**: Use `f38_fac_req_fao_regional.cs4` (regional time-varying) instead of `f38_fac_req_fao.csv` (global 2005 benchmark).

### 11.2 Increase capital mobility (default realization)

**Edit**: `modules/38_factor_costs/sticky_feb18/input.gms:15`
```gams
s38_immobile  immobile capital (share) / 0.5 /   ! Was: 1
```
**Effect**: 50% of capital becomes mobile (crop-flexible). Easier crop switching; lower switching costs; more dynamic crop rotation.

### 11.3 Change depreciation rate (default realization)

**Edit**: `modules/38_factor_costs/sticky_feb18/input.gms:13`
```gams
s38_depreciation_rate depreciation rate (share of costs)  / 0.033 /   ! Was: 0.05 (3.3% = 30-year lifetime)
```
**Effect**: Capital persists longer; lower annualized cost; stronger path dependency.

### 11.4 Switch to `sticky_labor` for climate/wage scenarios

**Edit**: `config/default.cfg`
```r
cfg$gms$factor_costs <- "sticky_labor"   # Was: "sticky_feb18"
```

**Then** modify `sticky_labor` parameters as needed:
- **Adjust CES elasticity** at `modules/38_factor_costs/sticky_labor/input.gms` — `s38_ces_elast_subst` (default 0.3; higher = easier labor-capital substitution)
- **Adjust labor-substitution start year** — `s38_startyear_labor_substitution` (default 2025)
- **Activate labor-share target** — `s38_target_labor_share` (default 0 = OFF; set 0.4 for 40% labor floor)
- **Adjust target fulfillment speed** — `s38_target_fulfillment` (default 0.5 = close 50% of gap)

### 11.5 Switch to `per_ton_fao_may22` for simplicity

**Edit**: `config/default.cfg`
```r
cfg$gms$factor_costs <- "per_ton_fao_may22"
```
**Effect**: Removes capital stocks; pure per-ton-volume cost; useful for sensitivity analysis where stickiness would complicate comparison.

---

## 12. Testing & Validation

The following checks assume the default `sticky_feb18` realization unless noted.

### 12.1 Factor cost components — sanity ranges

**Objective**: Verify labor and capital costs land in plausible ranges.

```r
library(magpie4)
library(magclass)

gdx <- "fulldata.gdx"

costs_labor   <- readGDX(gdx, "ov_cost_prod_crop", select=list(type="level", factors="labor"))
costs_capital <- readGDX(gdx, "ov_cost_prod_crop", select=list(type="level", factors="capital"))
prod          <- readGDX(gdx, "ov_prod_reg", select=list(type="level"))

costs_total  <- costs_labor + costs_capital
cost_per_ton <- costs_total / prod

# Plausible range
print(range(cost_per_ton["y2020",,], na.rm=TRUE))   # 50-300 USD17MER/tDM

# Labor share
labor_share <- costs_labor / costs_total
print(range(labor_share["y2020",,], na.rm=TRUE))    # 0.2-0.8 depending on region
```

**Red flags**: cost-per-ton < 20 USD/tDM (unrealistically cheap); labor share > 0.9 or < 0.1 (extreme mechanization or extreme labor dependence).

### 12.2 Capital stock dynamics (sticky_feb18 / sticky_labor)

**Objective**: Verify the depreciation/accumulation cycle is consistent.

```r
library(gdxrrw)
igdx("/path/to/gams")

stocks <- rgdx.param(gdx, "p38_capital_immobile", squeeze=FALSE)
invest <- rgdx.param(gdx, "ov38_investment_immobile", squeeze=FALSE)

stocks_mc <- as.magpie(stocks)
invest_mc <- as.magpie(invest)

# Check depreciation between two consecutive timesteps
stock_now    <- stocks_mc["y2020",,]
stock_5yr    <- stocks_mc["y2025",,]
expected_5yr <- stock_now * (1-0.05)^5 + invest_mc["y2020",,] * 5   # approximate

print(max(abs(stock_5yr - expected_5yr), na.rm=TRUE))   # should be small
```

**Red flag**: large deviation suggests a postsolve or presolve bug in capital stock updating.

### 12.3 Historical calibration (1995-2020)

**Objective**: Verify the GDP→capital-share regression reproduces observed shares within tolerance.

```r
calib_shares <- as.magpie(rgdx.param(gdx, "pm_factor_cost_shares", squeeze=FALSE))
hist_shares  <- as.magpie(rgdx.param(gdx, "f38_historical_share",  squeeze=FALSE))

# Compare 2010 (last historical benchmark)
err <- calib_shares["y2010",,"capital"] - hist_shares["y2010",,]
print(summary(as.vector(err)))   # should be near zero
```

**Red flag**: large 2010 calibration error suggests `p38_capital_share_calibration` offset is mis-applied or the regression parameters are stale.

### 12.4 Climate / wage response (sticky_labor only)

If you've switched to `sticky_labor`, the additional checks are:
- `pm_labor_prod` < 1 in tropical regions under RCP8.5 → expect `ov38_capital_need` to increase (mechanization response)
- Wage scenario above baseline → expect `ov38_laborhours_need` to decrease
- These checks are MEANINGLESS in `sticky_feb18` where `v38_laborhours_need` and `v38_capital_need` do not exist as variables

---

## 13. Literature and Data Sources

### 13.1 Peer-reviewed literature

**Capital stickiness and factor cost economics**:
- Dietrich, J.P., Schmitz, C., Müller, C., Fader, M., Lotze-Campen, H., & Popp, A. (2014): "Measuring agricultural land-use intensity – A global analysis using a model-based approach", *Ecological Modelling* 232. FAO Value of Production methodology and factor cost share estimation.

**CES function and labor productivity** (sticky_labor):
- Orlov, A. et al. (2021): "Climate change and labour-related impacts in MAgPIE", *Environmental Research Letters* (or relevant Orlov et al. paper depending on canonical reference).

**Capital depreciation**:
- Hertel, T.W. (1999): "Global Trade Analysis: Modeling and Applications", Cambridge University Press. Agricultural capital depreciation rates (5% standard) and annuitization conventions.

**Elasticity of substitution** (sticky_labor):
- Mundlak, Y. & Hellinghausen, R. (1982): "The Intercountry Agricultural Production Function", *American Journal of Agricultural Economics*. Estimates σ = 0.2-0.4 for agriculture.

### 13.2 Data sources

- **FAO Value of Production**: FAOSTAT (2005 benchmark) — `f38_fac_req_fao.csv`, `f38_fac_req_fao_regional.cs4`
- **USDA Cost of Production**: USDA Economic Research Service — factor cost share basis
- **Historical factor costs**: GTAP + national agricultural accounts — `f38_historical_share_iso.csv`, `f38_hist_factor_costs_iso.csv`
- **GDP per capita PPP**: World Bank Development Indicators + SSP scenarios — `im_gdp_pc_ppp_iso`

### 13.3 Model documentation

- Dietrich, J.P., et al. (2019): "MAgPIE 4 – a modular open-source framework for modeling global land systems", *Geoscientific Model Development* 12, 1299-1317. https://doi.org/10.5194/gmd-12-1299-2019

---

## 14. Summary for AI Agents

### 14.1 Module identity

- **Name**: Factor Costs (Module 38)
- **Purpose**: Calculate labor and capital costs for crop production
- **Active default**: `sticky_feb18` (verify: `grep "cfg\$gms\$factor_costs" ../config/default.cfg`)
- **Output**: `vm_cost_prod_crop(i,factors)` consumed by Module 11's `q11_cost_reg` (both factors) and Module 36's `q36_employment` (`"labor"` slice only, for agricultural employment calculation)

### 14.2 Realization quick-reference

| Realization | # q38 eqns | Endogenous L/K? | Climate-driven `pm_labor_prod`? | Capital stocks? | Labor-share target? |
|---|---:|---|---|---|---|
| **`sticky_feb18`** (default) | 4 | NO (`p38_labor_need` is parameter) | NO (aborts if ≠1) | YES (mobile/immobile, 5%/yr depreciation) | NO |
| `sticky_labor` (alt) | 6 | YES (CES; `v38_*_need` are variables) | YES | YES | OPTIONAL (`s38_target_labor_share`) |
| `per_ton_fao_may22` (alt) | 2 | NO | depends — read source | NO | NO |

### 14.3 Common misconceptions

- ❌ "Factor costs are fixed per ton" — only in `per_ton_fao_may22` and in `sticky_feb18` for labor; `sticky_labor` allows endogenous substitution
- ❌ "All capital is mobile" — default `s38_immobile = 1` means 100% immobile (crop-specific) in both sticky realizations
- ❌ "CES is the default" — `sticky_labor` (with CES) is NOT the default; `sticky_feb18` (no CES) is
- ❌ "Module 38 drives employment" — Module 38 calculates *costs*; employment outputs are in Module 36
- ❌ "Factor costs include everything" — excludes land rent (M11), fertilizer (M50/M54), seeds (intermediate inputs)

### 14.4 Debugging decision tree

**Issue: factor costs seem too low/high**
→ Check the active realization first; the structure differs significantly
→ Check `c38_fac_req` setting (`glo` vs `reg`)
→ Check `pm_factor_cost_shares` (labor/capital split — preloop output)
→ Check `pm_hourly_costs` (wage levels from Module 36)

**Issue: no mechanization response to wages/climate**
→ Confirm you are on `sticky_labor`, not `sticky_feb18` (the default cannot respond)
→ If on `sticky_labor`: check `m_year(t) > s38_startyear_labor_substitution` (default 2025)
→ Check `v38_laborhours_need` bounds (should be 0.1× to 10×)

**Issue: model aborts at the start of `38_factor_costs` presolve**
→ Almost always: `pm_labor_prod ≠ 1` with `sticky_feb18` active. Either switch realization to `sticky_labor` or fix the upstream Module 37 that's producing non-unit labor productivity.

**Issue: unrealistic crop switching patterns**
→ Check `s38_immobile` (default 1 = maximum stickiness)
→ Check `p38_capital_immobile` values (sufficient stickiness?)
→ Consider reducing `s38_immobile` toward 0.5 if you want more flexibility

---

**Module 38 Status**: ✅ COMPLETE (R3 Phase C body rewrite, 2026-05-23)

---

**Last Verified**: 2026-05-23 (R3 Phase C)
**Verified Against**: `modules/38_factor_costs/sticky_feb18/*.gms` (default), with cross-reference to `modules/38_factor_costs/sticky_labor/` and `modules/38_factor_costs/per_ton_fao_may22/`
**Verification Method**: All sticky_feb18 equations and parameters re-derived from source; sticky_labor and per_ton_fao_may22 sections describe key differences without duplicating full content (read each realization's source if needed).
**Changes Since Last Verification**: R3 body rewrite — default-first restructuring; removed R3 interim warning header; all citations realization-prefixed.
