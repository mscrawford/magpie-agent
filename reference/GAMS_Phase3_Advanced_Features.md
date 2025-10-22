# GAMS Programming Reference - Phase 3: Advanced Features

**Version**: 1.0 | **Status**: Complete | **Target Audience**: AI agents working with MAgPIE

**Purpose**: Advanced GAMS patterns used extensively in MAgPIE—macros, dollar control options, variable attributes, set operations, and time indexing.

**Prerequisites**: Phase 1 (Fundamentals) + Phase 2 (Control Structures)

**Official GAMS Documentation**:
- [Dollar Control Options](https://www.gams.com/latest/docs/UG_DollarControlOptions.html)
- [Variables](https://www.gams.com/latest/docs/UG_Variables.html)
- [Set Definition](https://www.gams.com/latest/docs/UG_SetDefinition.html)
- [Ordered Sets](https://www.gams.com/latest/docs/UG_OrderedSets.html)
- [Dynamic Sets](https://www.gams.com/latest/docs/UG_DynamicSets.html)

---

## Table of Contents

1. [Macros ($macro)](#1-macros-macro)
2. [Dollar Control Options](#2-dollar-control-options)
3. [Variable Attributes (.l, .m, .lo, .up, .fx)](#3-variable-attributes-l-m-lo-up-fx)
4. [Set Operations & Functions](#4-set-operations--functions)
5. [Time Indexing Patterns](#5-time-indexing-patterns)

---

## 1. Macros ($macro)

### 1.1 What are Macros?

**Macros** enable **compile-time text substitution** for reusable code templates. They function like preprocessor macros in C or inline functions, but operate purely through text replacement before GAMS compilation.

**Official GAMS Documentation**: "The `$macro` option preprocesses macro definitions" ([UG_DollarControlOptions](https://www.gams.com/latest/docs/UG_DollarControlOptions.html))

**Key characteristics**:
- **No side effects**: Pure substitution at compile time
- **No recursion**: Macros cannot call themselves
- **Parameterized**: Accept arguments for flexibility
- **Inline everywhere**: Expand in assignments, equations, parameters

### 1.2 Basic Syntax

```gams
$macro macro_name(arg1, arg2, arg3) expression_using_args
```

**Usage**:
```gams
result = macro_name(value1, value2, value3);
```

The macro call is **textually replaced** with the expression before compilation.

### 1.3 Simple Macro Example

```gams
$macro square(x) (x * x)

parameter a, b;
a = 5;
b = square(a);  * Expands to: b = (5 * 5)
```

**Result**: `b = 25`

### 1.4 MAgPIE Core Macros

MAgPIE defines many essential macros in `core/macros.gms`. Here are the most important:

#### 1.4.1 Time Conversion Macros

**m_year(t)** - Convert time set to calendar year

**Source** (`core/macros.gms:37`):
```gams
$macro m_year(t) (sum(time_annual,ord(time_annual)$sameas(t,time_annual)) + 1964)
```

**Usage**:
```gams
if (m_year(t) > 2030,
    future_policy_active = 1;
);
```

**Explanation**: Sums the ordinal position of the matching `time_annual` element and adds 1964 (base year). Returns the actual calendar year.

**m_yeardiff(t)** - Years since previous timestep

**Source** (`core/macros.gms:41`):
```gams
$macro m_yeardiff(t) (1$(ord(t)=1) + (m_year(t)-m_year(t-1))$(ord(t)>1))
```

**Usage**:
```gams
annual_cost(t) = total_cost(t) / m_yeardiff(t);
```

**Explanation**: Returns 1 for first timestep, otherwise calculates year difference from previous timestep.

**m_timestep_length** - Current timestep length (for use in equations)

**Source** (`core/macros.gms:51`):
```gams
$macro m_timestep_length sum((ct,t2),(1$(ord(t2)=1) + (m_year(t2)-m_year(t2-1))$(ord(t2)>1))$sameas(ct,t2))
```

**Requirements**:
- `t2` must be alias of `t`
- `ct` must be singleton set for current timestep

**Usage in equations**:
```gams
q_growth.. v_stock(ct) =e= v_stock_prev + v_growth * m_timestep_length;
```

#### 1.4.2 Financial Macros

**m_annuity_ord(interest_rate, time_horizon)** - Ordinary annuity factor

**Source** (`core/macros.gms:25`):
```gams
$macro m_annuity_ord(interest_rate,time_horizon) \
    ((1+interest_rate)**(time_horizon)-1)/(interest_rate*(1+interest_rate)**(time_horizon))
```

**Purpose**: Convert present value to annual payment (cash flow at end of period)

**Formula**: From [time value of money](https://en.wikipedia.org/wiki/Time_value_of_money)

**Usage**:
```gams
annual_payment = investment_cost / m_annuity_ord(0.05, 20);
```

**m_annuity_due(interest_rate, time_horizon)** - Annuity due factor

**Source** (`core/macros.gms:31`):
```gams
$macro m_annuity_due(interest_rate,time_horizon) \
    (1-(1+interest_rate)**(-time_horizon))/((interest_rate)/(1+interest_rate))
```

**Purpose**: Convert present value to annual payment (cash flow at beginning of period)

**Used for**: TC, land conversion, irrigation infrastructure costs in MAgPIE

**Reference**: Jordan et al. (2000), Fundamentals of Corporate Finance, pp. 164-165

#### 1.4.3 Growth Function Macros

**m_growth_vegc(S, A, k, m, ac)** - Chapman-Richards vegetation carbon growth

**Source** (`core/macros.gms:18`):
```gams
$macro m_growth_vegc(S,A,k,m,ac) S + (A-S)*(1-exp(-k*(ac*5)))**m
```

**Parameters**:
- `S` - Starting carbon density
- `A` - Asymptotic (maximum) carbon density
- `k` - Growth rate parameter
- `m` - Shape parameter
- `ac` - Age class (multiplied by 5 for years)

**Usage** (Module 52 - Carbon):
```gams
carbon_density(ac) = m_growth_vegc(initial, maximum, 0.06, 2.4, ac);
```

**m_growth_litc_soilc(start, end, ac)** - Linear litter/soil carbon growth

**Source** (`core/macros.gms:20`):
```gams
$macro m_growth_litc_soilc(start,end,ac) \
    (start + (end - start) * 1/20 * ac*5)$(ac <= 20/5) + end$(ac > 20/5)
```

**Explanation**: Linear growth over 20 years (4 age classes at 5 years each), then constant.

#### 1.4.4 Interpolation Macros

**m_linear_time_interpol(input, start_year, target_year, start_value, target_value)**

**Source** (`core/macros.gms:79-83`):
```gams
$macro m_linear_time_interpol(input,start_year,target_year,start_value,target_value) \
  input(t_all)$(m_year(t_all) > start_year AND m_year(t_all) < target_year) = \
      ((m_year(t_all)-start_year) / (target_year-start_year));  \
  input(t_all) = start_value + input(t_all) * (target_value-start_value); \
  input(t_all)$(m_year(t_all) <= start_year) = start_value; \
  input(t_all)$(m_year(t_all) >= target_year) = target_value;
```

**Purpose**: Linear transition from `start_value` to `target_value` between two years.

**Example**:
```gams
m_linear_time_interpol(policy_strength, 2020, 2050, 0, 1);
```

Creates gradual policy phase-in from 0 in 2020 to 1 in 2050.

**m_sigmoid_time_interpol(...)** - S-curve (sigmoid) interpolation

**Source** (`core/macros.gms:86-91`):
```gams
$macro m_sigmoid_time_interpol(input,start_year,target_year,start_value,target_value) \
  input(t_all)$(m_year(t_all) >= start_year AND m_year(t_all) <= target_year) = \
      ((m_year(t_all)-start_year) / (target_year-start_year));  \
  input(t_all) = 1 / (1 + exp(-10*(input(t_all)-0.5))); \
  input(t_all) = start_value + input(t_all) * (target_value-start_value); \
  input(t_all)$(m_year(t_all) <= start_year) = start_value; \
  input(t_all)$(m_year(t_all) >= target_year) = target_value;
```

**Purpose**: Smooth S-shaped transition (slow→fast→slow change).

**Sigmoid formula**: `1 / (1 + exp(-10*(x-0.5)))`

#### 1.4.5 Utility Macros

**m_weightedmean(x, w, s)** - Weighted mean with zero-check

**Source** (`core/macros.gms:16`):
```gams
$macro m_weightedmean(x,w,s) (sum(s,x*w)/sum(s,w))$(sum(s,w)>0) + 0$(sum(s,w)<=0)
```

**Protection**: Returns 0 if total weight is zero (avoids division by zero).

**Usage**:
```gams
avg_yield(i) = m_weightedmean(yield(i,j), area(i,j), j);
```

**m_boundfix(x, arg, sufx, sens)** - Auto-fix variables with narrow bounds

**Source** (`core/macros.gms:14`):
```gams
$macro m_boundfix(x,arg,sufx,sens) x.fx arg$(x.up arg-x.lo arg<sens) = x.sufx arg
```

**Purpose**: Fix variable if upper and lower bounds are very close (within `sens`).

**Example**:
```gams
m_boundfix(vm_land, (j,"forest"), up, 1e-6);
```

If `vm_land.up(j,"forest") - vm_land.lo(j,"forest") < 1e-6`, fix to upper bound.

**m_fillmissingyears(input, sets)** - Fill data gaps

**Source** (`core/macros.gms:68-75`):
```gams
$macro m_fillmissingyears(input,sets) loop(t_all, \
          ct_all(t_all) = yes;     \
          if(sum((ct_all,&&sets),input(ct_all,&&sets))=0,    \
            input(t_all,&&sets) = input(t_all-1,&&sets);    \
            display "Data gap in input filled with data from previous time step for the following year: ",ct_all;    \
          ); \
          ct_all(t_all) = no;    \
       );
```

**Purpose**: Forward-fill missing years from previous timestep.

### 1.5 Multi-Line Macros

Use backslash `\` for continuation:

```gams
$macro complex_calculation(a,b,c) \
    (a * b) + \
    (b * c) + \
    (a * c)
```

### 1.6 Macro Best Practices

**DO**:
- ✅ Use descriptive names (e.g., `m_year`, not `my`)
- ✅ Parenthesize macro body to avoid operator precedence issues
- ✅ Parenthesize arguments in macro definition: `(x * x)` not `x * x`
- ✅ Document parameters and purpose with comments
- ✅ Test edge cases (zero values, boundary conditions)

**DON'T**:
- ❌ Use recursion (not supported)
- ❌ Expect side effects (pure substitution only)
- ❌ Forget to parenthesize complex expressions
- ❌ Use variable names that might conflict with call site

**Example of precedence issue**:

```gams
$macro bad_square(x) x * x

a = bad_square(2 + 3);  * Expands to: a = 2 + 3 * 2 + 3 = 11 (WRONG!)
```

**Fixed**:
```gams
$macro good_square(x) ((x) * (x))

a = good_square(2 + 3);  * Expands to: a = ((2 + 3) * (2 + 3)) = 25 (CORRECT!)
```

### 1.7 When to Create Macros

**Create macros when**:
- Same complex expression repeated many times
- Derived quantities needed in multiple modules
- Standardizing calculations across codebase
- Financial formulas (annuities, NPV, etc.)
- Growth functions with many parameters

**Use inline code when**:
- Expression used only once
- Simple arithmetic
- Code clarity would suffer
- Debugging required (macros harder to debug)

---

## 2. Dollar Control Options

### 2.1 Overview

**Dollar control options** are **compile-time directives** that control file inclusion, conditional compilation, output formatting, and macro processing.

**Syntax**: `$option_name argument_list`

**Key characteristic**: Executed during **compilation**, not runtime.

### 2.2 File Inclusion

#### $include

**Syntax**: `$include filename` or `$include "filename"`

**Purpose**: Insert contents of external file at this location.

**MAgPIE example** (`main.gms`):
```gams
$include "./core/sets.gms"
$include "./core/macros.gms"
$include "./modules/10_land/declarations.gms"
```

**Path rules**:
- Relative to current file location
- Use forward slashes `/` (cross-platform)
- Quotes optional unless filename has spaces

#### $batInclude

**Syntax**: `$batInclude filename arg1 arg2 arg3`

**Purpose**: Include file with **parameter substitution** (`%1`, `%2`, `%3`, ...).

**Example**:

**File `module_loader.gms`**:
```gams
* %1 = module number, %2 = module name, %3 = realization
$include "./modules/%1_%2/%3/declarations.gms"
$include "./modules/%1_%2/%3/equations.gms"
```

**Usage**:
```gams
$batInclude module_loader 10 land landmatrix_dec18
```

**Expands to**:
```gams
$include "./modules/10_land/landmatrix_dec18/declarations.gms"
$include "./modules/10_land/landmatrix_dec18/equations.gms"
```

### 2.3 Conditional Compilation

#### $if / $ifI / $ifE

**Syntax**:
```gams
$if condition statement
$ifI condition statement     * Case-insensitive
$ifE condition statement     * Evaluate expression
```

**Example - Testing if variable is set**:
```gams
$if not set scenario $abort "Scenario parameter required!"
```

**Example - File existence check**:
```gams
$if exist "custom_config.gms" $include "custom_config.gms"
```

**Example - Solver availability**:
```gams
$if solver CPLEX $setGlobal use_cplex yes
```

#### $ifThen / $elseIf / $else / $endIf

**Syntax**:
```gams
$ifThen condition
    statements
$elseIf condition
    statements
$else
    statements
$endIf
```

**MAgPIE example**:
```gams
$ifThen %scenario% == "SSP2"
    $setGlobal population ssp2
    $setGlobal gdp ssp2
$elseIf %scenario% == "SSP1"
    $setGlobal population ssp1
    $setGlobal gdp ssp1
$else
    $abort "Unknown scenario"
$endIf
```

### 2.4 Compile-Time Variables

#### $set / $setGlobal / $setLocal

**Syntax**:
```gams
$set VARNAME value           * Scoped (current file)
$setGlobal VARNAME value     * Global (all files)
$setLocal VARNAME value      * Local (innermost scope)
```

**Usage**:
```gams
$setGlobal scenario SSP2
$include "./config_%scenario%.gms"  * Loads config_SSP2.gms
```

**Accessing**: `%VARNAME%`

#### $eval - Evaluate expressions

**Syntax**: `$eval VARNAME expression`

**Example**:
```gams
$set year_start 2020
$set year_end 2050
$eval time_horizon %year_end% - %year_start%
display "Time horizon: %time_horizon% years";
```

**Result**: `Time_horizon: 30 years`

#### $drop - Remove variable

```gams
$drop VARNAME
$dropGlobal VARNAME
$dropLocal VARNAME
```

### 2.5 Macro Control

**Enable/disable macros**:
```gams
$onMacro     * Enable macro expansion
$offMacro    * Disable macro expansion
```

**Expand during argument processing**:
```gams
$onExpand    * Expand macros in arguments
$offExpand   * Don't expand in arguments
```

### 2.6 Output Control

**Listing control**:
```gams
$onListing    * Show code in listing file
$offListing   * Hide code from listing
```

**Dollar statement echo**:
```gams
$onDollar     * Show $ statements
$offDollar    * Hide $ statements
```

**Text/subtitles**:
```gams
$title "MAgPIE Model - Land Use Optimization"
$sTitle "Module 10 - Land Allocation"
```

### 2.7 Program Control

**Abort compilation**:
```gams
$abort [text]     * Stop with error
```

**Example**:
```gams
$if not set input_data $abort "Input data path must be specified"
```

**Exit current file**:
```gams
$exit      * Stop reading this file
```

**Stop all**:
```gams
$stop      * Stop entire compilation
```

**Call system command**:
```gams
$call command_line
```

**Example**:
```gams
$call gzip output.gdx
```

### 2.8 GDX Operations

**Load from GDX**:
```gams
$gdxIn filename.gdx
$load symbol1 symbol2 symbol3
$gdxIn     * Close
```

**Save to GDX**:
```gams
$gdxOut filename.gdx
$unLoad symbol1 symbol2
$gdxOut    * Close
```

**MAgPIE usage**: Loading calibrated parameters, saving intermediate results.

### 2.9 Comments

**Block comments**:
```gams
$onText
This entire section is ignored by GAMS.
Useful for long explanatory text.
Can span multiple lines.
$offText
```

**Inline comments**: Use `*` (not dollar control)

---

## 3. Variable Attributes (.l, .m, .lo, .up, .fx)

### 3.1 Overview

**Official GAMS Documentation**: "Variables possess several key attributes that control their behavior before and after optimization" ([UG_Variables](https://www.gams.com/latest/docs/UG_Variables.html))

**Five primary attributes**:
1. `.l` - **Level** (value/solution)
2. `.m` - **Marginal** (shadow price/reduced cost)
3. `.lo` - **Lower bound**
4. `.up` - **Upper bound**
5. `.fx` - **Fixed value** (sets both bounds equal)

**Usage context**:
- **Before solve**: Set bounds, initialize warm starts
- **After solve**: Retrieve solution values, examine marginals

### 3.2 Lower Bound (.lo)

**Purpose**: Minimum allowable value for variable.

**Official**: "Set by the user either explicitly or through default values associated with the variable type" ([UG_Variables](https://www.gams.com/latest/docs/UG_Variables.html))

**Default by variable type**:
- `free` → `-inf`
- `positive` → `0`
- `negative` → `-inf`
- `binary` → `0`
- `integer` → `0` (or specified lower)

**Syntax**:
```gams
variable_name.lo(indices) = expression;
```

**MAgPIE example** (Module 10):
```gams
vm_land.lo(j,land) = 0;
```

Ensures land allocation is non-negative (though `positive variable` already enforces this).

**Example - Non-zero lower bound**:
```gams
vm_production.lo(i,"wheat") = min_production(i);
```

### 3.3 Upper Bound (.up)

**Purpose**: Maximum allowable value for variable.

**Default by variable type**:
- `free` → `+inf`
- `positive` → `+inf`
- `negative` → `0`
- `binary` → `1`
- `integer` → `+inf` (or specified upper)

**Syntax**:
```gams
variable_name.up(indices) = expression;
```

**MAgPIE example** (Module 10 - land cannot exceed total cell area):
```gams
vm_land.up(j,land) = pm_land_start(j,land) * 1.5;
```

**Example - Unbounded**:
```gams
vm_trade.up(i,k) = Inf;  * Explicitly set to infinity (default for positive variables)
```

### 3.4 Fixed Value (.fx)

**Purpose**: Fix variable to specific value (makes it a constant in optimization).

**Official**: "If set it results in the upper and lower bounds of the variable to be set to the value of the `.fx` attribute" ([UG_Variables](https://www.gams.com/latest/docs/UG_Variables.html))

**Effect**: `.fx = value` is equivalent to `.lo = value` AND `.up = value`

**Syntax**:
```gams
variable_name.fx(indices) = expression;
```

**MAgPIE example** (`modules/56_ghg_policy/price_aug22/preloop.gms:34`):
```gams
v56_emis_pricing.fx(i,emis_oneoff,pollutants)$(not sameas(pollutants,"co2_c")) = 0;
```

Fixes emissions pricing to zero for non-CO2 pollutants.

**Use cases**:
- **Historical period**: Fix variables to known values
- **Scenario constraints**: Force specific outcomes
- **Debugging**: Isolate variable behavior
- **Reducing model size**: Eliminate decision variables

**Unfixing**:
```gams
variable_name.lo(indices) = lower_value;
variable_name.up(indices) = upper_value;
* .fx no longer active once .lo and .up differ
```

### 3.5 Level / Activity (.l)

**Purpose**: Current value or starting point (before solve); solution value (after solve).

**Before solve**:
```gams
vm_land.l(j,"crop") = pm_land_start(j,"crop");
```

Sets **initial value** for warm start (nonlinear models benefit from good starting points).

**After solve**:
```gams
parameter p_land_solution(j,land);
p_land_solution(j,land) = vm_land.l(j,land);
```

Retrieves **optimal solution** values.

**MAgPIE pattern** (rolling parameters for time loop):
```gams
solve magpie using nlp minimizing vm_cost_glo;
* After solve, carry forward solution to next timestep
pcm_land(j,land) = vm_land.l(j,land);
```

### 3.6 Marginal / Reduced Cost (.m)

**Purpose**: Shadow price (constraint) or reduced cost (variable).

**Official**: "The marginal value (or reduced cost) for the variable. This attribute is reset to a new value when a model containing the variable is solved" ([UG_Variables](https://www.gams.com/latest/docs/UG_Variables.html))

**Interpretation**:
- **Objective improvement**: Rate of objective change if variable increased by 1 unit
- **Shadow price**: Opportunity cost of the variable's current value
- **Zero marginal**: Variable is not at a bound (interior solution)
- **Non-zero marginal**: Variable is at bound; marginal shows improvement from relaxing bound

**Example**:
```gams
solve model using nlp minimizing cost;

if (vm_land.m(j,"forest") > 0,
    display "Increasing forest land would reduce costs";
);
```

**MAgPIE usage**: Analyzing binding constraints, identifying bottlenecks.

### 3.7 Practical Patterns in MAgPIE

#### Fixing Historical Period

```gams
vm_land.fx(j,land)$(t_past(t)) = pm_land_hist(t,j,land);
```

For all historical timesteps, fix land allocation to observed data.

#### Soft Fixing with Narrow Bounds

```gams
vm_production.lo(i,k) = target(i,k) * 0.95;
vm_production.up(i,k) = target(i,k) * 1.05;
```

Constrain variable to within 5% of target (soft constraint).

#### Initialization for Warm Start

```gams
vm_cost_glo.l = sum((i,factor), pm_factor_cost(i,factor));
```

Provide solver with reasonable starting point for objective variable.

#### Retrieving Solutions for Postprocessing

```gams
* In postsolve.gms
ov_land(t,j,land,"level") = vm_land.l(j,land);
ov_land(t,j,land,"marginal") = vm_land.m(j,land);
ov_land(t,j,land,"lower") = vm_land.lo(j,land);
ov_land(t,j,land,"upper") = vm_land.up(j,land);
```

Store all attributes in output parameter for analysis.

### 3.8 Advanced Attributes

**Scale (.scale)** - Numerical scaling (if `scaleopt = 1`):
```gams
vm_large_number.scale = 1e6;  * Internally divide by 1 million
```

**Priority (.prior)** - MIP branching priority:
```gams
vm_binary_choice.prior(i) = importance(i);  * Higher = branch first
```

**Stage (.stage)** - Stochastic programming:
```gams
vm_investment.stage(t) = 1;  * First-stage decision
vm_operation.stage(t,scenario) = 2;  * Second-stage decision
```

**Range (.range)** - Computed (read-only):
```gams
* .range = .up - .lo
```

**Slack (.slack, .slacklo, .slackup)** - Distance from bounds:
```gams
* .slack = .l - .lo (lower slack)
* .slackup = .up - .l (upper slack)
```

---

## 4. Set Operations & Functions

### 4.1 Aliases

**Purpose**: Create alternative name for same set (essential for multi-dimensional operations).

**Official GAMS Documentation**: "Aliases create multiple names for the same set" ([UG_SetDefinition](https://www.gams.com/latest/docs/UG_SetDefinition.html))

**Syntax**:
```gams
alias(original_set, new_name);
alias(set, name1, name2, name3);  * Multiple aliases at once
```

**MAgPIE examples** (`core/sets.gms:222, 358-360`):
```gams
alias(t, t2);
alias(ac, ac2);
alias(ac_sub, ac_sub2);
alias(ac_est, ac_est2);
```

**Why aliases are essential**:

**Without alias** (WRONG):
```gams
distance(i,i) = 0;  * ERROR: Same index name twice!
```

**With alias** (CORRECT):
```gams
alias(i, i2);
distance(i,i2)$(not sameas(i,i2)) = sqrt((x(i)-x(i2))**2 + (y(i)-y(i2))**2);
distance(i,i2)$sameas(i,i2) = 0;
```

**Common uses**:
- Distance matrices
- Transition matrices (land_from → land_to)
- Lead/lag operations (t vs t-1)
- Pairwise comparisons

### 4.2 Set Operations

**Official**: "GAMS provides symbols for arithmetic set operations that may be used with dynamic sets" ([UG_DynamicSets](https://www.gams.com/latest/docs/UG_DynamicSets.html))

#### Union (+ or OR)

```gams
set union_set(i);
union_set(i) = set1(i) + set2(i);
* OR
union_set(i) = set1(i) or set2(i);
```

**Example**:
```gams
set all_crops(k);
all_crops(k) = cereals(k) + oilcrops(k);
```

#### Intersection (* or AND)

```gams
set intersection_set(i);
intersection_set(i) = set1(i) * set2(i);
* OR
intersection_set(i) = set1(i) and set2(i);
```

**Example**:
```gams
set rainfed_cereals(k);
rainfed_cereals(k) = cereals(k) and rainfed_crops(k);
```

#### Difference (-)

```gams
set difference_set(i);
difference_set(i) = set1(i) - set2(i);
```

**Example**:
```gams
set non_forest_land(land);
non_forest_land(land) = all_land(land) - forest_types(land);
```

#### Complement (NOT)

```gams
set complement_set(i);
complement_set(i) = not set1(i);
```

**Example**:
```gams
set inactive(i);
inactive(i) = not active(i);
```

### 4.3 Set Functions

#### ord(element) - Ordinal Position

**Official**: "The ord operator returns integer values when applied to sets" ([UG_OrderedSets](https://www.gams.com/latest/docs/UG_OrderedSets.html))

**Purpose**: Position in ordered set (1-indexed).

**Requirements**:
- Set must be **one-dimensional**
- Set must be **ordered** (not dynamic multi-dimensional)

**Usage**:
```gams
if (ord(t) = 1,
    first_timestep_initialization;
);
```

**Common patterns**:
```gams
$(ord(t) = 1)                 * First element
$(ord(i) = card(i))           * Last element
$(ord(ac) > 1)                * All except first
```

**MAgPIE example** (`modules/70_livestock/fbask_jan16/presolve.gms:119`):
```gams
if (ord(t)>1,
  p70_cattle_stock_proxy(t,i) = p70_cattle_stock_proxy(t-1,i);
);
```

#### card(set) - Cardinality

**Official**: "In the assignment `x.fx(i) $ (ord(i) = card(i)) = 7`, the variable x is fixed for the final element" ([UG_OrderedSets](https://www.gams.com/latest/docs/UG_OrderedSets.html))

**Purpose**: Number of elements in set.

**Usage**:
```gams
scalar num_regions;
num_regions = card(i);
```

**Last element pattern**:
```gams
if (ord(t) = card(t),
    final_timestep_reporting;
);
```

**Empty set check**:
```gams
if (card(active_cells) = 0,
    abort "No active cells found!";
);
```

#### sameas(element1, element2) - Identity Check

**Official**: "The predefined symbol sameas restricts the domain to those label combinations where sameas evaluates to TRUE" ([UG_CondExpr](https://www.gams.com/latest/docs/UG_CondExpr.html))

**Purpose**: Test if two elements are identical.

**Usage**:
```gams
$(sameas(i, "USA"))              * Only for USA
$(not sameas(land_from, land_to)) * Exclude diagonal
```

**MAgPIE example** (`modules/10_land/landmatrix_dec18/equations.gms:16`):
```gams
sum(land_to$(not sameas(land_from,land_to)),
    v10_lu_transitions(j2,land_from,land_to))
```

Sums all land transitions **except** self-transitions.

**Diagonal vs. off-diagonal**:
```gams
* Diagonal elements (land type to itself)
self_retention(land)$sameas(land_from, land_to) = ...;

* Off-diagonal (transitions between types)
transitions(land_from, land_to)$(not sameas(land_from,land_to)) = ...;
```

#### smin / smax - Set minimum/maximum

**Purpose**: Find minimum or maximum value over set.

**Syntax**:
```gams
value = smin(set, expression);
value = smax(set, expression);
```

**Example**:
```gams
* Find year of last historical timestep
last_historical_year = smax(t2$(t_past(t2)), m_year(t2));

* Find minimum cost region
cheapest_region = smin(i, production_cost(i));
```

**MAgPIE pattern** (last historical timestep):
```gams
if (ord(t) = smax(t2, ord(t2)$(t_past(t2))),
    * This is the last historical timestep
);
```

### 4.4 Dynamic Sets

**Dynamic sets** change membership during execution:

```gams
set active(i);      * Declare dynamic set

* Initially empty
active(i) = no;

* Set membership based on condition
active(i)$( production(i) > threshold) = yes;

* Use in loops
loop(active,
    process_active_regions;
);
```

**MAgPIE example** (`modules/80_optimization/nlp_par/solve.gms:52-53`):
```gams
loop(i2,
    j2(j)$cell(i2,j) = yes;  * Dynamically activate cells for region i2
);
```

### 4.5 Set Attributes

**Position (.pos, .ord)**: Element position (1-indexed)
```gams
report(id) = id.pos;  * Position in set
```

**Reverse position (.rev)**:
```gams
report(id) = id.rev;  * Position from end
```

**First/last (.first, .last)**: Boolean indicators
```gams
if (t.first,
    initialization;
);

if (t.last,
    finalization;
);
```

**Length (.len, .tlen)**: String length
```gams
* .len = element label length
* .tlen = element text length
```

---

## 5. Time Indexing Patterns

### 5.1 Time Sets in MAgPIE

**Core time sets** (from `core/sets.gms`):
- `t_all` - All possible time steps (past + present + future)
- `t` - Active optimization time steps (current + future)
- `t_past` - Historical period (calibration data)
- `ct` - Current time step (singleton set, changes each loop iteration)

**Relationships**:
```
t_all = t_past + t
ct ⊂ t  (ct is singleton - exactly one element)
```

### 5.2 Lag and Lead Operators

**Syntax**: `set(index ± offset)`

**Examples**:
```gams
value(t) = value(t-1) * growth_rate;    * Previous timestep (lag)
forecast(t) = projection(t+1);          * Next timestep (lead)
multi_year(t) = baseline(t-5);          * Five steps back
```

**MAgPIE example** (`modules/70_livestock/fbask_jan16/presolve.gms:120`):
```gams
p70_cattle_stock_proxy(t,i) = p70_cattle_stock_proxy(t-1,i);
```

**Important**: Lag/lead only work with **ordered sets**.

### 5.3 First Timestep Patterns

**Pattern 1: Using ord()**
```gams
if (ord(t) = 1,
    initialization_code;
);
```

**Pattern 2: Using set attribute**
```gams
if (t.first,
    initialization_code;
);
```

**Pattern 3: Dollar condition**
```gams
parameter(t)$(ord(t) = 1) = initial_value;
```

**MAgPIE example** (`modules/17_production/flexreg_apr16/presolve.gms:13`):
```gams
if (ord(t) = 1,
  im_demandshare_reg.l(i,kall) = f17_prod_init(i,kall)/sum(i2,f17_prod_init(i2,kall));
);
```

### 5.4 Last Timestep Patterns

**Last of subset**:
```gams
if (ord(t) = smax(t2, ord(t2)$(t_past(t2))),
    * This is last historical timestep
);
```

**Last of full set**:
```gams
if (ord(t) = card(t),
    * This is absolutely last timestep
);

* OR
if (t.last,
    finalization;
);
```

### 5.5 Rolling Parameters (Carrying Values Forward)

**Pattern**: Use previous timestep's solution as input for current timestep.

```gams
loop(t,
    ct(t) = yes;

    * Use previous solution for parameters
    pm_current(j) = vm_solution.l(j);  * From previous solve

    solve model using nlp minimizing objective;

    * Store solution for next iteration
    pcm_land(j,land) = vm_land.l(j,land);

    ct(t) = no;
);
```

**MAgPIE pattern**: Parameters with `pcm_` prefix (Previous Current Module) store solution values.

### 5.6 Time-Dependent Interpolation

**Linear interpolation over time**:
```gams
m_linear_time_interpol(diet_shift, 2020, 2050, 0, 1);
* Result: diet_shift(2020) = 0, diet_shift(2035) = 0.5, diet_shift(2050) = 1
```

**Sigmoid interpolation** (smooth S-curve):
```gams
m_sigmoid_time_interpol(carbon_price, 2025, 2100, 0, 200);
* Slow start, fast middle, slow end
```

### 5.7 Time Conditionals

**After specific year**:
```gams
$(m_year(t) > 2030)
```

**Between years**:
```gams
$(m_year(t) >= 2020 and m_year(t) <= 2050)
```

**MAgPIE example** (`modules/56_ghg_policy/price_aug22/preloop.gms:82`):
```gams
loop(t_all$(m_year(t_all) > max(m_year("%c56_mute_ghgprices_until%"),
                                 s56_fader_start*s56_ghgprice_fader)),
    im_pollutant_prices(t_all,i,pollutants_ghgp) = ...;
);
```

Only applies GHG prices after a threshold year.

### 5.8 Accumulation Over Time

**Cumulative sum up to current timestep**:
```gams
cumulative(t) = sum(t2$(ord(t2) <= ord(t)), annual_value(t2));
```

**Weighted by timestep length**:
```gams
total_emissions(t) = sum(t2$(ord(t2) <= ord(t)),
                         annual_emissions(t2) * m_yeardiff(t2));
```

### 5.9 Common MAgPIE Time Patterns

**Historical fixing**:
```gams
vm_land.fx(j,land)$(t_past(t)) = pm_land_hist(t,j,land);
```

**Transition from historical to projection**:
```gams
if (ord(t) = smax(t2, ord(t2)$(t_past(t2))) AND card(t) > 1,
    * Bridge historical to future
    calibration_adjustment;
);
```

**Current timestep marker**:
```gams
loop(t,
    ct(t) = yes;          * Mark current
    ... solve model ...
    ct(t) = no;           * Unmark
);
```

**Year difference calculation**:
```gams
years_elapsed = m_yeardiff(t);              * Since previous timestep
total_years = m_year(t) - m_year(t_past);   * Since start
```

---

## Summary and Quick Reference

### When to Use Each Feature

| Feature | Use Case | Common Pattern |
|---------|----------|----------------|
| **Macros** | Repeated complex expressions | `m_year(t)`, `m_annuity_ord(r,n)` |
| **Dollar control** | File organization, conditional compilation | `$include`, `$if set scenario` |
| **Variable attributes** | Bounds, warm starts, solution retrieval | `.fx`, `.lo`, `.up`, `.l`, `.m` |
| **Set operations** | Building dynamic subsets | `union_set = set1 + set2` |
| **ord/card** | Timestep logic, counting | `$(ord(t) = 1)`, `card(active)` |
| **sameas** | Element comparison, exclude diagonal | `$(not sameas(i,j))` |
| **Aliases** | Multi-dimensional operations | `alias(t,t2)` for `t` vs `t-1` |
| **Time indexing** | Temporal dynamics, initialization | `if (ord(t) = 1,...)` |

### Most Critical for MAgPIE

1. **Time macros**: `m_year(t)`, `m_yeardiff(t)`, `m_timestep_length`
2. **Financial macros**: `m_annuity_ord`, `m_annuity_due`
3. **Variable fixing**: `.fx` for historical period, bounds for constraints
4. **sameas**: Excluding diagonal in transition matrices
5. **ord(t)**: First-timestep initialization
6. **Aliases**: Essential for multi-index operations (t vs t-1, i vs i2)

### Mandatory Check Before Writing Complex GAMS Code

**When working with advanced GAMS features**:
1. ✅ Consult this Phase 3 documentation
2. ✅ Check `core/macros.gms` for existing macros
3. ✅ Reference official GAMS docs for edge cases
4. ✅ Verify similar patterns in relevant MAgPIE modules
5. ✅ Test with simple examples before production use
6. ✅ Document custom macros with comments

---

**Next Phase**: [Phase 4: Functions & Operations](GAMS_Phase4_Functions_Operations.md) - Mathematical functions, logical operators, aggregation, and conditional assignments.
