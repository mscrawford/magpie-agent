# Warning: Land Allocation Modification Cascades

**Type**: Warning
**Module**: 10 (Land)
**Submitted**: 2025-10-26 (TEST EXAMPLE)
**Severity**: High

---

## Issue

Modifying `vm_land` bounds or initial values without checking downstream dependencies can cause infeasibility in water allocation (Module 42) and cost calculations (Module 11).

---

## What Happened

While testing a scenario with restricted cropland expansion, I modified `vm_land.up("crop")` in Module 10's bounds file. The model became infeasible with the following error:

```
Model status: 4 (INFEASIBLE)
Binding constraint: q42_water_demand_constraint
```

Root cause: Reducing crop upper bounds reduced water demand, but environmental flow reservations in Module 43 were still calibrated to original land-use patterns, creating inconsistency.

---

## How to Avoid

**Before modifying Module 10**:

1. Check dependency list: Phase2_Module_Dependencies.md#module-10 (23 dependents)
2. Review modification_safety_guide.md (Module 10 section)
3. Pay special attention to:
   - Water allocation (Module 42 & 43)
   - Carbon stocks (Module 52)
   - Total costs (Module 11)

**Testing protocol**:
1. Start with small bound changes (±10%)
2. Run test scenario
3. Check for infeasibility
4. Gradually increase modification magnitude

---

## Verification

- Tested on: MAgPIE 4.6.8
- Scenario: SSP2, RCP2.6
- Region: All regions (global run)
- Code location: modules/10_land/landmatrix_dec18/bounds.gms:45-67

---

## Related Documentation

- Phase2_Module_Dependencies.md (Module 10 has 23 dependents)
- cross_module/land_balance_conservation.md (land area conservation law)
- cross_module/water_balance_conservation.md (water demand calculation)

---

**This is a TEST EXAMPLE for demonstrating the staged feedback workflow.**
