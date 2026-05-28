# R25-G1: Default Realization and Equations of Module 14 (Yields)

## Default Realization

🟢 **`managementcalib_aug19`** is the default (and only) realization of module 14.

This is confirmed by two sources:

- `module_14.md` line 3: `**Realization:** managementcalib_aug19`
- `module_14_notes.md` Warning 3: "`managementcalib_aug19` is the only realization: `module.gms` has a single `$Ifi` branch. An earlier `biocorrect` realization was removed in 2021 (commit `cc84ae5e1`); there is no `input` realization."

There are no alternative realizations to select.

---

## Equations Defined in equations.gms

Module 14's `equations.gms` defines exactly **2 equations** (`module_14.md` lines 6–7, §2):

### 1. `q14_yield_crop` — Crop Yield Calculation

**File:** `equations.gms:14-20`

```gams
q14_yield_crop(j2,kcr,w) ..
 vm_yld(j2,kcr,w) =e= sum(ct,i14_yields_calib(ct,j2,kcr,w)) *
                         vm_tau(j2,"crop") / sum((cell(i2,j2), supreg(h2,i2)), fm_tau1995(h2));
```

Calculates cellular crop yields by scaling calibrated baseline yields (`i14_yields_calib`) by the ratio of the current technological change factor (`vm_tau`) to the 1995 regional baseline (`fm_tau1995`). In words:

```
Yield(j, crop, water) = CalibratedBaseline(j, crop, water)
                         x tau_current(j, "crop")
                         / tau_1995(h)
```

🟢 (module_14.md §2.1, `equations.gms:14-20`)

---

### 2. `q14_yield_past` — Pasture Yield Calculation

**File:** `equations.gms:24-39` (also cited as `equations.gms:35-39` for the GAMS block)

```gams
q14_yield_past(j2,w) ..
 vm_yld(j2,"pasture",w) =e=
 sum(ct,(i14_yields_calib(ct,j2,"pasture",w))
 * sum(cell(i2,j2),pm_past_mngmnt_factor(ct,i2)))
 * (1 + s14_yld_past_switch*(sum((cell(i2,j2), supreg(h2,i2)), pcm_tau(j2, "crop")/fm_tau1995(h2)) - 1));
```

Calculates pasture yields using the calibrated baseline, an exogenous management factor (`pm_past_mngmnt_factor` from Module 70), and a partial spillover from crop-sector technological change. In words:

```
PastureYield(j, w) = CalibratedPastureYield(j, w)
                      x ManagementFactor(i)
                      x [1 + spillover x (tau_crop_prev(j) / tau_1995(h) - 1)]
```

Key distinctions from the crop equation:
- Uses **previous time step** tau (`pcm_tau`) rather than current (`vm_tau`), representing delayed knowledge transfer from crop to pasture systems.
- Applies exogenous pasture management factor from Module 70.
- Spillover parameter `s14_yld_past_switch` defaults to **0.25** (`input.gms:20`), meaning 25% of crop-sector intensification benefits pasture yields.

🟢 (module_14.md §2.2, `equations.gms:24-39`)

---

## Summary of Key Switches

| Switch | Default | Effect |
|--------|---------|--------|
| `s14_yld_past_switch` | 0.25 | Fraction of crop tau improvement passed to pasture |
| `s14_degradation` | 0 (OFF) | Yield reductions from soil loss / pollination deficits |
| `s14_limit_calib` | 1 (ON) | Lambda-based blending of relative and additive calibration |
| `s14_calib_ir2rf` | 1 (ON) | Calibration of irrigated-to-rainfed yield ratios to AQUASTAT |

🟡 (module_14.md §5)

---

## Equation Count Verification

The documentation states 2 equations and provides a verification command (`module_14.md §13.1`):

```bash
grep "^[ ]*q14_" modules/14_yields/managementcalib_aug19/declarations.gms | wc -l
# Expected: 2
```

Note: `equations.gms` defines q14_yield_crop and q14_yield_past. The preloop, presolve, nl_fix, and nl_release files contain extensive calibration and initialization logic, but these are not GAMS equations (they are parameter assignments and conditional statements executed outside the optimization problem).

---

**Source statements:**

- 🟡 Based on `modules/module_14.md` (fully verified documentation, last verified 2025-10-12 for main doc, 2026-05-17 for realization count correction)
- 💬 Includes user feedback from `modules/module_14_notes.md` (Warning 3 confirms single-realization status)
