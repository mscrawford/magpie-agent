# GAMS Programming Reference - Phase 4: Functions & Operations

**Version**: 1.0 | **Status**: Complete | **Target Audience**: AI agents working with MAgPIE

**Purpose**: Reference guide for mathematical functions, logical operators, aggregation operations, and conditional assignments in GAMS.

**Prerequisites**: Phase 1 (Fundamentals) + Phase 2 (Control Structures)

**Official GAMS Documentation**:
- [Data Manipulations with Parameters](https://www.gams.com/latest/docs/UG_Parameters.html)
- [Conditional Expressions](https://www.gams.com/latest/docs/UG_CondExpr.html)
- [Extrinsic Functions](https://www.gams.com/latest/docs/UG_ExtrinsicFunctions.html)

---

## Table of Contents

1. [Mathematical Functions](#1-mathematical-functions)
2. [Logical Operators & Expressions](#2-logical-operators--expressions)
3. [Set Functions (ord, card, sameas)](#3-set-functions-ord-card-sameas)
4. [Aggregation (sum, prod, smin, smax)](#4-aggregation-sum-prod-smin-smax)
5. [Conditional Assignments](#5-conditional-assignments)

---

## 1. Mathematical Functions

### 1.1 Overview

**Official GAMS Documentation**: "GAMS provides many functions, ranging from commonly used standard functions like exponentiation, logarithms, and trigonometric functions to utility functions" ([UG_Parameters](https://www.gams.com/latest/docs/UG_Parameters.html))

GAMS supports a comprehensive set of mathematical functions for use in assignments, parameters, and equations.

### 1.2 Arithmetic Operators

| Operator | Meaning | Example | Result |
|----------|---------|---------|--------|
| `+` | Addition | `5 + 3` | `8` |
| `-` | Subtraction | `10 - 4` | `6` |
| `*` | Multiplication | `7 * 6` | `42` |
| `/` | Division | `20 / 4` | `5` |
| `**` | Exponentiation | `2**10` | `1024` |

**Precedence** (high to low):
1. `**` (exponentiation)
2. `*`, `/` (multiplication, division)
3. `+`, `-` (addition, subtraction)

**Parentheses**: Use `( )` to override precedence.

### 1.3 Standard Mathematical Functions

#### Exponential and Logarithmic

| Function | Description | Domain | Example |
|----------|-------------|--------|---------|
| `exp(x)` | Exponential (e^x) | All x | `exp(1)` = 2.71828 |
| `log(x)` | Natural logarithm (ln x) | x > 0 | `log(2.71828)` = 1 |
| `log10(x)` | Base-10 logarithm | x > 0 | `log10(100)` = 2 |
| `power(x,y)` | Integer power (x^y) | x ≥ 0 for y non-integer | `power(2,10)` = 1024 |

**MAgPIE usage** - Chapman-Richards growth function (`core/macros.gms:18`):
```gams
$macro m_growth_vegc(S,A,k,m,ac) S + (A-S)*(1-exp(-k*(ac*5)))**m
```

Uses `exp()` for exponential decay term.

#### Roots and Powers

| Function | Description | Example |
|----------|-------------|---------|
| `sqrt(x)` | Square root (√x) | `sqrt(16)` = 4 |
| `sqr(x)` | Square (x²) | `sqr(5)` = 25 |
| `power(x,y)` | General power | `power(3, 0.5)` = 1.732 |

**Protection pattern** (avoid negative sqrt):
```gams
result $ (value >= 0) = sqrt(value);
```

#### Absolute Value and Sign

| Function | Description | Example |
|----------|-------------|---------|
| `abs(x)` | Absolute value | `abs(-7)` = 7 |
| `sign(x)` | Sign (-1, 0, or 1) | `sign(-3.5)` = -1 |

**Common pattern** - Error calculation:
```gams
error = abs(observed - predicted);
relative_error = abs((observed - predicted) / observed) $ (observed <> 0);
```

#### Rounding Functions

| Function | Description | Example |
|----------|-------------|---------|
| `round(x)` | Round to nearest integer | `round(4.6)` = 5 |
| `round(x,n)` | Round to n decimal places | `round(3.14159, 2)` = 3.14 |
| `floor(x)` | Round down | `floor(4.9)` = 4 |
| `ceil(x)` | Round up | `ceil(4.1)` = 5 |
| `trunc(x)` | Truncate (toward zero) | `trunc(-4.9)` = -4 |

**Numerical stability** - Comparing floats:
```gams
* BAD: Direct comparison vulnerable to rounding
if (value = 2.6,  ...

* GOOD: Use round() for stable comparison
if (round(value, 2) = 2.6,  ...
```

#### Min and Max

| Function | Description | Example |
|----------|-------------|---------|
| `min(x,y,...)` | Minimum value | `min(3, 7, 2, 9)` = 2 |
| `max(x,y,...)` | Maximum value | `max(3, 7, 2, 9)` = 9 |

**Note**: For indexed min/max over sets, use `smin`/`smax` (see Section 4.4).

**Common pattern** - Bounds:
```gams
actual_value = max(lower_bound, min(upper_bound, calculated_value));
```

### 1.4 Trigonometric Functions

| Function | Description | Input (radians) |
|----------|-------------|-----------------|
| `sin(x)` | Sine | radians |
| `cos(x)` | Cosine | radians |
| `tan(x)` | Tangent | radians |
| `arcsin(x)` | Arc sine | -1 ≤ x ≤ 1 |
| `arccos(x)` | Arc cosine | -1 ≤ x ≤ 1 |
| `arctan(x)` | Arc tangent | all x |
| `arctan2(y,x)` | Two-argument arc tangent | all x,y |

**Conversion**:
```gams
scalar pi;
pi = arctan(1) * 4;  * π = 3.14159...

degrees_to_radians = pi / 180;
radians_to_degrees = 180 / pi;
```

**Less common in MAgPIE** (agricultural model doesn't use much trigonometry).

### 1.5 Special Functions

#### Modulo

| Function | Description | Example |
|----------|-------------|---------|
| `mod(x,y)` | Remainder of x/y | `mod(17, 5)` = 2 |

**Pattern** - Even/odd check:
```gams
loop(i,
    continue$(mod(ord(i), 2) = 0);  * Skip even ordinals
    process_odd(i);
);
```

#### Error Function

| Function | Description |
|----------|-------------|
| `errorf(x)` | Error function |

**Rarely used** in typical optimization models.

### 1.6 Division by Zero Protection

**Problem**: Division by zero causes execution error.

**Solutions**:

**1. Dollar condition** (left-side):
```gams
result(i) $ (denominator(i) <> 0) = numerator(i) / denominator(i);
```

If denominator is zero, `result(i)` is not assigned (stays at default 0).

**2. Small epsilon**:
```gams
result(i) = numerator(i) / (denominator(i) + 1e-10);
```

**3. Conditional expression** (right-side):
```gams
result(i) = (numerator(i) / denominator(i)) $ (denominator(i) <> 0);
```

If denominator is zero, assigns 0 (from false condition).

**MAgPIE pattern** (`core/macros.gms:16`):
```gams
$macro m_weightedmean(x,w,s) (sum(s,x*w)/sum(s,w))$(sum(s,w)>0) + 0$(sum(s,w)<=0)
```

Returns 0 if total weight is zero.

### 1.7 Function Nesting

Functions can be nested:

```gams
result = sqrt(abs(value));                   * Nested: sqrt(abs())
growth = exp(-k * t**2);                     * Multiple functions
distance = sqrt(sqr(x2-x1) + sqr(y2-y1));    * Euclidean distance
```

**Readability tip**: For deep nesting, use intermediate parameters:

**Less readable**:
```gams
final = exp(-sqrt(abs(a*b + c*d) / (e*f + 1e-10)));
```

**More readable**:
```gams
param1 = a*b + c*d;
param2 = e*f + 1e-10;
param3 = abs(param1) / param2;
param4 = sqrt(param3);
final = exp(-param4);
```

---

## 2. Logical Operators & Expressions

### 2.1 Overview

**Official GAMS Documentation**: "Logical conditions are special expressions that evaluate to either TRUE or FALSE" ([UG_CondExpr](https://www.gams.com/latest/docs/UG_CondExpr.html))

**Numerical interpretation**: `0` = FALSE, non-zero = TRUE.

### 2.2 Comparison Operators

| Operator | Meaning | Alternative | Example |
|----------|---------|-------------|---------|
| `<` | Less than | `lt` | `x < 10` |
| `<=` | Less than or equal | `le` | `x <= 10` |
| `=` | Equal | `eq` | `x = 5` |
| `<>` | Not equal | `ne` | `x <> 0` |
| `>=` | Greater than or equal | `ge` | `x >= 0` |
| `>` | Greater than | `gt` | `x > 100` |

**Note**: `=` is both assignment AND comparison (context-dependent).

### 2.3 Logical Operators

| Operator | Meaning | Truth Table |
|----------|---------|-------------|
| `not x` | Negation | TRUE if x is FALSE |
| `x and y` | Conjunction | TRUE if both TRUE |
| `x or y` | Disjunction | TRUE if at least one TRUE |
| `x xor y` | Exclusive OR | TRUE if exactly one TRUE |
| `x imp y` | Implication | FALSE only if x=TRUE and y=FALSE |
| `x eqv y` | Equivalence | TRUE if both same value |

**Truth table** (for `and`, `or`, `not`):

| x | y | not x | x and y | x or y | x xor y |
|---|---|-------|---------|--------|---------|
| F | F | T | F | F | F |
| F | T | T | F | T | T |
| T | F | F | F | T | T |
| T | T | F | T | T | F |

### 2.4 Compound Conditions

```gams
* Multiple conditions with and/or
if ((temperature > 30 and rainfall < 50) or irrigation_available,
    drought_stress = yes;
);

* Using not
active(i) $ (not excluded(i)) = yes;

* Parentheses for clarity
result = (a > 0 and b > 0) or (c < 10 and d < 10);
```

**MAgPIE example** (`modules/56_ghg_policy/price_aug22/preloop.gms:82`):
```gams
loop(t_all$(m_year(t_all) > max(m_year("%c56_mute_ghgprices_until%"),
                                 s56_fader_start*s56_ghgprice_fader)),
    ...
);
```

Complex condition: year must exceed maximum of two thresholds.

### 2.5 Short-Circuit Evaluation

**WARNING**: GAMS does **not** short-circuit logical expressions.

**In other languages** (C, Python):
```python
if (x != 0 and y/x > 10):  # x!=0 checked first, safe
```

**In GAMS** (NOT SAFE):
```gams
if ((x <> 0) and (y/x > 10),  * DANGER: y/x evaluated even if x=0
```

**Solution** - Use nested if or dollar:
```gams
* Safe version 1: Nested if
if (x <> 0,
    if (y/x > 10,
        action;
    );
);

* Safe version 2: Separate dollar conditions
action$(x <> 0)$(y/x > 10);
```

### 2.6 Numerical Interpretation

```gams
scalar flag;
flag = 5;

if (flag,         * TRUE because flag = 5 (non-zero)
    display "Flag is true";
);

flag = 0;
if (flag,         * FALSE because flag = 0
    display "This won't display";
);
```

**Common pattern** - Using 1/0 as TRUE/FALSE:
```gams
parameter is_active(i);
is_active(i) = 1$(production(i) > 0);  * 1 if producing, 0 otherwise

if (is_active(i),
    process_active(i);
);
```

---

## 3. Set Functions (ord, card, sameas)

### 3.1 Overview

**Set functions** query properties of sets and elements. Covered extensively in Phase 3, summarized here for reference.

### 3.2 ord(element) - Ordinal Position

**Purpose**: Position in ordered, one-dimensional set (1-indexed).

**Syntax**: `ord(element)`

**Requirements**:
- Set must be **ordered** (not dynamic multi-dimensional)
- Set must be **one-dimensional**

**Examples**:
```gams
if (ord(t) = 1,                    * First timestep
if (ord(i) = card(i),              * Last element
if (ord(ac) > 1 and ord(ac) < card(ac),  * Interior elements
```

**MAgPIE pattern** - Lag operator with ord:
```gams
if (ord(t) > 1,
    value(t) = value(t-1) * growth;
);
```

### 3.3 card(set) - Cardinality

**Purpose**: Number of elements in set.

**Syntax**: `card(set_name)`

**Examples**:
```gams
scalar num_regions, num_timesteps;
num_regions = card(i);
num_timesteps = card(t);

* Check if set is empty
if (card(active_cells) = 0,
    abort "No active cells!";
);

* Last element
if (ord(t) = card(t),
    final_reporting;
);
```

### 3.4 sameas(element1, element2) - Identity Check

**Purpose**: Test if two elements refer to same set member.

**Syntax**: `sameas(set1, set2)` or `sameas(element1, element2)`

**Returns**: `TRUE` (1) if identical, `FALSE` (0) otherwise.

**Examples**:
```gams
* Diagonal of matrix
transition(land, land)$sameas(land, land) = retention_rate;

* Off-diagonal
transition(land_from, land_to)$(not sameas(land_from, land_to)) = conversion_rate;

* Specific element
if (sameas(scenario, "SSP2"),
    baseline_scenario = yes;
);
```

**MAgPIE example** (`modules/10_land/landmatrix_dec18/equations.gms:32`):
```gams
sum(land_to$(not sameas(land_from,land_to)),
    v10_lu_transitions(j2,land_from,land_to))
```

### 3.5 diag(element1, element2) - Numeric Identity

**Purpose**: Returns **numeric value** (1 if same, 0 if different).

**Syntax**: `diag(element1, element2)`

**Difference from sameas**: `diag` returns number, `sameas` returns boolean.

```gams
* Using diag for weighted sum
weighted_sum = sum((i,j), value(i,j) * diag(i,j));  * Diagonal elements only
```

### 3.6 smin / smax - Set Minimum/Maximum

**Purpose**: Find min/max value over set (with selection).

**Covered in Section 4.4** below.

---

## 4. Aggregation (sum, prod, smin, smax)

### 4.1 Overview

**Official GAMS Documentation**: "The indexed operators available are: sum, prod, smin, smax" ([UG_Parameters](https://www.gams.com/latest/docs/UG_Parameters.html))

**Indexed operations** aggregate values over sets.

### 4.2 sum - Summation

**Syntax**:
```gams
sum(index_set, expression)
sum((index1, index2, ...), expression)
```

**Official**: "The index is separated from the reserved word sum by a left parenthesis and from the data term by a comma" ([UG_Parameters](https://www.gams.com/latest/docs/UG_Parameters.html))

#### Single Index Sum

```gams
total_population = sum(i, population(i));
total_land = sum(land, area(land));
```

**MAgPIE example** (`modules/10_land/landmatrix_dec18/equations.gms:14`):
```gams
sum(land, vm_land(j2,land)) =e= sum(land, pcm_land(j2,land));
```

Land conservation: total land area remains constant.

#### Multi-Index Sum

```gams
global_production = sum((i,k), production(i,k));
```

**Parentheses required** for multiple indices.

#### Conditional Sum (Dollar Filter)

```gams
sum(index$(condition), expression)
```

**Example**:
```gams
* Sum only positive values
total_positive = sum(i$(value(i) > 0), value(i));

* Sum specific subset
crop_area = sum(land$(crop_types(land)), area(land));

* Complex condition
future_total = sum(t$(m_year(t) > 2030 and m_year(t) <= 2050), annual_value(t));
```

**MAgPIE example** (`modules/10_land/landmatrix_dec18/equations.gms:32`):
```gams
sum(land_from$(not sameas(land_from,land_to)),
    v10_lu_transitions(j2,land_from,land_to))
```

Sum transitions **except** self-transitions.

#### Nested Sums

```gams
* Regional then product aggregation
global_total = sum(i, sum(k, production(i,k)));

* Equivalent single multi-index sum
global_total = sum((i,k), production(i,k));
```

**Performance**: Multi-index sum (single call) usually faster than nested.

### 4.3 prod - Product

**Syntax**: Identical to `sum`, but multiplies instead of adds.

```gams
prod(index_set, expression)
```

**Example**:
```gams
* Total factor productivity
tfp = prod(factor, efficiency(factor));

* Compound growth
final_value = initial * prod(t, (1 + growth_rate(t)));
```

**Less common** than `sum` in typical models.

### 4.4 smin / smax - Set Min/Max

**Purpose**: Find minimum or maximum value over set (and identify which element).

**Official**: "The smin and smax operations are used to find the largest and smallest values over the domain of the index set or sets" ([Smin, Smax](https://www.gams.com/mccarlGuide/smin__smax.htm))

**Syntax**:
```gams
smin(index_set, expression)
smax(index_set, expression)
```

**Difference from min/max functions**:
- `min(a,b,c)` - Compares **fixed list** of values
- `smin(i, value(i))` - Scans **set** to find minimum

#### Basic smin/smax

```gams
* Find minimum value in set
min_cost = smin(i, cost(i));

* Find maximum
max_yield = smax(k, yield(k));
```

#### With Conditional

```gams
* Find max only among active regions
max_active = smax(i$(active(i)), production(i));

* Find last historical year
last_hist_year = smax(t$(t_past(t)), m_year(t));

* Find minimum non-zero value
min_nonzero = smin(i$(value(i) > 0), value(i));
```

**MAgPIE example** - Last historical timestep ordinal:
```gams
smax(t2, ord(t2)$(t_past(t2)))
```

#### Multi-Index smin/smax

```gams
* Find maximum across two dimensions
global_max = smax((i,k), production(i,k));

* Find minimum with complex condition
min_cost = smin((i,tech)$(available(i,tech) and cost(i,tech) > 0), cost(i,tech));
```

#### Important Restriction (Equations)

**Official**: "The indexed operations smin and smax may be used in equation definitions only if the corresponding model is of type DNLP" ([UG_Parameters](https://www.gams.com/latest/docs/UG_Parameters.html))

**DNLP** = Discontinuous Nonlinear Programming

**Workaround for LP/NLP**: Calculate in `presolve.gms` and use parameter:
```gams
* In presolve.gms
parameter p_max_yield(i);
p_max_yield(i) = smax(k, yield(i,k));

* In equations.gms (use parameter, not smax)
q_constraint(i).. vm_production(i) =l= p_max_yield(i);
```

### 4.5 Aggregation Patterns in MAgPIE

#### Regional Aggregation

```gams
* Cell-level to region-level
regional_value(i) = sum(cell(i,j), cell_value(j));
```

#### Product Aggregation

```gams
* All crops
total_crop_area = sum(kcr, cropland(kcr));

* Specific categories
cereal_production = sum(kcr_cereals, production(kcr_cereals));
```

#### Time Aggregation

```gams
* Cumulative over time
cumulative(t) = sum(t2$(ord(t2) <= ord(t)), annual(t2));

* Average over period
average = sum(t, value(t)) / card(t);
```

#### Weighted Aggregation

```gams
* Weighted average using macro
avg_yield = m_weightedmean(yield(i,j), area(i,j), (i,j));

* Manual weighted sum
weighted_avg = sum(i, value(i) * weight(i)) / sum(i, weight(i));
```

---

## 5. Conditional Assignments

### 5.1 Overview

**Conditional assignments** combine assignment with logical conditions using the dollar operator.

**Official**: "Exceptions may easily be modeled with a logical condition combined with the dollar operator '$'" ([UG_CondExpr](https://www.gams.com/latest/docs/UG_CondExpr.html))

### 5.2 Dollar on Left (Conditional Assignment)

**Syntax**: `parameter(indices) $ (condition) = expression;`

**Behavior**: Assigns **only if** condition is TRUE. Otherwise, parameter is **not modified**.

```gams
* Assign only for positive denominator
ratio(i) $ (denom(i) > 0) = numer(i) / denom(i);
* If denom(i) <= 0, ratio(i) is unchanged (default 0)

* Assign only for specific elements
value(i) $ sameas(i, "USA") = special_value;
* Only USA gets assigned, others unchanged

* Multiple conditions
adjusted(i,j) $ (active(i) and valid(j)) = base(i,j) * factor;
```

**Use when**: Want to preserve existing values for excluded cases.

### 5.3 Dollar on Right (Ternary-Like)

**Syntax**: `parameter = expression1 $ (condition) + expression2 $ (not condition);`

**Behavior**: Assignment **always** occurs. Expression evaluates to zero if condition is FALSE.

```gams
* If-else using dollar
result = value1 $ (x > 0) + value2 $ (x <= 0);
* Equivalent to: if x>0 then value1 else value2

* Simple conditional value
flag = 1 $ (production > threshold) + 0 $ (production <= threshold);
* Simplifies to:
flag = 1 $ (production > threshold);  * Implicit + 0 when false
```

**Use when**: Always want assignment (with zero as fallback).

### 5.4 Simulating If-Else

**Pattern**: Multiple conditional terms sum to create if-elseif-else behavior.

```gams
* If-elseif-else structure
category(i) = 1 $ (value(i) < 10)
            + 2 $ (value(i) >= 10 and value(i) < 20)
            + 3 $ (value(i) >= 20);
```

**Explanation**: Exactly one condition is TRUE for each `i`, so result is the corresponding number.

**More complex**:
```gams
* Piecewise function
cost(x) = (10*x) $ (x <= 100)
        + (1000 + 8*x) $ (x > 100 and x <= 500)
        + (4200 + 5*x) $ (x > 500);
```

### 5.5 Protecting Against Edge Cases

#### Division by Zero

```gams
* Method 1: Left dollar (no assignment if zero)
result(i) $ (denom(i) <> 0) = numer(i) / denom(i);

* Method 2: Right dollar (assigns zero if zero denom)
result(i) = (numer(i) / denom(i)) $ (denom(i) <> 0);

* Method 3: Epsilon (always assigns, avoids division)
result(i) = numer(i) / (denom(i) + 1e-10);
```

#### Logarithm of Zero or Negative

```gams
* Left dollar
log_value(i) $ (value(i) > 0) = log(value(i));

* Right dollar
log_value(i) = log(value(i)) $ (value(i) > 0);  * Zero if value <= 0
```

#### Square Root of Negative

```gams
* Left dollar
sqrt_value(i) $ (value(i) >= 0) = sqrt(value(i));

* With abs for safety
safe_sqrt(i) = sqrt(abs(value(i)));
```

### 5.6 Set Assignment (Yes/No)

**Dynamic sets** use conditional assignment:

```gams
set active(i);

* Set membership based on condition
active(i) = yes $ (production(i) > threshold);
* Equivalent to:
active(i)$(production(i) > threshold) = yes;

* Clear set
active(i) = no;

* Conditional clearing
active(i)$(production(i) = 0) = no;
```

### 5.7 Multi-Dimensional Conditionals

```gams
* Conditional on multiple indices
valid(i,j) = yes $ (distance(i,j) < max_dist and cost(i,j) < budget);

* Assignment with multi-index condition
flow(i,j) $ (connected(i,j) and capacity(i,j) > 0) = demand(j);
```

### 5.8 Combining with Aggregation

```gams
* Conditional sum in assignment
total_active = sum(i, production(i) $ (active(i)));
* Equivalent to:
total_active = sum(i$(active(i)), production(i));

* Right-side conditional in aggregation
avg_positive = sum(i, value(i)$(value(i) > 0)) / sum(i, 1$(value(i) > 0));
```

---

## Summary and Quick Reference

### Function Categories

| Category | Functions | Common Use |
|----------|-----------|------------|
| **Exponential/Log** | exp, log, log10, power | Growth, decay, elasticity |
| **Roots/Powers** | sqrt, sqr, power | Distances, areas, CES functions |
| **Absolute/Sign** | abs, sign | Errors, deviations |
| **Rounding** | round, floor, ceil, trunc | Numerical stability, integers |
| **Min/Max** | min, max | Bounds, constraints |
| **Trig** | sin, cos, tan, arctan | Geometry (rare in MAgPIE) |
| **Modulo** | mod | Cyclical patterns, parity |

### Aggregation Operators

| Operator | Purpose | Returns |
|----------|---------|---------|
| `sum` | Add over set | Sum of values |
| `prod` | Multiply over set | Product of values |
| `smin` | Find minimum | Minimum value |
| `smax` | Find maximum | Maximum value |

### Set Functions

| Function | Purpose | Returns |
|----------|---------|---------|
| `ord(i)` | Position in set | Integer (1-indexed) |
| `card(set)` | Set size | Number of elements |
| `sameas(i,j)` | Identity test | TRUE/FALSE |
| `diag(i,j)` | Numeric identity | 1 or 0 |

### Logical Operators

| Operator | Meaning | Usage |
|----------|---------|-------|
| `not` | Negation | `not active(i)` |
| `and` | Both true | `x > 0 and y > 0` |
| `or` | At least one true | `error or warning` |
| `xor` | Exactly one true | `a xor b` |

### Dollar Condition Patterns

| Pattern | Meaning | Example |
|---------|---------|---------|
| `p(i)$(cond)` | Assign if true | `value(i)$(x>0) = y` |
| `p = x$(cond)` | Value or zero | `flag = 1$(active)` |
| `sum(i$(cond),x)` | Conditional aggregation | `sum(i$(i>10),v(i))` |

### Protection Patterns

```gams
* Division by zero
result $ (denom <> 0) = numer / denom;
result = numer / (denom + 1e-10);

* Logarithm
log_val $ (x > 0) = log(x);

* Square root
sqrt_val $ (x >= 0) = sqrt(x);

* Numerical comparison
if (round(value, 6) = target, ...
```

### When to Consult This Phase

**Use Phase 4 when**:
- Writing complex mathematical expressions
- Implementing growth functions, production functions
- Performing aggregations (regional, product, temporal)
- Protecting against numerical errors
- Simulating if-else logic with dollars
- Finding min/max over sets

**Common MAgPIE Patterns**:
- `exp()` in growth functions
- `sum()` for regional/product aggregation
- `smax()` for finding last timestep
- Dollar conditions for division protection
- `abs()` for error calculations

---

**Next Phase**: [Phase 5: MAgPIE-Specific Patterns](GAMS_Phase5_MAgPIE_Patterns.md) - Module structure, interface variables, time management, calibration, and common MAgPIE idioms.
