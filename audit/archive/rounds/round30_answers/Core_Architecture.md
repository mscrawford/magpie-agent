# MAgPIE Execution Sequence and Timestep Loop

## Overview

MAgPIE's execution follows a strict sequential phase structure. All phases run across all 46 modules before the next phase begins — the model does not run one module end-to-end, then the next. The entry point is `main.gms`, which dispatches each phase via `$batinclude "./modules/include.gms" [phase]`.

---

## Part 1: Pre-Loop Phases (Run Once, Before Any Timestep)

These phases fire in order across all modules. Each phase completes for all 46 modules before the next begins.

### 1. sets

`$batinclude "./modules/include.gms" sets` — each module declares its module-specific sets and mappings. Core sets (spatial: `i`, `j`, `cell(i,j)`; temporal: `t_all`, `t`, `t_past`, `ct`, `pt`; product: `kall`; land: `land`; forest age: `ac`) are declared in `core/sets.gms` before this phase.

### 2. declarations

`$batinclude "./modules/include.gms" declarations` — each module declares all its variables (`v##_*`, `vm_*`), parameters (`p##_*`, `pm_*`, `f_*`, `i_*`), equations (`q##_*`), and scalars. No data is loaded yet.

### 3. input

`$batinclude "./modules/include.gms" input` — each module loads raw file data from its `input/` directory into `f_` parameters (file parameters). Approximately 172 files (~72 MB compressed) are loaded in formats `.cs2`, `.cs3`, `.cs4`, `.mz`, `.csv`. Example: Module 14 loads `lpj_yields.cs3` into `f14_yields(t_all,j,kve,w)`. Scenario filters and `m_fillmissingyears()` calls happen here.

### 4. equations

`$batinclude "./modules/include.gms" equations` — each module defines its optimization equations. The complete MAgPIE model is then declared in `main.gms`:

```gams
model magpie / all - m15_food_demand /;
```

This includes all equations from all active realizations except the food demand model (`m15_food_demand`), which runs as a separate coupled model.

### 5. scaling

`$batinclude "./modules/include.gms" scaling` — each module sets variable scaling factors. Combined with the global solver option `magpie.scaleopt = 1`, this improves numerical stability for the NLP.

### 6. start / preloop

`$batinclude "./modules/include.gms" start` — one-time initialization. Then `$batinclude "./modules/include.gms" preloop` — runs ONCE before the timestep loop begins, not once per timestep. Modules use preloop for calibrations that depend on the initialized state, for example Module 14 computes FAO-calibrated yields (`i14_yields_calib`). Module 80 (`nlp_apr17` realization) uses `preloop.gms` to declare the CONOPT4 option file object (`conopt4.opt`); `nlp_ipopt` declares both `ipopt.opt` and `ipopt.op2` in its `preloop.gms`.

---

## Part 2: The Timestep Loop (5-Year Steps, 1995-2100 by Default)

After preloop completes, `main.gms` enters a GAMS `loop` over the set `t`. At each timestep:

```
ct(t) = yes   # activate current timestep element
pt(t-1) = yes # activate previous timestep element
```

The following phases then execute inside the loop:

### Step A: presolve_ini

`$batinclude "./modules/include.gms" presolve_ini`

Runs before `presolve`. Its primary purpose is setting variable bounds that must be in place before any other presolve logic. The canonical user is Module 22 (land conservation), which sets `vm_land.lo(j,land_natveg)` based on `pm_land_conservation(t,j,land,"protect")`. Separating this from `presolve` ensures bounds are locked before other modules read them.

### Step B: presolve

`$batinclude "./modules/include.gms" presolve`

Every module's `presolve.gms` runs here, across all modules, before the solver fires. This is where modules update dynamic parameters for the current timestep using results from the *previous* timestep's solution. Examples:

- Module 35 progresses forest age classes: `p35_secdforest(t,j,ac) = pc35_secdforest(j,ac-1)` (5-year age-class shift).
- Module 35 applies disturbance loss rates from input data: `p35_disturbance_loss_secdf(t,j,ac) = pc35_secdforest(j,ac) * f35_forest_lost_share(i,"fires")`.
- Modules update `vm_land.lo` / `vm_land.up` variable bounds based on state carried over via `pcm_*` parameters (the `pcm_` prefix indicates cross-module parameters that hold state across timesteps).

Critically, **presolve runs before the solve**. At this point the optimizer has not yet been called for timestep `t`. Modules are preparing the problem for the solver, not reading the solution.

### Step C: The Intersolve Loop (solve + intersolve, iterated)

```gams
while(sm_intersolve = 0,
    $batinclude "./modules/include.gms" solve
    $batinclude "./modules/include.gms" intersolve
);
```

`sm_intersolve` is a scalar flag. The loop fires at least once (since `sm_intersolve` starts at 0) and continues iterating until Module 15 sets `sm_intersolve = 1`.

**solve phase** — only Module 80 does meaningful work here. All other modules' `solve.gms` files are stubs or empty. Module 80 calls:

```gams
solve magpie USING nlp MINIMIZING vm_cost_glo;
```

minimizing total global costs (`vm_cost_glo`, provided by Module 11). The default realization is `nlp_apr17` (CONOPT4 NLP solver). On infeasibility, a fallback retry loop cycles through up to four strategies (CONOPT4 default / CONOPT4 optfile / CONOPT4 relaxed limits / CONOPT3) up to `s80_maxiter` (default: 30) times. On persistent failure the model dumps `fulldata.gdx` and ABORTs. The alternative realization `lp_nlp_apr17` runs an LP warmstart (CPLEX) before the NLP, and also does a secondary `vm_landdiff` minimization after cost-optimality; `nlp_ipopt` uses the Ipopt interior-point solver instead of CONOPT4.

**intersolve phase** — Module 15 (food demand) checks whether the food demand system has converged with the land-use optimizer's solution. If not, it updates food demand parameters and resets `sm_intersolve = 0`, causing another solve iteration. Convergence typically requires 2-5 iterations. When converged, it sets `sm_intersolve = 1`, exiting the while loop.

**The relationship between presolve and solve is strict**: presolve always completes across all modules before the first call to the solver within a given timestep. The intersolve loop may then trigger multiple additional solve calls, but no further presolve phase occurs within a timestep.

### Step D: postsolve

`$batinclude "./modules/include.gms" postsolve`

Runs once per timestep, after the while loop exits (i.e., after the final solve has produced a converged solution). Each module's `postsolve.gms` reads optimal variable levels (`.l` attribute) and marginals (`.m` attribute) and:

1. Stores results in `o_*` output parameters and `x_*` critical output parameters.
2. Updates `pc*` carry-forward parameters (e.g., `pcm_land(j,land) = vm_land.l(j,land)`) so that the next timestep's `presolve` has access to the current solution.
3. Extracts equation-level information (level, marginal, upper, lower bounds), for example:
   ```gams
   oq52_emis_co2_actual(t,i,emis_oneoff,"level") = q52_emis_co2_actual.l(i,emis_oneoff);
   ```

**postsolve runs after the solve, using the final converged optimal solution.** This is the mirror of presolve: presolve prepares parameters for the optimizer; postsolve extracts the optimizer's output and carries state forward.

### Step E: GDX dump and timestep advance

```gams
Execute_Unload "fulldata.gdx";
```

The complete model state is written to `fulldata.gdx` (50-100 MB per timestep). `ct` and `pt` are cleared, and the loop advances to the next 5-year step.

---

## Summary: Phase Ordering Relative to the Solve

```
[ONCE PER RUN]
  sets → declarations → input → equations → scaling → start → preloop

[EACH TIMESTEP]
  presolve_ini    (bounds setup, BEFORE solve)
  presolve        (dynamic parameter updates, BEFORE solve)
  WHILE not converged:
    solve         (Module 80: NLP optimization via CONOPT4/Ipopt)
    intersolve    (Module 15: food demand coupling, sets convergence flag)
  postsolve       (result extraction + carry-forward, AFTER final solve)
  Execute_Unload "fulldata.gdx"
```

The key ordering rule: all module `presolve` hooks complete before any module's `solve` fires. All module `postsolve` hooks fire after the final converged solve, using `.l` levels from the optimizer's solution.

---

## Sources

- 🟡 Core_Architecture.md (Section 5.1 Phase Execution Order, Section 5.2 Time Step Execution)
- 🟡 Data_Flow.md (Section 3.1-3.5, loop structure)
- 🟡 module_80.md (Solve sequence for `nlp_apr17` and all realizations; model declaration; intersolve flag; postsolve commentary)

Epistemic status: All claims are drawn from the magpie-agent AI documentation (🟡 Documented). No raw GAMS source was read this session per the question's constraint. Line numbers for main.gms (e.g., "line 279" for model declaration) are as recorded in Core_Architecture.md at its last verification date and may have drifted with subsequent MAgPIE commits.
