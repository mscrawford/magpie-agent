# Round 49 Adversarial Verification — circular_dependency_resolution.md

Ground truth: `/tmp/magpie_develop_ro` (develop worktree). Defaults from `config/default.cfg`.
All greps run as isolated commands with `|| true`/fallback; absence claims double-checked with positive controls.

Target doc lines re-read (cdr:94-114, 298) — match the auditor's `claim_in_doc` verbatim:
- cdr:98 `pm_carbon_density <------ vm_carbon_stock`
- cdr:105 `Use pm_carbon_density(t-1) as fixed parameter for land costs`
- cdr:113-114 `* Module 29/30 (land conversion costs), equations.gms: / * Uses pm_carbon_density from PREVIOUS timestep for conversion costs`
- cdr:298 `... [q10_land, 10]`

---

## CDR-B1 — VERDICT: UPHELD  (class: consumer_set / attribution; citation_ok=true)

### STEP A — citation check (file_evidence + proposed_fix citations)
```
test -f modules/39_landconversion/calib/equations.gms        -> EXISTS
test -f modules/39_landconversion/calib/declarations.gms     -> EXISTS
wc -l calib/equations.gms = 15 ; declarations.gms = 27
declarations.gms:13  -> " vm_cost_landcon(j,land)  Costs for land expansion and reduction (mio. USD17MER per yr)"  [token present]
equations.gms (q39_cost_landcon, lines 12-15) area-based:
  q39_cost_landcon(j2,land) .. vm_cost_landcon(j2,land) =e=
    (vm_landexpansion(...)*i39_cost_establish(...) - vm_landreduction(...)*i39_reward_reduction(...))
    * pm_interest/(1+pm_interest)
```
Proposed-fix new citations also verified:
```
modules/52_carbon/normal_dec17/equations.gms  EXISTS, 19 lines
  :16  q52_emis_co2_actual(i2,emis_oneoff) ..
  :19  (pcm_carbon_stock(j2,land,c_pools,"actual") - vm_carbon_stock(j2,land,c_pools,"actual"))/m_timestep_length
modules/56_ghg_policy/price_aug22/postsolve.gms:8  pcm_carbon_stock(...) = vm_carbon_stock.l(...)   [matches cdr:110-111]
```
default.cfg: ghg_policy <- price_aug22 ; carbon module dir has only normal_dec17.

### STEP C — adjudication
1. **M39 has ZERO carbon references** (entire module, case-insensitive):
   `rg -ni 'carbon' modules/39_landconversion/` -> no matches.
   `rg -n 'carbon_stock' modules/39_landconversion/` -> no matches.
   Positive control (proves grep works in M39): `rg 'vm_landexpansion' .../equations.gms` -> line 13 hit; `rg 'pm_interest'` -> line 15 hit.
   => M39 (default `calib`) computes conversion costs from land expansion/reduction AREA × annuity, NOT carbon. CONFIRMED.
2. **M29/M30 are not conversion-cost modules**: dir names 29_cropland, 30_croparea, 39_landconversion. `vm_cost_landcon` DECLARED only in `39.../calib/declarations.gms:13`. `q39_cost_landcon` defined only in M39 (declarations/equations/postsolve). M30 realizations = {detail_apr24, simple_apr24} (cropland-area, no conversion-cost eq). CONFIRMED the doc mis-attributes conversion costs to 29/30.
3. **Genuine temporal feedback = pcm_carbon_stock** (NOT carbon density into land costs):
   pcm_carbon_stock DECLARED `56_ghg_policy/price_aug22/declarations.gms:19`, POPULATED `postsolve.gms:8` (= vm_carbon_stock.l), READ by M52 `q52_emis_co2_actual` (equations.gms:19) differencing previous vs current stock. This is the correct Type-1 lagged interface.

### Re-derived true set for the pm_carbon_density_*_ac family (whole-tree, both `(` and inspection of every literal occurrence)
- **DECLARED + POPULATED (producer): Module 52** — declarations.gms:9-13; preloop.gms:71,114; start.gms:17-51.
- **READ (consumers): M14** (14_yields/managementcalib_aug19/presolve.gms:14,26,44,53), **M29** (29_cropland/detail_apr24/preloop.gms:46,48 — default realization), **M32** (32_forestry/dynamic_may24/preloop.gms:18,56 + presolve.gms:59-68), **M35** (35_natveg/pot_forest_may24/presolve.gms:117,240-251).
  (29_cropland/simple_apr24/not_used.txt is a not-used marker, not a consumer; default cropland = detail_apr24, which IS a real consumer.)

**Note for fixer (minor prose imprecision, fix text itself is fine):** the auditor's `reality_in_code` says the _ac family is "read by M14/M29/M32/M35/M52" — strictly M52 *declares/populates* it (producer); the readers are M14/M29/M32/M35. The PROPOSED FIX does not repeat this and correctly uses pcm_carbon_stock / vm_carbon_stock, so apply the fix as written.

UPHELD. Both the attribution (M29/M30 -> should be M39 / M52) and the causal mechanism (carbon density -> land costs is false; the real loop is pcm_carbon_stock -> CO2 emissions in M52) are wrong in the doc; the proposed fix is mechanically sound.

---

## CDR-B2 — VERDICT: UPHELD  (class: producer_declaration; citation_ok=true)

### STEP A — citation check
```
modules/52_carbon/normal_dec17/declarations.gms  EXISTS, 37 lines
  :9  pm_carbon_density_secdforest_ac(t_all,j,ac,ag_pools)
  :10 pm_carbon_density_secdforest_ac_uncalib(...)
  :11 pm_carbon_density_other_ac(...)
  :12 pm_carbon_density_plantation_ac(...)
  :13 pm_carbon_density_plantation_ac_uncalib(...)
```
Lines 9-13 cited -> in range, contain the claimed identifiers. citation_ok=true.

### STEP C — adjudication (bare name absent, whole-tree, both forms + control)
```
rg -n 'pm_carbon_density\('  modules/  -> ABSENT (no bare pm_carbon_density( anywhere)
rg -n 'pm_carbon_density\.'   modules/  -> ABSENT (no solution-level bare form)
rg -no 'pm_carbon_density[a-z_]*' modules/ | uniq  -> ONLY the *_ac (+_uncalib) variants in M52/M35/M32/M29/M14
```
No plain `pm_carbon_density` and no `pm_carbon_density_ac` exist. Actual family = secdforest_ac / other_ac / plantation_ac (+ _uncalib), all dimensioned (t_all,j,ac,ag_pools), declared in M52. CONFIRMED. UPHELD (subsumed by B1 fix; if any density mention is retained, use exact age-class-resolved names).

---

## CDR-B3 — VERDICT: UPHELD  (class: other / wrong equation name; citation_ok=true)

### STEP A — citation check
```
modules/10_land/landmatrix_dec18/declarations.gms  EXISTS
  :27  q10_land_area(j)   Land transition constraint cell area (mio. ha)
modules/10_land/landmatrix_dec18/equations.gms     EXISTS
  :13  q10_land_area(j2) ..
```
Both cited lines in range, contain `q10_land_area`. citation_ok=true.

### STEP C
default.cfg:232 `cfg$gms$land <- "landmatrix_dec18"` (the cited realization IS default).
```
rg -n '\bq10_land\b' modules/  -> NO bare q10_land anywhere (good)
positive control: rg 'q10_land_area' modules/10_land/ -> many hits (decl:27, eq:13, postsolve)
```
The equation is `q10_land_area`; bare `q10_land` does not exist. Doc itself already uses the correct name at cdr:67. cdr:298 `[q10_land, 10]` -> should read `[q10_land_area, 10]`. UPHELD.

---

## Summary
| Bug | Class | citation_ok | Verdict |
|-----|-------|-------------|---------|
| CDR-B1 | consumer_set/attribution | true | UPHELD |
| CDR-B2 | producer_declaration | true | UPHELD |
| CDR-B3 | other (eq name) | true | UPHELD |

All three citations reproduce mechanically; all three claims are correct. No confabulated cross-realization structure detected. Apply all three proposed fixes as written (B1's fix text is accurate despite a minor producer-vs-reader imprecision in the auditor's narrative `reality_in_code`).
