# Round 37 Doc Audit: module_34.md (Urban Land)

**Auditor**: Opus 4.8 (1M) adversarial doc auditor
**Date**: 2026-05-30
**Target**: `magpie-agent/modules/module_34.md`
**Ground truth**: `/tmp/magpie_develop_ro/modules/34_urban/` (develop worktree) + `config/default.cfg`

## Overall Verdict: MOSTLY ACCURATE
## Accuracy Score: 7/10 (1 Major + 2 Minor; raw_severity_weighted = 2 + 1 + 1 = 4)

The doc is well-grounded: all 5 equation names, formulas, and line citations verified exact; default realization correct; all parameter/scalar names exist; the static-vs-exo LUH2/LUH3 nuance is handled correctly (matches realization.gms). The main defect is an incomplete reader-set for `vm_carbon_stock` (M56 omitted), plus two small count/provenance errors in the static-realization description.

---

## Verified Claims (correct)

### Realization & config
- **Default = `exo_nov21`**: `config/default.cfg:1126` `cfg$gms$urban <- "exo_nov21"`. ✓
- **Realizations are `exo_nov21` and `static`**: `ls /tmp/magpie_develop_ro/modules/34_urban/` → `exo_nov21/`, `static/`, `module.gms`. ✓ (MANDATE 8)
- **`c34_urban_scenario` default = "SSP2"**: `config/default.cfg:1129` `cfg$gms$c34_urban_scenario <- "SSP2"`. ✓ (MANDATE 3)
- **`s34_urban_deviation_cost = 1e6 USD17MER/ha`**: `exo_nov21/input.gms:13` `/ 1e+06 /`. ✓ (MANDATE 3)
- **Equation count = 5 (exo), 0 (static)**: `exo_nov21/declarations.gms:18-24` declares exactly q34_urban_cell, q34_urban_land, q34_urban_cost1, q34_urban_cost2, q34_bv_urban; static has no equations file. ✓

### Equations (all formulas + line citations exact)
- **q34_urban_cost1** `equations.gms:17-18`: `v34_cost1(j2) =g= sum(ct, i34_urban_area(ct, j2)) - vm_land(j2,"urban")`. ✓
- **q34_urban_cost2** `equations.gms:20-21`: `v34_cost2(j2) =g= vm_land(j2,"urban") - sum(ct, i34_urban_area(ct, j2))`. ✓
- **q34_urban_cell** `equations.gms:25-26`: `vm_cost_urban(j2) =e= (v34_cost1(j2) + v34_cost2(j2)) * s34_urban_deviation_cost`. ✓
- **q34_urban_land** `equations.gms:30-31`: `sum(cell(i2,j2), vm_land(j2,"urban")) =e= sum((ct,cell(i2,j2)), i34_urban_area(ct,j2))`, indexed `(i2)`. ✓
- **q34_bv_urban** `equations.gms:34-35`: `vm_bv(j2,"urban", potnatveg) =e= vm_land(j2,"urban") * fm_bii_coeff("urban",potnatveg) * fm_luh2_side_layers(j2,potnatveg)`. ✓
- All formulas verified character-for-character against source (MANDATE 1).

### Presolve / preloop citations
- `presolve.gms:8` `vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0`. ✓ (doc's interface line 196 correctly writes `ag_pools`)
- `presolve.gms:10-11` t=1: `vm_land.fx(j,"urban") = i34_urban_area(t,j)`. ✓
- `presolve.gms:13-15` t>1: `vm_land.lo=0` (13), `vm_land.l=i34_urban_area` (14), `vm_land.up=Inf` (15). ✓
- `preloop.gms:9-15` two-stage SSP2-freeze-then-scenario logic. ✓
- `preloop.gms:17` `pcm_land(j,"urban") = i34_urban_area("y1995",j)`. ✓
- `preloop.gms:20-21` `vm_bv.l` initialization. ✓
- `scaling.gms:8` `vm_cost_urban.scale(j) = 1e3`; `scaling.gms:9-10` v34_cost1/2 scaling commented out (1e-4). ✓
- `realization.gms:8` LUH3 (LUH2v2: Hurtt 2020, LUH3 publication pending) description. ✓
- `module.gms:8-14` @title/@description. ✓

### Interface variables (declarations + consumers verified)
- **`vm_cost_urban`** declared in M34 (`exo_nov21/declarations.gms:13`); **sole consumer M11** (`11_costs/default/equations.gms:45` `+ sum(cell(i2,j2), vm_cost_urban(j2))`). Positive control: `vm_cost_landcon` present in same M11 eq file. ✓ Doc's M11 attribution correct (MANDATE 9).
- **`vm_land`** declared in M10 (`10_land/landmatrix_dec18/declarations.gms:19` `vm_land(j,land)`); M10 reads it via `q10_land_area` `sum(land, vm_land(j2,land))` (`10_land/landmatrix_dec18/equations.gms:13-14`). M34 sets bounds (presolve) + constrains (q34_urban_land) the `"urban"` slice — "provides vm_land(j,'urban')" framing is accurate. ✓
- **`vm_bv`** declared in M44 (`44_biodiversity/bv_btc_mar21/declarations.gms:19`); populated by M29/M30/M31/M32/M34/M35 (each its own land slice); read/aggregated only by M44 (`bv_btc_mar21/equations.gms:23` q44_bv_weighted; `bii_target/equations.gms:16`). Doc's M44 consumer attribution correct and complete. ✓
- **`vm_carbon_stock`** declared in M56 (`56_ghg_policy/price_aug22/declarations.gms`), NOT M52 (consistent with G2 anchor). M34 populates the `"urban",ag_pools` slice = 0. (Reader-set issue below.)
- `fm_bii_coeff`, `fm_luh2_side_layers`, `sm_fix_SSP2`, `i34_urban_area`, `urban_scen34` set (SSP1-5) all exist. ✓

### Static-vs-exo LUH2/LUH3 (R16 anchor — checked specifically)
- Doc static section (line 55, 514) says "1995 LUH2 baseline". `static/realization.gms:9` says "spatial distribution of 1995 from the LUH2 data set [@hurtt2018luh2]". **Doc matches realization.gms.** The `config/default.cfg:1124` comment says "LUH3" for static — that is a code-internal config-comment vs realization.gms discrepancy, NOT a doc error. The R16 Minor anchor (doc claims LUH2 while config says LUH3) does NOT re-fire here because the doc faithfully tracks the realization.gms source. **No bug.**

### Advisory-checker items (confirm/refute)
- "Verify default realization" → CONFIRMED correct (`exo_nov21`).
- "Verify M34's vm_land('urban') populator role" → CONFIRMED: M34 does not declare vm_land (M10 does); it populates the urban slice via presolve bounds (`presolve.gms:10-16`) and the q34_urban_land equality. Doc's "provides vm_land(j,'urban')" / "DECLARED vs POPULATED vs READ" handling is acceptable (it never claims M34 declares vm_land).
- "Verify urban-land equations" → CONFIRMED: 5 equations, all exact.
- "Consumer sets with both grep forms + positive control" → DONE for vm_cost_urban, vm_bv, vm_land, vm_carbon_stock; one omission found (M56, below).

---

## Bugs Found

### Bug M34-B1 — `vm_carbon_stock` reader-set omits Module 56
- **Severity**: Major (tier_uncertainty: true — G2/R20 anchor argues Critical; zero-value mitigant + correct primary reader pull to Major; tie-breaker → lower)
- **Class**: 15 (latent doc error / consumer-set incompleteness); related to MANDATE 13/17
- **Trigger**: incomplete consumer set for an interface variable M34 populates (R20 anchor: "doc said wrong consumer set; user would have missed modules in a refactor"). Not a Critical-tier listed trigger verbatim; closest is the latent-doc-bug §1.5 mandate (wrong/incomplete producer-consumer set).
- **Doc line**: module_34.md:288-290 (Downstream Modules item 3) and 473 (Related Modules) and 196-198 (Data Flow Outputs item 3)
- **Claim in doc**: "**Module 52 (Carbon)**: Receives vm_carbon_stock(j,"urban",*) = 0 for carbon accounting" — M52 listed as the only recipient of M34's carbon-stock slice.
- **Reality in code**: `vm_carbon_stock` is read directly in equations by M29, M31, M32, M35, M52, M56, M59. M56 (GHG policy) reads it for emission pricing: `56_ghg_policy/price_aug22/equations.gms:22` `(pcm_carbon_stock(...) - vm_carbon_stock(j2,land,c_pools,"%c56_carbon_stock_pricing%"))/m_timestep_length`. M52 reads it for CO2 accounting: `52_carbon/normal_dec17/equations.gms:19`. The urban slice flows to BOTH. (Urban carbon is fixed to 0, so it contributes no numeric emissions — this bounds the harm but a maintainer who lifts the zero-carbon assumption, which the doc itself flags as a limitation, would be misled into thinking only M52 is affected.)
- **File evidence**: `/tmp/magpie_develop_ro/modules/56_ghg_policy/price_aug22/equations.gms:22`; declaration `/tmp/magpie_develop_ro/modules/56_ghg_policy/price_aug22/declarations.gms`
- **verify_cmd**: `rg -ln "vm_carbon_stock\(" /tmp/magpie_develop_ro/modules/*/*/equations.gms` → returns M29, M31, M32, M35, M52, M56, M59 equations.gms (M56 + M52 both present). `rg -n "vm_carbon_stock" /tmp/magpie_develop_ro/modules/56_ghg_policy/price_aug22/equations.gms` → line 22 hit. Positive control: same grep returns M52 (the doc-listed reader), proving the search works.
- **Anchor reference**: G2 carbon-stock populator/reader anchor (R20/R22-R27); R20 `pm_carbon_density_ac` missed-consumer Critical.
- **confirmed**: true
- **proposed_fix**: In module_34.md:288-290, add Module 56 as a second carbon reader. Replace the "Module 52 (Carbon)" bullet block with:
  "3. **Module 52 (Carbon)** and **Module 56 (GHG Policy)**: Both read `vm_carbon_stock(j,"urban",ag_pools,stockType)` (the urban slice, fixed to 0). M52 computes CO2 emissions from inter-timestep carbon-stock change (`q52_emis_co2_actual`); M56 prices those emissions (`q56_emis_pricing_co2`). Note: `vm_carbon_stock` is declared in Module 56, not Module 52. Urban contributes zero because the slice is fixed to 0; lifting that assumption would propagate to BOTH modules." Also update the Data Flow Outputs item (line 197) "To: Module 52 (Carbon) for carbon accounting" → "To: Module 52 (Carbon, emissions) and Module 56 (GHG policy, pricing)"; and add Module 56 to the Related Modules > Downstream list (line 473).

### Bug M34-B2 — static realization eliminates 2 variables, not 3
- **Severity**: Minor
- **Class**: 6 (hardcoded count drift)
- **Trigger**: §1 Minor — wrong detail; careful reader not misled into action ("Computational efficiency" aside).
- **Doc line**: module_34.md:489
- **Claim in doc**: "Computational efficiency: Eliminate 5 equations and 3 variables (marginal savings)"
- **Reality in code**: exo_nov21 declares 3 positive variables (`vm_cost_urban`, `v34_cost1`, `v34_cost2` — `exo_nov21/declarations.gms:13-15`). static declares 1 (`vm_cost_urban` — `static/declarations.gms:10`, fixed to 0 at `static/presolve.gms:14`). So static eliminates the 2 cost-helper variables (`v34_cost1`, `v34_cost2`), not 3 — `vm_cost_urban` persists.
- **File evidence**: `/tmp/magpie_develop_ro/modules/34_urban/static/declarations.gms:10` (only vm_cost_urban); `/tmp/magpie_develop_ro/modules/34_urban/exo_nov21/declarations.gms:13-15` (3 vars)
- **verify_cmd**: `awk '/positive variables/,/^;/' .../exo_nov21/declarations.gms` → 3 vars; `rg -n "vm_|v34_" .../static/declarations.gms | grep -v ov` → only `vm_cost_urban(j)`.
- **confirmed**: true
- **proposed_fix**: module_34.md:489 replace "Eliminate 5 equations and 3 variables (marginal savings)" with "Eliminate 5 equations and 2 variables (v34_cost1, v34_cost2; vm_cost_urban persists, fixed to 0) (marginal savings)".

### Bug M34-B3 — static `vm_land.fx` value wrongly attributed to `i34_urban_area`
- **Severity**: Minor (tier_uncertainty: true — arguably Informational; it is a parenthetical provenance note, not a code-edit target)
- **Class**: 12 (content-level citation mismatch)
- **Trigger**: §1 Minor — wrong detail in a citation-anchored statement; a careful reader checking `static/presolve.gms:9` would see the parameter named does not exist in that realization.
- **Doc line**: module_34.md:514
- **Claim in doc**: "**All t**: vm_land.fx(j,"urban") = pcm_land(j,"urban") = i34_urban_area("y1995",j) (fixed to 1995)" cited to `static/presolve.gms:9`.
- **Reality in code**: `static/presolve.gms:9` is `vm_land.fx(j,"urban") = pcm_land(j,"urban");`. The static realization includes ONLY declarations/presolve/postsolve (`static/realization.gms:17-19`) — no input.gms, no preloop. `i34_urban_area` is therefore NOT defined anywhere in the static realization; the `= i34_urban_area("y1995",j)` equality holds only in exo_nov21 (`exo_nov21/preloop.gms:17`). In static, `pcm_land(j,"urban")` is supplied by core land initialization (read from input), not by an M34 parameter.
- **File evidence**: `/tmp/magpie_develop_ro/modules/34_urban/static/presolve.gms:9`; `/tmp/magpie_develop_ro/modules/34_urban/static/realization.gms:17-19` (phases); absence confirmed.
- **verify_cmd**: `rg -n "i34_urban_area" /tmp/magpie_develop_ro/modules/34_urban/static/` → empty (no matches). Positive control: `rg -n "pcm_land" .../static/presolve.gms` → lines 9, 12 (search works in that dir). `rg -n "phase" .../static/realization.gms` → only declarations/presolve/postsolve.
- **confirmed**: true
- **proposed_fix**: module_34.md:514 replace "vm_land.fx(j,"urban") = pcm_land(j,"urban") = i34_urban_area("y1995",j) (fixed to 1995)" with "vm_land.fx(j,"urban") = pcm_land(j,"urban") (fixed to the 1995 baseline; static reads `pcm_land` from core initialization and does not use M34's i34_urban_area parameter)".

---

## Missing Nuances (not scored — observations)
- Doc line 16/320 says M34 "Depends On: Module 09 (Drivers - LUH3 scenarios)". The actual M09 link is the timing scalar `sm_fix_SSP2` (M09 `aug17/input.gms` `ln = 2025`), used at `exo_nov21/preloop.gms:10`. The LUH3 *scenario data* comes from the input file `f34_urbanland.cs3` (`input.gms:16-20`), not from M09. Characterizing the M09 dependency as "LUH3 scenarios" is imprecise (the SSP-freeze year is the real dependency), but it is hedged/secondary prose, not a code-checkable interface claim. Deferred, not a bug.
- Doc line 318 "Provides To: ... Module 22 (Conservation - potentially)". M22 reads the core parameter `pcm_land(j,"urban")` (`22_land_conservation/area_based_apr22/presolve_ini.gms:83,93,104`), not a direct M34 interface variable. The doc already hedges "potentially"; the link is via the shared core parameter, not a direct M34→M22 variable. Acceptable as hedged.
- Doc lines 6/556: static "~40 lines" — actual is 66 total lines across 4 .gms files (incl. license headers). exo "~217" → actual 220. Both are approximations prefixed "~"; not scored.
- `vm_carbon_stock.fx(...,ag_pools,...)` fixes only above-ground pools (`ag_pools`), not the full `c_pools` set. The doc's interface citation (line 196) correctly uses `ag_pools`; prose "fixes urban carbon stocks to zero" is a defensible simplification. Not scored.

---

## Mechanical checks
- M1 (file:line citations present): PASS — 60+ citations, sampled set verified exact.
- M3 (variable prefixes valid): PASS — vm_/v34_/s34_/c34_/i34_/fm_/pcm_/sm_ all valid and exist in code.
- Realization names (MANDATE 8): PASS — `exo_nov21`, `static` both exist.

## Summary
Strong doc: equations, formulas, citations, default realization, and the LUH2/LUH3 static nuance all verified correct. One Major (vm_carbon_stock reader-set omits M56 — G2-anchor consumer-set incompleteness, bounded by the zero-value urban slice) and two Minor (static eliminates 2 not 3 variables; static vm_land.fx value mis-attributed to the exo-only i34_urban_area parameter). Score 7/10.
