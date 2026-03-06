# Module 14 (Yields) — User Notes & Warnings

**Last updated**: 2026-03-06
**Source**: Deep validation session

---

## ⚠️ Warnings

1. **Yield calibration is critical**: Module 14 uses `tau` factors (technological change multipliers) from Module 13. If `tc` realization is `off`, yields are static — all scenario results reflect only land-use change, not productivity improvements.

2. **managementcalib vs. kcalibrated**: The `managementcalib_aug19` realization applies a calibration correction (`p14_yields_calib`) that adjusts model yields to match FAO data. Without this calibration, results can diverge significantly from observed production patterns.

## 💡 Tips

- Always check which yield realization is active: `managementcalib_aug19` (default, recommended) applies both tau-based growth and calibration corrections.
- Yield data comes from LPJmL crop model output — if using different climate scenarios, yields change through `f14_yields` input.

## 📝 Lessons from Usage

- Module 14 Last Verified: 2026-01-20 (recently updated)
