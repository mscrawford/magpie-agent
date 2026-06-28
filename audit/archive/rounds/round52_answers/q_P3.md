## Nitrogen Release from Cropland Change: Module 59 → Module 50 → Module 51

**Realization covered**: `cellpool_jan23` (default; `cfg$gms$som <- "cellpool_jan23"` in `config/default.cfg`). The only alternative, `static_jan19`, does not compute dynamic N release.

---

### 1. The Core Equation: `q59_nr_som`

🟡 **module_59.md, §3.5; `equations.gms:69-75`**:

```gams
q59_nr_som(j2) ..
  vm_nr_som(j2) =e=
    sum(ct,i59_lossrate(ct))/m_timestep_length * 1/15
    * (sum((ct,land_from), p59_carbon_density(ct,j2,land_from)
               * vm_lu_transitions(j2,land_from,"crop"))
       - v59_som_target(j2,"crop"));
```

**What this computes:**

`vm_nr_som(j)` [Mt N yr⁻¹] = annual nitrogen release from SOM loss in cell j.

The carbon driver is the **gap** between (a) the legacy SOM carbon carried into the cropland land-use class via the transition matrix, and (b) the IPCC-based equilibrium target for that cell's cropland:

```
Carbon gap = sum_{land_from} [ p59_carbon_density(land_from) x vm_lu_transitions(land_from -> crop) ]
             - v59_som_target("crop")
```

- When cropland **expands** into forest or natural vegetation, `land_from` has high carbon density (e.g., forest SOM); the equilibrium target for cropland is lower; the gap is positive → N is released.
- When cropland **contracts** (abandonment), transitions into crop are small; the gap can go negative (SOM is rebuilding) → `vm_nr_som` is negative (N is immobilized).
- The variable is declared as a **free variable** (`declarations.gms:45`), so both signs are valid.

---

### 2. C:N Ratio and Convergence Coefficient

**C:N ratio**: Fixed at **15:1** for all soils and climates (`equations.gms:76`). The `1/15` term in the equation directly encodes this. It is a global constant; there is no spatial or crop-type variation.

**Convergence rate (lossrate)**:

```gams
i59_lossrate(t) = 1 - 0.85^m_yeardiff(t)          ! preloop.gms:45
```

For the default 5-year timestep: `1 - 0.85^5 ≈ 0.5563` (55.6% of the C:N gap closes in 5 years).

| Timestep | `i59_lossrate` |
|---|---|
| 1 yr | 0.15 |
| 5 yr (default) | ≈ 0.556 |
| 10 yr | 0.80 |
| 20 yr | 0.96 |

**Timestep divisor**: The factor `/m_timestep_length` (default = 5) converts from a per-period carbon change to an **annual** nitrogen flux. So the full expression, collecting terms for a standard 5-year run:

```
vm_nr_som [Mt N yr⁻¹]
  = (0.5563 / 5)  x  (legacy_C - target_C) [mio. tC]  x  (1/15)
  = 0.00741  x  (legacy_C - target_C)
```

(Units: mio. tC x (Mt N / mio. tC) = Mt N. ✓)

---

### 3. Two-Variable Split: `vm_nr_som` vs. `vm_nr_som_fertilizer`

Module 59 computes **two distinct interface variables** from the same SOM loss signal:

#### `vm_nr_som(j)` — total N release

Used by Module 51 for emissions. This is the full mineralization signal before any cap.

#### `vm_nr_som_fertilizer(j)` — plant-available N fraction

Subject to two simultaneous upper-bound constraints (`equations.gms:81-91`):

```gams
q59_nr_som_fertilizer(j2) ..
    vm_nr_som_fertilizer(j2) =l= vm_nr_som(j2);

q59_nr_som_fertilizer2(j2) ..
    vm_nr_som_fertilizer(j2) =l=
        vm_landexpansion(j2,"crop") * s59_nitrogen_uptake;
```

`s59_nitrogen_uptake` = **0.0002 Mt N/Mha = 200 kg N ha⁻¹** (`input.gms:9`). Only newly expanded cropland receives this nitrogen credit; existing cropland is assumed to already be at equilibrium. The effective plant-available N is therefore `min(vm_nr_som, area_expansion × 200 kg/ha)`.

---

### 4. Connection to Module 50 (Soil Nitrogen Budget)

**Realization**: `macceff_aug22` (confirmed in `config/default.cfg`).

🟡 **module_50.md, §3.1; `equations.gms:22-32`** — `q50_nr_inputs`:

```gams
q50_nr_inputs(i2) ..
    v50_nr_inputs(i2) =e=
      vm_res_recycling(i2,"nr")
    + ...
    + vm_nr_inorg_fert_reg(i2,"crop")
    + sum(cell(i2,j2), vm_nr_som_fertilizer(j2))   ! ← M59 contribution
    + sum(ct, f50_nitrogen_balanceflow(ct,i2))
    + v50_nr_deposition(i2,"crop");
```

`vm_nr_som_fertilizer` enters **alongside** residues, manure, biological fixation, synthetic fertilizer, and atmospheric deposition as one of the eight cropland N input sources. It is cell-to-region aggregated via the `cell(i2,j2)` mapping.

The balance constraint (`equations.gms:14-16`) is:

```
q50_nr_bal_crp:  vm_nr_eff(i) × v50_nr_inputs(i) ≥ sum_kcr v50_nr_withdrawals(i,kcr)
```

Because `vm_nr_som_fertilizer` is an input on the left-hand side, a larger SOM-derived N flux reduces the **endogenous fertilizer demand** `vm_nr_inorg_fert_reg` that the optimizer must supply to close the balance — at given SNUpE (vm_nr_eff is FIXED in presolve at the scenario-plus-MACC value; it is not itself optimized).

---

### 5. Connection to Module 51 (N2O and Other N Emissions)

**Realization**: `rescaled_jan21` (confirmed in `config/default.cfg`).

🟡 **module_51.md, Equation 5; `equations.gms:55-59`** — `q51_emissions_som`:

```gams
vm_emissions_reg(i2,"som",n_pollutants_direct)
=e=
sum(cell(i2,j2), vm_nr_som(j2))
* sum(ct, i51_ef_n_soil(ct,i2,n_pollutants_direct,"som"))
/ (1 - s51_snupe_base) * (1 - vm_nr_eff(i2))
```

Key features:

- **Input is `vm_nr_som`, not `vm_nr_som_fertilizer`** — the full mineralised N, aggregated from cell level (j) to regional level (i) via the `cell(i2,j2)` map.
- **NUE rescaling** is applied, identical in form to the manure and fertiliser equations: the factor `(1 - vm_nr_eff(i)) / (1 - s51_snupe_base)` adjusts relative to the IPCC baseline assumption of 50% NUE (`s51_snupe_base = 0.5`, `input.gms:8`).
  - If actual NUE = 60%: scaling = (1-0.6)/(1-0.5) = 0.40/0.50 = **0.8** → 20% fewer emissions than IPCC baseline.
  - If actual NUE = 40%: scaling = 0.60/0.50 = **1.2** → 20% more emissions.
- **`i51_ef_n_soil(ct,i,"n2o_n_direct","som")`** is the regional emission factor for SOM N2O. In the future period (post-2010), it is held constant at its 2010 value (`presolve.gms:14-15`); in the historical period it uses time-varying input data (`presolve.gms:11-12`).
- The equation computes four direct pollutants: `n2o_n_direct`, `nh3_n`, `no2_n`, `no3_n` (all via the same equation structure, looping over `n_pollutants_direct`).

**Indirect N2O** then follows from `q51_emissions_indirect_n2o` (`equations.gms:83-89`): the NH3+NOx emissions from the "som" source are multiplied by IPCC EF4 (1%), and the NO3 emissions by IPCC EF5 (0.75%), to produce secondary N2O from volatilization-redeposition and leaching pathways respectively.

---

### 6. End-to-End Chain Summary

```
Cropland expansion (vm_lu_transitions[land_from -> crop])
    ↓
q59_nr_som  [cellpool_jan23, equations.gms:69-75]
    Carbon gap × lossrate / timestep_length × (1/15)
    C:N = 15:1  |  lossrate ≈ 0.556 (5-yr step)
    ↓
vm_nr_som(j)          ————————→  Module 51: q51_emissions_som
[Mt N yr⁻¹, cell]                  × i51_ef_n_soil(…,"som")
                                    × NUE rescaling factor (1-vm_nr_eff)/(1-0.5)
                                    → vm_emissions_reg(i,"som", {n2o,nh3,no2,no3})
                                    → indirect N2O via EF4/EF5

+ two upper-bound constraints
    ↓
vm_nr_som_fertilizer(j)  ≤ vm_nr_som
                         ≤ vm_landexpansion(j,"crop") × 200 kg N/ha
    ↓ (cell→region aggregation)
Module 50: q50_nr_inputs [macceff_aug22, equations.gms:30]
    one of 8 cropland N inputs
    → reduces vm_nr_inorg_fert_reg demand in q50_nr_bal_crp
```

---

### Key Quantitative Facts

| Parameter | Value | Source |
|---|---|---|
| C:N ratio | **15:1** (fixed, global) | `equations.gms:76` |
| Annual convergence base | 0.85 per year | `preloop.gms:45` |
| `i59_lossrate` (5-yr step) | ≈ 0.556 | derived from 1 - 0.85^5 |
| Annualisation divisor | `m_timestep_length` (=5 for default) | `equations.gms:70` |
| Max plant-available N cap | 200 kg N ha⁻¹ on new cropland | `input.gms:9` |
| IPCC base NUE (Module 51) | 0.50 | `input.gms:8` |
| Emission factor source | `i51_ef_n_soil(ct,i,"n2o_n_direct","som")` — regional, frozen at 2010 post-calibration | `presolve.gms:14-15` |

---

### Limitations to flag

- C:N = 15 is global and fixed; actual soils range from ~10:1 (tropical mineral soils) to ~25:1 (peat); spatial or crop-specific variation is not implemented (`module_59.md §13`).
- Only **cropland** SOM is tracked dynamically; pasture and forest are assumed to hold natural carbon density, so SOM N release from pasture intensification is not modelled (`realization.gms:21-24`).
- `vm_nr_som_fertilizer` is capped by crop uptake capacity (`s59_nitrogen_uptake`); the remainder of `vm_nr_som` (the emissions-relevant portion) is not credited to crops but does drive Module 51's emission source "som".
- Post-2010, `i51_ef_n_soil` emission factors for the "som" source are frozen — no dynamic climate response to changing leaching or denitrification rates (`module_51.md Limitation 1`).

---

**Source statement**: 🟡 All claims based on `modules/module_59.md` (verified 2026-03-06), `modules/module_50.md` (verified 2025-10-13), and `modules/module_51.md` (verified 2025-10-13), all of which were cross-referenced against the `cellpool_jan23`, `macceff_aug22`, and `rescaled_jan21` GAMS source respectively. Line numbers cited from module docs; code changes since those verification dates may shift them.
