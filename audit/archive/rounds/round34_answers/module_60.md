# Module 60 (Bioenergy): Demand Setting, vm_dem_bioen, and Key Equations

## Default Realization

`1st2ndgen_priced_feb24` — confirmed in `config/default.cfg`: `cfg$gms$bioenergy <- "1st2ndgen_priced_feb24"`.
The alternative `1stgen_priced_dec18` supports only first-generation bioenergy pricing and is not the default.

Source: module_60.md line 12-13.

---

## How Bioenergy Demand Is Set

Module 60 uses **exogenous scenario trajectories** loaded from input data files; it does NOT derive bioenergy demand endogenously from energy prices, land costs, or climate policy within the optimization. Three demand streams are specified independently and then combined:

1. **1st generation (oils, ethanol — set `k1st60`)**: Fixed minimum trajectories from `f60_1stgen_bioenergy_dem(t,i,scen1st60,kall)` (mio. GJ/yr), selected via switch `c60_1stgen_biodem` (default: `const2020`). Trajectories extend to 2050 only; demand is assumed to be zero post-2050.

2. **2nd generation dedicated (bioenergy grasses/trees — set `kbe60 = {betr, begr}`)**: Selected from 88+ scenarios via `c60_2ndgen_biodem` (default: `"R34M410-SSP2-NPi2025"`) from `f60_bioenergy_dem(t,i,scen2nd60)` (mio. GJ/yr). A special `"coupling"` mode reads from an external file; `"emulator"` reads a global total and divides equally by region; `"none"` sets zero demand.

3. **2nd generation residues (set `kres`)**: From `f60_res_2ndgenBE_dem(t,i,scen2ndres60)` (mio. GJ/yr), selected via `c60_res_2ndgenBE_dem` (default: `ssp2`). Estimated as approximately 33% of cropland-recyclable residues.

All scenarios are harmonized to the SSP2-NPi baseline until `sm_fix_SSP2` (typically 2020-2025) regardless of the user's scenario switch (presolve.gms:16-28).

A minimum demand floor `s60_2ndgen_bioenergy_dem_min = 1 mio. GJ/yr` is enforced per region to prevent numerical degeneracy (presolve.gms:64).

---

## vm_dem_bioen: Role, Unit, and Consumer Set

**Declaration**: `vm_dem_bioen(i,kall)` (declarations.gms:20)

**Unit**: mio. tDM per yr (million tonnes of dry matter per year, mass units)

**Dimensions**:
- `i`: MAgPIE regions
- `kall`: All products — but only bioenergy-relevant subsets carry non-zero values: oils, ethanol (`k1st60`), betr, begr (`kbe60`), and crop residues (`kres`). All livestock products (`kap`) are fixed to zero via `vm_dem_bioen.fx(i,kap) = 0` in presolve.gms:8-10.

**Role**: `vm_dem_bioen` is the bridge variable between Module 60 and the rest of the demand system. It is expressed in mass units (tDM), not energy units. The conversion to energy (GJ) happens inside `q60_bioenergy` by multiplying by `fm_attributes("ge",kall)` (GJ per tDM).

**Consumers** (modules that read vm_dem_bioen):
- **Module 16 (Demand)**: aggregates `vm_dem_bioen` with food, feed, material, and seed demands to construct total commodity demand (module.gms:11).
- **Module 11 (Costs)**: indirectly, via `vm_bioenergy_utility(i)` which is computed in `q60_bioenergy_incentive` using `vm_dem_bioen * fm_attributes("ge",kall) * (-subsidy)` (module.gms:15-16).

---

## Key Equations (5 total)

### q60_bioenergy (equations.gms:16-21)
**Total bioenergy demand constraint** — the core equation. Converts mass-based demand to energy and ensures it meets the sum of all three demand streams:

```
vm_dem_bioen(i2,kall) * fm_attributes("ge",kall) =g=
    sum(ct, i60_1stgen_bioenergy_dem(ct,i2,kall))
    + v60_2ndgen_bioenergy_dem_dedicated(i2,kall)
    + v60_2ndgen_bioenergy_dem_residues(i2,kall)
```

Type: inequality (>=). Units: mio. GJ/yr throughout.

### q60_bioenergy_glo (equations.gms:43-44)
**Global 2nd generation dedicated demand** — active only when `c60_biodem_level = 0`. Allows the model to freely distribute bioenergy production across regions to minimize cost. Inactive under the default configuration (`c60_biodem_level = 1`).

### q60_bioenergy_reg (equations.gms:46-47)
**Regional 2nd generation dedicated demand** — active when `c60_biodem_level = 1` (the default). Each region must meet its local 2nd generation dedicated demand target; no cross-regional substitution is permitted.

```
sum(kbe60, v60_2ndgen_bioenergy_dem_dedicated(i2,kbe60)) =g=
    sum(ct, i60_bioenergy_dem(ct,i2)) * c60_biodem_level
```

### q60_res_2ndgenBE (equations.gms:61-64)
**Regional residue demand** — always regional (no global analog). Constrains the sum of residue-type demands to meet the scenario-specific residue target:

```
sum(kres, v60_2ndgen_bioenergy_dem_residues(i2,kres)) =g=
    sum(ct, i60_res_2ndgenBE_dem(ct,i2))
```

### q60_bioenergy_incentive (equations.gms:73-75)
**Bioenergy utility / subsidy** — calculates `vm_bioenergy_utility(i)` (mio. USD17MER/yr, negative value = benefit) passed to Module 11 (Costs):

```
vm_bioenergy_utility(i2) =e=
    sum((ct,k1st60), vm_dem_bioen(i2,k1st60) * fm_attributes("ge",k1st60)
        * (-i60_1stgen_bioenergy_subsidy(ct)))
    + sum((ct,kbe60), vm_dem_bioen(i2,kbe60) * fm_attributes("ge",kbe60)
        * (-i60_2ndgen_bioenergy_subsidy(ct)))
```

Default subsidy values: 1st gen = 6.5 USD17MER/GJ (constant floor); 2nd gen = 0 unless `s60_bioenergy_2nd_price > 0`. The negative sign makes this enter the objective as a production incentive beyond minimum demand.

---

## Source

- 🟡 Based on module_60.md (magpie-agent/modules/module_60.md), Status: Fully Verified, Last Verified: 2025-10-13 against `../modules/60_*/1st2ndgen_priced_feb24/*.gms`.
- Documentation freshness not independently checked this session; line numbers may have drifted if MAgPIE has had commits since 2025-10-13.
