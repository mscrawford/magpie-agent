# Round 49 Answer: Circular Dependency in the TC/Yield/Production Cluster (Modules 13, 14, 17)

## Selected Cycle: Module 13 (TC) ↔ Module 14 (Yields)

The best-documented cycle in `circular_dependency_resolution.md` that directly involves the TC/yield/production cluster is **Cycle 1 (Production-Yield-Livestock Triangle, ⭐⭐⭐)**, but the sharpest and most precisely documented sub-dependency within that cluster is the **M13 ↔ M14 bidirectional link**, which is resolved by two distinct mechanisms operating simultaneously. I focus here because this is where the circular dependency resolution.md gives the most precise code-level citation.

---

## What Creates the Cycle

### M13 needs from M14 (indirect, via production)

Module 13 (`endo_jan22`) costs the intensification decision using regional agricultural area `pc13_land(i2,tautype)` (a lagged parameter from Module 10, not from M14 directly). The endogenous optimization of `v13_tau_core(h,tautype)` is driven by the economic trade-off between intensification costs (paid as `vm_tech_cost(i)` into the objective via Module 11) and the land-saving benefit that flows through **yields → production → land demand**. Module 14's output `vm_yld(j,kve,w)` feeds Module 30/31 (croparea/pasture) and Module 17 (production), and the optimizer can only value raising τ if it knows the yield response.

Concretely: the equation `q13_cost_tc` sets the cost of intensification, and `q14_yield_crop` sets the yield benefit. Both appear in the same optimization problem — Module 13 needs to know the yield *gain* from increasing τ (which is the M14 equation structure), and M14 needs the *current* τ value from M13 to compute `vm_yld`.

### M14 needs from M13

`q14_yield_crop` (crop yields) requires `vm_tau(j2,"crop")` — the current-timestep decision variable produced by Module 13's equation `q13_tau`:

```
q14_yield_crop(j2,kcr,w) ..
  vm_yld(j2,kcr,w) =e= sum(ct,i14_yields_calib(ct,j2,kcr,w))
                        * vm_tau(j2,"crop")
                        / sum((cell(i2,j2), supreg(h2,i2)), fm_tau1995(h2));
```
`module_14.md §2.1, equations.gms:14-16`

`q14_yield_past` (pasture yields) also involves τ — but critically, it uses the **previous-timestep** parameter `pcm_tau(j2,"crop")`, not the current variable `vm_tau`:

```
q14_yield_past(j2,w) ..
  vm_yld(j2,"pasture",w) =e=
    sum(ct,(i14_yields_calib(ct,j2,"pasture",w))
    * sum(cell(i2,j2),pm_past_mngmnt_factor(ct,i2)))
    * (1 + s14_yld_past_switch
       * (sum((cell(i2,j2), supreg(h2,i2)), pcm_tau(j2,"crop")/fm_tau1995(h2)) - 1));
```
`module_14.md §2.2, equations.gms:35-39`

### M13's output into M14

Module 13 produces interface variable `vm_tau(j,tautype)` via equation `q13_tau`, which is a weighted average of `v13_tau_core(h2,tautype)` and `v13_tau_consv(h2,tautype)` across the conservation-area share `p13_cropland_consv_shr`:

```
q13_tau(j2,tautype)..
    vm_tau(j2,tautype) =e= sum((ct, cell(i2,j2), supreg(h2,i2)),
        (1-p13_cropland_consv_shr(ct,j2)) * v13_tau_core(h2,tautype)
        + p13_cropland_consv_shr(ct,j2) * v13_tau_consv(h2,tautype));
```
`module_13.md §4, equations.gms:52-53`

This `vm_tau` enters M14's `q14_yield_crop` as the current-timestep variable. Both `v13_tau_core` (M13's decision variable) and `vm_yld` (M14's output) are **optimized simultaneously** within the same solve.

---

## How the Cycle Is Resolved

The documentation draws a clear distinction between crop and pasture:

### Crop yields (q14_yield_crop): Simultaneous optimization

The cycle between `vm_tau` (M13) and `vm_yld` (M14 crop) is resolved by **simultaneous optimization within the same GAMS solve**. Both variables are endogenous:
- M13 chooses `v13_tau_core` (and hence `vm_tau`) by balancing investment costs against yield benefits
- M14 computes `vm_yld` as a linear function of `vm_tau`
- The GAMS solver (CONOPT/IPOPT) receives both equations — `q13_cost_tc`, `q13_tech_cost`, `q13_tau` from M13, and `q14_yield_crop` from M14 — simultaneously and finds the internally consistent solution in a single NLP solve

`circular_dependency_resolution.md §3.1` states this explicitly:
> "Within timestep: the calibrated yield baseline `i14_yields_calib` (14) is a fixed parameter, but the realized yield `vm_yld` is **endogenous** — `q14_yield_crop` scales it by the current-timestep decision variable `vm_tau` (`modules/14_yields/managementcalib_aug19/equations.gms:14-16`), so the 14↔13 coupling is a *simultaneous* NLP, not a within-timestep cycle."

**Resolution type: Type 2 — Simultaneous Equations (solver handles it).**

No presolve fixed value breaks this link. Both `vm_tau` and `vm_yld` are live optimization variables within the solve.

### Pasture yields (q14_yield_past): Lagged (previous-timestep) value

For the M13 → M14 *pasture* sub-link, the cycle *is* broken by a temporal lag. The pasture equation does not use `vm_tau` (the current decision variable). It uses `pcm_tau(j,"crop")` — the parameter-form of τ carried forward from the previous timestep's solution.

`module_14.md §2.2` states:
> "Pastures use **previous time step** τ (`pcm_tau`) instead of current τ (`vm_tau`), reflecting delayed knowledge transfer from crop to pasture systems."

`circular_dependency_resolution.md §3.1` confirms:
> "Pasture yields (`q14_yield_past`) instead use the **lagged** `pcm_tau(j,'crop')` (previous timestep) — the actual cross-timestep cycle-breaker (`modules/14_yields/managementcalib_aug19/equations.gms:35-39`; `pcm_tau` updated `modules/13_tc/endo_jan22/postsolve.gms:16`)"

`pcm_tau` is updated in M13's postsolve after each timestep's solve completes:
> `postsolve.gms:8-16`: `pcm_tau = vm_tau.l` (from `module_13.md §Postsolve Updates`)

**Resolution type: Type 1 — Temporal Feedback (previous-timestep lagged value).**

---

## Summary Table

| Sub-link | Interface variable needed | Direction | Resolution mechanism | GAMS phase |
|---|---|---|---|---|
| M13 → M14 (crop) | `vm_tau(j,"crop")` — current optimization variable | M13 to M14 | Simultaneous NLP within single solve | SOLVE |
| M14 → M13 (crop) | `vm_yld` drives land demand, which prices τ investment | M14 to M13 | Simultaneous NLP (same solve) | SOLVE |
| M13 → M14 (pasture) | `pcm_tau(j,"crop")` — previous timestep parameter | M13 to M14 | Lagged parameter updated in postsolve | POSTSOLVE → next PRESOLVE |
| M13 postsolve update | `vm_tau.l` → `pcm_tau` | Self | `postsolve.gms:16` assignment | POSTSOLVE |

---

## Not involved: presolve fixed value for this cycle

The docs do not cite any presolve `.fx` fix as the cycle-breaking mechanism for the M13↔M14 crop coupling. The nl_fix mechanism (`nl_fix.gms:10-11`, module_14.md §10.1) fixes `vm_yld` to a scalar computed from the *previous solve's* `vm_tau.l`, but this is an iterative NLP warm-start device — it is not the primary resolution of the M13↔M14 dependency.

The two mechanisms are thus:
1. **Crop yields**: Simultaneous optimization — both `vm_tau` and `vm_yld` are co-optimized in the same solve. GAMS treats this as a coupled NLP; no external cycle-breaker needed.
2. **Pasture yields**: Lagged parameter `pcm_tau` provides the previous timestep's τ value, so pasture yields at time *t* depend only on a fixed parameter (not a co-optimized variable), breaking the within-timestep circularity.

---

## Epistemic Status

- 🟡 **Documented**: All claims sourced from `cross_module/circular_dependency_resolution.md §3.1` and `modules/module_13.md` + `modules/module_14.md` (both read this session). I did not read raw GAMS source per task constraints.
- Key equations (`q14_yield_crop`, `q14_yield_past`, `q13_tau`) and variable names (`vm_tau`, `vm_yld`, `pcm_tau`, `v13_tau_core`) are quoted verbatim from the AI documentation.
- Line citations (e.g., `equations.gms:14-16`, `equations.gms:35-39`, `postsolve.gms:16`) are as stated in the documentation; actual line numbers may have drifted since last verification (last verified: `module_14.md` 2025-10-12, `module_13.md` 2026-01-20).
