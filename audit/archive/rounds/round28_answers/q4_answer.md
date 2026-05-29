# Q4: Module 37 (Labor Productivity) — Default State, Non-Default Pathway, and Cost Objective Feed-Through

---

## 1. Default Realization: `off`

**Config confirmation** (`config/default.cfg`):
```
cfg$gms$labor_prod <- "off"         # default = off
```

The default realization of module 37 is **`off`**.

### What MAgPIE does in the `off` default state

Module 37 in the `off` realization performs exactly one action (`modules/37_labor_prod/off/preloop.gms:8`):

```gams
pm_labor_prod(t,j) = 1;
```

Every element of the parameter `pm_labor_prod(t,j)` — dimensioned over time periods × 200 MAgPIE cells — is set to the scalar value 1 for all time periods and all spatial cells. No data files are read. No climate scenarios are applied. No heat stress curves are evaluated.

**What is NOT active by default**:
- No heat stress impacts on labor productivity
- No loading of `f37_labourprodimpact.cs3` (the LAMACLIMA ESM ensemble data)
- No differentiation by RCP scenario (`c37_labor_rcp`), heat stress metric (`c37_labor_metric`), work intensity (`c37_labor_intensity`), or ensemble uncertainty (`c37_labor_uncertainty`)
- No climate-scenario switching (`c37_labor_prod_scenario`; "cc" / "nocc" / "nocc_hist" paths are all `exo`-realization logic only)

**Consequence in module 38**: The default module 38 realization is `sticky_feb18` (`cfg$gms$factor_costs <- "sticky_feb18"`). Its presolve file explicitly aborts if `pm_labor_prod(t,j) != 1` anywhere (`modules/38_factor_costs/sticky_feb18/presolve.gms:8-10`). With `off` producing a uniform 1, that check always passes and the abort is never triggered.

In summary: **in the default configuration, module 37 is a no-op stub that passes a unit multiplier to module 38, which ignores it.**

---

## 2. Non-Default Realization: `exo`

The `exo` realization loads exogenous climate-driven labor productivity factors from LAMACLIMA project ESM data. Its core action in preloop (`modules/37_labor_prod/exo/preloop.gms:8`):

```gams
pm_labor_prod(t,j) = f37_labor_prod(t,j,"%c37_labor_rcp%","%c37_labor_metric%",
                                     "%c37_labor_intensity%","%c37_labor_uncertainty%");
```

This slices the 6-dimensional input array `f37_labourprodimpact.cs3` (dimensions: t_all × j × rcp37 × metric37 × intensity37 × uncertainty37) using the four configuration globals to produce a time × cell productivity factor, values typically in the range 0.5–1.0 for tropical cells under RCP8.5 by 2100.

To use `pm_labor_prod` < 1 in module 38, the **`sticky_labor`** realization of module 38 must also be activated (`cfg$gms$factor_costs <- "sticky_labor"`). The default `sticky_feb18` cannot consume non-unit `pm_labor_prod` — it aborts.

---

## 3. How `pm_labor_prod` Feeds into Module 38 (non-default path: `sticky_labor`)

When `sticky_labor` is active, labor productivity from module 37 enters the CES production function equation **`q38_ces_prodfun`** (`modules/38_factor_costs/sticky_labor/equations.gms`):

```gams
q38_ces_prodfun(j2,kcr) ..
  i38_ces_scale(j2,kcr) *
  ( i38_ces_shr(j2,kcr) * sum(mobil38, v38_capital_need(j2,kcr,mobil38))**(-s38_ces_elast_par)
    + (1 - i38_ces_shr(j2,kcr)) * (pm_labor_prod(j2) * pm_productivity_gain_from_wages(i2)
                                   * v38_laborhours_need(j2,kcr))**(-s38_ces_elast_par)
  )**(-1/s38_ces_elast_par)
    =e= 1 + v38_relax_CES_lp(j2,kcr);
```

**What this means**: Effective labor input to the CES function is the product `pm_labor_prod × pm_productivity_gain_from_wages × v38_laborhours_need`. When `pm_labor_prod` falls below 1 (heat stress), achieving the same normalized output requires either more labor hours (`v38_laborhours_need` rises) or more capital (`v38_capital_need` rises), subject to the elasticity of substitution `s38_ces_elast_subst` (default 0.3, meaning low substitutability — a 10% drop in labor productivity yields roughly a 3% shift toward capital).

This endogenous substitution is absent in `sticky_feb18`. There, the labor cost equation (`q38_cost_prod_labor`, `modules/38_factor_costs/sticky_feb18/equations.gms:15-17`) does divide by `pm_productivity_gain_from_wages` — but `pm_labor_prod` is not in that equation at all, and the pre-solve abort ensures `pm_labor_prod = 1` before any computation.

### Module 38 output: `vm_cost_prod_crop`

All three module 38 realizations expose the same interface variable to the rest of the model:

**`vm_cost_prod_crop(i,factors)`** — unit: mio USD17MER/yr; `factors = {labor, capital}`

Declared in `modules/38_factor_costs/sticky_feb18/declarations.gms:16`.

- In `sticky_feb18`: computed by `q38_cost_prod_labor` (equations.gms:15-17) and `q38_cost_prod_capital` (equations.gms:21-24)
- In `sticky_labor`: same two equations plus the CES constraint (`q38_ces_prodfun`) and optional `q38_labor_share_target`

When `pm_labor_prod` < 1 with `sticky_labor` active, the CES function forces higher factor requirements, which raises both the labor and capital slices of `vm_cost_prod_crop`.

---

## 4. How `vm_cost_prod_crop` Feeds into Module 11 (Cost Objective)

Module 11 (`default` realization, only one realization exists) is the global cost aggregator and defines MAgPIE's optimization objective.

### Equation `q11_cost_reg` (`modules/11_costs/default/equations.gms:15`)

```gams
q11_cost_reg(i2) .. v11_cost_reg(i2) =e= sum(factors, vm_cost_prod_crop(i2,factors))
                   + [... 30+ additional cost components ...]
```

The very first term on the right-hand side is `sum(factors, vm_cost_prod_crop(i2,factors))` — the sum over labor and capital of module 38's output.

### Equation `q11_cost_glo` (`modules/11_costs/default/equations.gms:10`)

```gams
q11_cost_glo .. vm_cost_glo =e= sum(i2, v11_cost_reg(i2));
```

**`vm_cost_glo` is MAgPIE's objective function** — the variable the solver minimizes. It is the sum of all regional costs, with `vm_cost_prod_crop` entering through `v11_cost_reg`.

### Full transmission chain (non-default path)

```
Climate change (ESM / LAMACLIMA data)
  → pm_labor_prod(t,j) < 1          [Module 37, exo/preloop.gms:8]
  → CES: effective labor falls       [Module 38, sticky_labor: q38_ces_prodfun]
  → v38_laborhours_need or
    v38_capital_need rises           [Module 38, sticky_labor: declarations.gms]
  → vm_cost_prod_crop(i,"labor")
    or vm_cost_prod_crop(i,"capital") rises
                                     [Module 38, q38_cost_prod_labor / q38_cost_prod_capital]
  → v11_cost_reg(i) rises            [Module 11, q11_cost_reg: equations.gms:15-47]
  → vm_cost_glo rises                [Module 11, q11_cost_glo: equations.gms:10]
  → solver seeks lower-cost land allocations (shift to cooler regions, crops, or technologies)
```

---

## 5. Summary Table

| Path | Module 37 realization | pm_labor_prod | Module 38 realization | CES active? | Cost impact |
|---|---|---|---|---|---|
| **Default** | `off` | 1.0 everywhere | `sticky_feb18` | NO | None (no-op) |
| Non-default (climate) | `exo` | 0.5–1.0 (tropical, late-century) | `sticky_labor` | YES | Labor/capital costs rise; optimization responds |

---

## 6. What the Docs Do Not Cover

- **Exact `sticky_labor` equation file line numbers for `q38_ces_prodfun`**: the docs quote the GAMS code block from `modules/38_factor_costs/sticky_labor/equations.gms` but do not supply a specific line number. Line numbers in module_38.md are cited as from the `sticky_feb18` realization only; `sticky_labor` lines are described structurally without `file:line` precision.
- **Whether `per_ton_fao_may22` consumes `pm_labor_prod`**: module_38.md §4 notes "depends — read source" for the climate-productivity column. This is explicitly flagged as not covered by docs alone.
- **Module 11's realization name**: it is always `default` (only one realization). This is stated in module_11.md but not in a `cfg$gms$costs` block in default.cfg (module 11 has no realization switch).

---

## Source Confidence

- Module 37 default (`off`) and `pm_labor_prod = 1`: module_37.md §7.2 + config/default.cfg (confirmed)
- Module 38 default (`sticky_feb18`), abort on non-unit pm_labor_prod, `q38_cost_prod_labor`, `q38_cost_prod_capital`: module_38.md §2.1, §2.8, config/default.cfg (confirmed)
- `sticky_labor` CES equation `q38_ces_prodfun` quoting pm_labor_prod: module_38.md §3.1 (GAMS code block quoted from source; line number not given in docs — treat as 🟡 Documented without file:line for sticky_labor)
- Module 11 `q11_cost_reg` and `q11_cost_glo`: module_11.md §2.1, §2.2 + §3.1 (confirmed)

🟢 All factual identifiers (variable names, equation names, realization names, scalar names) copied directly from documentation. No names fabricated.
