# module_10_notes.md

**📌 User Feedback & Lessons Learned**

This file contains practical insights, warnings, and lessons from users working with Module 10 (Land). These supplement the main documentation in module_10.md.

Last updated: 2025-10-22

---

## ⚠️ Warnings - Don't Do This

### [W001] Don't Modify Module 10 Without Thorough Testing - It's High-Centrality
**Severity**: CRITICAL | **Added**: 2025-10-22 (example)

Module 10 is one of the **4 highest-centrality modules** in MAgPIE (along with 11, 17, 56). It has 23 dependent modules.

**What this means**: Changes to land allocation affect almost everything:
- Water (Modules 42, 43) - land use determines irrigation demand
- Carbon (Module 52) - land types have different carbon densities
- Biodiversity (Module 44) - land use change impacts BII
- Costs (Module 11) - land conversion and maintenance costs
- Production (Module 17) - available agricultural land constrains output

**Real-world example of what can go wrong**:
```
User forced cropland expansion in water-stressed regions
→ Module 42 water demand increased
→ Module 43 couldn't supply enough water
→ Model infeasibility in 2050
```

**Do this instead**:
1. **Before modifying**, read: `cross_module/modification_safety_guide.md` (Module 10 section)
2. **Check conservation laws**: `cross_module/land_balance_conservation.md`
3. **Test in stages**:
   - Single region first
   - One time period at a time
   - Monitor key variables: `vm_land`, `vm_water`, `vm_cost`
4. **Use debugger** if infeasibilities occur

**References**:
- modification_safety_guide.md Section 2 (Module 10 safety protocols)
- Phase2_Module_Dependencies.md (Module 10 has 23 dependents)
- land_balance_conservation.md (land area is strictly conserved)

---

### [W002] Land Area is Strictly Conserved - Don't Violate This
**Severity**: High | **Added**: 2025-10-22 (example)

The equation `q10_land_area` enforces **strict equality**:
```
sum(land_types) = pm_land_hist(j) [constant for each cell]
```

**What you CAN'T do**:
- Add land types without removing others
- Expand total land area
- Shrink total land area
- Have negative land areas

**What WILL happen if you try**:
- Model infeasibility
- Solver crashes
- Nonsensical results

**What you CAN do**:
- Shift land between types (primforest → secdforest → crop → past, etc.)
- Change transition rates
- Modify costs of conversion (Module 39)
- Constrain certain transitions (Module 22 conservation)

**Verification**:
```r
# Check land balance holds
sum(vm_land(j,land)) == pm_land_hist(j)  # Must be TRUE for all j
```

**Reference**: land_balance_conservation.md Section 1 (Land Area Conservation)

---

## 💡 Lessons Learned

### [L001] Understanding the Land Transition Matrix
**Tags**: land_transitions, debugging | **Added**: 2025-10-22 (example)

**Lesson**: Not all land transitions are bidirectional or even allowed.

**Key insights**:
- **Primary forest → Secondary forest**: One-way only (via Module 35 natural vegetation loss)
- **Secondary forest → Cropland**: Allowed (deforestation)
- **Cropland → Secondary forest**: Allowed (abandonment, natural regrowth)
- **Primary forest ↔ Cropland**: NOT direct (must go through secondary forest first)

**Why this matters for debugging**:
If you expect a land transition that's not happening:
1. Check if that transition is even allowed
2. Check conservation constraints (Module 22) - protected areas block transitions
3. Check economic incentives - is there pressure for that change?

**Common debugging scenario**:
```
"Why isn't primary forest converting to cropland?"

Answer: It can't directly. It must:
1. Primary → Secondary (Module 35, if not protected)
2. Secondary → Cropland (Module 29, if economic pressure exists)
```

**Reference**: land_balance_conservation.md Section 2 (Land Transitions)

---

### [L002] Cell-Level vs Regional-Level Land Decisions
**Tags**: spatial, model_structure | **Added**: 2025-10-22 (example)

**Lesson**: Land allocation happens at CELL level (set `j`), making MAgPIE spatially explicit.

**What this means**:
- Each cell has its own land endowment (`pm_land_hist(j)`)
- Land can't move between cells (no teleportation!)
- Regional totals are sums: `sum(j in region, vm_land(j,land))`

**When this matters**:
- **Scenario design**: Regional land targets need to be achievable within cell endowments
- **Output analysis**: Some cells may hit constraints others don't
- **Performance**: More cells = more decision variables = slower solve time

**Example**:
```
Europe total land: 100 Mha
But individual cells have different suitability for crops
→ Can't just divide 100 Mha / cells equally
→ Model optimizes based on cell-specific costs and yields
```

**Reference**: Phase1_Core_Architecture.md (spatial sets and dimensions)

---

## ✏️ Corrections & Clarifications

### [C001] Land Type Set Names
**Status**: ✅ Clarified | **Added**: 2025-10-22 (example)

**Clarification needed**: The set `land` contains 7 land types, and the naming can be confusing.

**Correct names** (as used in the model):
- `crop` - Cropland
- `past` - Pasture
- `forestry` - Managed forests
- `primforest` - Primary forest
- `secdforest` - Secondary forest
- `urban` - Urban land
- `other` - Other natural land

**Common mistakes**:
- Calling it "crops" (plural) - model uses "crop" (singular)
- Confusing "forestry" with "primforest" - different types!
- Not distinguishing primary vs secondary forest

**Reference**: module_10.md Section 1 (Sets)

---

## 📖 Missing Content - Now Documented

### [M001] Protected Areas Prevent Transitions
**Status**: Documented here | **Added**: 2025-10-22 (example)

**What was missing**: The interaction between Module 10 (land) and Module 22 (conservation) wasn't obvious from module_10.md alone.

**Key mechanism**:
- Module 22 sets: `pm_land_conservation(t,j,land_type)`
- This acts as a LOWER BOUND on `vm_land(j,land_type)`
- Protected land CANNOT transition to other types

**Practical implication**:
If your scenario has conservation policies enabled and you're wondering why land isn't transitioning:
```r
# Check if land is protected
display pm_land_conservation;
# Non-zero values = that land type is protected in that cell
```

**Common debugging situation**:
```
"Why isn't primary forest in Brazil converting to cropland?"

Check:
1. Is c22_conservation_policy != "none"? → Yes
2. Does pm_land_conservation(t,brazil_cells,"primforest") > 0? → Yes
3. Conclusion: Protected area constraint is active
```

**References**:
- module_22.md (conservation policies)
- land_balance_conservation.md Section 2.2 (constrained transitions)

---

## 🧪 Practical Examples

### [E001] Debugging Land Use Infeasibilities
**Tags**: debugging, troubleshooting | **Added**: 2025-10-22 (example)

**Situation**: Model becomes infeasible, solver messages mention land-related constraints.

**Debugging checklist**:

1. **Check land balance** (most common issue):
```r
# Does sum of land types equal total?
sum(vm_land(j,land)) =?= pm_land_hist(j)
```

2. **Check conservation constraints**:
```r
# Is protected area larger than available?
pm_land_conservation(t,j,"primforest") > vm_land.up(j,"primforest")
```

3. **Check urban land expansion** (Module 34):
```r
# Urban land only increases, never decreases
# Is urban demand exceeding total land?
vm_land(j,"urban") > pm_land_hist(j)
```

4. **Check for negative land**:
```r
# Any land type going negative?
vm_land.lo(j,land) >= 0
```

5. **Examine transition costs** (Module 39):
```r
# Are conversion costs prohibitively high?
display vm_cost_land_conversion;
```

**Common fixes**:
- Reduce conservation stringency
- Adjust urban land projections
- Modify transition costs
- Check input data for errors (pm_land_hist)

**Reference**: circular_dependency_resolution.md (debugging guide)

---

### [E002] Setting Up Afforestation Scenario
**Tags**: scenario, climate_mitigation, afforestation | **Added**: 2025-10-22 (example)

**Scenario goal**: Increase forest area for carbon sequestration.

**Approach**:

1. **Enable afforestation** (Module 32):
```r
cfg$gms$c32_aff_policy <- "npi"  # National afforestation policies
```

2. **Set carbon price** to incentivize (Module 56):
```r
cfg$gms$c56_pollutant_prices <- "SSP2"
cfg$gms$c56_emis_policy <- "all"
```

3. **Monitor land transitions**:
- `vm_land(j,"secdforest")` should increase (afforestation)
- `vm_land(j,"crop")` or `vm_land(j,"past")` should decrease (freed land)
- `vm_carbon_stock(j,"vegc")` should increase over time

4. **Expected behavior**:
- Module 32 (forestry) creates new forest area
- Module 10 (land) allocates it, respecting land balance
- Module 52 (carbon) tracks sequestration
- Module 56 (GHG policy) values the carbon removed

**Gotchas**:
- ❌ Afforestation competes with food production (land is scarce!)
- ❌ Not all cells equally suitable for forests (check `pm_carbon_density`)
- ✅ Realistic scenarios have gradual afforestation (10-30 years)
- ✅ Check food security impacts (Module 15, 21)

**References**:
- module_32.md (afforestation)
- module_52.md (carbon sequestration)
- circular_dependency_resolution.md Section 3.4 (Forest-Carbon cycle)

---

**Want to add feedback about Module 10?** Run `./scripts/submit_feedback.sh` and select the appropriate template.
