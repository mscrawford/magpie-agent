# MAgPIE Data Flow Documentation
## Phase 3: Complete Data Pipeline from Inputs to Outputs

### Executive Summary

MAgPIE processes approximately 72 MB of input data across ~172 files through a sophisticated multi-phase pipeline. The model integrates diverse data sources (LPJmL, FAO, IMAGE, IPCC, etc.) through standardized loading patterns, performs extensive calibration and spatial aggregation, optimizes land-use decisions, and generates comprehensive outputs in GDX format for post-processing.

### 1. Input Data Architecture

#### 1.1 File Format Distribution

| Format | Count | Purpose | Example Files |
|--------|-------|---------|---------------|
| `.cs3` | 20 | 3D GAMS data (time×region×category) | `lpj_yields.cs3`, `f14_region_yields.cs3` |
| `.cs4` | 10 | 4D GAMS data | `f53_EFch4Rice.cs4` |
| `.mz` | 26 | Binary compressed spatial data (0.5°) | `LUH2_croparea_0.5.mz`, `wdpa_baseline_0.5.mz` |
| `.csv` | 76 | Standard comma-separated values | `f09_gdp_ppp_iso.csv`, `f09_pop_iso.csv` |
| `.cs2` | Legacy | 2D GAMS data | `lpj_watavail_grper.cs2` |
| `.rds` | 22 | R data serialization | Configuration files |

**Total Input Volume:** ~72 MB compressed, ~172 files

#### 1.2 Major Data Sources

**Biophysical Data (LPJmL - Lund-Potsdam-Jena managed Land model):**
- Crop yields: `modules/14_yields/input/lpj_yields.cs3`
- Carbon stocks: `modules/52_carbon/input/lpj_carbon_stocks.cs3`
- Soil carbon: `modules/59_som/input/lpj_carbon_topsoil.cs2b`
- Water availability: `modules/43_water_availability/input/lpj_watavail_grper.cs2`
- Irrigation requirements: `modules/42_water_demand/input/lpj_airrig.cs2`
- Grassland productivity: `modules/31_past/input/lpj_grper_0.5.mz`

**Agricultural Statistics (FAO):**
- Historical yields: `modules/14_yields/managementcalib_aug19/input/f14_region_yields.cs3`
- Water requirements: `modules/42_water_demand/input/f42_wat_req_fao.csv`
- Food supply: `input/f15_supply2intake_ratio_FAO.cs3`
- Livestock production: `modules/70_livestock/fbask_jan16/input/f70_hist_prod_livst.cs3`

**Land Use (LUH2 - Land-Use Harmonization v2):**
- Initial cropland: `input/LUH2_croparea_0.5.mz`
- Land-use layers: `modules/10_land/landmatrix_dec18/input/fm_luh2_side_layers()`

**Climate & Emissions (IPCC):**
- Emission factors: `modules/58_peatland/input/f58_ipcc_wetland_ef2.cs3`
- Methane coefficients: `modules/53_methane/input/f53_EFch4Rice.cs4`
- Climate zones: `input/ipcc_climate_zones_c200.mz`

**Conservation (WDPA - World Database on Protected Areas):**
- Protected areas: `modules/22_land_conservation/input/wdpa_baseline_0.5.mz`

**Socioeconomic Projections:**
- GDP/Population: `modules/09_drivers/input/f09_gdp_ppp_iso.csv`, `f09_pop_iso.csv`
- Development indicators: `input/f09_governance_indicator.cs3`
- Urban population: `input/f09_urbanpop_grid.cs3`

### 2. Data Loading and Processing Pipeline

#### 2.1 Standardized Parameter Prefixes

| Prefix | Type | Description | Scope |
|--------|------|-------------|-------|
| `f_` | File parameters | Raw data as read from files | Module-internal |
| `i_` | Input parameters | Processed data influencing optimization | Module-internal |
| `p_` | Processing parameters | Dynamic parameters (influenced by & influence optimization) | Module-internal |
| `fm_` | File module parameters | File data shared across modules | Cross-module |
| `pm_` | Processing module parameters | Processed data shared across modules | Cross-module |
| `im_` | Input module parameters | External inputs shared across modules | Cross-module |
| `vm_` | Variables | Optimization variables | Cross-module |
| `o_` | Output parameters | Results from optimization | Module-internal |
| `x_` | eXtremely important outputs | Critical outputs for post-processing | Module-internal |

#### 2.2 Module Input Structure

Each module follows this standardized file organization:
```
modules/XX_module_name/realization_name/
├── input.gms          # Parameter declarations & data loading
├── declarations.gms   # Variable/parameter definitions
├── preloop.gms        # One-time preprocessing
├── presolve.gms       # Per-timestep preprocessing
├── equations.gms      # Constraint definitions
├── postsolve.gms      # Output data extraction
└── input/
    └── files          # Manifest of required input files
```

#### 2.3 Data Loading Example - Yield Module (14)

```gams
# Step 1: Load raw file data
table f14_yields(t_all,j,kve,w) LPJmL potential yields (tDM per ha per yr)
$ondelim
$include "./modules/14_yields/input/lpj_yields.cs3"
$offdelim
;

# Step 2: Apply climate scenario filters
$if "%c14_yields_scenario%" == "nocc"
    f14_yields(t_all,j,kve,w) = f14_yields("y1995",j,kve,w);

# Step 3: Fill missing years
m_fillmissingyears(f14_yields,"j,kve,w");

# Step 4: Transform to calibrated inputs (in preloop.gms)
i14_yields_calib(t,j,kve,w) = f14_yields(t,j,kve,w);

# Step 5: Apply FAO calibration
i14_managementcalib(t,j,knbe14,w) =
    1 + (sum(cell(i,j), i14_fao_yields_hist(t,i,knbe14)
                       - i14_modeled_yields_hist(t,i,knbe14))
         / f14_yields(t,j,knbe14,w)
         * (f14_yields(t,j,knbe14,w)
            / (sum(cell(i,j),i14_modeled_yields_hist(t,i,knbe14))+10**(-8)))
         ** sum(cell(i,j),i14_lambda_yields(t,i,knbe14)))
         $(f14_yields(t,j,knbe14,w)>0);

i14_yields_calib(t,j,knbe14,w) = i14_managementcalib(t,j,knbe14,w)
                                  * f14_yields(t,j,knbe14,w);
```

### 3. Execution Phases

#### 3.1 Phase 1: Preprocessing (Once per simulation)

**Location:** `/core/calculations.gms` → `$batinclude "./modules/include.gms" start`

**Execution Order:**
1. **Sets Definition** (`/core/sets.gms`): Define all dimensions
2. **Declarations** (`modules/include.gms declarations`): Declare variables/parameters
3. **Input Loading** (`modules/include.gms input`): Load all data files
4. **Start Phase** (`modules/include.gms start`): Initialize baseline
5. **Preloop** (`modules/include.gms preloop`): One-time calibrations

**Key Transformations:**
- **Spatial Aggregation:** 67,420 grid cells (0.5°) → 200 simulation clusters (`j`)
- **Temporal Alignment:** Fill missing years, apply scenarios
- **Calibration:** Align to historical observations (FAO yields, production)

#### 3.2 Phase 2: Time Loop (Per 5-year timestep)

**Loop Structure:**
```gams
loop (t$(m_year(t) > start_year),
    ct(t) = yes;  # Activate current timestep

    # PRESOLVE: Update dynamic parameters
    $batinclude "./modules/include.gms" presolve

    # SOLVE: Run optimization
    $batinclude "./modules/include.gms" solve

    # POSTSOLVE: Extract and store results
    $batinclude "./modules/include.gms" postsolve

    Execute_Unload "fulldata.gdx";  # Save complete state
);
```

#### 3.3 Phase 3A: Per-Timestep Preprocessing (presolve.gms)

**Dynamic Updates:**
```gams
# Update land bounds based on previous timestep
vm_land.lo(j,"primforest") = (1-s35_natveg_harvest_shr) * pcm_land(j,"primforest")

# Forest age-class progression (5-year shift)
p35_secdforest(t,j,ac) = pc35_secdforest(j,ac-1)

# Forest disturbance losses
p35_disturbance_loss_secdf(t,j,ac) =
    pc35_secdforest(j,ac) × f35_forest_lost_share(i,"fires")

# Carbon density updates
pm_carbon_density_secdforest_ac(t,j,ac,"vegc") from LPJmL

# Conservation bounds
vm_land.lo(j,land_natveg) = pm_land_conservation(t,j,land,"protect")
```

#### 3.4 Phase 3B: Optimization

**Model Configuration:**
```gams
model magpie / all - m15_food_demand /;
option iterlim = 1000000;
option reslim = 1000000;
```

**Objective Function:**
```
minimize vm_cost_glo = Σ costs - Σ benefits
```

**Key Optimization Variables:**
| Variable | Description | Unit |
|----------|-------------|------|
| `vm_land(j,land)` | Land allocation by type | mio. ha |
| `vm_area(j,kcr,w)` | Crop area by crop and water type | mio. ha |
| `vm_prod(j,k)` | Production by product | mio. tDM |
| `vm_yld(j,kve,w)` | Realized yields | tDM/ha/yr |
| `vm_carbon_stock(j,land,c_pools)` | Carbon storage | mio. tC |
| `vm_tau(h,tax)` | Technology change factor | 1 |
| `vm_trade(i,k)` | Trade flows | mio. tDM |
| `vm_water_demand(j,wat_src,wat_dem)` | Water use | mio. m³ |

**Core Constraint Types:**
```gams
# Example: Yield constraint with technology change
q14_yield_crop(j,kcr,w) ..
    vm_yld(j,kcr,w) =e=
        sum(ct, i14_yields_calib(ct,j,kcr,w))
        * sum((cell(i,j), supreg(h,i)),
            vm_tau(h,"crop") / fm_tau1995(h));
```

#### 3.5 Phase 4: Output Extraction (postsolve.gms)

**Extract 4 attributes per variable/equation:**
```gams
oq52_emis_co2_actual(t,i,emis_oneoff,"level")    = q52_emis_co2_actual.l(i,emis_oneoff);
oq52_emis_co2_actual(t,i,emis_oneoff,"marginal") = q52_emis_co2_actual.m(i,emis_oneoff);
oq52_emis_co2_actual(t,i,emis_oneoff,"upper")    = q52_emis_co2_actual.up(i,emis_oneoff);
oq52_emis_co2_actual(t,i,emis_oneoff,"lower")    = q52_emis_co2_actual.lo(i,emis_oneoff);

# Update state for next timestep
pcm_land(j,land) = vm_land.l(j,land);
```

### 4. Spatial and Temporal Data Handling

#### 4.1 Spatial Resolution Cascade

**Input Resolution (0.5° grid):**
- Global grid: 360 × 720 = 259,200 theoretical cells
- Land cells: ~67,420 actual cells with land
- Storage format: `.mz` compressed binary grids

**Simulation Resolution (200 clusters):**
- Clustering based on:
  - Biophysical similarity (soil, climate, topography)
  - Current land use patterns
  - Market accessibility
- Mapping: `cell(i,j)` links clusters to regions

**Regional Aggregation (12 regions):**
- Regions (`i`): CAZ, CHA, EUR, IND, JPN, LAM, MEA, NEU, OAS, REF, SSA, USA
- Super-regions (`h`): Same as regions, used for technology spillovers

**Example Cell Distribution:**
```
CHA (China): 19 cells (CHA_6 through CHA_24)
IND (India): 12 cells (IND_37 through IND_48)
USA: 18 cells (USA_183 through USA_200)
```

#### 4.2 Temporal Data Flow

**Time Dimensions:**
```gams
t_all       # All periods (1965-2150, 5-year steps)
t_past      # Historical (1965-2015, configurable)
t           # Simulated (1995-2100, configurable)
ct(t)       # Current timestep (single-element dynamic)
pt(t)       # Previous timestep
```

**Temporal Dynamics Example - Forest Age Classes:**
```gams
# Age-class progression (5-year timesteps)
s35_shift = m_timestep_length_forestry/5;  # Usually = 1
p35_secdforest(t,j,ac)$(ord(ac) > s35_shift) =
    pc35_secdforest(j,ac-s35_shift);  # Shift to older age class
```

### 5. Critical Data Dependencies

#### 5.1 Multi-Module Parameters

**Land System:**
- `pcm_land(j,land)` - Current land state (updated each timestep)
- `pm_land_start(j,land)` - Initial land distribution
- `vm_lu_transitions(j,land_from,land_to)` - Land-use change flows

**Carbon System:**
- `fm_carbon_density(t_all,j,land,c_pools)` - From LPJmL
- `pm_carbon_density_secdforest_ac(t,j,ac,ag_pools)` - Age-specific
- Used by: modules 35, 32, 52, 56

**Production System:**
- `i14_yields_calib(t,j,kve,w)` - Calibrated yields
- `vm_tau(h,tax)` - Technology factor
- Flow: Module 14 → 30 → 17

#### 5.2 Calibration Feedback Loops

**Yield Calibration Process:**
1. Load LPJmL yields at 0.5° resolution
2. Aggregate to regions using cropland patterns
3. Compare to FAO regional yields
4. Calculate calibration factor:
   ```gams
   λ = 1 if FAO ≤ LPJmL (overestimation)
   λ = √(LPJmL/FAO) if FAO > LPJmL (underestimation)
   ```
5. Apply limited calibration to maintain spatial patterns

### 6. Output Data Structure

#### 6.1 GDX Files (GAMS Data Exchange)

**Main Output File:** `fulldata.gdx`
- Complete model state at each timestep
- All variables with .l, .m, .up, .lo attributes
- All parameters (input and calculated)
- Size: 50-100 MB per timestep

**Restart Files:** `restart_*.gdx`
- Enable continuation from saved states
- Contains complete variable levels

#### 6.2 R-Based Post-Processing

**Processing Package:** `magpie4` (R package)

**Key Functions:**
```r
reportLandUse()       # Land statistics
reportEmissions()     # GHG calculations
reportProduction()    # Agricultural output
reportPrices()        # Shadow prices
reportWater()         # Water stress
reportBiodiversity()  # BII indicators
```

**Output Formats:**
- IAMC format for model intercomparison
- NetCDF grids at 0.5° resolution
- CSV regional/global aggregates
- Visualization plots (ggplot2)

### 7. Data Flow Example: Carbon Emissions

Complete flow for CO2 emissions from land-use change:

1. **Input:** LPJmL carbon density
   ```gams
   fm_carbon_density(t_all,j,land,c_pools)  # tC/ha
   ```

2. **Preloop:** Initialize age-class specific stocks
   ```gams
   pm_carbon_density_secdforest_ac(t,j,ac,"vegc")
   ```

3. **Presolve:** Track land transitions
   ```gams
   vm_lu_transitions.l(j,"primforest","crop")
   ```

4. **Optimization:** Determine land allocation
   ```gams
   vm_land(j,land)  # Endogenous decision
   ```

5. **Postsolve:** Calculate emissions
   ```gams
   emissions = (land_before - land_after) × carbon_density × 44/12
   ```

6. **Output:** Store in GDX
   ```gams
   oq52_emis_co2_actual(t,i,emis_oneoff,"level")
   ```

### 8. Performance Considerations

#### 8.1 Computational Efficiency

**Spatial Clustering Benefits:**
- Original: 67,420 cells → Intractable
- Clustered: 200 cells → ~100,000 variables
- Trade-off: Detail vs. computation time

**Temporal Resolution:**
- 5-year steps reduce solve frequency
- Annual data interpolated as needed

#### 8.2 Typical Run Statistics

| Metric | Value |
|--------|-------|
| Variables | ~100,000 |
| Equations | ~150,000 |
| Solve time/timestep | 5-30 minutes |
| Full run (1995-2100) | 2-6 hours |
| Input data | 72 MB |
| Output per timestep | 50-100 MB |
| Total output | 1-2 GB |

### 9. Data Quality and Validation

#### 9.1 Calibration Targets

**Historical Alignment:**
- FAO crop yields (regional level)
- FAO production quantities
- LUH2 land-use patterns
- National forest inventories

**Validation Metrics:**
- R² for yield predictions: >0.8
- Land-use change rates: ±10% of observations
- Production trends: within FAO confidence intervals

#### 9.2 Uncertainty Handling

**Parameter Uncertainty:**
- Scenario analysis (SSP1-5)
- Sensitivity runs
- Monte Carlo sampling (selected parameters)

**Spatial Uncertainty:**
- Clustering validation
- Scale effects analysis
- Resolution sensitivity tests

### 10. Best Practices for Data Management

#### 10.1 Adding New Input Data

1. Place file in appropriate module's `input/` folder
2. Add filename to `input/files` manifest
3. Declare parameter in `input.gms`
4. Apply standard preprocessing (scenarios, missing years)
5. Document units and source

#### 10.2 Modifying Data Flow

1. Follow naming conventions (f_, i_, p_, vm_, o_)
2. Update both `declarations.gms` and `input.gms`
3. Consider multi-module impacts
4. Test with minimal timesteps first
5. Validate against known outputs

#### 10.3 Debugging Data Issues

**Common Problems:**
- Unit mismatches (check for 10^6 factors)
- Missing years (use `m_fillmissingyears`)
- Spatial aggregation errors (verify `cell(i,j)` mapping)
- Calibration divergence (check λ factors)

**Diagnostic Tools:**
- `$onlisting` / `$offlisting` for selective output
- `display` statements in GAMS
- GDX viewer for inspecting outputs
- R scripts for validation plots

### Summary

MAgPIE's data flow architecture provides a robust pipeline from diverse input sources through calibration, optimization, and output generation. The standardized parameter naming convention and modular structure enable clear data provenance tracking. The system balances computational efficiency through spatial clustering with maintenance of sufficient detail for policy-relevant analysis. Understanding this data flow is essential for model development, debugging, and interpretation of results.