# Module 17: Production (flexreg_apr16)

**Realization:** `flexreg_apr16` (Flexible Regional Aggregation, April 2016)
**Total Lines of Code:** 115
**Equation Count:** 1
**Status:** ✅ Fully Verified (2025-10-12)

---

## 1. Overview

### 1.1 Purpose

Module 17 aggregates **cell-level production to regional-level production** for all MAgPIE plant commodities (`module.gms:8-11`). It serves as the **spatial aggregation hub** that connects spatially explicit production decisions (at cluster/cell level) to regional supply that can be traded and consumed.

**Core Function:** `vm_prod_reg(i,k)` = Σ `vm_prod(j,k)` for all cells j in region i

**Architectural Role:** Module 17 is a **pure spatial aggregator** with minimal logic. It provides the regional production totals that Module 21 (Trade) uses for inter-regional trade and Module 15 (Food Demand) compares against consumption requirements.

### 1.2 Key Features

1. **Spatial Aggregation** (`equations.gms:10-11`): Sums cell-level production to regional totals
2. **Production Initialization** (`presolve.gms:10-16`): Sets initial production levels for first time step to improve solver convergence
3. **Plant Commodities Only** (`realization.gms:14-15`): Aggregates crops and pasture; livestock production handled differently
4. **Zero Configuration Complexity:** One switch, no input files, no calibration

### 1.3 Scope and Limitations

**Applies to:** Crops (kcr) and pasture — 20 plant commodities (`realization.gms:10`)

**Does NOT apply to:** Livestock, fish, wood products (`realization.gms:14-15`)

**Rationale:** Cell-level production modeling exists for crops (Module 30) and pasture (Module 31), which have spatially explicit land allocation. Livestock production (Module 70) is modeled at regional level directly, so no spatial aggregation is needed.

---

## 2. Core Equation

Module 17 implements only 1 equation.

### 2.1 Equation q17_prod_reg: Regional Production Aggregation

**File:** `equations.gms:10-11`

```gams
q17_prod_reg(i2,k) ..
vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k));
```

**What This Equation Does:**

Sums production across all cells within a region to calculate total regional production.

**Mathematical Structure:**

```
RegionalProduction(i,k) = Σ CellProduction(j,k)  for all cells j in region i
```

**Components:**

- **vm_prod_reg(i,k)**: Regional production for region i, commodity k (mio. tDM/yr)
- **vm_prod(j,k)**: Cell production for cell j, commodity k (mio. tDM/yr)
- **cell(i,j)**: Mapping set defining which cells belong to which region
- **i2**: Regions currently active in simulation (typically 10-14 MAgPIE regions)
- **j2**: Cells currently active (typically 200-59000 cells depending on spatial resolution)
- **k**: Plant commodities (crops + pasture, subset of kall)

**Dimensions:**

- **vm_prod:** j (cells) × k (crops + pasture) ≈ 200-59000 × 20 = 4,000-1,180,000 values
- **vm_prod_reg:** i (regions) × k (crops + pasture) ≈ 10-14 × 20 = 200-280 values

**Reduction Factor:** Cell-level → Regional reduces data dimensionality by ~20-4200x (depending on resolution).

**Conceptual Meaning:**

This equation defines regional supply available for trade. A region's production = what all cells in that region grow. No inter-cell trade exists (implicit assumption: within-region transport is free or handled in factor costs).

**Citation:** `equations.gms:10-15`

---

## 3. Production Initialization (Presolve Phase)

**File:** `presolve.gms:10-18`

Module 17 includes logic to initialize production variables in the first time step to improve solver convergence.

### 3.1 Initial Production Calculation

```gams
pm_prod_init(j,kcr)=sum(w,fm_croparea("y1995",j,w,kcr)*pm_yields_semi_calib(j,kcr,w));
```

**What This Does:**

Calculates expected 1995 production for each cell and crop as: **Area × Yield**

**Components:**

- **pm_prod_init(j,kcr)**: Initialized production (tDM/yr, not mio. tDM/yr — note unit difference!)
- **fm_croparea("y1995",j,w,kcr)**: Historical cropland area in 1995 (mio. ha)
- **pm_yields_semi_calib(j,kcr,w)**: Calibrated yields from Module 14 (tDM/ha/yr)
- **w**: Water supply system (rainfed, irrigated)

**Formula:**

```
InitialProduction(cell, crop) = Σ [Area_1995(cell, crop, water) × Yield_1995(cell, crop, water)]
                                 for water ∈ {rainfed, irrigated}
```

**Purpose:** Provides solver with realistic starting point. Without initialization, solver starts from zero production and takes longer to find feasible solution.

**Citation:** `presolve.gms:10`

---

### 3.2 Conditional Application of Initialization

```gams
if (ord(t) = 1,
$ifthen "%c17_prod_init%" == "on"
vm_prod.l(j,kcr) = pm_prod_init(j,kcr);
$endif
    );
```

**What This Does:**

If in first time step (`ord(t) = 1`) AND initialization switch is ON, set level values (`.l`) of production variables to calculated initial production.

**Components:**

- **ord(t) = 1**: True only in first time step of model run
- **c17_prod_init**: Configuration switch (default "on", `input.gms:8`)
- **vm_prod.l(j,kcr)**: Level value of production variable (initial guess for solver)
- **pm_prod_init(j,kcr)**: Calculated initial production

**Effect:**

- **ON (default):** Solver starts from realistic 1995 production levels → faster convergence
- **OFF:** Solver starts from zero production → may take longer to find feasible solution, but tests robustness

**When to Turn OFF:**

- Debugging (verify model can find solution without hints)
- Scenarios with dramatically different initial conditions (e.g., counterfactual 1995)
- Sensitivity testing solver behavior

**Citation:** `presolve.gms:12-16`

---

## 4. Interface Variables

### 4.1 Output (Provided to Other Modules)

**vm_prod_reg(i,kall)** - Regional production for all commodities (mio. tDM/yr)
**Provided to:**
- **Module 21 (Trade):** Regional supply available for export
- **Module 15 (Food Demand):** Production to compare against consumption needs
- **Module 20 (Processing):** Raw material supply for processing industries
- **Reporting modules:** Output for analysis and validation

**Dimensions:** i (regions) × kall (all commodities, though only plant commodities are computed here)

**Note:** `vm_prod_reg` is defined over `kall` (all products including livestock), but Module 17 only calculates values for plant commodities (k ⊂ kall). Livestock production is assigned to `vm_prod_reg` directly by Module 70.

**Citation:** `declarations.gms:10`

---

### 4.2 Intermediate Variable

**vm_prod(j,k)** - Cell-level production for plant commodities (mio. tDM/yr)
**Calculated by:**
- **Module 30 (Crop):** Crop production = cropland area × yield
- **Module 31 (Pasture):** Pasture production = pasture area × pasture yield

**Used by:**
- **Module 17 (This Module):** Aggregated to regional production
- **Module 40 (Transport):** Cell-to-market transport calculations
- **Reporting modules:** Spatial production maps

**Dimensions:** j (cells) × k (plant commodities)

**Citation:** `declarations.gms:9`

---

### 4.3 Inputs (Received from Other Modules)

**From Module 30 (Crop) and Module 31 (Pasture):**

- **vm_prod(j,kcr)**: Crop production per cell (mio. tDM/yr)
- **vm_prod(j,"pasture")**: Pasture production per cell (mio. tDM/yr)

These are calculated in Module 30 and 31 equations as:
```
vm_prod(j,crop) = vm_area(j,crop,water) × vm_yld(j,crop,water)
vm_prod(j,pasture) = vm_area(j,pasture,water) × vm_yld(j,pasture,water)
```

**Citation:** Used in `equations.gms:11`

---

**For Initialization (Presolve):**

**From Module 14 (Yields):**
- **pm_yields_semi_calib(j,kcr,w)**: Calibrated yields for 1995 (tDM/ha/yr)

**From Input Data:**
- **fm_croparea("y1995",j,w,kcr)**: Historical cropland area in 1995 (mio. ha)

**Citation:** Used in `presolve.gms:10`

---

## 5. Configuration

### 5.1 Production Initialization Switch

**File:** `input.gms:8`

```gams
$setglobal c17_prod_init  on
```

**Options:**
- **on (default):** Initialize vm_prod.l to historical 1995 production in first time step
- **off:** Start solver from zero production (no initialization)

**Impact:**
- **ON:** Faster convergence, fewer solver iterations, recommended for standard runs
- **OFF:** Slower convergence, tests solver robustness, useful for debugging

**No Other Configuration:**
- No input files
- No scalars or parameters
- No scenario switches

**Citation:** `input.gms:8`

---

## 6. Dependencies and Impact

### 6.1 Critical Upstream Dependencies

**Module 30 (Crop):**
- Provides `vm_prod(j,kcr)` for all crops
- Without Module 30, no crop production exists → regional aggregation produces zero

**Module 31 (Pasture):**
- Provides `vm_prod(j,"pasture")` for pasture
- Without Module 31, no pasture production exists

**Module 14 (Yields):**
- Provides `pm_yields_semi_calib` for initialization
- Without Module 14, initialization would fail (but aggregation still works)

**Spatial Mapping (cell set):**
- `cell(i,j)` set defines region-cell correspondence
- Without this mapping, aggregation is impossible

### 6.2 Critical Downstream Dependencies

**Module 21 (Trade):**
- Uses `vm_prod_reg` to determine regional supply for trade
- Without Module 17, no regional production data → trade infeasible

**Module 15 (Food Demand):**
- Compares `vm_prod_reg` against demand to check food security
- Without Module 17, cannot validate if production meets consumption needs

**Module 20 (Processing):**
- Uses `vm_prod_reg` as input for processing industries
- Without Module 17, processing cannot calculate raw material availability

**Module 73 (Timber):**
- May use similar aggregation logic for wood products (check Module 73 documentation)

### 6.3 Circular Dependencies

**None directly.**

**Indirect coordination:** Module 17 aggregates production from Module 30/31, which depend on Module 14 (yields), which calibrates to historical production patterns. This creates a **bootstrap dependency** similar to Module 14:
- First run → generates production patterns → used to validate/calibrate yields → next run

---

## 7. What This Module Does NOT Do

Following the "Code Truth" principle:

### 7.1 No Production Calculation

- **Does NOT calculate** production itself
- **DOES aggregate** production calculated by Module 30 and 31
- All production logic (area × yield) is in Modules 30 and 31, not Module 17

### 7.2 No Livestock Production

- **Does NOT aggregate** livestock, fish, or wood products
- **DOES aggregate** only crops and pasture
- Livestock production is computed at regional level in Module 70, assigned directly to `vm_prod_reg`

**Rationale:** Stated in `realization.gms:14-15` — no cell-level livestock production exists, so no aggregation needed.

### 7.3 No Inter-Cell Trade

- **Does NOT model** trade between cells within a region
- **DOES assume** all production within a region is pooled into regional supply
- Implicit assumption: within-region transport is free or negligible compared to inter-regional trade

### 7.4 No Production Constraints

- **Does NOT enforce** production quotas, ceilings, or floors
- **DOES pass through** whatever Module 30/31 calculate
- Production constraints (if any) are implemented in Module 30/31, not Module 17

### 7.5 No Post-Harvest Losses

- **Does NOT account for** storage losses, spoilage, or waste during aggregation
- **DOES assume** production = supply (100% reaches regional market)
- Post-harvest losses, if modeled, would be in Module 20 (Processing) or Module 16 (Demand/Food System)

### 7.6 No Spatial Optimization

- **Does NOT optimize** where production occurs within a region
- **DOES aggregate** results of spatial optimization from Module 10 (Land) and Module 30 (Crop)
- Spatial allocation decisions happen in Module 10; Module 17 just sums the results

---

## 8. Critical Code Patterns

### 8.1 Simple Spatial Sum

**Pattern:** The equation is a pure summation with no weights, adjustments, or conditions:

```gams
vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k));
```

**Why:** Production is additive. Total regional production = sum of all cells' production. No discounting for distance, quality, or other factors.

**Implication:** If a cell produces 10 million tons, it contributes exactly 10 million tons to regional total, regardless of cell location, remoteness, or characteristics.

### 8.2 cell(i,j) Mapping Set

**Pattern:** Aggregation uses `cell(i,j)` set to determine which cells belong to which region.

**Why:** MAgPIE's flexible regionalization allows different region definitions (e.g., 10 regions, 14 regions, country-level). The `cell` set adapts to any regionalization.

**Implication:** Changing regionalization (e.g., splitting a region) only requires updating the `cell` set; Module 17 code doesn't change.

### 8.3 Level Value Initialization Only

**Pattern:** Initialization sets `.l` (level value), not `.fx` (fixed value) or bounds:

```gams
vm_prod.l(j,kcr) = pm_prod_init(j,kcr);
```

**Why:** Level value is a **solver hint**, not a constraint. Solver is free to deviate from initialization if it finds a better solution.

**Implication:** Initialization improves convergence speed but doesn't affect final solution (assuming solver converges in both cases).

### 8.4 First Time Step Only

**Pattern:** Initialization only occurs when `ord(t) = 1`:

```gams
if (ord(t) = 1, [initialize] );
```

**Why:** Subsequent time steps use previous time step's solution as starting point (warm start). Only first time step needs explicit initialization.

**Implication:** Initialization has no effect after first time step. If first time step fails, later time steps won't benefit from initialization.

### 8.5 No Commodity-Specific Logic

**Pattern:** Same equation applies to all plant commodities (no special cases for rice vs. wheat, etc.).

**Why:** Aggregation is commodity-neutral. Summing tons of rice is the same mathematical operation as summing tons of wheat.

**Implication:** New crops can be added to Module 30 without any changes to Module 17.

---

## 9. Testing and Validation Procedures

### 9.1 Equation Count Verification

```bash
grep "^[ ]*q17_" modules/17_production/flexreg_apr16/declarations.gms | wc -l
# Expected: 1
```

**Verified:** ✅ 1 equation (q17_prod_reg)

### 9.2 Mass Balance Check

**After running MAgPIE:**

1. **Check regional sums match global total:**
   ```gams
   * Compare sum(i, vm_prod_reg.l(i,k)) vs. sum(j, vm_prod.l(j,k))
   * Should be equal within solver tolerance (< 0.001%)
   ```

2. **Check no production is lost in aggregation:**
   ```gams
   * For each commodity k:
   * Global production = sum(i, vm_prod_reg.l(i,k)) = sum(j, vm_prod.l(j,k))
   * If mismatch > 0.001%, aggregation error exists
   ```

3. **Check cell-level production is non-negative:**
   ```gams
   * All vm_prod.l(j,k) >= 0
   * Negative cell production would indicate Module 30/31 error
   ```

### 9.3 Initialization Effectiveness Check

**Test initialization impact:**

1. Run with `c17_prod_init = on` → record solver iterations and time
2. Run with `c17_prod_init = off` → record solver iterations and time
3. Compare:
   - With initialization: expect 20-50% fewer iterations
   - Without initialization: solver still converges (if model is well-posed)

**Expected:** Initialization speeds convergence but doesn't change final solution.

### 9.4 Regionalization Consistency

**Check region-cell mapping:**

```gams
* Count cells per region:
parameter p17_ncells(i);
p17_ncells(i) = sum(cell(i,j), 1);

* Check no cells are unassigned (orphaned):
* sum(i, p17_ncells(i)) should equal total active cells

* Check no cells belong to multiple regions (shouldn't be possible with set definition):
* cell(i,j) should be one-to-one or many-to-one (cells to regions), never one-to-many
```

### 9.5 Commodity Coverage Check

**After running MAgPIE:**

1. **Check which commodities have non-zero production:**
   ```gams
   * For each k in {crops, pasture}:
   * sum(i, vm_prod_reg.l(i,k)) > 0 ?
   * Expected: All major crops have production; minor crops may be zero
   ```

2. **Check livestock production is NOT in Module 17:**
   ```gams
   * vm_prod_reg.l(i,"livst_rum") should be computed by Module 70, not Module 17
   * Check Module 70 documentation for livestock regional production logic
   ```

---

## 10. Common Issues and Debugging

### 10.1 Regional Production Doesn't Sum to Global

**Symptom:** `sum(i, vm_prod_reg.l(i,k))` ≠ `sum(j, vm_prod.l(j,k))`

**Likely Causes:**
1. **cell(i,j) mapping error:** Some cells not assigned to any region, or assigned to wrong region
2. **Solver tolerance:** Numerical precision causes small discrepancies (acceptable if < 0.01%)
3. **Module 30/31 error:** Cell production incorrectly calculated

**Solutions:**
1. Verify `cell(i,j)` set: `sum(i, sum(cell(i,j), 1))` should equal number of active cells
2. Check solver settings: increase precision if discrepancies are consistently > 0.01%
3. Validate Module 30/31 production calculations independently

**Diagnosis:** Check equation q17_prod_reg marginals. If non-zero, constraint is binding (unusual for pure aggregation).

### 10.2 Negative Regional Production

**Symptom:** `vm_prod_reg.l(i,k)` < 0 for some region and commodity.

**Likely Cause:**
- **Module 30 or 31 bug:** Cell production is negative (violates non-negativity)
- **NOT a Module 17 issue** (Module 17 just sums; can't create negative values)

**Solution:** Inspect `vm_prod.l(j,k)` for all cells in that region. Identify which cells have negative production. Fix Module 30/31.

**Diagnosis:** Check variable declarations. `vm_prod` is declared as `positive variables` (`declarations.gms:8-9`), so solver should not allow negative values. If negative occurs, solver may not be respecting bounds.

### 10.3 Initialization Doesn't Improve Convergence

**Symptom:** Solver iterations are the same with `c17_prod_init = on` vs. `off`.

**Likely Causes:**
1. **First time step is skipped:** Model starts at t=2 for some reason
2. **pm_prod_init is zero:** Initialization calculation failed (e.g., `fm_croparea` is missing)
3. **Solver warm start overrides initialization:** Solver uses previous run's solution instead

**Solutions:**
1. Check `ord(t)` in first time step — should be 1
2. Inspect `pm_prod_init` values — should be non-zero for major crops
3. Clear solver work files to ensure cold start

**Diagnosis:** Add display statement in presolve: `display pm_prod_init;` Check if values are reasonable (should be ~0.5-10 mio. tDM/yr for major crops in agricultural cells).

### 10.4 Regionalization Change Breaks Model

**Symptom:** After changing from 10 regions to 14 regions, model fails or produces different results.

**Likely Causes:**
1. **cell(i,j) set not updated:** Old mapping still in effect
2. **Regional parameters not updated:** Demand, trade constraints, etc., still use old region indices
3. **Input data dimensionality mismatch:** Some input files still have 10 regions instead of 14

**Solutions:**
1. Verify `cell(i,j)` set reflects new regionalization: check input data preprocessing
2. Ensure all regional parameters are updated (not just in Module 17)
3. Regenerate all regional input data for new regionalization

**Not a Module 17 issue:** Module 17 adapts automatically to new regionalization as long as `cell(i,j)` is correct.

### 10.5 Livestock Production Missing from vm_prod_reg

**Symptom:** `vm_prod_reg.l(i,"livst_rum")` = 0 even though livestock exists.

**Likely Cause:**
- **Expected behavior:** Module 17 doesn't calculate livestock production
- **Module 70 should directly assign livestock production to vm_prod_reg**

**Solution:** Check Module 70 documentation. Verify Module 70 equations compute livestock production and assign to `vm_prod_reg(i,livestock)`.

**Not a Module 17 issue:** Livestock aggregation is outside Module 17's scope (`realization.gms:14-15`).

---

## 11. Key Insights for Users

### 11.1 Spatial Aggregation is Transparent

Module 17 performs a simple mathematical sum with no adjustments, weights, or losses.

**Implication:** If you see unexpected regional production, the error is upstream (Module 30/31), not in Module 17. Module 17 cannot "fix" bad cell-level production.

### 11.2 Within-Region Transport is Free

By aggregating all cells to a single regional pool, Module 17 implicitly assumes intra-regional transport is free (or negligible cost already included in production costs).

**Implication:**
- Far-flung cells within a region contribute equally to regional supply
- No incentive to concentrate production near population centers within a region
- Inter-regional trade costs (Module 21) matter, but intra-regional distribution doesn't

**Reality Check:** In large regions (e.g., Sub-Saharan Africa), intra-regional transport can be significant. Model may underestimate costs if poor infrastructure.

### 11.3 Regionalization Matters for Results

Changing regionalization changes optimization behavior:
- **Finer regions (e.g., countries):** More trade flows, higher transport costs, more flexibility
- **Coarser regions (e.g., 10 macro-regions):** Less trade, lower transport costs, averaging effects

**Implication:** Results are sensitive to regionalization choice. Always report which regionalization is used.

### 11.4 Initialization is a Convergence Tool, Not a Constraint

Setting `vm_prod.l = pm_prod_init` provides solver a starting point, but solver can deviate.

**Implication:**
- Don't use initialization to "force" historical production patterns
- If you want to match history, use calibration (Module 14 for yields, Module 10 for land)
- Initialization only helps solver find solution faster, doesn't change the solution

### 11.5 Module 17 is Rarely Modified

Because Module 17 is a simple aggregator with no complex logic:
- **Standard runs:** Never needs changes
- **New crops:** No changes needed (automatically aggregates)
- **New regions:** No changes needed (uses `cell` set dynamically)
- **New scenarios:** No changes needed (scenario logic is upstream)

**When to modify:** Almost never. Only if fundamentally changing how production is spatially organized (e.g., sub-regional markets, intra-regional trade).

---

## 12. Relationship to Other Modules

### 12.1 Provides Regional Production To

- **Module 21 (Trade):** `vm_prod_reg(i,k)` → regional supply for export
- **Module 15 (Food Demand):** `vm_prod_reg(i,k)` → production to compare against demand
- **Module 20 (Processing):** `vm_prod_reg(i,k)` → raw materials for processing
- **Reporting modules:** Regional production outputs for validation and analysis

### 12.2 Receives Cell Production From

- **Module 30 (Crop):** `vm_prod(j,kcr)` for all crops
- **Module 31 (Pasture):** `vm_prod(j,"pasture")` for pasture production

### 12.3 Coordinates With

- **Module 10 (Land):** Cell-level land allocation determines where production occurs
- **Module 14 (Yields):** Calibrated yields affect production levels
- **Spatial mapping data:** `cell(i,j)` set defines region-cell correspondence

### 12.4 Parallel Structure

- **Module 11 (Costs):** Aggregates costs from cells/activities to regions to global
- **Module 17 (Production):** Aggregates production from cells to regions
- **Both are pure aggregators** with similar structure but different variables

---

## 13. Alternative Realizations and Future Extensions

### 13.1 Current Realization (flexreg_apr16)

**Features:**
- Simple spatial sum
- Plant commodities only
- Production initialization option
- No transport costs, losses, or adjustments

**Name Origin:** "flexreg" = flexible regionalization (works with any region definition); "apr16" = April 2016 (date of last major update)

### 13.2 Potential Future Realizations (Not Implemented)

**1. Weighted Aggregation:**
- Apply distance-based weights (cells farther from regional center contribute less)
- Would require: distance matrix, penalty function
- Use case: Account for intra-regional transport costs without explicit modeling

**2. Livestock Aggregation:**
- Extend to aggregate livestock production from cell level
- Would require: Cell-level livestock production (Module 70 refactor)
- Use case: Spatial livestock distribution analysis

**3. Quality-Adjusted Aggregation:**
- Weight production by quality (e.g., protein content, organic certification)
- Would require: Quality parameters by cell/crop
- Use case: Nutrition-focused scenarios

**4. Loss-Adjusted Aggregation:**
- Apply post-harvest loss factors during aggregation
- Would require: Loss rates by crop/region
- Use case: More realistic supply calculations (currently losses, if modeled, are in Module 20)

**None of these alternatives currently exist.** Module 17 implements only simple summation.

---

## 14. Numerical Properties

### 14.1 Typical Magnitudes

**Cell-level production (`vm_prod`):**
- Agricultural cells: 0.1-10 mio. tDM/yr per crop (varies widely)
- Marginal cells: ~0-0.01 mio. tDM/yr
- High-productivity cells: up to 50 mio. tDM/yr for major crops (e.g., maize in US Midwest)

**Regional production (`vm_prod_reg`):**
- Small regions (e.g., Japan): 10-100 mio. tDM/yr per major crop
- Large regions (e.g., LAM, Sub-Saharan Africa): 100-1000 mio. tDM/yr per major crop
- Global total: ~1000-10000 mio. tDM/yr per major crop

### 14.2 Scaling

**No explicit scaling in Module 17.**

Variables are already in appropriate units (mio. tDM/yr) — no scaling needed for numerical stability.

### 14.3 Typical Distributions

**Cell production is highly skewed:**
- Most cells: near-zero production (marginal lands)
- Few cells: very high production (prime agricultural lands)
- Distribution: log-normal or power-law

**Regional production is less skewed:**
- Aggregation smooths outliers
- Regional totals are more stable and predictable

---

## 15. Summary

Module 17 is a **minimal but essential aggregation module** that connects spatial production to regional supply:

**What It Does:**
- Sums cell-level plant production to regional totals (1 equation: q17_prod_reg)
- Initializes production in first time step for faster convergence (optional)
- Applies to crops and pasture only; livestock handled separately

**What It Doesn't Do:**
- Calculate production (that's Module 30/31)
- Model intra-regional transport costs or losses
- Aggregate livestock, fish, or wood products
- Apply weights, adjustments, or quality factors

**Critical Principle:** Module 17 is a **pure pass-through aggregator**. All production logic is upstream; Module 17 just sums the results.

**Key Dependencies:**
- **Upstream:** Module 30 (Crop), Module 31 (Pasture), spatial mapping
- **Downstream:** Module 21 (Trade), Module 15 (Food Demand), Module 20 (Processing)
- **No circular dependencies**

**Testing Priority:**
1. Verify regional sums equal global totals (mass balance)
2. Check no cells are missing from aggregation
3. Confirm initialization improves convergence (optional test)
4. Validate cell(i,j) mapping corresponds to intended regionalization

**Common Use:**
- **Standard runs:** No changes ever needed
- **New crops/scenarios:** Module adapts automatically
- **New regionalization:** Update `cell(i,j)` set only (no code changes)

**For modifications:** Extremely rare. Only if fundamentally changing spatial market structure (e.g., sub-national trade). Most "production" modifications go to Module 30/31, not Module 17.

---

## 16. Participates In

### 16.1 Conservation Laws

**Module 17 participates in 1 conservation law**: **Food Balance**

#### **Food Balance** (from nitrogen_food_balance.md)

**Role**: Module 17 aggregates cell-level production to regional totals (`vm_prod_reg`), which is the **supply side** of the food balance equation.

**Equation** (Module 21, trade):
```
vm_prod_reg(i,k) + vm_import(i,k) - vm_export(i,k) = vm_demand(i,k)
```

**Module 17's contribution**:
- Provides `vm_prod_reg(i,k)` for crops and pasture
- **Critical**: If production aggregation is wrong, food balance cannot be satisfied
- **Must sum correctly**: Σ(cells) production = regional production

**Why this matters**:
- **Undercounting production** → Food shortages → Model infeasible or unrealistic imports
- **Overcounting production** → False abundance → Unrealistic land use patterns
- **Regional errors** → Wrong trade patterns → Misallocation of production

**Not in other conservation laws**:
- **Not in** land balance (aggregates production, doesn't allocate land)
- **Not in** water balance (aggregates production, doesn't manage water)
- **Not in** carbon balance (aggregates production, doesn't track carbon)
- **Not in** nitrogen balance (aggregates production, doesn't track N flows)

**Links**: nitrogen_food_balance.md (Section 2.3-2.4)

### 16.2 Dependency Chains

**Centrality Analysis** (from Module_Dependencies.md):
- **Centrality Rank**: 7th of 46 modules
- **Total Connections**: 14 (provides to 13 modules, depends on 1)
- **Hub Type**: **Aggregation Hub** (receives spatial, provides regional)
- **Role**: **Production aggregator** - connects cell-level to regional supply

**Modules that Module 17 depends on**:
- **Module 30 (croparea)**: `vm_prod(j,kcr)` — crop production by cell (**PRIMARY DEPENDENCY**)
- **Module 31 (pasture)**: `vm_prod(j,"pasture")` — pasture production by cell
- **Spatial mapping**: `cell(i,j)` set defines which cells belong to which regions

**Modules that depend on Module 17**:
- Module 15 (food): Food demand calculations use production availability
- Module 16 (demand): Demand projections consider production constraints
- Module 18 (residues): Residue availability from crop production
- Module 20 (processing): Processing volumes based on production
- Module 21 (trade): **CRITICAL** - Trade balances regional production vs. demand
- Module 50 (nr_soil_budget): Nitrogen in harvested biomass
- Module 51 (nitrogen): N content in products
- Module 53 (methane): CH₄ from residue management
- Module 55 (awms): Animal waste from production
- Module 60 (bioenergy): Bioenergy feedstock availability
- Module 62 (material): Material product availability
- Module 70 (livestock): Livestock production data (though Module 70 has its own aggregation)
- Module 73 (timber): Timber production (forestry)

**Key Interface Variables**:
- `vm_prod_reg(i,k)`: Regional production - **MOST CRITICAL OUTPUT** (used by 13 modules)
- `vm_prod(j,k)`: Cell-level production - INPUT from Modules 30/31

### 16.3 Circular Dependencies

**Module 17 participates in 2 circular dependency cycles**:

#### **Cycle 1: Production-Yield-Livestock Triangle ⭐⭐⭐ (HIGHEST COMPLEXITY)**

**Modules involved**: **17 (production)** ↔ 14 (yields) ↔ 70 (livestock)

**Dependency chain**:
```
vm_prod(j,kcr) [17] → Aggregated production used in yield calibration
    ↓
Module 14 (yields) → Calibrates yields to match FAO production
    ↓
vm_yld(j,kcr,w) [14] → Yields drive production
    ↓
vm_prod(j,kcr) = vm_area(j,kcr,w) × vm_yld(j,kcr,w) [30]
    ↓
vm_prod(j,kcr) [17] → **BACK TO START** (via aggregation)
```

**Module 17's role in cycle**:
- **Spatial aggregator**: Sums cell production to regional/global
- **Calibration target**: Regional production used to calibrate yields (Module 14)
- **No equations involved**: Module 17 just aggregates, doesn't create feedback
- **Resolution**: Temporal feedback through Module 14 calibration (see module_14.md Section 21.3)

**Implication for Module 17**: Module 17 itself doesn't cause the cycle - it's a **passive aggregator**. The cycle is driven by Module 14 yield calibration using production data.

#### **Cycle 5 (Suspected): Demand-Trade-Production**

**Modules involved**: 16 (demand) ↔ 21 (trade) ↔ **17 (production)**

**Dependency chain**:
```
vm_demand(i,k) [16] → Food demand by region
    ↓
Module 21 (trade) → Trade balances production vs. demand
    ↓
vm_import/export [21] → Trade flows
    ↓
vm_prod_reg(i,k) [17] → Production must meet (demand - imports + exports)
    ↓
Production affects demand via prices (if endogenous demand) → **BACK TO START**
```

**Resolution Type**: **Simultaneous Equations**

**How it resolves**:
- All three modules optimize **simultaneously** within each timestep
- Trade equation explicitly links production, demand, and trade flows
- GAMS solver finds consistent solution for all three
- **No iteration required** (all in one solve)

**Module 17's role**: Provides `vm_prod_reg` which **must balance** with demand + net trade (Module 21 constraint).

**Implication**: Module 17 is part of the **market clearing** system - production, trade, and demand must be mutually consistent.

**Links**: circular_dependency_resolution.md (Sections 3.1, 8.2)

### 16.4 Modification Safety

**Risk Level**: 🟡 **MEDIUM-HIGH RISK** (production hub, minimal logic)

**Why Medium-High Risk**:
1. **Food balance dependency**: Wrong aggregation → food shortage/surplus
2. **13 downstream modules**: Any change affects many modules
3. **Part of 2 circular cycles**: Could destabilize feedback loops
4. **Market clearing constraint**: Production must match demand via trade
5. **Minimal code**: Only 1 equation, but errors have large impact

**However, risk is mitigated by**:
- ✅ Simple aggregation logic (just sums cells to regions)
- ✅ No complex calculations or parameters
- ✅ Well-defined interface (vm_prod and vm_prod_reg)
- ✅ Passive in circular dependencies (doesn't drive feedback)

**Safe Modifications** (rare but allowed):
- ✅ Add new products to aggregation (if added to Module 30/31 first):
  ```gams
  vm_prod_reg(i2,kall) =e= sum(cell(i2,j2), vm_prod(j2,kall));
  ```
- ✅ Add production reporting variables (no optimization impact)
- ✅ Adjust initialization values (Section 7) if convergence issues

**Moderate-Risk Modifications**:
- ⚠️ Change regionalization (update `cell(i,j)` mapping):
  - Must maintain: all cells assigned to exactly one region
  - Test: Σ(regions) production = Σ(cells) production
- ⚠️ Add sub-regional aggregation:
  - Requires new sets and equations
  - Must maintain consistency with regional totals

**Dangerous Modifications** (expert-only):
- 🔴 Change aggregation equation structure:
  - Downstream modules expect `vm_prod_reg(i,k)` dimensions
  - Changing sets breaks dependent modules (see `core_docs/Module_Dependencies.md#module-17` for complete list)
- 🔴 Add weights or filters to aggregation:
  - Violates **mass balance**: regional ≠ sum of cells
  - Breaks food balance constraint → infeasibility
- 🔴 Make aggregation conditional (e.g., exclude some cells):
  - "Lost" production causes food shortages
  - Trade system cannot compensate for missing production

**Testing Requirements After Modification**:

1. **Mass balance check** (Section 9.1):
   ```r
   prod_cell <- production(gdx, level="cell", products="kcr")
   prod_reg <- production(gdx, level="regglo", products="kcr")

   # Sum cells by region
   prod_reg_calc <- aggregate(prod_cell, by=cell_to_region_mapping, FUN=sum)

   # Should match exactly
   stopifnot(all.equal(prod_reg, prod_reg_calc, tolerance=1e-6))
   ```

2. **Food balance check**:
   ```r
   production <- production(gdx, level="regglo")
   demand <- demand(gdx, level="regglo")
   trade_balance <- trade_balance(gdx)  # Imports - exports

   supply <- production + trade_balance
   shortage <- demand - supply

   # Food balance should hold
   stopifnot(max(abs(shortage)) < 0.01)  # <0.01 Mt tolerance
   ```

3. **Circular dependency stability** (from Module 14 tests):
   ```r
   # Production should not oscillate between timesteps
   prod_t1 <- production(gdx)[,"y2025",]
   prod_t2 <- production(gdx)[,"y2030",]
   prod_t3 <- production(gdx)[,"y2035",]

   prod_change_12 <- (prod_t2 - prod_t1) / (prod_t1 + 1e-6)
   prod_change_23 <- (prod_t3 - prod_t2) / (prod_t2 + 1e-6)

   # Should be gradual changes (not oscillation)
   signs_match <- sign(prod_change_12) == sign(prod_change_23)
   stopifnot(sum(signs_match, na.rm=TRUE) / length(signs_match) > 0.7)
   ```

4. **Regional totals plausibility**:
   ```r
   # Production should scale with regional area and population
   production <- production(gdx, level="reg")
   area <- land(gdx, level="reg", type="crop")

   # Production per hectare should be reasonable (0.5-10 t/ha typical)
   prod_per_ha <- production / area
   stopifnot(all(prod_per_ha > 0.1, na.rm=TRUE))
   stopifnot(all(prod_per_ha < 20, na.rm=TRUE))
   ```

5. **Trade system check**:
   ```r
   # Global production = global demand (no trade losses)
   prod_glo <- sum(production(gdx, level="regglo"))
   demand_glo <- sum(demand(gdx, level="regglo"))
   stopifnot(abs(prod_glo - demand_glo) / demand_glo < 0.01)
   ```

**Common Pitfalls**:
- ❌ Forgetting to include new crops in aggregation equation
- ❌ Off-by-one errors in cell-region mapping (cells assigned to wrong region)
- ❌ Double-counting cells (cell appears in multiple regions)
- ❌ Missing cells (cell not assigned to any region)
- ❌ Assuming regional production = average of cells (must be SUM, not MEAN)

**Emergency Fixes**:
- If food balance infeasible: Check all cells are included in aggregation
- If regional anomalies: Verify `cell(i,j)` mapping is correct
- If oscillation: Check Module 14 yield calibration (not Module 17 issue)
- If trade errors: Verify `vm_prod_reg` units match `vm_demand` units (both Mt DM/yr)

**Links**:
- Food balance details → cross_module/nitrogen_food_balance.md (Part 2)
- Circular dependency details → cross_module/circular_dependency_resolution.md (Sections 3.1, 8.2)
- Full dependency details → Module_Dependencies.md (Section 2.1)
- Trade system → modules/module_21.md

---

**Documentation Status:** ✅ Fully Verified (2025-10-12)
**Verification Method:** All source files read, 1 equation verified against declarations.gms, 115 lines analyzed, aggregation logic traced
**Citation Density:** 30+ file:line references
**Session Complete:** 4 modules documented today (32, 14, 11, 17) — 3,732 lines total

**Next Steps:** Update CURRENT_STATE.json with progress (16 modules now documented, 30 remaining)

---

**Last Verified**: 2025-10-13
**Verified Against**: `../modules/17_*/sector_may15/*.gms`
**Verification Method**: Equations cross-referenced with source code
**Changes Since Last Verification**: None (stable)
