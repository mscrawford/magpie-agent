# Round 36 Adversarial Verification — module_51.md (consumer/producer/dependency-set bugs)

Ground truth: `/tmp/magpie_develop_ro` (develop worktree). Defaults confirmed active:
`cfg$gms$nitrogen=rescaled_jan21`, `cfg$gms$maccs=on_aug22`, `cfg$gms$ghg_policy=price_aug22`
(all three are the DEFAULT and the only non-`off`/`input` realization, so doc-vs-code is apples-to-apples).

All three findings are consumer/producer/dependency-SET claims → fully re-derived from code.

---

## M51-B1 — VERDICT: UPHELD  (class_is_consumer_set = true)

**Claim under test:** doc attributes `im_maccs_mitigation` to "Module 56 (GHG Policy) (input data)" at L244-245, L458, and counts it in the upstream "(50, 18, 55, 59, 56)" list at L469. Auditor says the producer is Module **57** (maccs), not 56.

**Re-derivation:**
- Declaration: `57_maccs/on_aug22/declarations.gms:13` — `im_maccs_mitigation(t,i,emis_source,pollutants)  Technical mitigation of GHG emissions (percent)`.
- Population (LHS assignment): `57_maccs/on_aug22/preloop.gms:46,48,52,56,60,64`.
- M51 (the doc's own module) READS it once: `51_nitrogen/rescaled_jan21/equations.gms:71` `(1-sum(ct, im_maccs_mitigation(ct,i2,"awms","n2o_n_direct")))`. So M51 is a consumer, not the producer — consistent with B1.
- ABSENT from Module 56: searched both forms; zero hits.

**Positive control (proves M56 dir is searchable):** `rg 'vm_emissions_reg' .../56_ghg_policy/` → 8 hits (declarations.gms:40, equations.gms:17, postsolve.gms:13/27/41/55). Search works.

**Both-form + absence check:**
```
rg -n 'im_maccs_mitigation\(' /tmp/magpie_develop_ro/modules/   # paren form
  -> 57_maccs preloop.gms:46/48/52/56/60/64; 57 declarations.gms:13;
     57 equations.gms:38/41/48/51; 50 presolve.gms:56/58/61/63;
     53 equations.gms:29/52/63; 51 equations.gms:71   (NO module 56)
rg -n 'im_maccs_mitigation' /tmp/magpie_develop_ro/modules/   # any form incl '.'
  -> same set + 51/off + 53/off not_used.txt   (still NO module 56)
rg -n 'maccs_mitigation' /tmp/magpie_develop_ro/modules/56_ghg_policy/ ; echo exit=$?
  -> (no output) exit=1   [confirmed twice: paren-form scan + this bare scan]
```
Co-located-name caveat N/A — there is no M56 line bearing the token at all.

**Conclusion:** Producer/source is Module 57, not Module 56. Apply auditor fix exactly:
L244 header → "From Module 57 (maccs) (input data):"; L458 table module 56→57 ("MACC-based technical mitigation fraction for AWMS N2O", cite `57_maccs/on_aug22/declarations.gms:13`); L469 upstream list → "(50, 18, 55, 59, 57)". Keep Module 56 as DOWNSTREAM consumer of `vm_emissions_reg` (L249/L464) — do not touch.

---

## M51-B2 — VERDICT: UPHELD  (class_is_consumer_set = true)

**Claim under test:** Downstream table (L462-464) lists only "56 | vm_emissions_reg" and Hub Status (L470) says "Provides emissions to 1 downstream module (56)". Auditor: M51's `vm_emissions_reg` slices are ALSO read by Module 57 → ≥2 direct downstream consumers.

**Re-derivation — who POPULATES vs who READS `vm_emissions_reg`:**
- M51 POPULATES (LHS `=e=`) the nitrogen slices: `51_nitrogen/rescaled_jan21/equations.gms:23,31,43,50,56,66,75` (man_crop, inorg_fert, resid, resid_burn, som, awms, man_past) + indirect n2o at :84,86,88. These are M51's output.
- M57 READS them (RHS of cost integral): `57_maccs/on_aug22/equations.gms:38,48` `... * vm_emissions_reg(i2,emis_source,pollutants_maccs57) / (1 - im_maccs_mitigation(...))` and :40,50 `vm_emissions_reg(i2,emis_source_inorg_fert_n2o,"n2o_n_direct") / s57_implicit_emis_factor`. With `pollutants_maccs57 = {ch4, n2o_n_direct}` this directly consumes M51's `n2o_n_direct` slice. Genuine consume → M57 is a 2nd downstream consumer. (Read confirmed in q57_labor_costs / q57_capital_costs, eq lines 35-53.)
- M56 READS it: `56_ghg_policy/price_aug22/equations.gms:17` `vm_emissions_reg(i2,emis_annual,pollutants)`. 1st downstream consumer (already in doc).
- M52/M53/M58 are CO-POPULATORS, not consumers of M51's slices (auditor's parenthetical confirmed):
  - M52 `52_carbon/normal_dec17/equations.gms:17` `vm_emissions_reg(i2,emis_oneoff,"co2_c") =e=` (own co2_c source).
  - M53 `53_methane/ipcc2006_aug22/equations.gms:22,49,60,71` `vm_emissions_reg(...,"ch4") =e=` (own ch4 sources).
  - M58 `58_peatland/v2/equations.gms:92` `vm_emissions_reg(i2,"peatland",poll58) =e=` (own peatland source).
  None reads an M51 nitrogen slice on a RHS → correctly excluded from M51's downstream set.

**Positive control:** same `vm_emissions_reg` rg in 56_ghg_policy dir returned 8 hits (above) → search reliable.

**Conclusion:** UPHELD. Apply auditor fix: add downstream row "57 (maccs) | vm_emissions_reg | Baseline emissions for MAC-cost integral (`57_maccs/on_aug22/equations.gms:38,48`)"; L470 → "Provides emissions (via vm_emissions_reg) to 2 downstream modules: 56 (GHG pricing) and 57 (MACC cost calculation)". One precision note recorded in corrected_set so the fixer doesn't mis-cite M57's read lines.

---

## M51-B3 — VERDICT: UPHELD  (class_is_consumer_set = true)

**Claim under test:** L742 "Depends on: Module 50 ... , Module 14 (yields): Crop nitrogen content". Auditor: M51 reads NOTHING from Module 14; yields are transitive only.

**Re-derivation — full interface enumeration across M51 equations+presolve+preloop:**
```
cat .../rescaled_jan21/{equations,presolve,preloop}.gms | grep -oE '\b(vm|pm|im)_[a-z_]+' | sort -u
-> im_maccs_mitigation, vm_emissions_reg, vm_manure, vm_manure_confinement,
   vm_manure_recycling, vm_nr_eff, vm_nr_eff_pasture, vm_nr_inorg_fert_reg,
   vm_nr_som, vm_res_ag_burn, vm_res_recycling
```
This matches the auditor's enumeration exactly. No Module-14 variable (no `vm_yld`/`pm_yld`), no "crop nitrogen content" object.

**Absence confirmed twice + positive control:**
```
grep -rc 'yld\|yield' .../rescaled_jan21/   -> every file = 0  (method 2)
rg -n '14|yld|yield|crop.?n.?content' .../{equations,presolve,preloop}.gms -> 0 hits
rg -n 'vm_nr_eff\b' .../equations.gms       -> 26,34,46  (POSITIVE CONTROL: search works)
```
Direct-vs-transitive (MANDATE 17): yields feed N flows only through M50/M17/M18, never read by M51 directly. So the L742 listing is a transitive-as-direct error.

**Conclusion:** UPHELD. Remove "Module 14 (yields): Crop nitrogen content" from L742 "Depends on" (or relabel "(indirect, via Module 50)"). Direct upstream set = 50, 55, 18, 59 (+ 57 for the MACC parameter per B1). NB: L742 also has "Module 11 (costs): via emissions" on the *Provides to* line and a phantom-ish framing, but that is outside B3's stated scope; flag only, no change proposed here.

---

### Summary
| Bug | consumer_set? | Verdict |
|-----|---------------|---------|
| M51-B1 | yes | UPHELD (producer is 57, not 56) |
| M51-B2 | yes | UPHELD (downstream consumers = 56 + 57) |
| M51-B3 | yes | UPHELD (M14 is transitive, not direct) |

No refutations. The auditor's evidence reproduced cleanly on develop under all-default realizations; every fix is safe to apply. The one nuance: B2's corrected_set pins M57's read-line citations to avoid a fixer mis-cite.
