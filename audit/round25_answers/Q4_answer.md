# R25-Q4: Module 38 `per_ton_fao_may22` — Interface Variables and Consumers

## Realization Context

**The question asks about `per_ton_fao_may22`, which is NOT the default realization.**
The default realization for Module 38 is `sticky_feb18` (confirmed: `cfg$gms$factor_costs <- "sticky_feb18"`
in `config/default.cfg`). `per_ton_fao_may22` is an alternative, simplified realization. 🟡
(module_38.md §0 header box)

---

## Interface Variables Declared by Module 38 (`per_ton_fao_may22`)

Module 38's `per_ton_fao_may22` realization exposes **exactly one** `vm_cost_*` interface variable:

### `vm_cost_prod_crop(i, factors)`

- **Unit**: mio USD17MER/yr
- **Dimensions**: `i` (regions) × `factors` where `factors = {labor, capital}`
- **Declaration file**: `modules/38_factor_costs/per_ton_fao_may22/declarations.gms`
  (the docs note this is the same interface variable exposed by all three Module 38 realizations)

**What the realization computes** (two equations, `q38_cost_prod_crop_labor` and `q38_cost_prod_crop_capital`):
🟡 (module_38.md §4)

```
vm_cost_prod_crop(i,"labor")   = sum_kcr( vm_prod_reg(i,kcr) * fac_req(i,kcr) * labor_share(i)   * wage_scaling * (1/productivity_gain) )
vm_cost_prod_crop(i,"capital") = sum_kcr( vm_prod_reg(i,kcr) * fac_req(i,kcr) * capital_share(i) )
```

No capital stocks, no annuitization, no immobility — purely volume-based per-ton costs. 🟡
(module_38.md §4, explicitly labeled "Conceptually")

**Note on documentation depth**: The module_38.md docs provide the conceptual form for
`per_ton_fao_may22` and explicitly direct the reader to the raw GAMS source for exact syntax
(`modules/38_factor_costs/per_ton_fao_may22/equations.gms`). The declarations file citation
is inferred from the cross-realization interface statement in §5; the notes do not provide
an explicit line number for the `per_ton_fao_may22` declarations file. 🟡 / 🔴 (partial)

---

## Consuming Module and Equation

### Consumer: Module 11 (Costs), equation `q11_cost_reg`

**File:line**: `modules/11_costs/default/equations.gms:15-47` (for the consumer equation) 🟡
(module_11.md §2.2)

**Exact consumer line** (from module_11.md §2.2):

```gams
q11_cost_reg(i2) .. v11_cost_reg(i2) =e= sum(factors,vm_cost_prod_crop(i2,factors))
                   + sum(kres,vm_cost_prod_kres(i2,kres))
                   + vm_cost_prod_past(i2)
                   ...
```

`vm_cost_prod_crop` appears as the **first term** in the regional cost aggregation, summed over
the `factors` set: `sum(factors, vm_cost_prod_crop(i2,factors))`.

`v11_cost_reg` feeds directly into the global objective via `q11_cost_glo`:

```gams
q11_cost_glo .. vm_cost_glo =e= sum(i2, v11_cost_reg(i2));
```

**File:line**: `modules/11_costs/default/equations.gms:10` 🟡 (module_11.md §2.1)

**There is no other consuming module.** Module 38's `vm_cost_prod_crop` is not consumed anywhere
except Module 11's `q11_cost_reg`. The docs describe Module 11 as the single convergence point
for all cost variables, with Module 38 among the 27 upstream providers. 🟡 (module_11.md §1.2)

---

## Cross-Realization Note

All three Module 38 realizations (`sticky_feb18`, `sticky_labor`, `per_ton_fao_may22`) expose the
same single interface variable `vm_cost_prod_crop(i,factors)` to the same single consumer
(Module 11 `q11_cost_reg`). The realizations differ in HOW they compute the variable, not in
WHAT they expose or WHO consumes it. 🟡 (module_38.md §5 "Cross-Realization Interface")

---

## Confidence Notes and Limitations

1. **Consumer identification** (HIGH confidence): module_38.md §5 and §6 both explicitly name Module 11 `q11_cost_reg` as the sole consumer; module_11.md §2.2 quotes the exact equation line. 🟢 (documented from both producer and consumer sides)

2. **Single interface variable** (HIGH confidence): module_38.md explicitly states `vm_cost_prod_crop(i,factors)` is the output variable for all realizations, and the docs describe `per_ton_fao_may22` as the simplest realization with the fewest equations (2 equations). 🟡

3. **`per_ton_fao_may22` declarations line number** (LOW confidence): The docs do not provide an explicit `declarations.gms:NN` line citation for this non-default realization. The pattern `modules/38_factor_costs/per_ton_fao_may22/declarations.gms` is inferred from the standard MAgPIE module file layout. A code read is required to confirm the exact line. 🔴

4. **No second `vm_cost_*` variable**: The docs describe `per_ton_fao_may22` as having only 2 equations and no capital stocks. The docs list no other `vm_` interface variable for this realization beyond `vm_cost_prod_crop`. I am not aware of a second `vm_cost_*` variable from `per_ton_fao_may22`, but cannot rule it out without reading `declarations.gms` directly. 🔴 (absence-of-evidence caveat)

---

Based on module_38.md documentation (§4, §5, §6) and module_11.md documentation (§2.2).
