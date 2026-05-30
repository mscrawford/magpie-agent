# Round 36 Doc Audit — module_42.md (Water Demand)

**Auditor**: Opus adversarial doc auditor
**Target**: `magpie-agent/modules/module_42.md`
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree, HEAD `ee98739fd`, branch detached at develop merge), `config/default.cfg`
**Date**: 2026-05-30

## Overall Verdict: MOSTLY ACCURATE

The doc is high quality. The default realization, all 11 scalar defaults, both equation formulas, the irrigation-efficiency sigmoid constants, all interface variable names, all file:line citations into `equations.gms`/`declarations.gms`/`presolve.gms`/`preloop.gms`/`realization.gms`/`module.gms`, and the producer/consumer SETS are correct. Two Major bugs (a wrong hardcoded country count repeated 4×, and one citation-to-wrong-content for the sector set) and two Minor bugs.

---

## Pre-run advisory resolution

The advisory flagged three things to verify specifically:

1. **DEFAULT realization via config/default.cfg** — CONFIRMED CORRECT. `config/default.cfg:1319`: `cfg$gms$water_demand<- "all_sectors_aug13"  # def = all_sectors_aug13`. Doc leads with `all_sectors_aug13` as default (lines 3, 9-10, 57). Both real dirs exist: `ls /tmp/magpie_develop_ro/modules/42_water_demand/` → `agr_sector_aug13`, `all_sectors_aug13`. No bug.
2. **R33: M42 reads `vm_area('irrigated')`** — CONFIRMED. `all_sectors_aug13/equations.gms:12`: `sum(kcr, vm_area(j2,kcr,"irrigated") * ic42_wat_req_k(j2,kcr))`. Doc line 75, 495 correct.
3. **`vm_watdem` consumer set (both grep forms + positive control)** — VERIFIED, doc is CORRECT.
   - `rg -ln "vm_watdem\(" modules/` → outside M42, only `43_water_availability/total_water_aug13/equations.gms`.
   - `rg -ln "vm_watdem\." modules/` → outside M42, only `43_water_availability/total_water_aug13/presolve.gms`.
   - Positive control `rg -n "vm_watdem" modules/43_.../equations.gms` → hits line 11. Grep mechanism confirmed working.
   - Conclusion: Module 43 is the sole external direct consumer of `vm_watdem`. Doc line 450-451 ("Module 43 ... Total demand constraints") correct. No phantom, no omission.

---

## Verified Claims (correct)

- **Default realization** `all_sectors_aug13` — `config/default.cfg:1319`.
- **Both equations** `q42_water_demand`, `q42_water_cost` — `equations.gms:10-14`, `16-17`. Formulas reproduced verbatim correct including the livestock-term efficiency factor.
- **Equation declarations** at `declarations.gms:24-25`; variables at `declarations.gms:29` (`vm_watdem`), `30` (`v42_irrig_eff`), `31` (`vm_water_cost`). All correct.
- **All 11 scalar defaults** (verified each in `input.gms`): `s42_watdem_nonagr_scenario=2` (L9), `s42_irrig_eff_scenario=2` (L14), `s42_irrigation_efficiency=0.66` (L19), `s42_env_flow_scenario=2` (L22), `s42_efp_startyear=2025` (L35), `s42_efp_targetyear=2040` (L36), `s42_env_flow_base_fraction=0.05` (L37), `s42_env_flow_fraction=0.2` (L38), `s42_pumping=0` (L39), `s42_multiplier_startyear=1995` (L40), `s42_multiplier=0` (L41). **`s42_pumping` default 0** (pumping costs OFF by default) is correctly stated (doc lines 120, 385, 627) — the historical R3 anchor failure is avoided.
- **Globals**: `c42_watdem_scenario` default `cc` (`input.gms:44`), `c42_env_flow_policy` default `off` (`input.gms:122`). Both correct.
- **Scalar count = 11** (doc line 897) — exactly 11 `s42_` scalars in input.gms. Correct.
- **Irrigation-efficiency sigmoid** constants `-22160`, `37767`, base `2.718282` and the `"y1995"` lock for default scenario 2 — `presolve.gms:13,18,20`. Doc lines 230/237/246/251/253/267/533 correct. The doc's repeated emphasis that the DEFAULT (scenario 2) is time-invariant (uses 1995 GDP) is accurate and valuable.
- **Interface providers** (`declarations.gms` of provider modules): `vm_area`→M30 (`30_croparea/{detail,simple}_apr24/declarations.gms`), `vm_prod`→M17 (`17_production/flexreg_apr16/declarations.gms`), `im_wat_avail`→M43, `im_gdp_pc_mer`/`im_development_state`/`im_pop_iso`→M09 (`09_drivers/aug17/declarations.gms`). All correct.
- **`vm_water_cost` consumer** = Module 11 (`11_costs/default/equations.gms:46`). Doc lines 465, 980 correct.
- **EFP trajectory** `m_linear_time_interpol(p42_efp_fader, s42_efp_startyear, s42_efp_targetyear, 0, 1)` — `preloop.gms:16`. Doc line 290 correct.
- **Ecosystem demand** formula — `presolve.gms:87-88`. Correct.
- **Module.gms** citations 10-11 (sector list) and 22-23 (realization includes) — correct.
- **nocc/nocc_hist** filters — `input.gms:84-85`. Correct.
- **Advisory R-code variable names** `v43_watavail` (`43_.../declarations.gms:13`), `vm_cost_glo` (`11_costs/default/declarations.gms`) — exist as named.
- **postsolve** writes marginals/levels/bounds — `postsolve.gms:9-28` (doc says 9-29; line 29 is the R-section-end comment — within tolerance).

---

## Bugs Found

### Bug 42-B1 — "195 countries" wrong count (×4)
- **Severity**: Major
- **Class**: 6 (Hardcoded counts drift)
- **Trigger** (§1 Major): "Fabricated count for a set/parameter/realization list."
- **Doc lines**: module_42.md:313, 652, 859, 904
- **Claim**: "Default: All 195 countries included" (313); "default: all 195" (652); "Default includes all 195 countries (input.gms:52-76)" (859); "Countries: 195 (default EFP coverage)" (904).
- **Reality in code**: `EFP_countries(iso)` lists **249** ISO codes (`input.gms:52-76`), identical to the core `iso` set (`core/sets.gms:38-55`, 249 countries). The set comment says "Default: all iso countries selected" (`input.gms:50`).
- **verify_cmd**: `awk 'NR>=52 && NR<=76' .../all_sectors_aug13/input.gms | tr ',' '\n' | grep -oE '\b[A-Z]{3}\b' | sort -u | wc -l` → **250**; minus the false "EFP" token (from the variable name `EFP_countries`) = **249**. Cross-checked: core `iso` set (`core/sets.gms:37-55`) is the same 249-country list.
- **Confirmed**: yes.
- **Proposed fix**: replace every "195" with "249" in these four locations (e.g. "Default: All 249 countries included").

### Bug 42-B2 — `sets.gms:9-10` cited for the 5-sector vm_watdem list (wrong content)
- **Severity**: Major
- **Class**: 12 (Content-level citation mismatch)
- **Trigger** (§1 Major): "Citation points at content that's no longer at the cited line, AND the actual cited content says something materially different."
- **Doc line**: module_42.md:442
- **Claim**: "**Sectors** (sets.gms:9-10):" followed by all 5 sectors including `"agriculture"`.
- **Reality in code**: `all_sectors_aug13/sets.gms:9-10` defines `watdem_exo(wat_dem) / domestic, manufacturing, electricity, ecosystem /` — only the **4 exogenous** sectors, NO "agriculture". The full 5-sector `wat_dem` set (incl. agriculture) is defined in **`core/sets.gms:247`**: `wat_dem Water demand sectors / agriculture, domestic, manufacturing, electricity, ecosystem /`.
- **file_evidence**: `core/sets.gms:247` (full set); `modules/42_water_demand/all_sectors_aug13/sets.gms:9-10` (watdem_exo, 4 sectors).
- **verify_cmd**: `rg -n "wat_dem" /tmp/magpie_develop_ro/core/sets.gms` → `247: wat_dem Water demand sectors / agriculture, domestic, manufacturing, electricity, ecosystem /`; and Read of module sets.gms:9-10 shows `watdem_exo / domestic, manufacturing, electricity, ecosystem /`.
- **Confirmed**: yes.
- **Proposed fix**: change line 442 to: `**Sectors** (full set `wat_dem` in `core/sets.gms:247`; the module's `sets.gms:9-10` defines only the exogenous subset `watdem_exo`):`

### Bug 42-B3 — "pumping cost parameters (`s42_watdem_nonagr_*`)" mislabel
- **Severity**: Minor
- **Class**: 7-adjacent / wrong-parameter reference (manual review)
- **Trigger** (§1 Minor): "Wrong detail, but a careful reader wouldn't be misled into action or misunderstanding" — the wildcard resolves to a real scalar, just the wrong family; line 1018 already lists the correct switch for that family.
- **Doc line**: module_42.md:1020
- **Claim**: "✅ Modify pumping cost parameters (`s42_watdem_nonagr_*`)"
- **Reality in code**: `s42_watdem_nonagr_*` resolves only to `s42_watdem_nonagr_scenario` (the non-agricultural SSP demand switch — already listed on line 1018). The actual pumping-cost parameters are `s42_pumping`, `s42_multiplier`, `s42_multiplier_startyear` (`input.gms:39-41`).
- **verify_cmd**: `rg "s42_watdem_nonagr\w*" -o .../all_sectors_aug13/*.gms | sort -u` → only `s42_watdem_nonagr_scenario`. `rg "s42_(pumping|multiplier)\w*" -o ...` → `s42_pumping`, `s42_multiplier`, `s42_multiplier_startyear`.
- **Confirmed**: yes.
- **Proposed fix**: change the parenthetical on line 1020 to `(\`s42_pumping\`, \`s42_multiplier\`, \`s42_multiplier_startyear\`)`.

### Bug 42-B4 — `sets.gms:9-13` cited for "endogenous and exogenous water demand"
- **Severity**: Minor
- **Class**: 12 (Content-level citation mismatch, weaker form)
- **Trigger** (§1 Minor): cited lines say something adjacent-but-incomplete; a careful reader checking the file would see the endogenous (agriculture) member is not there.
- **Doc line**: module_42.md:127
- **Claim**: "Module 42 distinguishes between endogenous and exogenous water demand (sets.gms:9-13):"
- **Reality in code**: `sets.gms:9-13` defines only `watdem_exo` (4 exogenous sectors) and `watdem_ineldo` (3 humanly-induced exogenous). The **endogenous** member ("agriculture") is part of the `wat_dem` set in `core/sets.gms:247`, not in the module's sets.gms. The module sets.gms contains no "endogenous" set.
- **file_evidence**: `modules/42_water_demand/all_sectors_aug13/sets.gms:9-13`; `core/sets.gms:247`.
- **verify_cmd**: Read of module sets.gms (lines 9-13 = watdem_exo + watdem_ineldo, both `(wat_dem)` subsets, both exogenous).
- **Confirmed**: yes.
- **Proposed fix**: change line 127 to: `Module 42 distinguishes endogenous (agriculture) from exogenous water demand; the exogenous subsets are defined at sets.gms:9-13 (`watdem_exo`, `watdem_ineldo`), while the full `wat_dem` set is in `core/sets.gms:247`:`

---

## Deferred (not edited — uncertain or not a clean doc-vs-code error)

- **`vm_prod` attributed to Module 70 in the "Participates In > Depends on" list (line 986)** vs Module 17 in the primary sections (lines 22, 505). `vm_prod` is DECLARED in Module 17 (`17_production/flexreg_apr16/declarations.gms`); Module 17 aggregates it (`q17_prod_reg`, equations.gms:11). Module 70 also references `vm_prod` (livestock subset, `70_livestock/fbask_jan16/equations.gms`). Both attributions are defensible (M17 = interface declarer, M70 = source of the livestock subset M42 actually uses). Internal inconsistency, but NOT a clean code-falsifiable producer flip — rubric warns strongly against false-positive producer flips. Worth a one-line harmonization but not recording as a confirmed bug.
- **`vm_water_cost` units**: Quick Reference (line 19) and Components (line 112) say "USD17MER/yr"; the code declaration (`declarations.gms:31`) says "USD17MER **per m^3**", and the doc's own declaration quote (line 461) faithfully copies "per m^3". The equation `vm_water_cost = sum(watdem[m^3]) * pumping_cost[USD/m^3]` is dimensionally USD/yr, so the "/yr" usage is dimensionally correct and the code's declaration label is arguably the inconsistent one. Not a clean doc-contradicts-code bug (doc reproduces the code label verbatim where it quotes the declaration). Deferred.
- **"Input Files: 5" (lines 27, 898)**: input.gms `$include`s 6 files, but one (`watdem_nonagr_total.cs3`) is explicitly "not used within MAgPIE, but necessary for the postprocessing" (`input.gms:102-108`) and conditionally included (`$if exist`). The doc enumerates exactly the 5 active inputs and separately notes the full-year file is stored for post-processing (line 692). Defensible; not a bug.
- **`cfg$water_demand` (line 563)** vs the full `cfg$gms$water_demand` (used correctly on line 10). Shorthand in body text; cosmetic. Not recorded.
- **postsolve.gms:9-29 (line 683)**: definitions are lines 9-28; line 29 is the R-section-end comment. Off-by-one at the range end, within citation tolerance. Not recorded.

---

## Mechanical checks
- M1 (file:line citations present): PASS (60+ citations, nearly all verified correct).
- M2 (active realization stated, matches default): PASS.
- M3 (variable prefixes valid): PASS.

## Summary
2 Major (repeated 195→249 country-count drift; sets.gms:9-10 cited for the 5-sector list that actually lives in core/sets.gms:247) + 2 Minor (s42_watdem_nonagr_* mislabeled as pumping params; sets.gms:9-13 endogenous/exogenous citation). Default realization, all defaults, equations, formulas, and producer/consumer sets are correct. Score ≈ 10 − 2 − 2 − 1 − 1 = 4 raw weighted → ~6/10 band, but most content verified accurate; harm is bounded (country count + two set-citation pointers).
