# Anchor G1: Module 14 (Yields) — Default Realization & Equations

**Question:** What is the default realization of module 14 (yields)? List the equations defined in its equations.gms.

**Sources used (doc-only, no GAMS code read):**
- `modules/module_14.md`
- `modules/module_14_notes.md`

---

## Answer

### Default realization

**`managementcalib_aug19`**

- `modules/module_14.md` header: "# Module 14: Yields (managementcalib_aug19)" and "**Realization:** `managementcalib_aug19`" (module_14.md:1,3).
- `modules/module_14_notes.md` confirms it is the **only** realization, and explicitly names it the default:
  - "**`managementcalib_aug19` is the only realization**: `module.gms` has a single `$Ifi` branch. An earlier `biocorrect` realization was removed in 2021 (commit `cc84ae5e1`); there is no `input` realization (`modules/14_yields/input/` is the input-data directory)." (module_14_notes.md:13)
  - Tips section: "Always check which yield realization is active: `managementcalib_aug19` (default, recommended) applies both tau-based growth and calibration corrections." (module_14_notes.md:19)

### Equations defined in equations.gms

`modules/module_14.md` states in the header: "**Equation Count:** 2" (module_14.md:6), and in Section 2: "Module 14 implements only 2 equations, but relies on extensive preloop calibration to prepare the input data." (module_14.md:39)

1. **`q14_yield_crop`** — Crop Yield Calculation
   - Citation: `equations.gms:14-16` (module_14.md:43), also cited as `equations.gms:14-20` (module_14.md:79)
   - Code as quoted in doc:
     ```gams
     q14_yield_crop(j2,kcr,w) ..
      vm_yld(j2,kcr,w) =e= sum(ct,i14_yields_calib(ct,j2,kcr,w)) *
                              vm_tau(j2,"crop") / sum((cell(i2,j2), supreg(h2,i2)), fm_tau1995(h2));
     ```
   - What it does (per doc): calculates cellular crop yields by scaling calibrated baseline yields (`i14_yields_calib`) by the ratio of the current technological-change factor (`vm_tau`) to the 1995 baseline (`fm_tau1995`).

2. **`q14_yield_past`** — Pasture Yield Calculation
   - Citation: `equations.gms:35-39` (module_14.md:85), also cited as `equations.gms:24-39` (module_14.md:120)
   - Code as quoted in doc:
     ```gams
     q14_yield_past(j2,w) ..
      vm_yld(j2,"pasture",w) =e=
      sum(ct,(i14_yields_calib(ct,j2,"pasture",w))
      * sum(cell(i2,j2),pm_past_mngmnt_factor(ct,i2)))
      * (1 + s14_yld_past_switch*(sum((cell(i2,j2), supreg(h2,i2)), pcm_tau(j2, "crop")/fm_tau1995(h2)) - 1));
     ```
   - What it does (per doc): calculates pasture yields from the calibrated baseline, an exogenous pasture-management factor (`pm_past_mngmnt_factor`, from Module 70), and a partial spillover term using the **previous** time step's crop τ (`pcm_tau`, not current `vm_tau`), scaled by `s14_yld_past_switch` (default 0.25).

Note: the doc's own equation-count statement ("2") is taken verbatim from module_14.md and not independently recomputed, per this session's no-tools/no-GAMS-code constraint.

---

## Verification badges

- 🟡 Documented — both equations and the realization/default claim are read from `modules/module_14.md` and `modules/module_14_notes.md` this session.
- No raw GAMS code (`.gms` files) was read in this session; equation text above is exactly as quoted inside the markdown docs, not independently re-verified against `../modules/14_yields/managementcalib_aug19/equations.gms`.
