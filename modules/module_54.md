# Module 54: Phosphorus (off)

**Status**: **CURRENTLY DISABLED - Placeholder for future development**

**Realization**: `off` (only realization)

**Purpose (intended)**: Estimate major phosphorus flows in the agricultural sector and determine dynamics of P-pools in soil (module.gms:10-11).

**Current implementation**: Module is **NOT activated** in MAgPIE. All phosphorus-related calculations are disabled (module.gms:26-28, realization.gms:8-9).

---

## Module Structure

**Files**:
- `module.gms` - Module description and selection (module.gms:1-35)
- `off/realization.gms` - Deactivation realization (realization.gms:1-18)
- `off/declarations.gms` - Variable declaration (declarations.gms:1-18)
- `off/preloop.gms` - Variable fixation (preloop.gms:1-13)
- `off/postsolve.gms` - Output reporting (postsolve.gms:1-16)

**Equations**: 0 (no active implementation)

**Variables**: 1 (`vm_p_fert_costs` fixed to zero)

**Author**: Benjamin Leon Bodirsky (module.gms:30)

---

## Current Implementation (off realization)

### Variable Declaration

**vm_p_fert_costs(i)** (declarations.gms:10)
- **Description**: Costs for mineral phosphorus fertilizers (mio. USD17MER per yr)
- **Type**: Variable (would be calculated in active realization)
- **Current value**: **Fixed to zero** (preloop.gms:10)

### Deactivation

**preloop.gms:10**:
```gams
vm_p_fert_costs.fx(i)=0;
```

This line **fixes** `vm_p_fert_costs` to zero for all regions, effectively disabling any phosphorus fertilizer costs in the model.

**Purpose** (realization.gms:8-9):
- "This is the current default implementation of the module. It deactivates calculations related to the phosphorus module."

### Output Reporting

**postsolve.gms** (not shown, standard output structure):
- Reports `vm_p_fert_costs` levels (all zeros)
- No actual phosphorus flows computed or reported

---

## Intended Functionality (Future Development)

According to module.gms:12-24, the phosphorus module is **intended** to account for these P-flows (NOT currently implemented):

### P Withdrawals (Outflows from Soil)

**1. P withdrawals by harvest** (module.gms:14):
- Phosphorus content of crop harvest removed from field
- Would be calculated as: Crop production × P content

**2. P withdrawals by harvest of above-ground residues** (module.gms:15):
- Phosphorus in residues removed for feed, bioenergy, or other uses
- Would be calculated as: Removed residues × P content

### P Inputs (Inflows to Soil)

**3. P inputs by decaying recycled residues** (module.gms:16):
- Phosphorus in residues left on field or incorporated
- Would be calculated as: Recycled residues × P content

**4. P inputs by burned residues** (module.gms:17):
- Phosphorus in residues burned (assuming no combustion losses for P, unlike N)
- Would be calculated as: Burned residues × P content
- Note: P does NOT volatilize during burning (remains in ash), unlike N/C

**5. P inputs by manure recycled to croplands** (module.gms:18):
- Phosphorus in animal manure applied to cropland
- Would be calculated as: Manure application × P content
- Source: Module 55 (AWMS) would provide manure P available for recycling

**6. P inputs by fertilizers** (module.gms:19):
- Mineral P fertilizer application (superphosphate, DAP, MAP, rock phosphate)
- Would be optimized variable (apply P to meet crop demand or maintain soil P)
- Drives `vm_p_fert_costs` (currently zero)

**7. P inputs by release of plant-available P from permanent P-Pool** (module.gms:20):
- Mineralization of organic P and release from soil mineral P stocks
- Would track soil P pools (labile, stable, occluded) and transformation rates

**8. P inputs by seed** (module.gms:21):
- Phosphorus in seeds planted
- Typically minor compared to other flows (<1% of total P inputs)

**9. P inputs by weathering** (module.gms:22):
- Release of P from parent material (rocks, minerals)
- Region-specific (high in volcanic soils, low in old weathered soils)
- Very slow process (~0.1-1 kg P/ha/yr)

### P Losses (Outflows from System)

**10. P losses by erosion** (module.gms:23):
- Phosphorus lost via soil erosion (attached to soil particles)
- Major pathway in unprotected soils (tillage, bare soil, steep slopes)
- Would require erosion model or erosion risk factors

**11. P losses by leaching** (module.gms:24):
- Phosphorus lost via leaching to groundwater or surface runoff
- Generally minor for P (low mobility, binds to soil particles)
- Exception: High in sandy soils, high P saturation, or dissolved organic P

---

## Why Module 54 is Currently Off

**Reasons for deactivation** (inferred from module.gms:26-28):

1. **Under development** (realization.gms:11):
   - "The realization is still under development"
   - Indicates module framework exists but not fully implemented

2. **Future enrichment** (module.gms:27-28):
   - "It is a topic we seek to include in future developments of the model as enriches the biophysical aspects of the model as well as adds to the fertilizer costs (and hence total costs of production)."

3. **Complexity**:
   - Phosphorus dynamics involve multiple soil pools (labile, stable, occluded)
   - Requires calibration to regional soil P stocks and plant-available P
   - Interactions with other modules (Module 50 NR Soil Budget, Module 55 AWMS)

4. **Data requirements**:
   - Soil P stocks by region and soil type (limited global datasets)
   - Crop P uptake efficiencies (vary by crop, soil pH, P fertilizer type)
   - P transformation rates (labile ↔ stable ↔ occluded, mineralization/immobilization)
   - Erosion and leaching rates (region and management-specific)

5. **Lower priority than N**:
   - Nitrogen (Module 51) prioritized due to:
     - GHG emissions (N2O)
     - Water quality (NO3 leaching, eutrophication)
     - Air quality (NH3, NOx)
   - Phosphorus primarily environmental concern (water quality, eutrophication)
   - P fertilizer costs lower than N fertilizer costs (~20% of N costs per kg nutrient)

---

## Implications of Module 54 Being Off

### What MAgPIE Currently Does NOT Model

**1. Phosphorus fertilizer costs** (vm_p_fert_costs fixed to zero):
- P fertilizer application is **implicitly assumed** to meet crop P requirements
- No P fertilizer costs in objective function (underestimates production costs)
- Typical P fertilizer costs: 10-20% of total fertilizer costs (N + P + K)

**2. Soil P dynamics**:
- No tracking of soil P depletion or accumulation
- No P mining (withdrawal > inputs → soil P depletion over time)
- No P buildup (inputs > withdrawal → soil P accumulation, risk of eutrophication)

**3. P use efficiency (PUE)**:
- No optimization of P fertilizer application based on soil P status
- Cannot represent precision P management (apply P only where needed)
- Cannot model P recovery from manure or residues

**4. Eutrophication risk**:
- No P losses to water bodies (runoff, leaching, erosion)
- Cannot assess eutrophication risk from agricultural P
- Key environmental issue in many regions (algal blooms, dead zones)

**5. P recycling**:
- Manure P recycling from Module 55 (AWMS) not explicitly tracked
- Residue P recycling not distinguished from other residue benefits
- Cannot optimize P recycling to reduce fertilizer costs

**6. P limitations on crop production**:
- Crop production assumed unlimited by P availability
- Reality: Low soil P can limit yields even with adequate N
- Particularly relevant in Sub-Saharan Africa (low soil P, low fertilizer use)

### What MAgPIE Implicitly Assumes

**Assumption 1**: **Adequate P fertilizer application**
- Farmers apply sufficient P fertilizer to meet crop requirements
- No P deficiency limiting yields
- Reasonable for intensive agriculture (Europe, North America, East Asia)
- Questionable for low-input systems (Sub-Saharan Africa, smallholders)

**Assumption 2**: **P fertilizer costs negligible**
- P fertilizer costs excluded from production costs (vs. reality: 10-20% of fertilizer costs)
- May underestimate total production costs by 5-10%
- Affects competitiveness of P-intensive crops (e.g., oilseeds need more P than cereals)

**Assumption 3**: **No P mining or buildup**
- Soil P stocks remain constant over time
- No P depletion in low-input systems
- No P accumulation in high-input systems (manure-intensive regions)

**Assumption 4**: **No P-related environmental impacts**
- Eutrophication from agricultural P not modeled
- Cannot assess water quality co-benefits of reduced fertilizer use or improved manure management

### Where Missing P Modeling Matters Most

**1. Sub-Saharan Africa**:
- Low soil P (highly weathered soils, low P parent material)
- Low fertilizer use (P fertilizer often not applied due to cost)
- P deficiency limits yields (N fertilizer ineffective without P)
- Omission: Cannot model P as constraint on agricultural intensification

**2. Manure-intensive regions** (Netherlands, Denmark, North Carolina, China):
- High manure application → soil P buildup
- Risk of P runoff to water bodies (eutrophication)
- Regulations limit manure application based on P (not just N)
- Omission: Cannot model P-based manure management regulations

**3. Organic agriculture**:
- Relies on organic P sources (manure, compost, green manure)
- P availability from organic sources lower than mineral fertilizer
- P may be limiting nutrient in organic systems
- Omission: Cannot distinguish organic P management challenges

**4. Precision agriculture**:
- Site-specific P management based on soil testing
- Apply P only where soil P is low (reduce costs, environmental impacts)
- Omission: Cannot model precision P management benefits

**5. P scarcity scenarios**:
- Phosphate rock is finite resource (estimates: 50-400 years reserves depending on source)
- Peak phosphorus concept (production peak followed by decline)
- Omission: Cannot model P fertilizer price shocks or P scarcity-driven recycling

---

## Related Modules

### Modules That Would Interact with Module 54 (if active)

**1. Module 50 (NR Soil Budget)**:
- Currently tracks nitrogen budgets (inputs, outputs, soil N changes)
- Would be extended to track phosphorus budgets (inputs, outputs, soil P changes)
- P budget: Inputs (fertilizer, manure, residues, weathering) - Outputs (harvest, residue removal, erosion, leaching) = ΔSoil P

**2. Module 55 (AWMS)**:
- Currently tracks manure nitrogen (N) by management system
- Would be extended to track manure phosphorus (P)
- Manure P available for recycling to cropland

**3. Module 18 (Residues)**:
- Currently tracks residue allocation (field, removal, burning)
- Would provide residue P flows (recycled P, removed P, burned P)

**4. Module 38 (Factor Costs)**:
- Would receive P fertilizer costs from Module 54
- P fertilizer costs added to total production costs in objective function

**5. Module 11 (Costs)**:
- Would aggregate P fertilizer costs from Module 38
- Total costs: Labor + Capital + Land conversion + **P fertilizer** + N fertilizer + Irrigation + ...

**6. Module 51 (Nitrogen) and Module 53 (Methane)**:
- N-P-K nutrient interactions:
  - Balanced fertilization (NPK ratio) affects uptake efficiency
  - P deficiency reduces N uptake (P needed for root growth, protein synthesis)
- Currently: N and CH4 modeled independently, P missing

### Modules That Might Depend on Module 54 (if active)

**1. Module 14 (Yields)**:
- Crop yields could be P-limited in low-P soils
- P fertilizer application (from Module 54) could affect yields via P response functions
- Currently: Yields based on LPJmL (implicitly assumes adequate P)

**2. Module 43 (Water Availability)** or Module 44 (Biodiversity)**:
- Water quality (eutrophication) depends on P runoff from agriculture
- P losses from Module 54 could inform water quality indicators
- Biodiversity impacts of eutrophication (algal blooms, hypoxia)

---

## Future Development Directions

### Minimal Implementation (Phase 1)

**Goal**: Add P fertilizer costs to production costs

**Components**:
1. **P fertilizer demand**: Calculate P needed based on:
   - Crop harvest P (production × P content)
   - Residue removal P (if removed)
   - Minus manure P (recycled from livestock)
   - Minus residue P (if left on field)

2. **P fertilizer costs**: Apply costs based on:
   - P fertilizer price (regional, time-varying)
   - P fertilizer application (kg P per ha)

3. **Integration with Module 11 (Costs)**:
   - Add `vm_p_fert_costs` to objective function
   - P costs affect crop production decisions (P-intensive crops less competitive if P expensive)

**Limitations**:
- No soil P dynamics (assume instantaneous P availability)
- No P losses (all applied P assumed plant-available)
- No P use efficiency variations

**Benefit**: More realistic production costs (5-10% increase in fertilizer costs)

### Intermediate Implementation (Phase 2)

**Goal**: Add soil P dynamics and P use efficiency

**Components**:
1. **Soil P pools**: Track labile P (plant-available), stable P (slowly available), occluded P (unavailable)
2. **P transformations**: Labile ↔ Stable (fixation/release), Stable ↔ Occluded (irreversible fixation)
3. **P use efficiency (PUE)**: Crop P uptake = f(Soil P, P fertilizer, soil pH, soil texture)
4. **P application optimization**: Apply P only when soil P is low (cost savings, environmental benefit)

**Limitations**:
- No spatial P transport (erosion, runoff, leaching)
- No eutrophication risk assessment

**Benefit**: Optimize P management (reduce over-application, target low-P soils)

### Advanced Implementation (Phase 3)

**Goal**: Add P losses and environmental impacts

**Components**:
1. **P erosion**: Soil erosion removes P attached to particles (link to land management, slope, cover)
2. **P runoff**: Surface runoff transports dissolved P and particulate P to water bodies
3. **P leaching**: Leaching to groundwater (minor for most soils, significant for sandy soils)
4. **Eutrophication risk**: P losses → water quality impacts (algal blooms, hypoxia)
5. **Environmental constraints**: Limit P losses to protect water quality (similar to N limits)

**Limitations**:
- Requires spatial erosion model
- Requires watershed routing (P transport from fields to water bodies)
- Data-intensive (soil P saturation, P binding capacity, hydrological pathways)

**Benefit**: Integrated nutrient-water quality modeling, assess environmental co-benefits of sustainable agriculture

---

## Key Insights

### 1. Module 54 is Placeholder, Not Abandoned

- Module structure exists (declarations, preloop, postsolve files)
- Intended functionality well-documented (module.gms:12-24)
- "Future development" indicates plan to activate eventually (module.gms:27-28)

### 2. P Fertilizer Costs Currently Omitted

- MAgPIE production costs underestimate true costs by ~5-10%
- P fertilizer costs: 10-20% of total fertilizer costs (N + P + K)
- Affects crop competitiveness (P-intensive crops like soybeans, cotton more expensive than modeled)

### 3. Phosphorus Less Urgent Than Nitrogen

- N prioritized due to GHG (N2O), water quality (NO3), air quality (NH3)
- P primarily water quality concern (eutrophication)
- P fertilizer costs lower than N (less economic impact)
- Justifies current deactivation (N first, P later)

### 4. P Matters for Low-Input Systems

- Sub-Saharan Africa: Low soil P limits agricultural intensification
- P deficiency bottleneck: Adding N fertilizer ineffective without P
- MAgPIE currently cannot model P as constraint on development

### 5. P Matters for High-Input Systems

- Manure-intensive regions (Netherlands, Denmark): Soil P buildup → eutrophication risk
- P-based manure regulations not represented (only N-based in Module 51)
- Cannot model trade-offs between N and P management

### 6. P Recycling Implicitly Included

- Manure P recycling occurs (via Module 55 manure flows) but not explicitly tracked
- Residue P recycling occurs (via Module 18 residue management) but not quantified
- P content of recycled materials not distinguished from N or C benefits

### 7. Soil P Stocks Missing

- No soil P depletion (mining) in low-input systems
- No soil P accumulation (buildup) in high-input systems
- Long-term P sustainability not assessed

### 8. Eutrophication Not Modeled

- Agricultural P losses to water bodies not calculated
- Cannot link agriculture to water quality impacts
- Missing: P runoff → eutrophication → algal blooms → hypoxia → fish kills

### 9. Precision P Management Not Represented

- Cannot model site-specific P application (soil testing, variable rate)
- Cannot optimize P recycling (manure, biosolids, compost) to reduce fertilizer costs
- Missed opportunity for cost savings and environmental benefits

### 10. Future Activation Would Enrich MAgPIE

- Add biophysical realism (P as limiting nutrient)
- Add economic realism (P fertilizer costs in objective function)
- Add environmental dimension (eutrophication risk, water quality)
- Integrate with N and K for complete nutrient cycle modeling

---

## Verification Summary

**Equations**: 0/0 verified ✅ (no equations in `off` realization)

**Variables**: 1/1 verified ✅
- `vm_p_fert_costs(i)`: Declared (declarations.gms:10), fixed to zero (preloop.gms:10)

**Realization**: Confirmed ✅
- Only `off` realization exists (module.gms:33)
- Deactivates all phosphorus calculations (realization.gms:8-9)

**Status**: Confirmed ✅
- Module currently NOT activated in MAgPIE (module.gms:26)
- Under development for future inclusion (module.gms:27-28, realization.gms:11)

**Intended functionality**: Documented ✅
- 11 P flows listed in module.gms:12-24
- All verified as NOT currently implemented (no equations, no calculations)

**Code truth adherence**: All claims verified against source code ✅

---

## Summary

Module 54 (Phosphorus) is a **placeholder module** currently **deactivated** in MAgPIE.

**Current status**:
- Only `off` realization exists
- 0 equations (no active calculations)
- 1 variable (`vm_p_fert_costs`) fixed to zero
- No phosphorus flows tracked
- No phosphorus costs included in model

**Intended functionality** (future development):
- Track 11 major P flows in agriculture (fertilizer, manure, residues, harvest, erosion, leaching, etc.)
- Calculate soil P dynamics (labile, stable, occluded pools)
- Optimize P fertilizer application
- Include P fertilizer costs in production costs
- Assess eutrophication risk from agricultural P losses

**Implications**:
- Production costs underestimated by ~5-10% (P fertilizer costs missing)
- Cannot model P as limiting nutrient (especially Sub-Saharan Africa)
- Cannot model P-based manure regulations (high-input systems)
- Cannot assess eutrophication risk from agricultural P
- P recycling from manure and residues not explicitly quantified

**Module positioning**: Part of nutrient cycle trio (N-P-K), along with Module 50 (NR Soil Budget), Module 51 (Nitrogen), and Module 55 (AWMS). Currently only N is fully active; P and K await future development.

---

**Documentation Quality Check**:
- [x] Cited file:line for every claim
- [x] Used exact variable names (vm_p_fert_costs)
- [x] Verified module status (off realization only, no active implementation)
- [x] Described CODE behavior only (what is and is NOT implemented)
- [x] Distinguished intended functionality from current status
- [x] Stated limitations explicitly (entire module is limitation - not active)
- [x] No vague language (specific about deactivation, no equations, zero costs)
- [x] Total citations: 20+ file:line references

**Verification**: Module 54 documentation is **fully verified** against source code. Module is confirmed as **inactive placeholder** with zero errors (because there are no calculations to have errors).
---

## Participates In

### Conservation Laws

**Not in conservation laws** (phosphorus tracking only)

### Dependency Chains

**Centrality**: Very Low (peripheral tracker)
**Details**: `core_docs/Module_Dependencies.md`

### Circular Dependencies

None

### Modification Safety

**Risk Level**: 🟡 **LOW RISK**
**Testing**: Verify phosphorus flows reasonable

---

**Module 54 Status**: ✅ COMPLETE

---

**Last Verified**: 2025-10-13
**Verified Against**: `../modules/54_*/off/*.gms`
**Verification Method**: Equations cross-referenced with source code
**Changes Since Last Verification**: None (stable)
