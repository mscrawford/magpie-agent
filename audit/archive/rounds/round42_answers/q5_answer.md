# Q5 Answer: Bioenergy Demand IAMC Variable — Full Trace

**Version pin**: magpie4 v2.70.0 @ SHA a360d8c9ec (resolution: sha, exact match)  
**Pin file**: `/Users/turnip/Documents/Work/Workspace/magpie/magpie-agent/project/version_pins.json`  
**Cached source root**: `.cache/sources/magpie4/` (all source paths below are relative to this root)

---

## (a) magpie4 `report*` function and source file

**Function**: `reportDemandBioenergy`  
**Source**: `.cache/sources/magpie4/R/reportDemandBioenergy.R` (v2.70.0 @ a360d8c9ec) 🟢

**Dispatch**: Called unconditionally from `getReport()` at:
```
R/getReport.R:79  "reportDemandBioenergy(gdx, detail = detail, level = level)"
```
(getReport() tryList block is L62–182, function L56–235 per `magpie4_reference.md`.)

**IAMC variable names produced** (from `@section` roxygen in `reportDemandBioenergy.R:22–26`):

| IAMC variable | Unit | Description |
|---|---|---|
| `Demand\|Bioenergy` | EJ/yr | Total bioenergy demand (summation parent) |
| `Demand\|Bioenergy\|++\|2nd generation` | EJ/yr | Dedicated crops (betr, begr) + residues |
| `Demand\|Bioenergy\|++\|1st generation` | EJ/yr | Oils + ethanol |
| `Demand\|Bioenergy\|++\|Traditional Burning` | EJ/yr | Traditional biomass from kres set |
| `Demand\|Bioenergy\|Overproduction` | EJ/yr | Surplus above the three main streams |
| `Demand\|Bioenergy\|Biochar` | EJ/yr | Biochar feedstock (conditional, if biochar module active) |

The `++` separator marks `summationhelper` stackplot grouping; `Demand|Bioenergy` is the sum of all `++` children.

---

## (b) Underlying GAMS variables and the module that defines them

### Primary GDX variable: `ov_dem_bioen`

The central GDX variable is **`ov_dem_bioen`** — the GDX output form (prefix `ov_`) of the GAMS interface variable **`vm_dem_bioen(i,kall)`**.

**GAMS declaration** (`module_60.md` → `modules/60_bioenergy/1st2ndgen_priced_feb24/declarations.gms:20`):
```gams
vm_dem_bioen(i,kall)   !! mio. tDM per yr
```
🟡 Documented in `module_60.md` (Interface Variables section, "Outputs to Other Modules").

**Defining module**: **Module 60 (Bioenergy)**, realization `1st2ndgen_priced_feb24`.  
This is the ONLY module that constrains and writes `vm_dem_bioen`. Module 16 (Demand) reads it as a downstream consumer.

**Additional GDX variables read by `reportDemandBioenergy` for sub-category decomposition** (all from Module 60):

| GDX variable | GAMS source | Description |
|---|---|---|
| `ov_dem_bioen` | `vm_dem_bioen(i,kall)`, `declarations.gms:20` | Total bioenergy demand in mass units (mio. tDM/yr) |
| `ov60_2ndgen_bioenergy_dem_residues` | `v60_2ndgen_bioenergy_dem_residues(i,kall)`, `declarations.gms` | 2nd gen residue demand (mio. GJ/yr in GAMS, read in mass-level from GDX) |
| `ov60_2ndgen_bioenergy_dem_dedicated` | `v60_2ndgen_bioenergy_dem_dedicated(i,kall)`, `declarations.gms` | 2nd gen dedicated crops demand (betr, begr) |
| `i60_1stgen_bioenergy_dem` | `i60_1stgen_bioenergy_dem(ct,i,kall)`, `presolve.gms:17–18` | 1st gen demand (mio. GJ/yr) — parameter, not variable |

The three sub-demand GDX reads are used to decompose the total `bioenergyDemand` into the sub-categories 1st gen / 2nd gen dedicated / 2nd gen residues / overflow (`reportDemandBioenergy.R:47–56`).

**Module 62 (Material)** does NOT contribute to any `Demand|Bioenergy` variable. Module 62 defines `vm_dem_material(i,kall)` (`module_62.md`, `declarations.gms:25`) for cosmetics, chemicals, textiles, and bioplastic substrate. These flow to `Demand|Non-Energy Crops|...` / `Demand|Material|...` IAMC variables via `reportDemand`, not to `Demand|Bioenergy`.

---

## (c) Aggregation and units conversion applied by magpie4

The conversion chain is two-step, both applied in magpie4 R code:

### Step 1 — Mass × energy-content attribute → PJ/yr, then ÷ 1000 → EJ/yr

In `demand.R:48`, the bioenergy slice is extracted from GDX in dry matter (mio. tDM/yr):
```r
bioenergy <- readGDX(gdx, "ov_dem_bioen", select = list(type = "level"))
```
In `demand.R:121–123`, the caller passes `attributes = "ge"`, which triggers multiplication by `fm_attributes[,,"ge"]` (GJ/tDM), converting to mio. GJ/yr = PJ/yr:
```r
att <- readGDX(gdx, "fm_attributes")[, , products][, , attributes]
out <- out * att
```
In `reportDemandBioenergy.R:47`, the result is divided by 1000 to reach EJ/yr:
```r
bioenergyDemand <- collapseNames(demand(gdx, level = "regglo", attributes = "ge")[, , "bioenergy"]) / 1000
```
The same `/1000` is applied to the three sub-category reads at lines 50, 53, 54.

### Step 2 — Spatial aggregation to "regglo"

`superAggregateX(..., aggr_type = "sum", level = "regglo")` sums the 200-cluster or regional dimension to both individual MAgPIE regions AND a global total in one object. The GAMS `vm_dem_bioen` is dimensioned over regions `i` (10–15 regions in default config).

### Summation helper

`summationhelper(round(out, 8), sep = "++")` (`reportDemandBioenergy.R:101`) constructs the parent `Demand|Bioenergy` variable as the arithmetic sum of the `++`-tagged children. No weights or further conversions are applied at this stage.

### Summary of the full unit chain

```
vm_dem_bioen(i,kall)                    [mio. tDM/yr, GAMS Module 60]
  → ov_dem_bioen in fulldata.gdx
  → readGDX(gdx, "ov_dem_bioen")        [mio. tDM/yr]
  × fm_attributes("ge", kall)           [GJ/tDM]
  = demand(..., attributes="ge")        [mio. GJ/yr = PJ/yr]
  / 1000
  = EJ/yr
  + summationhelper("++")
  → report.mif: "Demand|Bioenergy (EJ/yr)"
```

---

## Source citations

| Claim | Source | Tag |
|---|---|---|
| `reportDemandBioenergy` is in getReport | `.cache/sources/magpie4/R/getReport.R:79` | 🟢 |
| IAMC variable names and units | `.cache/sources/magpie4/R/reportDemandBioenergy.R:22–26, 87–102` | 🟢 |
| `ov_dem_bioen` read in `demand.R` | `.cache/sources/magpie4/R/demand.R:48` | 🟢 |
| `fm_attributes` multiplication | `.cache/sources/magpie4/R/demand.R:121–123` | 🟢 |
| `/1000` conversion to EJ | `.cache/sources/magpie4/R/reportDemandBioenergy.R:47, 50, 53, 54` | 🟢 |
| Sub-category GDX reads | `.cache/sources/magpie4/R/reportDemandBioenergy.R:48–54` | 🟢 |
| `vm_dem_bioen` GAMS declaration | `module_60.md` (Interface Variables) → `declarations.gms:20` | 🟡 |
| Module 60 as defining module | `module_60.md` (Core Function + Interface Variables) | 🟡 |
| Module 62 does NOT contribute | `module_62.md` (Executive Summary, `vm_dem_material`) | 🟡 |
| Version pin | `project/version_pins.json` | 🟢 |

---

## What the docs leave unclear

1. **`fm_attributes("ge", kall)` values**: The gross energy content coefficients are read from GDX as a shared parameter, not declared in Module 60's own declarations. The exact numeric values per commodity (GJ/tDM for betr, begr, oils, ethanol, kres) are in the input data but not in the module docs or magpie4 docs. A modeler wanting the exact GJ/tDM factors needs to read `fm_attributes` from a run's GDX or from the preprocessing pipeline.

2. **`Demand|Bioenergy|Traditional Burning` provenance**: The `bioenergyTra` slice in `reportDemandBioenergy.R:60–62` is constructed from `bioenergy1stTra[,, kres]` — i.e., it re-uses the `i60_1stgen_bioenergy_dem` parameter filtered to `kres` (residue) commodities. This interpretation (residues in the 1st-gen parameter treated as "traditional burning") is readable in the code but is not explained in the module docs or the magpie4_reference helper, and the naming is potentially confusing.

3. **Biochar branch**: The conditional `if (!is.null(bioenergyBiochar))` path (`reportDemandBioenergy.R:67–84`) reallocates a fraction of bioenergy demand into a `Demand|Bioenergy|Biochar` sub-variable. This branch depends on whether the biochar module is active. Neither the module_60 docs nor the magpie4_reference helper document this sub-variable or the reallocation logic.
