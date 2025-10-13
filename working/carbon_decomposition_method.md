# Carbon Stock Decomposition: Land-Use Change vs. Climate Change Effects

## Mathematical Framework

### Basic Relationship
Carbon stock for any land type in a grid cell:
```
C(t) = A(t) × D(t)
```
where:
- C(t) = Total carbon stock at time t (mio. tC)
- A(t) = Land area at time t (mio. ha)
- D(t) = Carbon density at time t (tC/ha)

### Carbon Stock Change
```
ΔC = C(t+Δt) - C(t) = A(t+Δt)×D(t+Δt) - A(t)×D(t)
```

## Decomposition Methods

### Method 1: Additive Laspeyres Decomposition

**Formula:**
```
ΔC = ΔC_area + ΔC_density + ΔC_interaction

where:
ΔC_area = [A(t+Δt) - A(t)] × D(t)              # Land-use change effect
ΔC_density = A(t) × [D(t+Δt) - D(t)]           # Climate change effect
ΔC_interaction = [A(t+Δt) - A(t)] × [D(t+Δt) - D(t)]  # Interaction term
```

**Interpretation:**
- **ΔC_area**: Carbon change if only area changed (density held constant at t)
- **ΔC_density**: Carbon change if only density changed (area held constant at t)
- **ΔC_interaction**: Joint effect of both changing simultaneously

**Advantages:**
- Simple, intuitive
- Uses initial period as reference

**Disadvantages:**
- Leaves residual (interaction term)
- Not symmetric (Paasche decomposition using final period gives different results)

### Method 2: Logarithmic Mean Divisia Index (LMDI) - RECOMMENDED

**Formula:**
```
ΔC_area = L(C(t+Δt), C(t)) × ln[A(t+Δt)/A(t)]
ΔC_density = L(C(t+Δt), C(t)) × ln[D(t+Δt)/D(t)]

where L(a,b) is the logarithmic mean:
L(a,b) = (a - b) / ln(a/b)   if a ≠ b
L(a,b) = a                    if a = b
```

**Interpretation:**
- **ΔC_area**: Carbon change attributable to area change
- **ΔC_density**: Carbon change attributable to density change
- **No residual**: ΔC = ΔC_area + ΔC_density (exact)

**Advantages:**
- No residual term
- Theoretically sound (based on Divisia index)
- Symmetric and time-reversal
- Widely used in energy/carbon decomposition literature

**Disadvantages:**
- Slightly more complex calculation
- Cannot handle zero or negative values directly

### Method 3: Midpoint Method

**Formula:**
```
ΔC_area = [(D(t) + D(t+Δt))/2] × [A(t+Δt) - A(t)]
ΔC_density = [(A(t) + A(t+Δt))/2] × [D(t+Δt) - D(t)]
```

**Interpretation:**
- Uses average density/area as reference point
- Symmetric approximation

**Advantages:**
- Simple calculation
- No residual
- Symmetric

**Disadvantages:**
- Less theoretically justified than LMDI

## Implementation in MAgPIE

### Data Sources (from single "cc" scenario)

**Carbon Densities** (Module 52):
- `fm_carbon_density(t,j,land,c_pools)` - Time-varying from LPJmL
  - Source: `modules/52_carbon/input/lpj_carbon_stocks.cs3`
  - Includes climate change effects
  - Units: tC/ha
  - Pools: vegc, litc, soilc

**Land Areas** (Module 10):
- `vm_land(j,land)` - Optimized land allocation
  - Changes due to economic optimization
  - Units: mio. ha
  - Land types: crop, past, primforest, secdforest, urban, other

**Carbon Stocks** (Module 52/59):
- `vm_carbon_stock(j,land,c_pools,stockType)` - Total stocks
  - Computed as: Stock = Area × Density (with age-class adjustments)
  - Units: mio. tC

### MAgPIE-Specific Considerations

**1. Multiple Carbon Pools**
```
For each pool p ∈ {vegc, litc, soilc}:
  ΔC_total(p) = ΔC_area(p) + ΔC_density(p)

Total decomposition:
  ΔC_area_total = Σ_p ΔC_area(p)
  ΔC_density_total = Σ_p ΔC_density(p)
```

**2. Multiple Land Types**
```
For each land type l:
  ΔC_area(l) = decompose area effect for land l
  ΔC_density(l) = decompose density effect for land l

Regional totals:
  ΔC_area_region = Σ_j Σ_l ΔC_area(j,l)
  ΔC_density_region = Σ_j Σ_l ΔC_density(j,l)
```

**3. Age-Class Dynamics (plantations, secondary forests)**

For land types with age-class structure, density changes include:
- Climate effects on mature forest carbon (A parameter in Chapman-Richards)
- Age-class distribution changes (management effect)

To isolate pure climate effect:
```
D_climate(t) = fm_carbon_density(t,j,land,pool)  # From LPJmL
D_ageclass(t) = actual age-class-weighted density  # From Module 52/35

Total density effect: ΔD_total = D(t+Δt) - D(t)
Climate effect: ΔD_climate = D_climate(t+Δt) - D_climate(t)
Management effect: ΔD_management = ΔD_total - ΔD_climate
```

**4. Soil Organic Matter (Module 59)**

SOM has additional dynamics:
```
Topsoil equilibrium: Target = Area × CRatio × NaturalDensity
Actual pool: Pool(t) = λ×Target + (1-λ)×Pool(t-1)
```

Decomposition should use:
- Area effect: Changes in cropland/pasture/forest area
- Density effect: Changes in NaturalDensity from LPJmL (climate)
- Management effect: Changes in CRatio (IPCC factors, irrigation, SCM)

**5. Land-Use Transitions**

MAgPIE uses `vm_lu_transitions(j,land_from,land_to)` which complicates decomposition:
- When forest→crop, both area AND density change simultaneously
- Carbon from transitioning land carries legacy density from source land type

Recommendation:
- Treat transitions as area changes
- Density changes are from time-varying fm_carbon_density

## R Post-Processing Implementation

### LMDI Method (Recommended)

```r
library(magclass)
library(magpie4)

# Function to calculate logarithmic mean
log_mean <- function(a, b) {
  ifelse(abs(a - b) < 1e-10,
         a,  # if equal, return a
         (a - b) / log(a / b))
}

# Main decomposition function
decompose_carbon_lmdi <- function(gdx, level = "cell") {

  # Read data
  area <- land(gdx, level = level)  # mio. ha
  density <- carbonDensity(gdx, level = level)  # tC/ha
  carbon <- carbonstock(gdx, level = level)  # mio. tC

  years <- getYears(carbon)

  # Initialize results
  decomp <- list()

  for (i in 2:length(years)) {
    t0 <- years[i-1]
    t1 <- years[i]

    # Current and previous timestep
    C0 <- carbon[,t0,]
    C1 <- carbon[,t1,]
    A0 <- area[,t0,]
    A1 <- area[,t1,]
    D0 <- density[,t0,]
    D1 <- density[,t1,]

    # Total change
    dC <- C1 - C0

    # LMDI weights
    L_C <- log_mean(C1, C0)

    # Decomposition
    dC_area <- L_C * log(A1 / A0)
    dC_density <- L_C * log(D1 / D0)

    # Handle edge cases (zero values)
    dC_area[!is.finite(dC_area)] <- 0
    dC_density[!is.finite(dC_density)] <- 0

    # Store results
    decomp[[paste0(t0, "_", t1)]] <- list(
      total = dC,
      area_effect = dC_area,
      density_effect = dC_density,
      verification = abs(dC - (dC_area + dC_density))  # Should be ~0
    )
  }

  return(decomp)
}

# Usage
gdx <- "output/default/fulldata.gdx"
decomp_cell <- decompose_carbon_lmdi(gdx, level = "cell")
decomp_reg <- decompose_carbon_lmdi(gdx, level = "reg")

# Aggregate to regional totals
landuse_effect_regional <- dimSums(decomp_reg[[1]]$area_effect, dim = c(1,3))
climate_effect_regional <- dimSums(decomp_reg[[1]]$density_effect, dim = c(1,3))

print(paste("Land-use change effect:", landuse_effect_regional, "mio. tC"))
print(paste("Climate change effect:", climate_effect_regional, "mio. tC"))
```

### Laspeyres Method (Alternative)

```r
decompose_carbon_laspeyres <- function(gdx, level = "cell") {

  # Read data
  area <- land(gdx, level = level)
  density <- carbonDensity(gdx, level = level)
  carbon <- carbonstock(gdx, level = level)

  years <- getYears(carbon)

  decomp <- list()

  for (i in 2:length(years)) {
    t0 <- years[i-1]
    t1 <- years[i]

    C0 <- carbon[,t0,]
    A0 <- area[,t0,]
    A1 <- area[,t1,]
    D0 <- density[,t0,]
    D1 <- density[,t1,]

    # Laspeyres decomposition (using initial period as base)
    dA <- A1 - A0
    dD <- D1 - D0

    dC_area <- dA * D0
    dC_density <- A0 * dD
    dC_interaction <- dA * dD
    dC_total <- C1 - C0

    decomp[[paste0(t0, "_", t1)]] <- list(
      total = dC_total,
      area_effect = dC_area,
      density_effect = dC_density,
      interaction = dC_interaction,
      verification = dC_total - (dC_area + dC_density + dC_interaction)  # Should be ~0
    )
  }

  return(decomp)
}
```

## Interpretation Guidelines

### Land-Use Change Effect (ΔC_area)
- **Direct anthropogenic control**: Driven by food demand, trade, policies
- **Includes**: Deforestation, afforestation, cropland expansion, abandonment
- **Sign interpretation**:
  - Negative: Net carbon loss from land conversion (e.g., forest→crop)
  - Positive: Net carbon gain from land conversion (e.g., crop→forest)

### Climate Change Effect (ΔC_density)
- **Indirect effect**: Driven by exogenous climate scenario (RCP/SSP)
- **Includes**:
  - CO₂ fertilization (increased productivity)
  - Temperature effects on growth and decomposition
  - Precipitation changes
  - Climate-driven vegetation shifts
- **Sign interpretation**:
  - Positive: Climate increases carbon density (e.g., CO₂ fertilization)
  - Negative: Climate decreases carbon density (e.g., drought, heat stress)

### Interaction Term (Laspeyres only)
- **Joint effect**: Both area and density changing
- **Can be positive or negative**
- **Usually small relative to main effects**
- **Example**: Expanding cropland into regions where climate is also increasing forest productivity

## Caveats and Limitations

### 1. Exogenous Climate Effects
- MAgPIE uses **pre-computed LPJmL carbon densities**
- Climate effect is from **LPJmL's climate scenario**, not MAgPIE's own emissions
- **No feedback**: MAgPIE emissions don't affect its own carbon densities

### 2. Density Changes Include Non-Climate Factors
In MAgPIE, `fm_carbon_density` includes:
- ✓ Climate change effects (temperature, precipitation, CO₂)
- ✓ LPJmL's vegetation dynamics
- ✗ NOT MAgPIE management intensity (uniform assumptions)
- ✗ NOT MAgPIE-specific degradation (except Module 59 SOM)

### 3. Age-Class Complications
For plantations and secondary forests:
- Density changes include **age-class distribution changes**
- Pure climate effect requires additional decomposition (see above)

### 4. Soil Organic Matter
Module 59 SOM has:
- Climate effect: via `f59_topsoilc_density` from LPJmL
- Management effect: via IPCC stock change factors
- Temporal dynamics: 15% annual convergence to new equilibrium

Requires separate decomposition to fully isolate climate vs. management.

### 5. Conservation Law Verification

Always verify:
```
ΔC_total = ΔC_area + ΔC_density (+ ΔC_interaction for Laspeyres)
```

If this doesn't hold (>1% error), check for:
- Age-class dynamics not captured
- SOM convergence dynamics
- Data extraction errors
- Zero/negative values in LMDI

## Validation Example

Compare single-scenario decomposition with two-scenario approach:

```r
# Scenario decomposition (from two runs)
carbon_cc <- carbonstock(gdx_cc)
carbon_nocc <- carbonstock(gdx_nocc)
climate_effect_scenario <- carbon_cc - carbon_nocc

# LMDI decomposition (from single run)
decomp <- decompose_carbon_lmdi(gdx_cc)
climate_effect_lmdi <- decomp$density_effect

# These should be similar but NOT identical because:
# 1. nocc scenario has different land allocation (economic response)
# 2. Single-scenario LMDI is marginal decomposition
# 3. Two-scenario is total effect decomposition
```

## Literature Basis

**Index Decomposition Analysis:**
- Ang, B.W. (2004). "Decomposition analysis for policymaking in energy." Energy Policy.
- Ang, B.W. (2015). "LMDI decomposition approach: A guide for implementation." Energy Policy.

**Carbon Flux Attribution:**
- Houghton, R.A. & Nassikas, A.A. (2017). "Global and regional fluxes of carbon from land use and land-use change." Global Biogeochemical Cycles.
- Grassi et al. (2021). "Critical adjustment of land mitigation pathways." Nature Climate Change.

**Forest Carbon Decomposition:**
- Kauppi et al. (2006). "Returning forests analyzed with the forest identity." PNAS.
- Various studies on separating area vs. density effects in forest carbon accounting.

---

**Generated:** 2025-10-13
**For:** MAgPIE AI Documentation Project
**Purpose:** Enable single-scenario carbon stock decomposition
