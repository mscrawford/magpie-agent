# R29 Q6 / Regression anchor G1: Module 14 (Yields) — Default Realization and Equations

## Question

What is the default realization of module 14 (yields)? List the equations defined in its equations.gms.

---

## Default Realization

**`managementcalib_aug19`**

Confirmed from two independent sources:

- `<magpie-root>/config/default.cfg`:
  ```
  cfg$gms$yields <- "managementcalib_aug19"          # def = managementcalib_aug19
  ```
- `<magpie-agent>/modules/module_14.md` line 3:
  ```
  **Realization:** `managementcalib_aug19`
  ```

---

## Equations in equations.gms (count: 2)

Module 14's `managementcalib_aug19/equations.gms` defines exactly **2 equations**.

### 1. q14_yield_crop — Crop Yield Calculation

**File:** `equations.gms:14-16` (citation range extends to `:14-20` per section 2.1 footnote)

```gams
q14_yield_crop(j2,kcr,w) ..
 vm_yld(j2,kcr,w) =e= sum(ct,i14_yields_calib(ct,j2,kcr,w)) *
                         vm_tau(j2,"crop") / sum((cell(i2,j2), supreg(h2,i2)), fm_tau1995(h2));
```

**What it does:** Scales calibrated baseline yields (`i14_yields_calib`) by the ratio of the current technological change factor (`vm_tau`, from Module 13, at cluster level) to the 1995 baseline (`fm_tau1995`). If τ doubles from 1995, crop yields double.

**Dimensions:** j (cluster cells), kcr (crops), w (rainfed/irrigated)

**Key variables:**
- `vm_yld(j,kcr,w)` — output crop yield (tDM/ha/yr)
- `i14_yields_calib(ct,j,kcr,w)` — calibrated baseline yields from preloop
- `vm_tau(j,"crop")` — current τ factor at cluster level (≥1, starts at 1 in 1995)
- `fm_tau1995(h)` — regional τ in 1995 (super-region level, for normalization)

---

### 2. q14_yield_past — Pasture Yield Calculation

**File:** `equations.gms:35-39` (citation range also given as `:24-39` in section 2.2 footnote)

```gams
q14_yield_past(j2,w) ..
 vm_yld(j2,"pasture",w) =e=
 sum(ct,(i14_yields_calib(ct,j2,"pasture",w))
 * sum(cell(i2,j2),pm_past_mngmnt_factor(ct,i2)))
 * (1 + s14_yld_past_switch*(sum((cell(i2,j2), supreg(h2,i2)), pcm_tau(j2, "crop")/fm_tau1995(h2)) - 1));
```

**What it does:** Calculates pasture yields using calibrated baseline, an exogenous management factor (`pm_past_mngmnt_factor` from Module 70), and partial spillover from crop-sector τ. Crucially, it uses `pcm_tau` (the **previous** time-step's τ) rather than `vm_tau` (current τ), representing delayed knowledge transfer from crop to pasture systems.

**Dimensions:** j (cluster cells), w (rainfed/irrigated)

**Key variables:**
- `vm_yld(j,"pasture",w)` — output pasture yield (tDM/ha/yr)
- `i14_yields_calib(ct,j,"pasture",w)` — calibrated pasture baseline from preloop
- `pm_past_mngmnt_factor(ct,i)` — exogenous pasture management factor (livestock-demand driven, from Module 70)
- `s14_yld_past_switch` — spillover parameter (default 0.25; `input.gms:20`)
- `pcm_tau(j,"crop")` — **previous** time-step's crop τ at cluster level

**Key difference from q14_yield_crop:** Uses `pcm_tau` (previous τ) not `vm_tau` (current τ), and includes the exogenous management factor.

---

## Summary

| Item | Value |
|------|-------|
| Default realization | `managementcalib_aug19` |
| Equation count | 2 |
| Equation 1 | `q14_yield_crop` (equations.gms:14-16) |
| Equation 2 | `q14_yield_past` (equations.gms:35-39) |

---

## Sources

- 🟢 Config verified: `<magpie-root>/config/default.cfg` (grep for `cfg$gms$yields`)
- 🟡 Documented: `<magpie-agent>/modules/module_14.md` sections 1, 2.1, 2.2, 13.1

**Note on line numbers:** Line numbers are as documented in `module_14.md` at its last verified date (2025-10-12). Code changes since then may have shifted them. For critical work, verify against current `../modules/14_yields/managementcalib_aug19/equations.gms`.

**Equation count verification command (from module_14.md §13.1):**
```bash
grep "^[ ]*q14_" ../modules/14_yields/managementcalib_aug19/declarations.gms | wc -l
# Expected: 2
```
