# Module 35 (Natural Vegetation) — User Notes & Warnings

**Last updated**: 2026-03-06
**Source**: Deep validation session

---

## ⚠️ Warnings

1. **32 equations total** (validated 2026-03-06): This is one of MAgPIE's most complex modules. 21 equations were added during deep validation — many govern age-class dynamics, disturbance rates, and NPI/NDC constraints.

2. **Disturbance rates are NOT mechanistic fire modeling**: Module 35 applies historical disturbance rates labeled "fire" and "other" — these are fixed rates from input data, not process-based fire simulation. Don't describe MAgPIE as "modeling wildfire."

3. **Strong interaction with Module 22 (conservation)**: Protected area constraints from Module 22 set lower bounds on natural vegetation area. Changes to conservation targets directly constrain Module 35.

## 💡 Tips

- Always check Module 22 settings when analyzing natural vegetation outcomes.
- NPI/NDC constraints (p35_min_forest) can create infeasibility if combined with high bioenergy or agricultural expansion.
