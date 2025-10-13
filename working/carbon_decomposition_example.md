# Carbon Decomposition: Worked Example

## Quick Reference

### LMDI Formula (Recommended)

```
ΔC = ΔC_area + ΔC_density

where:
ΔC_area = L(C₁, C₀) × ln(A₁/A₀)     # Land-use change effect
ΔC_density = L(C₁, C₀) × ln(D₁/D₀)  # Climate change effect

L(a,b) = (a-b)/ln(a/b)                # Logarithmic mean
```

## Worked Example: Tropical Forest Cell

### Initial State (Year 2020)

**Cell j in Amazon region:**
- Forest area: A₀ = 1.0 mio. ha
- Carbon density: D₀ = 150 tC/ha (from LPJmL)
- Total carbon stock: C₀ = A₀ × D₀ = 150 mio. tC

### Final State (Year 2025)

**After 5 years:**
- Forest area: A₁ = 0.8 mio. ha (deforestation)
- Carbon density: D₁ = 155 tC/ha (CO₂ fertilization)
- Total carbon stock: C₁ = A₁ × D₁ = 124 mio. tC

### Decomposition

**1. Total change:**
```
ΔC = C₁ - C₀ = 124 - 150 = -26 mio. tC
```

**2. Calculate logarithmic mean:**
```
L(C₁, C₀) = (C₁ - C₀) / ln(C₁/C₀)
          = (124 - 150) / ln(124/150)
          = -26 / ln(0.8267)
          = -26 / (-0.1897)
          = 137.06 mio. tC
```

**3. Area effect (land-use change):**
```
ΔC_area = L(C₁, C₀) × ln(A₁/A₀)
        = 137.06 × ln(0.8/1.0)
        = 137.06 × ln(0.8)
        = 137.06 × (-0.2231)
        = -30.58 mio. tC
```

Interpretation: **Deforestation caused -30.58 mio. tC loss**

**4. Density effect (climate change):**
```
ΔC_density = L(C₁, C₀) × ln(D₁/D₀)
           = 137.06 × ln(155/150)
           = 137.06 × ln(1.0333)
           = 137.06 × 0.0328
           = +4.50 mio. tC
```

Interpretation: **CO₂ fertilization caused +4.50 mio. tC gain**

**5. Verification:**
```
ΔC = ΔC_area + ΔC_density
   = -30.58 + 4.50
   = -26.08 mio. tC
   ≈ -26.00 mio. tC ✓
```

(Small rounding error is expected)

### Interpretation

**Net carbon loss: -26 mio. tC**
- **117% from land-use change** (deforestation: -30.58 mio. tC)
- **-17% from climate change** (CO₂ fertilization: +4.50 mio. tC)

Climate change partially offset land-use emissions by increasing the carbon density of remaining forests.

---

## Comparison: Laspeyres vs. LMDI

### Laspeyres Method (Using Same Data)

**Area effect:**
```
ΔC_area = ΔA × D₀
        = (0.8 - 1.0) × 150
        = -0.2 × 150
        = -30.0 mio. tC
```

**Density effect:**
```
ΔC_density = A₀ × ΔD
           = 1.0 × (155 - 150)
           = 1.0 × 5
           = +5.0 mio. tC
```

**Interaction term:**
```
ΔC_interaction = ΔA × ΔD
               = (0.8 - 1.0) × (155 - 150)
               = -0.2 × 5
               = -1.0 mio. tC
```

**Total:**
```
ΔC = ΔC_area + ΔC_density + ΔC_interaction
   = -30.0 + 5.0 + (-1.0)
   = -26.0 mio. tC ✓
```

### Comparison Table

| Method | Area Effect | Density Effect | Interaction | Total |
|--------|------------|----------------|-------------|-------|
| **LMDI** | -30.58 | +4.50 | 0 (exact) | -26.08 |
| **Laspeyres** | -30.00 | +5.00 | -1.00 | -26.00 |

**Key differences:**
- LMDI: No residual, theoretically sound
- Laspeyres: Has interaction term (ambiguous attribution)
- Results are similar but LMDI is preferred for formal analysis

---

## MAgPIE-Specific Example: Multiple Carbon Pools

### Scenario: Cropland Expansion into Forest

**Initial (t=0):**
```
Forest: 1.0 mio. ha
  vegc: 100 tC/ha → 100 mio. tC
  litc: 20 tC/ha  → 20 mio. tC
  soilc: 80 tC/ha → 80 mio. tC
  Total: 200 mio. tC
```

**Final (t=1):**
```
Forest: 0.7 mio. ha
  vegc: 105 tC/ha → 73.5 mio. tC  (climate effect: +5%)
  litc: 21 tC/ha  → 14.7 mio. tC  (climate effect: +5%)
  soilc: 82 tC/ha → 57.4 mio. tC  (climate effect: +2.5%)
  Subtotal: 145.6 mio. tC

Cropland: 0.3 mio. ha (new)
  vegc: 5 tC/ha   → 1.5 mio. tC
  litc: 5 tC/ha   → 1.5 mio. tC
  soilc: 60 tC/ha → 18.0 mio. tC
  Subtotal: 21.0 mio. tC

Total: 166.6 mio. tC
```

### Decomposition by Pool

**Total change:** ΔC = 166.6 - 200 = -33.4 mio. tC

**Using LMDI for each pool:**

1. **Vegetation carbon (vegc):**
   - Forest area: 1.0→0.7, density: 100→105
   - Cropland area: 0→0.3, density: 0→5
   - Decompose separately, then sum

2. **Litter carbon (litc):**
   - Similar approach

3. **Soil carbon (soilc):**
   - Note: SOM dynamics from Module 59 add complexity
   - May need additional decomposition (see below)

---

## Special Case: Soil Organic Matter (Module 59)

### Problem
Module 59 has convergence dynamics:
```
SOM(t) = λ×Target(t) + (1-λ)×SOM(t-1)
```

Where:
- Target depends on climate (via f59_topsoilc_density)
- Target depends on management (via IPCC factors)
- λ = convergence rate (0.15 per year)

### Solution: Three-Way Decomposition

**Total SOM density change:**
```
ΔD_total = D(t+1) - D(t)
```

**Decompose into:**
1. **Climate effect:** Change in natural topsoil density
   ```
   ΔD_climate = f59_topsoilc_density(t+1) - f59_topsoilc_density(t)
   ```

2. **Management effect:** Change in IPCC stock change factors
   ```
   ΔD_management = [Target_management(t+1) - Target_management(t)]
   ```

3. **Convergence effect:** Approach to equilibrium
   ```
   ΔD_convergence = λ × [Target(t) - SOM(t-1)]
   ```

**Implementation:**
```r
# Extract from Module 59
natural_density <- readGDX(gdx, "f59_topsoilc_density")
cratio <- readGDX(gdx, "i59_cratio")
som_pool <- readGDX(gdx, "ov59_som_pool", select = list(type = "level"))
som_target <- readGDX(gdx, "ov59_som_target", select = list(type = "level"))

# Decompose density changes
dD_climate <- natural_density[,t1,] - natural_density[,t0,]
dD_management <- (cratio[,t1,] - cratio[,t0,]) * natural_density[,t1,]
dD_convergence <- lossrate * (som_target[,t0,] - som_pool[,t0,])

# Then apply LMDI with each component
```

---

## Practical Tips

### 1. Edge Cases

**Zero initial area:**
```r
# When A₀ = 0 (new land use):
# ln(A₁/A₀) = ln(A₁/0) = undefined

# Solution: Treat as special case
if (A0 == 0 & A1 > 0) {
  dC_area <- C1  # All change is area effect
  dC_density <- 0
}
```

**Zero initial density:**
```r
# When D₀ = 0 (bare land):
# ln(D₁/D₀) = undefined

# Solution: Use small epsilon
D0 <- max(D0, 1e-10)
```

### 2. Aggregation Order

**Option A: Decompose then aggregate**
```r
# Decompose at cell level
dC_area_cell <- LMDI_decomposition(C_cell)
# Then sum over regions
dC_area_regional <- sum(dC_area_cell)
```

**Option B: Aggregate then decompose**
```r
# Sum carbon stocks first
C_regional <- sum(C_cell)
# Then decompose
dC_area_regional <- LMDI_decomposition(C_regional)
```

⚠️ **These give different results!** Option A is more accurate but computationally expensive.

### 3. Interpretation Pitfalls

**Pitfall 1: Climate effect includes CO₂ fertilization**
- ΔC_density includes productivity gains from rising CO₂
- This is NOT the same as "climate damage" (temperature, drought)
- To separate: Need LPJmL runs with/without CO₂ fertilization

**Pitfall 2: Density changes from age-class distributions**
- For plantations/secondary forests, density changes include:
  - True climate effect (mature forest carbon increasing)
  - Management effect (harvest timing, rotation length)
- Requires additional decomposition

**Pitfall 3: Interaction between area and density**
- LMDI assumes separability: C = A × D
- In reality: Area changes may trigger density changes
  - Example: Deforestation → edge effects → density loss in remaining forest
- LMDI doesn't capture these feedbacks

### 4. Validation Checks

**Always verify:**
```r
# 1. Decomposition is exact (no residual)
residual <- dC_total - (dC_area + dC_density)
max(abs(residual)) < 0.01 * max(abs(dC_total))  # <1% error

# 2. Sign makes sense
# If forest area decreases → dC_area should be negative
# If climate increases density → dC_density should be positive

# 3. Magnitude is reasonable
# Area effect should dominate for large land-use changes
# Density effect should be small (few % per year)
```

---

## Expected Results for Different Scenarios

### Scenario 1: Business-as-usual (High Deforestation)
```
Expected decomposition:
  Land-use change: -80% to -95% of total carbon loss
  Climate change: -5% to -20% (partial offset from CO₂ fertilization)
```

### Scenario 2: Afforestation (Carbon Sequestration)
```
Expected decomposition:
  Land-use change: +100% to +120% of total carbon gain
  Climate change: -20% to +20% (can enhance or reduce, depending on climate scenario)
```

### Scenario 3: Stabilized Land Use (Post-transition)
```
Expected decomposition:
  Land-use change: ~0% (minimal area changes)
  Climate change: +100% (all change from density shifts)
```

### Scenario 4: Climate Mitigation (NDCs + Nature-based Solutions)
```
Expected decomposition:
  Land-use change: +60% to +80% (afforestation, restoration)
  Climate change: +20% to +40% (CO₂ fertilization enhancing uptake)
```

---

## References to MAgPIE Code

### Key Variables to Extract

**From Module 52 (Carbon):**
```r
fm_carbon_density <- readGDX(gdx, "fm_carbon_density")
# File: modules/52_carbon/input/lpj_carbon_stocks.cs3
# Dimensions: t × j × land × c_pools
# Units: tC/ha
```

**From Module 10 (Land):**
```r
vm_land <- readGDX(gdx, "ov_land", select = list(type = "level"))
# Dimensions: t × j × land
# Units: mio. ha
```

**From Module 56 (GHG):**
```r
vm_carbon_stock <- readGDX(gdx, "ov_carbon_stock", select = list(type = "level"))
# Dimensions: t × j × land × c_pools × stockType
# Units: mio. tC
```

**From Module 59 (SOM):**
```r
f59_topsoilc_density <- readGDX(gdx, "f59_topsoilc_density")
# File: modules/59_som/input/lpj_carbon_topsoil.cs2b
i59_cratio <- readGDX(gdx, "i59_cratio")
# Calculated in: modules/59_som/cellpool_jan23/preloop.gms:60-67
```

---

## Conclusion

**LMDI decomposition allows you to answer:**

1. **"How much of carbon loss is from deforestation vs. climate change?"**
   → Compare ΔC_area vs. ΔC_density

2. **"Is CO₂ fertilization offsetting land-use emissions?"**
   → Check sign of ΔC_density when ΔC_area is negative

3. **"Which carbon pool dominates the climate response?"**
   → Decompose vegc, litc, soilc separately

4. **"How do effects vary by region?"**
   → Apply decomposition at regional level

5. **"What's the relative contribution over time?"**
   → Track ΔC_area / ΔC_total ratio across timesteps

**Next steps:**
1. Run the R script on your MAgPIE output
2. Check validation (residuals <1%)
3. Interpret results in context of your scenario
4. Consider special cases (SOM, age-classes) if needed

