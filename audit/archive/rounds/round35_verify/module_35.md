# Adversarial verification — module_35 confirmed bugs (consumer/dependency-set focus)

Ground truth: `/tmp/magpie_develop_ro` @ develop HEAD `ee98739fd` (Merge PR #887).
Verifier defaulted to skepticism; ran both `NAME(` and `NAME.` forms + positive controls.

Grep harness note: in this environment `grep`/`rg` propagate exit 1 on no-match and the
tool harness aborts the call even with trailing `|| echo`/`true`. Workaround used throughout:
`grep -rc PATTERN DIR | awk -F: '{s+=$2} END{print s+0}'` (always exits 0; prints occurrence count),
cross-checked with `rg -n`.

---

## M35-B1 — Range truncation (ac set) — NOT_CONSUMER_SET
Asserts the documented age-class set is truncated (ac150 vs ac300) and acx threshold mis-stated.
This is a set-membership/range claim about `core/sets.gms`, not a claim about WHICH modules
consume/populate/depend-on an interface variable. → NOT_CONSUMER_SET. Passes to fixer unchanged.
(Not independently re-derived per method step 2; outside the consumer-set scope of this pass.)

---

## M35-B2 — vm_natforest_reduction consumer attribution — CORRECTED
class_is_consumer_set = TRUE (asserts which module consumes vm_natforest_reduction).

Doc line 655 claims the var is "provided to other modules (e.g. Module 73 timber)".
Auditor: sole direct consumer is M32; M73 does not reference it. Auditor's SET is right,
but the auditor's proposed-fix EQUATION NAME is WRONG.

Evidence:
- equation form (all modules): `rg -n 'vm_natforest_reduction\(' /tmp/magpie_develop_ro/modules/`
  -> 32_forestry/dynamic_may24/equations.gms:80 (consumer);
     35_natveg/.../declarations.gms:90 (own decl); 35_natveg/.../equations.gms:84 (own q35 def).
- attribute form (all modules): `rg -n 'vm_natforest_reduction\.'`
  -> only 35_natveg/.../postsolve.gms:39/85/131/177 (M35 writing its own ov_ reporting). No other consumer.
- bare token (all modules): same union as above — confirms no hidden consumer.
- M73 count: `grep -rc 'vm_natforest_reduction' modules/73_timber/ | awk...` = 0
- M73 POSITIVE CONTROL: `grep -rc 'vm_prod_natveg' modules/73_timber/ | awk...` = 6 (search works in M73 dir).
  => M73 genuinely does NOT consume vm_natforest_reduction.

CORRECTION to auditor: the equation at modules/32_forestry/dynamic_may24/equations.gms:80 is
**q32_ndc_aff_limit**, NOT q32_aff_pol. Confirmed:
`rg -n 'q32_aff_pol\b|q32_ndc_aff_limit\b' .../equations.gms`
  -> line 74 ` q32_aff_pol(j2) ..` (NPI/NDC area accounting; reads v32_land + p32_aff_pol_timestep,
     NO vm_natforest_reduction)
  -> line 79 ` q32_ndc_aff_limit(j2) ..` ; line 80 `sum(ct, p32_aff_pol_timestep(ct,j2)) * vm_natforest_reduction(j2) =e= 0;`
The mechanism the auditor described (force =0 when afforestation policy active) is correct;
only the equation label is wrong.

VERDICT: CORRECTED. Apply set-fix (M73 -> M32) but with the right equation name.

---

## M35-B3 — pm_land_start phantom M10 dependency — UPHELD
class_is_consumer_set = TRUE (asserts M35 depends-on / receives pm_land_start from M10).

Doc line 894 lists `pm_land_start(j,land)` as an M35 input from Module 10.

Evidence (M35 = modules/35_natveg/):
- equation form: `grep -rc 'pm_land_start(' modules/35_natveg/ | awk...` = 0
- attribute form: `grep -rc 'pm_land_start\.' modules/35_natveg/ | awk...` = 0
- bare token: `grep -rc 'pm_land_start' modules/35_natveg/ | awk...` = 0
- rg second method: `rg -n 'pm_land_start' modules/35_natveg/` -> no match (exit nonzero).
- POSITIVE CONTROLS (prove M35 dir searchable):
  `grep -rc 'pcm_land' modules/35_natveg/ | awk...` = 29;
  `grep -rc 'vm_lu_transitions' modules/35_natveg/ | awk...` = 4.
- Existence (real token, not typo): `grep -rc 'pm_land_start' modules/10_land/ | awk...` = 3;
  `rg -n 'pm_land_start' modules/10_land/` ->
    10_land/landmatrix_dec18/declarations.gms:9 (decl, "Land initialization area"),
    .../start.gms:8 (pm_land_start = f10_land("y1995",...)),
    .../start.gms:11 (pcm_land = pm_land_start).
  => pm_land_start is an M10 initialization parameter used only to seed pcm_land; M35 never reads it.

Auditor's fix (delete the bullet; M35's real M10 input is vm_lu_transitions already on line 893;
the per-timestep land state M35 reads is core `pcm_land`, not an M10 interface parameter) is correct.

VERDICT: UPHELD.

---

## M35-B4 — M59 (SOM) realization-specific consumer w/o caveat — UPHELD
class_is_consumer_set = TRUE (asserts M59 is a direct consumer of an M35 interface var,
and that the default M59 realization is not).

Doc line 25 lists M59 (SOM) among "Provides to" direct consumers of M35 interface vars.

Default realization: `grep -n 'cfg\$gms\$som' config/default.cfg` -> line 1916
`cfg$gms$som <- "cellpool_jan23"` (default = cellpool_jan23).
Realizations present: cellpool_jan23, static_jan19 (+ input/).

M35 interface vars (from declarations.gms): vm_land_other, vm_landdiff_natveg,
vm_prod_natveg, vm_cost_hvarea_natveg, vm_natforest_reduction.

static_jan19 (NON-default) consumes vm_land_other:
- `rg -n 'vm_land_other\(' modules/59_som/` -> static_jan19/equations.gms:23 & :24
  (vm_land_other "othernat"/"youngsecdf" * fm_carbon_density). Real read.
- static_jan19/not_used.txt does NOT list vm_land_other (it lists pm_land_start, fm_croparea,
  pm_avl_cropland_iso, vm_landexpansion, vm_lu_transitions, pm_climate_class) -> consume is genuine.

cellpool_jan23 (DEFAULT) consumes NO M35 interface var — verified each:
  vm_land_other=1, vm_prod_natveg=0, vm_cost_hvarea_natveg=0, vm_natforest_reduction=0,
  vm_landdiff_natveg=0  (`grep -rc <v> modules/59_som/cellpool_jan23/ | awk...`).
  POSITIVE CONTROL: `grep -rc 'vm_' modules/59_som/cellpool_jan23/ | awk...` = 37 (dir searchable).
  The single vm_land_other "hit" is NOT a consume: `rg -n 'vm_land_other' .../cellpool_jan23/`
  -> cellpool_jan23/not_used.txt:2 `vm_land_other,input,not needed` — i.e. the realization
  EXPLICITLY opts out. So default consumes zero M35 interface vars. Auditor's claim holds.

(Trap avoided: a naive grep count of 1 would falsely read cellpool as a consumer; the not_used.txt
convention disambiguates. R33-style — solution/declaration artifacts must be inspected, not counted.)

VERDICT: UPHELD. Refinement: the precise reason the default consumes none is that
cellpool_jan23 lists `vm_land_other,input,not needed` in its not_used.txt.

---

## M35-B5 — hardcoded line-count drift — NOT_CONSUMER_SET
Asserts body/footer line-count metadata (229/262/203, "1,085 lines") is stale vs the header (294/233/210).
This is metadata internal-consistency, not an interface-variable consumer/populator/dependency claim.
→ NOT_CONSUMER_SET. Passes to fixer unchanged.
Light cross-check (not required): `wc -l` -> equations.gms=233, presolve.gms=294, postsolve.gms=210
(matches the auditor's corrected numbers; total of the three = 737, full-dir total claimed 1165 not
re-derived here). Out of scope for the consumer-set pass.

---

## Summary
| Bug | consumer-set? | Verdict |
|-----|---------------|---------|
| M35-B1 | no  | NOT_CONSUMER_SET |
| M35-B2 | yes | CORRECTED (right set M73->M32; wrong eq name: q32_ndc_aff_limit not q32_aff_pol) |
| M35-B3 | yes | UPHELD |
| M35-B4 | yes | UPHELD (default opts out via not_used.txt) |
| M35-B5 | no  | NOT_CONSUMER_SET |
