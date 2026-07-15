# Q3 Answer: Cropland Soil-Nitrogen Budget in Module 50 (Default Realization)

**Source confidence**: All claims tagged 🟡 (from AI docs read this session; no raw .gms files read per task constraint).

---

## Default Realization

Module 50's default realization is **`macceff_aug22`**, confirmed by `config/default.cfg` (line: `cfg$gms$nr_soil_budget <- "macceff_aug22"  # def = macceff_aug22`). The AI documentation covers this realization exclusively.

---

## (a) The Balance Equation, Inputs, and Outputs

### The Core Balance Constraint

The cropland nitrogen balance is enforced by **`q50_nr_bal_crp`**:

```gams
q50_nr_bal_crp(i2) ..
    vm_nr_eff(i2) * v50_nr_inputs(i2)
    =g= sum(kcr, v50_nr_withdrawals(i2,kcr));
```

🟡 Source: `module_50.md` (citing `macceff_aug22/equations.gms:14-16`)

Mathematical form:
```
SNUpE(i) × N_inputs(i) ≥ N_withdrawals(i)
```

where `vm_nr_eff(i)` is the Soil Nitrogen Uptake Efficiency (SNUpE), a dimensionless fraction FIXED in presolve (not optimized). The inequality, not equality, is the balance constraint. The model optimizes `vm_nr_inorg_fert_reg` (inorganic fertilizer) upward until the constraint is satisfied.

---

### The Input Aggregation Equation

All inputs enter via **`q50_nr_inputs`**:

```gams
q50_nr_inputs(i2) ..
    v50_nr_inputs(i2) =e=
    vm_res_recycling(i2,"nr")
      + sum((cell(i2,j2),kcr,w), vm_area(j2,kcr,w) * f50_nr_fix_area(kcr))
      + sum(cell(i2,j2), vm_fallow(j2) * f50_nr_fix_area("tece"))
      + vm_manure_recycling(i2,"nr")
      + sum(kli, vm_manure(i2, kli, "stubble_grazing","nr"))
      + vm_nr_inorg_fert_reg(i2,"crop")
      + sum(cell(i2,j2), vm_nr_som_fertilizer(j2))
      + sum(ct, f50_nitrogen_balanceflow(ct,i2))
      + v50_nr_deposition(i2,"crop");
```

🟡 Source: `module_50.md` (citing `macceff_aug22/equations.gms:22-32`)

**Eight input components, mapped to the question's categories:**

| Budget term | Variable(s) in q50_nr_inputs | Notes |
|---|---|---|
| Biological N fixation | `sum((cell,kcr,w), vm_area * f50_nr_fix_area(kcr))` + fallow term | Area-based, exogenous rate per crop; legumes have non-zero rates |
| Atmospheric deposition | `v50_nr_deposition(i2,"crop")` | Computed by `q50_nr_deposition` as area × exogenous rate from `f50_atmospheric_deposition_rates`; separate equation `equations.gms:88-90` |
| Inorganic fertilizer | `vm_nr_inorg_fert_reg(i2,"crop")` | The only free optimization variable in the budget; solver sets it to satisfy the balance |
| Residue recycling | `vm_res_recycling(i2,"nr")` | From Module 18 (see part b) |
| Manure (managed + stubble) | `vm_manure_recycling(i2,"nr")` + `sum(kli, vm_manure(i2,kli,"stubble_grazing","nr"))` | From Module 55 (AWMS); the first is collected/applied manure, the second is manure deposited in-field by grazing animals on crop stubble |
| SOM-derived N | `sum(cell(i2,j2), vm_nr_som_fertilizer(j2))` | From Module 59 (see part b) |
| Balance flow correction | `sum(ct, f50_nitrogen_balanceflow(ct,i2))` | Exogenous correction for regions with structurally unrealistic SNUpE values; from input data |

Note: the question names "fixation" and "deposition" as separate inputs — both are present. Manure appears in two terms (managed recycling and stubble grazing). There is no separate "organic input from SOM" term beyond `vm_nr_som_fertilizer` (which is the plant-available fraction of SOM-released N, not a full SOM budget variable).

---

### The Withdrawal Equation

Withdrawals are computed per crop by **`q50_nr_withdrawals`**:

```gams
q50_nr_withdrawals(i2,kcr) ..
    v50_nr_withdrawals(i2,kcr) =e=
    (1 - sum(ct, f50_nr_fix_ndfa(ct,i2,kcr))) *
    (vm_prod_reg(i2,kcr) * fm_attributes("nr",kcr)
       + vm_res_biomass_ag(i2,kcr,"nr")
       + vm_res_biomass_bg(i2,kcr,"nr"))
    - vm_dem_seed(i2,kcr) * fm_attributes("nr",kcr);
```

🟡 Source: `module_50.md` (citing `macceff_aug22/equations.gms:36-43`)

Mathematical form:
```
N_withdrawal(i,kcr) = (1 - NDFA(i,kcr)) × [N_harvest + N_resid_ag + N_resid_bg]
                      - N_seed
```

- **NDFA** (`f50_nr_fix_ndfa`): Nitrogen Derived From Atmosphere — the share of crop-biomass N that came from biological fixation, not the soil. For legumes this can be 0.5–0.8. Multiplying by `(1 - NDFA)` gives only the fraction the soil must supply.
- **N_harvest**: `vm_prod_reg(i,kcr) * fm_attributes("nr",kcr)` — harvested product N content.
- **N_resid_ag + N_resid_bg**: aboveground and belowground residue N content (`vm_res_biomass_ag`, `vm_res_biomass_bg` from Module 18).
- **N_seed**: seed N returned to the field at planting, subtracted because seeds are an N inflow.

---

## (b) How Organic Inputs Enter: Residues (M18) and SOM (M59)

### Residues — Module 18 → `vm_res_recycling(i,"nr")`

Module 18 (`flexreg_apr16` default) computes residue N recycled to soil via **`q18_res_recycling_nr`**:

```gams
q18_res_recycling_nr(i2) ..
    vm_res_recycling(i2,"nr")
    =e=
    sum(kcr, v18_res_ag_recycling(i2,kcr,"nr")
            + vm_res_ag_burn(i2,kcr,"nr") * (1 - f18_res_combust_eff(kcr))
            + vm_res_biomass_bg(i2,kcr,"nr"));
```

🟡 Source: `module_18.md` (citing `flexreg_apr16/equations.gms:90-96`)

Three pathways add up to `vm_res_recycling`:
1. **AG recycling** (`v18_res_ag_recycling`): Aboveground residues left on the field to decay — their full N content returns to soil.
2. **Burning ash N** (`vm_res_ag_burn * (1 - f18_res_combust_eff)`): The fraction of N in burned residues that is NOT volatilized (i.e., remains in ash). `f18_res_combust_eff` is the per-crop N volatilization fraction during burning.
3. **Belowground residues** (`vm_res_biomass_bg`): All root N stays in soil because roots are never physically removed.

This aggregated variable `vm_res_recycling(i,"nr")` is then read directly as the first term of `q50_nr_inputs` (`macceff_aug22/equations.gms:24`). The residue amounts themselves are functions of Module 17 production (`vm_prod_reg`) and Module 30 croparea (`vm_area`), flowing through Module 18's crop growth functions.

Note on the withdrawal side: Module 50 also reads `vm_res_biomass_ag(i,kcr,"nr")` and `vm_res_biomass_bg(i,kcr,"nr")` directly in `q50_nr_withdrawals` to calculate total plant N demand (these represent the N that goes into residue biomass, which must be supplied from soil). This is a separate reading from the recycling aggregation in Module 18 — Module 50 reads both the total residue N (for withdrawals) and the recycled fraction (for inputs).

---

### SOM — Module 59 → `vm_nr_som_fertilizer(j)`

Module 59 (`cellpool_jan23` default) computes N release from SOM loss via **`q59_nr_som`**:

```gams
q59_nr_som(j2) ..
  vm_nr_som(j2) =e=
    sum(ct, i59_lossrate(ct)) / m_timestep_length * 1/15
    * (sum((ct,land_from), p59_carbon_density(ct,j2,land_from)
           * vm_lu_transitions(j2,land_from,"crop"))
       - v59_som_target(j2,"crop"));
```

🟡 Source: `module_59.md` (citing `cellpool_jan23/equations.gms:69-75`)

This calculates annual N release using a C:N ratio of 15:1 and the 15%-per-year convergence to equilibrium. Positive when cropland expands (transitions bring more C than the new equilibrium requires), negative when cropland contracts.

**The plant-available fraction** is `vm_nr_som_fertilizer(j)`, constrained by two inequalities in Module 59:

1. `q59_nr_som_fertilizer`: `vm_nr_som_fertilizer(j) ≤ vm_nr_som(j)` — cannot exceed total N released.
2. `q59_nr_som_fertilizer2`: `vm_nr_som_fertilizer(j) ≤ vm_landexpansion(j,"crop") * s59_nitrogen_uptake` — limited to what crops on newly expanded land can actually absorb (default `s59_nitrogen_uptake = 200 kg N/ha`).

🟡 Source: `module_59.md` (citing `cellpool_jan23/equations.gms:81-91`)

**Entry into Module 50**: `vm_nr_som_fertilizer(j)` is summed across cells within a region:
```gams
sum(cell(i2,j2), vm_nr_som_fertilizer(j2))
```
and enters `q50_nr_inputs` at `macceff_aug22/equations.gms:30`. Only the plant-available fraction enters as a positive N input; the remainder of `vm_nr_som(j)` is tracked by Module 51 for emission calculations.

---

## (c) N Surplus: Computation and Downstream Fate

### Surplus Computation

The cropland N surplus is computed by **`q50_nr_surplus`**:

```gams
q50_nr_surplus(i2) ..
    v50_nr_surplus_cropland(i2)
    =e= v50_nr_inputs(i2)
    - sum(kcr, v50_nr_withdrawals(i2,kcr));
```

🟡 Source: `module_50.md` (citing `macceff_aug22/equations.gms:46-49`)

Mathematical form:
```
v50_nr_surplus_cropland(i) = v50_nr_inputs(i) - Σ_kcr v50_nr_withdrawals(i,kcr)
```

Because the balance constraint is `vm_nr_eff × v50_nr_inputs ≥ Σ withdrawals`, the surplus is the total inputs minus only the withdrawn fraction. Since SNUpE < 1, the system must apply *more* inputs than are withdrawn — the surplus is the fraction not taken up. For example, with SNUpE = 0.65 and withdrawals of 100 Tg N, inputs are driven to ≥ 154 Tg N, and the surplus is 54 Tg N.

`v50_nr_surplus_cropland` is a per-period flow variable (units: Tg N/yr). There is no soil mineral-N stock carried across periods; the surplus is a within-period residual.

---

### Downstream: What the Surplus Feeds

Module 50 does NOT compute emission pathways from the surplus. The surplus feeds **Module 51 (Nitrogen)** via the efficiency variables, not the surplus variable directly. The mechanism in Module 51 is:

```
N_loss = N_inorganic_fert / (1 - SNUpE_base) × (1 - SNUpE) × emission_factor
```

🟡 Source: `module_50.md` §6.2 (citing `modules/51_nitrogen/rescaled_jan21/equations.gms:26,34,46,59`)

The variables Module 50 provides to Module 51 are:
- `vm_nr_eff(i)` — cropland SNUpE, used in Module 51 to rescale emission fractions
- `vm_nr_eff_pasture(i)` — pasture NUE, same purpose
- `vm_nr_inorg_fert_reg(i,"crop")` — the endogenous fertilizer quantity, used as the base N flow for emission scaling

The surplus drives fertilizer costs via **`q50_nr_cost_fert`**:
```gams
q50_nr_cost_fert(i2) ..
    vm_nr_inorg_fert_costs(i2) =e=
    sum(land_ag, vm_nr_inorg_fert_reg(i2,land_ag)) * s50_fertilizer_costs;
```
🟡 Source: `module_50.md` (citing `macceff_aug22/equations.gms:94-97`; default `s50_fertilizer_costs = 738 USD17MER/tN`)

`vm_nr_inorg_fert_costs(i)` enters Module 11's objective function, creating a cost incentive that pushes the model to minimize fertilizer use (and hence minimize the surplus) while still satisfying the withdrawal constraint.

**Summary of downstream flows from the N surplus / efficiency:**

| Receiver | Variable consumed | Purpose |
|---|---|---|
| Module 51 (Nitrogen) | `vm_nr_eff`, `vm_nr_eff_pasture`, `vm_nr_inorg_fert_reg` | Compute N2O, NH3, NO3 emissions via NUE-rescaling |
| Module 11 (Costs) | `vm_nr_inorg_fert_costs` | Fertilizer cost enters objective function |

Module 51 disaggregates the surplus-linked losses into ammonia volatilization, N2O emissions, nitrate leaching, and other reactive nitrogen pathways — but that accounting happens entirely within Module 51, not Module 50.

---

## Closing Source Statement

**Primary source**: `<magpie-agent>/modules/module_50.md` — comprehensive, verified documentation of Module 50 `macceff_aug22` realization.

**Supporting sources**:
- `<magpie-agent>/modules/module_18.md` — Module 18 `flexreg_apr16` residue N recycling (equation `q18_res_recycling_nr`)
- `<magpie-agent>/modules/module_59.md` — Module 59 `cellpool_jan23` SOM N release equations
- `<magpie-agent>/cross_module/nitrogen_food_balance.md` — system-level nitrogen tracking overview
- `<magpie-root>/config/default.cfg` — confirmed `macceff_aug22` as active realization

**All claims are tagged 🟡** (read from AI documentation this session, not verified against raw `.gms` source per task constraint). Line numbers reflect the AI docs' last verification date (2025-10-13 per `module_50.md`); code changes since then may have shifted them.

**No docs-unavailable confabulation**: Where the docs were silent (e.g., what share of `vm_nr_som` is not plant-available), the answer states the constraint structure rather than inventing a number.
