# Q1 Answer: LUC CO2 → Global Objective Cost Chain

**Round:** 42 | **Date:** 2026-06-03 | **Model:** Claude Sonnet 4.6

---

## (a) How `f56_emis_policy` selects priced (pollutant, source) pairs

### The parameter

`f56_emis_policy(scen56, pollutants, emis_source)` is a **binary matrix** (0/1 entries) stored in the input data file `f56_emis_policy.csv`. It has three dimensions:

- `scen56`: policy scenario name (60+ rows, including `"reddnatveg_nosoil"`, `"all"`, `"none"`, etc.)
- `pollutants`: greenhouse gas (`"co2_c"`, `"ch4"`, `"n2o_n_direct"`, `"n2o_n_indirect"`)
- `emis_source`: emission-source label (`primforest_vegc`, `secdforest_litc`, `inorg_fert`, `ent_ferm`, etc.)

A value of **1** means "price this (pollutant, source) pair"; a value of **0** means "do not price it".

### How it gates pricing — Stage 7 of preloop

🟡 (`modules/56_ghg_policy/price_aug22/preloop.gms:84-91`)

```gams
loop(t_all,
 if(m_year(t_all) <= sm_fix_SSP2,
  im_pollutant_prices(t_all,i,pollutants,emis_source) =
    im_pollutant_prices(t_all,i,pollutants,emis_source)
    * f56_emis_policy("reddnatveg_nosoil",pollutants,emis_source);
 else
  im_pollutant_prices(t_all,i,pollutants,emis_source) =
    im_pollutant_prices(t_all,i,pollutants,emis_source)
    * f56_emis_policy("%c56_emis_policy%",pollutants,emis_source);
 );
);
```

**Mechanism**: the already-loaded GHG prices `im_pollutant_prices` (constructed in Stages 1–6, e.g. from `f56_pollutant_prices.cs3` for a named scenario) are **multiplied** by the 0/1 matrix. Any pair with a 0 entry becomes zero regardless of the price level in the scenario file. Any pair with a 1 entry keeps its price unchanged.

**Historical override**: for years ≤ `sm_fix_SSP2` (default 2025), the matrix is always applied with the hardcoded `"reddnatveg_nosoil"` row, regardless of the runtime `c56_emis_policy` setting. This prevents retrospective carbon pricing in historical calibration years.

**Effect**: `im_pollutant_prices` after Stage 7 is the **effective** price matrix — non-zero only for (pollutant, source) pairs where the chosen policy scenario has a 1-entry.

---

## (b) Pricing chain from carbon-stock change to `vm_emission_costs`

The chain involves four equations across Modules 52, 56, and 56's cost aggregation. The default CO2 pricing path (for one-off, i.e. land-use-change CO2) proceeds as follows:

### Step 1 — Carbon stock change → `vm_emissions_reg` (Module 52, but declared in M56)

🟡 (`modules/52_carbon/normal_dec17/equations.gms:16-19`)

```gams
q52_emis_co2_actual(i2,emis_oneoff) ..
  vm_emissions_reg(i2,emis_oneoff,"co2_c") =e=
    sum((cell(i2,j2),emis_land(emis_oneoff,land,c_pools)),
      (pcm_carbon_stock(j2,land,c_pools,"actual")
       - vm_carbon_stock(j2,land,c_pools,"actual"))
      / m_timestep_length);
```

Module 52's equation `q52_emis_co2_actual` computes annual CO2 from land-use change as (previous carbon stock − current carbon stock) / timestep length, aggregated over all cells and land–pool combinations belonging to the `emis_oneoff` source. The result populates `vm_emissions_reg(i, emis_oneoff, "co2_c")` (Tg C/yr). Note that `vm_carbon_stock` is **declared in M56**, not M52; land modules (M29, M31, M32, M34, M35) and M59 (soilc) populate it.

### Step 2 — `vm_carbon_stock` change → `v56_emis_pricing` (Module 56, DIRECT path — bypasses `vm_emissions_reg`)

🟡 (`modules/56_ghg_policy/price_aug22/equations.gms:19-22`)

```gams
q56_emis_pricing_co2(i2,emis_oneoff) ..
  v56_emis_pricing(i2,emis_oneoff,"co2_c") =e=
    sum((cell(i2,j2),emis_land(emis_oneoff,land,c_pools)),
      (pcm_carbon_stock(j2,land,c_pools,"actual")
       - vm_carbon_stock(j2,land,c_pools,"%c56_carbon_stock_pricing%"))
      / m_timestep_length);
```

**Critical architectural note**: for one-off CO2 (land-use change), Module 56 does **not** route through `vm_emissions_reg`. Instead, equation `q56_emis_pricing_co2` computes the same stock-change quantity independently, but using the configurable stock type `%c56_carbon_stock_pricing%` (default `"actualNoAcEst"`, which excludes afforestation establishment to avoid double-counting with CDR rewards). The result is `v56_emis_pricing(i, emis_oneoff, "co2_c")` (Tg C/yr).

In contrast, annual (recurring) emissions (CH4, N2O, and other annual CO2) do flow through `vm_emissions_reg`:

🟡 (`modules/56_ghg_policy/price_aug22/equations.gms:15-17`)

```gams
q56_emis_pricing(i2,pollutants,emis_annual) ..
  v56_emis_pricing(i2,emis_annual,pollutants) =e=
    vm_emissions_reg(i2,emis_annual,pollutants);
```

### Step 3 — `v56_emis_pricing` × effective price → `v56_emission_cost` (Module 56)

For one-off sources (deforestation CO2):

🟡 (`modules/56_ghg_policy/price_aug22/equations.gms:45-52`)

```gams
q56_emission_cost_oneoff(i2,emis_oneoff) ..
  v56_emission_cost(i2,emis_oneoff) =e=
    sum(pollutants,
        v56_emis_pricing(i2,emis_oneoff,pollutants)
        * m_timestep_length
        * sum(ct, im_pollutant_prices(ct,i2,pollutants,emis_oneoff)
              * pm_interest(ct,i2)/(1+pm_interest(ct,i2))));
```

The formula `× m_timestep_length × price × r/(1+r)` converts the annualised emission rate back to a total stock-change, then multiplies by an infinite-horizon annuity factor `r/(1+r)`. This levels a one-time emission cost against recurring annual costs: without it, deforestation (a single event) would appear cheaper than fertilization (recurring). Units: Tg/yr × yr × USD17MER/Mg × (dimensionless) = mio. USD17MER/yr (because 1 Tg = 10⁶ Mg, so Tg × USD/Mg = mio. USD).

For annual sources (CH4, N2O):

🟡 (`modules/56_ghg_policy/price_aug22/equations.gms:29-33`)

```gams
q56_emission_cost_annual(i2,emis_annual) ..
  v56_emission_cost(i2,emis_annual) =e=
    sum(pollutants,
        v56_emis_pricing(i2,emis_annual,pollutants)
        * sum(ct, im_pollutant_prices(ct,i2,pollutants,emis_annual)));
```

### Step 4 — Sum over all sources → `vm_emission_costs` (Module 56)

🟡 (`modules/56_ghg_policy/price_aug22/equations.gms:56-58`)

```gams
q56_emission_costs(i2) ..
  vm_emission_costs(i2) =e=
    sum(emis_source, v56_emission_cost(i2,emis_source));
```

`vm_emission_costs(i)` (mio. USD17MER/yr) is the total regional emission cost across all sources (annual + one-off).

### Summary of the chain

```
vm_carbon_stock (land modules)
  → pcm_carbon_stock – vm_carbon_stock  (stock change)
  → q56_emis_pricing_co2 → v56_emis_pricing(i,emis_oneoff,"co2_c")  [direct, not via vm_emissions_reg]
  → × im_pollutant_prices × annuity factor (m_timestep_length × r/(1+r))
  → q56_emission_cost_oneoff → v56_emission_cost(i,emis_oneoff)
  → q56_emission_costs → vm_emission_costs(i)
```

`im_pollutant_prices` at this point already encodes the `f56_emis_policy` gating (Stage 7 of preloop): if the source–pollutant pair was zeroed out by the policy matrix, `im_pollutant_prices = 0`, so `v56_emission_cost = 0` regardless of the physical emission magnitude.

---

## (c) Where `vm_emission_costs` enters the Module 11 objective

🟡 (`modules/11_costs/default/equations.gms:15-47`)

Equation `q11_cost_reg` aggregates all regional cost components into `v11_cost_reg(i)`:

```gams
q11_cost_reg(i2) .. v11_cost_reg(i2) =e=
  ...
  + vm_emission_costs(i2)
  - vm_reward_cdr_aff(i2)
  ...
;
```

`vm_emission_costs(i)` appears as a **positive additive term** (`equations.gms:26`). The CDR reward `vm_reward_cdr_aff(i)` (also from M56) appears with a **negative sign** immediately after (`equations.gms:27`), so afforestation CDR revenue partially or fully offsets emission costs.

`v11_cost_reg` is then summed globally:

🟡 (`modules/11_costs/default/equations.gms:10`)

```gams
q11_cost_glo .. vm_cost_glo =e= sum(i2, v11_cost_reg(i2));
```

`vm_cost_glo` is the single variable MAgPIE minimizes. Increasing `vm_emission_costs` — through higher emissions or a higher carbon price — raises `vm_cost_glo`, incentivizing the solver to reduce land-use-change CO2 by retaining forest, extensifying cropland conversion, etc.

---

## (d) Which non-default `c56_emis_policy` scenarios additionally price agricultural CH4/N2O, and does `redd+natveg_nosoil` price them?

### Scenarios that additionally price agricultural CH4 and N2O

🟡 (`modules/56_ghg_policy/price_aug22/modules/module_56.md:654-667`, Section 5.2 table)

The following non-default scenarios price agricultural CH4 and/or N2O alongside LULUCF CO2:

| Scenario | CH4 | N2O | Notes |
|----------|-----|-----|-------|
| `all` | ✓ | ✓ | Price all gases and all sources including soil C |
| `all_nosoil` | ✓ | ✓ | Price all gases except soil CO2 |
| `reddnatveg_nosoil` **(default)** | ✓ (ag: awms, resid_burn, rice, ent_ferm, peatland) | ✓ (ag: inorg_fert, man_crop, awms, resid, resid_burn, man_past, som, rice + indirect N) | "nosoil" means soil C excluded, not non-CO2 gases |
| `sdp_all` | ✓ | ✓ | Sustainable Development Pathway |

**Important caveat about the default**: `reddnatveg_nosoil` itself (the default) DOES price agricultural CH4 and N2O. The name describes CO2 coverage (REDD+ natural-vegetation CO2 stocks, excluding soil carbon), not non-CO2 gas coverage. See `module_56_notes.md:19` ("Default behavior: rice CH4 IS priced under `reddnatveg_nosoil`").

### Does `redd+natveg_nosoil` price agricultural CH4/N2O?

🟡 (`modules/56_ghg_policy/price_aug22/modules/module_56.md:662`)

**No.** According to the policy scenario table in the documentation:

| Scenario | CO2 LULUCF | CH4 | N2O |
|----------|------------|-----|-----|
| `redd+natveg_nosoil` | ✓ (deforestation + reforestation) | ✗ | ✗ |

`redd+natveg_nosoil` covers only CO2 from deforestation and reforestation. It does **not** price agricultural CH4 or N2O. This is in contrast to the default `reddnatveg_nosoil` (no `+`), which does price agricultural non-CO2 gases. The `+` in the name signals an expanded forestry CO2 coverage (adding reforestation/afforestation CO2 to the deforestation-only REDD scope) but at the same time the policy does not extend to non-CO2 agricultural sources.

---

## Source Statement

All claims are 🟡 **Documented** — drawn from AI documentation read in this session. No raw GAMS source was opened.

Primary sources:
- `<magpie-agent>/modules/module_56.md` — M56 full documentation (Sections 2, 3.7, 5.2; lines 51-116, 478-514, 654-667)
- `<magpie-agent>/modules/module_52.md` — M52 documentation (Section 3, equations.gms:16-19)
- `<magpie-agent>/modules/module_11.md` — M11 documentation (Section 2.2, equations.gms:15-47, 26-27)
- `<magpie-agent>/modules/module_56_notes.md` — notes on default behavior and unit conventions
- `<magpie-root>/config/default.cfg` — confirmed `c56_emis_policy = "reddnatveg_nosoil"` default

**Default realization confirmed**: Module 56 has a single realization `price_aug22` (no multi-realization ambiguity). All claims describe this realization.

**Doc coverage**: All four sub-questions are covered by the module documentation. No gaps requiring doc creation — though a dedicated "reddnatveg_nosoil vs redd+natveg_nosoil comparison" section would save confusion in future queries.
