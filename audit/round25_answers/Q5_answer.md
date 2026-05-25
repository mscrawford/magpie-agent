# R25-Q5: Trace of `Emissions|N2O|Land|Agriculture|+|Animal Waste Management`

## Summary

The IAMC variable `Emissions|N2O|Land|Agriculture|+|Animal Waste Management` is produced by
`reportEmissions()` in magpie4 v2.70.0 @ a360d8c9ec. It reads GDX variable `ov_emissions_reg`,
slices the `awms` emission-source subcategory, and applies a gas unit conversion (Mt N/yr to
Mt N2O/yr). The `ov_emissions_reg["awms"]` values are populated in the solved GDX from
`vm_emissions_reg(i,"awms",n_pollutants_direct)`, which is computed by equation
`q51_emissionbal_awms` in Module 51 (Nitrogen, realization `rescaled_jan21`), using manure flows
from Module 55 (AWMS, realization `ipcc2006_aug16`).

---

## Step 1 — magpie4 function: `reportEmissions()`

**Dispatched from**: `.cache/sources/magpie4/R/getReport.R:104` 🟢

```r
"reportEmissions(gdx, level = level)",
```

`getReport.R` calls `reportEmissions` unconditionally in its `tryList(...)` block.

**Function signature**: `.cache/sources/magpie4/R/reportEmissions.R:126` 🟢

```r
reportEmissions <- function(gdx, level = "regglo", storageWood = TRUE) {
```

**Where the Animal Waste Management variable is assembled** (`.cache/sources/magpie4/R/reportEmissions.R:884-921`) 🟢:

The internal helper `.generateNitrogenReport(.type)` is called for each of six nitrogen pollutant
types (`n2o_n`, `nh3_n`, `no2_n`, `no3_n`, `n2o_n_direct`, `n2o_n_indirect`) at line 950:

```r
nEmisTypes <- c("n2o_n", "nh3_n", "no2_n", "no3_n", "n2o_n_direct", "n2o_n_indirect")
nitrogenEmissions <- mbind(lapply(X = nEmisTypes, FUN = .generateNitrogenReport))
```

Inside `.generateNitrogenReport`, the key line is (`.cache/sources/magpie4/R/reportEmissions.R:921`) 🟢:

```r
.createReport(nEmissions, "awms", "|Agriculture|+|Animal Waste Management"),
```

This produces the IAMC name by concatenation:
`paste0("Emissions|", reportingnames(type), "|Land", .name, " (Mt ", unit, "/yr)")` (line 896)
where `type` = `"n2o"` (after the `_n` suffix is stripped) and `.name` = `"|Agriculture|+|Animal Waste Management"`,
yielding `Emissions|N2O|Land|Agriculture|+|Animal Waste Management (Mt N2O/yr)`.

The `n2o_n` → `n2o` rename and unit conversion (44/28, Mt N/yr to Mt N2O/yr) occur inside
`Emissions()` when `unit = "gas"` (`.cache/sources/magpie4/R/Emissions.R:54-66`) 🟢.

---

## Step 2 — GDX variable read: `ov_emissions_reg`

The `nEmissions` object is created at (`.cache/sources/magpie4/R/reportEmissions.R:904`) 🟢:

```r
nEmissions <- Emissions(gdx, level = level, type = .type, unit = "gas",
                        subcategories = TRUE, inorg_fert_split = TRUE)
```

Inside `Emissions()` (`.cache/sources/magpie4/R/Emissions.R:32`) 🟢:

```r
a <- readGDX(gdx, "ov_emissions_reg", react = "silent", format = "first_found",
             select = list(type = "level"))
```

`ov_emissions_reg` is a parameter in MAgPIE's auto-generated R output section ("R SECTION") of
`declarations.gms`, which stores the solved `.l` (level) values of the endogenous variable
`vm_emissions_reg(i, emis_source, pollutants)` (🟡 module_51.md, Data Flow section). The `ov_`
prefix denotes an output variable that carries the solution values of its `vm_` counterpart into
the GDX file (🟡 `reference/GAMS_MAgPIE_Patterns.md:156`).

The `awms` slice used at line 921 is dimension 3.1 of `ov_emissions_reg`, corresponding to the
emission source label `"awms"` within the `emis_source` set.

---

## Step 3 — GAMS variable and declaring module

### Variable declaration

`vm_emissions_reg(i, emis_source, pollutants)` is **declared by Module 56** (GHG Policy,
realization `price_aug22`) at `modules/56_ghg_policy/price_aug22/declarations.gms:40`
(🟡 module_51.md, Outputs section). Units: Tg N per yr (=  Mt N per yr).

### Equation that populates the `awms` subcategory

**Module 51** (Nitrogen, realization `rescaled_jan21`, default confirmed in `config/default.cfg`)
contains the equation that writes `vm_emissions_reg(i,"awms",n_pollutants_direct)`:

**`q51_emissionbal_awms(i, n_pollutants_direct)`** — `modules/51_nitrogen/rescaled_jan21/equations.gms:65-71`
(🟡 module_51.md §6, Equation 6)

Formula as documented:

```gams
vm_emissions_reg(i2,"awms",n_pollutants_direct)
=e=
sum((kli,awms_conf),
   vm_manure_confinement(i2,kli,awms_conf,"nr")
   * f51_ef3_confinement(i2,kli,awms_conf,n_pollutants_direct))
   * (1 - sum(ct, im_maccs_mitigation(ct,i2,"awms","n2o_n_direct")))
```

**Interpretation**:

- Iterates over all livestock types (`kli`, 5 types) and all confinement waste management systems
  (`awms_conf`, 9 types: lagoon, liquid_slurry, solid_storage, drylot, daily_spread, digester,
  other, pit_short, pit_long) (🟡 module_55.md §Sets).
- Multiplies manure nitrogen in confinement by system-specific emission factors
  `f51_ef3_confinement` (IPCC 2006 Chapter 10 emission factors; dimensions region × livestock ×
  confinement system × 4 pollutants). 🟡 module_51.md §Parameters.
- Applies MACC-based mitigation via `im_maccs_mitigation`, which can reduce emissions if Module 57
  (MACCs) is active. 🟡 module_51.md §6.
- **No NUE rescaling**: unlike soil-applied nitrogen sources, AWMS emissions are not rescaled by
  nitrogen use efficiency (cropland uptake efficiency is irrelevant to storage emissions).
  🟡 module_51.md §6.

### Upstream: Module 55 supplies `vm_manure_confinement`

`vm_manure_confinement(i,kli,awms_conf,"nr")` — the manure nitrogen in each confinement system —
is **declared and populated by Module 55** (AWMS, realization `ipcc2006_aug16`,
`modules/55_awms/ipcc2006_aug16/declarations.gms:21`, default confirmed in `config/default.cfg`).
The relevant equation is `q55_manure_confinement` at `modules/55_awms/ipcc2006_aug16/equations.gms:75-78`
(🟡 module_55.md §Equation 6):

```gams
vm_manure_confinement(i2,kli,awms_conf,npk) =e=
  vm_manure(i2,kli,"confinement",npk) * ic55_awms_shr(i2,kli,awms_conf)
```

Where `ic55_awms_shr` distributes total confinement manure across the 9 management systems, using
scenario-dependent shares (SSP1-5 scenarios; default SSP2; 🟡 module_55.md §Parameters).
`vm_manure(i,"confinement","nr")` is itself computed by `q55_bal_manure` (module_55.md §Equation 5)
from livestock feed intake data supplied by Module 70.

---

## Complete trace

```
report.mif: Emissions|N2O|Land|Agriculture|+|Animal Waste Management (Mt N2O/yr)
  ↑ produced by reportEmissions()
    .cache/sources/magpie4/R/reportEmissions.R:921 (.createReport with "awms", "|Agriculture|+|Animal Waste Management")
    ↑ calls Emissions(gdx, type="n2o_n", unit="gas", subcategories=TRUE)
      .cache/sources/magpie4/R/Emissions.R:32
      readGDX(gdx, "ov_emissions_reg", select=list(type="level"))["awms"]
      ↑ ov_emissions_reg is the GDX output copy of vm_emissions_reg
        vm_emissions_reg(i,"awms",n_pollutants_direct)
        ↑ set by equation q51_emissionbal_awms
          modules/51_nitrogen/rescaled_jan21/equations.gms:65-71
          Module 51 (Nitrogen, realization rescaled_jan21)
          ↑ reads vm_manure_confinement(i,kli,awms_conf,"nr")
            ↑ set by equation q55_manure_confinement
              modules/55_awms/ipcc2006_aug16/equations.gms:75-78
              Module 55 (AWMS, realization ipcc2006_aug16)
              ↑ reads vm_manure(i,kli,"confinement","nr") from q55_bal_manure
                ↑ reads vm_feed_intake(i,kli,...) from Module 70 (Livestock)
```

---

## Citations

**Source**: "Verified against .cache/sources/magpie4/R/reportEmissions.R:104,126,896,904,921; .cache/sources/magpie4/R/Emissions.R:32,54-66 (magpie4 v2.70.0 @ a360d8c9ec); module_51.md §6 (Equation 6, q51_emissionbal_awms); module_55.md §Equations 5-6 (q55_bal_manure, q55_manure_confinement)"

**Note on M2 (realization)**:
- Module 51: `rescaled_jan21` (default per `config/default.cfg`; described throughout) 🟡
- Module 55: `ipcc2006_aug16` (default per `config/default.cfg`; described throughout) 🟡
- Module 56: `price_aug22` (declares `vm_emissions_reg`) 🟡
