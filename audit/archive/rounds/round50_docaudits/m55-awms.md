# Doc Audit — module_55.md (AWMS, ipcc2006_aug16)

**Auditor**: Opus adversarial doc auditor (round50 doc-audit sweep)
**Target**: `<magpie-agent>/modules/module_55.md`
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree), `config/default.cfg`
**Date**: 2026-06-06

---

## Overall Verdict: ACCURATE (one Minor stale-default finding)

module_55.md is an exceptionally well-verified document. Every load-bearing code-checkable
claim — interface variable names, equation names, equation formulas, file:line citations
within M55, the downstream consumer set (M50/M51/M53), the upstream producer (M70), set
definitions and members, realization names, the default realization, parameter defaults, and
phase citations — checks out against develop. The consumer/producer sets are precise and
include the nuanced (and correct) M53 distinction (reads `vm_manure(...,"confinement",...)`,
NOT `vm_manure_confinement`). The single code-verifiable error is a stale parenthetical year
annotation for `sm_fix_SSP2` (doc says "typically 2015"; current default is 2025).

---

## Default realization & cross-module realization checks

| Module | Config var | Default (code) | Doc | Verdict |
|---|---|---|---|---|
| 55 awms | `cfg$gms$awms` | `ipcc2006_aug16` (default.cfg:1593) | `ipcc2006_aug16` | ✓ |
| 50 nr_soil_budget | `cfg$gms$nr_soil_budget` | `macceff_aug22` (default.cfg:1479) | line numbers match macceff_aug22 | ✓ |
| 51 nitrogen | `cfg$gms$nitrogen` | `rescaled_jan21` (default.cfg:1550) | line numbers match rescaled_jan21 | ✓ |
| 53 methane | `cfg$gms$methane` | `ipcc2006_aug22` (default.cfg:1583) | line numbers match ipcc2006_aug22 | ✓ |
| 70 livestock | `cfg$gms$livestock` | `fbask_jan16` (default.cfg:2146) | `fbask_jan16` (line 243) | ✓ |

Realization dirs present: `ipcc2006_aug16`, `off` (matches doc's "Alternative `off`").

---

## Interface variable / consumer-producer set verification (MANDATEs 13, 17, 18, 20)

Grepped BOTH `name(` and `name.` forms across `modules/` and `core/`, with a positive
control (`vm_feed_intake`) to confirm the search works.

### `vm_manure` (DECLARED + POPULATED in M55 ipcc2006_aug16/declarations.gms:19, equations.gms:69)
Consumers (READ on equation RHS), complete set:
- M50 `macceff_aug22/equations.gms:28` — `vm_manure(i2,kli,"stubble_grazing","nr")` in `q50_nr_inputs` (eq at line 22)
- M50 `macceff_aug22/equations.gms:77` — `vm_manure(i2,kli,"grazing","nr")` in `q50_nr_inputs_pasture` (eq at line 74)
- M51 `rescaled_jan21/equations.gms:78` — `vm_manure(i2,kli,awms_prp,"nr")` in `q51_emissionbal_man_past` (eq at line 74)
- M53 `ipcc2006_aug22/equations.gms:50` — `vm_manure(i2,kli,"confinement","nr")` in `q53_emissionbal_ch4_awms` (eq at line 48)
No solution-level (`.l/.lo/...`) reads outside M55. No core/ consumers (positive control confirmed empty for core/). **Doc matches exactly** (lines 260, 261, 265, 270, 512, 513, 515, 517).

### `vm_manure_recycling` (DECLARED in M55 declarations.gms:21, POPULATED equations.gms:84)
Consumers:
- M50 `macceff_aug22/equations.gms:27` in `q50_nr_inputs`
- M51 `rescaled_jan21/equations.gms:25` in `q51_emissions_man_crop` (eq at line 22)
NOT M53. **Doc matches** (lines 259, 267, 511, 516). Doc never claims M53 reads it.

### `vm_manure_confinement` (DECLARED in M55 declarations.gms:22, POPULATED equations.gms:76)
Consumers:
- M51 `rescaled_jan21/equations.gms:69` in `q51_emissionbal_awms` (eq at line 65)
ONLY M51. **Doc matches** (lines 264, 514). Doc correctly states M53 does NOT use it (line 270).

### Upstream producer `vm_feed_intake`
DECLARED `modules/70_livestock/fbask_jan16/declarations.gms:18` as `vm_feed_intake(i,kap,kall)`. **Doc matches exactly** (line 243 cites this exact path:line and signature).

**Net**: phantom members = 0; omitted consumers = 0. The 3-downstream / 1-upstream summary
(line 524, 835) is correct.

---

## Equation names & formulas (all 7)

All 7 equation names match declarations.gms:27-33 and equations.gms exactly:
`q55_bal_intake_confinement` (eq 26-33), `q55_bal_intake_grazing_pasture` (37-41),
`q55_bal_intake_fuel` (44-48), `q55_bal_intake_grazing_cropland` (52-56),
`q55_bal_manure` (68-71), `q55_manure_confinement` (75-78), `q55_manure_recycling` (83-87).
Doc's cited ranges for each (lines 44, 75, 97, 119, 147, 178, 209) are correct.

Formulas reproduced faithfully (MANDATE 1):
- Confinement (doc 50-56) = code 27-33, incl. residue dev-state factor `(1-(1-sum(ct,im_development_state(ct,i2)))*0.25)`. ✓
- Grazing-pasture (doc 81-84) = code 38-40, `*(1-ic55_manure_fuel_shr(i2,kli))`. ✓
- Fuel (doc 103-106) = code 45-47, `*sum(ct,ic55_manure_fuel_shr(i2,kli))`. ✓
- Stubble (doc 125-128) = code 53-55, `*(1 - sum(ct,im_development_state(ct,i2)))*0.25`. ✓
- Manure balance (doc 153-156) = code 69-71. ✓
- Confinement distribution (doc 184-186) = code 76-77. ✓
- Recycling (doc 215-219) = code 84-87. ✓

Dev-state arithmetic (doc 67): developed `1-(1-1)*0.25=1`, developing `1-(1-0)*0.25=0.75`. ✓

---

## Sets (sets.gms)

- `awms` /grazing, stubble_grazing, fuel, confinement/ — sets.gms:10-11. ✓ (doc 343-344)
- `awms_prp(awms)` /grazing, stubble_grazing/ — sets.gms:13-14. ✓ (doc 346-347, 266)
- `awms_conf` /lagoon, liquid_slurry, solid_storage, drylot, daily_spread, digester, other, pit_short, pit_long/ — sets.gms:16-17. ✓ 9 members, exact order (doc 189-197, 349-350).
- `scen_conf55` /constant,ssp1,ssp2,ssp3,ssp4,ssp5,sdp,a1,a2,b1,b2,GoodPractice/ — sets.gms:19-20, 12 members incl. `sdp`. ✓ (doc 352-353). "12 scenarios" (doc 718) ✓.

---

## Parameters & defaults (MANDATE 3)

- `c55_scen_conf` default `ssp2` — input.gms:9. ✓ (doc 279, 282)
- `c55_scen_conf_noselect` default `ssp2` — input.gms:10. ✓ (doc 284)
- options list — input.gms:11-13 (ssp1-5, constant, a1/a2/b1/b2, GoodPractice; `sdp` not in the comment). Doc 280 faithfully mirrors the input.gms comment. ✓
- `i55_manure_recycling_share(i,kli,awms_conf,npk)` — declarations.gms:10. ✓ (doc 321). P=1, K=1 in preloop.gms:12-13; N from `f55_awms_recycling_share` preloop.gms:10. ✓ (doc 323-326)
- `ic55_manure_fuel_shr(i,kli)` — declarations.gms:11. ✓ (doc 314)
- `ic55_awms_shr(i,kli,awms_conf)` — declarations.gms:12. ✓ (doc 290)
- `p55_region_shr(t_all,i)` — declarations.gms:13. ✓
- `p55_country_switch(iso)` — declarations.gms:14. ✓ (doc 336)
- `scen_countries55(iso)` — input.gms:18-42, **249** unique ISO codes (counted). ✓ (doc 332-334 "All 249 countries")
- Input files `f55_awms_recycling_share.cs4` (input.gms:48), `f55_awms_shr.cs4` (input.gms:56). ✓ (doc 323, 328, 663, 805)

### Presolve / preloop / postsolve / nl_* line citations
- preloop: 10-13 (N at 10, P at 12, K at 13). ✓ (doc 359-364, 222-224, 232)
- presolve: country switch 11-12; region share 16; if-block 19-26; ssp2 baseline 20-21; blending 23-24; fuel scenario 25. ✓ (doc 291-293, 301, 315, 376-386)
- postsolve spans 10-55. ✓ (doc 390-392)
- nl_fix.gms / nl_release.gms / nl_relax.gms all empty (header + blank line 8). ✓ (doc 394-396)

### Purpose / methodology citations
- module.gms:10 (purpose), module.gms:11-13 (I/O: feed from 70; recycled manure to 50; GHG to 51 & 53). ✓ (doc 16)
- realization.gms:9-10 (mass balance + Bodirsky 2012), realization.gms:11-12 (IPCC 2006). ✓ (doc 18, 701, 705)

### `off` realization
preloop.gms:8-10 fix `vm_manure`, `vm_manure_recycling`, `vm_manure_confinement` to 0. ✓ (doc 655)

---

## BUG (1)

### m55-awms-B1 — `sm_fix_SSP2` stale year annotation (Minor)
- **Class**: 13 (wrong parameter default value) — hedged, parenthetical.
- **Trigger**: §1 Major "right concept, wrong number"; downgraded to Minor via tie-breaker
  (hedged with "typically"; the value is parenthetical context, not the load-bearing claim;
  not an M55-specific parameter).
- **Doc quote** (line 292): "**Historical period** (≤ `sm_fix_SSP2`, typically 2015): Fixed at SSP2 baseline".
  Also line 381: "**Historical calibration** (≤ `sm_fix_SSP2`):" with the same "2015" context implied;
  the explicit "2015" string is on **line 292 only**.
- **Reality**: `cfg$gms$sm_fix_SSP2 <- 2025` (config/default.cfg:225).
- **File evidence**: `/tmp/magpie_develop_ro/config/default.cfg:225`.
- **verify_cmd**: `grep -n "sm_fix_SSP2" /tmp/magpie_develop_ro/config/default.cfg` →
  `225:cfg$gms$sm_fix_SSP2 <- 2025`.
- **Confirmed**: true.
- **Fix**: on module_55.md line 292 replace "typically 2015" with "2025 by default".
  (Line 381 has no explicit year, so no change needed there, but the surrounding text is
  consistent with the corrected value.)

---

## Items checked and NOT flagged (deferred / not-a-bug)

- **`vm_manure` description "Manure excreted in confinements"** (doc 851): vm_manure actually
  spans all 4 awms, not just confinements, so the label is imprecise — but it is copied
  verbatim from the GAMS source comment (declarations.gms:19 "Calculation of manure excreted
  in confinements"). Doc faithfully reflects the (imprecise) source; not a doc-vs-code error.
- **`kli ⊂ kap` / feed-type sets `⊂ kall`** (doc 243, 502): structural claim consistent with
  M55's equation indexing of `vm_feed_intake(i,kap,kall)`. The `kli/kap/kall/kcr` sets are
  core auto-generated product sets (R SECTION), not located in core/sets.gms statically;
  could not pin the exact subset declaration line in-session. Internally consistent, not
  contradicted by code → deferred, no edit.
- **Doc's mixed citation convention in the Outputs section** (lines 259-270): bare
  `equations.gms:NN` = M55's own producing line (69, 76, 84 — all correct); named-equation
  citations (e.g. "q50_nr_inputs, equations.gms:28") = the consumer module's file (28, 77, 25,
  50 — all correct). Slightly inconsistent but every line number resolves correctly under the
  in-context interpretation. Not flagged.
- **`im_pop_iso(t,iso)`** doc signature (line 248) vs code `im_pop_iso(t_all,iso)` (presolve.gms:16):
  doc uses `t`; code uses `t_all`. Cosmetic index-label difference in a prose signature; the
  formula citation is correct. Not flagged (Informational at most).

---

## Mechanical checks
- M1 file:line citations present — pass (100+).
- M2 active realization stated — pass (ipcc2006_aug16 + default confirmation up top).
- M3 variable prefixes valid — pass.
- Realization names all real (`ipcc2006_aug16`, `off`).

## Summary
1 Minor bug (stale `sm_fix_SSP2` year). Consumer/producer sets, equation names/formulas,
defaults, set members, and in-module + cross-module file:line citations all verified correct
against develop. Score: 9.5/10 (essentially Accurate).
