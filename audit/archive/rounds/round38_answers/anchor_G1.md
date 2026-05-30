# G1 — Module 14 default realization and equations

**Source:** `/Users/turnip/Documents/Work/Workspace/magpie/magpie-agent/modules/module_14.md`

---

## Default realization

The default (and only) realization of module 14 (Yields) is:

> **`managementcalib_aug19`**

This is stated verbatim at the top of `module_14.md`:

> Realization: `managementcalib_aug19`

---

## Equations defined in equations.gms

The module documentation states "Equation Count: 2" and identifies exactly two equations:

| Equation | Location | Purpose |
|---|---|---|
| `q14_yield_crop` | `equations.gms:14-16` (citation range `equations.gms:14-20`) | Calculates cellular crop yields by scaling calibrated baseline yields (`i14_yields_calib`) by the ratio of current τ (`vm_tau`) to 1995 baseline τ (`fm_tau1995`) |
| `q14_yield_past` | `equations.gms:35-39` (citation range `equations.gms:24-39`) | Calculates pasture yields using calibrated baseline, exogenous management factor (`pm_past_mngmnt_factor`), and partial spillover from crop-sector technological change |

The module documentation explicitly confirms this count at `modules/module_14.md` section 13.1:

> **Verified:** 2 equations (q14_yield_crop, q14_yield_past)

---

## Source

- `module_14.md` lines 2-7 (realization header and equation count)
- `module_14.md` section 2.1 (q14_yield_crop)
- `module_14.md` section 2.2 (q14_yield_past)
- `module_14.md` section 13.1 (equation count verification)
