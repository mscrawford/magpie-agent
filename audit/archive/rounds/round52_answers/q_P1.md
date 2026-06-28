## Soil CO2 carry-forward: full timestep mechanics

**Realization context**: Module 52 `normal_dec17` (default), Module 56 `price_aug22` (single realization), Module 59 `cellpool_jan23` (default) or `static_jan19`.

---

### 1. Declaration

`pcm_carbon_stock(j,land,c_pools,stockType)` is declared in **Module 56** (`modules/56_ghg_policy/price_aug22/declarations.gms`). 🟡 The `pcm_` prefix signals a cross-module previous-timestep parameter; it is not a local module variable.

---

### 2. Initialization (preloop — before optimization begins)

🟡 `pcm_carbon_stock` is initialized in **Module 56's preloop**, at `modules/56_ghg_policy/price_aug22/preloop.gms:8-11`, using:

```
pcm_carbon_stock(...) = fm_carbon_density × pcm_land
```

(cross-referenced at `module_56.md` Section 10.4 and Section 8.1). This gives the 1995 (first timestep) stock values. The first-period "emissions" from `q52_emis_co2_actual` and `q56_emis_pricing_co2` are therefore initialization artifacts, which is harmless because `im_pollutant_prices` is zeroed for all years ≤ `sm_fix_SSP2` (default 2025) at `preloop.gms:70`.

---

### 3. Carry-forward: who owns which pool

This is a **split ownership** by pool type. After each timestep's solve, the realized `vm_carbon_stock.l` is written into `pcm_carbon_stock` for the next period — but the assignment is split:

| Pool | Carry-forward owned by | File:line |
|------|----------------------|-----------|
| `ag_pools` = vegc, litc (above-ground) | **Module 56** (GHG Policy) | `modules/56_ghg_policy/price_aug22/postsolve.gms:8` |
| `soilc` (soil pool) | **Module 59** (SOM) | `modules/59_som/cellpool_jan23/postsolve.gms:13` and `modules/59_som/static_jan19/postsolve.gms:9` |

🟡 The Module 59 soil carry-forward line:
```gams
pcm_carbon_stock(j,land,"soilc",stockType) = vm_carbon_stock.l(j,land,"soilc",stockType);
```

The rationale for the split: above-ground stocks are aggregated by Module 56 from the land modules (32, 35, etc.), while soil carbon is specifically computed and owned by Module 59's IPCC dynamics equations — so Module 59 is the natural owner of that pool's carry-forward.

**Recent bug-fix note** (critical to understand the history): This soil carry-forward line was **absent from both SOM realizations until develop commit 931db85c4 (2026-06-25)**. Before the fix, `pcm_carbon_stock(...,"soilc",...)` was never updated between timesteps — it stayed at the preloop initialization value for the entire run. The soil term in both `q52_emis_co2_actual` and `q56_emis_pricing_co2` therefore computed a **cumulative-since-initialization change divided by the current timestep length**, rather than the per-timestep flux it nominally represents (roughly 17x error in a default H12 run). Default runs were unaffected because `c56_emis_policy = reddnatveg_nosoil` (the default at `config/default.cfg:1810`) excludes the soilc pool via the policy matrix.

---

### 4. How `pcm_carbon_stock(...,"soilc",...)` enters `q52_emis_co2_actual`

🟡 The single equation in Module 52 (`modules/52_carbon/normal_dec17/equations.gms:16-19`):

```gams
q52_emis_co2_actual(i2,emis_oneoff) ..
  vm_emissions_reg(i2,emis_oneoff,"co2_c") =e=
    sum((cell(i2,j2),emis_land(emis_oneoff,land,c_pools)),
      (pcm_carbon_stock(j2,land,c_pools,"actual") - vm_carbon_stock(j2,land,c_pools,"actual"))
      / m_timestep_length);
```

For the soilc pool, when `emis_land` maps `emis_oneoff` to `(land,"soilc")`, the numerator `pcm_carbon_stock(j2,land,"soilc","actual") - vm_carbon_stock(j2,land,"soilc","actual")` is the per-timestep carbon stock change (mio. tC). Division by `m_timestep_length` annualizes this to Tg C yr⁻¹. A positive value (previous > current stock) is an emission; negative is sequestration.

`vm_carbon_stock(...,"soilc","actual")` is populated by Module 59's equation `q59_carbon_soil` (`modules/59_som/cellpool_jan23/equations.gms:61-64`): topsoil pool (`v59_som_pool`) plus static subsoil (`vm_land × i59_subsoilc_density`).

---

### 5. How soilc enters CO2 pricing in Module 56

🟡 There is a **deliberate architectural bypass** here. CO2 emissions from land-use change enter the pricing system NOT through `vm_emissions_reg` (the channel used for CH4, N2O, and other annual gases), but through a **parallel direct-stock calculation** in Module 56 itself.

**Equation `q56_emis_pricing_co2`** (`modules/56_ghg_policy/price_aug22/equations.gms:19-22`):

```gams
q56_emis_pricing_co2(i2,emis_oneoff) ..
  v56_emis_pricing(i2,emis_oneoff,"co2_c") =e=
    sum((cell(i2,j2),emis_land(emis_oneoff,land,c_pools)),
      (pcm_carbon_stock(j2,land,c_pools,"actual")
       - vm_carbon_stock(j2,land,c_pools,"%c56_carbon_stock_pricing%"))
      / m_timestep_length);
```

This mirrors the `q52_emis_co2_actual` formula but with the configurable switch `c56_carbon_stock_pricing` on the right-hand (current) stock — default `"actualNoAcEst"`, which excludes afforestation establishment from pricing to avoid double-counting with the CDR reward. This pricing equation reads `pcm_carbon_stock` directly from its previous-timestep state (carried forward by Module 59 for soilc, Module 56 for ag_pools) and by Module 56 for the above-ground pools.

The `v56_emis_pricing` intermediate variable then feeds into `q56_emission_cost_oneoff` (`equations.gms:45-52`), which applies the annuity factor `m_timestep_length × price × r/(1+r)` to convert the annualized stock-change flux into a one-off cost entering the objective function via `vm_emission_costs` → Module 11.

**Whether soilc actually gets priced** depends on `c56_emis_policy`. Under the default `"reddnatveg_nosoil"`, the policy matrix (`f56_emis_policy`) zeros `im_pollutant_prices` for soil sources (`crop_soilc`, `past_soilc`, `secdforest_soilc`, etc.), so soilc contributes zero cost regardless of the stock change. Soil pricing is activated by policies like `"all"` or `"sdp_all"`.

---

### 6. Contrast: soil vs. above-ground carry-forward

| Dimension | Above-ground pools (vegc, litc) | Soil pool (soilc) |
|-----------|--------------------------------|-------------------|
| **Module that owns postsolve carry-forward** | Module 56 (`price_aug22/postsolve.gms:8`) | Module 59 (`cellpool_jan23/postsolve.gms:13`; `static_jan19/postsolve.gms:9`) |
| **Physical source of `vm_carbon_stock`** | Land modules (35 for natveg, 32 for forestry, 29/31 for crop/past), using age-class Chapman-Richards densities from Module 52 | Module 59's `q59_carbon_soil`, using IPCC 2019 stock-change factors + 15%-annual convergence |
| **Age-class specificity** | Yes — `pm_carbon_density_secdforest_ac(t,j,ac,"vegc/litc")` from Module 52 start.gms/preloop.gms | No — soilc has no age-class growth function in Module 52; soil is driven by land-use transition matrix and convergence toward equilibrium in Module 59 |
| **Carry-forward present before 2026-06-25?** | Yes (Module 56 postsolve:8 was always present) | No — absent from both SOM realizations until commit 931db85c4; soilc was frozen at preloop initialization |

The above-ground pools are carried by Module 56 because Module 56 is the hub that declares `pcm_carbon_stock` and aggregates carbon stocks from all land modules. The soil pool is carried by Module 59 because Module 59 is the exclusive calculator of `vm_carbon_stock(...,"soilc",...)` — no other module writes to that pool index.

---

### Source statement

🟡 Based on AI documentation (verified at last sync):
- `module_52.md` — Module 52 (`normal_dec17`), all sections; equations verified against source at `equations.gms:16-19`
- `module_56.md` — Module 56 (`price_aug22`), Sections 2.2, 4.1, 8.1, 10.4
- `module_59.md` — Module 59 (`cellpool_jan23`), Sections 3.4 and the carry-forward note with the 2026-06-25 bug-fix annotation

Line numbers for `pcm_carbon_stock` initialization (`preloop.gms:8-11`) and the preloop cost-zeroing (`preloop.gms:70`) are from Module 56 docs last verified 2025-10-12. The Module 59 carry-forward lines (`:13` and `:9`) reflect the 2026-06-25 patch noted in both module_52.md (Interface Variables section, line 431) and module_59.md (Section 3.4 carry-forward note). For any work directly modifying either carry-forward, verify current line numbers against source as they may have shifted since last doc sync.
