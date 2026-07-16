# M11 adversarial audit (R58)

**Target:** `modules/module_11.md` vs `../modules/11_costs/` (branch `develop` @ 0d7ebeb90)
**Date:** 2026-07-17
**Method:** all six `11_costs` `.gms` files read in full this session; every one of the 32 `q11_cost_reg`
terms traced to its declaring module and default realization; sets, units and declaration blocks
re-derived from source. `scripts/check_*.py` was NOT read, imported, or run (per round constraint).

## Denominator

```
claims_evaluated: 241
```

Breakdown of what was counted:

| Section | Claims | Notes |
|---|---|---|
| Header/metadata | 5 | realization, LOC 149, LOC 170, equation count 2, verification date |
| §1 Overview | 10 | citations, objective role, aggregator role, counts |
| §2 Equations | 10 | both formulas verbatim, units, `i2` semantics, citations |
| §3 Cost catalog | 110 | 32 × (variable name exists / source module / `equations.gms:N` citation) = 96, plus 14 extra specific claims (set `factors` at `38.../sets.gms:15-16`, `land` members, `kres` members, `k` members, M54-not-M50, PR#866 split, feasibility fixed in `exo`, feasibility fixed in `bilateral22`, `vm_costs_additional_mon` line/dim/default-realization/semantics, maccs `factors` at `57.../equations.gms:36,46`, cropland mechanism, urban mechanism) |
| §4 Interface vars | 6 | declaration lines, counts, naming convention, unit invariant, reward exception |
| §5 Scaling | 7 | 3 code lines verbatim, citation, 3 magnitude glosses |
| §6 Configuration | 3 | no input.gms, no scalars, one realization |
| §7 Dependencies | 20 | "27 modules" + 18 curated attributions + no-circular claim |
| §8 What it does NOT do | 5 | |
| §9 Code patterns | 4 | |
| §10 Testing | 3 | equation-count grep, non-negativity rule, sum check |
| §13 Relationships | 4 | |
| §14 Evolution | 2 | |
| §15 Numerical properties | 4 | |
| §17.1 Conservation laws | 1 | grouped (spot-check only) |
| §17.2 Centrality/table | 29 | rank, connections, provides-to, depends-on, hub type, 31+1, 46 total, non-contributor count + 18 members, pm_interest claim, 2 provides claims |
| §17.3 Circular deps | 3 | |
| §17.4 Mod safety | 8 | 6 GDX symbol names + non-negativity test + centrality restatement |
| §16 Summary | 2 | |
| Limitations block | 5 | |
| **Total** | **241** | |

**Honesty note on the denominator.** 241 is a mechanical count of individually-checkable
assertions. Two blocks inflate it relative to intuition: the §3 catalog contributes 96 via a
systematic 32 × 3 sweep, and §17.2's non-contributor list contributes 18 membership claims. If you
prefer "distinct hand-reasoned assertions", the figure is nearer **~130**. I report 241 because each
of the 241 was in fact mechanically verified against source; I flag the composition so the number
is not read as more artisanal than it is.

**Excluded from the denominator** (not counted, not checked — see Coverage honesty):
prose in §11 (Common Issues), §12 (Key Insights), §14.2 (hypothetical future realizations),
the 15 fabricated names preserved in the R3 footnote, and all unfalsifiable-without-a-GDX
magnitude/share claims in §15.2.

---

## Findings

### F1: The doc reifies "the GAMS solver" as M11's only consumer, erasing the real M11 → M80 module edge

- **severity:** Critical
- **self_named_class:** `abstraction-substituted-for-module` (solver reification)
- **fits_existing_taxonomy:** **NO.** This is not a wrong name, a wrong count, or a wrong
  attribution. It is a *category* error one level up: the doc names a non-module entity ("the GAMS
  solver") as the endpoint of a data-flow edge, and by doing so silently drops a real,
  realization-switchable MAgPIE module from the dependency graph. Every existing class I am aware of
  presupposes that both endpoints of the claimed edge are modules; this defect is invisible to any
  check built on that presupposition, because the doc never states a *wrong* module — it states no
  module at all. The doc is not lying about M80; it has no slot in which M80 could appear.
- **doc_location:** `modules/module_11.md:1091`, `:1144`, `:944`, `:1130`
- **doc_says:**
  - `:1091` — "**Hub Type**: **Pure Sink Hub** (receives from many, provides only to solver)"
  - `:1144` — "**No variables provided back**: Other modules do NOT depend on Module 11 variables"
  - `:944` — "it aggregates costs but doesn't provide variables to other modules (except the solver)"
  - `:1130` — module 80 is listed among modules that "either provide non-cost outputs (yields, areas, biophysical accounting) or feed costs in indirectly"
- **code_says:** Module **80_optimization** is an ordinary MAgPIE module with four realizations
  (`nlp_apr17` [default], `lp_nlp_apr17`, `nlp_ipopt`, `nlp_par`) and it **consumes `vm_cost_glo`**:
  `solve magpie USING nlp MINIMIZING vm_cost_glo;`. So "other modules do NOT depend on Module 11
  variables" is flatly false — M80 is precisely such a module. M80 also does *not* "provide non-cost
  outputs" nor "feed costs in indirectly"; it is the sole consumer of M11's output, which §17.2's
  own non-contributor rationale has no category for.
- **code_evidence:**
  - `modules/80_optimization/nlp_apr17/solve.gms:34` (default realization)
  - `modules/80_optimization/nlp_ipopt/solve.gms:62`; `modules/80_optimization/nlp_par/solve.gms:41`;
    `modules/80_optimization/lp_nlp_apr17/solve.gms:65`
  - `config/default.cfg:2300` — `cfg$gms$optimization <- "nlp_apr17"`
- **why_it_matters:** A reader assessing the blast radius of an M11 change (exactly what §17.4 is
  for) concludes "nothing downstream reads my variables — only the abstract solver does." They then
  miss that M80 reads `vm_cost_glo` in four different realizations with four different control flows,
  one of which also *writes* to it (see F2). The "Pure Sink Hub" label actively discourages the grep
  that would find M80. Note the doc's own "Total Connections: 28 (provides to 1 [GAMS solver],
  depends on 27 modules)" at `:1090` is numerically right *by accident*: the "1" is a real module,
  but the doc thinks it is not one.
- **confidence:** high

---

### F2: "One-way data flow" / "no feedback loops" is false — module 80 writes a bound onto `vm_cost_glo`

- **severity:** Major
- **self_named_class:** `dot-form write-back invisible to paren-form reasoning`
- **fits_existing_taxonomy:** unsure. The *mechanism* of the miss (grepping `vm_cost_glo(` and never
  `vm_cost_glo.`) is anticipated by existing grep-discipline guidance, so the failure mode is named.
  But the resulting *claim class* — "a downstream module writes a solution-level bound back onto the
  hub's own variable, creating a genuine two-way edge the doc calls impossible" — is not something I
  can map onto an existing category. I record it as its own class.
- **doc_location:** `modules/module_11.md:1142-1144`
- **doc_says:** "**No feedback loops**: Module 11 is a **terminal sink** (receives costs, provides
  only to solver) / **One-way data flow**: All cost modules → Module 11 → Solver objective /
  **No variables provided back**"
- **code_says:** In `80_optimization/lp_nlp_apr17`, M80 sets `vm_cost_glo.up = vm_cost_glo.l`, re-solves
  minimising `vm_landdiff`, then releases the bound with `vm_cost_glo.up = Inf`. That is another
  module *writing* an attribute of an M11-declared variable — a real edge back into M11's symbol,
  not a "one-way" flow. It happens twice in that realization.
- **code_evidence:** `modules/80_optimization/lp_nlp_apr17/solve.gms:75`, `:78`, `:195`, `:198`
- **why_it_matters:** Two harms. (1) Anyone changing `vm_cost_glo`'s bounds, scaling, or sign domain
  in M11 will not know that `lp_nlp_apr17` manipulates `.up` and depends on `Inf` being the correct
  release value. (2) The doc's blanket "no feedback loops" would let a reader conclude the flat-optimum
  land-smoothing second solve cannot exist — when it does, and it works precisely by feeding M11's
  own solution value back as an M11 bound.
  Severity is Major rather than Critical because `lp_nlp_apr17` is **not** the default
  (`config/default.cfg:2300` = `nlp_apr17`, which only reads `.l`); the universal claim is still false.
- **confidence:** high

---

### F3: §7.1 attributes urban costs to Module 10 (Land)

- **severity:** Critical
- **self_named_class:** `curated-summary attribution drift`
- **fits_existing_taxonomy:** partly — "wrong module attribution for a cost variable" is a named
  Critical trigger. What is *not* captured by that name is the structural signature: the machine-checkable
  catalog (§3) and table (§17.2) are **correct**, and the wrongness lives exclusively in the
  hand-written, prose-formatted "key modules" summary that no name-checking validator parses because
  it contains no variable identifiers at all. The defect survives precisely by being written in prose.
- **doc_location:** `modules/module_11.md:599`
- **doc_says:** "- Module 10 (Land): Land transition and urban costs"
- **code_says:** M10 (`landmatrix_dec18`) declares only `vm_cost_land_transition(j)`. `vm_cost_urban(j)`
  is declared by **Module 34 (urban)**. The doc's own §3.2 (`:260`) and §17.2 table (`:1107`) both
  correctly say M34 — so the doc contradicts itself.
- **code_evidence:** `modules/10_land/landmatrix_dec18/declarations.gms:22` (`vm_cost_land_transition(j)`,
  positive variables); `modules/34_urban/exo_nov21/declarations.gms:13` (`vm_cost_urban(j)`);
  `modules/11_costs/default/equations.gms:41`, `:45`
- **why_it_matters:** §7.1 is the section a reader consults for "which module do I talk to about cost X".
  Sending someone to M10 to change urban costs wastes the session and, worse, invites an edit to
  `landmatrix_dec18` — a module in the land balance — on the belief it owns urban costs.
- **confidence:** high

---

### F4: §7.1 attributes cropland costs to Module 30

- **severity:** Critical
- **self_named_class:** `curated-summary attribution drift` (same class as F3)
- **fits_existing_taxonomy:** partly (see F3)
- **doc_location:** `modules/module_11.md:594`
- **doc_says:** "- Module 30 (Crop): Cropland and rotation costs"
- **code_says:** M30 (`30_croparea`, default `simple_apr24`) declares **only** `vm_rotation_penalty(i)`.
  `vm_cost_cropland(j)` is declared by **Module 29 (cropland)**. Additionally M30's name is
  `30_croparea`, not "Crop" — the doc's own §3.4 (`:308`) and §17.2 (`:1104`) say "Croparea" and
  correctly separate M29 from M30.
- **code_evidence:** `modules/30_croparea/simple_apr24/declarations.gms:19`;
  `modules/29_cropland/detail_apr24/declarations.gms:38`; `config/default.cfg:811,912`
- **why_it_matters:** Same as F3. M29 and M30 are adjacent, similarly-named, and both feed M11 —
  which is exactly the condition under which a reader will not notice the swap.
- **confidence:** high

---

### F5: PR#866 note claims `vm_cost_trade_feasibility` is fixed at 0 in `selfsuff_reduced_bilateral22` — it is not

- **severity:** Critical
- **self_named_class:** `over-generalized negative from one confirming instance`
- **fits_existing_taxonomy:** **NO.** This is not fabrication and not staleness. The author checked
  one realization (`exo`), found the `.fx(i) = 0`, and then extended the *negative existence claim*
  ("no feasibility-import mechanism there") to a second realization without checking it. The class is
  about the **direction of generalization**: a verified positive in one member of a set was
  converted into a verified negative across the set. No existing class I know of describes
  "one instance checked, N asserted, and the assertion is a non-existence claim" — which is the worst
  possible shape, because non-existence claims are the ones readers never re-verify.
- **doc_location:** `modules/module_11.md:289`
- **doc_says:** "`vm_cost_trade_feasibility` is fixed at 0 in the `exo` and
  `selfsuff_reduced_bilateral22` realizations of Module 21 (no feasibility-import mechanism there),
  so it contributes 0 to the sum in those cases"
- **code_says:** `exo` — **true**, `vm_cost_trade_feasibility.fx(i) = 0;`.
  `selfsuff_reduced_bilateral22` — **false**. It has a live equation
  `q21_cost_trade_feasibility(i2).. vm_cost_trade_feasibility(i2) =g= sum((i_im,k_trade),
  v21_import_for_feasibility(i2,i_im,k_trade) * s21_cost_import);`, a declared
  `positive variables vm_cost_trade_feasibility(i)`, a scaling factor of `1e5`, and **no `.fx`
  anywhere** in the realization (it has no `presolve.gms` at all). It therefore has exactly the
  feasibility-import mechanism the doc says it lacks.
- **code_evidence:**
  - `modules/21_trade/exo/presolve.gms:10` — `vm_cost_trade_feasibility.fx(i) = 0;`
  - `modules/21_trade/selfsuff_reduced_bilateral22/equations.gms:99-101` — live equation
  - `modules/21_trade/selfsuff_reduced_bilateral22/declarations.gms:27`; `.../scaling.gms:10`
  - `rg -n 'vm_cost_trade_feasibility\.' modules/` returns no `.fx` for `bilateral22`
    (positive control: the same sweep returns the `exo` `.fx` line, so the absence is real)
- **why_it_matters:** `selfsuff_reduced_bilateral22` is the bilateral-trade realization used for
  trade-policy work. A reader debugging why regional costs are higher than expected under bilateral
  trade would read this note, cross `vm_cost_trade_feasibility` off the list as structurally zero,
  and never look at the one term that prices infeasibility-driven imports. This is "claiming
  something doesn't exist when it does" — the rubric's explicit Critical trigger — even though the
  affected realization is not the default.
- **confidence:** high

---

### F6: "All 32 cost variables are non-negative (except `vm_reward_cdr_aff`)" — 9 of 32 are free variables, and at least 3 are negative by design

- **severity:** Major
- **self_named_class:** `catalog-vs-checklist contradiction` (secondary: `declaration-block blindness`)
- **fits_existing_taxonomy:** **NO**, and this is the finding I would most want kept. Two things are
  going on and only the second is familiar.
  1. *Declaration-block blindness*: the sign domain of every term was inferred from the sign it
     carries in `q11_cost_reg` (all `+` except one `-`), never from the `positive variables` vs
     plain `variables` block that actually constrains it. That is a recognisable provenance failure.
  2. *Catalog-vs-checklist contradiction* — the class I am naming. **The doc already knows the
     truth and states it, in a different section, and then contradicts itself in the only section
     that is executable.** §3.8 (`:417`) says `vm_bioenergy_utility` "may be positive or negative
     cost"; §17.2 (`:1121`) says it "can be positive cost or negative benefit depending on
     scenario". Both correct. But §10.2, §16 and §17.4 — the testing/validation sections, the ones a
     reader converts into `stopifnot()` calls — encode a single-exception model. The reference prose
     is right; the prescription is wrong; only the prescription runs. Any audit that scores a doc
     claim-by-claim marks §3.8 correct and moves on, and any audit that scores section-by-section
     never notices the two sections disagree. The defect lives in the *gap between* two individually
     defensible statements.
- **doc_location:** `modules/module_11.md:738`, `:1051`, `:1220`
- **doc_says:**
  - `:738` — "**Check that all 32 cost variables are non-negative** (except `vm_reward_cdr_aff`) …
    Flag any negative costs (would indicate source module error)"
  - `:1051` — "1. Verify all cost variables are defined and non-negative"
  - `:1220` — `stopifnot(all(emission_costs >= 0))`
- **code_says:** In their **default** realizations, **9 of the 32** terms are declared in a plain
  `variables` block (free, sign-unconstrained), not `positive variables`:

  | Variable | Default realization | Line | Code's own description |
  |---|---|---|---|
  | `vm_processing_substitution_cost` | `20_processing/substitution_may21` | `:24` | "Costs **or benefits** of substituting one product by another" |
  | `vm_cost_landcon` | `39_landconversion/calib` | `:13` | "Costs for land expansion **and reduction**" |
  | `vm_cost_transp` | `40_transport/gtap_nov12` | `:13` | |
  | `vm_cost_AEI` | `41_area_equipped_for_irrigation/endo_apr13` | `:15` | |
  | `vm_p_fert_costs` | `54_phosphorus/off` | `:10` | |
  | `vm_emission_costs` | `56_ghg_policy/price_aug22` | `:39` | |
  | `vm_reward_cdr_aff` | `56_ghg_policy/price_aug22` | `:43` | (the one the doc names) |
  | `vm_peatland_cost` | `58_peatland/v2` | `:45` | "One-time and recurring cost of peatland conversion and management" |
  | `vm_bioenergy_utility` | `60_bioenergy/1st2ndgen_priced_feb24` | `:26` | "Utility as **negative costs** for producing bioenergy" |

  `vm_bioenergy_utility` is not merely *allowed* to be negative — it is negative **by construction**:
  `q60_bioenergy_incentive(i2).. vm_bioenergy_utility(i2) =e= sum((ct,k1st60), vm_dem_bioen(...) *
  fm_attributes("ge",k1st60) * (-i60_1stgen_bioenergy_subsidy(ct))) + sum((ct,kbe60), ... *
  (-i60_2ndgen_bioenergy_subsidy(ct)));` — a sum of terms each carrying an explicit unary minus. Under
  any non-negative subsidy it is ≤ 0 in every run.
- **code_evidence:** declaration blocks at the 9 file:line pairs tabled above (all read this session);
  `modules/60_bioenergy/1st2ndgen_priced_feb24/equations.gms:73-75`;
  `modules/38_factor_costs/sticky_feb18/declarations.gms:16` and
  `modules/10_land/landmatrix_dec18/declarations.gms:22` as positive-block controls confirming the
  block classification is being read correctly
- **why_it_matters:** §10.2 does not just misinform, it prescribes. A reader implements
  "flag any negative cost → source module error", the check fires on `vm_bioenergy_utility` in a
  perfectly correct default run, and they go debug M60 — which has no bug. §17.4's
  `stopifnot(all(emission_costs >= 0))` is worse: it is copy-pasteable R that aborts a correct
  validation suite, because `vm_emission_costs` is free and M56 can price net-negative emissions.
  The doc turns a correct model into an apparent failure.
- **confidence:** high

---

### F7: `vm_cost_urban` mechanism described as "costs for urban land expansion" — it is a symmetric deviation penalty on exogenously-fixed urban land

- **severity:** Major
- **self_named_class:** `name-inferred mechanism`
- **fits_existing_taxonomy:** unsure. It is adjacent to MAgPIE's standing parameterization-vs-mechanistic
  rule, but that rule is about "uses data about X" vs "models X". This is narrower and more mechanical:
  **the gloss is fully reconstructible from the variable's name alone**, and reconstructing it from the
  name is exactly what produces the error. `vm_cost_urban` → "costs for urban" → "costs for urban land
  expansion". No equation was consulted. The tell is that the gloss contains no information the
  identifier did not already carry.
- **doc_location:** `modules/module_11.md:261`, `:1107`
- **doc_says:** `:261` — "**Description:** Costs for urban land expansion";
  `:1107` — "| **34** (urban) | `vm_cost_urban(j)` | + | Urban land expansion (declared in M34) |"
- **code_says:** Under the default `exo_nov21`, urban land is **exogenous and hard-constrained**:
  `q34_urban_land(i2) .. sum(cell(i2,j2), vm_land(j2,"urban")) =e= sum((ct,cell(i2,j2)),
  i34_urban_area(ct,j2));`. `vm_cost_urban` is a **two-sided deviation penalty**:
  `q34_urban_cost1(j2) .. v34_cost1(j2) =g= sum(ct, i34_urban_area(ct,j2)) - vm_land(j2,"urban");`
  `q34_urban_cost2(j2) .. v34_cost2(j2) =g= vm_land(j2,"urban") - sum(ct, i34_urban_area(ct,j2));`
  `q34_urban_cell(j2) .. vm_cost_urban(j2) =e= (v34_cost1(j2) + v34_cost2(j2)) * s34_urban_deviation_cost;`
  The realization's own header states the purpose: "Cellular level land is prescribed via a very
  strong incentive not to deviate from cellular input data … This safeguards against infeasible
  outcomes". So it penalises **reducing** urban land exactly as much as expanding it, it is a
  numerical infeasibility safeguard rather than an economic cost, and its expected value in a
  feasible solution is ~0. The doc's gloss is wrong in direction (symmetric, not expansion-only), in
  kind (penalty, not cost), and in implication (urban land is not an optimisation choice at all under
  the default).
- **code_evidence:** `modules/34_urban/exo_nov21/equations.gms:9-13` (header), `:17-18`, `:20-21`,
  `:25-26`, `:30-31`; `config/default.cfg:1144` (`cfg$gms$urban <- "exo_nov21"`)
- **why_it_matters:** A reader building an urbanisation scenario reads "costs for urban land
  expansion", concludes MAgPIE prices urban sprawl economically, and designs a scenario around
  tuning that cost. In fact urban area is prescribed exogenously and the "cost" is a solver
  guardrail. This is a textbook violation of the CODE TRUTH directive ("Module 35 applies historical
  disturbance rates labeled 'wildfire'" is the canonical analogue), and it is duplicated in the
  §17.2 table, so both places a reader might check agree with each other and disagree with the code.
- **confidence:** high

---

### F8: `vm_cost_cropland` described as "(likely maintenance or baseline costs)" — it is tree-cover establishment + recurring costs + fallow/treecover shortfall penalties

- **severity:** Major
- **self_named_class:** `hedged speculation where the code is one grep away`
- **fits_existing_taxonomy:** **NO**, and I think this is the second-most valuable finding here.
  Every confabulation class I am aware of describes a claim asserted with unearned *confidence*. This
  is the inverse: the doc **flags its own uncertainty** ("likely") and is still wrong — and the hedge
  makes it worse, not better, in two compounding ways. (1) It launders an unchecked guess into
  something that reads as epistemic honesty, so it passes a reviewer scanning for overconfidence.
  (2) The hedge *suppresses* the reader's impulse to verify: "the doc already told me it's unsure,
  so this is the best available knowledge" — when in fact the answer is four lines of GAMS one grep
  away, and AGENT.md Step 2c authorises "I'm not certain" only when the code is *ambiguous*, which
  it is not here. A hedge in a position where the code is directly readable is a defect *because*
  it is a hedge. No existing class penalises a correctly-marked uncertainty; this one should be
  penalised, because the marking is itself the failure.
- **doc_location:** `modules/module_11.md:250`
- **doc_says:** "**Description:** Costs specific to cropland management (likely maintenance or
  baseline costs)"
- **code_says:** Under the default `detail_apr24`:
  `q29_cost_cropland(j2) .. vm_cost_cropland(j2) =e= v29_cost_treecover_est(j2) +
  v29_cost_treecover_recur(j2) + v29_fallow_missing(j2) * sum(ct, i29_fallow_penalty(ct)) +
  v29_treecover_missing(j2) * sum(ct, i29_treecover_penalty(ct));`
  That is: cropland **tree-cover** establishment cost + tree-cover recurring cost + a penalty for
  missing fallow-land requirements + a penalty for missing tree-cover requirements. It is neither
  "maintenance" nor "baseline" cost of cropland; two of the four terms are policy-constraint
  penalties and the other two are agroforestry costs. The §17.2 table (`:1103`) says only
  "Cell-summed", so it offers no correction.
- **code_evidence:** `modules/29_cropland/detail_apr24/equations.gms:26-32`;
  `modules/29_cropland/detail_apr24/declarations.gms:38`; `config/default.cfg:811`
- **why_it_matters:** A reader analysing a cost breakdown attributes `vm_cost_cropland` to
  generic cropland upkeep and misses that it is the channel through which cropland tree-cover
  targets and fallow requirements enter the objective — i.e. exactly the policy lever they would be
  looking for if they were studying agroforestry or fallow mandates.
- **confidence:** high

---

### F9: `kres` described as "(crop residues, wood fuel)" — `woodfuel` is not in `kres`

- **severity:** Major
- **self_named_class:** `set-member import from an adjacent set`
- **fits_existing_taxonomy:** unsure — close to exact-set-member-label discipline, but the specific
  signature is that the wrong member is **real and lives in a neighbouring set that appears in the
  same equation**. `woodfuel` is a genuine MAgPIE set member — of `k`, which is summed two lines away
  in `q11_cost_reg` (`equations.gms:21`). The error is contamination between two sets co-occurring in
  the reader's field of view, not invention.
- **doc_location:** `modules/module_11.md:186`
- **doc_says:** "**Description:** Costs for residue collection and processing (crop residues, wood fuel)"
- **code_says:** `kres(kall) Residues / res_cereals, res_fibrous, res_nonfibrous /` — three crop-residue
  types, no wood fuel. `woodfuel` is a member of `k(kall) Primary products`. M18's own declaration
  says "Production costs of harvesting **crop** residues".
- **code_evidence:** `modules/16_demand/sector_may15/sets.gms:13-14` (`kres` definition);
  `modules/14_yields/managementcalib_aug19/sets.gms:12-16` (`k` definition, contains `wood, woodfuel`);
  `modules/18_residues/flexreg_apr16/declarations.gms:17`
- **why_it_matters:** A reader accounting for wood-fuel costs would look in `vm_cost_prod_kres` and
  find nothing, or worse, would double-count wood fuel across `vm_cost_prod_kres` and
  `vm_cost_transp(j,k)`. The doc's §11.3 explicitly warns about double-counting; this claim causes it.
- **confidence:** high

---

### F10: `land` set members given as 5 friendly names — the set has 7 members with different labels

- **severity:** Major
- **self_named_class:** `friendly-label set enumeration`
- **fits_existing_taxonomy:** unsure. Exact-set-member-label discipline covers "use the code's
  labels". What it does not cover is the specific damage here: the paraphrase into readable English
  **silently changed the set's arity** (7 → 5) by collapsing `forestry`, `primforest` and
  `secdforest` into a single "forest" and dropping nothing visibly. The prose reads as an
  enumeration, so a reader takes the count as authoritative; the count is a casualty of the
  prettification, not of a miscount.
- **doc_location:** `modules/module_11.md:229`
- **doc_says:** "**Dimensions:** j (cells), land (cropland, pasture, forest, urban, other)"
- **code_says:** `land Land pools / crop, past, forestry, primforest, secdforest, urban, other /` —
  **7** members. Neither "cropland", "pasture" nor "forest" is a member label; the three distinct
  forest pools are exactly the distinction that matters for `vm_cost_landcon(j,land)`, since
  conversion costs differ across them.
- **code_evidence:** `core/sets.gms:250-251`
- **why_it_matters:** `sum((cell(i2,j2),land), vm_cost_landcon(j2,land))` at
  `modules/11_costs/default/equations.gms:20` sums over all 7 pools. A reader reconstructing the
  cost breakdown from the doc's 5-member list will produce a sum that does not reconcile with
  `v11_cost_reg.l(i)` and will then chase the phantom bug §11.5 describes. The doc supplies both the
  wrong set and the debugging section for the symptom it causes.
- **confidence:** high

---

### F11: Unit-gloss arithmetic drift — magnitude claims are off by 10^6, and §5 contradicts §15.1/§16

- **severity:** Major
- **self_named_class:** `unit-gloss arithmetic drift`
- **fits_existing_taxonomy:** unsure. "Right concept / wrong number" is the nearest fit, but the
  generating mechanism is specific enough to deserve its own name: the variable's **declared unit is
  already `mio. USD`**, and every gloss re-reads the numeral as if it were plain USD. The error is
  not a miscalculation; it is a unit that was declared once and then dropped in every downstream
  sentence. Once named this way it is mechanically greppable (any "10^N mio. USD" followed by a
  parenthetical in plain currency), which no arithmetic-error class would suggest.
- **doc_location:** `modules/module_11.md:553`, `:554`, `:988`, `:1054`
- **doc_says:**
  - `:553` — "**vm_cost_glo:** ~10^7 USD/yr (tens of billions of dollars globally)"
  - `:554` — "**v11_cost_reg:** ~10^6 USD/yr (billions per region)"
  - `:988` — "Baseline scenarios: ~10^8 mio. USD/yr (100 billion USD/yr) in 1995"
  - `:1054` — "4. Validate objective function value is realistic (10^8-10^9 mio. USD/yr)"
- **code_says:** `vm_cost_glo` is declared "Total costs of production (**mio. USD17MER** per yr)".
  Therefore:
  - `:988` — 10^8 **mio.** USD = 10^14 USD = **100 trillion**, not "100 billion". Off by 10^6.
  - `:553` — 10^7 in the variable's own units = 10^13 USD = **10 trillion**, not "tens of billions".
    Off by ~10^3–10^4 in the opposite direction (the numeral was read as plain USD, the gloss written
    from a plausible-sounding intuition).
  - `:554` — 10^6 mio. USD = 10^12 USD = **1 trillion** per region, not "billions".
  - §5 and §15.1 **contradict each other**: §5 derives ~10^7 from `vm_cost_glo.scale = 1e7`, while
    §15.1/§16 assert 10^8–10^9. These cannot both be right; the code's scaling factors
    (`vm_cost_glo.scale = 1e7`, `v11_cost_reg.scale = 1e6`, ×12 regions ≈ 1.2e7) are internally
    consistent with §5 and inconsistent with §15.1.
- **code_evidence:** `modules/11_costs/default/declarations.gms:9-10` (units);
  `modules/11_costs/default/scaling.gms:8-9`; `core/sets.gms:20-21` (`i` has 12 members:
  CAZ, CHA, EUR, IND, JPN, LAM, MEA, NEU, OAS, REF, SSA, USA)
- **why_it_matters:** `:1054` is under "**Testing Priority**" — it is an acceptance criterion. A
  reader validates `vm_cost_glo.l` against "10^8–10^9 mio. USD/yr" and accepts a run 10–100× too
  large, or rejects a correct one. §11.3 ("Unrealistic Cost Magnitudes") then tells them the symptom
  of exactly the error the doc just induced. I do **not** assert the true magnitude — that needs a
  GDX I did not read (see Coverage honesty). The finding is the internal arithmetic and the §5-vs-§15.1
  contradiction, both of which are settled without a run.
- **confidence:** high (on the arithmetic and the contradiction); the true magnitude is unverified.

---

### F12: "All cost variables have naming convention `vm_cost_*` or `vm_*_cost*`" — refuted by the equation quoted 500 lines earlier

- **severity:** Minor
- **self_named_class:** `self-refuting generalization`
- **fits_existing_taxonomy:** unsure. The interesting property is not that the generalization is
  false but that **its counterexamples are already printed in the same document**, in the verbatim
  code block at `:84-116` that the doc itself calls canonical. No external verification was needed —
  only re-reading the page. A class worth naming because it is detectable with zero code access.
- **doc_location:** `modules/module_11.md:531`
- **doc_says:** "**Key Pattern:** All cost variables have naming convention `vm_cost_*` or
  `vm_*_cost*` and units of mio. USD17MER/yr. **Exception:** `vm_reward_cdr_aff` is revenue, not
  cost, hence the negative sign."
- **code_says:** At least four of the 32 terms match neither pattern: `vm_rotation_penalty(i2)`
  (`equations.gms:23`), `vm_bioenergy_utility(i2)` (`:38`), `vm_costs_additional_mon(i2)` (`:40`),
  and `vm_reward_cdr_aff(i2)` (`:27`). Note the stated "Exception" is about **sign**, not naming, so
  it does not discharge the naming claim even for `vm_reward_cdr_aff`. The unit half of the same
  sentence is separately problematic — see Observation O1.
- **code_evidence:** `modules/11_costs/default/equations.gms:23`, `:27`, `:38`, `:40`
- **why_it_matters:** Low direct harm — a reader is unlikely to act on a naming convention. It
  matters as a signal: a "Key Pattern" asserted over a set whose full enumeration is on the same
  page, and falsified by it, indicates the section was written from recollection of the module rather
  than from the module.
- **confidence:** high

---

### F13: "Modules that do NOT contribute (19 modules)" followed by an 18-item list

- **severity:** Minor
- **self_named_class:** `count/enumeration off-by-self`
- **fits_existing_taxonomy:** partly ("fabricated count for a set list"), but the cause is specific
  and worth its own name: 46 − 27 = 19 is arithmetically **correct** only if Module 11 is counted
  among the modules that do not contribute to its own equation. The list, written separately, omits
  M11 — reasonably. So the count and the list are each defensible under different conventions and
  contradict each other. Not a fabrication; a boundary-condition disagreement between two adjacent
  lines.
- **doc_location:** `modules/module_11.md:1128-1129`
- **doc_says:** "**Modules that do NOT contribute to `q11_cost_reg`** (19 modules): - 09 (drivers),
  12 (interest rate), 14 (yields), 15 (food), 16 (demand), 17 (production), 22 (land conservation),
  28 (age class), 36 (employment), 37 (labor productivity), 43 (water availability), 45 (climate),
  51 (nitrogen emissions), 52 (carbon), 53 (methane), 55 (AWMS), 62 (material), 80 (optimization)"
- **code_says:** MAgPIE has 46 module directories. 27 contribute to `q11_cost_reg`. The listed
  non-contributors number **18**; the 19th is Module 11 itself, which is not listed. Every one of the
  18 listed non-contributions is correct (verified: none of the 32 terms is declared by any of them).
- **code_evidence:** `ls -d modules/*/` → 46 directories; the 32-term producer sweep across all
  `modules/*/*/declarations.gms` returns exactly the 27 modules of the §17.2 table
- **why_it_matters:** Minor. The list is right and the count is one off; a reader who counts the
  bullets and gets 18 has to decide which to trust. It matters mainly because §17.2 is billed as
  "canonical … re-derived 2026-05-23 R3", and a canonical section should not disagree with itself
  on the count it exists to provide.
- **confidence:** high

---

### F14: Header verification date (2025-10-12) contradicts the two footers (2026-05-16)

- **severity:** Minor
- **self_named_class:** stale metadata header
- **fits_existing_taxonomy:** yes
- **doc_location:** `modules/module_11.md:6` vs `:1275` and `:1282`
- **doc_says:** `:6` — "**Status:** ✅ Fully Verified (2025-10-12)"; `:1275` — "**Documentation
  Status:** ✅ Verified (2026-05-16 — PR #866 sync)"; `:1282` — "**Last Verified**: 2026-05-16"
- **code_says:** The PR#866 trade split is present in the code and reflected in the doc, so the
  2026-05-16 footer is the accurate one and the header was not updated with the rest of the file.
- **code_evidence:** `modules/11_costs/default/equations.gms:30-32` (the three split trade terms)
- **why_it_matters:** The header is the first thing read and drives the staleness badge. A reader
  applying the Step 1b freshness rule from the header would classify this doc ~9 months more stale
  than it is and either distrust correct content or trigger an unnecessary `/sync`.
- **confidence:** high

---

## Out-of-taxonomy / unclassifiable observations

Recorded individually, uncollapsed. None of these is scored as a defect above; each is either a
code-side issue, an unresolvable claim, or something I could not confidently call wrong.

**O1 — The doc asserts a unit invariant that 5 of 32 code declaration strings contradict, and gives
no hint the code disagrees. This is a CODE defect the doc trips over, not a doc defect.**
§4.3 (`:531`) and §11.3 (`:834`) both assert "All cost variables should be in mio. USD17MER/yr".
Semantically the doc is **right** — `q11_cost_reg` sums them all with no conversion factor, so they
must be. But the declaration strings in the default realizations say otherwise in five places:
- `modules/42_water_demand/all_sectors_aug13/declarations.gms:31` — `vm_water_cost(i)  Cost of
  irrigation water (**USD17MER per m^3**)`. The equation proves this docstring wrong:
  `vm_water_cost(i2) =e= sum(cell(i2,j2), vm_watdem("agriculture",j2)) * ic42_pumping_cost(i2)`
  (`equations.gms:17`), and `vm_watdem` is `(mio. m^3 per yr)` (`declarations.gms:29`) — so the
  product is mio. USD/yr. The **same file** gets it right one block up:
  `q42_water_cost(i)  Total cost of pumping irrigation water (USD17MER per yr)` (`:25`). The
  variable's docstring is simply stale.
- `modules/60_bioenergy/1st2ndgen_priced_feb24/declarations.gms:26` — "(USD17MER per yr)", missing "mio."
- `modules/32_forestry/dynamic_may24/declarations.gms:63` — "(Mio USD)", no year vintage, no "per yr"
- `modules/44_biodiversity/bii_target/declarations.gms:10` — "(mio USD17MER)", no "per yr"
- `modules/34_urban/exo_nov21/declarations.gms:13` — "Technical adjustment costs", **no unit at all**

Why this is worth recording rather than scoring: §11.3's debugging advice is "**Check units:** All
cost variables should be in mio. USD17MER/yr". A reader who follows that advice for a water-cost
anomaly opens M42's declarations, reads "USD17MER per m^3", and concludes they have found a genuine
unit bug in the objective function. They have not. The doc is correct and the code comment is wrong,
and the doc's own debugging procedure routes the reader into the trap without warning them. I do not
know what to call a doc defect that consists of *being right without noticing the code disagrees* —
the doc would be improved by a caveat it currently has no reason to contain. Flagging for M42/M60/M32/M44/M34
docstring fixes upstream.

**O2 — §8.3's "benefits are not in the objective function" is contradicted by three terms in the
objective, but I am not confident it is a defect.** `:657` says "Benefits/demand are represented as
constraints (in Module 15, 70, etc.), not in objective function." Yet `vm_reward_cdr_aff` (revenue),
`vm_bioenergy_utility` ("Utility as negative costs", `60/…/declarations.gms:26`) and
`vm_processing_substitution_cost` ("Costs **or benefits**", `20/…/declarations.gms:24`) are all
benefit terms sitting in `q11_cost_reg`. The sentence's evident intended referent is welfare /
consumer surplus / ecosystem services — and §12.1 (`:889`) states that narrower claim correctly
("Not represented in objective: Consumer surplus, ecosystem services, health benefits, social
welfare"). So §8.3 is either a sloppy overreach of a true claim or a false claim, and I cannot
adjudicate which without knowing authorial intent. Reporting as uncertain rather than inflating to a
finding or dropping it.

**O3 — "Module 38 … LARGEST contributor" is unverifiable from source.** `:1109` ("LARGEST — labor +
capital factor costs for crops") and `:937` ("largest contributor") are empirical claims about
solution values. Confirming or refuting requires a `fulldata.gdx`, which I did not read. Not scored.
Plausible on domain grounds, but it is stated as fact in a table whose other cells are all
code-verifiable, which makes it read as though it were equally verified. Recording the
category mismatch rather than the claim.

**O4 — Centrality: the doc is faithful to its cited source, but the source's semantics are confused,
and neither matches this round's brief.** `:1088-1092` cites `Module_Dependencies.md` and reports
"Rank 1 of 46, Total Connections 28 (provides to 1 [GAMS solver], depends on 27 modules)".
`core_docs/Module_Dependencies.md:31` does say exactly that, so module_11.md has not drifted from its
source. Three problems I could not resolve and will not assert either way:
  (a) The audit brief states "degree centrality 35, the 2nd-highest, consuming 33 interface
      variables". I independently count **32** terms in `q11_cost_reg` from **27** modules and could
      not reproduce 33 or 35 under any counting rule I tried (32 terms; 32 distinct variables; +1 for
      `vm_cost_glo` = 33 if the module's own output is counted; 33 + ~2 for `v11_cost_reg`/`vm_cost_transp`
      scaling ≠ 35 cleanly). I flag the discrepancy rather than adopt either figure.
  (b) "Total Connections: 28" mixes units — it adds a **module** count (27) to a **non-module**
      count (1 = "the solver"). As F1 establishes, that "1" is really Module 80, so 28 happens to be
      the correct module-degree; but the doc counts 27 *modules* on one side while ignoring that
      those 27 supply **32 variables**. A variable-degree metric and a module-degree metric are being
      averaged into one number labelled "Total Connections".
  (c) `Module_Dependencies.md:425` explicitly declares itself the authority for centrality rankings
      and warns that ~15+ files cite it. If (a) is right, the error is in the hub, not here.
Not scored against module_11.md, which correctly cites its source. Escalating to whoever owns
`Module_Dependencies.md`.

**O5 — §3.1 residues gloss is slightly off but I would not act on it.** `:186` "Costs for residue
collection **and processing**"; `modules/18_residues/flexreg_apr16/declarations.gms:17` says
"Production costs of **harvesting** crop residues". "Processing" is not in the code's description.
Too minor to score separately from F9, which covers the same line; recording the second inaccuracy
in the same sentence so it is not lost when F9 is fixed.

**O6 — The Limitations block says "unconditionally sums 31 cost variables" where the rest of the doc
says 32.** `:1017`. Reconcilable (31 costs + 1 reward = 32 terms), so probably not an error — but it
is the only place in the doc using 31 as the headline figure, and §1.2/§4.2/§4.3/§14.1/§17.2 all use
32. Recording as a consistency wobble, not scoring it.

**O7 — `vm_cost_urban` has no unit in its declaration and the doc supplies one.** §4.3 asserts all
32 are "mio. USD17MER/yr"; `modules/34_urban/exo_nov21/declarations.gms:13` reads
`vm_cost_urban(j)          Technical adjustment costs` — no unit, and the phrase "technical
adjustment" corroborates F7's reading that this is a solver guardrail rather than an economic cost.
The doc supplying a unit the code omits is *probably* correct (dimensional necessity) but is an
inference presented as a fact. Related to O1; separated because here the code says nothing at all
rather than something wrong, which is a different provenance situation.

**O8 — I could not classify the §7.1 "Module 50 (Nitrogen): Fertilizer costs" entry.** `:601`.
M50 provides `vm_nr_inorg_fert_costs` (nitrogen only); phosphorus fertilizer costs come from M54,
as the doc's own §3.5 (`:330`) emphatically states ("NOT Module 50 or 51 despite the variable name").
"Fertilizer costs" unqualified in §7.1 therefore either (a) means "the fertilizer costs M50
provides", which is true, or (b) implies M50 owns fertilizer costs generally, which is false and is
precisely the confusion §3.5 exists to prevent. Same section and same class as F3/F4, but unlike
those two it is genuinely ambiguous rather than plainly wrong, so I am not scoring it. Noting that
the §7.1 curated list has now produced two confirmed wrong attributions (F3, F4) and one ambiguous
one — the section as a whole looks written from memory and warrants regeneration from §17.2's table
rather than line-by-line patching.

**O9 — A structural observation about where the defects are, which I think matters more than any
single finding.** Of the 14 findings, **zero** are in §2 (the verbatim equation quotes) or §3's
identifier/citation layer: all 32 variable names, all 32 `equations.gms:N` citations, all 27 source
modules, both formulas, all three scaling lines, both declaration line numbers, the LOC counts, the
equation count, the realization name, and all six `ov_*` GDX symbol names are **correct**. The doc's
machine-checkable surface is in excellent shape. Every defect found lives in one of three places:
(i) prose summaries that restate the table in English (F3, F4 — §7.1); (ii) *descriptions* and
*dimension glosses* attached to correct identifiers (F7, F8, F9, F10 — §3); (iii) the
testing/validation prescriptions (F6, F11 — §10, §16, §17.4). That is a coherent signal: the
identifier layer has been audited to death by previous rounds and by the name-checking validators,
and the defects have migrated to exactly the layers those validators cannot parse — English prose
attached to correct names. F6 and F8 are the sharpest cases: in F6 the doc states the correct fact in
one section and contradicts it in the executable one; in F8 the doc marks its own uncertainty and is
wrong anyway. Neither is reachable by any check that verifies identifiers, counts, or citations.
I record this as an observation rather than a finding because it is a claim about the audit, not
about the doc.

---

## Coverage honesty

What I did **not** check, and why:

1. **No GDX / no model run.** Every solution-value claim is unverified: §15.1 typical magnitudes,
   §15.2 cost composition shares (40-60% factor costs, etc.), "M38 is the LARGEST contributor"
   (§13.2, §17.2), §16's "10^8-10^9" acceptance range, and §10.3's "top 5-10 components >90% of
   total". F11 scores only the **internal arithmetic and the §5-vs-§15.1 contradiction**, which are
   settled without a run; it does **not** assert the true magnitude of `vm_cost_glo`. If someone has
   a `fulldata.gdx`, §15 is the highest-value unaudited surface in this doc and I would expect
   further findings there.

2. **The "land rent" claim at `:176` is unchecked.** "land rent is not an explicit M38 cost — it
   emerges as the shadow value of the land constraint, not a term in Module 11". I did not read M38's
   equations or verify the shadow-price reasoning. It is a substantive economic-mechanism claim
   sitting in the catalog, and it is exactly the kind of claim F7/F8 show this doc gets wrong.
   **Recommend it be audited.**

3. **The 15 fabricated names in the R3 footnote (`:1132-1133`) were not re-verified.** The footnote
   asserts that `v12_interest`, `vm_cost_natveg`, `vm_cost_prod`, etc. exist in no GAMS file. I did
   not re-run that. Per the read-side gate, I am relaying a recalled negative verdict without
   re-derivation — treat it as unverified.

4. **Non-default realizations of the 27 source modules were not audited.** My declaration sweep
   covered each source module's **default** realization only (as listed in `config/default.cfg`). The
   sign-domain table in F6 is therefore a claim about defaults; other realizations may declare more
   or fewer of the 32 terms as free variables. F5 (`bilateral22`) is the exception — I checked all
   three M21 realizations because the doc made a specific cross-realization claim.

5. **§11 (Common Issues), §12 (Key Insights), §14.2 (hypothetical future realizations) were read
   but not scored**, and are excluded from the denominator. They are advisory/speculative prose with
   little falsifiable content. §11.3's "Check units" line is the exception and surfaces in O1.

6. **§17.1 (conservation laws) got a spot-check only, counted as 1 claim.** I confirmed M11 declares
   no equations other than `q11_cost_glo`/`q11_cost_reg` (`declarations.gms:13-16`), which makes the
   five "Not in [X] balance" claims true on their face. I did not cross-read the four
   `cross_module/*_conservation.md` files to check the claim is stated consistently there.

7. **`scripts/check_*.py` was not read, run, or consulted in any form** — no regexes, no role map, no
   `--dump-rolemap`. Ground truth in this report is derived only from `.gms` files and
   `config/default.cfg` read this session. One consequence worth stating: I do not know whether the
   existing validators already catch any of F1-F14, or whether the allowlist marker at `:1133` masks
   anything. That comparison is deliberately out of scope for this round.

8. **Absence claims carry positive controls.** The two negative findings that matter (F5's "no `.fx`
   in `bilateral22`", and the `pm_interest`-not-in-M11 check backing O4's context) were each run
   alongside a positive control on the same command — the `exo` `.fx` line returns for F5, and
   `rg -c 'i2' modules/11_costs/default/equations.gms` returns 33 for the `pm_interest` sweep. Neither
   absence rests on a single silent-empty result. All greps used `rg -n` (never `rg -r`).
