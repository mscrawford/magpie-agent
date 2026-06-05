# P6: Trade Module (21) — Dependency Relationships with M17 and M15/M16

**Question**: Using Module_Dependencies documentation, describe the dependency relationships among trade (M21), production (M17), and food/material demand (M15/M16): which interface variables does trade CONSUME and PRODUCE, which modules sit on each side of those edges, and is the doc's stated dependency set accurate and complete?

---

## 1. What Trade CONSUMES (upstream interface variables)

Module 21 (`selfsuff_reduced` default) consumes exactly **two** interface variables from upstream modules:

| Variable | Declared by | Module | Doc source |
|---|---|---|---|
| `vm_prod_reg(i,k)` | M17 (Production) | `modules/17_production/flexreg_apr16/declarations.gms:10` | `module_21.md §Interface Variables / Used by Module 21` |
| `vm_supply(i,k)` | M16 (Demand) | `modules/16_demand/sector_may15/declarations.gms:10-14` | `module_21.md §Interface Variables / Used by Module 21` |

Both variables appear in every core trade balance equation. For `vm_prod_reg`:
- `q21_trade_glo`: `sum(i2, vm_prod_reg(i2,k_trade)) =g= sum(i2, vm_supply(i2,k_trade)) + balanceflow` (`modules/21_trade/selfsuff_reduced/equations.gms:12-14`)
- `q21_notrade`, `q21_trade_reg`, `q21_trade_reg_up`, `q21_cost_trade_tariff`, `q21_cost_trade_margin`: all reference `vm_prod_reg` or net exports `(vm_prod_reg - vm_supply)`

For `vm_supply`:
- Same equations reference it as the demand-side counterpart

**Module 15 does NOT supply a variable that M21 reads directly.** M15's output is `vm_dem_food`, which feeds into M16's `q16_supply_crops` equation (`modules/16_demand/sector_may15/equations.gms:19-29`). M16 then aggregates all demand sectors into `vm_supply`. M21 consumes `vm_supply` only — the M15 signal is already embedded in it. (`module_15.md §1 Purpose & Overview`: "Provides to: Modules 16, 20, 62 — vm_dem_food"; `module_17.md §4.1 note`: "Module 15 does NOT read vm_prod_reg directly.")

---

## 2. What Trade PRODUCES (downstream interface variables)

Module 21 produces **three** interface variables, all consumed exclusively by M11 (Costs):

| Variable | Dimensions | Consumer | Equation that defines it | Doc source |
|---|---|---|---|---|
| `vm_cost_trade_tariff(i)` | region | M11 | `q21_cost_trade_tariff` (`equations.gms:62-65`) | `module_21.md §Interface Variables / Provided by Module 21` |
| `vm_cost_trade_margin(i)` | region | M11 | `q21_cost_trade_margin` (`equations.gms:69-72`) | ibid |
| `vm_cost_trade_feasibility(i)` | region | M11 | `q21_cost_trade_feasibility` (`equations.gms:76-78`) | ibid |

All three are summed individually into the M11 objective via `q11_cost_reg` (`modules/11_costs/default/equations.gms:30-32`). These three variables replaced the former single `vm_cost_trade` variable after PR #866 ("Major Update to Bilateral trade implementation").

**Units**: Mio. USD17MER/yr each. **Scaling**: all three set to `1e5` in `modules/21_trade/selfsuff_reduced/scaling.gms:8-10`.

---

## 3. Module positions on each side of the dependency edges

```
M15 (Food Demand) ──→ vm_dem_food ──→ M16 (Demand)
                                          │
                          (+ feed from M70, + material from M62, etc.)
                                          │ computes vm_supply
                                          ↓
M17 (Production) ──→ vm_prod_reg ──→ M21 (Trade) ──→ vm_cost_trade_tariff ──→ M11
                                              │       vm_cost_trade_margin   ──→ M11
                                              │       vm_cost_trade_feasibility → M11
                                              │
                     (trade balance constrains production/demand simultaneously)
```

The 16–21–17 triangle is a **simultaneous-equation feedback** (Cycle C5 in `cross_module/circular_dependency_resolution.md §3.1`): `vm_supply` (M16) and `vm_prod_reg` (M17) are co-optimized with `v21_excess_dem`, `v21_excess_prod` in a single GAMS SOLVE.

---

## 4. Accuracy and completeness assessment of Module_Dependencies.md

### What the doc gets right

`Module_Dependencies.md §6.2` lists M21 as having **10 inputs** ("Most Dependent Modules" table). The two principal upstream interface variables (`vm_prod_reg` from M17, `vm_supply` from M16) are correct and the dependency edges are correctly attributed. `§3.1` correctly places M21 in Layer 3 conceptually alongside production modules.

The doc (`§4.1`) describes the Production–Yield–Livestock triangle correctly, and the Cycle 4 forest–carbon feedback chain. M21's Cycle C5 (demand–trade–production) is mentioned in `§4.2 Dependency Chains` only as the "Demand-to-Land Chain" (not the correct name), and the resolution type (simultaneous equations) is not stated.

### Where the doc is incomplete or imprecise

1. **Stale produced-variable list.** `§6.2` does not explicitly list M21's output interface variables by name. The "provides to 8 modules" claim in `module_21.md §Dependency Chains` is stated without naming those 8 modules beyond M11. The Module_Dependencies doc itself never names `vm_cost_trade_tariff`, `vm_cost_trade_margin`, or `vm_cost_trade_feasibility` — it predates PR #866 or does not reflect the split. The doc does not flag that the former `vm_cost_trade` no longer exists.

2. **M15 is absent from the dependency edge.** The dependency set in `§6.2` says M21 "depends on" M16 and M17 (correct) but does not clarify that M15 is a transitive upstream to M21 via M16 — not a direct interface. This is actually correct behaviour to omit it from direct edges, but the doc does not explain why M15 is not listed, which could confuse readers.

3. **"Provides to 8 modules" claim in `module_21.md` is unsupported.** The interface variable table in `module_21.md §Provided by Module 21` lists only M11 as a consumer of M21's interface variables. The claim that M21 also provides to M16, M17, M73, and 4 others (in `§Dependency Chains`) is listed as "supply signals" and "trade flows inform production decisions" — these are not GAMS interface variable flows but conceptual/implicit couplings. The Module_Dependencies doc does not flag this distinction.

4. **Centrality rank discrepancy.** `Module_Dependencies.md §1.2` does not include M21 in the top-10 hub table, yet `§6.2` states M21 has "10 inputs." `module_21.md §Dependency Chains` gives a centrality rank of 6, which is inconsistent with the hub table in `§1.2` that ends at rank 10 without M21. The hub table appears to score only modules that *produce* many outputs; M21's high input count does not appear in it.

### Summary verdict

The doc's stated dependency set is **accurate on the critical direct edges** — M21 consumes `vm_prod_reg` (M17) and `vm_supply` (M16), and produces cost variables to M11 — but **incomplete in three respects**: (a) the post-PR#866 three-variable split is absent; (b) the claim of 8 downstream recipients of M21 output conflates interface variables with conceptual influence; (c) the M15–M16–M21 transitive chain is not explained. For practical dependency analysis these omissions matter: a developer tracing M21's output consumers would find only M11 in the actual GAMS interface, not 8 modules.

---

## Sources

- 🟡 `core_docs/Module_Dependencies.md` §1.2, §3.1, §4.1, §6.2
- 🟡 `modules/module_21.md` §Interface Variables, §Equations, §Key Dependencies, §Dependency Chains — fully verified status noted therein
- 🟡 `modules/module_17.md` §4.1, §6.2, §12.1, §16.2
- 🟡 `modules/module_16.md` §Core Functionality, §Equations §1 (q16_supply_crops)
- 🟡 `modules/module_15.md` §1 Purpose & Overview

All claims from module docs only (no raw GAMS code read this session per task constraints).
