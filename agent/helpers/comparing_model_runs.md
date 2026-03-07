# Helper: Comparing MAgPIE Model Runs

**Auto-load triggers**: "compare runs", "compare scenarios", "model comparison", "output comparison", "multiple runs", "scenario comparison", "diff runs"
**Last updated**: 2025-07-18
**Lessons count**: 0 entries

---

## Quick Reference

MAgPIE stores each run in a separate folder under `output/`. The folder name follows the pattern `<title>_<YYYY-MM-DD_HH.MM.SS>` (configured via `cfg$results_folder` in `config/default.cfg:2298`, which defaults to `"output/:title::date:"`). The run title comes from `cfg$title` (`config/default.cfg:17`, default: `"default"`).

**Key files per run:**

| File | Purpose |
|------|---------|
| `fulldata.gdx` | Complete model state — all variables, parameters, sets |
| `report.mif` | IAMC-format report: hundreds of variables, regional + global |
| `report.rds` | Same as report.mif as R quitte object |
| `config.yml` | Full run configuration (load with `gms::loadConfig()`) |
| `full.log` | GAMS listing/log output |
| `validation.mif` | Historical validation data |
| `cell.land_0.5.mz` | Disaggregated land pools at 0.5° grid |
| `magpie_y<year>.gdx` | Per-timestep solver savepoints |

**Comparison scripts** (marked `comparison script: TRUE` in their YAML header) receive all selected output directories at once, whereas single-run scripts are called once per directory. The `output.R` framework handles this automatically (`output.R:94-98`).

---

## Step-by-Step Comparison Workflow

### Step 1: Identify Runs to Compare

List available runs:
```bash
ls -d output/*/
```

Each folder contains `config.yml` with the full configuration. To quickly compare configs:
```r
library(gms)
cfg1 <- loadConfig("output/run1_2025-01-01_12.00.00/config.yml")
cfg2 <- loadConfig("output/run2_2025-01-01_13.00.00/config.yml")

# Compare specific settings
cfg1$gms$s56_cprice_red_factor  # carbon price setting in run 1
cfg2$gms$s56_cprice_red_factor  # carbon price setting in run 2
```

**Tip**: `config.yml` stores the exact `cfg$gms` switches used, so you can always reconstruct what differed between runs.

### Step 2: Using output.R for Comparison

`output.R` is the central entry point for all post-processing. It can run in interactive mode (prompts you to select runs and scripts) or via command-line arguments.

**Interactive mode** — select runs and scripts from menus:
```bash
Rscript output.R
```

**Command-line mode** — specify runs and scripts directly:
```bash
# Merge reports from multiple runs into one file
Rscript output.R output=merge_report outputdir=output/run1,output/run2

# Generate side-by-side validation PDF
Rscript output.R output=comparison_validation outputdir=output/run1,output/run2

# Compare model status across runs
Rscript output.R output=extra/modelstat outputdir=output/run1,output/run2

# Compare runtimes across runs
Rscript output.R output=extra/runtime outputdir=output/run1,output/run2
```

**Submission modes** (the `submit` argument):
- `direct` — run immediately in the current R session
- `background` — run as a background R process
- SLURM modes available on HPC (configured in `scripts/slurmOutput.yml`)

### Step 3: Built-in Comparison Scripts

**Main comparison scripts** (`scripts/output/`):

| Script | What It Does |
|--------|-------------|
| `merge_report.R` | Merges `report.rds` from multiple runs into `output/report_all.rds` and `output/report_all.mif`. Uses `magclass::write.mif()` and `quitte` format. |
| `comparison_validation.R` | Generates a side-by-side validation PDF using `mip::validationpdf()` with `style="comparison"`. Reads each run's `fulldata.gdx` via `magpie4::getReport()` and binds them together. |

**Extra comparison scripts** (`scripts/output/extra/`):

| Script | What It Does |
|--------|-------------|
| `extra/modelstat.R` | Compares solver status (`modelstat`) across runs. Writes `output/modelstat_<project>.csv`. Warns if any timestep has modelstat ≠ 2. |
| `extra/runtime.R` | Compares solve times across runs using `lucode2::readRuntime()` with plot output. |
| `extra/runtimePR.R` | Runtime comparison formatted for pull request reviews. |
| `extra/aff_area.R` | Extracts afforestation area from multiple runs (useful template for custom variable extraction). |
| `extra/ForestChangeCluster.R` | Compares forest change at cluster level across runs. |
| `extra/resubmit.R` | Re-submits failed runs (operational, not analytical). |

### Step 4: Programmatic Comparison in R

**Using merged report data:**
```r
library(magclass)
library(quitte)
library(mip)

# After running merge_report.R:
all_runs <- readRDS("output/report_all.rds")  # quitte data frame

# Filter by variable and scenario
library(dplyr)
all_runs %>%
  filter(variable == "Land Cover (million ha)",
         region == "World") %>%
  ggplot(aes(x = period, y = value, color = scenario)) +
  geom_line()
```

**Direct GDX comparison using magpie4:**
```r
library(magpie4)
library(magclass)

gdx1 <- "output/run1/fulldata.gdx"
gdx2 <- "output/run2/fulldata.gdx"

# Compare land use
land1 <- land(gdx1, level = "glo")
land2 <- land(gdx2, level = "glo")
diff_land <- land2 - land1  # magclass supports arithmetic

# Compare costs
costs1 <- costs(gdx1, level = "glo")
costs2 <- costs(gdx2, level = "glo")

# Compare emissions
emis1 <- emissions(gdx1, level = "glo")
emis2 <- emissions(gdx2, level = "glo")

# Compare food demand
demand1 <- demand(gdx1, level = "reg")
demand2 <- demand(gdx2, level = "reg")

# Compare model status
ms1 <- modelstat(gdx1)
ms2 <- modelstat(gdx2)
```

**Using mip for comparison plots:**
```r
library(mip)

# Read reports as magclass objects
rep1 <- magclass::read.report("output/run1/report.mif")
rep2 <- magclass::read.report("output/run2/report.mif")
combined <- mbind(rep1, rep2)

# Generate comparison validation PDF
validationpdf(x = combined, hist = "input/validation.mif",
              file = "my_comparison.pdf", style = "comparison")
```

### Step 5: Visual Comparison Approaches

**Option A: Validation PDFs** (quickest)
```bash
Rscript output.R output=comparison_validation outputdir=output/run1,output/run2
```
Produces a PDF with side-by-side plots against historical data for all standard reporting variables.

**Option B: Custom R plots with ggplot2**
```r
library(quitte)
library(ggplot2)

q1 <- readRDS("output/run1/report.rds")
q2 <- readRDS("output/run2/report.rds")
combined <- rbind(q1, q2)

combined %>%
  filter(grepl("Land Cover\\|Cropland", variable),
         region != "World") %>%
  ggplot(aes(x = period, y = value, color = scenario)) +
  geom_line() +
  facet_wrap(~region) +
  labs(title = "Cropland by Region", y = "million ha")
```

**Option C: Spatial comparison (0.5° grid)**
```r
library(magclass)

land1 <- read.magpie("output/run1/cell.land_0.5.mz")
land2 <- read.magpie("output/run2/cell.land_0.5.mz")
diff <- land2 - land1  # Spatial difference map

# Use luplot for map visualization
library(luplot)
```

---

## Key Variables to Compare

### Land Use
| report.mif Variable | magpie4 Function | Unit |
|---------------------|-----------------|------|
| `Land Cover|Cropland` | `land(gdx, level="glo")` | million ha |
| `Land Cover|Forest` | `land(gdx, level="glo")` | million ha |
| `Land Cover|Pastures and Rangelands` | `land(gdx, level="glo")` | million ha |
| `Land Cover|Other Land` | `land(gdx, level="glo")` | million ha |
| Crop-specific areas | `croparea(gdx, level="reg")` | million ha |

### Emissions
| report.mif Variable | magpie4 Function | Unit |
|---------------------|-----------------|------|
| `Emissions|CO2|Land` | `emissions(gdx)` | Mt CO2/yr |
| `Emissions|CH4|Land` | `emissions(gdx)` | Mt CH4/yr |
| `Emissions|N2O|Land` | `emissions(gdx)` | Mt N2O/yr |

### Food & Agriculture
| report.mif Variable | magpie4 Function | Unit |
|---------------------|-----------------|------|
| Food demand | `demand(gdx, level="reg")` | million tDM |
| Agricultural production | `production(gdx, level="reg")` | million tDM |
| Per-capita calories | `Kcal(gdx, level="reg")` | kcal/cap/day |

### Costs
| report.mif Variable | magpie4 Function | Unit |
|---------------------|-----------------|------|
| Total costs | `costs(gdx, level="glo")` | million USD17MER/yr |

### Trade
Trade variables are available in the report.mif under `Trade|` prefixed variables. Use `read.report()` and filter for trade-related entries.

---

## Common Pitfalls

1. **Different timestep configurations**: Runs with different `cfg$gms$c_timesteps` settings will have outputs at different years. Arithmetic operations on mismatched timestep magclass objects will fail or produce misleading results. Always check `getYears()` on both objects before comparing.

2. **Regional aggregation mismatches**: If runs use different regional mappings (e.g., H12 vs H16), region names and counts differ. The `clustermap_*.rds` file in each output folder documents the spatial mapping used. Merge at the global (`"glo"`) level for safe comparison, or re-aggregate to a common mapping.

3. **Comparing runs with different base years**: If `cfg$gms$c_past` or input data vintages differ, the calibration baseline changes, making absolute comparisons misleading. Compare *differences from baseline* or percentage changes instead of absolute values.

4. **GDX variable naming**: Output parameters use `ov_` prefix (variables) and `oq_` prefix (equations). Raw GAMS variables use `vm_` (global), `v_` (local). In `fulldata.gdx`, `ov_*` parameters have all timesteps (via `t` dimension), but `vm_*` variables only have the last timestep's values.

5. **Unit consistency**: All production is in dry matter (`million tDM`), NOT fresh weight. Costs are `million USD17MER/yr` (2017 market exchange rate). Land is `million ha`. Carbon stocks are `million tC`. Confusing units across different data sources is a common error.

6. **report.mif scenario names**: Each run's report uses `cfg$title` as the scenario name. If two runs have the same title, `merge_report.R` will concatenate them but `comparison_validation.R` auto-deduplicates via `make.unique()` (`comparison_validation.R:37-39`). Set distinct `cfg$title` values before running to avoid confusion.

7. **Missing report files**: `merge_report.R` silently skips folders lacking `report.rds` and lists them at the end. If a run didn't execute `rds_report` as an output script, generate it first: `Rscript output.R output=rds_report outputdir=output/my_run`.

8. **Stale fulldata.gdx after re-runs**: `fulldata.gdx` is overwritten each timestep during a run (`core/calculations.gms:92`). If a run was interrupted and restarted, ensure the GDX reflects the complete run, not a partial one. Check `modelstat(gdx)` for all expected timesteps.

---

## Related Helpers & Docs

- **Interpreting outputs** → `interpreting_outputs.md` (understanding individual run results)
- **Debugging infeasibilities** → `debugging_infeasibility.md` (when compared runs fail)
- **Scenario setup** → `scenario_carbon_pricing.md`, `scenario_diet_change.md`
- **Land balance conservation** → `cross_module/land_balance_conservation.md`
- **Output scripts index** → `scripts/output/INFO.yml`

---

## Lessons Learned
<!-- APPEND-ONLY -->
