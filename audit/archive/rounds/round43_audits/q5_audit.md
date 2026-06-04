# Audit Report: Q5 (How is timber demand satisfied in MAgPIE?)

**Round 43 — semantic-validation flywheel**
**Auditor**: Opus, adversarial code-grounded
**Ground truth**: live GAMS @ develop HEAD ee98739fd (clean), `modules/` + `config/default.cfg`

---

## Overall Verdict: ACCURATE
## Accuracy Score: 8/10

The answer is structurally sound and substantively correct on every load-bearing claim: the M73 default realization, the exogenous-demand mechanism, the production-variable algebra, the harvest-draws-on-growing-stock formulas for both plantations (M32) and natural vegetation (M35), the M52 stock-difference emission equation, and — the central probe — the **absence of any harvested-wood-product (HWP) carbon pool**. All core equation citations (`q73_prod_wood/woodfuel`, `q32_prod_forestry`, `q32_hvarea_forestry`, `q32_carbon`, `q35_prod_*`, `q35_hvarea_secdforest`, `q52_emis_co2_actual`) land on exact lines with faithful formula reproduction. Two citation drifts in the construction-wood region of `preloop.gms` are the only defects, both Minor (correct concept, line numbers ~6 lines off to adjacent content).

This question overlaps the **G2 regression anchor** (vm_carbon_stock producer/consumer attribution). The answer handles it correctly: M52 only READS `vm_carbon_stock` via `q52_emis_co2_actual`; the land modules (M32 forestry, M35 natveg) POPULATE it. No producer/consumer inversion.

---

## Mechanical checks (M1–M6)

| # | Check | Result | Evidence |
|---|---|---|---|
| M1 | File:line citations present | ✅ PASS | Dozens of `modules/XX/realization/file.gms:NN` citations throughout |
| M2 | Active realization stated | ✅ PASS | M73 `default` (only realization), and the Sources block names M52 `normal_dec17`, M32 `dynamic_may24`, M35 `pot_forest_may24` — all match config defaults |
| M3 | Variable prefixes valid | ✅ PASS | `vm_prod`, `vm_prod_forestry`, `vm_prod_natveg`, `vm_carbon_stock`, `pcm_carbon_stock`, `im_growing_stock`, `im_vol_conv`, `pm_demand_forestry`, `v73_*`, `s73_*`, `s35_*` all correct prefix/scope |
| M4 | Epistemic badges present | ✅ PASS | 🟡 used throughout; closing block present |
| M5 | Confidence tier matches depth | ✅ PASS | All claims tagged 🟡 (docs-only); answer explicitly states "No .gms files were opened" — honest and consistent |
| M6 | Closing source statement | ✅ PASS | Sources block: "docs verified against modules/.../*.gms" per module |

All 6 mechanical checks pass.

---

## Verified Claims (correct)

**(a) Default realization + demand drivers:**
- M73 default = `default` (only realization). ✅ `config/default.cfg:2205` `cfg$gms$timber <- "default"`; `ls modules/73_timber/` shows only `default/` + `input/`.
- Demand is **exogenous**, computed in preloop, fed to optimization via `pm_demand_forestry(t_ext,i,kforestry)`. ✅ `preloop.gms:49-51` sets `pm_demand_forestry` from `p73_timber_demand_gdp_pop * im_vol_conv`; it is a parameter, not a variable — parameterized, not endogenous.
- Lauri 2019 demand formula `Demand(t) = Demand(t-1) × Pop-ratio × GDP_pc-ratio^elasticity`. ✅ `preloop.gms:21-27` matches exactly (loop over `t_all`, lines 22-26).
- Income elasticity from Morland 2018 (`f73_income_elasticity.csv`). ✅ `input.gms:33-39` reads `f73_income_elasticity`; `preloop.gms:14` populates `p73_income_elasticity`.
- Saturation: elasticity → 0 above `s73_income_threshold = 10000 USD17PPP`. ✅ `input.gms:19` `/ 10000 /`; `preloop.gms:15` zeroes elasticity when `im_gdp_pc_ppp_iso > s73_income_threshold`.
- Woodfuel elasticity always active (re-set after the threshold zeroing). ✅ `preloop.gms:16` re-assigns `p73_income_elasticity(...,"wood_fuel")` AFTER line 15's zeroing, so woodfuel is exempt from saturation. (Answer's "always active" is correct; element name `wood_fuel` matches sets.gms:13.)
- Drivers from M09: `im_pop_iso`, `im_gdp_pc_ppp_iso`. ✅ Used at `preloop.gms:21,24,26`.
- Historical anchor to FAO before projection horizon. ✅ `preloop.gms:12` sets `t_past_forestry` to `f73_prod_specific_timber` (FAO).
- ISO→region aggregation. ✅ `preloop.gms:31`.
- Conversion mio m³ → mio tDM via `im_vol_conv(i)` (tDM/m³) **from M52**. ✅ `im_vol_conv` DECLARED `modules/52_carbon/normal_dec17/declarations.gms:23` ("Regional basic wood density (tDM per m3)"), POPULATED `preloop.gms:21` in M52. Cross-module attribution correct.
- Two product categories (wood, woodfuel) via `kforestry_to_woodprod`. ✅ `sets.gms:37-41` maps `wood→industrial_roundwood`, `woodfuel→wood_fuel`.
- Construction-wood add-on via Churkina 2020 (`c73_build_demand` = BAU/10pc/50pc/90pc) or linear ramp (`s73_expansion`). ✅ Scenario names confirmed `sets.gms:48-51` + `input.gms:11-12`; branches exist `preloop.gms:72-80` (but see citation drift below for exact lines).

**(b) Production variable + harvest-on-stock:**
- `vm_prod(j,kforestry)` is the production variable (mio tDM/yr). ✅
- `q73_prod_wood` (`equations.gms:43-50`) and `q73_prod_woodfuel` (`equations.gms:52-61`) — both quoted verbatim and **match exactly**. ✅
- M32 plantations: `q32_hvarea_forestry` (`equations.gms:237-240`) `v32_hvarea_forestry =e= v32_land_reduction(j,"plant",ac_sub)`. ✅ Exact.
- `q32_prod_forestry` (`equations.gms:246-249`): `sum(kforestry,vm_prod_forestry) =e= sum(ac_sub, v32_hvarea_forestry × im_growing_stock(ct,j,ac_sub,"forestry")) / m_timestep_length_forestry`. ✅ Exact (answer omits the inner `sum(ct,...)` singleton wrapper — conventional, immaterial).
- `im_growing_stock` computed by **M14** from `pm_carbon_density_plantation_ac`. ✅ `modules/14_yields/managementcalib_aug19/presolve.gms:24-26` `im_growing_stock(t,j,ac,"forestry") = ... pm_carbon_density_plantation_ac(t,j,ac,"vegc")`. Cross-module attribution correct.
- Replanting to youngest age class, excluded from net expansion via `q32_land_expansion_forestry` (`equations.gms:61-62`). ✅ Line 62 subtracts `v32_land_replant` for `"plant"`.
- M35 natveg three forest types:
  - `q35_prod_secdforest` (`equations.gms:144-147`). ✅ Exact match.
  - `q35_prod_primforest` (`equations.gms:153-156`), uses `im_growing_stock(ct,j,"acx","primforest")` — mature acx, no age structure. ✅ Exact.
  - `q35_prod_other` (`equations.gms:162-168`): `othernat`→"other" stock, `youngsecdf`→"secdforest" stock. ✅ Matches lines 165-166 exactly.
  - `q35_hvarea_secdforest` (`equations.gms:176-179`): harvest ≤ reduction. ✅ Exact.
- Harvest bound `s35_natveg_harvest_shr` (default 1 = unconstrained). ✅ `input.gms:25` `/1/`.
- `s35_hvarea` default = 2 (endogenous). ✅ `input.gms:18` "(0=zero 1=exogenous 2=endogenous) / 2 /".
- Natural-origin secdforest (`pc35_secdforest_natural`) protected by lower bound on `v35_secdforest` (`presolve.gms:177-180`). ✅ `presolve.gms:177` and `:179` set `v35_secdforest.lo = max(..., pc35_secdforest_natural(...))`.
- Residues → woodfuel only, ≤ 15% of stem harvest. ✅ `q73_prod_residues` (`equations.gms:75-81`), `s73_residue_ratio = 0.15` (`input.gms:20`); 0.27 × 0.52 ≈ 0.15 derivation in eq comments (`equations.gms:63-67`).
- Emergency slack `v73_prod_heaven_timber` @ 1e6 USD17MER/tDM. ✅ `s73_free_prod_cost / 1e+06 /` (`input.gms:17`).

**(c) M52 carbon interaction:**
- M32 `q32_carbon` (`equations.gms:108-109`) computes `vm_carbon_stock(j,"forestry",ag_pools,stockType)` via `m_carbon_stock_ac` macro. ✅ Quoted verbatim, exact.
- M35 computes `vm_carbon_stock` for primforest/secdforest. ✅ `q35_carbon_primforest` (`:42-44`), `q35_carbon_secdforest` (`:49-51`).
- M52 single equation `q52_emis_co2_actual` (`equations.gms:16-19`) `(pcm_carbon_stock - vm_carbon_stock)/m_timestep_length`. ✅ Quoted verbatim, **exact**. M52 is a pure READER (G2 anchor handled correctly).
- Stock-difference method, harvest → CO2-C emission. ✅ Correct characterization.
- **No HWP pool — all harvested carbon emitted immediately.** ✅✅ **VERIFIED IN CODE**: `core/sets.gms:324-325` `c_pools /vegc,litc,soilc/` — only land-based pools; `emis_land(emis_oneoff,land,c_pools)` (`:332`) maps only land×carbon-pool. Codebase-wide search found NO HWP/wood-product carbon pool in M52/M73/M32. The "wood product" string matches are FAO demand SETS (`total_wood_products`, `wood_products` — `73_timber/sets.gms:10-25`), not carbon storage. Claim is fully correct.
- Emissions flow to M56 carbon price → harvest cost signal. ✅ Directionally correct (`vm_emissions_reg` is the M52 output consumed by M56).

---

## Bugs Found

### Q5-B1
- **Severity**: Minor
- **Class**: 10 (stale file:line citation)
- **Trigger** (§1 Minor): "Off-by-few line citation where adjacent lines say similar things" — citation drift to nearby content in the same code region.
- **Claim in answer**: "Optional construction wood demand can add to industrial roundwood: Churkina et al. 2020 scenarios (`c73_build_demand` = BAU/10pc/50pc/90pc, `preloop.gms:66-69`)"
- **Reality in code**: The Churkina construction-wood branch is `if(s73_expansion = 0, p73_demand_constr_wood(...) = f73_construction_wood_demand(...,"%c73_build_demand%"));` at **`preloop.gms:72-75`**. Lines 66-69 are the `p73_fraction` post-processing (subtract `p73_fraction_sm_fix`, clamp negatives, hold post-2100). The concept (Churkina scenarios driven by `c73_build_demand`) is correctly described; only the line pointer is ~6 lines early to different content.
- **File evidence**: `modules/73_timber/default/preloop.gms:72-75` (Churkina branch) vs cited 66-69 (`p73_fraction` cleanup).
- **Anchor reference**: resembles R20 citation-drift anchor but smaller magnitude and concept-correct → Minor, not Major.

### Q5-B2
- **Severity**: Minor
- **Class**: 10 (stale file:line citation)
- **Trigger** (§1 Minor): off-by-few line citation, adjacent region.
- **Claim in answer**: "...or a simple linear expansion ramp (`s73_expansion > 0`, `preloop.gms:71-74`)"
- **Reality in code**: The `if(s73_expansion > 0, p73_demand_constr_wood(t_all,i) = pm_demand_forestry(t_all,i,"wood") * p73_fraction(t_all));` branch is at **`preloop.gms:78-80`**. The cited range 71-74 overlaps the Churkina branch (72-75), not the expansion branch. Concept correct, line pointer drifts to the wrong `if` block.
- **File evidence**: `modules/73_timber/default/preloop.gms:78-80` (expansion branch) vs cited 71-74.
- **Anchor reference**: same family as B1.

**Score computation**: `10 − (4×0 crit) − (2×0 maj) − (1×2 min) = 8`.

---

## Tier-uncertainty / judgment notes (not scored as bugs)

- **`s35_hvarea` activation phrasing** (answer line 84): "The default for `s35_hvarea` is 2 (endogenous harvest), but this is only activated when `s73_timber_demand_switch = 1`." This loosely couples two distinct switches: `s35_hvarea = 2` is what makes harvested area an endogenous (free) variable (no `.fx` in `presolve.gms:274-281`); `s73_timber_demand_switch` controls whether `pm_demand_forestry` is non-zero (`preloop.gms:31` multiplies by the switch). With the switch off, demand is zero so endogenous harvest produces nothing — so the operational effect the answer describes is real, but "s35_hvarea=2 is activated by the s73 switch" is imprecise (the switches are independent; one gates demand, the other gates the harvest variable's freedom). **Not scored** — defensible reading, no reader would be misled into a wrong action, and the §1 tie-breaker pulls toward not-a-bug. Flagging for the record.
- **`im_growing_stock` inner `sum(ct,...)`**: answer writes `im_growing_stock(ct,j,ac_sub,"forestry")`; code wraps in `sum(ct, ...)`. `ct` is the current-timestep singleton; the sum is a no-op semantically. Conventional simplification, not a bug.

---

## Latent doc bugs (§1.5)

**None.** The answer is correct AND I found no evidence it leaned on a wrong load-bearing doc claim. Every interface variable, equation name, populator/consumer attribution, realization, and default the answer asserts matches code. (I did not separately re-read `module_73.md`/`module_52.md`/`module_32.md`/`module_35.md` line-by-line against code for THIS audit — the latent-bug mandate triggers only when the answer is correct but visibly rests on a doc claim that contradicts code, and nothing in the answer's content contradicts the code I read. The two citation drifts in B1/B2 are answerer-level, not doc-error-propagation that I could confirm without diffing the doc; treated as `answerer_confabulation`-adjacent citation drift, scored on the answer.)

---

## Missing Nuances (informational, not scored)

- The `s73_free_prod_cost` value is conditionally lowered to `s73_timber_prod_cost_wood` when `s73_timber_demand_switch = 0` (`preloop.gms:9`). With the default switch=1 this never fires, so the answer's 1e6 figure is right for default — but the conditional is worth knowing for non-default runs. (Answer's scope is default config, so this is fine.)
- The FAO woodfuel stacking correction (`s73_woodfuel_stacking_factor = 0.65`, `preloop.gms:42`) reduces woodfuel demand ~35%; not mentioned, but tangential to the question.
- The answer's "Doc wished existed" suggestion (a cross-module timber-carbon feedback doc) is well-judged — the end-to-end harvest→area-reduction→vm_carbon_stock→q52→M56 loop is genuinely not consolidated anywhere; `cross_module/carbon_balance_conservation.md` covers accounting but not this pathway.

---

## Summary

A strong, code-faithful answer (8/10). It nails the three sub-questions: (a) M73 `default` realization with exogenous Lauri-2019/Morland-2018 demand saturating above 10000 USD17PPP and converted via M52's `im_vol_conv`; (b) `vm_prod(j,kforestry)` assembled from `vm_prod_forestry` (M32, harvested area × `im_growing_stock`/timestep) and `vm_prod_natveg` (M35, same formula per forest type) plus residues and the heaven-timber slack; (c) harvest shrinks `vm_carbon_stock`, M52's lone `q52_emis_co2_actual` registers the stock drop as immediate CO2-C, and — the headline check — **there is no HWP pool** (`c_pools = vegc/litc/soilc` only), so harvested carbon is emitted in full at harvest with no decay delay. Both defects are Minor `preloop.gms` citation drifts in the construction-wood region (Churkina branch is `:72-75`, expansion branch is `:78-80`, not the cited `:66-69`/`:71-74`). The G2-adjacent carbon producer/consumer attribution is correct (M52 reads; land modules populate).

**Verified M73 default**: `default` (the only realization; `config/default.cfg:2205`).
**No-HWP claim**: **CORRECT** — verified in code (`core/sets.gms:324-325`, `c_pools /vegc,litc,soilc/`; no wood-product carbon pool anywhere in M52/M73/M32).
