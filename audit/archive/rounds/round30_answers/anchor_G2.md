# Anchor G2: vm_carbon_stock computation in Module 52 and entry into GHG-policy cost in Module 56

## Sources

- `modules/module_52.md` (🟡 documented)
- `modules/module_56.md` (🟡 documented)

---

## Part 1: How vm_carbon_stock is populated

`vm_carbon_stock(j,land,c_pools,stockType)` is an **interface variable declared in Module 56** (`declarations.gms:34`), not in Module 52. Module 52 reads it; the land modules write it.

### Who populates vm_carbon_stock

The variable is filled by the land modules during optimization:

| Land type | Populated by |
|-----------|-------------|
| crop (vegc, litc) | Module 29 (cropland) — which folds in `vm_carbon_stock_croparea` from Module 30 |
| past (vegc, litc, soilc) | Module 31 (Pasture) |
| plant/forestry (vegc, litc) | Module 32 (Forestry) |
| urban (all pools) | Module 34 (Urban), fixed to 0 |
| primforest, secdforest, other (vegc, litc) | Module 35 (Natural Vegetation) |
| soilc for all land types | Module 59 (SOM) |

Module 58 (Peatland) does NOT populate `vm_carbon_stock`.

(`module_52.md` Interface Variables section; `module_56.md` Section 4.1)

### What carbon densities the land modules use

The land modules derive their carbon stocks from parameters supplied by Module 52:

- `fm_carbon_density(t_all,j,land,c_pools)` — LPJmL-derived base densities for non-age-class land types, loaded from `lpj_carbon_stocks.cs3` (`module_52.md` input.gms:16-20)
- `pm_carbon_density_plantation_ac(t_all,j,ac,ag_pools)` — age-class-specific vegc+litc for plantations, computed in `start.gms:17,20`; vegc overwritten by bisection calibration in `preloop.gms:114-116` when `s52_growingstock_calib = 1`
- `pm_carbon_density_secdforest_ac(t_all,j,ac,ag_pools)` — analogous for secondary forests, `start.gms:28,31`; vegc overwritten at `preloop.gms:71-73`
- `pm_carbon_density_other_ac(t_all,j,ac,ag_pools)` — for other land, `start.gms:48,51`; not calibrated

Vegetation carbon uses the Chapman-Richards growth macro (`core/macros.gms:18`):

```
m_growth_vegc(S, A, k, m, ac) = S + (A - S) * (1 - exp(-k*(ac*5)))^m
```

Litter carbon uses a linear 20-year approach to equilibrium (`core/macros.gms:20`).

Module 56 also maintains `pcm_carbon_stock(j,land,c_pools,stockType)`, which stores the carbon stock from the **previous** timestep. Module 56 updates this at the end of each period from the solved `vm_carbon_stock`.

---

## Part 2: How vm_carbon_stock enters Module 52's CO2 equation

Module 52 has exactly one optimization equation: `q52_emis_co2_actual` (`equations.gms:16-19`).

```gams
q52_emis_co2_actual(i2,emis_oneoff) ..
  vm_emissions_reg(i2,emis_oneoff,"co2_c") =e=
    sum((cell(i2,j2), emis_land(emis_oneoff,land,c_pools)),
      (pcm_carbon_stock(j2,land,c_pools,"actual") - vm_carbon_stock(j2,land,c_pools,"actual"))
      / m_timestep_length
    );
```

- `pcm_carbon_stock` — previous-period carbon stock (mio. tC)
- `vm_carbon_stock` — current-period carbon stock (mio. tC)
- `m_timestep_length` — years in the timestep (typically 5)
- Result written to `vm_emissions_reg(i2,emis_oneoff,"co2_c")` in Tg C/yr (1 mio. tC = 1 Tg C)

A positive result means carbon was lost (the land emitted CO2); a negative result means carbon was gained (sequestration).

---

## Part 3: How vm_carbon_stock enters Module 56's GHG-policy cost

### Important architectural note: dual pathway for CO2

There are **two separate pathways** through which carbon-stock change reaches costs in Module 56:

**Pathway A — via vm_emissions_reg (indirect):** Module 52's `q52_emis_co2_actual` writes `vm_emissions_reg(i,emis_oneoff,"co2_c")`. However, this value is NOT used by Module 56's emission-pricing equations for CO2. Annual-emission pricing (`q56_emis_pricing`, `equations.gms:15-17`) routes only the `emis_annual` subset (CH4, N2O, recurring CO2), not `emis_oneoff`.

**Pathway B — via vm_carbon_stock (direct, used for CO2 pricing):** Module 56's equation `q56_emis_pricing_co2` reads `vm_carbon_stock` directly (`equations.gms:19-22`):

```gams
q56_emis_pricing_co2(i2,emis_oneoff) ..
  v56_emis_pricing(i2,emis_oneoff,"co2_c") =e=
    sum((cell(i2,j2), emis_land(emis_oneoff,land,c_pools)),
      (pcm_carbon_stock(j2,land,c_pools,"actual")
       - vm_carbon_stock(j2,land,c_pools,"%c56_carbon_stock_pricing%"))
      / m_timestep_length
    );
```

Key differences from Module 52's equation:
- The current-stock dimension uses `%c56_carbon_stock_pricing%` (a switch), not the hardcoded `"actual"`. Default is `"actualNoAcEst"`, which excludes afforestation establishment area from pricing to avoid double-counting with the CDR reward.
- This is a deliberate bypass of `vm_emissions_reg` to give Module 56 direct control over which stock type enters the LULUCF accounting.

(`module_56.md` Section 2.2, `equations.gms:19-22`)

### From emission to cost: the oneoff chain

`v56_emis_pricing(i,emis_oneoff,"co2_c")` then enters `q56_emission_cost_oneoff` (`equations.gms:45-52`):

```gams
q56_emission_cost_oneoff(i2,emis_oneoff) ..
  v56_emission_cost(i2,emis_oneoff) =e=
    sum(pollutants,
      v56_emis_pricing(i2,emis_oneoff,pollutants)
      * m_timestep_length
      * sum(ct,
          im_pollutant_prices(ct,i2,pollutants,emis_oneoff)
          * pm_interest(ct,i2)/(1+pm_interest(ct,i2))));
```

The annuity factor `r/(1+r)` converts the one-time stock-change emission to an equivalent perpetual annual cost, ensuring deforestation is penalized at the same rate as recurring emissions.

All per-source costs are aggregated by `q56_emission_costs` (`equations.gms:56-58`):

```gams
q56_emission_costs(i2) ..
  vm_emission_costs(i2) =e= sum(emis_source, v56_emission_cost(i2,emis_source));
```

`vm_emission_costs(i)` passes to Module 11 (Costs) and enters the objective function, causing MAgPIE's optimizer to internalize the carbon price signal into land-use decisions.

### Policy-matrix gate

Before any CO2 cost is incurred, `im_pollutant_prices` must be non-zero for the relevant `emis_oneoff` source. This is controlled by the emission-policy matrix (`preloop.gms:84-91`): `im_pollutant_prices` is multiplied by `f56_emis_policy(c56_emis_policy, pollutants, emis_source)`, which is 0 or 1. Under the default policy `"reddnatveg_nosoil"`, CO2 pricing covers `primforest_vegc`, `primforest_litc`, `secdforest_vegc`, `secdforest_litc`, `other_vegc`, `other_litc`, and peatland — but not soil carbon or cropland/pasture stocks.

---

## Summary of the chain

```
LPJmL data (fm_carbon_density, f52_growth_par)
  → Module 52 start.gms / preloop.gms
  → pm_carbon_density_*_ac parameters
    → Land modules 29/31/32/34/35/59 (optimization)
    → vm_carbon_stock(j,land,c_pools,"actual")     [declared in M56]

vm_carbon_stock (current period)
pcm_carbon_stock (previous period, updated by M56 postsolve)
  → q52_emis_co2_actual (M52, equations.gms:16-19)
  → vm_emissions_reg(i,emis_oneoff,"co2_c")         [used for reporting only, not CO2 pricing]

vm_carbon_stock + pcm_carbon_stock
  → q56_emis_pricing_co2 (M56, equations.gms:19-22)  [direct pathway for CO2 pricing]
  → v56_emis_pricing(i,emis_oneoff,"co2_c")
  → q56_emission_cost_oneoff (M56, equations.gms:45-52)  [× annuity factor × price]
  → v56_emission_cost(i,emis_oneoff)
  → q56_emission_costs (M56, equations.gms:56-58)
  → vm_emission_costs(i)
  → Module 11 (Costs) → objective function
```

---

## Citations

| Claim | Source |
|-------|--------|
| `vm_carbon_stock` declared in M56 | `module_52.md` Interface Variables; `module_56.md` declarations.gms:34 |
| Land-module providers of `vm_carbon_stock` | `module_52.md` Interface Variables section |
| `q52_emis_co2_actual` formula | `module_52.md` equations.gms:16-19 |
| `fm_carbon_density` loaded from LPJmL | `module_52.md` input.gms:16-20 |
| `pm_carbon_density_plantation_ac` computed | `module_52.md` start.gms:17,20 |
| `pm_carbon_density_secdforest_ac` computed | `module_52.md` start.gms:28,31 |
| Calibration overwrites vegc | `module_52.md` preloop.gms:71-73, 114-116 |
| `q56_emis_pricing_co2` formula and architectural note | `module_56.md` Section 2.2, equations.gms:19-22 |
| `q56_emission_cost_oneoff` annuity formula | `module_56.md` Section 2.4, equations.gms:45-52 |
| `q56_emission_costs` aggregation | `module_56.md` Section 2.5, equations.gms:56-58 |
| Policy matrix gate | `module_56.md` Section 3.7, preloop.gms:84-91 |
| Default policy `"reddnatveg_nosoil"` coverage | `module_56.md` Section 5.2 |
