# Missing Content: Land Transition Variable Documentation

**Type**: missing
**Module**: 10 (Land)
**Submitted**: 2025-10-26 (TEST EXAMPLE - Type-Based Routing)
**Target**: modules/module_10.md (core documentation)
**Severity**: Medium

---

## Missing Information

The `modules/module_10.md` documentation does not mention `vm_lu_transitions`, an important interface variable used by Module 59 (SOM) for tracking land-use change impacts on soil organic matter.

**Current state**: No documentation of `vm_lu_transitions` in Interface Variables section

**Expected**: This variable should be documented as it's a key output consumed by other modules

---

## What's Missing

**Variable**: `vm_lu_transitions(j,land_from,land_to)`

**Purpose**: Tracks land-use transitions between land types per timestep

**Used by**:
- Module 59 (SOM): Calculates soil carbon changes from land-use transitions
- Module 52 (Carbon): Tracks carbon stock changes from land conversions
- Module 39 (Land Conversion Costs): Calculates conversion costs

**Defined in**: `modules/10_land/landmatrix_dec18/declarations.gms:67`

**Calculated in**: `modules/10_land/landmatrix_dec18/equations.gms:123-128`

---

## Content to Add

**In `modules/module_10.md`, Interface Variables section**:

Add new subsection:

```markdown
### vm_lu_transitions

**Definition**: Land-use transition matrix tracking changes between land types

**Equation**: q10_lu_transitions (equations.gms:123-128)
```gams
vm_lu_transitions(j,land_from,land_to) =e=
  vm_land(j-1,land_from) - vm_land(j,land_from)$land_to
```

**Used by**:
- Module 59 (SOM): Calculates SOM decay/accumulation from land-use change
- Module 52 (Carbon): Tracks carbon emissions from land conversions
- Module 39 (Land Conversion Costs): Calculates establishment and conversion costs

**Units**: Million ha per timestep

**Dimensions**:
- j: Spatial units (cells)
- land_from: Source land type (crop, forest, pasture, etc.)
- land_to: Destination land type

**Note**: Diagonal elements (land_from = land_to) represent no change; off-diagonal elements represent conversions.
```

---

## Routing Test

**This feedback has `Type: missing`**, which means:
- ✅ Should route to `modules/module_10.md` (core documentation)
- ❌ Should NOT go to `modules/module_10_notes.md` (notes file)
- ✅ Should update "Last Verified" timestamp
- ✅ Content should be integrated seamlessly into existing structure

**Why this matters**: Missing technical content belongs in authoritative documentation, not in notes!

---

## Verification

- Verified in: `modules/10_land/landmatrix_dec18/declarations.gms:67`
- Equation at: `modules/10_land/landmatrix_dec18/equations.gms:123-128`
- Usage verified in: `modules/59_som/static_jan19/preloop.gms:45`
- Cross-reference: `Phase2_Module_Dependencies.md` (Module 10 → Module 59 dependency)

---

**This is a TEST EXAMPLE demonstrating type-based routing for missing content.**
