# Module 42 (Water Demand) — User Notes & Warnings

**Last updated**: 2026-03-06
**Source**: Deep validation session

---

## ⚠️ Warnings

1. **Water module can be turned off**: The `off` realization removes all water constraints — useful for testing but produces unrealistic irrigation expansion.

2. **Water availability is from Module 43**: Water demand (42) must not exceed supply (43). When it does and there's no flexibility, the model becomes infeasible.

## 💡 Tips

- Water-related infeasibility is common in dry regions with high food demand — check `agent/helpers/debugging_infeasibility.md`.
- See `cross_module/water_balance_conservation.md` for the water balance mechanics.
