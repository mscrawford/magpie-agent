# module_70_notes.md

**📌 User Feedback & Lessons Learned**

This file contains practical insights, warnings, and lessons from users working with Module 70 (Livestock). These supplement the main documentation in module_70.md.

Last updated: 2025-10-22

---

## ⚠️ Warnings - Don't Do This

### [W001] Don't Modify Feed Baskets Without Checking Dependencies
**Severity**: High | **Added**: 2025-10-22 (example)

If you modify feed basket parameters (`f70_feed_baskets.cs4`) directly, you MUST also check:
- Module 18 (residues) - feed availability calculations depend on this
- Module 60 (bioenergy) - residue competition for feed vs energy
- Module 11 (costs) - feed costs cascade through production costs

**Why this matters**: Feed baskets cascade through 4+ modules. Changing them without coordinated updates can cause:
- Model infeasibility (not enough feed available)
- Incorrect cost calculations
- Broken residue balance

**Do this instead**: Use the scenario configuration switch `c70_feed_scen` to choose between pre-validated feed basket sets:
- `ssp1` - Low livestock demand scenario
- `ssp2` - Medium livestock demand (most commonly used)
- `ssp5` - High livestock demand scenario

**Configuration example**:
```r
cfg$gms$c70_feed_scen <- "ssp2"
```

**References**:
- module_70.md Section 3.2 (Feed Baskets)
- module_18.md Section 2.1 (Residue Availability)
- Phase2_Module_Dependencies.md (Module 70 dependents list)

---

## 💡 Lessons Learned

### [L001] SSP2 Feed Baskets Are Most Stable for Testing
**Tags**: configuration, testing | **Added**: 2025-10-22 (example)

When testing modifications to livestock module or related modules, **always start with SSP2 feed baskets**.

**Why**:
- Most commonly used in published MAgPIE papers
- Well-validated across diverse scenarios
- Intermediate assumptions (between SSP1 low-demand and SSP5 high-demand)
- Less likely to hit corner cases or boundary conditions

**Configuration**:
```r
cfg$gms$c70_feed_scen <- "ssp2"
```

**When to use alternatives**:
- SSP1: Testing low-meat diets, alternative protein scenarios
- SSP5: Testing high-demand, intensive livestock scenarios

**Reference**: Robinson et al. (2014) for feed basket methodology

---

### [L002] Regional vs Cell-Level Computation Matters
**Tags**: spatial, performance | **Added**: 2025-10-22 (example)

**Lesson**: Module 70 calculates livestock feed demand at REGIONAL level (set `i`), not cell level (set `j`).

**Why it matters**:
- Affects computational performance (fewer regions than cells)
- Important for interpreting output data
- If you need cell-level detail, that comes from Module 71 (spatial disaggregation)

**When this comes up**:
- Analyzing output: `vm_prod_reg(i,kli)` is regional
- Performance optimization: Don't expect cell-level resolution here
- Scenario setup: Regional feed baskets get disaggregated later

**Where to find cell-level detail**: See module_71.md for livestock spatial distribution

**Reference**: module_70.md Section 2.1 (equation q70_feed notes)

---

## ✏️ Corrections & Clarifications

### [C001] Module 70 Has 7 Equations, Not 8
**Status**: ✅ Main docs corrected | **Added**: 2025-10-22 (example)

**Previous (incorrect)**: Some early documentation stated "Module 70 contains 8 equations"

**Correct**: Module 70 contains **7 equations** in the fbask_jan16 realization

**Verification**:
```bash
grep "^[ ]*q70_" ../../modules/70_livestock/*/declarations.gms | wc -l
# Returns: 7
```

**Main documentation updated**: module_70.md Section 2 (Overview) corrected on 2025-10-22

---

## 📖 Missing Content - Now Documented

### [M001] Pasture vs Non-Pasture Feed Distinction
**Status**: Partially documented | **Added**: 2025-10-22 (example)

**What was missing**: The distinction between pasture-based feed and non-pasture feed (crops, residues) wasn't clearly explained in module docs.

**Now clarified here**:
- **Pasture feed**: Comes from `vm_land(j,"past")` via Module 31
- **Non-pasture feed**: Includes crop-based feed, residues from Module 18
- Feed basket (`f70_feed_baskets.cs4`) specifies the MIX of these sources

**Why it matters**:
- Affects land use decisions (pasture expansion vs cropland)
- Impacts on biodiversity (pasture vs crops have different BII values)
- Influences carbon accounting (different carbon densities)

**Reference**: module_70.md Section 3.2, module_31.md (pasture)

---

## 🧪 Practical Examples

### [E001] Setting Up Plant-Based Diet Scenario
**Tags**: scenario, diet_change, alternative_protein | **Added**: 2025-10-22 (example)

**Scenario goal**: Model transition to plant-based diets (reduced livestock consumption)

**Approach**:

1. **Reduce livestock demand** (upstream in Module 15):
```r
# Modify food demand projections
# Reduce demand for: livst_milk, livst_rum, livst_pig, livst_chick
# Increase demand for: plant-based alternatives (others category)
```

2. **Switch to lower livestock intensity feed baskets**:
```r
cfg$gms$c70_feed_scen <- "ssp1"  # Lower feed requirements
```

3. **Monitor key outputs**:
- `vm_prod_reg(i,kli)` should decrease over time
- `vm_land(j,"past")` should decline (less pasture needed)
- Emissions from Module 53 should decrease (less enteric fermentation)

4. **Expected cascades**:
- Module 31: Pasture land released for other uses
- Module 11: Lower feed production costs
- Module 52: Carbon sequestration if pasture → forest
- Module 21: Trade patterns shift (less livestock trade)

**Gotchas to avoid**:
- ❌ Don't zero out livestock completely (causes solver issues, unrealistic)
- ❌ Don't make abrupt changes (gradual 10-20 year transitions more realistic)
- ✅ Do check trade implications (Module 21) - some regions may still produce/export
- ✅ Do verify land use makes sense (released pasture should have economic alternative)

**References**:
- module_70.md (this module)
- module_15.md (food demand)
- module_31.md (pasture)
- module_53.md (methane emissions)

---

**Want to add feedback about Module 70?** Run `./scripts/submit_feedback.sh` and select the appropriate template.
