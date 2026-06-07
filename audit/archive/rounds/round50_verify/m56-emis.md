# Adversarial verification — module_56.md (round 50, m56-emis batch)

Ground truth: `/tmp/magpie_develop_ro` (develop worktree). Defaults from `config/default.cfg`:
ghg_policy=`price_aug22` (1613), food=`anthro_iso_jun22` (410), maccs=`on_aug22` (1822),
forestry=`dynamic_may24` (976), natveg=`pot_forest_may24` (1135). **All cited realizations ARE the defaults.**

Method: for each bug, mechanical citation check (test -f / wc -l / read exact line), then class-specific
adjudication. Consumer/producer claims re-derived with BOTH `NAME(` and `NAME.` greps + positive control.

## Shared mechanical facts
| Fact | Source | Result |
|------|--------|--------|
| scen56 member count | price_aug22/sets.gms:120-163 | **44** |
| ghgscen56 (price scen) member count | price_aug22/sets.gms:16-117 | **102** |
| pollutants_all member count | price_aug22/sets.gms:172-185 | **16** |
| emis_source member count | core/sets.gms:303-312 | **31** |
| f56_emis_policy table index | price_aug22/input.gms:113 | `(scen56,pollutants_all,emis_source)` |
| im_pollutant_prices declaration | price_aug22/declarations.gms:9 | DECLARED in M56 |
| vm_emission_costs declaration | price_aug22/declarations.gms:39 | DECLARED in M56 |

---

## m56-emis-01 — UPHELD (core) but proposed_fix CORRECTED (it injects a new wrong number)
Class: realization_structure (set-member count). Citation_ok: TRUE.

- `test -f sets.gms` -> EXISTS; `wc -l` = 214 (lines 119-163 in range). scen56 (lines 120-163) count = **44**. Matches.
- `f56_emis_policy(scen56,...)` (input.gms:113) confirms "policy scenarios" == scen56 == 44.

Core claim (60+ policy scenarios/policies -> **44**) is verified.

**BUT** proposed_fix line 797 = "44 policies x 101 scenarios ~ 4400 combinations". The price-scenario set
`ghgscen56` (sets.gms:16-117) = **102** members, NOT 101. "101" is an unverified/wrong number the auditor added to a
side-clause; the price count is not a flagged bug and the doc's other lines use "100+" (correct: 102>=100+). Fixer
must NOT write "101". M56 input dir holds no "160 data files" set either.

corrected_set: line 37 (Range col) "44 policies"; line 494 "44 policies x 16 pollutants x 31 emission sources"
(== m56-emis-05); line 636 "100+ price scenarios and 44 policy scenarios"; line 797 "44 policies x 100+ scenarios"
(drop "6000 combinations from 160 data files" and the invented "101"); line 1063 "100+ price scenarios x 44 policy
scenarios".

---

## m56-emis-02 — UPHELD
Class: consumer_set. Citation_ok: TRUE.
- `test -f 57_maccs/on_aug22/preloop.gms` -> EXISTS; wc -l=110 (24-25 in range).
- L24 `i57_mac_step_n2o(...) = min(201, ceil(im_pollutant_prices(t,i,"n2o_n_direct",emis_source)/298*28/44*44/12 / s57_step_length)+1);`
- L25 `i57_mac_step_ch4(...) = ... im_pollutant_prices(t,i,"ch4",emis_source)/25*44/12 ...` -> M57 reads it to set MACC steps.

Full re-derivation: `rg 'im_pollutant_prices\(' modules/` -> M56 (decl/preloop/equations = producer) + **M57 on_aug22/preloop.gms**
(only cross-module consumer). `rg 'im_pollutant_prices\.'` -> NONE. Set complete; M57 is the sole omitted consumer.
Declaration: declarations.gms:9 (DECLARED in M56). Doc framing "M56-internal, no consumer" was wrong.

---

## m56-emis-03 — NOT_REVIEWABLE (other) — fix VALUE confirmed
Class: other (value/illustration). Citation_ok: TRUE.
- preloop.gms:81-82 = `... s56_limit_ch4_n2o_price*12/44*265*44/28` (exact match).
- 4920*12/44*265*44/28 = **558,771.4** -> 558,771. Doc:833 says $499,320 (WRONG); doc:1109 says 558,771 (contradiction).
- Auditor fix -> $558,771/Tg N matches code + doc:1109. Pass unchanged.

---

## m56-emis-04 — NOT_REVIEWABLE (other) — fix VALUE confirmed
Class: other (value/illustration). Citation_ok: TRUE.
- preloop.gms:80 = `...,"ch4",...)$(... > s56_limit_ch4_n2o_price*12/44*28) = s56_limit_ch4_n2o_price*12/44*28;` (exact match).
- 4920*12/44*28 = **37,570.9** -> 37,571. Doc:832 says $37,709 (WRONG); doc:1109 says 37,571 (contradiction).
- Auditor fix -> $37,571/Tg CH4 matches code + doc:1109. Pass unchanged.

---

## m56-emis-05 — UPHELD
Class: realization_structure (set-member counts). Citation_ok: TRUE.
- pollutants_all (sets.gms:172-185) count = **16** (co2_c..so2). Doc says 15 -> 16 correct.
- emis_source (core/sets.gms:303-312) count = **31**. Doc says "20+" -> 31 correct.
- Table index: input.gms:113 `f56_emis_policy(scen56,pollutants_all,emis_source)`.
- Fix "44 policies x 16 pollutants x 31 emission sources" fully verified (consistent with m56-emis-01 line-494 sub-fix).

---

## m56-emis-06 — UPHELD
Class: producer_declaration (which module PRODUCES vm_cdr_aff). Citation_ok: TRUE.
- 32_forestry/dynamic_may24/equations.gms:37 `vm_cdr_aff(j2,ac,"bgc") =e=` (q32_cdr_aff LHS); :42 `vm_cdr_aff(j2,ac,"bph") =e=`
  (q32_bgp_aff LHS). M32 POPULATES it. Exact match.

Adversarial full re-derivation (both forms):
- `rg 'vm_cdr_aff\(' modules/` -> M32 declarations.gms:83 (DECLARED) + equations.gms:37,42 (POPULATED) + **M56**
  equations.gms:77 (CONSUMED in reward). No M35.
- `rg 'vm_cdr_aff\.' modules/` -> only M32 postsolve (.m/.l/.up/.lo). No M35.
- `rg 'vm_cdr_aff' modules/35_natveg/` -> ABSENT (both forms).
- POSITIVE CONTROL: `rg 'vm_carbon_stock' modules/35_natveg/` -> present (pot_forest_may24/equations.gms) — grep works there.
- => M35 does NOT produce vm_cdr_aff; CDR reward driven by vm_cdr_aff = M32 only; M35 carbon priced via vm_carbon_stock
  CO2 stock-change. Auditor correction is correct.

---

## m56-emis-07 — NOT_REVIEWABLE (other: prose/mechanism) — auditor reading confirmed
Class: other. Citation_ok: TRUE.
- preloop.gms:70 = `im_pollutant_prices(t_all,i,pollutants,emis_source)$(m_year(t_all) <= sm_fix_SSP2) = 0;` -> zeroes the
  PRICE, not emissions. Doc:757 "emissions ... zeroed via preloop.gms:70" mis-describes mechanism.
- preloop.gms:8-11: comment "emissions in 1995 are not meaningful" + 1995 stock = estimate. Supports auditor rewrite.
  Both cited lines (70 and 8-11) exist and match. Pass fix to fixer.

---

## m56-emis-08 — UPHELD
Class: consumer_set (solution-level read). Citation_ok: TRUE.
- `test -f 15_food/anthro_iso_jun22/intersolve.gms` -> EXISTS; wc -l=162 (23 in range).
- L23 `p15_tax_recycling(t,iso) = sum(i_to_iso(i,iso), (vm_emission_costs.l(i) / im_pop(t,i)) * s15_tax_recycling ...`
  -> M15 reads vm_emission_costs.l (GHG-tax recycling).

Full re-derivation (both forms):
- `rg 'vm_emission_costs\(' modules/` -> M11 costs/default/equations.gms (objective, documented) + M56 decl/equations (producer).
- `rg 'vm_emission_costs\.' modules/` -> M56 postsolve + M56 scaling + **M15 anthro_iso_jun22/intersolve.gms:23 (.l)** +
  M15 scaling.gms:22 (.scale).
- => Two real cross-module consumers: M11 (objective) + **M15 (tax recycling)**. Doc lists only M11. Omission confirmed.
  Default food realization = anthro_iso_jun22 (default.cfg:410) -> live. This is the `.l` read a `vm_emission_costs(` grep misses (R33 class).

---

### Summary
- UPHELD: m56-emis-02, -05, -06, -08.
- UPHELD core / proposed_fix CORRECTED: m56-emis-01 (44 policy scenarios right; "101 price scenarios" wrong — ghgscen56=102;
  keep "100+"; drop "6000/160 data files").
- NOT_REVIEWABLE (citation validated, value/prose passed to fixer): m56-emis-03, -04 (arithmetic matches code AND doc:1109),
  m56-emis-07 (mechanism rewrite matches preloop.gms:70 + 8-11).
- CITATION_FAILED: none. Every file_evidence and proposed-fix file:line exists, in range, with the claimed token.
