# M70 adversarial audit (R58)

Target: `modules/module_70.md` (1343 lines) vs `../modules/70_livestock/` @ develop 0d7ebeb90.
Auditor derived all ground truth by reading the `.gms` files directly. No `scripts/check_*.py` artifact was read or consulted.

## Denominator

**claims_evaluated: 186**

What I counted: one claim per independently-checkable assertion. Concretely —
- 20 equation-level claims (7 default + 2 sticky equations × {name, formula, citation, constraint type})
- 34 `file:line` citations (realization.gms ×14, equations.gms ×9, presolve.gms ×11 — each resolved by reading the cited line)
- 27 identifier claims (variable/parameter/equation/set/scalar names, prefixes, dimensions)
- 24 default-value claims (every `s70_*` scalar, every `c70_*` switch, config/default.cfg realization) — verified **cfg-first**: `config/default.cfg` is the operative default for every `Rscript start.R` run and overrides the `input.gms` literal, so the literal alone is not authoritative. All 11 M70 keys present in default.cfg match their `input.gms` literal exactly (`c70_feed_scen` ssp2, `c70_fac_req_regr` glo, `s70_past_mngmnt_factor_fix` 2005, `s70_scavenging_ratio` 0.385, `s70_feed_intake_weight_balanceflow` 1, `s70_cereal_scp_substitution` 0, `s70_foddr_scp_substitution` 0, `s70_feed_substitution_start` 2025, `s70_feed_substitution_target` 2050, `s70_multiplicator_capital_need` 1). Four scalars are cfg-absent, so their literal *is* operative (`s70_pyld_intercept` 0.24, `s70_depreciation_rate` 0.05, `s70_subst_functional_form` 1, and the two dead `c70_*_scp_scen` switches). Every doc `(default: N)` claim therefore holds under either reading — none of the 14 findings turns on this axis.
- 21 producer/consumer/data-flow-direction claims (interface variables in both directions)
- 17 input-file claims (8 data files × {name, dimensions} + scenario set membership)
- 13 set-membership/count claims (sys, sys_to_kli, kap, kli_rum, kli_rd, kcer70, feed_scen70, fadeoutscen70, factors, scen_countries70)
- 12 mechanism descriptions (scavenging flag, SCP fader, pasture mgmt factor, sticky capital, balance-flow bounds…)
- 10 preloop.gms citations + formulas
- 8 summary-statistic / metadata counts

What I EXCLUDED from the denominator (not counted, not scored):
- Prose interpretation with no code referent ("Interpretation:", "Rationale:", "Why the Distinction?", the 10 "Key Assumptions and Limitations" narratives except where they cite a line).
- "Expected Pattern" blocks in §Interpretation and Use Cases — these are behavioral predictions, not code claims.
- `Centrality: HIGH (Rank #6)` and `Risk Level: MEDIUM-HIGH` — these reference `core_docs/Module_Dependencies.md`, not code. Unchecked; see Coverage honesty.
- Duplicate restatements of a claim already counted at its first occurrence (e.g. `s70_scavenging_ratio = 0.385` appears 4×, counted once).

Result: **14 findings** against 186 claims. 172 claims verified correct. The doc's citation hygiene is genuinely good — 33 of 34 `file:line` citations resolve to the right content. The defects cluster almost entirely in the **cross-module consumer sets** and in **config-surface claims**, not in the equation algebra.

---

## Findings

### F1: `vm_feed_balanceflow` is documented as internal-only; Module 71 (default realization) consumes it in two equations

- **severity**: Critical
- **self_named_class**: `phantom-internal interface` — an interface variable whose external consumer set is documented as *empty* ("used internally") when it is non-empty. Distinct from an ordinary incomplete-consumer-list because the doc makes an affirmative negative claim ("internally") rather than merely omitting a name.
- **fits_existing_taxonomy**: unsure. It is adjacent to "wrong producer/consumer set", but the harm mechanism is different: an omission invites a reader to go look; an affirmative "internal" tells them not to. I invented the class because the negative-assertion property is what makes it Critical rather than Major.
- **doc_location**: `modules/module_70.md:702-707`
- **doc_says**: "**3. Feed Balance Flows** (`declarations.gms:17`): `vm_feed_balanceflow(i,kap,kall)  // mio. tDM` — Used internally for FAO consistency and scavenging adjustments — Contributes to `vm_dem_feed` via `q70_feed`"
- **code_says**: `vm_feed_balanceflow` is read by Module 71 (`disagg_lvst`), whose default realization is `foragebased_jul23` (`config/default.cfg:2218`), in **two** equations: `q71_feed_balanceflow_nlp(j2)` reads `vm_feed_balanceflow(i2,kli_rum,kforage)` and `q71_feed_balanceflow_lp(i2)` reads it again. `kforage` = {pasture, foddr}. The non-default `foragebased_aug18` realization reads it too. So M70→M71 is a live, default-active interface edge on the pasture/fodder disaggregation path.
- **code_evidence**: `modules/71_disagg_lvst/foragebased_jul23/equations.gms:36`, `modules/71_disagg_lvst/foragebased_jul23/equations.gms:46`, `modules/71_disagg_lvst/foragebased_aug18/equations.gms:31`, `config/default.cfg:2218`; declared `modules/70_livestock/fbask_jan16/declarations.gms:17`
- **why_it_matters**: This is the exact shape of the anchor precedent. A reader doing modification-impact analysis on M70 — which the doc invites, being flagged "⚠️ MEDIUM-HIGH RISK (Hub module)" — would conclude `vm_feed_balanceflow` has no external consumers and is safe to rescope, rename, or restrict to `kli_rum × pasture`. Any of those silently breaks the cellular forage balance flow in M71's default realization. The doc compounds this: it *does* discuss M71 at line 714, but only to explain that M71's `vm_costs_additional_mon` is unrelated to M70's costs — so it looked at M71 and still recorded the consumer edge as absent. M71 appears nowhere in §Downstream Dependencies (1139-1145) or §Related Modules (1236-1244).
- **confidence**: high

### F2: `c70_cereal_scp_scen` / `c70_foddr_scp_scen` are inert `$setglobal`s, documented as the functional SCP scenario control

- **severity**: Major (I argue below it is defensibly Critical; per the "pick the LOWER tier" rule I record Major)
- **self_named_class**: `inert-switch documented as live control` — a declared-but-never-expanded config switch presented as the mechanism's selector. Sub-property: the switch is also absent from `config/default.cfg`, so it has no config surface at all.
- **fits_existing_taxonomy**: **no.** Existing severity language covers *wrong* defaults, *inverted* defaults, and *invented* names. This name is real, its documented default value is real and correctly transcribed, and its documented effect is nil. Nothing in the given tiers names "the identifier is real, the value is right, and the wire is not connected."
- **doc_location**: `modules/module_70.md:404-406`, `790-800`, `1193`
- **doc_says**: line 404-406: "**Switches** (`input.gms:18-19`): `c70_cereal_scp_scen`: Cereal substitution scenario (default: "constant" = no substitution); `c70_foddr_scp_scen`: Fodder substitution scenario (default: "constant" = no substitution)". Line 1193 (use-case recipe): "Configure: `c70_cereal_scp_scen = "lin_50pc_20_50"`, `s70_cereal_scp_substitution = 0.5`"
- **code_says**: `c70_cereal_scp_scen` and `c70_foddr_scp_scen` occur in exactly 4 places in the entire repository — the `$setglobal` lines in each of the two realizations' `input.gms`. They are never expanded (`%c70_cereal_scp_scen%` does not exist), never compared, never used to index anything. They are also **not present in `config/default.cfg`** (which does carry `cfg$gms$c70_feed_scen`, `c70_fac_req_regr`, and all the `s70_*` SCP scalars). Positive control: `%c70_feed_scen%` IS expanded at `preloop.gms:19-21`, and `cfg$gms$c70_feed_scen` IS at `config/default.cfg:2170`. The actual SCP substitution is driven entirely by `s70_cereal_scp_substitution` / `s70_foddr_scp_substitution` (magnitude), `s70_subst_functional_form` (linear vs sigmoid), and `s70_feed_substitution_start` / `_target` (timing) — `preloop.gms:40-55`.
- **code_evidence**: `modules/70_livestock/fbask_jan16/input.gms:18-19` (only definition site); `modules/70_livestock/fbask_jan16/preloop.gms:40-55` (actual mechanism, no reference to the c70 switches); `config/default.cfg:2170` (c70_feed_scen present) vs. absence of any `c70_*_scp_scen` line in default.cfg; `config/default.cfg:2191,2193,2197,2199,2201` (the s70 scalars that ARE the control surface). **Empirical confirmation from a real solved run**: `output/BAU_TCendo/full.gms` (the fully expanded model as actually solved) contains the literal string `c70_cereal_scp_scen` — i.e. the `$setglobal` line was carried through into the model verbatim and never expanded or consumed by anything.
- **why_it_matters**: A user following the doc's own §SCP Substitution Impact recipe sets `c70_cereal_scp_scen = "lin_50pc_20_50"` and expects the scenario name to select the fader shape, target, and window. It selects nothing. The recipe only works by accident because it *also* sets `s70_cereal_scp_substitution = 0.5` — but the window (2025→2050) then comes from `s70_feed_substitution_start/target`, not from the `_20_50` in the scenario name, so a user picking `lin_zero_20_30` gets a 2025→2050 fader, silently. A user who sets only the c70 switch gets zero substitution and a plausible-looking run. That is a silent wrong-number outcome, which is why I think Critical is defensible; I record Major because the doc's paired recipe happens to produce the intended behavior.
- **confidence**: high

### F3: Module 36 is missing from the `vm_cost_prod_livst` consumer set; the M70↔M36 reciprocal edge is undocumented

- **severity**: Major
- **self_named_class**: `half-duplex interface` — the doc records one direction of a genuinely bidirectional module coupling and presents the module as purely upstream. Detection rule this implies: any module named as an *input* provider must also be grepped as an *output* consumer.
- **fits_existing_taxonomy**: no — "wrong producer/consumer set" describes the symptom but not the generative cause. The cause here is a structural blind spot: once M36 was filed under "Inputs from Other Modules", it became ineligible for the outputs list. The doc lists M36 correctly in three places, all upstream, and never once downstream.
- **doc_location**: `modules/module_70.md:709-714` (§Outputs, item 4), `1139-1145` (§Downstream Dependencies), `1236-1244` (§Related Modules), `1132-1137` (§Upstream, where M36 correctly appears)
- **doc_says**: line 714: "**To Module 11 (Costs)**: `vm_cost_prod_livst` and `vm_cost_prod_fish` enter `q11_cost_reg` directly (see module_11.md §3)." Line 1242: "**Module 36 (Employment)**: Provides wage scenario parameters for labor cost scaling" — upstream framing only.
- **code_says**: Module 36's default realization `exo_may22` reads `vm_cost_prod_livst(i2,"labor")` inside `q36_employment(i2)`, where it is summed with `vm_cost_prod_crop(i2,"labor")` and divided by hourly costs to yield employment. So M70 produces a labor-cost input to M36, while M36 produces `pm_hourly_costs` and `pm_productivity_gain_from_wages` that M70's `q70_cost_prod_liv_labor` consumes. M11 is correct but is not the only consumer.
- **code_evidence**: `modules/36_employment/exo_may22/equations.gms:24`; `modules/11_costs/default/equations.gms:18-19`; `modules/70_livestock/fbask_jan16/equations.gms:59-62` (the reverse direction)
- **why_it_matters**: Two harms. (1) Someone rescaling, renaming, or re-dimensioning `vm_cost_prod_livst` breaks `q36_employment` with no warning from the doc. (2) The doc's §Circular Dependencies (1147-1151, 1319-1326) enumerates only the 70→16→21→17→70 cycle. The 70→36→70 cycle (M70 labor costs → M36 employment; M36 wage/productivity params → M70 labor costs) is real and unlisted — and it is a cycle the doc had every ingredient to spot, since it documents both halves separately.
- **confidence**: high

### F4: §Participates In inverts the M70↔M14 dependency direction and contradicts the doc's own upstream list

- **severity**: Major
- **self_named_class**: `metadata-block dependency inversion` — a summary/metadata footer that reverses an edge the body of the same document gets right. The interesting property is *intra-document* contradiction: the doc is simultaneously right (line 540, 720, 1141) and wrong (line 1315, 1322) about the same edge.
- **fits_existing_taxonomy**: unsure — "wrong data-flow direction" names it, but not the pattern that the error lives only in a metadata block that no one regenerated when the body was fixed. That staleness pattern is the actionable part.
- **doc_location**: `modules/module_70.md:1315`, `1322`
- **doc_says**: line 1315: "**Depends on**: Modules 14 (yields), 17 (production), 70 (self - feed baskets)". Line 1322: "**Production-Yield-Livestock Cycle**: Module 17 (production) → 14 (yields) → **70 (livestock)** → 17"
- **code_says**: M70 reads **nothing** from M14. Across all 9 `.gms` files of `fbask_jan16` the identifiers consumed from other modules are: `vm_prod_reg` (M17), `pm_factor_cost_shares` (M38), `pm_hourly_costs` + `pm_productivity_gain_from_wages` (M36), `pm_kcal_pc_initial` (M15), `im_pop` + `im_pop_iso` (M09), plus core `fm_attributes` / `fm_nutrition_attributes` / `sm_fix_SSP2`. No `vm_yld`, no `i14_*`, no M14 identifier of any kind. The edge runs the other way: M70 *produces* `pm_past_mngmnt_factor`, which M14 consumes in `q14_yield_past`. The doc's own §Critical Module Dependencies (1132-1137) lists the correct upstream set (09, 15, 17, 36, 38) and correctly omits 14. `not_used.txt` further confirms the default realization deliberately does not take `pm_interest`.
- **code_evidence**: `modules/14_yields/managementcalib_aug19/equations.gms:35-39` (`q14_yield_past` reads `pm_past_mngmnt_factor`); `modules/70_livestock/fbask_jan16/presolve.gms:63-68` (M70 produces it); `modules/70_livestock/fbask_jan16/not_used.txt`; absence of any M14 identifier across `modules/70_livestock/fbask_jan16/*.gms` (all 9 files read in full this session)
- **why_it_matters**: A reader consulting the compact §Participates In block — which is precisely the block a fast lookup lands on — gets a 3-module upstream set that is wrong in every element: it invents M14, and it drops M09, M15, M36, and M38, four real upstream providers the body of the same doc lists correctly. "Depends on: 70 (self - feed baskets)" is not a module dependency at all. The reversed 14→70 edge also propagates into the §Circular Dependencies claim at 1322, manufacturing a cycle that does not close.
- **confidence**: high

### F5: Scavenging-flag activation timing — doc says "first future timestep", code computes it in the last *historical* timestep

- **severity**: Major
- **self_named_class**: `guard-condition phase misread` — the doc narrates *when* a presolve block fires by reading the block's intent rather than evaluating its guard. Here the outer guard is a membership test in `t_past`, which is the exact negation of the doc's claim.
- **fits_existing_taxonomy**: no. Nothing in the tier language covers "the mechanism is right, the algebra is right, the *timestep it fires in* is wrong." It is not a citation drift (the citation is correct) and not a wrong default.
- **doc_location**: `modules/module_70.md:125`, `1086-1087`
- **doc_says**: line 125: "**Scavenging Flag Calculation** (`presolve.gms:14-20`): Flag activated in first future timestep after historical period". Line 1087: "Flag calculation only executed in first future timestep after historical period to avoid overwriting in subsequent timesteps."
- **code_says**: the outer guard is `if (sum(sameas(t_past,t),1) = 1, ...` — true **iff the current timestep t is itself in `t_past`**, i.e. iff t is a *historical* timestep. It can never be true in a future timestep. The inner guard `if (ord(t) = smax(t2, ord(t2)$(t_past(t2))) AND card(t) > sum(t_all$(t(t_all) and t_past(t_all)), 1), ...` narrows to the **last historical timestep**, and only when future timesteps exist at all. So `p70_endo_scavenging_flag` is computed in the last historical timestep's presolve and then persists (it is a parameter, and the outer guard never fires again) through every future timestep. The doc's own "to avoid overwriting in subsequent timesteps" reasoning is right; its identification of the firing timestep is not.
- **code_evidence**: `modules/70_livestock/fbask_jan16/presolve.gms:14-20`; same code at `modules/70_livestock/fbask_jan16_sticky/presolve.gms:14-20`
- **why_it_matters**: The flag gates `q70_feed_balanceflow` (`equations.gms:25-29`) between exogenous FAO balance flows and endogenous scavenging. A reader who trusts the doc believes the **last historical year still uses exogenous FAO balance flows** and that endogenous scavenging begins one timestep later. It does not — the switch to endogenous scavenging happens *inside* the last historical timestep, in flagged regions. Anyone validating M70 against FAO history in that year, or attributing a discontinuity to the historical/future boundary, is off by one timestep and looking on the wrong side of the seam. Two independent doc locations state it, so it is not a typo.
- **confidence**: high

### F6: Sticky capital-stock dynamics omit the postsolve carry-forward, leaving a mechanism that only decays

- **severity**: Major
- **self_named_class**: `phase-partial mechanism` — the doc reconstructs a multi-phase parameter's lifecycle from one phase (presolve) and never checks the other phases, yielding a mechanism that is locally accurate and globally wrong.
- **fits_existing_taxonomy**: no — it is an omission, not a contradiction; every sentence the doc writes is true of presolve. The defect only exists at the level of the assembled mechanism. Existing tiers score statements, not assemblies.
- **doc_location**: `modules/module_70.md:265-267`, `1123-1128` (§Execution Sequence)
- **doc_says**: "**Capital Stock Update** (`fbask_jan16_sticky/presolve.gms`): First timestep: `p70_capital = p70_capital_need × p70_initial_1995_prod`; Subsequent timesteps: `p70_capital = p70_capital × (1 - s70_depreciation_rate)^timestep_length`". §Execution Sequence lists postsolve as only: "Update pasture feed demand parameter for next timestep (`postsolve.gms:9`)".
- **code_says**: both quoted presolve branches are exact. But `fbask_jan16_sticky/postsolve.gms:13` adds the missing third branch: `p70_capital(t+1,i,kli) = p70_capital(t,i,kli) + v70_investment.l(i,kli);` — realized investment is accumulated into the *next* timestep's stock. Without it the described stock decays monotonically from its 1995 initialization and `q70_investment` would demand ever-growing investment; with it, capital accumulates and the "sticky" path dependency the doc describes at line 234 and 273 actually exists. The sticky postsolve is a superset of the default's, so the doc's §Execution Sequence postsolve bullet is also incomplete for this realization.
- **code_evidence**: `modules/70_livestock/fbask_jan16_sticky/postsolve.gms:13`; `modules/70_livestock/fbask_jan16_sticky/presolve.gms:83-95` (the two branches the doc did quote); `modules/70_livestock/fbask_jan16_sticky/preloop.gms:94` (`p70_initial_1995_prod` from `f70_hist_prod_livst("y1995",i,kli,"dm")`)
- **why_it_matters**: The doc's stated rationale for the sticky realization is path dependency — "existing capital stocks carry over between timesteps" (line 234). The mechanism it documents cannot carry anything over; it only depreciates. A reader tracing why sticky suppresses abrupt regional livestock shifts would find the documented equations insufficient to produce the effect and either mistrust the realization or reinvent the missing line. Non-default realization, which caps the blast radius.
- **confidence**: high

### F7: `preloop.gms:26` is rendered as `max(...)` in a fenced code block; the code is a zero-only `$`-conditional

- **severity**: Major
- **self_named_class**: `paraphrase-idiom over-application` — the doc has a consistent and *correct* house style of rendering GAMS `x$(x < y) = y` as `max(x, y)`. It applied that same rendering to `x$(x = 0) = c`, which is not a max. The defect is a style rule escaping its domain of validity.
- **fits_existing_taxonomy**: unsure. "Fabricated formula presented as the code's implementation" is a Critical trigger and technically fires — the block is fenced, cited to a line, and is not what that line says. But the generative mechanism is not fabrication; it is a valid transform applied one case too far, and the semantic delta is confined to a near-degenerate interval. I record Major under the "pick the LOWER tier when between two" rule and flag the Critical reading explicitly.
- **doc_location**: `modules/module_70.md:1078-1082`
- **doc_says**: "**Livestock Productivity** (`preloop.gms:26`): `i70_livestock_productivity(t,i,sys) = max(i70_livestock_productivity(t,i,sys), 0.02)` — Default minimum productivity (0.02 ton FM/animal/yr) prevents division by zero in cattle stock proxies"
- **code_says**: `i70_livestock_productivity(t_all,i,sys)$(i70_livestock_productivity(t_all,i,sys)=0) = 0.02;` — this substitutes 0.02 **only where the value is exactly zero**. It is not a floor. A productivity of 0.005 survives untouched under the code and is raised to 0.02 under the doc's version. The code comment on the preceding line ("set default livestock productivity to avoid division of zero") confirms the narrow intent. Note the doc's *other* use of this idiom is legitimate: at line 568-569 it renders `presolve.gms:41-42` (`p70_cattle_stock_proxy(t,i)$(... < 0.2*...) = 0.2*...`) as `max(...)`, which is exactly equivalent.
- **code_evidence**: `modules/70_livestock/fbask_jan16/preloop.gms:25-26`; contrast `modules/70_livestock/fbask_jan16/presolve.gms:41-42` (where the same doc idiom is correct)
- **why_it_matters**: The doc frames this as a guard against division-by-zero in the cattle-stock proxies at `presolve.gms:32-36`. Under the code that guard is exact-zero-only, so a very small but nonzero `i70_livestock_productivity` still produces an enormous `p70_cattle_stock_proxy` — the 20%-of-1995 bound at `presolve.gms:41-42` is a *lower* bound and does not catch the blow-up. A reader debugging an implausible cattle-stock proxy would consult the doc, believe a 0.02 floor is in force, and eliminate the actual cause.
- **confidence**: high

### F8: Fabricated interface-variable counts (4 outputs / 6 inputs) contradicting the doc's own enumerations

- **severity**: Major
- **self_named_class**: `self-contradicting tally` — a summary count that disagrees not only with the code but with the enumerated list printed earlier in the same document. Diagnostic value: no reading of either source produces the stated number, so the count was not derived from anything.
- **fits_existing_taxonomy**: yes — "fabricated count for a set/parameter/realization list" covers it directly.
- **doc_location**: `modules/module_70.md:1252-1253`
- **doc_says**: "- 4 interface variables (outputs) / - 6 interface variables (inputs from other modules)"
- **code_says**: Outputs: the doc's own §Interface Variables → Outputs enumerates **6 numbered items** covering **7 identifiers** (`vm_dem_feed`, `vm_feed_intake`, `vm_feed_balanceflow`, `vm_cost_prod_livst`, `vm_cost_prod_fish`, `pm_past_mngmnt_factor`, `im_slaughter_feed_share`) — all 7 confirmed in `declarations.gms` lines 11, 18, 17, 12, 13, 41, 34 respectively. Restricting to `vm_` gives 5. No reading yields 4. Inputs: the doc's own §Inputs enumerates **7 numbered items** covering **8 identifiers** (`vm_prod_reg`, `pm_factor_cost_shares`, `pm_hourly_costs`, `pm_productivity_gain_from_wages`, `pm_kcal_pc_initial`, `im_pop`, `fm_nutrition_attributes`, `fm_attributes`) — all confirmed read in `equations.gms` / `presolve.gms` / `preloop.gms`. No reading yields 6.
- **code_evidence**: `modules/70_livestock/fbask_jan16/declarations.gms:10-19,34,41`; `modules/70_livestock/fbask_jan16/equations.gms:59-62`; `modules/70_livestock/fbask_jan16/presolve.gms:32-47`; `modules/70_livestock/fbask_jan16/preloop.gms:63-76`
- **why_it_matters**: §Summary Statistics reads as a verified fingerprint of the module and is the kind of line a reader quotes without re-deriving. Both numbers undercount, in a doc whose real defects (F1, F3) are *also* undercounted interfaces — so the tally actively corroborates the blind spot rather than exposing it. Note the neighbouring counts in the same block are correct and non-trivially so: 7 equations ✓, 5 systems ✓, 10 feed scenarios ✓, 17 SCP scenarios ✓ (I counted `fadeoutscen70` members: exactly 17), 2 regression modes ✓.
- **confidence**: high

### F9: "Provides to: 7 modules" is numerically right for the wrong reason; the enumerated downstream list has 6 and omits the two real gaps

- **severity**: Minor
- **self_named_class**: `right-number-wrong-set` — a count that matches ground truth by coincidence while the accompanying enumeration does not. Worth naming because a count-vs-code check passes here and a count-vs-enumeration check fails; only the latter finds it.
- **fits_existing_taxonomy**: no — a taxonomy keyed on "fabricated count" scores this as clean, because the number is correct.
- **doc_location**: `modules/module_70.md:1314`
- **doc_says**: "**Provides to**: 7 modules (production, costs, emissions, manure)"
- **code_says**: the true set of direct consumers of M70 outputs is exactly 7 — M11 (`vm_cost_prod_livst`, `vm_cost_prod_fish`), M14 (`pm_past_mngmnt_factor`), M16 (`vm_dem_feed`), M36 (`vm_cost_prod_livst`), M53 (`vm_feed_intake`), M55 (`vm_feed_intake`, `im_slaughter_feed_share`), M71 (`vm_feed_balanceflow`). But the doc's §Downstream Dependencies (1139-1145) enumerates only 6 entries — 11, 14, 16, 31 (itself flagged INDIRECT, so only 5 direct), 53, 55 — missing M36 (F3) and M71 (F1) while counting M31, which is not a direct consumer.
- **code_evidence**: `modules/11_costs/default/equations.gms:18-19`; `modules/14_yields/managementcalib_aug19/equations.gms:38` and `nl_fix.gms:11`; `modules/16_demand/sector_may15/equations.gms:22,34,43,53,63`; `modules/36_employment/exo_may22/equations.gms:24`; `modules/53_methane/ipcc2006_aug22/equations.gms:23,25,27`; `modules/55_awms/ipcc2006_aug16/equations.gms:28-31,39,46,54,71`; `modules/71_disagg_lvst/foragebased_jul23/equations.gms:36,46`
- **why_it_matters**: Low direct harm — but this is the one place the doc would have caught F1 and F3 itself. The "7" and the 6-item list disagree by one net entry and by two identities; nobody reconciled them.
- **confidence**: high

### F10: `Lines of Code: ~450` understates the realization by ~39%

- **severity**: Minor
- **self_named_class**: `unrefreshed magnitude` — a soft quantity that drifts with the code and that nothing re-derives.
- **fits_existing_taxonomy**: yes — ordinary stale count; no reader acts on it.
- **doc_location**: `modules/module_70.md:7`, `1258`, `1296`
- **doc_says**: "**Lines of Code**: ~450 (main realization)" (stated 3×)
- **code_says**: `wc -l` over `modules/70_livestock/fbask_jan16/*.gms` = **625** (declarations 69, equations 70, input 113, postsolve 65, preloop 90, presolve 70, realization 91, scaling 11, sets 46). The sticky realization totals 706.
- **code_evidence**: `modules/70_livestock/fbask_jan16/*.gms` (all 9 files read this session)
- **why_it_matters**: Negligible operationally. Recorded because it is a cheap, mechanical staleness signal that three separate footers repeat.
- **confidence**: high

### F11: Historical-override year range stated as "1990-t_past_last"; the code excludes 1990

- **severity**: Minor
- **self_named_class**: `inclusive/exclusive boundary slip`
- **fits_existing_taxonomy**: yes — right concept, wrong boundary.
- **doc_location**: `modules/module_70.md:530`
- **doc_says**: "**Historical Override** (`preloop.gms:90`): If regional regression enabled, use actual historical values instead of regression for years 1990-t_past_last"
- **code_says**: the guard is `$(m_year(t_all) <= sum(t_past$(ord(t_past) eq card(t_past)), m_year(t_past)) and m_year(t_all) > 1990)` — strictly **greater than** 1990, so a `y1990` timestep keeps the regression value and is not overridden. Range is (1990, t_past_last], not [1990, t_past_last].
- **code_evidence**: `modules/70_livestock/fbask_jan16/preloop.gms:90`
- **why_it_matters**: Only bites a reader inspecting 1990 specifically, under the non-default `c70_fac_req_regr = "reg"`. Small, but it is a stated numeric boundary that the code contradicts.
- **confidence**: high

### F12: Regional-intercept formula block drops the `i70_` prefix and the `sys_to_kli` mapping sum

- **severity**: Minor
- **self_named_class**: `pseudocode leakage into a cited code block` — the block carries a `preloop.gms:83` citation and code fencing but uses invented tokens (`t_past_last`, bare `livestock_productivity`).
- **fits_existing_taxonomy**: partially — "wrong variable prefix" is listed as Major, but here the surrounding block is transparently a paraphrase (`t_past_last` is not a MAgPIE set and no reader would paste it), which caps the harm.
- **doc_location**: `modules/module_70.md:519-525`
- **doc_says**: "`i70_cost_regr(i,kli,"cost_regr_a") = (f70_hist_factor_costs_livst(t_past_last,i,kli) / f70_hist_prod_livst(t_past_last,i,kli,"dm")) - f70_cost_regr(kli,"cost_regr_b") * livestock_productivity(t_past_last,i,sys)`"
- **code_says**: `$if "%c70_fac_req_regr%" == "reg" i70_cost_regr(i,kli,"cost_regr_a") = sum(t_past$(ord(t_past) eq card(t_past)), (f70_hist_factor_costs_livst(t_past,i,kli) / f70_hist_prod_livst(t_past,i,kli,"dm")) - f70_cost_regr(kli,"cost_regr_b") * sum(sys_to_kli(sys,kli), i70_livestock_productivity(t_past,i,sys)));` — the real identifier is `i70_livestock_productivity`, and the `sys` index is not free: it is bound by `sum(sys_to_kli(sys,kli), ...)`. The doc's rendering leaves `sys` dangling, which as written would be an uncontrolled set.
- **code_evidence**: `modules/70_livestock/fbask_jan16/preloop.gms:83`; contrast `preloop.gms:88`, which the doc renders correctly *with* both the `i70_` prefix and the `sum(sys_to_kli(...))` at doc line 156-159
- **why_it_matters**: Minor — the doc gets the same construct right 60 lines earlier, so a careful reader self-corrects. Recorded because a bare `livestock_productivity` is an identifier that does not exist anywhere in MAgPIE.
- **confidence**: high

### F13: `pm_past_mngmnt_factor`'s second consumer site (`nl_fix.gms:11`) is undocumented

- **severity**: Minor
- **self_named_class**: `equations-only consumer sweep` — the doc's consumer discovery appears to cover `equations.gms` and miss the other phase files (`nl_fix.gms`, `presolve.gms`, `postsolve.gms`) where interface variables are also read.
- **fits_existing_taxonomy**: no. It is the same generative blind spot as F1/F3 but at a sub-module granularity: not "which module reads this" but "which *phase file* reads this". Worth separating because the fix differs — F1/F3 need a wider module sweep, F13 needs a wider file-glob.
- **doc_location**: `modules/module_70.md:720`
- **doc_says**: "**To Module 14 (Yields)**: Scales pasture yields to account for exogenous intensification (`presolve.gms:23-26`; consumed in `modules/14_yields/managementcalib_aug19/equations.gms:38`)"
- **code_says**: the cited site is exact — `equations.gms:38` is `* sum(cell(i2,j2),pm_past_mngmnt_factor(ct,i2)))` inside `q14_yield_past`. But M14 reads it a second time at `nl_fix.gms:11`, in the `vm_yld.fx(j,"pasture",w)` fixing statement used to linearize the model. Both are in the default realization `managementcalib_aug19` (`config/default.cfg:354`).
- **code_evidence**: `modules/14_yields/managementcalib_aug19/equations.gms:35-39`; `modules/14_yields/managementcalib_aug19/nl_fix.gms:11`; `config/default.cfg:354`
- **why_it_matters**: Small. But the `nl_fix` path is what runs when the model is fixed to linear behaviour, so anyone changing `pm_past_mngmnt_factor`'s domain would break an LP-mode run while the NLP-mode run the doc points at looks fine. This is exactly the `.fx`/`.l`-form read that a paren-only consumer grep misses.
- **confidence**: high

### F14: §Verification footer asserts "Zero errors detected" and "Status: Fully Verified"

- **severity**: Informational
- **self_named_class**: `self-certification` — an unfalsifiable clean-bill claim embedded in the artifact it certifies.
- **fits_existing_taxonomy**: no; it is not a code claim at all, which is why I nearly excluded it. Recorded because it is load-bearing on reader trust and this audit falsifies it.
- **doc_location**: `modules/module_70.md:3`, `1293`, `1339`
- **doc_says**: line 1293: "**Verification**: All 7 equations verified against source code. All formulas, dimensions, and parameter names confirmed exact. All interface variables cross-referenced with Phase 2 dependency documentation. Zero errors detected." Line 3: "**Status**: Fully Verified". Line 1339: "**Last Verified**: 2026-03-06 (sticky realization added, 8/8 equations documented)".
- **code_says**: the equation-level half of the claim holds up remarkably well — all 7 default formulas and both sticky formulas are exact, and 33 of 34 file:line citations resolve. The *interface* half does not: F1, F3, F4, F9 and F8 are all interface/dependency defects, which is precisely what "All interface variables cross-referenced" asserts was done. Separately "8/8 equations documented" cannot be squared with 7 default + 8 sticky equations under any reading.
- **why_it_matters**: The footer's confidence is inversely distributed relative to the doc's actual reliability: it is loudest about the dimension (interfaces) that is weakest. A reader triaging what to re-check would deprioritize exactly the section that needed it.
- **confidence**: high

---

## Out-of-taxonomy / unclassifiable observations

Recorded individually. None of these is scored as a defect above; several are code observations rather than doc observations.

**O1 — `fadeoutscen70` is a dead set, and the doc cites it as ground truth.** `sets.gms:41-45` declares `fadeoutscen70` with 17 members in both realizations. The identifier appears nowhere else in the repository — no parameter is indexed by it, no `$if` compares against it. The doc (line 408-412, 794) cites `sets.gms:41-45` as the option list for `c70_cereal_scp_scen`. So the doc's option list is accurate as a *transcription* and meaningless as a *specification*: it enumerates the members of an unused set as the legal values of an unexpanded switch (F2). The doc also never names the set. I could not decide whether this is a doc defect or faithful documentation of a code defect — the doc reports what is written; what is written does nothing. It is the cleanest example in this module of a claim that is simultaneously true and useless.

**O2 — CONFIRMED MAgPIE CODE BUG (not a doc bug): `cfg$gms$s70_feed_subst_functional_form` is an orphan config key; the sigmoid SCP fader is unreachable through the config surface.**

This started as an uncertain lead and I chased it down. It is now settled.

- **The orphan pair.** `config/default.cfg:2197` declares `cfg$gms$s70_feed_subst_functional_form <- 1`. The GAMS scalar is `s70_subst_functional_form` (`fbask_jan16/input.gms:29`, `fbask_jan16_sticky/input.gms:29`) — no `_feed_`. A full-tree scan shows the two names never co-occur: the cfg-style name appears **only** in `config/default.cfg` and in run `config.yml` files; the GAMS name appears **only** in the `.gms` sources, `full.gms`, and `fulldata.gdx`. Every other M70 cfg key matches its scalar exactly (all 11 verified).
- **Why nothing catches it.** `scripts/start_functions.R:243` calls `gms::check_config(cfg, ...)` — but I read its source: it validates the user's cfg against `config/default.cfg` as the *reference file*, not against the GAMS sources. A key that is wrong *in default.cfg itself* is therefore unfalsifiable by that check. The binding at `scripts/start_functions.R:346`, `lucode2::manipulateConfig(file.path(ll, "input.gms"), cfg$gms)`, builds three pure regex substitutions keyed on the setting name (`$setglobal <name>`, `scalar[s] <name> .../value/`, `<name> = value`) and hands them to `manipulateFile`. There is no existence check and no warning: a name that matches nothing is a **silent no-op**.
- **Empirical confirmation against a real solved run.** `output/BAU_TCendo/config.yml:769` carries `s70_feed_subst_functional_form: 1.0`. The model actually solved from that config, `output/BAU_TCendo/full.gms`, contains `s70_subst_functional_form` (declaration + both `if`/`elseif` branches) and does **not** contain the string `s70_feed_subst_functional_form` at all. The cfg key traversed the whole config pipeline and was dropped at the GAMS boundary without a word. By contrast `s70_cereal_scp_substitution` (`config.yml:767`) binds correctly — the name matches.
- **Consequence**: setting `cfg$gms$s70_feed_subst_functional_form <- 2` in a config or scenario CSV does nothing. `s70_subst_functional_form` keeps its `input.gms` literal of 1, so `preloop.gms:40-50` always takes the `m_linear_time_interpol` branch. The sigmoid branch at `preloop.gms:45-48` is dead code via the sanctioned `Rscript start.R` route; only a direct hand-edit of `input.gms` reaches it.
- **The doc is not at fault** — it names the GAMS scalar correctly at lines 419 and 808-811 and describes both branches accurately. Scored as an observation, not a finding, for exactly this reason. But it compounds F2: **both** SCP-scenario control surfaces are broken — `c70_*_scp_scen` is dead in GAMS, and `s70_feed_subst_functional_form` is dead in cfg. Of the doc's four documented SCP knobs, only the substitution shares and the start/target years actually work.
- **Recommend surfacing upstream.** This is a model bug worth a MAgPIE issue independent of the documentation round.

**O2b — the same class may be repo-wide.** The generative pattern (a cfg key silently not matching any GAMS identifier, caught by neither `check_config` nor `manipulateConfig`) is not M70-specific — it is a property of the binding machinery. A trivial checker (for each `cfg$gms$X` in default.cfg, assert `X` appears in some `.gms`) would find every instance in the model in one pass. I did not run it beyond M70; scope was this module. Flagging as a lead, not a claim.

**O3 — `kall` glossed as "All feed items".** Doc line 44: "`kall`: All feed items (cereals, fodder, pasture, residues, SCP, etc.)". `kall` is the set of all products; it is being *used* here as a feed-item index because `im_feed_baskets` is indexed over it. The gloss describes the role, not the set. Contextually harmless and arguably clearer for the reader; not scored. Noted only because the doc's other set glosses (`kap`, `kli_rum`, `kli_rd`) are exact set definitions, so this one is inconsistent in kind. (Verified `kap` = {livst_rum, livst_pig, livst_chick, livst_egg, livst_milk, fish}, `kli_rum` = `kli_rd` = {livst_rum, livst_milk}, `kforage` = {pasture, foddr}, `factors` = {labor, capital} from the expanded `output/BAU_TCendo/full.gms` — see Coverage honesty.)

**O4 — §Inputs item 1 header contradicts its own sub-bullet.** Doc line 730: "**1. Regional Production** (from Module 16 via Module 17)". The sub-bullet at 734 says "**From Module 17 (Production)**: Regional production target drives feed demand" — which is right. `vm_prod_reg` is M17's. The header's "from Module 16 via Module 17" reverses the routing (M70's `vm_dem_feed` goes *to* M16; `vm_prod_reg` comes *from* M17). Two lines apart, contradictory. Too minor and too self-correcting to score, but it is the same directional confusion as F4 appearing in a second, independent place — which makes me think the doc's directional errors are not one stale block but a recurring reading error.

**O5 — `presolve.gms:9` is labeled "Non-Pasture Feed Items" but the quoted statement is full-domain.** Doc line 374-378 heads the section "**Non-Pasture Feed Items** (`presolve.gms:9`)" and quotes `vm_feed_balanceflow.fx(i,kap,kall) = fm_feed_balanceflow(t,i,kap,kall)`. The statement fixes the *entire* `(i,kap,kall)` domain including pasture; lines 10-11 then relax only `(i,kli_rum,"pasture")`. So pasture balance flows for non-ruminants stay fixed, and the doc's own next subsection (380-385) gets the relaxation right. Net behavior as documented is correct; the heading mis-scopes the quoted line. I could not call this a defect — the section as a whole conveys the right thing — but a reader who reads only the heading and the code block would think line 9 has a `kall`-minus-pasture domain, which it does not.

**O6 — the doc never states that `p70_endo_scavenging_flag` persists.** Related to F5 but separable. The flag is a parameter written once (in the last historical timestep) and never reset; every future timestep reads a value computed at the historical boundary. The doc describes the computation and the branch it gates but never says the value is frozen. A reader could reasonably assume it is recomputed each timestep from the current pasture demand — which would make scavenging responsive to the solution, when it is in fact fixed at the boundary. Not scored because the doc makes no contrary claim; it is silence, not error. But it is the single most load-bearing unstated fact in the scavenging mechanism.

**O7 — the doc's "asymmetric adjustment costs" reading of sticky is plausible but unverified by me.** Doc line 273: "When production decreases, existing capital exceeds needs, so no new investment is required (the inequality allows `v70_investment` to be zero). This creates asymmetric adjustment costs — expansion is costly but contraction is 'free' (sunk capital)." The `=g=` and the positive-variable declaration of `v70_investment` (`fbask_jan16_sticky/declarations.gms:14`) are consistent with this. But given F6 (the postsolve carry-forward is real), whether contraction is truly free depends on the interaction of accumulation and depreciation across timesteps, which I did not trace through a run. Recording as unverified rather than dropping it: the claim may well be right, I just can't certify it from statics.

**O8 — M31's "INDIRECT" annotation is unusually well done and I want that recorded.** Doc lines 692 and 1143 and 1238 all carry the same careful hedge: `vm_dem_feed` reaches M31 only transitively via M16/M21, and M31 reads `vm_prod`/`vm_land`/`vm_yld`, not `vm_dem_feed`. I verified this: the only external reader of `vm_dem_feed` is M16 `sector_may15` (5 sites), and `q31_prod` at `modules/31_past/endo_jun13/equations.gms:16-18` reads `vm_land` and `vm_yld` only. The doc's citation `31_past/endo_jun13/equations.gms:16-18, q31_prod` is exact. This is a one-hop-vs-transitive distinction correctly drawn and correctly cited in three places — which sharpens the puzzle of F1/F3, since the same doc that carefully verified a *non*-edge failed to grep for two real ones. My read: the doc's consumer analysis was hypothesis-driven (checking edges it suspected) rather than sweep-driven (enumerating readers of each declared identifier). That would explain the exact pattern of what it got right and wrong, and it is the observation I'd most want carried into the next round.

---

## Coverage honesty

**Read in full this session** (ground truth basis): all 9 `fbask_jan16/*.gms`, all 10 `fbask_jan16_sticky/*.gms`, `70_livestock/module.gms`, `fbask_jan16/not_used.txt`, `fbask_jan16/input/f70_capit_liv_regr.csv`, `config/default.cfg:2160-2180` plus targeted extractions, the cited lines of `modules/{11,14,16,31,36,53,55,71}` consumer sites, and (for O2) `scripts/start_functions.R:240-350` plus the installed sources of `gms::check_config` and `lucode2::manipulateConfig`.

**Provenance check on the working tree**: `git status --porcelain modules/70_livestock config/default.cfg` is **empty** and `HEAD` = `0d7ebeb90`, the exact commit named in the audit brief. This matters specifically because running MAgPIE rewrites `input.gms` scalar literals in place (that is what `manipulateConfig` does — see O2), so a dirty tree would mean the `input.gms` defaults I read were a prior run's artifact rather than source. They are not. All default-value findings rest on committed source at the target commit.

**What I did NOT check:**

- **`Centrality: HIGH (Rank #6)` and `Provides to`/`Depends on` as claims about `core_docs/Module_Dependencies.md`.** I audited them against *code* (F4, F9). I did not open Module_Dependencies.md, so I cannot say whether module_70.md faithfully reproduces a wrong upstream doc or diverges from a right one. The prompt states degree centrality 25; the doc says Rank #6. Both may be true (rank ≠ degree); unresolved and excluded from the denominator.
- **`Risk Level: MEDIUM-HIGH`** — a judgment, not a code claim.
- **Input data file contents and dimensions.** I verified every `f70_*` declaration's name, dimension list, and `input.gms` line citation against `input.gms`, and I read `f70_capit_liv_regr.csv` in full (confirming `cost_regr_b = 0` for livst_chick/livst_egg/livst_pig/fish and > 0 for livst_milk = 49.2, livst_rum = 30930.1 — the doc's ruminant/monogastric slope claim at lines 502-504 is correct). I did **not** parse the `.cs3`/`.cs4` files; claims about their contents (e.g. that `f70_feed_baskets` actually carries all 10 `feed_scen70` scenarios) are unverified.
- **Core set definitions came from an expanded run file, not from source.** `kap`, `kli`, `kli_rum`, `kli_rd`, `kforage`, `factors` are not defined in any tracked `.gms` — they arrive via the un-extracted `input.tgz`. I resolved them from `output/BAU_TCendo/full.gms`, a previously-expanded model file in this working tree. That file is from an unknown config at an unknown commit. Set membership is stable enough in MAgPIE that I am confident, but this is **not** develop@0d7ebeb90 ground truth and I flag it as such. Everything downstream of it (the `kap` = kli+fish check, `kli_rum`/`kli_rd` membership, `factors` = {labor, capital}) inherits that caveat.
- ~~The R config→GAMS binding machinery.~~ **Resolved during the audit** — I read `scripts/start_functions.R`, `gms::check_config`, and `lucode2::manipulateConfig`, and confirmed O2 empirically against `output/BAU_TCendo/{config.yml,full.gms}`. O2 is no longer uncertain. The remaining gap is O2b: I did not sweep the *other 45 modules* for the same orphan-key class.
- **`modules/module_70_notes.md`.** It exists. The audit target was `module_70.md`; I did not read the notes file, so a defect above may already be documented as a known caveat there.
- **The magpie4 reporting layer.** No report.mif/IAMC claims are made in module_70.md, so nothing to check — but I did not confirm that absence is correct (i.e. whether M70 outputs *should* have a documented reporting path).
- **No model was run.** Every finding is static analysis. F5 (flag timing) and F6 (capital carry-forward) are the two most worth confirming dynamically — both are claims about *when* code executes, and both would be settled definitively by one GDX.
- **Bibliography.** I verified that the citation keys `@weindl_livestock_2017`, `@weindl_livestock_2017-1`, `@wirsenius_human_2000`, `@narayanan_gtap7_2008` appear at the cited `realization.gms` / `equations.gms` lines. I did **not** verify the expanded references at doc lines 993-1004 (journal, volume, page numbers) against any bibliography file.

**Negative-claim discipline**: every "X is absent" assertion above (F2's inert switches, F4's no-M14-identifier, O1's dead set) was established by a repo-wide search *plus* a positive control on a token known to be present — `%c70_feed_scen%` for F2/O1 (found at `preloop.gms:19-21` and `config/default.cfg:2170`, proving the search reaches both GAMS and cfg), and full reads of all 9 `fbask_jan16` files for F4. I note that `rg -c 'kli' core/sets.gms` returned empty during this session and I initially misread it as a tool failure; a Python `.count()` confirmed the file genuinely contains no `kli`, which is what led me to the `full.gms` route above.
