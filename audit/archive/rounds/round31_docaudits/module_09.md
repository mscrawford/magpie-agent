# R31 Doc Audit — module_09.md (Socioeconomic Drivers)

**Auditor**: Opus 4.8 (1M), adversarial documentation auditor
**Date**: 2026-05-30
**Target doc**: `modules/module_09.md`
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree) + `config/default.cfg`
**Realization**: `aug17` (only realization; default confirmed `cfg$gms$drivers <- "aug17"` at config/default.cfg:210)

---

## Overall verdict: MOSTLY ACCURATE (lower band)

The doc's factual spine is strong: all 8 interface variable names, all file:line citations (declarations.gms + input.gms), the 216-line count, the 9-member scenario set, the SSP2-until-2025 switching logic, and **section 5.2's per-module consumer set (the verified, load-bearing list) are all correct**. The consumer counts (im_pop_iso=10, im_pop=3, im_gdp_pc_ppp_iso=4, im_gdp_pc_mer_iso=2, im_gdp_pc_mer=1, im_development_state=5, im_demography=1, im_physical_inactivity=1) and the 14-module union all reconcile exactly with code.

The errors are concentrated in **mechanism descriptions** — chiefly the Module-13 GDP/technology claim (flagged by the R30 advisory, CONFIRMED) and a cluster of wrong/imprecise driver attributions in the **section 12.2 prose list (lines 862-876)** that contradict the doc's own verified section 5.2. These are doc-quality (mechanism-characterization) bugs, not consumer-set bugs.

---

## Claims verified CORRECT (high-value confirmations)

### Interface variables & declarations (declarations.gms)
All 8 `im_*` declarations at the cited lines:
- `im_pop_iso` :10 ✓ | `im_pop` :11 ✓ | `im_gdp_pc_mer_iso` :16 ✓ | `im_gdp_pc_mer` :20 ✓ | `im_gdp_pc_ppp_iso` :29 ✓ | `im_development_state` :32 ✓ | `im_physical_inactivity` :33 ✓ | `im_demography` :34 ✓
- Count "8 interface variables" (lines 123, 483, 791): exactly 8 `im_*` in declarations.gms. ✓

### Consumer sets (grep-verified, rg with exit codes + positive controls)
- `im_pop_iso` → 12,13,15,42,50,55,56,60,70,73 = **10 modules** (doc line 132 "10 modules"). ✓
- `im_pop` → 15,62,70 = **3** (doc line 149). ✓
- `im_gdp_pc_ppp_iso` → 13,15,38,73 = **4** (doc line 203). ✓
- `im_gdp_pc_mer_iso` → 15,36 = **2** (doc line 174). ✓
- `im_gdp_pc_mer` → 42 = **1** (doc line 191). ✓
- `im_development_state` → 12,18,42,55,56 = **5** (doc line 228, recomputed R5). ✓
- `im_demography` → 15 = **1** (doc line 161). ✓
- `im_physical_inactivity` → 15 = **1** (doc line 237). ✓
- Union of all 8 = {12,13,15,18,36,38,42,50,55,56,60,62,70,73} = **14 modules**, matches doc lines 315, 791, 816 exactly. ✓
- M38 "all three realizations consume im_gdp_pc_ppp_iso in preloop" (line 350): per_ton_fao_may22, sticky_feb18, sticky_labor all confirmed. ✓
- **Section 5.2 per-module variable attributions (lines 334-374) all correct** — this is the load-bearing list and it is clean.

### Citations (input.gms data files) — all correct
- f09_pop_iso :36-38 ✓ | f09_gdp_ppp_iso :26-28 ✓ | f09_gdp_mer_iso :31-33 ✓ | f09_development_state :41-43 ✓ | f09_demography :46-48 ✓ | f09_physical_inactivity :51-53 ✓ | fm_gdp_defl_ppp :56-60 ✓
- preloop citations: +0.000001 demography :39,48 ✓ | im_pop_iso load :40,49 ✓ | per-capita calc ranges :14-20, :23-33 ✓

### Other
- "216 lines across 6 files" (line 5): 20+36+61+60+16+23 = 216 ✓
- Scenario set 9 members `SSP1..SSP5, SDP, SDP_EI, SDP_MC, SDP_RC` at sets.gms:10-11 (doc lines 52-56, 46). ✓
- `sm_fix_SSP2 = 2025` (doc lines 405, 610): input.gms:22 `/ 2025 /`. ✓
- Config defaults `c09_pop_scenario/c09_gdp_scenario/c09_pal_scenario = SSP2` (doc lines 110-112): input.gms:8,12,16. ✓
- Scenario-switching loop logic (doc lines 422-445): matches preloop.gms:36-56 verbatim. ✓
- 21 age groups, M/F (doc lines 162, 292-293): sets.gms:14-22 → 21 age members + sex {M,F}. ✓
- GDX-example parameter names in §10 (i09_gdp_ppp_iso, i09_gdp_mer_iso, i09_gdp_pc_ppp_iso_raw, im_demography): all real declared parameters. ✓

---

## Bugs found

### BUG 09-B1 — Module 13: GDP "technology adoption" mechanism is wrong + OFF by default
- **Severity**: Major (tier_uncertainty: true — see note)
- **Class**: 4 (conceptual pseudo-code / mechanism mischaracterization) + missing-default-caveat
- **Trigger**: Major "Missing default-state caveat (mechanism described as if always active when it's OFF by default)". Competing Critical trigger "Active mechanism claimed when actually OFF by default" considered; tie-broken DOWN because the consumer SET (which variables M13 reads) is correct, so a user would not edit the wrong file.
- **Doc lines**: module_09.md:864 (primary, advisory-flagged); also :338, :208, :39.
- **Claim in doc**:
  - :864 "Module 13 (tc): GDP affects technology adoption rates"
  - :338 "Technology adoption driven by income; population for ISO-level scaling"
  - :208 "Technology adoption (Module 13)"
  - :39 "GDP drives income-elastic demand, technology adoption"
- **Reality in code**: The ONLY GDP linkage in all of Module 13 is at `presolve.gms:26`, where `im_gdp_pc_ppp_iso * im_pop_iso` (summed to regional GDP) × `s13_max_gdp_shr` sets an **upper bound (cap) on `vm_tech_cost.up(i)`** — a cap on tech-investment SPENDING, not a driver of adoption. Comment at presolve.gms:23-24: "We constrain tech cost to a defined share of regional GDP to avoid unrealistically high endogenous tech investments." The whole block is gated by `if(m_year(t) > sm_fix_SSP2 AND s13_max_gdp_shr <> Inf, ...)`. **`s13_max_gdp_shr` defaults to `Inf`** (input.gms:11 `/ Inf /`; config/default.cfg:304 `<- Inf`), so the cap — and hence the only GDP→tech linkage — is **INACTIVE in a default run**. Technology intensity (`vm_tau`) and tech cost are endogenous to the cost-minimization via the TC cost curve (`c13_tccost`), not "driven by income."
- **File evidence**: `modules/13_tc/endo_jan22/presolve.gms:21-26`; default `modules/13_tc/endo_jan22/input.gms:11` and `config/default.cfg:304`.
- **verify_cmd & result**:
  - `rg -n 'im_gdp_pc_ppp_iso|im_pop_iso' modules/13_tc/ --glob '*.gms'` → single hit: `endo_jan22/presolve.gms:26`.
  - `rg -n 's13_max_gdp_shr' modules/13_tc/` → `input.gms:11: ... / Inf /`; `presolve.gms:21: if(... AND s13_max_gdp_shr <> Inf,`.
  - `grep -n 's13_max_gdp_shr' config/default.cfg` → `304:cfg$gms$s13_max_gdp_shr <- Inf # def = Inf`.
- **confirmed**: true
- **Note on R30 advisory**: CONFIRMED. The advisory also said the line-337 consumer set (`im_gdp_pc_ppp_iso`, `im_pop_iso`) was verified correct in R30 — TRUE, those are exactly the two vars at presolve.gms:26. Do NOT touch the variable list; only the mechanism prose is wrong.
- **proposed_fix**:
  - :864 replace with: "Module 13 (tc): regional GDP (`im_gdp_pc_ppp_iso` x `im_pop_iso`) can CAP endogenous tech-investment cost via `s13_max_gdp_shr`; OFF by default (`s13_max_gdp_shr = Inf`). Technology intensity itself is endogenous, not income-driven."
  - :338 replace with: "Regional GDP optionally caps tech-investment spending (`vm_tech_cost.up`) via `s13_max_gdp_shr` (default Inf = no cap, post-2025 only); population enters the same regional-GDP product."
  - :208 replace "Technology adoption (Module 13)" with: "Tech-cost GDP-share cap (Module 13, default off)".
  - :39 replace "technology adoption" with: "technology-cost caps (Module 13, off by default)".

### BUG 09-B2 — Section 12.2: Module 50 wrong driver variable + phantom process
- **Severity**: Major
- **Class**: 15 (latent doc error — secondary list contradicts verified primary list) / wrong mechanism
- **Trigger**: Major "claim is wrong in a way that misleads about behavior". Names a variable M50 does not read and a process it does not derive from drivers.
- **Doc line**: module_09.md:870
- **Claim in doc**: "Module 50 (nr_soil_budget): Atmospheric N deposition scaled by development"
- **Reality in code**: M50 reads ONLY `im_pop_iso` (not `im_development_state`), and uses it to build **population-weighted region shares for nitrogen-use efficiency** (`p50_cropneff_region_shr`, `p50_pastneff_region_shr`). Code comment (preloop.gms:19): "Countries are weighted by their population size." There is no atmospheric-N-deposition computation from drivers here, and `im_development_state` is absent from M50 entirely. (The doc's own section 5.2 entry, line 355-356, correctly attributes `im_pop_iso`.)
- **File evidence**: `modules/50_nr_soil_budget/macceff_aug22/preloop.gms:20-21` (uses im_pop_iso); `:14-19` (population-weight comment).
- **verify_cmd & result**:
  - `rg -n 'im_development_state' modules/50_nr_soil_budget/ --glob '*.gms'` → EXIT=1 (no match).
  - Positive control `rg -n 'im_pop_iso' modules/50_nr_soil_budget/macceff_aug22/preloop.gms` → lines 20,21.
- **confirmed**: true
- **proposed_fix**: Replace :870 with "Module 50 (nr_soil_budget): population (`im_pop_iso`) weights country influence in regional nitrogen-use-efficiency shares". (Drop "atmospheric N deposition" and "development".)

### BUG 09-B3 — Section 12.2: cluster of wrong/extra driver attributions contradicting verified §5.2
- **Severity**: Minor
- **Class**: 15 (latent doc error — secondary prose list contradicts verified primary list)
- **Trigger**: Minor "Wrong detail, but a careful reader wouldn't be misled into action" — the authoritative, verified attributions live in section 5.2 (correct); section 12.2 is a secondary summary a careful reader cross-checks. Each entry names a wrong/extra driver variable.
- **Doc lines**: module_09.md:866, :867, :874, :875
- **Claims in doc vs reality**:
  - :866 M18 "Population affects residue demand" → M18 reads `im_development_state` (NOT population) to split residue burning between high/low-income (`equations.gms:77-78`). §5.2 line 343 correctly says `im_development_state`.
  - :867 M36 "Labor productivity from development state" → M36 reads `im_gdp_pc_mer_iso` (NOT `im_development_state`) to compute hourly labor costs (`preloop.gms:9,18`). §5.2 line 346 correctly says `im_gdp_pc_mer_iso`. (Also: M36 is employment/wages; labor productivity is Module 37.)
  - :874 M62 "Material demand from population/GDP" → M62 reads ONLY `im_pop` (no GDP variable). §5.2 line 367 correctly says `im_pop` only.
  - :875 M70 "Livestock demand from population/income" → M70 reads ONLY `im_pop`/`im_pop_iso` (no income/GDP variable). §5.2 line 370 correctly says population only.
- **File evidence**: M18 `modules/18_residues/flexreg_apr16/equations.gms:55-56`; M36 `modules/36_employment/exo_may22/preloop.gms:9,18`; M62 `modules/62_material/exo_flexreg_apr16/preloop.gms:17` (im_pop only); M70 `modules/70_livestock/fbask_jan16/presolve.gms:32,35` (im_pop only).
- **verify_cmd & result**:
  - `rg -n 'im_gdp_pc_mer_iso|im_development_state' modules/36_employment/exo_may22/*.gms` → im_gdp_pc_mer_iso at :9,:18; no im_development_state.
  - `rg -n 'im_gdp' modules/62_material/exo_flexreg_apr16/*.gms` → EXIT=1 (no GDP).
  - `rg -n 'im_gdp' modules/70_livestock/fbask_jan16/*.gms` → EXIT=1 (no GDP).
  - `rg -n 'im_development_state' modules/18_residues/flexreg_apr16/equations.gms` → :55,:56.
- **confirmed**: true
- **proposed_fix**: Align section 12.2 lines with the verified section 5.2 attributions:
  - :866 "Module 18 (residues): development state splits residue burning between income groups"
  - :867 "Module 36 (employment): hourly labor costs scale with GDP per capita MER (`im_gdp_pc_mer_iso`)"
  - :874 "Module 62 (material): bioplastic material demand scales with regional population (`im_pop`)"
  - :875 "Module 70 (livestock): livestock product demand scales with population (`im_pop`/`im_pop_iso`)"

---

## Deferred (not code-verifiable or insufficient certainty — DO NOT EDIT)

1. **Data-source attributions** (IIASA SSP Database, KC & Lutz 2017, World Bank, OECD/IMF, WHO, UN, van Vuuren et al. 2018, O'Neill/Riahi 2017): citations to external literature, not checkable against GAMS code. Plausible but out of scope.
2. **SSP2EU**: input.gms comments (lines 9,13,17) list `SSP2EU` as a selectable option, but the actual `pop_gdp_scen09` set (sets.gms:10-11) does NOT include it. This is a code-internal comment/set inconsistency, NOT a doc error — the doc correctly describes the 9-member set. Flagging as a develop-code note, not a doc bug.
3. **"249 ISO countries" / "12 MAgPIE regions"** (lines 20,132,147,189): standard MAgPIE counts set by `i_to_iso` mapping / regional resolution (H12) at preprocessing time, not by module-09 GAMS code. Not module-09-specific; not verified here.
4. **Per-capita code snippets (lines 177-181, 213-218)**: the doc's GAMS excerpts omit the `= 0` init and the `$(...>0)` division guard present at preloop.gms:23-24,29-30. A simplification, but the cited line range (29-33 / 23-27) is correct and the conceptual calc (pc = GDP/pop) is right; the doc separately notes the div-by-zero guard at line 473. Borderline Informational; not recording as a load-bearing bug.
5. **Section 12.2 lines 869 (M42 "non-ag water from population/GDP"), 872 (M56 "policy ambition scaled by income"), 873 (M60 "from economic scenarios"), 876 (M73 "construction activity (GDP)")**: loose/vague prose that is defensible (M42 does read pop+gdp+devstate; M56 devstate IS an income classification; M73 GDP is right). Too imprecise to call clearly wrong; left to the optional 12.2 rewrite but not recorded as bugs.
6. **Footer "Last Verified 2025-10-13"**: metadata; not a content claim.

---

## Summary

Spine correct (8 vars, all citations, 216 lines, 9-scenario set, switching logic, **§5.2 consumer set verified clean = 14 modules**). 3 mechanism bugs: B1 (Major) M13 "GDP drives tech adoption" — actually an Inf-default-OFF spending CAP (R30 advisory CONFIRMED); B2 (Major) §12.2:870 M50 wrong var (`im_development_state`) + phantom "atmospheric N deposition" (actually `im_pop_iso` N-use-efficiency weighting); B3 (Minor) §12.2 M18/M36/M62/M70 wrong/extra drivers contradicting verified §5.2. Root cause of B2/B3: §12.2 prose list was written from intuition, not from §5.2's verified reads.
