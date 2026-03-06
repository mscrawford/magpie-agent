# Module 59 (Soil Organic Matter) — User Notes & Warnings

**Last updated**: 2026-03-06
**Source**: Deep validation session

---

## ⚠️ Warnings

1. **8 equations fully documented** (validated 2026-03-06): The `cellpool_aug16` realization was fully verified with equations split into correct sections.

2. **Static vs. dynamic**: The `static_jan19` realization tracks carbon stocks without dynamic feedbacks. The `cellpool_aug16` realization models carbon pool dynamics at cell level — much more computationally intensive.

3. **Interaction with Module 52 (carbon)**: SOM carbon stocks feed into Module 52's total carbon accounting. Changes to tillage or crop residue management affect SOM, which affects carbon sequestration reporting.

## 💡 Tips

- If SOM results seem static despite land-use changes, check which realization is active.
- See `agent/helpers/realization_selection.md` for guidance on choosing between static and dynamic SOM.
