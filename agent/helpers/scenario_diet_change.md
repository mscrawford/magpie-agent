# Helper: Setting Up Diet Change Scenarios

**Auto-load triggers**: "diet", "EAT-Lancet", "food demand", "livestock reduction", "food waste", "dietary change", "BMI", "food scenario"
**Last updated**: 2026-03-06
**Lessons count**: 0 entries

---

## Quick Reference

Diet scenarios are configured entirely in **Module 15** (`anthro_iso_jun22`). There are **three independent mechanisms** for modifying diets, plus food waste control. All parameters are in `modules/15_food/anthro_iso_jun22/input.gms` (lines 65–115) and `config/default.cfg` (lines 413–602).

| Mechanism | Master Switch | What It Does |
|-----------|--------------|--------------|
| **Exogenous diet (EAT-Lancet)** | `s15_exo_diet` (0,1,2,3) | Replace regression diets with EAT-Lancet targets |
| **Food substitution** | `s15_*_substitution` scalars | Fade out specific food groups post-regression |
| **Livestock calorie target** | `s15_livescen_target` (0,1) | Cap livestock kcal/cap/day at threshold |
| **Food waste reduction** | `s15_exo_waste` (0,1) | Reduce demand-to-intake ratio |

**Data flow**: Module 15 (food demand) → `vm_dem_food` → Module 16 (aggregation into `vm_supply`) → Module 21 (trade) → production & land use.

---

## Key Configuration Parameters

### Master Switches

| Parameter | Default | Options | What It Controls | File:Line |
|-----------|---------|---------|-----------------|-----------|
| `s15_exo_diet` | `0` | 0=off, 1=EAT-Lancet v1, 2=NIN+EAT, **3=recommended** | Exogenous diet scenario | `input.gms:76` |
| `s15_exo_waste` | `0` | 0=regression waste, 1=exogenous target | Food waste scenario | `input.gms:74` |
| `s15_elastic_demand` | `0` | 0=exogenous, 1=price-responsive | Demand responds to prices | `input.gms:66` |
| `c15_food_scenario` | `SSP2` | SSP1–5, A1/A2/B1/B2 | Income/pop regression scenario | `input.gms:9` |

### EAT-Lancet Diet Settings (only active when `s15_exo_diet` > 0)

| Parameter | Default | Options | File:Line |
|-----------|---------|---------|-----------|
| `c15_kcal_scen` | `healthy_BMI` | `healthy_BMI`, `2100kcal`, `2500kcal`, `endo`, `no_underweight`, `no_overweight`, `half_overweight`, `no_underweight_half_overweight` | `input.gms:21` |
| `c15_EAT_scen` | `FLX` | `BMK`, `FLX`, `PSC`, `VEG`, `VGN`, `FLX_hmilk`, `FLX_hredmeat` | `input.gms:26` |

**Commodity sub-switches** (`input.gms:82–95`) — all default ON (1) except `s15_exo_brans` (0).
Set any to 0 to exclude that food group from the exogenous diet shift:
`s15_exo_monogastric`, `s15_exo_ruminant`, `s15_exo_fish`, `s15_exo_fruitvegnut`, `s15_exo_roots` (diet=3 only), `s15_exo_pulses`, `s15_exo_sugar`, `s15_exo_oils`, `s15_exo_brans` (⚠️ ON sets brans→0), `s15_exo_scp`, `s15_exo_alcohol` (diet=1,3 only).
Alcohol ceiling: `s15_alc_scen` (default 0 = no alcohol; 0.014 = 1.4% of kcal).

### Food Substitution Settings (independent of `s15_exo_diet`)

| Parameter | Default | What It Controls | File:Line |
|-----------|---------|-----------------|-----------|
| `s15_ruminant_substitution` | `0` | Fraction (0–1) of ruminant meat phased out | `input.gms:103` |
| `s15_fish_substitution` | `0` | Fraction of fish phased out | `input.gms:104` |
| `s15_alcohol_substitution` | `0` | Fraction of alcohol phased out | `input.gms:105` |
| `s15_livestock_substitution` | `0` | Fraction of ALL livestock phased out | `input.gms:106` |
| `s15_rumdairy_substitution` | `0` | Ruminant meat + dairy phased out | `input.gms:107` |
| `s15_rumdairy_scp_substitution` | `0` | Ruminant/dairy → SCP | `input.gms:108` |
| `s15_livescen_target` | `0` | 0/1: converge livestock to kcal cap | `input.gms:109` |
| `s15_kcal_pc_livestock_supply_target` | `430` | kcal/cap/day ceiling (if target=1) | `input.gms:98` |
| `s15_livescen_target_subst` | `1` | 0=fadeout only, 1=substitute with plants | `input.gms:99` |

### Timing & Transition Controls

| Parameter | Default | What It Controls | File:Line |
|-----------|---------|-----------------|-----------|
| `s15_food_substitution_start/target` | `2025/2050` | Substitution fader window | `input.gms:101–102` |
| `s15_food_subst_functional_form` | `1` | 1=linear, 2=sigmoid curve | `input.gms:100` |
| `s15_exo_foodscen_start/target` | `2025/2050` | Exo diet + waste fader window | `input.gms:111–112` |
| `s15_exo_foodscen_functional_form` | `1` | 1=linear, 2=sigmoid | `input.gms:110` |
| `s15_exo_foodscen_convergence` | `1` | 0–1: degree of convergence to target | `input.gms:113` |

### Food Waste & Country Targeting

| Parameter | Default | What It Controls | File:Line |
|-----------|---------|-----------------|-----------|
| `s15_exo_waste` | `0` | 0=regression waste, 1=exogenous target | `input.gms:74` |
| `s15_waste_scen` | `1.2` | Demand/intake ratio (1.0=zero waste, 1.2=20%) | `input.gms:75` |
| `scen_countries15` | all ISO countries | Which countries get exo diet/waste/substitution | `input.gms:33–58` |

---

## Common Recipes

### Recipe 1: Full EAT-Lancet Diet (recommended)
```r
cfg$gms$s15_exo_diet <- 3; cfg$gms$c15_kcal_scen <- "healthy_BMI"; cfg$gms$c15_EAT_scen <- "FLX"
```

### Recipe 2: Vegan Diet
```r
cfg$gms$s15_exo_diet <- 3; cfg$gms$c15_kcal_scen <- "healthy_BMI"; cfg$gms$c15_EAT_scen <- "VGN"
```

### Recipe 3: 50% Livestock Reduction (no EAT-Lancet)
```r
cfg$gms$s15_livestock_substitution <- 0.5  # Replaced with plant-based
```

### Recipe 4: Halve Food Waste
```r
cfg$gms$s15_exo_waste <- 1; cfg$gms$s15_waste_scen <- 1.1  # Converge to 10% waste
```

### Recipe 5: EAT-Lancet + Waste Reduction (SDP-style)
```r
cfg$gms$s15_exo_diet <- 3; cfg$gms$c15_kcal_scen <- "healthy_BMI"; cfg$gms$c15_EAT_scen <- "FLX"
cfg$gms$s15_exo_waste <- 1; cfg$gms$s15_waste_scen <- 1.2
```

### Recipe 6: Replace Ruminant/Dairy with SCP
```r
cfg$gms$s15_rumdairy_scp_substitution <- 0.5  # 50% of rum/dairy → SCP
```

### Recipe 7: Cap Livestock at 430 kcal/cap/day
```r
cfg$gms$s15_livescen_target <- 1; cfg$gms$s15_kcal_pc_livestock_supply_target <- 430
cfg$gms$s15_livescen_target_subst <- 1  # Substitute with plants
```

### Recipe 8: Diet Change in Specific Countries Only
```r
cfg$gms$s15_exo_diet <- 3; cfg$gms$c15_EAT_scen <- "FLX"
cfg$gms$scen_countries15 <- "DEU,FRA,GBR,USA"
```

---

## Step-by-Step: Setting Up a Diet Scenario

1. **Choose mechanism**: EAT-Lancet (`s15_exo_diet`=3) OR substitution scalars OR livestock cap — avoid combining EAT-Lancet with substitution (double-counts)
2. **Set diet target**: For EAT-Lancet: `c15_kcal_scen` + `c15_EAT_scen`; for substitution: set share (0–1) per food group
3. **Configure timing**: Faders default 2025→2050 linear; set `*_functional_form`=2 for sigmoid
4. **Add waste reduction** (optional): `s15_exo_waste`=1 + `s15_waste_scen` (shares same fader as exo diet)
5. **Restrict countries** (optional): edit `scen_countries15` — affects ALL three mechanisms via `p15_country_switch` (`preloop.gms:62–63`)
6. **Check feed side**: diet changes don't auto-improve feed efficiency — consider matching `c70_feed_scen`

---

## How Diet Changes Propagate Through MAgPIE

```
Module 15 (Food Demand) ── standalone NLP model, ISO-level
  ├─ Exo diet + substitution + waste applied in exodietmacro.gms (included at intersolve.gms:155)
  └─ Output: p15_kcal_pc_calibrated → q15_food_demand (equations.gms:10) → vm_dem_food(i,kfo)
       │
Module 16 ── vm_supply = vm_dem_food + vm_dem_feed + processing + material + bioen + seed + waste
       │
Module 21 (Trade) ── self-sufficiency constraints drive regional production
       │
Module 70 (Livestock) ── animal food demand → feed requirements → vm_dem_feed → back to M16
       │
Modules 10/20/30/34/35 ── production needs → cropland/pasture/forest allocation
```

---

## Common Pitfalls

1. **`s15_exo_diet` = 0 by default** — EAT-Lancet settings (`c15_EAT_scen`, `c15_kcal_scen`) have NO effect unless you set `s15_exo_diet` > 0. This is the #1 forgotten step.

2. **Substitution and EAT-Lancet are independent** — Setting `s15_ruminant_substitution = 0.5` AND `s15_exo_diet = 3` applies BOTH, which may double-count livestock reduction. Choose one mechanism or the other.

3. **Two separate fader timelines** — Substitution faders use `s15_food_substitution_start/target`. EAT-Lancet and waste faders use `s15_exo_foodscen_start/target`. Mismatching them creates unexpected phasing.

4. **`s15_exo_brans` default is 0** — Turning it ON sets brans intake to 0 (there is no EAT-Lancet target for brans). This is counterintuitive but by design (`input.gms:90`).

5. **`s15_exo_diet` = 1 is deprecated** — Use `s15_exo_diet` = 3 (MAgPIE-specific) for new work. Value 1 uses a fixed external dataset; value 3 uses `f15_rec_EATLancet` min/max bounds with the model's own intake projections (`exodietmacro.gms:441–442`).

6. **Country selection affects ALL three mechanisms** — `scen_countries15` gates exo diet, waste reduction, AND substitution via `p15_country_switch` (`preloop.gms:62–63`).

7. **Waste target is a ratio, not a percentage** — `s15_waste_scen = 1.2` means demand = 1.2 × intake (20% waste), NOT 120% waste. Setting it to 1.0 = zero waste.

8. **Feed-side not automatic** — Reducing livestock food demand does NOT automatically improve feed efficiency. Consider also setting `c70_feed_scen` to match your diet ambition (e.g., `ssp1` for efficient feeding).

---

## Module Cross-References

| Topic | Document | Key Content |
|-------|----------|-------------|
| Module 15 full reference | `magpie-agent/modules/module_15.md` | All 18 equations, 35+ scalars, modification guides |
| Module 16 demand hub | `magpie-agent/modules/module_16.md` | Supply balance equations, 8 equation details |
| Food balance law | `magpie-agent/cross_module/nitrogen_food_balance.md` | How supply ≥ demand is enforced system-wide |
| Livestock/feed system | Module 70 (`modules/70_livestock/`) | `c70_feed_scen`, SCP feed substitution |
| Predefined scenarios | `config/scenario_config.csv` | SDP, VLLO columns with preset diet settings |
| EAT-Lancet 2.0 project | `config/projects/scenario_config_el2.csv` | EL2_PHD, EL2_Demand presets |
| FSEC project scenarios | `config/projects/scenario_config_fsec.csv` | Per-commodity diet scenario columns |
| Modification safety | `magpie-agent/agent/helpers/modification_impact_analysis.md` | Risk assessment for food module changes |

---

## Lessons Learned
<!-- APPEND-ONLY: Record practical insights from real usage below this line -->
