# GAMS Programming Reference - Phase 1: Fundamentals

**Version**: 1.0 | **Status**: Complete | **Target Audience**: AI agents working with MAgPIE

**Purpose**: Foundation concepts required to read and understand any GAMS code in the MAgPIE model.

**Prerequisites**: General programming knowledge (variables, loops, functions, etc.)

---

## Table of Contents

1. [GAMS Basics & Philosophy](#1-gams-basics--philosophy)
2. [Sets (Indices)](#2-sets-indices)
3. [Parameters (Data)](#3-parameters-data)
4. [Variables (Decision Variables)](#4-variables-decision-variables)
5. [Equations (Constraints)](#5-equations-constraints)
6. [Model & Solve Statements](#6-model--solve-statements)

---

## 1. GAMS Basics & Philosophy

### 1.1 What is GAMS?

**GAMS** (General Algebraic Modeling System) is a high-level modeling language specifically designed for mathematical optimization problems. Unlike general-purpose programming languages, GAMS is declarative rather than imperative—you describe **what** the optimization problem is, not **how** to solve it step-by-step.

**Key characteristics**:
- **Algebraic notation**: Write mathematical formulas naturally
- **Solver-independent**: Same model works with different optimization solvers
- **Data separation**: Clearly separate problem structure from data
- **Automatic differentiation**: Solver computes gradients automatically
- **Domain checking**: Validates set membership and dimensions

### 1.2 Model Execution Flow

Every GAMS model follows a logical progression:

```
1. SETS        → Define indices (regions, products, time periods)
2. DATA        → Load parameters, scalars, tables
3. VARIABLES   → Declare decision variables
4. EQUATIONS   → Define mathematical relationships
5. MODEL       → Group equations into solvable model
6. SOLVE       → Invoke optimization solver
7. DISPLAY     → Show results
```

This order is not just convention—it's enforced by GAMS. You **must** declare entities before using them.

### 1.3 Terminology Mapping

GAMS uses specialized terms for familiar mathematical concepts:

| Mathematical Concept | GAMS Term | Example |
|---------------------|-----------|---------|
| Indices (i, j, k) | **Sets** | i (regions), j (cells), t (time) |
| Given data, constants | **Parameters** | population(i,t), prices(j) |
| Decision variables (x, y) | **Variables** | land allocation, production |
| Constraints | **Equations** | supply ≤ demand, mass balance |
| Objective function | **Equation** (special) | minimize cost, maximize welfare |
| Domain restriction | **Dollar condition** | x(i,j) $ (i ≠ j) |

### 1.4 Declaration-Before-Use Principle

**Critical rule**: Every identifier (set, parameter, variable, equation) must be declared before it can be used.

**Valid ordering**:
```gams
* Declare first
sets i, j;
parameters data(i,j);
variables x(i,j);
equations balance(i);

* Use later
data(i,j) = 100;
balance(i).. sum(j, x(i,j)) =e= data(i,"total");
```

**Invalid ordering**:
```gams
* ERROR: Using before declaring
data(i,j) = 100;        ← ERROR: 'data' not declared yet
parameters data(i,j);   ← Too late!
```

### 1.5 File Structure

GAMS models are stored in `.gms` text files. Large models (like MAgPIE) split code across multiple files:

**MAgPIE structure**:
```
main.gms                    ← Entry point
core/
  sets.gms                  ← Global sets
  declarations.gms          ← Interface variables/parameters
  macros.gms                ← Reusable code templates
modules/
  10_land/
    landmatrix_dec18/
      declarations.gms      ← Module-specific declarations
      equations.gms         ← Equation definitions
      input.gms             ← Load data files
      presolve.gms          ← Pre-processing before solve
      postsolve.gms         ← Post-processing after solve
```

Files are connected using `$include`:
```gams
$include "./core/sets.gms"
$include "./modules/10_land/landmatrix_dec18/declarations.gms"
```

### 1.6 Comments & Documentation

**Line comments**: Start with asterisk `*`
```gams
* This is a comment
sets i regions / USA, EUR, CHN /;  * inline comment after statement
```

**Block comments**: Use `$ontext` / `$offtext`
```gams
$ontext
This is a multi-line comment block.
Everything here is ignored by GAMS compiler.
Useful for temporarily disabling code sections.
$offtext
```

**Roxygen-style comments** (MAgPIE convention): Use `*'` for documentation
```gams
*' @equations
*' This equation defines the total amount of land to be constant over time.

q10_land_area(j2) ..
  sum(land, vm_land(j2,land)) =e= sum(land, pcm_land(j2,land));
```

### 1.7 Semicolons & Formatting

**Semicolons**: All GAMS statements must end with `;`

```gams
sets i / USA, EUR, CHN /;          ← Required
parameters pop(i);                  ← Required
pop("USA") = 330;                   ← Required
```

**Flexible formatting**:
- Whitespace (spaces, tabs, newlines) is ignored
- Multiple statements per line allowed (but not recommended)
- Line breaks within statements allowed

```gams
* All valid:
x = 1;
x = 1; y = 2; z = 3;    * Multiple per line (avoid)
x = a + b
    + c + d             * Statement continues
    + e;                * Until semicolon
```

### 1.8 MAgPIE Example Walkthrough

Let's examine a simple MAgPIE module (Module 10 - Land):

**File**: `modules/10_land/landmatrix_dec18/declarations.gms`
```gams
*** Standard header (license, copyright)

parameters
 pm_land_start(j,land)         Land initialization area (mio. ha)
;

variables
 vm_landdiff                   Aggregated difference in land (mio. ha)
;

positive variables
 vm_land(j,land)               Land area of different types (mio. ha)
;

equations
 q10_land_area(j)              Land transition constraint (mio. ha)
;
```

**What this does**:
1. **Parameters**: `pm_` prefix indicates interface parameter (passed between modules)
2. **Variables**: `vm_` prefix indicates interface variable (optimized across modules)
3. **Positive variables**: Constrained to be ≥ 0 (land area cannot be negative)
4. **Equations**: `q10_` prefix indicates equations belonging to module 10

**File**: `modules/10_land/landmatrix_dec18/equations.gms`
```gams
*' @equations
*' This equation defines the total amount of land to be constant over time.

q10_land_area(j2) ..
  sum(land, vm_land(j2,land)) =e=
  sum(land, pcm_land(j2,land));
```

**What this equation means**:
- Total land in current timestep (left side): `sum(land, vm_land(j2,land))`
- Must equal total land from previous timestep (right side): `sum(land, pcm_land(j2,land))`
- This enforces **land conservation**: land area cannot change (only redistribution allowed)
- `j2` is an active subset of `j` (cells currently being optimized)

---

## 2. Sets (Indices)

### 2.1 What Are Sets?

**Sets** are the fundamental index structure in GAMS, corresponding to mathematical index sets. They define the domain over which parameters, variables, and equations are defined.

**Mathematical notation** → **GAMS notation**:
- Σ_{i ∈ I} x_i → `sum(i, x(i))`
- x_{i,j} ∀ i,j → `x(i,j)` with sets i, j

### 2.2 Basic Set Declaration

**Syntax**:
```gams
Sets
  identifier  text_description  / elements /
  identifier2 text2 / elem1, elem2, elem3 /
;
```

**Example**:
```gams
Sets
  i   regions / USA, EUR, CHN, IND, BRA /
  j   products / wheat, corn, rice /
  t   time periods / y2000, y2010, y2020, y2030 /
;
```

**Key points**:
- Set names (identifiers) should be short (i, j, k common for spatial indices)
- Text descriptions are documentation (printed in outputs)
- Elements are listed in `/` slashes, comma-separated
- Elements are also identifiers (alphanumeric, start with letter)

### 2.3 Sequential Sets

**Asterisk notation**: Generate sequential elements quickly

```gams
Set t time periods / y1995*y2100 /;
* Equivalent to: / y1995, y1996, y1997, ..., y2100 /

Set j cells / CAZ_1*CAZ_5 /;
* Equivalent to: / CAZ_1, CAZ_2, CAZ_3, CAZ_4, CAZ_5 /
```

**MAgPIE example** (from `core/sets.gms`):
```gams
j   number of LPJ cells
  / CAZ_1*CAZ_5,
    CHA_6*CHA_24,
    EUR_25*EUR_36,
    IND_37*IND_48,
    ...
    USA_183*USA_200 /
```

This creates 200 spatial cells (numbered sequentially within regions).

### 2.4 Multi-Dimensional Sets (Mappings)

**Multi-dimensional sets** define relationships between sets:

```gams
Set cell(i,j) mapping regions to cells
  / CAZ . (CAZ_1*CAZ_5)
    CHA . (CHA_6*CHA_24)
    EUR . (EUR_25*EUR_36)
    ...
  /
;
```

**Syntax for mappings**:
- `region . (cells)` means "region contains these cells"
- Dot `.` separates parent from children
- Parentheses group multiple children

**Usage**: Restrict operations to valid combinations
```gams
* Sum only over cells belonging to each region
regional_total(i) = sum(cell(i,j), cell_value(j));
```

### 2.5 Subsets

**Subsets** are sets defined as restrictions of larger sets:

```gams
Set
  kall       all products  / wheat, corn, rice, cattle, milk /
  kcr(kall)  crop products / wheat, corn, rice /
  kli(kall)  livestock     / cattle, milk /
;
```

**Syntax**: `subset_name(parent_set)` declares subset relationship

**Dynamic subsets**: Defined by conditions at runtime
```gams
Set active_regions(i);  * Declare empty
active_regions(i) = yes$(population(i) > 1000000);  * Populate conditionally
```

### 2.6 Aliases

**Aliases** create alternative names for the same set:

```gams
Set i regions / USA, EUR, CHN /;
Alias(i, i2);      * i2 is another name for i
Alias(i, src, dest);  * Multiple aliases

* Use for pairs from same set:
distance(src,dest) = ...;  * All combinations of regions
```

**When needed**:
- Origin-destination pairs (trade flows, migration)
- Time lags: `t` and `t2` for current vs. previous timestep
- Self-joins: Comparing elements within the same set

### 2.7 Set Operations

**Union**: Combine sets
```gams
Set combined / set1, set2, set3 /;
```

**Intersection**: Common elements (via conditions)
```gams
Set intersection(i);
intersection(i)$(set1(i) and set2(i)) = yes;
```

**Difference**: Elements in A but not in B
```gams
Set difference(i);
difference(i)$(set1(i) and not set2(i)) = yes;
```

### 2.8 Special Sets in MAgPIE

**Spatial sets**:
- `i` - Economic regions (12 in standard setup)
- `j` - Grid cells (200 in standard setup: 0.5° resolution clustered)
- `cell(i,j)` - Mapping regions to their cells

**Temporal sets**:
- `t_all` - All possible time periods
- `t_past` - Historical calibration period
- `t` - Active optimization time steps
- `ct(t)` - Current time step (singleton, moves in loop)

**Product sets**:
- `kall` - All products
- `kcr` - Crops
- `kli` - Livestock products
- `kli_rum` - Ruminant livestock (cattle, sheep, goats)
- `kres` - Crop residues

**Land type sets**:
- `land` - All land types
- `land_from, land_to` - For transition matrices
- Specific types: `crop`, `past` (pasture), `forestry`, `primforest`, `secdforest`, `urban`, `other`

**Set definition example** (from `core/sets.gms`):
```gams
sets

  h all superregional economic regions
    / CAZ, CHA, EUR, IND, JPN, LAM, MEA, NEU, OAS, REF, SSA, USA /

  i all economic regions
    / CAZ, CHA, EUR, IND, JPN, LAM, MEA, NEU, OAS, REF, SSA, USA /

  supreg(h,i) mapping of superregions to its regions
    / CAZ . (CAZ)
      CHA . (CHA)
      EUR . (EUR)
      ...
    /
```

### 2.9 Common Set Patterns

**Excluding diagonal**: When you don't want self-transitions
```gams
* Land transitions EXCLUDING staying in same type:
vm_lu_transitions(j,land_from,land_to)$(not sameas(land_from,land_to))
```

**Subset iteration**: Looping over subsets
```gams
loop(kcr(kall),  * Loop only over crop products
  processing(kall) = ...;
);
```

**Regional aggregation**: Summing cells to regions
```gams
regional_value(i) = sum(cell(i,j), cell_value(j));
```

---

## 3. Parameters (Data)

### 3.1 What Are Parameters?

**Parameters** store numeric data—either given inputs, calibrated values, or intermediate calculations. Unlike variables, parameters are **not** optimized by the solver; they are **fixed** values.

**Use cases**:
- Input data from files (prices, yields, population)
- Model calibration factors (efficiency parameters)
- Intermediate calculations (derived quantities)
- Results from previous time steps (recursive dynamics)

### 3.2 Parameter Declaration

**Syntax**:
```gams
Parameters
  name(index1, index2, ...)  text_description
  another_name               description (no indices = scalar)
;
```

**Example**:
```gams
Parameters
  population(i,t)      Population by region and time (million people)
  yield_factor(j,kcr)  Crop yield factor by cell and crop (-)
  base_price           Global base price (USD per ton)
;
```

**Scalars**: Parameters with no indices
```gams
Scalar
  s_interest_rate  Interest rate for capital costs (percent) / 0.05 /
  s_start_year     Simulation start year / 1995 /
;
```

### 3.3 Three Ways to Assign Parameter Values

#### Method 1: List Format

**Direct element-value pairs** in declaration:

```gams
Parameters
  capacity(i) factory capacity
    / USA   350
      EUR   280
      CHN   600
      IND   420 /
;
```

**Key features**:
- Zero default for unspecified elements
- Only non-zero values need entry
- Can combine with declaration

**MAgPIE example**:
```gams
Scalar s70_scavenging_ratio     Scavenging ratio / 0.15 /;
```

#### Method 2: Table Format

**Two-dimensional data matrices**:

```gams
Table distance(i,j) shipping distance in 1000 km
           USA   EUR   CHN
  USA       0    7.5   10.2
  EUR      7.5    0    8.1
  CHN     10.2   8.1    0
;
```

**Key features**:
- Natural representation of matrices
- Row headers = first index
- Column headers = second index
- Missing values = zero
- Only works for 2D data

**MAgPIE example** (input files use CSV, loaded via $load):
```gams
Table f10_land_initial(j,land) initial land distribution
$ondelim
$include "./input/f10_land_initial.csv"
$offdelim
;
```

#### Method 3: Direct Assignment

**Computed values** using formulas:

```gams
Parameters cost(i,j);
* Declare first, assign later
cost(i,j) = distance(i,j) * freight_rate * (1 + tariff(i,j));
```

**Key features**:
- Requires separate declaration
- Can use complex expressions
- Can use dollar conditions for filtering
- Can reference other parameters, sets, functions

**MAgPIE example** (from Module 70, `presolve.gms`):
```gams
p70_cattle_stock_proxy(t,i) = im_pop(t,i)*pm_kcal_pc_initial(t,i,"livst_rum")
                              /i70_livestock_productivity(t,i,"sys_beef");
```

### 3.4 Parameter Naming Conventions in MAgPIE

**Prefixes indicate scope and source**:

| Prefix | Meaning | Example | Scope |
|--------|---------|---------|-------|
| `pm_` | **Interface parameter** | `pm_land_start(j,land)` | Shared between modules |
| `p{N}_` | **Module internal** | `p70_cattle_stock_proxy(t,i)` | Module N only |
| `fm_` | **Input from file** | `fm_croparea(t,j,kcr)` | Loaded from input files |
| `f{N}_` | **Module input file** | `f10_land_initial(j,land)` | Module N input data |
| `i{N}_` | **Module input** | `i70_livestock_productivity(t,i,sys)` | Module N parameters |
| `s_` | **Scalar** | `s_interest_rate` | Global scalar value |
| `s{N}_` | **Module scalar** | `s70_scavenging_ratio` | Module N scalar |
| `pcm_` | **Previous iteration** | `pcm_land(j,land)` | Values from last solve |

**Naming rules**:
- Descriptive names (not x, y, z)
- Units in text description: `(mio. ha)`, `(USD per ton)`, `(-)`
- Lowercase with underscores: `cattle_stock_proxy`

### 3.5 Zero Default

**Important**: Unspecified parameter values default to **zero**.

```gams
Parameter price(i);
price("USA") = 100;
price("EUR") = 150;
* price("CHN") is ZERO (not undefined, not missing)

total = sum(i, price(i));  * Includes zero for CHN
```

**Implication**: Don't need to initialize every element
```gams
* Only set non-zero values:
calibration_factor(i) = 1.0;  * Default for all i
calibration_factor("special_region") = 1.5;  * Override specific
```

### 3.6 Multi-Dimensional Parameters

Parameters can have many indices:

```gams
Parameter carbon_density(t,j,land,ag_pools,potnatveg)
  Carbon density by time, cell, land type, pool, vegetation type
  (ton C per ha);
```

**Access pattern**:
```gams
cell_carbon = carbon_density("y2020","CAZ_1","primforest","vegc","NatGr");
```

**Partial summing**: Aggregate over some dimensions
```gams
* Total carbon across all pools in a cell:
total_carbon(t,j,land) = sum(ag_pools, carbon_density(t,j,land,ag_pools));
```

### 3.7 Time-Dependent Parameters

**Common pattern**: Parameters that change over time

```gams
Parameters
  pm_population(t,i)     Population trajectory (million)
  pm_gdp(t,i)            GDP trajectory (billion USD)
  pm_carbon_price(t,i)   Carbon price over time (USD per ton CO2)
;
```

**Filling time series** (linear interpolation macro):
```gams
* MAgPIE macro for time interpolation:
m_linear_time_interpol(
  parameter_name,
  start_year, target_year,
  start_value, target_value
);
```

### 3.8 Parameter Calculations: Common Patterns

**Conditional assignment** (dollar on left):
```gams
* Only assign if condition true, else keep previous value:
rho(i) $ (sig(i) <> 0) = (1./sig(i)) - 1;
```

**Conditional value** (dollar on right):
```gams
* Always assign: value if true, zero if false:
adjustment(i) = base_value * (multiplier(i) $ (multiplier(i) > 1));
```

**Lower/upper bounds**:
```gams
* Enforce minimum value:
p70_cattle_stock_proxy(t,i)$(p70_cattle_stock_proxy(t,i) < 0.2*p70_cattle_stock_proxy("y1995",i))
  = 0.2*p70_cattle_stock_proxy("y1995",i);
```

**Weighted average**:
```gams
* MAgPIE macro with zero protection:
$macro m_weightedmean(x,w,s) (sum(s,x*w)/sum(s,w))$(sum(s,w)>0) + 0$(sum(s,w)<=0);

average_yield = m_weightedmean(yield(j), area(j), j);
```

**Growth rates**:
```gams
growth_rate(t,i) = (value(t,i) - value(t-1,i)) / value(t-1,i);
```

### 3.9 MAgPIE Parameter Examples

**From Module 70** (`presolve.gms`):

```gams
*' The parameter `p70_cattle_feed_pc_proxy` is a proxy for regional daily per capita
*' feed demand for pasture biomass driven by demand for beef and dairy products,
*' which is later used for weighted aggregation.

p70_cattle_feed_pc_proxy(t,i,kli_rd) =
  pm_kcal_pc_initial(t,i,kli_rd) * im_feed_baskets(t,i,kli_rd,"pasture")
  / (fm_nutrition_attributes(t,kli_rd,"kcal") * 10**6);
```

**Explanation**:
- Multi-line formulas allowed (no semicolon until end)
- Multiplication across multiple parameters
- Division for normalization
- Scientific notation: `10**6` (one million)
- Roxygen comment `*'` documents purpose

---

## 4. Variables (Decision Variables)

### 4.1 What Are Variables?

**Variables** are the quantities that the optimization solver determines. They represent the **decisions** or **outcomes** the model optimizes.

**Key distinction**:
- **Parameters**: Fixed values (inputs, calibrations)
- **Variables**: Optimized values (solver determines)

**Example**:
- *Given* demand (parameter), available land (parameter)
- *Decide* how much to plant (variable), what to produce (variable)

### 4.2 Variable Declaration

**Syntax**:
```gams
Variables
  name(indices)  description
;

Positive Variables
  name2(indices)  description (non-negative)
;

Binary Variables
  name3(indices)  description (0 or 1)
;
```

**Example**:
```gams
Variables
  z                  total cost (objective function)
  vm_emissions(i,t)  GHG emissions by region and time (Mt CO2eq)
;

Positive Variables
  vm_land(j,land)             land allocation by cell and type (mio. ha)
  vm_prod(j,kcr)              crop production by cell (Mt)
;
```

### 4.3 Variable Types

GAMS provides several variable type declarations that constrain the feasible domain:

#### Free Variables (default)
**No bounds**: Can take any value (−∞, +∞)

```gams
Variable
  vm_cost_glo    global total costs (can be negative or positive)
;
```

**When to use**: Objectives, net quantities (revenues minus costs), emissions balances

#### Positive Variables
**Lower bound = 0**: Can only be non-negative [0, +∞)

```gams
Positive Variable
  vm_land(j,land)    land area (cannot be negative)
  vm_prod(j,kcr)     production (cannot be negative)
;
```

**When to use**: Physical quantities (area, mass, volume), costs, resources

#### Negative Variables
**Upper bound = 0**: Can only be non-positive (−∞, 0]

```gams
Negative Variable
  vm_deficit(i,t)    resource deficit (negative = shortage)
;
```

**When to use**: Deficits, debts (rarely used; usually just use free or positive with sign conventions)

#### Binary Variables
**Only 0 or 1**: Discrete choice variables

```gams
Binary Variable
  vm_build(i,plant_type)    whether to build plant (0=no, 1=yes)
;
```

**When to use**: Yes/no decisions, technology selection, on/off states

**Note**: Binary variables invoke **mixed-integer programming (MIP)**, which is much slower than continuous optimization. MAgPIE uses very few binary variables.

#### Integer Variables
**Only integer values**: {..., -2, -1, 0, 1, 2, ...}

```gams
Integer Variable
  vm_number_of_plants(i)    how many plants to build
;
```

**When to use**: Counting discrete units (rarely used in MAgPIE)

### 4.4 Variable Attributes (Database Fields)

Every variable has **five attributes** (database fields):

| Attribute | Name | Meaning | Set When |
|-----------|------|---------|----------|
| `.l` | **Level** | Variable's value | After solve (solution) |
| `.m` | **Marginal** | Shadow price (dual value) | After solve (solution) |
| `.lo` | **Lower bound** | Minimum allowed value | Before solve (bounds) |
| `.up` | **Upper bound** | Maximum allowed value | Before solve (bounds) |
| `.fx` | **Fixed value** | Fix to specific value | Before solve (set .lo = .up) |

#### Setting Bounds (Before Solve)

**Lower bound**:
```gams
vm_land.lo(j,land) = 0;  * Non-negative (redundant for Positive Variable)
vm_prod.lo(j,"wheat") = min_production(j);  * Minimum production requirement
```

**Upper bound**:
```gams
vm_land.up(j,land) = pm_cell_area(j);  * Cannot exceed total cell area
vm_emissions.up(i,t) = emission_cap(i,t);  * Emission cap
```

**Unbounded** (remove default bounds):
```gams
vm_net_balance.up(i) = Inf;   * No upper limit
vm_net_balance.lo(i) = -Inf;  * No lower limit
```

**Fixing** (set both bounds equal):
```gams
vm_land.fx(j,"urban") = pm_urban_area(j);  * Urban area fixed (not optimized)
* Equivalent to:
* vm_land.lo(j,"urban") = pm_urban_area(j);
* vm_land.up(j,"urban") = pm_urban_area(j);
```

**MAgPIE example** (from Module 70, `presolve.gms`):
```gams
*' Fix feed balance flow based on input data:
vm_feed_balanceflow.fx(i,kap,kall) = fm_feed_balanceflow(t,i,kap,kall);

*' Allow ruminant pasture to vary freely:
vm_feed_balanceflow.up(i,kli_rum,"pasture") = Inf;
vm_feed_balanceflow.lo(i,kli_rum,"pasture") = -Inf;
```

#### Retrieving Results (After Solve)

**Level** (.l): The optimized value
```gams
* After solve:
display vm_land.l;  * Show all land allocations

* Store in parameter for further use:
parameter p_land_result(j,land);
p_land_result(j,land) = vm_land.l(j,land);
```

**Marginal** (.m): Shadow price (sensitivity)
```gams
* After solve:
display vm_land.m;  * How much objective would improve if bound relaxed

* Interpretation:
* If vm_land.m(j,"cropland") = 1500
* → Relaxing the upper bound on cropland by 1 ha would reduce cost by 1500 USD
```

**Common pattern** - Carry variable values to next time step:
```gams
* In postsolve.gms (after each timestep solve):
pcm_land(j,land) = vm_land.l(j,land);

* In next timestep's presolve.gms:
* Use pcm_land (previous land) to enforce constraints or set bounds
```

### 4.5 Variable Initialization (Warm Starts)

**Purpose**: Give solver a good starting point for faster convergence

**Setting initial values**:
```gams
* Before solve:
vm_land.l(j,"cropland") = pm_land_initial(j,"cropland");  * Start from historical
vm_prod.l(j,kcr) = historical_production(j,kcr);
```

**Benefits**:
- Faster solve times (solver starts near optimum)
- Better convergence for nonlinear models
- Useful in recursive dynamic models (use previous timestep as starting point)

**MAgPIE approach**: Variables from timestep *t−1* become initial guess for timestep *t*

### 4.6 Variable Naming Conventions in MAgPIE

| Prefix | Meaning | Example | Scope |
|--------|---------|---------|-------|
| `vm_` | **Interface variable** | `vm_land(j,land)` | Optimized across modules, shared |
| `v{N}_` | **Module internal variable** | `v70_feed(i,kap,kall)` | Module N only, not shared |

**Naming rules**:
- Descriptive names: `vm_landexpansion`, not `vm_x1`
- Units in description: `(mio. ha)`, `(Mt)`, `(billion USD)`
- Lowercase with underscores

### 4.7 Common Variable Patterns in MAgPIE

#### Land Variables
```gams
Positive Variables
  vm_land(j,land)                      Land area by type (mio. ha)
  vm_landexpansion(j,land)             Land expansion (mio. ha)
  vm_landreduction(j,land)             Land reduction (mio. ha)
  vm_lu_transitions(j,land_from,land_to) Land-use transitions (mio. ha)
;
```

#### Production Variables
```gams
Positive Variables
  vm_prod(j,kcr)           Crop production by cell (Mt)
  vm_prod_reg(i,kcr)       Crop production by region (Mt)
  vm_supply(i,kall)        Food supply by product (Mt)
;
```

#### Cost Variables
```gams
Variable
  vm_cost_glo              Global total costs (billion USD per year)
;

Positive Variables
  vm_cost_land_transition(j)          Land transition costs (mio. USD per yr)
  vm_cost_prod(i,kall)                Production costs (mio. USD per yr)
  vm_cost_trade(i,kall)               Trade costs (mio. USD per yr)
;
```

**Hierarchical structure**: Module costs sum to global cost
```gams
vm_cost_glo = sum(i, vm_cost_land_transition(i)
                   + vm_cost_prod(i)
                   + vm_cost_trade(i)
                   + ...);
```

### 4.8 Equation Reference Variables

Variables appear in equations to define optimization problem:

```gams
* Declaration:
Positive Variable vm_land(j,land);
Equation q10_land_area(j);

* Equation definition:
q10_land_area(j2) ..
  sum(land, vm_land(j2,land)) =e= sum(land, pcm_land(j2,land));
  ^^^^^^^^^^^^^^^^
  Variable is optimized to satisfy this constraint
```

**Key point**: Variables in equations are **symbolic**—you don't assign them values manually. The solver determines their values to satisfy all equations while optimizing the objective.

---

## 5. Equations (Constraints)

### 5.1 What Are Equations?

**Equations** define mathematical relationships that must be satisfied by the optimized variables. In optimization terminology:
- **Constraints**: Restrictions on feasible solutions
- **Objective**: Special equation to minimize/maximize

**Structure**:
```
Left-Hand Side  RELATION  Right-Hand Side
     (LHS)        (rel)        (RHS)
```

Where:
- LHS = expression with variables
- RHS = expression with variables and/or parameters
- RELATION = equality or inequality

### 5.2 Two-Step Process: Declaration and Definition

**Critical**: Equations require **two separate statements**:

**Step 1 - Declaration**: Announce the equation exists
```gams
Equations
  q10_land_area(j)      Land area conservation constraint
  q10_cost(j)           Land transition cost calculation
  q10_landdiff          Global land difference aggregation
;
```

**Step 2 - Definition**: Specify the mathematical formula
```gams
q10_land_area(j2) ..
  sum(land, vm_land(j2,land)) =e= sum(land, pcm_land(j2,land));

q10_cost(j2) ..
  vm_cost_land_transition(j2) =e=
    sum(land, vm_landexpansion(j2,land) + vm_landreduction(j2,land)) * 1;

q10_landdiff ..
  vm_landdiff =e=
    sum((j2,land), vm_landexpansion(j2,land) + vm_landreduction(j2,land))
    + vm_landdiff_natveg
    + vm_landdiff_forestry;
```

**Why two steps?**
- Declaration establishes scope and indices (used for validation)
- Definition can reference other equations in its domain
- Allows forward references in complex models

### 5.3 Equation Definition Syntax

**General form**:
```gams
equation_name(indices)$(condition) ..
  Left_Hand_Side  RELATIONAL_OPERATOR  Right_Hand_Side ;
```

**Components**:
1. **Name**: Must match declaration
2. **Indices**: Domain restriction (often subset like `j2` instead of `j`)
3. **Dollar condition** (optional): Further domain filtering
4. **Double dot** `..`: Separates header from definition
5. **Relational operator**: `=e=`, `=l=`, or `=g=`
6. **Semicolon**: Ends definition

### 5.4 Relational Operators

GAMS provides three types of constraints:

| Operator | Mathematical Symbol | Meaning | Name |
|----------|-------------------|---------|------|
| `=e=` | = | **Equal to** | Equality constraint |
| `=l=` | ≤ | **Less than or equal to** | Inequality constraint (≤) |
| `=g=` | ≥ | **Greater than or equal to** | Inequality constraint (≥) |

**Examples**:

**Equality** (balance, conservation):
```gams
* Land conservation: total land must equal previous total
q10_land_area(j2) ..
  sum(land, vm_land(j2,land)) =e= sum(land, pcm_land(j2,land));
```

**Less-than-or-equal** (capacity, resource limits):
```gams
* Production cannot exceed capacity:
q_capacity(i) ..
  vm_prod(i) =l= pm_capacity(i);
```

**Greater-than-or-equal** (demand satisfaction, minimum requirements):
```gams
* Production must meet demand:
q_demand(i) ..
  vm_prod(i) =g= pm_demand(i);
```

### 5.5 Domain Restriction in Equations

**Full set vs subset**:
```gams
* Declared over all j:
Equation q_balance(j);

* Defined over active subset j2:
q_balance(j2) ..
  expression;
```

**Why subsets?**
- `j2` typically contains only **spatially active cells** (not all 200 cells)
- Reduces problem size (computational efficiency)
- Matches solver variables' active domain

**MAgPIE pattern**: Most equations use `j2`, `i2`, etc. (active subsets) rather than full sets `j`, `i`

### 5.6 Summation in Equations

**Single sum**:
```gams
q_total(i) ..
  vm_total(i) =e= sum(j, vm_component(i,j));
  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  Total equals sum of components
```

**Multiple sums** (nested):
```gams
q_global_total ..
  vm_global_total =e= sum((i,j,k), vm_value(i,j,k));
  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  Sum over all three indices
```

**Conditional sum** (with dollar condition):
```gams
q_cropland_total(i) ..
  vm_cropland_total(i) =e= sum(kcr(kall), vm_prod(i,kall));
  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  Sum only over crops, not all products
```

**Sum with exclusion**:
```gams
q_off_diagonal(i,j) ..
  vm_trade_flow(i,j)$(not sameas(i,j)) =e= expression;
  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  Exclude i=j (no self-trade)
```

### 5.7 Multi-Line Equations

Long equations can span multiple lines:

```gams
q_complex_equation(i) ..
  vm_result(i) =e=
    term1(i)
    + term2(i) * factor
    - sum(j, term3(i,j))
    + (term4(i) / denominator(i))$(denominator(i) > 0)
    + sum((k,t), term5(i,k,t) * weight(t));
```

**Formatting**:
- No semicolon until final line
- Indent continuations for readability
- Align operators vertically (optional but helpful)

### 5.8 Dollar Conditions in Equations

**Two uses**:

#### 1. Domain restriction (in equation header)
```gams
q_equation(i,j)$(condition) ..
  LHS =e= RHS;
```

Equation **only generated** for (i,j) where condition is true.

**Example**:
```gams
* Only generate equation for cells with cropland:
q_crop_yield(j)$(pm_cropland_area(j) > 0) ..
  vm_prod(j) =e= vm_area(j) * pm_yield(j);
```

#### 2. Term filtering (in equation body)
```gams
q_equation(i) ..
  LHS =e= term1 + (term2 $ condition);
```

Term **included only if** condition is true (otherwise treated as zero).

**Example**:
```gams
* Export term only for tradable goods:
q_balance(i,k) ..
  vm_production(i,k) =e=
    vm_domestic_use(i,k)
    + (vm_exports(i,k) $ tradable(k));  ← zero if not tradable
```

**MAgPIE example** (Module 10, excluding diagonal):
```gams
q10_landexpansion(j2,land_to) ..
  vm_landexpansion(j2,land_to) =e=
    sum(land_from$(not sameas(land_from,land_to)),
        vm_lu_transitions(j2,land_from,land_to));
  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  Sum excludes land_from = land_to (no expansion from staying same type)
```

### 5.9 Equation Naming Conventions in MAgPIE

| Prefix | Meaning | Example | Scope |
|--------|---------|---------|-------|
| `q{N}_` | **Module equation** | `q10_land_area(j)` | Module N internal |
| `q_` | **Core equation** (rare) | `q_objective` | Cross-module |

**Naming rules**:
- Descriptive: `q10_land_area`, not `q10_eq1`
- Lowercase with underscores
- Module number prefix for traceability

### 5.10 Common Equation Patterns in MAgPIE

#### Conservation Laws (Equality)
```gams
*' Land area conservation (Module 10):
q10_land_area(j2) ..
  sum(land, vm_land(j2,land)) =e=
  sum(land, pcm_land(j2,land));
```
Total land this timestep = total land previous timestep

#### Mass Balance (Equality)
```gams
*' Food balance (Module 16):
q16_food_supply(i,kall) ..
  vm_supply(i,kall) =e=
    vm_prod_reg(i,kall)
    + vm_trade_import(i,kall)
    - vm_trade_export(i,kall)
    - vm_seed_demand(i,kall)
    - vm_processing(i,kall);
```
Supply = Production + Imports − Exports − Seed − Processing

#### Resource Constraints (Inequality ≤)
```gams
*' Water availability (Module 43):
q43_water_availability(i) ..
  sum(water_use, vm_water_withdrawal(i,water_use)) =l=
  pm_water_available(i);
```
Total water use ≤ available water

#### Demand Satisfaction (Inequality ≥)
```gams
*' Minimum food demand (Module 15):
q15_food_demand(i,kall) ..
  vm_supply(i,kall) =g=
  pm_demand_min(i,kall);
```
Food supply ≥ minimum required demand

#### Cost Aggregation (Equality)
```gams
*' Module cost calculation:
q10_cost(j2) ..
  vm_cost_land_transition(j2) =e=
    sum(land, vm_landexpansion(j2,land) + vm_landreduction(j2,land)) * 1;
```
Module cost = sum of cost components

#### Transition Matrix (Equality)
```gams
*' Land transitions TO each type:
q10_transition_to(j2,land_to) ..
  sum(land_from, vm_lu_transitions(j2,land_from,land_to)) =e=
  vm_land(j2,land_to);

*' Land transitions FROM each type:
q10_transition_from(j2,land_from) ..
  sum(land_to, vm_lu_transitions(j2,land_from,land_to)) =e=
  pcm_land(j2,land_from);
```
Ensures transitions account for all land changes

### 5.11 MAgPIE Documentation Comments

**Roxygen-style** (`*'`) documents equations:

```gams
*' @equations

*' This equation defines the total amount of land to be constant over time.

q10_land_area(j2) ..
  sum(land, vm_land(j2,land)) =e=
  sum(land, pcm_land(j2,land));

*' The following two equations describe the land transition matrix.

q10_transition_to(j2,land_to) ..
  ...
```

**Benefits**:
- Explains purpose and interpretation
- Auto-extracted for documentation generation
- Improves code readability

---

## 6. Model & Solve Statements

### 6.1 What Are Model and Solve?

Once you've declared sets, parameters, variables, and equations, you need to:
1. **Model**: Group equations into a solvable optimization problem
2. **Solve**: Invoke the solver to find optimal variable values

### 6.2 Model Declaration

**Syntax**:
```gams
Model model_name / equation_list /;
```

**Include all equations**:
```gams
Model magpie / all /;
```

**Include specific equations**:
```gams
Model transport / cost_eq, supply_eq, demand_eq /;
```

**Exclude specific equations** (use `-`):
```gams
Model partial / all - excluded_eq1 - excluded_eq2 /;
```

**MAgPIE structure**: One main model including all module equations
```gams
Model magpie / all /;
```

### 6.3 Solve Statement

**Syntax**:
```gams
Solve model_name using solver_type minimizing|maximizing objective_variable ;
```

**Example**:
```gams
Solve magpie using nlp minimizing vm_cost_glo ;
```

**Components**:
1. **Model name**: Previously declared model
2. **Solver type**: Algorithm to use (lp, nlp, mip, etc.)
3. **Direction**: `minimizing` (reduce objective) or `maximizing` (increase objective)
4. **Objective variable**: The variable to optimize (must be scalar, i.e., no indices)

### 6.4 Solver Types

GAMS supports many solver types for different problem classes:

| Solver Type | Problem Class | Example Use |
|-------------|--------------|-------------|
| `lp` | **Linear Programming** | Linear objective, linear constraints |
| `nlp` | **Nonlinear Programming** | Nonlinear objective or constraints, continuous |
| `mip` | **Mixed Integer Programming** | Integer or binary variables, linear |
| `minlp` | **Mixed Integer Nonlinear** | Integer/binary + nonlinear |
| `qcp` | **Quadratic Constrained** | Quadratic terms in constraints |
| `mcp` | **Mixed Complementarity** | Complementarity conditions (KKT) |
| `cns` | **Constrained Nonlinear System** | Solve system of equations (no optimization) |

**MAgPIE uses**: `nlp` (nonlinear programming)
- Continuous variables (no integers)
- Nonlinear growth functions (exponential, power)
- Large-scale (thousands of variables and constraints)

### 6.5 Optimization Direction

**Minimizing** (cost minimization, common in MAgPIE):
```gams
Solve magpie using nlp minimizing vm_cost_glo ;
```

**Maximizing** (welfare maximization, revenue, etc.):
```gams
Solve welfare_model using nlp maximizing vm_social_welfare ;
```

**MAgPIE objective**: Minimize global total costs
- Production costs
- Trade costs
- Land conversion costs
- Factor costs (labor, capital)
- Greenhouse gas emission costs (if carbon price active)

### 6.6 Solution Status

After solving, GAMS sets status variables:

**Model status** (`model_name.modelstat`):
- `1` = Optimal solution found
- `2` = Locally optimal (for nonlinear problems)
- `3` = Unbounded (no finite optimum)
- `4` = Infeasible (no solution satisfying all constraints)
- `5` = Locally infeasible
- (Many other codes for various conditions)

**Solver status** (`model_name.solvestat`):
- `1` = Normal completion
- `2` = Iteration interrupt (iteration limit reached)
- `3` = Resource interrupt (time or memory limit)
- `4` = Terminated by solver
- (Others for errors, licensing, etc.)

**Checking solution**:
```gams
display magpie.modelstat, magpie.solvestat;

if (magpie.modelstat > 2,
  abort "Model not solved to optimality!";
);
```

### 6.7 Iterative Solving (MAgPIE Time Loop)

**MAgPIE structure**: Solve repeatedly for each time period

```gams
loop(t,
  * Set current time step
  ct(t) = yes;

  * PRESOLVE: Prepare data, set bounds
  $include "./modules/10_land/presolve.gms"
  $include "./modules/14_yields/presolve.gms"
  ...

  * SOLVE: Optimize current time step
  Solve magpie using nlp minimizing vm_cost_glo;

  * POSTSOLVE: Process results
  $include "./modules/10_land/postsolve.gms"
  $include "./modules/14_yields/postsolve.gms"
  ...

  * Clear current time step
  ct(t) = no;
);
```

**Key points**:
- Each timestep is solved independently (recursive dynamic)
- Results from timestep *t* inform constraints in timestep *t+1*
- Presolve sets up problem (bounds, initial values)
- Postsolve stores results, updates parameters for next step

### 6.8 Accessing Solution Values

**After solve**, retrieve results from variable attributes:

**Level** (.l): Optimized value
```gams
* Display solution:
display vm_land.l, vm_prod.l, vm_cost_glo.l;

* Store in parameters:
parameter p_land_result(t,j,land);
p_land_result(t,j,land) = vm_land.l(j,land);
```

**Marginal** (.m): Shadow price (dual value)
```gams
* Display marginals (sensitivity to bound changes):
display vm_land.m;

* Identify binding constraints:
parameter p_binding_constraint(j,land);
p_binding_constraint(j,land)$(abs(vm_land.m(j,land)) > 0.01) = 1;
```

**Equation levels and marginals**:
```gams
* Check if constraint is binding:
display q10_land_area.l;   * LHS value at solution
display q10_land_area.m;   * Shadow price of constraint
```

### 6.9 Solver Options

**Setting solver options** (advanced):

```gams
* Option file number:
option nlp = conopt;        * Use CONOPT solver for NLP
magpie.optfile = 1;         * Use option file "conopt.opt"

* Solver time limit:
magpie.reslim = 36000;      * 10 hours max

* Iteration limit:
magpie.iterlim = 1000000;

* Optimality tolerance:
option optcr = 0.01;        * 1% optimality gap acceptable
```

**MAgPIE typically uses**:
- CONOPT for NLP (nonlinear programming)
- Tight tolerances for accuracy
- Long time limits for large problems

### 6.10 Model Validation

**Common checks after solve**:

```gams
* 1. Check solve status:
if (magpie.modelstat > 2,
  display "Warning: Model not optimal", magpie.modelstat;
);

* 2. Verify conservation laws:
parameter p_land_balance(j);
p_land_balance(j) = sum(land, vm_land.l(j,land)) - sum(land, pcm_land(j,land));
display "Land balance (should be ~0):", p_land_balance;

* 3. Check for unrealistic values:
if (smax((j,land), vm_land.l(j,land)) > 1000,
  abort "Unrealistic land area detected!";
);

* 4. Display key results:
display vm_cost_glo.l, vm_prod.l, vm_land.l;
```

---

## Summary

**Phase 1 covered the six fundamental GAMS concepts**:

1. **GAMS Basics**: Declarative language, execution flow, syntax rules
2. **Sets**: Indices defining domains (spatial, temporal, product)
3. **Parameters**: Fixed data (inputs, calibrations, intermediate calculations)
4. **Variables**: Optimized quantities (decision variables)
5. **Equations**: Mathematical relationships (constraints + objective)
6. **Model & Solve**: Grouping equations and invoking solver

**With these fundamentals, you can**:
- Read and understand any GAMS code structure
- Identify what is given (parameters) vs. optimized (variables)
- Understand constraint definitions (equations)
- Follow optimization problem setup (model & solve)

**Next phases will cover**:
- **Phase 2**: Control structures (if, loops, dollar conditions)
- **Phase 3**: Advanced features (macros, attributes, time indexing)
- **Phase 4**: Functions and operations (mathematical, logical, set functions)
- **Phase 5**: MAgPIE-specific patterns (module structure, interface variables)
- **Phase 6**: Best practices (scaling, debugging, performance)

---

## Quick Reference: GAMS Syntax at a Glance

```gams
*** SETS (indices) ***
Sets
  i   regions / USA, EUR, CHN /
  j   products / wheat, corn, rice /
  t   time / y2000*y2030 /
;

*** PARAMETERS (data) ***
Parameters
  price(i,j)     product prices
  demand(i,j,t)  demand trajectory
;
price(i,j) = 100 + uniform(0,50);

*** VARIABLES (optimize these) ***
Variables
  z              objective (total cost)
;
Positive Variables
  x(i,j,t)       production quantities
;

*** EQUATIONS (constraints) ***
Equations
  obj            objective function
  balance(i,j,t) supply-demand balance
;

obj..
  z =e= sum((i,j,t), price(i,j) * x(i,j,t));

balance(i,j,t)..
  x(i,j,t) =g= demand(i,j,t);

*** MODEL & SOLVE ***
Model mymodel / all /;
Solve mymodel using lp minimizing z;

*** DISPLAY RESULTS ***
display x.l, x.m, z.l;
```

---

**End of Phase 1: GAMS Fundamentals**
