# P5 Answer: Tracing a Key Input Dataset from File Format through GAMS into the Model

## Question

Trace how a key input dataset enters MAgPIE: pick the land-use initialisation input (or the yield input) and follow it from the input file format (.cs2 / .cs3 / .mz) through the GAMS reading mechanism into the set or parameter the model actually uses, and name the first module or execution phase that consumes it. What file types and parameter names are involved, and what is the upstream data source?

---

## Answer: Land-Use Initialisation Input (Module 10)

I trace the land-use initialisation path, which is documented across two authoritative sources: `core_docs/Data_Flow.md` and `modules/module_10.md`.

### Step 1: Upstream Data Source

🟡 **Documented** — The land-use initialisation data originates from the **LUH2 (Land-Use Harmonization v2)** dataset. LUH2 provides gridded historical land-use categories at 0.5° spatial resolution.

Source: `core_docs/Data_Flow.md` §1.2 ("Land Use (LUH2)"); `modules/module_10.md` §4 ("File 1: Historical Land Area").

### Step 2: Input File Format and Path

🟡 **Documented** — The LUH2 data enters MAgPIE as a `.cs3` file — the 3D GAMS data format (time × region × category):

```
modules/10_land/input/avl_land_t.cs3
```

The `.cs3` format is used for 3D tabular GAMS data. In this case the three dimensions are:
- `t_ini10` — historical time periods (1995, 2000, 2005, 2010, 2015)
- `j` — the ~200 MAgPIE simulation clusters
- `land` — the 7 land types (crop, past, forestry, primforest, secdforest, urban, other)

Source: `core_docs/Data_Flow.md` §1.1 (file format table, `.cs3` = "3D GAMS data (time×region×category)"); `modules/module_10.md` §4 ("File 1").

A second related `.cs3` file provides LUH2 side layers (managed pasture fraction, rangeland fraction, primary vegetation fraction, etc.):

```
modules/10_land/input/luh2_side_layers.cs3
```

Source: `modules/module_10.md` §4 ("File 2: LUH2 Side Layers").

### Step 3: GAMS Reading Mechanism

🟡 **Documented** — The file is read into a raw file parameter using the standard MAgPIE `$include` + `$ondelim`/`$offdelim` pattern in `input.gms`:

```gams
table f10_land(t_ini10,j,land) Different land type areas (mio. ha)
$include "./modules/10_land/input/avl_land_t.cs3"
```

The `f_` prefix marks this as a **file parameter** — raw data as read from a file, module-internal scope. This is the first GAMS parameter the data lands in.

Source: `modules/module_10.md` §4 ("File 1: Historical Land Area", `input.gms:8-11`); `core_docs/Data_Flow.md` §2.1 (parameter prefix table: "`f_` = Raw data as read from files").

A correction for negative values is applied immediately after loading:

```
input.gms:16  # Negative values (from rounding) set to zero
```

Source: `modules/module_10.md` §4.

### Step 4: Transformation to Usable Parameters

🟡 **Documented** — After loading, `f10_land` is projected into two derived parameters:

1. **`pm_land_start(j,land)`** — Initial land area at 1995 (mio. ha)
   - Populated from `f10_land("y1995",j,land)`
   - Used in `start.gms:8` to initialise the model state
   - `pm_` prefix = "processing module parameter" — cross-module, shared

2. **`pm_land_hist(t_ini10,j,land)`** — Historical land area 1995–2015 (mio. ha)
   - Populated from `f10_land(t_ini10,j,land)` for calibration and validation
   - `pm_` prefix = cross-module shared parameter

3. **`pcm_land(j,land)`** — Previous timestep land area (mio. ha)
   - Initialised from `pm_land_start` and updated in `postsolve.gms:9` after each timestep
   - `pcm_` prefix = previous-timestep cross-module shared parameter
   - This is the dynamic "current state" parameter used inside Module 10's land conservation constraint

Source: `modules/module_10.md` §3 ("Parameters", `declarations.gms:8-12` and `start.gms:8`).

### Step 5: Spatial Aggregation

🟡 **Documented** — LUH2 raw data is at 0.5° grid resolution (~67,420 land cells globally). Before entering GAMS, the R preprocessing pipeline (mrmagpie / madrat) aggregates from the 67,420-cell grid to the ~200 MAgPIE simulation clusters. The mapping is stored in `cell(i,j)` which links clusters to regions.

Source: `core_docs/Data_Flow.md` §4.1 ("Spatial Resolution Cascade"); §3.1 ("Spatial Aggregation: 67,420 grid cells (0.5°) → 200 simulation clusters (j)").

### Step 6: First Module and Execution Phase to Consume It

🟡 **Documented** — The first consumption occurs in **Phase 1: Preprocessing, Start sub-phase** (`start.gms:8`), where `pm_land_start` is set from `f10_land("y1995",...)`. This is the `$batinclude "./modules/include.gms" start` call inside `/core/calculations.gms`.

The first **optimization-phase** consumer is Module 10 itself via the land conservation constraint `q10_land_area`, which compares the new `vm_land(j,land)` against `pcm_land(j,land)` (ultimately initialised from the LUH2 input).

Downstream, `pm_land_start` is shared to 4 other modules immediately:
- Module 32 (Forestry) — plantation initialisation
- Module 14 (Yields) — pasture-yield aggregation
- Module 71 (Livestock disaggregation) — livestock spatial allocation
- Module 59 (Soil organic matter) — soil carbon initialisation

Source: `modules/module_10.md` §5 ("PROVIDES TO" table); `core_docs/Data_Flow.md` §3.1 ("Execution Order", steps 3–4).

---

## Summary Table

| Step | What | Name | Format / Prefix |
|------|------|------|-----------------|
| Upstream source | LUH2 gridded historical land use | LUH2 v2 | 0.5° raster |
| Input file | Historical land areas 1995–2015 | `avl_land_t.cs3` | `.cs3` (3D) |
| Raw GAMS parameter | Read via `$include` in `input.gms:8-11` | `f10_land(t_ini10,j,land)` | `f_` file parameter |
| Cross-module parameter (static) | 1995 initialisation value | `pm_land_start(j,land)` | `pm_` cross-module |
| Cross-module parameter (historical) | 1995–2015 calibration values | `pm_land_hist(t_ini10,j,land)` | `pm_` cross-module |
| Dynamic state parameter | Previous-timestep land area | `pcm_land(j,land)` | `pcm_` previous cross-module |
| First phase to consume | Phase 1 Start sub-phase | `start.gms:8` | Preprocessing |
| First equation to use | Land conservation constraint | `q10_land_area` | Module 10 `equations.gms:13-15` |

---

## Yield Input Parallel (for completeness)

The yield input follows the same pattern but using a `.cs3` file from LPJmL rather than LUH2:

- Input file: `modules/14_yields/input/lpj_yields.cs3`
- Raw parameter: `f14_yields(t_all,j,kve,w)` — loaded via `$include` in Module 14 `input.gms`
- Calibrated parameter: `i14_yields_calib(t,j,kve,w)` — derived in `preloop.gms` after FAO calibration
- First optimization consumer: Module 14 yield constraint `q14_yield_crop` (equations.gms)
- This flow is documented in `core_docs/Data_Flow.md` §2.3 with full GAMS code excerpt

Source: `core_docs/Data_Flow.md` §2.3 ("Data Loading Example - Yield Module (14)").

---

## Sources

- 🟡 `core_docs/Data_Flow.md` §1.1, §1.2, §2.1, §2.3, §3.1, §4.1, §5.1
- 🟡 `modules/module_10.md` §3, §4, §5 (`declarations.gms:8-12`, `input.gms:8-11`, `input.gms:16`, `input.gms:19-23`, `start.gms:8`, `postsolve.gms:9`, `equations.gms:13-15`)
