# Round 34 Doc Audit — module_59.md (Soil Organic Matter)

**Auditor**: Opus 4.8 (1M) adversarial doc-vs-code auditor
**Date**: 2026-05-30
**Target doc**: `magpie-agent/modules/module_59.md`
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree), `config/default.cfg`
**Realization audited**: `cellpool_jan23` (confirmed default)

---

## Pre-run advisory checker verdict

The advisory flagged 4 items. Verdicts:

1. **"Verify default realization (likely cellpool_jan23)"** — CONFIRMED. `config/default.cfg:1916` → `cfg$gms$som <- "cellpool_jan23"`. Doc lines 4, 38-39 correct.
2. **"Verify M59's vm_carbon_stock POPULATOR role (soilc pool, per G2)"** — CONFIRMED. M59 populates `vm_carbon_stock(j,land,"soilc",stockType)` via `q59_carbon_soil` (`equations.gms:62`) and initializes `vm_carbon_stock.l` in `preloop.gms:32,35`. `vm_carbon_stock` is DECLARED in M56 (`56_ghg_policy/price_aug22/declarations.gms:34`), READ by M52. The doc frames M59 as "Provides To Module 52 ... Defined in: equation q59_carbon_soil" (line 538) — correct populate→read framing; the doc does NOT falsely claim M59 declares the variable. No bug.
3. **"R33 confirmed M59 reads vm_area in equations"** — CONFIRMED M59 reads `vm_area` (`equations.gms:22,100`). But the doc attributes `vm_area`'s PRODUCER to Module 17; the actual owner is Module 30. See BUG-1.
4. **"Verify with both 'name(' and 'name.' greps"** — Done. `vm_carbon_stock(` (equations) and `vm_carbon_stock.l` (preloop) both checked.

---

## Verified-correct claims (high-value sample)

- **8 equations**, names + order all match `declarations.gms:28-35` and `equations.gms`: q59_som_target_cropland (20-27), q59_som_target_noncropland (31-34), q59_som_pool (46-52), q59_carbon_soil (61-64), q59_nr_som (69-75), q59_nr_som_fertilizer (81-84), q59_nr_som_fertilizer2 (88-91), q59_cost_scm (98-101). Every equation file:line citation in Section 3 is ACCURATE.
- **Equation formulas** in §3.1-3.8 reproduce the GAMS verbatim (set-based sums preserved, no expansion; MANDATE 10 satisfied). C:N = 15:1 and `/m_timestep_length*1/15` confirmed at `equations.gms:71,76`.
- **Interface variable declarations**: `vm_nr_som` (declarations.gms:45), `vm_nr_som_fertilizer` (:46), `vm_cost_scm` (:41) — all exact.
- **Consumer set of M59 outputs** (the Critical-prone surface) is CORRECT and complete:
  - `vm_nr_som` → M51 `rescaled_jan21/equations.gms:58` (default ✓)
  - `vm_nr_som_fertilizer` → M50 `macceff_aug22/equations.gms:30` (default ✓)
  - `vm_cost_scm` → M11 `default/equations.gms:37` (default ✓)
  - `vm_carbon_stock` (soilc) populated here, read by M52 (default `normal_dec17`).
  Verified via `grep -rln "<var>" modules/ --include="*.gms"` (excluding 59_som) + positive control (`vm_nr_som` correctly located in M51). No phantom consumers, no omitted consumers among the OUTPUT variables.
- **Producers of M59 inputs** (mostly correct): `vm_land`, `vm_lu_transitions`, `vm_landexpansion`, `pcm_land`, `pm_land_start` → M10 `landmatrix_dec18` (default ✓); `vm_fallow`, `vm_treecover` → M29 `cropland` ✓.
- **Scalar defaults** (input.gms): s59_nitrogen_uptake=0.2 (:9), s59_scm_target=0 (:11), s59_scm_target_noselect=0 (:12), s59_scm_scenario_start=2025 (:13), s59_scm_scenario_target=2050 (:14), s59_cost_scm_recur=65 (:15), s59_fader_functional_form=1 (:10). All match.
- **Scenario switches**: `c59_som_scenario` default "cc" (config:1930; input.gms:72), `c59_irrigation_scenario` default "on" (input.gms:61). nocc/nocc_hist assignment citations input.gms:84/85 correct; irrigation-off input.gms:70 correct.
- **Input table citations** §4.3: f59_cratio_landuse (43), f59_cratio_tillage (49), f59_cratio_inputs (55), f59_cratio_irrigation (65), f59_topsoilc_density (77) — all match.
- **preloop/presolve/postsolve citations** §6-8: subsoil density (preloop:12), lossrate (:45), i59_cratio (:60-67), treecover=1 (:82), i59_cratio_scm high_input_nomanure (:88-90), tillage/input defaults full_tillage/medium_input (:52-55); secdforest update (presolve:14-18), other (:20-22), primforest (:24-26), carbon density recalc (:28), i59_scm_target (:31-33); postsolve store (:8-10). All ACCURATE.
- **static_jan19 legacy realization** uses `vm_land_other` for othernat/youngsecdf (doc line 66) — confirmed `static_jan19/equations.gms:23-24`.
- **s14_degradation** default 0 / OFF-by-default (doc lines 847, 872) — confirmed config:389, `14_yields/managementcalib_aug19/input.gms:17`.
- **noncropland59 set** = past, forestry, primforest, secdforest, other, urban (sets.gms:11) — matches doc.
- **Climate zones**: climate59 (4 members) used; boreal_dry/boreal_moist declared in climate59_2019 (6 members) but unmapped in clcl_climate59 → doc's "not used in default simulation" (line 400) correct.

---

## Bugs found

### BUG-1 (Major) — `vm_area` attributed to Module 17; actual producer is Module 30

- **Doc lines**: module_59.md:20 ("Receives from: Modules 10 (land), 17 (production - via vm_area), 29 ...") and module_59.md:557 ("**From Module 17 (Production)** via `vm_area(j,kcr,w)`").
- **Reality**: `vm_area(j,kcr,w)` is declared in **Module 30 (croparea)** — `30_croparea/detail_apr24/declarations.gms:21` and `simple_apr24/declarations.gms:21` (default croparea = `simple_apr24`, config:896). It is DEFINED/used in `30_croparea/simple_apr24/equations.gms` (rotation constraints, carbon, BII, and the `vm_prod = sum(w, vm_area*vm_yld)` production identity at line 15). Module 17 (`flexreg_apr16`, default) does NOT reference `vm_area` at all (grep returned no match in its `.gms` files; the `vm_area`-declaration grep on `17_production/*/declarations.gms` exited 1 = no match).
- **Severity rationale**: §1 Major trigger — wrong module attribution that misleads about dependencies/behavior (cf. MANDATE 9 cost-attribution pattern, MANDATE 17 producer-vs-consumer). Not Critical: the variable name is correct, M59's consuming equations are correctly described, so a user would not edit a wrong file in M59 itself — but anyone tracing "where does the cropland area feeding M59 come from?" is sent to M17 instead of M30. Appears in two places (Quick Reference + Section 9.2).
- **verify_cmd**: `grep -rln "vm_area(" /tmp/magpie_develop_ro/modules/*/*/declarations.gms` → only `30_croparea/{detail,simple}_apr24/declarations.gms`. `grep -rln "vm_area(" /tmp/magpie_develop_ro/modules/17_production/*/declarations.gms` → exit 1 (none).
- **confirmed**: true.
- **Proposed fix**: line 20 → "Modules 10 (land), 30 (croparea - via vm_area), 29 (crop management)"; line 557 → "**From Module 30 (Croparea)** via `vm_area(j,kcr,w)`".

### BUG-2 (Minor) — Convergence figure "44% in 5 yrs" contradicts the formula and the doc's own §3.3/§4.2

- **Doc line**: module_59.md:14 ("15% annual convergence toward equilibrium (44% in 5 yrs, 80% in 10 yrs, 96% in 20 yrs)").
- **Reality**: `i59_lossrate(t) = 1 - 0.85^m_yeardiff(t)` (`preloop.gms:45`) is the CONVERGED fraction. 1-0.85^5 = 0.5563 (55.6%), not 44%. 44.4% = 0.85^5 = the REMAINING (un-converged) fraction. Doc §3.3 line 148 ("5 years: ~56% (1 - 0.85^5 ≈ 0.5563)") and §4.2 line 321 ("~0.5563 (55.6%)") are correct, so line 14 self-contradicts. Note: the source code COMMENT (`preloop.gms:42`) itself says "44% in 5 years, 80% in 10 years, 96% in 20 years" — internally inconsistent (44% remaining vs 80/96% converged); line 14 inherited the comment's error.
- **Severity rationale**: §1 "right concept, wrong number" leans Major, but tie-breaker pulls down: the correct value appears twice elsewhere in the same doc, the error is a visible self-contradiction, and it mirrors a code-comment quirk. tier_uncertainty.
- **verify_cmd**: `python3 -c "print(1-0.85**5, 0.85**5)"` → `0.5563... 0.4437...`.
- **confirmed**: true.
- **Proposed fix**: module_59.md:14 → "15% annual convergence toward equilibrium (56% in 5 yrs, 80% in 10 yrs, 96% in 20 yrs)". (Optionally add a parenthetical that 44% is the *remaining* fraction, to explain the code comment.)

### BUG-3 (Minor) — `cellpool_aug16` "directory exists" claim is false

- **Doc line**: module_59.md:39 ("Note: `cellpool_aug16` directory exists but has been removed from the model (no code files, not listed in `module.gms`).").
- **Reality**: There is NO `cellpool_aug16` directory under `modules/59_som/`. `ls` shows only `cellpool_jan23/`, `static_jan19/`, `input/`, `module.gms`. `module.gms:20-21` lists only `cellpool_jan23` and `static_jan19`. The realization.gms `@description` (line 9) refers to "cellpool_aug23" (a stale code-comment name), but no such directory exists either.
- **Severity rationale**: §1 Minor — the operative conclusion (not a usable realization; only jan23 + static_jan19 exist) is correct, and this is a parenthetical note inside a callout. But the stated reason ("directory exists ... no code files") is factually false; a reader who goes looking for the directory finds nothing.
- **verify_cmd**: `ls -d /tmp/magpie_develop_ro/modules/59_som/*/` → only cellpool_jan23, input, static_jan19. `grep -n "cellpool" modules/59_som/module.gms` → only cellpool_jan23.
- **confirmed**: true.
- **Proposed fix**: module_59.md:39 → "Alternative: `static_jan19` (static SOC without dynamics). Only these two realizations exist (`module.gms`)." Delete the cellpool_aug16 sentence entirely.

### BUG-4 (Minor) — `f59_cratio_landuse` index-set name: doc says `climate59`, declaration is `climate59_2019`

- **Doc line**: module_59.md:337 ("**f59_cratio_landuse(i,climate59,kcr)** - Land use factor (1)").
- **Reality**: Declared `f59_cratio_landuse(i,climate59_2019,kcr)` (`input.gms:43`). The 6-element `climate59_2019` (includes boreal) is the declared domain; the 4-element subset `climate59` is what the code indexes with in `preloop.gms:16,62,75`. So the doc's `climate59` matches USAGE but not the DECLARED dimension.
- **Severity rationale**: §1 Minor — wrong index-set label on a parameter; a careful reader checking the declaration sees a different set name. Findable, low harm. tier_uncertainty (could be deemed Informational).
- **verify_cmd**: `grep -n "f59_cratio_landuse" .../cellpool_jan23/input.gms` → `table f59_cratio_landuse(i,climate59_2019,kcr) ...`.
- **confirmed**: true.
- **Proposed fix**: module_59.md:337 → "**f59_cratio_landuse(i,climate59_2019,kcr)** - Land use factor (1)" (and optionally note it is applied via the `climate59` subset in preloop).

### BUG-5 (Minor) — "Depends on: ... 35 (natveg)" overstates a direct dependency; Module 30 omitted

- **Doc line**: module_59.md:1019 ("**Depends on**: Modules 10 (land), 29 (cropland), 35 (natveg)").
- **Reality**: M59 reads NO module-35-owned variable. Full set of external interface vars read by `cellpool_jan23` (grep of `vm_/pm_/pcm_/im_/fm_` over all its .gms): vm_land, vm_lu_transitions, vm_landexpansion, pcm_land, pm_land_start (all M10), vm_area (M30), vm_fallow, vm_treecover (M29), vm_carbon_stock (M56-declared, populated here), plus input params (fm_carbon_density, fm_croparea, pm_climate_class, pm_avl_cropland_iso, pcm_carbon_stock). A `v35_/p35_/i35_` grep over M59 returned EMPTY. M35's role is conceptual only: the `presolve.gms:11-12` comment points to 35_natveg for transition-consistency, but the land-transition data reaches M59 via M10's `pcm_land`/`vm_lu_transitions`, not a direct M35 read (transitive — MANDATE 17). Meanwhile Module 30 (true owner of `vm_area`) is omitted from this line.
- **Severity rationale**: §1 Minor — this is a coarse dependency-summary line, M35 has a genuine conceptual/comment link, and the top-of-doc Quick Reference (line 20) does not list M35. Listing M35 as a direct "Depends on" while omitting M30 mildly misleads modification-safety reasoning. tier_uncertainty (borderline Informational vs Minor; could also be argued the summary intends conceptual neighbors).
- **verify_cmd**: `grep -rhoE "\b(v35_|p35_|i35_)[a-zA-Z_]+" .../cellpool_jan23/*.gms` → empty. `grep -rhoE "\b(vm_|pm_|pcm_|im_|fm_)[a-zA-Z_]+" .../cellpool_jan23/*.gms | sort -u` → list above; none owned by M35.
- **confirmed**: true.
- **Proposed fix**: module_59.md:1019 → "**Depends on**: Modules 10 (land), 30 (croparea), 29 (cropland). (Module 35 natveg is a conceptual upstream driver of land transitions via Module 10, not a direct interface dependency.)"

---

## Deferred (not edited; uncertain or not clearly load-bearing)

- **Module 50 omitted from line 19 Quick-Reference "Provides to"** (lists only M51, M11; M50 consumes `vm_nr_som_fertilizer`). Section 9.1 correctly includes M50. Borderline Minor incompleteness in a summary line; not recording as a separate bug to avoid over-counting — could be folded into a Quick-Reference cleanup. (Verified: M50 IS a real consumer.)
- **`i51_ef_n_soil(i,n_pollutants_direct,"som")`** (line 526) drops the leading `t`/`ct` index vs declaration `i51_ef_n_soil(t,i,n_pollutants_direct,emis_source_n_cropsoils51)` (used as `(ct,i2,...)` at 51:58). This describes Module 51's INTERNAL parameter inside M59's "provides to" note, not M59's own interface. Minor index imprecision on a non-M59 helper; deferring (low harm, not M59-load-bearing).
- **Line counts** (line 970-973): equations "103" (wc=102), preloop "117" (116), presolve "34" (33), input "118" (117) — all off-by-one, consistent with files lacking a final newline (the doc counted the last content line). Informational metadata; not editing.
- **"8% yield penalty"** (Module 14, lines 847/872) — the OFF-by-default part is verified (s14_degradation=0); the specific 8% magnitude is a cross-module M14 detail not verified here and not M59-load-bearing. Deferred.
- **Step-9 preloop formula simplification** (line 448): doc shows `pc59_carbon_density = pc59_som_pool / land_area` without the `$(pc59_land_before > 1e-10)` guard present in code (preloop.gms:116). Pedagogical simplification, not a content error. Not recording.

---

## Summary

8 equations, all formulas, all §3 equation citations, scalar defaults, scenario-switch defaults, the OUTPUT-variable consumer set (M51/M50/M11/M52), and the vm_carbon_stock populator role are ACCURATE. Doc is high quality. One Major (vm_area producer = M30, not M17; appears 2×) + four Minor (convergence "44%" self-contradiction, false cellpool_aug16-directory note, climate59 vs climate59_2019 index-set, M35 listed as direct dependency while M30 omitted). No Critical: no inverted defaults, no wrong default realization, no invented variables/equations, no wrong OUTPUT consumer set.
