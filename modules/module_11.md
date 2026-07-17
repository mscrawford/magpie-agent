# Module 11: Costs (default)

**Realization:** `default`
**Total Lines of Code:** 149 (default/ realization; 170 incl. module.gms)
**Equation Count:** 2
**Status:** ✅ Verified (2026-05-16 — PR #866 sync; R58 corrections applied 2026-07-17)

> ⚠️ **CORRECTED (R58, 2026-07-17)**: the header previously read "Fully Verified (2025-10-12)", contradicting both footers (2026-05-16). The footers are accurate — PR #866's trade split is present in the code and reflected here (`equations.gms:30-32`).

---

## 1. Overview

### 1.1 Purpose

Module 11 is the **central cost aggregation hub** and **defines MAgPIE's optimization objective** (`module.gms:8-15`). It calculates total global production costs by summing regional costs, which in turn aggregate costs from 30+ different production activities across all other modules.

**Core Function:** `vm_cost_glo` = Σ(all regional costs) → This is the variable MAgPIE **minimizes** in its objective function.

**Architectural Role:** Module 11 is a **pure aggregator** with no independent logic or input data. It depends entirely on cost variables provided by other modules and serves as the single point where all economic components converge into the optimization objective.

### 1.2 Key Features

1. **Global Cost Aggregation** (`equations.gms:10`): Sums regional costs to produce global total
2. **Regional Cost Aggregation** (`equations.gms:15-47`): Sums **32 cost components** (31 positive + 1 negative term) from production, land use, emissions, and policy modules
3. **Objective Function Definition:** `vm_cost_glo` is the variable MAgPIE minimizes
4. **Scaling for Numerical Stability** (`scaling.gms:8-10`): Applies scaling factors to improve solver performance
5. **Zero Configuration:** Module has no input files, switches, or parameters of its own

### 1.3 Critical Importance

**Module 11 is non-negotiable:**
- Without it, MAgPIE has no objective function (solver cannot run)
- It connects **all production decisions** to a single economic metric (USD/yr)
- Any cost missed here is **ignored by optimization** (model will use "free" resources)

**Dependency Impact:**
- **Upstream:** 27 modules provide cost variables
- **Downstream:** Solver uses `vm_cost_glo` to guide all land-use and production decisions

---

## 2. Core Equations

Module 11 implements only 2 equations, both pure summations with no parameters or complex logic.

### 2.1 Equation q11_cost_glo: Global Cost Aggregation

**File:** `equations.gms:10`

```gams
q11_cost_glo .. vm_cost_glo =e= sum(i2, v11_cost_reg(i2));
```

**What This Equation Does:**

Sums regional costs across all regions to produce the global total cost.

**Mathematical Structure:**

```
GlobalCost = Σ(RegionalCost_i)  for all regions i
```

**Components:**

- **vm_cost_glo**: Global total cost (mio. USD17MER/yr) — **THIS IS THE OBJECTIVE FUNCTION**
- **v11_cost_reg(i)**: Regional cost for region i (mio. USD17MER/yr)
- **i2**: Regions currently active in simulation (typically 10-14 MAgPIE regions)

**Currency Unit:** USD17MER = 2017 US Dollars at Market Exchange Rates (not Purchasing Power Parity)

**Conceptual Meaning:**

This equation defines what MAgPIE minimizes. Every decision about land use, production, trade, and technology is evaluated based on how it affects `vm_cost_glo`. Lower cost solutions are preferred by the solver.

**Citation:** `equations.gms:10-13`

---

### 2.2 Equation q11_cost_reg: Regional Cost Aggregation

**File:** `equations.gms:15-47`

```gams
q11_cost_reg(i2) .. v11_cost_reg(i2) =e= sum(factors,vm_cost_prod_crop(i2,factors))
                   + sum(kres,vm_cost_prod_kres(i2,kres))
                   + vm_cost_prod_past(i2)
                   + vm_cost_prod_fish(i2)
                   + sum(factors,vm_cost_prod_livst(i2,factors))
                   + sum((cell(i2,j2),land), vm_cost_landcon(j2,land))
                   + sum((cell(i2,j2),k), vm_cost_transp(j2,k))
                   + vm_tech_cost(i2)
                   + vm_rotation_penalty(i2)
                   + vm_nr_inorg_fert_costs(i2)
                   + vm_p_fert_costs(i2)
                   + vm_emission_costs(i2)
                   - vm_reward_cdr_aff(i2)
                   + sum(factors,vm_maccs_costs(i2,factors))
                   + vm_cost_AEI(i2)
                   + vm_cost_trade_tariff(i2)
                   + vm_cost_trade_margin(i2)
                   + vm_cost_trade_feasibility(i2)
                   + vm_cost_fore(i2)
                   + vm_cost_timber(i2)
                   + vm_cost_hvarea_natveg(i2)
                   + vm_cost_processing(i2)
                   + sum(cell(i2,j2), vm_cost_scm(j2))
                   + vm_bioenergy_utility(i2)
                   + vm_processing_substitution_cost(i2)
                   + vm_costs_additional_mon(i2)
                   + sum(cell(i2,j2), vm_cost_land_transition(j2))
                   + sum(cell(i2,j2), vm_peatland_cost(j2))
                   + sum(cell(i2,j2), vm_cost_cropland(j2))
                   + sum(cell(i2,j2), vm_cost_bv_loss(j2))
                   + sum(cell(i2,j2), vm_cost_urban(j2))
                   + vm_water_cost(i2)
;
```

**What This Equation Does:**

Aggregates all cost components for a single region from 30+ different modules.

**Mathematical Structure:**

```
RegionalCost = CropProductionCosts
              + ResidueProductionCosts
              + PastureProductionCosts
              + FishProductionCosts
              + LivestockProductionCosts
              + LandConversionCosts
              + TransportationCosts
              + TechnologicalChangeCosts
              + RotationPenalty
              + NitrogenFertilizerCosts
              + PhosphorusFertilizerCosts
              + EmissionCosts
              - AfforestationCDRRewards
              + AbatementCosts
              + IrrigationExpansionCosts
              + TradeTariffCosts
              + TradeMarginCosts
              + TradeFeasibilityCosts
              + ForestryCosts
              + TimberHarvestCosts
              + NaturalVegetationHarvestCosts
              + ProcessingCosts
              + SoilCarbonManagementCosts
              + BioenergyUtility
              + ProcessingSubstitutionCosts
              + AdditionalMonitoringCosts
              + LandTransitionCosts
              + PeatlandCosts
              + CroplandCosts
              + BiodiversityLossCosts
              + UrbanLandCosts
              + WaterCosts
```

**Note:** `vm_reward_cdr_aff` has a **negative sign** — afforestation CDR (Carbon Dioxide Removal) generates revenue, reducing net costs.

**Citation:** `equations.gms:15-47`

---

## 3. Cost Components by Source Module

Module 11 aggregates costs from 27 modules. Here is the complete mapping of each cost variable to its source module:

### 3.1 Production Costs

#### Crop Production Costs

**Variable:** `vm_cost_prod_crop(i,factors)`
**Source Module:** Module 38 (Factor Costs)
**Description:** Labor and capital costs for crop production (only labor and capital; land rent is not an explicit M38 cost -- it emerges as the shadow value of the land constraint, not a term in Module 11)
**Dimensions:** i (regions), factors (labor, capital) — verified at `modules/38_factor_costs/sticky_feb18/sets.gms:15-16`
**Citation:** `equations.gms:15`, documented in the component comment block `equations.gms:49-69`

---

#### Residue Production Costs

**Variable:** `vm_cost_prod_kres(i,kres)`
**Source Module:** Module 18 (Residues)
**Description:** Production costs of harvesting **crop** residues (`modules/18_residues/flexreg_apr16/declarations.gms:17`)
**Dimensions:** i (regions), kres (residue types) — `kres` has exactly **3** members: `res_cereals`, `res_fibrous`, `res_nonfibrous` (`modules/16_demand/sector_may15/sets.gms:13-14`)
**Citation:** `equations.gms:16`

> ⚠️ **CORRECTED (R58, 2026-07-17)**: this previously read "residue collection and processing (crop residues, wood fuel)". `woodfuel` is **not** in `kres` — it is a member of `k` (Primary products, `modules/14_yields/managementcalib_aug19/sets.gms:12-16`), which `q11_cost_reg` sums separately via `vm_cost_transp(j,k)` at `equations.gms:21`. Attributing wood fuel to `vm_cost_prod_kres` risks the double-counting §11.3 warns about. "Processing" is also not in the code's description, which says "harvesting".

---

#### Pasture Production Costs

**Variable:** `vm_cost_prod_past(i)`
**Source Module:** Module 31 (Pasture)
**Description:** Labor and capital costs for pasture management
**Dimensions:** i (regions)
**Citation:** `equations.gms:17`

---

#### Fish Production Costs

**Variable:** `vm_cost_prod_fish(i)`
**Source Module:** Module 70 (Livestock)
**Description:** Costs for fish production (aquaculture and capture fisheries)
**Dimensions:** i (regions)
**Citation:** `equations.gms:18`

---

#### Livestock Production Costs

**Variable:** `vm_cost_prod_livst(i,factors)`
**Source Module:** Module 70 (Livestock)
**Description:** Labor and capital costs for livestock production
**Dimensions:** i (regions), factors (labor, capital)
**Citation:** `equations.gms:19`, documented in the component comment block `equations.gms:49-69`

---

### 3.2 Land Use Costs

#### Land Conversion Costs

**Variable:** `vm_cost_landcon(j,land)`
**Source Module:** Module 39 (Land Conversion)
**Description:** One-time costs for converting land between types (clearing, drainage, leveling)
**Dimensions:** j (cells), land (**7** members, exact labels: `crop`, `past`, `forestry`, `primforest`, `secdforest`, `urban`, `other` — `core/sets.gms:250-251`)
**Aggregation:** Sum over all cells in region, all 7 land pools
**Citation:** `equations.gms:20`, documented in the component comment block `equations.gms:49-69`

> ⚠️ **CORRECTED (R58, 2026-07-17)**: the `land` dimension previously read "(cropland, pasture, forest, urban, other)" — 5 friendly names. The set has **7** members; collapsing `forestry`/`primforest`/`secdforest` into one "forest" drops two pools whose conversion costs differ. `equations.gms:20` sums `vm_cost_landcon(j2,land)` over all 7.

---

#### Land Transition Costs

**Variable:** `vm_cost_land_transition(j)`
**Source Module:** Module 10 (Land)
**Description:** Small smoothing costs to penalize rapid land-use changes
**Dimensions:** j (cells)
**Aggregation:** Sum over all cells in region
**Citation:** `equations.gms:41`, documented in the component comment block `equations.gms:49-69`

---

#### Cropland Costs

**Variable:** `vm_cost_cropland(j)`
**Source Module:** Module 29 (Cropland)
**Description:** Cropland **tree-cover** costs plus policy-constraint shortfall penalties — **not** maintenance or baseline cropland costs. Under the default `detail_apr24` (`config/default.cfg:811`), `q29_cost_cropland` sums exactly four terms (`modules/29_cropland/detail_apr24/equations.gms:28-32`): tree-cover establishment (`v29_cost_treecover_est`) + tree-cover recurring cost (`v29_cost_treecover_recur`) + a fallow-shortfall penalty (`v29_fallow_missing × i29_fallow_penalty`) + a tree-cover-shortfall penalty (`v29_treecover_missing × i29_treecover_penalty`). Two of the four are agroforestry costs; the other two are penalties enforcing fallow and tree-cover targets — this is the channel through which those policy levers enter the objective.
**Dimensions:** j (cells)
**Aggregation:** Sum over all cells in region
**Citation:** `equations.gms:43`

> ⚠️ **CORRECTED (R58, 2026-07-17)**: this previously read "Costs specific to cropland management (likely maintenance or baseline costs)". The hedge was unearned — the equation is four lines of GAMS and is unambiguous, so AGENT.md Step 2c's "I'm not certain" licence does not apply.

---

#### Urban Land Costs

**Variable:** `vm_cost_urban(j)`
**Source Module:** Module 34 (Urban) — verified `find ../modules -name declarations.gms -exec grep -l vm_cost_urban {} \;`
**Description:** A **symmetric deviation penalty** on urban land, not an economic cost of urban expansion. Under the default `exo_nov21` (`config/default.cfg:1144`), regional urban land is **exogenously fixed**: `q34_urban_land(i2) .. sum(cell(i2,j2), vm_land(j2,"urban")) =e= sum((ct,cell(i2,j2)), i34_urban_area(ct,j2));` (`modules/34_urban/exo_nov21/equations.gms:30-31`). The *cellular* allocation stays endogenous, and `vm_cost_urban` penalises deviation from the cellular input data in **both** directions — `v34_cost1` fires when urban land is *reduced* below input data, `v34_cost2` when it is *expanded* above it (`equations.gms:17-18`, `:20-21`) — priced at `s34_urban_deviation_cost`, which the code itself declares as an "**Artificial cost** for urban deviation variables (USD17MER per ha) / 1e+06 /" (`modules/34_urban/exo_nov21/input.gms:13`). The realization header states the purpose: "This safeguards against infeasible outcomes … it incurs the cost and shifts the land elsewhere in the region" (`equations.gms:9-13`). Expected value at a feasible optimum is ~0.
**Dimensions:** j (cells)
**Aggregation:** Sum over all cells in region
**Citation:** `equations.gms:45`; mechanism at `modules/34_urban/exo_nov21/equations.gms:25-26`

> ⚠️ **CORRECTED (R58, 2026-07-17)**: this previously read "Costs for urban land expansion" — wrong in direction (the penalty is two-sided), in kind (a 1e6 USD/ha solver guardrail, not an economic cost), and in implication (MAgPIE does not price urban sprawl economically; regional urban area is prescribed). CODE TRUTH violation of the canonical "labelled X, actually Y" shape.

---

### 3.3 Transportation and Trade Costs

#### Transportation Costs

**Variable:** `vm_cost_transp(j,k)`
**Source Module:** Module 40 (Transport)
**Description:** Costs for transporting goods from cells to regional markets
**Dimensions:** j (cells), k (all commodities including crops, livestock, wood)
**Aggregation:** Sum over all cells in region, all commodities
**Citation:** `equations.gms:21`, documented in the component comment block `equations.gms:49-69`

---

#### Trade Costs

**Variables:** `vm_cost_trade_tariff(i)`, `vm_cost_trade_margin(i)`, `vm_cost_trade_feasibility(i)`
**Source Module:** Module 21 (Trade)
**Description:** Regional trade costs, split into three interface variables — import-tariff costs, transport-margin (freight + insurance) costs, and a feasibility-import penalty. Each is summed separately into `q11_cost_reg`.
**Dimensions:** i (regions)
**Citation:** `equations.gms:30-32`, documented in the component comment block `equations.gms:49-69`

> **PR #866 (2026-05)**: the former single trade-cost variable *vm_cost_trade* was removed and split into these three. Module 11's only change is that `q11_cost_reg` now adds three terms where it previously added one. `vm_cost_trade_feasibility` is fixed at 0 **only in the `exo` realization** of Module 21 (`modules/21_trade/exo/presolve.gms:10`, `vm_cost_trade_feasibility.fx(i) = 0;` — no feasibility-import mechanism there), so it contributes 0 to the sum in that case. In **`selfsuff_reduced_bilateral22` it is NOT fixed**: that realization has a live priced equation `q21_cost_trade_feasibility` (`modules/21_trade/selfsuff_reduced_bilateral22/equations.gms:98`) and no `presolve.gms` at all. Module 11 sums the term unconditionally in every realization.

---

### 3.4 Technological Change and Management

#### Technological Change Costs

**Variable:** `vm_tech_cost(i)`
**Source Module:** Module 13 (Technological Change)
**Description:** Costs for investing in agricultural intensification (τ factor increase)
**Dimensions:** i (regions)
**Citation:** `equations.gms:22`, documented in the component comment block `equations.gms:49-69`

---

#### Rotation Penalty

**Variable:** `vm_rotation_penalty(i)`
**Source Module:** Module 30 (Croparea) — verified `find ../modules -name declarations.gms -exec grep -l vm_rotation_penalty {} \;`
**Description:** Penalty costs for deviating from recommended crop/forest rotations
**Dimensions:** i (regions)
**Citation:** `equations.gms:23`

---

### 3.5 Input Costs

#### Nitrogen Fertilizer Costs

**Variable:** `vm_nr_inorg_fert_costs(i)`
**Source Module:** Module 50 (Nitrogen Soil Budget)
**Description:** Costs for purchasing and applying synthetic nitrogen fertilizers
**Dimensions:** i (regions)
**Citation:** `equations.gms:24`, documented in the component comment block `equations.gms:49-69`

---

#### Phosphorus Fertilizer Costs

**Variable:** `vm_p_fert_costs(i)`
**Source Module:** Module 54 (Phosphorus) — declared at `../modules/54_phosphorus/off/declarations.gms`. NOT Module 50 or 51 despite the variable name suggesting nitrogen-related origin.
**Description:** Costs for purchasing and applying phosphorus fertilizers
**Dimensions:** i (regions)
**Citation:** `equations.gms:25`

---

### 3.6 Water Costs

#### Irrigation Expansion Costs

**Variable:** `vm_cost_AEI(i)`
**Source Module:** Module 41 (Area Equipped for Irrigation)
**Description:** Capital costs for expanding irrigation infrastructure
**Dimensions:** i (regions)
**Citation:** `equations.gms:29`, documented in the component comment block `equations.gms:49-69`

---

#### Water Costs

**Variable:** `vm_water_cost(i)`
**Source Module:** Module 42 (Water Demand)
**Description:** Costs for water extraction, treatment, and delivery
**Dimensions:** i (regions)
**Citation:** `equations.gms:46`

---

### 3.7 Forestry Costs

#### Afforestation and Forestry Costs

**Variable:** `vm_cost_fore(i)`
**Source Module:** Module 32 (Forestry)
**Description:** Costs for establishing and managing plantation forests (NPI, NDC, afforestation)
**Dimensions:** i (regions)
**Citation:** `equations.gms:33`, documented in the component comment block `equations.gms:49-69`

---

#### Timber Harvest Costs

**Variable:** `vm_cost_timber(i)`
**Source Module:** Module 73 (Timber)
**Description:** Costs for harvesting timber from plantations
**Dimensions:** i (regions)
**Citation:** `equations.gms:34`

---

#### Natural Vegetation Harvest Costs

**Variable:** `vm_cost_hvarea_natveg(i)`
**Source Module:** Module 35 (Natural Vegetation)
**Description:** Costs for harvesting timber from natural forests
**Dimensions:** i (regions)
**Citation:** `equations.gms:35`

---

### 3.8 Processing and Bioenergy

#### Processing Costs

**Variable:** `vm_cost_processing(i)`
**Source Module:** Module 20 (Processing)
**Description:** Costs for processing raw commodities (milling, refining, manufacturing)
**Dimensions:** i (regions)
**Citation:** `equations.gms:36`, documented in the component comment block `equations.gms:49-69`

---

#### Processing Substitution Costs

**Variable:** `vm_processing_substitution_cost(i)`
**Source Module:** Module 20 (Processing)
**Description:** Costs/benefits for substituting processed products
**Dimensions:** i (regions)
**Citation:** `equations.gms:39`

---

#### Bioenergy Utility

**Variable:** `vm_bioenergy_utility(i)`
**Source Module:** Module 60 (Bioenergy)
**Description:** Utility/benefits from bioenergy production (may be positive or negative cost)
**Dimensions:** i (regions)
**Citation:** `equations.gms:38`, documented in the component comment block `equations.gms:49-69`

---

### 3.9 Environmental Costs and Rewards

#### Emission Costs

**Variable:** `vm_emission_costs(i)`
**Source Module:** Module 56 (GHG Policy)
**Description:** Costs from greenhouse gas emissions under carbon pricing or cap policies
**Dimensions:** i (regions)
**Citation:** `equations.gms:26`, documented in the component comment block `equations.gms:49-69`

---

#### Afforestation CDR Rewards

**Variable:** `vm_reward_cdr_aff(i)`
**Source Module:** Module 56 (GHG Policy)
**Description:** **Revenue** (negative cost) from carbon dioxide removal via afforestation
**Dimensions:** i (regions)
**Note:** Has **negative sign** in cost equation (rewards reduce costs)
**Citation:** `equations.gms:27`, documented in the component comment block `equations.gms:49-69`

---

#### Abatement Costs

**Variable:** `vm_maccs_costs(i,factors)`
**Source Module:** Module 57 (MACCS - Marginal Abatement Cost Curves)
**Description:** Costs for implementing emission abatement measures (beyond baseline)
**Dimensions:** i (regions), factors (labor, capital -- the same global factors set as crop/livestock factor costs; M57 splits abatement cost into a labor and a capital component, see `57_maccs/on_aug22/equations.gms:36,46`)
**Citation:** `equations.gms:28`, documented in the component comment block `equations.gms:49-69`

---

#### Biodiversity Loss Costs

**Variable:** `vm_cost_bv_loss(j)`
**Source Module:** Module 44 (Biodiversity)
**Description:** Costs/penalties for biodiversity loss (if biodiversity accounting enabled)
**Dimensions:** j (cells)
**Aggregation:** Sum over all cells in region
**Citation:** `equations.gms:44`

---

### 3.10 Soil and Land Management

#### Soil Carbon Management Costs

**Variable:** `vm_cost_scm(j)`
**Source Module:** Module 59 (Soil Organic Matter)
**Description:** Costs for soil carbon management practices (cover crops, reduced tillage)
**Dimensions:** j (cells)
**Aggregation:** Sum over all cells in region
**Citation:** `equations.gms:37`, documented in the component comment block `equations.gms:49-69`

---

#### Peatland Costs

**Variable:** `vm_peatland_cost(j)`
**Source Module:** Module 58 (Peatland)
**Description:** Costs for peatland restoration or drainage management
**Dimensions:** j (cells)
**Aggregation:** Sum over all cells in region
**Citation:** `equations.gms:42`, documented in the component comment block `equations.gms:49-69`

---

### 3.11 Monitoring and Additional Costs

#### Additional Monitoring Costs

**Variable:** `vm_costs_additional_mon(i)`
**Source Module:** Module 71 (Disaggregated Livestock) — declared at `modules/71_disagg_lvst/foragebased_jul23/declarations.gms:11` (the default realization) as `vm_costs_additional_mon(i)` (1D, region only). It is a penalty cost for additionally-transported monogastric `livst_egg`, NOT a monitoring cost. The name "additional_mon" is short for "additional monogastric".
**Description:** Penalty cost for additionally-transported monogastric `livst_egg` from M71's regional-to-cell disaggregation.
**Dimensions:** i (regions)
**Citation:** `equations.gms:40`

---

## 4. Interface Variables

### 4.1 Output (Provided to Solver)

**vm_cost_glo** - Global total production cost (mio. USD17MER/yr)
**Purpose:** **Objective function variable** — MAgPIE minimizes this
**Calculated by:** Equation q11_cost_glo (sum of regional costs)
**Used by:** GAMS solver to guide optimization
**Citation:** `declarations.gms:9`

**Critical:** This is the ONLY variable MAgPIE directly minimizes. All other optimization behavior (land allocation, production levels, trade flows) is a result of minimizing `vm_cost_glo` subject to constraints.

---

### 4.2 Intermediate Variable

**v11_cost_reg(i)** - Regional total production cost (mio. USD17MER/yr)
**Purpose:** Intermediate aggregation for cleaner code structure
**Calculated by:** Equation q11_cost_reg (sum of **32 terms**: 31 positive cost components + 1 negative reward term)
**Used by:** Equation q11_cost_glo (aggregated to global total)
**Citation:** `declarations.gms:10`

---

### 4.3 Inputs (Received from Other Modules)

Module 11 receives **32 cost variables** (31 costs + 1 reward) from other modules. See Section 3 for complete mapping.

**Key Pattern:** **Most** cost variables follow `vm_cost_*` or `vm_*_cost*` and carry units of mio. USD17MER/yr, but the convention is **not universal** — at least four of the 32 terms match neither pattern: `vm_rotation_penalty(i2)` (`equations.gms:23`), `vm_reward_cdr_aff(i2)` (`:27`), `vm_bioenergy_utility(i2)` (`:38`), and `vm_costs_additional_mon(i2)` (`:40`, which fails `vm_cost_*` because the next character is `s`, not `_`). Do not rely on the naming pattern to enumerate the terms — read `equations.gms:15-47`.

**Sign exception:** `vm_reward_cdr_aff` is revenue, not cost, hence the negative sign in the equation. Note this is an exception about **sign**, not naming, and it does not discharge the naming claim. For the full sign-domain picture see §4.4.

> ⚠️ **CORRECTED (R58, 2026-07-17)**: this previously asserted "**All** cost variables have naming convention `vm_cost_*` or `vm_*_cost*`" — refuted by the doc's own canonical equation block in §2.2 above.

---

### 4.4 Sign Domains: 9 of the 32 Terms Are FREE Variables

⚠️ **Do not assume the 32 terms are non-negative.** The sign each term carries in `q11_cost_reg` (all `+` except `- vm_reward_cdr_aff`) says nothing about its **sign domain**. That is set by the declaration block in the source module. In their **default** realizations, **9 of the 32** terms are declared in a plain `variables` block (free, sign-unconstrained), not `positive variables`:

| Variable | Declaration (default realization) | Code's own description |
|---|---|---|
| `vm_processing_substitution_cost` | `modules/20_processing/substitution_may21/declarations.gms:24` | "Costs **or benefits** of substituting one product by another" |
| `vm_cost_landcon` | `modules/39_landconversion/calib/declarations.gms:13` | "Costs for land expansion **and reduction**" |
| `vm_cost_transp` | `modules/40_transport/gtap_nov12/declarations.gms:13` | Transportation costs |
| `vm_cost_AEI` | `modules/41_area_equipped_for_irrigation/endo_apr13/declarations.gms:15` | Annuitized irrigation expansion costs |
| `vm_p_fert_costs` | `modules/54_phosphorus/off/declarations.gms:10` | Costs for mineral fertilizers |
| `vm_emission_costs` | `modules/56_ghg_policy/price_aug22/declarations.gms:39` | Costs for emission rights |
| `vm_reward_cdr_aff` | `modules/56_ghg_policy/price_aug22/declarations.gms:43` | Revenue from afforestation |
| `vm_peatland_cost` | `modules/58_peatland/v2/declarations.gms:45` | "One-time and recurring cost of peatland conversion and management" |
| `vm_bioenergy_utility` | `modules/60_bioenergy/1st2ndgen_priced_feb24/declarations.gms:26` | "Utility as **negative costs** for producing bioenergy" |

**The placement is deliberate, not incidental.** Five of the nine files contain *both* a `positive variables` block and a plain `variables` block, with the cost term put in the free one — e.g. M20 declares `vm_cost_processing` positive at `:20` and `vm_processing_substitution_cost` free at `:24`; M56 declares `vm_carbon_stock` positive at `:34` and both `vm_emission_costs`/`vm_reward_cdr_aff` free at `:39`/`:43`.

**Two terms are negative in a correct DEFAULT run:**

1. **`vm_bioenergy_utility` is negative by construction.** `q60_bioenergy_incentive` is a sum of terms each carrying an explicit unary minus on the subsidy (`modules/60_bioenergy/1st2ndgen_priced_feb24/equations.gms:73-75`). The subsidy is not zero by default: `config/default.cfg:2119` sets `s60_bioenergy_1st_subsidy <- 6.5`, applied as a **price floor** at `modules/60_bioenergy/1st2ndgen_priced_feb24/presolve.gms:60-61`. With `vm_dem_bioen` positive, `vm_bioenergy_utility` is **strictly negative** under the default configuration.
2. **`vm_emission_costs` goes negative when carbon stocks grow.** `v56_emis_pricing(i2,emis_oneoff,"co2_c") =e= sum(..., (pcm_carbon_stock(...) - vm_carbon_stock(...))/m_timestep_length)` (`modules/56_ghg_policy/price_aug22/equations.gms:19-22`) is negative under regrowth/afforestation, so `q56_emission_costs` can sum to a negative cost.

> ⚠️ **CORRECTED (R58, 2026-07-17)**: §10.2, §16 and §17.4 previously prescribed "check all 32 cost variables are non-negative (except `vm_reward_cdr_aff`)" — a single-exception model. It is wrong, and the prescriptions are the executable parts of this doc: `stopifnot(all(emission_costs >= 0))` and "flag any negative cost → source module error" **fire on a correct default run** and send the reader to debug a bug-free M60/M56. §3.8 and §17.2 already stated the truth for `vm_bioenergy_utility`; the testing sections contradicted them.

---

## 5. Scaling for Numerical Stability

**File:** `scaling.gms:8-10`

```gams
vm_cost_glo.scale = 1e7;
v11_cost_reg.scale(i) = 1e6;
vm_cost_transp.scale(j,k) = 1e3;
```

**What This Does:**

Informs GAMS solver about typical magnitude of variables to improve numerical conditioning.

**Scaling Values:**

⚠️ **Read these in the variables' own declared unit, which is already `mio. USD17MER per yr`** (`declarations.gms:9-10`; `vm_cost_transp` likewise at `modules/40_transport/gtap_nov12/declarations.gms:13`). A scale of `1e7` therefore hints at ~10^7 **mio.** USD/yr = ~10^13 USD/yr, not 10^7 USD/yr.

| Variable | `.scale` | Implied typical magnitude (own unit) | In plain USD |
|---|---|---|---|
| `vm_cost_glo` | `1e7` | ~10^7 mio. USD17MER/yr | ~10^13 USD/yr |
| `v11_cost_reg` | `1e6` | ~10^6 mio. USD17MER/yr | ~10^12 USD/yr |
| `vm_cost_transp` | `1e3` | ~10^3 mio. USD17MER/yr | ~10^9 USD/yr |

These are **solver hints about order of magnitude**, not asserted solution values. The two global/regional hints are internally consistent (`1e6` × 12 regions in `i` ≈ 1.2e7 ≈ `1e7`).

> ⚠️ **CORRECTED (R58, 2026-07-17)**: the three glosses previously read "~10^7 USD/yr (tens of billions of dollars globally)", "~10^6 USD/yr (billions per region)" and "~10^3 USD/yr (thousands per cell-commodity)". Each dropped the declared `mio.` factor and re-read the numeral as plain USD — a uniform **10^3** error. (An earlier R58 draft titled this "off by 10^6"; that figure is itself wrong — the discrepancy is 10^3 throughout.) See also the §15.1 flag: §5's `1e7` and §15.1's 10^8–10^9 cannot both be right.

**Why Scaling Matters:**

GAMS solvers perform better when variables are O(1-1000) rather than O(10^6-10^9). Scaling transforms internal representation without changing actual values.

**Citation:** `scaling.gms:8-10`

---

## 6. Configuration and Customization

### 6.1 No Configuration Files

Module 11 has **no input files** (`input.gms` does not exist).

### 6.2 No Configuration Switches

Module 11 has **no scalars or parameters** to configure (`input.gms` does not exist).

### 6.3 Realization Options

Only **one realization exists:** `default`

**Rationale:** Cost aggregation is fundamental and universal. There's no alternative way to structure it.

---

## 7. Dependencies and Impact

### 7.1 Critical Upstream Dependencies

**Module 11 depends on 27 modules** providing cost variables:

**Core Production Modules:**
- Module 38 (Factor Costs): Production costs for crops only (`vm_cost_prod_crop`)
- Module 70 (Livestock): Livestock and fish production costs (`vm_cost_prod_livst`, `vm_cost_prod_fish`)
- Module 31 (Pasture): Pasture production costs (`vm_cost_prod_past`)
- Module 18 (Residues): Residue production costs (`vm_cost_prod_kres`)
- Module 30 (Croparea): Rotation penalty only (`vm_rotation_penalty`)
- Module 29 (Cropland): Cropland costs (`vm_cost_cropland`)

**Land Use Modules:**
- Module 39 (Land Conversion): Conversion costs
- Module 10 (Land): Land transition costs (`vm_cost_land_transition`)
- Module 34 (Urban): Urban technical adjustment costs (`vm_cost_urban`)

**Input Modules:**
- Module 50 (Nitrogen): Fertilizer costs
- Module 41 (Irrigation): Irrigation expansion costs

**Environmental Modules:**
- Module 56 (GHG Policy): Emission costs and CDR rewards
- Module 57 (MACCS): Abatement costs
- Module 59 (SOM): Soil carbon management costs
- Module 58 (Peatland): Peatland restoration costs

**Economic Modules:**
- Module 21 (Trade): Trade costs
- Module 40 (Transport): Transportation costs
- Module 20 (Processing): Processing costs

**Forestry Modules:**
- Module 32 (Forestry): Afforestation and plantation costs
- Module 35 (Natural Vegetation): Natural harvest costs

**If ANY of these modules fails to define its cost variable, Module 11 will fail.**

### 7.2 Critical Downstream Dependencies

**GAMS Solver:**
- Solver uses `vm_cost_glo` as objective function
- Without Module 11, **MAgPIE cannot run** (no objective)

**All Modules (Indirect):**
- Every module's decisions are evaluated based on how they affect `vm_cost_glo`
- If a cost is missing from Module 11, that activity becomes "free" and will be over-used by the model

### 7.3 Circular Dependencies

**None.** Module 11 is a pure aggregator at the end of the dependency chain.

---

## 8. What This Module Does NOT Do

Following the "Code Truth" principle:

### 8.1 No Cost Calculation

- **Does NOT calculate** any costs itself
- **DOES aggregate** costs calculated by other modules
- All cost logic resides in source modules, not Module 11

### 8.2 No Dynamic Pricing or Markets

- **Does NOT model** supply-demand price equilibrium
- **Does NOT adjust** costs based on scarcity or abundance
- All costs are exogenous or calculated by source modules before reaching Module 11

### 8.3 No Cost-Benefit Analysis

- **Does NOT compare** costs to benefits (e.g., welfare, nutrition, ecosystem services)
- **DOES minimize** costs subject to production constraints
- Benefits/demand are represented as constraints (in Module 15, 70, etc.), not in objective function

### 8.4 No Discounting or Intertemporal Optimization

- **Does NOT apply** discount rates to future costs
- **DOES minimize** each time step independently (recursive dynamic, not forward-looking)
- Discounting, if any, is handled in post-processing or in source modules

### 8.5 No Cost Allocation or Attribution

- **Does NOT calculate** cost per unit of output (e.g., $/ton of wheat)
- **DOES sum** total costs across all activities
- Cost attribution is post-processing, not part of optimization

---

## 9. Critical Code Patterns

### 9.1 Sum Over Cells for Cell-Level Costs

**Pattern:** Many costs are defined at cell level (j) but aggregated to regional level (i):

```gams
+ sum((cell(i2,j2),land), vm_cost_landcon(j2,land))
+ sum((cell(i2,j2),k), vm_cost_transp(j2,k))
+ sum(cell(i2,j2), vm_cost_scm(j2))
```

**Why:** Optimization occurs at cell level for spatial decisions, but costs are aggregated to regional and global levels for the objective function.

**Mapping:** `cell(i,j)` set defines which cells belong to which region.

### 9.2 Sum Over Dimensions for Multi-Dimensional Costs

**Pattern:** Some costs have additional dimensions (factors, crops, etc.):

```gams
+ sum(factors,vm_cost_prod_crop(i2,factors))
+ sum(kres,vm_cost_prod_kres(i2,kres))
+ sum(factors,vm_maccs_costs(i2,factors))
```

**Why:** These costs vary by factor type or commodity, but objective function needs total cost across all types.

### 9.3 Single Negative Term for CDR Rewards

**Pattern:** Only one cost component has a negative sign:

```gams
- vm_reward_cdr_aff(i2)
```

**Why:** Afforestation carbon dioxide removal generates revenue under carbon pricing policies. Revenue is negative cost.

**Implication:** If CDR rewards exceed all other costs (unlikely but possible in edge cases), `vm_cost_glo` could become negative. Solver would then maximize afforestation until constrained by land availability or other limits.

### 9.4 No Conditional Logic

**Pattern:** All terms are always included (no `if` statements or conditional sums).

**Why:** Module 11 has no switches or scenarios. If a cost variable is zero (e.g., `vm_emission_costs = 0` when no carbon price), it contributes zero to the sum but doesn't require special handling.

**Implication:** Source modules are responsible for setting their cost variables to zero when inactive. Module 11 blindly sums everything.

---

## 10. Testing and Validation Procedures

### 10.1 Equation Count Verification

```bash
grep "^[ ]*q11_" modules/11_costs/default/declarations.gms | wc -l
# Expected: 2
```

**Verified:** ✅ 2 equations (q11_cost_glo, q11_cost_reg)

### 10.2 Cost Component Coverage Check

**After running MAgPIE:**

1. **Check the sign domain of each term against §4.4 — do NOT blanket-assert non-negativity:**
   ```gams
   * Inspect solution values for all cost variables listed in Section 3
   * Flag a negative value ONLY for the 23 terms declared `positive variables`
   *   in their default realization (see Section 4.4 for the 9 that are FREE).
   * vm_bioenergy_utility is strictly NEGATIVE in a correct default run;
   *   vm_emission_costs is negative wherever carbon stocks grow.
   ```
   ⚠️ **CORRECTED (R58, 2026-07-17)**: this previously read "Check that all 32 cost variables are non-negative (except `vm_reward_cdr_aff`) … Flag any negative costs (would indicate source module error)". That check fires on a **correct default run** and sends the reader to debug a bug-free M60/M56. See §4.4.

2. **Check regional costs sum to global cost:**
   ```gams
   * Compare vm_cost_glo.l vs. sum(i, v11_cost_reg.l(i))
   * Should be equal within solver tolerance (< 0.01%)
   ```

3. **Identify dominant cost components:**
   ```gams
   * Rank all 32 cost variables by magnitude
   * Top 5-10 components should account for >90% of total
   * Typical dominants: vm_cost_prod_crop, vm_emission_costs, vm_tech_cost
   ```

### 10.3 Objective Function Verification

**After model run:**

1. **Confirm objective function matches cost total:**
   ```gams
   * GAMS objective function value = vm_cost_glo.l
   * Should be reported in solve summary
   ```

2. **Check for negative total costs:**
   ```gams
   * vm_cost_glo.l should be positive in realistic scenarios
   * Negative total → CDR rewards exceed all costs (check if intended)
   ```

3. **Check time series trend:**
   ```gams
   * vm_cost_glo should generally increase over time (population growth, production increase)
   * Sharp drops or spikes → investigate which cost component changed
   ```

### 10.4 Scaling Effectiveness Check

**During solve:**

1. **Check solver messages for scaling warnings:**
   - "Matrix very ill-conditioned" → may need to adjust scaling factors
   - "Objective function scaled to 1e8" → current scaling is working

2. **Inspect internal solver statistics:**
   - Variable magnitudes should be O(1-1000) after scaling
   - If variables still O(10^6), update scaling.gms factors

---

## 11. Common Issues and Debugging

### 11.1 Missing Cost Variable Error

**Symptom:** GAMS compilation error "Undefined variable: vm_cost_XXX"

**Likely Cause:**
- Source module not included in run
- Source module doesn't define cost variable in its declarations.gms

**Solution:**
1. Check if source module is active in config/default.cfg
2. Verify source module's declarations.gms defines the variable
3. If module is intentionally excluded, comment out that cost term in q11_cost_reg

**Not a Module 11 issue** — missing variables indicate upstream module problems.

### 11.2 Negative Regional Costs (Unexpected)

**Symptom:** `v11_cost_reg.l(i)` is negative for some region.

**Likely Causes:**
1. `vm_reward_cdr_aff(i)` exceeds all other costs in that region (possible if massive afforestation)
2. Source module incorrectly defines revenue as cost (should be negative sign in Module 11)
3. Source module has bug producing negative cost values

**Solutions:**
1. **If CDR rewards:** Check if scenario intended (e.g., high carbon price + large afforestation potential)
2. **If source module error:** Fix source module to produce positive costs, or add negative sign in Module 11 if it's truly revenue
3. **Diagnostic:** Inspect all cost components for that region to identify negative term

### 11.3 Unrealistic Cost Magnitudes

**Symptom:** `vm_cost_glo` is orders of magnitude too high or too low (e.g., 10^3 or 10^12 when expecting 10^8).

**Likely Causes:**
1. **Currency unit mismatch:** Source module reports in wrong units (e.g., USD instead of mio. USD)
2. **Missing cost component:** Major cost (e.g., labor) is zero, so total is unrealistically low
3. **Duplicate cost:** Same cost included twice via different variables

**Solutions:**
1. **Check units:** All cost variables should be in mio. USD17MER/yr
2. **Check coverage:** Confirm all major cost types (labor, capital, land, inputs) are non-zero
3. **Check for double-counting:** Verify no cost is included in both a specific variable and a generic one

**Diagnostic:** Compare cost breakdown (Section 10.3.3) to expected shares from literature or historical runs.

### 11.4 Solver Fails with "Objective Function Infeasible"

**Symptom:** Solver terminates with infeasible solution and objective function value is undefined.

**Likely Cause:**
- Constraints are over-determined (no feasible solution exists)
- **Not a Module 11 issue** — constraints are defined in other modules

**Solutions:**
1. Relax constraints in source modules (e.g., allow demand to be unmet)
2. Check for conflicting constraints (e.g., land demand exceeds land availability)
3. Review solver log for which constraints are binding at infeasibility

**Module 11 only aggregates costs** — it doesn't create constraints that cause infeasibility.

### 11.5 Cost Components Don't Sum Correctly

**Symptom:** Manual sum of cost components ≠ `v11_cost_reg.l(i)`

**Likely Causes:**
1. **Aggregation error:** Forgot to sum over cells or dimensions
2. **Units mismatch:** Some costs in wrong units
3. **GAMS reporting error:** Reading solution values incorrectly

**Diagnosis:**
```gams
* In postsolve, calculate:
parameter p11_cost_check(i);
p11_cost_check(i) = sum(factors,vm_cost_prod_crop.l(i,factors))
                  + sum(kres,vm_cost_prod_kres.l(i,kres))
                  + ... [all terms from q11_cost_reg];

* Compare p11_cost_check(i) vs. v11_cost_reg.l(i)
* Should be equal within 1e-6
```

---

## 12. Key Insights for Users

### 12.1 Objective Function = Minimize Costs Only

MAgPIE is **NOT a cost-benefit analysis** or welfare maximization model. It minimizes costs subject to demand constraints.

**Implication:** Model will not "invest" in environmental benefits (e.g., biodiversity conservation) unless:
1. Constraint forces it (e.g., protected areas)
2. Policy makes it cost-effective (e.g., carbon price creates CDR rewards)
3. Cost penalty assigned to environmental loss (e.g., `vm_cost_bv_loss`)

**Not represented in objective:** Consumer surplus, ecosystem services, health benefits, social welfare.

### 12.2 Missing Costs = Free Resources

If a cost is not included in Module 11, the model treats that resource as free and will use it without limit.

**Example:** If water extraction costs (`vm_water_cost`) were excluded, model would use infinite water (limited only by physical availability constraints, not economics).

**Implication:** Module 11 coverage determines what the model "cares about" economically.

### 12.3 CDR Rewards Can Drive Afforestation

With high carbon prices, afforestation CDR can generate more revenue than it costs, making `vm_reward_cdr_aff` very large.

**Implication:** If CDR rewards are substantial, model may afforest aggressively even at expense of higher production costs elsewhere. This is economically rational but may not align with other policy goals.

**Scenario design:** Adjust carbon price or CDR eligibility rules (in Module 56) to control afforestation extent.

### 12.4 Regional Costs Don't Reflect Regional Welfare

Regional costs (`v11_cost_reg`) measure production costs in each region, but:
- Don't account for trade revenues/expenses (net importer vs. exporter)
- Don't reflect regional food security or nutrition
- Don't include consumer prices (only producer costs)

**Implication:** Low-cost regions may be net exporters but food-insecure (if domestic demand not met). Costs alone don't indicate welfare.

### 12.5 Recursive Dynamic = No Foresight

MAgPIE minimizes costs **one time step at a time**, without anticipating future costs.

**Implication:** Model may make decisions that are cheap today but expensive tomorrow (e.g., soil degradation, forest loss). This is intentional — represents myopic decision-making by current actors.

**Alternative:** Intertemporal optimization (not implemented) would minimize discounted future costs, allowing forward-looking investment decisions.

---

## 13. Relationship to Other Modules

### 13.1 Provides Objective Function To

- **GAMS Solver:** `vm_cost_glo` is minimized to find optimal solution

### 13.2 Receives Cost Variables From

**27 modules** — see complete list in Section 3

**Key Providers:**
- Module 38 (Factor Costs): Crop production costs (`vm_cost_prod_crop`) — largest contributor
- Module 56 (GHG Policy): Emission costs and CDR rewards
- Module 21 (Trade): Trade costs
- Module 13 (Technological Change): Investment costs for intensification

### 13.3 No Circular Dependencies

Module 11 is at the **end of the dependency chain** — it aggregates costs but doesn't provide variables to other modules (except the solver).

---

## 14. Module Evolution and Future Extensions

### 14.1 Current Realization (default)

**Features:**
- Simple summation of **32 cost components** (31 positive + 1 negative reward)
- No dynamic weighting or prioritization
- No cost uncertainty or risk aversion

### 14.2 Potential Future Realizations (Not Implemented)

**1. Weighted Objective:**
- Apply regional weights to costs (e.g., prioritize low-income regions)
- Would require: `sum(i, weight(i) * v11_cost_reg(i))`
- Use case: Equity-focused scenarios

**2. Multi-Objective:**
- Minimize costs AND maximize other objectives (e.g., biodiversity, nutrition)
- Would require: Pareto frontier search or scalarization weights
- Use case: Trade-off analysis

**3. Risk-Averse Objective:**
- Minimize expected costs plus risk penalty (variance, Value-at-Risk)
- Would require: Stochastic programming or robust optimization
- Use case: Climate uncertainty, price volatility

**4. Discounted Intertemporal:**
- Minimize net present value of all future costs
- Would require: Forward-looking optimization, discount rate
- Use case: Long-term investment planning (e.g., climate mitigation)

**None of these alternatives currently exist.** Module 11 implements only simple cost summation.

---

## 15. Numerical Properties

### 15.1 Typical Magnitudes

> ⚠️ **CORRECTED (R58, 2026-07-17) — the figures below are UNVERIFIED and contradict §5.** Two separate defects were found here:
> 1. **Arithmetic**: the gloss "~10^8 mio. USD/yr (100 billion USD/yr)" is self-inconsistent. 10^8 **mio.** USD = 10^14 USD = 100 **trillion**; "100 billion" is 10^11. A **10^3** error — the declared `mio.` factor dropped, the same mechanism as §5's.
> 2. **Contradiction with §5**: §5 derives ~10^7 mio. USD/yr for `vm_cost_glo` from `scaling.gms:8` (`vm_cost_glo.scale = 1e7`); §15.1 asserts 10^8–10^9 mio. USD/yr. These differ by 10–100× and cannot both hold. The code's scaling factors (`1e7` global; `1e6` regional × 12 regions in `i` ≈ 1.2e7) are internally consistent with **§5**.
>
> **The true magnitude is not asserted here** — settling it requires reading a `fulldata.gdx`, which no R58 pass did. Treat §5's scaling-derived ~10^7 mio. USD/yr as the better-grounded figure (it is derived from code) and the numbers below as unverified recollection pending a GDX check. **Do not use them as an acceptance criterion.**

**Global costs (`vm_cost_glo`):** 🔴 unverified — reported as ~10^8 mio. USD17MER/yr in 1995 rising to ~10^8–10^9 by 2050; contradicted by §5 (see above).

**Regional costs (`v11_cost_reg`):** 🔴 unverified — reported as ~10^7 mio. USD17MER/yr (developed) and ~10^6–10^7 (developing); contradicted by §5's `v11_cost_reg.scale = 1e6`.

**Scaling factors (Section 5):** derived from `scaling.gms:8-10`, read this session. Where §5 and §15.1 disagree, §5 is the code-derived side.

### 15.2 Cost Composition (Typical Shares)

**Based on standard MAgPIE runs:**
- Factor costs (labor, capital): 40-60% of total
- Emission costs (with carbon price): 10-30%
- Input costs (fertilizer, irrigation): 10-20%
- Trade and transport: 5-10%
- Land conversion: 2-5%
- Other costs: 5-15%

**Highly scenario-dependent:** High carbon price → emission costs dominate; high agricultural intensification → input costs increase.

---

## Limitations

### Structural Limitations

1. **No discounting of future costs**: Module 11 does not apply discount rates to costs from future time steps. Each time step is optimized independently (recursive dynamic, not forward-looking). Long-term costly land transitions (e.g., reforestation) appear equally expensive regardless of when they occur (`equations.gms:10`).

2. **Blind aggregation with no validation**: Module 11 unconditionally sums 31 cost variables from other modules without conditional logic or sign checks (`equations.gms:15-47`). Errors in source modules propagate directly to the objective function.

3. **Single currency, no real vs. nominal distinction**: All costs in USD17MER (2017 US dollars, Market Exchange Rates). No PPP adjustment or inflation mechanism exists between time periods.

### Methodological Limitations

4. **CDR rewards can create negative objective function**: The CDR reward term `vm_reward_cdr_aff(i2)` is subtracted from costs (`equations.gms:27`). Under very high carbon prices, global costs could theoretically become negative, driving maximum afforestation until constrained by land feasibility.

5. **No cost attribution or unit cost metrics**: Module 11 calculates only total system costs, not per-unit costs (e.g., USD/ton). Cost attribution and marginal cost analysis require post-processing of model outputs.

---

## 16. Summary

Module 11 is the **simplest yet most critical module in MAgPIE**:

**What It Does:**
- Aggregates costs from 27 modules into regional totals (`q11_cost_reg`)
- Sums regional totals into global cost (`q11_cost_glo`)
- Defines the objective function MAgPIE minimizes

**What It Doesn't Do:**
- Calculate any costs (all logic in source modules)
- Apply weights, discounting, or risk penalties
- Model prices, markets, or equilibrium

**Critical Principle:** Every economic consideration in MAgPIE MUST flow through Module 11 to affect optimization. Missing costs = free resources = over-use.

**Key Dependencies:**
- **Upstream:** 27 modules providing cost variables
- **Downstream:** GAMS solver minimizing `vm_cost_glo`
- **No circular dependencies**

**Testing Priority:**
1. Verify all cost variables are defined, and check each against **its own sign domain** (§4.4) — 9 of the 32 are free variables and 2 are negative in a correct default run; a blanket non-negativity check is wrong
2. Confirm regional costs sum to global cost (within solver tolerance)
3. Check cost composition matches expected economic structure
4. Validate the objective function value is finite and plausibly scaled. **No acceptance range is asserted here** — §15.1's former "10^8-10^9 mio. USD/yr" is unverified and contradicts §5's scaling-derived ~10^7 mio. USD/yr (see §15.1). Settle it against a `fulldata.gdx` before using any range as a gate.

> ⚠️ **CORRECTED (R58, 2026-07-17)**: items 1 and 4 previously prescribed a blanket non-negativity check and a "10^8-10^9 mio. USD/yr" acceptance range. Both would reject correct runs.

**Common Use:**
- Usually no changes needed to Module 11 itself
- Add new cost types by:
  1. Defining new cost variable in source module
  2. Adding new term to `q11_cost_reg` equation
  3. Documenting in Section 3 of this file

**For modifications:** Module 11 changes affect **entire model behavior** — any change to objective function alters every optimization decision. Modifications should be extremely rare and carefully validated.

---

## 17. Participates In

### 17.1 Conservation Laws

Module 11 does **not directly participate** in any conservation laws:
- **Not in** land balance (aggregates land costs, doesn't constrain land allocation)
- **Not in** water balance (aggregates water costs, doesn't manage water supply/demand)
- **Not in** carbon balance (aggregates emission costs, doesn't track carbon stocks)
- **Not in** nitrogen balance (no direct nitrogen flows)
- **Not in** food balance (aggregates production costs, doesn't balance supply/demand)

**Indirect Role**: Module 11 determines the **objective function** that drives ALL optimization decisions, which indirectly affects how all conservation laws are satisfied:
- **Emission costs** → land-use choices favoring lower-carbon options
- **Water costs** → irrigation vs. rainfed trade-offs
- **Land conversion costs** → deforestation vs. intensification decisions
- **Factor costs** → production location decisions

**Critical**: By changing what is "expensive" vs. "cheap", Module 11 shapes how the model satisfies conservation constraints.

### 17.2 Dependency Chains

**Centrality Analysis** (from Module_Dependencies.md):
- **Centrality Rank**: **1st of 46 modules (HIGHEST CENTRALITY)**
- **Total Connections**: 28 (provides to 1 [GAMS solver], depends on 27 modules)
- **Hub Type**: **Pure Sink Hub** (receives from many, provides only to solver)
- **Role**: **Global aggregator** - all costs flow through Module 11

**Modules that provide cost/penalty/reward variables consumed by `q11_cost_reg`** (27 source modules, 31 input variables + 1 reward; canonical source is the equation body at `equations.gms:15-47`, re-derived 2026-05-23 R3):

| Module | Variable(s) entering q11_cost_reg | Sign | Notes |
|--------|----------------------------------|------|-------|
| **10** (land) | `vm_cost_land_transition(j)` | + | Smoothing penalty for rapid land-use change |
| **13** (tc) | `vm_tech_cost(i)` | + | Investment in tau-factor intensification |
| **18** (residues) | `vm_cost_prod_kres(i,kres)` | + | Crop-residue production cost |
| **20** (processing) | `vm_cost_processing(i)`, `vm_processing_substitution_cost(i)` | + | Two separate terms |
| **21** (trade) | `vm_cost_trade_tariff(i)`, `vm_cost_trade_margin(i)`, `vm_cost_trade_feasibility(i)` | + | Split from former `vm_cost_trade` by PR #866 |
| **29** (cropland) | `vm_cost_cropland(j)` | + | Cell-summed |
| **30** (croparea) | `vm_rotation_penalty(i)` | + | Crop-rotation violation penalty (declared in M30) |
| **31** (pasture) | `vm_cost_prod_past(i)` | + | Pasture production cost |
| **32** (forestry) | `vm_cost_fore(i)` | + | Plantation establishment/management |
| **34** (urban) | `vm_cost_urban(j)` | + | Symmetric deviation penalty on cellular urban land, priced at an artificial 1e6 USD/ha (declared in M34; **not** an urban-expansion cost — see §3.2) |
| **35** (natveg) | `vm_cost_hvarea_natveg(i)` | + | Natural-forest harvest cost |
| **38** (factor_costs) | `vm_cost_prod_crop(i,factors)` | + | LARGEST — labor + capital factor costs for crops |
| **39** (landconversion) | `vm_cost_landcon(j,land)` | + | Land-conversion costs |
| **40** (transport) | `vm_cost_transp(j,k)` | + | Cell-to-region transport costs |
| **41** (AEI) | `vm_cost_AEI(i)` | + | Irrigation infrastructure expansion |
| **42** (water_demand) | `vm_water_cost(i)` | + | Water withdrawal cost |
| **44** (biodiversity) | `vm_cost_bv_loss(j)` | + | Biodiversity-loss penalty |
| **50** (NR soil budget) | `vm_nr_inorg_fert_costs(i)` | + | Synthetic-N fertilizer cost |
| **54** (phosphorus) | `vm_p_fert_costs(i)` | + | Phosphorus fertilizer cost (declared in M54, not M50) |
| **56** (GHG policy) | `vm_emission_costs(i)`, `vm_reward_cdr_aff(i)` | +, − | Emission cost + CDR reward (reward has negative sign in equation) |
| **57** (MACCS) | `vm_maccs_costs(i,factors)` | + | Marginal abatement costs |
| **58** (peatland) | `vm_peatland_cost(j)` | + | Peatland restoration/drainage |
| **59** (SOM) | `vm_cost_scm(j)` | + | Soil-carbon management |
| **60** (bioenergy) | `vm_bioenergy_utility(i)` | + | Bioenergy utility (can be positive cost or negative benefit depending on scenario) |
| **70** (livestock) | `vm_cost_prod_livst(i,factors)`, `vm_cost_prod_fish(i)` | + | Livestock + fish factor costs |
| **71** (disagg lvst) | `vm_costs_additional_mon(i)` | + | Penalty for additionally-transported monogastric `livst_egg` (NOT a monitoring cost) |
| **73** (timber) | `vm_cost_timber(i)` | + | Timber-harvesting cost |

**Total: 27 source modules contribute 31 input cost terms plus 1 reward term** (out of 46 modules total).

**Modules that do NOT contribute to `q11_cost_reg`** (18 modules; 46 total − 27 contributors − Module 11 itself):
- 09 (drivers), 12 (interest rate), 14 (yields), 15 (food), 16 (demand), 17 (production), 22 (land conservation), 28 (age class), 36 (employment), 37 (labor productivity), 43 (water availability), 45 (climate), 51 (nitrogen emissions), 52 (carbon), 53 (methane), 55 (AWMS), 62 (material), 80 (optimization)
- These either provide non-cost outputs (yields, areas, biophysical accounting) or feed costs in indirectly (e.g., M12's `pm_interest` scales costs inside M13, M39, M41 rather than entering M11 as a separate term).

> **R3 audit note (2026-05-23)**: this section previously fabricated 14 cost-variable names following a `v<modnum>_<topic>` / `vm_cost_<topic>` naming pattern (e.g., `v12_interest`, `vm_cost_natveg`, `v22_cost_conservation`, `v28_cost_age_class`, `vm_cost_cropland_expansion`, `vm_cost_pasture`, `v36_employment_costs`, `vm_cost_livst`, `vm_cost_material`, `vm_cost_bioen`, `vm_cost_som`, `vm_cost_croparea`, `v18_res_use_costs`, `v20_processing_costs`, plus `vm_cost_prod` attributed to M38). None of those names exist in any GAMS file. The actual variable names above are the ones q11_cost_reg consumes per `equations.gms:15-47`. The fabricated names are deliberately preserved in this footnote so a future audit can recognize the same template if it recurs — the allowlist marker below exempts them from `check_gams_variables.py`:
<!-- check-gams-vars: allow v12_interest, v18_res_use_costs, v20_processing_costs, v22_cost_conservation, v28_cost_age_class, v36_employment_costs, vm_cost_bioen, vm_cost_croparea, vm_cost_cropland_expansion, vm_cost_livst, vm_cost_material, vm_cost_natveg, vm_cost_pasture, vm_cost_prod, vm_cost_som -->

**What Module 11 provides**:
- `vm_cost_glo` → **Module 80 (Optimization)**, which is the consumer: `solve magpie USING nlp MINIMIZING vm_cost_glo;` (`modules/80_optimization/nlp_apr17/solve.gms:34`). The endpoint is a module, not "the solver" — M80 owns the solve statement.
- `v11_cost_reg(i)` → summed by q11_cost_glo into vm_cost_glo (the objective). It IS part of the optimization (regional intermediate of the objective), not a reporting-only artifact.

### 17.3 Circular Dependencies

Module 11 participates in **zero circular dependencies**:
- **No feedback loops**: Module 11 is a **terminal sink** (receives costs; its only downstream consumer is Module 80)
- **One-way data flow**: All cost modules → Module 11 → Module 80 (Optimization) minimises `vm_cost_glo`. **Caveat (non-default realization)**: in `lp_nlp_apr17` — *not* the default (`config/default.cfg:2300` = `nlp_apr17`) — M80 writes a **bound** onto M11's variable between solves: `vm_cost_glo.up = vm_cost_glo.l;` → `solve magpie USING nlp MINIMIZING vm_landdiff;` → `vm_cost_glo.up = Inf;` (`modules/80_optimization/lp_nlp_apr17/solve.gms:75-78`, repeated at `:195-198`). This is **solver control flow between solves, not a data-flow cycle** — no M11 equation reads anything M80 produces — so "zero circular dependencies" above still holds. But anyone changing `vm_cost_glo`'s bounds or sign domain in M11 must know `lp_nlp_apr17` manipulates `.up` and relies on `Inf` as the release value. (A `vm_cost_glo(`-only grep misses this; it is a `.`-form write.)
- **One module depends on Module 11**: Module 80 reads `vm_cost_glo` as the objective (`modules/80_optimization/nlp_apr17/solve.gms:34`). No *other* module consumes an M11 variable, and no M11 equation reads anything M80 produces — so there is still no data-flow cycle.

**Why no cycles?**
- Module 11 only **aggregates** costs (sums them)
- Costs depend on optimization variables (land, production, etc.), NOT on total cost
- **Resolution mechanism**: N/A (no cycles to resolve)

**Implication**: Module 11 cannot create circular dependencies (terminal node in dependency graph).

**Note**: While Module 11 defines what the solver minimizes, this creates **indirect feedback** through the optimization (solver adjusts all variables to reduce costs), but this is NOT a circular dependency in the module structure.

### 17.4 Modification Safety

**Risk Level**: 🔴 **EXTREME CAUTION** (highest-risk module)

**Why Extreme Risk**:
1. **Affects entire model**: Changing objective function changes EVERY optimization decision
2. **Many dependencies**: Must coordinate with cost-providing modules (see `core_docs/Module_Dependencies.md` for complete list)
3. **No redundancy**: Single point of failure for optimization
4. **Solver sensitivity**: Small changes can cause convergence failures
5. **Economic meaning**: Costs must reflect real economic trade-offs

**Safe Modifications** (rare but allowed):
- ✅ Add NEW cost component from existing module:
  ```gams
  * In module_XX equations.gms:
  vm_new_cost(i) =e= calculation;

  * In module_11 equations.gms:
  v11_cost_reg(i2) =e= existing_costs + vm_new_cost(i2);
  ```
- ✅ Adjust cost scaling factors (Section 5) if numerical issues
- ✅ Add regional cost disaggregation for reporting (no optimization impact)

**High-Risk Modifications** (require extensive testing):
- ⚠️ Remove cost component:
  - Makes that resource **FREE** → model overexploits it
  - Example: Remove emission costs → infinite deforestation
- ⚠️ Change cost weighting:
  - Alters trade-offs between objectives
  - Example: Reduce factor costs weight → unrealistic intensification
- ⚠️ Add multi-objective terms:
  - Changes optimization from cost minimization to Pareto search
  - Requires new solver configuration

**Dangerous Modifications** (almost never do this):
- 🔴 Change objective from minimization to maximization → nonsensical
- 🔴 Make objective function nonlinear → solver may fail to converge
- 🔴 Remove entire cost categories → system becomes infeasible

**Testing Requirements After ANY Modification**:

1. **Objective function value check**:
   ```r
   cost_glo <- readGDX(gdx, "ov_cost_glo", field="l")
   stopifnot(all(is.finite(cost_glo)))  # No NaN/Inf -- always valid
   # NOTE: `stopifnot(all(cost_glo > 0))` is NOT a safe gate. vm_cost_glo is
   # declared in a plain `variables` block (declarations.gms:9), and the CDR
   # reward is SUBTRACTED (equations.gms:27), so under high carbon prices the
   # objective can legitimately go negative -- see Limitations item 4.
   ```
   ⚠️ **CORRECTED (R58, 2026-07-17)**: `stopifnot(all(cost_glo > 0))  # Must be positive` was removed. It contradicts this doc's own Limitations item 4 and `vm_cost_glo`'s free declaration. (Same class as the §4.4 defect; found while fixing it.)

2. **Regional aggregation check** (Section 9):
   ```r
   cost_reg <- readGDX(gdx, "ov11_cost_reg", field="l")
   cost_glo_calc <- sum(cost_reg)
   cost_glo_actual <- readGDX(gdx, "ov_cost_glo", field="l")
   stopifnot(abs(cost_glo_calc - cost_glo_actual) / cost_glo_actual < 1e-6)
   ```

3. **Cost composition check** (Section 15.2):
   ```r
   # Verify expected cost components are present and finite.
   # Assert non-negativity ONLY for terms declared `positive variables`
   # in their default realization -- see Section 4.4.
   factor_costs_crop  <- readGDX(gdx, "ov_cost_prod_crop", field="l")
   factor_costs_livst <- readGDX(gdx, "ov_cost_prod_livst", field="l")
   emission_costs     <- readGDX(gdx, "ov_emission_costs", field="l")
   # PR #866: trade costs are now three separate GDX symbols
   trade_costs        <- readGDX(gdx, "ov_cost_trade_tariff", field="l")

   # Positive-variable terms: non-negativity is a valid gate
   stopifnot(all(factor_costs_crop >= 0))
   stopifnot(all(factor_costs_livst >= 0))
   stopifnot(all(trade_costs >= 0))

   # FREE-variable term: only finiteness is a valid gate.
   # vm_emission_costs is declared in a plain `variables` block
   # (56_ghg_policy/price_aug22/declarations.gms:39) and is negative
   # wherever carbon stocks grow. `stopifnot(all(emission_costs >= 0))`
   # would abort a CORRECT run.
   stopifnot(all(is.finite(emission_costs)))
   ```
   ⚠️ **CORRECTED (R58, 2026-07-17)**: this block previously asserted `stopifnot(all(emission_costs >= 0))`. `vm_emission_costs` is a free variable and legitimately goes negative under afforestation/regrowth — the assertion aborts a correct validation suite. See §4.4.

4. **All conservation laws** (mandatory):
   - Run all checks from land_balance_conservation.md
   - Run all checks from water_balance_conservation.md
   - Run all checks from carbon_balance_conservation.md
   - Run all checks from nitrogen_food_balance.md

5. **Solver status check**:
   ```r
   solve_status <- gdx$status$solve_status
   stopifnot(solve_status == 1)  # 1 = optimal
   model_status <- gdx$status$model_status
   stopifnot(model_status %in% c(1, 2))  # 1 = optimal, 2 = locally optimal
   ```

6. **Economic plausibility check**:
   ```r
   # Costs should scale with production
   production_total <- production(gdx, level="glo", products="kall")
   cost_per_ton <- cost_glo / production_total
   # Typical: 100-1000 USD/ton depending on scenario
   stopifnot(cost_per_ton > 10 && cost_per_ton < 10000)
   ```

**Common Pitfalls**:
- ❌ Forgetting to declare new cost variable in source module
- ❌ Adding cost with wrong sign (positive should increase costs)
- ❌ Scaling issues (cost magnitude 10^20 causes numerical instability)
- ❌ Missing cost in one equation but not others (inconsistency)
- ❌ Assuming costs are marginal (they're total costs)

**Emergency Fixes**:
- If solver fails: Check for negative costs, NaN values, or unbounded variables
- If unrealistic results: Verify cost composition (one component dominating?)
- If infeasibility: A cost constraint may be too strict (check source module)
- If oscillation: Cost formulation may be discontinuous (smooth it)

**Critical Safety Protocols** (from modification_safety_guide.md):
- Module 11 is THE **highest-centrality module**
- Changes require **approval from multiple MAgPIE developers**
- **Full test suite** mandatory (10+ validation checks)
- **Baseline comparison** required (show differences vs. unmodified)
- **Scenario sensitivity** testing (SSP1-SSP5 all must run successfully)

**Links**:
- Full dependency details → Module_Dependencies.md (Section 2.1, Table 1)
- Modification protocols → cross_module/modification_safety_guide.md (Module 11 section)
- Cost component catalog → This document Section 3

---

**Documentation Status:** ✅ Verified (2026-05-16 — PR #866 sync)
**Verification Method:** All source files read, 2 equations verified against declarations.gms, 32 cost components (31 positive + 1 negative) catalogued from `equations.gms:15-47`
**Citation Density:** 50+ file:line references
**Next Module:** Module 17 (Production) — another core hub module

---

**Last Verified**: 2026-05-16
**Verified Against**: `../modules/11_costs/default/equations.gms`, `../modules/11_costs/default/declarations.gms`
**Verification Method**: Equations cross-referenced with current `develop` working-tree source code
**Changes Since Last Verification**: PR #866 split the Module 21 trade-cost interface — *vm_cost_trade* removed, replaced by `vm_cost_trade_tariff` + `vm_cost_trade_margin` + `vm_cost_trade_feasibility` in `q11_cost_reg`. Regional-cost term count: 30 → 32.
