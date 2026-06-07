# Module 55 (AWMS): Manure Nitrogen Flow Trace

**Source docs**: `modules/module_55.md` (status: Fully Verified 2025-10-12), `modules/module_51.md` (Fully Verified 2025-10-12), `modules/module_50.md` (active realization: `macceff_aug22`).
**Active realization (M55)**: `ipcc2006_aug16` (default.cfg: `cfg$gms$awms <- "ipcc2006_aug16"`).

---

## 1. Set Architecture: awms, awms_prp, awms_conf

Three distinct sets govern the AWMS slices (module_55.md §Sets, citing `sets.gms`):

| Set | Members | Nature |
|-----|---------|--------|
| `awms` | {grazing, stubble_grazing, fuel, confinement} | Full set — 4 top-level management categories |
| `awms_prp(awms)` | {grazing, stubble_grazing} | Subset of `awms` — pasture/range/paddock systems (`sets.gms:13-14`) |
| `awms_conf` | {lagoon, liquid_slurry, solid_storage, drylot, daily_spread, digester, other, pit_short, pit_long} | **Separate set** (not a subset of `awms`) — 9 confinement system types (`sets.gms:16-17`) |

Critical distinction: `awms_conf` is NOT a subset of `awms`. The two sets are parallel, not hierarchical. `vm_manure` uses `awms` as its third index; `vm_manure_confinement` uses `awms_conf` as its third index. They are different variables with different third dimensions.

---

## 2. vm_manure: Structure and Indexing

**Declaration** (module_55.md §Interface Variables, citing `declarations.gms`):

```
vm_manure(i, kli, awms, npk)   units: mio. t nutrient
```

Dimensions:
- `i` — MAgPIE region (200 clusters aggregated to ~12 world regions)
- `kli` — livestock type (subset of commodity set)
- `awms` — management system: {grazing, stubble_grazing, fuel, confinement}
- `npk` — nutrient: {nr (nitrogen), p (phosphorus), k (potassium)}

So `vm_manure` carries all four top-level AWMS slices in its third dimension. The `awms_prp` subset {grazing, stubble_grazing} and the singleton element "confinement" are both accessed by slicing this third dimension.

**Computed by**: `q55_bal_manure(i,kli,awms,npk)` (`equations.gms:68-71`):

```gams
vm_manure(i2, kli, awms, npk) =e=
v55_feed_intake(i2, kli, awms, npk)
* (1 - sum(ct, im_slaughter_feed_share(ct,i2,kli,npk)))
```

Mass balance: manure = feed nutrients - nutrients retained in animal biomass (meat, milk, eggs). The `awms` index in `vm_manure` is populated by first computing `v55_feed_intake` separately for each AWMS category via four equations (see §3).

---

## 3. The awms_conf versus awms_prp Slices

### 3a. Populating the awms_prp slice (grazing and stubble_grazing)

Two feed-intake equations compute the inputs, then `q55_bal_manure` converts to manure:

**Grazing** (`q55_bal_intake_grazing_pasture`, `equations.gms:37-41`):
```gams
v55_feed_intake(i2, kli, "grazing", npk) =e=
  vm_feed_intake(i2, kli, "pasture") * fm_attributes(npk, "pasture")
  * (1 - ic55_manure_fuel_shr(i2, kli))
```
Animals graze pasture; manure stays on pasture; `(1 - fuel_share)` ensures the fuel-collected fraction is excluded.

**Stubble_grazing** (`q55_bal_intake_grazing_cropland`, `equations.gms:52-56`):
```gams
v55_feed_intake(i2, kli, "stubble_grazing", npk) =e=
  sum(kres, vm_feed_intake(i2,kli,kres) * fm_attributes(npk,kres)
      * (1 - sum(ct, im_development_state(ct,i2))) * 0.25)
```
Animals graze crop residues on harvested fields. Only developing regions (im_development_state = 0) have 25% of residues grazed this way; developed regions contribute zero.

After `q55_bal_manure` runs, `vm_manure(i,kli,"grazing","nr")` and `vm_manure(i,kli,"stubble_grazing","nr")` hold the pasture/range/paddock manure nitrogen flows that downstream modules consume as the `awms_prp` slice.

### 3b. Populating the confinement slice

**Confinement** (`q55_bal_intake_confinement`, `equations.gms:26-33`):
```gams
v55_feed_intake(i2, kli, "confinement", npk) =e=
  sum(kcr,  vm_feed_intake(i2,kli,kcr)  * fm_attributes(npk,kcr))
  + sum(kap, vm_feed_intake(i2,kli,kap)  * fm_attributes(npk,kap))
  + sum(ksd, vm_feed_intake(i2,kli,ksd)  * fm_attributes(npk,ksd))
  + sum(kres,vm_feed_intake(i2,kli,kres) * fm_attributes(npk,kres)
        * (1 - (1-sum(ct,im_development_state(ct,i2)))*0.25))
```
Crops, animal products, seeds, and the confinement-fed portion of residues (100% in developed, 75% in developing regions).

After `q55_bal_manure`, `vm_manure(i,kli,"confinement","nr")` holds total confinement manure. This is then **further disaggregated** into the 9 confinement system types by:

**`q55_manure_confinement(i,kli,awms_conf,npk)`** (`equations.gms:75-78`):
```gams
vm_manure_confinement(i2, kli, awms_conf, npk) =e=
  vm_manure(i2, kli, "confinement", npk) * ic55_awms_shr(i2, kli, awms_conf)
```

`ic55_awms_shr` (scenario-dependent, population-weighted) distributes confinement manure across the 9 `awms_conf` types. The output variable is:

```
vm_manure_confinement(i, kli, awms_conf, npk)   units: mio. t nutrient
```

This is the variable downstream modules use for confinement-specific calculations. Note that `vm_manure(i,kli,"confinement",npk)` (the aggregate) is also read directly by Module 53 (see §5 below).

### 3c. The fuel slice

**Fuel** (`q55_bal_intake_fuel`, `equations.gms:44-48`): pasture manure × fuel_share. This slice flows into neither the soil budget nor the nitrogen emission equations for PRP — it represents manure burned as household fuel, removing those nutrients from the agricultural cycle. The module_55.md documents it as part of the AWMS accounting but does not list it in downstream consumption by M50/M51/M53.

---

## 4. Module 50 Consumption (Soil Nitrogen Budget)

Module 50's active realization is `macceff_aug22`. It reads `vm_manure` in two equations:

### q50_nr_inputs — cropland nitrogen budget (`equations.gms:22-32`)
```gams
q50_nr_inputs(i2) ..
  v50_nr_inputs(i2) =e=
    vm_res_recycling(i2,"nr")
    + ...
    + vm_manure_recycling(i2,"nr")
    + sum(kli, vm_manure(i2, kli, "stubble_grazing", "nr"))
    + vm_nr_inorg_fert_reg(i2,"crop")
    + ...
```

Two M55 variables enter the cropland budget:
- `vm_manure_recycling(i,"nr")` — confinement manure that survived storage and was recycled back to fields (computed by `q55_manure_recycling`, `equations.gms:83-87` in M55)
- `vm_manure(i2, kli, "stubble_grazing", "nr")` — direct deposition on cropland by animals grazing crop residues (`module_50.md §3.1`)

### q50_nr_inputs_pasture — pasture nitrogen budget (`equations.gms:74-80`)
```gams
q50_nr_inputs_pasture(i2) ..
  v50_nr_inputs_pasture(i2) =e=
    sum(kli, vm_manure(i2, kli, "grazing", "nr"))
    + vm_nr_inorg_fert_reg(i2,"past")
    + ...
```

- `vm_manure(i2, kli, "grazing", "nr")` — grazing manure directly deposited on pasture (`module_50.md §3.2`)

Summary: M50 reads the `awms_prp` elements of `vm_manure` directly (both "grazing" and "stubble_grazing") plus the aggregate recycling output `vm_manure_recycling`. It does NOT read `vm_manure_confinement` (the disaggregated confinement variable).

---

## 5. Module 51 Consumption (Nitrogen Emissions)

Module 51 realization `rescaled_jan21` uses three M55 variables:

### q51_emissions_man_crop — manure-on-cropland emissions (`equations.gms:22-27`)
```gams
vm_emissions_reg(i2,"man_crop",n_pollutants_direct) =e=
  vm_manure_recycling(i2,"nr")
  / (1 - s51_snupe_base) * (1 - vm_nr_eff(i2))
  * sum(ct, i51_ef_n_soil(ct,i2,n_pollutants_direct,"man_crop"))
```
Reads `vm_manure_recycling(i,"nr")` at `equations.gms:25`. NUE-rescaling applied: IPCC baseline assumes 50% NUE; actual NUE from M50 adjusts the emission intensity.

### q51_emissionbal_awms — confinement AWMS emissions (`equations.gms:65-71`)
```gams
vm_emissions_reg(i2,"awms",n_pollutants_direct) =e=
  sum((kli,awms_conf),
      vm_manure_confinement(i2,kli,awms_conf,"nr")
      * f51_ef3_confinement(i2,kli,awms_conf,n_pollutants_direct))
  * (1 - sum(ct, im_maccs_mitigation(ct,i2,"awms","n2o_n_direct")))
```
Reads `vm_manure_confinement(i,kli,awms_conf,"nr")` at `equations.gms:69`. Iterates over all 5 livestock types × 9 confinement systems. No NUE rescaling (AWMS emissions are not crop-uptake dependent). MACC mitigation from M57 is applied.

### q51_emissionbal_man_past — pasture/range/paddock emissions (`equations.gms:74-80`)
```gams
vm_emissions_reg(i2,"man_past",n_pollutants_direct) =e=
  sum((awms_prp,kli),
      vm_manure(i2, kli, awms_prp, "nr")
      * f51_ef3_prp(i2,n_pollutants_direct,kli))
  / (1 - s51_nue_pasture_base) * (1 - vm_nr_eff_pasture(i2))
```
Reads `vm_manure(i2,kli,awms_prp,"nr")` at `equations.gms:78`. `awms_prp` = {grazing, stubble_grazing} per M55 `sets.gms:13-14`. Pasture-specific NUE rescaling applied.

---

## 6. Module 53 Consumption (Methane)

Module 53 reads `vm_manure(i,kli,"confinement",npk)` — the **aggregate** confinement element of `vm_manure` — directly for AWMS CH4 calculations in `q53_emissionbal_ch4_awms` (`equations.gms:50`). It does NOT read `vm_manure_confinement` (the 9-way disaggregated variable). Enteric fermentation CH4 in M53 uses `vm_feed_intake` instead (`q53_emissionbal_ch4_ent_ferm`, `equations.gms:21-29`), not manure.

---

## 7. Complete Consumer Map

| Consumer equation | Module | Variable read | Slice/index | File:line (M51/M50) |
|---|---|---|---|---|
| `q50_nr_inputs` | M50 | `vm_manure_recycling(i,"nr")` | scalar (all confinement, post-recycling) | `equations.gms:91` |
| `q50_nr_inputs` | M50 | `vm_manure(i,kli,"stubble_grazing","nr")` | awms_prp stub slice | `equations.gms:92` |
| `q50_nr_inputs_pasture` | M50 | `vm_manure(i,kli,"grazing","nr")` | awms_prp graze slice | `equations.gms:117` |
| `q51_emissions_man_crop` | M51 | `vm_manure_recycling(i,"nr")` | scalar | `equations.gms:25` |
| `q51_emissionbal_awms` | M51 | `vm_manure_confinement(i,kli,awms_conf,"nr")` | all 9 awms_conf | `equations.gms:69` |
| `q51_emissionbal_man_past` | M51 | `vm_manure(i,kli,awms_prp,"nr")` | both awms_prp members | `equations.gms:78` |
| `q53_emissionbal_ch4_awms` | M53 | `vm_manure(i,kli,"confinement","nr")` | confinement aggregate | `equations.gms:50` |

Note: The M50 line numbers for `q50_nr_inputs` and `q50_nr_inputs_pasture` are cited from `module_50.md §3.1` and `§3.2` respectively, which reproduce the equation blocks from `modules/50_nr_soil_budget/macceff_aug22/equations.gms`. The M51 line numbers are cited verbatim from `module_51.md`.

---

## 8. Internal M55 Variable Summary

| Variable | Declaration | Computed by | Purpose |
|---|---|---|---|
| `v55_feed_intake(i,kli,awms,npk)` | M55 internal | q55_bal_intake_confinement/grazing_pasture/fuel/grazing_cropland | Feed nutrients allocated per AWMS category |
| `vm_manure(i,kli,awms,npk)` | M55 interface | `q55_bal_manure` (`equations.gms:68-71`) | Manure by AWMS category (all 4 top-level) |
| `vm_manure_confinement(i,kli,awms_conf,npk)` | M55 interface | `q55_manure_confinement` (`equations.gms:75-78`) | Confinement manure disaggregated to 9 systems |
| `vm_manure_recycling(i,npk)` | M55 interface | `q55_manure_recycling` (`equations.gms:83-87`) | Confinement manure surviving storage → cropland |

---

## Epistemic Status

All claims: 🟡 Documented — drawn from `modules/module_55.md`, `modules/module_51.md`, and `modules/module_50.md`, all verified-status docs citing specific `equations.gms` line numbers against the `ipcc2006_aug16` (M55) and `rescaled_jan21` (M51) and `macceff_aug22` (M50) realizations. No raw GAMS code was read this session. Line numbers from module docs were verified at their last update date (2025-10-12 for M55/M51); code changes since that date could shift them. For high-stakes modification work, verify against current code directly.
