# R24-Q3 Sonnet answer (Tau cost formula → objective function)

## Module 13 (`endo_jan22`): Tau cost formula, bounds, and objective function entry

### (a) The equations linking tau to its cost

The cost derivation in Module 13 is a two-step pipeline: first a unit cost per intensity level, then annualization of that cost weighted by the actual intensification rate.

**Step 1 — Unit cost of intensification (`q13_cost_tc`)**

```gams
q13_cost_tc(i2, tautype) ..
  v13_cost_tc(i2, tautype) =e=
      sum(ct, pc13_land(i2, tautype)
              * i13_tc_factor(ct)
              * sum(supreg(h2,i2), v13_tau_core(h2,tautype)) ** i13_tc_exponent(ct)
              * (1 + pm_interest(ct,i2)) ** 15);
```
`modules/13_tc/endo_jan22/equations.gms:20-23`

The four multiplicands:

- `pc13_land(i2, tautype)` — regional agricultural area (million ha) from the previous timestep. Costs scale with area because broader coverage means greater biophysical heterogeneity and therefore more research effort required for the same average productivity gain.
- `i13_tc_factor(ct)` — a regression factor (USD17MER per ha) read from `f13_tc_factor.cs3`. Its value depends on the scenario switch `c13_tccost` (`low`, `medium` [default], or `high`) and the timestep.
- `v13_tau_core(h2, tautype) ** i13_tc_exponent(ct)` — a power function of the current tau level, read from `f13_tc_exponent.cs3`. This captures the increasing marginal cost of intensification: the higher tau already is, the more expensive it is to push it further.
- `(1 + pm_interest(ct,i2)) ** 15` — the 15-year time-shift factor. Because research investments precede yield gains by ~15 years, costs are shifted forward by 15 periods using the regional interest rate `pm_interest` (provided by Module 12). This allows the optimizer to correctly align costs with benefits.

**Step 2 — Annualized technology cost (`q13_tech_cost`)**

```gams
q13_tech_cost(i2, tautype) ..
  v13_tech_cost(i2, tautype) =e=
      sum(supreg(h2,i2), v13_tau_core(h2,tautype) / pc13_tau(h2,tautype) - 1)
      * v13_cost_tc(i2, tautype)
      * sum(ct, pm_interest(ct,i2) / (1 + pm_interest(ct,i2)));
```
`modules/13_tc/endo_jan22/equations.gms:40-42`

- `v13_tau_core / pc13_tau - 1` is the intensification rate: how much tau grows this timestep relative to the previous one. A value of 0.20 means a 20 % increase.
- `v13_cost_tc` is the unit cost from Step 1.
- `pm_interest / (1 + pm_interest)` is an infinite-horizon annuity factor (`r / (1+r)`), distributing the one-time investment over perpetuity without needing an explicit depreciation period. Note: unlike Module 41 (irrigation), there is no depreciation term `d` here — the formula is strictly `r/(1+r)`.

The overall interpretation: the model incurs an annualized cost proportional to (a) how large a step up in tau it is taking, (b) how expensive each unit of intensification is at the current tau level and area, and (c) the cost of capital.

**Step 3 — Aggregation across tau types (`q13_tech_cost_sum`)**

```gams
q13_tech_cost_sum(i2) ..
  vm_tech_cost(i2) =e= sum(tautype, v13_tech_cost(i2, tautype));
```
`modules/13_tc/endo_jan22/equations.gms:44-45`

`tautype` contains two elements: `crop` and `pastr` (`sets.gms:13-14`). The interface variable `vm_tech_cost(i)` is the sum across both, declared at `modules/13_tc/endo_jan22/declarations.gms:10`.

---

### (b) How tau is bounded over time

Tau bounds are set in `presolve.gms` before each solve.

**Initial value (first timestep, `ord(t) = 1`):**
- `v13_tau_core.l` is initialized to `pc13_tau`, which was set from `fm_tau1995.cs4` — historical observed tau values for 1995 by super-region (`presolve.gms:74-78`).

**Lower bound (all timesteps):**
- With `s13_ignore_tau_historical = 1` (default): `v13_tau_core.lo = pc13_tau(h, tautype)` — tau cannot fall below its value in the previous timestep. Intensification is irreversible.
- With `s13_ignore_tau_historical = 0`: in historical periods, the lower bound is instead set to `f13_tau_historical(t,h)` (crops) or `f13_pastr_tau_hist(t,h)` (pasture) to match observed trajectories (`presolve.gms:12-19`).

**Upper bound (all timesteps):**
- `v13_tau_core.up = 2 * pc13_tau(h, tautype)` — tau cannot more than double within a single 5-year timestep (`presolve.gms:19`). This prevents implausibly rapid adoption.

**GDP cap (optional, after SSP2 fixing period):**
When `s13_max_gdp_shr ≠ Inf` (default is `Inf`, i.e. no cap), a bound is applied to `vm_tech_cost.up(i)` equal to `s13_max_gdp_shr` times total regional GDP (from `im_gdp_pc_ppp_iso × im_pop_iso`). This prevents the optimizer from choosing unrealistically high intensification expenditures when land expansion is strongly constrained (`presolve.gms:30-42`).

**Cost scenario (`c13_tccost`):** After the SSP2 historical fixing period, `i13_tc_factor` and `i13_tc_exponent` are selected from the `low`, `medium` (default), or `high` scenario columns of their respective input files (`preloop.gms:8-16`). This shifts the marginal cost curve up or down without changing its functional form.

---

### (c) Entry into the global objective function

The interface variable `vm_tech_cost(i)` feeds directly into Module 11 (Costs, `default` realization).

**Module 11, `q11_cost_reg` (`equations.gms:15-47`)** aggregates all regional cost components:

```gams
q11_cost_reg(i2) .. v11_cost_reg(i2) =e=
    sum(factors, vm_cost_prod_crop(i2,factors))
    + ...
    + vm_tech_cost(i2)       ← Module 13's contribution
    + ...
;
```

`vm_tech_cost(i)` appears as one of 32 additive terms in `v11_cost_reg(i)`.

**Module 11, `q11_cost_glo` (`equations.gms:10`)** then sums across regions:

```gams
q11_cost_glo .. vm_cost_glo =e= sum(i2, v11_cost_reg(i2));
```

`vm_cost_glo` is the scalar that MAgPIE minimizes. Every euro of technological-change cost Module 13 generates raises `vm_cost_glo` by the same amount, creating a direct economic incentive: the optimizer takes intensification only as far as it is cheaper than expanding land (or importing).

The complete path is:

```
q13_cost_tc  →  v13_cost_tc
q13_tech_cost  →  v13_tech_cost  (per tautype)
q13_tech_cost_sum  →  vm_tech_cost(i)
    ↓
q11_cost_reg  →  v11_cost_reg(i)
    ↓
q11_cost_glo  →  vm_cost_glo  [MINIMIZED]
```

---

**Source statement:**

- 🟡 Based on `modules/module_13.md` (fully verified 2026-01-20 against `endo_jan22` source)
- 🟡 Based on `modules/module_11.md` (verified 2025-10-12 against `default` realization source)
