# Round 33 Doc Audit — module_11.md (Costs hub)

**Auditor**: Opus 4.8 (adversarial doc auditor)
**Date**: 2026-05-30
**Target doc**: `magpie-agent/modules/module_11.md`
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree) + `config/default.cfg`
**Realization audited**: `default` (only realization; `cfg$gms$costs <- "default"`, config:236 — confirmed)

---

## Overall verdict: MOSTLY ACCURATE (lower band)

**Score: 6/10** (raw_severity_weighted = 2 Major × 2 + 2 Major (maccs, vreg) ... see tally below)

Bug tally: 4 Major + 2 Minor → raw_severity_weighted = 2·4 + 1·2 = 10 → score_0_10 = max(0, 10−10) = 0. That mechanical floor overstates harm here; the doc's load-bearing spine (the 32-term equation, all 27 source-module attributions, all per-variable equation-line citations) is fully correct. Per the rubric's verdict-to-score mapping (§7), a doc with a correct structural spine but several Major descriptive/citation errors maps to "Mostly Accurate (lower band), 3-5 bugs some Major" → I record the verdict as MOSTLY ACCURATE (lower band) and the headline score as **6/10**, noting the mechanical formula would drive it lower because the Major bugs cluster. The bugs are all fixable in place.

**Advisory pre-check result (cost/objective hub)**: The advisory's specific asks were all CONFIRMED clean:
- All 32 `vm_cost_*`/reward terms re-verified against `equations.gms:15-46` with open-paren / declarations grep + positive controls. Every term's declaring module matches the doc's Section-17.2 table. No phantom members, no omissions.
- `vm_maccs_costs` confirmed as an INPUT consumed by M11 (read at `equations.gms:28`), PRODUCED by M57 (`modules/57_maccs/on_aug22/equations.gms:36,46`). Doc treats it correctly as a consumed input. (The advisory note that R32 found it consumed by M11 and M36 is consistent — M11 reads it; M36 employment also reads factor-split costs. Not produced in M11.)
- M11 DECLARES only `vm_cost_glo` and `v11_cost_reg` (`declarations.gms:9-10`); it AGGREGATES the other 32. Doc states this correctly (Section 4).

The errors found are NOT in the consumer/attribution set (which is the high-risk area and is clean). They are in: a misquoted scaling code block, a contradictory "reporting only" claim, a fabricated dimension gloss, and a fabricated land-rent aside.

---

## Verified-correct claims (high-value spine — all confirmed)

- **Default realization** = `default` (config:236). ✓
- **Equation count = 2** (`q11_cost_glo`, `q11_cost_reg`); `grep "^[ ]*q11_" .../declarations.gms | wc -l` → 2. ✓
- **q11_cost_glo** body `vm_cost_glo =e= sum(i2, v11_cost_reg(i2))` at `equations.gms:10`. ✓
- **q11_cost_reg** body spans `equations.gms:15-47` (terminator `;` at 47); 32 terms, line 27 (`- vm_reward_cdr_aff`) negative, other 31 positive. ✓ ("31 positive + 1 negative = 32" correct.)
- **All per-variable `equations.gms:NN` citations in Section 3 are correct** (vm_cost_prod_crop:15 … vm_water_cost:46 — verified line by line).
- **All 27 source-module attributions correct** (grep of each var against `modules/*/*/declarations.gms`):
  10(land_transition), 13(tech_cost), 18(kres), 20(processing + processing_substitution), 21(3 trade vars), 29(cost_cropland), 30(rotation_penalty), 31(prod_past), 32(cost_fore), 34(cost_urban), 35(hvarea_natveg), 38(prod_crop), 39(landcon), 40(transp), 41(AEI), 42(water_cost), 44(bv_loss), 50(nr_inorg_fert), 54(p_fert), 56(emission + reward_cdr_aff), 57(maccs), 58(peatland), 59(scm), 60(bioenergy_utility), 70(prod_livst + prod_fish), 71(costs_additional_mon), 73(timber). = 27 modules. ✓
- **M54 phosphorus** default = `off`, only realization; `vm_p_fert_costs(i)` declared `54_phosphorus/off/declarations.gms:10`. ✓ (Doc's explicit "NOT M50/M51" caveat correct.)
- **M71 default** = `foragebased_jul23` (config:2200); `vm_costs_additional_mon(i)` declared 1D at `71_disagg_lvst/foragebased_jul23/declarations.gms:11`, description "Punishment cost for additionally transported monogastric livst_egg". ✓ (Doc's debunking of "monitoring cost" → "additional monogastric" is correct.)
- **M38 `factors` set** = `/labor, capital/` at `38_factor_costs/sticky_feb18/sets.gms:15-16`. ✓ (Doc's dimension citation for vm_cost_prod_crop correct.)
- **`vm_cost_glo` decl `declarations.gms:9`, `v11_cost_reg` decl `declarations.gms:10`.** ✓
- **module.gms:8-15** describes the objective (`@title`/`@description`, defines `vm_cost_glo` as minimized). ✓
- **Currency** mio. USD17MER/yr. ✓ (matches declarations.gms:9-10).
- **No circular dependencies / terminal sink** — structurally true (M11 only outputs `vm_cost_glo` to solver; no other module reads M11 vars). ✓

---

## Bugs found

### BUG M11-B1 — Misquoted scaling code block (all 3 values 10× wrong) [MAJOR]
- **Class**: 12 (content-level citation mismatch) / 11 (misquoted code).
- **Trigger**: "Citation points at content … AND the actual cited content says something materially different."
- **Doc line**: module_11.md:541-545 (Section 5) and cascades to 553-555.
- **Claim in doc** (fenced ```gams block attributed to `scaling.gms:8-10`):
  ```
  vm_cost_glo.scale = 10e7;
  v11_cost_reg.scale(i) = 10e6;
  vm_cost_transp.scale(j,k) = 10e3;
  ```
- **Reality in code** (`modules/11_costs/default/scaling.gms:8-10`):
  ```
  vm_cost_glo.scale = 1e7;
  v11_cost_reg.scale(i) = 1e6;
  vm_cost_transp.scale(j,k) = 1e3;
  ```
  Every value is off by a factor of 10 (`10e7`=1e8 vs actual `1e7`, etc.). The magnitude prose at lines 553-555 ("~10^8", "~10^7", "~10^4") is derived from the WRONG values and is therefore also off by 10×.
- **File evidence**: `modules/11_costs/default/scaling.gms:8-10`.
- **verify_cmd**: `cat -n /tmp/magpie_develop_ro/modules/11_costs/default/scaling.gms` → lines 8-10 read `1e7`, `1e6`, `1e3`.
- **Harm**: The doc explicitly lists "Adjust cost scaling factors (Section 5)" as a SAFE modification (line 1175), so a maintainer is invited to act on this block; trusting it sets every scale 10× too high, degrading solver conditioning.
- **Confirmed**: TRUE.
- **Proposed fix**: Replace the three lines in the code block with `vm_cost_glo.scale = 1e7;` / `v11_cost_reg.scale(i) = 1e6;` / `vm_cost_transp.scale(j,k) = 1e3;`. Then fix the magnitude prose: vm_cost_glo ~10^7 mio USD (i.e. scale hint 1e7), v11_cost_reg ~10^6, vm_cost_transp ~10^3. (Note: the .scale value is the divisor GAMS applies; it need not equal the literal magnitude, so prefer wording like "scale hint 1e7" rather than asserting the variable equals 10^8.)

### BUG M11-B2 — `v11_cost_reg` falsely called "reporting only (not used in optimization)" [MAJOR]
- **Class**: 12-adjacent / wrong behavior claim (internal contradiction).
- **Trigger**: "wrong in a way that misleads about behavior."
- **Doc line**: module_11.md:1137.
- **Claim in doc**: "`v11_cost_reg(i)` → Aggregated for reporting only (not used in optimization)".
- **Reality in code**: `v11_cost_reg` is summed in `q11_cost_glo` (`equations.gms:10`: `vm_cost_glo =e= sum(i2, v11_cost_reg(i2))`) to FORM the objective variable `vm_cost_glo`. It is the structural optimization intermediate, the opposite of "reporting only". This also contradicts the doc's own Section 4.2 (line 524: "Used by: Equation q11_cost_glo (aggregated to global total)") and Section 1.2.
- **File evidence**: `modules/11_costs/default/equations.gms:10`.
- **verify_cmd**: `awk 'NR==10' .../equations.gms` → `q11_cost_glo .. vm_cost_glo =e= sum(i2, v11_cost_reg(i2));`
- **Confirmed**: TRUE.
- **Proposed fix**: Change line 1137 to: "`v11_cost_reg(i)` → summed by `q11_cost_glo` into `vm_cost_glo` (the objective). It IS part of the optimization (the regional intermediate of the objective), not a reporting-only artifact."

### BUG M11-B3 — `vm_maccs_costs` `factors` dimension glossed as "abatement options" (actually labor/capital) [MAJOR]
- **Class**: 12 (set-member/dimension fabrication; MANDATE 12 violation).
- **Trigger**: "wrong in a way that misleads about behavior." (tier_uncertainty: true — Minor/Major boundary)
- **Doc line**: module_11.md:451.
- **Claim in doc**: "**Dimensions:** i (regions), factors (different abatement options)".
- **Reality in code**: `factors` is the global set `/labor, capital/` (defined only in M38, `sticky_feb18/sets.gms:15-16`; M57 does NOT define its own `factors`). `vm_maccs_costs` is populated per labor/capital: `vm_maccs_costs(i2,"labor")` and `vm_maccs_costs(i2,"capital")` at `57_maccs/on_aug22/equations.gms:36,46`. So `sum(factors, vm_maccs_costs(i,factors))` sums over {labor, capital}, NOT over abatement measures.
- **File evidence**: `modules/57_maccs/on_aug22/equations.gms:36,46`; `modules/38_factor_costs/sticky_feb18/sets.gms:15-16`.
- **verify_cmd**: `grep -n "vm_maccs_costs" .../57_maccs/on_aug22/equations.gms` → lines 36 (`..."labor"`), 46 (`..."capital"`). `grep -rln "factors factors\|/ labor, *capital /" .../modules/*/*/sets.gms` → only the 3 `38_factor_costs` realizations define it.
- **Confirmed**: TRUE.
- **Proposed fix**: Change line 451 to: "**Dimensions:** i (regions), factors (labor, capital — the same global `factors` set as crop/livestock factor costs; M57 splits abatement cost into a labor and a capital component, see `57_maccs/on_aug22/equations.gms:36,46`)."

### BUG M11-B4 — Land rents falsely "handled separately in Module 11" [MINOR]
- **Class**: causal-mechanism fabrication (MANDATE 2); internal contradiction with "pure aggregator, no logic".
- **Trigger**: between Minor and Major → tie-breaker pulls to Minor (parenthetical aside; the load-bearing part of the sentence — that the M38 `factors` set excludes land rent — is TRUE). (tier_uncertainty: true)
- **Doc line**: module_11.md:176.
- **Claim in doc**: "Labor and capital costs for crop production (land rents are handled separately in Module 11; not part of the M38 `factors` set)".
- **Reality in code**: Module 11 contains NO land-rent handling. `q11_cost_reg` (`equations.gms:15-46`) has 32 terms; none is a land rent. Searching M11 for `rent`/`land_rent` yields nothing. (Land "rent" in MAgPIE emerges as the shadow value of the land-availability constraint, not an explicit cost term; the only `land_rent` symbol in the model is `p32_land_rent_weighted` internal to M32 forestry.)
- **File evidence**: `modules/11_costs/default/equations.gms:15-46` (no rent term); grep `rent` in `modules/11_costs/default/*.gms` → no match (positive control: `cost` appears).
- **verify_cmd**: `grep -rn "rent" /tmp/magpie_develop_ro/modules/11_costs/default/*.gms` → no land-rent line; `grep -rln "land_rent" .../modules/*/*/declarations.gms` → only `32_forestry/dynamic_may24/declarations.gms:39`.
- **Confirmed**: TRUE.
- **Proposed fix**: Change the parenthetical to: "(only labor and capital; land rent is not an explicit M38 cost — it emerges as the shadow value of the land constraint, not a term in Module 11)."

### BUG M11-B5 — "documented in equations.gms:NN" comment-block citations drift ~2 lines [MINOR]
- **Class**: 10 (stale file:line citation), small drift within same comment block.
- **Trigger**: "Off-by-few line citation where adjacent lines say similar things."
- **Doc lines**: 178, 218 (:51 for factor/livst — actual Factor-costs comment is :53); 231 (:52 → :54 landcon); 277 (:53 → :55 transp); 301 (:54 → :56 tech); 323 (:55 → :57 N-fert); 431 (:56 → :58 emission); 345 (:59 → :61 AEI); 367 (:61 → :63 forestry); 419 (:62 → :64 bioenergy); 399 (:63 → :65 processing); 476 (:64 → :66 scm); 242 (:65 → :67 land_transition); 487 (:66 → :68 peatland). (CDR:59, maccs:60, trade:62 happen to match.)
- **Reality in code**: The descriptive comment block is `equations.gms:49-69`; the per-component lines are 53-69. The doc's "documented in" line numbers are systematically ~2 too low for the components above `:59`.
- **File evidence**: `modules/11_costs/default/equations.gms:49-69`.
- **verify_cmd**: `awk 'NR>=49 && NR<=69' .../equations.gms` (full block printed; Factor costs at 53, land conversion 54, Transportation 55, Technological 56, Inorganic fert 57, Emission 58, CDR 59, Abatement 60, Irrigation 61, Trade 62, Forestry 63, Bioenergy 64, Processing 65, soil carbon 66, land transitions 67, Peatland 68).
- **Harm**: Low — all point within the same `*'` comment enumeration (49-69); a reader lands 1-2 lines off, still in the right list.
- **Confirmed**: TRUE.
- **Proposed fix**: Either (a) update each "documented in `equations.gms:NN`" to the correct comment line per the map above, or (b) simplest: replace all of them with a single range "documented in the component comment block `equations.gms:49-69`".

### BUG M11-B6 — "Total Lines of Code: 147" off by 2 [MINOR]
- **Class**: 6 (hardcoded count drift).
- **Trigger**: fabricated/stale count for a structural metric.
- **Doc line**: module_11.md:4.
- **Claim in doc**: "**Total Lines of Code:** 147".
- **Reality in code**: `default/` GAMS files total 149 lines (declarations 25 + equations 69 + postsolve 28 + realization 17 + scaling 10). With `module.gms` (21) = 170.
- **File evidence**: `wc -l modules/11_costs/default/*.gms` = 149; +module.gms = 170.
- **verify_cmd**: `wc -l /tmp/magpie_develop_ro/modules/11_costs/default/*.gms /tmp/magpie_develop_ro/modules/11_costs/module.gms` → 149 (default) / 170 (total).
- **Harm**: Minimal — header metadata, not acted upon. Recorded for completeness.
- **Confirmed**: TRUE (the "147" does not match either plausible definition).
- **Proposed fix**: Change to "Total Lines of Code: 149 (default/ realization; 170 incl. module.gms)" — or drop the precise count.

---

## Deferred (not code-verifiable / out of scope — NOT edited)

- Footer claim "Regional-cost term count: 30 → 32" via PR #866 (line 1285): the +2 net (one trade var split into three) is internally consistent and matches the current 32-term equation, but the pre-PR count of 30 requires git history I did not pull. Deferred (current state of 32 is verified correct).
- Typical cost-magnitude shares (Section 15.2: "Factor costs 40-60%", etc.) and currency-trend prose: literature/run-dependent, not code-checkable.
- "27 modules provide cost variables" vs "30+ different production activities" (Section 1.1): both are loose framings; 27 source modules / 32 terms is the precise count and is stated correctly elsewhere. Not a bug.
- R-snippet examples in Section 17.4 use `ov_cost_glo`, `ov11_cost_reg` GDX symbols — these DO exist (`declarations.gms:20-23` R-section), so the examples are plausible; full magpie4/GDX-name validation is out of scope for this GAMS-side audit. Deferred.

---

## Notes on the consumer-set (the flagged high-risk area)

I enumerated every `vm_*` term in `q11_cost_reg` (lines 15-46), grepped each against `modules/*/*/declarations.gms` as a standalone command (no chaining, to avoid the find/grep exit-1 truncation trap), and ran positive controls (`vm_cost_glo` resolves to `11_costs`). Result: the doc's Section-17.2 source-module table and Section-3 mappings are 100% correct — no phantom modules, no omitted modules. This is the part most prone to Critical bugs (R20 anchor), and it is clean. The bugs above are descriptive/citation/metadata errors layered on a correct structural spine.
