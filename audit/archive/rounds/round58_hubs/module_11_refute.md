# M11 refutation pass (R58)

**Target of refutation:** `audit/archive/rounds/round58_hubs/module_11_audit.md`
**Method:** every finding re-derived from `.gms` source + `config/default.cfg` read this session on
`develop` @ 0d7ebeb90. `scripts/check_*.py` not read or run. All greps `rg -n` (never `rg -r`).
Absence claims carry positive controls, recorded inline.

**Headline:** 0 of 14 fully refuted. 11 survive as stated; 3 partially refuted (2 severity
reductions, 1 arithmetic correction). The auditor's *code* claims held up under independent
re-derivation without exception — every declaration block, equation, set, and realization default
they cite is as they describe it. Where they overreached, it was in **framing and severity**, not in
fact. Two of their own citations are off (F6 `:1220`→`:1221`, F8 `26-32`→`28-32`) and one headline
number is wrong by 10^3 (F11).

---

### F1: The doc reifies "the GAMS solver" as M11's only consumer, erasing the real M11 → M80 module edge
- **verdict:** PARTIALLY_REFUTED
- **my_independent_check:**
  - `rg -n 'vm_cost_glo' modules/ core/ scripts/ --glob '!*.md'` — outside `11_costs`, hits are
    **exclusively** in `modules/80_optimization/*/solve.gms` (+ `80_optimization/module.gms:15`).
    Positive control: same sweep returns the 8 in-module hits (`11_costs/default/declarations.gms:9`,
    `scaling.gms:8`, `equations.gms:10`, `postsolve.gms:11,15,19,23`, `module.gms:12`). Absence
    elsewhere is real.
  - `modules/80_optimization/nlp_apr17/solve.gms:34` — `solve magpie USING nlp MINIMIZING vm_cost_glo;`
    (default per `config/default.cfg:2300` = `nlp_apr17`).
  - `rg -n 'solve +magpie' modules/ core/` outside `80_optimization` → **empty**; positive control
    `rg -c` inside returns 16/3/2/4 for `lp_nlp_apr17`/`nlp_par`/`nlp_ipopt`/`nlp_apr17`. So every
    solve is mediated by M80.
  - Doc read: `modules/module_11.md:1090`, `:1091`, `:1128-1130`, `:1136`, `:1144`.
- **reasoning:** The code fact is right: M80 is an ordinary module and it is M11's only consumer, so
  `:1144` ("Other modules do NOT depend on Module 11 variables") is **flatly false** — that part
  stands. But three planks of the Critical framing do not survive:
  1. **"The doc has no slot in which M80 could appear" is wrong.** `:1090` records "provides to 1",
     and `:1136` records "`vm_cost_glo` → **GAMS Solver** (objective function to minimize)". The doc
     consistently carries exactly one downstream consumer and counts it. The defect is the *label* on
     that endpoint, not a missing slot. "Numerically right by accident" overstates: a doc that says
     "one downstream consumer, it's the thing that runs the solve" points a reader at
     `80_optimization/*/solve.gms` in one grep.
  2. **The `:1130` complaint misfires on the wrong sentence.** `:1128`'s header is "Modules that do
     NOT contribute to **`q11_cost_reg`**" — and M80 genuinely contributes no term to `q11_cost_reg`
     (I re-derived all 32 terms from `equations.gms:15-47`; none is M80's). Listing M80 there is
     **correct**. The real flaw is narrower: `:1130`'s blanket rationale ("provide non-cost outputs …
     or feed costs in indirectly") over-generalizes across an 18-item list and does not fit M80.
  3. **Not a new taxonomy class.** This is the R20 anchor shape — "doc states the wrong consumer set"
     (bug class 15 / the `pm_carbon_density_ac` anchor). The novelty claimed ("category error one
     level up, invisible to any check presupposing two module endpoints") does not earn a new class;
     the consumer set is stated, just with a non-module label on its single member.
  **Severity:** the R20 anchor is Critical because the missed consumers failed **silently** (wrong
  numbers, no error). Here the failure is **loud**: rename or retype `vm_cost_glo` and M80's solve
  statement throws a GAMS compile error immediately. A blast-radius reader cannot silently ship the
  mistake. That is the Major definition ("misleads about behavior, but won't directly cause damaging
  action"), not Critical.
- **if PARTIALLY:** Stands — `:1144`'s universal is false; `:1130`'s rationale sentence does not
  cover M80; "GAMS solver" should read "Module 80 (optimization), whose `solve.gms` names
  `vm_cost_glo` as the objective". Refuted — the "erased / no slot / right by accident" framing, the
  `:1130` listing complaint (the listing is correct; only its rationale is), and the new-class claim.
- **severity_agreed:** **Major** (down from Critical)

---

### F2: "One-way data flow" / "no feedback loops" is false — module 80 writes a bound onto `vm_cost_glo`
- **verdict:** PARTIALLY_REFUTED
- **my_independent_check:** `modules/80_optimization/lp_nlp_apr17/solve.gms:70-79` read in full:
  `:75 vm_cost_glo.up = vm_cost_glo.l;` → `:76 solve magpie USING nlp MINIMIZING vm_landdiff;` →
  `:78 vm_cost_glo.up = Inf;`, guarded by `:74 if ((magpie.modelstat=1 or magpie.modelstat = 7),`.
  Repeated at `:195`/`:198` (confirmed via `rg -n 'vm_cost_glo\.'`). `config/default.cfg:2300` =
  `nlp_apr17`; I confirmed `nlp_apr17/solve.gms` contains no `.up` write (only `.l` displays at
  `:39-40`, `:75-76`). Doc read: `modules/module_11.md:1141-1144`.
- **reasoning:** The code fact is exactly as described. But the finding attacks a section whose
  actual claim is **true**. §17.3 is titled "Circular Dependencies" and its lead claim (`:1141`,
  "Module 11 participates in **zero circular dependencies**") is correct: there is no equation-level
  cycle. `vm_cost_glo.up = vm_cost_glo.l` is **solver control flow between solves** in a `.gms`
  script — no M11 equation reads anything M80 produces, and M80 supplies M11 no variable. M11 really
  is a terminal sink in the data-flow sense the section is about. Bounding a variable from outside is
  not "providing a variable back".
  Harm claim (2) — that "no feedback loops" would let a reader conclude the land-smoothing second
  solve cannot exist — is a stretch; nobody infers M80's solve-loop capabilities from M11's
  circular-dependency section. Harm claim (1) — that a reader changing `vm_cost_glo`'s bounds won't
  know `lp_nlp_apr17` manipulates `.up` — is real, but that is **F1's defect** (M80 unnamed as
  consumer), not a separate feedback-loop defect.
  **Double-counting:** F1 and F2 both score `:1144`. The same doc line carries a Critical in F1 and a
  Major in F2. F2's only distinct contribution is the `.up` code fact in a **non-default** realization.
- **if PARTIALLY:** Stands — the `.up`/`Inf` write is real and does dent the universal at `:1143`
  ("One-way data flow"); a one-clause caveat in §17.3 is warranted. Refuted — "zero circular
  dependencies" (`:1141`) is TRUE and should not be scored against; `:1144` is F1's line, not a
  second finding; and no "two-way edge" exists in the data-flow sense §17.3 uses.
- **severity_agreed:** **Minor** (down from Major) — a non-default control-flow detail of another
  module, absent from a section whose own subject is correctly described.

---

### F3: §7.1 attributes urban costs to Module 10 (Land)
- **verdict:** SURVIVES
- **my_independent_check:** `rg -n 'vm_cost_urban' --glob 'modules/*/*/declarations.gms'` →
  **only** `modules/34_urban/exo_nov21/declarations.gms:13` and `modules/34_urban/static/declarations.gms:10`.
  `rg -n 'vm_cost_land_transition' --glob 'modules/*/*/declarations.gms'` → only
  `modules/10_land/landmatrix_dec18/declarations.gms:22`. M10's block header confirmed
  `positive variables` containing `vm_land`, `vm_landexpansion`, `vm_landreduction`,
  `vm_cost_land_transition` — **no urban cost**. `config/default.cfg:1144` = `exo_nov21`.
  Doc read: `:599`, and its own contradicting `:260` (§3.2) and `:1107` (§17.2 table, "**34** (urban)
  | `vm_cost_urban(j)`").
- **reasoning:** I tried to defend `:599`. The only available defence is that M10 declares
  `vm_land(j,land)` whose `land` set contains `"urban"` (`core/sets.gms:250-251`), so M10 "touches"
  urban land. That defence fails on the section's own framing: `:587` scopes §7.1 to "**27 modules**
  providing **cost variables**". In that scope "urban costs" can only denote `vm_cost_urban`, which
  M34 owns. Worse, §7.1 omits M29 and M34 entirely (its curated list runs 38, 70, 31, 18, 30, 39, 10,
  50, 41, 56, 57, 59, 58, 21, 40, 20, 32, 35 = 18 of the 27), so the cost is not merely mislabelled —
  it is reassigned to a module that has it not, with the true owner absent from the list.
  Rubric trigger fires verbatim and first: **"Wrong module attribution for a cost variable"** →
  Critical. `landmatrix_dec18` is in the land balance; sending an editor there is precisely the
  "edit the wrong file" harm the Critical definition names.
- **severity_agreed:** **Critical**

---

### F4: §7.1 attributes cropland costs to Module 30
- **verdict:** SURVIVES
- **my_independent_check:** `rg -n 'vm_cost_cropland' --glob 'modules/*/*/declarations.gms'` →
  `modules/29_cropland/detail_apr24/declarations.gms:38` and `simple_apr24/declarations.gms:21` only.
  `rg -n 'vm_rotation_penalty' --glob 'modules/*/*/declarations.gms'` →
  `modules/30_croparea/detail_apr24/declarations.gms:22` and `simple_apr24/declarations.gms:19` only.
  `config/default.cfg:811` = `cropland <- "detail_apr24"`; `:912` = `croparea <- "simple_apr24"`.
  Doc read: `:594`, vs its own `:308` (§3.4, "Module 30 (Croparea)") and `:1103`/`:1104` (§17.2
  correctly splits `vm_cost_cropland`→M29, `vm_rotation_penalty`→M30).
- **reasoning:** Half the entry is right ("rotation costs" → M30 ✓); "Cropland … costs" → M30 is
  wrong, M29 owns `vm_cost_cropland`. I looked for a loose reading — "cropland costs" as "costs
  relating to crop area", which M30 does handle — but it dies on the same fact as F3: M29 is **absent
  from §7.1 entirely**, so the loose reading leaves `vm_cost_cropland` attributed to M30 and nowhere
  else in the section. Same explicit Critical trigger as F3. The "Module 30 (Crop)" naming slip
  (the module is `30_croparea`) is a Minor sub-issue and I would fold it into this finding rather than
  score it separately — it is not what makes the entry Critical.
- **severity_agreed:** **Critical**

---

### F5: PR#866 note claims `vm_cost_trade_feasibility` is fixed at 0 in `selfsuff_reduced_bilateral22` — it is not
- **verdict:** SURVIVES
- **my_independent_check:** `ls -d modules/21_trade/*/` → `exo`, `selfsuff_reduced`,
  `selfsuff_reduced_bilateral22`. `rg -n 'vm_cost_trade_feasibility' modules/21_trade/ modules/11_costs/`:
  - `exo/presolve.gms:10` — `vm_cost_trade_feasibility.fx(i) = 0;` → doc **correct** here.
  - `selfsuff_reduced_bilateral22`: `equations.gms:97-99` — live
    `q21_cost_trade_feasibility(i2).. vm_cost_trade_feasibility(i2) =g= sum((i_im,k_trade), v21_import_for_feasibility(i2,i_im,k_trade) * s21_cost_import);`
    (I read `:90-101`); `declarations.gms:27` inside a **`positive variables`** block that also
    declares `v21_import_for_feasibility(i_ex,i_im,k_trade) Additional imports to maintain feasibility`;
    `scaling.gms:10` = `1e5`. **No `.fx` returned, and `ls modules/21_trade/selfsuff_reduced_bilateral22/`
    shows no `presolve.gms` exists at all.** Positive control: the identical sweep returns `exo`'s
    `.fx` line, so the absence is real, not a broken search.
  - `config/default.cfg:650` = `trade <- "selfsuff_reduced"` (bilateral22 is **not** default).
- **reasoning:** I pushed hard on one defence: since the equation is `=g=` on a positive variable
  entering a minimised objective, the solver drives `vm_cost_trade_feasibility.l` to `max(0, RHS)`,
  which **is** 0 whenever no feasibility imports are needed. So the doc's numeric claim could be
  accidentally true in a well-behaved run. That defence fails, because the doc does not claim "is
  usually 0" — it claims it **"is fixed at 0"** and that there is **"no feasibility-import mechanism
  there"**. Both are structurally false: `v21_import_for_feasibility` exists and the model *can* buy
  feasibility at `s21_cost_import`. The difference between "hard-fixed to 0, mechanism absent" (`exo`)
  and "priced penalty that is 0 only at a feasible optimum" (`bilateral22`) is exactly the difference
  a trade researcher needs. Rubric trigger fires: **"Claimed a function/variable/file does not exist
  when it does"** → Critical; "first trigger that fires wins", and non-default status is not a listed
  mitigator. The class name ("over-generalized negative from one confirming instance") is a fair
  description of the mechanism but the defect itself is the standard false-non-existence trigger.
- **severity_agreed:** **Critical**

---

### F6: "All 32 cost variables are non-negative (except `vm_reward_cdr_aff`)" — 9 of 32 are free variables, at least 3 negative by design
- **verdict:** SURVIVES (auditor's citation off by one line; substance strengthened)
- **my_independent_check:** I dumped the block structure of every cited `declarations.gms` and
  confirmed **9 of 9** sit in a plain `variables` block, not `positive variables`:
  | Variable | File:line | Block header |
  |---|---|---|
  | `vm_processing_substitution_cost` | `20_processing/substitution_may21/declarations.gms:24` | `variables` `:23` (a `positive variables` block sits at `:15` with `vm_cost_processing` at `:20`) |
  | `vm_cost_landcon` | `39_landconversion/calib/declarations.gms:13` | `variables` `:12` |
  | `vm_cost_transp` | `40_transport/gtap_nov12/declarations.gms:13` | `variables` `:12` |
  | `vm_cost_AEI` | `41_area_equipped_for_irrigation/endo_apr13/declarations.gms:15` | `variables` `:14` (`positive variables` at `:18`) |
  | `vm_p_fert_costs` | `54_phosphorus/off/declarations.gms:10` | `variables` `:9` |
  | `vm_emission_costs` | `56_ghg_policy/price_aug22/declarations.gms:39` | `variables` `:38` (`positive variables` at `:33`) |
  | `vm_reward_cdr_aff` | `56_ghg_policy/price_aug22/declarations.gms:43` | `variables` `:38` |
  | `vm_peatland_cost` | `58_peatland/v2/declarations.gms:45` | `variables` `:43` (`positive variables` at `:49`) |
  | `vm_bioenergy_utility` | `60_bioenergy/1st2ndgen_priced_feb24/declarations.gms:26` | `variables` `:25` (`positive variables` at `:19`) |
  Positive controls that the block classification is being read correctly:
  `38_factor_costs/sticky_feb18/declarations.gms:15` = `positive variables` → `:16 vm_cost_prod_crop`;
  `10_land/landmatrix_dec18/declarations.gms` `positive variables` → `:22 vm_cost_land_transition`.
  All 9 defaults confirmed against `config/default.cfg:633,1285,1311,1319,1605,1631,1871,2000`.
- **reasoning:** This is the auditor's strongest finding and it got **stronger** under adversarial
  scrutiny, not weaker. Two independent confirmations they did not fully press:
  1. **The placement is deliberate, not incidental.** Five of the nine files contain *both* a
     `positive variables` block and a plain `variables` block, with the cost term deliberately in the
     free one (M20 puts `vm_cost_processing` positive at `:20` and
     `vm_processing_substitution_cost` free at `:24`; M56 puts `vm_carbon_stock` positive at `:34` and
     both `vm_emission_costs`/`vm_reward_cdr_aff` free at `:39`/`:43`). MAgPIE's authors are signing
     the sign domain explicitly. This is not an oversight the doc is entitled to paper over.
  2. **The check fires in a DEFAULT run.** I tested the obvious escape — that the bioenergy subsidy
     might be 0 by default, making `vm_bioenergy_utility` identically 0 and the check harmless. It
     is not: `config/default.cfg:2119` = `s60_bioenergy_1st_subsidy <- 6.5`, and
     `60_bioenergy/1st2ndgen_priced_feb24/presolve.gms:60` applies it as a **price floor**
     (`i60_1stgen_bioenergy_subsidy(t)$(i60_1stgen_bioenergy_subsidy(t) < s60_bioenergy_1st_subsidy) = ...`),
     so the subsidy is ≥ 6.5 always. With `equations.gms:73-75` carrying an explicit unary minus on
     each subsidy term and `vm_dem_bioen` positive, `vm_bioenergy_utility` is **strictly negative in
     the default configuration**. The prescribed "flag any negative cost → source module error" check
     therefore fires on a correct default run and sends the reader to debug a bug-free M60.
  3. **`vm_emission_costs` genuinely goes negative.** `56_ghg_policy/price_aug22/equations.gms:19-22`:
     `v56_emis_pricing(i2,emis_oneoff,"co2_c") =e= sum(..., (pcm_carbon_stock(...) - vm_carbon_stock(...))/m_timestep_length)` —
     negative when carbon stock **grows** (regrowth/afforestation), so `q56_emission_costs` (`:56-58`)
     sums to a negative cost. `stopifnot(all(emission_costs >= 0))` aborts a correct validation suite.
  **Correction to the auditor:** `:1220` is `stopifnot(all(factor_costs_livst >= 0))`. The
  `emission_costs` assertion they quote is at **`:1221`**. Off-by-one; the claim exists and their
  substance is unaffected. Ironic in a report enforcing citation discipline, but not a refutation.
  The "catalog-vs-checklist contradiction" class claim is fair: `:417` (§3.8) and `:1121` (§17.2) both
  state the truth while `:738`/`:741`, `:1051` and `:1221` encode a single-exception model.
- **severity_agreed:** **Major** — misleads about behavior and induces a false-positive debug session,
  but does not itself cause a wrong code edit. (Not Critical: no listed Critical trigger fires; the
  prescription is wrong, not a wrong attribution/default/non-existence claim.)

---

### F7: `vm_cost_urban` described as "costs for urban land expansion" — it is a symmetric deviation penalty
- **verdict:** SURVIVES (one sub-claim of the auditor's overstated)
- **my_independent_check:** `modules/34_urban/exo_nov21/equations.gms` read in full. Header `:9-13`:
  "Cellular level land is prescribed via a very strong incentive not to deviate from cellular input
  data … This safeguards against infeasible outcomes". `:17-18` `q34_urban_cost1(j2) .. v34_cost1(j2)
  =g= sum(ct, i34_urban_area(ct, j2)) - vm_land(j2,"urban");` `:20-21` `q34_urban_cost2(j2) ..
  v34_cost2(j2) =g= vm_land(j2,"urban") - sum(ct, i34_urban_area(ct, j2));` `:25-26` `q34_urban_cell(j2)
  .. vm_cost_urban(j2) =e= (v34_cost1(j2) + v34_cost2(j2)) * s34_urban_deviation_cost;` `:30-31`
  `q34_urban_land(i2) .. sum(cell(i2,j2), vm_land(j2,"urban")) =e= sum((ct,cell(i2,j2)), i34_urban_area(ct,j2));`
  `config/default.cfg:1144` = `exo_nov21`. All the auditor's F7 citations are **exact**.
  Additional evidence they missed, which *strengthens* the finding: `exo_nov21/input.gms:13` —
  `s34_urban_deviation_cost Artificial cost for urban deviation variables (USD17MER per ha) / 1e+06 /`.
  The code calls it an **artificial cost** and prices it at 1e6 USD/ha — a guardrail number, not an
  economic one.
- **reasoning:** The doc's gloss is wrong in direction (the penalty is two-sided — `v34_cost1` fires
  when urban land is *reduced* below input data), wrong in kind (an artificial 1e6 USD/ha
  infeasibility guardrail, per the code's own words), and wrong in implication. This is the canonical
  CODE TRUTH violation AGENT.md names ("Module 35 applies historical disturbance rates labeled
  'wildfire'"), duplicated at `:1107` so both places a reader checks agree with each other and
  disagree with the code.
  **One overreach to correct:** the auditor writes "urban land is not an optimisation choice at all
  under the default". Not quite — `q34_urban_land` (`:30-31`) fixes only the **regional** total; the
  **cellular** allocation remains endogenous, which is the entire reason the deviation penalty exists.
  The realization header says so explicitly (`:13`: "it incurs the cost and shifts the land elsewhere
  in the region"). The finding does not depend on this sub-claim.
- **severity_agreed:** **Major**

---

### F8: `vm_cost_cropland` described as "(likely maintenance or baseline costs)"
- **verdict:** SURVIVES (auditor's line citation off by 2)
- **my_independent_check:** `modules/29_cropland/detail_apr24/equations.gms:28-32` (I read `:20-35`
  and confirmed exact lines via `rg -n 'q29_cost_cropland|v29_cost_treecover_est|v29_treecover_missing'`):
  ```
  28:  q29_cost_cropland(j2) ..
  29:    vm_cost_cropland(j2) =e=
  30:      v29_cost_treecover_est(j2) + v29_cost_treecover_recur(j2)
  31:      + v29_fallow_missing(j2) * sum(ct, i29_fallow_penalty(ct))
  32:      + v29_treecover_missing(j2) * sum(ct, i29_treecover_penalty(ct));
  ```
  `config/default.cfg:811` = `detail_apr24`. Doc `:250`.
- **reasoning:** Confirmed. Four terms: tree-cover establishment, tree-cover recurring, fallow
  shortfall penalty, tree-cover shortfall penalty. None is "maintenance" or "baseline". Two of four
  are policy-constraint penalties; the other two are agroforestry costs. §17.2 `:1103` says only
  "Cell-summed" and offers no correction.
  The auditor's meta-argument — that a hedge ("likely") in a position where the code is four lines
  away is a defect *because* it is a hedge — is sound and correctly grounded in AGENT.md Step 2c,
  which authorises "I'm not certain" only when the code is **ambiguous**. It is not ambiguous here.
  I would not, however, grant the claimed novelty much weight: the harm is the standard
  "gloss contradicts the equation" defect; the hedge affects *why it survived review*, not what class
  it is.
  **Citation correction:** the equation spans `:28-32`, not `:26-32` (`:26` is the doc comment
  `*' Total cost for the cropland module.`). Off-by-2; content claim unaffected.
- **severity_agreed:** **Major**

---

### F9: `kres` described as "(crop residues, wood fuel)" — `woodfuel` is not in `kres`
- **verdict:** SURVIVES
- **my_independent_check:** `modules/16_demand/sector_may15/sets.gms:13-14` —
  `kres(kall) Residues / res_cereals, res_fibrous, res_nonfibrous /`. Three members, no wood fuel.
  `modules/14_yields/managementcalib_aug19/sets.gms:12-16` — `k(kall) Primary products / tece, …,
  fish, wood, woodfuel/` — `woodfuel` is a member of `k`, which `q11_cost_reg` sums two lines away at
  `modules/11_costs/default/equations.gms:21` (`sum((cell(i2,j2),k), vm_cost_transp(j2,k))`).
  `modules/18_residues/flexreg_apr16/declarations.gms:17` — `vm_cost_prod_kres(i,kres) Production
  costs of harvesting crop residues (mio. USD17MER per yr)`. Doc `:186`.
- **reasoning:** Confirmed on both counts. I looked for a defence — that "wood fuel" might be a loose
  gloss for `res_fibrous`/`res_nonfibrous` — but M18's own declaration says "**crop** residues", and
  `woodfuel` is a distinct, real member of a distinct set. The auditor's double-counting harm
  (wood fuel appearing in both `vm_cost_prod_kres` and `vm_cost_transp(j,k)`) is concrete, and the
  doc's own §11.3 warns about exactly that. The "set-member import from an adjacent set" framing is
  apt — this is contamination, not invention, so the Critical "invented variable name" trigger does
  **not** fire. O5 (the second error in the same sentence: "processing" vs the code's "harvesting")
  is correct and should be fixed with F9, as the auditor suggests.
- **severity_agreed:** **Major**

---

### F10: `land` set members given as 5 friendly names — the set has 7
- **verdict:** SURVIVES
- **my_independent_check:** `core/sets.gms:250-251` —
  `land Land pools / crop, past, forestry, primforest, secdforest, urban, other /` → **7** members.
  Doc `:229` — "**Dimensions:** j (cells), land (cropland, pasture, forest, urban, other)" → 5.
  `modules/11_costs/default/equations.gms:20` sums `sum((cell(i2,j2),land), vm_cost_landcon(j2,land))`
  over all 7.
- **reasoning:** Confirmed. I considered defending it as an informal gloss (it does use friendly
  labels — "cropland" for `crop`, "pasture" for `past` — which signals paraphrase, not literal
  enumeration). That defence covers the *labels* but not the **arity**: collapsing `forestry`,
  `primforest`, `secdforest` into one "forest" silently drops two dimensions of a set whose members
  carry materially different conversion costs. A paraphrase is entitled to rename members; it is not
  entitled to lose them.
  **Severity check against the R16 anchor:** that anchor made a set truncation Critical explicitly
  because the element count was "off by 35×". Here it is 7 vs 5 (1.4×). The Major trigger
  ("Fabricated count for a set/parameter/realization list") is the correct match. The auditor got
  this calibration right.
- **severity_agreed:** **Major**

---

### F11: Unit-gloss arithmetic drift — "off by 10^6", and §5 contradicts §15.1/§16
- **verdict:** PARTIALLY_REFUTED — **the finding's headline number is itself wrong**
- **my_independent_check:** `modules/11_costs/default/declarations.gms:9-10` —
  `vm_cost_glo Total costs of production (mio. USD17MER per yr)`, `v11_cost_reg(i) Regional costs
  (mio. USD17MER per yr)`. `scaling.gms:8-9` — `vm_cost_glo.scale = 1e7; v11_cost_reg.scale(i) = 1e6;`.
  Doc lines read individually: `:553`, `:554`, `:988`, `:1054`.
- **reasoning:** The **substance stands**: `vm_cost_glo`'s declared unit is already `mio. USD`, and
  every gloss re-reads the numeral as plain USD. But I re-did the arithmetic and the finding's own
  headline is wrong:
  - `:988` — "~10^8 mio. USD/yr (**100 billion USD/yr**) in 1995". 10^8 mio. USD = 10^8 × 10^6 =
    **10^14 USD** = 100 trillion. The gloss says 100 billion = **10^11 USD**. 10^14 / 10^11 = **10^3**.
    The auditor asserts "Off by **10^6**". That is wrong by three orders of magnitude, and it is the
    number in the finding's **title** ("magnitude claims are off by 10^6"). No pairing of the doc's
    stated value and its own gloss yields 10^6.
  - `:553` — "~10^7 USD/yr (tens of billions)". 10^7 mio. USD = 10^13 USD = 10 trillion vs a gloss of
    ~10^10. ≈10^3. The auditor's "~10^3–10^4" is acceptable.
  - `:554` — "~10^6 USD/yr (billions per region)". 10^6 mio. USD = 10^12 USD = 1 trillion vs ~10^9.
    ≈10^3. Their prose ("1 trillion per region, not billions") is right.
  So the consistent error is **10^3 throughout** — the "mio." factor dropped once — which is in fact a
  *cleaner* and more diagnostic finding than the auditor's inconsistent 10^6/10^3–10^4 mix, and better
  supports their own "declared once, dropped downstream" mechanism.
  The **§5-vs-§15.1 contradiction stands** and is settled without a GDX: §5 (`:553`) asserts ~10^7 for
  `vm_cost_glo`, derived from `scaling.gms:8` (`1e7`); §15.1 (`:988`) asserts ~10^8 mio. USD/yr and
  §16 (`:1054`) asserts 10^8–10^9 mio. USD/yr. These differ by 10–100× and cannot both hold. The
  code's scaling factors (`1e7` global, `1e6` regional × 12 regions in `i` ≈ 1.2e7) are internally
  consistent with §5. `:1054` sits under "Testing Priority" as an acceptance criterion, which is the
  real harm. The auditor is right to decline asserting the true magnitude without a GDX — I decline too.
- **if PARTIALLY:** Stands — the unit-gloss drift, the §5-vs-§15.1/§16 contradiction, and the
  acceptance-criterion hazard at `:1054`. Refuted — the "off by 10^6" figure; the true, uniform
  discrepancy is **10^3**, and the finding should be retitled accordingly before it is actioned,
  or it will propagate its own arithmetic error into the fix.
- **severity_agreed:** **Major** (severity unchanged; the correction is to the number, not the class)

---

### F12: "All cost variables have naming convention `vm_cost_*` or `vm_*_cost*`"
- **verdict:** SURVIVES
- **my_independent_check:** Doc `:531` and `:533` read. Counterexamples verified against
  `modules/11_costs/default/equations.gms` (read in full this session): `vm_rotation_penalty(i2)` `:23`,
  `vm_reward_cdr_aff(i2)` `:27`, `vm_bioenergy_utility(i2)` `:38`, `vm_costs_additional_mon(i2)` `:40`.
- **reasoning:** I glob-tested each against both patterns. `vm_rotation_penalty`,
  `vm_bioenergy_utility` and `vm_reward_cdr_aff` contain no "cost" substring at all.
  `vm_costs_additional_mon` fails `vm_cost_*` (the character after `vm_cost` is `s`, not `_`) and
  fails `vm_*_cost*` (no second `_cost`). Four genuine counterexamples. The auditor's observation that
  the stated "Exception" at `:533` is about **sign** ("is revenue, not cost, hence the negative sign")
  and therefore does not discharge a **naming** claim is correct.
  The framing (counterexamples printed 500 lines earlier in the doc's own canonical code block at
  `:84-116`) is accurate and is a fair diagnostic signal. Harm is genuinely low — a reader does not
  act on a naming convention — so Minor is right, and the auditor did not inflate it.
- **severity_agreed:** **Minor**

---

### F13: "Modules that do NOT contribute (19 modules)" followed by an 18-item list
- **verdict:** SURVIVES
- **my_independent_check:** `sed -n '1129p' modules/module_11.md | tr ',' '\n' | wc -l` → **18**.
  Manual recount: 09, 12, 14, 15, 16, 17, 22, 28, 36, 37, 43, 45, 51, 52, 53, 55, 62, 80 = 18.
  `ls -d ../modules/*/ | wc -l` → **46**. Doc `:1128` says "(19 modules)"; `:1126` says 27 contribute.
- **reasoning:** Confirmed. 46 − 27 = 19 only if M11 is counted among modules not contributing to its
  own equation; the list sensibly omits M11, giving 18. Both are defensible under different
  conventions and they contradict each other on the same screen. The auditor's own re-derivation
  (that all 18 listed non-contributions are correct) matches mine — I re-derived the 32 terms from
  `equations.gms:15-47` and none is declared by any of the 18. Minor is right: the list is correct,
  only the count is off, and no reader acts on it. Their "count/enumeration off-by-self" class name is
  a reasonable refinement of "fabricated count", though I would not add a class for it.
- **severity_agreed:** **Minor**

---

### F14: Header verification date (2025-10-12) contradicts the two footers (2026-05-16)
- **verdict:** SURVIVES
- **my_independent_check:** `:6` — `**Status:** ✅ Fully Verified (2025-10-12)`; `:1275` —
  `**Documentation Status:** ✅ Verified (2026-05-16 — PR #866 sync)`; `:1282` — `**Last Verified**:
  2026-05-16`. PR#866's three split trade terms are present at
  `modules/11_costs/default/equations.gms:30-32` (read this session), confirming the 2026-05-16
  footer is the accurate one and the header was left behind.
- **reasoning:** Confirmed and uncontroversial. Rubric maps this to Minor ("Stale realization name in
  a verification footer — the footer is metadata; readers don't act on it"). The auditor's argument
  that the **header** is worse than a footer because AGENT.md Step 1b drives the staleness badge off
  it is a fair point, but it does not lift it out of Minor: the failure mode is an unnecessary
  `/sync`, not a wrong edit. They assigned Minor and did not inflate.
- **severity_agreed:** **Minor**

---

## Summary of the refutation pass

| Finding | Auditor severity | Verdict | My severity |
|---|---|---|---|
| F1 M80 erased as consumer | Critical | PARTIALLY_REFUTED | **Major** |
| F2 M80 writes `.up` back | Major | PARTIALLY_REFUTED | **Minor** |
| F3 urban costs → M10 | Critical | SURVIVES | **Critical** |
| F4 cropland costs → M30 | Critical | SURVIVES | **Critical** |
| F5 feasibility fixed in bilateral22 | Critical | SURVIVES | **Critical** |
| F6 non-negativity checklist | Major | SURVIVES | **Major** |
| F7 urban cost mechanism | Major | SURVIVES | **Major** |
| F8 cropland cost mechanism | Major | SURVIVES | **Major** |
| F9 `kres` includes wood fuel | Major | SURVIVES | **Major** |
| F10 `land` 5 vs 7 members | Major | SURVIVES | **Major** |
| F11 unit-gloss drift | Major | PARTIALLY_REFUTED (number wrong) | **Major** |
| F12 naming convention | Minor | SURVIVES | **Minor** |
| F13 19 vs 18 | Minor | SURVIVES | **Minor** |
| F14 header date | Minor | SURVIVES | **Minor** |

**Survivor severity counts:** Critical **3** (F3, F4, F5) · Major **7** (F1, F6, F7, F8, F9, F10, F11)
· Minor **4** (F2, F12, F13, F14). Weighted (4·C + 2·M + 1·m) = 12 + 14 + 4 = **30**.
Auditor's own weighting would have been 4·4 + 2·6 + 1·3 = 16 + 12 + 3 = 31 — the reduction is small
because the two severity downgrades (F1, F2) are nearly offset by nothing else moving.

**Where the auditor was overeager:**
1. **F1 severity + novelty.** The doc does carry the M11→M80 edge (`:1090` "provides to 1", `:1136`
   "`vm_cost_glo` → GAMS Solver"); it labels the endpoint wrongly rather than omitting it, and the
   `:1128` listing of M80 under "does NOT contribute to `q11_cost_reg`" is **correct** (only the
   `:1130` rationale sentence misfits). Critical requires the R20 anchor's *silent* miss; a
   `vm_cost_glo` rename fails loudly at GAMS compile time in M80's solve statement. → Major, and it
   is the known "wrong consumer set" class, not a new category.
2. **F2 attacks a true claim + double-counts.** §17.3's actual assertion — "zero circular
   dependencies" (`:1141`) — is **TRUE**; `vm_cost_glo.up = vm_cost_glo.l` is solver control flow
   between solves in a non-default realization, not a data-flow feedback edge, and M80 supplies M11
   no variable. F2 also scores `:1144`, the same line F1 scores. → Minor.
3. **F11 contains the error it is named after.** "Off by 10^6" is wrong; `:988`'s stated 10^8 mio. USD
   (10^14) vs its own gloss "100 billion" (10^11) is **10^3**, and 10^3 is the uniform discrepancy at
   `:553` and `:554` too. Fix the finding before actioning it.
4. **Two citation slips.** F6's `stopifnot(all(emission_costs >= 0))` is at `:1221`, not `:1220`
   (`:1220` is `factor_costs_livst`). F8's `q29_cost_cropland` spans `:28-32`, not `:26-32`.
5. **F7 sub-claim.** "Urban land is not an optimisation choice at all under the default" overstates —
   `q34_urban_land` (`:30-31`) fixes only the **regional** total; cellular allocation stays
   endogenous, which is why the deviation penalty exists at all.

**Where the auditor was right and I could not break it:** every code claim. All nine free-variable
declaration blocks (F6), the M34 symmetric penalty (F7), the M29 four-term equation (F8), `kres`'s
three members and `woodfuel`'s membership in `k` (F9), `land`'s seven members (F10), the
`bilateral22` live equation with no `presolve.gms` in existence (F5), and both wrong §7.1
attributions (F3, F4) reproduced exactly under independent derivation with positive controls.
F6 in particular got **stronger**: I tested the escape that the bioenergy subsidy might be zero by
default, and it is not (`config/default.cfg:2119` = 6.5, applied as a price floor at
`presolve.gms:60`), so `vm_bioenergy_utility` is strictly negative and the doc's prescribed check
fires on a correct **default** run. F7 also gained evidence the auditor missed:
`34_urban/exo_nov21/input.gms:13` prices `s34_urban_deviation_cost` at 1e6 USD/ha and the code itself
calls it an "**Artificial cost**".

**Not re-litigated per brief:** O4 (centrality figure — already independently resolved: M11 declares
1 interface var `vm_cost_glo` and reads 32 from other modules).
