# Module 38: Factor Costs — Round 34 Answer

**Question**: How does Module 38 compute factor costs in its default realization, and what is the CES production-function structure? Name the default realization, the q38_* equations, and the vm_cost_prod / vm_factor_costs consumer set.

---

## Default Realization

The default realization is **`sticky_feb18`**, confirmed in `config/default.cfg`:
`cfg$gms$factor_costs <- "sticky_feb18"`.

Source: `modules/module_38.md` §2, with verification note at footer (last verified 2026-05-23 against `modules/38_factor_costs/sticky_feb18/*.gms`).

---

## How `sticky_feb18` Computes Factor Costs

The realization separates factor costs into labor and capital via four equations. There is **no CES production function** in this realization — labor and capital per unit of output are fixed parameters, not endogenous variables.

### Equations (4 total in `sticky_feb18`)

**1. `q38_cost_prod_labor(i2)`**
(`modules/38_factor_costs/sticky_feb18/equations.gms:15-17`)

```
vm_cost_prod_crop(i2,"labor")
  =e=
  sum(kcr, vm_prod_reg(i2,kcr)
           * sum(ct, p38_labor_need(ct,i2,kcr)
                     * (1 / pm_productivity_gain_from_wages(ct,i2))
                     * (pm_hourly_costs(ct,i2,"scenario") / pm_hourly_costs(ct,i2,"baseline"))))
```

Labor cost = production volume x per-ton labor requirement x wage-ratio scaling x inverse productivity gain.
The quantity of labor per ton (`p38_labor_need`) is a parameter fixed in presolve from FAO factor requirements multiplied by the regional labor cost share — it does not respond to relative prices. Only the *price* (wage ratio) and *productivity adjustment* are scenario-responsive.

**2. `q38_cost_prod_capital(i2)`**
(`modules/38_factor_costs/sticky_feb18/equations.gms:21-24`)

```
vm_cost_prod_crop(i2,"capital")
  =e= (sum((cell(i2,j2), kcr), v38_investment_immobile(j2,kcr))
     + sum((cell(i2,j2)),       v38_investment_mobile(j2)))
     * sum(ct, (pm_interest(ct,i2) + s38_depreciation_rate) / (1 + pm_interest(ct,i2)))
```

Capital cost = annuitized sum of cellular investments (immobile + mobile), where the annuity factor `(r + d)/(1 + r)` converts a one-time investment into a per-period flow. With `r = pm_interest ≈ 0.05` and `s38_depreciation_rate = 0.05`, the factor ≈ 0.0952 per year.

**3. `q38_investment_immobile(j2,kcr)`**
(`modules/38_factor_costs/sticky_feb18/equations.gms:33-36`)

```
v38_investment_immobile(j2,kcr)
  =g= vm_prod(j2,kcr) * sum(cell(i2,j2), sum(ct, p38_capital_need(ct,i2,kcr,"immobile")))
    - sum(ct, p38_capital_immobile(ct,j2,kcr))
```

Investment is the **shortfall** between the production-required immobile capital stock and the existing pre-period stock. The `=g=` inequality means the optimizer may over-invest but not under-invest. Capital is crop-specific; investments in crop A cannot serve crop B ("immobile" = not fungible across crops).

**4. `q38_investment_mobile(j2)`**
(`modules/38_factor_costs/sticky_feb18/equations.gms:41-44`)

```
v38_investment_mobile(j2)
  =g= sum((cell(i2,j2), kcr), vm_prod(j2,kcr) * sum(ct, p38_capital_need(ct,i2,kcr,"mobile")))
    - sum(ct, p38_capital_mobile(ct,j2))
```

Same structure as immobile, but mobile capital is pooled across all crops within a cell, so the shortfall check is over the crop sum against a single pooled stock.

### Capital stock dynamics

The capital stocks (`p38_capital_immobile`, `p38_capital_mobile`) are maintained outside the GAMS optimization:
- **Presolve**: stocks depreciate by `(1 - s38_depreciation_rate)^m_timestep_length` each period
- **Postsolve**: solved investment levels are added to the pre-period stock to form the next period's opening stock

### Key scalars

- `s38_depreciation_rate = 0.05` (5%/yr, ~20-year linear lifetime)
- `s38_immobile = 1` (default: 100% of capital is crop-specific; no general-purpose machinery)

### What `sticky_feb18` does NOT do

- No endogenous labor-capital substitution — factor requirements per ton are parameters, not variables
- No CES production function (that is `sticky_labor`-only)
- Aborts in presolve if `pm_labor_prod(t,j) != 1` — cannot handle climate-driven labor productivity changes
- No labor-share enforcement target

---

## CES Production Function Structure

The CES production function is implemented only in the **`sticky_labor` realization (NOT the default)**. It adds equation `q38_ces_prodfun` (plus `q38_labor_share_target` when active), for 6 total equations versus 4 in `sticky_feb18`.

**`q38_ces_prodfun(j2,kcr)`**
(`modules/38_factor_costs/sticky_labor/equations.gms:19-23`)

```
i38_ces_scale(j2,kcr) *
( i38_ces_shr(j2,kcr) * sum(mobil38, v38_capital_need(j2,kcr,mobil38))^(-s38_ces_elast_par)
+ (1 - i38_ces_shr(j2,kcr)) * (sum(ct, pm_labor_prod(ct,j2)
                                       * sum(cell(i2,j2), pm_productivity_gain_from_wages(ct,i2)))
                                       * v38_laborhours_need(j2,kcr))^(-s38_ces_elast_par)
)^(-1/s38_ces_elast_par)
=e= 1 + v38_relax_CES_lp(j2,kcr)
```

Mathematical form: `Y = A * [α·K^(-ρ) + (1-α)·L_eff^(-ρ)]^(-1/ρ)`

| Symbol | GAMS name | Meaning |
|--------|-----------|---------|
| Y | normalized to 1 | output per unit crop production |
| A | `i38_ces_scale` | total factor productivity (calibration) |
| α | `i38_ces_shr` | capital share parameter |
| K | `sum(mobil38, v38_capital_need)` | capital per unit output — **endogenous variable** |
| L_eff | `pm_labor_prod * pm_productivity_gain_from_wages * v38_laborhours_need` | effective labor — **endogenous variable** |
| ρ | `s38_ces_elast_par` = (1/σ) - 1 | CES substitution parameter |
| σ | `s38_ces_elast_subst` = **0.3** (default) | elasticity of substitution |

σ = 0.3 implies low substitutability: a 10% wage increase drives only ~3% labor reduction (consistent with Mundlak & Hellinghausen 1982 for agriculture).

`v38_capital_need` and `v38_laborhours_need` are positive optimization **variables** in `sticky_labor`, bounded 0.1x–10x historical calibration. In `sticky_feb18` these do not exist as variables — the analogous quantities are parameters (`p38_capital_need`, `p38_labor_need`).

---

## Interface Variable and Consumer Set

**Output variable**: `vm_cost_prod_crop(i, factors)` where `factors = {labor, capital}`, unit mio USD17MER/yr.

(`modules/38_factor_costs/sticky_feb18/declarations.gms:16`)

**Consumers**:

1. **Module 11 (Costs)** — `q11_cost_reg` reads `sum(factors, vm_cost_prod_crop(i2,factors))` — both labor and capital factors enter the global cost objective.
   (`modules/11_costs/default/equations.gms:15`)

2. **Module 36 (Employment)** — `q36_employment` reads `vm_cost_prod_crop(i2,"labor")` (the labor slice only) to compute agricultural employment from labor expenditure.
   (`modules/36_employment/exo_may22/equations.gms:23-25`)

Note: the variable is named `vm_cost_prod_crop`, not `vm_factor_costs`. There is no interface variable named `vm_factor_costs` in Module 38.

`pm_factor_cost_shares(t,i,factors)` is a secondary `pm_` interface set in preloop (via a log-linear GDP-per-capita regression), used by other modules needing the labor/capital cost-share split.

---

## Realization Summary Table

| Realization | q38 equations | Endogenous L/K ratio | CES | Capital stocks | Default? |
|---|---|---|---|---|---|
| **`sticky_feb18`** | 4 (`q38_cost_prod_labor`, `q38_cost_prod_capital`, `q38_investment_immobile`, `q38_investment_mobile`) | NO | NO | YES (mobile/immobile, 5%/yr) | **YES** |
| `sticky_labor` | 6 (above + `q38_ces_prodfun` + `q38_labor_share_target`) | YES | YES (σ=0.3) | YES | NO |
| `per_ton_fao_may22` | 2 (`q38_cost_prod_crop_labor`, `q38_cost_prod_crop_capital`) | NO | NO | NO | NO |

---

**Source**: `modules/module_38.md` (last verified 2026-05-23 against `modules/38_factor_costs/sticky_feb18/*.gms`, with cross-reference to `sticky_labor` and `per_ton_fao_may22`)

**Epistemic status**: 🟡 Documented — based on module_38.md documentation read this session. No raw GAMS source read this session (not required for this question; the documentation was verified against source at 2026-05-23). For high-stakes modifications, verify equations.gms line numbers directly as line numbers may drift.
