# GAMS Programming Reference - Phase 6: Best Practices

**Version**: 1.0 | **Status**: Complete | **Target Audience**: AI agents working with MAgPIE

**Purpose**: Practical guidance for writing robust, efficient, and maintainable GAMS code.

**Prerequisites**: Phases 1-5 (Fundamentals through MAgPIE Patterns)

**Official GAMS Documentation**:
- [Good NLP Formulations](https://www.gams.com/latest/docs/UG_NLP_GoodFormulations.html)
- [Finding and Fixing Execution Errors](https://www.gams.com/latest/docs/UG_ExecErrPerformance.html)

---

## Table of Contents

1. [Model Scaling & Units](#1-model-scaling--units)
2. [Numerical Stability](#2-numerical-stability)
3. [Performance Optimization](#3-performance-optimization)
4. [Debugging Strategies](#4-debugging-strategies)
5. [Common Pitfalls & Solutions](#5-common-pitfalls--solutions)

---

## 1. Model Scaling & Units

### 1.1 Why Scaling Matters

**Official**: "Poorly scaled models can cause excessive time to be taken in solving or can cause the solver to fail" ([UG_ExecErrPerformance](https://www.gams.com/latest/docs/UG_ExecErrPerformance.html))

**Problem**: Solvers work with floating-point arithmetic. If model coefficients vary by many orders of magnitude (e.g., 1e-10 to 1e+10), numerical precision suffers.

**Impact**:
- Slower convergence
- Solver failure (infeasibility reports when feasible solution exists)
- Incorrect solutions
- Poor marginal values

### 1.2 Good Unit Choices

**Guideline**: "Units should be chosen to a scale such that numerical values encountered by the optimizer have relatively small absolute orders of magnitude" ([Best Practices](https://pascua.iit.comillas.edu/aramos/simio/transpa/s_GoodOptimizationModelingPractices.pdf))

**Target range**: Keep coefficients and variable values between **0.01 and 1000**.

#### MAgPIE Unit Choices (Well-Scaled)

| Quantity | Unit | Typical Values |
|----------|------|----------------|
| Land area | Million hectares (mio. ha) | 0.01 - 100 |
| Costs | Million USD (mio. USD17MER) | 1 - 10,000 |
| Production | Million tons (mio. t) | 0.1 - 1,000 |
| Population | Million people (mio.) | 1 - 1,500 |
| Prices | USD/ton | 100 - 10,000 |

**Bad example** (poorly scaled):
```gams
* Land in square meters (values like 50,000,000,000)
variables vm_land_sqm(j);

* Cost in cents (values like 100,000,000,000)
variables vm_cost_cents;
```

**Good example** (well-scaled):
```gams
* Land in million hectares (values like 50)
positive variables vm_land(j,land);

* Cost in million USD (values like 1,000)
variables vm_cost_glo;
```

### 1.3 Scaling Variables

**GAMS scaling option**: `.scale` attribute

**Usage**:
```gams
* Variable with very large values
vm_large_number.scale = 1e6;  * Internally divide by 1 million
```

**Effect**: Solver sees `vm_large_number / 1e6`, improving numerical properties.

**Activate scaling**:
```gams
model.scaleopt = 1;  * Enable scaling
```

### 1.4 Checking Scaling

**Display model statistics**:
```gams
option limrow = 10;    * Show first 10 rows
option limcol = 10;    * Show first 10 columns
solve model using nlp minimizing objective;
```

**Review listing file** for:
- Very large or very small coefficients
- Matrix statistics (condition number)
- Range of variable bounds

**Danger signs**:
- Coefficients > 1e6 or < 1e-6
- Variable bounds spanning 10+ orders of magnitude

---

## 2. Numerical Stability

### 2.1 Division by Zero Protection

**Always protect division** operations:

**Method 1: Left dollar** (no assignment if zero):
```gams
ratio(i) $ (denom(i) <> 0) = numer(i) / denom(i);
```

**Method 2: Small epsilon**:
```gams
ratio(i) = numer(i) / (denom(i) + 1e-10);
```

**Method 3: Conditional expression**:
```gams
ratio(i) = (numer(i) / denom(i)) $ (denom(i) <> 0);
```

**MAgPIE pattern** (weighted mean with protection):
```gams
$macro m_weightedmean(x,w,s) (sum(s,x*w)/sum(s,w))$(sum(s,w)>0) + 0$(sum(s,w)<=0)
```

### 2.2 Logarithm and Root Protection

**Logarithm**: Domain is x > 0

```gams
* Protect with dollar condition
log_value(i) $ (value(i) > 0) = log(value(i));

* Or use max to ensure positivity
log_value(i) = log(max(value(i), 1e-10));
```

**Square root**: Domain is x ≥ 0

```gams
* Protect with condition
sqrt_value(i) $ (value(i) >= 0) = sqrt(value(i));

* Or use abs
sqrt_value(i) = sqrt(abs(value(i)));
```

### 2.3 Variable Bounds

**Official**: "The best way to avoid evaluating functions outside their domain of definition is to specify reasonable variable bounds" ([UG_NLP_GoodFormulations](https://www.gams.com/latest/docs/UG_NLP_GoodFormulations.html))

**Always set realistic bounds**:

**Bad** (unbounded):
```gams
positive variables vm_production(j,k);
* No upper bound → solver may explore unrealistic values
```

**Good** (bounded):
```gams
positive variables vm_production(j,k);
vm_production.up(j,k) = max_possible_production(j,k);
vm_production.lo(j,k) = min_required_production(j,k);
```

**Benefits**:
- Faster convergence (smaller search space)
- Avoid domain errors
- Improve numerical conditioning

### 2.4 Avoiding Extreme Values

**Problem**: Variables reaching very large or very small values.

**Solutions**:

**1. Reformulate constraints**:

**Bad**:
```gams
* Forces variable to become very large
constraint.. vm_big_number =g= 1e10;
```

**Good**:
```gams
* Rescale the constraint
constraint.. vm_scaled_number =g= 10;
* Where vm_scaled_number = vm_big_number / 1e9
```

**2. Use logs for exponential variables**:

**Bad**:
```gams
* Exponential growth creates huge numbers
vm_gdp(t+1) = vm_gdp(t) * (1 + growth_rate)**years;
```

**Good**:
```gams
* Work in log space
vm_log_gdp(t+1) = vm_log_gdp(t) + log(1 + growth_rate) * years;
* Then: vm_gdp = exp(vm_log_gdp)
```

### 2.5 Rounding for Comparisons

**Problem**: Floating-point equality comparisons unreliable.

**Bad**:
```gams
while(counter <> 2.6,  * May never equal exactly due to rounding
    counter = counter + 0.1;
);
```

**Good**:
```gams
while(round(counter, 2) <> 2.6,  * Stable comparison
    counter = counter + 0.1;
);
```

**Tolerance-based comparison**:
```gams
scalar tolerance / 1e-6 /;

if (abs(value - target) < tolerance,
    * Treat as equal
);
```

---

## 3. Performance Optimization

### 3.1 Model Size Reduction

**Smaller models solve faster**.

#### Tighter Set Definitions

**Bad** (large domain):
```gams
* All possible (i,j,k) combinations
sum((i,j,k), production(i,j,k))
```

**Good** (restricted domain):
```gams
* Only valid combinations
set valid(i,j,k);
valid(i,j,k) = yes$(production_possible(i,j,k));

sum(valid(i,j,k), production(i,j,k))
```

#### Equation Filtering

**Bad** (generate all):
```gams
equation q_example(i,j,k);
q_example(i,j,k).. ...;
* Generates constraints for all (i,j,k) even if many are redundant
```

**Good** (filter domain):
```gams
equation q_example(i,j,k);
q_example(valid(i,j,k)).. ...;
* Generates only necessary constraints
```

### 3.2 Vectorization

**Vectorize operations** instead of explicit loops:

**Slow** (explicit nested loops):
```gams
loop(i,
    loop(j,
        result(i,j) = data1(i) * data2(j);
    );
);
```

**Fast** (vectorized):
```gams
result(i,j) = data1(i) * data2(j);
* GAMS optimizes this internally
```

### 3.3 Warm Starts

**Official**: "It's recommended to specify as many sensible initial values for nonlinear variables as possible" ([UG_NLP_GoodFormulations](https://www.gams.com/latest/docs/UG_NLP_GoodFormulations.html))

**Initialize variables** before solve:

**No warm start** (solver picks default, often 0):
```gams
solve model using nlp minimizing cost;
* May take many iterations
```

**With warm start**:
```gams
* Set reasonable initial values
vm_production.l(j,k) = historical_production(j,k);
vm_land.l(j,land) = initial_land(j,land);

solve model using nlp minimizing cost;
* Converges faster from good starting point
```

**MAgPIE pattern**: Use previous timestep solution:
```gams
vm_land.l(j,land) = pcm_land(j,land);  * Previous solution
```

### 3.4 Solver Selection

Different solvers have different strengths:

**For MAgPIE (NLP)**:
- CONOPT - Good for sparse, large-scale NLP
- IPOPT - Interior point method, handles large models
- SNOPT - Sequential quadratic programming

**Test alternative solvers**:
```gams
option nlp = conopt;   * Default
solve model using nlp minimizing cost;

* OR
option nlp = ipopt;
solve model using nlp minimizing cost;
```

**Solver tuning** (for MIP):
```gams
* Use Cplex tuning tool
option mip = cplex;
option tuning = 1;
solve model using mip minimizing cost;
```

### 3.5 Sparsity

**Exploit sparsity** in large models:

**Dense** (inefficient):
```gams
* Creates entries for all (i,j) pairs
parameter distance(i,j);
distance(i,j) = calculation(i,j);
* Even if many are zero
```

**Sparse** (efficient):
```gams
* Only create non-zero entries
parameter distance(i,j);
distance(i,j)$(i <> j) = calculation(i,j);
* Zeros not stored, saves memory
```

---

## 4. Debugging Strategies

### 4.1 Compilation Errors

**Common syntax errors**:

**Missing semicolon**:
```gams
parameter a, b, c
parameter d, e, f;  * ERROR: Missing ; after line 1
```

**Forward reference** (using before declaring):
```gams
a = b + c;         * ERROR: b and c not declared yet
parameters b, c;   * Too late!
```

**Wrong set dimensions**:
```gams
parameter value(i,j);
value(i) = 10;     * ERROR: Declared with (i,j), used with (i)
```

### 4.2 Execution Errors

#### Infeasibility Diagnosis

**Official**: "Search the solution for equations that are infeasible (INFES)" ([UG_ExecErrPerformance](https://www.gams.com/latest/docs/UG_ExecErrPerformance.html))

**Steps**:

**1. Check solve status**:
```gams
solve model using nlp minimizing cost;

if (model.solvestat <> 1,
    display "Solve failed with status:", model.solvestat;
    abort "Model infeasible or unsolved";
);
```

**2. Display infeasible equations**:
```gams
option limrow = 0;      * Show all infeasible equations
option limcol = 0;      * Show all nonoptimal variables
```

**Check listing file** for equations marked `INFES`.

**3. Identify problematic constraints**:
```gams
* In postsolve.gms, check equation levels
parameter infeas_report(equation_name);

infeas_report("q10_land_area") = q10_land_area.l("cell_123");
display "Equation levels:", infeas_report;
```

#### Domain Violations

**Error**: "Function evaluation outside domain"

**Cause**: sqrt(negative), log(zero or negative), division by zero

**Solution**: Add bounds and protections:
```gams
* Ensure variables stay positive for log
vm_positive_var.lo(i) = 1e-6;

* Protect division
result $ (denom <> 0) = numer / denom;
```

### 4.3 Display Statements

**Use display** to inspect values:

```gams
* Display parameter values
display pm_land_start;

* Display variable levels
display vm_land.l;

* Display equation marginals
display q10_land_area.m;

* Display subsets
display "Active regions:", active_regions;

* Conditional display
if (debug_mode = 1,
    display "Debug info:", intermediate_results;
);
```

### 4.4 Validation Checks

**Add assertions** to verify assumptions:

```gams
* Check parameter range
abort$(smin(i, pm_population(i)) < 0) "Negative population detected!";

* Check conservation law
scalar land_balance_error;
land_balance_error = smax(j, abs(sum(land, vm_land.l(j,land)) - pm_total_land(j)));
abort$(land_balance_error > 1e-4) "Land conservation violated!", land_balance_error;

* Check solver status
abort$(model.solvestat <> 1) "Model did not solve normally", model.solvestat;
```

### 4.5 Incremental Debugging

**Build model incrementally**:

**1. Start simple**:
```gams
* Test with one region, one product, one timestep
set debug_i(i) / USA /;
set debug_k(k) / wheat /;
set debug_t(t) / y2020 /;

* Temporarily restrict model
loop(debug_t,
    ...
);
```

**2. Add complexity gradually**:
```gams
* Once simple case works, expand
set debug_i(i) / USA, EUR, CHN /;
```

**3. Use small test case**:
```gams
* Create minimal input data
parameter test_data(i,k);
test_data("USA","wheat") = 100;
test_data("EUR","wheat") = 150;
* Verify equation logic with hand-calculable values
```

---

## 5. Common Pitfalls & Solutions

### 5.1 Forward References

**Pitfall**: Using identifier before declaration.

**Error**:
```gams
a = b + c;          * ERROR: b, c not declared
parameters b, c;
```

**Solution**: Declare first, use later:
```gams
parameters b, c;
a = b + c;          * OK
```

### 5.2 Domain Errors

**Pitfall**: Using wrong index dimensions.

**Error**:
```gams
parameter value(i,j);
value(i) = 10;      * ERROR: Needs (i,j)
```

**Solution**: Match declaration:
```gams
value(i,j) = 10;    * OK (assigns to all j for each i)
```

### 5.3 Uninitialized Variables

**Pitfall**: Variables start at default (usually 0), may be poor starting point.

**Problem**:
```gams
solve model using nlp minimizing cost;
* Solver starts from vm_production.l = 0 for all
* May converge poorly or fail
```

**Solution**: Initialize:
```gams
vm_production.l(j,k) = historical_production(j,k);
solve model using nlp minimizing cost;
* Better starting point
```

### 5.4 Fixed Variables in Optimization

**Pitfall**: Accidentally fixing variables that should be free.

**Problem**:
```gams
* In presolve.gms for historical period
vm_land.fx(j,land) = pm_land_hist(t,j,land);

* Forgotten: Need to unfix for future periods!
* Model over-constrained
```

**Solution**: Fix only when appropriate:
```gams
if (t_past(t),
    vm_land.fx(j,land) = pm_land_hist(t,j,land);
else
    * Ensure bounds, not fixing
    vm_land.lo(j,land) = lower_bound(j,land);
    vm_land.up(j,land) = upper_bound(j,land);
);
```

### 5.5 Dollar Condition Logic Errors

**Pitfall**: Off-by-one or wrong filter logic.

**Error**:
```gams
* Intended: All except first
if (ord(t) > 1,          * WRONG: Skips first, includes rest
    value(t) = value(t-1) * growth;
);

* But at ord(t)=2, uses t-1=ord(1), which is t_past!
```

**Solution**: Check boundary conditions:
```gams
* Verify sets and ordinals
display "First t ordinal:", ord(t.first);
display "Last t ordinal:", smax(t2, ord(t2));

* Test logic separately
parameter test_flag(t);
test_flag(t)$(ord(t) > 1) = 1;
display test_flag;  * Verify which timesteps selected
```

### 5.6 Circular Dependencies

**Pitfall**: Module A needs output from B, but B needs output from A.

**Problem**: Infeasibility or oscillation.

**Solution**: Break with temporal lag:
```gams
* Module A uses previous value from B
value_A(t) = value_B(t-1) * factor;

* Module B uses current A
value_B(t) = value_A(t) + adjustment;
```

**See**: `magpie-agent/cross_module/circular_dependency_resolution.md`

### 5.7 Macro Expansion Issues

**Pitfall**: Unexpected text substitution.

**Problem**:
```gams
$macro square(x) x * x

result = square(a + b);  * Expands to: a + b * a + b = a + (b*a) + b
* Precedence issue!
```

**Solution**: Parenthesize macro body:
```gams
$macro square(x) ((x) * (x))

result = square(a + b);  * Expands to: ((a + b) * (a + b))
* Correct!
```

### 5.8 Set Membership Errors

**Pitfall**: Empty sets or wrong domain.

**Error**:
```gams
set active(i);
* Forgot to assign elements

loop(active,           * ERROR: Empty set, loop never executes
    process(i);
);
```

**Solution**: Check cardinality:
```gams
if (card(active) = 0,
    display "Warning: Active set is empty!";
else
    loop(active,
        process(i);
    );
);
```

### 5.9 Time Indexing Confusion

**Pitfall**: Mixing up `t` vs `ct` vs `t-1`.

**Error**:
```gams
* In equation (can't reference loop index t directly)
equation q_example;
q_example.. vm_var(t) =e= pm_param(t);  * ERROR: t not in scope
```

**Solution**: Use `ct` (current timestep marker):
```gams
equation q_example;
q_example.. vm_var(ct) =e= pm_param(ct);  * OK
```

### 5.10 Unit Mismatches

**Pitfall**: Mixing incompatible units.

**Error**:
```gams
* Land in mio. ha, but yield in t/ha
production = land * yield;  * Wrong: should be (mio. ha) * (t/ha) = mio. t
```

**Solution**: Document and verify units:
```gams
parameters
 pm_land(j)   Land area (mio. ha)
 pm_yield(j)  Yield (t per ha)
 pm_prod(j)   Production (mio. t)
;

pm_prod(j) = pm_land(j) * pm_yield(j);  * (mio. ha) * (t/ha) = (mio. t) ✓
```

---

## Summary: Quick Checklist

**Before running model**:
- [ ] Check scaling: Are values in range 0.01-1000?
- [ ] Protect division: All divisions guarded?
- [ ] Set bounds: All variables have reasonable `.lo` and `.up`?
- [ ] Initialize variables: Warm start `.l` values set?
- [ ] Verify units: Compatible across all calculations?
- [ ] Check domains: Sets non-empty, indices match declarations?

**After solve fails**:
- [ ] Check `model.solvestat`: What type of failure?
- [ ] Display infeasible equations: Which constraints violated?
- [ ] Check variable bounds: Any at extreme values?
- [ ] Verify input data: Display parameters, look for anomalies
- [ ] Simplify: Test with minimal case (one region, one product)
- [ ] Add validation: Assertions for conservation laws

**Performance optimization**:
- [ ] Use vectorization: Avoid explicit nested loops
- [ ] Filter domains: Generate only necessary constraints
- [ ] Warm start: Initialize variables from previous solution
- [ ] Check sparsity: Dollar conditions to exclude zeros
- [ ] Try alternative solver: Test CONOPT vs IPOPT vs SNOPT

**Code quality**:
- [ ] Follow naming conventions: `vm_`, `pm_`, `p{NN}_`, `q{NN}_`
- [ ] Document units: Every parameter/variable declaration
- [ ] Cite sources: Reference files for input data
- [ ] Add comments: Explain non-obvious logic
- [ ] Use macros: Reuse common patterns
- [ ] Handle edge cases: First timestep, empty sets, zero values

---

## Final Guidance: When to Consult Documentation

**Always reference GAMS documentation when**:
- Implementing complex optimization models
- Debugging solver failures
- Optimizing performance for large models
- Working with unfamiliar GAMS features
- Encountering numerical issues

**MAgPIE-specific documentation**:
- Module structure → Phase 5
- Naming conventions → Phase 5
- Interface variables → Phase 5
- Time management → Phase 5
- Conservation laws → `cross_module/` docs
- Circular dependencies → `cross_module/circular_dependency_resolution.md`

**Official GAMS resources**:
- [GAMS User's Guide](https://www.gams.com/latest/docs/UG_MAIN.html)
- [Good NLP Formulations](https://www.gams.com/latest/docs/UG_NLP_GoodFormulations.html)
- [Finding and Fixing Execution Errors](https://www.gams.com/latest/docs/UG_ExecErrPerformance.html)
- [Good Optimization Modeling Practices](https://pascua.iit.comillas.edu/aramos/simio/transpa/s_GoodOptimizationModelingPractices.pdf)

---

**Completion**: You have now completed all 6 phases of the GAMS Programming Reference. You should be able to read, understand, modify, and write GAMS code for the MAgPIE model with confidence.

**Next steps**: Apply these principles, refer back as needed, and continue learning from actual MAgPIE code examples.
