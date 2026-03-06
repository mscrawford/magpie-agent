# GAMS Programming Reference - Documentation Plan

**Purpose**: Comprehensive reference for AI agents to understand and work with GAMS code in the MAgPIE model

**Target Audience**: AI agents with general programming knowledge but limited GAMS experience

**Sources**:
- Official GAMS Documentation (gams.com/latest/docs)
- MAgPIE codebase patterns (analyzed from modules/ and core/)
- Best practices from "Good Optimization Modeling Practices with GAMS"

---

## Documentation Structure Overview

### Phase 1: GAMS Fundamentals (Foundation)
**Estimated**: ~8,000 words | **Priority**: CRITICAL

Core concepts required to read any GAMS code:
1. **GAMS Basics & Philosophy**
2. **Sets (Indices)**
3. **Parameters (Data)**
4. **Variables (Decision Variables)**
5. **Equations (Constraints)**
6. **Model & Solve Statements**

### Phase 2: GAMS Control Structures (Essential)
**Estimated**: ~6,000 words | **Priority**: HIGH

Flow control and programming logic:
1. **Dollar Conditions ($)**
2. **Conditional Execution (if-elseif-else)**
3. **Loops (loop, while, for, repeat)**
4. **Break & Continue**
5. **Abort Statements**

### Phase 3: GAMS Advanced Features (Important)
**Estimated**: ~7,000 words | **Priority**: HIGH

Advanced patterns used extensively in MAgPIE:
1. **Macros ($macro)**
2. **Dollar Control Options**
3. **Variable Attributes (.l, .m, .lo, .up, .fx)**
4. **Set Operations & Functions**
5. **Time Indexing Patterns**

### Phase 4: GAMS Functions & Operations (Reference)
**Estimated**: ~5,000 words | **Priority**: MEDIUM

Mathematical and logical operations:
1. **Mathematical Functions**
2. **Logical Operators & Expressions**
3. **Set Functions (ord, card, sameas, etc.)**
4. **Aggregation (sum, prod, smin, smax)**
5. **Conditional Assignments**

### Phase 5: MAgPIE-Specific Patterns (Applied)
**Estimated**: ~8,000 words | **Priority**: HIGH

Real-world patterns from MAgPIE codebase:
1. **Module Structure Patterns**
2. **Interface Variable Patterns**
3. **Time Step Management**
4. **Calibration & Initialization**
5. **Common Macros in MAgPIE**

### Phase 6: Optimization Modeling Best Practices (Guidance)
**Estimated**: ~4,000 words | **Priority**: MEDIUM

How to write good GAMS code:
1. **Model Scaling & Units**
2. **Numerical Stability**
3. **Performance Optimization**
4. **Debugging Strategies**
5. **Common Pitfalls & Solutions**

---

## Detailed Content Breakdown

### Phase 1: GAMS Fundamentals

#### 1.1 GAMS Basics & Philosophy (800 words)
- **What is GAMS**: Algebraic modeling language for optimization
- **Model execution flow**: Sets → Data → Variables → Equations → Solve → Display
- **Terminology mapping**: Mathematical concepts ↔ GAMS entities
- **Declaration-before-use principle**
- **File structure**: .gms files, code organization
- **Comments**: `*` for line comments, `$ontext/$offtext` for blocks
- **Semicolons**: Statement terminators
- **MAgPIE example**: Brief tour of a simple module

#### 1.2 Sets (Indices) (1,200 words)
- **Purpose**: Define index domains for parameters, variables, equations
- **Declaration syntax**:
  ```gams
  Sets
    i   regions / CAZ, CHA, EUR /
    j   cells / CAZ_1*CAZ_5 /
  ;
  ```
- **Subset declarations**: Restricting to subsets
- **Multi-dimensional sets**: Set mappings like `cell(i,j)`
- **Dynamic sets**: Sets defined by conditions
- **Aliases**: Alternative names for same set
- **Set operations**: Union, intersection, difference
- **Special sets in MAgPIE**:
  - Spatial: i (regions), j (cells)
  - Temporal: t (time), t_past, t_all
  - Products: kall, kcr, kli
  - Land: land, land_from, land_to
- **Examples from MAgPIE**: core/sets.gms patterns

#### 1.3 Parameters (Data) (1,200 words)
- **Purpose**: Store given data, calibrated values, intermediate calculations
- **Declaration**: `parameters p_name(i,j) Description ;`
- **Three assignment methods**:
  1. **List format**: `p(i) / seattle 350, san-diego 600 /`
  2. **Table format**: Two-dimensional data matrices
  3. **Direct assignment**: `p(i,j) = expression ;`
- **Zero default**: Unspecified values are zero
- **Parameter vs Scalar**: Scalar has no indices
- **Time-dependent parameters**: pm_ prefix convention in MAgPIE
- **Input parameters**: f_ prefix from input files
- **Module parameters**: p{module}_ internal calculations
- **Examples from MAgPIE**:
  - `pm_land_start(j,land)` - initialization
  - `p70_cattle_stock_proxy(t,i)` - intermediate calculation
  - `fm_nutrition_attributes(t,kall,nutrients)` - input data

#### 1.4 Variables (Decision Variables) (1,400 words)
- **Purpose**: Quantities to be optimized by solver
- **Declaration**: `variables vm_name(i,j) Description ;`
- **Variable types**:
  - `free` - unrestricted (default)
  - `positive` - non-negative (≥ 0)
  - `negative` - non-positive (≤ 0)
  - `binary` - 0 or 1 only
  - `integer` - integer values only
- **Variable attributes** (.l, .m, .lo, .up, .fx):
  - `.l` - level (primal value after solve)
  - `.m` - marginal (dual value, shadow price)
  - `.lo` - lower bound
  - `.up` - upper bound
  - `.fx` - fix to specific value
- **Setting bounds**:
  ```gams
  vm_land.lo(j,land) = 0;
  vm_land.up(j,land) = sum(land, pm_land_start(j,land));
  vm_land.fx(j,"urban") = pm_urban_land(j);
  ```
- **Initialization**: Setting .l for warm starts
- **Interface variables in MAgPIE**: vm_ prefix
- **Examples from MAgPIE**:
  - `vm_land(j,land)` - positive variable with bounds
  - `vm_cost_glo` - free variable for objective
  - `.fx` usage: fixing variables in presolve

#### 1.5 Equations (Constraints) (1,500 words)
- **Purpose**: Define mathematical relationships and constraints
- **Two-step process**:
  1. **Declaration**: `equations q_name(i) Description ;`
  2. **Definition**: Algebraic formula with `..`
- **Relational operators**:
  - `=e=` - equality (=)
  - `=l=` - less than or equal (≤)
  - `=g=` - greater than or equal (≥)
- **Equation syntax**:
  ```gams
  q10_land_area(j2) ..
    sum(land, vm_land(j2,land)) =e=
    sum(land, pcm_land(j2,land));
  ```
- **Domain restriction**: Using specific set members (j2 vs j)
- **Summation in equations**: `sum((i,j), expression)`
- **Multiple terms**: Building complex constraints
- **Equation naming**: q{module}_ prefix in MAgPIE
- **Documentation**: *' for equation comments in MAgPIE
- **Examples from MAgPIE**:
  - `q10_land_area` - equality constraint (land conservation)
  - `q42_water_demand` - inequality constraint (water availability)
  - Complex equations with multiple sums

#### 1.6 Model & Solve Statements (900 words)
- **Model declaration**: Grouping equations
  ```gams
  Model magpie / all /;
  ```
- **Selective inclusion**: `Model m / eq1, eq2, eq3 /;`
- **Solve statement**:
  ```gams
  Solve magpie using nlp minimizing vm_cost_glo;
  ```
- **Solver types**:
  - `lp` - linear programming
  - `nlp` - nonlinear programming
  - `mip` - mixed integer programming
  - `qcp` - quadratic constraint programming
- **Optimization direction**: `minimizing` or `maximizing`
- **Solve status**: Checking feasibility and optimality
- **Solution retrieval**: Accessing .l and .m values
- **MAgPIE model structure**: Main model with modular equations
- **Iterative solving**: MAgPIE's time step approach

---

### Phase 2: GAMS Control Structures

#### 2.1 Dollar Conditions ($) (1,800 words)
- **Purpose**: Conditional filtering and exception handling
- **General syntax**: `expression $ logical_condition`
- **Two positions**:
  1. **Dollar on the left**: No assignment if false
     ```gams
     rho(i) $ (sig(i) <> 0) = (1./sig(i)) - 1;
     ```
  2. **Dollar on the right**: Assigns zero if false
     ```gams
     a = 2 $ (b > 1.5);
     ```
- **In assignments**: Protecting against invalid operations
- **In equations**: Restricting equation domain or terms
  ```gams
  mb(i).. x(i) =g= y(i) + (e(i) - m(i)) $ t(i);
  ```
- **In sums**: Conditional aggregation
  ```gams
  sum(i$(condition), expression)
  ```
- **Nested conditions**: Multiple $ operators
- **Set membership**: `$(set(i))` checks if i is in set
- **Comparison operators**: `<`, `<=`, `=`, `<>`, `>=`, `>`
- **Logical operators**: `and`, `or`, `not`, `xor`
- **MAgPIE patterns**:
  - `$(not sameas(land_from,land_to))` - excluding diagonal
  - `$(m_year(t) > threshold)` - time-based conditions
  - `$(condition1 and condition2)` - compound conditions
- **Common uses**:
  - Avoiding division by zero
  - Conditional parameter updates
  - Filtering unwanted combinations
  - Exception handling

#### 2.2 Conditional Execution (if-elseif-else) (1,000 words)
- **Purpose**: Branch execution based on runtime conditions
- **Basic syntax**:
  ```gams
  if (condition,
    statements;
  );
  ```
- **If-else structure**:
  ```gams
  if (condition,
    statements1;
  else
    statements2;
  );
  ```
- **If-elseif-else chains**:
  ```gams
  if (condition1,
    statements1;
  elseif condition2,
    statements2;
  else
    statements3;
  );
  ```
- **Restrictions**: Only execution statements allowed (no declarations)
- **Nesting**: If statements within if statements
- **MAgPIE examples**:
  - Time step checks: `if (ord(t) > 1, ...)`
  - Scenario switches: `if (s_scenario = 1, ...)`
  - Calibration logic: `if (sum(sameas(t_past,t),1) = 1, ...)`
- **Common patterns**:
  - First timestep initialization
  - Scenario-dependent parameter setting
  - Conditional data processing

#### 2.3 Loops (loop, while, for, repeat) (1,500 words)
- **Loop statement** (most common in MAgPIE):
  ```gams
  loop(i,
    statements;
  );
  ```
- **Multi-index loops**: `loop((i,j), ...)`
- **Nested loops**:
  ```gams
  loop(i,
    loop(j,
      statements;
    );
  );
  ```
- **Dynamic loop sets**: Loop over filtered sets
- **While statement**:
  ```gams
  while(condition,
    statements;
  );
  ```
- **For statement**:
  ```gams
  for(n = start to end by step,
    statements;
  );
  ```
- **Repeat-until statement**:
  ```gams
  repeat(
    statements;
  until condition);
  ```
- **MAgPIE patterns**:
  - `loop(t_all, ...)` - processing all time steps
  - `loop(i, loop(biome44, ...))` - nested spatial loops
  - Iterative calibration procedures
- **When to use each type**:
  - `loop`: Iterating over sets (most common)
  - `while`: Unknown iteration count, condition-driven
  - `for`: Numeric iteration with known range
  - `repeat`: At least one execution guaranteed

#### 2.4 Break & Continue (600 words)
- **Break**: Exit loop prematurely
  ```gams
  loop(i,
    if(condition, break);
    statements;
  );
  ```
- **Break with level**: `break 2` exits two nested loops
- **Continue**: Skip to next iteration
  ```gams
  loop(i,
    if(skip_condition, continue);
    statements;
  );
  ```
- **Use cases**:
  - Early termination on convergence
  - Skipping invalid combinations
  - Efficient processing

#### 2.5 Abort Statements (500 words)
- **Purpose**: Terminate execution with message
- **Basic abort**:
  ```gams
  abort$(condition) "Error message";
  ```
- **Abort with value**: Display parameter value
- **Abort.noError**: Exit without error flag
- **MAgPIE usage**: Validation checks
- **Best practices**: Clear error messages

---

### Phase 3: GAMS Advanced Features

#### 3.1 Macros ($macro) (1,800 words)
- **Purpose**: Reusable code templates, function-like constructs
- **Declaration**:
  ```gams
  $macro macro_name(args) expression
  ```
- **Usage**: Call like a function
  ```gams
  result = macro_name(arg1, arg2);
  ```
- **No side effects**: Pure substitution at compile time
- **Common macro patterns**:
  1. **Mathematical formulas**: Reduce repetition
  2. **Conditional expressions**: Complex logic
  3. **Time calculations**: Year differences
  4. **Data transformations**: Interpolation
- **MAgPIE macros** (from core/macros.gms):
  - `m_year(t)` - Convert time set to calendar year
  - `m_yeardiff(t)` - Years since previous timestep
  - `m_timestep_length` - Current timestep length
  - `m_annuity_ord/due` - Financial calculations
  - `m_linear_time_interpol` - Linear interpolation
  - `m_sigmoid_time_interpol` - S-curve interpolation
  - `m_carbon_stock` - Carbon calculation pattern
  - `m_weightedmean` - Weighted averages
  - `m_growth_vegc` - Chapman-Richards growth
- **Multi-line macros**: Using backslash `\`
- **Nested macro calls**: Macros calling macros
- **Advantages**:
  - Code reusability
  - Readability
  - Maintainability
  - Compile-time evaluation
- **Limitations**:
  - No recursion
  - Text substitution only
  - Debugging can be harder

#### 3.2 Dollar Control Options (1,200 words)
- **Purpose**: Compile-time directives and file handling
- **Common options**:
  - `$include file.gms` - Insert external file
  - `$setglobal name value` - Global compile variable
  - `$if condition code` - Conditional compilation
  - `$ontext/$offtext` - Block comments
  - `$phantom` - Suppress identifier warnings
  - `$onEnd/$offEnd` - Alternative loop syntax
- **File inclusion patterns**:
  ```gams
  $include "./modules/10_land/declarations.gms"
  ```
- **Conditional compilation**:
  ```gams
  $if %scenario% == "SSP2" code
  ```
- **MAgPIE usage**:
  - Module loading
  - Scenario configuration
  - R code generation markers
- **Best practices**: Organizing large models

#### 3.3 Variable Attributes (.l, .m, .lo, .up, .fx) (1,200 words)
- **Five attributes** (database fields):
  1. `.l` - Level (solution value)
  2. `.m` - Marginal (shadow price)
  3. `.lo` - Lower bound
  4. `.up` - Upper bound
  5. `.fx` - Fixed value (sets both .lo and .up)
- **Before solve**: Setting bounds and initialization
  ```gams
  vm_land.lo(j,land) = 0;
  vm_land.up(j,land) = pm_cell_area(j);
  vm_land.fx(j,"urban") = pm_urban(j);
  ```
- **After solve**: Retrieving results
  ```gams
  parameter p_result(j);
  p_result(j) = vm_land.l(j,"cropland");
  ```
- **Fixing variables**: Convert to parameters
  ```gams
  vm_feed_balanceflow.fx(i,kap,kall) = fm_feed_balanceflow(t,i,kap,kall);
  ```
- **Unbounded variables**: `Inf` and `-Inf`
  ```gams
  vm_feed_balanceflow.up(i,kli_rum,"pasture") = Inf;
  vm_feed_balanceflow.lo(i,kli_rum,"pasture") = -Inf;
  ```
- **Initialization for warm starts**: Setting .l values
- **Marginals for sensitivity**: Understanding .m values
- **MAgPIE patterns**:
  - Fixing historical time steps
  - Soft fixing with bounds
  - Retrieving results for next timestep

#### 3.4 Set Operations & Functions (1,000 words)
- **Set membership**: `set(i)` evaluates to true/false
- **Set operations**:
  - Union: `set1 + set2`
  - Intersection: `set1 * set2`
  - Difference: `set1 - set2`
- **Set functions**:
  - `ord(set)` - Ordinal position (1-indexed)
  - `card(set)` - Cardinality (number of elements)
  - `sameas(set1, set2)` - Identity check
  - `sameAs(element1, element2)` - Element equality
- **Dynamic sets**: Defined by conditions
  ```gams
  set active(i);
  active(i) = yes$(condition);
  ```
- **Set assignment**: yes/no values
- **MAgPIE examples**:
  - `ord(t)` - First timestep checks
  - `sameas(land_from, land_to)` - Diagonal exclusion
  - `card(t)` - Count time steps
  - Dynamic regional sets

#### 3.5 Time Indexing Patterns (1,800 words)
- **Time sets in MAgPIE**:
  - `t_all` - All possible time steps
  - `t` - Active optimization time steps
  - `t_past` - Historical period
  - `ct` - Current time step (singleton)
- **Lag and lead operators**:
  - `t-1` - Previous time step
  - `t+1` - Next time step
  - `t+5` - Five steps ahead
- **Ordinal functions**:
  - `ord(t)` - Time step number
  - `m_year(t)` - Calendar year (MAgPIE macro)
  - `m_yeardiff(t)` - Years since last step
- **First timestep patterns**:
  ```gams
  if (ord(t) = 1,
    initialization;
  else
    normal_calculation;
  );
  ```
- **Last timestep patterns**:
  ```gams
  if (ord(t) = smax(t2, ord(t2)),
    finalization;
  );
  ```
- **Rolling parameters** (values carried forward):
  ```gams
  pcm_land(j,land) = vm_land.l(j,land);
  ```
- **Time-dependent interpolation**:
  - Linear: `m_linear_time_interpol`
  - Sigmoid: `m_sigmoid_time_interpol`
- **MAgPIE time management**:
  - Recursive dynamic optimization
  - Decadal time steps (5-10 years)
  - Historical calibration period
  - Future projection period
- **Common patterns**:
  - Growth rates: `(value(t) - value(t-1)) / value(t-1)`
  - Accumulation: `sum(t2$(ord(t2) <= ord(t)), increment(t2))`
  - Time-conditional parameters
  - Initialization vs. projection logic

---

### Phase 4: GAMS Functions & Operations (Reference)

#### 4.1 Mathematical Functions (1,200 words)
- **Arithmetic**: +, -, *, /, ** (power)
- **Standard math functions**:
  - `abs(x)` - Absolute value
  - `sqrt(x)` - Square root
  - `exp(x)` - Exponential
  - `log(x)`, `log10(x)` - Logarithms
  - `power(x,y)` - x^y
- **Trigonometric**: sin, cos, tan, arctan, etc.
- **Rounding**: round, ceil, floor, trunc
- **Min/Max**: min, max (for scalars)
- **Sign**: sign(x), max(0, x) patterns
- **Division by zero protection**: Adding small epsilon
- **MAgPIE examples**:
  - Growth functions: `exp(-k*ac)`
  - Sigmoid curves: `1 / (1 + exp(-10*(x-0.5)))`
  - Power functions: `(1+r)**t`

#### 4.2 Logical Operators & Expressions (800 words)
- **Comparison operators**: `<, <=, =, <>, >=, >`
- **Logical operators**:
  - `and` - Conjunction
  - `or` - Disjunction
  - `not` - Negation
  - `xor` - Exclusive or
  - `imp` - Implication (a imp b ≡ not a or b)
  - `eqv` - Equivalence
- **Numerical interpretation**: 0 = FALSE, non-zero = TRUE
- **Short-circuit evaluation**: None in GAMS
- **Compound conditions**:
  ```gams
  $(condition1 and condition2)
  $(not condition or condition3)
  ```
- **MAgPIE patterns**: Complex filtering conditions

#### 4.3 Set Functions (ord, card, sameas, etc.) (900 words)
- **ord(element)**: Position in set (1-indexed)
  - Use: Time step ordering, sequential processing
- **card(set)**: Number of elements
  - Use: Checking if set is empty, counting
- **sameas(set1, set2)**: Test if sets are identical
  - Use: Excluding diagonal in matrices
- **sameAs(element1, element2)**: Test element equality
  - Use: Element comparison
- **smax, smin**: Maximum/minimum over set
  ```gams
  smax(t2, ord(t2))  // Last time step ordinal
  smin(i, parameter(i))  // Minimum parameter value
  ```
- **MAgPIE examples**:
  - Last timestep: `smax(t2, ord(t2)$(t_past(t2)))`
  - Excluding self-transitions: `$(not sameas(land_from,land_to))`

#### 4.4 Aggregation (sum, prod, smin, smax) (1,100 words)
- **sum(set, expression)**: Summation over set
  ```gams
  total = sum(i, parameter(i));
  ```
- **Multi-index sum**: `sum((i,j), expression)`
- **Conditional sum**: `sum(i$(condition), expression)`
- **Nested sums**: Building complex aggregations
- **prod(set, expression)**: Product over set
- **smin, smax**: Minimum/maximum with choice
  ```gams
  lowest_value = smin(i, parameter(i));
  highest_value = smax(i, parameter(i));
  ```
- **MAgPIE patterns**:
  - Land totals: `sum(land, vm_land(j,land))`
  - Regional aggregation: `sum(cell(i,j), value(j))`
  - Product sums: `sum(kall, production(kall))`
  - Conditional aggregation with dollar conditions

#### 4.5 Conditional Assignments (1,000 words)
- **Dollar condition assignment**:
  ```gams
  parameter(i) $ (condition) = expression;
  ```
- **If-else in assignment** (using $):
  ```gams
  result = value1$(condition) + value2$(not condition);
  ```
- **Multiple conditions**: Chaining conditionals
- **ifthen equivalent**: Simulating ternary operator
  ```gams
  result = expression1$(condition) + expression2$(not condition);
  ```
- **Protecting against edge cases**:
  - Division by zero: `$(denominator <> 0)`
  - Negative square root: `$(value >= 0)`
  - Log of zero: `$(value > 0)`
- **MAgPIE patterns**:
  - Conditional parameter updates
  - Scenario-specific values
  - Threshold-based assignments

---

### Phase 5: MAgPIE-Specific Patterns (Applied)

#### 5.1 Module Structure Patterns (1,600 words)
- **Standard module files**:
  1. `declarations.gms` - Sets, parameters, variables, equations
  2. `equations.gms` - Equation definitions
  3. `input.gms` - Load input data, set scalars
  4. `presolve.gms` - Pre-processing, bounds, initialization
  5. `postsolve.gms` - Post-processing, result calculation
  6. `preloop.gms` - Before time loop
  7. `sets.gms` - Module-specific sets
  8. `realization.gms` - Module metadata
- **Naming conventions**:
  - Parameters: `p{module}_name` (internal)
  - Variables: `v{module}_name` (internal)
  - Equations: `q{module}_name` (internal)
  - Interface: `vm_name`, `pm_name` (shared)
  - Inputs: `f{module}_name`, `i{module}_name`
- **R sections**: Auto-generated output declarations
  ```gams
  *#################### R SECTION START (OUTPUT DECLARATIONS) ####################
  *##################### R SECTION END (OUTPUT DECLARATIONS) #####################
  ```
- **Documentation comments**: Using `*'` for roxygen-style docs
- **Module execution order**: Defined in main.gms
- **Interface vs internal**: Clear separation of scope

#### 5.2 Interface Variable Patterns (1,400 words)
- **Interface variables** (vm_ prefix): Shared between modules
- **Interface parameters** (pm_ prefix): Passed data
- **Declaration location**: Core declarations.gms
- **Usage pattern**:
  1. Module A defines/calculates vm_X
  2. Module B uses vm_X in equations/parameters
- **Example flows**:
  - `vm_land` (Module 10) → used by Modules 14, 30, 31, etc.
  - `vm_prod` (Module 17) → used by Modules 20, 21, 70
  - `vm_carbon_stock` (Module 52) → used by Module 56
- **Dependency management**: Order matters
- **Circular dependencies**: Resolution strategies
  - Temporal feedback (t vs t-1)
  - Sequential execution
  - Simultaneous equations
- **Interface completeness**: All modules respect contracts

#### 5.3 Time Step Management (1,600 words)
- **Time loop structure** (in main.gms):
  ```gams
  loop(t,
    ct(t) = yes;
    * Presolve phase
    * Solve model
    * Postsolve phase
    ct(t) = no;
  );
  ```
- **Current time marker**: `ct` singleton set
- **Historical vs projection**: `t_past` vs `t`
- **Recursive optimization**: Each timestep uses previous results
- **Rolling parameters**: Carrying values forward
  ```gams
  pcm_land(j,land) = vm_land.l(j,land);
  ```
- **Time-conditional logic**:
  - First timestep initialization
  - Historical period calibration
  - Future projection calculations
- **Year conversion**: `m_year(t)` macro
- **Timestep length**: Variable (5-10 years in MAgPIE)
- **Anticipation**: Model has perfect foresight within timestep

#### 5.4 Calibration & Initialization (1,600 words)
- **Purpose**: Match historical data, set realistic starting points
- **Historical fixing**:
  ```gams
  vm_land.fx(j,land)$(t_past(t)) = pm_land_hist(t,j,land);
  ```
- **Calibration parameters**: Matching observed patterns
  - Yield calibration factors
  - Cost calibration
  - Behavioral parameters
- **Initialization sequence**:
  1. Load historical data (input.gms)
  2. Set starting values (presolve.gms)
  3. Fix historical period (presolve.gms)
  4. Initialize variables (.l values)
- **Warm start**: Using previous solution as starting point
- **First timestep special handling**: `if (ord(t) = 1, ...)`
- **Transition from historical to projection**:
  ```gams
  if (ord(t) = smax(t2, ord(t2)$(t_past(t2))) AND card(t) > ...,
    transition_logic;
  );
  ```
- **Validation**: Checking calibration quality
- **MAgPIE calibration examples**:
  - Pasture management factor (Module 70)
  - Technological change (Module 13)
  - Land use transitions (Module 10)

#### 5.5 Common Macros in MAgPIE (1,800 words)
- **Time conversion macros**:
  - `m_year(t)` - Calendar year from time set
  - `m_yeardiff(t)` - Years between timesteps
  - `m_timestep_length` - Current step length
- **Financial macros**:
  - `m_annuity_ord(r,n)` - Ordinary annuity factor
  - `m_annuity_due(r,n)` - Annuity due factor
  - Used for capital cost amortization
- **Interpolation macros**:
  - `m_linear_time_interpol` - Linear trajectory
  - `m_sigmoid_time_interpol` - S-curve transition
  - `m_linear_cell_data_interpol` - Spatial interpolation
- **Growth macros**:
  - `m_growth_vegc` - Chapman-Richards vegetation carbon
  - `m_growth_litc_soilc` - Linear litter/soil carbon
  - Used in Module 52 (carbon)
- **Aggregation macros**:
  - `m_weightedmean` - Weighted average with zero-check
  - `m_carbon_stock` - Carbon pool aggregation
  - `m_carbon_stock_ac` - Carbon with age classes
- **Utility macros**:
  - `m_boundfix` - Fix variable if bounds too close
  - `m_fillmissingyears` - Fill data gaps
  - Module-specific macros (m21_, m58_, etc.)
- **Usage examples**: Real code from MAgPIE
- **When to create macros**:
  - Repeated complex expressions
  - Derived quantities needed in multiple places
  - Standardizing calculations across modules
- **Macro best practices**:
  - Clear naming with module prefix
  - Document parameters and units
  - Test for edge cases (division by zero, etc.)

---

### Phase 6: Optimization Modeling Best Practices (Guidance)

#### 6.1 Model Scaling & Units (900 words)
- **Why scaling matters**: Numerical stability and solver performance
- **Unit choices**: Keep values in reasonable range (0.01 to 1000)
- **MAgPIE units**:
  - Land: million hectares (mio. ha)
  - Costs: million USD
  - Production: million tons
- **Avoiding extreme values**: Prevents ill-conditioning
- **Normalization strategies**: Dividing by large constants
- **Solver tolerances**: How scaling affects feasibility
- **Checking model statistics**: Reviewing matrix coefficients

#### 6.2 Numerical Stability (800 words)
- **Division by zero protection**: Using dollar conditions or epsilon
  ```gams
  result$(denom <> 0) = numerator / denom;
  result = numerator / (denom + 1e-10);
  ```
- **Logarithm protection**: Ensuring positive arguments
- **Square root protection**: Ensuring non-negative arguments
- **Avoiding very small/large numbers**: Precision issues
- **Rounding errors**: Careful with equality comparisons
- **Solver tolerances**: Understanding feasibility gaps
- **Infeasibility diagnosis**: Common causes and fixes

#### 6.3 Performance Optimization (900 words)
- **Reducing model size**: Efficient set definitions
- **Equation formulation**: Linear vs nonlinear
- **Variable bounds**: Tighter bounds = faster solve
- **Sparsity**: Avoiding dense matrices
- **Presolving**: Reducing problem before solve
- **Solver options**: Tuning for specific problem
- **Warm starts**: Using previous solutions
- **MAgPIE performance**:
  - Module-level optimization
  - Aggregation strategies
  - Sparse set usage

#### 6.4 Debugging Strategies (1,000 words)
- **GAMS compilation errors**: Reading error messages
- **Execution errors**: Domain violations, infeasibilities
- **Model infeasibilities**: Diagnosis techniques
  - Relaxing constraints
  - Slack variables
  - Infeasibility reports
- **Display statements**: Printing intermediate values
  ```gams
  display parameter_name;
  display variable_name.l, variable_name.m;
  ```
- **Abort with conditions**: Validating assumptions
- **GDX inspection**: Examining solution files
- **Common MAgPIE errors**:
  - Domain violations
  - Unbounded variables
  - Infeasible constraints
  - Convergence failures
- **Systematic debugging**:
  1. Isolate the problem (which module?)
  2. Check input data
  3. Verify equation formulation
  4. Test with simpler case
  5. Add validation checks

#### 6.5 Common Pitfalls & Solutions (1,400 words)
- **Forward references**: Using before declaring
  - Solution: Proper ordering
- **Domain errors**: Index out of set
  - Solution: Domain checking, dollar conditions
- **Uninitialized variables**: Missing .l values
  - Solution: Explicit initialization
- **Circular dependencies**: Module order issues
  - Solution: Time lags, parameter passing
- **Fixed variables in optimization**: Over-constraining
  - Solution: Review .fx usage
- **Missing semicolons**: Common syntax error
  - Solution: Careful formatting
- **Dollar condition logic**: Off-by-one, wrong filter
  - Solution: Test conditions separately
- **Macro expansion issues**: Unexpected substitution
  - Solution: Parenthesize macro arguments
- **Set membership errors**: Empty sets, wrong domain
  - Solution: Validate sets, display card(set)
- **Time indexing errors**: t vs t-1 confusion
  - Solution: Document time relationships
- **MAgPIE-specific pitfalls**:
  - Interface variable misuse
  - Module execution order
  - Historical period handling
  - Unit mismatches between modules

---

## Documentation Delivery Plan

### Implementation Phases

**Phase 1-2 (Fundamentals + Control Structures)**: ~14,000 words
- **Target completion**: Week 1-2
- **Priority**: CRITICAL - Required for reading any GAMS code
- **Validation**: Test understanding with simple MAgPIE examples

**Phase 3 (Advanced Features)**: ~7,000 words
- **Target completion**: Week 3
- **Priority**: HIGH - Required for understanding MAgPIE patterns
- **Validation**: Explain MAgPIE macros and time indexing

**Phase 4 (Functions & Operations)**: ~5,000 words
- **Target completion**: Week 4
- **Priority**: MEDIUM - Reference material, on-demand
- **Validation**: Reference guide completeness check

**Phase 5 (MAgPIE Patterns)**: ~8,000 words
- **Target completion**: Week 5
- **Priority**: HIGH - Applied knowledge for MAgPIE work
- **Validation**: Navigate and explain actual MAgPIE modules

**Phase 6 (Best Practices)**: ~4,000 words
- **Target completion**: Week 6
- **Priority**: MEDIUM - Guidance for improvements
- **Validation**: Code review checklist

### Total Estimated Content
- **~38,000 words** across all phases
- **~120-150 pages** formatted
- **Comprehensive code examples** from MAgPIE throughout
- **Quick reference sections** for each topic
- **Cross-references** to official GAMS documentation

---

## Documentation Format

### Each Section Will Include:

1. **Concept Introduction** (2-3 paragraphs)
   - What it is
   - Why it matters
   - When to use it

2. **Syntax Reference** (code blocks)
   - Basic syntax
   - Variations
   - Special cases

3. **MAgPIE Examples** (real code snippets)
   - Module file references
   - Line number citations
   - Explanation of usage

4. **Common Patterns** (bullet points)
   - Typical use cases
   - Best practices
   - Things to avoid

5. **Gotchas & Edge Cases** (warnings)
   - Common mistakes
   - Debugging tips
   - Error messages

6. **See Also** (cross-references)
   - Related concepts
   - Official GAMS docs links
   - Other MAgPIE modules

---

## Success Criteria

An AI agent using this reference should be able to:

1. **Read & understand** any GAMS code in MAgPIE
2. **Explain** what equations and logic do
3. **Navigate** module structure and dependencies
4. **Identify** common patterns and idioms
5. **Debug** basic syntax and logic errors
6. **Suggest** improvements following best practices
7. **Reference** official documentation when needed

---

## Maintenance Plan

- **Update frequency**: As GAMS features evolve or MAgPIE patterns change
- **Feedback integration**: Add examples based on common AI questions
- **Validation**: Periodic review against actual MAgPIE code
- **Expansion**: Add sections as new needs identified

---

**Status**: Plan Complete | **Next Step**: Begin Phase 1 Documentation
