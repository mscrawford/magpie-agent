# Module 55 (awms): Animal Waste Management Systems

## Default realization

The default and only non-trivial realization is `ipcc2006_aug16`, confirmed in
`config/default.cfg` as `cfg$gms$awms <- "ipcc2006_aug16"`. The only alternative
is `off`, which zeros all AWMS variables. Everything below refers to
`ipcc2006_aug16`.

Source: `modules/module_55.md`

---

## What the module does

Module 55 is a pure accounting module — no optimization, no decision variables
beyond manure distribution. Its job is to route the nutrient (N, P, K) content of
animal manure to the correct destination, using IPCC 2006 Guidelines and the mass
balance methodology of Bodirsky et al. (2012) (`realization.gms:10-12`).

### Step 1 — Classify feed intake into four AWMS categories (equations 1-4)

The module distinguishes where animals eat and where their manure lands
(`equations.gms:13-23`):

| AWMS | Feed source | Manure destination |
|---|---|---|
| `confinement` | Concentrate, crop residues (kcr/kap/ksd/kres) | Managed in facilities |
| `grazing` | Pasture, share `(1 - ic55_manure_fuel_shr)` | Left on pasture |
| `fuel` | Pasture, share `ic55_manure_fuel_shr` | Collected as household fuel |
| `stubble_grazing` | Crop residues grazed in-field | Deposited on cropland |

Development state (`im_development_state`, 0 = developing, 1 = developed) governs
the residue split: in developed regions all residues go to confinement; in
developing regions 25 % are grazed as stubble (`equations.gms:31-32, 54-55`).

Equations:
- `q55_bal_intake_confinement` (`equations.gms:26-33`)
- `q55_bal_intake_grazing_pasture` (`equations.gms:37-41`)
- `q55_bal_intake_fuel` (`equations.gms:44-48`)
- `q55_bal_intake_grazing_cropland` (`equations.gms:52-56`)

### Step 2 — Manure excretion via mass balance (equation 5)

**`q55_bal_manure`** (`equations.gms:68-71`):

```
vm_manure(i, kli, awms, npk) = v55_feed_intake(i, kli, awms, npk)
                                * (1 - im_slaughter_feed_share(ct, i, kli, npk))
```

Nutrients not retained in animal products (meat, milk, eggs) become manure.
`im_slaughter_feed_share` is exogenous (preprocessed). This applies to all four
AWMS categories.

### Step 3 — Distribute confinement manure across 9 sub-systems (equation 6)

**`q55_manure_confinement`** (`equations.gms:75-78`):

```
vm_manure_confinement(i, kli, awms_conf, npk) =
    vm_manure(i, kli, "confinement", npk) * ic55_awms_shr(i, kli, awms_conf)
```

`awms_conf` has 9 elements (`sets.gms:16-17`): lagoon, liquid_slurry,
solid_storage, drylot, daily_spread, digester, other, pit_short, pit_long.
Shares `ic55_awms_shr` are scenario-driven (SSP1-5 / GoodPractice, controlled by
`c55_scen_conf`; default `ssp2`). They are fixed to SSP2 in the historical period
and become scenario-specific after `sm_fix_SSP2` (`presolve.gms:19-26`).

### Step 4 — Recycle confinement manure to cropland (equation 7)

**`q55_manure_recycling`** (`equations.gms:83-87`):

```
vm_manure_recycling(i, npk) =
    sum((awms_conf, kli),
        vm_manure_confinement(i, kli, awms_conf, npk)
        * i55_manure_recycling_share(i, kli, awms_conf, npk))
```

Recycling shares (`preloop.gms:10-13`):
- Nitrogen: system-specific (loaded from `f55_awms_recycling_share.cs4`); some N
  is lost during storage via volatilization, leaching, denitrification.
- Phosphorus: fixed at 1.0 (100 % recycled — simplified assumption).
- Potassium: fixed at 1.0 (100 % recycled — simplified assumption).

---

## Output to Module 50 (NR Soil Budget)

Module 55 produces one variable consumed by Module 50:

**`vm_manure_recycling(i, npk)`** — manure nutrients (Mt N/P/K) returned to
croplands from confinement systems after storage losses.

In Module 50 (`macceff_aug22`), this enters the cropland nitrogen input equation
`q50_nr_inputs` (`equations.gms:22-32`) as a direct additive term:

```gams
v50_nr_inputs(i2) =e=
    vm_res_recycling(i2,"nr")
    + ...
    + vm_manure_recycling(i2,"nr")     ← from M55 confinement recycling
    + sum(kli, vm_manure(i2, kli, "stubble_grazing","nr"))  ← also from M55
    + vm_nr_inorg_fert_reg(i2,"crop")
    + ...
```

Note that `vm_manure(i, kli, "stubble_grazing", "nr")` is also consumed by Module
50 for the cropland budget (`equations.gms:28`), and `vm_manure(i, kli, "grazing",
"nr")` enters the pasture input equation `q50_nr_inputs_pasture`
(`equations.gms:74-80`) as:

```gams
v50_nr_inputs_pasture(i2) =e=
    sum(kli, vm_manure(i2, kli, "grazing", "nr"))  ← from M55 grazing
    + vm_nr_inorg_fert_reg(i2,"past")
    + ...
```

Module 50 does not itself calculate emissions. It calculates nitrogen surplus (total
inputs minus withdrawals) and the efficiency parameters `vm_nr_eff` (cropland
SNUpE) and `vm_nr_eff_pasture` (pasture NUE), which Module 51 then uses to
back-scale emissions (`module_50.md` §6.2).

---

## Output to Module 51 (Nitrogen Emissions)

Module 55 provides two variables to Module 51 (`rescaled_jan21`):

### 1. `vm_manure_recycling(i, "nr")` — manure applied to cropland

Consumed by `q51_emissions_man_crop` (`equations.gms:22-27`):

```gams
vm_emissions_reg(i2,"man_crop",n_pollutants_direct) =e=
    vm_manure_recycling(i2,"nr")
    / (1 - s51_snupe_base) * (1 - vm_nr_eff(i2))
    * sum(ct, i51_ef_n_soil(ct,i2,n_pollutants_direct,"man_crop"))
```

The rescaling factor `(1 - vm_nr_eff) / (1 - s51_snupe_base)` adjusts IPCC
baseline emission factors (calibrated at `s51_snupe_base = 0.5`) for the actual
regional SNUpE: higher efficiency means less surplus and proportionally fewer
emissions (N₂O, NOₓ, NH₃, NO₃⁻).

### 2. `vm_manure_confinement(i, kli, awms_conf, "nr")` — confinement system manure

Consumed by `q51_emissionbal_awms` (`equations.gms:65-71`):

```gams
vm_emissions_reg(i2,"awms",n_pollutants_direct) =e=
    sum((kli, awms_conf),
        vm_manure_confinement(i2, kli, awms_conf, "nr")
        * f51_ef3_confinement(i2, kli, awms_conf, n_pollutants_direct))
    * (1 - sum(ct, im_maccs_mitigation(ct, i2, "awms", "n2o_n_direct")))
```

This uses system-specific emission factors `f51_ef3_confinement` (lagoons have
high CH₄/N₂O factors; digesters low). MACC mitigation (`im_maccs_mitigation`) is
applied. There is **no NUE rescaling** here — AWMS emissions are not tied to crop
uptake efficiency.

### 3. `vm_manure(i, kli, awms_prp, "nr")` — pasture/range/paddock manure

Consumed by `q51_emissionbal_man_past` (`equations.gms:74-80`):

```gams
vm_emissions_reg(i2,"man_past",n_pollutants_direct) =e=
    sum((awms_prp, kli),
        vm_manure(i2, kli, awms_prp, "nr")
        * f51_ef3_prp(i2, n_pollutants_direct, kli))
    / (1 - s51_nue_pasture_base) * (1 - vm_nr_eff_pasture(i2))
```

`awms_prp` = {grazing, stubble_grazing} (`sets.gms:13-14`). Pasture NUE
rescaling (`vm_nr_eff_pasture` from Module 50) is applied analogously to the
cropland rescaling.

---

## Summary of variable routing

```
Module 70 (Livestock)
  vm_feed_intake(i, kli, kall)
        |
        v
Module 55 (AWMS, ipcc2006_aug16)
  ┌─────────────────────────────────────────────────────┐
  │ Feed → 4 AWMS categories (confinement / grazing /   │
  │         fuel / stubble_grazing)                      │
  │ Mass balance → vm_manure(i, kli, awms, npk)         │
  │ Confinement → 9 sub-systems → vm_manure_confinement │
  │ Recycling fraction applied → vm_manure_recycling     │
  └─────────────────────────────────────────────────────┘
        |                    |                    |
        v                    v                    v
  Module 50             Module 51             Module 53
  (NR Soil Budget)      (Nitrogen)            (Methane)

  vm_manure_recycling   vm_manure_recycling   vm_manure_confinement
  vm_manure("stubble_   vm_manure_confinement
  grazing")             vm_manure(awms_prp)
  vm_manure("grazing")
        |
  Cropland/pasture N
  balance; drives
  vm_nr_eff →
  fed back to M51
  for emission rescaling
```

---

## Key limitations

- AWMS shares (`ic55_awms_shr`) are exogenous scenario inputs, not optimized.
  GHG pricing (Module 56) does not endogenously shift AWMS choice.
- P and K recycling shares are fixed at 1.0 (no runoff, leaching, or fixation
  losses modeled).
- No seasonal dynamics — annual averages only per 5-year timestep.
- No inter-regional manure trade; all recycled manure stays within the same
  MAgPIE region.
- `im_slaughter_feed_share` is exogenous and does not respond to endogenous
  changes in livestock productivity.

---

## Epistemic status

🟡 Based on `modules/module_55.md` (verified 2025-10-12, 100+ file:line
citations) and `modules/module_51.md` (verified 2025-10-12, 120+ file:line
citations) and `modules/module_50.md` (active realization `macceff_aug22`,
fully documented). Raw GAMS code was not re-read this session; line numbers
from the module docs may have drifted if MAgPIE code changed since the last
doc sync.
