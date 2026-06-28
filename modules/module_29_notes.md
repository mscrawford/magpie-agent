# Module 29 (Cropland) — User Notes & Warnings

**Source**: Deep validation session; 2026-04-20 sync with MAgPIE develop (PR #869)

---

## ⚠️ Warnings

1. **Cropland is a subset of total land (Module 10)**: Cropland area is constrained by the land balance. Expanding cropland requires reducing pasture, forestry, or natural vegetation — this is a zero-sum game enforced by q10_land_area.

2. **Fallow land**: Fallow dynamics are modeled in the **default `detail_apr24`** realization — `vm_fallow` enters total cropland in `q29_cropland` (`modules/29_cropland/detail_apr24/equations.gms:12`) and is governed by a minimum-fallow penalty `q29_fallow_min` (`modules/29_cropland/detail_apr24/equations.gms:66-68`). The `simple_apr24` realization **fixes fallow to zero** (`modules/29_cropland/simple_apr24/preloop.gms:9` `vm_fallow.fx(j)=0`; `realization.gms:9`), so total cropland equals croparea there. (Corrects an earlier note that inverted this, attributing fallow dynamics to `simple_apr24`.)

3. **Tree cover carbon density uses UNCALIBRATED Chapman-Richards curves as of 2026-04-20** (commit `75d7ee167`): `modules/29_cropland/detail_apr24/preloop.gms:46,48` now reads `pm_carbon_density_secdforest_ac_uncalib` and `pm_carbon_density_plantation_ac_uncalib` (instead of the calibrated `_ac` variants). This is deliberate: tree cover represents *new establishment* (similar to afforestation), not existing managed forest, so the uncalibrated growth curve is appropriate. See `module_52.md` Section 2.C for the distinction.

## 💡 Tips

- Cropland expansion costs are in Module 39 (land conversion costs).
- Biodiversity impact of cropland expansion depends on Module 44 (biodiversity) and which land type is converted.
- The `s29_treecover_plantation` switch toggles between secdforest-uncalib (=0) and plantation-uncalib (=1) growth curves for tree cover on cropland.
