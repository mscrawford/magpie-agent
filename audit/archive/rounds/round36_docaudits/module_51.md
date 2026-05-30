# Round 36 doc audit — module_51.md (Nitrogen, rescaled_jan21)

**Auditor**: Opus adversarial doc-auditor
**Target**: `magpie-agent/modules/module_51.md`
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree), `config/default.cfg`
**Date**: 2026-05-30

---

## Overall verdict: MOSTLY ACCURATE (lower band)

The equation block, formulas, set definitions, scalar defaults, in-module citations, execution-phase descriptions, and the carefully-worded `vm_emissions_reg` declaration claim (line 250) are all **correct and well-verified** — this is a high-quality doc on its core content. The errors are concentrated in the cross-module data-flow attribution: the source module of the consumed MACC parameter is wrong (Module 56 stated, Module 57 is correct), a direct downstream consumer (Module 57) is omitted, and the auto-generated "Participates In" section asserts a phantom direct dependency on Module 14.

3 confirmed bugs (1 Critical, 2 Major).

---

## Setup verification (all confirmed)

- Realizations present: `ls /tmp/magpie_develop_ro/modules/51_nitrogen/` → `off`, `rescaled_jan21`, `module.gms`. ✓
- Default realization: `config/default.cfg:1550` → `cfg$gms$nitrogen <- "rescaled_jan21"`. Doc lines 4, 10-11 correct. ✓
- Module 56 default `price_aug22` (cfg:1613), Module 57 default `on_aug22` (cfg:1822), Module 50 `macceff_aug22` (cfg:1479), Module 55 `ipcc2006_aug16` (cfg:1593), Module 18 `flexreg_apr16` (cfg:622), Module 59 `cellpool_jan23` (cfg:1916).

---

## Verified-correct load-bearing claims

### Equations (all 8 match code exactly)
- 8 equations, names + line ranges all correct against `equations.gms`:
  - `q51_emissions_man_crop` (22-27), `q51_emissions_inorg_fert` (30-39), `q51_emissions_resid` (42-46), `q51_emissions_resid_burn` (49-52), `q51_emissions_som` (55-59), `q51_emissionbal_awms` (65-71), `q51_emissionbal_man_past` (74-80), `q51_emissions_indirect_n2o` (83-89). ✓
- All formula transcriptions verified verbatim against `equations.gms` (manure/crop rescaling, two-pool fertilizer with separate `vm_nr_eff_pasture`, residue-burn DM × `f51_ef_resid_burn`, SOM cell→region sum, AWMS `kli×awms_conf` with `(1-sum(ct,im_maccs_mitigation(...)))`, pasture `awms_prp×kli`, indirect EF4/EF5). No fabricated formulas. ✓
- NUE-rescaling "Applied To" list (lines 388-394) matches code: rescaled for man_crop/inorg_fert/resid/som/man_past; NOT rescaled for awms (MACC instead) and resid_burn. ✓

### Interface variable producers (upstream) — all attributions correct
- `vm_manure_recycling` → M55 `ipcc2006_aug16/declarations.gms:21` (doc line 40 cites this exact path:line). ✓
- `vm_manure_confinement`, `vm_manure` → M55. ✓
- `vm_nr_eff`, `vm_nr_eff_pasture`, `vm_nr_inorg_fert_reg` → M50 `macceff_aug22/declarations.gms:10,12,13`. ✓
- `vm_res_recycling`, `vm_res_ag_burn` → M18. ✓
- `vm_nr_som` → M59. ✓
- All in-equation citations for these (`equations.gms:25,26,33,34,36,37,45,46,52,58,59,69,71,78,80`) verified by `rg -no` enumeration of M51's own files. ✓

### `vm_emissions_reg` declaration (the G2-style distinction) — correct
- Line 250: "declared by Module 56 (`price_aug22/declarations.gms:40`, dimensioned `(i, emis_source, pollutants)`, units Tg per yr)". Code line 40 verbatim: `vm_emissions_reg(i,emis_source,pollutants) ... (Tg per yr)`. Sole declarer (grep across all `declarations.gms` returns only M56). The doc correctly states M51's equations *produce values for* it rather than declaring it. ✓ Well done.

### Sets — all correct
- `emis_source_n51 = {inorg_fert, man_crop, awms, resid, resid_burn, man_past, som}` (7), sets.gms:15-16. ✓
- `emis_source_n_cropsoils51 = {inorg_fert, man_crop, resid, som, rice}`, sets.gms:18-19. ✓
- `emis_uncertainty51 = {best, low, high}` sets.gms:9-10; `ipcc_ef51` 9-member list sets.gms:12-13. ✓
- `pollutant_nh3no2_51 = {nh3_n, no2_n}` defined `56_ghg_policy/price_aug22/sets.gms:204-205` (doc line 212 attributes to "Module 56 sets.gms" — correct). ✓
- `n_pollutants_direct = {n2o_n_direct, nh3_n, no2_n, no3_n}` (4 pollutants), `price_aug22/sets.gms:199-202` — confirms the pervasive "4 pollutants" claims. ✓
- `awms_conf` 9 confinement types (lagoon…pit_long), `55_awms/ipcc2006_aug16/sets.gms:16-17` (doc line 161). ✓
- `awms_prp = {grazing, stubble_grazing}`, sets.gms:13-14 (doc line 185). ✓
- `kli = {livst_rum, livst_pig, livst_chick, livst_egg, livst_milk}` (5, fish excluded), `16_demand/sector_may15/sets.gms:21-22` — confirms "kli (5 livestock types)" (doc line 157). ✓

### Scalars / parameters / files — all correct
- `s51_snupe_base = 0.5` (input.gms:8), `s51_nue_pasture_base = 0.5` (input.gms:9). Doc lines 41, 261, 265, 73 all correct (both 0.5). ✓ (NOT in default.cfg — hard-coded scalars in input.gms; verified there directly per MANDATE 3.)
- `i51_ef_n_soil(t,i,n_pollutants_direct,emis_source_n_cropsoils51)` declared `declarations.gms:20` (doc line 279). ✓
- Input filenames: all 5 (`f51_ipcc_ef.csv`, `f51_ef3_confinement.cs4`, `f51_ef3_prp.cs4`, `f51_ef_resid_burn.cs4`, `f51_ef_n_soil_reg.cs3`) match `input/files` manifest. ✓
- `f51_ef3_prp` input.gms:31-36 exact; `f51_ef_resid_burn` 38-43 exact. (`f51_ipcc_ef` doc says 11-14, table is 11-15 incl. `;`; `f51_ef3_confinement` doc says 23-28, block is 23-29 — both trivial range-end off-by-one, content correct, NOT flagged.)

### Execution phases — all correct
- preloop.gms:8-10 (`vm_emissions_reg.fx=0`, `.lo=-Inf`, `.up=Inf`) — doc lines 330-334 exact. ✓
- presolve.gms:8-16 dynamic-EF if/else (history uses `f51_ef_n_soil`, future repeats t-1) — doc lines 281-283, 339-350 correct incl. the "2010 levels" wording (matches code comment presolve.gms:9). ✓
- postsolve.gms:10-43 R-section output recording — doc line 352 correct. ✓

### realization.gms claims — correct, and corroborate the bug below
- realization.gms:11-13 lists M51's inputs as **50, 55, 18, 59** and output as **56** only. This matches doc line 16 — and notably does NOT list Module 56 as an input source, corroborating that the MACC parameter is NOT from M56.

---

## Bugs found

### BUG 1 (Critical) — `im_maccs_mitigation` attributed to Module 56; it is Module 57 (maccs)

- **Doc lines**: 244-245, 458, 469 (three locations).
- **Claim in doc**:
  - L244-245: "**From Module 56 (GHG Policy)** (input data): `im_maccs_mitigation(t,i,"awms","n2o_n_direct")`: MACC-based mitigation fraction (0-1)".
  - L458 (Upstream Dependencies table): "**56** (GHG Policy) | `im_maccs_mitigation` | Mitigation effort for AWMS (input data, not variable)".
  - L469: "Receives nitrogen flows from 5 upstream modules (50, 18, 55, 59, **56**)".
- **Reality in code**: `im_maccs_mitigation` is declared **and** populated in **Module 57 (maccs)**, realization `on_aug22` (the default and only realization). It does NOT appear anywhere in Module 56.
- **File evidence**:
  - Declared: `modules/57_maccs/on_aug22/declarations.gms:13` — `im_maccs_mitigation(t,i,emis_source,pollutants) Technical mitigation of GHG emissions (percent)`.
  - Populated: `modules/57_maccs/on_aug22/preloop.gms:46,48,52,56,60,64`.
  - Absent from M56: `rg -ln 'im_maccs_mitigation' /tmp/magpie_develop_ro/modules/56_ghg_policy/` → exit 1 (no match); positive control `rg im_maccs_mitigation modules/57_maccs/on_aug22/*.gms` → 11 hits.
- **verify_cmd + result**:
  - `rg -n 'im_maccs_mitigation' .../56_ghg_policy/.../declarations.gms` → (no output / nothing in M56)
  - `rg -n 'im_maccs_mitigation' .../modules/*/*/declarations.gms` → only `57_maccs/on_aug22/declarations.gms:13`
  - `grep -n 'cfg.gms.maccs' config/default.cfg` → `cfg$gms$maccs <- "on_aug22"`
- **Severity rationale**: Wrong source-module for a consumed interface parameter, stated as positive fact in 3 places; Module 57 is never named anywhere in the doc. A user doing impact analysis ("what feeds Module 51's AWMS mitigation term?") or attempting to modify the MACC input is sent to the wrong module and would not find the parameter. This is the populator-set analog of the R20 Critical anchor (wrong producer/populator set) and the MANDATE 9 "wrong module attribution" failure mode. Tier: Critical (positively-false source attribution, not a mere omission).
- **bug_class**: Latent doc error / wrong module attribution (rubric class 15; MANDATE 9 / MANDATE 13 surface).
- **Proposed fix**: Replace all three "Module 56"/"56" references *for `im_maccs_mitigation`* with **Module 57 (maccs)**. Specifically:
  - L244: change header to "**From Module 57 (maccs)** (input data):".
  - L458: change table row module from "**56** (GHG Policy)" to "**57** (maccs)" with purpose "MACC-based technical mitigation fraction for AWMS N2O (`on_aug22/declarations.gms:13`)".
  - L469: change upstream-module list to "(50, 18, 55, 59, **57**)".
  - (Module 56 remains correct as the *downstream* consumer of `vm_emissions_reg` — do not remove it there.)

### BUG 2 (Major) — Module 57 (maccs) omitted as a direct downstream consumer of `vm_emissions_reg`

- **Doc lines**: 462-464 (Downstream Dependencies table), 469-470 (Critical Hub Status).
- **Claim in doc**: L463-464 table lists only "**56** (GHG Policy) | `vm_emissions_reg`"; L470: "Provides emissions to **1 downstream module (56)**".
- **Reality in code**: `vm_emissions_reg` (the variable M51 populates for its 7 nitrogen sources) is **directly read by Module 57 (maccs)** in its cost equations, including the `n2o_n_direct` slice that M51 produces. So M51's output has at least **two** direct downstream consumers: M56 (pricing) and M57 (MACC costs).
- **File evidence**:
  - `modules/57_maccs/on_aug22/equations.gms:38,48` — `... * vm_emissions_reg(i2,emis_source,pollutants_maccs57) / (1 - im_maccs_mitigation(...))` and `:40,50` reading `vm_emissions_reg(i2,emis_source_inorg_fert_n2o,"n2o_n_direct")`.
  - `pollutants_maccs57 = {ch4, n2o_n_direct}` (`57_maccs/on_aug22/sets.gms:25-26`) — i.e. M57 reads the N2O-direct emissions M51 produces.
  - M56 reads it too: `56_ghg_policy/price_aug22/equations.gms:17` (`q56_emis_pricing`). (M52/M53/M58 also reference it but as **co-populators** for their own sources, not consumers of M51's nitrogen slices.)
- **verify_cmd + result**:
  - `rg -ln 'vm_emissions_reg' modules/*/*/*.gms` → includes `57_maccs/on_aug22/equations.gms`, `56_ghg_policy/price_aug22/{equations,postsolve,declarations}.gms`, plus co-populators 52/53/58 and M51 itself.
  - `rg -n 'vm_emissions_reg' modules/57_maccs/on_aug22/equations.gms` → lines 38, 40, 48, 50 (reads, not assigns).
- **Severity rationale**: Incomplete consumer set (R20-anchor family). Misleads modification-safety reasoning: a user changing how M51 computes N2O would not expect the change to ripple into M57's MACC cost calculation. Stated as an explicit count ("1 downstream module"), so a careful reader is positively misinformed. Major (omission of a real direct consumer; M56 is correctly listed, variable name correct). tier_uncertainty: borderline Critical given the explicit "1" count — pulled to Major per tie-breaker.
- **bug_class**: Latent doc error / incomplete consumer set (rubric class 15; MANDATE 13 surface).
- **Proposed fix**:
  - L463-464: add a row "**57** (maccs) | `vm_emissions_reg` | Baseline emissions for MAC-cost integral (`on_aug22/equations.gms:38,48`)".
  - L470: change "Provides emissions to 1 downstream module (56)" to "Provides emissions (via `vm_emissions_reg`) to 2 downstream modules: **56** (GHG pricing) and **57** (MACC cost calculation)".

### BUG 3 (Major) — Phantom direct dependency on Module 14 (yields)

- **Doc line**: 742.
- **Claim in doc**: "**Depends on**: Module 50 (nr_soil_budget): Nitrogen inputs, **Module 14 (yields): Crop nitrogen content**".
- **Reality in code**: Module 51 reads **nothing** from Module 14. A full enumeration of every interface object referenced in M51's `equations.gms`/`presolve.gms`/`preloop.gms` yields only: `vm_emissions_reg`, `vm_manure_recycling`, `vm_nr_eff`, `vm_nr_inorg_fert_reg`, `vm_nr_eff_pasture`, `vm_res_recycling`, `vm_res_ag_burn`, `vm_manure_confinement`, `im_maccs_mitigation`, `vm_manure`, `vm_nr_som`, plus its own `i51_*`/`f51_*`/`s51_*`. No Module-14 variable, no "crop nitrogen content" variable. Any influence of yields on M51 is **transitive** (via M50/M17/M18), not a direct dependency.
- **File evidence**: `rg -no 'vm_[a-z_]+|im_[a-z_]+|pm_[a-z_]+' modules/51_nitrogen/rescaled_jan21/{equations,presolve,preloop}.gms | sort -u` → list above; zero Module-14-owned names.
- **verify_cmd + result**: enumeration command above run; output contained no `pm_` from M14 and no crop-N-content variable. Positive control: the same command correctly surfaced all 11 known upstream/own variables.
- **Severity rationale**: MANDATE 17 violation (direct vs transitive). Exactly the R24 Q4-B3 anchor pattern (module_30.md phantom direct consumer), which was scored Major. Lives in the auto-generated "Participates In" section (lower-stakes), but is a positively-false direct-dependency claim that misleads modification reasoning. Major.
- **bug_class**: Latent doc error / transitive-as-direct dependency (rubric class 15; MANDATE 17 surface).
- **Proposed fix**: On L742 remove "Module 14 (yields): Crop nitrogen content" from "Depends on", or relabel as transitive: "(indirectly, via Module 50)". The direct upstream set is 50, 55, 18, 59 (+ 57 for the MACC parameter — see Bug 1).

---

## Pre-run advisory — verdict

The advisory said: "Verify default realization. M51 reads vm_area (R33). Verify i51_ef_n_soil EFs and the vm_emissions/nitrogen-emission consumer/producer sets; q51_* equations."

- **Default realization**: CONFIRMED `rescaled_jan21` (cfg:1550). Doc correct.
- **"M51 reads vm_area (R33)"**: **REFUTED for Module 51.** Full enumeration of M51's files shows NO `vm_area` reference (neither `vm_area(` nor `vm_area.`). Verified: `rg 'vm_area' modules/51_nitrogen/rescaled_jan21/*.gms` → no match; positive control `rg 'vm_emissions_reg' ...` → many hits. The R33 `vm_area` near-miss concerned **Module 32** (afforestation presolve), not M51. No `vm_area` claim exists in module_51.md, so nothing to flag. (The advisory's R33 note is a generic carry-over, not applicable here.)
- **`i51_ef_n_soil` EFs**: CONFIRMED. Declared `declarations.gms:20`; updated in presolve.gms:10-16 (history `f51_ef_n_soil`, future t-1). Doc lines 279-284, 339-350 correct.
- **`vm_emissions_reg` / nitrogen-emission consumer/producer sets**: This is where the real bugs are — see Bugs 1 (wrong producer module for the consumed MACC param) and 2 (omitted M57 consumer). The PRODUCER of `vm_emissions_reg` (declarer = M56; populated by M51/52/53/58) is handled correctly by the doc (line 250). The CONSUMER set is incomplete (M57 missing).
- **`q51_*` equations**: CONFIRMED all 8 correct (names, formulas, lines).
- **grep discipline**: both grep forms used (`NAME(` via `rg -no` enumeration AND a `.`-attribute check for vm_area), positive controls run, co-located-name caveat applied (M52/M53/M58 correctly classified as co-populators not consumers of M51's slices).

---

## Deferred (not code-verifiable from develop, or judgment calls — NOT edited)

- `f51_ipcc_ef` values ef_4 = 0.01, ef_5 = 0.0075 (doc lines 208-209, 274-275): the input CSV `f51_ipcc_ef.csv` is not present in the develop worktree (only the `files` manifest ships). Values match standard IPCC 2006 EF4/EF5 and are presented as IPCC defaults; cannot confirm from code. Not flagged.
- "No feedback loops" / "Circular Dependencies: None" (lines 471, 748): M57 reads M51's `vm_emissions_reg` and M51 reads M57's `im_maccs_mitigation`, but the latter is a parameter set in preloop (not an endogenous variable), so there is no optimization-level circular dependency. realization.gms:18-19 notes MACCs are applied at NUE estimation in M50. Defensible framing; not a clear code bug.
- "Terminal calculation node" / "Centrality Rank: Low-Medium" (lines 468, 736): qualitative/architectural; slightly undercut by the M57 read (Bug 2) but a judgment call, not a discrete code-checkable error.
- "Module 11 (costs): via emissions" (line 740): explicitly labeled transitive ("via emissions") — M51 → M56 emission costs → M11 total costs. Correctly hedged; not flagged.
- Trivial range-end off-by-one on two input.gms parameter citations (`f51_ipcc_ef` 11-14 vs 11-15; `f51_ef3_confinement` 23-28 vs 23-29): content correct, within tolerance, Informational at most — not flagged.

---

## Summary

3 confirmed bugs. Core content (equations, formulas, sets, scalars, in-module citations, execution phases, the M56 `vm_emissions_reg` declaration distinction) is accurate and well-verified. All errors are in cross-module data-flow attribution: (1) **Critical** — `im_maccs_mitigation` attributed to Module 56 in 3 places; it is Module 57 (maccs, `on_aug22/declarations.gms:13`), never mentioned in the doc; (2) **Major** — Module 57 omitted as a direct downstream consumer of `vm_emissions_reg` (doc claims "1 downstream module"); (3) **Major** — phantom direct dependency on Module 14 (yields) in the auto-generated section (M51 reads nothing from M14; influence is transitive via M50). Advisory's "M51 reads vm_area" refuted (that was Module 32, R33).
