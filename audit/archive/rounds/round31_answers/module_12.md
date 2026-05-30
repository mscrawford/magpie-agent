# Module 12 (interest_rate) — Round 31 Answer

## Default Realization

The default (and only) realization of module 12 is **`select_apr20`**, located at
`modules/12_interest_rate/select_apr20/`.

The mode switch is `c12_interest_rate`, default value `"gdp_dependent"`. A second
mode, `"coupling"`, exists for external model coupling but is not the default.

---

## How pm_interest is Determined

`pm_interest(t,i)` is a **parameter** (not a variable), computed once in the
**`preloop` phase** — there are no GAMS equations (no `=e=` / `=l=` / `=g=`
blocks) in this module.

### Formula (preloop.gms:23-26)

```
pm_interest(t,i) =
    [ (s12_interest_lic - (s12_interest_lic - s12_interest_hic) * im_development_state(t,i))
      * f12_interest_fader(t)
    + (s12_hist_interest_lic - (s12_hist_interest_lic - s12_hist_interest_hic) * im_development_state(t,i))
      * (1 - f12_interest_fader(t)) ] * p12_reg_shr(t,i)
  + [ (s12_interest_lic_noselect - ...) * ... ] * (1 - p12_reg_shr(t,i))
```

Three components drive the result:

**1. Development-state interpolation** (from Module 09)

`im_development_state(t,i)` ranges 0 (low-income) to 1 (high-income), based on
GDP per capita (PPP).

- At development state 0: interest = `s12_interest_lic` (default 0.10 = 10 %)
- At development state 1: interest = `s12_interest_hic` (default 0.04 = 4 %)
- In between: linear interpolation — richer regions pay lower rates.

**2. Time-dynamic fader** (`f12_interest_fader(t)`, read from
`modules/12_interest_rate/input/f12_interest_fader.csv`)

- Pre-2025: fader = 0 → 100 % historical rates apply
- 2025-2050: fader rises gradually
- Post-2050: fader = 1 → 100 % policy rates apply

This produces a smooth weighted average of historical rates
(`s12_hist_interest_lic/hic`) and policy rates (`s12_interest_lic/hic`).
Default values for both sets are identical (0.10 / 0.04), so with an unmodified
config the fader has no visible effect.

**3. Country selection weighting** (`p12_reg_shr(t,i)`, preloop.gms:17)

```
p12_reg_shr(t,i) = sum(i_to_iso(i,iso), p12_country_switch(iso) * im_pop_iso(t,iso))
                 / sum(i_to_iso(i,iso), im_pop_iso(t,iso))
```

Population-weighted share of "selected" countries in each region. With the
default `select_countries12` set covering all 249 ISO countries,
`p12_reg_shr = 1` everywhere and only the first branch of the formula is active.

---

## Units

`pm_interest(t,i)` is dimensionless — a **fraction per year** (e.g., 0.10 = 10 %
per year). The Interface Variables table in module_12.md labels it as "% per yr"
in prose but the GAMS unit convention is `1` (pure fraction).

---

## Modules that Consume pm_interest

The documented consumer list (updated to 9 modules in module_12.md §10, verified
2026-05-23) includes at minimum:

| Module | Role |
|---|---|
| **13 (TC — Technical Change)** | Amortizes upfront TC investment costs into annualized costs; higher rate → costlier TC → less adoption |
| **38 (Factor Costs)** | Uses pm_interest in factor cost amortization |
| **39 (Land Conversion)** | Annualizes one-time land conversion / establishment costs; higher rate → pricier expansion → less deforestation pressure |
| **41 (Irrigation)** | Annualizes irrigation infrastructure capital costs; higher rate → less irrigation investment |
| **29 (Cropland)** | Amortization of area-related capital costs |
| **32 (Forestry)** | Faustmann rotation discount |
| **56 (GHG Policy)** | CDR reward annuity discounting |
| **58 (Peatland)** | Capital cost amortization |
| **70 (Livestock)** | Investment amortization |

The three originally named in the question — 13 (TC), 38 (factor costs), 39
(land conversion) — are all confirmed consumers.

---

## Epistemic Status

- Default realization name (`select_apr20`): 🟡 Documented — read from
  `modules/module_12.md` this session (doc last verified 2025-10-13 against
  `../modules/12_*/select_apr20/*.gms`).
- Formula structure: 🟡 Documented — formula block reproduced verbatim from
  module_12.md §2A (preloop.gms:23-26 citation).
- Units: 🟡 Documented — interface table in module_12.md, with the note that
  GAMS convention uses `1` (fraction) while the prose says "% per yr".
- Consumer list (13, 38, 39, 41, and five more): 🟡 Documented — module_12.md
  §10 Summary "Provides to" note (updated 2026-05-23 R3 verification).
- Raw GAMS source was NOT read this session per task instructions.

Source: `modules/module_12.md` (magpie-agent AI documentation).
