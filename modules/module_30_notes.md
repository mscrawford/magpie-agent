# Module 30 (Croparea) — User Notes & Warnings

**Source**: Deep validation session

---

## ⚠️ Warnings

1. **Multiple realizations with different crop allocation approaches**: The `simple_apr24` realization (default) uses simplified allocation. Check which realization is active — they differ in how crop types are distributed across cells.

2. **Realization differences**: `simple_apr24` has 9 equations (q30_prod, q30_betr_missing, q30_cost, q30_rotation_max, q30_rotation_min, q30_carbon, q30_bv_ann, q30_bv_per, q30_crop_reg). `detail_apr24` adds rotation penalties (q30_rotation_penalty) and finer rotation rules (q30_rotation_max2, q30_rotation_min2, q30_rotation_max_irrig). Check which realization is active before debugging rotation constraints.

3. **R24 (2026-05-24) — `vm_area` consumer list corrected**: Earlier wording in `module_30.md` listed M38 (factor costs) as a consumer of `vm_area(j,kcr,w)`. M38 has **zero** references to `vm_area` across all three of its realizations (`per_ton_fao_may22`, `sticky_feb18` default, `sticky_labor`). Earlier wording also omitted M29 (cropland), which consumes `vm_area` directly in its `q29_cropland` equation. **Correct consumer set**: {18, 29, 41, 42, 50, 53, 59}. (Source: R24 audit Q4-B4.)

4. **R24 (2026-05-24) — `vm_carbon_stock_croparea` is a one-hop variable, NOT a direct M52/M56 input**: Earlier wording at `module_30.md:360` said the variable "is used by Module 52 (Carbon) and Module 56 (GHG Policy)". Direct verification: only **M29** reads `vm_carbon_stock_croparea` (in `q29_carbon`), aggregating it into `vm_carbon_stock(j,"crop",ag_pools)`. M52 and M56 then read the aggregated `vm_carbon_stock`. Same one-hop pattern as the G2 calibration anchor — be explicit about declarer-vs-aggregator-vs-reader.

## 💡 Tips

- Crop area allocation works WITH Module 14 (yields) — higher yields in a cell make that cell preferred for a crop.
- See `agent/helpers/adding_new_crop.md` for how to add new crop types.
