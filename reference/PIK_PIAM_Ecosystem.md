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
| `gms` | GAMS/R interface — read/write GDX, manage GAMS runs from R | https://github.com/pik-piam/gms |
| `lucode2` | Run management, config handling, job submission | https://github.com/pik-piam/lucode2 |
| `magclass` | Core array class for spatio-temporal model data | https://github.com/pik-piam/magclass |
| `gdx2` | GDX file I/O bridge between GAMS and R | https://github.com/pik-piam/gdx2 |
| `goxygen` | GAMS code documentation generation | https://github.com/pik-piam/goxygen |

## Output & reporting

| Package | Role | GitHub |
|---------|------|--------|
| `magpie4` | MAgPIE output reporting — reads GDX, produces `.mif` | https://github.com/pik-piam/magpie4 |
| `mip` | Model intercomparison plots | https://github.com/pik-piam/mip |
| `piamInterfaces` | Variable mapping / IIASA template handling | https://github.com/pik-piam/piamInterfaces |
| `lusweave` | PDF report generation | https://github.com/pik-piam/lusweave |
| `luplot` | Plotting utilities | https://github.com/pik-piam/luplot |
| `trafficlight` | Validation traffic-light reporting | https://github.com/pik-piam/trafficlight |
| `m4fsdp` | Food systems / sustainable development reporting | https://github.com/pik-piam/m4fsdp |

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
| `luscale` | Scaling/aggregation helpers | https://github.com/pik-piam/luscale |
| `GDPuc` | GDP unit conversion | https://github.com/pik-piam/GDPuc |
| `piamutils` | Shared utilities across piam packages | https://github.com/pik-piam/piamutils |
| `piamenv` | R+conda environment reproducibility: checks/fixes R package deps (`checkDeps`, `fixDeps`), creates the `renv/archive/<version>_renv.lock` snapshots (`archiveRenv`), manages safe updates (`updateRenv` + `stopIfLoaded` to prevent lazy-load crashes), and initialises conda for external tool calls | https://github.com/pik-piam/piamenv |
| `mstools` | Model statistics tools | https://github.com/pik-piam/mstools |
| `lpjclass` | LPJmL data class (for land surface model coupling) | https://github.com/pik-piam/lpjclass |
| `blackmagicc` | MAGICC climate model interface | https://github.com/pik-piam/blackmagicc |
| `modelstats` | Run statistics collection | https://github.com/pik-piam/modelstats |
| `gdxdt` | GDX to data.table helpers | https://github.com/pik-piam/gdxdt |
| `citation` | Citation management | https://github.com/pik-piam/citation |

---

## Debugging notes

- **`madrat` cache errors** are among the most common input-side failures. Cache path is set by `madrat::setConfig(cachePath=...)`. Check the cache before assuming a code bug.
- **`magpie4` failures** usually mean the GDX output from the GAMS solve is malformed or missing — confirm GAMS completed successfully before debugging the R reporting layer.
- **`gms` version mismatches** between `renv/library/` and a run's `output/<run>/renv.lock` are a recurring source of subtle failures. Always check which renv the run actually used.
- The 111 total pik-piam packages include many `mr*` data retrieval wrappers that rarely cause bugs. Focus debugging effort on `magpie4`, `madrat`, `gms`, and `lucode2` first.
