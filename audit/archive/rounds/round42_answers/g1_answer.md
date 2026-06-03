# G1 Answer: Module 14 (Yields) — Default Realization and Equation List

**Question:** What is the default realization of module 14 (yields)? List the equations defined in its equations.gms.

---

## Default Realization

The default (and only active) realization of module 14 is **`managementcalib_aug19`**.

Config citation: `/Users/turnip/Documents/Work/Workspace/magpie/config/default.cfg:354`

```r
cfg$gms$yields <- "managementcalib_aug19"          # def = managementcalib_aug19
```

**Important:** `managementcalib_aug19` is the ONLY realization. An earlier `biocorrect` realization was removed in 2021 (commit `cc84ae5e1`). There is no `input` realization; `modules/14_yields/input/` is the input-data directory, not a realization. (Source: `module_14_notes.md:13`)

---

## Equations in equations.gms

Module 14's `equations.gms` defines exactly **2 equations**:

### 1. `q14_yield_crop`

**File:** `equations.gms:14-20` (cited range per docs; core expression at lines 14-16)

```gams
q14_yield_crop(j2,kcr,w) ..
 vm_yld(j2,kcr,w) =e= sum(ct,i14_yields_calib(ct,j2,kcr,w)) *
                         vm_tau(j2,"crop") / sum((cell(i2,j2), supreg(h2,i2)), fm_tau1995(h2));
```

Calculates cellular crop yields by scaling calibrated baseline yields (`i14_yields_calib`) with the ratio of the current technological change factor (`vm_tau`, at cluster level j) to the 1995 baseline (`fm_tau1995`, at super-region level h).

### 2. `q14_yield_past`

**File:** `equations.gms:24-39` (cited range per docs; core expression at lines 35-39)

```gams
q14_yield_past(j2,w) ..
 vm_yld(j2,"pasture",w) =e=
 sum(ct,(i14_yields_calib(ct,j2,"pasture",w))
 * sum(cell(i2,j2),pm_past_mngmnt_factor(ct,i2)))
 * (1 + s14_yld_past_switch*(sum((cell(i2,j2), supreg(h2,i2)), pcm_tau(j2, "crop")/fm_tau1995(h2)) - 1));
```

Calculates pasture yields using calibrated baseline, an exogenous management factor (`pm_past_mngmnt_factor` from Module 70), and partial spillover from crop-sector technological change. Uses the **previous** time step's τ (`pcm_tau`) rather than current `vm_tau`, representing delayed knowledge transfer from crop to pasture systems. Spillover fraction is controlled by `s14_yld_past_switch` (default 0.25).

---

## Equation Count Verification

The documentation states (🟡 documented, module_14.md:7 and 39 and Section 13.1):

> **Equation Count:** 2

Validator command per docs:
```bash
grep "^[ ]*q14_" modules/14_yields/managementcalib_aug19/declarations.gms | wc -l
# Expected: 2
```

---

## Source Statement

All claims are 🟡 **documented** — sourced from:

- `/Users/turnip/Documents/Work/Workspace/magpie/magpie-agent/modules/module_14.md` (Sections 1, 2, 13.1)
- `/Users/turnip/Documents/Work/Workspace/magpie/magpie-agent/modules/module_14_notes.md:13` (only-realization warning)
- `/Users/turnip/Documents/Work/Workspace/magpie/config/default.cfg:354` (cfg line, read directly this session — 🟢)

Raw GAMS source (`.gms` files) was NOT opened per task constraints. Line number ranges cited from docs were verified at their last doc-update date; line numbers may have drifted since then.
