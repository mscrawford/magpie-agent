# Round 55 depth audit — module_52.md — lens: consumer_read

**Target**: `modules/module_52.md` (Module 52 Carbon, realization `normal_dec17`)
**Ground truth**: `/private/tmp/magpie_develop_ro` (develop worktree)
**Lens**: consumer_read — entered from the reader side (presolve/postsolve/equation-RHS of named consumers), grepped BOTH `NAME(` and `NAME.` forms, checked the role map first then confirmed both endpoints.

Default realization confirmed: `normal_dec17` (only realization; `main.gms:235 $setglobal carbon normal_dec17`).

---

## Bugs found (3)

### BUG 1 — Major — attribution_read (consumer-set omission)
**Doc**: module_52.md:458 (also 138, 292) — `pm_carbon_density_secdforest_ac_uncalib` "Consumers: Module 32 (afforestation "aff" ... and NDC forest "ndc"), Module 29 (tree cover on cropland). All three use cases represent *new establishment*..." Line 292 adds M35; line 138 adds M35. **All three consumer lists OMIT Module 14.**

**Reality**: Module 14 reads `pm_carbon_density_secdforest_ac_uncalib` at `modules/14_yields/managementcalib_aug19/presolve.gms:66` to build `im_growing_stock_ysf` (young secondary forest regrowing on other land — its wood yield). This is a fourth, load-bearing consumer.

**Role map**: `pm_carbon_density_secdforest_ac_uncalib` read_by = [14, 29, 32, 35, 52]. Doc lists 29/32/35, omits 14.

**Verify**:
```
rg -n "pm_carbon_density_secdforest_ac_uncalib" .../14_yields/
→ managementcalib_aug19/presolve.gms:66:     pm_carbon_density_secdforest_ac_uncalib(t,j,ac,"vegc")
```
Context (presolve.gms:64-66): `im_growing_stock_ysf(t,j,ac) = ( pm_carbon_density_secdforest_ac_uncalib(t,j,ac,"vegc") / sm_carbon_fraction * fm_aboveground_fraction("secdforest") / ... )`.

Note the plantation sibling is fine: `pm_carbon_density_plantation_ac_uncalib` read_by = [29, 32, 52]; the doc (line 478) correctly lists only 29/32. Only the secdforest-uncalib list omits M14.

**Severity**: Major (borderline Critical). Same parameter family and failure mode as the immutable R20 anchor (pm_carbon_density_ac consumer-set omission → Critical) and §1.5 latent-doc-bug mandate (wrong consumer set = Critical for refactor harm). Downgraded to Major per the tie-breaker: a single omission from an otherwise-correct multi-consumer list, and M14 is prominently listed elsewhere in the doc as a consumer of the sibling calibrated params.

**Fix**: Add Module 14 to the `pm_carbon_density_secdforest_ac_uncalib` consumer list in all three places (§1b line 458, line 292 cross-module read/write, line 138 caveat), citing `modules/14_yields/managementcalib_aug19/presolve.gms:66` (im_growing_stock_ysf for youngsecdf wood yield).

---

### BUG 2 — Major — data_flow_direction (R51 / MANDATE 21: parallel not serial)
**Doc**: module_52.md:443 — `vm_emissions_reg` "**Consumers**: Module 56 (GHG Policy) for carbon pricing and emission constraints." Reinforced at line 740-741 ("`vm_emissions_reg(i,emis_oneoff,"co2_c")` ... Used for carbon pricing and emission constraints") and the Execution Sequence (line 764-765: "Module 52: Calculate CO2 emissions ... Module 56: Apply carbon prices to emissions").

**Reality**: M52 writes ONLY the `emis_oneoff`/`co2_c` slice of `vm_emissions_reg` (`equations.gms:17`). **No equation anywhere reads that slice.** Module 56's carbon pricing (`q56_emis_pricing_co2`, `modules/56_ghg_policy/price_aug22/equations.gms:19-22`) RE-COMPUTES CO2 emissions directly from `pcm_carbon_stock - vm_carbon_stock` — it does NOT read `vm_emissions_reg`. M56's only `vm_emissions_reg` read (`equations.gms:17`, q56_emis_pricing) is the DISJOINT `emis_annual` slice (CH4/N2O/peatland). M52 and M56 are PARALLEL readers of `vm_carbon_stock`, not a producer→consumer pair. M52's `vm_emissions_reg` co2_c output flows only to postsolve/reporting (`ov_emissions_reg`, magpie4::reportEmissions).

**Verify**:
```
rg -n "vm_emissions_reg" .../56_ghg_policy/price_aug22/*.gms | grep -v declarations | grep -v postsolve
→ equations.gms:17:    vm_emissions_reg(i2,emis_annual,pollutants);   # emis_annual ONLY
grep -n -A6 "emis_oneoff|emis_annual" core/sets.gms
→ emis_oneoff (314-318) = {crop_vegc..other_soilc};  emis_annual (320-322) = {inorg_fert..peatland}   # DISJOINT
# full-tree: no equation reads vm_emissions_reg(emis_oneoff,...) except M52 writing it
rg -n "vm_emissions_reg" .../modules/ --glob '*.gms' | (only M51/53/58 write their own slices; M56 reads emis_annual; M57 reads maccs/n2o slices)
```
This is exactly the immutable R51 anchor ("M56 reads vm_carbon_stock DIRECTLY in q56_emis_pricing_co2, parallel to M52; M56 does NOT consume M52's vm_emissions_reg co2_c").

**Severity**: Major — misleads about the model's core carbon-pricing mechanism. A user editing `q52_emis_co2_actual` expecting the carbon price/cost to change would be wrong (M56 recomputes from stocks); wrong-file modification risk.

**Fix**: Change the consumer claim to reflect parallel structure: M52's `vm_emissions_reg(i,emis_oneoff,"co2_c")` is a REPORTING output (postsolve `ov_emissions_reg` / magpie4). Carbon PRICING of land-use CO2 is done independently by M56's `q56_emis_pricing_co2` (`modules/56_ghg_policy/price_aug22/equations.gms:19-22`), which reads `vm_carbon_stock` directly (parallel to M52), NOT M52's emissions. M56 reads `vm_emissions_reg` only for the `emis_annual` (non-CO2) slice at `equations.gms:17`.

---

### BUG 3 — Minor — set_membership (phantom consumers in dependency metadata)
**Doc**: module_52.md:1201 — "**Provides to**: Modules 56 (ghg_policy), 11 (costs), 44 (biodiversity)".

**Reality**: Neither Module 11 (costs) nor Module 44 (biodiversity) reads ANY M52 output (`fm_carbon_density`, `pm_carbon_density_*`, `im_vol_conv`, `vm_emissions_reg`, `i52_*`, or the shared `vm_carbon_stock`). Only M56 is a genuine M52 consumer (reads `fm_carbon_density` at `price_aug22/preloop.gms:10`).

**Verify** (positive control M14 hit, so the search is live):
```
rg -n "fm_carbon_density|pm_carbon_density|im_vol_conv|vm_emissions_reg|i52_|vm_carbon_stock" .../11_costs/   → (empty)
rg -n "...same..." .../44_biodiversity/                                                                        → (empty)
rg -ln "pm_carbon_density" .../14_yields/  → managementcalib_aug19/presolve.gms   (control passes)
```
Related looseness in the same auto-generated block: "**Depends on**: Modules 10 (land), 28 (age class), 35 (natveg)" — only M28 is a direct M52 dependency (`im_forest_ageclass`); M52's actual direct upstreams are M45/M56/M28/M32/M14. Not flagged separately (same heuristic-metadata block).

**Severity**: Minor — this is the auto-generated "Dependency Chains / centrality" appendix (loose graph metadata), low action-stakes, but a plain "provides to" reading of M11/M44 is a phantom-consumer content error.

**Fix**: Drop Modules 11 and 44 from "Provides to" (or relabel the block as transitive/centrality-graph metadata, not direct consumers). Genuine direct M52 consumers: 14, 29, 30, 31, 32, 35, 56, 59, 73.

---

## Claims verified correct (high-signal, not exhaustive)

- **Formula** q52_emis_co2_actual (doc 306-311, 780-784): exact match `equations.gms:16-19`; declared `declarations.gms:30`. ✓
- **Macros**: `m_growth_vegc` core/macros.gms:18, `m_growth_litc_soilc` :20, `m_timestep_length` :51 — all exact. ✓
- **Defaults**: `s52_growingstock_calib`=1 (input.gms:46), `s52_k_high_secdf`=0.1 (:47), `s52_k_high_plant`=0.15 (:48), `c52_carbon_scenario`=cc, `c52_land_carbon_sink_rcp`=RCPBU (config + input.gms). ✓
- **Phase order** (doc: "preloop runs AFTER start.gms"): confirmed — `core/calculations.gms:13` start, `:15` preloop. ✓ (initially suspected wrong; verified correct.)
- **Uncalib save-before-overwrite**: start.gms:43-44 (indexes ag_pools = vegc+litc) then preloop.gms:71-73/114-116 overwrite vegc. ✓
- **pm_carbon_density_secdforest_ac** consumers M14 (`.../14_yields/.../presolve.gms:44`), M35 (`.../35_natveg/pot_forest_may24/presolve.gms:248`). Role map [14,35,52]. ✓
- **pm_carbon_density_plantation_ac** consumers M14 (presolve.gms:26), M32 (`.../32_forestry/dynamic_may24/presolve.gms:65`). Role map [14,32,52]. ✓
- **pm_carbon_density_other_ac** consumers M14, M35. Role map [14,35,52]. ✓
- **pm_carbon_density_plantation_ac_uncalib** consumers M32 (aff presolve.gms:61), M29 (preloop.gms:48). Role map [29,32,52]. ✓
- **fm_carbon_density** consumers (doc 266-273, 484): M14 (presolve.gms:35), M29 (detail_apr24/equations.gms:41), M30 (simple_apr24/equations.gms:51, default realization confirmed), M31 (endo_jun13/equations.gms:24), M32 (dynamic_may24/presolve.gms:176), M35 (pot_forest_may24/equations.gms:44), M56 (price_aug22/preloop.gms:10), M59 (cellpool_jan23/preloop.gms:12). Role map read_by = [14,29,30,31,32,35,52,56,59]. Exact match. ✓
- **vm_carbon_stock** populators (doc 424): 29,31,32,34,35,59; M30 populates separate `vm_carbon_stock_croparea` folded in by M29 (simple_apr24/equations.gms:31 reads, 30/simple_apr24/equations.gms:50 writes); M58 does NOT populate. Aligns with immutable G2 anchor (M56's preloop.gms:11 `.l` init is not a populate). ✓
- **pcm_carbon_stock** carry-forward split by pool: ag_pools in M56 postsolve.gms:8; soilc in M59 cellpool postsolve.gms:13 + static postsolve.gms:9. Commit `931db85c4` = "59_som: carry soil pcm_carbon_stock forward each timestep" (verified via git log). ✓
- **im_vol_conv** consumer M73: preloop.gms:49,51 (pm_demand_forestry m³→tDM) + :90,91 (im_timber_prod_cost wood/woodfuel). Role map [52,73]. ✓
- **im_forest_ageclass** from M28 (populated_by [28]); also read by M35 (pot_forest_may24/preloop.gms:20). ✓
- **pm_land_plantation** from M32 (declared+populated 32, read_by [32,52]). ✓
- **fm_ipcc_bef** (M14 input.gms:66), **fm_aboveground_fraction** (M14 input.gms:74), **sm_carbon_fraction** (M14 input.gms:22, /0.5/). ✓
- **im_growing_stock** downstream (doc 724): M32 (presolve.gms:181), M35 (equations.gms:147). ✓
- **Sets**: emis_oneoff core/sets.gms:314-318, emis_annual :320-322, c_pools :324, emis_land :332; rcp52 sets.gms:9-10; iter52 sets.gms:12-13. ✓
- **Step-3/Step-4 calibration formulas** (doc 245-263) match preloop.gms:53-64 (secdf) and :88-99 (plantation), incl. the secdforest vs forestry aboveground-fraction difference (:61 vs :96). ✓

---

## Deferred (unverifiable / out of scope, no bug asserted)
- Exact date "2026-06-25" for commit 931db85c4 (hash + commit message content confirmed; date not independently checked — provenance detail only).
- "GFAD (Poulter et al.)" attribution for im_forest_ageclass — descriptive provenance, matches code comment "full GFAD age distribution"; source citation itself not verified against a paper.
- `s52_plantation_threshold` appears in config/default.cfg (=8) but no `.gms` in modules/ references it (rg empty); not a doc claim, so not a doc bug — noted only as an observation.
