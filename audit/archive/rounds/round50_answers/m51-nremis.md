# Module 51 — Nitrogen Emissions: vm_emissions_reg Population and MACC Application

**Source**: `modules/module_51.md` (verified 2025-10-13), `modules/module_56.md` (verified 2025-10-12), `modules/module_53.md`, `modules/module_57.md` (verified 2025-10-12), `modules/module_58.md`

---

## 1. Who DECLARES vm_emissions_reg

`vm_emissions_reg(i, emis_source, pollutants)` is **declared by Module 56 (GHG Policy)**, realization `price_aug22`, in `modules/56_ghg_policy/price_aug22/declarations.gms:40`. Units are Tg per yr. Module 51 contains no declaration of this variable; its `equations.gms` lines are equation bodies that assign values into the variable, not declarations.

Source: `module_51.md` (Data Flow / Outputs section): "declared by Module 56 (`modules/56_ghg_policy/price_aug22/declarations.gms:40`, dimensioned `(i, emis_source, pollutants)`, units Tg per yr). Module 51's `equations.gms:9-16` are equation declarations that produce values for this variable, not its declaration."

---

## 2. Which Emission Sources and Pollutant Slices Module 51 POPULATES

Module 51 (realization `rescaled_jan21`) populates seven emission-source slices of `vm_emissions_reg`, all within the set `emis_source_n51 = {inorg_fert, man_crop, awms, resid, resid_burn, man_past, som}` (`sets.gms:15-16`). The pollutant dimensions covered are `n_pollutants_direct = {n2o_n_direct, nh3_n, no2_n, no3_n}` for the direct equations, plus `n2o_n_indirect` produced by the indirect equation.

### Equation-by-equation breakdown

| # | Equation | Source slice written | Pollutants | File:line |
|---|----------|----------------------|------------|-----------|
| 1 | `q51_emissions_man_crop` | `man_crop` | `n_pollutants_direct` | `equations.gms:22-27` |
| 2 | `q51_emissions_inorg_fert` | `inorg_fert` | `n_pollutants_direct` | `equations.gms:30-39` |
| 3 | `q51_emissions_resid` | `resid` | `n_pollutants_direct` | `equations.gms:42-46` |
| 4 | `q51_emissions_resid_burn` | `resid_burn` | `n_pollutants_direct` | `equations.gms:49-52` |
| 5 | `q51_emissions_som` | `som` | `n_pollutants_direct` | `equations.gms:55-59` |
| 6 | `q51_emissionbal_awms` | `awms` | `n_pollutants_direct` | `equations.gms:65-71` |
| 7 | `q51_emissionbal_man_past` | `man_past` | `n_pollutants_direct` | `equations.gms:74-80` |
| 8 | `q51_emissions_indirect_n2o` | `emis_source_n51` (all 7) | `n2o_n_indirect` | `equations.gms:83-89` |

Equations 1-5 and 7 apply NUE-based rescaling. Equations 4 (`resid_burn`) and 6 (`awms`) do not use NUE rescaling; `awms` uses the MACC term instead (see section 3 below). Equation 8 loops over all seven `emis_source_n51` members and writes `n2o_n_indirect` — it is self-referencing, consuming the direct-pollutant slices already written by equations 1-7.

### Preloop variable bounds

Module 51's `preloop.gms:8-10` first fixes the entire `vm_emissions_reg` to zero across all sources and pollutants, then unbounds exactly the seven `emis_source_n51` nitrogen sources:

```gams
vm_emissions_reg.fx(i,emis_source,n_pollutants) = 0       ! all sources fixed at 0
vm_emissions_reg.lo(i,emis_source_n51,n_pollutants) = -Inf ! unbound for N sources
vm_emissions_reg.up(i,emis_source_n51,n_pollutants) = Inf
```

This means only the seven N sources can carry non-zero values from Module 51's equations; all other emission sources that Module 51 does not own remain at zero from Module 51's perspective (they are freed and populated by the modules that do own them).

---

## 3. How Module 51 Applies im_maccs_mitigation from Module 57

`im_maccs_mitigation(t, i, emis_source, pollutant)` is an input-data parameter declared in Module 57 (`modules/57_maccs/on_aug22/declarations.gms:13`) and populated in Module 57's `preloop.gms:41-66` (a table lookup from MACC curves keyed by the GHG-price-to-step mapping).

Module 51 applies it **only in equation 6** (`q51_emissionbal_awms`, `equations.gms:65-71`), for the `awms` source:

```gams
vm_emissions_reg(i2,"awms",n_pollutants_direct)
=e=
sum((kli,awms_conf),
   vm_manure_confinement(i2,kli,awms_conf,"nr")
   * f51_ef3_confinement(i2,kli,awms_conf,n_pollutants_direct))
   * (1 - sum(ct, im_maccs_mitigation(ct,i2,"awms","n2o_n_direct")))
```

Key points about this application:

- The mitigation fraction read is `im_maccs_mitigation(ct, i2, "awms", "n2o_n_direct")` — the N2O-specific MACC result.
- It is applied as a uniform multiplicative abatement factor `(1 - mitigation_fraction)` to **all** `n_pollutants_direct` (N2O, NH3, NOx, NO3-), not just N2O (`equations.gms:62-64`). This is an explicit assumption: measures that reduce AWMS N2O (e.g., covered storage, digesters) are assumed to also reduce all other N pollutants from the same confinement systems.
- The `awms` slice is the **only** slice where Module 51 applies `im_maccs_mitigation`. The other six source equations in Module 51 contain no MACC term.
- None of the NUE-rescaled equations (man_crop, inorg_fert, resid, som, man_past) use `im_maccs_mitigation` directly; any MACC influence on soil N2O works indirectly through NUE in Module 50 (which is a separate channel), not as a multiplier in Module 51's equations.

---

## 4. Which Other Modules POPULATE vm_emissions_reg

Module 51 is not the only populator. Based on the module documentation:

| Module | Sources written | Pollutant(s) | Key equations |
|--------|-----------------|--------------|---------------|
| **51** (nitrogen, `rescaled_jan21`) | `inorg_fert`, `man_crop`, `awms`, `resid`, `resid_burn`, `man_past`, `som` | `n2o_n_direct`, `nh3_n`, `no2_n`, `no3_n`, `n2o_n_indirect` | `q51_emissions_*`, `q51_emissionbal_*` (`equations.gms:22-89`) |
| **53** (methane, `ipcc2006_aug22`) | `ent_ferm`, `awms`, `rice`, `resid_burn` | `ch4` | `q53_emissionbal_ch4_ent_ferm` (`equations.gms:21-29`), plus AWMS, rice, resid_burn CH4 equations (`equations.gms:40-72`) |
| **58** (peatland, `v2`) | peatland sources | `co2_c`, `ch4`, `n2o_n_direct` | peatland emission equations |

Module 52 does **not** directly write into `vm_emissions_reg` for the purpose of the GHG policy pricing equations; CO2 from land-use change is calculated inside Module 56's own equation `q56_emis_pricing_co2` (`equations.gms:19-22`) by reading `vm_carbon_stock` directly, deliberately bypassing `vm_emissions_reg` for one-off CO2. This is confirmed by `module_56.md` §2.2: "CO2 pricing is calculated directly from `vm_carbon_stock`, intentionally bypassing `vm_emissions_reg`."

---

## 5. Who READS vm_emissions_reg

Two modules read `vm_emissions_reg` as consumers:

**Module 56 (GHG Policy)**
- `q56_emis_pricing` (`equations.gms:15-17`): Reads `vm_emissions_reg(i2, emis_annual, pollutants)` to set `v56_emis_pricing`, which feeds into the emission-cost calculation.

**Module 57 (MACCs)**
- `q57_labor_costs` (`equations.gms:35-43`) and `q57_capital_costs` (`equations.gms:45-52`): Both read `vm_emissions_reg(i2, emis_source, pollutants_maccs57)` as the post-mitigation emission level, then back-calculate pre-mitigation baseline as `vm_emissions_reg / (1 - im_maccs_mitigation)` to integrate the area under the MACC cost curve.

The `module_51.md` Downstream Dependencies table confirms: "Module 56 (ghg_policy): N2O emissions for GHG accounting; Module 57 (maccs): Baseline emissions for MAC-cost integral (`modules/57_maccs/on_aug22/equations.gms:38,48`)."

---

## 6. Summary of Roles

```
DECLARES:    Module 56  (modules/56_ghg_policy/price_aug22/declarations.gms:40)

POPULATES:
  Module 51  — 7 N-sources × n_pollutants_direct + n2o_n_indirect    (equations.gms:22-89)
  Module 53  — CH4 sources (ent_ferm, awms, rice, resid_burn)         (equations.gms:21-72)
  Module 58  — peatland sources (CO2, CH4, N2O)

READS:
  Module 56  — for emission pricing (equations.gms:15-17)
  Module 57  — for MACC cost integral (equations.gms:35-52)
```

---

## Epistemic Status

All claims sourced from AI documentation read this session:

- `modules/module_51.md` (Equations section, Data Flow section, Execution Phases section) — 🟡 Documented
- `modules/module_56.md` (§2.1, §2.2, §3.7, Declarations) — 🟡 Documented
- `modules/module_53.md` (Core Functionality, q53_emissionbal_ch4_ent_ferm) — 🟡 Documented
- `modules/module_57.md` (Equations §1 and §2, Step 3) — 🟡 Documented
- `modules/module_58.md` (§1.3 Architectural Position) — 🟡 Documented

Raw GAMS source was not read per task constraints. Line numbers are as recorded in documentation at last verification date (2025-10-12 to 2025-10-13); code changes since then may have shifted them.
