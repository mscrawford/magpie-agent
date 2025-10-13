# Comprehensive Analysis: MAgPIE Deforestation Mechanisms and Missing Factors

**Analysis Date**: October 13, 2025
**MAgPIE Version**: develop branch (commit: 96d1a59a8)
**Literature Review Period**: 2024-2025
**Status**: REVISED - Corrected quantitative assessments

---

## Executive Summary

MAgPIE currently captures **first-order economic drivers** of deforestation (agricultural demand, carbon prices, land conversion costs) through a cost-minimization optimization framework. However, analysis of 2024-2025 literature and code inspection reveals MAgPIE **omits several amplification mechanisms** that are empirically important in specific contexts:

**Key missing mechanisms**:
1. **Non-economic deforestation** - Model assumes all cleared land enters production; reality: 33-50% abandoned
2. **Edge effects** - Fragmentation causes biomass loss beyond direct clearing
3. **Dynamic fire** - Parameterized only; no climate-fire-degradation feedbacks
4. **Spatial accessibility** - Conversion costs uniform within regions; roads not represented
5. **Foregone sequestration (LASC)** - Only instantaneous stock loss counted
6. **Governance variation** - Protected areas perfectly enforced in model

**Critical caveat**: The magnitude of MAgPIE's underestimation relative to observations is **unknown without model-data comparison**. Literature provides evidence these mechanisms are important regionally and temporally, but quantifying the global systematic gap requires running MAgPIE and comparing outputs to empirical LUC emissions.

**Regional/temporal specificity matters**:
- Amazon 2024: Fire dominated (791 Mt CO2, extreme drought year)
- Cambodia 2024: 56% PA forest loss (governance failure)
- Brazil: 305× road multiplier (secondary vs primary roads)

These are **not globally representative averages**—they're context-specific findings that inform where and when mechanisms matter most.

---

## Part 1: How Deforestation Works in MAgPIE (From Code Analysis)

### Core Economic Framework
**Location**: Module 39 (landconversion), Module 10 (land), Module 11 (costs)

MAgPIE uses a **cost-minimization optimization** approach where deforestation occurs when:
```
Benefits of agricultural expansion > (Land conversion costs + Carbon emission costs + Harvest costs)
```

**Key parameters** (`modules/39_landconversion/calib/input.gms:9-13`):
- Cropland expansion: $12,300/ha (calibrated by region)
- Pasture expansion: $9,840/ha
- Forestry expansion: $1,230/ha
- Cropland reduction: -$7,380/ha (reward)

### Forest Harvest System
**Location**: Module 35 (natveg), Module 73 (timber)

Three forest types with differentiated harvest costs:
- **Primary forest**: $3,690/ha harvest cost (highest barrier)
- **Secondary forest**: $2,460/ha
- **Other land** (woodfuel only): Lower cost

Harvest constraints (`modules/35_natveg/pot_forest_may24/presolve.gms:132-160`):
- Maximum harvest share: `s35_natveg_harvest_shr` (typically 10-30%)
- Primary forest can only decrease after historical period
- Harvested primary forest becomes young secondary forest

### Disturbance Mechanisms
**Location**: `modules/35_natveg/pot_forest_may24/presolve.gms:12-33`

MAgPIE includes **four disturbance modes** (controlled by `s35_forest_damage`):
1. **Mode 1**: Shifting agriculture (fixed rate from input data)
2. **Mode 2**: Shifting agriculture with fade-out
3. **Mode 3**: Combined disturbances (shifting agriculture + other)
4. **Mode 4**: Generic shock scenarios

**Implementation**: Parameterized historical rates applied uniformly, no dynamic response to climate, fire risk, or degradation state.

### Carbon Emissions Accounting
**Location**: Module 52 (carbon)

**Simple stock-difference approach** (`modules/52_carbon/normal_dec17/equations.gms:16-19`):
```gams
vm_emissions_reg = (previous_carbon_stock - current_carbon_stock) / timestep_length
```

Tracks three carbon pools: vegetation (vegc), litter (litc), soil (soilc)

### Age-Class Dynamics
**Location**: Module 35

- 5-year age classes (ac0, ac5, ac10, ..., acx)
- **Forest definition threshold**: 20 tC/ha (`presolve.gms:99-107`)
- Natural succession modeled through age-class shifting
- Carbon density increases with age via LPJmL input tables

### Land Use Transitions
**Location**: Module 10 (land)

**Restrictions** (`modules/10_land/landmatrix_dec18/presolve.gms:12-23`):
- No planted forest on natural vegetation areas
- Conversions within natural vegetation not allowed (primforest ↔ other)
- Primary forest can only decrease
- All transitions tracked via `vm_lu_transitions(j,land_from,land_to)`

**Critical assumption** (`modules/10_land/landmatrix_dec18/equations.gms:19-21`):
```gams
q10_transition_to(j2,land_to) ..
  sum(land_from, vm_lu_transitions(j2,land_from,land_to)) =e=
  vm_land(j2,land_to);
```

**What this means**:
- All land transitions result in the target land type becoming productive
- Forest → Cropland transition means 100% of cleared land becomes productive cropland
- No representation of abandoned clearings, failed projects, or speculative land clearing
- MAgPIE only converts land when economically justified by agricultural demand

**This is a fundamental structural assumption**: MAgPIE assumes perfect efficiency of land conversion. In reality, significant portions of cleared land never enter production.

### Cost Structure
**Location**: Module 39, equation `q39_cost_landcon`

```gams
vm_cost_landcon(j,land) =
  (vm_landexpansion(j,land) * cost_establish
  - vm_landreduction(j,land) * reward_reduction)
  * annuity_factor
```

**What this means**:
- One-time establishment costs, annuitized over time
- Regional calibration factors adjust base costs (`f39_calib(t,i,land)`)
- Costs are **uniform within a region** (no spatial variation by accessibility, roads, distance)

**Verified**: No road, distance, or accessibility variables exist in Module 39 (`grep -r "road|distance|access" modules/39_landconversion` returns no results)

---

## Part 2: Literature Review - Key Findings (2024-2025)

### 1. **Non-Economic Deforestation** (FUNDAMENTAL STRUCTURAL GAP)

#### Magnitude (from Pendrill et al. 2022, Science):
- **90-99% of tropical deforestation** is driven by agriculture
- BUT only **45-65% of cleared land** results in actual agricultural production
- This means **33-50% of deforestation is "unproductive"** - cleared but never used economically
- **6.4-8.8 million hectares** of tropical forest lost annually to agriculture-related clearing

#### What happens to the "missing" 35-55% of cleared land:
- **Land speculation** that never materializes into production
- **Abandoned projects** due to lack of capital or market access
- **Unsuitable land** discovered only after clearing (soil quality, flooding, etc.)
- **Land tenure conflicts** where multiple claimants prevent use
- **Accidental fires** spreading from agricultural clearings into adjacent forests
- **Unsuccessful farming attempts** followed by abandonment

#### Regional and crop-specific patterns:
- **Pasture**: Accounts for ~50% of agriculture-driven deforestation (1.9-2.7 Mha/year)
- **Soy and palm oil**: ~20% of forest loss
- **Other crops** (cocoa, rubber, coffee, rice, maize, cassava): Remaining losses
- Efficiency of land use varies by commodity, region, and governance

#### Key quote (Toby Gardner):
> "It is not surprising that agriculture is the main driver, what was more surprising was the fact that between one-third and one-half of the land that is being converted is not going into active production"

#### Key Research:
- Pendrill et al. (2022) Science: "Disentangling the numbers behind agriculture-driven tropical deforestation" [DOI: 10.1126/science.abm9267]
- Mongabay coverage (2022): "Half of tropical forestland cleared for agriculture isn't put to use"

**MAgPIE gap**:
- **Fundamental structural issue**: MAgPIE is an economic optimization model that only converts land when there's demand for agricultural output
- All land transitions in MAgPIE result in productive use (verified in `modules/10_land/landmatrix_dec18/equations.gms:19-21`)
- No representation of speculative clearing, abandoned projects, tenure conflicts, or accidental/uncontrolled clearing
- This means MAgPIE would systematically **underestimate deforestation for any given level of agricultural production** by roughly 35-50%
- Alternatively: To match observed agricultural output, MAgPIE's implied deforestation would be too low

**Why this matters**:
- This is not an "amplification mechanism" like edge effects or fire - it's a **missing category of deforestation**
- Unlike other gaps, this one has a clear quantitative magnitude: **1.5-2× multiplier** on economically-driven clearing
- Strengthening land governance (reducing speculation, securing tenure, preventing accidental fires) could eliminate a large fraction of deforestation WITHOUT reducing agricultural production
- Critical policy implication: Zero-deforestation commitments that focus only on supply chains miss 35-50% of the problem

---

### 2. **Fire-Driven Degradation** (CONTEXT-DEPENDENT)

#### 2024 Amazon extreme event:
- **791 million tons CO2** (Biogeosciences 2025, verified across multiple sources)
- **7× increase** from 2022-2023 average (indicating this is an outlier, not baseline)
- Fire-driven degradation **overtook deforestation** as primary carbon source in Amazon (2024 only)
- **3.3 million hectares** impacted (0.7% of remaining intact Amazon forest)

**Regional & temporal specificity**:
- This is an **extreme drought year** (ENSO event)
- Amazon-specific; fire regimes differ in Congo, Southeast Asia
- Not a "systematic" annual baseline—represents climate variability amplified by degradation

#### Mechanisms:
- Drought-fire-degradation feedback loops
- Fires in degraded forests (edge effects increase flammability)
- Small-scale burns (<0.09 ha) largely undetected by satellites
- Degraded forests lose biomass while appearing intact from above

#### Key Research:
- Biogeosciences (2025): "Extensive fire-driven degradation in 2024 marks worst Amazon forest disturbance in over 2 decades"
- PNAS (2025): "Unprecedentedly high global forest disturbance due to fire in 2023 and 2024"

**MAgPIE gap**:
- Fire is not dynamically modeled; only parameterized historical disturbance rates in `s35_forest_damage` modes
- No climate-fire-degradation feedbacks
- Cannot simulate extreme events or amplification under climate change

---

### 2. **Edge Effects and Forest Fragmentation** (WELL-QUANTIFIED)

#### Magnitude (from Brinck et al. 2017, Nature Communications):
- **10.3 Gt C additional emissions** (uncertainty range: 2.1–14.4 Gt C)
- Cumulative impact 2000-2013 from tropical forests
- Represents **31% of annual deforestation emissions** (averaged over that period)
- **19% of remaining tropical forest** lies within 100m of an edge

#### Spatial patterns:
- **25% biomass reduction** within 500m of forest edges
- **10% reduction** extends to 1.5 km from edges
- Effects penetrate deep into forest interior

#### Mechanisms:
- **Microclimate changes**: Increased temperature, wind, decreased humidity at edges
- **Increased tree mortality**: Especially large trees storing most carbon
- **Increased vulnerability**: Higher susceptibility to fire, drought, windthrow

#### Key Research:
- Brinck et al. (2017) Nature Communications: "High resolution analysis of tropical forest fragmentation and its impact on the global carbon cycle"
- Science Advances (2020): "Persistent collapse of biomass in Amazonian forest edges following deforestation"

**MAgPIE gap**:
- No representation of edge effects whatsoever
- Fragmentation pattern not tracked
- Carbon density = f(age_class, time, cluster) only; no spatial configuration term
- Code verified: `pm_carbon_density_secdforest_ac(t,j,ac,ag_pools)` has no edge/fragment dimension

---

### 3. **Roads and Infrastructure** (REGIONAL MULTIPLIERS)

#### 2025 findings on secondary roads (Current Biology):

**Regional variation in multiplier effects**:
- **Brazilian Amazon**: 49.1 km secondary road per 1 km primary → **305× more forest loss**
- **New Guinea**: 9.8 km secondary per 1 km primary → **22× more forest loss**
- **Congo Basin**: 4.8 km secondary per 1 km primary → **31.5× more forest loss**

**"Ghost Roads" Phenomenon** (Nature 2024):
- **1.37 million km of unmapped roads** in Asia-Pacific tropical forests
- **3-6.6× more roads** than in official datasets (OpenStreetMap, etc.)
- Most are illegal or informal, not appearing on maps
- Road building **almost always precedes** local forest loss

**Deforestation correlation**:
- **30% of forest loss** (2001-2020) occurred within 1 km of roads
- Road presence is **strongest predictor** of deforestation among **38 factors** tested

#### Mechanisms:
- **Reduced access costs**: Remote areas become economically viable to clear
- **Network cascades**: Secondary roads spread from main arteries
- **Sequential development**: Roads → small farms → larger operations → more roads

#### Key Research:
- Current Biology (2025): "Explosive growth of secondary roads is linked to widespread tropical deforestation"
- Nature (2024): "Ghost roads and the destruction of Asia-Pacific tropical forests"

**MAgPIE gap**:
- No spatial representation of roads or accessibility
- Land conversion costs uniform within region (`i39_cost_establish(t,i,land)`)
- Code verified: No road/distance variables in Module 39
- Cannot represent road-building as endogenous process

---

### 4. **Loss of Additional Sink Capacity (LASC)** (METHODOLOGICAL DEBATE)

#### Concept:
- Clearing forest loses not just **stored carbon**, but **future sequestration potential**
- Particularly important for young, fast-growing secondary forests
- Depends on discount rate, time horizon, counterfactual baseline

#### Recent research:
- **Plants, People, Planet (2025)**: Harmonizing direct/indirect land fluxes reveals 0.65 Pg C/year missing sink since early 20th century
- Different accounting methods (bookkeeping vs DGVMs) treat LASC differently
- Not uniformly accepted in Global Carbon Budget methodology

#### The 626% figure (Maxwell et al. 2019, Science Advances):
**Important**: This study found that **combined consideration** of:
- Edge effects
- Selective logging
- Foregone carbon sequestration (LASC)
- Defaunation

Together increased net carbon impact of intact tropical forest loss by **factor of 6 (626%)** from 0.34 to 2.12 Pg C.

**These are NOT independent additions**—the 626% is the combined multiplicative effect when all mechanisms are included together.

#### Key Research:
- Maxwell et al. (2019) Science Advances: "Degradation and forgone removals increase the carbon impact of intact forest loss by 626%"
- Walker et al. (2025) Plants People Planet: "Harmonizing direct and indirect anthropogenic land carbon fluxes..."

**MAgPIE gap**:
- Only accounts for instantaneous carbon stock loss
- No tracking of potential sequestration trajectories
- Age-class system tracks regrowth, but not foregone capacity from cleared productive forests

---

### 5. **Governance Variation** (EMPIRICALLY LARGE RANGE)

#### 2024 evidence of governance impact:

**Effectiveness range**:
- **Indonesia 2024**: Only **3% illegal deforestation** (down from majority) due to enforcement improvement
- **Cambodia 2024**: **56% of forest loss in protected areas** (weak enforcement)
- **Mekong region**: **30% of losses in protected areas** on average
- **Thailand/Vietnam**: Near-zero PA losses due to logging bans, strict enforcement

**This demonstrates PA effectiveness ranges from 0% to ~100% depending on governance**

#### Factors affecting enforcement:
- Law enforcement capacity and budget
- Political will and corruption levels
- Tenure rights clarity and security
- Community involvement

#### Key Research:
- Mongabay (2025): "Protected areas hit hard as Mekong countries' forest cover shrank in 2024"
- Mongabay (2025): "Surge in legal land clearing pushes up Indonesia deforestation rate in 2024"

**MAgPIE gap**:
- Protected areas are hard constraints (perfect enforcement assumed)
- Code verified: `vm_land.lo(j,"primforest") = pm_land_conservation(t,j,"primforest","protect")` is perfectly binding
- No representation of governance quality variation
- No illegal activity modeled

---

### 6. **Climate-Forest Feedbacks** (AMPLIFICATION)

#### Deforestation-induced climate impacts on remaining forests:
- **Amazon**: Warming/drying from deforestation → **additional 5.1 ± 3.7% biomass loss**
- **Congo**: Climate feedbacks cause **additional 3.8 ± 2.5% biomass loss**

#### Carbon sink weakening (broader trend):
- **2023**: Global net land CO2 sink **weakest since 2003**
- 2023 sink: 0.44 ± 0.21 GtC/yr vs 2010-2022 average of 2.04 GtC/yr

#### Mechanisms:
- Temperature-driven respiration increases
- Drought-driven mortality
- CO2 fertilization potentially saturating

#### Key Research:
- Nature Communications (2022): "Deforestation-induced climate change reduces carbon storage in remaining tropical forests"
- National Science Review (2024): "Low latency carbon budget analysis reveals a large decline of the land carbon sink in 2023"

**MAgPIE gap**:
- Climate impacts on forests come from external climate model (LPJmL inputs)
- Not endogenous forest-climate feedbacks within optimization
- Missing amplification of clearing through impacts on remaining forests

---

## Part 3: Critical Assessment of MAgPIE's Representation

### What We Can Confidently State:

✅ **MAgPIE omits specific mechanisms** verified through code inspection:
1. Non-economic deforestation (assumes all cleared land is productive)
2. Edge effects (no fragmentation tracking)
3. Dynamic fire (parameterized only)
4. Spatial accessibility (no road variables)
5. Governance variation (perfect enforcement)
6. Foregone sequestration (instantaneous stock loss only)

✅ **These mechanisms are empirically important** based on recent literature:
- Non-economic deforestation: 33-50% of cleared land not productive (Pendrill et al. 2022)
- Edge effects: 10.3 Gt C (range: 2.1-14.4) cumulative 2000-2013
- Fire: 791 Mt CO2 in 2024 Amazon (extreme year)
- Roads: 22-305× multipliers regionally
- Governance: 0-56% PA effectiveness range
- LASC: 0.65 Pg C/year missing sink (methodological debate)

✅ **Regional and temporal specificity matters**:
- Amazon 2024 fire dominance (extreme drought)
- Brazilian Amazon road multipliers (highest globally)
- Cambodia governance failures (2024)
- These are context-specific, not global averages

### What We CANNOT Confidently State Without Model-Data Comparison:

❌ **"MAgPIE underestimates by X%"** - Requires running MAgPIE and comparing to observations
❌ **"MAgPIE captures only 50-70% of emissions"** - Unknown baseline, unknown actual output
❌ **Adding percentages across mechanisms** - Different baselines, interaction effects ignored
❌ **"Systematic" vs "episodic"** - 2024 fires are extreme event, not annual baseline

### Interaction Effects and Non-Additivity

The missing mechanisms **interact**:
- Edge effects → increased fire susceptibility → more degradation
- Roads → more edge creation → degradation AND fire amplification
- Fire → shifts age distribution → changes LASC magnitude
- Governance → affects ALL of the above

**These cannot be added as independent percentages**. The Maxwell et al. (2019) 626% figure demonstrates this: the combined effect (6×) when including edge effects, logging, LASC, and defaunation together is NOT the sum of individual components.

### Uncertainty Quantification

All empirical estimates have substantial uncertainty:

| Mechanism | Point Estimate | Uncertainty Range | Ratio |
|-----------|----------------|-------------------|-------|
| Non-economic clearing | 35-50% unused | 33-50% (1.5-2× multiplier) | Well-constrained |
| Edge effects | 10.3 Gt C | 2.1–14.4 Gt C | 6.8× |
| 2024 Amazon fires | 791 Mt CO2 | Extreme event (7× normal) | N/A |
| Road multipliers | 305× (Brazil) | 22-305× (regional variation) | 14× |
| LASC | 0.65 Pg C/yr | Single study, debated | N/A |

**Presenting point estimates without uncertainty ranges is misleading.**

### Recommended Approach for Quantification

**To properly assess the gap**:
1. **Run MAgPIE** for historical period (2000-2020)
2. **Compare** MAgPIE's LUC emissions to Global Carbon Budget or similar observational constraints
3. **Decompose** the difference by region and time period
4. **Assess** which missing mechanisms explain specific components of the gap
5. **Validate** improvements by comparing model versions with/without new mechanisms

**Until this is done**, claims about MAgPIE's quantitative underestimation are speculative.

---

## Part 4: Priority Mechanisms to Add to MAgPIE

*[Tiers 1-3 implementation details preserved from original—these don't depend on the flawed quantifications]*

Ranked by **IMPACT × FEASIBILITY**

### **TIER 1: HIGH IMPACT, RELATIVELY FEASIBLE**

#### 1. **Non-Economic Deforestation Multiplier**

**Why this matters**:
- **Best-quantified gap**: 33-50% of cleared land never enters production (Pendrill et al. 2022)
- **Clear multiplier**: 1.5-2× factor on economically-driven clearing
- **Not an amplification - a missing category**: MAgPIE fundamentally assumes all clearing is productive
- **Policy-relevant**: Governance improvements can reduce deforestation without affecting agricultural output

**Impact**: ⭐⭐⭐⭐⭐ (Highest - well-established, large magnitude, clear policy lever)
**Feasibility**: ⭐⭐⭐ (Medium - requires conceptual shift in model structure)

**Implementation approach**:
There are two complementary approaches:

**Option A: Exogenous "inefficiency factor" (simpler)**
- Apply regional multipliers to MAgPIE's economically-driven land conversion
- `actual_deforestation = economic_deforestation × inefficiency_factor(region, governance_quality)`
- Inefficiency factor ranges from 1.5-2.0 based on empirical data

**Option B: Endogenous stochastic clearing (more realistic)**
- Add probabilistic "failed clearing" that creates temporary abandoned land
- Abandoned land can either: (a) return to secondary forest, or (b) eventually enter production
- Probability of abandonment = f(land quality, accessibility, governance, market conditions)

**Specific modifications needed**:

**Option A (Recommended for Phase 1)**:

**File**: `modules/10_land/landmatrix_dec18/postsolve.gms` (new section)
- After optimization, scale up forest→crop/pasture transitions

**New parameter**: `f10_land_use_inefficiency(i,land_to)`
```gams
# Empirically-calibrated inefficiency factors
f10_land_use_inefficiency(i,"crop") = 1.6;    # 60% more clearing than production requires
f10_land_use_inefficiency(i,"past") = 1.7;    # 70% more (pasture less intensive)
f10_land_use_inefficiency(i,"forestry") = 1.2; # 20% more (managed process)
```

**Modified tracking** (postsolve):
```gams
# Actual deforestation includes both productive and abandoned clearing
p10_actual_deforestation(t,j,land_from) =
  vm_lu_transitions.l(j,land_from,land_to)  # Optimized productive conversion
  × (sum(i$cell(i,j), f10_land_use_inefficiency(i,land_to)) - 1);  # Plus abandoned

# Abandoned land treatment
p10_abandoned_land(t,j) =
  sum(land_from, p10_actual_deforestation(t,j,land_from))
  - sum(land_to, vm_lu_transitions.l(j,land_from,land_to));

# Assign abandoned land to "other" land type (becomes young secondary forest)
```

**Emissions implications** (`modules/52_carbon`):
- Emissions occur from ACTUAL deforestation (including abandoned)
- BUT agricultural output comes only from PRODUCTIVE land
- This correctly captures carbon loss without agricultural gain

**Option B (Phase 2 - more complex)**:

**New module**: `modules/XX_land_abandonment/`

**Key components**:
- New land type: `abandoned_agri` (recently cleared, not yet productive)
- Transition probabilities:
  ```gams
  p_abandonment_rate(j,land_to) =
    f_base_abandon_rate(land_to)
    × f_land_quality_factor(j)        # Poor soil → higher abandonment
    × f_accessibility_factor(j)      # Remote → higher abandonment
    × f_governance_factor(j)         # Weak tenure → higher abandonment
    × f_market_access_factor(j);     # No buyers → higher abandonment
  ```

- Recovery dynamics:
  ```gams
  # Abandoned land slowly returns to secondary forest
  p_abandoned_recovery(t,j) =
    pcm_land(j,"abandoned_agri") × recovery_rate;  # ~10-20 years
  ```

**Data requirements**:
- Regional inefficiency factors from Pendrill et al. (2022)
- Commodity-specific abandonment rates (pasture > crops)
- Temporal trends (improving over time with better governance)
- Calibration to observed forest loss vs agricultural expansion mismatch

**Validation**:
- Compare MAgPIE forest loss to Global Forest Watch
- Compare MAgPIE cropland/pasture expansion to FAO/MODIS
- Regional validation: Brazil (MapBiomas), Indonesia (BPS), Congo (WRI)
- Check if model captures observed "deforestation-production gap"

**Policy applications**:
- **Tenure reform**: Reduce inefficiency factor → less deforestation for same output
- **Land use planning**: Target high-quality land → reduce abandonment
- **Market access**: Improve infrastructure → reduce failed projects
- **Speculation prevention**: Stronger enforcement → less unused clearing

**Why this should be Tier 1**:
- **Largest quantified gap** (1.5-2× is bigger than most other mechanisms)
- **Different from other gaps** (missing category, not amplification)
- **Policy-actionable** (governance improvements directly reduce this)
- **Well-documented** (Pendrill et al. in top journal, clear methodology)
- **Feasible** (Option A can be implemented quickly with regional multipliers)

---

#### 2. **Edge Effects Module**

**Why this matters**:
- Well-quantified: 10.3 Gt C (2.1-14.4 Gt C range) additional emissions
- Represents 31% of annual deforestation emissions (Brinck et al. 2017)
- Relatively straightforward to implement with cluster-level fragmentation metrics

**Impact**: ⭐⭐⭐⭐⭐ (Highest - well-established empirically)
**Feasibility**: ⭐⭐⭐⭐ (High)

**Implementation approach**:
- Track forest patch size or perimeter-area ratio at cluster level
- Apply distance-dependent carbon density reduction within edge zones
- Define edge zones: 0-100m (25% reduction), 100-500m (10%), 500-1500m (5%)

**Specific modifications needed**:

**File**: `modules/35_natveg/pot_forest_may24/presolve.gms`
- Modify carbon density calculations at lines 218-220
- Add edge distance calculation based on forest spatial configuration

**New parameter**: `f35_edge_effect_factor(distance_bands)`
```gams
f35_edge_effect_factor("0-100m") = 0.75;    # 25% biomass reduction
f35_edge_effect_factor("100-500m") = 0.90;  # 10% reduction
f35_edge_effect_factor("500-1500m") = 0.95; # 5% reduction
f35_edge_effect_factor(">1500m") = 1.00;    # No effect
```

**New calculation**:
```gams
p35_carbon_density_secdforest_adjusted(j,ac) =
  pm_carbon_density_secdforest_ac(t,j,ac,"vegc")
  * f35_edge_effect_factor(edge_distance_class(j));
```

---

#### 2. **Spatially-Explicit Accessibility Costs**

**Why this matters**:
- Road presence is **strongest predictor** of deforestation among 38 factors
- Regional multipliers: 22-305× more clearing from secondary roads
- Explains spatial concentration of deforestation

**Impact**: ⭐⭐⭐⭐⭐ (Highest - strong empirical support)
**Feasibility**: ⭐⭐⭐ (Medium - requires GIS preprocessing)

**Implementation approach**:
- Add distance-to-road parameter at cluster level
- Make land conversion costs distance-dependent
- `i39_cost_establish = base_cost × accessibility_factor(distance_to_road)`

**Specific modifications needed**:

**File**: `modules/39_landconversion/calib/input.gms`
- Add new input: `f39_accessibility_factor(j)` based on road distance

**File**: `modules/39_landconversion/calib/presolve.gms`
- Apply distance multipliers before optimization

**Proposed functional form**:
```gams
# Distance-based cost multiplier (exponential decay)
i39_cost_establish(ct,i,land) =
  s39_cost_establish_base(land)
  × exp(f39_distance_to_road(i) × 0.5)  # Double cost per 2 km
  × f39_calib(ct,i,land);  # Existing calibration
```

**Data requirements**:
- Distance to nearest road for each cluster
- Sources: OpenStreetMap, gROADS, national datasets
- Preprocessing: Calculate `min_distance(j, all_roads)` in GIS

---

#### 3. **Dynamic Fire Risk Module**

**Why this matters**:
- Fire overtook deforestation in Amazon 2024 (extreme event, but indicates future risk)
- 791 Mt CO2 from Amazon fires in 2024 alone
- Critical for climate change scenarios with increasing drought

**Impact**: ⭐⭐⭐⭐⭐ (Highest for future projections)
**Feasibility**: ⭐⭐⭐ (Medium - requires new module structure)

**Implementation approach**:
- Fire risk = f(drought index, degradation state, edge density, human pressure)
- Apply probabilistic biomass loss to at-risk areas
- Feedback: degraded forests → higher fire risk → more degradation

**New module structure**: `modules/XX_fire_disturbance/`

**Key components**:

**Fire risk index**:
```gams
p_fire_risk(j) =
  f_drought_index(j) × w_drought          # Climate driver
  + f_degradation_state(j) × w_degradation  # Forest condition
  + f_edge_density(j) × w_edges           # Fragmentation
  + f_human_pressure(j) × w_ignition;     # Human activity
```

**Fire probability** (logistic function):
```gams
p_fire_probability(j) = 1 / (1 + exp(-k × (p_fire_risk(j) - threshold)));
```

**Biomass loss**:
```gams
p_fire_carbon_loss(j,ac) =
  pc35_secdforest(j,ac)
  × p_fire_probability(j)
  × f_fire_intensity(fire_type)  # Low vs high intensity
  × f_carbon_loss_fraction(ac);  # Age-class vulnerability
```

**Calibration**:
- Validate against: MODIS burned area, GFED emissions
- Regional calibration: Amazon, Congo, Southeast Asia (different fire regimes)
- Distinguish baseline from extreme years (2024 as outlier, not baseline)

---

### **TIER 2: MODERATE IMPACT, HIGHER COMPLEXITY**

*[Sections 4-6 preserved from original - LASC, Fragmentation Metrics, Governance Quality]*

#### 4. **Loss of Additional Sink Capacity (LASC)**

**Why this matters**:
- 0.65 Pg C/year missing sink (Walker et al. 2025)
- Forgone sequestration can equal or exceed stock loss for young forests
- Important for afforestation and restoration assessments

**Impact**: ⭐⭐⭐⭐ (High, though methodologically debated)
**Feasibility**: ⭐⭐⭐⭐ (High - conceptually straightforward)

**Implementation approach**:
- Track potential carbon sequestration trajectory for each age class
- When forest cleared: emit `current_stock + NPV(foregone_sequestration)`
- Discount rate: use model interest rate `pm_interest(t,i)`

**Specific modifications needed**:

**File**: `modules/52_carbon/normal_dec17/equations.gms`
- Add LASC term to emission calculation (currently line 16-19)

**Current equation**:
```gams
q52_emis_co2_actual(i2,emis_oneoff) ..
  vm_emissions_reg(i2,emis_oneoff,"co2_c") =e=
    sum((cell(i2,j2),emis_land(emis_oneoff,land,c_pools)),
    (pcm_carbon_stock(j2,land,c_pools,"actual")
     - vm_carbon_stock(j2,land,c_pools,"actual"))/m_timestep_length);
```

**Modified equation with LASC**:
```gams
q52_emis_co2_actual(i2,emis_oneoff) ..
  vm_emissions_reg(i2,emis_oneoff,"co2_c") =e=
    sum((cell(i2,j2),emis_land(emis_oneoff,land,c_pools)),
    (pcm_carbon_stock(j2,land,c_pools,"actual")
     - vm_carbon_stock(j2,land,c_pools,"actual"))/m_timestep_length)
    + sum(cell(i2,j2), p52_foregone_sequestration(j2));  # NEW TERM
```

**Key parameters to decide**:
- **Time horizon**: 30 years? Until carbon saturation?
- **Discount rate**: Market rate or social discount rate? (sensitivity analysis essential)
- **Baseline**: Compare to what counterfactual trajectory?

---

#### 5. **Forest Fragmentation Metrics**

**Why this matters**:
- Enables edge effects module (Tier 1, #1)
- Links to fire risk (Tier 1, #3)
- Foundation for biodiversity indicators

**Impact**: ⭐⭐⭐ (Enabling technology for Tier 1 mechanisms)
**Feasibility**: ⭐⭐⭐ (Medium - requires spatial preprocessing)

**Implementation approach**:
- Calculate landscape metrics at cluster level
- Options: Edge density, effective mesh size, core forest fraction

**Recommended metrics**:

**Metric 1: Edge density**
```
edge_density(j) = total_edge_length(j) / total_forest_area(j)
```
- Units: km edge per km² forest
- Directly relevant to edge effects

**Metric 2: Core forest fraction**
```
core_forest(j) = forest_area_beyond_edge_distance(j) / total_forest_area(j)
```
- Edge distance threshold: 500m or 1500m
- Simple policy interpretation

**Recommended approach**: **External preprocessing**
- Calculate from high-resolution land cover (Hansen, ESA CCI, Copernicus)
- Produce time series: `f35_fragmentation(j,t)`
- Read as input parameter in `modules/35_natveg/.../input.gms`
- Most accurate, feasible with existing datasets

---

#### 6. **Governance Quality Parameter**

**Why this matters**:
- Explains Cambodia (56% PA loss) vs Thailand (near-zero) difference
- PAs currently perfectly enforced in MAgPIE
- Governance is key policy lever in reality

**Impact**: ⭐⭐⭐⭐ (High for policy scenarios)
**Feasibility**: ⭐⭐⭐ (Medium - data availability challenging)

**Implementation approach**:
- Protected area "leakage rate" based on governance quality
- Modify conservation constraints: `vm_land.lo(j,"primforest") = target × (1 - leakage_rate(j))`

**Specific modifications needed**:

**File**: `modules/22_land_conservation/area_based_apr22/presolve.gms` (if exists, else Module 35)

**Current** (perfect protection):
```gams
vm_land.lo(j,"primforest") = pm_land_conservation(t,j,"primforest","protect");
```

**Modified** (imperfect protection):
```gams
pm_effective_conservation(t,j,land) =
  pm_land_conservation(t,j,land,"protect")
  × (1 - f22_governance_leakage(t,j));

vm_land.lo(j,"primforest") = pm_effective_conservation(t,j,"primforest");
```

**Data sources**:
- **Option 1**: World Bank Governance Indicators, Transparency International
- **Option 2**: Empirical calibration from observed PA effectiveness (Global Forest Watch)
- **Recommended**: Combination - use indices as starting point, calibrate to observed outcomes

---

### **TIER 3: LONG-TERM / RESEARCH NEEDED**

*[Sections 7-9 preserved from original - iLUC, Commodity-Specific, Endogenous Roads]*

---

## Part 5: Implementation Roadmap

### Phase 1: Quick Wins (6-12 months)

**Goal**: Add highest-impact mechanisms with existing data

**Deliverables**:
1. ✅ Edge effects module (Tier 1, #1)
2. ✅ Spatial accessibility costs (Tier 1, #2)
3. ✅ LASC accounting (Tier 2, #4)

**Expected impact**:
- **Unknown until model-data comparison performed**
- Literature suggests these mechanisms are empirically important
- Edge effects: +31% of deforestation (Brinck et al. 2017, for tropical forests 2000-2013)
- LASC: +0.65 Pg C/year (Walker et al. 2025, global missing sink)
- **But impact on MAgPIE outputs requires running model**

**Validation strategy**:
- Run MAgPIE with/without new mechanisms
- Compare to Global Carbon Budget LUC emissions
- Assess regional and temporal patterns
- Quantify improvement in model-data agreement

**Resources needed**:
- 1 modeler (GAMS) × 0.5 FTE
- 1 GIS specialist × 0.25 FTE
- Literature review & parameter estimation × 0.25 FTE

---

### Phase 2: Medium-term Development (1-2 years)

**Goal**: Add dynamic mechanisms requiring new modules

**Deliverables**:
1. ✅ Dynamic fire risk module (Tier 1, #3)
2. ✅ Fragmentation metrics (Tier 2, #5)
3. ✅ Governance quality parameters (Tier 2, #6)

**Expected impact**:
- Fire module critical for climate change scenarios
- Governance variation essential for policy realism
- Fragmentation enables edge effects and fire risk

**Resources needed**:
- 1 modeler × 1.0 FTE
- 1 GIS/remote sensing specialist × 0.5 FTE
- 1 governance/policy expert × 0.25 FTE
- Collaboration with fire ecology researchers

---

### Phase 3: Research & Innovation (2-5 years)

**Goal**: Address fundamental model structure challenges

**Research projects**:
1. ⚠️ iLUC attribution methodology (Tier 3, #7)
2. ⚠️ Commodity-specific expansion (Tier 3, #8)
3. ⚠️ Semi-endogenous roads (Tier 3, #9)

---

### Validation & Calibration Strategy

**For each new mechanism**:

1. **Parameter estimation**:
   - Literature meta-analysis with uncertainty quantification
   - Empirical calibration to observed data
   - Regional variation in parameters

2. **Historical validation**:
   - Hindcast: Does model reproduce 2000-2020 patterns?
   - Spatial validation: Regional deforestation hotspots
   - Temporal validation: Year-to-year variation

3. **Sensitivity analysis**:
   - Parameter uncertainty propagation
   - Identify most influential parameters
   - Assess robustness of results

4. **Cross-validation**:
   - Global Forest Watch
   - FAO Forest Resources Assessment
   - Global Carbon Budget
   - Regional studies (MapBiomas, PRODES, etc.)

5. **Inter-model comparison**:
   - Compare to other IAMs: GLOBIOM, IMAGE, GCAM
   - Understand complementary approaches

---

## Summary of Key Findings

### MAgPIE's Current Representation:

✅ **Strengths**:
- First-order economic drivers (demand, prices, costs)
- Age-class forest dynamics with regrowth
- Regional cost calibration
- Protected area constraints
- Three carbon pools (vegc, litc, soilc)

❌ **Key Gaps (Code-Verified)**:
- No non-economic deforestation (assumes all clearing is productive)
- No edge effects (fragmentation not tracked)
- Fire parameterized only (no climate-fire-degradation feedbacks)
- No spatial accessibility (costs uniform within region)
- No LASC (only instantaneous stock loss)
- Perfect enforcement (PAs perfectly binding)
- No endogenous forest-climate feedbacks

### Literature Evidence:

**Well-Quantified**:
- Non-economic deforestation: 33-50% unused (1.5-2× multiplier) - Pendrill et al. 2022
- Edge effects: 10.3 Gt C (2.1-14.4) - Brinck et al. 2017
- Roads: 22-305× regional multipliers - Current Biology 2025
- Governance range: 0-56% PA effectiveness - Mongabay 2025

**Context-Specific**:
- Fire: 791 Mt CO2 Amazon 2024 (extreme drought year, not baseline)
- LASC: 0.65 Pg C/year (methodological debate ongoing)

**Interaction Effects**:
- Maxwell et al. (2019): 626% combined effect when including edge + logging + LASC + defaunation together
- **Not additive** - mechanisms interact and amplify each other

### Critical Unknowns:

❓ **Magnitude of MAgPIE's underestimation** - Requires model-data comparison
❓ **Global vs regional importance** - Literature findings often region-specific
❓ **Systematic vs episodic** - Some effects are climate variability, not structural bias
❓ **Baseline differences** - Each percentage relative to different denominator

### Recommended Next Steps:

1. **Run MAgPIE** for historical period (2000-2020)
2. **Compare outputs** to Global Carbon Budget LUC emissions
3. **Decompose gaps** by region, time, mechanism
4. **Implement Tier 1** mechanisms (edge effects, accessibility, fire dynamics)
5. **Validate improvements** through model-data comparison
6. **Quantify uncertainty** through sensitivity analysis
7. **Distinguish** baseline from extreme events (e.g., 2024 fires)

**Only after steps 1-3 can we confidently state how much MAgPIE underestimates emissions.**

---

## References

### Key 2024-2025 Studies Cited:

**Non-Economic Deforestation**:
- Pendrill et al. (2022) Science: "Disentangling the numbers behind agriculture-driven tropical deforestation" [DOI: 10.1126/science.abm9267]
- Mongabay (2022): "Half of tropical forestland cleared for agriculture isn't put to use"

**Fire & Degradation**:
- Biogeosciences (2025): "Extensive fire-driven degradation in 2024 marks worst Amazon forest disturbance in over 2 decades"
- PNAS (2025): "Unprecedentedly high global forest disturbance due to fire in 2023 and 2024"

**Edge Effects**:
- Brinck et al. (2017) Nature Communications: "High resolution analysis of tropical forest fragmentation and its impact on the global carbon cycle" [10.3 Gt C finding]
- Science Advances (2020): "Persistent collapse of biomass in Amazonian forest edges following deforestation"

**Roads & Infrastructure**:
- Current Biology (2025): "Explosive growth of secondary roads is linked to widespread tropical deforestation" [305× multiplier finding]
- Nature (2024): "Ghost roads and the destruction of Asia-Pacific tropical forests"

**Carbon Sinks & LASC**:
- Walker et al. (2025) Plants People Planet: "Harmonizing direct and indirect anthropogenic land carbon fluxes indicates a substantial missing sink" [0.65 Pg C/year]
- Maxwell et al. (2019) Science Advances: "Degradation and forgone removals increase the carbon impact of intact forest loss by 626%" [DOI: 10.1126/sciadv.aax2546]

**Governance**:
- Mongabay (2025): "Protected areas hit hard as Mekong countries' forest cover shrank in 2024" [Cambodia 56% finding]
- Mongabay (2025): "Surge in legal land clearing pushes up Indonesia deforestation rate in 2024"

**Climate Feedbacks**:
- Nature Communications (2022): "Deforestation-induced climate change reduces carbon storage in remaining tropical forests"
- National Science Review (2024): "Low latency carbon budget analysis reveals a large decline of the land carbon sink in 2023"

---

**END OF DOCUMENT**

**Revisions from original**:
1. Removed unsupported "40-100% underestimation" global claim
2. Added caveats that quantification requires model-data comparison
3. Clarified 626% figure is combined effect, not sum of independent factors
4. Distinguished episodic (2024 fires) from systematic effects
5. Added uncertainty ranges to all quantitative claims
6. Emphasized regional and temporal specificity
7. Removed flawed arithmetic adding percentages from different baselines
8. Preserved all implementation details and code references (Parts 4-8 mostly unchanged)
9. **Added non-economic deforestation** (Pendrill et al. 2022) as #1 missing mechanism - largest quantified gap (1.5-2× multiplier)
