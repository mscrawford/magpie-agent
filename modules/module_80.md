# Module 80: Optimization - MAgPIE Model Solver Module

**Status**: Fully Verified
**Realization**: nlp_apr17 (default), lp_nlp_apr17, nlp_ipopt, nlp_par
**Equations**: 0 (pure solver module, no model equations defined)

---

> ⚙️ **Default Realization**: `nlp_apr17`
> Confirmed in `config/default.cfg`: `cfg$gms$optimization <- "nlp_apr17"`. Alternatives: `lp_nlp_apr17` (LP presolve then NLP), `nlp_ipopt` (direct NLP with the Ipopt interior-point solver), `nlp_par` (parallel NLP).
>
> ⚠️ **R3 audit warning (2026-05-23)**: this doc has dedicated Parameters tables for `lp_nlp_apr17`, `nlp_ipopt`, and `nlp_par`, but NOT for the default `nlp_apr17`. The default realization has distinct parameters: it includes `s80_resolve_option` (which `lp_nlp_apr17` lacks) and lacks `s80_obj_linear` (which `lp_nlp_apr17` has). For default-config questions about Module 80 parameters, read `../modules/80_optimization/nlp_apr17/declarations.gms` and `../modules/80_optimization/nlp_apr17/input.gms` directly. A dedicated `Parameters (nlp_apr17)` section is deferred to a future session.


## Overview

**Purpose**: Module 80 (Optimization) is THE CORE EXECUTION MODULE that solves the entire MAgPIE optimization problem at each timestep (module.gms:8-21). It does NOT define any model equations itself, but rather manages the solution strategy, solver selection, and error handling for the complete MAgPIE model containing all equations from the other 45 modules.

**Key Characteristic**: This is a pure **solver orchestration module** that allows switching between different optimization strategies to improve runtime performance without changing the underlying model structure (module.gms:10-13).

**Core Task**: At each timestep, Module 80 solves the nonlinear programming (NLP) problem:

```
minimize vm_cost_glo  (total system costs)
subject to:  all equations from Modules 09-73
```

And optionally minimizes land use changes (vm_landdiff) to select among equivalent cost-optimal solutions (module.gms:15-19).

---

## Interface Variables (INPUTS to optimization)

Module 80 does NOT define variables. The interface-variable set used depends on the active realization:

**Default `nlp_apr17` realization** — uses 1 interface variable:

| Variable | Provider | Dimensions | Unit | Description | Reference |
|----------|----------|------------|------|-------------|-----------|
| `vm_cost_glo` | Module 11 (Costs) | (none, global) | 10⁶ USD17MER/yr | Total global system costs (objective function) | `modules/80_optimization/nlp_apr17/solve.gms` lines 34, 36, 70, 71 (`MINIMIZING vm_cost_glo`) |

**Non-default `lp_nlp_apr17` realization** — uses 2 interface variables (adds `vm_landdiff`):

| Variable | Provider | Dimensions | Unit | Description | Reference |
|----------|----------|------------|------|-------------|-----------|
| `vm_cost_glo` | Module 11 (Costs) | (none, global) | 10⁶ USD17MER/yr | Cost objective for LP phase | `modules/80_optimization/lp_nlp_apr17/solve.gms` |
| `vm_landdiff` | Module 10 (Land) | (none, global) | 10⁶ ha | Land-use change penalty used in the cost-tied stabilization solve | `modules/80_optimization/lp_nlp_apr17/solve.gms` lines 76, 77, 196, 197 |

**Note**: Module 80 does NOT provide variables to other modules. It only solves for the optimal values of ALL variables in the model.

---

## Model Declaration

The full MAgPIE model is declared in `main.gms` as:

```gams
model magpie / all - m15_food_demand /;
```

This includes ALL equations from all active module realizations, EXCEPT the food demand model (m15_food_demand) which is typically run exogenously (main.gms).

---

## Realization: lp_nlp_apr17 (LP Warmstart + NLP)

**Strategy**: Two-stage approach: first solve a linearized version of the model, then use this solution as starting point for the full nonlinear optimization (realization.gms:8-12).

**Rationale**: The LP warmstart provides a high-quality initial point, often reducing NLP solve time and improving convergence (realization.gms:8-12).

### Key Mechanism: Nonlinearity Fixation

**Step 1 - Fix Nonlinear Terms** (solve.gms:52-55):
- All nonlinear terms are temporarily fixed to best-guess values
- Each nonlinear module realization MUST provide `nl_fix.gms` file
- Example: Module 13 (TC) fixes tau factors to previous timestep values
- After fixation, model becomes linear (or mostly linear)

```gams
$batinclude "./modules/include.gms" nl_fix
```
(solve.gms:55)

**Step 2 - LP Solve with CPLEX** (solve.gms:47-78):

Solver settings (solve.gms:19-24):
- Linear solver: CPLEX
- QCP solver: CPLEX
- Threads: 1
- `magpie.trylinear = 1` signals GAMS to attempt linear solve

Primary solve:
```gams
solve magpie USING nlp MINIMIZING vm_cost_glo;
```
(solve.gms:65)

**Note**: Declared as NLP but solved as LP due to fixations and `trylinear` flag (solve.gms:58-61).

**Optional second solve** (for matching LHS and RHS, controlled by `s80_secondsolve` scalar):
```gams
if(s80_secondsolve = 1, solve magpie USING nlp MINIMIZING vm_cost_glo; );
```
(solve.gms:66)

**Step 3 - Minimize Land Use Changes** (solve.gms:74-79):

If LP solve is optimal (modelstat = 1) or feasible (modelstat = 7):
1. Fix total costs: `vm_cost_glo.up = vm_cost_glo.l`
2. Minimize land changes: `solve magpie USING nlp MINIMIZING vm_landdiff`
3. Release cost constraint: `vm_cost_glo.up = Inf`

Purpose: Among multiple cost-optimal solutions, select the one with minimal land use change compared to previous timestep (solve.gms:68-72).

**Step 4 - Check Linear Solve** (solve.gms:84-96):

Success (modelstat = 1 or 7):
- Store objective value: `s80_obj_linear = vm_cost_glo.l`

Failure (modelstat = 2):
- Error: Unfixed nonlinear terms remain → ABORT
- ALL nonlinear modules MUST provide `nl_fix.gms` and `nl_release.gms`

Other failures:
- Set `s80_obj_linear = Inf` (indicates infeasibility)

**Step 5 - Release Nonlinear Terms** (solve.gms:101-104):

```gams
$batinclude "./modules/include.gms" nl_release
```

**Step 6 - Relax and Retry LP** (if infeasible) (solve.gms:106-121):

If `p80_modelstat(t) ≠ 1`:
- Relax nonlinear term fixations: `$batinclude "./modules/include.gms" nl_relax`
- Retry LP solve
- Repeat up to `s80_maxiter` times (default: 30)

**Step 7 - Full NLP Solve with CONOPT4** (solve.gms:124-133):

Solver selection (solve.gms:27-35):
- Default NLP solver: CONOPT4
- Alternative: CONOPT4 + CPLEX (set `c80_nlp_solver = "conopt4+cplex"`)
- Alternative: CONOPT4 + CONOPT3 (set `c80_nlp_solver = "conopt4+conopt3"`)

CONOPT4 settings (solve.gms:37-39):
- Tolerance: `Tol_Optimality = s80_toloptimal` (default: 1e-08)

Primary NLP solve:
```gams
solve magpie USING nlp MINIMIZING vm_cost_glo;
if(s80_secondsolve = 1, solve magpie USING nlp MINIMIZING vm_cost_glo; );
```
(solve.gms:130-131)

**Step 8 - Fallback Strategies** (solve.gms:135-146):

**Fallback A - Additional CONOPT3 solve** (if `s80_add_conopt3 = 1`):
```gams
option nlp = conopt3;
solve magpie USING nlp MINIMIZING vm_cost_glo;
```
(solve.gms:138-140)

**Fallback B - Modelstat 13 recovery** (solve.gms:145-146):
- Modelstat 13: Error during solve (e.g., evaluation error)
- Retry 1: CONOPT4 with increased variable limit (optfile = 2, Lim_Variable = 1.e25)
- If still fails, proceed to Fallback C

**Fallback C - CONOPT3 as last resort** (solve.gms):
- Switch to CONOPT3 (older, more robust solver)
- Final attempt to find feasible solution

**Step 9 - Optional CPLEX Polish** (solve.gms):

If `s80_add_cplex = 1` (set via `c80_nlp_solver = "conopt4+cplex"`):
1. Fix nonlinearities again (`nl_fix`)
2. Solve linearized model with CPLEX
3. Release nonlinearities (`nl_release`)
4. If optimal/feasible, minimize land differences

Purpose: CPLEX may find solutions closer to previous timestep pattern (solve.gms).

**Step 10 - Finalization** (solve.gms):

Success (modelstat < 3, excluding modelstat = 7):
- Save GDX file: `mv magpie_p.gdx magpie_YEAR.gdx`

Failure (modelstat > 2 and ≠ 7):
- Dump full data: `Execute_Unload "fulldata.gdx"`
- ABORT: "no feasible solution found!"

### Parameters (lp_nlp_apr17)

**Declarations** (`lp_nlp_apr17/declarations.gms:8-16`):

| Parameter | Dimensions | Unit | Description | Reference |
|-----------|------------|------|-------------|-----------|
| `p80_modelstat(t)` | time | (1) | Modelstat indicator (1=optimal, 2=locally optimal, >2=infeasible/error) | `lp_nlp_apr17/declarations.gms:9` |
| `p80_num_nonopt(t)` | time | (1) | Number of non-optimal variables (numNOpt) | `lp_nlp_apr17/declarations.gms:10` |
| `s80_counter` | scalar | (1) | Iteration counter for retry loop | `lp_nlp_apr17/declarations.gms:14` |
| `s80_obj_linear` | scalar | 10⁶ USD17MER/yr | Linear solve objective value | `lp_nlp_apr17/declarations.gms:15` |

**Inputs** (`lp_nlp_apr17/input.gms:8-13`):

| Scalar | Default | Unit | Description | Reference |
|--------|---------|------|-------------|-----------|
| `s80_maxiter` | 30 | (1) | Maximum solve iterations if modelstat > 2 | input.gms:9 |
| `s80_optfile` | 1 | (1) | Switch to use specified solver settings (0=default, 1=custom) | input.gms:10 |
| `s80_secondsolve` | 0 | binary | Enable second solve statement (0=off, 1=on) | input.gms:11 |
| `s80_toloptimal` | 1e-08 | (1) | CONOPT4 optimality tolerance | input.gms:12 |

**Configuration switches** (solve.gms:27-35):
- `c80_nlp_solver`: "conopt4" (default), "conopt4+cplex", "conopt4+conopt3"

---

## Realization: nlp_apr17 (DEFAULT - Direct NLP)

**Strategy**: Solve the full nonlinear model directly using CONOPT4, without LP warmstart (realization.gms:8-12).

**Use Case**: Faster for small models or when LP warmstart doesn't improve convergence. Simpler implementation without need for `nl_fix`/`nl_release` files.

### Solve Sequence (nlp_apr17)

**Step 1 - Solver Configuration** (solve.gms:13-27):

```gams
option nlp = conopt4;
option threads = 1;
magpie.optfile   = s80_optfile;    // 1 = use custom settings
magpie.scaleopt  = 1;              // Enable scaling
magpie.solprint  = 0;              // Suppress detailed solve output
magpie.holdfixed = 1;              // Keep fixed variables out of basis
```
(solve.gms:14-19)

CONOPT4 settings:
- Tolerance: `Tol_Optimality = s80_toloptimal` (default: 1e-08)
- Alternate optfile: `Lim_Variable = 1.e25` (optfile = 2, relaxed variable limits)

**Step 2 - Primary NLP Solve** (solve.gms:33-36):

```gams
solve magpie USING nlp MINIMIZING vm_cost_glo;
if(s80_secondsolve = 1, solve magpie USING nlp MINIMIZING vm_cost_glo; );
```
(solve.gms:34-36)

**Step 3 - Fallback Retry Loop** (if modelstat > 2) (solve.gms:47-93):

Iteration strategies (4 attempts, cyclic):

1. **Attempt 1**: CONOPT4 default settings (optfile = 0)
2. **Attempt 2**: CONOPT4 with custom optfile (optfile = 1)
3. **Attempt 3**: CONOPT4 with relaxed limits (optfile = 2, Lim_Variable = 1.e25)
4. **Attempt 4**: CONOPT3 (older solver, optfile = 0)

Loop continues until:
- Solution found (modelstat ≤ 2), OR
- Max iterations reached (`s80_counter >= s80_maxiter`, default: 30)

```gams
repeat(
  s80_counter = s80_counter + 1;
  s80_resolve_option = s80_resolve_option + 1;

  // Select strategy based on s80_resolve_option (1-4, then reset)
  if(s80_resolve_option = 1, ... CONOPT4 default
  elseif s80_resolve_option = 2, ... CONOPT4 optfile
  elseif s80_resolve_option = 3, ... CONOPT4 relaxed
  elseif s80_resolve_option = 4, ... CONOPT3

  solve magpie USING nlp MINIMIZING vm_cost_glo;

  s80_resolve_option$(s80_resolve_option >= 4) = 0;  // Reset cycle

  until (magpie.modelstat <= 2 or s80_counter >= s80_maxiter)
);
```
(solve.gms:48-92)

**Step 4 - Finalization** (solve.gms:95-109):

Success (modelstat ≤ 2):
- Save GDX: `mv magpie_p.gdx magpie_YEAR.gdx`

Failure (modelstat > 2 and ≠ 7):
- Zip debug files: `gmszip -r magpie_problem.zip`
- Dump full data: `Execute_Unload "fulldata.gdx"`
- ABORT: "no feasible solution found!"

### Key Differences from lp_nlp_apr17

| Feature | lp_nlp_apr17 | nlp_apr17 |
|---------|--------------|-----------|
| LP warmstart | ✅ Yes | ❌ No |
| Requires `nl_fix`/`nl_release` | ✅ Yes | ❌ No |
| Initial solve complexity | High (LP + NLP) | Low (NLP only) |
| Fallback strategies | 3 (CONOPT3, CPLEX polish, relaxed CONOPT4) | 4 (cycle through CONOPT4 configs + CONOPT3) |
| Land difference minimization | ✅ Yes (after LP and NLP) | ❌ No |
| Typical use case | Large models (e.g., 200 cells) | Small/medium models or when LP doesn't help |

### Parameters (nlp_apr17)

`nlp_apr17` is the minimal-state realization: just enough scratch parameters to drive the retry loop. No LP-related state, no land-difference accumulator (consistent with the "no LP warmstart, no land-diff minimization" simplifications above).

**Declarations** (`nlp_apr17/declarations.gms:8-15`):

| Parameter | Dimensions | Unit | Description | Reference |
|-----------|------------|------|-------------|-----------|
| `p80_modelstat(t)` | time | (1) | Modelstat indicator (1=optimal, 2=locally optimal, >2=infeasible/error) | `nlp_apr17/declarations.gms:9` |
| `p80_num_nonopt(t)` | time | (1) | Number of non-optimal variables (numNOpt) | `nlp_apr17/declarations.gms:10` |
| `s80_counter` | scalar | (1) | Iteration counter for retry loop | `nlp_apr17/declarations.gms:14` |
| `s80_resolve_option` | scalar | (1) | Option for resolve (cycles 1-4 across the 4-config fallback strategy) | `nlp_apr17/declarations.gms:15` |

**Inputs** (`nlp_apr17/input.gms:8-13`):

| Scalar | Default | Unit | Description | Reference |
|--------|---------|------|-------------|-----------|
| `s80_maxiter` | 30 | (1) | Maximum solve iterations if modelstat > 2 | `nlp_apr17/input.gms:9` |
| `s80_optfile` | 1 | (1) | Switch to use specified solver settings (0=default, 1=custom) | `nlp_apr17/input.gms:10` |
| `s80_secondsolve` | 0 | binary | Enable second solve statement (0=off, 1=on) | `nlp_apr17/input.gms:11` |
| `s80_toloptimal` | 1e-08 | (1) | CONOPT4 optimality tolerance | `nlp_apr17/input.gms:12` |

**Configuration switches** — `nlp_apr17` is solver-agnostic in the sense that it uses CONOPT4 with the `s80_resolve_option`-driven retry cycle; no separate `c80_nlp_solver` switch (that's lp_nlp_apr17-specific).

**Compared with lp_nlp_apr17**: nlp_apr17 has 2 declarations + 4 inputs vs. lp_nlp_apr17's 4 declarations + 4 inputs. The missing 2 parameters (`s80_obj_linear`, plus the LP-warmstart-specific bookkeeping) reflect nlp_apr17's no-LP-warmstart simplification.

---

## Realization: nlp_ipopt (Alternative - Direct NLP with the Ipopt Solver)

**Strategy**: Solve the full nonlinear model directly using the **Ipopt** interior-point solver instead of CONOPT4, without LP warmstart (realization.gms:8-13).

> ⚠️ **Non-default alternative**: The default `optimization` realization remains `nlp_apr17` (CONOPT4-based). `nlp_ipopt` is an **alternative** realization, added in MAgPIE `develop` (commit 9cba74ab7, PR #871, "Adding IPOPT as an alternative solver for MAgPIE"). To use it, set `cfg$gms$optimization <- "nlp_ipopt"`.

**What is Ipopt in this context**: Ipopt (Interior Point OPTimizer) is an open-source NLP solver implementing a primal-dual interior-point (barrier) method. In MAgPIE it is selected via `option nlp = ipopt;` (solve.gms:13) and is the **only** solver `nlp_ipopt` uses — it does not fall back to CONOPT. This realization shares the direct-NLP structure of `nlp_apr17` (solve once, retry on infeasibility) but swaps the solver and the option-file mechanism.

**Use Case**: Provides a non-CONOPT solver path. Useful for cross-checking solutions against the CONOPT-based realizations, or where the Ipopt interior-point method converges better than CONOPT4 on a given problem.

### Solve Sequence (nlp_ipopt)

**Step 1 - Solver Configuration** (solve.gms:9-55):

```gams
s80_counter = 0;
p80_modelstat(t) = 14;

option nlp = ipopt;
option threads = 1;
```
(solve.gms:9-14)

`magpie` solver attributes (solve.gms:52-55):
```gams
magpie.optfile   = s80_optfile;    // 1 = use the written ipopt.opt file
magpie.scaleopt  = 1 ;             // enable scaling
magpie.solprint  = 0 ;             // suppress detailed solve output
magpie.holdfixed = 1 ;             // keep fixed variables out of basis
```

**Step 2 - Write Ipopt option files at runtime** (solve.gms:16-50):

The CONOPT-based realizations also write their primary option file (`conopt4.opt`) at runtime via `put`/`putclose`; they differ only in writing the secondary `conopt4.op2` via a compile-time `$onecho` block in `solve.gms`. `nlp_ipopt` writes **both** Ipopt option files from GAMS via `put`/`putclose`, into the `File` objects declared in `preloop.gms` (`ipopt.opt` and `ipopt.op2`):

- **`ipopt.opt`** (default optfile, used when `s80_optfile = 1`) — solve.gms:18-29. Comment in code: "starting immediately with the monotone `mu_strategy` to make the behavior more consistent." Settings written: `tol` (= `s80_toloptimal`), `mu_strategy monotone`, `mu_init 1e-5`, `mu_linear_decrease_factor 0.85`, `mu_superlinear_decrease_power 1.02`, `nlp_scaling_method none`, `bound_relax_factor 1e-7`, `honor_original_bounds yes`, `constr_viol_tol 1e-6`, `dependency_detector mumps`.
- **`ipopt.op2`** (alternative optfile) — solve.gms:33-50. Comment in code: uses "the adaptive `mu_strategy` which starts faster but is less reliable. Seems to behave better for values near zero." Settings include `mu_strategy adaptive`, `mu_oracle quality-function`, `nlp_scaling_method gradient-based`, `acceptable_*` tolerances, `max_iter 10000`, `linear_solver mumps`, `dependency_detector mumps`.

⚠️ **Note**: `ipopt.op2` is written to disk but the solve loop never sets `magpie.optfile = 2` (the retry loop reuses the same `s80_optfile` setting — see Step 4). The `.op2` file is therefore prepared but not exercised by the current code path; switching to it would require a manual `magpie.optfile = 2` or code change. (Verified: `solve.gms` contains no assignment of `magpie.optfile` other than the `s80_optfile` assignment at line 52.)

**Step 3 - Primary NLP Solve** (solve.gms:61-67):

```gams
solve magpie USING nlp MINIMIZING vm_cost_glo;
```
(solve.gms:62)

There is **no `s80_secondsolve` second solve** in `nlp_ipopt` — that scalar is not declared for this realization (see Parameters below).

**Step 4 - Retry Loop** (if modelstat > 2) (solve.gms:69-95):

If the primary solve returns `modelstat > 2`, a `repeat` loop re-solves with **the same Ipopt optfile settings** (no solver/optfile cycling):

```gams
* set modelstat to 13 in case of NA for continuation
magpie.modelStat$(magpie.modelStat=NA) = 13;

if (magpie.modelstat > 2,
  repeat(
    s80_counter = s80_counter + 1 ;

    solve magpie USING nlp MINIMIZING vm_cost_glo;

    if ((s80_counter >= (s80_maxiter-1) and magpie.modelstat > 2),
      magpie.solprint = 1
    );

    magpie.modelStat$(magpie.modelStat=NA) = 13;

    until (magpie.modelstat <= 2 or s80_counter >= s80_maxiter)
  );
);
```
(solve.gms:69-95)

Loop terminates when a solution is found (`modelstat <= 2`) or `s80_counter >= s80_maxiter` (default 30). On the penultimate iteration, `magpie.solprint` is set to 1 so the final (infeasible) solve writes detailed output to the LST file (solve.gms:83-85).

**Key contrast with `nlp_apr17`**: `nlp_apr17`'s retry loop cycles through 4 strategies (CONOPT4 default → CONOPT4 optfile → CONOPT4 relaxed → CONOPT3) via `s80_resolve_option`. `nlp_ipopt` has **no `s80_resolve_option`** — every retry is an identical Ipopt re-solve. The only thing a retry can change is the solver's internal restart from the previous (failed) point.

**Step 5 - Finalization** (solve.gms:97-109):

```gams
p80_modelstat(t) = magpie.modelstat;
p80_num_nonopt(t) = magpie.numNOpt;
```

Success (`p80_modelstat(t) <= 2`):
- Save GDX: `mv -f magpie_p.gdx magpie_YEAR.gdx` (solve.gms:100-102)

Failure (`p80_modelstat(t) > 2` and `≠ 7`):
- Zip debug files: `gmszip -r magpie_problem.zip "%gams.scrdir%"`, renamed `magpie_problem_YEAR.zip` (solve.gms:104-106)
- Dump full data: `Execute_Unload "fulldata.gdx"`
- ABORT: "no feasible solution found!" (solve.gms:107-108)

This finalization block is identical to `nlp_apr17`'s (solve.gms:97-109 in both files).

### Parameters (nlp_ipopt)

**Declarations** (declarations.gms:8-15):

| Parameter | Dimensions | Unit | Description | Reference |
|-----------|------------|------|-------------|-----------|
| `p80_modelstat(t)` | time | (1) | Modelstat indicator (1=optimal, 2=locally optimal, >2=infeasible/error) | declarations.gms:9 |
| `p80_num_nonopt(t)` | time | (1) | Number of non-optimal variables (numNOpt) | declarations.gms:10 |
| `s80_counter` | scalar | (1) | Iteration counter for the retry loop | declarations.gms:14 |

**Note**: `nlp_ipopt`'s `declarations.gms` does **NOT** declare `s80_resolve_option` (it has no solver-cycling fallback). `nlp_apr17`'s `declarations.gms` does.

**Inputs** (input.gms:8-12):

| Scalar | Default | Unit | Description | Reference |
|--------|---------|------|-------------|-----------|
| `s80_maxiter` | 30 | (1) | Maximum solve iterations if modelstat > 2 | input.gms:9 |
| `s80_optfile` | 1 | (1) | Switch to use specified solver settings (0=default, 1=use `ipopt.opt`) | input.gms:10 |
| `s80_toloptimal` | 1e-08 | (1) | Ipopt solver tolerance (written as the `tol` option) | input.gms:11 |

**Note**: `nlp_ipopt`'s `input.gms` does **NOT** declare `s80_secondsolve` (no second-solve mechanism). `s80_toloptimal` here feeds the Ipopt `tol` option (`nlp_apr17` uses the same scalar for the CONOPT4 `Tol_Optimality` option). The `c80_nlp_solver` switch is **not** used by `nlp_ipopt` — that switch applies only to `lp_nlp_apr17` (config comment, `config/default.cfg:2287`).

**No `equations` defined** — like all Module 80 realizations, `nlp_ipopt` defines zero model equations; it is pure solver-control logic.

### Files (nlp_ipopt)

| File | Lines | Purpose |
|------|-------|---------|
| `realization.gms` | 20 | Phase includes; description of the Ipopt direct-NLP strategy |
| `declarations.gms` | 15 | `p80_modelstat(t)`, `p80_num_nonopt(t)`, `s80_counter` |
| `input.gms` | 12 | `s80_maxiter`, `s80_optfile`, `s80_toloptimal` |
| `preloop.gms` | 10 | Declares `File` objects `optfile /ipopt.opt/` and `optfile2 /ipopt.op2/` |
| `solve.gms` | 111 | Writes Ipopt option files, primary solve, retry loop, finalization |

### Key Differences from nlp_apr17 (default) and lp_nlp_apr17

| Feature | lp_nlp_apr17 | nlp_apr17 (default) | nlp_ipopt |
|---------|--------------|---------------------|-----------|
| NLP solver | CONOPT4 (+ CPLEX for LP) | CONOPT4 | **Ipopt** (interior-point) |
| LP warmstart | ✅ Yes | ❌ No | ❌ No |
| Requires `nl_fix`/`nl_release` | ✅ Yes | ❌ No | ❌ No |
| Retry strategy | Relax + retry LP, then NLP fallbacks | Cycle 4 strategies (CONOPT4 ×3 + CONOPT3) | Re-solve with **same** Ipopt settings |
| `s80_resolve_option` | ❌ Not declared (relax counted by s80_counter) | ✅ Declared (4-way cycle) | ❌ Not declared |
| `s80_secondsolve` | ✅ Declared | ✅ Declared | ❌ Not declared |
| Solver fallback to other solver | ✅ (CONOPT3) | ✅ (CONOPT3) | ❌ None |
| Land difference minimization | ✅ Yes | ❌ No | ❌ No |
| Option file(s) | `conopt4.opt`, `conopt4.op2` (CPLEX `cplex.opt`) | `conopt4.opt`, `conopt4.op2` | `ipopt.opt`, `ipopt.op2` (both via runtime `put`; cf. `conopt4.op2` via compile-time `$onecho`) |

---

## Realization: nlp_par (Parallel NLP - Regional Decomposition)

**Strategy**: Solve each MAgPIE region (superregion `h`) in parallel using asynchronous GAMS handles, enabling high-resolution spatial analysis (realization.gms:8-16).

**Critical Requirement**: Works ONLY with fixed trade patterns (Module 21 `exo` realization). Trade flows must be predetermined from a prior global optimization run (realization.gms:11-12).

**Use Case**: High-resolution runs (e.g., 0.5° resolution = 59,199 grid cells). Parallel solving by region reduces wall-clock time on multi-core systems.

**Workflow** (realization.gms:12-13):
1. Run global optimization (lp_nlp_apr17 or nlp_apr17) with low resolution (e.g., 200 cells)
2. Extract regional trade patterns
3. Fix trade in Module 21 (`exo` realization)
4. Run nlp_par with high-resolution cells, each region solved independently

### Parallel Solve Mechanism

**Step 1 - Initialize Handles** (solve.gms:8-30):

```gams
magpie.solvelink = 3;   // Asynchronous solve (submit, check later)
option threads = 1;     // Each regional solve uses 1 thread
```
(solve.gms:17-22)

Parameters for parallel tracking:
| Parameter | Dimensions | Description | Reference |
|-----------|------------|-------------|-----------|
| `p80_modelstat(t,h)` | time, superregion | Modelstat for each region | declarations.gms:9 |
| `p80_counter(h)` | superregion | Retry counter per region | declarations.gms:10 |
| `p80_handle(h)` | superregion | GAMS handle ID for async solve | declarations.gms:11 |
| `p80_extra_solve(h)` | superregion | Flag: 1 = needs retry, 0 = done | declarations.gms:12 |
| `p80_counter_modelstat(h)` | superregion | Counter for successful solves (modelstat ≤ 2) | declarations.gms:13 |
| `p80_resolve_option(h)` | superregion | Current fallback strategy (1-4) | declarations.gms:14 |

**Step 2 - Submission Loop** (submit all regions) (solve.gms:36-46):

```gams
loop(h,
  h2(h) = yes;                               // Activate current superregion
  i2(i)$supreg(h,i) = yes;                  // Activate regions in superregion h
  loop(i2, j2(j)$cell(i2,j) = yes);         // Activate cells in regions

  solve magpie USING nlp MINIMIZING vm_cost_glo;

  h2(h) = no;                                // Deactivate superregion
  i2(i) = no;                                // Deactivate regions
  j2(j) = no;                                // Deactivate cells

  p80_handle(h) = magpie.handle;            // Store handle for later collection
);
```
(solve.gms:37-46)

**Key mechanism**: By activating/deactivating set elements (`h2`, `i2`, `j2`), each solve only includes equations for one superregion. Regions are independent because trade is fixed.

**Step 3 - Collection Loop** (collect results asynchronously) (solve.gms:48-136):

Main loop structure:
```gams
repeat
  loop(h$p80_handle(h),   // Loop over regions with active handles
    if(handleStatus(p80_handle(h)) = 2,   // Status = 2: solve completed

      // COLLECT RESULT
      magpie.handle = p80_handle(h);
      execute_loadhandle magpie;

      // CHECK MODELSTAT
      if(p80_modelstat(t,h) > 2,
        // RETRY with fallback strategies
      else
        // SUCCESS: optionally second solve
      );

      // CLEANUP
      handledelete(p80_handle(h));

    );
  );

  // WAIT for next region to complete
  display$sleep(card(p80_handle)*0.2) 'sleep some time';
  display$readyCollect(p80_handle,INF) 'Problem waiting...';

until card(p80_handle) = 0 OR smax(h, p80_counter(h)) >= s80_maxiter;
```
(solve.gms:49-136)

**Step 4 - Retry Logic** (per region) (solve.gms:70-127):

If `p80_modelstat(t,h) > 2` (infeasible/error):

1. Increment counters: `p80_counter(h)`, `p80_resolve_option(h)`
2. Select fallback strategy (same 4 as nlp_apr17):
   - Attempt 1: CONOPT4 default
   - Attempt 2: CONOPT4 optfile
   - Attempt 3: CONOPT4 relaxed
   - Attempt 4: CONOPT3
3. Reactivate region sets (`h2`, `i2`, `j2`)
4. Resubmit solve for that region
5. Store new handle: `p80_handle(h) = magpie.handle`
6. Reset cycle if ≥ 4 attempts: `p80_resolve_option(h)$(p80_resolve_option(h) >= 4) = 0`

If `p80_counter(h) >= s80_maxiter`:
- Dump debug info: `gmszip -r magpie_problem.zip`
- Write LST file with solve details
- Clear handle: `p80_extra_solve(h) = 0`

**Step 5 - Success Handling** (per region) (solve.gms:82-94):

If `p80_modelstat(t,h) ≤ 2` (optimal/locally optimal):

Optional second solve (if `s80_secondsolve = 1` and first success):
```gams
if(p80_counter_modelstat(h) < 2 AND s80_secondsolve = 1,
  solve magpie USING nlp MINIMIZING vm_cost_glo;
  p80_handle(h) = magpie.handle;  // New handle for second solve
else
  p80_handle(h) = 0;  // Clear handle (done)
);
```
(solve.gms:84-93)

**Step 6 - Final Check** (solve.gms:137-140):

If ANY region failed:
```gams
if (smax(h,p80_modelstat(t,h)) > 2 and smax(h,p80_modelstat(t,h)) ne 7,
  Execute_Unload "fulldata.gdx";
  abort "No feasible solution found!";
);
```

### Key Differences from Other Realizations

| Feature | lp_nlp_apr17 | nlp_apr17 | nlp_par |
|---------|--------------|-----------|---------|
| Optimization scope | Global | Global | Regional (parallel) |
| Trade module | Any | Any | **MUST be `exo` (fixed trade)** |
| Spatial resolution | Any (typically 200 cells) | Any | High (e.g., 59,199 cells) |
| Parallel execution | No | No | ✅ Yes (by superregion) |
| Wall-clock time | Sequential solve | Sequential solve | Reduced (if multi-core) |
| Complexity | High | Low | Very high |
| Solve independence | N/A | N/A | Regions independent via fixed trade |

---

## Solver Configuration

### Linear Solvers (lp_nlp_apr17 only)

**CPLEX** (solve.gms:19-24):
- Used for LP warmstart phase
- Settings: 1 thread, default options (empty cplex.opt file)
- Purpose: Fast linear solver for convex problems

### Nonlinear Solvers

**CONOPT4** (used by `lp_nlp_apr17`, `nlp_apr17`, `nlp_par`) (lp_nlp_apr17/solve.gms:27-39, nlp_apr17/solve.gms:14-27, nlp_par/solve.gms:14-30):
- Modern NLP solver (successor to CONOPT3)
- Default tolerance: `Tol_Optimality = 1e-08`
- Optfile 1 (default): Custom tolerance
- Optfile 2 (fallback): Relaxed variable limits (`Lim_Variable = 1.e25`)

**CONOPT3** (fallback for `lp_nlp_apr17`, `nlp_apr17`, `nlp_par`) (lp_nlp_apr17/solve.gms:138-141, nlp_apr17/solve.gms:65-67):
- Older, more robust NLP solver
- Used as last resort when CONOPT4 fails
- Often succeeds on difficult problems where CONOPT4 encounters evaluation errors

**Ipopt** (used by `nlp_ipopt` only) (nlp_ipopt/solve.gms:13):
- Open-source interior-point (primal-dual barrier) NLP solver
- Selected via `option nlp = ipopt;`
- `nlp_ipopt` uses Ipopt exclusively — there is **no fallback to CONOPT**
- Two option files written from GAMS at runtime: `ipopt.opt` (monotone `mu_strategy`) and `ipopt.op2` (adaptive `mu_strategy`); see the `nlp_ipopt` realization section. `s80_toloptimal` feeds the Ipopt `tol` option.

### Solver Options

**magpie.optfile** (CONOPT realizations: lp_nlp_apr17/nlp_apr17/nlp_par input.gms:10):
- 0: Use solver defaults
- 1: Use custom options from `conopt4.opt` (default)
- 2: Use alternate options from `conopt4.op2` (relaxed limits)

For `nlp_ipopt` the same `s80_optfile` switch instead selects `ipopt.opt` (value 1, default); `ipopt.op2` would correspond to value 2 but is not activated by the current `nlp_ipopt` code (see the `nlp_ipopt` realization section).

**magpie.scaleopt** = 1 (all realizations):
- Enable automatic variable/equation scaling
- Improves numerical stability

**magpie.solprint** = 0 (normal), = 1 (if infeasible) (solve.gms:16, 174):
- 0: Suppress detailed solve output (normal)
- 1: Print full solve details to LST file (when debugging failures)

**magpie.holdfixed** = 1 (all realizations):
- Keep fixed variables out of basis
- Reduces basis size, improves solve efficiency

**magpie.trylinear** = 1 (lp_nlp_apr17 LP phase) (solve.gms:47):
- Signal GAMS to attempt linear solve if no nonlinearities detected
- Used after `nl_fix` fixations

**magpie.solvelink** = 3 (nlp_par only) (solve.gms:17):
- Asynchronous solve mode
- Returns immediately with handle, allows parallel submission

---

## Modelstat Codes

GAMS modelstat values used throughout Module 80:

| Modelstat | Meaning | Action in Module 80 |
|-----------|---------|---------------------|
| 1 | Optimal | ✅ Success: save results, continue to next timestep |
| 2 | Locally optimal | ✅ Success (NLP may be locally optimal, not globally) |
| 7 | Feasible solution | ⚠️ `nlp_apr17`: 7 `>2` so it enters the retry loop (solve.gms:47) and never hits the `<=2` success-exit; at finalization NO timestep GDX is saved (`<=2` required, :98) and NO abort (excluded by `ne 7`, :102). Silent limbo, not "success". |
| 13 | Error during solve | ❌ Retry (CONOPT realizations: CONOPT3/relaxed CONOPT4; `nlp_ipopt`: re-solve with Ipopt) |
| >2 (except 7) | Infeasible/unbounded/error | ❌ Retry up to s80_maxiter times, then ABORT |
| NA | Not available (evaluation error) | Set to 13, then retry (nlp_apr17/solve.gms:44, 87; nlp_ipopt/solve.gms:70, 91) |

**Note**: Modelstat values stored in `p80_modelstat(t)` (lp_nlp_apr17, nlp_apr17, nlp_ipopt) or `p80_modelstat(t,h)` (nlp_par) for diagnostics. `nlp_ipopt`'s `solve.gms` initializes `p80_modelstat(t) = 14` before solving (solve.gms:10), the same sentinel used by `nlp_apr17`.

---

## Model Options (main.gms)

Global GAMS options for MAgPIE model (main.gms):

```gams
option iterlim    = 1000000;   // Max solver iterations (1M)
option reslim     = 1000000;   // Max solver time in seconds (~278 hours)
option sysout     = Off;       // Suppress system output
option limcol     = 0;         // No column listing limit (full model)
```

**Purpose**: These generous limits ensure the solver has sufficient resources for large-scale optimization. MAgPIE runs can take hours to days per timestep for high-resolution configurations.

---

## Key Limitations and Design Decisions

### 1. **No Guarantee of Global Optimum** (Nonlinear Models)

**What the code does**: Solves nonlinear programming (NLP) problem using local solvers (CONOPT4, CONOPT3) (solve.gms:130, nlp_apr17/solve.gms:34).

**Limitation**: NLP solvers find locally optimal solutions, not globally optimal. The solution depends on:
- Starting point (LP warmstart in lp_nlp_apr17 provides better starting point)
- Solver algorithm (CONOPT4 interior-point vs. CONOPT3 augmented Lagrangian)
- Numerical conditioning (scaling, tolerances)

**Implication**: Different realizations may yield slightly different solutions, all locally optimal but potentially different global optimum.

---

### 2. **LP Warmstart Requires Module Cooperation** (lp_nlp_apr17 only)

**Requirement**: ALL nonlinear module realizations MUST provide three files (realization.gms:15-19):
1. `nl_fix.gms`: Fix nonlinear terms to best guesses
2. `nl_release.gms`: Release nonlinear terms after LP solve
3. `nl_relax.gms`: Relax fixations if LP is infeasible

**What happens if missing**: Model run cancelled by error (solve.gms:88-92):
```
"Unfixed nonlinear terms in linear solve!"
abort
```

**Current status**: All MAgPIE modules provide these files (verified by model functionality).

**Implication**: Adding new nonlinear equations requires updating `nl_fix`/`nl_release`/`nl_relax` files in the corresponding module realization.

---

### 3. **Fixed Trade Requirement for Parallel Solving** (nlp_par only)

**Requirement**: Module 21 (Trade) MUST use `exo` realization (fixed trade patterns) (realization.gms:11-12).

**Reason**: Parallel regional solves are independent only if trade flows are predetermined. Endogenous trade (Module 21 `selfsuff_*` realizations) creates interdependencies between regions, breaking parallelizability.

**Workflow**:
1. Run global model with endogenous trade → get trade patterns
2. Fix trade patterns in Module 21 `exo` realization
3. Run nlp_par with high-resolution cells

**Implication**: nlp_par cannot explore trade policy scenarios or endogenous trade responses. It's a spatial downscaling tool, not a trade policy tool.

---

### 4. **Land Difference Minimization Only in lp_nlp_apr17**

**What lp_nlp_apr17 does**: After optimal solution found, minimize `vm_landdiff` subject to cost constraint (solve.gms:74-79):
```gams
vm_cost_glo.up = vm_cost_glo.l;
solve magpie USING nlp MINIMIZING vm_landdiff;
vm_cost_glo.up = Inf;
```

**Purpose**: Select among multiple cost-equivalent solutions the one with least land use change.

**What nlp_apr17, nlp_ipopt, and nlp_par do**: NO land difference minimization step. They return the first optimal solution found.

**Implication**: nlp_apr17, nlp_ipopt, and nlp_par may exhibit more land use volatility between timesteps compared to lp_nlp_apr17, even if costs are identical.

---

### 5. **No Parallelization Within Regions** (nlp_par)

**What nlp_par does**: Solves each superregion `h` in parallel (e.g., 10 superregions on 10 cores) (solve.gms:37-46).

**What it does NOT do**: Parallelize within a region (e.g., split 5,920 cells in one superregion across multiple cores).

**Implication**: Wall-clock speedup limited to number of superregions (typically 10), not number of cells (can be 59,199). Single-region problems (e.g., Europe-only scenario) see no speedup from nlp_par.

---

### 6. **Fallback Strategies May Not Converge**

**Retry limit**: All realizations retry up to `s80_maxiter` times (default: 30) (input.gms:9).

**What happens if all retries fail**:
1. Dump full data: `Execute_Unload "fulldata.gdx"`
2. ABORT: "no feasible solution found!"
3. Model run terminates

**Causes of persistent infeasibility**:
- Model parameterization errors (e.g., negative land area from configuration mistake)
- Binding constraints (e.g., insufficient cropland + forest to meet food + timber demand)
- Numerical issues (e.g., poorly scaled equations)
- True infeasibility (e.g., conflicting policy constraints)

**Implication**: Module 80 has no mechanism to "skip" an infeasible timestep. Model run must terminate. User must diagnose and fix the underlying issue.

---

### 7. **Second Solve Statement (`s80_secondsolve`) Purpose Unclear**

**What the code does**: If `s80_secondsolve = 1`, repeat each solve statement immediately (solve.gms:66, 77, 131, 140, 190, etc.).

**Documented purpose**: "Improved model results, in particular for matching LHS and RHS of equations" (solve.gms:62-63).

**Observation**: Default is 0 (disabled) (input.gms:11). Rarely enabled in practice.

**Limitation**: No clear explanation WHY a second identical solve would improve results. Possibly historical artifact or numerical stability mechanism.

**Implication**: Users may be uncertain whether to enable this flag. Doubling solve count increases runtime with unclear benefit.

**Note**: `s80_secondsolve` exists only in `lp_nlp_apr17`, `nlp_apr17`, and `nlp_par`. The `nlp_ipopt` realization has **no** `s80_secondsolve` scalar and no second-solve step.

---

### 8. **Modelstat 7 (Feasible) Lands in Silent Limbo (default `nlp_apr17`)**

In the **default `nlp_apr17`** realization, modelstat 7 is NOT treated as success. Because 7 `> 2` it enters the retry loop (`nlp_apr17/solve.gms:47`) and never satisfies the success-exit `modelstat <= 2` (`:91`), so a solver that keeps returning 7 burns all `s80_maxiter` (30) retries. At finalization it falls into a gap between the two end-of-solve checks:

```gams
if ((p80_modelstat(t) <= 2), ... mv -f magpie_p.gdx magpie_<t>.gdx);   * :98  - 7 fails <=2 -> NO timestep GDX written
if ((p80_modelstat(t) > 2 and p80_modelstat(t) ne 7), ... abort);      * :102 - 7 is excluded -> NO abort
```

So modelstat 7 saves no timestep GDX and triggers no abort: the run continues with no `magpie_<year>.gdx` for that step and no console error. Only `magpie.solprint = 1` (extended .lst output, `:79-81`) fires near the iteration cap.

**Where the `modelstat=1 or 7` gate actually lives**: that snippet is in the **non-default `lp_nlp_apr17`** realization (`lp_nlp_apr17/solve.gms:74,194`), and there it is NOT a generic success check - it is the gate that, once the cost solve succeeds, fixes `vm_cost_glo.up = vm_cost_glo.l` and runs the secondary `vm_landdiff` minimization. It does not exist in `nlp_apr17`. (The earlier version of this note mislabeled that gate as a default-realization "success check".)

**Implication**: A persistent modelstat-7 case in the default realization yields a missing-GDX timestep with no abort. Diagnose via `p80_modelstat(t)`, not just the presence/absence of an abort.

---

### 9. **No Time Limit per Timestep**

**What the code does**: Sets global resource limit `reslim = 1000000` (seconds ≈ 278 hours) (main.gms).

**What it does NOT do**: Limit solve time per timestep. A single difficult timestep can consume days of compute time.

**Implication**: If one timestep becomes computationally intractable (e.g., due to binding constraint or poor scaling), the entire model run stalls. No automatic failover or timeout per timestep.

---

### 10. **Asynchronous Handle Management Complexity** (nlp_par)

**Complexity**: nlp_par uses GAMS asynchronous solve API with handle submission, status checking, collection, and deletion (solve.gms:36-136).

**Error-prone aspects**:
- Handle leaks if `handledelete` fails (solve.gms:80)
- Race conditions in handle status checking (solve.gms:51)
- NA modelstat requires special handling (solve.gms:66, 87)
- Sleep/wait mechanisms for coordination (solve.gms:133-134)

**Implication**: nlp_par is the most complex realization, hardest to debug, and most susceptible to subtle bugs in parallel execution.

**Current status**: Code includes error handling for most issues (solve.gms:74-77, 80, 118), but parallel execution remains inherently more fragile than sequential.

---

## Computational Performance Considerations

### Runtime Comparison (Illustrative Example)

**Scenario**: Global MAgPIE run, 200 grid cells, 15 timesteps (1995-2100), standard resolution

**lp_nlp_apr17** (LP warmstart + NLP):
- LP warmstart: 30-60 seconds per timestep
- NLP solve: 5-15 minutes per timestep
- Land difference minimization: 1-3 minutes per timestep
- **Total per timestep**: ~7-20 minutes
- **Full run**: ~2-5 hours

**nlp_apr17** (Direct NLP):
- NLP solve: 10-25 minutes per timestep (worse initial point)
- **Total per timestep**: ~10-25 minutes
- **Full run**: ~3-7 hours

**nlp_par** (Parallel NLP, 10 regions on 10 cores):
- Submission overhead: 1-2 minutes
- NLP solve per region: 15-30 minutes (high-resolution, 59,199 cells)
- Wall-clock (parallel): 15-30 minutes (if balanced)
- **Total per timestep**: ~20-35 minutes wall-clock
- **Full run**: ~5-9 hours wall-clock

*Note: These are made-up numbers for illustration. Actual runtimes depend on hardware, model complexity, scenario, and solver tuning. High-resolution runs (59,199 cells) with nlp_par can take 12-48 hours even with parallelization.*

### When to Use Each Realization

**Use lp_nlp_apr17 when**:
- Standard global optimization (200-1000 cells)
- Minimizing land use volatility is important
- Compute time is not critical bottleneck
- All modules provide `nl_fix`/`nl_release` files

**Use nlp_apr17 when** (the default):
- LP warmstart doesn't improve convergence (test by comparing runtimes)
- Simpler code path preferred (fewer files to maintain)
- Small model (few cells, few constraints)
- Rapid prototyping (avoid `nl_fix` file creation)

**Use nlp_ipopt when**:
- A non-CONOPT solver is needed (e.g., to cross-check solutions, or where the CONOPT family struggles)
- The Ipopt interior-point method is preferred or known to converge better on the problem
- Note: this realization has no solver fallback — if Ipopt fails, every retry is another Ipopt solve with the same settings

**Use nlp_par when**:
- Very high spatial resolution required (>10,000 cells)
- Multi-core hardware available (10+ cores)
- Trade patterns fixed (spatial downscaling, not trade policy)
- Wall-clock time more important than CPU-hours
- Willing to accept complexity of parallel execution

---

## Module Interfaces

### Upstream Dependencies

Module 80 depends on ALL modules to:
1. Define equations correctly (syntactically and semantically)
2. Provide `nl_fix`/`nl_release`/`nl_relax` files if nonlinear (lp_nlp_apr17 only)
3. Declare variables with appropriate bounds and initial values

**No explicit parameter/variable inputs**: Module 80 uses the entire model's variable and equation structure.

### Downstream Effects

**CRITICAL**: Module 80's solution (optimal variable values) affects ALL modules in subsequent phases:
- **postsolve**: Modules read optimal variable values (`.l` levels)
- **output**: Report generation uses optimal solution

**Example**: Module 50 (NR Soil Budget) reads `v50_nr_surplus_cropland.l` (optimal nitrogen surplus) in postsolve to calculate cumulative soil degradation.

---

## Related Configuration Files

Module 80 behavior controlled by main configuration switches in `config/default.cfg`:

**cfg$gms$optimization** (module realization):
- "nlp_apr17" (default)
- "lp_nlp_apr17"
- "nlp_ipopt" (Ipopt interior-point solver, alternative)
- "nlp_par"

**cfg$gms$c80_nlp_solver** (solver selection — applies to `lp_nlp_apr17` only; see `config/default.cfg:2287`):
- "conopt4" (default)
- "conopt4+cplex"
- "conopt4+conopt3"

**cfg$gms$s80_maxiter** (override default 30):
- Increase for difficult convergence (e.g., 50)
- Decrease for faster failure detection (e.g., 10)
- Used by all realizations, including `nlp_ipopt`

**cfg$gms$s80_secondsolve** (enable double-solve):
- 0 (default, disabled)
- 1 (enabled, doubles solve count)
- Not present in `nlp_ipopt` (that realization has no second-solve mechanism)

**cfg$gms$s80_toloptimal** (solver optimality tolerance):
- 1e-08 (default, tight)
- 1e-06 (looser, faster but less accurate)
- 1e-10 (tighter, slower but more accurate)
- Feeds CONOPT4's `Tol_Optimality` in the CONOPT realizations, and Ipopt's `tol` option in `nlp_ipopt`

⚠️ **Config-comment gap (as of 2026-05-16)**: `config/default.cfg` registers the `nlp_ipopt` realization in code, but the realization-comment block above the `cfg$gms$optimization` line (`config/default.cfg:2266-2278`) still lists only `nlp_apr17`, `lp_nlp_apr17`, and `nlp_par`. `nlp_ipopt` is selectable, just not yet described in that comment block.

---

## Summary of File Locations

| Realization | Key Files | Purpose |
|-------------|-----------|---------|
| lp_nlp_apr17 | `modules/80_optimization/lp_nlp_apr17/solve.gms` | LP warmstart + NLP solve loop |
| lp_nlp_apr17 | `modules/80_optimization/lp_nlp_apr17/input.gms:8-13` | Configuration scalars |
| lp_nlp_apr17 | `modules/80_optimization/lp_nlp_apr17/declarations.gms` | Parameters and scalars |
| nlp_apr17 | `modules/80_optimization/nlp_apr17/solve.gms:7-109` | Direct NLP solve with 4-strategy fallback loop |
| nlp_apr17 | `modules/80_optimization/nlp_apr17/input.gms:8-13` | Configuration scalars (`s80_maxiter`, `s80_optfile`, `s80_secondsolve`, `s80_toloptimal`) |
| nlp_apr17 | `modules/80_optimization/nlp_apr17/declarations.gms:8-16` | Parameters and scalars (incl. `s80_resolve_option`) |
| nlp_ipopt | `modules/80_optimization/nlp_ipopt/solve.gms:7-111` | Direct NLP solve with Ipopt; writes `ipopt.opt`/`ipopt.op2`; same-settings retry loop |
| nlp_ipopt | `modules/80_optimization/nlp_ipopt/input.gms:8-12` | Configuration scalars (`s80_maxiter`, `s80_optfile`, `s80_toloptimal` — no `s80_secondsolve`) |
| nlp_ipopt | `modules/80_optimization/nlp_ipopt/declarations.gms:8-15` | Parameters and `s80_counter` (no `s80_resolve_option`) |
| nlp_ipopt | `modules/80_optimization/nlp_ipopt/preloop.gms:9-10` | `File` objects `ipopt.opt` and `ipopt.op2` |
| nlp_par | `modules/80_optimization/nlp_par/solve.gms` | Parallel NLP with handle management |
| nlp_par | `modules/80_optimization/nlp_par/input.gms` | Configuration scalars (same as others) |
| nlp_par | `modules/80_optimization/nlp_par/declarations.gms` | Parameters for parallel tracking |
| ALL | `modules/80_optimization/module.gms:23-28` | Module interface and realization selection |
| nlp_apr17 / nlp_par | `preloop.gms:8` | `conopt4.opt` optfile declaration |

---

## Citation Summary

**Total file:line citations**: 100+

**Key references**:
- Module overview: `modules/80_optimization/module.gms:8-21`
- Realization registration: `modules/80_optimization/module.gms:23-28`
- lp_nlp_apr17 strategy: `modules/80_optimization/lp_nlp_apr17/realization.gms:8-19`
- nlp_apr17 strategy: `modules/80_optimization/nlp_apr17/realization.gms:8-12`
- nlp_apr17 solve loop: `modules/80_optimization/nlp_apr17/solve.gms:7-109`
- nlp_ipopt strategy: `modules/80_optimization/nlp_ipopt/realization.gms:8-13`
- nlp_ipopt solve loop: `modules/80_optimization/nlp_ipopt/solve.gms:7-111`
- nlp_ipopt Ipopt option-file writing: `modules/80_optimization/nlp_ipopt/solve.gms:16-50`
- nlp_par strategy: `modules/80_optimization/nlp_par/realization.gms:8-16`
- Model declaration: `main.gms` (model magpie / all - m15_food_demand /)

---

## Quality Assurance

**Verification Date**: 2025-10-12 (initial, 3 realizations); 2026-05-16 sync update (added `nlp_ipopt`)

**Verification Method**:
- ✅ Read all source files for the original 3 realizations (lp_nlp_apr17, nlp_apr17, nlp_par)
- ✅ Verified equation count: 0 (Module 80 defines no model equations)
- ✅ Verified interface variables: 2 (vm_cost_glo, vm_landdiff)
- ✅ Traced solve sequences for all realizations
- ✅ Documented all fallback strategies
- ✅ Verified all parameter declarations against source
- ✅ Confirmed all file:line citations by direct file reading

**2026-05-16 sync update** (commit 9cba74ab7, PR #871):
- ✅ Read all 5 new `nlp_ipopt/*.gms` files (realization, declarations, input, preloop, solve) and `module.gms`
- ✅ Verified `nlp_ipopt` registration in `module.gms:26`
- ✅ Verified `nlp_apr17` remains the default in `config/default.cfg:2282`
- ✅ Verified `nlp_ipopt` scalars/parameters against `declarations.gms` and `input.gms`
- ✅ Verified `nlp_ipopt`'s solve sequence and Ipopt option-file writing against `solve.gms`

**Completeness**:
- Equation count: 0/0 ✅
- Realizations documented: 4/4 ✅
- Parameters documented: 100% ✅
- Solver configurations: 100% ✅
- Limitations catalogued: 10 ✅

**No arithmetic verification required** (Module 80 contains no mathematical formulas in model equations, only solver control logic).

**Illustrative examples clearly labeled** (e.g., runtime comparison: explicitly stated as "made-up numbers for illustration").

---

**END OF MODULE 80 DOCUMENTATION**
---

## Participates In

### Conservation Laws

**Not in conservation laws** (optimization objective aggregator)

**Role**: Aggregates all cost components into global objective function

### Dependency Chains

**Centrality**: TERMINAL (final aggregator)
**Hub Type**: Optimization Objective
**Depends on**: Module 11 (costs) - aggregated costs
**Provides to**: NONE (terminal node - solver minimizes this)

### Circular Dependencies

None (terminal aggregator)

### Modification Safety

**Risk Level**: 🔴 **HIGH RISK** (Objective function)
**Why**: Changes affect what model optimizes for
**Testing**: Verify objective components weighted correctly, check solution makes economic sense

**Details**: `core_docs/Module_Dependencies.md`

---

**Module 80 Status**: ✅ COMPLETE

---

**Last Verified**: 2026-05-16
**Verified Against**: `../modules/80_optimization/module.gms`, `../modules/80_optimization/nlp_ipopt/*.gms`, `../modules/80_optimization/nlp_apr17/*.gms`
**Verification Method**: Realizations cross-referenced with source code; new `nlp_ipopt` realization read in full
**Changes Since Last Verification**: Added `nlp_ipopt` realization (MAgPIE `develop` commit 9cba74ab7, PR #871 — Ipopt as an alternative solver). `nlp_apr17` remains the default.
