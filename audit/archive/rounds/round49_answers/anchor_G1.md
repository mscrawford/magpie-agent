# G1: Module 14 (Yields) — Default Realization and Equations

## Default Realization

The default realization of module 14 (yields) is **`managementcalib_aug19`**.

Source: `modules/module_14.md` header ("Realization: `managementcalib_aug19`", "Date: August 2019").

---

## Equations Defined in equations.gms

Module 14's `equations.gms` defines exactly **2 equations** (Equation Count: 2, per module_14.md §2):

### 1. `q14_yield_crop` — Crop Yield Calculation

**File:** `equations.gms:14-16` (citation from module_14.md §2.1; full citation range given as `equations.gms:14-20`)

```gams
q14_yield_crop(j2,kcr,w) ..
 vm_yld(j2,kcr,w) =e= sum(ct,i14_yields_calib(ct,j2,kcr,w)) *
                         vm_tau(j2,"crop") / sum((cell(i2,j2), supreg(h2,i2)), fm_tau1995(h2));
```

Calculates cellular crop yields by scaling calibrated baseline yields (`i14_yields_calib`) with the ratio of the current technological change factor (`vm_tau`) to the 1995 baseline (`fm_tau1995`).

### 2. `q14_yield_past` — Pasture Yield Calculation

**File:** `equations.gms:35-39` (citation from module_14.md §2.2; full citation range given as `equations.gms:24-39`)

```gams
q14_yield_past(j2,w) ..
 vm_yld(j2,"pasture",w) =e=
 sum(ct,(i14_yields_calib(ct,j2,"pasture",w))
 * sum(cell(i2,j2),pm_past_mngmnt_factor(ct,i2)))
 * (1 + s14_yld_past_switch*(sum((cell(i2,j2), supreg(h2,i2)), pcm_tau(j2, "crop")/fm_tau1995(h2)) - 1));
```

Calculates pasture yields using calibrated baseline, an exogenous management factor (`pm_past_mngmnt_factor`), and partial spillover from crop-sector technological change. Notably uses `pcm_tau` (previous time step's tau) rather than `vm_tau` (current), reflecting delayed knowledge transfer from crop to pasture systems.

---

## Source

All content sourced from `modules/module_14.md` (Sections 2.1 and 2.2, header metadata). Documentation status: Fully Verified (2025-10-12).
