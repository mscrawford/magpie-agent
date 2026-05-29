# Circular Dependency: Land / Carbon (Modules 10 and 56)

## The dependency

Module 10 (`landmatrix_dec18`) decides how land is allocated across seven land pools
(`vm_land(j,land)`). Module 56 (`price_aug22`) prices the CO2 implied by those land
allocations using the change in carbon stocks between timesteps. If both directions were
active within the same timestep — land allocation affecting carbon stocks, carbon costs
affecting land allocation — the system would be circular: the optimizer could not form a
consistent LP/NLP.

The data flow is:

```
Module 10  vm_land(j,land)          →   Module 52 calculates vm_carbon_stock(j,land,c_pools,type)
Module 56  reads vm_carbon_stock         to compute one-off CO2 emission costs
Module 56  vm_cost_reg(i,"co2_c")   →   Module 11 aggregates into vm_cost_glo (objective)
Module 11  vm_cost_glo              →   drives land allocation decisions back in Module 10
```

That is a genuine loop: land → carbon stocks → emission costs → objective → land.

---

## The resolution mechanism: one lagged variable breaks the loop

Module 56's equation `q56_emis_pricing_co2` calculates the CO2 flow subject to pricing
as:

```gams
q56_emis_pricing_co2(i2,emis_oneoff) ..
  v56_emis_pricing(i2,emis_oneoff,"co2_c") =e=
    sum((cell(i2,j2),emis_land(emis_oneoff,land,c_pools)),
      (pcm_carbon_stock(j2,land,c_pools,"actual")
       - vm_carbon_stock(j2,land,c_pools,"%c56_carbon_stock_pricing%"))
      / m_timestep_length);
```

(`equations.gms:19-22`, documented in module_56.md Section 2.2)

The term `pcm_carbon_stock` is a **parameter**, not a variable. It holds the carbon stock
from the **previous** timestep's solution, frozen at the start of the current solve. Only
`vm_carbon_stock` (right-hand side, current-period variable) is free to change during
optimization.

This means within any single timestep solve:

- `pcm_carbon_stock` is a fixed constant — the optimizer cannot move it.
- The "CO2 emission cost" therefore depends on `vm_carbon_stock(current) - constant`,
  which is purely a function of current land decisions.
- There is no circularity: the model can linearize "what does changing land allocation
  cost in carbon terms?" without needing to know the answer in advance.

---

## The `pcm_*` update that makes it recursive across timesteps

After the solver returns, Module 56's `postsolve.gms` runs:

```gams
pcm_carbon_stock(j,land,c_pools) = vm_carbon_stock.l(j,land,c_pools);
```

(documented in cross_module/circular_dependency_resolution.md Appendix A; `.l` is the
GAMS notation for the optimal level value returned by the solver)

This copies the current-period optimal carbon stock into `pcm_carbon_stock`, which
becomes the frozen baseline for the *next* timestep. The feedback that "today's
afforestation increases tomorrow's carbon stock and therefore reduces tomorrow's CO2
emission charge" is real and economically meaningful — but it operates *across*
timesteps, not within one.

---

## Execution-phase summary

| Phase | What happens |
|---|---|
| **Preloop** | `im_pollutant_prices` (exogenous carbon price trajectory) loaded once |
| **Presolve (timestep t)** | `pcm_carbon_stock` still holds the postsolve value from t-1; frozen |
| **Solve (timestep t)** | Solver optimizes `vm_land`, `vm_carbon_stock`, `v56_emission_cost`, `vm_cost_glo` simultaneously; `pcm_carbon_stock` enters as a fixed RHS constant in `q56_emis_pricing_co2` |
| **Postsolve (timestep t)** | `pcm_carbon_stock ← vm_carbon_stock.l` — lag updated for t+1 |

This is the Type 1 (Temporal Feedback) resolution mechanism described in
`cross_module/circular_dependency_resolution.md` Section 2.1. Convergence is guaranteed:
there is no iteration within the timestep, only a single solver call.

---

## Key variables and equations

| Name | Type | Role |
|---|---|---|
| `vm_land(j,land)` | variable | Current land allocation (Module 10) |
| `vm_carbon_stock(j,land,c_pools,type)` | variable | Current carbon stocks (Module 52, consumed by 56) |
| `pcm_carbon_stock(j,land,c_pools,type)` | parameter | **Lagged** carbon stock — the loop-breaker |
| `v56_emis_pricing(i,emis_oneoff,"co2_c")` | variable | CO2 priced for the current period (Module 56) |
| `v56_emission_cost(i,emis_oneoff)` | variable | Monetary cost of one-off CO2 (Module 56) |
| `vm_cost_glo` | variable | Global total cost (Module 11 objective) |
| `q56_emis_pricing_co2` | equation | Computes CO2 flow as (pcm - vm_carbon_stock) / timestep; Module 56 `equations.gms:19-22` |
| `q10_land_area(j2)` | equation | Land conservation: sum(vm_land) = sum(pcm_land); Module 10 `equations.gms:13-15` |

Note that `q10_land_area` uses its own lagged variable `pcm_land` for the same structural
reason: to fix total land area without depending on a within-timestep circular reference.

---

## Sources

- `cross_module/circular_dependency_resolution.md` Sections 2.1, 3.4, Appendix A, B
- `modules/module_56.md` Sections 2.2, 2.4
- `modules/module_10.md` Section 2, Equations 1 and 3

---

## Epistemic status

All variable names, equation names, GAMS code fragments, and phase descriptions are
sourced from AI documentation verified against the GAMS codebase at the time of the last
doc sync.

- `q56_emis_pricing_co2` GAMS snippet: 🟡 Documented (module_56.md Section 2.2,
  citing `equations.gms:19-22`)
- `q10_land_area` GAMS snippet: 🟡 Documented (module_10.md Section 2, citing
  `equations.gms:13-15`)
- `pcm_carbon_stock` postsolve update: 🟡 Documented
  (circular_dependency_resolution.md Appendix A, citing
  `modules/56_ghg_policy/price_aug22/postsolve.gms:8`)
- Execution phase structure (preloop / presolve / solve / postsolve): 🟡 Documented
  (circular_dependency_resolution.md Appendix B)
- No claims about other IAMs or out-of-codebase behavior.
