# PIK-PIAM Package Reference

The [PIK-PIAM organization](https://github.com/orgs/pik-piam/repositories) maintains ~111 R packages
used across PIK land-use and energy models. MAgPIE uses 34 of them (verified against
`renv/archive/4.13.0_renv.lock`).

**renv layout (non-standard — read carefully before advising on package issues):**
- There is **no `renv.lock` in the repo root**. The main library lives at `renv/library/` without a root lockfile.
- Lockfile snapshots are archived at `renv/archive/<version>_renv.lock`.
- Each run snapshots its own lockfile into `output/<run>/renv.lock` at submission time, then calls `renv::restore()`.
- To inspect what a specific run actually loaded: check `output/<run>/renv.lock` — not the main library.
- To open R with a run's environment: `renv::activate("<run_folder>")` or cd into the run folder (`.Rprofile` auto-activates).

**When a traceback bottoms out in a pik-piam package:**
1. Ask the user to paste the function source: `getAnywhere(<function>)` or `https://github.com/pik-piam/<package>/blob/main/R/<function>.R`
2. Check the package GitHub Issues and Releases for the installed version
3. Check whether the version in `renv/archive/<version>_renv.lock` is current — a newer version may have the fix
4. Do **not** suggest cloning these repos locally — reference GitHub URLs only

---

## Core model interface

| Package | Role | GitHub |
|---------|------|--------|
| `gms` | GAMS modularization toolkit — provides the module/realization code structure and naming conventions that MAgPIE and REMIND are built on; monitors compliance with modular coding guidelines | https://github.com/pik-piam/gms |
| `lucode2` | Run management, config handling, job submission | https://github.com/pik-piam/lucode2 |
| `magclass` | Array class for spatio-temporal model data with name-based dimension addressing and automatic consistency checks | https://github.com/pik-piam/magclass |
| `gdx2` | Read GDX files into R via gamstransfer; the standard bridge between GAMS solve output and the R reporting pipeline | https://github.com/pik-piam/gdx2 |

## Output & reporting

| Package | Role | GitHub |
|---------|------|--------|
| `magpie4` | MAgPIE output reporting — reads GDX, produces `.mif` | https://github.com/pik-piam/magpie4 |
| `mip` | Model intercomparison plots | https://github.com/pik-piam/mip |
| `piamInterfaces` | Interfaces for REMIND and MAgPIE output — maps model variables to project templates for IIASA database submission; includes summation checks and model intercomparison support | https://github.com/pik-piam/piamInterfaces |
| `lusweave` | PDF report generation | https://github.com/pik-piam/lusweave |
| `luplot` | Spatial and time-series plot functions for MAgPIE objects, including map plots for land-use data | https://github.com/pik-piam/luplot |
| `trafficlight` | Data validation and aggregation of validation results into traffic-light summaries | https://github.com/pik-piam/trafficlight |
| `m4fsdp` | MAgPIE output routines for the Food Systems Demonstrated Pathways (FSDP) project | https://github.com/pik-piam/m4fsdp |

## Input data (madrat framework)

| Package | Role | GitHub |
|---------|------|--------|
| `madrat` | Data preprocessing framework — cacheable, reproducible input data pipeline | https://github.com/pik-piam/madrat |
| `mrland` | Land-use input data retrieval | https://github.com/pik-piam/mrland |
| `mrlandcore` | Core land data shared across mr* packages | https://github.com/pik-piam/mrlandcore |
| `mrmagpie` | MAgPIE-specific input data | https://github.com/pik-piam/mrmagpie |
| `mrcommons` | Shared data sources (FAO, FAOSTAT, etc.) | https://github.com/pik-piam/mrcommons |
| `mrfaocore` | FAO core data | https://github.com/pik-piam/mrfaocore |
| `mrwater` | Water input data | https://github.com/pik-piam/mrwater |
| `mrsoil` | Soil data | https://github.com/pik-piam/mrsoil |
| `mrvalidation` | Validation data sources | https://github.com/pik-piam/mrvalidation |
| `mrdrivers` | Socioeconomic drivers (population, GDP) | https://github.com/pik-piam/mrdrivers |
| `mrfactors` | Factor cost data | https://github.com/pik-piam/mrfactors |
| `mrdownscale` | Spatial downscaling of input data | https://github.com/pik-piam/mrdownscale |

## Utilities

| Package | Role | GitHub |
|---------|------|--------|
| `magpiesets` | Regional/sectoral set definitions | https://github.com/pik-piam/magpiesets |
| `quitte` | Tidy data helpers for IAM scenario data | https://github.com/pik-piam/quitte |
| `luscale` | Aggregation and disaggregation of spatial/sectoral data | https://github.com/pik-piam/luscale |
| `GDPuc` | GDP unit conversion | https://github.com/pik-piam/GDPuc |
| `piamutils` | Shared utilities across piam packages | https://github.com/pik-piam/piamutils |
| `piamenv` | R+conda environment reproducibility: checks/fixes R package deps (`checkDeps`, `fixDeps`), creates the `renv/archive/<version>_renv.lock` snapshots (`archiveRenv`), manages safe updates (`updateRenv` + `stopIfLoaded` to prevent lazy-load crashes), and initialises conda for external tool calls | https://github.com/pik-piam/piamenv |
| `mstools` | Shared helper functions for `madrat` and `magpie4` output routines | https://github.com/pik-piam/mstools |
| `modelstats` | Tools for analyzing and monitoring model run performance | https://github.com/pik-piam/modelstats |
| `goxygen` | Extracts model documentation from GAMS code comments — dev tool, not part of the runtime | https://github.com/pik-piam/goxygen |
| `citation` | Extracts and formats citation metadata from R packages (CFF format) | https://github.com/pik-piam/citation |

## Model coupling

| Package | Role | GitHub |
|---------|------|--------|
| `lpjclass` | Data class for LPJmL land surface model output, used when coupling MAgPIE with LPJmL | https://github.com/pik-piam/lpjclass |
| `blackmagicc` | Runs MAGICC climate projections from MAgPIE using REMIND reference scenarios for energy-sector emissions | https://github.com/pik-piam/blackmagicc |

---

## Debugging notes

- **`madrat` cache errors** are among the most common input-side failures. Cache path is set by `madrat::setConfig(cachePath=...)`. Check the cache before assuming a code bug.
- **`magpie4` failures** usually mean the GDX output from the GAMS solve is malformed or missing — confirm GAMS completed successfully before debugging the R reporting layer.
- **`gms` version mismatches** between `renv/library/` and a run's `output/<run>/renv.lock` are a recurring source of subtle failures. Always check which renv the run actually used.
- The 111 total pik-piam packages include many `mr*` data retrieval wrappers that rarely cause bugs. Focus debugging effort on `magpie4`, `madrat`, `gms`, and `lucode2` first.
