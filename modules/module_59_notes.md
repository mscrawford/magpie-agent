# Module 59 (Soil Organic Matter) — User Notes & Warnings

**Source**: Deep validation session

---

## ⚠️ Warnings

1. **8 equations fully documented** (validated 2026-03-06): The `cellpool_jan23` realization was fully verified with equations split into correct sections.

2. **Static vs. dynamic**: The `static_jan19` realization tracks carbon stocks without dynamic feedbacks. The `cellpool_jan23` realization models carbon pool dynamics at cell level — much more computationally intensive.

3. **Interaction with Module 52 (carbon)**: SOM carbon stocks feed into Module 52's total carbon accounting. Changes to tillage or crop residue management affect SOM, which affects carbon sequestration reporting.

4. **Soil carbon carry-forward bug fix (develop commit 931db85c4, 2026-06-25)**: Both SOM realizations now carry the soil carbon stock forward each timestep in `postsolve.gms` (`pcm_carbon_stock(j,land,"soilc",stockType) = vm_carbon_stock.l(...)`; `cellpool_jan23/postsolve.gms:13`, `static_jan19/postsolve.gms:9`). Previously this line was absent: `pcm_carbon_stock` for the soil pool stayed at its preloop initialization, so the soil emission term in `q52_emis_co2_actual` / `q56_emis_pricing_co2` was a cumulative-since-init change over a single timestep length (soil pools off by about 17x in a default H12 run) rather than a per-timestep flux. **Default runs are NOT affected** (the default `c56_emis_policy = reddnatveg_nosoil` excludes soil, and dynamic-SOM soil reporting routes through `magpie4::emisSOC`). Affected: soil-inclusive emission/cap policies, or post-processing that reads per-pool soil `vm_emissions_reg` directly.

## 💡 Tips

- If SOM results seem static despite land-use changes, check which realization is active.
- See `agent/helpers/realization_selection.md` for guidance on choosing between static and dynamic SOM.
