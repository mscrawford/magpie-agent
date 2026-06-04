# G1 Answer: Module 14 (Yields) — Default Realization and Equations

## Default Realization

The default realization of module 14 is **`managementcalib_aug19`**.

Config line (🟡 `config/default.cfg:354`):
```
cfg$gms$yields <- "managementcalib_aug19"          # def = managementcalib_aug19
```

This is the **only** realization. An earlier `biocorrect` realization was removed in 2021 (commit `cc84ae5e1`); `modules/14_yields/input/` is the input-data directory, not a realization. (🟡 `modules/module_14_notes.md`, Warning 3)

---

## Equations in equations.gms

Module 14 defines exactly **2 equations** (🟡 `modules/module_14.md:6`):

### 1. `q14_yield_crop` — Crop Yield Calculation

**File:** `equations.gms:14-16` (🟡 `modules/module_14.md:43`)

```gams
q14_yield_crop(j2,kcr,w) ..
 vm_yld(j2,kcr,w) =e= sum(ct,i14_yields_calib(ct,j2,kcr,w)) *
                         vm_tau(j2,"crop") / sum((cell(i2,j2), supreg(h2,i2)), fm_tau1995(h2));
```

Calculates cellular crop yields by scaling calibrated baseline yields (`i14_yields_calib`) with the ratio of the current technological change factor (`vm_tau`, at cluster level j) to the 1995 baseline tau (`fm_tau1995`, at super-region level h).

### 2. `q14_yield_past` — Pasture Yield Calculation

**File:** `equations.gms:35-39` (🟡 `modules/module_14.md:86`)

```gams
q14_yield_past(j2,w) ..
 vm_yld(j2,"pasture",w) =e=
 sum(ct,(i14_yields_calib(ct,j2,"pasture",w))
 * sum(cell(i2,j2),pm_past_mngmnt_factor(ct,i2)))
 * (1 + s14_yld_past_switch*(sum((cell(i2,j2), supreg(h2,i2)), pcm_tau(j2, "crop")/fm_tau1995(h2)) - 1));
```

Calculates pasture yields using calibrated baseline, an exogenous management factor (`pm_past_mngmnt_factor` from Module 70), and partial spillover from crop-sector tau change. Key distinction: uses `pcm_tau` (previous time step's tau) rather than current `vm_tau`, representing delayed knowledge transfer from crop to pasture systems. The spillover magnitude is controlled by `s14_yld_past_switch` (default 0.25, meaning 25% of crop intensification benefits pasture).

---

## Summary

| Equation | Dimensions | Key mechanism |
|---|---|---|
| `q14_yield_crop` | j, kcr, w | Calibrated yield × (tau_current / tau_1995) |
| `q14_yield_past` | j, w | Calibrated yield × management factor × (1 + spillover × (tau_prev/tau_1995 - 1)) |

The module's substantial complexity resides not in the 2 optimization equations but in the preloop calibration system (6 stages in `preloop.gms`), which transforms raw LPJmL yields into FAO-calibrated baselines before the solver runs.

---

## Sources

- 🟡 `modules/module_14.md` (fully verified 2025-10-12, LPJmL-yields audit 2026-05-17)
- 🟡 `modules/module_14_notes.md` (user warnings, Warning 3 on realization uniqueness)
- 🟡 `config/default.cfg:354` (cfg$gms$yields assignment)

---

## Doc Wished Existed

A **cross-realization comparison card** for module 14 would have been useful — even a one-liner noting "biocorrect was removed in 2021; only one realization exists" directly in `module_14.md`'s header rather than in the notes file. The relevant warning (note 3) exists in `module_14_notes.md`, but an agent answering without the notes file would have to infer the single-realization status from the doc header alone. This is a minor gap; the notes file does cover it.
