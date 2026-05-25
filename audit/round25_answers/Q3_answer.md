# R25-Q3: Nitrogen-MACC Cost Flow into the Objective Function

## Question

Trace how nitrogen-MACC costs from Module 57 enter MAgPIE's objective function. Name:
- (a) the cost variable Module 57 produces
- (b) any intermediary variable in Module 51 (nitrogen emissions) it flows through
- (c) the term in `q11_cost_reg` (Module 11 default realization) that incorporates it

---

## Answer

### (a) Cost Variable Produced by Module 57

Module 57 (`on_aug22`, the only realization) calculates mitigation costs through two equations, producing a single cost variable split by factor type:

**`vm_maccs_costs(i, factors)`** — "Costs of technical GHG mitigation", dimensions region × {labor, capital}, units million USD17MER/yr. 🟡

- `q57_labor_costs(i)` sets `vm_maccs_costs(i2,"labor")` — MACC integral costs adjusted for regional wages and productivity (`module_57.md`, `equations.gms:35-43`)
- `q57_capital_costs(i)` sets `vm_maccs_costs(i2,"capital")` — same integral but with only the capital-share factor (`module_57.md`, `equations.gms:45-52`)

Both equations use the integral of the MACC curve (`p57_maccs_costs_integral`) multiplied by back-calculated baseline emissions, plus a fertilizer-cost correction to avoid double-counting endogenous fertilizer savings. The variable is declared in `declarations.gms:25`. 🟡

**Attribution**: `vm_maccs_costs` is **produced by Module 57** (`on_aug22`). Module 57's downstream dependency table lists "Module 11 (Costs): `vm_maccs_costs`" explicitly as the route to the objective function (`module_57.md`, Downstream Dependencies table).

---

### (b) Intermediary Variable in Module 51

**There is no intermediary variable in Module 51 that `vm_maccs_costs` flows through.** 🟡

The relationship between Modules 51 and 57 runs in the opposite direction for costs:

- Module 57 → Module 51 (MACC mitigation fractions): `im_maccs_mitigation(t,i,emis_source,pollutants)` flows **from Module 57 to Module 51**. This parameter (preprocessed in `preloop.gms:41-66`) reduces baseline AWMS N₂O emissions in Module 51's equation `q51_emissionbal_awms` (`module_51.md`, `equations.gms:65-71`). Specifically, the AWMS emission equation multiplies confined-manure emissions by `(1 - sum(ct, im_maccs_mitigation(ct,i2,"awms","n2o_n_direct")))`.

- Module 51 → Module 57 (cost direction): Module 57 reads `vm_emissions_reg(i,emis_source,"n2o_n_direct")` from Module 51 (and `"ch4"` from Module 53) to calculate the MACC cost integral. But `vm_emissions_reg` is not a cost variable; it is the emission quantity used as an input to Module 57's cost equations, not an intermediary in the cost chain.

The cost variable `vm_maccs_costs` exits Module 57 **directly** to Module 11. Module 51 is not in the cost chain at all — it is a cost *input* provider (via `vm_emissions_reg`), not a cost *conduit*.

**Summary**: There is no Module 51 intermediary variable in the nitrogen-MACC cost flow. The flow is: Module 57 computes `vm_maccs_costs` → Module 11 receives it directly. 🟡

---

### (c) Term in `q11_cost_reg` (Module 11, `default` realization)

Module 11's `default` realization is the only realization. The relevant term in `q11_cost_reg` is:

```gams
+ sum(factors, vm_maccs_costs(i2, factors))
```

This appears at **`equations.gms:28`** in Module 11's `default` realization, summing the labor and capital components of MACC costs across all factor types for each region. 🟡

The full equation `q11_cost_reg` is documented at `module_11.md`, Section 2.2 (`equations.gms:15-47`). In the cost-component taxonomy, this term is labeled:

> **Variable**: `vm_maccs_costs(i,factors)`
> **Source Module**: Module 57 (MACCS)
> **Description**: Costs for implementing emission abatement measures (beyond baseline)
> **Citation**: `equations.gms:28`, documented in `equations.gms:58`

The sum then feeds into `q11_cost_glo`:

```gams
q11_cost_glo .. vm_cost_glo =e= sum(i2, v11_cost_reg(i2));
```

where `v11_cost_reg` is the intermediate variable accumulating all 32 regional cost terms (`module_11.md`, `equations.gms:10`). `vm_cost_glo` is the variable MAgPIE minimizes. 🟡

---

## Complete Cost Chain Summary

```
Module 57 (on_aug22)
  Equations: q57_labor_costs, q57_capital_costs
  Output: vm_maccs_costs(i, factors)          [declarations.gms:25]
         ↓
  NO Module 51 intermediary
         ↓
Module 11 (default)
  q11_cost_reg: + sum(factors, vm_maccs_costs(i2, factors))   [equations.gms:28]
         ↓
  v11_cost_reg(i)                              [declarations.gms:10]
         ↓
  q11_cost_glo: vm_cost_glo =e= sum(i2, v11_cost_reg(i2))    [equations.gms:10]
         ↓
  vm_cost_glo  ← MINIMIZED BY SOLVER
```

**Key clarification on Module 51's role**: Module 51 participates in the MACC mechanism as a *provider* of `vm_emissions_reg` (the emission quantities Module 57 uses to compute mitigation costs) and as a *consumer* of `im_maccs_mitigation` (the fraction by which AWMS N₂O emissions are reduced). Module 51 is not a cost conduit. The note in `module_51.md`'s dependency section — "Provides to: Module 11 (costs): via emissions" — refers to the fact that Module 51 emissions feed into `vm_emission_costs` (produced by Module 56) and affect MACC costs indirectly through the emission quantities used in Module 57's equations. It does **not** mean `vm_emissions_reg` is itself a cost variable. 🟡

---

**Sources**:
- Based on `module_57.md` documentation (Equations section, Downstream Dependencies table)
- Based on `module_51.md` documentation (Equation 6 `q51_emissionbal_awms`, Upstream Dependencies table)
- Based on `module_11.md` documentation (Section 2.2 `q11_cost_reg`, Section 3.9 Abatement Costs)
- Realization confirmation: Module 57 `on_aug22` (only realization); Module 51 `rescaled_jan21` (default); Module 11 `default` (only realization)
