# Module 56 GHG Policy: vm_emissions_reg Producers, Consumers, and Pricing Equations

**Default realization**: `price_aug22` (Module 56 has a single realization — module_56.md §13 Limitations, item 3).

---

## 1. What is vm_emissions_reg?

`vm_emissions_reg(i, emis_source, pollutants)` is the **central interface variable** for regional GHG emissions. It is **declared in Module 56** (module_56.md §4.2; module_52.md "Variables Written by Module 52"). Its dimensions span all regions (i), all emission sources (emis_source — a superset of both emis_oneoff and emis_annual), and all pollutants.

---

## 2. Which modules POPULATE vm_emissions_reg, and for which subset?

### Module 52 (Carbon, normal_dec17) — POPULATES for emis_oneoff, pollutant "co2_c"

Module 52 **writes** `vm_emissions_reg` via equation **q52_emis_co2_actual** (module_52.md §3, equations.gms:16-19):

```gams
q52_emis_co2_actual(i2,emis_oneoff) ..
  vm_emissions_reg(i2,emis_oneoff,"co2_c") =e=
    sum((cell(i2,j2),emis_land(emis_oneoff,land,c_pools)),
      (pcm_carbon_stock(j2,land,c_pools,"actual") - vm_carbon_stock(j2,land,c_pools,"actual"))
      / m_timestep_length
    );
```

- **Subset populated**: `emis_oneoff` x `"co2_c"` (one-off CO2-C emissions from all land/pool combinations mapped through `emis_land`)
- **Mechanism**: Stock-difference method — previous minus current carbon stock, annualised by dividing by `m_timestep_length`
- **emis_oneoff sources** include: crop_vegc, crop_litc, crop_soilc, past_vegc, past_litc, past_soilc, forestry_vegc, forestry_litc, forestry_soilc, primforest_vegc, primforest_litc, primforest_soilc, secdforest_vegc, secdforest_litc, secdforest_soilc, urban_vegc, urban_litc, urban_soilc, other_vegc, other_litc, other_soilc (module_52.md §3, core/sets.gms:314-318)
- **Role**: POPULATED (left-hand side of an =e= equation)
- **Citation**: module_52.md equations.gms:16-19; "Variables Written by Module 52"

### Module 51 (Nitrogen, rescaled_jan21) — POPULATES for emis_annual, N pollutants

Module 51 writes `vm_emissions_reg` for annual nitrogen emission sources via 8 equations. The pattern is shown by equation q51_emissions_man_crop (module_51.md §Equations):

```gams
q51_emissions_man_crop(i2,n_pollutants_direct) ..
  vm_emissions_reg(i2,"man_crop",n_pollutants_direct) =e= ...
```

Similar equations cover: `"inorg_fert"`, `"resid"`, `"resid_burn"`, `"som"`, `"man_past"`, `"rice"` (N2O), and indirect N2O.

- **Subset populated**: `emis_annual` emission sources for N pollutants (n2o_n_direct, n2o_n_indirect, nh3_n, nox_n, no3_n, n2_n)
- **Role**: POPULATED

### Module 53 (Methane, ipcc2006_aug22) — POPULATES for emis_annual, "ch4"

Module 53 writes `vm_emissions_reg` via 4 equations covering CH4 from enteric fermentation, AWMS, rice, and residue burning. Example (module_53.md §1 Enteric Fermentation, equations.gms:21-29):

```gams
vm_emissions_reg(i2,"ent_ferm","ch4") =e=
  1/55.65 * (...feed intake × gross energy × Ym factors...)
  * (1 - sum(ct, im_maccs_mitigation(ct,i2,"ent_ferm","ch4")));
```

- **Subset populated**: `emis_annual` emission sources (`ent_ferm`, `awms`, `rice`, `resid_burn`) for pollutant `"ch4"`
- **Role**: POPULATED
- Note: 3 of 4 sources include the `(1 - im_maccs_mitigation)` MACC reduction term (module_53.md §Core Functionality, equations.gms:29, 52, 63). `resid_burn` is mitigated only via reducing burned quantities, not MACC technical mitigation.

### Other emission modules (50/55/58/peatland)

Module_56.md §4.2 and §12.2 lists "emission modules (51 N2O, 52 LULUCF CO2, 53 CH4, 57 MACC-adjusted, 58 peatland)" as providing `vm_emissions_reg`. Modules 50 (SOM), 55 (AWMS), and 58 (peatland) also write into the emis_annual slice for their respective sources.

---

## 3. Does Module 57 (MACCs) POPULATE or only READ vm_emissions_reg?

**Module 57 only READS vm_emissions_reg — it does not populate it.**

The MACC equations q57_labor_costs and q57_capital_costs (module_57.md §Equations, equations.gms:35-52) use `vm_emissions_reg` on the **right-hand side** to compute mitigation costs:

```gams
vm_maccs_costs(i2,"labor") =e=
  (sum((ct,emis_source,pollutants_maccs57),
     p57_maccs_costs_integral(ct,i2,emis_source,pollutants_maccs57)
     * vm_emissions_reg(i2,emis_source,pollutants_maccs57)
     / (1 - im_maccs_mitigation(ct,i2,emis_source,pollutants_maccs57)))
   + ...) * ...
```

Module 57 reads `vm_emissions_reg` for `pollutants_maccs57` = {ch4, n2o_n_direct} across the emis_source subset it covers (module_57.md §Data Flow Inputs). Module 57's output is `vm_maccs_costs` (to Module 11) and `im_maccs_mitigation` (to Modules 51/53/50 preloop, where it modifies baseline emissions before those modules populate `vm_emissions_reg`).

**Role of Module 57 with respect to vm_emissions_reg**: READ only. It influences the values via `im_maccs_mitigation` applied upstream in Module 53's equations, but Module 57 itself does not hold the left-hand side of any equation writing to `vm_emissions_reg`.

- **Citation**: module_57.md §Data Flow; equations.gms:35-52; "Downstream Dependencies" table

---

## 4. How does q56_emis_pricing use vm_emissions_reg?

**q56_emis_pricing reads vm_emissions_reg for emis_annual only.**

```gams
q56_emis_pricing(i2,pollutants,emis_annual) ..
  v56_emis_pricing(i2,emis_annual,pollutants) =e=
    vm_emissions_reg(i2,emis_annual,pollutants);
```

(module_56.md §2.1, equations.gms:12-17)

This equation passes recurring (annual) emissions — N2O from fertilizer, CH4 from livestock, etc. — directly to `v56_emis_pricing`, which is then multiplied by `im_pollutant_prices` in q56_emission_cost_annual (equations.gms:29-33) to produce emission costs.

The `emis_annual` set contains recurring emission sources (those that occur every year under ongoing management — fertilizer use, livestock, etc.). Their full magnitude enters pricing without adjustment.

---

## 5. How does q56_emis_pricing_co2 differ? The carbon-stock CO2 path.

**q56_emis_pricing_co2 deliberately bypasses vm_emissions_reg entirely for one-off CO2.**

```gams
q56_emis_pricing_co2(i2,emis_oneoff) ..
  v56_emis_pricing(i2,emis_oneoff,"co2_c") =e=
    sum((cell(i2,j2),emis_land(emis_oneoff,land,c_pools)),
      (pcm_carbon_stock(j2,land,c_pools,"actual")
       - vm_carbon_stock(j2,land,c_pools,"%c56_carbon_stock_pricing%"))
      / m_timestep_length);
```

(module_56.md §2.2, equations.gms:19-22)

Key distinctions from q56_emis_pricing:

1. **Subset**: covers `emis_oneoff` only (deforestation and other one-off land-use change CO2 sources), not emis_annual.

2. **Does not read vm_emissions_reg**: reads carbon stocks directly — `pcm_carbon_stock` (previous timestep, always "actual") minus `vm_carbon_stock` (current timestep, type governed by `c56_carbon_stock_pricing`).

3. **The `c56_carbon_stock_pricing` switch** (default `"actualNoAcEst"`) determines which carbon pools are included in LULUCF CO2 accounting. `"actualNoAcEst"` excludes afforestation establishment carbon from pricing to avoid double-counting with the CDR reward mechanism `vm_reward_cdr_aff`. Using `"actual"` would include all carbon stock changes including afforestation.

4. **Why bypass vm_emissions_reg?** Module 56 does this to give itself a full LULUCF accounting lens: it can apply pool-selection granularity (via `c56_carbon_stock_pricing`) that the stock-difference equation in Module 52 (q52_emis_co2_actual, which always uses "actual") does not provide. Module 52's q52_emis_co2_actual populates `vm_emissions_reg(i,emis_oneoff,"co2_c")` using the "actual" stockType, while Module 56's q56_emis_pricing_co2 recalculates CO2 for pricing purposes from `vm_carbon_stock` with the configurable stockType — so one-off CO2 is computed twice, from different angles, for different purposes.

5. **Annuity factor**: The resulting `v56_emis_pricing(i,emis_oneoff,"co2_c")` flows into q56_emission_cost_oneoff (equations.gms:45-52), which applies `× m_timestep_length × price × r/(1+r)` — converting the annualised emission rate back to a total timestep quantity and then to an equivalent perpetual annual cost via the annuity due factor. This levels one-off deforestation costs against recurring emission costs.

---

## 6. Summary table: DECLARED vs. POPULATED vs. READ

| Module | Equation | Action on vm_emissions_reg | Subset |
|--------|----------|-----------------------------|--------|
| **56** (GHG Policy, price_aug22) | — (declarations.gms) | DECLARED | all dims |
| **52** (Carbon, normal_dec17) | q52_emis_co2_actual (equations.gms:16-19) | POPULATED | emis_oneoff × "co2_c" |
| **51** (Nitrogen, rescaled_jan21) | q51_emissions_* (equations.gms:22-) | POPULATED | emis_annual × N pollutants |
| **53** (Methane, ipcc2006_aug22) | q53_emissionbal_* (equations.gms:21-72) | POPULATED | emis_annual × "ch4" |
| **57** (MACCs, on_aug22) | q57_labor_costs, q57_capital_costs (equations.gms:35-52) | READ only | emis_annual × {ch4, n2o_n_direct} |
| **56** (GHG Policy, price_aug22) | q56_emis_pricing (equations.gms:12-17) | READ (assigns to v56_emis_pricing) | emis_annual × all pollutants |
| **56** (GHG Policy, price_aug22) | q56_emis_pricing_co2 (equations.gms:19-22) | NOT READ (bypasses; reads vm_carbon_stock directly) | emis_oneoff × "co2_c" |

---

## Epistemic status

- module_56.md: 🟡 Documented (read this session; fully verified 2025-10-13 per module_56.md footer)
- module_52.md: 🟡 Documented (read this session; fully verified per module_52.md; updated 2026-04-20 for PR #869 growing-stock calibration — the q52_emis_co2_actual equation itself is unaffected by that PR)
- module_57.md: 🟡 Documented (read this session; fully verified 2025-10-13 per module_57.md footer)
- module_51.md and module_53.md: 🟡 Documented (read this session; verified per their footers)

No raw GAMS source code was read this session (per task constraints). Line numbers cited from module docs were verified at their last update dates and may have shifted in code since then. For critical modifications, verify against current equations.gms files.
