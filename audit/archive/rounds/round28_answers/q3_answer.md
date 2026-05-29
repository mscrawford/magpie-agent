# Q3: Urban Land Representation in MAgPIE (Modules 34, 10, 52)

## Default Realization

Module 34's default realization is **`exo_nov21`**, confirmed in `config/default.cfg`:

```
cfg$gms$urban <- "exo_nov21"    # def = exo_nov21
cfg$gms$c34_urban_scenario <- "SSP2"    # def = SSP2
```

(Source: `module_34.md` Section "exo_nov21 (Default)" and `config/default.cfg` directly verified.)

---

## Exogenous vs. Endogenous

Under `exo_nov21`, urban land is **exogenous**. The trajectory of urban land area is prescribed externally from the LUH3 dataset (Hurtt et al. 2020 for LUH2v2; LUH3 publication pending as of Nov 2021) with SSP-specific scenarios (SSP1-5). MAgPIE does NOT determine how much urban land there is — it must follow the prescribed amounts.

The key mechanism is:
- **Regional totals**: A **hard equality constraint** (`q34_urban_land`, `modules/34_urban/exo_nov21/equations.gms:30-31`) forces the sum of `vm_land(j,"urban")` across all cells in a region to match the prescribed LUH3 regional total exactly.
- **Cell-level distribution**: Flexible but strongly incentivized to match cell-level prescriptions via punishment costs of 1e6 USD17MER/ha (`s34_urban_deviation_cost`, `input.gms:13`), implemented through deviation-cost equations (`q34_urban_cost1`, `q34_urban_cost2`, `q34_urban_cell` at `equations.gms:17-26`).
- **First timestep**: `vm_land.fx(j,"urban")` is fixed to `i34_urban_area(t,j)` — no optimization freedom at initialization (`presolve.gms:11`).
- **Subsequent timesteps**: `vm_land.lo(j,"urban") = 0`, `vm_land.l(j,"urban") = i34_urban_area(t,j)`, `vm_land.up(j,"urban") = Inf` — the optimizer may deviate but pays extreme penalties (`presolve.gms:12-14`).

Urban expansion is one-way: since `i34_urban_area` increases monotonically across all SSPs, urban land cannot shrink back to non-urban uses in practice (`module_34.md`, Limitation 4).

The scenario selection uses a two-stage logic: historical years (up to `sm_fix_SSP2`) always use SSP2 data for consistency; future years use the selected `c34_urban_scenario` (`preloop.gms:10-14`).

---

## How Urban Land Enters the Module 10 Land Balance

Module 10 (`landmatrix_dec18`, the only realization) is the **central land allocation hub**. It enforces the fundamental land conservation law via equation `q10_land_area` (`modules/10_land/landmatrix_dec18/equations.gms:13-15`):

```gams
q10_land_area(j2) ..
  sum(land, vm_land(j2,land)) =e=
  sum(land, pcm_land(j2,land));
```

The `land` set contains **7 mutually exclusive land types**: `crop`, `past`, `forestry`, `primforest`, `secdforest`, `urban`, `other`. Urban land participates in this sum as `vm_land(j,"urban")`.

Because total land per cell is held constant at all times, any increase in `vm_land(j,"urban")` (prescribed by Module 34) must be offset by a reduction elsewhere — in cropland, pasture, forestry, or natural vegetation. Urban land thus **directly competes** with all other land types for the fixed land budget. There is no separate constraint on which land type gives way; the optimizer determines that based on costs, yields, conservation constraints, and other module interactions.

Module 10 does NOT restrict or enforce urban land itself — it only accounts for it (`module_10.md`, Section "What Module 10 does NOT": "Does NOT Restrict Urban Land — Urban is exogenous from Module 34. Module 10 accounts for it but doesn't constrain it."). Urban expansion comes into Module 10 via the shared variable `vm_land(j,"urban")` that Module 34 writes and Module 10 includes in the land balance sum.

The transition matrix (`vm_lu_transitions(j,land_from,"urban")`, equations `q10_transition_to` and `q10_transition_from` at `equations.gms:19-25`) tracks which land types are converted to urban, enabling downstream modules (e.g., carbon, biodiversity) to correctly attribute impacts to the source land type.

---

## Urban Carbon Stock in Module 52

Module 52 (`normal_dec17`) is MAgPIE's carbon accounting hub. It handles urban carbon in two related but distinct ways:

### 1. Urban vegetation carbon (vegc) and litter carbon (litc): Fixed to zero by Module 34

Module 34 (`exo_nov21`) **fixes `vm_carbon_stock(j,"urban",ag_pools,stockType) = 0`** in its presolve phase (`presolve.gms:8`). This is a direct assignment upstream of Module 52's equations. The reason given by the docs is: "no data available on urban land carbon density" (`module_34.md`, "What Module 34 does NOT do", item 2; and "Limitation 2: Zero Urban Carbon Stocks").

This means the urban entry in `vm_carbon_stock` — the variable declared in Module 56 and populated by each land module — is held at zero for all above-ground pools by Module 34's initialization, not by a Module 52 equation.

### 2. Urban soil carbon (soilc): Temporary workaround in Module 52

Module 52 applies a **different treatment for urban soilc** in its input processing (`input.gms:33-35`): urban soil carbon (`fm_carbon_density(t_all,j,"urban","soilc")`) is set equal to the "other" land soil carbon density as a **temporary fix**, pending preprocessing improvements that would supply meaningful urban soil carbon values (`module_52.md`, Limitation "Urban soil carbon workaround"). This is explicitly flagged in docs as a workaround that may obscure urban-specific soil dynamics.

### Consequence for CO2 emissions

Module 52's sole equation, `q52_emis_co2_actual` (`equations.gms:16-19`), calculates CO2 emissions as the change in `vm_carbon_stock` between timesteps:

```gams
vm_emissions_reg(i2,emis_oneoff,"co2_c") =e=
  sum((cell(i2,j2),emis_land(emis_oneoff,land,c_pools)),
    (pcm_carbon_stock(j2,land,c_pools,"actual") - vm_carbon_stock(j2,land,c_pools,"actual"))
    / m_timestep_length
  );
```

The `emis_land` mapping includes `urban_vegc`, `urban_litc`, `urban_soilc` (docs: `core/sets.gms:314-318`). Because `vm_carbon_stock(j,"urban",vegc/litc,*)` is fixed to zero, those pools contribute zero directly to urban carbon emissions. The carbon cost of urban expansion is instead captured implicitly: when land converts to urban (e.g., forest to urban), the previous land type's carbon stock is released — `pcm_carbon_stock` of the source land type exceeds `vm_carbon_stock` in the next period, generating a positive emission.

In summary:
- Urban land carries **zero vegetation and litter carbon** in the current stock (Module 34 presolve fixation).
- Urban land soil carbon is set to "other" land soilc density as a temporary fix (Module 52 input.gms:33-35).
- Carbon emissions from land conversion **to** urban are correctly captured via the reduction in the source land type's carbon stock.
- The docs explicitly flag this as an **oversimplification**: real urban areas have parks, street trees, and green infrastructure with non-zero above-ground carbon stocks (`module_34.md`, Limitation 2; `module_52.md`, "Urban soil carbon workaround").

---

## Input Data Source Caveat

The docs explicitly note an **input data provenance uncertainty** for urban land. The `exo_nov21` realization is named for November 2021 and sources its urban area trajectory from LUH3, but:

> "LUH3 dataset not yet published (as of Nov 2021 realization date). LUH2v2 (Hurtt et al. 2020) documented; LUH3 improvements unknown ('publication not yet available' in `realization.gms:8`). Methodology changes between LUH2 and LUH3 not documented."
>
> (module_34.md, Limitation 10: LUH3 Data Vintage)

This means users relying on this realization cannot fully verify the urban data provenance or assess LUH3-specific uncertainties. The relevant input file is `f34_urbanland.cs3` (`module_34.md`, Data Flow section).

---

## Summary of Key Variables, Equations, and File:Line Citations

| Item | Identifier | File:Line |
|------|-----------|-----------|
| Default realization | `exo_nov21` | `config/default.cfg` (line confirmed) |
| Default scenario switch | `cfg$gms$c34_urban_scenario = "SSP2"` | `config/default.cfg` |
| Urban land area (optimization variable) | `vm_land(j,"urban")` | Declared in `10_land/landmatrix_dec18/declarations.gms` |
| Urban area prescribed input | `i34_urban_area(t,j)` | `34_urban/exo_nov21/preloop.gms:10-14` |
| Below-target deviation cost | `q34_urban_cost1` / `v34_cost1` | `equations.gms:17-18` |
| Above-target deviation cost | `q34_urban_cost2` / `v34_cost2` | `equations.gms:20-21` |
| Cell-level total cost | `q34_urban_cell` → `vm_cost_urban(j)` | `equations.gms:25-26` |
| Regional urban totals constraint (hard) | `q34_urban_land` | `equations.gms:30-31` |
| Biodiversity value for urban | `q34_bv_urban` → `vm_bv(j,"urban",potnatveg)` | `equations.gms:34-35` |
| Urban carbon stock fixed to zero | `vm_carbon_stock(j,"urban",ag_pools,*) = 0` | `34_urban/exo_nov21/presolve.gms:8` |
| Urban soilc workaround in M52 | `fm_carbon_density(t_all,j,"urban","soilc")` set to "other" | `52_carbon/normal_dec17/input.gms:33-35` |
| Land conservation constraint in M10 | `q10_land_area` | `10_land/landmatrix_dec18/equations.gms:13-15` |
| CO2 emission equation in M52 | `q52_emis_co2_actual` | `52_carbon/normal_dec17/equations.gms:16-19` |
| Deviation punishment cost scalar | `s34_urban_deviation_cost = 1e6 USD17MER/ha` | `34_urban/exo_nov21/input.gms:13` |

---

## Source

🟢 Verified against: `modules/module_34.md` (fully verified, 2025-10-13), `modules/module_10.md` (verified 2026-03-06), `modules/module_52.md` (verified 2026-05-16), `cross_module/land_balance_conservation.md`, and `config/default.cfg` (directly read this session).

Line numbers are as documented in module docs; verified against source code at the dates noted above. Code changes since those dates may have shifted line numbers.
