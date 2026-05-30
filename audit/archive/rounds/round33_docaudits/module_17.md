# Round 33 doc audit — module_17.md (Production, flexreg_apr16)

**Auditor**: Opus adversarial doc-auditor
**Date**: 2026-05-30
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree) + `config/default.cfg`
**Target**: `magpie-agent/modules/module_17.md`

---

## Verdict: MOSTLY ACCURATE (lower band) — 1 Major behavior error + several Minor citation/consumer-set issues

The module's central code facts are correct: default realization is `flexreg_apr16` (config:612); the single equation `q17_prod_reg(i2,k)` sums cells→regions (`equations.gms:11`); set `k` has 28 primary members (M14 sets.gms:12-16); `c17_prod_init` default `on` (config:617, input.gms:8); the equation/variable declarations resolve. The doc's R23-lead UPDATE about M71 livestock disaggregation (default `foragebased_jul23`, config:2200) making `vm_prod_reg(i,kli_rum/kli_mon)` non-zero is SUBSTANTIVELY CORRECT and well-reasoned — the `realization.gms:14` `@limitations` comment IS genuinely stale.

**The one consequential error**: the doc applies that exact M71 reasoning to livestock but FAILS to apply it to timber. It repeatedly asserts wood/woodfuel "remain zero at cell level." Under the DEFAULT timber realization (`73_timber/default`, config:2205), `vm_prod(j,"wood")` and `vm_prod(j,"woodfuel")` ARE populated (`q73_prod_wood:43`, `q73_prod_woodfuel:52`) and q17 aggregates them. Only **fish** is genuinely zero at cell level.

Secondary: the consumer set of `vm_prod_reg` is mis-stated — M15 is a phantom direct consumer (M15 reads no `vm_prod*`), M38 and M71 (real direct consumers) are omitted, and §16.2 lists 7 transitive-only modules as if direct (MANDATE 17). The §16.1 "food balance" code block uses three non-existent variables (`vm_import`/`vm_export`/`vm_demand`).

---

## ADVISORY-CHECKER VERDICT

> "Expected default realization flexreg_apr16 … M17 doc may be stale relative to foragebased_jul23 … verify vm_prod_reg / q17_prod_reg regional-aggregation claims (sum cells→regions; don't over/under-state the set) and the consumer set."

- **Default flexreg_apr16**: CONFIRMED (config:612). Doc correct.
- **Aggregation direction (cells→regions)**: CONFIRMED. `vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k))` (`equations.gms:11`). Doc states it correctly throughout.
- **Set not over/under-stated**: equation over `k` (28 primary). CONFIRMED (M14 sets.gms:12-16; doc count "28" correct).
- **foragebased_jul23 staleness concern**: the doc has ALREADY been updated for this and is CORRECT on livestock. REFUTED as a doc error — the doc handles M71 well. BUT the same staleness applies to M73 timber and the doc did NOT catch it (Bug 17-01).
- **Consumer set**: CONFIRMED problematic (Bugs 17-02, 17-03, 17-04).

---

## VERIFIED-CORRECT claims (sample)

- `q17_prod_reg(i2,k) .. vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k))` — `equations.gms:10-11`. ✓ exact.
- 1 equation (`q17_prod_reg`). `grep "q17_" declarations.gms` → line 14 (eq) + line 25 (output param). Doc's anchored grep `^[ ]*q17_` → 1. ✓
- Set `k` = 28 primary commodities (incl. livestock/fish/wood/woodfuel). M14 `managementcalib_aug19/sets.gms:12-16`. ✓
- `vm_prod(j,k)` `declarations.gms:9`; `vm_prod_reg(i,kall)` `declarations.gms:10`; positive variables. ✓
- `c17_prod_init` default `on`: `input.gms:8` + config:617. ✓
- `pm_prod_init(j,kcr)=sum(w,fm_croparea("y1995",j,w,kcr)*pm_yields_semi_calib(j,kcr,w))` — `presolve.gms:10`. ✓ `pm_yields_semi_calib` declared in M14 (`managementcalib_aug19/declarations.gms`). ✓
- vm_prod crop formula `vm_prod(j2,kcr) =e= sum(w, vm_area*vm_yld)` — M30 `croparea/detail_apr24/equations.gms:15` (default `simple_apr24` also populates). ✓
- M71 default `foragebased_jul23` (config:2200) constrains cell livestock: `vm_prod(j2,kli_mon)` in `q71_prod_mon_liv` (`foragebased_jul23/equations.gms:55-59`). ✓ Citation correct.
- realization.gms:14 `@limitations` "not applied to livestock" IS stale. ✓ Doc's flag correct.
- Direct consumers of `vm_prod_reg` (code-enumerated): M16, M18, M20, M21, M38, M50, M70, M71 = 8 modules.

---

## BUGS

### 17-01 (Major) — wood/woodfuel are NOT zero at cell level (M73 default populates them)
- **doc_line**: module_17.md:31 (also :171, :311, :476, :715)
- **Claim**: "Fish (`fish`) and wood products (`wood`, `woodfuel`) remain zero at cell level." (:31); "wood products … remain zero at cell level — M17 aggregates them to zero" (:311); "Produce non-zero aggregation for livestock, fish, or wood products (current limitation — vm_prod is not populated for these)" (:715).
- **Reality**: Default timber realization `73_timber/default` (config:2205 `cfg$gms$timber <- "default"`) DEFINES cell-level `vm_prod(j2,"wood")` via `q73_prod_wood` and `vm_prod(j2,"woodfuel")` via `q73_prod_woodfuel`. q17_prod_reg(i,k) then aggregates these (wood, woodfuel ∈ k) into `vm_prod_reg(i,"wood"/"woodfuel")`. This is the SAME situation the doc correctly identified for livestock (M71) but failed to apply to timber (M73). Only **fish** is genuinely zero at cell level (no module populates `vm_prod(j,"fish")`).
- **file_evidence**: `modules/73_timber/default/equations.gms:43-50` (q73_prod_wood), `:52-60` (q73_prod_woodfuel)
- **verify_cmd**: `grep -n "q73_prod_wood\|q73_prod_woodfuel" /tmp/magpie_develop_ro/modules/73_timber/default/equations.gms` → `43:q73_prod_wood(j2)..` `52:q73_prod_woodfuel(j2)..`; `grep -n "timber <-" config/default.cfg` → `2205:cfg$gms$timber <- "default"`. Cross-check fish: `grep -rn 'vm_prod(j2,"fish")' modules/` → no hit (fish cell-level genuinely zero).
- **confirmed**: true
- **proposed_fix**: Globally replace the "wood/woodfuel remain zero at cell level" narrative with the timber-default reality. At :31 change to: "Fish (`fish`) remains zero at cell level (no module populates `vm_prod(j,'fish')`). Wood and woodfuel are ALSO populated at cell level under the default timber realization `73_timber/default` (`q73_prod_wood` / `q73_prod_woodfuel`, `modules/73_timber/default/equations.gms:43-60`) and aggregated to `vm_prod_reg(i,'wood'/'woodfuel')` by q17." Update :171, :311 (Section 7.2 must say forestry IS populated by M73 default, not zero), :476, and :715 (remove wood from the "remain zero" list; keep only fish).

### 17-02 (Major) — M15 (Food Demand) falsely claimed as a direct consumer of vm_prod_reg
- **doc_line**: module_17.md:18 (also :166, :277-279, :608, :722, :750)
- **Claim**: "Module 15 (Food Demand) compares against consumption requirements" (:18); "Module 15 (Food Demand): Production to compare against consumption needs" (:166); "Module 15 (Food Demand): Compares `vm_prod_reg` against demand to check food security" (:277-278).
- **Reality**: M15 (`15_food`) references NO `vm_prod*` variable. The supply-vs-demand balance is enforced in M21 (trade) using `vm_supply` (declared in M16), not M15. M15 computes food demand only; it is not a direct consumer of M17's output.
- **file_evidence**: M15 has zero `vm_prod_reg`/`vm_prod` hits; M21 `selfsuff_reduced/equations.gms:13-14` is the balance (`sum vm_prod_reg =g= sum vm_supply + balanceflow`).
- **verify_cmd**: `grep -rln "vm_prod" /tmp/magpie_develop_ro/modules/15_food/` → (empty, exit 1); positive control `grep -rln "vm_dem_food" .../15_food/` → 3 files (grep works). `rg -ln "vm_prod_reg" .../15_food/` → empty.
- **confirmed**: true
- **proposed_fix**: Remove M15 from the vm_prod_reg consumer lists, OR reframe as indirect: "Food balance: regional production (`vm_prod_reg`) is balanced against demand by Module 21 (trade) using `vm_supply`; Module 15 supplies the demand side but does not read `vm_prod_reg` directly." Apply at :18, :166, :277-279, :608, :722. Keep M21 as the real balancer.

### 17-03 (Major) — Real direct consumers M38 and M71 omitted from all consumer lists
- **doc_line**: module_17.md:162-167 (§4.1), :786-799 (§16.2), :608-611 (§12.1)
- **Claim**: §4.1/§12.1 "Provided to: Module 21, Module 15, Module 20"; §16.2 lists 13 dependers (15,16,18,20,21,50,51,53,55,60,62,70,73) — neither M38 nor M71 appears anywhere.
- **Reality**: M38 (factor_costs, default `sticky_feb18`) reads `vm_prod_reg(i2,kcr)` (`sticky_feb18/equations.gms:16`) to compute `vm_cost_prod_crop`. M71 (disagg_lvst, default `foragebased_jul23`) reads `vm_prod_reg(i2,kli_rum)` (`foragebased_jul23/equations.gms:37`) and `vm_prod_reg(i2,kli_mon)` (`:57`). Both are direct consumers. Per the R20 anchor, omitting real consumers from a list a refactorer relies on is the documented Critical-prone pattern (here Major: §16.2 frames the list as the dependency set used for modification-safety reasoning at §16.4).
- **file_evidence**: `modules/38_factor_costs/sticky_feb18/equations.gms:16`; `modules/71_disagg_lvst/foragebased_jul23/equations.gms:37,57`
- **verify_cmd**: `for f in $(rg -ln "vm_prod_reg" /tmp/magpie_develop_ro/modules/ --glob "*.gms"); do echo $f; done` → includes 38_factor_costs/sticky_feb18 + per_ton_fao_may22, 71_disagg_lvst/foragebased_jul23 + foragebased_aug18. `grep -n "vm_prod_reg" .../38_factor_costs/sticky_feb18/equations.gms` → line 16.
- **confirmed**: true
- **proposed_fix**: Add to §16.2 dependers list: "Module 38 (factor_costs): `vm_prod_reg(i,kcr)` → crop factor (labor/capital) cost (`sticky_feb18/equations.gms:16`)" and "Module 71 (disagg_lvst): reads `vm_prod_reg(i,kli_rum/kli_mon)` for cellular livestock disaggregation (`foragebased_jul23/equations.gms:37,57`)". Also reflect M38 in §4.1/§12.1 if those lists are meant to be representative. State the code-verified direct-consumer set is {16,18,20,21,38,50,70,71}.

### 17-04 (Minor) — §16.2 lists transitive-only modules (15,51,53,55,60,62,73) as direct dependers (MANDATE 17)
- **doc_line**: module_17.md:787,793,794,795,796,797,799
- **Claim**: §16.2 presents M15,M51,M53,M55,M60,M62,M73 among "Modules that depend on Module 17" with specific mechanisms, implying direct consumption.
- **Reality**: None of these reads `vm_prod_reg` (or `vm_prod`) directly. They depend on production only transitively (e.g., M51/M50-chain N flows, M53 residue CH4, M60 bioenergy feedstock). M73 is actually an UPSTREAM populator of cell-level `vm_prod(j,kforestry)` (`q73_prod_wood/woodfuel`), not a downstream consumer of `vm_prod_reg` — a direction error. Per MANDATE 17, one-hop/transitive consumers must be labeled as such, not listed as direct.
- **file_evidence**: zero `vm_prod_reg` hits in modules 15,51,53,55,60,62,73; M73 writes `vm_prod(j2,kforestry)` at `73_timber/default/equations.gms:26,44,53`.
- **verify_cmd**: `for m in 15_food 51_nitrogen 53_methane 55_awms 60_bioenergy 62_material 73_timber; do echo $m; grep -rl "vm_prod_reg" /tmp/magpie_develop_ro/modules/$m/ | wc -l; done` → all 0 (cross-checked rg + grep -rl; positive control M21=3).
- **confirmed**: true
- **proposed_fix**: In §16.2, split the list into "Direct consumers of `vm_prod_reg` (grep-verified): 16, 18, 20, 21, 38, 50, 70, 71" and "Indirect/transitive dependents (depend on production downstream, do NOT read `vm_prod_reg`): 15, 51, 53, 55, 60, 62". Move M73 to the UPSTREAM/populator side: "Module 73 (timber) populates cell-level `vm_prod(j,'wood'/'woodfuel')`, which q17 aggregates — M73 is upstream, like M30/M31/M71, not a consumer."

### 17-05 (Minor) — wrong equation attributed for cell-level ruminant constraint
- **doc_line**: module_17.md:31 (also :310, :550)
- **Claim**: "constrains `vm_prod(j, kli_rum)` via `q71_feed_forage` (`modules/71_disagg_lvst/foragebased_jul23/equations.gms:21-24`)".
- **Reality**: Lines 21-24 are `q71_feed_forage(j2)`, which DEFINES forage feed requirements as a function of ruminant production (references `vm_prod(j2,kli_rum)` on the RHS at :23). The equation labeled "Production constraint for ruminant livestock products" in `declarations.gms:19` is `q71_feed_rum_liv(j2,kforage)` (`equations.gms:14-17`: forage `vm_prod` ≥ feed need). Ruminant cell production is bounded by the conjunction of `q71_feed_rum_liv` + `q71_feed_forage`, not by `q71_feed_forage` alone. (The mono claim `q71_prod_mon_liv:55-59` IS correct.)
- **file_evidence**: `modules/71_disagg_lvst/foragebased_jul23/equations.gms:14-17` (q71_feed_rum_liv), `:21-24` (q71_feed_forage), declarations.gms:19 (label).
- **verify_cmd**: `cat -n .../foragebased_jul23/equations.gms` → q71_feed_rum_liv at 14-17, q71_feed_forage at 21-24; `grep -n "q71_feed_rum_liv" declarations.gms` → line 19 "Production constraint for ruminant livestock products".
- **confirmed**: true
- **proposed_fix**: Change to: "constrains `vm_prod(j, kli_rum)` indirectly: `q71_feed_rum_liv` (`…/foragebased_jul23/equations.gms:14-17`) requires forage production ≥ feed need, where the feed need is set by `q71_feed_forage` (`:21-24`) as a function of ruminant production." Apply at :31, :310, :550.

### 17-06 (Minor) — citation `declarations.gms:9,11` mislabeled as the equation declaration
- **doc_line**: module_17.md:29 (also :309)
- **Claim**: "Equation declared over: Full set `k` … (`declarations.gms:9,11`)" (:29); "The equation `q17_prod_reg(i2,k)` IS declared over the full set `k` … — `declarations.gms:9,11`" (:309).
- **Reality**: `declarations.gms:9` is the VARIABLE `vm_prod(j,k)`; line 11 is the closing `;`. The EQUATION `q17_prod_reg(i,k)` is declared at `declarations.gms:14`. The substance ("declared over k") is true, but the cited lines point at the variable declaration, not the equation declaration.
- **file_evidence**: `modules/17_production/flexreg_apr16/declarations.gms:14` (`q17_prod_reg(i,k)`); line 9 = `vm_prod(j,k)`.
- **verify_cmd**: `cat -n .../17_production/flexreg_apr16/declarations.gms` → 9:`vm_prod(j,k)`, 11:`;`, 14:`q17_prod_reg(i,k)`.
- **confirmed**: true
- **proposed_fix**: Change citation to `declarations.gms:14` (equation declaration). If the intent is to also show `vm_prod`/`vm_prod_reg` are over k/kall, cite `declarations.gms:9,10,14`.

### 17-07 (Minor) — §2.1 mislabels set `k` as "plant commodities"
- **doc_line**: module_17.md:69
- **Claim**: "**k**: Plant commodities (crops + pasture, subset of kall)".
- **Reality**: `k` (28 members) is the full PRIMARY-products set (crops, pasture, livestock, fish, wood, woodfuel), not just plants. The doc itself states this correctly at :24/:29 (k = 28). Plant commodities = `kve` (20). Internal inconsistency.
- **file_evidence**: M14 `managementcalib_aug19/sets.gms:12-16` (k = 28 incl. livst_*, fish, wood, woodfuel); `kve` = 20 (lines 18-21).
- **verify_cmd**: `sed -n '12,26p' .../14_yields/managementcalib_aug19/sets.gms` → k lists 28 incl. livestock/fish/wood/woodfuel.
- **confirmed**: true
- **proposed_fix**: Change :69 to "**k**: Primary commodities (28 members: crops, pasture, livestock, fish, wood, woodfuel; subset of kall). The summed `vm_prod(j2,k)` is currently non-zero for crops, pasture (M30/31), ruminant/monogastric livestock (M71) and wood/woodfuel (M73); fish is zero at cell level."

### 17-08 (Minor) — §16.1 "food balance" code block uses three non-existent variables
- **doc_line**: module_17.md:752
- **Claim**: ```vm_prod_reg(i,k) + vm_import(i,k) - vm_export(i,k) = vm_demand(i,k)``` attributed to "Equation (Module 21, trade)".
- **Reality**: `vm_import`, `vm_export`, `vm_demand` do not exist anywhere in the modules tree. The default trade equation (`21_trade/selfsuff_reduced/equations.gms:13-14`) is an INEQUALITY using `vm_supply`: `sum(i2, vm_prod_reg(i2,k_trade)) =g= sum(i2, vm_supply(i2,k_trade)) + balanceflow`. This is a conceptual identity inherited from `nitrogen_food_balance.md`, but it is fenced as GAMS and attributed to M21, so a reader may take the variable names as real (MANDATE 7). Tie-broken to Minor because the surrounding prose frames it as the food-balance concept and the load-bearing M17 variable (`vm_prod_reg`) is correct.
- **file_evidence**: `modules/21_trade/selfsuff_reduced/equations.gms:13-14`; no `vm_import`/`vm_export`/`vm_demand` in tree.
- **verify_cmd**: `grep -rln "vm_import\|vm_export\|vm_demand " /tmp/magpie_develop_ro/modules/` → empty; positive control `vm_supply` found in M16 declarations; `sed -n '13,14p' .../21_trade/selfsuff_reduced/equations.gms`.
- **confirmed**: true
- **proposed_fix**: Label the block as conceptual and use real names: "Conceptually (food balance identity): regional production + net imports ≈ demand. In the default trade realization this is `sum(i, vm_prod_reg(i,k_trade)) =g= sum(i, vm_supply(i,k_trade)) + balanceflow` (`modules/21_trade/selfsuff_reduced/equations.gms:13-14`); `vm_supply` (M16) carries the demand side." Or cross-reference nitrogen_food_balance.md as the source of the simplified identity and note the names are illustrative.

---

## DEFERRED (not code-verifiable here / out of scope — do NOT edit)
- "Total Lines of Code: 115" (:4): actual sum of 7 .gms files = 124. Likely a counting-convention difference (blank/comment exclusion); header metadata, not load-bearing. Not flagged.
- Centrality "Rank 7th of 46", "Total Connections 14 (provides to 13, depends on 1)" (:776-778): graph metrics sourced to `Module_Dependencies.md`; not directly code-derivable (depends on the graph's edge definition). The "13" is inconsistent with the 8 code-verified direct consumers, but the metric may count multiple interface vars / looser edges — defer to Module_Dependencies.md.
- §16.3 circular-dependency cycles (Production-Yield-Livestock; Demand-Trade-Production): sourced to `circular_dependency_resolution.md`; conceptual graph claims, not single-file code checks.
- §16.1 "Not in carbon/nitrogen balance" (:766-769): modeling-role statement (M17 doesn't TRACK C/N; M50 uses vm_prod_reg for N). Defensible framing; not a clear code error.
- presolve.gms range citations `:12-16` vs actual if-block `:12-18` (close paren at 18): off-by-2 on range end in a 19-line file with matching content. Informational; not flagged.
- Module 30 labeled "(Crop)" in several places (actual name `30_croparea`; cropland is M29): common shorthand, module number correct, vm_prod equation does live in M30. Not flagged.
- "v1.2 rubric" doc-quality framing, Section 13 "future realizations" (none implemented): forward-looking, no code claim.
