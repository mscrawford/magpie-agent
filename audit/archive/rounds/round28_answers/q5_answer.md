# Q5: Does MAgPIE track phosphorus by default? Module 54 default state, and cross-module connections when enabled.

---

## Module 54 — Default State: `off`

**MAgPIE does NOT track phosphorus by default.**

Module 54's only realization is `off`, confirmed in `config/default.cfg`:
```
cfg$gms$phosphorus  <- "off"                     # def = off
```

In the `off` realization:
- **0 equations** are active (module_54.md: "Equations: 0 (no active implementation)")
- **1 variable** exists: `vm_p_fert_costs(i)` — costs for mineral phosphorus fertilizers (mio. USD17MER/yr) — declared in `off/declarations.gms:10`
- That variable is **fixed to zero** in `off/preloop.gms:10`:
  ```gams
  vm_p_fert_costs.fx(i)=0;
  ```
- `off/realization.gms:8-9` explicitly states: "This is the current default implementation of the module. It deactivates calculations related to the phosphorus module."
- `off/realization.gms:11` notes: "The realization is still under development."
- `module.gms:27-28` identifies it as a topic for future development: "It is a topic we seek to include in future developments of the model as enriches the biophysical aspects of the model as well as adds to the fertilizer costs."

**What this means in practice:**
- No phosphorus flows are computed or tracked.
- P fertilizer costs are zero in the objective function; production costs are therefore underestimated by roughly 5–10% (P fertilizer is typically 10–20% of total fertilizer costs).
- No soil P dynamics, no P mining or buildup, no P losses to water bodies.
- No P use efficiency optimization.
- Crop production is implicitly assumed to be unconstrained by P availability.
- P recycling from manure (Module 55) and residues (Module 18) occurs in those modules' mass balances but is not quantified or tracked as phosphorus.

---

## Intended P Flows When/If Enabled (Not Currently Implemented)

`module.gms:12-24` documents eleven intended P flows that a future active realization would track:

**Withdrawals from soil:**
1. P withdrawals by harvest (`module.gms:14`)
2. P withdrawals by harvest of above-ground residues (`module.gms:15`)

**Inputs to soil:**
3. P inputs by decaying recycled residues (`module.gms:16`)
4. P inputs by burned residues — note: P does not volatilize during burning, unlike N (`module.gms:17`)
5. P inputs by manure recycled to croplands (`module.gms:18`)
6. P inputs by mineral fertilizers — drives `vm_p_fert_costs` (`module.gms:19`)
7. P inputs by release from permanent P pool / mineralization (`module.gms:20`)
8. P inputs by seed (`module.gms:21`)
9. P inputs by weathering (`module.gms:22`)

**Losses from system:**
10. P losses by erosion (`module.gms:23`)
11. P losses by leaching (`module.gms:24`)

None of these flows are currently calculated. All are cited in `module.gms:12-24` as intended structure, not implemented code.

---

## Cross-Module Connections When Phosphorus Is Enabled

The following explains what the connections WOULD be, derived entirely from what other modules currently expose or receive. These cross-module linkages are either already structurally present (residues, SOM) or identified in module_54.md's "Related Modules" section as the intended design.

### Module 54 ↔ Module 18 (Residues, default realization `flexreg_apr16`)

Module 18 already calculates phosphorus flows as part of its residue accounting, but these flows are not consumed by Module 54 (which is off). The relevant equations in the default realization `flexreg_apr16`:

**Equation `q18_res_recycling_pk`** (`flexreg_apr16/equations.gms:104-110`):
```gams
q18_res_recycling_pk(i2,pk18) ..
    vm_res_recycling(i2,pk18)
    =e=
    sum(kcr, v18_res_ag_recycling(i2,kcr,pk18)
           + vm_res_ag_burn(i2,kcr,pk18));
```

This equation calculates P (and K) recycled to soils from AG residues — the sum of residues left on field (`v18_res_ag_recycling`) plus burned residues (full P content retained, because P does **not** volatilize during burning, unlike N). The set `pk18 = {p, k}` (`flexreg_apr16/sets.gms:14-15`).

Key difference from nitrogen recycling (`q18_res_recycling_nr`, `equations.gms:90-96`): BG residues are **not** included in the P/K recycling equation, because P/K from roots is treated as already in the soil. Nitrogen from BG residues IS separately tracked (`vm_res_biomass_bg(i,kcr,"nr")`). The combustion efficiency term `(1 - f18_res_combust_eff(kcr))` that appears in the nitrogen equation is **absent** from the P/K equation — P returns fully in ash.

The variable `vm_res_recycling(i,"p")` (part of the `npk` attribute set) is produced by Module 18 and would be consumed by Module 54 when/if it becomes active, analogous to how `vm_res_recycling(i,"nr")` flows to Module 50 (nitrogen soil budget) at `modules/50_nr_soil_budget/macceff_aug22/equations.gms:24`.

**P content in residue biomass** is already tracked via `f18_attributes_residue_ag(attributes,kcr)` and `f18_attributes_residue_bg(dm_nr,kcr)` applied in `q18_prod_res_ag_reg` (`equations.gms:14-19`) and `q18_prod_res_bg_reg` (`equations.gms:24-28`). The attribute dimension includes "p" (phosphorus), so P content in aboveground and belowground residues is already computed — it simply has no downstream consumer while Module 54 is off.

### Module 54 ↔ Module 50 (Nitrogen Soil Budget, realization `macceff_aug22`)

Module 50 is the structurally closest analogue to what a phosphorus budget would look like. Key parallels and connection points:

**Module 50's cropland N balance** (`macceff_aug22/equations.gms:14-16`):
```gams
q50_nr_bal_crp(i2) ..
    vm_nr_eff(i2) * v50_nr_inputs(i2)
    =g= sum(kcr,v50_nr_withdrawals(i2,kcr));
```

A phosphorus balance, when active, would be structured analogously: P inputs (fertilizer + manure + residues + weathering) minus P withdrawals (harvest + residue removal) = delta soil P. The P fertilizer term would drive `vm_p_fert_costs(i)`.

**Module 50 already receives `vm_res_recycling(i,"nr")` from Module 18** at `equations.gms:24`:
```gams
vm_res_recycling(i2,"nr")
```
When phosphorus is enabled, the parallel connection would be Module 50 (or Module 54) consuming `vm_res_recycling(i,"p")` from Module 18.

**Module 50 also receives `vm_nr_som_fertilizer(j)` from Module 59** at `equations.gms:30`:
```gams
sum(cell(i2,j2),vm_nr_som_fertilizer(j2))
```
There is no SOM-P equivalent: Module 59 tracks C:N ratios (C:N = 15:1 assumed, `equations.gms:76`) but does not track soil phosphorus pools. So the SOM → Module 54 connection does not have a direct analogue; the P budget would need to handle soil P cycling differently.

**Interface variable `vm_p_fert_costs(i)`** would flow from Module 54 to Module 38 (Factor Costs) and Module 11 (Costs), just as `vm_nr_inorg_fert_costs(i)` flows from Module 50 to Module 11 (`module_54.md` "Related Modules" section; `module_50.md` interface table).

### Module 54 ↔ Module 59 (Soil Organic Matter, realization `cellpool_jan23`)

Module 59 provides nitrogen from SOM decomposition to Module 50. It does **not** track phosphorus in SOM.

The relevant SOM-to-nitrogen pathway:

**`q59_nr_som`** (`equations.gms:69-75`): calculates nitrogen released from SOM loss, using an assumed C:N ratio of 15:1 (`equations.gms:76`). This produces `vm_nr_som(j)`.

**`q59_nr_som_fertilizer`** (`equations.gms:81-84`): constrains plant-available nitrogen from SOM:
```gams
q59_nr_som_fertilizer(j2) ..
  vm_nr_som_fertilizer(j2) =l= vm_nr_som(j2);
```

**`q59_nr_som_fertilizer2`** (`equations.gms:88-91`): further constrains by crop uptake capacity on expanded cropland:
```gams
q59_nr_som_fertilizer2(j2) ..
  vm_nr_som_fertilizer(j2) =l=
    vm_landexpansion(j2,"crop") * s59_nitrogen_uptake;
```
Default `s59_nitrogen_uptake = 200 kg N/ha` (`input.gms:9`).

`vm_nr_som_fertilizer(j)` feeds into Module 50's nitrogen inputs at `macceff_aug22/equations.gms:30`. There is no phosphorus equivalent in Module 59 — no C:P ratio is tracked, no SOM-P release variable exists. A phosphorus budget (Module 54, if active) would need to model soil P pools (labile, stable, occluded) through a separate mechanism rather than inheriting from Module 59's SOM carbon dynamics.

---

## Summary: Default-off vs. Enabled Behavior

| Aspect | Default (`off`) | Enabled (future realization) |
|---|---|---|
| Realization | `off` — only realization | Not yet implemented |
| Equations | 0 | Would include P budget balance, P fertilizer demand, P losses |
| Variables active | `vm_p_fert_costs(i)` fixed to zero | `vm_p_fert_costs(i)` optimized |
| Residue P flows (Module 18) | Calculated by `q18_res_recycling_pk` but not consumed | `vm_res_recycling(i,"p")` consumed by P budget |
| Soil N budget (Module 50) | No P analog; N tracks independently | P budget would parallel Module 50 structure |
| SOM P release (Module 59) | Not modeled; Module 59 uses C:N=15 for N only | No direct SOM-P connection exists in current architecture |
| Manure P (Module 55) | Not tracked | Would use manure P flows analogously to `vm_manure_recycling(i,"nr")` |
| P fertilizer costs | Zero (excluded from objective function) | `vm_p_fert_costs(i)` → Module 38/11 |

---

## Source

- 🟡 Module 54: `modules/module_54.md` (module_54.md throughout) + `config/default.cfg` (realization confirmed)
- 🟡 Module 18: `modules/module_18.md` (equations.gms:104-110 for `q18_res_recycling_pk`; sets.gms:14-15 for `pk18`)
- 🟡 Module 50: `modules/module_50.md` (equations.gms:14-16, 22-32 for N budget structure; equations.gms:24, 30 for residue and SOM N inputs)
- 🟡 Module 59: `modules/module_59.md` (equations.gms:69-91 for SOM N release and fertilizer variables)
