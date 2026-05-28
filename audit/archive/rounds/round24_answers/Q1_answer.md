# R24-Q1 Sonnet answer (CH4 rice → GHG pricing chain)

## Module 53 rice CH4 computation and propagation to Module 56 GHG pricing

**Active realization**: `ipcc2006_aug22` (confirmed as default in `modules/module_53.md`: `cfg$gms$methane <- "ipcc2006_aug22"`).

---

### (a) The rice CH4 equation: `q53_emissionbal_ch4_rice`

The equation that populates the rice CH4 emissions entry into the shared emissions variable is `q53_emissionbal_ch4_rice`, documented in `modules/module_53.md` at equations.gms:59-63:

```gams
q53_emissionbal_ch4_rice(i2) ..
  vm_emissions_reg(i2,"rice","ch4") =e=
    sum((cell(i2,j2),w), vm_area(j2,"rice_pro",w)
        * sum(ct, f53_ef_ch4_rice(ct,i2)))
    * (1 - sum(ct, im_maccs_mitigation(ct,i2,"rice","ch4")));
```

The structure is:

- **Outer set-sum**: `sum((cell(i2,j2),w), ...)` sums over all simulation cells `j2` that belong to region `i2` (via the `cell(i2,j2)` mapping) and over all water management types `w` (rainfed, irrigated).
- **Rice area**: `vm_area(j2,"rice_pro",w)` is the harvested area of rice (in ha) at cell level, provided by Module 30 (Croparea) or Module 17 (Production). MANDATE 10 applies here: the sum over `w` is retained as-is; it is not expanded into explicit irrigated/rainfed terms.
- **Emission factor**: `f53_ef_ch4_rice(ct,i2)` is the CH4 emission rate in tCH4/ha/year, applied uniformly at the region level (not distinguished by `w`). This is a documented limitation: all rice area in a region — irrigated and rainfed alike — receives the same regional average emission factor.
- **MACC mitigation**: `(1 - sum(ct, im_maccs_mitigation(ct,i2,"rice","ch4")))` reduces gross emissions by the technical mitigation fraction provided by Module 57. Technologies include alternate wetting and drying (AWD), mid-season drainage, and improved cultivars. Mitigation here is applied to the region-level aggregate before writing to `vm_emissions_reg`.

The left-hand side writes to `vm_emissions_reg(i2,"rice","ch4")` — a variable declared in Module 56, not Module 53. This is the transmission variable between the two modules.

---

### (b) Source of the emission factor: `f53_ef_ch4_rice`

The emission factor is the parameter `f53_ef_ch4_rice(t_all,i)` (modules/module_53.md, Data Inputs section, equations.gms:62 and input.gms:16-21):

- **Loaded from**: `f53_EFch4Rice.cs4` (input.gms:19).
- **Dimensions**: `t_all` (all time periods) and `i` (regions). The time dimension allows for time-varying values reflecting management changes or cultivar adoption trends across scenarios; the regional dimension captures differences in water management prevalence, organic amendments, soil type, and climate. The factor is NOT distinguished by water management type `w` within a region — that is an explicit simplification noted in the documentation.
- **Methodological basis**: IPCC 2006 Guidelines for National Greenhouse Gas Inventories, calibrated to FAO Rice Cultivation Emissions statistics (equations.gms:57).
- **Nature of the factor**: This is a parameterized input, not a mechanistically computed value. The emission factor is read from an input data file at model initialization; it is not recalculated based on any model state during the optimization. In the equation, `f53_ef_ch4_rice` enters as a data-driven scalar per region-year, so what the model computes is rice area times a fixed rate — classic parameterization, not mechanistic rice CH4 modeling.

---

### (c) How Module 56 picks up the rice CH4 emissions for pricing

The interface variable `vm_emissions_reg(i,emis_source,pollutants)` is declared in Module 56 (GHG Policy) and written by Module 53 (modules/module_53.md, Interface Variables section). Module 56 picks it up through two sequential equations:

**Step 1: Routing to the pricing variable — `q56_emis_pricing`**

Documented in `modules/module_56.md`, equations.gms:15-17:

```gams
q56_emis_pricing(i2,pollutants,emis_annual) ..
  v56_emis_pricing(i2,emis_annual,pollutants) =e=
    vm_emissions_reg(i2,emis_annual,pollutants);
```

Rice CH4 is an annual (recurring) emission — rice paddies emit CH4 every year the land is managed — so it falls under the `emis_annual` set. Equation `q56_emis_pricing` simply passes `vm_emissions_reg(i2,"rice","ch4")` through to the internal variable `v56_emis_pricing(i2,"rice","ch4")` without modification. No annuity factor is applied here (that is reserved for one-off land-use-change CO2 in `q56_emis_pricing_co2`).

**Step 2: Computing the cost — `q56_emission_cost_annual`**

Documented in `modules/module_56.md`, equations.gms:29-33:

```gams
q56_emission_cost_annual(i2,emis_annual) ..
  v56_emission_cost(i2,emis_annual) =e=
    sum(pollutants,
        v56_emis_pricing(i2,emis_annual,pollutants) *
        sum(ct, im_pollutant_prices(ct,i2,pollutants,emis_annual)));
```

For the rice CH4 entry, this resolves to:

```
v56_emission_cost(i2,"rice") = v56_emis_pricing(i2,"rice","ch4") × im_pollutant_prices(ct,i2,"ch4","rice")
```

`im_pollutant_prices(ct,i,pollutants,emis_source)` is the GHG price (USD17MER per Tg) loaded during the preloop phase from the scenario-specific price file (`f56_pollutant_prices.cs3`), selected by the switch `c56_pollutant_prices`. Whether the "rice" emission source is actually priced depends on the `c56_emis_policy` switch, which configures which (gas, source) combinations receive a non-zero price. Under the default policy `reddnatveg_nosoil`, soil-based CH4 sources may or may not be included; this is determined by the policy configuration table in `f56_pollutant_prices.cs3`.

**Step 3: Aggregation to total emission cost — `q56_emission_costs`**

Documented in `modules/module_56.md`, equations.gms:56-58:

```gams
q56_emission_costs(i2) ..
  vm_emission_costs(i2) =e=
    sum(emis_source, v56_emission_cost(i2,emis_source));
```

The per-source costs — including the rice CH4 component — are summed to `vm_emission_costs(i2)`, which enters Module 11 (Costs) as part of MAgPIE's objective function. The optimizer minimizes total costs including this GHG cost term, creating the economic incentive for the model to reduce rice area, adopt MACC mitigation measures, or shift production that drives the CH4 cost.

---

### Summary of the chain

```
vm_area(j2,"rice_pro",w)   [Module 30/17]
  × f53_ef_ch4_rice(ct,i2) [input: f53_EFch4Rice.cs4]
  × (1 - im_maccs_mitigation(...,"rice","ch4")) [Module 57]
  → vm_emissions_reg(i2,"rice","ch4")   [written by q53_emissionbal_ch4_rice]
  → v56_emis_pricing(i2,"rice","ch4")   [routed by q56_emis_pricing]
  × im_pollutant_prices(ct,i2,"ch4","rice")
  → v56_emission_cost(i2,"rice")        [q56_emission_cost_annual]
  → vm_emission_costs(i2)               [q56_emission_costs → Module 11 objective]
```

One structural point worth flagging explicitly (MANDATE 4): MACC mitigation for rice is present in the code but is adoption-rate driven. If no carbon price is active (i.e., `c56_pollutant_prices = "none"` or the rice source is excluded from `c56_emis_policy`), Module 57 will provide zero mitigation, and the full gross rice CH4 enters the chain but accumulates no GHG cost. The MACC term and the pricing pathway are both necessary for rice CH4 to actually exert economic pressure in the optimization.

---

Based on `modules/module_53.md` (fully verified against `modules/53_methane/ipcc2006_aug22/*.gms`, last verified 2026-03-06) and `modules/module_56.md` (fully verified against `modules/56_ghg_policy/price_aug22/*.gms`, status verified 2025-10-12). Loaded helper: `agent/helpers/verifiers.md` (16 anti-confabulation MANDATEs).
