# Audit Report: module_51.md (Nitrogen — rescaled_jan21)

**Auditor**: Opus adversarial doc-auditor (round50_docaudits)
**Target doc**: `/Users/turnip/Documents/Work/Workspace/magpie/magpie-agent/modules/module_51.md`
**Ground truth**: `/tmp/magpie_develop_ro/modules/51_nitrogen/rescaled_jan21/` (develop worktree)
**Default verified**: `cfg$gms$nitrogen <- "rescaled_jan21"` at `config/default.cfg:1550`

## Overall Verdict: MOSTLY ACCURATE
## Accuracy Score: 8/10

This is a high-quality, heavily-cited doc. All 8 equation names, all variable names, all set definitions/members, all scalar defaults, all input filenames, and the overwhelming majority of file:line citations verified correct against develop. One Major producer-attribution error (a variable listed as coming "From Module 50" that is actually declared+populated by Module 55), plus a small cluster of trivial off-by-one/off-by-two range-closing line citations (Minor/Informational).

---

## Verified Claims (correct)

### Realizations & default
- Realization dirs: `off`, `rescaled_jan21` (`ls /tmp/magpie_develop_ro/modules/51_nitrogen/` confirms). ✓
- Default `rescaled_jan21` confirmed `config/default.cfg:1550`. ✓
- `off` realization fixes emissions to zero (`off/preloop.gms:8: vm_emissions_reg.fx(i,emis_source,n_pollutants) = 0`). Doc lines 592-594 accurate. ✓

### Equations (all 8 names + line ranges)
declarations.gms:9-16 lists exactly 8 equations, matching the doc's 8. Line ranges in equations.gms all verified:
- `q51_emissions_man_crop` (eq.gms:22-27) ✓
- `q51_emissions_inorg_fert` (eq.gms:30-39) ✓
- `q51_emissions_resid` (eq.gms:42-46) ✓
- `q51_emissions_resid_burn` (eq.gms:49-52) ✓
- `q51_emissions_som` (eq.gms:55-59) ✓
- `q51_emissionbal_awms` (eq.gms:65-71) ✓
- `q51_emissionbal_man_past` (eq.gms:74-80) ✓
- `q51_emissions_indirect_n2o` (eq.gms:83-89) ✓

Formulas in the doc match the GAMS source verbatim (man_crop, inorg_fert two-pool, resid, resid_burn DM-based, som cell-to-region sum, awms MACC, man_past, indirect ef_4/ef_5). ✓

### Variable producers/declarations (DECLARED vs POPULATED vs READ)
- `vm_emissions_reg` DECLARED in M56 `price_aug22/declarations.gms:40` (doc line 250 cites 40). ✓ POPULATED by M51 (own N sources), M52 (co2_c), M53 (ch4), M58 (peatland). READ by M56 (eq.gms:17 pricing) and M57 (eq.gms:38,48 MACC cost). Doc correctly lists ONLY M56+M57 as downstream consumers (52/53/58 are co-populators, NOT consumers of M51's output) — no phantom, no omission.
- `im_maccs_mitigation` DECLARED M57 `on_aug22/declarations.gms:13` (doc line 458 cites 13). ✓
- `vm_nr_eff`, `vm_nr_eff_pasture`, `vm_nr_inorg_fert_reg` DECLARED M50 `macceff_aug22/declarations.gms:12,13,10`. ✓
- `vm_manure_confinement` (M55 decl:22), `vm_manure` (M55 decl:19) — doc Module-55 attribution correct. ✓
- `vm_res_recycling`, `vm_res_ag_burn` DECLARED M18. ✓ `vm_nr_som` DECLARED M59. ✓

### Sets (members + line cites)
- `emis_uncertainty51` {best,low,high} sets.gms:9-10 ✓
- `ipcc_ef51` 9 members {frac_gasf,frac_gasm,frac_leach,frac_leach_h,ef_1,ef_1fr,ef_2,ef_4,ef_5} sets.gms:12-13 ✓
- `emis_source_n51` 7 members {inorg_fert,man_crop,awms,resid,resid_burn,man_past,som} sets.gms:15-16 ✓
- `emis_source_n_cropsoils51` {inorg_fert,man_crop,resid,som,rice} sets.gms:18-19 ✓
- `n_pollutants_direct` {n2o_n_direct,nh3_n,no2_n,no3_n} M56 sets.gms:199-202 (4 pollutants) ✓
- `pollutant_nh3no2_51` {nh3_n,no2_n} M56 sets.gms:204-205 ✓
- `awms_conf` 9 members (lagoon...pit_long) M55 sets.gms:16-17 ✓
- `awms_prp` {grazing,stubble_grazing} M55 sets.gms:13-14 ✓
- `kli` 5 members {livst_rum,livst_pig,livst_chick,livst_egg,livst_milk} (16_demand/sector_may15/sets.gms:21-22) — doc's "5 livestock types" correct. ✓

### Scalars
- `s51_snupe_base` = 0.5, input.gms:8 ✓
- `s51_nue_pasture_base` = 0.5, input.gms:9 ✓
(Both verified directly in input.gms; not in config/default.cfg — they are realization-internal scalars, no override needed.)

### Phases
- preloop.gms:8-10 (fx=0, lo=-Inf, up=Inf) all three lines verified. ✓
- presolve.gms:8-16 (dynamic historical eq.gms:11-12, future eq.gms:14-15, rationale 8-9) all verified. ✓
- postsolve.gms:10-43 output definitions verified. ✓

### Input filenames
All 5 confirmed against input.gms + input/files manifest: f51_ipcc_ef.csv, f51_ef_n_soil_reg.cs3, f51_ef3_confinement.cs4, f51_ef3_prp.cs4, f51_ef_resid_burn.cs4. ✓

### Interface-variable section
M51 declares no vm_/pm_/im_ (`rg "^\s*(vm_|pm_|im_)" declarations.gms` → none). Doc line 720 correct. ✓

---

## Bugs Found

### Bug m51-nremis-B1 (Major) — producer mis-attribution: vm_manure_recycling listed "From Module 50"
- **Severity**: Major (tie-breaker pulled down from Critical; the correct attribution appears twice elsewhere in the same doc, and M50 IS a legitimate co-reader, so a careful reader recovers; but the Data-Flow Inputs section sends a reader to the wrong source module for provenance).
- **Class**: 15 (latent doc error / producer attribution) — MANDATE 18 (DECLARED-vs-POPULATED-vs-READ).
- **Trigger**: §1 Major "wrong variable ... semantic scope wrong" / producer-set wrong (R20/R33-R37 vein).
- **Doc line**: module_51.md:229 (under header "**From Module 50 (NR Soil Budget)**" at line 226).
- **Claim in doc**: "**From Module 50 (NR Soil Budget)**: ... `vm_manure_recycling(i,\"nr\")`: Manure nitrogen recycled to cropland (Mt N) (`equations.gms:25`)"
- **Reality in code**: `vm_manure_recycling` is DECLARED in Module 55 (`modules/55_awms/ipcc2006_aug16/declarations.gms:21`) and POPULATED (LHS) in Module 55 (`modules/55_awms/ipcc2006_aug16/equations.gms:84: vm_manure_recycling(i2,npk) =e=`). Module 50 only READS it on an RHS (`modules/50_nr_soil_budget/macceff_aug22/equations.gms:27`), exactly as Module 51 does (`rescaled_jan21/equations.gms:25`). So the source is Module 55, not Module 50.
- **File evidence**: `modules/55_awms/ipcc2006_aug16/declarations.gms:21` (declared); `modules/55_awms/ipcc2006_aug16/equations.gms:84` (populated); `modules/50_nr_soil_budget/macceff_aug22/equations.gms:27` (M50 only reads).
- **verify_cmd**: `grep -rn "vm_manure_recycling" /tmp/magpie_develop_ro/modules/*/*/declarations.gms` → only 55_awms (ipcc2006_aug16:21, off:11). `grep -rn "vm_manure_recycling" /tmp/magpie_develop_ro/modules/*/*/equations.gms` → 51_nitrogen/rescaled_jan21:25 (RHS), 50_nr_soil_budget/macceff_aug22:27 (RHS, prefixed by `+`), 55_awms/ipcc2006_aug16:84 (LHS `=e=`).
- **Internal inconsistency note**: The SAME doc gets this right in two other places — equation-1 component note line 40 ("declared by Module 55 AWMS"), and Critical Interfaces upstream table line 455 (lists `vm_manure_recycling` under Module 55). Only the Data-Flow Inputs section (line 229) misfiles it under Module 50.
- **Confirmed**: true.
- **Proposed fix**: Move the `vm_manure_recycling` bullet out of the "From Module 50" block into the "From Module 55 (AWMS)" block. Concretely: delete the line at module_51.md:229 (`- \`vm_manure_recycling(i,"nr")\`: Manure nitrogen recycled to cropland (Mt N) (\`equations.gms:25\`)`) from the Module-50 list, and add it to the "**From Module 55 (AWMS)**" list (currently lines 237-239) as: `- \`vm_manure_recycling(i,"nr")\`: Manure nitrogen recycled to cropland (Mt N) (\`equations.gms:25\`)`. This makes the Inputs section consistent with line 40 and line 455.

### Bug m51-nremis-B2 (Minor) — off-by-one citation for n2o_n_indirect set member
- **Severity**: Minor (off-by-one line cite; adjacent content within the same set block; reader not misled into action).
- **Class**: 10 (stale/imprecise file:line citation).
- **Trigger**: §1 Minor "off-by-few line citation where adjacent lines say similar things".
- **Doc line**: module_51.md:253.
- **Claim in doc**: "Indirect: n2o_n_indirect (calculated in equation 8) (Module 56 sets.gms,196)"
- **Reality in code**: `n2o_n_indirect` appears at M56 `price_aug22/sets.gms:195` (within the `n_pollutants` set, lines 194-197) and at line 190 (within `pollutants`). Line 196 is `nh3_n, no2_n,`. The cited 196 is one line past the member.
- **File evidence**: `modules/56_ghg_policy/price_aug22/sets.gms:195` (`n2o_n_direct,n2o_n_indirect,`).
- **verify_cmd**: `sed -n '188,205p'` equivalent via Read of price_aug22/sets.gms → line 195 holds `n2o_n_indirect`, line 196 holds `nh3_n, no2_n,`.
- **Confirmed**: true.
- **Proposed fix**: change "(Module 56 sets.gms,196)" → "(Module 56 sets.gms:195)". (Low priority; could also be left, since the "Module 56 sets.gms" pointer without exact line is the doc's loose convention here.)

---

## Minor / Informational (grouped — not individually load-bearing)

These are trivial range-closing drifts where the START line of every citation is correct (the load-bearing parameter/table declaration), and only the END of the cited range overshoots/undershoots by 1-2 lines onto the `;` / delimiter line. A careful reader is not misled. Recorded for completeness, NOT proposed as edits unless a sweep is being done:

- module_51.md:271 cites `f51_ipcc_ef` at `input.gms:11-14`; the table block is input.gms:11-15 (`;` on 15). Off-by-one on the closing line.
- module_51.md:286 cites `f51_ef3_confinement` at `input.gms:23-28`; actual 23-29. Off-by-one.
- (module_51.md:292 `f51_ef3_prp` input.gms:31-36 — exact ✓; module_51.md:298 `f51_ef_resid_burn` input.gms:38-43 — exact ✓.)

Severity: Informational (start lines correct; metadata-grade range drift).

---

## Deferred (cannot verify against committed code / not code-checkable)

- **ef_4 = 0.01, ef_5 = 0.0075 numeric values** (doc lines 208-209, 274-275, 429-430): the input data CSV `f51_ipcc_ef.csv` is NOT committed in this worktree (only `input/files` manifest present; CSV absent). The values are standard IPCC-2006 EF4/EF5 and almost certainly correct, but cannot be confirmed against code here. NOT flagged as a bug.
- **f51_ef3_confinement "Based on IPCC 2006 Chapter 10 ... and Chapter 11"** (doc line 288): provenance prose; the doc lists Ch.10/Ch.11 with specific titles. The chapter-title attribution mirrors realization.gms references but the exact chapter numbering per EF table is not in the committed `.gms`/`.cs4`. Not code-checkable; not flagged.
- **"off disables nitrogen surplus accounting"** (doc line 11): loosely worded — the `off` realization disables nitrogen EMISSION calculations (fixes `vm_emissions_reg` N sources to 0); nitrogen SURPLUS is Module 50's domain. This is a metadata/wording imprecision in the front-matter callout, arguably Informational, but it is a paraphrase judgment rather than a hard code contradiction, so deferred rather than flagged as a bug.
- **IPCC uncertainty ranges (±50%, ±100%, ±30%, ±40%)** (doc lines 611-614): cited "from IPCC 2006", not from MAgPIE code. Not code-checkable.

---

## Summary

Strong, well-cited doc. Equations, variable/equation names, sets, scalars, input filenames, phases, and ~all file:line cites verified correct against develop. One Major producer mis-attribution: `vm_manure_recycling` is listed in the Data-Flow Inputs section as coming "From Module 50" but it is declared+populated by Module 55 (M50 merely co-reads it) — notably the doc gets this RIGHT in two other locations (line 40 and the Critical Interfaces table line 455), so it's a localized inconsistency. One Minor off-by-one set-member citation (n2o_n_indirect, sets.gms:195 vs cited 196), plus a couple of Informational range-closing drifts on input.gms parameter blocks. No invented names, no wrong realization, no inverted defaults, no phantom/omitted consumers.
