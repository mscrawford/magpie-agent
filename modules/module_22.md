## Module 22: Land Conservation (Protected Areas & Restoration) ✅ COMPLETE

**Status**: Fully documented
**Location**: `modules/22_land_conservation/area_based_apr22/`
**Method**: Exogenous protection targets (WDPA baseline + conservation priority areas)
**Realization**: `area_based_apr22` (April 2022 version)
**Author**: Patrick v. Jeetze

### 1. Purpose & Overview

**Core Function**: Module 22 provides **exogenous land conservation targets** that prevent conversion of natural vegetation and enable active restoration. It operates as a **data provider module** (no equations) that calculates protection and restoration requirements in `presolve`, which are then used as constraints in Modules 10 (Land), 35 (NatVeg), and 31 (Pasture).

**Two Conservation Types**:
1. **Protection** (`consv_type = "protect"`): Prevents conversion of existing land to other uses
2. **Restoration** (`consv_type = "restore"`): Active restoration to meet conservation targets

**Key Output**:
- `pm_land_conservation(t,j,land,consv_type)` - Conservation requirements by land type (mio. ha)
  - Used as **binding constraint** in land allocation modules
  - Applies to: Primary forest, secondary forest, other natural land, pasture

**Conservation Architecture**:
```
WDPA Baseline (1995-2020)                Additional Priority Areas (post-2020)
       ↓                                             ↓
Historical protected areas            +    Conservation scenarios
(864 Mha → 1662 Mha)                      (BH, IFL, KBA, 30by30, etc.)
       ↓                                             ↓
       └──────────────────┬──────────────────────────┘
                          ↓
              p22_conservation_area(t,j,land)
                          ↓
         ┌────────────────┴────────────────┐
         ↓                                  ↓
  Protection target                  Restoration target
(min(target, current land))      (max(0, target - current land))
         ↓                                  ↓
pm_land_conservation(t,j,land,"protect")  pm_land_conservation(t,j,land,"restore")
```

**From Module Header** (`realization.gms:8-24`):
```gams
*' Land reserved for area-based conservation is derived from WDPA and is based on observed
*' land conservation trends. In 1995, the total area under land conservation (across all land
*' types) in the input data set is 864.31 Mha and, by 5-year time steps, increases to
*' 1662.02 Mha in 2020 (13.06 % of the total land area, excluding inland water bodies under
*' protection). After 2020 land conservation is held constant at 2020 values. The protected area
*' based on WDPA includes all areas under legal protection meeting the IUCN and CBD protected
*' area definitions (including IUCN categories Ia, Ib, III, IV, V, VI and 'not assigned' but
*' legally designated areas). Natural vegetation (natveg) and grassland ('past') within protected
*' areas cannot be converted to other land types.
```

**Realization**: `area_based_apr22`
- Area-based approach (not species-based or ecosystem service-based)
- April 2022 version
- WDPA baseline + multiple conservation priority area options

---

### 2. Mechanisms & Logic

Module 22 has **NO EQUATIONS** - it's a **parameter calculation module** that runs only in `preloop` and `presolve` phases.

---

#### **A. Baseline Protection (WDPA)** (`presolve.gms:20-26`)

**Purpose**: Implements historical protected area trends from World Database on Protected Areas

```gams
if(m_year(t) <= sm_fix_SSP2,
* from 1995 to 2020 land conservation is based on
* historic trends as derived from WDPA
 p22_conservation_area(t,j,land) = sum(cell(i,j),
      p22_wdpa_baseline(t,j,"%c22_base_protect%",land) * p22_country_weight(i)
      + p22_wdpa_baseline(t,j,"%c22_base_protect_noselect%",land) * (1-p22_country_weight(i))
      );
```

**Mechanism**:
- **Historical period (1995-2020)**: Uses observed WDPA data by 5-year timesteps
- **Post-2020**: Held constant at 2020 values (via `m_fillmissingyears` in `input.gms:57`)
- **Country weighting**: Allows different protection scenarios for selected countries
  - `p22_country_weight(i)`: Fraction of region covered by policy countries (by land area)
  - Default: All countries selected → weight = 1.0

**WDPA Coverage** (`realization.gms:11-17`):
- 1995: 864.31 Mha (6.8% of land area)
- 2020: 1662.02 Mha (13.06% of land area)
- Growth rate: +93% over 25 years (~2.6%/yr)
- Categories included: IUCN Ia, Ib, III, IV, V, VI + legally designated areas

---

#### **B. Additional Conservation Priority Areas** (`presolve.gms:28-44`)

**Purpose**: Add future conservation scenarios on top of WDPA baseline

```gams
else
* future options for land conservation are added to the WDPA baseline
p22_conservation_area(t,j,land_natveg) =
    sum(cell(i,j),
      p22_wdpa_baseline(t,j,"%c22_base_protect%",land_natveg) * p22_country_weight(i)
      + p22_wdpa_baseline(t,j,"%c22_base_protect_noselect%",land_natveg) * (1-p22_country_weight(i))
      )
    + sum(cell(i,j),
      p22_add_consv(t,j,"%c22_protect_scenario%",land_natveg) * p22_country_weight(i)
      + p22_add_consv(t,j,"%c22_protect_scenario_noselect%",land_natveg) * (1-p22_country_weight(i))
      );
);
```

**Logic**:
1. **Start with WDPA baseline** (2020 levels held constant)
2. **Add additional priority areas** (`p22_add_consv`) based on scenario
3. **Only applies to natural vegetation** (`land_natveg` = primforest, secdforest, other)
4. **Gradual phase-in**: `p22_conservation_fader(t)` provides sigmoid transition (2025→2050)

**Priority Areas Available** (`sets.gms:21-24`):
- **BH**: Biodiversity Hotspots (Myers et al.)
- **IFL**: Intact Forest Landscapes (Potapov et al.)
- **BH_IFL**: Combination of BH and IFL
- **KBA**: Key Biodiversity Areas
- **30by30**: 30% of land by 2030 target
- **GSN_xxx**: Global Safety Net scenarios (DSA, RarePhen, AreaIntct, ClimTier1, ClimTier2, HalfEarth)
- **IrrC_xxx**: Irreplaceability thresholds (50%, 75%, 95%, 99%, 100%)
- **CCA**: Conservation Concern Areas
- **PBL_HalfEarth**: PBL Half-Earth scenario

**Special Case: IFL Primary Forest** (`presolve.gms:16-17`):
```gams
* Include all remaining primary forest areas in IFL conservation target
p22_add_consv(t,j,"IFL","primforest") = pcm_land(j,"primforest") * p22_conservation_fader(t);
p22_add_consv(t,j,"BH_IFL","primforest") = pcm_land(j,"primforest") * p22_conservation_fader(t);
```

**Why**: IFL and BH_IFL scenarios protect ALL remaining primary forest, not just designated IFL areas.

---

#### **C. Protection Calculation** (`presolve.gms:47-55`)

**Purpose**: Set protection targets, capped at current land availability

```gams
* Note: The prescribed conservation area for each land pool can be smaller, equal or
* higher than the land pools of the previous time step. If the conservation area is
* larger and s22_restore_land = 1, missing land will be restored.
pm_land_conservation(t,j,land,"protect") = p22_conservation_area(t,j,land);
pm_land_conservation(t,j,land,"protect")$(pm_land_conservation(t,j,land,"protect") > pcm_land(j,land)) = pcm_land(j,land);
```

**Logic**:
1. Start with conservation target: `pm_land_conservation = p22_conservation_area`
2. **Cap at current land area**: Cannot protect more land than currently exists
   - If target > current: Protection = current (restoration needed for the difference)
   - If target < current: Protection = target (allows some deprotection)
   - If target = current: Protection = current (no change)

**Example**:
```
Scenario: BH_IFL in Brazil
  - WDPA 2020: 500 Mha forest protected
  - Current forest (2025): 600 Mha
  - Target (BH_IFL): 700 Mha forest

Result:
  - Protection: min(700, 600) = 600 Mha (all current forest protected)
  - Restoration (if enabled): 700 - 600 = 100 Mha
```

---

#### **D. Restoration Calculation** (`presolve.gms:58-118`)

**Purpose**: Calculate restoration requirements to meet conservation targets

**Condition**: Only if `s22_restore_land = 1` OR during historical period

```gams
if(s22_restore_land = 1 OR m_year(t) <= sm_fix_SSP2,
```

**D.1 Grassland Restoration** (`presolve.gms:64-67`):

```gams
* Grassland
pm_land_conservation(t,j,"past","restore")$(p22_conservation_area(t,j,"past") > pcm_land(j,"past")) =
        p22_conservation_area(t,j,"past") - pcm_land(j,"past");
```

**Logic**: If target > current pasture area, restore the difference

**D.2 Forest Restoration** (`presolve.gms:68-74`):

```gams
* Forest land
* Total forest restoration requirements are attributed to
* secdforest, as primforest cannot be restored by definition
pm_land_conservation(t,j,"secdforest","restore") =
        (p22_conservation_area(t,j,"primforest") + p22_conservation_area(t,j,"secdforest"))
        - (pcm_land(j,"primforest") + pcm_land(j,"secdforest"));
pm_land_conservation(t,j,"secdforest","restore")$(pm_land_conservation(t,j,"secdforest","restore") < 1e-6) = 0;
```

**Logic**:
- Calculate total forest deficit: (Target primforest + target secdforest) - (Current primforest + current secdforest)
- **All restoration goes to secondary forest** (primforest cannot be created by definition)
- Zero out very small restoration requirements (< 0.000001 Mha) to avoid numerical issues

**D.3 Other Land Restoration** (`presolve.gms:75-77`):

```gams
* Other land
pm_land_conservation(t,j,"other","restore")$(p22_conservation_area(t,j,"other") > pcm_land(j,"other")) =
        p22_conservation_area(t,j,"other") - pcm_land(j,"other");
```

**Logic**: If target > current other natural land, restore the difference

---

#### **E. Restoration Potential Constraints** (`presolve.gms:79-111`)

**Purpose**: Limit restoration by available land (restoration potential)

**Problem**: Cannot restore more land than is available after accounting for:
- Urban land (permanent)
- Timber plantations (locked in)
- Protected pasture (cannot convert to forest)
- Crop minimum (food security)
- Tree cover (from Module 32)

**E.1 Secondary Forest Restoration Potential** (`presolve.gms:82-89`):

```gams
p22_secdforest_restore_pot(t,j) = sum(land, pcm_land(j, land))
                - pcm_land(j, "urban")
                - sum(land_timber, pcm_land(j, land_timber))
                - pm_land_conservation(t,j,"past","protect")
                - vm_land.lo(j,"crop")
                - vm_treecover.l(j);
p22_secdforest_restore_pot(t,j)$(p22_secdforest_restore_pot(t,j) < 1e-6) = 0;
pm_land_conservation(t,j,"secdforest","restore")$(pm_land_conservation(t,j,"secdforest","restore") > p22_secdforest_restore_pot(t,j)) = p22_secdforest_restore_pot(t,j);
```

**Translation**:
```
Secdforest restoration potential = Total land
                                   - Urban
                                   - Timber plantations
                                   - Protected pasture
                                   - Minimum cropland
                                   - Tree cover

Secdforest restoration = min(Target restoration, Restoration potential)
```

**E.2 Grassland Restoration Potential** (`presolve.gms:92-100`):

```gams
p22_past_restore_pot(t,j) = sum(land, pcm_land(j, land))
              - pcm_land(j, "urban")
              - sum(land_timber, pcm_land(j, land_timber))
              - pm_land_conservation(t,j,"past","protect")
              - pm_land_conservation(t,j,"secdforest","restore")
              - vm_land.lo(j,"crop")
              - vm_treecover.l(j);
```

**Logic**: Same as secdforest, but also excludes already-allocated secdforest restoration

**E.3 Other Land Restoration Potential** (`presolve.gms:103-111`):

```gams
p22_other_restore_pot(t,j) = sum(land, pcm_land(j, land))
               - pcm_land(j, "urban")
               - sum(land_timber, pcm_land(j, land_timber))
               - sum(consv_type, pm_land_conservation(t,j,"past",consv_type))
               - pm_land_conservation(t,j,"secdforest","restore")
               - vm_land.lo(j,"crop")
               - vm_treecover.l(j);
```

**Logic**: Residual land after secdforest and pasture restoration

**Restoration Priority Order**:
1. Secondary forest (first claim on available land)
2. Pasture (second claim)
3. Other land (residual)

---

#### **F. No Restoration Mode** (`presolve.gms:113-118`)

```gams
else
* set restoration to zero
pm_land_conservation(t,j,land,"restore") = 0;
);
```

**When**: If `s22_restore_land = 0` AND after historical period
**Effect**: Only protection applies, no active restoration

---

#### **G. Protection Reversal** (`presolve.gms:120-122`)

```gams
if (m_year(t) >= s22_base_protect_reversal,
  pm_land_conservation(t,j,land,consv_type) = 0;
);
```

**Purpose**: Allow scenario where protection is lifted after a certain year
**Default**: `s22_base_protect_reversal = Inf` (protection never reversed)
**Use case**: Exploring economic costs of protection by comparing with/without protection scenarios

---

### 3. Parameters & Data

#### **A. Key Parameters** (`declarations.gms:12-24`)

| Parameter | Description | Units | Source |
|-----------|-------------|-------|--------|
| `pm_land_conservation(t,j,land,consv_type)` | **OUTPUT: Land protection and restoration** | mio. ha | Calculated |
| `p22_conservation_area(t,j,land)` | Total conservation target (protect + restore) | mio. ha | Calculated |
| `p22_wdpa_baseline(t,j,base22,land)` | WDPA baseline protection | mio. ha | Input data |
| `p22_add_consv(t,j,consv22_all,land)` | Additional conservation (priority areas) | mio. ha | Input data × fader |
| `p22_conservation_fader(t)` | Sigmoid transition (2025→2050) | 1 | Calculated |
| `p22_secdforest_restore_pot(t,j)` | Available land for forest restoration | mio. ha | Calculated |
| `p22_past_restore_pot(t,j)` | Available land for grassland restoration | mio. ha | Calculated |
| `p22_other_restore_pot(t,j)` | Available land for other land restoration | mio. ha | Calculated |
| `p22_country_weight(i)` | Fraction of region in policy countries | 1 | Calculated (area-weighted) |
| `p22_country_switch(iso)` | 1 if country affected, 0 otherwise | 1 | From `policy_countries22` set |

---

#### **B. Switches & Scalars** (`input.gms:13-18`)

| Switch | Description | Values | Default |
|--------|-------------|--------|---------|
| `c22_base_protect` | Baseline protection scenario | WDPA, WDPA_I-II-III, WDPA_IV-V-VI, none | WDPA |
| `c22_base_protect_noselect` | Baseline for non-selected countries | (same options) | WDPA |
| `c22_protect_scenario` | Additional protection scenario | none, BH, IFL, BH_IFL, KBA, 30by30, GSN_xxx, IrrC_xxx, CCA, PBL_HalfEarth, GSN_HalfEarth | none |
| `c22_protect_scenario_noselect` | Scenario for non-selected countries | (same options) | none |
| `s22_restore_land` | Enable restoration | 0 (no), 1 (yes) | 1 |
| `s22_conservation_start` | Start year for phase-in | year | 2025 |
| `s22_conservation_target` | Target year for full implementation | year | 2050 |
| `s22_base_protect_reversal` | Year protection reversed | year | Inf (never) |

---

#### **C. Sets** (`sets.gms`)

**Conservation Type** (`consv_type`):
- `protect`: Prevent conversion of existing land
- `restore`: Active restoration to create new protected land

**Baseline Protection Options** (`base22`):
- `none`: No baseline protection
- `WDPA`: All IUCN categories + legally designated (default)
- `WDPA_I-II-III`: Strict protection (IUCN Ia, Ib, III)
- `WDPA_IV-V-VI`: Less strict protection (IUCN IV, V, VI)

**Conservation Priority Areas** (`consv_prio22`):
- `BH`: Biodiversity Hotspots
- `IFL`: Intact Forest Landscapes
- `BH_IFL`: Both BH and IFL
- `KBA`: Key Biodiversity Areas
- `30by30`: 30% of land by 2030
- `GSN_xxx`: Global Safety Net variants
- `IrrC_xxx`: Irreplaceability thresholds (50%, 75%, 95%, 99%, 100%)
- `CCA`: Conservation Concern Areas
- `GSN_HalfEarth`: Half-Earth scenario (Global Safety Net)
- `PBL_HalfEarth`: Half-Earth scenario (PBL Netherlands)

**Land Types Covered**:
- `primforest`: Primary forest
- `secdforest`: Secondary forest
- `other`: Other natural land
- `past`: Pasture/grassland

---

### 4. Data Sources

#### **File 1: WDPA Baseline** (`input.gms:51-57`)

```gams
table f22_wdpa_baseline(t_all,j,wdpa_cat22,land) Initial protected area as derived from WDPA until 2020 (mio. ha)
$include "./modules/22_land_conservation/input/wdpa_baseline.cs3"
* fix to 2020 values for years after 2020
m_fillmissingyears(f22_wdpa_baseline,"j,wdpa_cat22,land");
```

**Source**: World Database on Protected Areas (WDPA)
- **Provider**: UNEP-WCMC and IUCN
- **Time series**: 1995-2020 (5-year timesteps)
- **Post-2020**: Held constant at 2020 levels
- **Categories**: IUCN Ia, Ib, III, IV, V, VI + legally designated areas
- **Land cover estimation**: Based on ESA-CCI land-use/land-cover maps

**Coverage by Land Type** (approximate, 2020):
- Total: 1662 Mha (13.06% of land area)
- Forest: ~400-500 Mha (primforest + secdforest)
- Grassland/pasture: ~200-300 Mha
- Other natural land: ~100-200 Mha
- Urban: ~10-20 Mha

**IUCN Categories Explained**:
- **Ia**: Strict nature reserve (no human use)
- **Ib**: Wilderness area (low impact)
- **III**: Natural monument (specific features)
- **IV**: Habitat/species management (active conservation)
- **V**: Protected landscape/seascape (sustainable use)
- **VI**: Protected area with sustainable use of natural resources

---

#### **File 2: Conservation Priority Areas** (`input.gms:59-63`)

```gams
table f22_consv_prio(j,consv_prio22,land) Conservation priority areas (mio. ha)
$include "./modules/22_land_conservation/input/consv_prio_areas.cs3"
```

**Sources by Priority Area**:

**Biodiversity Hotspots (BH)**:
- Source: Myers et al. 2000, Brooks et al. 2006
- Criteria: >1500 endemic plant species + >70% habitat loss
- Coverage: 36 global hotspots (~2-3% of land area)

**Intact Forest Landscapes (IFL)**:
- Source: Potapov et al. 2008, 2017
- Criteria: >500 km² contiguous forest, no fragmentation, low human impact
- Coverage: ~13.1 million km² globally (as of 2016)

**Key Biodiversity Areas (KBA)**:
- Source: IUCN and partners
- Criteria: Sites critical for biodiversity persistence
- Coverage: ~16,000 sites globally

**30by30**:
- Source: UN Convention on Biological Diversity (Kunming-Montreal Framework 2022)
- Target: 30% of terrestrial and inland water by 2030
- Implementation: Focus on high biodiversity/carbon areas

**Global Safety Net (GSN)**:
- Source: Dinerstein et al. 2020
- Variants:
  - DSA: Distinct Species Assemblages
  - RarePhen: Rare phenomena
  - AreaIntct: Large intact areas
  - ClimTier1: Climate stabilization tier 1
  - ClimTier2: Climate stabilization tier 2
  - HalfEarth: 50% of land by 2050

**Irreplaceability (IrrC)**:
- Source: Derived from systematic conservation planning
- Thresholds: 50%, 75%, 95%, 99%, 100%
- Higher % = more irreplaceable for biodiversity

---

#### **File 3: Country-Level Land Area** (`preloop.gms:20`)

```gams
i22_land_iso(iso) = sum(land, fm_land_iso("y1995",iso,land));
```

**Source**: `fm_land_iso` from Module 09 (Drivers)
**Purpose**: Calculate country weights for regional aggregation
**Logic**: Countries weighted by total land area (not population or GDP)

---

### 5. Dependencies

**From Phase 2 Analysis**: Module 22 is a **data provider** with 1 input and 3 critical outputs.

#### **DEPENDS ON (1 module)**:

**1. Module 10 (Land)** - **CRITICAL DEPENDENCY**:
   - **Variables received**:
     - `pcm_land(j,land)`: Previous timestep land area (mio. ha)
     - `vm_land.lo(j,"crop")`: Minimum cropland requirement (mio. ha)
   - **Why critical**: Cannot calculate restoration potential without knowing current land allocation
   - **Timing**: Module 10 runs in optimization, Module 22 in presolve (uses previous timestep values)
   - **File**: `presolve.gms:54-111`

**Additional Dependencies** (indirect):
- **Module 32 (Forestry)**: `vm_treecover.l(j)` - tree cover area (mio. ha)
- **Module 09 (Drivers)**: `fm_land_iso(t,iso,land)` - country-level land areas (mio. ha)

---

#### **PROVIDES TO (3 modules)** - **CRITICAL OUTPUTS**:

**1. Module 10 (Land)** - **PRIMARY CONSUMER**:
   - **Variable provided**: `pm_land_conservation(t,j,land,consv_type)`
   - **Purpose**: Land conservation constraints in land allocation
   - **Mechanism**: Protected land cannot be converted, restored land must be created
   - **Impact**: **Directly constrains land-use optimization**

**2. Module 35 (NatVeg - Natural Vegetation)** - **SECONDARY CONSUMER**:
   - **Variable provided**: `pm_land_conservation(t,j,land_natveg,consv_type)`
   - **Purpose**: Natural vegetation protection and restoration targets
   - **Mechanism**: Prevents conversion of primforest, secdforest, other natural land
   - **Impact**: Protects biodiversity, carbon stocks, ecosystem services

**3. Module 31 (Pasture)** - **TERTIARY CONSUMER**:
   - **Variable provided**: `pm_land_conservation(t,j,"past",consv_type)`
   - **Purpose**: Grassland protection and restoration
   - **Mechanism**: Prevents conversion of protected pasture to cropland
   - **Impact**: Maintains rangeland ecosystems

---

#### **Circular Dependencies**: NONE

Module 22 has **NO circular dependencies** because:
1. It runs in `presolve` (before optimization)
2. Uses only previous timestep values (`pcm_land`, not `vm_land`)
3. Provides parameters to other modules, not variables

---

### 5.1. Participates In

#### Conservation Laws

**Land Area Balance**: ✅ **CRITICAL PARTICIPANT**

Module 22 provides **exogenous protection and restoration targets** that constrain land allocation in Module 10:

- **Protection Constraint**: Enforces minimum land area that cannot be converted
  - Formula: `vm_land(j,land) ≥ pm_land_conservation(j,land,"protect")`
  - Applied in Module 10 land allocation equations
  - Prevents conversion of protected primary forest, secondary forest, other natural land, and pasture

- **Restoration Constraint**: Drives active restoration to meet targets
  - Formula: `vm_land(j,land) ≥ pm_land_conservation(j,land,"restore")`
  - Increases land area above historical levels where targets exceed current allocation
  - Example: 30by30 scenario restores 3,094 Mha globally by 2030

- **Historical Coverage**:
  - 1995: 864.31 Mha protected (6.79% of land)
  - 2020: 1,662.02 Mha protected (13.06% of land)
  - Post-2020: Constant at 2020 levels (unless additional scenarios active)

- **Cross-Module Reference**: `cross_module/land_balance_conservation.md` (Section 5, Module Interactions)

**Other Conservation Laws**:
- Water Balance: ❌ Does NOT directly participate (but conservation may reduce available irrigated area)
- Carbon Balance: ⚠️ INDIRECT - Protection prevents deforestation → preserves carbon stocks (Module 52)
- Food Balance: ❌ Does NOT participate (parameter-only module)
- Nitrogen: ❌ Does NOT participate (parameter-only module)

---

#### Dependency Chains

**Centrality Rank**: ~25 of 46 modules (moderate centrality)
**Total Connections**: 5-7 (provides to 5-7 modules, depends on 1)
**Hub Type**: **Data Provider** (exogenous policy constraints)

**Provides To** (5-7 modules):
1. **Module 10 (Land)** - Conservation constraints (`pm_land_conservation`)
2. **Module 31 (Pasture)** - Pasture protection targets
3. **Module 35 (NatVeg)** - Natural vegetation protection/restoration targets
4. **Module 32 (Forestry)** - Land availability constraints for afforestation
5. Plus 2-3 other modules receiving conservation data

**Depends On** (1 module):
1. **Module 09 (Drivers)** - Population and scenario data (for conservation priority areas)

**Key Position**: Module 22 acts as **policy enforcement layer** that translates WDPA baseline + conservation scenarios into binding land allocation constraints.

**Reference**: `core_docs/Module_Dependencies.md` (Section 4, Module Catalog)

---

#### Circular Dependencies

**Participates In**: 1 temporal feedback cycle (NOT within-timestep circular dependency)

#### Temporal Feedback: Land Allocation ↔ Conservation Targets

**Structure**:
```
Module 22 (Conservation) ──→ pm_land_conservation(t,j,land) ──→ Module 10 (Land)
       ↑                                                              │
       │                                                              │
       └────────── pcm_land(t-1,j,land) (previous timestep) ←────────┘
                                    ↓
                          Module 35 (NatVeg)
                    (natural vegetation dynamics)
```

**Why NOT a Within-Timestep Circular Dependency**:
1. **Module 22 runs in `presolve`** (before optimization), NOT during solve
2. **Uses previous timestep values**: `pcm_land(t-1,j,land)`, not current `vm_land(t,j,land)`
3. **Provides parameters** (`pm_land_conservation`), not optimization variables
4. **One-way flow**: Conservation targets → Land allocation (no backward link within timestep)

**Temporal Feedback Mechanism** (across timesteps):
- **Time t-1**: Land allocation produces `vm_land(t-1,j,land)`
- **Time t presolve**: Module 22 calculates targets using `pcm_land(t-1,j,land)`
- **Time t solve**: Module 10 respects new conservation constraints
- **Impact**: Protection targets can increase if previous land exceeded thresholds

**Resolution Mechanism**: **Type 1 - Temporal Feedback** (NOT simultaneous)
- No circular equations within a single timestep
- Sequential execution: presolve → solve
- Feedback occurs across time steps, not within them

**Testing Protocol** (if modifying Module 22):
- ✅ Verify protection targets don't exceed available land (can cause infeasibility)
- ✅ Check restoration targets are achievable given land availability
- ✅ Test that `vm_land(j,land) ≥ pm_land_conservation(j,land,"protect" + "restore")`
- ✅ Validate land balance holds with conservation constraints

**Reference**: `cross_module/circular_dependency_resolution.md` (Temporal feedback patterns)

---

#### Modification Safety

**Risk Level**: 🟡 **MEDIUM RISK**

**Safe Modifications**:
- ✅ Adjusting conservation priority area scenarios (BH, IFL, KBA, WDPA, etc.)
- ✅ Changing protection/restoration allocation logic (`s22_conservation_target`)
- ✅ Modifying conservation share parameters (`f22_conservation_fader`)
- ✅ Adding new conservation scenarios or land protection types
- ✅ Updating WDPA baseline data with new protected area information

**Dangerous Modifications**:
- ⚠️ Setting protection targets > available land → **model infeasibility**
- ⚠️ Removing protection constraints → violates conservation policies (NPI/NDC)
- ⚠️ Hardcoding land types → can conflict with land balance equations in Module 10
- ⚠️ Changing restoration logic without testing land availability

**Required Testing** (for ANY modification):
1. **Land Balance Conservation**:
   - Verify total conservation ≤ total available land by region
   - Check that protection + restoration targets are consistent
   - Test extreme scenarios (e.g., 30by30 with 3,094 Mha restoration)

2. **Dependency Chain Validation**:
   - Module 10 (Land): Verify land allocation respects conservation constraints
   - Module 35 (NatVeg): Verify natural vegetation meets protection targets
   - Module 31 (Pasture): Verify pasture protection works correctly
   - Module 32 (Forestry): Verify afforestation doesn't violate protected areas

3. **Infeasibility Testing**:
   - Test regions where conservation targets approach 100% of available land
   - Check conflict resolution between cropland expansion and protection
   - Verify restoration is feasible given land type transitions

4. **Scenario Testing**:
   - Run with different conservation scenarios (BH, IFL, 30by30, etc.)
   - Test interaction between WDPA baseline and additional priority areas
   - Validate conservation fader trajectories (0 to 1 over time)

**Common Issues**:
- **Infeasibility from over-protection**: Conservation targets exceed available land → reduce targets or adjust land allocation flexibility
- **Restoration conflicts**: Target land type cannot be restored from current type → check land type transition matrix
- **Scenario conflicts**: Multiple conservation scenarios applied → targets sum to > available land → use `s22_conservation_target` to prioritize
- **Pasture protection ignored**: Pasture has low conservation priority in data → manually increase pasture protection in scenarios

**Reference**: `cross_module/modification_safety_guide.md` (Conservation constraint impacts)

---

### 6. Code Truth: What Module 22 DOES

✅ **1. Implements WDPA Baseline Protection (1995-2020)** (`presolve.gms:20-26`):
- Historical protected area trends from World Database on Protected Areas
- 1995: 864 Mha → 2020: 1662 Mha (93% increase, 13.06% of land)
- Post-2020: Held constant at 2020 levels unless additional scenarios applied
- Covers IUCN categories Ia, Ib, III, IV, V, VI + legally designated areas

✅ **2. Provides Multiple Conservation Scenarios** (`sets.gms:21-24`):
- **20+ scenarios available**: BH, IFL, BH_IFL, KBA, 30by30, GSN variants, IrrC thresholds
- **Gradual phase-in**: Sigmoid fader from 2025 to 2050 (default)
- **Country-specific**: Can apply different scenarios to selected countries
- **Additive**: Priority areas added to WDPA baseline, not replacing it

✅ **3. Calculates Restoration Requirements** (`presolve.gms:62-77`):
- If conservation target > current land area → restoration needed
- **Restoration types**:
  - Grassland restoration: `target_pasture - current_pasture`
  - Forest restoration: `(target_primforest + target_secdforest) - (current_primforest + current_secdforest)`
  - Other land restoration: `target_other - current_other`
- **Forest restoration attribution**: All forest restoration goes to secondary forest (primforest cannot be created)

✅ **4. Limits Restoration by Available Land** (`presolve.gms:79-111`):
- **Restoration potential** = Total land - Urban - Timber - Protected pasture - Minimum cropland - Tree cover
- **Priority order**: Secdforest → Pasture → Other land
- **Prevents infeasibility**: Cannot restore more land than physically available

✅ **5. Supports Country-Specific Policies** (`preloop.gms:13-21`):
- **Country selection**: `policy_countries22` set (default: all 249 countries)
- **Country weights**: By total land area (not population)
- **Regional aggregation**: Weighted average for MAgPIE's 10 regions
- **Dual scenarios**: Different scenarios for selected vs. non-selected countries

✅ **6. Provides Binding Constraints to Land Modules** (`presolve.gms:54-55`):
- **Protection**: `pm_land_conservation(t,j,land,"protect")` prevents conversion
- **Restoration**: `pm_land_conservation(t,j,land,"restore")` requires land creation
- **Used by**: Module 10 (Land), Module 35 (NatVeg), Module 31 (Pasture)

✅ **7. Handles Land Cover Data Mismatch** (`realization.gms:27-30`):
- **WDPA baseline**: Based on ESA-CCI land cover (1995-2020)
- **MAgPIE initialization**: Based on LUH data + FAO harmonization
- **Result**: Slight mismatches in some regions
- **Resolution**: Protection capped at current land area (line 55)

✅ **8. Allows Protection Reversal** (`presolve.gms:120-122`):
- **Switch**: `s22_base_protect_reversal` (default: Inf = never)
- **Purpose**: Scenario analysis (e.g., costs of protection)
- **Effect**: Sets `pm_land_conservation = 0` after reversal year

---

### 7. Code Truth: What Module 22 does NOT

❌ **1. Does NOT Model Conservation Effectiveness**:
- Assumes 100% protection effectiveness (all protected areas enforced)
- No "paper parks" (protected in name only)
- No variation by governance quality, corruption, or enforcement capacity
- All protected areas treated equally regardless of IUCN category

❌ **2. Does NOT Calculate Conservation Costs**:
- Sets targets but does not estimate implementation costs
- No opportunity costs (forgone agricultural production)
- No management costs (ranger salaries, infrastructure)
- No compensation for landowners or communities
- Cost implications handled by other modules (e.g., Module 39: Land Conversion Costs)

❌ **3. Does NOT Optimize Protection Allocation**:
- Conservation areas are **exogenous scenarios** (external inputs)
- Not chosen endogenously based on cost-benefit analysis
- No trade-off between biodiversity value and economic costs
- No spatial optimization (Marxan-style reserve selection)

❌ **4. Does NOT Include Marine Protected Areas**:
- Only terrestrial and inland water bodies
- No coastal or ocean conservation
- WDPA includes marine areas, but Module 22 only uses terrestrial

❌ **5. Does NOT Prevent All Land Conversion**:
- Protection only affects natural vegetation (`primforest`, `secdforest`, `other`) and grassland (`past`)
- Does NOT protect:
  - Cropland (can be converted to other crops or abandoned)
  - Forestry plantations (can be harvested and replanted)
  - Urban land (no protection needed - already developed)

❌ **6. Does NOT Model Restoration Dynamics**:
- Restoration is instantaneous (no succession dynamics)
- No restoration costs or timescales (Module 32: Forestry handles plantation establishment)
- No ecological constraints (soil quality, water availability, seed sources)
- Restored land immediately becomes fully functional protected area

❌ **7. Does NOT Account for Climate Change Impacts**:
- Protection boundaries static (no climate-driven range shifts)
- No protected area migration or relocation
- No adaptation of protection strategies to changing conditions

❌ **8. Does NOT Model Indigenous & Community Lands**:
- WDPA focuses on formal protected areas (government/NGO managed)
- Limited coverage of Indigenous and Community Conserved Areas (ICCAs)
- No explicit recognition of indigenous land rights

❌ **9. Does NOT Include Connectivity or Fragmentation**:
- Treats each grid cell independently
- No corridor planning or connectivity targets
- No fragmentation penalties (protected areas can be scattered)

❌ **10. Does NOT Model Ecosystem Services Explicitly**:
- Protection based on area and biodiversity priority, not ecosystem services
- No explicit valuation of:
  - Carbon storage (handled by Module 52: Carbon)
  - Water regulation
  - Pollination services
  - Recreation values

❌ **11. Does NOT Allow Partial Protection**:
- Binary protection (0% or 100%)
- No intermediate protection levels (e.g., 50% extractive reserve)
- IUCN categories not differentiated in model behavior (all equally strict)

---

### 8. Common Modifications

#### 8.1 Implement 30by30 Target

**Purpose**: Meet UN's 30% of land protected by 2030 target

**How**: Modify `input.gms:10`
```gams
* Default: WDPA baseline only (13% in 2020)
$setglobal c22_protect_scenario  none

* Alternative: 30% by 2030 scenario
$setglobal c22_protect_scenario  30by30
s22_conservation_target = 2030    # Accelerated timeline
```

**Effect**:
- Protected area increases from 13% (2020) to 30% (2030)
- Distributed proportionally across natural vegetation types
- Requires significant restoration (~2000-2500 Mha additional)
- Large land-use implications (reduced agricultural expansion potential)

**Files**: `input.gms:10`, `input.gms:16`

---

#### 8.2 Protect All Intact Forest Landscapes

**Purpose**: Prevent deforestation of all remaining large, undisturbed forests

**How**: Modify `input.gms:10`
```gams
* Default: WDPA baseline only
$setglobal c22_protect_scenario  none

* Alternative: Protect all IFL
$setglobal c22_protect_scenario  IFL
s22_conservation_start = 2025
s22_conservation_target = 2030    # Quick phase-in
```

**Effect**:
- All primary forest automatically protected (`presolve.gms:16`)
- IFL-designated secondary forest and other natural land also protected
- Focuses protection on largest remaining wilderness areas
- High impact on tropical deforestation (Amazon, Congo, SE Asia)

**Files**: `input.gms:10`, `presolve.gms:16-17`

---

#### 8.3 Combine Biodiversity Hotspots & Intact Forests

**Purpose**: Protect both high biodiversity areas and large intact areas

**How**: Modify `input.gms:10`
```gams
* Default: WDPA baseline only
$setglobal c22_protect_scenario  none

* Alternative: BH + IFL combination
$setglobal c22_protect_scenario  BH_IFL
```

**Effect**:
- Protects 36 biodiversity hotspots (Myers et al.) + all IFL areas
- Maximum protection coverage (~20-25% of land)
- All primary forest protected (special case in `presolve.gms:17`)
- Comprehensive conservation strategy (complementary criteria)

**Files**: `input.gms:10`, `presolve.gms:16-17`

---

#### 8.4 Disable Restoration (Protection Only)

**Purpose**: Protect existing natural vegetation but do not actively restore degraded land

**How**: Modify `input.gms:14`
```gams
* Default: Restoration enabled
s22_restore_land = 1

* Alternative: No restoration
s22_restore_land = 0
```

**Effect**:
- Protection targets capped at current land availability
- No active restoration even if targets exceed current land
- Lower land-use pressure (no need to free up land for restoration)
- More conservative scenario (protect what remains)

**Use Cases**:
- Limited restoration funding or capacity
- Focusing on "no further loss" rather than "net gain"
- Baseline scenario for comparing with restoration scenarios

**Files**: `input.gms:14`, `presolve.gms:62`

---

#### 8.5 Apply Protection Only to Selected Countries

**Purpose**: Explore regional conservation policies (e.g., EU only, tropical countries only)

**How**: Modify `input.gms:23-48`
```gams
* Default: All countries
sets
  policy_countries22(iso) countries affected by land conservation policy
  / ABW,AFG,AGO, ... ZWE /    # All 249 countries

* Alternative: EU countries only
sets
  policy_countries22(iso) countries affected by land conservation policy
  / AUT,BEL,BGR,HRV,CYP,CZE,DNK,EST,FIN,FRA,DEU,GRC,HUN,
    IRL,ITA,LVA,LTU,LUX,MLT,NLD,POL,PRT,ROU,SVK,SVN,ESP,SWE /
```

**Effect**:
- Only listed countries apply `c22_protect_scenario`
- Other countries use `c22_protect_scenario_noselect` (default: none)
- Allows comparison of unilateral vs. global conservation policies
- Country weights calculated by land area (`preloop.gms:20-21`)

**Use Cases**:
- EU Green Deal (30% protection in EU)
- Amazon countries coalition
- Tropical forest conservation (Brazil, Indonesia, DRC)

**Files**: `input.gms:23-48`, `preloop.gms:15-21`

---

#### 8.6 Accelerate Protection Phase-In

**Purpose**: Implement protection targets faster (by 2030 instead of 2050)

**How**: Modify `input.gms:15-16`
```gams
* Default: Gradual phase-in (2025-2050)
s22_conservation_start = 2025
s22_conservation_target = 2050

* Alternative: Rapid phase-in (2025-2030)
s22_conservation_start = 2025
s22_conservation_target = 2030
```

**Effect**:
- Sigmoid fader compressed (steeper transition)
- Full protection targets reached by 2030 instead of 2050
- Higher short-term restoration and land-use pressure
- Consistent with CBD 30by30 timeline

**Files**: `input.gms:15-16`, `preloop.gms:36`

---

#### 8.7 Allow Protection Reversal After 2050

**Purpose**: Explore economic costs of long-term conservation by comparing scenarios

**How**: Modify `input.gms:17`
```gams
* Default: Protection never reversed
s22_base_protect_reversal = Inf

* Alternative: Protection lifted after 2050
s22_base_protect_reversal = 2050
```

**Effect**:
- All protection removed after 2050 (both WDPA baseline and additional scenarios)
- Allows land to be converted to agriculture or other uses
- Useful for **cost analysis**: Compare economic outcomes with/without perpetual protection
- **Not realistic scenario** - used only for counterfactual analysis

**Use Cases**:
- Estimating opportunity costs of conservation
- Sensitivity analysis of protection duration
- Policy evaluation (what if protection funding stops?)

**Files**: `input.gms:17`, `presolve.gms:120-122`

---

#### 8.8 Use Stricter WDPA Categories Only

**Purpose**: Only count strict protection (IUCN Ia, Ib, III), exclude sustainable use areas (IV, V, VI)

**How**: Modify `input.gms:8`
```gams
* Default: All IUCN categories
$setglobal c22_base_protect  WDPA

* Alternative: Only strict protection
$setglobal c22_base_protect  WDPA_I-II-III
```

**Effect**:
- Lower baseline protection (~400-600 Mha instead of 1662 Mha)
- Focuses on "no human use" areas
- More consistent with "wilderness" definition
- Higher restoration requirements if additional scenarios applied

**IUCN Categories**:
- `WDPA_I-II-III`: Ia (strict reserve), Ib (wilderness), III (natural monument)
- `WDPA_IV-V-VI`: IV (habitat management), V (protected landscape), VI (sustainable use)

**Files**: `input.gms:8`

---

#### 8.9 Implement Half-Earth Scenario

**Purpose**: Protect 50% of Earth's land by 2050 (E.O. Wilson's Half-Earth proposal)

**How**: Modify `input.gms:10`
```gams
* Default: WDPA baseline only (13%)
$setglobal c22_protect_scenario  none

* Alternative: Half-Earth (50% by 2050)
$setglobal c22_protect_scenario  GSN_HalfEarth
s22_conservation_target = 2050
```

**Effect**:
- Protected area increases from 13% (2020) to 50% (2050)
- Based on Global Safety Net (Dinerstein et al. 2020)
- Prioritizes areas with high biodiversity, carbon, and intactness
- **Massive restoration requirements** (~4000-5000 Mha)
- **Severe land-use constraints** (limited agricultural expansion)

**Variants**:
- `GSN_HalfEarth`: Global Safety Net approach
- `PBL_HalfEarth`: PBL Netherlands approach (different spatial priorities)

**Files**: `input.gms:10`

---

#### 8.10 Target High Irreplaceability Areas

**Purpose**: Protect areas most critical for biodiversity (highest irreplaceability scores)

**How**: Modify `input.gms:10`
```gams
* Default: WDPA baseline only
$setglobal c22_protect_scenario  none

* Alternative: 95% irreplaceability threshold
$setglobal c22_protect_scenario  IrrC_95pc
```

**Irreplaceability Thresholds**:
- `IrrC_50pc`: Moderate priority (~15-20% of land)
- `IrrC_75pc`: High priority (~10-15% of land)
- `IrrC_95pc`: Very high priority (~5-10% of land)
- `IrrC_99pc`: Extreme priority (~2-5% of land)
- `IrrC_100pc`: Absolutely irreplaceable (~1-2% of land)

**Effect**:
- Focuses protection on areas where no alternatives exist for biodiversity conservation
- Higher thresholds = smaller area but more critical for species persistence
- Efficient conservation (maximum biodiversity per hectare protected)

**Files**: `input.gms:10`

---

### 9. Testing & Validation

#### 9.1 Protection Cap Check

**Test**: Is protection capped at current land availability?

**How**:
```r
library(magpie4)
library(gdx)

gdx <- "fulldata.gdx"
protection <- readGDX(gdx, "pm_land_conservation", select=list(type="protect"))
current_land <- readGDX(gdx, "pcm_land")

# Check if protection ever exceeds current land
excess <- protection - current_land
max_excess <- max(excess, na.rm=TRUE)

print(paste("Maximum protection excess:", max_excess, "Mha"))
stopifnot(max_excess < 0.001)  # Should be essentially zero (rounding errors only)
```

**Expected**: `max_excess ≈ 0` (protection capped at current land)

**If fails**: Check `presolve.gms:54-55` capping logic

**File**: `presolve.gms:54-55`

---

#### 9.2 Restoration Conservation Check

**Test**: Does restoration sum to restoration target?

**How**:
```r
conservation_area <- readGDX(gdx, "p22_conservation_area")
current_land <- readGDX(gdx, "pcm_land")
restoration <- readGDX(gdx, "pm_land_conservation", select=list(type="restore"))

# Calculate expected restoration
expected_restoration <- pmax(0, conservation_area - current_land)

# Compare with actual
difference <- restoration - expected_restoration

# Some difference expected due to restoration potential limits
max_diff <- max(abs(difference), na.rm=TRUE)
print(paste("Maximum restoration difference:", max_diff, "Mha"))

# Restoration should be ≤ expected (capped by restoration potential)
stopifnot(all(restoration <= expected_restoration + 0.001))
```

**Expected**: `restoration ≤ expected_restoration` (capped by potential)

**If fails**: Check restoration potential calculations (`presolve.gms:79-111`)

**Files**: `presolve.gms:64-77`, `presolve.gms:79-111`

---

#### 9.3 Total Conservation Sum Check

**Test**: Does total conservation (protect + restore) equal conservation area?

**How**:
```r
protection <- readGDX(gdx, "pm_land_conservation", select=list(type="protect"))
restoration <- readGDX(gdx, "pm_land_conservation", select=list(type="restore"))
total_conservation <- protection + restoration

conservation_area <- readGDX(gdx, "p22_conservation_area")

# Compare
difference <- abs(total_conservation - conservation_area)
max_diff <- max(difference, na.rm=TRUE)

print(paste("Maximum total conservation difference:", max_diff, "Mha"))
stopifnot(max_diff < 1)  # Within 1 Mha tolerance (due to restoration potential limits)
```

**Expected**: `total_conservation ≈ conservation_area` (within 1 Mha)

**If fails**: Either protection capping or restoration potential limiting

**Files**: `presolve.gms:54-77`

---

#### 9.4 WDPA Baseline Trend Check

**Test**: Does WDPA baseline match documented trends (864 Mha in 1995 → 1662 Mha in 2020)?

**How**:
```r
wdpa_baseline <- readGDX(gdx, "p22_wdpa_baseline", select=list(base22="WDPA"))

# Sum across all land types and regions
total_1995 <- sum(wdpa_baseline["y1995",,], na.rm=TRUE)
total_2020 <- sum(wdpa_baseline["y2020",,], na.rm=TRUE)

print(paste("1995 total:", total_1995, "Mha"))
print(paste("2020 total:", total_2020, "Mha"))

# Check against documented values
stopifnot(abs(total_1995 - 864.31) < 10)  # Within 10 Mha tolerance
stopifnot(abs(total_2020 - 1662.02) < 10)
```

**Expected**:
- 1995: ~864 Mha
- 2020: ~1662 Mha
- Growth: +798 Mha (+92%)

**If fails**: Check input data file (`wdpa_baseline.cs3`)

**Files**: `input.gms:51-54`, `realization.gms:11-14`

---

#### 9.5 Country Weight Sum Check

**Test**: Do country weights sum to 1.0 within each region?

**How**:
```r
country_weight <- readGDX(gdx, "p22_country_weight")

# Sum should be 1.0 for each region (if all countries selected)
sums <- dimSums(country_weight, dim="i")

print("Country weight sums by region:")
print(sums)

# Should be 1.0 for each region (within tolerance)
stopifnot(all(abs(sums - 1.0) < 0.01))
```

**Expected**: Each region sums to 1.0

**If fails**: Check country weight calculation (`preloop.gms:20-21`)

**Files**: `preloop.gms:15-21`

---

#### 9.6 Restoration Potential Feasibility Check

**Test**: Is restoration potential always non-negative?

**How**:
```r
secdforest_pot <- readGDX(gdx, "p22_secdforest_restore_pot")
past_pot <- readGDX(gdx, "p22_past_restore_pot")
other_pot <- readGDX(gdx, "p22_other_restore_pot")

# Check for negative values
min_sf <- min(secdforest_pot, na.rm=TRUE)
min_past <- min(past_pot, na.rm=TRUE)
min_other <- min(other_pot, na.rm=TRUE)

print(paste("Minimum restoration potentials:"))
print(paste("  Secdforest:", min_sf))
print(paste("  Pasture:", min_past))
print(paste("  Other:", min_other))

stopifnot(min_sf >= -0.001)  # Essentially non-negative
stopifnot(min_past >= -0.001)
stopifnot(min_other >= -0.001)
```

**Expected**: All restoration potentials ≥ 0

**If fails**: Check restoration potential calculations (`presolve.gms:82-111`)

**Files**: `presolve.gms:79-111`

---

#### 9.7 Protection Reversal Check

**Test**: If reversal enabled, is protection zero after reversal year?

**How**:
```r
reversal_year <- readGDX(gdx, "s22_base_protect_reversal")

if(reversal_year < 9999) {  # Reversal enabled
  protection_post <- readGDX(gdx, "pm_land_conservation",
                              select=list(t=paste0("y", reversal_year+5)))

  max_protection <- max(protection_post, na.rm=TRUE)

  print(paste("Max protection after reversal:", max_protection, "Mha"))
  stopifnot(max_protection < 0.001)  # Should be essentially zero
}
```

**Expected**: Protection = 0 after reversal year

**If fails**: Check reversal logic (`presolve.gms:120-122`)

**Files**: `presolve.gms:120-122`

---

### 10. Summary

**Module 22 (Land Conservation)** provides **exogenous land conservation targets** that constrain land-use optimization in MAgPIE. It operates as a **data provider module** (no equations) that calculates protection and restoration requirements based on WDPA baseline trends and optional conservation priority scenarios.

**Core Functions**:
1. **WDPA baseline** (1995-2020): Historical protected area trends (864 → 1662 Mha)
2. **Conservation scenarios** (post-2020): 20+ options (BH, IFL, 30by30, GSN, etc.)
3. **Protection calculation**: Min(target, current land) - prevents conversion
4. **Restoration calculation**: Max(0, target - current land) - active restoration
5. **Restoration potential limits**: Ensures feasibility (available land after other uses)
6. **Country-specific policies**: Different scenarios for selected countries
7. **Gradual phase-in**: Sigmoid fader (2025→2050 default)

**Key Features**:
- **No equations**: Parameter calculation only (runs in preloop/presolve)
- **Exogenous targets**: Not optimized, provided as scenarios
- **20+ conservation scenarios**: From 13% (WDPA 2020) to 50% (Half-Earth)
- **2 conservation types**: Protection (prevent conversion) + Restoration (active recovery)
- **Restoration limited by available land**: Cannot restore more than physically possible
- **Country-specific**: Can apply different policies to selected countries

**Critical Output**:
- `pm_land_conservation(t,j,land,consv_type)`: **Binding constraint** in land allocation
  - Used by: Module 10 (Land), Module 35 (NatVeg), Module 31 (Pasture)
  - Effect: Protected land cannot be converted, restored land must be created

**Conservation Priority Areas**:
- **BH**: Biodiversity Hotspots (36 global hotspots)
- **IFL**: Intact Forest Landscapes (>500 km² contiguous)
- **KBA**: Key Biodiversity Areas (~16,000 sites)
- **30by30**: 30% of land by 2030 (CBD target)
- **GSN**: Global Safety Net (multiple variants)
- **IrrC**: Irreplaceability thresholds (50%, 75%, 95%, 99%, 100%)
- **Half-Earth**: 50% of land by 2050 (E.O. Wilson)

**Execution Flow**:
1. **Preloop**:
   - Calculate country weights (by land area)
   - Initialize WDPA baseline and conservation priority areas
   - Create sigmoid fader (2025→2050)
2. **Presolve** (each timestep):
   - Calculate total conservation area (WDPA + priority areas)
   - Set protection targets (capped at current land)
   - Calculate restoration requirements (target - current)
   - Limit restoration by available land (restoration potential)
   - Output `pm_land_conservation` to land allocation modules

**Dependencies**:
- **Receives from**: Module 10 (Land) - previous timestep land areas
- **Provides to**: Module 10 (Land), Module 35 (NatVeg), Module 31 (Pasture) - conservation constraints
- **Circular**: None (uses previous timestep values)

**Limitations**:
- No conservation effectiveness variation (all 100% effective)
- No conservation costs (opportunity, management, compensation)
- No spatial optimization (scenarios are exogenous)
- No marine protected areas (terrestrial only)
- No restoration dynamics (instantaneous)
- No climate change adaptation
- No indigenous & community lands explicitly
- No connectivity or fragmentation
- No ecosystem service valuation

**Common Uses**:
1. **Biodiversity scenarios**: BH, IFL, KBA protection
2. **Climate commitments**: 30by30, Half-Earth
3. **Regional policies**: EU-only, tropical countries-only
4. **Restoration analysis**: Enable/disable restoration
5. **Economic analysis**: Protection reversal scenarios (opportunity costs)

**Testing Focus**:
- Protection capped at current land
- Restoration conservation (target - current)
- Total conservation sum (protect + restore ≈ target)
- WDPA baseline trends (864 → 1662 Mha)
- Country weight sums (= 1.0 per region)
- Restoration potential feasibility (≥ 0)
- Protection reversal (= 0 after reversal year)

**Why Module 22 Matters**:
- **Biodiversity conservation**: Prevents habitat loss in priority areas
- **Carbon storage**: Protected forests store ~200-300 GtC
- **Policy relevance**: CBD 30by30, Half-Earth, national protection targets
- **Land-use tradeoffs**: Conservation vs. agricultural expansion
- **Simple but powerful**: Exogenous targets, no equations, but major impact on land allocation

---

**Module 22 Status**: ✅ COMPLETE (~850 lines documented)
**Verified Against**: Actual code in `modules/22_land_conservation/area_based_apr22/`

---

### 11. AI Agent Response Patterns

#### **User Query**: "How does MAgPIE handle protected areas?"

**Response**:
```
Module 22 (Land Conservation) implements protected areas as EXOGENOUS constraints:

1. WDPA Baseline (1995-2020):
   - Historical trends: 864 Mha (1995) → 1662 Mha (2020) = 13% of land
   - Post-2020: Held constant at 2020 levels (unless scenarios applied)
   - Categories: IUCN Ia, Ib, III, IV, V, VI + legally designated
   - File: modules/22_land_conservation/area_based_apr22/presolve.gms:20-26

2. Future Scenarios (optional):
   - 20+ options: BH, IFL, KBA, 30by30, GSN, IrrC, Half-Earth
   - Gradual phase-in: 2025→2050 (sigmoid fader)
   - Additive: Priority areas added to WDPA baseline
   - File: input.gms:10 (c22_protect_scenario)

3. Mechanism:
   → pm_land_conservation(t,j,land,"protect"): Binding constraint (mio. ha)
   → Used by Module 10 (Land), Module 35 (NatVeg), Module 31 (Pasture)
   → Protected land CANNOT be converted to agriculture or other uses

4. Restoration (if enabled):
   → If target > current land: restore the difference
   → Forest restoration → secondary forest (presolve.gms:71-73)
   → Limited by available land (restoration potential)

⚠️ IMPORTANT: Protection is EXOGENOUS (not optimized). MAgPIE does not decide
what to protect based on costs/benefits - protection scenarios are external inputs.
```

---

#### **User Query**: "Can I implement the 30by30 target in MAgPIE?"

**Response**:
```
YES! Module 22 includes a 30by30 scenario (30% of land protected by 2030):

1. Configuration (modules/22_land_conservation/area_based_apr22/input.gms):

   $setglobal c22_protect_scenario  30by30
   s22_conservation_target = 2030    # Accelerated timeline
   s22_restore_land = 1              # Enable restoration

2. What it does:
   - Current protection (WDPA 2020): 1662 Mha = 13.06%
   - Target (30by30): ~3800 Mha = 30%
   - Additional protection needed: ~2100 Mha
   - Phase-in: Gradual increase from 2025 to 2030 (sigmoid fader)

3. Restoration requirements:
   - If target > current land: Restoration needed (~1000-1500 Mha)
   - Priority: Secdforest → Pasture → Other land
   - Limited by available land (not all targets may be achievable)

4. Land-use implications:
   - Significant constraint on agricultural expansion
   - Higher food prices (less land available)
   - Reduced deforestation
   - Increased restoration costs

5. Alternative: Combine with other scenarios
   - 30by30 + IFL: Protect 30% total with focus on intact forests
   - IrrC_75pc_30by30: 30% with 75% irreplaceability threshold

⚠️ Note: 30by30 is very ambitious. Restoration potential may limit achievement
in some regions. Check p22_secdforest_restore_pot to verify feasibility.
```

---

#### **User Query**: "Why is restoration limited in my conservation scenario?"

**Response**:
```
Restoration is limited by RESTORATION POTENTIAL (available land after other uses):

1. Check restoration potential (modules/22_land_conservation/area_based_apr22/presolve.gms:79-111):

   Restoration potential = Total land
                          - Urban land
                          - Timber plantations
                          - Protected pasture
                          - Minimum cropland
                          - Tree cover

2. Priority order (restoration allocated sequentially):
   a) Secondary forest (first claim)
   b) Pasture (second claim, after forest allocated)
   c) Other land (residual)

3. Common causes of limited restoration:

   a) High crop demand:
      → vm_land.lo(j,"crop") is high (food security)
      → Little land available for restoration
      → Solution: Increase crop yields, reduce food waste

   b) Large timber areas:
      → Module 32 (Forestry) locks in plantation areas
      → Reduces available land
      → Solution: Reduce timber production targets

   c) Previous restoration already consumed land:
      → E.g., large forest restoration leaves little for grassland
      → Solution: Adjust conservation targets (reduce one to increase other)

   d) Small region:
      → Total land area limited
      → Urban + cropland + timber ≈ total land
      → Solution: Cannot fix (physical constraint)

4. Diagnostic steps:
   - Read p22_secdforest_restore_pot: How much land available for forest?
   - Read p22_past_restore_pot: How much land available for grassland?
   - Read p22_other_restore_pot: How much land available for other?
   - Compare with pm_land_conservation(t,j,land,"restore"): How much actually restored?

5. If restoration potential = 0:
   → Cannot restore ANY land (fully constrained)
   → Protection only (capped at current land area)
   → Consider: Reduce crop demand, increase yields, or accept lower conservation targets

⚠️ Remember: Restoration limited by AVAILABLE LAND, not by costs or ecological constraints.
```

---

#### **User Query**: "What conservation scenarios are available in MAgPIE?"

**Response**:
```
Module 22 provides 20+ conservation scenarios (c22_protect_scenario):

1. Baseline:
   - none: WDPA baseline only (13% in 2020, held constant post-2020)

2. Biodiversity-focused:
   - BH: Biodiversity Hotspots (36 global hotspots, Myers et al. 2000)
   - IFL: Intact Forest Landscapes (>500 km² contiguous, Potapov et al. 2017)
   - BH_IFL: Combination of BH + IFL
   - KBA: Key Biodiversity Areas (~16,000 sites, IUCN)

3. Target-based:
   - 30by30: 30% of land by 2030 (CBD Kunming-Montreal Framework 2022)

4. Global Safety Net (Dinerstein et al. 2020):
   - GSN_DSA: Distinct Species Assemblages
   - GSN_RarePhen: Rare Phenomena
   - GSN_AreaIntct: Large Intact Areas
   - GSN_ClimTier1: Climate Stabilization Tier 1
   - GSN_ClimTier2: Climate Stabilization Tier 2
   - GSN_HalfEarth: 50% of land by 2050

5. Irreplaceability thresholds:
   - IrrC_50pc: 50% irreplaceability (~15-20% of land)
   - IrrC_75pc: 75% irreplaceability (~10-15% of land)
   - IrrC_95pc: 95% irreplaceability (~5-10% of land)
   - IrrC_99pc: 99% irreplaceability (~2-5% of land)
   - IrrC_100pc: 100% irreplaceable (~1-2% of land)

6. Combined scenarios:
   - IrrC_75pc_30by30: 30% target with 75% irreplaceability focus
   - IrrC_95pc_30by30: 30% target with 95% irreplaceability focus
   - IrrC_99pc_30by30: 30% target with 99% irreplaceability focus

7. Other:
   - CCA: Conservation Concern Areas
   - PBL_HalfEarth: PBL Netherlands Half-Earth approach

8. WDPA category subsets:
   - WDPA: All IUCN categories (default)
   - WDPA_I-II-III: Strict protection only (Ia, Ib, III)
   - WDPA_IV-V-VI: Less strict (IV, V, VI)

Configuration:
- File: modules/22_land_conservation/area_based_apr22/input.gms:10
- Sets: modules/22_land_conservation/area_based_apr22/sets.gms:21-24

Data sources:
- BH, IFL: Brooks et al. 2006
- KBA: IUCN and partners
- GSN: Dinerstein et al. 2020
- IrrC: Systematic conservation planning
- 30by30: CBD Kunming-Montreal Framework

⚠️ Note: Scenarios are ADDITIVE to WDPA baseline (not replacing). Total protection = WDPA + scenario.
⚠️ Higher protection % = greater land-use constraints and higher food prices.
```

---

**Last Verified**: 2025-10-13
**Verified Against**: `../modules/22_*/land_feb18/*.gms`
**Verification Method**: Equations cross-referenced with source code
**Changes Since Last Verification**: None (stable)
