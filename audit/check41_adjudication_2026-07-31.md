# Check 41 — adjudication table (2026-07-31)

**Status: FOR REVIEW. No doc was edited from this table.** These are 47 module-level
judgments about other people's modules; Mike reviews the *decisions*, not a fait
accompli. Produced by the autonomous overnight run under an explicit instruction to
emit a table rather than corrections.

**Generated after** the owner-less-vars fix landed (commit `179ddeb`), because that fix
moves the finding set. Pre-fix the numbers were 19 omission claims / 33 modules and 12
phantom claims / 18 modules; the fix removed 4 phantom claims and 8 phantom modules
outright and surfaced 4 more omission modules.

| | claims | module entries |
|---|---:|---:|
| OMISSION (higher confidence) | 19 | 37 |
| PHANTOM (lower confidence by design) | 8 | 10 |
| **total adjudications** | **27** | **47** |

## Method, and its limits

Check 41 is **definition-robust**: it reports only defects holding under all three
readings of Provides-To (D1 flow / D2 ownership / D3 blast), so the pending ruling
cannot invalidate a finding here. OMISSION means "in every definition, yet unclaimed";
PHANTOM means "in no definition, yet claimed".

Ground truth is the role map (`check_attribution_omissions.py --dump-rolemap`). I
cross-checked it with an independent probe — and **positive-controlled the probe first**
against a known edge (M14 reads `pm_climate_class`, declared in 45_climate) after an
earlier version of it silently returned "0 shared vars" for all eight phantom pairs
because it skipped the `declared_in` field, which is a string where the others are
lists. A uniform zero is the signature of a broken probe, not a finding.

**The standing limit that governs every PHANTOM row below**: the role map covers
`vm_`/`pm_`/`im_`/`fm_`/`pcm_`/`sm_` variables, **not GAMS sets**. A module that
provides only a set (M28 provides `ac` to 29/32) has no interface variable, so a real
coupling reads as a phantom. Phantoms are therefore *questions*, not defects.

---

## PHANTOM claims — 8 claims / 10 module entries

Every pair below was verified to have **no shared interface variable** in the role map.
That is necessary but not sufficient for "the doc is wrong": the coupling may be
set-based, conceptual, or routed through a third module.

> ## ⚠️ REVISED 2026-07-31 (later the same day) — **6 of the original verdicts were wrong.**
> An independent re-derivation checked every load-bearing claim against GAMS source rather
> than against the role map alone. Corrections are marked **[REVISED]** below and the
> original wording is retained beneath each so the error is visible, not silently patched.
> The biggest was P8, where my caveat pointed the wrong way.

| # | Doc | Claim | Phantom | Mechanism check | Verdict |
|---|---|---|---|---|---|
| P1 | `module_28.md:790` | downstream: 29,32,35,52 | **29, 32** | M28 declares **zero** interface vars; it provides the `ac` age-class set | **KEEP DOC — known limit 1.** Textbook set-based provision. The doc is right; the checker cannot see sets. *(unchanged, re-confirmed)* |
| P2 | `module_32.md:1391` | receives from: … | **28** | Same `ac` set coupling, other direction | **KEEP DOC — known limit 1.** *(unchanged, re-confirmed)* |
| P3 | `module_31.md:527` | provides to: 10,11,52,70 | **70** | Zero shared identifiers — but the coupling is **real and two-hop**: `31_past/endo_jun13/equations.gms:16-18` bounds `vm_prod(j2,"pasture")`; M70's feed baskets demand pasture (`70_livestock/fbask_jan16/equations.gms:26-28`) routed via M16/M17 through `vm_prod_reg`→`vm_prod` | **[REVISED] KEEP DOC, add "(via 16/17)".** Not stale — transitive. `module_31.md:531` already describes exactly this. ~~Originally "NEEDS MIKE".~~ |
| P4 | `module_31.md:529` | depends on: 10,14,70 | **70** | As P3 | **[REVISED] KEEP DOC, add "(via 16/17)".** ~~Originally "NEEDS MIKE".~~ |
| P5 | `module_34.md:320` | depends on: 09 | **09** | Default realization `exo_nov21` (`config/default.cfg:1147`); urban land is exogenous input `f34_urbanland(t_all,j,urban_scen34)` (`34_urban/exo_nov21/input.gms:16`). `c34_urban_scenario` (`:1150`) is an **independent** switch from `c09_pop_scenario` (`:211`) — nothing derives one from the other. M34 references no `im_pop`, no `im_gdp_pc_*` | **[REVISED] REWRITE THE LINE — misattributed, not merely conceptual.** The dependency on 09 is genuinely absent; the doc's own "(LUH3 scenarios)" parenthetical points at *preprocessing*, not module 09. And the line simultaneously **misses the real edge** to M10 — which is O8. Fix both together. ~~Originally "NEEDS MIKE — plausibly conceptual".~~ |
| P6 | `module_51.md:742` | provides to: 11,56 | **11** | The doc already reads "Module 11 (costs): **via emissions**". Route verified: M51 populates `vm_emissions_reg` (`51_nitrogen/rescaled_jan21/equations.gms:23`ff) → M56 computes `vm_emission_costs` (`56_ghg_policy/price_aug22/equations.gms:57`) → M11 reads it (`11_costs/default/equations.gms:26`) | **[REVISED] KEEP DOC UNCHANGED.** The doc already marks the hop; my "likely stale" was simply wrong. ~~Originally "LIKELY STALE — verify".~~ |
| P7 | `module_52.md:1206` | provides to: 11,44,56 | **11, 44** | Split, because they differ: **→11** is the same transitive route as P6 (M52 populates `vm_emissions_reg` at `equations.gms:17`) but carries **no** "via" marker. **→44** is genuinely dead — M44's entire interface is `pcm_land`, `vm_bv`, `fm_bii_coeff`, `vm_cost_bv_loss`, `sm_fix_SSP2`; a case-insensitive grep for "carbon" across `44_biodiversity/**/*.gms` returns **nothing** | **[REVISED] SPLIT: soften →11 with "(via 56)"; DELETE →44.** Lumping them hid a real defect. ~~Originally "LIKELY STALE — verify, same shape as P6".~~ |
| P8 | `module_52.md:1207` | depends on: 10,28,35 | **10** | **No role-map gap.** M52's whole `equations.gms` is 19 lines with one equation (`:16-19`) differencing `pcm_carbon_stock` against `vm_carbon_stock` — and `vm_carbon_stock` is declared in **`56_ghg_policy/price_aug22/declarations.gms:34`**, not in 52. M52 *owns and populates* the carbon densities and hands them **to** the land modules; 29/31/32/34/35/59 do the area×density multiply. **M52 never sees a hectare.** | **[REVISED] GENUINE DEFECT — apply the fix.** ~~My original caveat said the zero "may indicate a role-map gap" and "do not fix this on the strength of this row". That was backwards: the premise "carbon reads land pools via `pcm_land`" is simply false.~~ Neighbours are fine: `28` is real via `im_forest_ageclass`, `35` sits in the ambiguous band. |

---

## OMISSION claims — 19 claims / 37 module entries

Higher confidence by construction (present under *every* definition). I spot-verified 6
of the 19 against the role map; all 6 resolved to a concrete interface variable.

| # | Doc | Claim | Omitted | Verifying variable | Confidence |
|---|---|---|---|---|---|
| O1 | `module_13.md:438` | depends on: 09,10,12 | 22, 29 | `pm_avl_cropland_iso` (declared+populated 29, read 13) | **VERIFIED** |
| O2 | `module_15.md:19` | receives from: 09 | 56 | `vm_emission_costs` (declared+populated 56, read 11/15/56) | **VERIFIED** |
| O3 | `module_15.md:1539` | receives from: 09 | 56 | same as O2 — duplicate claim, same fix | **VERIFIED** |
| O4 | `module_20.md:737` | depends on: 16 | 17 | `vm_prod_reg` (declared 17, read by 20) | **VERIFIED** |
| O5 | `module_22.md:1366` | receives from: 10 | 29 | not individually verified | high |
| O6 | `module_31.md:529` | depends on: 10,14,70 | 22, 52 | not individually verified | high |
| O7 | `module_32.md:765` | provides to: 10,11,52,56,73 | 58 | not individually verified | high |
| O8 | `module_34.md:320` | depends on: 09 | 10 | not individually verified | high |
| O9 | `module_35.md:26` | receives from: 10,22,28,32,44 | 14, 52 | not individually verified | high |
| O10 | `module_35.md:966` | provides to: 10,11,22,32,52,56,73 | 59 | not individually verified | high |
| O11 | `module_36.md:577` | depends on: 09,38 | 57, 70 | **[REVISED] APPLY AS WRITTEN.** M36 genuinely reads `vm_cost_prod_livst` (M70, `70_livestock/fbask_jan16/declarations.gms:12` → `36_employment/exo_may22/equations.gms:24`) and `vm_maccs_costs` (M57, `57_maccs/on_aug22/declarations.gms:25` → same line 28) | **VERIFIED** |
| O12 | `module_36.md:1024` | receives from: 09 | ~~38, 57, 70~~ | **[WITHDRAWN — FALSE POSITIVE, and it was a CHECKER BUG.** The doc already reads "Modules 38/57/70 (labor costs)". `MODULE_LIST_RE` did not accept `/` as a list separator, so `_mod_nums` returned only `{'09'}`. **Fixed 2026-07-31** (regex + 5 regression cases incl. `tDM/ha` and path false-positive guards). `:1025` also parsed to the empty set and was never checked at all — it now enters coverage. | **NOT A DEFECT** |
| O13 | `module_52.md:1206` | provides to: 11,44,56 | 14,29,30,31,32,35,59,73 | largest single omission (8 modules) | high |
| O14 | `module_52.md:1207` | depends on: 10,28,35 | 32, 56 | not individually verified | high |
| O15 | `module_56.md:1139` | depends on: 51,52,53,58 | 09, 10, 32 | ⚠️ **DO NOT EDIT** — this line is one of the 3 findings frozen pending the Provides-To ruling | **FROZEN** |
| O16 | `module_71.md:657` | depends on: 70 | 10, 17 | not individually verified | high |
| O17 | `module_73.md:1052` | provides to: 32 | 11, 62 | not individually verified | high |
| O18 | `module_73.md:1053` | depends on: 09 | 52 | `im_vol_conv` (declared+populated 52, read 52/73) | **VERIFIED** |
| O19 | `module_80.md:1070` | depends on: 11 | 10 | `vm_landdiff` (declared+populated 10, read 10/80) | **VERIFIED** |

> ⚠️ **[RETRACTED] The O11/O12 "direction suspect" caveat was a FALSE ALARM.** I picked the
> wrong verifying variable and stopped at the first one. `pm_hourly_costs` does flow
> 36→70, but it is one of **four** shared variables, and the others run the other way:
> M36 *reads* `vm_cost_prod_livst` (M70), `vm_maccs_costs` (M57), `vm_cost_prod_crop` and
> `pm_factor_cost_shares` (M38). **The answer is BOTH directions, for all three modules** —
> which is precisely the "two-stage calculation resolves apparent circular dependency"
> that `module_36.md:1026` already states. Direction as written is correct.

---

## Recommended handling — **REVISED 2026-07-31**

1. **P1, P2 — close as KEEP DOC.** Set-based provision, the checker's documented blind
   spot. Candidates for `audit/advisory_allowlist.json` once Check 41 has a finding-level
   hook (not built — see the run's STATUS block).
2. **O1–O4, O18, O19 — safe to apply.** Verified to a named variable.
3. **O11 — apply as written.** Direction confirmed correct.
4. **O12 — withdraw.** False positive from a checker bug, now fixed.
5. **O15 — do not touch.** Frozen pending the Provides-To ruling.
6. **P8 — APPLY.** `module_52.md:1207`'s `10` is a genuine defect. *(Reversed from
   "re-derive before acting"; the doubt was misplaced.)*
7. **P3, P4, P6 — KEEP DOC**, adding a "(via …)" transitivity marker to P3/P4.
8. **P7 — split**: soften `→11` with "(via 56)", **delete `→44`**.
9. **P5 — rewrite `module_34.md:320`**, dropping 09 *and* adding 10 (O8) in one edit.

**Net after revision**: 6 verdicts changed, 1 finding withdrawn as a checker bug, and the
one row I had explicitly warned against fixing turned out to be the clearest defect in the
set. The lesson worth carrying: an intuitive-sounding mechanism ("carbon obviously reads
land") is not evidence, and I let it manufacture doubt about a correct finding.

## Provenance

Role map: `scripts/check_attribution_omissions.py --dump-rolemap`, post-fix `179ddeb`.
Findings: `scripts/check_module_set_claims.py`, run through its real entry point.
Nothing in this table was auto-applied. Nothing was pushed.
