# Doc Audit — module_56.md (GHG Policy, price_aug22)

**Auditor**: Opus adversarial doc-auditor (Round 50 doc-audit sweep)
**Target**: `<magpie-agent>/modules/module_56.md`
**Ground truth**: `/tmp/magpie_develop_ro/modules/56_ghg_policy/` (develop worktree) + `/tmp/magpie_develop_ro/config/default.cfg`
**Date**: 2026-06-06

---

## Summary verdict

The doc is **substantially accurate** on the high-stakes, score-relevant claims: all 7 equation names/signatures/citations, the G2 `vm_carbon_stock` populator set (M29/31/32/34/35/59), all scalar defaults (verified in both `input.gms` and `default.cfg`), the single realization name, and the `vm_emissions_reg` producer set are all CORRECT. No Critical bugs.

Found **2 Major** + **6 Minor/Informational** bugs. The two Major issues are: (1) a recurring fabricated count — "60+ policy scenarios" when `scen56` has exactly **44** members; (2) an interface-parameter consumer omission — `im_pollutant_prices` is read by **M57 (maccs)** but the doc never lists M57 as a consumer.

---

## Claims verified CORRECT (high-value)

### Equations (all 7) — `price_aug22/equations.gms`
- `q56_emis_pricing` (15-17), `q56_emis_pricing_co2` (19-22), `q56_emission_cost_annual` (29-33), `q56_emission_cost_oneoff` (45-52), `q56_emission_costs` (56-58), `q56_reward_cdr_aff_reg` (67-71), `q56_reward_cdr_aff` (73-79). Every signature, index order, and `=e=` body matches the doc's quoted GAMS. Equation count = 7 (declarations.gms grep). ✅
- `q56_emis_pricing_co2` reads `vm_carbon_stock` directly (bypassing `vm_emissions_reg`) — confirmed equations.gms:22. The doc's "Architectural Note — Direct Carbon Stock Pathway" is accurate. ✅

### G2 anchor — `vm_carbon_stock` DECLARED / POPULATED / READ
- **DECLARED**: M56 only — `price_aug22/declarations.gms:34`. ✅
- **POPULATED** (equation LHS `=e=`): M29 (`29_cropland/simple_apr24/equations.gms:30`, `detail_apr24/equations.gms:39`, crop), M31 (`31_past/endo_jun13/equations.gms:23`, past), M32 (`32_forestry/dynamic_may24/equations.gms:108`, forestry), M35 (`35_natveg/pot_forest_may24/equations.gms:43,50,54`, primforest/secdforest/other), M59 (`59_som/cellpool_jan23/equations.gms:62`, `static_jan19/equations.gms:12,18,22`, soilc). **POPULATED via `.fx`**: M34 (`34_urban/exo_nov21/presolve.gms:8`, `static/presolve.gms:10`, urban=0), M31 (`31_past/static/presolve.gms:15`). → populator set = **M29,31,32,34,35,59**. Doc Section 4.1 + 12.4 match EXACTLY. ✅
- **READ** (RHS): M52 (`52_carbon/normal_dec17/equations.gms:19`), M56 (equations.gms:22). ✅
- M30 populates `vm_carbon_stock_croparea` (NOT `vm_carbon_stock`); M29 folds it in (`29_cropland/simple_apr24/equations.gms:31`, `detail_apr24/equations.gms:40`). M58 does NOT populate `vm_carbon_stock` (grep empty, positive control passed). Doc's croparea/peatland caveat is CORRECT. ✅

### Other interface variables
- `vm_emissions_reg`: DECLARED M56 (declarations.gms:40); POPULATED by M51 (`rescaled_jan21`), M52 (`normal_dec17/equations.gms:17`, co2_c oneoff), M53 (`ipcc2006_aug22`), M57 (`on_aug22`), M58 (`v2/equations.gms:92`, peatland). Doc's "51 N2O, 52 LULUCF CO2, 53 CH4, 57 MACC-adjusted, 58 peatland" is CORRECT. ✅
- `vm_emission_costs` → M11 objective (`11_costs/default/equations.gms:26`). ✅
- `vm_reward_cdr_aff` → M11 with negative sign (`11_costs/default/equations.gms:27`). ✅
- `vm_cdr_aff` DECLARED+POPULATED M32 (`dynamic_may24/declarations.gms:83`, `equations.gms:37,42`); read by M56 at equations.gms:77. ✅
- `pm_interest` declared M12 (`12_*/declarations.gms:9`); read by M56 at equations.gms:52,78. ✅

### Defaults (verified in input.gms AND config/default.cfg)
| Param | Doc | input.gms | default.cfg | OK |
|---|---|---|---|---|
| realization | price_aug22 (only) | ls confirms only price_aug22/ | — | ✅ |
| s56_buffer_aff | 0.5 | :71 / 0.5 / | :1767 = 0.5 | ✅ |
| s56_c_price_exp_aff | 50 | :70 / 50 / | :1760 = 50 | ✅ |
| s56_minimum_cprice | 3.67 | :67 / 3.67 / | :1729 = 3.67 | ✅ |
| s56_limit_ch4_n2o_price | 4920 | :65 / 4920 / | :1780 = 4920 | ✅ |
| s56_cprice_red_factor | 1 | :66 / 1 / | :1620 = 1 | ✅ |
| s56_c_price_induced_aff | 1 | :69 / 1 / | :1741 = 1 | ✅ |
| s56_ghgprice_devstate_scaling | 0 (OFF) | :68 / 0 / | :1616 = 0 | ✅ |
| s56_ghgprice_fader | 0 (OFF) | :75 / 0 / | :1623 = 0 | ✅ |
| s56_fader_start / end / target | 2035/2050/1 | :76-78 | :1627/1629/1631 | ✅ |
| c56_emis_policy | reddnatveg_nosoil | :86 setglobal | :1810 | ✅ |
| c56_pollutant_prices | R34M410-SSP2-NPi2025 | :84 setglobal | :1713 | ✅ |
| c56_carbon_stock_pricing | actualNoAcEst | :90 setglobal | :1817 | ✅ |
| c56_cprice_aff | secdforest_vegc | :87 setglobal | :1754 | ✅ |
| c56_mute_ghgprices_until | y2030 | :88 setglobal | :1726 | ✅ |
| sm_fix_SSP2 | 2025 | — | :225 = 2025 | ✅ |

### Counts / citations
- LOC = 709 (sum of 8 price_aug22 files: 64+79+117+67+123+34+11+214). ✅
- "100+" price scenarios — `ghgscen56` = **101** members (sets.gms:15-117). ✅
- 5 named price scenarios all exist in `ghgscen56` (R34M410-SSP2-NPi2025 @73, -PkBudg650 @75, -PkBudg1000 @74, SSPDB-SSP2-19-REMIND-MAGPIE @93, SSPDB-SSP2-Ref-REMIND-MAGPIE @103). ✅
- declarations.gms citations 9/11/34/39/43 all land on the claimed identifier. ✅
- Preloop stage citations (35-45, 50-51, 53-63, 65-67, 69-74, 76-82, 84-91, 93-123) all map to the correct code blocks. ✅
- `stockType` set = {actual, actualNoAcEst} (sets.gms:212-213). ✅
- CH4 GWP 28, N2O GWP 265 (AR5), conversion factors 12/44 and 44/28 — confirmed in preloop.gms:77-81 comments + formulae. ✅

---

## BUGS

### BUG m56-emis-01 — "60+ policy scenarios" (actual: 44) [MAJOR]
- **Class**: Hardcoded counts drift (Pattern 6) / fabricated set count.
- **Trigger** (§1 Major): "Fabricated count for a set/parameter/realization list."
- **Doc lines**: module_56.md:37, :494, :636, :1063 ("60+ policies" / "60+ policy scenarios"); :797 ("60 policies ... = 6000 combinations from 160 data files").
- **Claim**: e.g. line 636 "Module 56 provides 100+ price scenarios and 60+ policy scenarios."
- **Reality**: `scen56` (emission policy scenarios) has exactly **44** members.
- **Evidence**: `/tmp/magpie_develop_ro/modules/56_ghg_policy/price_aug22/sets.gms:119-163`.
- **verify_cmd**: `awk 'NR>=120 && NR<=163' sets.gms | tr ',' '\n' | sed 's#/##g;s/[[:space:]]//g' | grep -vE "^$" | wc -l` → **44**.
- **Confirmed**: YES.
- **Fix**: Replace every "60+ policy scenarios" / "60+ policies" with "44 policy scenarios" (or "40+"). At line 797 change "60 policies × 100 scenarios = 6000 combinations from 160 data files" to "44 policies × 101 scenarios ≈ 4400 combinations from ~145 data files" (or drop the spurious file-count). At line 1063 change "60+ policy scenarios" to "44 policy scenarios."

### BUG m56-emis-02 — `im_pollutant_prices` consumer omission: M57 not listed [MAJOR]
- **Class**: Interface-parameter consumer omission (MANDATE 13; R20-class).
- **Trigger** (§1 Major): consumer-set incompleteness for an interface parameter (R20 anchor: doc omits consumers a refactorer would miss).
- **Doc line**: module_56.md:675-677 (Section 6.1 documents `im_pollutant_prices` — "Constructed in preloop" — with no consumer list; M57 never appears as a consumer of it anywhere in the doc).
- **Claim**: doc treats `im_pollutant_prices` as an M56-internal pricing parameter only.
- **Reality**: `im_pollutant_prices` (declared M56:9) is READ by **M57 (maccs)** to set MACC abatement steps.
- **Evidence**: `/tmp/magpie_develop_ro/modules/57_maccs/on_aug22/preloop.gms:24-25` (`i57_mac_step_n2o ... im_pollutant_prices(t,i,"n2o_n_direct",emis_source)...` and `i57_mac_step_ch4 ... im_pollutant_prices(t,i,"ch4",...)`).
- **verify_cmd**: `rg -ln "im_pollutant_prices" modules/*/*/*.gms | grep -v 56_ghg_policy` → `57_maccs/on_aug22/preloop.gms` (positive control: `rg p56_fader_cpriceaff` in same M57 file = no match, search works).
- **Confirmed**: YES.
- **Fix**: In Section 6.1 (after the `im_pollutant_prices` entry, ~line 677) add: "**Consumed by:** Module 57 (MACCs) reads `im_pollutant_prices` to set MACC abatement steps (`modules/57_maccs/on_aug22/preloop.gms:24-25`), in addition to the within-M56 cost equations." (Severity reflects that the doc makes no false exhaustive-consumer claim, but omits a direct cross-module consumer per MANDATE 13.)

### BUG m56-emis-03 — Section 9.2 N2O cap arithmetic wrong ($499,320 vs 558,771) [MINOR]
- **Class**: Conceptual pseudo-code / wrong number in illustration.
- **Trigger** (§1 Minor): "Wrong detail, but a careful reader wouldn't be misled into action" — it is a sanity-check threshold, and the doc itself states the correct value elsewhere.
- **Doc line**: module_56.md:833 ("Max N2O-N price ≤ 4920 × 12/44 × 265 × 44/28 ≈ $499,320/Tg N").
- **Reality**: 4920 × 12/44 × 265 × 44/28 = 4920 × 12 × 265 / 28 = **558,771** (the 44s cancel). The doc's OWN Limitations section (line 1109) states "N2O-N cap ~= 558,771 USD/tN" — internal contradiction.
- **verify_cmd**: `python3 -c "print(4920*12/44*265*44/28)"` → 558771.4...
- **Confirmed**: YES.
- **Fix**: line 833 → "≈ $558,771/Tg N".

### BUG m56-emis-04 — Section 9.2 CH4 cap arithmetic wrong ($37,709 vs 37,571) [MINOR]
- **Class**: Wrong number in illustration.
- **Trigger** (§1 Minor): illustrative threshold; doc states correct value elsewhere.
- **Doc line**: module_56.md:832 ("Max CH4 price ≤ 4920 × 12/44 × 28 ≈ $37,709/Tg CH4").
- **Reality**: 4920 × 12/44 × 28 = **37,571**. Doc's Limitations (line 1109) states "CH4 cap ~= 4920*12/44*28 ~= 37,571 USD/tCH4" — internal contradiction.
- **verify_cmd**: `python3 -c "print(4920*12/44*28)"` → 37570.9...
- **Confirmed**: YES.
- **Fix**: line 832 → "≈ $37,571/Tg CH4".

### BUG m56-emis-05 — "15 pollutants" (actual: 16) [MINOR]
- **Class**: Hardcoded counts drift (Pattern 6).
- **Trigger** (§1 Minor): off-by-one count in an illustrative dimension statement.
- **Doc line**: module_56.md:494 ("Dimensions: 60+ policies × 15 pollutants × 20+ emission sources").
- **Reality**: the f56_emis_policy table is indexed on `pollutants_all`, which has **16** members (co2_c, ch4, n2o_n_direct, nh3_n, no2_n, no3_n, n2o_n_indirect, co, nmhc, h2, pm2_5, tpm, tc, oc, bc, so2).
- **Evidence**: `/tmp/magpie_develop_ro/modules/56_ghg_policy/price_aug22/sets.gms:171-185`; table index `pollutants_all` at input.gms:113.
- **verify_cmd**: `awk 'NR>=172 && NR<=185' sets.gms | tr ',' '\n' | sed 's#/##g;s/[[:space:]]//g' | grep -vE "^$" | wc -l` → 16.
- **Confirmed**: YES.
- **Fix**: line 494 → "44 policies × 16 pollutants × 31 emission sources" (also corrects the 60+ and makes the source count exact: `emis_source` = 31).

### BUG m56-emis-06 — Section 7.2 attributes CDR *reward* to M35 [MINOR]
- **Class**: Producer/mechanism mis-attribution (MANDATE 18, softened — prose).
- **Trigger** (§1 Minor, tie-breaker down from Major): the claim is in a "what it does NOT do" prose bullet; broader "sequestration is M32/M35/M52" is defensible, but the CDR *reward* input is M32-only.
- **Doc line**: module_56.md:720 ("**DOES reward** CDR calculated by Module 32 (Forestry) and Module 35 (Natural Vegetation)").
- **Reality**: the CDR reward `vm_reward_cdr_aff` (q56_reward_cdr_aff) is driven exclusively by `vm_cdr_aff`, which is produced ONLY by M32. M35 natural-vegetation carbon enters via `vm_carbon_stock` (priced through the CO2 stock-change pathway), NOT via the CDR reward.
- **Evidence**: `vm_cdr_aff` populated only in `32_forestry/dynamic_may24/equations.gms:37,42`; absent from all M35 files.
- **verify_cmd**: `rg -n "vm_cdr_aff\(" modules/*/*/equations.gms` → only M32 (LHS) + M56 (RHS read).
- **Confirmed**: YES (M32-only producer).
- **Fix**: line 720 → "**DOES reward** CDR calculated by Module 32 (Forestry) via `vm_cdr_aff`. (Module 35 natural-vegetation regrowth carbon is priced via the `vm_carbon_stock` CO2 stock-change pathway, not via this reward.)"

### BUG m56-emis-07 — Section 8.1: 1995 "emissions ... zeroed via preloop.gms:70" (line 70 zeroes prices) [MINOR]
- **Class**: Content-level citation mismatch (Pattern 12).
- **Trigger** (§1 Minor): the practical outcome (zero 1995 cost) is right, but the stated mechanism is imprecise.
- **Doc line**: module_56.md:757 ("emissions are initialization artifacts → zeroed via `preloop.gms:70`").
- **Reality**: `preloop.gms:70` zeroes `im_pollutant_prices` for years ≤ sm_fix_SSP2 — it zeroes the PRICE (hence the cost), not the emissions. The 1995 carbon stock is an estimate (preloop.gms:8-11; code comment "emissions in 1995 are not meaningful"); the emissions themselves are not zeroed by line 70.
- **Evidence**: `/tmp/magpie_develop_ro/modules/56_ghg_policy/price_aug22/preloop.gms:70` (`im_pollutant_prices(...)$(m_year(t_all) <= sm_fix_SSP2) = 0;`).
- **verify_cmd**: `sed -n '70p' preloop.gms`.
- **Confirmed**: YES.
- **Fix**: line 757 → "First time step (1995) has no previous stock → emissions are initialization artifacts (`preloop.gms:8-11`: 'emissions in 1995 are not meaningful') → their **cost** is zero because GHG prices are zeroed for years ≤ sm_fix_SSP2 (`preloop.gms:70`)."

### BUG m56-emis-08 — `vm_emission_costs` consumer omission: M15 (tax recycling) not listed [MINOR]
- **Class**: Interface-variable consumer omission (MANDATE 13/20, solution-level read).
- **Trigger** (§1 Minor): a `.l` recycling read in the default food realization; primary consumer (M11) is correctly stated, so low harm.
- **Doc line**: module_56.md:565 + :1017 (Section 4.1 / 12.1 list only Module 11 as the consumer of `vm_emission_costs`).
- **Reality**: M15 (food, default realization `anthro_iso_jun22`) reads `vm_emission_costs.l` for `p15_tax_recycling`.
- **Evidence**: `/tmp/magpie_develop_ro/modules/15_food/anthro_iso_jun22/intersolve.gms:23`; default food realization confirmed at default.cfg:410.
- **verify_cmd**: `rg -n "vm_emission_costs" modules/*/*/*.gms` → M11 equations.gms:26 (objective) + M15 intersolve.gms:23 (`.l` recycling).
- **Confirmed**: YES (verified direct `.l` consumer; secondary use).
- **Fix**: Optional — add to Section 4.1: "Also read post-solve by Module 15 (food) as `vm_emission_costs.l` for GHG-tax revenue recycling (`modules/15_food/anthro_iso_jun22/intersolve.gms:23`)."

---

## Informational

- **module_56.md:1137** "Depends on: Modules 52 (carbon stocks), 53 (methane), 51 (N₂O)" — understates dependencies relative to the doc's OWN body (Sections 4.2/12 correctly add M57, M58, M32, M12, and the carbon-stock populators 29/31/34/35/59). This "Participates In → Dependency Chains" line appears to be legacy centrality metadata. Consider aligning with Section 12.

---

## Deferred (NOT code-verifiable in this worktree; no edit proposed)

- **f56_emis_policy.csv content claims** (lines 499, 506-508, 656-665, 967, and the "reddnatveg_nosoil prices vegc+litc for primforest/secdforest/other + peatland; routes ag CH4/N2O" details): the CSV is NOT present in the worktree (`modules/56_ghg_policy/input/` contains only `files`; populated from input.tgz at runtime). The doc's "Verified from f56_emis_policy.csv" claims could not be confirmed or refuted. **Plausible** given the `scen56`/`pollutants_all`/`emis_source` set membership, but the 0/1 matrix entries are unread. Do NOT edit.
- **Price-level values** in the Section 5.1 table (~$0/$300/$800 etc.) and the "~$0/tC for NPi2025" claim: require `f56_pollutant_prices.cs3` (not in worktree). Doc flags them "Approximate". Do NOT edit.
- **"R34M410-SSP2-NPi2025 (No Policy Improvement)"** (line 959): NPi conventionally = "(current) National Policies implemented", not "No Policy Improvement". Not defined in the GAMS code; acronym semantics are external. Flag-only, do NOT edit without a non-code source.
- **Centrality "Rank #3", "Provides to: 13 modules", "Affects 13 modules"** (lines 1134-1148): agent-internal dependency-analysis metadata, not derivable from a clean code grep. Direct variable-level downstream consumers of M56's cost outputs are M11 (+M15 `.l`). Do NOT edit (would need the centrality artifact).
- **Circular dependency "56 → 32 → 10 → 52 → 56"** (line 1141): cross_module claim, deferred to `circular_dependency_resolution.md`.
- **"at least 11 distinct operations" in preloop** (line 322): vague/hedged; not a hard count claim.
- **Limitation 2 simplification** ("CH4 from enteric fermentation, N2O from soils", line 1111): high-level limitation prose; the fuller source list is correctly given in Section 5.2. Acceptable simplification, no edit.

---

## Mechanical checks (doc-as-artifact)
- M1 file:line citations — present and overwhelmingly accurate. PASS.
- M2 realization stated — yes (price_aug22, single realization noted). PASS.
- M3 variable prefixes — all valid (vm_/v56_/im_/p56_/s56_/c56_/pcm_/pm_). PASS.
- Equation-name fidelity — all 7 correct. PASS.
- Citation drift — none material (all spot-checked land on claimed content).
