# Module 14 (Yields) — User Notes & Warnings

**Source**: Deep validation session; 2026-05-17 LPJmL-yields audit

---

## ⚠️ Warnings

1. **Yield calibration is critical**: Module 14 uses `tau` factors (technological change multipliers) from Module 13. If `tc` realization is `off`, yields are static — all scenario results reflect only land-use change, not productivity improvements.

2. **managementcalib vs. kcalibrated**: The `managementcalib_aug19` realization applies a calibration correction (`i14_yields_calib`) that adjusts model yields to match FAO data. Without this calibration, results can diverge significantly from observed production patterns.

3. **`managementcalib_aug19` is the only realization**: `module.gms` has a single `$Ifi` branch. An earlier `biocorrect` realization was removed in 2021 (commit `cc84ae5e1`); there is no `input` realization (`modules/14_yields/input/` is the input-data directory). Section 18 of `module_14.md` was corrected on 2026-05-17 (it had listed `biocorrect` and `input` as alternative realizations).

4. **Degradation input file has no standard producer**: the `s14_degradation` block reads `f14_yld_ncp_report.cs3`, but a 2026-05-17 audit found no preprocessing function produces a file by that name. `calcDegradationYieldReduction` (mrmagpie) instead writes a differently-named `f14_degradation_yld_reduc_<ctype>.mz`. The two sides do not connect. This is dormant because `s14_degradation = 0` by default; if you enable degradation, verify the input file is actually supplied. (Audit observation, not a confirmed root cause - the rename/packaging path was not traced.)

## 💡 Tips

- Always check which yield realization is active: `managementcalib_aug19` (default, recommended) applies both tau-based growth and calibration corrections.
- Yield data comes from LPJmL crop model output — if using different climate scenarios, yields change through `f14_yields` input.

## 📝 Lessons from Usage

- Module 14 Last Verified: 2026-05-17 (LPJmL-yields audit: corrected dead realization list and drifted `input.gms` citations)
