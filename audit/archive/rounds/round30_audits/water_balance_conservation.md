# Audit Report: Round 30 — Water Balance Conservation (default water realization)

**Question**: How does MAgPIE balance water supply and demand in the default water realization? Name the equation and variables, equality vs inequality, which sectoral demands enter.

**Answer source**: anchored on `cross_module/water_balance_conservation.md` + `modules/module_42.md`.

**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree), `config/default.cfg`.

---

### Overall Verdict: ACCURATE
### Accuracy Score: 10/10

`raw_severity_weighted = 4*0 + 2*0 + 1*0 + 0*1 = 0` → `score = max(0, 10 - 0) = 10`.

---

### Verified Claims (correct)

| # | Answer claim | Code evidence | Status |
|---|---|---|---|
| 1 | Default M42 realization = `all_sectors_aug13` | `config/default.cfg:1319` `cfg$gms$water_demand <- "all_sectors_aug13"` | ✅ |
| 2 | Default M43 realization = `total_water_aug13` | `config/default.cfg:1406` `cfg$gms$water_availability <- "total_water_aug13"` | ✅ |
| 3 | Equation `q43_water`, operator `=l=`, at `equations.gms:10-11` | `modules/43_water_availability/total_water_aug13/equations.gms:10-11` — verbatim match incl. `sum(wat_dem,vm_watdem(...)) =l= sum(wat_src,v43_watavail(...))` | ✅ |
| 4 | LHS `vm_watdem(wat_dem,j)`, RHS `v43_watavail(wat_src,j)` | same line; declarations confirm both | ✅ |
| 5 | `wat_dem` = 5 sectors (agriculture, manufacturing, electricity, domestic, ecosystem) | `core/sets.gms:247` `wat_dem ... / agriculture, domestic, manufacturing, electricity, ecosystem /` | ✅ |
| 6 | `wat_src` = surface, ground, ren_ground, technical | `core/sets.gms:244` `wat_src ... / surface, ground, technical, ren_ground /` | ✅ |
| 7 | Agricultural eq `q42_water_demand` at `equations.gms:10-14` (verbatim formula) | `modules/42_water_demand/all_sectors_aug13/equations.gms:10-14` — exact match | ✅ |
| 8 | `v42_irrig_eff` converts net→gross; default time-invariant 1995-GDP sigmoidal | `presolve.gms:12-22`: `m_year(t)<=sm_fix_SSP2` → 1995-GDP sigmoid (l.13); default `s42_irrig_eff_scenario=2` → same 1995-GDP sigmoid (l.17-18) | ✅ |
| 9 | Crop irrigation = irrigated area (M30) × per-ha req; livestock = M17 prod × per-ton req | `vm_area(j,kcr,w)` declared `30_croparea/{detail,simple}_apr24/declarations.gms`; `vm_prod` declared `17_production/flexreg_apr16/declarations.gms` | ✅ |
| 10 | Manuf/elec/domestic exogenous, `.fx` to WATERGAP SSP, default SSP2 | `presolve.gms:40-54`; `s42_watdem_nonagr_scenario = 2` (`input.gms:9`, with `2: SSP2`) | ✅ |
| 11 | `watdem_ineldo` = manufacturing + electricity + domestic | `all_sectors_aug13/sets.gms:12-13` `/ domestic, manufacturing, electricity /` | ✅ |
| 12 | Ecosystem `.fx` (EFP) at `presolve.gms:87-88`; default `s42_env_flow_scenario = 2` (Smakhtin LPJmL) | `presolve.gms:87-88` exact; `input.gms:22` `/ 2 /` with `2: ...Smakhtin 2004` | ✅ |
| 13 | Default `c42_env_flow_policy = "off"`; only 5% base protection applies | `input.gms:122` `$setglobal c42_env_flow_policy off`; base = `s42_env_flow_base_fraction = 0.05` (`input.gms:37`) | ✅ |
| 14 | RHS sums 4 sources but only surface non-zero; ground/ren_ground/technical zeroed in `preloop.gms` | `preloop.gms:8` surface = `f43_wat_avail`; `:10-12` other three = 0 | ✅ |
| 15 | `v43_watavail` fixed via `.fx` (declared variable for marginals, not parameter) | `presolve.gms:8-11` `.fx` assignments; declaration comment confirms intent (`declarations.gms`) | ✅ |
| 16 | Buffer at `presolve.gms:14-16`: shortfall × 1.01, `watdem_exo` only, agriculture excluded | `presolve.gms:14-16` exact; `watdem_exo` = {domestic, manufacturing, electricity, ecosystem} (`sets.gms:9-10`), excludes agriculture | ✅ |
| 17 | `s42_pumping` default OFF (answer implies via "pumping cost ... enters objective" but cites it conditionally) | `input.gms:39` `s42_pumping ... / 0 /` — answer did not claim it active by default | ✅ |
| 18 | Per-cell (~200 clusters), no inter-cell trading | `q43_water(j2)` is cell-indexed; no transfer term | ✅ |

**Mechanical checks**: M1 ✅ (full-path file:line citations present); M2 ✅ (states both realizations + that they are default); M3 ✅ (all prefixes valid: `vm_`, `v43_`, `v42_`); M4 ✅ (🟡 badge); M5 ✅ (🟡 documented, both docs cited, explicit "raw GAMS not read per task constraint"); M6 ✅ (closing source statement present).

---

### Bugs Found

**Bug ID**: Q30-B1
- **Severity**: Informational
- **Class**: (not a Bug_Taxonomy pattern — unit-label divergence)
- **Trigger**: §1 Informational — wrong detail, careful reader not misled into action
- **Claim in answer**: "`vm_water_cost(i)` | region | Pumping cost for irrigation (USD17MER/yr)"
- **Reality in code**: `modules/42_water_demand/all_sectors_aug13/declarations.gms:31`: `vm_water_cost(i) Cost of irrigation water (USD17MER per m^3)`. The declaration comment labels it "per m^3".
- **Adjudication**: This is a genuine divergence from the nominal source-of-truth (the declaration comment), but the answer's "/yr" is the *dimensionally correct* reading of the variable: the equation `q42_water_cost` (`equations.gms:16-17`) computes `vm_water_cost(i2) =e= sum(cell, vm_watdem("agriculture",j2)) * ic42_pumping_cost(i2)` = [mio m³/yr] × [USD/m³] = USD/yr total cost. The declaration comment "per m^3" appears to describe the cost *rate* (`ic42_pumping_cost`), not the variable it labels. So the answer reasoned correctly about dimension rather than confabulating. Additionally `s42_pumping = 0` by default, so this variable is identically zero in default runs. Tie-breaker (Minor vs Informational) → Informational.
- **Root cause**: `answerer_style_or_framing` (defensible reinterpretation of a likely-mislabeled code comment; no harm).
- **tier_uncertainty**: false

No Critical, Major, or Minor bugs.

---

### Latent Doc Bugs (rubric §1.5 — fixed regardless of answer score)

**Latent-1** — `cross_module/water_balance_conservation.md:55`
- **Doc claim**: "**Irrigation efficiency**: Accounts for conveyance losses (66% default)"
- **Code reality**: The 66% value is `s42_irrigation_efficiency = 0.66` (`modules/42_water_demand/all_sectors_aug13/input.gms:19`), which is applied **only** under non-default `s42_irrig_eff_scenario = 1` (`presolve.gms:15-16`). The **default** is `s42_irrig_eff_scenario = 2` (`input.gms:14` `/ 2 /`), a GDP-based sigmoidal function `1/(1+e^((-22160-im_gdp_pc_mer(y1995))/37767))` (`presolve.gms:17-18`) — NOT a flat 66%.
- **Severity (future-reader harm)**: Minor→Major. A reader trusting "66% default" would mis-state the default irrigation-efficiency mechanism (flat static value vs. region-specific GDP-sigmoidal), and would cite the wrong scenario switch. It is a single-parameter default mischaracterization, not cascading across variables/equations, so it sits at the Minor/Major boundary; per tie-breaker, **Minor**.
- **Why latent / answer beat it**: The answer did NOT repeat "66%". It correctly wrote: "under the default scenario 2 it is time-invariant, based on 1995 GDP via a sigmoidal function (approximately 64-90%)". The answerer re-derived the default from code/M42 doc rather than trusting line 55. This is the exact §1.5 pattern (answer correct, doc wrong) — record and fix regardless of the 10/10 answer score.
- **Root cause**: `doc_error_answerer_beat_it`
- **Suggested fix**: change line 55 to "Irrigation efficiency: accounts for conveyance losses. Default (`s42_irrig_eff_scenario = 2`) is a region-specific GDP-based sigmoidal function (~64-90%); a flat 66% (`s42_irrigation_efficiency = 0.66`) applies only under non-default scenario 1." (Note: the doc is internally inconsistent — line 347 already gives the correct "~64% to ~90%" GDP range, so line 55's "66% default" is the stale/wrong instance.)

---

### Missing Nuances (not bugs)

1. The answer says the EFP "full ramp (2025-2040) is active only when EFP is switched on." Verified: `s42_efp_startyear = 2025`, `s42_efp_targetyear = 2040` (`input.gms:35-36`), and the ramp magnitude is gated by `c42_env_flow_policy` (default `off`). Accurate; no nuance missing.
2. The answer's "approximately 64-90%" efficiency range is doc-sourced (it matches doc line 347) and labeled approximate; not independently re-derivable without GDP input data, but correctly hedged.
3. The doc itself contains illustrative numeric examples explicitly labeled "Made-up numbers for illustration" — the answer correctly did not present any of these as real data.

---

### Summary

A near-flawless answer. Every load-bearing claim verified verbatim against develop: equation name `q43_water`, `=l=` operator, both core equations (`q43_water`, `q42_water_demand`) reproduced exactly, all defaults (`all_sectors_aug13`, `total_water_aug13`, `s42_env_flow_scenario=2`, `c42_env_flow_policy=off`, `s42_watdem_nonagr_scenario=2`/SSP2, `s42_pumping=0`), set memberships (`wat_dem` 5, `wat_src` 4, `watdem_exo` 4, `watdem_ineldo` 3), all file:line citations, supply-side zeroing, and the infeasibility-buffer logic. Variable prefixes and cross-module attributions (`vm_area`→M30, `vm_prod`→M17, `vm_water_cost`→enters M11 costs) all correct.

The single answer-level flag (`vm_water_cost` unit "/yr" vs declaration's "per m^3") is Informational — the answer's dimension is arguably the correct reading of a mislabeled declaration comment, and the variable is zero by default. **Score 10/10.**

One latent doc bug recorded (`doc_error_answerer_beat_it`, Minor): line 55's "66% default" mischaracterizes the default irrigation-efficiency mechanism (default is GDP-sigmoidal scenario 2, not flat 66%). The answer correctly avoided it; the doc is internally inconsistent (line 347 has the right range) and should be fixed this session regardless of the answer's perfect score — this is precisely the G2-style blind spot §1.5 was added to close.
