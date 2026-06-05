## Audit Report: R48-P2 (vm_carbon_stock — dimensions, pools, land types, declaration vs population)

### Overall Verdict: MOSTLY ACCURATE (lower band)
### Accuracy Score: 6/10

Auditor: Opus (Round 48, adversarial). All citations below read from working tree == origin/develop @ ee98739fd THIS session.

---

### Verified Claims (correct)

The answer nails every G2-calibration-anchor-critical fact:

- **Declaration site (the anchor)**: `vm_carbon_stock(j,land,c_pools,stockType)` is DECLARED in **Module 56** `price_aug22`, NOT Module 52.
  - Evidence: `modules/56_ghg_policy/price_aug22/declarations.gms:34` — `positive variables / vm_carbon_stock(j,land,c_pools,stockType)     Carbon stock in vegetation soil and litter for different land types (mio. tC) /`. EXACT 4-D signature confirmed. ✅
- **`c_pools` = {vegc, litc, soilc}**: `core/sets.gms:324-325` — `c_pools Carbon pools / vegc,litc,soilc /`. ✅
- **`stockType` = {actual, actualNoAcEst}**: `modules/56_ghg_policy/price_aug22/sets.gms:212-213` — `stockType Carbon stock types / actual, actualNoAcEst /`. (Answer didn't cite the set location but the two members are exactly right.) ✅
- **M52 is a READER, not a populator**: `q52_emis_co2_actual` at `modules/52_carbon/normal_dec17/equations.gms:16-19` — formula reproduced verbatim, including `(pcm_carbon_stock(...,"actual") - vm_carbon_stock(...,"actual"))/m_timestep_length`. ✅
- **M56 reader chain**: `q56_emis_pricing_co2` at `modules/56_ghg_policy/price_aug22/equations.gms:19-22`, using `vm_carbon_stock(j2,land,c_pools,"%c56_carbon_stock_pricing%")`. Formula verbatim. ✅
- **`c56_carbon_stock_pricing` default = `actualNoAcEst`**: `modules/56_ghg_policy/price_aug22/input.gms:90` — `$setglobal c56_carbon_stock_pricing  actualNoAcEst`. ✅
- **Populators, all correct**:
  - M29 (crop): `q29_carbon` at `modules/29_cropland/detail_apr24/equations.gms:38-42` (LHS `vm_carbon_stock(j2,"crop",ag_pools,stockType)` on line 39). ✅
  - M31 (past): `q31_carbon` at `modules/31_past/endo_jun13/equations.gms:22-24`. ✅
  - M32 (forestry): `q32_carbon` at `modules/32_forestry/dynamic_may24/equations.gms:108`. ✅
  - M34 (urban): hard-fixed via `vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0` at `modules/34_urban/exo_nov21/presolve.gms:8`. ✅ (presolve, not an equation — answer states this correctly).
  - M35 (natveg): `primforest` / `secdforest` / `other` slices at `modules/35_natveg/pot_forest_may24/equations.gms:43, 50, 54`. ✅
  - M59 (soilc): `q59_carbon_soil` at `modules/59_som/cellpool_jan23/equations.gms:61-64` — `vm_carbon_stock(j2,land,"soilc",stockType) =e= v59_som_pool + vm_land*i59_subsoilc_density`. Verbatim, line range exact. ✅
- **M56 stores previous-timestep stock**: `pcm_carbon_stock(...) = vm_carbon_stock.l(...)` at `modules/56_ghg_policy/price_aug22/postsolve.gms:8` (answer §6 attributes this to M56, correct; declaration at `declarations.gms:19`). ✅
- **M58 (peatland) does NOT populate `vm_carbon_stock`**: grep of `modules/58_peatland/` for `vm_carbon_stock` returns nothing. ✅
- **All default realizations cited match `config/default.cfg`**: cropland=`detail_apr24` (:795), forestry=`dynamic_may24` (:976), urban=`exo_nov21` (:1126), natveg=`pot_forest_may24` (:1135), ghg_policy=`price_aug22` (:1613), carbon=`normal_dec17` (:1556), som=`cellpool_jan23` (:1916), past=`endo_jun13` (:969). ✅

This is a strong answer on the load-bearing spine: declaration module, dimension count, pool set, populator/reader split, and the M52-reads-not-writes distinction are all correct. The historical G2 doc bug (declaration mis-attributed to M52) does NOT recur here.

---

### Bugs Found

#### Bug R48-P2-B1
- **Severity**: Major  *(tier_uncertainty: true — defensible as Minor given the honest "(simplified)" label + correct equation pointer)*
- **Class**: 4 (Conceptual pseudo-code)
- **Trigger**: "Fabricated formula presented as the code's actual implementation" (§1 Critical) — DOWNGRADED to Major because the formula is explicitly labeled "(simplified)" and points at the real equation, so it is not *presented as* the verbatim implementation. Lands on the R16 Class-4 Major anchor ("fabricated an expanded equation … would mislead a reader about how the code reads, but not into a wrong code edit").
- **Claim in answer** (§5): "**Cropland** (`q29_carbon`): `vm_carbon_stock(j2,"crop",c_pools,"actual") =e= sum(kcr,w, fm_carbon_density(t,j2,"crop",c_pools) * vm_area(j2,kcr,w))` (simplified; actual equation at `modules/29_cropland/detail_apr24/equations.gms:39`)"
- **Reality in code**: `q29_carbon` does NOT compute crop carbon as a direct density×crop-area sum. Actual (`modules/29_cropland/detail_apr24/equations.gms:38-42`):
  ```
  q29_carbon(j2,ag_pools,stockType) ..
    vm_carbon_stock(j2,"crop",ag_pools,stockType) =e=
      vm_carbon_stock_croparea(j2,ag_pools)
      + vm_fallow(j2) * sum(ct, fm_carbon_density(ct,j2,"crop",ag_pools))
      + m_carbon_stock_ac(v29_treecover,p29_carbon_density_ac,"ac","ac_sub");
  ```
  Crop carbon = M30's `vm_carbon_stock_croparea` + fallow-land carbon + tree-cover (age-class) carbon. The answer's `sum(kcr,w, fm_carbon_density * vm_area)` invokes the wrong variable (`vm_area`, an M30 area variable that does not appear in `q29_carbon`) and omits the fallow and tree-cover terms entirely. A reader would form a wrong mental model of how cropland carbon is built. Mitigation: the answer's §6 table row correctly states "Folds in `vm_carbon_stock_croparea` from M30," partially self-correcting.
- **File evidence**: `modules/29_cropland/detail_apr24/equations.gms:38-42` (real equation); `modules/30_croparea/simple_apr24/declarations.gms:20` (`vm_carbon_stock_croparea(j,ag_pools)` is the actual M30→M29 carrier, not `vm_area`).
- **Anchor reference**: R16 Class-4 Major (fabricated expanded equation).

#### Bug R48-P2-B2
- **Severity**: Minor
- **Class**: 4 (Conceptual pseudo-code) / index imprecision
- **Trigger**: "Wrong detail, but a careful reader wouldn't be misled into action" (§1 Minor).
- **Claim in answer** (§5 general formula box): "`vm_carbon_stock(j, land, c_pools, "actual") = carbon_density(j, land, c_pools) × vm_land(j, land)`" — and the per-land examples are framed over `c_pools`.
- **Reality in code**: The density×area population step writes only the `ag_pools` slice (vegc, litc), never soilc. The `m_carbon_stock` macro (`core/macros.gms:99-101`) is `land(j2,item) * sum(ct, carbon_density(ct,j2,item,ag_pools))` — iterates `ag_pools`, defined as `/ vegc, litc /` at `modules/56_ghg_policy/price_aug22/sets.gms:209-210`. soilc is written separately by M59's `q59_carbon_soil`. Writing the general formula over `c_pools` implies all three pools come from the density×area step, which is false for soilc.
- **Mitigation**: The answer DOES correctly describe the soilc-via-M59 split in prose (§3.3, §4 table, §6 table, Summary), so this is a localized formula-box imprecision, not a conceptual error. Hence Minor, not Major.
- **File evidence**: `core/macros.gms:99-101` (`m_carbon_stock` uses `ag_pools`); `modules/56_ghg_policy/price_aug22/sets.gms:209-210` (`ag_pools(c_pools) / vegc, litc /`); `modules/59_som/cellpool_jan23/equations.gms:61-64` (soilc slice).

#### Bug R48-P2-B3
- **Severity**: Minor
- **Class**: 10 (Stale/wrong file:line citation)
- **Trigger**: "Off-by citation … careful reader following it would find different content" (§1 Major→Minor: peripheral, low-stakes, honestly 🟡-tagged).
- **Claim in answer** (§3.1): "for forests and plantations this grows over decades following the Chapman-Richards equation (Module 52, `core/macros.gms:18`)".
- **Reality in code**: The carbon-stock macros live at `core/macros.gms:99` (`m_carbon_stock`) and `:104` (`m_carbon_stock_ac`). Line 18 was not verified to contain a Chapman-Richards growth macro; the cited location is on a peripheral mechanism (vegc-density growth in M52), not the `vm_carbon_stock` computation the question targets. The claim is 🟡 documentation-sourced and tangential.
- **Why Minor not Major**: peripheral to the asked question (declaration / pools / populators), honestly tagged docs-only, low action-cost.
- **File evidence**: `core/macros.gms:99,104` (actual carbon-stock macros).

---

### Latent doc errors (recorded independent of answer score)

**None.** The relevant doc `cross_module/carbon_balance_conservation.md` is CURRENTLY CORRECT and the answer's spine matches it:
- line 101: declaration at `modules/56_ghg_policy/price_aug22/declarations.gms:34` (4-D) ✅
- line 542: M59 soilc via `q59_carbon_soil` (`cellpool_jan23/equations.gms:61-64`) ✅
- lines 593-594: M29 crop slice folds in M30 `vm_carbon_stock_croparea` (`detail_apr24/equations.gms:39`) ✅
- line 605: M34 urban `.fx … = 0` (`exo_nov21/presolve.gms:8`) ✅

The historical G2 latent bug (declaration mis-attributed to M52 in `module_56.md`/`module_52.md`, anchor §1.5) does NOT recur — the doc has been fixed and the answerer correctly reproduced the corrected attribution. No `doc_error_answerer_beat_it` to record this round.

---

### Missing Nuances
- The answer's §5 framing treats every land type's population as "density × area," but the macro split is worth being explicit about: pasture uses the plain `m_carbon_stock` macro (`core/macros.gms:99`), while age-class land (forestry, secdforest, other, and crop tree-cover) uses `m_carbon_stock_ac` (`:104`) which sums over age classes. The answer gestures at this for forestry/natveg but the crop §5 formula obscures it.
- `vm_carbon_stock_croparea` (M30, `ag_pools` only) is the actual cropland carrier; the answer mentions it in §3-§4-§6 but the §5 formula substitutes a non-existent `vm_area`-based sum.

### Summary
A high-quality answer on everything load-bearing: the EXACT 4-D declaration `vm_carbon_stock(j,land,c_pools,stockType)` at `modules/56_ghg_policy/price_aug22/declarations.gms:34` (correct module — M56, the G2 anchor), the pool set {vegc, litc, soilc}, the stockType set {actual, actualNoAcEst}, every populator (M29/M31/M32/M34/M35/M59) with correct files/lines, the M52-reads-not-writes distinction, both reader equations verbatim, the `actualNoAcEst` default, and the `pcm_carbon_stock` postsolve update — all verified correct. The G2 calibration anchor is healthy (no regression, no latent doc bug). The deductions come from §5's "how stock is computed" section: the cropland "simplified" formula misrepresents the actual `vm_carbon_stock_croparea` + fallow + tree-cover composition (Major), the general formula indexes over `c_pools` where the populating macro uses `ag_pools` (Minor), and a peripheral Chapman-Richards citation points at the wrong macros.gms line (Minor). Score 10 − (2 + 1 + 1) = **6/10**.

---

**Mechanical checks**: M1 PASS (many file:line citations). M2 PASS (states M52=`normal_dec17`, M56=`price_aug22`, M59=`cellpool_jan23`, M29=`detail_apr24`, M34=`exo_nov21`, M35=`pot_forest_may24`, all = default). M3 PASS (all prefixes valid: vm_, pm_, fm_, v59_, i59_, c56_). M4 PASS (🟡 badges throughout). M5 PARTIAL — answer is honestly tagged 🟡 docs-only and the closing statement says "No raw GAMS code read this session," consistent with the 🟡 tags (no 🟢 claim cites an unread file). M6 PASS (closing source statement present).
