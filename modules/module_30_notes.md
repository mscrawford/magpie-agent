# Module 30 (Croparea) — User Notes & Warnings

**Last updated**: 2026-03-06
**Source**: Deep validation session

---

## ⚠️ Warnings

1. **Multiple realizations with different crop allocation approaches**: The `simple_apr24` realization (default) uses simplified allocation. Check which realization is active — they differ in how crop types are distributed across cells.

2. **Realization differences**: `simple_apr24` has 9 equations (q30_prod, q30_betr_missing, q30_cost, q30_rotation_max, q30_rotation_min, q30_carbon, q30_bv_ann, q30_bv_per, q30_crop_reg). `detail_apr24` adds rotation penalties (q30_rotation_penalty) and finer rotation rules (q30_rotation_max2, q30_rotation_min2, q30_rotation_max_irrig). Check which realization is active before debugging rotation constraints.

## 💡 Tips

- Crop area allocation works WITH Module 14 (yields) — higher yields in a cell make that cell preferred for a crop.
- See `agent/helpers/adding_new_crop.md` for how to add new crop types.
