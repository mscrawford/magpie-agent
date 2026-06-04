# Q2 Answer: Module 37 (Labor Productivity), M38 (Factor Costs), M36 (Employment)

**Question**: In MAgPIE's default config, how does Module 37 (labor productivity) work?
(a) Default realization and what labor productivity drives
(b) M37–M38 interaction: does it scale a labor cost, and which variable?
(c) How M36 (employment) relates

---

## (a) Default Realization and Purpose of pm_labor_prod

**Default realization: `off`**

Confirmed in `config/default.cfg:1214`:
```r
cfg$gms$labor_prod <- "off"         # default = off
```

Under the `off` realization, Module 37 sets:
```gams
pm_labor_prod(t,j) = 1;
```
(🟡 `modules/module_37.md §7.2`, citing `off/preloop.gms:8`)

The parameter `pm_labor_prod(t,j)` is dimensioned over time and the 200 MAgPIE cells. It is a dimensionless multiplier: 1 = no impact, <1 = productivity loss, >1 = gain. With the default `off` realization it is identically 1.0 for all cells and all time periods — heat stress has no effect.

The alternative `exo` realization populates `pm_labor_prod` from `f37_labourprodimpact.cs3`, a 6-dimensional array from the LAMACLIMA project, selecting a climate scenario (RCP1.9 or RCP8.5), productivity metric (ISO or HOTHAPS), work intensity (300W or 400W), and ensemble statistics (enslower / ensmean / ensupper):
```gams
pm_labor_prod(t,j) = f37_labor_prod(t,j,"%c37_labor_rcp%","%c37_labor_metric%",
                                     "%c37_labor_intensity%","%c37_labor_uncertainty%");
```
(🟡 `modules/module_37.md §7.1`, citing `exo/preloop.gms:8`)

This is pure parameterization: rates come from external ESM input data, not from equations computing productivity endogenously. Module 37 has zero GAMS equations and is a pure source (data provider) module.

---

## (b) M37 → M38 Interaction: Which Variable, Which Equation

**`pm_labor_prod(t,j)` is the sole interface from M37 to M38.**
(🟡 `modules/module_37.md §8`, `modules/module_38.md §6`)

### Under the default factor_costs realization (`sticky_feb18`)

`config/default.cfg:1235`:
```r
cfg$gms$factor_costs <- "sticky_feb18"        # default = "sticky_feb18"
```

**`sticky_feb18` does NOT use `pm_labor_prod` to scale any cost.** Instead it aborts the run if `pm_labor_prod` is not identically 1:

> `modules/38_factor_costs/sticky_feb18/presolve.gms:8-10` — abort if `pm_labor_prod(t,j) ≠ 1`

(🟡 `modules/module_38.md §2.3` footnote and §2.8`)

In `sticky_feb18`, labor cost is calculated in `q38_cost_prod_labor` (`modules/38_factor_costs/sticky_feb18/equations.gms:15-17`):
```gams
q38_cost_prod_labor(i2) ..
  vm_cost_prod_crop(i2,"labor")
    =e=
    sum(kcr, vm_prod_reg(i2,kcr)
             * sum(ct, p38_labor_need(ct,i2,kcr)
                       * (1 / pm_productivity_gain_from_wages(ct,i2))
                       * (pm_hourly_costs(ct,i2,"scenario") / pm_hourly_costs(ct,i2,"baseline"))));
```

- `vm_cost_prod_crop(i,"labor")` is the **output variable** (mio USD17MER/yr).
- `pm_labor_prod` does NOT appear in this equation. It is absent from `sticky_feb18`'s labor cost scaling.
- The divisor `pm_productivity_gain_from_wages` comes from **Module 36**, not Module 37. It captures the efficiency-wage effect (default 0 = no effect, so `pm_productivity_gain_from_wages = 1` by default).

So under the default configuration (M37 `off` + M38 `sticky_feb18`): `pm_labor_prod = 1` everywhere, M38 asserts it is 1 (or aborts), and there is no cost effect from M37 at all.

### Under the non-default `sticky_labor` realization (NOT default)

`sticky_labor` is required to run the `exo` heat-stress scenario. It consumes `pm_labor_prod` in the CES production function `q38_ces_prodfun` (`modules/38_factor_costs/sticky_labor/equations.gms:19-23`):
```gams
q38_ces_prodfun(j2,kcr) ..
  i38_ces_scale(j2,kcr) *
  (i38_ces_shr(j2,kcr)*sum(mobil38, v38_capital_need(j2,kcr,mobil38))**(-s38_ces_elast_par) +
  (1 - i38_ces_shr(j2,kcr))*(sum(ct, pm_labor_prod(ct,j2) * sum(cell(i2,j2), pm_productivity_gain_from_wages(ct,i2))) * v38_laborhours_need(j2,kcr))**(-s38_ces_elast_par))**(-1/s38_ces_elast_par)
  =e= 1 + v38_relax_CES_lp(j2,kcr);
```

Here `pm_labor_prod(ct,j2)` multiplies `pm_productivity_gain_from_wages(ct,i2)` to produce effective labor input `L_eff`. `v38_laborhours_need(j2,kcr)` is an **endogenous variable** (labor hours per ton of crop output). Lower `pm_labor_prod` → reduced effective labor → optimizer raises `v38_laborhours_need` (needs more hours) → higher labor cost via `vm_cost_prod_crop(i,"labor")`.

**Summary**:
- Under default config, `pm_labor_prod` is never seen by the optimizer; no variable is scaled.
- Under `sticky_labor` (non-default), `pm_labor_prod` enters `q38_ces_prodfun` and scales the effective labor component `v38_laborhours_need` (endogenous variable for labor hours per ton), indirectly raising `vm_cost_prod_crop(i,"labor")`.
- The final cost variable in both cases is `vm_cost_prod_crop(i,factors)` (mio USD17MER/yr), split into `"labor"` and `"capital"` factors.

---

## (c) Module 36 (Employment) Relationship

**Default realization: `exo_may22`** (`config/default.cfg:1191`):
```r
cfg$gms$employment <- "exo_may22"        # default = "exo_may22"
```

M36 interacts with M37 and M38 along two directions:

### M36 → M38 (upstream provision: wages)

Module 36 provides two parameters to Module 38 (and also M57, M70):

| Parameter | Dimensions | Default behavior |
|---|---|---|
| `pm_hourly_costs(t,i,wage_scen)` | t × i × {baseline, scenario} | GDP-regression wages (USD17MER/hr) |
| `pm_productivity_gain_from_wages(t,i)` | t × i | 1.0 (s36_scale_productivity_with_wage = 0, default) |

`pm_hourly_costs` enters `q38_cost_prod_labor` as the wage-scaling ratio `(scenario/baseline)`. Under default config with no minimum wage, this ratio = 1.0 at baseline, and only diverges when a minimum wage is active.

`pm_productivity_gain_from_wages` enters the divisor of `q38_cost_prod_labor` and, in `sticky_labor`, also multiplies the effective labor in `q38_ces_prodfun`. Default value = 1.0 (no efficiency-wage effect, because `s36_scale_productivity_with_wage = 0`; `modules/module_36.md §2.4`).

### M38 → M36 (downstream provision: labor costs for employment back-calculation)

The `q36_employment` equation in Module 36 (`modules/36_employment/exo_may22/equations.gms:23-25`):
```gams
q36_employment(i2) .. v36_employment(i2) =e=
  (vm_cost_prod_crop(i2,"labor") + vm_cost_prod_livst(i2,"labor") + sum(ct,p36_nonmagpie_labor_costs(ct,i2))) *
  (1 / sum(ct, f36_weekly_hours(ct,i2) * s36_weeks_in_year * pm_hourly_costs(ct,i2,"scenario")));
```

`vm_cost_prod_crop(i,"labor")` — the output variable of Module 38 — is divided by (annual hours × hourly wage) to back-calculate `v36_employment(i)` (mio. people). Employment is therefore a **reporting output**, not an optimization constraint (no labor supply limit).

### Indirect M37 → M36 path

Under the non-default `sticky_labor` + `exo` combination:
- `pm_labor_prod` decreases (heat stress) → `v38_laborhours_need` increases → `vm_cost_prod_crop(i,"labor")` rises → `v36_employment` rises (more labor cost at same wage → more inferred workers).

Under default (`off` + `sticky_feb18`): `pm_labor_prod = 1`, M38 asserts it is 1, no cost increase, no employment effect from heat stress. M36 sets `v36_employment` purely from the optimized labor cost which reflects GDP-driven wages via `pm_hourly_costs`.

### M36 relationship to M37 directly

Module 36 does NOT read `pm_labor_prod` directly. The M37–M36 link is fully mediated through M38's `vm_cost_prod_crop(i,"labor")` output. M37 is a pure source with zero inbound connections and one declared outbound connection (to M38 only).

---

## Key variables and parameters — summary table

| Name | Type | Dim | Origin | Consumer |
|---|---|---|---|---|
| `pm_labor_prod(t,j)` | pm parameter | t × j (200 cells) | M37 (`off/preloop.gms:8` or `exo/preloop.gms:8`) | M38 `sticky_labor` only (`equations.gms:22`) |
| `vm_cost_prod_crop(i,factors)` | vm variable | i × {labor, capital} | M38 (`q38_cost_prod_labor`, `q38_cost_prod_capital`) | M11 (`q11_cost_reg`), M36 (`q36_employment`) |
| `pm_hourly_costs(t,i,wage_scen)` | pm parameter | t × i × scen | M36 (`preloop.gms:49`) | M38, M57, M70 |
| `pm_productivity_gain_from_wages(t,i)` | pm parameter | t × i | M36 (`preloop.gms:63`) | M38, M57, M70 |
| `v38_laborhours_need(j,kcr)` | v variable | j × kcr | M38 `sticky_labor` only (`declarations.gms`) | M38 `q38_ces_prodfun` |
| `v36_employment(i)` | v variable | i | M36 `q36_employment` | Reporting only |

---

## Default config state (summary)

Under `cfg$gms$labor_prod = "off"` + `cfg$gms$factor_costs = "sticky_feb18"` + `cfg$gms$employment = "exo_may22"`:

1. M37 sets `pm_labor_prod = 1` for all t, j. No climate-driven productivity change.
2. M38 `sticky_feb18` checks `pm_labor_prod == 1` (presolve abort otherwise), then ignores it. Labor cost is `vm_cost_prod_crop(i,"labor")` = production × per-ton labor requirement × (scenario/baseline wage ratio) / `pm_productivity_gain_from_wages`. Both ratios default to 1.0, so costs are proportional to production × historical per-ton factor requirement.
3. M36 `exo_may22` provides `pm_hourly_costs` and `pm_productivity_gain_from_wages` (both at baseline = 1.0 divisor by default). After optimization, it back-calculates `v36_employment` from the labor cost output of M38 + M70 + M57.

---

## Documentation gaps (what I wished existed)

One gap worth flagging: the docs note (correctly, in `module_37.md §8.1` "Default-config caveat") that `pm_labor_prod` is consumed only by `sticky_labor`, not `sticky_feb18`, and that the abort exists in `sticky_feb18/presolve.gms:8-10`. However, **there is no dedicated cross-module doc** that shows the full wiring table for the M36–M37–M38 triad in one place — a reader must stitch together §6 of module_38.md, §7.1 of module_37.md, and §7.2 of module_36.md to see the complete signal flow. A short `cross_module/labor_factor_costs_employment.md` covering this triad would reduce Q&A friction significantly.

---

## Source statement

- All factual claims: 🟡 **Based on AI documentation** (`modules/module_37.md`, `modules/module_38.md`, `modules/module_36.md`).
- Default realization confirmations: 🟡 **Cross-checked against `config/default.cfg:1214, 1235, 1191`** (read this session).
- Raw GAMS `.gms` files: NOT opened (per task constraint). Citations to `presolve.gms`, `equations.gms`, etc. are as recorded in the module docs (last verified 2025-10-13 for M36/M37, 2026-05-23 for M38). Line numbers may have shifted since those verification dates.
- No fabricated variable names: all `vm_*`, `pm_*`, `v38_*`, `q38_*` names copied verbatim from documentation.
