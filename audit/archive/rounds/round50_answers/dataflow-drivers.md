# Driver Input Trace: Population/GDP from Module 09 through to First Consumer

**Question**: Trace a driver input (population or GDP) from its input file format through the GAMS reading mechanism into the parameter the model uses, and name the first module/phase that consumes it. Verify the doc's description of the overall input-pipeline stages. Flag any mislabeled or stale data source.

---

## 1. Complete Trace: Population (`f09_pop_iso`) from raw file to consumer

### 1.1 Input File Format

The raw driver data for population arrives as a `.csv` file.

- **File**: `modules/09_drivers/input/f09_pop_iso.csv`
- **Format**: `.csv` (standard comma-separated values)
- **Dimensions**: `(t_all, iso, pop_gdp_scen09)` — time x 249 ISO countries x scenario
- **Units**: mio. capita per yr
- **Time horizon**: 1965–2150 (historical + projections)

Source: `core_docs/Data_Flow.md` §1.1 (file format table), §1.2 (Socioeconomic Projections); `modules/module_09.md` §4.1.

The overall `.csv` format for drivers contrasts with biophysical inputs which arrive as `.cs3` (3D GAMS data), `.cs4` (4D), or `.mz` (binary compressed spatial grids). Of the ~172 input files, 76 are `.csv`; the population and GDP files are among these. (`Data_Flow.md` §1.1)

### 1.2 GAMS Reading Mechanism

Module 09 loads the file via a standard GAMS `$include` / `$ondelim` pattern into a raw file parameter with the `f09_` prefix (denoting: raw data as read from file, module-internal, per the naming convention table at `Data_Flow.md` §2.1).

From `module_09.md` §4.1, the GAMS declaration is:
```gams
* Located at input.gms:36-38
* Declared as:
f09_pop_iso(t_all, iso, pop_gdp_scen09)
```

This is the `f_` prefix type: "File parameters — Raw data as read from files, module-internal" (`Data_Flow.md` §2.1).

GDP PPP arrives analogously at `input.gms:26-28` as `f09_gdp_ppp_iso(t_all, iso, pop_gdp_scen09)`.

### 1.3 Intermediate Processing in preloop.gms (one-time, per simulation)

After loading, Module 09's `preloop.gms` transforms the raw file parameters into intermediate internal parameters (`i09_` prefix = input parameters, processed, module-internal), then population-aggregates ISO countries to MAgPIE regions, and computes per-capita GDP.

The key steps (all in `preloop.gms`, citations from `module_09.md` §7):

**Step 1 — Regional aggregation (preloop.gms:9-11):**
```gams
i09_pop_raw(t_all,i,pop_gdp_scen09) = sum(i_to_iso(i,iso), f09_pop_iso(t_all,iso,pop_gdp_scen09));
```
ISO countries are summed into the 12 MAgPIE regions via the mapping set `i_to_iso`.

**Step 2 — GDP PPP per capita at ISO level (preloop.gms:23-27):**
```gams
i09_gdp_pc_ppp_iso_raw(t_all,iso,pop_gdp_scen09) =
  f09_gdp_ppp_iso(t_all,iso,pop_gdp_scen09) / f09_pop_iso(t_all,iso,pop_gdp_scen09);
* Missing data filled with SSP2 regional average
i09_gdp_pc_ppp_iso_raw(t_all,iso,pop_gdp_scen09)$(i09_gdp_pc_ppp_iso_raw(t_all,iso,pop_gdp_scen09) = 0)
  = sum(i_to_iso(i,iso), i09_gdp_pc_ppp_raw(t_all,i,"SSP2"));
```

**Step 3 — Scenario selection and SSP2 baseline lock (preloop.gms:36-56):**

The `im_` interface module parameters (cross-module shared, `Data_Flow.md` §2.1) are assigned from the scenario-selected slice. Before 2025 all scenarios use SSP2; after 2025 the selected scenario takes effect:
```gams
* Before sm_fix_SSP2 (= 2025):
im_pop_iso(t_all,iso) = f09_pop_iso(t_all,iso,"SSP2");
im_pop(t_all,i)       = i09_pop_raw(t_all,i,"SSP2");
im_gdp_pc_ppp_iso(t_all,iso) = i09_gdp_pc_ppp_iso_raw(t_all,iso,"SSP2");
...
* After 2025:
im_pop_iso(t_all,iso) = f09_pop_iso(t_all,iso,"%c09_pop_scenario%");
im_pop(t_all,i)       = i09_pop_raw(t_all,i,"%c09_pop_scenario%");
im_gdp_pc_ppp_iso(t_all,iso) = i09_gdp_pc_ppp_iso_raw(t_all,iso,"%c09_gdp_scenario%");
```

The final parameters exposed cross-module are:
- `im_pop_iso(t_all, iso)` — population by ISO country, mio. people/yr
- `im_pop(t_all, i)` — population by MAgPIE region, mio. people/yr
- `im_gdp_pc_ppp_iso(t_all, iso)` — GDP per capita PPP, USD17PPP/capita/yr
- `im_gdp_pc_mer_iso(t_all, iso)` — GDP per capita MER, USD17MER/capita/yr
- `im_gdp_pc_mer(t_all, i)` — GDP per capita MER, regional level
- (plus `im_development_state`, `im_demography`, `im_physical_inactivity`)

All of the above are populated in the **Preloop phase** (Phase 1 preprocessing, `Data_Flow.md` §3.1, step 5), which runs once per simulation before the time loop.

### 1.4 First Module/Phase That Consumes the Driver

All `im_*` interface assignments in Module 09 happen in `preloop.gms`. Consumers read these `im_` parameters during their own preloop or (for time-varying use) at presolve. The first structural consumer in the MAgPIE phase sequence is **Module 15 (food demand)**.

From `module_09.md` §5.2 and §12.2:
- `im_pop_iso` is used by **10 modules** (highest usage of any driver variable)
- **Module 15** receives `im_pop_iso`, `im_pop`, `im_gdp_pc_ppp_iso`, `im_gdp_pc_mer_iso`, `im_demography`, and `im_physical_inactivity` — the full set of population and income drivers
- Module 15's role: "Food demand = population x per capita consumption (income-elastic) x age/sex structure"

From `module_15.md` §1:
> "**Receives from**: Module 09 (Drivers) - population, GDP, demography"

Module 15 uses `im_pop(ct, i2)` directly in its food demand constraint `q15_food_demand` (`module_15.md` §2, `equations.gms:10-14`):
```gams
q15_food_demand(i2,kfo) ..
    (vm_dem_food(i2,kfo) + ...)
    * sum(ct,(fm_nutrition_attributes(ct,kfo,"kcal") * 10**6)) =g=
    sum(ct,im_pop(ct,i2) * p15_kcal_pc_calibrated(ct,i2,kfo)) * 365;
```

Module 15 is architecturally the first significant consumer: it runs as a standalone optimization model that feeds `vm_dem_food` (food demand) into the main MAgPIE optimization. It also consumes the driver variables earliest in the time-loop sequence — during the intersolve iteration — making it the effective first consumer.

**Summary of the full trace:**

```
f09_pop_iso.csv          (.csv, t_all x iso x pop_gdp_scen09)
    |
    | $include in input.gms:36-38
    v
f09_pop_iso(t_all,iso,pop_gdp_scen09)   [f_ prefix: raw file param, module-internal]
    |
    | preloop.gms:11 — sum over i_to_iso mapping
    v
i09_pop_raw(t_all,i,pop_gdp_scen09)    [i_ prefix: processed, module-internal]
    |
    | preloop.gms:40-50 — scenario selection (SSP2 until 2025, then c09_pop_scenario)
    v
im_pop_iso(t_all,iso)                   [im_ prefix: cross-module interface]
im_pop(t_all,i)                         [im_ prefix: cross-module interface]
    |
    | consumed first by Module 15 (food) in q15_food_demand
    v
vm_dem_food(i,kfo)  → feeds MAgPIE core optimization
```

---

## 2. Overall Input-Pipeline Stages: Verification

`Data_Flow.md` §3 describes 4 phases. Here is each stage with a verification status:

### Phase 1: Preprocessing — Once per simulation (`Data_Flow.md` §3.1)

Execution order:
1. **Sets Definition** (`/core/sets.gms`) — define all dimensions
2. **Declarations** (`modules/include.gms declarations`) — declare variables/parameters
3. **Input Loading** (`modules/include.gms input`) — load all data files via `$include`
4. **Start Phase** (`modules/include.gms start`) — initialize baseline
5. **Preloop** (`modules/include.gms preloop`) — one-time calibrations

Key transformations stated in the doc:
- Spatial aggregation: 67,420 grid cells (0.5°) → 200 simulation clusters (`j`)
- Temporal alignment: fill missing years, apply scenarios
- Calibration: align to historical observations (FAO yields, production)

These are consistent with the Module 09 preloop operations documented in `module_09.md` — the ISO→region aggregation and per-capita calculations all happen in Phase 1/preloop. **Verified internally consistent.**

### Phase 2: Time Loop — Per 5-year timestep (`Data_Flow.md` §3.2)

Loop sub-steps: `presolve_ini` → `presolve` → solve/intersolve (food demand coupling) → `postsolve`. The time loop structure shown (`loop(t$(m_year(t) > %TIMESTEP%),...`) includes `ct(t)` and `pt(t-1)` timestep tracking.

Module 09 drivers do not re-compute in the time loop — their `im_` parameters were fully populated in preloop. This is consistent with Module 09 being a "pure data provider" with no presolve or equations phase (`module_09.md` §1, §8 item 2).

### Phase 3A: Per-Timestep Preprocessing — presolve.gms (`Data_Flow.md` §3.3)

Dynamic updates shown (land bounds, forest age-class progression, carbon density, conservation bounds). Module 09 variables are not dynamic — they are static lookups from `im_*` parameters. **No contradiction; drivers are exogenous and time-indexed, not dynamically recomputed.**

### Phase 3B: Optimization (`Data_Flow.md` §3.4)

Model `magpie / all - m15_food_demand /` with objective `vm_cost_glo`. The exclusion of `m15_food_demand` from the main MAgPIE model (Module 15 runs as a separate standalone) is consistent with `module_15.md` §1 ("Unique Architecture: STANDALONE MODEL").

### Phase 4: Output Extraction — postsolve.gms (`Data_Flow.md` §3.5)

GDX output via `Execute_Unload "fulldata.gdx"`. The 4-attribute extract pattern (`oq52_...(t,i,emis,"level")`, `.m`, `.up`, `.lo`) is an accurate representation of MAgPIE's postsolve convention.

**Overall pipeline stages: Internally consistent and verified across Data_Flow.md and module_09.md.**

---

## 3. File Types, Parameter Names, and Upstream R Sources

### File types involved in driver data

| File | Format | Content |
|------|--------|---------|
| `f09_pop_iso.csv` | `.csv` | Population by ISO, scenario |
| `f09_gdp_ppp_iso.csv` | `.csv` | GDP PPP by ISO, scenario |
| `f09_gdp_mer_iso.csv` | `.csv` | GDP MER by ISO, scenario |
| `f09_development_state.cs3` | `.cs3` | World Bank income groups by region, scenario |
| `f09_demography.cs3` | `.cs3` | Population by age/sex/ISO/scenario |
| `f09_physical_inactivity.cs3` | `.cs3` | Inactivity rates by age/sex/ISO/scenario |
| `fm_gdp_defl_ppp.cs4` | `.cs4` | GDP deflators (rarely used directly) |

The core population and GDP files use `.csv`; the richer demographic and categorical files use `.cs3`/`.cs4`. Source: `module_09.md` §4.

### Key parameter names

| Parameter | Prefix type | Scope | Note |
|-----------|-------------|-------|------|
| `f09_pop_iso` | `f_` | module-internal | raw file read |
| `i09_pop_raw` | `i_` | module-internal | aggregated, scenario-indexed |
| `i09_gdp_pc_ppp_iso_raw` | `i_` | module-internal | per-capita computed |
| `im_pop_iso` | `im_` | cross-module | main consumer interface |
| `im_pop` | `im_` | cross-module | regional-level |
| `im_gdp_pc_ppp_iso` | `im_` | cross-module | used by 4 modules |
| `im_gdp_pc_mer_iso` | `im_` | cross-module | used by 2 modules |
| `im_gdp_pc_mer` | `im_` | cross-module | regional MER |
| `im_development_state` | `im_` | cross-module | used by 5 modules |
| `im_demography` | `im_` | cross-module | age/sex structure |
| `im_physical_inactivity` | `im_` | cross-module | PAL for caloric req |

### Upstream R sources

The doc (`module_09.md` §4, §5.1) names these as the upstream data origins:
- **Population**: IIASA SSP Database (KC & Lutz 2017) — via `f09_pop_iso.csv`
- **GDP PPP**: OECD, IMF, World Bank historical + IIASA SSP projections — via `f09_gdp_ppp_iso.csv`
- **GDP MER**: World Bank, IMF historical + IIASA SSP projections — via `f09_gdp_mer_iso.csv`
- **Demographics**: UN Population Division + IIASA SSP Database — via `f09_demography.cs3`
- **Development state**: World Bank income classification — via `f09_development_state.cs3`
- **Physical inactivity**: WHO Global Health Observatory + projections — via `f09_physical_inactivity.cs3`

The R preprocessing package that produces these files for `input.tgz` is the `mrdrivers` package (the upstream R preprocessing layer). The doc does not name `mrdrivers` explicitly in Module 09's own documentation but the AGENT.md Quick Module Finder ("Adjacent layers") lists `mrdrivers` as the R package for driver data. The Data_Flow.md does not mention `mrdrivers` by package name — it only names the underlying data sources (IIASA, World Bank, etc.). This is a minor gap in documentation cross-referencing, but not a factual error.

---

## 4. Flags: Mislabeled or Stale Data Sources

### 4.1 IIASA SSP Database vintage

`module_09.md` §8 item 10 explicitly acknowledges:
> "IIASA SSP Database from 2017. Does NOT include post-COVID updates. Does NOT include recent geopolitical changes."

This is not a documentation mislabeling — it is a correctly documented limitation. The SSP2 scenario projections were frozen at the 2017 vintage of the IIASA database. For users running scenarios post-2025 this means the near-term divergence year (sm_fix_SSP2 = 2025) locks to 2017-vintage SSP2 data, which predates substantial real-world demographic and economic deviations from that baseline (COVID mortality and fertility effects, post-2022 energy price shocks, etc.).

The documentation correctly flags this, so it is not a documentation error — but it is a stale data source that users should be aware of.

### 4.2 LUH2 vs LUH3 source label in Data_Flow.md

`Data_Flow.md` §1.2 lists under "Land Use":
> "Initial land use (LUH3 - CMIP7 input4MIPs v3.1.1, via `mrlandcore::calcLanduseInitialisation`): `modules/10_land/input/avl_land_t.cs3` -> `f10_land`"
> "LUH2 side layers (biodiversity / secondary-forest shares, via `mrmagpie::calcLuh2SideLayers`): `input/luh2_side_layers_0.5.mz`, ..."

These are the land-use inputs, not driver inputs, but they illustrate how the doc explicitly distinguishes LUH3 (initial land use, CMIP7 v3.1.1) from LUH2 (side layers — biodiversity/secondary forest). This distinction is correctly labeled. No mislabeling detected here.

### 4.3 No R package name for module 09 driver preprocessing in Data_Flow.md

As noted above, `Data_Flow.md` §1.2 names the underlying data institutions (IIASA, World Bank, etc.) for GDP/population but does not explicitly name `mrdrivers` as the R preprocessing package. The preproc-agent's `PREPROC_AGENT.md` covers this layer. Within the scope of the Data_Flow.md, this is an omission rather than a mislabeling — the doc correctly names the data sources but does not trace the R preprocessing provenance. This is not a factual error.

### 4.4 No stale source mislabeling found specific to drivers

No case was found where the doc claims a data source that is demonstrably wrong (e.g., wrongly attributing population data to FAO rather than IIASA). The sources documented in `module_09.md` §4 are internally consistent. The stale-vintage flag (IIASA 2017) is the main issue and is already documented by the module itself.

---

## Summary

**File format**: Population enters as `f09_pop_iso.csv` (`.csv`, dimensions `t_all x iso x pop_gdp_scen09`, mio. capita/yr, 1965–2150).

**GAMS reading**: `$include` into `f09_pop_iso(t_all,iso,pop_gdp_scen09)` (`f_` prefix = raw file, module-internal) at `input.gms:36-38`.

**Processing chain**: `f09_pop_iso` → `i09_pop_raw` (regional sum, preloop.gms:11) → `im_pop_iso` / `im_pop` (scenario-selected cross-module interface parameters, preloop.gms:40-50).

**Phase**: All Module 09 processing happens in Phase 1 / Preloop (once per simulation). No Module 09 computation occurs in the time loop.

**First consumer**: Module 15 (food demand, `anthro_iso_jun22` realization), which uses `im_pop`, `im_pop_iso`, `im_gdp_pc_ppp_iso`, `im_gdp_pc_mer_iso`, `im_demography`, and `im_physical_inactivity` in `q15_food_demand` (`equations.gms:10-14`) and throughout its standalone demand model.

**Pipeline stages**: Data_Flow.md's 4-phase description (Preprocessing → Time Loop → presolve/solve/postsolve → Output) is internally consistent and corroborated by module_09.md.

**Data source flags**: No mislabeling detected. One correctly documented staleness issue: IIASA SSP Database vintage is 2017 (module_09.md §8 item 10), predating post-COVID demographic updates.

---

## Epistemic Status

- `core_docs/Data_Flow.md` — 🟡 Documented (read this session)
- `modules/module_09.md` — 🟡 Documented (read this session)
- `modules/module_15.md` — 🟡 Documented (read this session, partial)
- No raw GAMS source code read (per task constraints); all citations are to AI documentation files, with file:line references as stated in those docs
- Line numbers cited from module docs were verified at the doc's last update date (`module_09.md` last verified 2025-10-13); code changes since then may have shifted them

**Sources**: `core_docs/Data_Flow.md`, `modules/module_09.md`, `modules/module_15.md` (partial)
