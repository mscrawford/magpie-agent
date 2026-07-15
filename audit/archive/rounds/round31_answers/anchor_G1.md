# Anchor G1: Module 14 Default Realization and Equations

**Question:** What is the default realization of module 14 (yields)? List the equations defined in its equations.gms.

---

## Default Realization

The default (and only) realization of module 14 is **`managementcalib_aug19`**.

Source: `magpie-agent/modules/module_14.md` line 3 — "**Realization:** `managementcalib_aug19`"

---

## Equations Defined in equations.gms

Module 14 defines exactly **2 equations** in `equations.gms`:

| Equation | File:Lines | Description |
|----------|-----------|-------------|
| `q14_yield_crop(j2,kcr,w)` | `equations.gms:14-20` | Crop yield calculation — scales calibrated baseline yields (`i14_yields_calib`) by the ratio of current technological change factor (`vm_tau`) to the 1995 baseline (`fm_tau1995`) |
| `q14_yield_past(j2,w)` | `equations.gms:24-39` | Pasture yield calculation — applies calibrated baseline, an exogenous management factor (`pm_past_mngmnt_factor`), and partial spillover (25% by default, `s14_yld_past_switch = 0.25`) from crop sector technological change using the **previous time step** τ (`pcm_tau`) |

### Equation signatures (from module_14.md)

```gams
q14_yield_crop(j2,kcr,w) ..
 vm_yld(j2,kcr,w) =e= sum(ct,i14_yields_calib(ct,j2,kcr,w)) *
                         vm_tau(j2,"crop") / sum((cell(i2,j2), supreg(h2,i2)), fm_tau1995(h2));

q14_yield_past(j2,w) ..
 vm_yld(j2,"pasture",w) =e=
 sum(ct,(i14_yields_calib(ct,j2,"pasture",w))
 * sum(cell(i2,j2),pm_past_mngmnt_factor(ct,i2)))
 * (1 + s14_yld_past_switch*(sum((cell(i2,j2), supreg(h2,i2)), pcm_tau(j2, "crop")/fm_tau1995(h2)) - 1));
```

---

## Source

- Doc file: `<magpie-agent>/modules/module_14.md`
- Sections 2.1 and 2.2, verified count at Section 13.1
- Status: Fully Verified (2025-10-12)
- Note: Line numbers cited from module_14.md were verified at that doc's last update. For critical work, verify against current GAMS code.
