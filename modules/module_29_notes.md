# Module 29 (Cropland) — User Notes & Warnings

**Last updated**: 2026-03-06
**Source**: Deep validation session

---

## ⚠️ Warnings

1. **Cropland is a subset of total land (Module 10)**: Cropland area is constrained by the land balance. Expanding cropland requires reducing pasture, forestry, or natural vegetation — this is a zero-sum game enforced by q10_land_area.

2. **Fallow land**: The `simple_apr24` realization includes fallow land dynamics. Fallow area appears as a separate land pool within cropland. Check which realization is active to understand if fallow is modeled.

## 💡 Tips

- Cropland expansion costs are in Module 39 (land conversion costs).
- Biodiversity impact of cropland expansion depends on Module 44 (biodiversity) and which land type is converted.
