# R25-Q2: Solver-Control Scalars in MAgPIE's Default Optimization Realization

## Active Realization

The default optimization realization is **`nlp_apr17`**, confirmed by `config/default.cfg`:
`cfg$gms$optimization <- "nlp_apr17"`.

This realization solves the full nonlinear MAgPIE problem directly via CONOPT4, without an LP warmstart, using a 4-strategy cyclic fallback loop on failure. 🟡 (module_80.md, "Realization: nlp_apr17 (DEFAULT - Direct NLP)")

---

## Solver-Control Scalars in `nlp_apr17` (Default)

All four scalars are declared in `nlp_apr17/input.gms:8-13` and one additional scratch scalar in `nlp_apr17/declarations.gms:13-14`. 🟡

| Scalar | Default | Source | Role |
|--------|---------|--------|------|
| `s80_maxiter` | 30 | `nlp_apr17/input.gms:9` | Max re-solve attempts before ABORT |
| `s80_optfile` | 1 | `nlp_apr17/input.gms:10` | Optfile selector (0=solver defaults, 1=`conopt4.opt`, 2=`conopt4.op2` with relaxed limits) |
| `s80_secondsolve` | 0 | `nlp_apr17/input.gms:11` | Binary: repeat each solve statement once (0=off, 1=on) |
| `s80_toloptimal` | 1e-08 | `nlp_apr17/input.gms:12` | CONOPT4 optimality tolerance (`Tol_Optimality`) |
| `s80_resolve_option` | 0 (counter) | `nlp_apr17/declarations.gms:14` | Internal cycle index (1-4) driving the 4-strategy fallback loop; resets after each cycle |

### What each scalar does

**`s80_maxiter` = 30** (`nlp_apr17/input.gms:9`): The retry loop in `nlp_apr17/solve.gms:47-93` runs until `s80_counter >= s80_maxiter`. With 4 strategies per cycle, 30 iterations means up to 7 full cycles (CONOPT4-default, CONOPT4-optfile, CONOPT4-relaxed, CONOPT3, ...) before the model ABORTs and dumps `fulldata.gdx`. 🟡

**`s80_optfile` = 1** (`nlp_apr17/input.gms:10`): Passed directly to `magpie.optfile` at solve.gms:16 (`magpie.optfile = s80_optfile`). Value 1 activates the custom `conopt4.opt` file (tight tolerance); value 0 uses CONOPT4's built-in defaults; value 2 activates `conopt4.op2` (relaxed `Lim_Variable = 1.e25`). The retry loop itself overrides `magpie.optfile` transiently as it cycles through strategies, but the initial solve uses this scalar's value. 🟡

**`s80_secondsolve` = 0** (`nlp_apr17/input.gms:11`): When set to 1, each solve statement is immediately repeated:
```gams
solve magpie USING nlp MINIMIZING vm_cost_glo;
if(s80_secondsolve = 1, solve magpie USING nlp MINIMIZING vm_cost_glo; );
```
(`nlp_apr17/solve.gms:34-36`). The documented purpose is "improved model results, in particular for matching LHS and RHS of equations." Default is 0 (disabled). 🟡

**`s80_toloptimal` = 1e-08** (`nlp_apr17/input.gms:12`): Written into the CONOPT4 option file at runtime as `Tol_Optimality = s80_toloptimal` (`nlp_apr17/solve.gms:22-27`). Tighter values improve solution accuracy; looser values (e.g., 1e-06) reduce solve time. 🟡

**`s80_resolve_option`** (`nlp_apr17/declarations.gms:14`): Not an input scalar but a runtime scratch counter. Increments 1-4 each retry and drives the 4-strategy cycle in the fallback loop (`solve.gms:48-92`):
- 1: CONOPT4 with default settings (optfile=0)
- 2: CONOPT4 with custom optfile (optfile=1)
- 3: CONOPT4 with relaxed limits (optfile=2, `Lim_Variable = 1.e25`)
- 4: CONOPT3 (older, more robust solver)

Resets to 0 when it reaches 4: `s80_resolve_option$(s80_resolve_option >= 4) = 0`. This scalar is unique to `nlp_apr17` and absent from `lp_nlp_apr17`. 🟡

---

## NLP Relaxation Note

`nlp_apr17` performs no explicit NLP relaxation in the sense of fixing nonlinear terms (that is the LP-warmstart mechanism of `lp_nlp_apr17`). The NLP "relaxation" in `nlp_apr17` is accomplished via `s80_resolve_option = 3`: switching CONOPT4 to optfile 2 with `Lim_Variable = 1.e25`, which relaxes internal variable-bound checking and can recover from evaluation errors (modelstat 13). 🟡 (`nlp_apr17/solve.gms:47-93`)

---

## Contrast with the Alternative Realization: `lp_nlp_apr17`

`lp_nlp_apr17` has a related but distinct scalar set (`lp_nlp_apr17/input.gms:8-13`). Three scalars differ meaningfully: 🟡

| Scalar | `nlp_apr17` (default) | `lp_nlp_apr17` (alternative) | Difference |
|--------|----------------------|------------------------------|------------|
| `s80_resolve_option` | Declared at `nlp_apr17/declarations.gms:14`; drives 4-strategy cyclic retry (CONOPT4 x3 + CONOPT3) | **Not declared** in `lp_nlp_apr17` | `lp_nlp_apr17` uses a different fallback logic (LP-relax via `nl_relax.gms`, then CONOPT3/CPLEX polish); the cyclic 4-strategy loop does not exist there |
| `s80_obj_linear` | **Not declared** in `nlp_apr17` | Declared at `lp_nlp_apr17/declarations.gms:15`; stores LP-phase objective value | `nlp_apr17` has no LP phase and therefore no need to record its objective |
| `s80_secondsolve` | Declared in `nlp_apr17/input.gms:11`, default **0** | Declared in `lp_nlp_apr17/input.gms:11`, default **0** | Same default, but in `lp_nlp_apr17` the second solve fires after both the LP solve and the NLP solve (two distinct injection points), whereas in `nlp_apr17` it fires only after the single NLP solve |

The four input scalars `s80_maxiter`, `s80_optfile`, `s80_secondsolve`, and `s80_toloptimal` carry the same defaults in both realizations (30, 1, 0, 1e-08 respectively). The declaration-level divergence is `s80_resolve_option` (only `nlp_apr17`) vs. `s80_obj_linear` (only `lp_nlp_apr17`), reflecting their fundamentally different fallback architectures. 🟡 (`nlp_apr17/declarations.gms:8-16`; `lp_nlp_apr17/declarations.gms:8-16`)

---

## Summary Table

| Scalar | Default | File:line | Controls |
|--------|---------|-----------|----------|
| `s80_maxiter` | 30 | `nlp_apr17/input.gms:9` | Max re-solve attempts |
| `s80_optfile` | 1 | `nlp_apr17/input.gms:10` | Initial optfile selection (0/1/2) |
| `s80_secondsolve` | 0 | `nlp_apr17/input.gms:11` | Repeat each solve immediately (binary) |
| `s80_toloptimal` | 1e-08 | `nlp_apr17/input.gms:12` | CONOPT4 optimality tolerance |
| `s80_resolve_option` | 0 | `nlp_apr17/declarations.gms:14` | Runtime cycle index for 4-strategy fallback |

---

Based on module_80.md documentation (verified 2026-05-16 against `nlp_apr17/*.gms` and `lp_nlp_apr17/*.gms`).
