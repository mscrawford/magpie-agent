## Module 35: Natural Vegetation (NatVeg) 🚧 IN PROGRESS

**Status**: Being documented (COMPLEX - highest priority)
**Location**: `modules/35_natveg/pot_forest_may24/`
**Size**: 1,085 lines across 9 files
**Authors**: Florian Humpenöder, Abhijeet Mishra, Patrick v. Jeetze

### Quick Reference

**Purpose**: Central module for natural vegetation dynamics including primary & secondary forests, other natural land, age-class tracking, disturbances, harvest, and conservation

**Core Features**:
- **3 land types**: Primary forest, secondary forest (age-classes), other land (natural + young secondary)
- **Age-class system**: 5-year intervals (ac0, ac5, ..., acx) with dynamic aging
- **4 disturbance modes**: No disturbance, shifting agriculture, combined shocks, generic scenarios
- **Critical threshold**: 20 tC/ha separates forest from other land
- **Harvest system**: Differentiated costs (primforest $3,690/ha > other $3,075/ha > secdforest $2,460/ha)
- **Conservation**: NPI/NDC policies, protected area constraints, restoration targets
- **Biodiversity**: BII (Biodiversity Intactness Index) by age class

**Dependencies**: VERY HIGH (central hub) - **HIGH modification risk**
- **Provides to**: Modules 10 (land), 11 (costs), 22 (conservation), 28 (age_class), 32 (forestry), 52 (carbon), 56 (ghg_policy), 73 (timber)
- **Receives from**: Modules 10 (land), 22 (conservation), 28 (age_class), 32 (forestry), 44 (biodiversity)

**Key Variables**:
- `vm_land(j,"primforest")` - Primary forest area (mio. ha)
- `v35_secdforest(j,ac)` - Secondary forest by age class (mio. ha)
- `vm_land_other(j,othertype35,ac)` - Other land: "othernat", "youngsecdf" (mio. ha)
- `vm_prod_natveg(j,land_natveg,kforestry)` - Timber production (mio. tDM/yr)
- `vm_bv(j,land_natveg,potnatveg)` - Biodiversity value (mio. ha equivalent)

**Key Switches**:
- `s35_forest_damage` = 0-4 (disturbance mode)
- `s35_natveg_harvest_shr` = 0-1 (fraction of forest available for harvest)
- `s35_secdf_distribution` = 0,1,2 (initial age-class distribution)
- `s35_hvarea` = 0,1,2 (harvest: off, exogenous, endogenous)
- `c35_ad_policy` = "none", "npi", "ndc" (avoided deforestation policy)

**File Sizes**:
- `presolve.gms` (262 lines) ⭐ CRITICAL - Age dynamics, disturbances, recovery, bounds
- `equations.gms` (229 lines) - 33 equations for land, carbon, harvest, BII
- `postsolve.gms` (203 lines) - State updates and output
- `declarations.gms` (140 lines) - 33 equations, 88 variables/parameters
- `preloop.gms` (99 lines) - Initialization
- `input.gms` (66 lines) - Configuration and data loading
- `realization.gms` (48 lines) - Module description
- `sets.gms` (30 lines) - Land types and policies
- `scaling.gms` (8 lines) - Variable scaling

---

### 1. Core Purpose

**VERIFIED**: Module 35 calculates land and carbon stock dynamics of natural vegetation (`module.gms:10-15`).

**What Module 35 DOES**:
1. Tracks primary forest, secondary forest (age-classes), and other natural land
2. Models age-class dynamics with 5-year shifts
3. Implements 4 disturbance modes (shifting agriculture, wildfire, generic shocks)
4. Transitions recovering land to forest when carbon > 20 tC/ha
5. Constrains natural vegetation harvest with differentiated costs
6. Enforces NPI/NDC conservation policies and protected area constraints
7. Calculates biodiversity value (BII) by age class
8. Provides remaining forest establishment area to Module 32 (forestry)
9. Handles land restoration targets and regrowth after abandonment
10. Links harvest to timber production (Module 73)

**What Module 35 does NOT do**:
- ❌ Does NOT model detailed fire dynamics (uses fixed damage shares or scenarios)
- ❌ Does NOT model edge effects or spatial fire spread
- ❌ Does NOT differentiate disturbance rates by forest age or condition
- ❌ Does NOT model insect outbreaks, disease, or storms separately (generic only)
- ❌ Does NOT track individual tree species or forest types
- ❌ Does NOT model active forest management within natural forests
- ❌ Harvested primary forest becomes secondary forest (one-way transition) (`realization.gms:37`)
- ❌ Harvested secondary forest stays secondary (`realization.gms:36-37`)

---

### 2. Land Types and Structure

#### 2.1 Three Natural Vegetation Types

**Primary Forest** (`vm_land(j,"primforest")`):
- **Definition**: Undisturbed forest, highest carbon density
- **Dynamics**: Can only decrease (one-way) (`presolve.gms:124-126`)
- **Harvest**: Converts to secondary forest youngest age class (`equations.gms:208`)
- **Age class**: Not tracked (assumed mature "acx")
- **Conservation**: Highest protection level

**Secondary Forest** (`v35_secdforest(j,ac)`):
- **Definition**: Regenerating or previously disturbed forest
- **Age tracking**: Full age-class structure (ac0, ac5, ..., acx)
- **Sources**: Primary forest harvest, land abandonment, natural regrowth
- **Harvest**: Stays secondary after harvest (`equations.gms:207`)
- **Carbon threshold**: Vegetation carbon > 20 tC/ha

**Other Land** (`vm_land_other(j,othertype35,ac)`):
- **Two subtypes** (`sets.gms:23-24`):
  - `"othernat"`: Natural grassland, savanna, shrubland
  - `"youngsecdf"`: Young secondary forest with carbon < 20 tC/ha (recovering toward forest)
- **Transition**: youngsecdf → secdforest when carbon > 20 tC/ha (`presolve.gms:99-107`)
- **Harvest**: Woodfuel only, no industrial timber

#### 2.2 Critical Threshold: 20 tC/ha

**VERIFIED** (`presolve.gms:99-107`):
```gams
*' If the vegetation carbon density in a simulation unit due to regrowth
*' exceeds a threshold of 20 tC/ha the respective area is shifted from young secondary
*' forest, which is still considered other land, to secondary forest land.
p35_maturesecdf(t,j,ac)$(not sameas(ac,"acx")) =
      p35_land_other(t,j,"youngsecdf",ac)$(pm_carbon_density_secdforest_ac(t,j,ac,"vegc") > 20);
```

**Meaning**:
- Below 20 tC/ha: Land is "other land" (not counted as forest)
- Above 20 tC/ha: Land graduates to "secondary forest" status
- Threshold applies to vegetation carbon only (not soil carbon)

---

### 3. Age-Class System

**Age Classes** (Module 28 defines structure):
- `ac0`, `ac5`, `ac10`, ..., `ac150`, `acx` (mature, > 150 years)
- **Interval**: 5 years
- **Used for**: Secondary forest and other land (both othertype35)

**Age Progression** (`presolve.gms:79-92`):

```gams
* Regrowth of natural vegetation (natural succession) is modelled by shifting age-classes according to time step length.
s35_shift = m_timestep_length_forestry/5;
* example: ac10 in t = ac5 (ac10-1) in t-1 for a 5 yr time step (s35_shift = 1)
    p35_secdforest(t,j,ac)$(ord(ac) > s35_shift) = pc35_secdforest(j,ac-s35_shift);
* account for cases at the end of the age class set (s35_shift > 1) which are not shifted by the above calculation
    p35_secdforest(t,j,"acx") = p35_secdforest(t,j,"acx")
                  + sum(ac$(ord(ac) > card(ac)-s35_shift), pc35_secdforest(j,ac));
```

**VERIFIED**:
- For 5-year timesteps: `s35_shift = 1` → ac5 becomes ac10, ac10 becomes ac15, etc.
- For 10-year timesteps: `s35_shift = 2` → ac5 becomes ac15, ac10 becomes ac20, etc.
- Oldest classes accumulate in `acx` (mature forest)

**Same logic applies** to other land (`presolve.gms:82-85`)

---

### 4. Disturbance System

**Control Switch**: `s35_forest_damage` (0-4) (`input.gms:27`)

#### 4.1 Mode 0: No Disturbance
- No forest loss from disturbances
- Use for counterfactual scenarios

#### 4.2 Mode 1: Shifting Agriculture Only

**VERIFIED** (`presolve.gms:13-16`):
```gams
if(s35_forest_damage=1,
  p35_disturbance_loss_secdf(t,j,ac_sub) = pc35_secdforest(j,ac_sub) * sum(cell(i,j),f35_forest_lost_share(i,"shifting_agriculture"))*m_timestep_length_forestry;
  p35_disturbance_loss_primf(t,j) = pcm_land(j,"primforest") * sum(cell(i,j),f35_forest_lost_share(i,"shifting_agriculture"))*m_timestep_length_forestry;
);
```

**Mechanism**:
- Fixed historical loss rates from `f35_forest_lost_share` data
- Proportional loss across all age classes
- Primary and secondary forest both affected

#### 4.3 Mode 2: Shifting Agriculture Fade-Out (DEFAULT)

**VERIFIED** (`presolve.gms:18-22` and `input.gms:27-28`):
```gams
* shifting cultivation is faded out
if(s35_forest_damage=2,
  p35_disturbance_loss_secdf(t,j,ac_sub) = pc35_secdforest(j,ac_sub) * sum(cell(i,j),f35_forest_lost_share(i,"shifting_agriculture"))*m_timestep_length_forestry*(1 - p35_damage_fader(t));
  p35_disturbance_loss_primf(t,j) = pcm_land(j,"primforest") * sum(cell(i,j),f35_forest_lost_share(i,"shifting_agriculture"))*m_timestep_length_forestry*(1 - p35_damage_fader(t));
);
```

**Default settings**:
- `s35_forest_damage = 2` (default)
- `s35_forest_damage_end = 2050` (fade-out complete by 2050)
- Fader: `p35_damage_fader(t)` = sigmoid from 0 to 1 between `sm_fix_SSP2` and 2050 (`preloop.gms:80`)

**Meaning**: Shifting agriculture damage gradually reduces to zero by 2050

#### 4.4 Mode 3: Combined Disturbances

**VERIFIED** (`presolve.gms:24-27`):
```gams
if(s35_forest_damage=3,
  p35_disturbance_loss_secdf(t,j,ac_sub) = pc35_secdforest(j,ac_sub) * sum((cell(i,j),combined_loss),f35_forest_lost_share(i,combined_loss))*m_timestep_length_forestry;
  p35_disturbance_loss_primf(t,j) = pcm_land(j,"primforest") * sum((cell(i,j),combined_loss),f35_forest_lost_share(i,combined_loss))*m_timestep_length_forestry;
);
```

**Combined sources** (`sets.gms:14-15`):
- `shifting_agriculture`
- `wildfire`

**Mechanism**: Sum of both loss drivers applied simultaneously

#### 4.5 Mode 4: Generic Shock Scenarios

**VERIFIED** (`presolve.gms:29-33`):
```gams
* generic disturbance scenarios
if(s35_forest_damage=4,
  p35_disturbance_loss_secdf(t,j,ac_sub) = pc35_secdforest(j,ac_sub) * f35_forest_shock(t,"%c35_shock_scenario%") * m_timestep_length;
  p35_disturbance_loss_primf(t,j) = pcm_land(j,"primforest") * f35_forest_shock(t,"%c35_shock_scenario%") * m_timestep_length;
);
```

**Scenarios** (`sets.gms:26-28`, `input.gms:10`):
- `none`: No shock
- `002lin2030`: 0.2% annual loss linear to 2030
- `004lin2030`: 0.4% annual loss linear to 2030
- `008lin2030`: 0.8% annual loss linear to 2030
- `016lin2030`: 1.6% annual loss linear to 2030

**Use case**: Testing fire, pest, or storm scenarios

#### 4.6 Disturbance Distribution

**VERIFIED** (`presolve.gms:35-39`):
```gams
* Distribution of damages correctly
pc35_secdforest(j,ac_est) = pc35_secdforest(j,ac_est) + sum(ac_sub,p35_disturbance_loss_secdf(t,j,ac_sub))/card(ac_est2) + p35_disturbance_loss_primf(t,j)/card(ac_est2);

pc35_secdforest(j,ac_sub) = pc35_secdforest(j,ac_sub) - p35_disturbance_loss_secdf(t,j,ac_sub);
pcm_land(j,"primforest") = pcm_land(j,"primforest") - p35_disturbance_loss_primf(t,j);
```

**CRITICAL MECHANISM**:
1. Disturbed area removed from existing age classes
2. Disturbed area added to youngest establishment age classes (`ac_est`)
3. Distributed evenly across ac_est (typically ac0 and ac5 for 10-year timestep)
4. Primary forest disturbance becomes secondary forest youngest age class

**Limitations** (from gap analysis):
- ❌ No age-dependent disturbance rates (young forest equally vulnerable as old)
- ❌ No spatial fire spread or edge effects
- ❌ No climate-fire feedbacks (fire risk not dynamic)
- ❌ No post-disturbance mortality cascades

---

### 5. Forest Recovery After Abandonment

**Recovery Sources** (`presolve.gms:43-73`):
1. Forestry abandonment (transition from managed plantations to natural land)
2. Agricultural land abandonment (cropland or pasture to natural land)

**VERIFIED Mechanism** (`presolve.gms:47-73`):

**Step 1**: Calculate maximum forest recovery potential
```gams
pc35_max_forest_recovery(j) = pm_max_forest_est(t,j) - sum(ac, pc35_land_other(j,"youngsecdf",ac));
```

**Step 2**: Prioritize forestry abandonment (directly becomes youngsecdf)
```gams
p35_forest_recovery_area(t,j,ac_est) = vm_lu_transitions.l(j,"forestry","other")/card(ac_est2);
```

**Step 3**: Calculate forest recovery share for remaining abandoned land
```gams
pc35_forest_recovery_shr(j)$((...) > 0) =
  (pc35_max_forest_recovery(j) - sum(ac_est, p35_forest_recovery_area(t,j,ac_est)))
  / (sum(land_ag, pcm_land(j,land_ag))+pcm_land(j,"urban"));
```

**Step 4**: Distribute remaining abandoned land
```gams
* Portion becomes youngsecdf (recovering forest)
pc35_land_other(j,"youngsecdf",ac_est) += p35_forest_recovery_area(t,j,ac_est);
* Remainder becomes othernat (non-forest)
pc35_land_other(j,"othernat",ac_est) = pc35_land_other(j,"othernat",ac_est) - p35_forest_recovery_area(t,j,ac_est);
```

**Key Insight**: Not all abandoned land becomes forest - recovery limited by:
1. Potential forest area (climatic suitability)
2. Existing youngsecdf area
3. Proportional allocation based on forest recovery share

---

### 6. Key Equations (Selected from 33 Total)

**Full list**: 33 equations in `equations.gms` (229 lines)

#### 6.1 Land Aggregation

**q35_land_secdforest** (`equations.gms:11`):
```gams
vm_land(j2,"secdforest") =e= sum(ac, v35_secdforest(j2,ac));
```

**q35_land_other** (`equations.gms:13`):
```gams
vm_land(j2,"other") =e= sum((othertype35,ac), vm_land_other(j2,othertype35,ac));
```

**Purpose**: Aggregate age-class areas for interface with other modules

#### 6.2 Conservation Constraints

**q35_natveg_conservation** (`equations.gms:19-22`):
```gams
sum(land_natveg, vm_land(j2,land_natveg))
=g=
sum((ct,land_natveg), pm_land_conservation(ct,j2,land_natveg,"protect"));
```

**Purpose**: Total natural land ≥ total protection target (from Module 22)

**q35_min_forest** (`equations.gms:75-77`):
```gams
sum(land_forest, vm_land(j2,land_forest)) =g= sum(ct, p35_min_forest(ct,j2));
```

**q35_min_other** (`equations.gms:79`):
```gams
vm_land(j2,"other") =g= sum(ct, p35_min_other(ct,j2));
```

**Purpose**: NPI/NDC policies for specific forest and other land targets (non-interchangeable)

#### 6.3 Carbon Stocks

**q35_carbon_secdforest** (`equations.gms:46-48`):
```gams
vm_carbon_stock(j2,"secdforest",ag_pools,stockType) =e=
  m_carbon_stock_ac(v35_secdforest,pm_carbon_density_secdforest_ac,"ac","ac_sub");
```

**Purpose**: Carbon = area × age-class-specific carbon density (summed over age classes)

**Similar equations** for primforest and other land

#### 6.4 Biodiversity Value (BII)

**q35_bv_secdforest** (`equations.gms:60-63`):
```gams
vm_bv(j2,"secdforest",potnatveg) =e=
  sum(bii_class_secd, sum(ac_to_bii_class_secd(ac,bii_class_secd), v35_secdforest(j2,ac)) *
  fm_bii_coeff(bii_class_secd,potnatveg)) * fm_luh2_side_layers(j2,potnatveg);
```

**Purpose**: Biodiversity value = area × BII coefficient (by age class) × potential natural vegetation layer

**BII coefficients** increase with forest age (Module 44 provides coefficients)

#### 6.5 Harvest Constraints

**q35_hvarea_secdforest** (`equations.gms:172-175`):
```gams
v35_hvarea_secdforest(j2,ac_sub) =l= v35_secdforest_reduction(j2,ac_sub);
```

**Purpose**: Harvested area ≤ area reduction (not all reduction is harvest - some is conversion)

**Similar constraints** for primforest and other land

#### 6.6 Timber Production

**q35_prod_secdforest** (`equations.gms:140-143`):
```gams
sum(kforestry, vm_prod_natveg(j2,"secdforest",kforestry))
=e=
sum(ac_sub, v35_hvarea_secdforest(j2,ac_sub) * sum(ct,pm_timber_yield(ct,j2,ac_sub,"secdforest"))) / m_timestep_length_forestry;
```

**Purpose**: Production = harvested area × yield / timestep length

**Similar equations** for primforest and other land (woodfuel only)

#### 6.7 Regeneration

**q35_secdforest_regeneration** (`equations.gms:204-210`):
```gams
sum(ac_est, v35_secdforest(j2,ac_est))
=e=
sum(ac_sub,v35_hvarea_secdforest(j2,ac_sub))
+ v35_hvarea_primforest(j2)
+ p35_land_restoration(j2,"secdforest");
```

**Purpose**: New secondary forest = harvested secondary + harvested primary + restoration

**CRITICAL**: Harvested primary forest becomes secondary forest (one-way transition)

#### 6.8 Maximum Forest Establishment

**q35_max_forest_establishment** (`equations.gms:192-197`):
```gams
sum(land_forest, vm_landexpansion(j2,land_forest))
=l=
sum(ct,pm_max_forest_est(ct,j2))
- sum(ac, vm_land_other(j2,"youngsecdf",ac) );
```

**Purpose**: Total forest expansion (natural + managed) ≤ potential forest area - existing youngsecdf

**Provides constraint** to Module 32 (forestry) for plantation establishment

---

### 7. Harvest System

#### 7.1 Harvest Costs (Differentiated)

**VERIFIED** (`input.gms:22-24`):
- **Primary forest**: `s35_timber_harvest_cost_primforest = 3690 USD17MER/ha`
- **Other land**: `s35_timber_harvest_cost_other = 3075 USD17MER/ha`
- **Secondary forest**: `s35_timber_harvest_cost_secdforest = 2460 USD17MER/ha`

**Rationale** (`equations.gms:121-126`):
- Higher costs for primary forest mimic access difficulties
- Costs paid every time natural vegetation is harvested
- Older forest preferred (higher growing stock, lower per-unit costs)

#### 7.2 Harvest Control Modes

**Switch**: `s35_hvarea` (0, 1, 2) (`input.gms:18`)

**Mode 0**: No harvest from natural vegetation

**Mode 1**: Exogenous harvest (fixed rates)
- `s35_hvarea_secdforest`: Annual harvest rate (%)
- `s35_hvarea_primforest`: Annual harvest rate (%)
- `s35_hvarea_other`: Annual harvest rate (%)

**Mode 2**: Endogenous harvest (DEFAULT)
- Model optimizes harvest based on timber demand and costs
- Subject to conservation constraints

**VERIFIED** (`presolve.gms:242-250`):
```gams
if(s35_hvarea = 0,
 v35_hvarea_secdforest.fx(j,ac_sub) = 0;
 v35_hvarea_primforest.fx(j) = 0;
 v35_hvarea_other.fx(j,othertype35,ac_sub) = 0;
elseif s35_hvarea = 1,
 v35_hvarea_secdforest.fx(j,ac_sub) = (v35_secdforest.l(j,ac_sub) - v35_secdforest.lo(j,ac_sub))*s35_hvarea_secdforest*m_timestep_length_forestry;
 ...
);
```

#### 7.3 Harvest Share Constraint

**VERIFIED** (`presolve.gms:132-141` and `input.gms:25`):
```gams
** Allowing selective logging only after historical period
if (sum(sameas(t_past,t),1) = 1,
vm_land.lo(j,"primforest") = 0;
else
vm_land.lo(j,"primforest") = (1-s35_natveg_harvest_shr) * pcm_land(j,"primforest");
);
```

**Default**: `s35_natveg_harvest_shr = 1` (100% can be harvested, subject to other constraints)

**Purpose**: Limit maximum harvest to a fraction of available forest (e.g., 0.2 = 20% max harvest)

#### 7.4 Age-Class Harvest Restrictions

**VERIFIED** (`presolve.gms:236-240`):
```gams
** Youngest age classes are not allowed to be harvested
v35_hvarea_secdforest.fx(j,ac_est) = 0;
v35_hvarea_other.fx(j,othertype35,ac_est) = 0;
v35_secdforest_reduction.fx(j,ac_est) = 0;
v35_other_reduction.fx(j,othertype35,ac_est) = 0;
```

**Meaning**: Only older age classes (`ac_sub`) can be harvested, not establishment classes (`ac_est`)

---

### 8. Conservation and NPI/NDC Policies

#### 8.1 Land Conservation (General)

**Source**: Module 22 (land_conservation) provides `pm_land_conservation(t,j,land_natveg,consv_type)`

**Types**:
- `"protect"`: Protected areas (no conversion allowed)
- `"restore"`: Restoration targets (minimum expansion)

**Applied in presolve** (`presolve.gms:129-213`):
- Sets lower bounds on land areas
- Distributes protection across age classes proportionally
- Ensures restoration targets are met

#### 8.2 NPI/NDC Policies (Country-Specific)

**VERIFIED** (`input.gms:8-9`, `preloop.gms:62-63`):
```gams
$setglobal c35_ad_policy  npi
...
p35_min_forest(t,j) = f35_min_land_stock(t,j,"%c35_ad_policy%","forest");
p35_min_other(t,j) = f35_min_land_stock(t,j,"%c35_ad_policy%","other");
```

**Policy options**:
- `"none"`: No NPI/NDC constraints
- `"npi"`: National Policy Instruments (implemented policies)
- `"ndc"`: Nationally Determined Contributions (Paris Agreement pledges)

**Data**: `f35_min_land_stock` from country reports

**Ramp-up**: Policies ramp up until 2030, constant thereafter (`realization.gms:17-21`)

**NPI/NDC Reversal**: Optional switch to remove policies after a year (`presolve.gms:231-234`)

**CRITICAL** (`presolve.gms:225-228`):
```gams
p35_min_forest(t,j)$(p35_min_forest(t,j) > pcm_land(j,"primforest") + pcm_land(j,"secdforest") + pcm_land(j,"forestry"))
  = pcm_land(j,"primforest") + pcm_land(j,"secdforest") + pcm_land(j,"forestry");
```

**Meaning**: Targets cannot exceed current forest area (no retroactive requirements)

#### 8.3 Protection Distribution

**VERIFIED** (`presolve.gms:153-160`):
```gams
* Secondary forest conservation
p35_protection_dist(j,ac_sub)$(sum(ac_sub2,pc35_secdforest(j,ac_sub2)) > 0) = pc35_secdforest(j,ac_sub) / sum(ac_sub2,pc35_secdforest(j,ac_sub2));
...
v35_secdforest.lo(j,ac_sub) = max((1-s35_natveg_harvest_shr) * pc35_secdforest(j,ac_sub), pm_land_conservation(t,j,"secdforest","protect") * p35_protection_dist(j,ac_sub));
```

**Mechanism**: Protection distributed proportionally across age classes based on current area

---

### 9. Configuration Options

#### 9.1 Disturbance Mode

**c35_forest_damage** (scalar, 0-4):
- **Default**: 2 (shifting agriculture with fade-out)
- See Section 4 for details on all modes

#### 9.2 Harvest Control

**s35_hvarea** (scalar, 0-2):
- **Default**: 2 (endogenous)
- 0 = no harvest, 1 = exogenous, 2 = optimized

**s35_natveg_harvest_shr** (scalar, 0-1):
- **Default**: 1 (100% available)
- Controls maximum harvest fraction

#### 9.3 Initial Age-Class Distribution

**s35_secdf_distribution** (scalar, 0-2):
- **Default**: 2 (MODIS/Poulter satellite data)
- 0 = all in highest age class (acx)
- 1 = equal distribution across all classes
- 2 = empirical distribution from Global Forest Age Dataset (GFAD)

#### 9.4 Conservation Policies

**c35_ad_policy** (global setting):
- **Default**: "npi"
- Options: "none", "npi", "ndc"

**s35_npi_ndc_reversal** (scalar, year):
- **Default**: Inf (no reversal)
- Year to remove NPI/NDC policies

#### 9.5 Potential Forest Area

**c35_pot_forest_scenario** (global setting):
- **Default**: "cc" (climate change)
- "nocc": Static at 1995 values
- "nocc_hist": Static after fixed year

---

### 10. Module Interfaces

#### 10.1 Provides To (Outputs)

**To Module 10 (Land)**:
- `vm_land(j,land_natveg)` - Natural vegetation areas
- `vm_landdiff_natveg` - Gross changes in natural vegetation
- `vm_landexpansion(j,land_natveg)` - Natural land expansion

**To Module 52 (Carbon)**:
- `vm_carbon_stock(j,land_natveg,ag_pools,stockType)` - Carbon stocks

**To Module 73 (Timber)**:
- `vm_prod_natveg(j,land_natveg,kforestry)` - Timber and woodfuel production

**To Module 11 (Costs)**:
- `vm_cost_hvarea_natveg(i)` - Harvest costs

**To Module 44 (Biodiversity)**:
- `vm_bv(j,land_natveg,potnatveg)` - Biodiversity value

**To Module 32 (Forestry)**:
- `pm_max_forest_est(t,j)` - Remaining forest establishment potential

#### 10.2 Receives From (Inputs)

**From Module 10 (Land)**:
- `vm_lu_transitions(j,land_from,land_to)` - Land use transitions
- `pm_land_start(j,land)` - Initial land areas

**From Module 22 (Conservation)**:
- `pm_land_conservation(t,j,land_natveg,consv_type)` - Protection and restoration targets

**From Module 52 (Carbon)**:
- `pm_carbon_density_secdforest_ac(t,j,ac,ag_pools)` - Age-class carbon density
- `pm_carbon_density_other_ac(t,j,ac,ag_pools)` - Other land carbon density
- `fm_carbon_density(t,j,land,ag_pools)` - Primary forest carbon density

**From Module 73 (Timber)**:
- `pm_timber_yield(t,j,ac,land_natveg)` - Timber yields by age class

**From Module 44 (Biodiversity)**:
- `fm_bii_coeff(bii_class,potnatveg)` - Biodiversity intactness coefficients

---

### 11. Typical Modifications

#### 11.1 Increase Disturbance Rates

**Goal**: Test higher fire/disturbance scenario

**Configuration**:
```r
cfg$gms$s35_forest_damage <- 4            # Generic shock mode
cfg$gms$c35_shock_scenario <- "008lin2030"  # 0.8% annual loss
```

**Expected Effect**:
- Higher forest loss in young age classes
- More primary → secondary transitions
- Increased emissions
- Lower timber availability

**Dependencies**: Check Module 52 (carbon) and Module 56 (emissions)

#### 11.2 Strict Harvest Limits

**Goal**: Reduce natural forest harvest to 10% maximum

**Configuration**:
```r
cfg$gms$s35_natveg_harvest_shr <- 0.1   # 10% max harvest
cfg$gms$s35_hvarea <- 2                  # Endogenous (optimized)
```

**Expected Effect**:
- Lower timber from natural forests
- Higher plantation demand (Module 32)
- Higher timber prices
- Better forest conservation

**Dependencies**: Check Module 32 (forestry) and Module 73 (timber)

#### 11.3 Disable Disturbances

**Goal**: Counterfactual without disturbances

**Configuration**:
```r
cfg$gms$s35_forest_damage <- 0   # No disturbance
```

**Expected Effect**:
- No natural forest loss except harvest or land conversion
- Older age-class distribution in secondary forest
- Higher carbon stocks
- Lower emissions

#### 11.4 Change Initial Age Distribution

**Goal**: Test sensitivity to initial conditions

**Configuration**:
```r
cfg$gms$s35_secdf_distribution <- 1   # Equal distribution
```

**Expected Effect**:
- More young forest initially
- Different carbon accumulation trajectory
- Different harvest availability

---

### 12. Key Limitations & Assumptions

**VERIFIED Limitations**:

1. **Disturbance mechanisms** (`presolve.gms:12-33`):
   - ❌ Fixed regional rates, not age-dependent
   - ❌ No spatial fire spread or edge effects
   - ❌ No climate-fire feedbacks (static scenarios only)
   - Reality: Fire risk depends on forest age, edge distance, climate

2. **Forest maturation threshold** (`presolve.gms:99-107`):
   - ❌ Hard 20 tC/ha cutoff for forest/other land classification
   - Reality: Gradual transition, regional variation

3. **Primary to secondary transition** (`realization.gms:37`):
   - ❌ Harvested primary forest becomes secondary (one-way, irreversible)
   - Reality: Very old secondary forest can approach primary characteristics

4. **Harvest impact** (`equations.gms:207-210`):
   - ❌ Harvested secondary forest stays secondary (doesn't reset to young)
   - Reality: Clear-cutting resets succession; selective logging doesn't

5. **Biodiversity** (`equations.gms:60-68`):
   - ❌ BII coefficients globally uniform (no regional variation)
   - Reality: Biodiversity value varies by region, ecosystem type

6. **Age-class initialization** (`realization.gms:31-35`):
   - ❌ MODIS data available but causes negative LUC emissions
   - ❌ Current default: Poulter distribution or equal/acx only
   - Reality: Actual age distribution more complex

7. **Restoration** (`presolve.gms:166-178`):
   - ❌ Restoration targets may shift between forest and other land if potential area insufficient
   - Reality: Restoration location and type should be specified

---

### 13. Testing & Validation

**Test 1**: Age-Class Mass Balance
```r
# For each timestep, check:
Delta_secdf(ac) = secdf(t-1, ac-shift) - secdf(t, ac) + additions - reductions
Tolerance: < 0.01% of area
```

**Test 2**: Forest/Other Threshold
```r
# Youngsecdf should graduate when carbon > 20 tC/ha
Check: vm_land_other(t,j,"youngsecdf",ac)$(carbon_density > 20) = 0
```

**Test 3**: Land Conservation
```r
# Total natural land >= protection target
Check: sum(land_natveg, vm_land(t,j,land_natveg)) >= sum(land_natveg, pm_land_conservation(t,j,land_natveg,"protect"))
```

**Test 4**: Harvest Constraints
```r
# Harvested area <= area reduction
Check: v35_hvarea_secdforest(t,j,ac) <= v35_secdforest_reduction(t,j,ac)
```

**Test 5**: Primary Forest One-Way
```r
# Primary forest can only decrease
Check: vm_land(t,j,"primforest") <= vm_land(t-1,j,"primforest")
```

**Test 6**: Regeneration Balance
```r
# New secondary forest = harvested + restoration
Check: sum(ac_est, v35_secdforest(t,j,ac_est)) = sum(ac_sub, v35_hvarea_secdforest(t,j,ac_sub)) + v35_hvarea_primforest(t,j) + p35_land_restoration(j,"secdforest")
```

---

### 14. Summary: Module 35 at a Glance

**Purpose**: Central hub for natural vegetation dynamics with age-class tracking, disturbances, harvest, and conservation

**Complexity**: VERY HIGH (1,085 lines, 33 equations, 8 files)

**Key Innovation**: Age-class tracking with 20 tC/ha threshold for forest maturation

**Key Limitation**: Disturbances are uniform by age class; no spatial dynamics or climate feedbacks

**Dependencies**: VERY HIGH (8 modules) - **HIGH modification risk**

**Typical Modifications**:
1. Adjust disturbance mode (s35_forest_damage = 0-4)
2. Set harvest limits (s35_natveg_harvest_shr = 0-1)
3. Change conservation policy (c35_ad_policy = "none", "npi", "ndc")
4. Test disturbance scenarios (c35_shock_scenario)

**Critical Files**:
- `presolve.gms` (262 lines) ⭐ - Disturbances, age dynamics, recovery, bounds
- `equations.gms` (229 lines) - 33 equations for land, carbon, harvest, BII
- `postsolve.gms` (203 lines) - State updates

**AI Response Pattern**:
- Cite specific equations and line numbers (33 equations available)
- Clarify forest vs. other land threshold (20 tC/ha)
- Distinguish primary/secondary/other land dynamics
- Warn about age-class complexity when modifying
- Check Modules 32 (forestry), 52 (carbon), 73 (timber) for dependencies
- Emphasize disturbance limitations (no spatial dynamics)

---

