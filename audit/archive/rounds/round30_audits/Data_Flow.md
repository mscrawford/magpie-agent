# Audit Report: Round 30 — SSP driver data flow (Module 09 → 15/16 and → 14)

**Question (anchored on core_docs/Data_Flow.md):** How does SSP driver data (GDP and population from module 09) flow into food demand (modules 15/16) and into yields (module 14)? Name the parameters and files that carry it through the chain.

**Ground truth:** `/tmp/magpie_develop_ro` develop worktree.

## Overall Verdict: MOSTLY ACCURATE
## Accuracy Score: 7/10

The core load-bearing content the question asked for is correct and well-cited: the two distinct chain shapes (direct GDP+population → food demand; indirect GDP → M13 → tau → yields), the M09 published-parameter set, the M15 consumer set, and — most valuably — the two negative findings (M14 consumes ZERO M09 parameters; M16 consumes ZERO M09 parameters and is a passive aggregator). Three secondary-detail imprecisions keep it from a 9–10.

---

## Mechanical checks
- **M1 (file:line citations present):** PASS — many `equations.gms:NN`, `presolve.gms:NN`, `input.gms:NN` citations.
- **M2 (active realization stated):** PASS — names aug17/anthro_iso_jun22/sector_may15/managementcalib_aug19, all verified default (config/default.cfg). Did NOT name the M13 realization, but M13 was tangential; default is `endo_jan22` (config/default.cfg).
- **M3 (variable prefixes valid):** PASS for prose. One diagram shorthand `vm_yld_past` is not a real variable (Informational; prose has `vm_yld(j,"pasture",w)`).
- **M4 (epistemic badges):** PASS — explicit 🟡 hierarchy block.
- **M5 (confidence tier matches depth):** PASS — claims tagged 🟡 Documented, consistent with docs-first sourcing.
- **M6 (closing source statement):** PASS — "Sources:" + module docs listed.

---

## Verified Claims (correct)

- **M09 realization = aug17, default.** `config/default.cfg`: `cfg$gms$drivers <- "aug17"`. ✓
- **Three independent scenario switches, all SSP2 default.** `modules/09_drivers/aug17/input.gms:8,12,16` — `c09_pop_scenario`, `c09_gdp_scenario`, `c09_pal_scenario` all `SSP2`. Answer's `input.gms:8-18` citation ✓.
- **SSP2 lock until `sm_fix_SSP2` = 2025.** `input.gms:22` `sm_fix_SSP2 ... / 2025 /`. ✓
- **Scenario-selection loop at `preloop.gms:36-56`.** ✓ (loop spans 36–56).
- **M09 publishes exactly 8 `im_*` interface parameters.** `declarations.gms:8-36`: `im_pop_iso, im_pop, im_gdp_pc_mer_iso, im_gdp_pc_mer, im_gdp_pc_ppp_iso, im_development_state, im_physical_inactivity, im_demography`. Answer's 8-row table matches. ✓ (module_09.md:483 corroborates "8 interface variables".)
- **M15 (anthro_iso_jun22) consumes EXACTLY the 6 listed M09 params.** Verified by per-parameter grep: `im_gdp_pc_ppp_iso, im_gdp_pc_mer_iso, im_pop, im_pop_iso, im_demography, im_physical_inactivity`. Correctly EXCLUDES `im_development_state` (grep: NONE in M15) and regional `im_gdp_pc_mer` (grep with `\b`: NONE in M15 — only the iso variant is used). Matches module_09.md:340 consumer table. ✓
- **`q15_budget` (equations.gms:48-52)** sets `v15_income_pc_real_ppp_iso(iso)` = price adjustment + `im_gdp_pc_ppp_iso` + tax recycling. Verified line 49,52. ✓ Variable name `v15_income_pc_real_ppp_iso` exact. ✓
- **`q15_regr_bmi_shr` (equations.gms:71-76)** Michaelis-Menten saturation of `v15_income_pc_real_ppp_iso × fm_gdp_defl_ppp`. Verified lines 75-76. ✓
- **`q15_regr` (equations.gms:169-173)** saturation of real income for diet composition. Verified. ✓
- **`q15_intake` (equations.gms:141-151)** weights by `im_demography`. Verified lines 143,147. ✓
- **`q15_food_demand` (equations.gms:10-14)** `=g=` linking `vm_dem_food` to `im_pop × p15_kcal_pc_calibrated × 365`. Verified. Citation ✓; constraint type `=g=` ✓.
- **`im_gdp_pc_mer_iso` used for PPP/MER price bridging.** `intersolve.gms:25` `im_gdp_pc_ppp_iso / im_gdp_pc_mer_iso`. ✓
- **`im_physical_inactivity` drives PAL → BMR energy requirements.** `presolve.gms:189-191` (PAL), `194-197` (`p15_intake` = Schofield BMR × PAL). Answer's `presolve.gms:194-197` citation points at the BMR-scaling step it describes (the inactivity var itself enters at 190-191 — off by ~4 lines, but the cited lines do match the "scales BMR to energy requirements" clause). Not scored as a bug.
- **M16 (sector_may15) consumes ZERO M09 params; passive aggregator.** Verified: all 8 `im_*` return NONE in M16. ✓ (high-value negative finding, double-checked.)
- **`q16_supply_crops` (equations.gms:19-29)** = food+feed+processing+material+bioen+seed+waste+balanceflow → `vm_supply`. Verified; 8 equations total in file (q16_supply_crops/livestock/secondary/residues/pasture, q16_waste_demand, q16_seed_demand, q16_supply_forestry). ✓
- **`vm_supply` passed to M21 (Trade).** Verified: `vm_supply` in `modules/21_trade/selfsuff_reduced/equations.gms` (and other realizations). ✓
- **Feed channel: M70 (default fbask_jan16) consumes `im_pop`, `im_pop_iso`.** Verified preloop.gms/presolve.gms. ✓ Default `fbask_jan16` confirmed (config/default.cfg:2146).
- **M14 (managementcalib_aug19) consumes ZERO M09 params — the critical negative finding.** Verified TWICE with positive control: all 8 `im_*` → NONE; positive control `vm_tau` → hits. ✓✓ This is the single most important claim and it is correct.
- **`q14_yield_crop` (equations.gms:14-16)** `vm_yld = sum(ct,i14_yields_calib) × vm_tau / sum(...,fm_tau1995(h2))`. Verified verbatim via `sed`. ✓ (`fm_tau1995` confirmed as the real divisor — an earlier ripgrep display artifact briefly suggested `ln(h)`; `sed` extraction is authoritative and shows `fm_tau1995(h2)`.)
- **`q14_yield_past` (equations.gms:35-39)** structure correct (i14_yields_calib × pm_past_mngmnt_factor × spillover term). ✓ (coefficient issue → B1.)
- **M13 (endo_jan22) consumes `im_gdp_pc_ppp_iso`.** Verified `presolve.gms:26`. ✓ Produces `vm_tau` (declared `declarations.gms:13`). ✓
- **M14 upstream deps = M13, M52, M35, M70; none are M09.** Verified: M14 reads `vm_tau`(M13), `pm_past_mngmnt_factor`(M70), `fm_carbon_density`/`pm_carbon_density_*_ac`(M52), `im_growing_stock`(M35). Matches module_14.md §7.2. ✓
- **Climate scenario `c14_yields_scenario` independent of SSP; default `cc`.** `modules/14_yields/managementcalib_aug19/input.gms:8` + config/default.cfg:360. ✓ Decoupling claim correct.

---

## Bugs Found

### Bug QN-B1
- **Severity:** Minor
- **Class:** 4 (conceptual pseudo-code / formula fidelity) — MANDATE 1
- **Trigger:** "Wrong detail, but a careful reader wouldn't be misled into action" (§1 Minor). Number is correct, so the §1 Major "right concept, wrong number" trigger does NOT fire.
- **Claim in answer:** q14_yield_past rendered as `... * (1 + 0.25 * (pcm_tau(j,"crop")/fm_tau1995(h) - 1))` in Stage 4 prose and in the diagram (`[1 + 0.25*(tau-1)]`).
- **Reality in code:** The coefficient is the named scalar `s14_yld_past_switch`, not a hardcoded `0.25`. `modules/14_yields/managementcalib_aug19/equations.gms:39`: `* (1 + s14_yld_past_switch*(... pcm_tau(j2,"crop")/fm_tau1995(h2)) - 1))`. Default value IS 0.25 (`input.gms:20` `/ 0.25 /`; `config/default.cfg:366` `s14_yld_past_switch <- 0.25`), so the number is correct, but the answer hides a user-tunable switch and misrepresents the equation as having a magic constant. A user wanting to change pasture spillover would search for `0.25` and miss the switch.
- **File evidence:** `modules/14_yields/managementcalib_aug19/equations.gms:39`; default `modules/14_yields/managementcalib_aug19/input.gms:20`, `config/default.cfg:366`.
- **Root cause:** answerer_style_or_framing (default-value substitution / simplification).

### Bug QN-B2
- **Severity:** Minor
- **Class:** 7-adjacent (producer/input mischaracterization) — MANDATE 7
- **Trigger:** "Wrong detail" (§1 Minor). Tie-breaker pulls down from Major: the chain direction and the parameter's role as the 1995 baseline are both stated correctly elsewhere in the answer, so harm is localized to the verb.
- **Claim in answer:** "Module 13 (Technological Change), which consumes `im_gdp_pc_ppp_iso` ... and **produces** `vm_tau(j,"crop")` and `fm_tau1995(h)`." Diagram likewise lists `fm_tau1995(h)` as an M13 output flowing into M14.
- **Reality in code:** `fm_tau1995` is a static INPUT data parameter (1995 baseline tau), loaded from a file — `modules/13_tc/endo_jan22/input.gms:51-56` (`parameter fm_tau1995(h) ... $include "./modules/13_tc/input/fm_tau1995.cs4"`). M13 does not compute it; it reads it into `pc13_tau` (`preloop.gms:18`). The `fm_` prefix marks it as a file-loaded interface parameter. `vm_tau` IS produced by M13 (`declarations.gms:13`), so that half is correct.
- **File evidence:** `modules/13_tc/endo_jan22/input.gms:51-56`, `preloop.gms:18`; M14 reads the same `fm_tau1995` at `modules/14_yields/managementcalib_aug19/equations.gms:16,39`.
- **Root cause:** answerer_confabulation (conflated "M13 owns this input parameter" with "M13 computes it").

### Bug QN-B3
- **Severity:** Minor
- **Class:** 4 (conceptual simplification of a data mapping)
- **Trigger:** "Wrong detail" (§1 Minor).
- **Claim in answer:** Stage 1 input-file table maps `f09_gdp_ppp_iso.csv` → `im_gdp_pc_ppp_iso(t_all,iso)` with units "USD17PPP/cap/yr" (and analogously `f09_gdp_mer_iso.csv` → `im_gdp_pc_mer_iso` / `im_gdp_pc_mer`).
- **Reality in code:** The raw file `f09_gdp_ppp_iso` is a TOTAL GDP table — `input.gms:26` `table f09_gdp_ppp_iso(t_all,iso,pop_gdp_scen09) ... (mio. USD17PPP per yr)` — 3-D including the `pop_gdp_scen09` scenario dimension. `im_gdp_pc_ppp_iso` is PER-CAPITA, computed in `preloop.gms:24,53` by dividing total GDP by population and selecting the scenario. The table thus pairs a raw total-GDP, scenario-indexed file directly with a derived per-capita parameter and lists the parameter's units against the file, eliding both the per-capita transform and the scenario dimension. A careful reader could think the CSV directly holds per-capita USD17PPP. (Prose elsewhere DOES correctly explain the SSP2 lock / scenario selection, which mitigates the omission.)
- **File evidence:** `modules/09_drivers/aug17/input.gms:26-39` (raw total tables, 3-D); `preloop.gms:14-20,24,30,42-44,51-53` (per-capita derivation + scenario select); `declarations.gms:20,29` (per-capita parameter dims `(t_all,i)` / `(t_all,iso)`).
- **Root cause:** answerer_style_or_framing (table compression).

---

## Informational (noted, not scored)
- **I1 — diagram shorthand `vm_yld_past`** is not a real variable; the prose correctly uses `vm_yld(j,"pasture",w)`. Diagram-only; careful reader sees the correct name two paragraphs up.
- **I2 — dropped `sum(ct,...)` wrappers** in the rendered `q15_food_demand` (nutrition term and `f15_household_balanceflow`) and `q16_supply_crops` (`f16_domestic_balanceflow`) formulas. Equations otherwise faithful; index labels simplified (i/j vs i2/j2). Simplified-rendering, not a fabrication.
- **I3 — M13 mechanism gloss + omitted co-consumer.** Answer says M13 GDP "drive[s] technology adoption rates"; the code path is a GDP-share *cap* on tech spending: `vm_tech_cost.up(i) = sum(...,im_gdp_pc_ppp_iso(ct,iso) * im_pop_iso(ct,iso)) * s13_max_gdp_shr`, active only when `m_year > sm_fix_SSP2` (`presolve.gms:21-26`). Direction (GDP→TC→yields) is correct. Answer also omitted that M13 co-consumes `im_pop_iso` on the same line. Both are tangential to the question's focus; the gloss is doc-sourced (see latent note).

---

## Latent doc bugs (doc_errors_latent — fixed regardless of score)

- **module_09.md:864** — "Module 13 (tc): GDP affects technology adoption rates" (and line 208 "Technology adoption (Module 13)"). **Code reality:** `im_gdp_pc_ppp_iso × im_pop_iso` sets an upper *bound* on `vm_tech_cost.up(i)` as a share of regional GDP (`s13_max_gdp_shr`), and only when `m_year > sm_fix_SSP2` — `modules/13_tc/endo_jan22/presolve.gms:21-26`. It is a spending cap to prevent unrealistically high endogenous TC investment, not a direct "adoption rate" driver. The answer reproduced this gloss (so it did NOT beat the doc; root cause is `doc_error`, propagated). **Severity: Minor** by future-reader harm — directionally correct and the CONSUMER SET in module_09.md:337 (`Module 13 ← im_gdp_pc_ppp_iso, im_pop_iso`) is CORRECT and matches code, so this is NOT an R20-class wrong-set Critical. Recommend tightening the one-line mechanism phrasing to "GDP-share cap on tech-cost (`vm_tech_cost.up`, via `s13_max_gdp_shr`)".

No load-bearing consumer/producer SET in the docs the answer relied on (module_09.md §5.2, module_14.md §7.2, module_15.md, module_16.md) was found wrong vs code — those sets were re-verified against the develop worktree and match.

---

## Summary
The answer nails the question's spine — both chain shapes, the parameter/file carriers, and the two high-value negative findings (M14 and M16 consume zero M09 parameters), all verified against develop with positive controls. Three Minor imprecisions: (B1) hardcoded `0.25` for the `s14_yld_past_switch` scalar (value correct, structure hidden), (B2) `fm_tau1995` mislabeled as "produced" by M13 when it is a file-loaded input baseline, (B3) input-file table conflates raw total-GDP files with derived per-capita interface parameters. Score: 10 − 3×1 = **7**. One latent doc imprecision (module_09.md:864 M13 mechanism gloss) recorded for fixing; the doc's consumer/producer sets are correct.
