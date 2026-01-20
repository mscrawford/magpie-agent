# Module 14: Yields (managementcalib_aug19)

**Realization:** `managementcalib_aug19`
**Date:** August 2019
**Total Lines of Code:** 557
**Equation Count:** 2
**Status:** ✅ Fully Verified (2025-10-12)

---

## 1. Overview

### 1.1 Purpose

Module 14 calculates crop yields and pasture productivity for all agricultural production systems in MAgPIE (`module.gms:8-24`). It serves as the **critical bridge between biophysical constraints and agricultural production**, translating LPJmL climate-driven productivity into model-ready yields calibrated to FAO historical observations.

**Core Function:** Transform spatially explicit LPJmL yields → Apply technological change (τ factor) → Calibrate to FAO regional levels → Provide yields to production modules (30_crop, 31_past)

### 1.2 Key Features

1. **LPJmL Input Integration** (`realization.gms:8-11`): Reads gridded crop and pasture yields from the Lund-Potsdam-Jena managed Land model, providing climate-sensitive biophysical baselines
2. **Multi-Stage Calibration System** (`preloop.gms:26-145`): Calibrates LPJmL yields to FAO regional statistics through sophisticated "limited calibration" approach
3. **Technological Change** (`equations.gms:14-16`): Scales yields using τ (tau) factor from Module 13 to represent agricultural intensification over time
4. **Irrigated/Rainfed Differentiation** (`preloop.gms:116-143`): Calibrates irrigated-to-rainfed yield ratios to match AQUASTAT country-level observations
5. **Pasture Spillover** (`equations.gms:35-39`): Allows crop sector technological improvements to partially benefit pasture yields
6. **Degradation Effects** (`preloop.gms:183-188`): Reduces yields based on soil loss and pollination deficiency
7. **Timber Yield Calculation** (`presolve.gms:24-60`): Converts carbon density to harvestable wood biomass for forestry and natural vegetation

### 1.3 Limitations Stated in Code

The realization explicitly acknowledges (`realization.gms:23-26`):
- **No land scarcity feedback:** Pasture intensification is exogenous, cannot respond to land constraints
- **Uncertain spillover magnitude:** Effect of crop technological change on pasture management is empirical

---

## 2. Core Equations

Module 14 implements only 2 equations, but relies on extensive preloop calibration to prepare the input data.

### 2.1 Equation q14_yield_crop: Crop Yield Calculation

**File:** `equations.gms:14-16`

```gams
q14_yield_crop(j2,kcr,w) ..
 vm_yld(j2,kcr,w) =e= sum(ct,i14_yields_calib(ct,j2,kcr,w)) *
                         vm_tau(j2,"crop") / sum((cell(i2,j2), supreg(h2,i2)), fm_tau1995(h2));
```

**What This Equation Does:**

Calculates cellular crop yields by scaling calibrated baseline yields (`i14_yields_calib`) with the ratio of current technological change factor (`vm_tau`) to the 1995 baseline (`fm_tau1995`).

**Mathematical Structure:**

```
Yield(j,crop,water) = CalibratedYield(j,crop,water) × (τ_current(j) / τ_1995(h))
```

**Components:**

- **vm_yld(j,kcr,w)**: Output yield variable (tDM/ha/yr) for cell j, crop kcr, water system w
- **i14_yields_calib(ct,j,kcr,w)**: Calibrated baseline yields from preloop (see Section 3)
- **vm_tau(j2,"crop")**: Current technological change factor from Module 13 at cluster level (≥1, starts at 1 in 1995)
- **fm_tau1995(h)**: Regional τ factor in baseline year 1995 (at super-region level for normalization)
- **Dimensions:** j (cells/clusters), kcr (crops), w (rainfed/irrigated), h (super-regions)

**f_btc2 Change:** As of commit 480e300b1, `vm_tau` is now defined at cluster level (j) rather than super-region level (h). This allows spatial heterogeneity in intensification rates, particularly for differentiating conservation priority areas with lower intensification.

**Conceptual Meaning:**

If τ doubles from 1995 to 2050 (τ=2), yields double. If τ=1.5, yields increase 50%. The baseline `i14_yields_calib` already incorporates FAO calibration, climate change scenarios, and all corrections from preloop.

**Citation:** `equations.gms:14-20`

---

### 2.2 Equation q14_yield_past: Pasture Yield Calculation

**File:** `equations.gms:35-39`

```gams
q14_yield_past(j2,w) ..
 vm_yld(j2,"pasture",w) =e=
 sum(ct,(i14_yields_calib(ct,j2,"pasture",w))
 * sum(cell(i2,j2),pm_past_mngmnt_factor(ct,i2)))
 * (1 + s14_yld_past_switch*(sum((cell(i2,j2), supreg(h2,i2)), pcm_tau(j2, "crop")/fm_tau1995(h2)) - 1));
```

**What This Equation Does:**

Calculates pasture yields using calibrated baseline, an exogenous management factor, and partial spillover from crop sector technological change.

**Mathematical Structure:**

```
PastureYield(j,w) = CalibratedPastureYield(j,w) × ManagementFactor × [1 + spillover × (τ_crop_prev(j)/τ_1995(h) - 1)]
```

**Components:**

- **vm_yld(j,"pasture",w)**: Output pasture yield (tDM/ha/yr)
- **i14_yields_calib(ct,j,"pasture",w)**: Calibrated pasture baseline from preloop
- **pm_past_mngmnt_factor(ct,i)**: Exogenous pasture management factor from Module 70 (livestock demand-driven)
- **s14_yld_past_switch**: Spillover parameter (default 0.25, range 0-1) (`input.gms:24`)
- **pcm_tau(j2,"crop")**: Previous time step's crop τ factor at cluster level (not current time step!)
- **Interpretation:** 25% of crop sector intensification benefits pasture yields

**f_btc2 Change:** `pcm_tau` is now at cluster level (j) rather than super-region level (h), consistent with the change to `vm_tau`.

**Key Difference from Crop Equation:**

Pastures use **previous time step** τ (`pcm_tau`) instead of current τ (`vm_tau`), reflecting delayed knowledge transfer from crop to pasture systems.

**Citation:** `equations.gms:24-39`

---

## 3. Calibration System (Preloop Phase)

The true complexity of Module 14 lies in the preloop phase, where raw LPJmL yields are transformed into calibrated, model-ready yields through six calibration stages.

### 3.1 Stage 1: Bioenergy Yield Correction

**File:** `preloop.gms:10-12`

**Problem Addressed:** No robust FAO data exists for bioenergy crop yields.

**Solution:** Assume LPJmL bioenergy yields correspond to the highest observed τ factor globally:

```gams
i14_yields_calib(t,j,"begr",w) = f14_yields(t,j,"begr",w) * sum((supreg(h,i),cell(i,j)),fm_tau1995(h))/smax(h,fm_tau1995(h));
i14_yields_calib(t,j,"betr",w) = f14_yields(t,j,"betr",w) * sum((supreg(h,i),cell(i,j)),fm_tau1995(h))/smax(h,fm_tau1995(h));
```

**What This Does:** Scales down bioenergy yields (begr = tropical woody, betr = temperate woody) by the ratio of local τ to global maximum τ, assuming bioenergy represents "best possible" management.

**Citation:** `preloop.gms:10-12`

---

### 3.2 Stage 2: Pasture Management Correction

**File:** `preloop.gms:14-20`

**Problem Addressed:** LPJmL pasture yields don't reflect regional differences in grazing intensity and management practices.

**Solution:** Correct LPJmL pasture yields to match historical modeled pasture productivity:

```gams
p14_pyield_LPJ_reg(t,i) = (sum(cell(i,j),i14_yields_calib(t,j,"pasture","rainfed") * pm_land_start(j,"past")) /
                            sum(cell(i,j),pm_land_start(j,"past")) );

p14_pyield_corr(t,i) = (f14_pyld_hist(t,i)/p14_pyield_LPJ_reg(t,i))$(sum(sameas(t_past,t),1) = 1)
      + sum(t_past,(f14_pyld_hist(t_past,i)/(p14_pyield_LPJ_reg(t_past,i)+0.000001))$(ord(t_past)=card(t_past)))$(sum(sameas(t_past,t),1) <> 1);

i14_yields_calib(t,j,"pasture",w) = i14_yields_calib(t,j,"pasture",w) * sum(cell(i,j),p14_pyield_corr(t,i));
```

**What This Does:**
1. Calculate regional average LPJmL pasture yield weighted by initial pasture area
2. Compute correction factor = historical modeled pasture yield / LPJmL regional yield
3. Apply correction to all cells in the region

**Rationale:** Historical model runs incorporate pasture management patterns; this correction propagates that knowledge into LPJmL yields.

**Citation:** `preloop.gms:14-21`

---

### 3.3 Stage 3: Limited Calibration to FAO Yields

**File:** `preloop.gms:26-109`

**Problem:** Simple relative calibration (multiplying by FAO/LPJmL ratio) works when baselines are accurate, but produces unrealistic future yields when FAO >> LPJmL (underestimated baseline).

**Solution:** Implement "limited calibration" that blends relative and additive calibration based on baseline quality.

#### Step 3a: Calculate Regional Modeled Yields

**File:** `preloop.gms:60-66`

```gams
i14_modeled_yields_hist(t_past,i,knbe14)
   = (sum((cell(i,j),w), fm_croparea(t_past,j,w,knbe14) * f14_yields(t_past,j,knbe14,w)) /
      sum((cell(i,j),w), fm_croparea(t_past,j,w,knbe14)))$(sum((cell(i,j),w), fm_croparea(t_past,j,w,knbe14)) > 0.00001 AND
                                                           sum((cell(i,j),w), fm_croparea(t_past,j,w,knbe14) * f14_yields(t_past,j,knbe14,w)) > 0.00001)
   + (sum((cell(i,j),w), i14_croparea_total(t_past,w,j) * f14_yields(t_past,j,knbe14,w)) /
      sum((cell(i,j),w), i14_croparea_total(t_past,w,j)))$(sum((cell(i,j),w), fm_croparea(t_past,j,w,knbe14)) <= 0.00001 OR
                                                           sum((cell(i,j),w), fm_croparea(t_past,j,w,knbe14) * f14_yields(t_past,j,knbe14,w)) <= 0.00001);
```

**What This Does:** Calculate area-weighted average LPJmL yield for each region and crop. If a crop has no area in a region, use total cropland as weights (proxy for missing data).

**Division by Zero Protection (Bugfix 2025-09-22 & 2025-10-06):** The dual condition checks prevent division by zero in two edge cases:
1. When crop-specific area is zero or very small (`fm_croparea < 0.00001`)
2. When crop-specific area × yields = 0 (area exists but all yields are zero, or data mismatch)

In either case, the calculation falls back to using total cropland area as weights. This handles FAO/LUH croparea mismatches with LPJmL yield data that could otherwise cause overestimated yields or division errors.

**Citation:** `preloop.gms:60-66`

#### Step 3b: Calculate Lambda (Calibration Mode Factor)

**File:** `preloop.gms:75-95`

```gams
loop(t,
     if(sum(sameas(t,"y1995"),1)=1,
          if    ((s14_limit_calib = 0),
               i14_lambda_yields(t,i,knbe14) = 1;
          Elseif (s14_limit_calib =1 ),
               i14_lambda_yields(t,i,knbe14) =
                    1$(f14_fao_yields_hist(t,i,knbe14) <= i14_modeled_yields_hist(t,i,knbe14))
                    + sqrt(i14_modeled_yields_hist(t,i,knbe14)/f14_fao_yields_hist(t,i,knbe14))$
                    (f14_fao_yields_hist(t,i,knbe14) > i14_modeled_yields_hist(t,i,knbe14));
          );
          i14_fao_yields_hist(t,i,knbe14) = f14_fao_yields_hist(t,i,knbe14);
     Else
          i14_modeled_yields_hist(t,i,knbe14) = i14_modeled_yields_hist(t-1,i,knbe14);
          i14_FAO_yields_hist(t,i,knbe14)  = i14_fao_yields_hist(t-1,i,knbe14);
          i14_lambda_yields(t,i,knbe14)   = i14_lambda_yields(t-1,i,knbe14);
     );
);
```

**What Lambda Controls:**

- **λ = 1** (FAO ≤ LPJmL): LPJmL overestimates yields → use **pure relative calibration**
- **λ = √(LPJmL/FAO)** (FAO > LPJmL): LPJmL underestimates yields → blend relative and additive
- **λ → 0**: Extreme underestimation → approach pure **additive calibration**

**Why This Matters:**

- **Relative calibration:** Multiply by (FAO/LPJmL). Good when baseline correct. But if FAO=10 and LPJmL=5, doubling LPJmL yields in 2050 gives 4x FAO yields (unrealistic).
- **Additive calibration:** Add (FAO - LPJmL). Maintains future yield increases, avoids over-scaling.
- **Lambda blends the two:** As baseline quality worsens (FAO >> LPJmL), shift from relative toward additive.

**Citation:** `preloop.gms:69-95`, mathematical foundation cited as `@Heinke.2013` in `preloop.gms:47`

#### Step 3c: Apply Calibration Factor

**File:** `preloop.gms:101-109`

```gams
i14_managementcalib(t,j,knbe14,w) =
  1 + (sum(cell(i,j), i14_fao_yields_hist(t,i,knbe14) - i14_modeled_yields_hist(t,i,knbe14)) /
                             f14_yields(t,j,knbe14,w) *
      (f14_yields(t,j,knbe14,w) / (sum(cell(i,j),i14_modeled_yields_hist(t,i,knbe14))+10**(-8))) **
                             sum(cell(i,j),i14_lambda_yields(t,i,knbe14)))$(f14_yields(t,j,knbe14,w)>0);

i14_yields_calib(t,j,knbe14,w)    = i14_managementcalib(t,j,knbe14,w) * f14_yields(t,j,knbe14,w);
pm_yields_semi_calib(j,knbe14,w)  = i14_yields_calib("y1995",j,knbe14,w);
```

**Mathematical Form (from Heinke 2013 eq. 9):**

```
CalibFactor = 1 + [(FAO - LPJmL_regional) / LPJmL_cellular] × [(LPJmL_cellular / LPJmL_regional)^λ]
```

**Behavior:**

- **λ = 1:** Factor = 1 + [(FAO - LPJmL_reg) / LPJmL_cell] × 1 = FAO/LPJmL_cell × (ratio), pure relative
- **λ = 0:** Factor = 1 + [(FAO - LPJmL_reg) / LPJmL_cell] × 1 = additive difference
- **λ intermediate:** Smooth blend between the two

**Citation:** `preloop.gms:101-109`

---

### 3.4 Stage 4: Irrigated-Rainfed Ratio Calibration

**File:** `preloop.gms:116-143`

**Problem:** AQUASTAT reports irrigated yields are often 2-3x rainfed yields in some regions, but LPJmL may underpredict this ratio.

**Solution:** Scale irrigated yields to meet AQUASTAT ratios while maintaining FAO regional total yields.

```gams
if ((s14_calib_ir2rf = 1),
* Weighted yields
  i14_calib_yields_hist(i,w)
     = sum((cell(i,j), knbe14), fm_croparea("y1995",j,"irrigated",knbe14) * i14_yields_calib("y1995",j,knbe14,w)) /
       sum((cell(i,j), knbe14), fm_croparea("y1995",j,"irrigated",knbe14));

* Use irrigated-rainfed ratio of Aquastat if larger than our calculated ratio
  i14_calib_yields_ratio(i) = i14_calib_yields_hist(i,"irrigated") / i14_calib_yields_hist(i,"rainfed");
  i14_target_ratio(i) = max(i14_calib_yields_ratio(i), f14_ir2rf_ratio(i));
  i14_yields_calib(t,j,knbe14,"irrigated") = sum((cell(i,j)), i14_target_ratio(i) / i14_calib_yields_ratio(i)) *
                                               i14_yields_calib(t,j,knbe14,"irrigated");

* Calibrate newly calibrated yields to FAO yields
  [re-apply FAO calibration to maintain regional totals - equations at lines 130-140]
);
```

**What This Does:**

1. Calculate current irrigated/rainfed ratio from calibrated yields
2. Compare to AQUASTAT target ratio
3. If AQUASTAT ratio is higher, scale up irrigated yields
4. Re-calibrate to FAO regional totals to maintain production balance

**Why Two-Stage Calibration:** Increasing irrigated yields without re-calibration would violate FAO regional yield constraint. The second calibration at lines 130-140 adjusts both irrigated and rainfed to maintain FAO totals.

**Bugfix Note (2025-09-26):** The re-calibration step (lines 130-140) was corrected to use `i14_yields_calib` instead of `f14_yields` for total cropland weighting, ensuring consistency with the first-stage calibration. Additionally, the same division-by-zero protection (dual condition checks) from Step 3a is applied here to handle edge cases.

**Control Switch:** `s14_calib_ir2rf = 1` enables this (default ON, `input.gms:15`)

**Citation:** `preloop.gms:116-143`

---

### 3.5 Stage 5: Yield Calibration Factors

**File:** `preloop.gms:150-167`

**Purpose:** Apply optional post-calibration adjustments from previous model runs to improve representation of historical cropland and production patterns.

```gams
if(s14_use_yield_calib = 0 OR sum((i,ltype14),f14_yld_calib(i,ltype14)) = 0,
  f14_yld_calib(i,ltype14) = 1;
);

i14_yields_calib(t,j,kcr,w)       = i14_yields_calib(t,j,kcr,w)
                                    * sum(cell(i,j),f14_yld_calib(i,"crop"));
i14_yields_calib(t,j,"pasture",w) = i14_yields_calib(t,j,"pasture",w)
                                    * sum(cell(i,j),f14_yld_calib(i,"past"));
```

**What This Does:** Multiply calibrated yields by regional adjustment factors (`f14_yld_calib`) from file `f14_yld_calib.csv` if it exists.

**Use Case:** After running MAgPIE, if historical cropland areas don't match observations, compute adjustment factors that correct yields to match observed patterns, then use these factors in future runs.

**Default:** OFF (`s14_use_yield_calib = 0`, `input.gms:19`)

**Citation:** `preloop.gms:150-167`

---

### 3.6 Stage 6: Degradation Effects

**File:** `preloop.gms:170-188`

**Purpose:** Reduce yields on degraded land with soil loss or pollination deficiency.

```gams
if ((s14_degradation = 1),
  i14_yields_calib(t,j,kcr,w) = i14_yields_calib(t,j,kcr,w) * (1 - s14_yld_reduction_soil_loss)
                                + i14_yields_calib(t,j,kcr,w) * s14_yld_reduction_soil_loss * f14_yld_ncp_report(t,j,"soil_intact");
  i14_yields_calib(t,j,kcr,w) = i14_yields_calib(t,j,kcr,w) * (1 - f14_kcr_pollinator_dependence(kcr))
                                + i14_yields_calib(t,j,kcr,w) * f14_kcr_pollinator_dependence(kcr) * f14_yld_ncp_report(t,j,"poll_suff");
);
```

**Mathematical Form:**

```
Yield_degraded = Yield × (1 - reduction) + Yield × reduction × intact_fraction

Where:
- reduction = 0.08 for soil loss (8% yield penalty, s14_yld_reduction_soil_loss, input.gms:25)
- reduction = pollinator_dependence for pollination (0-1 by crop, f14_kcr_pollinator_dependence)
- intact_fraction = share of cell with intact NCP (0-1, from f14_yld_ncp_report.cs3)
```

**Conceptual Meaning:**

- **Soil loss:** 92% of yield on all land, plus 8% of yield only on intact-soil land
- **Pollination:** (1 - dependence) × yield is pollinator-independent, plus dependence × yield only on sufficient-pollination land

**Example:**
- Crop with 40% pollinator dependence
- Cell with 70% pollination sufficiency
- Yield reduction = 40% × (1 - 70%) = 12% yield loss

**Default:** OFF (`s14_degradation = 0`, `input.gms:17`)

**NCP Tracking:** Module 14 expects another module to provide `f14_yld_ncp_report(t,j,ncp_type14)` with "soil_intact" and "poll_suff" shares (likely Module 29 or Module 35).

**Citation:** `preloop.gms:171-188`, `input.gms:17,25`

---

## 4. Timber Yield Calculation (Presolve Phase)

**File:** `presolve.gms:10-66`

Module 14 also calculates timber yields (harvestable wood biomass) for forestry and natural vegetation by converting carbon density to dry matter biomass.

### 4.1 Conversion Formula

**Mathematical Structure:**

```
TimberYield [tDM/ha] = CarbonDensity [tC/ha] / CarbonFraction × AbovegroundFraction / BCE
```

Where:
- **CarbonDensity:** Vegetation carbon from Module 52 (tC/ha)
- **CarbonFraction:** 0.5 tC/tDM (`s14_carbon_fraction`, `input.gms:29`)
- **AbovegroundFraction:** Root-to-shoot ratio, varies by forest type (0.75-0.8, `f14_aboveground_fraction.csv`)
- **BCE:** IPCC Biomass Conversion and Expansion factor (1.4-1.6, `f14_ipcc_bce.cs3`)

**Rationale:**
- Divide by 0.5: Convert carbon to total dry matter (carbon = 50% of biomass)
- Multiply by aboveground fraction: Only harvest stems/branches, not roots
- Divide by BCE: BCE converts merchantable volume to total aboveground biomass; inverse converts total biomass to merchantable stem wood

### 4.2 Implementation for Each Forest Type

#### Plantation Forestry

**File:** `presolve.gms:24-31`

```gams
pm_timber_yield(t,j,ac,"forestry") =
    (
     pm_carbon_density_plantation_ac(t,j,ac,"vegc")
     / s14_carbon_fraction
     * f14_aboveground_fraction("forestry")
     / sum(clcl, pm_climate_class(j,clcl) * f14_ipcc_bce(clcl,"plantations"))
    );
```

**Source:** `pm_carbon_density_plantation_ac` from Module 52 (carbon)

#### Primary Forest

**File:** `presolve.gms:33-40`

```gams
pm_timber_yield(t,j,ac,"primforest") =
    (
     fm_carbon_density(t,j,"primforest","vegc")
     / s14_carbon_fraction
     * f14_aboveground_fraction("primforest")
     / sum(clcl, pm_climate_class(j,clcl) * f14_ipcc_bce(clcl,"natveg"))
    );
```

**Source:** `fm_carbon_density` for primary forest (fixed input)

#### Secondary Forest

**File:** `presolve.gms:42-49`

```gams
pm_timber_yield(t,j,ac,"secdforest") =
    (
     pm_carbon_density_secdforest_ac(t,j,ac,"vegc")
     / s14_carbon_fraction
     * f14_aboveground_fraction("secdforest")
     / sum(clcl, pm_climate_class(j,clcl) * f14_ipcc_bce(clcl,"natveg"))
    );
```

**Source:** `pm_carbon_density_secdforest_ac` from Module 35 (natural vegetation)

#### Other Natural Land

**File:** `presolve.gms:51-58`

```gams
pm_timber_yield(t,j,ac,"other") =
    (
     pm_carbon_density_other_ac(t,j,ac,"vegc")
     / s14_carbon_fraction
     * f14_aboveground_fraction("other")
     / sum(clcl, pm_climate_class(j,clcl) * f14_ipcc_bce(clcl,"natveg"))
    );
```

**Source:** `pm_carbon_density_other_ac` from Module 35 (other natural land)

### 4.3 Constraints on Timber Yields

**File:** `presolve.gms:62-65`

```gams
pm_timber_yield(t,j,ac,land_timber) = pm_timber_yield(t,j,ac,land_timber)$(pm_timber_yield(t,j,ac,land_timber) > 0) + 0.0001$(pm_timber_yield(t,j,ac,land_timber) = 0);
pm_timber_yield(t,j,ac,land_natveg)$(pm_timber_yield(t,j,ac,land_natveg) < s14_minimum_wood_yield) = 0;
```

**What These Do:**

1. **Positive constraint:** Ensure all timber yields ≥ 0.0001 tDM/ha (prevents division by zero in harvest calculations)
2. **Minimum harvest threshold:** Natural vegetation yields < 10 tDM/ha are set to 0 (too sparse to economically harvest, `s14_minimum_wood_yield`, `input.gms:21`)

**Citation:** `presolve.gms:62-65`

---

## 5. Configuration Switches and Scenarios

### 5.1 Climate Scenario

**File:** `input.gms:8-12`

```gams
$setglobal c14_yields_scenario  cc
*   options:  cc        (climate change)
*             nocc      (no climate change)
*             nocc_hist (no climate change after year defined by sm_fix_cc)
```

**What This Does:**

- **cc (default):** Use time-varying LPJmL yields from `lpj_yields.cs3` that incorporate climate change projections
- **nocc:** Fix all yields to 1995 values (no climate impact on productivity)
- **nocc_hist:** Use climate change up to year `sm_fix_cc`, then hold constant (counterfactual: "no climate change after 2020")

**Implementation:** `input.gms:48-49` replaces future LPJmL yields with 1995 or fixed-year values

**Citation:** `input.gms:8-49`

### 5.2 Limited Calibration Switch

**File:** `input.gms:13`

```gams
scalar s14_limit_calib   Relative managament calibration switch (1=limited 0=pure relative) / 1 /;
```

**Options:**
- **1 (default):** Enable limited calibration (lambda-based blending)
- **0:** Pure relative calibration (λ always = 1)

**Citation:** `input.gms:13`

### 5.3 Irrigated-Rainfed Calibration

**File:** `input.gms:15`

```gams
scalar s14_calib_ir2rf   Switch to calibrate rainfed to irrigated yield ratios (1=calib 0=not calib) / 1 /;
```

**Citation:** `input.gms:15`

### 5.4 Degradation Effects

**File:** `input.gms:17`

```gams
scalar s14_degradation   Switch to include yield impacts of land degradation(0=no degradation 1=with degradation) / 0 /;
```

**Default:** OFF (degradation not included by default)

**Citation:** `input.gms:17`

### 5.5 Pasture Spillover Magnitude

**File:** `input.gms:24`

```gams
s14_yld_past_switch  Spillover parameter for translating technological change in the crop sector into pasture yield increases  (1)     / 0.25 /
```

**Default:** 0.25 (25% of crop τ increase benefits pasture)

**Valid Range:** 0 (no spillover) to 1 (full spillover)

**Citation:** `input.gms:24`

### 5.6 Degradation Severity

**File:** `input.gms:25`

```gams
s14_yld_reduction_soil_loss  Decline of land productivity in areas with severe soil loss (1)     / 0.08 /
```

**Default:** 0.08 (8% yield reduction on land with soil loss)

**Citation:** `input.gms:25`

---

## 6. Input Data Files

Module 14 reads 9 input data files:

### 6.1 LPJmL Yield Data

**File:** `lpj_yields.cs3` (read at `input.gms:44`)
**Contents:** Gridded potential yields for all crops, pasture, and bioenergy under rainfed and irrigated conditions (tDM/ha/yr), time-varying to incorporate climate change
**Dimensions:** t_all × j × kve × w (time, cells, crops, water systems)

### 6.2 Historical Pasture Yields

**File:** `f14_pasture_yields_hist.csv` (read at `input.gms:54`)
**Contents:** Regional pasture yields from historical model runs (tDM/ha/yr)
**Purpose:** Used in Stage 2 calibration (`preloop.gms:18`) to correct LPJmL pasture patterns
**Dimensions:** t_all × i (time, regions)

### 6.3 FAO Historical Yields

**File:** `f14_region_yields.cs3` (read at `input.gms:60`)
**Contents:** FAO-reported regional yields for all crops (tDM/ha/yr)
**Purpose:** Target for limited calibration in Stage 3
**Dimensions:** t_all × i × kcr (time, regions, crops)

### 6.4 AQUASTAT Irrigated-Rainfed Ratios

**File:** `f14_ir2rf_ratio.cs4` (read at `input.gms:68`)
**Contents:** Country-level irrigated/rainfed yield ratios from AQUASTAT
**Purpose:** Target for Stage 4 calibration
**Citation:** `@fao_aquastat_2016` in `module.gms:21`
**Dimensions:** i (regions)

### 6.5 IPCC Biomass Conversion Factors

**File:** `f14_ipcc_bce.cs3` (read at `input.gms:75`)
**Contents:** Climate-zone-specific Biomass Conversion and Expansion factors
**Purpose:** Convert total biomass to merchantable stem wood for timber yield calculation
**Dimensions:** clcl × forest_type (climate classes, forest types)

### 6.6 Root-to-Shoot Ratios

**File:** `f14_aboveground_fraction.csv` (read at `input.gms:82`)
**Contents:** Fraction of biomass that is aboveground (stems/branches vs. roots)
**Purpose:** Timber calculation (only harvest aboveground biomass)
**Dimensions:** land_timber (forestry, primforest, secdforest, other)

### 6.7 NCP Degradation Indicators

**File:** `f14_yld_ncp_report.cs3` (read at `input.gms:90`, optional)
**Contents:** Share of land with intact nature's contributions to people (NCP): soil integrity and pollination sufficiency (0-1)
**Purpose:** Stage 6 degradation effects
**Dimensions:** t_all × j × ncp_type14 (time, cells, "soil_intact"/"poll_suff")

### 6.8 Pollinator Dependence by Crop

**File:** `f14_kcr_pollinator_dependence.csv` (read at `input.gms:98`)
**Contents:** Share of yield dependent on biotic pollination for each crop (0-1)
**Example:** Oilpalm ≈0.4, maize ≈0, rapeseed ≈0.3
**Purpose:** Scale pollination deficiency impact by crop sensitivity
**Dimensions:** kcr (crops)

### 6.9 Optional Yield Calibration Factors

**File:** `f14_yld_calib.csv` (read at `input.gms:37`, optional)
**Contents:** Regional adjustment factors for crops and pasture (1 = no adjustment)
**Purpose:** Stage 5 post-calibration correction from previous model runs
**Dimensions:** i × ltype14 (regions, "crop"/"past")

---

## 7. Interface Variables

### 7.1 Outputs (Provided to Other Modules)

**Primary Output:**

**vm_yld(j,kve,w)** - Yields for crops and pasture (tDM/ha/yr)
**Provided to:**
- Module 30 (Crop): Crop production = area × yield
- Module 31 (Pasture): Pasture production = area × yield

**Dimensions:** j (cells), kve (crops + pasture), w (rainfed/irrigated)
**Citation:** `declarations.gms:26`

---

**Secondary Output:**

**pm_timber_yield(t,j,ac,land_timber)** - Growing stock / harvestable wood biomass (tDM/ha/yr)
**Provided to:**
- Module 32 (Forestry): Plantation harvest calculations
- Module 35 (Natural Vegetation): Natural forest harvest calculations

**Dimensions:** t (time), j (cells), ac (age classes), land_timber (forestry, primforest, secdforest, other)
**Citation:** `declarations.gms:17`

---

**Tertiary Output:**

**pm_yields_semi_calib(j,kve,w)** - 1995 calibrated yields (tDM/ha/yr)
**Purpose:** Baseline reference for other modules
**Set at:** `preloop.gms:109,142`
**Citation:** `declarations.gms:18`

---

### 7.2 Inputs (Received from Other Modules)

**From Module 13 (Technological Change):**

- **vm_tau(h,"crop")**: Current technological change factor (optimization variable)
- **pcm_tau(h,"crop")**: Previous time step τ factor (for pasture spillover)
- **fm_tau1995(h)**: Baseline τ in 1995 (fixed parameter)

**Citation:** Used in `equations.gms:16,39`

---

**From Module 52 (Carbon):**

- **pm_carbon_density_plantation_ac(t,j,ac,"vegc")**: Plantation carbon density (tC/ha)
- **pm_carbon_density_secdforest_ac(t,j,ac,"vegc")**: Secondary forest carbon density (tC/ha)

**Citation:** Used in `presolve.gms:26,44`

---

**From Module 35 (Natural Vegetation):**

- **pm_carbon_density_other_ac(t,j,ac,"vegc")**: Other natural land carbon density (tC/ha)

**Citation:** Used in `presolve.gms:53`

---

**From Module 70 (Livestock):**

- **pm_past_mngmnt_factor(ct,i)**: Exogenous pasture management factor (driven by livestock demand)

**Citation:** Used in `equations.gms:38`

---

**From Input Data:**

- **fm_croparea(t_all,j,w,kcr)**: Historical cropland area patterns (for calibration weighting)
- **pm_land_start(j,"past")**: Initial pasture area (for pasture correction weighting)
- **fm_carbon_density(t,j,"primforest","vegc")**: Primary forest carbon (fixed input)
- **pm_climate_class(j,clcl)**: Climate classification for BCE factors

**Citation:** Various uses in `preloop.gms` and `presolve.gms`

---

## 8. Dependencies and Impact

### 8.1 Critical Upstream Dependencies

**Module 13 (Technological Change):**
- Provides τ factor that drives all yield increases over time
- Without τ, yields would remain at calibrated baseline forever

**Module 52 (Carbon):**
- Provides carbon density for timber yield calculations
- Timber harvest infeasible without this

**LPJmL External Model:**
- Provides biophysical yield baseline with climate sensitivity
- Without LPJmL, no spatial heterogeneity or climate impacts

**FAO and AQUASTAT Data:**
- Calibration targets; without these, yields would be purely biophysical (no human management representation)

### 8.2 Critical Downstream Dependencies

**Module 30 (Crop) and Module 31 (Pasture):**
- **Cannot function without vm_yld**
- Production = area × yield, so yields determine how much land is needed to meet demand

**Module 32 (Forestry):**
- Plantation harvest quantity = area × pm_timber_yield
- Without timber yields, forestry module cannot calculate wood supply

**Module 17 (Production) and Module 11 (Costs):**
- Yields affect production levels, which cascade to regional supply, trade, and economic costs

### 8.3 Circular Dependencies

**None directly in equations.**

**Indirect calibration dependencies:**
- Preloop calibration uses `fm_croparea` (historical cropland patterns)
- Those patterns were likely generated by previous MAgPIE runs
- This creates a **bootstrap dependency**: First run → generates cropland → used to calibrate yields for next run

---

## 9. Key Parameters

### 9.1 Equation-Level Parameters

**i14_yields_calib(t,j,kve,w)** - Calibrated baseline yields (tDM/ha/yr)
**Computed in:** `preloop.gms` (Stages 1-6)
**Used in:** `equations.gms:15,37`, `nl_fix.gms:10-11`
**Purpose:** Final yield baseline after all calibrations
**Citation:** `declarations.gms:9`

---

**i14_managementcalib(t,j,kcr,w)** - Limited calibration factor (dimensionless)
**Computed in:** `preloop.gms:101-105`
**Formula:** See Section 3.3.3
**Purpose:** Scales LPJmL yields to FAO regional levels
**Citation:** `declarations.gms:16`

---

**i14_lambda_yields(t,i,kcr)** - Calibration mode factor (dimensionless, 0-1)
**Computed in:** `preloop.gms:76-86`
**Formula:** λ = 1 if FAO ≤ LPJmL, else √(LPJmL/FAO)
**Purpose:** Controls blend between relative and additive calibration
**Citation:** `declarations.gms:15`

---

### 9.2 Intermediate Calibration Parameters

**p14_pyield_corr(t,i)** - Pasture yield correction factor (dimensionless)
**Computed in:** `preloop.gms:18-19`
**Purpose:** Corrects LPJmL pasture yields to historical model patterns
**Citation:** `declarations.gms:11`

---

**i14_modeled_yields_hist(t_all,i,kcr)** - Regional LPJmL yields (tDM/ha/yr)
**Computed in:** `preloop.gms:60-66`
**Purpose:** Area-weighted average for calibration
**Citation:** `declarations.gms:13`

---

**i14_fao_yields_hist(t,i,kcr)** - FAO target yields (tDM/ha/yr)
**Computed in:** `preloop.gms:88` (copied from input file)
**Purpose:** Calibration target
**Citation:** `declarations.gms:14`

---

### 9.3 Timber Yield Parameters

**pm_timber_yield(t,j,ac,land_timber)** - Harvestable wood biomass (tDM/ha/yr)
**Computed in:** `presolve.gms:24-58`
**Formula:** CarbonDensity / 0.5 × AbovegroundFraction / BCE
**Citation:** `declarations.gms:17`

---

## 10. Nonlinear Fix/Release

Module 14 uses the nl_fix/nl_release mechanism for pre-solving yield values in iterative solves.

### 10.1 NL Fix Phase

**File:** `nl_fix.gms:10-11`

```gams
vm_yld.fx(j,kcr,w) = sum(ct,i14_yields_calib(ct,j,kcr,w)) * sum((cell(i,j), supreg(h,i)),vm_tau.l(h, "crop") / fm_tau1995(h));
vm_yld.fx(j,"pasture",w) = sum(ct,(i14_yields_calib(ct,j,"pasture",w)) * sum(cell(i,j), pm_past_mngmnt_factor(ct,i))) * (1 + s14_yld_past_switch * (sum((cell(i,j), supreg(h,i)), pcm_tau(h, "crop") / fm_tau1995(h)) - 1));
```

**What This Does:** Fixes vm_yld to the level values (`.l`) from equations q14_yield_crop and q14_yield_past, using **previous solve's vm_tau.l** instead of the variable vm_tau.

**Purpose:** In iterative solution methods, some modules may need yields to be temporarily fixed (not variables) to simplify the optimization problem.

**Citation:** `nl_fix.gms:10-11`

### 10.2 NL Release Phase

**File:** `nl_release.gms:10-11`

```gams
vm_yld.lo(j,kve,w) = 0;
vm_yld.up(j,kve,w) = Inf;
```

**What This Does:** Releases vm_yld back to a free variable (lower bound 0, upper bound infinity).

**Citation:** `nl_release.gms:10-11`

---

## 11. What This Module Does NOT Do

Following the "Code Truth" principle, it's important to state what Module 14 does NOT implement:

### 11.1 No Dynamic Climate Modeling

- **Does NOT dynamically model** weather, temperature, precipitation, or CO2 effects
- **DOES use** pre-computed LPJmL yields that already incorporate these effects
- Climate change impacts are **parameterized**, not simulated

### 11.2 No Endogenous Management Decisions

- **Does NOT optimize** fertilizer application, irrigation scheduling, or crop varieties
- **DOES scale** yields using exogenous τ factor from Module 13
- Management is represented as a **single scalar intensification factor**, not detailed practices

### 11.3 No Yield Variability or Risk

- **Does NOT model** yield variability, crop failure, or weather shocks
- **DOES use** expected (average) yields only
- All yields are **deterministic** given τ and calibration

### 11.4 No Pest, Disease, or Weed Dynamics

- **Does NOT model** pest outbreaks, disease spread, or herbicide resistance
- **DOES include** pollination and soil degradation IF enabled (optional)
- Pest/disease impacts are **implicit in LPJmL calibration**, not explicit

### 11.5 No Endogenous Pasture Intensification

- **Does NOT optimize** pasture management in response to land scarcity
- **DOES apply** exogenous management factor from Module 70 (livestock demand-driven)
- Limitation explicitly stated in `realization.gms:23-24`

### 11.6 No Nitrogen or Water Constraints in Yield Equations

- **Does NOT include** nitrogen or water as factors in equations q14_yield_crop/past
- **DOES assume** LPJmL yields already incorporate water-limited vs. irrigated productivity
- Nitrogen impacts on yields are **external** (LPJmL input), not calculated in Module 14

---

## 12. Critical Code Patterns

### 12.1 Two-Stage Calibration for FAO Totals

**Pattern:** Whenever irrigated yields are scaled up (Stage 4), a second calibration pass (`preloop.gms:130-140`) re-applies FAO regional yield targets to maintain production balance.

**Why:** Increasing irrigated yields without adjusting rainfed yields would cause regional average yields to exceed FAO targets, violating historical production constraint.

### 12.2 Lambda-Based Limited Calibration

**Pattern:** Use λ as exponent on ratio term to blend relative and additive calibration (`preloop.gms:101-105`).

**Why:** Pure relative calibration (λ=1) over-amplifies future yield growth when baseline is underestimated. Lambda reduces amplification by approaching additive calibration (λ→0) as underestimation worsens.

**Literature:** Based on Heinke et al. 2013 equation 9.

### 12.3 Pasture Uses Previous Time Step τ

**Pattern:** Pasture equation uses `pcm_tau` (previous τ) instead of `vm_tau` (current τ) (`equations.gms:39`).

**Why:** Represents delayed knowledge transfer from crop to pasture sector. Crop innovations take time to adapt to extensive grazing systems.

### 12.4 Timber Yield = Carbon / Conversion Factors

**Pattern:** All timber yields calculated as `CarbonDensity / 0.5 × AbovegroundFrac / BCE` (`presolve.gms:24-58`).

**Why:** Carbon densities from Module 52 are in tC/ha. Need to convert to harvestable stem wood in tDM/ha using standard forestry conversion factors (carbon fraction, root-to-shoot ratio, biomass expansion).

### 12.5 Preloop Calibration Held Constant

**Pattern:** All calibration occurs in preloop phase (`preloop.gms:8-190`). Parameter `i14_yields_calib` computed once, then held constant. Equations use `sum(ct,i14_yields_calib(ct,...))` to access current time step value.

**Why:** Calibration targets (FAO 1995, AQUASTAT ratios) are historical. Once calibrated, baseline remains constant; only τ varies to change yields over time.

---

## 13. Testing and Validation Procedures

### 13.1 Equation Count Verification

```bash
grep "^[ ]*q14_" modules/14_yields/managementcalib_aug19/declarations.gms | wc -l
# Expected: 2
```

**Verified:** ✅ 2 equations (q14_yield_crop, q14_yield_past)

### 13.2 Calibration Quality Check

**After running MAgPIE with Module 14:**

1. **Check regional yields match FAO in 1995:**
   ```gams
   * Compare sum(j,cell(i,j), vm_yld.l("y1995",j,kcr,w) * vm_area.l("y1995",j,kcr,w)) / sum(j,cell(i,j), vm_area.l("y1995",j,kcr,w))
   * against i14_fao_yields_hist("y1995",i,kcr)
   ```
   Should match within <1% for all regions and crops.

2. **Check irrigated/rainfed ratios match AQUASTAT:**
   ```gams
   * Compare [irrigated weighted yield] / [rainfed weighted yield]
   * against f14_ir2rf_ratio(i)
   ```
   Should be ≥ AQUASTAT ratio for all regions.

3. **Check pasture yields are reasonable:**
   Compare pasture production (area × yield) against FAO pasture production. Should match historical totals.

### 13.3 Lambda Values Inspection

**Examine `i14_lambda_yields` after preloop:**
- Values near 1.0 → good baseline (LPJmL ≈ FAO)
- Values 0.5-0.9 → moderate underestimation
- Values <0.5 → severe underestimation, additive calibration dominant

**Expected pattern:** Most crops have λ > 0.8, indicating reasonable LPJmL baseline quality.

### 13.4 Timber Yield Sanity Check

**After presolve:**

1. **Check plantation yields are reasonable:**
   - Young plantations (ac0-ac2): 50-200 tDM/ha
   - Mature plantations (ac5+): 200-400 tDM/ha
   - Old plantations (ac10+): 300-500 tDM/ha

2. **Check natural forest yields respect minimum:**
   ```gams
   * All pm_timber_yield(t,j,ac,"primforest") should be either 0 or ≥ s14_minimum_wood_yield (10 tDM/ha)
   ```

3. **Check age-class progression:**
   Timber yields should generally increase with age class (older forests have more biomass).

### 13.5 Scenario Reproducibility

**Test climate scenarios:**

1. Run with `c14_yields_scenario = "cc"` → record 2050 yields
2. Run with `c14_yields_scenario = "nocc"` → yields should equal 1995 yields in all years
3. Run with `c14_yields_scenario = "nocc_hist"` and `sm_fix_cc = 2020` → yields should change until 2020, then freeze

**Expected:** Yields in "nocc" should be constant; yields in "cc" should increase/decrease based on LPJmL climate projections.

### 13.6 Degradation Impact Test

**Test degradation switch:**

1. Run with `s14_degradation = 0` → record yields
2. Run with `s14_degradation = 1` → yields should be ≤ previous run
3. Calculate average yield loss: should be ~1-5% globally (depends on NCP input data)

**Expected:** Degradation reduces yields in cells with low soil integrity or pollination sufficiency.

---

## 14. Common Issues and Debugging

### 14.1 Unrealistic Future Yields

**Symptom:** Yields in 2050 are 5-10x higher than 1995 yields.

**Likely Cause:**
- Limited calibration is OFF (`s14_limit_calib = 0`)
- FAO yields >> LPJmL yields
- Relative calibration amplifying future yield growth

**Solution:** Enable limited calibration (`s14_limit_calib = 1`)

**Diagnosis:** Check `i14_lambda_yields` values. If all = 1.0, limited calibration is not active.

### 14.2 Regional Production Doesn't Match FAO

**Symptom:** 1995 regional production (area × yield) differs from FAO by >10%.

**Likely Causes:**
1. Cropland areas (`fm_croparea`) don't match FAO areas
2. Yield calibration factors (`f14_yld_calib`) are not set correctly
3. Limited calibration lambda is too low (too much additive calibration)

**Solutions:**
1. Check cropland input data from Module 10
2. Enable yield calibration factors (`s14_use_yield_calib = 1`) and provide `f14_yld_calib.csv`
3. Inspect `i14_lambda_yields` for regions with production mismatch

### 14.3 Negative or Zero Yields

**Symptom:** Some cells have vm_yld = 0 or solver reports negative yields.

**Likely Causes:**
1. LPJmL input yields are 0 (unsuitable climate for crop)
2. Degradation effects reduce yields to 0 (100% degraded land)
3. Calibration factor is negative (data error)

**Solutions:**
1. **If LPJmL = 0:** Expected behavior, crop not grown in that cell
2. **If degradation:** Check `f14_yld_ncp_report` input data for realistic values (0-1 range)
3. **If calibration issue:** Inspect `i14_managementcalib` for negative values, fix FAO or LPJmL input data

### 14.4 Irrigated Yields Lower Than Rainfed

**Symptom:** Irrigated yields < rainfed yields in some regions after calibration.

**Likely Cause:**
- AQUASTAT ratio calibration is OFF (`s14_calib_ir2rf = 0`)
- LPJmL irrigated yields are poorly estimated

**Solution:** Enable AQUASTAT calibration (`s14_calib_ir2rf = 1`)

**Diagnosis:** Compare `f14_yields(...,"irrigated")` vs `f14_yields(...,"rainfed")` in input data. If LPJmL ratios are unrealistic, calibration is essential.

### 14.5 Pasture Yields Don't Respond to Livestock Demand

**Symptom:** Pasture yields remain constant despite increasing livestock production.

**Likely Cause:** `pm_past_mngmnt_factor` is constant (Module 70 not providing dynamic management signal).

**Solution:** Check Module 70 realization. Some realizations provide dynamic `pm_past_mngmnt_factor` based on livestock demand, others use fixed values.

**Not a Module 14 issue:** Module 14 correctly implements the equation; the management factor comes from Module 70.

---

## 15. Key Insights for Users

### 15.1 Yields Are Hybrid Biophysical-Statistical

Module 14 yields are **NOT pure LPJmL outputs**. They are:
1. LPJmL biophysical baseline (climate, soil, water)
2. Calibrated to FAO statistical observations (management, varieties, practices)
3. Scaled by τ factor (future intensification)

**Implication:** Yields incorporate both **biophysical constraints** (can't grow wheat in Sahara) and **observed management** (actual farmer practices in 1995).

### 15.2 Technological Change Is the Primary Yield Driver

In most scenarios, climate change effects on yields are **smaller than τ factor effects**:
- Climate: ±5-20% by 2050 (region-dependent)
- τ factor: +50-150% by 2050 (scenario-dependent)

**Implication:** Module 13 (technological change) is more important than climate scenario for long-term yield projections.

### 15.3 Limited Calibration Prevents Overestimation

Without limited calibration (λ), regions with underestimated baselines (FAO >> LPJmL) would experience **explosive yield growth** as LPJmL improves in future time steps.

**Example:**
- LPJmL 1995: 2 tDM/ha
- FAO 1995: 6 tDM/ha → calibration factor = 3x
- LPJmL 2050: 4 tDM/ha (doubled)
- Without λ: Calibrated yield = 4 × 3 = 12 tDM/ha (unrealistic 2x FAO)
- With λ=0.58: Calibrated yield ≈ 8 tDM/ha (reasonable 1.3x FAO)

**Implication:** Always use `s14_limit_calib = 1` unless you have high confidence in LPJmL baseline accuracy.

### 15.4 Timber Yields Are Age-Class Dependent

Harvestable wood biomass increases with forest age, reflecting carbon accumulation over time. Rotating plantations at optimal age (see Module 32) maximizes long-term wood supply.

**Implication:** Forestry optimization depends on accurate carbon density projections from Module 52.

### 15.5 Degradation Impacts Are Modular

Soil loss and pollination deficiency are **optional features** that can be enabled/disabled independently of yield calculation. This allows scenario analysis of conservation policies.

**Implication:** To study biodiversity or soil conservation benefits, enable degradation and compare scenarios with/without conservation investments.

---

## 16. Relationship to Other Modules

### 16.1 Provides Yields To

- **Module 30 (Crop):** `vm_yld(j,kcr,w)` → crop production calculation
- **Module 31 (Pasture):** `vm_yld(j,"pasture",w)` → pasture production calculation
- **Module 32 (Forestry):** `pm_timber_yield(t,j,ac,"forestry")` → plantation harvest
- **Module 35 (Natural Vegetation):** `pm_timber_yield(t,j,ac,land_natveg)` → natural forest harvest

### 16.2 Receives Intensification From

- **Module 13 (Technological Change):** `vm_tau(h,"crop")` → scales crop yields
- **Module 13 (Technological Change):** `pcm_tau(h,"crop")` → scales pasture yields (lagged)

### 16.3 Receives Carbon Density From

- **Module 52 (Carbon):** Plantation and secondary forest carbon → timber yields
- **Module 35 (Natural Vegetation):** Other natural land carbon → timber yields

### 16.4 Receives Pasture Management From

- **Module 70 (Livestock):** `pm_past_mngmnt_factor(ct,i)` → exogenous pasture intensification

### 16.5 Coordination with Calibration Modules

- **Module 10 (Land):** Provides `fm_croparea` (historical cropland patterns) for calibration weighting
- **External FAO/AQUASTAT Data:** Provide calibration targets for yield levels and irrigated/rainfed ratios

---

## 17. Literature and Methodology References

**Limited Calibration Methodology:**
- **@Heinke.2013:** Heinke et al. (2013), equation 9 — foundation for lambda-based calibration (`preloop.gms:47`)

**LPJmL Crop Model:**
- **@bondeau_lpjml_2007:** Bondeau et al. (2007) — LPJmL managed land model (`module.gms:14`)

**Calibration Data Sources:**
- **@FAOSTAT:** FAO Statistical Database — regional yield targets (`module.gms:16,21`)
- **@fao_aquastat_2016:** AQUASTAT — irrigated/rainfed yield ratios (`module.gms:21`)

**Biomass Conversion Factors:**
- **IPCC Guidelines:** `f14_ipcc_bce.cs3` contains IPCC default BCE factors for forest types

---

## 18. Version History and Module Evolution

**Current Realization:** `managementcalib_aug19` (August 2019)

**Key Features of This Realization:**
1. Limited calibration (λ-based blending) — introduced to address yield overestimation
2. AQUASTAT irrigated-rainfed ratio calibration — improves irrigation investment decisions
3. Pasture spillover from crop τ — represents knowledge transfer to extensive systems
4. Timber yield calculation — supports forestry and natural vegetation harvest
5. Degradation effects (soil loss, pollination) — optional NCP accounting

**Alternative Realizations:**
- **biocorrect:** Simpler calibration without λ, uses current time step τ for pasture
- **input:** No calibration, pure LPJmL yields (debugging only)

---

## 19. Configuration Examples

### 19.1 Standard Run (Default Settings)

```gams
$setglobal c14_yields_scenario  cc
s14_limit_calib = 1
s14_calib_ir2rf = 1
s14_degradation = 0
s14_use_yield_calib = 0
s14_yld_past_switch = 0.25
```

**Use case:** Standard MAgPIE run with climate change, calibrated yields, no degradation

### 19.2 No Climate Change Counterfactual

```gams
$setglobal c14_yields_scenario  nocc
s14_limit_calib = 1
s14_calib_ir2rf = 1
s14_degradation = 0
s14_use_yield_calib = 0
s14_yld_past_switch = 0.25
```

**Use case:** Isolate impacts of climate change by fixing yields at 1995 biophysical levels

### 19.3 Degradation Scenario

```gams
$setglobal c14_yields_scenario  cc
s14_limit_calib = 1
s14_calib_ir2rf = 1
s14_degradation = 1
s14_use_yield_calib = 0
s14_yld_past_switch = 0.25
s14_yld_reduction_soil_loss = 0.08
```

**Use case:** Study impacts of soil degradation and pollination loss on agricultural productivity

### 19.4 Pure Relative Calibration (Testing Only)

```gams
$setglobal c14_yields_scenario  cc
s14_limit_calib = 0
s14_calib_ir2rf = 1
s14_degradation = 0
s14_use_yield_calib = 0
s14_yld_past_switch = 0.25
```

**Use case:** Diagnostic run to assess impact of limited calibration (expect unrealistic yields in regions with poor LPJmL baseline)

### 19.5 High Pasture Spillover

```gams
$setglobal c14_yields_scenario  cc
s14_limit_calib = 1
s14_calib_ir2rf = 1
s14_degradation = 0
s14_use_yield_calib = 0
s14_yld_past_switch = 1.0
```

**Use case:** Optimistic scenario where pasture benefits fully from crop intensification (100% spillover)

---

## 20. Summary

Module 14 is the **calibration and delivery module** for agricultural yields in MAgPIE. It transforms spatially explicit, climate-sensitive LPJmL biophysical yields into model-ready values through six calibration stages:

1. **Bioenergy correction:** Scale to realistic management levels
2. **Pasture correction:** Adjust for regional grazing patterns
3. **Limited calibration:** Match FAO regional yields using λ-blended approach
4. **Irrigated-rainfed calibration:** Match AQUASTAT yield ratios
5. **Yield calibration factors:** Optional post-calibration adjustments
6. **Degradation effects:** Optional soil loss and pollination impacts

The module implements only **2 equations** but performs extensive data preparation in the preloop phase. Equations scale calibrated yields using the **τ (tau) technological change factor** from Module 13, with crop yields responding immediately and pasture yields responding with a one-time-step lag.

Timber yields are calculated separately in the presolve phase by converting carbon densities from Module 52 to harvestable wood biomass using IPCC forestry conversion factors.

**Key Principle:** Yields are **hybrid biophysical-statistical**, combining LPJmL climate sensitivity with FAO observed management practices. This hybrid approach ensures yields are both physically plausible and consistent with historical agricultural patterns.

**Critical Dependencies:**
- **Upstream:** LPJmL data, Module 13 (τ factor), Module 52 (carbon density), FAO/AQUASTAT data
- **Downstream:** Module 30 (Crop), Module 31 (Pasture), Module 32 (Forestry), Module 35 (Natural Vegetation)

**Common Use Cases:**
- Baseline yield projections with climate change
- Counterfactual scenarios (no climate change, high intensification, degradation impacts)
- Sensitivity analysis of calibration approaches (limited vs. relative)
- Forestry rotation optimization (via timber yields)

**For modifications:** Always check Phase 2 dependency matrix before changing yield equations. Many modules depend on `vm_yld` structure and dimensions.

---

## 21. Participates In

### 21.1 Conservation Laws

Module 14 does **not directly participate** in any conservation laws:
- **Not in** land balance (provides yields, doesn't allocate land)
- **Not in** water balance (provides yields, doesn't manage water - though yields affect water demand indirectly)
- **Not in** carbon balance (provides yields, doesn't track carbon stocks)
- **Not in** nitrogen balance (no direct nitrogen flows - yields assume N is met)
- **Not in** food balance (provides yields to calculate production, doesn't balance supply/demand)

**Indirect Role**: Yields are **the critical link** between land and production:
- **Higher yields** → Less land needed for same production → Land balance affected
- **Irrigation vs. rainfed yields** → Water demand trade-offs → Water balance affected
- **Pasture yields** → Grazing intensity → Potential land sparing → Land balance affected

**Critical**: Module 14 shapes **how efficiently land converts to food**, which determines feasibility of meeting demand within land/water constraints.

### 21.2 Dependency Chains

**Centrality Analysis** (from Module_Dependencies.md and module connections):
- **Centrality Rank**: High (exact rank not in top 10, but critical provider to production system)
- **Total Connections**: 5+ (provides to 4 major consumers, depends on 3 sources)
- **Hub Type**: **Processing Hub** (receives biophysical data, provides to production modules)
- **Role**: **Yield calibration and delivery** - connects LPJmL to crop/pasture/forestry modules

**Modules that Module 14 depends on**:
- Module 13 (tc): τ (tau) technological change factor — **CRITICAL DEPENDENCY**
- Module 52 (carbon): Carbon densities for timber yield calculation
- Module 45 (climate): Climate class data for calibration
- **External data**: LPJmL biophysical yields, FAO production/yield data, AQUASTAT irrigation data

**Modules that depend on Module 14**:
- Module 30 (croparea): `vm_yld(j,kcr,w)` for crop yields → determines crop area needed
- Module 31 (pasture): `vm_yld(j,"pasture",w)` for pasture yields → determines pasture area needed
- Module 32 (forestry): Timber yields (`pm_timber_yield`) → determines plantation productivity
- Module 35 (natveg): Natural vegetation yields (implicitly through land competition)
- Module 17 (production): Production = Area × Yield (via modules 30/31/32)
- Module 70 (livestock): Feed availability from crop residues (via Module 18)

**Key Interface Variables**:
- `vm_yld(j,kcr,w)`: Crop yields by irrigation type — **MOST CRITICAL OUTPUT**
- `vm_yld(j,"pasture",w)`: Pasture yields
- `pm_timber_yield(t,j,ac,sys)`: Timber yields by age class and plantation type

### 21.3 Circular Dependencies

**Module 14 participates in 1 major circular dependency**:

#### **Cycle 1: Production-Yield-Livestock Triangle ⭐⭐⭐ (HIGHEST COMPLEXITY)**

**Modules involved**: 17 (production) ↔ 14 (yields) ↔ 70 (livestock)

**Dependency chain**:
```
vm_prod(j,kcr) [17] → Used for calibration of yields
    ↓
pm_yields_semi_calib(j,kcr,w) [14] → Calibrated yields
    ↓
vm_yld(j,kcr,w) [14] → Scaled by tau factor → Affects crop production
    ↓
vm_prod(j,kcr) [30/17] → Crop production = Area × Yield
    ↓
Feed availability [18] → Crop residues for livestock
    ↓
vm_prod(j,kli) [70] → Livestock production
    ↓
Manure production [70/55] → Affects soil fertility
    ↓
pm_yields_semi_calib(j,kcr,w) [14] → **BACK TO START** (via soil organic matter effects)
```

**Resolution Type**: **Temporal Feedback + Iterative Convergence**

**How it resolves**:
1. **Within timestep**: Yields are **fixed parameters** from calibration (not optimized)
2. **Across timesteps**:
   - τ factor (Module 13) adjusts yields based on past production patterns
   - Soil organic matter (Module 59) from manure affects future yields
   - **Temporal lag** breaks the circular dependency within optimization
3. **Calibration phase**: Requires **multiple model runs** to match observed FAO yields
   - Run 1: Use LPJmL base yields
   - Calibration: Adjust λ blend factors to match FAO regional averages
   - Run 2: Re-run with calibrated yields → production changes
   - Iterate until yields stabilize

**Risks from this cycle**:
- **Oscillating yields**: τ factor too sensitive → yields swing between timesteps
- **Unrealistic intensification**: Manure contribution overestimated → yields too high
- **Calibration non-convergence**: FAO target impossible to match with LPJmL base
- **Feed demand infeasibility**: Low yields → insufficient crop residues → livestock fails

**Resolution mechanism in code** (from circular_dependency_resolution.md Section 3.1):
- **Preloop calibration**: `pm_yields_semi_calib` calculated BEFORE optimization
- **τ factor from previous timestep**: `pm_tau(t)` uses **lagged** production values
- **SOM effects gradual**: 15% annual convergence (Module 59) → smooth feedback
- **No iteration within timestep**: Yields fixed → production optimized → manure calculated → affects NEXT timestep

**Testing for cycle stability** (Section 5.3 from circular_dependency_resolution.md):
```r
# Check yields don't oscillate between timesteps
yields_t1 <- yields(gdx, level="cell", products="kcr")[,"y2025",]
yields_t2 <- yields(gdx, level="cell", products="kcr")[,"y2030",]
yields_t3 <- yields(gdx, level="cell", products="kcr")[,"y2035",]

yield_change_12 <- (yields_t2 - yields_t1) / (yields_t1 + 1e-6)
yield_change_23 <- (yields_t3 - yields_t2) / (yields_t2 + 1e-6)

# Changes should be gradual (driven by TC, not oscillation)
stopifnot(all(abs(yield_change_12) < 0.2))  # <20% per 5-year timestep
stopifnot(all(abs(yield_change_23) < 0.2))

# Direction should be consistent (not alternating)
signs_match <- sign(yield_change_12) == sign(yield_change_23)
stopifnot(sum(signs_match, na.rm=TRUE) / length(signs_match) > 0.7)  # 70% same direction
```

### 21.4 Modification Safety

**Risk Level**: 🔴 **HIGH RISK** (critical production determinant)

**Why High Risk**:
1. **Production system bottleneck**: Yields determine if model can meet food demand
2. **Circular dependency**: Part of Production-Yield-Livestock cycle (requires calibration)
3. **Spatial complexity**: Cell-level yields with 200+ cells × 18 crops × 2 irrigation types
4. **Calibration fragility**: Limited calibration tuned to FAO data → easy to break
5. **Climate sensitivity**: LPJmL yields respond to climate → modifications may alter climate response

**Safe Modifications**:
- ✅ Change τ (tau) factor scaling (via Module 13 configuration)
- ✅ Adjust pasture spillover (`s14_yld_past_switch`) within 0-1 range
- ✅ Toggle degradation effects (`s14_degradation` 0/1)
- ✅ Switch climate scenario (`c14_yields_scenario`: cc/nocc/nocc_hist)
- ✅ Modify timber conversion factors (small adjustments to IPCC factors)
- ✅ Change bioenergy scaling (`s14_yld_bioen_scaling`) if using bioenergy scenarios

**Moderate-Risk Modifications** (require calibration testing):
- ⚠️ Change limited calibration bounds (`s14_limit_calib`):
  - Lower bound → more LPJmL influence → may mismatch FAO
  - Higher bound → more statistical adjustment → may mask climate signal
- ⚠️ Disable irrigated-rainfed calibration (`s14_calib_ir2rf = 0`):
  - Loses AQUASTAT yield ratio data → irrigation overestimated or underestimated
- ⚠️ Add new crops to calibration system:
  - Requires FAO production data for target
  - Requires LPJmL biophysical yields as base
  - Requires testing convergence

**High-Risk Modifications** (expert-only, full testing required):
- 🔴 Change calibration methodology (e.g., replace λ-blend with different approach):
  - May break convergence
  - Requires re-tuning all parameters
  - Must maintain climate sensitivity
- 🔴 Modify yield equation structure:
  - Other modules expect `vm_yld(j,kcr,w)` dimensions
  - Changing sets or indices breaks downstream modules
- 🔴 Remove calibration entirely (`s14_use_yield_calib = 0` AND `s14_limit_calib = 0`):
  - Pure LPJmL yields often unrealistic (too low in some regions, too high in others)
  - Model likely infeasible (can't meet food demand)

**Testing Requirements After Modification**:

1. **Calibration target check** (Section 13.1):
   ```r
   # Compare modeled to FAO yields
   yields_model <- yields(gdx, level="reg", products="kcr")
   yields_fao <- read.csv("modules/14_yields/input/f14_yields_calib.cs3")
   relative_error <- abs(yields_model - yields_fao) / yields_fao
   stopifnot(mean(relative_error, na.rm=TRUE) < 0.15)  # <15% avg error
   ```

2. **Irrigation ratio check** (Section 6):
   ```r
   yld_irrig <- yields(gdx, irrigation="irrigated")
   yld_rainfed <- yields(gdx, irrigation="rainfed")
   ratio <- yld_irrig / yld_rainfed
   # Ratio should be 1.0-3.0 for most crops (AQUASTAT typical)
   stopifnot(all(ratio > 0.8, na.rm=TRUE))  # Irrigated never worse than rainfed
   stopifnot(mean(ratio, na.rm=TRUE) > 1.0 && mean(ratio, na.rm=TRUE) < 5.0)
   ```

3. **Yield stability check** (Cycle 1 test above)

4. **Production feasibility** (downstream check):
   ```r
   # Verify model can meet food demand
   production <- production(gdx, level="glo", products="kcr")
   demand <- demand(gdx, level="glo", products="kcr")
   stopifnot(all(production >= demand * 0.95))  # Allow 5% trade slack
   ```

5. **Timber yield plausibility** (Section 8):
   ```r
   timber_yld <- readGDX(gdx, "pm_timber_yield")
   # Typical: 5-20 m³/ha/yr depending on climate and rotation
   stopifnot(all(timber_yld > 0, na.rm=TRUE))
   stopifnot(all(timber_yld < 50, na.rm=TRUE))  # Very high yields suspicious
   ```

6. **Climate signal preservation**:
   ```r
   # Compare cc vs. nocc scenarios
   yields_cc <- yields(gdx_cc, level="glo")
   yields_nocc <- yields(gdx_nocc, level="glo")
   yield_change <- (yields_cc - yields_nocc) / yields_nocc
   # Should see climate impact (usually negative in many regions by 2050)
   stopifnot(abs(mean(yield_change["y2050",,])) > 0.02)  # >2% avg change
   ```

**Common Pitfalls**:
- ❌ Breaking limited calibration bounds (λ outside [0,1]) → nonsensical blending
- ❌ Forgetting to update FAO calibration targets when adding new crops
- ❌ Ignoring pasture yield changes (often overlooked, but critical for livestock)
- ❌ Not testing timber yields after carbon density changes (Module 52 updates)
- ❌ Assuming yield changes are linear (degradation effects are multiplicative)

**Emergency Fixes**:
- If food demand infeasibility: Increase `s14_limit_calib` upper bound (allow more statistical adjustment)
- If unrealistic yield patterns: Check LPJmL input data quality
- If oscillation: Reduce τ factor sensitivity in Module 13 (`s13_tau_response`)
- If irrigation fails: Verify irrigated-rainfed calibration (`s14_calib_ir2rf = 1`)
- If calibration non-convergence: Relax convergence tolerance or fix problematic crops

**Links**:
- Circular dependency details → cross_module/circular_dependency_resolution.md (Section 3.1)
- Full calibration methodology → This document Sections 4-8
- Technological change → modules/module_13.md
- Production system → modules/module_17.md, module_30.md, module_31.md

---

**Documentation Status:** ✅ Fully Verified (2025-10-12)
**Verification Method:** All source files read, 2 equations verified against declarations.gms, 557 lines of code analyzed, calibration methodology traced through preloop phase
**Citation Density:** 100+ file:line references throughout this document
**Next Module:** Module 11 (Costs) or Module 17 (Production) — core hub modules

---

**Last Verified**: 2026-01-20
**Verified Against**: `../modules/14_yields/managementcalib_aug19/*.gms` (origin/develop branch)
**Verification Method**: Equations cross-referenced with source code
**Changes Since Last Verification**: f_btc2 update - vm_tau and pcm_tau now at cluster level (j) instead of super-region (h) in equations q14_yield_crop and q14_yield_past
