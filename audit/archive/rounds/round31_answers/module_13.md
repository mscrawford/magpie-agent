# Module 13 (endo_jan22): vm_tau, pm_interest, and downstream flows

## 1. How vm_tau is determined

In the default realization `endo_jan22`, `vm_tau(j,tautype)` is an **endogenously optimized** output — the solver chooses it by trading intensification costs against land expansion costs.

The decision variable is `v13_tau_core(h,tautype)` at super-region level `h`. The interface output `vm_tau(j,tautype)` at cluster level `j` is produced by `q13_tau`:

```gams
q13_tau(j2,tautype)..
    vm_tau(j2,tautype) =e= sum((ct, cell(i2,j2), supreg(h2,i2)),
        (1-p13_cropland_consv_shr(ct,j2)) * v13_tau_core(h2,tautype)
        + p13_cropland_consv_shr(ct,j2) * v13_tau_consv(h2,tautype));
```

(Source: `modules/13_tc/endo_jan22/equations.gms:52-58`)

So `vm_tau` at the cluster level is a **weighted average** of the core tau and the conservation-area tau, weighted by the share of cropland in conservation priority areas (`p13_cropland_consv_shr`). The underlying intensification investment (`v13_tau_core`) is spatially uniform within each super-region `h`; spatial variation in `vm_tau` across clusters within an `h` arises only through the conservation-area mask.

**Bounds on v13_tau_core** (presolve.gms:12-19):
- Lower bound: `pc13_tau(h,tautype)` — tau cannot decrease from the previous timestep.
- Upper bound: `2 * pc13_tau(h,tautype)` — maximum doubling per 5-year timestep.
- Initial values seeded from `fm_tau1995` (1995 historical tau read from `fm_tau1995.cs4`).

The conservation tau `v13_tau_consv` links to core tau via `q13_tau_consv`:

```gams
q13_tau_consv(h2,tautype)$(c13_croparea_consv_tau_increase = 1 OR sum(ct, m_year(ct)) < s13_croparea_consv_start)..
 v13_tau_consv(h2,tautype) =e= p13_croparea_consv_tau_factor(h2) * v13_tau_core(h2,tautype);
```

(Source: `modules/13_tc/endo_jan22/equations.gms:59-60`)

The default factor is 0.8, meaning conservation-area intensification is 20% lower than core. When `c13_croparea_consv = 0` (the default), no conservation differentiation is active, and `vm_tau = v13_tau_core` uniformly.

---

## 2. How pm_interest enters the TC cost — two distinct roles

`pm_interest(ct,i)` from Module 12 appears in **two** equations in Module 13, playing a different role in each.

### Role 1: 15-year time shift in q13_cost_tc

```gams
q13_cost_tc(i2, tautype) ..
  v13_cost_tc(i2, tautype) =e= sum(ct, pc13_land(i2, tautype) *
                     i13_tc_factor(ct) * sum(supreg(h2,i2),v13_tau_core(h2,tautype))**
                     i13_tc_exponent(ct) * (1+pm_interest(ct,i2))**15);
```

(Source: `modules/13_tc/endo_jan22/equations.gms:20-23`)

The term `(1+pm_interest(ct,i2))**15` computes a **future-value multiplier** for a 15-year research-to-yield lag. TC investments take on average 15 years before they deliver yield improvements. The cost is shifted forward by compounding at the regional interest rate so that the model sees the cost concurrent with the benefit, enabling correct intertemporal optimization.

### Role 2: Annuity factor in q13_tech_cost

```gams
q13_tech_cost(i2, tautype) ..
 v13_tech_cost(i2, tautype) =e= sum(supreg(h2,i2), v13_tau_core(h2,tautype)/pc13_tau(h2,tautype)-1) * v13_cost_tc(i2,tautype)
                               * sum(ct,pm_interest(ct,i2)/(1+pm_interest(ct,i2)));
```

(Source: `modules/13_tc/endo_jan22/equations.gms:40-42`)

The term `pm_interest/(1+pm_interest)` is the **infinite-horizon annuity factor** `r/(1+r)`. It distributes the total investment cost over an infinite time horizon without specifying an explicit depreciation period. There is no depreciation term (`d`) — the annuity formula is strictly `r/(1+r)`, in contrast to Module 41 (irrigation) which uses `(r+d)/(1+r)`.

The intensification rate `v13_tau_core/pc13_tau - 1` scales the unit cost: the larger the relative jump in tau (current vs. prior period), the more annualized cost the region incurs.

---

## 3. Path from tau to yields (Module 14)

`vm_tau(j,"crop")` reaches Module 14 via `q14_yield_crop` (the default and only realization `managementcalib_aug19`):

```gams
q14_yield_crop(j2,kcr,w) ..
 vm_yld(j2,kcr,w) =e= sum(ct,i14_yields_calib(ct,j2,kcr,w)) *
                         vm_tau(j2,"crop") / sum((cell(i2,j2), supreg(h2,i2)), fm_tau1995(h2));
```

(Source: `modules/14_yields/managementcalib_aug19/equations.gms:14-16`)

**Mechanism**: Calibrated LPJmL baseline yields (`i14_yields_calib`) are scaled by the ratio of current tau to the 1995 baseline tau `fm_tau1995`. If tau doubles relative to 1995, yields double. The ratio form means the calibration baseline and tau are consistently indexed to the same reference year.

`vm_yld` then feeds Module 30 (cropland) and Module 31 (pasture) to determine how much land area is needed to satisfy demand, creating the core intensive–extensive trade-off.

**Pasture spillover** (q14_yield_past, `equations.gms:35-39`): A partial spillover from crop technological change is applied to pasture yields — crop tau improvements partially lift pasture productivity. This is a separate equation consuming `vm_tau(j,"crop")` again.

---

## 4. Path from tau to the cost objective (Module 11)

The annualized technology cost `v13_tech_cost(i,tautype)` is aggregated across tau types by `q13_tech_cost_sum`:

```gams
q13_tech_cost_sum(i2) ..
 vm_tech_cost(i2) =e= sum(tautype, v13_tech_cost(i2, tautype));
```

(Source: `modules/13_tc/endo_jan22/equations.gms:44-45`)

`vm_tech_cost(i)` is then picked up directly in Module 11's regional cost equation `q11_cost_reg`:

```
v11_cost_reg(i2) =e= ... + vm_tech_cost(i2) + ...
```

(Source: `modules/11_costs/default/equations.gms:15-47`, line `+ vm_tech_cost(i2)`)

And `q11_cost_glo` sums regional costs to `vm_cost_glo`, the global objective variable MAgPIE minimizes.

**Complete flow**:
```
v13_tau_core [optimized] → q13_cost_tc → v13_cost_tc
                         → q13_tech_cost → v13_tech_cost
                         → q13_tech_cost_sum → vm_tech_cost(i)
                         → q11_cost_reg → v11_cost_reg(i)
                         → q11_cost_glo → vm_cost_glo [objective]

v13_tau_core → q13_tau → vm_tau(j)
                        → q14_yield_crop → vm_yld(j,kcr,w)
                        → Modules 30/31 (production)
```

---

## Summary table

| Component | Equation | Key formula element | Purpose |
|-----------|----------|--------------------|---------| 
| Unit TC cost | `q13_cost_tc` | `tau^exponent * (1+r)^15` | Power-function cost scaled by 15-yr interest compounding |
| Annualized TC cost | `q13_tech_cost` | `(tau/tau_prev - 1) * cost * r/(1+r)` | Infinite-horizon annuity of investment for this period's tau increase |
| Summed TC cost | `q13_tech_cost_sum` | `sum(tautype, ...)` | Aggregate crop + pasture for Module 11 |
| Tau at cluster | `q13_tau` | Weighted avg of core + conservation tau | Spatial interface output to Module 14 |
| Crop yield | `q14_yield_crop` | `calib_yield * tau / tau_1995` | Tau scales biophysical yields |
| Regional cost | `q11_cost_reg` | `... + vm_tech_cost(i) + ...` | TC cost enters objective |

---

## Epistemic status

- 🟢 **Verified**: All equation formulas quoted from `module_13.md` and `module_14.md`, both marked "Fully Verified" against `../modules/13_tc/endo_jan22/*.gms` (last verified 2026-01-20) and `../modules/14_yields/managementcalib_aug19/equations.gms` (last verified 2025-10-12).
- 🟢 **Verified**: `vm_tech_cost` appearance in `q11_cost_reg` confirmed from `module_11.md` (fully verified 2025-10-12, `modules/11_costs/default/equations.gms:15-47`).
- Source: `module_13.md`, `module_14.md`, `module_11.md`
