## Module 35: Natural Vegetation (NatVeg) 🚧 IN PROGRESS

**Status**: Being documented (COMPLEX - highest priority)
**Location**: `modules/35_natveg/pot_forest_may24/`
**Size**: 1,165 lines across 9 files
**Authors**: Florian Humpenöder, Abhijeet Mishra, Patrick v. Jeetze

> **🔄 Update 2026-04-20 (commit `c7731e234`, refactor `2fa7b8bea`): Natural-origin tracking for secondary forest carbon density.**
> Secondary forest is now split by *origin*: existing/managed secdforest uses the FRA-calibrated natveg growth curve (from Module 52), while natural-origin secdforest grown by succession on abandoned cropland uses the **uncalibrated** natveg curve (Braakhekke et al.). The natural-origin area is tracked per age class in the new parameters `p35_secdforest_natural`/`pc35_secdforest_natural`, and `q35_carbon_secdforest` now multiplies area by a blended density `p35_carbon_density_secdforest`. See Section 5.1.

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
- **Provides to**: Modules 10 (land), 11 (costs), 32 (forestry), 59 (SOM), 73 (timber) — direct consumers of M35 interface variables (`vm_land_other`, `vm_prod_natveg`, `vm_cost_hvarea_natveg`, `vm_natforest_reduction`, `vm_landdiff_natveg`, `v35_*`), verified 2026-05-23 R3 via `find ../modules -name '*.gms' -exec grep -l '<var>' {} \;`. Modules 22, 28, 52, 56 do NOT directly consume any M35 interface variable — earlier doc claim removed.
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
- `presolve.gms` (294 lines) ⭐ CRITICAL - Age dynamics, disturbances, recovery, bounds
- `equations.gms` (233 lines) - 32 equations for land, carbon, harvest, BII
- `postsolve.gms` (210 lines) - State updates and output
- `declarations.gms` (143 lines) - 32 equations, variables/parameters
- `preloop.gms` (107 lines) - Initialization
- `input.gms` (66 lines) - Configuration and data loading
- `realization.gms` (47 lines) - Module description
- `sets.gms` (30 lines) - Land types and policies
- `scaling.gms` (35 lines) - Variable scaling

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
- ❌ Harvested primary forest becomes secondary forest (one-way transition) (`realization.gms:35-36`)
- ❌ Harvested secondary forest stays secondary (`realization.gms:35-36`)

---

### 2. Land Types and Structure

#### 2.1 Three Natural Vegetation Types

**Primary Forest** (`vm_land(j,"primforest")`):
- **Definition**: Undisturbed forest, highest carbon density
- **Dynamics**: Can only decrease (one-way) (`presolve.gms:143-145`)
- **Harvest**: Converts to secondary forest youngest age class (`equations.gms:208`)
- **Age class**: Not tracked (assumed mature "acx")
- **Conservation**: Highest protection level

**Secondary Forest** (`v35_secdforest(j,ac)`):
- **Definition**: Regenerating or previously disturbed forest
- **Age tracking**: Full age-class structure (ac0, ac5, ..., acx)
- **Sources**: Primary forest harvest, land abandonment, natural regrowth
- **Harvest**: Stays secondary after harvest (`equations.gms:208`)
- **Carbon threshold**: Vegetation carbon > 20 tC/ha
- **Origin tracking** (2026-04-20): Natural-origin area (from natural succession on abandoned cropland) is tracked separately in `p35_secdforest_natural(t,j,ac)` so its carbon density can be computed with the uncalibrated natveg growth curve (see Section 5.1)

**Other Land** (`vm_land_other(j,othertype35,ac)`):
- **Two subtypes** (`sets.gms:23-24`):
  - `"othernat"`: Natural grassland, savanna, shrubland
  - `"youngsecdf"`: Young secondary forest with carbon < 20 tC/ha (recovering toward forest)
- **Transition**: youngsecdf → secdforest when carbon > 20 tC/ha (`presolve.gms:116-122`)
- **Harvest**: Woodfuel only, no industrial timber

#### 2.2 Critical Threshold: 20 tC/ha

**VERIFIED** (`modules/35_natveg/pot_forest_may24/presolve.gms:109-122`):
```gams
*' If the vegetation carbon density in a simulation unit due to regrowth
*' exceeds a threshold of 20 tC/ha the respective area is shifted from young secondary
*' forest, which is still considered other land, to secondary forest land.
p35_maturesecdf(t,j,ac)$(not sameas(ac,"acx")) =
      p35_land_other(t,j,"youngsecdf",ac)$(pm_carbon_density_secdforest_ac_uncalib(t,j,ac,"vegc") > 20);
```

**Meaning**:
- Below 20 tC/ha: Land is "other land" (not counted as forest)
- Above 20 tC/ha: Land graduates to "secondary forest" status
- Threshold applies to vegetation carbon only (not soil carbon)

> **🔄 Changed 2026-04-20 (commit `c7731e234`)**: The maturation test now applies `pm_carbon_density_secdforest_ac_uncalib` (the *uncalibrated* natveg curve), not the FRA-calibrated `pm_carbon_density_secdforest_ac`. Rationale (per `presolve.gms:113-115` comment): natural succession from abandoned cropland should mature at realistic rates, independent of the FRA 2025 calibration applied in Module 52. Freshly matured youngsecdf is recorded as natural-origin area (`p35_secdforest_natural`).
> - `pm_carbon_density_secdforest_ac` is consumed by Module 14 (`modules/14_yields/managementcalib_aug19/presolve.gms:44`)
> - `pm_carbon_density_secdforest_ac_uncalib` is consumed by Module 29 (`modules/29_cropland/detail_apr24/preloop.gms:46`), Module 32 (`modules/32_forestry/dynamic_may24/presolve.gms:59`)

---

### 3. Age-Class System

**Age Classes** (Module 28 defines structure):
- `ac0`, `ac5`, `ac10`, ..., `ac150`, `acx` (mature, > 150 years)
- **Interval**: 5 years
- **Used for**: Secondary forest and other land (both othertype35)

**Age Progression** (`presolve.gms:84-97`):

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

**Same logic applies** to other land (`presolve.gms:87-90`). The natural-origin area `p35_secdforest_natural` ages in lockstep (`presolve.gms:99-102`) — see Section 5.1.

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
- Fader: `p35_damage_fader(t)` = sigmoid from 0 to 1 between `sm_fix_SSP2` and 2050 (`preloop.gms:88`)

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

**Recovery Sources** (`presolve.gms:48-78`):
1. Forestry abandonment (transition from managed plantations to natural land)
2. Agricultural land abandonment (cropland or pasture to natural land)

**VERIFIED Mechanism** (`presolve.gms:53-78`):

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

### 5.1 Natural-Origin Tracking for Secondary Forest Carbon Density (NEW 2026-04-20)

**Introduced by commit `c7731e234`** ("Natural-origin tracking for secondary forest carbon density"), refactored by `2fa7b8bea`.

**Problem addressed**: Module 52 calibrates the secondary-forest Chapman-Richards `k` to FRA 2025 growing-stock targets (`s52_growingstock_calib = 1` by default — see `modules/module_52.md`). That calibration represents *existing* managed/legacy secondary forest, whose realized growing stock is typically below the LPJmL potential. Applying that suppressed growth rate to forest grown by fresh natural succession on abandoned cropland would underestimate its carbon accumulation. The fix tracks the **natural origin** of secondary forest per age class and uses the *uncalibrated* natveg curve for that fraction.

**The two carbon densities**:
- `pm_carbon_density_secdforest_ac(t,j,ac,ag_pools)` — FRA-calibrated natveg curve (existing/managed secdforest); provided by Module 52
- `pm_carbon_density_secdforest_ac_uncalib(t,j,ac,ag_pools)` — uncalibrated natveg curve (Braakhekke et al.); provided by Module 52, preserved before the preloop calibration overwrite

**New parameters** (`declarations.gms:16-17,29`):
- `p35_secdforest_natural(t,j,ac)` — secdforest area from natural succession, using the uncalibrated natveg growth curve (mio. ha)
- `pc35_secdforest_natural(j,ac)` — current-timestep natural-origin secdforest area (mio. ha)
- `p35_carbon_density_secdforest(t,j,ac,ag_pools)` — secdforest carbon density blending the FRA-calibrated and uncalibrated curves by natural-origin share (tC per ha)

**Lifecycle of the natural-origin area**:

1. **Initialization** (`preloop.gms:49-50`): `p35_secdforest_natural` and `pc35_secdforest_natural` set to 0 — all initial secdforest is treated as existing/managed (natural origin = 0). New natural-origin area only enters via `youngsecdf` maturation.

2. **Disturbance** (`presolve.gms:42-45`): natural-origin area is reduced proportionally with disturbance losses, preserving the natural-vs-existing ratio of the damaged area:
   ```gams
   pc35_secdforest_natural(j,ac_sub)$(pc35_secdforest(j,ac_sub) > 1e-6) =
     pc35_secdforest_natural(j,ac_sub) * (1 - p35_disturbance_loss_secdf(t,j,ac_sub) / (pc35_secdforest(j,ac_sub) + p35_disturbance_loss_secdf(t,j,ac_sub)));
   ```
   (The `1e-12` threshold in commit `c7731e234` was raised to `1e-6` by refactor `2fa7b8bea`.)

3. **Age-class shift** (`presolve.gms:99-102`): natural-origin area ages in lockstep with the secdforest age classes, using the same `s35_shift` logic.

4. **Maturation** (`presolve.gms:116-122`): area maturing from `youngsecdf` into secdforest (`p35_maturesecdf`, gated on the uncalibrated 20 tC/ha threshold — see Section 2.2) is added to `p35_secdforest_natural`. Freshly matured youngsecdf is natural-origin by definition.

5. **Safety clamp** (`presolve.gms:127-128`, `postsolve.gms:14-16`): `pc35_secdforest_natural` is clamped so it never exceeds total `pc35_secdforest`.

6. **Post-solve** (`postsolve.gms:11-16`): natural-origin area stays at its presolve value — the lower bound (step in `presolve.gms:177,179`) prevents the solver from reducing it, and any area *increases* during optimization (harvest cycling into `ac_est`, primforest reclassification, restoration) are NOT natural origin.

**Protection of the natural-origin area** (`presolve.gms:175-180`): the lower bound on `v35_secdforest(j,ac_sub)` is raised to include `pc35_secdforest_natural(j,ac_sub)`, so natural-origin secondary forest cannot be harvested:
```gams
if (sum(sameas(t_past,t),1) = 1,
v35_secdforest.lo(j,ac_sub) = max(pm_land_conservation(t,j,"secdforest","protect") * p35_protection_dist(j,ac_sub), pc35_secdforest_natural(j,ac_sub));
else
v35_secdforest.lo(j,ac_sub) = max((1-s35_natveg_harvest_shr) * pc35_secdforest(j,ac_sub), pm_land_conservation(t,j,"secdforest","protect") * p35_protection_dist(j,ac_sub), pc35_secdforest_natural(j,ac_sub));
);
```

**The blended carbon density** (`presolve.gms:248-252`): `p35_carbon_density_secdforest` is the area-weighted average of the two curves, with the natural-origin share as the weight:
```gams
p35_carbon_density_secdforest(t,j,ac,ag_pools) = pm_carbon_density_secdforest_ac(t,j,ac,ag_pools);
p35_carbon_density_secdforest(t,j,ac,ag_pools)$(pc35_secdforest(j,ac) > 1e-10) =
  pm_carbon_density_secdforest_ac(t,j,ac,ag_pools)
  - (pm_carbon_density_secdforest_ac(t,j,ac,ag_pools) - pm_carbon_density_secdforest_ac_uncalib(t,j,ac,ag_pools))
    * pc35_secdforest_natural(j,ac) / pc35_secdforest(j,ac);
```
- Where natural-origin share = 0, the blend equals the FRA-calibrated curve.
- Where natural-origin share = 1 (all area natural-origin), the blend equals the uncalibrated natveg curve.
- This blended density feeds `q35_carbon_secdforest` (see Section 6.3).

**Youngsecdf carbon density** (`presolve.gms:241-242`): `p35_carbon_density_other(t,j,"youngsecdf",ac,ag_pools)` is now also set from `pm_carbon_density_secdforest_ac_uncalib` (previously the calibrated curve). Young secondary forest is recovering-from-abandonment land, so the uncalibrated curve is consistent with the maturation logic.

---

### 6. Key Equations (Complete — 32 Total)

**Full list**: 32 equations in `equations.gms` (229 lines)

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

**q35_min_forest** (`equations.gms:78-80`):
```gams
sum(land_forest, vm_land(j2,land_forest)) =g= sum(ct, p35_min_forest(ct,j2));
```

**q35_min_other** (`equations.gms:82`):
```gams
vm_land(j2,"other") =g= sum(ct, p35_min_other(ct,j2));
```

**Purpose**: NPI/NDC policies for specific forest and other land targets (non-interchangeable)

**q35_secdforest_restoration** (`equations.gms:24-28`):
```gams
sum(land_ag, vm_lu_transitions(j2,land_ag,"secdforest"))
+ vm_lu_transitions(j2,"forestry","secdforest")
=g=
p35_land_restoration(j2,"secdforest");
```

**Purpose**: Ensures that transitions from agricultural land and forestry into secondary forest meet the restoration target set for secondary forest. The constraint includes both agricultural-to-secdforest and forestry-to-secdforest transitions.
**Key variables**:
- `vm_lu_transitions` (land use transitions from Module 10; also consumed by Module 29 `modules/29_cropland/simple_apr24/equations.gms:49`, Module 59 `modules/59_som/cellpool_jan23/equations.gms:51`)
- `p35_land_restoration` (restoration target, computed in presolve)

**q35_other_restoration** (`equations.gms:30-33`):
```gams
sum(land_ag, vm_lu_transitions(j2,land_ag,"other"))
=g=
p35_land_restoration(j2,"other");
```

**Purpose**: Ensures that transitions from agricultural land into other natural land meet the other-land restoration target. Unlike secondary forest, forestry-to-other transitions are not included.
**Key variables**: `vm_lu_transitions`, `p35_land_restoration`

#### 6.3 Carbon Stocks

**q35_carbon_secdforest** (`equations.gms:49-51`):
```gams
vm_carbon_stock(j2,"secdforest",ag_pools,stockType) =e=
  m_carbon_stock_ac(v35_secdforest,p35_carbon_density_secdforest,"ac","ac_sub");
```

**Purpose**: Carbon = area × age-class-specific carbon density (summed over age classes)

> **🔄 Changed 2026-04-20 (commit `c7731e234`)**: The density argument changed from `pm_carbon_density_secdforest_ac` (Module 52's FRA-calibrated curve) to `p35_carbon_density_secdforest` — a **blended** density computed in `presolve.gms:248-252` that weights the FRA-calibrated curve (existing/managed secdforest) and the uncalibrated natveg curve (natural-origin secdforest) by the per-age-class natural-origin share. See Section 5.1 for the blend formula and the natural-origin tracking mechanism.

**q35_carbon_primforest** (`equations.gms:42-44`):
```gams
vm_carbon_stock(j2,"primforest",ag_pools,stockType) =e=
  m_carbon_stock(vm_land,fm_carbon_density,"primforest");
```

**Purpose**: Primary forest carbon stock = area × carbon density. Uses the `m_carbon_stock` macro with `fm_carbon_density` (global, no age-class dimension since primforest is always mature).
**Key variables**: `vm_land(j,"primforest")` (area), `fm_carbon_density` (carbon density input from LPJmL)

**q35_carbon_other** (`equations.gms:53-55`):
```gams
vm_carbon_stock(j2,"other",ag_pools,stockType) =e=
  m_carbon_stock_ac(vm_land_other,p35_carbon_density_other,"othertype35,ac","othertype35,ac_sub");
```

**Purpose**: Other land carbon stock = sum over othertype35 and age classes of area × carbon density. Uses the age-class macro `m_carbon_stock_ac` because other land tracks age classes, and iterates over both other land subtypes (othernat, youngsecdf).
**Key variables**: `vm_land_other(j,othertype35,ac)` (area by subtype and age class), `p35_carbon_density_other` (age-class-specific carbon density)

#### 6.4 Biodiversity Value (BII)

**q35_bv_secdforest** (`equations.gms:63-66`):
```gams
vm_bv(j2,"secdforest",potnatveg) =e=
  sum(bii_class_secd, sum(ac_to_bii_class_secd(ac,bii_class_secd), v35_secdforest(j2,ac)) *
  fm_bii_coeff(bii_class_secd,potnatveg)) * fm_luh2_side_layers(j2,potnatveg);
```

**Purpose**: Biodiversity value = area × BII coefficient (by age class) × potential natural vegetation layer

**BII coefficients** increase with forest age (Module 44 provides coefficients)

**q35_bv_primforest** (`equations.gms:59-61`):
```gams
vm_bv(j2,"primforest",potnatveg) =e=
  vm_land(j2,"primforest") * fm_bii_coeff("primary",potnatveg) * fm_luh2_side_layers(j2,potnatveg);
```

**Purpose**: Biodiversity value of primary forest = area × BII coefficient for "primary" class × LUH2 potential natural vegetation share. Primary forest always uses the highest BII class ("primary"), which has a coefficient of 1.0.
**Key variables**: `vm_land(j,"primforest")` (area), `fm_bii_coeff("primary",potnatveg)` (BII coefficient), `fm_luh2_side_layers` (spatial mask for potential natural vegetation type)

**q35_bv_other** (`equations.gms:68-71`):
```gams
vm_bv(j2,"other",potnatveg) =e=
  sum(bii_class_secd, sum(ac_to_bii_class_secd(ac,bii_class_secd), sum(othertype35, vm_land_other(j2,othertype35,ac))) *
  fm_bii_coeff(bii_class_secd,potnatveg)) * fm_luh2_side_layers(j2,potnatveg);
```

**Purpose**: Biodiversity value of other land, calculated identically to secondary forest BII — area is mapped to BII age classes via `ac_to_bii_class_secd`, then multiplied by corresponding BII coefficients and the LUH2 potential vegetation layer. Sums across both other land subtypes (othernat, youngsecdf).
**Key variables**: `vm_land_other(j,othertype35,ac)` (area by subtype and age), `ac_to_bii_class_secd` (mapping from age class to BII class), `fm_bii_coeff`, `fm_luh2_side_layers`

#### 6.5 Harvest Constraints

**q35_hvarea_secdforest** (`equations.gms:176-179`):
```gams
v35_hvarea_secdforest(j2,ac_sub) =l= v35_secdforest_reduction(j2,ac_sub);
```

**Purpose**: Harvested area ≤ area reduction (not all reduction is harvest - some is conversion)

**q35_hvarea_primforest** (`equations.gms:181-184`):
```gams
v35_hvarea_primforest(j2) =l= v35_primforest_reduction(j2);
```

**Purpose**: Harvested area from primary forest ≤ total primary forest reduction. Not all primary forest loss is timber harvest — some may be land use conversion.
**Key variables**: `v35_hvarea_primforest` (harvest area), `v35_primforest_reduction` (total area reduction)

**q35_hvarea_other** (`equations.gms:186-189`):
```gams
v35_hvarea_other(j2,othertype35,ac_sub) =l= v35_other_reduction(j2,othertype35,ac_sub);
```

**Purpose**: Harvested area from other land ≤ total other land reduction, by subtype and age class.
**Key variables**: `v35_hvarea_other` (harvest area by subtype and age), `v35_other_reduction` (total area reduction by subtype and age)

#### 6.6 Timber Production

> **🔄 Updated 2026-04-20 (PR #869):** Formerly *pm_timber_yield* (tDM/ha/yr, flux) → `im_growing_stock` (tDM/ha, stock). Same formula structure; consumers still divide by `m_timestep_length_forestry` to recover an annual flux. `im_growing_stock` is now provided by **Module 14** (was already Module 14's responsibility; just renamed). Under the new default `s52_growingstock_calib = 1`, the underlying `pm_carbon_density_secdforest_ac(vegc)` is calibrated to FRA 2025 NRF growing stock before M14 computes `im_growing_stock`.

**q35_prod_secdforest** (`equations.gms:144-147`):
```gams
sum(kforestry, vm_prod_natveg(j2,"secdforest",kforestry))
=e=
sum(ac_sub, v35_hvarea_secdforest(j2,ac_sub) * sum(ct,im_growing_stock(ct,j2,ac_sub,"secdforest"))) / m_timestep_length_forestry;
```

**Purpose**: Production = harvested area × growing stock / timestep length

**q35_prod_primforest** (`equations.gms:153-156`):
```gams
sum(kforestry, vm_prod_natveg(j2,"primforest",kforestry))
=e=
v35_hvarea_primforest(j2) * sum(ct, im_growing_stock(ct,j2,"acx","primforest")) / m_timestep_length_forestry;
```

**Purpose**: Woody biomass production from primary forest = harvested area × growing stock at mature age class ("acx") / timestep length. Primary forest always uses the "acx" value since it is assumed mature.
**Key variables**: `v35_hvarea_primforest` (harvest area), `im_growing_stock(t,j,"acx","primforest")` (stem biomass at mature age class), `m_timestep_length_forestry` (timestep divisor)

**q35_prod_other** (`equations.gms:162-168`):
```gams
sum(kforestry, vm_prod_natveg(j2,"other",kforestry))
=e=
(sum(ac_sub, v35_hvarea_other(j2,"othernat",ac_sub) * sum(ct, im_growing_stock(ct,j2,ac_sub,"other")))
+ sum(ac_sub, v35_hvarea_other(j2,"youngsecdf",ac_sub) * sum(ct, im_growing_stock(ct,j2,ac_sub,"secdforest"))))
/ m_timestep_length_forestry;
```

**Purpose**: Woody biomass production from other land. `othernat` uses "other" growing stock while `youngsecdf` uses "secdforest" growing stock (since young secondary forest has timber characteristics closer to secondary forest). Both are summed and divided by timestep length.
**Key variables**: `v35_hvarea_other` (harvest area by subtype and age), `im_growing_stock` (values differ by subtype: "other" vs "secdforest")

#### 6.7 Regeneration

**q35_secdforest_regeneration** (`equations.gms:208-214`):
```gams
sum(ac_est, v35_secdforest(j2,ac_est))
=e=
sum(ac_sub,v35_hvarea_secdforest(j2,ac_sub))
+ v35_hvarea_primforest(j2)
+ p35_land_restoration(j2,"secdforest");
```

**Purpose**: New secondary forest = harvested secondary + harvested primary + restoration

**CRITICAL**: Harvested primary forest becomes secondary forest (one-way transition)

**q35_other_regeneration** (`equations.gms:218-223`):
```gams
sum(ac_est, vm_land_other(j2,"othernat",ac_est))
=e=
sum((othertype35,ac_sub),v35_hvarea_other(j2,othertype35,ac_sub))
+ vm_landexpansion(j2,"other");
```

**Purpose**: New other natural land in establishment age classes = harvested other land (from both subtypes) + land expansion into "other". Harvested other land regenerates as `othernat` regardless of its original subtype. Land expansion (from agricultural abandonment via Module 10) also enters as `othernat`.
**Key variables**: `vm_land_other(j,"othernat",ac_est)` (new other land), `v35_hvarea_other` (harvested area), `vm_landexpansion(j,"other")` (land expansion from Module 10)

**q35_secdforest_est** (`equations.gms:228-229`):
```gams
v35_secdforest(j2,ac_est) =e= sum(ac_est2, v35_secdforest(j2,ac_est2)) / card(ac_est2);
```

**Purpose**: Distributes new secondary forest additions equally across establishment age classes (`ac_est`). For a 10-year timestep, `ac_est` = {ac0, ac5}, so each gets half. This ensures uniform distribution of new area across the establishment period.
**Key variables**: `v35_secdforest(j,ac_est)` (secdforest in establishment classes), `ac_est2` (alias for `ac_est`), `card(ac_est2)` (number of establishment classes)

**q35_other_est** (`equations.gms:231-232`):
```gams
vm_land_other(j2,"othernat",ac_est) =e= sum(ac_est2, vm_land_other(j2,"othernat",ac_est2)) / card(ac_est2);
```

**Purpose**: Distributes new other natural land additions equally across establishment age classes, analogous to `q35_secdforest_est`. Only applies to `othernat` subtype (not `youngsecdf`, which is handled via forest recovery in presolve).
**Key variables**: `vm_land_other(j,"othernat",ac_est)`, `ac_est2`, `card(ac_est2)`

#### 6.8 Maximum Forest Establishment

**q35_max_forest_establishment** (`equations.gms:196-201`):
```gams
sum(land_forest, vm_landexpansion(j2,land_forest))
=l=
sum(ct,pm_max_forest_est(ct,j2))
- sum(ac, vm_land_other(j2,"youngsecdf",ac) );
```

**Purpose**: Total forest expansion (natural + managed) ≤ potential forest area - existing youngsecdf

**Provides constraint** to Module 32 (forestry) for plantation establishment

#### 6.9 Land Change Tracking (Expansion, Reduction, Diff)

*' The following technical calculations are needed for reducing differences in land-use patterns between time steps.

**q35_other_expansion** (`equations.gms:100-102`):
```gams
v35_other_expansion(j2,othertype35) =e= sum(ac_est, vm_land_other(j2,othertype35,ac_est));
```

**Purpose**: Other land expansion = area in establishment age classes. Expansion is defined as new area appearing in the youngest age classes relative to the previous timestep.
**Key variables**: `v35_other_expansion` (gross expansion), `vm_land_other(j,othertype35,ac_est)` (area in establishment classes)

**q35_other_reduction** (`equations.gms:104-106`):
```gams
v35_other_reduction(j2,othertype35,ac_sub) =e=
  pc35_land_other(j2,othertype35,ac_sub) - vm_land_other(j2,othertype35,ac_sub);
```

**Purpose**: Other land reduction per subtype and age class = previous area (`pc35_land_other`, fixed in presolve after aging) minus current optimized area. Positive values indicate land was converted away.
**Key variables**: `pc35_land_other` (previous timestep area after aging), `vm_land_other` (current optimized area)

**q35_secdforest_expansion** (`equations.gms:108-110`):
```gams
v35_secdforest_expansion(j2) =e= sum(ac_est, v35_secdforest(j2,ac_est));
```

**Purpose**: Secondary forest expansion = area in establishment age classes. Analogous to other land expansion.
**Key variables**: `v35_secdforest_expansion`, `v35_secdforest(j,ac_est)`

**q35_secdforest_reduction** (`equations.gms:112-114`):
```gams
v35_secdforest_reduction(j2,ac_sub) =e=
  pc35_secdforest(j2,ac_sub) - v35_secdforest(j2,ac_sub);
```

**Purpose**: Secondary forest reduction per age class = previous area minus current optimized area.
**Key variables**: `pc35_secdforest` (previous timestep area after aging), `v35_secdforest` (current optimized area)

**q35_primforest_reduction** (`equations.gms:116-118`):
```gams
v35_primforest_reduction(j2) =e=
  pcm_land(j2,"primforest") - vm_land(j2,"primforest");
```

**Purpose**: Primary forest reduction = previous area minus current area. Since primary forest has no age classes, this is a simple scalar difference per cluster.
**Key variables**: `pcm_land(j,"primforest")` (previous timestep area), `vm_land(j,"primforest")` (current area)

**q35_natforest_reduction** (`equations.gms:84-85`):
```gams
vm_natforest_reduction(j2) =e=
  v35_primforest_reduction(j2) + sum(ac_sub, v35_secdforest_reduction(j2,ac_sub));
```

**Purpose**: Total natural forest reduction = primary forest reduction + sum of secondary forest reduction across all age classes. This interface variable is provided to other modules (e.g. Module 73 timber).
**Key variables**: `vm_natforest_reduction` (total natural forest loss), `v35_primforest_reduction`, `v35_secdforest_reduction`

**q35_landdiff** (`equations.gms:92-98`):
```gams
vm_landdiff_natveg =e=
  sum(j2,
      sum(othertype35, v35_other_expansion(j2,othertype35))
      + sum((othertype35,ac_sub), v35_other_reduction(j2,othertype35,ac_sub))
      + v35_secdforest_expansion(j2)
      + sum(ac_sub, v35_secdforest_reduction(j2,ac_sub))
      + v35_primforest_reduction(j2));
```

**Purpose**: Aggregated gross change in natural vegetation across all clusters. Sums all expansion and reduction variables. This value is passed to Module 10 (land) to minimize land-use pattern oscillations between timesteps — the objective function penalizes large `vm_landdiff_natveg` values to encourage stability.
**Key variables**: `vm_landdiff_natveg` (global scalar), all expansion and reduction variables above

#### 6.10 Harvest Costs

**q35_cost_hvarea** (`equations.gms:132-138`):
```gams
vm_cost_hvarea_natveg(i2) =e=
  sum((ct,cell(i2,j2),ac_sub), v35_hvarea_secdforest(j2,ac_sub)) * s35_timber_harvest_cost_secdforest
+ sum((ct,cell(i2,j2),othertype35,ac_sub), v35_hvarea_other(j2,othertype35,ac_sub)) * s35_timber_harvest_cost_other
+ sum((ct,cell(i2,j2)), v35_hvarea_primforest(j2)) * s35_timber_harvest_cost_primforest;
```

**Purpose**: Total harvest cost per economic region (i) = harvested area × per-hectare cost for each land type. Costs are differentiated: primary forest ($3,690/ha) > other land ($3,075/ha) > secondary forest ($2,460/ha). Higher costs for primary forest mimic access difficulties. Aggregated from cluster (j) to regional (i) level via `cell(i,j)` mapping.
**Key variables**: `vm_cost_hvarea_natveg(i)` (total cost, passed to Module 11), `v35_hvarea_secdforest`, `v35_hvarea_other`, `v35_hvarea_primforest` (harvested areas), `s35_timber_harvest_cost_*` (per-hectare cost scalars)

---

### 7. Harvest System

#### 7.1 Harvest Costs (Differentiated)

**VERIFIED** (`input.gms:22-24`):
- **Primary forest**: `s35_timber_harvest_cost_primforest = 3690 USD17MER/ha`
- **Other land**: `s35_timber_harvest_cost_other = 3075 USD17MER/ha`
- **Secondary forest**: `s35_timber_harvest_cost_secdforest = 2460 USD17MER/ha`

**Rationale** (`equations.gms:124-129`):
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

**VERIFIED** (`presolve.gms:274-282`):
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

**VERIFIED** (`presolve.gms:155-160` and `input.gms:25`):
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

**VERIFIED** (`presolve.gms:268-272`):
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

**Applied in presolve** (`presolve.gms:140-234`):
- Sets lower bounds on land areas
- Distributes protection across age classes proportionally
- Ensures restoration targets are met

#### 8.2 NPI/NDC Policies (Country-Specific)

**VERIFIED** (`input.gms:8-9`, `preloop.gms:70-71`):
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

**Ramp-up**: Policies ramp up until 2030, constant thereafter (`realization.gms:17-23`)

**NPI/NDC Reversal**: Optional switch to remove policies after a year (`presolve.gms:262-266`)

**CRITICAL** (`presolve.gms:258-260`):
```gams
p35_min_forest(t,j)$(p35_min_forest(t,j) > pcm_land(j,"primforest") + pcm_land(j,"secdforest") + pcm_land(j,"forestry"))
  = pcm_land(j,"primforest") + pcm_land(j,"secdforest") + pcm_land(j,"forestry");
```

**Meaning**: Targets cannot exceed current forest area (no retroactive requirements)

#### 8.3 Protection Distribution

**VERIFIED** (`presolve.gms:172-180`):
```gams
* Secondary forest conservation
p35_protection_dist(j,ac_sub)$(sum(ac_sub2,pc35_secdforest(j,ac_sub2)) > 0) = pc35_secdforest(j,ac_sub) / sum(ac_sub2,pc35_secdforest(j,ac_sub2));
...
if (sum(sameas(t_past,t),1) = 1,
v35_secdforest.lo(j,ac_sub) = max(pm_land_conservation(t,j,"secdforest","protect") * p35_protection_dist(j,ac_sub), pc35_secdforest_natural(j,ac_sub));
else
v35_secdforest.lo(j,ac_sub) = max((1-s35_natveg_harvest_shr) * pc35_secdforest(j,ac_sub), pm_land_conservation(t,j,"secdforest","protect") * p35_protection_dist(j,ac_sub), pc35_secdforest_natural(j,ac_sub));
);
```

**Mechanism**: Protection distributed proportionally across age classes based on current area. As of 2026-04-20 (commit `c7731e234`), the lower bound also includes `pc35_secdforest_natural(j,ac_sub)` so natural-origin secondary forest is protected from harvest — see Section 5.1.

---

### 9. Configuration Options

#### 9.1 Disturbance Mode

**s35_forest_damage** (scalar, 0-4):
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
- `pm_carbon_density_secdforest_ac(t,j,ac,ag_pools)` - Age-class carbon density, FRA-calibrated natveg curve (used for existing/managed secdforest)
- `pm_carbon_density_secdforest_ac_uncalib(t,j,ac,ag_pools)` - Age-class carbon density, uncalibrated natveg curve (used for natural-origin secdforest, youngsecdf, and the 20 tC/ha maturation test) — new consumer 2026-04-20
- `pm_carbon_density_other_ac(t,j,ac,ag_pools)` - Other land carbon density
- `fm_carbon_density(t,j,land,ag_pools)` - Primary forest carbon density

**From Module 14 (Yields)** (was previously attributed to Module 73; corrected 2026-04-20):
- `im_growing_stock(t,j,ac,land_timber)` — Harvestable stem biomass by age class (tDM/ha). Renamed 2026-04-20 from *pm_timber_yield* (tDM/ha/yr); semantic changed from flux to stock.

**From Module 44 (Biodiversity)**:
- `fm_bii_coeff(bii_class,potnatveg)` - Biodiversity intactness coefficients

---

### 10.1. Participates In

#### Conservation Laws

**Land Balance**: ✅ **CRITICAL PARTICIPANT (RESIDUAL ALLOCATOR)** - Module 35 receives land NOT claimed by other modules: `vm_land(j,"primforest")`, `v35_secdforest(j,ac)`, `vm_land_other(j,othertype,ac)`. Three land types: primary forest, secondary forest (age-classes 1-15), other land (grassland, shrubland, etc.). **CRITICAL ROLE**: Natural vegetation is the **RESIDUAL** in land balance - it absorbs consequences of all other land use decisions. Conservation constraints must be met: NPI/NDC/protected area targets enforced via Module 22.

**Carbon Balance**: ✅ **CRITICAL PARTICIPANT (DOMINANT POOL)** - Natural vegetation holds **LARGEST carbon stocks** in model. Chapman-Richards growth: `vegc(age) = A × (1-exp(-k×age))^m`. Three pools: vegetation (age-dependent), litter, soil. Disturbances (fire, shifting agriculture, generic shocks) trigger carbon loss. **Avoided deforestation** is major carbon mitigation strategy (via Module 56 policy constraints).

**Food Balance**: ❌ Does NOT participate (natural vegetation does not supply food)

**Water Balance**: ⚠️ **INDIRECT** - Natural vegetation changes affect water availability (deforestation reduces evapotranspiration)

**Nitrogen**: ⚠️ **INDIRECT** - Forest N through soil carbon dynamics (Module 59)

**Cross-Reference**: `cross_module/land_balance_conservation.md` (Section 5.7, "Module 35 Complex Age-Class Dynamics"), `cross_module/carbon_balance_conservation.md` (Sections 3.5-3.6, "Natural Vegetation Carbon")

---

#### Dependency Chains

**Centrality**: **Rank 10 of 46** modules (HIGH centrality)
**Total Connections**: **12** (provides to 5, depends on 7)
**Hub Type**: Central Hub (land residual + carbon dynamics + conservation)

**Provides To**: Module 10 (Land), Module 11 (Costs), Module 22 (Conservation - eligible restoration area), Module 32 (Forestry - max forest establishment potential), Module 52 (Carbon - natural vegetation carbon stocks), Module 56 (GHG policy - avoided deforestation potential), Module 73 (Timber - harvest production)

**Depends On**: Module 10 (Land - available land after other allocations), Module 22 (Conservation - protection/restoration targets), Module 28 (Age Class - age-class structure), Module 32 (Forestry - land competition), Module 44 (Biodiversity - BII calculations reference), plus 2 others

**Key Role**: **RESIDUAL LAND ALLOCATOR** + **LARGEST CARBON POOL** + **CONSERVATION ENFORCEMENT**

---

#### Circular Dependencies

**Participates In**: **3+ circular dependency cycles** (one of most complex modules)

**Cycle 1**: Land ↔ NatVeg ↔ Conservation (land-vegetation-protection triangle)
**Resolution**: Type 2 - Simultaneous equations

**Cycle 2**: NatVeg ↔ Forestry (land competition for afforestation)
**Resolution**: Type 2 - Simultaneous equations

**Cycle 3**: NatVeg ↔ Carbon ↔ GHG Policy (avoided deforestation)
**Structure**: Module 35 → Module 52 (carbon stocks) → Module 56 (carbon pricing / avoided deforestation policy) → **back to Module 35** (deforestation constraints)
**Resolution**: Type 1 + 2 (Temporal feedback + Simultaneous equations)

**Risk**: Module 35 is central to **MOST COMPLEX FEEDBACK LOOP** in MAgPIE (5-module Forest-Carbon-Price cycle via Module 32). Changes can destabilize carbon accounting or land allocation.

**Reference**: `cross_module/circular_dependency_resolution.md` (Sections 3.2, 3.4)

---

#### Modification Safety

**Risk Level**: 🔴 **EXTREME RISK**

**Justification**: Rank 10 of 46, 12 connections, 3+ circular cycles, CRITICAL for land balance (residual allocator), CRITICAL for carbon balance (largest natural carbon pool), CRITICAL for conservation policies, affects 7+ downstream modules including core modules 10, 52, 56

**Safe**: Adjusting disturbance rates, changing age-class progression logic, modifying BII coefficients, updating harvest rules
**Dangerous**: Removing residual land allocation (breaks land balance), hardcoding natural vegetation area (prevents land use change), changing age-class dynamics (affects carbon growth), modifying conservation enforcement (violates NPI/NDC targets)
**Required Testing**: ALL 5 conservation laws (land is CRITICAL, carbon is CRITICAL), age-class dynamics convergence, conservation target feasibility, circular dependency cycles stable
**Common Issues**: Conservation targets exceed available land (infeasibility) → reduce protection ambition; Age-class dynamics unstable (carbon stocks oscillate) → check disturbance rates and growth parameters; Deforestation unrealistic (too fast/slow) → adjust land competition costs

**CRITICAL IMPORTANCE**: Module 35 is the **RESIDUAL ALLOCATOR** for land - it receives whatever land is NOT used by agriculture/forestry/urban. It also holds the **LARGEST CARBON STOCKS**. Any modification affects:
- ✅ Land balance (CRITICAL - residual must absorb all other land use)
- ✅ Carbon balance (CRITICAL - natural vegetation is dominant carbon pool)
- ✅ Conservation policies (NPI/NDC/protected areas enforced here)
- ✅ Avoided deforestation potential (climate mitigation)

**File Complexity**: 1,085 lines across 9 files, 32 equations - one of the most complex modules in MAgPIE.

**Reference**: `cross_module/modification_safety_guide.md` (HIGH RISK - Complex land and carbon dynamics)

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

2. **Forest maturation threshold** (`presolve.gms:116-122`):
   - ❌ Hard 20 tC/ha cutoff for forest/other land classification
   - Reality: Gradual transition, regional variation

3. **Primary to secondary transition** (`realization.gms:35-36`):
   - ❌ Harvested primary forest becomes secondary (one-way, irreversible)
   - Reality: Very old secondary forest can approach primary characteristics

4. **Harvest impact** (`equations.gms:208-214`):
   - ❌ Harvested secondary forest stays secondary (doesn't reset to young)
   - Reality: Clear-cutting resets succession; selective logging doesn't

5. **Biodiversity** (`equations.gms:59-71`):
   - ❌ BII coefficients globally uniform (no regional variation)
   - Reality: Biodiversity value varies by region, ecosystem type

6. **Age-class initialization** (`realization.gms:30-34`):
   - ❌ MODIS data available but causes negative LUC emissions
   - ❌ Current default: Poulter distribution or equal/acx only
   - Reality: Actual age distribution more complex

7. **Restoration** (`presolve.gms:191-198`):
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

**Complexity**: VERY HIGH (1,085 lines, 32 equations, 8 files)

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
- `equations.gms` (229 lines) - 32 equations for land, carbon, harvest, BII
- `postsolve.gms` (203 lines) - State updates

**AI Response Pattern**:
- Cite specific equations and line numbers (32 equations available)
- Clarify forest vs. other land threshold (20 tC/ha)
- Distinguish primary/secondary/other land dynamics
- Warn about age-class complexity when modifying
- Check Modules 32 (forestry), 52 (carbon), 73 (timber) for dependencies
- Emphasize disturbance limitations (no spatial dynamics)

---

**Last Verified**: 2026-05-16 (sync — natural-origin tracking for secdforest carbon density)
**Verified Against**: `../modules/35_natveg/pot_forest_may24/*.gms`
**Verification Method**: Equations cross-referenced with source code
**Changes Since Last Verification**: 2026-05-16 sync to commit `c7731e234` (+ refactor `2fa7b8bea`): added Section 5.1 (natural-origin tracking for secondary forest carbon density); new parameters `p35_secdforest_natural`, `pc35_secdforest_natural`, `p35_carbon_density_secdforest`; `q35_carbon_secdforest` now uses blended density `p35_carbon_density_secdforest`; 20 tC/ha maturation test now uses `pm_carbon_density_secdforest_ac_uncalib`; updated file sizes.

## Interface Variables

### Provided to Other Modules

| Variable | Dimensions | Description | Units |
|----------|------------|-------------|-------|
| `vm_land_other` | `(j,othertype35,ac)` | Detailed stock of other land | mio. ha |
| `vm_prod_natveg` | `(j,land_natveg,kforestry)` | Production of woody biomass from natural vegetation | mio. tDM/yr |
| `vm_cost_hvarea_natveg` | `(i)` | Cost of harvesting natural vegetation | mio. USD17MER |
| `vm_natforest_reduction` | `(j)` | Natural forest reduction | mio. ha |
| `pm_max_forest_est` | `(t,j)` | Overall forest establishment potential in current time step | mio. ha |

**Source**: `declarations.gms` (verified against GAMS code)

### Received from Other Modules

Key input variables from other modules are documented in the Dependencies section.

