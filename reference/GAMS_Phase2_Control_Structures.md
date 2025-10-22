# GAMS Programming Reference - Phase 2: Control Structures & Flow

**Version**: 1.0 | **Status**: Complete | **Target Audience**: AI agents working with MAgPIE

**Purpose**: Essential control flow and conditional execution patterns for reading and writing GAMS code.

**Prerequisites**: Phase 1 (Fundamentals) - understanding of sets, parameters, variables, and equations

**Official GAMS Documentation**:
- [Conditional Expressions, Assignments and Equations](https://www.gams.com/latest/docs/UG_CondExpr.html)
- [Programming Flow Control Features](https://www.gams.com/latest/docs/UG_FlowControl.html)

---

## Table of Contents

1. [Dollar Conditions ($)](#1-dollar-conditions-)
2. [If-ElseIf-Else Statements](#2-if-elseif-else-statements)
3. [Loop Statements](#3-loop-statements)
4. [While and Repeat Statements](#4-while-and-repeat-statements)
5. [For Statements](#5-for-statements)
6. [Break and Continue](#6-break-and-continue)
7. [Abort Statements](#7-abort-statements)

---

## 1. Dollar Conditions ($)

### 1.1 What are Dollar Conditions?

**Official GAMS Documentation**: "The dollar operator is one of the most powerful features in GAMS" ([UG_CondExpr](https://www.gams.com/latest/docs/UG_CondExpr.html))

Dollar conditions (`$`) enable **conditional filtering** of assignments, operations, and equations. They execute a term only when a logical condition evaluates to `TRUE` (non-zero).

**General syntax**:
```gams
term $ logical_condition
```

**Read as**: "Execute `term` under the condition that `logical_condition` is TRUE"

### 1.2 Logical Conditions

#### 1.2.1 Numerical Expressions

Non-zero values are `TRUE`; zero is `FALSE`:

```gams
b $ (2*a - 4) = 7;          * Assign b=7 if 2*a-4 is non-zero
b $ cos(a) = 7;             * Functions permitted
```

**Important**: Variables cannot appear in conditions, but variable attributes (`.l`, `.m`, `.lo`, `.up`) are allowed.

#### 1.2.2 Relational Operators

Standard comparisons: `<`, `<=`, `=`, `<>`, `>=`, `>` (or `lt`, `le`, `eq`, `ne`, `ge`, `gt`)

```gams
b $ (a < 0) = 10;           * Assign if a is negative
t(i) $ (a <> 0) = t(i) + 1; * Increment if a is non-zero
```

**MAgPIE example** (`modules/70_livestock/fbask_jan16/presolve.gms:120`):
```gams
if (ord(t)>1,
  p70_cattle_stock_proxy(t,i) = p70_cattle_stock_proxy(t-1,i);
);
```

#### 1.2.3 Logical Operators

Full set of logical operators:
- `not x` — negation
- `x and y` — conjunction (both true)
- `x or y` — disjunction (at least one true)
- `x xor y` — exclusive OR
- `x imp y` (or `x -> y`) — implication
- `x eqv y` (or `x <=> y`) — equivalence

```gams
u(i) $ (not s(i)) = v(i);
u(i) $ (s(i) and u(i) and t(i)) = s(i);
```

**MAgPIE example** (`modules/56_ghg_policy/price_aug22/preloop.gms:34`):
```gams
v56_emis_pricing.fx(i,emis_oneoff,pollutants)$(not sameas(pollutants,"co2_c")) = 0;
```

This fixes emissions pricing to zero for all pollutants except CO2.

#### 1.2.4 Set Functions in Conditions

**Common set functions**:
- `sameas(element1, element2)` — identity check (are they the same element?)
- `diag(element1, element2)` — numeric identity (returns 1 if same, 0 otherwise)
- `card(set_name)` — cardinality (number of elements)
- `ord(set_name)` — ordinal position in ordered sets (1-indexed)

```gams
b = sum((i,j)$sameas(i,j), 1);      * Sum only diagonal elements
x.fx(i) $ (ord(i) = 1) = 3;          * Fix first element to 3
```

**MAgPIE example** (`modules/10_land/landmatrix_dec18/equations.gms:13-16`):
```gams
q10_land_from(j2,land_from) ..
    v10_lu_transitions(j2,land_from,"crop")
    =e=
    sum(land_to$(not sameas(land_from,land_to)),
        v10_lu_transitions(j2,land_from,land_to));
```

The `$(not sameas(land_from,land_to))` excludes diagonal transitions (land type to itself).

### 1.3 Dollar on Left vs Right

#### 1.3.1 Dollar on Left (Conditional Assignment)

Assignment occurs **only if** condition is `TRUE`. Otherwise, previous values persist (default zero).

```gams
rho(i) $ (sig(i) <> 0) = (1./sig(i)) - 1;
```

If `sig(i) = 0`, `rho(i)` is **not modified** (avoids division by zero).

**MAgPIE example** (`modules/35_natveg/pot_forest_may24/presolve.gms:82`):
```gams
p35_maturesecdf(t,j,ac)$(not sameas(ac,"acx")) =
    (s35_natveg_harvest_secdforest * sum(ac_est, p35_secdforest(t,j,ac_est)))
    / (sum(ac_sub, 1$(not sameas(ac_sub,"acx"))) * s35_natveg_harvest_secdforest + (1-s35_natveg_harvest_secdforest));
```

Only assigns for age classes that are not "acx".

#### 1.3.2 Dollar on Right (Ternary-Like Behavior)

Assignment **always** occurs; assigns zero if condition is `FALSE`.

```gams
a = 2 $ (b > 1.5);  /* if b>1.5 then a=2, else a=0 */
```

**Multi-condition example**:
```gams
mur(i) = (1.0 + .0030*ied(i,'barge')) $ ied(i,'barge')
       + (0.5 + .0144*ied(i,'road'))  $ ied(i,'road');
```

Each term contributes only when its condition is true, summing the results.

### 1.4 Dollar in Indexed Operations

Restrict summation and aggregation using dollar conditions:

```gams
tsupc = sum(i $ (supc(i) <> inf), supc(i));        * Sum non-infinite values
y(r) = sum(s $ corr(r,s), income(s));              * Sum only correlated elements
```

**MAgPIE example** (`modules/70_livestock/fbask_jan16/presolve.gms:70`):
```gams
if (ord(t) = smax(t2, ord(t2)$(t_past(t2))) AND card(t) > sum(t_all$(t(t_all) and t_past(t_all)), 1),
```

The `sum(t_all$(t(t_all) and t_past(t_all)), 1)` counts timesteps that are both in `t` and `t_past`.

### 1.5 Dollar in Equations

#### 1.5.1 Within Equation Algebra

Dollar conditions on the right-hand side of the equation operator:

```gams
mb(i).. x(i) =g= y(i) + (e(i) - m(i)) $ t(i);
```

The term `(e(i) - m(i))` is included only if `t(i)` is TRUE (non-zero or set membership).

**MAgPIE example** (`modules/10_land/landmatrix_dec18/equations.gms:13`):
```gams
q10_land_from(j2,land_from) ..
    v10_lu_transitions(j2,land_from,"crop")
    =e=
    sum(land_to$(not sameas(land_from,land_to)),
        v10_lu_transitions(j2,land_from,land_to));
```

#### 1.5.2 Domain Restriction (Before ..)

Dollar before `..` restricts which constraint instances are generated:

```gams
gple(w,wp,te) $ ple(w,wp).. yw(w,te) - yw(wp,te) =l= dpack;
```

**Read as**: "Generate constraint `gple(w,wp,te)` only for combinations where `ple(w,wp)` is true."

**MAgPIE example** (`modules/32_forestry/dynamic_may24/preloop.gms:65`):
```gams
loop(ac$(ord(ac) > 1),
  p32_carbon_density_ac(t,j,"acx",ag_pools) = p32_carbon_density_ac(t,j,ac,ag_pools);
);
```

Loop executes only for age classes with ordinal position > 1.

### 1.6 Nested Dollar Conditions

```gams
u(i) $ (j(i)$k(i)) = v(i);  /* equivalent to: j(i) and k(i) */
```

**Recommendation**: Use explicit `and` for readability:
```gams
u(i) $ (j(i) and k(i)) = v(i);  /* Clearer */
```

### 1.7 Filtering Sets (Alternative to Dollar)

When conditions involve only set membership, **filtering** can replace dollar operators:

**Instead of**:
```gams
shipcost(i,j) $ r(i,j) = factor*distance(i,j);
```

**Use**:
```gams
shipcost(r) = factor*distance(r);  /* r is a subset of (i,j) */
```

This is cleaner when all indices appear consistently in the condition.

### 1.8 Common MAgPIE Dollar Patterns

#### Excluding Diagonal Elements
```gams
$(not sameas(land_from, land_to))    * Land transitions (no self-transitions)
$(not sameas(pollutants,"co2_c"))    * All pollutants except CO2
```

#### Time-Based Conditions
```gams
$(ord(t) = 1)                        * First timestep only
$(ord(t) > 1)                        * All except first timestep
$(t_past(t))                         * Historical period
$(m_year(t) > 2030)                  * After year 2030
```

#### Avoiding Division by Zero
```gams
result(i) $ (denom(i) <> 0) = num(i) / denom(i);
```

#### Set Membership Checks
```gams
value(i,j) $ cell(i,j) = ...         * Only for valid cell mappings
production(kcr) $ ...                * Only for crop products
```

### 1.9 Important Restrictions

**From GAMS documentation**:
1. **Variables not allowed**: Logical conditions cannot contain variables, only parameters, scalars, and variable attributes
2. **Extended-range values**: `inf` and `eps` in conditions evaluate as `TRUE`
3. **Set membership**: Limited to subsets and dynamic sets only
4. **ord() operator**: Works only with one-dimensional, static, ordered sets

### 1.10 Quick Reference

| Pattern | Meaning | Use Case |
|---------|---------|----------|
| `a $ b` | Execute if b ≠ 0 | Conditional assignment |
| `$(condition)` | Filter by condition | Restrict domains |
| `$(set(i))` | If i ∈ set | Set membership test |
| `$(not sameas(i,j))` | If i ≠ j | Exclude diagonal |
| `$(ord(t) = 1)` | First element | Initialization |
| `sum(i$(cond), x)` | Conditional sum | Filtered aggregation |

---

## 2. If-ElseIf-Else Statements

### 2.1 Overview

**Official GAMS Documentation**: "GAMS offers programming flow control features including the if statement for expressing complex conditional statements" ([UG_FlowControl](https://www.gams.com/latest/docs/UG_FlowControl.html))

The `if` statement provides **branching execution** around statements based on runtime conditions. More readable than dollar conditions for complex logic.

**Key restriction**: Only **execution statements** permitted—no declarations or equation definitions inside `if` blocks.

### 2.2 Basic Syntax

```gams
if (logical_condition,
    statement; {statement;}
);
```

**Example**:
```gams
if (f <= 0,
    p(i) = -1;
    q(j) = -1;
);
```

### 2.3 If-Else Structure

```gams
if (logical_condition,
    statement; {statement;}
else
    statement; {statement;}
);
```

**Example**:
```gams
if (f <= 0,
    p(i) = -1;
else
    p(i) = p(i)**3;
);
```

### 2.4 If-ElseIf-Else Chains

```gams
if (logical_condition1,
    statements1;
elseif logical_condition2,
    statements2;
elseif logical_condition3,
    statements3;
else
    statements4;
);
```

**Complete example**:
```gams
if (f <= 0,
    p(i) = -1;
    q(j) = -1;
elseif ((f > 0) and (f < 1)),
    p(i) = p(i)**2;
else
    p(i) = p(i)**3;
);
```

### 2.5 MAgPIE Examples

#### First Timestep Initialization

**Example** (`modules/17_production/flexreg_apr16/presolve.gms:13`):
```gams
if (ord(t) = 1,
  im_demandshare_reg.l(i,kall) = f17_prod_init(i,kall)/sum(i2,f17_prod_init(i2,kall));
);
```

Initializes regional demand shares only in the first timestep.

#### Historical-to-Projection Transition

**Example** (`modules/70_livestock/fbask_jan16/presolve.gms:69-75`):
```gams
if (ord(t) = smax(t2, ord(t2)$(t_past(t2))) AND card(t) > sum(t_all$(t(t_all) and t_past(t_all)), 1),
    p70_cattle_stock_proxy(t,i) =  im_pop(t,i)
                                  * pm_gdp_pc_ppp(t,i)
                                  / sum(i_to_iso(i,iso), im_pop_iso("y1995",iso))
                                  * sum(i_to_iso(i,iso), im_gdp_pc_ppp_iso("y1995",iso));
);
```

**Explanation**: At the transition from historical (`t_past`) to projection period, calculate cattle stock proxy based on population and GDP per capita.

**Breaking down the condition**:
- `ord(t) = smax(t2, ord(t2)$(t_past(t2)))` — Current timestep is the **last historical** timestep
- `card(t) > sum(t_all$(t(t_all) and t_past(t_all)), 1)` — There are timesteps **beyond** the historical period

#### Time-Conditional Parameter Updates

**Example** (`modules/70_livestock/fbask_jan16/presolve.gms:119-121`):
```gams
if (ord(t)>1,
  p70_cattle_stock_proxy(t,i) = p70_cattle_stock_proxy(t-1,i);
);
```

For all timesteps after the first, carry forward the previous value.

### 2.6 Nesting If Statements

If statements can be nested:

```gams
if (condition1,
    if (condition2,
        action_both_true;
    else
        action_1_true_2_false;
    );
else
    action_1_false;
);
```

**Recommendation**: For deep nesting, consider refactoring with intermediate flags or using dollar conditions.

### 2.7 When to Use If vs Dollar Conditions

| Use `if` statement when: | Use dollar `$` when: |
|--------------------------|----------------------|
| Multiple statements to execute | Single assignment or filter |
| Complex branching logic (elseif) | Simple condition |
| More readable for complex conditions | Inline filtering in equations |
| Scenario switches | Protecting against division by zero |
| Time-dependent initialization | Set-based restrictions |

**Example where if is clearer**:
```gams
if (scenario = 1,
    param_a = 100;
    param_b = 200;
    param_c = 300;
elseif scenario = 2,
    param_a = 150;
    param_b = 250;
    param_c = 350;
else
    abort "Unknown scenario";
);
```

**Example where dollar is clearer**:
```gams
value(i,j) $ (i <> j) = distance(i,j);  * Off-diagonal only
```

### 2.8 Common Patterns in MAgPIE

```gams
* First timestep initialization
if (ord(t) = 1,
    initialization_code;
);

* All timesteps after first
if (ord(t) > 1,
    normal_calculation;
);

* Last historical timestep transition
if (ord(t) = smax(t2, ord(t2)$(t_past(t2))),
    transition_logic;
);

* Scenario-based configuration
if (s_scenario = 1,
    scenario1_parameters;
elseif s_scenario = 2,
    scenario2_parameters;
else
    default_parameters;
);
```

---

## 3. Loop Statements

### 3.1 Overview

**Official GAMS Documentation**: "GAMS offers four loop constructs: the loop statement, the while statement, the for statement and the repeat statement" ([UG_FlowControl](https://www.gams.com/latest/docs/UG_FlowControl.html))

The `loop` statement is the **most common** iteration construct in MAgPIE, used for iterating over sets.

### 3.2 Basic Syntax

```gams
loop(index_list[$(logical_condition)],
     statement; {statement;}
);
```

**Key characteristics**:
- Executes statements for each member of the controlling set(s)
- Supports multiple controlling sets
- Allows dollar condition restrictions
- **Cannot modify controlling set inside loop body**

### 3.3 Simple Loop

**Example**:
```gams
loop(t,
    pop(t+1) = pop(t) + growth(t);
);
```

Calculates population recursively for each timestep.

**MAgPIE example** (`modules/13_tc/exo/preloop.gms:13`):
```gams
loop(t,
  im_technological_change(t,i,kcr) = f13_tcguess(t,i,kcr);
);
```

Loads technological change parameters for all timesteps.

### 3.4 Multi-Index Loops

Loop over multiple sets simultaneously:

```gams
loop((i,j),
    distance(i,j) = sqrt((x(i)-x(j))**2 + (y(i)-y(j))**2);
);
```

**MAgPIE example** (`modules/80_optimization/nlp_par/solve.gms:52-53`):
```gams
loop(i2,
    j2(j)$cell(i2,j) = yes;
);
```

For each region `i2`, activate cells `j` that belong to that region.

### 3.5 Nested Loops

```gams
loop(i,
    loop(j,
        matrix(i,j) = calculation(i,j);
    );
);
```

**MAgPIE example** (`modules/32_forestry/dynamic_may24/preloop.gms:65-67`):
```gams
loop(ac$(ord(ac) > 1),
  p32_carbon_density_ac(t,j,"acx",ag_pools) = p32_carbon_density_ac(t,j,ac,ag_pools);
);
```

Nested within an outer time loop, this copies carbon density for age classes with ordinal > 1.

### 3.6 Conditional Loop (Dollar Filter)

```gams
loop(i$(condition),
    statements;
);
```

**MAgPIE example** (`modules/56_ghg_policy/price_aug22/preloop.gms:82`):
```gams
loop(t_all$(m_year(t_all) > max(m_year("%c56_mute_ghgprices_until%"),s56_fader_start*s56_ghgprice_fader)),
    im_pollutant_prices(t_all,i,pollutants_ghgp) = ...;
);
```

Loop executes only for timesteps after a certain year threshold.

### 3.7 Dynamic Sets in Loops

The controlling set can be a dynamic subset:

```gams
set active(i);
active(i) = yes$(production(i) > threshold);

loop(active,
    process_active_regions;
);
```

**MAgPIE example** (`modules/80_optimization/nlp_par/solve.gms:46`):
```gams
loop(h$p80_handle(h),
    * Solve for this handle
);
```

Loop over handles that are flagged in the `p80_handle` parameter.

### 3.8 Common MAgPIE Loop Patterns

#### Time Loop (All Timesteps)
```gams
loop(t_all,
    parameter(t_all) = calculation;
);
```

#### Filtered Time Loop
```gams
loop(t$(m_year(t) > 2020),
    future_calculation;
);
```

#### Regional Loop
```gams
loop(i,
    regional_total(i) = sum(cell(i,j), cell_value(j));
);
```

#### Age Class Loop
```gams
loop(ac$(ord(ac) > 1),
    cohort_calculation;
);
```

### 3.9 Important Restrictions

**From GAMS documentation**:
1. **No set modification**: Cannot add/remove elements from controlling set inside loop
2. **No equation definitions**: Only execution statements allowed
3. **No declarations**: Cannot declare new entities inside loop

**Valid inside loops**:
- Assignments
- Display statements
- Solve statements
- Other control structures (if, nested loops)
- Put statements (output)

**Invalid inside loops**:
```gams
loop(i,
    parameters new_param;  * ERROR: Declaration not allowed
    equations new_eq;      * ERROR: Equation declaration not allowed
);
```

### 3.10 Performance Considerations

**Efficient**:
```gams
* Single vectorized assignment (GAMS optimizes this)
result(i,j) = data1(i) * data2(j);
```

**Less efficient**:
```gams
* Nested explicit loops (slower)
loop(i,
    loop(j,
        result(i,j) = data1(i) * data2(j);
    );
);
```

**Recommendation**: Use vectorized assignments when possible; reserve loops for truly iterative calculations.

---

## 4. While and Repeat Statements

### 4.1 While Statement

**Official GAMS Documentation**: "The while statement repeats the execution of a statement or statement block while a condition remains true" ([UG_FlowControl](https://www.gams.com/latest/docs/UG_FlowControl.html))

**Syntax**:
```gams
while(logical_condition,
      statement; {statement;}
);
```

**Characteristics**:
- Checks condition **before** each iteration
- May execute **zero times** if initially false
- Useful for convergence loops

**Example**:
```gams
scalar error;
error = 100;
while(error > 0.001,
    * Iterative calculation
    new_value = calculation();
    error = abs(new_value - old_value);
    old_value = new_value;
);
```

### 4.2 Numerical Stability in While Loops

**GAMS documentation warning**: "To ensure an exact result, in numerical comparisons we need a stable check...otherwise rounding errors may occur"

**Problem**:
```gams
while(i <> 2.6,  * May never be exactly 2.6 due to floating point
    i = i + 0.1;
);
```

**Solution**:
```gams
while(round(i,2) <> 2.6,  * Stable comparison
    i = i + 0.1;
);
```

### 4.3 Repeat Statement

**Syntax**:
```gams
repeat (
    statement; {statement;}
until logical_condition );
```

**Key difference**: Executes **at least once** before checking condition (post-test loop).

**Example**:
```gams
scalar a;
a = 0;
repeat (
    a = a + 1;
    display a;
until a = 5);
```

Displays values 1, 2, 3, 4, 5.

### 4.4 While vs Repeat

| while | repeat |
|-------|--------|
| Pre-test (condition first) | Post-test (condition last) |
| May execute 0 times | Always executes ≥ 1 time |
| `while(cond, ...)` | `repeat(...until cond)` |

**Use `while` when**: You might not need any iterations (e.g., already converged)

**Use `repeat` when**: You need at least one iteration (e.g., initialization + check)

### 4.5 Loop Limits

**GAMS documentation**: "The number of passes in a while statement may be restricted using the command line parameter or option forlim"

```gams
option forlim = 1000;  * Maximum 1000 iterations
```

**Safety**: Prevents infinite loops from hanging execution.

### 4.6 MAgPIE Usage

While and repeat loops are **less common** in MAgPIE than `loop` statements, but may appear in:
- Calibration procedures with convergence criteria
- Iterative solvers for nonlinear systems
- Multi-start optimization algorithms

**Pattern**:
```gams
scalar converged;
converged = 0;
while(converged = 0,
    solve model using nlp minimizing objective;
    if (model.solvestat = 1,
        converged = 1;
    );
    * Adjust parameters for next iteration
);
```

---

## 5. For Statements

### 5.1 Overview

**Syntax**:
```gams
for (a = start_value to|downto end_value [by incr],
     statement; {statement;}
);
```

**Characteristics**:
- Numeric iteration (not set-based)
- Default increment: 1
- `to` increases, `downto` decreases
- Increment must be positive

### 5.2 Basic For Loop

```gams
scalar s;
for (s = -3.8 to -0.1 by 1.4,
     display s;
);
```

**Output**: Displays s = -3.8, -2.4, -1.0

### 5.3 Downto (Decreasing)

```gams
for (k = 10 downto 1,
    value(k) = calculation;
);
```

Iterates k = 10, 9, 8, ..., 1

### 5.4 When to Use For vs Loop

| Use `for` when: | Use `loop` when: |
|-----------------|------------------|
| Numeric iteration with known range | Iterating over GAMS sets |
| Fixed start/stop/increment | Set-based domain |
| Simple counting | Multi-dimensional indices |
| Not tied to model structure | Working with model entities |

**For example**:
```gams
for (year = 2020 to 2050,
    projection(year) = baseline * (1 + growth_rate)**(year - 2020);
);
```

**Loop example** (more common in MAgPIE):
```gams
loop(t,
    projection(t) = baseline * (1 + growth_rate)**(m_year(t) - 2020);
);
```

### 5.5 MAgPIE Usage

`for` statements are **rare** in MAgPIE because most iteration is set-based. However, they might appear in:
- Testing/debugging scripts
- Report generation utilities
- Numeric experiments over parameter ranges

---

## 6. Break and Continue

### 6.1 Break Statement

**Official GAMS Documentation**: "The break statement terminates the execution of the n innermost control structures" ([UG_FlowControl](https://www.gams.com/latest/docs/UG_FlowControl.html))

**Syntax**:
```gams
break [n];
```

**Default**: `n = 1` (exit one loop)

### 6.2 Basic Break

```gams
loop(i,
    break$sameas('i6',i);
    cnt = cnt + 1;
);
```

**Explanation**: Exits loop when reaching element 'i6' (after processing 5 elements).

### 6.3 Break with Level

```gams
loop(i,
    loop(j,
        if (error_condition,
            break 2;  * Exit both i and j loops
        );
        process(i,j);
    );
);
```

### 6.4 Continue Statement

**Syntax**:
```gams
continue;
```

**Function**: Skips remaining statements in current iteration, proceeds to next iteration.

**Example**:
```gams
loop(i,
    continue$(mod(ord(i),2) = 0);  * Skip even-numbered elements
    cnt = cnt + 1;
);
```

Processes only odd ordinal positions.

### 6.5 Common Patterns

#### Early Exit on Convergence
```gams
loop(iter,
    solve model using nlp minimizing obj;
    break$(model.objval < tolerance);
);
```

#### Skipping Invalid Combinations
```gams
loop((i,j),
    continue$(not valid(i,j));
    process_valid_pair(i,j);
);
```

#### Search Loop
```gams
loop(candidate,
    if (meets_criteria(candidate),
        best = candidate;
        break;  * Found it, stop searching
    );
);
```

---

## 7. Abort Statements

### 7.1 Overview

**Official GAMS Documentation**: "The abort statement terminates program execution" ([UG_FlowControl](https://www.gams.com/latest/docs/UG_FlowControl.html))

**Purpose**: Halt execution with error message when validation fails.

**Syntax**:
```gams
abort [$(condition)] "message text" {, identifier};
abort.noError [$(condition)] "message text" {, identifier};
```

### 7.2 Basic Abort

```gams
if (parameter < 0,
    abort "Parameter must be non-negative", parameter;
);
```

Displays message and parameter value, then terminates with error.

### 7.3 Conditional Abort (Dollar Syntax)

```gams
abort$(condition) "Error message";
```

More compact than if-statement wrapper.

**Example**:
```gams
abort$(sum(i, production(i)) = 0) "Total production is zero";
```

### 7.4 Abort.noError

Terminates execution **without** setting error flag:

```gams
abort.noError$(scenario_flag = 0) "Scenario deactivated, skipping run";
```

Useful for conditional execution without marking as failed.

### 7.5 Displaying Values with Abort

```gams
abort$(total > threshold) "Threshold exceeded:", total, threshold;
```

Displays both message and identifier values before terminating.

### 7.6 MAgPIE Validation Patterns

#### Parameter Validation
```gams
abort$(s_scenario < 1 or s_scenario > 5) "Invalid scenario number", s_scenario;
```

#### Consistency Checks
```gams
abort$(sum(land, pm_land_start(j,land)) = 0) "No initial land allocation", j;
```

#### Solver Status Checks
```gams
solve model using nlp minimizing cost;
abort$(model.solvestat <> 1) "Model did not solve to optimality", model.solvestat;
```

### 7.7 Abort vs $abort

| `abort` statement | `$abort` dollar control |
|-------------------|-------------------------|
| Runtime (execution) | Compile-time |
| Checks calculated values | Checks static conditions |
| In normal code flow | Dollar control directive |
| After assignments | Before compilation completes |

**Example of $abort**:
```gams
$if not set scenario $abort "Scenario parameter must be set"
```

This checks at **compile-time** whether `scenario` was defined.

### 7.8 Best Practices

1. **Clear messages**: Explain what went wrong and what value is problematic
2. **Include values**: Display relevant identifiers to aid debugging
3. **Early validation**: Check preconditions before expensive operations
4. **Use conditionally**: Don't abort unnecessarily; allow normal error handling when appropriate
5. **Distinguish error types**: Use `.noError` for controlled exits vs actual errors

**Good abort message**:
```gams
abort$(pm_interest_rate(t,i) < 0)
    "Interest rate must be non-negative", t, i, pm_interest_rate;
```

**Poor abort message**:
```gams
abort$(error_flag) "Error";  * Too vague!
```

---

## Summary and Quick Reference

### Control Structure Comparison

| Structure | When to Use | Key Feature |
|-----------|-------------|-------------|
| **Dollar $** | Simple filtering, inline conditions | Compact, no multi-statement |
| **if/elseif/else** | Complex branching, multiple statements | Readable, scenario logic |
| **loop** | Iterate over sets | Most common in MAgPIE |
| **while** | Unknown iteration count, convergence | Pre-test condition |
| **repeat** | Need ≥1 iteration | Post-test condition |
| **for** | Numeric ranges | Simple counting |
| **break** | Early loop exit | Optimization, search |
| **continue** | Skip iteration | Filter within loop |
| **abort** | Validation failure | Error handling |

### Most Common in MAgPIE

1. **Dollar conditions** — Pervasive in equations, assignments, sums
2. **loop(t, ...)** — Time step iteration
3. **if (ord(t) = 1, ...)** — First-timestep initialization
4. **$(not sameas(...))** — Excluding diagonal/specific elements
5. **abort$(...)** — Parameter validation

### Mandatory Check Before Writing GAMS Code

**When working with complex GAMS control structures**:
1. ✅ Consult this Phase 2 documentation
2. ✅ Reference official GAMS docs for edge cases
3. ✅ Check MAgPIE examples in relevant modules
4. ✅ Verify syntax with similar existing code
5. ✅ Test edge cases (first timestep, empty sets, boundary conditions)

---

**Next Phase**: [Phase 3: Advanced Features](GAMS_Phase3_Advanced_Features.md) - Macros, dollar control options, variable attributes, set operations, and time indexing patterns.
