# Anchor G1: Module 14 default realization and equations

**Question**: What is the default realization of module 14 (yields)? List the equations defined in its equations.gms.

---

## Default Realization

The default (and only) realization of module 14 is **`managementcalib_aug19`**.

Source: `magpie-agent/modules/module_14.md` line 3 ("Realization: `managementcalib_aug19`") and confirmed by `module_14_notes.md` warning 3: "`managementcalib_aug19` is the only realization: `module.gms` has a single `$Ifi` branch. An earlier `biocorrect` realization was removed in 2021 (commit `cc84ae5e1`)."

---

## Equations in equations.gms

Module 14 defines exactly **2 equations** (doc: `module_14.md` line 6, "Equation Count: 2"):

### 1. `q14_yield_crop`

**File:** `equations.gms:14-20`

Calculates cellular crop yields by scaling calibrated baseline yields with the ratio of current tau to the 1995 baseline tau:

```gams
q14_yield_crop(j2,kcr,w) ..
 vm_yld(j2,kcr,w) =e= sum(ct,i14_yields_calib(ct,j2,kcr,w)) *
                         vm_tau(j2,"crop") / sum((cell(i2,j2), supreg(h2,i2)), fm_tau1995(h2));
```

Output variable: `vm_yld(j,kcr,w)` — crop yield in tDM/ha/yr.

### 2. `q14_yield_past`

**File:** `equations.gms:24-39`

Calculates pasture yields using the calibrated baseline, an exogenous management factor from module 70, and partial spillover from crop-sector technological change:

```gams
q14_yield_past(j2,w) ..
 vm_yld(j2,"pasture",w) =e=
 sum(ct,(i14_yields_calib(ct,j2,"pasture",w))
 * sum(cell(i2,j2),pm_past_mngmnt_factor(ct,i2)))
 * (1 + s14_yld_past_switch*(sum((cell(i2,j2), supreg(h2,i2)), pcm_tau(j2, "crop")/fm_tau1995(h2)) - 1));
```

Output variable: `vm_yld(j,"pasture",w)` — pasture yield in tDM/ha/yr. Uses `pcm_tau` (previous time step's tau) rather than `vm_tau` (current), representing delayed knowledge transfer from crop to pasture systems.

---

## Source citation

- Primary source: `/Users/turnip/Documents/Work/Workspace/magpie/magpie-agent/modules/module_14.md` sections 2.1 and 2.2
- Supplementary: `/Users/turnip/Documents/Work/Workspace/magpie/magpie-agent/modules/module_14_notes.md` warning 3
- Documentation status: Fully Verified 2025-10-12; last audited 2026-05-17
