# Module 18: Residues - Complete Documentation

**Realization (DEFAULT)**: `flexreg_apr16` (regional-level, 9 equations) - confirmed in `config/default.cfg:622` (`cfg$gms$residues <- "flexreg_apr16"`)
**Alternative Realizations**: `flexcluster_jul23` (cluster-level, 12 equations), `off` (no residue accounting)
**Source Files Verified**: `flexreg_apr16/declarations.gms` (58 lines), `equations.gms` (124 lines), `input.gms` (51 lines), `sets.gms` (40 lines), `presolve.gms` (10 lines), `preloop.gms` (9 lines), `realization.gms` (37 lines), `scaling.gms` (14 lines)
**Documentation Coverage**: This document leads with the default `flexreg_apr16` realization. The `flexcluster_jul23` realization is summarized in the [Alternative Realization](#alternative-realization-flexcluster_jul23) section below.

---

> ⚙️ **Default Realization**: `flexreg_apr16`
> Confirmed in `config/default.cfg:622`. Alternatives: `flexcluster_jul23` (cluster-based AG biomass aggregation), `off` (disables residue accounting entirely).

## Overview

Module 18 calculates **production of crop residues** (aboveground and belowground biomass) and their **allocation to different uses**: burning on fields, removal for feed/bioenergy, recycling to soils, or other purposes (construction, fuel).

**Core Function**: Translates crop production (Module 17) and harvested area (Module 30) into residue biomass, tracks residue fate, calculates nutrient recycling (N, P, K), and computes harvest costs.

**Key Innovation**: Uses **crop growth functions (CGFs)** with slope and intercept (IPCC 2006) instead of fixed harvest indices, allowing regional differences and future evolution of harvest efficiency.

**Methodological Source**: IPCC 2006 Guidelines for National Greenhouse Gas Inventories (referenced in `flexreg_apr16/realization.gms:14-19`).

**Reference**: `module.gms:8-16`

---

## Realization Architecture

### `flexreg_apr16` (Default)

All residue accounting - biomass production, field balance, burning, recycling - happens at the **regional level (i)**. The only cluster-distributed variable is `v18_prod_res(j,kres)`, which represents the cluster-level allocation of homogeneous residue groups for spatial reporting; its regional sum is locked to `vm_prod_reg(i,kres)` via `q18_prod_res_reg` (`flexreg_apr16/equations.gms:78-81`).

- **9 equations**, all regional except the cluster-sum constraint
- **8 variables**: 7 at regional level (i), 1 at cluster level (`v18_prod_res(j,kres)`)
- **Computational profile**: Smaller variable space than `flexcluster_jul23` (no per-cluster field balance, burning, or recycling)

### `flexcluster_jul23` (Alternative)

Adds cluster-level AG biomass and removal constraints (12 equations total). The default `flexreg_apr16` enforces residue mass-balance only at the regional level; `flexcluster_jul23` adds three extra constraints that pin residue biomass and removal at the cluster level for tighter spatial coupling. See [Alternative Realization: flexcluster_jul23](#alternative-realization-flexcluster_jul23) below.

### `off`

Disables residue accounting entirely (no residue biomass, no burning, no nutrient recycling from residues).

---

## Residue Classification

### Residue Types (`flexreg_apr16/sets.gms:28-34`)

Module 18 aggregates **crop-specific residues** into **three homogeneous residue groups** via the `kres_kcr(kres,kcr)` mapping:

```gams
kres_kcr(kres,kcr) mapping:
  res_cereals      -> tece, maiz, trce, rice_pro
  res_fibrous      -> soybean, rapeseed, groundnut, puls_pro,
                       sugr_beet, sugr_cane, cottn_pro
  res_nonfibrous   -> potato, cassav_sp, others
```

**Purpose** (`flexreg_apr16/equations.gms:60-68`):
- Residue biomass estimated with **crop-specific nutrient composition** (for accurate nutrient budgets)
- Removed residues treated as **homogeneous within groups** (to reduce commodity count in MAgPIE)
- Translation (equation 5 below) ensures mass balance is maintained

### Non-Used Crops (`flexreg_apr16/sets.gms:23-24`)

**Fixed to zero removal at the regional level** (`flexreg_apr16/presolve.gms:8`):
```gams
nonused18 = / sunflower, oilpalm, foddr, begr, betr /
v18_res_ag_removal.fx(i,nonused18,attributes) = 0;
```

**Rationale**:
- sunflower, oilpalm: specialized processing residues (handled outside the residue pipeline)
- foddr: direct forage (no separate residue product)
- begr, betr: bioenergy grasses (full plant harvested as the primary product)

---

## Equations (Default Realization `flexreg_apr16`)

The default realization has **9 equations** in `flexreg_apr16/equations.gms` (124 lines). All operate at regional level (i) except the cluster-sum constraint (equation 6).

### 1. Aboveground Residue Production (`q18_prod_res_ag_reg`)

**Formula** (`flexreg_apr16/equations.gms:14-19`):
```gams
q18_prod_res_ag_reg(i2,kcr,attributes) ..
    vm_res_biomass_ag(i2,kcr,attributes)
    =e=
    (sum((cell(i2,j2),w), vm_area(j2,kcr,w)) * sum(ct,f18_multicropping(ct,i2)) * f18_cgf("intercept",kcr)
    + vm_prod_reg(i2,kcr) * f18_cgf("slope",kcr))
    * f18_attributes_residue_ag(attributes,kcr);
```

**Meaning**: Regional AG residue biomass (in attribute units X) = (Sigma cluster harvested area x multicropping x intercept + regional production x slope) x attribute conversion.

**Crop Growth Function (CGF)** (IPCC 2006 methodology):
- **Slope** (`f18_cgf("slope",kcr)`): ratio of residue to harvested product (dimensionless)
- **Intercept** (`f18_cgf("intercept",kcr)`): base residue per unit area (tDM/ha), independent of yield

**Multicropping** (`f18_multicropping(ct,i2)`): Accounts for multiple cropping cycles per year. Applied to the area-based intercept term only (not the production-based slope term). Values > 1 indicate multiple harvests annually.

**Attribute conversion** (`f18_attributes_residue_ag(attributes,kcr)`): Maps dry-matter biomass to per-attribute content (dm, nr, c, gj, p, k, wm; full attribute set from core sets).

**Inputs**:
- `vm_area(j,kcr,w)` - cluster harvested area by water type (from Module 30)
- `vm_prod_reg(i,kcr)` - regional crop production (from Module 17)

---

### 2. Belowground Residue Production (`q18_prod_res_bg_reg`)

**Formula** (`flexreg_apr16/equations.gms:24-28`):
```gams
q18_prod_res_bg_reg(i2,kcr,dm_nr) ..
    vm_res_biomass_bg(i2,kcr,dm_nr)
    =e=
    (vm_prod_reg(i2,kcr) + vm_res_biomass_ag(i2,kcr,"dm")) * f18_cgf("bg_to_ag",kcr)
    * f18_attributes_residue_bg(dm_nr,kcr);
```

**Meaning**: BG residue biomass = (regional crop production + AG residue dry matter) x BG-to-AG ratio x attribute conversion.

**Logic**:
- Total aboveground biomass = harvested production + AG residues
- Belowground biomass = fraction of total aboveground biomass
- Root:shoot ratio varies by crop type

**CGF parameter** (`f18_cgf("bg_to_ag",kcr)`): belowground-to-aboveground biomass ratio.

**Attributes set** (`dm_nr`, from `flexreg_apr16/sets.gms:11-12`): `dm, nr, c` (subset of attributes, only nutrients relevant for belowground tracking).

---

### 3. Field Balance (`q18_res_field_balance`)

**Formula** (`flexreg_apr16/equations.gms:38-43`):
```gams
q18_res_field_balance(i2,kcr,attributes) ..
    vm_res_biomass_ag(i2,kcr,attributes)
    =e=
    v18_res_ag_removal(i2,kcr,attributes)
    + vm_res_ag_burn(i2,kcr,attributes)
    + v18_res_ag_recycling(i2,kcr,attributes);
```

**Meaning**: AG biomass = removal + burning + recycling. All three fate variables and the biomass variable are at regional level (i) in the default realization.

**Three fates** (mass-balance constraint, no residue can disappear or be created):
1. **Removal** (`v18_res_ag_removal`) - harvested for feed, bioenergy, or other uses
2. **Burning** (`vm_res_ag_burn`) - burned on field (emissions + partial nutrient return)
3. **Recycling** (`v18_res_ag_recycling`) - left on field to decay (full nutrient return)

---

### 4. Residue Burning (`q18_res_field_burn`)

**Formula** (`flexreg_apr16/equations.gms:52-57`):
```gams
q18_res_field_burn(i2,kcr,attributes) ..
    vm_res_ag_burn(i2,kcr,attributes)
    =e=
    sum(ct, im_development_state(ct,i2) * i18_res_use_burn(ct,"high_income",kcr)
    + (1-im_development_state(ct,i2)) * i18_res_use_burn(ct,"low_income",kcr))
    * vm_res_biomass_ag(i2,kcr,attributes);
```

**Meaning**: Burned residue = (development-weighted burn share) x AG biomass.

**Development weighting** (`im_development_state(t,i)`, from Module 09, ranges 0-1):
- 0 = low-income (developing)
- 1 = high-income (developed)
- Linear interpolation between development states

**Historical burn shares** (Smil 1999, cited in `flexreg_apr16/equations.gms:45-50`):
- Developed regions: 15% of AG residue biomass burned
- Developing regions: 25% of AG residue biomass burned

**Future trajectory**: scenario-dependent via `c18_burn_scen` (see Configuration Options below).

---

### 5. Residue Translation: heterogeneous -> homogeneous (`q18_translate`)

**Formula** (`flexreg_apr16/equations.gms:70-73`):
```gams
q18_translate(i2,kres,attributes) ..
    sum(kres_kcr(kres,kcr), v18_res_ag_removal(i2,kcr,attributes))
    =e=
    vm_prod_reg(i2,kres) * fm_attributes(attributes,kres);
```

**Meaning**: Sum of crop-specific removals (per attribute) = homogeneous residue-group production (`vm_prod_reg(i,kres)`) x per-attribute content (`fm_attributes(attributes,kres)`).

**Purpose**:
- **Input**: heterogeneous crop-specific residues (different nutrient content per crop)
- **Output**: homogeneous residue groups (`res_cereals`, `res_fibrous`, `res_nonfibrous`)
- **Constraint**: mass balance per attribute is maintained during aggregation

**Why needed**:
- Nutrient budgets require crop-specific composition
- Trade/feed modules need simple commodities (fewer variables)
- Translation conserves mass and nutrients

---

### 6. Cluster Distribution Constraint (`q18_prod_res_reg`)

**Formula** (`flexreg_apr16/equations.gms:78-81`):
```gams
q18_prod_res_reg(i2,kres) ..
    sum(cell(i2,j2), v18_prod_res(j2,kres))
    =e=
    vm_prod_reg(i2,kres);
```

**Meaning**: Sum of cluster-level residue production (`v18_prod_res(j,kres)`) over the clusters of a region equals the regional residue production (`vm_prod_reg(i,kres)`).

**Purpose**: Distributes the regional homogeneous-group residue production across clusters for spatial reporting. The cluster allocation is flexible (no upper bound at cluster level); only the regional sum is constrained.

**Interface variable**: `vm_prod_reg(i,kres)` is consumed by Module 21 (Trade) and Module 16 (Demand). Note: `kres` is a subset of `kall`, so `vm_prod_reg` is the same name reused for residue groups.

---

### 7. Nitrogen Recycling (`q18_res_recycling_nr`)

**Formula** (`flexreg_apr16/equations.gms:90-96`):
```gams
q18_res_recycling_nr(i2) ..
    vm_res_recycling(i2,"nr")
    =e=
    sum(kcr, v18_res_ag_recycling(i2,kcr,"nr")
            + vm_res_ag_burn(i2,kcr,"nr")*(1-f18_res_combust_eff(kcr))
            + vm_res_biomass_bg(i2,kcr,"nr"));
```

**Meaning**: N recycled to soils = AG recycling + N from burned residues that escapes combustion + all BG residue N.

**Three N sources**:
1. **AG recycling**: residues left on field (full N content returned to soil)
2. **Burned residues**: partial N loss to volatilization; fraction `(1 - f18_res_combust_eff(kcr))` remains in ash and returns to soil
3. **BG residues**: all belowground N stays in soil (roots are never harvested in the default model)

**Combustion efficiency** (`f18_res_combust_eff(kcr)`): fraction of N volatilized during burning (per crop). Example: efficiency 0.80 -> 20% of N remains in ash.

**Interface**: `vm_res_recycling(i,"nr")` -> Module 50 (Nitrogen Soil Budget).

---

### 8. Phosphorus and Potassium Recycling (`q18_res_recycling_pk`)

**Formula** (`flexreg_apr16/equations.gms:104-110`):
```gams
q18_res_recycling_pk(i2,pk18) ..
    vm_res_recycling(i2,pk18)
    =e=
    sum(kcr, v18_res_ag_recycling(i2,kcr,pk18)
           + vm_res_ag_burn(i2,kcr,pk18));
```

**Meaning**: P/K recycled = AG recycling + burned residues (full P/K content returned, no volatilization).

**Key differences from N** (`flexreg_apr16/equations.gms:98-103`):
- P and K are **not volatile** during burning -> ash retains 100%
- P and K are **not water-soluble** in this representation -> remain in soil/ash
- BG residues **not included** here (P/K already in soil; no separate flow tracked)

**Set**: `pk18 = {p, k}` (subset of `npk`, excludes nitrogen; defined in `flexreg_apr16/sets.gms:14-15`).

**Interface**: `vm_res_recycling(i,pk18)` -> Module 50 (nutrient budget consumers).

---

### 9. Harvest Costs (`q18_cost_prod_res`)

**Formula** (`flexreg_apr16/equations.gms:116-119`):
```gams
q18_cost_prod_res(i2,kres) ..
    vm_cost_prod_kres(i2,kres)
    =e=
    vm_prod_reg(i2,kres) * fm_attributes("wm",kres) * f18_fac_req_kres(kres);
```

**Meaning**: Harvest cost = residue production x wet-matter conversion x unit cost.

**Data source** (`flexreg_apr16/equations.gms:112-114`): Budynski 2020, *Straw Manufacturing in Alberta*, using the lower range of US baling and hauling costs.

**Interface**: `vm_cost_prod_kres(i,kres)` -> Module 11 (Costs) objective function.

**Units**:
- `vm_prod_reg(i,kres)` - mio. tDM/yr
- `fm_attributes("wm",kres)` - wet-matter conversion (tWM per tDM)
- `f18_fac_req_kres(kres)` - factor requirement (USD17MER per tWM in the formula; note: `flexreg_apr16/input.gms:44` labels it "USD17MER per tDM" but the equation form multiplies by `fm_attributes("wm",kres)`, so the implied unit on the parameter is per tWM)
- Result: mio. USD17MER/yr

---

## Key Algorithms

### Algorithm 1: Crop Growth Functions (CGFs)

**Data source**: IPCC 2006 Guidelines (`flexreg_apr16/realization.gms:14-19`).

**Crop categories**:

1. **IPCC CGFs with intercept** (cereals, legumes, potatoes, grasses):
   - Biomass = intercept x area + slope x production
   - Allows harvest index to vary with productivity

2. **Fixed harvest indices** (oilcrops, sugar, roots, cotton, others):
   - Biomass = slope x production (intercept = 0)
   - Based on Wirsenius 2000, Lal 2005, Feller & Dun Gung 2007

**Weighted averaging** (`flexreg_apr16/realization.gms:24-26`): If multiple CGFs exist within a crop group, the model uses a weighted average based on 1995 production for historical consistency.

**File**: `f18_cgf.csv` contains slope, intercept, and bg_to_ag ratios (`flexreg_apr16/input.gms:27-30`).

---

### Algorithm 2: Burning Scenario Implementation

**Scenario selection** (`flexreg_apr16/preloop.gms:9`):
```gams
i18_res_use_burn(t_all,dev18,kcr) =
  f18_res_use_burn(t_all,"%c18_burn_scen%",dev18,kcr);
```

**Scenarios** (`flexreg_apr16/input.gms:8-9`):
- `phaseout` (default) - gradual reduction to 2050
- `constant` - maintain historical rates

**Phaseout trajectory**:
- 2010: 25% (developing), 15% (developed)
- 2050: 0% (developing), 10% (developed)
- Linear interpolation between timesteps

**Development state** (`flexreg_apr16/equations.gms:55-56`): `im_development_state(t,i)` ranges 0 to 1, providing smooth transition as countries develop.

---

### Algorithm 3: Multicropping Adjustment

**Implementation** (`flexreg_apr16/equations.gms:17`):
```gams
... sum((cell(i2,j2),w), vm_area(j2,kcr,w)) * sum(ct,f18_multicropping(ct,i2)) * f18_cgf("intercept",kcr) ...
```

**Purpose**: account for multiple cropping cycles on the same physical area.

**When multicropping > 1**:
- Harvested area > physical area
- Multiple crops per year (e.g., rice double-cropping)
- Residue production scales with number of harvests (via the intercept term only)

**Application**: applied to the intercept term (area-based), **not** the slope term (production-based). The slope term already captures yield-driven residue scaling via `vm_prod_reg`.

**File**: `f18_multicropping.csv` (time-varying by region; `flexreg_apr16/input.gms:11-14`).

---

### Algorithm 4: Non-Used Crops Exclusion

**Implementation** (`flexreg_apr16/presolve.gms:8`):
```gams
v18_res_ag_removal.fx(i,nonused18,attributes) = 0;
```

**Fixed at regional level** (`i`, not `j`, in the default realization) for: `sunflower, oilpalm, foddr, begr, betr`.

**Effect**:
- These crops still produce residue biomass (via CGFs)
- But removal is fixed at zero -> all residues must be burned or recycled
- Simplifies commodity tracking

---

## Input Data Files

| File | Parameter | Description | Dimensions | Units |
|------|-----------|-------------|------------|-------|
| `modules/18_residues/input/f18_multicropping.csv` | `f18_multicropping` | Multicropping indicator | (t_all, i) | Dimensionless (>=1) |
| `modules/18_residues/input/f18_attributes_residue_ag.csv` | `f18_attributes_residue_ag` | AG residue attribute content | (attributes, kve) | X per tDM |
| `modules/18_residues/input/f18_attributes_residue_bg.csv` | `f18_attributes_residue_bg` | BG residue attribute content | (dm_nr, kve) | X per tDM |
| `modules/18_residues/flexreg_apr16/input/f18_cgf.csv` | `f18_cgf` | Crop growth functions (slope, intercept, bg_to_ag) | (cgf, kve) | Slope (1), intercept (tDM/ha), bg_to_ag (1) |
| `modules/18_residues/flexreg_apr16/input/f18_res_use_burn.cs3` | `f18_res_use_burn` | Burn share scenarios | (t_all, burn_scen18, dev18, kcr) | Dimensionless (0-1) |
| `modules/18_residues/input/f18_res_combust_eff.cs4` | `f18_res_combust_eff` | Combustion efficiency | (kve) | Dimensionless (0-1) |
| `modules/18_residues/flexreg_apr16/input/f18_fac_req_kres.csv` | `f18_fac_req_kres` | Harvest unit costs | (kres) | USD17MER/tWM (per equation; docstring says per tDM) |

**Source**: `flexreg_apr16/input.gms:11-49`. Some files live in the realization-specific `flexreg_apr16/input/` subdirectory (CGFs, burn scenarios, factor costs); shared files (multicropping, attribute conversions, combustion efficiency) live in `modules/18_residues/input/`.

---

## Interface Variables

### Provided by Module 18

| Variable | Description | Dimensions | Units | Used By |
|----------|-------------|------------|-------|---------|
| `vm_res_biomass_ag` | AG residue biomass | (i, kcr, attributes) | Mio. tX/yr | Internal (field balance, burning, BG biomass) |
| `vm_res_biomass_bg` | BG residue biomass | (i, kcr, dm_nr) | Mio. tX/yr | Internal (N recycling) |
| `vm_res_ag_burn` | Burned AG residues | (i, kcr, attributes) | Mio. tX/yr | Module 50 (nitrogen budget), Module 57 (GHG emissions) |
| `vm_res_recycling` | Recycled nutrients | (i, npk) | Mio. tX/yr | Module 50 (nitrogen and P/K budgets) |
| `vm_cost_prod_kres` | Residue harvest costs | (i, kres) | Mio. USD17MER/yr | Module 11 (Costs) |
| `vm_prod_reg` | Regional residue production (kres slice) | (i, kres) | Mio. tDM/yr | Module 21 (Trade), Module 16 (Demand) |

**Source**: `flexreg_apr16/declarations.gms:9-18`.

**Note**: `vm_prod_reg` is also declared in Module 17 (for crops); the residue module uses the `kres` slice. Both modules share the same variable.

### Used by Module 18

| Variable | Description | Dimensions | Units | Provided By |
|----------|-------------|------------|-------|-------------|
| `vm_area` | Harvested area | (j, kcr, w) | Mio. ha | Module 30 (Croparea) |
| `vm_prod_reg` | Regional crop production (kcr slice) | (i, kcr) | Mio. tDM/yr | Module 17 (Production) |
| `im_development_state` | Development indicator | (t, i) | 0-1 | Module 09 (Drivers) |
| `fm_attributes` | Commodity attribute content | (attributes, kall) | X per tDM | Core data |

---

## Internal Variables

| Variable | Description | Dimensions | Units |
|----------|-------------|------------|-------|
| `v18_prod_res` | Cluster-level residue production | (j, kres) | Mio. tDM/yr |
| `v18_res_ag_removal` | Regional AG residue removal | (i, kcr, attributes) | Mio. tX/yr |
| `v18_res_ag_recycling` | Regional AG residue recycling | (i, kcr, attributes) | Mio. tX/yr |

**Source**: `flexreg_apr16/declarations.gms:10-14`.

**Note**: in the default realization, only `v18_prod_res` is indexed by cluster (`j`). All other internal residue variables are at regional level (`i`). This contrasts with `flexcluster_jul23`, where AG removal and biomass are tracked at cluster level.

---

## Configuration Options

| Setting | Description | Values | Default |
|---------|-------------|--------|---------|
| `c18_burn_scen` | Residue burning scenario | `phaseout`, `constant` | `phaseout` |

**Source**: `flexreg_apr16/input.gms:8-9`.

---

## Scaling

Most scaling is commented out. The only active scaling (`flexreg_apr16/scaling.gms:8`):
```gams
vm_cost_prod_kres.scale(i,kres) = 1e3;
```

Other scaling entries for `vm_res_ag_burn`, `q18_prod_res_bg_reg`, `q18_res_field_balance`, `q18_res_field_burn`, `q18_res_recycling_nr`, `q18_translate` are present but commented out.

---

## Key Dependencies

### Upstream Dependencies (Variables Used)

1. **Module 30 (Croparea)**:
   - `vm_area(j, kcr, w)` - cluster harvested area, summed via `cell(i,j)` mapping in `q18_prod_res_ag_reg`

2. **Module 17 (Production)**:
   - `vm_prod_reg(i, kcr)` - regional crop production, used in AG and BG biomass equations and in the translation equation (as `vm_prod_reg(i, kres)`)

3. **Module 09 (Drivers)**:
   - `im_development_state(t, i)` - development indicator, used in the burn share weighting

### Downstream Dependencies (Variables Provided)

1. **Module 11 (Costs)**:
   - `vm_cost_prod_kres(i, kres)` - residue harvest costs (objective function term)

2. **Module 21 (Trade) & Module 16 (Demand)**:
   - `vm_prod_reg(i, kres)` - regional residue production (supply balance)

3. **Module 50 (Nitrogen Budget)**:
   - `vm_res_recycling(i, "nr")` - N recycling from residues
   - `vm_res_ag_burn(i, kcr, "nr")` - N from burned residues

4. **Module 50 (Phosphorus/Potassium Budget)**:
   - `vm_res_recycling(i, pk18)` - P/K recycling from residues

5. **Module 57 (GHG Emissions)**:
   - `vm_res_ag_burn(i, kcr, attributes)` - residue burning emissions

---

## Limitations

### 1. No trade of residues
**What**: residues cannot be traded between regions.
**Where**: `flexreg_apr16/equations.gms:121-122`.
**Impact**: all produced residues must be used within the producing region.
**Reality**: some residue trade exists (e.g., straw pellets).

### 2. Fixed crop growth functions
**What**: CGF parameters (slope, intercept) do not evolve with technology or management.
**Where**: `f18_cgf` parameter is static.
**Impact**: cannot model breeding for improved harvest index over time.
**Exception**: multicropping factor is time-varying.

### 3. Homogeneous residue groups
**What**: crop-specific residues aggregated into 3 groups (cereal/fibrous/nonfibrous).
**Where**: `kres_kcr` mapping (`flexreg_apr16/sets.gms:28-34`).
**Impact**: loses crop-specific quality differences in feed/bioenergy applications.
**Trade-off**: reduces commodity count from ~15 crops to 3 residue groups.

### 4. Regional-level field balance
**What**: in the default realization, AG biomass, removal, burning, and recycling are all balanced at the regional level (i) - there is no cluster-level field balance.
**Where**: `flexreg_apr16/equations.gms:38-43` (field balance is i-indexed).
**Impact**: residue removal in one cluster can be implicitly compensated by another cluster within the same region; no cluster-specific harvesting constraints.
**Alternative**: `flexcluster_jul23` adds cluster-level AG biomass and a `q18_clust_field_constraint` for tighter spatial coupling.

### 5. Fixed burn shares
**What**: burn shares determined exogenously by development state and scenario.
**Where**: `i18_res_use_burn` parameter (`flexreg_apr16/preloop.gms:9`).
**Impact**: cannot optimize burning vs recycling based on economic incentives.
**Exception**: development state provides some endogenous dynamics across time.

### 6. No residue quality degradation
**What**: removed residues have the same quality regardless of storage time or conditions.
**Where**: no degradation equations in the module.
**Impact**: cannot model storage losses or quality decay.

### 7. Constant combustion efficiency
**What**: `f18_res_combust_eff(kcr)` does not vary with burning practices or technology.
**Where**: fixed parameter from `modules/18_residues/input/f18_res_combust_eff.cs4`.
**Impact**: cannot model improved burning technologies reducing N volatilization.

### 8. No belowground removal
**What**: belowground residues always remain in soil.
**Where**: only AG residues can be removed (BG enters N recycling fully).
**Impact**: cannot model root harvest (e.g., cassava stems).

### 9. Wet matter costs
**What**: harvest costs scale with wet matter via `fm_attributes("wm",kres)`, but moisture content is fixed.
**Where**: `flexreg_apr16/equations.gms:119`.
**Impact**: cannot model drying technologies or seasonal moisture variation.

---

## Alternative Realization: `flexcluster_jul23`

The `flexcluster_jul23` realization (`modules/18_residues/flexcluster_jul23/`) extends the default with **cluster-level (j2) residue accounting**, raising the equation count from 9 to 12.

**Realization rationale** (from `flexcluster_jul23/realization.gms:29-31`):
> This realization enforces cluster-level agricultural residue production, based on agricultural production at the same level. However, other uses such as burning and recycling are allowed to be balanced at the regional level, in order to reduce computational complexity.

**Three additional cluster-level equations** (in `flexcluster_jul23/equations.gms`):
1. **`q18_prod_res_ag_clust(j2,kcr)`** - cluster-level AG biomass calculation (computes `v18_res_biomass_ag_clust(j,kcr)` from cluster area and `vm_prod(j,kcr)`)
2. **`q18_clust_field_constraint(j2,kres)`** - sum of cluster AG biomass per residue group must be >= cluster-level removal `v18_prod_res(j2,kres)`, preventing over-harvesting in any cluster
3. **`q18_regional_removals(i2,kcr,attributes)`** - sums cluster-level removals `v18_res_ag_removal(j,kcr,attributes)` to a regional aggregate `v18_res_ag_removal_reg(i,kcr,attributes)`, which then enters the regional field balance

**Variable-level differences from the default**:
- `v18_res_biomass_ag_clust(j,kcr)` - cluster-level AG biomass (additional internal variable, not in default)
- `v18_res_ag_removal(j,kcr,attributes)` - **cluster-level** removal (in the default, this is at `i`)
- `v18_res_ag_removal_reg(i,kcr,attributes)` - regional aggregation of removal (additional, not in default)

**Equations that remain regional in `flexcluster_jul23`**:
- Field balance, burning, recycling, translation, costs, and cluster-distribution constraint all remain at `i` level (same as default), with field balance consuming the aggregated `v18_res_ag_removal_reg`.

**When to choose `flexcluster_jul23`**:
- When cluster-level removal constraints are needed (e.g., to enforce that no individual cluster is over-harvested even if regional totals balance)
- Trade-off: more variables and constraints -> larger model

**When to stay on the default `flexreg_apr16`**:
- For runs where regional mass balance is sufficient and computational efficiency matters
- For most standard SSP/baseline runs (the chosen default)

For the full equation listing of `flexcluster_jul23`, see `modules/18_residues/flexcluster_jul23/equations.gms` (145 lines) and `declarations.gms` (76 lines).

---

## Verification Notes

**Default realization (`flexreg_apr16`)**:
- **Equation count**: 9 equations verified in `flexreg_apr16/declarations.gms:21-29` and `equations.gms` (q18_prod_res_ag_reg, q18_prod_res_bg_reg, q18_res_field_balance, q18_res_field_burn, q18_translate, q18_prod_res_reg, q18_res_recycling_nr, q18_res_recycling_pk, q18_cost_prod_res)
- **Variable count**: 8 variables (7 at regional level i, 1 cluster v18_prod_res) verified in `declarations.gms:9-18`
- **Formulas**: All 9 equation formulas in this document copied verbatim from `flexreg_apr16/equations.gms`
- **Citations**: All file:line citations target `flexreg_apr16/*.gms` unless explicitly marked as shared (`modules/18_residues/input/`)
- **Realization name**: `flexreg_apr16` confirmed in `config/default.cfg:622`

**Alternative realization (`flexcluster_jul23`)**: Summary section above reflects the 3 additional cluster-level equations identified by comparing `flexcluster_jul23/declarations.gms` (76 lines, 12 equations) vs `flexreg_apr16/declarations.gms` (58 lines, 9 equations).

---

## Participates In

### Conservation Laws
**Module 18 participates in food/material balance** (residues as byproducts):
- Residue availability depends on crop production
- Residues feed into the demand system (bioenergy, feed, material)
- Affects supply balance for residue commodities (`kres`)

### Dependency Chains
**Centrality**: Low-medium (specialized byproduct handler)
- **Depends on**: Module 17 (regional crop production), Module 30 (cluster area), Module 09 (development indicator)
- **Provides to**: Modules 11 (costs), 16 (demand), 21 (trade), 50 (N and P/K budgets), 57 (GHG emissions)
- **Role**: Residue calculator - determines agricultural byproduct biomass, fate, and nutrient flows

### Circular Dependencies
**Zero circular dependencies** - residues are byproducts (crop production -> residues, one-way).

### Modification Safety
**Risk Level**: 🟢 **LOW-MEDIUM RISK** (specialized module, clear interfaces).

**Safe modifications**:
- ✅ Adjust residue-to-product ratios (CGF slope/intercept)
- ✅ Change residue burning scenarios
- ✅ Modify burned/recycled fractions
- ✅ Adjust harvest cost coefficients

**Higher-risk modifications**:
- ⚠️ Changing realization (default <-> flexcluster_jul23) - alters variable dimensionality and shifts which constraints bind
- ⚠️ Removing the translation equation (`q18_translate`) - breaks the residue-group aggregation and would cascade to trade/demand

**Testing**: verify residue availability < crop production (physically consistent); confirm regional N/P/K recycling sums match expected partition of burning/recycling/BG.

---

**Verified Against**: `../modules/18_residues/flexreg_apr16/*.gms` (default body) and `../modules/18_residues/flexcluster_jul23/{declarations,equations,realization}.gms` (alternative summary).
**Verification Method**: Equations and variable signatures copied directly from source; cross-realization comparison via declarations.gms line counts.
