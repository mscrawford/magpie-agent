# Module 30 (Croparea) — User Notes & Warnings

**Last updated**: 2026-03-06
**Source**: Deep validation session

---

## ⚠️ Warnings

1. **Multiple realizations with different crop allocation approaches**: The `simple_apr24` realization (default) uses simplified allocation. Check which realization is active — they differ in how crop types are distributed across cells.

2. **3 equations added in simple_apr24**: q30_land_snv, q30_treecover, q30_rotation_penalty were documented during deep validation. These handle semi-natural vegetation on cropland, tree cover requirements, and rotation constraints respectively.

## 💡 Tips

- Crop area allocation works WITH Module 14 (yields) — higher yields in a cell make that cell preferred for a crop.
- See `agent/helpers/adding_new_crop.md` for how to add new crop types.
