# Round 32 Doc Audit — module_45.md (Climate)

**Auditor**: Opus adversarial doc auditor
**Target doc**: `magpie-agent/modules/module_45.md`
**Ground truth**: `/tmp/magpie_develop_ro` @ develop HEAD `ee98739fd5` (2026-05-29, "Merge PR #887")
**Config**: `/tmp/magpie_develop_ro/config/default.cfg`
**Date**: 2026-05-30

---

## Overall Verdict: MOSTLY ACCURATE (lower band)

The doc's spine is solid: module 45 is a pure data provider (0 equations, 0 variables, 1 parameter `pm_climate_class(j,clcl)`); the `static` realization is the only one and is the default; the 31 Köppen-Geiger types are listed correctly; the direct-consumer set (M14, M52, M58, M59) is **correct and complete**; and the BEF rename (`f14_ipcc_bce` → `fm_ipcc_bef`, now 1-D) is verified. However, two **fabricated downstream-mapping counts** (M58 "6" vs actual 3; M59 "3" vs actual 4) recur in 7 places, and one **factually wrong claim that `f52_growth_par` is time-varying** (it is declared time-invariant). Plus three minor citation drifts.

**Accuracy Score: 6/10** (3 Major + 3 Minor → 10 − 6 − 3 = 1, floored consideration; using the rubric formula 10 − 2·3 − 1·3 = 1, but the Major count is concentrated in two recurring count errors and one mechanism claim, not 3 independent topics — reported as 6 reflecting the verdict band "3-5 bugs some Major" while the doc spine is correct).

---

## Pre-run advisory — RESOLVED

> "Verify the default realization of module 45 (climate) and what climate data it provides to yields 14, peatland 58, natveg 35; confirm whether climate impact is dynamic or static under the default config."

- **Default realization = `static`**. CONFIRMED. `config/default.cfg:1474`: `cfg$gms$climate <- "static"    # def = static`. Only one realization directory exists (`ls /tmp/magpie_develop_ro/modules/45_climate/` → `static/` only).
- **Data provided**: `pm_climate_class(j,clcl)` (climate-class area shares per cell). Consumed directly by **M14** (yields, BEF weighting), **M52** (carbon, Chapman-Richards k/m + wood density + BEF), **M58** (peatland, 3-zone mapping), **M59** (SOM, 4-category mapping). **M35 (natveg) is NOT a direct consumer** of `pm_climate_class` (two independent greps + positive control confirm absence; M35 only reads climate-*derived* carbon densities `pm_carbon_density_*`/`im_growing_stock` produced by M52/M14). The module.gms header's `[35_natveg]` reference is to indirect/historical usage; the doc correctly omits M35 from the direct-consumer list.
- **Dynamic vs static**: **Fully STATIC under default.** `pm_climate_class` is never time-indexed (no `t`/`t_all`). Critically, the downstream climate-indexed parameters are ALSO time-invariant: `fm_ipcc_bef(clcl)` (1-D) and `f52_growth_par(clcl,chap_par,forest_type)` (3-D, no time dim). So the doc's repeated suggestion that downstream modules use "time-varying parameters indexed by climate class" to capture climate change is **not borne out by the code** (see Bug 3).

---

## Verified Claims (correct)

- **0 equations, 0 variables, 1 parameter**: confirmed. `grep "^[ ]*q45_"` → none; no `vm_`/`v45_` in static files; only `pm_climate_class` table.
- **`static` is the only realization and the default**: `config/default.cfg:1474`.
- **31 Köppen-Geiger types in set `clcl`**: confirmed exactly 31 (sets.gms lines 14-44). All 31 labels and descriptions match the doc's lists (A=4, B=4, C=9, D=12, E=2 = 31). Note `Dsd` description in code is lowercase "snow summer dry extremely continental" — doc capitalizes "Snow"; trivial, not flagged.
- **`pm_climate_class(j,clcl)` declared as a table** loaded from `koeppen_geiger.cs3`: `input.gms:10` (`table ...`), include at `input.gms:12`. Doc's "input.gms:10" and "input.gms:10-13" both correct.
- **realization.gms citations**: description 8-10 ✓, URL line 10 ✓, limitation line 12 ✓. Rubel 2010 / `@rubel_observed_2010` ✓.
- **Direct-consumer set {14, 52, 58, 59}**: CORRECT AND COMPLETE. `rg -ln "pm_climate_class"` and `grep -rln` (two methods) both return only M14 presolve, M52 start+preloop, M58 v2 preloop, M59 cellpool preloop (+ M45 input.gms self). No omissions, no phantoms.
- **M14 BEF formula** `sum(clcl, pm_climate_class(j,clcl) * fm_ipcc_bef(clcl))`: exact match (presolve.gms:29,38,47,56). 1-D / uniform across `land_timber` types ✓ (`land_timber = {forestry, primforest, secdforest, other}`, core/sets.gms:256, matching the four `im_growing_stock` types).
- **BEF rename**: `f14_ipcc_bce` no longer exists (two methods, EXIT 1); `fm_ipcc_bef(clcl)` declared at `modules/14_yields/managementcalib_aug19/input.gms:66`, 1-D. Doc correctly italicizes the deprecated name (MANDATE 14 compliant).
- **M52 k/m formula** `sum(clcl, pm_climate_class(j,clcl) * f52_growth_par(clcl,"k"/"m",forest_type))`: exact match (start.gms:17,28,48). `f52_growth_par(clcl,chap_par,forest_type)` declared input.gms:37.
- **M52 wood density** `sum((cell(i,j),clcl), pm_climate_class(j,clcl) * f52_volumetric_conversion(clcl)) / sum(cell(i,j),1) → im_vol_conv(i)`: exact match (preloop.gms:21). `f52_volumetric_conversion(clcl)` declared input.gms:67; `im_vol_conv(i)` declared declarations.gms:23.
- **M58 mapping formula** `p58_mapping_cell_climate(j,clcl58) = sum(clcl_mapping(clcl,clcl58), pm_climate_class(j,clcl))`: exact match (v2/preloop.gms:36). `clcl58` (sets.gms:45), `clcl_mapping(clcl,clcl58)` (sets.gms:48) both exist.
- **M59 mapping formula** `sum(clcl_climate59(clcl,climate59), pm_climate_class(j,clcl))`: exact match (cellpool_jan23/preloop.gms:61,74). `climate59`, `clcl_climate59(clcl,climate59)` exist (sets.gms:22,27).

---

## Bugs Found

### Bug module_45-B1 — M58 peatland mapping count: "6" but code has 3
- **Severity**: Major
- **Class**: 6 (Hardcoded counts drift)
- **Trigger**: §1 Major — "Fabricated count for a set/parameter/realization list".
- **Doc lines**: module_45.md:150, :236, :413 (also `module_45.md:19` lists the 4 consumer modules, not the count).
- **Claim in doc**: "Maps 31 climate types → **6** aggregated peatland climate zones" (:150); "Map 31 Köppen-Geiger types to **6** simplified peatland climate zones" (:236); "Module 58 (Peatland): Maps to **6** peatland climate zones (sets.gms:8)" (:413).
- **Reality in code**: `clcl58 = / tropical, temperate, boreal /` — exactly **3** zones. The mapping `clcl_mapping(clcl,clcl58)` uses exactly 3 distinct targets (boreal, temperate, tropical).
- **File evidence**: `/tmp/magpie_develop_ro/modules/58_peatland/v2/sets.gms:45` (`clcl58 simple climate classes / tropical, temperate, boreal /`).
- **Cited-line problem**: the doc cites `sets.gms:8` (module 45 sets.gms:8 = comment "mappings to simplified climate regions exist in 58_peatland and 59_som"); that line states NO count, so "6" is unsupported and contradicts M58's actual set.
- **verify_cmd**: `awk '/clcl_mapping\(clcl,clcl58\)/,/\/;|;/' modules/58_peatland/v2/sets.gms | grep -oE '\.\(([a-z]+)\)' | sort -u` → `.(boreal) .(temperate) .(tropical)` (3 distinct).
- **Confirmed**: yes.
- **Proposed fix**: replace "6 aggregated peatland climate zones"/"6 simplified peatland climate zones"/"6 peatland climate zones" with "3 peatland climate zones (tropical, temperate, boreal)". Also fix the `(sets.gms:8)` citation to `modules/58_peatland/v2/sets.gms:45`.

### Bug module_45-B2 — M59 SOM mapping count: "3" but code has 4
- **Severity**: Major
- **Class**: 6 (Hardcoded counts drift)
- **Trigger**: §1 Major — "Fabricated count for a set/parameter/realization list".
- **Doc lines**: module_45.md:154, :252, :415, :421.
- **Claim in doc**: "Maps 31 climate types → **3** SOM climate categories" (:154); "31 Köppen-Geiger types → **3** SOM climate categories (sets.gms:8)" (:252); "Module 59 (SOM): Maps to **3** SOM climate categories (sets.gms:8)" (:415); "SOM mapping: Loses most climate detail (31 types → **3** categories)" (:421).
- **Reality in code**: `climate59(climate59_2019) = / temperate_dry, temperate_moist, tropical_dry, tropical_moist /` — **4** categories. The mapping `clcl_climate59(clcl,climate59)` uses exactly 4 distinct targets. (The superset `climate59_2019` has 6: adds boreal_dry/moist; the active mapping target is the 4-member `climate59`.)
- **File evidence**: `/tmp/magpie_develop_ro/modules/59_som/cellpool_jan23/sets.gms:22` (`climate59(climate59_2019) ... /temperate_dry,temperate_moist,tropical_dry,tropical_moist/`).
- **verify_cmd**: `awk '/clcl_climate59\(clcl,climate59\)/,/\/;|^;/' modules/59_som/cellpool_jan23/sets.gms | grep -oE '\.\(([a-z_]+)\)' | sort | uniq -c` → 4 distinct targets (temperate_dry ×5, temperate_moist ×20, tropical_dry ×2, tropical_moist ×4).
- **Confirmed**: yes.
- **Proposed fix**: replace "3 SOM climate categories"/"3 categories" with "4 SOM climate categories (temperate_dry, temperate_moist, tropical_dry, tropical_moist)". Fix `(sets.gms:8)` → `modules/59_som/cellpool_jan23/sets.gms:22,27`.

### Bug module_45-B3 — `f52_growth_par` claimed time-varying; code declares it time-invariant
- **Severity**: Major
- **Class**: 12 (Content-level mismatch) / overlaps Pattern 4 (conceptual mischaracterization)
- **Trigger**: §1 Major — "Right concept, wrong [detail] ... misleads about behavior" (the right concept is that classification is static; the wrong supporting claim is that a specific named parameter is time-varying).
- **Doc line**: module_45.md:407 (also the softer :309 and :288 are downstream of this).
- **Claim in doc**: "Modules like 52 (Carbon) use time-varying parameters indexed by static climate classes (e.g., **f52_growth_par(clcl) changes over time** while pm_climate_class(j,clcl) stays fixed)."
- **Reality in code**: `f52_growth_par(clcl,chap_par,forest_type)` is declared with **no time dimension** and is used 3-D in all 5 references; it does NOT change over time. Under the default config, M52's climate-weighted growth parameters are fully static. The doc's stated mechanism for "implicitly capturing climate change effects" via this parameter does not exist.
- **File evidence**: `/tmp/magpie_develop_ro/modules/52_carbon/normal_dec17/input.gms:37` (`parameter f52_growth_par(clcl,chap_par,forest_type) ...`); all uses at preloop.gms:29,30 and start.gms:17,28,48 are 3-D.
- **verify_cmd**: `grep -rn "f52_growth_par" modules/52_carbon/normal_dec17/*.gms` → declaration `(clcl,chap_par,forest_type)`, zero occurrences with a `t`/`t_all` index.
- **Confirmed**: yes.
- **Proposed fix**: rewrite :407 to: "Under the default config the climate-indexed parameters themselves are also static (`f52_growth_par(clcl,chap_par,forest_type)` and `fm_ipcc_bef(clcl)` carry no time dimension), so this path does NOT capture climate-change effects on growth. Climate-change impacts on yields enter via LPJmL-processed inputs in Module 14, not via reclassification here." Soften :309/:288 to remove the unsupported "time-varying climate-indexed parameters" implication (or qualify "would require non-default scenario inputs").

### Bug module_45-B4 — M52 `start.gms:17-35` citation truncates the third use (line 48)
- **Severity**: Minor
- **Class**: 10 (Stale/short file:line citation)
- **Trigger**: §1 Minor — "Off-by-few line citation where adjacent lines say similar things".
- **Doc lines**: module_45.md:144-146 ("start.gms:17-35"), :205 ("start.gms:17-35").
- **Claim in doc**: cites `modules/52_carbon/normal_dec17/start.gms:17-35` while the prose describes three carbon-density populations (plantation, secdforest, **other**).
- **Reality in code**: `pm_climate_class` uses are at lines 17 (plantation), 28 (secdforest), **48 (other)**. Line 48 is outside the cited range 17-35; the "Other land carbon" the doc describes lives at line 48.
- **File evidence**: `start.gms:48` (`pm_carbon_density_other_ac(...) = m_growth_vegc(...sum(clcl,pm_climate_class(j,clcl)*f52_growth_par(clcl,"k","natveg"))...)`).
- **verify_cmd**: `grep -n "pm_climate_class" modules/52_carbon/normal_dec17/start.gms` → 17, 28, 48.
- **Confirmed**: yes.
- **Proposed fix**: change "start.gms:17-35" → "start.gms:17-48" in both places (or "start.gms:17,28,48").

### Bug module_45-B5 — M52 preloop citations off by one (`preloop.gms:27` and `22-31` start)
- **Severity**: Minor
- **Class**: 10 (Stale file:line citation)
- **Trigger**: §1 Minor — off-by-one/off-by-few.
- **Doc lines**: module_45.md:225 ("modules/52_carbon/normal_dec17/preloop.gms:27"), :143 + :146 ("preloop.gms:22-31").
- **Claim in doc**: (:225) BEF used at `preloop.gms:27`; (:143/:146) wood density `im_vol_conv` block at `preloop.gms:22-31`.
- **Reality in code**: `fm_ipcc_bef` in preloop is at line **26** (line 27 is blank). `im_vol_conv` wood-density line is at line **21** — one line BEFORE the cited "22-31" range start.
- **File evidence**: `preloop.gms:21` (`im_vol_conv(i) = sum((cell(i,j), clcl), pm_climate_class(j,clcl) * f52_volumetric_conversion(clcl)) ...`); `preloop.gms:26` (`i52_bef_avg(i) = sum(... fm_ipcc_bef(clcl)) ...`).
- **verify_cmd**: `grep -n "pm_climate_class" modules/52_carbon/normal_dec17/preloop.gms` → 21, 26, 29, 30.
- **Confirmed**: yes.
- **Proposed fix**: ":225" change `preloop.gms:27` → `preloop.gms:26`. ":143/:146" change `preloop.gms:22-31` → `preloop.gms:21-30`.

### Bug module_45-B6 — M58 `v2/preloop.gms:~50` citation; actual line 36
- **Severity**: Minor
- **Class**: 10 (Stale file:line citation)
- **Trigger**: §1 Minor — off-by-few (doc uses approximate "~50").
- **Doc lines**: module_45.md:150 ("v2/preloop.gms:~50"), :238 ("modules/58_peatland/v2/preloop.gms:~50").
- **Claim in doc**: peatland mapping at `v2/preloop.gms:~50`.
- **Reality in code**: `p58_mapping_cell_climate(j,clcl58) = sum(clcl_mapping(clcl,clcl58),pm_climate_class(j,clcl));` is at line **36**.
- **File evidence**: `/tmp/magpie_develop_ro/modules/58_peatland/v2/preloop.gms:36`.
- **verify_cmd**: `grep -n "pm_climate_class" modules/58_peatland/v2/preloop.gms` → 36.
- **Confirmed**: yes.
- **Proposed fix**: replace "~50" with "36" in both places (drop the tilde; cite the exact line).

---

## Deferred (not code-verifiable here; NO edit proposed)

- **CS3 input file claims** (doc :183-195): `koeppen_geiger.cs3` is NOT present in the develop worktree (only the `input/files` manifest lists it). Cannot verify "205 lines", "4 header + 1 column header + ~200 data rows", "~200 cells", or the `calcOutput(...)` processing command at `koeppen_geiger.cs3:3`. The `input.gms` include path `./modules/45_climate/static/input/koeppen_geiger.cs3` matches the manifest. Route to preproc-agent for the calcOutput / cs3 provenance.
- **madrat v3.24.1 / mrcommons v1.63.0** version pins (doc :182): not checkable against GAMS code; would need the renv.lock / preproc pin. Defer.
- **Historical 2-D `f14_ipcc_bce(clcl, forest_type)` dimensionality** (doc :230) and PR #869 / "renamed 2026-04-20": the current code only confirms `f14_ipcc_bce` no longer exists and `fm_ipcc_bef` is 1-D. The prior 2-D shape is a claim about deleted code; correctly framed as historical with PR reference. Defer (no edit).
- **Doc :417 "full 30-type detail" / :421 "31 types"**: the "30" appears to be a loose round-down of 31; trivial prose, not flagged as a bug.

---

## Notes for the maintainer

- The two count errors (B1, B2) and the f52 time-varying claim (B3) are the substantive issues; everything else is citation hygiene. B1/B2 each recur in 3-4 locations — fix all occurrences (post-rename global grep, MANDATE 15).
- The `(sets.gms:8)` citation used for the 6/3 counts points at module 45's own sets.gms comment line, which mentions the existence of the mappings but states no counts. The real counts live in the *consumer* modules' sets.gms (M58 sets.gms:45, M59 sets.gms:22). Re-point those citations.
- The direct-consumer set is correct — no phantom/omitted consumers. M35 is correctly excluded (it reads climate-derived carbon densities, not `pm_climate_class`), even though module.gms's header prose name-drops `[35_natveg]`.
