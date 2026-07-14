# GAMS Programming Reference - Phase 5: MAgPIE-Specific Patterns

<!-- Naming-convention tables below use ONLY real MAgPIE symbols, verified against develop.
     No check-gams-vars allowlist is needed here: the 11 previously-allowlisted names
     (pm_gdp, im_gdp_pc, sm_years, s10_timestep, ...) were ALL fabricated, and were
     replaced with real ones on 2026-07-14 rather than suppressed. Keep it that way —
     if you add an example to these tables, use a symbol that exists. -->

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

**Most MAgPIE module realizations contain these files. Required: `realization.gms`, `declarations.gms`, `equations.gms`. Present only when needed: `sets.gms`, `preloop.gms`, `scaling.gms`, `start.gms`.**

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

**File pattern**: GAMS source files use the `.gms` extension.

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
| `v{NN}_` | **Module-internal** (local to module NN) | `v32_land`, `v70_feed_intake_pre` |

**Example**:
```gams
* Interface variable (Module 10 → used by many modules)
positive variables vm_land(j,land);

* Module-internal variable (only used within Module 32)
positive variables v32_land(j,type32,ac);
```

#### Parameters

| Prefix | Scope | Example (all real — verified in develop) |
|--------|-------|---------|
| `pm_` | **Interface** (data shared between modules) | `pm_carbon_density_secdforest_ac`, `pm_interest` |
| `p{NN}_` | **Module-internal** (calculated within module) | `p70_cattle_stock_proxy`, `p32_aff_pol` |
| `pcm_` | **Previous Current Module** (rolling parameter from last timestep) | `pcm_land`, `pcm_carbon_stock` |
| `f{NN}_` | **Input file** (loaded from external file) | `f18_multicropping`, `f32_aff_pol` |
| `i{NN}_` | **Input intermediate** (processed from file data) | `i70_livestock_productivity`, `i14_fao_yields_hist` |
| `fm_` | **File interface** (input shared across modules) | `fm_croparea`, `fm_aboveground_fraction` |
| `im_` | **Interface input** (shared input) | `im_growing_stock`, `im_pollutant_prices` |

**Example** (real declarations):
```gams
* Interface parameter, declared in Module 52, read by Module 14
pm_carbon_density_secdforest_ac(t_all,j,ac,ag_pools)

* Module-internal parameter (Module 32)
p32_aff_pol(t,j)

* Rolling parameter (carries last timestep's solution)
pcm_land(j,land)

* Input from file (Module 18)
f18_multicropping(t_all,i)

* Input interface, declared in Module 14, read by Modules 32 and 35
im_growing_stock(t,j,ac,land_timber)
```

#### Equations

| Prefix | Scope | Example (all real — verified in develop) |
|--------|-------|---------|
| `q{NN}_` | **Module equations** | `q35_prod_other`, `q18_prod_res_ag_reg` |

**Example** (`modules/35_natveg/pot_forest_may24/equations.gms:162`):
```gams
q35_prod_other(j2)..
```

#### Scalars

| Prefix | Scope | Example (all real — verified in develop) |
|--------|-------|---------|
| `s{NN}_` | **Module scalar** | `s14_minimum_growing_stock`, `s70_scavenging_ratio` |
| `sm_` | **Shared scalar** | `sm_carbon_fraction` |

**Example** (real declarations — `modules/14_yields/managementcalib_aug19/input.gms:19` and
`modules/70_livestock/fbask_jan16/input.gms:27`):
```gams
s14_minimum_growing_stock   Minimum growing stock for timber harvest in natural vegetation (tDM per ha) / 5 /
s70_scavenging_ratio        Ratio to adjust estimated pasture feed demand using scavenged feed sources (1) / 0.385 /
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
| `j` | Simulation cells (resolution-dependent; default ~200 clusters) |
| `cell(i,j)` | Mapping: cell j belongs to region i |
| `i2`, `j2` | Aliases for multi-index operations |

#### Product Sets

| Set | Meaning |
|-----|---------|
| `kall` | All products |
| `kcr` | Crop products |
| `kli` | Livestock products |
| `kap` | Animal products |
| `kve` | Land-use activities (crops + pasture + bioenergy/fodder; defined in module 14) |
| `kfo` | Food-relevant products (all products considered as food; module 15). Note: forestry products use the separate set `kforestry`. |

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

**Declaration**: In module `declarations.gms` files (each module declares its own interface variables).

**Usage**:
- **Defined by** one module (primary owner)
- **Used by** many modules (consumers)

**Example**: `vm_land(j,land)`
- **Defined**: Module 10 (Land)
- **Used by**: Modules 29 (cropland), 30 (croparea), 31 (pasture), 32 (forestry), 34 (urban), 35 (natural vegetation), 50 (nitrogen budget), 58 (peatland), 59 (SOM). Note: yields/production/carbon read `vm_area`/`vm_yld`/`vm_carbon_stock`, not `vm_land` directly.

### 3.2 Common Interface Variables

| Variable | Module | Used By | Purpose |
|----------|--------|---------|---------|
| `vm_land(j,land)` | 10 | Many | Land allocation by type |
| `vm_prod(j,k)` | 17 | 18, 30, 31, 38, 40, 42, 71, 73 | Production by product (cell-level); 20/21/70 consume the regional aggregate `vm_prod_reg` |
| `vm_carbon_stock(j,land,c_pools,stockType)` | 56 | 52, 32, 35 | Carbon stocks |
| `vm_watdem(wat_dem,j)` | 42 | 43 | Water demand |
| `vm_cost_glo` | 11 | - | Global costs (objective) |

### 3.3 Interface Parameters

**Interface parameters** (`pm_` prefix) pass **data** between modules.

**Example**: `fm_carbon_density(t_all,j,land,c_pools)`
- **Loaded**: Module 52 (Carbon) from input data
- **Used by**: Module 56 (GHG policy), Module 32 (Forestry)

### 3.4 Dependency Pattern

**Module A produces → Module B consumes**

**Example**: Carbon pricing affects afforestation

**Module 56 (GHG policy)**:
```gams
* Conceptually: carbon pricing turns emissions into costs via vm_emissions_reg x im_pollutant_prices
* (The actual q56_emis_pricing_co2 computes one-off CO2 costs from carbon-stock differences;
*  the annual emission cost equation, q56_emission_cost_annual, accumulates pricing over time.)
```

**Module 32 (Forestry)**:
```gams
* In equations.gms — forestry costs include land conversion
q32_cost_total(i2) ..
    vm_cost_fore(i2) =e=
    sum(cell(i2,j2), v32_cost_establishment(j2) + ... );
```

Module 32 responds to carbon prices indirectly through `vm_carbon_stock` → `vm_emission_costs`.

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

**See**: `cross_module/circular_dependency_resolution.md` for complete documentation.

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

**`ct` is a plain set (`set ct(t)`) assigned exactly one element per solve** (via `ct(t) = yes`). It behaves like a singleton at solve time, but it is **not** declared as a GAMS `singleton set`, so GAMS does not always treat a bare `ct` index as a constant scalar (see the pitfall below).

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

**⚠️ Pitfall - wrap `ct` in `sum(ct, ...)` when indexing a file/interface parameter:**
Because `ct` is a plain (non-singleton) set, using it as a **bare** index inside an
equation raises compile **Error 149 "Uncontrolled set entered as constant"** — `ct` is not
in the equation's domain, so nothing controls it. The robust idiom, used throughout MAgPIE,
is to sum over `ct` to pull the current-timestep value.

Real example — the residue-biomass equation `q18_prod_res_ag_reg`
(`modules/18_residues/flexreg_apr16/equations.gms:14-19`):
```gams
* RIGHT (as in develop): sum(ct, ...) controls ct
(sum((cell(i2,j2),w), vm_area(j2,kcr,w)) * sum(ct,f18_multicropping(ct,i2)) * f18_cgf("intercept",kcr)
 + vm_prod_reg(i2,kcr) * f18_cgf("slope",kcr))
* f18_attributes_residue_ag(attributes,kcr);

* WRONG: bare ct -> Error 149 "Uncontrolled set entered as constant"
(sum((cell(i2,j2),w), vm_area(j2,kcr,w)) * f18_multicropping(ct,i2) * f18_cgf("intercept",kcr)
 + vm_prod_reg(i2,kcr) * f18_cgf("slope",kcr))
* f18_attributes_residue_ag(attributes,kcr);
```
Note `f18_multicropping(t_all,i)` is **regional** (2-D) and sits *outside* the `cell/w` sum —
it is not indexed by cell, water type, or crop. `modules/53_methane/ipcc2006_aug22/equations.gms:62`
applies the same idiom for the same reason: `sum(ct,f53_ef_ch4_rice(ct,i2))`.

A real refactor that replaced these summed terms with bare `ct` references in
`modules/18_residues` and `modules/53_methane` produced exactly this Error 149.

> **Naming caveat:** this parameter used to be the cross-module interface *fm_multicropping*,
> consumed by `42_water_demand` until commit `2f3f0fb88` dropped that use (`CHANGELOG.md:671`:
> "removed ... factor because of fallow inconsistency"). With no cross-module consumer left it
> was demoted to module-local **`f18_multicropping`**. The `fm_` name is stale — reach for it
> from memory and you will write a symbol that no longer exists.
> (Guarded by `audit/renames.json` → Check 24.)

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

**Example** (Module 17, `modules/17_production/flexreg_apr16/presolve.gms:10-18`):

```gams
* pm_prod_init is computed UNCONDITIONALLY (note the hardcoded "y1995", not ct):
pm_prod_init(j,kcr) = sum(w, fm_croparea("y1995",j,w,kcr) * pm_yields_semi_calib(j,kcr,w));

* the ord(t)=1 guard wraps only the warm-start of the SOLUTION LEVEL:
if (ord(t) = 1,
$ifthen "%c17_prod_init%" == "on"
vm_prod.l(j,kcr) = pm_prod_init(j,kcr);
$endif
);
```

Note what the guard does and does not cover: the initial-production *parameter* is built
every timestep from a fixed 1995 base year, and only the `.l` (level) warm-start is gated on
the first timestep — and that further behind the `c17_prod_init` switch.

**Common first-timestep tasks**:
- Load historical data
- Initialize model state
- Set warm-start values
- Calibrate parameters

### 4.5 Historical Period (t_past)

**Pattern**: Bind variables to observed values during the historical period.

The historical-timestep test is `if (sum(sameas(t_past,t), 1) = 1, ...)`.

**Example** (Module 13, `modules/13_tc/endo_jan22/presolve.gms:12-17`):

```gams
if (sum(sameas(t_past,t),1) = 1 AND s13_ignore_tau_historical = 0,
v13_tau_core.lo(h,"pastr") =   f13_pastr_tau_hist(t,h);
v13_tau_core.lo(h,"crop") =    f13_tau_historical(t,h);
else
v13_tau_core.lo(h, tautype) =    pc13_tau(h, tautype);
);
```

In the historical period, τ is bounded **below** by the observed historical value; outside it,
by the previous timestep's τ (`pc13_tau`). Note this is a **lower bound (`.lo`), not a fix
(`.fx`)** — the optimiser may still raise τ above history, it just may not fall below it. Don't
assume `.fx` when you mean "constrained to history"; check which bound the code actually sets.

Other real instances of the same test: `modules/35_natveg/pot_forest_may24/presolve.gms:156`
(bounds `vm_land.lo(j,"primforest")`) and `modules/62_material/exo_flexreg_apr16/presolve.gms:15`
(sets a historical flag).

**Set relationships**:
```
t_all = t_past + t          (all = historical + future)
```

### 4.6 Transition from Historical to Projection

**Critical timestep**: Last historical → first projection.

**Pattern**: Bridge calibration to simulation.

**Example** (Module 70, modules/70_livestock/fbask_jan16/presolve.gms:32-33):

```gams
* Unconditional — runs every timestep in presolve.gms
p70_cattle_stock_proxy(t,i) = im_pop(t,i)
                              * pm_kcal_pc_initial(t,i,"livst_rum")
                              / i70_livestock_productivity(t,i,"sys_beef");
```

**Breakdown**:
- `im_pop(t,i)` — Regional population
- `pm_kcal_pc_initial(t,i,"livst_rum")` — Per-capita initial kcal from ruminant livestock
- `i70_livestock_productivity(t,i,"sys_beef")` — Livestock productivity for beef system
- Assignment is unconditional (no historical/future guard); runs every timestep

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
table f10_land(t_ini10,j,land) Land area (mio. ha)
$ondelim
$include "./modules/10_land/input/avl_land_t.cs3"
$offdelim
;

* Assign to parameter
pm_land_start(j,land) = f10_land("y1995",j,land);
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

**Example** (Module 70 - Feed requirement):

```gams
* In equations.gms — feed balance constraint
q70_feed(i2,kap,kall) ..
    sum(ct, im_feed_baskets(ct,i2,kap,kall))
    * vm_prod_reg(i2,kap) =g= vm_feed_intake(i2,kap,kall);
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
* In presolve.gms — exclude diagonal via equation dollar condition
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
q11_cost_reg(i2) ..
    v11_cost_reg(i2) =e=
    vm_cost_prod_crop(i2) + vm_cost_prod_past(i2) + vm_cost_prod_livst(i2)
    + vm_cost_trade_tariff(i2) + vm_cost_trade_margin(i2) + vm_cost_trade_feasibility(i2)
    + vm_emission_costs(i2) + ... ;
```

**Global cost** (objective function):

```gams
q11_cost_glo ..
    vm_cost_glo =e=
    sum(i2, v11_cost_reg(i2));
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

**Scalar switch** — a real on/off switch, `s52_growingstock_calib`
(`modules/52_carbon/normal_dec17/input.gms:46`), consumed at
`modules/52_carbon/normal_dec17/preloop.gms:23`:

```gams
* declaration (input.gms)
s52_growingstock_calib  Switch for growing stock calibration of secdforest growth curves 1=on 0=off (1) / 1 /

* consumption (preloop.gms)
if(s52_growingstock_calib = 1,
    * calibrate the secdforest growth curve to the FRA growing-stock target
    ...
);
```

The `if(<scalar> = 1, ...)` form is the common MAgPIE idiom for a binary switch. GAMS also
supports `elseif` for multi-way scalar switches, but MAgPIE more often expresses a multi-way
choice with a **`$setglobal` string switch** selected against a set (see below) rather than a
numeric scalar.

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

**Next**: [Best Practices](GAMS_Best_Practices.md) - Model scaling, numerical stability, performance, debugging, and common pitfalls.
