# GAMS Programming Reference - Phase 5: MAgPIE-Specific Patterns

**Version**: 1.0 | **Status**: Complete | **Target Audience**: AI agents working with MAgPIE

**Purpose**: Practical guide to MAgPIE coding patterns, module structure, naming conventions, and common idioms.

**Prerequisites**: Phases 1-4 (Fundamentals, Control Structures, Advanced Features, Functions)

**This phase is ESSENTIAL** for reading and writing MAgPIE code correctly.

---

## Table of Contents

1. [Module Structure & Files](#1-module-structure--files)
2. [Naming Conventions](#2-naming-conventions)
3. [Interface Variables & Parameters](#3-interface-variables--parameters)
4. [Time Step Management](#4-time-step-management)
5. [Calibration & Initialization](#5-calibration--initialization)
6. [Common MAgPIE Idioms](#6-common-magpie-idioms)

---

## 1. Module Structure & Files

### 1.1 Module Organization

MAgPIE follows a strict modular architecture. Each module resides in:

```
modules/[NN]_[name]/[realization]/
```

**Example**: `modules/10_land/landmatrix_dec18/`

**Components**:
- `NN` - Two-digit number (09-80)
- `name` - Module purpose (land, yields, costs, etc.)
- `realization` - Implementation variant (e.g., `landmatrix_dec18`, `fbask_jan16`)

### 1.2 Standard Module Files

**Every MAgPIE module realization contains these files**:

| File | Purpose | When Executed |
|------|---------|---------------|
| `declarations.gms` | Declare sets, parameters, variables, equations | Once, before first timestep |
| `equations.gms` | Define equation algebra | Once, before first timestep |
| `sets.gms` | Module-specific sets | Once, at start |
| `input.gms` | Load input data, set scalars | Once, before timeloop |
| `preloop.gms` | Pre-processing before time loop | Once, before timeloop |
| `presolve.gms` | Pre-solve processing | Every timestep, before solve |
| `postsolve.gms` | Post-solve processing | Every timestep, after solve |
| `realization.gms` | Module metadata | Read by framework |
| `scaling.gms` | Equation scaling factors | Once, before solve |
| `start.gms` | (Optional) Startup logic | Varies by module |

**File pattern**: Each file has `.gms` (source) and `.gsp` (preprocessed) versions.

### 1.3 Module File Execution Order

**One-time initialization** (before time loop):
```
1. sets.gms          - Define module-specific sets
2. declarations.gms  - Declare all symbols
3. input.gms         - Load data, set parameters
4. preloop.gms       - Pre-processing
5. equations.gms     - Define equation algebra
6. scaling.gms       - Set scaling factors
```

**Every timestep** (within time loop):
```
loop(t,
    ct(t) = yes;

    * All modules: presolve.gms  - Prepare for solve

    solve magpie using nlp minimizing vm_cost_glo;

    * All modules: postsolve.gms - Extract results

    ct(t) = no;
);
```

### 1.4 Example: Module 10 (Land) Structure

**File**: `modules/10_land/landmatrix_dec18/declarations.gms`

**Content structure** (lines 8-34):
```gams
*** Module-internal parameters
parameters
 pm_land_start(j,land)          Land initialization (mio. ha)
 pm_land_hist(t_ini10,j,land)   Historical land (mio. ha)
 pcm_land(j,land)                Previous timestep land (mio. ha)
;

*** Module-internal variables
variables
 vm_landdiff                     Aggregate land difference (mio. ha)
;

*** Decision variables
positive variables
 vm_land(j,land)                              Land area (mio. ha)
 vm_landexpansion(j,land)                     Land expansion (mio. ha)
 vm_landreduction(j,land)                     Land reduction (mio. ha)
 vm_cost_land_transition(j)                   Transition costs (mio. USD17MER per yr)
 vm_lu_transitions(j,land_from,land_to)       Transitions (mio. ha)
;

*** Equations
equations
 q10_land_area(j)                 Conservation constraint (mio. ha)
 q10_transition_to(j,land_to)     Transition balance TO (mio. ha)
 q10_transition_from(j,land_from) Transition balance FROM (mio. ha)
 q10_landexpansion(j,land_to)     Expansion calc (mio. ha)
 q10_landreduction(j,land_from)   Reduction calc (mio. ha)
 q10_cost(j)                       Transition costs (mio. USD17MER per yr)
 q10_landdiff                      Land difference (mio. ha)
;
```

**Note**: `vm_` prefix = interface variables (used by other modules).

### 1.5 R Section (Output Declarations)

**Purpose**: Auto-generated output parameters for R post-processing.

**Pattern** (in `declarations.gms` lines 36-52):
```gams
*#################### R SECTION START (OUTPUT DECLARATIONS) ####################
parameters
 ov_landdiff(t,type)                           Aggregated difference (mio. ha)
 ov_land(t,j,land,type)                        Land area (mio. ha)
 ov_landexpansion(t,j,land,type)               Land expansion (mio. ha)
 ov_landreduction(t,j,land,type)               Land reduction (mio. ha)
 ov_cost_land_transition(t,j,type)             Costs (mio. USD17MER per yr)
 ov_lu_transitions(t,j,land_from,land_to,type) Transitions (mio. ha)
 oq10_land_area(t,j,type)                      Land constraint (mio. ha)
 oq10_transition_to(t,j,land_to,type)          Transition TO (mio. ha)
 oq10_transition_from(t,j,land_from,type)      Transition FROM (mio. ha)
 oq10_landexpansion(t,j,land_to,type)          Expansion (mio. ha)
 oq10_landreduction(t,j,land_from,type)        Reduction (mio. ha)
 oq10_cost(t,j,type)                            Costs (mio. USD17MER per yr)
 oq10_landdiff(t,type)                         Land difference (mio. ha)
;
*##################### R SECTION END (OUTPUT DECLARATIONS) #####################
```

**Naming**:
- `ov_` = output variable (stores variable levels and marginals)
- `oq_` = output equation (stores equation levels and marginals)
- `type` dimension = `"level"`, `"marginal"`, `"lower"`, `"upper"`

**DO NOT EDIT** R sections manually—they're auto-generated by framework scripts.

### 1.6 Presolve Pattern

**File**: `modules/10_land/landmatrix_dec18/presolve.gms`

**Common patterns** (lines 10-25):
```gams
*' Some land transitions are restricted:

*' No planted forest on natural vegetation
vm_lu_transitions.fx(j,"primforest","forestry") = 0;

*' Conversions within natveg not allowed
vm_lu_transitions.fx(j,"primforest","other") = 0;
vm_lu_transitions.fx(j,"secdforest","other") = 0;

*' Primary forest can only decrease
vm_lu_transitions.fx(j,land_from,"primforest") = 0;
vm_lu_transitions.up(j,"primforest","primforest") = Inf;

*' Auto-fix variables with very narrow bounds
m_boundfix(vm_land,(j,land),up,1e-6);
```

**Common operations in presolve**:
- Set variable bounds (`.lo`, `.up`, `.fx`)
- Calculate parameters from previous timestep
- Initialize variables (`.l` for warm start)
- Apply scenario-specific constraints

---

## 2. Naming Conventions

### 2.1 Prefix System

MAgPIE uses **strict prefixes** to indicate scope and type:

#### Variables (Decision Variables)

| Prefix | Scope | Example |
|--------|-------|---------|
| `vm_` | **Interface** (shared between modules) | `vm_land`, `vm_prod` |
| `v{NN}_` | **Module-internal** (local to module NN) | `v10_lu_transitions`, `v70_feed` |

**Example**:
```gams
* Interface variable (Module 10 → used by many modules)
positive variables vm_land(j,land);

* Module-internal variable (only used within Module 10)
positive variables v10_lu_transitions(j,land_from,land_to);
```

#### Parameters

| Prefix | Scope | Example |
|--------|-------|---------|
| `pm_` | **Interface** (data shared between modules) | `pm_carbon_density`, `pm_gdp` |
| `p{NN}_` | **Module-internal** (calculated within module) | `p70_feed_req`, `p10_land_start` |
| `pcm_` | **Previous Current Module** (rolling parameter from last timestep) | `pcm_land`, `pcm_carbon_stock` |
| `f{NN}_` | **Input file** (loaded from external file) | `f10_land_init`, `f14_yields` |
| `i{NN}_` | **Input intermediate** (processed from file data) | `i10_urban_area` |
| `fm_` | **File interface** (input shared across modules) | `fm_nutrition`, `fm_gdp_pop` |
| `im_` | **Interface input** (shared input) | `im_pop`, `im_gdp_pc` |

**Example**:
```gams
* Interface parameter (from Module 52, used in Module 56)
parameters pm_carbon_price(t,i);

* Module-internal parameter (only in Module 70)
parameters p70_cattle_stock_proxy(t,i);

* Rolling parameter (carries last timestep's solution)
parameters pcm_land(j,land);

* Input from file (Module 14)
parameters f14_yields(t,i,kcr);

* Input interface (population data)
parameters im_pop(t,i);
```

#### Equations

| Prefix | Scope | Example |
|--------|-------|---------|
| `q{NN}_` | **Module equations** | `q10_land_area`, `q70_feed_demand` |

**Example**:
```gams
equations
 q10_land_area(j)                Land conservation
 q10_transition_to(j,land_to)    Transition balance
;
```

#### Scalars

| Prefix | Scope | Example |
|--------|-------|---------|
| `s{NN}_` | **Module scalar** | `s10_timestep`, `s70_feed_factor` |
| `sm_` | **Shared scalar** | `sm_years` |

**Example**:
```gams
scalars
 s10_fix_transition   Fix land transitions (0=no 1=yes) / 0 /
 s70_feed_waste       Feed waste factor                 / 0.1 /
;
```

#### Sets

| Prefix | Scope | Example |
|--------|-------|---------|
| No prefix | **Global sets** | `t`, `i`, `j`, `kcr`, `land` |
| `{module}_` | **Module-specific sets** | `land_from`, `land_to`, `kli`, `kcr` |

#### Macros

| Prefix | Scope | Example |
|--------|-------|---------|
| `m_` | **Global macros** | `m_year`, `m_annuity_ord` |
| `m{NN}_` | **Module macros** | `m21_baseline_prod`, `m58_LandMerge` |

### 2.2 Output Parameters (R Section)

| Prefix | Meaning | Example |
|--------|---------|---------|
| `ov_` | **Output variable** | `ov_land(t,j,land,type)` |
| `oq_` | **Output equation** | `oq10_land_area(t,j,type)` |

**Type dimension**: `"level"`, `"marginal"`, `"lower"`, `"upper"`

### 2.3 Special Naming Patterns

#### Time Sets

| Set | Meaning |
|-----|---------|
| `t_all` | All time steps (past + present + future) |
| `t` | Active optimization time steps |
| `t_past` | Historical period |
| `ct` | Current timestep (singleton) |
| `t2` | Alias of `t` (for lag/lead operations) |

#### Spatial Sets

| Set | Meaning |
|-----|---------|
| `i` | Regions (10-14 aggregated regions) |
| `j` | Simulation cells (~60,000 grid cells) |
| `cell(i,j)` | Mapping: cell j belongs to region i |
| `i2`, `j2` | Aliases for multi-index operations |

#### Product Sets

| Set | Meaning |
|-----|---------|
| `kall` | All products |
| `kcr` | Crop products |
| `kli` | Livestock products |
| `kap` | Animal products |
| `kve` | Veg etables/fruits |
| `kfo` | Forestry products |

#### Land Types

| Set | Meaning |
|-----|---------|
| `land` | All land types |
| `land_from`, `land_to` | For transition matrices |
| `primforest` | Primary forest |
| `secdforest` | Secondary forest |
| `forestry` | Managed forestry |
| `crop` | Cropland |
| `past` | Pasture |
| `urban` | Urban land |
| `other` | Other natural land |

#### Age Classes

| Set | Meaning |
|-----|---------|
| `ac` | Age classes (vegetation cohorts) |
| `ac_sub` | Subset of age classes |
| `ac_est` | Establishment age classes |
| `ac2` | Alias of `ac` |

---

## 3. Interface Variables & Parameters

### 3.1 What are Interface Variables?

**Interface variables** (`vm_` prefix) are **decision variables shared between modules**.

**Declaration**: In `core/declarations.gms` (not in module files).

**Usage**:
- **Defined by** one module (primary owner)
- **Used by** many modules (consumers)

**Example**: `vm_land(j,land)`
- **Defined**: Module 10 (Land)
- **Used by**: Modules 14 (Yields), 17 (Production), 30 (Croparea), 31 (Pasture), 32 (Forestry), 35 (Natural vegetation), 52 (Carbon), etc.

### 3.2 Common Interface Variables

| Variable | Module | Used By | Purpose |
|----------|--------|---------|---------|
| `vm_land(j,land)` | 10 | Many | Land allocation by type |
| `vm_prod(j,k)` | 17 | 20, 21, 70 | Production by product |
| `vm_carbon_stock(j,land,c_pools)` | 52 | 56, 57 | Carbon stocks |
| `vm_water_demand(wat_src,j)` | 42 | 43 | Water demand |
| `vm_cost_glo` | 11 | - | Global costs (objective) |

### 3.3 Interface Parameters

**Interface parameters** (`pm_` prefix) pass **data** between modules.

**Example**: `pm_carbon_density(t,j,land,c_pools)`
- **Calculated**: Module 52 (Carbon) in `postsolve.gms`
- **Used by**: Module 56 (GHG policy), Module 57 (MACC)

### 3.4 Dependency Pattern

**Module A produces → Module B consumes**

**Example**: Carbon pricing affects afforestation

**Module 56 (GHG policy)**:
```gams
* In postsolve.gms
pm_carbon_price(t,i) = v56_carbon_price.l(i);  * Store for next modules
```

**Module 32 (Forestry)**:
```gams
* In equations.gms
q32_cost_afforestation(j)..
    vm_cost_afforestation(j) =e=
    sum((kcr,w), vm_afforestation(j,kcr,w) * pm_carbon_price(t,i));
```

Module 32 **reads** `pm_carbon_price` that Module 56 **wrote**.

### 3.5 Circular Dependencies

**Problem**: Module A needs output from Module B, but Module B needs output from Module A.

**Solutions**:

**1. Temporal feedback** (most common):
```gams
* Module A uses value from previous timestep
value_A(t) = value_B(t-1) * factor;

* Module B uses current value from A
value_B(t) = value_A(t) + adjustment;
```

**2. Simultaneous equations**:
- Both modules contribute equations
- Solver finds simultaneous solution

**3. Sequential execution**:
- Module A makes initial guess
- Module B refines
- Iterate if necessary

**See**: `magpie-agent/cross_module/circular_dependency_resolution.md` for complete documentation.

---

## 4. Time Step Management

### 4.1 Time Loop Structure

**Main time loop** (in `main.gms`):

```gams
loop(t,
    * 1. Mark current timestep
    ct(t) = yes;

    * 2. All modules: presolve.gms
    *    (set bounds, initialize, calculate parameters)

    * 3. Solve optimization
    solve magpie using nlp minimizing vm_cost_glo;

    * 4. All modules: postsolve.gms
    *    (extract results, update rolling parameters)

    * 5. Unmark current timestep
    ct(t) = no;
);
```

### 4.2 Current Timestep Marker (ct)

**`ct` is a singleton set** - contains exactly one element at a time.

**Purpose**: Reference current timestep in equations without explicit `t` dependency.

**Pattern**:
```gams
* Before each solve
ct(t) = yes;  * Now ct = this iteration's t

* In equations (no explicit t index)
q_example.. vm_stock(ct,j) =e= vm_flow(ct,j) * m_timestep_length;

* After solve
ct(t) = no;   * Clear marker
```

**Why?**: Equations can't directly reference loop index `t`. Using `ct` allows time-awareness in equations.

### 4.3 Rolling Parameters (pcm_)

**Pattern**: Carry solution from timestep `t` to timestep `t+1`.

**Naming**: `pcm_` = **P**revious **C**urrent **M**odule parameter

**Example** (Module 10):

**In postsolve.gms**:
```gams
* After solve, store solution for next timestep
pcm_land(j,land) = vm_land.l(j,land);
```

**In next timestep's presolve.gms**:
```gams
* Use previous solution as starting point
if (ord(t) > 1,
    vm_land.l(j,land) = pcm_land(j,land);  * Warm start
);
```

**In equations.gms**:
```gams
* Reference previous timestep value
q10_land_area(j)..
    sum(land, vm_land(j,land)) =e=
    sum(land, pcm_land(j,land));  * Conservation: total area unchanged
```

### 4.4 First Timestep Initialization

**Pattern**: Initialize values only in first timestep (`ord(t) = 1`).

**Example** (Module 17):

```gams
* In presolve.gms
if (ord(t) = 1,
    im_demandshare_reg.l(i,kall) = f17_prod_init(i,kall)/sum(i2,f17_prod_init(i2,kall));
);
```

**Common first-timestep tasks**:
- Load historical data
- Initialize model state
- Set warm-start values
- Calibrate parameters

### 4.5 Historical Period (t_past)

**Pattern**: Fix variables to observed values during historical period.

**Example** (Module 70):

```gams
* In presolve.gms
if (sum(sameas(t_past,t), 1) = 1,
    * This is a historical timestep
    vm_prod.fx(j,kli) = f70_hist_prod(t,j,kli);  * Fix to data
);
```

**Set relationships**:
```
t_all = t_past + t          (all = historical + future)
```

### 4.6 Transition from Historical to Projection

**Critical timestep**: Last historical → first projection.

**Pattern**: Bridge calibration to simulation.

**Example** (Module 70, lines 69-75):

```gams
if (ord(t) = smax(t2, ord(t2)$(t_past(t2))) AND card(t) > sum(t_all$(t(t_all) and t_past(t_all)), 1),
    * This is last historical timestep AND there are future timesteps
    p70_cattle_stock_proxy(t,i) =  im_pop(t,i)
                                  * pm_gdp_pc_ppp(t,i)
                                  / sum(i_to_iso(i,iso), im_pop_iso("y1995",iso))
                                  * sum(i_to_iso(i,iso), im_gdp_pc_ppp_iso("y1995",iso));
);
```

**Breakdown**:
- `ord(t) = smax(t2, ord(t2)$(t_past(t2)))` — Is this the last historical timestep?
- `card(t) > sum(...)` — Are there future timesteps?
- If both TRUE: Initialize projection using historical calibration

### 4.7 Time Macros

**m_year(t)** - Convert timestep to calendar year:
```gams
if (m_year(t) > 2030,
    future_policy = yes;
);
```

**m_yeardiff(t)** - Years since previous timestep:
```gams
annual_cost(t) = total_cost(t) / m_yeardiff(t);
```

**m_timestep_length** - Current timestep length (for equations):
```gams
q_accumulation.. vm_stock(ct) =e= vm_stock_prev + vm_flow(ct) * m_timestep_length;
```

---

## 5. Calibration & Initialization

### 5.1 Purpose

**Calibration**: Adjust parameters so model reproduces historical observations.

**Initialization**: Set reasonable starting values for optimization.

**Why critical**:
- Nonlinear models sensitive to initial point
- Good start → faster convergence
- Historical match → credible projections

### 5.2 Historical Data Loading

**Pattern**: Load observed data in `input.gms`.

**Example** (Module 10):

```gams
* In input.gms
table f10_land_hist(t_all,j,land) Historical land use (mio. ha)
$ondelim
$include "./modules/10_land/input/land_history.csv"
$offdelim
;

* Assign to parameter
pm_land_hist(t_all,j,land) = f10_land_hist(t_all,j,land);
```

### 5.3 Fixing Historical Period

**Pattern**: In `presolve.gms`, fix variables to data for `t_past`.

```gams
* Fix historical period to observations
vm_land.fx(j,land)$(t_past(t)) = pm_land_hist(t,j,land);
```

**After historical period**: Bounds are released, variables are free.

### 5.4 Warm Start Initialization

**Pattern**: Set `.l` (level) values before solve.

**Example** (Module 10):

```gams
* In presolve.gms
if (ord(t) = 1,
    vm_land.l(j,land) = pm_land_start(j,land);  * Initial guess
else
    vm_land.l(j,land) = pcm_land(j,land);      * Use previous solution
);
```

**Benefit**: Solver starts from feasible point → faster, more reliable convergence.

### 5.5 Calibration Factors

**Pattern**: Adjust parameters to match observations.

**Example** (Module 70 - Feed calibration):

```gams
* In presolve.gms
* Calculate calibration factor to match historical production
p70_calib_factor(t,i,kli) = f70_hist_prod(t,i,kli) / vm_prod_calibrated.l(i,kli);

* Apply calibration
vm_prod_final(i,kli) = vm_prod_raw(i,kli) * p70_calib_factor(t,i,kli);
```

### 5.6 Transition Calibration

**Pattern**: At last historical timestep, calibrate projection.

**Purpose**: Smooth transition from data to simulation.

**Example pattern**:
```gams
if (ord(t) = smax(t2, ord(t2)$(t_past(t2))),
    * Calculate trend from last N historical years
    trend = (value(t) - value(t-5)) / 5;

    * Project first future year
    initial_projection(t+1) = value(t) + trend;
);
```

---

## 6. Common MAgPIE Idioms

### 6.1 Land Conservation Pattern

**Constraint**: Total land area in cell must remain constant.

**Equation** (`modules/10_land/landmatrix_dec18/equations.gms:13-15`):

```gams
q10_land_area(j2) ..
    sum(land, vm_land(j2,land)) =e=
    sum(land, pcm_land(j2,land));
```

**Interpretation**: Current total land = previous total land (strict equality).

### 6.2 Transition Matrix Pattern

**Purpose**: Track land use changes between types.

**Variables**:
```gams
positive variables
 vm_lu_transitions(j,land_from,land_to)  Land transitions (mio. ha);
```

**Balance equations**:

```gams
* FROM constraint
q10_transition_from(j,land_from) ..
    sum(land_to, vm_lu_transitions(j,land_from,land_to)) =e=
    pcm_land(j,land_from);

* TO constraint
q10_transition_to(j,land_to) ..
    sum(land_from, vm_lu_transitions(j,land_from,land_to)) =e=
    vm_land(j,land_to);
```

**Excluding diagonal** (land type to itself):

```gams
* In presolve.gms
vm_lu_transitions.fx(j,land,land) = 0;  * No self-transitions allowed

* OR in equation (with dollar condition)
sum(land_to$(not sameas(land_from,land_to)),
    vm_lu_transitions(j,land_from,land_to))
```

### 6.3 Regional Aggregation Pattern

**Purpose**: Aggregate cell-level values to regional level.

**Set relationship**: `cell(i,j)` maps cell `j` to region `i`.

**Pattern**:
```gams
regional_total(i) = sum(cell(i,j), cell_value(j));
```

**Example** (Module 17):

```gams
* Regional production from cell production
vm_prod_reg(i,k) =e= sum(cell(i,j), vm_prod(j,k));
```

### 6.4 Weighted Average Pattern

**Purpose**: Average with heterogeneous weights (e.g., area-weighted yields).

**Using macro** (`core/macros.gms:16`):

```gams
$macro m_weightedmean(x,w,s) (sum(s,x*w)/sum(s,w))$(sum(s,w)>0) + 0$(sum(s,w)<=0)

* Usage
avg_yield(i) = m_weightedmean(yield(i,j), area(i,j), j);
```

**Manual version**:

```gams
avg_yield(i) = sum(j, yield(i,j) * area(i,j)) / sum(j, area(i,j))$(sum(j, area(i,j)) > 0);
```

**Protection**: Returns 0 if total weight is zero (avoids division by zero).

### 6.5 Growth Function Pattern

**Purpose**: Model vegetation or economic growth over time/age.

**Chapman-Richards** (vegetation carbon):

```gams
$macro m_growth_vegc(S,A,k,m,ac) S + (A-S)*(1-exp(-k*(ac*5)))**m

carbon_density(t,j,ac,pool) = m_growth_vegc(
    initial_density,
    asymptotic_density,
    growth_rate,
    shape_param,
    ac
);
```

**Linear growth** (litter/soil carbon):

```gams
$macro m_growth_litc_soilc(start,end,ac) \
    (start + (end - start) * 1/20 * ac*5)$(ac <= 20/5) + end$(ac > 20/5)
```

### 6.6 Cost Calculation Pattern

**Purpose**: Calculate regional or global costs with annualization.

**Annuity pattern**:

```gams
* Capital investment annualized over lifetime
annual_cost = investment_cost / m_annuity_due(interest_rate, lifetime);
```

**Regional cost aggregation**:

```gams
q11_cost_reg(i) ..
    vm_cost_reg(i) =e=
    sum(cost_type, vm_cost_component(i,cost_type));
```

**Global cost** (objective function):

```gams
q11_cost_glo ..
    vm_cost_glo =e=
    sum(i, vm_cost_reg(i));
```

### 6.7 Fixing and Bounding Pattern

**Prevent unwanted transitions** (presolve.gms):

```gams
* No conversion from primary forest to forestry
vm_lu_transitions.fx(j,"primforest","forestry") = 0;

* Primary forest can only decrease (never increase)
vm_lu_transitions.fx(j,land_from,"primforest") = 0;

* Allow primary forest self-retention (up to infinity)
vm_lu_transitions.up(j,"primforest","primforest") = Inf;
```

**Auto-fix narrow bounds** (using macro):

```gams
m_boundfix(vm_land,(j,land),up,1e-6);
```

If `vm_land.up(j,land) - vm_land.lo(j,land) < 1e-6`, fix to upper bound.

### 6.8 Scenario Switch Pattern

**Purpose**: Configure model based on scenario settings.

**Scalar switch**:

```gams
scalar s10_scenario  Scenario selection / 1 /;

* In presolve.gms or input.gms
if (s10_scenario = 1,
    * SSP2 baseline
    parameter_set = baseline_values;
elseif s10_scenario = 2,
    * SSP1 sustainability
    parameter_set = sustainability_values;
else
    abort "Unknown scenario";
);
```

**Set-based switch**:

```gams
set scenario / SSP1, SSP2, SSP3 /;
set active_scenario(scenario);

active_scenario("SSP2") = yes;

if (sameas(active_scenario,"SSP2"),
    load_SSP2_data;
);
```

### 6.9 Time Interpolation Pattern

**Purpose**: Gradually phase in policies or parameters.

**Linear interpolation** (using macro):

```gams
* Phase in diet shift from 0 (2020) to 1 (2050)
m_linear_time_interpol(diet_shift, 2020, 2050, 0, 1);

* Result:
* diet_shift(2020) = 0
* diet_shift(2035) = 0.5
* diet_shift(2050) = 1
```

**Sigmoid interpolation** (S-curve):

```gams
* Smooth phase-in with slow start, fast middle, slow end
m_sigmoid_time_interpol(carbon_price, 2025, 2100, 0, 200);
```

### 6.10 Conditional Processing Pattern

**Time-dependent parameters**:

```gams
loop(t,
    if (m_year(t) > 2030,
        * Future scenario
        pm_parameter(t,i) = future_values(i);
    else
        * Historical/baseline
        pm_parameter(t,i) = historical_values(t,i);
    );
);
```

**Region-specific logic**:

```gams
loop(i,
    if (sameas(i,"SSA"),  * Sub-Saharan Africa
        special_africa_calculation;
    else
        standard_calculation;
    );
);
```

---

## Summary & Best Practices

### Module Development Checklist

**When creating or modifying a module**:

1. ✅ **Follow file structure**: Include all standard files
2. ✅ **Use correct prefixes**: `vm_`, `pm_`, `p{NN}_`, `q{NN}_`, etc.
3. ✅ **Document thoroughly**: Units, purpose, sources
4. ✅ **Handle first timestep**: Initialize in `if (ord(t) = 1, ...)`
5. ✅ **Manage time**: Use `pcm_` rolling parameters
6. ✅ **Set bounds carefully**: Use `presolve.gms` for `.fx`, `.lo`, `.up`
7. ✅ **Warm start**: Set `.l` values for nonlinear models
8. ✅ **Check dependencies**: Ensure interface variables/parameters available
9. ✅ **Test calibration**: Verify historical period matching
10. ✅ **Update R sections**: Run framework scripts to regenerate

### Common Pitfalls to Avoid

**❌ DON'T**:
- Use wrong prefixes (e.g., `p10_` for interface parameter—should be `pm_`)
- Modify R section manually (auto-generated, will be overwritten)
- Forget first-timestep initialization
- Ignore circular dependencies (causes infeasibility or oscillation)
- Mix up `t` vs `ct` in equations
- Hardcode years instead of using `m_year(t)`
- Skip warm start initialization (poor convergence)
- Fix variables permanently (should be in `presolve.gms`, not `declarations.gms`)

**✅ DO**:
- Check naming conventions carefully
- Use macros from `core/macros.gms` where appropriate
- Reference existing modules for patterns
- Document units and sources
- Test with simple scenarios first
- Verify conservation laws (see `cross_module/` docs)
- Use `m_boundfix` for numerical stability

### Quick Reference: Where to Put Code

| Task | File | When Executed |
|------|------|---------------|
| Declare symbols | `declarations.gms` | Once at start |
| Define equation algebra | `equations.gms` | Once at start |
| Load external data | `input.gms` | Once before loop |
| One-time setup | `preloop.gms` | Once before loop |
| Set bounds, initialize | `presolve.gms` | Every timestep (before solve) |
| Extract results | `postsolve.gms` | Every timestep (after solve) |
| Module-specific sets | `sets.gms` | Once at start |

### Essential MAgPIE Patterns

**Most frequently used**:
1. **Land conservation**: `sum(land, vm_land) =e= constant`
2. **Regional aggregation**: `sum(cell(i,j), value(j))`
3. **Transition matrix**: `vm_lu_transitions(j,land_from,land_to)`
4. **First timestep init**: `if (ord(t) = 1, ...)`
5. **Rolling parameters**: `pcm_land(j,land) = vm_land.l(j,land)`
6. **Excluding diagonal**: `$(not sameas(land_from,land_to))`
7. **Historical fixing**: `vm_X.fx$(t_past(t)) = data(t)`
8. **Weighted average**: `m_weightedmean(value, weight, set)`
9. **Time macros**: `m_year(t)`, `m_yeardiff(t)`
10. **Auto-fix bounds**: `m_boundfix(vm_X, (j,land), up, 1e-6)`

---

**Final Phase**: [Phase 6: Best Practices](GAMS_Phase6_Best_Practices.md) - Model scaling, numerical stability, performance, debugging, and common pitfalls.
