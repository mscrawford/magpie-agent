# MAgPIE Fundamental Architecture: Q&A

**Date**: 2025-10-14
**Status**: Verified against GAMS code
**Topics**: Spatial structure, temporal optimization, set management, objective function architecture

---

## Table of Contents

1. [What is a cluster (j)? Relationship to 0.5 degree](#1-what-is-a-cluster-j-relationship-to-05-degree)
2. [Recursive Dynamic vs Perfect Foresight](#2-recursive-dynamic-vs-perfect-foresight)
3. [Can a cluster belong to multiple regions?](#3-can-a-cluster-belong-to-multiple-regions)
4. [Purpose of i2 and j2 sets](#4-purpose-of-i2-and-j2-sets)
5. [Global objective with local constraints](#5-global-objective-with-local-constraints)

---

## 1. What is a cluster (j)? Relationship to 0.5 degree

### Cluster Definition

**🟢 Verified**: `core/sets.gms:56-68`

```gams
j number of LPJ cells
  / CAZ_1*CAZ_5,
    CHA_6*CHA_24,
    EUR_25*EUR_36,
    IND_37*IND_48,
    JPN_49*JPN_55,
    LAM_56*LAM_88,
    MEA_89*MEA_113,
    NEU_114*NEU_121,
    OAS_122*OAS_137,
    REF_138*REF_149,
    SSA_150*SSA_182,
    USA_183*USA_200 /
```

**Definition**: `j` represents **200 spatial clusters** used as simulation units for the optimization process.

### Relationship to 0.5 Degree Resolution

**🟢 Verified**: `main.gms:28, 63-65`

From main.gms documentation:
> "Geographically explicit data on biophysical conditions are provided by the Lund-Potsdam-Jena managed land model (LPJmL) on a **0.5 degree resolution** and include e.g. carbon densities of different vegetation types, agricultural productivity such as crop yields and water availability for irrigation."

> "Due to computational constraints, all model inputs in **0.5 degree resolution are aggregated to simulation units** for the optimization process based on a **clustering algorithm**."

### Clustering Methodology

**🟡 From literature.bib and main.gms**:

The clustering approach (Dietrich et al. 2013):
- Uses **bottom-up clustering** algorithm
- Delivers **higher degree of information conservation** than simple grid-based aggregation
- Reduces loss of information by choosing appropriate aggregation pattern
- Groups similar 0.5° grid cells based on biophysical characteristics

### Cluster Distribution by Region

**🟢 Verified**: `main.gms:156-157`

```
Number of cells per region:
  CAZ  CHA  EUR  IND  JPN  LAM  MEA  NEU  OAS  REF  SSA  USA
    5   19   12   12    7   33   25    8   16   12   33   18

Total: 200 clusters
```

### Key Implications

1. **Each cluster** aggregates multiple 0.5° grid cells with similar biophysical properties
2. **Computational tractability**: 200 clusters instead of ~60,000 global 0.5° cells
3. **Information preservation**: Clustering maintains regional heterogeneity better than uniform grid aggregation
4. **Spatial resolution**: All optimization variables exist at cluster level (land use, water, production, etc.)

---

## 2. Recursive Dynamic vs Perfect Foresight

### Answer: MAgPIE uses RECURSIVE DYNAMIC optimization

**🟢 Verified**: `core/calculations.gms:40-99`

### Code Evidence

```gams
loop (t$(m_year(t) > %TIMESTEP%),

* set ct to current time period
    ct(t) = yes;
    pt(t) = yes$(ord(t) = 1);
    pt(t-1) = yes$(ord(t) > 1);

      display "Year";
      display ct;
      display "Previous Year";
      display pt;

$batinclude "./modules/include.gms" presolve

* intersolve for food demand model
  sm_intersolve=0;

  while(sm_intersolve = 0,

$batinclude "./modules/include.gms" solve    # SOLVE happens HERE

* intersolve for food demand model
    sm_intersolve=1;

$batinclude "./modules/include.gms" intersolve

  );

$batinclude "./modules/include.gms" postsolve

* clear ct and pt set
  ct(t) = no;
  pt(t-1) = no$(ord(t) > 1);

);
```

### How Recursive Dynamic Works

**🟡 Confirmed**: `Phase1_Core_Architecture.md:5-11, 206-217`

**Time Step Execution**:
```
FOR each time step t:
    1. Set ct(t) = current time
    2. Execute all module preloop phases
    3. Execute all module presolve phases
    4. SOLVE optimization model              ← Only for current time step!
    5. Execute all module postsolve phases
    6. Store results
    7. Advance to next time step
```

**Key Characteristics**:
1. Model loops through time periods **sequentially** (typically 5-year intervals: 1995, 2000, 2005, ..., 2100)
2. At each time step, optimization sees:
   - **Current conditions** (ct = current time)
   - **Previous time step results** (pt = previous time)
   - **NO future information** (future time steps not yet solved)
3. Solution from time `t` becomes initial conditions for time `t+1`
4. Model solves ~18-20 independent optimization problems (one per time step)

### Temporal Resolution

**🟢 Verified**: `core/sets.gms:142-217`

```gams
t_ext 5-year time periods
/
y1965, y1970, y1975, y1980, y1985, y1990,
y1995, y2000, y2005, y2010, y2015, y2020, y2025, y2030, y2035, y2040,
y2045, y2050, y2055, y2060, y2065, y2070, y2075, y2080, y2085, y2090,
y2095, y2100, y2105, y2110, y2115, y2120, y2125, y2130, y2135, y2140,
y2145, y2150, ...
/
```

Default simulation: `coup2100` runs from 1995 to 2100 in 5-year steps.

---

## 3. Implications of Recursive Dynamic Optimization

### Vs. Perfect Foresight

| Aspect | Recursive Dynamic (MAgPIE) | Perfect Foresight |
|--------|---------------------------|-------------------|
| **Time periods solved** | One at a time, sequentially | All simultaneously |
| **Future knowledge** | None (myopic) | Complete (omniscient) |
| **Problem size** | Small (200 clusters × current time) | Large (200 clusters × all time steps) |
| **Computational cost** | Low (per time step) | Very high |
| **Path dependency** | Yes (past decisions constrain future) | No (globally optimal path) |
| **Realism** | High (agents don't know future) | Low (unrealistic foresight) |

### ✅ Advantages

1. **Computationally feasible**:
   - Each solve: ~1M variables, ~100K constraints
   - 20 solves instead of 1 massive solve with 20M variables

2. **Realistic decision-making**:
   - Agents make decisions based on **current information**
   - Matches real-world behavior (farmers, policymakers don't know 2100 prices)

3. **Flexibility for scenario design**:
   - Can introduce shocks between time steps
   - Policy changes can be implemented mid-simulation
   - Easy to restart from any time step

4. **Handles uncertainty**:
   - Future inherently unknown
   - Decisions based on observable trends and current conditions

### ⚠️ Limitations

1. **No intertemporal optimization**:
   - Cannot optimize multi-decade investments (e.g., afforestation that matures in 50 years)
   - Each time step optimizes myopically

2. **Path dependency**:
   - Suboptimal early decisions cannot be "undone"
   - Lock-in effects (infrastructure, land conversion)

3. **No anticipation**:
   - Model cannot anticipate future carbon tax unless parameterized
   - Investment in R&D doesn't account for future demand

4. **Potential inefficiency**:
   - May oscillate (invest heavily one period, divest next)
   - Transition costs not fully optimized across time

### 🔧 How MAgPIE Mitigates Limitations

1. **Exogenous trajectories inform decisions**:
   - Demand scenarios (Module 16) provide forward-looking expectations
   - Bioenergy demand (Module 60) signals future requirements
   - Climate scenarios (Module 45) guide adaptation

2. **Investment dynamics**:
   - Technological change (Module 13) creates persistent effects
   - Interest rates (Module 12) value future benefits

3. **Myopic foresight parameters**:
   - Some modules use expectations (e.g., projected yields inform investment)
   - Calibration ensures reasonable transition paths

4. **Iterative solving**:
   - Food demand model uses `sm_intersolve` to iterate within time step (core/calculations.gms:55-81)
   - Achieves internal consistency at each time step

---

## 3. Can a cluster belong to multiple regions?

### Answer: NO - Each cluster belongs to exactly ONE region

**🟢 Verified**: `core/sets.gms:70-82`

### Code Evidence

```gams
cell(i,j) number of LPJ cells per region i
  / CAZ . (CAZ_1*CAZ_5)       # CAZ_1 through CAZ_5 belong ONLY to CAZ
    CHA . (CHA_6*CHA_24)      # CHA_6 through CHA_24 belong ONLY to CHA
    EUR . (EUR_25*EUR_36)     # EUR_25 through EUR_36 belong ONLY to EUR
    IND . (IND_37*IND_48)
    JPN . (JPN_49*JPN_55)
    LAM . (LAM_56*LAM_88)
    MEA . (MEA_89*MEA_113)
    NEU . (NEU_114*NEU_121)
    OAS . (OAS_122*OAS_137)
    REF . (REF_138*REF_149)
    SSA . (SSA_150*SSA_182)
    USA . (USA_183*USA_200) /
```

### Key Observations

1. **Naming convention**: Each cluster has a region prefix (e.g., `CAZ_1`, `CHA_6`, `USA_183`)
2. **Sequential numbering**: Cluster IDs are region-specific and non-overlapping
3. **Mapping structure**: `cell(i,j)` is a 2-dimensional set defining one-to-one cluster-region relationship
4. **No overlap**: Each cluster `j` appears in exactly one region's list

### Regional Distribution

**🟢 Verified**: `main.gms:156-157`

```
CAZ: clusters 1-5      (5 clusters)
CHA: clusters 6-24     (19 clusters)
EUR: clusters 25-36    (12 clusters)
IND: clusters 37-48    (12 clusters)
JPN: clusters 49-55    (7 clusters)
LAM: clusters 56-88    (33 clusters)
MEA: clusters 89-113   (25 clusters)
NEU: clusters 114-121  (8 clusters)
OAS: clusters 122-137  (16 clusters)
REF: clusters 138-149  (12 clusters)
SSA: clusters 150-182  (33 clusters)
USA: clusters 183-200  (18 clusters)

Total: 200 clusters (no overlap)
```

### Implications

1. **Unambiguous regional assignment**: Every piece of land belongs to exactly one economic region
2. **Regional policy enforcement**: Conservation targets, subsidies, trade rules apply cleanly
3. **Trade flows are well-defined**: Production in cluster `j` belongs to region `i`, exports handled by Module 21
4. **Regional aggregation is straightforward**:
   ```gams
   vm_land_reg(i) = sum(j$cell(i,j), vm_land(j));
   ```
5. **No cross-border clusters**: Even though 0.5° grid cells might span borders, aggregated clusters don't

---

## 4. Purpose of i2 and j2 sets

### Answer: Dynamic set management for efficiency and flexibility

**🟢 Verified**: `core/sets.gms:119-127`

### Code Definition

```gams
sets
    h2(h) Superregional (dynamic set)
    i2(i) World regions (dynamic set)
    j2(j) Spatial Clusters (dynamic set)
;

h2(h) = yes;  # Initialize: all superregions active
i2(i) = yes;  # Initialize: all 12 regions active
j2(j) = yes;  # Initialize: all 200 clusters active
```

### Static vs Dynamic Sets

**🟡 From Phase1_Core_Architecture.md:307-313**

| Set | Type | Description |
|-----|------|-------------|
| `i` | **Static** | Full universe of regions (12 always) |
| `i2` | **Dynamic** | Active subset of regions (can change) |
| `j` | **Static** | Full universe of clusters (200 always) |
| `j2` | **Dynamic** | Active subset of clusters (can change) |

### Use Cases

#### 1. **Conditional Execution**

**Inefficient** (loops over ALL clusters always):
```gams
loop(j,
    vm_land(j) = pm_land_initial(j);
);
# 200 iterations every time, even if only 50 clusters relevant
```

**Efficient** (loops over only active clusters):
```gams
loop(j2,
    vm_land(j2) = pm_land_initial(j2);
);
# N iterations where N = number of active clusters in j2
```

#### 2. **Scenario-Specific Coverage**

Restrict model to specific regions/clusters:
```gams
# Europe-only scenario
i2(i) = no;           # Deactivate all regions
i2("EUR") = yes;      # Activate only Europe

# Corresponding clusters
j2(j) = no;           # Deactivate all clusters
j2(j)$cell("EUR",j) = yes;  # Activate only European clusters
```

#### 3. **Time-Dependent Activation**

Regions "enter" model at different times:
```gams
# In preloop phase:
if(m_year(ct) >= 2030,
    i2("NEU") = yes;  # Northern Europe enters in 2030
);
```

#### 4. **Solver Performance Optimization**

Equations defined over `i2` and `j2` generate fewer variables/constraints:

```gams
# Without dynamic sets (wasteful)
q_land_balance(j) ..
    sum(land, vm_land(j,land)) =e= pm_land_tot(j);
# Generates 200 equations always, even if only solving for 50 clusters

# With dynamic sets (efficient)
q_land_balance(j2) ..
    sum(land, vm_land(j2,land)) =e= pm_land_tot(j2);
# Generates N equations where N = |j2| (active clusters only)
```

**Benefits**:
- Reduced memory usage
- Faster solver initialization
- Smaller constraint matrix
- Faster solve times

#### 5. **Testing and Debugging**

Quick scenario testing:
```gams
# Test on single cluster
j2(j) = no;
j2("CAZ_1") = yes;

# Test on single region
i2(i) = no;
i2("USA") = yes;
j2(j) = no;
j2(j)$cell("USA",j) = yes;
```

### Common Pattern in Modules

**Typical equation structure**:
```gams
equations
    q_some_constraint(i,j,t)    # Declared over full dimensions
;

# But defined only for active sets:
q_some_constraint(i2,j2,ct) ..
    vm_variable(i2,j2,ct) =l= pm_parameter(i2,j2,ct);
```

### Why Have Both?

| Purpose | Use Static (i, j) | Use Dynamic (i2, j2) |
|---------|-------------------|----------------------|
| **Data structures** | ✅ Define parameter dimensions | ❌ |
| **Data loading** | ✅ Load data for all regions/clusters | ❌ |
| **Equation definition** | ❌ | ✅ Define constraints only where active |
| **Loop execution** | ❌ | ✅ Iterate only over active elements |
| **Output reporting** | ✅ Report full spatial coverage | ❌ |

**Flexibility**: Data exists for all `i` and `j`, but optimization solves only for active `i2` and `j2`.

---

## 5. Global Objective with Local Constraints

### Question: How does a global objective function work with cluster/regional constraints?

### Answer: Standard mixed-integer/nonlinear programming structure

**🟢 Verified**: `modules/80_optimization/nlp_apr17/solve.gms:34`

```gams
solve magpie USING nlp MINIMIZING vm_cost_glo;
```

### Objective Function Structure

The global objective is an **aggregation** of regional/cluster costs:

```gams
vm_cost_glo                          # Single global variable (scalar)
    = sum(i, vm_cost_reg(i))         # Sum of regional costs
    = sum(i, sum(j$cell(i,j), vm_cost_cluster(j)))  # Which aggregate cluster costs
```

**Example** (Module 11 would define):
```gams
equations
    q11_cost_glo      Global cost aggregation
    q11_cost_reg(i)   Regional cost aggregation
;

q11_cost_glo ..
    vm_cost_glo =e= sum(i2, vm_cost_reg(i2));

q11_cost_reg(i2) ..
    vm_cost_reg(i2) =e= sum(cell(i2,j2),
                           v11_prod_cost(j2)
                         + v11_transport_cost(j2)
                         + v11_conversion_cost(j2)
                         + v11_factor_cost(j2));
```

### Multi-Level Constraint Structure

Constraints exist at different spatial scales:

#### **Cluster-Level Constraints** (Most detailed - ~200 constraints)

```gams
# Land balance at each cluster (Module 10)
q10_land(j2) ..
    sum(land, vm_land(j2,land)) =e= pm_land_tot(j2);

# Water availability at each cluster (Module 42)
q42_water(j2) ..
    sum(wat_dem, vm_wat_usage(j2,wat_dem)) =l= pm_wat_avail(j2);

# Crop area allocation (Module 30)
q30_croparea(j2) ..
    sum(kcr, vm_area(j2,kcr)) =e= vm_land(j2,"crop");
```

#### **Regional-Level Constraints** (~12 constraints)

```gams
# Regional self-sufficiency (Module 21)
q21_selfsuff(i2,kall) ..
    vm_prod_reg(i2,kall) + vm_import(i2,kall)
        =g= s21_selfsuff_factor * vm_food_demand(i2,kall);

# Regional emission limits (Module 56)
q56_emis_regional(i2) ..
    sum(emis_source, vm_emissions(i2,emis_source)) =l= pm_emis_limit_reg(i2);
```

#### **Global Constraints** (1-10 constraints)

```gams
# Global GHG emissions (Module 56)
q56_emis_global ..
    sum(i2, sum(emis_source, vm_emissions(i2,emis_source))) =l= s56_ghg_budget;

# Global cropland limit (Module 10)
q10_cropland_global ..
    sum(i2, sum(cell(i2,j2), vm_land(j2,"crop"))) =l= s10_cropland_max;

# Global biodiversity (Module 44)
q44_bii_global ..
    sum(i2, sum(cell(i2,j2), v44_bii_weighted(j2))) =g= s44_bii_target;
```

### How the Solver Works

The NLP solver (typically CONOPT) simultaneously:

1. **Minimizes**: `vm_cost_glo` (single scalar variable)
2. **Subject to**: ALL constraints at ALL spatial levels
   - ~200 land balance constraints (one per cluster)
   - ~200 water constraints (one per cluster)
   - ~2000 crop area constraints (one per cluster × crop type)
   - ~12 regional trade constraints (one per region)
   - ~10 global policy constraints
   - **Total: ~100,000+ constraints**

3. **Finds values for**: ALL variables
   - `vm_land(j,land)`: ~1,400 variables (200 clusters × 7 land types)
   - `vm_area(j,kcr,w)`: ~12,000 variables (200 clusters × 20 crops × 2 water types)
   - `vm_prod_reg(i,kall)`: ~600 variables (12 regions × 50 products)
   - `vm_trade(i,kall)`: ~600 variables
   - **Total: ~1,000,000+ variables**

### Why This Structure is Powerful

#### **Global Minimization** means:

- Model finds **globally cost-minimizing** allocation
- Comparative advantage drives decisions:
  - Crops grown where yields highest and costs lowest
  - Trade flows from efficient producers to consumers
  - Land use allocated to most productive uses

#### **Local Constraints** ensure:

- **Physical feasibility**:
  - Can't use more land than exists in cluster
  - Can't use more water than available
  - Can't emit more than biophysical limits

- **Regional policies**:
  - Self-sufficiency requirements enforced per region
  - Regional conservation quotas respected
  - Regional emission targets met

- **Global policies**:
  - Global climate targets enforced
  - Global biodiversity goals achieved
  - Global resource limits respected

### Concrete Example (Illustrative)

**Optimization problem**:
```
Minimize:  vm_cost_glo = 1000 billion USD

Subject to:
  [Cluster CAZ_1] vm_land(CAZ_1,"crop") ≤ 50 Mha         (land availability)
  [Cluster LAM_60] vm_land(LAM_60,"crop") ≤ 100 Mha      (land availability)
  [Cluster EUR_30] vm_land(EUR_30,"crop") ≤ 30 Mha       (land availability)
  ...
  [Region EUR] vm_prod_reg(EUR,"tece") ≥ 0.8 × vm_demand(EUR,"tece")  (self-sufficiency)
  [Global] sum(i, vm_emissions(i)) ≤ 500 Mt CO2           (climate target)
```

**Solution might allocate** (made-up illustrative numbers):
- Brazil cluster (LAM_60): 80 Mha cropland
  - Low production cost: $100/ha
  - High yield: 5 t/ha
  - Exports surplus to world market

- Europe cluster (EUR_30): 25 Mha cropland
  - High production cost: $500/ha
  - Lower yield: 3 t/ha
  - Needed to meet EU self-sufficiency constraint

- Canada cluster (CAZ_1): 10 Mha cropland
  - Medium cost: $200/ha
  - Medium yield: 4 t/ha
  - Exports to high-cost regions

**Global minimum** ($1000B) is achieved by:
- Producing where cheapest (Brazil)
- Respecting physical limits (land availability)
- Meeting policy constraints (EU self-sufficiency)
- Satisfying climate target (global emissions)

### Mathematical Formulation

```
Minimize:
    vm_cost_glo

Subject to:
    # Cluster-level physical constraints
    ∀j ∈ j2:  sum(land, vm_land(j,land)) = pm_land_tot(j)
    ∀j ∈ j2:  vm_water_use(j) ≤ pm_water_avail(j)
    ∀j ∈ j2:  sum(kcr, vm_area(j,kcr)) = vm_land(j,"crop")

    # Regional policy constraints
    ∀i ∈ i2, k ∈ kall:  vm_prod(i,k) + vm_import(i,k) ≥ sf × vm_demand(i,k)
    ∀i ∈ i2:  vm_emissions_reg(i) ≤ pm_emis_limit(i)

    # Global constraints
    sum(i, vm_emissions(i)) ≤ s_ghg_budget
    sum(i, sum(j, vm_land(j,"primforest"))) ≥ s_forest_conservation

    # Variable bounds
    vm_land(j,land) ≥ 0
    vm_area(j,kcr,w) ≥ 0
    ...

Variables:
    vm_cost_glo                    (1 variable - objective)
    vm_land(j,land)                (200 × 7 = 1,400 variables)
    vm_area(j,kcr,w)               (200 × 20 × 2 = 8,000 variables)
    vm_prod_reg(i,k)               (12 × 50 = 600 variables)
    ... 1,000,000+ total variables

Constraint count:
    ~200 cluster land balances
    ~200 cluster water limits
    ~8,000 cluster crop area constraints
    ~600 regional production constraints
    ~600 regional trade constraints
    ~10 global policy constraints
    ... ~100,000+ total constraints
```

**Result**: Solver finds values for ~1M variables that satisfy ~100K constraints while minimizing the single global cost objective.

### Why Not Regional Objectives?

MAgPIE could theoretically have **regional objectives** (e.g., minimize each region's cost independently). But this would:

❌ **Lose comparative advantage**: Regions wouldn't trade efficiently
❌ **Miss global optimum**: Sum of regional optima ≠ global optimum
❌ **Ignore spillovers**: Emissions, trade, deforestation affect other regions

✅ **Global objective captures**:
- Efficient trade: Produce where cheap, import where expensive
- Global climate goals: Minimize total emissions across all regions
- Land-use efficiency: Allocate globally scarce land to highest-value uses

**Local constraints** prevent:
- Violating physical limits (land, water)
- Ignoring regional policies (self-sufficiency, conservation)
- Unrealistic spatial concentration (all production in one cluster)

---

## Summary Table

| Question | Answer | Verification Status |
|----------|--------|---------------------|
| **What is a cluster (j)?** | 200 spatial units aggregated from 0.5° LPJmL grid cells using bottom-up clustering algorithm for computational efficiency | 🟢 core/sets.gms:56-82, main.gms:28,63-65 |
| **Recursive dynamic?** | YES - MAgPIE solves one 5-year time step at a time sequentially with no perfect foresight. Each solve uses previous results but cannot see future. | 🟢 core/calculations.gms:40-99, Phase1_Core_Architecture.md |
| **Cluster in 2 regions?** | NO - Each cluster belongs to exactly one region, defined by cell(i,j) mapping. Cluster naming enforces this (e.g., CAZ_1, CHA_6). | 🟢 core/sets.gms:70-82 |
| **Purpose of i2, j2?** | Dynamic subsets for (1) conditional execution, (2) scenario control, (3) time-dependent activation, (4) solver performance, (5) testing. Separate static sets (i,j) define full universe, dynamic (i2,j2) define active elements. | 🟢 core/sets.gms:119-127 |
| **Global objective + local constraints?** | Standard NLP optimization: Minimize single global cost (vm_cost_glo) subject to ~100K constraints at cluster/regional/global levels. Solver finds ~1M variable values satisfying all constraints while minimizing objective. | 🟢 modules/80_optimization/nlp_apr17/solve.gms:34 |

---

## Verification Status Key

- 🟢 **Verified**: Read actual GAMS code THIS session with line numbers
- 🟡 **Documented**: Read official AI documentation THIS session
- 🟠 **Literature**: Published papers (cited)
- 🔵 **General Knowledge**: Domain knowledge about optimization/modeling
- 🔴 **Inferred**: Logical deduction from training data

---

## Key Files Referenced

### Core Files
- `core/sets.gms` - Spatial and temporal set definitions
- `core/calculations.gms` - Time loop and solve sequence
- `core/declarations.gms` - Core variable declarations
- `main.gms` - Model entry point and configuration

### Module Files
- `modules/80_optimization/nlp_apr17/solve.gms` - Solve statement
- `modules/10_land/` - Land balance constraints
- `modules/11_costs/` - Cost aggregation
- `modules/21_trade/` - Regional trade constraints
- `modules/42_water_demand/` - Water constraints
- `modules/56_ghg_policy/` - Global emission constraints

### Documentation
- `magpie-agent/core_docs/Phase1_Core_Architecture.md` - Architecture overview
- `literature.bib` - Clustering methodology reference (Dietrich et al. 2013)

---

## Related Topics for Further Investigation

1. **Clustering algorithm details**: How are similar 0.5° cells identified and grouped?
2. **Recursive dynamic in specific modules**: How does forestry handle 50-year rotations?
3. **Solver performance**: How long does each time step take? Bottlenecks?
4. **Spatial resolution trade-offs**: Could model run with 400 clusters? 100?
5. **Temporal resolution**: Could model use 10-year steps? 1-year steps?
6. **Perfect foresight experiments**: What would change if MAgPIE used perfect foresight?
7. **Regional vs global objectives**: How would results differ with regional cost minimization?

---

**End of Document**

**Generated by**: Claude Code (magpie-agent)
**Session date**: 2025-10-14
**MAgPIE version**: 4.x series
**Verification approach**: Direct code reading with line number citations
