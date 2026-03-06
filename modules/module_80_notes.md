# Module 80 (Optimization) — User Notes & Warnings

**Last updated**: 2026-03-06
**Source**: Deep validation session + infeasibility analysis

---

## ⚠️ Warnings

1. **Retry pipeline**: Module 80 retries solving up to 30 times, cycling through CONOPT4 (3 configurations) → CONOPT3. A single failed solve attempt does NOT mean the model failed.

2. **modelstat=7 is TOLERATED**: MAgPIE does NOT abort on intermediate infeasible (modelstat=7). The solution exists but may not be fully optimal. Check results carefully when this occurs.

3. **13 slack variables** exist across MAgPIE with penalty costs from $100 to $1M per unit. CRITICAL GAP: food, feed, and bioenergy have NO slack variables — these constraints are hard and any violation causes true infeasibility.

## 💡 Tips

- See `agent/helpers/debugging_infeasibility.md` for complete diagnostic workflow.
- See `reference/Infeasibility_Debugging_Guide.md` for the comprehensive 648-line reference.
- The retry pipeline means long solve times may be normal — check `p80_modelstat` to see which attempts succeeded.
