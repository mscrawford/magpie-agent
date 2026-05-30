# Round 37 Doc Audit — module_20.md (Processing, substitution_may21)

**Auditor**: Opus adversarial doc auditor
**Date**: 2026-05-30
**Target doc**: `magpie-agent/modules/module_20.md`
**Ground truth**: `/tmp/magpie_develop_ro/modules/20_processing/substitution_may21/*.gms` + `config/default.cfg`

## Overall Verdict: MOSTLY ACCURATE (high quality)
## Accuracy Score: 8/10

This doc is unusually well-verified. All 10 equation names, all 10 equation formulas (set-sums preserved, no expansion), all 4 interface-variable declaration citations, all input.gms / presolve.gms / preloop.gms / sets.gms citations, the default realization, the `c20_scp_type` default, the kpr/knpr set membership, and the complete producer/consumer sets check out against develop. The only confirmed code-level error is a factor-of-10 mistake in the two scale factors. Remaining items are metadata/typo (Informational).

---

## Default realization & config (MANDATE 3, 8)

- `cfg$gms$processing <- "substitution_may21"` — `config/default.cfg:633`. Doc header + Realization line correct. ✓
- Only one realization dir exists: `ls /tmp/magpie_develop_ro/modules/20_processing/` → `substitution_may21` only. Doc's comparison to `substitution_dec18` is grounded in `realization.gms:9` code comment (a historical realization), not a phantom claim. ✓
- `c20_scp_type` default `"sugar"` — `config/default.cfg:642` AND `input.gms:8` (`$setglobal c20_scp_type sugar`). Doc:246,332,681 correct. ✓

---

## Verified claims (correct)

### Equation names + line citations (declarations.gms:27-38; equations.gms)
All 10 equations exist with exact names and the doc's cited line ranges match develop:
- q20_processing_aggregation_nocereals → equations.gms:22-24 ✓
- q20_processing_aggregation_cereals → equations.gms:32-33 ✓
- q20_processing_aggregation_cotton → equations.gms:40-41 ✓
- q20_processing → equations.gms:59-65 ✓
- q20_processing_substitution_oils → equations.gms:68-70 ✓
- q20_processing_substitution_sugar → equations.gms:73-75 ✓
- q20_processing_substitution_protein → equations.gms:81-89 ✓
- q20_processing_substitution_brans → equations.gms:93-97 ✓
- q20_processing_costs → equations.gms:115-121 ✓
- q20_substitution_utility_loss → equations.gms:134-142 ✓

All formulas reproduced faithfully (set-based sums preserved per MANDATE 10; the 200 USD literal, fm_attributes("nr",...) protein weighting, vm_prod_reg/balanceflow/shares RHS, scp cost term — all match).

### Interface variables (declarations.gms)
- vm_dem_processing → declarations.gms:16 ✓
- vm_secondary_overproduction → declarations.gms:19 ✓
- vm_cost_processing → declarations.gms:20 ✓
- vm_processing_substitution_cost → declarations.gms:24 ✓ (free `variables`, not positive — consistent with doc's "utility loss/cost" framing and code desc "Costs or benefits")

### Producer / consumer SETS (MANDATE 13, 17 — verified with rg + attribute-form grep + positive control)
**Provides To** (doc:664-666):
- vm_cost_processing → read by M11 `11_costs/default/equations.gms:36` ✓
- vm_processing_substitution_cost → read by M11 `11_costs/default/equations.gms:39` ✓
- vm_dem_processing → read by M16 `16_demand/sector_may15/equations.gms:23,44` ✓
- vm_secondary_overproduction → read by M16 `16_demand/sector_may15/equations.gms:72` ✓
No other external consumers. Attribute-form (`vm_*.l/.up/.fx/.m`) grep across all modules returned only M20's own presolve/postsolve/scaling — no hidden external consumers. Consumer set is COMPLETE and correct.

**Receives From** (doc:669-672):
- vm_prod_reg ← declared M17 `17_production/flexreg_apr16/declarations.gms`; read by M20 at equations.gms:41 (`"cottn_pro"`), :62 (`ksd`), :120 (`"scp"`). Doc:308 cites equations.gms:62 ✓. (Advisory R36 note re kcr/kap/kres: doc makes no kres claim; the actual slices are ksd/cottn_pro/scp — no bug.)
- vm_dem_food ← declared M15 `15_food/anthro_iso_jun22/declarations.gms` ✓
- fm_attributes — global parameter, used at equations.gms:84,89,95,97 (matches doc:310) ✓

### Advisory-checker items — RESOLVED
- "Verify default realization via config/default.cfg" → confirmed substitution_may21 (config:633).
- "Verify processing equations (q20_*) / vm_dem_processing / cm_processing; consumer/producer sets" → all q20_* verified; `cm_processing` does NOT exist in code AND the doc never claims it — no bug. Doc correctly uses `c20_scp_type`.
- "R36 confirmed M20 reads vm_prod_reg on kcr/kap (NOT kres)" → doc's vm_prod_reg description is generic ("regional production"); no kres mis-claim present.
- Both grep forms + positive control (kcereals20) run; consumer-set absence claims double-checked.

### Other citations spot-verified accurate
sets.gms:10-13 (kpr), 15-18 (knpr), 26-27 (kcereals20), 29-30 (no_milling_ginning20), 32-33 (oilcake_substitutes20), 35-36 (scptype), 38-39 (scen20); input.gms:8,10-13,15-18,20-23,25-28,30-33,35-38,40-43,45-50; preloop.gms:9,10,11,13-16,18-20; presolve.gms:9,11-12,14-19. All match. kpr (23 members) and knpr (19 members) lists complete, including `oilcakes` appearing in BOTH sets (matches code).

---

## Bugs found

### Bug 20-B1 — Scale factors off by 10× (both interface cost vars)
- **Severity**: Major (tier_uncertainty: true — between Minor and Major; scale factors are solver hints, but the doc cites them as exact code values and both are wrong by 10×)
- **Class**: 13 (wrong parameter value) / "wrong number"
- **Trigger** (§1 Major): "Right concept, wrong number ... off by a moderate factor."
- **Claim in doc** (module_20.md:253): "`vm_cost_processing.scale(i) = 10e5` (1 million USD) `scaling.gms:8`"
  and (module_20.md:280): "`vm_processing_substitution_cost.scale(i) = 10e4` (10,000 USD) `scaling.gms:9`"
- **Reality in code**: `scaling.gms:8` → `vm_cost_processing.scale(i) = 1e5;` (= 100,000, not 10e5=1,000,000). `scaling.gms:9` → `vm_processing_substitution_cost.scale(i) = 1e4;` (= 10,000, not 10e4=100,000).
- **File evidence**: `/tmp/magpie_develop_ro/modules/20_processing/substitution_may21/scaling.gms:8-9`
- **verify_cmd**: `grep -n "scale" .../scaling.gms` → `8:vm_cost_processing.scale(i) = 1e5;` / `9:vm_processing_substitution_cost.scale(i) = 1e4;`
- **Internal inconsistency**: doc:253 writes `10e5` but annotates "(1 million USD)" — 10e5 does equal 1e6, so the annotation matches the WRONG written value, not the code (code 1e5 = 100,000). doc:280 writes `10e4` but annotates "(10,000 USD)" — the annotation matches the CODE value (1e4 = 10,000) while the written `10e4` (=100,000) does not. So both lines are self-contradictory in opposite directions.
- **confirmed**: true
- **Proposed fix**: doc:253 → "`vm_cost_processing.scale(i) = 1e5` (100,000 USD) `scaling.gms:8`"; doc:280 → "`vm_processing_substitution_cost.scale(i) = 1e4` (10,000 USD) `scaling.gms:9`".

### Bug 20-B2 — Interface-output count mismatch (header says 3, doc lists 4)
- **Severity**: Informational
- **Class**: 6 (hardcoded count drift)
- **Trigger** (§1 Informational): metadata/style, reader not misled into action.
- **Claim in doc** (module_20.md:7): "**Interface Variables (Outputs)**: 3"
- **Reality**: The Outputs table (module_20.md:292-295) lists 4 vm_ outputs (vm_dem_processing, vm_secondary_overproduction, vm_cost_processing, vm_processing_substitution_cost). declarations.gms has 4 vm_ outputs (lines 16,19,20,24). The header value 3 is internally inconsistent with the doc's own table and with code.
- **File evidence**: `declarations.gms:16,19,20,24` (4 vm_ outputs)
- **verify_cmd**: `rg -n 'vm_' .../declarations.gms` → 4 vm_ output vars (vm_dem_processing, vm_secondary_overproduction, vm_cost_processing, vm_processing_substitution_cost).
- **confirmed**: true
- **Proposed fix**: module_20.md:7 → "**Interface Variables (Outputs)**: 4".

### Bug 20-B3 — Reversed line-range citation typo
- **Severity**: Informational
- **Class**: 10 (file:line citation) — typo, not drift
- **Trigger** (§1 Informational): syntax typo not changing meaning.
- **Claim in doc** (module_20.md:526): "Quality cost adjustments for oils `f20_quality_cost` provide some differentiation `equations.gms:142-132`."
- **Reality**: range is written backwards (142-132). The quality-cost prose/term lives at equations.gms:127-132 (quality cost description) and the term itself at equations.gms:140-142. Intended range is presumably `equations.gms:127-132` (or 134-142). The reversed range is a typo.
- **File evidence**: `equations.gms:127-132` (quality-cost prose) / `:140-142` (f20_quality_cost term)
- **verify_cmd**: `rg -n 'f20_quality_cost|quality' .../equations.gms` → prose 127-132; term applied 140-142.
- **confirmed**: true
- **Proposed fix**: module_20.md:526 → replace "`equations.gms:142-132`" with "`equations.gms:127-132`".

---

## Deferred (not code-verifiable here; NOT edited)

- `fm_attributes` declaration site: it is a global `fm_`-prefixed attributes parameter read at equations.gms:84,89,95,97; declaration is in a core/preprocessing-fed block I did not cleanly resolve via grep. Doc's characterization ("Global parameter", used in protein-based substitution) is correct by usage — no bug, just not declaration-site-confirmed.
- SCP "Land Requirement" column (doc:321-326) and conversion-factor example values (0.18, 0.77, 0.13 — explicitly labeled illustrative): these depend on .cs3/.csv input data I cannot parse. Doc labels them illustrative; not asserting them as code facts. No bug.
- Header metadata "Lines of Code: ~270" — approximate, non-load-bearing.

---

## Summary
Doc is high-accuracy: realization, defaults, all equation names/formulas/citations, full producer+consumer sets, and set membership all verified against develop. One real code-value bug (scale factors 10e5/10e4 should be 1e5/1e4 — Major, factor-of-10, self-contradictory annotations) plus two Informational items (output count 3 vs 4; reversed citation range 142-132). No phantom/omitted consumers, no inverted defaults, no fabricated names.
