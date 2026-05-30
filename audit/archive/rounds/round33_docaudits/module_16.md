# Audit Report: module_16.md (Demand, sector_may15)

**Doc**: `/Users/turnip/Documents/Work/Workspace/magpie/magpie-agent/modules/module_16.md`
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree), `config/default.cfg`
**Auditor**: round33 doc-audit (Opus, adversarial)
**Date**: 2026-05-30

## Overall Verdict: SIGNIFICANT ERRORS (consumer-set section)
## Accuracy Score: 6/10

The doc's **equation core is excellent** — all 8 equations, all formulas, all `equations.gms`/`declarations.gms`/`input.gms` line citations, all input-variable SOURCE attributions, all set definitions, and the default realization are verified correct. The damage is concentrated in two derived/templated sections:
1. **"Provides Output To"** (lines 564-572) — fabricated variable→module consumer attributions.
2. **"Dependency Chains → Depends on"** (line 705) — wrong producer-module list, internally contradicting the doc's own correct "Receives Input From".
3. **Conservation-law equation** (line 694) — two invented GAMS variable names (`vm_import`, `vm_export`).

The doc's self-assessment ("Zero errors found", "100% verified", lines 666/680) is therefore false for these sections.

---

## Verified Claims (correct)

- **Default realization `sector_may15`**: `config/default.cfg:608` → `cfg$gms$demand <- "sector_may15"`. Only one realization dir exists (`ls /tmp/magpie_develop_ro/modules/16_demand/` → `sector_may15` only). Doc claim of single realization (line 550) CORRECT.
- **All 8 equation formulas**: match `equations.gms` verbatim (read lines 19-88). q16_supply_crops (19-29), livestock (31-38), secondary (40-49), residues (51-58), pasture (62-63), waste_demand (69-72), seed_demand (77-79), forestry (85-88). All location citations match.
- **Declarations**: `vm_supply` decl line 11, `v16_dem_waste` line 12, `vm_dem_seed` line 13 — all match. 8 equations declared 17-24 — matches.
- **Input citations**: f16_seed_shr (10-13), f16_waste_shr (15-18), fm_attributes (20-23), f16_domestic_balanceflow (25-28) — all match `input.gms`.
- **Input-variable SOURCE attributions** (lines 340-389): all 7 correct against declaring module:
  - `vm_dem_food`→M15 (`15_food/anthro_iso_jun22/declarations.gms`), `vm_dem_feed`→M70, `vm_dem_processing`→M20, `vm_dem_material`→M62 (`62_material/exo_flexreg_apr16`), `vm_dem_bioen`→M60, `vm_prod_reg`→M17 (`17_production/flexreg_apr16`), `vm_secondary_overproduction`→M20.
- **Usage-line citations** for input vars (lines 342,349,359,366,373,380,387): all verified by `sed -n` spot-check.
- **Sets** (lines 454-492): ksd/kres/kap/kli/kli_rd/kforestry elements all match `sets.gms:10-28`. Aliases `kap4`, `kforestry2` match `sets.gms:32-33`.
- **"Receives Input From"** (lines 556-562): M15, M70, M20, M62, M60, M17 — CORRECT and matches realization.gms:9-11 ("demand coming from 62_material, 60_bioenergy, 70_livestock, 15_food, 17_production").
- **M21 vm_supply consumer + citation** (line 568, `selfsuff_reduced/equations.gms:14`): VERIFIED — line 14 reads `sum(i2, vm_supply(i2,k_trade)) + ...`. `selfsuff_reduced` is the default trade realization (`config/default.cfg:650`).

---

## Bugs Found

### Bug module_16-B1 (CRITICAL) — phantom `vm_supply` consumers + omitted real path
- **Severity**: Critical
- **Class**: 15 (latent doc error / wrong consumer set) + 12 (content mismatch)
- **Trigger**: R20 anchor — "doc said wrong consumer set; user would have missed/added modules in a refactor". Wrong consumer SET.
- **Doc line**: module_16.md:567-572 ("Provides Output To" section)
- **Claim in doc**:
  - L567 "Module 20 (Processing): `vm_supply` - total supply available for processing"
  - L568 "Module 18 (Residues): `vm_supply` - residue supply for various uses"
  - L571 "Module 32 (Forestry): `vm_supply` - forestry product demand"
  - L572 "Module 53 (Methane): `vm_supply` - commodity flows for methane accounting"
  - L569 "Module 55 (AWMS): ... `vm_supply`"
  - L570 "Module 50 (Nitrogen): `vm_supply`, ..."
- **Reality in code**: `vm_supply` is read (in equations) ONLY by **Module 21 (Trade)**. M18/M20/M55/M50/M32/M53 do NOT reference `vm_supply` at all. M70 references it only in a `*'` interface COMMENT in `module.gms:18` (not an equation read).
- **File evidence**: `rg -n 'vm_supply' /tmp/magpie_develop_ro/modules/ -g '*.gms' | grep -v 16_demand` → all hits in `21_trade/{selfsuff_reduced,selfsuff_reduced_bilateral22,exo}/equations.gms`, plus the single `70_livestock/module.gms:18` comment. Per-module grep with positive controls: M18/M20/M55/M50/M32/M53 = NO MATCH for `vm_supply`; positive control (`vm_` / `vm_prod` / `vm_dem_processing`) IS found in each dir (grep works).
- **verify_cmd**: `rg -n 'vm_supply' /tmp/magpie_develop_ro/modules/18_residues/ -g '*.gms'` → (empty); positive control `rg -ln 'vm_prod' /tmp/magpie_develop_ro/modules/18_residues/ -g '*.gms'` → 2 files. (Repeated for M20/M55/M50/M32/M53, all empty for vm_supply, all positive controls hit.) Second method `grep -rn 'vm_supply' ... --include='*.gms' | grep -v 16_demand | grep -v 21_trade | grep -v 70_livestock/module.gms` → NO OTHER MATCHES.
- **Anchor reference**: R20 (`pm_carbon_density_ac` wrong consumer set → Critical).
- **Why the doc went wrong**: `realization.gms:11-13` says M16 "delivers data to 60_bioenergy, 21_trade, 20_processing, 18_residues, 55_awms, 50_nr_soil_budget, 32_forestry, 53_methane". That coarse-grained delivery is via the **`fm_attributes`** input table (declared in M16's `input.gms:20`, read by M55/M53/M18/etc. — confirmed) and via reporting, NOT via `vm_supply`. The doc mistakenly pinned `vm_supply` to each receiver.
- **Proposed fix**: Rewrite the `vm_supply` consumer lines. `vm_supply` is read in equations ONLY by Module 21. The "delivers to" relationship for M18/M20/M55/M50/M32/M53 is via the shared `fm_attributes` conversion table (and reporting), not `vm_supply`. Suggested replacement for the section (see B2/B3 for the seed/food lines):
  ```
  ### Provides Output To:
  - **Module 21** (Trade): `vm_supply` - regional supply/demand; the ONLY equation-level
    consumer of vm_supply (PRIMARY CONNECTION). Default realization selfsuff_reduced:
    modules/21_trade/selfsuff_reduced/equations.gms:14 (q21_trade_glo).
  - **Module 50** (Nitrogen): `vm_dem_seed` - seed N removed from the soil budget
    (modules/50_nr_soil_budget/macceff_aug22/equations.gms:42).
  - **Shared input table `fm_attributes`** (declared here, input.gms:20): read by many
    modules (e.g. 18_residues, 53_methane, 55_awms, 50, 20) for nutrient/DM/energy
    conversion. This - not vm_supply - is why realization.gms lists those modules as
    recipients. fm_attributes is a passed-through input parameter, not a vm_supply read.
  ```

### Bug module_16-B2 (MAJOR) — `vm_dem_seed` attributed to wrong module (M60 phantom; real consumer M50)
- **Severity**: Major
- **Class**: 15 (latent doc error / wrong consumer set)
- **Trigger**: §1 Major — wrong attribution that misleads about behavior. (Sits one notch below Critical because the correct consumer M50 IS listed elsewhere in the same section at L570, so the seed dependency is not wholly lost; but the M60 attribution is fabricated.)
- **Doc line**: module_16.md:566
- **Claim in doc**: "**Module 60** (Bioenergy): `vm_dem_seed` - seed demand (constraints on bioenergy crops)"
- **Reality in code**: M60 does NOT reference `vm_dem_seed` anywhere. The only consumer of `vm_dem_seed` outside M16 is **Module 50** (`50_nr_soil_budget/macceff_aug22/equations.gms:42`: `- vm_dem_seed(i2,kcr) * fm_attributes("nr",kcr)`).
- **File evidence**: `rg -n 'vm_dem_seed' /tmp/magpie_develop_ro/modules/60_bioenergy/ -g '*.gms'` → empty; positive control `rg -ln 'vm_dem_bioen' /tmp/magpie_develop_ro/modules/60_bioenergy/` → hits (grep works). Full set: `rg -n 'vm_dem_seed' .../modules/ -g '*.gms' | grep -v 16_demand` → only the M50 line.
- **verify_cmd**: `rg -n 'vm_dem_seed' /tmp/magpie_develop_ro/modules/60_bioenergy/ -g '*.gms'` → (empty, NO MATCH); `rg -n 'vm_dem_seed' /tmp/magpie_develop_ro/modules/ -g '*.gms' | grep -v 16_demand` → `50_nr_soil_budget/macceff_aug22/equations.gms:42`.
- **Proposed fix**: Delete line 566 ("Module 60 (Bioenergy): `vm_dem_seed` ..."). The real `vm_dem_seed` consumer is Module 50, already covered if B1's rewrite includes the M50/vm_dem_seed line. If keeping a separate bullet: "**Module 50** (Nitrogen): `vm_dem_seed` - seed N flux in the soil budget (modules/50_nr_soil_budget/macceff_aug22/equations.gms:42)."

### Bug module_16-B3 (MAJOR) — `vm_dem_food` falsely attributed to Module 55 (AWMS)
- **Severity**: Major
- **Class**: 15 (latent doc error / wrong consumer set)
- **Trigger**: §1 Major — wrong consumer attribution; misleads about which module reads the variable.
- **Doc line**: module_16.md:569
- **Claim in doc**: "**Module 55** (AWMS): `vm_dem_food`, `vm_supply` - food system flows for nutrient accounting"
- **Reality in code**: M55 references NEITHER `vm_dem_food` NOR `vm_supply`. `vm_dem_food` consumers outside M15/M16 are **M20** (`20_processing/substitution_may21/equations.gms:33`, sets it for milling cereals) and **M62** (`62_material/exo_flexreg_apr16/{postsolve,presolve}.gms`, reads `.l`). M55 connects to M16 only via the shared `fm_attributes` table.
- **File evidence**: `rg -n 'vm_dem_food' /tmp/magpie_develop_ro/modules/55_awms/ -g '*.gms'` → empty; positive control `rg -ln 'vm_' /tmp/magpie_develop_ro/modules/55_awms/` → hits. `rg -ln 'fm_attributes' /tmp/magpie_develop_ro/modules/55_awms/` → `ipcc2006_aug16/equations.gms` (the real M16→M55 interface).
- **verify_cmd**: `rg -n 'vm_dem_food' /tmp/magpie_develop_ro/modules/55_awms/ -g '*.gms'` → (empty); `rg -n 'vm_dem_food' /tmp/magpie_develop_ro/modules/ -g '*.gms' | grep -v 15_food | grep -v 16_demand` → M20 (eq:33) + M62 (postsolve/presolve) only.
- **Note**: vm_dem_food is also DECLARED in M15 and the doc's "Receives Input From" correctly says M16 reads it from M15. The error is the *output* claim that M55 reads M16's vm_dem_food (vm_dem_food is not even an M16 output — M16 reads it, M15 declares it). The whole L569 entry is wrong.
- **Proposed fix**: Delete line 569 ("Module 55 (AWMS): `vm_dem_food`, `vm_supply` ..."). If documenting the M16→M55 link, state it is via the shared `fm_attributes` input table (modules/55_awms/ipcc2006_aug16/equations.gms reads fm_attributes), not via vm_dem_food/vm_supply.

### Bug module_16-B4 (MAJOR) — "Depends on" producer list wrong (phantoms 09/18/73; omits 17/20), contradicts own "Receives Input From"
- **Severity**: Major
- **Class**: 6 (count/list drift) + 2 (wrong attribution)
- **Trigger**: §1 Major — fabricated/wrong list for a load-bearing dependency structure; internally inconsistent with lines 556-562.
- **Doc line**: module_16.md:705
- **Claim in doc**: "**Depends on**: Modules 09, 15, 18, 60, 62, 70, 73 (for demands)"
- **Reality in code**: M16 equations read interface variables produced by **M15, M70, M20, M62, M60, M17** (6 modules). Phantoms in the doc list: **M09 (drivers), M18 (residues), M73 (timber)** — M16 reads no interface variable from any of them. Omitted: **M17 (production, `vm_prod_reg`)** and **M20 (processing, `vm_dem_processing` + `vm_secondary_overproduction`)**.
- **File evidence**: All RHS interface vars in `16_demand/sector_may15/equations.gms`: `vm_dem_food`(M15), `vm_dem_feed`(M70), `vm_dem_processing`(M20), `vm_dem_material`(M62), `vm_dem_bioen`(M60), `vm_dem_seed`(self), `vm_secondary_overproduction`(M20), `vm_prod_reg`(M17). `realization.gms:9-11` independently confirms "62, 60, 70, 15, 17". The doc's OWN "Receives Input From" (556-562) correctly lists 15/70/20/62/60/17 — directly contradicting line 705.
- **verify_cmd**: `rg -no 'vm_[a-z_]+' /tmp/magpie_develop_ro/modules/16_demand/sector_may15/equations.gms | sort -u` → vm_dem_food/feed/processing/material/bioen/seed, vm_secondary_overproduction, vm_prod_reg, vm_supply. Cross-checked declaring modules (each grepped in `*/declarations.gms`): vm_dem_processing & vm_secondary_overproduction → 20_processing; vm_prod_reg → 17_production; (no var traces to 09/18/73).
- **Proposed fix**: Replace line 705 with: `**Depends on**: Modules 15, 17, 20, 60, 62, 70 (for demand and production inputs)` and update line 703 centrality text "depends on 7 modules" → "depends on 6 modules". (The "Receives Input From" section 556-562 is already correct and can be the canonical source.)

### Bug module_16-B5 (MAJOR) — conservation-law equation uses invented variables `vm_import`/`vm_export`; misrepresents default trade balance
- **Severity**: Major
- **Class**: 2 (hallucinated variable name) / 4 (conceptual pseudo-code presented as the model's equation)
- **Trigger**: §1 — "Invented variable name presented as authoritative" is a Critical trigger, but the tie-breaker pulls DOWN: this is inside a conceptual conservation-law block using the math symbol `≥` (not GAMS `=g=`) and labelled "Food Balance Equation", so it reads as a conceptual balance rather than a verbatim code quote. Net: Major (misleads about the default realization's structure; fabricated names).
- **Doc line**: module_16.md:694 (and the same form at the "Participates In → Conservation Laws" block ~693-695)
- **Claim in doc**: `vm_prod_reg(i,k) + vm_import(i,k) - vm_export(i,k) ≥ vm_supply(i,k)`
- **Reality in code**: `vm_import` and `vm_export` do NOT exist in ANY module. The DEFAULT trade realization (`selfsuff_reduced`) balance is a GLOBAL pool, not a bilateral import/export identity: `q21_trade_glo`: `sum(i2, vm_prod_reg(i2,k_trade)) =g= sum(i2, vm_supply(i2,k_trade)) + sum(ct, f21_trade_balanceflow(ct,k_trade))` (`modules/21_trade/selfsuff_reduced/equations.gms:13-15`).
- **File evidence**: `rg -ln 'vm_import\b|vm_export\b' /tmp/magpie_develop_ro/modules/ -g '*.gms'` → no files (NOT in any module); positive control `rg -lc 'vm_prod_reg' /tmp/magpie_develop_ro/modules/21_trade/` → hits (grep works). Actual eq read in `selfsuff_reduced/equations.gms`.
- **verify_cmd**: `rg -ln 'vm_import\b|vm_export\b' /tmp/magpie_develop_ro/modules/ -g '*.gms'` → "NOT in any module"; `cat .../21_trade/selfsuff_reduced/equations.gms` → q21_trade_glo global-pool form.
- **Proposed fix**: Replace the fenced equation at line 693-695 with the actual default-realization global balance and a note that no per-region import/export variables exist:
  ```
  **Food Balance Equation** (Module 21, default selfsuff_reduced - q21_trade_glo):
  sum(i, vm_prod_reg(i,k)) >= sum(i, vm_supply(i,k)) + f21_trade_balanceflow(k)
  ```
  Add: "MAgPIE's default trade does not use per-region vm_import/vm_export variables; it enforces a global supply>=demand pool (see modules/21_trade/selfsuff_reduced/equations.gms:13-15)."

### Bug module_16-B6 (INFORMATIONAL/MINOR) — `vm_prod_reg` cited at line 78, actual reference at line 79
- **Severity**: Informational (tie-breaker down from Minor; the equation block 77-79 is correctly cited and a reader sees vm_prod_reg on the adjacent line)
- **Class**: 10 (off-by-one citation)
- **Doc line**: module_16.md:380
- **Claim in doc**: "`vm_prod_reg(i,kcr)`: ... **Usage**: `equations.gms:78` (seed demand calculation)"
- **Reality in code**: line 78 is the LHS `vm_dem_seed(i2,kcr) =e=`; `vm_prod_reg` is on line 79.
- **File evidence**: `sed -n '78p;79p' .../16_demand/sector_may15/equations.gms` → 78 = `vm_dem_seed(i2,kcr) =e=`, 79 = `vm_prod_reg(i2,kcr) * sum(ct,f16_seed_shr(...))`.
- **verify_cmd**: `sed -n '79p' /tmp/magpie_develop_ro/modules/16_demand/sector_may15/equations.gms` → vm_prod_reg line.
- **Proposed fix**: Change `equations.gms:78` → `equations.gms:79` on line 380 (optional; very low priority).

---

## Refutation of the pre-run advisory checker lead

> CHECKER LEAD: "vm_supply consumer prose at module_16.md:568 lists M18 with NO grep-hit (possible phantom) AND omits M70/livestock (which has grep-hits)."

- **M18 phantom**: CONFIRMED. M18 does not reference `vm_supply` (positive control: `vm_prod` IS in M18). → folded into Bug B1.
- **"omits M70/livestock (which has grep-hits)"**: REFUTED as an omission to ADD. The only M70 grep-hit for `vm_supply` is `70_livestock/module.gms:18`, inside a `*'` documentation COMMENT ("pasture module is organized via interfaces `vm_dem_feed`, `vm_supply` and ..."), NOT an equation/presolve/postsolve read. Per MANDATE 17 (direct vs transitive) and the open-paren discipline, a comment mention is NOT a consumer. **Do NOT add M70 as a vm_supply consumer.** The real and only equation-level consumer is M21. (This is exactly the co-located/comment false-positive the task warned about.)

---

## Deferred (not code-verifiable / out of scope)

- Whether the coarse "delivers to" set in `realization.gms:11-13` is best documented via `fm_attributes` + reporting is an editorial judgment; I verified `fm_attributes` is read by M55/M53/M18 (the plausible real channel) but did not exhaustively trace every recipient's exact M16-origin parameter.
- The "C5: Demand-Trade-Production" cycle framing and "Circular Dependencies Resolved" prose (waste/seed) are conceptual; the math (waste share < 1) is sound and not a code-checkable claim.
- Literature/FAO references (lines 637-645) not audited (out of scope).
- `vm_dem_food` is also populated/set by M20 for milling cereals (`q20_..` at eq:33) — a co-population relationship that the doc does not currently address; flagged for awareness, not scored as a bug (the doc's M15-source claim for M16's READ is correct).

---

## Summary

Equation core, formulas, citations, sets, input data, and input-variable sources: all verified correct (the doc is genuinely strong here). The errors cluster in the derived/templated dependency sections. **B1 (Critical)**: `vm_supply` is read in equations ONLY by Module 21, but the doc attributes it to M18/M20/M55/M50/M32/M53 (all phantom; the real shared interface to those modules is the `fm_attributes` input table). **B2/B3 (Major)**: `vm_dem_seed` falsely pinned to M60 (real consumer = M50); `vm_dem_food` falsely pinned to M55 (real consumers = M20/M62). **B4 (Major)**: "Depends on 09/15/18/60/62/70/73" is wrong and self-contradictory (real: 15/17/20/60/62/70). **B5 (Major)**: conservation eq invents `vm_import`/`vm_export` and misrepresents the default global-pool trade balance. The advisory's M18-phantom lead is confirmed; its "add M70" lead is REFUTED (M70's only hit is a doc comment, not a consumer).
